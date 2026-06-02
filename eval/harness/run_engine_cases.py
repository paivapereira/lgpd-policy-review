r"""eval/harness/run_engine_cases.py — deterministic ENGINE-level harness.

Two deterministic layers, NO model and NO MCP wire:

1) VERDICT GATE (Pattern A, as scripts/smoke_tests/check_applicability_48b/probe.py):
       state  = load_policy(root)                                  # loader.py
       result = tools.check_applicability(clause_id, ctx, state)   # tools.py
       verdict = result.structured_content["verdict"]              # Option B
   Exercises the four-verdict logic of check_applicability against eval/cases.yaml.

2) CONSOLIDATED REPORTS (this file's extension): for each candidate-bearing LGPD
   case, sweep every active clause (the Matcher check-all, DD-M1), assemble one
   Matcher `Finding` per (candidate × clause) from the engine verdict, then call
   the SAME coordinator derivations used by the real pipeline —
   `derive_run_outcome` and `aggregate_summary` (src/coordinator/run.py) — plus
   the coordinator's own `_build_consolidated_state`, and validate the result
   against `ReportPayload` (the emit_report inputSchema). These functions are
   IMPORTED, never reimplemented (single source of truth). The Reporter is a
   passthrough, so reusing the coordinator's derivations reproduces a REAL,
   deterministic Report without the LLM.

   Reports are written to eval/harness/reports/<CASE>.report.json (and, for
   cases with a synthetic PR, to <pr_dir>/.expected-report.json as that PR's
   expected baseline). Every emitted Report is validated by instantiating
   `ReportPayload` — an invalid build is a loud failure, not a silent miss.

Topology B: LGPD cases load policies/eval-lgpd; GDPR cases load policies/eval-gdpr.

run_outcome coverage (deterministic layer):
  - success_with_findings / success_all_not_applicable  -> covered here.
  - skipped_by_triager   -> NOT reachable without the Triager (LLM). Pipeline-only.
  - success_no_candidates -> NOT reachable without the Detector finding zero. Pipeline-only.

GDPR Reports are NOT emittable in the MVP: Finding/ReportPayload pin
`legal_framework: Literal["LGPD"]` (src/subagents/{matcher,reporter}/models.py).
The GDPR swap VERDICT is still covered by the gate (SWAP-001-GDPR); only the
consolidated-Report assembly is LGPD-locked until a minor bump.

report_id is the ONLY non-deterministic field (uuid4, required by the model
pattern); everything else is reproducible. Baseline comparison should ignore it.

Run (from repo root):
    uv run python eval/harness/run_engine_cases.py            # gate table + reports
    uv run python eval/harness/run_engine_cases.py --json     # gate JSON (reports still written)

Exit code 0 iff every engine-runnable case matched AND every emitted Report is valid.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from coordinator.run import (
    _build_consolidated_state,
    aggregate_summary,
    derive_run_outcome,
)
from mcp_servers.policy_reader import tools
from mcp_servers.policy_reader.loader import load_policy
from subagents.matcher.models import Finding
from subagents.reporter.models import ReportPayload
from subagents.triager.models import TriagerInput

REPO_ROOT = Path(__file__).resolve().parents[2]
LGPD_ROOT = REPO_ROOT / "policies" / "eval-lgpd"
GDPR_ROOT = REPO_ROOT / "policies" / "eval-gdpr"
CASES_FILE = REPO_ROOT / "eval" / "cases.yaml"
REPORTS_DIR = REPO_ROOT / "eval" / "harness" / "reports"

# Single-clause contract probes (not candidate-level Reports): NA-MISMATCH targets
# one applies_to mismatch, NA-DEF targets POL-000 definitional. They stay in the
# verdict gate but do not get a consolidated Report.
_REPORT_EXCLUDE = {"NA-MISMATCH-001", "NA-DEF-001"}


def _structured(result: Any) -> dict[str, Any]:
    """Extract the structured_content dict from a ToolResult (Option B)."""
    return dict(result.structured_content)


def _verdict_or_error(sc: dict[str, Any]) -> str:
    """Map a check_applicability structured_content to a single outcome token.

    Option B: a domain error carries `errorCode`; a success carries `verdict`.
    """
    if "errorCode" in sc:
        return f"error:{sc['errorCode']}"
    return str(sc.get("verdict", "<no verdict>"))


def _resolve_root(policy_root: str) -> Path:
    if policy_root == "eval-lgpd":
        return LGPD_ROOT
    if policy_root == "eval-gdpr":
        return GDPR_ROOT
    raise ValueError(f"policy_root desconhecido: {policy_root!r}")


def _active_clause_ids(state: Any) -> list[str]:
    return sorted(
        cid for cid, c in state.clauses.items() if c.status == "active"
    )


def _run_single(state: Any, clause_id: str, ctx: dict[str, Any]) -> dict[str, Any]:
    result = tools.check_applicability(clause_id, ctx, state)
    sc = _structured(result)
    return {"outcome": _verdict_or_error(sc), "detail": sc}


def _sweep(state: Any, ctx: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Sweep every active clause (Matcher check-all, DD-M1): (clause_id, sc)."""
    return [
        (cid, _structured(tools.check_applicability(cid, ctx, state)))
        for cid in _active_clause_ids(state)
    ]


