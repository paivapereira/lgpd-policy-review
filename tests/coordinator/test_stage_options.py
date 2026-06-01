"""Phase 2b anchors — Classifier/Matcher stage `ClaudeAgentOptions` tools axis
(coordinator §3.3 / §3.4; run.py `_classifier_options` / `_matcher_options`).

Order-sensitive `list ==` (DD-c): the anchor style is strict (test-strategy.md) and
run.py encodes a deliberate built-in order — the Classifier's `tools` and `allowed_tools`
differ in the order of the two resource built-ins. Green from the (fixed, not re-wired)
Phase 1 wiring; these lock it.
"""
from __future__ import annotations

from typing import Any, cast

from coordinator.config import McpServersConfig
from coordinator.run import _classifier_options, _matcher_options


def _cfg() -> McpServersConfig:
    server = cast(Any, {"command": "uv"})  # value only threads into mcp_servers; shape irrelevant here
    return McpServersConfig(
        mcp_servers_dict={"policy-reader": server, "semgrep-runner": server},
        policy_reader_config=server,
        semgrep_runner_config=server,
    )


def test_classifier_options_tools_exact() -> None:
    opts = _classifier_options(_cfg())
    assert opts.tools == ["Read", "Grep", "ReadMcpResourceTool", "ListMcpResourcesTool"]
    # allowed_tools intentionally orders the two resource built-ins differently (DD-c)
    assert opts.allowed_tools == ["Read", "Grep", "ListMcpResourcesTool", "ReadMcpResourceTool"]


def test_matcher_options_tools_exact() -> None:
    opts = _matcher_options(_cfg())
    # tools is NOT [] (DD-M30): the check-all reads policy://catalog via the resource
    # built-ins, which are governed by `tools` (availability), unlike the Reporter (Gate 6).
    assert opts.tools == ["Read", "ReadMcpResourceTool", "ListMcpResourcesTool"]
    assert opts.allowed_tools == [
        "ListMcpResourcesTool",
        "ReadMcpResourceTool",
        "mcp__policy-reader__check_applicability",
        "mcp__policy-reader__get_clause",
        "mcp__policy-reader__find_clauses_by_law_article",
    ]
