# Session-handoff — atualizações pós-T04 (sessão #24 close)

**Para aplicar:** este arquivo carrega as seções de `docs/session-handoff.md` que
mudam pós-T04. Cada seção abaixo é um bloco que **substitui** a seção homônima
no arquivo atual via `str_replace` cirúrgico no Code. Seções não listadas aqui
(Decisões cristalizadas, Defaults arquiteturais, Glossário, etc.) **permanecem
inalteradas** — o handoff é atualizado, não reescrito.

Ordem de aplicação:

1. Header (3 primeiros bullets) — `str_replace` simples.
2. Estado atual — substitui seção inteira.
3. Pendências cross-sessão — substitui seção inteira.
4. Hashes da sessão — apenda novo bloco de #24 abaixo do bloco de #23.
5. Pre-flight pins para sessão #24 — **REMOVER** essa seção (despachada).
6. Pre-flight pins para sessão #25 — nova seção (adicionar).
7. Estado real pós-T04 — substitui seção homônima de "Estado real pós-T03-housekeeping".

Após apresentar o diff cirúrgico ao usuário, Code aguarda OK explícito antes
de aplicar.

---

## 1. Header (3 primeiros bullets)

**Substituir** o bloco que começa com `**Última sessão fechada:** #23` (final
do close de housekeeping pós-T03) por:

```markdown
**Última sessão fechada:** #24 (Chat persistente) — prep prompt T04 iterativo
v1→v2→v3 com 3 rounds de multi-instance review + GATE 1 sancionado com
DD-T04-14 emergente + 2 Observations + Fase 2 implementação + Chat review
pós-implementação com canonical §3.1 sync emergente anotado em
§Companion edits + push + merge T04 — 2026-05-19
**Próxima sessão:** #25 — duas alternativas válidas:
- **Alternativa A (recomendada):** Chat fresh dedicada ~1-2h para gate
  milestone-level Milestone A via MCP Inspector contra RFs 004-parcial /
  005 / 007-parcial / 008-parcial / 009.
- **Alternativa B:** Code curta ~1h para housekeeping cross-doc
  consolidando os 4 débitos em PR única `chore/housekeeping-post-t04`.

Decisão de ordem A→B vs B→A na hora; ambas válidas.
**Branch ativa atual:** `main` (pós-merge T04).
**Branch nova a abrir para #25:** depende da alternativa escolhida:
- A: não-aplicável (sessão Chat de gate milestone-level).
- B: `chore/housekeeping-post-t04`.
```

---

## 2. Estado atual

**Substituir** a seção `## Estado atual` inteira por:

```markdown
## Estado atual

**Milestone A task-level COMPLETO.** Tasks T01-T04 todas fechadas com gate
task-level (function tests + Chat review independente). Pytest cumulativo:
53/53 verde. Spec policy-reader operacional em 4 das 4 tools+resources
contratadas (`get_clause`, `find_clauses_by_law_article`, `check_applicability`,
`get_catalog`, `get_vocabularies`) — `policy://schema-version` +
`policy://catalog` + `policy://vocabularies` os 3 resources operacionais.
Framework swap exercitado no nível do componente via fixture synthetic_gdpr
(AS-5 de T04).

