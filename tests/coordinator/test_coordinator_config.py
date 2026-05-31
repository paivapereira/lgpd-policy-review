"""Phase 0 anchors — `.mcp.json` whitelist parse (coordinator.md §6 Camada 1).

AS-a: loads exactly the whitelisted servers. AS-b: fails loud (halt before any
query) on an unexpected server. Hardening: a missing required server also halts
(the named slices POLICY_READER_CONFIG / SEMGREP_RUNNER_CONFIG would otherwise
KeyError downstream).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from coordinator.config import EXPECTED_SERVERS, load_mcp_config
from coordinator.errors import CoordinatorStartupError


def _write_mcp(tmp_path: Path, servers: dict) -> Path:
    path = tmp_path / ".mcp.json"
    path.write_text(json.dumps({"mcpServers": servers}), encoding="utf-8")
    return path


def test_expected_servers_constant() -> None:
    assert EXPECTED_SERVERS == {"policy-reader", "semgrep-runner"}


def test_config_loads_only_whitelisted(tmp_path: Path) -> None:
    path = _write_mcp(
        tmp_path,
        {
            "policy-reader": {"command": "uv", "args": ["run", "policy"]},
            "semgrep-runner": {"command": "uv", "args": ["run", "semgrep"]},
        },
    )
    cfg = load_mcp_config(path)
    assert set(cfg.mcp_servers_dict.keys()) == {"policy-reader", "semgrep-runner"}
    assert cfg.policy_reader_config == {"command": "uv", "args": ["run", "policy"]}
    assert cfg.semgrep_runner_config["command"] == "uv"


def test_config_fails_loud_on_unexpected_server(tmp_path: Path) -> None:
    path = _write_mcp(
        tmp_path,
        {
            "policy-reader": {"command": "uv"},
            "semgrep-runner": {"command": "uv"},
            "rogue-debugger": {"command": "x"},
        },
    )
    with pytest.raises(CoordinatorStartupError) as exc_info:
        load_mcp_config(path)
    assert "rogue-debugger" in str(exc_info.value)


def test_config_fails_loud_on_missing_required_server(tmp_path: Path) -> None:
    path = _write_mcp(tmp_path, {"policy-reader": {"command": "uv"}})
    with pytest.raises(CoordinatorStartupError):
        load_mcp_config(path)


def test_config_fails_loud_on_missing_file(tmp_path: Path) -> None:
    with pytest.raises(CoordinatorStartupError):
        load_mcp_config(tmp_path / "does-not-exist.json")
