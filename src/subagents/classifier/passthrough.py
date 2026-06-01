"""Classifier passthrough verifier (classifier.md §4.3 / coordinator §3.3, §5).

Phase 2b RED scaffolding: a no-op stub so the passthrough anchor imports and fails on
the ASSERTION (no raise on drift), not on import. The real 5-field positional zip is
authored in the Phase 2b impl commit.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def verify_classifier_passthrough(obj: BaseModel, upstream: Any) -> None:  # noqa: ARG001 — stub
    """STUB (Phase 2b impl pending). Will index-zip each classified candidate's
    `(file, line, rule_id, snippet, surrounding_context)` against the upstream
    `DetectorFinding[i]` and raise `SubagentContractViolation` on drift / length
    mismatch."""
    return None
