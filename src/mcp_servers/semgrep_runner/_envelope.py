"""Envelope builders + ToolResult wrappers + stdout/stderr helpers.

Mirror estrutural de `policy_reader/_envelope.py`: cada `errorCode` da
canonical §5.4 tem um builder underscore-prefix retornando
`ErrorEnvelope`; dois wrappers convertem `ErrorEnvelope`/`ScanSuccessPayload`
em `ToolResult` per Option B (envelope em `structured_content`,
`content[0].text` reproduz `message` ou um resumo humano).

Os helpers `_truncate_stderr` (DD-T06-10) e `_parse_semgrep_stdout_errors`
(DD-T06-22) processam saída raw do subprocess Semgrep para
`ErrorEnvelope.details.stderr_excerpt` e para refinamento de discriminação
de `INSUFFICIENT_GIT_HISTORY` (DD-T06-6 lazy layer).

Wire-shape convention (Option B): o envelope vai em `structured_content`
do `ToolResult`; `content[0].text` reproduz `message`; wire `isError`
permanece `False`. Consumers discriminam sucesso vs erro de domínio pela
presença de `errorCode` em `structured_content`. Ver `ErrorEnvelope` em
`models.py` para o raciocínio completo da convenção.
"""
from __future__ import annotations

import json
import re

from fastmcp.tools.base import ToolResult
from mcp.types import TextContent

from .models import ErrorEnvelope, ScanSuccessPayload

_STDERR_LIMIT_DEFAULT = 1000
# `re.sub` collapses runs of 2+ whitespace chars (including \n, \t) into a
# single space. The `\s` class is unicode-aware in Python 3 by default,
# which is fine for the Semgrep banner output we typically excerpt.
_WHITESPACE_RUN = re.compile(r"\s{2,}")


# ---------------------------------------------------------------------------
# ToolResult wrappers
# ---------------------------------------------------------------------------

def _envelope_tool_result(envelope: ErrorEnvelope) -> ToolResult:
    """Mirror de `policy_reader._envelope_tool_result`: envelope de erro
    serializado em `structured_content`; `content[0].text` reproduz
    `message`; wire `isError` fica `False` (Option B).
    """
    return ToolResult(
        content=[TextContent(type="text", text=envelope.message)],
        structured_content=envelope.model_dump(mode="json"),
    )


def _scan_success_tool_result(
    payload: ScanSuccessPayload, text_summary: str,
) -> ToolResult:
    """Wrapper de sucesso: `ScanSuccessPayload` serializado em
    `structured_content`; `content[0].text` carrega resumo humano
    (DD-T06-9) com contagem + top findings ou mensagem de empty result.
    Wire `isError` fica `False` por Option B (mesma convenção do envelope
    de erro — discriminação é por presença de `errorCode`).
    """
    return ToolResult(
        content=[TextContent(type="text", text=text_summary)],
        structured_content=payload.model_dump(mode="json"),
    )


# ---------------------------------------------------------------------------
# Error envelope builders — canonical §5.4 (6 errorCodes)
# ---------------------------------------------------------------------------

def _git_ref_not_found(ref_param: str, ref_value: str) -> ErrorEnvelope:
    """Business, non-retryable. `ref_param` ∈ {"base_ref", "head_ref"}
    sinaliza qual input falhou (caller pode discriminar sem regex no
    `message`). `hint` documenta causas comuns conforme exemplo
    canonical §4.3 lines 286-307.
    """
    return ErrorEnvelope(
        errorCode="GIT_REF_NOT_FOUND",
        message=(
            f"Ref {ref_value!r} não encontrada no repositório atual."
        ),
        isRetryable=False,
        details={
            "ref_param": ref_param,
            "ref_value": ref_value,
            "hint": (
                "Verifique o valor passado; commits removidos por "
                "force-push, refs órfãs após cleanup de branches, ou "
                "shallow clone sem o histórico necessário são causas "
                "comuns."
            ),
        },
    )


def _insufficient_git_history() -> ErrorEnvelope:
    """Business, non-retryable. Emitido quando proactive
    `is-shallow-repository` retorna `true` OU quando lazy inspection
    de `errors[].message` no JSON de Semgrep detecta substring de
    shallow/baseline (DD-T06-6 refinada).
    """
    return ErrorEnvelope(
        errorCode="INSUFFICIENT_GIT_HISTORY",
        message=(
            "Histórico Git insuficiente para resolver diff entre os "
            "refs informados. Provável shallow clone — aumente "
            "`fetch-depth` no checkout do CI e reinvoque."
        ),
        isRetryable=False,
        details={"hint": "increase actions/checkout fetch-depth"},
    )


def _scan_timeout(
    timeout_seconds: int, elapsed_seconds: float,
) -> ErrorEnvelope:
    """System, retryable (per ADR-0002 D3 system-class default).
    Subprocess Semgrep terminado via `Popen.kill()` interno do
    `subprocess.run` em `TimeoutExpired` (DD-T06-1; canonical §4.3
    lines 262-281).
    """
    return ErrorEnvelope(
        errorCode="SCAN_TIMEOUT",
        message=(
            f"Scan excedeu o limite de {timeout_seconds} segundos. "
            "Subprocess Semgrep terminado após grace period."
        ),
        isRetryable=True,
        details={
            "timeout_seconds": timeout_seconds,
            "elapsed_seconds": round(elapsed_seconds, 1),
            "partial_findings_discarded": True,
        },
    )


