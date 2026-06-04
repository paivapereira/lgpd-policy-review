# Session handoff — frente de avaliacao (MC-D / eval)

> Template-overwrite, nao patch cumulativo. Tratar como hipotese a verificar contra o repo
> (git log, leitura de arquivo), nao como estado autoritativo. Primeira acao de qualquer
> sessao Code: confirmar git state, nao assumir.

## Onde estamos

Caminho critico da frente de avaliacao: **1 -> 1.5 -> 2 (FECHADO) -> 3 (PROXIMO) -> 4**.

### Concluidos
- **Passo 1 (PR #100).** Exposto `data_categories` via `policy://vocabularies`; experimento
  discriminante (names-only vs names+examples, 5 casos). Lista de tokens bastou ->
  `policy://examples` adiado por suficiencia medida (nao refutado em geral).
- **Passo 1.5 (#101, #102, ADR-0016).** Arco do Reporter (desync de proveniencia + guarda de
  wrapper que conta sucessos). Nao planejado; emergiu do smoke do Passo 2.
- **Passo 2 (corrida live — branch `feat/eval-emit-count` @ d297187, PR a abrir pela UI).**
  Harness e2e sobre os 6 PRs, root eval-lgpd, 28 runs. **27 CONVERGENTE / 1 DIVERGENTE / 0 ERRO.**
  Detalhe e adjudicacao na entrada do learning-log de 2026-06-03.
  - DD-1 (`reporter_emit_count`) validado nos 28: 24 single / 4 recovery / 0 halt / 0 None.
    Valida ADR-0016 fix (c) ao vivo. Hold do PR liberado.
  - O unico DIVERGENTE (PROBE-UNGOV-001 run 1) = imprecisao de GT por contaminacao de sonda,
    NAO bug do Matcher. Documentado, nao corrigido (ver "heranca").

## Proximo passo: Passo 3 — normalizar `rule_id`

Edicao de `src/` (mapper do `semgrep-runner`, campo `check_id`): hoje o `rule_id` chega ao Report
final como path absoluto da maquina
(`C.Users.joaoguilherm.pereira.dev.lgpd-policy-review.mcp_servers.semgrep_runner.rules.br-cpf`);
deve ficar so `br-cpf`. **Confirmado presente nos Reports live do Passo 2** (nao so no trace do
Detector). PR proprio, red-first (anchor que captura o id poluido falhando, depois o fix), hermetico.
Tocar so o mapper; nao reabrir o harness congelado.

Depois: **Passo 4** — CI minima (pipeline num PR posta Report). Por ultimo.

## Heranca — NAO reabrir (decidido)

- `policy://examples` adiado por suficiencia medida (Passo 1).
- Unificacao `policy/` (`_seed` + instancias irmas): DECIDIDA, mas **fora do caminho critico**.
- ADR-0015 (GDPR / `legal_framework`): pos-entrega.
- POL-007 inversao: documentada-e-nao-corrigida.
- **PROBE-UNGOV-001 GT (novo):** imprecisao documentada-e-nao-corrigida. A sonda usa br-cpf como
  gatilho, e cpf e categoria condicionalmente governada -> coverage_gap so vale se o cpf resolver
  para documentos_oficiais. Re-enquadrar GT como condicional no capitulo. **Distribuicao 4-vs-1
  fica como esta — nao re-rodar, nao "consertar" (seria ajuste-de-input proibido).**
- CI minima e o Passo 4, nao antes.

## Debitos vivos

- **DD-1 PR a abrir:** `feat/eval-emit-count` @ d297187, harness-only (+71/-2). Abrir pela UI;
  NAO levar o `M .claude/settings.json` solto junto.
- `reason` vazio no finding `violation_candidate` da POL-005 (run 1 PROBE) — possivel buraco de
  proveniencia no caminho de violacao do Matcher. **A VERIFICAR** (nao bloqueia Passo 3).
- single-emit silent-success: coberto por `ReportNotEmitted`; agora com evidencia viva (0 halts
  em 28). Vira investigacao propria so se reaparecer.
- sem-findings: proveniencia top-level estale nos caminhos skipped; inocuo; em `tasks.md`.
- doc cpf §7: estendido pelo achado de consequencia-de-veredito-a-jusante do Passo 2.
- COMP-001 sobre-inclui `dados_de_autenticacao` as vezes; sem efeito de veredito; anotado.

## Artefatos do Passo 2

- `eval/experiments/output/pipeline_e2e_raw.json` (28 runs, 261 KB, trace por estagio +
  report_payload por run) — untracked; decidir commit/descartar na escrita do capitulo.
- `eval/experiments/output/pipeline_e2e_run.log` (UTF-8 limpo) — gitignored.
- Trio verde: ruff / mypy (src 46 + eval tipado, zero supressoes) / pytest 278 passed.