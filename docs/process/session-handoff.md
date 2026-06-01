# Session handoff — implementação MC-C (entrada da Fase 3, lado Code)

> **Durante o ciclo MC-C este handoff é território do Code** (o Chat corrige a
> implementação, não o handoff). Cada fase roda em **sessão Code fresca**
> (`.claude/rules/session-management.md`). **A Fase 3 NÃO é o que o plano original
> (l.117-124) descreve** — o gate G2b descobriu que `query()` one-shot **não**
> entrega os MCP servers prontos (cold-start race). O escopo da Fase 3 é o do plano
> **expandido por essa descoberta**, e o desenho vive em **`docs/adr/0014-mcp-connection-lifecycle-and-resilience.md`** (DRAFT). Leia o ADR-0014 + a seção
> "GATE G2b" de `scripts/smoke_tests/coordinator_live/RESULTS.md` + o plano antes de codar.

## 0. Primeira ação ao abrir a sessão
`git log main --oneline -6` + `git status` — verifique o estado real; não confie em
SHAs deste doc se algo mergeou. Plano completo (5 fases):
`C:\Users\paiva\.claude\plans\quero-que-analise-as-graceful-steele.md` (mas a Fase 3
está **reconciliada aqui** — não transcreva o plano).
>
> **STATUS pós-gate (sessão D1, 2026-06-01) — registro de fechamento.** O **D1
> verification gate PASSOU** (RESULTS.md "GATE D1"): o modelo recebe `scan_diff` no
> snapshot de init E o **chama** (semgrep roda) — readiness-wait re-apresenta o tool;
> **ADR D1 confirmado COMO ESCRITO**, **DD-3.2 = PASS, sem redirect**. **DD-3.1
> RATIFICADO = DUAS PRs** (PR-A reliability → PR-B hardening+capstone). Um `findings=[]`
> observado foi isolado como **fixture-mismatch do probe** (não recognizer, não diff-mode,
> não readiness — **o BR-CPF recognizer FUNCIONA; a claim central do TCC está intacta**);
> recipe de fix na §2 passo 5. **A próxima ação TÉCNICA NÃO é mais o gate — é a impl da
> PR-A.** PORÉM: **NÃO abrir sessão fresca de migração até `prompt-phase3-reliability-v1.md`
> passar pelo review do Chat** (padrão 2a/2b: Code rascunha → Chat revisa → sessão fresca
> executa o revisado).
>
> **STATUS pós-PR-A (2026-06-01) — Fase 3 RELIABILITY FECHADA.** Mergeadas em `main`: **#95**
> (`df78441`, PR-A reliability: readiness via `_run_mcp_stage` + retry in-session); **#96**
> (`2cb0ab9`, ADR-0014 **Accepted**, Appendix sincronizado ao código mergeado); **#97**
> (`4c4c953`, cleanup: os 4 arms do g2b re-apontados pro `_run_mcp_stage` + fixture
> `def collect(cpf)` param). **140 testes verdes** (`tests/coordinator` + `tests/subagents`),
> ruff + mypy-strict limpos, `test_driver.py` byte-untouched (preserved-spine). Os dois débitos
> **G3-blocking** (g2b transporte + fixture) estão **RESOLVIDOS por #97**. **A próxima ação é o
> capstone G3** — milestone-level, live, opt-in: entry brief completo na **§10**. (§1-§9 abaixo
> = registro do ciclo PR-A, fechado; não re-litigar.)

## 1. Onde estamos
- **Fases 0/1/2a/2b mergeadas** em `main`: #88 / #89 / #90 / **#92** (Phase 2b). `main` @ `75c7aac`+.
- **127 testes verdes** (`tests/coordinator` + `tests/subagents`); `ruff check src tests` + `mypy --strict src/coordinator src/subagents` limpos.
- Gates: **G0 PASS**, **G1 PASS** (skip-path), **G2a PASS**, **G2b PARTIALLY-GATED** —
  arms determinísticos (Inspector-CLI) PASS; arm de agent-loop **bloqueado pelo cold-start
  race** (RESULTS.md "GATE G2b"). Débito unificado na memória `mc-c-phase2b-deferred-debts`.
- **Já implementado — NÃO re-implementar na Fase 3** (verificado neste handoff):
  logging stderr (`stage.start`/`stage.result{subtype,stop_reason}`/`run.start`/`run.halt`/
  `run.done`; stdout reservado) — `driver.py`/`run.py`; `_coverage_gap` + projeção
  `CoordinatorError{cause,stage,coverage_gap}` — `run.py`; `derive_run_outcome`/
  `aggregate_summary`; o hook **escalate-all** do Detector carregando `is_retryable`.
  **NÃO existe retry / reconnect / ClaudeSDKClient em lugar nenhum** — isso é a Fase 3.

