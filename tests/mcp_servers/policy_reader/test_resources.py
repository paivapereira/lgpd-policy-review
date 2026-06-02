"""T04 acceptance tests — Resources `policy://catalog` and
`policy://vocabularies`.

Each `test_as*_` covers one acceptance scenario from `docs/tasks.md` T04;
anchor tests labelled distinctly per `.claude/rules/test-strategy.md`
exercise contract invariants by code (conditional `successors`,
natural-order ordering not relying on dict iteration order).

Wire-access pattern follows T01 (DD-T04-14): `server.mcp.read_resource(uri)`
yields a FastMCP-internal `ResourceResult`, converted to MCP-wire
`ReadResourceResult` via `.to_mcp_result(uri)`. The text payload reaches
the consumer via `.contents[0].text` (JSON string); byte-idempotência is
asserted on that string directly (DD-T04-11).
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import mcp.types as mcp_types
import pytest

from mcp_servers.policy_reader import server, tools
from mcp_servers.policy_reader.models import (
    Clause,
    DefinitionalClause,
    LoadedPolicy,
    PolicyHeader,
    StatutoryReferenceEntry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _read_catalog() -> list[dict]:
    fastmcp_result = await server.mcp.read_resource("policy://catalog")
    mcp_wire = fastmcp_result.to_mcp_result("policy://catalog")
    assert isinstance(mcp_wire, mcp_types.ReadResourceResult)
    content = mcp_wire.contents[0]
    assert isinstance(content, mcp_types.TextResourceContents)
    assert content.mimeType == "application/json"
    return json.loads(content.text)


async def _read_vocabularies() -> dict[str, dict]:
    fastmcp_result = await server.mcp.read_resource("policy://vocabularies")
    mcp_wire = fastmcp_result.to_mcp_result("policy://vocabularies")
    assert isinstance(mcp_wire, mcp_types.ReadResourceResult)
    content = mcp_wire.contents[0]
    assert isinstance(content, mcp_types.TextResourceContents)
    assert content.mimeType == "application/json"
    return json.loads(content.text)


def _stub_definitional(clause_id: str) -> Clause:
    """Build a minimal DefinitionalClause stub for anchor 2.

    Anchor 2 only inspects `clause_id`; remaining fields are filled with
    placeholder values that satisfy the model validators
    (`statutory_reference: min_length=1`, `policy_schema_version` semver
    pattern). Active status keeps `tombstone` None per the
    `_tombstone_iff_deprecated` validator.
    """
    return DefinitionalClause(
        clause_id=clause_id,
        title=f"stub {clause_id}",
        policy_schema_version="0.1.0",
        statutory_reference=[StatutoryReferenceEntry(lei="LGPD", artigo=1)],
        defines={"vocabulary_kind": "personal_data_categories", "entries": []},
    )


# ---------------------------------------------------------------------------
# AS-1 — Catalog lists clauses in natural POL-NNN order
# ---------------------------------------------------------------------------

async def test_as1_catalog_lists_clauses_in_natural_order(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-1. Five clauses (POL-000 real + POL-001..POL-004 pack) appear
    ordered POL-000, POL-001, POL-002, POL-003, POL-004."""
    server._bootstrap(policy_root_with_pack_clauses)

    items = await _read_catalog()

    assert [item["clause_id"] for item in items] == [
        "POL-000", "POL-001", "POL-002", "POL-003", "POL-004",
    ]


# ---------------------------------------------------------------------------
# AS-2 — Each item carries the five contractual fields; successors
#         appears iff status == "deprecated"
# ---------------------------------------------------------------------------

