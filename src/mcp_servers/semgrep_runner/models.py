"""Pydantic models for the semgrep-runner MCP server.

T05 introduced `LoadedRules` — the structural envelope of the rule set
state populated by `loader.load_rules` at startup. T06 adds the public
shapes returned by `scan_diff`: `Location`, `Finding`, `ScanMetadata`,
`ScanSuccessPayload`, and `ErrorEnvelope` (canonical §5 six errorCodes).

Wire-shape convention (Option B, per ADR-0002 §3 amendment 2026-05-17):
the error envelope is serialised into `structured_content` of the
returned `ToolResult`; `content[0].text` reproduces `message`; wire
`isError` stays `False` and is reserved for protocol-level failures.
Consumers discriminate success vs domain error by the presence of
`errorCode` in `structured_content`. See `ErrorEnvelope` docstring for
the full convention rationale.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# Resolved git refs are emitted as 40-char hex SHA-1 per canonical §6.
_SHA1_PATTERN = r"^[a-f0-9]{40}$"


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


class Location(BaseModel):
    """File location of a finding (canonical §4.2 lines 134-140).

    All coordinates are 1-indexed (Semgrep convention preserved through
    the component). `path` is repo-root-relative — Semgrep emits relative
    paths when invoked with `--baseline-commit` per pre-flight 3.D
    empirical observation against 1.163.0.
    """

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    start_line: int = Field(ge=1)
    start_col: int = Field(ge=1)
    end_line: int = Field(ge=1)
    end_col: int = Field(ge=1)


class Finding(BaseModel):
    """One candidate finding emitted by `scan_diff` (canonical §4.2).

    `rule_severity` is normalised to lowercase by the mapper from
    Semgrep's uppercase emission (`INFO`/`WARNING`/`ERROR`); the
    `Literal` constraint here makes the mapper invariant explicit and
    rejects any unexpected severity value via Pydantic ValidationError
    (caught upstream as `SEMGREP_EXECUTION_FAILED` per DD-T06-8).

    `snippet` is derived from the filesystem by the component (DD-T06-23)
    — Semgrep OSS without `SEMGREP_APP_TOKEN` populates `extra.lines =
    "requires login"` rather than the actual code excerpt, and canonical
    §8 last bullet vetoes the token. Empty string is a legitimate value
    when the source file was deleted between commits.
    """

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(min_length=1)
    rule_severity: Literal["info", "warning", "error"]
    rule_message: str = Field(min_length=1)
    location: Location
    snippet: str


class ScanMetadata(BaseModel):
    """Per-scan dynamic provenance (canonical §6 + §4.2 lines 124-128).

    `base_ref` and `head_ref` are the 40-char hex commits resolved via
    `git rev-parse --verify {ref}^{commit}` (DD-T06-4), NOT the input
    refs passed by the caller. Provenance trail: the caller's branch
    name or relative ref is recorded only via input args; the resolved
    SHA is the auditable trace.
    """

    model_config = ConfigDict(extra="forbid")

    base_ref: Annotated[str, Field(pattern=_SHA1_PATTERN)]
    head_ref: Annotated[str, Field(pattern=_SHA1_PATTERN)]
    files_scanned: int = Field(ge=0)
    elapsed_seconds: float = Field(ge=0)


class ScanSuccessPayload(BaseModel):
    """Top-level `structuredContent` for a successful `scan_diff` return
    (canonical §4.2 lines 116-145).

    `rules_version` and `semgrep_version` are top-level static provenance
    — they do not change during the server lifetime for a given rule set
    or binary. `scan_metadata` carries per-scan dynamic provenance.
    `findings` is sorted by `(location.path, location.start_line)` per
    canonical §4.2 line 148 (implemented in `tools.scan_diff` via
    `sorted()` before constructing the payload — DD-T06-21).
    """

    model_config = ConfigDict(extra="forbid")

    rules_version: str = Field(min_length=1)
    semgrep_version: str = Field(min_length=1)
    scan_metadata: ScanMetadata
    findings: list[Finding]


class ErrorEnvelope(BaseModel):
    """Canonical error envelope shape for tool returns (canonical §5.1).

    Field names are camelCase deliberately — they are JSON keys consumed
    by downstream agents and must match the contract in canonical §5.1
    / §5.4 verbatim. The Python attribute names follow the same casing
    because `model_dump()` is used directly on the wire (no alias
    indirection).

    Wire-shape convention adopted by this project (Option B from T02a):
    the envelope is serialised into `structuredContent` of the wire
    `CallToolResult`; `content[0].text` reproduces `message` as a human
    fallback; wire `isError` stays `False` and is reserved for
    protocol-level failures (input schema rejection, tool-not-found).
    Consumers discriminate success vs domain error by the presence of
    `errorCode` in `structuredContent`. Canonical §5.1 (as amended in
    canonical-sync-B / ADR-0002 §3 amendment) prescribes this Option B
    placement explicitly; the FastMCP 3.2.4 framework constraint
    documented in the ADR amendment is the structural reason.
    """

    model_config = ConfigDict(extra="forbid")

    errorCode: str = Field(min_length=1)
    message: str = Field(min_length=1)
    isRetryable: bool
    details: dict[str, Any] = Field(default_factory=dict)
