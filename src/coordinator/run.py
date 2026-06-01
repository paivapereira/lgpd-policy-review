"""Coordinator main loop (coordinator.md §3).

Orchestrates the five subagents as sequential `query()` calls (pattern A''),
threading state stage->stage as JSON inline in the next prompt (§4), writing the
audit scratchpad, and capturing the Report via the Reporter's `ToolUseBlock.input`
(§3.5). Returns the external `CoordinatorResult` union (§3.6).

Phase 1 (walking skeleton): real driver + config + factory + options + the §3.5
Reporter loop + run_outcome/summary derivation are wired; only the prompt TEXT
(system prompts, build_*_prompt) is stubbed, and the Detector tool hook /
Classifier passthrough verify are wired as None (added in Phase 2b).
"""
from __future__ import annotations

import logging
import sys
import uuid
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    McpSdkServerConfig,
    ResultMessage,
    ToolUseBlock,
    query,
)

from coordinator.config import McpServersConfig, load_mcp_config
from coordinator.driver import run_branch_b_stage
from coordinator.errors import (
    CoordinatorStreamFailure,
    DetectorScanFailed,
    MalformedToolUseBlock,
    MultipleReportEmissions,
    ReporterPermissionDenied,
    ReporterTurnsExhausted,
    ReportNotEmitted,
)
from coordinator.models import CoordinatorError, CoordinatorReport, CoordinatorResult
from coordinator.prompts import (
    build_classifier_prompt,
    build_detector_prompt,
    build_matcher_prompt,
    build_reporter_prompt,
    build_triager_prompt,
)
from subagents.classifier.models import ClassifierOutput
from subagents.classifier.passthrough import verify_classifier_passthrough
from subagents.classifier.system_prompts import CLASSIFIER_SYSTEM_PROMPT
from subagents.detector.hooks import inspect_scan_diff_result
from subagents.detector.models import DetectorOutput, ScanProvenance
from subagents.detector.system_prompts import DETECTOR_SYSTEM_PROMPT
from subagents.matcher.models import Finding, MatcherOutput
from subagents.matcher.system_prompts import MATCHER_SYSTEM_PROMPT
from subagents.reporter.constants import REPORT_SCHEMA_VERSION
from subagents.reporter.models import RunOutcome, SummaryCounts, SummaryModel
from subagents.reporter.system_prompts import REPORTER_SYSTEM_PROMPT
from subagents.reporter.tools import create_reporter_server
from subagents.triager.models import TriagerDecision, TriagerInput

log = logging.getLogger("coordinator")

_EMIT_REPORT_TOOL = "mcp__reporter_tools__emit_report"
_LOCKDOWN: dict[str, Any] = {
    "permission_mode": "dontAsk",
    "setting_sources": [],
    "strict_mcp_config": True,
}


def configure_logging() -> None:
    """stderr-only structured logging; stdout is reserved for the Report payload
    consumed by the CI caller in headless mode (§3.0)."""
    if not log.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        log.addHandler(handler)
        log.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Deterministic derivations performed by the coordinator (Reporter is passthrough)
# ---------------------------------------------------------------------------
def derive_run_outcome(
    triager_skip_reason: str | None,
    candidates_count: int,
    matcher_findings: list[Finding],
) -> RunOutcome:
    """reporter.md §3.5 verbatim."""
    if triager_skip_reason is not None:
        return "skipped_by_triager"
    if candidates_count == 0:
        return "success_no_candidates"
    substantive = {"compliant", "violation_candidate", "indeterminate"}
    if not any(f.verdict in substantive for f in matcher_findings):
        return "success_all_not_applicable"
    return "success_with_findings"


def aggregate_summary(findings: list[Finding]) -> SummaryModel:
    """Tally findings by verdict; total == len(findings) == sum(counts)."""
    counts = SummaryCounts(
        compliant=sum(1 for f in findings if f.verdict == "compliant"),
        violation_candidate=sum(1 for f in findings if f.verdict == "violation_candidate"),
        indeterminate=sum(1 for f in findings if f.verdict == "indeterminate"),
        not_applicable=sum(1 for f in findings if f.verdict == "not_applicable"),
    )
    return SummaryModel(counts=counts, total=len(findings))


