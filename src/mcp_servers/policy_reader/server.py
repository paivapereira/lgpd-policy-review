"""policy-reader MCP server.

Exposes the versioned LGPD Data Protection Policy as queryable resource
and as compliance-evaluation tool. See docs/specs/policy-reader/canonical.md
for the contract.
"""
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("policy-reader")


# =============================================================================
# Resources
# =============================================================================

@mcp.resource("policy://catalog")
def get_catalog() -> dict[str, Any]:
    """Index of all clauses in the current Policy.

    Each entry carries clause_id, title, status, and article_sources_summary.
    Deprecated clauses include successors. Use this resource for discovery
    of available clauses without invoking tools.

    [SKELETON STUB — returns empty list; real loader lands in a later commit.]
    """
    return {
        "_stub": "policy-reader skeleton — get_catalog not yet implemented",
        "clauses": [],
    }


@mcp.resource("policy://schema-version")
def get_schema_version() -> dict[str, Any]:
    """Schema version handshake.

    Returns policy_schema_version (the structural schema), policy_version
    (the content), and compatible_schema_range. Read this before invoking
    tools to verify schema compatibility with your consumer expectations.

    [SKELETON STUB — returns hardcoded values; real loader lands in a later commit.]
    """
    return {
        "_stub": "policy-reader skeleton — get_schema_version not yet implemented",
        "policy_schema_version": "0.1.0",
        "policy_version": "0.1.0",
        "compatible_schema_range": "0.x",
    }


# =============================================================================
# Tools
# =============================================================================

@mcp.tool
def get_clause(clause_id: str) -> dict[str, Any]:
    """Retrieve a single clause by its identifier.

    Use this when you have a clause_id (e.g. POL-000) and need the full clause
    structure: article_source, requirements, exceptions, status, and tombstone
    if deprecated. For deprecated clauses, the returned object includes a
    tombstone field with successors, effective_until, and deprecation_reason
    — retrieval is legitimate (historical audit).

    Do not use this for searching by law article — use
    `find_clauses_by_law_article` instead. Do not use this for compliance
    evaluation — use `check_applicability` instead.

    [SKELETON STUB — echoes input; real implementation lands in a later commit.]
    """
    return {
        "_stub": "policy-reader skeleton — get_clause not yet implemented",
        "clause_id_received": clause_id,
    }


@mcp.tool
def find_clauses_by_law_article(
    lei: str,
    artigo: int,
    paragrafo: int | None = None,
    inciso: int | None = None,
    alinea: str | None = None,
) -> dict[str, Any]:
    """Find clauses referencing a specific article of a law.

    Use this when you have a law reference (e.g. LGPD, Art. 7, inciso IX) and
    need to discover which clauses in the Policy invoke that article. Supports
    hierarchical narrowing: provide `lei` + `artigo` for broad search; add
    `paragrafo`, `inciso`, `alinea` to narrow further.

    Returns a list of matching clauses (deprecated clauses excluded — for
    historical retrieval, use `get_clause` with a known clause_id).

    Do not use this when you already have a clause_id — use `get_clause`.

    [SKELETON STUB — returns empty list; real implementation lands in a later commit.]
    """
    return {
        "_stub": "policy-reader skeleton — find_clauses_by_law_article not yet implemented",
        "lei_received": lei,
        "artigo_received": artigo,
        "clauses": [],
    }


@mcp.tool
def check_applicability(
    clause_id: str,
    structured_context: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate whether a clause applies to a structured operational context.

    Use this when you have a clause_id and a structured_context describing a
    data-processing operation (data_categories, operation, lawful_basis,
    purpose, etc.), and need a verdict on whether the operation complies with
    the clause.

    Returns one of four verdicts:
      - compliant: operation conforms to the clause requirements
      - violation_candidate: operation contradicts a requirement (with
        evidence and contradicted_requirement)
      - indeterminate: static analysis cannot decide (with verification_scope
        describing the dimension to verify manually)
      - not_applicable: clause does not govern this context

    Successful returns carry policy_schema_version and policy_version
    (provenance). For deprecated clauses, returns business error
    CLAUSE_DEPRECATED (retryable) with successors in details.

    Do not use this for clause retrieval — use `get_clause` instead.
    Do not use this without a clause_id — discover clauses first via
    `find_clauses_by_law_article`.

    [SKELETON STUB — returns indeterminate; real implementation lands in a later commit.]
    """
    return {
        "_stub": "policy-reader skeleton — check_applicability not yet implemented",
        "clause_id_received": clause_id,
        "verdict": "indeterminate",
    }


if __name__ == "__main__":
    mcp.run()