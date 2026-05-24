"""Gate Milestone B exercise script — RF-008 rule-set-axis.

Exercise artefact: spawns the semgrep-runner MCP server as a real subprocess
via FastMCP Client + stdio transport against two different rule sets, and
confirms that swapping the rule set changes the findings produced by
`scan_diff` without modifying anything under `src/` or `mcp_servers/`.

Two phases, each with its own subprocess (fresh Client, fresh transport):

  Phase 1 — baseline. Spawn server with no `SEMGREP_RUNNER_ROOT` override
  so the loader resolves the default rule set at
  `mcp_servers/semgrep_runner/rules/` (six BR recognizers). The diff
  introduces a CPF function-parameter fixture; expect rule_id `br-cpf`.

  Phase 2 — alternative rule set. Spawn server with `SEMGREP_RUNNER_ROOT`
  pointing at `tests/.../alternative_rule_set_synthetic/rules/`
  (single rule `synthetic-iban`). The diff introduces a synthetic IBAN
  function-parameter fixture; expect rule_id `synthetic-iban`.

Phase 3 evaluates five invariants over the two phase outputs (rule_id
axis, rules_version distinct, semgrep_version identical, wire is_error
False uniformly, refs resolved to 40-hex). Phase 4 prints a consolidated
JSON to stdout suitable for citation in `docs/milestoneB.md`.

This script replaces the MCP Inspector CLI attempt; the Inspector's
client-side request timeout default was too short for the Windows cold
start of `scan_diff`, and the `MCP_SERVER_REQUEST_TIMEOUT` override had
no observable effect. FastMCP `Client(timeout=...)` gives explicit
control over that timeout. Protocol fidelity is preserved — same MCP
wire format over stdio, just a Python client instead of a Node client.

Run manually (output: consolidated JSON to stdout, verbose per-phase to
stderr):

    uv run python scripts/gate_milestone_b_exercise.py

Exit code 0 if gate_verdict is PASS; 1 if FAIL.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

REPO_ROOT = Path(__file__).resolve().parents[1]

BR_FIXTURE = (
    REPO_ROOT
    / "tests"
    / "mcp_servers"
    / "semgrep_runner"
    / "fixtures"
    / "recognizers_pack_br"
    / "br_cpf_function_param.py"
)
ALT_FIXTURE = (
    REPO_ROOT
    / "tests"
    / "mcp_servers"
    / "semgrep_runner"
    / "fixtures"
    / "alternative_rule_set_synthetic"
    / "synthetic_iban_function_param.py"
)
ALT_RULES_DIR = (
    REPO_ROOT
    / "tests"
    / "mcp_servers"
    / "semgrep_runner"
    / "fixtures"
    / "alternative_rule_set_synthetic"
    / "rules"
)

# Client-side request timeout for `scan_diff`. Windows cold start of
# `semgrep --version` + the actual diff scan can take tens of seconds on
# first invocation; 180s gives ample headroom while still failing visibly
# if the server hangs.
CLIENT_TIMEOUT_S = 180.0

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=True,
    )


def _rev_parse_head(repo: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=True,
    )
    return result.stdout.strip()


def build_repo(
    prefix: str,
    head_file_src: Path,
    head_file_rel: str,
) -> tuple[Path, str, str]:
    """Build a fresh git repo in a tmpdir with a baseline + one head commit.

    The baseline commit holds a neutral `README.md`. The head commit copies
    `head_file_src` into the repo at `head_file_rel`. Returns the repo root,
    the baseline SHA, and the head SHA (both 40-hex).
    """
    repo_root = Path(tempfile.mkdtemp(prefix=prefix))
    _git(repo_root, "init", "-q")
    _git(repo_root, "config", "user.email", "gate-b@semgrep-runner.local")
    _git(repo_root, "config", "user.name", "gate-b-exercise")
    (repo_root / "README.md").write_text(
        "# gate milestone B exercise -- baseline\n",
        encoding="utf-8",
        newline="\n",
    )
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-q", "-m", "base")
    base_sha = _rev_parse_head(repo_root)

    target = repo_root / head_file_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(head_file_src, target)
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-q", "-m", "head: introduce fixture")
    head_sha = _rev_parse_head(repo_root)

    return repo_root, base_sha, head_sha


async def run_scan(
    cwd: Path,
    extra_env: dict[str, str],
    base_ref: str,
    head_ref: str,
) -> dict[str, Any]:
    """Spawn the semgrep-runner server via stdio and call `scan_diff` once.

    `cwd` becomes the subprocess working directory — `scan_diff` resolves
    `base_ref`/`head_ref` via `git rev-parse` relative to that cwd
    (canonical §4.2 caller invariant DD-T06-3/DD-T06-19).

    `extra_env` is merged over a copy of the parent process environment.
    Always strips any inherited `SEMGREP_RUNNER_ROOT` first so Phase 1 hits
    the loader default deterministically.

    Returns a dict with the wire-level capture: `structured_content` (the
    full envelope dict), `is_error` (the wire isError flag), and
    `content_text` (the first text content block, or None).
    """
    env = dict(os.environ)
    env.pop("SEMGREP_RUNNER_ROOT", None)
    env.update(extra_env)

    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "mcp_servers.semgrep_runner.server"],
        env=env,
        cwd=str(cwd),
    )
    async with Client(transport, timeout=CLIENT_TIMEOUT_S) as client:
        result = await client.call_tool(
            "scan_diff",
            {"base_ref": base_ref, "head_ref": head_ref},
            raise_on_error=False,
        )

    text_payload: str | None = None
    if result.content:
        first_block = result.content[0]
        text_payload = getattr(first_block, "text", None)

    return {
        "structured_content": result.structured_content,
        "is_error": result.is_error,
        "content_text": text_payload,
    }


def summarize_phase(
    label: str,
    base_ref: str,
    head_ref: str,
    scan: dict[str, Any],
) -> dict[str, Any]:
    """Extract the fields cited in the consolidated JSON from a scan capture."""
    sc: dict[str, Any] = scan["structured_content"] or {}
    findings: list[dict[str, Any]] = sc.get("findings") or []
    scan_metadata: dict[str, Any] = sc.get("scan_metadata") or {}
    first = findings[0] if findings else None
    location_path: str | None = None
    if first is not None:
        location = first.get("location") or {}
        location_path = location.get("path")
    return {
        "label": label,
        "rule_id": first.get("rule_id") if first is not None else None,
        "location_path": location_path,
        "rules_version": scan_metadata.get("rules_version"),
        "semgrep_version": scan_metadata.get("semgrep_version"),
        "base_ref": scan_metadata.get("base_ref") or base_ref,
        "head_ref": scan_metadata.get("head_ref") or head_ref,
        "finding_count": len(findings),
        "is_error": scan["is_error"],
    }


def check_invariants(
    p1: dict[str, Any],
    p2: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Evaluate INV-1..INV-5 over the two phase summaries.

    Returns a dict keyed by invariant name; each value is
    `{"pass": bool, "detail": str}`. All invariants are evaluated
    unconditionally — none short-circuit — so the consolidated JSON
    always carries the full diagnostic.
    """
    invariants: dict[str, dict[str, Any]] = {}

    # INV-1: rule_id distinct between phases — phase 1 br-cpf, phase 2 synthetic-iban.
    inv1 = (p1["rule_id"] == "br-cpf") and (p2["rule_id"] == "synthetic-iban")
    invariants["INV-1_rule_set_axis"] = {
        "pass": bool(inv1),
        "detail": (
            f"phase_1 rule_id={p1['rule_id']!r}, "
            f"phase_2 rule_id={p2['rule_id']!r}"
        ),
    }

    # INV-2: rules_version distinct — the deterministic SHA-256 over the
    # loaded rule set must differ between two genuinely different packs.
    inv2 = (
        p1["rules_version"] is not None
        and p2["rules_version"] is not None
        and p1["rules_version"] != p2["rules_version"]
    )
    invariants["INV-2_rules_version_distinct"] = {
        "pass": bool(inv2),
        "detail": (
            f"phase_1={p1['rules_version']}, phase_2={p2['rules_version']}"
        ),
    }

    # INV-3: semgrep_version identical — same engine across phases; only
    # the input rule set varied.
    inv3 = (
        p1["semgrep_version"] is not None
        and p2["semgrep_version"] is not None
        and p1["semgrep_version"] == p2["semgrep_version"]
    )
    invariants["INV-3_semgrep_version_identical"] = {
        "pass": bool(inv3),
        "detail": (
            f"phase_1={p1['semgrep_version']}, phase_2={p2['semgrep_version']}"
        ),
    }

    # INV-4: wire is_error uniformly False (Option B amended — successful
    # scan returns the success envelope with isError=false).
    inv4 = (p1["is_error"] is False) and (p2["is_error"] is False)
    invariants["INV-4_wire_is_error_false"] = {
        "pass": bool(inv4),
        "detail": (
            f"phase_1.is_error={p1['is_error']}, "
            f"phase_2.is_error={p2['is_error']}"
        ),
    }

    # INV-5: refs resolved to 40-char hex — `scan_diff` is contracted to
    # echo resolved SHAs (not the caller's ref shorthand) in
    # `scan_metadata`.
    refs_ok = all(
        isinstance(ref, str) and bool(SHA_RE.match(ref))
        for ref in (p1["base_ref"], p1["head_ref"], p2["base_ref"], p2["head_ref"])
    )
    invariants["INV-5_refs_resolved_to_40_hex"] = {
        "pass": bool(refs_ok),
        "detail": (
            f"phase_1 base={p1['base_ref']}, head={p1['head_ref']}; "
            f"phase_2 base={p2['base_ref']}, head={p2['head_ref']}"
        ),
    }

    return invariants


