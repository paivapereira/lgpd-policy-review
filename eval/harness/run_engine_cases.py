r"""eval/harness/run_engine_cases.py — deterministic ENGINE-level harness.

Runs the engine-runnable cases of eval/cases.yaml directly against the
policy-reader engine, with NO model and NO MCP wire (Pattern A, the same
in-process pattern as scripts/smoke_tests/check_applicability_48b/probe.py):

    state  = load_policy(root)                                  # loader.py
    result = tools.check_applicability(clause_id, ctx, state)   # tools.py
    verdict = result.structured_content["verdict"]              # Option B

This exercises the deterministic core of the system — the four-verdict logic of
check_applicability. It does NOT run the LLM pipeline (Triager -> Detector ->
Classifier -> Matcher -> Reporter); those cases are marked engine_runnable:
false and skipped here. See eval/harness/README.md for how to run the full
pipeline later.

Policy roots (topology B): LGPD cases load policies/eval-lgpd; GDPR cases load
policies/eval-gdpr. The product seed policy/ (POL-000-only) is NOT used by the
evaluator.

Scope of each "mode":
  - single : one check_applicability(clause_id, ctx) call -> verdict.
  - sweep  : call check_applicability(ctx) for EVERY active clause in the
             root (mirrors the Matcher check-all, DD-M1) and derive the
             aggregate. coverage_gap == every clause not_applicable while
             ctx has data + operation == collection (matcher.md DD-M8).

NOTE on lawful_basis_required: that control is NOT implemented by the engine
(_verdict_for_control raises AssertionError for unknown controls). It is a
PROPOSAL (ADR-0015); the demonstration clause POL-008 lives in eval/proposed/
and is deliberately OUT of the eval catalog and out of every loaded policy root,
so no case here triggers that AssertionError. If a future loaded policy uses an
unimplemented control, the engine crashes LOUDLY here — which is the intended
signal.

Run (from repo root):
    uv run python eval/harness/run_engine_cases.py
    uv run python eval/harness/run_engine_cases.py --json   # machine output

Exit code 0 iff every engine-runnable case matched its expected outcome.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from mcp_servers.policy_reader import tools
from mcp_servers.policy_reader.loader import load_policy

REPO_ROOT = Path(__file__).resolve().parents[2]
LGPD_ROOT = REPO_ROOT / "policies" / "eval-lgpd"
GDPR_ROOT = REPO_ROOT / "policies" / "eval-gdpr"
CASES_FILE = REPO_ROOT / "eval" / "cases.yaml"


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


def _run_sweep(state: Any, ctx: dict[str, Any]) -> dict[str, Any]:
    """Sweep every active clause (Matcher check-all) and derive the aggregate."""
    per_clause: list[dict[str, str]] = []
    verdicts: list[str] = []
    for cid in _active_clause_ids(state):
        result = tools.check_applicability(cid, ctx, state)
        sc = _structured(result)
        outcome = _verdict_or_error(sc)
        per_clause.append({"clause": cid, "outcome": outcome})
        verdicts.append(outcome)

    has_data = bool(ctx.get("data_categories"))
    is_collection = ctx.get("operation") == "collection"
    all_na = bool(verdicts) and all(v == "not_applicable" for v in verdicts)
    # coverage_gap (matcher.md DD-M8): data present, collection, and every
    # active clause returned not_applicable (only the definitional floor +
    # category mismatches; no substantive clause governs the category).
    if all_na and has_data and is_collection:
        aggregate = "coverage_gap"
    elif all_na:
        aggregate = "all_not_applicable"
    else:
        aggregate = "has_substantive_verdict"
    return {
        "outcome": aggregate,
        "detail": {"per_clause": per_clause},
    }


def run(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    # cache loaded states per root so we don't reload for every case
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


def _print_table(results: list[dict[str, Any]]) -> None:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON results")
    args = parser.parse_args()

    cases = yaml.safe_load(CASES_FILE.read_text(encoding="utf-8"))["cases"]
    results = run(cases)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    else:
        _print_table(results)

    runnable = [r for r in results if r["match"] is not None]
    return 0 if all(r["match"] for r in runnable) else 1


if __name__ == "__main__":
    sys.exit(main())
