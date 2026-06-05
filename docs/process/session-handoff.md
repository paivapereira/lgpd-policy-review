# Session handoff — frente de avaliacao — pos-Passo-4 (Camada-3-MVP FECHADA)

> Template-overwrite, nao patch cumulativo. Tratar como hipotese a verificar contra o
> repo (git log, leitura de arquivo), nao como estado autoritativo. Primeira acao de
> qualquer sessao Code: confirmar git state, nao assumir.

## Onde estamos

Caminho critico da frente de avaliacao: **1 -> 1.5 -> 2 -> 3 -> 4 (FECHADO).**
O caminho critico do entregavel 15/06 esta CONCLUIDO. O que resta nao e construcao.

### Passo 4 / Camada-3-MVP — FECHADO (2026-06-04)

GitHub Action funcional que roda o pipeline real e compara contra baseline
field-scoped. Tres PRs squash-merged em `main` (`b9259c3`): #107 (entrypoint +
format_summary), #108 (companion edits B/C), #109 (harness gate + workflow).
Doc de fecho `docs/process/camada3-mvp.md` (status: FECHADA).

- **Local (K=2): PASS.** Convergencia estrita nos 3 fixtures (COMP/VIOL/SKIP), 2
  rodadas live. Unica divergencia = data_categories do COMP-001 (advisory, inocua).
- **CI: CONFIRMADO.** Run 26983111920 — 3 arms PASS. Gate #1 (auth API-key + wheel)
  e Gate #2 (--project/cwd-efemero) selados no runner ubuntu.
- **rule_id bare `br-cpf`** confirmado e2e pos-#105 (blocker fechado, K=2 + CI).

Pecas (todas em `main`): `scripts/ci/{format_summary,run_review}.py`,
`eval/harness/{camada3_compare,camada3_gate,synthetic_pr}.py`,
`.github/workflows/lgpd-review.yml`, testes em `tests/ci/` e `tests/harness/`.

## Proximo passo: criar casos de teste para documentar a avaliacao via pipeline GitHub

Expandir a cobertura de avaliacao alem da triade MVP. Os 3 fixtures restantes ja
existem em `eval/prs/` mas foram diferidos no MVP: **INDET-001** (perfil/
anonimizacao -> indeterminate), **PROBE-UNGOV-001** (localizacao, lacuna de
cobertura -> not_applicable+coverage_gap), **SWAP-001** (mesmo codigo, vocab GDPR
-> flip de base legal).

**Primeiro movimento e inventario, nao design** (mesma disciplina do Passo 4):
- Confirmar quais dos 3 tem `.expected-report.json` committado e quais sao
  `engine_runnable` (ver `eval/cases.yaml`). PROBE-UNGOV e INDET tem baseline;
  SWAP-001 roda root eval-gdpr (policy_root distinto) — confirmar.
- Decidir: entram na **matrix do workflow_dispatch** (geram baseline via
  `run_engine_cases.py`, gate estrito), ou ficam como **eval qualitativa** (casos
  que exercitam vereditos que a triade MVP nao cobre — indeterminate, coverage_gap,
  flip GDPR)? PROBE-UNGOV tem GT condicional (imprecisao 4-vs-1 documentada, NAO
  re-rodar) — pode nao caber num gate estrito.
- O `camada3_gate.py._CASES` e a matrix do YAML precisam de entradas novas;
  confirmar que `make_pr_repo` lida com fixtures multi-arquivo se houver.

**Tensao a fechar:** INDET-001 produz `indeterminate` e PROBE-UNGOV produz
`not_applicable + coverage_gap` — vereditos onde o nao-determinismo do Classifier
tem mais superficie que COMP/VIOL. Aplicar o mesmo field-scoping; provavelmente
mais campos caem no advisory. Decidir K (>=2) e se o GT condicional do PROBE-UNGOV
entra como estrito ou so qualitativo.

**Disposicao de honestidade (mantida):** convergencia-sobre-K, sem re-roll;
divergencia e dado a documentar. Vale especialmente aqui, onde os vereditos sao
mais sujeitos a variancia.

## Heranca — NAO reabrir (decidido)

- `policy://examples` adiado por suficiencia medida (Passo 1).
- Unificacao `policy/` (`_seed` + instancias irmas): DECIDIDA, fora do critico.
- ADR-0015 (GDPR / `legal_framework`): pos-entrega.
- POL-007 inversao: documentada-e-nao-corrigida.
- PROBE-UNGOV-001 GT: imprecisao documentada-e-nao-corrigida (4-vs-1, nao re-rodar).
- `pipeline_e2e_raw.json` tracked: tracked-as-evidence, DECIDIDO.
- `pipeline_e2e_eval_lgpd.py` FROZEN: nao refatorar em PR de feature.
- DD-P4-2 inline comments: Future Work (Milestone D). Producao (pull_request ativo,
  posting via API, checkout de head): Milestone D.

## Debitos vivos

- **Deduplicacao `synthetic_pr.py` <- `pipeline_e2e_eval_lgpd.py:187-230`** (copias
  privadas no frozen). Chore/companion futuro (DD-P4-5). NAO no PR de feature.
- **`reason` vazio no `violation_candidate` da POL-005** (caminho de violacao do
  Matcher): possivel buraco de proveniencia. A VERIFICAR. Nao bloqueia.
- **Ruff repo-wide F401 x3** em `scripts/smoke_tests/coordinator_live/d1_readiness_gate.py`
  — pre-existente, fora do gate `src/`. Gate dos PRs foi escopado
  (`ruff check src tests scripts/ci eval/harness`), nao limpo. Cleanup separado.
- **Mypy --strict tests/:** 2 erros pre-existentes (`conftest.py:51`,
  `test_scan_diff.py:711`) — fora do gate `src/`-only.
- **Step Summaries do CI:** confirmar que as linhas RAW (redirect E1) apareceram no
  Step Summary do run 26983111920 — auditabilidade pra banca. Nao bloqueia.

## Sobre a horizonte (nao-critico, alto-ROI)

- **Relatorio TCC2:** atividade de maior ROI agora que a implementacao fechou. O
  `camada3-mvp.md` ja e rascunho de secao de resultados (multisets, estrito-vs-
  advisory, invariante de cluster, nota de metodo, DD-P4-6 agnosticismo).
- **Exame Claude Certified Architect — Foundations (jun/2026).**