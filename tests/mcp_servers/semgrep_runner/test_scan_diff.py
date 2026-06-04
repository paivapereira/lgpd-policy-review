"""Acceptance scenarios for `scan_diff` (canonical §4.2-4.3, §5).

T06 AS namespace — distinct from T05's `test_bootstrap.py` namespace.
T06 AS-7 covers `SEMGREP_BINARY_UNAVAILABLE` per-call; T06 AS-8 covers
`SEMGREP_EXECUTION_FAILED`. T05's AS-7 (description byte-identity) and
T05's AS-8 (stub envelope) live in `test_bootstrap.py` and are unrelated;
T05's AS-8 is removed by T06 §3.J cleanup because the stub envelope is
gone.

Naming convention: `test_as<N>_*` consistent with T05. Anchor tests are
labelled by what they validate (`test_anchor_*`), not by AS number.

Each AS exercises one dimension of the contract. Most use real Semgrep
subprocess via `make_git_repo` + `test_rules_dir` fixtures; tests that
cannot get deterministic results from a real subprocess (AS-6 timeout,
AS-7 PATH manipulation, AS-8 specific exit code injection) use
`monkeypatch` + mocked `subprocess.run`.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from mcp.types import TextContent

from mcp_servers.semgrep_runner import server, tools
from mcp_servers.semgrep_runner._envelope import (
    _git_ref_not_found,
    _insufficient_git_history,
    _invalid_rule_set,
    _scan_timeout,
    _semgrep_binary_unavailable,
    _semgrep_execution_failed,
)
from mcp_servers.semgrep_runner._semgrep_output import (
    _SemgrepLocation,
    _SemgrepResult,
    _SemgrepResultExtra,
)
from mcp_servers.semgrep_runner.loader import load_rules, resolve_runner_root

from .conftest import _pid_alive_windows, make_git_repo, make_shallow_clone


# ---------------------------------------------------------------------------
# AS-1 — Findings emitted on real diff with real Semgrep
# ---------------------------------------------------------------------------

def test_as1_findings_emitted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
) -> None:
    """AS-1. A real git repo with a head commit introducing code that
    matches a rule produces a non-empty `findings` list. The wire
    envelope is Option B (no `errorCode`; `scan_metadata` present;
    `content[0].text` carries a Portuguese summary).

    Snippet derivation (DD-T06-23): assert `finding.snippet` reproduces
    the actual matched line from the filesystem, NOT Semgrep's
    `extra.lines = "requires login"` placeholder for OSS-no-token scans.
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files={"snippet.py": "def foo(): pass\nfoo()\n"},
    )
    monkeypatch.chdir(repo)
    state = load_rules(test_rules_dir)

    result = tools.scan_diff(base_sha, head_sha, state)

    assert result.structured_content is not None
    sc = result.structured_content
    assert "errorCode" not in sc
    assert sc["rules_version"] == state.rules_version
    assert sc["semgrep_version"]  # populated from JSON top-level
    assert sc["scan_metadata"]["base_ref"] == base_sha
    assert sc["scan_metadata"]["head_ref"] == head_sha

    findings = sc["findings"]
    assert len(findings) == 1
    finding = findings[0]
    assert "test-foo-call" in finding["rule_id"]
    assert finding["rule_severity"] == "warning"
    assert finding["rule_message"] == "foo() call detected by test rule"
    assert finding["location"]["path"] == "snippet.py"
    assert finding["location"]["start_line"] == 2
    # DD-T06-23: snippet read from filesystem, not "requires login".
    assert finding["snippet"] == "foo()"

    # content[0].text is the human-readable summary (DD-T06-9).
    assert len(result.content) == 1
    text = result.content[0].text  # type: ignore[union-attr]
    assert "1 candidato" in text
    assert "snippet.py:2" in text


# ---------------------------------------------------------------------------
# AS-2 — Empty findings list on diff with no rule matches (normal state)
# ---------------------------------------------------------------------------

