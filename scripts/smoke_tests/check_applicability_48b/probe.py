r"""Smoke-test #48-b — probes C2 and H1 against the real policy-reader impl.

C2 — what does `check_applicability` return for the two VALID Classifier
outputs that the matcher.md §6.2/§6.6 currently calls "upstream contract
violation"? (`data_categories: []` and `operation: null`/absent).

H1 — does the jurisdictional axis of the handshake have an owner server-side?
Boot the loader against the synthetic GDPR fixture (legal_framework != LGPD)
and observe whether load_policy aborts (gatekeeping) or serves it (agnostic).

Pure in-process calls — no MCP wire, no SDK, no auth. The MCP layer adds
nothing for these cases: `check_applicability` takes `structured_context` as
`dict[str, Any]` (no inputSchema constraint on its contents), so the pure
function call reproduces the domain behaviour the wire would surface.

Run:
    uv run python scripts\smoke_tests\check_applicability_48b\probe.py
"""
from __future__ import annotations

import json
from pathlib import Path

from mcp_servers.policy_reader import tools
from mcp_servers.policy_reader.errors import PolicyLoadError
from mcp_servers.policy_reader.loader import load_policy

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_POLICY = REPO_ROOT / "policy"
SYNTHETIC_GDPR = (
    REPO_ROOT / "tests" / "mcp_servers" / "policy_reader"
    / "fixtures" / "synthetic_gdpr"
)


def _sc(result) -> dict:
    """Extract the structured_content dict from a ToolResult."""
    return dict(result.structured_content)


def _line() -> None:
    print("-" * 72)


def probe_c2() -> None:
    print("\n=== C2 — check_applicability on valid Classifier edge outputs ===")
    state = load_policy(REAL_POLICY)

    # A valid data-category token, so C2b/C2c reach the operation check
    # rather than short-circuiting on INVALID_DATA_CATEGORY.
    from mcp_servers.policy_reader._envelope import (
        _load_data_categories_vocabulary,
        _load_operation_vocabulary,
    )

    cats = sorted(_load_data_categories_vocabulary(state))
    ops = sorted(_load_operation_vocabulary(state))
    valid_cat = cats[0]
    print(f"POL-000 data_categories vocab (first): {valid_cat!r}")
    print(f"operation vocab: {ops}")
    _line()

    cases = [
        ("C2a  data_categories=[]      operation='collection'",
         {"data_categories": [], "operation": "collection"}),
        ("C2b  data_categories=[ok]    operation=None",
         {"data_categories": [valid_cat], "operation": None}),
        ("C2c  data_categories=[ok]    operation ABSENT",
         {"data_categories": [valid_cat]}),
    ]
    for label, ctx in cases:
        result = tools.check_applicability("POL-000", ctx, state)
        sc = _sc(result)
        is_error = getattr(result, "is_error", None)
        err = sc.get("errorCode", "<no errorCode — success payload>")
        print(f"{label}")
        print(f"    -> errorCode      : {err}")
        print(f"    -> isRetryable    : {sc.get('isRetryable')}")
        print(f"    -> wire is_error  : {is_error}")
        print(f"    -> structuredContent keys: {sorted(sc)}")
        _line()


def probe_h1() -> None:
    print("\n=== H1.3 — boot probe: legal_framework=GDPR (!= LGPD) ===")
    try:
        state = load_policy(SYNTHETIC_GDPR)
    except PolicyLoadError as exc:
        print(f"    -> ABORTED at load: {exc}")
        print("    -> VERDICT: (c) EXISTS — server gatekeeps by framework.")
        return
    fw = state.header.legal_framework
    print(f"    -> load_policy SUCCEEDED. header.legal_framework = {fw!r}")
    print(f"    -> clauses loaded     : {sorted(state.clauses)}")
    print(f"    -> vocab keys         : {sorted(state.vocabularies)}")
    print("    -> VERDICT: NO jurisdictional gate server-side (agnostic).")
    print("       (c) does NOT exist; load serves whatever <framework>/ dir")
    print("       is present. Combined with grep (no comparison anywhere in")
    print("       src/) and absence of src/coordinator/, (d) does NOT exist.")


if __name__ == "__main__":
    probe_c2()
    probe_h1()
    print("\nDONE.")
