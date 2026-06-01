"""Detector constants — single source for the scan_diff tool name (the hook's `tool`
field) and the surrounding-context window (DD-D2). detector.md §3.4 / §6.2.
"""
from __future__ import annotations

# The Option-B tool the Detector consumes; the stream-inspection hook tags
# DetectorScanFailed with this name for blame/audit (coordinator §5).
SCAN_DIFF_TOOL_NAME = "mcp__semgrep-runner__scan_diff"

# +/-N lines window the Detector Reads around each finding to compose
# surrounding_context (DD-D2). Provisional — calibrate in MC-D.
SURROUNDING_CONTEXT_LINES = 10
