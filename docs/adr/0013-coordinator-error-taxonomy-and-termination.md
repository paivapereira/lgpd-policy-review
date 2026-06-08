# ADR-0013 — Coordinator error taxonomy and termination contract

**Status.** Proposed — draft assembled in Chat 2026-06-07. **Not ratified.** This ADR is mechanical assembly of decisions already materialized in `src/coordinator/errors.py`, `src/coordinator/models.py`, and the coordinator driver, cross-referenced against the specs that authored them; the normative framing requires the author's ratification before acceptance (per the project's ADR-authoring convention — Code assembles and cross-references, the author decides; same posture as ADR-0012 and ADR-0016).
**Date.** 2026-06-07
**Supersedes.** Nothing.
**Superseded by.** Nothing.
**Related.** ADR-0002 (MCP conventions — the Option B `{errorCode, message, isRetryable, details}` wire envelope this taxonomy consumes and converts into typed exceptions). ADR-0011 D2 (custom-exception-types decision for the git wrappers inside `semgrep-runner` — the sibling precedent at the server layer, distinct module). ADR-0016 (Reporter single-emission guard — one materialized instance of the fail-loud posture generalized in Decision 5). ADR-0012 Deferral B (the consumer-side `legal_framework` jurisdictional gate whose revisit condition was "implementation of `src/coordinator/`"; this ADR closes it — see Companion edits). ADR-0005 (LGPD as the MVP jurisdictional instance). ADR-0007 (MVP collection-only scope — relevant to the `framework_guard` citation correction in Companion edits). ADR-0009 (the runtime-consequence threshold for ADR vs `.claude/rules/` placement, which the decisions below satisfy).

## Context

The coordinator orchestrates the five Branch-B stages (Triager → Detector → Classifier → Matcher → Reporter) as sequential one-shot `query()` calls, threading state stage-to-stage and projecting any halt into a single external union. The typed exception taxonomy that represents, attributes, and projects failure lives in `src/coordinator/errors.py` with the termination union in `src/coordinator/models.py`. The system is fully implemented and tested (`tests/coordinator/test_coordinator_errors.py`, `test_coordinator_models.py`).

The taxonomy was authored under a deferred-formalization marker. `coordinator.md` §5 and `matcher.md` §6.4 both state that the hierarchy formalization "stays ADR-0013 follow-up"; the `errors.py` module docstring repeats it verbatim ("hierarchy formalization stays ADR-0013 follow-up"). The number ADR-0013 was reserved across these loci but never written, so the ADR sequence currently skips from 0012 to 0014. This ADR claims the reserved number and formalizes the set of load-bearing decisions embedded in `errors.py`, not only the narrow sibling-vs-base question of DD-M18.

Scope note. The decisions below all share one subject — how the coordinator represents, attributes, and projects failure — and one consumer pair — the external caller (GitHub Action / exercise script) and the auditor reading the scratchpad. They are consolidated in one ADR for the same reason ADR-0003 consolidated two spec-design meta-decisions: the unit is readable as a whole, and splitting it would fragment a single concern across several documents. Each decision is retrospective (taken during Milestone C, materialized in code); the two Companion edits close loops opened by prior ADRs.

## Decision

### 1. Two orthogonal axes for the coordinator exception taxonomy

The coordinator's typed exceptions are partitioned into two axes that do not share a base:

- **Tool-error family** — base `SubagentToolError(Exception)`, with `DetectorScanFailed` as its only MVP subclass. These represent a domain error of an MCP tool consumed by a subagent (Option B `errorCode` surfaced by deterministic inspection), and carry the tool envelope fields `(tool, error_code, is_retryable, details)` inherited verbatim from ADR-0002 §3.
- **SDK-class + contract exceptions** — `SubagentRefusedTask`, `SubagentValidationFailed`, `SubagentUnresponsive`, `CoordinatorStreamFailure`, `SubagentExecutionError`, `SubagentContractViolation`, `CoordinatorStartupError`, `UnsupportedLegalFramework`, and the Reporter family (`ReportNotEmitted`, `ReporterTurnsExhausted`, `ReporterPermissionDenied`, `MultipleReportEmissions`, `MalformedToolUseBlock`). These derive directly from `Exception` and are **NOT** placed under `SubagentToolError`.

**DD-M18 resolution.** Within the tool-error family, future Matcher tool errors take a shared base (`SubagentToolError`), not independent sibling classes. The reasons, as authored in `matcher.md` §6.4: it is the pattern of `claude-agent-sdk` itself (`ClaudeSDKError` base + subclasses, catch-all by base); it is the Python idiom for a family of related errors; `DetectorScanFailed` is already a sibling under that base via DD-D5; and the choice is low-risk because retry-vs-escalate is decided by the `is_retryable` data field, not by the exception type (Decision 4). The minimal base was introduced in MC-C as a non-breaking move; this ADR ratifies the hierarchy.

