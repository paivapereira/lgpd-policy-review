"""Phase 0 anchors — coordinator exception taxonomy (coordinator.md §5 + A1/A2/A3).

The §5 table freezes 13 typed exceptions; A2 introduces the base
`SubagentToolError` for the tool-error family (DetectorScanFailed + future
Matcher tool errors), making 14. `UnsupportedLegalFramework` (framework guard,
ADR-0007) brings it to 15; the coordinator.md §5 table update is tracked as a
docs débito (source-of-truth-precedence). Every exception carries `stage` for
blame. These are strict anchors: the exact name set and the subclass
relationship are the contract, not an incidental fact of the module.
"""
from __future__ import annotations

import pytest

from coordinator import errors

EXPECTED_EXCEPTIONS = {
    "SubagentToolError",
    "DetectorScanFailed",
    "CoordinatorStartupError",
    "SubagentValidationFailed",
    "SubagentUnresponsive",
    "CoordinatorStreamFailure",
    "ReportNotEmitted",
    "ReporterTurnsExhausted",
    "ReporterPermissionDenied",
    "MultipleReportEmissions",
    "MalformedToolUseBlock",
    "SubagentRefusedTask",
    "SubagentExecutionError",
    "SubagentContractViolation",
    "UnsupportedLegalFramework",
}


def test_errors_taxonomy_complete() -> None:
    present = {name for name in EXPECTED_EXCEPTIONS if isinstance(getattr(errors, name, None), type)}
    assert present == EXPECTED_EXCEPTIONS
    # A2: tool-error family base; DetectorScanFailed is its only MVP subclass.
    assert issubclass(errors.SubagentToolError, Exception)
    assert issubclass(errors.DetectorScanFailed, errors.SubagentToolError)
    # The SDK-class exceptions are a distinct axis, NOT under SubagentToolError.
    assert not issubclass(errors.SubagentValidationFailed, errors.SubagentToolError)
    assert not issubclass(errors.SubagentRefusedTask, errors.SubagentToolError)


def test_detector_scan_failed_rich_field_signature() -> None:
    # A3: rich signature so both call sites typecheck.
    e = errors.DetectorScanFailed(
        stage="detector",
        tool="scan_diff",
        error_code="GIT_REF_NOT_FOUND",
        is_retryable=False,
        details={"ref": "main"},
    )
    assert e.stage == "detector"
    assert e.tool == "scan_diff"
    assert e.error_code == "GIT_REF_NOT_FOUND"
    assert e.is_retryable is False
    assert e.details == {"ref": "main"}


def test_detector_scan_failed_minimal_stage_only() -> None:
    # §3.0bis raises `DetectorScanFailed(stage=stage)` with no rich fields.
    e = errors.DetectorScanFailed(stage="detector")
    assert e.stage == "detector"
    assert e.tool is None
    assert e.error_code is None


@pytest.mark.parametrize(
    "factory, expected_stage",
    [
        (lambda: errors.SubagentValidationFailed(stage="triager"), "triager"),
        (lambda: errors.SubagentUnresponsive(stage="detector"), "detector"),
        (lambda: errors.CoordinatorStreamFailure(stage="classifier"), "classifier"),
        (lambda: errors.SubagentRefusedTask(stage="matcher"), "matcher"),
        (lambda: errors.SubagentExecutionError(stage="detector"), "detector"),
        (lambda: errors.SubagentContractViolation(stage="classifier"), "classifier"),
        (lambda: errors.DetectorScanFailed(stage="detector"), "detector"),
        (lambda: errors.CoordinatorStartupError("boom"), "startup"),
        (lambda: errors.ReportNotEmitted(), "reporter"),
        (lambda: errors.ReporterTurnsExhausted(), "reporter"),
        (lambda: errors.ReporterPermissionDenied(denials=[{"tool": "x"}]), "reporter"),
        (lambda: errors.MultipleReportEmissions(), "reporter"),
        (lambda: errors.MalformedToolUseBlock(), "reporter"),
        (lambda: errors.UnsupportedLegalFramework("GDPR"), "framework_guard"),
    ],
)
def test_every_exception_carries_stage(factory, expected_stage) -> None:
    e = factory()
    assert isinstance(e, Exception)
    assert e.stage == expected_stage


def test_reporter_exception_payload_fields() -> None:
    turns = errors.ReporterTurnsExhausted(num_turns=4, errors=["timeout"])
    assert turns.num_turns == 4
    assert turns.errors == ["timeout"]

    denied = errors.ReporterPermissionDenied(denials=[{"tool": "emit_report"}], subtype="success")
    assert denied.denials == [{"tool": "emit_report"}]
    assert denied.subtype == "success"

    multi = errors.MultipleReportEmissions(first_payload={"a": 1}, second_payload={"b": 2})
    assert multi.first_payload == {"a": 1}
    assert multi.second_payload == {"b": 2}

    not_emitted = errors.ReportNotEmitted(subtype="success")
    assert not_emitted.subtype == "success"
