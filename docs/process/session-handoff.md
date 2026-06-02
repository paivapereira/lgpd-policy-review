# Session handoff — fim do exploratório, abertura da sessão ADR

**Data**: 2026-06-02
**Branch fechada**: `eval/test-cases-exploratory` (PR #99 → `main`).
**Próxima sessão**: implementação (frente Policy + motor), partindo de `main`.
**Restrição dominante**: ~2 semanas até a entrega. É o filtro de toda priorização abaixo.

---

## 1. Onde paramos

A sessão exploratória produziu e validou o corpo de trabalho de avaliação, agora em
PR #99 (3 commits, `src/` intacto, seed `policy/` preservado, gate 13/13, suíte 274,
G3 live passou). Conteúdo entregue:

- Instâncias de avaliação (topologia B): `policies/eval-lgpd/` (POL-005/006/007 +
  rationale) e `policies/eval-gdpr/` (gêmeo GDPR).
- Evaluator `eval/`: `cases.yaml`, `harness/run_engine_cases.py` (gate de veredito
  13/13 + Reports consolidados 10/10 válidos), PRs sintéticos, POL-008 staged fora
  do catálogo.
- Docs: `test-cases-proposal.md`, `pol-007-inversao-sensibilidade.md`, ADR-0015
  (Proposed, não implementado).

Pendência de merge do PR #99 (ações tuas, antes de mergear):
- Remover a linha `🤖 Generated with Claude Code` do corpo do PR.
- Corrigir §6(b) do `pol-007-inversao-sensibilidade.md`: o token `explicit_consent`
  **já existe** em `lawful_basis.yaml`; a correção projetada precisa do motor
  *consumir* o token + o gate de sensibilidade, não *adicionar* o token. (Inferência
  minha não-verificada; o Code leu o arquivo e desmentiu.)

---

## 2. Decisões tomadas nesta sessão (não reabrir)

- **Junção `policy/` única**: eliminar a pasta `policies/` irmã. Estrutura-alvo:
  `policy/_seed/` (fallback POL-000-only), `policy/eval-lgpd/`, `policy/eval-gdpr/`
  (instâncias irmãs). `policy/` singular = a Camada 1; nada privilegiado exceto o
  default `_seed`. Implica mudar o fallback hardcoded do loader (`<repo>/policy` →
  `<repo>/policy/_seed`). Substitui a topologia B do PR #99.
- **ADR-0015 será implementado** (não adiado), incluindo GDPR (`legal_framework`).
- **Inversão POL-007 fica DOCUMENTADA, não corrigida** — é exemplo de erro na
  avaliação, com causa-raiz e correção projetada (documento já escrito). Sai do
  caminho crítico de *código*; é trabalho de *redação*, já feito.
- **CI mínima**, não robusta: rodar o pipeline num PR e postar o Report. O resto da
  CI é trabalho futuro documentado.
- **Classifier `[]` tem causa estrutural** (não bug do modelo): `get_vocabularies`
  omite `data_categories` e `policy://examples` não existe. O Classifier foi
  instruído a classificar com um vocabulário que não lhe é exposto.

---

## 3. Lista completa de pendências (priorizada)

P0 = bloqueia tudo; P1 = necessário para o relatório; P2 = melhora o relatório;
P3 = pós-TCC. Itens marcados **[no plano]** entram no caminho crítico das 2 semanas;
os demais são "se sobrar tempo" ou pós-TCC.

| # | Pendência | Serve | Prio | No plano? |
|---|---|---|---|---|
| 1 | Expor `data_categories` no `get_vocabularies` + rodar discriminante (cpf nu vs rico) | Funcionar | P0 | **sim — passo 1** |
| 2 | Reestruturar `policy/` única (`_seed`+instâncias) + fallback loader | Funcionar/CI | P1 | **sim — passo 2** |
| — | Harness live sobre `eval-lgpd` (produz Reports de pipeline real p/ o capítulo) | Avaliação | P1 | **sim — passo 3** |
| 6 | `rule_id` poluído com caminho absoluto (dar `id:` às regras `br_*.yaml`) | Avaliação | P1 | **sim — passo 4** |
| — | CI mínima (pipeline num PR, posta Report) | CI | P2 | **sim — passo 5** |
| 3 | Inversão POL-007 | Avaliação | P1 (redação) | feito (documento) |
| 7 | `policy://examples` completo (PR autônomo + amendment ADR-0005 Decisão 9 + seed ≥2 LGPD + SCHEMA §2) | Funcionar | P1 condicional | só se passo 1 mostrar que a lista não basta |
| 8 | Correções jurídicas: POL-006 (Art. 12§2º→6ºIII), POL-005 (estreitar p/ marketing) | Avaliação | P2 | se tocar as cláusulas |
| 4 | `legal_framework: Literal["LGPD"]` → validar contra `accepted_law_identifiers` (destrava Report GDPR) | Avaliação | P2 | se sobrar tempo |
| 5 | Token `consent` hardcoded ao LGPD no motor | — | P3 | pós-TCC (limite documentado) |
| 9 | Mover `scripts/`→`tests/`, deletar `scripts/` do root | Higiene | P3 | pós-TCC; **depois** do passo 2 |

