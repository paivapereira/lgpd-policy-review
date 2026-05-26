"""Smoke-test pre-Reporter-flesh (sessao Code #38b).

Three TCs filling empirical gates for DDs 5.1, 9.1, 10.4 of the
forthcoming docs/specs/subagents/reporter.md spec.

TC1 — Pydantic BaseModel class as @tool input_schema (vs JSON Schema dict).
TC2 — ClaudeAgentOptions.tools field effect under full lockdown.
TC3 — ResultMessage shape on max_turns exhaustion.

Run: uv run --with claude-agent-sdk==0.2.87 python scripts\\smoke_tests\\sdk_reporter_gates\\smoke_test.py

Auth: relies on Claude Code CLI authentication (per smoke-test #38 precedent);
no ANTHROPIC_API_KEY required.
"""

from __future__ import annotations

import asyncio
import dataclasses
import sys
import traceback
from typing import Any

from pydantic import BaseModel, Field

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
# TC1 — Pydantic BaseModel as input_schema                                    #
# --------------------------------------------------------------------------- #


class TC1Payload(BaseModel):
    title: str = Field(..., description="Document title")
    tags: list[str] = Field(default_factory=list, description="Tags")


async def tc1_pydantic_type_as_input_schema() -> dict[str, Any]:
    pydantic_error: Exception | None = None
    dict_error: Exception | None = None
    pydantic_tool = None
    dict_tool = None

    try:
        @tool(
            "tc1_pydantic_type",
            "Echo the payload (pydantic type variant). Always invoke me when asked.",
            TC1Payload,
        )
        async def _pydantic_handler(args: dict[str, Any]) -> dict[str, Any]:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"pydantic_type handler received: {args!r}",
                    }
                ]
            }

        pydantic_tool = _pydantic_handler
        print("  Pydantic-type decoration: OK")
    except Exception as exc:
        pydantic_error = exc
        print(f"  Pydantic-type decoration: FAIL ({type(exc).__name__}: {exc})")

    try:
        @tool(
            "tc1_jsonschema_dict",
            "Echo the payload (json schema dict variant). Always invoke me when asked.",
            TC1Payload.model_json_schema(),
        )
        async def _dict_handler(args: dict[str, Any]) -> dict[str, Any]:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"jsonschema_dict handler received: {args!r}",
                    }
                ]
            }

        dict_tool = _dict_handler
        print("  JSON-Schema-dict decoration: OK")
    except Exception as exc:
        dict_error = exc
        print(f"  JSON-Schema-dict decoration: FAIL ({type(exc).__name__}: {exc})")

    # If both decorations fail, abort.
    if pydantic_error is not None and dict_error is not None:
        return {
            "name": "TC1",
            "verdict": "FAIL",
            "summary": "Both decoration variants raised on @tool registration.",
            "details": {
                "pydantic_error": repr(pydantic_error),
                "dict_error": repr(dict_error),
            },
        }

    # If only pydantic failed, ratify dict and report.
    if pydantic_error is not None:
        return {
            "name": "TC1",
            "verdict": "PARTIAL",
            "summary": (
                f"Pydantic-type decoration raised {type(pydantic_error).__name__}; "
                "DD-5.1 ratifies JSON Schema dict via BaseModel.model_json_schema()."
            ),
            "details": {
                "pydantic_error": repr(pydantic_error),
                "dict_decoration": "OK (but not exercised end-to-end since pydantic failed first)",
            },
        }

    # Both decorations succeeded — build server and exercise both end-to-end.
    tools_list = []
    if pydantic_tool is not None:
        tools_list.append(pydantic_tool)
    if dict_tool is not None:
        tools_list.append(dict_tool)

    server = create_sdk_mcp_server(
        name="tc1_tools",
        version="1.0.0",
        tools=tools_list,
    )

    options_base = dict(
        system_prompt=(
            "You are a test agent. When asked to use a specific tool, you MUST "
            "invoke that exact tool exactly once with the arguments provided. "
            "Do not explain. Do not invoke other tools."
        ),
        mcp_servers={"tc1_tools": server},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
    )

    results_per_variant: dict[str, dict[str, Any]] = {}

    for variant_name, full_tool_name in [
        ("pydantic_type", "mcp__tc1_tools__tc1_pydantic_type"),
        ("jsonschema_dict", "mcp__tc1_tools__tc1_jsonschema_dict"),
    ]:
        subbanner(f"TC1 — invoking {variant_name} (tool {full_tool_name})")
        options = ClaudeAgentOptions(
            allowed_tools=[full_tool_name],
            **options_base,
        )
        prompt = (
            f'Use the {full_tool_name} tool with title="hello" and tags=["a","b"]. '
            "Invoke the tool once, then stop."
        )
        captured_invocations: list[dict[str, Any]] = []
        exception_during: Exception | None = None
        try:
            async for msg in query(prompt=prompt, options=options):
                content = getattr(msg, "content", None)
                if not content:
                    continue
                for block in content:
                    if isinstance(block, ToolUseBlock) and getattr(block, "name", None) == full_tool_name:
                        captured_invocations.append(
                            {
                                "name": block.name,
                                "id": getattr(block, "id", None),
                                "input": getattr(block, "input", None),
                                "input_type": type(getattr(block, "input", None)).__name__,
                            }
                        )
                        print(f"    ToolUseBlock captured: input={block.input!r}")
        except Exception as exc:
            exception_during = exc
            print(f"    EXCEPTION during {variant_name}: {type(exc).__name__}: {exc}")
            traceback.print_exc()

        results_per_variant[variant_name] = {
            "invocations": captured_invocations,
            "invoked_count": len(captured_invocations),
            "exception": repr(exception_during) if exception_during else None,
            "expected_args_seen": any(
                isinstance(inv["input"], dict)
                and inv["input"].get("title") == "hello"
                and inv["input"].get("tags") == ["a", "b"]
                for inv in captured_invocations
            ),
        }

    pydantic_ok = (
        results_per_variant["pydantic_type"]["invoked_count"] >= 1
        and results_per_variant["pydantic_type"]["expected_args_seen"]
        and results_per_variant["pydantic_type"]["exception"] is None
    )
    dict_ok = (
        results_per_variant["jsonschema_dict"]["invoked_count"] >= 1
        and results_per_variant["jsonschema_dict"]["expected_args_seen"]
        and results_per_variant["jsonschema_dict"]["exception"] is None
    )

    if pydantic_ok and dict_ok:
        verdict = "PASS"
        summary = (
            "Both variants accepted, invoked, and delivered expected args to handler. "
            "DD-5.1 reopens: Pydantic type may be preferred for idiomatic Python."
        )
    elif dict_ok and not pydantic_ok:
        verdict = "PARTIAL"
        summary = (
            "Only JSON-Schema-dict variant worked end-to-end. "
            "DD-5.1 ratifies JSON Schema dict via BaseModel.model_json_schema()."
        )
    elif pydantic_ok and not dict_ok:
        verdict = "PARTIAL"
        summary = (
            "Only Pydantic-type variant worked end-to-end (unexpected — dict failed)."
        )
    else:
        verdict = "FAIL"
        summary = "Neither variant invoked successfully end-to-end."

    return {
        "name": "TC1",
        "verdict": verdict,
        "summary": summary,
        "details": {
            "decoration_errors": {
                "pydantic": repr(pydantic_error) if pydantic_error else None,
                "dict": repr(dict_error) if dict_error else None,
            },
            "results_per_variant": results_per_variant,
        },
    }


