# sdk_tools_empty_list — smoke test

**Propósito.** Discriminar empiricamente entre três hipóteses sobre
como o SDK `claude-agent-sdk==0.2.87` trata `tools=[]` (lista vazia
explícita) no `ClaudeAgentOptions`. Gate 6 da sessão Chat (finding #3
do review V2 do prep-PR `docs/coordinator-context-tightening`).

- **H-empty-lockdown (principal):** `tools=[]` remove todos built-ins
  do contexto do modelo, deixando apenas MCP tools de
  `mcp_servers={...}` + `allowed_tools=[...]`. Semântica de "allowlist
  vazia". Precedent conceitual: `setting_sources=[]` pós-0.1.60
  ("carregar nada").
- **H-empty-as-none (alt 1):** `tools=[]` é tratado como `tools=None`
  (omissão), i.e., todos built-ins continuam visíveis. Lista vazia ==
  ausência. Precedent conceitual: `setting_sources=[]` pré-0.1.60.
- **H-empty-raises (alt 2):** SDK rejeita `tools=[]` durante init de
  `ClaudeAgentOptions` ou no `query()` — sintaxe inválida.

A resolução destrava ou invalida o pivot do finding #3 do review V2
para coordinator §3.4 e §3.5 (Reporter e Matcher), onde se propôs
trocar `tools=["Read"]` (defensive minimum) por `tools=[]` (lockdown)
porque esses subagents não usam built-ins do Claude Code.

