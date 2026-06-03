# ADR-0016 — Reporter single-emission guard counts successful emissions, not attempts

**Status.** Accepted (ratified by the author 2026-06-03, with the post-`(c)` confirmation smoke below). The decision and its empirical grounding are assembled here per the project's ADR-authoring convention (Code assembles and cross-references measured facts; the author ratifies the normative framing).
**Date.** 2026-06-02 (authored) · 2026-06-03 (ratified).
**Supersedes.** Nothing.
**Superseded by.** Nothing.
**Related.** `reporter.md` §3.5/§6.7/§9.2.a (the retry-on-error contract the AS-IS guard contradicted), `coordinator.md` §3.5/§3.6 (the emit-counting discrimination), ADR-0014 (the Reporter stage transport this guard lives in), PR #101 (the provenance fix `(a)` whose deployment surfaced the residual), PR #102 (the `(c)` fix this ADR records), `docs/tasks.md` §Companion (the debt this ADR closes).

## Context

The coordinator's Reporter stage (`src/coordinator/run.py` `_run_reporter_stage`, **read 2026-06-02**) inspects the `query()` message stream and raises `MultipleReportEmissions` on the **second** `emit_report` `ToolUseBlock` it sees, **blind to whether the first emission succeeded**. The `emit_report` handler (`src/subagents/reporter/tools.py`) validates the payload (Pydantic + four intra-handler cross-checks) and, **only on success**, writes `99-report.json` atomically (`os.replace`); on any validation failure it returns an `is_error` envelope and writes nothing.

This collapses two distinct situations into one halt:
- a 2nd emit **after a successful** first emit — genuine redundancy, which **should** halt;
- a 2nd emit **after a failed** first emit — a legitimate validation-retry, which the Reporter system prompt explicitly instructs ("if `emit_report` returns an error envelope … correct the payload, and retry") and which `reporter.md` **already sanctions**: §9.2.a ("first `emit_report` returns `PYDANTIC_VALIDATION`; model retries with corrected payload; second emit succeeds; **coordinator captures**") and §6.7 ("Multi-turn no caminho normal … não-erro").

### Empirical grounding (measured, not assumed)

