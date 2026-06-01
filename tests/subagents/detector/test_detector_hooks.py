"""Phase 2b anchors — Detector `scan_diff` stream-inspection hook
(`inspect_scan_diff_result`; detector.md §6.2 / coordinator §3.2, §5).

DD-d ratified shape: **escalate-all**. The hook raises `DetectorScanFailed` on EVERY
`scan_diff` domain error (Option B: `errorCode` present in
`UserMessage.tool_use_result.structuredContent`, wire `isError=False`), carrying
`error_code`/`is_retryable`/`details` verbatim. `findings:[]` (or any findings) NEVER
aliases an error.

DD-d DEFERRED DIVERGENCE: the spec mandates retry-BEFORE-raise for retryable codes in
three loci (detector §6.2 l.245, coordinator §5 l.393-395 + l.428 verbatim). That
retry-under-budget loop is DEFERRED to Fase 3 (registered debt; see docs/tasks.md /
project memory). Until then a retryable scan error fails the run. These anchors assert
the `is_retryable` CLASSIFICATION is correct, NOT that retry happens — "field populated"
is not "behavior implemented".
"""
from __future__ import annotations

import json
from typing import Any

import pytest
from claude_agent_sdk import AssistantMessage, ResultMessage, ToolResultBlock, UserMessage

from coordinator.errors import DetectorScanFailed
from subagents.detector.hooks import inspect_scan_diff_result


def _scan_result(envelope: dict[str, Any]) -> UserMessage:
    """A UserMessage carrying a scan_diff Option-B tool result: wire isError False, the
    structured envelope under tool_use_result.structuredContent (sdk-mcp-conventions
    Eixo 2; ToolResultBlock.content carries only the JSON string)."""
    return UserMessage(
        content=[ToolResultBlock(tool_use_id="tu-scan", content=json.dumps(envelope), is_error=False)],
        tool_use_result={"structuredContent": envelope, "isError": False},
    )


def test_inspect_scan_diff_errorCode_retryable() -> None:
    """Escalate-all in 2b: a retryable errorCode raises DetectorScanFailed carrying
    is_retryable=True. The retry-under-budget loop mandated by coordinator §5 l.428 +
    detector §6.2 is DEFERRED to Fase 3 (see docs/tasks.md / project memory); until then
    a retryable scan error fails the run. Asserts the CLASSIFICATION is correct, NOT that
    retry happens."""
    msg = _scan_result(
        {"errorCode": "SCAN_TIMEOUT", "isRetryable": True, "details": {"timeout_seconds": 30}}
    )
    with pytest.raises(DetectorScanFailed) as exc:
        inspect_scan_diff_result(msg)
    assert exc.value.error_code == "SCAN_TIMEOUT"
    assert exc.value.is_retryable is True  # classification carried for the Fase-3 retry consumer
    assert exc.value.stage == "detector"
    assert exc.value.details == {"timeout_seconds": 30}


def test_inspect_scan_diff_errorCode_nonretryable() -> None:
    """A non-retryable errorCode escalates directly (coordinator §5 l.428 'non-retryable
    escalam direto'): raises DetectorScanFailed carrying is_retryable=False."""
    msg = _scan_result(
        {"errorCode": "GIT_REF_NOT_FOUND", "isRetryable": False, "details": {"ref_param": "base_ref"}}
    )
    with pytest.raises(DetectorScanFailed) as exc:
        inspect_scan_diff_result(msg)
    assert exc.value.error_code == "GIT_REF_NOT_FOUND"
    assert exc.value.is_retryable is False


def test_inspect_scan_diff_errorCode_with_findings_still_raises() -> None:
    """DD-d invariant (detector §6.2): an errorCode co-existing with NON-EMPTY findings
    STILL escalates — the findings are ignored, never aliased as a clean scan. The only
    anchor that proves 'nothing leaks as a fabricated finding'. Fails for the right
    reason against the no-op stub (DID NOT RAISE), not on import."""
    msg = _scan_result(
        {
            "errorCode": "SCAN_TIMEOUT",
            "isRetryable": True,
            "findings": [{"location": {"path": "a.py", "start_line": 1}, "rule_id": "BR-CPF"}],
        }
    )
    with pytest.raises(DetectorScanFailed) as exc:
        inspect_scan_diff_result(msg)
    assert exc.value.error_code == "SCAN_TIMEOUT"  # raised on the errorCode; findings ignored


def test_detector_empty_findings_valid() -> None:
    """Hook side of 'empty findings is valid, not an error' (detector §3.6): a clean
    scan result (NO errorCode, even with findings:[]) does NOT raise — findings:[] is a
    legitimate empty scan, never aliased to an error."""
    clean_empty = _scan_result({"findings": []})
    clean_hit = _scan_result(
        {"findings": [{"location": {"path": "a.py", "start_line": 1}, "rule_id": "BR-CPF"}]}
    )
    assert inspect_scan_diff_result(clean_empty) is None
    assert inspect_scan_diff_result(clean_hit) is None


def test_inspect_scan_diff_shape_surprise_degrades_no_raise() -> None:
    """Defensive guard: a shape surprise (non-UserMessage, missing tool_use_result, or
    missing/empty structuredContent) degrades to 'no errorCode seen' (clean path) — never
    a KeyError mid-stream. Guards the DD-d OPEN ASSUMPTION on the nested structuredContent
    shape (verified live at G2b)."""
    assert inspect_scan_diff_result(ResultMessage(  # non-UserMessage ignored
        subtype="success", duration_ms=0, duration_api_ms=0, is_error=False, num_turns=1,
        session_id="s", stop_reason="end_turn", structured_output=None,
        permission_denials=None, errors=None,
    )) is None
    assert inspect_scan_diff_result(AssistantMessage(content=[], model="m")) is None
    assert inspect_scan_diff_result(UserMessage(content="echo")) is None  # no tool_use_result
    assert inspect_scan_diff_result(UserMessage(content="x", tool_use_result={})) is None  # no sc
    assert inspect_scan_diff_result(
        UserMessage(content="x", tool_use_result={"structuredContent": {}})  # sc without errorCode
    ) is None
