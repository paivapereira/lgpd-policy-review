"""Live e2e: Camada-3-MVP gate over COMP-001 — one of the 2 ratified validations.

`@pytest.mark.live` → excluded from the default run (addopts `-m 'not live'`). Run:
`uv run pytest -m live tests/harness/test_camada3_gate_live.py -s`. Needs an
authenticated Claude Agent SDK session + semgrep on PATH (Gate #3 prereqs).

This is the FIRST end-to-end verification of the bare `rule_id` post-#105: a
full-path `rule_id` failure is a normalization/staleness issue, NOT Classifier
drift. Honesty disposition (plano §3.5 / G): a divergence is a datum reported, never
re-run away — so this test asserts once and surfaces the diff; it does not retry.
"""
from __future__ import annotations

import shutil

import pytest

from eval.harness.camada3_gate import _CASES, _run_case


@pytest.mark.live
async def test_camada3_gate_comp001_live() -> None:
    if shutil.which("semgrep") is None:
        pytest.skip("semgrep not on PATH (ADR-0010 prereq)")
    result, summary, evidence = await _run_case(_CASES["COMP-001"])
    assert result.passed, (
        f"COMP-001 STRICT failures: {result.strict_failures}; "
        f"advisory: {result.advisory_notes}\n{evidence}\n{summary}"
    )
