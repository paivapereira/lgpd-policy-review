# Session handoff

**Última sessão fechada:** #19 (Chat review + Code execution) — 2026-05-16
**Próxima sessão:** #20 (Code) — implementação de T02a (`get_clause`)
**Branch ativa atual:** `main` (PR T01 mergeada)
**Branch nova a abrir para #20:** `feat/policy-reader-get-clause` 
(ramificar de `main` atualizada)

## Estado atual

Milestone A em progresso. T01 (Loader + handshake `policy://schema-version`) 
fechada com gate task-level ADR-0008 §3 cumprido: pytest 11/11 verde, ruff 
verde, mypy verde, Chat review independente aprovou diff. Implementação em 
`src/mcp_servers/policy_reader/` cobrindo loader.py, models.py, errors.py, 
server.py (modificado, com `_STATE` module-level e `_bootstrap()`), mais 
suíte de testes em `tests/mcp_servers/policy_reader/test_bootstrap.py`.

PR cleanup cross-doc (`docs/cleanup-stale-references`) também mergeada em 
main antes de T01. Fechou dois dos quatro débitos listados em tasks.md 
§Companion edits cross-doc (article_source → statutory_reference em quatro 
docs prescritivos; FastMCP 2.x → 3.x em dois docs). Os outros dois débitos 
(canonical/compact) seguem pinned para PR Chat dedicada de canonical sync, 
prevista para janela entre T03 e T04 ou pós-T04 pré-gate-milestone-level.

## Onde encontrar detalhes do que T01 cristalizou

- **Implementação:** `src/mcp_servers/policy_reader/` 
  (loader, models, errors, server).
- **Suíte de testes:** `tests/mcp_servers/policy_reader/test_bootstrap.py` 
  (11 testes cobrindo AS-1..AS-8) + `conftest.py` (fixture 
  `valid_policy_root` clona policy/ real para tmp_path).
- **Anchor de wire-shape FastMCP:** 
  `test_documents_fastmcp_read_resource_shape` em test_bootstrap.py — 
  asserts mínimos sobre tipo de retorno; falha primeiro se release 
  futura de FastMCP mudar o wrap.
- **Deps adicionadas:** `packaging>=24` (deps), `pytest-asyncio>=0.24` 
  + `types-PyYAML>=6.0` (dev deps), `asyncio_mode = "auto"` em 
  `[tool.pytest.ini_options]`. Em `pyproject.toml`.
- **Constante module-level:** `COMPATIBLE_SCHEMA_RANGE = 
  SpecifierSet(">=0.1.0,<0.2.0")` em loader.py. Constante do componente, 
  não da Política — formato packaging-compatível, parseável nativamente.
- **Processo de cristalização da sessão #19:** `docs/learning-log.md` 
  (entry 2026-05-16).

## Pre-flight pins para a sessão #20 (Code, T02a)

Cinco aprendizados de T01 que migram como pre-flight para T02a:

