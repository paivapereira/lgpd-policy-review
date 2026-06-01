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

import asyncio
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


def _server_entry(name: str, status: str, *, tools: tuple[str, ...] = ()) -> dict[str, Any]:
    """A single `get_mcp_status()` server entry, mirroring the shape OBSERVED in
    `d1_mock_fidelity_smoke.py` / RESULTS.md "GATE D1" Probe 1 VERBATIM (not the type
    signature): a `pending` entry carries only {name, status, config, scope}; a `connected`
    entry additionally carries `serverInfo` + `tools`. A mock that lies + a green test is
    worse than a red one — the 2b nested-shape lesson."""
    entry: dict[str, Any] = {"name": name, "status": status, "config": {}, "scope": "dynamic"}
    if status == "connected":
        entry["serverInfo"] = {"name": name, "version": "3.2.4"}
        entry["tools"] = [{"name": t, "annotations": {}} for t in tools]
    return entry


# Real per-server tool names (from the MCP servers / run.py allowed_tools) — so the connected
# `tools` field is honest per target, not uniformly `scan_diff` (mock-fidelity discipline).
_TARGET_TOOLS: dict[str, tuple[str, ...]] = {
    "semgrep-runner": ("scan_diff",),
    "policy-reader": ("get_clause", "find_clauses_by_law_article", "check_applicability"),
}


def make_mcp_client(
    *,
    attempts: list[list[Any]],
    statuses: list[str] | None = None,
    raise_after: BaseException | None = None,
    hang: bool = False,
    reconnect_raises: BaseException | None = None,
    target: str = "semgrep-runner",
    connected_tools: tuple[str, ...] = ("scan_diff",),
) -> tuple[Callable[..., Any], dict[str, Any]]:
    """Build a mock streaming `ClaudeSDKClient` CLASS for direct `_run_mcp_stage` tests
    (ADR-0014 D5). Install via `monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", cls)`.

    - `attempts`: one message-script consumed per `receive_response()` call (i.e. per retry
      attempt) — reuse `result`/`assistant_tool_use`/`scan_error` verbatim.
    - `statuses`: status literals yielded by successive `get_mcp_status()` polls (default one
      `"connected"`; clamps to the last so a short list stays terminal). A stuck `["pending"]`
      exercises the readiness-timeout (ADR-0014 D4).
    - `raise_after`: if set, the FIRST `receive_response()` raises it AFTER yielding its
      messages (models the SDK 'ResultMessage then raise' post-result exit — arm B).
    - `hang`: if set, `receive_response()` blocks forever after yielding its messages (models
      the SDK iterator hanging without a terminal ResultMessage) — exercises STAGE_TIMEOUT_S.
    - `reconnect_raises`: if set, `reconnect_mcp_server()` raises it (the real SDK raises on a
      failed reconnect, client.py:406) AFTER counting the attempt — exercises Achado 1.
    `state` exposes `reconnects` / `queries` / `prompts` for assertions."""
    status_seq = list(statuses) if statuses is not None else ["connected"]
    state: dict[str, Any] = {"reconnects": 0, "queries": 0, "prompts": []}

    class _MockClient:
        def __init__(self, options: Any = None) -> None:
            self.options = options
            self._attempt = 0
            self._poll = 0

        async def __aenter__(self) -> _MockClient:
            return self

        async def __aexit__(self, *exc: Any) -> bool:
            return False

        async def get_mcp_status(self) -> dict[str, Any]:
            status = status_seq[min(self._poll, len(status_seq) - 1)]
            self._poll += 1
            return {"mcpServers": [_server_entry(target, status, tools=connected_tools)]}

        async def query(self, prompt: str) -> None:
            state["queries"] += 1
            state["prompts"].append(prompt)

        async def receive_response(self) -> Any:
            first = self._attempt == 0
            script = attempts[self._attempt] if self._attempt < len(attempts) else []
            self._attempt += 1
            for message in script:
                yield message
            if hang:
                await asyncio.Event().wait()  # never set: models receive_response() hanging
            if raise_after is not None and first:
                raise raise_after

        async def reconnect_mcp_server(self, name: str) -> None:
            state["reconnects"] += 1
            if reconnect_raises is not None:
                raise reconnect_raises

    return _MockClient, state


def make_sequential_transport(
    scripts: list[list[Any]],
    *,
    connected_targets: tuple[str, ...] = ("semgrep-runner", "policy-reader"),
) -> tuple[Callable[..., Any], Callable[..., Any], dict[str, Any]]:
    """Heterogeneous-transport sequencer for the post-ADR-0014-D1 pipeline e2e (D5). ONE shared
    `state['i']` counter spans the Triager+Reporter `query()` fake AND the
    Detector/Classifier/Matcher mock `ClaudeSDKClient`, so the '5 stages invoked' contract
    assertion (`state['i'] == 5`) SURVIVES the patch-target split — the migration replumbs the
    counter across both transports WITHOUT rewriting the assertion. Install `query_fn` at BOTH
    `coordinator.driver.query` and `coordinator.run.query`, and `client_cls` at
    `coordinator.driver.ClaudeSDKClient`. In e2e the servers are connected by the time a stage
    acts (readiness is unit-tested separately), so `get_mcp_status` reports them connected at
    once. Models ONE `receive_response()` per MCP stage (the happy path); a re-issued prompt
    would `_pull()` the NEXT stage's script, so use `make_mcp_client` for retry/reconnect."""
    state: dict[str, Any] = {"i": 0, "prompts": [], "reconnects": 0}

    def _pull() -> list[Any]:
        idx = state["i"]
        state["i"] += 1
        return scripts[idx] if idx < len(scripts) else []

    async def query_fn(*, prompt: str, options: Any, **_: Any) -> Any:
        state["prompts"].append(prompt)
        for message in _pull():
            yield message

    class _MockClient:
        def __init__(self, options: Any = None) -> None:
            self.options = options

        async def __aenter__(self) -> _MockClient:
            return self

        async def __aexit__(self, *exc: Any) -> bool:
            return False

        async def get_mcp_status(self) -> dict[str, Any]:
            return {
                "mcpServers": [
                    _server_entry(t, "connected", tools=_TARGET_TOOLS.get(t, ())) for t in connected_targets
                ]
            }

        async def query(self, prompt: str) -> None:
            state["prompts"].append(prompt)  # no counter bump — receive_response pulls the script

        async def receive_response(self) -> Any:
            for message in _pull():
                yield message

        async def reconnect_mcp_server(self, name: str) -> None:
            state["reconnects"] += 1

    return query_fn, _MockClient, state


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
        transport=make_sequential_transport,
        mcp_client=make_mcp_client,
    )
