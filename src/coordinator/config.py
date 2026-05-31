"""`.mcp.json` consumption with whitelist enforcement (coordinator.md §6 Camada 1).

The coordinator does not trust SDK auto-load: it parses `.mcp.json` itself and
halts loud (`CoordinatorStartupError`) on any server outside `EXPECTED_SERVERS`
(a dev-added debug server left behind) or any required server missing (the named
slices would otherwise KeyError downstream). The parsed `mcp_servers_dict` and
the named slices (`policy_reader_config`, `semgrep_runner_config`) are the
`*_CONFIG` anchors the stage options in §3.2-§3.4 consume.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coordinator.errors import CoordinatorStartupError

EXPECTED_SERVERS: frozenset[str] = frozenset({"policy-reader", "semgrep-runner"})


@dataclass(frozen=True)
class McpServersConfig:
    """Parsed, whitelisted MCP server configuration."""

    mcp_servers_dict: dict[str, Any]
    policy_reader_config: dict[str, Any]
    semgrep_runner_config: dict[str, Any]


def load_mcp_config(path: Path | str = Path(".mcp.json")) -> McpServersConfig:
    """Parse `.mcp.json`, enforce the `EXPECTED_SERVERS` whitelist, and return
    the named-slice config. Raises `CoordinatorStartupError` (halt) on a missing
    file, malformed JSON, an unexpected server, or a missing required server."""
    path = Path(path)
    if not path.is_file():
        raise CoordinatorStartupError(f".mcp.json not found at {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CoordinatorStartupError(f"failed to read/parse {path}: {exc}") from exc

    declared = raw.get("mcpServers", {}) if isinstance(raw, dict) else {}
    if not isinstance(declared, dict):
        raise CoordinatorStartupError(f"{path}: 'mcpServers' must be a JSON object")
    declared_names = set(declared.keys())

    unexpected = declared_names - set(EXPECTED_SERVERS)
    if unexpected:
        raise CoordinatorStartupError(
            f"Unexpected MCP servers in {path}: {sorted(unexpected)} "
            f"(expected only {sorted(EXPECTED_SERVERS)})"
        )
    missing = set(EXPECTED_SERVERS) - declared_names
    if missing:
        raise CoordinatorStartupError(f"Missing required MCP servers in {path}: {sorted(missing)}")

    mcp_servers_dict: dict[str, Any] = {name: declared[name] for name in EXPECTED_SERVERS}
    return McpServersConfig(
        mcp_servers_dict=mcp_servers_dict,
        policy_reader_config=mcp_servers_dict["policy-reader"],
        semgrep_runner_config=mcp_servers_dict["semgrep-runner"],
    )
