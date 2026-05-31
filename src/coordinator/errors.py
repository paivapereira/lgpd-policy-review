"""Typed exception taxonomy for the coordinator pipeline (coordinator.md §5).

Two orthogonal axes (coordinator §5 reconciliation note):

- **Tool-error family** — `SubagentToolError` base (A2; minimal non-breaking
  introduction, hierarchy formalization stays ADR-0013 follow-up) with
  `DetectorScanFailed` as its only MVP subclass (A1/A3). Carries the verbatim
  tool envelope fields `(tool, error_code, is_retryable, details)`.
- **SDK-class + contract exceptions** — refusal, validation, unresponsiveness,
  stream failure, execution error, passthrough violation, and the Reporter
  family. These are NOT under `SubagentToolError`.

Every exception carries `stage` for blame; the coordinator projects any of
them into the external `CoordinatorError` envelope (§3.6).
"""
from __future__ import annotations

from typing import Any


class SubagentToolError(Exception):
    """Base for the MCP-tool-error family consumed by a subagent (DD-M18 / A2).

    MVP subclass: `DetectorScanFailed`. The choice between sibling exceptions
    and a shared base for future Matcher tool errors is deferred to ADR-0013;
    this base is introduced now so that decision stays non-breaking.
    """

    def __init__(self, stage: str, *, message: str | None = None) -> None:
        self.stage = stage
        super().__init__(message or f"{type(self).__name__} at stage {stage!r}")


class DetectorScanFailed(SubagentToolError):
    """`scan_diff` domain error (Option B `errorCode`) that is non-retryable, or
    retryable with the retry budget exhausted (detector §6.2, coordinator §5).

    Field signature `(stage, tool, error_code, is_retryable, details)` per the
    §5 precedent note; the rich fields are inherited verbatim from the tool
    envelope and are optional so the bare `DetectorScanFailed(stage=...)` raise
    in the §3.0bis driver also typechecks (A3).
    """

    def __init__(
        self,
        stage: str,
        *,
        tool: str | None = None,
        error_code: str | None = None,
        is_retryable: bool | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.tool = tool
        self.error_code = error_code
        self.is_retryable = is_retryable
        self.details = details
        message = f"scan_diff failed at stage {stage!r}"
        if error_code is not None:
            message += f" (errorCode={error_code!r}, isRetryable={is_retryable})"
        super().__init__(stage, message=message)


class CoordinatorStartupError(Exception):
    """`.mcp.json` whitelist failure, invalid env vars, or scratchpad creation
    failure — halt before any query (§6 Camada 1)."""

    def __init__(self, message: str, *, stage: str = "startup") -> None:
        self.stage = stage
        super().__init__(message)


class SubagentValidationFailed(Exception):
    """Subagent `structured_output` failed Pydantic validation (§3.0bis)."""

    def __init__(self, stage: str, *, raw: Any | None = None) -> None:
        self.stage = stage
        self.raw = raw
        super().__init__(f"subagent output failed Pydantic validation at stage {stage!r}")


class SubagentUnresponsive(Exception):
    """`error_max_turns` / `error_max_budget_usd` / timeout (§3.0bis). Transient."""

    def __init__(self, stage: str) -> None:
        self.stage = stage
        super().__init__(f"subagent unresponsive (timeout/budget) at stage {stage!r}")


class CoordinatorStreamFailure(Exception):
    """Exception raised during `async for` with no `ResultMessage` captured
    (§3.0bis) — a stream-level failure, distinct from a deliberate is_error exit."""

    def __init__(self, stage: str) -> None:
        self.stage = stage
        super().__init__(f"query() stream failed before any ResultMessage at stage {stage!r}")


class SubagentRefusedTask(Exception):
    """`stop_reason == 'refusal'` on a Branch B stage — checked BEFORE subtype
    (the subtype lies 'success' under refusal; §3.0bis / RESULTS.md)."""

    def __init__(self, stage: str) -> None:
        self.stage = stage
        super().__init__(f"subagent refused the task (stop_reason=='refusal') at stage {stage!r}")


class SubagentExecutionError(Exception):
    """`subtype == 'error_during_execution'` or an unexpected subtype (§3.0bis)."""

    def __init__(self, stage: str, *, detail: str | None = None) -> None:
        self.stage = stage
        self.detail = detail
        message = f"subagent execution error at stage {stage!r}"
        if detail is not None:
            message += f": {detail}"
        super().__init__(message)


class SubagentContractViolation(Exception):
    """`verify_passthrough` failed — mutation/loss/reordering (Classifier in MVP;
    Matcher deferred via G6). coordinator §5."""

    def __init__(self, stage: str, *, index: int | None = None, detail: str | None = None) -> None:
        self.stage = stage
        self.index = index
        self.detail = detail
        message = f"passthrough contract violation at stage {stage!r}"
        if index is not None:
            message += f" (index={index})"
        if detail is not None:
            message += f": {detail}"
        super().__init__(message)


class ReportNotEmitted(Exception):
    """Reporter ended its query without invoking `emit_report` (`subtype=='success'`
    AND `emit_report_seen` False AND no denials). Non-retryable (§3.5/§5)."""

    def __init__(self, *, subtype: str | None = None, stage: str = "reporter") -> None:
        self.stage = stage
        self.subtype = subtype
        super().__init__(f"Reporter ended query without emit_report (subtype={subtype!r})")


class ReporterTurnsExhausted(Exception):
    """Reporter hit `max_turns` without emitting (`subtype=='error_max_turns'`).
    Retryable with a larger budget (§5)."""

    def __init__(
        self,
        *,
        num_turns: int | None = None,
        errors: list[Any] | None = None,
        stage: str = "reporter",
    ) -> None:
        self.stage = stage
        self.num_turns = num_turns
        self.errors = errors
        super().__init__(f"Reporter exhausted max_turns without emit_report (num_turns={num_turns})")


class ReporterPermissionDenied(Exception):
    """`permission_denials` populated on the final `ResultMessage` — a lockdown
    anomaly. Strict (any denial halts), checked first (§3.5 tri-axial)."""

    def __init__(
        self,
        *,
        denials: list[Any],
        subtype: str | None = None,
        stage: str = "reporter",
    ) -> None:
        self.stage = stage
        self.denials = denials
        self.subtype = subtype
        super().__init__(f"Reporter query produced permission_denials under lockdown: {denials!r}")


class MultipleReportEmissions(Exception):
    """Reporter invoked `emit_report` more than once in one query — anti-pattern
    signalling a system_prompt bug (§5)."""

    def __init__(
        self,
        *,
        first_payload: dict[str, Any] | None = None,
        second_payload: dict[str, Any] | None = None,
        stage: str = "reporter",
    ) -> None:
        self.stage = stage
        self.first_payload = first_payload
        self.second_payload = second_payload
        super().__init__("Reporter invoked emit_report more than once in the same query")


class MalformedToolUseBlock(Exception):
    """A `ToolUseBlock` lacked the expected `.input` attribute (defensive; signals
    an SDK version below the MVP floor). coordinator §5."""

    def __init__(self, *, stage: str = "reporter") -> None:
        self.stage = stage
        super().__init__("ToolUseBlock lacked the expected '.input' attribute (SDK incompat)")
