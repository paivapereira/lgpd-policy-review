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

Defensive: the SDK relays `tool_use_result` verbatim from the CLI wire
(`_internal/message_parser.py:83`); its runtime value is `dict | None` on a healthy MCP
result but is a **string** when the server fails to spawn — and a real production timeout /
semgrep crash can also surface a non-envelope value. So ANY non-`dict` shape (str, list,
None, ...) at either level degrades to "no errorCode seen" (clean path), never an
`AttributeError`/`KeyError` mid-stream. A non-dict is not an Option-B domain envelope: infra
failures surface via the stream (`CoordinatorStreamFailure`), not as a fabricated
`DetectorScanFailed`. Confirmed live at G2b that a healthy result carries the nested
`structuredContent` dict.
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
    tool_result = message.tool_use_result
    if not isinstance(tool_result, dict):  # str (server failed to spawn) / None / etc.
        return
    structured = tool_result.get("structuredContent")
    if not isinstance(structured, dict):
        return
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
