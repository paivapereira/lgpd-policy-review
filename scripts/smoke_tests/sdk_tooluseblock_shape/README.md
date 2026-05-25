# sdk_tooluseblock_shape — smoke test

**Propósito.** Ratchet empírico do Gate 1 do
[`docs/specs/subagents/coordinator.md`](../../../docs/specs/subagents/coordinator.md)
§11: confirma que `ToolUseBlock.input` é o canal canônico de captura
do payload de custom tools no `claude-agent-sdk` Python, e
ratifica a quíntupla canônica do lockdown agent CI/CD-headless
(`permission_mode="dontAsk"` + `setting_sources=[]` +
`strict_mcp_config=True` + `allowed_tools` whitelist + `mcp_servers`
dict).

Originalmente proposto em sessão Chat #38 pós-round-trip de quatro
rounds de review independente. Executado com status **PASS** em
sessão Code dedicada #38.

## Execução

```powershell
uv run --with claude-agent-sdk python scripts/smoke_tests/sdk_tooluseblock_shape/smoke_test.py
```

Ad-hoc dependency via `uv run --with` — não toca `pyproject.toml`
nem `uv.lock` do projeto. SDK version usada na execução de
ratificação: `claude-agent-sdk==0.2.87`. Mínimo da Provisão MC-E
declarada: `>=0.1.59` (para `setting_sources=[]` suportado).

Wall time esperado: ~30s (incluindo network round-trip ao modelo).
Pré-requisito: Claude Code CLI autenticado.

## Output esperado (Pass)

```
Block type: ToolUseBlock
Block module: claude_agent_sdk.types
Block attrs (non-dunder): ['id', 'input', 'name']
block.input value: {'text': 'hello', 'count': 3}

TC1 (ToolUseBlock.input shape):   PASS
TC2 (canonical quintuple e2e):    PASS
TC3 (underscore naming resolve):  PASS
```

## Quando re-rodar

Em qualquer um dos cenários:
- Bump de `claude-agent-sdk` major (atualmente 0.x → 1.x ainda
  hipotético) para reratificar surface estável do `ToolUseBlock`.
- Mudança em qualquer um dos 5 campos da quíntupla canônica usada
  pelo coordinator (`permission_mode`, `setting_sources`,
  `strict_mcp_config`, `allowed_tools`, `mcp_servers`) — verificar
  que SDK ainda aceita.
- Suspeita de regression em filter por `block.name` quando tool
  search está ON (achado AC1 do reporting #38).

Em uso normal (sem mudanças acima), não precisa ser re-rodado. Não é
CI test — é one-shot ratchet com valor histórico documentado.

## Achados ratificados pelo smoke-test

Catalogados em coordinator.md §11 (Gate 1 status PASS). Resumo:

- `ToolUseBlock` surface mínima: 3 atributos exatos (`id`, `name`,
  `input`).
- Quíntupla canônica do lockdown agent funciona end-to-end com SDK
  0.2.87.
- Underscore em server name (`test_tools` → `mcp__test_tools__echo`)
  resolve sem quirks; ratifica recomendação preventiva de §7 para
  `reporter_tools`.
- Tool search está ON por default; stream pode conter
  `ToolUseBlock`s intermediários (ex: `ToolSearch`) antes da tool
  real — filter por `block.name` em §3.5 do coordinator sustenta
  captura correta. Documentado em coordinator.md §3.5 + §5 + §8.

## Refs

- [`docs/specs/subagents/coordinator.md`](../../../docs/specs/subagents/coordinator.md) §11 Gates pré-coordinator-flesh
- [`docs/REQUIREMENTS.md`](../../../docs/REQUIREMENTS.md) RF-006 (Reporter como locus emissor; subjacente ao gate)
- [`docs/learning-log.md`](../../../docs/learning-log.md) entry #38 (a redigir)