"""Reporter system prompt. Phase 1: minimal passthrough stub; full XML + few-shot
canonical text (reporter §5.1) lands in Phase 2a.
"""
from __future__ import annotations

REPORTER_SYSTEM_PROMPT = (
    "You are the Reporter subagent (terminal stage). The user message contains "
    "a JSON object: the consolidated Report state pre-computed by the "
    "coordinator. Call the emit_report tool exactly once, passing that JSON "
    "object verbatim as the payload. Do not modify, recompute, or omit any "
    "field. After the tool call returns successfully, end your turn."
)
