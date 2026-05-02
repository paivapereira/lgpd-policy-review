# ADR-0001: Bootstrap of the lgpd-policy-review project

## Status

Accepted — 2026-05-01.

## Context

This ADR records the foundational decisions made during the bootstrap phase
(week 1 of an 8–10 week implementation window) of `lgpd-policy-review`, the
software artifact for João Pereira's Software Engineering bachelor thesis at
UTFPR.

Three contextual constraints shape every decision below:

1. **Inverted priority.** The thesis exists primarily as a vehicle to study
   for the Claude Certified Architect — Foundations exam (June 2026). Every
   technical choice was evaluated first against "does this exercise concepts
   tested on the exam?" and only second against "does this make a good
   thesis?".

2. **Solo developer in a corporate Windows 11 environment.** PowerShell 5.1
   native, no WSL (corporate restriction), no local admin, Python via
   pyenv-win, Node via npm in user directory. All commands and paths must
   work in this environment.

3. **Bootstrap phase is exploratory but the workflow is already validated.**
   No production code exists yet, no tests run, no MCP server has been
   started. The first PR (initial `CLAUDE.md`) was merged via squash in
   session 1, so the branch → PR → merge → delete-branch flow is already
   tested empirically. The decisions below were made on 2026-05-01 during
   the first work session (see `docs/learning-log.md` entry
   `2026-05-01 — bootstrap-claude-md-d3` for the empirical validation of
   the CLAUDE.md adherence tests).

## Decision

### 1. Repository: single private monorepo, MIT-licensed code

Repository `paivapereira/lgpd-policy-review` on GitHub, private during
development, code licensed under MIT.

**Rationale.** Single-developer thesis project — no organizational benefit
from polyrepo splits, and a polyrepo layout would actively contradict the
project's central thesis ("Policy as a first-class artifact versioned
*together* with the system that consumes it"). Private during development
avoids premature exposure of an incomplete academic artifact.

MIT was chosen over Apache 2.0 after explicit comparison with three
factors weighed:

- No commercial intent. The artifact will be made available to Vilt Group
  and UTFPR for use after senior-developer review post-defense; no
  monetization or proprietary fork is planned.
- No patents anticipated. Apache 2.0's explicit patent grant and
  termination-on-suit clauses provide no benefit when there is no patent
  surface to protect.
