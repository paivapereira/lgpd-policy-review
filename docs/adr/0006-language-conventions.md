# ADR-0006 — Language conventions: Portuguese technical docs, English jurisdictional-vocabulary tokens

**Status.** Accepted (retrospective — conventions inherited from sessions #04–#11 and #16, formalized here in session #17 after PR #22 surfaced concrete drift).
**Date.** 2026-05-15
**Supersedes.** Nothing.
**Superseded by.** Nothing.
**Related.** ADR-0001 (workflow conventions — fixed the foundational language rule for code, commits, CLAUDE.md, ADRs, Policy content, and user-facing outputs; this ADR formalizes two derived conventions left implicit there), ADR-0005 (multi-client policy architecture — Decision 3 introduced the four jurisdictional vocabulary files whose token language is governed here).

## Context

ADR-0001 and `CLAUDE.md` ("Languages" section) declare the foundational language rule of the project:

- Code, comments, identifiers, docstrings, commit messages, ADRs, `CLAUDE.md` → English.
- Policy content under `policy/` (clause text, rationale) → Brazilian Portuguese (legal fidelity to LGPD).
- System outputs to end users (Report findings rendered for humans, PR comments, escalation messages) → Brazilian Portuguese.

Two derived conventions emerged across sessions #04 through #11 and crystallized in session #16 with the multi-client architecture, but were never written down:

1. **Technical documentation in Portuguese.** Specs (`docs/specs/<component>/canonical.md` and `compact.md`), `docs/architecture-overview.md`, `docs/DESIGN.md`, `docs/REQUIREMENTS.md`, `policy/SCHEMA.md`, `docs/process/learning-log.md`, `docs/process/session-handoff.md` — the operational documentation layer that explains the system to the author and to future maintainers — are written in Portuguese. The convention was inherited from the author's working language and never declared. Tracked as a debt in [`docs/process/learning-log.md:1518`](docs/process/learning-log.md#L1518) since session #16.

2. **Jurisdictional-vocabulary tokens in English.** The four YAML files at `policy/vocabularies/<framework>/` (`operation.yaml`, `lawful_basis.yaml`, `control.yaml`, `out_of_scope.yaml`) declare token values via the `name:` field in English snake_case (e.g., `collection`, `consent`, `consent_required`, `unmodeled_special_category`). The Portuguese human-readable label lives in the `description:` field of each entry. No document declares this; the convention was applied implicitly when the vocabularies were extracted from `SCHEMA.md` §9 in PR #22.

The PR #22 audit caught a concrete drift caused by absence of convention 2: `REQUIREMENTS.md` RF-004 originally declared `operation_type: coleta` while `operation.yaml` declared the canonical token `collection`. The drift was patched in PR #22 itself, but with examples (`transfer`, `deletion`) that turn out not to be canonical tokens either (the real LGPD vocabulary has 22 values including `disclosure_by_transmission`, `international_transfer`, `erasure`, `destruction` — see `policy/vocabularies/LGPD/operation.yaml`). The deeper drift is corrected in this PR's companion patches; the root cause — absence of an ADR declaring the convention — is resolved by this document.

## Decision

### 1. Technical documentation (non-ADR) is authored in Portuguese

The following document classes are authored in Portuguese:

- `docs/architecture-overview.md`
- `docs/DESIGN.md`
- `docs/REQUIREMENTS.md`
- `docs/process/learning-log.md`
- `docs/process/session-handoff.md`
- `docs/specs/<component>/canonical.md` and `compact.md`
- `policy/SCHEMA.md`

The list enumerates the technical-doc classes currently authored in Portuguese. New documents in the same operational category default to Portuguese without requiring an ADR amendment; the convention is descriptive of practice, not a gate.

Within these documents, citations of technical identifiers remain in their canonical form regardless of the surrounding prose language: `clause_id`, `policy_schema_version`, `legal_framework`, vocabulary tokens (`collection`, `consent_required`), error codes, and analogous machine-readable strings are quoted verbatim.

**Rationale.** Portuguese is the author's working language and the language of the LGPD source material the technical documentation reasons about. Forcing English on this layer would add cognitive load without serving any downstream consumer: ADRs already cover the externally-citable decision surface, code covers machine-readable artifacts, and these documents sit between — operational reading for the author at implementation time and for future maintainers in the same linguistic context. Translation overhead is real and accumulates across hundreds of pages of session logs and specs.

**Consequences.** Spec readability requires Portuguese; collaborators without Portuguese rely on machine translation. The cost is documented and accepted as bounded for the TCC scope (single author, Portuguese-speaking thesis committee). ADRs remain English to preserve external citability and Anglophone reviewer accessibility.

### 2. Jurisdictional-vocabulary tokens are English snake_case

Token values declared via the `name:` field in the four jurisdictional vocabulary YAMLs under `policy/vocabularies/<framework>/` are English snake_case. The convention applies to:

- `operation.yaml` — 22 values in the LGPD vocabulary, all English (`collection`, `recording`, `storage`, `use`, `disclosure_by_transmission`, `erasure`, `international_transfer`, etc.).
- `lawful_basis.yaml` — 18 values across personal-data and sensitive-data categories, all English (`consent`, `legitimate_interests`, `contract_performance`, `explicit_consent`, etc.).
- `control.yaml` — 2 MVP values, all English (`consent_required`, `anonymization_required`).
- `out_of_scope.yaml` — 7 values, all English (`unmodeled_special_category`, `not_personal_data_per_definition`, etc.).

The Portuguese human-readable label of each token lives in the `description:` field of the same entry. Reports and PR comments rendering tokens to end users translate through `description`, never by aliasing the key.

The convention scope is restricted to the four jurisdictional vocabulary files under `policy/vocabularies/<framework>/`. POL-000 lives in a separate architectural layer — it is a `definitional` clause under `policy/clauses/`, not a vocabulary file, per ADR-0005 Decision 3. POL-000 token form (`dados_de_identificacao`, `dados_de_contato`, etc.) follows the Portuguese convention that governs Policy clause content under ADR-0001 (legal fidelity to LGPD Art. 5º). The two surfaces are governed by different rules because they belong to different architectural layers, not because POL-000 is an exception to the present rule.

**Rationale.** The "code in English" principle of ADR-0001 applies to anything the Matcher, Classifier, or `policy-reader` compare with `==` or `in`. Jurisdictional-vocabulary tokens are compared in code paths (`if candidate.operation_type == "collection": ...`) and indexed across multilingual frameworks: a future `policy/vocabularies/GDPR/operation.yaml` must share token shape with the LGPD file, not vary by language. POL-000, by contrast, is referenced from clauses that themselves describe Brazilian-specific categorizations, is not cross-framework, and is authored under the same legal-fidelity rule that governs Policy clause text.

**Consequences.** GDPR, CCPA, or other future jurisdictional vocabularies can reuse `collection`, `consent`, `legitimate_interests` directly as canonical tokens. The Matcher reads `policy://vocabularies` and dispatches by token without language-aware preprocessing. The `description:` field per vocabulary entry carries the per-jurisdiction human-readable label for Reports. Adding a non-Brazilian framework introduces no new top-level token language.

### 3. Scope summary table

Quick reference. Updates to the table require ADR amendment.

| Surface                                                                       | Language   |
| ----------------------------------------------------------------------------- | ---------- |
| Code, identifiers, docstrings, type hints                                     | English    |
| `CLAUDE.md`, ADRs (`docs/adr/`)                                               | English    |
| Commit messages, PR titles, branch names                                      | English    |
| Technical docs (specs, architecture, DESIGN, REQUIREMENTS, SCHEMA, learning-log, handoff) | Portuguese |
| Policy clause content (`policy/clauses/`, rationale Markdown)                 | Portuguese |
| Jurisdictional-vocabulary tokens (`operation.yaml`, `lawful_basis.yaml`, `control.yaml`, `out_of_scope.yaml` `name:` field) | English    |
| POL-000 data category vocabulary                                              | Portuguese |
| Vocabulary `description:` field (any of the four jurisdictional YAMLs)        | Portuguese |
| Report findings rendered for humans, PR comments                              | Portuguese |
| Error `errorCode` (machine identifiers per ADR-0002 §2)                       | English    |
| Error `message` (human-readable per ADR-0002 §2)                              | Portuguese |

## Aggregated consequences

**Positive.**

- Cross-framework consistency at the token layer: future jurisdictional vocabularies reuse token shape directly without translation.
- Author cognitive load is bounded: Portuguese for prose authoring, English only at code, ADR, and token boundaries.
- Drift detection becomes mechanical: any English token in a docs paragraph (other than verbatim citation) or any Portuguese token in a jurisdictional vocabulary `name:` field is structurally wrong and detectable by grep.

**Negative.**

- Anglophone reviewers cannot read specs and architecture docs directly. Mitigated by ADRs being English (the externally-citable decision layer) and by reports/outputs being Portuguese (the consumer-facing layer) — together, the English ADR set plus machine translation of the Portuguese specs is sufficient for external review of architectural soundness.
- The boundary between the four jurisdictional vocabulary files (governed by convention 2) and Policy clause content (governed by ADR-0001 legal-fidelity rule) is judgemental rather than mechanical. POL-000 is the current example of clause-as-vocabulary: a definitional clause that functions as a closed vocabulary of personal-data categories. Future definitional clauses or jurisdictional vocabularies may surface edge cases where the architectural layer is not obvious. Documented as a layer-allocation rationale rather than an absolute rule; if a future framework expansion surfaces such an edge case, this ADR is the place to amend.

**Migration path.** Not applicable. The conventions are descriptive of current state across the codebase post-PR #22. The companion patches in this PR are the only operational changes associated with the ADR; future drift is prevented by the rule existing in citable form.

## Companion patches in this PR

- **`docs/specs/policy-reader/canonical.md` and `compact.md`** — `"operation": "collect"` → `"operation": "collection"` in the `check_applicability` `compliant` example payload. Internal spec inconsistency: the vocabulary declares `collection`, the example used `collect`. Resolved before this ADR was authored (companion to the convention being documented, not derived from it).
- **`docs/REQUIREMENTS.md`** — RF-004 example tokens corrected from `use`, `transfer`, `storage`, `deletion` (where `transfer` and `deletion` are not canonical tokens in `operation.yaml`) to `use`, `storage`, `disclosure_by_transmission`, `erasure` (all canonical). RF-004 description rephrased identically. The change is editorial alignment with the operational vocabulary now governed by this ADR.
