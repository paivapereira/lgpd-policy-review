"""Phase 2b anchors — Classifier system prompt content (classifier.md §5.1).

The model-level null-on-miss / extra-forbid / empty invariants are already locked by the
Phase 0 anchors in `test_classifier_models.py` (not duplicated). RED against the Phase 1
stub prompt.
"""
from __future__ import annotations

from subagents.classifier.system_prompts import CLASSIFIER_SYSTEM_PROMPT


def test_classifier_prompt_resource_load_first() -> None:
    """§5.1 mandatory first step: load policy://vocabularies + policy://examples via
    ReadMcpResourceTool from the policy-reader server."""
    p = CLASSIFIER_SYSTEM_PROMPT
    assert "ReadMcpResourceTool" in p
    assert "policy://vocabularies" in p
    assert "policy://examples" in p


def test_classifier_prompt_four_fields() -> None:
    p = CLASSIFIER_SYSTEM_PROMPT
    for field in ("operation_type", "data_categories", "declared_legal_basis", "declared_transformations"):
        assert field in p


def test_classifier_prompt_null_on_miss_and_examples_uniform() -> None:
    """RF-003 null-on-miss discipline + identical handling of empty/error/absent
    policy://examples (the three cases treated IDÊNTICA), plus the embedded miss-total
    example anchoring 'null is not invention'."""
    p = CLASSIFIER_SYSTEM_PROMPT
    assert "null" in p
    assert "IDÊNTICA" in p  # empty / error / absent examples handled identically
    assert "<example" in p  # embedded miss-total example


def test_classifier_prompt_has_no_unfilled_candidates_placeholder() -> None:
    """Reconciliation (fixed wiring system_prompt=CLASSIFIER_SYSTEM_PROMPT, not None):
    the candidates arrive in the turn prompt (build_classifier_prompt), so the system
    prompt carries NO unfilled '{candidates_block}' placeholder and is not .format()-ed.
    It DOES declare the 'classified' output wrapper."""
    p = CLASSIFIER_SYSTEM_PROMPT
    assert "{candidates_block}" not in p
    assert "classified" in p  # output wrapper key declared in FORMATO DO OUTPUT