---

## 4. Plano de ação — 1 → 2 → harness live → 6 → CI mínima

Cada passo abaixo é uma tarefa de Code separada (prep no Chat → prompt ratificado →
GATE 1 plan-mode → execução → review de diff → merge). Ordem é por dependência: cada
passo destrava o seguinte.

### Passo 1 — Expor `data_categories` ao Classifier + medir

**O quê**: hoje `get_vocabularies` (no `policy-reader`) retorna operation/lawful_basis/
control/out_of_scope mas **omite** `data_categories`, que fica server-side, usado só
dentro de `check_applicability`. O Classifier é instruído a classificar usando o
vocabulário de categorias — que nunca lhe é exposto. Resultado: devolve `[]`, e o
pipeline inteiro cai em `not_applicable`/POL-000 (provado no run G3).

**Por que primeiro**: é o gargalo de todos os três objetivos. Sem categoria, nenhum
caso produz veredito substantivo no pipeline real — não há o que avaliar nem o que
mostrar na CI. É também o mais barato: expor um vocabulário que já existe.

**Como**: acrescentar `data_categories` ao retorno de `get_vocabularies` (consertar o
código contra o que a própria spec já espera — Gate G12 da `classifier.md`). Toca
`src/mcp_servers/policy_reader` (tools/server). É additive.

**A medição (parte essencial, não opcional)**: com a categoria exposta, rodar o
**experimento discriminante** — o Classifier sobre `def collect(cpf)` (input pobre,
o do G3) e sobre um campo rico (`cpf: str` num model Pydantic, como em
`eval/prs/COMP-001/users.py`). Três desfechos possíveis: (a) classifica os dois → a
lista bastava; (b) classifica o rico, abstém no pobre → o input pobre era a causa, o
sistema está são (resultado positivo); (c) abstém nos dois → ainda falta algo
(provavelmente `policy://examples`, item 7). **Medir antes de decidir o item 7** —
ele é caro (PR autônomo + amendment de ADR) e pode ser desnecessário.

**Saída esperada**: Classifier classificando categoria; veredito de se o item 7 é
necessário.

### Passo 2 — Reestruturar a Camada 1 sob `policy/` única