async def test_as2_catalog_item_carries_five_contractual_fields(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-2. Every item carries `clause_id`, `title`, `status`,
    `article_sources_summary`; deprecated items additionally carry
    `successors` (active items do NOT carry the key)."""
    server._bootstrap(policy_root_with_pack_clauses)

    items = await _read_catalog()
    by_id = {item["clause_id"]: item for item in items}

    # Every item carries the four base fields populated.
    for item in items:
        assert item["clause_id"].startswith("POL-")
        assert isinstance(item["title"], str) and item["title"]
        assert item["status"] in {"active", "deprecated"}
        assert isinstance(item["article_sources_summary"], list)
        assert item["article_sources_summary"]  # non-empty

    # Active clauses do NOT carry `successors`.
    active_item = by_id["POL-001"]
    assert active_item["status"] == "active"
    assert "successors" not in active_item

    # Deprecated clauses DO carry `successors` (list of POL-NNN strings).
    deprecated_item = by_id["POL-003"]
    assert deprecated_item["status"] == "deprecated"
    assert deprecated_item["successors"] == ["POL-004"]


# ---------------------------------------------------------------------------
# AS-3 — Catalog byte-idempotent on `.contents[0].text`
# ---------------------------------------------------------------------------

async def test_as3_catalog_byte_idempotent(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-3. Two sequential reads produce byte-identical text payloads."""
    server._bootstrap(policy_root_with_pack_clauses)

    first = (
        await server.mcp.read_resource("policy://catalog")
    ).to_mcp_result("policy://catalog")
    second = (
        await server.mcp.read_resource("policy://catalog")
    ).to_mcp_result("policy://catalog")

    assert isinstance(first.contents[0], mcp_types.TextResourceContents)
    assert isinstance(second.contents[0], mcp_types.TextResourceContents)
    assert first.contents[0].text == second.contents[0].text
    assert first.contents[0].mimeType == second.contents[0].mimeType


# ---------------------------------------------------------------------------
# AS-4 — Vocabularies aggregates the four jurisdictional vocabs under LGPD
# ---------------------------------------------------------------------------

async def test_as4_vocabularies_aggregates_four_keys_lgpd(
    valid_policy_root: Path, reset_server_state: None,
) -> None:
    """AS-4. Against the real LGPD Policy, the resource exposes the four
    jurisdictional keys (each `{schema_version, framework: "LGPD", values[...]}`
    populated from `policy/vocabularies/LGPD/`) plus the structural
    `data_categories` key (Option B; `framework` omitted — its full structural
    contract is pinned by
    `test_vocabularies_data_categories_structural_contract`)."""
    server._bootstrap(valid_policy_root)

    payload = await _read_vocabularies()

    assert set(payload.keys()) == {
        "operation", "lawful_basis", "control", "out_of_scope", "data_categories",
    }
    for key in ("operation", "lawful_basis", "control", "out_of_scope"):
        vocab = payload[key]
        assert vocab["framework"] == "LGPD", key
        assert vocab["schema_version"] == "0.1.0", key
        assert isinstance(vocab["values"], list) and vocab["values"], key


# ---------------------------------------------------------------------------
# AS-5 — Vocabularies framework-agnostic against synthetic GDPR fixture
# ---------------------------------------------------------------------------

async def test_as5_vocabularies_framework_agnostic_against_gdpr(
    policy_root_with_synthetic_gdpr: Path, reset_server_state: None,
) -> None:
    """AS-5. Against a Policy declaring `legal_framework: GDPR` with
    `policy/vocabularies/GDPR/` populated, the resource reflects the GDPR
    content without any code change — operative assertions distinguish
    by name (`consent_gdpr` ≠ LGPD `consent`) rather than cosmetic
    structure."""
    server._bootstrap(policy_root_with_synthetic_gdpr)

    payload = await _read_vocabularies()

    assert set(payload.keys()) == {
        "operation", "lawful_basis", "control", "out_of_scope", "data_categories",
    }

    assert payload["operation"]["framework"] == "GDPR"
    assert {v["name"] for v in payload["operation"]["values"]} == {"collection"}

    assert payload["lawful_basis"]["framework"] == "GDPR"
    assert (
        {v["name"] for v in payload["lawful_basis"]["values"]}
        == {"consent_gdpr"}
    )

    assert payload["control"]["framework"] == "GDPR"
    assert (
        {v["name"] for v in payload["control"]["values"]}
        == {"consent_required"}
    )

    assert payload["out_of_scope"]["framework"] == "GDPR"
    assert (
        {v["name"] for v in payload["out_of_scope"]["values"]}
        == {"out_of_geographic_scope"}
    )

    # The structural `data_categories` vocab is framework-agnostic too: it is
    # derived from the fixture's POL-000 (single entry `identification_data`),
    # and — being structural, not jurisdictional — carries NO `framework` field.
    dc = payload["data_categories"]
    assert "framework" not in dc
    assert [v["name"] for v in dc["values"]] == ["identification_data"]


# ---------------------------------------------------------------------------
# AS-6 — Vocabularies byte-idempotent on `.contents[0].text`
# ---------------------------------------------------------------------------

async def test_as6_vocabularies_byte_idempotent(
    valid_policy_root: Path, reset_server_state: None,
) -> None:
    """AS-6. Two sequential reads produce byte-identical text payloads."""
    server._bootstrap(valid_policy_root)

    first = (
        await server.mcp.read_resource("policy://vocabularies")
    ).to_mcp_result("policy://vocabularies")
    second = (
        await server.mcp.read_resource("policy://vocabularies")
    ).to_mcp_result("policy://vocabularies")

    assert isinstance(first.contents[0], mcp_types.TextResourceContents)
    assert isinstance(second.contents[0], mcp_types.TextResourceContents)
    assert first.contents[0].text == second.contents[0].text
    assert first.contents[0].mimeType == second.contents[0].mimeType


# ---------------------------------------------------------------------------
# Anchor 1 — `successors` field present IFF status == "deprecated"
# (DD-T04-9)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("clause_id", "expect_successors"),
    [
        ("POL-001", False),  # active
        ("POL-003", True),   # deprecated
    ],
)
async def test_catalog_successors_field_iff_deprecated(
    clause_id: str,
    expect_successors: bool,
    policy_root_with_pack_clauses: Path,
    reset_server_state: None,
) -> None:
    """Anchor — `successors` is present in a catalog item IFF the clause
    status is `deprecated`. AS-2 covers the contract by example; this
    anchor cristallises the invariant by parametrised construction so a
    refactor that uniformises entries (e.g., adding `successors: []` to
    active items, or stripping it from deprecated ones) fails loudly.
    """
    server._bootstrap(policy_root_with_pack_clauses)

    items = await _read_catalog()
    by_id = {item["clause_id"]: item for item in items}
    entry = by_id[clause_id]

    if expect_successors:
        assert "successors" in entry
        assert isinstance(entry["successors"], list)
        assert len(entry["successors"]) >= 1
    else:
        assert "successors" not in entry


