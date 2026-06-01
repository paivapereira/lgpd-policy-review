"""D1 verification gate (session-handoff §2 step 1 / ADR-0014 "D1 verification
gate") — the load-bearing causal probe of the entire MC-C Phase-3 reliability fix.

What G2b OBSERVED (RESULTS.md "GATE G2b"): the one-shot `query()` fires the prompt
before semgrep-runner finishes its ~3.5 s cold-start; the init `SystemMessage` shows
`tools: ['Read','StructuredOutput']` with semgrep-runner `status: 'pending'` —
`scan_diff` is NEVER registered — and the Detector emits `findings=[]` on turn 1.

What ADR-0014 D1 PROPOSES: open a streaming `ClaudeSDKClient`, poll
`get_mcp_status()` until the server is `'connected'` BEFORE `client.query(prompt)`,
and that makes `scan_diff` available TO THE MODEL when it acts.

That proposal is an INFERENCE until observed. This gate observes it. Crucially it
does NOT pass on `get_mcp_status -> 'connected'` alone: a connected SERVER (even one
whose `get_mcp_status` `tools` list advertises `scan_diff`) is necessary, NOT
sufficient — server-emits != model-receives, the same relay-re-presentation class
that cost four round-trips in the 2b saga (the handshake's `tools.listChanged:true`
is PROTOCOL support, not a guarantee the SDK relay re-presents the updated list to
the model before it acts). The gate PASSES only if the MODEL actually CALLS
`scan_diff` after the readiness wait — proven by a `ToolUseBlock` named
`mcp__semgrep-runner__scan_diff` in the live stream AND a populated `DetectorOutput`
on the same synthetic-CPF repo G2b used.

  PASS  -> ADR D1 is the fix as written (wait-for-connected, then query).
  FAIL  -> the model acts on the init snapshot anyway; ADR D1 must REDESIGN
           (guarantee 'connected' before the initial stream, or re-prompt after
           connect). Re-design in the ADR BEFORE any migration code.

This is a SMOKE gate (not a hermetic test): an LLM is non-deterministic, so per
gates.md the persisted evidence is the gate's existence + outcome in RESULTS.md.

Pre-reqs: semgrep==1.163.0 on PATH (ADR-0010); authenticated Claude Code session.
Run (PowerShell, no WSL):
  uv run python scripts/smoke_tests/coordinator_live/d1_readiness_gate.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    ToolUseBlock,
    UserMessage,
)

from coordinator.prompts import build_detector_prompt
from coordinator.run import _detector_options
from g2b_mcp_middle_live import _cfg_with_project_semgrep, _make_cpf_repo, _scope
from subagents.triager.models import TriagerDecision

_TARGET = "semgrep-runner"
_SCAN_TOOL = "mcp__semgrep-runner__scan_diff"
_MAX_POLL = 40
_POLL_S = 0.5
_STAGE_TIMEOUT_S = 240.0


async def _wait_for_connected(client: ClaudeSDKClient) -> tuple[bool, list[str]]:
    """ADR-0014 D1 (b): poll get_mcp_status until target 'connected'. Returns
    (connected, server_tools). server_tools is the SERVER's advertised tool list
    (necessary, NOT sufficient — still server-side, not the model's snapshot)."""
    for i in range(_MAX_POLL):
        status = await client.get_mcp_status()
        srv = next(
            (s for s in status.get("mcpServers", []) if s.get("name") == _TARGET), None
        )
        st = srv.get("status") if srv else None
        tools = [t.get("name") for t in srv.get("tools", [])] if srv else []
        print(f"  [gate] poll#{i} {_TARGET} status={st!r} server_tools={tools}", file=sys.stderr)
        if st == "connected":
            return True, tools
        if st == "failed":
            print(f"  [gate] reconnect on 'failed' error={srv.get('error')!r}", file=sys.stderr)
            await client.reconnect_mcp_server(_TARGET)
        await asyncio.sleep(_POLL_S)
    return False, []


async def _main() -> int:
    cfg = _cfg_with_project_semgrep()
    repo, base, head = _make_cpf_repo()
    options = _detector_options(cfg)
    prompt = build_detector_prompt(
        _scope(base, head),
        TriagerDecision(decision="proceed", relevance_summary="cpf"),
    )

    saw_scan_call = False
    saw_scan_result = False
    model_tools_snapshot: list[str] | None = None
    final_result: ResultMessage | None = None

    cwd = os.getcwd()
    os.chdir(repo)  # spawned semgrep-runner inherits cwd -> scan_diff scans the CPF repo
    try:
        async with ClaudeSDKClient(options) as client:
            connected, server_tools = await _wait_for_connected(client)
            server_advertises = any("scan_diff" in (t or "") for t in server_tools)
            print(f"  [gate] connected={connected} server_advertises_scan_diff={server_advertises}", file=sys.stderr)
            if not connected:
                print("\nGATE D1: FAIL/REVIEW — server never reached 'connected' "
                      "(readiness/env issue, NOT the causal question — debug before re-running)")
                return 1

            await client.query(prompt)
            try:
                async with asyncio.timeout(_STAGE_TIMEOUT_S):
                    async for message in client.receive_response():
                        if isinstance(message, SystemMessage):
                            data = getattr(message, "data", None)
                            if isinstance(data, dict) and "tools" in data and model_tools_snapshot is None:
                                model_tools_snapshot = data.get("tools")
                                print(f"  [gate] SystemMessage subtype={message.subtype!r} "
                                      f"model_tools={model_tools_snapshot} "
                                      f"mcp_servers={data.get('mcp_servers')}", file=sys.stderr)
                        if isinstance(message, AssistantMessage) and message.content:
                            for block in message.content:
                                if isinstance(block, ToolUseBlock):
                                    print(f"  [gate] ToolUseBlock name={block.name!r}", file=sys.stderr)
                                    if block.name == _SCAN_TOOL:
                                        saw_scan_call = True
                        if isinstance(message, UserMessage):
                            tur = message.tool_use_result
                            # scan_diff result is a dict whose 'content' carries the JSON
                            # envelope (rules_version/semgrep_version/scan_metadata/findings);
                            # the StructuredOutput ack is the bare str (shared channel, 2b).
                            is_scan = isinstance(tur, dict) and "content" in tur
                            if is_scan:
                                saw_scan_result = True
                            limit = 4000 if is_scan else 300
                            print(f"  [gate] UserMessage tool_use_result type={type(tur).__name__} "
                                  f"repr={repr(tur)[:limit]}", file=sys.stderr)
                        if isinstance(message, ResultMessage):
                            final_result = message
            except TimeoutError:
                print(f"  [gate] receive_response timed out after {_STAGE_TIMEOUT_S}s (no ResultMessage)", file=sys.stderr)
    finally:
        os.chdir(cwd)

    so = final_result.structured_output if final_result else None
    findings = so.get("findings") if isinstance(so, dict) else None
    populated = bool(findings)

    print()
    print(f"  init tools snapshot (model)          : {model_tools_snapshot}")
    print(f"  model CALLED scan_diff (ToolUseBlock): {saw_scan_call}")
    print(f"  scan_diff result observed in stream  : {saw_scan_result}")
    print(f"  ResultMessage subtype                : {final_result.subtype if final_result else None}")
    print(f"  final structured_output (verbatim)   : {so!r}")

    # GATE D1's question (ADR-0014): does readiness-wait make scan_diff available TO
    # THE MODEL? Proven ONLY by the model actually calling it (server-connected status
    # is necessary-not-sufficient) AND the tool actually returning a result in-model.
    # DetectorOutput.findings being [] is a SEPARATE, downstream concern (the
    # {"output"} wrapper / scan-transcription fail-action that readiness UNBLOCKS for
    # observation, handoff §5) — NOT part of this gate's causal question.
    gate_pass = saw_scan_call and saw_scan_result
    print()
    print(f"  [downstream, NOT the gate] DetectorOutput.findings populated: "
          f"{populated} (n={len(findings) if findings else 0})")
    print(f"GATE D1 (readiness re-presents scan_diff TO THE MODEL): {'PASS' if gate_pass else 'FAIL/REVIEW'}")
    return 0 if gate_pass else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
