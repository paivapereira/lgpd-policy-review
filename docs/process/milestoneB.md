# Milestone B — Gate empírico do `semgrep-runner` MCP server

**Sessão de execução:** #34 (descoberta de defeito) + #35 (fix + re-execução PASS).
**Branch de exercise:** `chore/gate-milestone-b-rule-set-fixture` (PR `<TBD — preencher pós-merge>`).
**Branch de fix dependente:** `fix/scan-diff-stdin-isolation-windows-stdio` (PR #59, merged via squash `<TBD>`).
**Mecanismo:** FastMCP `Client` + `StdioTransport` exercitando o servidor MCP `mcp_servers.semgrep_runner.server` spawnado como subprocess Python real.
**Pré-requisito procedural:**
- Semgrep 1.163.0 instalado e resolvível via PATH.
- Binário em path ASCII-only (Windows: evitar paths com acentos via `joaoguilherm.pereira` resolvido como `JOAOGU~1.PER` no Windows short name).
- Branch `chore/gate-milestone-b-rule-set-fixture` checkout (contém pack alternativo `synthetic_iban` em `tests/.../fixtures/alternative_rule_set_synthetic/` + script `scripts/gate_milestone_b_exercise.py`).
- Para versão pós-fix do produto: branch `chore/*` rebasada sobre `main` que já contém merge da PR #59 (fix do `subprocess.run` handle inheritance).

**Não usado:** MCP Inspector CLI (descartado pré-#34; client-side request timeout default insuficiente para cold start do `scan_diff` em Windows; `MCP_SERVER_REQUEST_TIMEOUT` override sem efeito documentado). FastMCP `Client(timeout=...)` expõe o parâmetro explicitamente, viabilizando exercise fiel. Equivalência cliente↔cliente sob mesma surface protocolar (MCP via stdio) preserva fidelidade — trocar Node Inspector por Python FastMCP Client não muda wire format.

## Decisão de escopo do gate — RF-008 rule-set-axis only

O gate exercita exclusivamente RF-008 (substituibilidade do rule set via `SEMGREP_RUNNER_ROOT` env injection). Demais RFs do Milestone B (RF-001 contract `scan_diff`; RF-002 wire format Option B; RF-003 errorCode discrimination; etc.) são cobertos por pytest unit (134 tests passing pós-merge PR #59; ver `tests/mcp_servers/semgrep_runner/test_scan_diff.py` AS-1..AS-14).

Razão: gate empírico com wire protocolar real tem custo desproporcional para invariantes que pytest com `Client(server.mcp)` in-memory já cobre adequadamente. Gate é reservado para propriedades que **só** o transport real expõe — RF-008 substitui rule set via env var lido por subprocess spawned, exatamente o caminho que requer wire-real.

## Narrativa metodológica em 2 atos

### Ato 1 — Sessão #34: descoberta de defeito empírico em `scan_diff`

**Premissa de entrada da #34.** Milestone B implementacionalmente completo após PR #58 (T07 — rule pack BR). 132 tests passing. Plano: redigir gate script (`scripts/gate_milestone_b_exercise.py`), exercer RF-008 contra dois rule sets distintos (default BR vs synthetic_iban alternativo), declarar PASS, redigir este documento.

**O que aconteceu.** Script rodou e o gate retornou FAIL. Phase 1 (baseline BR rule set) e Phase 2 (alternative synthetic_iban via `SEMGREP_RUNNER_ROOT` override) ambas falharam ao resolver `base_ref` via `git rev-parse`. Output do servidor: `errorCode: GIT_REF_NOT_FOUND` para refs que existiam empíricamente no repo de fixture (commits criados via `git commit` pelo próprio script).

**Diagnóstico empírico via progressive narrowing.** Sequência metodológica documentada em learning-log #34:
1. Suspeita ampla ("MCP timeout").
2. Isolamento de transport (Inspector vs FastMCP Client).
3. Isolamento cliente vs servidor (script vs Inspector).
4. Isolamento cliente MCP vs invocação direta (`scan_diff` standalone com `state` injetado manualmente).
5. Revelação do defeito empírico no transport via comparação `subprocess.run` com vs sem `stdin=subprocess.DEVNULL`.

**Causa raiz proximal identificada.** `src/mcp_servers/semgrep_runner/tools.py` invoca `subprocess.run` em 3 sites sem `stdin=` explícito (`_resolve_ref:164`, `_is_shallow_repository:144`, `scan_diff` body:306). Em Windows sob stdio transport real, o processo filho (git ou semgrep) herda o pipe stdin do servidor MCP (parent). Mecânica fina não totalmente caracterizada — hipótese principal: handle inheritance do anonymous pipe Windows usado para stdio MCP + `subprocess.Popen.wait()` no parent + Win32 pipe internals. `git rev-parse --verify <sha>^{commit}` não lê stdin (operação instantânea, não interativa), então o hang não é "git esperando input" — é interação entre handle inheritance e terminação do filho que `subprocess.run` não detecta corretamente.

**Captura defeituosa upstream.** `TimeoutExpired` é subclass de `subprocess.SubprocessError`. O `except (subprocess.SubprocessError, OSError)` em `tools.py:173` captura genericamente e retorna `None`, fazendo o fluxo emitir `GIT_REF_NOT_FOUND` (errorCode business, `isRetryable=false`). Anti-pattern D5 canônico: bug transient (deadlock por handle inheritance) misclassificado como erro semântico de business (ref inexistente).

**Por que pytest com 132 tests verdes não pegou.** AS-11 e todos os tests de `scan_diff` pré-#34 usam `Client(server.mcp)` — transport in-memory dentro do mesmo processo Python. Não há pipe stdio real entre cliente e servidor; não há handle a herdar; defeito não se manifesta. Categoria de bug que **apenas** gate manual com transport real pode capturar. Pattern `.claude/rules/review-patterns.md` Justificativa #2 materializada empíricamente: "exercise contra wire real expõe debt que pytest cobre por coincidência".

**Decisão de fluxo.** Sessão #34 fechou com defeito empírico documentado em halt report do Code, branch `chore/gate-milestone-b-rule-set-fixture` aberta mas não-mergeada (evidência da descoberta, não deliverable), e prescrição: fix em PR separada (sessão #35), ADR pos-hoc após escopo de fix consolidado, re-rodar gate após merge do fix.

### Ato 2 — Sessão #35: fix + re-execução PASS

**Fix do produto via PR #59.** Sessão Chat #35 redigiu prompt T-fix v1→v3 com multi-instance review canônico (3 rounds, ~30+ catches absorvidos). Decisão load-bearing emergente dos reviews: **deferir Fix-4 inteiro** (separação `TimeoutExpired` vs `OSError` vs business nos wrappers git) para ADR-0012 + PR posterior — convergência R1 C5 + R2 N-C1 demonstrou type breakage arquitetural (helpers retornam `str | None` e `bool`; retornar `ErrorEnvelope` Pydantic do `except` quebraria type contract e callers em `scan_diff`).

PR #59 manteve escopo cirúrgico: 3 sites de `stdin=subprocess.DEVNULL` em `tools.py` (+3 / -0) + AS-14 cross-platform happy path sob `StdioTransport` real + AS-14b Windows-only com `@pytest.mark.skipif(sys.platform != "win32", ...)` assertando `elapsed < 10.0s` para regressão por timing (+134 / -0 em `test_scan_diff.py`).

Misclassificação `TimeoutExpired → GIT_REF_NOT_FOUND` permanece como débito conhecido — documentada em §2.4 do prompt T-fix v3, no commit message da PR #59, e na PR description. ADR-0012 pos-hoc cobrirá caracterização Win32 fina (E-1) + design da separação de classes de erro (E-2); PR posterior implementará.

**Validação antecipada via branch combinada local.** Após Code aplicar PR #59 e antes de merge em main, sessão #35 validou empíricamente o gate Milestone B contra branch `test/gate-on-fix-v2` (combinação local: `fix/scan-diff-stdin-isolation-windows-stdio` + merge `chore/gate-milestone-b-rule-set-fixture`). Pattern análogo conceitual a `fork_session` aplicado ao Git workflow: branch temporária local, descartada após validação.

**Re-execução do gate — segundo defeito emerge.** Gate rodou ambas as phases sem hang (`elapsed: 7.7s` Phase 1; `6.9s` Phase 2 — fix funcionou empíricamente). Mas verdict ainda foi FAIL: 3 dos 5 invariantes falharam (INV-1, INV-2, INV-3). Output do JSON consolidado revelou que os 5 invariantes **substantivos** estão verdes; os 3 que falham são defeitos do script de aferição, não do produto:

- **Defeito 1 — `summarize_phase` lê `rules_version`/`semgrep_version` do lugar errado.** Linhas 223-224 do script lia esses campos de `scan_metadata.get(...)`, mas a canonical §5.1 do `semgrep-runner` declara que são top-level em `structuredContent`, irmãos de `scan_metadata`. Resultado: ambos os campos vinham `None` → propagava em INV-2 (rules_version distinct: `None != None` é False) e INV-3 (semgrep_version identical: `None == None` mas guard `is not None` falha).

- **Defeito 2 — `check_invariants` INV-1 string equality literal.** Linha 246 fazia `p1["rule_id"] == "br-cpf"`, mas Semgrep com `--config <local-dir>` empacota `rule_id` como `<dot-encoded-path>.<bare-name>` — valor real é `C.Users.joaoguilherm.pereira.dev.lgpd-policy-review.mcp_servers.semgrep_runner.rules.br-cpf`. Equality literal contra bare name falha.

**Patch ao script via commit `34b6c05` em `chore/gate-milestone-b-rule-set-fixture`.** 1 file modificado, +11/-4 linhas:
- Patch 1: ler `rules_version` e `semgrep_version` de `sc` (top-level structured_content) em vez de `scan_metadata`.
- Patch 2: usar `rsplit(".", 1)[-1] == "<bare-name>"` em vez de equality literal. Idioma do projeto (vide `_short_rule_id` em `tests/.../test_recognizers_br.py:36-39`) ratificado em Pin 2 do GATE 1 do Code; aplicado conforme convergência cross-código.

**Gate Milestone B PASS — 5/5 invariantes verdes.** Re-execução do script pós-patch contra `test/gate-on-fix-v2` retornou `gate_verdict: PASS`. Evidência consolidada em `gate_b_output.json` + `gate_b_stderr.log` (working dir untracked).

## Sumário 1-linha do gate

> RF-008 (substituibilidade de rule set via `SEMGREP_RUNNER_ROOT`) validada empíricamente: spawn de subprocess servidor MCP via `StdioTransport` carrega rule pack indicado pela env var; finding emerge contra a regra do pack ativo; pack BR default e pack alternativo synthetic_iban produzem `rule_id` distintos, `rules_version` distintos, `semgrep_version` idêntico, `isError=false` uniforme, refs resolvidas para 40-hex SHA — 5/5 invariantes verdes.

## Fases B.1..B.4 executadas

| Fase | Descrição | Output |
|---|---|---|
| **B.1 — Setup** | Build de dois tmp repos via `tempfile.mkdtemp` + `git init` + commit baseline (README) + commit head (fixture file). Phase 1 fixture: `br_cpf_function_param.py` (do pack BR). Phase 2 fixture: `synthetic_iban_function_param.py` (do pack alternative). | 2 repos tmp prontos com refs resolvíveis (base SHA + head SHA, ambos 40-hex). |
| **B.2 — Phase 1 (baseline BR)** | Spawn `mcp_servers.semgrep_runner.server` via `StdioTransport(command=sys.executable, args=["-m", ...], cwd=phase_1_repo, env={…, sem SEMGREP_RUNNER_ROOT override})`. Invocação `client.call_tool("scan_diff", {"base_ref": phase_1_base, "head_ref": phase_1_head})`. Loader resolve default rule set `mcp_servers/semgrep_runner/rules/` (6 regras BR). | Phase 1 result: `rules_version=sha256:0be103f1...`, `semgrep_version=1.163.0`, `is_error=false`, `findings=[{rule_id: "...rules.br-cpf", location: "br_cpf_function_param.py:10-12"}]`, `elapsed_seconds=7.7`. |
| **B.3 — Phase 2 (alternative synthetic_iban)** | Spawn idêntico ao Phase 1 mas com `extra_env={"SEMGREP_RUNNER_ROOT": str(ALT_RULES_DIR)}` (pack alternativo em `tests/.../alternative_rule_set_synthetic/rules/`, 1 regra `synthetic-iban`). Loader resolve pack alternativo. | Phase 2 result: `rules_version=sha256:ffb1ac00...`, `semgrep_version=1.163.0`, `is_error=false`, `findings=[{rule_id: "...rules.synthetic-iban", location: "synthetic_iban_function_param.py:11-14"}]`, `elapsed_seconds=6.9`. |
| **B.4 — Invariantes + JSON consolidado** | Função `check_invariants(p1_summary, p2_summary)` avalia INV-1..INV-5 unconditionally. JSON consolidado a stdout. Verbose per-phase a stderr. Exit code 0 se PASS; 1 se FAIL. | `gate_verdict: PASS`. JSON consolidado em `gate_b_output.json`. |

### Verdict por invariante

| Invariante | Verdict | Detalhe |
|---|---|---|
| **INV-1 rule_set_axis** | ✅ PASS | `rsplit(".", 1)[-1]` extrai bare name `br-cpf` da Phase 1 e `synthetic-iban` da Phase 2 — assertion idiomática alinhada com `_short_rule_id` em `test_recognizers_br.py`. |
| **INV-2 rules_version_distinct** | ✅ PASS | `sha256:0be103f1...` (Phase 1) ≠ `sha256:ffb1ac00...` (Phase 2). Hashes distintos comprovam que `SEMGREP_RUNNER_ROOT` injection carregou pack diferente em cada phase. |
| **INV-3 semgrep_version_identical** | ✅ PASS | `1.163.0` em ambas as phases. Mesmo engine; apenas o input rule set variou. |
| **INV-4 wire_is_error_false** | ✅ PASS | `false` em ambas as phases. Option B (per ADR-0002 §3 amendment) materializada em wire stdio real — discriminação semântica sucesso-vs-erro opera por presença de `errorCode` em `structuredContent`, nunca pelo `isError` flag. |
| **INV-5 refs_resolved_to_40_hex** | ✅ PASS | 4 SHAs validados contra `^[0-9a-f]{40}$`. `scan_diff` ecoa os SHAs resolvidos no `scan_metadata`, não o input do caller — confirma resolução via `git rev-parse --verify <ref>^{commit}` per canonical §4.2. |

## Cleanup pós-gate

- Branches descartáveis locais (`test/gate-on-fix`, `test/gate-on-fix-v2`): deletar via `git branch -D <name>` após confirmação de merge da PR `chore/*`.
- `gate_b_output.json` + `gate_b_stderr.log` em working dir: untracked. Evidência operacional do gate. Cleanup em housekeeping própria (G) do handoff #35→#36; recomendação: adicionar pattern `gate_b_*.json` + `gate_b_*.log` ao `.gitignore`.
- Branch `chore/gate-milestone-b-rule-set-fixture` após PR mergeada: deletar local + remote conforme git workflow ADR-0001 Decision 5.

## Catches detectados e endereçamento

| # | Catch | Origem | Endereçamento |
|---|---|---|---|
| 1 | `subprocess.run` em 3 sites de `tools.py` sem `stdin=` → handle inheritance Windows-stdio → `TimeoutExpired` → misclassificado como `GIT_REF_NOT_FOUND`. | Sessão #34 (gate empírico contra wire real). | PR #59 (sessão #35) — `stdin=subprocess.DEVNULL` adicionado em 3 sites + AS-14/AS-14b cobertura. |
| 2 | `summarize_phase` lê `rules_version`/`semgrep_version` de `scan_metadata` aninhado em vez de `structured_content` top-level (canonical §5.1). | Sessão #35 (gate re-rodado pós-fix). | Commit `34b6c05` (sessão #35) — leitura de `sc.get(...)`. |
| 3 | `check_invariants` INV-1 string equality literal contra bare rule name vs Semgrep encoding `<dot-path>.<bare-name>`. | Sessão #35 (gate re-rodado pós-fix). | Commit `34b6c05` (sessão #35) — `rsplit(".", 1)[-1] == "<bare-name>"` per idioma do projeto. |
| 4 | Misclassificação semântica `TimeoutExpired → GIT_REF_NOT_FOUND` (anti-pattern D5: transient tratado como business). | Sessão #34 (análise causal pós-descoberta). | **Diferido** para ADR-0012 + PR posterior. PR #59 elimina manifestação atual (handle inheritance) mas não resolve estrutura. Decisão registrada em §2.4 do prompt T-fix v3 + commit message PR #59. |

## Próximas tasks dependentes (handoff #35→#36)

- **(E) ADR-0012 pos-hoc** cobrindo: (E-1) caracterização Win32 fina do handle inheritance + cascading inheritance em sub-processes do semgrep-core; (E-2) design da separação de classes de erro nos wrappers git (três opções identificadas em review v2 do prompt T-fix).
- **(F) PR posterior** implementando ADR-0012 (E-2). Inclui AS-15 com mock filtrado por comando (split em 2 tests, um por helper).
- **(G) Housekeeping CLAUDE.md `§Status flags`** — drift ≥6 linhas em 3 bullets distintos (catalogado em DD-Tfix-1 da #35).

## Limitações conhecidas

- **Mecânica fina Windows-stdio não totalmente caracterizada.** Evidência empírica é sólida: variante de `subprocess.run` sem `stdin=` trava em ~10s + variante com `stdin=DEVNULL` retorna em <100ms. Causa proximal confirmada como handle inheritance do anonymous pipe stdin. Causa raiz fina (interação Win32 internals + `Popen.wait()`) merece caracterização em ADR-0012 (E-1). O fix funciona independentemente da explicação fina.

- **Misclassificação `TimeoutExpired → GIT_REF_NOT_FOUND` persiste como débito conhecido.** PR #59 elimina a manifestação atual (handle inheritance Windows) mas não corrige a estrutura — outras causas futuras de `TimeoutExpired` (system pressure, network latency em hipotéticas refs remotas) continuariam sendo colapsadas no errorCode business. Endereçamento estrutural em ADR-0012 (E-2) + PR posterior.

- **Defeito de aferição mascarado por defeito upstream.** Os defeitos de leitura de campo no `summarize_phase` (`rules_version`/`semgrep_version` lidos do lugar errado) e o assertion literal de INV-1 existiam no script `gate_milestone_b_exercise.py` desde a sessão #34. Não foram detectados naquela sessão porque o defeito do `subprocess.run` (layer-1) mascarava o caminho de execução — gate falhava antes de chegar à fase de aferição. Apenas pós-fix do layer-1 na #35 os defeitos de layer-2 emergiram. Pattern empírico canônico para Capítulo de Método: validação de cobertura tem que assumir que defeitos podem estar empilhados em layers; PASS em um nível não atesta correção em outros níveis.

- **Threshold AS-14b = 10.0s não medido contra cold-start empírico.** Análise factual no prompt T-fix v3 §8.1 cobre o espaço (defeito ~22-23s vs success ~5-8s); margem 10s separa claramente. Mas cold-start `StdioTransport` em CI extremamente fria (antivírus inspecionando `python.exe`, SSD lento) poderia encostar no threshold. Se flake materializar pós-merge, ajustar em PR follow-up — não-bloqueante para esta validação.

- **`summarize_phase` fallback `scan_metadata.base_ref or base_ref` (linhas 225-226).** Mede "input refs bem formados" se scan retornar erro, não strictamente "servidor ecoou refs resolvidos". Nuance metodológica original do gate; aceitável dado que INV-5 valida adicionalmente o formato 40-hex contra `^[0-9a-f]{40}$`.

- **Cobertura E2E restrita a RF-008.** Demais RFs do Milestone B (RF-001 contract `scan_diff`, RF-002 wire format Option B, RF-003 errorCode discrimination) cobertos por pytest unit com `Client(server.mcp)` in-memory (134 tests passing). Pattern empírico ratificado pelo gate Milestone B: cobertura unit complete não substitui cobertura E2E com wire real — são camadas ortogonais. Próximas validações empíricas a considerar em milestones futuros: scan_diff sob carga (timeout legítimo), errorCode mapping per-class, error envelope shape sob diversos exit codes Semgrep.

---

**Insumo metodológico para Capítulo de Método do TCC**

A trajetória completa #34 → #35 materializou empíricamente em 6 fases sequenciais o pattern de cobertura multi-layer que `.claude/rules/review-patterns.md` Justificativa #2 prescreve:

1. **132 tests passing** pré-#34 → defeito invisível.
2. **Gate Milestone B sessão #34** → defeito do `subprocess.run` (layer-1, transport) emerge.
3. **PR #59** → fix layer-1 + cobertura regression unit (AS-14b).
4. **Gate Milestone B re-rodado sessão #35** → defeito do `summarize_phase` (layer-2, aferição) emerge — estava mascarado.
5. **Patch ao script** → fix layer-2.
6. **Gate Milestone B pós-patch** → 5/5 invariantes verdes simultaneamente; cobertura unit + cobertura E2E ambas verdes.

Defense candidate forte: cobertura unit verde **nunca** é evidência suficiente; cobertura empírica E2E com wire protocolar real é cobertura independente, complementar, não substituível. Pattern aplica recursivamente — fix de defeito em layer-N pode revelar defeito previamente mascarado em layer-(N+1). Validação de cobertura requer assumir que defeitos podem estar empilhados.

**Defeitos empilhados ≠ defeitos múltiplos independentes.** O defeito de aferição no `summarize_phase` (defeito #2 e #3 da tabela acima) já existia no script desde a sessão #34 — não foi introduzido pela #35. O `subprocess.run` defeito (defeito #1) mascarava o caminho de execução, fazendo o script falhar antes de chegar à fase de aferição. Isto é "empilhamento" no sentido literal: layer-N abaixo de layer-(N+1) no fluxo de execução. Resolver layer-N necessariamente expõe layer-(N+1) ao escrutínio empírico pela primeira vez.

A consequência metodológica: re-execução de gates após qualquer fix em layer downstream é não-opcional — não é cerimônia, é cobertura necessária. Pattern empírico das sessões #21-#35 ratifica.

---

obs milestoneB-draft.md:

Header "PR <TBD>": para PR chore preencher PR #60 + b4ec3fe; para PR #59 preencher hash real.
§Ato 2 "Patch ao script via commit 34b6c05 em chore/..." → "Patch ao script via PR #60 (sessão #35 aplicado local; pós-rebase sobre main pós-PR #59, SHA regenerado; absorvido em main via squash como b4ec3fe). 1 file modificado, +11/-4 linhas."
Tabela §Catches detectados, linhas com "Commit 34b6c05" → "PR #60 / squash b4ec3fe".