def _build_consolidated_state(
    *,
    run_outcome: RunOutcome,
    triager_skip_reason: str | None,
    report_id: str,
    policy_schema_version: str,
    policy_version: str,
    legal_framework: str,
    scope: TriagerInput,
    summary: SummaryModel,
    findings: list[Finding],
    scan_provenance: ScanProvenance | None,
) -> dict[str, Any]:
    """The Reporter input dict (reporter §2.2/§2.3) — pure JSON, pre-computed."""
    state: dict[str, Any] = {
        "run_outcome": run_outcome,
        "triager_skip_reason": triager_skip_reason,
        "report_id": report_id,
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "policy_schema_version": policy_schema_version,
        "policy_version": policy_version,
        "legal_framework": legal_framework,
        "scope": scope.model_dump(mode="json"),
        "summary": summary.model_dump(mode="json"),
        "findings": [f.model_dump(mode="json") for f in findings],
    }
    if scan_provenance is not None:
        state["scan_provenance"] = scan_provenance.model_dump(mode="json")
    return state


# ---------------------------------------------------------------------------
# Per-stage ClaudeAgentOptions (quintupla canonica + tools axis), coordinator §3.1-§3.5
# ---------------------------------------------------------------------------
def _triager_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        # DD-4: the canonical §5.1 prompt (with the PR context + tool instructions)
        # is rendered by build_triager_prompt and delivered as the turn prompt
        # (triager §2.2); the stage runs in SDK minimal system-prompt mode (§5.1 note).
        system_prompt=None,
        tools=["Read", "Glob"],
        allowed_tools=["Read", "Glob"],
        mcp_servers={},
        output_format={"type": "json_schema", "schema": TriagerDecision.model_json_schema()},
        max_turns=20,
        **_LOCKDOWN,
    )


def _detector_options(cfg: McpServersConfig) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=DETECTOR_SYSTEM_PROMPT,
        tools=["Read"],
        allowed_tools=["Read", "mcp__semgrep-runner__scan_diff"],
        mcp_servers={"semgrep-runner": cfg.semgrep_runner_config},
        output_format={"type": "json_schema", "schema": DetectorOutput.model_json_schema()},
        max_turns=30,
        **_LOCKDOWN,
    )


def _classifier_options(cfg: McpServersConfig) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=CLASSIFIER_SYSTEM_PROMPT,
        tools=["Read", "Grep", "ReadMcpResourceTool", "ListMcpResourcesTool"],
        allowed_tools=["Read", "Grep", "ListMcpResourcesTool", "ReadMcpResourceTool"],
        mcp_servers={"policy-reader": cfg.policy_reader_config},
        output_format={"type": "json_schema", "schema": ClassifierOutput.model_json_schema()},
        max_turns=20,
        **_LOCKDOWN,
    )


def _matcher_options(cfg: McpServersConfig) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=MATCHER_SYSTEM_PROMPT,
        tools=["Read", "ReadMcpResourceTool", "ListMcpResourcesTool"],
        allowed_tools=[
            "ListMcpResourcesTool",
            "ReadMcpResourceTool",
            "mcp__policy-reader__check_applicability",
            "mcp__policy-reader__get_clause",
            "mcp__policy-reader__find_clauses_by_law_article",
        ],
        mcp_servers={"policy-reader": cfg.policy_reader_config},
        output_format={"type": "json_schema", "schema": MatcherOutput.model_json_schema()},
        max_turns=30,
        **_LOCKDOWN,
    )


def _reporter_options(reporter_server: McpSdkServerConfig) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=REPORTER_SYSTEM_PROMPT,
        tools=[],  # PR #67 Gate 6: remove built-ins; emit_report is a server tool
        allowed_tools=[_EMIT_REPORT_TOOL],
        mcp_servers={"reporter_tools": reporter_server},
        max_turns=3,
        **_LOCKDOWN,
    )


# ---------------------------------------------------------------------------
# Reporter stage (coordinator §3.5) — direct query, tri-axial discrimination
# ---------------------------------------------------------------------------
async def _run_reporter_stage(
    consolidated_state: dict[str, Any],
    reporter_server: McpSdkServerConfig,
) -> dict[str, Any]:
    final_result: ResultMessage | None = None
    emit_report_seen = False
    report_payload: dict[str, Any] | None = None
    try:
        async for message in query(
            prompt=build_reporter_prompt(consolidated_state),
            options=_reporter_options(reporter_server),
        ):
            if isinstance(message, ResultMessage):
                final_result = message
            if isinstance(message, AssistantMessage) and message.content:
                for block in message.content:
                    if isinstance(block, ToolUseBlock) and block.name == _EMIT_REPORT_TOOL:
                        if not hasattr(block, "input"):
                            raise MalformedToolUseBlock()
                        if emit_report_seen:
                            raise MultipleReportEmissions(
                                first_payload=report_payload, second_payload=block.input
                            )
                        emit_report_seen = True
                        report_payload = block.input  # canonical capture (§7)
    except (MultipleReportEmissions, MalformedToolUseBlock):
        raise
    except Exception as exc:  # noqa: BLE001 — re-raised as typed coordinator error
        if final_result is None:
            raise CoordinatorStreamFailure(stage="reporter") from exc

    denials = (final_result.permission_denials or []) if final_result else []
    if denials:  # strict: any denial under lockdown is an integrity anomaly
        raise ReporterPermissionDenied(
            denials=denials, subtype=final_result.subtype if final_result else None
        )
    if final_result is not None and final_result.subtype == "error_max_turns":
        raise ReporterTurnsExhausted(num_turns=final_result.num_turns, errors=final_result.errors)
    if not emit_report_seen:
        raise ReportNotEmitted(subtype=final_result.subtype if final_result else None)
    assert report_payload is not None  # emit_report_seen guarantees this
    return report_payload


