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
import re
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

# Cross-check #1: policy_clause_ref shape, all four verdicts (reporter §4.8 #1).
_CLAUSE_REF_PATTERN = re.compile(r"^POL-\d{3}$")


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


def _error_envelope(
    *, error_code: str, message: str, is_retryable: bool, details: dict[str, Any]
) -> dict[str, Any]:
    """Structured error for the @tool handler. Per `.claude/rules/sdk-mcp-conventions.md`
    Eixo 2 (verified in scripts/smoke_tests/sdk_tool_error_channel v1/v2), the SDK
    bridge DROPS `structuredContent` for in-process @tool servers — only `content`
    + the `is_error` flag survive. So the structured payload is serialized into
    `content` as a JSON string and `is_error` (snake_case Python idiom; SDK maps to
    camelCase `isError` on the wire) is the discriminator. The model reads errorCode
    and details from `content` to retry (REPORTER_SYSTEM_PROMPT §5.1 constraints)."""
    structured = {
        "errorCode": error_code,
        "message": message,
        "isRetryable": is_retryable,
        "details": details,
    }
    return {
        "content": [{"type": "text", "text": json.dumps(structured, ensure_ascii=False)}],
        "is_error": True,
    }


def _validation_error_envelope(exc: ValidationError) -> dict[str, Any]:
    # PYDANTIC_VALIDATION is validation-class, isRetryable=False (reporter §6.3).
    # Exclude input values from details (privacy-safety.md: payload values may be PII;
    # loc/type/msg suffice for the model to correct the field).
    return _error_envelope(
        error_code="PYDANTIC_VALIDATION",
        message="Report payload falhou na validação de schema.",
        is_retryable=False,
        details={"errors": exc.errors(include_url=False, include_input=False)},
    )


def _run_cross_checks(payload: ReportPayload) -> dict[str, Any] | None:
    """Intra-handler cross-checks #1-#3 (reporter §4.8), in order. Returns an error
    envelope on the first violation, else None. All are validation-class,
    isRetryable=False (§6.3)."""
    # #1 — policy_clause_ref format, all findings (CLAUSE_REF_FORMAT).
    for finding in payload.findings:
        if not _CLAUSE_REF_PATTERN.match(finding.policy_clause_ref):
            return _error_envelope(
                error_code="CLAUSE_REF_FORMAT",
                message=(
                    f"policy_clause_ref {finding.policy_clause_ref!r} não casa o "
                    "formato POL-NNN."
                ),
                is_retryable=False,
                details={
                    "file": finding.file,
                    "line": finding.line,
                    "policy_clause_ref": finding.policy_clause_ref,
                },
            )

    # #2 — provenance trinca top-level == per-finding (PROVENANCE_MISMATCH).
    top_trinca = (
        payload.policy_schema_version,
        payload.policy_version,
        payload.legal_framework,
    )
    for finding in payload.findings:
        finding_trinca = (
            finding.policy_schema_version,
            finding.policy_version,
            finding.legal_framework,
        )
        if finding_trinca != top_trinca:
            return _error_envelope(
                error_code="PROVENANCE_MISMATCH",
                message=(
                    "Trinca de proveniência per-finding diverge do top-level "
                    f"(top={top_trinca}, finding={finding_trinca})."
                ),
                is_retryable=False,
                details={"file": finding.file, "line": finding.line},
            )

    # #3a — declared counts == aggregation of findings by verdict.
    aggregation = {
        "compliant": sum(1 for f in payload.findings if f.verdict == "compliant"),
        "violation_candidate": sum(
            1 for f in payload.findings if f.verdict == "violation_candidate"
        ),
        "indeterminate": sum(1 for f in payload.findings if f.verdict == "indeterminate"),
        "not_applicable": sum(1 for f in payload.findings if f.verdict == "not_applicable"),
    }
    if payload.summary.counts.model_dump() != aggregation:
        return _error_envelope(
            error_code="COUNTS_DISAGREE_WITH_FINDINGS",
            message="summary.counts não casa com a agregação real dos findings por verdict.",
            is_retryable=False,
            details={"declared": payload.summary.counts.model_dump(), "aggregated": aggregation},
        )

    # #3b — total == sum(counts.values()).
    counts_sum = sum(payload.summary.counts.model_dump().values())
    if payload.summary.total != counts_sum:
        return _error_envelope(
            error_code="TOTAL_NOT_SUM_OF_COUNTS",
            message=(
                f"summary.total ({payload.summary.total}) ≠ soma dos counts ({counts_sum})."
            ),
            is_retryable=False,
            details={"total": payload.summary.total, "sum_of_counts": counts_sum},
        )

    return None


async def emit_report_impl(
    args: dict[str, Any], *, run_path: Path, expected_report_id: str
) -> dict[str, Any]:
    """Pure handler body (reporter §4.8 Step 1-5), extracted from the `@tool` closure
    so the cross-checks + dual-sink are unit-testable without the SDK bridge."""
    # Step 1 — Pydantic validation.
    try:
        payload = ReportPayload.model_validate(args)
    except ValidationError as exc:
        return _validation_error_envelope(exc)

    # Step 2 — cross-check #4: report_id matches expected (closure capture).
    if payload.report_id != expected_report_id:
        return _error_envelope(
            error_code="REPORT_ID_MISMATCH",
            message=(
                f"report_id {payload.report_id!r} não corresponde ao esperado "
                f"{expected_report_id!r}."
            ),
            is_retryable=False,
            details={"expected": expected_report_id, "got": payload.report_id},
        )

    # Step 3 — intra-handler cross-checks #1-#3.
    cross_check_error = _run_cross_checks(payload)
    if cross_check_error is not None:
        return cross_check_error

    # Step 4 — atomic write-then-rename.
    report_path = run_path / "99-report.json"
    _atomic_write_json(report_path, payload.model_dump(mode="json"))

    # Step 5 — success envelope.
    return _success_envelope(
        report_id=payload.report_id, path=report_path, finding_count=len(payload.findings)
    )


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
        return await emit_report_impl(
            args, run_path=run_path, expected_report_id=expected_report_id
        )

    return create_sdk_mcp_server(name="reporter_tools", version="0.1.0", tools=[emit_report_handler])
