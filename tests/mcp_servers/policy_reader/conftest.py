"""Shared fixtures for policy-reader tests.

The repo's real `policy/` is cloned into `tmp_path` for every test that
needs to mutate it (knock out a file, mutate the header, inject a synthetic
clause). The real `policy/` is never written to.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_POLICY = REPO_ROOT / "policy"


@pytest.fixture
def valid_policy_root(tmp_path: Path) -> Path:
    """Deep copy of the real `policy/` into `tmp_path / 'policy'`.

    Each test that needs a Policy that is _almost_ valid (with one
    intentional knock-out) starts from this fixture and mutates files
    in-place before invoking `load_policy`.
    """
    root = tmp_path / "policy"
    shutil.copytree(REAL_POLICY, root)
    return root


@pytest.fixture
def reset_server_state():
    """Teardown fixture for tests that call `server._bootstrap`.

    Bootstrap mutates module-level `_STATE`; without explicit teardown,
    subsequent tests would observe stale state. Yields nothing; on
    teardown, clears `_STATE` back to None.
    """
    from mcp_servers.policy_reader import server

    yield
    server._reset_state_for_tests()
