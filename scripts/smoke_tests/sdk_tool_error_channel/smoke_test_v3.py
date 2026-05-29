"""Smoke-test v3 — structuredContent de server FastMCP sobrevive ao query() stream?

v1/v2 provaram: para SDK @tool in-process, structuredContent e DROPADO no
bridge (so content + is_error chegam). Mas isso era in-process. A pergunta que
fica de pe — e que BLOQUEIA a Peca 1 do item 3 — e sobre servers FastMCP
full-fledged (policy-reader, semgrep-runner): o coordinator os consome pelo
MESMO query() stream, e a regra/Peca 1 manda discriminar erro por "presenca de
errorCode em structuredContent". Se o stream estripa structuredContent tambem
de servers stdio, a estrategia Option B do coordinator quebra.

Este teste registra um FastMCP stdio MINIMO (self-spawn via --serve) cuja tool
devolve um dict no formato do envelope Option B (errorCode/isRetryable/sentinel,
wire isError:false) e observa o ToolResultBlock + tool_use_result no stream.

AVISO: teste de DESCOBERTA. Dois PROBEs marcados abaixo (forma do decorator
FastMCP 3.2.4; onde o sentinel aterrissa). Ler o FRAME DECISIVO, nao so o exit.

Execucao (PowerShell) — note os DOIS --with (precisa de fastmcp no env):
    uv run --with claude-agent-sdk==0.2.87 --with fastmcp==3.2.4 python \\
        scripts\\smoke_tests\\sdk_tool_error_channel\\smoke_test_v3.py

Auth: Claude Code CLI (sem ANTHROPIC_API_KEY).
"""

# NOTA: exit code (1 / ERRORCODE_VIA_CONTENT) MENTE — bug de heurística
# profundidade-1 no veredito. Achado real = OPTION_B_VIÁVEL. Ver RESULTS.md.

from __future__ import annotations

import asyncio
import os
import sys
import traceback

SENTINEL = "EIXO2_FASTMCP_SENTINEL_c41e"
SERVER_KEY = "probe"
TOOL_NAME = "fastmcp_probe"
FQ_TOOL = f"mcp__{SERVER_KEY}__{TOOL_NAME}"


def _run_server() -> None:
    """Processo filho: FastMCP stdio minimo. STDOUT TEM QUE FICAR LIMPO —
    transporte stdio usa stdout para JSON-RPC. Nenhum print aqui."""
    from fastmcp import FastMCP

    mcp = FastMCP("probe")

    # PROBE A: forma do decorator em FastMCP 3.2.4. Se `@mcp.tool` quebrar no
    # import, trocar pela forma usada em src/mcp_servers/semgrep_runner (prov.
    # @mcp.tool()). O server falho aparece como tool ausente no init do stream.
    @mcp.tool
    def fastmcp_probe() -> dict:
        # Option B fiel (ADR-0002 §3, como semgrep-runner): retorna dict ->
        # structuredContent + wire isError:false; discriminacao por errorCode.
        return {
            "errorCode": "PROBE_DOMAIN_ERROR",
            "message": "erro de dominio simulado (Option B)",
            "isRetryable": False,
            "sentinel": SENTINEL,
        }

    mcp.run()  # stdio por default


def banner(t: str) -> None:
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def sub(t: str) -> None:
    print("\n" + "-" * 70 + f"\n{t}\n" + "-" * 70)


