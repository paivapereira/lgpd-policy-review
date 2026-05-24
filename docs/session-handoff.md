# Session Handoff #35 → #36

**De:** Sessão #35 (Chat prep T-fix v1→v3 + Code aplicação PR #59 + gate Milestone B PASS empírico)
**Para:** Sessão #36
**Data:** 2026-05-24
**Estado:** PR #59 pronta para merge; chore com script patched local não-pushed; gate Milestone B PASS confirmado empíricamente; milestoneB.md draft entregue como artefato Chat (definitivo após squash hashes).

---

## 1. Estado factual do repo

- **Branch atual recomendada para #36:** `main` após pull do merge da PR #59.
- **PR #59** — `fix/scan-diff-stdin-isolation-windows-stdio` → main. 1 commit `6f9bc44`. Diff: `tools.py +3 / test_scan_diff.py +134`. **Status ao fechar #35: aprovada para merge pelo Chat; aguardando ação manual do operador.**
- **Branch local `chore/gate-milestone-b-rule-set-fixture`** — 3 commits: `19e0536` (pack alternativo), `84672a5` (gate script v1), `34b6c05` (patch script #35). **Não pushed ao fechar #35.**
- **Branches descartáveis pós-merge:** `fix/scan-diff-stdin-isolation-windows-stdio` (depois do squash); `test/gate-on-fix` (antigo); `test/gate-on-fix-v2` (validação #35).
- **Untracked persistente:** `gate_b_output.json` (evidência consolidada do gate PASS, sessão #35) e `gate_b_stderr.log` (verbose stderr da #35).
- **Tests pós-merge da PR #59:** 134 passing esperado em Windows local; 133 em Linux/macOS (AS-14b skipped).

## 2. Tasks pendentes para sessão #36

### (B) Confirmação documental do gate PASS — sessão #36 abertura

- Atualizar `docs/learning-log.md` entry #34 (já existente) com 1 linha de PASS confirmation citando hash do merge da PR #59 + hash do merge da PR chore quando esta vier.
- Atualizar `docs/learning-log.md` entry #35 (entregue como artefato Chat — `learning-log-35.md` em outputs; integrar ao log oficial).
- ~5min Code ou pode ser absorvido pela sessão que abre PR chore.

### (C) Push + PR de `chore/gate-milestone-b-rule-set-fixture`

- Rebase de `chore/*` sobre `main` pós-merge PR #59 (deve ser limpo; arquivos disjuntos).
- `git push -u origin chore/gate-milestone-b-rule-set-fixture`.
- Abrir PR via GitHub. Description cita: (a) gate PASS empírico contra `test/gate-on-fix-v2`; (b) 3 commits internos (pack + script v1 + patch #35); (c) evidência do `gate_b_output.json` consolidado.
- Decisão pendente: incluir cleanup do `gate_b_output.json` + `gate_b_stderr.log` na PR ou diferir para housekeeping? Inclinação: defer + adicionar pattern ao `.gitignore` em housekeeping própria — separação de concerns.
- ~30min Chat de redação + Code de push + review.

### (D) Redação definitiva de `docs/milestoneB.md`

- Draft entregue como artefato Chat (`milestoneB-draft.md` em outputs) com `<TBD>` para squash hashes.
- Sessão #36 popula hashes pós-merges (PR #59 + PR chore).
- Adicionar §"Limitações conhecidas" referenciando o defeito de aferição do `summarize_phase` original e sua resolução cruzada no patch da #35 — ilustra empíricamente "defeito mascarado por defeito upstream".
- ~30min Chat para popular + revisar + integrar.

### (E) ADR-0012 pos-hoc

- Sessão Chat própria. Não bloquear (C)/(D).
- Dois eixos:
  - **(E-1)** Mecânica fina Windows-stdio handle inheritance. Hipótese principal: handle inheritance do anonymous pipe Windows usado para stdio MCP + `subprocess.Popen.wait()` no parent + Win32 internals não totalmente caracterizados. Insight R-3 da #35: caracterização Win32 deveria considerar cascading inheritance em sub-processes do semgrep-core (não vimos hang com fix aplicado, mas teoricamente ortogonal e merece nota).
  - **(E-2)** Design da separação de classes de erro (Fix-4 deferido). Três opções identificadas em review v2 do prompt T-fix: (a) signature change dos helpers + caller restructure; (b) custom exception types raised + caught em `scan_diff`; (c) outro pattern emergente da deliberação ADR.
- Pos-hoc tem precedente projetual forte: ADR-0001 D2 amendment retroativo (Presidio→Semgrep); ADR-0004 retroativo (uv migration).
- ~2-3h Chat dedicada.

### (F) PR posterior implementando ADR-0012 (E-2)

- Após ADR-0012 ratificar opção de design.
- Inclui AS-15 com mock filtrado por comando (R2 N-S1 da #35 review): mock target precisa filtrar por `cmd[:3] == ["git", "rev-parse", "--verify"]` ou similar; senão primeira `subprocess.run` a disparar é `_is_shallow_repository`, não `_resolve_ref`, e AS-15 cobre o helper errado.
- Adicionalmente: split AS-15 em 2 tests (um por helper) per `.claude/rules/test-strategy.md` "granularity calibrada por failure dimension expected".
- ~3-5h Code (depende da opção ratificada em E-2).

### (G) Housekeeping CLAUDE.md `§Status flags`

- Drift de ≥6 linhas em 3 bullets distintos (catalogado em DD-Tfix-1 da #35 / Pin 7 da #35 Code):
  - Bullet 1: status milestone stale ("T06 + T07 + gate pending"; T06/T07 mergeados, gate PASS).
  - Bullet 2: contagem de tests stale ("64 passing"; real é 134 pós-#35).
  - Bullet 3: descrição semgrep-runner stale ("scan_diff stub returning NOT_IMPLEMENTED"; scan_diff real implementado e exercido).
- Bloqueante para Milestone C arrancar; não-bloqueante para (D)/(E)/(F).
- Sessão housekeeping própria ou consolidada com sweep imutável-rules.
- ~1h Chat + Code.

### (H) Cleanup operacional menor

- `gate_b_output.json` + `gate_b_stderr.log` em working dir (untracked).
- Decisão: adicionar pattern `gate_b_*.json` + `gate_b_*.log` ao `.gitignore` na housekeeping (G) acima.
- ~5min.

## 3. Catches catalogados (não bloqueantes para sessão #36)

| # | Item | Severidade | Locus sugerido |
|---|------|-----------|----------------|
| 1 | Cold-start `StdioTransport` não medido empiricamente na #35 (R-1 do Code #35). Threshold 10.0s no AS-14b é margem confortável dado defeito ~22-23s vs success ~5-8s, mas pode flake em CI Windows extremamente fria (antivírus inspecionando python.exe). | Cosmético | Ajustar threshold em PR follow-up se flake materializar; não-bloqueante. |
| 2 | Cascading inheritance em sub-processes do semgrep-core (R-3 do Code #35). Ortogonal ao defeito empírico; não vimos hang com fix aplicado. | Substantivo conceitual | Input do ADR-0012 (E-1). |
| 3 | `gate_b_output.json` + `gate_b_stderr.log` untracked. Evidência operacional; cleanup em housekeeping. | Cosmético | (H) + `.gitignore` pattern. |
| 4 | Branch `chore/gate-milestone-b-rule-set-fixture` tem 3 commits internos (pack + script + patch); operador pode preferir squash em 1 commit ao abrir PR ou manter 3 para audit trail. | Estilístico | Decisão da #36 ao abrir PR. |
| 5 | Defeitos de aferição do `summarize_phase` original (catch #2 do handoff #34→#35) foram promovidos a defeitos ativos na #35 quando fix do `subprocess.run` desbloqueou o caminho. Pattern "defeito mascarado" merece registro em milestoneB.md §"Limitações conhecidas" como ilustração metodológica. | Substantivo metodológico | (D) milestoneB.md. |

## 4. Pre-flight para sessão #36

Antes de abrir Chat #36 (qualquer task acima):

- **Confirmar merge da PR #59 em main.** `git log main --oneline -3` mostra commit do merge; squash hash a registrar nos artefatos pendentes.
- **Confirmar estado de branches.** `git branch -a` deve mostrar: `main` atualizada; `chore/gate-milestone-b-rule-set-fixture` local; branches descartáveis deletadas (ou ainda presentes, sem importância).
- **Confirmar untracked.** `git status` deve listar `gate_b_output.json` + `gate_b_stderr.log` como untracked (não modificar; cleanup em (H)).
- **Para task (C):** rebase de `chore/*` sobre `main` pós-fix deve ser limpo. Se conflitar, halt-and-escalate (significaria que algum arquivo em comum mudou pós-fix — não-esperado dado que arquivos da PR #59 e da chore são disjuntos).
- **Para task (D):** ter em mãos squash hash da PR #59 + squash hash da PR chore (quando esta for mergeada) para popular `<TBD>` no draft.
- **Para task (E):** carregar contexto de ADR-0001 D2 amendment + ADR-0004 como precedentes de ADR pos-hoc.

## 5. Conceitos da prova relevantes para sessão #36

Anotar para uso em tasks específicas:

- **D5 (Reliability) — defeito empilhado em layers.** Pattern "defeito em layer-2 mascarado por defeito em layer-1" materializado em duas fases sequenciais (#34 → #35). Cobertura ratifica que PASS em um nível não atesta correção em outros níveis. Defense candidate forte para Capítulo de Método.

- **D4 (Prompt Engineering) — calibração de cerimônia proporcional à complexidade.** Briefing T-gate-script-fix da #35 usou ~180 linhas (4 Pins simples + 1 DD + GATE 1 leve) vs T-fix da PR #59 com ~470 linhas v3 (9 Pins + 2 DDs + GATE 1 estruturado). Cerimônia proporcional à complexidade é skill discriminada do exam guide; aplicar em #36 — task (C) push+PR e (D) milestoneB são prep leve; (E) ADR-0012 é prep deliberativa pesada.

- **D2 (Tool Design) — convergência > consistência local.** Pin 2 da #35 Code venceu inclinação do Chat: idioma do projeto (`rsplit(".", 1)[-1]` de `_short_rule_id`) prevaleceu sobre proposta nova (`endswith("rules.<name>")`). Pattern empírico para futuras tasks: prompts devem instruir Code a verificar convenções locais antes de aplicar proposições do Chat.

- **D1 (Agentic Architecture) — validação antecipada via branch temporária.** Pattern de criar branch combinada local + validar + descartar é análogo conceitual a `fork_session` aplicado ao Git workflow. Reduz risk pós-merge sem comprometer trunk. Aplicar quando task #36 (F) abrir PR posterior implementando ADR-0012.

---

**Status do handoff:** completo. Próxima sessão Chat (#36) consume este documento + draft milestoneB + draft learning-log #35 como base.

**Custo total da sessão #35:** ~3-4h Chat (prep T-fix v1→v3 + reviews + briefing T-gate-script-fix + handoff/learning-log/milestoneB authoring) + ~2.5h Code (T-fix execution PR #59 + gate script patch). Ratio Chat:Code = ~1.5:1. Proporcionalmente mais Code-pesado vs sessões prep T06/T07 (6:1) — esperado para sessão de execução + validação.

---

obs handoff-35-36.md:

§1 "Branch local chore/gate-milestone-b-rule-set-fixture" — reescrever bullet inteiro de "3 commits internos não-pushed" para "mergeada em main como b4ec3fe (PR #60); branch deletável."
§1 "PR #59 — squash hash <TBD>" → preencher com hash real.
§1 "branches descartáveis pós-merge" — adicionar chore/gate-milestone-b-rule-set-fixture à lista.
§2 task (C) — marcar como concluída com referência a PR #60 + b4ec3fe; tasks subsequentes (D/E/F/G/H) permanecem.
§4 "Para task (C)" pre-flight — remover (concluída).