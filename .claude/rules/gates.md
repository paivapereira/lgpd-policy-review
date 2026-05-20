# Gates

## Principles

1. Plan gates declare explicit halt conditions parameterized by
   empirical outcomes.
2. When a contract observable depends on framework behavior not
   covered by existing anchors, smoke-test the framework before
   committing implementation work.

## Justifications

(1) GATE halt condition pattern materialized in session #24 (T04
DD-T04-13): prompt v3 prescribed a FastMCP smoke test in Phase
1.A with an explicit halt clause ("if FastMCP rejects top-level
list, v4 of prompt before Phase 2, do NOT improvise"). Result:
empirical confirmation of route, no improvisation.

(2) Smoke test pre-implementation materialized in #24 same DD:
ad-hoc `uv run python -c '...'` confirmed FastMCP wire shape
before code committed to a structure. Without the smoke test,
the implementation would have committed to inference about
framework behavior.

## When to apply

- Any plan with phases (Phase 1.A → Phase 2 → ...) where
  Phase N+1 depends on a contract that Phase N is supposed to
  verify: declare the halt condition explicitly.
- Any framework, library, or external API whose behavior on
  this specific call shape is not already anchored by existing
  tests: run a smoke test that produces empirical evidence
  before scaling.

## How to apply

In the plan, for each gate, declare:
- The empirical question being tested.
- The mechanism (command, test, manual exercise).
- The pass condition.
- The fail action — return to plan, do not improvise.

Smoke tests do not need to be persisted artifacts. An ad-hoc
shell command is acceptable. What is persisted is the gate's
existence and its outcome.

## Reference

Anthropic Claude Code Plan Mode guidance:
"if reality doesn't match the plan, return to Plan Mode rather
than ad-libbing. The cheapest place to fix a bug is in the plan."
https://code.claude.com/docs/en/permission-modes
