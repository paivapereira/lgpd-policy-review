# CLAUDE.md — lgpd-policy-review

This file is loaded automatically at the start of every Claude Code session in this repository. It is project memory: facts and rules that apply to all work in this repo, for any contributor.

## Project identity

`lgpd-policy-review` is an academic prototype: an automated code review system that checks pull requests for compliance with a versioned LGPD (Brazilian General Data Protection Law) policy. Built on Claude Agent SDK, Claude Code, and Model Context Protocol (MCP).

The system is the bachelor thesis of João Guilherme de Mello Paiva Pereira (UTFPR, Software Engineering, 2026). It is a research artifact — not a production tool. Treat correctness, auditability, and reproducibility as primary concerns; performance optimization is out of scope unless explicitly asked.

## Repository state

The repository implements a complete minimum viable product (MVP). The three layers are built and exercised end-to-end: the versioned Policy under `policy/`, the two MCP servers under `src/mcp_servers/`, the coordinator and five subagents under `src/`, and the GitHub Actions integration under `.github/workflows/`. Consult these directories rather than assuming their contents. Directories outside MVP scope (for example, a full `benchmark/`) may still be absent; when asked to create new structure, confirm the design choice with the user before scaffolding directories or files that do not yet exist.

## Stack (canonical)

- **Language:** Python 3.12.7 (pinned via `.python-version`).
- **Dependency manager:** uv (`uv.lock` versioned in repo, `uv_build` build backend, `uv sync` for setup). See ADR-0004.
- **Agent runtime:** Claude Agent SDK (`claude-agent-sdk`), Claude Code CLI, Model Context Protocol (MCP).
- **MCP framework:** FastMCP 3.2.4 (pinned in `uv.lock`; `pyproject.toml` constraint `>=3.2.0,<4.0`) for any custom MCP server in this repo. See ADR-0004 and ADR-0001 Decision 2 (amended 2026-05-21) for the rationale of the formal pin.
- **Static analysis + Brazilian recognizers:** Semgrep 1.163.0 (via `uv tool install`, per ADR-0010), invoked through the `semgrep-runner` MCP server. Brazilian recognizers (CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde) authored as Semgrep YAML rules under `mcp_servers/semgrep_runner/rules/`. Pre-pivot the recognizers were a separate Microsoft Presidio layer; post-ADR-0010 they are part of the curated Semgrep rule set. See ADR-0001 Decision 2 (amended 2026-05-21) for the stack realignment rationale.
- **Schema validation:** Pydantic 2.13.4 (pinned in `uv.lock`; `pyproject.toml` declares `>=2.13.4` as lower bound, no upper bound).
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

## What does NOT belong in this file

- Setup instructions → `README.md`.
- Architectural decisions and their rationale → `docs/adr/NNNN-title.md`.
- Architectural overview and component contracts → `docs/architecture-overview.md`.
- Component-level specifications → `docs/specs/<component>.md`.
- Multi-step procedures, runbooks, or workflows → `.claude/skills/<skill-name>/SKILL.md`.
- Path-scoped rules (only relevant when working inside `policy/` or
  `mcp_servers/`) → nested `CLAUDE.md` in that subdirectory, OR
  `.claude/rules/<topic>.md` with `paths:` YAML frontmatter (glob
  patterns) for finer-grained scoping. The latter is preferred when
  scope is by file pattern rather than directory containment.
- Personal preferences of any individual contributor → user-scope `~/.claude/CLAUDE.md`.

## Status flags for the agent

- **Repository age:** MVP complete. Milestone A closed in session #25 (gate via MCP Inspector CLI mode, evidence in `docs/process/milestoneA.md`); Milestone B closed in session #35 (gate PASS against real stdio transport, evidence in `docs/process/milestoneB.md`); Milestone C — the multi-agent pipeline — implemented, with the Camada-3-MVP gate passing both locally and in CI (June 2026). Milestone D — the production job that runs on every pull request and the conditional merge block — remains the deferred scope.
- **Tests:** full suite passing; Ruff clean, mypy strict clean. Consult the latest gate/QA evidence in `docs/process/` for the current count rather than a number embedded here.
- **CI:** configured (GitHub Actions). The milestone gate runs in CI via `workflow_dispatch`; the `production` job triggered by pull requests is a deferred stub (`if: false`, Milestone D).
- **MCP servers:** policy-reader fully operational — 3 of 3 resources (`policy://catalog`, `policy://schema-version`, `policy://vocabularies`) + 3 of 3 tools (`get_clause`, `find_clauses_by_law_article`, `check_applicability`). semgrep-runner fully operational — `scan_diff` complete with 6 errorCodes per canonical §5, BR rule pack (6 recognizers: CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde), exercised end-to-end via FastMCP stdio transport. Windows-stdio handle inheritance hardened (`stdin=subprocess.DEVNULL` per PR #59).
- **Subagents:** implemented — Triager, Detector, Classifier, Matcher, Reporter, plus the Python coordinator. Exercised end-to-end over synthetic pull requests; Camada-3-MVP gate PASS locally and in CI.
- **Policy:** schema v0.1.0 stable; POL-000 (definitional, universal vocabulary) authored in real `policy/`; MVP ships bundled with POL-000 only, substantive clauses authored per-client.

When the agent is asked to perform an action that depends on infrastructure described above as deferred or pending (e.g., the Milestone D production job), it must say so plainly rather than fabricate.