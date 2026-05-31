"""Phase 1 anchors/acceptance — walking skeleton e2e under a mocked SDK.

Proves the composition (axis C): the five stages wire in sequence, state flows
stage->stage, the driver writes the scratchpad, and the Reporter payload is
captured via ToolUseBlock.input -> CoordinatorReport. The 99-report.json write
(handler dual-sink #1) is NOT exercised here (the handler only runs under the
real SDK); it is unit-tested in Phase 2a and confirmed live at G1.
"""
from __future__ import annotations

import json
from pathlib import Path

from coordinator.models import CoordinatorReport
from coordinator.run import run_pipeline
from subagents.triager.models import TriagerInput

_DETECTOR_OUT = {
    "findings": [
        {"file": "a.py", "line": 1, "rule_id": "BR-EMAIL", "snippet": "x=email", "surrounding_context": "# c"}
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
            "rule_id": "BR-EMAIL",
            "snippet": "x=email",
            "surrounding_context": "# c",
            "structured_context": {
                "operation_type": "collection",
                "declared_legal_basis": None,
                "data_categories": ["email"],
                "declared_transformations": [],
            },
        }
    ]
}
_MATCHER_OUT = {
    "findings": [
        {
            "file": "a.py",
            "line": 1,
            "snippet": "x=email",
            "rule_id": "BR-EMAIL",
            "data_categories": ["email"],
            "operation_type": "collection",
            "verdict": "compliant",
            "evidence": "guarded by consent",
            "policy_clause_ref": "POL-005",
            "policy_schema_version": "0.1.0",
            "policy_version": "0.1.0",
            "legal_framework": "LGPD",
        }
    ]
}


def _scope() -> TriagerInput:
    return TriagerInput(
        pr_number=42, base_ref="main", head_ref="feature/x", repo_url="https://github.com/ex/app"
    )


def _mcp_json(tmp_path: Path) -> Path:
    path = tmp_path / ".mcp.json"
    path.write_text(
        json.dumps(
            {"mcpServers": {"policy-reader": {"command": "uv"}, "semgrep-runner": {"command": "uv"}}}
        ),
        encoding="utf-8",
    )
    return path


async def test_skeleton_skip_path_jumps_to_reporter(tmp_path, monkeypatch, sdk) -> None:
    reporter_payload = {
        "report_id": "550e8400-e29b-41d4-a716-446655440000",
        "report_schema_version": "0.1.0",
        "policy_schema_version": "0.1.0",
        "policy_version": "0.1.0",
        "legal_framework": "LGPD",
        "run_outcome": "skipped_by_triager",
        "triager_skip_reason": "docs-only",
        "scope": _scope().model_dump(mode="json"),
        "summary": {
            "counts": {"compliant": 0, "violation_candidate": 0, "indeterminate": 0, "not_applicable": 0},
            "total": 0,
        },
        "findings": [],
    }
    scripts = [
        [sdk.result(subtype="success", structured_output={"decision": "skip", "skip_reason": "docs-only"})],
        [sdk.assistant_tool_use("mcp__reporter_tools__emit_report", reporter_payload), sdk.result()],
    ]
    fake, state = sdk.sequential(scripts)
    monkeypatch.setattr("coordinator.driver.query", fake)
    monkeypatch.setattr("coordinator.run.query", fake)

    result = await run_pipeline(_scope(), mcp_config_path=_mcp_json(tmp_path), scratchpad_root=tmp_path)

    assert isinstance(result, CoordinatorReport)
    assert result.payload == reporter_payload
    # Only Triager + Reporter were invoked (Detector/Classifier/Matcher skipped).
    assert state["i"] == 2
    run_dirs = list(tmp_path.glob("run-*"))
    assert len(run_dirs) == 1
    written = {p.name for p in run_dirs[0].iterdir()}
    assert "01-triager.json" in written
    assert "02-detector.json" not in written
    assert "03-classifier.json" not in written
    assert "04-matcher.json" not in written


async def test_skeleton_proceed_path_returns_report(tmp_path, monkeypatch, sdk) -> None:
    reporter_payload = {
        "report_id": "550e8400-e29b-41d4-a716-446655440000",
        "report_schema_version": "0.1.0",
        "policy_schema_version": "0.1.0",
        "policy_version": "0.1.0",
        "legal_framework": "LGPD",
        "run_outcome": "success_with_findings",
        "triager_skip_reason": None,
        "scope": _scope().model_dump(mode="json"),
        "summary": {
            "counts": {"compliant": 1, "violation_candidate": 0, "indeterminate": 0, "not_applicable": 0},
            "total": 1,
        },
        "findings": _MATCHER_OUT["findings"],
        "scan_provenance": _DETECTOR_OUT["provenance"],
    }
    scripts = [
        [sdk.result(subtype="success", structured_output={"decision": "proceed", "relevance_summary": "PII collection"})],
        [sdk.result(subtype="success", structured_output=_DETECTOR_OUT)],
        [sdk.result(subtype="success", structured_output=_CLASSIFIER_OUT)],
        [sdk.result(subtype="success", structured_output=_MATCHER_OUT)],
        [sdk.assistant_tool_use("mcp__reporter_tools__emit_report", reporter_payload), sdk.result()],
    ]
    fake, state = sdk.sequential(scripts)
    monkeypatch.setattr("coordinator.driver.query", fake)
    monkeypatch.setattr("coordinator.run.query", fake)

    result = await run_pipeline(_scope(), mcp_config_path=_mcp_json(tmp_path), scratchpad_root=tmp_path)

    assert isinstance(result, CoordinatorReport)
    assert result.payload == reporter_payload
    assert state["i"] == 5  # all five stages invoked
    written = {p.name for p in next(tmp_path.glob("run-*")).iterdir()}
    assert {"01-triager.json", "02-detector.json", "03-classifier.json", "04-matcher.json"} <= written


async def test_skeleton_reporter_not_emitted_raises(tmp_path, monkeypatch, sdk) -> None:
    # Reporter ends without calling emit_report -> CoordinatorError(ReportNotEmitted).
    from coordinator.errors import ReportNotEmitted
    from coordinator.models import CoordinatorError

    scripts = [
        [sdk.result(subtype="success", structured_output={"decision": "skip", "skip_reason": "x"})],
        [sdk.result(subtype="success")],  # no emit_report ToolUseBlock
    ]
    fake, _ = sdk.sequential(scripts)
    monkeypatch.setattr("coordinator.driver.query", fake)
    monkeypatch.setattr("coordinator.run.query", fake)

    result = await run_pipeline(_scope(), mcp_config_path=_mcp_json(tmp_path), scratchpad_root=tmp_path)
    assert isinstance(result, CoordinatorError)
    assert isinstance(result.cause, ReportNotEmitted)
    assert result.stage == "reporter"
