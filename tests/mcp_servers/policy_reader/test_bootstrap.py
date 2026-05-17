"""T01 acceptance tests — Loader + handshake `policy://schema-version`.

Each `test_as_*` covers one acceptance scenario from `docs/tasks.md` T01.
Mutators of the fixture `valid_policy_root` are inlined per test to keep
the failure path obvious. Fixtures never touch the real `policy/`.
"""
from __future__ import annotations

import json
from pathlib import Path

import mcp.types as mcp_types
import pytest
import yaml

from mcp_servers.policy_reader import server
from mcp_servers.policy_reader.errors import PolicyLoadError
from mcp_servers.policy_reader.loader import (
    COMPATIBLE_SCHEMA_RANGE,
    load_policy,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_yaml(path: Path, data: object) -> None:
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Premise documentation — FastMCP 3.x resource wrap shape
# ---------------------------------------------------------------------------

async def test_documents_fastmcp_read_resource_shape(
    valid_policy_root: Path, reset_server_state: None,
) -> None:
    """Anchor test documenting the wire shape FastMCP 3.x produces from a
    `@mcp.resource(..., mime_type="application/json")` handler.

    Locked-in observation against FastMCP 3.2.4:
      `mcp.read_resource(uri)` returns `fastmcp.resources.resource.ResourceResult`
      with `.contents: list[ResourceContent]` (FastMCP-internal type, fields
      `content: str` + `mime_type: str`). The MCP-wire equivalent —
      `mcp.types.ReadResourceResult` with `contents: [TextResourceContents]`
      (`text` + `mimeType`) — is produced by calling `.to_mcp_result(uri)` on
      the ResourceResult. AS-7 of `docs/tasks.md` T01 prescribes the wire
      shape (`text`, `mimeType`), so production tests pin against that
      after the `to_mcp_result` conversion. If FastMCP changes this in a
      future release, this test fails first and clearly.
    """
    server._bootstrap(valid_policy_root)

    fastmcp_result = await server.mcp.read_resource("policy://schema-version")
    assert type(fastmcp_result).__name__ == "ResourceResult"
    assert len(fastmcp_result.contents) == 1
    assert type(fastmcp_result.contents[0]).__name__ == "ResourceContent"

    mcp_wire = fastmcp_result.to_mcp_result("policy://schema-version")
    assert isinstance(mcp_wire, mcp_types.ReadResourceResult)
    assert len(mcp_wire.contents) == 1
    assert isinstance(mcp_wire.contents[0], mcp_types.TextResourceContents)


# ---------------------------------------------------------------------------
# AS-1 — Startup OK against the real Policy
# ---------------------------------------------------------------------------

def test_as1_startup_ok_against_real_policy_root() -> None:
    """AS-1. The current state of `policy/` (real artefact) loads without
    exception and exposes header, clauses {POL-000}, and the four
    jurisdictional vocabularies.
    """
    real_policy = Path(__file__).resolve().parents[3] / "policy"

    loaded = load_policy(real_policy)

    assert loaded.header.policy_schema_version == "0.1.0"
    assert loaded.header.policy_version == "0.1.0"
    assert loaded.header.legal_framework == "LGPD"
    assert loaded.header.accepted_law_identifiers == ["LGPD"]

    assert set(loaded.clauses.keys()) == {"POL-000"}
    assert loaded.clauses["POL-000"].clause_type == "definitional"

    assert set(loaded.vocabularies.keys()) == {
        "operation", "lawful_basis", "control", "out_of_scope",
    }
    for name, vocab in loaded.vocabularies.items():
        assert vocab.framework == "LGPD", name
        assert vocab.values, name


# ---------------------------------------------------------------------------
# AS-2 — Missing vocabulary file aborts startup
# ---------------------------------------------------------------------------

def test_as2_aborts_on_missing_vocabulary_file(
    valid_policy_root: Path,
) -> None:
    """AS-2. Removing one of the four jurisdictional vocabulary files
    aborts startup with a message naming the missing file.
    """
    (valid_policy_root / "vocabularies" / "LGPD" / "operation.yaml").unlink()

    with pytest.raises(PolicyLoadError, match=r"operation\.yaml"):
        load_policy(valid_policy_root)


# ---------------------------------------------------------------------------
# AS-3 — Header violations abort startup
# ---------------------------------------------------------------------------

def test_as3_aborts_on_header_missing_field(
    valid_policy_root: Path,
) -> None:
    """AS-3 (first case). Header missing a required field (`legal_framework`)
    aborts with a message citing the SCHEMA rule and the offending field.
    """
    header_path = valid_policy_root / "policy.yaml"
    header = _load_yaml(header_path)
    del header["legal_framework"]
    _write_yaml(header_path, header)

    with pytest.raises(
        PolicyLoadError, match=r"(?s)policy\.yaml.*legal_framework",
    ):
        load_policy(valid_policy_root)


def test_as3_aborts_on_header_schema_version_out_of_range(
    valid_policy_root: Path,
) -> None:
    """AS-3 (second case). Header with `policy_schema_version` outside
    `compatible_schema_range` aborts with a message citing the range.
    """
    header_path = valid_policy_root / "policy.yaml"
    header = _load_yaml(header_path)
    header["policy_schema_version"] = "0.3.0"
    _write_yaml(header_path, header)

    with pytest.raises(
        PolicyLoadError,
        match=r"(?s)policy_schema_version.*compatible_schema_range",
    ):
        load_policy(valid_policy_root)


# ---------------------------------------------------------------------------
# AS-4 — Clause × header schema-version divergence aborts startup
# ---------------------------------------------------------------------------

def test_as4_aborts_on_clause_schema_version_divergence(
    valid_policy_root: Path,
) -> None:
    """AS-4. Header at `0.1.0` (within range), clause at `0.2.0` (outside
    `compatible_schema_range`) aborts with a message naming the divergent
    clause. SCHEMA §4.5: clause carries `policy_schema_version` redundantly
    by design; incompatible divergence aborts loading.
    """
    pol000 = valid_policy_root / "clauses" / "POL-000.yaml"
    raw = _load_yaml(pol000)
    raw["policy_schema_version"] = "0.2.0"
    _write_yaml(pol000, raw)

    with pytest.raises(
        PolicyLoadError,
        match=r"(?s)POL-000.*compatible_schema_range",
    ):
        load_policy(valid_policy_root)


# ---------------------------------------------------------------------------
# AS-5 — Clause citing a law outside accepted_law_identifiers aborts
# ---------------------------------------------------------------------------

def test_as5_aborts_on_top_level_lei_outside_accepted(
    valid_policy_root: Path,
) -> None:
    """AS-5 (top-level case). Synthetic substantive clause with
    `statutory_reference[0].lei: CDC` in a Policy whose header declares
    `accepted_law_identifiers: [LGPD]` aborts.
    """
    pol100 = valid_policy_root / "clauses" / "POL-100.yaml"
    _write_yaml(pol100, {
        "clause_id": "POL-100",
        "title": "Cláusula sintética para teste de AS-5 top-level",
        "clause_type": "substantive",
        "status": "active",
        "policy_schema_version": "0.1.0",
        "statutory_reference": [
            {"lei": "CDC", "artigo": 1},
        ],
        "applies_to": {
            "personal_data_categories": ["dados_de_contato"],
            "operation": ["collection"],
        },
        "control": "consent_required",
        "requirements": [{"id": "R1", "text": "irrelevante"}],
        "exceptions": [],
    })

    with pytest.raises(
        PolicyLoadError,
        match=r"(?s)POL-100.*statutory_reference top-level.*CDC",
    ):
        load_policy(valid_policy_root)


def test_as5_aborts_on_nested_lei_outside_accepted(
    valid_policy_root: Path,
) -> None:
    """AS-5 (nested case — DD-2 extension). Synthetic definitional clause
    whose `defines.entries[0].statutory_reference[0].lei` is `CDC` aborts
    even when the top-level `statutory_reference` is clean. Validates that
    nested references are walked per SCHEMA §7.
    """
    pol101 = valid_policy_root / "clauses" / "POL-101.yaml"
    _write_yaml(pol101, {
        "clause_id": "POL-101",
        "title": "Cláusula sintética para teste de AS-5 aninhado",
        "clause_type": "definitional",
        "status": "active",
        "policy_schema_version": "0.1.0",
        "statutory_reference": [
            {"lei": "LGPD", "artigo": 5},
        ],
        "defines": {
            "vocabulary_kind": "personal_data_categories",
            "entries": [
                {
                    "name": "categoria_teste",
                    "definition": "categoria sintética",
                    "canonical_examples": ["a", "b", "c"],
                    "statutory_reference": [
                        {"lei": "CDC", "artigo": 1},
                    ],
                    "special_category": False,
                },
            ],
        },
    })

    with pytest.raises(
        PolicyLoadError,
        match=r"(?s)POL-101.*defines\.entries\[0\]\.statutory_reference.*CDC",
    ):
        load_policy(valid_policy_root)


# ---------------------------------------------------------------------------
# AS-6 — Empty clauses directory aborts startup
# ---------------------------------------------------------------------------

def test_as6_aborts_on_empty_clauses_dir(valid_policy_root: Path) -> None:
    """AS-6. Empty `clauses/` aborts with the canonical §3.1 message
    ("Política sem cláusulas é configuração inválida do artefato").
    """
    for clause_file in (valid_policy_root / "clauses").glob("POL-*.yaml"):
        clause_file.unlink()

    with pytest.raises(
        PolicyLoadError,
        match=r"Política sem cláusulas é configuração inválida do artefato",
    ):
        load_policy(valid_policy_root)


# ---------------------------------------------------------------------------
# AS-7 — Handshake returns the full triple + compatible_schema_range
# ---------------------------------------------------------------------------

async def test_as7_schema_version_resource_returns_full_handshake(
    valid_policy_root: Path, reset_server_state: None,
) -> None:
    """AS-7. After bootstrap, `policy://schema-version` returns a
    `ReadResourceResult` with `contents: [TextResourceContents]` whose
    `text` decodes to exactly the four-field handshake (values matching
    the header) and `mimeType: "application/json"`.
    """
    server._bootstrap(valid_policy_root)

    fastmcp_result = await server.mcp.read_resource("policy://schema-version")
    mcp_wire = fastmcp_result.to_mcp_result("policy://schema-version")

    assert isinstance(mcp_wire, mcp_types.ReadResourceResult)
    assert len(mcp_wire.contents) == 1

    content = mcp_wire.contents[0]
    assert isinstance(content, mcp_types.TextResourceContents)
    assert content.mimeType == "application/json"

    payload = json.loads(content.text)
    assert payload == {
        "policy_schema_version": "0.1.0",
        "policy_version": "0.1.0",
        "legal_framework": "LGPD",
        "compatible_schema_range": str(COMPATIBLE_SCHEMA_RANGE),
    }


# ---------------------------------------------------------------------------
# AS-8 — Handshake is idempotent
# ---------------------------------------------------------------------------

async def test_as8_schema_version_resource_is_idempotent(
    valid_policy_root: Path, reset_server_state: None,
) -> None:
    """AS-8. Two reads in sequence produce byte-identical payloads."""
    server._bootstrap(valid_policy_root)

    first = (
        await server.mcp.read_resource("policy://schema-version")
    ).to_mcp_result("policy://schema-version")
    second = (
        await server.mcp.read_resource("policy://schema-version")
    ).to_mcp_result("policy://schema-version")

    assert isinstance(first, mcp_types.ReadResourceResult)
    assert isinstance(second, mcp_types.ReadResourceResult)
    assert isinstance(first.contents[0], mcp_types.TextResourceContents)
    assert isinstance(second.contents[0], mcp_types.TextResourceContents)

    assert first.contents[0].text == second.contents[0].text
    assert first.contents[0].mimeType == second.contents[0].mimeType
