"""Phase 2b anchors — `verify_classifier_passthrough` (classifier.md §4.3 /
coordinator §3.3 l.205 / §5).

Index-zip POSITIONAL (not keyed — duplicate (file,line,rule_id) are legitimate, G10):
candidate i must preserve the upstream DetectorFinding[i]'s **5 fields** — DD-b resolves
the plan-vs-§4.3 divergence to the 5-field set per coordinator §3.3 l.205 (the
authoritative coordinator-side locus), `{file, line, rule_id, snippet,
surrounding_context}`. Drift / length mismatch → SubagentContractViolation. RED against
the no-op passthrough stub (DID NOT RAISE).
"""
from __future__ import annotations

import pytest

from coordinator.errors import SubagentContractViolation
from subagents.classifier.models import ClassifiedCandidate, ClassifierOutput, StructuredContext
from subagents.classifier.passthrough import verify_classifier_passthrough
from subagents.detector.models import DetectorFinding


def _finding(**override: object) -> DetectorFinding:
    base: dict = dict(file="a.py", line=1, rule_id="BR-CPF", snippet="cpf=x", surrounding_context="# ctx")
    base.update(override)
    return DetectorFinding(**base)  # type: ignore[arg-type]


def _candidate(**override: object) -> ClassifiedCandidate:
    base: dict = dict(
        file="a.py",
        line=1,
        rule_id="BR-CPF",
        snippet="cpf=x",
        surrounding_context="# ctx",
        structured_context=StructuredContext(operation_type=None, declared_legal_basis=None),
    )
    base.update(override)
    return ClassifiedCandidate(**base)  # type: ignore[arg-type]


def test_classifier_passthrough_zip_strict() -> None:
    upstream = [_finding(), _finding(file="b.py", line=9, rule_id="BR-CNPJ", snippet="cnpj=y")]
    # clean 5-field passthrough → no raise
    clean = ClassifierOutput(
        classified=[
            _candidate(),
            _candidate(file="b.py", line=9, rule_id="BR-CNPJ", snippet="cnpj=y"),
        ]
    )
    assert verify_classifier_passthrough(clean, upstream) is None

    # drift in a core field at index 1 (snippet mutated) → violation at that index
    drifted = ClassifierOutput(
        classified=[
            _candidate(),
            _candidate(file="b.py", line=9, rule_id="BR-CNPJ", snippet="MUTATED"),
        ]
    )
    with pytest.raises(SubagentContractViolation) as exc:
        verify_classifier_passthrough(drifted, upstream)
    assert exc.value.stage == "classifier"
    assert exc.value.index == 1


def test_classifier_passthrough_checks_surrounding_context() -> None:
    """DD-b: the verifier compares 5 fields INCLUDING surrounding_context (coordinator
    §3.3 l.205), not the 4 of classifier.md §4.3. A Classifier that mutates only
    surrounding_context must be caught — this is the load-bearing 5-vs-4 anchor."""
    upstream = [_finding(surrounding_context="# original window")]
    mutated = ClassifierOutput(classified=[_candidate(surrounding_context="# TAMPERED window")])
    with pytest.raises(SubagentContractViolation) as exc:
        verify_classifier_passthrough(mutated, upstream)
    assert exc.value.index == 0


def test_classifier_passthrough_length_mismatch_raises() -> None:
    """Cardinality is 1:1 (Classifier does not change cardinality); a length mismatch is
    a contract violation, not a silent zip-truncation."""
    upstream = [_finding(), _finding(file="b.py", line=9)]
    short = ClassifierOutput(classified=[_candidate()])  # 1 vs 2
    with pytest.raises(SubagentContractViolation):
        verify_classifier_passthrough(short, upstream)
