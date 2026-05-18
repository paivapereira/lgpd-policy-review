# Git Conventions

## Commits

Conventional Commits format: `feat:`, `fix:`, `docs:`, `chore:`,
`refactor:`, `test:`, `ci:`, `build:`.

## Branches

`main` is protected; work happens in `feat/<short-description>`,
`fix/<short-description>`, `docs/<short-description>`,
`chore/<short-description>`. No long-lived feature branches.

## Pull requests

Describe what changed and why; link to relevant ADR if applicable;
include manual test notes for any change that touches policy loading,
MCP server contracts, or the agent loop.

## PR sequencing pattern

When a feature task discovers debt that affects a shared helper or
module (e.g., render drift, naming inconsistency, framework version
mismatch), prefer a **separate PR for the cleanup** merged first, then
ramify the feature branch from corrected `main`.

Bundling cleanup into the feature PR ("PR mista" anti-pattern) breaks
blame auditability per PR — if the gate fails post-merge, investigation
has to disambiguate between cleanup and feature as the cause.

Empirical baseline:

- Sessão #19 — `docs/cleanup-cross-doc` → `main` → T01 ramifies.
- Sessão #20 — `canonical-sync-A` → `main` → T02a continues, then
  `canonical-sync-A.2` follow-up in same session for discovered
  semgrep-runner debt (separate PR, scope discipline preserved).
- Sessão #21 — `canonical-sync-B` → `main` → T02b prep.
- Sessão #22.5 — `fix/render-romano-in-T02a` → `main` → T02b ramifies
  with helper already in place.

The pattern is descriptive of a property (blame auditability per PR),
not a ritual of "fresh session per PR". If the diff is clean
(verifiable by direct Chat review), the property is satisfied
regardless of which Code session produced the diff.
