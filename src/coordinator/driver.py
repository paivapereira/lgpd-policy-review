"""Branch B stage drivers (coordinator.md §3.0bis) + scratchpad writer (§4).

Two transports share ONE capture/discrimination tail (`_discriminate_and_capture`):

- `run_branch_b_stage` — one-shot `query()`, for stages with NO subprocess-MCP cold-start
  race (the Triager, `mcp_servers={}`). The consumption-loop error mechanics live here and
  ONLY here (anti-drift rule #3).
- `_run_mcp_stage` — streaming `ClaudeSDKClient`, for the subprocess-MCP stages
  (Detector/Classifier/Matcher): wait-for-connected before acting (ADR-0014 D1, proven by
  RESULTS.md "GATE D1") + in-session reconnect-and-retry on a retryable `scan_diff` error
  (ADR-0014 D2). The discrimination tail is shared, so the preserved-spine regression anchors
  (`test_driver.py`) stay green through the transport split.

Invariants pinned in `scripts/smoke_tests/sdk_l2_capture/RESULTS.md`: ResultMessage precedes
any raise (last_result is capturable); `refusal` discriminated by `stop_reason` (subtype
lies 'success'); no `break` (trailing events); never discriminate by exception string.

The spec's `run_id` / `run_path` closure state is threaded as explicit keyword params here —
more testable than module globals, behavior unchanged.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ResultMessage, query
from pydantic import BaseModel, ValidationError

from coordinator.errors import (
    CoordinatorStreamFailure,
    DetectorScanFailed,
    SubagentExecutionError,
    SubagentRefusedTask,
    SubagentUnresponsive,
    SubagentValidationFailed,
)

log = logging.getLogger("coordinator")

# Readiness/retry budgets (ADR-0014 Deferral A — provisional, GENEROUS). Cold-start ~3.5 s
# idle (RESULTS.md "GATE D1"); a generous budget only costs latency on a rare failure, while
# a tight one risks a false CoordinatorStreamFailure on a server that WOULD have connected.
# Module-level so a test can shrink them (e.g. READINESS_POLL_S=0) without sleeping for real.
# margem pra CI sob carga; calibracao real = MC-D.
READINESS_POLL_S = 0.5
READINESS_ATTEMPTS = 40
RETRY_BUDGET = 1  # retry COUNT, not total attempts: _run_mcp_stage loops range(RETRY_BUDGET + 1)
STAGE_TIMEOUT_S = 240.0  # bound on receive_response() — D1 step 4: the iterator hangs w/o a ResultMessage


def write_scratchpad(run_path: Path, name: str, obj: BaseModel) -> Path:
    """Serialize `obj` (Pydantic) as JSON to `<run_path>/<name>`, atomic write via
    `os.replace` (Windows-native), UTF-8/LF. Audit-only (§4): written by the
    coordinator, never read by subagents."""
    target = run_path / name
    tmp = run_path / f".{name}.tmp"
    payload = json.dumps(obj.model_dump(mode="json"), ensure_ascii=False, indent=2)
    tmp.write_text(payload + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, target)
    return target


def _discriminate_and_capture(
    last_result: ResultMessage | None,
    *,
    stage: str,
    output_model: type[BaseModel],
    scratchpad_name: str,
    run_path: Path,
    run_id: str,
    verify_passthrough: Callable[[BaseModel, Any], None] | None = None,
    upstream: Any = None,
) -> BaseModel:
    """The capture/discrimination tail shared by both transports (coordinator §3.0bis),
    extracted verbatim so the one-shot `query()` path and the streaming `ClaudeSDKClient`
    path (ADR-0014 D1) discriminate through a SINGLE source — the preserved-spine regression
    anchor (`test_driver.py`) stays tautologically green.

    Synchronous: the tail performs no `await`. Any exception it raises (refusal / subtype /
    validation / passthrough — i.e. a STRUCTURED VERDICT) therefore propagates from the
    caller's discrimination point, NOT from inside `_run_mcp_stage`'s retry `try`. That is
    deliberate (ADR-0014 D2): a reconnect-and-retry recovers an unstable TRANSPORT (a
    consumption-phase `DetectorScanFailed`, hooks.py:51); re-running a scan that already
    returned a verdict would be non-deterministic and pointless, so a structured verdict
    never retries — which is exactly why the caller keeps this call OUTSIDE its retry try."""
    if last_result is None:
        raise CoordinatorStreamFailure(stage=stage)
    log.info(
        "stage.result",
        extra={
            "run_id": run_id,
            "stage": stage,
            "subtype": last_result.subtype,
            "stop_reason": last_result.stop_reason,
        },
    )
    if last_result.stop_reason == "refusal":  # PRECEDES subtype (which lies 'success')
        raise SubagentRefusedTask(stage=stage)
    match last_result.subtype:
        case "error_max_turns" | "error_max_budget_usd":
            raise SubagentUnresponsive(stage=stage)
        case "error_during_execution":
            raise SubagentExecutionError(stage=stage)
        case "error_max_structured_output_retries":
            raise SubagentValidationFailed(stage=stage)
        case "success":
            try:
                obj = output_model.model_validate(last_result.structured_output)
            except ValidationError as exc:
                raise SubagentValidationFailed(
                    stage=stage, raw=last_result.structured_output
                ) from exc
            if verify_passthrough is not None:
                verify_passthrough(obj, upstream)
            write_scratchpad(run_path, scratchpad_name, obj)
            return obj
        case other:
            raise SubagentExecutionError(stage=stage, detail=f"unexpected subtype {other!r}")


async def run_branch_b_stage(
    *,
    stage: str,
    prompt: str,
    options: ClaudeAgentOptions,
    output_model: type[BaseModel],
    scratchpad_name: str,
    run_path: Path,
    run_id: str,
    on_tool_result: Callable[[Any], None] | None = None,
    verify_passthrough: Callable[[BaseModel, Any], None] | None = None,
    upstream: Any = None,
) -> BaseModel:
    """One-shot `query()` capture spine for stages WITHOUT a subprocess-MCP cold-start race
    (the Triager, `mcp_servers={}`). MCP-consuming stages use `_run_mcp_stage` (ADR-0014 D1).
    The transport differs; the discrimination tail (`_discriminate_and_capture`) is shared."""
    log.info("stage.start", extra={"run_id": run_id, "stage": stage})
    last_result: ResultMessage | None = None
    try:
        async for message in query(prompt=prompt, options=options):
            if on_tool_result is not None:
                on_tool_result(message)  # Detector: scan_diff errorCode -> DetectorScanFailed
            if isinstance(message, ResultMessage):
                last_result = message  # NO break: trailing events (e.g. prompt_suggestion)
    except DetectorScanFailed:
        raise  # tool error already typed by the hook; do not mask
    except Exception as exc:  # noqa: BLE001 — re-raised as a typed coordinator error
        if last_result is None:
            raise CoordinatorStreamFailure(stage=stage) from exc
        # else: deliberate post-result exit (is_error=True); last_result authoritative.

    return _discriminate_and_capture(
        last_result,
        stage=stage,
        output_model=output_model,
        scratchpad_name=scratchpad_name,
        run_path=run_path,
        run_id=run_id,
        verify_passthrough=verify_passthrough,
        upstream=upstream,
    )


async def _wait_for_connected(client: ClaudeSDKClient, target: str, stage: str) -> None:
    """ADR-0014 D1(b): poll `get_mcp_status()` until `target` reaches 'connected' BEFORE the
    stage acts — the D1 gate proved this re-presents the tool to the model (RESULTS.md
    "GATE D1"). On each 'failed' poll, reconnect and keep polling (bounded by
    READINESS_ATTEMPTS). Exhausting the budget without 'connected' is a no-result stream
    failure (D4 -> CoordinatorStreamFailure). The observed
    shape is `{"mcpServers":[{name,status,...}]}` (d1_mock_fidelity_smoke.py); `name`/`status`
    are required keys of `McpServerStatus`."""
    for _ in range(READINESS_ATTEMPTS):
        servers = (await client.get_mcp_status())["mcpServers"]
        srv = next((s for s in servers if s["name"] == target), None)
        if srv is not None and srv["status"] == "connected":
            return
        if srv is not None and srv["status"] == "failed":
            try:
                await client.reconnect_mcp_server(target)
            except Exception as exc:  # noqa: BLE001 — reconnect_mcp_server raises on failure (client.py:406)
                # Achado 1 (D2 completeness): a failed reconnect = dead transport -> TYPED halt,
                # not an untyped propagation that degrades to a generic CoordinatorError.
                raise CoordinatorStreamFailure(stage=stage) from exc
        await asyncio.sleep(READINESS_POLL_S)
    raise CoordinatorStreamFailure(stage=stage)  # D4: never reached 'connected'


async def _run_mcp_stage(
    *,
    stage: str,
    prompt: str,
    options: ClaudeAgentOptions,
    output_model: type[BaseModel],
    scratchpad_name: str,
    run_path: Path,
    run_id: str,
    target: str,
    retries: int = 0,
    on_tool_result: Callable[[Any], None] | None = None,
    verify_passthrough: Callable[[BaseModel, Any], None] | None = None,
    upstream: Any = None,
) -> BaseModel:
    """Streaming `ClaudeSDKClient` capture spine for the subprocess-MCP stages
    (Detector/Classifier/Matcher) — ADR-0014 D1 (readiness) + D2 (recovery).

    ONE session per stage: the `async with` opens ONCE (NOT per attempt — re-spawn would
    re-pay the ~3.5 s cold-start and discard the very session `reconnect_mcp_server` operates
    on) and wraps the readiness wait + ALL retries. The retry `try` wraps the CONSUMPTION
    loop, because the `on_tool_result` hook raises `DetectorScanFailed` DURING consumption
    (hooks.py:51), not in the tail. Only a consumption-phase, retryable `DetectorScanFailed`
    reconnects IN-SESSION and re-issues the prompt; the `_discriminate_and_capture` call sits
    OUTSIDE the `try` so a structured verdict (refusal/subtype/validation/passthrough)
    propagates with NO reconnect (ADR-0014 D2 rider). Consumption runs under `STAGE_TIMEOUT_S`
    (D1 step 4): `receive_response()` hangs without a terminal `ResultMessage`, so a hung stage
    becomes a bounded `CoordinatorStreamFailure` (D4), never an infinite block — and a hang is
    NOT a retryable scan error. `retries` is the retry COUNT (Detector=RETRY_BUDGET;
    Classifier/Matcher=0, readiness only — DD-A3)."""
    log.info("stage.start", extra={"run_id": run_id, "stage": stage})
    async with ClaudeSDKClient(options) as client:
        await _wait_for_connected(client, target, stage)
        last_result: ResultMessage | None = None
        for attempt in range(retries + 1):
            last_result = None
            try:
                await client.query(prompt)
                # D1 step 4: receive_response() self-terminates on a ResultMessage but hangs
                # otherwise (client.py:579) -> bound it with a stage timeout.
                async with asyncio.timeout(STAGE_TIMEOUT_S):
                    async for message in client.receive_response():
                        if on_tool_result is not None:
                            on_tool_result(message)  # raises DetectorScanFailed DURING consumption
                        if isinstance(message, ResultMessage):
                            last_result = message  # NO break: trailing events
            except DetectorScanFailed as exc:  # D2: retry-vs-escalate by isRetryable
                if exc.is_retryable and attempt < retries:
                    try:
                        await client.reconnect_mcp_server(target)  # RECONNECT in-session — never re-spawn
                    except Exception as rexc:  # noqa: BLE001 — reconnect raises on failure (client.py:406)
                        # Achado 1: a failed reconnect during recovery = dead transport -> TYPED
                        # CoordinatorStreamFailure(stage), not an untyped propagation -> generic error.
                        raise CoordinatorStreamFailure(stage=stage) from rexc
                    await _wait_for_connected(client, target, stage)
                    continue
                raise  # non-retryable, or retry budget exhausted
            except TimeoutError as exc:  # D1 step 4 / D4: a hung stream is a bounded no-result failure
                raise CoordinatorStreamFailure(stage=stage) from exc
            except Exception as exc:  # noqa: BLE001 — re-raised as a typed coordinator error
                if last_result is None:
                    raise CoordinatorStreamFailure(stage=stage) from exc
                # else: deliberate post-result exit (is_error=True); last_result authoritative.
            # tail OUTSIDE the try: a structured verdict propagates without triggering retry
            return _discriminate_and_capture(
                last_result,
                stage=stage,
                output_model=output_model,
                scratchpad_name=scratchpad_name,
                run_path=run_path,
                run_id=run_id,
                verify_passthrough=verify_passthrough,
                upstream=upstream,
            )
    # outside the `async with` (session closed): the loop only falls through if every attempt
    # `continue`d, which the `attempt < retries` guard forbids on the last attempt — so this is
    # an unreachable, defensive terminator (also makes the return-coverage explicit to mypy).
    raise CoordinatorStreamFailure(stage=stage)
