"""policy-reader MCP server.

Exposes the versioned Data Protection Policy under the jurisdictional
framework declared in its header (`legal_framework`) as queryable resource
and as compliance-evaluation tool. See `docs/specs/policy-reader/canonical.md`
for the contract.

T01 wires the Policy loader to the bootstrap path and replaces the
`policy://schema-version` resource handler with one that returns the real
handshake payload (`policy_schema_version`, `policy_version`,
`legal_framework`, `compatible_schema_range`). The remaining resource
(`policy://catalog`) and the three tools (`get_clause`,
`find_clauses_by_law_article`, `check_applicability`) remain as skeleton
stubs until T02a/T02b/T03/T04 land.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

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
def get_clause(clause_id: str) -> dict[str, Any]:
    """Retrieve a single clause by its identifier.

    Use this when you have a clause_id (e.g. POL-000) and need the full clause
    structure: statutory_reference, requirements, exceptions, status, and
    tombstone if deprecated. For deprecated clauses, the returned object
    includes a tombstone field with successors, effective_until, and
    deprecation_reason — retrieval is legitimate (historical audit).

    Do not use this for searching by law article — use
    `find_clauses_by_law_article` instead. Do not use this for compliance
    evaluation — use `check_applicability` instead.

    [SKELETON STUB — echoes input; real implementation lands in T02a.]
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

    [SKELETON STUB — returns empty list; real implementation lands in T02b.]
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
    data-processing operation (data_categories, operation, legal_basis,
    purpose, etc.), and need a verdict on whether the operation complies with
    the clause.

    Returns one of four verdicts:
      - compliant: operation conforms to the clause requirements
      - violation_candidate: operation contradicts a requirement (with
        evidence and contradicted_requirement)
      - indeterminate: static analysis cannot decide (with verification_scope
        describing the dimension to verify manually)
      - not_applicable: clause does not govern this context

    Successful returns carry policy_schema_version, policy_version, and
    legal_framework (provenance). For deprecated clauses, returns business
    error CLAUSE_DEPRECATED (retryable) with successors in details.

    Do not use this for clause retrieval — use `get_clause` instead.
    Do not use this without a clause_id — discover clauses first via
    `find_clauses_by_law_article`.

    [SKELETON STUB — returns indeterminate; real implementation lands in T03.]
    """
    _ = json.dumps(structured_context, default=str)  # touch arg, lint quiet
    return {
        "_stub": "policy-reader skeleton — check_applicability not yet implemented",
        "clause_id_received": clause_id,
        "verdict": "indeterminate",
    }


if __name__ == "__main__":
    _bootstrap()
    mcp.run()