**Rationale.** The two axes answer different questions. The tool-error family represents *a tool's domain failure* and must carry the verbatim retry semantics the tool declared; the SDK-class + contract axis represents *the agent loop or a contract breach* and has no tool envelope to carry. Conflating them under one base would force the SDK-class exceptions to either fabricate envelope fields or carry them as dead `None`s, and would invite a catch-by-base that swallows two unrelated failure kinds. Keeping the axes orthogonal preserves precise `except` targeting.

**Consequences.** A reader of `errors.py` can tell from the class's base which axis a failure belongs to. Adding a Matcher tool error is non-breaking: it subclasses `SubagentToolError` and inherits the field contract. Adding an SDK-class or contract exception derives from `Exception` directly and carries `stage` (Decision 2).

### 2. Every exception carries a `stage` blame field

Every exception in the taxonomy carries a `stage` attribute identifying where in the pipeline the failure is attributed. The invariant is enforced by the anchor test `test_every_exception_carries_stage` (`tests/coordinator/test_coordinator_errors.py`), which constructs every class and asserts `e.stage` equals the expected stage. Stages that are not one of the five pipeline names are still explicit: `CoordinatorStartupError` carries `stage="startup"`; `UnsupportedLegalFramework` carries `stage="framework_guard"` (a dedicated value — see Decision 5).

**Rationale.** Blame attribution is provenance. The coordinator projects any halt into `CoordinatorError(cause, stage, coverage_gap)` (Decision 3), and `stage` is the field that tells the auditor *which* stage produced the halt without parsing the exception type. A dedicated `stage` per failure point (rather than inferring it from the type) keeps blame accurate even when the same exception class can be raised at more than one stage.

**Consequences.** The anchor test makes the invariant load-bearing rather than conventional: a new exception that omits `stage` fails the suite. Blame is uniform across both axes of Decision 1.

### 3. The termination contract is a discriminated union with a coverage annotation

The coordinator returns `CoordinatorResult = CoordinatorReport | CoordinatorError` to the external caller (`src/coordinator/models.py`, `coordinator.md` §3.6):

- `CoordinatorReport(payload)` — the success path; `payload` is the `ReportPayload` dict captured from the Reporter's `emit_report` `ToolUseBlock.input`.
- `CoordinatorError(cause, stage, coverage_gap)` — any pipeline halt; `cause` is a typed Decision-1 exception, `stage` is the blame (Decision 2), and `coverage_gap` is a Brazilian-Portuguese human annotation of what was not analyzed.

The main entry wraps the pipeline in a top-level try/except: success projects to `CoordinatorReport`; any typed exception projects to `CoordinatorError`. The `coverage_gap` is decided per cause, not generic: for `DetectorScanFailed` it is "cobertura zero — scan não rodou" (because `scan_diff` is all-or-nothing per detector §8.2), **not** "resultado parcial". The external `run_outcome="error"` that the specs reference maps to `CoordinatorError`, and is distinct from `ReportPayload.run_outcome`, which carries the four success tokens of the Reporter contract.

**Rationale.** A discriminated union forces the caller to handle both arms explicitly rather than reading a nullable Report. The `coverage_gap` annotation is the structured-error-context principle: a halt that says only "error" hides from the caller what the system did and did not manage to analyze; characterizing the coverage loss in the caller's language (and distinguishing "zero coverage" from "partial") is what lets a human reviewer or CI consumer act on the halt.

**Consequences.** Rich audit fields (e.g. a `partial_scratchpad_path`) are deferred to Milestone D when the GitHub Action contract and scratchpad retention are designed; the union shape is stable and additive. The two-arm contract is anchored by `test_coordinator_models.py`.

### 4. Retry-vs-escalate is decided by `is_retryable`, not by exception type

Whether a halt is retried or escalated is determined by the `is_retryable` data field (inherited verbatim from the Option B envelope for tool errors; declared on the relevant SDK-class exceptions — e.g. `ReporterTurnsExhausted` is retryable with a larger budget, `ReportNotEmitted` is not), never by the position of the exception in the type lattice.

**Rationale.** This is what makes Decision 1's hierarchy low-risk: because control flow keys off a data field, the choice between sibling and shared base never changes behavior. It also keeps retry semantics honest to the tool's own declaration — the coordinator does not re-interpret a tool's retryability, it reads it.

**Consequences.** Reclassifying an exception (sibling ↔ base) is non-breaking for control flow. Adding a new retryable failure means setting `is_retryable=True` / a retryable marker, not inventing a new type branch.

### 5. Fail-loud termination: structured halt over silent coercion

Every failure path produces an explicit, typed halt; no path returns a success-shaped result carrying a rejected or coerced payload. Concrete materializations in `errors.py` and the driver:

