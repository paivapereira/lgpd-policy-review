"""Pure tool implementations for the policy-reader MCP server.

T02a introduces this module and migrates `get_clause` from the inline
skeleton in `server.py`. The other two tools (`find_clauses_by_law_article`,
`check_applicability`) remain inline stubs in `server.py` until T02b / T03
migrate each in their own session — `tools.py` carries exactly one public
function (`get_clause`) in T02a.

Functions here are pure: they receive `state: LoadedPolicy` as an argument
(the same object the loader produces in T01) and return a `ToolResult`
ready for FastMCP's tool-call path. The `@mcp.tool` decorator lives in
`server.py` on a thin wrapper that injects `_STATE`.

Wire-shape convention (Option B, ratified in T02a session): the envelope
on errors travels in `structured_content` of the returned `ToolResult`;
`content[0].text` reproduces `message`; wire `isError` stays `False` and is
reserved for protocol-level failures. See `models.ErrorEnvelope` for the
full convention rationale.
"""
from __future__ import annotations

import re
from typing import Any

from fastmcp.tools.base import ToolResult
from mcp.types import TextContent

from .models import (
    Clause,
    ErrorEnvelope,
    LoadedPolicy,
    StatutoryReferenceEntry,
)

_CLAUSE_ID_PATTERN = re.compile(r"^POL-\d{3}$")
_CLAUSE_ID_EXPECTED_FORMAT = r"^POL-\d{3}$"


# ---------------------------------------------------------------------------
# Public surface — T02a contributes exactly one function
# ---------------------------------------------------------------------------

def get_clause(clause_id: str, state: LoadedPolicy) -> ToolResult:
    """Retrieve a single clause by its `clause_id` (canonical §4.1).

    Returns the clause as stored — polymorphic by `clause_type` — including
    the `tombstone` block when `status == "deprecated"`. Format errors and
    unknown `clause_id`s produce a domain envelope (see Wire-shape convention
    in the module docstring); the envelope is identified by the presence of
    `errorCode` in `structured_content`.
    """
    if not _CLAUSE_ID_PATTERN.match(clause_id):
        return _envelope_tool_result(_invalid_clause_id_format(clause_id))

    clause = state.clauses.get(clause_id)
    if clause is None:
        return _envelope_tool_result(_clause_not_found(clause_id))

    return _success_tool_result(clause)


# ---------------------------------------------------------------------------
# Error envelope builders — local to T02a
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


# ---------------------------------------------------------------------------
# ToolResult builders
# ---------------------------------------------------------------------------

def _envelope_tool_result(envelope: ErrorEnvelope) -> ToolResult:
    return ToolResult(
        content=[TextContent(type="text", text=envelope.message)],
        structured_content=envelope.model_dump(mode="json"),
    )


def _success_tool_result(clause: Clause) -> ToolResult:
    payload: dict[str, Any] = clause.model_dump(mode="json", exclude_none=True)
    return ToolResult(
        content=[TextContent(type="text", text=_render_clause_text(clause))],
        structured_content=payload,
    )


# ---------------------------------------------------------------------------
# content[0].text renderers
# ---------------------------------------------------------------------------

_ROMAN_NUMERALS: dict[int, str] = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
    6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
    11: "XI", 12: "XII", 13: "XIII", 14: "XIV", 15: "XV",
    16: "XVI", 17: "XVII", 18: "XVIII", 19: "XIX", 20: "XX",
    21: "XXI", 22: "XXII", 23: "XXIII", 24: "XXIV", 25: "XXV",
    26: "XXVI", 27: "XXVII", 28: "XXVIII", 29: "XXIX", 30: "XXX",
    31: "XXXI", 32: "XXXII", 33: "XXXIII", 34: "XXXIV", 35: "XXXV",
    36: "XXXVI", 37: "XXXVII", 38: "XXXVIII", 39: "XXXIX", 40: "XL",
    41: "XLI", 42: "XLII", 43: "XLIII", 44: "XLIV", 45: "XLV",
    46: "XLVI", 47: "XLVII", 48: "XLVIII", 49: "XLIX", 50: "L",
}


def _format_law_reference(
    lei: str,
    artigo: int,
    paragrafo: int | None = None,
    inciso: int | None = None,
    alinea: str | None = None,
) -> str:
    """Single source of truth for rendering a law reference (canonical §4.1, §4.2;
    SCHEMA §5.1 line 116).

    Shared between `get_clause` (which renders the entry stored on a clause) and
    `find_clauses_by_law_article` (which renders the caller's query — T02b).
    Sharing the formatter — not the type — keeps stored-entry and query domains
    distinct while guaranteeing the rendering stays consistent by construction.

    Brazilian legal-citation convention applied:
      - `artigo` carries the masculine ordinal indicator (`Art. 7º`).
      - `paragrafo` likewise (`§ 2º` rendered as `§2º` for compactness).
      - `inciso` is stored as an integer but rendered as a Roman numeral
        (`inciso: 1` → `I`); SCHEMA §5.1 line 116 prescribes this explicitly.
      - `alinea` is a lowercase Latin letter (`alínea a`).

    Optional fields are skipped when `None`. The Roman-numeral table covers
    inciso 1-50 inclusive; out-of-range values trigger `KeyError` deliberately
    (LGPD does not approach this range).
    """
    parts = [f"{lei} Art. {artigo}º"]
    if paragrafo is not None:
        parts.append(f", §{paragrafo}º")
    if inciso is not None:
        parts.append(f", {_ROMAN_NUMERALS[inciso]}")
    if alinea is not None:
        parts.append(f", alínea {alinea}")
    return "".join(parts)


def _format_first_stat_ref(entry: StatutoryReferenceEntry) -> str:
    """Render the first statutory_reference entry of a stored clause via the
    shared `_format_law_reference` helper.

    Invariant relied on by `_render_clause_text` for active clauses: every
    loaded clause carries at least one entry — `ClauseCommon.statutory_reference`
    declares `Field(min_length=1)` in `models.py`, enforced by the loader.
    """
    return _format_law_reference(
        entry.lei, entry.artigo, entry.paragrafo, entry.inciso, entry.alinea,
    )


def _render_clause_text(clause: Clause) -> str:
    if clause.status == "deprecated":
        tombstone = clause.tombstone
        assert tombstone is not None, (  # noqa: S101 — model invariant
            "ClauseCommon._tombstone_iff_deprecated guarantees this"
        )
        if tombstone.successors:
            joined = ", ".join(tombstone.successors)
            return f"{clause.clause_id} (deprecated): sucessores {joined}."
        return (
            f"{clause.clause_id} (deprecated): sem sucessores; razão: "
            f"{tombstone.deprecation_reason}"
        )

    first_ref = clause.statutory_reference[0]
    return (
        f"{clause.clause_id}: {clause.title} "
        f"({_format_first_stat_ref(first_ref)})."
    )
