# Session handoff

**Última sessão fechada:** #20 (T02a + canonical-sync-A + canonical-sync-A.2)
— 2026-05-17
**Próxima sessão:** #21 (Chat) — prep de canonical-sync-B do policy-reader
(decisão de design antes de T02b)
**Branch ativa atual:** `main` (três PRs da #20 mergeadas)
**Branch nova a abrir para #21:** não-aplicável (sessão Chat de prep)
**Branch nova a abrir pós-#21:** `feat/canonical-sync-B` (Code aplicará
edições decididas em #21)

## Estado atual

Milestone A em progresso. T02a (`get_clause` + migração `server.py` inline
→ `tools.py`) fechada com gate task-level ADR-0008 §3 cumprido: pytest
20/20 verde, ruff verde, mypy verde, Chat review independente aprovou
diff. Três PRs mergeadas em main durante #20:

- **PR T02a** (`feat/policy-reader-get-clause`). Implementação de
  `get_clause` em `tools.py` (novo módulo, função pure), wrapper
  `@mcp.tool` em `server.py` delegando, `ErrorEnvelope` em `models.py`,
  9 testes em `test_get_clause.py` cobrindo anchor wire-shape + AS-1.a
  (POL-000 definitional) + AS-1.b (POL-001 substantive) + AS-2 (POL-003
  deprecated) + AS-3 parametrizado (4 IDs inválidos) + AS-4 (not found).
- **PR canonical-sync-A** (`feat/canonical-sync-A`, três commits
  separados). Fechou três débitos cross-doc do policy-reader:
  `article_source` → `statutory_reference` em canonical+compact (16
  ocorrências); `FastMCP 2.x` → `FastMCP 3.x` em canonical (2
  ocorrências, com discriminação gramatical §1 vs §8.7); quotes ISO 8601
  em `policy.yaml` `effective_date`/`last_revision` (2 ocorrências).
- **PR canonical-sync-A.2** (`feat/canonical-sync-A.2-semgrep-runner`,
  um commit). Fechou débito análogo descoberto durante execução de A:
  `FastMCP 2.x` → `FastMCP 3.x` em
  `docs/specs/semgrep-runner/canonical.md` (2 ocorrências).

Débitos cross-doc remanescentes: dois (policy-reader) + possível um
(semgrep-runner a confirmar). Vão para canonical-sync-B em #21+ (decisão
de design, não mecânica).

## Onde encontrar detalhes do que #20 cristalizou

- **T02a implementação:** `src/mcp_servers/policy_reader/tools.py` (novo,
  `get_clause` pure function + helpers privados `_invalid_clause_id_format`,
  `_clause_not_found`, `_envelope_tool_result`, `_success_tool_result`,
  `_format_first_stat_ref`, `_render_clause_text`), `models.py`
  (modificado com `ErrorEnvelope` Pydantic), `server.py` (thin wrapper
  `@mcp.tool def get_clause(clause_id) -> ToolResult` chamando
  `tools.get_clause(clause_id, _STATE)`).
- **T02a testes:** `tests/mcp_servers/policy_reader/test_get_clause.py`
  (9 testes) + `conftest.py` (fixture `policy_root_with_pack_clauses`
  estendendo `valid_policy_root` com POL-001 e POL-003 do pack).
- **Anchor de wire-shape FastMCP para tool calls:**
  `test_documents_fastmcp_tool_call_shape` em `test_get_clause.py` —
  asserts mínimos sobre estrutura `CallToolResult` em sucesso e em
  domain error; falha primeiro se release futura de FastMCP mudar wrap.
  Família completa: anchor de resource (T01, `test_bootstrap.py`) + anchor
  de tool (T02a, `test_get_clause.py`).
- **Convenção Option B (envelope em `structuredContent`, wire `isError`
  reservado para protocol-level):** `ErrorEnvelope.__doc__` em
  `models.py` + asserções concretas no anchor test + relatório de gate
  de T02a. Pendente: documentação formal em canonical §5.1/§5.2 +
  amendment ADR-0002 (canonical-sync-B).
- **Processo de cristalização da sessão #20:** `docs/learning-log.md`
  (entry 2026-05-17).

## Pre-flight pins para a sessão #21 (Chat — prep canonical-sync-B)

Seis itens load-bearing para deliberação de design.

1. **`applicability_scope` → `applies_to`: cobertura polimórfica é
   obrigatória.** T02a cristalizou que `get_clause` retorna polimórfico
   (`DefinitionalClause` carrega `defines`/`out_of_scope`;
   `SubstantiveClause` carrega `applies_to`/`control`/`requirements`/
   `exceptions`). Canonical §4.1 atual descreve apenas
   `applicability_scope` (flat list) — não cobre o caso definitional,
   não cobre os sub-campos `personal_data_categories`/`operation`.
   Redação nova precisa ser polimórfica.