- The `framework_guard` raises `UnsupportedLegalFramework` and **refuses to emit** a mislabeled Report rather than coercing the `legal_framework` label; the per-clause verdicts remain observable on the `policy-reader` surface.
- `CoordinatorStreamFailure` is raised when the `async for` ends with no `ResultMessage` captured — a stream-level failure distinct from a deliberate `is_error` exit.
- `MalformedToolUseBlock` fails loud when a `ToolUseBlock` lacks the expected `.input` (signals an SDK version below the pinned floor of ADR-0001 D2) rather than proceeding on a malformed block.
- The post-loop safety net raises `ReportNotEmitted` when a retry was allowed but no Report ever committed (ADR-0016), never a `CoordinatorReport` with a rejected payload.

**Rationale.** Silent false success is the failure mode the project has repeatedly identified as the most expensive (learning-log; "deferred specification has produced silent false successes"). A structured halt with `stage` and `coverage_gap` is recoverable information; a coerced success is a latent defect. ADR-0016 proved one instance of this empirically (the emit guard, 10 measured runs) and ADR-0012 D5 anchored its enforcement-layer counterpart; this decision records the general posture so future error paths inherit it by default.

**Consequences.** New stages and new tool integrations must specify their error channel before implementation (no deferred error-path specification). A halt is always preferred to a degraded silent success; "honest halt" is an acceptable outcome.

## Alternatives considered

- **Single exception base for the whole taxonomy.** Rejected per Decision 1 rationale — it forces dead envelope fields on the SDK-class axis and invites catch-by-base across unrelated failure kinds.
- **Encode retryability in the type lattice** (e.g. `RetryableError` / `FatalError` superclasses). Rejected per Decision 4 — it duplicates information the envelope already carries and makes reclassification breaking.
- **Several small ADRs** (one per decision). Rejected per the Context scope note — the decisions share one subject and one consumer; ADR-0003 set the precedent for consolidating a coherent meta-decision unit.
- **Leave the taxonomy in spec + code, no ADR.** Rejected per ADR-0009's threshold: these are decisions with runtime consequence (changing them requires runtime refactor and regression risk), which is precisely the line that puts a decision in scope for an ADR rather than `.claude/rules/`.

## Consequences (aggregated)

- The reserved ADR-0013 number is claimed; the 0012→0014 gap is closed.
- `errors.py`, `models.py`, and the driver become legible against a ratified frame: a reader can place any exception on its axis (D1), read its blame (D2), and know how it projects to the caller (D3) and whether it retries (D4).
- The fail-loud posture (D5) is documented as a standing principle, with ADR-0016 and ADR-0012 D5 as its prior point materializations.
- Defense artifact (Capítulo de Método): the three-layer error pipeline — Option B envelope (`errorCode`, ADR-0002) → typed exception (`stage`, this ADR) → external projection (`CoordinatorError`, D3) — is recorded as a positive exemplar of structured error propagation, complementing the two exemplars ADR-0012 already lists (protocol-vs-domain error; availability-vs-capability governance).

## Companion edits in this PR

These materialize loop-closures the decisions above surface. **Both require the author's confirmation of intent before Code applies them.**

1. **Close ADR-0012 Deferral B.** Deferral B (the consumer-side `legal_framework` jurisdictional gate) declared its revisit condition as "implementation of `src/coordinator/` (Milestone C)" and named the coordinator code as the future owner (DD-M22, correction H1). The gate now exists as `UnsupportedLegalFramework` / `stage="framework_guard"` in `src/coordinator/errors.py`, raised before the Reporter. Add an `## Amendment scope` block to ADR-0012 recording that Deferral B is resolved by the coordinator-owned guard, with this ADR as the cross-reference — so the deferral does not silently become "abandoned" against ADR-0002's deferral-ledger discipline.

2. **Correct the `framework_guard` citation.** The `UnsupportedLegalFramework` docstring cites ADR-0007 ("the MVP emits Reports for LGPD only (ADR-0007)"). ADR-0007 decides `operation_type=collection` scope and does not decide `legal_framework=LGPD-only`. The governing decision is ADR-0012 Deferral B (the jurisdictional gate) together with ADR-0005 (LGPD as the MVP instance). **Author to confirm:** either (a) the citation is imprecise and should read ADR-0012 Deferral B + ADR-0005, or (b) the LGPD-only-framework decision was never formally taken and should be ratified here as a new sub-decision rather than borrowed from ADR-0007. The choice changes whether this is a one-line docstring fix or an added decision in this ADR.

## Open points for ratification

- **Decision 5 scope.** Whether to state the fail-loud posture as a *general principle* (as drafted) or to keep it as an enumeration of the four materialized instances. The general form is stronger for the defense but commits future error paths to it.
- **Companion edit 2** (above) — the framework citation question is the one substantive open decision; the rest is assembly of already-materialized facts.
- **Line-number anchors.** This draft cites file paths and symbol names only (content-based anchors per the project's `str_replace` discipline); Code confirms exact loci at materialization.
