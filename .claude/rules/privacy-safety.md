# Privacy and Safety

These restrictions are absolute. No `paths` frontmatter — always loaded.

## PII

Never commit real PII in fixtures, tests, examples, or documentation.
All test data must be synthetic. If the user pastes a real CPF, CNPJ,
name, address, or other identifiable data into a session, redact it
before writing to disk and warn the user.

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
