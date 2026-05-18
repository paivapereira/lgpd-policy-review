# Session handoff

**Última sessão fechada:** #23 (Chat persistente) — prep prompt T03
v1→v2→v3 (3 reviews independentes intercalados) + GATE 1 Code Fase 1
+ Code Fase 2 execução + Chat review do diff + correções pré-PR + body
PR + T03 mergeada + housekeeping cross-doc pós-T03 (análise + leituras
+ ratificação 5 decisões + aplicação no workspace Chat para validação
+ migração para Code via prompt v1 → v2 com review intermediário) —
2026-05-18
**Próxima sessão:** #24 (Chat fresh) — prep prompt T04. Pré-requisito:
merge da PR T03-housekeeping (em execução no Code no fechamento da
sessão Chat).
**Branch ativa atual:** depende do estado de execução do Code:
- Durante housekeeping: `docs/housekeeping-post-t03` ramificando de
  main pós-T03.
- Pós-merge housekeeping: `main`.
**Branch nova a abrir para #24:** não-aplicável (sessão Chat de prep).
**Branch nova a abrir pós-#24:** `feat/policy-reader-resources-t04`
(Code aplicará T04 ramificando de main pós-housekeeping).

## Estado atual

Milestone A em progresso. **T03 fechada sob ciclo Chat persistente #23
primeiro sub-ciclo** (sete sub-eventos: prep v1 + review #1 + prep v2
+ reviews #2/#3 + prep v3 + GATE 1 + Fase 2 + Chat review diff +
correções + body PR). **T03-housekeeping em execução no Code** sob
prompt versionado da #23 segundo sub-ciclo (sete sub-eventos
adicionais: análise de bloqueio + ratificação 5 decisões + 4 leituras
adjacentes + aplicação no workspace + migração para Code + prompt v1 +
review Code + prompt v2). Spec policy-reader operacional em 3 das 4
tools (`get_clause`, `find_clauses_by_law_article`,
`check_applicability`); resource `policy://schema-version` operacional;
`policy://catalog` permanece skeleton stub até T04;
`policy://vocabularies` não-introduzido até T04.

