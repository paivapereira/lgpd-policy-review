# ADR-0001: Bootstrap of the lgpd-policy-review project

## Status

Accepted — 2026-05-01; Decision 2 amended in-place 2026-05-21 (session #28) to reflect stack realignment formalized in ADR-0010 (Presidio → Semgrep) and the introduction of formal version pins (`fastmcp==3.2.4`, `pydantic==2.13.4`, `mcp==1.27.1`, `semgrep==1.163.0`); Decision 3 amended in-place 2026-05-22 (session #29 housekeeping) to deprecate `LGPD-Art-7-I`-form cláusula IDs in favor of opaque `POL-NNN` IDs per ADR-0005 RF-008 (framework-agnostic IDs); Decision 4 amended in-place 2026-05-24 (session #36) to sync the three immutable domain rules with CLAUDE.md operational text (R1 substantive design change ratified by ADR-0005 D2; R2 example drift fix; R3 operational refinement); Decision 2 amended in-place 2026-05-30 (pin claude-agent-sdk==0.2.87).

## Amendment scope (2026-05-21)

Decision 2 is amended in-place. The original formulation, authored 2026-05-01 in session #01, recorded the canonical stack as the recommended package for Claude-Agent-SDK-aligned Python projects at the start of the bootstrap phase, without formal version pins and listing Microsoft Presidio with custom Brazilian recognizers as the static-analysis layer. Two subsequent decisions in later sessions invalidated the original wording without retroactive sync:

1. ADR-0010 (session #26, 2026-05-20) replaced Presidio with Semgrep as the static-analysis engine, after empirical validation in the Windows corporate-restricted environment showed Semgrep's native Windows GA (Fall 2025) made it installable without WSL or admin while Presidio's AST-aware regex+context-window model was a poorer architectural fit than Semgrep's pattern-based rules for the curated Brazilian recognizer set.
2. The empirical resolution of `uv sync` against `pyproject.toml` produced concrete version pins for FastMCP, Pydantic, and MCP runtime (the latter as transitive dependency of FastMCP), which were never formalized in this ADR. The wire-format Option B adopted in ADR-0002 §3 amendment 2026-05-17 was calibrated against the FastMCP 3.2.4 source code observed in `uv.lock`; the pin therefore carries normative weight beyond mere reproducibility — migrating off this minor version would reopen ADR-0002 §3.

Amendment landed in-place rather than as a successor ADR because (a) the original Decision 2 was framed as canonical-package adoption ("the path of lowest pedagogical friction toward the exam") rather than as a deliberated technical comparison — there is no original comparison to preserve as historical record; (b) the substantive replacements (Presidio → Semgrep, formal pins) are first-class deliberated decisions documented elsewhere (ADR-0010 + uv.lock), not novel commitments of this ADR; this amendment is a sync, not an independent decision. The pattern follows ADR-0008's in-place amendment (2026-05-16), which used the same rationale.

The original wording survives in the git history at the pre-amendment commit. Decisions 1, 4, 5, and 6 are intact (D3 amended in-place 2026-05-22, see Amendment scope (2026-05-22) below).

## Amendment scope (2026-05-24)

Decision 4 is amended in-place. All three immutable rules are replaced
by text byte-identical to CLAUDE.md §"Immutable domain rules", which
records the operational invariants actually adopted by the project.

The three rules in the pre-amendment text reflected a design state that
had been superseded by subsequent ADRs and never propagated back:

- **R1 — substantive design change, not drift.** The original
  formulation, "Human escalation on legal–policy conflict" with
  `requires_human=true` flag, presupposed a runtime mechanism in which
  the agent would arbitrate disagreements between the LGPD statute and
  an internal Policy directive. That design was abandoned in session
  #04 (2026-05-06) in favor of "no fabricated certainty" with the four
  verdicts (`compliant`, `violation_candidate`, `indeterminate`,
  `not_applicable`) — and structurally precluded altogether by ADR-0005
  Decision 2 (session #16), which made `legal_framework` a top-level
  immutable field of the loaded Policy, eliminating the category of
  "Lei vs diretriz conflict at runtime" by construction. The Policy is
  internally consistent under a single declared framework; conflict
  resolution is an authoring-time concern, not a runtime one. CLAUDE.md
  was updated in #04 to the adopted design; ADR-0001 D4 carried the
  abandoned vocabulary until this amendment.

- **R2 — drift of example, plus operational refinement.** The original
  cited `LGPD-Art-7-I` as the canonical clause ID example. The
  Amendment scope (2026-05-22) of D3 declared this form deprecated in
  favor of opaque `POL-NNN` identifiers; CLAUDE.md already uses
  `POL-007`. This amendment carries that fix into D4 and adds the
  `statutory_reference` field reference, which CLAUDE.md materializes
  as the locus of the legal-text mapping (per ADR-0005 D1 and the
  canonical schema in `policy/SCHEMA.md` §5.1).

- **R3 — technical refinement, not divergence.** The original
  prescribed schema-versioned compatibility in principle; CLAUDE.md
  materializes the two-axis form (`policy_schema_version` for
  structure, `policy_version` for content) with explicit
  `compatible_schema_range`. This amendment aligns the ADR text to the
  operational mechanism.

This sync is the "dedicated semantic deliberation Chat session
scheduled before Milestone C kickoff" referenced in the Amendment
scope (2026-05-22) below. Materialized in session #36, 2026-05-24,
before Milestone C task authoring.

Amendment landed in-place rather than as a successor ADR because (a)
two of the three rules (R2, R3) are operational refinement, not
substantive change; (b) R1 is substantive design change but the new
design has been the de facto invariant since #04 and is documented in
CLAUDE.md, learning-log #04, and ADR-0005 D2 — this amendment closes
the sync gap, not commits to a novel design. Pattern follows D2
amendment (2026-05-21) and D3 amendment (2026-05-22).

The original wording survives in the git history at the pre-amendment
commit.

## Amendment scope (2026-05-22)

Decision 3 is amended in-place. The original formulation, authored 2026-05-01 in session #01, prescribed cláusula IDs in "stable Portuguese form (e.g., `LGPD-Art-7-I`), never translated." ADR-0005 (multi-client policy architecture, session #16, 2026-05-14) formalized the property RF-008 (framework substitution without code change): a cláusula ID literally containing "LGPD" is by definition not framework-agnostic, contradicting the central thesis. The amendment realigns D3 to the opaque `POL-NNN` form already materialized in real artifacts: `policy/clauses/POL-000.yaml`, fixtures POL-001..POL-004, CLAUDE.md §"Languages", architecture-overview.md. The mapping from cláusula to legal source moves entirely to the `statutory_reference` field of each clause.

Amendment landed in-place rather than as a successor ADR because (a) the original D3 was language convention guidance, not a deliberated architectural decision; (b) the substantive replacement (framework-agnostic IDs as RF-008 property) is documented in ADR-0005 and materialized in `policy/clauses/` — this amendment is sync, not novel commitment. The pattern follows Decision 2's in-place amendment (2026-05-21) and ADR-0008's amendment (2026-05-16).

The original wording survives in the git history at the pre-amendment commit.

## Amendment scope (2026-05-30)

Decision 2 is amended in-place. `claude-agent-sdk` was named in the canonical
stack from the outset but carried no version pin, unlike every other element
(FastMCP, MCP, Pydantic, Semgrep). With the dependency now added to
`pyproject.toml` and resolved in `uv.lock` (`uv add claude-agent-sdk==0.2.87`,
Milestone C), this amendment records the pin, closing the forward-reference that
the subagent specs carry (e.g. `reporter.md` §1.5: "amendment pendente registrando
adição de `claude-agent-sdk`") and satisfying prerequisite MC-E.

The pin is `claude-agent-sdk==0.2.87` — the baseline empirically verified across
the project's smoke tests (`sdk_output_format_lockdown`, `check_applicability_48b`,
and the `ResultMessage` field introspection of this session confirming direct
`stop_reason` access). Exact-pin rather than a range: the SDK's surface is
load-bearing for the subagent contracts and moves fast, so reproducibility against
a verified version outweighs the convenience of floating to newer minors; a bump
is a deliberate act with its own verification, not a silent resolve.

Provenance note (declarative vs resolved source, per Decision 2's existing
stance): `pyproject.toml` declares the exact-pin; `uv.lock` carries the resolved
artifact set. The SDK is distributed as platform-specific wheels
(`macosx_11_0_arm64`, `macosx_11_0_x86_64`, `manylinux_2_17_aarch64`,
`manylinux_2_17_x86_64`, `win_amd64`) that bundle the Claude Code CLI binary
inside the wheel. Consequence: the lock guarantees the SDK version, and the CLI
shipped with it is the one bundled in the platform wheel resolved for the host —
no separate CLI install. The Windows host (`win_amd64`) is the development target;
CI may resolve a different platform wheel, which is expected and provenance-tracked
by `uv.lock`.

Amendment landed in-place rather than as a successor ADR because it formalizes a
pin for an element the decision already named, identical in kind to the 2026-05-21
amendment that pinned FastMCP/MCP/Pydantic/Semgrep — not a new decision. The
original wording survives in the git history at the pre-amendment commit.

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
   the first work session (see `docs/process/learning-log.md` entry
   `2026-05-01 — bootstrap-claude-md-d3` for the empirical validation of
   the CLAUDE.md adherence tests).

## Decisions at a glance

| # | Decision | Read when |
|---|----------|-----------|
| 1 | Repository: single private monorepo, MIT-licensed code | Deciding repo layout; reviewing license questions; preparing the repo for public release; choosing a license for `policy/` content |
| 2 | Canonical stack | Adding dependencies; setting up env; reviewing stack changes; introducing a new tool category |
| 3 | Languages: English for code, Portuguese for legal content | Authoring any artifact; verifying language choice; cross-reference with ADR-0006 |
| 4 | Three immutable domain rules in CLAUDE.md | Designing any agent or tool path; reviewing for invariant violation; reasoning about escalation, citation, or schema-version |
| 5 | Git workflow: Conventional Commits, feature branches, squash-merge | Opening a PR; naming a branch; writing a commit message |
| 6 | Direct-commit allowlist for two metadocuments (permanent convention) | Touching `docs/process/session-handoff.md` or `docs/process/learning-log.md`; proposing to add a third file to the allowlist |

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

Pinned to: Python 3.12.7 (via pyenv-win), `claude-agent-sdk` 0.2.87, FastMCP
3.2.4 for custom MCP servers, MCP 1.27.1 runtime (transitive via
FastMCP), Pydantic 2.13.4 for structured payload validation, Semgrep
1.163.0 (via `uv tool install`, per ADR-0010) with project-curated
Brazilian recognizers authored as Semgrep rules, Ruff (lint + format),
mypy in strict mode, pytest with pytest-asyncio, GitHub Actions for
CI/CD. Authoritative pin sources: `pyproject.toml` (declarative
ranges; `[project].name = "mcp-servers"` is the package identifier
of the root project, not a subdirectory path), `uv.lock` (resolved
versions), and ADR-0010 for Semgrep (external CLI, not in the
project's lockfile). The full canonical list lives in `CLAUDE.md`
under section "Stack (canonical)"; this ADR records *why* it was
chosen.

**How this set was assembled.** The stack was not built element by
element through isolated comparisons. It was adopted as the canonical
package recommended for Python multi-agent systems aligned with the
Claude Agent SDK and the certification exam scope. The package travels
together: `claude-agent-sdk`, FastMCP, Pydantic for schemas, pytest +
pytest-asyncio for async testing, Ruff for tooling consolidation.
Static analysis sits adjacent to this core via Semgrep — separately
versioned per ADR-0010 and installed user-scope via `uv tool install`
to keep its transitive dependency graph (67 packages) isolated from
the project's `uv.lock`. This is the path of lowest pedagogical
friction toward the exam.

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
- **FastMCP 3.2.4.** Adopted as part of the canonical Python package
  above, not as the winner of an isolated FastMCP-vs-raw-MCP-SDK
  comparison. The 3.x line is pinned because the project's wire-format
  contract (Option B per ADR-0002 §3 amendment 2026-05-17) was
  calibrated against `fastmcp/tools/base.py` as observed at this
  version. Migration off FastMCP or to a major-version-incompatible
  successor would reopen ADR-0002 §3.
- **MCP 1.27.1.** MCP protocol runtime arrives transitively via
  FastMCP; not a direct dependency in `pyproject.toml`. Pinned in
  `uv.lock` for reproducibility. The wire-level error semantics
  (Option B per ADR-0002 §3 amendment) live at this layer.
- **Pydantic 2.13.4.** Structured payload validation for tool inputs
  and outputs; the schemas in `models.py` of each MCP server are
  Pydantic models. Pin matches `pyproject.toml` lower bound exactly
  (no looser version was resolved during initial `uv sync`).
- **Semgrep 1.163.0 + Brazilian recognizers as curated rule set.**
  Semgrep was chosen over Microsoft Presidio after empirical validation
  on the Windows corporate-restricted environment (ADR-0010, session
  #26). Recognizers for CPF/CNPJ/CNH and analogous Brazilian
  identifiers are authored as Semgrep YAML rules under
  `mcp_servers/semgrep_runner/rules/`, leveraging Semgrep's AST-aware
  pattern matching rather than Presidio's regex+context-window
  architecture. The shift was driven by (a) Semgrep's native Windows
  GA (Fall 2025) removing the WSL/Docker requirement that Presidio
  did not need but that the original Presidio adoption masked as a
  non-issue; (b) the project's framing of detection as static
  analysis primitive (not text-classification NER) being a more
  natural fit for Semgrep's rule paradigm; (c) installation via
  `uv tool install` keeping Semgrep's transitive dependency graph
  (67 packages) isolated from the project's `uv.lock`. Per-call
  binary availability check at tool invocation, not startup check —
  see `docs/specs/semgrep-runner/canonical.md` §8.6 + ADR-0010.
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

**Consequences.** Moderate ecosystem lock-in to Python + Anthropic.
Any future shift (rewriting subagents in TypeScript, swapping FastMCP
for a different MCP framework, swapping Semgrep for an alternative
static analyzer) requires an explicit ADR. The Presidio → Semgrep pivot
itself was an instance of this discipline materialized as ADR-0010;
this amendment is the retroactive sync of this ADR to that decision.
The lock-in is the point: alignment with the exam stack is the priority.

### 3. Languages: English for code, Portuguese for legal content

- Source code, comments, identifiers, docstrings, commit messages, ADRs
  including this file, and `CLAUDE.md` itself: **English**.
- Policy content under `policy/`: **Brazilian Portuguese**, with
  fidelity to the LGPD statute text.
- System outputs to end users (review reports, PR comments, escalation
  messages): **Brazilian Portuguese**.
- Cláusula IDs: **opaque stable identifiers** with `POL-` prefix
  (e.g., `POL-001`), framework-agnostic. The mapping to legal source
  lives in the `statutory_reference` field of each clause, not in the
  ID itself. Amended 2026-05-22 (see "Amendment scope (2026-05-22)"
  above); original form `LGPD-Art-7-I` deprecated.

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

Three rules express the core academic thesis of the project. They are
recorded in `CLAUDE.md` under "Immutable domain rules" (always-loaded
by Claude Code, ensuring per-session visibility) and must not be
relaxed in code, prompts, or design without explicit user instruction
*and* either an in-place amendment to this Decision or a dedicated ADR
superseding it for the specific rule. The text below is byte-identical
to CLAUDE.md; parallel sync between the two documents is mandatory on
any future modification.

1. **No fabricated certainty.** When the system cannot decide
   compliance with confidence — because the verification requires
   runtime observation, upstream behavior, or context the static
   analysis of a PR cannot see — it must return the verdict
   `indeterminate` with `verification_scope` indicating the dimension
   a human reviewer must verify manually. The system never fabricates
   `compliant` or `violation_candidate` to appear conclusive. The four
   valid verdicts are `compliant`, `violation_candidate`,
   `indeterminate`, `not_applicable`.

2. **Citation of stable clause IDs.** Every finding, suggestion, or
   block produced by the agent must cite the stable `clause_id` (opaque
   identifier with `POL-` prefix, e.g., `POL-007`) of the clause it
   relies on. The `statutory_reference` field of the clause carries the
   mapping to the legal text (lei, artigo, parágrafo, inciso, alínea).
   Findings without a `clause_id` citation are invalid output and must
   be rejected by validation.

3. **Two-axis policy versioning with declared compatibility.** The
   policy is versioned along two independent axes:
   `policy_schema_version` for the structural schema of the YAML files,
   and `policy_version` for the textual content of the clauses. The
   system declares which `policy_schema_version` range it supports via
   `compatible_schema_range`. A pull request that changes the schema
   (clause structure, ID format, required fields) requires a major bump
   of `policy_schema_version`. A pull request that changes only the
   textual content of clauses (without schema change) requires at
   minimum a minor bump of `policy_version`. The system must reject at
   load time any policy whose `policy_schema_version` falls outside its
   declared compatibility range.

**Rationale.** These three rules translate the academic thesis of the
project into operational invariants. Violating them in code or design
is not a bug — it invalidates the academic contribution. Recording
them as immutable, with override gated behind ADR ceremony, prevents
accidental relaxation under implementation pressure. Maintaining the
text byte-identical to CLAUDE.md eliminates the bifurcation risk
documented in the Amendment scope (2026-05-24) above: any future
modification must be a synchronous edit to both files.

**Consequences.** The agent will refuse to take actions that violate
these rules, even when prompted — tested empirically in session #01
(see learning-log: the "Vamos adicionar Flask" pushback test, which
invoked the related stack-immutability convention from CLAUDE.md).
Cost: less flexibility during exploration, since any adjustment
requires the amendment ceremony. This cost is accepted as the price of
provenance. Mandatory parallel sync to CLAUDE.md adds editorial
overhead per amendment but eliminates the silent-bifurcation failure
mode that motivated this 2026-05-24 sync.

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

- `docs/process/session-handoff.md`
- `docs/process/learning-log.md`

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

**Consequences.** The git history of `docs/process/session-handoff.md` and
`docs/process/learning-log.md` is non-bisectable in the conventional sense
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
the decisions above and are tracked in `docs/process/session-handoff.md` for
visibility. Listed here only for cross-reference.

- `.python-version` file at repo root pinning `3.12.7`.
- Branch protection enabled on `main` via GitHub web UI (enforces
  decision 5 mechanically).
- `~/.claude/CLAUDE.md` user-scope file with personal preferences.
- Advisor outreach at UTFPR (critical deadline: ~14 days from bootstrap).
