# Session handoff

**Última sessão fechada:** #22 (Chat) — prep prompt T02b + cleanup
`fix/render-romano-in-T02a` (sessão Code) + execução T02b
(`find_clauses_by_law_article`, sessão Code) + Chat review independente
+ housekeeping pré-T03 (sessão Code, 3 PRs paralelas) — 2026-05-17
**Próxima sessão:** #23 (Chat fresh) — prep do prompt T03
(`check_applicability`)
**Branch ativa atual:** `main` (PRs #39, #40, #41, #42, #43 mergeadas
via squash)
**Branch nova a abrir para #23:** não-aplicável (sessão Chat de prep)
**Branch nova a abrir pós-#23:** `feat/policy-reader-check-applicability`
(Code aplicará T03 ramificando de main pós-housekeeping)

## Estado atual

Milestone A em progresso. T02b fechada sob ciclo Chat persistente #22.
Housekeeping pré-T03 aplicado (3 PRs paralelas) formalizou 8 convenções
em artefatos auditáveis (5 rules em `.claude/rules/` + ADR-0009 + 2
pinadas em docstrings/pack README). Spec policy-reader coerente e
exercitada em três das quatro tools (`get_clause`,
`find_clauses_by_law_article` operacionais; `check_applicability`
permanece skeleton stub até T03; resource `policy://schema-version`
operacional; `policy://catalog` skeleton stub pendente T04;
`policy://vocabularies` não introduzido — entra em T04).

Status global de Milestone A:

- **T01** (Loader + handshake schema-version) — **fechada** (#19).
- **T02a** (`get_clause` + migração `tools.py`) — **fechada** (#20).
- **canonical-sync-A + A.2** (drift textual policy-reader +
  semgrep-runner) — **fechadas** (#20).
- **canonical-sync-B** (drift estrutural + Option B + polimorfismo +
  amendment ADR-0002) — **fechada** (#21).
- **fix/render-romano-in-T02a** (helper compartilhado
  `_format_law_reference` + romano em rendering de inciso) —
  **fechada** (PR #39, #22 cleanup).
- **T02b** (`find_clauses_by_law_article`) — **fechada** (PR #40,
  squash hash `fd6b833`, #22 execução).
- **Housekeeping pré-T03** (cosmetic debts + ADR-0009 + rules
  migration + new rules) — **fechada** (PRs #41, #42, #43, squash
  hashes `8f537d1`, `cc275dc`, `2ee1556` respectivamente; #22
  housekeeping).
- **T03** (`check_applicability`) — próxima task topológica, prep em
  #23, execução em sessão Code subsequente.
- **T04** (`policy://vocabularies` + framework swap) — após T03.
- **Gate milestone-level Milestone A** — sessão Chat dedicada após
  T01-T04 fecharem, ~1-2h, manual exercise via MCP Inspector
  exercitando cada RF de docs/REQUIREMENTS.md (RFs 004-parcial, 005,
  007-parcial, 008-parcial, 009).

## Onde encontrar detalhes do que #22 cristalizou

- **Prep do prompt T02b — versionamento iterativo:**
  `prompt-t02b-v1.md` → `prompt-t02b-v2.md` → `prompt-t02b-v3.md` →
  `prompt-t02b-execucao.md` (versão final pós-cleanup, ~380 linhas).
- **PR #39 `fix/render-romano-in-T02a`** (#22 cleanup): branch
  ramificada de main; `tools.py` adicionou `_format_law_reference(lei,
  artigo, paragrafo, inciso, alinea)` + `_ROMAN_NUMERALS` (dict 1-50);
  `_format_first_stat_ref(entry)` virou wrapper trivial;
  `test_get_clause.py:172` ganhou asserção estrita `"LGPD Art. 7º, I"
  in text`. Pytest 20/20, ruff verde, mypy clean.
- **PR #40 `feat/policy-reader-find-clauses`** (#22 execução, squash
  hash `fd6b833`): branch ramificada de main pós-merge de #39;
  `src/mcp_servers/policy_reader/tools.py` adiciona
  `find_clauses_by_law_article` pública + `_matches` +
  `_render_query_text` + `_invalid_law_identifier` builder;
  `server.py` substitui stub T01 por wrapper delegando para
  `tools.py` (docstring final carrega anti-uniformization rule
  literal); `conftest.py` estende `policy_root_with_pack_clauses`
  para incluir POL-004; novo `test_find_clauses.py` com 7 testes
  (AS-1 a AS-5 + AS-2 split narrow/broad + anchor polimórfico).
  Pytest 27/27, ruff verde, mypy clean.
- **PR #41 `chore/cosmetic-debts-and-status-flags`** (#22
  housekeeping, squash hash `8f537d1`): tasks.md §Companion edits
  cross-doc limpo (5 bullets resolvidos removidos + intro "Quatro" →
  "Dois"); canonical.md/compact.md correções `Art. Nº` em 6
  instâncias (1 prescrita Edit 2 + 5 análogos descobertos pelo Edit
  3); CLAUDE.md status flags refresh; "What does NOT belong" bullet
  atualizado.
- **PR #42 `docs/adr-0009-domain-boundaries`** (#22 housekeeping,
  squash hash `cc275dc`): ADR-0009 (133 linhas) formalizando "share
  functions, not types, between distinct domains" de DD-5 sub-sub
  T02b, com seção delimitando ADR scope vs `.claude/rules/` scope.
- **PR #43 `chore/rules-migration-and-authoring`** (#22 housekeeping,
  squash hash `2ee1556`): 5 arquivos novos em `.claude/rules/`
  (`spec-driven-workflow.md`, `privacy-safety.md`,
  `git-conventions.md`, `session-management.md`, `test-strategy.md`
  com `paths: "tests/**/*.py"` frontmatter); 3 seções removidas do
  CLAUDE.md (Conventions, Working methodology, Privacy and safety);
  CLAUDE.md final 69 linhas.

## Pins consolidados em #22 (carregam como contexto para #23)

**Convenções formalizadas em rules/ADR (load-bearing para todas
sessões futuras):**

- **Sessão Chat persistente vs sessão Code fresh — heurística por 
  tipo de output.** Chat sustenta múltiplos ciclos Code sem fresh
  entre eles quando o output é narrativo (decisões, ratificações,
  review); Code rotaciona sessão fresh por ciclo quando o output é
  verificável empiricamente. Formalizada em
  `.claude/rules/session-management.md`.

- **Scope discipline cross-PR — propriedade descritiva, não ritual.**
  Pattern PR sequencial (cleanup → main → feature) é descritivo de
  auditabilidade de blame por PR. Formalizada em
  `.claude/rules/git-conventions.md` (seção "PR sequencing pattern")
  com baseline empírico #19-#22 cleanup.

- **Convenção POL-9NN para fixtures sintéticas de teste.** Range
  reservado, separado de POL-001..POL-099 (cláusulas reais) e do pack
  POL-001..POL-004. Documentada em docstring de
  `_write_synthetic_art5_root` e README do pack. T03 herda — sem uso
  esperado em T03 se pack está bem calibrado.

- **Função compartilhada entre domínios vs tipo compartilhado.**
  Compartilhar função de formatação entre stored entry e query é OK
  (`_format_law_reference(lei, artigo, paragrafo, inciso, alinea)`);
  compartilhar tipo requer justificativa semântica. Formalizada em
  ADR-0009.

- **Filtro de deprecated em `find_clauses_by_law_article` é
  contratual per canonical §4.2 line 362.** AS-3 é o teste do
  contrato, não driver dele.

- **Assertion strictness escala inversamente com expansibilidade do
  fixture.** Testes que definem contrato (anchor polimórfico) usam
  asserções estritas com ordem exata e count exato. Testes que
  exercitam contrato (AS) usam subset/inclusion. Formalizada em
  `.claude/rules/test-strategy.md`.

- **Granularidade de teste calibrada por dimensão de falha.** AS-2
  narrow vs AS-2 broad em T02b — bug do `_matches` escaparia em 5/6
  testes se split não existisse. Formalizada em
  `.claude/rules/test-strategy.md`.

- **Plan mode pattern (Fase 1 / gate / Fase 2) obrigatório para
  tasks com múltiplos DDs.** Formalizada em
  `.claude/rules/spec-driven-workflow.md`.

- **Source-of-truth precedence: artefatos reais > docs em divergência
  mecânica.** Formalizada em `.claude/rules/spec-driven-workflow.md`.

- **Companion edits cross-doc como living debt registry.**
  Formalizada em `.claude/rules/spec-driven-workflow.md`.

**Wire/runtime invariantes (carregam para T03):**

- **Option B canonicalizado e aplicado dois consumidores.** T02a
  (`INVALID_CLAUSE_ID_FORMAT`, `CLAUSE_NOT_FOUND`) e T02b
  (`INVALID_LAW_IDENTIFIER`) consumiram sem DD. T03 herda: envelope
  em `structured_content` com `errorCode`, `content[0].text ==
  message`, wire `isError: false`.

- **Helper de envelope `_envelope_tool_result` permanece em
  `tools.py` inline.** DD-1 de T02b ratificou inline ao invés de
  extrair. **Gatilho de extração para T03**: 5 errorCodes
  adicionais (`CLAUSE_DEPRECATED`, `INVALID_DATA_CATEGORY`,
  `INVALID_OPERATION`, `EMPTY_DATA_CATEGORIES`,
  `STRUCTURED_CONTEXT_MISMATCH`) aterrissam de uma vez. Refator
  natural na Fase 1 de T03, agora substantivo.

- **Wire-shape FastMCP 3.2.4 validado em T02a, T02b consumiu sem
  revalidar.** Anchor `test_documents_fastmcp_tool_call_shape`
  permanece em `test_get_clause.py` como detector de breaking change
  futuro. T03 reusa sem revalidar.

- **Helper `_format_law_reference` em `tools.py`** (pós-cleanup #39)
  é single source of truth para rendering de referência legal. T03
  consome em mensagens de veredito que carregam referência legal
  (e.g., `violation_candidate` message citando o artigo da cláusula).
  Não duplica `_ROMAN_NUMERALS`, não cria função paralela.

## Pre-flight pins para sessão #23 (Chat fresh — prep do prompt T03)

Itens load-bearing para deliberação antes de virar prompt mecânico
de Code.

1. **DD-T03-1: refator de envelope helpers para módulo dedicado.**
   T03 é o gatilho real de extração registrado em DD-1 de T02b — 5
   errorCodes novos (`CLAUSE_DEPRECATED`, `INVALID_DATA_CATEGORY`,
   `INVALID_OPERATION`, `EMPTY_DATA_CATEGORIES`,
   `STRUCTURED_CONTEXT_MISMATCH` per canonical §5.4) aterrissam de
   uma vez. Manter inline aumentaria `tools.py` de ~285 para ~450+
   linhas. Decisão #23: extrair `_envelope.py` (genérico
   `_envelope_tool_result` + builders por errorCode) ou manter
   inline? Inclinação prévia: **extrair**. Brief T03 confirma na
   Fase 1.

2. **DD-T03-2: mecanismo interno de reasoning de
   `check_applicability`.** Plano de Fase 1.5 (#18) deferiu para
   Code livre: regra determinística, LLM-assisted, ou híbrido.
   Decisão substantiva na prep de T03. Trade-offs: regra é
   reprodutível e testável; LLM-assisted introduz não-determinismo e
   exige provenance; híbrido é compromisso. Inclinação prévia:
   **regra determinística para MVP**, honestidade epistêmica via
   `indeterminate` quando regra não decide. Pack cobre só 2
   controles MVP (consent_required, anonymization_required per
   ADR-0007), regra cabe em ~30 linhas legíveis. Brief T03 confirma.

3. **DD-T03-3: filtro de escopo MVP via `not_applicable` para
   `operation ≠ collection`** per ADR-0007. Decisão #23: implementar
   o filtro antes ou depois do matching de cláusulas? Inclinação
   prévia: **antes** (curto-circuita; evita invocar matching fora de
   escopo). AS-5 valida estruturalmente via spy/monkeypatch que o
   método de matching não foi invocado. Brief T03 pina.

4. **DD-T03-4: modelagem do `structured_context`.** Análoga à
   DD-T02b-3 mas com 4 campos (`data_categories`, `operation`,
   `legal_basis`, `destination`) e estruturalmente mais rico.
   Inclinação prévia: **Pydantic `StructuredContext` em `models.py`**
   porque a complexidade justifica modelagem rica e canonical §4.3
   explicitamente modela como objeto aninhado. FastMCP 3.x gera
   inputSchema aninhado a partir do model. Apresentar snippet
   mostrando inputSchema gerado na Fase 1.

5. **DD-T03-5: injeção da trinca de provenance
   `(policy_schema_version, policy_version, legal_framework)` em
   todo sucesso** per canonical §6.4. Inclinação prévia: **inline no
   payload retornado por `check_applicability`** (a trinca é parte
   semântica do veredito, não meta-info). Brief confirma.

**Itens adicionais derivados do review do Code sobre housekeeping
spec v1 (cinco issues que valem aplicar a prep T03):**

6. **DD-T03-6: output models polimórficos por veredito — localização
   pública vs privada.** Pydantic models discriminados por
   `Literal[verdict]` (Compliant, ViolationCandidate, Indeterminate,
   NotApplicable) + union type. Sub-decisão: union type em
   `models.py` exportado (contrato externo) ou privado em `tools.py`?
   Inclinação prévia: **`models.py` exportado** (parte do contrato
   MCP consumido pelo cliente). Diferenciar de
   `StructuredContext`: input se model é externo, fica em models.py;
   se Code optar por parâmetros nomeados, fica privado.

7. **DD-T03-7: AS-5 spy/monkeypatch — fragilidade conhecida
   anotada.** Monkeypatch sobre `_evaluate_clause` introduz
   acoplamento da test ao nome do helper privado. Refactor futuro
   renomeando o helper quebra o teste. Trade-off aceitável dado o
   ganho (validação estrutural real, não comportamental), mas
   anotar como débito de fragilidade conhecida no docstring do
   teste.

8. **DD-T03-8: vocabulary validation ordering.** Ordem das
   validations dita precedência de errorCode em inputs com
   múltiplos defeitos. Ordem natural: erros de formato
   (`INVALID_CLAUSE_ID_FORMAT`) → erros de existência
   (`CLAUSE_NOT_FOUND`) → erros de estado (`CLAUSE_DEPRECATED`) →
   escopo (`operation ≠ collection` → `not_applicable`) → erros de
   input semântico (`INVALID_DATA_CATEGORY`, `INVALID_OPERATION`,
   `EMPTY_DATA_CATEGORIES`) → matching. Apresentar ordem proposta
   em Fase 1 e justificar; senão a ordem fica implícita no
   algoritmo e vira débito.

9. **DD-T03-9: anchor tests análogos a `test_polymorphic_mix_at_art_5`
   de T02b.** Pelo menos dois anchors obrigatórios em T03:
   (i) `test_provenance_in_every_verdict_path` — parametrize sobre
   os 4 vereditos, asserta que payload carrega
   `policy_schema_version`, `policy_version`, `legal_framework` em
   todos. Cobertura por construção, não por confiar que cada AS
   checou. (ii) `test_deprecated_clause_returns_envelope_not_tombstone`
   — invoca `check_applicability(POL-003, ...)`, asserta
   `CLAUSE_DEPRECATED` no envelope; contraste com `get_clause(POL-003)`
   que retorna sucesso com tombstone (assimetria canonical §2.2
   load-bearing).

10. **DD-T03-10: vocabulary validation consome POL-000 carregado
    runtime.** T03 introduz primeira dependência semântica de
    POL-000 como vocabulário runtime (não só presença estrutural).
    Convenção a formalizar: validations de vocabulário consomem
    POL-000 via helper `_load_data_categories_vocabulary(state) ->
    set[str]` em `tools.py` (ou `_envelope.py` se aterrissar lá),
    não inline em `check_applicability`. Análogo para `operation`
    via `policy/vocabularies/<framework>/operation.yaml`.

**Pré-leitura obrigatória durante Fase 1 do prompt T03:**

- `docs/tasks.md` T03 inteira (Função, Dependências, Files,
  AS-1..AS-8, Gate, Nota sobre nomenclatura do
  `structured_context`).
- `docs/specs/policy-reader/canonical.md` §4.3 inteiro (load-bearing
  — quatro vereditos + provenance + escopo MVP).
- `docs/specs/policy-reader/canonical.md` §5.4 (tabela consolidada
  — 5 errorCodes novos de T03).
- `docs/specs/policy-reader/compact.md` §3 (error contract — T03
  emite 5 dos 7 errorCodes) + §5.3 (descrição da tool).
- `policy/SCHEMA.md` §6 inteiro (estrutura `substantive` —
  load-bearing para algoritmo de matching).
- `docs/adr/0007-mvp-collection-only-scope.md` inteiro.
- `docs/adr/0005-*.md` Decision 5 (provenance non-opcional) +
  Decision 7 (mecanismo de raciocínio livre).
- `docs/adr/0009-domain-boundaries-function-vs-type.md` — aplica
  ao design de `StructuredContext`.
- Pack POL-001..004 inteiro (incluindo POL-002 que ficou de fora de
  T02b). README do pack seção "AS coverage por arquivo" mapeia AS
  de T03 para cláusulas específicas.
- Estado real pós-T02b em `tools.py`, `server.py`, `models.py`,
  `conftest.py` — pin obrigatório de verificação direta antes de
  inferir do brief.
- Rules em `.claude/rules/` (carregadas automaticamente; particularmente
  `spec-driven-workflow.md` para plan mode + source-of-truth
  precedence + companion edits, e `test-strategy.md` para assertion
  strictness em anchors vs AS).

## Pendências cross-sessão (organizado por horizonte de resolução)

**Resolver na #23 (Chat fresh — prep do prompt T03):**

- Dez pre-flight pins acima.
- Rascunho do prompt T03 com Fase 1 (leitura + plano com gate de
  OK) + Fase 2 (implementação com gates pytest/ruff/mypy) +
  guard-rails. Estrutura reusa pattern T01/T02a/T02b. Custo
  estimado: ~1-1.5h Chat de prep (T03 é a maior task em
  complexidade; mais DDs substantivas que T02b).

**Resolver em sessão Code #24+ (T03 execução):**

- Implementação completa de `check_applicability` em `tools.py` +
  thin wrapper em `server.py` + Pydantic `StructuredContext` +
  output models discriminados em `models.py` (se DD-T03-4 e
  DD-T03-6 ratificarem) + refator de envelope helpers para
  `_envelope.py` (se DD-T03-1 ratificar extração) + testes em
  `test_check_applicability.py` cobrindo AS-1..AS-8 + 2 anchors
  obrigatórios (provenance ubíqua, deprecated assimetria) per
  DD-T03-9.
- Gate task-level ADR-0008 §3 conforme
  `.claude/rules/spec-driven-workflow.md`.

**Resolver pós-T03:**

- **T04** (`policy://vocabularies` + framework swap) — exercita
  framework-awareness via consumo dinâmico do vocabulário carregado.
  Pré-leitura consome cláusulas reais hipotéticas para GDPR (a
  redigir como fixture de teste de framework swap; sem pack
  análogo).
- **Sync canonical §4.3 `evidence` → `reason`** após T03 implementar
  e empiricamente validar (canonical-sync-C ou housekeeping
  cross-doc futura).
- **Sync RF-003 ↔ canonical §4.3 field naming** após T03 implementar
  e empiricamente validar.

**Resolver em sessão Chat de housekeeping cross-doc dedicada:**

- **Variantes "LGPD Art. N" sem ordinal `º` em prosa** —
  descobertas pelo Code durante Edit 3 da housekeeping (canonical
  §4.2 line 472 cobriu o pattern `Art\. [0-9]+\.` mas variantes
  inline em prosa passaram fora do scope do grep). Não bloqueia
  nada; cosmético textual em docs. Sessão Chat de housekeeping
  cross-doc futura resolve.

**Resolver em janela futura sem urgência:**

- **DX residual:** linters (ruff, mypy) como dev deps oficiais em
  `pyproject.toml`. Workaround `uvx ruff` / `uv run --with mypy
  mypy` funciona. Sessão Code curta (~15min) em qualquer janela.
- **Itens deferidos T03 herdados de Fase 1.5** (listados em
  `tasks.md` §Companion edits): `operation`/`legal_basis` vs
  `operation_type`/`declared_legal_basis`; `evidence` vs `reason`
  em `not_applicable`. Resolver pós-T03 quando spec for
  empiricamente validado.
- **Decomposição formal de Milestone B em sessão Chat dedicada.**
  Após gate milestone-level de A. Decisão Semgrep-on-Windows
  precede.

## Hashes da sessão #22 (audit trail)

Branches mergeadas em main durante #22:

- `<TBD-PR39>` — refactor(policy-reader): unify law-reference
  rendering with Roman inciso (squash de
  `fix/render-romano-in-T02a`, PR #39, #22 cleanup) — hash a
  preencher pelo João pós-pull.
- `fd6b833` — feat(policy-reader): T02b — tool
  `find_clauses_by_law_article` com semântica prefix-hierarchical
  (squash de `feat/policy-reader-find-clauses`, PR #40, #22
  execução).
- `8f537d1` — chore: housekeeping cosmetic debts and status flags
  refresh (squash de `chore/cosmetic-debts-and-status-flags`,
  PR #41, #22 housekeeping).
- `cc275dc` — docs(adr): ADR-0009 — domain boundaries, share
  functions not types (squash de `docs/adr-0009-domain-boundaries`,
  PR #42, #22 housekeeping).
- `2ee1556` — chore: migrate three CLAUDE.md sections to
  `.claude/rules/` and author two new rules (squash de
  `chore/rules-migration-and-authoring`, PR #43, #22 housekeeping).

## Nota de calibração metodológica (defense candidates novos)

Oito defense candidates consolidados em #22 (detalhados em
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
   (auditabilidade de blame), não ritual normativo.
6. Canary check via pin de pré-condição — replicação do "build the
   canary that screams first" (#19 wire-shape FastMCP) para estado
   de main entre sessões.
7. Triangulação cross-instância sobre cutoff — Code/Chat/docs
   externas/versão local concordando contra mesma source de verdade.
8. Convergência metodológica entre instâncias — review do Code
   sobre housekeeping spec capturou 4 classes em 1 round, indicador
   de internalização autônoma dos critérios do projeto.

O método está se estabilizando suficientemente para virar
contribuição metodológica autônoma do TCC, não só ferramenta
operacional. Capítulo de Método ganha oito defense candidates
empíricos desta sessão, mais a formalização canônica de oito
convenções em rules/ADR auditáveis (5 rules + 1 ADR + 2 em
docstrings/pack README).