# Session handoff — Passo 1 concluido, abertura do Passo 2

**Data**: 2026-06-02 (pos-merge do PR #100)
**Estado**: Passo 1 fechado e em `main`. Proximo: Passo 2 (harness live).
**Restricao dominante**: ~2 semanas ate a entrega. Filtro de toda priorizacao.

---

## 1. Onde paramos

PR #100 mergeado em `main` (`feat/expose-data-categories-vocab`, 4 commits):
exposicao de `data_categories` (Opcao B), experimento discriminante + dados crus,
nota de debito R5, documento de avaliacao do cpf. O Classifier agora classifica
(gargalo do Passo 1 resolvido). Trio gate 276 passed; MCP Inspector smoke
confirma names-only default-off; experimento live 42 chamadas.

**Pendencia leve (nao bloqueia)**: a linha de status do
`docs/eval/cpf-exposicao-categorias-suficiencia.md` diz "PR e merge pendentes" —
desatualizada agora que #100 mergeou. Correcao de uma linha; pode ir junto com o
proximo trabalho ou num housekeeping direto em main. Nao vale branch propria.

---

## 2. Decisoes tomadas (nao reabrir)

- **policy://examples (item 7) ADIADO do escopo das 2 semanas** — por suficiencia
  medida (a lista bastou nos casos testados), NAO refutado em geral. Residuo nao
  testado: categorias sensiveis (saude/biometricos, evitadas por causa do POL-007),
  tokens idiossincraticos, Politicas futuras menos transparentes. Disponivel se o
  residuo aparecer; nao construir agora.
- Exposicao via Opcao B (boundary, framework omitido, names-only default).
- R5 (emenda ADR-0005 + arch-overview §5.4) = nota de debito, consolidar com
  futura decisao de policy://examples. Nao redigir a frio.
- R6: ground truth do cpf aceita ambos (identificacao E documentos_oficiais).
- **Unificacao `policy/` unica** segue DECIDIDA mas FORA do caminho critico
  (plano completo na gaveta, blast radius de 6 loci mapeado). Pos-entregaveis.
- ADR-0015 (gate de sensibilidade / GDPR) — pos caminho critico.
- Inversao POL-007 — documentada, nao corrigida (doc pronto em docs/eval/).
- CI minima, nao robusta.

---

## 3. Caminho critico revisado (item 7 fora)

Tudo sobre `policies/eval-lgpd/`. Cada passo = tarefa de Code separada
(prep Chat -> prompt ratificado -> GATE 1 plan-mode -> execucao -> review de diff
-> merge). PR e do Joao; Code nao abre PR.

| Passo | Pendencia | Estado |
|---|---|---|
| 1 | Expor data_categories + discriminante | **CONCLUIDO (PR #100)** |
| 2 | Harness live sobre eval-lgpd (Reports de pipeline real) | **proximo** |
| 3 | Normalizar rule_id (check_id no mapper do semgrep-runner) | apos 2 |
| 4 | CI minima (pipeline num PR posta Report) | por ultimo |

Pos-entregaveis / se sobrar: unificacao policy/ (plano pronto), ADR-0015,
correcoes juridicas item 8, itens 4/5/9 do backlog antigo.

---

## 4. Passo 2 — Harness live sobre eval-lgpd (proximo, coracao da avaliacao)

**O que**: adaptar o padrao do `test_g3_live_e2e.py` (pipeline real ponta-a-ponta)
para rodar sobre os PRs sinteticos, apontando `POLICY_READER_ROOT=policies/eval-lgpd`
(oposto do G3, que limpa a env var para usar o seed). Capturar os Reports reais.

**Por que e o coracao**: os 10 Reports atuais sao do harness DETERMINISTICO (so
motor, categorias injetadas a mao). O capitulo de avaliacao de um sistema
multi-agente precisa de Reports onde Triager/Detector/Classifier rodaram de fato.
Este passo produz isso — e mede a taxa de acerto real do Classifier sobre PRs
reais (dado mais forte que os fixtures controlados do experimento).

**Pre-condicoes (todas satisfeitas)**: Classifier classifica (Passo 1); ambiente
live roda (G3 passou); `_make_cpf_repo` do G3 mostra como virar arquivos soltos
em commits git que `scan_diff` consome; padrao de fixture de preocupacao-unica do
experimento disponivel para reaproveitar.

**Tres decisoes de desenho a fechar no Chat ANTES do prompt** (nenhuma trivial):
1. **K execucoes por PR**: o pipeline live e nao-deterministico (Classifier/Matcher
   sao LLMs) E tem falha de transporte ocasional (~1/42 observada no experimento).
   Um Report unico por PR nao representa. Decidir K e como reportar
   (distribuicao? Report representativo? todos?).
2. **Enriquecimento dos PRs sinteticos**: o experimento mostrou que campo nomeado
   vs param nu importa para a classificacao. Decidir se os `eval/prs/*` precisam de
   campos nomeados (nao params nus) antes de rodar, ou se rodam como estao.
3. **Dobrar correcoes juridicas (item 8)?**: se for tocar as clausulas eval-lgpd
   de qualquer jeito, considerar dobrar POL-006 (re-ancorar Art.12§2 -> Art.6 III;
   erro juridico afirmativo que um avaliador de Direito pega) e POL-005 (estreitar
   para marketing). Barato se ja se esta editando as clausulas; evita um passe extra.

**Nao-determinacao dos Reports live**: planejar K execucoes representativas e
DECLARAR a nao-determinacao no capitulo. Os 10 deterministicos ficam como baseline
do motor; os live mostram a realidade multi-agente.

**Saida**: Reports de pipeline real sobre eval-lgpd — material empirico do capitulo.

---

## 5. Notas de metodo (preservar entre sessoes)

- **Verificacao antes de inferencia**: 4 erros do Chat nesta sessao por inferir/
  generalizar sem ler — §6(b) POL-007, fix do rule_id, blast radius, e a
  generalizacao "lista basta sempre" no doc de avaliacao do cpf. Code pegou os 4.
  Regra: no Chat, separar "resultado" de "leitura do resultado" no proprio texto;
  marcar "nao li, e hipotese" ao afirmar estrutura OU generalizar alem da amostra.
- **Measure-before-tune**: validado no Passo 1 — o item 7 foi adiado por medicao,
  poupando o trabalho caro. Aplicar o mesmo no Passo 2 (medir acerto antes de
  ajustar prompt/clausula).
- **Resultado vs leitura no repo**: o experimento commitou dado cru sem conclusao;
  o doc de avaliacao (interpretacao) e decisao consciente separada. Manter a
  fronteira.
- **Honest measurement**: erro de transporte e dado, nao bug a re-rodar.
  Inconsistencia entre runs e dado. Nao mascarar com re-execucao.
- **PR e do Joao, Code nao abre PR.**
- **Boa decisao != fazer agora** (unificacao policy/ continua fora do caminho).

---

## 6. Primeiro passo concreto da proxima sessao

Fechar no Chat as tres decisoes de desenho do Passo 2 (K execucoes, enriquecimento
de PR, dobrar item 8), depois redigir o prompt do harness live. Plan-mode, para
ratificacao. Tudo sobre policies/eval-lgpd. Antes ou junto: atualizar a linha de
status do doc de avaliacao do cpf (PR #100 mergeado) e commitar handoff +
learning-log direto em main.