## 2. Próximo: Fase 3 — reliability + hardening + capstone (RECONCILIADA)

> **Nomenclatura (evita a colisão de três "D1").** **D1 verification gate** = o PROBE
> (sempre com "gate") que valida a suposição causal. **ADR D1** = a DECISÃO do ADR-0014
> (readiness via `ClaudeSDKClient`). **DD-3.2** = a decisão de fase que o gate pode gerar
> se redirecionar. Ao dizer "D1 falhou", desambigue qual.

**A descoberta que reescreve a fase.** O plano (l.117-124) assumia que `query()` entrega
os MCP servers prontos. O G2b provou que **não**: cada stage abre um `query()` one-shot
que **re-spawna** seu server (Triager `mcp_servers={}`, logo o semgrep-runner é spawnado
fresco só pelo `query()` do Detector — sempre frio, ~3.5s de cold-start intrínseco), e
`query()` **não tem readiness-wait**; o modelo age no turn 1 antes de `scan_diff` registrar
→ `findings=[]`. O mecanismo de espera/recovery (`get_mcp_status`/`reconnect_mcp_server`)
só existe no **streaming `ClaudeSDKClient`**, não no `query()`. ADR-0014 é o escopo.

**Reconciliação plano × ADR-0014:**
- O **retry-budget** do plano (l.119) + acceptance (l.122: `test_as1_retryable_scan_timeout_retries_then_succeeds`, `test_as2_retry_exhausted_escalates`) = a metade **RECOVERY** do ADR (D2).
- O plano **NÃO previa READINESS** (D1: migração `query()`→`ClaudeSDKClient` pros 3 stages
  MCP) — assumia que `query()` bastava. Agora **readiness vem ANTES de recovery**.

**ORDEM INTERNA da fase (forçada pela descoberta):**
1. **D1 verification gate — ✓ DONE (PASS, RESULTS.md "GATE D1", 2026-06-01).** Probe que abre
   `ClaudeSDKClient`, espera `'connected'` via `get_mcp_status()`, e **confirma que
   `scan_diff` aparece nos tools DISPONÍVEIS PRO MODELO** (não só no status do server).
   Valida OU **REDIRECIONA** o ADR-0014 antes de qualquer código de migração. Pass → ADR D1
   como escrito. Fail (modelo age sobre o snapshot de init) → ADR D1 redesenha (garantir
   `connected` antes do stream inicial, ou re-prompt após connect). Recordar em RESULTS.md
   (gates.md / mcp-testing.md). É a suposição causal da qual a fase inteira depende —
   observar, não inferir (a lição transversal da saga 2b). [ADR-0014 "D1 verification gate"]
   **O que o gate DE FATO testa (não confundir): `get_mcp_status → 'connected'` prova só que
   o SERVER conectou — NÃO que o modelo VÊ o tool; é necessário, não suficiente.** O gate só
   PASSA se confirmar `scan_diff` na lista de tools que o modelo recebe **antes de agir** —
   observável fazendo o modelo de fato **chamar** `scan_diff` (ou inspecionando os tools
   pós-connect). Reportar "PASS" só com `get_mcp_status→connected` **NÃO é pass** (server-
   conectou ≠ tool-no-modelo — mesma classe servidor-emite ≠ consumidor-recebe da 2b;
   `tools.listChanged:true` no handshake é suporte de PROTOCOLO, não garantia de o relay
   re-apresentar a lista atualizada pro modelo).
2. **Readiness fix (ADR D1):** migrar Detector/Classifier/Matcher de `query()` →
   `ClaudeSDKClient` + wait-for-connected. **Triager (`mcp_servers={}`) e Reporter
   (in-process, sem race — G1 PASS) FICAM no `query()` one-shot.** O spine
   `run_branch_b_stage` preserva a discriminação verbatim (captura ResultMessage, refusal
   precede subtype, tabela de subtype, hook `on_tool_result`, `verify_passthrough`,
   validação, scratchpad, `except DetectorScanFailed: raise`); só o **prólogo de transporte**
   muda (abrir cliente → wait-for-connected → `query` → iterar `receive_response()`).
