# Session handoff format

## Principle

`docs/process/session-handoff.md` is a diff-log meta-document. Edits
between sessions are expressed as applicable diff blocks in
markdown code-fences, preserving cross-session blame
traceability.

## Justification

Pattern emerged in #24, replicated in #25 without friction. The
diff-block form expresses each edit as a locate-and-substitute
operation that survives squash-merge and preserves auditability
of what each session changed in the handoff state.

## When to apply

- Any modification to `docs/process/session-handoff.md` between sessions:
  express as one or more diff blocks. Do not edit in-place
  silently.
- Closure of a session that revises pendência horizons (e.g.,
  "Resolver em #N+1" lines): generate diff blocks that the next
  session pastes into the handoff document on open.

## How to apply

Each diff block follows the structure:

    ### Block N: <descriptive title>

    **Locate** the line or section that says:

```markdown
    <exact old text>
```

    **Substitute by:**

```markdown
    <new text>
```

For inserts without substitution, use **Add** with explicit
location ("after section X", "before block N") plus the text
to insert.

## Reference

No direct Anthropic equivalent. Pattern is a project-specific
extension of the community-practiced session-handoff document
pattern (compare: Claude-Handover plugin and similar tools).
