# ADR-0011 — Caracterização Windows-stdio handle inheritance + design da separação de classes de erro nos wrappers git

**Status:** Aceita — emendada em 2026-07-02: D1 (hardening `stdin=subprocess.DEVNULL`) implementado no PR #59 e validado no portão da Milestone B; D2 (separação de classes de erro) ratificado como design, com implementação diferida (ver §Emenda — 2026-07-02).
**Data:** 2026-05-24.
**Sessão de origem:** Chat #35 (pos-hoc, após merge PR #59 + PR #60).
**Refs:** PR #59 (squash `25d8c52`); PR #60 (squash `b4ec3fe`); learning-log §"Session #34" e §"Session #35".

## Contexto

A sessão #34 descobriu empiricamente, via gate Milestone B, que `subprocess.run` invocando `git` e `semgrep` em `tools.py` sem `stdin=` explícito travava sob stdio transport real no Windows. A PR #59 corrigiu a manifestação adicionando `stdin=subprocess.DEVNULL` em 3 sites. Dois eixos ficaram pendentes para esta ADR:

1. **Caracterização da mecânica fina** que produz o hang (necessária para defesa do TCC e para informar decisões futuras de portabilidade).
2. **Decisão de design** sobre como separar `TimeoutExpired` (transient) de `OSError` (environment) de erro de business (ref ausente) nos wrappers git `_resolve_ref` e `_is_shallow_repository`. A PR #59 deixou explícito em §2.4 do prompt T-fix v3 que a misclassificação `TimeoutExpired → GIT_REF_NOT_FOUND` permanece como débito conhecido até esta ADR ratificar a abordagem.

## D1 — Caracterização Windows-stdio handle inheritance

**Hipótese principal (não totalmente caracterizada empiricamente):** quando o servidor MCP é spawnado por um cliente externo via stdio transport, o handle do anonymous pipe Windows usado para `stdin` do servidor é herdável por padrão. `subprocess.run` no servidor, sem `stdin=` explícito, invoca `subprocess.Popen` que via `CreateProcess` com `bInheritHandles=TRUE` duplica handles herdáveis para o filho. O filho `git` (ou `semgrep`) recebe um duplicado do handle do pipe stdin do parent.

`git rev-parse --verify <sha>^{commit}` não lê stdin (operação instantânea), então o filho não trava aguardando input. **O hang ocorre na fase de terminação:** alguma interação entre o handle duplicado mantido aberto pelo filho, o cleanup do pipe pelo Win32, e o `WaitForSingleObject` que `Popen.wait()` usa internamente — produz timeout de 10s sem que `subprocess.run` detecte o exit do filho. Causa fina (qual API exata, qual flag, qual ordem de cleanup) não foi caracterizada empiricamente; a evidência só vai até "variante sem `stdin=` trava; variante com `stdin=DEVNULL` retorna em <100ms". Caracterização Win32 completa requer probe instrumentado com Process Monitor ou similar — fora do escopo deste TCC.

