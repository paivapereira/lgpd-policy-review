# Session handoff — Reporter confiavel, abertura do Passo 2 proper

**Data**: 2026-06-03 (pos-merge de #101, #102; PR docs/ratify-adr-0016 pendente de merge)
**Estado**: arco Reporter fechado e em `main`. Proximo: Passo 2 (rodar o harness live).
**Restricao dominante**: ~2 semanas ate a entrega. Filtro de toda priorizacao.

---

## 1. Onde paramos

O smoke de validacao do harness do Passo 2 expos dois bugs no estagio de saida
(Reporter) que tres camadas de teste anteriores mascaravam. Ambos diagnosticados,
corrigidos, e confirmados por medicao. O Reporter agora produz Reports de pipeline
real de forma confiavel — o que destrava o Passo 2.

- **(a) desync de proveniencia — PR #101 (`main`).** O estado consolidado chegava ao
  Reporter inconsistente: top-level policy_version=0.1.0 (default de parametro em
  run_pipeline) vs per-finding 0.2.0 (header eval-lgpd echoado nos findings). O
  cross-check rejeitava a 1a emissao; o prompt mandava retry; a guarda matava a 2a.
  Determinístico (5/5 no caminho substantivo). Correcao: derivar a proveniencia
  top-level dos FINDINGS (conformidade com reporter.md:377). Confirmado: 0/5
  PROVENANCE_MISMATCH live.
- **(c) guarda conta sucessos — PR #102 / ADR-0016 (`main`).** Halt residual pos-(a)
  de 2/5 por WRAPPER de tool-argument (modelo emite {"report": "<string>"} -> falha ->
  auto-corrige -> 2a valida; guarda estrangulava o retry). Correcao: guarda conta
  emissoes BEM-SUCEDIDAS (sinal de disco 99-report.json), nao tentativas; rede de
  seguranca ReportNotEmitted para o caso latente sem Report committed. Confirmado:
  halt 2/5 -> 0/5; recuperacao do wrapper observada direta (emits=2 -> Report) nos runs
  3 e 5; Reports recuperados identicos e convergentes com GT.
- **ADR-0016 ratificado (Accepted)** com o antes-e-depois do smoke. **Pendencia: merge
  do PR docs/ratify-adr-0016** (3 commits: ADR Accepted + doc cpf §7 + harness do Passo
  2 versionado). Unico item aberto antes do Passo 2.

---

## 2. Decisoes tomadas (nao reabrir)

- **(a) deriva dos findings, nao header-read** (coordinator nao carrega a Politica;
  fronteira MCP). Params = fallback para caminhos sem-findings. Cross-check intocado
  (e o detector, nao o bug).
- **(c) Forma 2 (sinal de disco 99-report.json) sobre Forma 1 (correlacao no stream).**
  Forma 1 e o alvo "mais limpo" mas depende de o query() surfacear o tool-result do
  @tool (nao-verificado; bridge dropa structuredContent). Forma 1 registrada no ADR
  como alternativa considerada-e-preterida (caminho de desacoplamento atras de smoke),
  NAO obrigacao.
- **(c) refina a invariante, nao a enfraquece**: "uma emissao" -> "uma emissao
  bem-sucedida"; a invariante real (um Report committed) preservada. Redundancia
  genuina (2 sucessos) e max_turns continuam halts honestos.
- **Debito single-emit silent-success: deferido.** Coberto pelo ReportNotEmitted (halt
  honesto), nao observado em 10 runs. Vira investigacao propria se aparecer no Passo 2.
- **Debito sem-findings (proveniencia top-level estale nos caminhos skipped/no-candidates):
  registrado em tasks.md, inocuo** (cross-check vacuamente satisfeito, nao halta).
  Conformidade total exigiria o coordinator ler o header via MCP — follow-up fora de
  escopo.
- **doc cpf §7 (isolado-vs-composto): registrado.** Contexto altera a classificacao;
  nao ha preferencia fixa do modelo. Reforça a licao "escopar conclusoes as condicoes
  medidas — incluindo o contexto".
- Heranca do Passo 1 (nao reabrir): policy://examples adiado por suficiencia medida;
  unificacao policy/ DECIDIDA mas fora do caminho critico; ADR-0015 pos-entrega;
  inversao POL-007 documentada-nao-corrigida; CI minima.

---

## 3. Caminho critico revisado

Tudo sobre `policies/eval-lgpd/`. Cada passo = tarefa de Code separada (prep Chat ->
prompt ratificado -> GATE 1 plan-mode -> execucao -> review de diff -> merge). PR e do
Joao; Code nao abre PR.

| Passo | Pendencia | Estado |
|---|---|---|
| 1 | Expor data_categories + discriminante | CONCLUIDO (PR #100) |
| 1.5 | Arco Reporter (desync + wrapper) — NAO planejado, surgiu do smoke | CONCLUIDO (#101, #102, ADR-0016) |
| 2 | Harness live sobre eval-lgpd (Reports de pipeline real, tabela CONVERGENTE/DIVERGENTE) | **proximo** |
| 3 | Normalizar rule_id (check_id no mapper do semgrep-runner) | apos 2 |
| 4 | CI minima (pipeline num PR posta Report) | por ultimo |

Pos-entregaveis / se sobrar: unificacao policy/ (plano pronto), ADR-0015, correcoes
juridicas item 8, debito single-emit, debito sem-findings.

---

## 4. Passo 2 — Harness live (proximo, coracao da avaliacao)

**O que**: rodar `eval/experiments/pipeline_e2e_eval_lgpd.py` (ja versionado, ruff/mypy
limpos) sobre os 6 PRs sinteticos de `eval/prs/` apontando
`POLICY_READER_ROOT=policies/eval-lgpd`, capturando os Reports reais + o trace por
estagio, e tabulando CONVERGENTE/DIVERGENTE vs o GT de `eval/cases.yaml`. Medicao, nao
pass/fail — GT e expectativa do projeto, nao gabarito vinculante; divergencia =
investigar, nao "errado".

**Por que e o coracao**: os Reports deterministicos sao do motor (categorias injetadas).
O capitulo de um sistema multi-agente precisa de Reports onde Triager/Detector/
Classifier/Matcher/Reporter rodaram de fato. Este passo produz isso + mede o acerto real
do Classifier sobre PRs reais.

**Pre-condicoes (todas satisfeitas agora)**: Classifier classifica (Passo 1); pipeline
produz Reports confiaveis (arco Reporter); harness versionado e limpo; 6 PRs em
eval/prs/ (COMP-001, VIOL-001, INDET-001, PROBE-UNGOV-001, SWAP-001, SKIP-001).

**Mecanica do harness (verificar no proprio arquivo antes do prompt; nao inferir)**: o
harness expoe `_matrix()` (enumera os casos) e `_run_one_pipeline(case, idx)` (constroi
repo de base-vazia -> chdir -> run_pipeline -> le scratchpad). Cada run live ~200s. A
conta K x 6 PRs decide foreground vs background (os diagnosticos do arco rodaram K=5 de
1 PR em background, ~15 min; 6 PRs x K vai ser bem maior — planejar background com leitura
de progresso). Helpers reutilizaveis: `_make_pr_repo`, `_write_project_mcp_json`,
`_read_stage_trace`. Os diagnosticos do arco instrumentaram smoke-only envolvendo
`coordinator.run.query` para contar emits do Reporter — reusavel para capturar
`reporter_emit_count` por run (distingue recuperacao de wrapper de single-shot na tabela).

**GT por PR (de eval/cases.yaml — confirmar la, mapa de conveniencia aqui)**: COMP-001 ->
POL-005 compliant; VIOL-001 -> POL-005 violation_candidate; INDET-001 -> POL-006
indeterminate; PROBE-UNGOV-001 -> coverage_gap (sweep); SWAP-001 -> POL-005 compliant
(LGPD-redundante); SKIP-001 -> triager_skip. Cuidado R6: o GT do cpf aceita ambos
identificacao E documentos_oficiais.

**Tres decisoes de desenho a fechar no Chat ANTES do prompt** (seguem abertas do handoff
anterior; o arco Reporter nao as tocou):
1. **K execucoes por PR**: pipeline live e nao-deterministico (Classifier/Matcher LLMs)
   + falha de transporte ocasional (~1/42). Decidir K e como reportar (distribuicao?
   Report representativo? todos?). Nota nova do arco: o wrapper agora RECUPERA (nao
   halta), mas emits=2 ainda acontece ~2/5 — vale capturar reporter_emit_count por run
   para distinguir recuperacao de single-shot na tabela.
2. **Enriquecimento dos PRs**: campo nomeado vs param nu importa para a classificacao
   (Passo 1) E o contexto altera a classificacao (doc cpf §7). Decidir se os eval/prs/*
   rodam como estao ou precisam de campos nomeados. A §7 sugere que rodar AS-IS ja
   produz variacao interessante (o cpf deu categorias diferentes por contexto).
3. **Dobrar correcoes juridicas (item 8)?**: se for tocar as clausulas eval-lgpd,
   considerar POL-006 (re-ancorar Art.12§2 -> Art.6 III) e POL-005 (estreitar para
   marketing). Barato se ja editando; evita passe extra.

**Nao-determinacao**: planejar K representativas e DECLARAR no capitulo. Os
deterministicos sao baseline do motor; os live mostram a realidade multi-agente. O arco
Reporter e, ele proprio, material de capitulo (avaliacao de composicao expondo o que
unidade nao pega).

**Investigar divergencia (metodo, quando aparecer)**: divergencia nao e "errado" — e
sinal de investigar. Ler o trace por estagio (o harness captura 01-triager..04-matcher +
o Report), isolar o estagio de ORIGEM (o Classifier emitiu categoria diferente? o Matcher
casou clausula diferente? o GT esta mal-calibrado?), e classificar antes de concluir:
instabilidade do modelo (varia entre runs — e dado, declarar) vs bug (corrigir, passo
proprio) vs GT a recalibrar (a expectativa do projeto estava errada). A §7 do doc cpf e
um exemplo ja vivido: a divergencia isolado-vs-composto era resposta-a-contexto do modelo,
nao bug.

**Saida**: tabela CONVERGENTE/DIVERGENTE + Reports reais sobre eval-lgpd. Chat le; sem
conclusao no harness.

---

## 5. Notas de metodo (preservar entre sessoes)

- **Verificacao antes de inferencia**: o Chat inclina, o Code verifica lendo. Esta
  sessao: (a) framing corrigido (findings, nao header); Forma 1 tinha buraco de SDK que
  so a leitura achou; a coluna 99-report era o mecanismo, nao "sinal extra". Marcar "nao
  li, e hipotese" ao afirmar estrutura.
- **Caminho de erro nao admite frouxidao**: a rede de seguranca do pos-loop foi fechada
  ANTES de implementar (recusado "a finalizar na impl"). Halt honesto > sucesso
  silencioso falso.
- **Guarda que dispara nao e o bug**: a inconsistencia que ela pega esta a montante.
  Verificar a fonte antes de culpar o detector.
- **Measure-before-tune / honest measurement**: a reordenacao de (c) veio do dado (40%),
  nao de palpite. Erro de transporte e dado; inconsistencia entre runs e dado; nao
  re-rodar para limpar.
- **Avaliacao de composicao != soma de avaliacoes de estagio**: o desync so apareceu no
  pipeline live x Politica != default. Defense candidate.
- **PR e do Joao; Code nao abre PR.** Boa decisao != fazer agora (unificacao policy/
  segue fora do caminho).
- **docs/process e territorio do Joao**; learning-log append-only; handoff
  overwrite-per-session.
- **Ruido conhecido no git status**: `.claude/settings.json` aparece como `M`
  (gitignored mas rastreado — o gerenciamento de permissoes do Code o toca). Ignorar; e
  ruido, nao mudanca relevante. Housekeeping futuro: `git rm --cached .claude/settings.json`
  para o status parar de mostra-lo.

---

## 5b. Pendencia de provenance (fazer ANTES do %TEMP% limpar)

Os dados crus do arco Reporter (diagnosticos pre-(c), smoke pos-(a), diagnostico pos-(a),
smoke de confirmacao pos-(c)) estao em `%TEMP%` — NAO versionados, somem quando o temp
limpa. A evidencia narrativa esta no ADR-0016 (numeros no texto), mas os dados crus que a
sustentam nao. Para o capitulo ter provenance citavel (como o Passo 1 tem o
`discriminant_raw.json` versionado em `eval/experiments/output/`):

- Salvar pelo menos `%TEMP%\_smoke_confirm_c_runs.json` (prova (c) end-to-end: 0/5 halt,
  runs 3 e 5 com emits=2 recuperados) em `eval/experiments/output/`, versionado.
- Idealmente tambem os JSONs dos dois diagnosticos de 5 runs (o pre-(c) com o 2/5 e o
  pos-(c)). Se ja sumiram do temp, re-medir e barato (~15 min cada) e o ADR documenta o
  esperado.
- Pode ir junto com o primeiro PR do Passo 2 (dados de avaliacao) ou housekeeping proprio.

---

## 6. Primeiro passo concreto da proxima sessao

Mergear o PR docs/ratify-adr-0016 (fecha o arco em main). Salvar os dados crus do arco
(§5b) antes que o %TEMP% limpe — barato agora, impossivel recuperar depois. Depois, sessao
Chat NOVA (marco de fase + esta acumulou todo o arco de diagnostico): fechar as tres
decisoes de desenho do Passo 2 (K, enriquecimento, item 8), depois redigir o prompt do
harness live. Plan-mode, ratificacao. Tudo sobre policies/eval-lgpd.