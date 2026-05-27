# ADR-0004 — uv adoption and FastMCP 3.x pin

**Status.** Accepted (session #17, 2026-05-16); retrospective ratification of de-facto state since session #14 (2026-05-12).
**Date.** 2026-05-16.
**Supersedes.** ADR-0001 §2 partially: Python version management (was "Python 3.12.7 via pyenv-win"; now Python 3.12.7 via uv) and FastMCP version (was unpinned; now `>=3.2.0,<4.0`).
**Superseded by.** Nothing.
**Related.** ADR-0001 (canonical stack framing — this ADR refines the *how* without disturbing the *why*); ADR-0008 (verification depends on the lockfile reproducibility property declared here).

## Context

ADR-0001 §2 declared the canonical stack at the framework level — Python 3.12.7, FastMCP, Pydantic, Ruff, mypy, pytest, GitHub Actions — and named pyenv-win as the Python version manager. Concrete dependency-management tooling (resolver, lockfile strategy, build backend) was left implicit, and FastMCP was not pinned to a major version.

Two pressures surfaced between #14 and #17 that closed both gaps:

1. **Empirical failure of pyenv-win (session #14, 2026-05-12).** Python 3.14 installed in parallel with 3.12.7 caused pyenv-win to fail at pinning 3.12.7 reliably. Root cause is architectural: pyenv-win operates via PATH manipulation and shims, which break on Windows 11 corporate machines under interference from Microsoft Store Python, the `py` launcher, and Anaconda installations. ADR-0001's "Python via pyenv-win" sub-decision lost empirical support.
2. **Project transitioning to team consumption.** Vilt Group colleagues are expected to use the artifact post-defense. The criterion "vai ser usado por outras pessoas na empresa" moved dependency-resolution reproducibility from "nice to have in solo-dev mode" to "load-bearing for team mode."

uv was adopted operationally during #14-#17 to address both pressures: `pyproject.toml` declares the `uv_build` backend, `.python-version` pins 3.12.7, `uv.lock` is versioned in the repository, and the existing skeleton at [src/mcp_servers/policy_reader/server.py](../../src/mcp_servers/policy_reader/server.py) imports FastMCP 3.x API. This ADR ratifies the de-facto state retroactively, supplying the rationale that operating decisions accumulated empirically.

## Decision

### 1. uv as dependency manager and Python version manager

Project uses [uv](https://docs.astral.sh/uv/) as the unified tool for:

- **Dependency management.** PEP 621 `pyproject.toml` for declarations; `uv.lock` versioned in the repository for transitive pinning; `uv sync` to materialize the environment.
- **Python version management.** `.python-version` pins 3.12.7; uv downloads the matching interpreter to `~/.local/share/uv/python/...` per user (no admin) and creates the venv against that explicit binary. No reliance on system Python, PATH manipulation, or shims.
- **Build backend.** `uv_build` declared in `[build-system]` of `pyproject.toml`.
- **CI invocation.** `uv sync` resolves identical environments in GitHub Actions and on developer machines.

**Rationale**, ordered by load-bearing weight:

- **Lockfile reproducibility (primary).** `pip install -r requirements.txt` resolves transitive dependencies against PyPI at install time; two developers running setup at different moments get different versions when upstream packages release between runs. `uv.lock` versioned + `uv sync` produces bit-identical environments across developer machines and CI. For a team-consumed artifact, non-reproducible setup is a "works on my machine" bug source disguised as transient.
- **Python version isolation per project (secondary, became primary).** Session #14 documented the pyenv-win failure described in Context above. uv does not depend on PATH inside a project — it reads `.python-version`, downloads the corresponding Python binary explicitly, and binds the venv to that exact binary. For colleagues: `git clone` followed by `uv sync` resolves Python and dependencies in one command, with zero prerequisite installation.
- **Performance (tertiary).** uv resolves and installs 10-100× faster than pip; matters in CI where every cold install costs minutes.
- **No-admin install (tertiary).** uv ships as a single binary installable without admin privileges; compatible with the corporate Windows 11 restriction declared in ADR-0001 Context.
- **CLI familiarity (tertiary).** `uv pip ...` mirrors pip syntax closely; contributors familiar with pip face a shallow learning curve.

**Portability defense.** uv consumes the standard PEP 621 `pyproject.toml`. The versioned artifact is portable: if downstream consumers (Vilt Group, UTFPR) later prefer poetry, pdm, rye, or a return to pip, `pyproject.toml` remains valid and only `uv.lock` needs translation. uv is an interface over a standard format, not a proprietary format — real lock-in surface is small. This argument is the canonical response to "but uv is one more tool to learn."

### 2. FastMCP pinned at 3.x

`pyproject.toml` declares `fastmcp>=3.2.0,<4.0`. ADR-0001 §2 specified FastMCP at the framework level without a version line; subsequent upstream evolution made 3.x the current stable line and 2.x is now in deprecated maintenance.

**Rationale.**

- 3.x is the current upstream stable line at authoring of this ADR. The skeleton in [src/mcp_servers/policy_reader/server.py](../../src/mcp_servers/policy_reader/server.py) is already written against the 3.x API (`@mcp.resource`, `@mcp.tool` decorators in their 3.x form).
- 2.x is in deprecated maintenance; no project code references it.
- The CVE survey against the 2.x line (registered as pendência since session #14) becomes informational: no 2.x code surface exists in this project to be patched. Pendência is dropped from the active list; if a future contributor argues for a 2.x downgrade, the survey can be reopened then.

## Aggregated consequences

**Positive.**

- New-contributor onboarding reduces to `git clone <repo>; cd <repo>; uv sync`. No separate Python install, no admin privileges, no pre-configuration.
- CI environments are bit-reproducible against developer machines. The "passes locally, fails in CI" class of false alarm is eliminated for dependency-resolution causes.
- `pyproject.toml` remains portable across any future tooling migration; uv adoption is interface-level, not format-level.
- FastMCP 3.x is current upstream; no migration debt accumulates from the start.
- ADR-0001 §2's framing of *why this stack at all* remains intact and citable; ADR-0004 records the *how* of management without disturbing the *why*.

**Negative.**

- Project depends on the uv binary being installable on the developer's machine. Mitigation: uv is single-binary no-admin install on Windows 11; empirically lower friction than the alternative stack (pip + pyenv-win + separate Python installer) that ADR-0001 originally implied.
- `uv.lock` is a uv-specific format. Migration to a different manager requires lockfile translation (not pyproject.toml rewrite). Acceptable given uv's interface-over-PEP-621 design.
- ADR-0001 §2 prose now drifts symbolically from the operative tooling (still mentions pyenv-win, leaves FastMCP unpinned). Drift is acknowledged in this ADR's "Supersedes" header and in `docs/process/session-handoff.md` cleanup list; substantive authority lives in ADR-0004 plus `pyproject.toml` plus `uv.lock`. Editorial sync of ADR-0001 prose is optional and may be deferred indefinitely.

## Migration path

Not applicable. The project already operates under uv (`uv_build` in `pyproject.toml`, `.python-version` pinning 3.12.7, `uv.lock` versioned, FastMCP 3.x in the dependency table and in the skeleton import). This ADR ratifies retroactively. No code change, no configuration change, no environment rebuild required at landing.

## Companion edits in this PR

- `CLAUDE.md` §"Stack (canonical)" — add a "Dependency manager" bullet citing uv and `uv.lock`; update the FastMCP line to specify 3.x.
- `docs/process/session-handoff.md` — three references removed: "ADR-0001 em débito (FastMCP 3.x; ADR-0004 reservado)" in the artifact-state list; "ADR-0004 ... decisão pendente. Bloqueia T01" in the Milestone A proposal blockers; "ADR-0001 sync com `uv.lock` real (...) ADR-0004 ainda pendente" in the editorial cleanup list. The optional editorial sync of ADR-0001 prose is preserved as a low-priority bullet without the ADR-0004 dependency.
- `docs/process/learning-log.md` session #17 entry, sub-section "Refinamento intra-sessão (continuação 2026-05-16)" — note ADR-0004 as second in-session work alongside the ADR-0008 amendment.
