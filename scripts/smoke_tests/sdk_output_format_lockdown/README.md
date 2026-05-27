# sdk_output_format_lockdown — smoke test

**Propósito.** Discriminar empiricamente entre três hipóteses sobre
`output_format=` em `claude-agent-sdk==0.2.87` quando combinado com
lockdown completo (`allowed_tools=[]`, `setting_sources=[]`,
`mcp_servers={}`, `strict_mcp_config=True`, `permission_mode="dontAsk"`).
Pre-gate Fase 0 da sessão Chat (Branch B do plano de aderência ao SDK).

Dois gates simultâneos no mesmo run:

- **Gate 1 — feature existe?** `ClaudeAgentOptions(output_format={...})`
  aceita o param sem `TypeError`/`AttributeError`?
- **Gate 2 — validação schema funciona sob lockdown?** Se Gate 1 PASS,
  a query converge para `ResultMessage.subtype == "success"` ou
  termina em `error_max_structured_output_retries`?

Pattern operacional alinhado aos precedents
[`scripts/smoke_tests/sdk_tools_empty_list/`](../sdk_tools_empty_list/)
(Gate 6),
[`scripts/smoke_tests/sdk_mcp_visibility/`](../sdk_mcp_visibility/)
(#38c), e
[`scripts/smoke_tests/sdk_reporter_gates/`](../sdk_reporter_gates/)
(#38b). Discriminação via comportamento real (subtype no
ResultMessage) e não via introspecção de shape do `ClaudeAgentOptions`.

## Execução

```powershell
uv run --with claude-agent-sdk==0.2.87 python scripts\smoke_tests\sdk_output_format_lockdown\smoke_test.py
```

Ad-hoc dependency via `uv run --with` — não toca `pyproject.toml` nem
`uv.lock` do projeto. SDK version pinada: `claude-agent-sdk==0.2.87`.

Wall time estimado: 30s-2min (1 query única, lockdown total).

Pré-requisito: Claude Code CLI autenticado (auth herdada de
smoke-tests anteriores). Não requer `ANTHROPIC_API_KEY` no shell.

## Cenário único

| Param                  | Valor                                                       |
|------------------------|-------------------------------------------------------------|
| `system_prompt`        | `"Você é um Triager. Decida proceed/skip com rationale curto."` |
| `allowed_tools`        | `[]`                                                        |
| `permission_mode`      | `"dontAsk"`                                                 |
| `setting_sources`      | `[]`                                                        |
| `strict_mcp_config`    | `True`                                                      |
| `mcp_servers`          | `{}`                                                        |
| `output_format`        | `{"type": "json_schema", "schema": TriagerDecisionStub.model_json_schema()}` |

Schema Pydantic stub:

```python
class TriagerDecisionStub(BaseModel):
    decision: Literal["proceed", "skip"]
    rationale: str
```

Prompt: *"Decida: proceed ou skip para este diff trivial: 'docs:
typo fix'. Devolva JSON estruturado."*

### Branches por sinal observado

| Sinal                                                       | Branch                | Exit code |
|-------------------------------------------------------------|-----------------------|-----------|
| `TypeError`/`AttributeError` em init `ClaudeAgentOptions`   | Caminho 3 (feature inexistente em 0.2.87) | 3 |
| `ResultMessage.subtype == "success"`                        | Branch B viável        | 0 |
| `ResultMessage.subtype == "error_max_structured_output_retries"` | Gate 2 falha (investigar) | 1 |
| Outro subtype ou exceção inesperada                         | Inconclusivo           | 4 |

## Resultados

Executado em sessão Code pre-Fase 0. SDK `claude-agent-sdk==0.2.87`.
Auth via Claude Code CLI.

| Gate   | Observação                                          | Resultado |
|--------|------------------------------------------------------|-----------|
| Gate 1 | `ClaudeAgentOptions(output_format={...})` aceita    | PASS      |
| Gate 2 | `ResultMessage.subtype == 'success'`                | PASS      |

`ResultMessage.structured_output` literal:

```json
{
  "decision": "skip",
  "rationale": "Diff trivial — apenas correção de typo em docs, sem impacto funcional, de comportamento ou de risco. Não justifica review."
}
```

Mensagens observadas (7 total): `SystemMessage(init)`,
`RateLimitEvent`, 3× `AssistantMessage` (intermediárias),
`UserMessage`, `AssistantMessage` (final com texto humano +
estrutura), `ResultMessage(success)` com `structured_output`
populado.

**Verdict:** **BRANCH_B_VIÁVEL**

`output_format={"type":"json_schema","schema":...}` é aceito no init
de `ClaudeAgentOptions` em 0.2.87, e a query converge para
`subtype='success'` mesmo sob lockdown completo (`allowed_tools=[]`,
`setting_sources=[]`, `mcp_servers={}`, `strict_mcp_config=True`,
`permission_mode="dontAsk"`). `structured_output` valida contra o
schema Pydantic stub.

### Side findings

- **SF-1 — Coexistência human text + structured_output.** Modelo
  emitiu tanto texto humano em PT-BR em `AssistantMessage` final
  ("Decisão: **skip** — correção de typo em docs é trivial, sem
  impacto funcional ou de risco, não justifica review.") quanto
  `structured_output` validado no `ResultMessage`. Não há
  necessidade de prompt suprimir prosa para obter estrutura — o
  SDK separa os canais. Implica que branch B pode permitir tom
  conversacional do subagent sem prejuízo da estrutura.
- **SF-2 — `RateLimitEvent` aparece no stream.** Tipo de mensagem
  não observado nos smoke-tests anteriores deste projeto. Confirma
  que loop de `async for msg in query(...)` em coordinator deve
  ignorar (ou ao menos tolerar) tipos de mensagem que não sejam
  `AssistantMessage`/`UserMessage`/`ResultMessage`/`SystemMessage`.
  Filter por `isinstance(msg, AssistantMessage)` continua sendo o
  pattern correto.
- **SF-3 — Múltiplos `AssistantMessage` antes do `ResultMessage`.**
  Modelo emitiu 4 `AssistantMessage` no total para uma decisão
  trivial. Sugere que validation retry interno do SDK pode usar
  rounds adicionais — não observado erro, mas consumo de turns é
  maior que o esperado para um output simples. Coordinator deve
  considerar este overhead ao calcular `num_turns` budget para
  subagents que usem `output_format=`.

## Estrutura

```
sdk_output_format_lockdown/
├── smoke_test.py    # 1 cenário × 1 run com Gate 1 e Gate 2 sequenciais
└── README.md        # este arquivo
```

## Quando re-rodar

- Bump de `claude-agent-sdk` para versão diferente de `0.2.87` (em
  particular qualquer release notes que mencione `output_format`,
  `structured_output`, ou JSON schema validation).
- Mudança no perfil de lockdown adotado pelo coordinator (e.g.,
  abrir `setting_sources`, `mcp_servers`, ou `strict_mcp_config`).

Em uso normal sem mudanças acima: one-shot ratchet com valor
histórico documentado, não CI test.

## Refs

- [`scripts/smoke_tests/sdk_tools_empty_list/README.md`](../sdk_tools_empty_list/README.md) — Gate 6, precedent de discriminação behavioral sob lockdown.
- [`scripts/smoke_tests/sdk_mcp_visibility/README.md`](../sdk_mcp_visibility/README.md) — `mcp_servers={...}` ortogonal a outros params.
- [`scripts/smoke_tests/sdk_reporter_gates/README.md`](../sdk_reporter_gates/README.md) — DD-9.1 ratificou padrão de smoke-test pre-implementação.