**Gate milestone-level Milestone A — pendente.** Sessão Chat dedicada ~1-2h
via MCP Inspector contra RFs 004-parcial / 005 / 007-parcial / 008-parcial /
009 conforme `docs/tasks.md` §Milestone A — pré-requisito para abrir
Milestone B.

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
  migration + new rules) — **fechada** (PRs #41/#42/#43, squash
  hashes `8f537d1`, `cc275dc`, `2ee1556`, #22 housekeeping).
- **T03** (`check_applicability` + extração `_envelope.py`) —
  **fechada** (PR `<TBD — preencher pós-pull>`, #23 primeiro sub-ciclo).
- **T03-housekeeping** (cross-doc cleanup pós-T03 — drift 1 + drift 2 +
  DD-T03-12 canonical sync + Anchor 1 estendido) — **fechada** (PR
  `<TBD — preencher pós-pull>`, squash hash `1db6257`, #23 segundo
  sub-ciclo).
- **T04** (`policy://catalog` + `policy://vocabularies` + framework swap)
  — **fechada** (PR #46, squash hash `<TBD — preencher pós-pull>`, #24
  ciclo Chat persistente + sequência Code).
- **Gate milestone-level Milestone A** — sessão Chat dedicada pendente,
  ~1-2h, manual exercise via MCP Inspector exercitando cada RF
  declarada de Milestone A.

Quatro débitos cross-doc residuais em `docs/tasks.md` §Companion edits
cross-doc aguardando housekeeping pós-T04 (detalhados em Pendências).
Não bloqueiam gate milestone-level.
```

---

## 3. Pendências cross-sessão

**Substituir** a seção `## Pendências cross-sessão (organizado por horizonte
de resolução)` inteira por:

```markdown
## Pendências cross-sessão (organizado por horizonte de resolução)

**Resolver em sessão #25:**

- Alternativa A (recomendada): **Gate milestone-level Milestone A** via
  MCP Inspector contra RFs 004-parcial / 005 / 007-parcial / 008-parcial
  / 009. Pré-requisito procedural: confirmar MCP Inspector funcional no
  ambiente Windows do João + Política de teste apontando para fixture
  synthetic_gdpr para exercitar RF-008.
- Alternativa B: **Housekeeping cross-doc pós-T04** consolidando 4
  débitos em PR única `chore/housekeeping-post-t04` (ver detalhamento
  abaixo).

**Resolver em sessão Code curta (~1h, não bloqueia gate milestone-level):**

- **Housekeeping cross-doc pós-T04.** 4 débitos em `docs/tasks.md`
  §Companion edits cross-doc:
  1. Sync `docs/session-handoff.md` ↔ split Milestone A/B (legado pré-T04).
  2. Sync canonical.md `structured_context` campos + `evidence`/`reason`
     em §4.3 (2 sub-itens legado pré-T04).
  3. Rename `_format_first_stat_ref` → `_format_stat_ref` em `tools.py`
     (3 call sites + 1 novo introduzido por T04; ~7 linhas de
     `str_replace` cirúrgico).
  4. Sync canonical.md §3.1 sobre shape de `article_sources_summary`
     (emergente T04: lista de strings renderizadas via formatter
     compartilhado, uma string por entrada de `statutory_reference`).
  Despacho recomendado: PR única `chore/housekeeping-post-t04` com
  commits separados internamente. Custo: ~1h Code.

**Resolver pós-gate milestone-level Milestone A:**

- **Decomposição formal de Milestone B em sessão Chat dedicada.**
  Pré-requisito: decisão Semgrep-on-Windows (Docker, pip native, remote
  worker, CI-only) precede.
- **Decomposição formal de Milestones C e D em sessões Chat dedicadas
  sequenciais.**
- **Migração de convenções novas (#23-#24) para rules/ADR.** Lista
  cumulativa de defense candidates pós-Milestone A:
  - DD emergente vs tactical (#23).
  - Multi-instance review trend com assimetria crítica/refinamento
    (#23, refinado em #24).
  - Verificação direta vence inferência — quinta materialização (#19,
    primeira metade #23, housekeeping #23, prep #24, Chat review #24).
  - Drift cumulativo via leitura adjacente (#23).
  - Prompt como artefato auditável (#23, refinado em #24 com 3 rounds
    de versionamento).
  - Cirurgia textual cleanup (#23).
  - GATE com halt condition explícita parametrizada por outcome (#24).
  - Smoke test pre-Fase 2 para framework unknown empírico (#24).
  - Diferimento via §Companion edits como pattern operacional de scope
    discipline (#24).
  - Rule auto-loading vs disciplina deliberada no Chat (#24).
  Sessão Chat metodológica pós-Milestone A. Custo estimado: ~1h Chat
  prep + ~30min Code aplicação em ~3 PRs mecânicas.

**Resolver em janela futura sem urgência:**

- **DX residual:** linters (ruff, mypy) como dev deps oficiais em
  `pyproject.toml`. Workaround `uvx ruff` / `uv run --with mypy mypy`
  funciona. Sessão Code curta (~15min) em qualquer janela.
- **Promoção do draft `_drafts/spec-authoring-principles.md` para
  `docs/`.**
- **Validação cruzada per-cliente (vocabulary × Semgrep metadata)**
  quando materializar ADR de per-client rule set.
```

---

## 4. Hashes da sessão #24 (audit trail)

**Apendar** novo bloco `### Hashes da sessão #24 (audit trail)` abaixo do
bloco existente `### Hashes da sessão #23 (audit trail)`. Conteúdo literal:

```markdown
### Hashes da sessão #24 (audit trail)

Branches mergeadas em main durante #24:

- `<TBD — preencher pós-pull>` — feat(policy-reader): T04 — resources
  catalog + vocabularies + framework swap (squash de
  `feat/policy-reader-resources-t04`, PR #46, #24 ciclo Chat persistente
  + sequência de sessões Code: prep iterativo v1→v2→v3 com 3 rounds de
  multi-instance review, Fase 1.A com smoke tests obrigatórios + canary
  9 itens, GATE 1 sancionado com 13 DDs ratificadas + DD-T04-14
  emergente + 2 Observations, Fase 2 implementação, Chat review com
  débito emergente anotado, push e merge).
```

---

## 5. Pre-flight pins para sessão #24

**REMOVER** a seção `## Pre-flight pins para sessão #24 (Chat fresh)`
inteira (incluindo todos os sub-blocos: Pré-leitura obrigatória, DDs
antecipadas, Estado real pós-T03-housekeeping, custo estimado). Conteúdo
foi consumido em #24; não precisa permanecer no handoff.

---

## 6. Pre-flight pins para sessão #25

**Adicionar** nova seção no lugar onde estava §"Pre-flight pins para sessão
#24" removida. Conteúdo literal:

```markdown
## Pre-flight pins para sessão #25

Pré-requisito procedural depende da alternativa:

- **Alternativa A (gate milestone-level):** MCP Inspector instalado e
  funcional no ambiente Windows do João. Confirmar via launch local
  contra `policy-reader` rodando com `uv run python -m
  mcp_servers.policy_reader.server` apontando para `policy/` real
  (LGPD) e depois contra fixture `synthetic_gdpr/` (GDPR).

- **Alternativa B (housekeeping cross-doc):** ramificar de `main`
  pós-merge T04; branch nova `chore/housekeeping-post-t04`. Pytest
  53/53 deve permanecer verde após housekeeping (rename de helper é
  cross-cutting e exercitado por testes existentes).

### Pré-leitura obrigatória para Alternativa A (gate milestone-level)

- `docs/REQUIREMENTS.md` RFs 004 / 005 / 007 / 008 / 009 — cenários
  Dado/Quando/Então redigidos em Fase 1.
- `docs/tasks.md` §Milestone A "RFs/RNFs cobertas no gate
  milestone-level" — boundary do que é coberto vs deferred (RF-004
  pleno requer Matcher em Milestone C; T03 entrega motor de veredito +
  filtro de escopo MVP).
- `docs/specs/policy-reader/canonical.md` §3 (resources) + §4 (tools)
  + §5 (errors) — contratos a exercitar via MCP Inspector.
- `docs/adr/0007-mvp-collection-only-scope.md` — boundary do `not_applicable`
  para operações fora de `collection` (exercitado em RF-005).
- `docs/adr/0005-multi-client-policy-architecture.md` Decisions 2 + 5 +
  6 — argumentação de RF-007/RF-008.

### Pré-leitura obrigatória para Alternativa B (housekeeping)

- `docs/tasks.md` §Companion edits cross-doc — 4 débitos enumerados.
- `tools.py` — sites de `_format_first_stat_ref` (3 pré-existentes + 1
  novo em `get_catalog`).
- `docs/specs/policy-reader/canonical.md` §3.1 — bloco a estender com
  shape de `article_sources_summary`.
- `docs/specs/policy-reader/canonical.md` §4.3 — bloco a estender com
  `evidence`/`reason` clarification.
- `docs/session-handoff.md` (este arquivo) — seções a sincronizar com
  split Milestone A/B.

### Estado real pós-T04

- `tools.py`: 5 funções públicas operacionais (`get_clause`,
  `find_clauses_by_law_article`, `check_applicability`, `get_catalog`,
  `get_vocabularies`).
- `server.py`: 3 tools registradas + 3 resources registrados, todos thin
  wrappers delegando a `tools.<func>(_STATE)`. `mime_type="application/json"`
  explícito em todos os 3 resources.
- `_envelope.py`: 7 errorCode builders + provenance helper + 2 vocabulary
  loaders. Intocado em T04 — tech debt declarada no docstring topo
  satisfeita por não-promoção.
- `models.py`: intocada em T04. `LoadedPolicy.vocabularies: dict[str,
  Vocabulary]` consumido por `tools.get_vocabularies` via
  `vocab.model_dump(mode="json")` direto.
- `tests/mcp_servers/policy_reader/`: 53 testes (44 herdados + 9 novos
  T04: 6 AS + anchor 1 parametrizado [2 cases] + anchor 2).
- `tests/.../fixtures/synthetic_gdpr/`: 6 arquivos (1 policy.yaml + 1
  POL-000 stub + 4 vocabs GDPR), conformância ao SCHEMA verificada.
- `policy/clauses/POL-000.yaml`: intocado (template estrutural usado
  como referência para stub synthetic_gdpr).
- Anchor `test_documents_fastmcp_read_resource_shape` de T01 cobre wire
  via `policy://schema-version` (dict shape); T04 confirmou empiricamente
  via smoke test que top-level list também é aceita por FastMCP 3.x —
  anchor não foi estendido, decisão deferida para sessão futura se
  necessário.
```

---

## 7. Aplicação via Code

Sequência sugerida (Code aplica via `str_replace` quando bloco é
substituição cirúrgica, ou via edit estrutural quando bloco é
remoção/adição):

1. **Substituições cirúrgicas** (`str_replace`):
   - Header 3 bullets (seção 1 acima).
   - Estado atual inteira (seção 2).
   - Pendências cross-sessão inteira (seção 3).

2. **Remoção** (`str_replace` com `new_str` vazio):
   - §"Pre-flight pins para sessão #24" inteira (seção 5).

3. **Adição** (`str_replace` localizando ponto de inserção):
   - Novo bloco "Hashes da sessão #24" abaixo de "Hashes da sessão #23"
     (seção 4).
   - Nova seção "Pre-flight pins para sessão #25" no lugar onde estava a
     §24 removida (seção 6).

**Verificação pré-commit:**
- `git diff docs/session-handoff.md` — confirmar 6 modificações
  cirúrgicas, sem ruído.
- `git diff docs/learning-log.md` — confirmar adição da entry #24
  inteira no final, sem modificar entries anteriores.
- Markdown rendering preview se IDE permitir — confirmar que tabelas/
  listas não quebraram.

**Commit messages** (Conventional Commits, sem `Co-Authored-By` per
`.claude/rules/git-conventions.md`):

```
docs(log): close session #24 — T04 implementation + 3-round prompt review pattern

Five defense candidates consolidated for the TCC Capítulo de Método:
- Validation-retry loop manual via multi-instance review (3 rounds; v1→v2→v3)
- GATE with explicit halt condition parameterized by empirical smoke-test
- Rule auto-loading vs deliberate invocation discipline at Chat layer
- Deferral via §Companion edits cross-doc as operational scope-discipline pattern
- Direct verification beats inference — fifth materialization crystallizes
  recurring pattern (rule candidate for .claude/rules/)

T04 closed (PR #46); Milestone A task-level complete (T01-T04). Pytest 53/53.
Four cross-doc debts pending housekeeping; gate milestone-level pending
dedicated Chat session ~1-2h via MCP Inspector against RFs 004-partial / 005 /
007-partial / 008-partial / 009.
```

```
docs(handoff): sync session-handoff.md to post-T04 state (close #24, open #25)

Update state, pending items, hashes, and pre-flight pins to reflect:
- Milestone A task-level complete (T01-T04 closed)
- Four cross-doc debts in tasks.md §Companion edits awaiting housekeeping
- Session #25 alternatives (A: gate milestone-level; B: housekeeping)
- Pre-flight pins per alternative
- Real state post-T04 (5 public functions in tools.py; 3 resources; envelope +
  models untouched)
```

PRs separadas (uma por commit) ou consolidadas em PR única
`docs/close-session-24` — decisão na hora. Inclinação minha:
consolidada, ambos commits são docs-only sem risco de regressão, blame
auditability preservada por commits separados internamente.