def _print_phase_verbose(label: str, repo: Path, base: str, head: str, scan: dict[str, Any]) -> None:
    """Per-phase verbose dump to stderr (keeps stdout clean for jq)."""
    print(f"[{label}] repo={repo} base={base} head={head}", file=sys.stderr)
    print(f"[{label}] structured_content:", file=sys.stderr)
    print(
        json.dumps(scan["structured_content"], indent=2, ensure_ascii=False),
        file=sys.stderr,
    )
    print(f"[{label}] is_error={scan['is_error']}", file=sys.stderr)
    print(f"[{label}] content_text={scan['content_text']!r}", file=sys.stderr)


async def main() -> int:
    # Phase 1 — baseline (default BR rule set, br_cpf fixture)
    p1_repo, p1_base, p1_head = build_repo(
        prefix="gate_b_baseline_",
        head_file_src=BR_FIXTURE,
        head_file_rel="br_cpf_function_param.py",
    )
    p1_scan = await run_scan(
        cwd=p1_repo,
        extra_env={},
        base_ref=p1_base,
        head_ref=p1_head,
    )
    _print_phase_verbose("phase 1", p1_repo, p1_base, p1_head, p1_scan)
    p1_sum = summarize_phase("phase_1_baseline_br", p1_base, p1_head, p1_scan)

    # Phase 2 — alternative rule set (synthetic_iban via SEMGREP_RUNNER_ROOT)
    p2_repo, p2_base, p2_head = build_repo(
        prefix="gate_b_alternative_",
        head_file_src=ALT_FIXTURE,
        head_file_rel="synthetic_iban_function_param.py",
    )
    p2_scan = await run_scan(
        cwd=p2_repo,
        extra_env={"SEMGREP_RUNNER_ROOT": str(ALT_RULES_DIR)},
        base_ref=p2_base,
        head_ref=p2_head,
    )
    _print_phase_verbose("phase 2", p2_repo, p2_base, p2_head, p2_scan)
    p2_sum = summarize_phase(
        "phase_2_alternative_synthetic_iban", p2_base, p2_head, p2_scan
    )

    # Phase 3 — invariants
    invariants = check_invariants(p1_sum, p2_sum)
    all_pass = all(inv["pass"] for inv in invariants.values())

    # Phase 4 — consolidated JSON to stdout
    consolidated: dict[str, Any] = {
        "phase_1_baseline_br": p1_sum,
        "phase_2_alternative_synthetic_iban": p2_sum,
        "invariants": invariants,
        "gate_verdict": "PASS" if all_pass else "FAIL",
    }
    if not all_pass:
        failed = [name for name, inv in invariants.items() if not inv["pass"]]
        consolidated["diagnostic"] = (
            "invariants that failed: " + ", ".join(failed)
        )
    print(json.dumps(consolidated, indent=2, ensure_ascii=False))
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
