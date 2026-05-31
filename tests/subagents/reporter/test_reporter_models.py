"""Phase 0 anchors — Reporter payload contract (reporter.md §3.1, §4.3) + A9.

ReportPayload mirrors §3.1; report_id is uuid4-validated at the model level
(failure -> PYDANTIC_VALIDATION); run_outcome is the 4-token Literal.
A9: SummaryModel is intentionally permissive on total==sum — that check (and
counts==aggregation) lives in the handler producing distinct errorCodes
(TOTAL_NOT_SUM_OF_COUNTS / COUNTS_DISAGREE_WITH_FINDINGS, reporter §4.8 #3).
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from subagents.matcher.models import Finding
from subagents.reporter.models import ReportPayload, SummaryCounts, SummaryModel
from subagents.triager.models import TriagerInput

_VALID_UUID4 = "550e8400-e29b-41d4-a716-446655440000"


def _scope() -> TriagerInput:
    return TriagerInput(
        pr_number=1,
        base_ref="main",
        head_ref="feature/x",
        repo_url="https://github.com/example/app",
    )


def _payload(**override: object) -> dict:
    base: dict = dict(
        report_id=_VALID_UUID4,
        report_schema_version="0.1.0",
        policy_schema_version="0.1.0",
        policy_version="1.2.0",
        legal_framework="LGPD",
        run_outcome="success_no_candidates",
        triager_skip_reason=None,
        scope=_scope(),
        summary=SummaryModel(counts=SummaryCounts(), total=0),
        findings=[],
    )
    base.update(override)
    return base


def test_reporter_payload_valid_no_candidates() -> None:
    p = ReportPayload(**_payload())
    assert p.run_outcome == "success_no_candidates"
    assert p.scan_provenance is None  # optional, defaults None


def test_reporter_payload_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        ReportPayload(**_payload(), bogus=1)


def test_reporter_payload_skip_path() -> None:
    p = ReportPayload(
        **_payload(run_outcome="skipped_by_triager", triager_skip_reason="docs-only")
    )
    assert p.triager_skip_reason == "docs-only"


def test_reporter_report_id_must_be_uuid4() -> None:
    with pytest.raises(ValidationError):
        ReportPayload(**_payload(report_id="not-a-uuid"))


def test_reporter_run_outcome_rejects_unknown_token() -> None:
    with pytest.raises(ValidationError):
        ReportPayload(**_payload(run_outcome="bogus_outcome"))


def test_reporter_payload_with_findings() -> None:
    finding = Finding(
        file="auth.py",
        line=14,
        snippet="x",
        rule_id="DATA-001",
        data_categories=["email"],
        operation_type="collection",
        verdict="compliant",
        evidence="guarded",
        policy_clause_ref="POL-005",
        policy_schema_version="0.1.0",
        policy_version="1.2.0",
        legal_framework="LGPD",
    )
    p = ReportPayload(
        **_payload(
            run_outcome="success_with_findings",
            summary=SummaryModel(counts=SummaryCounts(compliant=1), total=1),
            findings=[finding],
        )
    )
    assert len(p.findings) == 1


def test_summary_model_is_permissive_on_total_sum() -> None:
    # A9: model does NOT enforce total == sum(counts); the handler does
    # (TOTAL_NOT_SUM_OF_COUNTS). The model staying permissive keeps that
    # distinct errorCode reachable.
    m = SummaryModel(counts=SummaryCounts(compliant=1), total=99)
    assert m.total == 99
