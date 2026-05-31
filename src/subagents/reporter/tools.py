"""`emit_report` in-process MCP tool factory (coordinator §7, reporter §4.8).

Factory + closure: the handler must capture `run_path` (to write 99-report.json,
dual-sink #1) and `expected_report_id` (cross-check #4) — impossible with a
module-level `@tool`. Built via `create_sdk_mcp_server` (NOT FastMCP) because the
closure needs shared Python scope (reporter §1.5).

Phase 1 (walking skeleton): the handler validates the payload, writes the file
atomically, and returns the ack envelope. The four intra-handler cross-checks
(#1 clause_ref regex, #2 trinca equality, #3 counts/total, #4 report_id match)
land in Phase 2a; here only Pydantic validation + write + ack run.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    McpSdkServerConfig,
    ToolAnnotations,
    create_sdk_mcp_server,
    tool,
)
from pydantic import ValidationError

from subagents.reporter.constants import EMIT_REPORT_DESCRIPTION
from subagents.reporter.models import ReportPayload


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Write-then-rename via os.replace (Windows-native atomic; reporter §4.9)."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    os.replace(tmp, path)


def _success_envelope(*, report_id: str, path: Path, finding_count: int) -> dict[str, Any]:
    return {
        "content": [
            {"type": "text", "text": f"Report emitted: report_id={report_id}, findings={finding_count}"}
        ],
        "structuredContent": {
            "report_id": report_id,
            "path": str(path),
            "finding_count": finding_count,
        },
    }


def _validation_error_envelope(exc: ValidationError) -> dict[str, Any]:
    # SDK @tool handler uses snake_case is_error (sdk-mcp-conventions.md); the SDK
    # normalizes to camelCase isError on the wire. Option-B-style structured error.
    return {
        "content": [{"type": "text", "text": "Report payload failed validation."}],
        "structuredContent": {
            "errorCode": "PYDANTIC_VALIDATION",
            "message": str(exc),
            "isRetryable": True,
            "details": {},
        },
        "is_error": True,
    }


def create_reporter_server(run_path: Path, expected_report_id: str) -> McpSdkServerConfig:
    """Build the in-process `reporter_tools` server scoped to one run. Closure
    captures `run_path` + `expected_report_id` (the latter used by cross-check #4,
    Phase 2a)."""

    @tool(
        "emit_report",
        EMIT_REPORT_DESCRIPTION,
        ReportPayload.model_json_schema(),
        ToolAnnotations(
            readOnlyHint=False,  # writes 99-report.json (sink #1)
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )
    async def emit_report_handler(args: dict[str, Any]) -> dict[str, Any]:
        try:
            payload = ReportPayload.model_validate(args)
        except ValidationError as exc:
            return _validation_error_envelope(exc)
        # Phase 2a will insert cross-checks #1-#4 here (before the write).
        report_path = run_path / "99-report.json"
        _atomic_write_json(report_path, payload.model_dump(mode="json"))
        return _success_envelope(
            report_id=payload.report_id, path=report_path, finding_count=len(payload.findings)
        )

    return create_sdk_mcp_server(name="reporter_tools", version="0.1.0", tools=[emit_report_handler])
