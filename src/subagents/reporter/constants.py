"""Reporter constants — single source of truth referenced by the factory
(coordinator §7) and the tool registration (reporter §4.2).
"""
from __future__ import annotations

REPORT_SCHEMA_VERSION = "0.1.0"

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
