# RESULTS - smoke-test do capture loop (L2), sessão #50

> Insumo verificado para o `coordinator-flesh-completo` (MC-A) e artefato de
> defesa do TCC. Probes em `probe.py` (mesma pasta). Padrão espelha
> `scripts/smoke_tests/check_applicability_48b/` (#48-b): probe + RESULTS
> persistido.

## Objetivo

Fechar empiricamente três premissas do capture loop dos stages Branch B
(Triager/Detector/Classifier/Matcher) e do stage Reporter, antes de
materializar o flesh do coordinator:

- **ST-B** - o bug do wrapper `{"output":{...}}` (issues #502/#571 do SDK)
  derruba `structured_output` a `None` num schema enum-tag normal?
- **ST-C** - sob refusal de safety com `output_format` setado, como o SDK
  reporta a recusa (`subtype` / `stop_reason` / `is_error` /
  `structured_output`)? O stream levanta?
- **ST-A'** - em run limpo, `permission_denials` vem `[]` ou `None`?

## Ambiente verificado

- `python --version` - 3.12.7 (pyenv-win)
- `claude-agent-sdk` metadata version - **0.2.87** (== ADR-0001 D2 / MC-E)
- CLI: `claude.ps1` em PATH (auth da sessão Claude Code; sem `ANTHROPIC_API_KEY`
  nem `CLAUDE_CODE_OAUTH_TOKEN` no env)
- Windows 11 corporativo, PowerShell 5.1, sem WSL

## Achados estáticos (confirmados fora do live; não re-testar)

Introspecção do pacote 0.2.87 instalado:

- `ResultMessage` (dataclass, `types.py`) carrega `stop_reason: str | None`,
  `structured_output: Any`, `permission_denials: list[Any] | None`,
  `errors: list[str] | None` - todos com default `None`.
- `_internal/message_parser.py`: `permission_denials=data.get("permission_denials")`,
  `stop_reason=data.get("stop_reason")`, `errors=data.get("errors")` -> **sem
  default**, logo `None` quando a chave falta. -> discriminação por **truthiness**,
  nunca `== []` / `!= []`.
- `structured_output=data.get("structured_output")` - **passthrough puro**, sem
  unwrap client-side do `{"output":{...}}` (a correção pedida em #571 não está no
  0.2.87).
- `stop_reason` adicionado ao `ResultMessage` **Python** em 0.1.46 (#619);
  presente no 0.2.87. A página oficial do guia de stop-reasons que diz "TS-only"
  está stale.

## Resultados crus (live, 0.2.87)

### ST-B - caminho enum-tag normal

```
===== ST-B wrapper/structured_output (caminho normal) =====
  subtype           = 'success'
  stop_reason       = 'end_turn'
  is_error          = False
  num_turns         = 2
  structured_output = {'decision': 'proceed', 'relevance_summary': 'O PR introduz
    coleta de email em formulário de cadastro. Email é dado pessoal sob a LGPD
    (Art. 5o, I), portanto o handling configura operação de tratamento (coleta)
    relevante para revisão de conformidade — exige verificação de base legal,
    finalidade declarada e citação de clause_id aplicável.'}
  permission_denials= []
  errors            = None
```

### ST-C - refusal + structured_output (captura robusta)

```
===== ST-C refusal + structured_output =====
  subtype           = 'success'
  stop_reason       = 'refusal'
  is_error          = True
  num_turns         = 1
  structured_output = None
  permission_denials= []
  errors            = None

  >>> stream RAISED apos result: Exception: Claude Code returned an error result: success
```

## Análise de ordering (fonte do SDK, 0.2.87)

Loop `_read_messages` em `claude_agent_sdk/_internal/query.py`. Âncora por
**conteúdo**, não por linha (linhas drift entre versões; aprox. 0.2.87 entre
parênteses):

1. No corpo do loop, o bloco `if msg_type == "result":` **não tem `continue`**.
   Seta `_first_result_event`; se `is_error`, monta
   `_last_error_result_text = "; ".join(errors) or str(subtype)` (~304-308).
2. Ao fim do corpo, `await self._message_send.send(message)` (~322) envia o
   result ao stream - **incondicional**: success, refusal, e todos os
   `error_*` subtypes.
3. Quando o CLI emite result `is_error=True`, ele **sai com código não-zero de
   propósito** (comentário no fonte: "e.g. `error_max_turns`,
   `error_during_execution`"). Esse exit vira `ProcessError`, capturado no
   `except` do loop (~328), que o substitui por
   `{"type":"error", "error":"Claude Code returned an error result: <texto>"}`
   (~340-353).
4. No consumidor, `{"type":"error"}` vira `raise Exception(...)` (~852).

**Garantia por construção:** o send do result (passo 2, dentro do corpo do
loop) **precede** o `except` (passo 3, pós-iteração). Logo o `ResultMessage`
chega ao consumidor **antes** da exceção, em todos os subtypes de erro - não só
no refusal.

**Por que a string da exceção é inútil:** no ST-C, `errors == []`, então
`"; ".join([])` -> `""` -> fallback `str(subtype)` = `"success"`. Daí o
"returned an error result: **success**". Discriminar por `last_result`, nunca
pela string.

## Matriz de cenários (ST-B/ST-C provados; restante derivado da fonte)

| Cenário | result enviado? | raise? | `last_result` após o loop |
|---|---|---|---|
| success feliz (`is_error=False`) | sim | não | populado · `subtype=success` · `end_turn` |
| refusal (`is_error=True`, `subtype=success`) | sim | sim | populado · `stop_reason=refusal` ✓ |
| `error_max_turns` | sim | sim | populado · esse `subtype` |
| `error_during_execution` | sim | sim | populado · esse `subtype` |
| `error_max_structured_output_retries` | sim | sim | populado · esse `subtype` |
| crash real de transporte/reader (sem result) | **não** | sim (`str(e)`) | **None** |

## Conclusões por ponto

- **ST-B - wrapper NÃO se manifesta no schema enum-tag simples.**
  `structured_output` populado e válido. -> `SubagentValidationFailed` não
  precisa admitir retry por wrapper no caminho feliz do Triager.
  **Ressalva:** #502/#571 reportam o wrapper em schemas complexos (arrays
  grandes, union discriminada). O output do **Matcher** (`list[Finding]`,
  variantes por `verdict`) e do **Detector** (`list[DetectorFinding]`) têm esse
  perfil - observação mantida para esses dois stages; não generalizar "wrapper
  inexistente" a partir do schema mais simples.

- **ST-C - a premissa "success+refusal" estava certa, mas com dois ajustes:**
  (a) `subtype` **mente** sob refusal (continua `'success'`); o discriminador
  confiável é `stop_reason == "refusal"`, corroborado por `is_error == True` e
  `structured_output is None`. (b) o stream **levanta** - mas o `ResultMessage`
  é capturável com try/except (ordering acima).

- **ST-A' - `permission_denials == []`** nos dois runs (B e C). O CLI real
  emite a chave com lista vazia; o parser daria `None` se ausente. O fix por
  truthiness cobre os dois. Ratificado sem run dedicado.

- **Ordering - emissão incondicional do result antes do raise.** A tabela
  subtype->exceção da `detector.md` §6.3 é integralmente alcançável via
  `last_result.subtype`. A única linha `None` é exatamente o
  `CoordinatorStreamFailure`.

## Padrão de capture loop derivado (entra no coordinator flesh, §5/capture)

```python
last_result = None
try:
    async for msg in query(prompt=..., options=opts):
        if isinstance(msg, ResultMessage):
            last_result = msg                      # sem break - eventos trailing
except Exception as e:
    if last_result is None:
        raise CoordinatorStreamFailure(stage=...) from e
    # senão: raise é o exit deliberado pós-result; last_result manda
if last_result is None:
    raise CoordinatorStreamFailure(stage=...)      # caso sem exceção também
if last_result.stop_reason == "refusal":           # PRECEDE subtype (que mente: 'success')
    raise SubagentRefusedTask(stage=...)
match last_result.subtype:
    case "error_max_turns" | "error_max_budget_usd": raise SubagentUnresponsive(stage=...)
    case "error_during_execution":                   raise SubagentExecutionError(stage=...)
    case "error_max_structured_output_retries":      raise SubagentValidationFailed(stage=...)
    case "success":
        obj = StageModel.model_validate(last_result.structured_output)  # defense-in-depth
        # + verificação posicional de passthrough (G4) -> SubagentContractViolation
    case _:
        raise SubagentExecutionError(stage=..., detail=f"unexpected subtype {last_result.subtype!r}")
```

Notas de materialização para o flesh:

- `stop_reason == "refusal"` **antes** do `match subtype` é load-bearing: sob
  refusal, `subtype` é `"success"`; checar subtype primeiro mandaria o refusal
  para o ramo de `model_validate` (que receberia `None`) e o mis-classificaria
  como `SubagentValidationFailed`.
- Stage **Reporter** (§3.5): a triangulação de §6.5 usa `denials != []` /
  `denials == []` - trocar por truthiness (`if final_result.permission_denials:`
  / `not ...`), pelo achado estático. E o `async for` do Reporter também precisa
  do try/except (a iteração pode levantar antes da discriminação pós-loop).
- Não dar `break` no `ResultMessage`: eventos trailing (ex.: `prompt_suggestion`)
  podem chegar depois (doc oficial do agent-loop).

## Conexão com N1/L3

`refusal`, `error_max_turns`, `error_during_execution`,
`error_max_structured_output_retries` e `DetectorScanFailed` são todos caminhos
de **halt que não emitem Report**. O envelope externo coordinator->caller carrega
a família tipada de causas; `ReportPayload.run_outcome` permanece nos 4 tokens
de sucesso. Os achados reforçam a reconciliação (i) - erro fora do `ReportPayload`.

## Quirk a registrar (versão-específica 0.2.87)

`subtype == "success"` coexistindo com `is_error == True` e
`stop_reason == "refusal"` é inconsistência interna do CLI nesta versão.
Qualquer discriminação baseada em `subtype` no L2 seria bug latente.

> 💡 **Conceito Claude relevante (Domínio 5 - Context Management & Reliability;
> toca Domínio 1 - Agentic Architecture):** error propagation determinística >
> heurística de exceção. O sinal reliability-critical (refusal / erro de loop) é
> lido do estado estruturado já capturado (`last_result`), não da string crua do
> transporte (montada por fallback). O ordering result-antes-do-raise é a
> garantia que torna isso possível, e está provado por leitura de fonte, não só
> por observação de caixa-preta.
