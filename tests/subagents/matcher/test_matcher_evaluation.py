"""Phase 2b acceptance + prompt anchors — Matcher evaluation behaviors
(matcher.md §2.3, §3.4, §4.3, §4.4, §5.1, §6.5, §7.3).

The enum-tag wire shape + per-verdict validators are locked by the Phase 0 anchors in
`test_matcher_models.py` (not duplicated). Here: the prompt PRESCRIBES the check-all
behaviors (short-circuit, trinca source, coverage gap, deprecated retry, projection) —
prompt-content is RED against the Phase 1 stub; the corresponding Finding shapes validate
(documents-only). The behaviors themselves are LLM-driven and exercised LIVE at G2b.
"""
from __future__ import annotations

from subagents.matcher.models import Finding, MatcherOutput
from subagents.matcher.system_prompts import MATCHER_SYSTEM_PROMPT

_TRINCA = dict(policy_schema_version="0.1.0", policy_version="0.1.0", legal_framework="LGPD")


def _finding(**override: object) -> Finding:
    base: dict = dict(
        file="a.py", line=1, snippet="cpf=x", rule_id="BR-CPF",
        data_categories=["cpf"], operation_type="collection",
        verdict="not_applicable", policy_clause_ref="POL-000", reason="r", **_TRINCA,
    )
    base.update(override)
    return Finding(**base)  # type: ignore[arg-type]


def test_matcher_cardinality_floor() -> None:
    """DECISION (b) — DOCUMENTS-ONLY (§3.4). Asserts the floor `len(findings) >=
    candidates_count` + a POL-000 finding per candidate on a HAND-BUILT fixture. This
    does NOT enforce cardinality hermetically (the count is LLM-produced; a floor check
    on a self-built fixture is tautological) — the real floor is exercised at LIVE G2b.
    Kept only to lock the §3.4 contract shape as documentation."""
    candidates_count = 2
    out = MatcherOutput(
        findings=[
            _finding(file="a.py", line=1, policy_clause_ref="POL-000", reason="definitional"),
            _finding(file="b.py", line=9, policy_clause_ref="POL-000", reason="definitional"),
        ]
    )
    assert len(out.findings) >= candidates_count
    by_candidate = {(f.file, f.line) for f in out.findings}
    for loc in by_candidate:  # every candidate carries at least its POL-000 floor finding
        assert any(f.policy_clause_ref == "POL-000" for f in out.findings if (f.file, f.line) == loc)


def test_as1_matcher_short_circuit() -> None:
    """§4.3 step 2a / §4.4 C2: insufficient context (operation_type None OR
    data_categories []) → ONE not_applicable(POL-000) + requires_human_review=True +
    'contexto insuficiente' reason, WITHOUT calling the tool. Prompt prescribes it; the
    shape validates."""
    assert "POL-000" in MATCHER_SYSTEM_PROMPT
    assert "contexto insuficiente" in MATCHER_SYSTEM_PROMPT
    assert "requires_human_review" in MATCHER_SYSTEM_PROMPT
    sc = _finding(
        data_categories=[],  # empty → short-circuit trigger
        verdict="not_applicable", policy_clause_ref="POL-000",
        requires_human_review=True, reason="contexto insuficiente para avaliação",
    )
    assert sc.verdict == "not_applicable" and sc.policy_clause_ref == "POL-000"
    assert sc.requires_human_review is True


def test_as2_matcher_curto_circuito_trinca() -> None:
    """§4.4 R1 / §7.3: the short-circuit finding (no tool return) sources its provenance
    trinca from policy://schema-version. Prompt prescribes the source; the finding carries
    the three fields."""
    p = MATCHER_SYSTEM_PROMPT
    assert "policy://schema-version" in p
    for k in ("policy_schema_version", "policy_version", "legal_framework"):
        assert k in p
    sc = _finding(data_categories=[], requires_human_review=True, reason="contexto insuficiente")
    assert sc.policy_schema_version == "0.1.0"
    assert sc.policy_version == "0.1.0"
    assert sc.legal_framework == "LGPD"


def test_as3_matcher_coverage_gap() -> None:
    """§4.4 / DD-M8: non-empty data + collection + only POL-000 governing → verdict stays
    not_applicable BUT requires_human_review=True with a gap reason. Prompt prescribes the
    gap escalation; the shape validates."""
    assert "lacuna de cobertura" in MATCHER_SYSTEM_PROMPT
    gap = _finding(
        data_categories=["cpf"], operation_type="collection",
        verdict="not_applicable", policy_clause_ref="POL-000",
        requires_human_review=True, reason="lacuna de cobertura: nenhuma cláusula substantiva governa",
    )
    assert gap.verdict == "not_applicable" and gap.requires_human_review is True


def test_as4_matcher_clause_deprecated_retry() -> None:
    """§6.5: on CLAUSE_DEPRECATED, re-evaluate over details.successors (bounded). Prompt
    prescribes the successor retry."""
    p = MATCHER_SYSTEM_PROMPT
    assert "CLAUSE_DEPRECATED" in p
    assert "successor" in p


def test_matcher_prompt_prescribes_projection() -> None:
    """§2.3: the projection lives IN THE PROMPT — rename operation_type→operation and
    declared_legal_basis→legal_basis, DROP declared_transformations. (Hermetic side of
    test_as2_e2e_projection_renames_reach_tool; LIVE G2b spies the real ToolUseBlock.)"""
    p = MATCHER_SYSTEM_PROMPT
    assert "operation_type" in p and "operation" in p
    assert "declared_legal_basis" in p and "legal_basis" in p
    assert "declared_transformations" in p and "descarte" in p  # DROP declared_transformations
