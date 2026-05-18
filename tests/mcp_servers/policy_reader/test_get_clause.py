"""T02a acceptance tests — Tool `get_clause`.

Each `test_as_*` covers one acceptance scenario from `docs/tasks.md` T02a.
Wire-level invocation goes through the in-memory `fastmcp.Client`, which
returns `fastmcp.client.client.CallToolResult` with snake_case attributes
(`is_error`, `structured_content`, `content`). T02a adopts the Option B
convention (T02a session): domain envelopes travel in `structured_content`
with the four canonical fields (`errorCode`, `message`, `isRetryable`,
`details`); `content[0].text` reproduces `message`; wire `is_error` stays
`False` and is reserved for protocol-level failures. Consumers
discriminate domain errors by the presence of `errorCode` in
`structured_content`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastmcp import Client
from mcp.types import TextContent

from mcp_servers.policy_reader import server


# ---------------------------------------------------------------------------
# Premise documentation — FastMCP 3.x tool call wire shape
# ---------------------------------------------------------------------------

async def test_documents_fastmcp_tool_call_shape(
    valid_policy_root: Path, reset_server_state: None,
) -> None:
    """Anchor test documenting the wire shape FastMCP 3.x produces from a
    `@mcp.tool` handler invoked via the in-memory `Client`.

    Locked-in observation against FastMCP 3.2.4:
      `Client(server.mcp).call_tool(name, args)` returns
      `fastmcp.client.client.CallToolResult` with snake_case attrs
      (`is_error`, `structured_content`, `content`, `data`, `meta`).

    Two shapes are documented:
      - success: `is_error=False`, `structured_content` carries the clause
        payload (DD-1: as stored by the loader), `content[0]` is a
        `TextContent` with a human-readable rendering.
      - domain error (Option B convention): `is_error=False`,
        `structured_content` carries `{errorCode, message, isRetryable,
        details}`, `content[0].text == message`. Discriminated by presence
        of `errorCode` key in `structured_content`.

    If FastMCP changes the wire shape in a future release, this anchor
    fails first and forces revision of the project's error-envelope
    convention. See DD-6 (T02a session) for the cross-doc debt against
    canonical §5.1.
    """
    server._bootstrap(valid_policy_root)

    async with Client(server.mcp) as client:
        # --- Shape A: success path ---
        ok = await client.call_tool("get_clause", {"clause_id": "POL-000"})
        assert ok.is_error is False
        assert isinstance(ok.structured_content, dict)
        assert "errorCode" not in ok.structured_content
        assert ok.structured_content["clause_id"] == "POL-000"
        assert len(ok.content) == 1
        assert isinstance(ok.content[0], TextContent)
        assert ok.content[0].text  # non-empty rendering

        # --- Shape B: domain error path (Option B) ---
        err = await client.call_tool("get_clause", {"clause_id": "POL-1"})
        assert err.is_error is False  # wire reserved for protocol failures
        assert isinstance(err.structured_content, dict)
        assert err.structured_content["errorCode"] == "INVALID_CLAUSE_ID_FORMAT"
        assert err.structured_content["message"]
        assert err.structured_content["isRetryable"] is False
        assert "details" in err.structured_content
        assert len(err.content) == 1
        assert isinstance(err.content[0], TextContent)
        assert err.content[0].text == err.structured_content["message"]


# ---------------------------------------------------------------------------
# AS-1.a — Active definitional clause (POL-000, polymorphism coverage)
# ---------------------------------------------------------------------------

async def test_as1_returns_active_definitional_clause(
    valid_policy_root: Path, reset_server_state: None,
) -> None:
    """AS-1 (definitional cenário). Active definitional clause is returned
    with `defines` + `out_of_scope` fields; substantive-only fields
    (`applies_to`, `control`, `requirements`, `exceptions`) and `tombstone`
    are absent.
    """
    server._bootstrap(valid_policy_root)

    async with Client(server.mcp) as client:
        result = await client.call_tool("get_clause", {"clause_id": "POL-000"})

    assert result.is_error is False
    payload: dict[str, Any] = result.structured_content
    assert "errorCode" not in payload

    assert payload["clause_id"] == "POL-000"
    assert payload["clause_type"] == "definitional"
    assert payload["status"] == "active"
    assert payload["policy_schema_version"] == "0.1.0"
    assert isinstance(payload["title"], str) and payload["title"]
    assert isinstance(payload["statutory_reference"], list)
    assert payload["statutory_reference"]  # non-empty

    # Definitional-only fields present
    assert isinstance(payload["defines"], dict)
    assert payload["defines"]["vocabulary_kind"] == "personal_data_categories"
    assert "out_of_scope" in payload

    # Substantive-only fields absent; tombstone absent on active
    assert "applies_to" not in payload
    assert "control" not in payload
    assert "requirements" not in payload
    assert "exceptions" not in payload
    assert "tombstone" not in payload

    # content[0].text carries a human-readable summary
    assert result.content[0].text.startswith("POL-000:")


# ---------------------------------------------------------------------------
# AS-1.b — Active substantive clause (POL-001 from pack)
# ---------------------------------------------------------------------------

async def test_as1_returns_active_substantive_clause(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-1 (substantive cenário). Active substantive clause is returned
    with `applies_to`, `control`, `requirements`, `exceptions`;
    definitional-only fields (`defines`, `out_of_scope`) and `tombstone`
    are absent.
    """
    server._bootstrap(policy_root_with_pack_clauses)

    async with Client(server.mcp) as client:
        result = await client.call_tool("get_clause", {"clause_id": "POL-001"})

    assert result.is_error is False
    payload: dict[str, Any] = result.structured_content
    assert "errorCode" not in payload

    assert payload["clause_id"] == "POL-001"
    assert payload["clause_type"] == "substantive"
    assert payload["status"] == "active"

    # Substantive-only fields present
    assert payload["applies_to"] == {
        "personal_data_categories": ["dados_de_contato"],
        "operation": ["collection"],
    }
    assert payload["control"] == "consent_required"
    assert isinstance(payload["requirements"], list) and payload["requirements"]
    assert payload["requirements"][0]["id"] == "R1"
    assert payload["exceptions"] == []

    # Definitional-only fields absent; tombstone absent on active
    assert "defines" not in payload
    assert "out_of_scope" not in payload
    assert "tombstone" not in payload

    # statutory_reference present and populated
    assert payload["statutory_reference"] == [
        {"lei": "LGPD", "artigo": 7, "inciso": 1},
    ]

    assert result.content[0].text.startswith("POL-001:")
    assert "LGPD Art. 7º, I" in result.content[0].text


