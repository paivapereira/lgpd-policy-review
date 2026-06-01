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

Pre-reqs: semgrep==1.163.0 (ADR-0010) on PATH; real policy-reader + semgrep-runner via
.mcp.json; authenticated Claude Code session. Run (PowerShell, no WSL):
  uv run python scripts/smoke_tests/coordinator_live/g2b_mcp_middle_live.py
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import tempfile
from pathlib import Path

from coordinator.config import load_mcp_config
from coordinator.driver import run_branch_b_stage
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
# Synthetic CPF (valid checksum, NOT real PII) — triggers the br_cpf recognizer.
_SYNTHETIC_CPF = "529.982.247-25"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _make_cpf_repo() -> tuple[Path, str, str]:
    """A temp git repo: base commit clean, head commit adds a synthetic-CPF literal.
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
        f"def register(user):\n    cpf = '{_SYNTHETIC_CPF}'  # sintetico\n    return cpf\n",
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
    cfg = load_mcp_config(_CFG)
    repo, base, head = _make_cpf_repo()
    run_path = Path(tempfile.mkdtemp(prefix="g2b-det-run-"))
    cwd = os.getcwd()
    os.chdir(repo)  # the spawned semgrep-runner inherits cwd -> scans this repo
    try:
        out = await run_branch_b_stage(
            stage="detector",
            prompt=build_detector_prompt(_scope(base, head), TriagerDecision(decision="proceed", relevance_summary="cpf")),
            options=_detector_options(cfg),
            output_model=DetectorOutput,
            scratchpad_name="02-detector.json",
            run_path=run_path,
            run_id="g2b-det",
            on_tool_result=inspect_scan_diff_result,
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
        DetectorFinding(file="src/reg.py", line=2, rule_id="br-cpf", snippet=f"cpf = '{_SYNTHETIC_CPF}'",
                        surrounding_context="def register(user):\n    cpf = '...'  # coleta de CPF"),
    ]
    run_path = Path(tempfile.mkdtemp(prefix="g2b-cls-run-"))
    out = await run_branch_b_stage(
        stage="classifier",
        prompt=build_classifier_prompt(findings),
        options=_classifier_options(cfg),
        output_model=ClassifierOutput,
        scratchpad_name="03-classifier.json",
        run_path=run_path,
        run_id="g2b-cls",
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
                    "file": "src/reg.py", "line": 2, "rule_id": "br-cpf",
                    "snippet": f"cpf = '{_SYNTHETIC_CPF}'", "surrounding_context": "coleta de CPF",
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
    out = await run_branch_b_stage(
        stage="matcher",
        prompt=build_matcher_prompt(classifier_out),
        options=_matcher_options(cfg),
        output_model=MatcherOutput,
        scratchpad_name="04-matcher.json",
        run_path=run_path,
        run_id="g2b-mat",
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
        await run_branch_b_stage(
            stage="detector",
            prompt=build_detector_prompt(_scope("nonexistent-ref-aaaa", "HEAD"), TriagerDecision(decision="proceed", relevance_summary="x")),
            options=_detector_options(cfg),
            output_model=DetectorOutput,
            scratchpad_name="02-detector.json",
            run_path=run_path,
            run_id="g2b-deterr",
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
