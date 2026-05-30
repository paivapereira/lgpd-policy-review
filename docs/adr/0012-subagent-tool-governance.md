# ADR-0012 — Two-axis MCP tool governance in subagent configuration (capability vs availability)

**Status.** Accepted (retrospective — D1–D4 taken in session #48 and verified empirically; D5 carried forward from the documentation review of the same period; formalized here).
**Date.** 2026-05-29
**Aprovação.** Aceita ao registrar em `docs/adr/0012-subagent-tool-governance.md` via PR `docs/adr-0012`.
**Supersedes.** Nothing.
**Superseded by.** Nothing.
**Related.** ADR-0005 (Resource vs Tool boundary, Decision 4; multi-client policy; provenance triple, Decision 5). ADR-0002 (MCP conventions; error contract; deferral-with-revisit pattern A–I). ADR-0011 (Windows-stdio handle).

## Context

Milestone C composes the five subagents (Triager → Detector → Classifier → Matcher → Reporter) under a coordinator that invokes them through the Claude Agent SDK. During the authoring of `matcher.md` (session #48), applying the `tools`-field cascade across five specification loci surfaced a root question that governs every subagent configuration: how MCP tooling is granted, and on which axis.

Decisions D1–D4 below were taken mechanically in #48 and verified empirically — four distinct `tools` shapes were measured against the live `policy-reader` server and the result matched the prediction DD-M30 exactly, with no configuration revised. The evidence is persisted at `scripts/smoke_tests/check_applicability_48b/RESULTS.md`. This ADR formalizes them retrospectively.

As in ADR-0003, the temporality is mixed: D1–D4 are retrospective; the two deferrals (A, B) are forward-looking, each with a machine-checkable revisit condition rather than an arbitrary deadline.

The motivating defect: a `tools=[]` configuration on the Matcher (inherited as "Gate 6", correct for the Reporter) silently broke the Matcher's check-all loop, because the loop reads `policy://catalog` through a built-in tool that `tools=[]` hides. The break was invisible to existing tests and only appeared under the live resource-access probe (#48-b). The fix was not "add a tool" but "name the governing axis", which is what this ADR records.

## Decision

### D1 — MCP tooling is governed on two orthogonal axes

Subagent MCP tooling is governed independently on two axes:

- **Capability** (what a tool can reach) is governed by `mcp_servers` in the subagent options. **Server tools** (e.g. `mcp__policy-reader__*`, `emit_report`) are reachable as long as their server is registered, and **survive `tools=[]`**.
- **Availability** (whether a tool enters the model's context at all) is governed by the `tools` field. The resource-access **built-ins** `ReadMcpResourceTool` and `ListMcpResourcesTool` are **invisible unless listed in `tools`**, even when the server is registered and the resource is reachable.

These axes do not substitute for each other: registering a server grants reach without granting visibility of the resource built-ins. Verified empirically (#48-b; `RESULTS.md`) — four shapes against the live `policy-reader`, matching DD-M30.

### D2 — Resource built-ins are listed explicitly per resource-reading subagent

Any subagent that reads MCP resources must list `ReadMcpResourceTool` and `ListMcpResourcesTool` explicitly in its `tools` field. `allowed_tools` is a distinct field and does **not** control availability: it pre-approves invocation (denial-on-miss) but does not place a tool in context (Issue #361 — the issue's claim was true of `allowed_tools`; the defect was extending it to the `tools` field, which is a different field). Consequence: the Classifier and Matcher list both built-ins; the Reporter's `tools=[]` is correct **because** its only tool, `emit_report`, is a server tool reached via `mcp_servers`, not a built-in.

### D3 — The Resource-vs-Tool boundary holds at capability level; SDK scoping is per-server

ADR-0005 Decision 4 (Resource vs Tool) is preserved at the **capability** level, not the resource level. Read-only resources carry no decisional capability, so a subagent granted `ReadMcpResourceTool` over a server can read any resource on that server — the Classifier can read `policy://catalog`, `policy://schema-version`, and `policy://vocabularies` — without thereby gaining the power to emit a verdict or fetch clause-specific content (`get_clause` remains restricted to the Matcher as a decisional tool). The SDK's scoping granularity is **per-server-via-built-in**: there is one `ReadMcpResourceTool` gate per registered server, not one per resource URI. Lateral read access to sibling resources on the same server is therefore intentional and acceptable, not a leak — the boundary that matters (decisional capability) is held by the absence of decisional tools in the allowlist, not by per-resource gating.

### D4 — Ratified per-subagent tool shapes

| Subagent | `tools` | Notes |
| --- | --- | --- |
| Classifier | `["Read","Grep","ReadMcpResourceTool","ListMcpResourcesTool"]` | reads `policy://vocabularies` (+ lateral, per D3) |
| Matcher | `["Read","ReadMcpResourceTool","ListMcpResourcesTool"]` | + `output_format` (enum-tag); `max_turns=30` (DD-M15/M14); check-all reads `policy://catalog` |
| Reporter | `[]` | correct **only here** — `emit_report` is a server tool (D2) |
| Triager / read-only auditors | `["Read","Grep","Glob"]` | documented read-only-analysis pattern |

### D5 — Load-bearing rules are enforced at the engine/hook layer, not in prose

`CLAUDE.md` and `.claude/rules/` are best-effort context, not enforcement: to block an action regardless of what the model decides, a `PreToolUse` hook (or engine-level validation) is required. Therefore any rule whose violation must be *guaranteed-prevented* — not merely discouraged — is enforced at the engine or hook layer, not in prose. This is already partially materialized: the `policy-reader` engine hard-rejects out-of-vocabulary inputs (`INVALID_DATA_CATEGORY` / `INVALID_OPERATION`, `tools.py:268-279`) rather than relying on a CLAUDE.md instruction. Milestone C inherits this stance: load-bearing invariants over subagent behavior are placed at the deterministic layer, with CLAUDE.md/`.claude/rules/` reserved for guidance. This complements D1–D4: tool governance is not only *which* tools a subagent has, but *which layer* enforces the rules over their use.

## Deferrals (revisit-with-condition, ADR-0002 A–I pattern)

### Deferral A — `find_clauses_by_law_article` (orphan-with-formal-contract)

The tool is implemented, tested, and served by the `policy-reader` (canonical §4.2), and is granted in the Matcher's `allowed_tools` (`matcher.md:201/210`). It is **unsatisfiable on the review path**: the Matcher's `structured_context` never carries `{lei, artigo}`, and the conformance verdict is produced by the check-all loop calling `check_applicability` per candidate×clause (`matcher.md:215`, DD-M1/DD-M6). The tool serves the inverse direction — statute → clauses — for audit/discovery, a consumer the MVP does not have.

It is **orthogonal to the planned DD-M3 tool**, not subsumed by it: DD-M3 (`find_clauses_by_applicability`, `matcher.md:393`) covers the *applicability* direction (code-context → clauses) and is the planned replacement for the interim check-all mechanism — the *review* path. `find_clauses_by_law_article` covers the *statute* direction (statute → clauses) — the *audit* path. Different input, different direction, different consumer; DD-M3 landing does not retire it.

**Decision: keep the implementation.** Reverting functional, tested code mid-MVP is churn without gain; "orphan" describes the current call graph, not implementation quality. The tool is functional for audit even though no audit consumer exists yet. The only action is a documentation note on the server side (`policy-reader/canonical.md §4.2`): implemented and functional; no MVP review-path consumer; reserved for post-MVP audit.

**Revisit condition:** an audit/discovery consumer materializes → keep and document the consumer; otherwise re-evaluate removal at the post-MVP audit-feature decision.

### Deferral B — `legal_framework` consumer-side jurisdictional gate

The `legal_framework` field is fully used as **data** in four load-bearing points: it selects the `vocabularies/<framework>/` directory at load (`loader.py`); cross-validates each vocabulary file's own `framework` against the header, aborting on divergence (`loader.py`, fail-fast); enters the `policy://schema-version` handshake payload (`server.py`); and composes the provenance triple `(policy_schema_version, policy_version, legal_framework)` on every verdict (ADR-0005 Decision 5; `_envelope.py`, `models.py`).

What does **not** exist is the **gate**: comparing the received `legal_framework` against a jurisdiction the consumer accepts, and aborting if they diverge ("this server serves LGPD; refuse a request expecting GDPR"). The distinction is load-bearing: the loader enforces *internal consistency* of the Policy (`vocab.framework` vs `header.legal_framework`); no code enforces the *cross-system contract* (`header.legal_framework` vs the consumer's accepted jurisdiction). The gate is unowned; the future owner is the coordinator code (DD-M22, correction H1). It is deferred by YAGNI: in the co-versioned MVP (one release, one LGPD Policy, one server instance) the check would always pass.

**Revisit condition:** implementation of `src/coordinator/` (Milestone C). The gate is the natural home of the jurisdictional check the moment a consumer exists to perform it.

## Consequences

- Subagent configurations are now legible against the two axes (D1), so a future reader can tell whether a tool is reachable-but-hidden or simply absent. Reviewing tool grants after any change to server setup becomes an explicit maintenance obligation.
- The Resource-vs-Tool boundary is documented as capability-level and per-server (D3), closing the per-server-vs-per-resource ambiguity that recurred across the Classifier and coordinator specs.
- The Reporter's `tools=[]` is no longer a latent trap: D2 records *why* it is correct there and wrong elsewhere, so the "Gate 6" config is not copy-pasted into a resource-reading subagent again.
- Enforcement (D5) is anchored at the deterministic layer; the convergence of the immutable rules (ADR-0001 D4 ⟷ CLAUDE.md, session #36) is complemented by the principle that guaranteed compliance lives in the engine/hook, not in the converged prose.
- Two post-MVP threads (`find_clauses_by_law_article`; the `legal_framework` gate) are housed durably here, with revisit conditions, rather than buried in spec sections the coordinator implementer might not open.
- Defense artifact (Capítulo de Método): the project's specs already model, as positive exemplars, two distinctions the certification tests — protocol-vs-domain error (`isError` vs `errorCode`) and availability-vs-capability tool governance — and this ADR records them as exemplars, not gaps.
