"""Phase 2b anchors — Detector system prompt content (detector.md §5.1 / §5.2).

These are the prompt-content side of the Detector contract; the model-level strip-opinion
/ provenance / empty-findings invariants are already locked by the Phase 0 anchors in
`test_detector_models.py` (not duplicated here). RED against the Phase 1 stub prompt.
"""
from __future__ import annotations

from subagents.detector.system_prompts import DETECTOR_SYSTEM_PROMPT


def test_detector_mapping_strips_opinion() -> None:
    """§5.1 item 3 (DD-D1): the prompt prescribes the strip-opinion mapping — rename the
    location fields, drop the Semgrep opinion (rule_severity / rule_message)."""
    p = DETECTOR_SYSTEM_PROMPT
    assert "rule_severity" in p and "rule_message" in p  # named as the fields NOT to carry
    assert "location.path" in p and "location.start_line" in p  # the rename source fields


def test_detector_prompt_forbids_fabrication() -> None:
    """§5.1 item 4 (immutable, 'No fabricated certainty'): on a scan error (errorCode
    present) the Detector must NOT invent findings nor emit a misleading findings:[]."""
    p = DETECTOR_SYSTEM_PROMPT
    assert "errorCode" in p
    assert "invente" in p  # "NÃO invente findings" (non-fabrication rule)
    assert "findings" in p


def test_detector_prompt_has_behavior_anchor_examples() -> None:
    """§5.2: three few-shot behavior anchors (normal / empty / error). The error anchor
    (Exemplo C) references a scan errorCode (e.g. SCAN_TIMEOUT)."""
    p = DETECTOR_SYSTEM_PROMPT
    assert "<example" in p  # few-shot block present
    assert "SCAN_TIMEOUT" in p  # Exemplo C — scan-with-error behavior anchor
