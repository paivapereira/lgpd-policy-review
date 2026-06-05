"""Anchors — fail-loud guard refusing a Report under an unsupported legal_framework
(Caminho 1; coordinator `run_pipeline`).

Bug: under a non-LGPD Policy root the pipeline emitted a `CoordinatorReport` with
`legal_framework` silently coerced to "LGPD" (constrained decoding of the Matcher
`output_format`, `Finding.legal_framework: Literal["LGPD"]`, ADR-0007). The guard
reads the real header deterministically at init (`load_policy(resolve_policy_root())`)
and, right BEFORE the Reporter, REFUSES to emit when the framework is unsupported —
so the upstream stages still run (verdict observable on the policy-reader tool
surface) but no mislabeled Report leaves the pipeline.

RED before impl: with no guard, the negative + config-error anchors get a
`CoordinatorReport` (assertion red — the bug reproduced). Patch targets are BARE:
`coordinator.driver.query` + `coordinator.run.query` (same fn) + the streaming
`ClaudeSDKClient` (ADR-0014 D5 split transport), mirroring test_pipeline_contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from coordinator import run as run_mod
from coordinator.errors import CoordinatorStartupError, UnsupportedLegalFramework
from coordinator.models import CoordinatorError, CoordinatorReport
from subagents.triager.models import TriagerInput

_REPO = Path(__file__).resolve().parents[2]
_EVAL_GDPR = _REPO / "policies" / "eval-gdpr"
_EVAL_LGPD = _REPO / "policies" / "eval-lgpd"

_DETECTOR_OUT = {
    "findings": [
        {
            "file": "a.py",
            "line": 1,
            "rule_id": "br-cpf",
            "snippet": "cpf=x",
            "surrounding_context": "# c",
        }
    ],
    "provenance": {
        "rules_version": "2026.04.1",
        "semgrep_version": "1.163.0",
        "scan_metadata": {
            "base_ref": "a" * 40,
            "head_ref": "b" * 40,
            "files_scanned": 1,
            "elapsed_seconds": 1.0,
        },
    },
}
_CLASSIFIER_OUT = {
    "classified": [
        {
            "file": "a.py",
            "line": 1,
            "rule_id": "br-cpf",
            "snippet": "cpf=x",
            "surrounding_context": "# c",
            "structured_context": {
                "operation_type": "collection",
                "declared_legal_basis": "consent",
                "data_categories": ["dados_de_identificacao"],
                "declared_transformations": [],
            },
        }
    ]
}
# Matcher output is grammar-forced to legal_framework "LGPD" even under eval-gdpr —
# that is the very coercion the guard exists to refuse. The stub mirrors that.
_MATCHER_OUT = {
    "findings": [
        {
            "file": "a.py",
            "line": 1,
            "snippet": "cpf=x",
            "rule_id": "br-cpf",
            "data_categories": ["dados_de_identificacao"],
            "operation_type": "collection",
            "verdict": "compliant",
            "evidence": "consent declared",
            "policy_clause_ref": "POL-005",
            "policy_schema_version": "0.1.0",
            "policy_version": "0.2.0",
            "legal_framework": "LGPD",
        }
    ]
}


def _scope() -> TriagerInput:
    return TriagerInput(
        pr_number=42,
        base_ref="main",
        head_ref="feature/x",
        repo_url="https://github.com/ex/app",
    )


def _mcp_json(tmp_path: Path) -> Path:
    path = tmp_path / ".mcp.json"
    path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "policy-reader": {"command": "uv"},
                    "semgrep-runner": {"command": "uv"},
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def _reporter_payload() -> dict[str, Any]:
    return {
        "report_id": "550e8400-e29b-41d4-a716-446655440000",
        "report_schema_version": "0.1.0",
        "policy_schema_version": "0.1.0",
        "policy_version": "0.2.0",
        "legal_framework": "LGPD",
        "run_outcome": "success_with_findings",
        "triager_skip_reason": None,
        "scope": _scope().model_dump(mode="json"),
        "summary": {
            "counts": {
                "compliant": 1,
                "violation_candidate": 0,
                "indeterminate": 0,
                "not_applicable": 0,
            },
            "total": 1,
        },
        "findings": _MATCHER_OUT["findings"],
        "scan_provenance": _DETECTOR_OUT["provenance"],
    }


def _proceed_scripts(sdk: Any) -> list[list[Any]]:
    return [
        [
            sdk.result(
                subtype="success",
                structured_output={"decision": "proceed", "relevance_summary": "PII"},
            )
        ],
        [sdk.result(subtype="success", structured_output=_DETECTOR_OUT)],
        [sdk.result(subtype="success", structured_output=_CLASSIFIER_OUT)],
        [sdk.result(subtype="success", structured_output=_MATCHER_OUT)],
        [
            sdk.assistant_tool_use(
                "mcp__reporter_tools__emit_report", _reporter_payload()
            ),
            sdk.result(),
        ],
    ]


def _install(monkeypatch, sdk) -> dict[str, Any]:
    query_fn, client_cls, state = sdk.transport(_proceed_scripts(sdk))
    monkeypatch.setattr("coordinator.driver.query", query_fn)
    monkeypatch.setattr("coordinator.run.query", query_fn)
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", client_cls)
    return state


async def test_unsupported_framework_refuses_before_reporter(
    tmp_path, monkeypatch, sdk
) -> None:
    """Under eval-gdpr (header GDPR) the four stages run but the guard refuses BEFORE
    the Reporter: CoordinatorError(UnsupportedLegalFramework, stage='framework_guard'),
    the Reporter stage is never pulled, and the coverage_gap is honest."""
    monkeypatch.setenv("POLICY_READER_ROOT", str(_EVAL_GDPR))
    state = _install(monkeypatch, sdk)

    result = await run_mod.run_pipeline(
        _scope(), mcp_config_path=_mcp_json(tmp_path), scratchpad_root=tmp_path
    )

    assert isinstance(result, CoordinatorError)
    assert isinstance(result.cause, UnsupportedLegalFramework)
    assert result.cause.legal_framework == "GDPR"
    assert result.stage == "framework_guard"
    assert (
        state["i"] == 4
    )  # Triager+Detector+Classifier+Matcher ran; Reporter NOT invoked
    assert "GDPR" in result.coverage_gap and "ADR-0007" in result.coverage_gap


async def test_supported_framework_emits_report(tmp_path, monkeypatch, sdk) -> None:
    """Under eval-lgpd (header LGPD) the guard passes and the Reporter runs — Report
    emitted, all five stages invoked. Regression: LGPD behaviour unchanged."""
    monkeypatch.setenv("POLICY_READER_ROOT", str(_EVAL_LGPD))
    state = _install(monkeypatch, sdk)

    result = await run_mod.run_pipeline(
        _scope(), mcp_config_path=_mcp_json(tmp_path), scratchpad_root=tmp_path
    )

    assert isinstance(result, CoordinatorReport)
    assert state["i"] == 5


async def test_unreadable_policy_root_fails_startup(tmp_path, monkeypatch, sdk) -> None:
    """A header read that fails at init (root absent) is a deliberate typed
    CoordinatorError(CoordinatorStartupError, stage='startup') — fail-fast, no raw
    exception path, no stage run."""
    monkeypatch.setenv("POLICY_READER_ROOT", str(tmp_path / "does-not-exist"))
    state = _install(monkeypatch, sdk)

    result = await run_mod.run_pipeline(
        _scope(), mcp_config_path=_mcp_json(tmp_path), scratchpad_root=tmp_path
    )

    assert isinstance(result, CoordinatorError)
    assert isinstance(result.cause, CoordinatorStartupError)
    assert result.stage == "startup"
    assert state["i"] == 0  # failed before any stage