def test_as2_empty_findings_normal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
) -> None:
    """AS-2. A diff that introduces code which does NOT match any rule
    returns success with `findings: []`. Empty list is canonical normal
    state per §5.3, not an error. `scan_metadata` is still populated.
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files={"snippet.py": "def bar(): pass\nbar()\n"},
    )
    monkeypatch.chdir(repo)
    state = load_rules(test_rules_dir)

    result = tools.scan_diff(base_sha, head_sha, state)

    assert result.structured_content is not None
    sc = result.structured_content
    assert "errorCode" not in sc
    assert sc["findings"] == []
    assert sc["scan_metadata"]["base_ref"] == base_sha
    assert sc["scan_metadata"]["head_ref"] == head_sha

    text = result.content[0].text  # type: ignore[union-attr]
    assert "Nenhum candidato detectado" in text


# ---------------------------------------------------------------------------
# AS-3 — Empty diff (base == head) returns success with empty findings
# ---------------------------------------------------------------------------

def test_as3_empty_diff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
) -> None:
    """AS-3. When `base_ref == head_ref` (empty diff), Semgrep runs but
    finds nothing to scan; the component returns success with
    `findings: []`. Canonical §5.3 second bullet: empty diff is normal,
    not an error.
    """
    repo, base_sha, _ = make_git_repo(
        tmp_path,
        base_files={"snippet.py": "def foo(): pass\nfoo()\n"},
        head_files={},  # no head commit; head_sha == base_sha
    )
    monkeypatch.chdir(repo)
    state = load_rules(test_rules_dir)

    result = tools.scan_diff(base_sha, base_sha, state)

    assert result.structured_content is not None
    sc = result.structured_content
    assert "errorCode" not in sc
    assert sc["findings"] == []
    assert sc["scan_metadata"]["base_ref"] == base_sha
    assert sc["scan_metadata"]["head_ref"] == base_sha


# ---------------------------------------------------------------------------
# AS-4 — GIT_REF_NOT_FOUND parametrized over (base_ref, head_ref)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("which_ref", ["base_ref", "head_ref"])
def test_as4_git_ref_not_found(
    which_ref: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
) -> None:
    """AS-4. Passing a syntactically-valid string that does not resolve
    to a commit in the current repo returns `GIT_REF_NOT_FOUND` with
    `details.ref_param` discriminating which input failed (base_ref vs
    head_ref). Parametrized over both refs to ensure ordering of the
    two checks does not mask one direction.

    No Semgrep subprocess invoked here (ref resolution short-circuits).
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files={"snippet.py": "def foo(): pass\nfoo()\n"},
    )
    monkeypatch.chdir(repo)
    state = load_rules(test_rules_dir)

    bad = "nonexistent_ref_abc123def"
    if which_ref == "base_ref":
        result = tools.scan_diff(bad, head_sha, state)
    else:
        result = tools.scan_diff(base_sha, bad, state)

    assert result.structured_content is not None
    sc = result.structured_content
    assert sc["errorCode"] == "GIT_REF_NOT_FOUND"
    assert sc["isRetryable"] is False
    assert sc["details"]["ref_param"] == which_ref
    assert sc["details"]["ref_value"] == bad
    assert "hint" in sc["details"]
    assert result.content[0].text == sc["message"]  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# AS-5 — INSUFFICIENT_GIT_HISTORY on shallow repo (proactive layer)
# ---------------------------------------------------------------------------

def test_as5_insufficient_git_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
) -> None:
    """AS-5. A shallow clone (`--depth=1`) triggers the proactive
    `is-shallow-repository` check (DD-T06-6 layer 1) and returns
    `INSUFFICIENT_GIT_HISTORY` before any subprocess Semgrep invocation.
    Empirically validated against `file:///` clone in pre-flight 3.G.
    """
    deep_repo, _, _ = make_git_repo(
        tmp_path,
        base_files={"a.py": "x = 1\n"},
        head_files={"b.py": "y = 2\n"},
    )
    shallow = make_shallow_clone(deep_repo, tmp_path)
    monkeypatch.chdir(shallow)
    state = load_rules(test_rules_dir)

    result = tools.scan_diff("HEAD", "HEAD", state)

    assert result.structured_content is not None
    sc = result.structured_content
    assert sc["errorCode"] == "INSUFFICIENT_GIT_HISTORY"
    assert sc["isRetryable"] is False
    assert sc["details"]["hint"] == "increase actions/checkout fetch-depth"


# ---------------------------------------------------------------------------
# AS-6 — SCAN_TIMEOUT via mocked subprocess raising TimeoutExpired
# ---------------------------------------------------------------------------

