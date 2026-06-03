"""Phase 2a acceptance + §9.2 anchors — Reporter stage (`_run_reporter_stage`,
coordinator §3.5) under a mocked SDK.

Acceptance: the coordinator captures the emitted payload verbatim via
`ToolUseBlock.input` (no recompute, §2.4), filtering intermediate non-emit_report
blocks by `block.name` (§6.7). Anchors close the §9.2 tri-axial/anti-pattern
branches whose code paths exist since Phase 1 but were untested (only the
not-emitted branch was, in test_walking_skeleton).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from claude_agent_sdk import AssistantMessage, ToolUseBlock

from coordinator.errors import (
    MalformedToolUseBlock,
    MultipleReportEmissions,
    ReportNotEmitted,
    ReporterPermissionDenied,
    ReporterTurnsExhausted,
)
from coordinator.run import _run_reporter_stage
from subagents.reporter.tools import create_reporter_server

_RUN_ID = "550e8400-e29b-41d4-a716-446655440000"
_EMIT = "mcp__reporter_tools__emit_report"

_PAYLOAD = {
    "report_id": _RUN_ID,
    "report_schema_version": "0.1.0",
    "policy_schema_version": "0.1.0",
    "policy_version": "0.1.0",
    "legal_framework": "LGPD",
    "run_outcome": "success_no_candidates",
    "triager_skip_reason": None,
    "scope": {
        "pr_number": 1,
        "base_ref": "main",
        "head_ref": "feature/x",
        "repo_url": "https://github.com/ex/app",
    },
    "summary": {
        "counts": {
            "compliant": 0,
            "violation_candidate": 0,
            "indeterminate": 0,
            "not_applicable": 0,
        },
        "total": 0,
    },
    "findings": [],
}


def _server(tmp_path: Path) -> object:
    return create_reporter_server(tmp_path, _RUN_ID)


async def test_as1_reporter_passthrough_no_recompute(tmp_path, monkeypatch, sdk) -> None:
    monkeypatch.setattr(
        "coordinator.run.query",
        sdk.make_query([sdk.assistant_tool_use(_EMIT, _PAYLOAD), sdk.result()]),
    )
    captured = await _run_reporter_stage(_PAYLOAD, _server(tmp_path), tmp_path)
    assert captured == _PAYLOAD  # captured verbatim via ToolUseBlock.input, no recompute


async def test_as2_reporter_ignores_intermediate_blocks(tmp_path, monkeypatch, sdk) -> None:
    # A non-emit_report ToolUseBlock (e.g. an SDK-injected built-in) precedes the
    # real emission; coordinator filters by block.name and captures only emit_report.
    intermediate = sdk.assistant_tool_use("mcp__some_other__probe", {"q": "x"})
    emit = sdk.assistant_tool_use(_EMIT, _PAYLOAD)
    monkeypatch.setattr("coordinator.run.query", sdk.make_query([intermediate, emit, sdk.result()]))
    captured = await _run_reporter_stage(_PAYLOAD, _server(tmp_path), tmp_path)
    assert captured == _PAYLOAD


def _double_emit_query(sdk: object) -> object:
    return sdk.make_query(
        [
            sdk.assistant_tool_use(_EMIT, _PAYLOAD),
            sdk.assistant_tool_use(_EMIT, _PAYLOAD),
            sdk.result(),
        ]
    )


async def test_reporter_second_emit_after_success_raises(tmp_path, monkeypatch, sdk) -> None:
    """§9.2.c (ADR-0016) — a 2nd emit_report when the FIRST already SUCCEEDED is genuine
    redundancy -> MultipleReportEmissions. The success signal is `99-report.json` (the
    handler's sink). The mock does NOT run the handler, so the sink is pre-created to
    simulate the first emit's success. Invariant preserved (green before and after)."""
    (tmp_path / "99-report.json").write_text("{}\n", encoding="utf-8")  # first emit succeeded
    monkeypatch.setattr("coordinator.run.query", _double_emit_query(sdk))
    with pytest.raises(MultipleReportEmissions):
        await _run_reporter_stage(_PAYLOAD, _server(tmp_path), tmp_path)


async def test_reporter_second_emit_after_failure_allowed(tmp_path, monkeypatch, sdk) -> None:
    """§9.2.a (ADR-0016) — a 2nd emit_report when the FIRST FAILED (no `99-report.json`)
    is a legitimate validation-retry, NOT redundancy -> must NOT raise
    MultipleReportEmissions. Under the mock the handler does not run, so no success sink
    is produced for the retry either; the honest outcome is `ReportNotEmitted` (no committed
    Report — the happy 'retry succeeds -> Report' path is the live smoke). RED today: the
    AS-IS guard raises MultipleReportEmissions on ANY 2nd emit, blind to handler success."""
    assert not (tmp_path / "99-report.json").exists()  # first emit failed: no success sink
    monkeypatch.setattr("coordinator.run.query", _double_emit_query(sdk))
    with pytest.raises(ReportNotEmitted):
        await _run_reporter_stage(_PAYLOAD, _server(tmp_path), tmp_path)


async def test_reporter_triaxial_permission_denied(tmp_path, monkeypatch, sdk) -> None:
    # §9.2.e — any permission_denials under lockdown => ReporterPermissionDenied,
    # checked FIRST in the tri-axial ordering (denials -> subtype -> emit_seen).
    monkeypatch.setattr(
        "coordinator.run.query",
        sdk.make_query([sdk.result(subtype="success", permission_denials=[{"tool": "Bash"}])]),
    )
    with pytest.raises(ReporterPermissionDenied):
        await _run_reporter_stage(_PAYLOAD, _server(tmp_path), tmp_path)


async def test_reporter_turns_exhausted(tmp_path, monkeypatch, sdk) -> None:
    # §9.2.b — subtype="error_max_turns" without emit_report => ReporterTurnsExhausted.
    monkeypatch.setattr(
        "coordinator.run.query",
        sdk.make_query([sdk.result(subtype="error_max_turns", num_turns=3)]),
    )
    with pytest.raises(ReporterTurnsExhausted):
        await _run_reporter_stage(_PAYLOAD, _server(tmp_path), tmp_path)


async def test_reporter_malformed_tooluseblock(tmp_path, monkeypatch, sdk) -> None:
    # §9.2.f — defensive: an emit_report ToolUseBlock missing `.input` (SDK version
    # incompat) => MalformedToolUseBlock. Build via __new__ to omit `.input` robustly
    # (works whether the dataclass is frozen/slotted), keeping isinstance(.,ToolUseBlock).
    block = ToolUseBlock.__new__(ToolUseBlock)
    object.__setattr__(block, "id", "tu-x")
    object.__setattr__(block, "name", _EMIT)
    # .input deliberately absent
    msg = AssistantMessage(content=[block], model="test-model")
    monkeypatch.setattr("coordinator.run.query", sdk.make_query([msg, sdk.result()]))
    with pytest.raises(MalformedToolUseBlock):
        await _run_reporter_stage(_PAYLOAD, _server(tmp_path), tmp_path)
