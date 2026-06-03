"""Reporter constants — single source of truth referenced by the factory
(coordinator §7) and the tool registration (reporter §4.2).
"""
from __future__ import annotations

REPORT_SCHEMA_VERSION = "0.1.0"

# Reporter dual-sink #1 filename (reporter §4.9): the handler writes the committed Report
# here atomically ONLY on a successful emit. The coordinator's single-success guard reads its
# presence as the success signal (ADR-0016) — shared here so the writer and reader never drift.
REPORT_SINK_FILENAME = "99-report.json"

# Canonical English tool description (reporter.md §4.2), no markdown.
EMIT_REPORT_DESCRIPTION = (
    "Emit the final aggregated Report JSON for the current pull request "
    "analysis run. The payload must be a complete Report object matching "
    "the declared schema, including the provenance triple, summary counts, "
    "run_outcome discriminator, and all findings preserved verbatim from "
    "the Matcher output. Use this tool exactly once per query. After "
    "successful invocation, end the turn - do not call again. Do not "
    "synthesize or modify findings."
)
