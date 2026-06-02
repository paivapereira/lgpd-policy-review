"""Envelope builders + provenance helper + vocabulary loaders.

Coabitam neste módulo porque são co-dependentes no path de
`check_applicability`: validation envelopes consomem vocabulary loaders;
sucessos consomem `_provenance_from`. Separar por "natureza" (envelope
vs helper) fragmentaria o caminho de leitura sem ganho. Tech debt:
reavaliar separação em `_envelope.py` + `_helpers.py` se T04
(`policy://vocabularies`) ou Milestone B introduzir 3+ helpers
não-relacionados a envelope.

Wire-shape convention (Option B): the envelope is serialised into
`structured_content` of the returned `ToolResult`; `content[0].text`
reproduces `message`; wire `isError` stays `False` and is reserved for
protocol-level failures. Consumers discriminate success vs domain error
by the presence of `errorCode` in `structured_content`. See
`models.ErrorEnvelope` for the full convention rationale.
"""
from __future__ import annotations

from typing import Any, TypedDict

from fastmcp.tools.base import ToolResult
from mcp.types import TextContent

from .models import (
    DefinitionalClause,
    ErrorEnvelope,
    LoadedPolicy,
)


class Provenance(TypedDict):
    """Type of the trinque returned by `_provenance_from` — declared as a
    `TypedDict` so callers can `**unpack` it into verdict model constructors
    without collapsing the field types to `str` and shadowing the
    `Literal[verdict]` discriminator.
    """

    policy_schema_version: str
    policy_version: str
    legal_framework: str

_CLAUSE_ID_EXPECTED_FORMAT = r"^POL-\d{3}$"


# ---------------------------------------------------------------------------
# ToolResult wrapper
# ---------------------------------------------------------------------------

def _envelope_tool_result(envelope: ErrorEnvelope) -> ToolResult:
    return ToolResult(
        content=[TextContent(type="text", text=envelope.message)],
        structured_content=envelope.model_dump(mode="json"),
    )


# ---------------------------------------------------------------------------
# Error envelope builders — reused from T02a/T02b
# ---------------------------------------------------------------------------

def _invalid_clause_id_format(provided: str) -> ErrorEnvelope:
    return ErrorEnvelope(
        errorCode="INVALID_CLAUSE_ID_FORMAT",
        message=(
            f"clause_id inválido: {provided!r} não casa com o formato "
            f"esperado POL-NNN (regex {_CLAUSE_ID_EXPECTED_FORMAT})."
        ),
        isRetryable=False,
        details={
            "provided": provided,
            "expected_format": _CLAUSE_ID_EXPECTED_FORMAT,
        },
    )


def _clause_not_found(clause_id: str) -> ErrorEnvelope:
    return ErrorEnvelope(
        errorCode="CLAUSE_NOT_FOUND",
        message=f"Cláusula {clause_id} não encontrada na Política atual.",
        isRetryable=False,
        details={"clause_id": clause_id},
    )


def _invalid_law_identifier(
    provided: str, accepted: list[str],
) -> ErrorEnvelope:
    return ErrorEnvelope(
        errorCode="INVALID_LAW_IDENTIFIER",
        message=(
            f"Identificador de lei {provided!r} não está no vocabulário "
            f"aceito."
        ),
        isRetryable=False,
        details={"provided": provided, "accepted_values": sorted(accepted)},
    )


# ---------------------------------------------------------------------------
# Error envelope builders — new in T03
# ---------------------------------------------------------------------------

def _clause_deprecated(
    clause_id: str,
    successors: list[str],
    deprecation_reason: str,
) -> ErrorEnvelope:
    """Retryable envelope: caller invoked `check_applicability` on a
    deprecated clause. Assimetria deliberada com `get_clause`, que devolve
    sucesso com tombstone para recuperação histórica (canonical §2.2 /
    §5.3); aqui é erro de uso, pois avaliação de aplicabilidade sobre
    cláusula desativada é sempre ambígua. `isRetryable=True` sinaliza ao
    caller que reinvocar com um dos `successors` é o caminho de remediação.
    """
    return ErrorEnvelope(
        errorCode="CLAUSE_DEPRECATED",
        message=(
            f"Cláusula {clause_id} está deprecated; reinvoque "
            f"check_applicability sobre um dos sucessores."
        ),
        isRetryable=True,
        details={
            "clause_id": clause_id,
            "successors": list(successors),
            "deprecation_reason": deprecation_reason,
        },
    )


def _invalid_data_category(
    provided: str, accepted: set[str],
) -> ErrorEnvelope:
    """`structured_context.data_categories` contém um elemento fora do
    vocabulário canônico definido em POL-000 (`defines.entries[].name`).
    `accepted_values` é dinâmico — carregado do estado atual da Política,
    não hard-coded (canonical §5.4 nota dinâmica).
    """
    return ErrorEnvelope(
        errorCode="INVALID_DATA_CATEGORY",
        message=(
            f"Categoria de dados {provided!r} não está no vocabulário "
            f"canônico de POL-000."
        ),
        isRetryable=False,
        details={"provided": provided, "accepted_values": sorted(accepted)},
    )


