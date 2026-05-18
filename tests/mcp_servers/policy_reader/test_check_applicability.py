"""T03 acceptance tests — Tool `check_applicability`.

Each `test_as*` covers one acceptance scenario from `docs/tasks.md` T03;
AS-2 is split into AS-2a (legal_basis absent) and AS-2b (legal_basis not
canonical) per `.claude/rules/test-strategy.md` §"Granularity calibration".
Wire-level invocation goes through the in-memory `fastmcp.Client` and
asserts Option B convention (envelope discriminated by presence of
`errorCode` in `structured_content`; `is_error` always `False`).

Two anchor tests beyond the AS coverage (DD-T03-9):
- `test_provenance_trinque_in_every_verdict_path` — parametrize over the
  four verdict paths to assert the trinque (policy_schema_version,
  policy_version, legal_framework) is present and equal to the loaded
  header in every success path.
- `test_deprecated_clause_returns_envelope_not_tombstone` — assimetria
  canonical §2.2 / §5.3 between `get_clause` (success-with-tombstone) and
  `check_applicability` (envelope retryable) on the same deprecated clause.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastmcp import Client

from mcp_servers.policy_reader import server
from mcp_servers.policy_reader.loader import load_policy


# ---------------------------------------------------------------------------
# AS-1 — compliant
# ---------------------------------------------------------------------------

async def test_as1_returns_compliant_verdict(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-1. POL-001 (consent_required) + dados_de_contato + collection +
    legal_basis='consent' + destination='external_service' → compliant.
    Provenance trinque presente. Campo `destination` é opcional per canonical
    §4.3 (linha 525) e exercitado aqui sem efeito sobre o veredito — garante
    que StructuredContext aceita o campo (regression test contra remoção
    futura do campo do modelo)."""
    server._bootstrap(policy_root_with_pack_clauses)
    async with Client(server.mcp) as client:
        result = await client.call_tool("check_applicability", {
            "clause_id": "POL-001",
            "structured_context": {
                "data_categories": ["dados_de_contato"],
                "operation": "collection",
                "legal_basis": "consent",
                "destination": "external_service",
            },
        })
    assert result.is_error is False
    sc = result.structured_content
    assert sc is not None
    assert "errorCode" not in sc
    assert sc["verdict"] == "compliant"
    assert sc["policy_clause_ref"] == "POL-001"
    assert "consent" in sc["evidence"]
    assert sc["legal_framework"] == "LGPD"
    assert "policy_schema_version" in sc
    assert "policy_version" in sc


# ---------------------------------------------------------------------------
# AS-2 — violation_candidate (split per granularity calibration)
# ---------------------------------------------------------------------------