# --------------------------------------------------------------------------- #
# TC2 — tools field effect under lockdown                                     #
# --------------------------------------------------------------------------- #


async def _tc2_run_scenario(
    scenario_id: str,
    tools_field: list[str] | None,
    allowed_tools: list[str],
    run_index: int,
) -> dict[str, Any]:
    print(f"  [{scenario_id} run {run_index}] tools={tools_field!r} allowed={allowed_tools!r}")

    kwargs: dict[str, Any] = dict(
        system_prompt=(
            "You are an assistant with restricted tool access. If you cannot "
            "perform a task, explain plainly which tool you would need."
        ),
        allowed_tools=allowed_tools,
        mcp_servers={},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
    )
    if tools_field is not None:
        kwargs["tools"] = tools_field

    options = ClaudeAgentOptions(**kwargs)

    prompt = (
        "Please list the files in the current directory. "
        "Use whatever tool is appropriate. If you cannot, explain why."
    )

    bash_attempts = 0
    other_tool_attempts: list[str] = []
    text_chunks: list[str] = []
    result_subtype: str | None = None
    result_is_error: bool | None = None
    result_num_turns: int | None = None
    exception: Exception | None = None

    try:
        async for msg in query(prompt=prompt, options=options):
            content = getattr(msg, "content", None)
            if content:
                for block in content:
                    if isinstance(block, ToolUseBlock):
                        block_name = getattr(block, "name", "<no-name>")
                        if block_name == "Bash":
                            bash_attempts += 1
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
    except Exception as exc:
        exception = exc
        print(f"    EXCEPTION: {type(exc).__name__}: {exc}")

    full_text = " ".join(text_chunks).lower()
    mentions_bash_not_avail = any(
        marker in full_text
        for marker in (
            "don't have",
            "do not have",
            "cannot",
            "can't",
            "no access",
            "not have access",
            "without",
        )
    ) and "bash" in full_text

    return {
        "scenario": scenario_id,
        "run_index": run_index,
        "bash_attempts": bash_attempts,
        "other_tool_attempts": other_tool_attempts,
        "result_subtype": result_subtype,
        "result_is_error": result_is_error,
        "result_num_turns": result_num_turns,
        "mentions_bash_not_available": mentions_bash_not_avail,
        "text_excerpt": (full_text[:200] + "...") if len(full_text) > 200 else full_text,
        "exception": repr(exception) if exception else None,
    }


