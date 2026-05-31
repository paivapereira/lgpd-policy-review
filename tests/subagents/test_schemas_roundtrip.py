"""Phase 0 acceptance — every stage schema is a JSON-serializable object schema.

Parametrized over the input/output/payload models that feed `output_format`
(or the emit_report inputSchema). Subset/inclusion assertions per
test-strategy.md (acceptance role, not anchor).
"""
from __future__ import annotations

import json

import pytest
from pydantic import BaseModel

from subagents.classifier.models import ClassifierOutput
from subagents.detector.models import DetectorOutput
from subagents.matcher.models import MatcherOutput
from subagents.reporter.models import ReportPayload
from subagents.triager.models import TriagerDecision, TriagerInput

_MODELS: list[type[BaseModel]] = [
    TriagerInput,
    TriagerDecision,
    DetectorOutput,
    ClassifierOutput,
    MatcherOutput,
    ReportPayload,
]


@pytest.mark.parametrize("model", _MODELS, ids=lambda m: m.__name__)
def test_as1_all_stage_schemas_roundtrip(model: type[BaseModel]) -> None:
    schema = model.model_json_schema()
    assert isinstance(schema, dict)
    assert schema["type"] == "object"
    # additionalProperties:false everywhere (extra="forbid")
    assert schema.get("additionalProperties") is False
    # JSON-serializable (the SDK sends this over the wire)
    json.dumps(schema)
