"""Mock-SDK fixtures for coordinator tests (Phase 1 walking skeleton).

The load-bearing test infrastructure: faithful constructors for the real SDK
dataclasses (shapes introspected from claude-agent-sdk==0.2.87) and a
`make_query` helper returning a scripted async generator. Install via
`monkeypatch.setattr("coordinator.driver.query", make_query([...]))` (and the
Reporter import site) — patch where used.

The constructors replay the behaviors empirically pinned in
`scripts/smoke_tests/sdk_l2_capture/RESULTS.md`: ResultMessage emitted before any
raise; `stop_reason=='refusal'` while `subtype=='success'`; permission_denials
truthiness; trailing events after ResultMessage (no break).
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, Callable

import pytest
from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)


def result_msg(
    *,
    subtype: str = "success",
    stop_reason: str | None = "end_turn",
    structured_output: Any = None,
    permission_denials: list[Any] | None = None,
    errors: list[str] | None = None,
    num_turns: int = 1,
    is_error: bool = False,
) -> ResultMessage:
    """Build a ResultMessage supplying the 6 required fields + the optionals the
    coordinator discriminates on."""
    return ResultMessage(
        subtype=subtype,
        duration_ms=0,
        duration_api_ms=0,
        is_error=is_error,
        num_turns=num_turns,
        session_id="test-session",
        stop_reason=stop_reason,
        structured_output=structured_output,
        permission_denials=permission_denials,
        errors=errors,
    )


def assistant_tool_use(name: str, tool_input: dict[str, Any]) -> AssistantMessage:
    """An AssistantMessage carrying a single ToolUseBlock (e.g. emit_report)."""
    return AssistantMessage(
        content=[ToolUseBlock(id="tu-1", name=name, input=tool_input)],
        model="test-model",
    )


def system_msg() -> SystemMessage:
    return SystemMessage(subtype="init", data={})


def user_msg() -> UserMessage:
    return UserMessage(content="tool result echo")


def scan_error_user_msg(
    error_code: str,
    *,
    is_retryable: bool,
    details: dict[str, Any] | None = None,
    findings: list[Any] | None = None,
) -> UserMessage:
    """A UserMessage carrying a `scan_diff` Option-B error envelope (sdk-mcp-conventions
    Eixo 2): wire `isError=False`, the structured payload under
    `tool_use_result.structuredContent` with `errorCode` present (the discriminator).
    `findings`, when supplied, co-exist with the errorCode to exercise the 'nothing
    leaks as a fabricated finding' invariant (detector §6.2). Shape confirmed against
    claude-agent-sdk==0.2.87 `UserMessage.tool_use_result: dict|None`; the nested
    `structuredContent` key is verified live at G2b."""
    envelope: dict[str, Any] = {"errorCode": error_code, "isRetryable": is_retryable}
    if details is not None:
        envelope["details"] = details
    if findings is not None:
        envelope["findings"] = findings
    return UserMessage(
        content=[ToolResultBlock(tool_use_id="tu-scan", content=json.dumps(envelope), is_error=False)],
        tool_use_result={"structuredContent": envelope, "isError": False},
    )


def make_query(
    script: list[Any] | Callable[[str, Any], list[Any]],
    *,
    raise_after: BaseException | None = None,
) -> Callable[..., Any]:
    """Return an async-generator function standing in for `claude_agent_sdk.query`.

    `script` is the list of messages to yield (or a callable `(prompt, options)
    -> list` to vary per call). If `raise_after` is set, the generator raises it
    after yielding the scripted messages (models the SDK 'ResultMessage then
    raise' path, AC-5 #38b)."""

    async def fake_query(*, prompt: str, options: Any, **_: Any) -> Any:
        messages = script(prompt, options) if callable(script) else script
        for message in messages:
            yield message
        if raise_after is not None:
            raise raise_after

    return fake_query


def make_sequential_query(
    scripts: list[list[Any]],
) -> tuple[Callable[..., Any], dict[str, Any]]:
    """A fake `query` that returns `scripts[i]` on its i-th call, sharing one
    counter. Install the SAME returned function at both `coordinator.driver.query`
    and `coordinator.run.query` so call ordering across driver/Reporter stages is
    counted together. The returned `state` dict exposes `i` (call count) and
    `prompts` (each call's prompt) for assertions."""
    state: dict[str, Any] = {"i": 0, "prompts": []}

    async def fake_query(*, prompt: str, options: Any, **_: Any) -> Any:
        index = state["i"]
        state["i"] += 1
        state["prompts"].append(prompt)
        messages = scripts[index] if index < len(scripts) else []
        for message in messages:
            yield message

    return fake_query, state


@pytest.fixture
def sdk() -> SimpleNamespace:
    """Namespace of mock-SDK constructors, so tests need no fragile cross-module
    import of conftest helpers."""
    return SimpleNamespace(
        result=result_msg,
        assistant_tool_use=assistant_tool_use,
        system=system_msg,
        user=user_msg,
        scan_error=scan_error_user_msg,
        make_query=make_query,
        sequential=make_sequential_query,
    )