**Insight adicional registrado (R-3 da Code session #35):** o subprocess `semgrep`, mesmo com `stdin=DEVNULL` aplicado (Fix-3 da PR #59), spawna sub-processes internamente (`semgrep-core`, file scanners). Em teoria, esses sub-sub-processes herdariam handles do `semgrep` parent. Empíricamente não vimos hang com fix aplicado, então a propagação cascading não se manifestou — provavelmente porque `semgrep` consome stdin do seu parent de forma diferente (CLI tool, não MCP server). Mas a hipótese mecânica fina precisa considerar essa dimensão se a caracterização for retomada em trabalho futuro.

**Implicações práticas:**
- `stdin=subprocess.DEVNULL` em **todos** os `subprocess.run` invocados sob qualquer servidor MCP rodando em stdio transport é boa prática defensiva geral, não apenas correção de bug específico.
- Pattern aplica a qualquer projeto Python que (a) implementa MCP server em stdio + (b) spawna subprocess. Defense candidate para o Capítulo de Método como pattern transferível.
- Linux/macOS não experiencia o defeito (handle inheritance via fork não tem o mesmo problema de cleanup); cobertura cross-platform da AS-14 é honesta sobre isso via AS-14b Windows-only.

## D2 — Design da separação de classes de erro nos wrappers git

### Opções consideradas

**(a) Signature change.** `_resolve_ref` muda de `str | None` para `str | ErrorEnvelope | None`; `_is_shallow_repository` muda de `bool` para `bool | ErrorEnvelope`. Callers em `scan_diff` discriminam via `isinstance`.

- Pros: tipos explícitos no signature; sem exception flow.
- Cons: cascade de complexity para callers (3 sites: `base_ref` resolve, `head_ref` resolve, shallow check); narrowing via `isinstance` em cada uso; LOC adicional ~15-25.

**(b) Custom exception types.** Helpers raise exceções próprias (`GitOperationTimeout`, `GitBinaryUnavailable`); `scan_diff` captura no nível superior e emite errorCodes próprios.

- Pros: helpers preservam shapes simples (`str | None`, `bool`); error path estrutural concentrado em um locus (`scan_diff`); idiomática para Python; precedente já estabelecido no subprocess `semgrep` que usa `except subprocess.TimeoutExpired:` específico para emitir `SCAN_TIMEOUT`.
- Cons: exception flow para signaling de error structural (não business normal); 2 classes novas a manter.

**(c) Result type pattern (Rust-style).** Helpers retornam `Result[str, ErrorKind]`. Rejeitado: não é idiomático em Python sem libraries dedicadas; cascade equivalente à opção (a) sem ganho.

### Decisão — Opção (b)

Razão: alinha com pattern já estabelecido no projeto (subprocess semgrep usa `except TimeoutExpired:` específico para emitir errorCode próprio); preserva semântica simples dos helpers (`_resolve_ref` continua significando "retorna SHA resolvido ou None se ref não existe", semântica business limpa); error path estrutural fica concentrado em um único locus (`scan_diff`), o que reduz cascade e facilita amendments futuros.

### Implementação proposta (referência — PR posterior detalha)

**Novas exception classes** em `src/mcp_servers/semgrep_runner/errors.py` (ou módulo análogo per convenção; PR pre-flight ratifica):
- `GitOperationTimeout(Exception)` — raised por `_resolve_ref` e `_is_shallow_repository` quando `subprocess.TimeoutExpired` for capturada.
- `GitBinaryUnavailable(Exception)` — raised quando `OSError` (e.g., `FileNotFoundError` para git binário ausente).
- Exception subclass naming definitivo: alinhar com `RulesLoadError` existente em `errors.py` se for o pattern do projeto (provavelmente `GitOperationTimeoutError` / `GitBinaryUnavailableError` com sufixo `Error`); PR pre-flight verifica.

**Novos errorCodes** em `_envelope.py` (builders) + `models.py` (string Field — não Literal) + canonical §5.4 (tabela) + `_RETRYABILITY_TABLE` em `test_scan_diff.py` (anchor):
- `GIT_OPERATION_TIMEOUT` — `isRetryable=true` (transient).
- `GIT_BINARY_UNAVAILABLE` — `isRetryable=false` (environment; simétrico ao `SEMGREP_BINARY_UNAVAILABLE` existente).

**Wrapper helpers** em `tools.py`:
```python
def _resolve_ref(ref: str, cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
            cwd=cwd, capture_output=True, text=True,
            timeout=10, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        raise GitOperationTimeout(...)
    except OSError:
        raise GitBinaryUnavailable(...)
    if result.returncode != 0:
        return None  # business: ref ausente — upstream emite GIT_REF_NOT_FOUND
    return result.stdout.strip()
```

**`scan_diff`** captura no nível superior:
```python
try:
    base_sha = _resolve_ref(base_ref, repo_root)
    ...
except GitOperationTimeout as exc:
    return _envelope_tool_result(_git_operation_timeout(detail=...))
except GitBinaryUnavailable as exc:
    return _envelope_tool_result(_git_binary_unavailable(detail=...))
```

**Tests** (PR posterior):
- AS-15 — mock filtrado por comando (`cmd[:3] == ["git", "rev-parse", "--verify"]`) para forçar `TimeoutExpired` no helper específico, não em ambos. Sem filtro, mock dispara em primeira chamada (`_is_shallow_repository`) e cobre helper errado.
- Split AS-15 em 2 tests: um por helper. `.claude/rules/test-strategy.md` "granularity calibrada por failure dimension expected".
- Análogo para `OSError` (mockar via raise `FileNotFoundError`).

### Out-of-scope desta ADR

- Introduzir `check=True` em `subprocess.run` (ativaria `CalledProcessError` como classe adicional). Mudança de semântica não-trivial sem benefício imediato; deixar para ADR futura se houver caso de uso.
- Caracterização Win32 fina (probe instrumentado com Process Monitor). Excedente ao escopo do TCC.
- Refactor mais amplo de error handling em outros loci de `tools.py`.

## Consequências

**Positivas:**
- Misclassificação `TimeoutExpired → GIT_REF_NOT_FOUND` resolvida estruturalmente.
- Cliente externo recebe `isRetryable=true` em transient errors → pode aplicar retry com backoff.
- Pattern de error handling consistente entre wrappers git e subprocess semgrep.

**Negativas:**
- 2 exception classes + 2 errorCodes + amendment canonical + 2 entries na retryability table + try/except no `scan_diff`. LOC estimado ~35-50.
- Misclassificação histórica em deployments existentes (não-relevante; produto não está em produção).

**Provenance/audit:**
- ADR ratificada antes da implementação (pattern do projeto: ADR-0001 D2 amendment retroativo Presidio→Semgrep; ADR-0004 retroativo uv migration — mas esses dois eram caracterização de mudanças já consumadas; este ADR é ratificação prévia para guiar PR posterior).
- Implementação em PR dedicada (sem bundle com outros fixes).

## Aprovação

Aceita ao registrar em `docs/adr/ADR-0011.md` via PR `docs/adr-0011`. Implementação em PR técnica subsequente referenciando este ADR como justificativa.

## Emenda — 2026-07-02 (ratificação e atualização de status)

Ratificada pelo autor em 2026-07-02, com status atualizado por eixo (fecha o achado XDOC-15 do relatório de QA, `docs/process/relatorio-qa.md` Quadro 14):

- **D1 — implementado e validado.** O hardening `stdin=subprocess.DEVNULL` está aplicado nos 3 sites de `subprocess.run` em `src/mcp_servers/semgrep_runner/tools.py` (PR #59, squash `25d8c52`) e foi exercitado pelo portão da Milestone B sobre transporte stdio real (`docs/process/milestoneB.md`), com regressão coberta por AS-14/AS-14b.
- **D2 — decisão ratificada; implementação diferida.** A Opção (b) permanece a abordagem decidida. Verificado em 2026-07-02: as exception classes (`GitOperationTimeout`, `GitBinaryUnavailable`) e os errorCodes (`GIT_OPERATION_TIMEOUT`, `GIT_BINARY_UNAVAILABLE`) ainda não existem em `src/`; a misclassificação `TimeoutExpired → GIT_REF_NOT_FOUND` segue como débito conhecido (relatório de QA §6.2) até a PR técnica dedicada prevista em §Provenance/audit.