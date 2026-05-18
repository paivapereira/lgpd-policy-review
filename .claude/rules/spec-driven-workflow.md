# Spec-Driven Workflow

This project follows Spec-Driven Development. Implementation work
proceeds against written specifications under `docs/specs/` and
architectural decisions under `docs/adr/`. Architecture context lives
in `docs/architecture-overview.md`. When asked to implement a component
without a corresponding spec, confirm with the user that the spec is
intentionally absent before writing code.

## Task decomposition and verification

Per ADR-0008 (amended 2026-05-16):

- Medium-granularity tasks (1-3h each) grouped into milestones.
- Capability acceptance is bound to `docs/REQUIREMENTS.md` RFs/RNFs at
  the **milestone scope**; tasks deliver coherent function within their
  milestone without individual RF binding.
- Verification operates at two scopes:
  - **Task-level**: function-specific pytest + independent Chat review.
  - **Milestone-level**: manual exercise validating each declared RF
    acceptance criterion (Dado/Quando/Então).

## Plan-mode pattern (Fase 1 / gate / Fase 2)

For tasks with multiple design decisions or non-trivial scope, the
established pattern is:

- **Fase 1 (Plan):** read prescribed sources, enumerate DDs (decisões
  de design) with options and recommendations, produce mapping of
  acceptance scenarios to test functions, identify files in scope and
  out of scope. Stop and await OK.
- **Gate:** the user ratifies DDs (cirurgical OK is valid — ratify
  some, contest others, modify; Code does NOT proceed until OK is
  explicit).
- **Fase 2 (Implement):** Code applies the plan with gates
  pytest/ruff/mypy. Reports outcomes; does not commit PR (PR is the
  user's manual step).

Skipping the gate for complex tasks reintroduces silent scope
expansion that the pattern exists to prevent (see learning-log
entries for sessions #19, #20 for empirical baseline).

## Source-of-truth precedence

When `docs/tasks.md`, `docs/specs/<component>/canonical.md`,
`docs/specs/<component>/compact.md`, and `policy/SCHEMA.md` diverge
mechanically: the implementation adopts the side of the **real
artifacts** (`policy/policy.yaml`, `policy/clauses/`,
`policy/vocabularies/`) and annotates the divergence in
`docs/tasks.md` §Companion edits cross-doc as debt. Cross-doc sync
happens in dedicated Chat housekeeping sessions, not silently during
feature implementation.

## Companion edits cross-doc as living debt registry

`docs/tasks.md` §Companion edits cross-doc tracks debts discovered
during implementation that are not bound to the current task. Bullets
are removed only when the corresponding debt is mergeed; bullets are
added (always in a separate housekeeping PR, not during feature work)
when new debt surfaces. The list is auditable evidence of scope
discipline — it shows what was deliberately deferred vs forgotten.
