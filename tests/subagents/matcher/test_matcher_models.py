"""Phase 0 anchors — Matcher output contract (matcher.md §3.1, §3.1bis, §3.2, §3.3).

The wire `Finding` is enum-tag (verdict Literal + per-verdict optionals as
anyOf[T,null]), NEVER oneOf/discriminator (DD-M13 — oneOf silently disables the
SDK grammar). Per-verdict field presence is enforced by a model_validator
(fail-loud), mirroring the Triager XOR pattern. Complexity budget (matcher §3.3,
"verificado #48, doc Structured outputs"): <=16 union params, <=24 optional.
"""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from subagents.matcher.models import Finding, MatcherOutput, VerificationScope


def _common(**override: object) -> dict:
    base: dict = dict(
        file="auth.py",
        line=14,
        snippet="db.users.insert(email=email)",
        rule_id="DATA-001",
        data_categories=["email"],
        operation_type="collection",
        policy_clause_ref="POL-005",
        policy_schema_version="0.1.0",
        policy_version="1.2.0",
        legal_framework="LGPD",
    )
    base.update(override)
    return base


def test_matcher_finding_schema_is_enum_tag_not_oneof() -> None:
    schema = MatcherOutput.model_json_schema()
    text = json.dumps(schema)
    assert schema["type"] == "object"
    assert "oneOf" not in text
    assert "discriminator" not in text

    finding_def = schema["$defs"]["Finding"]
    assert set(finding_def["properties"]["verdict"]["enum"]) == {
        "compliant",
        "violation_candidate",
        "indeterminate",
        "not_applicable",
    }
    # Budget: union (anyOf) <= 16; optional params <= 24 (matcher §3.3 / #48).
    assert text.count('"anyOf"') <= 16
    required = set(finding_def.get("required", []))
    optional = [p for p in finding_def["properties"] if p not in required]
    assert len(optional) <= 24


def test_matcher_finding_compliant_requires_evidence() -> None:
    Finding(**_common(verdict="compliant", evidence="consent guard present"))
    with pytest.raises(ValidationError):
        Finding(**_common(verdict="compliant"))  # missing evidence
    with pytest.raises(ValidationError):
        Finding(**_common(verdict="compliant", evidence="ok", reason="nope"))  # cross-variant


def test_matcher_finding_violation_candidate() -> None:
    Finding(**_common(verdict="violation_candidate", evidence="direct collection, no guard"))
    Finding(
        **_common(
            verdict="violation_candidate",
            evidence="x",
            contradicted_requirement="R1",
        )
    )
    with pytest.raises(ValidationError):
        Finding(**_common(verdict="violation_candidate"))  # missing evidence


def test_matcher_finding_indeterminate_requires_verification_scope() -> None:
    Finding(
        **_common(
            verdict="indeterminate",
            verification_scope=VerificationScope(
                dimension="retention",
                prescribed_treatment="delete_after_purpose",
                verification_target="runtime retention policy",
            ),
        )
    )
    with pytest.raises(ValidationError):
        Finding(**_common(verdict="indeterminate"))  # missing verification_scope


def test_matcher_finding_not_applicable_requires_reason() -> None:
    Finding(**_common(verdict="not_applicable", reason="POL-000 is definitional"))
    with pytest.raises(ValidationError):
        Finding(**_common(verdict="not_applicable"))  # missing reason


def test_matcher_finding_optional_requires_human_review() -> None:
    f = Finding(**_common(verdict="not_applicable", reason="x", requires_human_review=True))
    assert f.requires_human_review is True
    # absent is allowed (Reporter: absence != false)
    f2 = Finding(**_common(verdict="compliant", evidence="ok"))
    assert f2.requires_human_review is None


def test_matcher_output_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        MatcherOutput(findings=[], bogus=1)