async def tc2_tools_field_effect() -> dict[str, Any]:
    scenarios = [
        ("S1_minimal", ["Read"], ["Read"]),
        ("S2_expanded", ["Read", "Bash"], ["Read"]),
        ("S3_no_tools_field", None, ["Read"]),
        ("S4_bash_authorized", None, ["Read", "Bash"]),
    ]

    all_runs: list[dict[str, Any]] = []
    infra_failure: str | None = None

    for scenario_id, tools_field, allowed_tools in scenarios:
        for run_index in (1, 2):
            try:
                result = await _tc2_run_scenario(
                    scenario_id, tools_field, allowed_tools, run_index
                )
                all_runs.append(result)
            except TypeError as exc:
                # mcp_servers={} or tools=[...] might be rejected by ClaudeAgentOptions
                infra_failure = (
                    f"ClaudeAgentOptions rejected scenario {scenario_id}: {exc}"
                )
                print(f"    INFRA FAILURE: {infra_failure}")
                break
        if infra_failure:
            break

    if infra_failure:
        return {
            "name": "TC2",
            "verdict": "INCONCLUSIVE",
            "summary": f"Infrastructural failure: {infra_failure}",
            "details": {"runs_completed": all_runs, "infra_failure": infra_failure},
        }

    # Aggregate per scenario: take mode across 2 runs for bash_attempts > 0.
    per_scenario: dict[str, dict[str, Any]] = {}
    for scenario_id, _, _ in scenarios:
        runs = [r for r in all_runs if r["scenario"] == scenario_id]
        if not runs:
            continue
        bash_attempts_per_run = [r["bash_attempts"] for r in runs]
        any_bash_attempt = [b > 0 for b in bash_attempts_per_run]
        consistent = all(any_bash_attempt) or not any(any_bash_attempt)
        per_scenario[scenario_id] = {
            "runs": runs,
            "bash_attempts_per_run": bash_attempts_per_run,
            "any_bash_attempted": any(any_bash_attempt),
            "consistent_across_runs": consistent,
        }

    # Interpret hypotheses.
    s1_attempted = per_scenario.get("S1_minimal", {}).get("any_bash_attempted")
    s2_attempted = per_scenario.get("S2_expanded", {}).get("any_bash_attempted")
    s3_attempted = per_scenario.get("S3_no_tools_field", {}).get("any_bash_attempted")
    s4_attempted = per_scenario.get("S4_bash_authorized", {}).get("any_bash_attempted")

    # Print per-scenario detail unconditionally for traceability.
    print("\n  Per-scenario aggregate:")
    for sid, agg in per_scenario.items():
        print(
            f"    {sid}: bash_attempts_per_run={agg['bash_attempts_per_run']}, "
            f"any_bash={agg['any_bash_attempted']}, "
            f"consistent={agg['consistent_across_runs']}"
        )
        for r in agg["runs"]:
            print(
                f"      run{r['run_index']}: bash={r['bash_attempts']}, "
                f"others={r['other_tool_attempts']}, "
                f"subtype={r['result_subtype']}, "
                f"is_error={r['result_is_error']}, "
                f"num_turns={r['result_num_turns']}, "
                f"text='{r['text_excerpt'][:80]}...'"
            )

    # H_EFFECTIVE vs H_REDUNDANT is decided by S1 vs S2 only.
    # S3 (no tools field) and S4 (bash authorized) are auxiliary controls;
    # their non-determinism does NOT invalidate the H interpretation.
    s1_consistent = per_scenario.get("S1_minimal", {}).get("consistent_across_runs", False)
    s2_consistent = per_scenario.get("S2_expanded", {}).get("consistent_across_runs", False)

    if not (s1_consistent and s2_consistent):
        verdict = "INCONCLUSIVE"
        inconsistent_h = [
            sid for sid in ("S1_minimal", "S2_expanded")
            if not per_scenario.get(sid, {}).get("consistent_across_runs", False)
        ]
        summary = (
            f"Non-deterministic Bash-attempt behavior in H-relevant scenarios "
            f"{inconsistent_h}; cannot ratify either hypothesis cleanly."
        )
    elif s1_attempted is False and s2_attempted is True:
        verdict = "PASS_H_EFFECTIVE"
        summary = (
            "H-effective ratified: S1 (tools=['Read']) yielded 0 Bash attempts; "
            "S2 (tools=['Read','Bash'] but allowed=['Read']) yielded >=1 Bash "
            "attempt. tools field is an effective context-restriction layer. "
            "DD-9.1 ratifies adding tools field to coordinator skeleton."
        )
    elif s1_attempted is False and s2_attempted is False:
        verdict = "PASS_H_REDUNDANT"
        summary = (
            "H-redundant ratified: both S1 and S2 yielded 0 Bash attempts. "
            "Under full lockdown (dontAsk + setting_sources=[] + "
            "strict_mcp_config=True + allowed_tools=['Read']), the tools field "
            "is redundant. DD-9.1 descopes to companion-debt; skeleton stays "
            "as-is."
        )
    elif s1_attempted is True and s2_attempted is True:
        verdict = "MIXED"
        summary = (
            "Both S1 and S2 yielded Bash attempts despite Bash not being in "
            "allowed_tools. Lockdown not preventing context exposure as "
            "hypothesized. Needs Chat triage before ratification."
        )
    else:
        verdict = "MIXED"
        summary = (
            f"Unexpected pattern: S1_attempted={s1_attempted}, "
            f"S2_attempted={s2_attempted}, S3_attempted={s3_attempted}, "
            f"S4_attempted={s4_attempted}. Needs Chat triage."
        )

    return {
        "name": "TC2",
        "verdict": verdict,
        "summary": summary,
        "details": {
            "per_scenario": per_scenario,
            "interpretation_inputs": {
                "S1_minimal_attempted_bash": s1_attempted,
                "S2_expanded_attempted_bash": s2_attempted,
                "S3_no_tools_field_attempted_bash": s3_attempted,
                "S4_bash_authorized_attempted_bash": s4_attempted,
            },
        },
    }


