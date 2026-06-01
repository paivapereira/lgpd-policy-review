"""G2b live arm — the MCP middle (Detector -> Classifier -> Matcher) against the
REAL SDK + real MCP servers (Phase 2b).

Deterministic tool-boundary arms (scan_diff Option-B envelope, policy://vocabularies
read, check_applicability projection) are confirmed reproducibly via the MCP Inspector
CLI and recorded verbatim in RESULTS.md (no LLM needed). THIS script is the
non-deterministic agent-loop composition the Inspector cannot exercise: the real
subagent prompts driving the real tools through the SDK, and — critically — the
`{"output"}` wrapper staying quiet on the real DetectorOutput / MatcherOutput
`structured_output` (G0 already proved this on the schema; this re-confirms live).

Four ISOLATED arms (isolated at the driver, NOT run_pipeline):

  D. Detector — a synthetic-CPF git repo (base clean, head adds a synthetic CPF) +
     real semgrep scan_diff + the wired inspect_scan_diff_result hook. Confirms a
     populated DetectorOutput emits live with NO {"output"} wrapper, and the hook does
     NOT false-positive on a clean (errorCode-free) scan.
  E. Classifier — a fixed DetectorFinding list -> real Classifier (reads
     policy://vocabularies) -> ClassifierOutput; verify_classifier_passthrough passes;
     null-on-miss observable on an ambiguous candidate.
  F. Matcher — a ClassifierOutput -> real Matcher check-all on the real policy-reader ->
     MatcherOutput with NO {"output"} wrapper; cardinality floor (>= candidates_count);
     POL-000 not_applicable floor present.
  G. Detector hook (error) — scan_diff on a bad base_ref -> the wired hook raises
     DetectorScanFailed through the driver (errorCode in structuredContent, Option B).

STATUS — the MCP-readiness gap that originally blocked ARM D is FIXED (PR-A #95, ADR-0014
Accepted): these four arms now drive the production `_run_mcp_stage` (D/G → semgrep-runner,
E/F → policy-reader) with its readiness wait + in-session retry, NOT the one-shot `query()`.
The causal readiness question is already settled (RESULTS.md "GATE D1" PASS). What remains is
the milestone-level LIVE run at G3: re-run to complete D/E/F/G end-to-end and make the FIRST
observation of the `{"output"}` wrapper on a populated, list-shaped `DetectorOutput` (the
fixture now adds a `cpf` PARAMETER so `scan_diff` yields a real finding). The `uv run
--project` launch here is a foreign-cwd robustness aid, NOT the race fix.

Pre-reqs: semgrep==1.163.0 (ADR-0010) on PATH; real policy-reader + semgrep-runner via
.mcp.json; authenticated Claude Code session. Run (PowerShell, no WSL):
  uv run python scripts/smoke_tests/coordinator_live/g2b_mcp_middle_live.py
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from claude_agent_sdk import SystemMessage, UserMessage

from coordinator.config import McpServersConfig, load_mcp_config
from coordinator.driver import RETRY_BUDGET, _run_mcp_stage
from coordinator.prompts import (
    build_classifier_prompt,
    build_detector_prompt,
    build_matcher_prompt,
)
from coordinator.run import _classifier_options, _detector_options, _matcher_options
from subagents.classifier.models import ClassifierOutput
from subagents.classifier.passthrough import verify_classifier_passthrough
from subagents.detector.hooks import inspect_scan_diff_result
from subagents.detector.models import DetectorFinding, DetectorOutput
from subagents.matcher.models import MatcherOutput
from subagents.triager.models import TriagerDecision, TriagerInput

_CFG = ".mcp.json"
_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # scripts/smoke_tests/coordinator_live/<file>
# Synthetic CPF (valid checksum, NOT real PII). NOTE: the br-cpf rule is SYNTACTIC — it
# matches a parameter named `cpf` (`def $FN(..., cpf, ...)`), NOT this value. The value is
# realistic decoration for snippets/context; value/dict-key/attribute detection is a
# documented post-MVP gap (br_cpf.yaml).
_SYNTHETIC_CPF = "529.982.247-25"


def _cfg_with_project_semgrep() -> McpServersConfig:
    """Bug-1 fix (caller-side; scan_diff scans Path.cwd() by ratified design, tools.py:271 /
    canonical §4.2 / DD-T06-3,19 — NOT a contract change). The probe os.chdir()s into the
    synthetic-CPF repo so the spawned semgrep-runner inherits that cwd; but the default
    `uv run python -m ...` then runs from a dir with no project env. Override the
    semgrep-runner command with `uv run --project <PROJECT_ABS>` so uv resolves the env from
    the project while the spawned server's cwd stays the synthetic repo (verified: uv
    --project keeps cwd)."""
    base = load_mcp_config(_CFG)
    patched = {
        "command": "uv",
        "args": ["run", "--project", str(_PROJECT_ROOT), "python", "-m", "mcp_servers.semgrep_runner.server"],
    }
    return McpServersConfig(
        mcp_servers_dict={**base.mcp_servers_dict, "semgrep-runner": patched},  # type: ignore[dict-item]
        policy_reader_config=base.policy_reader_config,
        semgrep_runner_config=patched,  # type: ignore[arg-type]
    )


def _observe(message: object) -> None:
    """Instrumentation (arm-level, less invasive than the hook): log the init
    SystemMessage.data (registered tools + mcp_server statuses — Suspect 1/2/3 ground
    truth) and the type+repr of each UserMessage.tool_use_result, then delegate to the
    real hook. Captures the shape the CONSUMER receives via the SDK relay."""
    if isinstance(message, SystemMessage):
        data = getattr(message, "data", None)
        print(f"  [observe] SystemMessage subtype={message.subtype!r} data={repr(data)[:1500]}", file=sys.stderr)
    elif isinstance(message, UserMessage):
        tur = message.tool_use_result
        print(f"  [observe] tool_use_result type={type(tur).__name__} repr={repr(tur)[:500]}", file=sys.stderr)
    inspect_scan_diff_result(message)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _make_cpf_repo() -> tuple[Path, str, str]:
    """A temp git repo: base commit clean; head commit adds a function with a `cpf`
    PARAMETER (`def collect(cpf): ...`) — what the SYNTACTIC br-cpf rule matches (NOT a CPF
    value literal; value/dict-key/attribute detection is a documented post-MVP gap). So
    `scan_diff` diff-mode flags the added `def` line -> a real br-cpf finding.
    Returns (repo, base_ref, head_ref)."""
    repo = Path(tempfile.mkdtemp(prefix="g2b-cpf-repo-"))
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "g2b@example.com")
    _git(repo, "config", "user.name", "g2b")
    (repo / "src").mkdir()
    (repo / "src" / "reg.py").write_text("def register(user):\n    return user\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    (repo / "src" / "reg.py").write_text(
        "def register(user):\n    return user\n\n\n"
        "def collect(cpf):  # 'cpf' parameter -> matched by the syntactic br-cpf rule\n"
        "    return cpf\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "add cpf")
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    return repo, base, head


def _scope(base: str = "main", head: str = "feature/x") -> TriagerInput:
    return TriagerInput(pr_number=1, base_ref=base, head_ref=head, repo_url="https://github.com/ex/app")


async def _arm_d_detector_live() -> tuple[bool, bool]:
    # G2B_OBSERVE_BROKEN=1 -> DEFAULT (no --project) launch, to capture the failed-server
    # str shape once (diagnostic); else the Bug-1-fixed launch (`uv run --project`).
    broken = bool(os.environ.get("G2B_OBSERVE_BROKEN"))
    cfg = load_mcp_config(_CFG) if broken else _cfg_with_project_semgrep()
    repo, base, head = _make_cpf_repo()
    run_path = Path(tempfile.mkdtemp(prefix="g2b-det-run-"))
    opts = _detector_options(cfg)
    print(f"  [observe] options.mcp_servers={opts.mcp_servers}", file=sys.stderr)
    print(f"  [observe] options.allowed_tools={opts.allowed_tools}", file=sys.stderr)
    cwd = os.getcwd()
    os.chdir(repo)  # the spawned semgrep-runner inherits cwd -> scan_diff scans this repo
    try:
        out = await _run_mcp_stage(
            stage="detector",
            prompt=build_detector_prompt(_scope(base, head), TriagerDecision(decision="proceed", relevance_summary="cpf")),
            options=opts,
            output_model=DetectorOutput,
            scratchpad_name="02-detector.json",
            run_path=run_path,
            run_id="g2b-det",
            target="semgrep-runner",
            retries=RETRY_BUDGET,
            on_tool_result=_observe,
        )
    finally:
        os.chdir(cwd)
    assert isinstance(out, DetectorOutput)
    populated = len(out.findings) > 0  # synthetic CPF detected
    no_wrapper = isinstance(out, DetectorOutput)  # validated cleanly -> no {"output"} wrapper
    print(f"  DetectorOutput findings={len(out.findings)} provenance.semgrep={out.provenance.semgrep_version!r}")
    return populated, no_wrapper


async def _arm_e_classifier_live() -> bool:
    cfg = load_mcp_config(_CFG)
    findings = [
        DetectorFinding(file="src/reg.py", line=5, rule_id="br-cpf", snippet="def collect(cpf):",
                        surrounding_context=f"def collect(cpf):  # coleta de CPF (sintetico: {_SYNTHETIC_CPF})\n    return cpf"),
    ]
    run_path = Path(tempfile.mkdtemp(prefix="g2b-cls-run-"))
    out = await _run_mcp_stage(
        stage="classifier",
        prompt=build_classifier_prompt(findings),
        options=_classifier_options(cfg),
        output_model=ClassifierOutput,
        scratchpad_name="03-classifier.json",
        run_path=run_path,
        run_id="g2b-cls",
        target="policy-reader",
        verify_passthrough=verify_classifier_passthrough,
        upstream=findings,
    )
    assert isinstance(out, ClassifierOutput)
    print(f"  ClassifierOutput classified={len(out.classified)} sc0={out.classified[0].structured_context.model_dump() if out.classified else None}")
    return len(out.classified) == len(findings)  # passthrough cardinality + verify passed (no raise)


async def _arm_f_matcher_live() -> tuple[bool, bool]:
    cfg = load_mcp_config(_CFG)
    classifier_out = ClassifierOutput.model_validate(
        {
            "classified": [
                {
                    "file": "src/reg.py", "line": 5, "rule_id": "br-cpf",
                    "snippet": "def collect(cpf):", "surrounding_context": "def collect(cpf): coleta de CPF",
                    "structured_context": {
                        "operation_type": "collection",
                        "declared_legal_basis": "consent",
                        "data_categories": ["dados_de_documentos_oficiais"],
                        "declared_transformations": [],
                    },
                }
            ]
        }
    )
    run_path = Path(tempfile.mkdtemp(prefix="g2b-mat-run-"))
    out = await _run_mcp_stage(
        stage="matcher",
        prompt=build_matcher_prompt(classifier_out),
        options=_matcher_options(cfg),
        output_model=MatcherOutput,
        scratchpad_name="04-matcher.json",
        run_path=run_path,
        run_id="g2b-mat",
        target="policy-reader",
        # verify_passthrough OMITTED (G6 deferred)
    )
    assert isinstance(out, MatcherOutput)
    floor = len(out.findings) >= len(classifier_out.classified)  # cardinality floor
    has_pol000 = any(f.policy_clause_ref == "POL-000" for f in out.findings)
    print(f"  MatcherOutput findings={len(out.findings)} verdicts={[f.verdict for f in out.findings]}")
    return floor, has_pol000


async def _arm_g_detector_hook_error() -> bool:
    from coordinator.errors import DetectorScanFailed

    cfg = load_mcp_config(_CFG)
    run_path = Path(tempfile.mkdtemp(prefix="g2b-deterr-run-"))
    try:
        await _run_mcp_stage(
            stage="detector",
            prompt=build_detector_prompt(_scope("nonexistent-ref-aaaa", "HEAD"), TriagerDecision(decision="proceed", relevance_summary="x")),
            options=_detector_options(cfg),
            output_model=DetectorOutput,
            scratchpad_name="02-detector.json",
            run_path=run_path,
            run_id="g2b-deterr",
            target="semgrep-runner",
            retries=RETRY_BUDGET,
            on_tool_result=inspect_scan_diff_result,
        )
    except DetectorScanFailed as exc:
        print(f"  DetectorScanFailed errorCode={exc.error_code!r} isRetryable={exc.is_retryable}")
        return True
    return False


async def _main() -> int:
    print("=== G2b ARM D - Detector live (synthetic-CPF repo + semgrep) ===")
    d_pop, d_nowrap = await _arm_d_detector_live()
    print("=== G2b ARM E - Classifier live (reads policy://vocabularies) ===")
    e_ok = await _arm_e_classifier_live()
    print("=== G2b ARM F - Matcher live (check-all on real policy-reader) ===")
    f_floor, f_pol000 = await _arm_f_matcher_live()
    print("=== G2b ARM G - Detector hook escalates scan error (live) ===")
    g_ok = await _arm_g_detector_hook_error()

    print()
    print(f"ARM D (Detector populated + no wrapper) : {'PASS' if (d_pop and d_nowrap) else 'REVIEW'}")
    print(f"ARM E (Classifier passthrough verifies) : {'PASS' if e_ok else 'REVIEW'}")
    print(f"ARM F (Matcher floor + POL-000 + no wrapper): {'PASS' if (f_floor and f_pol000) else 'REVIEW'}")
    print(f"ARM G (hook escalates scan error)       : {'PASS' if g_ok else 'REVIEW'}")
    overall = d_pop and d_nowrap and e_ok and f_floor and f_pol000 and g_ok
    print(f"\nG2b MCP-middle: {'PASS' if overall else 'REVIEW - see arms above'}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
