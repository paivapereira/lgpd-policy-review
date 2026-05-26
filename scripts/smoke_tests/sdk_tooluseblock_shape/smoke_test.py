"""Gate 1 smoke-test — ToolUseBlock.input shape for custom SDK tools.

Reference: docs/specs/subagents/coordinator.md §11 (Gate 1).

Confirms empirically that:
  TC1 — ToolUseBlock emitted by claude-agent-sdk Python has an `.input`
        attribute whose value is a dict matching @tool-declared params.
  TC2 — The canonical quintuple (system_prompt + allowed_tools +
        mcp_servers + permission_mode="dontAsk" + setting_sources=[] +
        strict_mcp_config=True) executes end-to-end without SDK rejection
        or permission stall.
  TC3 — Tool naming with underscore (server name "test_tools" +
        allowed_tools "mcp__test_tools__echo") resolves correctly.

Run: uv run --with claude-agent-sdk python scripts/smoke_tests/sdk_tooluseblock_shape/smoke_test.py
"""

from __future__ import annotations

import asyncio
import sys
import traceback
from typing import Any

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ToolUseBlock,
    create_sdk_mcp_server,
    query,
    tool,
)


@tool("echo", "Echo the input text back the given number of times", {"text": str, "count": int})
async def echo(args: dict[str, Any]) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": "ack"}]}


def report_block_surface(block: ToolUseBlock) -> None:
    print(f"  Block class: {type(block).__name__}")
    print(f"  Block module: {type(block).__module__}")
    attrs = [a for a in dir(block) if not a.startswith("_")]
    print(f"  Non-dunder attrs: {attrs}")
    for attr in attrs:
        try:
            val = getattr(block, attr)
            if callable(val):
                continue
            print(f"    {attr} = {val!r}")
        except Exception as exc:  # pragma: no cover - defensive
            print(f"    {attr} = <error: {exc}>")


async def main() -> int:
    server = create_sdk_mcp_server(
        name="test_tools",
        version="0.0.1",
        tools=[echo],
    )

    options = ClaudeAgentOptions(
        system_prompt=(
            "You are a smoke-test agent. When asked to echo, you MUST invoke "
            "the echo tool exactly once with the text and count provided. Do "
            "not paraphrase. Do not respond in prose first."
        ),
        allowed_tools=["mcp__test_tools__echo"],
        mcp_servers={"test_tools": server},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
    )

    prompt = 'Use the echo tool with text="hello" and count=3.'

    tc1_pass = False
    tc1_diag: dict[str, Any] = {}
    seen_tool_use = False
    seen_messages: list[str] = []
    all_tool_uses: list[dict[str, Any]] = []

    print("=" * 70)
    print("Gate 1 smoke-test — ToolUseBlock.input shape")
    print("=" * 70)
    print(f"SDK options.permission_mode = {options.permission_mode!r}")
    print(f"SDK options.setting_sources = {options.setting_sources!r}")
    print(
        f"SDK options.strict_mcp_config = "
        f"{getattr(options, 'strict_mcp_config', '<absent>')!r}"
    )
    print(f"SDK options.allowed_tools  = {options.allowed_tools!r}")
    print(f"SDK options.mcp_servers keys = {list(options.mcp_servers.keys())!r}")
    print(f"Prompt: {prompt}")
    print("-" * 70)

    try:
        async for msg in query(prompt=prompt, options=options):
            msg_kind = type(msg).__name__
            seen_messages.append(msg_kind)
            content = getattr(msg, "content", None)
            if not content:
                continue
            for block in content:
                if isinstance(block, ToolUseBlock):
                    seen_tool_use = True
                    print(f"\n[MESSAGE {msg_kind}] ToolUseBlock found:")
                    report_block_surface(block)

                    has_input = hasattr(block, "input")
                    input_val = getattr(block, "input", None)
                    input_type = type(input_val).__name__
                    block_name = getattr(block, "name", None)

                    record = {
                        "has_input_attr": has_input,
                        "input_type": input_type,
                        "input_value": input_val,
                        "block_name": block_name,
                        "block_id": getattr(block, "id", None),
                    }
                    all_tool_uses.append(record)

                    # TC1 strictly evaluated on the echo invocation.
                    if block_name == "mcp__test_tools__echo":
                        tc1_diag = record
                        if (
                            has_input
                            and isinstance(input_val, dict)
                            and input_val.get("text") == "hello"
                            and input_val.get("count") == 3
                        ):
                            tc1_pass = True
    except Exception as exc:
        print("\n[EXCEPTION during query()]")
        print(f"  type: {type(exc).__name__}")
        print(f"  msg:  {exc}")
        print("  traceback:")
        traceback.print_exc()
        return _report(False, tc1_diag, seen_tool_use, seen_messages, all_tool_uses, error=exc)

    return _report(tc1_pass, tc1_diag, seen_tool_use, seen_messages, all_tool_uses)


def _report(
    tc1_pass: bool,
    tc1_diag: dict[str, Any],
    seen_tool_use: bool,
    seen_messages: list[str],
    all_tool_uses: list[dict[str, Any]],
    error: Exception | None = None,
) -> int:
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Messages seen in stream: {seen_messages}")
    print(f"ToolUseBlock count:      {len(all_tool_uses)}")
    print(f"All tool_use names:      {[t['block_name'] for t in all_tool_uses]}")
    print(f"TC1 diagnostic (echo):   {tc1_diag}")

    echo_invoked = any(
        t.get("block_name") == "mcp__test_tools__echo" for t in all_tool_uses
    )
    tc2_pass = error is None and seen_tool_use
    tc3_pass = echo_invoked

    print(f"\nTC1 (ToolUseBlock.input shape):   {'PASS' if tc1_pass else 'FAIL'}")
    print(f"TC2 (canonical quintuple e2e):    {'PASS' if tc2_pass else 'FAIL'}")
    print(f"TC3 (underscore naming resolve):  {'PASS' if tc3_pass else 'FAIL'}")

    overall = tc1_pass and tc2_pass and tc3_pass
    print(f"\nGATE 1: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
