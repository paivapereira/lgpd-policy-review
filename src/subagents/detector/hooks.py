"""Detector `scan_diff` stream-inspection hook (detector.md §6.2 / coordinator §3.2, §5).

Phase 2b RED scaffolding: a no-op stub so the hook anchors import and fail on the
ASSERTION (no raise), not on import. The real escalate-all body is authored in the
Phase 2b impl commit.
"""
from __future__ import annotations

from typing import Any


def inspect_scan_diff_result(message: Any) -> None:  # noqa: ARG001 — stub
    """STUB (Phase 2b impl pending). Will deterministically escalate any `scan_diff`
    domain error (Option B `errorCode` in `UserMessage.tool_use_result.structuredContent`)
    as `DetectorScanFailed`."""
    return None