async def test_as2a_violation_candidate_when_legal_basis_absent(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-2a. POL-001 + dados_de_contato + collection sem legal_basis →
    violation_candidate citando R1 e a omissão do campo. Sub-caso 'ausente'
    da árvore de decisão R1 — separado de AS-2b por DD-T03-7 e por
    test-strategy.md §Granularity."""
    server._bootstrap(policy_root_with_pack_clauses)
    async with Client(server.mcp) as client:
        result = await client.call_tool("check_applicability", {
            "clause_id": "POL-001",
            "structured_context": {
                "data_categories": ["dados_de_contato"],
                "operation": "collection",
            },
        })
    assert result.is_error is False
    sc = result.structured_content
    assert sc is not None
    assert sc["verdict"] == "violation_candidate"
    assert sc["policy_clause_ref"] == "POL-001"
    assert sc["contradicted_requirement"] == "R1"
    assert "omite" in sc["evidence"]


async def test_as2b_violation_candidate_when_legal_basis_not_consent(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-2b. POL-001 + dados_de_contato + collection + legal_basis=
    'legitimate_interest' (não consent) → violation_candidate citando R1
    e o valor fora do vocabulário canônico. Sub-caso 'valor diferente'."""
    server._bootstrap(policy_root_with_pack_clauses)
    async with Client(server.mcp) as client:
        result = await client.call_tool("check_applicability", {
            "clause_id": "POL-001",
            "structured_context": {
                "data_categories": ["dados_de_contato"],
                "operation": "collection",
                "legal_basis": "legitimate_interest",
            },
        })
    assert result.is_error is False
    sc = result.structured_content
    assert sc is not None
    assert sc["verdict"] == "violation_candidate"
    assert sc["contradicted_requirement"] == "R1"
    assert "legitimate_interest" in sc["evidence"]


# ---------------------------------------------------------------------------
# AS-3 — indeterminate (anonymization_required)
# ---------------------------------------------------------------------------

async def test_as3_indeterminate_for_anonymization_required(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-3. POL-002 (anonymization_required) + dados_de_perfil_comportamental
    + collection → indeterminate. structured_context não tem campo para
    declarar transformação efetiva; análise estática local de PR não decide
    esta dimensão (canonical §7.3). verification_scope identifica o que um
    revisor humano precisa verificar."""
    server._bootstrap(policy_root_with_pack_clauses)
    async with Client(server.mcp) as client:
        result = await client.call_tool("check_applicability", {
            "clause_id": "POL-002",
            "structured_context": {
                "data_categories": ["dados_de_perfil_comportamental"],
                "operation": "collection",
            },
        })
    assert result.is_error is False
    sc = result.structured_content
    assert sc is not None
    assert sc["verdict"] == "indeterminate"
    assert sc["policy_clause_ref"] == "POL-002"
    vs = sc["verification_scope"]
    assert vs["dimension"] == "upstream_state"
    assert vs["prescribed_treatment"] == "anonymization_required"
    assert vs["verification_target"]
    assert "anonimização" in vs["verification_target"]


# ---------------------------------------------------------------------------
# AS-4 — not_applicable (applicability mismatch)
# ---------------------------------------------------------------------------

async def test_as4_not_applicable_when_category_mismatch(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-4. POL-004 governa dados_de_documentos_oficiais; context declara
    dados_de_contato → intersecção vazia → not_applicable com reason
    descrevendo o desencontro de escopos (DD-T03-8 step 8)."""
    server._bootstrap(policy_root_with_pack_clauses)
    async with Client(server.mcp) as client:
        result = await client.call_tool("check_applicability", {
            "clause_id": "POL-004",
            "structured_context": {
                "data_categories": ["dados_de_contato"],
                "operation": "collection",
                "legal_basis": "consent",
            },
        })
    assert result.is_error is False
    sc = result.structured_content
    assert sc is not None
    assert sc["verdict"] == "not_applicable"
    assert sc["policy_clause_ref"] == "POL-004"
    assert "Sem intersecção" in sc["reason"]


# ---------------------------------------------------------------------------
# AS-5 — not_applicable (MVP scope filter) — behavioral proxy (DD-T03-7 A)
# ---------------------------------------------------------------------------

async def test_as5_scope_filter_short_circuits_before_matching(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-5 via behavioral proxy (DD-T03-7 Opção A).

    POL-001 + dados_de_contato + legal_basis='consent' produziria
    `compliant` se o matching rodasse. Com operation='use' (fora do MVP),
    retorna not_applicable. O contraste de veredito é a evidência
    estrutural de que o filtro MVP curto-circuita antes do matching
    (DD-T03-3 + DD-T03-8 step 7 < step 8). Robusto a refactor: não acopla
    ao nome do helper privado de matching."""
    server._bootstrap(policy_root_with_pack_clauses)
    async with Client(server.mcp) as client:
        result = await client.call_tool("check_applicability", {
            "clause_id": "POL-001",
            "structured_context": {
                "data_categories": ["dados_de_contato"],
                "operation": "use",
                "legal_basis": "consent",
            },
        })
    assert result.is_error is False
    sc = result.structured_content
    assert sc is not None
    assert sc["verdict"] == "not_applicable"
    assert sc["policy_clause_ref"] == "POL-001"
    assert "ADR-0007" in sc["reason"]


# ---------------------------------------------------------------------------
# AS-7 — CLAUSE_DEPRECATED envelope (retryable)
# ---------------------------------------------------------------------------

async def test_as7_clause_deprecated_returns_retryable_envelope(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """AS-7. POL-003 (deprecated, sucessor POL-004) → envelope retryable
    com details {clause_id, successors, deprecation_reason}. Wire stays
    `is_error: False` (Option B); discriminação por presença de errorCode."""
    server._bootstrap(policy_root_with_pack_clauses)
    async with Client(server.mcp) as client:
        result = await client.call_tool("check_applicability", {
            "clause_id": "POL-003",
            "structured_context": {
                "data_categories": ["dados_de_documentos_oficiais"],
                "operation": "collection",
                "legal_basis": "consent",
            },
        })
    assert result.is_error is False
    sc = result.structured_content
    assert sc is not None
    assert sc["errorCode"] == "CLAUSE_DEPRECATED"
    assert sc["isRetryable"] is True
    assert sc["details"]["clause_id"] == "POL-003"
    assert sc["details"]["successors"] == ["POL-004"]
    assert sc["details"]["deprecation_reason"]


# ---------------------------------------------------------------------------
# AS-8 — input validation envelopes (parametrize)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("ctx_overrides", "expected_error_code"),
    [
        (
            {"data_categories": [], "operation": "collection"},
            "EMPTY_DATA_CATEGORIES",
        ),
        (
            {
                "data_categories": ["dados_inventados"],
                "operation": "collection",
            },
            "INVALID_DATA_CATEGORY",
        ),
        (
            {
                "data_categories": ["dados_de_contato"],
                "operation": "operacao_inventada",
            },
            "INVALID_OPERATION",
        ),
    ],
    ids=["empty_categories", "invalid_category", "invalid_operation"],
)
async def test_as8_input_validation_envelopes(
    ctx_overrides: dict[str, Any],
    expected_error_code: str,
    policy_root_with_pack_clauses: Path,
    reset_server_state: None,
) -> None:
    """AS-8 parametrize. Os 3 errorCodes de input validation
    (EMPTY_DATA_CATEGORIES, INVALID_DATA_CATEGORY, INVALID_OPERATION).
    accepted_values em INVALID_DATA_CATEGORY e INVALID_OPERATION é dinâmico
    (canonical §5.4 nota dinâmica); EMPTY não carrega accepted_values."""
    server._bootstrap(policy_root_with_pack_clauses)
    async with Client(server.mcp) as client:
        result = await client.call_tool("check_applicability", {
            "clause_id": "POL-001",
            "structured_context": ctx_overrides,
        })
    assert result.is_error is False
    sc = result.structured_content
    assert sc is not None
    assert sc["errorCode"] == expected_error_code
    assert sc["isRetryable"] is False
    if expected_error_code != "EMPTY_DATA_CATEGORIES":
        assert "accepted_values" in sc["details"]
        assert isinstance(sc["details"]["accepted_values"], list)


# ---------------------------------------------------------------------------
# Coverage — DefinitionalClause path (DD-T03-12 emergente em Fase 2.C)
# ---------------------------------------------------------------------------

async def test_definitional_clause_returns_not_applicable(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """Cobertura — `check_applicability` sobre POL-000 (definitional)
    retorna `not_applicable` com reason citando o tipo de cláusula.

    POL-000 define vocabulário (data_categories canônicos); não prescreve
    control e não carrega `applies_to`. Aplicabilidade não é definida
    para clauses definitional — verdict honesto é `not_applicable`.

    DD-T03-12 emergente: este caminho de retorno foi adicionado em
    Fase 2.C como guard estrutural antes do branch em
    `clause.applies_to[...]` (que quebraria com AttributeError em
    DefinitionalClause). Adição expande a superfície contratual da tool
    para além dos 4 paths previstos (compliant/violation_candidate/
    indeterminate/not_applicable via applicability mismatch ou MVP scope);
    o quinto path — cláusula definitional — merece cobertura própria."""
    server._bootstrap(policy_root_with_pack_clauses)
    async with Client(server.mcp) as client:
        result = await client.call_tool("check_applicability", {
            "clause_id": "POL-000",
            "structured_context": {
                "data_categories": ["dados_de_contato"],
                "operation": "collection",
            },
        })
    assert result.is_error is False
    sc = result.structured_content
    assert sc is not None
    assert sc["verdict"] == "not_applicable"
    assert sc["policy_clause_ref"] == "POL-000"
    assert "definitional" in sc["reason"]


# ---------------------------------------------------------------------------
# Anchor 1 — provenance trinque em todos os 4 vereditos (DD-T03-9)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("clause_id", "ctx", "expected_verdict"),
    [
        (
            "POL-001",
            {
                "data_categories": ["dados_de_contato"],
                "operation": "collection",
                "legal_basis": "consent",
            },
            "compliant",
        ),
        (
            "POL-001",
            {
                "data_categories": ["dados_de_contato"],
                "operation": "collection",
                "legal_basis": "legitimate_interest",
            },
            "violation_candidate",
        ),
        (
            "POL-002",
            {
                "data_categories": ["dados_de_perfil_comportamental"],
                "operation": "collection",
            },
            "indeterminate",
        ),
        (
            "POL-004",
            {
                "data_categories": ["dados_de_contato"],
                "operation": "collection",
                "legal_basis": "consent",
            },
            "not_applicable",
        ),
        (
            "POL-001",
            {
                "data_categories": ["dados_de_contato"],
                "operation": "use",
                "legal_basis": "consent",
            },
            "not_applicable",
        ),
    ],
    ids=[
        "compliant",
        "violation_candidate",
        "indeterminate",
        "not_applicable_mismatch",
        "not_applicable_mvp_scope",
    ],
)
async def test_provenance_trinque_in_every_verdict_path(
    clause_id: str,
    ctx: dict[str, Any],
    expected_verdict: str,
    policy_root_with_pack_clauses: Path,
    reset_server_state: None,
) -> None:
    """Anchor — trinque (policy_schema_version, policy_version,
    legal_framework) presente em todos os 4 vereditos de sucesso, igual ao
    header carregado da Política. Cobertura por construção, não por
    confiança que AS-1..AS-5 checaram individualmente; quebra detectável
    se alguém remover o trinque de uma das 4 paths sem atualizar a AS
    correspondente. Coincide com AS-6 da tasks.md.

    Strict assertion (anchor): cada campo do trinque é comparado
    exatamente ao header — não substring, não presença."""
    state = load_policy(policy_root_with_pack_clauses)
    expected_trinque = {
        "policy_schema_version": state.header.policy_schema_version,
        "policy_version": state.header.policy_version,
        "legal_framework": state.header.legal_framework,
    }
    server._bootstrap(policy_root_with_pack_clauses)
    async with Client(server.mcp) as client:
        result = await client.call_tool("check_applicability", {
            "clause_id": clause_id,
            "structured_context": ctx,
        })
    sc = result.structured_content
    assert sc is not None
    assert sc["verdict"] == expected_verdict
    for key, value in expected_trinque.items():
        assert sc[key] == value, (
            f"trinque mismatch on {key} for verdict {expected_verdict}: "
            f"expected {value!r}, got {sc[key]!r}"
        )


# ---------------------------------------------------------------------------
# Anchor 2 — deprecated assimetria check_applicability vs get_clause
# ---------------------------------------------------------------------------

async def test_deprecated_clause_returns_envelope_not_tombstone(
    policy_root_with_pack_clauses: Path, reset_server_state: None,
) -> None:
    """Anchor — assimetria canonical §2.2 / §5.3.

    Sobre a mesma cláusula POL-003 deprecated:
    - `check_applicability` → envelope CLAUSE_DEPRECATED retryable em
      structured_content (avaliação de aplicabilidade sobre deprecated é
      erro de uso).
    - `get_clause` → sucesso com bloco tombstone no payload (recuperação
      histórica é legítima).

    As duas tools têm semânticas deliberadamente diferentes sobre
    deprecated. Protege contra refactor 'DRY' que tente unificar
    tratamento entre as tools."""
    server._bootstrap(policy_root_with_pack_clauses)
    async with Client(server.mcp) as client:
        check_result = await client.call_tool("check_applicability", {
            "clause_id": "POL-003",
            "structured_context": {
                "data_categories": ["dados_de_documentos_oficiais"],
                "operation": "collection",
                "legal_basis": "consent",
            },
        })
        get_result = await client.call_tool("get_clause", {
            "clause_id": "POL-003",
        })

    check_sc = check_result.structured_content
    assert check_sc is not None
    assert "errorCode" in check_sc
    assert check_sc["errorCode"] == "CLAUSE_DEPRECATED"
    assert check_sc["isRetryable"] is True

    get_sc = get_result.structured_content
    assert get_sc is not None
    assert "errorCode" not in get_sc
    assert get_sc["status"] == "deprecated"
    assert "tombstone" in get_sc
    assert get_sc["tombstone"]["successors"] == ["POL-004"]
