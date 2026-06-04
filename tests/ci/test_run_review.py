"""Anchor tests for the CI edge adapter (`scripts/ci/run_review.py`).

`run_pipeline` is monkeypatched (no SDK, no MCP, no LLM). Verifies the
source-agnostic env -> TriagerInput -> run_pipeline -> stdout-summary flow and the
exit-code contract: 0 = CoordinatorReport (findings non-blocking, RNF-002), 1 =
CoordinatorError (terminal halt), 2 = bad invocation (missing/invalid env).
Summary goes to STDOUT only (E1 — the YAML redirects to $GITHUB_STEP_SUMMARY).
"""
from __future__ import annotations

from typing import Any

import pytest

from coordinator.models import CoordinatorError, CoordinatorReport
from scripts.ci import run_review


def _payload() -> dict[str, Any]:
    return {
        "report_id": "11111111-1111-4111-8111-111111111111",
        "report_schema_version": "0.1.0",
        "policy_schema_version": "0.1.0",
        "policy_version": "0.2.0",
        "legal_framework": "LGPD",
        "run_outcome": "success_with_findings",
        "triager_skip_reason": None,
        "scope": {"pr_number": 7, "base_ref": "b", "head_ref": "h", "repo_url": "u"},
        "summary": {
            "counts": {
                "compliant": 0,
                "violation_candidate": 1,
                "indeterminate": 0,
                "not_applicable": 3,
            },
            "total": 4,
        },
        "findings": [
            {
                "file": "models.py",
                "line": 30,
                "snippet": "cpf = ...",
                "rule_id": "br-cpf",
                "data_categories": ["dados_de_identificacao"],
                "operation_type": "collection",
                "verdict": "violation_candidate",
                "policy_clause_ref": "POL-005",
                "evidence": "sem base legal declarada",
                "contradicted_requirement": "R1",
            },
        ],
    }


def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASE_REF", "0000000000000000000000000000000000000000")
    monkeypatch.setenv("HEAD_REF", "1111111111111111111111111111111111111111")
    monkeypatch.setenv("PR_NUMBER", "7")
    monkeypatch.setenv("REPO_URL", "https://example.invalid/app")


def test_report_path_exit_zero_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    captured: dict[str, Any] = {}

    async def fake_pipeline(scope: Any, **kwargs: Any) -> CoordinatorReport:
        captured["scope"] = scope
        return CoordinatorReport(payload=_payload())

    monkeypatch.setattr(run_review, "run_pipeline", fake_pipeline)
    _set_env(monkeypatch)

    code = run_review.main()

    assert code == 0
    out = capsys.readouterr().out
    assert "success_with_findings" in out
    assert "POL-005" in out
    # scope was built from the generic env vars
    assert captured["scope"].pr_number == 7
    assert captured["scope"].base_ref.startswith("0000")


def test_error_path_exit_one_and_prints_error_summary(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    async def fake_pipeline(scope: Any, **kwargs: Any) -> CoordinatorError:
        return CoordinatorError(
            cause=RuntimeError("scan failed"),
            stage="detector",
            coverage_gap="cobertura zero - scan nao rodou",
        )

    monkeypatch.setattr(run_review, "run_pipeline", fake_pipeline)
    _set_env(monkeypatch)

    code = run_review.main()

    assert code == 1
    out = capsys.readouterr().out
    assert "detector" in out
    # no fabricated verdict on the terminal-error path
    assert "violation_candidate" not in out


def test_missing_env_exit_two(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("BASE_REF", "HEAD_REF", "PR_NUMBER", "REPO_URL"):
        monkeypatch.delenv(var, raising=False)
    assert run_review.main() == 2


def test_non_integer_pr_number_exit_two(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)
    monkeypatch.setenv("PR_NUMBER", "not-an-int")
    assert run_review.main() == 2
