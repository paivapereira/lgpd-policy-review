# Session handoff

**Última sessão fechada:** #18 (Chat) — 2026-05-16
**Próxima sessão:** #19 (Code) — implementação de T01 de Milestone A
**Branch ativa atual:** `docs/tasks-and-fixtures` (PR em main, em mergeação)
**Branch nova a abrir para #19:** `feat/policy-reader-implementation` (ramificar de main pós-merge)

## Estado atual

Fase 1.5 fechada. `docs/REQUIREMENTS.md` (9 RFs + 2 RNFs), `docs/adr/0004-uv-fastmcp-3x.md`, `docs/adr/0007-mvp-collection-only-scope.md`, `docs/adr/0008-task-decomposition-and-verification.md` (amended 2026-05-16) e `docs/tasks.md` v1.1 estão em main ou na PR em mergeação. Pacote POL-001..POL-004 está em `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/` como fixture isolada de teste — sem rationale, sem bump de `policy_version`, sem estabilização de SCHEMA §6. Implementação real (Fase 2) começa em Milestone A: cinco tasks (T01-T04 + T02b) para o `policy-reader` standalone, validáveis via MCP Inspector cross-tool, ancoradas em `docs/specs/policy-reader/canonical.md`.

Quatro débitos cross-doc no canonical.md estão anotados em `docs/tasks.md` §Companion edits para PR separada em sessão Chat dedicada: nome do campo `statutory_reference`, naming dos campos do `structured_context` no inputSchema de `check_applicability`, payload `reason` (vs `evidence`) em `not_applicable` conforme ADR-0007 Decision 3, e versão de FastMCP (canonical 2.x → real 3.x conforme ADR-0004). Estes débitos não bloqueiam Code de Milestone A — implementação adota o lado dos artefatos reais (já pinned em `tasks.md`), canonical alinha depois.

## Onde encontrar detalhes do que a Fase 1.5 cristalizou

- **Plano executável de Fase 2:** `docs/tasks.md` (Milestone A com cinco tasks; B/C/D referenciados, autoria deferida pós-gate milestone-level de A).
- **Contrato de aceitação global:** `docs/REQUIREMENTS.md` (RFs/RNFs com critério Dado/Quando/Então).
- **Governance de task decomposition e verificação:** `docs/adr/0008-task-decomposition-and-verification.md` (amended) — granularidade 8-12 tasks de 1-3h, gate task-level (function tests + Chat review independente) + gate milestone-level (manual exercise contra RFs).
- **Escopo MVP operacional:** `docs/adr/0007-mvp-collection-only-scope.md` (apenas `operation: collection` invoca matching no MVP v0.1.0; outras 21 operações do vocabulário retornam `not_applicable` com `reason` MVP-scope).
- **Stack management:** `docs/adr/0004-uv-fastmcp-3x.md` (uv como gerenciador, FastMCP 3.x).
- **Pack teste de check_applicability:** `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/README.md` (AS coverage por arquivo, pattern de fixture root assembly, ressalvas).
- **Processo de cristalização da sessão #18:** `docs/learning-log.md` (entry 2026-05-16).

## Pre-flight pins para a sessão #19 (Code, T01)

Cinco decisões pre-flight identificadas pela terceira passada Code de auditoria de `tasks.md` v1.1. Não vão para `tasks.md` (que é estável); vão para a descrição da PR de Milestone A ou para o prompt de abertura da sessão Code.