# ---------------------------------------------------------------------------
# AS-2 — Deprecated clause with tombstone (POL-003 from pack)
# ---------------------------------------------------------------------------

async def test_as2_returns_deprecated_clause_with_tombstone(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-2. Deprecated clause is returned successfully (not an error) with
    a populated `tombstone` block containing `successors`, `effective_until`,
    and `deprecation_reason`.
    """
    server._bootstrap(policy_root_with_pack_clauses)

    async with Client(server.mcp) as client:
        result = await client.call_tool("get_clause", {"clause_id": "POL-003"})

    assert result.is_error is False
    payload: dict[str, Any] = result.structured_content
    assert "errorCode" not in payload  # success, not domain error

    assert payload["clause_id"] == "POL-003"
    assert payload["status"] == "deprecated"

    assert isinstance(payload["tombstone"], dict)
    assert payload["tombstone"]["successors"] == ["POL-004"]
    assert payload["tombstone"]["effective_until"] == "2026-04-01"
    assert payload["tombstone"]["deprecation_reason"]

    # Substantive shape preserved on deprecated
    assert payload["clause_type"] == "substantive"
    assert payload["control"] == "consent_required"

    # content[0].text identifies deprecated state and successors
    text = result.content[0].text
    assert "deprecated" in text
    assert "POL-004" in text


# ---------------------------------------------------------------------------
# AS-3 — INVALID_CLAUSE_ID_FORMAT envelope
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "bad_id",
    ["POL-1", "pol-001", "foo", ""],
    ids=["short_digit", "lowercase", "no_prefix", "empty"],
)
async def test_as3_returns_invalid_clause_id_format_envelope(
    bad_id: str, valid_policy_root: Path, reset_server_state: None,
) -> None:
    """AS-3 (reformulado per Option B). `clause_id` que não casa
    `^POL-\\d{3}$` retorna envelope `INVALID_CLAUSE_ID_FORMAT` em
    `structured_content`; `content[0].text == message`; wire `is_error`
    permanece `False`. Discriminador: presença de `errorCode`.
    """
    server._bootstrap(valid_policy_root)

    async with Client(server.mcp) as client:
        result = await client.call_tool("get_clause", {"clause_id": bad_id})

    assert result.is_error is False  # wire reserved for protocol failures
    payload: dict[str, Any] = result.structured_content
    assert payload["errorCode"] == "INVALID_CLAUSE_ID_FORMAT"
    assert payload["isRetryable"] is False
    assert payload["message"]
    assert payload["details"] == {
        "provided": bad_id,
        "expected_format": r"^POL-\d{3}$",
    }
    assert result.content[0].text == payload["message"]


# ---------------------------------------------------------------------------
# AS-4 — CLAUSE_NOT_FOUND envelope
# ---------------------------------------------------------------------------

async def test_as4_returns_clause_not_found_envelope(
    valid_policy_root: Path, reset_server_state: None,
) -> None:
    """AS-4 (reformulado per Option B). `clause_id` com formato válido mas
    inexistente retorna envelope `CLAUSE_NOT_FOUND` em `structured_content`;
    `content[0].text == message`; wire `is_error` permanece `False`.
    """
    server._bootstrap(valid_policy_root)

    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "get_clause", {"clause_id": "POL-999"},
        )

    assert result.is_error is False
    payload: dict[str, Any] = result.structured_content
    assert payload["errorCode"] == "CLAUSE_NOT_FOUND"
    assert payload["isRetryable"] is False
    assert payload["message"]
    assert payload["details"] == {"clause_id": "POL-999"}
    assert result.content[0].text == payload["message"]
