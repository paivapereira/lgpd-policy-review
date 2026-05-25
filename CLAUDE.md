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

- **Repository age:** mid development — Milestone A closed in session #25
  (gate milestone-level via MCP Inspector CLI mode, evidence in
  `docs/milestoneA.md`); Milestone B closed in session #35 (gate
  milestone-level PASS empirically against stdio transport real, evidence
  in `docs/milestoneB.md`); Milestone C authoring deferred to dedicated
  Chat session post-housekeeping pre-C.
- **Tests:** 134 passing local Windows, 133 Linux/macOS (AS-14b
  skipped). Composição: 53 policy_reader + 11 semgrep_runner anchor
  (AS-1..AS-8) + 21 test_scan_diff + 49 test_recognizers_br + AS-14
  cross-platform + AS-14b Windows-only. Ruff clean, mypy strict clean.
- **CI:** not configured yet (Milestone D).
- **MCP servers:** policy-reader fully operational — 3 of 3 resources
  (`policy://catalog`, `policy://schema-version`, `policy://vocabularies`)
  + 3 of 3 tools (`get_clause`, `find_clauses_by_law_article`,
  `check_applicability`). semgrep-runner fully operational — `scan_diff`
  implementation complete with 6 errorCodes per canonical §5, BR rule
  pack (6 recognizers: CPF, CNPJ, CNH, NIS/PIS, título de eleitor,
  CNS-saúde), exercised end-to-end via FastMCP stdio transport in gate
  Milestone B PASS. Windows-stdio handle inheritance hardened
  (`stdin=subprocess.DEVNULL` per PR #59).
- **Subagents:** designed (Triager, Detector, Classifier, Matcher,
  Reporter, plus coordinator), not implemented (Milestone C).
- **Policy:** schema v0.1.0 stable; POL-000 (definitional, universal
  vocabulary) authored in real `policy/`; pack POL-001..POL-004 in
  `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/`
  exercises T02b and T03 four-verdict matrix; no substantive clauses in
  real policy yet (substantive content authored per-client, MVP ships
  bundled with POL-000 only).

When the agent is asked to perform an action that depends on
infrastructure described as "not yet", "pending", or "skeleton stub"
above, it must say so plainly rather than fabricate.