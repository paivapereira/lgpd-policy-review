"""Anchor — top-level provenance is derived from the findings, not a default param.

Closes the root->symptom arc of the eval-lgpd `MultipleReportEmissions` halt
(diagnosed 5/5 on COMP-001): the coordinator assembled the consolidated state with a
top-level provenance trinca from `run_pipeline`'s default param (`policy_version=0.1.0`)
while every per-finding trinca came from the loaded Policy header (eval-lgpd = `0.2.0`,
echoed by `check_applicability`). The reporter cross-check #2 requires top == per-finding
equality (reporter.md §3.3 / tools.py `_run_cross_checks`), so the inconsistent state was
rejected on the first emit, the Reporter retried per its prompt, and the single-emission
guard aborted on the second.

The spec already mandates the correct source: `reporter.md` source table says the
top-level provenance comes from "header da Política". The coordinator cannot read the
header (it lives behind the policy-reader MCP boundary), but every `Finding` echoes it
verbatim — so the coordinator derives the top-level trinca from the findings.

RED before the fix: `run_pipeline` passes the `0.1.0` default to `_build_consolidated_state`,
so the consolidated state declares `policy_version=0.1.0` while the (mocked) Matcher finding
declares `0.2.0` -> the real `emit_report_impl` returns `PROVENANCE_MISMATCH`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from coordinator import run as run_mod
from coordinator.models import CoordinatorReport
from subagents.reporter.tools import emit_report_impl
from subagents.triager.models import TriagerInput

# Matcher finding whose provenance trinca echoes a Policy header at policy_version 0.2.0
# (the eval-lgpd header), DIFFERENT from run_pipeline's 0.1.0 default — the desync trigger.
_DETECTOR_OUT = {
    "findings": [
        {"file": "a.py", "line": 1, "rule_id": "BR-EMAIL", "snippet": "x=email", "surrounding_context": "# c"}
    ],
    "provenance": {
        "rules_version": "2026.04.1",
        "semgrep_version": "1.163.0",
        "scan_metadata": {"base_ref": "a" * 40, "head_ref": "b" * 40, "files_scanned": 1, "elapsed_seconds": 1.0},
    },
}
_CLASSIFIER_OUT = {
    "classified": [
        {
            "file": "a.py", "line": 1, "rule_id": "BR-EMAIL", "snippet": "x=email", "surrounding_context": "# c",
            "structured_context": {
                "operation_type": "collection", "declared_legal_basis": "consent",
                "data_categories": ["email"], "declared_transformations": [],
            },
        }
    ]
}
_MATCHER_OUT_V2 = {
    "findings": [
        {
            "file": "a.py", "line": 1, "snippet": "x=email", "rule_id": "BR-EMAIL",
            "data_categories": ["email"], "operation_type": "collection",
            "verdict": "compliant", "evidence": "guarded by consent", "policy_clause_ref": "POL-005",
            "policy_schema_version": "0.1.0", "policy_version": "0.2.0", "legal_framework": "LGPD",
        }
    ]
}


def _scope() -> TriagerInput:
    return TriagerInput(pr_number=42, base_ref="main", head_ref="feature/x", repo_url="https://github.com/ex/app")


def _mcp_json(tmp_path: Path) -> Path:
    path = tmp_path / ".mcp.json"
    path.write_text(
        json.dumps({"mcpServers": {"policy-reader": {"command": "uv"}, "semgrep-runner": {"command": "uv"}}}),
        encoding="utf-8",
    )
    return path


def _proceed_scripts(sdk: Any) -> list[list[Any]]:
    return [
        [sdk.result(subtype="success", structured_output={"decision": "proceed", "relevance_summary": "PII"})],
        [sdk.result(subtype="success", structured_output=_DETECTOR_OUT)],
        [sdk.result(subtype="success", structured_output=_CLASSIFIER_OUT)],
        [sdk.result(subtype="success", structured_output=_MATCHER_OUT_V2)],
        [sdk.assistant_tool_use("mcp__reporter_tools__emit_report", {"captured": "ignored"}), sdk.result()],
    ]


async def test_top_level_provenance_derived_from_findings_passes_cross_check(
    tmp_path, monkeypatch, sdk
) -> None:
    """Arc root->symptom, single drive of run_pipeline with a Matcher finding at 0.2.0.

    ROOT: the consolidated state's top-level trinca == the findings' trinca (0.2.0),
    not run_pipeline's 0.1.0 default.
    SYMPTOM: feeding that consolidated state to the REAL `emit_report_impl` does NOT
    return PROVENANCE_MISMATCH (it passes all intra-handler cross-checks).
    """
    # Spy on _build_consolidated_state to capture the exact dict handed to the Reporter.
    captured: dict[str, Any] = {}
    orig = run_mod._build_consolidated_state

    def _spy(**kwargs: Any) -> dict[str, Any]:
        state = orig(**kwargs)
        captured["state"] = state
        return state

    monkeypatch.setattr(run_mod, "_build_consolidated_state", _spy)

    query_fn, client_cls, _ = sdk.transport(_proceed_scripts(sdk))
    monkeypatch.setattr("coordinator.driver.query", query_fn)
    monkeypatch.setattr("coordinator.run.query", query_fn)
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", client_cls)

    result = await run_mod.run_pipeline(_scope(), mcp_config_path=_mcp_json(tmp_path), scratchpad_root=tmp_path)
    assert isinstance(result, CoordinatorReport)

    state = captured["state"]
    # ROOT — top-level trinca derived from the findings (0.2.0), not the 0.1.0 default.
    assert state["policy_version"] == "0.2.0", (
        f"top-level policy_version not derived from findings: {state['policy_version']!r}"
    )
    assert state["policy_schema_version"] == "0.1.0"
    assert state["legal_framework"] == "LGPD"

    # SYMPTOM — the consolidated state survives the REAL emit_report cross-checks.
    envelope = await emit_report_impl(
        state, run_path=tmp_path, expected_report_id=state["report_id"]
    )
    if envelope.get("is_error"):
        detail = json.loads(envelope["content"][0]["text"])
        assert detail.get("errorCode") != "PROVENANCE_MISMATCH", (
            "top-vs-finding provenance desync still trips the cross-check"
        )
        raise AssertionError(f"unexpected emit_report rejection: {detail}")
