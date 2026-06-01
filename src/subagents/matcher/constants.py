"""Matcher constants — single source for the policy-reader server name, the two
resources the check-all reads first, and the definitional backstop clause
(matcher.md §4.3, §4.4).
"""
from __future__ import annotations

POLICY_READER_SERVER = "policy-reader"

# Read first by the check-all (matcher.md §5.1 step 1): catalog enumerates the active
# clauses to sweep; schema-version supplies the provenance trinca that the short-circuit
# finding sources (R1 / §7.3) since it has no tool return to copy it from.
CATALOG_URI = "policy://catalog"
SCHEMA_VERSION_URI = "policy://schema-version"

# Definitional, always-active backstop clause: every candidate receives >=1 finding
# (its POL-000 not_applicable floor) and the short-circuit/coverage-gap findings cite it
# (DD-M4 / §4.4).
BACKSTOP_CLAUSE = "POL-000"
