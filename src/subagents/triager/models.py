"""Triager I/O models (triager.md §2.1, §3.1).

`TriagerInput` is the single source of truth for the pipeline scope; the
coordinator constructs it and the Reporter references it verbatim
(`ReportPayload.scope`, version coupling per triager §2.1).

`TriagerDecision` is the flat enum-tag wire model. The directional XOR
(relevance_summary present iff proceed; skip_reason present iff skip) lives in
a `model_validator`, NOT the wire grammar — a root union would emit `oneOf`,
silently disabling the SDK constrained decoding (DD-T16). The schema is a flat
object with two `anyOf[str,null]` optional fields and no discriminator.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class TriagerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pr_number: int
    base_ref: str  # SHA or nominal ref (e.g. "main")
    head_ref: str  # SHA or nominal ref (e.g. "feature/x")
    repo_url: str  # HTTPS repo URL — provenance only in MVP, not fetched


class TriagerDecision(BaseModel):
    """Wire model (flat enum-tag) emitted in `ResultMessage.structured_output`."""

    model_config = ConfigDict(extra="forbid")

    decision: Literal["proceed", "skip"]
    relevance_summary: str | None = None  # present iff decision == "proceed"
    skip_reason: str | None = None  # present iff decision == "skip"

    @model_validator(mode="after")
    def _directional_xor(self) -> "TriagerDecision":
        if self.decision == "proceed":
            if self.relevance_summary is None or self.skip_reason is not None:
                raise ValueError("proceed requires relevance_summary and forbids skip_reason")
        else:  # skip
            if self.skip_reason is None or self.relevance_summary is not None:
                raise ValueError("skip requires skip_reason and forbids relevance_summary")
        return self
