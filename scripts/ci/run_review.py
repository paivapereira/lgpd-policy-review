"""CI edge adapter (DD-P4-3 peça a): env -> TriagerInput -> run_pipeline -> stdout.

Source-agnostic (DD-P4-1): reads the generic BASE_REF / HEAD_REF / PR_NUMBER /
REPO_URL from the environment (the workflow YAML maps github.event.* -> *_REF).
Destination-agnostic (DD-P4-2 / E1): writes the formatted summary to STDOUT only;
the YAML redirects stdout to $GITHUB_STEP_SUMMARY. No GitHub API call here — the
system is git-coupled and platform-agnostic (DD-P4-6); posting is the YAML's job
(active pull_request path is Milestone D).

Exit codes: 0 = CoordinatorReport (findings non-blocking, RNF-002); 1 =
CoordinatorError (terminal pipeline halt); 2 = bad invocation (missing/invalid env).

Run (from repo root, so the `scripts` package resolves): `uv run python -m
scripts.ci.run_review`. File-path invocation fails — the module imports its sibling
as `scripts.ci.format_summary`, which needs repo-root on sys.path (-m provides it).
Contract of record: plano Passo 4 v3 ratificado (sem spec em docs/specs/).
"""
from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import Mapping
from pathlib import Path

from coordinator.models import CoordinatorReport
from coordinator.run import run_pipeline
from subagents.triager.models import TriagerInput

from scripts.ci.format_summary import render_error_summary, render_report_summary

_REQUIRED_ENV: tuple[str, ...] = ("BASE_REF", "HEAD_REF", "PR_NUMBER", "REPO_URL")


def build_scope(env: Mapping[str, str]) -> TriagerInput:
    """Build the source-agnostic TriagerInput from generic env vars.

    Raises KeyError (missing var) or ValueError (PR_NUMBER not an int); both map to
    exit code 2 in main().
    """
    missing = [name for name in _REQUIRED_ENV if name not in env]
    if missing:
        raise KeyError(f"variaveis de ambiente ausentes: {', '.join(missing)}")
    return TriagerInput(
        pr_number=int(env["PR_NUMBER"]),
        base_ref=env["BASE_REF"],
        head_ref=env["HEAD_REF"],
        repo_url=env["REPO_URL"],
    )


async def _run(scope: TriagerInput, mcp_config_path: Path) -> tuple[int, str]:
    result = await run_pipeline(scope, mcp_config_path=mcp_config_path)
    if isinstance(result, CoordinatorReport):
        return 0, render_report_summary(result.payload)
    return 1, render_error_summary(
        result.stage, result.coverage_gap, type(result.cause).__name__
    )


def main() -> int:
    try:
        scope = build_scope(os.environ)
    except (KeyError, ValueError) as exc:
        print(f"erro de invocacao: {exc}", file=sys.stderr)
        return 2
    mcp_config_path = Path(os.environ.get("MCP_CONFIG_PATH", ".mcp.json"))
    code, summary = asyncio.run(_run(scope, mcp_config_path))
    print(summary)  # stdout only (E1); the YAML redirects to $GITHUB_STEP_SUMMARY
    return code


if __name__ == "__main__":
    raise SystemExit(main())
