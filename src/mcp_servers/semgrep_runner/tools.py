"""Pure tool implementations for the semgrep-runner MCP server.

`scan_diff` invokes Semgrep over a Git diff range, parses the JSON
output, and returns either a `ScanSuccessPayload` (success) or an
`ErrorEnvelope` (one of six errorCodes per canonical §5). Functions
here are pure in the sense that they receive `state: LoadedRules` as
an argument; the `@mcp.tool` wrapper in `server.py` injects `_STATE`.

Subprocess invocation passes four mandatory flags:
    --json --metrics=off --baseline-commit <sha> --config <rules_path>
Target is `.` (current working directory). cwd is inherited from the
MCP server process — caller responsibility per canonical §4.2 caller
invariants (DD-T06-3 + DD-T06-19).

Snippet derivation (DD-T06-23): Semgrep OSS without `SEMGREP_APP_TOKEN`
emits `extra.lines = "requires login"` instead of the actual code
excerpt (canonical §8 vetoes the token). `_read_snippet` reads the file
from the filesystem at the finding's location and returns the line
range. Empty string is a legitimate value when the source file was
deleted between commits.

Exit code mapping (X1, ratified at GATE 1 per pre-flight 3.E empirical
observation):
    0           → success
    7, 8        → INVALID_RULE_SET (config malformed / unparseable YAML
                  collapsed by Semgrep into "invalid configuration"; or
                  language not supported by rule)
    other       → SEMGREP_EXECUTION_FAILED (generic fallback)
Exits 4 and 5 documented in the Semgrep CLI reference are empirically
unreachable in 1.163.0 and are not mapped (CLAUDE.md "no defensive code
for impossible scenarios"); they would fall through the fallback if they
ever surface in a future Semgrep release.

Wire-shape convention (Option B): see `_envelope.py`.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Final, Literal

from fastmcp.tools.base import ToolResult
from pydantic import ValidationError

from ._envelope import (
    _envelope_tool_result,
    _git_ref_not_found,
    _insufficient_git_history,
    _invalid_rule_set,
    _parse_semgrep_stdout_errors,
    _scan_success_tool_result,
    _scan_timeout,
    _semgrep_binary_unavailable,
    _semgrep_execution_failed,
    _truncate_stderr,
)
from ._semgrep_output import _SemgrepResult, _SemgrepRunOutput
from .models import (
    Finding,
    Location,
    LoadedRules,
    ScanMetadata,
    ScanSuccessPayload,
)

_DEFAULT_TIMEOUT_SECONDS: Final[int] = 300
_TIMEOUT_ENV_VAR: Final[str] = "SEMGREP_RUNNER_TIMEOUT_SECONDS"
_GIT_SUBCOMMAND_TIMEOUT: Final[int] = 10
_SHA1_HEX = set("0123456789abcdef")

# DD-T06-6 lazy layer: substrings inspected in `errors[].message` from
# Semgrep JSON output (DD-T06-22) when proactive `is-shallow-repository`
# returns false but a downstream baseline resolution still fails. First
# substring is specific to the `--baseline-commit` mechanism (empirical
# from pre-flight 3.G against Semgrep 1.163.0); the remaining three are
# robustness for git error messages that may bubble up when Semgrep is
# updated or git internals change — aligned with git documentation that
# persists cross-version.
_SHALLOW_SIGNALS: Final[tuple[str, ...]] = (
    "BaselineHandler initialization",
    "shallow",
    "merge-base",
    "cannot find common ancestor",
)

_SeverityT = Literal["info", "warning", "error"]


def _resolve_timeout_seconds() -> int:
    """Read `SEMGREP_RUNNER_TIMEOUT_SECONDS` from env; default 300.

    Invalid values (non-int, ≤ 0) fall back to the default rather than
    surfacing a configuration error — operator misconfiguration of an
    env var should not block scans entirely.
    """
    raw = os.environ.get(_TIMEOUT_ENV_VAR)
    if raw is None:
        return _DEFAULT_TIMEOUT_SECONDS
    try:
        value = int(raw)
    except ValueError:
        return _DEFAULT_TIMEOUT_SECONDS
    return value if value > 0 else _DEFAULT_TIMEOUT_SECONDS


def _read_snippet(location: Location, repo_root: Path) -> str:
    """Read snippet from filesystem (DD-T06-23).

    Semgrep OSS without `SEMGREP_APP_TOKEN` does not provide code lines
    (`extra.lines = "requires login"` per pre-flight 3.D); canonical §8
    vetoes the token, so the component derives snippet by reading the
    file itself. Semgrep `start_line` / `end_line` are 1-indexed and
    inclusive.

    Failures (file deleted between commits, OSError, IndexError
    out-of-range) return `""`. Empty string is a legitimate value per
    canonical §4 — snippet is a required field but the empty value is
    acceptable when the source is unavailable.
    """
    try:
        with (repo_root / location.path).open(
            encoding="utf-8", errors="replace",
        ) as handle:
            lines = handle.read().splitlines()
        return "\n".join(
            lines[location.start_line - 1 : location.end_line]
        )
    except (OSError, IndexError):
        return ""


def _is_shallow_repository(repo_root: Path) -> bool:
    """Proactive shallow detection (DD-T06-6 layer 1).

    Failure of `git rev-parse` itself (non-zero, timeout, OSError)
    is interpreted as "not detectably shallow" — the lazy layer in
    `scan_diff` will catch the actual shallow signal in Semgrep's
    `errors[].message` if it materialises.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-shallow-repository"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_GIT_SUBCOMMAND_TIMEOUT,
            stdin=subprocess.DEVNULL,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def _resolve_ref(ref: str, repo_root: Path) -> str | None:
    """Resolve `ref` to 40-char hex SHA via `git rev-parse --verify
    {ref}^{commit}` (DD-T06-4). Returns the SHA on success; `None`
    otherwise (non-zero exit, malformed output, timeout, OSError).
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_GIT_SUBCOMMAND_TIMEOUT,
            stdin=subprocess.DEVNULL,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    if len(sha) != 40:
        return None
    return sha if all(c in _SHA1_HEX for c in sha) else None


def _normalize_severity(raw: str) -> _SeverityT:
    """Map Semgrep uppercase severity → canonical lowercase.

    Raises `ValueError` on unexpected values; `scan_diff` catches it
    alongside `ValidationError` and surfaces as `SEMGREP_EXECUTION_FAILED`
    (DD-T06-8).
    """
    lower = raw.lower()
    if lower == "info":
        return "info"
    if lower == "warning":
        return "warning"
    if lower == "error":
        return "error"
    raise ValueError(
        f"Unexpected Semgrep severity {raw!r}; expected INFO/WARNING/ERROR",
    )


def _normalize_rule_id(raw: str) -> str:
    """Strip Semgrep's dotified config-path prefix, returning the bare rule id.

    Semgrep namespaces `check_id` as `<dotified-config-path>.<rule-id>`. The
    prefix is the rule set path dotified relative to the project root Semgrep
    resolves from cwd, falling back to the absolute path when the rule set is
    outside the scanned repo (empirical, pre-flight 0.D) — so the prefix is not
    stable across scan contexts. Taking the last dotted segment yields the
    rule's `id` field independent of any prefix; this holds while no rule id
    contains an internal dot (anchored by
    `test_anchor_no_production_rule_id_contains_dot`).

    Raises `ValueError` when the normalised id is empty (e.g. a `check_id`
    ending in a dot); `scan_diff` catches it alongside `_normalize_severity`'s
    `ValueError` / Pydantic `ValidationError` and surfaces it as
    `SEMGREP_EXECUTION_FAILED` (DD-T06-8). Mirrors `_normalize_severity`.
    """
    cleaned = raw.rsplit(".", 1)[-1]
    if not cleaned:
        raise ValueError(
            f"Normalised rule_id is empty for check_id {raw!r}",
        )
    return cleaned


def _map_finding(result: _SemgrepResult, repo_root: Path) -> Finding:
    """Convert internal `_SemgrepResult` to public `Finding`. Reads
    snippet from filesystem (DD-T06-23). Pydantic `ValidationError` or
    `ValueError` from severity/rule-id normalisation surfaces upstream as
    `SEMGREP_EXECUTION_FAILED`.
    """
    location = Location(
        path=result.path,
        start_line=result.start.line,
        start_col=result.start.col,
        end_line=result.end.line,
        end_col=result.end.col,
    )
    return Finding(
        rule_id=_normalize_rule_id(result.check_id),
        rule_severity=_normalize_severity(result.extra.severity),
        rule_message=result.extra.message,
        location=location,
        snippet=_read_snippet(location, repo_root),
    )


def _build_success_text(
    findings: list[Finding], elapsed: float,
) -> str:
    """Build human-readable summary for `content[0].text` (DD-T06-9
    plural agreement rule, inline)."""
    n = len(findings)
    if n == 0:
        return (
            f"Scan concluído em {elapsed:.1f}s. "
            "Nenhum candidato detectado no diff."
        )
    verb = "Encontrado" if n == 1 else "Encontrados"
    noun = "candidato" if n == 1 else "candidatos"
    top = ", ".join(
        f"{f.location.path}:{f.location.start_line} ({f.rule_id})"
        for f in findings[:5]
    )
    suffix = "" if n <= 5 else f" ... e mais {n - 5}"
    return (
        f"Scan concluído em {elapsed:.1f}s. {verb} {n} {noun}: "
        f"{top}{suffix}."
    )


def scan_diff(
    base_ref: str, head_ref: str, state: LoadedRules,
) -> ToolResult:
    """Run Semgrep diff-aware scan between `base_ref` and `head_ref`.

    Ordering (DD-T06-7 as ratified at GATE 1):
      1. `shutil.which("semgrep")` → `SEMGREP_BINARY_UNAVAILABLE` if None.
      2. `_is_shallow_repository()` → `INSUFFICIENT_GIT_HISTORY` (proactive).
      3. `_resolve_ref(base_ref)` + `_resolve_ref(head_ref)` →
         `GIT_REF_NOT_FOUND` per ref param.
      4. `subprocess.run(["semgrep", ...4 flags...])` with timeout.
      5. Catch `TimeoutExpired` → `SCAN_TIMEOUT`.
      6. Exit 0 → parse via `_SemgrepRunOutput` → success
         (sorted findings per DD-T06-21).
      7. Exit ≠ 0 → DD-T06-22 enrichment + DD-T06-6 lazy refinement +
         X1 mapping.

    Wire format: Option B (envelope or success payload in
    `structured_content`; `content[0].text` is human prose; wire
    `isError` always `False`).
    """
    repo_root = Path.cwd()

    # (1) Binary availability per-call (DD-T06-2).
    binary = shutil.which("semgrep")
    if binary is None:
        searched = os.environ.get("PATH", "").split(os.pathsep)
        return _envelope_tool_result(_semgrep_binary_unavailable(searched))

    # (2) Proactive shallow check (DD-T06-6 layer 1).
    if _is_shallow_repository(repo_root):
        return _envelope_tool_result(_insufficient_git_history())

    # (3) Resolve git refs (DD-T06-4).
    resolved_base = _resolve_ref(base_ref, repo_root)
    if resolved_base is None:
        return _envelope_tool_result(
            _git_ref_not_found("base_ref", base_ref),
        )
    resolved_head = _resolve_ref(head_ref, repo_root)
    if resolved_head is None:
        return _envelope_tool_result(
            _git_ref_not_found("head_ref", head_ref),
        )

    # (4) Invoke Semgrep with 4 mandatory flags. cwd inherited per
    # DD-T06-3 + DD-T06-19 — caller responsibility per canonical §4.2.
    timeout = _resolve_timeout_seconds()
    cmd = [
        binary, "scan",
        "--json",
        "--metrics=off",
        "--baseline-commit", resolved_base,
        "--config", state.rules_root,
        ".",
    ]
    start_monotonic = time.monotonic()
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        # (5) Timeout — subprocess.run kills child internally on
        # TimeoutExpired (DD-T06-1 ratified via pre-flight 3.H zero
        # zombies). Elapsed measured from start_monotonic, not from
        # the timeout config (caller wants actual elapsed).
        elapsed = time.monotonic() - start_monotonic
        return _envelope_tool_result(_scan_timeout(timeout, elapsed))
    elapsed = time.monotonic() - start_monotonic

    # (6) Exit 0 → success path.
    if completed.returncode == 0:
        try:
            output = _SemgrepRunOutput.model_validate_json(
                completed.stdout,
            )
            # _map_finding is materialised here, inside the try: it calls
            # _normalize_rule_id and _normalize_severity, whose ValueError on a
            # malformed value must be caught by the except below and surfaced as
            # SEMGREP_EXECUTION_FAILED. Moving sorted() out of the try would let
            # that ValueError escape uncaught (T-G3 / DD-G3-2).
            findings = sorted(
                (_map_finding(r, repo_root) for r in output.results),
                key=lambda f: (f.location.path, f.location.start_line),
            )
        except (ValidationError, ValueError) as exc:
            return _envelope_tool_result(
                _semgrep_execution_failed(
                    completed.returncode,
                    _truncate_stderr(completed.stderr),
                    parse_error=str(exc),
                ),
            )
        scanned_raw = output.paths.get("scanned", [])
        files_scanned = (
            len(scanned_raw) if isinstance(scanned_raw, list) else 0
        )
        payload = ScanSuccessPayload(
            rules_version=state.rules_version,
            semgrep_version=output.version,
            scan_metadata=ScanMetadata(
                base_ref=resolved_base,
                head_ref=resolved_head,
                files_scanned=files_scanned,
                elapsed_seconds=round(elapsed, 1),
            ),
            findings=findings,
        )
        text_summary = _build_success_text(findings, elapsed)
        return _scan_success_tool_result(payload, text_summary)

    # (7) Exit ≠ 0 — DD-T06-22 enrichment + DD-T06-6 lazy + X1 mapping.
    stderr_excerpt = _truncate_stderr(completed.stderr)
    enriched = _parse_semgrep_stdout_errors(completed.stdout)
    diagnostic = enriched if enriched is not None else stderr_excerpt

    # DD-T06-6 lazy layer: shallow signal in errors[].message?
    if enriched is not None and any(
        sig in enriched for sig in _SHALLOW_SIGNALS
    ):
        return _envelope_tool_result(_insufficient_git_history())

    # X1 mapping (GATE 1 ratified): exits 7|8 → INVALID_RULE_SET,
    # everything else → SEMGREP_EXECUTION_FAILED.
    if completed.returncode in (7, 8):
        return _envelope_tool_result(
            _invalid_rule_set(completed.returncode, diagnostic),
        )
    return _envelope_tool_result(
        _semgrep_execution_failed(completed.returncode, diagnostic),
    )
