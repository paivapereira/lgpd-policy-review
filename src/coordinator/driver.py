"""Branch B stage driver (coordinator.md §3.0bis) + scratchpad writer (§4).

`run_branch_b_stage` is the shared capture/discrimination spine for the four
Branch B stages (Triager, Detector, Classifier, Matcher); only the deltas vary
(output model, scratchpad name, tool hook, passthrough verification). The error
mechanics live here and ONLY here (anti-drift rule #3). Invariants pinned in
`scripts/smoke_tests/sdk_l2_capture/RESULTS.md`: ResultMessage precedes any raise
(last_result is capturable); `refusal` discriminated by `stop_reason` (subtype
lies 'success'); no `break` (trailing events); never discriminate by exception
string.

The spec's `run_id` / `run_path` closure state is threaded as explicit keyword
params here — more testable than module globals, behavior unchanged.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query
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
