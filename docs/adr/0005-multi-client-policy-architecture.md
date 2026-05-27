# ADR-0005 — Architecture for multi-client policy support: vocabularies as data, LGPD as instance

**Status.** Accepted, session #16.
**Date.** 2026-05-14
**Supersedes.** Nothing.
**Superseded by.** Nothing.
**Related.** ADR-0002 (MCP conventions and deferments — this ADR refines Decision 7 with the `policy://vocabularies` resource and registers framework-related deferments not covered by Part 2 of ADR-0002).

## Amendment scope (2026-05-22)

Decisions 1 and 2 are amended in-place to align with the canonical clause-envelope field name. The original formulation (2026-05-14, session #16) referred to a clause envelope field `article_source` in Decision 1 ("(`clause_id`, `article_source`, ...)") and described `accepted_law_identifiers` in Decision 2 as governing "statute references admissible in clause `article_source` fields". The field name `article_source` was a residue of a pre-#16 envelope sketch that did not survive into the canonical schema: `policy/SCHEMA.md` §5.1, materialized YAMLs (`policy/clauses/POL-000.yaml`, fixtures POL-001..POL-004), and both `_format_law_reference` (5 positional args, ADR-0009) and `_format_stat_ref` (Pydantic-aware wrapper) in `src/mcp_servers/policy_reader/tools.py` all use `statutory_reference` as the canonical field name, with hierarchical entries (`lei`/`artigo`/`paragrafo`/`inciso`/`alinea`).

Amendment landed in-place rather than as a successor ADR because the substantive decisions of this ADR (vocabulary layering, multi-client architecture, `legal_framework` axis) are intact; only field-name terminology is corrected. Pattern follows ADR-0001 D2 amendment (2026-05-21) and D3 amendment (2026-05-22).

## Context

The architecture declared in `docs/process/proposta-tcc2.md` §6 is explicitly
multi-client: the system targets clients across jurisdictions (LGPD as
exemplary MVP, GDPR as the natural next instance), with the Policy
artifact under `policy/` customized per client. The implementation
inherited from session #14 (policy-reader skeleton + early mitigations)
still treated LGPD as a system-level invariant — vocabularies were
embedded in `policy/SCHEMA.md` §9 appendices as if they belonged to
the schema rather than to a specific jurisdictional instance.

This ADR formalizes the separation already implicit in the proposta
and materializes it across the documentation layer in advance of the
Fase 2 implementation work. The decisions below were taken in session
#15 (Chat) under the "Defaults arquiteturais consolidados" header of
`docs/process/session-handoff.md`; this ADR lifts them out of the handoff
(operational document) into the ADR record (decision document).

This ADR does not change the schema versioning rule of ADR-0002
Decision 6 nor the deferment C of ADR-0002 (single coexisting
`policy_schema_version` per instance). Those rules govern the
*structure* of the Policy artifact and remain in force. This ADR
governs *jurisdictional content* loaded into that structure: a single
instance serves a single Policy under a single `legal_framework`,
immutable during the server session. Multi-framework support is a
data-substitution exercise (replace Policy + vocabularies, restart),
not a code-modification one.

## Decisions at a glance

| # | Decision | Read when |
|---|----------|-----------|
| 1 | SCHEMA.md layered: structural universal + jurisdictional per-client | Authoring or modifying `policy/SCHEMA.md`; deciding where a new vocabulary belongs |
| 2 | `legal_framework` is a top-level header field, immutable during the server session | Implementing `policy-reader` startup; reasoning about multi-framework support |
| 3 | Four canonical vocabulary files per framework; POL-000 universal | Authoring vocabularies under `policy/vocabularies/<framework>/`; deciding whether a new vocabulary is universal (POL-000-like) or per-framework |
| 4 | `policy://vocabularies` is a shared resource (Matcher + Classifier); tools remain Matcher-exclusive | Implementing Classifier or Matcher; designing subagent `allowed-tools` |
| 5 | Provenance trinque: jurisdiction is non-optional in verdicts | Implementing `check_applicability`; understanding why every verdict carries `legal_framework`; consuming Matcher output downstream |
| 6 | Clause succession is intra-Policy, not cross-framework | Implementing `successors` lookup; reasoning about Policy evolution |
| 7 | Internal reasoning strategy of `check_applicability` is implementation, not contract | Implementing the Matcher logic in Phase 2; deciding between data-driven and hybrid strategies |
| 8 | `semgrep-runner` rule set is bundled in MVP; per-client deferred | Implementing `semgrep-runner` rule loading; planning Phase 2+ multi-client work |

## Decision

### 1. SCHEMA.md layered: structural universal + jurisdictional per-client

`policy/SCHEMA.md` is refactored into two declared layers:

- **Structural layer.** Universal across all clients and jurisdictions.
  Defines the YAML shape of `policy.yaml`, the clause envelope
  (`clause_id`, `statutory_reference`, `status`, `requirements`,
  `exceptions`, and the `tombstone` block — containing `successors`,
  `effective_until`, `deprecation_reason` — when `status: deprecated`),
  the closed structural vocabularies (`status` enum: `active`,
  `deprecated`), the resource and tool contracts of the
  `policy-reader`, and the canonical-vs-derivation correspondence
  rules between Markdown rationale and YAML structure.
- **Jurisdictional layer.** Per-client. The closed vocabularies whose
  values depend on the legal framework — `operation`, `lawful_basis`,
  `control`, `out_of_scope.reason` — live as data files outside
  `SCHEMA.md` itself, under `policy/vocabularies/<framework>/`.

`SCHEMA.md` §7 (vocabulários fechados) gains a `Natureza` column
distinguishing `estrutural` from `jurisdicional`, with a normative note
that jurisdictional values are not source of truth in §9 appendices
but in the YAML files of `policy/vocabularies/<framework>/`. The §9
appendices are preserved as human-readable reference; the canonical
machine-readable source moves to the YAML files.

**Rationale.** The proposta-tcc2 thesis hinges on Policy being a
first-class artifact decoupled from the system that consumes it.
Embedding LGPD enums inside `SCHEMA.md` made that decoupling
rhetorical rather than structural: a GDPR client would have required
editing the schema document, not just replacing data. Externalizing
jurisdictional values converts the decoupling from claim to property.

**Consequences.** `SCHEMA.md` becomes a stable contract; jurisdictional
content evolves independently. The four YAML files become the unit of
audit for legal-framework alignment, separable from schema review.

### 2. `legal_framework` as top-level Policy header field

The `policy.yaml` header carries `legal_framework` as a top-level
required field, single value (not a list), immutable during the
server session. The existing field `accepted_law_identifiers` is
preserved as a list — it enumerates statutes citable *within* the
declared jurisdiction (e.g., `[LGPD, Marco_Civil]` for a Brazilian
Policy under `legal_framework: LGPD`).

The distinction is deliberate: `legal_framework` declares the
jurisdiction (single, governs which `policy/vocabularies/<framework>/`
files are loaded); `accepted_law_identifiers` declares the lexicon of
statute references admissible in clause `statutory_reference` fields
within that jurisdiction (plural, governs validation).

**Rationale.** A Policy operates under one legal framework at a time.
Citing multiple statutes within that framework is normal practice
(LGPD plus the Marco Civil; GDPR plus the e-Privacy Directive); citing
across frameworks is not — those would be different Policies. The
field separation captures this asymmetry without overloading either
field.

**Consequences.** The handshake protocol of `policy://schema-version`
(see ADR-0002 Decision 7 and the policy-reader spec §3.2) expands
from three to four identity axes: `policy_schema_version`,
`policy_version`, `legal_framework`, alongside `accepted_law_identifiers`
returned for caller validation.

### 3. Four canonical vocabulary files per framework; POL-000 universal

Each `policy/vocabularies/<framework>/` directory contains exactly
four files:

- `operation.yaml` — the data processing operations vocabulary
  (LGPD Art. 5º X ∪ GDPR Art. 4(2) in the LGPD MVP; equivalent
  enumerations for other frameworks).
- `lawful_basis.yaml` — the legal bases for processing (LGPD Art. 7º
  for personal data, Art. 11 for sensitive data; GDPR Art. 6(1) and
  Art. 9(2) for equivalent classes).
- `control.yaml` — the prescribed controls vocabulary (`consent_required`,
  `anonymization_required` in the MVP; framework-specific extensions
  beyond MVP).
- `out_of_scope.yaml` — the reasons a clause may declare itself
  out-of-scope for static analysis.

`POL-000` (the foundational categorization of personal data
categories — identifiers, contact data, sensitive data, etc.) is
**not** in this set. It remains a universal semantic catalog under
`policy/rationale/POL-000.md` and the structural layer of `SCHEMA.md`.
Its substantive content may differ per client (a healthcare client
may expand the sensitive category enumeration) but its structural
role — defining the categories any Policy references — is universal.

**Rationale.** Four is the empirical count of closed vocabularies in
the current `SCHEMA.md` §9 whose values are statute-bound. POL-000 is
statute-informed but not statute-bound — both LGPD and GDPR
recognize the same broad categories of personal data with different
boundaries; the categorization itself is semantic, not jurisdictional.
Promoting POL-000 to jurisdictional would over-fragment the universal
content.

**Consequences.** Adding a new framework (GDPR, CCPA) is a four-file
exercise plus a Policy rewrite under `policy/`. No structural change
required.

### 4. New resource `policy://vocabularies` on `policy-reader`

`policy-reader` exposes a new resource at URI `policy://vocabularies`
(per ADR-0002 Decision 7 scheme convention). The resource is read-only,
idempotent, returning a structured object aggregating the four
jurisdictional vocabularies loaded at server startup from
`policy/vocabularies/<framework>/*.yaml`. The framework is derived
from `legal_framework` in `policy.yaml` and is invariant for the
session.

The resource is consumed by **both** Classifier and Matcher subagents.
Tools of `policy-reader` (`get_clause`, `find_clauses_by_law_article`,
`check_applicability`) remain exclusive to the Matcher.

**Rationale.** The Classifier needs the closed lexicon of operations
and lawful bases to produce a `structured_context` payload — containing
`operation_type`, `data_categories`, `declared_legal_basis`,
`declared_transformations` — that the Matcher can route against
clauses — a lexical-context need, not an action need. Resources
expose lexical context idempotently; tools expose actions with
semantics. The distinction maps directly to the Resource vs Tool
principle of the MCP specification: app-controlled context for
resources, model-controlled invocation for tools.

**Consequences.** The `architecture-overview.md` §5.7 capability
matrix splits the `policy-reader` row into two: tools (Matcher only),
resource `policy://vocabularies` (Classifier and Matcher). The
spec_version of `policy-reader` bumps minor (per ADR-0002 Decision 6:
new resource that does not alter existing ones).

### 5. Provenance trinque: jurisdiction is non-optional in verdicts

Every successful return of `check_applicability` and every Report
emitted by the Reporter carries three provenance fields as a unit:

- `policy_schema_version` — structural version of the schema in force.
- `policy_version` — content version of the loaded Policy.
- `legal_framework` — jurisdictional instance under which the verdict
  was produced.

The three are returned together; omitting any one is a contract
violation. The Reporter places `legal_framework` as a top-level
Report field alongside `report_id`, `policy_schema_version`, and
`policy_version`.

**Rationale.** A verdict produced under LGPD against a system later
audited under GDPR is not the same verdict; the audit trail must
expose under which framework the reasoning was performed. Reducing
provenance to schema+content versions, as the pre-#15 contract did,
implicitly assumed a single framework — a flag that becomes incorrect
the moment a second client onboards.

**Consequences.** Audit-trail integrity across multi-jurisdiction
deployments is structural rather than reliant on deployment metadata.
Reports are self-describing for jurisdictional context.

### 6. Clause succession is intra-Policy, not cross-framework

The clause succession relation, materialized by the `successors` field
within the `tombstone` block of a deprecated clause, operates strictly
within a single Policy under a single `legal_framework`. The
`successors` array carries `clause_id` references that resolve only
within the loaded Policy. Cross-framework succession (e.g., a GDPR
clause superseding an LGPD clause) is not a supported relation and is
explicitly out of scope.

**Rationale.** Succession encodes Policy evolution within a juridical
regime, not migration between regimes. Migrating from LGPD to GDPR is
a new Policy authoring exercise, not a chain of `successors`
references; treating it as the latter would create misleading audit
chains across incompatible legal foundations.

**Consequences.** The `policy-reader` spec declares this in §7.1
(non-objectives). No additional mechanism is required to enforce it
since `successors` resolves clause IDs within the single loaded Policy
and has no cross-Policy lookup path.

### 7. Internal reasoning strategy of `check_applicability` is implementation, not contract

The spec of `policy-reader` declares only the observable contract of
`check_applicability`: input shape, the four verdict variants
(`compliant`, `violation_candidate`, `indeterminate`, `not_applicable`),
the trinque provenance fields (Decision 5), and the structured payload
of each variant. The internal reasoning mechanism by which the tool
arrives at a verdict — purely data-driven dispatch over loaded
vocabularies and clauses, or a hybrid combining data dispatch with
inferential steps — is **not** prescribed by this ADR or by the spec.

That decision is deferred to Fase 2 implementation, where empirical
behavior of candidate strategies against the MVP test corpus will
inform the choice.

**Rationale.** Separating observable contract from internal strategy
preserves substitutability of the component. A future migration from
data-driven to hybrid (or vice versa) is an implementation change
that should not require contract revision — the spec, the ADR, and
the downstream consumers (Matcher, Reporter) must remain stable
across that migration. Locking the strategy at the ADR layer would
prematurely commit the architecture to a specific solution shape
before the empirical evidence justifying it exists.

**Consequences.** The policy-reader spec §4.3 documents the
observable contract of `check_applicability` exhaustively but
declares no reasoning-strategy invariant. The Fase 2 implementation
is free to evolve the strategy across iterations without ADR ceremony,
provided the contract holds.

### 8. `semgrep-runner` rule set scope: bundled in MVP, per-client deferred

The `semgrep-runner` MCP server bundles its rule set with the project
in the MVP. The rules in `mcp_servers/semgrep_runner/rules/` (or
equivalent path) — including Brazilian-specific recognizers for CPF,
CNPJ, CNH, and related identifiers — are version-controlled alongside
the system source code, not under `policy/`.

Per-client rule sets — where a client could supply its own Semgrep
rules under `policy/<client>/semgrep_rules/` or equivalent path — are
deferred until a concrete client outside the LGPD-Brazilian scope
materializes with documented detection requirements not covered by
the bundled set.

**Rationale.** Unlike jurisdictional vocabularies (Decision 3), which
encode statute-bound categories whose values depend on the legal
framework, Semgrep rules encode syntactic detection patterns whose
authorship is arguably project-level expertise rather than
client-level customization. Forcing client authorship of detection
rules without a documented need would shift expert work onto the
wrong audience. Deferring the decision keeps both options open: if a
future client demonstrably needs custom rules, the per-client model
can be adopted then with full information; if no client materializes
that need, the simpler bundled model survives.

**Consequences.** The `semgrep-runner` spec §7.1 records this
deferment with revisit criterion. Adding a per-client rule set in the
future is an additive change (new path resolved per client) requiring
no contract revision on `scan_diff`.

## Aggregated consequences

**Positive.**

- Onboarding a non-LGPD client (e.g., GDPR) is a data-substitution
  exercise: replace `policy/`, replace `policy/vocabularies/<framework>/`,
  declare `legal_framework: GDPR` in the header, restart. No code
  changes in `policy-reader`, no changes in subagent definitions, no
  changes in CI/CD wiring.
- The proposta-tcc2 §6 architectural claim ("framework-agnostic
  system, framework-specific Policy") becomes structurally honest
  rather than rhetorical.
- The Resource vs Tool MCP principle is exercised in a textbook case
  with directly observable rationale: `policy://vocabularies` is
  shared context; `get_clause` / `find_clauses_by_law_article` /
  `check_applicability` are directed queries with action semantics.
- Multi-tenant architectural integrity is established at the
  documentation layer before implementation pressure can erode it.

**Negative.**

- Maintenance overhead: each new framework requires four YAML files
  authored with juridical accuracy. The MVP carries only LGPD; the
  cost is theoretical until a second client materializes.
- Partial loss of static type safety on jurisdictional fields: values
  of `operation`, `lawful_basis`, `control`, and `out_of_scope.reason`
  are no longer enum-checkable from `SCHEMA.md` alone — they are
  validated at runtime against the loaded YAML files. Mitigated by
  startup-time validation in the `policy-reader` (a Policy citing a
  value not in the loaded vocabulary fails fast at load).
- **Privilege boundary relaxation on `policy-reader`.** The pre-#15
  design held a strict boundary: "only Matcher consults the Policy."
  This ADR relaxes it to "only Matcher consults the *tools* of the
  Policy; *resources* are shareable." The relaxation is defensible
  under the Resource vs Tool principle (resources are idempotent,
  read-only, model-passive context — they expose no decisional
  capability) but it is a relaxation of minimal-privilege scope and
  should be re-examined if a future subagent argues for resource
  access on a similarly thin pretext. The fronteira "Classifier
  describes, Matcher judges" is preserved: the Classifier gains
  lexical context, not the capacity to issue verdicts.

**Migration path.** Not applicable. The system is greenfield; no
deployment exists to migrate. This ADR concretizes the architecture
before the Fase 2 implementation begins.

## Companion patches in this PR

The following patches materialize the decisions above and land on the
same branch (`arch/multi-client-policy-rewrite`) across commits:

- **`docs/architecture-overview.md`** (landed in `2612f99`) — seven
  cirurgical patches: §4.1 Layer 1 marked per-client, §4.2
  `policy-reader` exposes three resources, §5.4 Classifier gains
  `policy://vocabularies` read access, §5.5 Matcher marked
  framework-aware, §5.6 Report carries `legal_framework` top-level,
  §5.7 capability matrix split into tools/resource lines, systemic
  mentions of "LGPD" desreferenced.
- **`policy/SCHEMA.md`** — refactored into structural layer +
  jurisdictional layer; §7 gains `Natureza` column; §10 (Layout
  multi-cliente) added; §9 appendices retain human-readable form with
  pointer to YAML canonical (Commit 3).
- **`policy/vocabularies/LGPD/`** — four YAML files created
  (`operation.yaml`, `lawful_basis.yaml`, `control.yaml`,
  `out_of_scope.yaml`) extracting current §9 content into canonical
  data form (Commit 3).
- **`docs/specs/policy-reader/canonical.md`** — twelve patches applied
  expanding contract to multi-framework: §2.1 three identity axes,
  §3.2 handshake includes `legal_framework`, §3.3 new resource
  `policy://vocabularies` documented, §4.3 `check_applicability`
  returns trinque, §7.1 non-objectives include multi-Policy and
  hot-swap deferments (Commit 4).
- **`docs/specs/policy-reader/compact.md`** — derived from canonical
  preserving paridade on contract surfaces (Commit 4).
- **`docs/specs/semgrep-runner/canonical.md` and `compact.md`** —
  per-client rule set added as explicit deferment in §7.1 (Commit 5).
- **`docs/DESIGN.md`** — new lightweight entrypoint document routing
  implementation reading across the distributed docs (Commit 5.5).
