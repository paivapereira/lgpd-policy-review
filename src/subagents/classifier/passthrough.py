"""Classifier passthrough verifier (classifier.md §4.3 / coordinator §3.3 l.205 / §5).

Coordinator-side 1:1 positional check that each classified candidate preserved the
upstream `DetectorFinding`'s locus verbatim. POSITIONAL (index zip), NOT keyed —
duplicate `(file, line, rule_id)` are legitimate (G10), so a keyed join would
mis-correlate. The compared set is the **5 fields** `{file, line, rule_id, snippet,
surrounding_context}` per coordinator §3.3 l.205 (DD-b: the authoritative coordinator-side
locus; classifier.md §4.3's 4-field block is stale doc-lag). Any drift / cardinality
mismatch → `SubagentContractViolation` (the Classifier does not change cardinality).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from coordinator.errors import SubagentContractViolation

_PASSTHROUGH_FIELDS = ("file", "line", "rule_id", "snippet", "surrounding_context")


def verify_classifier_passthrough(obj: BaseModel, upstream: Any) -> None:
    """Raise `SubagentContractViolation(stage="classifier", ...)` if the classified
    candidates dropped, reordered, or mutated any of the 5 passthrough fields relative to
    the upstream Detector findings."""
    classified = list(getattr(obj, "classified", None) or [])
    upstream_list = list(upstream or [])
    if len(classified) != len(upstream_list):
        raise SubagentContractViolation(
            stage="classifier",
            detail=f"cardinality drift: {len(classified)} classified vs {len(upstream_list)} upstream",
        )
    for index, (candidate, source) in enumerate(zip(classified, upstream_list)):
        for field in _PASSTHROUGH_FIELDS:
            if getattr(candidate, field) != getattr(source, field):
                raise SubagentContractViolation(stage="classifier", index=index, detail=f"{field} drift")
