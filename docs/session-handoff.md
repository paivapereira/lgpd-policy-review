# Session handoff

**Última sessão fechada:** #22 (Chat) — prep prompt T02b + cleanup
`fix/render-romano-in-T02a` (sessão Code #22.5) + execução T02b
(`find_clauses_by_law_article`, sessão Code #23) + Chat review
independente — 2026-05-17
**Próxima sessão:** #24 (Chat fresh) — prep do prompt T03
(`check_applicability`)
**Branch ativa atual:** `main` (PRs `<TBD>` cleanup + `<TBD>` T02b
mergeadas via squash; hashes a registrar pós-merge)
**Branch nova a abrir para #24:** não-aplicável (sessão Chat de prep)
**Branch nova a abrir pós-#24:** `feat/policy-reader-check-applicability`
(Code aplicará T03 ramificando de main)

## Estado atual

Milestone A em progresso. T02b fechada em #23 sob ciclo Chat
persistente #22. Spec policy-reader coerente e exercitada em três das
quatro tools (`get_clause`, `find_clauses_by_law_article` operacionais;
`check_applicability` permanece skeleton stub até T03; resources
`policy://schema-version` operacional; `policy://catalog` skeleton até
T04; `policy://vocabularies` aterrissa em T04).

Status global de Milestone A:

- **T01** (Loader + handshake schema-version) — **fechada** (#19).
- **T02a** (`get_clause` + migração `tools.py`) — **fechada** (#20).
- **canonical-sync-A + A.2** (drift textual policy-reader +
  semgrep-runner) — **fechadas** (#20).
- **canonical-sync-B** (drift estrutural + Option B + polimorfismo +
  amendment ADR-0002) — **fechada** (#21).
- **fix/render-romano-in-T02a** (helper compartilhado
  `_format_law_reference` + romano em rendering de inciso) —
  **fechada** (#22.5).
- **T02b** (`find_clauses_by_law_article`) — **fechada** (#23, sob
  ciclo Chat persistente #22).
- **T03** (`check_applicability`) — próxima task topológica, prep em
  #24, execução em #25+.
- **T04** (`policy://vocabularies` + framework swap) — após T03.
- **Gate milestone-level Milestone A** — sessão Chat dedicada após
  T01-T04 fecharem, ~1-2h, manual exercise via MCP Inspector
  exercitando cada RF de docs/REQUIREMENTS.md (RFs 004-parcial, 005,
  007-parcial, 008-parcial, 009).

## Onde encontrar detalhes do que #22 cristalizou

- **Prep do prompt T02b — versionamento iterativo:**
  `prompt-t02b-v1.md` (esqueleto T02a + 6 correções minhas vs draft
  inicial do Code) → `prompt-t02b-v2.md` (DD-5 adicionada após review
  do Code que pegou drift romano vs literal) → `prompt-t02b-v3.md` 
  (sub-sub d.1 pinada após João ratificar) → `prompt-t02b-final.md`
  (versão pré-cleanup, com DD-5 expandida) → 
  `prompt-t02b-execucao.md` (versão final pós-cleanup, DD-5 colapsada,
  ~380 linhas — esta foi a colada no Code de #23).
- **PR `fix/render-romano-in-T02a` (#22.5):** branch ramificada de
  main; `tools.py` adicionou `_format_law_reference(lei, artigo,
  paragrafo, inciso, alinea)` + `_ROMAN_NUMERALS` (dict 1-50);
  `_format_first_stat_ref(entry)` virou wrapper trivial;
  `test_get_clause.py:172` ganhou asserção estrita `"LGPD Art. 7º, I"
  in text`. Pytest 20/20, ruff verde, mypy clean. Squash hash `<TBD>`.
- **PR `feat/policy-reader-find-clauses` (#23):** branch ramificada
  de main pós-merge de #22.5;
  `src/mcp_servers/policy_reader/tools.py` (adiciona
  `find_clauses_by_law_article` pública + `_matches` +
  `_render_query_text` + `_invalid_law_identifier` builder); 
  `src/mcp_servers/policy_reader/server.py` (substitui stub T01 por
  wrapper delegando para `tools.py`; docstring final carrega
  anti-uniformization rule literal); 
  `tests/mcp_servers/policy_reader/conftest.py` (estende 
  `policy_root_with_pack_clauses` para incluir POL-004); 
  `tests/mcp_servers/policy_reader/test_find_clauses.py` (novo, 7
  testes: AS-1 a AS-5 + AS-2 split narrow/broad + anchor 
  polimórfico). Pytest 27/27, ruff verde, mypy clean. Squash hash 
  `<TBD>`.

## Pins consolidados em #22 (carregam como contexto para #24+)

**Da Fase 2 — sessão #22 — convenções formalizadas:**

- **Sessões Chat persistentes vs sessões Code fresh — heurística por 
  tipo de output.** Chat sustenta múltiplos ciclos Code sem fresh entre
  eles quando o output é narrativo (decisões, ratificações, review);
  Code rotaciona sessão fresh por ciclo quando o output é verificável
  empiricamente (código com gates). Contexto que vale preservar vs
  descartar não é função do papel (Chat vs Code), é função do tipo de
  output. Aplicado em #22: Chat persistiu sobre prep + #22.5 + #23 +
  review sem degradação observável.

- **Scope discipline cross-PR — propriedade descritiva, não ritual.**
  Pattern PR sequencial (cleanup → main → feature) é descritivo de
  auditabilidade de blame por PR, não normativo de "sessão fresh por
  PR". Se o diff está limpo (verificável via Chat review do diff
  direto), a propriedade está atendida independente da sessão Code que
  produziu. Aplicado em #22 ao falso alarme da sessão Code de cleanup:
  cinco checks estruturais do diff bastaram, sem refazer em fresh.

- **Convenção POL-9NN para fixtures sintéticas de teste.** Range 
  reservado, separado de POL-001..POL-099 (cláusulas reais da Política)
  e do pack POL-001..POL-004 (`tests/.../fixtures/`). Documentada em
  docstring de `_write_synthetic_art5_root` e no README do pack. T03 e 
  além herdam.

- **Função compartilhada entre domínios vs tipo compartilhado.** 
  Compartilhar **função de formatação** entre stored entry e query é 
  OK (estabelecido em #22.5 via `_format_law_reference(lei, artigo, 
  paragrafo, inciso, alinea)`); compartilhar **tipo** requer
  justificativa semântica (rejeitado em DD-5 d.2 de #22: usar 
  `StatutoryReferenceEntry` para renderizar query confunde domínios
  deliberadamente distintos).

- **Filtro de deprecated em `find_clauses_by_law_article` é
  contratual per canonical §4.2 line 362.** AS-3 é o teste do contrato,
  não driver dele. Algoritmo aplica `c.status == "active"`
  estruturalmente, independente da AS.

- **Assertion strictness escala inversamente com expansibilidade do
  fixture.** Testes que **definem** contrato (anchor polimórfico) usam
  asserções estritas com ordem exata e count exato. Testes que
  **exercitam** contrato (AS-1, AS-2 broad) usam subset/inclusion. Pin
  a formalizar para T03+.

- **Filtro estrutural de deprecated estabelecido como pattern para 
  retrieval-style tools.** `get_clause` admite deprecated com tombstone
  (caso modal AS-2 de T02a); `find_clauses_by_law_article` exclui
  deprecated (canonical §4.2). T03 `check_applicability` precisa
  decidir explicitamente o tratamento — provavelmente retornar
  `CLAUSE_DEPRECATED` retryable com `details` completo (per canonical
  §5.4 e tasks.md T03 AS-7).

**Da Fase 2 — sessão #22 — wire/runtime invariantes (carregam para T03):**

- **Option B canonicalizado e aplicado dois consumidores.** T02a
  (`INVALID_CLAUSE_ID_FORMAT`, `CLAUSE_NOT_FOUND`) e T02b
  (`INVALID_LAW_IDENTIFIER`) consumiram sem DD. T03 herda: envelope
  em `structured_content` com `errorCode`, `content[0].text == message`,
  wire `isError: false`.

- **Helper de envelope `_envelope_tool_result` permanece em `tools.py`
  inline.** DD-1 de T02b ratificou inline ao invés de extrair para
  `_envelope.py`. **Gatilho de extração para T03**: T03 introduz 5
  errorCodes adicionais (`CLAUSE_DEPRECATED`, `UNKNOWN_DATA_CATEGORY`,
  `UNKNOWN_OPERATION`, `UNKNOWN_LEGAL_BASIS`, `STRUCTURED_CONTEXT_
  MISMATCH` conforme canonical §5.4). Refator natural na Fase 1 de T03,
  não additive — substantivo.

- **Wire-shape FastMCP 3.2.4 validado em T02a, T02b consumiu sem
  revalidar.** `Client(server.mcp).call_tool(...)` retorna
  `CallToolResult` com snake_case attrs (`is_error`, 
  `structured_content`, `content`). Anchor 
  `test_documents_fastmcp_tool_call_shape` permanece em
  `test_get_clause.py` como detector de breaking change futuro. T03
  reusa sem revalidar.

- **Helper `_format_law_reference` em `tools.py` (pós-cleanup #22.5)
  é single source of truth para rendering de referência legal.** T03
  consome em mensagens de veredito que carregam referência legal
  (e.g., `violation_candidate` message citando o artigo da cláusula).
  Não duplica `_ROMAN_NUMERALS`, não cria função paralela.

**Da Fase 2 — sessão #22 — pendências cosméticas anotadas (NÃO 
consertar agora):**

- **`tasks.md` §Companion edits cross-doc stale.** Lista menciona 
  itens resolvidos por PRs #36-#38 + cleanup #22.5. Quatro sessões
  consecutivas anotaram; ainda pendente. Sessão Chat de housekeeping
  cross-doc dedicada — após gate milestone-level de A ou em janela
  oportuna.

- **canonical §4.2 line 472 sem ordinal `º`.** "Nenhuma cláusula
  referencia LGPD Art. 50." (sem º) divergente das linhas 431/459
  (com º). Implementação T02b adotou consistência interna (`º`
  sempre); asserção AS-4 acompanha (`"Art. 50º."`). Débito anotado
  em três lugares para evitar perda de rastro: relatório Code Fase 2,
  Chat review independente, learning-log #22. Mesma sessão de
  housekeeping cross-doc resolve.

- **Convenções a formalizar em `.claude/rules/` ou ADR:** (a)
  sessões fresh vs persistentes por tipo de output; (b) assertion
  strictness vs subset; (d) função compartilhada vs tipo compartilhado
  entre domínios. (c) POL-9NN já documentada em docstring +
  pack README.

## Pre-flight pins para a sessão #24 (Chat fresh — prep do prompt T03)

Itens load-bearing para deliberação antes de virar prompt mecânico
de Code.

1. **DD-T03-1: refator de envelope helpers para módulo dedicado.**
   T03 é o gatilho real de extração registrado em DD-1 de T02b — 5
   errorCodes novos (`CLAUSE_DEPRECATED`, `UNKNOWN_DATA_CATEGORY`,
   `UNKNOWN_OPERATION`, `UNKNOWN_LEGAL_BASIS`, 
   `STRUCTURED_CONTEXT_MISMATCH` per canonical §5.4) aterrissam de
   uma vez. Manter inline aumentaria `tools.py` de ~285 para ~450+
   linhas. Decisão #24: extrair `_envelope.py` (genérico
   `_envelope_tool_result` + builders por errorCode) ou manter
   inline? Inclinação prévia: **extrair**. Brief T03 confirma na
   Fase 1.

2. **DD-T03-2: mecanismo interno de reasoning de
   `check_applicability`.** Plano de Fase 1.5 (#18) deferiu para Code
   livre: regra determinística, LLM-assisted, ou híbrido. Decisão
   substantiva na prep de T03. Trade-offs: regra é reprodutível e
   testável; LLM-assisted introduz não-determinismo e exige
   provenance; híbrido (regra primeiro, LLM como tie-breaker) é
   compromisso. Inclinação prévia: regra determinística para MVP,
   honestidade epistêmica via `indeterminate` quando regra não
   decide. Brief T03 confirma com escopo MVP per ADR-0007.

3. **DD-T03-3: filtro de escopo MVP via `not_applicable` para
   `operation ≠ collection`** per ADR-0007. Decisão #24: implementar
   o filtro antes ou depois do matching de cláusulas? Inclinação
   prévia: **antes** (curto-circuita; evita invocar matching fora de
   escopo). Brief T03 pina.

4. **DD-T03-4: modelagem do `structured_context`.** Análoga à
   DD-T02b-3 mas com 4 campos (`data_categories`, `operation`,
   `legal_basis`, `destination`) e estruturalmente mais rico (lista
   de categorias). Três caminhos: (a) parâmetros nomeados na
   assinatura; (b) Pydantic model `StructuredContext` em
   `models.py`; (c) dict via Field. Inclinação prévia: **(b)
   Pydantic** porque a complexidade justifica modelagem rica e
   permite validação cross-field via `model_validator`. Diferença
   vs T02b: aqui a estrutura ganha o suficiente para sair de "5
   args na assinatura" para "objeto estruturado".

5. **DD-T03-5: injeção da trinca de provenance
   `(policy_schema_version, policy_version, legal_framework)` em
   todo sucesso.** canonical §6.4 prescreve. Onde injetar — no
   envelope de sucesso (`_success_tool_result`), em layer separado
   (`_provenance_tool_result`), ou inline no payload retornado por
   `check_applicability`? Inclinação prévia: **inline no payload**
   (a trinca é parte semântica do veredito, não meta-info). Brief
   confirma.

6. **Pré-leitura obrigatória durante Fase 1 do prompt T03:**
   - `docs/tasks.md` T03 inteira (Função, Dependências, Files,
     AS-1..AS-7, Gate, Nota sobre nomenclatura do
     `structured_context`).
   - `docs/specs/policy-reader/canonical.md` §4.3 inteiro
     (load-bearing — quatro vereditos + provenance + escopo MVP).
   - `docs/specs/policy-reader/canonical.md` §5.4 (tabela
     consolidada — 5 errorCodes novos de T03).
   - `policy/SCHEMA.md` §6 inteiro (estrutura `substantive` —
     load-bearing para algoritmo de matching).
   - `docs/adr/0007-mvp-collection-only-scope.md` (escopo MVP).
   - Pack POL-001..004 inteiro (`tests/mcp_servers/policy_reader/
     fixtures/clauses_pack_check_applicability/`) incluindo POL-002
     que ficou de fora de T02b. README do pack seção "AS coverage
     por arquivo" mapeia AS de T03 para cláusulas específicas.
   - Estado real pós-T02b em `tools.py`, `server.py`, `models.py`,
     `conftest.py` — pin obrigatório de verificação direta antes
     de inferir do brief.

## Pendências cross-sessão (organizado por horizonte de resolução)

**Resolver na #24 (Chat fresh — prep do prompt T03):**

- Cinco pre-flight pins acima.
- Rascunho do prompt T03 com Fase 1 (leitura + plano com gate de
  OK) + Fase 2 (implementação com gates pytest/ruff/mypy) +
  guard-rails. Estrutura reusa pattern T01/T02a/T02b. Custo
  estimado: ~1-1.5h Chat de prep (T03 é a maior task em
  complexidade; mais DDs substantivas que T02b).

**Resolver em sessão Code #25+ (T03 execução):**

- Implementação completa de `check_applicability` em `tools.py` +
  thin wrapper em `server.py` + Pydantic `StructuredContext` em
  `models.py` (se DD-T03-4 ratificar) + refator de envelope helpers
  para `_envelope.py` (se DD-T03-1 ratificar extração) + testes em
  `test_check_applicability.py` cobrindo AS-1..AS-7.
- Gate task-level ADR-0008 §3: pytest verde, ruff verde, mypy
  verde, Chat review independente em sessão separada.

**Resolver pós-T03:**

- **T04** (`policy://vocabularies` + framework swap) — exercita
  framework-awareness via consumo dinâmico do vocabulário carregado.
  Pré-leitura consome cláusulas reais hipotéticas para GDPR (a
  redigir como fixture de teste de framework swap; sem pack
  análogo).

**Resolver em sessão Chat de housekeeping cross-doc dedicada:**

- **`tasks.md` §Companion edits cross-doc stale** (4 sessões
  anotaram; ainda pendente).
- **canonical §4.2 line 472 sem ordinal `º`** (débito cosmético).
- **Convenções a formalizar em `.claude/rules/` ou ADR:** (a)
  sessões fresh vs persistentes; (b) assertion strictness vs
  subset; (d) função vs tipo compartilhado.

**Resolver em janela futura sem urgência:**

- **DX residual:** linters como dev deps oficiais em
  `pyproject.toml`. Workaround `uvx ruff` / `uv run --with mypy
  mypy` funciona. Sessão Code curta (~15min).
- **Itens deferidos T03 herdados de Fase 1.5** (já listados em
  `tasks.md` §Companion edits): `operation`/`legal_basis` vs
  `operation_type`/`declared_legal_basis`; `evidence` vs `reason`
  em `not_applicable`. Resolver pós-T03 quando spec for empiricamente
  validado.
- **Decomposição formal de Milestone B em sessão Chat dedicada.**
  Após gate milestone-level de A. Decisão Semgrep-on-Windows
  precede.

## Hashes da sessão #22 (audit trail interno)

Branches `fix/render-romano-in-T02a` (#22.5) e
`feat/policy-reader-find-clauses` (#23). Hashes sobrevivem a
squash-merge — após merge das PRs, hashes individuais somem do main,
mas ficam registrados aqui:

- `<TBD>` — refactor(policy-reader): unify law-reference rendering 
  with Roman inciso (squash de `fix/render-romano-in-T02a` — sessão 
  Code #22.5)
- `<TBD>` — feat(policy-reader): T02b — tool 
  `find_clauses_by_law_article` com semântica prefix-hierarchical 
  (squash de `feat/policy-reader-find-clauses` — sessão Code #23)

(Hashes preenchidos após `git log main` pós-merge das duas PRs.)

## Nota de calibração metodológica (defense candidates novos)

Seis defense candidates novos consolidados em #22 (detalhados em
`docs/learning-log.md` entry de 2026-05-17 sessão #22):

1. Multi-instance review com escalation progressiva — três rounds,
   três classes distintas de catches.
2. AS-2 narrow como teste único pegando bug do `_matches` que
   escaparia silencioso em 5/6 testes — granularidade calibrada por
   dimensão de falha.
3. Reversão fundamentada DD-4 (fixture nova → estender existente)
   com argumentos novos via verificação direta ≠ inércia.
4. Heurística sessões fresh vs persistentes por tipo de output —
   refinamento empírico sobre quando Chat sustenta múltiplos ciclos
   Code.
5. Scope discipline cross-PR como propriedade descritiva
   (auditabilidade de blame), não ritual normativo — falso alarme
   #22.5 capturou isso.
6. Canary check via pin de pré-condição — replicação do "build the
   canary that screams first" (#19 wire-shape FastMCP) para estado
   de main entre sessões.

O método está se estabilizando suficientemente para virar
contribuição metodológica autônoma do TCC, não só ferramenta
operacional.