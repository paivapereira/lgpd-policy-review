"""Smoke-test v4 — structuredContent sobrevive com outputSchema DECLARADO violado?

Guarda (nao blocker). v3 provou que structuredContent de FastMCP dict NAO-tipado
sobrevive ao query() stream. Mas o scan_diff real tem shapes disjuntos sucesso vs
erro (canonical §5/§9). A tensao do ADR-0002: validacao de outputSchema ANTES da
inspecao -> falha de schema dispara _make_error_result -> isError:true, o que
quebraria a Option B se o scan_diff declarasse um outputSchema estrito.

Logica do canonical (linhas 475-477) ja IMPLICA que scan_diff nao tem outputSchema
estrito (senao o erro viraria isError:true, contradizendo "isError:false em todos
os retornos"). Este teste CONFIRMA empiricamente o que o FastMCP 3.2.4 faz quando
um outputSchema declarado e violado por um envelope de erro Option B.

Duas tools, MESMO outputSchema de sucesso (Pydantic):
  - ok_scan  -> retorna sucesso VALIDO (casa o schema)        [controle]
  - err_scan -> retorna envelope de erro que VIOLA o schema   [teste]

AVISO: teste de DESCOBERTA. PROBE C marcado: como FastMCP 3.2.4 reage a um retorno
que viola o annotation. Ler o FRAME DECISIVO, nao so o exit.

Execucao (PowerShell):
    uv run --with claude-agent-sdk==0.2.87 --with fastmcp==3.2.4 python \\
        scripts\\smoke_tests\\sdk_tool_error_channel\\smoke_test_v4.py

Auth: Claude Code CLI (sem ANTHROPIC_API_KEY).
"""

# NOTA: exit code (4 / SETUP_FAIL) MENTE — timing de conexão stdio, não PROBE C.
# Achado real (via Client direto) = tensão ADR-0002 confirmada; o caminho real
# -> ToolResult a evita. Ver RESULTS.md.

from __future__ import annotations

import asyncio
import os
import sys
import traceback

SENTINEL_OK = "EIXO2_V4_OK_d71a"
SENTINEL_ERR = "EIXO2_V4_ERR_e92b"
SERVER_KEY = "probe"


def _run_server() -> None:
    """Filho FastMCP stdio. STDOUT LIMPO (JSON-RPC). Nenhum print."""
    from fastmcp import FastMCP
    from pydantic import BaseModel

    # outputSchema de sucesso, espelhando o shape do scan_diff (canonical §9).
    class ScanSuccess(BaseModel):
        rules_version: str
        semgrep_version: str
        scan_metadata: dict
        findings: list

    mcp = FastMCP("probe")

    # PROBE C: a anotacao `-> ScanSuccess` gera o outputSchema (forma padrao do
    # FastMCP). Se o scan_diff real declarar de outra forma, espelhar. ok_scan
    # casa o schema; err_scan o viola deliberadamente.
    @mcp.tool
    def ok_scan() -> ScanSuccess:
        return {
            "rules_version": "1.0.0",
            "semgrep_version": "1.163.0",
            "scan_metadata": {"sentinel": SENTINEL_OK},
            "findings": [],
        }

    @mcp.tool
    def err_scan() -> ScanSuccess:
        # Envelope de erro Option B — NAO casa ScanSuccess (sem findings/scan_metadata).
        return {
            "errorCode": "PROBE_DOMAIN_ERROR",
            "message": "erro de dominio simulado",
            "isRetryable": False,
            "sentinel": SENTINEL_ERR,
        }

    mcp.run()


def banner(t: str) -> None:
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def sub(t: str) -> None:
    print("\n" + "-" * 70 + f"\n{t}\n" + "-" * 70)


def _struct_sentinel(tur, sentinel: str) -> bool:
    """Sentinel alcancavel como DADO em tool_use_result.structuredContent
    (profundidade-2 — conserto do bug do PROBE B do v3)."""
    if isinstance(tur, dict):
        sc = tur.get("structuredContent")
        if isinstance(sc, dict) and sentinel in repr(sc):
            return True
    return False


