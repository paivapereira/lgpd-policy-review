# ADR-0008 — Task decomposition granularity and verification gate

**Status.** Accepted (session #17).
**Date.** 2026-05-15
**Supersedes.** Nothing.
**Superseded by.** Nothing.
**Related.** ADR-0001 (workflow and SDD adoption), ADR-0003 (spec architecture — dual canonical+compact), ADR-0006 (language conventions). REQUIREMENTS.md is the upstream artifact whose RFs and RNFs anchor task acceptance under Decision 2 below.

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

### 1. Medium-granularity task decomposition (8-12 tasks of 1-3 hours each)

`docs/tasks.md` decomposes Fase 2 implementation into 8-12 tasks of
1-3 hours each, not 15-25 tasks of 30-60 minutes. Each task delivers an
observable capability against the system contract declared in
`docs/REQUIREMENTS.md`, not an internal implementation step.

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
maps to a meaningful slice of system capability rather than to a
micro-step of implementation. Code is expected to plan internal
sub-steps within a task without explicit guidance.

### 2. Task acceptance is bound to REQUIREMENTS.md RFs and RNFs

Each task in `docs/tasks.md` declares which RFs and RNFs it covers and
inherits their Dado/Quando/Então acceptance criteria as its own. Tasks
do not invent new acceptance criteria; they reference and satisfy the
existing ones.

**Rationale.** REQUIREMENTS.md is the single source of truth for system
capabilities (cf. PR #23). Replicating acceptance across tasks would
introduce drift between requirement and task statements, and would
weaken the citation chain RF → task → commit established in
REQUIREMENTS.md's "Convenção" section. Binding tasks to RFs preserves
this chain trivially.

**Consequences.** Adding a system capability requires adding the RF
first, then the task that implements it. Changing acceptance for a
capability is a REQUIREMENTS.md edit, not a tasks.md edit. Tasks remain
short and stable; refinement of acceptance lives in the upstream
artifact.

### 3. Tripartite verification gate per task

Each task declares an explicit verification gate composed of three
mechanisms, all of which must pass before the task is marked done:

- **Automated tests.** Pytest suite covering the RF acceptance criteria
  in executable form. Test failure blocks task completion.
- **Independent review pass.** A separate Chat session reads the diff
  produced by Code against the task's RFs and lists any divergences,
  bugs, or violations of project conventions. Functions as the
  independent evaluator pattern of Rajasekaran 2026, applied to code
  review rather than to code generation. Review issues are addressed
  before task completion.
- **Manual exercise.** Operator-driven exercise of the new capability
  via MCP Inspector or CLI, validating behavior end-to-end against
  expectation. Catches issues automated tests and code review miss:
  output organization, message quality, user-facing latency, edge
  scenarios not anticipated in specs.

A task is marked done only when all three mechanisms pass for its
declared RF coverage. Self-evaluation by the implementing Code session
does not satisfy the independent review requirement.

**Rationale.** Reducing task granularity reduces the number of natural
verification checkpoints. The tripartite gate compensates by adding
defense in depth at each remaining checkpoint. The independent review
pass is the key insurance against subtle bugs that single-instance
self-review tends to miss, documented as multi-instance review pattern
in the Claude Certified Architect Foundations exam guide (Task
Statement 4.6) and validated empirically by Rajasekaran 2026.

**Consequences.** Each task carries higher verification cost than under
fine-grained decomposition, where a passing test on a 30-minute task
was often the only gate. Total project cost is comparable or lower
because the number of tasks decreased proportionally, and the
verification work that previously fragmented across many tasks
concentrates on fewer, more meaningful checkpoints.

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
- Task list is short, stable, and bound to REQUIREMENTS.md as source of
  truth, removing duplicate-statement drift risk.
- Verification gate captures the multi-instance review pattern explicitly,
  reducing the surface for subtle bugs to slip past single-session
  self-evaluation.
- Methodological calibration is defensible in the TCC defense via direct
  reference to the published Anthropic article and to the broader
  Anthropic principle of progressive harness simplification.

**Negative.**
- Independent review by a separate Chat session adds wall-clock time per
  task (a Chat session of meaningful length) that fine-grained
  decomposition with passing tests alone would skip. Accepted as the
  cost of defense in depth.
- Manual exercise requires operator availability per task milestone,
  competing with passive automated runs. Accepted because the failure
  modes manual exercise catches (UX-grade issues, latency, integration
  rough edges) are precisely the ones Code self-review and tests miss.

**Migration path.** Not applicable — `docs/tasks.md` does not yet exist.
This ADR is the governing decision at its authoring.

## Companion edits in this PR

- `CLAUDE.md` — append a one-line pointer to this ADR in the section
  governing task workflow.
- `docs/proposta-tcc2.md` — add a paragraph to §7 (Metodologia) citing
  Rajasekaran 2026 and stating the SDD calibration adopted here, with
  the bibliographic entry added to §11.
- `docs/learning-log.md` — entry for session #17 references this ADR.
- `docs/session-handoff.md` — pendência entry for `docs/tasks.md`
  authoring updated to cite this ADR as governing.
