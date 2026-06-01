"""Phase 2a anchor — Triager prompt rendering (triager §2.2 + §5.1, A5).

`build_triager_prompt` renders the §5.1 format-string template via `.format()`:
the four single-brace PR refs are substituted, and the double-brace `{{…}}` JSON
examples survive as single-brace valid JSON. RED against the Phase-1 stub (which
threads the four refs but carries no §5.1 JSON examples).
"""
from __future__ import annotations

from coordinator.prompts import build_triager_prompt
from subagents.triager.models import TriagerInput


def test_triager_prompt_renders_all_refs() -> None:
    scope = TriagerInput(
        pr_number=42,
        base_ref="main",
        head_ref="feature/user-registration",
        repo_url="https://github.com/example/app",
    )
    rendered = build_triager_prompt(scope)

    # all four PR refs substituted into the §5.1 template
    assert "42" in rendered
    assert "main" in rendered
    assert "feature/user-registration" in rendered
    assert "https://github.com/example/app" in rendered

    # double-brace JSON examples survived .format() as single-brace valid JSON
    assert '{"decision": "proceed"' in rendered
    assert '{"decision": "skip"' in rendered

    # no escaped/unrendered braces leaked to the model
    assert "{{" not in rendered
    assert "}}" not in rendered
    assert "{pr_number}" not in rendered
    assert "{repo_url}" not in rendered
