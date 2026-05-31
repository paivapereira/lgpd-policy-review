"""Phase 2a acceptance — Triager stage (triager §9.1/§9.3) under a mocked SDK.

Exercises the real Triager wiring (`build_triager_prompt` rendering §5.1 +
`_triager_options` with system_prompt=None, DD-4) through the Branch B driver:
a proceed/skip decision is captured and validated as a `TriagerDecision`, and a
`success`+`refusal` ResultMessage is discriminated to `SubagentRefusedTask`
(§9.3) — not consumed as (possibly absent) structured_output.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from coordinator import driver
from coordinator.errors import SubagentRefusedTask
from coordinator.prompts import build_triager_prompt
from coordinator.run import _triager_options
from subagents.triager.models import TriagerDecision, TriagerInput


def _scope() -> TriagerInput:
    return TriagerInput(
        pr_number=42, base_ref="main", head_ref="feature/x", repo_url="https://github.com/ex/app"
    )


async def _run_triager(tmp_path: Path, monkeypatch: Any, sdk: Any, *, result: Any) -> Any:
    monkeypatch.setattr("coordinator.driver.query", sdk.make_query([result]))
    return await driver.run_branch_b_stage(
        stage="triager",
        prompt=build_triager_prompt(_scope()),  # renders §5.1 (smoke: no .format KeyError)
        options=_triager_options(),  # system_prompt=None (DD-4) constructs cleanly
        output_model=TriagerDecision,
        scratchpad_name="01-triager.json",
        run_path=tmp_path,
        run_id="r1",
    )


async def test_as1_triager_proceed_captured(tmp_path, monkeypatch, sdk) -> None:
    obj = await _run_triager(
        tmp_path,
        monkeypatch,
        sdk,
        result=sdk.result(
            subtype="success",
            structured_output={
                "decision": "proceed",
                "relevance_summary": "PR adiciona schema em src/users/ com CPF e email.",
            },
        ),
    )
    assert isinstance(obj, TriagerDecision)
    assert obj.decision == "proceed"
    assert obj.relevance_summary  # non-empty (§9.3)
    assert obj.skip_reason is None


async def test_as2_triager_skip_captured(tmp_path, monkeypatch, sdk) -> None:
    obj = await _run_triager(
        tmp_path,
        monkeypatch,
        sdk,
        result=sdk.result(
            subtype="success",
            structured_output={
                "decision": "skip",
                "skip_reason": "PR contém apenas mudanças em docs/.",
            },
        ),
    )
    assert isinstance(obj, TriagerDecision)
    assert obj.decision == "skip"
    assert obj.skip_reason  # non-empty (§9.3)
    assert obj.relevance_summary is None


async def test_as3_triager_refusal(tmp_path, monkeypatch, sdk) -> None:
    # §9.3 — subtype="success" + stop_reason="refusal" => SubagentRefusedTask,
    # discriminated BEFORE consuming (possibly absent) structured_output.
    with pytest.raises(SubagentRefusedTask):
        await _run_triager(
            tmp_path,
            monkeypatch,
            sdk,
            result=sdk.result(subtype="success", stop_reason="refusal", structured_output=None),
        )
