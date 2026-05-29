"""Smoke-test — canal de erro de @tool SDK (Eixo 2 da regra sdk-mcp-conventions).

Hipótese sob teste: um handler @tool do claude-agent-sdk pode sinalizar erro
de dominio de forma que o consumidor (coordinator, via stream) discrimine — e,
especificamente, se consegue carregar conteudo ESTRUTURADO junto com o erro
(premissa do Eixo 2), ou se precisa de um workaround tipo-Option-B como o
FastMCP.

AVISO: teste de DESCOBERTA, nao de assertion. A doc oficial do SDK NAO
documenta o contrato de retorno de @tool para erro + conteudo estruturado
(verificado work-session #47: docs so mostram {"content":[...]} e
{"content":[...], "is_error": true}). Os dois pontos marcados PROBE abaixo sao
o que o teste existe para descobrir. Ajustar contra o SDK real instalado.

Execucao (PowerShell):
    uv run --with claude-agent-sdk==0.2.87 python \\
        scripts\\smoke_tests\\sdk_tool_error_channel\\smoke_test.py

Auth: Claude Code CLI (sem ANTHROPIC_API_KEY).
"""

from __future__ import annotations

import asyncio
import sys
import traceback


def banner(t: str) -> None:
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def sub(t: str) -> None:
    print("\n" + "-" * 70 + f"\n{t}\n" + "-" * 70)


async def main() -> int:
    banner("Smoke test — canal de erro de @tool SDK (Eixo 2)")

    try:
        from claude_agent_sdk import (
            ClaudeAgentOptions,
            create_sdk_mcp_server,
            query,
            tool,
        )
    except Exception as exc:
        sub("IMPORT FAIL")
        print(f"{type(exc).__name__}: {exc}")
        return 4

    # ---- PROBE 1: forma de retorno do @tool para erro + estrutura ---------- #
    # A doc so confirma {"content":[...], "is_error": true}. O 'structuredContent'
    # aqui e a HIPOTESE a testar. Se o SDK rejeitar a chave no retorno, o except
    # de Gate 2 captura como sinal (Caminho: @tool nao aceita estrutura).
    SENTINEL = "EIXO2_STRUCT_SENTINEL_8f3a"

    @tool("failing_probe", "Retorna erro de dominio para sondar o canal", {})
    async def failing_probe(args):
        return {
            "content": [{"type": "text", "text": "erro de dominio simulado"}],
            "is_error": True,                       # snake_case, idioma Python
            "structuredContent": {                  # PROBE — sobrevive? e descartado?
                "errorCode": "PROBE_DOMAIN_ERROR",
                "isRetryable": False,
                "sentinel": SENTINEL,
            },
        }

    server = create_sdk_mcp_server(name="probe", version="0.0.1", tools=[failing_probe])

    sub("Gate 1 — server/tool construidos?")
    print(f"server = {server!r}")

    options = ClaudeAgentOptions(
        system_prompt="Voce e um probe. Chame a tool failing_probe exatamente uma vez e pare.",
        mcp_servers={"probe": server},
        allowed_tools=["mcp__probe__failing_probe"],
        permission_mode="bypassPermissions",
        setting_sources=[],
        max_turns=3,
    )

    sub("Gate 2 — DUMP do stream (reconhecimento; ler, nao julgar)")
    saw_error_flag = False
    saw_sentinel = False
    raised = False
    try:
        async for msg in query(
            prompt="Chame failing_probe uma vez.", options=options
        ):
            mt = type(msg).__name__
            # PROBE 2: como o resultado da tool chega ao consumidor? Nao sei o
            # atributo exato (UserMessage.tool_use_result? bloco no content?
            # is_error vs isError?). Dump agressivo: __dict__ inteiro do msg.
            payload = getattr(msg, "__dict__", {})
            blob = repr(payload)
            print(f"  msg {mt}: {blob[:600]}")
            if "is_error" in blob or "isError" in blob:
                saw_error_flag = True
            if SENTINEL in blob:
                saw_sentinel = True
    except Exception as exc:
        raised = True
        print(f"\nEXCECAO durante query: {type(exc).__name__}: {exc}")
        traceback.print_exc()

    # ---- Veredito por sinal observado ------------------------------------- #
    sub("VEREDITO")
    print(f"raised={raised}  saw_error_flag={saw_error_flag}  saw_sentinel={saw_sentinel}")

    if raised:
        print("\nEIXO2_INDETERMINADO — SDK levantou no retorno/stream. "
              "Possivel: @tool nao aceita 'structuredContent'. emit_report pode "
              "precisar de workaround tipo-Option-B. Ler o traceback acima.")
        return 2
    if saw_error_flag and saw_sentinel:
        print("\nEIXO2_CONFIRMADO — erro discriminavel E estrutura sobreviveu. "
              "emit_report pode usar is_error nativo + conteudo estruturado.")
        return 0
    if saw_error_flag and not saw_sentinel:
        print("\nEIXO2_PARCIAL — flag de erro chegou, mas o sentinel estruturado "
              "NAO. Estrutura nao sobrevive ao retorno do @tool; precisa ir no "
              "content (string), nao em structuredContent. Eixo 2 muda.")
        return 1
    print("\nEIXO2_NEGADO (pior caso) — nenhum discriminador de erro chegou ao "
          "consumidor. Erro silenciado: exatamente o bug que a regra previne. "
          "Investigar antes de qualquer impl do Reporter.")
    return 3


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
