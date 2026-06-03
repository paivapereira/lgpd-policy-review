# ADR-0016 — Reporter single-emission guard counts successful emissions, not attempts

**Status.** Proposed (skeleton authored on branch `fix/reporter-guard-counts-successes`). **Not ratified.** This ADR is mechanical assembly of empirically-measured pipeline facts plus the decision they motivate; the normative rationale requires the author's ratification before acceptance (per the project's ADR-authoring convention — Code assembles and cross-references, the author decides).
**Date.** 2026-06-02
**Supersedes.** Nothing.
**Superseded by.** Nothing.
**Related.** `reporter.md` §3.5/§6.7/§9.2.a (the retry-on-error contract the AS-IS guard contradicted), `coordinator.md` §3.5/§3.6 (the emit-counting discrimination), ADR-0014 (the Reporter stage transport this guard lives in), PR #101 (the provenance fix `(a)` whose deployment surfaced the residual), `docs/tasks.md` §Companion (the debt this ADR closes).

## Context

The coordinator's Reporter stage (`src/coordinator/run.py` `_run_reporter_stage`, **read 2026-06-02**) inspects the `query()` message stream and raises `MultipleReportEmissions` on the **second** `emit_report` `ToolUseBlock` it sees, **blind to whether the first emission succeeded**. The `emit_report` handler (`src/subagents/reporter/tools.py`) validates the payload (Pydantic + four intra-handler cross-checks) and, **only on success**, writes `99-report.json` atomically (`os.replace`); on any validation failure it returns an `is_error` envelope and writes nothing.

This collapses two distinct situations into one halt:
- a 2nd emit **after a successful** first emit — genuine redundancy, which **should** halt;
- a 2nd emit **after a failed** first emit — a legitimate validation-retry, which the Reporter system prompt explicitly instructs ("if `emit_report` returns an error envelope … correct the payload, and retry") and which `reporter.md` **already sanctions**: §9.2.a ("first `emit_report` returns `PYDANTIC_VALIDATION`; model retries with corrected payload; second emit succeeds; **coordinator captures**") and §6.7 ("Multi-turn no caminho normal … não-erro").

### Empirical grounding (measured, not assumed)

After the provenance fix `(a)` (PR #101) removed the deterministic `PROVENANCE_MISMATCH` cause, a diagnostic of **5 live COMP-001 pipeline runs** (root `policies/eval-lgpd`, **2026-06-02**) measured a **residual 2/5 halt** in `MultipleReportEmissions`:

- `PROVENANCE_MISMATCH` in the 1st emission: **0/5** (`(a)` confirmed live).
- Outcome: **3/5 Report** (`success_with_findings`, consistent provenance, `99-report.json` present); **2/5 halt**.
- Both halts: 1st emission `PYDANTIC_VALIDATION` from a **tool-argument wrapper** — the model called `emit_report` with `{"report": "<the whole payload serialized as a JSON string>"}` instead of the flat Report object; **2nd emission VALID** (the model corrected the shape); payloads **not identical**; `99-report.json` **absent** in both halts, **present** in all 3 Reports (a 5/5 clean success signal).

So the residual halt is the AS-IS guard **strangling the legitimate retry** the model auto-corrected — exactly the path `reporter.md` §9.2.a already declares non-erroneous. The AS-IS guard is the **divergence from the existing spec**, not a deliberate strictness to preserve.

## Decision (proposed — to be ratified)

The Reporter single-emission guard counts/aborts on **successful** emissions, not attempts. The success signal is the handler's `99-report.json` sink (`REPORT_SINK_FILENAME`, now a shared constant in `subagents/reporter/constants.py` so writer and reader cannot drift).

- 1st emit: capture the candidate payload (unchanged).
- 2nd+ emit: if `99-report.json` **present** (a prior emit succeeded) → `MultipleReportEmissions` (genuine redundancy); if **absent** (the prior emit failed) → allow the retry, re-capture the new candidate (`allowed_retry = True`).
- Post-loop safety net: if `allowed_retry` and `99-report.json` **absent** and `subtype != error_max_turns` → `ReportNotEmitted` (no Report was ever committed) — a **honest halt**, never a `CoordinatorReport` carrying a rejected payload silently.

This **refines** the invariant "exactly one emission" → "exactly one **successful** emission", preserving the real integrity invariant — **one committed Report** — rather than weakening it. The provenance cross-check and the redundancy halt remain legitimate invariants; this is **conformance with an existing spec** (`reporter.md` §9.2.a), in the same spirit as `(a)` (which made the impl conform to the `reporter.md` provenance-source table), not a new decision to relax integrity.

### Scope / calibration (do not overstate)

This resolves the **wrapper-auto-corrected** mode (1st emit fails on shape, 2nd succeeds). It does **not** eliminate `MultipleReportEmissions` universally:
- two **genuinely successful** emissions still halt (real redundancy);
- exhausting `max_turns` still raises `ReporterTurnsExhausted`;
- the single-failed-emit-then-voluntary-end case (a 1st emit fails and the model ends without retrying, `subtype == "success"`) is a **pre-existing latent** silent-success in the AS-IS code (it returns the rejected payload); it is **out of scope** here (rare — the model normally retries) and registered as separate debt.

## Consequences

- The guard gains a **filesystem read** of `99-report.json` (coupling to the handler's sink), scoped to the run's `run_path` which the coordinator already owns and threads to the stage.
- The consumption loop and the tri-axial post-loop discrimination are **preserved** — the change is localized to the emit-counting branch + a post-loop net + the `run_path` parameter; the §3.0bis driver spine is untouched.
- `reporter.md` §9.2.a becomes **reachable** (the retry-success path now returns the corrected Report); the §3.5↔§9.2.a contradiction debt (`docs/tasks.md` §Companion) is **closed**.
- The deterministic anchor was rewritten: `test_reporter_second_emit_after_success_raises` (redundancy preserved) and `test_reporter_second_emit_after_failure_allowed` (retry not redundancy). The mock cannot run the handler, so the tests control the `99-report.json` signal manually and the end-to-end happy path (retry → committed Report) is the **live smoke**, separate.

## Open for the author's ratification

- The rationale/normative framing above (especially "conformance, not relaxation") — confirm or revise.
- The disk-signal coupling (Form 2) vs the stream-correlation form (Form 1, `ToolUseBlock`↔`ToolResultBlock.is_error`): Form 1 is the originally-documented target but hinges on an unverified SDK question (whether `query()` surfaces the in-process `@tool` result; the Detector precedent uses `ClaudeSDKClient` + `structuredContent`, which the `@tool` bridge drops). Form 2 was chosen as de-risked by the 5/5 diagnostic. Confirm Form 2, or require the Form-1 smoke first.
- Whether the pre-existing single-emit silent-success warrants its own follow-up now or stays deferred debt.
