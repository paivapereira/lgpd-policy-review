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
está **reconciliada aqui** — não transcreva o plano). **A primeira ação TÉCNICA da
fase NÃO é implementação — é o D1 verification gate (probe), §2 passo 1.**

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
1. **D1 verification gate — PRIMEIRA AÇÃO, não implementação.** Probe que abre
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

**PRONTO — herdar, NÃO reescrever:** todo o flesh de 2a/2b (prompts/hook/passthrough/
constants/wiring); logging + `_coverage_gap` + `CoordinatorError`; o hook escalate-all
(carrega `is_retryable`, ainda não age sobre ele); os 127 testes; o mock-SDK conftest.

**MATERIALIZAR:** (a) o probe do D1 gate; (b) a migração `ClaudeSDKClient` no spine
`run_branch_b_stage` (prólogo de transporte); (c) o retry-loop in-session; (d) os anchors
de hardening (l.121) + a acceptance de layer-enforcement; (e) o **mock `ClaudeSDKClient`**
no conftest; (f) o capstone G3.

## 3. DDs abertos (ratificar ANTES de implementar — a primeira ação é o gate, não isto)
- **DD-3.1 — sub-divisão de PR.** Fase 3 expandida = **UMA PR ou DUAS?** Reliability
  (readiness+recovery, ADR-0014, mudança de transporte do driver, **risco real — o D1 gate
  pode redirecionar**) vs hardening+capstone (logging tests + G3, incremental, baixo risco).
  **Inclinação: SUB-DIVIDIR** (PR reliability primeiro; PR hardening+capstone depois) pra
  não prender o hardening trivial atrás do risco da migração de transporte. Desvia de
  "one PR per phase" — **decisão consciente, registrar** (git-conventions).
- **DD-3.2 — desfecho do D1 verification gate.** O gate pode gerar uma segunda DD se
  **redirecionar** (ADR D1 precisa de shape diferente — connected-antes-do-stream, ou
  re-prompt-após-connect). Não dá pra pré-decidir; o desfecho do gate decide o desenho da migração.
- **DD-3.3 — texto do `coverage_gap` → RECOMENDAÇÃO: ACENTUADO (ratificar).**
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
- **ADR-0014** (`docs/adr/0014-...`) — DRAFT, **não-committado**, em revisão no Chat; aceitação **condicional ao D1 verification gate**. **NÃO registrar como ACCEPTED até o gate passar** — se o gate redirecionar (modelo age sobre o snapshot de init), o ADR D1 muda de forma, e um ADR proposed que depende de uma verificação não-feita não vira accepted antes dela (honestidade epistêmica aplicada ao próprio registro de decisão).
- **PR housekeeping** (separada, não-Fase-3): os débitos de doc-lag de `docs/tasks.md` §Companion + a staleness de `classifier.md` §4.3 (4-vs-5 campos) — memória `mc-c-phase2b-deferred-debts`.
- learning-log: a lição `tool_use_result` é canal COMPARTILHADO (acks de structured output + envelopes MCP; `isinstance(dict)` é o discriminador) + "partially-gated" como categoria de desfecho de gate.