**Before `(c)` — the residual halt.** After the provenance fix `(a)` (PR #101) removed the deterministic `PROVENANCE_MISMATCH` cause, a diagnostic of **5 live COMP-001 pipeline runs** (root `policies/eval-lgpd`, **2026-06-02**) measured a **residual 2/5 halt** in `MultipleReportEmissions`:

- `PROVENANCE_MISMATCH` in the 1st emission: **0/5** (`(a)` confirmed live).
- Outcome: **3/5 Report** (`success_with_findings`, consistent provenance, `99-report.json` present); **2/5 halt**.
- Both halts: 1st emission `PYDANTIC_VALIDATION` from a **tool-argument wrapper** — the model called `emit_report` with `{"report": "<the whole payload serialized as a JSON string>"}` instead of the flat Report object; **2nd emission VALID** (the model corrected the shape); payloads **not identical**; `99-report.json` **absent** in both halts, **present** in all 3 Reports (a 5/5 clean success signal).

So the residual halt is the AS-IS guard **strangling the legitimate retry** the model auto-corrected — exactly the path `reporter.md` §9.2.a already declares non-erroneous. The AS-IS guard is the **divergence from the existing spec**, not a deliberate strictness to preserve.

**After `(c)` — the confirmation smoke.** 5 live COMP-001 runs against `main` with `(c)`/PR #102 deployed (**2026-06-03**) gave **0/5 halt (was 2/5)** — `5/5 Report success_with_findings`. The wrapper phenomenon **did not disappear**: runs **3 and 5** had `reporter_emit_count == 2` (1st emit a wrapper, 2nd valid) — the same ~2/5 wrapper occurrence as before, now **recovered to a Report instead of halted**. The recovery was **observed directly**, not inferred from halt absence: a smoke-only instrumentation wrapped the Reporter's `query` to count `emit_report` `ToolUseBlock`s per run, so `emits == 2` on a Report run is a literal observation of "first emit failed, second succeeded, guard allowed it, Report committed". The recovered Reports (runs 3, 5) are **identical in shape** to the single-emit Reports — `top policy_version=0.2.0` (`(a)` holds in the recovered path too), `POL-005=compliant`, `counts {compliant:1, not_applicable:3}` — and converge with the COMP-001 ground truth. **Recovery does not degrade the Report.** Runs 3 and 5 are literally `reporter.md` §9.2.a executing.

## Decision

The Reporter single-emission guard counts/aborts on **successful** emissions, not attempts. The success signal is the handler's `99-report.json` sink (`REPORT_SINK_FILENAME`, now a shared constant in `subagents/reporter/constants.py` so writer and reader cannot drift).

- 1st emit: capture the candidate payload (unchanged).
- 2nd+ emit: if `99-report.json` **present** (a prior emit succeeded) → `MultipleReportEmissions` (genuine redundancy); if **absent** (the prior emit failed) → allow the retry, re-capture the new candidate (`allowed_retry = True`).
- Post-loop safety net: if `allowed_retry` and `99-report.json` **absent** and `subtype != error_max_turns` → `ReportNotEmitted` (no Report was ever committed) — a **honest halt**, never a `CoordinatorReport` carrying a rejected payload silently.

This **refines** the invariant "exactly one emission" → "exactly one **successful** emission", preserving the real integrity invariant — **one committed Report** — rather than weakening it. The provenance cross-check and the redundancy halt remain legitimate invariants; this is **conformance with an existing spec** (`reporter.md` §9.2.a), in the same spirit as `(a)` (which made the impl conform to the `reporter.md` provenance-source table), not a new decision to relax integrity. The confirmation smoke proves it empirically: runs 3 and 5 are the §9.2.a retry-success path executing, which the AS-IS guard had been contradicting.

### Alternatives considered

**Form 1 — stream correlation (`ToolUseBlock` ↔ `ToolResultBlock.is_error`).** The reconciliation originally sketched in `docs/tasks.md` §Companion ("correlate ToolUseBlock with ToolResultBlock.is_error; count only successful emits"). **Considered and not chosen.** It hinges on an **unverified SDK question** — whether `query()` surfaces the in-process `@tool` result at all: the only tool-result-inspection precedent in the codebase is the Detector, which uses `ClaudeSDKClient` + `structuredContent`, and the `@tool` bridge **drops** `structuredContent` (`.claude/rules/sdk-mcp-conventions.md` Eixo 2). Form 2 (the disk signal) was chosen because it is **de-risked by measurement** — `99-report.json` discriminated recovery from redundancy correctly in **every one of the 10 runs measured** (present on all Reports; absent when the guard correctly allowed the retry in runs 3 and 5) — and it does not touch the Reporter transport. If the filesystem coupling ever becomes a problem, Form 1 is the decoupling path, behind a smoke that first confirms `query()` surfaces the `@tool` result. This is documentation of a weighed alternative, **not** a deferred obligation.

### Scope / calibration (do not overstate)

This resolves the **wrapper-auto-corrected** mode (1st emit fails on shape, 2nd succeeds). It does **not** eliminate `MultipleReportEmissions` universally:
- two **genuinely successful** emissions still halt (real redundancy);
- exhausting `max_turns` still raises `ReporterTurnsExhausted`;
- the **single-failed-emit-then-voluntary-end** case (a 1st emit fails and the model ends without retrying, `subtype == "success"`) is a **pre-existing latent** silent-success in the AS-IS code (it returns the rejected payload). It was **not observed in any of the 10 runs** measured (5 pre-`(c)` + 5 post-`(c)`) — when the 1st emit fails, the model retries rather than ending. It is **covered** by the `ReportNotEmitted` safety net (if it ever happens it is an honest halt, never a silent false success), so the risk is contained though the case is not *resolved* (it halts rather than recovering). **Deferred debt** — if it surfaces in the full Passo-2 sweep it becomes its own investigation. (Same calibration applied throughout: do not fix what was not measured, do not ignore what is known to exist.)

## Consequences

- The guard gains a **filesystem read** of `99-report.json` (coupling to the handler's sink), scoped to the run's `run_path` which the coordinator already owns and threads to the stage.
- The consumption loop and the tri-axial post-loop discrimination are **preserved** — the change is localized to the emit-counting branch + a post-loop net + the `run_path` parameter; the §3.0bis driver spine is untouched.
- `reporter.md` §9.2.a becomes **reachable** (the retry-success path now returns the corrected Report — confirmed live, runs 3 & 5); the §3.5↔§9.2.a contradiction debt (`docs/tasks.md` §Companion) is **closed**.
- The deterministic anchor was rewritten: `test_reporter_second_emit_after_success_raises` (redundancy preserved) and `test_reporter_second_emit_after_failure_allowed` (retry not redundancy). The mock cannot run the handler, so the tests control the `99-report.json` signal manually and the end-to-end happy path (retry → committed Report) is the **live smoke** (the 0/5-halt confirmation above), separate.

## Ratification (2026-06-03)

Ratified by the author with the confirmation smoke as the closing evidence. The three points the skeleton left open are closed:

1. **Conformance, not relaxation** — confirmed; runs 3 and 5 are `reporter.md` §9.2.a executing. The real invariant ("one committed Report") is preserved; "one emission" → "one successful emission" is a refinement, not a weakening.
2. **Form 2 (disk signal)** — confirmed as the decision, on the measured basis above; Form 1 recorded as a considered-and-rejected alternative (a decoupling path behind a smoke, not an obligation).
3. **Single-emit silent-success** — deferred debt; covered by the `ReportNotEmitted` honest halt; not observed in 10 runs; revisited only if it surfaces in Passo 2.

This ADR closes the arc: `(a)` fixed the provenance desync, the diagnostic localized the wrapper, `(c)` made the guard count successes, and the confirmation smoke proved the recovery — decision recorded with the complete before-and-after empirical grounding.
