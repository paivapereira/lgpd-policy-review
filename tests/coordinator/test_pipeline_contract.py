"""Phase 2b contract e2e — the MCP-middle handoff under a mocked SDK
(coordinator §3.2-§3.4; run.py `run_pipeline`).

Exercises the Phase 2b wiring through the REAL driver: the Detector `scan_diff`
error-inspection hook (`on_tool_result`) and the Classifier passthrough verifier
(`verify_passthrough` + `upstream`). RED before impl — the hook/verifier are not wired in
run.py and their bodies are no-op stubs, so the scan-error halt and the passthrough-drift
halt do not fire. Patch targets are BARE: `coordinator.driver.query` (Branch B) AND
`coordinator.run.query` (Reporter), the SAME `sdk.sequential` fn at both.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from coordinator import run as run_mod
from coordinator.driver import RETRY_BUDGET
from coordinator.models import CoordinatorError, CoordinatorReport
from coordinator.prompts import build_classifier_prompt
from subagents.classifier.models import ClassifierOutput
from subagents.classifier.passthrough import verify_classifier_passthrough
from subagents.detector.hooks import inspect_scan_diff_result
from subagents.detector.models import DetectorOutput
from subagents.matcher.models import MatcherOutput
from subagents.triager.models import TriagerDecision, TriagerInput

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
                "operation_type": "collection", "declared_legal_basis": None,
                "data_categories": ["email"], "declared_transformations": [],
            },
        }
    ]
}
_MATCHER_OUT = {
    "findings": [
        {
            "file": "a.py", "line": 1, "snippet": "x=email", "rule_id": "BR-EMAIL",
            "data_categories": ["email"], "operation_type": "collection",
            "verdict": "compliant", "evidence": "guarded by consent", "policy_clause_ref": "POL-005",
            "policy_schema_version": "0.1.0", "policy_version": "0.1.0", "legal_framework": "LGPD",
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


def _reporter_payload(run_outcome: str = "success_with_findings") -> dict[str, Any]:
    return {
        "report_id": "550e8400-e29b-41d4-a716-446655440000",
        "report_schema_version": "0.1.0", "policy_schema_version": "0.1.0",
        "policy_version": "0.1.0", "legal_framework": "LGPD",
        "run_outcome": run_outcome, "triager_skip_reason": None,
        "scope": _scope().model_dump(mode="json"),
        "summary": {"counts": {"compliant": 1, "violation_candidate": 0, "indeterminate": 0, "not_applicable": 0}, "total": 1},
        "findings": _MATCHER_OUT["findings"], "scan_provenance": _DETECTOR_OUT["provenance"],
    }


def _proceed_scripts(sdk: Any, *, classifier_out: dict[str, Any] | None = None) -> list[list[Any]]:
    return [
        [sdk.result(subtype="success", structured_output={"decision": "proceed", "relevance_summary": "PII"})],
        [sdk.result(subtype="success", structured_output=_DETECTOR_OUT)],
        [sdk.result(subtype="success", structured_output=classifier_out or _CLASSIFIER_OUT)],
        [sdk.result(subtype="success", structured_output=_MATCHER_OUT)],
        [sdk.assistant_tool_use("mcp__reporter_tools__emit_report", _reporter_payload()), sdk.result()],
    ]


async def test_as1_e2e_json_handoff(tmp_path, monkeypatch, sdk) -> None:
    """Full proceed pipeline with the hook + verifier wired: Detector findings →
    Classifier candidates (5 fields verbatim) → Matcher findings → Reporter payload; all
    five stages invoked; audit scratchpads written. The clean passthrough does NOT trip
    the wired verifier."""
    # ADR-0014 D5 split transport (Triager+Reporter query() / 3 MCP stages mock client),
    # one shared counter; contract assertions below unchanged (rider-3 replumb-only).
    query_fn, client_cls, state = sdk.transport(_proceed_scripts(sdk))
    monkeypatch.setattr("coordinator.driver.query", query_fn)
    monkeypatch.setattr("coordinator.run.query", query_fn)
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", client_cls)

    result = await run_mod.run_pipeline(_scope(), mcp_config_path=_mcp_json(tmp_path), scratchpad_root=tmp_path)

    assert isinstance(result, CoordinatorReport)
    assert state["i"] == 5
    # the candidate the Classifier saw carries the Detector's 5 fields verbatim
    cand = _CLASSIFIER_OUT["classified"][0]
    finding = _DETECTOR_OUT["findings"][0]
    assert {k: cand[k] for k in ("file", "line", "rule_id", "snippet", "surrounding_context")} == finding
    # the Matcher finding preserves operation_type verbatim (rename is projection-only, §2.3)
    assert result.payload["findings"][0]["operation_type"] == "collection"


async def test_as3_e2e_classifier_passthrough_verbatim(tmp_path, monkeypatch, sdk) -> None:
    """The wired verify_classifier_passthrough catches a Classifier that mutated a
    passthrough field (here surrounding_context — the DD-b 5th field) → the run halts as
    CoordinatorError(stage='classifier'). Clean data flows through unchanged."""
    tampered = {
        "classified": [
            {**_CLASSIFIER_OUT["classified"][0], "surrounding_context": "# TAMPERED"},
        ]
    }
    query_fn, client_cls, _ = sdk.transport(_proceed_scripts(sdk, classifier_out=tampered))
    monkeypatch.setattr("coordinator.driver.query", query_fn)
    monkeypatch.setattr("coordinator.run.query", query_fn)
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", client_cls)

    result = await run_mod.run_pipeline(_scope(), mcp_config_path=_mcp_json(tmp_path), scratchpad_root=tmp_path)

    assert isinstance(result, CoordinatorError)
    assert result.stage == "classifier"


async def test_as4_e2e_dual_sink_capture(tmp_path, monkeypatch, sdk) -> None:
    """Dual sink observable by the coordinator: (1) the audit scratchpads 02/03/04 written
    by the driver; (2) the Report payload captured in-memory via ToolUseBlock.input. (The
    99-report.json handler sink runs only under the real SDK — LIVE / Phase-2a unit.)"""
    query_fn, client_cls, _ = sdk.transport(_proceed_scripts(sdk))
    monkeypatch.setattr("coordinator.driver.query", query_fn)
    monkeypatch.setattr("coordinator.run.query", query_fn)
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", client_cls)

    result = await run_mod.run_pipeline(_scope(), mcp_config_path=_mcp_json(tmp_path), scratchpad_root=tmp_path)

    assert isinstance(result, CoordinatorReport)
    assert result.payload  # in-memory capture sink
    written = {p.name for p in next(tmp_path.glob("run-*")).iterdir()}
    assert {"01-triager.json", "02-detector.json", "03-classifier.json", "04-matcher.json"} <= written


async def test_e2e_detector_scan_error_halts(tmp_path, monkeypatch, sdk) -> None:
    """A scan_diff Option-B error in the Detector stream (via the wired hook) escalates as
    DetectorScanFailed → CoordinatorError with the 'cobertura zero' coverage gap. Uses the
    conftest scan_error factory (UserMessage.tool_use_result.structuredContent)."""
    scripts = [
        [sdk.result(subtype="success", structured_output={"decision": "proceed", "relevance_summary": "PII"})],
        [sdk.scan_error("GIT_REF_NOT_FOUND", is_retryable=False), sdk.result(subtype="success", structured_output=_DETECTOR_OUT)],
    ]
    query_fn, client_cls, _ = sdk.transport(scripts)
    monkeypatch.setattr("coordinator.driver.query", query_fn)
    monkeypatch.setattr("coordinator.run.query", query_fn)
    monkeypatch.setattr("coordinator.driver.ClaudeSDKClient", client_cls)

    result = await run_mod.run_pipeline(_scope(), mcp_config_path=_mcp_json(tmp_path), scratchpad_root=tmp_path)

    assert isinstance(result, CoordinatorError)
    assert result.stage == "detector"
    assert result.coverage_gap == "cobertura zero - scan nao rodou"


async def test_stage_wiring_contract(tmp_path, monkeypatch, sdk) -> None:
    """The Phase 2b wiring deltas (coordinator §3.2-§3.4): the Detector stage is invoked
    with on_tool_result=inspect_scan_diff_result; the Classifier with
    verify_passthrough=verify_classifier_passthrough + upstream=detector findings; the
    Matcher with verify_passthrough None (G6 deferred). Post ADR-0014 D1 the 3 MCP stages run
    via `_run_mcp_stage`, so the recorder is installed at BOTH `run_branch_b_stage` (Triager)
    and `_run_mcp_stage` (MCP stages); this also anchors the Phase-3 transport wiring —
    per-stage `target`, and that ONLY the Detector carries a retry budget (DD-A3)."""
    calls: list[dict[str, Any]] = []
    outputs = {
        "triager": TriagerDecision.model_validate({"decision": "proceed", "relevance_summary": "PII"}),
        "detector": DetectorOutput.model_validate(_DETECTOR_OUT),
        "classifier": ClassifierOutput.model_validate(_CLASSIFIER_OUT),
        "matcher": MatcherOutput.model_validate(_MATCHER_OUT),
    }

    async def _recorder(**kwargs: Any) -> Any:
        calls.append(kwargs)
        return outputs[kwargs["stage"]]

    monkeypatch.setattr("coordinator.run.run_branch_b_stage", _recorder)  # Triager
    monkeypatch.setattr("coordinator.run._run_mcp_stage", _recorder)  # Detector/Classifier/Matcher
    monkeypatch.setattr(
        "coordinator.run.query",
        sdk.make_query([sdk.assistant_tool_use("mcp__reporter_tools__emit_report", _reporter_payload()), sdk.result()]),
    )

    await run_mod.run_pipeline(_scope(), mcp_config_path=_mcp_json(tmp_path), scratchpad_root=tmp_path)

    by_stage = {c["stage"]: c for c in calls}
    assert by_stage["detector"].get("on_tool_result") is inspect_scan_diff_result
    assert by_stage["classifier"].get("verify_passthrough") is verify_classifier_passthrough
    # upstream is detector_out.findings (list[DetectorFinding] model objects), not raw dicts
    assert by_stage["classifier"].get("upstream") == outputs["detector"].findings
    assert by_stage["matcher"].get("verify_passthrough") is None  # G6 deferred
    # the scan hook is ONLY on the Detector; passthrough verify is ONLY on the Classifier
    assert by_stage["classifier"].get("on_tool_result") is None
    assert by_stage["matcher"].get("on_tool_result") is None
    assert by_stage["detector"].get("verify_passthrough") is None
    # Phase-3 transport wiring (ADR-0014 D1 + DD-A3): which server each MCP stage waits on,
    # and that ONLY the Detector is given a retry budget.
    assert by_stage["detector"].get("target") == "semgrep-runner"
    assert by_stage["detector"].get("retries") == RETRY_BUDGET
    assert by_stage["classifier"].get("target") == "policy-reader"
    assert by_stage["matcher"].get("target") == "policy-reader"
    assert by_stage["classifier"].get("retries", 0) == 0  # readiness only, no retry
    assert by_stage["matcher"].get("retries", 0) == 0


def test_build_classifier_prompt_carries_candidates() -> None:
    """Reconciliation: candidates arrive in the TURN prompt (build_classifier_prompt), not
    interpolated into the static system prompt. The serialized candidate JSON is present."""
    findings = DetectorOutput.model_validate(_DETECTOR_OUT).findings
    prompt = build_classifier_prompt(findings)
    assert "BR-EMAIL" in prompt and "surrounding_context" in prompt
