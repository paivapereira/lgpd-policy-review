# Coordinator (Python main loop)

**Tipo.** Python main loop — não AgentDefinition. Cada etapa do pipeline é uma chamada `query()` do `claude-agent-sdk` cujo `ClaudeAgentOptions` declara `system_prompt=SUBAGENT_SYSTEM_PROMPT` direto, sem `agents={}` e sem dispatch via Agent tool (decisão Coordinator A'' / sessão #38, refinamento sobre A' inicial / sessão #37). Subagente é o main agent dessa query; pattern alinha literalmente com prompt chaining (D1.6 do exam guide canônico).

**Status.** Spec completa (flesh MC-A, sessão #50). Os contratos técnicos (quíntupla canônica §2, factory `create_reporter_server` §7, Pattern A'' §2, quatro camadas de enforcement §6) estão no corpo. Histórico de derivação do skeleton (drafts #37/#38, reflow, ratificações) vive no learning-log; decisões load-bearing de Milestone C em ADR-0012 (já autorado).

**Gate pré-coordinator-flesh** (§11): smoke-test residual de `ToolUseBlock.input` attribute shape para custom tools — único item load-bearing não-resolvido via doc canônica.

## 1. Responsabilidade

Orquestrar sequência fixa de cinco subagentes (Triager → Detector → Classifier → Matcher → Reporter); injetar estado entre etapas inline no prompt da próxima query; gravar scratchpad como audit/provenance/CI artifact; capturar Report final via inspeção do tool result stream do Reporter.

## 2. Arquitetura de execução

Coordinator não é AgentDefinition. É script Python que executa cinco chamadas sequenciais `query()` do `claude-agent-sdk`. Em cada chamada, `ClaudeAgentOptions` declara a **quíntupla canônica do lockdown agent CI/CD-headless** (5 elementos de denial-on-miss), juntamente com `system_prompt` (role definition, separado) e `tools` (context restriction; eixo ortogonal — ver nota abaixo):

| Campo | Função | Categoria | Tipo |
|---|---|---|---|
| `permission_mode` | `"dontAsk"` — tools fora do allowlist são DENIED outright | quíntupla (denial-on-miss) | str |
| `setting_sources` | `[]` — SDK isolation; bloqueia auto-load de filesystem settings (`.mcp.json`, user config, plugins) | quíntupla (denial-on-miss) | list |
| `strict_mcp_config` | `True` — ortogonal a `setting_sources`; ignora especificamente `.mcp.json` + user MCP + plugin MCP servers | quíntupla (denial-on-miss) | bool |
| `allowed_tools` | Allowlist (auto-approval); tools listadas auto-aprovadas | quíntupla (denial-on-miss) | list[str] |
| `mcp_servers` | Dict explícito de servers MCP disponíveis ao subagente | quíntupla (denial-on-miss) | dict |
| `system_prompt` | Define o role do main agent daquela query | role definition (separado da quíntupla) | str |
| `tools` | `[]` no Reporter (PR #67; `emit_report` é server tool, visível via `mcp_servers`). **Matcher e Classifier listam `ReadMcpResourceTool`/`ListMcpResourcesTool`** — built-ins de resource governados por este campo; `[]` ou lista sem eles os esconde e quebra o read de resource (#48-b; §10 DD-9.1). Remove built-ins do contexto do modelo. | context restriction (eixo ortogonal) | list[str] |

Os cinco elementos da quíntupla são ortogonais sob falha — ver §6 quatro camadas de enforcement.

**Distinção load-bearing entre denial-on-miss e availability** (ratificada em Reporter spec §1.4 + §1.5, sessão #42). A quíntupla materializa **denial-on-miss**: invocações de tool fora do `allowed_tools` são denied outright sob `permission_mode="dontAsk"`. `tools` opera em eixo **ortogonal de availability**: `tools=[]` remove built-ins do contexto do modelo, evitando que o modelo tente invocá-los. Issue #361 da SDK Python documenta o gap: *"It [allowed_tools] does not remove tools from Claude's toolset"*. Defesa em profundidade requer ambos os eixos. Evidência empírica em `scripts/smoke_tests/sdk_tools_empty_list/` (Gate 6, PR #67).

Não há `agents={}`, não há AgentDefinition, não há Agent tool dispatch. Cada subagente é o main agent da sua própria query; pattern é prompt chaining estrito (D1.6 do exam guide canônico).

Trade-off A' vs A'' registrado em learning-log #38: A' (AgentDefinition + Agent tool dispatch) paga custo de surface SDK sem usar o benefício (dispatch só compensa quando o main agent escolhe entre múltiplos subagentes). A'' elimina indireção, reduz error propagation surface (um modo de falha por etapa, não dois) e reduz token cost por etapa (sem main-agent reasoning + dispatch overhead).

Restrição arquitetural do SDK confirmada em `docs.claude.com/en/docs/agent-sdk/subagents`: *"Subagents cannot spawn their own subagents. Don't include `Agent` in a subagent's `tools` array."* Sob A'', a restrição não toca o desenho (não há subagent spawn em jogo), mas confirma que coordinator-como-Python permanece arquiteturalmente correto.

**Nota terminológica.** Tool de dispatch foi renomeada de `Task` para `Agent` em Claude Code v2.1.63. Exam guide ainda usa "Task tool"; documentação canônica corrente usa "Agent tool". Sob A'', nenhum dos dois nomes aparece em `allowed_tools` do coordinator porque não há dispatch.

## 3. Workflow

Cada etapa segue protocolo idêntico: (a) coordinator monta prompt injetando output da etapa anterior serializado JSON inline; (b) dispatch `query()` com `ClaudeAgentOptions` configurada para aquela etapa (quíntupla canônica completa); (c) captura final message do subagente; (d) valida payload via Pydantic; (e) grava `NN-<etapa>.json` no scratchpad; (f) avalia branching para próxima etapa.

### §3.0 Initialization

Carrega a config de MCP via `src/coordinator/config.py` (single-source; ver §6 Camada 1): o módulo parseia `.mcp.json` com whitelist `EXPECTED_SERVERS`, expõe `mcp_servers_dict` e os slices nomeados `POLICY_READER_CONFIG = mcp_servers_dict["policy-reader"]` e `SEMGREP_RUNNER_CONFIG = mcp_servers_dict["semgrep-runner"]` (as âncoras `*_CONFIG` que §3.2–§3.4 usam); gera `run_id` (UUID v4); cria `.scratchpad/run-<id>/`; instancia `reporter_sdk_server = create_reporter_server(run_path, run_id)` (factory de `src/subagents/reporter/tools.py`; reuso desta instância em §3.5 stage Reporter); valida env vars opcionais (`POLICY_READER_ROOT`, `SEMGREP_RUNNER_ROOT`, `SEMGREP_RUNNER_TIMEOUT_SECONDS`) e usa fallbacks CWD-relative quando ausentes.

**Sob (b2), coordinator NÃO carrega `policy://vocabularies`.** Classifier e Matcher consomem o resource diretamente via `ReadMcpResourceTool` em suas respectivas queries, conforme ADR-0005 Decision 4 (Resource vs Tool textbook case): `policy://vocabularies` é shared resource; `get_clause`, `find_clauses_by_law_article`, `check_applicability` são tools exclusivas do Matcher.

**Logging/observabilidade (decisão deste flesh; reporter §8.4 a delegou aqui).** O coordinator emite log **estruturado em stderr**; **stdout é reservado ao payload do Report** (capturado em §3.6, consumido pelo caller CI em modo `-p` headless — poluir stdout quebraria a captura). Eventos mínimos do MVP: no startup, `run_id`; por stage, uma linha de transição (`stage.start`) e uma de resultado (`stage.result` com `subtype`, `stop_reason`); no halt, a exceção tipada com seus campos (`stage`; quando aplicável `errorCode`/`isRetryable`). O scratchpad (`NN-<stage>.json`, §4) permanece como **audit trail de replay**; stderr é o **trace de execução**. Campos alinhados ao envelope `CoordinatorError` (§3.6). Design completo de observabilidade (níveis, sinks externos, correlação de runs) é Milestone D.

### §3.0bis Driver dos stages Branch B

Os quatro stages Branch B (Triager, Detector, Classifier, Matcher) compartilham o mesmo spine de captura/discriminação; só os **deltas** variam (output model, scratchpad, hook de tool, verificação de passthrough). O spine vive **aqui** (anti-drift rule #3: mecânica de erro só em §5/§3.0bis, nunca duplicada nos corpos §3.1–§3.4). Invariantes travados empiricamente em `scripts/smoke_tests/sdk_l2_capture/RESULTS.md` (#50): emissão de `ResultMessage` precede o raise (→ `last_result` é capturável); `refusal` discrimina por `stop_reason` (o `subtype` vem `'success'` sob refusal — não confiar nele); nunca discriminar pela string da exceção; sem `break` (eventos trailing).

```python
async def run_branch_b_stage(
    *,
    stage: str,
    prompt: str,
    options: ClaudeAgentOptions,            # delta por stage (corpo em §3.1-§3.4)
    output_model: type[BaseModel],          # delta: TriagerDecision / DetectorOutput / ...
    scratchpad_name: str,                   # delta: "01-triager.json" / ...
    on_tool_result=None,                    # delta: so Detector (inspecao scan_diff, §3.2)
    verify_passthrough=None,                # delta: so Classifier (1:1); None no Triager e no Matcher (G6)
    upstream=None,                          # delta: output do stage anterior p/ verify_passthrough
) -> BaseModel:
    log.info("stage.start", extra={"run_id": run_id, "stage": stage})
    last_result: ResultMessage | None = None
    try:
        async for msg in query(prompt=prompt, options=options):
            if on_tool_result is not None:
                on_tool_result(msg)         # Detector: scan_diff errorCode -> pode levantar DetectorScanFailed
            if isinstance(msg, ResultMessage):
                last_result = msg           # SEM break: eventos trailing (ex. prompt_suggestion)
            # demais tipos (SystemMessage/RateLimitEvent/UserMessage): audit, log-and-continue
    except DetectorScanFailed:
        raise                               # erro de tool ja tipado pelo hook; nao mascarar
    except Exception as e:
        if last_result is None:
            raise CoordinatorStreamFailure(stage=stage) from e
        # senao: exit deliberado pos-result (is_error=True); last_result e autoritativo

    if last_result is None:
        raise CoordinatorStreamFailure(stage=stage)        # caminho sem excecao tambem
    log.info("stage.result", extra={"run_id": run_id, "stage": stage,
                                     "subtype": last_result.subtype,
                                     "stop_reason": last_result.stop_reason})
    if last_result.stop_reason == "refusal":               # PRECEDE subtype (mente: 'success')
        raise SubagentRefusedTask(stage=stage)
    match last_result.subtype:
        case "error_max_turns" | "error_max_budget_usd":
            raise SubagentUnresponsive(stage=stage)
        case "error_during_execution":
            raise SubagentExecutionError(stage=stage)
        case "error_max_structured_output_retries":
            raise SubagentValidationFailed(stage=stage)
        case "success":
            try:
                obj = output_model.model_validate(last_result.structured_output)
            except ValidationError as ve:
                raise SubagentValidationFailed(stage=stage, raw=last_result.structured_output) from ve
            if verify_passthrough is not None:
                verify_passthrough(obj, upstream)          # Classifier (1:1); None no Matcher (G6) e Triager
            write_scratchpad(scratchpad_name, obj)         # §4
            return obj
        case other:
            raise SubagentExecutionError(stage=stage, detail=f"unexpected subtype {other!r}")
```

O `match subtype` casa as tabelas §6.3 dos quatro subagentes (incl. `error_max_budget_usd → SubagentUnresponsive`, detector/triager §6.3). As exceções estão na tabela §5. **`verify_passthrough` por stage:** Triager `None` (1º stage, sem upstream); Detector `None` (constrói de `scan_diff`, não de upstream Branch B); Classifier presente (1:1 posicional, classifier §4.3); Matcher **`None` no MVP** — a verificação coordinator-side de ordem/completude é follow-up explícito (matcher §3.5/AC-M8: a ordem não é garantia estrutural), ratificada como diferida na decisão #2.

### §3.1 Etapa 1 — Triager

```python
triager_out = await run_branch_b_stage(
    stage="triager",
    prompt=build_triager_prompt(pr_metadata),
    output_model=TriagerDecision,
    scratchpad_name="01-triager.json",
    options=ClaudeAgentOptions(
        system_prompt=TRIAGER_SYSTEM_PROMPT,
        tools=["Read", "Glob"],
        allowed_tools=["Read", "Glob"],
        mcp_servers={},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
        output_format={"type": "json_schema", "schema": TriagerDecision.model_json_schema()},
        max_turns=20,                   # Triager spec v0.1.0 §1.5 calibracao provisional
    ),
)
```

Validação, discriminação (subtype × stop_reason) e escrita do scratchpad ficam no driver §3.0bis. A nota de tolerância a tipos não-padrão no stream (RateLimitEvent etc.) move-se para §3.0bis (vale para todos os stages, não só Triager).

Branching:
- `decision == "skip"` → coordinator pula §3.2-§3.4 e segue direto para §3.5 (Reporter) com input mínimo carregando `skip_reason` no metadata. Reporter é invocado normalmente (preserva arch-overview §4.3 "Reporter como único locus emissor").
- `decision == "proceed"` → coordinator segue para §3.2.

### §3.2 Etapa 2 — Detector

```python
detector_out = await run_branch_b_stage(
    stage="detector",
    prompt=build_detector_prompt(pr_metadata, triager_out),
    output_model=DetectorOutput,
    scratchpad_name="02-detector.json",
    on_tool_result=inspect_scan_diff_result,   # §5: errorCode em structuredContent (Option B) -> isRetryable -> DetectorScanFailed
    options=ClaudeAgentOptions(
        system_prompt=DETECTOR_SYSTEM_PROMPT,
        tools=["Read"],
        allowed_tools=["Read", "mcp__semgrep-runner__scan_diff"],
        mcp_servers={"semgrep-runner": SEMGREP_RUNNER_CONFIG},
        permission_mode="dontAsk",
        setting_sources=[],
        strict_mcp_config=True,
        output_format={"type": "json_schema", "schema": DetectorOutput.model_json_schema()},
        max_turns=30,                   # detector §1.4 (aritmetica 2+N)
    ),
)
```

O coordinator desempacota o `DetectorOutput`: `findings` → Classifier (§3.3); `provenance` (`ScanProvenance`) → `02-detector.json` **e** ao estado consolidado do Reporter (§3.5), per reporter.md §3 `scan_provenance` (C2). `inspect_scan_diff_result` é o backstop coordinator-side do erro de tool **específico do Detector** (§5); os demais stages não têm hook análogo — ver nota de assimetria em §5.

Sem branching condicional: zero candidatos é caso válido (`findings: []` propaga ao Classifier → Matcher → Reporter; Reporter formata Report final propagando verbatim o `run_outcome` pré-computado pelo coordinator a partir de estado observável (DD-1.2 V2); Reporter não inventa nem reclassifica discriminador).

### §3.3 Etapa 3 — Classifier

```python
classifier_out = await run_branch_b_stage(
    stage="classifier",
    prompt=build_classifier_prompt(detector_out.findings),
    output_model=ClassifierOutput,
    scratchpad_name="03-classifier.json",
    verify_passthrough=verify_classifier_passthrough,   # 1:1 posicional vs list[DetectorFinding] (classifier §4.3)
    upstream=detector_out.findings,
    options=ClaudeAgentOptions(
        system_prompt=CLASSIFIER_SYSTEM_PROMPT,
        # ReadMcpResourceTool/ListMcpResourcesTool are built-ins governed by the
        # `tools` field (availability), NOT by mcp_servers/allowed_tools. The
        # Classifier reads policy://vocabularies via ReadMcpResourceTool at
        # startup; under a non-empty `tools` without them the model cannot see
        # the built-in and the vocabulary load fails — emitting non-canonical
        # tokens that break the Matcher's consent comparison (#48-b; §10 DD-9.1).
        tools=["Read", "Grep", "ReadMcpResourceTool", "ListMcpResourcesTool"],
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
        output_format={
            "type": "json_schema",
            "schema": ClassifierOutput.model_json_schema(),
        },
        max_turns=20,                   # classifier §1.5 (provisional, MC-D)
    ),
)
```

`verify_classifier_passthrough` é zip por índice: candidato *i* preserva `{file, line, rule_id, snippet, surrounding_context}` do finding *i*; divergência → `SubagentContractViolation` (§5). 1:1 é legítimo aqui (Classifier não muda cardinalidade) — assimetria deliberada vs Matcher (§3.4).

System_prompt instrui: *"Use `ReadMcpResourceTool` with `server='policy-reader'` and `uri='policy://vocabularies'` to load the jurisdictional vocabulary at start of session. Use loaded vocabularies to constrain `operation_type`, `data_categories`, and `declared_legal_basis` values when extracting `structured_context` from candidates."*

Output Pydantic-validado, gravado em `03-classifier.json`.

**Nota sobre scoped access — granularidade per-server, não per-resource.** SDK Python expõe acesso a resources MCP via duas tools genéricas built-in: `ListMcpResourcesTool` e `ReadMcpResourceTool`, ambas tomando `server` como argumento. Implicação para a fronteira "Classifier descreve, Matcher julga":

- **Preservado em capability:** Classifier é impedido pela whitelist `allowed_tools` (sob `permission_mode="dontAsk"`) de invocar `mcp__policy-reader__check_applicability`, `mcp__policy-reader__get_clause`, ou `mcp__policy-reader__find_clauses_by_law_article` — tools que emitem veredict ou retornam cláusulas substantivas.
- **Acesso lateral a outros resources:** `ReadMcpResourceTool` aceita qualquer `uri` do server registrado em `mcp_servers={...}`. Classifier consegue ler também `policy://catalog` e `policy://schema-version`, além do `vocabularies` designado pelo system_prompt. Defensável porque resources são read-only context (sem decisional capability): Classifier pode "ver" catálogo de cláusulas e versão do schema, mas não pode emitir veredict nem retornar conteúdo cláusula-specific (que vem de `get_clause`, restricted to Matcher).

Princípio ADR-0005 Decision 4 (Resource vs Tool) preservado em **nível de capability** (Classifier não tem decisional power); granularidade de scoping no SDK Python é per-server-via-built-in-tools (uma `ReadMcpResourceTool` gate per server). Documentar nuance em ADR-0012 retroativo.

**Caveat de availability (≠ capability).** O scoping per-server acima é sobre *capability* (qual resource o built-in alcança). É ortogonal à *availability* do built-in: registrar o server em `mcp_servers` concede o alcance, mas `ReadMcpResourceTool`/`ListMcpResourcesTool` só entram no contexto do modelo se estiverem no campo `tools` (#48-b; §10 DD-9.1). Por isso o `tools` do Classifier (§3.3) e do Matcher (§3.4) lista os dois built-ins explicitamente — `allowed_tools` pré-aprova mas não controla availability (Issue #361).

Sem branching: pipeline prossegue mesmo com candidatos parcialmente classificáveis; campos nulos em `structured_context` são válidos per RF-003 (extração que falha em mapear ao vocabulário resulta em null, não em invenção).

### §3.4 Etapa 4 — Matcher

```python
matcher_out = await run_branch_b_stage(
    stage="matcher",
    prompt=build_matcher_prompt(classifier_out),
    output_model=MatcherOutput,
    scratchpad_name="04-matcher.json",
    # verify_passthrough OMITIDO no MVP (G6 / decisao #2): a verificacao coordinator-side
    # de ordem/completude do sweep candidato x clausula e follow-up — matcher §3.5/AC-M8
    # declaram que a ordem NAO e garantia estrutural (depende do LLM enumerar), e o
    # finding-unico de curto-circuito (matcher §4.3) torna blocos de tamanho variavel.
    # Trazer ao MVP exigiria emenda ratificada a matcher.md.
    options=ClaudeAgentOptions(
        system_prompt=MATCHER_SYSTEM_PROMPT,
        # Gate 6 (tools=[]) is correct for the Reporter — emit_report is a server
        # tool, visible via mcp_servers — but WRONG for the Matcher: the check-all
        # reads policy://catalog via ReadMcpResourceTool, a built-in governed by
        # the `tools` field. tools=[] hides it and breaks the check-all
        # (#48-b; §10 DD-9.1 finding). List the resource built-ins explicitly.
        tools=["Read", "ReadMcpResourceTool", "ListMcpResourcesTool"],
        allowed_tools=[
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
        output_format={                 # enum-tag finding schema (Matcher spec §3.3 / DD-M13)
            "type": "json_schema",
            "schema": MatcherOutput.model_json_schema(),
        },
        max_turns=30,                   # check-all is call-heavy: ~N×(C+1) calls (Matcher spec §4.2 / DD-M14)
    ),
)
```

Trinca de provenance preservada verbatim por finding (RF-009); ver matcher §3.1. `len(findings) ≥ candidates_count` (DD-M6, sem invariante de igualdade).

Trinca de provenance (`policy_schema_version`, `policy_version`, `legal_framework`) preservada verbatim por finding (RF-009 + garantia β do SDR — decisão sessão #37). Matcher carrega `policy://vocabularies` via `ReadMcpResourceTool` no startup do prompt (mesmo mecanismo do Classifier) e invoca as três tools de ação para emitir veredicts.

### §3.5 Etapa 5 — Reporter

> **Proveniência top-level do estado consolidado.** A trinca `policy_schema_version`/
> `policy_version`/`legal_framework` do nível superior do Report é **derivada dos
> `findings`** (o header da Política echoado verbatim por cada veredito do Matcher via
> `check_applicability`, policy-reader AS-6), **não** de um parâmetro com default —
> mantendo-a igual à trinca per-finding por construção (intra-handler cross-check #2 do
> `emit_report`, reporter.md §3.3). `run_pipeline` usa os parâmetros `policy_*` apenas como
> **fallback** nos caminhos sem findings (`skipped_by_triager` / `success_no_candidates`),
> onde não há finding de onde derivar e o cross-check #2 é vácuo. Impl: `_effective_provenance`
> (`run.py`); regressão em `tests/coordinator/test_provenance_derivation.py`.

```python
final_result: ResultMessage | None = None
emit_report_seen = False
report_payload: dict | None = None

# try/except wrap: SDK pode emitir ResultMessage E levantar exceção
# na mesma execução (AC-5 #38b empirical). Preservar final_result
# capturado antes do raise permite discriminação tri-axial pós-loop;
# sem final_result, é falha de stream genuína.
try:
    async for msg in query(
        prompt=build_reporter_prompt(matcher_output_or_skip),
        options=ClaudeAgentOptions(
            system_prompt=REPORTER_SYSTEM_PROMPT,
            tools=[],                      # PR #67 Gate 6: remove built-ins do contexto
            allowed_tools=["mcp__reporter_tools__emit_report"],
            mcp_servers={"reporter_tools": reporter_sdk_server},
            permission_mode="dontAsk",
            setting_sources=[],
            strict_mcp_config=True,
            max_turns=3,                   # DD-10.4: retry budget; aritmética canônica em Reporter spec §1.5
        ),
    ):
        if isinstance(msg, ResultMessage):
            final_result = msg
        # AssistantMessage carrega ToolUseBlocks. Filter por block.name
        # garante captura do payload correto, ignorando blocks
        # intermediários audit-only. Sob tools=[] (per Gate 6 / PR #67),
        # ToolSearch é skipped — modelo dispõe dos 3 turns inteiros
        # (initial emit + até 2 retries; ver Reporter spec §1.5). O
        # filter passa a ser defesa preventiva contra futuros built-in
        # tool blocks intermediários introduzidos por versões posteriores
        # do SDK, não defesa contra ToolSearch ativo (ratificado em
        # Reporter spec §6.7 + §10.5 item 6 / sessão #42).
        if isinstance(msg, AssistantMessage) and msg.content:
            for block in msg.content:
                if isinstance(block, ToolUseBlock) and \
                   block.name == "mcp__reporter_tools__emit_report":
                    if emit_report_seen:
                        raise MultipleReportEmissions(
                            first_payload=report_payload,
                            second_payload=block.input,
                        )
                    emit_report_seen = True
                    report_payload = block.input  # ratificado smoke-test #38
except Exception as exc:
    # SDK may yield ResultMessage and raise (AC-5 #38b empirical).
    # If we captured final_result, fall through to discrimination;
    # otherwise, this is a stream-level failure.
    if final_result is None:
        raise CoordinatorStreamFailure(stage="reporter") from exc

# DD-10.4 V3 — discriminação tri-axial:
# denials → subtype → emit_report_seen.
denials = (final_result.permission_denials or []) if final_result else []
if denials:                                  # estrito (decisao #1): qualquer denial sob lockdown = anomalia de integridade
    raise ReporterPermissionDenied(
        denials=denials,
        subtype=final_result.subtype if final_result else None,
    )

if final_result and final_result.subtype == "error_max_turns":
    raise ReporterTurnsExhausted(
        num_turns=final_result.num_turns,
        errors=final_result.errors,
    )

if not emit_report_seen:
    raise ReportNotEmitted(
        subtype=final_result.subtype if final_result else None,
    )

# Success path: report_payload populated; coordinator returns to
# caller (§3.6).
```

Onde `reporter_sdk_server` é instância de `create_sdk_mcp_server` (ver §7).

Halt-condition: ausência de invocação de `emit_report` no stream completo da query do Reporter → `ReportNotEmitted` erro estruturado. Enforcement via inspeção Python do message stream **filtrando por `block.name`** ao longo de todos os `AssistantMessage` recebidos, não via hook PostToolUse (decisão sessão #37, ratificada #38; hook seria belt-and-suspenders sobre tool authorization, que já garante exclusividade do Reporter sobre `emit_report` via whitelist sob `dontAsk`). Filter por `name` é defesa preventiva contra futuros built-in tool blocks intermediários introduzidos por versões posteriores do SDK; sob `tools=[]` corrente (PR #67), ToolSearch é skipped, mas o filter permanece para robustness (ratificado em Reporter spec §6.7 + §10.5 item 6 / sessão #42).

No caminho normal, o coordinator injeta no estado consolidado do Reporter — ao lado de `run_outcome`, `summary`, `scope` — também a `scan_provenance` (de `DetectorOutput.provenance`, §3.2; per `reporter.md` §3, C2); ela é **ausente** no skip path (sem Detector, logo sem scan). Halt-condition aplica uniformemente: tanto path normal (Matcher → Reporter) quanto skip path (Triager skip → Reporter com `skip_reason`) requerem invocação de `emit_report` antes da terminação da query. Coordinator deve consumir o stream até `ResultMessage` (signal de término) acumulando filtered match; não retornar no primeiro `ToolUseBlock` qualquer.

### §3.6 Termination

O coordinator retorna ao caller (GitHub Action / exercise script) um **`CoordinatorResult`** — união discriminada no boundary externo:

```python
@dataclass
class CoordinatorReport:                 # caminho de sucesso
    payload: dict                        # ReportPayload capturado de emit_report (§3.5)

@dataclass
class CoordinatorError:                  # qualquer halt do pipeline
    cause: Exception                     # excecao tipada de §5 (DetectorScanFailed | SubagentRefusedTask | ...)
    stage: str                           # blame (toda excecao ja carrega)
    coverage_gap: str                    # anotacao humana do que nao foi analisado

CoordinatorResult = CoordinatorReport | CoordinatorError
```

O main entry envolve o pipeline num try/except de topo: sucesso → `CoordinatorReport(payload)`; qualquer exceção tipada de §5 → `CoordinatorError(cause, stage, coverage_gap)`. O `run_outcome="error"` que as specs mencionam **mapeia para `CoordinatorError`**, distinto de `ReportPayload.run_outcome` (que segue 4 tokens de sucesso, reporter §3.1). Para `DetectorScanFailed`, `coverage_gap` é "cobertura zero — scan não rodou" (`scan_diff` é all-or-nothing, detector §8.2), **não** "resultado parcial". Scratchpad permanece em disco como audit artifact. **Forma provisional:** campos ricos de audit (ex. `partial_scratchpad_path`) deferem para Milestone D, quando o contrato da GitHub Action e a retenção do scratchpad (§8) forem desenhados.

## 4. State passing

Output da etapa N → string JSON serializada → inline no prompt da etapa N+1. Scratchpad é **audit-only** (decisão S2', sessão #37): gravação em disco pelo coordinator após cada etapa, sem leitura pelos subagentes. Subagentes não têm `Read` sobre `.scratchpad/`.

Justificativa de evolução: se outputs intermediários crescerem o suficiente para inflar prompts (Detector > N candidatos com snippets grandes), pivô para S2-com-Read é refactor pequeno — coordinator passa path em vez de conteúdo + subagente ganha `Read` escopado (via `allowed_tools=["Read"]` cuja autorização já existe; mudança fica em prompt + scratchpad layout). Reversibilidade preservada por construção.

O driver §3.0bis grava cada output via `write_scratchpad(name, obj)`: serializa `obj` (Pydantic) como JSON em `<run_path>/<name>` (ex. `01-triager.json`), atomic write, UTF-8/LF. É a materialização da gravação audit-only descrita acima — escrita pelo coordinator, sem leitura pelos subagentes.

## 5. Error handling e propagation

Cenários estruturados que o coordinator trata:

- **Pydantic validation falha** em output do subagente → halt; emite erro estruturado com etapa, payload bruto recebido, erro Pydantic (exception: `SubagentValidationFailed`).
- **MCP server retorna envelope de erro** durante `query()` → propaga; coordinator decide retry (transient: `SCAN_TIMEOUT`, `SEMGREP_EXECUTION_FAILED`) vs halt (validation/business/ non-transient) por errorCode, conforme retryability table de `policy-reader`/`semgrep-runner`.
- **`scan_diff` retorna envelope de erro de domínio** (Detector, §3.2) →
  detecção determinística por **presença de `errorCode` em
  `tool_use_result.structuredContent`** da `UserMessage` que carrega o
  `ToolResultBlock` de `mcp__semgrep-runner__scan_diff` (Option B: o flag
  `isError` é sempre `false`; ver ADR-0002 §3 e `.claude/rules/sdk-mcp-conventions`).
  O `structuredContent` do FastMCP sobrevive ao `query()` stream íntegro
  (verificado: smoke-test `sdk_tool_error_channel` v3); o `ToolResultBlock.content`
  carrega só a string JSON, não o dado estruturado. Roteamento por `isRetryable`
  da tabela `semgrep-runner` §5.4: retryable (`SCAN_TIMEOUT`,
  `SEMGREP_EXECUTION_FAILED`) → retry sob orçamento; non-retryable ou retry
  esgotado → escala como `DetectorScanFailed`, projetado no **envelope
  externo `CoordinatorError`** (§3.6; kind de erro do resultado
  coordinator→caller, **distinto** de `ReportPayload.run_outcome`) com
  anotação de coverage-gap. `findings: []` nunca aliasa erro.
- **Triager `decision: "skip"`** → não-erro; branching para §3.5 direto com input mínimo (ver §3.1).
- **Detector retorna zero candidatos** → não-erro; pipeline prossegue normalmente até §3.5 com `findings: []` propagando.
- **Família de errorCodes do Reporter** (DD-10.4 V3, três errorCodes discriminados por sinais observáveis distintos):
  - **`ReporterTurnsExhausted`** — `final_result.subtype == "error_max_turns"`. `isRetryable=True` (payload complexo; retry com `max_turns` maior pode resolver).
  - **`ReportNotEmitted`** — `subtype == "success"` E `emit_report_seen == False` E **não** há denials (`not permission_denials`, robusto a `None`). `isRetryable=False`.
  - **`ReporterPermissionDenied`** — `permission_denials` truthy (qualquer denial). `isRetryable=False` (anomalia de lockdown). Inspeção pós-loop obrigatória (`subtype` pode ser `"success"` apesar do denial).

Discrimination ordering: `if permission_denials:` (estrito, primeiro) → `subtype == "error_max_turns"` → `not emit_report_seen`.
- **`.mcp.json` declara server fora do whitelist `EXPECTED_SERVERS`** → halt no startup com erro estruturado (`CoordinatorStartupError`; ver §6).
- **Subagente retorna texto não-JSON** → mesmo path de Pydantic validation falha.
- **Subagente não responde / timeout / connection error** → `SubagentUnresponsive` erro estruturado; coordinator decide retry (transient) vs halt conforme política.
- **Subagente retorna resposta vazia** (sem text block, sem tool_use) → mesmo path de Pydantic validation falha (payload bruto = "").
- **Múltipla invocação de `emit_report` na mesma query do Reporter** → halt com `MultipleReportEmissions` erro estruturado (DD-10.1 ratificada V3; anti-pattern sinaliza bug em system_prompt do Reporter). Implementação em §3.5 (commit 1428d1a) + entrada na tabela acima.
- **`ToolUseBlock` sem `.input` attribute** (defensivo, edge case de SDK version incompat) → `MalformedToolUseBlock` erro estruturado; sugere versão de SDK abaixo do mínimo da Provisão MC-E.
- **Stream contém `ToolUseBlock`s intermediários não-`emit_report`** (ex: `ToolSearch` injetado pelo SDK quando tool search está ON, confirmado empiricamente smoke-test #38) → comportamento esperado, não-erro; coordinator filtra por `block.name` e ignora blocks intermediários audit-only. Stream completo permanece audit trail implícito (logs internos do `query()`).

**Contrato de exceções estruturadas do coordinator** (forward refs ao módulo de implementação; detalhamento da taxonomia de errorCodes fica para flesh completo):

| Exception | Quando | Recoverable |
|---|---|---|
| `CoordinatorStartupError` | `.mcp.json` whitelist falha, env vars inválidas, scratchpad criação falha | Não |
| `SubagentValidationFailed` | Pydantic falha em output do subagente | Não (no MVP) |
| `SubagentUnresponsive` | Timeout/connection error em `query()` | Sim (transient) |
| `CoordinatorStreamFailure` | Exception levantada durante `async for` sem `ResultMessage` capturado | Não (stream-level failure) |
| `ReportNotEmitted` | Reporter terminou query sem invocar `emit_report` (`subtype="success"` E `emit_report_seen=False` E `permission_denials=[]`) | Não |
| `ReporterTurnsExhausted` | Reporter atingiu `max_turns` sem invocar `emit_report` (`subtype="error_max_turns"`) | Sim (retry com `max_turns` maior) |
| `ReporterPermissionDenied` | `permission_denials` populado no `ResultMessage` final (lockdown bug) | Não (lockdown configuration) |
| `MultipleReportEmissions` | Reporter invocou `emit_report` mais de uma vez na mesma query | Não (anti-pattern em system_prompt) |
| `MalformedToolUseBlock` | `ToolUseBlock` sem campos esperados | Não (sinaliza SDK incompat) |
| `DetectorScanFailed` | Erro de domínio de `scan_diff` (`errorCode` presente) non-retryable, ou retryable com orçamento esgotado | Não (retry dos codes retryable ocorre antes do raise; non-retryable escalam direto) |
| `SubagentRefusedTask` | `stop_reason == "refusal"` em stage Branch B (mesmo sob `subtype="success"`) | Não (refusal de safety) |
| `SubagentExecutionError` | `subtype == "error_during_execution"` ou subtype inesperado | Não |
| `SubagentContractViolation` | `verify_passthrough` falha (mutação/perda/reordenação) — Classifier no MVP; Matcher diferido (G6) | Não |

**Nota sobre nomenclatura de envelope de erro MCP.** SDK Python usa `is_error: True` (snake_case) no envelope; SDK TypeScript usa `isError: true` (camelCase). FastMCP wire format usa camelCase (`isError`) conforme convenção MCP protocol. Implementação Python do coordinator e do `emit_report` retornam `is_error: True` quando sinalizam erro estruturado ao caller; recepção lê de campo correspondente do envelope MCP. Débito de housekeeping catalogado: verificar se FastMCP servers existentes (`policy-reader`, `semgrep-runner`) usam convenção correta — sessão Code dedicada ~20-30min (catalogado em `docs/tasks.md` §Companion edits).

**Nota de precedente — erro de tool de subagente (DD-D5).**
`DetectorScanFailed` é a primeira materialização do padrão de propagação de
erro de tool MCP consumida por subagente. Assinatura
`(stage, tool, errorCode, isRetryable, details)`: `stage`/`tool` para blame e
auditoria; `errorCode`/`isRetryable` herdados verbatim do envelope da tool
(não reinterpretados); `details` opaco por `errorCode`. Duas camadas, não
exclusivas — a exceção é o sinal de **controle de fluxo interno** (capturada
no boundary de orquestração); o **`CoordinatorError` do §3.6** é a projeção
externa. Retry-vs-escalate decorre de `isRetryable`, não do tipo da exceção.

*Generalização ao Matcher.* O mesmo caminho de detecção ("MCP server retorna
envelope de erro", acima) cobre as tools do `policy-reader` que o Matcher
consumirá; os erros de tool do Matcher seguirão esta assinatura. A escolha
entre exceção-irmã (ex.: `MatcherClauseLookupFailed`) e base compartilhada
(`SubagentToolError` com subclasses) é deferida à autoria de `matcher.md` — o
**contrato de campos** acima congela agora, para que a decisão de hierarquia
seja não-breaking. Promoção a ADR-0013 catalogada como follow-up.

*Reconciliação de taxonomia (feita neste flesh).* As três exceções acima foram
adicionadas à tabela; a reconciliação foi por **nome** (numeração não-paralela
entre specs). Correção de claim stale: `SubagentExecutionError` **não** está
ausente da tabela do detector — detector §6.3 a mapeia (`error_during_execution
→ SubagentExecutionError`). Nota de hierarquia: a **família de erro de tool**
(`DetectorScanFailed` e futuras tool-errors do Matcher) compartilha a base
`SubagentToolError` (matcher §6.4/DD-M18); esta tabela congela só **contrato de
campos** (`stage`/quando/recoverable), e a hierarquia (irmã vs base) é deferida
a **ADR-0013** (follow-up). As exceções SDK-class (`SubagentRefusedTask`,
`SubagentValidationFailed`, `SubagentUnresponsive`, `SubagentExecutionError`) e
`SubagentContractViolation` são eixo distinto da base de tool-error — não entram
sob `SubagentToolError`. A base mínima `SubagentToolError(Exception)` foi
**introduzida em MC-C** (Fase 0, com `DetectorScanFailed` como única subclasse no
MVP — barato e não-breaking); a **formalização da hierarquia** (irmãs, base rica,
`is_retryable` como contrato) permanece deferida a **ADR-0013**. A introdução
antecipa a base, não a decide.

**Nota (wrapper `{"output":{...}}` — observação, não bloqueio).** O smoke #50
(ST-B) mostrou que o wrapper não se manifesta em schema enum-tag simples
(Triager). Mas issues SDK #502/#571 o reportam vivo em schemas complexos
(arrays grandes, união) — perfil do `MatcherOutput` (`list[Finding]`) e do
`DetectorOutput` (`list[DetectorFinding]`). Se `error_max_structured_output_retries`
aparecer empiricamente nesses stages em Milestone D, reavaliar se
`SubagentValidationFailed` admite 1 retry. Registrado, não bloqueia o flesh.

## 6. `.mcp.json` consumption — quatro camadas de enforcement

`.mcp.json` no root do repo é single source of truth para configuração de MCP servers (decisão M2 / sessão #37). Dual-consumer: Claude Code CLI nativamente em desenvolvimento local + coordinator Python em runtime via parsing controlado.

**Coordinator não confia em auto-load do SDK.** SDK Python carrega `.mcp.json` automaticamente quando `setting_sources` é None (default) porque o source `"project"` está habilitado por padrão. Pattern seguro adotado neste projeto materializa **quatro camadas de enforcement ortogonais**:

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

**Defense candidate D2.3 — scoped access via tool distribution + SDK isolation.** Quatro camadas falham de modo diferente e protegem contra modos de falha distintos:

| Camada | Mecanismo | Modo de falha protegido |
|---|---|---|
| **C1** | Coordinator parseia `.mcp.json` + whitelist `EXPECTED_SERVERS` | Dev adicionou server por motivo Claude Code (debugger MCP, proxy dev) e esqueceu de remover → halt no startup |
| **C2a** | `setting_sources=[]` no `ClaudeAgentOptions` | SDK auto-load de filesystem settings (`.mcp.json` via source `"project"`, user CLAUDE.md, local settings) injetando server não-whitelisted → desabilitado por construção |
| **C2b** | `strict_mcp_config=True` (ortogonal a C2a) | Plugin MCP servers ou user MCP injetando server fora do whitelist via path não-coberto por `setting_sources` → ignorados |
| **C3** | `allowed_tools=[...]` per-etapa | Subagente em runtime decide auto-aprovar tool fora do escopo → só listadas auto-aprovam |
| **C4** | `permission_mode="dontAsk"` | Tool fora do allowlist tenta fall-through para `canUseTool` (não definido em headless) → denied outright, não suspended |

C2a e C2b são **ortogonais**: `setting_sources=[]` desabilita TODOS os filesystem settings (incluindo `.claude/agents/`, `CLAUDE.md`, slash commands, etc.); `strict_mcp_config=True` desabilita especificamente MCP injection vinda de `.mcp.json` + user MCP + plugin MCP. Belt-and-suspenders: cobrem paths distintos.

C3 (allowlist) e C4 (denial) também ortogonais: C3 garante que tools designadas auto-aprovam (não param o pipeline esperando aprovação); C4 garante que tools não-designadas são denied (não param o pipeline esperando `canUseTool` callback que não existe).

AS de teste correspondente em task futura de implementação do coordinator:
- (a) Carrega só whitelisted: dado `.mcp.json` com 2 servers whitelisted, então `mcp_servers={...}` propagado às queries contém exatamente esses 2.
- (b) Fail loud em server não-whitelisted: dado `.mcp.json` com server fora do whitelist, então `CoordinatorStartupError` emitido + halt antes de qualquer query.
- (c) Camada 2 + 4 enforce no SDK: dado teste com configuração ambiente simulando user-settings injeção, verificar que server injetado não aparece em runtime e que tool fora do allowlist é denied (não suspended).

Schema do `.mcp.json` é convenção do Claude Code CLI; coordinator empresta a config. Env vars opcionais (`POLICY_READER_ROOT`, `SEMGREP_RUNNER_ROOT`, `SEMGREP_RUNNER_TIMEOUT_SECONDS`) só declaradas quando coordinator precisa de roots não-default (teste de substituição de framework GDPR; rule-set override em CI). Run "normal" usa fallbacks CWD-relative.

## 7. `emit_report` custom tool

Definida em `src/subagents/reporter/tools.py` via factory pattern. Factory necessária porque o handler precisa capturar (i) `run_path` para gravar `99-report.json` (dual sink, sink #1) e (ii) `expected_report_id` para o cross-check de identidade do payload (Reporter spec §4.8 cross-check #4). Module-level `@tool` definition não permite esse closure capture — handler seria criado uma vez na importação, sem acesso aos parâmetros do run específico. Pattern factory + closure resolve:

```python
from pathlib import Path
from claude_agent_sdk import tool, create_sdk_mcp_server, ToolAnnotations
from src.coordinator.constants import EMIT_REPORT_DESCRIPTION  # Reporter spec §4.2
from src.coordinator.models import ReportPayload                # Reporter spec §4.3

def create_reporter_server(run_path: Path, expected_report_id: str):
    """Factory: instancia MCP server in-process com closure capture
    sobre run_path + expected_report_id. Detalhe completo do handler
    (Pydantic validation + cross-checks #1-4 + atomic write + envelope
    returns) em Reporter spec §4.8."""

    @tool(
        "emit_report",
        EMIT_REPORT_DESCRIPTION,
        ReportPayload.model_json_schema(),
        annotations=ToolAnnotations(
            readOnlyHint=False,       # escreve 99-report.json (sink #1)
            destructiveHint=False,
            idempotentHint=False,     # multiple emit é erro estruturado
            openWorldHint=False,
        ),
    )
    async def emit_report_handler(args):
        # Validate → cross-check → atomic write → return envelope.
        # Closure captures run_path + expected_report_id.
        # Full handler logic em Reporter spec §4.8.
        ...

    return create_sdk_mcp_server(
        name="reporter_tools",        # underscore preventivo (G4 / sessão #38)
        version="0.1.0",              # alinhado pre-1.0 do projeto; Reporter spec §4.8
        tools=[emit_report_handler],
    )
```

Factory invocada uma vez por run em §3.0 (Initialization) com `run_path` e `run_id` corrente; instância retornada (`reporter_sdk_server`) é reusada em §3.5 stage Reporter via `mcp_servers={"reporter_tools": reporter_sdk_server}`.

Schema input validado Pydantic via `ReportPayload.model_json_schema()` (single source of truth do schema vive em `src/subagents/reporter/models.py`; Reporter spec §4.3). **Dual sink** — explicitação de captura:

1. Handler `emit_report_handler` grava `99-report.json` no `run_path` capturado pela closure (audit/CI artifact). Primeira via.
2. Coordinator captura payload via inspeção do message stream: localiza `ToolUseBlock` com `name == "mcp__reporter_tools__emit_report"`, extrai `block.input` que contém os argumentos exatos passados pelo modelo à tool — isto é o payload do Report (ver §3.5). Segunda via, canônica para retorno ao caller.
3. **`return` do handler é canal de signaling ao modelo**, não canal de captura do payload. Retorna envelope de sucesso ou envelope de erro (`is_error: True` em validation failure; ver Reporter spec §4.4 + §4.5). Coordinator ignora o return value; só inspeciona `ToolUseBlock.input` do message stream.

Esclarecimento load-bearing (corrige inconsistência do skeleton #38): **`ToolUseBlock.input` é o canal canônico de captura**, não `ToolResultBlock.content`. Razão: `block.input` é o que o modelo **emitiu** como argumentos ao tool — payload do Report agregado; `ToolResultBlock` carrega o que o handler **retornou** para o modelo — ack ou erro de signaling. O coordinator quer o payload, não o ack.

**Tool authorization.** Exposta apenas via `allowed_tools=["mcp__reporter_tools__emit_report"]` na query do Reporter (§3.5; sem `"Read"` per Edit 1a / sessão #42 alinhamento com Reporter spec §1.5). Outras queries do pipeline (§3.1-§3.4) não incluem `reporter_tools` em `mcp_servers={...}` e não autorizam `mcp__reporter_tools__emit_report` em `allowed_tools`. Sob `permission_mode="dontAsk"` (C4), tentativa de invocação por outro subagente seria denied outright. Restrição arquitetural materializada em três camadas (C2 + C3 + C4); falharia para Reporter emitir e outras etapas não poderem.

**Nota sobre tool naming.** Padrão oficial documentado em `code.claude.com`: *"The key in mcpServers becomes the {server_name} segment in each tool's fully qualified name: mcp__{server_name}__{tool_name}."* Tool resolve via chave do dict `mcp_servers={...}`, não via campo `name=` declarado em `create_sdk_mcp_server`. Underscore preventivo em `"reporter_tools"` (em ambos: chave do dict e `name=` do server) elimina risco de parser do SDK interpretar mal hyphens em triple-pattern `mcp__<name>__<tool>`. Servers existentes `policy-reader` e `semgrep-runner` mantêm hyphen (empiricamente validados em Milestones A+B); migração para underscore é deferimento, não escopo MVP (ver §8).

## 8. Evoluções previstas

- **`claude-agent-sdk` como dependência — feito.** Pinado `==0.2.87` (MC-E, sessão #49); ADR-0001 D2 emendado registrando a adição. Não é mais pendência.

- **SDR como serializador downstream (pattern β).** Report JSON é artefato canônico do sistema multi-agente. Transformação Report → SDR CSV (append, audit governance LGPD Art. 37) é responsabilidade de consumer downstream (GitHub Action ou job de governança independente), não do sistema multi-agente. Três garantias de design no MVP preservam compatibilidade: (i) superset de campos do `structured_context` propagados verbatim por finding; (ii) audit metadata top-level (`report_id`, `report_emitted_at`); (iii) separação Reporter ↔ serializadores externos. Decisão sessão #37.

- **Cleanup do scratchpad.** Política de retenção (delete pós-run? preservar última N runs? rotação por idade?) a decidir conforme uso empírico em Milestone D + benchmark.

- **Cascading inheritance de stdio em sub-processes.** Catalogado em ADR-0011; relevante se subagentes via SDK herdarem handles do coordinator no Windows. Não detectado empiricamente em #34-#35; ratchet futuro se reaparecer.

- **Migração hyphen → underscore em server names.** `policy-reader` e `semgrep-runner` mantêm hyphen no MVP por compat com Milestones A+B já validados; nuance de naming convention é housekeeping deferido condicional. **Pivô vira obrigatório se** G4 smoke-test eventual (ou teste de integração no Reporter-flesh+) detectar bug latente em `allowed_tools` resolution. Provisão MC-F potencial: PR `chore/migrate-server-names-underscore` se evidência empírica materializar.

- **Evolução para A' (AgentDefinition + Agent dispatch) ou A (main agentic).** Se evolução futura introduzir paralelização (Detector + Classifier em paralelo) ou roteamento dinâmico (main agent escolhe entre múltiplos subagent candidates), pivô para A' (AgentDefinition por etapa + Agent dispatch) ou A (main agentic orquestrando via `agents={...}`). A'' atual (system_prompt direto) acomoda RF-008 sem refactor. Não-MVP.

- **CI/CD via `--strict-mcp-config` flag CLI.** Em Milestone D, coordinator pode rodar com `--strict-mcp-config` apontando para config dedicada (e.g., `.github/mcp-ci.json`), blindando contra interferência de configs locais do GitHub Actions runner. Equivalente CLI ao `strict_mcp_config=True` programático. Considerar na decomposição de Milestone D.

- **`WaitForMcpServers` tool** (v2.1.142+; aparece apenas quando tool search está OFF). Relevante se coordinator precisar lidar com delay de conexão de MCP servers no startup (e.g., `policy-reader` carregando Política grande). Anti-pattern atual: confiar em conexão sync; pivô para `WaitForMcpServers` em `allowed_tools` se empiricamente necessário. Não-MVP.

- **Tool search habilitação confirmada empiricamente.** Smoke-test #38 (SDK 0.2.87) ratificou que tool search está ON por default mesmo com pipeline de poucas tools (1 tool no smoke-test, caso degenerate; nosso pipeline usa 4-6 por etapa). Implicação operacional: stream do subagente contém `ToolUseBlock`s de `ToolSearch` antes da tool real; filter por `block.name` em §3.5 é o que sustenta captura correta. Tool search NÃO precisa estar em `allowed_tools` — é mecanismo interno do SDK, não tool agent-invocable. Deferment: avaliar empiricamente em Milestone D (benchmark ~200 snippets) se overhead de tool search introduz latência sensível em ratio token cost vs throughput. Pivô para tool search OFF possível via opção SDK se overhead detectado.

## 9. Cross-references

**Source-of-truth artifacts:**
- `docs/REQUIREMENTS.md` — RFs cobertas em Milestone C: RF-003 pleno, RF-004 pleno, RF-005 pleno, RF-006, RF-007 pleno, RF-008 pleno + RF-009.
- `docs/architecture-overview.md` §3 (fluxo de execução; **patch applied em MC-F sessão #43+ / this PR**), §4.3 (sistema multi-agente), §5 (subagentes detalhados — §5.4 Classifier e §5.5 Matcher mantêm acesso direto a `policy://vocabularies` per ADR-0005 Decision 4; sem patches sob (b2)), §5.7 (matriz tools × subagentes — sem patches sob (b2)).
- `docs/tasks.md` Milestone C — capability statement + RFs + gate milestone-level placeholder.
- `docs/specs/policy-reader/canonical.md` §3.3 (consumidores autorizados de `policy://vocabularies`: Matcher + Classifier).

**ADRs aplicáveis:**
- ADR-0001 (stack canônica; **amendment pendente** registrando adição de `claude-agent-sdk` como dep nova de Milestone C — ver §8)
- ADR-0002 (MCP conventions; §Decision 5 three-beats lifecycle)
- ADR-0005 (multi-client / framework-agnostic; §Decision 4 textbook case Resource vs Tool — preservado em capability sob (b2); granularidade per-server-via-built-in-tools documentada como nuance em ADR-0012)
- ADR-0008 (task decomposition e verification)
- ADR-0011 (Windows-stdio handle inheritance; cascading risk)
- **ADR-0012 retroativo Milestone C** (autorado, `docs/adr/0012-subagent-tool-governance.md`; cobre divergências metodológicas + decisões load-bearing A'', (b2), M2, S2', dual sink emit_report, quíntupla canônica, quatro camadas de enforcement D2.3; **citação pendente PR `chore/sync-adr-references`** removendo refs stale ADR-0012 → ADR-0011 em `docs/process/milestoneB.md` e triagem em `docs/process/learning-log.md`).

**Specs dos subagentes:**
- `docs/specs/subagents/reporter.md` — **primeira a redigir; destila `_template-subagent.md`** (ordem híbrida sessão #37)
- `docs/specs/subagents/triager.md` (sanity check pós-Reporter)
- `docs/specs/subagents/detector.md`
- `docs/specs/subagents/classifier.md`
- `docs/specs/subagents/matcher.md`
- (coordinator-flesh-completo após as 5 specs)

**Convenções de cross-reference** (anti-drift rules, ratificadas sessão #37):

1. Workflow vive APENAS aqui (§3). Specs de subagente citam `coordinator.md §3.<N>`; nunca duplicam.
2. Capability vive APENAS em REQUIREMENTS.md. Specs citam `RF-<N>`; nunca redefinem critério.
3. Error handling pattern vive APENAS aqui (§5). Specs citam; nunca redescrevem mecânica.
4. Schema de tools/resources MCP vive APENAS em `docs/specs/<server>/`. Specs citam canonical §<N>.
5. Specs de subagente só referenciam contrato I/O entre si, nunca comportamento interno.
6. **§3 (Output)** de cada subagent spec é canonical I/O boundary que downstream cita verbatim — nunca paráfrase, nunca redefinição.

## 10. Companion edit arch-overview (three-beats)

Patch único pendente em `docs/architecture-overview.md`, derivado da decisão de halt-condition caminho (i) da sessão #37:

**§3 Fluxo mermaid.** Substituir `T -->|skip| END[Sem ação]` por `T -->|skip| R[Reporter]`. Reflete decisão "Reporter sempre invocado" (caminho i / sessão #37); preserva §4.3 "Reporter como único locus emissor" sob substituição do mermaid que originalmente sugeria coordinator emitindo em skip path.

**Patches removidos vis-à-vis skeleton #37.** Decisão (b2) da sessão #38 elimina dois patches anteriormente catalogados:

- ~~§5.1 — Coordinator com acesso a `policy://vocabularies`~~ — NÃO aplica sob (b2); coordinator não acessa o resource.
- ~~§5.7 — Matriz ganha linha coordinator com ✓ em `policy://vocabularies`~~ — NÃO aplica sob (b2).

**Status three-beats** (per ADR-0002 §Decision 5 + ADR-0003):
- Beat 1 (proposed): patch §3 mermaid proposto em sessão #37 (caminho i da halt-conditions deliberation), mantido sob (b2) na sessão #38; patches §5.1 e §5.7 propostos em #37 foram eliminados em #38.
- Beat 2 (applied): companion edit arch-overview aplicado em MC-F (sessão #43+, this PR; ver §3 mermaid pós-edit).
- Beat 3 (verified): pendente review independente Chat pós-aplicação.

Three-beats persiste pós-aplicação como audit trail (per ADR-0002 §Decision 5).

---

**Reconciliação M19/M20 (Beat 3 — verified, sessão #50).**

Gateia a autoria de `matcher.md`. Origem: o mecanismo de seleção
`find_clauses_by_law_article` prescrito no arch está stale pós-MC-F (a
descoberta de cláusulas aplicáveis não é por artigo de lei; é check-all
interino sobre o catálogo). Superfície cirúrgica (texto atual / texto
proposto) abaixo; loci confirmados por leitura direta nesta sessão.

*M20 — mecanismo de seleção (`find_clauses_by_law_article` → check-all interino).*

- **arch §3 l.82** (confirmado). Atual:
  > **Etapa 3 — Matcher.** Para cada candidato classificado, consulta o MCP server `policy-reader` via `find_clauses_by_law_article` para descobrir cláusulas aplicáveis, depois invoca `check_applicability` por cláusula. […]

  Proposto:
  > **Etapa 3 — Matcher.** Para cada candidato classificado, descobre cláusulas candidatas lendo o resource `policy://catalog` (cláusulas `active`) e invoca `check_applicability` por cláusula (mecanismo interino A — check-all; o mecanismo definitivo será a tool `find_clauses_by_applicability`, DD-M3). […]

- **arch §5.5 l.197** (Tools permitidas) — adiciona `policy://catalog`.
  ⚠️ **Decisão aberta:** isto expande a autorização de resource do
  Matcher (boundary de capability). Atual:
  > **Tools permitidas.** MCP server `policy-reader` — tools (`find_clauses_by_law_article`, `get_clause`, `check_applicability`) e resource `policy://vocabularies` (compartilhado com Classifier). […]

  Proposto:
  > **Tools permitidas.** MCP server `policy-reader` — tools (`get_clause`, `check_applicability`, `find_clauses_by_law_article`) e resources `policy://catalog` + `policy://vocabularies` (este último compartilhado com Classifier). O mecanismo de seleção interino (A check-all, DD-M3) lê `policy://catalog` para enumerar cláusulas `active` e invoca `check_applicability` por cláusula; `find_clauses_by_law_article` permanece autorizada mas não é o caminho de seleção. […]

- **arch §5.7** (matriz tools × subagentes) — adiciona linha de resource
  `policy://catalog` com ✓ no Matcher, após a linha `policy-reader — tools`:
  > `| `policy-reader` — resource `policy://catalog` | | | | | ✓ | |`

- **reporter §2.2 l.135** (re-deriva invariante de cardinalidade, DD-M6).
  **Roteia pela spec do Reporter, não por este ledger.** Atual:
  > […] Matcher para cada candidato invoca `find_clauses_by_law_article` retornando K cláusulas aplicáveis, e `check_applicability` por cláusula produz um verdict. Resultado: `len(findings) ≥ candidates_count`, sem invariante de igualdade.

  Proposto:
  > […] Matcher para cada candidato enumera as K cláusulas `active` de `policy://catalog` e invoca `check_applicability` por cláusula, produzindo um verdict por par (mecanismo interino A check-all, DD-M3). Resultado: `len(findings) ≥ candidates_count` (DD-M6), sem invariante de igualdade.

*M19 — `candidate_ref` + `evidence` flat → discriminated union por verdict.*

- **arch §5.5 l.201** (Output do Matcher) — dropa `candidate_ref`,
  alinha `evidence` flat à discriminated union vinculante de
  `reporter.md` §3.2. Atual:
  > **Output.** Lista de findings: `[{candidate_ref, policy_clause_ref, verdict, verification_scope?, requires_human_review?, evidence}]` onde `verdict ∈ {…}`. […]

  Proposto:
  > **Output.** Lista de findings, cada um uma discriminated union por `verdict` (shape vinculante: `reporter.md` §3.2): campos comuns `{policy_clause_ref, verdict, trinque de provenance, requires_human_review?}` mais o discriminador por veredito — `evidence` (`compliant`; `violation_candidate`, este com `contradicted_requirement?`), `reason` (`not_applicable`), `verification_scope` (`indeterminate`). […] (Localização do candidato — `file`/`line`/`snippet` — é threaded do Detector/Classifier per `reporter.md` §3.2; `candidate_ref` removido — M19.)

- **arch §5.7 para M19:** ⚠️ **sem alvo.** `candidate_ref`/`evidence`
  não aparecem na matriz §5.7 (é tabela tools × subagentes). O "+§5.7"
  da formulação M19 não tem onde aplicar; M19 incide só em arch §5.5 l.201.

*Loci confirmados / divergências de número de linha:* arch §3 l.82,
arch §5.5 l.197+l.201, arch §5.7 matriz, reporter §2.2 l.135 — todos
conferidos por leitura direta. `candidate_ref` existe **só** em arch
§5.5 l.201 (ausente de §5.7 e de `reporter.md`).

*Evidência empírica do mecanismo (smoke-test sessão #48, `server.py` +
servidor live).* `policy://catalog` **existe** e é a fonte de
enumeração do check-all: retorna lista top-level de
`{clause_id, title, status, article_sources_summary, successors?}` —
o Matcher filtra `status == "active"` e invoca `check_applicability`
por `clause_id`. O catalog **não** carrega `applies_to` (só os 5 campos
de índice), então todo o matching de aplicabilidade fica em
`check_applicability`. Os 3 únicos resources expostos são
`policy://catalog`, `policy://vocabularies`, `policy://schema-version`
(não existe `policy://clauses` nem `policy://rationale`).

*Checks de boundary pré-aplicação (sessão #48):*
- **Check A — ADR-0005 Decision 4:** D4 concede `policy://vocabularies`
  como resource **compartilhado** (Classifier + Matcher) e mantém os
  *tools* exclusivos do Matcher; a única restrição que impõe é sobre o
  **Classifier** (ganha o resource, não os tools). D4 é **silente**
  sobre o Matcher acessar `policy://catalog`. Logo conceder catalog ao
  Matcher é **extensão-de-doc**, não emenda ao ADR-0005. ✅ segue.
- **Check B — alcance runtime (smoke-test #48, `claude-agent-sdk==0.2.87`):**
  `ReadMcpResourceTool` com grant **bare** + `mcp_servers={policy-reader}`
  **leu `policy://catalog`** (retornou o catálogo POL-000), sem
  `permission_denials`. Acesso a resource é **per-server, não
  per-URI** — a concessão já alcança. ✅ §5.5/§5.7 documentam capability
  existente.
  - ⚠️ **Achado de config (DD-9.1 Matcher):** sob `tools=["Read"]` o
    modelo **não enxerga** `ReadMcpResourceTool`/`ListMcpResourcesTool`
    (o `tools` field governa built-ins; esses não estão em `["Read"]`),
    apesar de presentes em `allowed_tools`. Os tools de MCP server
    (`check_applicability` etc.) seguem visíveis via `mcp_servers`. Para
    o check-all rodar, o AgentDefinition do Matcher precisa incluir
    `ReadMcpResourceTool` + `ListMcpResourcesTool` no `tools` field (ou
    omitir o field, pagando o turn de ToolSearch — AC-1 de
    `sdk_mcp_visibility`). Registrar na atualização da tabela DD-9.1.
    - ⚠️ **Extensão (#48-b):** a #48-b mediu os estados lado a lado e
      confirmou que **`tools=[]` também** esconde os built-ins (não só
      `tools=["Read"]`). E o achado **propaga ao Classifier (§3.3)**:
      ele declara `tools=["Read","Grep"]` e lê `policy://vocabularies`
      via `ReadMcpResourceTool` — mesma quebra. Config corrigida em §3.3
      e §3.4 para listar os dois built-ins. Não basta o patch de prosa a
      `classifier.md:45`. **Princípio:** todo subagente que lê resource
      via `ReadMcpResourceTool` sob `tools` não-vazio lista os dois
      built-ins de resource. Evidência persistida em
      `scripts/smoke_tests/check_applicability_48b/RESULTS.md` (4 estados
      de `tools` lado a lado; Gate resource access PASS — `classifier.md`
      §10.3).

*Status three-beats:*
- Beat 1 (proposed): sessão #48, superfície acima.
- Beat 2 (applied): sessão #48 — Checks A (silente→extensão-de-doc) e B
  (alcança per-server) passaram; aplicado em `architecture-overview.md`
  (§3 l.82, §5.5 l.197+l.201, §5.7 linha de resource `policy://catalog`)
  e `reporter.md` (§2.2 cardinalidade DD-M6). M19 incidiu só em §5.5
  l.201 (sem alvo em §5.7, confirmado).
- Beat 3 (verified): ✅ sessão #50 — leitura verbatim confirmou aplicação em
  `architecture-overview.md` (§3 l.66 mermaid `T -->|skip| R`, §3 l.82 check-all
  sobre `policy://catalog`, §5.5 l.197 catalog + seleção interina, §5.5 l.201
  `candidate_ref` removido/M19, §5.7 linha `policy://catalog` ✓) e `reporter.md`
  (§2.2 l.139 cardinalidade DD-M6 `len(findings) ≥ candidates_count`). M19/M20
  fechados; three-beats persiste como audit trail (ADR-0002 §Decision 5).

## 11. Gates pré-coordinator-flesh

Smoke-test residual obrigatório antes de coordinator-flesh-completo ser autorado (sessão Chat #39+) e antes de tasks T11+ serem implementadas. Sessão Code curta dedicada ~10-15min.

**Gate 1 — `ToolUseBlock.input` attribute shape para custom tools.**

**Status: PASS** (smoke-test sessão Code #38; SDK `claude-agent-sdk==0.2.87`; script tracked em `scripts/smoke_tests/sdk_tooluseblock_shape/` com README).

Confirmações empíricas:
- `ToolUseBlock` em `claude_agent_sdk.types`; surface mínima é exatamente 3 atributos: `id`, `name`, `input` (sem `parent_tool_use_id` no nível do block — consistente com A'' ausência de nested subagent spawn).
- `block.input` é dict com chaves correspondentes aos parâmetros declarados via `@tool` decorator; valores são args exatos passados pelo modelo.
- Quíntupla canônica (`dontAsk` + `setting_sources=[]` + `strict_mcp_config=True` + `allowed_tools` whitelist + `mcp_servers` dict) ratificada como side effect do mesmo teste (TC2).
- Underscore naming (`mcp__test_tools__echo`) resolve sem quirks (TC3).

Achado adicional empírico (AC1 do reporting): tool search está ON por default no SDK 0.2.87; stream do subagente pode conter `ToolUseBlock`s intermediários (ex: `ToolSearch` com `{'query': 'select:mcp__test_tools__echo', 'max_results': 1}`) antes do tool real. Filter por `block.name` em §3.5 sustenta captura correta. Documentado em §3.5 (comentário inline + rationale de halt-condition) + §5 (caso de error handling não-erro) + §8 (item "Tool search habilitação confirmada empiricamente").

Achado adicional empírico (AC2 do reporting): tipos de message no stream — `SystemMessage`, `RateLimitEvent`, `AssistantMessage` (carrega `ToolUseBlock`), `UserMessage` (tool result injection back to model), `ResultMessage` (signal de término). Coordinator inspeciona ao menos `AssistantMessage` (para captura) e `ResultMessage` (para terminação); demais tipos são audit trail.

**Critério Fail (não-materializado; preservado como audit trail forward-looking).** Se TC1 tivesse falhado: atributo tem nome diferente (`.arguments`, `.params`, `.tool_input`, etc.). Surgical edit em §3.5 e §7 do skeleton para ajustar nome do atributo. Provisão MC-G aberta se Fail (não aberta; pattern padrão `.input` confirmado).

Custo de Fail teria sido trivial (~5min surgical edit). Custo de não-rodar teria sido: descobrir bug em Reporter-flesh ou em primeira execução do pipeline (caro de retornar). Ratchet barato preveniu ambos.

**Decisões fora do escopo deste gate** (documentadas como deferments):
- G4 hyphen-vs-underscore em server names existentes — deferred condicional (ver §8); ratchet futuro se bug latente materializar.
- `is_error`/`isError` em FastMCP servers existentes — débito de housekeeping catalogado em `docs/tasks.md` §Companion edits.
- `WaitForMcpServers` necessidade — pendente uso empírico (ver §8).
- Tool search ON quirk com poucas tools — pendente uso empírico (ver §8).

**Resolução por web search durante sessão Chat #38** (não-gates):
- Quíntupla canônica do lockdown agent (`dontAsk` + `setting_sources=[]` + `strict_mcp_config=True`) confirmada via doc canônica `platform.claude.com/docs/en/agent-sdk/permissions` e `platform.claude.com/docs/en/agent-sdk/mcp`.
- `ListMcpResourcesTool` + `ReadMcpResourceTool` (com sufixo `Tool`) como nomes corretos confirmados via tools-reference oficial.
- Restrição "subagents cannot spawn subagents" confirmada via `docs.claude.com/en/docs/agent-sdk/subagents`.
- Tool renaming `Task` → `Agent` em Claude Code v2.1.63 confirmado via mesma fonte.

Gates pré-flesh são honestidade epistêmica: design proposta em Chat sob inferência arquitetural sobre SDK requer ratchet empírico para claims não-cobertas por doc canônica antes de virar contrato. Defense candidate forte para Capítulo de Método: pattern dual-validation Chat-external (web) + Code-internal (repo) + Code-empirical (smoke-test) materializado em sessão #38 sobre design proposals do #37.
