"""G0 live arm — real MatcherOutput / DetectorOutput under a realistic payload.

The structural baseline (RESULTS.md scenarios A/B/C) used structural stand-ins
and proved: `oneOf`/discriminator -> structured_output None; enum-tag
(`$defs` + `anyOf[T,null]` + array-of-objects) -> populated & validates.

This probe closes the residual question the static arm cannot: does a REAL
multi-finding `MatcherOutput` / `DetectorOutput` (the #502/#571 wrapper is
payload-sensitive, not just schema-sensitive — so a trivial output would give a
false green) come back in `structured_output` and validate DIRECTLY via
`model_validate`, with NO `{"output": {...}}` wrapper nesting?

Pinned target: claude-agent-sdk==0.2.87. Lockdown quintupla + tools=[].
Run (PowerShell, no WSL):  uv run python scripts/smoke_tests/sdk_output_format_complex/g0_real_models_live.py
Record the table + verdict in RESULTS.md (gates.md: the gate outcome is the
persisted evidence).
"""
from __future__ import annotations

import asyncio
import json
import sys

try:
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query
except ImportError:
    sys.exit('Install: uv add "claude-agent-sdk==0.2.87"')

from subagents.detector.models import DetectorOutput
from subagents.matcher.models import MatcherOutput

_MATCHER_PROMPT = (
    "Emit a MatcherOutput with EXACTLY three findings, each a different verdict, "
    "matching the provided JSON schema. Use these (fabricated, synthetic) values:\n"
    "1) file='users/registration.py', line=42, snippet='db.insert(email=email)', "
    "rule_id='BR-EMAIL', data_categories=['email'], operation_type='collection', "
    "verdict='compliant', evidence='collection guarded by consent check', "
    "policy_clause_ref='POL-005', policy_schema_version='0.1.0', policy_version='1.2.0', "
    "legal_framework='LGPD'.\n"
    "2) file='users/registration.py', line=88, snippet='log.info(cpf)', rule_id='BR-CPF', "
    "data_categories=['cpf'], operation_type='collection', verdict='violation_candidate', "
    "evidence='CPF written to logs without basis', contradicted_requirement='R1', "
    "policy_clause_ref='POL-007', policy_schema_version='0.1.0', policy_version='1.2.0', "
    "legal_framework='LGPD', requires_human_review=true.\n"
    "3) file='cache.py', line=10, snippet='cache.set(session_id, ts)', rule_id='BR-SESS', "
    "data_categories=['session_id'], operation_type='collection', verdict='not_applicable', "
    "reason='session_id is not personal data governed by POL-005', "
    "policy_clause_ref='POL-000', policy_schema_version='0.1.0', policy_version='1.2.0', "
    "legal_framework='LGPD'."
)

_DETECTOR_PROMPT = (
    "Emit a DetectorOutput with EXACTLY three findings + provenance, matching the schema. "
    "Findings: (file,line,rule_id,snippet,surrounding_context) = "
    "('a.py',12,'BR-CPF','x=cpf','# ctx a'), ('a.py',30,'BR-EMAIL','y=email','# ctx b'), "
    "('b.py',5,'BR-CNPJ','z=cnpj','# ctx c'). "
    "provenance: rules_version='2026.04.1', semgrep_version='1.163.0', "
    "scan_metadata={base_ref:'"
    + "a" * 40
    + "', head_ref:'"
    + "b" * 40
    + "', files_scanned:2, elapsed_seconds:1.5}."
)


def _lockdown(schema: dict) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt="You output only structured data matching the declared schema.",
        tools=[],
        allowed_tools=[],
        mcp_servers={},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
        output_format={"type": "json_schema", "schema": schema},
        max_turns=4,
    )


async def _probe(label: str, prompt: str, model: type) -> dict:
    options = _lockdown(model.model_json_schema())
    last_result: ResultMessage | None = None
    raised: Exception | None = None
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                last_result = message  # no break — trailing events
    except Exception as exc:  # noqa: BLE001 — probe records, does not mask
        raised = exc

    out: dict = {"label": label, "raised": repr(raised) if raised else None}
    if last_result is None:
        out["verdict"] = "STREAM_FAILURE (no ResultMessage)"
        return out
    so = last_result.structured_output
    out["subtype"] = last_result.subtype
    out["structured_output_is_none"] = so is None
    out["has_output_wrapper"] = isinstance(so, dict) and set(so.keys()) == {"output"}
    if so is None:
        out["verdict"] = "FAIL — structured_output None (wrapper/oneOf regression)"
        return out
    target = so["output"] if out["has_output_wrapper"] else so
    try:
        model.model_validate(target)
        out["verdict"] = (
            "PASS (direct)" if not out["has_output_wrapper"] else "PASS (needs ['output'] unwrap)"
        )
    except Exception as exc:  # noqa: BLE001
        out["verdict"] = f"FAIL — model_validate raised: {exc!r}"
    return out


async def _main() -> int:
    results = [
        await _probe("MatcherOutput", _MATCHER_PROMPT, MatcherOutput),
        await _probe("DetectorOutput", _DETECTOR_PROMPT, DetectorOutput),
    ]
    print(json.dumps(results, indent=2, ensure_ascii=False))
    ok = all(r.get("verdict", "").startswith("PASS (direct)") for r in results)
    print("\nG0 LIVE VERDICT:", "PASS — direct validate, no wrapper" if ok else "REVIEW — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