2. **Granularidade da exposição de `applies_to`.** Decisão a tomar em
   #21: expor sub-campos `personal_data_categories` e `operation`
   literalmente no canonical (acoplamento com SCHEMA §6 — mudar SCHEMA
   exige sync), ou abstrair como "scope filters" (flexibilidade mas
   perde precisão para o Matcher). Inclinação prévia: literal — canonical
   é contrato da tool, não da arquitetura geral.

3. **Paralelismo `applies_to` ↔ `check_applicability.structured_context`.**
   O `inputSchema` de `check_applicability` consome `data_categories` +
   `operation`. Há paralelismo direto com `applies_to.personal_data_
   categories` + `applies_to.operation` da cláusula. Vale o canonical
   explicitar esse paralelismo em §4.1 (`get_clause`) e §4.3
   (`check_applicability`).

4. **`isError`-semantics: como descrever o constraint FastMCP 3.2.4.**
   Documentar convenção Option B sem mencionar o constraint (canonical
   fica "limpo" mas perde rastreabilidade), ou explicitar ("convenção
   adotada porque caminho ideal não é expressível em framework atual;
   revisar se framework evoluir")? Inclinação prévia: segundo caminho —
   canonical vira documento honest sobre por que existe a convenção que
   existe.

5. **Discriminador formal: declarar onde?** "Sucesso vs erro" passa a
   ser "presença do campo `errorCode` no `structuredContent`". §5.1
   (com estrutura do envelope), §2 (wire format geral), ou ambos com
   cross-reference? §2 é mais correto arquiteturalmente (convenção do
   componente inteiro); §5.1 é onde o leitor procura primeiro. Cross-
   reference em ambos provavelmente.

6. **Amendment ADR-0002 vs ADR novo.** ADR-0002 governa MCP conventions
   (em particular Decision 1 sobre hybrid placement `structuredContent`
   + `content`). Amendment preserva contexto histórico (porquê original
   + porquê da adaptação no mesmo doc, padrão estabelecido em
   ADR-0008 amended 2026-05-16). ADR novo é mais limpo se a divergência
   for grande. Para Option B, amendment parece certo.

## Pendências cross-sessão (organizado por horizonte de resolução)

**Resolver na #21 (Chat — prep canonical-sync-B):**

- Seis itens de design listados nos pre-flight pins acima.
- Rascunho de redação de canonical §4.1 (polimorfismo +
  `applicability_scope` → `applies_to`), §5.1, §5.2 (isError-semantics
  Option B), e amendment ADR-0002.

**Resolver em sessão Code #22 (canonical-sync-B aplicação):**

- Aplicar redações decididas em #21 em
  `docs/specs/policy-reader/canonical.md`,
  `docs/specs/policy-reader/compact.md`, `docs/adr/0002-mcp-conventions-
  and-deferments.md`. Edits sob decisão prévia, Code não decide nada
  novo durante implementação.

**Resolver em #23+ (T02b):**

- `find_clauses_by_law_article`. Próxima task topológica de Milestone A.
  Pré-leitura consome canonical já limpo pós-canonical-sync-B.

**Resolver em janela futura sem urgência:**

- **DX:** linters (ruff, mypy) como dev deps oficiais em `pyproject.toml`.
  Workaround atual via `uvx ruff` e `uv run --with mypy mypy` funciona,
  mas dev deps reduzem fricção. Sessão Code curta (~15min).
- **Decisão Semgrep-on-Windows** (Docker, pip native, remote worker,
  CI-only) — afeta forma de Milestone B; antecede decomposição formal.
- **Limpeza dos bullets fechados em `tasks.md` §Companion edits
  cross-doc** após canonical-sync-B completar (article_source, FastMCP
  2.x em policy-reader e semgrep-runner, applicability_scope,
  isError-semantics). Sessão Chat de housekeeping.

**Resolver pós-T03 ou em janela específica:**

- **Possível canonical-sync-B do semgrep-runner.** Deliberar na prep de
  Milestone B. Code de A.2 leu §1 e §8.6 do canonical do semgrep-runner
  e não encontrou análogos aos achados de policy-reader, mas varredura
  completa só na prep de Milestone B.
- **Dois itens deferidos T03** (já listados em `tasks.md` §Companion
  edits cross-doc): `operation`/`legal_basis` vs `operation_type`/
  `declared_legal_basis` (canonical §4.3 vs REQUIREMENTS RF-003);
  `evidence` vs `reason` em `not_applicable` (canonical §4.3 vs ADR-0007
  Decision 3). Resolver pós-T03 quando spec for empiricamente validado.
- **Validação cruzada per-cliente** (vocabulary × Semgrep metadata)
  quando materializar ADR de per-client rule set.
- **Promoção do draft `_drafts/spec-authoring-principles.md`** para
  `docs/`.
- **ADR retroativo formalizando convenção "português para docs técnicos
  não-ADR".**
- **Semântica de `last_revision` em `policy.yaml`** — formal vs
  informativo, atualização manual vs automática.
- **Decomposição formal de Milestone B + Milestone C + Milestone D em
  sessões Chat dedicadas, sequencialmente.** Após gate milestone-level
  de A.

## Defaults arquiteturais consolidados (pós-T02a)

Estado realizado, não plano em progresso.

**Sobre tools MCP do policy-reader:**

- Função pública pura por tool em `src/mcp_servers/policy_reader/tools.py`,
  recebendo `state: LoadedPolicy` explicitamente (testabilidade).
- Thin wrapper `@mcp.tool` em `server.py` importando e delegando, com
  guard `assert _STATE is not None` antes da delegação (consistência com
  `server.py:90` de T01).
- Output em sucesso preserva forma como armazenada:
  `clause.model_dump(mode="json", exclude_none=True)` direto sobre
  instância carregada; polimorfismo `DefinitionalClause | SubstantiveClause`
  visível no payload.
- `ErrorEnvelope` Pydantic estruturado em `structuredContent` +
  `content[0].text == message`; wire `isError` reservado para
  protocol-level (convenção Option B). Discriminador implícito por
  presença de campo `errorCode`.
- Helpers privados por errorCode em `tools.py` durante T02a; promoção
  para módulo compartilhado quando segundo consumidor (T02b/T03)
  demonstrar reuso real.

**Sobre fixtures de teste:**

- Pack POL-001..004 em
  `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/`
  é referência autorizada para consumo direto, não apenas inspiração
  estrutural.
- Fixture root estendida via `tmp_path`: `valid_policy_root` (real
  `policy/` deep-copy) + cláusulas do pack copiadas seletivamente para
  `clauses/`. POL-000 vem do real, sem cópia.
- Fixture `reset_server_state` em `conftest.py` é o teardown padrão entre
  testes que invocam `_bootstrap`. Chama
  `server._reset_state_for_tests()` internamente.

**Sobre wire-shape FastMCP 3.2.4:**

- Tools retornam dict; FastMCP wrappa em `CallToolResult` com
  `structuredContent` populado e wire `isError=False`.
- `raise ToolError` gera wire `isError=True` + `content[0].text=message`,
  mas `structuredContent=None` (perda do envelope estruturado).
- Convenção do projeto: tools nunca raise `ToolError` para erros de
  domínio (validation/business per canonical §5.2); sempre retornam dict
  com envelope estruturado (Option B). `raise ToolError` reservado para
  erros sistêmicos legítimos onde wire `isError` carrega informação útil
  e perder envelope estruturado é aceitável (caso ainda hipotético em
  policy-reader; possível em Milestone B se semgrep-runner tiver system
  errors runtime transientes).
- Anchor tests `test_documents_fastmcp_read_resource_shape` (T01) +
  `test_documents_fastmcp_tool_call_shape` (T02a) permanecem como sinal
  de regressão se release futura de FastMCP mudar wrap.

**Sobre tooling — uv runtime patterns:**

- `uvx <tool>`: download isolado para tools stand-alone (linters como
  ruff). Funciona quando tool não precisa do venv do projeto.
- `uv run --with <tool> <tool> ...`: injeta tool no venv do projeto na
  invocação. Necessário para tools que precisam enxergar packages
  instalados (mypy strict precisa enxergar pydantic, fastmcp etc).
- `uv run <tool>`: funciona apenas se tool está em dev-deps via
  `uv sync`. Atualmente NÃO funciona para ruff/mypy (não estão em
  dev-deps oficiais — débito DX residual).

**Sobre PRs mecânicas (canonical-sync pattern):**

- Escopo único por PR; varias PRs pequenas vs uma PR grande mista.
- Verificação empírica primeiro (`grep` contagens) antes de aplicar
  substituição; contagens validam que estado real bate com expectativa.
- Discriminação gramatical onde citações compostas exigem (e.g.
  "FastMCP 2.x conforme ADR-0001" vs "Stack conforme ADR-0001 (FastMCP
  2.x, ...)" exigem tratamento distinto).
- Explicit non-finding documentado quando verificação produz zero edit
  legítimo (e.g. compact.md do semgrep-runner sem débito FastMCP).
- Code não cria branch, não commita, não abre PR. Gate task-level Chat
  review independente é obrigatório mesmo para PRs mecânicas.
