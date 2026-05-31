"""Coordinator termination union (coordinator.md §3.6).

`CoordinatorResult` is the discriminated union returned to the external caller
(GitHub Action / exercise script): a success `CoordinatorReport` carrying the
captured `emit_report` payload, or a `CoordinatorError` carrying the typed §5
cause, the blame `stage`, and a human `coverage_gap` annotation.

Provisional form: rich audit fields (e.g. `partial_scratchpad_path`) are
deferred to Milestone D when the GitHub Action contract and scratchpad
retention are designed (§3.6).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CoordinatorReport:
    """Success path — the `ReportPayload` dict captured from `emit_report` (§3.5)."""

    payload: dict[str, Any]


@dataclass
class CoordinatorError:
    """Any pipeline halt. `cause` is a typed §5 exception; `stage` is blame;
    `coverage_gap` is the human annotation of what was not analyzed."""

    cause: Exception
    stage: str
    coverage_gap: str


CoordinatorResult = CoordinatorReport | CoordinatorError