def test_as6_scan_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
) -> None:
    """AS-6. When Semgrep exceeds `SEMGREP_RUNNER_TIMEOUT_SECONDS`,
    `subprocess.run` raises `TimeoutExpired`; `scan_diff` catches it
    and emits `SCAN_TIMEOUT` (system, retryable; canonical §5.4).
    `details.partial_findings_discarded` is `True` per
    all-or-nothing semantics (canonical §7).

    Real Semgrep cannot reliably emit a timeout in <2s; we mock
    `subprocess.run` to inject `TimeoutExpired` selectively for the
    Semgrep call (git rev-parse / is-shallow calls pass through).
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files={"snippet.py": "def foo(): pass\nfoo()\n"},
    )
    monkeypatch.chdir(repo)
    state = load_rules(test_rules_dir)
    monkeypatch.setenv("SEMGREP_RUNNER_TIMEOUT_SECONDS", "1")

    real_run = subprocess.run

    def mocked_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if cmd and "semgrep" in str(cmd[0]).lower():
            raise subprocess.TimeoutExpired(cmd, 1)
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "run", mocked_run)

    result = tools.scan_diff(base_sha, head_sha, state)

    assert result.structured_content is not None
    sc = result.structured_content
    assert sc["errorCode"] == "SCAN_TIMEOUT"
    assert sc["isRetryable"] is True
    assert sc["details"]["timeout_seconds"] == 1
    assert sc["details"]["partial_findings_discarded"] is True


# ---------------------------------------------------------------------------
# AS-7 — SEMGREP_BINARY_UNAVAILABLE (per-call, not startup abort)
# ---------------------------------------------------------------------------

def test_as7_semgrep_binary_unavailable_per_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
) -> None:
    """AS-7 (T06). When `shutil.which("semgrep")` returns `None` at
    invocation time (PATH cleared), the tool returns
    `SEMGREP_BINARY_UNAVAILABLE` per-call without aborting the server
    (canonical §8.6, ADR-0010). `searched_paths` carries the PATH
    components inspected, for operator diagnostic.

    Distinct from T05's AS-7 in `test_bootstrap.py` which asserts the
    tool description byte-identity (an invariant T06 must preserve).
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files={"snippet.py": "def foo(): pass\nfoo()\n"},
    )
    monkeypatch.chdir(repo)
    state = load_rules(test_rules_dir)
    monkeypatch.setenv("PATH", "")

    result = tools.scan_diff(base_sha, head_sha, state)

    assert result.structured_content is not None
    sc = result.structured_content
    assert sc["errorCode"] == "SEMGREP_BINARY_UNAVAILABLE"
    assert sc["isRetryable"] is False
    assert isinstance(sc["details"]["searched_paths"], list)


# ---------------------------------------------------------------------------
# AS-8 — SEMGREP_EXECUTION_FAILED on generic non-mapped exit code
# ---------------------------------------------------------------------------

def test_as8_semgrep_execution_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
) -> None:
    """AS-8 (T06). When Semgrep exits with a non-mapped fatal code
    (e.g., 2 under X1 mapping per GATE 1), the tool emits
    `SEMGREP_EXECUTION_FAILED` (system, retryable) with `exit_code` and
    `stderr_excerpt` in `details`. Distinct from T05's AS-8 in
    `test_bootstrap.py` (the stub envelope, removed by T06 §3.J).

    X1 mapping: exits not in {0, 7, 8} fall through to
    SEMGREP_EXECUTION_FAILED. Exit 2 is the canonical example because
    pre-flight 3.E observed it for invalid pattern syntax (the
    granularity loss documented in canonical §5.4 row
    SEMGREP_EXECUTION_FAILED).
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files={"snippet.py": "def foo(): pass\nfoo()\n"},
    )
    monkeypatch.chdir(repo)
    state = load_rules(test_rules_dir)

    real_run = subprocess.run

    def mocked_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if cmd and "semgrep" in str(cmd[0]).lower():
            return subprocess.CompletedProcess(
                args=cmd, returncode=2,
                stdout="", stderr="fatal: semgrep-core crashed unexpectedly",
            )
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "run", mocked_run)

    result = tools.scan_diff(base_sha, head_sha, state)

    assert result.structured_content is not None
    sc = result.structured_content
    assert sc["errorCode"] == "SEMGREP_EXECUTION_FAILED"
    assert sc["isRetryable"] is True
    assert sc["details"]["exit_code"] == 2
    assert "semgrep-core crashed" in sc["details"]["stderr_excerpt"]


# ---------------------------------------------------------------------------
# AS-9 — INVALID_RULE_SET on exit 7 (unparseable YAML / missing config)
# ---------------------------------------------------------------------------

def test_as9_invalid_rule_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
) -> None:
    """AS-9. When Semgrep exits with code 7 or 8 (rule set non-usable
    under X1 mapping per GATE 1 ratification — exits 7 covers
    config-malformed / unparseable-YAML / missing-config collapsed by
    Semgrep into "invalid configuration", exit 8 covers
    unsupported-language), the tool emits `INVALID_RULE_SET` (system,
    non-retryable).

    Mocked exit 7 with realistic JSON stdout (errors[].code=7) to
    validate the X1 mapping deterministically. Real broken rules
    produce the same exit per pre-flight 3.E observation.
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files={"snippet.py": "def foo(): pass\nfoo()\n"},
    )
    monkeypatch.chdir(repo)
    state = load_rules(test_rules_dir)

    real_run = subprocess.run

    def mocked_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if cmd and "semgrep" in str(cmd[0]).lower():
            return subprocess.CompletedProcess(
                args=cmd, returncode=7,
                stdout=(
                    '{"version":"1.163.0","results":[],"errors":'
                    '[{"code":7,"type":"SemgrepError",'
                    '"message":"invalid configuration file found"}],'
                    '"paths":{"scanned":[]}}'
                ),
                stderr="",
            )
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "run", mocked_run)

    result = tools.scan_diff(base_sha, head_sha, state)

    assert result.structured_content is not None
    sc = result.structured_content
    assert sc["errorCode"] == "INVALID_RULE_SET"
    assert sc["isRetryable"] is False
    assert sc["details"]["exit_code"] == 7
    # DD-T06-22 enrichment: stdout JSON errors[].message preferred over
    # raw stderr (empty here) in details.stderr_excerpt.
    assert "invalid configuration" in sc["details"]["stderr_excerpt"]


