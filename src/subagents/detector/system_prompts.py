"""Detector system prompt. Phase 1 stub; real behavior (scan_diff + context) in Phase 2b."""
from __future__ import annotations

DETECTOR_SYSTEM_PROMPT = (
    "You are the Detector subagent (Phase 1 walking-skeleton stub). Emit a "
    "DetectorOutput matching the schema. Real scan_diff-driven detection is "
    "authored in Phase 2b."
)