async def _run_test() -> int:
    banner("Smoke test v3 — structuredContent de FastMCP via query() stream")

    try:
        from claude_agent_sdk import ClaudeAgentOptions, query
    except Exception as exc:
        sub("IMPORT FAIL (claude_agent_sdk)")
        print(f"{type(exc).__name__}: {exc}")
        return 4

    options = ClaudeAgentOptions(
        system_prompt=f"Chame a tool {TOOL_NAME} exatamente uma vez e pare.",
        mcp_servers={
            SERVER_KEY: {
                "type": "stdio",
                "command": sys.executable,                 # python do env uv (tem fastmcp)
                "args": [os.path.abspath(__file__), "--serve"],
            }
        },
        allowed_tools=[FQ_TOOL],
        permission_mode="bypassPermissions",
        setting_sources=[],
        max_turns=6,
    )

    sub("Gate 1 — DUMP do stream (reconhecimento)")
    server_registered = False
    tool_called = False
    raised = False
    decisive_frames: list[str] = []
    sentinel_in_struct = False   # sentinel alcancavel como DADO estruturado
    sentinel_in_text = False     # sentinel so dentro de string/content-text
    errorcode_seen = False

    try:
        async for msg in query(prompt=f"Chame {TOOL_NAME} uma vez.", options=options):
            mt = type(msg).__name__
            payload = getattr(msg, "__dict__", {})
            blob = repr(payload)
            print(f"  msg {mt}: {blob[:700]}")

            if mt == "SystemMessage" and FQ_TOOL in blob:
                server_registered = True

            # Frame decisivo: o resultado da tool. Inspecionar tool_use_result
            # (canal mais rico, viu-se em v2) e o ToolResultBlock.
            tur = getattr(msg, "tool_use_result", None)
            content = None
            for blk in (payload.get("content") or []):
                if getattr(blk, "tool_use_id", None):  # ToolResultBlock
                    content = getattr(blk, "content", None)
            if tur is not None or content is not None:
                if FQ_TOOL in blob or "PROBE_DOMAIN_ERROR" in blob or SENTINEL in blob:
                    tool_called = True
                    decisive_frames.append(
                        f"tool_use_result type={type(tur).__name__} "
                        f"value={tur!r}\n      ToolResultBlock.content={content!r}"
                    )
                    # PROBE B: o sentinel aterrissa como DADO (dict/estrutura) ou
                    # so como texto serializado? dict alcancavel => structuredContent
                    # sobreviveu; so em string => estripado, parseavel via content.
                    if isinstance(tur, (dict, list)) and SENTINEL in repr(tur):
                        # se for dict com a chave, ou lista de blocos nao-texto
                        if isinstance(tur, dict) and "sentinel" in tur:
                            sentinel_in_struct = True
                        else:
                            sentinel_in_text = True
                    if isinstance(tur, str) and SENTINEL in tur:
                        sentinel_in_text = True
            if "PROBE_DOMAIN_ERROR" in blob:
                errorcode_seen = True
            if SENTINEL in blob and not (sentinel_in_struct or sentinel_in_text):
                sentinel_in_text = True  # apareceu em algum frame, trato como texto

    except Exception as exc:
        raised = True
        print(f"\nEXCECAO durante query: {type(exc).__name__}: {exc}")
        traceback.print_exc()

    sub("FRAME(S) DECISIVO(S)")
    if decisive_frames:
        for f in decisive_frames:
            print("  " + f)
    else:
        print("  (nenhum frame de resultado da tool capturado)")

    sub("VEREDITO")
    print(
        f"raised={raised}  server_registered={server_registered}  "
        f"tool_called={tool_called}  errorcode_seen={errorcode_seen}  "
        f"sentinel_in_struct={sentinel_in_struct}  sentinel_in_text={sentinel_in_text}"
    )

    if raised:
        print("\nINDETERMINADO — query levantou. Ler traceback.")
        return 2
    if not tool_called:
        print(
            "\nSETUP_FAIL — a tool FastMCP nao foi chamada/registrada. Provavel "
            "PROBE A (forma do decorator) ou fastmcp ausente do env. NAO e achado "
            "sobre structuredContent; corrigir o server antes de concluir."
        )
        return 4
    if sentinel_in_struct:
        print(
            "\nOPTION_B_VIAVEL — structuredContent de FastMCP SOBREVIVEU ao stream "
            "como dado estruturado. A Peca 1 ('errorCode no ToolResultBlock') se "
            "sustenta; a estrategia Option B do coordinator e viavel via query()."
        )
        return 0
    if sentinel_in_text or errorcode_seen:
        print(
            "\nERRORCODE_VIA_CONTENT — structuredContent-como-campo NAO sobreviveu, "
            "mas o errorCode/sentinel chegou serializado no content/tool_use_result. "
            "Discriminacao ainda POSSIVEL, porem parseando content, nao "
            "structuredContent. A Peca 1 precisa trocar 'presenca de errorCode em "
            "structuredContent' por 'em content'. Ler o frame decisivo."
        )
        return 1
    print(
        "\nOPTION_B_MORRE_NO_STREAM (pior caso) — nem estrutura nem errorCode "
        "chegaram ao consumidor. A estrategia Option B do coordinator NAO funciona "
        "via query() stream. Peca 1 e o desenho de error-handling do coordinator "
        "precisam ser repensados antes de qualquer impl."
    )
    return 3


if __name__ == "__main__":
    if "--serve" in sys.argv:
        _run_server()
    else:
        sys.exit(asyncio.run(_run_test()))