# ---------------------------------------------------------------------------
# AS-13 — Subprocess cleanup verified after TimeoutExpired (Windows-only)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# AS-12 — --baseline-commit filters out preexisting findings
# ---------------------------------------------------------------------------

def test_as12_baseline_commit_filters_preexisting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
) -> None:
    """AS-12. Matching code present at `base_ref` (before the diff)
    must NOT appear in findings — Semgrep's `--baseline-commit` filter
    is the mechanism that delivers diff-aware semantics. Matching code
    introduced at `head_ref` (the diff itself) DOES appear.

    Fixture: `existing.py` carries `foo()` at base (matches test rule
    but should be filtered). `new.py` introduces another `foo()` at
    head (matches and should appear). Result: findings include only
    `new.py`, not `existing.py`.
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"existing.py": "def foo(): pass\nfoo()\n"},
        head_files={"new.py": "def foo(): pass\nfoo()\n"},
    )
    monkeypatch.chdir(repo)
    state = load_rules(test_rules_dir)

    result = tools.scan_diff(base_sha, head_sha, state)

    assert result.structured_content is not None
    sc = result.structured_content
    assert "errorCode" not in sc
    paths = [f["location"]["path"] for f in sc["findings"]]
    assert "new.py" in paths
    assert "existing.py" not in paths


# ---------------------------------------------------------------------------
# AS-13 — Subprocess cleanup verified after TimeoutExpired (Windows-only)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    sys.platform != "win32",
    reason="AS-13 cleanup verification uses tasklist /FI (Windows-only); "
    "production target is Windows 11 corporate per CLAUDE.md §Stack.",
)
def test_as13_no_zombie_subprocess_post_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AS-13. Asserts the framework invariant `scan_diff` relies on:
    `subprocess.run` kills its child on `TimeoutExpired` (CPython's
    Popen.kill → `TerminateProcess` on Windows). DD-T06-1 ratification
    via pre-flight 3.H observed zero zombies; this test pins the
    invariant against future regression.

    Mechanism: monkeypatch `subprocess.Popen` with a factory that
    records spawned PIDs into a list. After triggering
    `TimeoutExpired` on a long-running Python subprocess via
    `subprocess.run(timeout=1)`, the recorded PID is verified
    non-alive via `_pid_alive_windows` (DD-T06-16). Tests the
    mechanism scan_diff inherits, not scan_diff itself — keeps the
    test deterministic without requiring a slow real Semgrep run.
    """
    captured_pids: list[int] = []
    real_popen = subprocess.Popen

    def capturing_popen(*args: Any, **kwargs: Any) -> subprocess.Popen[Any]:
        proc = real_popen(*args, **kwargs)
        captured_pids.append(proc.pid)
        return proc

    monkeypatch.setattr(subprocess, "Popen", capturing_popen)

    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=1,
        )

    assert len(captured_pids) == 1
    pid = captured_pids[0]
    time.sleep(0.5)  # allow Windows process table to update post-kill
    assert not _pid_alive_windows(pid)


# ---------------------------------------------------------------------------
# AS-10 — Provenance trinque populated correctly in success payload
# ---------------------------------------------------------------------------

