# sdk_mcp_visibility — smoke test

**Propósito.** Discriminar empiricamente entre duas hipóteses sobre
governance de MCP tool visibility no Claude Agent SDK Python, fechando
o Item 4 do Code review V2 da sessão Chat #38 (gap deixado por TC2 do
smoke-test #38b, que testou efeito do `tools` field apenas para tool
built-in `Bash`):

- **H-mcp-via-mcp_servers (principal):** MCP tools governadas pelo
  dict `mcp_servers={...}` em `ClaudeAgentOptions`; sempre visíveis ao
  modelo quando o server está registrado. `tools` field governa apenas
  built-ins.
- **H-mcp-via-tools (alternativa):** MCP tools governadas pelo `tools`
  field junto com built-ins. Se verdade, a tabela DD-9.1 proposta
  (Detector com `tools=["Read"]`) quebraria silenciosamente a
  visibilidade de `mcp__semgrep-runner__scan_diff`.

O resultado destrava prep-PR `docs/coordinator-context-tightening`
(DD-12.6).

Pattern operacional alinhado aos precedents
[`scripts/smoke_tests/sdk_tooluseblock_shape/`](../sdk_tooluseblock_shape/)
(sessão Chat/Code #38) e
[`scripts/smoke_tests/sdk_reporter_gates/`](../sdk_reporter_gates/)
(sessão Code #38b).

## Execução

```powershell
uv run --with claude-agent-sdk==0.2.87 python scripts\smoke_tests\sdk_mcp_visibility\smoke_test.py
```

Ad-hoc dependency via `uv run --with` — não toca `pyproject.toml` nem
`uv.lock` do projeto. SDK version pinada: `claude-agent-sdk==0.2.87`
(mesma versão dos smoke-tests #38 e #38b).

Wall time estimado: 4-6min (4 cenários × 2 runs = 8 queries).

Pré-requisito: Claude Code CLI autenticado (auth herdada de
[smoke-test #38b](../sdk_reporter_gates/README.md#execução)). Não
requer `ANTHROPIC_API_KEY` no shell.

## Cenários

| ID  | `tools`              | `mcp_servers`        | `allowed_tools`                       | Papel |
|-----|----------------------|----------------------|---------------------------------------|-------|
| S1  | `['Read']`           | `{'t': server}`      | `['Read', 'mcp__t__echo_mcp']`         | Discriminador principal |
| S2  | `['Read']`           | `{}`                 | `['Read']`                            | Control negative |
| S3  | _omitido_            | `{'t': server}`      | `['Read', 'mcp__t__echo_mcp']`         | Control positive (halt se falhar) |
| S4  | `['Read']`           | `{'t': server}`      | `['Read']` (sem pre-approval)         | Refinamento |

Prompt comum: *"Please call the mcp__t__echo_mcp tool with text='hello'.
If you cannot call it, explain why and stop. Do not call any other tool."*

## Resultados

Executado em sessão Code #38c. SDK `claude-agent-sdk==0.2.87`.

| Scenario                              | call_success (run1, run2) | num_turns (run1, run2) | verbalizes_absence (run1, run2) | Outras tools observadas | `permission_denials` populado |
|---------------------------------------|---------------------------|-------------------------|----------------------------------|-------------------------|-------------------------------|
| S1_restrict_tools_keep_server         | True, True                | 2, 2                    | False, False                     | nenhuma                 | não                           |
| S2_no_server_at_all                   | False, False              | 1, 1                    | True, True                       | nenhuma                 | não                           |
| S3_no_tools_field_with_server         | True, True                | 3, 3                    | False, False                     | `ToolSearch` (ambos)     | não                           |
| S4_server_present_not_preapproved     | True, True (tentativa)    | 2, 2                    | False, True                      | nenhuma                 | **sim** (ambos runs)          |

**Verdict:** **PASS_H_VIA_MCP_SERVERS**

S1 (discriminador) succeeded em ambos runs — modelo chamou `echo_mcp` mesmo
com `tools=["Read"]` (que não inclui o tool name MCP). MCP tool registrada
em `mcp_servers={...}` permanece visível independente do `tools` field.

S3 (control positive) confirmou setup. S2 (control negative) verbalizou
ausência de forma clean. S4 (refinamento) revelou que, sob lockdown
(`dontAsk` + sem pre-approval), o modelo TENTA chamar a MCP tool (vê no
context) e a denial é registrada em `ResultMessage.permission_denials` —
mesmo comportamento de defesa em profundidade que TC2 #38b mostrou para
Bash. Em run2 de S4 o modelo também verbalizou a denial explicitamente.

### Verbalizações observadas (literal)

- **S2 run1:** `"The tool 'mcp__t__echo_mcp' is not available to me — it isn't in my set of available tools, so I cannot call it."`
- **S2 run2:** `"The tool 'mcp__t__echo_mcp' is not available to me. The only tool I have access to is 'Read'..."`
- **S4 run1:** `"I'll call that tool for you. I attempted to call the 'mcp__t__echo_mcp' tool with 'text=hello', but permission was den..."`
- **S4 run2:** `"I'll call that tool for you. The 'mcp__t__echo_mcp' tool call was denied — permission to use it was refused because the ..."`

### `permission_denials` shape (S4)

```python
[
  {
    "tool_name": "mcp__t__echo_mcp",
    "tool_use_id": "toolu_014vibaK43dv21mJartXyqDH",
    "tool_input": {"text": "hello"},
  }
]
```

Lista de dicts com `tool_name`, `tool_use_id`, `tool_input`. Cf. TC3
#38b onde `permission_denials=[]` em max_turns exhaustion — confirma que
o campo é canal de erro **alternativo** para denial-by-allowed_tools
especificamente, não para outras condições.

## Resolução DD-9.1

**Tabela DD-9.1 ratificada como proposta.** Detector com `tools=["Read"]`
e `mcp_servers={"semgrep-runner": ...}` enxerga e pode invocar
`mcp__semgrep-runner__scan_diff` (modelo: caminho idêntico ao S1). O
`tools` field governa **apenas built-ins**; MCP tools governadas pelo
dict `mcp_servers={...}`.

Tradução para cada subagent do coordinator skeleton:

| Subagent   | `tools` field (built-ins)          | `mcp_servers` dict (MCP inventory)                       | `allowed_tools` (execution gating) |
|------------|------------------------------------|----------------------------------------------------------|-------------------------------------|
| Triager    | `["Bash"]`                         | `{}`                                                     | `["Bash(git diff:*)"]`              |
| Detector   | `["Read"]`                         | `{"semgrep-runner": server}`                             | `["Read", "mcp__semgrep-runner__scan_diff"]` |
| Classifier | `["Read", "Grep"]`                 | `{}` (resources via ListMcpResources opcional)            | `["Read", "Grep", "ListMcpResourcesTool", "ReadMcpResourceTool"]` |
| Matcher    | `["Read"]`                         | `{"policy-reader": server}`                              | `["Read", "ListMcpResourcesTool", "ReadMcpResourceTool", "mcp__policy-reader__check_applicability", "mcp__policy-reader__get_clause", "mcp__policy-reader__find_clauses_by_law_article"]` |
| Reporter   | `["Read"]`                         | `{"reporter_tools": server}`                              | `["Read", "mcp__reporter_tools__emit_report"]` |

Detalhamento per-subagent é editorial do prep-PR DD-12.6.

## Side findings

- **AC-1 — ToolSearch overhead em S3.** Sem `tools` field, MCP tool
  visível mas modelo gasta 1 turn extra em `ToolSearch` (`num_turns=3`
  em S3 vs `num_turns=2` em S1). Com `tools` field setado + MCP tool
  em `allowed_tools`, o schema parece chegar inline (sem ToolSearch).
  Implica que **omitir `tools` field é custo de turn para MCP tools
  também**, não apenas context bloat com built-ins (como visto em TC2
  #38b com Glob/PowerShell). Argumento operacional reforçado para
  setar `tools` field mesmo quando o subagent só usa MCP tools.
- **AC-2 — `permission_denials` como sinal forte.** S4 mostra que
  denial por ausência em `allowed_tools` populates a lista mesmo sob
  `permission_mode="dontAsk"` (modelo TENTA, é denied silenciosamente
  sem prompt ao user, lista preenchida). Coordinator pode inspecionar
  `ResultMessage.permission_denials` pós-loop para detectar tentativas
  inesperadas e tratar como debt signal (subagent tentando tool fora
  do escopo declarado).
- **AC-3 — S4 verbalization assimétrica run1 vs run2.** Run1 modelo
  diz `"I attempted to call ... but permission was denied"`; run2 diz
  `"The tool call was denied — permission to use it was refused"`.
  Diferença factual: ambos runs efetivamente tentam (echo_attempts=1)
  e ambos têm denial populated. Heurística `verbalizes_absence`
  capturou run2 mas não run1 (run1 fala em "permission denied", run2
  fala em "denied — permission to use it was refused"). Não invalida
  o verdict; informa que verbalization wording é levemente
  não-determinístico mesmo sob mesmo setup.
- **AC-4 — `ResultMessage.subtype == "success"` em S4 apesar de
  denial.** Mesmo com `permission_denials` populated, o subtype final
  é `success`, não erro. Confirma que denial-by-allowed_tools NÃO
  surfaces como erro de stream — coordinator MUST inspect
  `permission_denials` explicitamente (não pode confiar só em
  `is_error`).
- **AC-5 — `ToolSearch` aparece em S3 com `name='ToolSearch'`,
  consistente com finding AC2 do #38b.** Filter por `block.name` no
  coordinator loop necessário para ignorar ToolSearch ToolUseBlocks
  (não conta como subagent tool invocation).

## Estrutura

```
sdk_mcp_visibility/
├── smoke_test.py    # 1 TC com 4 cenários × 2 runs + runner com FINAL SUMMARY block
└── README.md        # este arquivo
```

## Quando re-rodar

- Bump de `claude-agent-sdk` para versão diferente de `0.2.87` (em
  particular qualquer mudança em `ClaudeAgentOptions` que envolva
  semantics do `tools` field ou `mcp_servers` dict).
- Suspeita de regressão na separação observada entre context-scoping
  (`tools` + `mcp_servers`) e execution-gating (`allowed_tools`).

Em uso normal sem mudanças acima: one-shot ratchet com valor histórico
documentado, não CI test.

## Refs

- [`scripts/smoke_tests/sdk_reporter_gates/README.md`](../sdk_reporter_gates/README.md) — TC2 (DD-9.1 para built-ins), gap fechado aqui
- [`scripts/smoke_tests/sdk_tooluseblock_shape/README.md`](../sdk_tooluseblock_shape/README.md) — precedent operacional original (smoke-test #38)
- `docs/specs/subagents/coordinator.md` §11 — Gate 1 pattern; prep-PR
  DD-12.6 destination das resoluções fechadas aqui.
