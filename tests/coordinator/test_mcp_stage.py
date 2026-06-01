"""Phase 3 anchors — the streaming `ClaudeSDKClient` MCP-stage driver `_run_mcp_stage`
(coordinator §3.0bis, ADR-0014 D1 readiness + D2 recovery).

These exercise ONLY what the new transport adds over the preserved discrimination tail (the
tail itself is anchored by `test_driver.py`): wait-for-connected before acting (D1), in-session
reconnect-and-retry on a RETRYABLE consumption-phase `DetectorScanFailed` (D2), readiness
timeout -> `CoordinatorStreamFailure` (D4), and the boundary policy that a STRUCTURED VERDICT
(refusal/subtype/validation) propagates with NO reconnect because `_discriminate_and_capture`
is called OUTSIDE the retry try.

Patch target: `coordinator.driver.ClaudeSDKClient` (the mock client, ADR-0014 D5). The mock
shapes mirror `d1_mock_fidelity_smoke.py` verbatim. Readiness sleeps are neutralized
(`READINESS_POLL_S=0`) so the timeout test is instant rather than ~20 s.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from claude_agent_sdk import ClaudeAgentOptions

from coordinator import driver
from coordinator.driver import _run_mcp_stage
from coordinator.errors import (
    CoordinatorStreamFailure,
    DetectorScanFailed,
    SubagentRefusedTask,
)
from subagents.detector.hooks import inspect_scan_diff_result
from subagents.detector.models import DetectorOutput
from subagents.triager.models import TriagerDecision

_DETECTOR_OUT = {
    "findings": [
        {"file": "a.py", "line": 1, "rule_id": "BR-CPF", "snippet": "cpf=x", "surrounding_context": "# c"}
    ],
    "provenance": {
        "rules_version": "2026.04.1",
        "semgrep_version": "1.163.0",
        "scan_metadata": {"base_ref": "a" * 40, "head_ref": "b" * 40, "files_scanned": 1, "elapsed_seconds": 1.0},
    },
}
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


async def _run_detector(tmp_path: Path, *, retries: int) -> Any:
    """Detector stage through `_run_mcp_stage` (semgrep-runner target + scan-error hook)."""
    return await _run_mcp_stage(
        stage="detector",
        prompt="p",
        options=_opts(),
        output_model=DetectorOutput,
        scratchpad_name="02-detector.json",
        run_path=tmp_path,
        run_id="r1",
        target="semgrep-runner",
        retries=retries,
        on_tool_result=inspect_scan_diff_result,
    )


async def test_readiness_timeout_stuck_pending_raises_stream_failure(tmp_path, monkeypatch, sdk) -> None:
    # D4: target never reaches 'connected' within the budget -> CoordinatorStreamFailure, and
    # the stage never acted (no query, no reconnect).
    monkeypatch.setattr(driver, "READINESS_POLL_S", 0)
    monkeypatch.setattr(driver, "READINESS_ATTEMPTS", 3)
    cls, state = sdk.mcp_client(
        attempts=[[sdk.result(subtype="success", structured_output=_DETECTOR_OUT)]],
        statuses=["pending"],
    )
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)
    with pytest.raises(CoordinatorStreamFailure):
        await _run_detector(tmp_path, retries=driver.RETRY_BUDGET)
    assert state["queries"] == 0
    assert state["reconnects"] == 0


async def test_readiness_waits_pending_then_connected(tmp_path, monkeypatch, sdk) -> None:
    # D1: the stage WAITS through 'pending' polls and acts only once 'connected'.
    monkeypatch.setattr(driver, "READINESS_POLL_S", 0)
    cls, state = sdk.mcp_client(
        attempts=[[sdk.result(subtype="success", structured_output=_DETECTOR_OUT)]],
        statuses=["pending", "pending", "connected"],
    )
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)
    out = await _run_detector(tmp_path, retries=driver.RETRY_BUDGET)
    assert isinstance(out, DetectorOutput)
    assert state["queries"] == 1  # acted once, after readiness resolved; no retry
    assert state["reconnects"] == 0


async def test_readiness_reconnects_on_failed_then_connects(tmp_path, monkeypatch, sdk) -> None:
    # D1(b): a 'failed' status during the readiness wait triggers a reconnect, then connects.
    monkeypatch.setattr(driver, "READINESS_POLL_S", 0)
    cls, state = sdk.mcp_client(
        attempts=[[sdk.result(subtype="success", structured_output=_DETECTOR_OUT)]],
        statuses=["failed", "connected"],
    )
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)
    out = await _run_detector(tmp_path, retries=driver.RETRY_BUDGET)
    assert isinstance(out, DetectorOutput)
    assert state["reconnects"] == 1


async def test_as1_retryable_scan_timeout_retries_then_succeeds(tmp_path, monkeypatch, sdk) -> None:
    # D2: a retryable SCAN_TIMEOUT on attempt 0 -> EXACTLY ONE in-session reconnect (no
    # re-spawn) + re-issued prompt -> success on attempt 1. RETRY_BUDGET=1 -> 2 attempts.
    monkeypatch.setattr(driver, "READINESS_POLL_S", 0)
    cls, state = sdk.mcp_client(
        attempts=[
            [sdk.scan_error("SCAN_TIMEOUT", is_retryable=True)],
            [sdk.result(subtype="success", structured_output=_DETECTOR_OUT)],
        ],
    )
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)
    out = await _run_detector(tmp_path, retries=driver.RETRY_BUDGET)
    assert isinstance(out, DetectorOutput)
    assert state["reconnects"] == 1  # exactly one reconnect, in-session
    assert state["queries"] == 2  # prompt re-issued on the SAME open session
    assert "BR-CPF" in (tmp_path / "02-detector.json").read_text(encoding="utf-8")


async def test_as2_retry_exhausted_escalates(tmp_path, monkeypatch, sdk) -> None:
    # D2: retryable on every attempt -> one reconnect, then the budget is exhausted and
    # DetectorScanFailed escalates (loud + typed, never a silent findings=[]).
    monkeypatch.setattr(driver, "READINESS_POLL_S", 0)
    cls, state = sdk.mcp_client(
        attempts=[
            [sdk.scan_error("SCAN_TIMEOUT", is_retryable=True)],
            [sdk.scan_error("SCAN_TIMEOUT", is_retryable=True)],
        ],
    )
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)
    with pytest.raises(DetectorScanFailed):
        await _run_detector(tmp_path, retries=driver.RETRY_BUDGET)
    assert state["reconnects"] == 1  # one retry, then escalate


async def test_non_retryable_scan_error_escalates_without_reconnect(tmp_path, monkeypatch, sdk) -> None:
    # D2 is isRetryable-driven, NOT exception-type-driven: a non-retryable scan error escalates
    # immediately, no reconnect — even with a retry budget available.
    monkeypatch.setattr(driver, "READINESS_POLL_S", 0)
    cls, state = sdk.mcp_client(
        attempts=[[sdk.scan_error("GIT_REF_NOT_FOUND", is_retryable=False)]],
    )
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)
    with pytest.raises(DetectorScanFailed):
        await _run_detector(tmp_path, retries=driver.RETRY_BUDGET)
    assert state["reconnects"] == 0


async def test_result_then_raise_falls_through_to_discrimination(tmp_path, monkeypatch, sdk) -> None:
    # Arm B (ADR-0014 D2 rider): a ResultMessage captured THEN a late stream raise is a
    # deliberate post-result exit -> last_result authoritative -> discrimination proceeds, NOT
    # CoordinatorStreamFailure. Mirrors test_driver_result_then_raise_falls_through for the
    # streaming transport — the path NO e2e drives, so it would regress silently without this.
    monkeypatch.setattr(driver, "READINESS_POLL_S", 0)
    cls, state = sdk.mcp_client(
        attempts=[[sdk.result(subtype="success", structured_output=_SKIP_OUTPUT)]],
        raise_after=RuntimeError("late"),
    )
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)
    out = await _run_mcp_stage(
        stage="detector",
        prompt="p",
        options=_opts(),
        output_model=TriagerDecision,
        scratchpad_name="02-detector.json",
        run_path=tmp_path,
        run_id="r1",
        target="semgrep-runner",
        retries=driver.RETRY_BUDGET,
    )
    assert isinstance(out, TriagerDecision)
    assert out.decision == "skip"
    assert state["reconnects"] == 0  # a post-result exit is not a retryable transport failure


async def test_late_raise_without_result_is_stream_failure(tmp_path, monkeypatch, sdk) -> None:
    # Arm B, no-result branch: a stream raise with NO ResultMessage captured is a real stream
    # failure -> CoordinatorStreamFailure (mirrors test_driver_stream_failure_when_no_result).
    monkeypatch.setattr(driver, "READINESS_POLL_S", 0)
    cls, state = sdk.mcp_client(attempts=[[]], raise_after=RuntimeError("boom"))
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)
    with pytest.raises(CoordinatorStreamFailure):
        await _run_mcp_stage(
            stage="detector",
            prompt="p",
            options=_opts(),
            output_model=TriagerDecision,
            scratchpad_name="02-detector.json",
            run_path=tmp_path,
            run_id="r1",
            target="semgrep-runner",
            retries=0,
        )
    assert state["reconnects"] == 0


async def test_refusal_verdict_propagates_without_reconnect(tmp_path, monkeypatch, sdk) -> None:
    # ADR-0014 D2 rider / the try boundary: a STRUCTURED VERDICT raised by the discrimination
    # tail (here refusal) propagates immediately — NO reconnect, even with a retry budget —
    # because _discriminate_and_capture sits OUTSIDE the retry try. Reconnect recovers an
    # unstable transport, never a verdict.
    monkeypatch.setattr(driver, "READINESS_POLL_S", 0)
    cls, state = sdk.mcp_client(
        attempts=[[sdk.result(subtype="success", stop_reason="refusal", structured_output=None)]],
    )
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)
    with pytest.raises(SubagentRefusedTask):
        await _run_detector(tmp_path, retries=driver.RETRY_BUDGET)
    assert state["reconnects"] == 0


async def test_stage_timeout_on_hung_stream_raises_stream_failure(tmp_path, monkeypatch, sdk) -> None:
    # ADR-0014 D1 step 4 / D4: receive_response() hangs without a terminal ResultMessage -> the
    # stage timeout bounds it -> CoordinatorStreamFailure. A hang is NOT a retryable scan error,
    # so it is never retried even with a budget. STAGE_TIMEOUT_S is shrunk so the test is instant.
    monkeypatch.setattr(driver, "READINESS_POLL_S", 0)
    monkeypatch.setattr(driver, "STAGE_TIMEOUT_S", 0.05)
    cls, state = sdk.mcp_client(attempts=[[]], hang=True)
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)
    with pytest.raises(CoordinatorStreamFailure):
        await _run_detector(tmp_path, retries=driver.RETRY_BUDGET)
    assert state["reconnects"] == 0


async def test_stage_timeout_with_result_captured_still_halts(tmp_path, monkeypatch, sdk) -> None:
    # Achado 2 / option (a): a stage timeout is ALWAYS a hard halt. Even when a ResultMessage was
    # already captured, the explicit `except TimeoutError` raises CoordinatorStreamFailure — it
    # does NOT fall through to _discriminate_and_capture like arm B's deliberate post-result exit.
    # Defensive: in production receive_response() self-terminates ON a ResultMessage, so a timeout
    # implies none was seen; this anchors that the branch is handled regardless of last_result.
    monkeypatch.setattr(driver, "READINESS_POLL_S", 0)
    monkeypatch.setattr(driver, "STAGE_TIMEOUT_S", 0.05)
    cls, state = sdk.mcp_client(
        attempts=[[sdk.result(subtype="success", structured_output=_SKIP_OUTPUT)]],
        hang=True,  # yields the result, THEN hangs -> timeout fires WITH last_result set
    )
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)
    with pytest.raises(CoordinatorStreamFailure):
        await _run_mcp_stage(
            stage="detector",
            prompt="p",
            options=_opts(),
            output_model=TriagerDecision,
            scratchpad_name="02-detector.json",
            run_path=tmp_path,
            run_id="r1",
            target="semgrep-runner",
            retries=0,
        )
    assert state["reconnects"] == 0


async def test_reconnect_failure_during_retry_is_typed_stream_failure(tmp_path, monkeypatch, sdk) -> None:
    # Achado 1 (D2 completeness): the recovery action of the recovery feature must have a TYPED
    # failure outcome. If reconnect_mcp_server() raises (dead transport), the retry path raises
    # CoordinatorStreamFailure(stage) — NOT an untyped exception that degrades to a generic
    # CoordinatorError(stage="coordinator") at the top handler, losing stage attribution.
    monkeypatch.setattr(driver, "READINESS_POLL_S", 0)
    cls, state = sdk.mcp_client(
        attempts=[
            [sdk.scan_error("SCAN_TIMEOUT", is_retryable=True)],
            [sdk.result(subtype="success", structured_output=_DETECTOR_OUT)],
        ],
        reconnect_raises=RuntimeError("mcp reconnect failed"),
    )
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)
    with pytest.raises(CoordinatorStreamFailure):
        await _run_detector(tmp_path, retries=driver.RETRY_BUDGET)
    assert state["reconnects"] == 1  # the reconnect was attempted (and raised)


async def test_reconnect_failure_during_readiness_is_typed_stream_failure(tmp_path, monkeypatch, sdk) -> None:
    # Achado 1, the readiness call site: a 'failed' status triggers reconnect in
    # _wait_for_connected; a raising reconnect there is likewise a TYPED CoordinatorStreamFailure,
    # not a bare untyped propagation.
    monkeypatch.setattr(driver, "READINESS_POLL_S", 0)
    cls, state = sdk.mcp_client(
        attempts=[[sdk.result(subtype="success", structured_output=_DETECTOR_OUT)]],
        statuses=["failed"],
        reconnect_raises=RuntimeError("mcp reconnect failed"),
    )
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)
    with pytest.raises(CoordinatorStreamFailure):
        await _run_detector(tmp_path, retries=driver.RETRY_BUDGET)
    assert state["reconnects"] == 1