def test_as10_provenance_in_scan_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
) -> None:
    """AS-10. Provenance fields populated per canonical §6:
    `rules_version` and `semgrep_version` are top-level static
    provenance (rule set hash + Semgrep binary version). `base_ref`,
    `head_ref` are 40-char hex SHA-1 resolved via `git rev-parse`,
    NOT the raw input refs (so branch names / short refs become
    auditable commit hashes). `files_scanned` and `elapsed_seconds`
    are populated.
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files={"snippet.py": "def foo(): pass\nfoo()\n"},
    )
    monkeypatch.chdir(repo)
    state = load_rules(test_rules_dir)

    # Pass a non-SHA ref (branch name "HEAD") to assert SHA resolution.
    result = tools.scan_diff("HEAD~1", "HEAD", state)

    assert result.structured_content is not None
    sc = result.structured_content
    assert "errorCode" not in sc

    # Top-level static provenance.
    assert sc["rules_version"] == state.rules_version
    assert sc["rules_version"].startswith("sha256:")
    assert sc["semgrep_version"]  # populated from Semgrep JSON top-level
    sha_pattern = re.compile(r"^[a-f0-9]{40}$")

    # Nested per-scan provenance — base_ref/head_ref are RESOLVED SHA,
    # not the input "HEAD~1"/"HEAD".
    assert sha_pattern.match(sc["scan_metadata"]["base_ref"])
    assert sha_pattern.match(sc["scan_metadata"]["head_ref"])
    assert sc["scan_metadata"]["base_ref"] == base_sha
    assert sc["scan_metadata"]["head_ref"] == head_sha
    assert isinstance(sc["scan_metadata"]["files_scanned"], int)
    assert sc["scan_metadata"]["files_scanned"] >= 0
    assert isinstance(sc["scan_metadata"]["elapsed_seconds"], (int, float))
    assert sc["scan_metadata"]["elapsed_seconds"] >= 0


# ---------------------------------------------------------------------------
# AS-11 — Option B wire format end-to-end via in-memory FastMCP Client
# ---------------------------------------------------------------------------

async def test_as11_wire_format_option_b(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
    reset_server_state: None,
) -> None:
    """AS-11. Option B wire format end-to-end through the FastMCP
    in-memory `Client`. Pattern mirrors T05's anchor test but with
    real `scan_diff` (T06 implementation wired in §3.H).

    Wire invariants asserted across BOTH success and error paths:
      - `is_error` is always `False` (Option B; protocol failures
        are the only signal for wire `is_error=True`).
      - `structured_content` is a dict carrying either the success
        payload (no `errorCode`) or the error envelope (with
        `errorCode`, `message`, `isRetryable`, `details`).
      - `content[0]` is a `TextContent` whose `text` reproduces
        the human-readable summary (success) or `message` (error).

    Discrimination is by presence of `errorCode` in
    `structured_content` per canonical §5.1 + ADR-0002 §3 amendment.
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files={"snippet.py": "def foo(): pass\nfoo()\n"},
    )
    monkeypatch.chdir(repo)
    server._bootstrap(rules_root=test_rules_dir)

    # Success path through Client.
    async with Client(server.mcp) as client:
        success = await client.call_tool(
            "scan_diff", {"base_ref": base_sha, "head_ref": head_sha},
        )

    assert success.is_error is False
    assert isinstance(success.structured_content, dict)
    assert "errorCode" not in success.structured_content
    assert "findings" in success.structured_content
    assert "scan_metadata" in success.structured_content
    assert len(success.content) == 1
    assert isinstance(success.content[0], TextContent)
    assert "candidato" in success.content[0].text  # PT-BR summary

    # Error path through Client (GIT_REF_NOT_FOUND).
    async with Client(server.mcp) as client:
        error = await client.call_tool(
            "scan_diff",
            {"base_ref": "nonexistent_abc", "head_ref": head_sha},
        )

    assert error.is_error is False  # Wire isError stays False (Option B)
    assert isinstance(error.structured_content, dict)
    assert error.structured_content["errorCode"] == "GIT_REF_NOT_FOUND"
    assert error.structured_content["isRetryable"] is False
    assert len(error.content) == 1
    assert isinstance(error.content[0], TextContent)
    assert error.content[0].text == error.structured_content["message"]


# ---------------------------------------------------------------------------
# Anchor — isRetryable table byte-by-byte matches canonical §5.4
# ---------------------------------------------------------------------------

_RETRYABILITY_TABLE: list[tuple[str, str, bool]] = [
    (
        "GIT_REF_NOT_FOUND",
        "_git_ref_not_found",
        False,
    ),
    (
        "INSUFFICIENT_GIT_HISTORY",
        "_insufficient_git_history",
        False,
    ),
    (
        "SCAN_TIMEOUT",
        "_scan_timeout",
        True,
    ),
    (
        "SEMGREP_BINARY_UNAVAILABLE",
        "_semgrep_binary_unavailable",
        False,
    ),
    (
        "SEMGREP_EXECUTION_FAILED",
        "_semgrep_execution_failed",
        True,
    ),
    (
        "INVALID_RULE_SET",
        "_invalid_rule_set",
        False,
    ),
]