3. **Recovery/retry-loop (ADR D2 = retry-budget do plano l.119):** **sessão por-stage
   (o `async with` FORA do loop de retry)**; retry = `reconnect_mcp_server` + re-`query()`
   **IN-SESSION (NUNCA re-spawn** — re-abrir o cliente paga cold-start de novo e contradiz
   o reconnect); decisão `isRetryable`-driven, não por tipo de exceção. [ADR-0014 D2 + Appendix]
4. **Hardening tests (resto do plano original l.121-122):** os anchors da l.121 — a
   **maioria NÃO existe ainda** — testam comportamento JÁ implementado (logging,
   coverage_gap, error-envelope, trinca) → escrevê-los; + a acceptance de layer-enforcement.
5. **Capstone G3:** pipeline completo vivo — **agora roda porque o readiness foi
   consertado**; sem o fix, o G3 falha no mesmo race que travou o G2b (mesma camada).
   **PRECONDIÇÃO (descoberta na sessão D1): corrigir o fixture do probe ANTES do G3.** O
   `br-cpf` casa `def $FN(..., cpf, ...)` (PARÂMETRO); `_make_cpf_repo` escreve `cpf` como
   VARIÁVEL LOCAL → 0 findings (determinístico: param→1, local-var→0; RESULTS.md "GATE D1"
   §RESOLVED). **O recognizer FUNCIONA — sem bug de detecção; claim do TCC intacta.** Fix:
   `_make_cpf_repo` (g2b + o D1 gate herdam) adiciona uma função com PARÂMETRO `cpf` no head
   commit → finding populado → G3 + a 1ª observação do wrapper `{"output"}` em lista não-vazia
   (#502/#571). Registrar o débito em `docs/tasks.md` §Companion.

**PRONTO — herdar, NÃO reescrever:** todo o flesh de 2a/2b (prompts/hook/passthrough/
constants/wiring); logging + `_coverage_gap` + `CoordinatorError`; o hook escalate-all
(carrega `is_retryable`, ainda não age sobre ele); os 127 testes; o mock-SDK conftest.

**MATERIALIZAR:** (a) o probe do D1 gate; (b) a migração `ClaudeSDKClient` no spine
`run_branch_b_stage` (prólogo de transporte); (c) o retry-loop in-session; (d) os anchors
de hardening (l.121) + a acceptance de layer-enforcement; (e) o **mock `ClaudeSDKClient`**
no conftest; (f) o capstone G3.

## 3. DDs abertos (ratificar ANTES de implementar — a primeira ação é o gate, não isto)
- **DD-3.1 — sub-divisão de PR — RATIFICADO 2026-06-01 = DUAS PRs** (PR-A reliability
  primeiro; PR-B hardening+capstone depois). Fase 3 expandida = **UMA PR ou DUAS?** Reliability
  (readiness+recovery, ADR-0014, mudança de transporte do driver, **risco real — o D1 gate
  pode redirecionar**) vs hardening+capstone (logging tests + G3, incremental, baixo risco).
  **Inclinação: SUB-DIVIDIR** (PR reliability primeiro; PR hardening+capstone depois) pra
  não prender o hardening trivial atrás do risco da migração de transporte. Desvia de
  "one PR per phase" — **decisão consciente, registrar** (git-conventions).
- **DD-3.2 — desfecho do D1 verification gate — RESOLVIDO 2026-06-01 = PASS, SEM redirect.**
  O gate passou (RESULTS.md "GATE D1": modelo recebe `scan_diff` no init E o chama). ADR D1
  procede **como escrito** — não precisou de shape diferente (nem connected-antes-do-stream,
  nem re-prompt-após-connect). A segunda DD que um redirect geraria não materializou.
- **DD-3.3 — texto do `coverage_gap` → RATIFICADO 2026-06-01 = ACENTUADO; aplicar na PR
  HOUSEKEEPING (com §4.3 stale + doc-lags), NÃO na PR-A reliability.**
  **Onde vive (investigado):** é campo do `CoordinatorError` (dataclass `models.py:32`),
  documentado como **"human annotation of what was not analyzed"**, retornado ao **caller
  externo (GitHub Action / exercise script)** (§3.6). **NÃO** vai pro `99-report.json` (esse
  é o success path / `emit_report`; num halt o Reporter não roda). Hoje **não é logado**
  (`run.halt` loga só `type(exc).__name__` — `run.py:367`) nem serializado a saída
  user-facing — a serialização (contrato GitHub Action / PR comment / escalation) está
  **deferida a MC-D** (`models.py:8-10`); por ora só o e2e o asserta (ASCII).
  **Recomendação: ACENTUADO** — é anotação humana destinada a escalation user-facing
  (CLAUDE.md: mensagens de escalação ao usuário são pt-BR), o plano l.121 **já** especifica
  o acentuado (logo o ASCII é **drift** da impl, não decisão), e o ASCII de `windows-tooling.md`
  aplica a **subject/HEREDOC de commit**, não a string de runtime. **Se ratificado:** mudar as
  DUAS branches de `_coverage_gap` (`run.py:264-266`) pra acentuado (`"cobertura zero — scan
  não rodou"` + `"pipeline interrompido em {stage} — análise incompleta"`), atualizar o assert
  ASCII do e2e `test_e2e_detector_scan_error_halts`, e o anchor
  `test_detector_scan_failed_coverage_gap_text` casa o acentuado. (Pequeno — pode ir na PR
  reliability ou numa housekeeping.)

## 4. AC → testes
- **Anchors originais (l.121, a maioria NÃO existe ainda):**
  `test_coordinator_error_envelope_maps_each_exception` (14 exceções → `CoordinatorError`);
  `test_detector_scan_failed_coverage_gap_text` (texto exato — pendente DD-3.3);
  `test_logging_stdout_reserved_for_payload`; `test_provenance_trinca_threads_to_report`
  (per-finding == top-level, RF-009).
- **Acceptance originais (l.122):** `test_as1_retryable_scan_timeout_retries_then_succeeds`,
  `test_as2_retry_exhausted_escalates` (= ADR D2 recovery); `test_as3_layer_enforcement_options`
  (quíntupla `permission_mode/setting_sources/strict_mcp_config` + FQNs por stage, guard
  hífen/underscore).
- **NOVOS (readiness, ADR D1/D5 — red-first):** readiness-timeout (status preso `pending`
  → `CoordinatorStreamFailure`, ADR D4); **preserved-spine regression — o anchor mais
  importante da migração:** os anchors de discriminação de `test_driver.py` (captura
  ResultMessage, refusal-precede-subtype, tabela de subtype, hook, passthrough, validação,
  scratchpad) passam **IDÊNTICOS** após o swap `query()`→`ClaudeSDKClient` — **mesmos asserts,
  mock novo**, NÃO asserts ajustados. Se algum precisar ser **reescrito** (não só re-apontado
  pro mock client) pra passar, o transporte **vazou** pra lógica de discriminação → migração
  não-limpa: **pára e reporta**. + o mock `ClaudeSDKClient`. O **D1 verification gate é SMOKE**
  (não teste hermético), recordado em RESULTS.md.

## 5. Fail-actions latentes (a Fase 3 finalmente exercita)
- **`{"output"}` wrapper no `DetectorOutput` de lista** (`findings:[...]`, o shape #502/#571):
  gated junto com o race desde a 2b — **só observável quando o readiness fix permitir o scan
  rodar** (NÃO está fechado por G0; G0 só cobriu o schema enum-tag do Matcher). G0 (l.67) já
  tem o unwrap armado como fail-action (`structured_output.get("output", structured_output)`
  + 1 retry). Se disparar live no capstone → aplicar o unwrap armado, **NÃO improvisar**
  (gates.md).
- **O retry-budget (l.119):** depende do readiness fix pra ser sequer exercitado.

## 6. Gates à frente + watch-points
- **D1 verification gate** (smoke, RESULTS.md) **ANTES** da impl de readiness — valida/redireciona o ADR.
- Trio hermético por fase; **mypy-strict** (esp. o mock `ClaudeSDKClient` + a união enum-tag — `match verdict`/`assert_never` se precisar).
- **G3 capstone** (live, `@pytest.mark.live`, opt-in) **DEPOIS** do readiness fix; `make_git_repo` synthetic-CPF + POL-000 bundled.
- **Mock-fidelity (a sangria recorrente da 2b — elevar):** smoke-test a superfície do `ClaudeSDKClient` contra `claude-agent-sdk==0.2.87` **real ANTES** de o mock fixar um shape — **OBSERVANDO o retorno real** de `get_mcp_status`/`receive_response`/`reconnect_mcp_server` (esp. o shape aninhado de `McpStatusResponse` = `{"mcpServers":[...]}`), **não inferindo da assinatura**. Mock que mente + teste verde é **pior** que teste vermelho. O nested-shape do `tool_use_result` mordeu na 2b — mesmo risco de campo aninhado aqui. (gates.md / verification-before-inference.)
- O padrão "instalar a MESMA fn em `coordinator.driver.query` E `coordinator.run.query`" **SPLITA** (ADR D5): patch targets heterogêneos (mock client pros stages MCP; `make_query` pro Reporter) — **maior custo de reescrita de teste**.
- `receive_response()` trava sem `ResultMessage` → timeout de stage. Single async context (`client.py:58-64`) → cliente por-stage num único task scope.

## 7. Convenções do ciclo + ambiente
- Um PR por fase (mas ver DD-3.1); corpo do PR linka ADRs (0014/0012/0002/0010) + notas de teste manual; **título via UI preserva acentos; subjects internos ASCII via HEREDOC sob PS 5.1**; **SEM `Co-Authored-By`** (convenção do projeto — `[[no-coauthor-trailer]]` na memória).
- Imports **BARE** (sem `src.`); mock SDK patch-where-used; `asyncio_mode="auto"`; Windows/PS 5.1.
- Runs live de gate = `scripts/smoke_tests/.../RESULTS.md` (gates.md: persiste o desfecho, não o run). Live tests `@pytest.mark.live`, opt-in, fora do CI default.
- **Ambiente (reverificar):** semgrep `1.163.0` instalado ✓ (uv tool, ADR-0010); `gh` autenticado ✓ (PRs via `gh pr create`).

## 8. Itens fora-de-código (território Chat/usuário)
- **ADR-0014** (`docs/adr/0014-...`) — committado como **`Proposed (DRAFT)`** no #93 (a "não-committado" de versões anteriores deste handoff estava stale: o arquivo está em `main`; só o **Status** não é ACCEPTED). **Condição de aceitação CLEARED 2026-06-01 — o D1 verification gate PASSOU sem redirect** (RESULTS.md "GATE D1"). **PRONTO pro flip `Proposed (DRAFT)` → `Accepted`** — **Chat step do usuário** (linkar RESULTS.md "GATE D1" como evidência + preencher a sessão #). Code NÃO flipa o Status (território Chat).
- **PR housekeeping** (separada, não-Fase-3): os débitos de doc-lag de `docs/tasks.md` §Companion + a staleness de `classifier.md` §4.3 (4-vs-5 campos) — memória `mc-c-phase2b-deferred-debts`; **+ DD-3.3 (`coverage_gap` acentuado)**; **+ o fixture-fix do `_make_cpf_repo` (param-named `cpf`) + o docstring stale do g2b ARM-D "BLOCKED by readiness"** (registrar em `docs/tasks.md` §Companion).
- learning-log: a lição `tool_use_result` é canal COMPARTILHADO (acks de structured output + envelopes MCP; `isinstance(dict)` é o discriminador) + "partially-gated" como categoria de desfecho de gate.

## 9. Entry brief da PR-A (prompt-phase3-reliability v2 — Chat-reviewed, ADR-0014-backed)

> O prompt da sessão fresca de **PR-A (reliability)** vive aqui (persistido no handoff por
> decisão do usuário, não em arquivo separado). DD-A1 foi ratificado = **forma-wrapper**, e a
> evidência DD-A1(ii) (o hook levanta `DetectorScanFailed` DENTRO do loop de consumo,
> `hooks.py:51`) **já está codificada no ADR-0014** (D2 + Appendix corrigidos). Abrir a sessão
> fresca com este §9 + o ADR-0014 + RESULTS.md "GATE D1" como fontes.

**Sessão Code — MC-C Fase 3, PR-A (reliability): readiness + recovery transport migration.**
Fresh session (`session-management.md`). Maior risco da fase. Design = **ADR-0014**
(D1+D2+D4+D5; Status `Proposed (DRAFT)`, condição de aceitação CLEARED pelo D1 gate). Ler
**ADR-0014 inteiro** + **RESULTS.md "GATE D1"** + a spine **`coordinator/driver.py`** +
**`coordinator/run.py`** + **`subagents/detector/hooks.py`** antes de codar.

**PRIMEIRA AÇÃO (não-impl):** `git log main --oneline -6` + `git status` — confirmar #92/#93 em
`main`, 127 testes verdes, os 2 probes D1 + RESULTS.md "GATE D1" + esta registration presentes.
Não confiar em SHAs.

**MODE: plan-mode (Fase 1 DDs → gate → Fase 2).** Enumerar DDs, esperar OK, implementar.

**O que o gate JÁ PROVOU (não re-litigar, não re-rodar):** readiness-wait via `ClaudeSDKClient`
re-apresenta `scan_diff` ao modelo (init tools incluem o tool; o modelo o chama; semgrep roda).
ADR D1 **como escrito**. Os shapes de mock-fidelity estão **observados** —
`scripts/smoke_tests/coordinator_live/d1_mock_fidelity_smoke.py` é a **fonte-de-verdade do shape
do mock** (não re-inferir da assinatura).

**Fase 1 — DDs a enumerar + recomendar (PARA pro OK):**
- **DD-A1 — threadar o transporte (RATIFICADO = forma-wrapper; confirmar com o código na frente).**
  Detector/Classifier/Matcher migram pro `ClaudeSDKClient`; **Triager fica no `query()`**. **DUAS
  formas registradas:** **(W) wrapper (ADR sketch) — ESCOLHIDA:** extrair o *tail* de
  discriminação de `run_branch_b_stage` num `_discriminate_and_capture(last_result, ...)`
  (refusal-precede-subtype, tabela de subtype, validação Pydantic, `verify_passthrough`,
  `write_scratchpad`, return); um driver novo `_run_mcp_stage` abre cliente + wait-for-connected +
  drena `receive_response()` e **chama o mesmo `_discriminate_and_capture`**; `run_branch_b_stage`
  mantém o caminho `query()` (Triager) e **também** chama o tail. **(M) `mcp_target: str|None`**
  (branch de transporte dentro de `run_branch_b_stage`). **RAZÃO de W:** o tail é uma função única
  intocada e o contrato externo de `run_branch_b_stage` pro Triager não muda → os anchors de
  discriminação de `test_driver.py` passam **IDÊNTICOS tautologicamente** (travamento #1 mais
  forte); M reestrutura a spine, e o anchor do Triager só cobre o branch `query()`. **CUSTO de W
  (já no ADR D2 + Appendix):** o hook levanta `DetectorScanFailed` DENTRO do `async for` de consumo
  (`hooks.py:51`), então W **duplica** o loop de consumo + hook + mapeamento `CoordinatorStreamFailure`
  em `_run_mcp_stage` (~10 linhas), e o **`try/except DetectorScanFailed` do retry envolve o LOOP
  DE CONSUMO** (não o tail). Net: custo mecânico < benefício (discriminação single-source) → W.
- **DD-A2 — budgets (ADR Deferral A, provisório GENEROSO).** Cold-start ≈ 3.5 s *idle*; CI sob carga
  mais lento. Assimetria: timeout generoso só custa latência numa falha rara; apertado custa **falso
  `CoordinatorStreamFailure`** num server que IA conectar (parece bug). `READINESS_POLL_S=0.5`,
  **`READINESS_ATTEMPTS≈40` (~20 s)**, `RETRY_BUDGET=1`. Comentário no código: `"margem pra CI sob
  carga; calibracao real = MC-D"`.
- **DD-A3 — retry-loop SÓ no Detector — RATIFICADO.** Readiness (D1) nos 3 stages MCP; recovery (D2)
  só no Detector (único com hook `isRetryable`-driven). Generalização ao Matcher = gated num hook
  inexistente → **fora da PR-A, flag explícito, NÃO inventar o hook**.
- **DD-A4 — split de patch-target (ADR D5).** mock client pros stages MCP (`coordinator.driver`);
  `make_query` permanece pro Triager + Reporter (`coordinator.run`).

**TRÊS INVARIANTES TRAVADAS:**
1. **Preserved-spine regression (anchor mais importante).** Os anchors de discriminação de
   `test_driver.py` passam **IDÊNTICOS** pós-swap (mesmos asserts, mock novo). **Se QUALQUER anchor
   precisar ter os ASSERTS reescritos** (não só patch-target trocado) → **transporte VAZOU →
   migração não-limpa → PÁRA E REPORTA** (não "ajeita o assert"). Halt-condition (`gates.md`). A
   forma W foi escolhida pra tornar este anchor tautológico.
2. **Retry-loop: `async with ClaudeSDKClient(...)` FORA do loop de retry** (sessão por-stage, abre
   uma vez, envolve readiness-wait + todos os retries). Retry = `reconnect_mcp_server(target)` +
   re-`query()` **IN-SESSION**, **NUNCA re-spawn**. O `try/except DetectorScanFailed` do retry
   **envolve o LOOP DE CONSUMO** (ADR D2 + Appendix; `hooks.py:51`).
3. **Mock `ClaudeSDKClient` espelha o shape OBSERVADO verbatim** (de `d1_mock_fidelity_smoke.py`):
   `get_mcp_status()` → `{"mcpServers":[{...}]}`; `pending` = `{name,status:'pending',config,scope}`
   **sem** `tools`/`serverInfo`; `connected` += `serverInfo:{name,version}` +
   `tools:[{name:'scan_diff',annotations:{}}]`; `reconnect_mcp_server()` → `None`. Async CM,
   `query()`, `receive_response()` (replay do MESMO script de `make_query` — reusa
   `sdk.result`/`assistant_tool_use`/`scan_error`), status scriptável (`pending→connected` ou preso
   `pending` pro readiness-timeout), `reconnect_mcp_server()` call-counted.

**ESCOPO — PR-A SÓ (MATERIALIZAR b/c/e):** (b) migração `ClaudeSDKClient` (forma W) com
`_discriminate_and_capture` extraído; (c) retry-loop in-session (Detector); (e) mock
`ClaudeSDKClient` no conftest. **FORA da PR-A** (→ PR-B / housekeeping): anchors de hardening l.121,
capstone G3, DD-3.3 (`coverage_gap` acentuado), **fixture-fix do `_make_cpf_repo`**.

**AC → testes (red-first):** mock `ClaudeSDKClient` (espelha o smoke); readiness-timeout (preso
`pending` → `CoordinatorStreamFailure`, D4); `test_as1_retryable_scan_timeout_retries_then_succeeds`
(**exatamente 1** `reconnect_mcp_server` call, in-session, sem re-spawn);
`test_as2_retry_exhausted_escalates`; **preserved-spine regression** (anchors de `test_driver.py`
verdes IDÊNTICOS — halt #1).

**Gates:** trio hermético (`uv run pytest tests/coordinator tests/subagents -q` + `ruff check
src/coordinator src/subagents tests/...` + `mypy --strict src/coordinator src/subagents`) — alvo
**127 + novos** verdes; mypy-strict no mock + na união enum-tag. Mock-fidelity + D1 gate **já feitos**.

**Convenções:** imports BARE; mock SDK patch-where-used; `asyncio_mode="auto"`; Windows/PS 5.1; **SEM
`Co-Authored-By`**; título do PR via UI / subjects internos ASCII; corpo do PR linka ADR-0014 +
RESULTS.md "GATE D1" + notas de teste manual. PR é passo manual do usuário.

**Fontes-de-verdade:** ADR-0014 (Decision + Appendix, já c/ DD-A1(ii)) · RESULTS.md "GATE D1" ·
`d1_mock_fidelity_smoke.py` (shape do mock) · `driver.py`/`run.py`/`hooks.py` ·
`.claude/rules/sdk-mcp-conventions.md`.

## 10. Entry brief da sessão G3 (capstone Fase 3 — milestone-level, live)

> Fase 3 reliability **FECHADA** (PR-A #95, ADR-0014 Accepted #96, cleanup #97). G3 é o
> **capstone milestone-level**: a rodada viva, opt-in, que valida o pipeline inteiro **agora que
> o readiness foi consertado** — e faz a **primeira observação do wrapper `{"output"}`** num
> `DetectorOutput` lista-não-vazia. NÃO é feature nova; é o gate que prova a migração
> ponta-a-ponta. Padrão 2a/2b: Code rascunha a forma do unwrap → Chat ratifica (com handoff §5
> aberto) → sessão fresca executa. Abrir com este §10 + handoff §5 + ADR-0014 (Accepted) + a
> `driver.py`/`run.py`/`g2b` mergeadas.

**PRIMEIRA AÇÃO (não-impl):** `git log main --oneline -8` + `git status` — confirmar #95/#96/#97
em `main`, **140 testes verdes**, o g2b re-apontado pro `_run_mcp_stage` + a fixture param
(`def collect(cpf):`) presentes. Não confiar em SHAs.

**MODE: plan-mode (Fase 1 DDs → gate → Fase 2).** UMA DD load-bearing a ratificar **ANTES de
qualquer rodada viva** — é a única incerteza real da fase (transporte e fixture já são
determinísticos):

- **DD-G3-1 — fork do unwrap do wrapper `{"output"}` (DECISÃO ANTES do gate; handoff §5 aberto).**
  O `DetectorOutput` populado no G3 é o **primeiro teste vivo** de se o SDK embrulha o
  `structured_output` lista-shaped sob `{"output"}` (#502/#571, ainda **não observado** — G0 só
  cobriu o schema objeto/enum-tag, que é quieto). O driver **não desembrulha** nada
  (`_discriminate_and_capture` → `model_validate` direto); se o wrapper disparar →
  `SubagentValidationFailed`. **gates.md: não improvisar dentro do gate** → decidir a forma do
  unwrap PRIMEIRO. Três formas (Chat ratifica com §5 na frente):
  - **(a)** unwrap transparente em `_discriminate_and_capture` antes do `model_validate`,
    uniforme a todo estágio;
  - **(b)** unwrap só no retry pós-`ValidationError` (validation-retry-loop, mais fiel ao §5:
    `structured_output.get("output", structured_output)` + 1 retry);
  - **(c)** escopado só aos outputs lista (`DetectorOutput`/`MatcherOutput`).
  → Se o wrapper ficar **quieto** (provável, por G0): nenhuma mudança de código; o gate passa e
  registra "wrapper quiet on populated list". Se **disparar**: aplica a forma ratificada, **não
  improvisa**.

**TRAVAMENTO — observe-vs-calibrate (pureza do gate, não-negociável).** O G3 **OBSERVA + REGISTRA**
o timing real (poll-counts até `connected`, scan elapsed, retries). A calibração de **Deferral A**
(`READINESS_ATTEMPTS`/`READINESS_POLL_S`/`RETRY_BUDGET`/`STAGE_TIMEOUT_S`) é passo **downstream
separado**, com os números na frente — **não** um ajuste improvisado durante a rodada (mesmo
anti-padrão "decidir dentro do gate" que o D1 evitou). A memória chama Deferral A de "calibração
real = MC-D"; respeitar ou **promover explicitamente** — decisão do usuário, fora do gate.

**O que o G3 MATERIALIZA:** uma rodada **viva, opt-in (`@pytest.mark.live`, fora do CI default)**
do `run_pipeline` ponta-a-ponta: repo git synthetic-CPF (param `cpf` — já em `_make_cpf_repo`,
#97) + **POL-000 bundled** → `run_pipeline(scope)` → assere `CoordinatorReport` com finding
populado (Detector achou o param `cpf`), a cadeia Classifier→Matcher→Reporter rodando em dado
real, POL-000 `not_applicable` floor, `counts == aggregation`, e o **wrapper `{"output"}`
observado** (quieto ou tratado pela forma DD-G3-1). Os arms re-apontados do g2b (D/E/F/G, #97)
são o **complemento granular** — observação por-estágio (wrapper isolado no D, hook-error no G,
passthrough no E/F) que um relatório e2e único não dá. **G3 = `run_pipeline` e2e (composição) +
g2b arms (granular).**

**PRÉ-CONDIÇÕES (TODAS FEITAS):** readiness fix (#95); ADR Accepted (#96); g2b re-apontado +
fixture param (#97). G3 **não está mais bloqueado** (nem pela corrida de cold-start, nem pela
fixture de finding-vazio).

**ESCOPO — G3 SÓ:** o capstone. FORA: a **PR de string** (doc-lags — `classifier.md` §4.3, DD-3.3
`coverage_gap` acentuado, `.gitignore` do `scheduled_tasks.lock`) é housekeeping **separada**
(antes/independente do G3, não dobra); a calibração de Deferral A é downstream.

**AC → evidência (milestone-level; gates.md persiste o desfecho, não o run):** `run_pipeline` e2e
PASS (`CoordinatorReport`, finding populado, POL-000 floor, `counts==aggregation`, wrapper
observado); g2b D/E/F/G re-run PASS; a observação do wrapper `{"output"}` registrada em RESULTS.md
**"GATE G3"**.

**FONTES-DE-VERDADE (ler antes de codar):** handoff **§5** (o fail-action do wrapper — o §5 a abrir
pra DD-G3-1) · `src/coordinator/driver.py` mergeado (`_run_mcp_stage` + `_discriminate_and_capture`,
**sem unwrap**) · `src/coordinator/run.py` (`run_pipeline`) · `scripts/smoke_tests/coordinator_live/g2b_mcp_middle_live.py`
(#97: arms no `_run_mcp_stage` + `_make_cpf_repo` param) · ADR-0014 (Accepted) · `.claude/rules/gates.md`
(não improvisar no gate). A memória `mc-c-phase3-g3-blocking-debts` foi **deletada** — os dois
débitos foram resolvidos por #97.

**Convenções:** live `@pytest.mark.live` opt-in; evidência em RESULTS.md "GATE G3"; imports BARE;
mock patch-where-used (qualquer teste hermético novo); `asyncio_mode="auto"`; trio (pytest + ruff +
mypy-strict) pros testes herméticos; Windows/PS 5.1; **SEM `Co-Authored-By`**; **a DD-G3-1 (unwrap)
passa pelo Chat com o §5 aberto ANTES da rodada viva**; PR é passo manual do usuário.