# --------------------------------------------------------------------------- #
# TC3 — ResultMessage shape on max_turns exhaustion                           #
# --------------------------------------------------------------------------- #


@tool(
    "tc3_never_satisfied",
    "Never returns success; instructs caller to call again with more detail.",
    {"detail": str},
)
async def tc3_never_satisfied_handler(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": (
                    "Validation failed: detail is too short. "
                    "Please call again with a longer detail field."
                ),
            }
        ],
        "isError": True,
    }


async def tc3_max_turns_resultmessage_shape() -> dict[str, Any]:
    server = create_sdk_mcp_server(
        name="tc3_tools",
        version="1.0.0",
        tools=[tc3_never_satisfied_handler],
    )
    options = ClaudeAgentOptions(
        system_prompt=(
            "You are a test agent. Use the tc3_never_satisfied tool as "
            "instructed and follow its feedback. Keep retrying with the "
            "guidance it returns."
        ),
        allowed_tools=["mcp__tc3_tools__tc3_never_satisfied"],
        mcp_servers={"tc3_tools": server},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
        max_turns=2,
    )

    prompt = (
        "Use the mcp__tc3_tools__tc3_never_satisfied tool with detail='short' "
        "and follow whatever instructions it returns. Keep retrying until it "
        "succeeds. Do not give up."
    )

    tool_use_count = 0
    user_message_count = 0
    assistant_message_count = 0
    final_result: ResultMessage | None = None
    exception: Exception | None = None
    all_messages_kinds: list[str] = []

    try:
        async for msg in query(prompt=prompt, options=options):
            kind = type(msg).__name__
            all_messages_kinds.append(kind)
            if isinstance(msg, AssistantMessage):
                assistant_message_count += 1
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        tool_use_count += 1
                        print(f"    [turn] ToolUse: {block.name}({block.input!r})")
            elif kind == "UserMessage":
                user_message_count += 1
            elif isinstance(msg, ResultMessage):
                final_result = msg
    except Exception as exc:
        exception = exc
        print(f"    EXCEPTION during query: {type(exc).__name__}: {exc}")
        traceback.print_exc()

    if final_result is None and exception is not None:
        return {
            "name": "TC3",
            "verdict": "FAIL",
            "summary": (
                f"SDK raised {type(exception).__name__} instead of returning "
                "ResultMessage. Coordinator must wrap async-for in try/except."
            ),
            "details": {
                "exception": repr(exception),
                "messages_seen": all_messages_kinds,
                "tool_use_count": tool_use_count,
            },
        }

    if final_result is None:
        return {
            "name": "TC3",
            "verdict": "FAIL",
            "summary": "Stream ended without ResultMessage and without exception.",
            "details": {
                "messages_seen": all_messages_kinds,
                "tool_use_count": tool_use_count,
            },
        }

    # Exhaustively dump ResultMessage fields.
    print("\n  ResultMessage attribute dump:")
    rm_dump: dict[str, Any] = {}
    for f in dataclasses.fields(ResultMessage):
        try:
            val = getattr(final_result, f.name)
        except Exception as exc:
            val = f"<error: {exc}>"
        rm_dump[f.name] = repr(val)
        print(f"    {f.name} = {val!r}")

    # Heuristic: did we actually hit max_turns? We configured max_turns=2.
    # If num_turns < 2, the model gave up naturally.
    hit_cap = final_result.num_turns >= 2

    verdict = "PASS" if hit_cap or final_result.is_error else "PARTIAL"
    summary = (
        f"ResultMessage captured: subtype={final_result.subtype!r}, "
        f"stop_reason={final_result.stop_reason!r}, "
        f"is_error={final_result.is_error}, num_turns={final_result.num_turns}, "
        f"errors={final_result.errors!r}, "
        f"api_error_status={final_result.api_error_status!r}. "
        f"max_turns cap (=2) {'hit' if hit_cap else 'NOT hit (natural end)'}."
    )

    return {
        "name": "TC3",
        "verdict": verdict,
        "summary": summary,
        "details": {
            "result_message_dump": rm_dump,
            "tool_use_count": tool_use_count,
            "assistant_messages": assistant_message_count,
            "user_messages": user_message_count,
            "all_messages_kinds": all_messages_kinds,
            "hit_max_turns_cap": hit_cap,
        },
    }


