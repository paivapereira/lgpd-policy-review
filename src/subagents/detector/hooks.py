"""Detector `scan_diff` stream-inspection hook (detector.md §6.2 / coordinator §3.2, §5).

The deterministic, model-independent backstop for `scan_diff` domain errors. Under
Option B (sdk-mcp-conventions Eixo 2) the wire `isError` is always `false`; the
discriminator is the presence of `errorCode` in
`UserMessage.tool_use_result["structuredContent"]`. `ToolResultBlock.content` carries
only the JSON string and is NOT inspected.

DD-d (ratified — escalate-all): every `errorCode` escalates as `DetectorScanFailed`
carrying `error_code` / `is_retryable` / `details` verbatim, so nothing leaks as a
fabricated/empty finding (the invariant the with-findings anchor pins). `is_retryable`
is a classified field carried for a future consumer — the retry-under-budget loop
mandated by coordinator §5 l.428 + detector §6.2 is DEFERRED to Fase 3 (registered debt);
until then a retryable scan error fails the run.

Defensive: a shape surprise (non-UserMessage, missing `tool_use_result`, missing/empty
`structuredContent`) degrades to "no errorCode seen" (clean path) — never a `KeyError`
mid-stream. The nested `structuredContent` shape is verified live at G2b.
"""
from __future__ import annotations

from typing import Any

from claude_agent_sdk import UserMessage

from coordinator.errors import DetectorScanFailed
from subagents.detector.constants import SCAN_DIFF_TOOL_NAME


def inspect_scan_diff_result(message: Any) -> None:
    """Raise `DetectorScanFailed` if `message` is a `scan_diff` Option-B error envelope;
    otherwise return None (success, empty scan, a `Read` result, or any non-tool message —
    `findings:[]` never aliases an error)."""
    if not isinstance(message, UserMessage):
        return
    tool_result = message.tool_use_result or {}
    structured = tool_result.get("structuredContent") or {}
    error_code = structured.get("errorCode")
    if error_code is None:
        return
    raise DetectorScanFailed(
        stage="detector",
        tool=SCAN_DIFF_TOOL_NAME,
        error_code=error_code,
        is_retryable=bool(structured.get("isRetryable", False)),
        details=structured.get("details"),
    )
