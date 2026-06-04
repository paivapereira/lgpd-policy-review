"""Anchor tests for the pure summary renderer (`scripts/ci/format_summary.py`).

Synthetic payloads only — no LLM, no pipeline. Verifies the renderer surfaces
`run_outcome`, counts, the provenance triple, and per-finding clause citation +
location, and that the error path emits NO fabricated verdict (immutable domain
rule 1: no fabricated certainty; rule 2: every finding cites its clause_id).

Contract of record: plano Passo 4 v3 ratificado (não há spec em docs/specs/ — é
adaptador de borda CI, não superfície de contrato do pipeline).
"""
from __future__ import annotations

from typing import Any

from scripts.ci.format_summary import render_error_summary, render_report_summary


def _findings_payload() -> dict[str, Any]:
    """A COMP-001-shaped success payload (1 substantive + 1 not_applicable)."""
    return {
        "report_id": "11111111-1111-4111-8111-111111111111",
        "report_schema_version": "0.1.0",
        "policy_schema_version": "0.1.0",
        "policy_version": "0.2.0",
        "legal_framework": "LGPD",
        "run_outcome": "success_with_findings",
        "triager_skip_reason": None,
        "scope": {"pr_number": 1, "base_ref": "b", "head_ref": "h", "repo_url": "u"},
        "summary": {
            "counts": {
                "compliant": 1,
                "violation_candidate": 0,
                "indeterminate": 0,
                "not_applicable": 1,
            },
            "total": 2,
        },
        "findings": [
            {
                "file": "users.py",
                "line": 26,
                "snippet": "def collect(cpf):",
                "rule_id": "br-cpf",
                "data_categories": ["dados_de_identificacao"],
                "operation_type": "collection",
                "verdict": "compliant",
                "policy_clause_ref": "POL-005",
                "evidence": "base legal consent declarada",
            },
            {
                "file": "users.py",
                "line": 26,
                "snippet": "def collect(cpf):",
                "rule_id": "br-cpf",
                "data_categories": ["dados_de_identificacao"],
                "operation_type": "collection",
                "verdict": "not_applicable",
                "policy_clause_ref": "POL-000",
                "reason": "cláusula definicional, sem controle",
            },
        ],
    }


def test_report_summary_surfaces_outcome_counts_and_provenance() -> None:
    out = render_report_summary(_findings_payload())
    assert "success_with_findings" in out
    # provenance triple
    assert "LGPD" in out
    assert "0.2.0" in out
    # all four verdict count tokens present
    for token in ("compliant", "violation_candidate", "indeterminate", "not_applicable"):
        assert token in out


def test_report_summary_cites_clause_rule_and_location_per_finding() -> None:
    out = render_report_summary(_findings_payload())
    # immutable rule 2: every finding cites its clause_id
    assert "POL-005" in out
    assert "POL-000" in out
    # rule_id (Passo 3 bare form) and location surfaced
    assert "br-cpf" in out
    assert "users.py:26" in out
    # data category surfaced
    assert "dados_de_identificacao" in out


def test_report_summary_skip_path_names_reason() -> None:
    payload = _findings_payload()
    payload["run_outcome"] = "skipped_by_triager"
    payload["triager_skip_reason"] = "PR somente de documentacao"
    payload["findings"] = []
    payload["summary"] = {
        "counts": {
            "compliant": 0,
            "violation_candidate": 0,
            "indeterminate": 0,
            "not_applicable": 0,
        },
        "total": 0,
    }
    out = render_report_summary(payload)
    assert "skipped_by_triager" in out
    assert "PR somente de documentacao" in out


def test_report_summary_no_candidates_path() -> None:
    payload = _findings_payload()
    payload["run_outcome"] = "success_no_candidates"
    payload["findings"] = []
    payload["summary"] = {
        "counts": {
            "compliant": 0,
            "violation_candidate": 0,
            "indeterminate": 0,
            "not_applicable": 0,
        },
        "total": 0,
    }
    out = render_report_summary(payload)
    assert "success_no_candidates" in out


def test_error_summary_emits_no_fabricated_verdict() -> None:
    out = render_error_summary(
        stage="detector",
        coverage_gap="cobertura zero - scan nao rodou",
        cause_type="DetectorScanFailed",
    )
    assert "detector" in out
    assert "DetectorScanFailed" in out
    assert "cobertura zero" in out
    # immutable rule 1: the error path fabricates NO conclusive verdict
    for verdict in ("compliant", "violation_candidate", "indeterminate", "not_applicable"):
        assert verdict not in out
