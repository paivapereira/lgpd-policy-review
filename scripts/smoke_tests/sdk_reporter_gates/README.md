# sdk_reporter_gates — smoke test

**Propósito.** Três TCs empíricos fechando DDs bloqueadas da spec
`docs/specs/subagents/reporter.md` (sessão Chat #38):

- **TC1** → DD-5.1 (input_schema: Pydantic class vs JSON Schema dict).
- **TC2** → DD-9.1 (efeito observável do `tools` field sob lockdown
  completo).
- **TC3** → DD-10.4 (shape do `ResultMessage` em `max_turns`
  exhausted).

Pattern operacional alinhado ao precedent
[`scripts/smoke_tests/sdk_tooluseblock_shape/`](../sdk_tooluseblock_shape/)
(sessão Chat/Code #38).

## Execução

```powershell
uv run --with claude-agent-sdk==0.2.87 python scripts\smoke_tests\sdk_reporter_gates\smoke_test.py
```

Ad-hoc dependency via `uv run --with` — não toca `pyproject.toml` nem
`uv.lock` do projeto. SDK version pinada: `claude-agent-sdk==0.2.87`
(mesma versão do smoke-test #38; sem delta de comportamento esperado
nos TCs herdados).

Wall time estimado: 3-5min (TC2 roda 8 queries: 4 cenários × 2 runs).

Pré-requisito: Claude Code CLI autenticado (auth herdada de
[smoke-test #38](../sdk_tooluseblock_shape/README.md#execução)). Não
requer `ANTHROPIC_API_KEY` no shell.

## Resultados

Executado em sessão Code #38b. SDK `claude-agent-sdk==0.2.87`.

| TC  | DD bound | Verdict           | Key finding |
|-----|----------|-------------------|-------------|
| TC1 | DD-5.1   | PARTIAL           | Pydantic class direto **degrada** `list[str]` para string JSON-encoded; `BaseModel.model_json_schema()` ratificado como caminho canônico |
| TC2 | DD-9.1   | PASS_H_EFFECTIVE  | `tools` field é layer effective de restrição de context mesmo sob lockdown completo; ratifica adicionar ao coordinator skeleton |
| TC3 | DD-10.4  | PASS              | `subtype='error_max_turns'` + `is_error=True` + `errors=['Reached maximum...']` é discriminador único; SDK também **raise Exception** após yield do ResultMessage |

### TC1 — DD-5.1 detalhado

Ambos variants decoraram OK (sem exception em `@tool(...)`). Ambos
foram invocados pelo modelo. Diferença observada nos args
recebidos pelo handler:

| Variant            | `title`   | `tags`            |
|--------------------|-----------|-------------------|
| pydantic_type      | `'hello'` | `'["a", "b"]'` (string JSON-encoded) |
| jsonschema_dict    | `'hello'` | `['a', 'b']` (native list) |

Interpretação: o `@tool` decorator, ao receber uma BaseModel class
direto como `input_schema`, gera internamente um schema lossy que
representa `list[str]` como string. Não há crash — degradação
silenciosa. `BaseModel.model_json_schema()` gera JSON Schema
completo (`{"type": "array", "items": {"type": "string"}}`) que o
modelo respeita produzindo array nativo.

**Resolução DD-5.1:** ratifica JSON Schema dict via
`BaseModel.model_json_schema()`. Spec do Reporter deve **NÃO** usar
Pydantic class direto no `@tool` decorator — risco de mojibake de
tipos compostos (lists, dicts, nested objects).

### TC2 — DD-9.1 detalhado

Per-scenario (2 runs cada, S1/S2 são H-relevant; S3/S4 são
auxiliary controls):

| Scenario               | `tools`              | `allowed_tools`      | Bash attempts (run1, run2) | num_turns | Outras tools observadas |
|------------------------|----------------------|----------------------|-----------------------------|-----------|-------------------------|
| S1_minimal             | `['Read']`           | `['Read']`           | 0, 0                        | 1, 1      | nenhuma — modelo desiste |
| S2_expanded            | `['Read', 'Bash']`   | `['Read']`           | 1, 1                        | 2, 2      | só Bash (denied)         |
| S3_no_tools_field      | _omitted_            | `['Read']`           | 0, 1                        | 2, 2      | Glob (run1)              |
| S4_bash_authorized     | _omitted_            | `['Read', 'Bash']`   | 0, 0                        | 3, 2      | Glob, PowerShell         |

**H-effective ratificada:**

- S1 (tools=['Read']): modelo verbaliza `"I can't list the
  directory contents with the tools available to me"` — context
  realmente restrito ao Read, modelo sequer tenta outros tools.
- S2 (tools inclui Bash mas allowed não): modelo TENTA Bash (vê no
  context), é denied pelo allowed_tools, completa via Read.
  Diferença observável de comportamento vs S1.
- S3 (sem tools field): modelo vê toolset completo do Claude Code
  e escolhe variavelmente — run1 usou Glob, run2 usou Bash. Sem
  tools field, há context bloat e turn variability.
- S4 (sem tools field, Bash autorizado): mesmo com Bash
  autorizado, modelo preferiu Glob/PowerShell. Confirma que
  toolset completo do Claude Code está visível quando tools field
  é omitido.

**Resolução DD-9.1:** ratifica setar `tools` field na
`ClaudeAgentOptions` do Reporter (e do coordinator). Não é
redundante sob lockdown — é a camada que restringe **context**,
enquanto `allowed_tools` restringe **execution**. Sem tools field,
turn budget é desperdiçado em tentativas de tools alternativos
(Glob, Bash, PowerShell) que o modelo descobre via inspection.

### TC3 — DD-10.4 detalhado

`ResultMessage` capturado integralmente. Campos relevantes:

```python
subtype = 'error_max_turns'      # discriminator único — não confundir com 'success' nem 'error_during_execution'
is_error = True
stop_reason = 'tool_use'         # NOT 'end_turn' nem 'max_tokens' — última action foi tool_use cortada
num_turns = 3                    # off-by-one: max_turns=2 cap mas reporta 3 (tentou turn 3 e foi barrado)
errors = ['Reached maximum number of turns (2)']
permission_denials = []
api_error_status = None
result = None
```

**SDK behavior crítico:**

1. SDK **yields** o `ResultMessage` no async iterator (capturável
   no loop normal).
2. SDK **logo depois raise** `Exception("Claude Code returned an
   error result: Reached maximum number of turns (2)")` —
   propaga após o yield.

Coordinator/caller **deve** wrap o `async for` em try/except:

```python
try:
    async for msg in query(prompt=..., options=options):
        if isinstance(msg, ResultMessage):
            final_result = msg          # CAPTURA antes da exception
except Exception as exc:
    # final_result já está populado se ResultMessage foi yielded
    if final_result and final_result.subtype == "error_max_turns":
        # propagar ReporterTurnsExhausted vs ReportNotEmitted
        ...
```

**Resolução DD-10.4:** discriminador é `subtype ==
"error_max_turns"`. Coordinator pode distinguir:

- **ReporterTurnsExhausted** (proposta nova): `is_error=True` E
  `subtype=='error_max_turns'` E nenhum `emit_report` ToolUseBlock
  no stream → Reporter foi cortado antes de emitir.
- **ReportNotEmitted** (proposta original): `is_error=False` E
  `subtype=='success'` E nenhum `emit_report` ToolUseBlock no
  stream → Reporter terminou turn naturalmente sem emitir.

Ambos errorCodes são distinguíveis. Spec do Reporter pode adotar
dois errorCodes separados, ou colapsar em um (`ReportNotEmitted`
genérico) cobrindo ambos casos — escolha editorial.

### Side findings (AC)

- **AC-1 (TC1):** Pydantic class direto NÃO valida args server-side
  via Pydantic — handler recebe dict bruto. Validation acontece
  apenas a montante via JSON Schema (que para Pydantic class está
  degradado). Tradeoff documentado.
- **AC-2 (TC2):** ToolSearch está ON por default (consistente com
  finding AC1 de [smoke-test #38](../sdk_tooluseblock_shape/README.md)).
  Em TC3, ToolUseBlock `ToolSearch(query='select:mcp__tc3_tools...')`
  apareceu no stream. Filter por `block.name` necessário para
  ignorar.
- **AC-3 (TC2):** Verbalização do modelo quando context é
  restrito a uma única tool: `"I can't list the directory contents
  with the tools available to me"` / `"I'm unable to ... with the
  tools I have available"`. Informa few-shot wording em DD-7.2 do
  Reporter.
- **AC-4 (TC3):** `num_turns` retorna `cap + 1` (configured 2,
  reportado 3). Off-by-one consistente — modelo conta a tentativa
  de turn 3 antes de ser barrado. Coordinator não deve usar
  `num_turns == max_turns` como check; usar `subtype` discriminator.
- **AC-5 (TC3):** `permission_denials` é list vazia em max_turns
  exhaustion. Não é canal de erro alternativo para esta condição.
- **AC-6 (TC3):** Multi-model usage observado — `model_usage` mostra
  uso de `claude-haiku-4-5` (478 input tokens) E `claude-opus-4-7[1m]`
  (1546 input tokens) na mesma query. SDK internamente delega
  tasks (provavelmente ToolSearch via Haiku, main loop via Opus).
  Não-óbvio para budgeting de custo.

## Estrutura

```
sdk_reporter_gates/
├── smoke_test.py    # 3 async TCs + runner com FINAL SUMMARY block
└── README.md        # este arquivo
```

Cada TC retorna dict `{name, verdict, summary, details}`. Runner
imprime FINAL SUMMARY paste-ready para Chat triage no fim do stdout.

## Quando re-rodar

- Bump de `claude-agent-sdk` para versão diferente de `0.2.87` (em
  particular, qualquer bump major que possa mudar shape do
  `ResultMessage`, semantics do `tools` field, ou validation do
  `input_schema` no `@tool` decorator).
- Suspeita de regressão em qualquer das 3 areas testadas
  (decoration acceptance, tools-field effect, ResultMessage shape).

Em uso normal sem mudanças acima: one-shot ratchet com valor
histórico documentado, não CI test.

## Refs

- [`docs/specs/subagents/coordinator.md`](../../../docs/specs/subagents/coordinator.md) §11 — precedent Gate 1 pattern
- [`scripts/smoke_tests/sdk_tooluseblock_shape/README.md`](../sdk_tooluseblock_shape/README.md) — precedent operacional (smoke-test #38)
- `docs/specs/subagents/reporter.md` (forthcoming) — spec destination
  das DDs fechadas aqui