def _invalid_operation(
    provided: str, accepted: set[str],
) -> ErrorEnvelope:
    """`structured_context.operation` está fora do vocabulário canônico
    de operações da Política. `accepted_values` é dinâmico (canonical
    §5.4 nota dinâmica).
    """
    return ErrorEnvelope(
        errorCode="INVALID_OPERATION",
        message=(
            f"Operação {provided!r} não está no vocabulário canônico "
            f"de operações."
        ),
        isRetryable=False,
        details={"provided": provided, "accepted_values": sorted(accepted)},
    )


def _empty_data_categories() -> ErrorEnvelope:
    """`structured_context.data_categories` é uma lista vazia. Validação
    semântica anterior à construção do `StructuredContext` Pydantic
    (DD-T03-4): a forma estrutural permite lista vazia para que este
    errorCode possa ser emitido com mensagem específica em vez do erro
    genérico de validação Pydantic.
    """
    return ErrorEnvelope(
        errorCode="EMPTY_DATA_CATEGORIES",
        message=(
            "data_categories não pode ser uma lista vazia; informe ao "
            "menos uma categoria do vocabulário canônico de POL-000."
        ),
        isRetryable=False,
        details={},
    )


# ---------------------------------------------------------------------------
# Provenance helper (DD-T03-5)
# ---------------------------------------------------------------------------

def _provenance_from(state: LoadedPolicy) -> Provenance:
    """Source-of-truth única do trinque de provenance (canonical §6.4).

    Injetado inline em todo retorno de sucesso de `check_applicability`
    (4 vereditos). Nunca duplicar em campo separado, nunca derivar de
    outra fonte. ADR-0005 D5 prescreve presença obrigatória.
    """
    return Provenance(
        policy_schema_version=state.header.policy_schema_version,
        policy_version=state.header.policy_version,
        legal_framework=state.header.legal_framework,
    )


# ---------------------------------------------------------------------------
# Vocabulary loaders (DD-T03-10)
# ---------------------------------------------------------------------------

def _load_data_categories_vocabulary(state: LoadedPolicy) -> set[str]:
    """Extrai o conjunto de categorias declaradas em POL-000.

    POL-000 é a única `DefinitionalClause` carregada no MVP; o loader
    do T01 garante sua presença, e a invariante de tipagem é assegurada
    aqui via `isinstance` para o type narrowing.
    """
    pol_000 = state.clauses.get("POL-000")
    assert pol_000 is not None, "POL-000 obrigatória em T01 invariant"
    assert isinstance(pol_000, DefinitionalClause), (
        f"POL-000 deve ser DefinitionalClause, mas é {type(pol_000).__name__}"
    )
    entries: Any = pol_000.defines.get("entries", [])
    names: set[str] = set()
    for entry in entries:
        name = entry.get("name")
        assert name is not None, (
            f"POL-000 entry sem campo 'name': {entry!r} "
            "(SCHEMA §5.3 invariant)"
        )
        names.add(name)
    return names


def _load_data_category_examples(state: LoadedPolicy) -> dict[str, list[str]]:
    """Mapeia cada categoria de POL-000 aos seus `canonical_examples`.

    Irmã de `_load_data_categories_vocabulary` (que devolve só os nomes — o
    conjunto de membership que o motor confia em `check_applicability`). Esta
    devolve o enriquecimento `name -> canonical_examples`, consumido
    EXCLUSIVAMENTE pela exposição experimental (arm C2 do discriminante de
    exposição de categorias) em `get_vocabularies`; NÃO faz parte do default
    names-only de produção. Mesma invariante de tipagem de POL-000
    (`DefinitionalClause`) que a irmã.
    """
    pol_000 = state.clauses.get("POL-000")
    assert pol_000 is not None, "POL-000 obrigatória em T01 invariant"
    assert isinstance(pol_000, DefinitionalClause), (
        f"POL-000 deve ser DefinitionalClause, mas é {type(pol_000).__name__}"
    )
    entries: Any = pol_000.defines.get("entries", [])
    examples: dict[str, list[str]] = {}
    for entry in entries:
        name = entry.get("name")
        assert name is not None, (
            f"POL-000 entry sem campo 'name': {entry!r} "
            "(SCHEMA §5.3 invariant)"
        )
        examples[name] = list(entry.get("canonical_examples", []))
    return examples


def _load_operation_vocabulary(state: LoadedPolicy) -> set[str]:
    """Extrai o conjunto de operações do vocabulário `operation`.

    `state.vocabularies["operation"]` é garantido pelo loader do T01
    (T01 valida que a Política carrega os 4 vocabulários jurisdicionais
    obrigatórios em SCHEMA §10).
    """
    vocab = state.vocabularies.get("operation")
    assert vocab is not None, "operation vocab obrigatório em T01"
    names: set[str] = set()
    for entry in vocab.values:
        name = entry.get("name")
        assert name is not None, (
            f"operation vocab entry sem campo 'name': {entry!r}"
        )
        names.add(name)
    return names
