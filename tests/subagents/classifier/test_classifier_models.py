"""Phase 0 anchors — Classifier output contract (classifier.md §3.1).

Scalars are `Optional[str]` with NO default → required + nullable (RF-003
null-on-miss is explicit, not silent omission). Lists default `[]`. Vocab
membership is soft (system prompt), NOT a hard Enum (DD-C2).
"""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from subagents.classifier.models import (
    ClassifiedCandidate,
    ClassifierOutput,
    StructuredContext,
)


def test_classifier_structured_context_scalars_required_nullable() -> None:
    schema = StructuredContext.model_json_schema()
    required = set(schema.get("required", []))
    # required + nullable scalars
    assert "operation_type" in required
    assert "declared_legal_basis" in required
    op = schema["properties"]["operation_type"]
    assert {"type": "string"} in op["anyOf"]
    assert {"type": "null"} in op["anyOf"]
    # lists default [] → NOT required, no Enum
    assert "data_categories" not in required
    assert "declared_transformations" not in required
    assert "enum" not in json.dumps(schema)  # no hard vocab Enum (DD-C2)


def test_classifier_null_on_miss_is_valid() -> None:
    sc = StructuredContext(operation_type=None, declared_legal_basis=None)
    assert sc.operation_type is None
    assert sc.declared_legal_basis is None
    assert sc.data_categories == []
    assert sc.declared_transformations == []


def test_classified_candidate_extra_forbid() -> None:
    sc = StructuredContext(operation_type=None, declared_legal_basis=None)
    with pytest.raises(ValidationError):
        ClassifiedCandidate(
            file="a.py",
            line=1,
            rule_id="R",
            snippet="x",
            surrounding_context="ctx",
            structured_context=sc,
            bogus=1,
        )


def test_classifier_output_accepts_empty() -> None:
    assert ClassifierOutput(classified=[]).classified == []
