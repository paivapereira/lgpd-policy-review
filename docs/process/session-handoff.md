# Session handoff — frente de avaliacao (MC-D / eval) — Passo 4

> Template-overwrite, nao patch cumulativo. Tratar como hipotese a verificar contra o repo
> (git log, leitura de arquivo), nao como estado autoritativo. Primeira acao de qualquer
> sessao Code: confirmar git state, nao assumir.

## Onde estamos

Caminho critico da frente de avaliacao: **1 -> 1.5 -> 2 -> 3 (FECHADO) -> 4 (PROXIMO, ULTIMO)**.

### Concluidos
- **Passo 1 (PR #100).** `data_categories` via `policy://vocabularies`; lista de tokens
  bastou (`policy://examples` adiado por suficiencia medida).
- **Passo 1.5 (#101, #102, ADR-0016).** Arco do Reporter (desync de proveniencia + guarda
  de wrapper).
- **Passo 2 (PR mergeada).** Harness e2e sobre os 6 PRs, root eval-lgpd, 28 runs.
  27 CONVERGENTE / 1 DIVERGENTE / 0 ERRO. DD-1 (`reporter_emit_count`) validado nos 28.
  O unico DIVERGENTE (PROBE-UNGOV-001 run 1) = imprecisao de GT por contaminacao de sonda,
  NAO bug. Adjudicado no learning-log de 2026-06-03.
- **Passo 3 (T-G3) — `rule_id` normalizado na fonte.** `_normalize_rule_id` no mapper do
  `semgrep-runner` (forma (a), `rsplit(".",1)[-1]`), espelhando `_normalize_severity`.
  Limpa a cadeia inteira (passthrough por `detector.md §3.3`). Branch `fix/g3-rule-id`,
  red-first 2 commits (`07810dd` test / `7deb9f9` fix), trio verde (pytest 284 / 1 live
  deselected, ruff, mypy --strict src/ 46 arquivos). Detalhe e adjudicacao no learning-log
  de 2026-06-04.
  - **A VERIFICAR no git:** squash hash + PR # do `fix/g3-rule-id` (mergeada via UI? `<TBD>`).
  - **A VERIFICAR no git:** nota ADR-0010 (`docs/adr-0010-checkid-mechanic`) — prompt
    autorado (`prompt-g3-adr0010-note-v1.md`), execucao/merge `<TBD>`. Se ainda nao rodou:
    o prompt manda confirmar primeiro que ADR-0010 e o lar certo (escopo = binario/execucao
    Semgrep) antes de escrever; pausa-e-pergunta se mau encaixe.

## Proximo passo: Passo 4 — Camada 3-MVP (CI minima)

GitHub Action funcional que roda o pipeline e posta o Report. Pipeline JA funciona (a
corrida e2e do Passo 2 provou coordinator + emit_report sobre os 6 PRs); Passo 4 e o
wrapping, nao impl nova.

**Escopo ratificado** (`planejamento-tcc2.md`, Camada 3-MVP): 3 PRs sinteticos
(compliant/violation/skip, matrix simples), GitHub Action funcional para esses 3, harness
Python local comparando contra `.expected-report.json`, 2 validacoes e2e completas, gate
milestone documentado QUALITATIVAMENTE (PASS/FAIL em prosa). Deferido pro Cap 3: matrix
6-8 PRs, gate quantitativo (precision/recall/F1), multi-cliente, recognizers BR completos.

**Sequencia dura:** impl do Passo 4 SO depois do Passo 3 mergeado — a Action posta o
Report e o `rule_id` nele precisa ser o limpo. Cronograma (Quadro 3): Action funcional na
banda 10-13/jun. Hoje 04/jun, ha folga.

**Primeiro movimento e inventario, nao design.** Confirmar contra o repo o que do MVP ja
existe vs. o novo: PR #99 trouxe "PRs sinteticos" + "harness 2 camadas"; `cases.yaml`
existe; cronograma lista "esqueleto GitHub Action" como em-andamento. A peca genuinamente
nova e `.github/workflows/*.yml` funcional + o que ele invoca. Confirmar tambem: interface
de entrada do coordinator (recebe base/head refs? PR number?) e o que `emit_report` faz na
ponta (escreve JSON que a Action posta, ou chama a API do GitHub?).

**DDs abertos (leans do Chat, ratificar em sessao nova):**
- DD-P4-1 trigger model. Lean: `workflow_dispatch` + matrix de 3 fixtures num run, em vez
  de `pull_request` real x3 PRs vivos. Mais barato/reproduzivel; o `pull_request` real fica
  como o que a Action faria em producao, documentado.
- DD-P4-2 inline vs summary comment. Lean MVP: summary comment com o Report estruturado
  (findings com file:line em texto); inline real (mapear posicao no diff) fica Future Work.
  Preserva a tese "Action fina".
- DD-P4-3 fronteira emit_report <-> Action. Confirmar lendo a spec/impl. Lean: emit_report
  escreve JSON, Action posta (coordinator agnostico de GitHub; Action = adaptador puro).

**Tensao load-bearing a fechar antes de codar o harness:** comparacao `.expected-report.json`
exata vs. nao-determinismo do pipeline (LLM-driven). A frente eval ja aprendeu isso —
convergencia-sobre-K, NAO match; PROBE-UNGOV 4-vs-1 foi ambiguidade legitima. Um gate de
match exato reprovaria ambiguidade legitima como falha. O harness tem que ser field-scoped
aos campos estaveis (`run_outcome`, veredito governante, set de categorias); prosa e variacao
aceitavel ficam fora; o gate qualitativo absorve o resto. Defensibilidade do capitulo depende
disso.

**Auth-em-CI:** runner headless nao faz OAuth interativo (dev local e OAuth, sem key). A
Action precisa de `ANTHROPIC_API_KEY` como GitHub secret — superficie de auth nova + custo de
tokens (5 subagentes x run). Confirmar o caminho de auth do claude-agent-sdk no runner.

**Nota de estudo (prova, fora do exercicio do projeto):** D3.6 cobra CI/CD via `claude -p`
(`--print`), `--output-format json`, `--json-schema` — o **CLI Claude Code** nao-interativo.
O projeto usa o coordinator Python+SDK, NAO o CLI. Mesmo principio (invocacao nao-interativa,
JSON estruturado, comentarios automaticos), superficie diferente. Estudar o pattern CLI
separado — construir o Passo 4 nao exercita.

## Heranca — NAO reabrir (decidido)

- `policy://examples` adiado por suficiencia medida (Passo 1).
- Unificacao `policy/` (`_seed` + instancias irmas): DECIDIDA, fora do caminho critico.
- ADR-0015 (GDPR / `legal_framework`): pos-entrega.
- POL-007 inversao: documentada-e-nao-corrigida.
- PROBE-UNGOV-001 GT: imprecisao documentada-e-nao-corrigida. Re-enquadrar GT como
  condicional no capitulo. Distribuicao 4-vs-1 fica como esta — nao re-rodar.
- `pipeline_e2e_raw.json` tracked: **tracked-as-evidence, DECIDIDO.** Espinha empirica do
  capitulo de avaliacao, nao output transitorio. NAO "consertar" com `.gitignore`.

## Debitos vivos

- **Nota ADR-0010** (`docs/adr-0010-checkid-mechanic`): status a verificar (ver acima).
- **`reason` vazio no `violation_candidate` da POL-005** (caminho de violacao do Matcher):
  possivel buraco de proveniencia. A VERIFICAR. Nao bloqueia Passo 4. Fora do T-G3 por
  no-mixed-concern.
- **Ruff repo-wide:** F401 x3 em `scripts/smoke_tests/coordinator_live/d1_readiness_gate.py`
  — pre-existente, fora do gate `src/`. Candidato a cleanup separado.
- **Mypy --strict tests/:** 2 erros pre-existentes (`conftest.py:51`, `test_scan_diff.py:711`)
  — fora do gate `src/`-only do projeto.
- **`.gitignore` do diretorio de output do eval** (runs ad-hoc futuros nao acumularem) —
  housekeeping, NAO Passo 4. Distinto da decisao tracked-as-evidence do raw canonico.