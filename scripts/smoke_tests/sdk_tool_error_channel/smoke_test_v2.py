"""Smoke-test v2 — canal de erro de @tool SDK (Eixo 2), caminho SUCESSO vs ERRO.

Continuacao do v1 (que provou: is_error sobrevive; structuredContent NAO
sobrevive no caminho de erro). v1 deixou aberto o caveat (a): structuredContent
sobrevive no caminho de SUCESSO?

v2 instala DOIS handlers no mesmo server e dirige as duas chamadas, cada uma com
um sentinel distinto, para discriminar:
  - ok_probe  -> sucesso (sem is_error) + structuredContent{sentinel=OK}
  - err_probe -> erro (is_error: True)  + structuredContent{sentinel=ERR}

Pergunta resolvida: o drop de structuredContent observado no v1 e especifico do
caminho de erro, ou o SDK @tool nunca propaga structuredContent ao consumidor?

AVISO: teste de DESCOBERTA, nao de assertion. Ajustar contra o SDK real.

Execucao (PowerShell):
    uv run --with claude-agent-sdk==0.2.87 python \\
        scripts\\smoke_tests\\sdk_tool_error_channel\\smoke_test_v2.py

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
    banner("Smoke test v2 — @tool SDK structuredContent: SUCESSO vs ERRO")

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

    SENTINEL_OK = "EIXO2_OK_SENTINEL_a17c"
    SENTINEL_ERR = "EIXO2_ERR_SENTINEL_b29d"

    @tool("ok_probe", "Retorna SUCESSO com conteudo estruturado", {})
    async def ok_probe(args):
        return {
            "content": [{"type": "text", "text": "sucesso simulado"}],
            "structuredContent": {"code": "OK", "sentinel": SENTINEL_OK},
            # sem is_error
        }

    @tool("err_probe", "Retorna ERRO com conteudo estruturado", {})
    async def err_probe(args):
        return {
            "content": [{"type": "text", "text": "erro de dominio simulado"}],
            "is_error": True,
            "structuredContent": {"errorCode": "PROBE_ERR", "sentinel": SENTINEL_ERR},
        }

    server = create_sdk_mcp_server(
        name="probe", version="0.0.2", tools=[ok_probe, err_probe]
    )

    sub("Gate 1 — server/tools construidos?")
    print(f"server = {server!r}")

    options = ClaudeAgentOptions(
        system_prompt=(
            "Voce e um probe. Chame a tool ok_probe exatamente uma vez, depois "
            "a tool err_probe exatamente uma vez, e entao pare. Nao chame mais nada."
        ),
        mcp_servers={"probe": server},
        allowed_tools=["mcp__probe__ok_probe", "mcp__probe__err_probe"],
        permission_mode="bypassPermissions",
        setting_sources=[],
        max_turns=6,
    )

    sub("Gate 2 — DUMP do stream (reconhecimento; ler, nao julgar)")
    saw_ok_sentinel = False
    saw_err_sentinel = False
    saw_err_flag = False
    raised = False
    try:
        async for msg in query(
            prompt="Chame ok_probe uma vez e depois err_probe uma vez.",
            options=options,
        ):
            mt = type(msg).__name__
            payload = getattr(msg, "__dict__", {})
            blob = repr(payload)
            print(f"  msg {mt}: {blob[:700]}")
            if SENTINEL_OK in blob:
                saw_ok_sentinel = True
            if SENTINEL_ERR in blob:
                saw_err_sentinel = True
            if "is_error=True" in blob or "'is_error': True" in blob:
                saw_err_flag = True
    except Exception as exc:
        raised = True
        print(f"\nEXCECAO durante query: {type(exc).__name__}: {exc}")
        traceback.print_exc()

    sub("VEREDITO")
    print(
        f"raised={raised}  saw_ok_sentinel={saw_ok_sentinel}  "
        f"saw_err_sentinel={saw_err_sentinel}  saw_err_flag={saw_err_flag}"
    )

    if raised:
        print("\nINDETERMINADO — SDK levantou. Ler traceback.")
        return 2
    if saw_ok_sentinel and not saw_err_sentinel:
        print(
            "\nSUCESSO_PROPAGA / ERRO_DROPA — structuredContent sobrevive no "
            "caminho de sucesso mas e descartado no caminho de erro. Confirma a "
            "hipotese do v1: o drop e especifico do erro. emit_report pode usar "
            "structuredContent em sucesso, mas erro precisa empacotar no content."
        )
        return 0
    if not saw_ok_sentinel and not saw_err_sentinel:
        print(
            "\nSDK_NUNCA_PROPAGA — structuredContent nao chega ao consumidor em "
            "NENHUM caminho. Toda saida estruturada de @tool tem que ir no content "
            "(string). Eixo 2 muda mais profundamente do que o v1 sugeriu."
        )
        return 1
    if saw_ok_sentinel and saw_err_sentinel:
        print(
            "\nAMBOS_PROPAGAM — structuredContent sobrevive nos dois caminhos. "
            "Contradiz o v1: reinvestigar por que o v1 nao viu o sentinel de erro."
        )
        return 3
    print(
        "\nSO_ERRO_PROPAGA (inesperado) — sentinel de erro chegou mas o de sucesso "
        "nao. Resultado estranho; reinvestigar ordem das chamadas / max_turns."
    )
    return 5


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