# ---------------------------------------------------------------------------
# Anchor 2 — `tools.get_catalog` sorts explicitly, not via dict order
# (DD-T04-10)
# ---------------------------------------------------------------------------

def test_get_catalog_sorts_explicitly_not_relying_on_dict_order() -> None:
    """Anchor — the resource's `sorted()` is load-bearing in
    `tools.get_catalog`.

    The loader sorts `clauses_dir.glob("POL-*.yaml")` before iterating,
    so `state.clauses` populated by the loader is already in natural
    order — AS-1 cannot distinguish "loader sorted" from "resource
    sorted". This anchor exercises the pure function with a `LoadedPolicy`
    whose `clauses` dict is deliberately constructed in non-natural
    order; the result must still be sorted. Layered with AS-1 by
    contract scope: AS-1 tests the wire under natural conditions, this
    anchor tests the function contract under conditions the loader
    cannot produce.
    """
    header = PolicyHeader(
        policy_schema_version="0.1.0",
        policy_version="0.1.0",
        legal_framework="LGPD",
        accepted_law_identifiers=["LGPD"],
        policy_owner="test",
        effective_date=date(2026, 1, 1),
        last_revision=date(2026, 1, 1),
    )
    shuffled: dict[str, Clause] = {
        "POL-003": _stub_definitional("POL-003"),
        "POL-000": _stub_definitional("POL-000"),
        "POL-004": _stub_definitional("POL-004"),
        "POL-001": _stub_definitional("POL-001"),
        "POL-002": _stub_definitional("POL-002"),
    }
    state = LoadedPolicy(
        header=header,
        clauses=shuffled,
        vocabularies={},
    )

    result = tools.get_catalog(state)

    assert [item["clause_id"] for item in result] == [
        "POL-000", "POL-001", "POL-002", "POL-003", "POL-004",
    ]


