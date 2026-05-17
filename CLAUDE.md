# CLAUDE.md — lgpd-policy-review

This file is loaded automatically at the start of every Claude Code session in this repository. It is project memory: facts and rules that apply to all work in this repo, for any contributor.

## Project identity

`lgpd-policy-review` is an academic prototype: an automated code review system that checks pull requests for compliance with a versioned LGPD (Brazilian General Data Protection Law) policy. Built on Claude Agent SDK, Claude Code, and Model Context Protocol (MCP).

The system is the bachelor thesis of João Guilherme de Mello Paiva Pereira (UTFPR, Software Engineering, 2026). It is a research artifact — not a production tool. Treat correctness, auditability, and reproducibility as primary concerns; performance optimization is out of scope unless explicitly asked.

## Repository state

The repository is in early development. Most directories described in the long-term architecture (`policy/`, `mcp_servers/`, `agents/`, `benchmark/`, `.github/workflows/`) do not exist yet. Do not assume their contents. When asked to create new structure, confirm the design choice with the user before scaffolding directories or files that do not yet exist.

## Stack (canonical)

- **Language:** Python 3.12.7 (pinned via `.python-version`).
- **Dependency manager:** uv (`uv.lock` versioned in repo, `uv_build` build backend, `uv sync` for setup). See ADR-0004.
- **Agent runtime:** Claude Agent SDK (`claude-agent-sdk`), Claude Code CLI, Model Context Protocol (MCP).
- **MCP framework:** FastMCP 3.x (`>=3.2.0,<4.0`) for any custom MCP server in this repo. See ADR-0004.
- **Static analysis:** Semgrep, invoked through the `semgrep-runner` MCP server.
- **PII detection:** Microsoft Presidio with custom Brazilian recognizers (CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde).
- **Schema validation:** Pydantic 2.5+.
- **Lint/format:** Ruff (replaces black, flake8, isort, pyupgrade).
- **Type check:** mypy in strict mode.
- **Tests:** pytest with `pytest-asyncio` for async tests.
- **Evaluation framework:** Inspect AI (for benchmark validation).
- **CI/CD:** GitHub Actions.
- **Operating environment:** Windows 11 corporate (PowerShell 5.1, no admin, no WSL). Commands and paths must be Windows-native compatible.
- **Claude Code CLI version:** v2.1.123 or higher (validated locally; older versions not verified).

When suggesting libraries, prefer the canonical stack above. Do not introduce alternatives (FastAPI, Flask, black, poetry, uv) without an explicit user request and a written ADR.

## Languages

- **Source code, comments, identifiers, docstrings, commit messages, ADRs, this file:** English.
- **LGPD policy content under `policy/`:** Brazilian Portuguese (legal fidelity to LGPD text).
- **System outputs to end users (review reports, PR comments, escalation messages):** Brazilian Portuguese.
- **Cláusula IDs in policy:** opaque, stable, with `POL-` prefix (e.g., `POL-001`). The mapping from clause to legal source lives in the `statutory_reference` field of each clause, not in the ID itself.

## Immutable domain rules

These rules express the core thesis of the project. Violating them in code, prompts, or design invalidates the academic contribution. Do not relax or override them without explicit user instruction and an ADR.

1. **No fabricated certainty.** When the system cannot decide compliance with confidence — because the verification requires runtime observation, upstream behavior, or context the static analysis of a PR cannot see — it must return the verdict `indeterminate` with `verification_scope` indicating the dimension a human reviewer must verify manually. The system never fabricates `compliant` or `violation_candidate` to appear conclusive. The four valid verdicts are `compliant`, `violation_candidate`, `indeterminate`, `not_applicable`.

2. **Citation of stable clause IDs.** Every finding, suggestion, or block produced by the agent must cite the stable `clause_id` (opaque identifier with `POL-` prefix, e.g., `POL-007`) of the clause it relies on. The `statutory_reference` field of the clause carries the mapping to the legal text (lei, artigo, parágrafo, inciso, alínea). Findings without a `clause_id` citation are invalid output and must be rejected by validation.

3. **Two-axis policy versioning with declared compatibility.** The policy is versioned along two independent axes: `policy_schema_version` for the structural schema of the YAML files, and `policy_version` for the textual content of the clauses. The system declares which `policy_schema_version` range it supports via `compatible_schema_range`. A pull request that changes the schema (clause structure, ID format, required fields) requires a major bump of `policy_schema_version`. A pull request that changes only the textual content of clauses (without schema change) requires at minimum a minor bump of `policy_version`. The system must reject at load time any policy whose `policy_schema_version` falls outside its declared compatibility range.

## Conventions

- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `ci:`, `build:`).
- **Branches:** `main` is protected; work happens in `feat/<short-description>`, `fix/<short-description>`, `docs/<short-description>`. No long-lived feature branches.
- **Pull requests:** describe what changed and why; link to ADR if applicable; include manual test notes for any change that touches policy loading, MCP server contracts, or the agent loop.

## Working methodology

This project follows Spec-Driven Development. Implementation work proceeds against written specifications under `docs/specs/` and architectural decisions under `docs/adr/`. Architecture context lives in `docs/architecture-overview.md`. When asked to implement a component without a corresponding spec, confirm with the user that the spec is intentionally absent before writing code.

Task decomposition and verification follow ADR-0008 (as amended 2026-05-16): medium-granularity tasks (1-3h each) grouped into milestones. Capability acceptance is bound to REQUIREMENTS.md RFs/RNFs at the milestone scope; tasks deliver coherent function within their milestone without individual RF binding. Verification operates at two scopes — task-level (function-specific pytest + independent Chat review) and milestone-level (manual exercise validating each declared RF acceptance criterion).

## Privacy and safety

- **Never commit real PII** in fixtures, tests, examples, or documentation. All test data must be synthetic. If a user pastes a real CPF, CNPJ, name, or address into a session, redact it before writing to disk and warn the user.
- **Never include API keys, OAuth tokens, or credentials in any committed file.** Use environment variable expansion (`${VAR_NAME}`) in `.mcp.json` and similar config.
- **Do not commit anything under `data/raw/` or `evaluation/private/`** — those paths are gitignored and reserved for benchmarks that may contain semi-sensitive material.

## What does NOT belong in this file

- Setup instructions → `README.md`.
- Architectural decisions and their rationale → `docs/adr/NNNN-title.md`.
- Architectural overview and component contracts → `docs/architecture-overview.md`.
- Component-level specifications → `docs/specs/<component>.md`.
- Multi-step procedures, runbooks, or workflows → `.claude/skills/<skill-name>/SKILL.md`.
- Path-scoped rules (only relevant when working inside `policy/` or `mcp_servers/`) → nested `CLAUDE.md` in that subdirectory.
- Personal preferences of any individual contributor → user-scope `~/.claude/CLAUDE.md`.

## Status flags for the agent

- **Repository age:** early development — architecture and conceptual design closed; implementation not yet started.
- **Tests:** none yet — `pytest` has nothing to run.
- **CI:** not configured yet.
- **MCP servers:** designed (`policy-reader`, `semgrep-runner`), not implemented.
- **Subagents:** designed (Triager, Detector, Classifier, Matcher, Reporter, plus coordinator), not implemented.
- **Policy:** schema v0.1.0 conceptually closed (sessão #03), spec to be written; no clauses authored yet.

When the agent is asked to perform an action that depends on infrastructure described as "not yet" above, it must say so plainly rather than fabricate.