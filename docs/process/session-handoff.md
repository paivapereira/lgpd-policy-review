# Session handoff — fim do exploratório, abertura da sessão de implementação

**Data**: 2026-06-02 (revisado após review do plano pelo Code)
**Branch fechada**: `eval/test-cases-exploratory` → mergeada em `main` (squash `cac06be`, ex-PR #99). Branch deletada local + remoto.
**Próxima sessão**: implementação (frente Policy + motor), partindo de `main`.
**Restrição dominante**: ~2 semanas até a entrega. É o filtro de toda priorização.

---

## 1. Onde paramos

PR #99 mergeado em `main`. `src/` intacto, seed `policy/` preservado, gate determinístico
13/13, suíte 274, G3 live passou. Conteúdo entregue:

- Instâncias de avaliação (topologia B, **mantida** para o prazo): `policies/eval-lgpd/`
  (POL-005/006/007 + rationale) e `policies/eval-gdpr/` (gêmeo GDPR).
- Evaluator `eval/`: `cases.yaml`, `harness/run_engine_cases.py` (gate 13/13 + Reports
  consolidados 10/10 válidos), PRs sintéticos, POL-008 staged fora do catálogo.
- Docs: `test-cases-proposal.md`, `pol-007-inversao-sensibilidade.md`, ADR-0015 (Proposed).

**Nenhuma ação pré-merge pendente** — a correção da §6(b) do doc POL-007 já entrou
(commit `a2ff560`, dentro do squash); o footer robô era do corpo do PR, sumiu no squash.
(Itens que constavam como pendentes no rascunho anterior do handoff estavam stale.)

Pendentes de commit direto em `main` (teus artefatos de sessão): este handoff e a
entrada de learning-log de 2026-06-02.

---

## 2. Decisoes tomadas (nao reabrir)

- **Unificacao `policy/` unica** (`_seed` + instancias irmas) esta **decidida**, mas
  **fora do caminho critico das 2 semanas** — ver secao 4 e 5. Plano de execucao completo
  ja escrito e auditado (blast radius de 6 loci funcionais mapeado); fica na gaveta para
  pos-entregaveis.
- ADR-0015 sera implementado (inclui GDPR / `legal_framework`) — pos caminho critico.
- Inversao POL-007 fica **documentada, nao corrigida** (documento pronto). Trabalho de
  redacao, ja feito.
- CI minima (pipeline num PR posta Report), nao robusta.
- Classifier `[]` tem causa **estrutural**: `get_vocabularies` omite `data_categories` e
  `policy://examples` nao existe. Nao e bug do modelo.
- `policy://examples` (item 7) e **condicional** ao resultado do discriminante do Passo 1
  (measure-before-tune).

---

## 3. Lista completa de pendencias (priorizada)

P0 = bloqueia tudo; P1 = necessario p/ relatorio; P2 = melhora; P3 = pos-TCC.
**[critico]** = no caminho das 2 semanas.

| # | Pendencia | Serve | Prio | Caminho critico? |
|---|---|---|---|---|
| 1 | Expor `data_categories` ao Classifier + discriminante | Funcionar | P0 | **sim — Passo 1** |
| — | Harness live sobre `eval-lgpd` (Reports de pipeline real) | Avaliacao | P1 | **sim — Passo 2** |
| 6 | `rule_id` poluido (normalizar `check_id` no mapper do semgrep-runner) | Avaliacao | P1 | **sim — Passo 3** |
| — | CI minima (pipeline num PR, posta Report) | CI | P2 | **sim — Passo 4** |
| 3 | Inversao POL-007 | Avaliacao | P1 (redacao) | feito (documento) |
| 7 | `policy://examples` completo (PR autonomo + amendment ADR-0005 D9 + seed >=2 LGPD + SCHEMA secao 2) | Funcionar | P1 condicional | so se Passo 1 desfecho (c) |
| 2 | Unificar `policy/` unica (`_seed`+instancias) + fallback loader | Funcionar/clareza | P2 | **NAO — pos-entregaveis** (plano pronto) |
| 8 | Correcoes juridicas: POL-006 (Art.12 par.2 -> Art.6 III), POL-005 (marketing) | Avaliacao | P2 | se tocar as clausulas (ver nota Passo 2) |
| 4 | `legal_framework: Literal["LGPD"]` -> validar contra `accepted_law_identifiers` | Avaliacao | P2 | se sobrar tempo |
| 5 | Token `consent` hardcoded ao LGPD no motor | — | P3 | pos-TCC (limite documentado) |
| 9 | Mover `scripts/`->`tests/`, deletar `scripts/` | Higiene | P3 | pos-TCC |

**Mudancas vs rascunho anterior** (pos-review do Code, verificadas em arquivo):
- **Passo 6 reescopado**: o `rule_id` poluido NAO e falta de `id:` nas regras
  (`br_cpf.yaml:2` ja tem `id: br-cpf`). E o Semgrep prefixar o namespace pelo caminho do
  config apesar do `id`. Fix real = normalizar `check_id` no mapper de saida do
  `semgrep-runner` (`_semgrep_output.py`; ex. `rule_id = check_id.rsplit(".",1)[-1]`), nao
  nas regras YAML.
- **Item 2 (unificacao) saiu do caminho critico**: blast radius maior que o estimado
  (6 loci funcionais, incl. 3 fixtures `conftest.py` que `copytree(REAL_POLICY)`),
  zero payload funcional para os entregaveis (harness live e CI so apontam
  `POLICY_READER_ROOT`, nao ligam se e `policies/` ou `policy/`). Alto risco de regressao
  + zero payload no caminho critico contraria o filtro de prazo. Adiada, plano pronto.

---

## 4. Plano de acao (caminho critico) — 1 -> harness live -> rule_id -> CI minima

Tudo roda sobre `policies/eval-lgpd/` (topologia B atual). Cada passo e uma tarefa de
Code separada (prep Chat -> prompt ratificado -> GATE 1 plan-mode -> execucao -> review de
diff -> merge). PR e teu; Code nao abre PR.

### Passo 1 — Expor `data_categories` ao Classifier + medir (P0, gargalo)

**O que**: `get_vocabularies` (policy-reader, ~`tools.py:117`/`server.py:96`) retorna so os
4 vocabularios jurisdicionais e **omite `data_categories`** (que existe via
`_load_data_categories_vocabulary(state)`, derivado do POL-000). O Classifier e instruido
a classificar com o vocabulario de categorias que nunca lhe e exposto -> devolve `[]` ->
pipeline cai em `not_applicable`/POL-000 (provado no G3).

**Por que primeiro**: gargalo dos tres objetivos. Sem categoria, nenhum caso produz
veredito substantivo no pipeline real — nada para avaliar nem mostrar na CI. Mais barato:
expor vocabulario que ja existe.

**Como**: adicionar `data_categories` ao retorno de `get_vocabularies`. **Nuance de camada
a levantar (nao decidir sozinho)**: categorias sao ESTRUTURAIS (POL-000, framework-neutral,
ADR-0005 D3), diferentes dos 4 vocabs jurisdicionais; expo-las em `policy://vocabularies`
mistura levemente as camadas. Propor onde expor (mesmo dict / chave separada / resource
proprio) com trade-off, para ratificacao. Confirmar tambem se o prompt do Classifier
aponta para o URI certo — se ele tenta ler `policy://examples` (inexistente), o ajuste do
prompt entra no escopo.

**Discriminante (versao forte — nao a ingenua)**: medir se expor a LISTA basta ou se falta
DEMONSTRACAO (few-shot). Exigencias:
- Barra de sucesso = classificacao **CORRETA**, nao so nao-vazia. Distinguir 4 desfechos:
  correto / abstem `[]` / **errado (categoria alucinada)** / inconsistente entre runs.
- **NAO testar so com `cpf`** — e o caso facil (o nome do campo E o token canonico
  POL-000 secao 2.2). Incluir >=1 caso de **inferencia nao-literal** (ex. campo de
  rastreamento->`perfil_comportamental`, campo clinico cujo nome nao seja "saude"->`saude`).
  Esse e o caso que de fato discrimina "lista basta" de "precisa de examples".
- Matriz minima: (1) cpf nu (baseline pobre do G3); (2) cpf em model rico; (3) >=1 inferencia
  nao-literal. Cada um com ground truth.
- Veiculo: nao ha harness de Classifier live isolado (os 3 `tests/.../classifier/*` sao
  unit estruturais). Propor veiculo: invocacao live one-off OU piggyback no pipeline (~2
  min/run).
- Nao-determinacao: rodar os casos de fronteira mais de uma vez, reportar consistencia.

**Desfechos e o que cada um decide**:
- (a) classifica os dois literais E o nao-literal -> lista basta; item 7 dispensado.
- (b) classifica rico, abstem no pobre -> input pobre era a causa; sistema sao (positivo).
- (c) abstem/erra no nao-literal mesmo com a lista -> falta demonstracao -> item 7 entra.

**Contingencia (c)**: se item 7 (`policy://examples` completo) for grande demais p/ 2
semanas, stopgap = few-shot minimo de mapeamento de categoria no prompt do Classifier
(aceita quebrar independencia de camada **temporariamente**, documentado como divida) — p/
um (c) nao afundar o prazo.

**Saida**: Classifier classificando; veredito sobre item 7.

### Passo 2 — Harness live sobre `eval-lgpd` (P1, coracao da avaliacao)

**O que**: adaptar o padrao do `test_g3_live_e2e.py` (que ja roda o pipeline real
ponta-a-ponta) p/ rodar sobre os PRs sinteticos, apontando
`POLICY_READER_ROOT=policies/eval-lgpd` (oposto do G3, que limpa a env var p/ usar o seed).
Capturar os Reports reais.

**Por que e o coracao**: os 10 Reports atuais sao do harness DETERMINISTICO (so motor,
categorias injetadas a mao). O capitulo de avaliacao de um sistema multi-agente precisa de
Reports onde Triager/Detector/Classifier **rodaram de fato**. Este passo produz isso — e
mede a taxa de acerto real do Classifier.

**Depende de**: Passo 1 (senao Classifier devolve `[]`). Ambiente ja confirmado pronto
(G3 passou). Insumo pronto: `_make_cpf_repo` do G3 mostra como virar arquivos soltos em
commits git que `scan_diff` consome; os `eval/prs/*` precisam desse tratamento e possivel
enriquecimento (campos nomeados, nao params nus) conforme o discriminante do Passo 1.

**Nota (decisao da sessao)**: se for tocar as clausulas eval-lgpd aqui, considerar dobrar
as correcoes juridicas do item 8 (POL-006 re-ancorar Art.12 par.2 -> Art.6 III; POL-005
estreitar p/ marketing) — barato e evita um passe extra. POL-006 tem erro juridico
afirmativo que um avaliador de Direito pega.

**Nao-determinacao dos Reports live**: Classifier/Matcher sao LLMs; o mesmo PR pode variar
entre runs. Planejar execucoes multiplas/representativas e DECLARAR a nao-determinacao no
capitulo. Os 10 deterministicos ficam como baseline do motor; os live mostram a realidade
multi-agente.

**Saida**: Reports de pipeline real sobre eval-lgpd — material empirico do capitulo.

### Passo 3 — Normalizar `rule_id` (P1, estetico mas vaza path)

**O que**: no G3 o `rule_id` veio `C.Users.joaoguilherm...rules.br-cpf` — o Semgrep
prefixa o namespace pelo caminho do config **apesar** do `id: br-cpf` explicito na regra.
Propaga verbatim ate o Report final (correto como passthrough, mas vaza teu path de usuario
no laudo).

**Como (reescopado)**: NAO mexer nas regras YAML (ja tem `id`). Normalizar o `check_id` no
mapper de saida do `semgrep-runner` (`_semgrep_output.py` parseia `check_id`; o mapper p/
`Finding.rule_id` passa verbatim) — ex. `rule_id = check_id.rsplit(".",1)[-1]`. Locus =
`semgrep_runner`, nao `rules/`. Pequeno.

**Por que depois do harness live**: cosmetico, mas os Reports "oficiais" do relatorio nao
podem sair com teu home dir dentro. Re-rodar o harness live depois p/ regenerar Reports
limpos.

**Saida**: `rule_id` = `br-cpf` limpo nos Reports.

### Passo 4 — CI minima (P2, objetivo 2)

**O que**: Action que, num PR, roda o pipeline e posta o Report como comentario. Minima,
nao robusta (sem matriz/retry/otimizacao).

**Por que por ultimo**: depende de tudo acima (pipeline com veredito real, Reports limpos).
Demonstravel como "integracao CI realizada" mesmo minima. CI robusta = trabalho futuro
documentado.

**Cuidado de ambiente**: precisa de sessao Claude autenticada (secret de repo) + semgrep no
runner. `test_g3` documenta os pre-requisitos; a Action replica (auth via secret, semgrep
via step de install).

**Saida**: PR de demonstracao com Report postado automaticamente — evidencia do objetivo 2.

---

## 5. Trabalho pos-entregaveis (plano pronto, fora das 2 semanas)

- **Unificacao `policy/` unica** (item 2). Plano completo ja escrito e auditado: move seed
  p/ `policy/_seed/`, instancias p/ `policy/eval-*/`, elimina `policies/`, muda fallback do
  loader (`<repo>/policy`->`<repo>/policy/_seed`). Blast radius = 6 loci funcionais
  (`loader.py:63`, `conftest.py:15` REAL_POLICY + 3 fixtures copytree,
  `test_bootstrap.py:82`, `test_find_clauses.py:29`, `run_engine_cases.py` LGPD/GDPR_ROOT,
  `probe.py:29`) + ~8 docs/comentarios (por-ocorrencia: seed->`_seed/`, SCHEMA fica no topo,
  instancias->`policy/eval-*`). `SCHEMA.md` no topo (nao move); secoes 2/10 ficam stale ->
  follow-up. Executar quando um teste vermelho nao for existencial.
- **ADR-0015** (gate de sensibilidade que corrigiria POL-007; `legal_framework`; etc.).
- **Itens 4, 5, 9**: P2/P3, se sobrar tempo ou pos-TCC.

---

## 6. Notas de metodo (preservar entre sessoes)

- **Verificacao antes de inferencia**: nesta sessao o Chat errou 3x por inferir estrutura
  de arquivo sem ler — secao 6(b) do doc POL-007 (token `explicit_consent` que "faltava" ja
  existia), o fix do `rule_id` (regras "sem `id`" ja tinham `id`), e o blast radius da
  unificacao (3 loci estimados, 6 reais). As 3 foram pegas pelo Code lendo os arquivos.
  Regra: no Chat, marcar explicitamente "nao li, e hipotese" ao afirmar estrutura; o Code
  verifica antes de executar.
- **Measure-before-tune**: item 7 so se o discriminante do Passo 1 (com caso nao-literal)
  provar que a lista nao basta. Nao construir a peca cara por suposicao.
- **Nao misturar naturezas de tarefa**: consertar input vs medir pipeline sao separados.
- **PR e teu, Code nao abre PR.**
- **Documentar limite > corrigir mal sob prazo** (POL-007).
- **Boa decisao != fazer agora**: a unificacao `policy/` e decisao boa e plano solido, mas
  zero payload funcional + alto blast radius = fora do caminho critico. Sequenciar onde o
  risco e absorvivel, nao abandonar.

---

## 7. Primeiro passo concreto da proxima sessao

Abrir o prompt do **Passo 1** (ja redigido no Chat): expor `data_categories` em
`get_vocabularies` + experimento discriminante forte (barra = correto; incluir caso de
inferencia nao-literal; veiculo de medicao; nao-determinacao). Plan-mode, para ratificacao.
Resultado decide se o item 7 entra nas 2 semanas. Tudo sobre `policies/eval-lgpd/` — sem
tocar a estrutura de pastas.