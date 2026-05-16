# ADR-0007 — MVP scope: evaluation limited to operation_type collection

**Status.** Accepted (session #18, deferred from session #17 after PR-23 cleanup).
**Date.** 2026-05-16
**Supersedes.** Nothing.
**Superseded by.** Nothing.
**Related.** ADR-0001 (immutable domain rule on stable clause citation that constrains the `not_applicable` contract), ADR-0005 (Decision 4 — `policy://vocabularies` as the canonical surface for the operation vocabulary; Decision 7 — `check_applicability` mechanism deferred to Phase 2), ADR-0006 (English snake_case convention for jurisdictional-vocabulary tokens, which fixes `collection` as the canonical token), ADR-0008 (task decomposition that consumes the MVP scope boundary defined here).

## Context

The Policy describes obligations across the full lifecycle of personal-data processing: collection, recording, storage, use, sharing, transfer, anonymization, deletion, and so on. The LGPD operation vocabulary published by the Policy (`policy/vocabularies/LGPD/operation.yaml` per ADR-0005 Decision 4, English snake_case tokens per ADR-0006 Decision 2) enumerates 22 such operations. A Policy authored to cover all of them is the eventual target; what the MVP evaluates is a strict subset.

The system as designed for TCC2 — Detector + Classifier + Matcher + `policy-reader` + `semgrep-runner` — is a static-analysis instrument: it reads pull-request diffs and reasons about constructs the diff contains. The diffs the system can read carry one class of operation reliably: the *capture* of personal data. Function parameters receiving named personal data, form-field definitions, instrumentation events (click, page view, cadastro/sign-up), and structured payloads of customer-data platforms (CDP/AEP-style schemas) are all constructs visible in a diff. These constructs map onto a single operation token: `collection`.

The other 21 operations in `operation.yaml` — `use`, `storage`, `disclosure_by_transmission`, `erasure`, `international_transfer`, and the rest — generally do not appear in the same kind of diff evidence. `storage` is determined by infrastructure declarations, retention policies, and database lifecycle configuration that live outside application code. `use` is downstream business logic whose conformance depends on operational context the diff does not encode. `international_transfer` typically surfaces in deployment topology and vendor contracts, not in pull-request snippets. Evaluating these operations responsibly would require evidence sources the MVP does not consume.

This boundary needs to be made explicit, defensible, and operationally stable before Phase 2 implementation begins. RF-004 of `docs/REQUIREMENTS.md` already encodes the boundary at the requirement level (the system evaluates `operation_type: collection` and returns `not_applicable` for the rest); this ADR registers the rationale for the boundary and the contract that preserves expansion.

Session #17 produced an earlier draft of this ADR with a different primary rationale (statistical signal density per operation derived from the synthetic-benchmark size in §4.f of the proposal). That rationale was identified as a post-hoc justification disconnected from the actual project motivation and was withdrawn. This ADR replaces that draft.

## Decision

### 1. The MVP evaluates conformance only for candidates with `operation_type: collection`

The evaluation pipeline (Matcher consuming `check_applicability`) emits a substantive verdict — `compliant`, `violation_candidate`, or `indeterminate` — only when the candidate's `operation_type` is `collection`. For any other value drawn from the operation vocabulary published by the loaded Policy, the pipeline emits `not_applicable` with a reason referencing the MVP-scope boundary.

**Rationale.** The system is an instrument for the *data-collection tagging map*: the artifact a product or analytics engineering team maintains when documenting which events, form fields, and instrumentation points capture personal data, under which categories, with which declared legal basis. The system reads the same surface that the tagging map describes — pull-request diffs introducing or modifying capture points — and produces verdicts about the conformance of those capture points to a versioned Policy. Restricting MVP evaluation to `operation_type: collection` is not a choice about which operation is *most important* to audit; it is the operation the system is *constitutively able* to audit given the evidence it reads. Other operations require other evidence sources (infrastructure declarations, retention configuration, deployment topology, vendor agreements) that the MVP architecture does not consume. The boundary is a property of what the system is, not a deferral of effort.

This also aligns the MVP with the contribution claim of the work. The thesis defends the viability of the Policy as a first-class declarative artifact decoupled from the mechanism that interprets it. The MVP demonstrates that viability for the operation the chosen mechanism can interpret. Expansion to additional operations is a question of adding mechanisms (additional evidence sources, additional subagents, possibly a runtime telemetry plane), not of relaxing this scope decision.

**Consequences.** RF-004 evaluates exactly one operation token; gate criteria for Milestone A exercise the four verdicts of `check_applicability` against candidates carrying `operation_type: collection`. PR comments and Reports referencing a `not_applicable` verdict carry an explanation tying the verdict to the MVP scope, so reviewers reading the comment understand the system is not silently ignoring the candidate. The Policy author retains full authority over which clauses exist in the Policy (see Decision 2); the MVP simply does not evaluate the subset of clauses keyed to non-`collection` operations.

### 2. The Policy retains clauses governing non-collection operations

Clauses in `policy/clauses/` are authored according to the Policy author's reading of the legal framework, not according to the MVP evaluation scope. A clause governing `use`, `storage`, `disclosure_by_transmission`, `erasure`, or any other operation in the published vocabulary remains a first-class member of the Policy. The MVP simply does not invoke `check_applicability` for candidates whose `operation_type` is outside the scope of Decision 1, and the Matcher does not query the Policy for clauses on those operations.

**Rationale.** Two distinct scopes are at play: (a) the scope of the *Policy* as a versioned legal artifact, which the Policy author governs and which is intended to be defensible against the full LGPD obligation surface; and (b) the scope of *MVP evaluation*, which the present ADR governs and which is bounded by the evidence the system can read. Conflating the two would impose an artificial ceiling on the Policy that has nothing to do with its authorial integrity and that would have to be undone before any future evaluation expansion. Keeping them separate preserves the Policy as a stable target and lets the evaluation perimeter grow under it.

**Consequences.** The Policy can encode obligations the MVP does not yet evaluate without producing inconsistency or operational confusion. Reviewing the Policy as a legal artifact (clauses, rationale, citations to law articles) is independent of running the MVP. Phase 2 work on additional evidence sources or additional subagents can target an already-codified Policy surface rather than competing for authorial time with Phase 1 evaluation.

### 3. `check_applicability` returns `not_applicable` for out-of-scope candidates with structured reason

When a candidate's `operation_type` falls outside the operations the MVP evaluates, `check_applicability` returns `verdict: not_applicable` together with a `reason` field whose text identifies the MVP-scope boundary and the version of the system at which the boundary applies. The exact wording of the reason is implementation-level and may be calibrated by the Matcher prompt or by `policy-reader` defaults; what this ADR fixes is the *contract shape* — verdict `not_applicable`, structured reason explicitly attributing the verdict to MVP scope, not to a Policy gap or to evidence shortage.

The contract supports expansion without breakage. When a future version of the system adds an evidence source enabling evaluation of, say, `storage`, the change is internal to the Matcher and to whatever subagent ingests that evidence; the `check_applicability` interface continues to accept the same `structured_context` and the same vocabulary tokens. Candidates that previously returned `not_applicable` with the MVP-scope reason can begin returning substantive verdicts. Clients reading the verdict field continue to read the same enum.

**Rationale.** ADR-0005 Decision 7 deferred the *internal mechanism* of `check_applicability` to Phase 2 while locking the *interface*. This decision extends that pattern: the MVP-scope boundary is encoded in the values the interface can return (`not_applicable` for out-of-scope), not in the interface shape itself. Any contractual ceremony required to expand the system later is therefore minimal.

The reason field is structured rather than free-form because Reports surface it to human reviewers and CI consumers; a recognizable marker for "this candidate was skipped due to MVP scope, not due to a Policy or evidence gap" prevents reviewers from interpreting `not_applicable` as a silent failure or as a Policy omission.

**Consequences.** Tests for `check_applicability` cover the `not_applicable` path explicitly for at least one non-`collection` operation token, verifying that the reason field is populated with an MVP-scope marker. Reports rendering findings whose verdict is `not_applicable` distinguish the MVP-scope case from other `not_applicable` cases (e.g., a clause that genuinely does not govern the context) so that operational readers receive useful signal.

## Aggregated consequences

**Positive.**

- The MVP claim is honest: the system audits what its evidence can support, and the boundary is documented at the requirement level (RF-004) and the architectural level (this ADR).
- The Policy retains authorial flexibility and can encode the full LGPD obligation surface without waiting for the evaluation perimeter to catch up.
- Expansion is mechanism-side, not interface-side: adding evidence sources or subagents in future work does not require renegotiating `check_applicability` consumers or Report consumers.
- The defense of the scope decision in front of an evaluator (TCC2 banca examinadora, peer reviewers) rests on the structural property of the system rather than on contingent quantitative arguments that can be challenged.

**Negative.**

- A reader of the system's first reports may need the boundary explained, particularly when a pull request contains candidates the system marks `not_applicable` even though those candidates clearly involve personal data. Mitigated by Decision 3's structured reason and by user-facing documentation (forthcoming as part of the Reporter spec, Phase 2).
- A clause governing, e.g., `storage` lives in the Policy without ever being exercised by the MVP. This is acceptable per Decision 2 but creates an asymmetry between "Policy clauses exist" and "Policy clauses are tested by the system's behavior". Documented; not corrected at MVP scope.
- The boundary is defined by reference to evidence sources, which are themselves implicit in the current architecture rather than explicitly enumerated in a single document. Future ADRs (e.g., when adding a runtime-telemetry source) will need to articulate which operations newly become evaluable; this ADR does not pre-empt them.

**Migration path.** Not applicable: the boundary is current state, materialized in RF-004 and consumed by the Phase 2 implementation now beginning. Future expansion (an operation moves from `not_applicable` to substantive verdict) is governed by a new ADR amending the present scope, not by silently relaxing Decision 1.
