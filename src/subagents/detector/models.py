"""Detector output contract (detector.md §3.1, §3.2).

`DetectorFinding` follows strip-opinion / keep-provenance (DD-D1): exactly the
five fields, with `rule_severity` / `rule_message` from `scan_diff` deliberately
dropped (the Semgrep detection opinion does not cross the boundary).

`ScanProvenance` is per-scan, carried on the envelope — never per-finding
(DD-D3). It mirrors the `scan_diff` provenance shape (semgrep-runner canonical
§6); per A4 it is defined fresh here (the subagent layer does not import from
`mcp_servers`), and `base_ref`/`head_ref` are plain non-empty strings rather
than the server's SHA-1 pattern, since the subagent echoes provenance through
the LLM and we do not want a non-SHA echo to fail validation.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DetectorFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file: str  # repo-relative path (scan_diff location.path)
    line: int  # candidate line (scan_diff location.start_line)
    rule_id: str  # Semgrep rule identifier
    snippet: str  # code excerpt
    surrounding_context: str  # +/-N lines window added by the Detector (DD-D2)


class ScanMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_ref: str = Field(min_length=1)  # resolved baseline ref (echoed from scan_diff)
    head_ref: str = Field(min_length=1)
    files_scanned: int = Field(ge=0)
    elapsed_seconds: float = Field(ge=0)


class ScanProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules_version: str
    semgrep_version: str
    scan_metadata: ScanMetadata


class DetectorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings: list[DetectorFinding]
    provenance: ScanProvenance