1. **Payload de `get_clause` (T02a) usa `statutory_reference`**, não `article_source`. Nome do campo segue o artefato real (`policy/SCHEMA.md` §5.1, `policy/clauses/POL-000.yaml`); canonical.md alinha em PR separada (Companion edit #1).
2. **Mecanismo de reasoning de `check_applicability` (T03) é regra programática determinística para Milestone A**. ADR-0005 Decision 7 dá liberdade entre regra/LLM/híbrido; tensão com pytest é estrutural — single LLM call vira teste flaky, AS-1..AS-5 de T03 assumem determinismo `(clause_id, structured_context) → veredito` idempotente. LLM-call fica para evolução pós-MVP quando regime de testes for ajustado.
3. **Validação de vocabulário runtime via `model_validator` ou validator function**, não `Literal[...]` dinâmico. `INVALID_OPERATION` e `INVALID_DATA_CATEGORY` (T03 AS-8) exigem validar `structured_context` contra vocabulários carregados em startup. Pydantic 2 `Literal` é estático em definition time — caminho correto: `inputSchema` declara `operation: str`, função body consulta estado carregado.
4. **`ReadResourceResult` shape validado empiricamente com MCP Inspector** na primeira hora de T01. Skeleton retorna `dict[str, Any]`; FastMCP 3.x auto-wrappa em `ReadResourceResult` com `contents: [TextResourceContents]`, mas o tipo concreto pós-wrap e o `mimeType` default precisam confirmação contra T01 AS-7 e T04 AS-4.
5. **`compatible_schema_range` em formato packaging-compatible**. Recomendação: trocar `policy/policy.yaml` para `compatible_schema_range: ">=0.1.0,<0.2.0"` (parseado nativamente por `packaging.specifiers.SpecifierSet`) em vez de manter `"0.1.x"` (que exige parser regex custom). Edit pequeno em `policy.yaml`, na mesma branch de implementação de T01.

## Pendências cross-sessão (organizado por horizonte de resolução)

**Resolver antes da #19 começar:**

- Merge da PR de `tasks.md` + pack POL-001..004 + handoff sync. Sem isso, branch de Code parte de main stale.

**Resolver em sessão Chat paralela (não bloqueia Milestone A):**

- PR de canonical.md sync (4 débitos listados em `docs/tasks.md` §Companion edits).
- Decisão Semgrep-on-Windows (Docker, pip native, remote worker, CI-only) — afeta forma de T05 em Milestone B, irrelevante para Milestone A.

**Resolver na #19 (Code, T01):**

- Edit em `policy/policy.yaml` para `compatible_schema_range: ">=0.1.0,<0.2.0"` (pre-flight pin #5).
- Validação empírica do `ReadResourceResult` shape (pre-flight pin #4).

**Resolver em #20+ ou ADR futuro:**

- Decomposição formal de Milestone B (semgrep-runner) em sessão Chat dedicada, após gate milestone-level de A completar. Decisão Semgrep-on-Windows precede.
- Decomposição formal de Milestone C (pipeline multi-agente) e Milestone D (CI/CD + validação empírica) em sessões Chat dedicadas, sequencialmente.
- Semântica de `last_revision` em `policy/policy.yaml` — formal vs informativo, atualização manual vs automática.
- Validação cruzada per-cliente (vocabulary × Semgrep metadata) quando materializar ADR de per-client rule set.
- ADR retroativo formalizando convenção "português para docs técnicos não-ADR".
- Promoção do draft `_drafts/spec-authoring-principles.md` para `docs/`.

## Defaults arquiteturais consolidados (pós-Fase 1.5)

Estado **realizado** (não plano em progresso). Referência canônica de cada item em ADR citado.

**Da Fase 1 (ADR-0005 — multi-client architecture):**

- Camada 1 (Política) é per-cliente; substituível por cliente sem alteração de código.
- `legal_framework` é campo top-level único do header, imutável durante sessão do server.
- POL-000 é vocabulário universal (semântico, não estatutário); vive em `policy/clauses/`, estrutura governada por `policy/SCHEMA.md` §5.
- Quatro vocabulários jurisdicionais (`operation`, `lawful_basis`, `control`, `out_of_scope`) vivem em `policy/vocabularies/<framework>/*.yaml`.
- `policy-reader` expõe três resources (`policy://catalog`, `policy://schema-version`, `policy://vocabularies`) e três tools (`get_clause`, `find_clauses_by_law_article`, `check_applicability`).
- `policy://vocabularies` é compartilhado Matcher+Classifier (read-only resource).
- `check_applicability` retorna trinca de provenance `(policy_schema_version, policy_version, legal_framework)` em todo sucesso.
- Sucessão de cláusulas é intra-Política, via `successors` no bloco `tombstone`.
- Mecanismo interno de reasoning de `check_applicability` é deferido (regra/LLM/híbrido livre para Code).
- `semgrep-runner` rule set é bundled no projeto no MVP.

**Da Fase 1.5 (ADR-0004 + ADR-0007 + ADR-0008 amended):**

- Stack management via `uv` + lockfile `uv.lock` versionado (ADR-0004).
- FastMCP 3.x como runtime MCP, Pydantic 2.13.x para validação (ADR-0004).
- Escopo MVP v0.1.0 de `check_applicability` é exclusivamente `operation: collection`. Outras 21 operações do vocabulário retornam `verdict: not_applicable` com `reason` MVP-scope, sem invocar matching (ADR-0007).
- Granularidade de Fase 2: 8-12 tasks de 1-3h agrupadas em milestones; cada milestone entrega capability declarada em REQUIREMENTS.md, cada task entrega função coerente (ADR-0008 amended §1).
- RFs/RNFs binding é milestone-level, não task-level (ADR-0008 amended §2).
- Gate de verificação em dois scopes: task-level (function tests + Chat review independente) e milestone-level (manual exercise contra RFs) (ADR-0008 amended §3).
- Bibliografia metodológica de referência: Rajasekaran (2026) "Harness design for long-running application development", Anthropic Engineering; Anthropic (2025) "Building Effective Agents" (ADR-0008 §4).

## Plano de ação Fase 2 — Code (sessões #19+)

**Input para Code.** `docs/tasks.md` v1.1 é o source-of-truth da Fase 2. Code consome task a task em ordem topológica (T01 → T02a → T02b → T03 → T04 para Milestone A; ordem subsequente conforme autoria dos próximos milestones), validando gate task-level conforme ADR-0008 §3 antes de marcar como done.

**Prompt de abertura da sessão #19 (Code, T01):**

> Implementar T01 de docs/tasks.md (loader + handshake policy://schema-version) para o policy-reader. Validar AS-1 a AS-8 em pytest sob uv run pytest antes de fechar. Ler antes: docs/tasks.md T01 inteira (Função, Dependências, Files, AS, Gate), docs/specs/policy-reader/canonical.md §3.2, policy/SCHEMA.md §3.1 + §4.5 + §6. Pre-flight pins do session-handoff aplicam — em particular: ReadResourceResult validado com Inspector (pin 4), compatible_schema_range trocado para ">=0.1.0,<0.2.0" no policy.yaml (pin 5), modelos Pydantic com model_validator runtime (pin 3). Após implementação, abrir sessão Chat separada para gate review do diff. Pausar e perguntar se algo na task estiver ambíguo.

**Estado de partida.** PR da Fase 1.5 (tasks.md + pack + handoff) mergeada em main. Code começa nova branch `feat/policy-reader-implementation` ramificando de main.

**Custo estimado.** Com cinco tasks de 1-3h cada, Milestone A é 8-12h de implementação cobrindo as cinco com gate task-level (pytest + Chat review por task). Gate milestone-level (manual exercise contra RFs 004-parcial, 005, 007-parcial, 008-parcial, 009) é sessão Chat dedicada de ~1-2h adicional, executada após T01-T04 fecharem. Total Milestone A: 10-14h, distribuídas em 4-6 sessões de Code de 2-3h cada.

## Hashes da Fase 1.5 (audit trail interno)

Branch `docs/tasks-and-fixtures` em PR. Hashes sobrevivem a squash-merge — após merge do PR, hashes individuais somem do main, mas ficam registrados aqui:

- `<TBD>` — docs(tasks): add tasks.md v1.1 for Milestone A implementation
- `<TBD>` — test(policy-reader): add POL-001..004 fixture pack for check_applicability
- `<TBD>` — docs: sync session-handoff.md to Milestone A/B split + Fase 1.5 close
- `<TBD>` — docs(log): close session #18 — tasks.md authoring + POL fixture pack

(Hashes preenchidos após `git log` da branch antes do merge.)
