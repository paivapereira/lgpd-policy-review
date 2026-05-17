# Session handoff

**Última sessão fechada:** #21 (Chat) — canonical-sync-B (Option B
documentado + polimorfismo + drift estrutural) — 2026-05-17
**Próxima sessão:** #22 (Chat) — prep do prompt T02b
(`find_clauses_by_law_article`)
**Branch ativa atual:** `main` (PR #38 mergeada via squash com hash
`<TBD>`)
**Branch nova a abrir para #22:** não-aplicável (sessão Chat de prep)
**Branch nova a abrir pós-#22:** `feat/policy-reader-find-clauses`
(Code aplicará T02b ramificando de main)

## Estado atual

Milestone A em progresso. canonical-sync-B fechada em #21, removendo
o último bloqueio para T02b. Spec do policy-reader agora coerente em
todos os eixos: isError-semantics adaptada para Option B em
canonical/compact + amendment ADR-0002 §3; polimorfismo
`applicability_scope` → `applies_to` materializado com discriminação
por `clause_type`; vocabulário de `operation` migrado para tokens
canônicos (`storage`, `disclosure_by_transmission`) per SCHEMA.md §9.2.
PR #38 mergeada em main consolidando dois commits pré-squash (`5926a03`
+ `1bbc6fe`) em um único hash de squash registrado no learning-log.

Status global de Milestone A:

- **T01** (Loader + handshake schema-version) — **fechada** (#19).
- **T02a** (`get_clause` + migração `tools.py`) — **fechada** (#20).
- **canonical-sync-A + A.2** (drift textual policy-reader +
  semgrep-runner) — **fechadas** (#20).
- **canonical-sync-B** (drift estrutural + Option B + polimorfismo +
  amendment ADR-0002) — **fechada** (#21).
- **T02b** (`find_clauses_by_law_article`) — próxima task topológica,
  prep em #22, execução em #23+.
- **T03** (`check_applicability`) — após T02b.
- **T04** (`policy://vocabularies` + framework swap) — após T03.
- **Gate milestone-level Milestone A** — sessão Chat dedicada após
  T01-T04 fecharem, ~1-2h, manual exercise contra RFs 004-parcial,
  005, 007-parcial, 008-parcial, 009.

## Onde encontrar detalhes do que #21 cristalizou

- **canonical-sync-B implementação:**
  `docs/specs/policy-reader/canonical.md` (9 edits cobrindo §4.1,
  §4.2, §4.3, §5.1, §5.3);
  `docs/specs/policy-reader/compact.md` (6 edits cobrindo §2, §3,
  §5.1, §5.2, §5.3);
  `docs/adr/0002-mcp-conventions-and-deferments.md` (1 edit cobrindo
  amendment in-place ao Decision 3, ~9 parágrafos com line-number
  provenance);
  `src/mcp_servers/policy_reader/models.py` (docstring `ErrorEnvelope`
  alinhada com canonical §5.1 pós-amendment).
- **Convenção Option B documentada formalmente:** canonical §5.1
  (reescrita), canonical §5.3 (reformulada em torno do discriminador
  `errorCode` presence), compact §2 (Option B parágrafo), ADR-0002 §3
  amendment (com constraint FastMCP + rationale + revisit trigger +
  CLOSED status acknowledgment de issues externas).
- **Polimorfismo `clause_type` discriminator + anti-uniformização
  MUST NOT:** canonical §4.1 (Output prose polimórfico + 4 exemplos),
  canonical §4.2 (tool description com anti-uniformização normativa),
  compact §5.1 e §5.2 (espelhos).
- **Citation chain do ADR-0002 amendment:** linhas precisas
  `fastmcp/tools/base.py:124,270` e
  `mcp/server/lowlevel/server.py:467,576` sob `fastmcp==3.2.4` pinado
  em `uv.lock`. Issues externas verificadas via web fetch: #4042
  IBM/mcp-context-forge, #654 modelcontextprotocol/typescript-sdk
  (ambas CLOSED com reconhecimento explícito no amendment de que
  patches downstream não invalidam tese estrutural).
- **Processo de cristalização da sessão #21:** `docs/learning-log.md`
  (entry 2026-05-17).

## Defaults arquiteturais consolidados pós-canonical-sync-B

Estado **realizado** (não plano em progresso). Referência canônica em
ADRs citadas.

**Da Fase 1 + Fase 1.5 (ADR-0005, ADR-0007, ADR-0008 amended):**
preservados verbatim do estado pós-#18; não recapitulados aqui para
brevidade. Ver entries de #16-#18 no learning-log.

**Da Fase 2 — Milestone A T01+T02a+sync-A+sync-A.2 (sessões #19-#20):**

- Cláusulas modeladas como Pydantic discriminated union
  `DefinitionalClause | SubstantiveClause` em `models.py` desde T01,
  reutilizadas em T02a sem refactor (validação cross-task).
- `tools.py` é módulo dedicado às pure functions tools; `server.py`
  carrega thin wrappers `@mcp.tool` delegando para `tools.<func>`.
- `ErrorEnvelope` Pydantic em `models.py` com docstring documentando
  Option B (alinhado com canonical §5.1 pós-canonical-sync-B).
- Convenção Option B materializada em quatro sítios coerentes pós-#21:
  `ErrorEnvelope.__doc__`, anchor test `test_documents_fastmcp_tool_call_shape`,
  canonical §5.1 + §5.3, ADR-0002 §3 amendment. Não há mais
  cross-doc debt entre código e spec sobre wire placement.
- Wire-shape FastMCP 3.2.4 empiricamente capturado:
  `fastmcp.Client(server.mcp).call_tool(name, args)` →
  `CallToolResult` com snake_case attrs; tool retorna dict → wire
  `isError=False` + `structuredContent=dict`; tool `raise ToolError(s)`
  → wire `isError=True` + `content[0].text=s` +
  `structuredContent=None`. Sem caminho público combinando ambos.
- Anchor tests permanecem como sinais de regressão para release
  futura de FastMCP que mude wrap: `test_documents_fastmcp_read_resource_shape`
  (T01, `test_bootstrap.py`); `test_documents_fastmcp_tool_call_shape`
  (T02a, `test_get_clause.py`).
- Pack POL-001..004 em
  `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/`
  é referência autorizada de fixture para T02b/T03 (consumo direto
  via `tmp_path` + `shutil.copytree`/`copy`, não estrutural-only).
  POL-000 vem do real, sem cópia.
- Patterns de fixture estabelecidos: `valid_policy_root` deep-copy do
  real; `policy_root_with_pack_clauses` extensão para POL-001 +
  POL-003 do pack; `reset_server_state` teardown padrão entre testes
  que invocam `_bootstrap`.

**Da Fase 2 — Milestone A canonical-sync-B (sessão #21):**

- **Polimorfismo polimorphic na superfície de retorno do componente.**
  `get_clause` retorna `DefinitionalClause | SubstantiveClause` via
  `model_dump(mode="json", exclude_none=True)`; campo `clause_type`
  discrimina substantive (carrega `applies_to`/`control`/`requirements`/
  `exceptions`) vs definitional (carrega `defines`/`out_of_scope`).
  `find_clauses_by_law_article` (T02b) retorna lista heterogênea
  polimórfica em `{clauses: [...]}` object-wrap; consumidores MUST
  NOT filtrar por `clause_type` para uniformizar.
- **Discriminador formal sucesso vs erro = presença de `errorCode`
  em `structuredContent`**, não wire `isError`. Sucesso carrega
  payload positivo sem `errorCode`; erro carrega envelope com
  `errorCode` populado. Wire `isError: true` reservado para falhas
  de protocolo MCP (parâmetro inválido no `inputSchema`, tool
  inexistente), produzidas pelo framework, não pelo componente.
- **Empty result, veredito `indeterminate`, e cláusula deprecated em
  `get_clause` não são erros.** Carregam `isError: false` SEM
  `errorCode`. Erros de domínio carregam `isError: false` COM
  `errorCode`. Apenas a presença de `errorCode` discrimina (canonical
  §5.3 reformulada).
- **Vocabulário operation canônico:** apenas `collection`, `storage`,
  `disclosure_by_transmission` e outros 19 tokens declarados em
  `policy/vocabularies/<framework>/operation.yaml` (per SCHEMA.md
  §9.2). Tokens deprecated do pré-canonical-sync-B (`store`,
  `transmit`) eliminados.
- **Vocabulário control MVP:** apenas `consent_required` ou
  `anonymization_required` (per SCHEMA.md §9.5 linhas 283-285).
  Evolução para objeto `{type, value}` deferida.

## Pre-flight pins para a sessão #22 (Chat — prep do prompt T02b)

Cinco itens load-bearing para deliberação antes de virar prompt
mecânico de Code.

1. **DD-T02b-1: helpers compartilhados de envelope.** T02b é o segundo
   consumidor de `_envelope_tool_result` + builders per-errorCode
   (`_invalid_clause_id_format`, `_clause_not_found` em `tools.py`
   privados). DD-6 de T02a registrou: extrair para módulo compartilhado
   quando segundo consumidor aterrissar — T02b é esse momento. Decisão
   #22: extrair para `tools/_envelope.py` agora ou manter inline em
   `tools.py` até T03 (cinco errorCodes adicionais) gerar pressão
   real? Inclinação prévia: **manter inline**. YAGNI aos quatro
   errorCodes atuais; T03 será o segundo gatilho que pode justificar
   extração. Brief T02b deve cobrar isso como DD de Fase 1, não
   silenciar.

2. **DD-T02b-2: modelagem do `specification` de input.** Três
   caminhos: (a) parâmetros nomeados na assinatura
   (`def find_clauses_by_law_article(lei, artigo, paragrafo=None,
   inciso=None, alinea=None)`) — FastMCP gera `inputSchema` MCP
   naturalmente; (b) Pydantic model dedicado em `models.py`
   (`FindClausesSpecification`) — mais rico mas exige investigar como
   FastMCP gera schema a partir disso; (c) dict com validação inline.
   Inclinação prévia: **(a)**, por simplicidade e por bater com o stub
   já em `server.py:125-152`. Brief T02b confirma na Fase 1.

3. **DD-T02b-3: lista heterogênea polimórfica como invariante de
   implementação.** Canonical §4.2 carrega `consumers MUST NOT filter
   or coerce by clause_type to uniformize` como invariante de
   protocolo. Brief T02b deve registrar como invariante de
   implementação: algoritmo de matching prefix-hierarchical não filtra
   por `clause_type`, nenhum refactor futuro pode "limpar" a lista.
   Candidato a AS de teste explícito (e.g., AS-6 cobrindo busca por
   Art. 5 retornando POL-000 definitional + alguma substantive
   simultaneamente).

4. **AS-2 fixtures sintéticas para prefix-hierarchical.** Pack
   POL-001..004 não cobre prefix-hierarchical — todas as cláusulas
   do pack têm inciso/parágrafo populado. T02b precisa de fixtures
   sintéticas inline em `test_find_clauses.py` via `_write_yaml` no
   `tmp_path` para exercitar AS-2: duas cláusulas, uma com
   `{lei: LGPD, artigo: 5}`-only (sem inciso), outra com
   `{lei: LGPD, artigo: 5, inciso: 1}`. Busca `{lei: LGPD, artigo: 5,
   inciso: 1}` (mais específica que o stored sem inciso) retorna **só**
   a segunda; busca `{lei: LGPD, artigo: 5}` retorna **ambas**. Brief
   T02b deve dizer explicitamente "criar fixtures sintéticas inline".

5. **Pré-leitura obrigatória durante Fase 1 do prompt T02b:**
   - `docs/tasks.md` T02b inteira (Função, Dependências, Files, AS,
     Gate).
   - `docs/specs/policy-reader/canonical.md` §4.2 inteiro (semântica
     prefix-hierarchical é prosa, não tabela — pós-canonical-sync-B
     é seguro consumir).
   - `docs/specs/policy-reader/canonical.md` §5.1, §5.3, §5.4
     (`INVALID_LAW_IDENTIFIER`: validation, non-retryable,
     `details: {provided, accepted_values}`; `accepted_values` dinâmico
     do header carregado).
   - `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/README.md`
     seção "Assimetrias deliberadas" — load-bearing: AS-2 não coberto
     pelo pack.
   - `src/mcp_servers/policy_reader/tools.py` e `models.py` para
     entender o que existe pós-T02a (não duplicar; reusar).
   - Preview de prompt T02b redigido em #21 (anexado ao chat em sessão
     anterior) — carrega 60% do framing.

## Pendências cross-sessão (organizado por horizonte de resolução)

**Resolver na #22 (Chat — prep do prompt T02b):**

- Cinco pre-flight pins acima.
- Rascunho do prompt T02b com Fase 1 (leitura + plano com gate de
  OK) + Fase 2 (implementação com gates pytest/ruff/mypy) +
  guard-rails. Esqueleto reusa estrutura do prompt T01/T02a com 60%
  herdado do preview em #21.

**Resolver em sessão Code #23+ (T02b execução):**

- Implementação completa de `find_clauses_by_law_article` em
  `tools.py` (segunda função pública; thin wrapper em `server.py`
  delegando) + `INVALID_LAW_IDENTIFIER` builder de envelope em
  `tools.py` (privado, decisão DD-T02b-1) + testes em
  `test_find_clauses.py` (AS-1 a AS-5 + possivelmente AS-6 polimórfico
  heterogêneo) + fixtures sintéticas inline para AS-2.
- Gate task-level ADR-0008 §3: pytest verde, ruff verde, mypy verde,
  Chat review independente em sessão separada.

**Resolver pós-T02b:**

- **T03** (`check_applicability`) — quatro vereditos +
  provenance trinque + escopo MVP via `not_applicable` para
  `operation ≠ collection` (ADR-0007). Pré-implementação consome pack
  POL-001..004 completo.
- **T04** (`policy://vocabularies` + framework swap) — exercita
  framework-awareness via consumo dinâmico do vocabulário carregado.

**Resolver em janela futura sem urgência:**

- **DX residual:** linters (ruff, mypy) como dev deps oficiais em
  `pyproject.toml`. Workaround atual via `uvx ruff` e `uv run --with
  mypy mypy` funciona. Sessão Code curta (~15min).
- **Itens deferidos T03** (já listados em `tasks.md` §Companion edits):
  `operation`/`legal_basis` vs `operation_type`/`declared_legal_basis`;
  `evidence` vs `reason` em `not_applicable`. Resolver pós-T03 quando
  spec for empiricamente validado.
- **Cosméticos diferidos do round 5 review de canonical-sync-B:**
  Finding 6.1 (ADR caracterização `_make_error_result` poderia
  enumerar 4 call sites em vez de 3 — schema input, return type,
  schema output, exception genérica do tool); Findings 7.1, 7.2
  (wordsmithing das descrições de issues externas no amendment);
  Finding 9 (POL-005 placeholder em §4.2 exemplo Art. 5
  semanticamente contrived). Todos cosméticos. Viajam com próxima PR
  que tocar respectivo arquivo.

**Resolver em prep de Milestone B (canonical-sync-C ou análoga):**

- **Drift análogo no template `docs/specs/_template.md`** — linha
  107 ainda carrega `### 5.3 Casos que parecem erro mas não são`
  (título antigo de policy-reader §5.3, agora renomeado para
  "Discriminador formal entre sucesso e erro"). Template precisa de
  sync.
- **Drift análogo no semgrep-runner spec** —
  `docs/specs/semgrep-runner/canonical.md` linha 283 ainda usa título
  antigo análogo; spec inteira do semgrep-runner não foi migrada para
  Option B. Trigger natural: prep de Milestone B (semgrep-runner
  implementation) deliberará canonical-sync-C que propaga amendment
  §3 para essa spec também.
- **Decisão Semgrep-on-Windows** (Docker, pip native, remote worker,
  CI-only) — afeta forma de Milestone B; antecede decomposição
  formal.
- **Decomposição formal de Milestone B** em sessão Chat dedicada.

**Resolver após gate milestone-level de Milestone A:**

- **Decomposição formal de Milestone C** (pipeline multi-agente) e
  **Milestone D** (CI/CD + validação empírica) em sessões Chat
  dedicadas, sequencialmente.

## Hashes da sessão #21 (audit trail interno)

PR #38 (`feat/canonical-sync-B`) mergeada em main via squash. Hashes
sobrevivem ao squash apenas via este registro interno:

- `5926a03` — `feat(canonical-sync-B): align canonical+compact+ADR-0002
  to Option B and empirical clause shape`. 3 arquivos, +445 / -87.
  13 edits originais + 3 patches de exaustividade durante apply.
- `1bbc6fe` — `fix(canonical-sync-B): close exhaustiveness drift caught
  by independent review`. 4 patches do Chat review pós-commit
  (Findings 2.1, 8, 11, 7.3).
- `<TBD>` — squash hash final em main. Preenchido após merge via
  `git log main --oneline | head -1`.