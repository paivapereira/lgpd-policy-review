"""T02b acceptance tests — Tool `find_clauses_by_law_article`.

Each `test_as_*` covers one acceptance scenario from `docs/tasks.md` T02b.
`test_polymorphic_mix_at_art_5` is an additional anchor (not an AS): it
exercises canonical §4.2's anti-uniformization invariant by code — the tool
must return heterogeneous `clause_type` lists when the same article is
referenced by both definitional and substantive clauses, and the algorithm
must not filter/coerce that heterogeneity away.

Wire-level invocation goes through the in-memory `fastmcp.Client`, which
returns `fastmcp.client.client.CallToolResult` with snake_case attributes
(`is_error`, `structured_content`, `content`). The wire shape itself is
documented in `test_get_clause.py::test_documents_fastmcp_tool_call_shape`
and not duplicated here.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
from fastmcp import Client
from mcp.types import TextContent

from mcp_servers.policy_reader import server

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_POLICY = REPO_ROOT / "policy"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SYNTHETIC_X_YAML = """\
clause_id: POL-901
title: "Fixture sintética T02b — substantive em Art. 5 sem inciso"
clause_type: substantive
status: active
policy_schema_version: "0.1.0"

statutory_reference:
  - lei: LGPD
    artigo: 5

applies_to:
  personal_data_categories:
    - dados_de_contato
  operation:
    - collection

control: consent_required

requirements:
  - id: R1
    text: >
      Requisito sintético mínimo para satisfazer SubstantiveClause; cláusula
      existe apenas para exercitar a semântica prefix-hierarchical de
      `find_clauses_by_law_article` (AS-2 + anchor polimórfico).

exceptions: []
"""

_SYNTHETIC_Y_YAML = """\
clause_id: POL-902
title: "Fixture sintética T02b — substantive em Art. 5 inciso I"
clause_type: substantive
status: active
policy_schema_version: "0.1.0"

statutory_reference:
  - lei: LGPD
    artigo: 5
    inciso: 1

applies_to:
  personal_data_categories:
    - dados_de_contato
  operation:
    - collection

control: consent_required

requirements:
  - id: R1
    text: >
      Requisito sintético mínimo para satisfazer SubstantiveClause; cláusula
      existe apenas para exercitar a semântica prefix-hierarchical de
      `find_clauses_by_law_article` (AS-2 + anchor polimórfico).

exceptions: []
"""


def _write_synthetic_art5_root(tmp_path: Path) -> Path:
    """Build a Policy root that carries POL-000 (real, definitional, Art. 5)
    plus two synthetic substantive clauses anchored at LGPD Art. 5:
    POL-901 without `inciso` and POL-902 with `inciso: 1`.

    The triple (POL-000, POL-901, POL-902) supports both AS-2 narrow
    (query `{lei: LGPD, artigo: 5, inciso: 1}` → only POL-902) and the
    polymorphic-mix anchor (query `{lei: LGPD, artigo: 5}` → all three,
    mixing 1 definitional + 2 substantive).
    """
    root = tmp_path / "policy"
    shutil.copytree(REAL_POLICY, root)
    (root / "clauses" / "POL-901.yaml").write_text(
        _SYNTHETIC_X_YAML, encoding="utf-8",
    )
    (root / "clauses" / "POL-902.yaml").write_text(
        _SYNTHETIC_Y_YAML, encoding="utf-8",
    )
    return root


@pytest.fixture
def synthetic_art5_root(tmp_path: Path) -> Path:
    return _write_synthetic_art5_root(tmp_path)


def _ids(payload: dict[str, Any]) -> list[str]:
    return [c["clause_id"] for c in payload["clauses"]]


# ---------------------------------------------------------------------------
# AS-1 — Broad search by artigo returns the matching list
# ---------------------------------------------------------------------------

async def test_as1_matches_by_artigo(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-1. Query `{lei: LGPD, artigo: 7}` returns all active clauses
    whose `statutory_reference` begins with LGPD Art. 7º — POL-001 and
    POL-004 in the pack. POL-003 (deprecated, same anchor) is filtered out;
    AS-3 asserts that filter independently.
    """
    server._bootstrap(policy_root_with_pack_clauses)

    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "find_clauses_by_law_article",
            {"lei": "LGPD", "artigo": 7},
        )

    assert result.is_error is False
    payload: dict[str, Any] = result.structured_content
    assert "errorCode" not in payload

    returned_ids = _ids(payload)
    assert "POL-001" in returned_ids
    assert "POL-004" in returned_ids
    assert "POL-003" not in returned_ids  # deprecated, filtered
    assert returned_ids == sorted(returned_ids)  # canonical §4.2 ordering

    # content[0].text summarises the query result
    assert isinstance(result.content[0], TextContent)
    assert "LGPD Art. 7º" in result.content[0].text


# ---------------------------------------------------------------------------
# AS-2 — Prefix-hierarchical match semantics
# ---------------------------------------------------------------------------

async def test_as2_narrow_query_excludes_general_stored(
    synthetic_art5_root: Path, reset_server_state: None,
) -> None:
    """AS-2 (narrow). Query `{lei: LGPD, artigo: 5, inciso: 1}` is strictly
    more specific than POL-901's stored entry `{lei: LGPD, artigo: 5}` and
    than POL-000's top-level `{lei: LGPD, artigo: 5}`; only POL-902 (with
    matching `inciso: 1`) is returned. Spec ≤ stored is the matching rule:
    a stored entry without `inciso` does not start hierarchically with a
    query that carries `inciso`.
    """
    server._bootstrap(synthetic_art5_root)

    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "find_clauses_by_law_article",
            {"lei": "LGPD", "artigo": 5, "inciso": 1},
        )

    assert result.is_error is False
    payload: dict[str, Any] = result.structured_content
    assert "errorCode" not in payload

    returned_ids = _ids(payload)
    assert returned_ids == ["POL-902"]
    assert "POL-901" not in returned_ids
    assert "POL-000" not in returned_ids