**O quê**: fundir `policy/` (seed) + `policies/` (instâncias, do PR #99) numa só pasta
`policy/`, com o seed em `policy/_seed/` e as instâncias como irmãs
(`policy/eval-lgpd/`, `policy/eval-gdpr/`). Eliminar `policies/`.

**Por que aqui**: é pré-requisito de paths do harness live (passo 3) e da CI (passo 5)
— ambos apontam para a raiz da policy. Fazer antes evita que os paths mudem no meio.
Vem depois do passo 1 porque o passo 1 mexe no `policy-reader` e não quer colidir com
mudança de estrutura de pasta na mesma janela.

**Como**: mover as instâncias para dentro de `policy/`; mudar o fallback default do
loader de `<repo>/policy` para `<repo>/policy/_seed`. Toca `loader.py` + ajustar
`test_bootstrap` (valida o fallback) e o `monkeypatch.delenv` do `test_g3` (que limpa
`POLICY_READER_ROOT` contando com o fallback ser o seed POL-000-only — segue válido,
só muda o path). Mudança de motor pequena, mas revalidar a suíte.

**Cuidado**: nenhuma instância pode ser privilegiada estruturalmente; o `_seed` é
default por config do loader, não por natureza. O underscore sinaliza "meta, não
cliente" e ordena no topo.

**Saída esperada**: `policy/` única, loader caindo em `_seed` por default, suíte verde.

### Passo 3 — Harness live sobre `eval-lgpd`

**O quê**: adaptar o padrão do `test_g3_live_e2e.py` (que já roda o pipeline real
ponta-a-ponta) para rodar sobre os PRs sintéticos de avaliação, apontando
`POLICY_READER_ROOT=policy/eval-lgpd` (oposto do G3, que limpa a env var para usar o
seed). Capturar os Reports reais emitidos.

**Por que é o coração da avaliação**: os 10 Reports que temos hoje são do harness
**determinístico** — exercitam só o motor (Matcher), com categorias injetadas à mão.
O capítulo de avaliação de um sistema multi-agente precisa de Reports onde Triager,
Detector e Classifier **de fato rodaram**. Este passo produz isso: Reports de
pipeline real, com as tuas cláusulas, e — de quebra — mede a taxa de acerto real do
Classifier (quantos PRs ele classifica certo).

**Depende de**: passo 1 (senão o Classifier devolve `[]` e tudo vira `not_applicable`)
e passo 2 (paths). O ambiente já está confirmado pronto (G3 passou: semgrep 1.163.0,
`.mcp.json`, sessão autenticada).

**Insumo pronto**: o `_make_cpf_repo` do G3 mostra como transformar arquivos soltos
em commits git que o `scan_diff` consome (base_ref/head_ref). Os `eval/prs/*` precisam
desse tratamento, e podem precisar de enriquecimento (campos nomeados, não parâmetros
nus) conforme o resultado do discriminante do passo 1.

**Saída esperada**: Reports de pipeline real sobre eval-lgpd — o material empírico do
capítulo de avaliação.

### Passo 4 — Limpar o `rule_id` poluído

**O quê**: no run G3, o `rule_id` veio
`C.Users.joaoguilherm.pereira.dev...rules.br-cpf` — o Semgrep prefixou o caminho
absoluto do arquivo de regra. Isso propaga verbatim por toda a cadeia até o Report
final (correto como passthrough, mas feio: vaza o teu path de usuário no laudo).

**Por que depois do harness live**: é cosmético, mas os Reports "oficiais" do
relatório não podem sair com o teu diretório home dentro. Fazer depois do passo 3
significa que os Reports do relatório saem limpos; fazer antes seria prematuro (o
passo 3 pode revelar outros campos a sanear).

**Como**: dar um `id:` explícito a cada regra `br_*.yaml` (hoje provavelmente sem
`id`, então o Semgrep deriva do caminho). Toca
`src/mcp_servers/semgrep_runner/rules/`. Pequeno, alto valor estético. Re-rodar o
harness live (passo 3) depois para regenerar os Reports limpos.

**Saída esperada**: `rule_id` = `br-cpf` limpo nos Reports.

### Passo 5 — CI mínima (GitHub Actions)

**O quê**: uma Action que, num PR, roda o pipeline e posta o Report como comentário.
Mínima, não robusta — sem matrizes, sem otimização, sem retry sofisticado.

**Por que por último**: depende de tudo acima funcionar (pipeline produzindo veredito
real, paths estáveis, Reports limpos). É o objetivo 2 do TCC, demonstrável como
"integração CI realizada" mesmo em forma mínima. CI robusta é trabalho futuro
documentado — a banca não cobra robustez de CI num TCC sobre conformidade LGPD.

**Cuidado de ambiente**: a CI precisa de sessão Claude autenticada (segredo de
repositório) e semgrep instalado no runner. O `test_g3` documenta os pré-requisitos;
a Action os replica. Auth via secret, semgrep via step de install.

**Saída esperada**: um PR de demonstração com o Report postado automaticamente — a
evidência do objetivo 2.

---

## 5. Notas de método (preservar entre sessões)

- **Verificação antes de inferência**: o erro da §6(b) do doc POL-007 (eu afirmei que
  faltava um token que já existia) é o caso-exemplo. Ler o arquivo antes de afirmar
  estrutura, sempre — vale para o Chat tanto quanto para o Code.
- **Measure-before-tune**: o item 7 (`policy://examples`) só se justifica se o
  discriminante do passo 1 mostrar que a lista de tokens não basta. Não construir a
  peça cara por suposição.
- **Não misturar naturezas de tarefa**: consertar input e medir pipeline são tarefas
  separadas (senão um Report ruim é ambíguo entre input e pipeline). Mesma lógica
  separou o PR de avaliação (não toca `src/`) da frente de implementação (toca o
  motor).
- **PR é teu, Code não abre PR**: Code implementa e commita na branch; tu crias o PR.
- **Documentar limite > corrigir mal sob prazo**: a inversão POL-007 vira seção forte
  de avaliação (achado + causa + correção projetada), com risco zero de prazo, em vez
  de uma correção de motor arriscada na véspera.

---

## 6. Primeiro passo concreto da próxima sessão

Abrir prompt do **Passo 1**: expor `data_categories` no `get_vocabularies` +
experimento discriminante. É P0, é barato, e o resultado dele (a lista basta? sim/não)
decide se o item 7 entra no escopo das 2 semanas ou sai. Prep no Chat antes do prompt:
confirmar o locus exato em `tools.py`/`server.py` onde `get_vocabularies` monta o
retorno, e definir os dois inputs do discriminante (o pobre do G3 e um rico de
`eval/prs/`).