# --------------------------------------------------------------------------- #
# Runner                                                                      #
# --------------------------------------------------------------------------- #


async def main() -> int:
    banner("Smoke-test pre-Reporter-flesh (sessao Code #38b)")
    print("SDK: claude-agent-sdk==0.2.87")
    print("Auth: Claude Code CLI (no ANTHROPIC_API_KEY required)")

    results: list[dict[str, Any]] = []
    for tc in (
        tc1_pydantic_type_as_input_schema,
        tc2_tools_field_effect,
        tc3_max_turns_resultmessage_shape,
    ):
        banner(f"Running {tc.__name__}")
        try:
            result = await tc()
        except Exception as exc:
            traceback.print_exc()
            result = {
                "name": tc.__name__,
                "verdict": "EXCEPTION",
                "summary": f"{type(exc).__name__}: {exc}",
                "details": {"traceback": traceback.format_exc()},
            }
        results.append(result)
        print(f"\n--- {result['name']} VERDICT: {result['verdict']} ---")
        print(f"  {result['summary']}")

    # Final summary block — paste-ready for Chat.
    banner("FINAL SUMMARY — paste this into Chat")
    for r in results:
        print(f"\n{r['name']}: {r['verdict']}")
        print(f"  {r['summary']}")

    fail_count = sum(
        1 for r in results if r["verdict"] in ("FAIL", "EXCEPTION", "INCONCLUSIVE")
    )
    print(f"\nFailing TCs: {fail_count}/{len(results)}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
