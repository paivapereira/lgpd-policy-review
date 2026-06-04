"""Shared synthetic-PR scaffolding for live harnesses (DD-P4-5).

NEW CANONICAL SOURCE for building an ephemeral two-commit git repo (empty base +
head adding a fixture's content files) and a temp `.mcp.json` whose servers spawn
via `uv run --project <repo-root>`. The frozen measurement harness
`eval/experiments/pipeline_e2e_eval_lgpd.py:187-230` still carries its own private
copies — left UNTOUCHED on purpose (frozen artifact, do not refactor in a feature
PR). Deduping it to import from here is CATALOGUED DEBT (companion edit / chore
futuro); importing its module-private `_make_pr_repo` would be worse.

Empty base => `worktree@head` == exactly the PR's files, so `scan_diff`'s
`--baseline-commit <base>` treats every head file as new (works on an empty-tree
baseline). Dotfiles are excluded from the head commit, so a fixture's
`.expected-report.json` never enters the synthetic PR.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _head_sha(repo: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def make_pr_repo(parent: Path, pr_dir: Path) -> tuple[Path, str, str]:
    """Build a two-commit repo under `parent`: an empty base, then a head commit
    adding every non-dotfile in `pr_dir`. Returns (repo, base_sha, head_sha)."""
    repo = parent / "pr-repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "eval@example.com")
    _git(repo, "config", "user.name", "eval")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "base")
    base = _head_sha(repo)

    copied = 0
    for item in sorted(pr_dir.iterdir()):
        if item.name.startswith("."):
            continue  # skip .expected-report.json and any dotfile
        if item.is_file():
            shutil.copy2(item, repo / item.name)
            copied += 1
    if copied == 0:
        raise RuntimeError(f"no content files to commit in {pr_dir} (fixture broken?)")

    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", f"pr {pr_dir.name}")
    head = _head_sha(repo)
    return repo, base, head


def write_project_mcp_json(dst_dir: Path, project_root: Path) -> Path:
    """Write a temp `.mcp.json` whose BOTH servers spawn via
    `uv run --project <project_root>` — they resolve their env from the repo root
    while keeping the synthetic-repo cwd. Returns the written path (absolute)."""
    prefix = ["run", "--project", str(project_root), "python", "-m"]
    payload = {
        "mcpServers": {
            "policy-reader": {
                "command": "uv",
                "args": [*prefix, "mcp_servers.policy_reader.server"],
            },
            "semgrep-runner": {
                "command": "uv",
                "args": [*prefix, "mcp_servers.semgrep_runner.server"],
            },
        }
    }
    path = dst_dir / ".mcp.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
