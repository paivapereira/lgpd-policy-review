"""Phase 1 — coordinator-side deterministic derivations (reporter §3.5 + §2.2).

These are the computations the coordinator performs so the Reporter stays pure
passthrough: run_outcome, summary aggregation, and the consolidated-state shape.
"""
from __future__ import annotations

from typing import Any

from coordinator.run import aggregate_summary, _build_consolidated_state, derive_run_outcome
from subagents.detector.models import ScanMetadata, ScanProvenance
from subagents.matcher.models import Finding
from subagents.reporter.models import SummaryModel
from subagents.triager.models import TriagerInput


def _finding(verdict: str, **extra: Any) -> Finding:
    base: dict[str, Any] = dict(
        file="a.py",
        line=1,
        snippet="x",
        rule_id="R",
        data_categories=["email"],
        operation_type="collection",
        verdict=verdict,
        policy_clause_ref="POL-005",
        policy_schema_version="0.1.0",
        policy_version="0.1.0",
        legal_framework="LGPD",
    )
    base.update(extra)
    return Finding(**base)


# --- derive_run_outcome (the 4 tokens) ---
def test_derive_run_outcome_skip() -> None:
    assert derive_run_outcome("docs-only", 0, []) == "skipped_by_triager"


def test_derive_run_outcome_no_candidates() -> None:
    assert derive_run_outcome(None, 0, []) == "success_no_candidates"


def test_derive_run_outcome_all_not_applicable() -> None:
    findings = [_finding("not_applicable", reason="POL-000 definitional")]
    assert derive_run_outcome(None, 1, findings) == "success_all_not_applicable"


def test_derive_run_outcome_with_findings() -> None:
    findings = [
        _finding("not_applicable", reason="x"),
        _finding("compliant", evidence="ok"),
    ]
    assert derive_run_outcome(None, 2, findings) == "success_with_findings"


# --- aggregate_summary ---
def test_aggregate_summary_counts_and_total() -> None:
    findings = [
        _finding("compliant", evidence="ok"),
        _finding("violation_candidate", evidence="bad"),
        _finding("not_applicable", reason="x"),
        _finding("not_applicable", reason="y"),
    ]
    summary = aggregate_summary(findings)
    assert isinstance(summary, SummaryModel)
    assert summary.counts.compliant == 1
    assert summary.counts.violation_candidate == 1
    assert summary.counts.not_applicable == 2
    assert summary.counts.indeterminate == 0
    assert summary.total == 4 == sum(
        [
            summary.counts.compliant,
            summary.counts.violation_candidate,
            summary.counts.indeterminate,
            summary.counts.not_applicable,
        ]
    )


# --- consolidated state shape (reporter §2.2/§2.3, §3.5 scan_provenance presence) ---
def _scope() -> TriagerInput:
    return TriagerInput(pr_number=1, base_ref="main", head_ref="f", repo_url="https://x/y")


def _prov() -> ScanProvenance:
    return ScanProvenance(
        rules_version="2026.04.1",
        semgrep_version="1.163.0",
        scan_metadata=ScanMetadata(
            base_ref="a" * 40, head_ref="b" * 40, files_scanned=1, elapsed_seconds=1.0
        ),
    )


def test_consolidated_state_proceed_has_scan_provenance() -> None:
    state = _build_consolidated_state(
        run_outcome="success_with_findings",
        triager_skip_reason=None,
        report_id="rid",
        policy_schema_version="0.1.0",
        policy_version="0.1.0",
        legal_framework="LGPD",
        scope=_scope(),
        summary=aggregate_summary([_finding("compliant", evidence="ok")]),
        findings=[_finding("compliant", evidence="ok")],
        scan_provenance=_prov(),
    )
    expected_keys = {
        "run_outcome",
        "triager_skip_reason",
        "report_id",
        "report_schema_version",
        "policy_schema_version",
        "policy_version",
        "legal_framework",
        "scope",
        "summary",
        "findings",
        "scan_provenance",
    }
    assert expected_keys <= set(state)
    assert state["scan_provenance"]["semgrep_version"] == "1.163.0"
    assert state["scope"]["pr_number"] == 1


def test_consolidated_state_skip_omits_scan_provenance() -> None:
    state = _build_consolidated_state(
        run_outcome="skipped_by_triager",
        triager_skip_reason="docs-only",
        report_id="rid",
        policy_schema_version="0.1.0",
        policy_version="0.1.0",
        legal_framework="LGPD",
        scope=_scope(),
        summary=aggregate_summary([]),
        findings=[],
        scan_provenance=None,
    )
    assert "scan_provenance" not in state  # absent in skip path (§3.5)
    assert state["findings"] == []
    assert state["triager_skip_reason"] == "docs-only"