def _coverage_gap(exc: BaseException) -> str:
    if isinstance(exc, DetectorScanFailed):
        return "cobertura zero - scan nao rodou"
    stage = getattr(exc, "stage", "coordinator")
    return f"pipeline interrompido em {stage} - analise incompleta"


# ---------------------------------------------------------------------------
# Pipeline entry (coordinator §3.0 init + stages + §3.6 termination)
# ---------------------------------------------------------------------------
async def run_pipeline(
    scope: TriagerInput,
    *,
    mcp_config_path: Path = Path(".mcp.json"),
    scratchpad_root: Path = Path(".scratchpad"),
    policy_schema_version: str = "0.1.0",
    policy_version: str = "0.1.0",
    legal_framework: str = "LGPD",
) -> CoordinatorResult:
    configure_logging()
    try:
        cfg = load_mcp_config(mcp_config_path)
        run_id = str(uuid.uuid4())
        run_path = scratchpad_root / f"run-{run_id}"
        run_path.mkdir(parents=True, exist_ok=True)
        reporter_server = create_reporter_server(run_path, run_id)
        log.info("run.start", extra={"run_id": run_id})

        triager_out = await run_branch_b_stage(
            stage="triager",
            prompt=build_triager_prompt(scope),
            options=_triager_options(),
            output_model=TriagerDecision,
            scratchpad_name="01-triager.json",
            run_path=run_path,
            run_id=run_id,
        )
        assert isinstance(triager_out, TriagerDecision)

        findings: list[Finding] = []
        scan_provenance: ScanProvenance | None = None
        candidates_count = 0
        triager_skip_reason: str | None = None

        if triager_out.decision == "skip":
            triager_skip_reason = triager_out.skip_reason
        else:
            detector_out = await run_branch_b_stage(
                stage="detector",
                prompt=build_detector_prompt(scope, triager_out),
                options=_detector_options(cfg),
                output_model=DetectorOutput,
                scratchpad_name="02-detector.json",
                run_path=run_path,
                run_id=run_id,
                on_tool_result=inspect_scan_diff_result,
            )
            assert isinstance(detector_out, DetectorOutput)
            candidates_count = len(detector_out.findings)
            scan_provenance = detector_out.provenance

            classifier_out = await run_branch_b_stage(
                stage="classifier",
                prompt=build_classifier_prompt(detector_out.findings),
                options=_classifier_options(cfg),
                output_model=ClassifierOutput,
                scratchpad_name="03-classifier.json",
                run_path=run_path,
                run_id=run_id,
                verify_passthrough=verify_classifier_passthrough,
                upstream=detector_out.findings,
            )
            assert isinstance(classifier_out, ClassifierOutput)

            matcher_out = await run_branch_b_stage(
                stage="matcher",
                prompt=build_matcher_prompt(classifier_out),
                options=_matcher_options(cfg),
                output_model=MatcherOutput,
                scratchpad_name="04-matcher.json",
                run_path=run_path,
                run_id=run_id,
            )
            assert isinstance(matcher_out, MatcherOutput)
            findings = matcher_out.findings

        run_outcome = derive_run_outcome(triager_skip_reason, candidates_count, findings)
        summary = aggregate_summary(findings)
        consolidated = _build_consolidated_state(
            run_outcome=run_outcome,
            triager_skip_reason=triager_skip_reason,
            report_id=run_id,
            policy_schema_version=policy_schema_version,
            policy_version=policy_version,
            legal_framework=legal_framework,
            scope=scope,
            summary=summary,
            findings=findings,
            scan_provenance=scan_provenance,
        )
        report_payload = await _run_reporter_stage(consolidated, reporter_server)
        log.info("run.done", extra={"run_id": run_id, "run_outcome": run_outcome})
        return CoordinatorReport(payload=report_payload)
    except Exception as exc:  # noqa: BLE001 — projected into the external error envelope
        stage = getattr(exc, "stage", "coordinator")
        log.error("run.halt", extra={"stage": stage, "error": type(exc).__name__})
        return CoordinatorError(cause=exc, stage=stage, coverage_gap=_coverage_gap(exc))
