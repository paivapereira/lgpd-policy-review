# Verification before inference

## Principle

Read the actual artifact before reasoning about it. Inference from
description, memory, or pattern-matching is a debt the next review
round will collect.

## Justification

Materialized empirically six times across sessions #19, #23 (×2),
#24, and #25 (×3). Each instance: a downstream review caught a
defect that direct reading at decision time would have prevented.
Pattern is operationally stable across roles (prompt authoring,
implementation, review).

## When to apply

- Before referencing field names, function signatures, or section
  numbers from a spec — read the file.
- Before asserting that a fixture, test, or doc has specific
  content — read it.
- Before deciding that a refactor preserves behavior — read the
  call sites and the tests, not the function in isolation.
- When a review round flags a missed detail, the corrective action
  is to read the artifact directly, not to argue from inference.

## How to apply

Use the `Read` tool (with `@filepath` syntax when applicable) for
files in the repo. Pull tool output for empirical questions about
runtime behavior. Quote the read content when relevant rather than
paraphrasing from memory.

## Reference

Anthropic Claude Code best-practices:
"Reference files with `@` instead of describing where code lives.
Claude reads the file before responding."
https://code.claude.com/docs/en/best-practices
