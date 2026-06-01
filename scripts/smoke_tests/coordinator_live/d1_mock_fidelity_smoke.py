"""D1 mock-fidelity smoke — observe the REAL ClaudeSDKClient MCP-control surface
against claude-agent-sdk==0.2.87 BEFORE the conftest mock commits to a shape
(session-handoff §6 / `.claude/rules/verification-before-inference.md` / gates.md).

NO LLM turn — pure API-shape observation of `get_mcp_status()` /
`reconnect_mcp_server()` (+ the nested `McpStatusResponse` shape). The mock that
the Phase-3 conftest will ship (ADR-0014 D5) must mirror what is printed here
verbatim, not what the type signature suggests: a mock that lies + a green test is
worse than a red test (the `tool_use_result` nested-shape bit the 2b saga the same
way). Recorded fields (observed, not inferred): the `{"mcpServers":[...]}` wrapper,
the per-server `status` literal, the per-server `tools` list (server-advertised),
and the return of `reconnect_mcp_server`.

This smoke runs BEFORE the D1 verification gate (`d1_readiness_gate.py`): it
de-risks the API shape cheaply (no model turn) so the expensive gate only has to
answer the causal question (does readiness re-present the tool TO THE MODEL).

Pre-reqs: real semgrep-runner via .mcp.json; authenticated Claude Code session.
Run (PowerShell, no WSL):
  uv run python scripts/smoke_tests/coordinator_live/d1_mock_fidelity_smoke.py
"""
from __future__ import annotations

import asyncio
import sys

from claude_agent_sdk import ClaudeSDKClient

from coordinator.run import _detector_options
from g2b_mcp_middle_live import _cfg_with_project_semgrep

_TARGET = "semgrep-runner"
_MAX_POLL = 40
_POLL_S = 0.5


def _srv(status: object) -> dict | None:
    servers = status.get("mcpServers", []) if isinstance(status, dict) else []
    return next((s for s in servers if s.get("name") == _TARGET), None)


async def _main() -> int:
    cfg = _cfg_with_project_semgrep()
    options = _detector_options(cfg)
    print(f"[smoke] opening ClaudeSDKClient mcp_servers={list(options.mcp_servers)}", file=sys.stderr)
    async with ClaudeSDKClient(options) as client:
        # --- get_mcp_status() nested shape + pending->connected transition ---
        connected = False
        first_repr = None
        for i in range(_MAX_POLL):
            status = await client.get_mcp_status()
            if first_repr is None:
                first_repr = repr(status)
                print(f"[smoke] get_mcp_status() type={type(status).__name__} top_keys={list(status) if isinstance(status, dict) else status!r}", file=sys.stderr)
            srv = _srv(status)
            st = srv.get("status") if srv else None
            tools = [t.get("name") for t in srv.get("tools", [])] if srv else []
            print(f"[smoke] poll#{i} {_TARGET} status={st!r} server_tools={tools}", file=sys.stderr)
            if st == "connected":
                connected = True
                print(f"[smoke] CONNECTED full_entry={srv!r}", file=sys.stderr)
                break
            if st == "failed":
                print(f"[smoke] FAILED error={srv.get('error')!r}", file=sys.stderr)
                break
            await asyncio.sleep(_POLL_S)

        print(f"[smoke] connected={connected}")
        print(f"[smoke] first get_mcp_status repr (verbatim, for the mock):\n{first_repr}")

        # --- reconnect_mcp_server() return shape (call once on the connected server) ---
        try:
            ret = await client.reconnect_mcp_server(_TARGET)
            print(f"[smoke] reconnect_mcp_server({_TARGET!r}) -> type={type(ret).__name__} value={ret!r}")
        except Exception as exc:  # noqa: BLE001 — observe whatever the real API does
            print(f"[smoke] reconnect_mcp_server raised {type(exc).__name__}: {exc}")

        # --- post-reconnect status (does it re-cold-start? observe, don't infer) ---
        srv2 = _srv(await client.get_mcp_status())
        post = srv2.get("status") if srv2 else None
        print(f"[smoke] post-reconnect {_TARGET} status={post!r}")

    print(f"\nMOCK-FIDELITY SMOKE: {'OK (connected observed)' if connected else 'REVIEW (never connected)'}")
    return 0 if connected else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
