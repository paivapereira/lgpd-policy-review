"""Pure tool implementations for the policy-reader MCP server.

T02a introduced this module migrating `get_clause` from the inline skeleton
in `server.py`. T02b added `find_clauses_by_law_article` alongside. T03
adds `check_applicability`, so this module now carries three public
functions; envelope helpers + vocabulary loaders + provenance helper were
extracted to `_envelope.py` co-located here.

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

from ._envelope import (
    _clause_deprecated,
    _clause_not_found,
    _empty_data_categories,
    _envelope_tool_result,
    _invalid_clause_id_format,
    _invalid_data_category,
    _invalid_law_identifier,
    _invalid_operation,
    _load_data_categories_vocabulary,
    _load_operation_vocabulary,
    _provenance_from,
)
from .models import (
    Clause,
    CompliantVerdict,
    IndeterminateVerdict,
    LoadedPolicy,
    NotApplicableVerdict,
    StatutoryReferenceEntry,
    StructuredContext,
    SubstantiveClause,
    VerificationScope,
    Verdict,
    ViolationCandidateVerdict,
)

_CLAUSE_ID_PATTERN = re.compile(r"^POL-\d{3}$")


# ---------------------------------------------------------------------------
# Public surface — get_clause (T02a) + find_clauses_by_law_article (T02b)
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


def find_clauses_by_law_article(
    lei: str,
    artigo: int,
    paragrafo: int | None,
    inciso: int | None,
    alinea: str | None,
    state: LoadedPolicy,
) -> ToolResult:
    """Find clauses matching a law-article specification (canonical §4.2).

    Match semantics are prefix-hierarchical: a stored `statutory_reference`
    entry matches when it starts hierarchically with the query
    (`lei` → `artigo` → `paragrafo` → `inciso` → `alinea`). A clause matches
    when ANY entry of its top-level `statutory_reference` list matches.
    Deprecated clauses are excluded from the result by contract (canonical
    §4.2) — operative-clause discovery is the sole use case here; historical
    retrieval goes through `get_clause` with a known `clause_id`.

    Returns the wrapper `{"clauses": [...]}` as success payload, polymorphic
    by `clause_type` and ordered by `clause_id`. Consumers MUST NOT filter or
    coerce by `clause_type` to uniformize the list (canonical §4.2). Returns
    the `INVALID_LAW_IDENTIFIER` envelope when `lei` is not in the Policy
    header's `accepted_law_identifiers` vocabulary.
    """
    accepted = state.header.accepted_law_identifiers
    if lei not in accepted:
        return _envelope_tool_result(
            _invalid_law_identifier(lei, accepted),
        )

    matched = sorted(
        (
            clause
            for clause in state.clauses.values()
            if clause.status == "active"
            and any(
                _matches(lei, artigo, paragrafo, inciso, alinea, entry)
                for entry in clause.statutory_reference
            )
        ),
        key=lambda c: c.clause_id,
    )

    payload: dict[str, Any] = {
        "clauses": [
            clause.model_dump(mode="json", exclude_none=True)
            for clause in matched
        ],
    }
    text = _render_query_text(
        lei, artigo, paragrafo, inciso, alinea, matched,
    )
    return ToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=payload,
    )


def check_applicability(
    clause_id: str,
    structured_context: dict[str, Any],
    state: LoadedPolicy,
) -> ToolResult:
    """Evaluate whether a Policy clause governs a candidate handling and,
    if so, with which verdict (canonical §4.3).

    Returns one of four verdicts in `structured_content` on success:
    `compliant`, `violation_candidate`, `indeterminate`, `not_applicable`.
    `indeterminate` is a first-class verdict per canonical §7.3 — it signals
    that static analysis of the PR cannot decide this dimension and that a
    human reviewer must verify upstream state; it does not represent
    evaluation failure.

    Every success carries the provenance trinque (`policy_schema_version`,
    `policy_version`, `legal_framework`) sourced from the loaded Policy
    header (ADR-0005 D5; canonical §6.4).

    Six error envelopes are possible: four input-validation domains
    (`INVALID_CLAUSE_ID_FORMAT`, `EMPTY_DATA_CATEGORIES`,
    `INVALID_DATA_CATEGORY`, `INVALID_OPERATION`), one existence check
    (`CLAUSE_NOT_FOUND`), and one usage error (`CLAUSE_DEPRECATED`,
    retryable). `accepted_values` in the two vocabulary envelopes is sourced
    dynamically from the loaded Policy, not hard-coded.

    Fail-fast ordering (DD-T03-8): input validations precede existence
    checks; existence checks precede the MVP-scope filter
    (`operation ≠ collection` → `not_applicable` per ADR-0007 D3); MVP-scope
    precedes applicability matching (both `operation` and
    `personal_data_categories` must intersect with the clause's `applies_to`);
    applicability precedes the control branch.
    """
    if not _CLAUSE_ID_PATTERN.match(clause_id):
        return _envelope_tool_result(_invalid_clause_id_format(clause_id))

    raw_data_categories = structured_context.get("data_categories", [])
    if not raw_data_categories:
        return _envelope_tool_result(_empty_data_categories())

    data_cat_vocab = _load_data_categories_vocabulary(state)
    for cat in raw_data_categories:
        if cat not in data_cat_vocab:
            return _envelope_tool_result(
                _invalid_data_category(cat, data_cat_vocab),
            )

    raw_operation = structured_context.get("operation", "")
    op_vocab = _load_operation_vocabulary(state)
    if raw_operation not in op_vocab:
        return _envelope_tool_result(
            _invalid_operation(raw_operation, op_vocab),
        )

    context = StructuredContext.model_validate(structured_context)

    clause = state.clauses.get(clause_id)
    if clause is None:
        return _envelope_tool_result(_clause_not_found(clause_id))

    if clause.status == "deprecated":
        tombstone = clause.tombstone
        assert tombstone is not None, (  # noqa: S101 — model invariant
            "ClauseCommon._tombstone_iff_deprecated guarantees this"
        )
        return _envelope_tool_result(
            _clause_deprecated(
                clause.clause_id,
                tombstone.successors,
                tombstone.deprecation_reason,
            ),
        )

    if not isinstance(clause, SubstantiveClause):
        return _verdict_tool_result(
            NotApplicableVerdict(
                policy_clause_ref=clause.clause_id,
                reason=(
                    f"Cláusula {clause.clause_id} é definitional — não "
                    "prescreve control. Aplicabilidade não definida para "
                    "este tipo de cláusula."
                ),
                **_provenance_from(state),
            ),
        )

    if context.operation != "collection":
        return _verdict_tool_result(
            NotApplicableVerdict(
                policy_clause_ref=clause.clause_id,
                reason=_reason_mvp_scope(context.operation),
                **_provenance_from(state),
            ),
        )

    if not _applies(clause, context):
        return _verdict_tool_result(
            NotApplicableVerdict(
                policy_clause_ref=clause.clause_id,
                reason=_reason_applicability_mismatch(clause, context),
                **_provenance_from(state),
            ),
        )

    return _verdict_for_control(clause, context, state)


# ---------------------------------------------------------------------------
# Applicability evaluation (canonical §4.3) — T03
# ---------------------------------------------------------------------------

def _applies(clause: SubstantiveClause, context: StructuredContext) -> bool:
    """True when `clause.applies_to` governs `context` (DD-T03-8 step 8).

    Both dimensions must intersect: `context.operation` ∈
    `clause.applies_to["operation"]` AND
    `context.data_categories` ∩ `clause.applies_to["personal_data_categories"]`
    is non-empty. Pack v0.1.0 has every clause declaring `operation:
    [collection]`, but the algorithm checks both fields structurally to
    preserve correctness for future clauses with broader operation scope.
    """
    clause_ops: list[str] = clause.applies_to["operation"]
    clause_cats: list[str] = clause.applies_to["personal_data_categories"]
    if context.operation not in clause_ops:
        return False
    if not set(context.data_categories) & set(clause_cats):
        return False
    return True


def _verdict_for_control(
    clause: SubstantiveClause,
    context: StructuredContext,
    state: LoadedPolicy,
) -> ToolResult:
    """Branch by `clause.control` to produce the final verdict
    (canonical §6.3 — MVP v0.1.0 supports two controls).

    `consent_required`: compares `context.legal_basis` against the canonical
    token `consent` (R1 of POL-001/POL-004 prescribes the canonical-token
    comparison explicitly). Match → `compliant`; absence → violation citing
    omission; mismatch → violation citing the non-canonical value.

    `anonymization_required`: always `indeterminate`. The `structured_context`
    has no field through which to declare an effective upstream transformation,
    so static analysis of the PR cannot decide (canonical §7.3); a human
    reviewer must verify.

    Any other `control` value is a programming error — canonical §6.3 limits
    MVP to the two above. The assertion fails loudly rather than silently
    falling through.
    """
    law_ref = _format_first_stat_ref(clause.statutory_reference[0])
    provenance = _provenance_from(state)

    if clause.control == "consent_required":
        if context.legal_basis == "consent":
            return _verdict_tool_result(
                CompliantVerdict(
                    policy_clause_ref=clause.clause_id,
                    evidence=(
                        f"Cláusula {clause.clause_id} ({law_ref}) exige "
                        "consentimento (R1: valor canônico 'consent' do "
                        "vocabulário lawful_basis de POL-000); context "
                        "declara legal_basis='consent'."
                    ),
                    **provenance,
                ),
            )
        if context.legal_basis is None:
            return _verdict_tool_result(
                ViolationCandidateVerdict(
                    policy_clause_ref=clause.clause_id,
                    evidence=(
                        f"Cláusula {clause.clause_id} ({law_ref}) exige "
                        "consentimento (R1: valor canônico 'consent' do "
                        "vocabulário lawful_basis de POL-000); context "
                        "omite o campo legal_basis."
                    ),
                    contradicted_requirement="R1",
                    **provenance,
                ),
            )
        return _verdict_tool_result(
            ViolationCandidateVerdict(
                policy_clause_ref=clause.clause_id,
                evidence=(
                    f"Cláusula {clause.clause_id} ({law_ref}) exige "
                    "consentimento (R1: valor canônico 'consent' do "
                    "vocabulário lawful_basis de POL-000); context "
                    f"declara legal_basis={context.legal_basis!r}, fora "
                    "do vocabulário canônico."
                ),
                contradicted_requirement="R1",
                **provenance,
            ),
        )

    if clause.control == "anonymization_required":
        return _verdict_tool_result(
            IndeterminateVerdict(
                policy_clause_ref=clause.clause_id,
                verification_scope=VerificationScope(
                    dimension="upstream_state",
                    prescribed_treatment="anonymization_required",
                    verification_target=(
                        f"Verificar manualmente se o tratamento que coleta "
                        f"as categorias governadas por {clause.clause_id} "
                        f"({law_ref}) aplica anonimização efetiva upstream "
                        "antes da coleta. Análise estática local de PR não "
                        "decide esta dimensão."
                    ),
                ),
                **provenance,
            ),
        )

    msg = (
        f"control {clause.control!r} fora do MVP v0.1.0 "
        "(canonical §6.3 — apenas consent_required e anonymization_required)"
    )
    raise AssertionError(msg)


# ---------------------------------------------------------------------------
# Verdict reason templates (canonical §4.3) — T03
# ---------------------------------------------------------------------------

def _reason_mvp_scope(operation: str) -> str:
    """`not_applicable` reason for `operation ≠ collection` (ADR-0007 D3)."""
    return (
        f"Operação {operation!r} fora do escopo MVP v0.1.0; somente "
        "'collection' é avaliada (ADR-0007 Decision 3)."
    )


def _reason_applicability_mismatch(
    clause: SubstantiveClause, context: StructuredContext,
) -> str:
    """`not_applicable` reason for category/operation mismatch against the
    clause's `applies_to` scope (DD-T03-8 step 8)."""
    clause_cats = sorted(clause.applies_to["personal_data_categories"])
    clause_ops = sorted(clause.applies_to["operation"])
    ctx_cats = sorted(context.data_categories)
    return (
        f"Cláusula {clause.clause_id} governa categorias "
        f"[{', '.join(clause_cats)}] e operações [{', '.join(clause_ops)}]; "
        f"context declara categorias [{', '.join(ctx_cats)}] e operação "
        f"{context.operation!r}. Sem intersecção em pelo menos uma dimensão."
    )


# ---------------------------------------------------------------------------
# Prefix-hierarchical matching (canonical §4.2)
# ---------------------------------------------------------------------------

def _matches(
    lei: str,
    artigo: int,
    paragrafo: int | None,
    inciso: int | None,
    alinea: str | None,
    entry: StatutoryReferenceEntry,
) -> bool:
    """True when `entry` starts hierarchically with the given specification.

    Field order is fixed by SCHEMA §5.1: lei → artigo → paragrafo → inciso →
    alinea. A `None` field in the specification imposes no constraint at that
    level; a non-`None` field must equal the corresponding stored field. A
    stored `None` against a non-`None` specification means the stored entry
    is strictly less specific than the query, so it does not match (per
    canonical §4.2 — "specification ≤ stored").
    """
    if entry.lei != lei or entry.artigo != artigo:
        return False
    for spec, stored in (
        (paragrafo, entry.paragrafo),
        (inciso, entry.inciso),
        (alinea, entry.alinea),
    ):
        if spec is not None and stored != spec:
            return False
    return True


# ---------------------------------------------------------------------------
# ToolResult builders
# ---------------------------------------------------------------------------

def _success_tool_result(clause: Clause) -> ToolResult:
    payload: dict[str, Any] = clause.model_dump(mode="json", exclude_none=True)
    return ToolResult(
        content=[TextContent(type="text", text=_render_clause_text(clause))],
        structured_content=payload,
    )


def _verdict_tool_result(verdict: Verdict) -> ToolResult:
    payload: dict[str, Any] = verdict.model_dump(mode="json", exclude_none=True)
    return ToolResult(
        content=[TextContent(type="text", text=_render_verdict_text(verdict))],
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


def _render_query_text(
    lei: str,
    artigo: int,
    paragrafo: int | None,
    inciso: int | None,
    alinea: str | None,
    matched: list[Clause],
) -> str:
    """Render the human-facing summary for `find_clauses_by_law_article`.

    Three rules distilled from canonical §4.2 examples (lines 431, 459, 472):
      1. The reference string carries the optional fields from the QUERY,
         not from the matched stored entries — `_format_law_reference` is the
         single source of truth for the rendering.
      2. Singular/plural agrees with `count`; `count == 0` renders the
         "Nenhuma cláusula referencia ..." phrasing.
      3. The `(N definitional, M substantive)` breakdown appears only when
         the result is heterogeneous (more than one distinct `clause_type`).
    """
    reference = _format_law_reference(lei, artigo, paragrafo, inciso, alinea)
    count = len(matched)
    if count == 0:
        return f"Nenhuma cláusula referencia {reference}."

    types = {clause.clause_type for clause in matched}
    if len(types) > 1:
        defs = sum(1 for c in matched if c.clause_type == "definitional")
        subs = count - defs
        breakdown = f" ({defs} definitional, {subs} substantive)"
    else:
        breakdown = ""

    noun = "cláusula encontrada" if count == 1 else "cláusulas encontradas"
    return f"{count} {noun} para {reference}{breakdown}."


def _render_verdict_text(verdict: Verdict) -> str:
    """Render the human-facing summary for a `check_applicability` verdict
    (Option B: `content[0].text` reproduces the verdict in one line for
    human fallback; `structured_content` carries the full payload)."""
    if isinstance(verdict, CompliantVerdict):
        return (
            f"{verdict.policy_clause_ref}: compliant. {verdict.evidence}"
        )
    if isinstance(verdict, ViolationCandidateVerdict):
        return (
            f"{verdict.policy_clause_ref}: violation_candidate "
            f"({verdict.contradicted_requirement}). {verdict.evidence}"
        )
    if isinstance(verdict, IndeterminateVerdict):
        return (
            f"{verdict.policy_clause_ref}: indeterminate. "
            f"{verdict.verification_scope.verification_target}"
        )
    return f"{verdict.policy_clause_ref}: not_applicable. {verdict.reason}"