Cinco débitos cross-doc residuais pós-T03 — em execução de fechamento
no Code no momento do close de #23. PR `docs/housekeeping-post-t03`
deve mergear na sequência (pytest 44/44 esperado: 43 prévios + 1 novo
do 5º setup do Anchor 1). Após esse merge, T03-housekeeping fecha e
T04 pode arrancar sem ruído cross-doc residual.

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
- **T03** (`check_applicability` + extração `_envelope.py`) —
  **fechada** (PR `<TBD>`, squash hash `<TBD — preencher pós-pull>`,
  #23 primeiro sub-ciclo prep+execução+review+merge).
- **T03-housekeeping** (cross-doc cleanup pós-T03 — drift 1 em 4 sites
  + DD-T03-12 canonical sync + drift 2 em tasks.md AS-7/AS-8 + gap
  destination + AS-5 trinque assertion) — **em execução** (PR
  `<TBD>`, squash hash `<TBD — preencher pós-merge>`, #23 segundo
  sub-ciclo).
- **T04** (`policy://catalog` + `policy://vocabularies` + framework
  swap) — próxima task topológica, prep em #24.
- **Gate milestone-level Milestone A** — sessão Chat dedicada após
  T04 fechar, ~1-2h, manual exercise via MCP Inspector exercitando
  cada RF de docs/REQUIREMENTS.md (RFs 004-parcial, 005,
  007-parcial, 008-parcial, 009).

## Onde encontrar detalhes do que #23 cristalizou

- **Prep do prompt T03 — versionamento iterativo:** `prompt-t03-v1.md`
  → `prompt-t03-v2.md` → `prompt-t03-v3.md` (~330 → ~430 → ~430
  linhas; segundo decaiu marginalmente após recuos calibrados).
  Iteração materializa multi-instance review.
- **Plano da Fase 1 do Code sancionado em GATE 1:** preservado no
  histórico Chat de #23 primeiro sub-ciclo. 10 DDs + DD-T03-11
  emergente + canary pre-flight executado contra estado real.
- **Body do PR T03:** `pr-body-t03.md` (~150 linhas) com 12 DDs
  tabuladas + drifts pós-T03 + notas metodológicas.
- **Prompt do housekeeping cross-doc:**
  `prompt-housekeeping-post-t03-v1.md` →
  `prompt-housekeeping-post-t03-v2.md` (~620 linhas, com 10 pares
  verbatim `str_replace`, pre-flight canary, gates pós-edit, PR body
  draft). v2 incorpora 5 melhorias do review do Code: numeração
  consistente, shell anotado, Edit 2 splitado em 2a + 2b, canary
  externo CI/scripts, limitação single-line do sanity grep
  documentada.
- **Detalhamento metodológico:** `docs/learning-log.md` entry
  2026-05-18 sessão #23 — onze defense candidates registrados.
- **Implementação T03:** +509/-98 linhas em 6 arquivos
  (`models.py`, `_envelope.py` novo, `tools.py`, `server.py`,
  `conftest.py`, `test_check_applicability.py`).

## Pins consolidados em #23 (carregam como contexto para #24+)

**Convenções formalizadas em rules/ADR (load-bearing para todas
sessões futuras — herdadas de #22 + reconfirmadas em #23):**

- Sessão Chat persistente vs sessão Code fresh — heurística por tipo
  de output (`.claude/rules/session-management.md`). #23 sustentou
  14+ sub-eventos sem fresh, escala consideravelmente maior que #22
  (6 sub-eventos).
- Scope discipline cross-PR — propriedade descritiva, não ritual
  (`.claude/rules/git-conventions.md`). #23 separou T03 e
  T03-housekeeping em PRs distintas materializando o pattern.
- Convenção POL-9NN para fixtures sintéticas de teste (docstring
  + pack README).
- Função compartilhada entre domínios vs tipo compartilhado (ADR-0009).
- Filtro de deprecated em `find_clauses_by_law_article` é contratual
  per canonical §4.2 line 362.
- Assertion strictness escala inversamente com expansibilidade do
  fixture (`.claude/rules/test-strategy.md`).
- Granularidade de teste calibrada por dimensão de falha
  (`.claude/rules/test-strategy.md`).
- Plan mode pattern (Fase 1 / gate / Fase 2) obrigatório para tasks
  com múltiplos DDs (`.claude/rules/spec-driven-workflow.md`).
- Source-of-truth precedence: artefatos reais > docs em divergência
  mecânica (`.claude/rules/spec-driven-workflow.md`).
- Companion edits cross-doc como living debt registry
  (`.claude/rules/spec-driven-workflow.md`).

**Convenções novas formalizadas em #23 (a migrar para rules/ADR em
sessão Chat de housekeeping ou ADR futura):**

- **DD emergente vs refinamento tactical — critério.** Alteração do
  set de retornos observáveis pelo caller separa as duas categorias.
  DD emergente exige cobertura própria (teste); tactical preserva
  contrato observável e dispensa ratificação. Materializado em #23
  com `Provenance(TypedDict)` (tactical) vs `DefinitionalClause`
  path → `not_applicable` (emergente, exigiu teste). Candidato a
  parágrafo em ADR-0008 ou rule nova `dd-classification.md`.

- **Multi-instance review com escalation progressiva — trend de
  convergência empírico.** #23 documentou 6 rounds com severidade
  decrescente (Material High → Minor → Material Medium → Emergent
  Constructive → Material Medium → 5 observações distintas em
  prompt-housekeeping v1). Pattern: review independente continua
  agregando enquanto redator e reviewer consultarem fontes
  diferentes. Candidato a defense narrative do Capítulo de Método.

- **Verificação direta vence inferência (terceira materialização
  pós-#19 e primeira metade #23).** v1 do prompt T03 errou
  DD-T03-2 ao inferir do brief; review #1 leu POL-001/POL-004
  YAMLs + README do pack direto e pegou o bug. Em housekeeping,
  leitura adjacente em compact §5.3 linha 376 descobriu site
  implícito que enumeração prévia não havia capturado. Three-strike
  rule materializado consolidando pattern. Candidato a rule
  `.claude/rules/verification-precedes-inference.md`.

- **Drift cumulativo é detectado por leitura adjacente ao site de
  edição, não por enumeração prévia.** DD-T03-11 escalou 2 → 3 →
  4 sites em rounds sucessivos. Pattern operacional para
  housekeeping cross-doc — leitura do contexto vizinho ao site de
  edição pega drifts implícitos que enumeração textual prévia
  perde.

- **Prompt como artefato auditável com mesma rigor que código.**
  Versionamento iterativo + review independente entre versões é
  pattern válido para output narrativo, não só para código.
  Materializado em #23 com prompt-housekeeping v1 → v2 pós-review
  do Code. Pattern relevante para qualquer sessão futura onde Chat
  produz prompt para Code executar.

- **Cirurgia textual via str_replace cirúrgico > substituição de
  arquivo inteiro para cleanup mecânico cross-doc.** Cada
  `old_str` funciona como canary de drift; se o estado de main
  divergiu, o `str_replace` falha cedo. Aplicável quando cleanup é
  mecânico (sem decisões de design) e auditabilidade de cada edit
  importa mais que velocidade. Materializado em
  prompt-housekeeping-post-t03-v2.

**Wire/runtime invariantes (carregam para T04):**

- **Option B canonicalizada em 7 sítios pós-T03-housekeeping.**
  Sítios: canonical §5.1/§5.3, compact §2, `models.py`
  `ErrorEnvelope.__doc__`, anchor `test_documents_fastmcp_tool_call_shape`
  em `test_get_clause.py`, ADR-0002 §3 amendment, **anchor novo
  `test_deprecated_clause_returns_envelope_not_tombstone` em
  `test_check_applicability.py`** (T03), **tasks.md AS-7/AS-8
  phrasing prescritivo** (T03-housekeeping). T04 herda sem
  deliberação.

- **Helper `_envelope_tool_result` em `_envelope.py`** (pós-T03).
  T04 consome para emitir envelopes de `policy://catalog` /
  `policy://vocabularies` se aplicável (resources tipicamente não
  emitem envelope; mas `INVALID_FRAMEWORK` ou análogos podem
  aterrissar).

- **Helper `_format_law_reference` em `tools.py`** (pós-cleanup #39
  + reuso em T03). Single source of truth. T04 herda sem deliberação.

- **`_provenance_from(state) -> Provenance(TypedDict)`** em
  `_envelope.py` (T03). Disponível para reuso em T04 se outros
  retornos exigirem trinque (e.g., entries de `policy://catalog`
  podem carregar provenance por cláusula? — decisão de DD em prep
  T04).

- **`_load_data_categories_vocabulary` e `_load_operation_vocabulary`**
  em `_envelope.py` (T03). T04 pode promover para externos (helpers
  públicos consumidos pelo resource `policy://vocabularies`) ou
  manter internos. Decisão de DD em prep T04.

- **`Verdict = Compliant | ViolationCandidate | Indeterminate |
  NotApplicable`** discriminated union plain (T03). Exportada;
  consumida por Milestone C Matcher.

- **`StructuredContext`** Pydantic interno pós-validação em
  `models.py` (T03) com campo `destination: str | None = None`
  (adicionado pós-Chat review do diff de T03; AS-1 exercita
  pós-housekeeping). NÃO exportado como contrato MCP. Decisão sobre
  subir para contrato externo deferred para Milestone C quando
  Matcher consumir.

- **DD-T03-12 documentada em canonical §4.3** (pós-housekeeping).
  Three sub-casos de `not_applicable` (MVP scope + applicability
  mismatch + definitional clause) explicitados em nota inline.
  Prep T04 lê §4.3 sem ruído.

## Pre-flight pins para sessão #24 (Chat fresh)

Pré-requisito procedural: confirmar merge da PR
`docs/housekeeping-post-t03` antes de arrancar prep T04. Checar via
GitHub ou `git log --oneline -5 main`.

### Pré-leitura obrigatória para prep T04

- canonical §3.1 inteira (`policy://catalog`): forma de retorno,
  ordering, status flags por entry, deprecated handling.
- canonical §3.3 inteira (`policy://vocabularies`): 4 vocabulários
  jurisdicionais expostos via 1 resource, forma de retorno per
  framework, framework swap consequence.
- compact §4.1 + §4.3: variantes compactas dos resources.
- `policy/SCHEMA.md` §10.1-§10.3 (layout multi-cliente, formato dos
  vocabularies, troca de framework).
- ADR-0005 Decisions 3 (4 vocabulários jurisdicionais), 4
  (`policy://vocabularies` como surface canônica), 7 (mecanismo de
  raciocínio livre — extends para T04 também).

### DDs antecipadas para T04

- **DD-T04-1 — `policy://catalog` shape.** Lista plana com clause_id
  + title + status + clause_type + statutory_reference_summary +
  successors (se deprecated)? Ou nested por clause_type? Inclinação
  prévia: lista plana ordenada por clause_id; deprecated entries
  incluem `successors` em entry; consumer filtra por `status` se
  precisar.
- **DD-T04-2 — `policy://vocabularies` shape.** Um resource expondo 4
  vocabulários jurisdicionais (`operation`, `lawful_basis`, `control`,
  `out_of_scope`) per framework. Forma: objeto top-level com chaves
  por vocabulário, ou 1 resource por vocabulário (4 resources
  separados)? Canonical §3.3 prescreve um single resource;
  reconfirmar.
- **DD-T04-3 — Provenance em entries do catalog.** Cada entry
  carrega trinque? Ou trinque vive só no header do resource? Reuso
  potencial de `_provenance_from`.
- **DD-T04-4 — `_load_*_vocabulary` helpers em `_envelope.py`
  externalizados?** Promover para públicos (consumidos pelo resource
  `policy://vocabularies`) ou criar duplicata específica do resource?
  Inclinação prévia: promover (single source of truth).
- **DD-T04-5 — Cláusulas reais hipotéticas para GDPR.** Fixture de
  teste de framework swap. Pack análogo ao
  `clauses_pack_check_applicability/` mas mínimo (2-3 cláusulas
  GDPR cobrindo o caminho crítico).
- **DD-T04-6 — Wire shape de resource `read_resource`.** Padrão
  T01 (FastMCP retorna estrutura específica para resources, captured
  por anchor `test_documents_fastmcp_read_resource_shape`). T04
  herda; anchor permanece como guard.

### Estado real pós-T03-housekeeping (pré-leitura adicional)

- `tools.py`: 3 funções públicas operacionais; `check_applicability`
  consome `_envelope.py` helpers via import.
- `server.py`: 3 tools registradas + 2 resources (1 operacional +
  1 skeleton stub `get_catalog`).
- `_envelope.py`: 7 errorCode builders + provenance helper +
  2 vocabulary loaders (candidatos a promoção em T04).

Custo estimado de T04: ~1-1.5h Chat prep + ~2-3h Code execução.
Menor que T03 (resources são aditivos sobre o existente; sem 4
verdict models nem 6 errorCodes a desenhar; mas DD-T04-2 e DD-T04-5
têm complexidade própria — framework swap é trade-off real).

## Pendências cross-sessão (organizado por horizonte de resolução)

**Resolver imediatamente (em execução no Code no close de #23):**

- PR `docs/housekeeping-post-t03` aplicando os 10 sub-edits
  cirúrgicos via `str_replace` em 4 arquivos
  (canonical/compact/tasks/test). Gates: canary greps pré + 10 edits
  + canary greps pós + pytest 44/44 + ruff + mypy. Custo: ~30-45min.

**Resolver em sessão #24 (Chat fresh) — prep prompt T04:**

- 6 DDs antecipadas (DD-T04-1 a DD-T04-6) + prep do prompt T04 com
  Fase 1/GATE 1/Fase 2 + guard-rails.

**Resolver em sessão Code #25+ (execução T04):**

- Execução T04 + Chat review independente + body PR + merge.

**Resolver pós-T04:**

- **Gate milestone-level Milestone A.** Sessão Chat dedicada ~1-2h
  manual exercise via MCP Inspector contra RFs 004-parcial, 005,
  007-parcial, 008-parcial, 009. Pré-requisito: T04 fechada.

**Resolver em janela futura sem urgência:**

- **DX residual:** linters (ruff, mypy) como dev deps oficiais em
  `pyproject.toml`. Workaround `uvx ruff` / `uv run --with mypy mypy`
  funciona. Sessão Code curta (~15min) em qualquer janela.
- **Decomposição formal de Milestone B em sessão Chat dedicada.**
  Após gate milestone-level de A. Decisão Semgrep-on-Windows
  precede.
- **Migração de convenções novas (#23) para rules/ADR:** critério DD
  emergente vs tactical, multi-instance review trend, verification
  precedes inference, drift cumulativo via leitura adjacente, prompt
  como artefato auditável, cirurgia textual cleanup. Sessão Chat de
  housekeeping metodológico pós-T04 ou pós-Milestone A. Custo
  estimado: ~1h Chat prep + ~30min Code aplicação em ~3 PRs
  mecânicas.

## Hashes da sessão #23 (audit trail)

Branches mergeadas em main durante #23:

- `<TBD — preencher pós-pull>` — feat(policy-reader): T03 —
  check_applicability with 4-verdict enum, provenance trinque,
  MVP-scope filter (squash de
  `feat/policy-reader-check-applicability`, PR #<TBD>, #23 primeiro
  sub-ciclo).
- `<TBD — preencher pós-merge>` — docs(policy-reader):
  T03-housekeeping — cross-doc cleanup pós-T03 (squash de
  `docs/housekeeping-post-t03`, PR #<TBD>, #23 segundo sub-ciclo —
  em execução no Code no fechamento da sessão Chat).

## Nota de calibração metodológica (defense candidates de #23)

Onze defense candidates consolidados em #23 (detalhados em
`docs/learning-log.md` entry de 2026-05-18 sessão #23):

1. Multi-instance review com escalation progressiva — trend
   empírico de convergência em 6 rounds com severidade decrescente.
2. DD emergente vs refinamento tactical — critério de classificação
   por alteração do set de retornos observáveis pelo caller.
3. Verificação direta vence inferência — terceira materialização
   após #19 e primeira metade #23.
4. Plan-mode admite refinamento técnico durante execução sem voltar
   ao Chat — critério tríplice (preserva contrato + resolve fricção
   real + sem coupling novo).
5. `.claude/rules/` carregadas automaticamente reduzem boilerplate
   em prompts subsequentes — ~30% redução v3 vs v1 do prompt T03.
6. Chat persistente sustentando 14+ sub-eventos sem fresh —
   escala consideravelmente maior que #22 (6 sub-eventos); pattern
   por tipo de output confirmado.
7. Cumulative drift discovery via reviews independentes — compact
   §5.3 linha 371 descoberta na Fase 1 do Code (3º site); linha 376
   descoberta em housekeeping (4º site).
8. Drift cumulativo é detectado por leitura adjacente ao site de
   edição, não por enumeração prévia.
9. Prompt como artefato auditável com mesma rigor que código —
   versionamento iterativo + review independente.
10. Cirurgia textual via str_replace cirúrgico > substituição de
    arquivo inteiro para cleanup mecânico cross-doc.
11. Escolha do mecanismo de edit (substitution vs replacement vs
    patch) é decisão arquitetural, não detalhe operacional.

O método deste projeto está se estabilizando suficientemente para
virar contribuição metodológica autônoma do TCC, não só ferramenta
operacional. Capítulo de Método ganha onze defense candidates
empíricos desta sessão. Total Capítulo de Método pós-#23: ~35+
defense candidates documentados em learning-log entries de #19-#23.