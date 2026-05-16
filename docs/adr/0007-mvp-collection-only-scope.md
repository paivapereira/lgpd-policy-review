# ADR-0007 — MVP v0.1.0 operation scope: only `collection` is evaluated against clauses

**Status.** Accepted (retrospective — restriction implicit since session #03, articulated in `REQUIREMENTS.md` RF-004 in PR #22 with a placeholder reference, formalized here).
**Date.** 2026-05-15
**Supersedes.** Nothing.
**Superseded by.** Nothing.
**Related.** ADR-0005 (multi-client policy architecture — Decision 4 introduced `policy://vocabularies`; this ADR governs which values of the `operation` vocabulary the Matcher acts on during MVP), ADR-0006 (language conventions — fixes the English-token form of the values cited below).

## Context

The Matcher subagent is designed framework-aware via `policy://vocabularies` (ADR-0005 Decision 4): for any candidate enriched by the Classifier, the Matcher dispatches against cláusulas whose `applies_to.operation_type` matches the candidate's `operation_type`. The operation vocabulary loaded from `policy/vocabularies/<framework>/operation.yaml` for the LGPD MVP contains **22 values** mapping the operations enumerated in LGPD Art. 5º X (and GDPR Art. 4(2) for cross-framework reuse): `collection`, `recording`, `organisation`, `structuring`, `storage`, `adaptation`, `alteration`, `retrieval`, `consultation`, `use`, `disclosure_by_transmission`, `dissemination`, `making_available`, `alignment`, `combination`, `restriction`, `erasure`, `destruction`, `evaluation`, `international_transfer`, `sharing`, `other`.

The MVP v0.1.0 evaluates clause applicability **only** for candidates with `operation_type: collection`. Candidates with any of the other 21 vocabulary values short-circuit before clause matching with `verdict: not_applicable` and a self-documenting reason string. This scope restriction is design-deliberate, not a missing feature.

The restriction has been implicit since session #03 (when the data collection operation was identified as the highest-signal target for the empirical contribution of the TCC) and was articulated in `docs/REQUIREMENTS.md` RF-004 during PR #22 with a placeholder reference to "ADR retroativo a redigir, registrado em `session-handoff.md`". This ADR fulfills that placeholder.

## Decision

### 1. Only `operation_type: collection` is evaluated against clauses

The Matcher evaluates candidates with `operation_type: collection` against clauses whose `applies_to.operation_type` includes `collection`. Candidates with `operation_type` in any of the 21 remaining vocabulary values short-circuit before clause matching:

```
verdict: not_applicable
reason: "operation outside MVP scope (v0.1.0): only 'collection' is evaluated"
```

The reason string is the literal text above. It is self-documenting in the Report: a human reader inspecting a `not_applicable` finding learns why the candidate was not evaluated without opening the requirement or this ADR.

**Rationale.** Three forces converge to support the restriction:

- **Research signal density.** The TCC benchmark corpus targets approximately 200 synthetic snippets (`docs/proposta-tcc2.md` §4.d–e). Distributing detection coverage uniformly across 22 operations would yield fewer than 10 snippets per operation, well below the threshold where false-positive and false-negative rates become statistically meaningful. Concentrating the corpus on the `collection` operation preserves signal density for the primary thesis claim (coverage gap on Brazilian identifiers detected at the point of data ingress).
- **Foundational data-flow position.** `collection` is the operation at which personal data first enters the system from external sources. Detecting collection accurately is logically prior to reasoning about subsequent operations (use, storage, transfer) over the same data; the inverse staging — reasoning about transfer of data whose collection point is unknown — is incoherent. Starting from the foundational operation matches the natural staging of a multi-operation tool.
- **Compliance-domain breadth.** Each of the 21 non-`collection` operations carries its own statute-grounded compliance dimensions: finality limitation and purpose binding for `use`; consent withdrawal and right-to-deletion for `erasure` and `destruction`; international transfer rules (LGPD Art. 33–36, GDPR Cap. V) for `international_transfer`; retention limits for `storage`; and so on. Each dimension would expand the clause set, the prescribed-treatment vocabulary, and the verification-scope semantics. The MVP scope limits this expansion to one operation to keep the contribution defensible at depth rather than diffuse at breadth.

### 2. Non-`collection` cláusulas remain in the Policy as audit-trail content

Cláusulas whose `applies_to.operation_type` is any value other than `collection` are first-class Policy content. They are:

- Authored in the same form as `collection` cláusulas, following `policy/SCHEMA.md`.
- Loaded at server startup with full validation against the schema and the vocabulary.
- Retrievable via `get_clause(clause_id)` and `find_clauses_by_law_article(...)`.
- Counted in `policy_schema_version` / `policy_version` bumps when content changes.
- Reflected in the trinque provenance of any Report header (`policy_version` covers the full Policy, including non-`collection` cláusulas).

What they do **not** do during MVP v0.1.0:

- Participate in `check_applicability` dispatch.
- Generate findings in the Report (the upstream candidate, if any, generates a `not_applicable` finding under Decision 1; the clause itself is not cited there).

**Rationale.** Removing non-`collection` cláusulas from the Policy would lose audit content — a non-`collection` cláusula remains a valid statement of the client's compliance posture under LGPD even if not evaluated at MVP — and would couple the MVP scope decision to the Policy authoring decision: two changes for one scope expansion. Preserving the cláusulas keeps the two concerns separable: MVP scope is a Matcher dispatch policy, Policy authoring is independent.

### 3. Post-MVP scope expansion is additive, not contract-breaking

Expanding MVP scope to evaluate additional operations is an additive change. The observable contract surfaces remain stable:

- `check_applicability` input shape unchanged (the `operation_type` field already accepts any vocabulary value).
- The four verdict variants (`compliant`, `violation_candidate`, `indeterminate`, `not_applicable`) unchanged.
- Trinque provenance (`policy_schema_version`, `policy_version`, `legal_framework`) unchanged.
- `policy://vocabularies` shape unchanged.

The operational change required to enable a second operation is a Matcher dispatch-policy update (a configuration-level decision recorded in a follow-up ADR when activated) plus test corpus expansion for the newly evaluated operation. No schema bump, no spec rewrite of `policy-reader`, no ADR ceremony other than the activation ADR itself.

**Rationale.** Locking the MVP scope at the Matcher dispatch layer rather than at the spec layer keeps the scope decision implementational, where it belongs. The spec describes the observable contract of `check_applicability`; the Matcher implementation enforces the MVP restriction; expanding scope post-MVP does not modify either. This mirrors the design pattern of ADR-0005 Decision 7 (internal reasoning strategy of `check_applicability` is implementation, not contract) applied to a different dimension of the same component.

**Consequences.** No structural blocker exists for post-MVP scope expansion. The expansion criterion is empirical: it depends on whether benchmark performance on `collection` saturates sufficiently to justify the operational complexity of evaluating a second operation, and on whether a concrete client need (e.g., a healthcare client requiring `international_transfer` evaluation under LGPD Art. 33) materializes to drive scope. Recorded as future work, not as a missing dependency.

## Aggregated consequences

**Positive.**

- The benchmark corpus is dense per evaluated operation; statistical claims about coverage and false-positive rates are defensible.
- Audit-trail integrity is preserved: out-of-scope operations surface as explicit `not_applicable` findings with a self-documenting reason, not silently dropped from the Report.
- The Matcher architecture is preserved for scope expansion without rework.

**Negative.**

- The Report carries a `not_applicable` finding for every non-`collection` candidate the Detector emits. For repositories with high non-`collection` density (e.g., data-pipeline code that mostly performs transformations and transfers), the Report grows with content that is informationally weak — the reader learns only that the operation was outside scope. Mitigated by the self-documenting reason string and by the Report being structured JSON, allowing consumers to filter by verdict.
- The architectural claim "framework-agnostic via data substitution" (ADR-0005 §1, RF-008) combined with "MVP scope is one operation" is rhetorically uncomfortable: a non-LGPD client onboarded post-MVP would need to wait for scope expansion before obtaining clause evaluation on operations central to their jurisdiction (e.g., GDPR Cap. V chapter on transfers). Documented and accepted; first-non-LGPD-client unblocking is post-MVP scope work, not a soundness gap in the MVP itself.

**Migration path.** Not applicable. The system is greenfield; no deployment exists to migrate.

## Companion patches in this PR

- **`docs/REQUIREMENTS.md`** — RF-004 "Refs." line: replace the placeholder `ADR retroativo sobre escopo de operações na v0.1.0 (a redigir, registrado em session-handoff.md)` with a direct citation to `ADR-0007`. RF-004 description and criteria example tokens (`use`, `transfer`, `storage`, `deletion`) corrected to canonical vocabulary tokens (`use`, `storage`, `disclosure_by_transmission`, `erasure`) — companion of ADR-0006 Decision 2.