- Compatibility with downstream corporate consumers. MIT appears in every
  Fortune 500 license whitelist, including Adobe (Vilt's client), making
  future reuse frictionless.

**Open question deferred.** The content under `policy/` (curated legal
text combining Lei 13.709/2018 articles with internal corporate
directives) is a textual-juridical work, not source code. MIT was written
for software and is not an appropriate license for that content. A
separate license — likely Creative Commons Attribution variant — will be
chosen in a dedicated ADR before the repository is made public or before
the policy schema reaches v1.0, whichever comes first.

**Consequences.** External code reuse is unrestricted. Policy content
reuse is undefined until the second license decision is made. The README
already flags this in its "Licença" section, which is sufficient
placeholder during private development.

### 2. Canonical stack

Pinned to: Python 3.12.7 (managed by pyenv-win), `claude-agent-sdk`,
FastMCP for any custom MCP server, Microsoft Presidio with custom
Brazilian recognizers, Ruff (lint + format), mypy in strict mode, pytest
with pytest-asyncio, GitHub Actions for CI/CD. The full canonical list
lives in `CLAUDE.md` under section "Stack (canonical)" and is the
authoritative reference; this ADR records *why* it was chosen, not what
it is.

**How this set was assembled.** The stack was not built element by
element through isolated comparisons. It was adopted as the canonical
package recommended for Python multi-agent systems aligned with the
Claude Agent SDK and the certification exam scope. The package travels
together: `claude-agent-sdk`, FastMCP, Pydantic for schemas, pytest +
pytest-asyncio for async testing, Ruff for tooling consolidation. This
is the path of lowest pedagogical friction toward the exam.

**Rationale per element.**

- **Python 3.12.7 via pyenv-win.** `claude-agent-sdk` officially supports
  Python 3.10+; 3.12 is current stable as of bootstrap. pyenv-win pins
  the version per project without admin privileges (the developer does
  not have local admin on the corporate machine). Python 3.14 was
  uninstalled to remove PATH ambiguity.
- **Claude Agent SDK + Claude Code + MCP.** The canonical Anthropic
  trio, and precisely the surface tested by the certification exam.
  Choosing alternatives (LangChain, LlamaIndex, raw Anthropic API)
  would make the project pedagogically misaligned with the exam goal.
- **FastMCP.** Adopted as part of the canonical Python package above,
  not as the winner of an isolated FastMCP-vs-raw-MCP-SDK comparison.
  A more detailed evaluation against raw SDK is deferred to the moment
  real friction surfaces (if it does).
- **Presidio with custom Brazilian recognizers.** Presidio is the
  de-facto open-source PII analyzer; its plugin model accepts custom
  recognizers, which is exactly the architectural seam needed for
  CPF/CNPJ/CNH support — the gap that justifies the academic
  contribution.
- **Ruff.** Replaces black + flake8 + isort + pyupgrade with a single
  Rust binary. Lower setup friction and faster feedback on a Windows
  machine where Python tool startup is a tax.
- **mypy strict.** The system produces structured output that
  downstream consumers (CI bots, auditors) treat as ground truth. Type
  guarantees on internal contracts are cheap insurance against silent
  contract drift.
- **pytest + pytest-asyncio.** Python testing default. The agent loop
  and MCP servers are async; pytest-asyncio is the path of least
  resistance.
- **GitHub Actions.** Repo is on GitHub; native integration; no extra
  cost; exam Scenario 5 ("Claude Code for CI/CD") assumes this exact
  CI surface.

**Consequences.** Moderate ecosystem lock-in to Python + Anthropic. Any
future shift (rewriting subagents in TypeScript, swapping FastMCP for a
different MCP framework, replacing Presidio) requires an explicit ADR.
This is a feature, not a bug: the lock-in is the point — alignment with
the exam stack is the priority.

### 3. Languages: English for code, Portuguese for legal content

- Source code, comments, identifiers, docstrings, commit messages, ADRs
  including this file, and `CLAUDE.md` itself: **English**.
- Policy content under `policy/`: **Brazilian Portuguese**, with
  fidelity to the LGPD statute text.
- System outputs to end users (review reports, PR comments, escalation
  messages): **Brazilian Portuguese**.
- Cláusula IDs: **stable Portuguese form** (e.g., `LGPD-Art-7-I`),
  never translated.

**Rationale.** Code in English is the unmarked default in the Python and
Anthropic ecosystems; deviating would create friction for any future
external reader. Policy content must preserve the exact wording of Lei
13.709/2018 and Brazilian internal directives — translating it would
destroy legal fidelity, which is the entire point. Outputs in Portuguese
match the system's intended audience. Stable cláusula IDs in Portuguese
form are the citation primitive: they appear in policy YAML, in agent
findings, and in PR comments, and must be byte-identical across all of
them.

**Consequences.** A non-Portuguese-speaking contributor can read and
modify code without barrier but cannot meaningfully review the policy
content. A Portuguese-speaking legal reviewer can validate policy
content without needing to read code. The boundary is clean and matches
the project's two-audience structure.

### 4. Three immutable domain rules in CLAUDE.md

Three rules are recorded in `CLAUDE.md` under "Immutable domain rules"
and must not be relaxed in code, prompts, or design without explicit
user instruction *and* a dedicated ADR superseding this one for that
specific rule:

1. **Human escalation on legal–policy conflict.** When the system
   detects a conflict between the LGPD statute and an internal Policy
   directive, it never decides automatically; it emits a structured
   escalation flag (`requires_human=true`) preserving both
   interpretations verbatim and stops further automated action on that
   finding.

2. **Citation of stable clause IDs.** Every finding, suggestion, or
   block produced by the agent must cite the stable clause ID (e.g.,
   `LGPD-Art-7-I`) it relies on. Findings without a clause citation
   are invalid output and must be rejected by validation.

3. **Schema-versioned policy compatibility.** The system declares which
   `policy_schema_version` range it supports. Schema-changing PRs
   require a major bump; content-only PRs require at least a minor
   bump. Policies outside the declared compatibility range are rejected
   at load time.

**Rationale.** These three rules translate the academic thesis of the
project into operational invariants. Violating them in code or design
is not a bug — it invalidates the academic contribution. Recording them
as immutable, with override gated behind a new ADR, prevents accidental
relaxation under implementation pressure.

**Consequences.** The agent will refuse to take actions that violate
these rules, even when prompted — this was tested empirically in
session 1 (see learning-log: the "Vamos adicionar Flask" pushback test,
which invoked the related stack-immutability convention from
CLAUDE.md). Cost: less flexibility during exploration, since any
adjustment requires the formal ADR ceremony. This cost is accepted as
the price of provenance.

### 5. Git workflow: Conventional Commits, feature branches, squash-merge

`main` is protected. All work happens in feature branches named
`feat/<short>`, `fix/<short>`, `docs/<short>`. Pull requests merge with
squash-merge, then the source branch is deleted. Commit messages follow
Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`,
`test:`, `ci:`, `build:`).

**Rationale.** Conventional Commits is widely adopted and
machine-readable, which keeps the door open for automated changelog
and release-note generation later without rework. Squash-merge keeps
`main` history linear and bisectable; the per-PR detail is preserved
in the closed PR's discussion view, not in the linear history.
Deleting source branches after merge avoids accumulation of dead refs.

**Consequences.** Slightly more friction than direct commits to main.
Traceability gain is meaningful: `git log main` reads as a clean,
chronological history of completed units of work, each linked to a PR
with its review trail. Validated empirically in session 1 with the
initial `CLAUDE.md` PR.

### 6. Direct-commit allowlist for two metadocuments (permanent convention)

Two specific files are committed directly to `main` without a PR, as
permanent convention rather than temporary exception:

- `docs/session-handoff.md`
- `docs/learning-log.md`

Everything else — including this ADR, future ADRs, code, configuration,
README updates, and policy content — follows the standard PR workflow
from decision 5.

**Rationale.** Both files are meta-operational documents. The
session-handoff is overwritten at the end of every session and exists
solely to brief the next conversation; reviewing it via PR provides no
signal because there is no prior version to compare meaningfully
against — the file's value is "current state", not "diff from
yesterday". The learning-log is append-only personal study notes; PR
review of personal study notes is performative ceremony without
substance. Forcing both through PR would add overhead with zero
quality gain.

**Why this is not a bootstrap exception.** An earlier draft of this
ADR framed direct commits as a "temporary bootstrap relaxation" that
would end once production code was introduced. That framing was wrong:
the rationale above (no review signal, no diff value) does not depend
on bootstrap status. It applies forever, for these two files. By the
same logic, no other file qualifies — adding a third file to this
allowlist requires a new ADR with explicit justification.

**Consequences.** The git history of `docs/session-handoff.md` and
`docs/learning-log.md` is non-bisectable in the conventional sense
(direct commits intermingled with squash-merges). Acceptable because
neither file is part of the build, tests, or runtime. All other files
remain bisectable.

## Aggregated consequences

- **Lock-in is intentional.** Stack, language, and workflow choices
  are aligned to the exam scope. The cost of pivoting away from any
  of them is meant to be high enough to require explicit deliberation.
- **Provenance is the project's currency.** ADRs, CLAUDE.md immutable
  rules, learning-log entries, stable clause IDs, schema-versioned
  policies — all of these are the same pattern repeated at different
  layers: every consequential decision must be traceable to a written
  artifact. Future ADRs should follow this template.
- **Time discipline is a hard constraint.** The 8–10 week window
  forbids scope creep. The "Fora de escopo" list in `proposta-tcc.md`
  is the guardrail. Adding anything to that list requires
  acknowledging the cost in an ADR.

## Pendências decorrentes (operational, not part of this decision)

These are not architectural decisions; they are tasks that follow from
the decisions above and are tracked in `docs/session-handoff.md` for
visibility. Listed here only for cross-reference.

- `.python-version` file at repo root pinning `3.12.7`.
- Branch protection enabled on `main` via GitHub web UI (enforces
  decision 5 mechanically).
- `~/.claude/CLAUDE.md` user-scope file with personal preferences.
- Advisor outreach at UTFPR (critical deadline: ~14 days from bootstrap).
