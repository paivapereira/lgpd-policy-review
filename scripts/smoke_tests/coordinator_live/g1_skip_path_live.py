"""G1 live arm — walking-skeleton composition against the REAL SDK (skip path).

Confirms the irreducible composition the handoff flagged as un-de-risked: real
`query()` + `output_format` (Triager) -> real driver capture/validate ->
coordinator-computed consolidated state -> real in-process `reporter_tools`
factory (`create_sdk_mcp_server`) -> `emit_report` dispatch -> handler atomic
write of 99-report.json (dual-sink #1) -> `ToolUseBlock.input` capture
(dual-sink #2) -> `CoordinatorReport`.

Skip path only: Detector/Classifier/Matcher are NOT invoked, so this needs
neither the semgrep binary nor a connected policy-reader. The proceed-path live
arm (real MCP servers + semgrep) is G2b.

Run (PowerShell, no WSL):
  uv run python scripts/smoke_tests/coordinator_live/g1_skip_path_live.py
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from coordinator.models import CoordinatorError, CoordinatorReport
from coordinator.run import run_pipeline
from subagents.triager.models import TriagerInput


async def _main() -> int:
    scope = TriagerInput(
        pr_number=1,
        base_ref="main",
        head_ref="feature/skeleton-probe",
        repo_url="https://github.com/example/app",
    )
    root = Path(tempfile.mkdtemp(prefix="g1-skeleton-"))
    result = await run_pipeline(scope, scratchpad_root=root)

    if isinstance(result, CoordinatorError):
        print(f"RESULT: CoordinatorError stage={result.stage} cause={type(result.cause).__name__}")
        print(f"  detail: {result.cause}")
        print("G1 SKIP-PATH: REVIEW")
        return 1

    assert isinstance(result, CoordinatorReport)
    run_dirs = list(root.glob("run-*"))
    report_path = (run_dirs[0] / "99-report.json") if run_dirs else None
    file_written = bool(report_path and report_path.exists())
    run_outcome = result.payload.get("run_outcome")
    triager_skip_reason = result.payload.get("triager_skip_reason")

    print("RESULT: CoordinatorReport")
    print(f"  run_outcome           : {run_outcome}")
    print(f"  triager_skip_reason   : {triager_skip_reason!r}")
    print(f"  99-report.json written: {file_written} ({report_path})")
    print(f"  captured payload keys : {sorted(result.payload)}")

    ok = run_outcome == "skipped_by_triager" and file_written and "scan_provenance" not in result.payload
    print("\nG1 SKIP-PATH:", "PASS - real composition round-trips" if ok else "REVIEW - see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