@pytest.mark.parametrize(
    ("error_code", "builder_name", "expected_retryable"),
    _RETRYABILITY_TABLE,
    ids=[row[0] for row in _RETRYABILITY_TABLE],
)
def test_anchor_isretryable_table_matches_canonical_5_4(
    error_code: str, builder_name: str, expected_retryable: bool,
) -> None:
    """Anchor. Each `errorCode`'s `isRetryable` value matches canonical
    §5.4 byte-by-byte. Without this anchor, a typo in `_envelope.py`
    (e.g., `isRetryable=True` instead of `False` in SCAN_TIMEOUT) would
    pass all AS-4..AS-9 + AS-13 because those test wire shape, not the
    exact retryability value. This is the invariant the anchor is
    designed to catch — distinct from AS-11's wire-shape coverage.

    Builders constructed with minimal valid args; the asserted invariant
    is the bool field, not the message or details (those are AS-tested).
    """
    builders = {
        "_git_ref_not_found": lambda: _git_ref_not_found("base_ref", "x"),
        "_insufficient_git_history": _insufficient_git_history,
        "_scan_timeout": lambda: _scan_timeout(300, 312.4),
        "_semgrep_binary_unavailable": lambda: _semgrep_binary_unavailable([]),
        "_semgrep_execution_failed": lambda: _semgrep_execution_failed(2, "x"),
        "_invalid_rule_set": lambda: _invalid_rule_set(7, "x"),
    }
    envelope = builders[builder_name]()
    assert envelope.errorCode == error_code
    assert envelope.isRetryable is expected_retryable


# ---------------------------------------------------------------------------
# Anchor — Findings sorted by (location.path, location.start_line) ascending
# ---------------------------------------------------------------------------

def test_anchor_findings_ordering_path_startline_ascending(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
) -> None:
    """Anchor. Implements canonical §4.2 line 148: `findings` ordered
    by `(location.path, location.start_line)` ascending. Without this
    anchor, the invariant lives only in the spec — Semgrep does not
    guarantee ordering, so an implementation that removes the
    `sorted()` call (DD-T06-21) would pass AS-1/AS-12 by coincidence
    if Semgrep happened to emit findings in lexicographic order.

    Fixture: two files (`a_file.py`, `z_file.py`), `z_file.py` has an
    early-line match (line 2) and a late-line match (line 5);
    `a_file.py` has a match at line 3. Expected order:
    `a_file.py:3`, then `z_file.py:2`, then `z_file.py:5`.
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files={
            "z_file.py": (
                "def foo(): pass\n"
                "foo()\n"
                "x = 1\n"
                "y = 2\n"
                "foo()\n"
            ),
            "a_file.py": (
                "def foo(): pass\n"
                "x = 1\n"
                "foo()\n"
            ),
        },
    )
    monkeypatch.chdir(repo)
    state = load_rules(test_rules_dir)

    result = tools.scan_diff(base_sha, head_sha, state)

    assert result.structured_content is not None
    sc = result.structured_content
    assert "errorCode" not in sc
    findings = sc["findings"]
    assert len(findings) == 3

    # Strict ordering: a_file.py:3, then z_file.py:2, then z_file.py:5.
    order = [(f["location"]["path"], f["location"]["start_line"]) for f in findings]
    assert order == [("a_file.py", 3), ("z_file.py", 2), ("z_file.py", 5)]


# ---------------------------------------------------------------------------
# AS-14 — scan_diff via StdioTransport (real subprocess MCP server)
# ---------------------------------------------------------------------------

def _stdio_transport_env(rules_dir: Path) -> dict[str, str]:
    """Env baseline for spawning the MCP server via StdioTransport.

    `env=dict(os.environ)` baseline is mandatory — never `env={}` alone:
    PATH is required for git/semgrep resolution, SYSTEMROOT is required
    on Windows for socket/stdlib imports to succeed in spawned subprocesses.
    `SEMGREP_RUNNER_ROOT` is overridden to point at the test rules dir so
    the server bootstrap does not depend on the project's installed rule
    set (see `loader.resolve_runner_root` precedence).
    """
    env = dict(os.environ)
    env["SEMGREP_RUNNER_ROOT"] = str(rules_dir)
    return env


async def test_as14_scan_diff_stdio_transport_success(
    tmp_path: Path,
    test_rules_dir: Path,
) -> None:
    """AS-14. `scan_diff` exercised through a real `StdioTransport`
    (subprocess MCP server spawned via `python -m
    mcp_servers.semgrep_runner.server`), in contrast with AS-11 which
    uses `Client(server.mcp)` in-memory.

    Cross-platform happy path: ensures the stdio transport works
    end-to-end for valid refs. AS-14b (Windows-only) covers the specific
    handle-inheritance regression that AS-11 cannot reach because
    in-memory transport has no parent stdin pipe to inherit.

    Strict assertions mirror AS-11 success path: no `errorCode`, success
    payload keys present, single `TextContent` with PT-BR summary.
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files={"snippet.py": "def foo(): pass\nfoo()\n"},
    )
    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "mcp_servers.semgrep_runner.server"],
        cwd=str(repo),
        env=_stdio_transport_env(test_rules_dir),
    )
    async with Client(transport, timeout=300) as client:
        result = await client.call_tool(
            "scan_diff",
            {"base_ref": base_sha, "head_ref": head_sha},
        )

    assert result.is_error is False
    assert isinstance(result.structured_content, dict)
    assert "errorCode" not in result.structured_content
    assert "findings" in result.structured_content
    assert "scan_metadata" in result.structured_content
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert "candidato" in result.content[0].text  # PT-BR summary


