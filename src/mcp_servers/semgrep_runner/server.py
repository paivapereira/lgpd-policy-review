"""semgrep-runner MCP server.

Exposes diff-aware Semgrep execution over a Git ref range as a single
tool (`scan_diff`) consumed by the Detector subagent. See
`docs/specs/semgrep-runner/canonical.md` for the contract.

T05 wired the rule set loader to the bootstrap path and registered
`scan_diff` as a stub returning the `NOT_IMPLEMENTED` envelope. T06
replaces the stub with the real implementation in `tools.scan_diff`
(canonical §4.2-4.3, §5); the @mcp.tool wrapper here is a thin
delegator that injects `_STATE`.

Per canonical §8.6 and ADR-0010, the Semgrep binary availability is
NOT verified at startup. The per-call check lives at the `scan_diff`
entry point (DD-T06-2), surfacing as `SEMGREP_BINARY_UNAVAILABLE`
when the binary is missing — never as a server crash.
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.tools.base import ToolResult

from .loader import load_rules, resolve_runner_root
from .models import LoadedRules
from .tools import scan_diff as _scan_diff_impl

mcp = FastMCP("semgrep-runner")

# Module-level state populated by `_bootstrap`. The `scan_diff` handler
# asserts it is not None when invoked — once the T06 implementation
# consumes `rules_version` from this state, the assert guards against
# bootstrap order regressions.
_STATE: LoadedRules | None = None


def _bootstrap(rules_root: Path | None = None) -> None:
    """Load the curated rule set and populate `_STATE`. On `RulesLoadError`,
    write the message to stderr and exit non-zero — `mcp.run()` is never
    reached.

    Mirrors `policy_reader.server._bootstrap`: catches only the domain
    exception (`RulesLoadError`). A `ValidationError` from `LoadedRules`
    construction would propagate uncaught, surfacing as a Python traceback
    — semantically correct, since that path is only reachable if the
    primary empty-rule-set check in `loader.load_rules` regresses (see
    DD-T05-12 / `models.LoadedRules`).
    """
    global _STATE
    from .errors import RulesLoadError

    try:
        _STATE = load_rules(resolve_runner_root(rules_root))
    except RulesLoadError as exc:
        print(f"[semgrep-runner] startup failed: {exc}", file=sys.stderr)
        sys.exit(1)


def _reset_state_for_tests() -> None:
    """Teardown hook used by tests that exercise `_bootstrap` to avoid
    cross-test pollution of `_STATE`. Production code never calls this.
    """
    global _STATE
    _STATE = None


# =============================================================================
# Tools
# =============================================================================

@mcp.tool
# -> ToolResult é load-bearing para a Option B; ver GUARD em _envelope_tool_result
def scan_diff(base_ref: str, head_ref: str) -> ToolResult:
    """Scans the Git diff between base_ref and head_ref using the project's curated Semgrep rule set, returning findings that match any rule in the set. Use this when the caller has the BASE and HEAD refs of a pull request and needs to identify candidate sites for downstream classification. The rule set is server-side curated and not callable-parameterizable; it is fixed at server build time. The MVP rule set covers Brazilian personal data identifiers (CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde), but the component itself is domain-agnostic — rule set substitution is the supported path for different jurisdictions or detection domains.

    Findings are single-file: the MVP does not perform cross-file taint analysis. Each finding carries rule provenance (rule_id), location (file path, line range), and code snippet. Empty findings list is a valid success outcome — the diff was scanned and no rules matched.

    Returns success with findings list (possibly empty) on completion. Returns business error if Git refs are unresolvable, system error if the scan times out or the Semgrep binary fails. Operation is synchronous and may take seconds to minutes depending on diff size.
    """
    assert _STATE is not None, "semgrep-runner bootstrap did not run"
    return _scan_diff_impl(base_ref, head_ref, _STATE)


if __name__ == "__main__":
    _bootstrap()
    mcp.run()
