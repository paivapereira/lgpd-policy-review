"""Smoke-test gate6 — `tools=[]` (empty list) semantics in claude-agent-sdk 0.2.87.

Gate 6 da sessão Chat #N: discriminar entre três hipóteses sobre como o SDK
trata `tools=[]` (lista vazia explícita) no `ClaudeAgentOptions`:

- **H-empty-lockdown (principal):** `tools=[]` remove todos built-ins do
  contexto do modelo, deixando apenas MCP tools de `mcp_servers={...}` +
  `allowed_tools=[...]`. Semântica de "allowlist vazia". Precedent
  conceitual: `setting_sources=[]` pós-0.1.60 ("carregar nada").
- **H-empty-as-none (alt 1):** `tools=[]` é tratado como `tools=None`
  (omissão), i.e., todos built-ins continuam visíveis. Lista vazia ==
  ausência. Precedent conceitual: `setting_sources=[]` pré-0.1.60.
- **H-empty-raises (alt 2):** SDK rejeita `tools=[]` durante init de
  `ClaudeAgentOptions` ou no `query()` — sintaxe inválida.

Discrimina via comportamento (não introspecção de `SystemMessage` —
shape não é estável entre versões do SDK; precedent dos smoke-tests
#38, #38b, #38c todos usam behavioral signal). Pergunta o modelo para
fazer duas coisas: (1) chamar uma MCP tool registrada, (2) executar
Bash. O atributo observável é se o modelo TENTA Bash (e.g.,
`ToolUseBlock(name='Bash')` no stream) ou verbaliza ausência.

Cenários:

| ID                    | `tools`        | Predição H-lockdown   | Predição H-as-none     | Predição H-raises |
|-----------------------|----------------|------------------------|------------------------|-------------------|
| S1_baseline_none      | `None`         | Bash attempted         | Bash attempted         | (N/A — só S2)     |
| S2_hypothesis_empty   | `[]`           | Bash NOT attempted     | Bash attempted         | exception em init |
| S3_sanity_read_only   | `["Read"]`     | Bash NOT attempted     | Bash NOT attempted     | (N/A — só S2)     |

S1 é controle positivo (built-ins devem estar visíveis sem restrição).
S3 é controle negativo ratificado em smoke-test #38b TC2
(`tools=["Read"]` esconde Bash do contexto). S2 é o discriminador.

Echo MCP tool é controle ortogonal — esperado succeed em todos cenários
(MCP tools governadas por `mcp_servers={...}` per smoke-test #38c).

Execução: `uv run --with claude-agent-sdk==0.2.87 python
scripts\\smoke_tests\\sdk_tools_empty_list\\smoke_test.py`

Auth: Claude Code CLI (sem `ANTHROPIC_API_KEY`).
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
    omit_tools_field: bool,
    run_index: int,
) -> dict[str, Any]:
    """Execute one (scenario, run) pair.

    `omit_tools_field=True` → kwargs sem `tools` key (canonical None /
    omissão). `omit_tools_field=False` → kwargs com `tools=tools_field`
    explícito (inclui o caso `tools=[]`).
    """
    tag = "omitted" if omit_tools_field else repr(tools_field)
    print(f"  [{scenario_id} run {run_index}] tools={tag}")

    server = create_sdk_mcp_server(
        name="t",
        version="1.0.0",
        tools=[echo_mcp_handler],
    )

    kwargs: dict[str, Any] = dict(
        system_prompt=(
            "You are a test agent. When asked to call a specific tool, "
            "invoke that exact tool exactly once with the arguments "
            "provided. If you cannot call a tool, state plainly which "
            "one you cannot call and why, then continue with whatever "
            "you can do. Do not substitute other tools."
        ),
        allowed_tools=["Read", "Bash", ECHO_TOOL_FULLNAME],
        mcp_servers={"t": server},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
        max_turns=4,
    )
    if not omit_tools_field:
        kwargs["tools"] = tools_field

    init_exception: Exception | None = None
    options: ClaudeAgentOptions | None = None
    try:
        options = ClaudeAgentOptions(**kwargs)
    except Exception as exc:
        init_exception = exc
        print(f"    INIT EXCEPTION: {type(exc).__name__}: {exc}")

    prompt = (
        f"Please do two things in order. First: call the "
        f"{ECHO_TOOL_FULLNAME} tool with text='hello'. Second: run the "
        "Bash tool with command='echo bashtest'. If you cannot call one "
        "of them, explain plainly which one and why, then continue "
        "with what you can call. Do not substitute other tools."
    )

    echo_attempts: list[dict[str, Any]] = []
    bash_attempts: list[dict[str, Any]] = []
    other_tool_attempts: list[str] = []
    text_chunks: list[str] = []
    result_subtype: str | None = None
    result_is_error: bool | None = None
    result_num_turns: int | None = None
    permission_denials: list[Any] | None = None
    query_exception: Exception | None = None

    if init_exception is None and options is not None:
        try:
            async for msg in query(prompt=prompt, options=options):
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, ToolUseBlock):
                            block_name = getattr(block, "name", "<no-name>")
                            block_input = getattr(block, "input", None)
                            if block_name == ECHO_TOOL_FULLNAME:
                                echo_attempts.append(
                                    {
                                        "name": block_name,
                                        "input": block_input,
                                    }
                                )
                            elif block_name == "Bash":
                                bash_attempts.append(
                                    {
                                        "name": block_name,
                                        "input": block_input,
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
            query_exception = exc
            print(f"    QUERY EXCEPTION: {type(exc).__name__}: {exc}")

    full_text = " ".join(text_chunks)
    lower = full_text.lower()

    # "Bash absence" verbalization heuristic: model explicitly says it
    # cannot call Bash, or the Bash tool is unavailable to it.
    absence_markers = (
        "not available",
        "no access",
        "cannot call",
        "can't call",
        "don't have access",
        "do not have access",
        "is not available",
        "isn't available",
        "unable to call",
        "cannot run",
        "can't run",
        "unable to run",
        "do not have the",
        "don't have the",
    )
    verbalizes_bash_absence = any(m in lower for m in absence_markers) and (
        "bash" in lower
    )

    return {
        "scenario": scenario_id,
        "run_index": run_index,
        "tools_field_repr": tag,
        "echo_attempts": echo_attempts,
        "echo_attempt_count": len(echo_attempts),
        "bash_attempts": bash_attempts,
        "bash_attempt_count": len(bash_attempts),
        "other_tool_attempts": other_tool_attempts,
        "verbalizes_bash_absence": verbalizes_bash_absence,
        "verbalization_snippet": (
            full_text[:240] + "..." if len(full_text) > 240 else full_text
        ),
        "result_subtype": result_subtype,
        "result_is_error": result_is_error,
        "result_num_turns": result_num_turns,
        "permission_denials": permission_denials,
        "init_exception": repr(init_exception) if init_exception else None,
        "query_exception": repr(query_exception) if query_exception else None,
    }


# --------------------------------------------------------------------------- #
# TC — tools=[] semantics discriminator                                       #
# --------------------------------------------------------------------------- #


async def tc_tools_empty() -> dict[str, Any]:
    # (scenario_id, tools_field, omit_tools_field)
    scenarios: list[tuple[str, list[str] | None, bool]] = [
        ("S1_baseline_none", None, True),  # omit kwarg entirely
        ("S2_hypothesis_empty", [], False),  # explicit empty list
        ("S3_sanity_read_only", ["Read"], False),
    ]

    all_runs: list[dict[str, Any]] = []

    for scenario_id, tools_field, omit in scenarios:
        for run_index in (1, 2):
            try:
                result = await _run_scenario(scenario_id, tools_field, omit, run_index)
                all_runs.append(result)
            except Exception as exc:
                print(
                    f"    SCENARIO RUNNER EXCEPTION ({scenario_id} run "
                    f"{run_index}): {type(exc).__name__}: {exc}"
                )
                all_runs.append(
                    {
                        "scenario": scenario_id,
                        "run_index": run_index,
                        "echo_attempt_count": 0,
                        "bash_attempt_count": 0,
                        "verbalizes_bash_absence": False,
                        "other_tool_attempts": [],
                        "verbalization_snippet": "",
                        "result_subtype": None,
                        "permission_denials": None,
                        "init_exception": None,
                        "query_exception": repr(exc),
                    }
                )

    # Aggregate per scenario.
    per_scenario: dict[str, dict[str, Any]] = {}
    for scenario_id, _, _ in scenarios:
        runs = [r for r in all_runs if r["scenario"] == scenario_id]
        if not runs:
            continue
        per_scenario[scenario_id] = {
            "runs": runs,
            "echo_per_run": [r["echo_attempt_count"] for r in runs],
            "bash_per_run": [r["bash_attempt_count"] for r in runs],
            "verbalize_per_run": [r["verbalizes_bash_absence"] for r in runs],
            "init_exc_per_run": [r["init_exception"] for r in runs],
            "query_exc_per_run": [r["query_exception"] for r in runs],
            "subtype_per_run": [r["result_subtype"] for r in runs],
            "num_turns_per_run": [r["result_num_turns"] for r in runs],
            "any_bash_attempt": any(r["bash_attempt_count"] > 0 for r in runs),
            "all_bash_attempt": all(r["bash_attempt_count"] > 0 for r in runs),
            "any_echo_attempt": any(r["echo_attempt_count"] > 0 for r in runs),
            "all_echo_attempt": all(r["echo_attempt_count"] > 0 for r in runs),
            "any_exception": any(
                r["init_exception"] or r["query_exception"] for r in runs
            ),
        }

    # Print per-scenario detail unconditionally for traceability.
    print("\n  Per-scenario aggregate:")
    for sid, agg in per_scenario.items():
        print(
            f"    {sid}: echo={agg['echo_per_run']}, "
            f"bash={agg['bash_per_run']}, "
            f"verbalize_absence={agg['verbalize_per_run']}, "
            f"subtype={agg['subtype_per_run']}, "
            f"num_turns={agg['num_turns_per_run']}"
        )
        for r in agg["runs"]:
            snip = r["verbalization_snippet"]
            if len(snip) > 120:
                snip = snip[:120] + "..."
            print(
                f"      run{r['run_index']}: "
                f"echo={r['echo_attempt_count']}, "
                f"bash={r['bash_attempt_count']}, "
                f"others={r['other_tool_attempts']}, "
                f"verbalize={r['verbalizes_bash_absence']}, "
                f"denials={r['permission_denials']}, "
                f"init_exc={r['init_exception']}, "
                f"query_exc={r['query_exception']}, "
                f"text='{snip}'"
            )

    # Verdict logic.
    s1 = per_scenario["S1_baseline_none"]
    s2 = per_scenario["S2_hypothesis_empty"]
    s3 = per_scenario["S3_sanity_read_only"]

    # First branch: did S2 raise during init? (H-empty-raises)
    s2_init_failed = any(s2["init_exc_per_run"])
    if s2_init_failed:
        return {
            "name": "TC-EMPTY",
            "verdict": "PASS_H_EMPTY_RAISES",
            "summary": (
                "`tools=[]` levantou exception em ClaudeAgentOptions init: "
                f"{s2['init_exc_per_run']}. SDK 0.2.87 rejeita lista vazia "
                "como sintaxe inválida. Finding #3 pivot inválido — manter "
                "`tools=['Read']` ou explorar `disallowed_tools=[...]`."
            ),
            "details": {"per_scenario": per_scenario},
        }

    # Sanity checks (S1 and S3 must behave per #38b TC2 ratification).
    if not s1["any_bash_attempt"]:
        return {
            "name": "TC-EMPTY",
            "verdict": "SETUP_BROKEN",
            "summary": (
                "S1 (baseline tools=None) did not attempt Bash in any run. "
                "Discriminator unusable — model must have access to Bash "
                "when tools field is omitted. Possible causes: ToolSearch "
                "interfering, system_prompt blocking, allowed_tools issue. "
                "Investigate before interpreting S2."
            ),
            "details": {"per_scenario": per_scenario},
        }
    if s3["any_bash_attempt"]:
        return {
            "name": "TC-EMPTY",
            "verdict": "SETUP_BROKEN",
            "summary": (
                "S3 (tools=['Read']) attempted Bash — contradicts ratified "
                "finding from smoke-test #38b TC2 that tools field hides "
                "non-listed built-ins. Either #38b finding regressed in "
                "0.2.87 or this test's setup leaks Bash visibility. "
                "Investigate before interpreting S2."
            ),
            "details": {"per_scenario": per_scenario},
        }

    # S1 has Bash attempts; S3 does not. Now classify S2.
    if not s2["any_bash_attempt"]:
        verdict = "PASS_H_EMPTY_LOCKDOWN"
        summary = (
            "`tools=[]` remove built-ins do contexto do modelo: S2 não "
            "tentou Bash em nenhum run (comportamento idêntico a S3 "
            "`tools=['Read']`). Hipótese principal ratificada. Lista vazia "
            "é signal válido de lockdown — finding #3 pivot procede: "
            "subagents Reporter/Matcher podem usar `tools=[]` para context "
            "restriction maximal sem prejudicar visibilidade de MCP tools "
            "(governadas por mcp_servers={...} per #38c)."
        )
    elif s2["all_bash_attempt"]:
        verdict = "PASS_H_EMPTY_AS_NONE"
        summary = (
            "`tools=[]` NÃO remove built-ins: S2 tentou Bash em todos runs "
            "(comportamento idêntico a S1 `tools=None`). Lista vazia "
            "tratada como omissão. Finding #3 pivot inválido — manter "
            "`tools=['Read']` como defensive minimum ou explorar "
            "`disallowed_tools=[...]` (caminho subóptimo per Anthropic doc, "
            "mas funcional)."
        )
    else:
        verdict = "MIXED"
        summary = (
            f"S2 inconsistente entre runs: bash_per_run="
            f"{s2['bash_per_run']}. Não classificável como lockdown nem "
            "as-none. Possível não-determinismo do SDK ou do modelo. "
            "Triagem Chat necessária antes de ratificação."
        )

    # Echo sanity (MCP tool should always succeed per #38c).
    if not s2["all_echo_attempt"]:
        summary += (
            f" ATENÇÃO: S2 não chamou echo_mcp em todos runs (echo_per_run="
            f"{s2['echo_per_run']}). Investigar — esperado succeed sempre "
            "por #38c."
        )

    return {
        "name": "TC-EMPTY",
        "verdict": verdict,
        "summary": summary,
        "details": {"per_scenario": per_scenario},
    }


# --------------------------------------------------------------------------- #
# Runner                                                                      #
# --------------------------------------------------------------------------- #


async def main() -> int:
    banner("Smoke-test gate6 — tools=[] semantics in claude-agent-sdk 0.2.87")
    print("SDK: claude-agent-sdk==0.2.87")
    print("Auth: Claude Code CLI (no ANTHROPIC_API_KEY required)")

    banner("Running tc_tools_empty")
    try:
        result = await tc_tools_empty()
    except Exception as exc:
        traceback.print_exc()
        result = {
            "name": "TC-EMPTY",
            "verdict": "EXCEPTION",
            "summary": f"{type(exc).__name__}: {exc}",
            "details": {"traceback": traceback.format_exc()},
        }

    print(f"\n--- {result['name']} VERDICT: {result['verdict']} ---")
    print(f"  {result['summary']}")

    # Final summary block — paste-ready for Chat.
    banner("FINAL SUMMARY — paste this into Chat")
    print(f"\nTC-EMPTY: {result['verdict']}")
    print(f"  {result['summary']}")
    per_scenario = result.get("details", {}).get("per_scenario", {})
    if per_scenario:
        print("\nPer-scenario:")
        for sid, agg in per_scenario.items():
            print(
                f"  {sid}: echo={agg['echo_per_run']}, "
                f"bash={agg['bash_per_run']}, "
                f"verbalize_absence={agg['verbalize_per_run']}, "
                f"subtype={agg['subtype_per_run']}, "
                f"num_turns={agg['num_turns_per_run']}"
            )
            for r in agg["runs"]:
                snippet = r["verbalization_snippet"]
                if len(snippet) > 160:
                    snippet = snippet[:160] + "..."
                print(
                    f"    run{r['run_index']}: "
                    f"echo={r['echo_attempt_count']}, "
                    f"bash={r['bash_attempt_count']}, "
                    f"others={r['other_tool_attempts']}, "
                    f"verbalize={r['verbalizes_bash_absence']}, "
                    f"denials={r['permission_denials']}, "
                    f"text='{snippet}'"
                )

    return 0 if result["verdict"].startswith("PASS_") else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
