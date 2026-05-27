# Gate report — Milestone A

**Sessão:** #25 — 2026-05-19
**Branch:** `main` (pós-merge T04, PR #46)
**Mecanismo:** manual exercise via MCP Inspector v0.21.2 CLI mode (`npx @modelcontextprotocol/inspector --cli ...`)
**Políticas exercitadas:**
- `policy/` (LGPD real) — Fases A.1 a A.4
- `tests/mcp_servers/policy_reader/fixtures/synthetic_gdpr/` (GDPR stub) — Fase A.5
**Pré-requisito procedural:** POL-001..POL-004 copiados temporariamente de `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/` para `policy/clauses/` durante Fase A.4; revertidos ao final da sessão.
**Critério de aprovação:** ADR-0008 §3, gate milestone-level — manual exercise validando cada Dado/Quando/Então das RFs declaradas em `docs/tasks.md` §Milestone A.

## Sumário

Todas as 5 RFs declaradas como cobertas pelo gate Milestone A em `docs/tasks.md` foram ancoradas empiricamente. **Gate aprovado.**

| RF (refs em `docs/REQUIREMENTS.md`) | Escopo | Status | Cenário ancorador |
|---|---|---|---|
| RF-004-parcial | avaliação de conformidade sobre `collection` | ✅ | `check_applicability(POL-001, operation=storage)` → `not_applicable` + `reason` citando ADR-0007 D3 |
| RF-005 | veredito `indeterminate` como honestidade epistêmica | ✅ | `check_applicability(POL-002, dados_de_perfil_comportamental)` → `indeterminate` + `verification_scope` completo (`dimension`, `prescribed_treatment`, `verification_target`) |
| RF-007-parcial | composição intra-jurisdição via `accepted_law_identifiers` | ✅ | `find_clauses_by_law_article(lei=GDPR)` → envelope `INVALID_LAW_IDENTIFIER` com `details.accepted_values: ["LGPD"]` lido dinamicamente do header |
| RF-008-parcial | substituição de framework sem alteração de código | ✅ | `POLICY_READER_ROOT=synthetic_gdpr` → `legal_framework: "GDPR"` propagado em `schema-version`, `catalog`, `vocabularies` e renderers; **zero modificação em `src/` ou `policy/`** entre A.1 e A.5 |
| RF-009 | provenance temporal e jurisdicional em vereditos | ✅ | Trinca `(policy_schema_version, policy_version, legal_framework)` presente em 6/6 vereditos de `check_applicability`; payload `policy://schema-version` carrega 4 campos canônicos |

## Fases executadas

### A.1 — Discovery (handshake e capabilities)

- `resources/list` → 3 resources: `policy://schema-version`, `policy://catalog`, `policy://vocabularies`, todos `mimeType: application/json`
- `resources/templates/list` → vazio (esperado; nenhum URI parametrizado)
- `tools/list` → 3 tools: `get_clause`, `find_clauses_by_law_article`, `check_applicability`, todas com descriptions seguindo padrão use-when / don't-use-when / returns + errors

### A.2 — Resources read (LGPD)

- `policy://schema-version` → 4 campos conforme spec `docs/specs/policy-reader/canonical.md` §3.2
- `policy://catalog` → 1 item (POL-000 active, `article_sources_summary: ["LGPD Art. 5º"]`)
- `policy://vocabularies` → 4 keys top-level (`operation`, `lawful_basis`, `control`, `out_of_scope`), cada uma com `framework: "LGPD"` redundante; convenção ADR-0006 (tokens `name` em inglês, `description` em português) confirmada empiricamente

### A.3 — Tools de leitura (LGPD)

- `find_clauses_by_law_article(lei=LGPD, artigo=5)` → POL-000 retornada via `structuredContent.clauses[]`
- `find_clauses_by_law_article(lei=LGPD, artigo=11)` → `clauses: []` (matcher é strict top-level — refs aninhadas em `defines.entries` não disparam match; comportamento correto mas descrição ambígua — débito #7)
- `find_clauses_by_law_article(lei=GDPR, artigo=6)` → envelope `INVALID_LAW_IDENTIFIER`, `isRetryable: false`, `details.accepted_values` lido do header da Política

### A.4 — `check_applicability` (4 vereditos + 2 erros, LGPD)

| # | Input | Veredito/Erro | Campo discriminador |
|---|---|---|---|
| 1 | POL-001, context válido completo | `compliant` | `evidence` cita R1 + token `consent` |
| 2 | POL-001, sem `legal_basis` | `violation_candidate` | `contradicted_requirement: "R1"`, evidence "omite o campo" |
| 3 | POL-002, sem declaração de anonimização | `indeterminate` | `verification_scope` com 3 sub-campos (`dimension: upstream_state`, `prescribed_treatment: anonymization_required`, `verification_target`) |
| 4 | POL-001, `operation: storage` | `not_applicable` | `reason` cita ADR-0007 D3 (escopo MVP) |
| 5 | POL-003 (deprecated) | erro `CLAUSE_DEPRECATED` | **`isRetryable: true`** + `details.successors: ["POL-004"]` (único error retryable do servidor) |
| 6 | `get_clause(POL-003)` | sucesso | `tombstone` com `successors`, `effective_until`, `deprecation_reason` (assimetria semântica com cenário 5 confirmada) |

### A.5 — Framework swap (GDPR via `synthetic_gdpr`)

- Relaunch com `-e POLICY_READER_ROOT="<path-absoluto>"` apontando para a fixture
- `policy://schema-version` → `legal_framework: "GDPR"`
- `policy://catalog` → POL-000 stub GDPR (`article_sources_summary: ["GDPR Art. 4º"]`, zero menção a LGPD)
- `policy://vocabularies` → 4 keys com `framework: "GDPR"`. Token `collection` preservado cross-jurisdiction (decisão ADR-0006 confirmada empiricamente). Token `lawful_basis: consent_gdpr` (sufixo divergente intencional — base legal não é cross-framework por natureza jurídica)

## Débitos emergentes a consolidar em `chore/housekeeping-post-t04`

Quatro novos somam aos 4 pré-existentes em `docs/tasks.md` §Companion edits cross-doc (total: 8).

| # | Item | Severidade | Localização |
|---|---|---|---|
| 5 | Resource `name` defaultando para nome da função Python (`get_catalog`, `get_vocabularies`, `get_schema_version`) em vez de substantivo human-readable. Confunde distinção tool/resource para cliente LLM. | Cosmético | `server.py` decorators `@mcp.resource(...)` — passar `name=` explícito |
| 6 | Description de `check_applicability` referencia `structured_content` (snake_case); wire MCP é `structuredContent` (camelCase). | Cosmético, doc | Docstring de `check_applicability` em `server.py`/`tools.py` |
| 7 | Description de `find_clauses_by_law_article` ambígua sobre escopo de matching ("ANY element of its `statutory_reference`" — top-level apenas vs recursivo em `defines.entries`). Comportamento é top-level; description não esclarece. | Cosmético, doc | Docstring de `find_clauses_by_law_article` |
| 8 | `_format_law_reference` em `tools.py` aplica `º` incondicionalmente; jurídico-correto apenas para artigos ≤ 9. Visível em catalog renderings ("LGPD Art. 12º", "LGPD Art. 11º" em mensagens texto). Afeta LGPD e GDPR (helper cross-jurisdiction). | **Substantivo, defensivo (jurídico)** | `tools.py` formatter, ~5 linhas |

## Cleanup pós-gate

- `Remove-Item policy\clauses\POL-00[1-4].yaml` executado após Fase A.5
- `git status` → clean confirmado
- `policy/clauses/` retorna ao estado pré-A.4 (apenas POL-000.yaml)

## Insumo metodológico

Dos 8 débitos consolidados ao fim da sessão, 4 emergiram apenas durante o gate manual; 0 teriam sido capturados pelos 53 testes de pytest. Confirmação empírica da decisão ADR-0008 amended (separação gate task-level vs milestone-level): function tests e capability tests cobrem espaços diferentes e ambos são necessários.

## Próximas tasks dependentes deste gate

- **Bloqueio levantado:** abertura de Milestone B (pré-requisito de decomposição: decisão Semgrep-on-Windows)
- **Não bloqueia:** PR `chore/housekeeping-post-t04` consolidando os 8 débitos pode rodar em paralelo