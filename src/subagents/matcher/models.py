"""Matcher output contract (matcher.md §3.1, §3.1bis, §3.2, §3.3).

`Finding` is the canonical pipeline finding — the Matcher produces it and the
Reporter consumes it verbatim ("o output do Matcher **é** o input do Reporter",
reporter §3.2). It is encoded **enum-tag**: `verdict` is a `Literal` and every
per-verdict field is an optional `anyOf[T,null]`. NEVER `oneOf` / a wire-level
discriminated union — that silently disables the SDK grammar (DD-M13, confirmed
in sdk_output_format_complex/RESULTS.md). Per-verdict field presence (and the
mutual exclusivity of the variant fields) is enforced by a `model_validator`,
fail-loud, mirroring the Triager directional-XOR pattern.

Defining `Finding` once here (the producer) and importing it in
`subagents.reporter.models` (the consumer) keeps a single symbol (ADR-0001 D3)
and sidesteps the mypy `union-attr` risk of `Field(discriminator=...)`.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

Verdict = Literal["compliant", "violation_candidate", "indeterminate", "not_applicable"]

# The four verdict-specific (variant) fields. Exactly one variant's required
# field(s) may be present per verdict; all others must be None.
_VARIANT_FIELDS = ("evidence", "contradicted_requirement", "verification_scope", "reason")


class VerificationScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: str
    prescribed_treatment: str
    verification_target: str


def _forbid_other_variants(finding: "Finding", *, allowed: set[str]) -> None:
    for name in _VARIANT_FIELDS:
        if name not in allowed and getattr(finding, name) is not None:
            raise ValueError(f"verdict {finding.verdict!r} must not carry '{name}'")


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Locus identity — verbatim passthrough from the Detector.
    file: str
    line: int
    snippet: str
    rule_id: str
    # Context passthrough from the Classifier.
    data_categories: list[str]
    operation_type: str  # passthrough; may be != "collection" in not_applicable (§3.2 i)
    # Verdict (verbatim from check_applicability).
    verdict: Verdict
    policy_clause_ref: str  # "POL-NNN" — present in all four verdicts (DD-M21)
    # Provenance trinca — per-finding, verbatim from check_applicability (RF-009).
    policy_schema_version: str
    policy_version: str
    legal_framework: Literal["LGPD"]  # MVP scope (ADR-0007); minor bump for GDPR/etc.
    # Human escalation — originated by the Matcher (DD-M29); absence != false.
    requires_human_review: bool | None = None
    # Verdict-specific variant fields (enum-tag: all optional at the wire level).
    evidence: str | None = None  # compliant, violation_candidate
    contradicted_requirement: str | None = None  # violation_candidate (optional)
    verification_scope: VerificationScope | None = None  # indeterminate
    reason: str | None = None  # not_applicable

    @model_validator(mode="after")
    def _verdict_variant_consistency(self) -> "Finding":
        if self.verdict == "compliant":
            if self.evidence is None:
                raise ValueError("compliant requires 'evidence'")
            _forbid_other_variants(self, allowed={"evidence"})
        elif self.verdict == "violation_candidate":
            if self.evidence is None:
                raise ValueError("violation_candidate requires 'evidence'")
            _forbid_other_variants(self, allowed={"evidence", "contradicted_requirement"})
        elif self.verdict == "indeterminate":
            if self.verification_scope is None:
                raise ValueError("indeterminate requires 'verification_scope'")
            _forbid_other_variants(self, allowed={"verification_scope"})
        else:  # not_applicable
            if self.reason is None:
                raise ValueError("not_applicable requires 'reason'")
            _forbid_other_variants(self, allowed={"reason"})
        return self


class MatcherOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings: list[Finding]
