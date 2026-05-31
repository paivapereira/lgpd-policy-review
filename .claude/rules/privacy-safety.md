# Privacy and Safety

These restrictions are absolute. No `paths` frontmatter — always loaded.

## PII

Never commit real PII in fixtures, tests, examples, or documentation.
All test data must be synthetic. If the user pastes a real CPF, CNPJ,
name, address, or other identifiable data into a session, redact it
before writing to disk and warn the user.

## Structured-output schemas (no PII in schema)

Structured-output schemas — the `output_format` JSON Schemas of the
subagents (Triager/Detector/Classifier/Matcher) and the `emit_report`
inputSchema — carry **category vocabulary** (tokens from
`policy://vocabularies`, e.g. `email`/`cpf` as category names), NEVER a
**personal-data value**. The Anthropic structured-output docs (Apr/2026)
warn that compiled grammars/schemas are cached without ZDR protection, so
no personal data may appear in any `enum`/`const`/`pattern`/property-name
of a schema. In this project the invariant holds by construction: enums
carry vocabulary tokens, not values; real data lives only in message
content (`snippet`, `surrounding_context`), which is ZDR-protected — never
in schema shape.

## Credentials

Never include API keys, OAuth tokens, or credentials in any committed
file. Use environment variable expansion (`${VAR_NAME}`) in
`.mcp.json` and similar config.

## Reserved paths (gitignored)

Do not commit anything under `data/raw/` or `evaluation/private/` —
those paths are gitignored and reserved for benchmarks that may
contain semi-sensitive material. Treat any file path matching those
patterns as opaque; do not read, write, or analyze contents during
operations that produce shareable output.