async def test_as2_broad_query_matches_general_and_specific_stored(
    synthetic_art5_root: Path, reset_server_state: None,
) -> None:
    """AS-2 (broad). Query `{lei: LGPD, artigo: 5}` equals POL-901's stored
    entry and is a prefix of POL-902's stored entry, so both match. POL-000
    (definitional, same broad anchor) also matches and appears in the
    result — the polymorphic-mix anchor asserts that explicitly.
    """
    server._bootstrap(synthetic_art5_root)

    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "find_clauses_by_law_article",
            {"lei": "LGPD", "artigo": 5},
        )

    assert result.is_error is False
    payload: dict[str, Any] = result.structured_content
    assert "errorCode" not in payload

    returned_ids = set(_ids(payload))
    assert {"POL-901", "POL-902"}.issubset(returned_ids)


# ---------------------------------------------------------------------------
# AS-3 — Deprecated clauses excluded from results
# ---------------------------------------------------------------------------

async def test_as3_deprecated_excluded(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-3. POL-003 is deprecated and anchored at LGPD Art. 7º, I — by
    matching alone it would belong in the AS-1 result, but the contract
    excludes deprecated clauses (canonical §4.2 line 362). Filter is
    structural in the algorithm, not an artefact of any single AS.
    """
    server._bootstrap(policy_root_with_pack_clauses)

    async with Client(server.mcp) as client:
        result_broad = await client.call_tool(
            "find_clauses_by_law_article",
            {"lei": "LGPD", "artigo": 7},
        )
        result_narrow = await client.call_tool(
            "find_clauses_by_law_article",
            {"lei": "LGPD", "artigo": 7, "inciso": 1},
        )

    for result in (result_broad, result_narrow):
        assert result.is_error is False
        payload: dict[str, Any] = result.structured_content
        assert "errorCode" not in payload
        assert "POL-003" not in _ids(payload)


# ---------------------------------------------------------------------------
# AS-4 — Empty list is success, not error
# ---------------------------------------------------------------------------

async def test_as4_empty_list_is_not_error(
    valid_policy_root: Path, reset_server_state: None,
) -> None:
    """AS-4. Valid specification with no matching clauses returns
    `{clauses: []}` with wire `is_error: False` and no `errorCode`. The
    rendered text uses the canonical "Nenhuma cláusula referencia ..."
    phrasing (canonical §4.2 line 472).
    """
    server._bootstrap(valid_policy_root)

    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "find_clauses_by_law_article",
            {"lei": "LGPD", "artigo": 50},
        )

    assert result.is_error is False
    payload: dict[str, Any] = result.structured_content
    assert "errorCode" not in payload
    assert payload == {"clauses": []}

    text = result.content[0].text
    assert text == "Nenhuma cláusula referencia LGPD Art. 50º."


# ---------------------------------------------------------------------------
# AS-5 — INVALID_LAW_IDENTIFIER envelope
# ---------------------------------------------------------------------------

async def test_as5_invalid_law_identifier_envelope(
    valid_policy_root: Path, reset_server_state: None,
) -> None:
    """AS-5. `lei` outside the Policy header's `accepted_law_identifiers`
    yields the `INVALID_LAW_IDENTIFIER` envelope: `errorCode` present,
    `isRetryable: False`, `details = {provided, accepted_values}` populated
    from the loaded header (not hardcoded). `content[0].text == message`.
    Wire `is_error` stays `False` per Option B.
    """
    server._bootstrap(valid_policy_root)

    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "find_clauses_by_law_article",
            {"lei": "GDPR", "artigo": 6},
        )

    assert result.is_error is False
    payload: dict[str, Any] = result.structured_content
    assert payload["errorCode"] == "INVALID_LAW_IDENTIFIER"
    assert payload["isRetryable"] is False
    assert payload["message"]
    assert payload["details"] == {
        "provided": "GDPR",
        "accepted_values": ["LGPD"],
    }
    assert result.content[0].text == payload["message"]


# ---------------------------------------------------------------------------
# Anchor — polymorphic-mix invariant (canonical §4.2 anti-uniformization)
# ---------------------------------------------------------------------------

async def test_polymorphic_mix_at_art_5(
    synthetic_art5_root: Path, reset_server_state: None,
) -> None:
    """Anchor (non-AS). Broad query at LGPD Art. 5 returns POL-000
    (definitional), POL-901 and POL-902 (substantive). Asserts the
    anti-uniformization invariant of canonical §4.2 by code: the result
    list mixes `clause_type: definitional` and `clause_type: substantive`,
    and the algorithm does NOT filter/coerce by type. The breakdown line
    `(N definitional, M substantive)` only appears for heterogeneous
    results, so the rendered text is also asserted here.
    """
    server._bootstrap(synthetic_art5_root)

    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "find_clauses_by_law_article",
            {"lei": "LGPD", "artigo": 5},
        )

    assert result.is_error is False
    payload: dict[str, Any] = result.structured_content
    assert "errorCode" not in payload

    returned = payload["clauses"]
    assert len(returned) == 3
    assert _ids(payload) == ["POL-000", "POL-901", "POL-902"]

    types = {c["clause_type"] for c in returned}
    assert types == {"definitional", "substantive"}

    text = result.content[0].text
    assert text == (
        "3 cláusulas encontradas para LGPD Art. 5º "
        "(1 definitional, 2 substantive)."
    )
