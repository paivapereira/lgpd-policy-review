# Review patterns

## Principles

1. Independent review instances catch what self-review and tests
   miss.
2. Manual exercise of integrated behavior catches debt that
   automated tests pass over.

## Justifications

(1) Multi-instance review materialized across sessions #21, #23,
#24, #25 with consistent pattern: severity decays monotonically
across rounds. Convergence on critical findings between
independent reviewers is signal of quality; divergence on
refinements is signal of coverage, not inconsistency.

(2) Milestone A gate (session #25) discovered 4 substantive
defects (#5-#8 in PR #47) against pytest 53/53 green pre-gate.
Automated tests asserted shape and structural invariants; manual
MCP Inspector exercise against declared requirements surfaced
naming, casing, and scope issues that no test was framed to
catch.

## When to apply

- After implementation, before merge: open an independent Chat
  session with no prior context for review of the diff.
- After all task-level gates pass on a milestone, before
  declaring the milestone closed: manual exercise against each
  declared requirement, via the canonical client surface for
  that requirement.

## How to apply (multi-instance review)

Open a Chat session without history. Provide only the diff and
the specification it claims to satisfy. Ask for findings ranked
by severity. Repeat with a different review trajectory
(different slice of the artifact) if the first round did not
saturate.

## How to apply (manual exercise gate)

Use the canonical client surface for the system under gate. For
MCP servers, see `mcp-testing.md`. Exercise each declared
requirement in sequence. Record commands and outputs as
reproducible evidence. Any divergence from specification is a
defect, even when tests pass.

## Reference

Anthropic Code Review (launched March 2026) implements multi-agent
review with specialized reviewers and confidence scoring.
Anthropic Claude Code best-practices, Writer/Reviewer pattern:
"A fresh context improves code review since Claude won't be
biased toward code it just wrote."
https://code.claude.com/docs/en/best-practices