# ---------------------------------------------------------------------------
# Anchor 3 — structural `data_categories` key: nine POL-000 tokens, sorted,
#            names-only, `framework` omitted (Option B)
# ---------------------------------------------------------------------------

# The nine canonical data-category tokens defined by the real POL-000
# (`policy/clauses/POL-000.yaml` `defines.entries[].name`). The structural
# `data_categories` vocabulary on `policy://vocabularies` is derived from these.
_POL000_CATEGORY_TOKENS = {
    "dados_de_identificacao",
    "dados_de_documentos_oficiais",
    "dados_de_contato",
    "dados_de_localizacao",
    "dados_de_autenticacao",
    "dados_financeiros",
    "dados_de_saude",
    "dados_biometricos",
    "dados_de_perfil_comportamental",
}


async def test_vocabularies_data_categories_structural_contract(
    valid_policy_root: Path,
    reset_server_state: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Anchor — the structural `data_categories` key (Option B) is composed at
    the resource boundary from POL-000, NOT stored as a jurisdictional vocab.

    Pins, by code, the three invariants the spec (`canonical.md` §3.3) declares:
    (1) the nine POL-000 tokens appear in `sorted()` order — load-bearing for
    the byte-idempotency contract (AS-6) across server restarts, where `set`
    iteration order is not stable; (2) `framework` is OMITTED — the absence is
    what distinguishes the structural layer from the four jurisdictional vocabs
    in the payload itself; (3) the production default is names-only (each value
    is `{name}` exactly), so the experiment-only `canonical_examples`
    enrichment does NOT leak when its env var is unset.
    """
    monkeypatch.delenv("POLICY_READER_EXPOSE_CATEGORY_EXAMPLES", raising=False)
    server._bootstrap(valid_policy_root)

    payload = await _read_vocabularies()
    dc = payload["data_categories"]

    assert "framework" not in dc  # structural-layer marker
    assert dc["schema_version"] == "0.1.0"
    assert [v["name"] for v in dc["values"]] == sorted(_POL000_CATEGORY_TOKENS)
    assert all(set(v.keys()) == {"name"} for v in dc["values"])  # names-only


async def test_data_categories_examples_appended_only_when_env_set(
    valid_policy_root: Path,
    reset_server_state: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Anchor — the C2 enrichment (`canonical_examples`) is gated behind the
    experiment-only env var, default OFF.

    With `POLICY_READER_EXPOSE_CATEGORY_EXAMPLES` set, each category entry gains
    a `canonical_examples` list (still `framework`-less, still sorted). This
    pins the env gate so a refactor cannot silently (a) leak examples into the
    production names-only default, or (b) break the experiment's C2 arm. The
    default-off direction is covered by
    `test_vocabularies_data_categories_structural_contract`.
    """
    monkeypatch.setenv("POLICY_READER_EXPOSE_CATEGORY_EXAMPLES", "1")
    server._bootstrap(valid_policy_root)

    payload = await _read_vocabularies()
    dc = payload["data_categories"]

    assert "framework" not in dc
    assert [v["name"] for v in dc["values"]] == sorted(_POL000_CATEGORY_TOKENS)
    by_name = {v["name"]: v for v in dc["values"]}
    assert "canonical_examples" in by_name["dados_de_identificacao"]
    assert "nome" in by_name["dados_de_identificacao"]["canonical_examples"]
    # `cpf` is a canonical_example of dados_de_documentos_oficiais in POL-000 —
    # the source form of the R6 category ambiguity the experiment accounts for.
    assert "cpf" in by_name["dados_de_documentos_oficiais"]["canonical_examples"]
