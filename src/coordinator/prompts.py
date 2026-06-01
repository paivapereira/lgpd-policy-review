"""Prompt builders (coordinator.md §3.1-§3.5 — `build_*_prompt`).

Phase 1: functional stubs that thread the inter-stage data contract (JSON inline,
§4). The canonical prompt text with few-shots / XML structure is authored per
stage in Phase 2a (Triager, Reporter) and Phase 2b (Detector, Classifier, Matcher).
"""
from __future__ import annotations

import json
from typing import Any

from subagents.classifier.models import ClassifierOutput
from subagents.detector.models import DetectorFinding
from subagents.triager.models import TriagerDecision, TriagerInput
from subagents.triager.system_prompts import TRIAGER_SYSTEM_PROMPT


def build_triager_prompt(scope: TriagerInput) -> str:
    # Renders the §5.1 format-string template (triager §2.2): the four single-brace
    # PR refs are substituted; double-brace JSON examples collapse to single-brace.
    # Delivered as the turn prompt (coordinator §3.1); the Triager stage runs in
    # SDK minimal system-prompt mode (DD-4 / §5.1 note).
    return TRIAGER_SYSTEM_PROMPT.format(
        pr_number=scope.pr_number,
        base_ref=scope.base_ref,
        head_ref=scope.head_ref,
        repo_url=scope.repo_url,
    )


def build_detector_prompt(scope: TriagerInput, triager_out: TriagerDecision) -> str:
    return (
        "Detect candidate personal-data handling points in the PR diff via scan_diff.\n"
        f"base_ref: {scope.base_ref}\n"
        f"head_ref: {scope.head_ref}\n"
        f"triager_relevance: {triager_out.relevance_summary}\n"
    )


def build_classifier_prompt(findings: list[DetectorFinding]) -> str:
    payload = json.dumps([f.model_dump(mode="json") for f in findings], ensure_ascii=False)
    return f"Classify each candidate (structured_context). Candidates JSON:\n{payload}\n"


def build_matcher_prompt(classifier_out: ClassifierOutput) -> str:
    payload = json.dumps(classifier_out.model_dump(mode="json"), ensure_ascii=False)
    return f"Evaluate each classified candidate against the Policy. Input JSON:\n{payload}\n"


def build_reporter_prompt(consolidated_state: dict[str, Any]) -> str:
    payload = json.dumps(consolidated_state, ensure_ascii=False)
    return (
        "Emit the final Report. Consolidated state JSON "
        "(copy verbatim into the emit_report payload):\n"
        f"{payload}\n"
    )
