# ADR-0009: Domain boundaries — share functions, not types, between distinct domains

**Status:** Accepted
**Date:** 2026-05-17 (sessão #22)
**Supersedes:** N/A
**Superseded by:** N/A

## Context

During T02b implementation (`find_clauses_by_law_article`, sessão #23
preceded by sessão #22.5 cleanup PR `fix/render-romano-in-T02a`), a
design decision arose about how to share rendering logic for legal
references between two tools:

1. `get_clause`, which renders the entry stored on a clause
   (`statutory_reference: list[StatutoryReferenceEntry]`).
2. `find_clauses_by_law_article`, which renders the caller's query
   (5 named parameters: `lei`, `artigo`, `paragrafo`, `inciso`,
   `alinea`).

Both contexts ultimately produce the same `content[0].text` format
(`"LGPD Art. 7º, I"`), so naïve DRY suggests a single helper shared
between them. The question is the **signature** of that helper.

## Options considered

**Option A — helper accepts `StatutoryReferenceEntry`.** Signature:
`_format_law_reference(entry: StatutoryReferenceEntry) -> str`.
`find_clauses_by_law_article` would instantiate
`StatutoryReferenceEntry(lei=..., artigo=..., ...)` from query
parameters just to call the helper.

**Option B — helper accepts 5 positional parameters.** Signature:
`_format_law_reference(lei, artigo, paragrafo, inciso, alinea) -> str`.
`get_clause`'s `_format_first_stat_ref(entry)` becomes a trivial
wrapper: `return _format_law_reference(entry.lei, entry.artigo,
entry.paragrafo, entry.inciso, entry.alinea)`. T02b consumes the
helper directly with query parameters.

## Decision

**Option B.**

## Rationale

`StatutoryReferenceEntry` represents the **state** of a legal
reference stored on a clause (Pydantic model with `Field(min_length=1)`
constraints, `extra="forbid"`, semantic role declared in
`docs/specs/policy-reader/canonical.md` §4.1). Reusing this type to
represent a **query** for legal references confuses two domains that
are deliberately distinct in the contract (canonical §4.2 separates
`statutory_reference` of a clause from the `inputSchema` of
`find_clauses_by_law_article`).

The cost of Option A is **semantic coercion**:
`StatutoryReferenceEntry` would need to mean both "stored entry" and
"query intermediate form" depending on call site. This contamination
propagates — type hints become misleading, refactors that touch one
domain risk breaking the other, the type's invariants get exercised
by code that has no semantic reason to enforce them, and downstream
consumers (e.g., future tools accepting query parameters) inherit the
ambiguity.

The cost of Option B is **mild verbosity** — 5 positional args in the
helper signature, and one trivial wrapper function in `get_clause`'s
call site. This cost is local, contained, and does not propagate.

**General principle distilled from this decision:** sharing a
**function** between two domains is OK; sharing a **type** between two
domains requires explicit semantic justification. Functions transform
values; types name concepts. Two distinct concepts should not share a
name even if their transformations overlap.

## Consequences

- Helper `_format_law_reference(lei, artigo, paragrafo, inciso,
  alinea) -> str` lives in
  `src/mcp_servers/policy_reader/tools.py` (introduced in pre-T02b
  cleanup PR `fix/render-romano-in-T02a`, sessão #22.5).
- `_format_first_stat_ref(entry)` is a trivial wrapper around
  `_format_law_reference`.
- Future tools that render legal references (e.g., T03
  `check_applicability` verdict messages citing the clause article;
  T04 `policy://vocabularies` examples) consume `_format_law_reference`
  with their own argument source — never coerce a domain-specific type
  just to share the function.
- When new pairs of domains arise (e.g., `StructuredContext` for T03
  vs the same structured input rendered for an audit log), the same
  principle applies: share the formatting function, do not share the
  type.

## Out of scope for ADR vs in scope for .claude/rules/

This ADR establishes a principle with runtime consequence: it dictates
type design and helper signatures in `tools.py`, `models.py`, and any
future module that handles polymorphic input/stored pairs. Decisions
with runtime consequence are in scope for ADR.

Coding-style decisions without runtime consequence (formatting,
naming conventions, where comments live) belong in
`.claude/rules/<topic>.md`, not in ADRs. The threshold: if the
decision would survive a code-style overhaul without changing
behavior, it's a rule; if changing the decision would require runtime
refactor and possible regression, it's an ADR.

## Reviewable conditions

Revisit this ADR when:

- A new tool's "query" form is empirically a stored entry (e.g., a
  search-by-example tool that takes an existing clause as the
  template). At that point, sharing the type might be justified
  because the two surfaces collapse into one domain.
- The number of distinct domains needing the same formatter exceeds
  the ergonomic threshold where positional args become unwieldy
  (more than ~7 positional parameters). At that point, a
  domain-neutral input dataclass might be justified.
- Empirical evidence shows that Option B introduces bugs that Option
  A would prevent. (Counter-pattern: Option A introducing bugs that
  Option B would prevent is the current empirical observation.)

ADRs are revisable when empirical evidence contradicts the rationale,
not when convenience suggests otherwise.

## References

- `docs/learning-log.md` sessão #22 entry — context of the decision
  and three-round review that surfaced it.
- `src/mcp_servers/policy_reader/tools.py` `_format_law_reference` —
  the canonical implementation.
- `docs/specs/policy-reader/canonical.md` §4.1, §4.2 — declares the
  two domains (stored entry vs query) as distinct surfaces of the
  contract.
