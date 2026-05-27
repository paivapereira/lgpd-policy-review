"""Smoke-test — `output_format=` em claude-agent-sdk 0.2.87 sob lockdown.

Pre-gate Fase 0 da sessão Chat #N: discriminar empiricamente entre tres
hipoteses sobre `output_format=` no `ClaudeAgentOptions` quando combinado
com lockdown completo (`allowed_tools=[]`, `setting_sources=[]`,
`mcp_servers={}`, `strict_mcp_config=True`, `permission_mode="dontAsk"`).

Gates probed:

- **Gate 1 — feature existe?** `ClaudeAgentOptions(output_format={...})`
  aceita o param sem `TypeError`/`AttributeError`?
- **Gate 2 — validacao schema funciona sob lockdown?** Se Gate 1 PASS,
  a query termina com `ResultMessage.subtype == "success"` (modelo
  produziu output validado pelo schema) ou com
  `subtype == "error_max_structured_output_retries"` (SDK reconhece o
  param mas algo no lockdown impede convergencia)?

Sinais observaveis e branches:

| Observacao                                              | Branch       |
|---------------------------------------------------------|--------------|
| `TypeError`/`AttributeError` em init `ClaudeAgentOptions` | Caminho 3 (feature inexistente em 0.2.87) |
| `ResultMessage.subtype == "success"`                    | Branch B viavel (output_format + lockdown coexistem) |
| `ResultMessage.subtype == "error_max_structured_output_retries"` | Gate 2 falha (investigar interacao lockdown x validacao) |
| `subtype` outro / excecao inesperada                    | Inconclusivo (reportar literal) |

Pattern operacional alinhado aos precedents:
- `scripts/smoke_tests/sdk_tools_empty_list/` (Gate 6, sessao Code #N).
- `scripts/smoke_tests/sdk_mcp_visibility/` (sessao Code #38c).
- `scripts/smoke_tests/sdk_reporter_gates/` (sessao Code #38b).

Discriminacao via comportamento real (subtype no ResultMessage) e nao
via introspecao de shape do `ClaudeAgentOptions` — shape do SDK pode
mudar entre versoes, comportamento end-to-end e mais estavel.

Execucao:

    uv run --with claude-agent-sdk==0.2.87 python \\
        scripts\\smoke_tests\\sdk_output_format_lockdown\\smoke_test.py

Auth: Claude Code CLI (sem `ANTHROPIC_API_KEY`).
"""

from __future__ import annotations

import asyncio
import sys
import traceback
from typing import Literal

from pydantic import BaseModel


# --------------------------------------------------------------------------- #
# Pydantic stub — modelo minimo para Triager decision                         #
# --------------------------------------------------------------------------- #


class TriagerDecisionStub(BaseModel):
    decision: Literal["proceed", "skip"]
    rationale: str


# --------------------------------------------------------------------------- #
# Banners                                                                     #
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
# Smoke test                                                                  #
# --------------------------------------------------------------------------- #


async def main() -> int:
    banner("Smoke test — output_format= em claude-agent-sdk 0.2.87 sob lockdown")

    # Import dentro de main para que falha de import seja capturada
    # como sinal (Caminho 3) e nao crash silencioso de import-time.
    try:
        from claude_agent_sdk import ClaudeAgentOptions, query
    except Exception as exc:
        subbanner("IMPORT FAIL — sinal forte de SDK quebrado")
        print(f"Exception: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        print("\nVerdict: INCONCLUSIVE (SDK import failed)")
        return 2

    # --- Gate 1: feature existe? ------------------------------------------ #
    subbanner("Gate 1 — ClaudeAgentOptions aceita output_format?")
    try:
        options = ClaudeAgentOptions(
            system_prompt="Voce e um Triager. Decida proceed/skip com rationale curto.",
            allowed_tools=[],
            permission_mode="dontAsk",
            setting_sources=[],
            strict_mcp_config=True,
            mcp_servers={},
            output_format={
                "type": "json_schema",
                "schema": TriagerDecisionStub.model_json_schema(),
            },
        )
    except (TypeError, AttributeError) as exc:
        print(f"Gate 1 FAIL — {type(exc).__name__}: {exc}")
        print("\nVerdict: CAMINHO_3 (output_format nao existe em 0.2.87)")
        return 3
    except Exception as exc:
        print(f"Gate 1 FAIL (unexpected): {type(exc).__name__}: {exc}")
        traceback.print_exc()
        print("\nVerdict: INCONCLUSIVE (exception inesperada em Gate 1)")
        return 4

    print("Gate 1 PASS — ClaudeAgentOptions(output_format=...) aceita o param.")
    print(f"Options type: {type(options).__name__}")
    of_attr = getattr(options, "output_format", "<no attr>")
    print(f"options.output_format = {of_attr!r}")

    # --- Gate 2: validacao schema funciona sob lockdown? ------------------ #
    subbanner("Gate 2 — query() converge para success ou max_retries?")

    prompt = (
        "Decida: proceed ou skip para este diff trivial: 'docs: typo fix'. "
        "Devolva JSON estruturado."
    )

    final_subtype: str | None = None
    seen_msg_count = 0

    try:
        async for msg in query(prompt=prompt, options=options):
            seen_msg_count += 1
            msg_type = type(msg).__name__
            subtype = getattr(msg, "subtype", "")
            structured = getattr(msg, "structured_output", None)
            # Texto curto se for AssistantMessage com TextBlock
            content_preview: str = ""
            content = getattr(msg, "content", None)
            if isinstance(content, list):
                for block in content:
                    text = getattr(block, "text", None)
                    if isinstance(text, str):
                        content_preview = text[:120].replace("\n", " ")
                        break
            print(
                f"  msg[{seen_msg_count}] {msg_type} subtype={subtype!r} "
                f"structured_output={structured!r} "
                f"text_preview={content_preview!r}"
            )
            if msg_type == "ResultMessage":
                final_subtype = subtype
    except (TypeError, AttributeError) as exc:
        print(f"Gate 2 FAIL — {type(exc).__name__} during query: {exc}")
        traceback.print_exc()
        print("\nVerdict: CAMINHO_3 (output_format aceito no init mas rejeitado em query)")
        return 3
    except Exception as exc:
        print(f"Gate 2 FAIL — exception inesperada: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        print("\nVerdict: INCONCLUSIVE")
        return 4

    # --- Verdict ----------------------------------------------------------- #
    subbanner("FINAL SUMMARY")
    print(f"Messages observed: {seen_msg_count}")
    print(f"ResultMessage.subtype = {final_subtype!r}")

    if final_subtype == "success":
        print("\nVerdict: BRANCH_B_VIAVEL (output_format + lockdown coexistem em 0.2.87)")
        return 0
    if final_subtype == "error_max_structured_output_retries":
        print(
            "\nVerdict: GATE_2_FAIL "
            "(SDK reconhece output_format mas validacao nao converge sob lockdown)"
        )
        return 1
    print(f"\nVerdict: INCONCLUSIVE (subtype inesperado: {final_subtype!r})")
    return 4


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
