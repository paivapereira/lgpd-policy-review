"""Reporter payload contract (reporter.md §3.1, §4.3).

`ReportPayload` is the `emit_report` inputSchema (via `model_json_schema()`)
and the captured Report. `report_id` is uuid4-validated at the model level
(failure surfaces as PYDANTIC_VALIDATION); `run_outcome` is the 4-token Literal.

`Finding` and `ScanProvenance` are imported from their producer modules
(Matcher, Detector) — single source of truth (ADR-0001 D3); the specs bind the
shapes ("o output do Matcher é o input do Reporter").

A9 (§4.3 vs §4.8): `SummaryModel` does NOT enforce `total == sum(counts)`. That
check, and `counts == aggregation(findings)`, live in the emit_report handler
producing the distinct errorCodes `TOTAL_NOT_SUM_OF_COUNTS` /
`COUNTS_DISAGREE_WITH_FINDINGS` (§4.8 #3). A model-level validator would raise
first and make those errorCodes unreachable, so the model stays permissive.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from subagents.detector.models import ScanProvenance
from subagents.matcher.models import Finding
from subagents.triager.models import TriagerInput

RunOutcome = Literal[
    "success_with_findings",
    "success_no_candidates",
    "success_all_not_applicable",
    "skipped_by_triager",
]

_UUID4_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
_SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"


class SummaryCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compliant: int = Field(default=0, ge=0)
    violation_candidate: int = Field(default=0, ge=0)
    indeterminate: int = Field(default=0, ge=0)
    not_applicable: int = Field(default=0, ge=0)


class SummaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    counts: SummaryCounts
    total: int = Field(ge=0)


class ReportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(pattern=_UUID4_PATTERN)
    report_schema_version: str = Field(pattern=_SEMVER_PATTERN)
    policy_schema_version: str = Field(pattern=_SEMVER_PATTERN)
    policy_version: str = Field(pattern=_SEMVER_PATTERN)
    legal_framework: Literal["LGPD"]  # MVP (ADR-0007); minor bump for additional frameworks
    run_outcome: RunOutcome
    triager_skip_reason: str | None  # required field, None accepted (§4.3)
    scope: TriagerInput
    summary: SummaryModel
    findings: list[Finding]
    scan_provenance: ScanProvenance | None = None  # present iff a scan ran (§3.5 / C2)
