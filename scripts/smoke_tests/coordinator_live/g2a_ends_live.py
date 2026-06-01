"""G2a live arm — "close the ends" against the REAL SDK (Phase 2a).

Three ISOLATED live arms (no semgrep, no MCP middle — that is G2b):

  A. Triager proceed — real §5.1 prompt (rendered by build_triager_prompt) +
     _triager_options (system_prompt=None, DD-4) on a synthetic PII worktree,
     run through the Branch B driver. Confirms a valid TriagerDecision(proceed)
     emits live. Isolated at the driver (NOT run_pipeline) so a proceed does NOT
     fall through to the Detector (which needs semgrep = G2b).
  B. Triager skip — same, on a docs-only worktree. Expects TriagerDecision(skip).
  C. Reporter round-trip — a valid consolidated state through _run_reporter_stage:
     real query() + real in-process reporter_tools server -> emit_report dispatch
     -> handler runs the 4 cross-checks (all pass) + atomic write -> ToolUseBlock
     .input capture. Confirms emit_report round-trips live with the cross-checks
     executing and the DD-2 envelope code in place.

Run (PowerShell, no WSL):
  uv run python scripts/smoke_tests/coordinator_live/g2a_ends_live.py
"""
from __future__ import annotations

import asyncio
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

from coordinator.driver import run_branch_b_stage
from coordinator.prompts import build_triager_prompt
from coordinator.run import _run_reporter_stage, _triager_options
from subagents.reporter.tools import create_reporter_server
from subagents.triager.models import TriagerDecision, TriagerInput


def _write(root: Path, rel: str, body: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _proceed_worktree() -> Path:
    root = Path(tempfile.mkdtemp(prefix="g2a-proceed-"))
    _write(
        root,
        "src/app/registration.py",
        "from pydantic import BaseModel\n\n\n"
        "class UserRegistration(BaseModel):\n"
        "    cpf: str\n"
        "    email: str\n"
        "    full_name: str\n",
    )
    return root


def _skip_worktree() -> Path:
    root = Path(tempfile.mkdtemp(prefix="g2a-skip-"))
    _write(root, "docs/README.md", "# Project docs\n\nUpdated the overview section.\n")
    _write(root, "docs/guide.md", "# Guide\n\nHow to run the tooling.\n")
    return root


async def _run_triager_live(worktree: Path, head_ref: str) -> TriagerDecision:
    scope = TriagerInput(
        pr_number=1, base_ref="main", head_ref=head_ref, repo_url="https://github.com/example/app"
    )
    run_path = Path(tempfile.mkdtemp(prefix="g2a-triager-run-"))
    cwd = os.getcwd()
    os.chdir(worktree)  # Glob/Read operate on the synthetic worktree
    try:
        out = await run_branch_b_stage(
            stage="triager",
            prompt=build_triager_prompt(scope),
            options=_triager_options(),
            output_model=TriagerDecision,
            scratchpad_name="01-triager.json",
            run_path=run_path,
            run_id="g2a-triager",
        )
    finally:
        os.chdir(cwd)
    assert isinstance(out, TriagerDecision)
    return out


def _valid_consolidated_state(report_id: str) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "report_schema_version": "0.1.0",
        "policy_schema_version": "0.1.0",
        "policy_version": "1.2.0",
        "legal_framework": "LGPD",
        "run_outcome": "success_with_findings",
        "triager_skip_reason": None,
        "scope": {
            "pr_number": 1,
            "base_ref": "main",
            "head_ref": "feature/x",
            "repo_url": "https://github.com/example/app",
        },
        "summary": {
            "counts": {
                "compliant": 1,
                "violation_candidate": 0,
                "indeterminate": 0,
                "not_applicable": 0,
            },
            "total": 1,
        },
        "findings": [
            {
                "file": "src/app/registration.py",
                "line": 4,
                "snippet": "cpf: str",
                "rule_id": "BR-CPF",
                "data_categories": ["cpf"],
                "operation_type": "collection",
                "verdict": "compliant",
                "evidence": "Coleta de CPF precedida por guard de consentimento.",
                "policy_clause_ref": "POL-005",
                "policy_schema_version": "0.1.0",
                "policy_version": "1.2.0",
                "legal_framework": "LGPD",
            }
        ],
    }


async def _run_reporter_live() -> tuple[bool, bool, str | None]:
    run_id = str(uuid.uuid4())
    run_path = Path(tempfile.mkdtemp(prefix="g2a-reporter-run-"))
    server = create_reporter_server(run_path, run_id)
    state = _valid_consolidated_state(run_id)
    captured = await _run_reporter_stage(state, server)
    verbatim = captured == state
    file_written = (run_path / "99-report.json").exists()
    return verbatim, file_written, captured.get("report_id")


async def _main() -> int:
    print("=== G2a ARM A — Triager proceed (live) ===")
    a = await _run_triager_live(_proceed_worktree(), "feature/user-registration")
    print(f"  decision={a.decision!r} relevance_summary={a.relevance_summary!r}")
    a_ok = a.decision == "proceed"

    print("=== G2a ARM B — Triager skip (live) ===")
    b = await _run_triager_live(_skip_worktree(), "docs/update-readme")
    print(f"  decision={b.decision!r} skip_reason={b.skip_reason!r}")
    b_ok = b.decision == "skip"

    print("=== G2a ARM C — Reporter emit_report round-trip (live) ===")
    verbatim, file_written, rid = await _run_reporter_live()
    print(f"  payload captured verbatim (no recompute): {verbatim}")
    print(f"  99-report.json written (dual-sink #1)    : {file_written}")
    print(f"  captured report_id                       : {rid}")
    c_ok = verbatim and file_written

    overall = a_ok and b_ok and c_ok
    print()
    print(f"ARM A (Triager proceed): {'PASS' if a_ok else 'REVIEW (decision != proceed; calibration MC-D)'}")
    print(f"ARM B (Triager skip)   : {'PASS' if b_ok else 'REVIEW (decision != skip; calibration MC-D)'}")
    print(f"ARM C (Reporter rt)    : {'PASS' if c_ok else 'REVIEW'}")
    print(f"\nG2a ENDS: {'PASS - both Triager decisions valid live + emit_report round-trips' if overall else 'REVIEW - see arms above'}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
