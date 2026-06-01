"""G3 capstone — live end-to-end of the coordinator `run_pipeline` (ADR-0014 D1/D2).

This is the milestone-level capstone of MC-C Phase 3: a single, opt-in
(`@pytest.mark.live`) end-to-end exercise of `coordinator.run.run_pipeline`
against the REAL Claude Agent SDK and the REAL `policy-reader` / `semgrep-runner`
MCP servers, now that the MCP-readiness fix shipped (PR-A #95). It is the
composition counterpart to the per-stage arms in
`scripts/smoke_tests/coordinator_live/g2b_mcp_middle_live.py` (granular) — together
they form GATE G3 (evidence in that directory's `RESULTS.md`).

What it proves end-to-end:
  - the full Triager -> Detector -> Classifier -> Matcher -> Reporter chain runs on
    REAL data and returns a `CoordinatorReport` (not a `CoordinatorError`);
  - the Detector actually scans (the readiness fix) and finds the synthetic `cpf`
    parameter -> a populated, list-shaped `DetectorOutput` — the FIRST live check of
    whether the SDK wraps that shape under `{"output"}` (#502/#571). The driver does
    NO unwrap (ADR-0014); if the wrapper fires it surfaces here as a
    `CoordinatorError(stage="detector")` and the ratified DD-G3-1 form (b) is applied;
  - the POL-000 `not_applicable` floor (only POL-000, definitional, is bundled in the
    real `policy/`, so check-all yields `not_applicable` citing POL-000);
  - the `counts == aggregation` invariant on the emitted report summary.

Config injection (ADR-0014 / DD-G3-2, option alpha). `run_pipeline` calls
`load_mcp_config(mcp_config_path)` ITSELF, and `scan_diff` scans `Path.cwd()`, so the
test `os.chdir`s into a synthetic-CPF git repo. Because the WHOLE pipeline runs under
that single cwd (unlike the g2b arms, which isolate per stage), BOTH spawned servers
must resolve their project env from the repo root while keeping the synthetic cwd — so
this test writes a temp `.mcp.json` whose two server commands use
`uv run --project <repo-root>` (verified in g2b: uv `--project` keeps cwd). The
`mcp_config_path` is absolute so `load_mcp_config` finds it despite the chdir.
`policy-reader` resolves `policy/` via `Path(__file__).resolve().parents[3]`
(loader.py:62 — cwd-independent), so the chdir does not break the POL-000 lookup;
`POLICY_READER_ROOT` is cleared to guarantee the fallback to that real `policy/`.

Prerequisites (opt-in). `semgrep==1.163.0` on PATH (ADR-0010); `.mcp.json` at the repo
root; and an AUTHENTICATED Claude Code session. The first two are skip-guarded below.
Authentication / the SDK's CLI discovery are NOT cheaply checkable: if the session is
unauthenticated the run surfaces as a FAILURE (a stream/stage failure), not a skip —
acceptable because this test runs only under explicit `-m live`.

Run (PowerShell, no WSL):
  uv run pytest -m live tests/coordinator/test_g3_live_e2e.py -s
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from coordinator import run as run_mod
from coordinator.models import CoordinatorReport
from subagents.triager.models import TriagerInput

_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # tests/coordinator/<file> -> repo root
_REAL_MCP_JSON = _PROJECT_ROOT / ".mcp.json"
_VERDICTS = ("compliant", "violation_candidate", "indeterminate", "not_applicable")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _head_sha(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _make_cpf_repo(parent: Path) -> tuple[Path, str, str]:
    """A git repo under `parent`: base commit clean; head commit adds
    `def collect(cpf): ...` (a `cpf` PARAMETER — what the SYNTACTIC br-cpf rule
    matches, NOT a CPF value literal; value/dict-key detection is a documented
    post-MVP gap). Mirrors the ratified g2b `_make_cpf_repo`. Returns
    (repo, base_ref, head_ref) as resolved SHAs."""
    repo = parent / "cpf-repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "g3@example.com")
    _git(repo, "config", "user.name", "g3")
    (repo / "src").mkdir()
    (repo / "src" / "reg.py").write_text("def register(user):\n    return user\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base = _head_sha(repo)
    (repo / "src" / "reg.py").write_text(
        "def register(user):\n    return user\n\n\n"
        "def collect(cpf):  # 'cpf' parameter -> matched by the syntactic br-cpf rule\n"
        "    return cpf\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "add cpf")
    head = _head_sha(repo)
    return repo, base, head


def _write_project_mcp_json(dst_dir: Path) -> Path:
    """Write a temp `.mcp.json` whose BOTH server commands use
    `uv run --project <repo-root>` (DD-G3-2 alpha): the pipeline runs every stage
    under the synthetic-repo cwd, so each spawned server must resolve its project env
    from the repo root while keeping the synthetic cwd (semgrep-runner scans it;
    policy-reader resolves `policy/` via __file__, cwd-independent)."""
    prefix = ["run", "--project", str(_PROJECT_ROOT), "python", "-m"]
    payload = {
        "mcpServers": {
            "policy-reader": {"command": "uv", "args": [*prefix, "mcp_servers.policy_reader.server"]},
            "semgrep-runner": {"command": "uv", "args": [*prefix, "mcp_servers.semgrep_runner.server"]},
        }
    }
    path = dst_dir / ".mcp.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


@pytest.mark.live
async def test_g3_run_pipeline_live_e2e(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if shutil.which("semgrep") is None:
        pytest.skip("semgrep not on PATH (ADR-0010 prereq)")
    if not _REAL_MCP_JSON.is_file():
        pytest.skip(f".mcp.json absent at repo root ({_REAL_MCP_JSON})")
    # Guarantee policy-reader falls back to the real bundled policy/ (loader.py:62,
    # __file__-based, cwd-independent) rather than a stale fixture root.
    monkeypatch.delenv("POLICY_READER_ROOT", raising=False)

    repo, base_ref, head_ref = _make_cpf_repo(tmp_path)
    mcp_json = _write_project_mcp_json(tmp_path)
    scratch = tmp_path / "scratch"
    scope = TriagerInput(
        pr_number=1,
        base_ref=base_ref,
        head_ref=head_ref,
        repo_url="https://github.com/ex/app",
    )

    cwd = Path.cwd()
    os.chdir(repo)  # scan_diff scans Path.cwd()
    start = time.perf_counter()
    try:
        result = await run_mod.run_pipeline(scope, mcp_config_path=mcp_json, scratchpad_root=scratch)
    finally:
        os.chdir(cwd)
    elapsed = time.perf_counter() - start

    # --- Composition (tolerant, acceptance-style per test-strategy.md) ---
    assert isinstance(result, CoordinatorReport), f"expected CoordinatorReport, got {result!r}"
    payload = result.payload
    findings = payload["findings"]
    # Detector found the `cpf` param -> >= 1 finding flowed through the chain. A Triager
    # `skip` would empty this -> a fixture-strength OBSERVATION (DD-G3-3), not a code bug.
    assert len(findings) >= 1, f"expected >=1 finding (run_outcome={payload['run_outcome']!r})"
    # POL-000 not_applicable floor: only POL-000 (definitional) is bundled, so check-all
    # yields not_applicable citing POL-000 (policy_reader/tools.py:300).
    assert any(
        f["policy_clause_ref"] == "POL-000" and f["verdict"] == "not_applicable" for f in findings
    ), "POL-000 not_applicable floor missing"
    # counts == aggregation invariant (run.aggregate_summary).
    summary = payload["summary"]
    counts = summary["counts"]
    assert summary["total"] == len(findings)
    assert sum(int(counts[v]) for v in _VERDICTS) == summary["total"]
    by_verdict = {v: sum(1 for f in findings if f["verdict"] == v) for v in _VERDICTS}
    assert {v: int(counts[v]) for v in _VERDICTS} == by_verdict
    # The pipeline completed a real run (not skipped, not errored).
    assert str(payload["run_outcome"]).startswith("success")

    # --- Timing OBSERVATION only (Deferral A calibration is downstream; do NOT tune here) ---
    scan_meta = (payload.get("scan_provenance") or {}).get("scan_metadata", {})
    print(
        f"\n[G3 timing] wall={elapsed:.1f}s "
        f"scan_elapsed={scan_meta.get('elapsed_seconds')!r} "
        f"files_scanned={scan_meta.get('files_scanned')!r} "
        f"findings={len(findings)} run_outcome={payload['run_outcome']!r}"
    )
