"""Shared fixtures for semgrep-runner tests.

Mirrors `tests/mcp_servers/policy_reader/conftest.py` in spirit. The
real `mcp_servers/semgrep_runner/rules/` directory of the repo is never
written to; tests that exercise loader/bootstrap failure modes build
fixture rule sets under `tmp_path` and pass the path explicitly to
`load_rules` or `server._bootstrap`.

T06 adds two helpers used by `test_scan_diff.py`:
  - `make_git_repo(tmp_path, base_files, head_files) -> (Path, str, str)`
    builds a real git repo with two commits, returns repo root + base
    SHA + head SHA. Files present at base but absent at head remain
    unchanged on disk (Git does not delete files between commits unless
    explicitly removed); files in `head_files` are written on top of
    base. Used by AS-1, AS-2, AS-3, AS-12, anchors.
  - `_pid_alive_windows(pid) -> bool` (DD-T06-16) checks PID liveness
    on Windows via `tasklist /FI` without killing the process — CPython
    `os.kill(pid, 0)` on Windows calls `TerminateProcess`, opposite of
    POSIX. Used by AS-13.

T07 adds helpers used by `test_recognizers_br.py`:
  - `_build_br_rules_dir(tmp_path, slugs) -> Path` copies selected BR
    rule YAMLs from the production rule set into a tmp rules dir.
  - `_build_pack_repo(tmp_path, fixture_names) -> (Path, str, str)`
    builds a git repo whose head commit introduces the requested
    fixtures from the BR pack.
  - Convenience fixtures `br_rules_dir` (all 6) and `br_pack_repo`
    (all 9 fixtures) wrap the helpers for tests that want the full set.
"""
from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path

import pytest

BR_SLUGS: tuple[str, ...] = (
    "br_cpf",
    "br_cnpj",
    "br_cnh",
    "br_nis_pis",
    "br_titulo_eleitor",
    "br_cns_saude",
)
"""Snake_case YAML basenames of the six T07 recognizers, in canonical order."""


@pytest.fixture
def reset_server_state():
    """Teardown fixture for tests that call `server._bootstrap`.

    Bootstrap mutates module-level `_STATE`; without explicit teardown,
    subsequent tests would observe stale state. Yields nothing; on
    teardown, clears `_STATE` back to None.
    """
    from mcp_servers.semgrep_runner import server

    yield
    server._reset_state_for_tests()