def _semgrep_binary_unavailable(searched_paths: list[str]) -> ErrorEnvelope:
    """System, non-retryable. `shutil.which("semgrep")` retornou `None`
    no momento da invocação (DD-T06-2: verificação per-call, sem cache,
    sem abort no startup). `searched_paths` é a lista do PATH no
    momento da chamada — útil para diagnóstico do operador.
    """
    return ErrorEnvelope(
        errorCode="SEMGREP_BINARY_UNAVAILABLE",
        message=(
            "Binário `semgrep` não encontrado no PATH. Instale via "
            "`uv tool install semgrep==1.163.0` (ver ADR-0010) e "
            "reinvoque."
        ),
        isRetryable=False,
        details={"searched_paths": searched_paths},
    )


def _semgrep_execution_failed(
    exit_code: int,
    stderr_excerpt: str,
    parse_error: str | None = None,
) -> ErrorEnvelope:
    """System, retryable. Fallback genérico para exits não-mapeados
    (2, 3, 13, 99, outros) sob X1 mapping ratificado em GATE 1.
    `parse_error` populado quando a falha foi detectada na fase de
    parse Pydantic do JSON Semgrep (DD-T06-8), não no exit code do
    subprocess.
    """
    details: dict[str, object] = {
        "exit_code": exit_code,
        "stderr_excerpt": stderr_excerpt,
    }
    if parse_error is not None:
        details["parse_error"] = parse_error
    return ErrorEnvelope(
        errorCode="SEMGREP_EXECUTION_FAILED",
        message=(
            f"Execução do Semgrep falhou (exit {exit_code}). "
            "Consulte `stderr_excerpt` em `details` para diagnóstico."
        ),
        isRetryable=True,
        details=details,
    )


def _invalid_rule_set(exit_code: int, stderr_excerpt: str) -> ErrorEnvelope:
    """System, non-retryable. Rule set curado pelo projeto não-utilizável
    — sob X1 mapping (GATE 1), cobre exits 7 (config ausente/malformada
    /YAML não-parseável colapsados em "invalid configuration") e 8
    (linguagem não-suportada por regra). Empiricamente em Semgrep
    1.163.0 (pre-flight 3.E), exits 4 e 5 documentados na CLI reference
    são inalcançáveis.
    """
    return ErrorEnvelope(
        errorCode="INVALID_RULE_SET",
        message=(
            f"Rule set curado pelo projeto não-utilizável (Semgrep "
            f"exit {exit_code}). Consulte `stderr_excerpt` em "
            "`details` para identificar a regra ou config inválida."
        ),
        isRetryable=False,
        details={
            "exit_code": exit_code,
            "stderr_excerpt": stderr_excerpt,
        },
    )


# ---------------------------------------------------------------------------
# Helpers — stderr truncation + stdout JSON parse (DD-T06-10, DD-T06-22)
# ---------------------------------------------------------------------------

def _truncate_stderr(
    stderr_raw: str, limit: int = _STDERR_LIMIT_DEFAULT,
) -> str:
    """Últimos `limit` chars de stderr, com runs de whitespace ≥2
    colapsados em single space (DD-T06-10). Stderr do Semgrep
    tipicamente carrega banner "Scan Status" + ANSI-art que infla o
    excerpt sem agregar diagnóstico; a normalização preserva o sinal
    sem inflar `details`.
    """
    tail = stderr_raw[-limit:] if len(stderr_raw) > limit else stderr_raw
    return _WHITESPACE_RUN.sub(" ", tail).strip()


def _parse_semgrep_stdout_errors(stdout_raw: str) -> str | None:
    """Parse best-effort do JSON Semgrep em ramo de erro (DD-T06-22).

    Quando Semgrep exits ≠ 0, stdout ainda contém JSON estruturado com
    `errors[]` carregando `code`/`type`/`message` por entry (descoberta
    empírica em pre-flight 3.E/3.G — 1.163.0 emite JSON válido em exit
    codes 2/7/8). Esta função extrai os campos `message` (preferencial)
    ou `type` de cada error entry e os concatena em string single-line.

    Returns:
        String non-empty concatenando todas as `errors[].message` ou
        `errors[].type` válidas (separadas por " | "), OU `None` se
        stdout não é JSON parseável, não tem chave `errors`, ou
        `errors` está vazio. Failure de parse é silenciosa por design
        — caller faz fallback transparente para `stderr_excerpt` cru
        (comportamento equivalente ao default sem JSON enrichment).
    """
    try:
        parsed = json.loads(stdout_raw)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(parsed, dict):
        return None
    errors = parsed.get("errors")
    if not isinstance(errors, list) or not errors:
        return None
    fragments: list[str] = []
    for entry in errors:
        if not isinstance(entry, dict):
            continue
        msg = entry.get("message") or entry.get("long_msg") or entry.get("type")
        if isinstance(msg, str) and msg.strip():
            fragments.append(msg.strip())
    if not fragments:
        return None
    return " | ".join(fragments)
