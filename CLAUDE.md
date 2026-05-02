# CLAUDE.md — lgpd-policy-review

This file is loaded automatically at the start of every Claude Code session in this repository. It is project memory: facts and rules that apply to all work in this repo, for any contributor.

## Project identity

`lgpd-policy-review` is an academic prototype: an automated code review system that checks pull requests for compliance with a versioned LGPD (Brazilian General Data Protection Law) policy. Built on Claude Agent SDK, Claude Code, and Model Context Protocol (MCP).

The system is the bachelor thesis of João Guilherme de Mello Paiva Pereira (UTFPR, Software Engineering, 2026). It is a research artifact — not a production tool. Treat correctness, auditability, and reproducibility as primary concerns; performance optimization is out of scope unless explicitly asked.

## Repository state

The repository is in early development. Most directories described in the long-term architecture (`policy/`, `mcp_servers/`, `pipeline/`, `benchmark/`, `studies/`) do not exist yet. Do not assume their contents. When asked to create new structure, confirm the design choice with the user before scaffolding directories or files that do not yet exist.

## Stack (canonical)

- **Language:** Python 3.12.7 (pinned via `.python-version`).
- **Agent runtime:** Claude Agent SDK (`claude-agent-sdk`), Claude Code CLI, Model Context Protocol (MCP).
- **MCP framework:** FastMCP for any custom MCP server in this repo.
- **PII detection:** Microsoft Presidio with custom Brazilian recognizers (CPF, CNPJ, RG, CNH).
- **Lint/format:** Ruff (replaces black, flake8, isort, pyupgrade).
- **Type check:** mypy in strict mode.
- **Tests:** pytest with `pytest-asyncio` for async tests.
- **CI/CD:** GitHub Actions.
- **Operating environment:** Windows 11 corporate (PowerShell 5.1, no admin, no WSL). Commands and paths must be Windows-native compatible.

When suggesting libraries, prefer the canonical stack above. Do not introduce alternatives (FastAPI, Flask, black, poetry, uv) without an explicit user request and a written ADR.

## Languages

- **Source code, comments, identifiers, docstrings, commit messages, ADRs, this file:** English.
- **LGPD policy content under `policy/`:** Brazilian Portuguese (legal fidelity to LGPD text).
- **System outputs to end users (review reports, PR comments, escalation messages):** Brazilian Portuguese.
- **Cláusula IDs in policy:** Portuguese-stable form (e.g., `LGPD-Art-7-I`, not translated).

## Immutable domain rules

These rules express the core thesis of the project. Violating them in code, prompts, or design invalidates the academic contribution. Do not relax or override them without explicit user instruction and an ADR.

1. **Human escalation on legal–policy conflict.** When the system detects a conflict between the LGPD statute (Lei) and an internal Policy directive, it must never decide automatically. It must emit a structured escalation flag (`requires_human=true`) with both interpretations preserved verbatim, and stop further automated action on that finding.

2. **Citation of stable clause IDs.** Every finding, suggestion, or block produced by the agent must cite the stable clause ID (e.g., `LGPD-Art-7-I`) it relies on. Findings without a clause citation are invalid output and must be rejected by validation.

3. **Schema-versioned policy compatibility.** The system declares which `policy_schema_version` range it supports. A pull request that changes the policy schema (structure of clauses, ID format, required fields) requires a major bump of `policy_schema_version`. A pull request that changes only the textual content of clauses (without schema change) requires at minimum a minor bump of the policy document version. The system must reject at load time any policy whose `schema_version` falls outside its declared compatibility range.

## Conventions

- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `ci:`, `build:`).
- **Branches:** `main` is protected; work happens in `feat/<short-description>`, `fix/<short-description>`, `docs/<short-description>`. No long-lived feature branches.
- **Pull requests:** describe what changed and why; link to ADR if applicable; include manual test notes for any change that touches policy loading, MCP server contracts, or the agent loop.

## Privacy and safety

- **Never commit real PII** in fixtures, tests, examples, or documentation. All test data must be synthetic. If a user pastes a real CPF, CNPJ, name, or address into a session, redact it before writing to disk and warn the user.
- **Never include API keys, OAuth tokens, or credentials in any committed file.** Use environment variable expansion (`${VAR_NAME}`) in `.mcp.json` and similar config.
- **Do not commit anything under `data/raw/` or `evaluation/private/`** — those paths are gitignored and reserved for benchmarks that may contain semi-sensitive material.

## What does NOT belong in this file

- Setup instructions → `README.md`.
- Architectural decisions and their rationale → `docs/adr/NNNN-title.md`.
- Multi-step procedures, runbooks, or workflows → `.claude/skills/<skill-name>/SKILL.md`.
- Path-scoped rules (only relevant when working inside `policy/` or `mcp_servers/`) → nested `CLAUDE.md` in that subdirectory.
- Personal preferences of any individual contributor → user-scope `~/.claude/CLAUDE.md`.

## Status flags for the agent

- **Repository age:** early development (no policy schema, no MCP servers, no CI).
- **Tests:** none yet — `pytest` has nothing to run.
- **CI:** not configured yet.
- **MCP servers:** none implemented yet.
- **Policy:** placeholder, v0.0.1, schema not finalized.

When the agent is asked to perform an action that depends on infrastructure described as "not yet" above, it must say so plainly rather than fabricate.