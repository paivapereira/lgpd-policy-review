"""Internal Pydantic models for parsing Semgrep CLI JSON output.

Private to the component — they exist to gate the untrusted JSON from
`subprocess.run(["semgrep", ...])` into typed Python before mapping to
the public `Finding` / `ScanMetadata` shapes in `models.py`. All models
use `ConfigDict(extra="ignore")` because Semgrep 1.163.0 emits several
additional top-level and nested fields the component does not consume —
empirical observation in pre-flight 3.C/3.D against the project's pinned
binary surfaced `time`, `engine_requested`, `skipped_rules`,
`profiling_results` at top-level and `metadata`, `fingerprint`, `lines`,
`validation_state`, `engine_kind` inside `extra`. Locking these to a
forbidden-extras policy would force a model change every time Semgrep
adds an output field.

Coverage scope: top-level `version`, `results`, `errors`, `paths`;
per-result `check_id`, `path`, `start`, `end`, `extra.severity`,
`extra.message`; per-error `code`, `type`, `message`. The `errors[]`
array is parsed even when Semgrep exits non-zero (DD-T06-22) to refine
INSUFFICIENT_GIT_HISTORY discrimination (DD-T06-6 lazy layer reads
`errors[].message` for `"BaselineHandler initialization"` /
`"shallow"` / `"merge-base"` / `"cannot find common ancestor"`).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _SemgrepLocation(BaseModel):
    """`start` / `end` of a Semgrep result. Line and col are 1-indexed.

    Semgrep also emits `offset` (byte offset from file start) — skipped
    via `extra="ignore"` because the component locates findings by
    line/col only.
    """

    model_config = ConfigDict(extra="ignore")

    line: int = Field(ge=1)
    col: int = Field(ge=1)


class _SemgrepResultExtra(BaseModel):
    """`extra` block of a Semgrep result.

    `severity` is uppercase as emitted by Semgrep (`INFO` / `WARNING` /
    `ERROR`); normalised to lowercase by the mapper to `Finding`.
    `message` is the rule's `message` field from the YAML. Other extra
    fields (`metadata`, `fingerprint`, `lines`, `validation_state`,
    `engine_kind`) are skipped — `lines` in particular is
    `"requires login"` for OSS-no-token scans (pre-flight 3.D), so the
    component derives snippet from filesystem read instead (DD-T06-23).
    """

    model_config = ConfigDict(extra="ignore")

    severity: str = Field(min_length=1)
    message: str = Field(min_length=1)


class _SemgrepResult(BaseModel):
    """One result entry in Semgrep JSON output `results[]`."""

    model_config = ConfigDict(extra="ignore")

    check_id: str = Field(min_length=1)
    path: str = Field(min_length=1)
    start: _SemgrepLocation
    end: _SemgrepLocation
    extra: _SemgrepResultExtra


class _SemgrepError(BaseModel):
    """One error entry in Semgrep JSON output `errors[]` (DD-T06-22).

    Populated even on non-zero exit; carries finer classification than
    the process exit code. Empirically observed in pre-flight 3.E /
    3.G: `type="Rule parse error"` on exit 2 from invalid pattern;
    `message` containing `"BaselineHandler initialization"` on exit 2
    in shallow repos; nested `code=5` entry inside an exit 7 wrapper
    when YAML is unparseable.

    `type` and `message` default to empty string because some Semgrep
    error shapes carry only `code` plus `long_msg` / `short_msg`
    variants (e.g., `UnknownLanguageError` per pre-flight 3.E). The
    component reads `message` for substring matching when present and
    falls back to a stderr excerpt otherwise.
    """

    model_config = ConfigDict(extra="ignore")

    code: int
    type: str = Field(default="")
    message: str = Field(default="")


class _SemgrepRunOutput(BaseModel):
    """Top-level Semgrep JSON output structure.

    `paths` is parsed as an opaque dict because Semgrep nests both
    `scanned` (list of repo-relative paths actually scanned) and
    `skipped` (filter-omitted) under it; the component only reads
    `paths["scanned"]` count to derive `ScanMetadata.files_scanned`.
    Treating the whole `paths` block as `dict[str, Any]` avoids locking
    in Semgrep's intermediate structure.
    """

    model_config = ConfigDict(extra="ignore")

    version: str = Field(min_length=1)
    results: list[_SemgrepResult] = Field(default_factory=list)
    errors: list[_SemgrepError] = Field(default_factory=list)
    paths: dict[str, Any] = Field(default_factory=dict)
