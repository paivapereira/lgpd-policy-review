## Description

<!-- Briefly describe what this PR changes and why. -->

## Canonical ↔ Compact parity

Contract surfaces — changes here require updating both canonical and compact:

- Tool description (semantic intent — when to use, what it returns, anti-uses)
- `inputSchema` (required/optional fields, types, validation)
- Output structure (success shape)
- Error contract — any `errorCode` row in the error table
- Resource URI, payload shape, or read semantics

If this PR touches any of the above in **only one** of the two specs, the other must be updated in the same PR.

- [ ] If this PR touches a contract surface in `docs/specs/<component>/canonical.md`, the corresponding update is applied to `docs/specs/<component>/compact.md`.
- [ ] If this PR touches a contract surface in `docs/specs/<component>/compact.md`, the corresponding update is applied to `docs/specs/<component>/canonical.md`.