1. **`statutory_reference` é o nome do campo, não `article_source`**, 
   conforme aplicado em T01 e cleanup. Models de T02a referenciam 
   `statutory_reference` direto. `compact.md` ainda diz `article_source` 
   (Companion edit #1 pinned) — Code aplica artefato real conforme 
   tasks.md linha 7, anota no relatório.

2. **`_STATE` module-level já está bootstrapped em server.py após T01.** 
   T02a não precisa redesenhar bootstrap; reutiliza `_STATE.clauses[clause_id]` 
   para a implementação de `get_clause`.

3. **`compatible_schema_range` é constante do componente, não da Política.** 
   T02a não interage com isso, mas se precisar referenciar versionamento, 
   o padrão já está estabelecido.

4. **Wire-shape MCP via `.to_mcp_result(uri)`, não retorno direto do 
   handler interno.** T02a vai retornar tool output (`CallToolResult` 
   per canonical §2), não resource (`ReadResourceResult`). Wire-shape 
   esperada está em compact §5/§6 — Code valida empiricamente o shape 
   de retorno de tool em FastMCP 3.2.4 na primeira hora de T02a (mesmo 
   padrão do anchor test de T01).

5. **PR contra main, branch `feat/policy-reader-get-clause` ramificada 
   de main atualizada.** Não encadear PRs.

## Pendências cross-sessão (organizado por horizonte de resolução)

**Resolver na #20 (Code, T02a):**

- Validação empírica do shape de retorno de tool em FastMCP 3.2.4 
  (análogo ao anchor de T01 para resource).

**Resolver em sessão Chat paralela (não bloqueia T02a):**

- PR de canonical sync (4 débitos listados em `docs/tasks.md` §Companion 
  edits + 1 descoberto pelo Code na sessão #19: `tasks.md` l.229 cita 
  canonical §8.7 que aparentemente não existe na numeração atual; 
  verificar se é referência stale ou seção renomeada).
- Decisão Semgrep-on-Windows (Docker, pip native, remote worker, CI-only) 
  — afeta forma de T05 em Milestone B, irrelevante para Milestone A.

**Resolver em #21+ ou ADR futuro:**

- Decomposição formal de Milestone B (semgrep-runner) em sessão Chat 
  dedicada, após gate milestone-level de A completar. Decisão 
  Semgrep-on-Windows precede.
- Decomposição formal de Milestone C (pipeline multi-agente) e Milestone 
  D (CI/CD + validação empírica) em sessões Chat dedicadas, 
  sequencialmente.
- Semântica de `last_revision` em `policy/policy.yaml` — formal vs 
  informativo, atualização manual vs automática.
- `effective_date` e `last_revision` no policy.yaml estão sem quotes 
  (YAML interpreta como `date` nativo); SCHEMA §3.1 prescreve "string 
  ISO 8601". Pequeno débito, pode entrar na PR Chat de canonical sync.
- Validação cruzada per-cliente (vocabulary × Semgrep metadata) quando 
  materializar ADR de per-client rule set.
- ADR retroativo formalizando convenção "português para docs técnicos 
  não-ADR".
- Promoção do draft `_drafts/spec-authoring-principles.md` para `docs/`.

## Defaults arquiteturais consolidados (pós-T01)

Estado **realizado** (não plano em progresso). Referência canônica de 
cada item em ADR/spec/código.

**Da Fase 1 (ADR-0005 — multi-client architecture):**

- Camada 1 (Política) é per-cliente; substituível por cliente sem 
  alteração de código.
- `legal_framework` é campo top-level único do header, imutável durante 
  sessão do server.
- POL-000 é vocabulário universal (semântico, não estatutário); vive em 
  `policy/clauses/`, estrutura governada por `policy/SCHEMA.md` §5.
- Quatro vocabulários jurisdicionais (`operation`, `lawful_basis`, 
  `control`, `out_of_scope`) vivem em 
  `policy/vocabularies/<framework>/*.yaml`.
- `policy-reader` expõe três resources (`policy://catalog`, 
  `policy://schema-version`, `policy://vocabularies`) e três tools 
  (`get_clause`, `find_clauses_by_law_article`, `check_applicability`).
- `policy://vocabularies` é compartilhado Matcher+Classifier (read-only 
  resource).
- `check_applicability` retorna trinca de provenance 
  `(policy_schema_version, policy_version, legal_framework)` em todo 
  sucesso.
- Sucessão de cláusulas é intra-Política, via `successors` no bloco 
  `tombstone`.
- Mecanismo interno de reasoning de `check_applicability` é deferido 
  (regra/LLM/híbrido livre para Code).
- `semgrep-runner` rule set é bundled no projeto no MVP.

**Da Fase 1.5 (ADR-0004 + ADR-0007 + ADR-0008 amended):**

- Stack management via `uv` + lockfile `uv.lock` versionado (ADR-0004).
- FastMCP 3.x como runtime MCP, Pydantic 2.13.x para validação 
  (ADR-0004). **Verificado empiricamente em T01:** FastMCP 3.2.4.
- Escopo MVP v0.1.0 de `check_applicability` é exclusivamente 
  `operation: collection`. Outras 21 operações do vocabulário retornam 
  `verdict: not_applicable` com `reason` MVP-scope, sem invocar 
  matching (ADR-0007).
- Granularidade de Fase 2: 8-12 tasks de 1-3h agrupadas em milestones; 
  cada milestone entrega capability declarada em REQUIREMENTS.md, cada 
  task entrega função coerente (ADR-0008 amended §1).
- RFs/RNFs binding é milestone-level, não task-level (ADR-0008 amended §2).
- Gate de verificação em dois scopes: task-level (function tests + Chat 
  review independente) e milestone-level (manual exercise contra RFs) 
  (ADR-0008 amended §3).
- Bibliografia metodológica de referência: Rajasekaran (2026) "Harness 
  design for long-running application development", Anthropic 
  Engineering; Anthropic (2025) "Building Effective Agents" 
  (ADR-0008 §4).

**De T01 (sessão #19):**

- `_STATE: LoadedPolicy | None` module-level em `server.py`; populado 
  por `_bootstrap(root: Path | None = None)`; resetável em teste via 
  `_reset_state_for_tests()`. Padrão a seguir em T02a/T02b/T03/T04.
- `COMPATIBLE_SCHEMA_RANGE = SpecifierSet(">=0.1.0,<0.2.0")` 
  module-level em `loader.py`. Constante do componente. Formato 
  packaging-compatível.
- `PolicyLoadError` exceção única para falhas de carregamento (categoria 
  system implícita, abortando antes de `mcp.run()`).
- Wire-shape MCP canônico via `.to_mcp_result(uri)`, não retorno direto 
  do handler. Anchor test 
  `test_documents_fastmcp_read_resource_shape` em test_bootstrap.py.

## Plano de ação Fase 2 — Code (sessões #20+)

**Input para Code.** `docs/tasks.md` v1.1 segue como source-of-truth de 
Fase 2. Code consome task a task em ordem topológica: T01 ✓ → T02a → 
T02b → T03 → T04. Gate task-level ADR-0008 §3 entre cada uma.

**Prompt de abertura da sessão #20 (Code, T02a).**

A redigir em sessão Chat de preparação curta (análoga à preparação de 
#19 que ocupou parte desta sessão), revisitando o template estrutural 
v4 do prompt de T01:

- Entrypoint DESIGN.md.
- Pré-leitura universal: architecture-overview §4.1–§4.4 e §5.7; 
  SCHEMA §2.1 e §3.
- Spec normativa: compact.md de policy-reader (canonical apenas em 
  ambiguidade).
- Sprint contract: tasks.md §T02a.
- Específico aos AS de T02a (definir na sessão de preparação após 
  releitura de §T02a).
- Estado real: arquivos da implementação T01 + 
  `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/` 
  (pack POL-001..004 já está em main desde Fase 1.5).
- Débito cross-doc residual: `article_source` em compact.md (mesma 
  forma de T01).
- Pre-flight pins: cinco itens listados na seção anterior deste handoff.
- Estrutura duas fases com gate de OK entre Plano e Implementação.
- Guard-rails: escopo estrito T02a, ambiguidade já conhecida vs nova, 
  AS não-executável, edits restritos a 
  `src/mcp_servers/policy_reader/` + `tests/mcp_servers/policy_reader/` 
  + pyproject.toml para deps decorrentes de DDs aprovadas.

**Custo estimado.** T02a estimada em 1-3h conforme tasks.md. Com Chat 
review independente: sessão Chat de preparação (~30min) + sessão Code 
(2-3h) + sessão Chat review (~30min) = ~3-4h total por task.

## Hashes da sessão #19 (audit trail interno)

PRs mergeadas em main durante a sessão:

- `<hash>` — chore(docs): rename article_source to statutory_reference 
  per SCHEMA.md
- `<hash>` — chore(docs): update FastMCP version references to 3.x per 
  ADR-0004
- `<hash>` — feat(policy-reader): T01 — loader + 
  policy://schema-version handshake

(Hashes preenchidos pelo autor após `git log` em main.)