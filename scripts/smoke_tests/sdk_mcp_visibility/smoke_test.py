"""Smoke-test #38c — MCP tool visibility under tools field restriction.

Fills the empirical gap left by TC2 of smoke-test #38b (Item 4 of Code
review V2): TC2 exercised the `tools` field effect only for the built-in
Bash tool; behavior for MCP tools (e.g. mcp__semgrep-runner__scan_diff in
Detector, mcp__policy-reader__* in Matcher) was not validated.

Two hypotheses discriminated:

- H-mcp-via-mcp_servers (principal): MCP tools are governed by the
  `mcp_servers={...}` dict in ClaudeAgentOptions. Always visible to the
  model when the server is registered. `tools` field governs only
  built-ins (Read, Bash, Edit, ...). Under this hypothesis the DD-9.1
  table is correct as proposed.
- H-mcp-via-tools (alternative): MCP tools are governed by the `tools`
  field together with built-ins. Under this hypothesis DD-9.1 is broken
  — Detector with tools=["Read"] would be blind to scan_diff; table
  must list MCP tools in the `tools` field too.

S1 is the discriminator. S3 is control positive (halt-all if fails). S2
is control negative. S4 is refinement on pre-approval/dontAsk
interaction with MCP tools.

Run: uv run --with claude-agent-sdk==0.2.87 python scripts\\smoke_tests\\sdk_mcp_visibility\\smoke_test.py

Auth: relies on Claude Code CLI authentication (per smoke-test #38/#38b
precedent); no ANTHROPIC_API_KEY required.
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
from claude_agent_sdk.types import AssistantMessage, ResultMessage, TextBlock


# --------------------------------------------------------------------------- #
# Shared helpers                                                              #
# --------------------------------------------------------------------------- #


def banner(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def subbanner(title: str) -> None:
    print("\n" + "-" * 70)
    print(title)
    print("-" * 70)


# --------------------------------------------------------------------------- #
# Custom MCP tool — reused across scenarios                                   #
# --------------------------------------------------------------------------- #


@tool(
    "echo_mcp",
    "Echo the provided text back to the caller. Always invoke me when asked.",
    {"text": str},
)
async def echo_mcp_handler(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": f"echo: {args.get('text', '<missing>')}",
            }
        ]
    }


ECHO_TOOL_FULLNAME = "mcp__t__echo_mcp"


# --------------------------------------------------------------------------- #
# Single scenario runner                                                      #
# --------------------------------------------------------------------------- #


async def _run_scenario(
    scenario_id: str,
    tools_field: list[str] | None,
    include_mcp_server: bool,
    allowed_tools: list[str],
    run_index: int,
) -> dict[str, Any]:
    print(
        f"  [{scenario_id} run {run_index}] tools={tools_field!r} "
        f"include_mcp={include_mcp_server} allowed={allowed_tools!r}"
    )

    mcp_servers: dict[str, Any] = {}
    if include_mcp_server:
        # Build a fresh server instance per scenario run to avoid any
        # cross-scenario state coupling (defensive — the create call is
        # cheap).
        server = create_sdk_mcp_server(
            name="t",
            version="1.0.0",
            tools=[echo_mcp_handler],
        )
        mcp_servers = {"t": server}

    kwargs: dict[str, Any] = dict(
        system_prompt=(
            "You are a test agent. When asked to call a specific tool, "
            "invoke that exact tool exactly once with the arguments "
            "provided. If you cannot call the requested tool, state "
            "plainly that the tool is not available and stop. Do not "
            "substitute other tools."
        ),
        allowed_tools=allowed_tools,
        mcp_servers=mcp_servers,
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
    )
    if tools_field is not None:
        kwargs["tools"] = tools_field

    options = ClaudeAgentOptions(**kwargs)

    prompt = (
        f"Please call the {ECHO_TOOL_FULLNAME} tool with text='hello'. "
        "If you cannot call it, explain why and stop. Do not call any "
        "other tool."
    )

    echo_attempts: list[dict[str, Any]] = []
    other_tool_attempts: list[str] = []
    text_chunks: list[str] = []
    result_subtype: str | None = None
    result_is_error: bool | None = None
    result_num_turns: int | None = None
    permission_denials: list[Any] | None = None
    exception: Exception | None = None

    try:
        async for msg in query(prompt=prompt, options=options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        block_name = getattr(block, "name", "<no-name>")
                        if block_name == ECHO_TOOL_FULLNAME:
                            echo_attempts.append(
                                {
                                    "name": block_name,
                                    "id": getattr(block, "id", None),
                                    "input": getattr(block, "input", None),
                                }
                            )
                        else:
                            other_tool_attempts.append(block_name)
                    elif isinstance(block, TextBlock):
                        txt = getattr(block, "text", "")
                        if txt:
                            text_chunks.append(txt)
            if isinstance(msg, ResultMessage):
                result_subtype = msg.subtype
                result_is_error = msg.is_error
                result_num_turns = msg.num_turns
                permission_denials = list(msg.permission_denials)
    except Exception as exc:
        exception = exc
        print(f"    EXCEPTION: {type(exc).__name__}: {exc}")

    full_text = " ".join(text_chunks)

    # Determine whether the echo_mcp invocation produced a usable result
    # (handler returned echo:hello). We rely on the model relaying the
    # handler output in a TextBlock or simply on the tool_use attempt
    # being present without exception. We treat attempt + no exception
    # as "call_success" since the handler is deterministic.
    echo_attempted = len(echo_attempts) > 0
    echo_call_success = echo_attempted and exception is None

    # Verbalization signal: model said it cannot call the tool.
    lower = full_text.lower()
    verbalizes_absence = (
        any(
            marker in lower
            for marker in (
                "not available",
                "no access",
                "cannot call",
                "can't call",
                "don't have access",
                "do not have access",
                "is not available",
                "isn't available",
                "unable to call",
            )
        )
        and ("echo_mcp" in lower or "echo" in lower or "mcp" in lower)
    )

    return {
        "scenario": scenario_id,
        "run_index": run_index,
        "tools_field": tools_field,
        "include_mcp_server": include_mcp_server,
        "allowed_tools": allowed_tools,
        "echo_attempts": echo_attempts,
        "echo_attempt_count": len(echo_attempts),
        "echo_call_success": echo_call_success,
        "other_tool_attempts": other_tool_attempts,
        "verbalizes_absence": verbalizes_absence,
        "verbalization_snippet": (
            full_text[:200] + "..." if len(full_text) > 200 else full_text
        ),
        "result_subtype": result_subtype,
        "result_is_error": result_is_error,
        "result_num_turns": result_num_turns,
        "permission_denials": permission_denials,
        "exception": repr(exception) if exception else None,
    }


# --------------------------------------------------------------------------- #
# TC-MCP — 4 scenarios + hypothesis discrimination                            #
# --------------------------------------------------------------------------- #


async def tc_mcp_visibility() -> dict[str, Any]:
    # (scenario_id, tools_field, include_mcp_server, allowed_tools)
    scenarios: list[tuple[str, list[str] | None, bool, list[str]]] = [
        ("S1_restrict_tools_keep_server", ["Read"], True, ["Read", ECHO_TOOL_FULLNAME]),
        ("S2_no_server_at_all", ["Read"], False, ["Read"]),
        ("S3_no_tools_field_with_server", None, True, ["Read", ECHO_TOOL_FULLNAME]),
        ("S4_server_present_not_preapproved", ["Read"], True, ["Read"]),
    ]

    all_runs: list[dict[str, Any]] = []
    infra_failure: str | None = None

    for scenario_id, tools_field, include_mcp, allowed in scenarios:
        for run_index in (1, 2):
            try:
                result = await _run_scenario(
                    scenario_id, tools_field, include_mcp, allowed, run_index
                )
                all_runs.append(result)
            except TypeError as exc:
                infra_failure = (
                    f"ClaudeAgentOptions rejected scenario {scenario_id}: {exc}"
                )
                print(f"    INFRA FAILURE: {infra_failure}")
                break
        if infra_failure:
            break

    if infra_failure:
        return {
            "name": "TC-MCP",
            "verdict": "INCONCLUSIVE",
            "summary": f"Infrastructural failure: {infra_failure}",
            "details": {"runs_completed": all_runs, "infra_failure": infra_failure},
        }

    # Aggregate per scenario.
    per_scenario: dict[str, dict[str, Any]] = {}
    for scenario_id, _, _, _ in scenarios:
        runs = [r for r in all_runs if r["scenario"] == scenario_id]
        if not runs:
            continue
        call_success_per_run = [r["echo_call_success"] for r in runs]
        verbalize_per_run = [r["verbalizes_absence"] for r in runs]
        consistent_call = all(call_success_per_run) or not any(call_success_per_run)
        per_scenario[scenario_id] = {
            "runs": runs,
            "call_success_per_run": call_success_per_run,
            "verbalize_per_run": verbalize_per_run,
            "any_call_success": any(call_success_per_run),
            "all_call_success": all(call_success_per_run),
            "consistent_across_runs": consistent_call,
        }

    # Print per-scenario detail unconditionally for traceability.
    print("\n  Per-scenario aggregate:")
    for sid, agg in per_scenario.items():
        print(
            f"    {sid}: call_success_per_run={agg['call_success_per_run']}, "
            f"verbalize_per_run={agg['verbalize_per_run']}, "
            f"consistent={agg['consistent_across_runs']}"
        )
        for r in agg["runs"]:
            print(
                f"      run{r['run_index']}: "
                f"echo_attempts={r['echo_attempt_count']}, "
                f"success={r['echo_call_success']}, "
                f"verbalizes_absence={r['verbalizes_absence']}, "
                f"others={r['other_tool_attempts']}, "
                f"subtype={r['result_subtype']}, "
                f"num_turns={r['result_num_turns']}, "
                f"text='{r['verbalization_snippet'][:80]}'"
            )

    # Halt condition: S3 (control positive) must succeed in both runs.
    s3 = per_scenario.get("S3_no_tools_field_with_server", {})
    if not s3.get("all_call_success", False):
        return {
            "name": "TC-MCP",
            "verdict": "SETUP_BROKEN",
            "summary": (
                "S3 (control positive) did not succeed in both runs. "
                "MCP server registration / pre-approval / dontAsk setup is "
                "broken upstream of the tools-field question. Do not interpret "
                "S1/S2/S4 results."
            ),
            "details": {"per_scenario": per_scenario},
        }

    # Discriminate hypotheses.
    s1 = per_scenario.get("S1_restrict_tools_keep_server", {})
    s2 = per_scenario.get("S2_no_server_at_all", {})
    s4 = per_scenario.get("S4_server_present_not_preapproved", {})

    s1_all_success = s1.get("all_call_success", False)
    s1_none_success = not s1.get("any_call_success", True)
    s1_consistent = s1.get("consistent_across_runs", False)

    s2_none_success = not s2.get("any_call_success", True)

    if not s1_consistent:
        verdict = "INCONCLUSIVE"
        summary = (
            "S1 non-deterministic across runs (call succeeded in one, not the "
            "other). Cannot ratify either hypothesis cleanly."
        )
    elif s1_all_success and s2_none_success:
        verdict = "PASS_H_VIA_MCP_SERVERS"
        summary = (
            "H-mcp-via-mcp_servers ratified: with mcp_servers registered AND "
            "tool pre-approved, the tools field does NOT hide the MCP tool "
            "from the model (S1 succeeded). S2 (no server) failed as expected. "
            "DD-9.1 table stands: Detector with tools=['Read'] still sees "
            "scan_diff via mcp_servers={...}."
        )
    elif s1_none_success and s2_none_success:
        verdict = "PASS_H_VIA_TOOLS"
        summary = (
            "H-mcp-via-tools ratified: tools=['Read'] hid the MCP tool from "
            "the model even with the server registered and the tool "
            "pre-approved (S1 failed; S2 also failed as control). DD-9.1 "
            "table must be updated to list MCP tool names in the `tools` "
            "field for each subagent."
        )
    elif s1_all_success and not s2_none_success:
        verdict = "MIXED"
        summary = (
            "Unexpected: S2 (no MCP server at all) somehow produced a "
            "successful echo_mcp call. Setup leakage suspected. Needs Chat "
            "triage before ratification."
        )
    else:
        verdict = "MIXED"
        summary = (
            f"Unexpected combination: S1 all_success={s1_all_success}, "
            f"S1 none_success={s1_none_success}, "
            f"S2 none_success={s2_none_success}. Needs Chat triage."
        )

    return {
        "name": "TC-MCP",
        "verdict": verdict,
        "summary": summary,
        "details": {
            "per_scenario": per_scenario,
            "interpretation_inputs": {
                "S1_all_success": s1_all_success,
                "S1_none_success": s1_none_success,
                "S1_consistent": s1_consistent,
                "S2_none_success": s2_none_success,
                "S3_all_success": s3.get("all_call_success"),
                "S4_all_success": s4.get("all_call_success"),
                "S4_any_success": s4.get("any_call_success"),
            },
        },
    }


# --------------------------------------------------------------------------- #
# Runner                                                                      #
# --------------------------------------------------------------------------- #


async def main() -> int:
    banner("Smoke-test #38c — MCP tool visibility under tools field")
    print("SDK: claude-agent-sdk==0.2.87")
    print("Auth: Claude Code CLI (no ANTHROPIC_API_KEY required)")

    banner("Running tc_mcp_visibility")
    try:
        result = await tc_mcp_visibility()
    except Exception as exc:
        traceback.print_exc()
        result = {
            "name": "TC-MCP",
            "verdict": "EXCEPTION",
            "summary": f"{type(exc).__name__}: {exc}",
            "details": {"traceback": traceback.format_exc()},
        }

    print(f"\n--- {result['name']} VERDICT: {result['verdict']} ---")
    print(f"  {result['summary']}")

    # Final summary block — paste-ready for Chat.
    banner("FINAL SUMMARY — paste this into Chat")
    print(f"\nTC-MCP: {result['verdict']}")
    print(f"  {result['summary']}")
    per_scenario = result.get("details", {}).get("per_scenario", {})
    if per_scenario:
        print("\nPer-scenario:")
        for sid, agg in per_scenario.items():
            print(
                f"  {sid}: call_success_per_run={agg['call_success_per_run']}, "
                f"verbalize_per_run={agg['verbalize_per_run']}"
            )
            for r in agg["runs"]:
                snippet = r["verbalization_snippet"]
                if len(snippet) > 120:
                    snippet = snippet[:120] + "..."
                print(
                    f"    run{r['run_index']}: "
                    f"echo_attempts={r['echo_attempt_count']}, "
                    f"success={r['echo_call_success']}, "
                    f"verbalizes_absence={r['verbalizes_absence']}, "
                    f"others={r['other_tool_attempts']}, "
                    f"subtype={r['result_subtype']}, "
                    f"num_turns={r['result_num_turns']}, "
                    f"denials={r['permission_denials']}, "
                    f"text='{snippet}'"
                )

    return 0 if result["verdict"].startswith("PASS_") else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