def _run_sweep(state: Any, ctx: dict[str, Any]) -> dict[str, Any]:
    """Aggregate of the sweep for the verdict gate (coverage_gap detection)."""
    per_clause = [
        {"clause": cid, "outcome": _verdict_or_error(sc)}
        for cid, sc in _sweep(state, ctx)
    ]
    verdicts = [pc["outcome"] for pc in per_clause]
    has_data = bool(ctx.get("data_categories"))
    is_collection = ctx.get("operation") == "collection"
    all_na = bool(verdicts) and all(v == "not_applicable" for v in verdicts)
    if all_na and has_data and is_collection:
        aggregate = "coverage_gap"
    elif all_na:
        aggregate = "all_not_applicable"
    else:
        aggregate = "has_substantive_verdict"
    return {"outcome": aggregate, "detail": {"per_clause": per_clause}}


# ---------------------------------------------------------------------------
# Verdict gate (layer 1)
# ---------------------------------------------------------------------------
def run(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    state_cache: dict[str, Any] = {}

    def _state(policy_root: str) -> Any:
        if policy_root not in state_cache:
            state_cache[policy_root] = load_policy(_resolve_root(policy_root))
        return state_cache[policy_root]

    for case in cases:
        cid = case["id"]
        if not case.get("engine_runnable", False):
            results.append({
                "id": cid, "expected": case["expected_verdict"],
                "obtained": "SKIPPED (pipeline-only)", "match": None,
            })
            continue
        state = _state(case["policy_root"])
        ctx = case["structured_context"]
        if case["mode"] == "single":
            r = _run_single(state, case["clause_id"], ctx)
        elif case["mode"] == "sweep":
            r = _run_sweep(state, ctx)
        else:
            raise ValueError(f"mode desconhecido em {cid}: {case['mode']}")
        expected = case["expected_verdict"]
        obtained = r["outcome"]
        results.append({
            "id": cid, "expected": expected, "obtained": obtained,
            "match": (expected == obtained), "detail": r.get("detail"),
        })
    return results


# ---------------------------------------------------------------------------
# Consolidated Reports (layer 2) — coordinator derivations, no LLM
# ---------------------------------------------------------------------------
def _emits_report(case: dict[str, Any]) -> bool:
    """A candidate-bearing LGPD case worth a consolidated Report."""
    return (
        bool(case.get("engine_runnable"))
        and case.get("policy_root") == "eval-lgpd"
        and case["id"] not in _REPORT_EXCLUDE
    )


def _synthetic_scope(case: dict[str, Any], pr_number: int) -> TriagerInput:
    """Synthetic pipeline scope (the engine harness has no real PR refs)."""
    return TriagerInput(
        pr_number=pr_number,
        base_ref="main",
        head_ref=f"eval/{case['id']}",
        repo_url="https://example.invalid/lgpd-eval-synthetic",
    )


def _synthetic_locus(case: dict[str, Any]) -> dict[str, Any]:
    """Synthetic Finding locus + Classifier context for the candidate.

    The locus (file/line/snippet/rule_id) is synthetic in the engine harness —
    the Detector/Classifier would supply real loci in the full pipeline. The
    candidate's data_categories/operation_type come from the case's
    classifier_fields. `rule_id` is the BR recognizer the synthetic PR carries.
    """
    cf = case["classifier_fields"]
    pr = case.get("pr")
    file = f"eval/{pr}/<synthetic>.py" if pr else f"eval/prs/{case['id']}/<synthetic>.py"
    return {
        "file": file,
        "line": 1,
        "snippet": f"# synthetic eval candidate ({case['id']})",
        "rule_id": "br-cpf",
        "data_categories": cf["data_categories"],
        "operation_type": cf["operation_type"],
    }


def build_report(case: dict[str, Any], state: Any, pr_number: int) -> ReportPayload:
    """Assemble + validate a consolidated Report for one candidate (no LLM).

    Sweeps all active clauses, builds one Finding per (candidate × clause) from
    the engine verdict, then reuses the coordinator's derive_run_outcome /
    aggregate_summary / _build_consolidated_state. Returns a validated
    ReportPayload (raises ValidationError on a malformed build).
    """
    ctx = case["structured_context"]
    locus = _synthetic_locus(case)
    findings: list[Finding] = []
    for cid, sc in _sweep(state, ctx):
        if "errorCode" in sc:
            msg = f"{case['id']}: clause {cid} returned errorCode {sc['errorCode']}"
            raise RuntimeError(msg)
        findings.append(Finding.model_validate({**locus, **sc}))

    run_outcome = derive_run_outcome(None, 1, findings)
    summary = aggregate_summary(findings)
    state_dict = _build_consolidated_state(
        run_outcome=run_outcome,
        triager_skip_reason=None,
        report_id=str(uuid.uuid4()),
        policy_schema_version=state.header.policy_schema_version,
        policy_version=state.header.policy_version,
        legal_framework=state.header.legal_framework,
        scope=_synthetic_scope(case, pr_number),
        summary=summary,
        findings=findings,
        scan_provenance=None,
    )
    # The decisive check: the assembled dict must satisfy the emit_report
    # inputSchema (ReportPayload). model_validate raises on any mismatch.
    return ReportPayload.model_validate(state_dict)


def emit_reports(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    state_cache: dict[str, Any] = {}
    pr_number = 0
    for case in cases:
        if not _emits_report(case):
            continue
        pr_number += 1
        root = case["policy_root"]
        if root not in state_cache:
            state_cache[root] = load_policy(_resolve_root(root))
        cid = case["id"]
        try:
            payload = build_report(case, state_cache[root], pr_number)
        except (ValidationError, RuntimeError) as exc:
            results.append({"id": cid, "valid": False, "error": str(exc), "paths": []})
            continue
        blob = json.dumps(payload.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
        written: list[str] = []
        out = REPORTS_DIR / f"{cid}.report.json"
        out.write_text(blob, encoding="utf-8")
        written.append(str(out.relative_to(REPO_ROOT)).replace("\\", "/"))
        pr = case.get("pr")
        if pr:  # also seed the PR's expected-report baseline (thesis convention)
            exp = REPO_ROOT / "eval" / pr / ".expected-report.json"
            exp.write_text(blob, encoding="utf-8")
            written.append(str(exp.relative_to(REPO_ROOT)).replace("\\", "/"))
        results.append({
            "id": cid, "valid": True, "run_outcome": payload.run_outcome,
            "findings": len(payload.findings), "paths": written,
        })
    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def _print_gate_table(results: list[dict[str, Any]]) -> None:
    width = max(len(r["id"]) for r in results)
    print(f"\n{'CASE'.ljust(width)}  {'EXPECTED':<22} {'OBTAINED':<22} MATCH")
    print("-" * (width + 52))
    for r in results:
        match = "-" if r["match"] is None else ("OK" if r["match"] else "FAIL")
        print(
            f"{r['id'].ljust(width)}  {str(r['expected']):<22} "
            f"{str(r['obtained']):<22} {match}"
        )
    runnable = [r for r in results if r["match"] is not None]
    passed = sum(1 for r in runnable if r["match"])
    skipped = sum(1 for r in results if r["match"] is None)
    print("-" * (width + 52))
    print(
        f"{passed}/{len(runnable)} engine-runnable cases matched "
        f"({skipped} pipeline-only skipped)."
    )


def _print_report_table(reports: list[dict[str, Any]]) -> None:
    if not reports:
        return
    width = max(len(r["id"]) for r in reports)
    print(f"\n{'REPORT'.ljust(width)}  {'RUN_OUTCOME':<28} FINDINGS  VALID")
    print("-" * (width + 46))
    for r in reports:
        if r["valid"]:
            print(
                f"{r['id'].ljust(width)}  {r['run_outcome']:<28} "
                f"{r['findings']:>8}  OK"
            )
        else:
            print(f"{r['id'].ljust(width)}  {'<build failed>':<28} {'-':>8}  FAIL")
    valid = sum(1 for r in reports if r["valid"])
    print("-" * (width + 46))
    print(f"{valid}/{len(reports)} consolidated Reports valid (ReportPayload).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit gate JSON")
    args = parser.parse_args()

    cases = yaml.safe_load(CASES_FILE.read_text(encoding="utf-8"))["cases"]
    results = run(cases)
    reports = emit_reports(cases)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    else:
        _print_gate_table(results)
        _print_report_table(reports)

    runnable = [r for r in results if r["match"] is not None]
    gate_ok = all(r["match"] for r in runnable)
    reports_ok = all(r["valid"] for r in reports)
    return 0 if (gate_ok and reports_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
