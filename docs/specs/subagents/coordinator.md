# Coordinator (Python main loop)

**Tipo.** Python main loop — não AgentDefinition. Cada etapa do
pipeline é uma chamada `query()` do `claude-agent-sdk` cujo
`ClaudeAgentOptions` declara `system_prompt=SUBAGENT_SYSTEM_PROMPT`
direto, sem `agents={}` e sem dispatch via Agent tool (decisão
Coordinator A'' / sessão #38, refinamento sobre A' inicial / sessão
#37). Subagente é o main agent dessa query; pattern alinha
literalmente com prompt chaining (D1.6 do exam guide canônico).

**Status.** Skeleton v2 (sessão #38, pós-round-trip de quatro rounds
de review). Substitui drafts skeleton-37 (sessão #37) e skeleton-38
(primeira passagem sessão #38) sob A'' (pattern refinado) + (b2)
(subagentes mantêm acesso direto a `policy://vocabularies` per
ADR-0005 Decision 4) + **quíntupla canônica** de configuração do
lockdown agent CI/CD-headless (`system_prompt` + `allowed_tools` +
`permission_mode="dontAsk"` + `setting_sources=[]` + `strict_mcp_config=True`)
+ **quatro camadas de enforcement** materializando D2.3 scoped access.
Flesh completo após specs dos 5 subagentes redigidas em ordem
Reporter → Triager → Detector → Classifier → Matcher (sessão #38+).

**Pendência metodológica.** Cinco decisões load-bearing de Milestone
C serão ratificadas em ADR-0012 retroativo (sessão futura
pós-coordinator-flesh):

- Divergência de método contra `docs/specs/_template.md` (preâmbulo
  §inicial, sentença sobre derivação de `_template-subagent.md`):
  template como hipótese de trabalho destilado no Reporter-flesh, não
  autorado upfront.
- Não-uso de ADR-0003 dual canonical+compact: subagent specs são
  comportamentais (contract surface), não wire format MCP, e já são
  compact-sized 1-2 páginas.
- Pattern A'' (system_prompt direto, sem AgentDefinition); decisão
  #38 sobre #37 A'.
- Caminho (b2) para `policy://vocabularies` access: subagentes
  carregam diretamente via `ReadMcpResourceTool`, coordinator não
  pré-carrega; preserva ADR-0005 Decision 4 textbook case (com
  nuance de granularidade per-server discutida em §3.3).
- Quíntupla canônica + quatro camadas de enforcement como pattern
  arquitetural do lockdown agent CI/CD-headless (defense candidate
  forte D2.3).

Número ADR-0012 fica reservado pendente PR `chore/sync-adr-references`
removendo refs stale "ADR-0012" em `docs/milestoneB.md` (linhas 50,
102, 106, 107, 112, 114) + triagem caso-a-caso em
`docs/learning-log.md` (forward refs legítimas a "ADR-0012 retroativo
Milestone C" preservadas; refs stale para Windows-stdio E-2 absorvido
em ADR-0011 substituídas por "ADR-0011").

**Companion edit arch-overview pendente** (three-beats em §10): patch
único — `docs/architecture-overview.md` §3 mermaid substitui
`T -->|skip| END[Sem ação]` por `T -->|skip| R[Reporter]`.

**Gate pré-coordinator-flesh** (§11): smoke-test residual de
`ToolUseBlock.input` attribute shape para custom tools — único item
load-bearing não-resolvido via doc canônica.

## 1. Responsabilidade

Orquestrar sequência fixa de cinco subagentes (Triager → Detector →
Classifier → Matcher → Reporter); injetar estado entre etapas inline
no prompt da próxima query; gravar scratchpad como audit/provenance/CI
artifact; capturar Report final via inspeção do tool result stream
do Reporter.

## 2. Arquitetura de execução

Coordinator não é AgentDefinition. É script Python que executa cinco
chamadas sequenciais `query()` do `claude-agent-sdk`. Em cada
chamada, `ClaudeAgentOptions` declara a **quíntupla canônica do
lockdown agent CI/CD-headless**:

| Campo | Função | Tipo |
|---|---|---|
| `system_prompt` | Define o role do main agent daquela query | str |
| `allowed_tools` | Allowlist (auto-approval); tools listadas auto-aprovadas | list[str] |
| `mcp_servers` | Dict explícito de servers MCP disponíveis ao subagente | dict |
| `permission_mode` | `"dontAsk"` — tools fora do allowlist são DENIED outright | str |
| `setting_sources` | `[]` — SDK isolation; bloqueia auto-load de filesystem settings (`.mcp.json`, user config, plugins) | list |
| `strict_mcp_config` | `True` — ortogonal a `setting_sources`; ignora especificamente `.mcp.json` + user MCP + plugin MCP servers | bool |

Quíntupla pode soar redundante mas as quatro últimas linhas são
ortogonais sob falha — ver §6 quatro camadas de enforcement.

Não há `agents={}`, não há AgentDefinition, não há Agent tool
dispatch. Cada subagente é o main agent da sua própria query; pattern
é prompt chaining estrito (D1.6 do exam guide canônico).

Trade-off A' vs A'' registrado em learning-log #38: A' (AgentDefinition
+ Agent tool dispatch) paga custo de surface SDK sem usar o benefício
(dispatch só compensa quando o main agent escolhe entre múltiplos
subagentes). A'' elimina indireção, reduz error propagation surface
(um modo de falha por etapa, não dois) e reduz token cost por etapa
(sem main-agent reasoning + dispatch overhead).

Restrição arquitetural do SDK confirmada em
`docs.claude.com/en/docs/agent-sdk/subagents`: *"Subagents cannot
spawn their own subagents. Don't include `Agent` in a subagent's
`tools` array."* Sob A'', a restrição não toca o desenho (não há
subagent spawn em jogo), mas confirma que coordinator-como-Python
permanece arquiteturalmente correto.

**Nota terminológica.** Tool de dispatch foi renomeada de `Task` para
`Agent` em Claude Code v2.1.63. Exam guide ainda usa "Task tool";
documentação canônica corrente usa "Agent tool". Sob A'', nenhum dos
dois nomes aparece em `allowed_tools` do coordinator porque não há
dispatch.

## 3. Workflow

Cada etapa segue protocolo idêntico: (a) coordinator monta prompt
injetando output da etapa anterior serializado JSON inline;
(b) dispatch `query()` com `ClaudeAgentOptions` configurada para
aquela etapa (quíntupla canônica completa); (c) captura final message
do subagente; (d) valida payload via Pydantic; (e) grava
`NN-<etapa>.json` no scratchpad; (f) avalia branching para próxima
etapa.

### §3.0 Initialization

Parse `.mcp.json` com whitelist `EXPECTED_SERVERS` (ver §6 Camada 1);
gera `run_id` (UUID v4); cria `.scratchpad/run-<id>/`; valida env
vars opcionais (`POLICY_READER_ROOT`, `SEMGREP_RUNNER_ROOT`,
`SEMGREP_RUNNER_TIMEOUT_SECONDS`) e usa fallbacks CWD-relative
quando ausentes.

**Sob (b2), coordinator NÃO carrega `policy://vocabularies`.**
Classifier e Matcher consomem o resource diretamente via
`ReadMcpResourceTool` em suas respectivas queries, conforme ADR-0005
Decision 4 (Resource vs Tool textbook case): `policy://vocabularies`
é shared resource; `get_clause`, `find_clauses_by_law_article`,
`check_applicability` são tools exclusivas do Matcher.

### §3.1 Etapa 1 — Triager

```python
async for msg in query(
    prompt=build_triager_prompt(pr_metadata),
    options=ClaudeAgentOptions(
        system_prompt=TRIAGER_SYSTEM_PROMPT,
        tools=["Read", "Glob"],
        allowed_tools=["Read", "Glob"],
        mcp_servers={},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
    ),
):
    ...
```

Output Pydantic-validado, gravado em `01-triager.json`.

Branching:
- `decision == "skip"` → coordinator pula §3.2-§3.4 e segue direto
  para §3.5 (Reporter) com input mínimo carregando `skip_reason` no
  metadata. Reporter é invocado normalmente (preserva
  arch-overview §4.3 "Reporter como único locus emissor").
- `decision == "proceed"` → coordinator segue para §3.2.

### §3.2 Etapa 2 — Detector

```python
async for msg in query(
    prompt=build_detector_prompt(pr_metadata, triager_output),
    options=ClaudeAgentOptions(
        system_prompt=DETECTOR_SYSTEM_PROMPT,
        tools=["Read"],
        allowed_tools=["Read", "mcp__semgrep-runner__scan_diff"],
        mcp_servers={"semgrep-runner": SEMGREP_RUNNER_CONFIG},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
    ),
):
    ...
```

Output Pydantic-validado, gravado em `02-detector.json`.

Sem branching condicional: zero candidatos é caso válido
(`findings: []` propaga ao Classifier → Matcher → Reporter; Reporter
formata Report final sem invenção de campo discriminador no
coordinator).

### §3.3 Etapa 3 — Classifier

```python
async for msg in query(
    prompt=build_classifier_prompt(detector_output),
    options=ClaudeAgentOptions(
        system_prompt=CLASSIFIER_SYSTEM_PROMPT,
        tools=["Read", "Grep"],
        allowed_tools=[
            "Read",
            "Grep",
            "ListMcpResourcesTool",    # listar resources de policy-reader
            "ReadMcpResourceTool",     # ler policy://vocabularies
        ],
        mcp_servers={"policy-reader": POLICY_READER_CONFIG},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
    ),
):
    ...
```

System_prompt instrui: *"Use `ReadMcpResourceTool` with `server='policy-reader'`
and `uri='policy://vocabularies'` to load the jurisdictional vocabulary
at start of session. Use loaded vocabularies to constrain `operation_type`,
`data_categories`, and `declared_legal_basis` values when extracting
`structured_context` from candidates."*

Output Pydantic-validado, gravado em `03-classifier.json`.

**Nota sobre scoped access — granularidade per-server, não
per-resource.** SDK Python expõe acesso a resources MCP via duas
tools genéricas built-in: `ListMcpResourcesTool` e `ReadMcpResourceTool`,
ambas tomando `server` como argumento. Implicação para a fronteira
"Classifier descreve, Matcher julga":

- **Preservado em capability:** Classifier é impedido pela whitelist
  `allowed_tools` (sob `permission_mode="dontAsk"`) de invocar
  `mcp__policy-reader__check_applicability`,
  `mcp__policy-reader__get_clause`, ou
  `mcp__policy-reader__find_clauses_by_law_article` — tools que
  emitem veredict ou retornam cláusulas substantivas.
- **Acesso lateral a outros resources:** `ReadMcpResourceTool` aceita
  qualquer `uri` do server registrado em `mcp_servers={...}`. Classifier
  consegue ler também `policy://catalog` e `policy://schema-version`,
  além do `vocabularies` designado pelo system_prompt. Defensável
  porque resources são read-only context (sem decisional capability):
  Classifier pode "ver" catálogo de cláusulas e versão do schema, mas
  não pode emitir veredict nem retornar conteúdo cláusula-specific
  (que vem de `get_clause`, restricted to Matcher).

Princípio ADR-0005 Decision 4 (Resource vs Tool) preservado em **nível
de capability** (Classifier não tem decisional power); granularidade
de scoping no SDK Python é per-server-via-built-in-tools (uma
`ReadMcpResourceTool` gate per server). Documentar nuance em ADR-0012
retroativo.

Sem branching: pipeline prossegue mesmo com candidatos parcialmente
classificáveis; campos nulos em `structured_context` são válidos per
RF-003 (extração que falha em mapear ao vocabulário resulta em null,
não em invenção).

### §3.4 Etapa 4 — Matcher

```python
async for msg in query(
    prompt=build_matcher_prompt(classifier_output),
    options=ClaudeAgentOptions(
        system_prompt=MATCHER_SYSTEM_PROMPT,
        tools=["Read"],
        allowed_tools=[
            "Read",
            "ListMcpResourcesTool",    # listar resources de policy-reader
            "ReadMcpResourceTool",     # ler policy://vocabularies
            "mcp__policy-reader__check_applicability",
            "mcp__policy-reader__get_clause",
            "mcp__policy-reader__find_clauses_by_law_article",
        ],
        mcp_servers={"policy-reader": POLICY_READER_CONFIG},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
    ),
):
    ...
```

Output Pydantic-validado, gravado em `04-matcher.json`.

Trinca de provenance (`policy_schema_version`, `policy_version`,
`legal_framework`) preservada verbatim por finding (RF-009 +
garantia β do SDR — decisão sessão #37). Matcher carrega
`policy://vocabularies` via `ReadMcpResourceTool` no startup do
prompt (mesmo mecanismo do Classifier) e invoca as três tools de
ação para emitir veredicts.

### §3.5 Etapa 5 — Reporter

```python
async for msg in query(
    prompt=build_reporter_prompt(matcher_output_or_skip),
    options=ClaudeAgentOptions(
        system_prompt=REPORTER_SYSTEM_PROMPT,
        tools=["Read"],
        allowed_tools=["Read", "mcp__reporter_tools__emit_report"],
        mcp_servers={"reporter_tools": reporter_sdk_server},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
    ),
):
    # AssistantMessage carrega ToolUseBlocks. Stream pode conter
    # múltiplos ToolUseBlocks antes do emit_report — tool search está
    # ON por default no SDK (confirmado empiricamente smoke-test #38),
    # e injeta ToolUseBlock de ToolSearch antes do tool real. Filter
    # por block.name garante captura do payload correto, ignorando
    # blocks intermediários audit-only.
    if hasattr(msg, "content") and msg.content:
        for block in msg.content:
            if isinstance(block, ToolUseBlock) and \
               block.name == "mcp__reporter_tools__emit_report":
                report_payload = block.input  # ratificado smoke-test #38
                ...
```

Onde `reporter_sdk_server` é instância de `create_sdk_mcp_server`
(ver §7).

Halt-condition: ausência de invocação de `emit_report` no stream
completo da query do Reporter → `ReportNotEmitted` erro estruturado.
Enforcement via inspeção Python do message stream **filtrando por
`block.name`** ao longo de todos os `AssistantMessage` recebidos,
não via hook PostToolUse (decisão sessão #37, ratificada #38; hook
seria belt-and-suspenders sobre tool authorization, que já garante
exclusividade do Reporter sobre `emit_report` via whitelist sob
`dontAsk`). Filter por `name` é necessário porque tool search no SDK
injeta `ToolUseBlock`s de `ToolSearch` no stream antes do tool real
(confirmado smoke-test #38; ver §8 — Tool search habilitação
confirmada empiricamente).

Halt-condition aplica uniformemente: tanto path normal
(Matcher → Reporter) quanto skip path (Triager skip → Reporter com
`skip_reason`) requerem invocação de `emit_report` antes da
terminação da query. Coordinator deve consumir o stream até
`ResultMessage` (signal de término) acumulando filtered match; não
retornar no primeiro `ToolUseBlock` qualquer.

### §3.6 Termination

Coordinator retorna Report payload (capturado em §3.5 via
`block.input` da `ToolUseBlock`) ao caller — GitHub Action (Milestone
D) ou exercise script (gate milestone-level). Scratchpad permanece
em disco como audit artifact; política de retenção/cleanup a decidir
em §8.

## 4. State passing

Output da etapa N → string JSON serializada → inline no prompt da
etapa N+1. Scratchpad é **audit-only** (decisão S2', sessão #37):
gravação em disco pelo coordinator após cada etapa, sem leitura pelos
subagentes. Subagentes não têm `Read` sobre `.scratchpad/`.

Justificativa de evolução: se outputs intermediários crescerem o
suficiente para inflar prompts (Detector > N candidatos com snippets
grandes), pivô para S2-com-Read é refactor pequeno — coordinator
passa path em vez de conteúdo + subagente ganha `Read` escopado
(via `allowed_tools=["Read"]` cuja autorização já existe; mudança
fica em prompt + scratchpad layout). Reversibilidade preservada por
construção.

## 5. Error handling e propagation

Cenários estruturados que o coordinator trata:

- **Pydantic validation falha** em output do subagente → halt; emite
  erro estruturado com etapa, payload bruto recebido, erro Pydantic
  (exception: `SubagentValidationFailed`).
- **MCP server retorna envelope de erro** durante `query()` →
  propaga; coordinator decide retry (transient: `SCAN_TIMEOUT`,
  `SEMGREP_EXECUTION_FAILED`) vs halt (validation/business/
  non-transient) por errorCode, conforme retryability table de
  `policy-reader`/`semgrep-runner`.
- **Triager `decision: "skip"`** → não-erro; branching para §3.5
  direto com input mínimo (ver §3.1).
- **Detector retorna zero candidatos** → não-erro; pipeline prossegue
  normalmente até §3.5 com `findings: []` propagando.
- **Reporter não invocou `emit_report`** → `ReportNotEmitted` erro
  estruturado; enforcement via inspeção do message stream em Python,
  não via PostToolUse hook.
- **`.mcp.json` declara server fora do whitelist `EXPECTED_SERVERS`**
  → halt no startup com erro estruturado (`CoordinatorStartupError`;
  ver §6).
- **Subagente retorna texto não-JSON** → mesmo path de Pydantic
  validation falha.
- **Subagente não responde / timeout / connection error** →
  `SubagentUnresponsive` erro estruturado; coordinator decide retry
  (transient) vs halt conforme política.
- **Subagente retorna resposta vazia** (sem text block, sem
  tool_use) → mesmo path de Pydantic validation falha (payload bruto
  = "").
- **Múltipla invocação de `emit_report` na mesma query do Reporter**
  → decisão deferida para Reporter-flesh; opções: primeira vence +
  warn, última vence, halt + erro estruturado. Inclinação: halt
  (anti-pattern não deveria ocorrer; sinaliza bug em system_prompt
  do Reporter).
- **`ToolUseBlock` sem `.input` attribute** (defensivo, edge case de
  SDK version incompat) → `MalformedToolUseBlock` erro estruturado;
  sugere versão de SDK abaixo do mínimo da Provisão MC-E.
- **Stream contém `ToolUseBlock`s intermediários não-`emit_report`**
  (ex: `ToolSearch` injetado pelo SDK quando tool search está ON,
  confirmado empiricamente smoke-test #38) → comportamento esperado,
  não-erro; coordinator filtra por `block.name` e ignora blocks
  intermediários audit-only. Stream completo permanece audit trail
  implícito (logs internos do `query()`).

**Contrato de exceções estruturadas do coordinator** (forward refs
ao módulo de implementação; detalhamento da taxonomia de errorCodes
fica para flesh completo):

| Exception | Quando | Recoverable |
|---|---|---|
| `CoordinatorStartupError` | `.mcp.json` whitelist falha, env vars inválidas, scratchpad criação falha | Não |
| `SubagentValidationFailed` | Pydantic falha em output do subagente | Não (no MVP) |
| `SubagentUnresponsive` | Timeout/connection error em `query()` | Sim (transient) |
| `ReportNotEmitted` | Reporter terminou query sem invocar `emit_report` | Não |
| `MalformedToolUseBlock` | `ToolUseBlock` sem campos esperados | Não (sinaliza SDK incompat) |

**Nota sobre nomenclatura de envelope de erro MCP.** SDK Python usa
`is_error: True` (snake_case) no envelope; SDK TypeScript usa
`isError: true` (camelCase). FastMCP wire format usa camelCase
(`isError`) conforme convenção MCP protocol. Implementação Python do
coordinator e do `emit_report` retornam `is_error: True` quando
sinalizam erro estruturado ao caller; recepção lê de campo
correspondente do envelope MCP. Débito de housekeeping catalogado:
verificar se FastMCP servers existentes (`policy-reader`,
`semgrep-runner`) usam convenção correta — sessão Code dedicada
~20-30min (catalogado em `docs/tasks.md` §Companion edits).

## 6. `.mcp.json` consumption — quatro camadas de enforcement

`.mcp.json` no root do repo é single source of truth para configuração
de MCP servers (decisão M2 / sessão #37). Dual-consumer: Claude Code
CLI nativamente em desenvolvimento local + coordinator Python em
runtime via parsing controlado.

**Coordinator não confia em auto-load do SDK.** SDK Python carrega
`.mcp.json` automaticamente quando `setting_sources` é None (default)
porque o source `"project"` está habilitado por padrão. Pattern
seguro adotado neste projeto materializa **quatro camadas de
enforcement ortogonais**:

```python
# Camada 1 — coordinator parseia .mcp.json com whitelist em runtime
EXPECTED_SERVERS = {"policy-reader", "semgrep-runner"}

mcp_config_raw = json.load(open(".mcp.json"))
declared_servers = set(mcp_config_raw.get("mcpServers", {}).keys())
unexpected = declared_servers - EXPECTED_SERVERS
if unexpected:
    raise CoordinatorStartupError(
        f"Unexpected MCP servers in .mcp.json: {unexpected}"
    )
mcp_servers_dict = {
    name: mcp_config_raw["mcpServers"][name]
    for name in declared_servers
    if name in EXPECTED_SERVERS
}

# Camadas 2-4 — aplicadas em cada ClaudeAgentOptions de §3.1-§3.5
options = ClaudeAgentOptions(
    system_prompt=...,
    allowed_tools=[...],
    mcp_servers=mcp_servers_dict,  # de Camada 1
    permission_mode="dontAsk",     # Camada 4
    setting_sources=[],            # Camada 2a
    strict_mcp_config=True,        # Camada 2b
)
```

**Defense candidate D2.3 — scoped access via tool distribution +
SDK isolation.** Quatro camadas falham de modo diferente e protegem
contra modos de falha distintos:

| Camada | Mecanismo | Modo de falha protegido |
|---|---|---|
| **C1** | Coordinator parseia `.mcp.json` + whitelist `EXPECTED_SERVERS` | Dev adicionou server por motivo Claude Code (debugger MCP, proxy dev) e esqueceu de remover → halt no startup |
| **C2a** | `setting_sources=[]` no `ClaudeAgentOptions` | SDK auto-load de filesystem settings (`.mcp.json` via source `"project"`, user CLAUDE.md, local settings) injetando server não-whitelisted → desabilitado por construção |
| **C2b** | `strict_mcp_config=True` (ortogonal a C2a) | Plugin MCP servers ou user MCP injetando server fora do whitelist via path não-coberto por `setting_sources` → ignorados |
| **C3** | `allowed_tools=[...]` per-etapa | Subagente em runtime decide auto-aprovar tool fora do escopo → só listadas auto-aprovam |
| **C4** | `permission_mode="dontAsk"` | Tool fora do allowlist tenta fall-through para `canUseTool` (não definido em headless) → denied outright, não suspended |

C2a e C2b são **ortogonais**: `setting_sources=[]` desabilita TODOS
os filesystem settings (incluindo `.claude/agents/`, `CLAUDE.md`,
slash commands, etc.); `strict_mcp_config=True` desabilita
especificamente MCP injection vinda de `.mcp.json` + user MCP +
plugin MCP. Belt-and-suspenders: cobrem paths distintos.

C3 (allowlist) e C4 (denial) também ortogonais: C3 garante que tools
designadas auto-aprovam (não param o pipeline esperando aprovação);
C4 garante que tools não-designadas são denied (não param o pipeline
esperando `canUseTool` callback que não existe).

AS de teste correspondente em task futura de implementação do
coordinator:
- (a) Carrega só whitelisted: dado `.mcp.json` com 2 servers
  whitelisted, então `mcp_servers={...}` propagado às queries contém
  exatamente esses 2.
- (b) Fail loud em server não-whitelisted: dado `.mcp.json` com
  server fora do whitelist, então `CoordinatorStartupError` emitido +
  halt antes de qualquer query.
- (c) Camada 2 + 4 enforce no SDK: dado teste com configuração
  ambiente simulando user-settings injeção, verificar que server
  injetado não aparece em runtime e que tool fora do allowlist é
  denied (não suspended).

Schema do `.mcp.json` é convenção do Claude Code CLI; coordinator
empresta a config. Env vars opcionais (`POLICY_READER_ROOT`,
`SEMGREP_RUNNER_ROOT`, `SEMGREP_RUNNER_TIMEOUT_SECONDS`) só declaradas
quando coordinator precisa de roots não-default (teste de substituição
de framework GDPR; rule-set override em CI). Run "normal" usa
fallbacks CWD-relative.

## 7. `emit_report` custom tool

Definida em `src/coordinator/tools.py` via `@tool` decorator do
`claude-agent-sdk`, agrupada em `create_sdk_mcp_server`:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("emit_report", "Emit the consolidated Report JSON", REPORT_SCHEMA)
async def emit_report(args):
    # Dual sink:
    # 1. Grava 99-report.json no scratchpad
    write_report_to_scratchpad(args)
    # 2. Retorna ack via tool result; coordinator captura payload via
    #    ToolUseBlock.input no message stream (ver §3.5), não via return
    return {"content": [{"type": "text", "text": "Report emitted"}]}
    # Erro: return {"content": [{"type": "text", "text": "..."}],
    #                "is_error": True}

reporter_sdk_server = create_sdk_mcp_server(
    name="reporter_tools",      # underscore preventivo (G4 / sessão #38)
    version="0.1.0",
    tools=[emit_report],
)
```

Schema input validado Pydantic. **Dual sink** — explicitação de
captura:

1. Handler `emit_report` grava `99-report.json` no scratchpad
   (audit/CI artifact). Primeira via.
2. Coordinator captura payload via inspeção do message stream:
   localiza `ToolUseBlock` com `name == "mcp__reporter_tools__emit_report"`,
   extrai `block.input` que contém os argumentos exatos passados
   pelo modelo à tool — isto é o payload do Report (ver §3.5).
   Segunda via, canônica para retorno ao caller.
3. **`return` do handler é canal de signaling ao modelo**, não canal
   de captura do payload. Retorna ack simples (sucesso) ou
   `is_error: True` (erro de validação intra-handler). Coordinator
   ignora o return value; só inspeciona `ToolUseBlock.input` do
   message stream.

Esclarecimento load-bearing (corrige inconsistência do skeleton #38):
**`ToolUseBlock.input` é o canal canônico de captura**, não
`ToolResultBlock.content`. Razão: `block.input` é o que o modelo
**emitiu** como argumentos ao tool — payload do Report agregado;
`ToolResultBlock` carrega o que o handler **retornou** para o modelo
— ack ou erro de signaling. O coordinator quer o payload, não o ack.

**Tool authorization.** Exposta apenas via
`allowed_tools=["Read", "mcp__reporter_tools__emit_report"]` na query
do Reporter (§3.5). Outras queries do pipeline (§3.1-§3.4) não
incluem `reporter_tools` em `mcp_servers={...}` e não autorizam
`mcp__reporter_tools__emit_report` em `allowed_tools`. Sob
`permission_mode="dontAsk"` (C4), tentativa de invocação por outro
subagente seria denied outright. Restrição arquitetural materializada
em três camadas (C2 + C3 + C4); falharia para Reporter emitir e
outras etapas não poderem.

**Nota sobre tool naming.** Padrão oficial documentado em
`code.claude.com`: *"The key in mcpServers becomes the {server_name}
segment in each tool's fully qualified name: mcp__{server_name}__{tool_name}."*
Tool resolve via chave do dict `mcp_servers={...}`, não via campo
`name=` declarado em `create_sdk_mcp_server`. Underscore preventivo
em `"reporter_tools"` (em ambos: chave do dict e `name=` do server)
elimina risco de parser do SDK interpretar mal hyphens em triple-pattern
`mcp__<name>__<tool>`. Servers existentes `policy-reader` e
`semgrep-runner` mantêm hyphen (empiricamente validados em Milestones
A+B); migração para underscore é deferimento, não escopo MVP (ver §8).

## 8. Evoluções previstas

- **Adoção formal de `claude-agent-sdk` como dependência.** PR
  dedicado `chore/add-claude-agent-sdk-dependency` antes de
  coordinator-flesh: `pyproject.toml` + `uv.lock` ganham
  `claude-agent-sdk >=0.1.59` (mínimo para `setting_sources=[]`
  suportado; idealmente latest stable disponível). ADR-0001 (stack
  canônica) recebe amendment registrando adição. Não bloqueia
  redação de specs de subagente; bloqueia início de implementação
  (T11+).

- **SDR como serializador downstream (pattern β).** Report JSON é
  artefato canônico do sistema multi-agente. Transformação Report →
  SDR CSV (append, audit governance LGPD Art. 37) é responsabilidade
  de consumer downstream (GitHub Action ou job de governança
  independente), não do sistema multi-agente. Três garantias de
  design no MVP preservam compatibilidade: (i) superset de campos do
  `structured_context` propagados verbatim por finding; (ii) audit
  metadata top-level (`report_id`, `report_emitted_at`); (iii)
  separação Reporter ↔ serializadores externos. Decisão sessão #37.

- **Cleanup do scratchpad.** Política de retenção (delete pós-run?
  preservar última N runs? rotação por idade?) a decidir conforme
  uso empírico em Milestone D + benchmark.

- **Cascading inheritance de stdio em sub-processes.** Catalogado em
  ADR-0011; relevante se subagentes via SDK herdarem handles do
  coordinator no Windows. Não detectado empiricamente em #34-#35;
  ratchet futuro se reaparecer.

- **Migração hyphen → underscore em server names.** `policy-reader`
  e `semgrep-runner` mantêm hyphen no MVP por compat com
  Milestones A+B já validados; nuance de naming convention é
  housekeeping deferido condicional. **Pivô vira obrigatório se**
  G4 smoke-test eventual (ou teste de integração no Reporter-flesh+)
  detectar bug latente em `allowed_tools` resolution. Provisão MC-F
  potencial: PR `chore/migrate-server-names-underscore` se evidência
  empírica materializar.

- **Evolução para A' (AgentDefinition + Agent dispatch) ou A (main
  agentic).** Se evolução futura introduzir paralelização (Detector
  + Classifier em paralelo) ou roteamento dinâmico (main agent
  escolhe entre múltiplos subagent candidates), pivô para A'
  (AgentDefinition por etapa + Agent dispatch) ou A (main agentic
  orquestrando via `agents={...}`). A'' atual (system_prompt direto)
  acomoda RF-008 sem refactor. Não-MVP.

- **CI/CD via `--strict-mcp-config` flag CLI.** Em Milestone D,
  coordinator pode rodar com `--strict-mcp-config` apontando para
  config dedicada (e.g., `.github/mcp-ci.json`), blindando contra
  interferência de configs locais do GitHub Actions runner.
  Equivalente CLI ao `strict_mcp_config=True` programático. Considerar
  na decomposição de Milestone D.

- **`WaitForMcpServers` tool** (v2.1.142+; aparece apenas quando tool
  search está OFF). Relevante se coordinator precisar lidar com
  delay de conexão de MCP servers no startup (e.g., `policy-reader`
  carregando Política grande). Anti-pattern atual: confiar em
  conexão sync; pivô para `WaitForMcpServers` em `allowed_tools` se
  empiricamente necessário. Não-MVP.

- **Tool search habilitação confirmada empiricamente.** Smoke-test
  #38 (SDK 0.2.87) ratificou que tool search está ON por default
  mesmo com pipeline de poucas tools (1 tool no smoke-test, caso
  degenerate; nosso pipeline usa 4-6 por etapa). Implicação
  operacional: stream do subagente contém `ToolUseBlock`s de
  `ToolSearch` antes da tool real; filter por `block.name` em §3.5
  é o que sustenta captura correta. Tool search NÃO precisa estar
  em `allowed_tools` — é mecanismo interno do SDK, não tool
  agent-invocable. Deferment: avaliar empiricamente em Milestone D
  (benchmark ~200 snippets) se overhead de tool search introduz
  latência sensível em ratio token cost vs throughput. Pivô para
  tool search OFF possível via opção SDK se overhead detectado.

## 9. Cross-references

**Source-of-truth artifacts:**
- `docs/REQUIREMENTS.md` — RFs cobertas em Milestone C: RF-003 pleno,
  RF-004 pleno, RF-005 pleno, RF-006, RF-007 pleno, RF-008 pleno
  + RF-009.
- `docs/architecture-overview.md` §3 (fluxo de execução; **patch
  pendente — ver §10**), §4.3 (sistema multi-agente), §5 (subagentes
  detalhados — §5.4 Classifier e §5.5 Matcher mantêm acesso direto a
  `policy://vocabularies` per ADR-0005 Decision 4; sem patches sob
  (b2)), §5.7 (matriz tools × subagentes — sem patches sob (b2)).
- `docs/tasks.md` Milestone C — capability statement + RFs + gate
  milestone-level placeholder.
- `docs/specs/policy-reader/canonical.md` §3.3 (consumidores
  autorizados de `policy://vocabularies`: Matcher + Classifier).

**ADRs aplicáveis:**
- ADR-0001 (stack canônica; **amendment pendente** registrando
  adição de `claude-agent-sdk` como dep nova de Milestone C — ver §8)
- ADR-0002 (MCP conventions; §Decision 5 three-beats lifecycle)
- ADR-0005 (multi-client / framework-agnostic; §Decision 4 textbook
  case Resource vs Tool — preservado em capability sob (b2);
  granularidade per-server-via-built-in-tools documentada como
  nuance em ADR-0012)
- ADR-0008 (task decomposition e verification)
- ADR-0011 (Windows-stdio handle inheritance; cascading risk)
- **ADR-0012 retroativo Milestone C** (a redigir; cobre divergências
  metodológicas + decisões load-bearing A'', (b2), M2, S2', dual
  sink emit_report, quíntupla canônica, quatro camadas de enforcement
  D2.3; **citação pendente PR `chore/sync-adr-references`** removendo
  refs stale ADR-0012 → ADR-0011 em `docs/milestoneB.md` e triagem
  em `docs/learning-log.md`).

**Specs dos subagentes:**
- `docs/specs/subagents/reporter.md` — **primeira a redigir; destila
  `_template-subagent.md`** (ordem híbrida sessão #37)
- `docs/specs/subagents/triager.md` (sanity check pós-Reporter)
- `docs/specs/subagents/detector.md`
- `docs/specs/subagents/classifier.md`
- `docs/specs/subagents/matcher.md`
- (coordinator-flesh-completo após as 5 specs)

**Convenções de cross-reference** (anti-drift rules, ratificadas
sessão #37):

1. Workflow vive APENAS aqui (§3). Specs de subagente citam
   `coordinator.md §3.<N>`; nunca duplicam.
2. Capability vive APENAS em REQUIREMENTS.md. Specs citam `RF-<N>`;
   nunca redefinem critério.
3. Error handling pattern vive APENAS aqui (§5). Specs citam; nunca
   redescrevem mecânica.
4. Schema de tools/resources MCP vive APENAS em `docs/specs/<server>/`.
   Specs citam canonical §<N>.
5. Specs de subagente só referenciam contrato I/O entre si, nunca
   comportamento interno.
6. **§3 (Output)** de cada subagent spec é canonical I/O boundary
   que downstream cita verbatim — nunca paráfrase, nunca redefinição.

## 10. Companion edit arch-overview (three-beats)

Patch único pendente em `docs/architecture-overview.md`, derivado da
decisão de halt-condition caminho (i) da sessão #37:

**§3 Fluxo mermaid.** Substituir
`T -->|skip| END[Sem ação]` por
`T -->|skip| R[Reporter]`. Reflete decisão "Reporter sempre invocado"
(caminho i / sessão #37); preserva §4.3 "Reporter como único locus
emissor" sob substituição do mermaid que originalmente sugeria
coordinator emitindo em skip path.

**Patches removidos vis-à-vis skeleton #37.** Decisão (b2) da sessão
#38 elimina dois patches anteriormente catalogados:

- ~~§5.1 — Coordinator com acesso a `policy://vocabularies`~~ — NÃO
  aplica sob (b2); coordinator não acessa o resource.
- ~~§5.7 — Matriz ganha linha coordinator com ✓ em
  `policy://vocabularies`~~ — NÃO aplica sob (b2).

**Status three-beats** (per ADR-0002 §Decision 5 + ADR-0003):
- Beat 1 (proposed): patch §3 mermaid proposto em sessão #37
  (caminho i da halt-conditions deliberation), mantido sob (b2) na
  sessão #38; patches §5.1 e §5.7 propostos em #37 foram eliminados
  em #38.
- Beat 2 (applied): pendente sessão Code curta de companion edit
  arch-overview (target pós-Reporter-flesh).
- Beat 3 (verified): pendente review independente Chat pós-aplicação.

Three-beats persiste pós-aplicação como audit trail (per ADR-0002
§Decision 5).

## 11. Gates pré-coordinator-flesh

Smoke-test residual obrigatório antes de coordinator-flesh-completo
ser autorado (sessão Chat #39+) e antes de tasks T11+ serem
implementadas. Sessão Code curta dedicada ~10-15min.

**Gate 1 — `ToolUseBlock.input` attribute shape para custom tools.**

**Status: PASS** (smoke-test sessão Code #38; SDK
`claude-agent-sdk==0.2.87`; script tracked em
`scripts/smoke_tests/sdk_tooluseblock_shape/` com README).

Confirmações empíricas:
- `ToolUseBlock` em `claude_agent_sdk.types`; surface mínima é
  exatamente 3 atributos: `id`, `name`, `input` (sem
  `parent_tool_use_id` no nível do block — consistente com A''
  ausência de nested subagent spawn).
- `block.input` é dict com chaves correspondentes aos parâmetros
  declarados via `@tool` decorator; valores são args exatos
  passados pelo modelo.
- Quíntupla canônica (`dontAsk` + `setting_sources=[]` +
  `strict_mcp_config=True` + `allowed_tools` whitelist + `mcp_servers`
  dict) ratificada como side effect do mesmo teste (TC2).
- Underscore naming (`mcp__test_tools__echo`) resolve sem quirks
  (TC3).

Achado adicional empírico (AC1 do reporting): tool search está ON
por default no SDK 0.2.87; stream do subagente pode conter
`ToolUseBlock`s intermediários (ex: `ToolSearch` com
`{'query': 'select:mcp__test_tools__echo', 'max_results': 1}`)
antes do tool real. Filter por `block.name` em §3.5 sustenta captura
correta. Documentado em §3.5 (comentário inline + rationale de
halt-condition) + §5 (caso de error handling não-erro) + §8 (item
"Tool search habilitação confirmada empiricamente").

Achado adicional empírico (AC2 do reporting): tipos de message no
stream — `SystemMessage`, `RateLimitEvent`, `AssistantMessage` (carrega
`ToolUseBlock`), `UserMessage` (tool result injection back to model),
`ResultMessage` (signal de término). Coordinator inspeciona ao menos
`AssistantMessage` (para captura) e `ResultMessage` (para
terminação); demais tipos são audit trail.

**Critério Fail (não-materializado; preservado como audit trail
forward-looking).** Se TC1 tivesse falhado: atributo tem nome
diferente (`.arguments`, `.params`, `.tool_input`, etc.). Surgical
edit em §3.5 e §7 do skeleton para ajustar nome do atributo. Provisão
MC-G aberta se Fail (não aberta; pattern padrão `.input` confirmado).

Custo de Fail teria sido trivial (~5min surgical edit). Custo de
não-rodar teria sido: descobrir bug em Reporter-flesh ou em primeira
execução do pipeline (caro de retornar). Ratchet barato preveniu
ambos.

**Decisões fora do escopo deste gate** (documentadas como deferments):
- G4 hyphen-vs-underscore em server names existentes — deferred
  condicional (ver §8); ratchet futuro se bug latente materializar.
- `is_error`/`isError` em FastMCP servers existentes — débito de
  housekeeping catalogado em `docs/tasks.md` §Companion edits.
- `WaitForMcpServers` necessidade — pendente uso empírico (ver §8).
- Tool search ON quirk com poucas tools — pendente uso empírico
  (ver §8).

**Resolução por web search durante sessão Chat #38** (não-gates):
- Quíntupla canônica do lockdown agent (`dontAsk` + `setting_sources=[]`
  + `strict_mcp_config=True`) confirmada via doc canônica
  `platform.claude.com/docs/en/agent-sdk/permissions` e
  `platform.claude.com/docs/en/agent-sdk/mcp`.
- `ListMcpResourcesTool` + `ReadMcpResourceTool` (com sufixo `Tool`)
  como nomes corretos confirmados via tools-reference oficial.
- Restrição "subagents cannot spawn subagents" confirmada via
  `docs.claude.com/en/docs/agent-sdk/subagents`.
- Tool renaming `Task` → `Agent` em Claude Code v2.1.63 confirmado
  via mesma fonte.

Gates pré-flesh são honestidade epistêmica: design proposta em Chat
sob inferência arquitetural sobre SDK requer ratchet empírico para
claims não-cobertas por doc canônica antes de virar contrato. Defense
candidate forte para Capítulo de Método: pattern dual-validation
Chat-external (web) + Code-internal (repo) + Code-empirical (smoke-test)
materializado em sessão #38 sobre design proposals do #37.