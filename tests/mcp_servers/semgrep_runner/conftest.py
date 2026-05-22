"""Shared fixtures for semgrep-runner tests.

Mirrors `tests/mcp_servers/policy_reader/conftest.py` in spirit. The
real `mcp_servers/semgrep_runner/rules/` directory of the repo is never
written to; tests that exercise loader/bootstrap failure modes build
fixture rule sets under `tmp_path` and pass the path explicitly to
`load_rules` or `server._bootstrap`.
"""
from __future__ import annotations

import pytest


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
