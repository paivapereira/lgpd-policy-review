"""policy-reader MCP server.

Exposes the versioned Data Protection Policy under the jurisdictional
framework declared in its header (`legal_framework`) as queryable resource
and as compliance-evaluation tool. See `docs/specs/policy-reader/canonical.md`
for the contract.

T01 wires the Policy loader to the bootstrap path and replaces the
`policy://schema-version` resource handler with one that returns the real
handshake payload (`policy_schema_version`, `policy_version`,
`legal_framework`, `compatible_schema_range`).

T02a migrates `get_clause` from an inline skeleton into a thin wrapper that
delegates to `tools.get_clause` (pure function in `tools.py`); T02b does the
same for `find_clauses_by_law_article`; T03 does the same for
`check_applicability`. The remaining resource (`policy://catalog`) is the
only skeleton stub left, pending T04.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.tools.base import ToolResult

from . import tools
from .loader import COMPATIBLE_SCHEMA_RANGE, load_policy, resolve_policy_root
from .models import LoadedPolicy

mcp = FastMCP("policy-reader")

# Module-level state populated by `_bootstrap`. Handlers below assert it is
# not None when invoked. Tests that load a fixture Policy directly via
# `loader.load_policy` do not touch this state; tests that invoke
# `mcp.read_resource(...)` call `_bootstrap` first and reset it in teardown.
_STATE: LoadedPolicy | None = None


def _bootstrap(root: Path | None = None) -> None:
    """Load the Policy and populate `_STATE`. On `PolicyLoadError`, write
    the message to stderr and exit non-zero — `mcp.run()` is never reached.
    """
    global _STATE
    from .errors import PolicyLoadError

    try:
        _STATE = load_policy(resolve_policy_root(root))
    except PolicyLoadError as exc:
        print(f"[policy-reader] startup failed: {exc}", file=sys.stderr)
        sys.exit(1)


def _reset_state_for_tests() -> None:
    """Teardown hook used by tests that exercise `_bootstrap` to avoid
    cross-test pollution of `_STATE`. Production code never calls this.
    """
    global _STATE
    _STATE = None


# =============================================================================
# Resources
# =============================================================================

@mcp.resource("policy://catalog")
def get_catalog() -> dict[str, Any]:
    """Index of all clauses in the current Policy.

    Each entry carries clause_id, title, status, and article_sources_summary.
    Deprecated clauses include successors. Use this resource for discovery
    of available clauses without invoking tools.

    [SKELETON STUB — returns empty list; real loader lands in T04.]
    """
    return {
        "_stub": "policy-reader skeleton — get_catalog not yet implemented",
        "clauses": [],
    }


@mcp.resource("policy://schema-version", mime_type="application/json")
def get_schema_version() -> dict[str, Any]:
    """Dual handshake (structural + jurisdictional) for the consumer.

    Returns `policy_schema_version` and `policy_version` from the loaded
    Policy header, `legal_framework` (the jurisdiction declared by the
    header, immutable for the lifetime of the server), and
    `compatible_schema_range` (constant of this implementation). The
    consumer aborts before invoking tools if either axis falls outside
    its accepted set — see canonical.md §3.2 / §6.3.
    """
    assert _STATE is not None, "policy-reader bootstrap did not run"
    return {
        "policy_schema_version": _STATE.header.policy_schema_version,
        "policy_version": _STATE.header.policy_version,
        "legal_framework": _STATE.header.legal_framework,
        "compatible_schema_range": str(COMPATIBLE_SCHEMA_RANGE),
    }


# =============================================================================
# Tools
# =============================================================================

@mcp.tool
def get_clause(clause_id: str) -> ToolResult:
    """Retrieve a single Policy clause by its stable `clause_id`.

    Use this when the caller already knows the exact identifier (e.g. from
    `policy://catalog`, from a previous `find_clauses_by_law_article` call,
    or from the `successors` field of a `CLAUSE_DEPRECATED` error returned
    by `check_applicability`). Do not use this to search clauses by law
    article — use `find_clauses_by_law_article`. Do not use this to evaluate
    whether a clause governs a code-handling context — use
    `check_applicability`.

    Returns the clause object as stored, polymorphic by `clause_type`:
    `definitional` clauses (POL-000 is the MVP instance) carry `defines`
    and `out_of_scope`; `substantive` clauses carry `applies_to`, `control`,
    `requirements`, and `exceptions`. Every clause carries `clause_id`,
    `title`, `clause_type`, `status`, `policy_schema_version`, and
    `statutory_reference`. Deprecated clauses additionally carry a
    `tombstone` block with `successors`, `effective_until`, and
    `deprecation_reason` — deprecated clauses are not errors here, since
    historical retrieval is a legitimate use case.

    Errors are returned as an envelope `{errorCode, message, isRetryable,
    details}` in `structuredContent`; `content[0].text` reproduces
    `message`. Domain errors: `INVALID_CLAUSE_ID_FORMAT` when `clause_id`
    does not match `^POL-\\d{3}$`; `CLAUSE_NOT_FOUND` when the format is
    valid but no clause with that identifier exists in the current Policy.
    Both are non-retryable.
    """
    assert _STATE is not None, "policy-reader bootstrap did not run"
    return tools.get_clause(clause_id, _STATE)


@mcp.tool
def find_clauses_by_law_article(
    lei: str,
    artigo: int,
    paragrafo: int | None = None,
    inciso: int | None = None,
    alinea: str | None = None,
) -> ToolResult:
    """Find Policy clauses that reference a given law article (or sub-section
    of it).

    Use this when the caller needs to enumerate clauses applicable to a
    specific piece of law without knowing clause identifiers in advance.
    Typical flow: the caller has structured context describing handling of
    personal data and needs to discover which clauses operate over the
    relevant law article. Do not use this when the caller already knows the
    `clause_id` — use `get_clause` instead. Do not use this to evaluate
    whether a clause applies to a context — use `check_applicability`.

    Specification is hierarchical and progressive. `lei` and `artigo` are
    required; `paragrafo`, `inciso`, `alinea` are optional and narrow the
    search. A clause matches when ANY element of its `statutory_reference`
    list starts hierarchically with the given specification. A query for
    `{lei: LGPD, artigo: 7}` returns all active clauses whose
    `statutory_reference` begins with LGPD Art. 7º, regardless of inciso;
    `{lei: LGPD, artigo: 7, inciso: 1}` returns only clauses tied
    specifically to inciso 1. `inciso` is encoded as integer (canonical
    form); rendering as Roman numeral lives in the presentation layer.

    Returns the object `{clauses: [...]}` in `structuredContent`. Each entry
    carries the polymorphic clause structure produced by `get_clause`, minus
    the `tombstone` block — deprecated clauses are excluded from results
    since this tool is for discovering operative clauses. The list MAY mix
    `clause_type: definitional` and `clause_type: substantive` when the same
    article is referenced by both kinds; consumers MUST NOT filter or coerce
    by `clause_type` to uniformize the list. Empty match is not an error:
    returns `{clauses: []}` with wire `isError: false`.

    Domain error: `INVALID_LAW_IDENTIFIER` (non-retryable) when `lei` is not
    in the Policy header's `accepted_law_identifiers` vocabulary. The
    envelope follows the Option B convention (envelope in `structuredContent`
    with `errorCode`; `content[0].text` reproduces `message`).
    """
    assert _STATE is not None, "policy-reader bootstrap did not run"
    return tools.find_clauses_by_law_article(
        lei, artigo, paragrafo, inciso, alinea, _STATE,
    )


@mcp.tool
def check_applicability(
    clause_id: str,
    structured_context: dict[str, Any],
) -> ToolResult:
    """Evaluate whether a Policy clause governs a candidate handling and,
    if so, with which verdict (canonical §4.3).

    Use this when you have a `clause_id` and a `structured_context`
    describing a data-processing operation observed in a pull request
    (`data_categories`, `operation`, optional `legal_basis`), and need a
    verdict on whether the handling aligns with the clause's prescription.

    Returns one of four verdicts in `structured_content` on success:
      - `compliant`: candidate satisfies the clause requirement; `evidence`
        cites the requirement and the canonical token observed.
      - `violation_candidate`: candidate contradicts a requirement;
        `contradicted_requirement` identifies which requirement (e.g.,
        "R1") and `evidence` differentiates the sub-case (omission vs.
        non-canonical value).
      - `indeterminate`: static analysis of the PR cannot decide this
        dimension; `verification_scope` names the dimension (e.g.,
        `upstream_state`), the prescribed treatment, and what a human
        reviewer must verify. `indeterminate` is a first-class verdict
        per canonical §7.3 — it signals epistemic honesty, not failure.
      - `not_applicable`: the clause does not govern this context; `reason`
        explains the boundary (MVP scope per ADR-0007 D3, or applicability
        mismatch between the clause's `applies_to` and the context).

    Every success carries the provenance trinque (`policy_schema_version`,
    `policy_version`, `legal_framework`) sourced from the loaded Policy
    header (ADR-0005 D5; canonical §6.4).

    Six error envelopes are possible (wire `isError: false`; envelope in
    `structured_content` discriminated by presence of `errorCode` per
    Option B):
      - `INVALID_CLAUSE_ID_FORMAT`: `clause_id` does not match `POL-NNN`.
      - `EMPTY_DATA_CATEGORIES`: `data_categories` is the empty list.
      - `INVALID_DATA_CATEGORY`: an element of `data_categories` is not
        in POL-000's canonical vocabulary (`accepted_values` is dynamic).
      - `INVALID_OPERATION`: `operation` is not in the canonical
        operation vocabulary (`accepted_values` is dynamic).
      - `CLAUSE_NOT_FOUND`: `clause_id` does not exist in the loaded
        Policy.
      - `CLAUSE_DEPRECATED` (retryable): the clause is deprecated; `details`
        carries `successors` and `deprecation_reason`. Asymmetric with
        `get_clause`, which returns success-with-tombstone for the same
        clause — historical retrieval is legitimate there; applicability
        evaluation on a deprecated clause is a usage error here
        (canonical §2.2 / §5.3).
    """
    assert _STATE is not None, "policy-reader bootstrap did not run"
    return tools.check_applicability(clause_id, structured_context, _STATE)


if __name__ == "__main__":
    _bootstrap()
    mcp.run()
