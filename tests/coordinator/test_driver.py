"""Phase 1 anchors — the Branch B driver `run_branch_b_stage` (coordinator §3.0bis).

The load-bearing capture/discrimination spine: ResultMessage captured with NO
break (trailing events consumed); `stop_reason=='refusal'` checked BEFORE the
subtype match (the subtype lies 'success' under refusal); subtype -> typed
exception matrix; success -> validate + optional verify_passthrough + scratchpad.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from claude_agent_sdk import ClaudeAgentOptions

from coordinator import driver
from coordinator.errors import (
    CoordinatorStreamFailure,
    SubagentContractViolation,
    SubagentExecutionError,
    SubagentRefusedTask,
    SubagentUnresponsive,
    SubagentValidationFailed,
)
from subagents.triager.models import TriagerDecision

_SKIP_OUTPUT = {"decision": "skip", "skip_reason": "docs-only"}


def _opts() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt="x",
        tools=[],
        allowed_tools=[],
        mcp_servers={},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
    )


async def _run(tmp_path: Path, **over: Any) -> Any:
    kw: dict[str, Any] = dict(
        stage="triager",
        prompt="p",
        options=_opts(),
        output_model=TriagerDecision,
        scratchpad_name="01-triager.json",
        run_path=tmp_path,
        run_id="r1",
    )
    kw.update(over)
    return await driver.run_branch_b_stage(**kw)


async def test_driver_success_validates_and_writes(tmp_path, monkeypatch, sdk) -> None:
    monkeypatch.setattr(
        "coordinator.driver.query",
        sdk.make_query([sdk.result(subtype="success", structured_output=_SKIP_OUTPUT)]),
    )
    obj = await _run(tmp_path)
    assert isinstance(obj, TriagerDecision)
    assert obj.decision == "skip"
    written = json.loads((tmp_path / "01-triager.json").read_text(encoding="utf-8"))
    assert written["decision"] == "skip"


async def test_driver_captures_last_result_no_break(tmp_path, monkeypatch, sdk) -> None:
    seen: list[Any] = []
    monkeypatch.setattr(
        "coordinator.driver.query",
        sdk.make_query(
            [sdk.result(subtype="success", structured_output=_SKIP_OUTPUT), sdk.system()]
        ),
    )
    obj = await _run(tmp_path, on_tool_result=seen.append)
    # the SystemMessage AFTER the ResultMessage was consumed -> no early break
    assert any(type(m).__name__ == "SystemMessage" for m in seen)
    assert isinstance(obj, TriagerDecision)


async def test_driver_refusal_precedes_subtype(tmp_path, monkeypatch, sdk) -> None:
    monkeypatch.setattr(
        "coordinator.driver.query",
        sdk.make_query(
            [sdk.result(subtype="success", stop_reason="refusal", structured_output=None)]
        ),
    )
    with pytest.raises(SubagentRefusedTask):
        await _run(tmp_path)


async def test_driver_stream_failure_when_no_result(tmp_path, monkeypatch, sdk) -> None:
    monkeypatch.setattr(
        "coordinator.driver.query", sdk.make_query([], raise_after=RuntimeError("boom"))
    )
    with pytest.raises(CoordinatorStreamFailure):
        await _run(tmp_path)


async def test_driver_result_then_raise_falls_through(tmp_path, monkeypatch, sdk) -> None:
    # ResultMessage captured THEN the stream raises -> deliberate post-result exit;
    # last_result is authoritative, discrimination proceeds (no StreamFailure).
    monkeypatch.setattr(
        "coordinator.driver.query",
        sdk.make_query(
            [sdk.result(subtype="success", structured_output=_SKIP_OUTPUT)],
            raise_after=RuntimeError("late"),
        ),
    )
    obj = await _run(tmp_path)
    assert obj.decision == "skip"


@pytest.mark.parametrize(
    "subtype, exc",
    [
        ("error_max_turns", SubagentUnresponsive),
        ("error_max_budget_usd", SubagentUnresponsive),
        ("error_during_execution", SubagentExecutionError),
        ("error_max_structured_output_retries", SubagentValidationFailed),
        ("some_unexpected_subtype", SubagentExecutionError),
    ],
)
async def test_driver_subtype_to_exception_matrix(tmp_path, monkeypatch, sdk, subtype, exc) -> None:
    monkeypatch.setattr(
        "coordinator.driver.query",
        sdk.make_query([sdk.result(subtype=subtype, stop_reason="end_turn", structured_output=None)]),
    )
    with pytest.raises(exc):
        await _run(tmp_path)


async def test_driver_validation_failure_on_bad_output(tmp_path, monkeypatch, sdk) -> None:
    monkeypatch.setattr(
        "coordinator.driver.query",
        sdk.make_query([sdk.result(subtype="success", structured_output={"decision": "bogus"})]),
    )
    with pytest.raises(SubagentValidationFailed):
        await _run(tmp_path)


async def test_driver_verify_passthrough_invoked(tmp_path, monkeypatch, sdk) -> None:
    calls: list[tuple[Any, Any]] = []
    monkeypatch.setattr(
        "coordinator.driver.query",
        sdk.make_query([sdk.result(subtype="success", structured_output=_SKIP_OUTPUT)]),
    )
    await _run(tmp_path, verify_passthrough=lambda obj, up: calls.append((obj, up)), upstream=["x"])
    assert len(calls) == 1
    assert calls[0][1] == ["x"]


async def test_driver_verify_passthrough_can_raise(tmp_path, monkeypatch, sdk) -> None:
    def verify(obj: Any, upstream: Any) -> None:
        raise SubagentContractViolation(stage="classifier", index=0)

    monkeypatch.setattr(
        "coordinator.driver.query",
        sdk.make_query([sdk.result(subtype="success", structured_output=_SKIP_OUTPUT)]),
    )
    with pytest.raises(SubagentContractViolation):
        await _run(tmp_path, stage="classifier", verify_passthrough=verify, upstream=[])
