# triager

**spec_version**: 0.1.0

> Spec leve do subagent Triager. Segue a estrutura de `reporter.md` v0.3.0 como template hipótese; a destilação formal de `_template-subagent.md` ocorre na Fase 2 da sessão #43 após esta spec. Decisões de design ancoradas em `docs/architecture-overview.md` §3, §5.2 e §5.7, com validação empírica em `scripts/smoke_tests/sdk_output_format_lockdown/` (PR pre-Fase-0, mergeada antes desta autoria).

## 1. Identidade e propósito

### 1.1 Nome canônico

`triager`. Subagent. Não é MCP server, não expõe resources, não expõe tools customizadas.

### 1.2 Função

Decide se um pull request é relevante para análise de conformidade contra a Política carregada. Output: decisão binária `proceed | skip` acompanhada de razão estruturada (shape concreto em §3).

Não há requisito funcional nominado para o Triager em `docs/REQUIREMENTS.md`. O Triager aparece apenas obliquamente no critério de RF-006 (`docs/REQUIREMENTS.md:91`), que reconhece a lista `findings (possivelmente vazia se Triager decidiu skip ou se nenhum candidato foi detectado)`. A omissão "ou se nenhum candidato foi detectado" é semanticamente material: RF-006 reconhece duas causas independentes para `findings=[]` — skip do Triager ou ausência de candidatos do Detector. O Triager é uma dessas causas, não a única.

Razão da ausência de RF nominado: o Triager não materializa capacidade externa observável — é mecanismo interno de eficiência da pipeline, gatekeeping pré-análise para evitar invocação dos subagentes downstream (Detector, Classifier, Matcher, Reporter) em PRs sem potencial de tratamento de dados pessoais. A capacidade externa observável é o Report do RF-006; o Triager é peça do mecanismo que produz Report vazio (ou pipeline early-exit) sob condições de baixa-relevância detectada.

Referência canônica de design: o pattern de **ticket routing** documentado em `https://docs.anthropic.com/en/docs/about-claude/use-case-guides/ticket-routing` materializa o mesmo princípio (Claude classifica entrada não-estruturada em decisão estruturada para roteamento downstream). Diferenças: nosso domínio é PR diff em vez de ticket de suporte; nossa decisão é binária em vez de multi-categoria; nosso modelo de operação é parte de pipeline determinística (não state machine de tickets). Convergência: a doc canônica recomenda Claude Haiku 4.5 como modelo para o classificador — material informativo para futura reabertura de DD-T11 (ver §8.4).

### 1.3 Posição na arquitetura

Etapa 0 do fluxo descrito em `docs/architecture-overview.md` §3. Invocado pelo coordinator imediatamente após recebimento do PR scope inicial (PR refs, metadata), antes do Detector.

Tools permitidas: `Read` (sobre arquivos do diff) e `Glob` (para inspecionar paths alterados). Sem MCP servers, sem `Bash`, sem `Write`/`Edit`. Matriz canônica em `docs/architecture-overview.md` §5.7.

> 💡 **Conceito Claude relevante (Domínio 2 — Tool Design & MCP Integration, Task Statement 2.3).** A omissão deliberada de `Grep` neste subagent — apesar de `Read`+`Grep`+`Glob` ser listada explicitamente como pattern "Read-only analysis" na doc oficial do SDK (tabela "Common tool combinations" em `agent-sdk/subagents`) — é decisão arquitetural de single-responsibility per `docs/architecture-overview.md` §5.4: Grep está reservado ao Classifier, que o usa para inspeção fina de declarações de base legal em comentários e docstrings. O Triager opera em nível de path patterns e overview do diff; granularidade fina é responsabilidade downstream. Heterogeneidade per concern, não desvio inadvertido da combinação canônica.

Routing downstream da decisão emitida pelo Triager — `proceed` invoca Detector; `skip` é tratado conforme `coordinator.md` §3.1 — é responsabilidade exclusiva do coordinator e não é re-decidido nesta spec. O Triager declara seu output; o coordinator é autoritativo sobre o que faz com ele. Esta cláusula previne contradição com o estado mermaid de `docs/architecture-overview.md` §3, cujo patch pendente (`skip → END` → `skip → Reporter`) está catalogado em `docs/tasks.md` §Provisão MC-B e em `coordinator.md` §10.

### 1.4 Invocador e modo de invocação

Único invocador autorizado: **coordinator**, via `claude_agent_sdk.query()` em pattern A'' (system prompt direto em `ClaudeAgentOptions`, sem `AgentDefinition`). Pattern justificado em `coordinator.md` §1.4 (não-uso de `AgentDefinition` é decisão template-wide para o sistema multi-agente deste projeto).

Lockdown agent CI/CD-headless materializado pela **quíntupla canônica de denial-on-miss** (locus canônico de enumeração: `coordinator.md` §2; também referenciada em `reporter.md` §1.4):

1. `permission_mode="dontAsk"` — denial determinístico de tools fora do allowlist.
2. `setting_sources=[]` — isolamento de `CLAUDE.md`, output styles e demais settings de filesystem.
3. `strict_mcp_config=True` — confinamento ao `mcp_servers` declarado.
4. `allowed_tools=["Read", "Glob"]` — whitelist explícita.
5. `mcp_servers={}` — dict vazio neste subagent (sem MCP servers in-process nem out-of-process).

