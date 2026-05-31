"""Phase 0 anchors — Triager I/O models (triager.md §2.1, §3.1, §3.2).

The directional XOR lives in a `model_validator` (NOT the wire grammar — a
root union would emit `oneOf` and silently disable constrained decoding,
DD-T16). The wire schema must be a flat object: no `oneOf`, no discriminator.
"""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from subagents.triager.models import TriagerDecision, TriagerInput


def test_triager_input_four_required_fields() -> None:
    ti = TriagerInput(
        pr_number=42,
        base_ref="main",
        head_ref="feature/x",
        repo_url="https://github.com/example/app",
    )
    assert ti.pr_number == 42
    assert ti.base_ref == "main"


def test_triager_decision_directional_xor() -> None:
    # Valid: proceed with relevance_summary; skip with skip_reason.
    TriagerDecision(decision="proceed", relevance_summary="touches PII collection")
    TriagerDecision(decision="skip", skip_reason="docs-only change")

    # proceed missing relevance_summary.
    with pytest.raises(ValidationError):
        TriagerDecision(decision="proceed")
    # proceed carrying skip_reason.
    with pytest.raises(ValidationError):
        TriagerDecision(decision="proceed", relevance_summary="x", skip_reason="y")
    # skip missing skip_reason.
    with pytest.raises(ValidationError):
        TriagerDecision(decision="skip")
    # skip carrying relevance_summary.
    with pytest.raises(ValidationError):
        TriagerDecision(decision="skip", skip_reason="x", relevance_summary="y")


def test_triager_schema_has_no_oneof_at_root() -> None:
    schema = TriagerDecision.model_json_schema()
    text = json.dumps(schema)
    assert schema["type"] == "object"
    assert "oneOf" not in text
    assert "discriminator" not in text
    assert schema["properties"]["decision"]["enum"] == ["proceed", "skip"]
    # exactly two union (anyOf) nodes: relevance_summary, skip_reason
    assert text.count('"anyOf"') == 2


def test_triager_decision_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        TriagerDecision(decision="skip", skip_reason="x", bogus=1)
