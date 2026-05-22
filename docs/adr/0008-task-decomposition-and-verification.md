# ADR-0008 — Task decomposition granularity and verification gate

**Status.** Accepted (session #17, 2026-05-15); amended in-place same session (2026-05-16) before any task authored under it.
**Date.** 2026-05-15 (original) / 2026-05-16 (amendment).
**Supersedes.** Nothing.
**Superseded by.** Nothing.
**Related.** ADR-0001 (workflow and SDD adoption), ADR-0003 (spec architecture — dual canonical+compact), ADR-0006 (language conventions). REQUIREMENTS.md is the upstream artifact whose RFs and RNFs anchor milestone acceptance under Decision 2 below.

**Amendment scope (2026-05-16).** Decisions 1-3 refined. RF binding moved from task to milestone scope (Decision 2). Verification gate split into task-level (function tests + independent review) and milestone-level (manual exercise validating RF acceptance) (Decision 3). Amendment landed in-place rather than as a successor ADR because the original was authored 2026-05-15 in session #17 with no tasks yet authored under it; #18 (tasks.md authoring) is the first downstream consumer and runs under the amended version. The original formulation conflated capability (externally observable, RF-shaped, milestone-scope in practice) with function (unit-of-work output, test-shaped, task-scope) at the task level, producing artificial RF bindings for internal tasks (loaders, scaffolding, configuration wiring). The amendment decouples the two.

## Context

The project adopted Spec-Driven Development (SDD) as formal methodology
in `docs/proposta-tcc2.md` §7, with four canonical phases: Specify, Plan,
Implement, Validate. The Plan phase produces `docs/tasks.md`, decomposing
implementation into discrete tasks consumed by Code one at a time.

Initial planning for `docs/tasks.md` in `docs/session-handoff.md` targeted
15-25 tasks calibrated to 30-60 minute implementation sessions, following
granularity conventions of frameworks like GitHub Spec Kit.

In session #17, Rajasekaran (Anthropic Labs, 2026-03-24, "Harness design
for long-running application development") was identified as posterior to
the project's reference cutoff and directly relevant. The article reports
empirical findings on harness design for autonomous coding agents: scaffold
patterns that were load-bearing for Claude Sonnet 4.5 — sprint constructs,
context resets, fine-grained task decomposition — became dead weight with
Claude Opus 4.6, which exhibits longer coherent autonomous operation
without the "context anxiety" of 4.5. The article converges on a minimal
three-agent architecture (planner, generator, evaluator) for full-stack
work, with progressive scaffold removal as model capability increases.

This project executes implementation on Claude Opus 4.7, one major release
past the Opus 4.6 baseline of the article. The conditions that justified
the original 15-25 fine-grained task plan no longer hold. A calibration
of SDD granularity and verification strategy is needed, recorded here as
formal decision before `docs/tasks.md` is authored.

## Decision

### 1. Medium-granularity task decomposition (8-12 tasks of 1-3 hours each, grouped into milestones)

`docs/tasks.md` decomposes Fase 2 implementation into 8-12 tasks of
1-3 hours each, not 15-25 tasks of 30-60 minutes. Tasks are grouped
into milestones. Each **milestone** delivers an observable capability
against the system contract declared in `docs/REQUIREMENTS.md`. Each
**task** delivers coherent function within its milestone — a loader,
a resource, a tool, a recognizer set, an integration step — and need
not stand alone as a capability.

**Rationale.** Fine-grained decomposition served, in earlier model
generations, to keep the coding agent coherent inside a limited
attention window — Rajasekaran 2026 documents this trade-off and its
expiration with Opus 4.6+. With Opus 4.7, the generator handles
multi-hour autonomous sessions on coherent specs. Decomposing further
adds orchestration overhead without buying coherence, and risks
duplicating context the generator already absorbs by reading
REQUIREMENTS.md and the canonical specs. Medium granularity preserves
two properties of explicit decomposition that remain load-bearing —
topological ordering of dependencies, and verifiable checkpoints —
while shedding the ceremonial overhead.

**Consequences.** `tasks.md` is shorter and less ceremonious. Each task
maps to a coherent function within a milestone; milestones aggregate
tasks into capability deliverables bound to REQUIREMENTS.md (Decision
2). Code is expected to plan internal sub-steps within a task without
explicit guidance.

### 2. Milestone acceptance is bound to REQUIREMENTS.md RFs and RNFs

Each milestone in `docs/tasks.md` declares which RFs and RNFs it
covers and inherits their Dado/Quando/Então acceptance criteria as
its own. Milestones do not invent new acceptance criteria; they
reference and satisfy the existing ones. Tasks within a milestone do
not bind individually to RFs — they implement coherent function that
contributes to the milestone's capability, including internal
infrastructure (loaders, scaffolding, configuration wiring) with no
1:1 RF correspondence.

**Rationale.** REQUIREMENTS.md is the single source of truth for
system capabilities (cf. PR #23). Capabilities are externally
observable units delivered at milestone closure, not within individual
tasks. The original per-task RF binding forced internal tasks to
either invent partial RF coverage claims ("RNF-X parcial") or remain
without acceptance criteria, weakening both the citation chain and
the task list's signal-to-noise ratio. Binding capability at the
milestone level preserves the citation chain
RF → milestone → constituent tasks → commits without distortion.

**Consequences.** Adding a system capability requires adding the RF
in REQUIREMENTS.md, then the milestone (and its tasks) that implements
it. Changing acceptance for a capability is a REQUIREMENTS.md edit.
Task-level acceptance is function-specific and lives in Decision 3,
independent of RF text.

### 3. Verification gate at two scopes — function per task, capability per milestone

Function and capability are different scopes and warrant different
tests. Two gates apply.

**Task-level gate.** Each task declares two mechanisms, both required
before the task is marked done:

- **Automated tests (function-specific).** Pytest suite covering the
  contract surface of what the task built — a loader parses YAML and
  aborts on missing files; a tool returns the correct error code for
  invalid input; a resource serializes loaded state correctly. Tests
  target the unit's external behavior, not internal helpers, and are
  independent of RF text. Test failure blocks task completion.
- **Independent review pass.** A separate Chat session reads the diff
  produced by Code against the task's stated function and lists any
  divergences, bugs, or violations of project conventions. Functions
  as the independent evaluator pattern of Rajasekaran 2026, applied
  at the unit-of-work level where subtle bugs are easiest to catch.
  Review issues are addressed before task completion.

**Milestone-level gate.** Each milestone declares one mechanism,
required before the milestone is marked complete:

- **Manual exercise against RFs.** Operator-driven exercise of the
  milestone's capability via MCP Inspector or CLI, validating
  end-to-end behavior against each Dado/Quando/Então acceptance
  criterion of the RFs declared in Decision 2. Catches issues
  automated tests and code review miss: output organization, message
  quality, user-facing latency, integration friction, edge scenarios
  not anticipated in specs.

A task is marked done when its tests pass and its independent review
pass clears. A milestone is marked complete when all its tasks are
done AND its manual exercise validates each declared RF acceptance
criterion. Self-evaluation by the implementing Code session satisfies
neither the independent review nor the manual exercise.

**Rationale.** The original formulation — three mechanisms per task,
all bound to RF acceptance — conflated two distinct scopes. Function
tests at the task level catch implementation bugs in the unit just
built; capability exercise at the milestone level catches integration
and RF-level regressions that no individual task could observe.
Decoupling sharpens each. The independent review pass remains the
key insurance against subtle bugs in single-instance self-review,
empirically validated by Rajasekaran 2026 and named as multi-instance
review pattern in the Claude Certified Architect Foundations exam
guide (Task Statement 4.6).

**Consequences.** Per-task overhead drops from three mechanisms to
two; the manual exercise was always milestone-shaped in practice
(capability validation requires multiple tasks done first).
Per-milestone overhead is explicit and concentrated, not fragmented
across tasks. Total verification work is comparable to the original
tripartite design; distribution now matches the scope at which each
mechanism is actually useful.

### 4. Reference to the methodological literature

The decisions above cite Rajasekaran 2026 as primary empirical reference
and incorporate the principle "find the simplest solution possible, and
only increase complexity when needed" from Anthropic's Building
Effective Agents (2025). This ADR is the canonical citation point for
both references in subsequent project artifacts (proposta-tcc2 §7,
future ADRs, the TCC technical report).

**Bibliographic entries.**

RAJASEKARAN, P. Harness design for long-running application development.
Anthropic Engineering, 24 mar. 2026. Disponível em:
<https://www.anthropic.com/engineering/harness-design-long-running-apps>.

ANTHROPIC. Building Effective Agents. Anthropic Research, 2025.
Disponível em: <https://www.anthropic.com/research/building-effective-agents>.

## Aggregated consequences

**Positive.**
- Task list and milestone list are short, stable, and bound to
  REQUIREMENTS.md at the scope where capability is delivered, removing
  duplicate-statement drift risk and the prior friction of per-task
  RF binding for internal tasks.
- Verification operates at the scope at which each mechanism is
  useful: function tests where function is built; independent review
  where bugs hide; manual capability exercise where integration meets
  RF expectation. Multi-instance review pattern preserved at the task
  level (independent Chat session).
- Methodological calibration is defensible in the TCC defense via
  direct reference to the published Anthropic article and to the
  broader Anthropic principle of progressive harness simplification.

**Negative.**
- Independent review by a separate Chat session adds wall-clock time
  per task that fine-grained decomposition with passing tests alone
  would skip. Accepted as the cost of defense in depth.
- Manual exercise requires operator availability at milestone
  closure, competing with passive automated runs. Accepted because
  the failure modes manual exercise catches (UX-grade issues,
  latency, integration rough edges) are precisely the ones Code
  self-review and tests miss.

**Migration path.** Not applicable — `docs/tasks.md` does not yet
exist. This ADR (as amended 2026-05-16) is the governing decision at
its authoring.

## Companion edits in this PR

- `CLAUDE.md` — append a one-line pointer to this ADR in the section
  governing task workflow.
- `docs/proposta-tcc2.md` — add a paragraph to §7 (Metodologia) citing
  Rajasekaran 2026 and stating the SDD calibration adopted here, with
  the bibliographic entry added to §11.
- `docs/learning-log.md` — entry for session #17 references this ADR.
- `docs/session-handoff.md` — pendência entry for `docs/tasks.md`
  authoring updated to cite this ADR as governing.

## Amendment companion edits (2026-05-16)

- `.claude/rules/spec-driven-workflow.md` — section on task workflow
  updated to reflect milestone-scope RF binding and the two-scope
  verification gate (originally cited "tripartite verification gate";
  now cites two-scope gate). Originally listed as CLAUDE.md edit, but
  the actual content landed in `.claude/rules/spec-driven-workflow.md`
  during the rules migration of session #22 (PR-3 housekeeping);
  location corrected 2026-05-22.
- `docs/learning-log.md` — session #17 entry annotates the in-place
  amendment, preserving the original entry and adding the amendment
  rationale as a sub-section.
- `docs/session-handoff.md` — pendência entry for `docs/tasks.md`
  authoring reflects amended ADR-0008 as governing.
