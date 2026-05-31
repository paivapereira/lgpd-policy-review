# Session handoff — implementação MC-C (entrada da Fase 2a, lado Code)

> **Durante o ciclo de implementação MC-C este handoff é território do Code**
> (o Chat corrige a implementação, não o handoff). Cada fase roda em **sessão
> Code fresca** (`.claude/rules/session-management.md`). O brief detalhado
> cross-session vive em `scripts/smoke_tests/coordinator_live/RESULTS.md` (seção
> "Phase 2a — CONSOLIDATE BRIEF") — leia-o + o plano antes de codar.

## 0. Primeira ação ao abrir a sessão
`git log main --oneline -6` + `git status` — verifique o estado real; **não
confie em SHAs deste doc** se algo já mergeou. Plano completo (5 fases):
`C:\Users\paiva\.claude\plans\quero-que-analise-as-graceful-steele.md`.

## 1. Onde estamos
- **Fases 0 e 1 mergeadas** em `main`: **#88** (type graph + A9/A2/§923) e **#89**
  (walking skeleton). `main` @ `29e52e8`+.
- **80 testes verdes**; ruff + mypy --strict limpos. Gates **G0 PASS**, **G1 PASS**
  (skip-path; proceed-path live deferido a G2b).
- A9 fechado nos quatro loci (cross-check `total==sum` é do handler, errorCode
  `TOTAL_NOT_SUM_OF_COUNTS`; `SubagentToolError` base introduzida em MC-C,
  hierarquia segue ADR-0013). Critério de fechamento: `grep -n model_validator
  docs/specs/subagents/reporter.md` → 2 hits (§386, §923), **ambos negando**.

## 2. Próximo: Fase 2a — fechar as pontas (Triager + Reporter)
Branch a partir de `main`: `feat/mc-c-phase2a-ends`.

**PRONTO — herdar, NÃO reescrever:** `coordinator/{errors,models,config,driver,run}.py`;
todos `subagents/*/models.py` (single-source `Finding`/`TriagerInput`/`ScanProvenance`);
`reporter/tools.py` factory (**os 4 cross-checks estão STUBBED**); `reporter/constants.py`
(`EMIT_REPORT_DESCRIPTION` já canônico); 5 `system_prompts.py` + `coordinator/prompts.py`
`build_*_prompt` STUBS; mock-SDK conftest (fixture `sdk`).

**MATERIALIZAR (engordar, não re-scaffold):**
1. `subagents/triager/system_prompts.py` — `TRIAGER_SYSTEM_PROMPT` canônico (triager §5.1:
   4 few-shots, XML); enriquecer `build_triager_prompt`.
2. `subagents/reporter/system_prompts.py` — `REPORTER_SYSTEM_PROMPT` canônico (reporter §5.1:
   XML + 1 few-shot example_input/example_tool_call).
3. `subagents/reporter/tools.py` `emit_report_handler` — os 4 cross-checks, **em ordem, ANTES**
   do atomic write:
   - #1 `policy_clause_ref` regex `^POL-\d{3}$` por finding → `CLAUSE_REF_FORMAT`.
   - #2 trinca top-level == per-finding → `PROVENANCE_MISMATCH`.
   - #3 counts == agregação(findings) → `COUNTS_DISAGREE_WITH_FINDINGS`; total == sum(counts)
     → `TOTAL_NOT_SUM_OF_COUNTS` (dois codes distintos; **A9: vivem no handler, não num
     `model_validator` do `SummaryModel`**).
   - #4 `report_id == expected_report_id` (closure) → `REPORT_ID_MISMATCH`.
   - **BUG a corrigir do stub da Fase 1:** `_validation_error_envelope` põe o erro estruturado
     em `structuredContent`, que o bridge do SDK `@tool` **descarta**. Mover o erro estruturado
     para `content` (string JSON) + flag `is_error: True` (`.claude/rules/sdk-mcp-conventions.md`;
     cross-ref `sdk_tool_error_channel/RESULTS.md`).

**Anchors red-first (escrever VERMELHO contra o handler stub PRIMEIRO):**
`test_emit_report_counts_disagree`, `test_emit_report_id_mismatch` (maior valor — auditabilidade
do Reporter), `test_emit_report_clause_ref_regex`, `test_emit_report_trinca_mismatch`,
`test_emit_report_dual_sink`; Triager `test_triager_prompt_renders_all_refs` +
`test_as*_triager_proceed/skip/refusal` (mock-SDK canned). **Já coberto na Fase 1 (não refazer):**
discriminação tri-axial §3.5 + `test_skeleton_reporter_not_emitted` (`test_walking_skeleton.py`).

## 3. Watch-points (carregar para 2a)
- **A9:** `SummaryModel` permanece PERMISSIVO em `total==sum`
  (`test_summary_model_is_permissive_on_total_sum`). **NÃO** adicionar `model_validator`.
- **`{"output"}` wrapper:** G0 provou que enum-tag não dispara nos modelos reais; o driver
  **não** faz unwrap — manter; reconfirmar live em G2b.
- **`tools` por stage** (strict-equality, guard #48-b): é Fase 2b (Classifier/Matcher). 2a toca
  só Triager (`tools=["Read","Glob"]`) + Reporter (`tools=[]`); options já wired em `run.py`.

## 4. Gates à frente
- **G2a (esta fase):** suíte mock dos 4 cross-checks + probe live "ends" (`coordinator_live/`,
  **sem semgrep** — Triager `mcp_servers={}`, Reporter in-process): Triager proceed+skip live +
  cross-checks do emit_report disparam.
- **G2b (Fase 2b):** proceed-path live — **precisa de semgrep instalado** (ver §6).

## 5. Convenções do ciclo
- Um PR por fase; corpo do PR linka ADRs + notas de teste manual (mudança no agent-loop).
- **Squash-merge + branches stacked:** após cada merge, `git rebase --onto origin/main
  <old-base-sha> <branch>` dropa os commits redundantes do squash (a colisão de `config.py` da
  Fase 1 veio disso — resolvida assim).
- Imports **BARE** (sem prefixo `src.`); mock SDK em `coordinator.driver.query` **e**
  `coordinator.run.query`; `asyncio_mode="auto"`; Windows/PS 5.1.
- Runs live de gate = `scripts/smoke_tests/.../RESULTS.md` (gates.md: persiste o desfecho, não o run).

## 6. Ambiente (preparado pelo usuário neste ciclo — reverificar)
- **semgrep:** `uv tool install semgrep==1.163.0` (ADR-0010). Necessário para G2b + os 55 testes
  `semgrep_runner` (ausência local = NÃO são regressões; 110 não-semgrep verdes).
- **gh:** `gh auth login` (para a próxima sessão abrir PRs sozinha; sem isso, push funciona via
  credential helper mas `gh pr create` falha — abrir via URL `compare` na UI).
