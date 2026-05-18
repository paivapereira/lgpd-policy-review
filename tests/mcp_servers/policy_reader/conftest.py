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
PACK_CLAUSES = (
    REPO_ROOT
    / "tests"
    / "mcp_servers"
    / "policy_reader"
    / "fixtures"
    / "clauses_pack_check_applicability"
)


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
def policy_root_with_pack_clauses(tmp_path: Path) -> Path:
    """`valid_policy_root` extended with the four pack clauses POL-001
    through POL-004 from
    `tests/.../fixtures/clauses_pack_check_applicability/`:

    - POL-001: active substantive, `consent_required`, LGPD Art. 7, I
    - POL-002: active substantive, `anonymization_required`, LGPD Art. 12 §2
    - POL-003: deprecated, tombstone with successors=[POL-004]
    - POL-004: active substantive, `consent_required`, declared successor
      of POL-003 (refined wording for `dados_de_documentos_oficiais`)

    POL-000 ships from the real `policy/clauses/` via the initial `copytree`.
    Composition history: T02a consumed POL-001/POL-003 for AS-1.b/AS-2; T02b
    added POL-004 for the broad LGPD Art. 7 query pair; T03 adds POL-002
    aditively for the indeterminate verdict path. The fixture name is kept
    across mutations to preserve T02a/T02b assertion compatibility (those
    suites use subset-style assertions; no test asserts exact count or
    absence of POL-002).
    """
    root = tmp_path / "policy"
    shutil.copytree(REAL_POLICY, root)
    for pol_id in ("POL-001", "POL-002", "POL-003", "POL-004"):
        shutil.copy(
            PACK_CLAUSES / f"{pol_id}.yaml",
            root / "clauses" / f"{pol_id}.yaml",
        )
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
