# reporter

**spec_version**: 0.3.0

> **Status.** Primeira spec de subagente do projeto. Destilada inicialmente na sessão Chat #39 (draft de 1530 linhas com hard-wrap), revisada por Code (V1 + V2 reviews), refinada via PR #66 (DD-21 — `policy_clause_ref` ratificado) e PR #67 (Gate 6 — `tools=[]` confirmado empiricamente). Sessão Chat #41 ratificou três achados de review e bumped a 0.2.0. Sessão Chat #42 absorveu dois reviews independentes (cross-doc rigoroso + arquitetural-gaps) que convergiram em catch crítico de cross-check #3 vocab source e divergiram em catches complementares; bump a 0.3.0 reflete refinamento substantivo de contract surface: (i) remoção de cross-check #3 (vocab membership é semântica do Matcher per §2.4 + §8.3, não shape do Reporter); (ii) anotações de contingência sobre `tools=[]` tense forward-looking até landing do companion edit ao coordinator §3.5; (iii) reescrita da invariante em §2.2 (Matcher emite finding por par candidato-cláusula, M ≥ N — não igualdade); (iv) correção da sintaxe few-shot em §5.1 (`emit_report({...})`, schema flat sem wrapper `payload`); (v) reescrita da aritmética de retry budget em §1.5 (linguagem reconciliada com §4.5 + §6.7); (vi) hardening: `legal_framework: Literal["LGPD"]` no MVP, `report_id` UUID v4 validation explícita, `os.replace` (Windows-native) declarado em §4.9, locus dos módulos pinado em `src/coordinator/{models,constants,system_prompts,tools}.py`. Segunda passada de review dentro de #42 absorveu quatro fixes documentacionais consolidados no mesmo PR (sem bump 0.3.1, por consenso entre os dois reviewers): renumbering propagation a §8.3 (remoção do bullet vocab + #4a/4b → #3a/3b + #5 → #4) e §10.3 (Gate 4 #4b → #3b); residual "trinque" → "triple" no `<input>` do `REPORTER_SYSTEM_PROMPT` em §5.1; stale "ou inline" removido de §7.2 alinhando ao pin de módulos em §1.5.

