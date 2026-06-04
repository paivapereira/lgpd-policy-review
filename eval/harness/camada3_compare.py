"""Pure field-scoped comparison of a live Report payload vs a committed baseline.

Implements the Camada-3-MVP Decisão de gate (plano Passo 4 v3 ratificado — no spec
em docs/specs/, é gate de avaliação). No I/O, no LLM: deterministic given two
payload dicts, so it is unit-tested exhaustively (tests/harness/test_camada3_compare).

STRICT (mismatch => fail):
  - run_outcome
  - summary.counts (4 verdict tokens) + summary.total
  - provenance triple (policy_schema_version, policy_version, legal_framework)
    + report_schema_version  (deterministic, derived from the loaded Policy header)
  - the MULTISET of (verdict, rule_id) over findings (order-independent)
ADVISORY (reported, never fails):
  - data_categories (Classifier/LLM-derived; baseline injects it by hand)
EXCLUDED (never compared):
  - report_id (uuid4 per run), scope.* (refs diverge by construction), prose
    (evidence/reason/snippet), file/line (baseline uses a synthetic placeholder)

§0 diagnostic — a STRICT failure has three causes, investigated never re-run-away:
  (1) multiset cardinality != baseline  -> Detector candidate-count divergence;
  (2) verdict-token flip                -> Classifier extraction drift
      (data_categories/legal_basis feed the engine verdict, matcher.md:69,89-91);
  (3) counts/floor change               -> a data_categories drift into a
      governing category (dados_de_saude->POL-007, comportamental->POL-006).
SKIP-001 has no baseline: PASS iff run_outcome is a no-substantive-verdict token
(skipped_by_triager OR success_no_candidates — the latter is the honest outcome if
the Triager drifts to "proceed" on a docs-only PR; eval/prs/SKIP-001.../README).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

_VERDICTS: tuple[str, ...] = (
    "compliant",
    "violation_candidate",
    "indeterminate",
    "not_applicable",
)
_PROVENANCE_KEYS: tuple[str, ...] = (
    "policy_schema_version",
    "policy_version",
    "legal_framework",
    "report_schema_version",
)
# SKIP-001: both tokens mean "no substantive verdict" (DD gate decision).
SKIP_PASS_OUTCOMES: tuple[str, ...] = ("skipped_by_triager", "success_no_candidates")


@dataclass
class CompareResult:
    """Outcome of one case's field-scoped comparison. `passed` reflects STRICT only;
    `advisory_notes` carry non-failing observations (e.g. data_categories drift)."""

    case_id: str
    passed: bool = True
    strict_failures: list[str] = field(default_factory=list)
    advisory_notes: list[str] = field(default_factory=list)


def _verdict_rule_multiset(findings: list[dict[str, Any]]) -> Counter[tuple[str, str]]:
    return Counter((str(f["verdict"]), str(f["rule_id"])) for f in findings)


def _data_categories_multiset(findings: list[dict[str, Any]]) -> Counter[tuple[str, ...]]:
    return Counter(tuple(sorted(f.get("data_categories") or [])) for f in findings)


def compare_report(case_id: str, actual: dict[str, Any], expected: dict[str, Any]) -> CompareResult:
    """Field-scoped STRICT compare of a live payload against a committed baseline."""
    result = CompareResult(case_id=case_id)

    if actual["run_outcome"] != expected["run_outcome"]:
        result.strict_failures.append(
            f"run_outcome: {actual['run_outcome']!r} != {expected['run_outcome']!r}"
        )

    actual_counts = actual["summary"]["counts"]
    expected_counts = expected["summary"]["counts"]
    for verdict in _VERDICTS:
        if actual_counts[verdict] != expected_counts[verdict]:
            result.strict_failures.append(
                f"counts.{verdict}: {actual_counts[verdict]} != {expected_counts[verdict]}"
            )
    if actual["summary"]["total"] != expected["summary"]["total"]:
        result.strict_failures.append(
            f"total: {actual['summary']['total']} != {expected['summary']['total']}"
        )

    for key in _PROVENANCE_KEYS:
        if actual.get(key) != expected.get(key):
            result.strict_failures.append(f"{key}: {actual.get(key)!r} != {expected.get(key)!r}")

    actual_ms = _verdict_rule_multiset(actual["findings"])
    expected_ms = _verdict_rule_multiset(expected["findings"])
    if actual_ms != expected_ms:
        result.strict_failures.append(
            f"(verdict,rule_id) multiset: {dict(actual_ms)} != {dict(expected_ms)}"
        )

    actual_cats = _data_categories_multiset(actual["findings"])
    expected_cats = _data_categories_multiset(expected["findings"])
    if actual_cats != expected_cats:
        result.advisory_notes.append(
            f"data_categories (advisory): {dict(actual_cats)} != {dict(expected_cats)}"
        )

    result.passed = not result.strict_failures
    return result


def compare_outcome_only(case_id: str, actual: dict[str, Any]) -> CompareResult:
    """SKIP-001 path (no baseline): PASS iff run_outcome is a no-verdict token."""
    result = CompareResult(case_id=case_id)
    outcome = str(actual["run_outcome"])
    if outcome not in SKIP_PASS_OUTCOMES:
        result.strict_failures.append(
            f"run_outcome {outcome!r} not in {SKIP_PASS_OUTCOMES}"
        )
    result.passed = not result.strict_failures
    return result
