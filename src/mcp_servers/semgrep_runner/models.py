"""Pydantic models for the semgrep-runner MCP server.

T05 introduces only `LoadedRules` — the structural envelope of the rule
set state populated by `loader.load_rules` at startup. Models for
`ScanMetadata`, `Finding`, `Location`, and error envelopes (canonical §5
six errorCodes) land in T06 alongside the real `scan_diff` implementation.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoadedRules(BaseModel):
    """Server state populated at startup with the curated Semgrep rule set.

    `rule_files` carries absolute paths as strings (not `Path`) for native
    JSON serialisation without custom encoders. On Windows, paths
    serialised to JSON may appear with escaped backslashes
    (e.g. `"C:\\\\repo\\\\rules\\\\foo.yaml"`); downstream consumers that
    parse the value should normalise via `Path` if path semantics matter.

    `min_length=1` on `rule_files` is defence-in-depth — the primary
    empty-rule-set check lives in `loader.load_rules`, which raises
    `RulesLoadError` with a Portuguese message before this model is ever
    constructed. A `ValidationError` from here at runtime indicates a
    regression in the primary check, not an expected condition.
    """

    model_config = ConfigDict(extra="forbid")

    rules_version: str = Field(min_length=1)
    rule_files: list[str] = Field(min_length=1)
    rules_root: str = Field(min_length=1)
