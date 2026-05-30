r"""Smoke-test #48-b H2 — is `ReadMcpResourceTool` visible under each `tools` config?

The Matcher MUST read `policy://catalog` via the built-in `ReadMcpResourceTool`
(check-all, DD-M1). Three `tools` states are in play and prior evidence only
covers one:

- `tools=[]`              — coordinator.md:155 current state (Gate 6); classifier.md:45
                            asserts it works for the Matcher. NEVER tested for
                            ReadMcpResourceTool specifically.
- `tools=["Read"]`        — #48 tested this: model said "ReadMcpResourceTool is not
                            available in my current toolset".
- `tools=["Read", "ReadMcpResourceTool", "ListMcpResourcesTool"]` — DD-M30 rec. Untested.
- tools omitted           — works via ToolSearch (1 extra turn).

Faithful to the real Matcher scenario: registers the REAL policy-reader over
stdio and asks the model to read `policy://catalog`. Observable = did the model
emit a `ReadMcpResourceTool` ToolUseBlock and obtain catalog content, or
verbalize that the tool is unavailable.

Run (needs Claude Code CLI auth, like the #38-series smoke tests):
    uv run --with claude-agent-sdk==0.2.87 python scripts\smoke_tests\check_applicability_48b\h2_probe.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, ToolUseBlock, query
from claude_agent_sdk.types import AssistantMessage, ResultMessage, TextBlock

REPO_ROOT = Path(__file__).resolve().parents[3]

# Real policy-reader over stdio — same module the gate exercises boot.
POLICY_READER_CONFIG: dict[str, Any] = {
    "type": "stdio",
    "command": "uv",
    "args": ["run", "python", "-m", "mcp_servers.policy_reader.server"],
    "cwd": str(REPO_ROOT),
}

RESOURCE_TOOLS = ["ReadMcpResourceTool", "ListMcpResourcesTool"]
ALLOWED = ["Read", *RESOURCE_TOOLS]

PROMPT = (
    "Use the ReadMcpResourceTool to read the resource with uri "
    "'policy://catalog' from the MCP server named 'policy-reader'. "
    "Report how many clauses the catalog lists. If you cannot call "
    "ReadMcpResourceTool, say plainly that it is unavailable and why; "
    "do not substitute another tool."
)

CONFIGS: list[tuple[str, list[str] | None, bool]] = [
    ("H2-empty", [], False),                         # tools=[]  (Gate 6 / classifier.md:45)
    ("H2-read", ["Read"], False),                    # reproduce #48
    ("H2-listed", ["Read", *RESOURCE_TOOLS], False), # DD-M30 rec
    ("H2-omitted", None, True),                      # omit tools field
]


async def run_one(cfg_id: str, tools_field: list[str] | None, omit: bool) -> dict[str, Any]:
    kwargs: dict[str, Any] = dict(
        system_prompt=(
            "You are a test agent. Call exactly the tool you are asked to "
            "call. If it is unavailable, state which tool and why; do not "
            "substitute."
        ),
        allowed_tools=ALLOWED,
        mcp_servers={"policy-reader": POLICY_READER_CONFIG},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
        max_turns=6,
    )
    if not omit:
        kwargs["tools"] = tools_field

    read_resource_attempts = 0
    other_tools: list[str] = []
    text_chunks: list[str] = []
    subtype: str | None = None
    num_turns: int | None = None
    denials: list[Any] | None = None
    exc_repr: str | None = None

    try:
        options = ClaudeAgentOptions(**kwargs)
        async for msg in query(prompt=PROMPT, options=options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        name = getattr(block, "name", "<no-name>")
                        if name in RESOURCE_TOOLS:
                            read_resource_attempts += 1
                        else:
                            other_tools.append(name)
                    elif isinstance(block, TextBlock):
                        t = getattr(block, "text", "")
                        if t:
                            text_chunks.append(t)
            if isinstance(msg, ResultMessage):
                subtype = msg.subtype
                num_turns = msg.num_turns
                denials = list(msg.permission_denials)
    except Exception as exc:  # noqa: BLE001 — report, don't crash the matrix
        exc_repr = f"{type(exc).__name__}: {exc}"

    full = " ".join(text_chunks)
    low = full.lower()
    verbalizes_absence = ("readmcpresourcetool" in low or "not available" in low
                          or "unavailable" in low or "isn't available" in low
                          or "is not available" in low) and (
        "not available" in low or "unavailable" in low or "cannot" in low
        or "can't" in low or "isn't" in low)

    return {
        "cfg": cfg_id,
        "tools": "omitted" if omit else repr(tools_field),
        "read_resource_attempts": read_resource_attempts,
        "other_tools": other_tools,
        "verbalizes_absence": verbalizes_absence,
        "subtype": subtype,
        "num_turns": num_turns,
        "denials": denials,
        "exception": exc_repr,
        "text": full[:280] + ("..." if len(full) > 280 else ""),
    }


async def main() -> int:
    print("=" * 72)
    print("Smoke-test #48-b H2 — ReadMcpResourceTool visibility by `tools` config")
    print("SDK: claude-agent-sdk==0.2.87  |  Auth: Claude Code CLI")
    print("=" * 72)
    rows = []
    for cfg_id, tf, omit in CONFIGS:
        print(f"\n--- {cfg_id} (tools={'omitted' if omit else tf}) ---")
        r = await run_one(cfg_id, tf, omit)
        rows.append(r)
        print(f"  read_resource_attempts : {r['read_resource_attempts']}")
        print(f"  other_tools            : {r['other_tools']}")
        print(f"  verbalizes_absence     : {r['verbalizes_absence']}")
        print(f"  subtype/num_turns      : {r['subtype']} / {r['num_turns']}")
        print(f"  denials                : {r['denials']}")
        print(f"  exception              : {r['exception']}")
        print(f"  text                   : {r['text']}")

    print("\n" + "=" * 72)
    print("FINAL SUMMARY")
    print("=" * 72)
    for r in rows:
        verdict = ("READ" if r["read_resource_attempts"] > 0 and not r["exception"]
                   else "NO-READ")
        print(f"  {r['cfg']:<12} tools={r['tools']:<48} -> {verdict} "
              f"(attempts={r['read_resource_attempts']}, "
              f"absence={r['verbalizes_absence']}, turns={r['num_turns']})")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
