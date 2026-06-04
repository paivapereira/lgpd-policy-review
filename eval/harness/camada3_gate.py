"""Camada-3-MVP live field-scoped gate (DD-P4-4): run the REAL pipeline over a
synthetic PR, compare its Report against the committed baseline, and emit a
Markdown summary to STDOUT (the workflow YAML redirects to $GITHUB_STEP_SUMMARY, E1).

Roots the run at policies/eval-lgpd (POL-000/005/006/007 active) so the live
finding set matches the engine-generated baseline. READS (never regenerates) the
committed .expected-report.json — the generator is eval/harness/run_engine_cases.py.

Run (from repo root): `uv run python -m eval.harness.camada3_gate --case COMP-001`
(or `--case all`). LIVE: needs an authenticated SDK session + semgrep on PATH (this
is Gate #3 — the first end-to-end verification of the bare rule_id post-#105).
Exit 0 iff the case's STRICT compare passes (advisory never fails); 1 on a STRICT
failure or a CoordinatorError; 2 on a FATAL precheck.

Contract of record: plano Passo 4 v3 ratificado (sem spec em docs/specs/).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from coordinator.models import CoordinatorReport
from coordinator.run import run_pipeline
from subagents.triager.models import TriagerInput

from eval.harness.camada3_compare import (
    CompareResult,
    compare_outcome_only,
    compare_report,
)
from eval.harness.synthetic_pr import make_pr_repo, write_project_mcp_json
from scripts.ci.format_summary import render_error_summary, render_report_summary

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_EVAL_LGPD_ROOT = _PROJECT_ROOT / "policies" / "eval-lgpd"
_PRS_ROOT = _PROJECT_ROOT / "eval" / "prs"


@dataclass(frozen=True)
class GateCase:
    case_id: str
    pr_dir: str
    pr_number: int
    baseline: str | None  # repo-relative path, or None for outcome-only (SKIP-001)


_CASES: dict[str, GateCase] = {
    "COMP-001": GateCase(
        "COMP-001",
        "COMP-001_identificacao_consent",
        1,
        "eval/prs/COMP-001_identificacao_consent/.expected-report.json",
    ),
    "VIOL-001": GateCase(
        "VIOL-001",
        "VIOL-001_identificacao_sem_base",
        2,
        "eval/prs/VIOL-001_identificacao_sem_base/.expected-report.json",
    ),
    "SKIP-001": GateCase("SKIP-001", "SKIP-001_docs_only", 3, None),
}


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


async def _run_case(case: GateCase) -> tuple[CompareResult, str]:
    """Build the synthetic PR, run the live pipeline rooted at eval-lgpd, and
    field-compare. Returns (compare_result, markdown_summary)."""
    workdir = Path(tempfile.mkdtemp(prefix=f"camada3-{case.case_id}-"))
    cwd = Path.cwd()
    try:
        repo, base_ref, head_ref = make_pr_repo(workdir, _PRS_ROOT / case.pr_dir)
        mcp_json = write_project_mcp_json(workdir, _PROJECT_ROOT)
        scratch = workdir / "scratch"
        scope = TriagerInput(
            pr_number=case.pr_number,
            base_ref=base_ref,
            head_ref=head_ref,
            repo_url="https://example.invalid/lgpd-eval-synthetic",
        )
        os.environ["POLICY_READER_ROOT"] = str(_EVAL_LGPD_ROOT)  # absolute; survives chdir
        os.chdir(repo)  # scan_diff scans Path.cwd()
        try:
            result = await run_pipeline(
                scope, mcp_config_path=mcp_json, scratchpad_root=scratch
            )
        finally:
            os.chdir(cwd)

        if not isinstance(result, CoordinatorReport):
            summary = render_error_summary(
                result.stage, result.coverage_gap, type(result.cause).__name__
            )
            failed = CompareResult(case_id=case.case_id, passed=False)
            failed.strict_failures.append(
                f"CoordinatorError em {result.stage}: {type(result.cause).__name__}"
            )
            return failed, summary

        payload = result.payload
        summary = render_report_summary(payload)
        if case.baseline is None:
            return compare_outcome_only(case.case_id, payload), summary
        baseline_text = (_PROJECT_ROOT / case.baseline).read_text(encoding="utf-8")
        baseline: dict[str, object] = json.loads(baseline_text)
        return compare_report(case.case_id, payload, baseline), summary
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _emit(case_result: CompareResult, summary: str) -> None:
    """Emit the Markdown summary + gate verdict to STDOUT (the YAML redirects it)."""
    verdict = "PASS" if case_result.passed else "FAIL"
    print(summary)
    print("")
    print(f"### Gate {case_result.case_id}: **{verdict}**")
    for failure in case_result.strict_failures:
        print(f"- STRICT: {failure}")
    for note in case_result.advisory_notes:
        print(f"- advisory: {note}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Camada-3-MVP live field-scoped gate")
    parser.add_argument("--case", required=True, choices=[*_CASES, "all"])
    args = parser.parse_args(argv)

    if not _EVAL_LGPD_ROOT.is_dir():
        _log(f"FATAL: eval-lgpd root ausente: {_EVAL_LGPD_ROOT}")
        return 2
    if shutil.which("semgrep") is None:
        _log("FATAL: semgrep nao esta no PATH (prereq ADR-0010)")
        return 2

    selected = list(_CASES.values()) if args.case == "all" else [_CASES[args.case]]
    all_passed = True
    for case in selected:
        case_result, summary = asyncio.run(_run_case(case))
        _emit(case_result, summary)
        all_passed = all_passed and case_result.passed
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
