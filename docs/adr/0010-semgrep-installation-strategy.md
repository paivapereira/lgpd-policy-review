# ADR-0010: Semgrep installation strategy

## Status

Accepted (2026-05-20, session #26).

## Context

The `semgrep-runner` MCP server (specified in `docs/specs/semgrep-runner/canonical.md`, session #07) invokes Semgrep CLI as a subprocess. The component (canonical §8.6) requires Semgrep CLI to be discoverable on PATH at MCP tool invocation time. The spec sets a minimum version constraint (§2.2).

The project's development environment is Windows 11 corporate-restricted: PowerShell 5.1 native (no WSL available), no local admin account, Python 3.12.7 via pyenv-win, Node 24 via npm in user directory, `uv` as Python project manager with `uv.lock` for reproducibility.

Until Fall 2025, Semgrep did not support Windows natively — installation required WSL or Docker. This created a pending procedural decision tracked across handoffs from session #18 onward: choose among Docker Desktop, pip native, remote worker, or CI-only as the Semgrep deployment path for the project.

In session #26, two findings collapsed the decision space:

1. Semgrep released native Windows support as GA in the Fall 2025 Community Edition release. Installation on Windows via `pipx` or `uv tool install` is the officially documented path; no WSL or Docker required.
2. Empirical smoke test in the project's Windows corporate-restricted environment completed successfully: Semgrep 1.163.0 installed via `uv tool install semgrep`, `semgrep --version` returned cleanly, and `semgrep scan --config=auto src/` ran 290 rules over 9 files with 0 findings and no errors.

A separate technical consideration: `uv` provides three mechanisms for installing CLI tools — `uv tool install` (user-scope, isolated venv), `uv add --dev` (project-scope dependency in `uv.lock`), and `uvx` (ephemeral execution). The choice affects whether Semgrep transitive dependencies enter the project's lockfile, whether version control is via `uv.lock` or via documented pin, and how the executable resolves on PATH.

## Decision

Install Semgrep via `uv tool install semgrep==1.163.0` as a user-scope isolated tool.

Components of the decision:

**1. Installation mechanism: `uv tool install`, not `uv add --dev` and not `uvx`.** Semgrep is consumed by `semgrep-runner` as an external CLI tool (subprocess invocation), not as a Python library imported by the project. Tool-scope installation aligns with the consumption pattern, with the official Semgrep recommendation, and with the general convention of placing standalone developer tools (formatters, linters, scanners) in user-scope isolated environments to avoid contaminating project dependency graphs.

**2. Version pinning: 1.163.0.** Pin documented in the project README as a setup prerequisite. Version drift across machines is prevented by three independent mechanisms:
   - The README pin (human-readable contract for new contributors and evaluators).
   - Per-call binary availability check at MCP tool invocation time (canonical §8.6; the component returns `SEMGREP_BINARY_UNAVAILABLE` if the binary is not resolvable on PATH; version pin is established by this ADR).
   - Identical pin in the GitHub Actions workflow that will install Semgrep in CI (to be added in Milestone D).

**3. No Semgrep cloud integration.** `SEMGREP_APP_TOKEN` is not configured. The component operates with Semgrep OSS rules from the public registry (290 rules at the time of the empirical test). This is consistent with §7 of the `semgrep-runner` canonical spec ("Componente opera com Semgrep open-source sem login") and with the project's general posture of not introducing secrets into CI for components that do not require them.

**4. Path discovery semantics unchanged.** The `semgrep-runner` server, per canonical §8.6, resolves the Semgrep binary via standard PATH resolution at MCP tool invocation time. `uv tool install` adds the binary to the user PATH via a uv-managed shim, satisfying this requirement without further indirection in the component code.

## Consequences

**Positive:**

- Semgrep transitive dependencies (67 packages observed in the smoke test, including parsers, opentelemetry libs, pydantic, cryptography) remain isolated in the tool's venv. They do not enter the project's `uv.lock`, reducing potential conflicts with project dependencies and keeping lockfile signal-to-noise high.
- Dev local and CI converge on the same Semgrep version via the shared pin, with three independent enforcement mechanisms (README, runtime check, CI workflow).
- Alignment with Semgrep's officially documented Windows installation path reduces ongoing support burden as Semgrep evolves.
- Coherent with the project's environment posture (no admin local, no WSL) — `uv tool install` operates entirely in user-scope and requires no elevated permissions.

**Negative:**

- Semgrep version pin requires manual synchronization across README and CI workflow on upgrade. Mitigation: a future "Semgrep upgrade" task touches both files atomically; pin is in two places only, not scattered.
- Semgrep installation is not captured by `uv sync` — fresh clones require a separate `uv tool install semgrep==1.163.0` step beyond the standard `uv sync`. Mitigation: README documents this as a prerequisite alongside Python 3.12.7 via pyenv-win and Node 24, in a consolidated "Setup" section.

**Neutral:**

- Semgrep 1.163.0 carries an `mcp` package (version 1.23.3 at time of test) among its transitive dependencies. Semgrep itself ships an MCP server. This MCP runtime is isolated inside the tool's venv and does not interact with the project's MCP servers (`policy-reader`, `semgrep-runner`). Future investigation of whether Semgrep's official MCP server would be useful for the project (vs. continuing to build `semgrep-runner` as a project-owned wrapper) remains open and is out of scope for this decision.

## References

- `docs/specs/semgrep-runner/canonical.md` §2.2 (versão mínima e pin de Semgrep) and §8.6 (per-call binary availability check; `SEMGREP_BINARY_UNAVAILABLE` errorCode).
- ADR-0001 (canonical stack adoption; Semgrep introduced as part of the canonical stack, without component-specific version policy).
- Session #26 Chat record: market research on Semgrep native Windows GA, empirical smoke test in project environment, and analysis of `uv tool install` vs `uv add --dev` vs `uvx` trade-offs.
- Semgrep Community Edition Fall Release 2025: announcement of native Windows support without WSL. `semgrep.dev/blog/2025/semgrep-community-edition-fall-release-2025/`
- Anthropic `uv` documentation, "Tools" concept (`docs.astral.sh/uv/concepts/tools/`): `uv tool install` semantics and isolation guarantees.