**Tools configuration — asymmetry deliberada vs Reporter.** Triager declara `tools=["Read", "Glob"]` (built-in tools do SDK necessárias para inspeção do diff). Contraste explícito com Reporter §1.5 que declara `tools=[]` (context restriction, per Gate 6 / PR #67) — Reporter substitui capacidade de built-ins por custom MCP tool `emit_report` via Branch A; Triager precisa de built-ins porque inspecionar o diff (Read/Glob) é parte do raciocínio, não capacidade substituível. Asymmetry per branch que o template-subagent (Fase 2) deve documentar: tools config é função do output mechanism e do tipo de inspeção que o subagent faz.

O `system_prompt` (role definition, texto canônico em §5.1) é categoria separada da quíntupla — coordinator.md §2 isola explicitamente role definition do conjunto denial-on-miss. Quíntupla governa *o que pode ser invocado e sob qual disciplina*; system prompt governa *o que o agente é*. Asymmetry categórica deliberada.

**Eixo ortogonal à quíntupla — structured contract via `output_format`** (específico do Triager Branch B, não compartilhado com Reporter):

```python
output_format = {
    "type": "json_schema",
    "schema": TriagerDecision.model_json_schema(),
}
```

Categoria semântica distinta dos 5 eixos da quíntupla: a quíntupla governa **denial-on-miss** (quais tools podem ser chamadas, sob qual permission discipline, com qual settings/MCP isolation); `output_format` governa o **shape do output** (validation-retry loop sobre o que o agente devolve ao caller). SDK valida `ResultMessage.structured_output` contra o schema e dispara retry automático em mismatch; em estouro de retries, retorna `ResultMessage` com `subtype="error_max_structured_output_retries"` (lista canônica completa de subtypes em §6.3). Validação empírica de coexistência dos 6 eixos sob SDK 0.2.87 em `scripts/smoke_tests/sdk_output_format_lockdown/`.

**Branch A vs Branch B — terminologia local desta família de specs.** Dois mecanismos diferentes para produzir output estruturado de um subagent:

- **Branch A** — output via **custom tool** definida por `@tool` + `create_sdk_mcp_server` (pattern do Reporter: `emit_report`). Apropriado quando há dual sink, closure capture de parâmetros runtime, ou side effect auditável (e.g., scratchpad write).
- **Branch B** — output via `output_format=json_schema` (pattern do Triager). Apropriado quando o subagent só devolve dado estruturado validado, sem side effect além da emissão. Validation-retry loop é responsabilidade do SDK, não do agente.

Decisão Branch A vs Branch B é per-subagent, calibrada por concern: Reporter precisa de dual sink (audit em scratchpad + capture no message stream) → Branch A; Triager devolve decisão estruturada efêmera consumida pelo coordinator → Branch B. Heterogeneidade per concern, não inconsistência (ver DD-T01).

> 💡 **Conceito Claude relevante (Domínio 4 — Prompt Engineering & Structured Output, Task Statements 4.2 + 4.3).** O `output_format=json_schema` materializa validation-retry loop como capability nativa do SDK, encapsulada no runtime em vez de implementada no agente. Pattern alternativo (custom tool via `@tool` + `create_sdk_mcp_server`, como Reporter usa para `emit_report`) permanece preferível quando há dual sink, closure capture de run-time parameters, ou side effects auditáveis. Match mechanism to concern.

### 1.5 Stack e governança

Stack: Python 3.12.7, `claude-agent-sdk` ≥ 0.2.87 (baseline empírico validado em smoke-tests Gate 1, Gate 6 e `sdk_output_format_lockdown`; piso definitivo a fixar em `pyproject.toml` na Provisão MC-E), `pydantic` 2.13.4.

**Modelo de inferência.** Claude Opus 4.7 com adaptive thinking (`thinking: {type: "adaptive"}`), herdado do default do coordinator. Escolha calibrada para fase de desenvolvimento e validação funcional: otimização de modelo (cost/latency via Haiku 4.5) é decisão deferida para pós-produção (ver DD-T11 em §8.4), seguindo o princípio de não introduzir variável adicional na investigação enquanto o sistema não estiver 100% funcional.

**Locus físico (implementação).** Triager mora em `src/subagents/triager/` (convenção `src/subagents/<name>/` per DD-T15 em §8.4). Esta convenção implica migration pendente do Reporter de `src/coordinator/` para `src/subagents/reporter/` — catalogada como Provisão MC-F em §10.5 (PR housekeeping pré-T11+).

**Locus de runtime.** O Triager **não** mantém estado próprio; cada invocação é uma `query()` independente, configurada em runtime pelo coordinator com o PR scope corrente como prompt input. Não há factory pattern, não há closure capture, não há in-process MCP server, não há arquivo persistente próprio. Diferença substantiva vs Reporter (`reporter.md` §1.5), que requer factory pattern para capturar `run_path` em closure devido ao dual sink — sob Branch B essa maquinaria toda some.

**Aritmética de turns substantivamente diferente do Reporter.** O Reporter usa `max_turns=3` (1 initial emit + até 2 retries do validation loop intra-handler). O Triager Branch B não tem locus intra-handler para retry — a validação contra o schema acontece no runtime do SDK, transparentemente ao agente. O orçamento de turns precisa cobrir: N invocações de `Read` (inspeção de arquivos do diff) + M invocações de `Glob` (resolução de paths alterados) + 1 produção final estruturada + retries implícitos do SDK em caso de mismatch contra schema. Smoke-test empírico (`scripts/smoke_tests/sdk_output_format_lockdown/`, side finding SF-3) registrou ~4 `AssistantMessage`s antes do `ResultMessage` para output trivial sem tool calls; PRs reais com inspeção de diff devem demandar consideravelmente mais.

Inclinação inicial: `max_turns=20` provisional. Cap generoso é deliberado para fase de calibragem (T11+) — permite observar distribuição real de turns em catálogo de PRs sintéticos (Provisão MC-D) antes de fixar piso definitivo. Cap baixo demais (e.g., 10) introduziria confound: estouros poderiam ser "PR precisava de mais turns" ou "loop não-produtivo", indistinguíveis sem evidência empírica. Pattern: measure-before-tune. Trade-off declarado: permissive-budget durante calibragem aceita risco de loops não-produtivos custarem mais turns em casos patológicos, em troca de sinal limpo na distribuição empírica. Ratchet down ao fim de T11+ se a distribuição empírica revelar piso seguro abaixo de 20 (ver DD-T06).

**Cap complementar — `max_budget_usd`.** A doc oficial do agent loop (`agent-sdk/agent-loop`) lista dois budgets complementares: `max_turns` (cap em round-trips de tool use) e `max_budget_usd` (cap em custo absoluto). Triager spec usa apenas `max_turns` no MVP. `max_budget_usd` fica como capability disponível mas não exercitada — possível instrumentação adicional em T11+ se observação empírica revelar correlação ruim entre número de turns e custo (e.g., PRs com arquivos grandes cuja inspeção via Read consome muito token por turn).

**Grammar compilation latency** (first-hit per schema). Doc oficial (`build-with-claude/structured-outputs`): "The first time you use a specific schema, there is additional latency while the grammar compiles. Automatic caching: Compiled grammars are cached for 24 hours from last use." Implicação: em CI workers efêmeros, primeiro PR analisado após cold start paga grammar compilation. Não-bloqueante para MVP; possível otimização futura via warm-up call (smoke-test trivial no início do worker para compilar grammar e popular cache).

> 💡 **Conceito Claude relevante (Domínio 1 — Agentic Architecture & Orchestration, Task Statement 1.1).** Loop termination tem dois mecanismos coexistentes neste subagent. (i) **Convergência semântica** via `output_format=json_schema`: o SDK encerra o agentic loop quando o modelo produz output que valida contra o schema declarado — stop implícito. (ii) **Budget hard** via `max_turns` (e/ou `max_budget_usd`): stop explícito por estouro. Os dois são complementares — (i) é o caminho feliz, (ii) é o cinto de segurança. Spec do Triager documenta a distinção para que callers (coordinator) saibam discriminar os subtypes de `ResultMessage` correspondentes (ver §6.3).

Governança: este spec é governado por ADR-0001 (stack canônica), ADR-0005 D4 (resource access scoping — Triager não consome `policy://vocabularies`), e companion-spec'd por `coordinator.md` §3.1 (Triager skeleton invocation) e `reporter.md` §1.4 (lockdown pattern compartilhado).

## 2. Input contract

### 2.1 Shape do input

O Triager recebe um único objeto de scope construído pelo coordinator a partir do trigger inicial (GitHub Action payload no MVP). Shape canônico:

```python
class TriagerInput(BaseModel):
    pr_number: int
    base_ref: str           # SHA ou ref nominado (e.g., "main")
    head_ref: str           # SHA ou ref nominado (e.g., "feature/x")
    repo_url: str           # URL HTTPS do repositório (não usado para fetch no MVP; provenance apenas)
```

Quatro campos mínimos, todos obrigatórios. Não há campos opcionais no MVP. Especificamente **ausente do input**:

- `changed_paths`. Decisão deferida (ver DD-T05). Triager descobre paths alterados via inspeção própria (`Glob` sobre o worktree do diff entre `base_ref` e `head_ref`); não recebe lista pré-computada. **Conflito conhecido com `docs/architecture-overview.md` §5.2** (que declara "Input. Diff do PR, lista de paths alterados"); companion edit pendente catalogado em §10.5.
- `pr_metadata` (autor, título, descrição). Reservado para extensão futura quando heurísticas semânticas sobre prosa do PR demonstrarem valor empírico em T11+. Não materializado no MVP.

A tipagem desta entrada como Pydantic BaseModel (variante (b) do espaço de design de `reporter.md` §8.4 "Estruturação Pydantic de scope" — Pydantic tipado vs dict opaco) fecha por construção a decisão deferida pelo Reporter spec. Esta spec ratifica a **abordagem** (Pydantic tipado); o **field set específico** (`{pr_number, base_ref, head_ref, repo_url}`) é definido por esta spec e supera a sugestão exploratória de field set hipotetizado em Reporter §8.4 (`{pr_number, repo, optional commit_sha}`). Adicionalmente, este spec compromete `Report.scope = TriagerInput` literalmente — Report.scope adota exatamente os 4 campos definidos aqui (per Provisão MC-F bullets 3-5 em §10.5), criando versioning coupling deliberado entre TriagerInput e Report payload. Companion edits cross-doc para alinhar Reporter §3.1, §4.3 e §8.4 catalogados em §10.5 sob Provisão MC-F.

### 2.2 Construção do prompt pelo coordinator

O coordinator constrói o prompt da `query()` chamando `build_triager_prompt(pr_metadata)` definido em `coordinator.md` §3.1 (locus canônico autoritativo). Assinatura monolítica recebe o objeto `TriagerInput` como `pr_metadata` e expande os 4 campos internamente no template definido em §5.1; não há serialização para JSON intermediário, os campos viram texto natural no prompt.

```python
# Pseudocódigo do coordinator (autoritativo: coordinator.md §3.1)
prompt = build_triager_prompt(pr_metadata=scope)  # scope: TriagerInput
async for message in query(prompt=prompt, options=triager_options):
    ...
```

### 2.3 Não há caminho upstream

Diferente do Reporter (`reporter.md` §2.2), que recebe estado acumulado dos 4 subagents anteriores, o Triager é a primeira etapa da pipeline. Não há "caminho normal vs caminho skip" — só há um caminho de entrada. Ausência deliberada de §2.3 do Reporter spec é informativa para a destilação do template-subagent (ver Fase 2 da sessão #43).

### 2.4 Princípio: Triager opera sobre o diff, não sobre o repositório

O Triager inspeciona **apenas** arquivos modificados no diff entre `base_ref` e `head_ref`. Não navega o repositório inteiro, não constrói modelo do sistema. Limitação alinhada a `docs/architecture-overview.md` §7.2 (PR-scoped, não system-wide).

Operacionalmente: o system prompt instrui uso de `Glob` para descobrir paths alterados (via convenção de path pattern do worktree do CI, materializada em §5.1) e `Read` apenas sobre paths assim descobertos. Spec não enforça isso programaticamente — depende de prompt discipline + lockdown da quíntupla (sem `Bash`, Triager não consegue rodar `git diff` arbitrário).

## 3. Output contract

### 3.1 Shape canônico — discriminated union

Output emitido em `ResultMessage.structured_output` após validação do SDK contra o schema declarado em `output_format`. Shape canônico, discriminado por valor de `decision`:

```python
from typing import Literal, Annotated, Union
from pydantic import BaseModel, Field

class TriagerProceed(BaseModel):
    decision: Literal["proceed"]
    relevance_summary: str  # Por que esta PR vale análise downstream

class TriagerSkip(BaseModel):
    decision: Literal["skip"]
    skip_reason: str  # Por que esta PR não vale análise downstream

TriagerDecision = Annotated[
    Union[TriagerProceed, TriagerSkip],
    Field(discriminator="decision"),
]
```

Justificativa do discriminated union (vs campo único `rationale`): `docs/architecture-overview.md` §5.2 prescreve fields distintos (`relevance_summary` xor `skip_reason`). Shape unificado perderia a semântica direcional do nome do campo — `rationale` em proceed e em skip não são intercambiáveis (um justifica análise downstream; outro justifica ausência dela), e Pydantic discriminator força essa não-intercambiabilidade por construção (ver DD-T02).

A discriminated union TriagerProceed xor TriagerSkip também **suporta por construção** a invariante de prompt unificado declarada em `reporter.md` §5.4. A invariante governa a shape do input que o coordinator constrói para o Reporter: top-level keys estáveis independente do branch (proceed vs skip) tomado pelo Triager. O Triager não monta esse input diretamente — coordinator §3.1 mapeia o output do Triager para o input do Reporter. O que esta spec provê: `TriagerSkip.skip_reason` é campo string obrigatório (per schema acima), permitindo coordinator popular `triager_skip_reason` no Reporter input preservando shape top-level (per reporter.md §2.3). Sem pivot para conditional prompt necessário. Companion edit a Reporter §5.4 (remover forward-ref) catalogado em §10.5.

**Custo de schema compilation.** Doc oficial (`build-with-claude/structured-outputs`) registra que `anyOf` / union types têm custo exponencial de compilação de grammar (interpretação a partir da tabela canônica "Schema complexity limits"):

> "Parameters with union types | 16 | Total parameters that use `anyOf` or type arrays across all strict schemas. **These are especially expensive because they create exponential compilation cost.**"

Triager usa 1 union (TriagerDecision) com 2 variantes — bem dentro do limite documentado de 16 union types por request. Mas o custo é informativo: schemas com mais unions inflam compilation latency no first-hit. Caching de 24h amortiza após primeira compilação (ver §1.5 grammar compilation latency).

### 3.2 Schema produzido por `model_json_schema()`

Pydantic 2.x gera JSON Schema com `oneOf` no nível raiz para discriminated union. Estrutura aproximada (verbatim depende da versão de Pydantic; verificação empírica em T11+):

```json
{
  "$defs": {
    "TriagerProceed": {
      "properties": {
        "decision": {"const": "proceed", "title": "Decision", "type": "string"},
        "relevance_summary": {"title": "Relevance Summary", "type": "string"}
      },
      "required": ["decision", "relevance_summary"],
      "title": "TriagerProceed",
      "type": "object"
    },
    "TriagerSkip": {
      "properties": {
        "decision": {"const": "skip", "title": "Decision", "type": "string"},
        "skip_reason": {"title": "Skip Reason", "type": "string"}
      },
      "required": ["decision", "skip_reason"],
      "title": "TriagerSkip",
      "type": "object"
    }
  },
  "discriminator": {"propertyName": "decision", "mapping": {...}},
  "oneOf": [{"$ref": "#/$defs/TriagerProceed"}, {"$ref": "#/$defs/TriagerSkip"}]
}
```

Interação `oneOf` + SDK `output_format=json_schema` não foi testada no smoke-test (que usou shape unificado `{decision, rationale}` por simplicidade). Decisão deferida formalizada como **DD-T16** em §8.4: confirmar em T11+ que o SDK aceita schemas com `oneOf` / `discriminator` no nível raiz; fallback é serialização ao shape unificado com pós-validação no coordinator se incompatibilidade aparecer.

### 3.3 Casos que parecem erro mas não são

Análogos aos casos do Reporter §3.6, adaptados:

- **`skip_reason` ou `relevance_summary` curtos.** Não há mínimo de tamanho prescrito. O modelo pode emitir razão de 1-2 frases. Validação do schema só exige `type: string` não-vazio.
- **Mesmo PR rodado duas vezes → decisões divergentes.** Triager é stateless e não-determinístico (modelo de LM). Divergência em re-execução é esperada; coordinator não compara runs.
- **Decisão "proceed" sobre PR que downstream descobre vazio (Detector retorna 0 candidatos).** Não é erro do Triager — Triager opera com precision menor que Detector por design (filtro grosseiro pré-análise). Cobertura empírica desse caso fica em §9.

### 3.4 Não há campos opcionais ou condicionais

O shape é exaustivo: cada variante tem exatamente 2 campos obrigatórios. Sem `metadata`, sem `signals`, sem `confidence_score`. Triager não emite confiança calibrada — decisão binária + rationale prosaico é o contrato. Extensão potencial de campo `reasoning` (chain-of-thought estruturado antes da decisão) registrada como decisão deferida em DD-T14 (§8.4).

## 4. Output mechanism

> Esta seção substitui §4 do Reporter spec ("Tool `emit_report`"). Triager opera em Branch B (output_format), sem tool customizada. Asymmetry deliberada documentada em §1.4 (Branch A vs Branch B). Sinal forte para destilação do template-subagent: §4 do template é condicional ao branch escolhido pelo subagent.

### 4.1 Não há custom tool

O Triager **não** define `@tool`, **não** instancia `create_sdk_mcp_server`, **não** registra MCP server in-process. Output emitido nativamente via runtime do SDK quando o modelo produz texto que valida contra o schema de `output_format`.

### 4.2 Mecânica do output

Sequência observada empiricamente em `scripts/smoke_tests/sdk_output_format_lockdown/`:

1. Coordinator chama `query(prompt=..., options=triager_options)` com `output_format` configurado.
2. Modelo emite uma sequência de `AssistantMessage` (eventualmente intercaladas com `ToolUseBlock`s para `Read`/`Glob` e seus `ToolResultBlock`s correspondentes).
3. Quando o modelo emite texto que o SDK consegue parsear como JSON validável contra o schema, o agentic loop encerra e o SDK emite `ResultMessage` com `subtype="success"` e `structured_output` populado.
4. Se o JSON falha validação, o SDK injeta retry no loop transparentemente (não visível ao agente como turn explícito; mecânica interna do SDK).
5. Se retries esgotam, o SDK emite `ResultMessage` com `subtype="error_max_structured_output_retries"` (lista canônica completa em §6.3).

### 4.3 Coordinator captura

```python
# Pseudocódigo do coordinator (autoritativo: coordinator.md §3.1)
async for message in query(prompt=triager_prompt, options=triager_options):
    if isinstance(message, ResultMessage):
        if message.subtype == "success" and message.stop_reason != "refusal":
            decision = TriagerDecision.model_validate(message.structured_output)
            # Discriminator do Pydantic resolve para TriagerProceed ou TriagerSkip
            break
        elif message.subtype == "success" and message.stop_reason == "refusal":
            # Caso especial: SDK marcou success mas modelo refusou; structured_output pode estar ausente
            raise SubagentRefusedTask(stage="triager")
        else:
            raise SubagentValidationFailed(stage="triager", subtype=message.subtype)
```

Validação Pydantic adicional no coordinator (`model_validate`) é defense-in-depth, não redundância: o SDK valida contra JSON Schema antes de devolver, mas tipos Python ricos (discriminated union, runtime variants) só emergem após `model_validate`. Custo: ~µs; ganho: tipos seguros downstream + segunda barreira contra schema drift entre SDK e Pydantic.

Discriminação dupla `subtype` × `stop_reason` no caminho de sucesso é documentada na doc oficial (`agent-sdk/agent-loop`): "The result also includes a `stop_reason` field ... To detect refusals, check `stop_reason == 'refusal'`." Ver §6.3 para tabela completa.

### 4.4 Sem dual sink

Contraste com Reporter §4.7 (dual sink): coordinator captura via `ResultMessage.structured_output` (single sink). Não há scratchpad write. Razão: output do Triager não é audit-bearing externamente — não vai para Report top-level (per RF-006, Report contém findings do Matcher, não da decisão do Triager). Se auditoria do Triager for desejada no futuro, materialização como side finding em PR cross-spec quando demanda concreta aparecer (ver §8.4).

## 5. System prompt

### 5.1 Texto canônico

> Atenção: o SDK opera em "minimal system prompt" mode por default (`agent-sdk/modifying-system-prompts`). O system prompt do Triager precisa ser auto-suficiente quanto a instrução de uso de tools — não há herança de Claude Code preset. O bloco `<examples>` ao final é parte integral do prompt canônico (convenção alinhada a `reporter.md` §5.1).
>
> **Template renderizado via `.format()` / f-string Python.** Placeholders runtime (`{pr_number}`, `{base_ref}`, `{head_ref}`, `{repo_url}`) usam single-brace; JSON literals nos exemplos usam double-brace (`{{...}}`) per escape syntax. Implementador T11+ deve estar ciente de que template é format-string, não raw string como o Reporter (cuja Branch A não tem placeholders runtime no system prompt — o `run_path` viaja via closure).

```
Você é o Triager de um sistema de code review automatizado de conformidade
LGPD. Sua única função é decidir se um pull request (PR) é relevante para
análise de conformidade contra a Política versionada de Proteção de Dados.

CONTEXTO DA PR

PR número: {pr_number}
Base ref: {base_ref}
Head ref: {head_ref}
Repositório: {repo_url}

WORKTREE

Você opera em um worktree Linux do CI/CD. O diretório de trabalho contém
a árvore do repositório no estado de {head_ref}. Use Glob para descobrir
arquivos alterados entre {base_ref} e {head_ref} via convenção de path
patterns (e.g., procure por arquivos modificados consultando metadados
do worktree).

TOOLS DISPONÍVEIS

- Read: leia conteúdo de arquivos específicos (use apenas em arquivos
  identificados como alterados pelo PR; não leia o repositório inteiro).
- Glob: descubra paths alterados ou inspecione estrutura de diretórios.

Você NÃO tem acesso a Bash, Grep, Write, Edit, ou MCP servers. Não
tente invocá-los.

CRITÉRIO DE DECISÃO

Emita decision="proceed" se o PR contém ao menos um sinal plausível de
tratamento de dados pessoais. Sinais incluem:

- Modificações em arquivos sob src/ ou módulos de aplicação.
- Presença de identificadores brasileiros (CPF, CNPJ, CNH, NIS, PIS,
  título de eleitor, CNS) em código, schemas, formulários ou payloads.
- Keywords em inglês ou português indicando dado pessoal (user, customer,
  email, telefone, endereço, name, identity, etc.).
- Mudanças em modelos de banco de dados, schemas de API, ou eventos de
  instrumentação que possam carregar dado de usuário.

Emita decision="skip" se o PR não tem sinal plausível de tratamento de
dados pessoais. Casos típicos de skip:

- Mudanças apenas em docs/ (markdown, ADRs).
- Mudanças apenas em tests/ (sem alterar comportamento de produção).
- Mudanças apenas em CI/CD (.github/, Dockerfile, scripts de build).
- Refatorações puramente sintáticas (rename de variável local, reordering
  de imports) sem tocar lógica de dados.

PRINCÍPIOS

1. Em dúvida, prefira "proceed". Custo de proceed é invocar Detector
   (que filtrará mais finamente); custo de skip falso-negativo é deixar
   passar violação sem análise. Erro recoverable (proceed-on-doubt) vs
   erro silencioso (skip-when-should-proceed).
2. Decisão é PR-level, não path-level. Você decide pela PR inteira.
3. Você opera sobre o diff, não sobre o repositório inteiro. Não navegue
   além dos arquivos alterados.

FORMATO DO OUTPUT

Sua resposta final será validada contra um schema JSON. O schema requer
um dos dois shapes:

  Para proceed:
    {{"decision": "proceed", "relevance_summary": "<sua razão>"}}

  Para skip:
    {{"decision": "skip", "skip_reason": "<sua razão>"}}

A razão (relevance_summary ou skip_reason) deve ser uma ou duas frases
em português, concretas (citem paths ou sinais específicos).

EXEMPLOS

<examples>

<example>
Input:
  pr_number: 42
  base_ref: main
  head_ref: feature/user-registration

Após Glob, você descobriu arquivos alterados:
  - src/users/registration.py
  - src/users/schemas.py
  - tests/test_registration.py

Após Read em src/users/schemas.py, você encontrou um Pydantic model com
campos: cpf, email, full_name.

Output:
  {{"decision": "proceed",
   "relevance_summary": "PR adiciona registro de usuário em src/users/ com
    schema capturando CPF, email e nome — sinais fortes de coleta de dados
    pessoais brasileiros sob LGPD."}}
</example>

<example>
Input:
  pr_number: 43
  base_ref: main
  head_ref: docs/update-readme

Após Glob, você descobriu arquivos alterados:
  - README.md
  - docs/architecture-overview.md
  - .github/workflows/lint.yml

Após Read em README.md e docs/architecture-overview.md, você confirmou
mudanças puramente em documentação. .github/workflows/lint.yml é CI
config sem tocar código de aplicação.

Output:
  {{"decision": "skip",
   "skip_reason": "PR contém apenas mudanças em documentação (README,
    architecture-overview) e CI config (lint.yml). Nenhum arquivo de
    aplicação alterado; sem sinal de tratamento de dados pessoais."}}
</example>

<example>
Input:
  pr_number: 44
  base_ref: main
  head_ref: feature/logging-improvements

Após Glob, você descobriu arquivos alterados:
  - src/utils/logger.py
  - docs/CHANGELOG.md
  - tests/test_logger.py

Após Read em src/utils/logger.py, você encontrou um formatter que
serializa objetos genéricos para JSON. Sem schema explícito de dados
pessoais, mas o logger é usado pela aplicação inteira e pode receber
qualquer tipo de objeto, incluindo objetos com dados de usuário.

Output:
  {{"decision": "proceed",
   "relevance_summary": "PR altera logger em src/utils/logger.py que pode
    serializar objetos contendo dados pessoais; em dúvida sobre o impacto
    no tratamento de dados, sigo princípio de proceed-on-doubt."}}
</example>

<example>
Input:
  pr_number: 45
  base_ref: main
  head_ref: ci/upgrade-actions

Após Glob, você descobriu arquivos alterados:
  - .github/workflows/test.yml
  - .github/workflows/deploy.yml
  - Dockerfile

Após Read em .github/workflows/test.yml e Dockerfile, você confirmou
mudanças puramente em CI/CD: upgrade de versão de actions, atualização
de base image do Docker. Nenhum código de aplicação tocado.

Output:
  {{"decision": "skip",
   "skip_reason": "PR é puramente CI/CD (workflows do GitHub Actions e
    Dockerfile); sem alteração em código de aplicação ou modelos de
    dados. Sem sinal de tratamento de dados pessoais."}}
</example>

</examples>
```

> 💡 **Conceito Claude relevante (Domínio 4 — Prompt Engineering & Structured Output, Task Statement 4.5).** O prompt **descreve** o shape esperado em prosa natural (bloco "FORMATO DO OUTPUT") complementando a constraint estrutural do `output_format=json_schema`, e **demonstra** o shape via bloco `<examples>` de 4 exemplares. Tripla camada — prompt orienta, examples demonstram, SDK enforça. Defensive-in-depth contra divergência entre instrução prosaica e shape estrutural (empírico em SF-3: ~4 turns para output trivial, sinaliza que prompt orientativo + few-shot reduz o número de tentativas de produção de output correto).

### 5.2 Behaviors explícitos

- **Tom.** Decisão técnica, sem hesitação verbal. Não pedir confirmação ao usuário (não há usuário no loop).
- **Granularidade.** Decisão pela PR inteira; não emitir sub-decisões por arquivo.
- **Idioma.** Razão em português (alinhado a ADR-0001 D3, idioma de outputs ao usuário); identifiers e tokens canônicos em inglês.
- **Não inventar contexto.** Triager não tem acesso ao código de produção, à Política, nem aos vocabulários. Decisão baseada apenas em paths + conteúdo dos arquivos alterados (acessível via Read/Glob).

### 5.3 Few-shot strategy — nota meta

Os 4 exemplares wrapped em `<examples>` no final do prompt canônico de §5.1 são derivados das seguintes diretrizes da doc oficial Anthropic (`prompt-engineering/multishot-prompting`):

- **Quantidade.** Doc canônica recomenda 3-5 exemplares ("Include 3-5 diverse, relevant examples to show Claude exactly what you want. More examples = better performance, especially for complex tasks"). Triager usa 4.
- **Cobertura.** Doc canônica: "Diverse: Your examples cover edge cases and potential challenges, and vary enough that Claude doesn't inadvertently pick up on unintended patterns." Triager cobre 2 happy paths (proceed clássico com CPF; skip clássico apenas docs/CI) + 2 edge cases (PR misto que dispara princípio 1; PR puramente CI sem código de aplicação).
- **Estrutura.** Doc canônica: "Clear: Your examples are wrapped in `<example>` tags (if multiple, nested within `<examples>` tags) for structure." Triager segue a convenção.
- **Localização física.** Os exemplares vivem inline dentro do string canônico de §5.1 (convenção do projeto, alinhada a `reporter.md` §5.1 onde REPORTER_SYSTEM_PROMPT inclui o `<example>` block dentro do mesmo string literal). Esta seção é nota meta sobre estratégia — não duplica conteúdo.

Argumento prévio (versão draft desta spec) defendia 2 exemplares com base em "decisão binária sem variante intermediária". Foi revisado: edge cases existem mesmo em decisão binária (PR misto, PR só CI, PR refactor sintático) e merecem exemplar próprio para evitar o modelo capturar pattern errado a partir de happy paths apenas (ver DD-T09).

### 5.4 Unified prompt — sem branch conditional

Um único prompt cobre ambos `proceed` e `skip`. Modelo decide qual variante emitir baseado na inspeção. Não há "prompt de proceed" e "prompt de skip" — paralelo a Reporter §5.4.

## 6. Error handling

### 6.1 Estrutura canônica

Triager Branch B não tem envelope de erro customizado — diferente do Reporter (`reporter.md` §6.1), que emite erros via `emit_report` como tool result com `isError: true` + `structuredContent` envelope. O Triager só pode falhar via mecanismos nativos do SDK; a propagação de erro acontece no coordinator (não no Triager).

### 6.2 Classes de erro relevantes

Quatro classes relevantes:

| Classe       | Locus       | Quem detecta                          | Quem propaga                            |
|--------------|-------------|---------------------------------------|-----------------------------------------|
| Validation   | SDK runtime | SDK (schema validation)               | Coordinator (via `SubagentValidationFailed`) |
| Budget       | SDK runtime | SDK (max_turns / max_budget_usd exceeded) | Coordinator (via `SubagentUnresponsive`)     |
| Refusal      | Modelo      | Modelo (safety refusal)               | Coordinator (via `SubagentRefusedTask`)      |
| System       | OS-level    | Coordinator (try/except sobre query)  | Coordinator (via re-raise tipado)            |

Triager não tem erros de **business** (não há classes intra-handler análogas ao `MULTIPLE_FINDINGS_FOR_CANDIDATE` do Reporter §6.3). Razão estrutural: Triager devolve decisão binária livre — não há condição de inconsistência interna que o handler precise detectar e reportar via errorCode.

A classe **Refusal aplica simetricamente a ambos os branches** via SDK-level `stop_reason="refusal"` — não é absorvida por envelope intra-handler em nenhum branch. A asymmetry real entre branches é a presença de família intra-handler para validation/business no Branch A (Reporter §6.3 lista 7 errorCodes: `PYDANTIC_VALIDATION`, `CLAUSE_REF_FORMAT`, `PROVENANCE_MISMATCH`, `COUNTS_DISAGREE_WITH_FINDINGS`, `TOTAL_NOT_SUM_OF_COUNTS`, `REPORT_ID_MISMATCH`, `SCRATCHPAD_WRITE_FAIL`) vs ausência completa no Branch B (Triager não tem locus análogo — ver §6.4).

### 6.3 Família de `ResultMessage.subtype` e `stop_reason`

Discriminação tem dois eixos independentes documentados na doc oficial: `ResultMessage.subtype` (decisão do agentic loop do SDK) e `ResultMessage.stop_reason` (razão da última geração do modelo, propagada do API Messages).

**Eixo 1 — `ResultMessage.subtype`** (lista canônica verbatim de `agent-sdk/agent-loop`):

| `subtype`                              | Significado                                                          | `result` populado | Tratamento no coordinator                    |
|----------------------------------------|----------------------------------------------------------------------|-------------------|----------------------------------------------|
| `success`                              | Claude completou a task; `structured_output` populado.               | Sim               | Consumir + verificar `stop_reason` (eixo 2). |
| `error_max_turns`                      | Estourou `max_turns=20` antes de emitir output validável.            | Não               | Levantar `SubagentUnresponsive`.             |
| `error_max_budget_usd`                 | Estourou `max_budget_usd` (se configurado).                          | Não               | Levantar `SubagentUnresponsive`.             |
| `error_during_execution`               | Erro interrompeu o loop (API failure, cancelled request).            | Não               | Levantar `SubagentExecutionError`.           |
| `error_max_structured_output_retries`  | SDK esgotou retries internos tentando produzir JSON válido.          | Não               | Levantar `SubagentValidationFailed`.         |

**Eixo 2 — `ResultMessage.stop_reason`** (lista canônica verbatim de `build-with-claude/handling-stop-reasons`):

| `stop_reason`                       | Significado                                                          | Relevância para Triager                      |
|-------------------------------------|----------------------------------------------------------------------|----------------------------------------------|
| `end_turn`                          | Modelo finalizou normalmente.                                        | Caminho feliz (com `subtype=success`).       |
| `max_tokens`                        | Output truncado por limit de tokens.                                 | `structured_output` pode estar incompleto.   |
| `stop_sequence`                     | Stop sequence customizado encontrado.                                | Não aplicável (Triager não usa stop_sequences). |
| `tool_use`                          | Modelo chamando tool.                                                | Intermediário; não aparece em `ResultMessage`. |
| `pause_turn`                        | Server-side iteration limit em server tools.                         | Não aplicável (Triager não usa server tools). |
| `refusal`                           | Safety refusal pelo modelo.                                          | **Crítico**: pode coexistir com `subtype=success` e `structured_output` ausente/incompleto. |
| `model_context_window_exceeded`     | Context window limit atingido.                                       | Output truncado; raro para Triager (input pequeno). |

**Caso crítico — `subtype=success` com `stop_reason=refusal`.** A doc oficial é explícita: "Claude maintains its safety and helpfulness properties even when using structured outputs. If Claude refuses a request for safety reasons: ... The output may not match your schema because the refusal message takes precedence over schema constraints." Para o Triager, esse caso é plausível porque PRs podem conter snippets de PII real (fixtures com CPF literais, dados de teste). Coordinator deve discriminar `stop_reason="refusal"` mesmo dentro de `subtype="success"` e tratar como classe Refusal (não como sucesso) — pseudocódigo em §4.3.

### 6.4 Não há família intra-handler

Reporter §6.3 documenta 7 errorCodes intra-handler. Triager não tem locus análogo — não há handler executando lógica entre receber input e emitir output. Validation-retry loop é gerenciado pelo SDK transparentemente; o agente nunca observa "falhei a validação, tentando de novo".

Asymmetry deliberada vs Reporter. Sinal para destilação do template (Fase 2): §6.3 do template é condicional ao branch escolhido (Branch A tem família intra-handler; Branch B não, mas precisa cobrir 5 subtypes + 7 stop_reasons como tabela invariante).

### 6.5 Casos que parecem erro mas não são

- **Triager emitiu `skip` quando deveria ter emitido `proceed` (falso-negativo).** Não é erro de runtime. É erro de calibragem do prompt ou do critério; tratado via §9 (acceptance scenarios) e via Provisão MC-D (catálogo de PRs sintéticos).
- **Mesmo PR re-rodado produz decisões diferentes.** Não é erro. Triager é não-determinístico por construção; coordinator não compara runs.
- **`relevance_summary` ou `skip_reason` vagos.** Não é erro estrutural — schema aceita qualquer string. Calibragem de qualidade da razão é responsabilidade do prompt + few-shot, não de runtime.

## 7. Provenance e versionamento

### 7.1 Versão da spec

`spec_version: 0.1.0`. Convenção SemVer. Bump rules:

- **Patch (0.1.x):** correções de redação, esclarecimentos, sem mudança de contrato.
- **Minor (0.x.0):** adição de campos opcionais a `TriagerInput` ou `TriagerDecision`; novos casos em §9; novos exemplares few-shot em §5.1.
- **Major (x.0.0):** mudança de contrato I/O (campos removidos/renomeados, semântica do `decision` alterada, troca de Branch B para Branch A).

Convenção alinhada a Reporter spec §7.1 (cross-subagent invariante). **Atenção ao acoplamento versioning com Report.scope** per §2.1: bump em `TriagerInput` força bump em Report payload (Reporter spec), porque `Report.scope = TriagerInput` literalmente (per Provisão MC-F).

### 7.2 Versão do schema `TriagerDecision`

Acompanha `spec_version`. Razão: schema é parte do contrato I/O canônico definido nesta spec; bump independente criaria drift entre spec e schema sem rastro.

Locus físico: declarado em `src/subagents/triager/models.py` (per DD-T15) quando T11+ implementar. Spec é fonte normativa do shape.

### 7.3 Não há trinque de provenance jurídico-temporal

Triager **não** emite `(policy_schema_version, policy_version, legal_framework)`. Razão: subset do RF-009 que aplica a vereditos do Matcher e ao Report do Reporter — Triager não consulta a Política, não emite veredito, e não vai para o Report top-level. Decisão de eficiência da pipeline não precisa de provenance jurídica.

Asymmetry vs Reporter §7.3 (quartet de versioning no Report). Sinal para destilação do template: §7 do template é condicional à exposição do subagent ao Report externo (ver DD-T08).

### 7.4 Mutabilidade durante execução

Triager é stateless e immutable per query. Não há hot reload, não há restart-triggered behavior, não há arquivo persistente próprio. Cada `query()` é fresh.

## 8. Não-objetivos e fronteiras

### 8.1 Não-objetivos do Triager

Lista exaustiva do que o Triager **não** faz, mesmo que pudesse fazer:

- **Não detecta candidatos de tratamento.** Isso é responsabilidade do Detector (RF-001) via `semgrep-runner.scan_diff`. Triager decide se vale invocar Detector; não substitui.
- **Não extrai contexto estruturado.** Isso é responsabilidade do Classifier (RF-003). Triager não emite `structured_context`.
- **Não avalia conformidade.** Isso é responsabilidade do Matcher (RF-004). Triager não consulta cláusulas, não emite vereditos.
- **Não emite findings.** O campo `findings` no Report (per RF-006) é populado por Matcher → Reporter. Triager não toca esse campo.
- **Não toca `requires_human_review`.** Esse campo, declarado em `reporter.md` §3.2 como presente no Report, é forward-ref ao Matcher spec (semântica ainda não autorada). Triager não emite findings, logo não tem campos análogos a este (ver DD-T10).
- **Não emite trinque de provenance jurídico-temporal.** Ver §7.3.
- **Não consome `policy://vocabularies`.** ADR-0005 D4 restringe esse resource a Matcher + Classifier; Triager sem MCP servers no allowlist (ver §1.3).
- **Não é path-level granular.** Decisão é pela PR inteira, não por arquivo. Granular skip por path adicionaria responsabilidade que não pertence ao Triager — eficiência granular fica para Detector quando `scan_diff` filtra paths irrelevantes per ruleset interno (ver DD-T07).
- **Não persiste estado próprio.** Stateless per §7.4.
- **Não modifica filesystem.** Tools restritas a `Read` + `Glob`; sem `Write`/`Edit`/`Bash`.

### 8.2 Não-objetivos do escopo

- **Não cobre PRs cross-repository.** Triager opera sobre o diff de uma PR única, alinhado a `docs/architecture-overview.md` §7.2.
- **Não cobre análise temporal cross-PR.** Cada execução é independente; sem memória entre PRs.

### 8.3 Fronteira epistêmica

O Triager faz triagem semi-semântica baseada em **paths alterados** + **inspeção de conteúdo de arquivos no diff** (via `Read`). Não tem janela para:

- Estado runtime do sistema (configuração, feature flags, dados de produção).
- Comportamento downstream do código (o que esse novo schema com CPF de fato faz com o CPF coletado).
- Histórico do repositório (PRs anteriores tocando a mesma área).

Implicação: a decisão `proceed`/`skip` é uma heurística calibrada para minimizar falso-negativo (skip-when-should-proceed) ao custo de aceitar algum falso-positivo (proceed-on-doubt). Custo do falso-positivo é invocação dos subagents downstream (recoverable); custo do falso-negativo é deixar passar violação sem análise (silencioso). Princípio 1 do system prompt §5.1 codifica essa assimetria.

Honestidade epistêmica análoga ao Matcher (`docs/REQUIREMENTS.md` RF-005 + `docs/architecture-overview.md` §7.1): Triager pode emitir `proceed` sem confiança alta — é o caminho seguro. Não há "indeterminate" no shape do Triager porque o coordinator não saberia o que fazer com indeterminate em etapa 0 (não há fallback abaixo do Triager).

### 8.4 Decisões deferidas

| ID         | Decisão                                                                                              | Razão do deferment                                                                  | Quando reabre                                            |
|------------|------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|----------------------------------------------------------|
| DD-T05     | `changed_paths` no scope compartilhado entre subagents                                               | Classifier spec não autorada; decisão prematura criaria invariant não-justificado | Quando Classifier spec for autorada (sessão #44+)        |
| DD-T11     | Modelo dedicado ao Triager (Haiku 4.5 vs Opus 4.7 adaptive)                                          | Otimização de modelo introduziria variável adicional durante validação funcional  | Pós-produção, após sistema 100% funcional               |
| DD-T14     | Adicionar `reasoning` field opcional ao schema (chain-of-thought estruturado antes da decisão)       | Doc canônica de ticket-routing usa `<reasoning>` tags antes do output classificado; benefício não medido empiricamente | Quando T11+ executar catálogo de PRs sintéticos com e sem o campo |
| DD-T16     | Aceitação de schemas com `oneOf` / `discriminator` no nível raiz pelo SDK `output_format=json_schema` | Smoke-test usou shape unificado (sem discriminator)                                | Quando implementação T11+ tentar discriminated union   |

**Notas sobre DD-T11 (fechada via deferment).** A doc oficial de ticket-routing (`use-case-guides/ticket-routing`) recomenda Claude Haiku 4.5 como modelo ideal para classification: "Many customers have found `claude-haiku-4-5-20251001` an ideal model for ticket routing, as it is the fastest and most cost-effective model in the Claude 4 family while still delivering excellent results." Material acumulado da pesquisa em docs oficiais (sessão #43): Haiku 4.5 é 3.75x mais barato que Sonnet, ~3x mais rápido, e classificado como ASL-2 (vs ASL-3 de Sonnet/Opus, com `refusal` rates correspondentes mais baixos per `build-with-claude/handling-stop-reasons`). Caveats descobertos: `effort` parameter não se aplica a Haiku 4.5 (lista oficial cobre apenas Opus 4.7/4.6/4.5 e Sonnet 4.6). Gate epistêmico para reabertura: smoke-test análogo a `sdk_output_format_lockdown` com `model="claude-haiku-4-5-20251001"` para confirmar coexistência de Haiku + output_format + lockdown. Se PASS, troca de modelo é mecânica; se FAIL, fallback documentado para Opus/Sonnet com `effort="low"`.

**Notas sobre DD-T15 (layout convention).** Spec adota convenção uniforme `src/subagents/<name>/` para todos os subagents. Implica migration do Reporter de `src/coordinator/` para `src/subagents/reporter/`, materializada como **Provisão MC-F** em §10.5 — PR housekeeping pré-T11+ que reabre Reporter spec (bump 0.3.0 → 0.4.0). Justificativa: convenção uniforme prevalece sobre asymmetry de implementation (Branch A factory pattern do Reporter pode importar utilitários do coordinator sem precisar morar dentro dele). Decisão tomada conscientemente aceitando o débito de migration; débito eliminado pré-T11+ via Provisão MC-F.

**Notas sobre DD-T13 (subtypes em exhaustion) — FECHADA.** Lista canônica completa documentada em `agent-sdk/agent-loop` e materializada em §6.3: 5 subtypes (`success`, `error_max_turns`, `error_max_budget_usd`, `error_during_execution`, `error_max_structured_output_retries`) + 7 stop_reasons (`end_turn`, `max_tokens`, `stop_sequence`, `tool_use`, `pause_turn`, `refusal`, `model_context_window_exceeded`). Não há mais verificação empírica pendente para os nomes; apenas para a observação de cada caminho específico sob o lockdown do Triager (cobertura empírica fica em T11+ via Provisão MC-D).

## 9. Critérios de aceitação

A implementação está completa quando todos os critérios abaixo forem demonstravelmente verdadeiros. Cada critério é verificável por teste automatizado ou inspeção direta contra catálogo de PRs sintéticos da Provisão MC-D.

### 9.1 Happy-path scenarios

- [ ] PR com mudança em `src/users/registration.py` declarando schema com campo `cpf` → Triager emite `decision="proceed"` com `relevance_summary` citando `src/users/` ou `cpf`.
- [ ] PR com mudanças apenas em `docs/` (markdown) → Triager emite `decision="skip"` com `skip_reason` citando `docs/` ou "apenas documentação".
- [ ] PR com mudanças apenas em `tests/` sem tocar `src/` → Triager emite `decision="skip"` com `skip_reason` citando `tests/`.
- [ ] PR com mudanças em `src/` mas refatoração puramente sintática (rename local sem tocar campos de schema) → Triager emite decisão dependente do critério; ambos `proceed` (defensivo) e `skip` (com `skip_reason` específico) são aceitáveis. Calibragem fina em Provisão MC-D.

### 9.2 Edge case scenarios

- [ ] PR misto: muda `src/utils/logger.py` + `docs/CHANGELOG.md` simultaneamente → Triager emite `decision="proceed"` (princípio 1 do system prompt: em dúvida, proceed) com `relevance_summary` citando `src/utils/logger.py`.
- [ ] PR apenas em `.github/workflows/` (CI config) sem `src/` → Triager emite `decision="skip"` com `skip_reason` citando CI.
- [ ] PR alterando `Dockerfile` ou `pyproject.toml` → Triager emite `decision="skip"` (mudanças de stack/build não tocam tratamento de dados). Calibragem fina em Provisão MC-D.
- [ ] PR vazio (sem arquivos modificados) → não aplicável (coordinator deve filtrar antes; mas se acontecer, Triager emite `decision="skip"` com `skip_reason` apontando ausência de diff).

### 9.3 Cross-check scenarios

- [ ] `relevance_summary` ou `skip_reason` não-vazios em toda execução `success`.
- [ ] `decision` é exatamente `"proceed"` ou `"skip"` (sem outros valores).
- [ ] Output passa `TriagerDecision.model_validate(message.structured_output)` no coordinator sem `ValidationError`.
- [ ] Coordinator discrimina `subtype="success"` + `stop_reason="refusal"` e levanta `SubagentRefusedTask` em vez de consumir `structured_output` potencialmente ausente.

### 9.4 Provenance scenarios

- [ ] `spec_version` desta spec é consultável em metadados da implementação (e.g., via constante em `src/subagents/triager/__init__.py`).
- [ ] Mudanças no shape de `TriagerDecision` disparam bump de `spec_version` per §7.1.

### 9.5 Persistence scenarios

Não aplicável. Triager é stateless (§7.4). Critério estrutural: ausência de arquivos persistidos por execução do Triager (verificável via inspeção de filesystem em catálogo de PRs sintéticos).

## 10. Cross-references

### 10.1 Source-of-truth artifacts

- **Função e posição:** `docs/architecture-overview.md` §3, §5.2, §5.7.
- **Input contract:** `docs/architecture-overview.md` §5.2 (com conflito catalogado em §10.5); este spec §2.
- **Output contract:** `docs/architecture-overview.md` §5.2; este spec §3.
- **Lockdown pattern:** `coordinator.md` §2 (locus canônico da quíntupla).
- **Branch A reference:** `reporter.md` §4 (`emit_report` como contraste arquitetural).
- **Smoke-test empírico:** `scripts/smoke_tests/sdk_output_format_lockdown/`.
- **Lista canônica de subtypes:** `agent-sdk/agent-loop` (doc oficial Anthropic).
- **Lista canônica de stop_reasons:** `build-with-claude/handling-stop-reasons` (doc oficial Anthropic).

### 10.2 ADRs aplicáveis

- **ADR-0001** — stack canônica (Python 3.12.7, claude-agent-sdk, pydantic).
- **ADR-0005 D4** — resource access scoping (Triager não consome `policy://vocabularies`).
- **ADR-0008** — task decomposition (tasks T11+ implementam este spec).
- **ADR pendente** — companion edit a ADR-0001 para fixar pin `claude-agent-sdk>=0.2.0,<1.0` em `pyproject.toml` (Provisão MC-E).

### 10.3 Gates pré-implementação

- **Gate 1** — smoke-test `sdk_tooluseblock_shape` (sessão Code #38, PR #63). Não impacta diretamente o Triager mas anchora pattern A''.
- **Gate 6** — smoke-test `sdk_tools_empty_list` (PR #67). Anchora a interpretação de `tools=[]` em context restriction (não direto pro Triager, que usa `tools=["Read","Glob"]`, mas valida mecânica).
- **Gate Branch B** — smoke-test `sdk_output_format_lockdown` (PR pre-Fase-0 da sessão #43). **Gate direto deste spec.** Valida `output_format=json_schema` sob lockdown completo em SDK 0.2.87.

### 10.4 DDs status pós-PR de aplicação deste spec

| DD       | Status                                                                            |
|----------|-----------------------------------------------------------------------------------|
| DD-T01   | Fechada via spec §1.4 + smoke-test PR pre-Fase-0 + endorsement direto da doc oficial `agent-sdk/structured-outputs` |
| DD-T02   | Fechada via spec §3.1 (com nota de custo exponencial dentro do limite 16)         |
| DD-T03   | Fechada via spec §1.3 (alinhada a arch §5.2 + §5.7)                               |
| DD-T04   | Fechada via spec §1.4                                                             |
| DD-T05   | **Aberta** (deferida para Classifier spec; companion edit a arch-overview catalogado) |
| DD-T06   | Fechada via spec §1.5 (provisional; max_budget_usd como cap complementar documentado) |
| DD-T07   | Fechada via spec §8.1 (path-level fora do escopo)                                 |
| DD-T08   | Fechada via spec §7.3                                                             |
| DD-T09   | Fechada via spec §5.1 + §5.3 (4 exemplares com XML tags; alinhamento com canônico 3-5) |
| DD-T10   | Fechada via spec §8.1                                                             |
| DD-T11   | Fechada via deferment para produção (Opus 4.7 adaptive em desenvolvimento; Haiku 4.5 candidato para reabertura pós-validação funcional) |
| DD-T12   | Fechada via spec §1.5 callout 💡 + §6.3 tabela completa                           |
| DD-T13   | Fechada via spec §6.3 (lista canônica completa de 5 subtypes + 7 stop_reasons)    |
| DD-T14   | **Aberta** (reasoning field; deferida para T11+ com catálogo MC-D)                |
| DD-T15   | Fechada via spec §1.5 + §8.4 nota (convenção uniforme `src/subagents/<name>/`; débito eliminado via Provisão MC-F pré-T11+) |
| DD-T16   | **Aberta** (oneOf/discriminator schema; deferida para T11+ tentativa de discriminated union) |

13 DDs fechadas, 3 abertas (DD-T05, DD-T14, DD-T16). Catalogadas em §8.4 como decisões deferidas.

> **Nota de categoria.** Das 13 fechadas, DD-T11 está em categoria distinta — **fechada via deferment para produção** (decisão consciente de adiar otimização de modelo, com gate epistêmico declarado para reabertura) — enquanto as outras 12 são fechadas por design ratificado nesta spec. DD-T14 e DD-T16 (abertas) são análogas a DD-T11 no sentido de carregarem gate empírico de reabertura, mas diferem por não ter direção pré-aprovada — aguardam evidência empírica em T11+. Categorização útil para reader navigation: spec resolve por design o que pode ser resolvido por design; o que precisa de evidência fica deferred com gate explícito.

### 10.5 Companion edits e Provisões pendentes a outros docs

Catálogo de edits a aplicar fora desta spec após merge:

1. **`coordinator.md` §3.1** — ✅ **aplicado** (MC-F): §3.1 já declara `output_format={"type": "json_schema", "schema": TriagerDecision.model_json_schema()}` (forma envelopada, não o shorthand) + `max_turns=20` (coordinator.md l.72-76), além da quíntupla + system_prompt + tools. Sem edit pendente — a prescrição "adicionar" desta entrada está obsoleta.

2. **`coordinator.md` §5** — adicionar entrada catalogando tipos de message não-padrão que o loop deve tolerar (e.g., `RateLimitEvent`). Contexto: `RateLimitEvent` foi observado em Gate 1 (sessão #38) e documentado em `coordinator.md` §11 AC2; reaparece no smoke-test `sdk_output_format_lockdown` (SF-2), mas o README desse smoke-test declara incorretamente que o tipo "não foi observado em smoke-tests anteriores" (ver companion edit #6 abaixo). Patch sugerido: adicionar nota em coordinator §5 declarando que loop deve tolerar tipos não-padrão sem rebentar (log e continue), referenciando coordinator §11 AC2 como locus observacional.

3. **`docs/tasks.md` §Tasks T11+** — quando decompor, prever ao menos uma task dedicada a implementação do Triager:
   - Definir `src/subagents/triager/models.py` com `TriagerDecision` discriminated union (per DD-T15).
   - Definir `src/subagents/triager/prompt.py` com template canônico de §5.1 (incluindo `<examples>` block).
   - Definir `src/subagents/triager/__init__.py` declarando `spec_version: str = "0.1.0"` para provenance §9.4.
   - Tests cobrindo §9.1, §9.2, §9.3, §9.4.

4. **`docs/architecture-overview.md` §3 mermaid** — Provisão MC-B (substituir `T -->|skip| END[Sem ação]` por `T -->|skip| R[Reporter]`). Catalogada em `coordinator.md` §10 e `docs/tasks.md` §Provisão MC-B; reforçada aqui por consistência cross-doc.

5. **`docs/architecture-overview.md` §5.2** — substituir "Input. Diff do PR, lista de paths alterados" por "Input. PR scope (`pr_number`, `base_ref`, `head_ref`, `repo_url`); paths alterados descobertos pelo Triager via `Glob`". Alinhamento com Triager spec §2.1 + DD-T05 aberta. Caso DD-T05 reabra com decisão de pré-computar `changed_paths` no coordinator, este edit é revertido.

6. **`scripts/smoke_tests/sdk_output_format_lockdown/README.md` SF-2** — corrigir a afirmação "Tipo de mensagem não observado nos smoke-tests anteriores deste projeto" para "Tipo de mensagem já observado em Gate 1 (sessão #38), documentado em `coordinator.md` §11 AC2; reaparece neste smoke-test e reforça obrigação do coordinator de tolerar tipos não-padrão (companion edit a `coordinator.md` §5 em #2 acima)". Erro factual conhecido no README do smoke-test; correção é cosmética mas evita propagação de informação desencontrada.

7. **Provisão MC-F — Reporter spec 0.3.0 → 0.4.0 + module migration sob DD-T15** (PR housekeeping pré-T11+). Escopo:
   - Reabrir `docs/specs/subagents/reporter.md`; bump minor 0.3.0 → 0.4.0 com mudança em §1.5 ("Locus físico"): substituir `src/coordinator/{models,constants,system_prompts,tools}.py` por `src/subagents/reporter/{models,constants,system_prompts,tools}.py`. Adicionar nota em §10 (changelog interno) declarando ratificação retroativa de DD-T15.
   - Remover forward-ref em `reporter.md` §5.4: o bullet que diz "Triager spec (a redigir, sessão pós-Reporter+sanity) ratifica a invariante ou força pivot para conditional prompt; revisão de §5.4 a re-confirmar nesse momento" deve ser substituído por "Triager spec v0.1.0 §3.1 define `TriagerSkip.skip_reason` como campo string obrigatório no caminho skip, permitindo ao coordinator §3.1 popular `triager_skip_reason` no Reporter input preservando top-level shape (per reporter.md §2.3). Sem pivot para conditional prompt necessário."
   - Atualizar `reporter.md` §3.1: substituir `"scope": {...}` (dict opaco no payload) por `"scope": TriagerInput` (cross-ref'ando Triager §2.1 para shape canônico `{pr_number, base_ref, head_ref, repo_url}`). Acoplamento literal `Report.scope = TriagerInput` ratificado nesta spec (§2.1); versioning coupling deliberado declarado em §7.1.
   - Atualizar `reporter.md` §4.3 inputSchema table: a row `scope` passa de `dict (opaco — não validado por Pydantic model dedicado no MVP; ver §8.4 decisões deferidas)` para `TriagerInput (Pydantic, ratificado em Triager §2.1)`.
   - Remover bullet "Estruturação Pydantic de scope (catch R2-F5 / #42)" da §8.4 do Reporter (deferment listing): Triager spec v0.1.0 §2.1 fechou esta decisão por construção (TriagerInput é Pydantic BaseModel tipado, variante (b) do espaço de design — abordagem ratificada; field set definido pela Triager spec supera sugestão exploratória do Reporter §8.4).
   - Catalogar Provisão MC-F também em `docs/tasks.md` §Companion edits / Provisões (não só nesta spec) — sincronização auxiliar para que o débito não seja perdido quando esta spec for arquivada.
   - Sequenciamento: MC-F é PR único, mecânico (rename + import updates + 4 edits cirúrgicos cross-spec ao Reporter), audit trail explícito. Não mistura concerns com PRs de implementação T11+. Custo de revisão estimado: ~15-20min.

8. **`docs/learning-log.md` entry #43** — registrar defense candidates da sessão (lista em §10.6) + DDs novos (DD-T14, DD-T15, DD-T16) + side finding `dontAsk` em Python (§10.7) + descoberta da imprecisão de SF-2 vs Gate 1 sobre RateLimitEvent (companion edit #6).

### 10.6 Defense candidates emergentes desta sessão

Material para Capítulo de Método do TCC (consolidação completa em entry #43 do learning-log):

1. **Heterogeneidade per concern em output mechanisms.** Subagents do mesmo sistema usam mecanismos diferentes (Branch A custom tool vs Branch B `output_format`) calibrados por concern, não por preferência. Defense candidate forte: match mechanism to need supera consistência sintática. Endorsement direto da doc oficial (`agent-sdk/structured-outputs`) reforça.

2. **Validation-retry loop como capability nativa do runtime.** `output_format=json_schema` delega ao SDK o que o Reporter Branch A implementa no handler. Pattern arquitetural: encapsular preocupações de validação onde a evidência empírica de robustez existe (runtime testado por Anthropic vs handler novo do projeto).

3. **Smoke-test gate como caminho mais curto vs changelog spelunking.** Gate epistêmico de versão (qual SDK suporta feature X) resolvido em ~10min de smoke-test com lockdown completo. Pattern: prefira evidência empírica direta sobre inferência indireta de documentação. (Aplicado nesta sessão; precedente literal em PR #67 / Gate 6.)

4. **Verificação cross-doc para falsificar inferência de revisores.** Sessão revelou múltiplos falsos positivos em reviews ostensivamente detalhados, todos por extrapolação de leitura parcial. Pattern: defesa contra fabricação cruza-citação verbatim antes de aceitar conclusão. Aplicado tanto contra meus próprios drafts (Code identificou D1, D3, e mais tarde RF-006 verbatim de novo) quanto contra reviewers (Code 2 fabricou ausência de "read-only analysis trio" sem fetch direto da doc). Caso meta-recente: review do Code identificou claim factualmente errado em draft anterior (refusal absorption pelo envelope `isError` do Reporter — verificação verbatim contra Reporter §6.3 mostrou que nenhum dos 7 errorCodes intra-handler trata refusal; e Reporter §5.4 invariante foi misframed como ratificada pela discriminated union do Triager quando na verdade é ratificada pela disponibilidade de `skip_reason` como campo string mapeável). Verificação cross-doc captura inferência plausível-mas-falsa que se propagaria para asymmetry argumentos do template.

5. **Template-hipótese exposto por single-responsibility extrema.** Triager (decisão binária, sem trinque, sem dual sink, sem tool customizada) expõe §4, §6 e §7 do template Reporter como condicionais. Defesa: cobertura de template emerge de instâncias com cobertura assimétrica, não de protótipos médios.

6. **Assimetria deliberada como sinal arquitetural, não débito.** Ausência de §4 (custom tool), redução de §6 (sem família intra-handler) e ausência de trinque em §7 são deliberadas — declaradas com justificativa, não omissões silenciosas. Audit-friendly.

7. **Calibração phase-aware de parâmetros operacionais (`max_turns=20`, modelo Opus 4.7).** Distinção entre cap-para-calibragem e cap-para-produção. Pattern measure-before-tune evita confound em distribuição empírica. Aplicado também à decisão de modelo: otimização de modelo (Haiku 4.5) deferida para pós-validação funcional do sistema.

8. **Convergência informativa com pattern canônico Anthropic (ticket-routing).** Doc canônica usada como ancoragem de design, não como prescrição. Diferenças explícitas demonstram leitura crítica, não cargo-cult: domínio diferente (PR diff vs ticket), aridade diferente (binária vs multi-categoria), modelo de operação diferente (pipeline determinística vs state machine).

9. **Contrato observável documentado supera contrato observável inferido.** Lista canônica de 5 subtypes + 7 stop_reasons da doc oficial (`agent-sdk/agent-loop` e `build-with-claude/handling-stop-reasons`) substitui qualquer tentativa de inferir esses nomes empiricamente subtype-a-subtype. Pattern: quando o vocabulário existe na doc, citá-lo verbatim em vez de descobri-lo por smoke-test fragmentado.

10. **Refusal como classe de erro estruturalmente distinta de validation failure.** Caso `subtype="success"` + `stop_reason="refusal"` é load-bearing: SDK declarou sucesso, mas `structured_output` pode estar ausente. Coordinator precisa discriminar ambos os eixos da `ResultMessage`, não apenas o subtype. Pattern: contratos com múltiplos eixos exigem discriminação em todos os eixos, não apenas no eixo aparentemente primário.

11. **Débito catalogado como Provisão é menos custoso que débito implícito.** DD-T15 (layout uniforme) cria débito real (Reporter precisa migrar de `src/coordinator/` para `src/subagents/reporter/`). Estratégia: catalogar como Provisão MC-F (PR housekeeping pré-T11+) em vez de absorver durante implementação T11+. Pattern: débito visível em catálogo enumerável é débito que se elimina antes de virar fricção; débito implícito vira surpresa durante implementação.

12. **Acoplamento explícito ratificado supera ambiguidade deferida.** `Report.scope = TriagerInput` literalmente (per Provisão MC-F) cria versioning coupling deliberado entre TriagerInput e Report payload. Alternativa (mapeamento via mapper layer no coordinator) foi considerada e rejeitada: indireção sem ganho substantivo no contexto atual; (iii) preservar variante hipotetizada de Reporter §8.4 preservaria a ambiguidade que MC-F deveria fechar. Pattern: quando acoplamento é benigno (volume baixo, evolução conjunta esperada), ratificá-lo explicitamente vale mais que evitar via abstração defensiva.

### 10.7 Side findings pendentes investigação

Material para entry #43 do learning-log, abre potencial smoke-test dedicado se demanda concreta emergir:

- **`permission_mode="dontAsk"` em Python.** Doc oficial (`agent-sdk/agent-loop`, tabela de permission modes) declara `dontAsk` como "(TypeScript only)". Projeto usa em Python no SDK 0.2.87 e smoke-tests Gate 1 e `sdk_output_format_lockdown` PASS sob esse modo. Possibilidades: (a) doc desatualizada e dontAsk JÁ funciona em Python; (b) doc certa e dontAsk em Python é no-op silencioso (denial vem dos outros eixos da quíntupla — `allowed_tools` whitelist + `setting_sources=[]` + `strict_mcp_config=True`); (c) comportamento undocumented mas funcional. Fica registrado para investigação empírica futura — possível smoke-test dedicado (~20min) testando 2 variantes (quíntupla completa vs quíntupla sem dontAsk/com outro modo) para discriminar (a) vs (b) vs (c). Não-bloqueante para spec; relevante antes de qualquer PR (e.g., ADR-0012 retroativo sobre defesa em camadas) que escreva sobre `dontAsk` como Camada 4 da defesa em camadas do coordinator §6.