async def _run_test() -> int:
    banner("Smoke test v4 — outputSchema declarado violado por envelope de erro")

    try:
        from claude_agent_sdk import ClaudeAgentOptions, query
    except Exception as exc:
        sub("IMPORT FAIL (claude_agent_sdk)")
        print(f"{type(exc).__name__}: {exc}")
        return 4

    options = ClaudeAgentOptions(
        system_prompt=(
            "Voce e um probe. Chame ok_scan uma vez, depois err_scan uma vez, "
            "e pare. Nao chame mais nada."
        ),
        mcp_servers={
            SERVER_KEY: {
                "type": "stdio",
                "command": sys.executable,
                "args": [os.path.abspath(__file__), "--serve"],
            }
        },
        allowed_tools=[f"mcp__{SERVER_KEY}__ok_scan", f"mcp__{SERVER_KEY}__err_scan"],
        permission_mode="bypassPermissions",
        setting_sources=[],
        max_turns=8,
    )

    sub("Gate 1 — DUMP do stream")
    raised = False
    ok_struct = err_struct = False        # sobreviveu em structuredContent (depth-2)
    ok_called = err_called = False
    err_became_iserror = False            # err virou isError:true (validacao rejeitou)
    decisive: list[str] = []

    try:
        async for msg in query(
            prompt="Chame ok_scan e depois err_scan.", options=options
        ):
            mt = type(msg).__name__
            payload = getattr(msg, "__dict__", {})
            blob = repr(payload)
            print(f"  msg {mt}: {blob[:700]}")

            tur = getattr(msg, "tool_use_result", None)
            # is_error do ToolResultBlock no content da UserMessage
            block_iserror = None
            for blk in (payload.get("content") or []):
                if getattr(blk, "tool_use_id", None):
                    block_iserror = getattr(blk, "is_error", None)

            if SENTINEL_OK in blob:
                ok_called = True
                if _struct_sentinel(tur, SENTINEL_OK):
                    ok_struct = True
                decisive.append(f"[OK] is_error={block_iserror} tur={tur!r}")
            if SENTINEL_ERR in blob or "PROBE_DOMAIN_ERROR" in blob:
                err_called = True
                if _struct_sentinel(tur, SENTINEL_ERR):
                    err_struct = True
                if block_iserror is True:
                    err_became_iserror = True
                decisive.append(f"[ERR] is_error={block_iserror} tur={tur!r}")

    except Exception as exc:
        raised = True
        print(f"\nEXCECAO durante query: {type(exc).__name__}: {exc}")
        traceback.print_exc()

    sub("FRAME(S) DECISIVO(S)")
    for d in decisive or ["(nenhum frame de resultado capturado)"]:
        print("  " + d)

    sub("VEREDITO")
    print(
        f"raised={raised}  ok_called={ok_called}  err_called={err_called}  "
        f"ok_struct={ok_struct}  err_struct={err_struct}  "
        f"err_became_iserror={err_became_iserror}"
    )

    if raised:
        print("\nINDETERMINADO — query levantou. Ler traceback.")
        return 2
    if not (ok_called and err_called):
        print(
            "\nSETUP_FAIL — uma das tools nao foi chamada/registrada. Pode ser "
            "PROBE C: FastMCP pode ter rejeitado err_scan no REGISTRO por o retorno "
            "violar o annotation (isso ja seria um achado: nao da nem pra emitir o "
            "envelope sob outputSchema estrito). Ler o dump."
        )
        return 4
    if ok_struct and err_struct:
        print(
            "\nSCHEMA_LENIENTE — structuredContent sobreviveu nos DOIS casos, "
            "inclusive no err que viola o outputSchema. FastMCP 3.2.4 nao rejeita "
            "output violado no caminho do stream; a Option B e segura MESMO com "
            "outputSchema declarado. A tensao do ADR-0002 nao morde aqui."
        )
        return 0
    if ok_struct and not err_struct:
        print(
            "\nSCHEMA_REJEITA_ERRO (constraint confirmado) — o sucesso valido "
            "sobreviveu, mas o envelope de erro que viola o outputSchema NAO "
            f"(virou isError:true? {err_became_iserror}). Confirma a tensao do "
            "ADR-0002: scan_diff NAO pode declarar outputSchema estrito de sucesso "
            "sem quebrar a Option B. Registrar como constraint de impl."
        )
        return 1
    print(
        "\nINESPERADO — ler o frame decisivo. (ok_struct ou err_struct em estado "
        "que nao casa as hipoteses; possivel diferenca na forma do structuredContent.)"
    )
    return 3


if __name__ == "__main__":
    if "--serve" in sys.argv:
        _run_server()
    else:
        sys.exit(asyncio.run(_run_test()))
