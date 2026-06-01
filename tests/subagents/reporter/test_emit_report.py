"""Phase 2a anchors — emit_report handler cross-checks (reporter §4.8) + the
DD-2 error-envelope channel (sdk-mcp-conventions.md Eixo 2).

Strict-equality anchors (test-strategy.md): each cross-check anchor builds a
payload that PASSES Pydantic but trips exactly one cross-check, asserting the
spec-frozen errorCode. All five cross-check anchors + the channel anchor are
RED against the Phase-1 stub (which runs neither the cross-checks nor the
content-serialized error envelope); test_emit_report_dual_sink is confirmatory
(the stub already writes the file).

The structured error MUST arrive in `content` as a JSON string (NOT in
`structuredContent`, which the @tool bridge drops): the model reads errorCode
from `content` to retry (REPORTER_SYSTEM_PROMPT) — verified empirically in
scripts/smoke_tests/sdk_tool_error_channel.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from subagents.reporter.tools import emit_report_impl

_RUN_ID = "550e8400-e29b-41d4-a716-446655440000"
_OTHER_UUID = "11111111-1111-4111-8111-111111111111"


def _finding(**override: Any) -> dict[str, Any]:
    base: dict[str, Any] = dict(
        file="auth.py",
        line=14,
        snippet="db.users.insert(email=email)",
        rule_id="DATA-001",
        data_categories=["email"],
        operation_type="collection",
        verdict="compliant",
        evidence="Coleta precedida por check_marketing_consent guard.",
        policy_clause_ref="POL-005",
        policy_schema_version="0.1.0",
        policy_version="1.2.0",
        legal_framework="LGPD",
    )
    base.update(override)
    return base


def _payload(**override: Any) -> dict[str, Any]:
    """The all-valid baseline: one compliant finding, counts/total consistent,
    trinca aligned top-level vs per-finding, report_id == _RUN_ID."""
    base: dict[str, Any] = dict(
        report_id=_RUN_ID,
        report_schema_version="0.1.0",
        policy_schema_version="0.1.0",
        policy_version="1.2.0",
        legal_framework="LGPD",
        run_outcome="success_with_findings",
        triager_skip_reason=None,
        scope={
            "pr_number": 1,
            "base_ref": "main",
            "head_ref": "feature/x",
            "repo_url": "https://github.com/example/app",
        },
        summary={
            "counts": {
                "compliant": 1,
                "violation_candidate": 0,
                "indeterminate": 0,
                "not_applicable": 0,
            },
            "total": 1,
        },
        findings=[_finding()],
    )
    base.update(override)
    return base


def _errorcode(result: dict[str, Any]) -> str:
    """Extract the errorCode from an error envelope, asserting the DD-2 channel:
    is_error flag set, structured payload serialized into content (not
    structuredContent)."""
    assert result.get("is_error") is True
    assert "structuredContent" not in result  # DD-2: dropped by the @tool bridge
    body = json.loads(result["content"][0]["text"])
    assert isinstance(body["errorCode"], str)
    return str(body["errorCode"])


async def test_emit_report_id_mismatch(tmp_path: Path) -> None:
    # §9.3.e — payload.report_id != expected_report_id (closure), Step 2.
    result = await emit_report_impl(
        _payload(), run_path=tmp_path, expected_report_id=_OTHER_UUID
    )
    assert _errorcode(result) == "REPORT_ID_MISMATCH"


async def test_emit_report_clause_ref_regex(tmp_path: Path) -> None:
    # §9.3.a — policy_clause_ref "POL-12" (no zero-pad) fails ^POL-\d{3}$.
    payload = _payload(findings=[_finding(policy_clause_ref="POL-12")])
    result = await emit_report_impl(payload, run_path=tmp_path, expected_report_id=_RUN_ID)
    assert _errorcode(result) == "CLAUSE_REF_FORMAT"


async def test_emit_report_trinca_mismatch(tmp_path: Path) -> None:
    # §9.3.b — finding policy_version diverges from top-level trinca.
    payload = _payload(findings=[_finding(policy_version="9.9.9")])
    result = await emit_report_impl(payload, run_path=tmp_path, expected_report_id=_RUN_ID)
    assert _errorcode(result) == "PROVENANCE_MISMATCH"


async def test_emit_report_counts_disagree(tmp_path: Path) -> None:
    # §9.3.c — declared counts.compliant (5) != aggregation of findings (1).
    payload = _payload(
        summary={
            "counts": {
                "compliant": 5,
                "violation_candidate": 0,
                "indeterminate": 0,
                "not_applicable": 0,
            },
            "total": 5,
        }
    )
    result = await emit_report_impl(payload, run_path=tmp_path, expected_report_id=_RUN_ID)
    assert _errorcode(result) == "COUNTS_DISAGREE_WITH_FINDINGS"


async def test_emit_report_total_not_sum(tmp_path: Path) -> None:
    # §9.3.d — counts agree with findings, but total (99) != sum(counts) (1).
    # Split from counts_disagree per test-strategy.md (distinct failure dimension).
    payload = _payload(
        summary={
            "counts": {
                "compliant": 1,
                "violation_candidate": 0,
                "indeterminate": 0,
                "not_applicable": 0,
            },
            "total": 99,
        }
    )
    result = await emit_report_impl(payload, run_path=tmp_path, expected_report_id=_RUN_ID)
    assert _errorcode(result) == "TOTAL_NOT_SUM_OF_COUNTS"


async def test_emit_report_error_in_content(tmp_path: Path) -> None:
    # DD-2 channel anchor — a Pydantic failure surfaces errorCode in `content`
    # (JSON string), NOT in `structuredContent` (dropped by the @tool bridge).
    payload = _payload(report_id="not-a-uuid")
    result = await emit_report_impl(payload, run_path=tmp_path, expected_report_id=_RUN_ID)
    assert _errorcode(result) == "PYDANTIC_VALIDATION"


async def test_emit_report_dual_sink(tmp_path: Path) -> None:
    # §4.7/§9.5.a — on success, 99-report.json content == the emitted payload.
    payload = _payload()
    result = await emit_report_impl(payload, run_path=tmp_path, expected_report_id=_RUN_ID)
    assert "is_error" not in result  # success
    written = json.loads((tmp_path / "99-report.json").read_text(encoding="utf-8"))
    from subagents.reporter.models import ReportPayload

    assert written == ReportPayload.model_validate(payload).model_dump(mode="json")