# ---------------------------------------------------------------------------
# AS-14b — scan_diff does not hang under Windows-stdio transport (timing)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    sys.platform != "win32",
    reason="Handle inheritance via Windows anonymous pipe is specific to "
    "Win32 stdio MCP transport; POSIX does not exhibit the hang.",
)
async def test_as14b_scan_diff_no_hang_on_windows_stdio_transport(
    tmp_path: Path,
    test_rules_dir: Path,
) -> None:
    """AS-14b. Windows-only regression: `scan_diff` does not hang when
    spawning git subprocesses under a real `StdioTransport`.

    Without `stdin=subprocess.DEVNULL` in `_resolve_ref` /
    `_is_shallow_repository`, the git child inherits the parent MCP
    server's stdin pipe. On Windows, this handle inheritance via
    anonymous pipe causes `subprocess.run` to hang until timeout,
    accumulating ~22-23s (10s `_is_shallow_repository` + 10s
    `_resolve_ref(base_ref)` + cold-start) before `TimeoutExpired` is
    misclassified as `GIT_REF_NOT_FOUND` by the generic
    `except (SubprocessError, OSError)` capture.

    With the fix applied across all three subprocess sites in
    `tools.py`, the full path (cold-start + 2 git rev-parse + semgrep
    scan) returns in ~5-8s. The 10.0s threshold establishes a safe
    margin between the success path (~5-8s) and the defect path
    (~22-23s) without rejecting cold CI runs.

    Root cause (proximal): handle inheritance via Windows anonymous
    pipe used for stdio MCP transport. Fine-grained root cause (Win32
    pipe internals + `Popen.wait()` interaction) not fully characterized
    here; ADR-0011 post-hoc will cover. The semantic misclassification
    (`TimeoutExpired` treated as business `GIT_REF_NOT_FOUND` instead of
    transient) remains as documented debt addressed in ADR-0011 +
    follow-up PR; this PR eliminates the current manifestation only.

    Mirrors AS-13 as precedent for an AS-namespaced Windows-only test
    validating an invariant the contract relies on (subprocess
    behaviour under stdio transport).
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files={"snippet.py": "def foo(): pass\nfoo()\n"},
    )
    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "mcp_servers.semgrep_runner.server"],
        cwd=str(repo),
        env=_stdio_transport_env(test_rules_dir),
    )
    start = time.perf_counter()
    async with Client(transport, timeout=300) as client:
        await client.call_tool(
            "scan_diff",
            {"base_ref": base_sha, "head_ref": head_sha},
        )
    elapsed = time.perf_counter() - start
    assert elapsed < 10.0, (
        f"scan_diff took {elapsed:.2f}s under real StdioTransport — "
        f"handle inheritance defect present? Verify "
        f"stdin=subprocess.DEVNULL in _resolve_ref / "
        f"_is_shallow_repository / semgrep subprocess in tools.py."
    )


# ---------------------------------------------------------------------------
# T-G3 Anchor 1 — _normalize_rule_id collapses every observed check_id form
# ---------------------------------------------------------------------------

_RULE_ID_NORMALIZATION_CASES: list[tuple[str, str]] = [
    # Relative form: Semgrep dotifies the config path relative to the repo
    # root it resolves from cwd when the rule set lives inside the scanned
    # tree (pre-flight 0.D, scan from within the repo).
    ("mcp_servers.semgrep_runner.rules.br-cpf", "br-cpf"),
    # Absolute form: when the rule set is outside the scanned repo (the live
    # Passo 2 scenario), Semgrep dotifies the absolute config path. Drive
    # letter casing (C vs c) is Windows-specific; form (a) ignores it.
    (
        "C.Users.joaoguilherm.pereira.dev.lgpd-policy-review"
        ".mcp_servers.semgrep_runner.rules.br-cpf",
        "br-cpf",
    ),
    # Idempotence: an already-bare id is unchanged — guards the clean path
    # against the fix mangling a non-prefixed check_id.
    ("br-cpf", "br-cpf"),
]


@pytest.mark.parametrize(
    ("check_id", "expected"),
    _RULE_ID_NORMALIZATION_CASES,
    ids=["relative", "absolute-live", "already-bare"],
)
def test_anchor_normalize_rule_id_collapses_observed_forms(
    check_id: str, expected: str,
) -> None:
    """Anchor (T-G3 / DD-G3-1, DD-G3-3). `_normalize_rule_id` returns the
    bare rule id for every `check_id` form Semgrep 1.163.0 emits, verified
    empirically in pre-flight 0.D (relative + absolute, both observed).
    Form (a) `rsplit(".", 1)[-1]` ignores the prefix entirely, so it is
    robust to the prefix instability between in-repo and external-repo scans.

    Referenced via module attribute (`tools._normalize_rule_id`) so the red
    state in the anchors-only commit is an uncaught `AttributeError` localised
    to this test — NOT a module-level `ImportError` that would break
    collection and mask the green no-dot anchor in the same file. The error
    propagates naturally (no `pytest.raises`): red here, green after the fix.
    """
    assert tools._normalize_rule_id(check_id) == expected


# ---------------------------------------------------------------------------
# T-G3 Anchor 2 — mapper wires _normalize_rule_id into Finding.rule_id
# ---------------------------------------------------------------------------

def test_anchor_map_finding_normalizes_rule_id(tmp_path: Path) -> None:
    """Anchor (T-G3 / DD-G3-2). Proves the helper is actually plugged into
    `_map_finding`, not merely existing: a hand-built `_SemgrepResult` with a
    polluted `check_id` maps to a `Finding` whose `rule_id` is the bare id.
    Hermetic — no subprocess, no git. `_read_snippet` tolerates the absent
    source file (its `except (OSError, IndexError)` catches `FileNotFoundError`
    and returns ""; tools.py), so no fixture file is required.
    """
    result = _SemgrepResult(
        check_id=(
            "C.Users.joaoguilherm.pereira.dev.lgpd-policy-review"
            ".mcp_servers.semgrep_runner.rules.br-cpf"
        ),
        path="users/registration.py",
        start=_SemgrepLocation(line=1, col=1),
        end=_SemgrepLocation(line=1, col=5),
        extra=_SemgrepResultExtra(severity="WARNING", message="m"),
    )

    finding = tools._map_finding(result, tmp_path)

    assert finding.rule_id == "br-cpf"


# ---------------------------------------------------------------------------
# T-G3 Anchor 3 — empty-normalised rule_id surfaces as SEMGREP_EXECUTION_FAILED
# ---------------------------------------------------------------------------

def test_anchor_empty_normalized_rule_id_is_execution_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_rules_dir: Path,
) -> None:
    """Anchor (T-G3 / DD-G3-2 degenerate). A `check_id` that normalises to
    empty (e.g. `"foo."` → `""`) makes `_normalize_rule_id` raise `ValueError`;
    because `_map_finding` is evaluated inside the `try/except (ValidationError,
    ValueError)` of `scan_diff` (the `sorted(...)` forces the generator there),
    the error surfaces as the `SEMGREP_EXECUTION_FAILED` envelope. Exercises the
    except reuse end-to-end, empirically — not by inference. Mirrors the
    AS-8/AS-9 mocked-subprocess pattern.
    """
    repo, base_sha, head_sha = make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files={"snippet.py": "def foo(): pass\nfoo()\n"},
    )
    monkeypatch.chdir(repo)
    state = load_rules(test_rules_dir)

    real_run = subprocess.run

    def mocked_run(
        cmd: list[str], **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        if cmd and "semgrep" in str(cmd[0]).lower():
            return subprocess.CompletedProcess(
                args=cmd, returncode=0,
                stdout=(
                    '{"version":"1.163.0","results":'
                    '[{"check_id":"foo.","path":"snippet.py",'
                    '"start":{"line":1,"col":1},'
                    '"end":{"line":1,"col":5},'
                    '"extra":{"severity":"WARNING","message":"m"}}],'
                    '"errors":[],"paths":{"scanned":["snippet.py"]}}'
                ),
                stderr="",
            )
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "run", mocked_run)

    result = tools.scan_diff(base_sha, head_sha, state)

    assert result.structured_content is not None
    sc = result.structured_content
    assert sc.get("errorCode") == "SEMGREP_EXECUTION_FAILED"


# ---------------------------------------------------------------------------
# T-G3 Anchor 4 — no production rule id contains a dot (form (a) invariant)
# ---------------------------------------------------------------------------

def test_anchor_no_production_rule_id_contains_dot() -> None:
    """Anchor (T-G3 / DD-G3-4). Form (a) `rsplit(".", 1)[-1]` is only lossless
    while no rule `id` contains an internal dot. This guards the invariant the
    normalization relies on: a future rule like `pii.email` would be silently
    truncated to `email`. Pins it loudly against the real curated rule set.
    Green from the start — a guard, not a red anchor.
    """
    rules_root = resolve_runner_root()
    rule_ids = [
        rule["id"]
        for path in sorted(rules_root.glob("*.yaml"))
        for rule in yaml.safe_load(path.read_text(encoding="utf-8"))["rules"]
    ]

    assert rule_ids, f"no rules found under {rules_root}"
    offenders = [rid for rid in rule_ids if "." in rid]
    assert offenders == [], (
        f"rule ids with an internal dot break _normalize_rule_id: {offenders}"
    )
