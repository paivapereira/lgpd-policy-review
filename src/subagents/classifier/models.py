"""Classifier output contract (classifier.md §3.1, §3.3).

`StructuredContext` enriches each candidate. The two scalar fields are
`str | None` with NO default → required + nullable: RF-003 demands an explicit,
auditable `null` on miss, not silent omission (`required + nullable` materializes
that; `optional + default` would allow silent absence). The two list fields
default `[]` (never null). Vocab membership is soft (system prompt + null-on-miss),
NOT a hard `Enum` (DD-C2) — the Matcher is the downstream membership authority.

Required-nullable scalars are declared before the defaulted lists to keep the
generated `__init__` ordering clean under the Pydantic dataclass transform; field
order only affects schema property order, not validation.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StructuredContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_type: str | None  # token of operation vocab, or null (null-on-miss)
    declared_legal_basis: str | None  # token of lawful_basis vocab, or null
    data_categories: list[str] = Field(default_factory=list)  # category tokens; [] if none
    declared_transformations: list[str] = Field(default_factory=list)  # free-form; [] if none


class ClassifiedCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Verbatim passthrough from DetectorFinding (preserved without mutation):
    file: str
    line: int
    rule_id: str
    snippet: str
    surrounding_context: str
    # Classifier enrichment:
    structured_context: StructuredContext


class ClassifierOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classified: list[ClassifiedCandidate]
