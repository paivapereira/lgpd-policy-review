"""Phase 0 anchors — coordinator termination union (coordinator.md §3.6).

`CoordinatorResult = CoordinatorReport | CoordinatorError` is the external
boundary the caller (GitHub Action / exercise script) consumes.
"""
from __future__ import annotations

from coordinator.models import CoordinatorError, CoordinatorReport, CoordinatorResult


def test_coordinator_report_holds_payload() -> None:
    report = CoordinatorReport(payload={"report_id": "x", "findings": []})
    assert report.payload["report_id"] == "x"


def test_coordinator_error_carries_cause_stage_coverage_gap() -> None:
    cause = ValueError("boom")
    err = CoordinatorError(cause=cause, stage="detector", coverage_gap="cobertura zero")
    assert err.cause is cause
    assert err.stage == "detector"
    assert err.coverage_gap == "cobertura zero"


def test_coordinator_result_alias_admits_both_members() -> None:
    # The union alias exists and both dataclasses are valid members.
    results: list[CoordinatorResult] = [
        CoordinatorReport(payload={}),
        CoordinatorError(cause=Exception("x"), stage="reporter", coverage_gap=""),
    ]
    assert isinstance(results[0], CoordinatorReport)
    assert isinstance(results[1], CoordinatorError)