> **Companion edits pendentes a `coordinator.md`.** Catalogadas em §10.5 (6 edits — item 6 adicionado em #42). Decisão de sub-packaging ratificada em sessão Chat #41 e mantida em #42: **PR único pós-merge desta spec**, narrativa "sync coordinator with reporter.md spec_version 0.3.0". Surgical edits triviais, ~30min de Code work agregado.

## 1. Identidade e propósito

### 1.1 Nome canônico

`reporter` — identificador do subagente, materializado em runtime como configuração de `ClaudeAgentOptions` aplicada à stage §3.5 do coordinator, não como `AgentDefinition` ou entrada em `agents={...}`.

Distinção de naming load-bearing: o subagente é `reporter`; o MCP server in-process que expõe sua tool exclusiva é `reporter_tools` (underscore preventivo per coordinator §7; instanciado via factory `create_reporter_server(run_path, expected_report_id)` em `src/coordinator/tools.py`). Esta spec descreve o subagente; o contrato de tool wire-level vive em §4 + coordinator §7.

### 1.2 Função

Subagente terminal do pipeline. Recebe o estado consolidado pelo coordinator — vereditos do Matcher no caminho normal, estado de skip do Triager no caminho de skip — e o emite verbatim como Report JSON estruturado, via a tool customizada `emit_report`, para captura pelo coordinator e persistência em scratchpad. **Não sintetiza, não reclassifica, não computa discriminadores derivados** — `run_outcome`, `summary.counts` e demais campos pré-computados pelo coordinator são propagados sem transformação (inversão DD-7.3 / sessão #38).

### 1.3 Posição na arquitetura

Ver `architecture-overview.md` §4.3 (Reporter como único locus emissor de Report), §5.6 (responsabilidades do Reporter), §5.7 (matriz tools × subagentes — linha Reporter). Workflow operacional em `coordinator.md` §3.5 (Reporter stage canônico), §3.6 (termination), §5 (família de errorCodes do Reporter), §7 (`emit_report` custom tool, dual sink). Esta spec não duplica nenhum desses loci — cita verbatim quando preciso (Rule 6 do coordinator §9).

### 1.4 Invocador e tool authorization

**Invocador.** O coordinator, exclusivamente. Mecanismo de enforcement materializado por construção sob pattern A'' (coordinator §2): Reporter é o **main agent** da sua própria `query()` no `claude-agent-sdk` — não há `AgentDefinition` registrada, não há entrada em `agents={...}` em nenhuma stage, não há dispatch via `Agent` tool em nenhum `allowed_tools` do pipeline. A restrição do SDK *"Subagents cannot spawn their own subagents"* reforça o lockdown, mas não opera como gate ativo porque nenhum subagente do pipeline tem `Agent` em seu inventário. Ausência de mecanismo é a garantia.

**Tool authorization sobre `emit_report`.** A tool `mcp__reporter_tools__emit_report` é exposta **exclusivamente** ao subagente Reporter via duas restrições combinadas: (i) o MCP server in-process `reporter_tools` aparece em `mcp_servers={...}` **somente** na stage §3.5 do coordinator (não em §3.1-§3.4); (ii) `mcp__reporter_tools__emit_report` aparece em `allowed_tools=[...]` **somente** na mesma stage. Sob a quíntupla canônica de lockdown do coordinator (§2 — `permission_mode="dontAsk"`, `setting_sources=[]`, `strict_mcp_config=True`, `allowed_tools` whitelist per-stage, `mcp_servers` dict per-stage) somada à context restriction `tools=[]` (eixo ortogonal availability vs denial-on-miss, ratificado em `scripts/smoke_tests/sdk_tools_empty_list/`; ver §1.5) e às quatro camadas de enforcement (coordinator §6), tentativa de invocação por qualquer outro subagente é denied outright no SDK — não suspended, não prompted. Reciprocidade: Reporter **não tem acesso** a `mcp__semgrep-runner__scan_diff`, `mcp__policy-reader__*`, nem aos resources `policy://*` (sem entrada em `mcp_servers={...}` da §3.5; sem entrada correspondente em `allowed_tools`).

> 💡 **Conceito Claude relevante (Domínio 2 — Tool Design & MCP Integration):** scoped tool access via combinação de `mcp_servers` (per-stage allowlist de servers) + `allowed_tools` (per-stage allowlist de tools fully-qualified) + `permission_mode="dontAsk"` (denial-on-miss) + `tools=[]` (availability lockdown — remove built-ins do contexto do modelo, per PR #67 evidência empírica) é o pattern arquitetural que materializa "subagent exclusivity" sob A'' (sem AgentDefinition). Nuance crítica: `allowed_tools` **NÃO controla availability** (issue #361 da SDK Python: "It does not remove tools from Claude's toolset"); apenas pre-aprova. Context restriction é via `tools` field. Defense candidate forte do projeto.

> 💡 **Conceito Claude relevante (Domínio 1 — Agentic Architecture & Orchestration):** sob pattern A'' (prompt chaining estrito), o Reporter não é "subagente" no sentido formal do SDK (entidade dispatchada por main agent via `Agent` tool); é **main agent de uma `query()` única**, com `system_prompt` e configuração de tools próprias, encadeada sequencialmente pelo coordinator Python. O termo "subagente" no projeto refere-se ao papel funcional no pipeline, não ao construct SDK. Distinção load-bearing para a defesa da arquitetura.

### 1.5 Stack e governança

**Runtime.** `claude-agent-sdk` Python. Versão mínima pinada via `uv lock` quando dep for adicionada a `pyproject.toml` (pendente em amendment a ADR-0001). Confirmação empírica em SDK 0.2.87 via smoke-tests #38b, #38c (sessão de extração de DDs) e Gate 6 (`tools=[]` semantics, PR #67).

**Locus do contrato runtime.** O contrato comportamental do Reporter materializa-se em três artefatos disjuntos: (i) o objeto `ClaudeAgentOptions` da stage §3.5 do coordinator (quíntupla canônica do lockdown + `max_turns=3` + `tools=[]` per Gate 6 + `allowed_tools=["mcp__reporter_tools__emit_report"]` + `mcp_servers={"reporter_tools": reporter_sdk_server}`); (ii) o `REPORTER_SYSTEM_PROMPT` (texto canônico em §5); (iii) o MCP server in-process `reporter_tools` definido em `src/coordinator/tools.py` (a criar) via factory `create_reporter_server(run_path, expected_report_id)` registrando o handler `emit_report` (wire-level em §4).

**Locus dos módulos Python.** Pinado nesta spec como ratificado em sessão Chat #42 (doc oficial Claude Agent SDK não prescreve estrutura; decisão de projeto baseada em blame auditability + symbol unicity per ADR-0001 D3): `src/coordinator/models.py` para `ReportPayload`/`Finding`/`SummaryModel` Pydantic; `src/coordinator/constants.py` para `REPORT_SCHEMA_VERSION` + `EMIT_REPORT_DESCRIPTION` (single source of truth referenciado também pelo coordinator §7 per companion edit §10.5 item 3); `src/coordinator/system_prompts.py` para `REPORTER_SYSTEM_PROMPT`; `src/coordinator/tools.py` para factory `create_reporter_server` + handler + helpers privados (`_validation_error_envelope`, `_error_envelope`, `_success_envelope`, `_atomic_write_json`, `_run_cross_checks`). Diretório `src/coordinator/` é módulo planejado de Milestone C — nenhum desses arquivos existe em main ainda.

**Tense forward-looking sobre `tools=[]`.** Esta spec descreve a configuração-alvo. O coordinator §3.5 em main corrente declara `tools=["Read"]`; a transição para `tools=[]` é companion edit §10.5 item 1 (sub-packaging PR único pós-merge desta spec). Claims subsequentes em §2.1 ("`tools=[]` … garante que built-ins Read/Grep/etc não estão no contexto"), §8.1 #7 ("`tools=[]` … remove Read/Write/Edit/Bash/Grep/Glob do contexto"), e §6.7 ("sob `tools=[]`, ToolSearch é skipped") assumem o estado pós-edit. Importante: a reciprocidade declarada em §1.4 (Reporter não tem acesso a `policy://*` ou a `mcp__policy-reader__*` ou a `mcp__semgrep-runner__*`) permanece verdadeira sob `tools=["Read"]` corrente — a proteção emerge da ausência de `policy-reader` e `semgrep-runner` em `mcp_servers={...}` da stage §3.5, não da configuração `tools`. Apenas o claim sobre availability dos built-ins é contingente.

**Por que `create_sdk_mcp_server` e não FastMCP.** CLAUDE.md declara FastMCP como stack canônico para custom MCP servers stdio (`policy-reader`, `semgrep-runner`). `reporter_tools` foge dessa regra deliberadamente: precisa de closure capture sobre `run_path` e `expected_report_id`, o que requer compartilhamento de escopo Python — impossível com FastMCP subprocess (sem shared memory). Doc Anthropic oficial (`platform.claude.com/docs/en/agent-sdk/custom-tools`) trata os dois constructs como casos de uso doc-validated distintos: **stdio MCP server** = "Local processes that communicate via stdin/stdout"; **in-process via `create_sdk_mcp_server`** = "Define custom tools directly in your application code instead of running a separate server process". `reporter_tools` cai legitimamente na segunda categoria.

**Turn economy via `tools=[]`.** PR #67 confirmou empiricamente: `tools=[]` herda comportamento de allowlist explícita (skip de ToolSearch deferred-loading do SDK), reduzindo `num_turns` baseline. Aritmética canônica do retry budget (locus authoritative — outros loci citam por referência):

- `max_turns=3` é o cap enforced pelo SDK.
- Sob baseline `tools=None`: SDK injeta um turn inicial de ToolSearch (deferred-loading do tool registry); modelo dispõe efetivamente de 2 turns para a lógica dentro do cap.
- Sob `tools=[]`: ToolSearch é skipped; modelo dispõe dos 3 turns inteiros para a lógica (initial emit + até 2 retries em caso de validation error envelope retornado pelo handler).
- Path normal: `num_turns=1` (emit_report → ack success → end_turn).
- Path retry-uma-vez: `num_turns=2`. Path retry-duas-vezes: `num_turns=3`.
- Path exaustivo (3 emits sucessivos com `is_error: True`): SDK reporta `num_turns=4` com `subtype="error_max_turns"` (AC-4 do smoke-test #38b empírico; ratifica que SDK conta o cap-overflow turn).

§4.5 e §6.7 citam esta aritmética por referência — não a redeclaram.

**ADRs aplicáveis.**

- **ADR-0001** — stack canônica; amendment pendente registrando adição de `claude-agent-sdk` como dep nova de Milestone C.
- **ADR-0002** — MCP conventions; três classes de erro (`validation`/`business`/`system`) + Option B wire format (`isError` discriminado por presença de `errorCode` em `structuredContent`). Aplicado ao envelope de erro de `emit_report` (§4 e §6). Nuance: handler do `@tool` claude-agent-sdk usa `is_error` (snake_case Python idiom) per `.claude/rules/sdk-mcp-conventions.md`; SDK traduz para `isError` no wire MCP.
- **ADR-0005** — multi-cliente; trinca de provenance (`policy_schema_version`, `policy_version`, `legal_framework`) preservada verbatim por finding e replicada top-level (cross-check intra-handler em §4.8).
- **ADR-0006** — language conventions: tool description em inglês, `REPORTER_SYSTEM_PROMPT` em inglês, identifiers/code em inglês, prosa de spec e cláusulas POL-NNN em português.
- **ADR-0007** — escopo MVP v0.1.0: matching restrito a `operation: collection`. Vereditos `not_applicable` decorrentes desse escopo são propagados verbatim pelo Reporter (sem re-filtragem).
- **ADR-0012 retroativo** (a redigir pós-coordinator-flesh-completo): cinco decisões load-bearing de Milestone C — pattern A'', `emit_report` dual sink, quíntupla canônica do lockdown agent CI/CD-headless, quatro camadas de enforcement de scoped access, e divergência metodológica contra `docs/specs/_template.md` (template destilado pós-Reporter+Triager, não autorado upfront).

## 2. Input contract

### 2.1 Shape do input

O Reporter recebe input **inline no prompt** construído pelo coordinator em §3.5, não via tool input ou resource read. O coordinator serializa o estado consolidado como string JSON e injeta no prompt builder `build_reporter_prompt(matcher_output_or_skip)`. Reporter não invoca tools de leitura para acessar estado upstream — todo o input necessário está literalmente no prompt da sua query.

Esta arquitetura preserva (i) determinismo do input — uma única fonte: o prompt; (ii) auditabilidade — input visível em logs do `query()`; (iii) ausência de side channel — Reporter não consome `policy://*` resources nem outputs intermediários de outros subagentes via `Read` no scratchpad. Adicionalmente, `tools=[]` na configuração da stage §3.5 (per Gate 6 / PR #67) garante que built-ins Read/Grep/etc não estão no contexto do modelo, eliminando tentativas de fallback para fontes alternativas.

### 2.2 Caminho normal (Triager → Detector → Classifier → Matcher → Reporter)

O coordinator monta o prompt do Reporter com o estado consolidado a seguir (representação lógica; serializado como JSON inline na string do prompt):

```python
{
    # Discriminadores pré-computados (DD-1.1, DD-1.2)
    "run_outcome": "success_with_findings" | "success_no_candidates"
                   | "success_all_not_applicable",
    "triager_skip_reason": None,

    # Audit metadata
    "report_id": "<uuid>",

    # Provenance trinca top-level
    "policy_schema_version": "0.1.0",
    "policy_version": "<...>",
    "legal_framework": "LGPD",

    # Schema versioning
    "report_schema_version": "0.1.0",

    # Scope (arch-overview §5.6 — herdado, não computado por Reporter)
    "scope": {...},

    # Counts pré-computados — zeros explícitos via Pydantic default
    "summary": {
        "counts": {
            "compliant": <int>,
            "violation_candidate": <int>,
            "indeterminate": <int>,
            "not_applicable": <int>,
        },
        "total": <int>,
    },

    # Findings — ordem preservada do Matcher (DD-19)
    "findings": [
        {
            "file": "<path>",
            "line": <int>,
            "snippet": "<código>",
            "rule_id": "<identificador da regra do Detector>",
            "data_categories": ["<token canônico de POL-000>", ...],
            "operation_type": "collection",  # MVP v0.1.0
            "verdict": "compliant" | "violation_candidate"
                       | "indeterminate" | "not_applicable",
            "policy_clause_ref": "POL-NNN",  # SEMPRE presente em todos 4 verdicts
                                              # (DD-21 ratificado PR #66)
            # ... campos variantes por verdict (ver §3.2)
            "requires_human_review": <bool>,  # opcional
            "policy_schema_version": "0.1.0",
            "policy_version": "<...>",
            "legal_framework": "LGPD",
        },
        ...
    ],
}
```

**Invariante upstream:** no caminho normal, o coordinator garante em §3.4 que cada finding emitido pelo Matcher carrega `policy_clause_ref` válido e shape de discriminated union completa por verdict, antes de invocar Reporter. (Nota: Matcher emite **um finding por par candidato-cláusula** — Classifier produz N candidatos com `structured_context`, Matcher para cada candidato invoca `find_clauses_by_law_article` retornando K cláusulas aplicáveis, e `check_applicability` por cláusula produz um verdict. Resultado: `len(findings) ≥ candidates_count`, sem invariante de igualdade.) Violação halt em `SubagentValidationFailed` no coordinator; Reporter não revalida shape.

### 2.3 Caminho skip (Triager → Reporter)

O coordinator monta o prompt do Reporter com estado consolidado de skip path:

```python
{
    "run_outcome": "skipped_by_triager",
    "triager_skip_reason": "<string razão do skip>",
    "report_id": "<uuid>",
    "policy_schema_version": "0.1.0",
    "policy_version": "<...>",
    "legal_framework": "LGPD",
    "report_schema_version": "0.1.0",
    "scope": {...},
    "summary": {
        "counts": {
            "compliant": 0,
            "violation_candidate": 0,
            "indeterminate": 0,
            "not_applicable": 0,
        },
        "total": 0,
    },
    "findings": [],  # vazio (DD-16)
}
```

Triager skip path passa por Reporter normalmente (decisão halt-conditions caminho i / sessão #37; coordinator §3.1 branching). Reporter formata o Report do skip path com a mesma estrutura do caminho normal, com `findings: []` e `triager_skip_reason` preenchido.

### 2.4 Princípio: Reporter não computa, não deriva, não infere

Toda quantidade derivada (`run_outcome`, `summary.counts`, `summary.total`) é **pré-computada pelo coordinator em Python**. Reporter recebe os valores prontos e os propaga verbatim ao payload do Report. Esta é a inversão DD-7.3 / sessão #38: lógica de discriminação determinística pertence ao coordinator; Reporter é puro passthrough + `emit_report` invocation.

Anti-pattern explícito: Reporter **NÃO** recomputa `run_outcome` a partir dos findings (mesmo que pudesse inferir corretamente em casos triviais); **NÃO** recomputa `counts` agregando findings; **NÃO** re-ordena findings (DD-19); **NÃO** decide se invoca `emit_report` em skip path baseado em sua própria avaliação. Coordinator é a fonte de verdade; Reporter é o serializador.

## 3. Output contract — Report payload

### 3.1 Top-level shape

Payload retornado pelo Reporter via `emit_report` (string JSON serializável; schema validado server-side via `ReportPayload` Pydantic model + cross-checks intra-handler — ver §4):

```python
{
    "report_id": "<uuid>",
    "report_schema_version": "0.1.0",
    "policy_schema_version": "0.1.0",
    "policy_version": "<...>",
    "legal_framework": "LGPD",
    "run_outcome": "success_with_findings"
                   | "success_no_candidates"
                   | "success_all_not_applicable"
                   | "skipped_by_triager",
    "triager_skip_reason": <str | None>,
    "scope": {...},
    "summary": {
        "counts": {
            "compliant": <int>,
            "violation_candidate": <int>,
            "indeterminate": <int>,
            "not_applicable": <int>,
        },
        "total": <int>,  # == sum(counts.values()); cross-check em §4.8
    },
    "findings": [<Finding>, ...],
}
```

> 💡 **Conceito Claude relevante (Domínio 5 — Context Management & Reliability):** o discriminador `run_outcome` materializa structured error metadata aplicado também ao caminho de sucesso. Quatro tokens distintos sinalizam quatro causas operacionais raiz para um Report com `findings: []` ou sem-substantive-verdict, sem ambiguidade. Auditor downstream (humano, SDR β, audit script) distingue "Triager pulou", "Detector achou zero candidatos", "Matcher devolveu tudo not_applicable", e "tem findings substantivos" sem inferir a partir do shape — o token declara.

### 3.2 Schema do finding individual

Cada finding é discriminated union por `verdict`. Estrutura comum seguida de campos específicos por verdict.

**Campos comuns (todos os vereditos).**

```python
{
    "file": <str>,
    "line": <int>,
    "snippet": <str>,
    "rule_id": <str>,
    "data_categories": [<str>, ...],
    "operation_type": "collection",  # MVP v0.1.0 per ADR-0007
    "verdict": <str>,
    "policy_clause_ref": "POL-NNN",  # obrigatório em todos 4 verdicts
                                      # (DD-21 ratificado PR #66; preservado
                                      # verbatim do output do policy-reader
                                      # check_applicability per canonical §4.3)
    "policy_schema_version": "0.1.0",
    "policy_version": "<...>",
    "legal_framework": "LGPD",
    "requires_human_review": <bool | undefined>,  # opcional
}
```

**Verdict `compliant`** (handling consistente com cláusula).

```python
{
    ...common,
    "verdict": "compliant",
    "evidence": "<texto curto>",
}
```

**Verdict `violation_candidate`** (handling contradiz cláusula).

```python
{
    ...common,
    "verdict": "violation_candidate",
    "evidence": "<texto identificando o ponto de contradição>",
    "contradicted_requirement": "R1",  # sub-id; opcional
}
```

**Verdict `indeterminate`** (depende de dimensão fora da análise estática).

```python
{
    ...common,
    "verdict": "indeterminate",
    "verification_scope": {
        "dimension": "<token de SCHEMA.md>",
        "prescribed_treatment": "<token de control.yaml>",
        "verification_target": "<texto em pt indicando onde verificar>",
    },
}
```

**Verdict `not_applicable`** (cláusula não governa este contexto).

```python
{
    ...common,
    "verdict": "not_applicable",
    "reason": "<texto explicando por que a cláusula não governa>",
    # policy_clause_ref OBRIGATÓRIO em not_applicable (DD-21 ratificado PR #66):
    # presença incondicional preserva audit trail substantivo — auditor LGPD
    # Art. 37 / SDR β precisa identificar qual cláusula foi avaliada-e-descartada,
    # não apenas que algum veredito não-aplicável foi emitido.
}
```

### 3.3 Provenance trinca top-level + per-finding

Trinca de provenance (`policy_schema_version`, `policy_version`, `legal_framework`) aparece em **dois loci** do Report payload: top-level (provenance do run inteiro) e per-finding (redundante, propagada verbatim de cada veredito do Matcher).

A redundância é **deliberada**. RF-009 descritiva literal exige presença em "todo veredito emitido pelo sistema" + no header do Report. Custo da redundância: ~3 campos × N findings de overhead JSON. Ganho: (a) audit isolation — single finding extraído (e.g., para investigação de incidente, ou snapshot em ticket) preserva sua provenance; (b) detecção de inconsistência — coordinator/handler cross-check de igualdade entre top-level e per-finding (§4.8) sinaliza payload corrompido.

### 3.4 Ordering de findings

Reporter **preserva ordem verbatim** do array `findings` emitido pelo Matcher. Reporter **NÃO** re-sort por `policy_clause_ref`, por file/line, por verdict, ou por qualquer outro critério. Reorder é responsabilidade de consumer downstream (PR comment renderer, SDR β serializer), não do Reporter. Ordem upstream é determinística por construção: Matcher itera candidatos do Classifier, que itera output do Detector, que itera diff do Semgrep. Determinismo audit-replayable preservado.

### 3.5 Variantes por `run_outcome`

`run_outcome` é discriminador de outcome do run inteiro; carrega afirmação semântica forte sobre o estado dos findings. Tabela de correspondência:

| `run_outcome`                | `findings` content                        | `triager_skip_reason` |
|------------------------------|-------------------------------------------|------------------------|
| `success_with_findings`      | pelo menos 1 com verdict ∈ {compliant, violation_candidate, indeterminate} | `None` |
| `success_no_candidates`      | `[]` (Detector achou zero candidatos)     | `None` |
| `success_all_not_applicable` | todos com `verdict == "not_applicable"` (e.g., todos `operation` ≠ `collection` per ADR-0007) | `None` |
| `skipped_by_triager`         | `[]` (caminho skip; sem Detector/Classifier/Matcher invocados) | `<str>` |

Algoritmo determinístico de derivação (executado pelo **coordinator em Python**, não pelo Reporter; Reporter recebe pré-computado):

```python
def derive_run_outcome(
    triager_skip_reason: str | None,
    candidates_count: int,
    matcher_findings: list[Finding],
) -> RunOutcome:
    if triager_skip_reason is not None:
        return "skipped_by_triager"
    if candidates_count == 0:
        return "success_no_candidates"
    substantive = {"compliant", "violation_candidate", "indeterminate"}
    if not any(f.verdict in substantive for f in matcher_findings):
        return "success_all_not_applicable"
    return "success_with_findings"
```

### 3.6 Casos que parecem erro mas não são

- **`findings: []` em `success_no_candidates`** — Detector achou zero candidatos; pipeline atravessa normalmente até Reporter. Não é erro.
- **`findings: []` em `skipped_by_triager`** — Triager pulou o run; pipeline pula §3.2-§3.4 mas atravessa §3.5 normalmente. Não é erro.
- **`findings` contendo apenas vereditos `not_applicable` (`success_all_not_applicable`)** — Matcher avaliou todos os candidatos como fora de escopo MVP. Não é erro; é design ADR-0007. Run válido.
- **`triager_skip_reason: None` quando `run_outcome ≠ skipped_by_triager`** — null é correto; presença do campo top-level é incondicional, valor é None nos outros três outcomes.
- **`requires_human_review` ausente em finding** — campo é opcional; Reporter propaga quando Matcher emite, omite quando Matcher omite. Ausência ≠ false.

## 4. Tool `emit_report`

### 4.1 Naming e resolução MCP

A tool resolve para o handle **`mcp__reporter_tools__emit_report`** — namespace gerado pelo runtime SDK a partir da chave do dict `mcp_servers={"reporter_tools": reporter_sdk_server}` aplicado ao nome do tool registrado via `@tool("emit_report", ...)`. Padrão canônico: *"The key in mcpServers becomes the {server_name} segment in each tool's fully qualified name: mcp__{server_name}__{tool_name}."*

Underscore preventivo em `reporter_tools` elimina risco de parser do SDK interpretar mal hyphens no triple-pattern `mcp__<name>__<tool>` (smoke-test #38 TC3 ratifica que `mcp__test_tools__echo` resolve sem quirks).

### 4.2 Tool description (canônica)

Texto canônico em inglês, sem markdown:

```python
EMIT_REPORT_DESCRIPTION = (
    "Emit the final aggregated Report JSON for the current pull request "
    "analysis run. The payload must be a complete Report object matching "
    "the declared schema, including the provenance triple, summary counts, "
    "run_outcome discriminator, and all findings preserved verbatim from "
    "the Matcher output. Use this tool exactly once per query. After "
    "successful invocation, end the turn — do not call again. Do not "
    "synthesize or modify findings."
)
```

### 4.3 `inputSchema`

JSON Schema dict, gerado via `ReportPayload.model_json_schema()` na factory `create_reporter_server`. `ReportPayload` é Pydantic v2 model espelhando a estrutura de §3.1 + §3.2, residindo em `src/coordinator/models.py` (a criar; locus pinado em §1.5). Fields:

| Campo                     | Tipo                                      | Obrigatório | Origem |
|---------------------------|-------------------------------------------|-------------|--------|
| `report_id`               | `str` validado contra UUID v4 regex (`^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`); falha vira `PYDANTIC_VALIDATION` | sim | coordinator (gerado via `uuid.uuid4()` em §3.0) |
| `report_schema_version`   | `str` (semver regex)                       | sim         | pinado em `src/coordinator/constants.py` |
| `policy_schema_version`   | `str` (semver regex)                       | sim         | coordinator (top-level, lido via `policy-reader` no startup); Matcher via `check_applicability` (per-finding) |
| `policy_version`          | `str` (semver regex)                       | sim         | coordinator (top-level, header da Política); Matcher via `check_applicability` (per-finding) |
| `legal_framework`         | `Literal["LGPD"]` no MVP v0.1.0 (per ADR-0007); bump para `Literal["LGPD", "GDPR", ...]` em versões futuras é minor da spec | sim | coordinator (top-level, header da Política); Matcher via `check_applicability` (per-finding) |
| `run_outcome`             | `Literal[...4 tokens]`                    | sim         | coordinator |
| `triager_skip_reason`     | `str \| None`                             | sim (None ok) | Triager |
| `scope`                   | `dict` (opaco — não validado por Pydantic model dedicado no MVP; ver §8.4 decisões deferidas) | sim | coordinator |
| `summary`                 | `SummaryModel`                            | sim         | coordinator |
| `findings`                | `list[Finding]` (discriminated union)     | sim         | Matcher |

`SummaryModel` carrega `counts` (4 ints, zeros explícitos) + `total` (int com `Field(ge=0)`; cross-check via `model_validator` contra sum). `Finding` é discriminated union por `verdict`. `extra='forbid'` em todos os modelos — campos não-declarados produzem `ValidationError` no parsing.

### 4.4 Output em sucesso

Handler retorna `dict[str, Any]` no formato MCP `CallToolResult`. Em sucesso:

```python
{
    "content": [
        {"type": "text", "text": "Report emitted: report_id=<uuid>, findings=<n>"}
    ],
    "structuredContent": {
        "report_id": "<uuid>",
        "path": "<run_path>/99-report.json",
        "finding_count": <int>,
    },
}
```

Wire format Option B (ADR-0002 §Decision 5): `is_error: false` discriminado por **ausência** de `errorCode` em `structuredContent`. Não é necessário declarar `is_error: false` explicitamente.

### 4.5 Output em erro

Em validation failure (Pydantic falha, cross-check falha, ou `report_id` mismatch):

```python
{
    "content": [
        {"type": "text", "text": "<message humana em pt>"}
    ],
    "structuredContent": {
        "errorCode": "<CODE>",
        "message": "<message humana em pt>",
        "isRetryable": <bool>,
        "details": {...},
    },
    "is_error": True,  # snake_case Python idiom per .claude/rules/sdk-mcp-conventions.md
                       # (claude-agent-sdk @tool handler layer; SDK traduz para
                       # isError camelCase no wire MCP automaticamente)
}
```

Codes específicos do handler em §6.3. Retry strategy: modelo recebe envelope com `is_error: True`, tenta novo emit_report com payload corrigido. Cap em `max_turns=3`.

### 4.6 `ToolAnnotations` declaradas

Declaradas no `@tool` decorator:

```python
@tool(
    "emit_report",
    EMIT_REPORT_DESCRIPTION,
    ReportPayload.model_json_schema(),
    annotations=ToolAnnotations(
        readOnlyHint=False,      # side effect: grava 99-report.json
        destructiveHint=False,   # não destrói nem modifica estado externo
        idempotentHint=False,    # multiple invocations não são idempotentes
        openWorldHint=False,     # não interage com mundo externo
    ),
)
```

`ToolAnnotations` importada via `from claude_agent_sdk import ToolAnnotations` (re-export do `mcp.types`). Annotations são sinais ao modelo, não enforcement — enforcement real está em tool authorization (§1.4) + handler validation (§4.8).

### 4.7 Dual sink: handler grava + coordinator captura

**Sink #1 — Handler grava `99-report.json` no `run_path`.** Audit/CI artifact. Locus de persistência para SDR β downstream, exercise scripts, e GitHub Action. Atomic write-then-rename.

**Sink #2 — Coordinator captura via `ToolUseBlock.input`.** Canal canônico de retorno ao caller. Coordinator inspeciona o message stream da `query()`, localiza `ToolUseBlock` com `block.name == "mcp__reporter_tools__emit_report"`, extrai `block.input` (que contém os argumentos exatos passados pelo modelo à tool — payload do Report).

**Esclarecimento load-bearing.** Canal de captura é `ToolUseBlock.input`, **não** `ToolResultBlock.content` — porque `block.input` é o que o modelo **emitiu** como argumentos (=payload do Report); `ToolResultBlock` carrega o que o handler **retornou** ao modelo (=ack de signaling, §4.4). Coordinator quer o payload, não o ack. `return` do handler é canal de signaling ao modelo, não canal de captura; coordinator ignora o return value e só inspeciona `ToolUseBlock.input`.

### 4.8 Factory pattern e closure capture

Factory `create_reporter_server(run_path, expected_report_id)` em `src/coordinator/tools.py`:

```python
def create_reporter_server(
    run_path: Path,
    expected_report_id: str,
) -> McpSdkServerConfig:
    """Build an in-process MCP server for the Reporter, scoped to
    the given run_path scratchpad directory and report_id.

    Closure captures both. Handler writes 99-report.json to run_path
    and validates payload.report_id == expected_report_id.
    """

    @tool(
        "emit_report",
        EMIT_REPORT_DESCRIPTION,
        ReportPayload.model_json_schema(),
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )
    async def emit_report_handler(args: dict[str, Any]) -> dict[str, Any]:
        # Step 1: Pydantic validation
        try:
            payload = ReportPayload.model_validate(args)
        except ValidationError as exc:
            return _validation_error_envelope(exc)

        # Step 2: Cross-check #4 — report_id matches expected (closure)
        if payload.report_id != expected_report_id:
            return _error_envelope(
                error_code="REPORT_ID_MISMATCH",
                message=f"Expected report_id {expected_report_id}, got {payload.report_id}.",
                is_retryable=False,
                details={"expected": expected_report_id, "got": payload.report_id},
            )

        # Step 3: Cross-checks intra-handler (#1-#3)
        cross_check_error = _run_cross_checks(payload)
        if cross_check_error is not None:
            return cross_check_error

        # Step 4: Atomic write-then-rename
        report_path = run_path / "99-report.json"
        _atomic_write_json(report_path, payload.model_dump(mode="json"))

        # Step 5: Success envelope
        return _success_envelope(
            report_id=payload.report_id,
            path=report_path,
            finding_count=len(payload.findings),
        )

    return create_sdk_mcp_server(
        name="reporter_tools",
        version="0.1.0",  # alinhado com pre-1.0 do projeto
        tools=[emit_report_handler],
    )
```

Quatro cross-checks intra-handler (cross-check #3 do draft 0.2.0 — vocabulary membership — foi **removido** em #42 por contradizer §2.4 passthrough principle + §8.3 fronteira epistêmica; vocab validation é semântica do Matcher upstream, não shape do Reporter):

1. **`policy_clause_ref` format regex** — campo em todos 4 verdicts casa `^POL-\d{3}$`; errorCode `CLAUSE_REF_FORMAT` (renomeado de `CLAUSE_ID_FORMAT` per DD-21 ratificado PR #66).
2. **Trinca top-level == per-finding** — `policy_schema_version`, `policy_version`, `legal_framework` idênticos em todos os loci.
3. **`summary.counts` casa com agregação real** — agregação por verdict bate com declared; `summary.total == sum(counts.values())`. Split em dois errorCodes (`COUNTS_DISAGREE_WITH_FINDINGS` e `TOTAL_NOT_SUM_OF_COUNTS`) para triage downstream mais limpo.
4. **`report_id` matches `expected_report_id`** — closure capture per Step 2 acima.

Invocada pelo coordinator em §3.0 (companion edit pendente — adicionar bullet do factory call lá; ver §10.5):

```python
# coordinator.py §3.0
run_id = str(uuid.uuid4())
run_path = SCRATCHPAD_ROOT / f"run-{run_id}"
run_path.mkdir(parents=True, exist_ok=True)
reporter_sdk_server = create_reporter_server(run_path, run_id)
# Reuse reporter_sdk_server em §3.5 stage Reporter
```

### 4.9 Order de operações no handler

Validate → cross-check → write → return. Atomicidade write-then-rename garante que `99-report.json` no filesystem nunca está corrompido ou parcialmente escrito. **Windows-native:** `_atomic_write_json` usa `os.replace(tmp, final)` (não `os.rename`) — `os.rename` falha em Windows se destino existe; `os.replace` é cross-platform atomic e overrides destino existente. Per ADR-0011 e `.claude/rules/windows-tooling.md`, todo I/O do projeto assume Windows-native canônico.

## 5. System prompt

### 5.1 Texto canônico

`REPORTER_SYSTEM_PROMPT` em inglês (ADR-0006), declarado em `src/coordinator/system_prompts.py` (a criar; locus pinado em §1.5). Estrutura em XML tags per recomendação Anthropic prompt engineering oficial (*"Anthropic's Claude model is particularly effective at following XML-style prompts"*) + 1 few-shot exemplar:

```python
REPORTER_SYSTEM_PROMPT = """You are the Reporter subagent, the terminal stage of a code-review pipeline that evaluates pull requests for compliance with a versioned Data Protection Policy.

<role>
Your sole responsibility is to call the `emit_report` tool exactly once, passing as input the complete Report payload assembled from the consolidated state provided in the user message.
</role>

<input>
The user message contains a JSON object with the consolidated state pre-computed by the coordinator. The object includes: `report_id`, `report_schema_version`, the provenance triple (`policy_schema_version`, `policy_version`, `legal_framework`), `run_outcome`, `triager_skip_reason`, `scope`, `summary`, and `findings`. All values are final — do not modify, recompute, infer, or synthesize any of them.
</input>

<task>
Construct the Report payload by copying the provided fields verbatim into the structure expected by the `emit_report` input schema. Call `emit_report` with the resulting payload. End your turn immediately after the tool call.
</task>

<constraints>
- Do not recompute `run_outcome` from `findings` — use the value provided.
- Do not recompute `summary.counts` or `summary.total` from `findings` — use the values provided.
- Do not reorder, filter, deduplicate, or modify the `findings` array.
- Do not synthesize evidence, reason, or verification_target text.
- Do not omit fields. Every field in the input must appear in the Report payload.
- Call `emit_report` exactly once. After the call returns successfully, end your turn — do not call the tool again.
- If `emit_report` returns an error envelope (`is_error: true`), inspect the errorCode and details, correct the payload, and retry. Do not retry more than two times.
</constraints>

<example>
<example_input>
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_schema_version": "0.1.0",
  "policy_schema_version": "0.1.0",
  "policy_version": "1.2.0",
  "legal_framework": "LGPD",
  "run_outcome": "success_with_findings",
  "triager_skip_reason": null,
  "scope": {"pr_number": 42, "repo": "example/app"},
  "summary": {
    "counts": {"compliant": 1, "violation_candidate": 1, "indeterminate": 0, "not_applicable": 1},
    "total": 3
  },
  "findings": [
    {
      "file": "auth.py", "line": 14, "snippet": "db.users.insert(email=email)",
      "rule_id": "DATA-001", "data_categories": ["email"], "operation_type": "collection",
      "verdict": "violation_candidate",
      "policy_clause_ref": "POL-005",
      "evidence": "Coleta direta de email sem guard de consentimento.",
      "contradicted_requirement": "R1",
      "policy_schema_version": "0.1.0", "policy_version": "1.2.0", "legal_framework": "LGPD"
    },
    {
      "file": "marketing.py", "line": 22, "snippet": "subscribe(email)",
      "rule_id": "DATA-001", "data_categories": ["email"], "operation_type": "collection",
      "verdict": "compliant",
      "policy_clause_ref": "POL-005",
      "evidence": "Coleta precedida por check_marketing_consent guard.",
      "policy_schema_version": "0.1.0", "policy_version": "1.2.0", "legal_framework": "LGPD"
    },
    {
      "file": "analytics.py", "line": 8, "snippet": "cache.set(session_id, ts)",
      "rule_id": "DATA-002", "data_categories": ["session_id"], "operation_type": "collection",
      "verdict": "not_applicable",
      "policy_clause_ref": "POL-005",
      "reason": "session_id não é dado de identificação pessoal; POL-005 governa nome/CPF/email/etc.",
      "policy_schema_version": "0.1.0", "policy_version": "1.2.0", "legal_framework": "LGPD"
    }
  ]
}
</example_input>

<example_tool_call>
emit_report({
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_schema_version": "0.1.0",
  "policy_schema_version": "0.1.0",
  "policy_version": "1.2.0",
  "legal_framework": "LGPD",
  "run_outcome": "success_with_findings",
  "triager_skip_reason": null,
  "scope": {"pr_number": 42, "repo": "example/app"},
  "summary": {
    "counts": {"compliant": 1, "violation_candidate": 1, "indeterminate": 0, "not_applicable": 1},
    "total": 3
  },
  "findings": [
    {... same 3 findings, verbatim ...}
  ]
})
</example_tool_call>
</example>

<output_format>
The Report payload is your only deliverable. You do not produce free-form text in your final turn — only the `emit_report` tool call.
</output_format>"""
```

### 5.2 Behaviors explícitos

Quatro behaviors load-bearing materializados:

1. **Anti-narração.** *"End your turn immediately after the tool call"* + *"You do not produce free-form text in your final turn"*. Sem isso, o modelo verbaliza naturalmente "I can't ... with the tools available to me" (observado smoke-test #38b).
2. **Anti-síntese.** Múltiplas asserções em `<constraints>`: *"do not modify, recompute, infer, or synthesize"*, *"do not synthesize evidence, reason, or verification_target text"*. Redundância deliberada — cada asserção captura um modo de falha distinto.
3. **Single emit.** *"Call `emit_report` exactly once"* + *"After the call returns successfully, end your turn — do not call the tool again"*. Coordinator inspeciona stream para detectar múltiplas invocações como anti-pattern (`MULTIPLE_REPORT_EMISSIONS`).
4. **Retry budget.** *"If `emit_report` returns an error envelope, inspect the errorCode and details, correct the payload, and retry. Do not retry more than two times."* Coordinator `max_turns=3` cap (initial call + 2 retries).

### 5.3 Few-shot strategy

Few-shot exemplar único do caminho normal incluído em §5.1. Cobre 3 dos 4 verdicts (compliant, violation_candidate, not_applicable); indeterminate fica implícito via schema. Justificativa per Anthropic prompt engineering oficial: *"By providing 2-5 well-crafted input/output examples, you dramatically improve accuracy and consistency, especially for structured outputs."*

Pivot para 4-shot completo (1 per verdict, incluindo indeterminate) se Gate 5 (smoke-test pré-implementação do system_prompt — ver §10.3) mostrar inventiveness em variantes pouco representadas. Reversibilidade preservada — adicionar terceiro example block dentro de `<example>` é refactor pequeno.

### 5.4 Unified prompt — sem branch conditional para skip path

O prompt não trata skip path como caso especial. Mesma instrução ("copy-verbatim do user message; call emit_report once") opera em ambos os caminhos. Diferenças entre normal e skip são apenas nos valores do input JSON (`run_outcome`, `triager_skip_reason`, `findings`), não na lógica do Reporter.

**Forward ref.** A defesa do prompt unified depende de coordinator §3.1 montar o input JSON do skip path com a mesma estrutura top-level do normal path (mesmas chaves, valores zerados/None onde aplicável). Estrutura mostrada em §2.3 presume essa invariante. Triager spec (a redigir, sessão pós-Reporter+sanity) ratifica a invariante ou força pivot para conditional prompt; revisão de §5.4 a re-confirmar nesse momento.

## 6. Error handling

### 6.1 Estrutura canônica do envelope

Convenção do projeto (ADR-0002 §3 Option B): quatro campos canônicos em `structuredContent`, discriminados por presença de `errorCode`:

```python
{
    "errorCode": "<CONSTANTE_EN>",
    "message": "<prosa pt-br>",
    "isRetryable": <bool>,
    "details": {...},
}
```

`content[0].text` reproduz `message` em prosa. `is_error: True` no top-level (snake_case Python idiom per `.claude/rules/sdk-mcp-conventions.md`; SDK traduz para `isError` no wire MCP) quando há `errorCode` em `structuredContent`; `is_error: False` (ou ausente) quando não há.

### 6.2 Classes de erro do Reporter

Três classes herdadas de ADR-0002:

- **validation** — payload falha validação intra-handler (Pydantic schema, cross-checks). `isRetryable=False` na maioria; excepcionalmente `True` se erro é em campo derivado que o modelo pode reconstruir.
- **business** — invariante de domínio violada (multiple emit, report_id mismatch). `isRetryable=False`.
- **system** — falha de I/O (scratchpad write fail), permission denial estrutural. `isRetryable=False`.

### 6.3 Família de errorCodes intra-handler

Erros emitidos pelo handler `emit_report`:

| `errorCode`                       | Classe     | `isRetryable` | Quando ocorre |
|-----------------------------------|------------|---------------|---------------|
| `PYDANTIC_VALIDATION`             | validation | False         | `ReportPayload.model_validate(args)` levanta `ValidationError`. |
| `CLAUSE_REF_FORMAT`               | validation | False         | Cross-check #1: campo `policy_clause_ref` não casa `^POL-\d{3}$` em algum finding. |
| `PROVENANCE_MISMATCH`             | validation | False         | Cross-check #2: trinca top-level ≠ trinca per-finding. |
| `COUNTS_DISAGREE_WITH_FINDINGS`   | validation | False         | Cross-check #3a: `summary.counts` não casa com agregação real dos `findings` por `verdict`. |
| `TOTAL_NOT_SUM_OF_COUNTS`         | validation | False         | Cross-check #3b: `summary.total ≠ sum(counts.values())`. |
| `REPORT_ID_MISMATCH`              | business   | False         | Cross-check #4: `payload.report_id ≠ expected_report_id` (closure capture). |
| `SCRATCHPAD_WRITE_FAIL`           | system     | False         | I/O falha ao escrever `99-report.json` no `run_path`. |

Split de `COUNTS_MISMATCH` em dois codes (`COUNTS_DISAGREE_WITH_FINDINGS` + `TOTAL_NOT_SUM_OF_COUNTS`) simplifica triage downstream — cada errorCode aponta direto para causa raiz distinta (bug no coordinator pre-compute vs bug em `derive_summary_total`).

### 6.4 Família de errorCodes do coordinator (Reporter stage)

Erros levantados pelo coordinator pós-loop ao inspecionar o stream:

| Exception                       | Sinal observável                                                | `isRetryable` |
|---------------------------------|------------------------------------------------------------------|----------------|
| `ReporterPermissionDenied`      | `final_result.permission_denials != []`                          | False          |
| `ReporterTurnsExhausted`        | `final_result.subtype == "error_max_turns"`                      | True (com `max_turns` maior) |
| `ReportNotEmitted`              | `subtype == "success"` E `emit_report_seen == False` E `denials == []` | False    |
| `MultipleReportEmissions`       | Múltiplos `ToolUseBlock` com `name == "mcp__reporter_tools__emit_report"` no stream | False |
| `MalformedToolUseBlock`         | `ToolUseBlock` sem `.input` attribute (SDK version incompat).    | False          |
| `CoordinatorStreamFailure`      | Exception levantada durante `async for` sem `ResultMessage` capturado. | False  |

### 6.5 Discrimination ordering

Coordinator §3.5 + §5 documentam a ordem canônica de discriminação pós-loop:

```
1. denials != []                          → ReporterPermissionDenied
2. subtype == "error_max_turns"            → ReporterTurnsExhausted
3. emit_report_seen == False               → ReportNotEmitted
4. (else success)                           → return report_payload
```

**Corolário sobre `permission_denials` interpretation** (per PR #67 side finding). `permission_denials` é signal de **tentativa fora de allowlist**, não signal de **lockdown funcionando**. Sob `tools=[]` (lockdown ativo per Gate 6), modelo nem tenta built-ins porque eles não estão no contexto — `permission_denials` permanece vazio em runs bem-sucedidos. Confirmação positiva de lockdown funcionando requer combinação de três sinais ortogonais: (a) `permission_denials == []`, (b) ausência de invocation de tool fora do allowlist no stream, (c) opcionalmente verbalização de ausência no AssistantMessage em runs forçados ao limite. `permission_denials` populado indica que modelo tentou tool fora do allowlist mas dentro do contexto — útil para diagnose, não para confirmação de lockdown.

> 💡 **Conceito Claude relevante (Domínio 5 — Context Management & Reliability):** structured error metadata via três axis de discriminação ortogonais: (1) classe (validation/business/system), (2) sinal observável (denials/subtype/emit_seen), (3) retryability. Audit downstream distingue causa raiz a partir do `errorCode` nominalmente, não a partir de exception type hierarchy ou shape heuristics.

### 6.6 Anti-pattern explícito

Coordinator **NUNCA** usa `num_turns == max_turns_cap` ou `stop_reason` para discriminar erros do Reporter (AC-4 #38b empirical: `num_turns == cap + 1` ao hit `error_max_turns`, e `stop_reason` pode ser `None` mesmo em paths de sucesso). Discriminação é sempre via `subtype` + `permission_denials` + `emit_report_seen` filter por `block.name`.

### 6.7 Casos que parecem erro mas não são

- **`ToolSearch` no message stream antes de `emit_report`** — SDK tool search está ON por default para `tools=None`; mas sob `tools=[]` per Gate 6, ToolSearch é skipped (turn economy benefit). Coordinator filtra por `block.name == "mcp__reporter_tools__emit_report"` defensivamente — sob `tools=[]` o filter passa a ser **defesa preventiva** contra futuros built-in tool blocks intermediários introduzidos por versões posteriores do SDK, não defesa contra ToolSearch corrente. Não-erro.
- **Multi-turn no caminho normal** — modelo pode chamar `emit_report`, receber envelope com `is_error: True` (e.g., `PYDANTIC_VALIDATION` por typo; nota: `is_error` aqui é snake_case do handler claude-agent-sdk per `.claude/rules/sdk-mcp-conventions.md`), corrigir, chamar novamente. `num_turns` pode ser 2 ou 3 em path válido (per aritmética canônica §1.5). Não-erro até `subtype == "error_max_turns"`.
- **`final_result.is_error == True` em path com `emit_report_seen == True`** — raro mas possível (SDK reporta `is_error` true em caso de transient API error mid-stream). Importante distinguir camadas: `final_result.is_error` é atributo da `ResultMessage` do SDK (snake_case ratificado em smoke-test `sdk_reporter_gates/` TC3); **distinto** do `is_error` do envelope retornado pelo handler em validation failure. Coordinator §5 preserva o payload capturado em `ToolUseBlock.input` e propaga o erro do SDK como audit; não anula o Report válido extraído antes.

## 7. Provenance e versionamento

### 7.1 Versão da spec

Esta spec carrega `spec_version: 0.3.0` no header. Bump de 0.2.0 → 0.3.0 reflete refinamento substantivo de contract surface pós-dois-reviews-independentes da sessão #42 (cross-check #3 removido, anotações tense forward-looking, invariante §2.2 reescrita, sintaxe few-shot corrigida, aritmética retry reconciliada, hardening UUID/Literal/Windows-replace, locus dos módulos pinado). Bumps prévios: 0.1.0 → 0.2.0 (sessão #41 — três achados de review). Convenção major/minor/patch:

- **Major** — break em contract surface (shape do `inputSchema`, shape do envelope de erro, semântica de tool authorization).
- **Minor** — adição de campos opcionais, novos errorCodes, refinamento de cross-checks, ampliação de behaviors, bump por aplicação de diretrizes forward-looking acumuladas, ou refinamento substantivo de contract surface mediante review pass.
- **Patch** — clarificação documentacional, exemplo adicional, reformatação.

Estabilização para 1.0 quando: (a) `_template-subagent.md` destilado, (b) implementação completa em `src/coordinator/tools.py` + system_prompt + tests acceptance, (c) review pass de spec contra implementação demonstrando paridade.

### 7.2 Versão do `report_schema`

Campo top-level **`report_schema_version: str`** no Report payload. Valor inicial **`"0.1.0"`** (alinhado com convenção pre-1.0 do projeto). Lifecycle paralelo a `spec_version` desta spec — mudanças que afetam o schema do Report bumpam ambos em sincronia.

Bump rules:

- **Major** (1.0.0 → 2.0.0): shape change do payload.
- **Minor** (0.1.0 → 0.2.0): campos opcionais adicionados, novos vereditos no enum.
- **Patch** (0.1.0 → 0.1.1): documentação / clarificação, sem mudança de wire.

Pinado como constante top-level em `src/coordinator/constants.py` (locus ratificado em §1.5):

```python
REPORT_SCHEMA_VERSION = "0.1.0"
```

### 7.3 Quartet de versioning no Report

O Report carrega top-level quatro versões:

| Campo                    | Origem                                       | Função |
|--------------------------|----------------------------------------------|--------|
| `report_schema_version`  | pinado nesta spec                            | shape do payload do Report |
| `policy_schema_version`  | header de `policy/policy.yaml`               | shape do schema da Política |
| `policy_version`         | header de `policy/policy.yaml`               | versão do conteúdo das cláusulas |
| `legal_framework`        | header de `policy/policy.yaml`               | jurisdição (LGPD, GDPR, ...) |

Consumer downstream parseia o Report e usa o quartet para: (i) determinar capabilities do parser; (ii) audit chain (qual Política gerou este finding); (iii) cross-version comparison de Reports históricos.

### 7.4 Mutabilidade durante execução

Os quatro campos do quartet são **fixos por instância do coordinator**. `report_schema_version` é pinado em build time; os três da Política são carregados em startup pelo `policy-reader` e propagados verbatim em cada veredito do Matcher. Nenhum hot-reload no MVP. Reload requer restart do MCP server `policy-reader` + nova execução do coordinator.

## 8. Não-objetivos e fronteiras

### 8.1 Não-objetivos do Reporter

1. **Não consolida estado upstream.** Estado é consolidado pelo coordinator antes do prompt ser montado.
2. **Não recomputa discriminadores.** `run_outcome`, `summary.counts`, `summary.total` vêm do coordinator (DD-7.3 inversão).
3. **Não reclassifica vereditos.** Cada `verdict` propaga verbatim do Matcher.
4. **Não re-ordena findings.** Ordem do Matcher preservada.
5. **Não filtra findings.** Mesmo findings com `verdict == "not_applicable"` aparecem no Report (audit trail per ADR-0007).
6. **Não invoca outros MCP servers.** `policy://*`, `mcp__policy-reader__*`, `mcp__semgrep-runner__*` não estão em `mcp_servers={...}` da §3.5; tools não estão em `allowed_tools`.
7. **Não usa built-ins.** `tools=[]` na configuração da stage §3.5 (per Gate 6 / PR #67) remove Read/Write/Edit/Bash/Grep/Glob do contexto do modelo. Reporter não tem capability de invocá-los.
8. **Não invoca `emit_report` mais de uma vez.** Múltipla invocação é halt em `MultipleReportEmissions`.
9. **Não escreve fora de `99-report.json` no `run_path`.** Handler única ação de filesystem é o atomic write do Report.
10. **Não gera identificadores.** `report_id` é injetado pelo coordinator via closure; Reporter recebe via input JSON, valida contra `expected_report_id`, propaga.

### 8.2 Não-objetivos do escopo do Report no MVP

- **Transformação Report → SDR CSV** (LGPD Art. 37 governance audit) — responsabilidade de consumer downstream β; fora do Reporter.
- **Posting de findings como inline review comments no GitHub PR** — responsabilidade da GitHub Action (Milestone D); fora do Reporter.
- **Bloqueio de merge** — RNF-002: sistema é informativo no MVP; bloqueio condicional é evolução pós-validação empírica de FPR.

### 8.3 Fronteira epistêmica do Reporter

Reporter consegue verificar formal-mente:

- Shape do payload contra `ReportPayload` schema (Pydantic).
- `policy_clause_ref` regex format `^POL-\d{3}$` (cross-check #1).
- Igualdade trinca top-level vs per-finding (cross-check #2).
- Consistência de `summary.counts` vs `findings` agregados (cross-check #3a + #3b).
- Match de `report_id` com `expected_report_id` (cross-check #4).

Reporter **NÃO** consegue verificar:

- Correção semântica de vereditos do Matcher.
- Existência factual da cláusula referenciada (fica em `policy-reader.get_clause`; cross-check estrutural pega formato inválido, não existência).
- Adequação da `evidence` ou `verification_target` em prosa.
- Correção do framework declarado em `legal_framework` (responsabilidade do `policy-reader`).

Falhas semânticas upstream propagam silenciosamente. Defesa em profundidade é responsabilidade de specs upstream — cada estágio valida seu próprio output antes de emitir. Reporter é último saneamento; não primeiro nem único.

### 8.4 Decisões deferidas

- **Pivô para `report_id ≠ run_id`** — reserva audit chain separation para uso pelo SDR β downstream. Requer ADR.
- **Pivô para `report_schema_version 1.0.0`** — atual `0.1.0` sinaliza pre-stability.
- **Pivot para 4-shot completo no `REPORTER_SYSTEM_PROMPT`** — Gate 5 (§10.3) decide.
- **Pivot para AgentDefinition** — evolução pós-MVP se paralelização ou roteamento dinâmico for introduzido.
- **Estruturação Pydantic de `scope`** (catch R2-F5 / #42) — atualmente `scope: dict` opaco, inconsistente com `extra='forbid'` dos demais modelos. Decisão entre (a) declarar `scope` como `dict[str, Any]` formalmente opaco com nota explícita do design choice em §4.3; (b) introduzir `ScopeModel` Pydantic com fields conhecidos (`pr_number`, `repo`, optional `commit_sha`). Postergada por requerer ratificação contra arch-overview §5.6 + REQUIREMENTS.md scope semantics. Decisão alvo: pré-implementação T11+ ou em Triager spec quando Triager scope-stamping for redigido.
- **Observabilidade / logging story** (catch R2-G1 / #42) — handler atual não declara logging behavior (o que loga, qual locus, qual formato structured logging). Para protótipo acadêmico cuja tese central é auditabilidade, isso é gap conspícuo. Decisão postergada por requerer design from scratch coordenado com coordinator §3.0 logging (também não declarado). Decisão alvo: redaction do coordinator-flesh-completo (sessão Chat #39+) ou nova seção §6.8 retroativa.
- **Schema migration story para Reports históricos** (catch R2-G4 / #42) — bump rules de `report_schema_version` declaradas em §7.2 mas tratamento de Reports mistos no histórico (MVP emitiu 0.1.0; v0.2.0 adiciona campo opcional — como parser de audit downstream lida?) não-especificado. Postergada por ser decisão de longo prazo; nota: SDR β downstream é responsável por handling cross-version, não Reporter — vale ratificar em ADR retroativo Milestone C ou em spec do SDR β quando este for redigido.
- **Callouts 💡 conceito-tag herdados pelo `_template-subagent.md`?** (catch R1-L3 / #42) — esta spec tem dois callouts ensaísticos em §1.4 referenciando exam guide canônico (defesa de TCC). Decisão de incluir como pattern estrutural do template depende de destilation pós-Triager-sanity (sessão Chat #42+).
- **`requires_human_review` semântica downstream** (catch R2-G5 / #42) — campo opcional propagado verbatim do Matcher; convenção de **quando** o Matcher emite (i.e., qual disjunção sobre `verdict` ou `verification_scope` triggers `requires_human_review: True`) não vive nesta spec — fica em Matcher spec a redigir (sessão Chat #38-#39 per ordem híbrida). Forward-ref análoga a §5.4 unified-prompt-vs-Triager-spec: ratificar consistência na redação do Matcher spec.

## 9. Critérios de aceitação

### 9.1 Happy-path scenarios

- [ ] **9.1.a** — `success_with_findings`: PR sintética dispara Detector → Classifier → Matcher → Reporter; Report emitido contém `run_outcome == "success_with_findings"`, `findings` não-vazio, ao menos um finding com `verdict ∈ {compliant, violation_candidate, indeterminate}`.
- [ ] **9.1.b** — `success_no_candidates`: PR sintética com diff vazio de coleta; Detector retorna `[]`; Report emitido contém `run_outcome == "success_no_candidates"`, `findings: []`, `summary.total == 0`.
- [ ] **9.1.c** — `success_all_not_applicable`: PR sintética com candidatos cujo `operation` ≠ `collection`; Matcher retorna vereditos `not_applicable`; Reporter emite Report com `run_outcome == "success_all_not_applicable"`, findings todos com `verdict == "not_applicable"` e `policy_clause_ref` presente em cada.
- [ ] **9.1.d** — `skipped_by_triager`: Triager decide `decision: "skip"`; Reporter invocado com `triager_skip_reason` populado; Report contém `run_outcome == "skipped_by_triager"`, `findings: []`, `triager_skip_reason == <razão>`.

### 9.2 Edge case scenarios

- [ ] **9.2.a** — Pydantic-invalid retry success: primeiro `emit_report` retorna `PYDANTIC_VALIDATION` `is_error: true`; modelo retry com payload corrigido; segundo emit_report sucesso; coordinator captura.
- [ ] **9.2.b** — Pydantic-invalid retry exhaustion (`ReporterTurnsExhausted`): payload corrompido em 3 invocações; `subtype == "error_max_turns"`; coordinator levanta `ReporterTurnsExhausted`.
- [ ] **9.2.c** — `MultipleReportEmissions`: system_prompt modificado para induzir múltiplas chamadas; coordinator detecta 2 `ToolUseBlock` com `block.name == "mcp__reporter_tools__emit_report"`; levanta `MultipleReportEmissions`.
- [ ] **9.2.d** — `ReportNotEmitted`: input malformed que faz modelo desistir; coordinator detecta `subtype == "success"` E `emit_report_seen == False` E `denials == []`; levanta `ReportNotEmitted`.
- [ ] **9.2.e** — `ReporterPermissionDenied`: test fixture com `allowed_tools=["Read"]` (sem `mcp__reporter_tools__emit_report`); Reporter tenta chamar tool; SDK denies via `dontAsk`; `permission_denials` populado; coordinator levanta `ReporterPermissionDenied`.
- [ ] **9.2.f** — `MalformedToolUseBlock`: fixture com SDK monkey-patched para retornar `ToolUseBlock` sem `.input` attribute; coordinator captura e levanta `MalformedToolUseBlock`. (Sinal de SDK version incompat; test defensivo, espera-se que nunca dispare contra SDK 0.2.87.)
- [ ] **9.2.g** — `CoordinatorStreamFailure`: fixture com `query()` levantando exception transient antes de `ResultMessage` ser emitido; coordinator captura e levanta `CoordinatorStreamFailure` preservando partial stream para audit.

### 9.3 Cross-check scenarios

- [ ] **9.3.a** — `CLAUSE_REF_FORMAT`: payload com `policy_clause_ref == "POL-12"` (sem zero-pad); handler detecta via regex; retorna `is_error: true` com errorCode `CLAUSE_REF_FORMAT`.
- [ ] **9.3.b** — `PROVENANCE_MISMATCH`: payload com `policy_version` top-level distinto do `policy_version` em um dos findings; handler cross-check #2 detecta.
- [ ] **9.3.c** — `COUNTS_DISAGREE_WITH_FINDINGS`: payload com `summary.counts.compliant: 5` mas `findings` contém apenas 3 compliant; handler cross-check #3a detecta.
- [ ] **9.3.d** — `TOTAL_NOT_SUM_OF_COUNTS`: payload com `summary.total: 12` mas `sum(counts.values()) == 10`; handler cross-check #3b detecta.
- [ ] **9.3.e** — `REPORT_ID_MISMATCH`: payload com `report_id` diferente do `expected_report_id`; handler cross-check #4 detecta.
- [ ] **9.3.f** — `CLAUSE_REF_FORMAT` em `not_applicable` (DD-21 rejection test): payload com finding `verdict: "not_applicable"` sem `policy_clause_ref` (campo omisso ou `null`); handler cross-check #1 rejeita com `CLAUSE_REF_FORMAT` (Pydantic discriminated union exige `policy_clause_ref` em todos 4 verdicts). Test confirma que presença incondicional do DD-21 é enforced em runtime, não apenas declarada em §3.2.

### 9.4 Provenance scenarios

- [ ] **9.4.a** — Trinca top-level idêntica a per-finding em payload válido (`success_with_findings`).
- [ ] **9.4.b** — `report_schema_version == "0.1.0"` em todos os Reports emitidos pelo MVP v0.1.0.
- [ ] **9.4.c** — `report_id == run_id` (UUID v4) em todos os Reports do MVP.
- [ ] **9.4.d** — `policy_clause_ref` presente em todos os findings de qualquer Report, incluindo findings com `verdict == "not_applicable"` (DD-21 ratificado).

### 9.5 Persistence scenarios

- [ ] **9.5.a** — Após emit_report bem-sucedido, `99-report.json` existe em `run_path` com conteúdo JSON-parseable casando o payload capturado.
- [ ] **9.5.b** — Write é atomic: crash mid-write deixa `.99-report.json.tmp` ou similar, nunca `99-report.json` parcial.

## 10. Cross-references

### 10.1 Source-of-truth artifacts

- **`docs/REQUIREMENTS.md`** — RF-006 (Report agregado em JSON estruturado), RF-009 (Provenance temporal e jurisdicional), RF-005 (Honestidade epistêmica via `indeterminate`). Amendments aplicados via PR #66 (DD-21).
- **`docs/architecture-overview.md`** — §4.3, §5.6, §5.7. Amendments aplicados via PR #66 (DD-21).
- **`docs/specs/subagents/coordinator.md`** — §2, §3.0, §3.5, §3.6, §5, §6, §7. Companion edits pendentes catalogadas em §10.5.
- **`docs/specs/policy-reader/canonical.md`** — §4.3 (`check_applicability` output shape; `policy_clause_ref` preservado verbatim).
- **`docs/DESIGN.md`** — separação de planos epistêmicos (tese central; sustenta DD-21).
- **`.claude/rules/sdk-mcp-conventions.md`** — `isError` (camelCase) vs `is_error` (snake_case) layer-aware.
- **Sync com `architecture-overview`** — patches consequentes desta spec ao arch-overview vivem em `coordinator.md` §10 (three-beats lifecycle), não aqui, per Rule 6 do coordinator §9. Companion edits ao próprio coordinator listados em §10.5.

### 10.2 ADRs aplicáveis

- ADR-0001 (stack canônica; amendment pendente para `claude-agent-sdk` dep).
- ADR-0002 (MCP conventions; Option B wire format).
- ADR-0005 (multi-cliente; trinca de provenance).
- ADR-0006 (language conventions).
- ADR-0007 (escopo MVP v0.1.0; `operation: collection`).
- ADR-0008 (task decomposition).
- ADR-0011 (Windows-stdio handle inheritance).
- ADR-0012 retroativo (a redigir) — cinco decisões load-bearing Milestone C.

### 10.3 Gates pré-implementação

**Gate 4 — Pydantic v2 `model_validator` em `SummaryModel`.** Confirmar que validator declarativo para cross-check #3b funciona em Pydantic 2.13.4. Smoke-test trivial (~5min).

**Gate 5 — Smoke-test do `REPORTER_SYSTEM_PROMPT`.** Antes de implementar coordinator §3.5 e Reporter stage para integração, rodar `query()` isolado com:
- `REPORTER_SYSTEM_PROMPT` da §5.1;
- payload sintético contendo os 4 verdicts (1 compliant + 1 violation_candidate + 1 indeterminate + 1 not_applicable) com campos variantes preenchidos;
- `mcp_servers={"reporter_tools": create_reporter_server(...)}`;
- `tools=[]`, `max_turns=3`.

Asserts: `subtype == "success"`; exatamente 1 `ToolUseBlock` com `block.name == "mcp__reporter_tools__emit_report"`; `block.input` casa o payload sintético verbatim (incluindo trinca per-finding, ordering, `policy_clause_ref` em todos 4 verdicts, `requires_human_review` quando presente); handler retorna sucesso. Se fail, adicionar 2 ou 3 few-shots adicionais ao `<example>` block para cobrir indeterminate explicitamente.

Tempo estimado: ~30min Code dedicado. Locus convencional do projeto: `scripts/smoke_tests/sdk_reporter_prompt/`.

**Nota sobre numeração de Gates.** Gates 4 e 5 desta spec usam numeração **local** à Reporter spec, não numeração contígua com Gates do projeto (Gate 1 = ToolUseBlock shape, em coordinator §11; Gate 6 = `tools=[]` semantics, em `scripts/smoke_tests/sdk_tools_empty_list/`). Numeração contígua project-wide seria refactor pos-#42 que adicionaria valor cosmético sem agregar a clareza local. Leitor cross-referencing entre specs encontra "Gate <N>" como rótulo local; cross-referência substantiva é via path do smoke-test, não via número.

### 10.4 DDs status pós-PR #66 e #67

| DD                                | Status                  |
|-----------------------------------|--------------------------|
| DD-1, DD-1.1, DD-1.2, DD-1.3      | incorporada              |
| DD-2 (summary counts)             | incorporada              |
| DD-3 (discriminated union)        | incorporada              |
| DD-3.3                            | ratchet por DD-21 (PR #66) |
| DD-3.5 (requires_human_review)    | incorporada              |
| DD-4 (provenance trinca)          | incorporada              |
| DD-5 family (handler details)     | incorporada              |
| DD-6 (tool description literal)   | incorporada              |
| DD-7.1 (few-shot)                 | invertida — incluído per Anthropic guide |
| DD-7.2 (anti-narração)            | incorporada              |
| DD-7.3 (Reporter passthrough)     | incorporada              |
| DD-7.4 (unified prompt)           | incorporada              |
| DD-9.1, DD-9.2                    | incorporada              |
| DD-10 family (error handling)     | incorporada              |
| DD-15 (report_id == run_id MVP)   | incorporada              |
| DD-16, DD-17                      | incorporada              |
| DD-18 (Matcher invariant locus)   | incorporada; coordinator §3.4 |
| DD-19 (findings ordering)         | incorporada              |
| DD-20 (`report_schema_version`)   | incorporada              |
| DD-21 (`policy_clause_ref`)       | **RATIFICADA — PR #66**  |
| DD-22 (SDK gaps)                  | dissolvida (gap era falso; ambos params no listing canônico) |
| Finding #3 (`tools=[]`)           | **RATIFICADO — PR #67**  |
| Finding #4 (isError/is_error)     | **RATIFICADO — rule scoped** |

### 10.5 Companion edits pendentes ao `coordinator.md`

Após esta spec ser ratificada, surgical edits ao coordinator:

1. **`docs/specs/subagents/coordinator.md` §3.4 e §3.5** — substituir `tools=["Read"]` por `tools=[]` per PR #67 evidência empírica. Sub-packaging ratificado em Chat #41: PR único pós-merge desta spec.
2. **`docs/specs/subagents/coordinator.md` §3.0** — coordinator §3.0 é sentença única separada por `;` (não lista de bullets). Inserir após o `;` que segue "cria `.scratchpad/run-<id>/`" a frase: "; instancia `reporter_sdk_server = create_reporter_server(run_path, run_id)` (factory de `src/coordinator/tools.py`; reuso desta instância em §3.5 stage Reporter)". (Reframe de #41 que prescrevia "adicionar bullet" — bullet structure não existe em §3.0 corrente.)
3. **`docs/specs/subagents/coordinator.md` §7** — substituir literal `"Emit the consolidated Report JSON"` por referência ao `EMIT_REPORT_DESCRIPTION` canônico (importado de `src/coordinator/constants.py`; symbol único como single source of truth, locus pinado em §1.5 desta spec).
4. **`docs/specs/subagents/coordinator.md` §7 (version arg)** — confirmar/alinhar `version="0.1.0"` em `create_sdk_mcp_server` call (consistente com §4.8 desta spec).
5. **`docs/specs/subagents/coordinator.md` §2** — alinhar enumeração da quíntupla canônica de lockdown aos 5 elementos explícitos decididos em §1.4 + §1.5 desta spec (`permission_mode`, `setting_sources`, `strict_mcp_config`, `allowed_tools`, `mcp_servers`), preservando a context restriction `tools=[]` declarada como **eixo ortogonal** availability vs denial-on-miss (não como sexto elemento da quíntupla). Sync mecânico pós-ratificação Reporter spec #41.
6. **`docs/specs/subagents/coordinator.md` §3.5** — atualizar comentário inline do filter `block.name == "mcp__reporter_tools__emit_report"` para refletir que sob `tools=[]` (post item 1 acima) ToolSearch é skipped; o filter passa a ser **defesa preventiva** contra futuros built-in tool blocks intermediários introduzidos por versões posteriores do SDK, não defesa contra ToolSearch ativo. Catalogado em #42 per Review 1 M4.

Sub-pacote total: ~6 edits, sub-30min Code work, defensável como PR único ao coordinator pós-ratificação desta spec.