Pattern operacional alinhado aos precedents
[`scripts/smoke_tests/sdk_tooluseblock_shape/`](../sdk_tooluseblock_shape/)
(sessão Chat/Code #38),
[`scripts/smoke_tests/sdk_reporter_gates/`](../sdk_reporter_gates/)
(sessão Code #38b), e
[`scripts/smoke_tests/sdk_mcp_visibility/`](../sdk_mcp_visibility/)
(sessão Code #38c). Discriminação via comportamento (não introspecção
de `SystemMessage`).

## Execução

```powershell
uv run --with claude-agent-sdk==0.2.87 python scripts\smoke_tests\sdk_tools_empty_list\smoke_test.py
```

Ad-hoc dependency via `uv run --with` — não toca `pyproject.toml` nem
`uv.lock` do projeto. SDK version pinada: `claude-agent-sdk==0.2.87`
(mesma dos smoke-tests #38, #38b, #38c).

Wall time estimado: 3-5min (3 cenários × 2 runs = 6 queries).

Pré-requisito: Claude Code CLI autenticado (auth herdada de
[smoke-test #38](../sdk_tooluseblock_shape/README.md#execução)). Não
requer `ANTHROPIC_API_KEY` no shell.

## Cenários

| ID                    | `tools`        | `mcp_servers`    | `allowed_tools`                       | Papel                          |
|-----------------------|----------------|------------------|---------------------------------------|--------------------------------|
| S1_baseline_none      | _omitido_      | `{'t': server}`  | `['Read', 'Bash', ECHO_TOOL]`         | Control positive               |
| S2_hypothesis_empty   | `[]`           | `{'t': server}`  | `['Read', 'Bash', ECHO_TOOL]`         | Discriminador principal        |
| S3_sanity_read_only   | `['Read']`     | `{'t': server}`  | `['Read', 'Bash', ECHO_TOOL]`         | Control ratificado (#38b TC2)  |

Prompt comum: *"Please do two things in order. First: call the
mcp__t__echo_mcp tool with text='hello'. Second: run the Bash tool
with command='echo bashtest'. If you cannot call one of them, explain
plainly which one and why, then continue with what you can call. Do
not substitute other tools."*

`allowed_tools` inclui `Bash` em todos os cenários para que o sinal de
contexto não seja mascarado por denial de execução. A diferença
observada entre cenários é puramente de **visibilidade do tool no
contexto do modelo**.

### Predições por hipótese

| Cenário              | H-empty-lockdown   | H-empty-as-none    | H-empty-raises |
|----------------------|--------------------|--------------------|----------------|
| S1_baseline_none     | Bash attempted     | Bash attempted     | (N/A — só S2)  |
| S2_hypothesis_empty  | Bash NOT attempted | Bash attempted     | init exception |
| S3_sanity_read_only  | Bash NOT attempted | Bash NOT attempted | (N/A — só S2)  |

Echo MCP tool deve succeed em todos cenários (governada por
`mcp_servers={...}` per #38c, ortogonal ao `tools` field).

## Resultados

Executado em sessão Code Gate 6. SDK `claude-agent-sdk==0.2.87`. Auth
via Claude Code CLI.

| Scenario              | echo (run1, run2) | bash (run1, run2) | verbalize_absence (run1, run2) | Outras tools observadas | `permission_denials` populado | num_turns (run1, run2) |
|-----------------------|-------------------|-------------------|--------------------------------|-------------------------|-------------------------------|------------------------|
| S1_baseline_none      | 1, 1              | 1, 1              | False, False                   | `ToolSearch` (ambos)     | não                           | 4, 4                   |
| S2_hypothesis_empty   | 1, 1              | **0, 0**          | True, True                     | nenhuma                  | não                           | 2, 2                   |
| S3_sanity_read_only   | 1, 1              | 0, 0              | True, True                     | nenhuma                  | não                           | 2, 2                   |

**Verdict:** **PASS_H_EMPTY_LOCKDOWN**

S2 (`tools=[]`) comportamento idêntico a S3 (`tools=['Read']`): modelo
não tentou Bash em nenhum run, verbalizou ausência explicitamente, MCP
tool echo continuou callable. S1 (`tools=None`, baseline) tentou Bash
em ambos runs como esperado. Hipótese principal ratificada — `tools=[]`
é signal válido de lockdown maximal de built-ins, equivalente a
"allowlist vazia" e não a "omissão".

### Verbalizações observadas (literal, trimmed)

- **S2 run1:** `"I'll call the echo tool now, then address the Bash request. Done with the first task — the mcp__t__echo_mcp tool returned: 'echo: hello'. For the second task..."`
- **S2 run2:** `"I'll start with the tool I can call. Done with the first task — mcp__t__echo_mcp returned 'echo: hello'. For the second task: I cannot call the Bash tool..."`
- **S3 run1:** `"I'll start with the echo tool I can call. Done with the first task — the echo tool returned: 'echo: hello'. For the second task: I cannot call the Bash tool..."`
- **S3 run2:** `"I'll call the echo tool now, and address the Bash request after. Done with the first task — the mcp__t__echo_mcp tool returned 'echo: hello'. For the second task..."`

Verbalização de S2 é qualitativamente indistinguível de S3 — sinal
forte de que o contexto do modelo nos dois cenários é o mesmo do
ponto de vista de Bash (ausente em ambos).

### Resolução finding #3 do review V2

**Pivot procede.** Coordinator §3.4 (Reporter) e §3.5 (Matcher) podem
substituir `tools=["Read"]` por `tools=[]` para context restriction
maximal, sem prejudicar visibilidade de MCP tools registradas em
`mcp_servers={...}` (governadas por canal ortogonal per #38c). Edit
deve ser feito em **PR separado** per pattern de PR sequencing
(`.claude/rules/git-conventions.md` §PR sequencing).

A mudança é minimal: para os subagents que não usam built-ins do Claude
Code (Reporter, Matcher), `tools=[]` é mais alinhado à recomendação
Anthropic oficial (`platform.claude.com/docs/en/agent-sdk/custom-tools`)
do que `disallowed_tools=[...]` (que deixa o tool visível e gera
"wasted turn" de denial).

## Side findings

- **AC-1 — `ToolSearch` aparece apenas em S1 (`tools=None`).** Sem
  `tools` field, modelo trata MCP tools como "deferred" e usa
  `ToolSearch` para carregar schema (`others=['ToolSearch']` em ambos
  runs de S1). Em S2 (`tools=[]`) e S3 (`tools=['Read']`), o schema
  da MCP tool aparece inline, sem ToolSearch. Implica que `tools=[]`
  herda o **benefício de turn economy** de `tools=[built-in,...]` —
  num_turns=2 em S2/S3 vs num_turns=4 em S1. Reforça argumento
  operacional para setar `tools` field (mesmo vazio) sempre que o
  conjunto de built-ins necessário ao subagent for empty ou pequeno.
- **AC-2 — `permission_denials=[]` em S2/S3.** Modelo não TENTA Bash
  em S2 nem em S3 (`bash_attempt_count=0`), portanto não há denial
  para registrar. Confirma que `tools` field age na camada de
  **context** (modelo decide não tentar) e não na de **execution**
  (denied após attempt). Contraste com S4 do smoke-test #38c onde
  `permission_denials` foi populated porque o modelo TENTOU a MCP
  tool e foi bloqueado em allowed_tools.
- **AC-3 — Não há precedent para inspecionar `SystemMessage.tools`
  neste projeto.** Este smoke-test mantém o pattern empírico de
  discriminação behavioral usado em #38, #38b, #38c. Introspecção de
  shape do `SystemMessage` foi considerada mas evitada — shape do
  SDK pode mudar entre versões, comportamento do modelo é mais
  estável.
- **AC-4 — `subtype='success'` em todos cenários.** Independente de
  `tools` field setting, o fim natural do turn é `success`. Não há
  signal de erro em nenhum cenário. Coordinator deve continuar a
  inspecionar `permission_denials` e ausência de ToolUseBlock
  esperado para detectar problemas (per #38b TC3 AC-5 e #38c AC-4).
- **AC-5 — Comportamento de `ToolSearch` em S1.** O bloco aparece
  com `name='ToolSearch'` consistente com AC-2 #38b e AC-5 #38c.
  Filter por `block.name` em coordinator loop continua necessário
  para ignorar ToolSearch como subagent tool invocation.

## Estrutura

```
sdk_tools_empty_list/
├── smoke_test.py    # 1 TC com 3 cenários × 2 runs + runner com FINAL SUMMARY block
└── README.md        # este arquivo
```

## Quando re-rodar

- Bump de `claude-agent-sdk` para versão diferente de `0.2.87` (em
  particular qualquer mudança em `ClaudeAgentOptions` que envolva
  semantics do `tools` field, incluindo possível mudança de empty-list
  semantics análoga ao que aconteceu com `setting_sources` no SDK
  0.1.60).
- Suspeita de regressão em separação observada entre context-scoping
  (`tools` + `mcp_servers`) e execution-gating (`allowed_tools`).

Em uso normal sem mudanças acima: one-shot ratchet com valor histórico
documentado, não CI test.

## Refs

- [`scripts/smoke_tests/sdk_reporter_gates/README.md`](../sdk_reporter_gates/README.md) — TC2 (DD-9.1) ratificou que `tools=['Read']` esconde Bash do contexto; precedent para S3 deste smoke-test
- [`scripts/smoke_tests/sdk_mcp_visibility/README.md`](../sdk_mcp_visibility/README.md) — `mcp_servers={...}` governa MCP tool visibility ortogonal ao `tools` field; precedent para echo MCP sanity
- `docs/specs/subagents/coordinator.md` §3.4, §3.5 — destino da resolução: Reporter e Matcher subagent configs
