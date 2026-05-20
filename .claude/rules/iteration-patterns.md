# Iteration patterns

## Principles

1. Prompts for non-trivial Code sessions are auditable artifacts
   versioned across rounds.
2. Edits to existing artifacts (code, docs, prompts) are
   surgical: smallest diff that satisfies the change.

## Justifications

(1) Multi-round prompt iteration (v1→v2→v3) materialized across
sessions #23, #24 with consistent pattern: each round captures a
distinct class of catch (factual, structural, semantic).
Versioning the prompt as a named file preserves reviewable
change history; regenerating from scratch loses it.

(2) Surgical edits emerged in cleanup PRs across #22.5, #23
(housekeeping post-T03), #25 (housekeeping post-T04). Three-beat
form materialized: current text / why inconsistent / patch
proposed. Smaller diffs review faster and have lower defect
rate per line changed.

## When to apply (prompt versioning)

- Non-trivial Code sessions (≥2h of Code work, novel capability,
  multi-file impact): version the prompt as named files like
  `prompt-tNN-v1.md`, `prompt-tNN-v2.md`.
- Do not regenerate the prompt from scratch between rounds;
  diff-edit the previous version.

## When to apply (surgical edits)

- Doc and spec edits in housekeeping PRs.
- Any edit to text that already exists and is mostly correct.

## How to apply (surgical edits)

For each proposed change, write:
- (a) current text, quoted exactly.
- (b) why the current text is incorrect or stale.
- (c) proposed replacement text.

Use `str_replace` or equivalent narrow operations. Avoid
rewriting adjacent text that is already correct.

## Reference

Anthropic prompt engineering guidance: "treat your prompts like
small experiments where you change one variable at a time and
measure what shifts. Track which prompt version scored highest
and make that your baseline."
