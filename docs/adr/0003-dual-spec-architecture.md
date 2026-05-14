# ADR-0003 — Dual-spec architecture: consumed/reference frame and §8.<final> lifecycle

**Status.** Accepted (retrospective — decisions taken in sessions #11 and #12, formalized here).
**Date.** 2026-05-13
**Supersedes.** Nothing.
**Superseded by.** Nothing.
**Related.** ADR-0001 (workflow conventions), ADR-0002 (MCP conventions; this ADR refines the lifecycle implied by Decision 5).

## Context

The dual canonical+compact spec strategy was sketched in the session #08 review and crystallized in sessions #11 and #12. Two meta-decisions emerged during execution that were not anticipated by the session #08 sketch and that affect how every future spec is structured and maintained. Both are retrospectively formalized here.

The first concerns the **purpose** of the canonical and compact files. Session #08 framed them as two versions of the same content paired by drift governance — a paridade-driven frame. Session #12 substituted this with a consumed/reference frame: compact is what Code reads when implementing the component; canonical is on-demand reference for humans and for Code when compact escalation pointers fire. The change has direct implications on sizing, validation method, and drift policy.

The second concerns the **lifecycle of §8.<final>** (the "review pass against architecture-overview" section). ADR-0002 Decision 5 prescribed the "three beats" form for each drift detected. It did not specify what happens to those entries after the proposed patches are applied to the overview. Session #12 preserved the "three beats" form post-application; this ADR records that decision and the formal lifecycle.

This ADR closes the spec-design meta-decision cycle. Implementation of the two MCP servers begins in the next session, anchored on the compacts cristalized in #11–#12.

## Decision

### 1. Consumed/reference frame supersedes the paridade frame

The canonical and compact files of a spec serve two different functions, not two presentations of one function. **Compact** (`docs/specs/<component>/compact.md`) is the artifact Code consumes at implementation time — always-loaded in the modal implementation workflow. Its budget is the empirical metric "Code implements the spec without opening canonical in the modal case", validated by proxy test (a separate Code instance implements the component from the compact alone and reports friction; applied to `policy-reader` compact in session #12). **Canonical** (`docs/specs/<component>/canonical.md`) is on-demand reference — read by humans for context, and by Code when a compact escalation pointer fires. Its size is governed by completeness, not by a line target.

Paridade is retained but scoped: it applies to **contract surfaces** (tool descriptions, output schemas, error codes, anti-uses, when-to-use guidance) — not to prose explanations. Contract drift between canonical and compact triggers paridade review; prose drift does not. This frame is the consumed/reference (always-loaded/on-demand) pattern from the small-always-loaded + large-on-demand idiom.

**Rationale.** The session #08 frame assumed compact was a literal compression of canonical, which implied a line-reduction target on the canonical (estimate from #08 was 575 lines for `policy-reader`). Session #12 made this target unreachable without losing canonical's utility for reference reading. The empirical method that emerged — read compact, implement against it, report friction — defined a different success criterion for compact, making canonical's size irrelevant to its evaluation. The frame change is therefore not stylistic; it changes what counts as success for each artifact.

**Consequences.** The canonical line-reduction target from session #08 is abandoned. Final canonical sizes are 673 lines for `policy-reader` and 440 for `semgrep-runner`, both accepted. Compact budget is no longer "fraction of canonical" but cognitive-load cap for skeleton implementation; empirical values are 397 and 202 lines respectively. The PR template checkbox bidirectional (`.github/PULL_REQUEST_TEMPLATE.md`) targets contract surfaces, not full-content paridade. Drift between canonical and compact in explanatory prose is acceptable without review action.

### 2. §8.<final> lifecycle: three beats persist post-application

Every spec carries §8.<final> with the "three beats" form prescribed by ADR-0002 Decision 5 (current overview text / why inconsistent / proposed patch). The lifecycle of those entries is now formalized in three states.

**During spec authoring** — drift detected, patch not yet applied to overview — §8.<final> contains the three beats as authored.

**After the proposed patches are applied to the overview** — in the same PR or a subsequent one — §8.<final> retains the three beats as historical record, with a closing line referencing the commit or PR that materialized the patch. The form does not collapse to a hash pointer.

**When no drift is detected** §8.<final> states this positively (mirrors ADR-0002 Decision 4 pattern), no three beats needed.

**Rationale.** Documentation of drift detected-and-resolved retains audit value after resolution. An auditor reading the spec learns not only what was changed but why the change was needed and what reasoning produced the patch. Collapsing to a hash pointer optimizes for length at the expense of provenance. The three-beats prose form is also stable across squash merges in a way that hash references are not — a referenced commit can disappear after rebase or repo migration; the prose survives.

**Consequences.** Specs that already passed through a §8.<final> drift cycle (policy-reader, semgrep-runner) receive companion patches in the PR that lands this ADR (see "Companion patches" below). Future specs (subagent specs in week 3 and beyond) follow this lifecycle by default. ADR-0002 Decision 5 is not amended in place; its lifecycle detail lives in this ADR, reachable from Decision 5 only via the "Related" header above.

## Aggregated consequences

- **Frame coherence.** Decisions 1 and 2 share a common subject — how specs are structured and audited — and a common consumer pair — Code at implementation time, human at review time. Consolidating them in one ADR keeps the meta-decision layer of spec authoring readable as a unit.
- **Closing of the spec-design ADR cycle.** ADR-0001 fixed workflow conventions, ADR-0002 fixed MCP conventions and deferments, and ADR-0003 fixes the dual-spec architecture and its review-pass lifecycle. Anything not registered here that affects implementation is implementation-level decision (component-internal) and lives in code, tests, or follow-up ADRs after the implementation phase.
- **Boundary with `_drafts/spec-authoring-principles.md`.** The principles draft is operational guidance — how to write a spec well. This ADR is structural decision — what specs are, and what their post-publication lifecycle is. Same boundary that ADR-0002 has with the 26 spec-authoring principles: ADR governs the shape; principles document the craft.

## Companion patches in this PR

These are concrete edits applied alongside this ADR, not deferred follow-ups. Both materialize Decision 2 for existing specs.

- **`docs/specs/policy-reader/canonical.md` §8.8.** The section currently carries the boilerplate from `_template.md` rather than three concrete beats — the spec was authored in sessions #05–#06, before the three-beats form crystallized in session #07 and was formalized in ADR-0002. Backfill three beats retrospectively, derived from the two classes of drift the cleanup PR resolved in `architecture-overview.md` (server-name canonicalization across eleven occurrences; addition of "Dimensões adicionais da Política" to the §7.3 evolution table). Closing resolution line points to `6945840` (PR #7, session #06 cleanup). The retrospective nature is declared in the section's opening paragraph.
- **`docs/specs/semgrep-runner/canonical.md` §8.<final>.** Three beats authored in session #07 are preserved verbatim. Replace the stale closing sentence ("Sync dos quatro patches… é o próximo commit nesta branch") with a resolution line pointing to `f7ec4b1` (PR #8).
