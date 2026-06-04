"""Anchor tests for the Camada-3-MVP field-scoped compare logic (pure, no LLM).

Exhaustively pins the Decisão de gate (plano Passo 4 v3):
- STRICT (fail): run_outcome, summary.counts/total, provenance triple +
  report_schema_version, multiset(verdict, rule_id).
- ADVISORY (never fail): data_categories.
- EXCLUDED (never fail): report_id, scope.*, file/line, prose.
- outcome-only (SKIP-001): PASS iff run_outcome in {skipped_by_triager,
  success_no_candidates}.

§0 diagnostic causes of a STRICT failure are reflected: verdict flip (multiset),
cardinality change (total + multiset), provenance mismatch.
"""
from __future__ import annotations

from typing import Any

from eval.harness.camada3_compare import (
    compare_outcome_only,
    compare_report,
    raw_evidence,
)


def _baseline() -> dict[str, Any]:
    """A COMP-001-shaped committed baseline (engine-generated: nominal refs,
    synthetic file path, hand-injected category)."""
    return {
        "report_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "report_schema_version": "0.1.0",
        "policy_schema_version": "0.1.0",
        "policy_version": "0.2.0",
        "legal_framework": "LGPD",
        "run_outcome": "success_with_findings",
        "scope": {
            "pr_number": 1,
            "base_ref": "main",
            "head_ref": "eval/COMP-001",
            "repo_url": "https://example.invalid/lgpd-eval-synthetic",
        },
        "summary": {
            "counts": {
                "compliant": 1,
                "violation_candidate": 0,
                "indeterminate": 0,
                "not_applicable": 3,
            },
            "total": 4,
        },
        "findings": [
            _finding("compliant", "POL-005"),
            _finding("not_applicable", "POL-000"),
            _finding("not_applicable", "POL-006"),
            _finding("not_applicable", "POL-007"),
        ],
    }


def _finding(verdict: str, clause: str) -> dict[str, Any]:
    return {
        "file": "<synthetic>.py",
        "line": 1,
        "snippet": "# synthetic eval candidate",
        "rule_id": "br-cpf",
        "data_categories": ["dados_de_identificacao"],
        "operation_type": "collection",
        "verdict": verdict,
        "policy_clause_ref": clause,
    }


def _live_equivalent() -> dict[str, Any]:
    """Same STRICT fields as the baseline; differs only in EXCLUDED fields
    (report_id, scope, file/line, prose) — must still PASS."""
    actual = _baseline()
    actual["report_id"] = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    actual["scope"] = {
        "pr_number": 99,
        "base_ref": "9d0a8df9b02f1ac03bac1972dd97e2411c465714",
        "head_ref": "6ba963d119db7873a9eb9c776c7445cb3314afc1",
        "repo_url": "v",
    }
    for finding in actual["findings"]:
        finding["file"] = "users.py"
        finding["line"] = 26
        finding["evidence"] = "prosa derivada do diff real"
    return actual


def test_identical_strict_fields_pass() -> None:
    result = compare_report("COMP-001", _live_equivalent(), _baseline())
    assert result.passed
    assert result.strict_failures == []


def test_excluded_fields_never_fail() -> None:
    # _live_equivalent differs only in report_id / scope / file / line / prose
    result = compare_report("COMP-001", _live_equivalent(), _baseline())
    assert result.passed


def test_verdict_flip_fails_on_multiset() -> None:
    actual = _live_equivalent()
    actual["findings"][0]["verdict"] = "violation_candidate"
    actual["summary"]["counts"]["compliant"] = 0
    actual["summary"]["counts"]["violation_candidate"] = 1
    result = compare_report("COMP-001", actual, _baseline())
    assert not result.passed
    assert any("multiset" in f for f in result.strict_failures)
    assert any("compliant" in f for f in result.strict_failures)


def test_data_categories_drift_is_advisory_not_fail() -> None:
    actual = _live_equivalent()
    actual["findings"][0]["data_categories"] = [
        "dados_de_identificacao",
        "dados_de_autenticacao",
    ]
    result = compare_report("COMP-001", actual, _baseline())
    assert result.passed  # advisory never fails
    assert any("data_categories" in n for n in result.advisory_notes)


def test_cardinality_change_fails() -> None:
    actual = _live_equivalent()
    actual["findings"].append(_finding("not_applicable", "POL-006"))
    actual["summary"]["total"] = 5
    actual["summary"]["counts"]["not_applicable"] = 4
    result = compare_report("COMP-001", actual, _baseline())
    assert not result.passed
    assert any("total" in f for f in result.strict_failures)
    assert any("multiset" in f for f in result.strict_failures)


def test_provenance_mismatch_fails() -> None:
    actual = _live_equivalent()
    actual["policy_version"] = "0.1.0"  # wrong Policy loaded
    result = compare_report("COMP-001", actual, _baseline())
    assert not result.passed
    assert any("policy_version" in f for f in result.strict_failures)


def test_run_outcome_mismatch_fails() -> None:
    actual = _live_equivalent()
    actual["run_outcome"] = "success_all_not_applicable"
    result = compare_report("COMP-001", actual, _baseline())
    assert not result.passed
    assert any("run_outcome" in f for f in result.strict_failures)


def test_outcome_only_skip_tokens_pass() -> None:
    assert compare_outcome_only("SKIP-001", {"run_outcome": "skipped_by_triager"}).passed
    assert compare_outcome_only("SKIP-001", {"run_outcome": "success_no_candidates"}).passed


def test_outcome_only_substantive_fails() -> None:
    result = compare_outcome_only("SKIP-001", {"run_outcome": "success_with_findings"})
    assert not result.passed


def test_raw_evidence_is_deterministic_and_carries_multiset() -> None:
    payload = _baseline()
    first = raw_evidence(payload)
    second = raw_evidence(payload)
    assert first == second  # deterministic — safe to compare across K rounds
    assert "run_outcome='success_with_findings'" in first
    assert "'br-cpf'" in first  # the (verdict, rule_id) multiset is surfaced
    assert "total=4" in first