def make_git_repo(
    tmp_path: Path,
    base_files: dict[str, str],
    head_files: dict[str, str],
) -> tuple[Path, str, str]:
    """Build a real git repo with two commits under `tmp_path / "repo"`.

    `base_files` and `head_files` are dicts mapping repo-relative path
    (forward slashes, POSIX style) to file content (str, UTF-8). Both
    commits are real — `git init` + `git config` for committer identity
    + `git add` + `git commit -q -m "..."`. Returns repo root path +
    base SHA (40 hex) + head SHA (40 hex).

    `head_files` is applied on top of the base tree — entries with paths
    already present in base overwrite; new entries are added; paths
    present only in base remain unchanged. To exercise deletion between
    commits, the caller should use the lower-level git commands directly
    (no AS in T06 needs deletion between commits).
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@semgrep-runner.local")
    _git(repo, "config", "user.name", "semgrep-runner-test")
    _write_tree(repo, base_files)
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "base")
    base_sha = _rev_parse_head(repo)
    if head_files:
        _write_tree(repo, head_files)
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "head")
        head_sha = _rev_parse_head(repo)
    else:
        head_sha = base_sha
    return repo, base_sha, head_sha


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
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


def _write_tree(repo: Path, files: dict[str, str]) -> None:
    for rel_path, content in files.items():
        target = repo / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")


def _pid_alive_windows(pid: int) -> bool:
    """Check if PID is alive on Windows without killing it (DD-T06-16).

    CPython `os.kill(pid, 0)` on Windows calls `TerminateProcess` —
    kills the process if alive, opposite of POSIX semantics. `tasklist
    /FI` is the non-destructive idiom on Windows; available since XP and
    more portable than `Get-Process` (PowerShell-only).
    """
    result = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=5,
    )
    return str(pid) in result.stdout


def make_shallow_clone(source_repo: Path, tmp_path: Path) -> Path:
    """Create a `--depth=1` clone of `source_repo` under `tmp_path / "shallow"`.

    Uses `file:///` URI so the operation is local (no network).
    `source_repo` must have ≥ 2 commits so the shallow clone is
    distinguishable from the source (`git rev-parse --is-shallow-repository`
    returns `true` only when the clone truncated history).
    """
    shallow = tmp_path / "shallow"
    source_uri = "file:///" + str(source_repo).replace("\\", "/")
    subprocess.run(
        ["git", "clone", "--depth=1", source_uri, str(shallow)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=True,
    )
    return shallow


@pytest.fixture
def test_rules_dir(tmp_path: Path) -> Path:
    """Minimal fixture rule set: one Python rule matching `foo()` calls.

    Used by AS-1, AS-2, AS-3, AS-12, anchors to exercise `scan_diff`
    against a known rule without depending on the project's MVP rule
    set (which would force AS coupling to the curated Brazilian
    recognizers).
    """
    rules = tmp_path / "rules"
    rules.mkdir()
    (rules / "foo_rule.yaml").write_text(
        "rules:\n"
        "  - id: test-foo-call\n"
        "    pattern: foo()\n"
        "    message: foo() call detected by test rule\n"
        "    languages: [python]\n"
        "    severity: WARNING\n",
        encoding="utf-8",
        newline="\n",
    )
    return rules


# ---------------------------------------------------------------------------
# T07 — BR recognizers helpers and fixtures
# ---------------------------------------------------------------------------

PRODUCTION_RULES_DIR = (
    Path(__file__).resolve().parents[3] / "mcp_servers" / "semgrep_runner" / "rules"
)
BR_PACK_DIR = Path(__file__).resolve().parent / "fixtures" / "recognizers_pack_br"


def _build_br_rules_dir(tmp_path: Path, slugs: Iterable[str]) -> Path:
    """Copy the requested BR rule YAMLs from the production rule set into a tmp dir.

    Each slug is a snake_case basename (e.g. `"br_cpf"`); the file
    `<slug>.yaml` is copied verbatim. Caller is responsible for passing
    only slugs whose YAML exists at call time (5 of 6 slugs are absent
    during 3.B-3.C incremental implementation).
    """
    rules = tmp_path / "rules"
    rules.mkdir()
    for slug in slugs:
        shutil.copy(PRODUCTION_RULES_DIR / f"{slug}.yaml", rules / f"{slug}.yaml")
    return rules


def _build_pack_repo(
    tmp_path: Path, fixture_names: Iterable[str]
) -> tuple[Path, str, str]:
    """Build a git repo whose head commit introduces the requested BR pack fixtures.

    `fixture_names` are basenames within the BR pack directory (e.g.
    `"br_cpf_function_param.py"`). The fixtures are copied verbatim into
    the head commit. Returns the same shape as `make_git_repo`:
    `(repo, base_sha, head_sha)`.
    """
    head_files = {
        name: (BR_PACK_DIR / name).read_text(encoding="utf-8")
        for name in fixture_names
    }
    return make_git_repo(
        tmp_path,
        base_files={"placeholder.txt": "base\n"},
        head_files=head_files,
    )


@pytest.fixture
def br_rules_dir(tmp_path: Path) -> Path:
    """Tmp rules dir containing all six BR rule YAMLs from the production set.

    Used by anchor tests (parse YAML files), AS-7 (negatives vs all 6 rules
    cumulatively), AS-8 (placeholder removed: only br-* rule_ids), and AS-9
    (idempotency over the full rule set). Tests that need only a subset
    call `_build_br_rules_dir(tmp_path, ("br_X",))` directly.
    """
    return _build_br_rules_dir(tmp_path, BR_SLUGS)


@pytest.fixture
def br_pack_repo(tmp_path: Path) -> tuple[Path, str, str]:
    """Git repo with all nine BR pack fixtures (6 positive + 3 negative) at head.

    Used by AS-7, AS-8, AS-9 which need to see the full fixture set in a
    single scan. Per-AS tests that scan a single fixture call
    `_build_pack_repo(tmp_path, ("br_X.py",))` directly.
    """
    fixture_names = sorted(p.name for p in BR_PACK_DIR.glob("*.py"))
    return _build_pack_repo(tmp_path, fixture_names)
