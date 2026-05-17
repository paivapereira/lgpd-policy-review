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

def _format_first_stat_ref(entry: StatutoryReferenceEntry) -> str:
    """Render the first statutory_reference entry as compact Portuguese prose.

    Invariant relied on by `_render_clause_text` for active clauses: every
    loaded clause carries at least one entry — `ClauseCommon.statutory_reference`
    declares `Field(min_length=1)` in `models.py`, enforced by the loader.
    """
    parts = [f"{entry.lei} Art. {entry.artigo}"]
    if entry.paragrafo is not None:
        parts.append(f", §{entry.paragrafo}")
    if entry.inciso is not None:
        parts.append(f", inciso {entry.inciso}")
    if entry.alinea is not None:
        parts.append(f", alínea {entry.alinea}")
    return "".join(parts)


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
