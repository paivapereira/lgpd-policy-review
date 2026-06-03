"""Full-pipeline e2e characterization over the synthetic PRs of `eval/prs/`,
rooted at the realistic Policy `policies/eval-lgpd` (POL-005/006/007 active).

THIS IS A MEASUREMENT, NOT A SEARCH FOR A RESULT (same honesty contract as
`category_exposure_discriminant.py`).
- The PR fixtures, the K budget, the policy root and the ground truth (GT) are
  FROZEN. Do not tweak inputs/prompts/clauses to "improve" a result; if a fixture
  seems broken (does not compile / does not trigger the Detector), STOP and report
  — that is distinct from enriching an input to ease classification.
- Every planned run is recorded; nothing is re-run to pick a better result. K runs
  that disagree are flagged `<<INCONSIST` — that is a datum, not a bug to re-run away.
- A transport/stage failure surfaces as `ERRO_EXECUCAO` (stage + type recorded):
  never hidden, never re-run, never masked, never refilled.
- This script does NOT draw the final conclusion. It marks each run CONVERGENTE or
  DIVERGENTE against the GT — NEVER "correct/wrong". The GT (`eval/cases.yaml`) is
  the *project expectation*, not a binding answer key: a divergence means
  "investigate" (the system erred? the GT is imprecise? legitimate legal
  ambiguity?), and that reading is done by a human over the raw trace, in the Chat.

Contrast with the deterministic engine harness (`eval/harness/run_engine_cases.py`),
which exercises only the `check_applicability` engine with `data_categories` injected
by hand. Here the REAL Triager->Detector->Classifier->Matcher->Reporter pipeline runs
end-to-end via `coordinator.run.run_pipeline` (IMPORTED, not reimplemented).

Root lever (the OPPOSITE of the G3 capstone). The G3 e2e test CLEARS
`POLICY_READER_ROOT` to fall back to the POL-000-only seed `policy/`
(test_g3_live_e2e.py:131). This harness SETS `POLICY_READER_ROOT` to the absolute
`policies/eval-lgpd` (resolve_policy_root precedence: explicit > env > <repo>/policy,
loader.py:51-63). Absolute is mandatory because each spawned server runs under the
synthetic-repo cwd (post-chdir).

Synthetic-repo construction. Per PR, `_make_pr_repo` builds a two-commit git repo
(generalizing the G3 `_make_cpf_repo`): an EMPTY base commit, then a head commit that
adds the PR's content file(s). Empty base => `worktree@head` == exactly the PR's
files, so the Triager (which only Globs the worktree — triager system prompt
:23-29 — it cannot truly diff) sees the PR content faithfully (decisive for the
SKIP-001 docs-only skip measurement). `scan_diff` runs `semgrep scan
--baseline-commit <base> .` (semgrep_runner/tools.py:298-305), which supports an
empty-tree baseline (every head file is "new"). The empty base is the one framework
behavior NOT covered by the G3 anchor (which used a non-empty base) — confirm it with
the COMP-001 smoke run before scaling (gates.md).

Per-stage trace capture WITHOUT touching the pipeline. `run_pipeline` returns only the
final Report (run.py:368), but each stage is persisted to the run scratchpad by
`write_scratchpad` (driver.py:55-64, 119): `01-triager.json` .. `04-matcher.json`. The
harness passes a FRESH `scratchpad_root` per run and reads the single `run-*/` dir
afterwards — works on success AND on halt (only the stages completed before the halt
exist, which is exactly what localizes WHERE a divergence happened).

Pre-reqs: authenticated Claude Code session; `.mcp.json` at repo root (for parity, not
read here — a temp one is written per run); `semgrep==1.163.0` on PATH (ADR-0010).
Run (PowerShell, no WSL):
  uv run python eval/experiments/pipeline_e2e_eval_lgpd.py
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import coordinator.run as coordinator_run
from claude_agent_sdk import ToolUseBlock, query
from coordinator.models import CoordinatorError, CoordinatorResult
from coordinator.run import run_pipeline
from subagents.triager.models import TriagerInput

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_EVAL_LGPD_ROOT = _PROJECT_ROOT / "policies" / "eval-lgpd"
_PRS_ROOT = _PROJECT_ROOT / "eval" / "prs"
_OUTPUT = Path(__file__).resolve().parent / "output" / "pipeline_e2e_raw.json"

# `cpf` is legitimately ambiguous between these two categories (R6, mirrors the
# discriminant). It is the GT-acceptable set for the SECONDARY classifier-categories
# axis only; the binding verdict GT for POL-005 is still `dados_de_identificacao`.
_IDENT_PAIR = frozenset({"dados_de_identificacao", "dados_de_documentos_oficiais"})


# ---------------------------------------------------------------------------
# DD-1 — Reporter emit-count instrumentation (harness-side; src/ UNTOUCHED)
# ---------------------------------------------------------------------------
# `coordinator.run.query` (the SDK `query` bound into the module) is consumed
# ONLY by `_run_reporter_stage` (run.py); the four upstream stages go through
# `coordinator.driver.query` / `ClaudeSDKClient`. Wrapping this one name therefore
# observes EXACTLY the Reporter stage (the test suite monkeypatches the same name).
# The wrapper is a TRANSPARENT TEE: it forwards every (*args, **kwargs) verbatim,
# re-yields each streamed message UNCHANGED, and only counts — as a pure side
# effect — emits matched by the FULL qualified tool name (identical to the guard's
# own filter, `coordinator.run._EMIT_REPORT_TOOL`). It must not swallow, reorder, or
# mutate any item, or it would corrupt the Reporter behavior it is meant to observe.
#   emits == 1 => single-shot (one valid emit).
#   emits == 2 => wrapper-recovery (1st emit failed the handler cross-checks; the
#                 ADR-0016 guard allowed the §9.2.a validation-retry, run.py).
#   emits == 0 => the run halted before a successful emit; the record's error
#                 `stage` disambiguates "before the Reporter" from "Reporter, no emit".
_EMIT_REPORT_TOOL = "mcp__reporter_tools__emit_report"  # == coordinator.run._EMIT_REPORT_TOOL
# The SDK `query` imported here is the SAME object `coordinator.run` binds as its
# module-global `query` (a plain `from claude_agent_sdk import query`); reading it
# from the SDK avoids depending on `coordinator.run` re-exporting it.
_REAL_QUERY = query
_emit_count: dict[str, int] = {"n": 0}


def _counting_query(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
    """Transparent tee over `coordinator.run.query`: forwards args and messages
    verbatim; counts `emit_report` ToolUseBlocks as a side effect only."""

    async def _tee() -> AsyncIterator[Any]:
        async for message in _REAL_QUERY(*args, **kwargs):
            content = getattr(message, "content", None)
            if content:
                for block in content:
                    if isinstance(block, ToolUseBlock) and block.name == _EMIT_REPORT_TOOL:
                        _emit_count["n"] += 1
            yield message

    return _tee()


# Swap ONLY the Reporter stage's seam (`coordinator.run.query`). `setattr` (not a
# direct attribute assignment) because `query` is imported-not-defined in
# `coordinator.run`, so mypy --strict's no-implicit-reexport would reject the
# dotted form. Install once; runs are strictly sequential.
setattr(coordinator_run, "query", _counting_query)


@dataclass(frozen=True)
class PRCase:
    """One synthetic PR + its frozen GT (from eval/cases.yaml) + its K budget.

    `mode` selects the convergence rule: `single` (verdict on `clause_id`), `sweep`
    (coverage_gap aggregate), `skip` (Triager skip). `gt_categories_acceptable` is the
    SECONDARY axis only (annotation; not folded into CONVERGENTE/DIVERGENTE).
    """

    case_id: str
    pr_dir: str  # relative under eval/prs/
    k: int
    mode: str  # "single" | "sweep" | "skip"
    clause_id: str | None
    expected_verdict: str
    gt_categories_acceptable: frozenset[str]


def _matrix() -> list[PRCase]:
    """The frozen PR x K matrix (ratified GATE 1). K=5 for substantive verdicts over a
    real clause; K=3 for the negative-path control (SKIP-001)."""
    return [
        PRCase("COMP-001", "COMP-001_identificacao_consent", 5, "single",
               "POL-005", "compliant", _IDENT_PAIR),
        PRCase("VIOL-001", "VIOL-001_identificacao_sem_base", 5, "single",
               "POL-005", "violation_candidate", _IDENT_PAIR),
        PRCase("INDET-001", "INDET-001_perfil_anonimizacao", 5, "single",
               "POL-006", "indeterminate", frozenset({"dados_de_perfil_comportamental"})),
        PRCase("PROBE-UNGOV-001", "PROBE-UNGOV-001_localizacao", 5, "sweep",
               None, "coverage_gap", frozenset({"dados_de_localizacao"})),
        PRCase("SWAP-001", "SWAP-001_identificacao_consent", 5, "single",
               "POL-005", "compliant", _IDENT_PAIR),
        PRCase("SKIP-001", "SKIP-001_docs_only", 3, "skip",
               None, "triager_skip", frozenset()),
    ]


# ---------------------------------------------------------------------------
# Synthetic-repo construction (generalizes test_g3_live_e2e._make_cpf_repo)
# ---------------------------------------------------------------------------
def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _head_sha(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _make_pr_repo(parent: Path, pr_dir: Path) -> tuple[Path, str, str]:
    """A two-commit git repo under `parent`: an EMPTY base commit, then a head commit
    that adds the PR's content file(s) (every entry in `pr_dir` EXCEPT dotfiles, so
    `.expected-report.json` is excluded — it is harness metadata, not part of the PR).
    Empty base => `worktree@head` == exactly the PR files; `scan_diff`'s
    `--baseline-commit <base>` treats every head file as new. Returns
    (repo, base_sha, head_sha)."""
    repo = parent / "pr-repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "eval@example.com")
    _git(repo, "config", "user.name", "eval")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "base")
    base = _head_sha(repo)
    copied = 0
    for item in sorted(pr_dir.iterdir()):
        if item.name.startswith("."):
            continue  # skip .expected-report.json and any dotfile
        if item.is_file():
            shutil.copy2(item, repo / item.name)
            copied += 1
    if copied == 0:
        raise RuntimeError(f"no content files to commit in {pr_dir} (fixture broken?)")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", f"pr {pr_dir.name}")
    head = _head_sha(repo)
    return repo, base, head


def _write_project_mcp_json(dst_dir: Path) -> Path:
    """Temp `.mcp.json` whose BOTH server commands use `uv run --project <repo-root>`
    (DD-G3-2 alpha): each spawned server resolves its project env from the repo root
    while keeping the synthetic-repo cwd (semgrep-runner scans it; policy-reader
    resolves its root via __file__/env, cwd-independent)."""
    prefix = ["run", "--project", str(_PROJECT_ROOT), "python", "-m"]
    payload = {
        "mcpServers": {
            "policy-reader": {"command": "uv", "args": [*prefix, "mcp_servers.policy_reader.server"]},
            "semgrep-runner": {"command": "uv", "args": [*prefix, "mcp_servers.semgrep_runner.server"]},
        }
    }
    path = dst_dir / ".mcp.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Per-stage trace capture (reads the scratchpad the pipeline already writes)
# ---------------------------------------------------------------------------
def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _read_stage_trace(run_dir: Path) -> dict[str, Any]:
    """Extract the per-stage trace from the run scratchpad. Each file is tolerated
    missing (Triager skip => no 02/03/04; a halt => only the completed stages)."""
    triager = _read_json(run_dir / "01-triager.json")
    detector = _read_json(run_dir / "02-detector.json")
    classifier = _read_json(run_dir / "03-classifier.json")
    matcher = _read_json(run_dir / "04-matcher.json")
    trace: dict[str, Any] = {
        "triager": None,
        "detector": None,
        "classifier": None,
        "matcher": None,
    }
    if triager is not None:
        trace["triager"] = {
            "decision": triager.get("decision"),
            "relevance_summary": triager.get("relevance_summary"),
            "skip_reason": triager.get("skip_reason"),
        }
    if detector is not None:
        dfindings = detector.get("findings", [])
        trace["detector"] = {
            "n_candidates": len(dfindings),
            "rule_ids": sorted({f["rule_id"] for f in dfindings}),
        }
    if classifier is not None:
        trace["classifier"] = [
            {
                "data_categories": c["structured_context"]["data_categories"],
                "declared_legal_basis": c["structured_context"]["declared_legal_basis"],
                "operation_type": c["structured_context"]["operation_type"],
            }
            for c in classifier.get("classified", [])
        ]
    if matcher is not None:
        trace["matcher"] = [
            {
                "clause": f["policy_clause_ref"],
                "verdict": f["verdict"],
                "requires_human_review": f.get("requires_human_review"),
            }
            for f in matcher.get("findings", [])
        ]
    return trace


def _classifier_categories(trace: dict[str, Any]) -> list[str]:
    """Union of data_categories the Classifier emitted across all candidates."""
    cls = trace.get("classifier") or []
    cats: list[str] = []
    for candidate in cls:
        cats.extend(candidate["data_categories"])
    return sorted(set(cats))


# ---------------------------------------------------------------------------
# Convergence (CONVERGENTE / DIVERGENTE / ERRO_EXECUCAO) against the GT
# ---------------------------------------------------------------------------
def _build_record(
    case: PRCase,
    result: CoordinatorResult,
    trace: dict[str, Any],
    run_id: str | None,
    reporter_emit_count: int,
) -> dict[str, Any]:
    classifier_cats = _classifier_categories(trace)

    if isinstance(result, CoordinatorError):
        # Transport/stage halt: honest datum, not re-run, not masked.
        return {
            "run_id": run_id,
            "convergence": "ERRO_EXECUCAO",
            "run_outcome": None,
            "summary_counts": None,
            "governing_clause_verdict": "<error>",
            "classifier_data_categories": classifier_cats,
            "classifier_categories_within_gt": None,
            "reporter_emit_count": reporter_emit_count,
            "trace": {**trace, "report_payload": None},
            "error": {
                "stage": result.stage,
                "type": type(result.cause).__name__,
                "msg": str(result.cause),
            },
        }

    payload = result.payload
    run_outcome = str(payload["run_outcome"])
    findings = payload["findings"]
    cats_within: bool | None

    if case.mode == "skip":
        convergence = "CONVERGENTE" if run_outcome == "skipped_by_triager" else "DIVERGENTE"
        governing = "<n/a: skip-path>"
        cats_within = None
    elif case.mode == "sweep":
        # PROBE-UNGOV: coverage_gap is an AGGREGATE, not a verdict token. Replicates
        # _run_sweep (run_engine_cases.py:126-142) + the Matcher DD-M8 escalation:
        # convergent iff every finding is not_applicable AND requires_human_review fired.
        all_na = bool(findings) and all(f["verdict"] == "not_applicable" for f in findings)
        any_rhr = any(bool(f.get("requires_human_review")) for f in findings)
        convergence = "CONVERGENTE" if (all_na and any_rhr) else "DIVERGENTE"
        governing = f"all_not_applicable={all_na}, requires_human_review={any_rhr}"
        cats_within = set(classifier_cats) <= set(case.gt_categories_acceptable)
    else:  # single
        clause_verdicts = [
            str(f["verdict"]) for f in findings if f["policy_clause_ref"] == case.clause_id
        ]
        governing = clause_verdicts[0] if clause_verdicts else "<absent>"
        convergence = "CONVERGENTE" if case.expected_verdict in clause_verdicts else "DIVERGENTE"
        cats_within = set(classifier_cats) <= set(case.gt_categories_acceptable)

    return {
        "run_id": run_id,
        "convergence": convergence,
        "run_outcome": run_outcome,
        "summary_counts": payload["summary"]["counts"],
        "governing_clause_verdict": governing,
        "classifier_data_categories": classifier_cats,
        "classifier_categories_within_gt": cats_within,
        "reporter_emit_count": reporter_emit_count,
        "trace": {**trace, "report_payload": payload},
        "error": None,
    }


_EMPTY_TRACE: dict[str, Any] = {
    "triager": None,
    "detector": None,
    "classifier": None,
    "matcher": None,
}


async def _run_one_pipeline(case: PRCase, idx: int) -> dict[str, Any]:
    """Build the PR repo, run the real pipeline once under its cwd, capture the trace.
    Any harness-level exception is captured honestly as ERRO_EXECUCAO (never hidden)."""
    workdir = Path(tempfile.mkdtemp(prefix=f"e2e-{case.case_id}-{idx}-"))
    cwd = Path.cwd()
    try:
        repo, base_ref, head_ref = _make_pr_repo(workdir, _PRS_ROOT / case.pr_dir)
        mcp_json = _write_project_mcp_json(workdir)
        scratch = workdir / "scratch"
        scope = TriagerInput(
            pr_number=idx + 1,
            base_ref=base_ref,
            head_ref=head_ref,
            repo_url="https://example.invalid/lgpd-eval-synthetic",
        )
        os.chdir(repo)  # scan_diff scans Path.cwd()
        _emit_count["n"] = 0  # DD-1: reset the tee counter before this run's Reporter stage
        try:
            result = await run_pipeline(
                scope, mcp_config_path=mcp_json, scratchpad_root=scratch
            )
        finally:
            os.chdir(cwd)
        emits = _emit_count["n"]  # captured immediately; nothing calls query() after the pipeline

        run_dirs = sorted(scratch.glob("run-*"))
        run_dir = run_dirs[0] if run_dirs else None
        trace = _read_stage_trace(run_dir) if run_dir is not None else dict(_EMPTY_TRACE)
        run_id = run_dir.name[len("run-"):] if run_dir is not None else None
        return _build_record(case, result, trace, run_id, emits)
    except Exception as exc:  # honest capture: harness-level failure, never hidden
        return {
            "run_id": None,
            "convergence": "ERRO_EXECUCAO",
            "run_outcome": None,
            "summary_counts": None,
            "governing_clause_verdict": "<harness-error>",
            "classifier_data_categories": [],
            "classifier_categories_within_gt": None,
            "reporter_emit_count": _emit_count["n"],
            "trace": None,
            "error": {"stage": "harness", "type": type(exc).__name__, "msg": str(exc)},
        }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Output (mirrors the discriminant's _dist / _print_table / _save)
# ---------------------------------------------------------------------------
def _dist(tokens: list[str]) -> str:
    counts = Counter(tokens)
    flag = "  <<INCONSIST" if len(set(tokens)) > 1 else ""
    body = " ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
    return body + flag


def _emit_dist(counts: list[int]) -> str:
    """Distribution of `reporter_emit_count` over K runs. Deliberately carries NO
    `<<INCONSIST` flag: emit-count variance across runs (single-shot vs
    wrapper-recovery) is EXPECTED behavior, not a convergence-token disagreement
    (contrast `_dist`). A run that halts before a successful emit shows as `0:n`."""
    tally = Counter(counts)
    return " ".join(f"{k}:{v}" for k, v in sorted(tally.items()))


def _print_table(cases: list[PRCase], raw: dict[str, Any]) -> None:
    print("\n" + "=" * 78)
    print("RESULTS — convergence distribution over K pipeline runs per PR")
    print("(vs eval/cases.yaml GT; CONVERGENTE/DIVERGENTE — NOT correct/wrong)")
    print("(NO conclusion drawn here — raw numbers only)")
    print("=" * 78)
    for case in cases:
        pr = raw["prs"][case.case_id]
        gt = f"{case.clause_id}={case.expected_verdict}" if case.clause_id else case.expected_verdict
        print(f"\n{case.case_id}  (K={case.k}, mode={case.mode})  GT: {gt}")
        print(f"    convergence        : {pr['distribution']}")
        print(f"    reporter_emit_count: {pr['emit_count_distribution']}")


def _save(raw: dict[str, Any]) -> None:
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")


async def _main() -> int:
    if not _EVAL_LGPD_ROOT.is_dir():
        print(f"FATAL: eval-lgpd root not found: {_EVAL_LGPD_ROOT}")
        return 2
    if shutil.which("semgrep") is None:
        print("FATAL: semgrep not on PATH (ADR-0010 prereq)")
        return 2

    os.environ["POLICY_READER_ROOT"] = str(_EVAL_LGPD_ROOT)  # absolute; survives chdir
    print(f"[root] POLICY_READER_ROOT = {os.environ['POLICY_READER_ROOT']}")

    cases = _matrix()
    raw: dict[str, Any] = {
        "policy_reader_root": str(_EVAL_LGPD_ROOT),
        "mcp_config": "temp .mcp.json per run (uv run --project <repo-root>)",
        "prs": {},
    }
    total = 0
    for case in cases:
        print(f"\n=== {case.case_id}  (K={case.k}, mode={case.mode}, GT={case.expected_verdict}) ===")
        runs: list[dict[str, Any]] = []
        for idx in range(case.k):
            rec = await _run_one_pipeline(case, idx)
            total += 1
            runs.append(rec)
            print(
                f"  [{case.case_id}] {idx + 1}/{case.k}: {rec['convergence']}  "
                f"(run_outcome={rec['run_outcome']}, "
                f"governing={rec['governing_clause_verdict']}, "
                f"emits={rec['reporter_emit_count']}, "
                f"classifier_cats={rec['classifier_data_categories']})"
            )
        raw["prs"][case.case_id] = {
            "gt": {
                "mode": case.mode,
                "clause_id": case.clause_id,
                "expected_verdict": case.expected_verdict,
                "data_categories_acceptable": sorted(case.gt_categories_acceptable),
            },
            "k": case.k,
            "runs": runs,
            "distribution": _dist([r["convergence"] for r in runs]),
            "emit_count_distribution": _emit_dist([r["reporter_emit_count"] for r in runs]),
        }

    raw["total_pipeline_runs"] = total
    _print_table(cases, raw)
    _save(raw)
    print(f"\n[done] policy root in use   : {_EVAL_LGPD_ROOT}")
    print(f"[done] total pipeline runs  : {total}")
    print(f"[done] raw data saved       : {_OUTPUT}")
    print("[done] NO conclusion drawn here — the reading (system erred? GT imprecise? "
          "legitimate ambiguity?) is for the Chat, over the raw trace above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
