# Caso de avaliação — Robustez a modelo: ablação por estágio da capacidade do modelo no pipeline

**Tipo**: investigação de robustez a modelo da fase de QA (posterior ao MVP), ao lado da fronteira de escalação (§9.2 do relatório de QA) e dos testes de limite tipo POL-007 — **indício exploratório, não conclusivo**, de configuração de modelo ótima.
**Status**: medido; achado **direcional** (régua estatística da regra 3/K aplicada). **Nenhuma configuração é certificada robusta** — teto IC95% ~30% sobre o caso de violação. Ferramenta de medição **read-only em scratch**, não parte de `src/`.
**Evidência**: harness de medição `convergence_harness.py` (artefato de scratch da fase de QA — importa a pipeline congelada e injeta modelo por estágio no *seam* do SDK; não modifica `src/`/gate/Política/MCP). Dados crus por execução em `runs.jsonl` (saída do harness, um registro por run, com `attribution` estágio→modelo efetivo). Configs A–E (ablação heterogênea) + Eixo 2 (homogêneo, contexto).

---

## 1. Resumo

Esta investigação mede **se e onde** a capacidade do modelo afeta a estabilidade do veredito *gated* do pipeline de cinco estágios (Triager→Detector→Classifier→Matcher→Reporter). O método é uma **ablação por estágio**: injeta-se um modelo por estágio (Haiku ou Sonnet) via o *seam* do SDK, sem tocar a pipeline congelada, e mede-se a taxa de falso-negativo sobre um caso de violação plantado (VIOL-001, POL-005), com um caso de conformidade (COMP-001) como controle.

O achado, **enunciado sob a régua estatística e não além dela**: a instabilidade de veredito **comprovada** (observações não-zero) aparece apenas quando o **Classifier** roda em Haiku (A: 1/3; B: 2/10 falsos-negativos). Quando o Classifier sobe para Sonnet, o falso-negativo observado **cai a 0/10** — e isso ocorre **com ou sem** o Matcher em Sonnet (Config E isola: Classifier-Sonnet + Matcher-**Haiku** já dá 0/10). A leitura direcional é que **a alavanca observada é o Classifier, não o Matcher**; as configs que mantinham o Matcher em Sonnet (C, D) pagaram esse custo sem retorno observável.

**Régua, declarada antes das conclusões (§4):** `0/10` **não é taxa zero** — pela regra dos três, o teto do IC95% da taxa real é ~30%. Nenhuma config (C, D, E) é robusta; são indistinguíveis nesse N. O sinal mais forte, **livre do teto de "zero eventos"**, é mecanístico: a variância da categoria advisory `data_categories` no VIOL-001 **colapsa de 5/10 para 10/10** quando o Classifier sobe a Sonnet, ligando a instabilidade à extração não-determinística do Classifier-Haiku.

Este documento registra o caso como **indício exploratório** de configuração de modelo ótima — mesmo estatuto epistêmico dos demais achados de fronteira da fase de QA (POL-007, suficiência de vocabulário, fronteira de escalação): medição, não suposição; conclusão escopada ao que foi medido.

---

## 2. A pergunta investigada

A propriedade central do sistema é que a decisão acompanha a Política versionada. Uma pergunta de robustez, ortogonal, é: **o veredito *gated* depende do modelo que executa os agentes?** E, se depende, **onde** na pipeline de cinco estágios a capacidade do modelo afeta a estabilidade da decisão?

Duas sub-perguntas, na ordem em que foram atacadas:

1. **Homogênea (Eixo 2):** trocando o modelo de *todos* os agentes simultaneamente, a saída *gated* converge? (contexto — §5.1)
2. **Heterogênea (Configs A–E):** isolando estágio a estágio, **qual estágio** carrega a instabilidade observada? (medição principal — §5.2)

A relevância para a tese: se a arquitetura afirma que a decisão é função da Política (e não do modelo), a localização de qualquer dependência de modelo residual é um limite a declarar, não a mascarar — exatamente como a inversão POL-007 é um limite do motor declarado em vez de escondido.

---

## 3. Método

**Ablação por estágio via injeção no *seam* do SDK (rota *inject*).** A pipeline congelada constrói `ClaudeAgentOptions` por estágio **sem** fixar `model` (verificado: `options.model is None` em todos os cinco *seams*), de modo que o modelo efetivo é o *default* ambiente. O harness, em scratch, faz *monkeypatch* dos três *seams* do SDK (`coordinator.driver.query`, `coordinator.driver.ClaudeSDKClient`, `coordinator.run.query`) e, **sem alterar `src/`**, resolve o estágio de cada chamada (pelo `system_prompt`, com asserção de unicidade — zero ou dois *matches* falham alto, nunca adivinham) e injeta `options.model` segundo um mapa `{estágio: modelo}`. O modelo homogêneo, por contraste, exigiria apenas a variável de ambiente `ANTHROPIC_MODEL` (global ao processo, logo incapaz de heterogeneidade).

**Gate de atribuição estágio→modelo (honestidade da medição).** Para cada run, o harness lê o **modelo efetivo** de `AssistantMessage.model` em cada estágio e confronta-o com o modelo atribuído. Um run em que qualquer estágio observe família diferente da atribuída é marcado `attribution_failed` e **não conta** para convergência. Nas cinco configs reportadas, a atribuição foi **100%** (A: 6/6; B/C/D/E: 13/13 cada) — em particular, a Config E confirmou `matcher` observando **Haiku** em todas as execuções, que é o ponto do teste de isolamento.

**Recorte de campos reusado VERBATIM do gate da Camada 3.** O harness importa, sem reimplementar, o recorte *gated*/advisory de `eval/harness/camada3_compare.py` (mesmas constantes `_VERDICTS`/`_PROVENANCE_KEYS` e projeções `_verdict_rule_multiset`/`_data_categories_multiset`). O veredito por cláusula (Nível 1) e os demais campos *gated* (Nível 2: `run_outcome`, `counts`/`total`, proveniência, *multiset* (verdict, rule_id)) são fatias do **mesmo** conjunto ESTRITO do portão; `data_categories` é o campo ADVISORY do portão.

**Régua estatística — regra dos três.** Com 0 eventos observados em N execuções, o limite superior do IC95% da taxa real é ≈ 3/N. Para N=10, o teto é ~30%. Portanto `0/10` é lido como "0 falsos-negativos em 10; teto IC95% ~30%; indício não conclusivo", nunca como "taxa zero" ou "robusto".

---

## 4. Escopo e limitações (declarados antes das conclusões)

- **Dois *fixtures* sintéticos, uma cláusula.** A medição usa VIOL-001 (violação plantada de coleta sem base legal) e COMP-001 (coleta com consentimento), ambos sob **POL-005 apenas**. **Não generaliza** para POL-006/POL-007, para outras jurisdições, nem para *pull requests* reais. A inversão POL-007 (caso sensível) está deliberadamente fora desta matriz.
- **N=10 por célula no caso de violação** (Configs B–E); a Config A foi medida com **K=3** (N menor ainda) no VIOL-001. `0/10` **não** é taxa zero: teto IC95% ~30% pela regra dos três. **Nenhuma configuração é certificada robusta**; afirmações são **direcionais**, e as três configs que deram `0/10` (C, D, E) são **estatisticamente indistinguíveis** entre si nesse N.
- **O Eixo 2 homogêneo (§5.1) foi medido em K=2** (sondagem), serve apenas de **contexto**, não de medição de taxa.
- **Custo é por run medido nesta amostra**, sujeito à variância de *cache* (o `cache_creation` amortiza ao longo das execuções agrupadas por config); compara configs entre si, não estabelece custo absoluto de produção.
- **A ferramenta é um artefato de scratch**, não versionada em `src/`. Os números abaixo são reproduzíveis em princípio (método acima), mas a promoção do harness + dados crus a `eval/experiments/` para reprodutibilidade plena é trabalho futuro (§7).

---

## 5. Dados

### 5.1 Eixo 2 — homogêneo (contexto, K=2)

Trocando o modelo de **todos** os estágios ao mesmo tempo (K=2 — contexto, não taxa):

| Modelo (todos os 5 estágios) | COMP-001 | VIOL-001 | Emite? | Observação |
|---|---|---|---|---|
| **Haiku** | — | — | **não** | `ReporterTurnsExhausted` nos casos com *finding* (4/4); SKIP-001 pula via Triager (2/2). O Reporter-Haiku estoura `max_turns=3` (limite congelado; não tocado) |
| **Sonnet** | `compliant` 2/2 | `violation_candidate` 2/2 | sim | converge; concorda com Opus |
| **Opus** | `compliant` 2/2 | `violation_candidate` 2/2 | sim | converge; concorda com Sonnet |

Leitura de contexto: entre os modelos que **completam** o pipeline (Sonnet, Opus), o veredito *gated* foi idêntico e concordante nas execuções observadas; o Haiku homogêneo **não emite** nos casos substantivos, por um limite de *turn-budget* do Reporter (não de raciocínio). Isso motivou a ablação heterogênea: o Reporter precisa de um modelo mais capaz para emitir, mas **onde** a *decisão* depende do modelo é uma pergunta separada.

### 5.2 Configs A–E — ablação heterogênea (medição principal)

Escada controlada; em todas, `reporter=sonnet` (necessário para emitir, §5.1). VIOL-001 K=10 (exceto A, K=3); COMP-001 K=3.

| Config | triager | detector | **classifier** | matcher | reporter | **VIOL falso-neg** | COMP | advisory VIOL | atribuição | $/run |
|---|---|---|---|---|---|---|---|---|---|---|
| A | haiku | haiku | **haiku** | haiku | sonnet | **1/3** *(K=3)* | 3/3 | — | 6/6 | $0,172 |
| B | haiku | haiku | **haiku** | sonnet | sonnet | **2/10** | 3/3 | varia 5/10 | 13/13 | $0,231 |
| **E** | haiku | haiku | **sonnet** | **haiku** | sonnet | **0/10** | 3/3 | estável 10/10 | 13/13 | **$0,230** |
| C | haiku | haiku | **sonnet** | sonnet | sonnet | **0/10** | 3/3 | estável 10/10 | 13/13 | $0,294 |
| D | haiku | **sonnet** | **sonnet** | sonnet | sonnet | **0/10** | 3/3 | estável 10/10 | 13/13 | $0,312 |

Ordenado para evidenciar a transição: **Classifier-Haiku (A, B) → falso-negativo presente; Classifier-Sonnet (E, C, D) → 0/10**, com o Matcher em Haiku (E) ou Sonnet (C, D).

**Custo por estágio (o porquê de E ser a mais barata das 0/10).** Em E o Matcher roda em Haiku ($0,41 somado nas 13 execuções) contra Sonnet em C ($1,15 somado) — o Matcher-Sonnet de C/D adiciona custo sem mudar o falso-negativo observado (0/10 nas duas). O Detector-Sonnet de D adiciona +$0,018/run sobre C, também sem efeito observável.

### 5.3 Mecanismo — a advisory `data_categories` (sinal sem o teto de "zero eventos")

A categoria advisory do VIOL-001, **que não sofre da limitação de 0 eventos** (é um contraste 5/10 vs 10/10, não uma contagem de eventos raros):

| Config | Classifier | advisory `data_categories` (VIOL-001, N=10) |
|---|---|---|
| B | **haiku** | **varia: 5/10** `[identificacao]` · 5/10 `[doc_oficiais+identificacao]` |
| E | **sonnet** | **estável: 10/10** `[doc_oficiais+identificacao]` |
| C | **sonnet** | estável: 10/10 |
| D | **sonnet** | estável: 10/10 |

Trocar o Classifier Haiku→Sonnet **colapsa a variância de categoria** — e isso vale mesmo com o Matcher em Haiku (E). Em B (Classifier-Haiku), a inspeção por run mostrou que o falso-negativo **não** se explicava pela categoria isolada (runs com a mesma categoria davam vereditos diferentes; os dois falsos-negativos tinham categorias *distintas* entre si), o que aponta para a extração não-determinística do Classifier-Haiku como um todo (provavelmente também `declared_legal_basis`, campo fora do recorte *gated*/advisory e portanto não quantificado aqui).

---

## 6. Achado direcional (régua aplicada)

1. **Instabilidade comprovada (observações não-zero) só com Classifier-Haiku.** A (1/3) e B (2/10) são as únicas observações de falso-negativo. Subir **apenas** o Matcher (A→B) **não** corrigiu — manteve-se em 2/10.
2. **O falso-negativo observado cai a 0/10 quando o Classifier sobe a Sonnet — com ou sem Matcher-Sonnet.** A Config E (Classifier-Sonnet, **Matcher-Haiku**) atinge o mesmo 0/10 observado que C e D (que tinham Matcher-Sonnet). Isso **desfaz o confound** de C/D: o Matcher-Sonnet não era necessário para o resultado observado. **A alavanca observada é o Classifier, não o Matcher.**
3. **Mecanismo corroborante, livre do teto de 0 eventos:** a variância da categoria advisory colapsa 5/10 → 10/10 ao subir o Classifier, ligando a instabilidade à extração não-determinística do Classifier-Haiku.
4. **Indício de configuração ótima (EXPLORATÓRIO):** entre as observadas, **E** (Classifier+Reporter em Sonnet; Triager/Detector/Matcher em Haiku) reproduz o 0/10 ao **menor custo** ($0,230/run, igual a B que ainda era 2/10, e abaixo de C $0,294 e D $0,312). **Não certificado** — teto IC95% ~30%, *single-clause*, *single-fixture*.

**O que NÃO se afirma:** que E (ou C, ou D) seja robusta; que `0/10` seja taxa zero; que o resultado se sustente em POL-006/POL-007, outras jurisdições ou PRs reais. As três configs `0/10` são indistinguíveis no N medido.

---

## 7. Trabalho futuro — de indício a evidência

- **Apertar o teto estatístico:** repetir a Config E (e C) com K maior (ex.: K≈50 derruba o teto IC95% de ~30% para ~6%), para distinguir "0 observado" de "baixo, mas não zero".
- **Ampliar o escopo:** mais cláusulas (POL-006, POL-007 — esta com o cuidado da inversão de sensibilidade documentada à parte) e mais *fixtures*, incluindo casos de violação com formas distintas de ausência de base legal.
- **Isolar o campo upstream exato do Classifier:** projetar `declared_legal_basis` do *trace* do Classifier (já escrito ao scratchpad pela pipeline) e correlacioná-lo com os falsos-negativos de B, para separar "categoria" de "base legal" como fonte.
- **Reprodutibilidade plena:** promover o harness `convergence_harness.py` e os `runs.jsonl` de scratch para `eval/experiments/`, alinhando o estatuto de evidência ao dos demais experimentos versionados (ex.: `category_exposure_discriminant.py`).

---

## 8. Linha de inventário para o relatório de QA

Entrada pronta para o **Quadro 9 — Experimentos empíricos (opt-in, medições não asserções)** do relatório de QA, no mesmo formato dos demais itens de fronteira:

| Experimento | Pergunta | Achado |
|---|---|---|
| `convergence_harness.py` (ablação por estágio; scratch da fase de QA) | O veredito *gated* depende do modelo? Em qual estágio da pipeline a capacidade do modelo afeta a estabilidade da decisão? | **Indício direcional (não conclusivo).** Falso-negativo em VIOL-001/POL-005 só com **Classifier-Haiku** (A 1/3, B 2/10); cai a **0/10** quando o Classifier sobe a Sonnet, **com ou sem** Matcher-Sonnet (Config E isola). Advisory de categoria colapsa 5/10→10/10 ao subir o Classifier. Ótimo observado: **E** (Classifier+Reporter Sonnet, resto Haiku) ao menor custo. **Régua:** `0/10` ≠ zero, teto IC95% ~30% (regra 3/K); *single-clause*/*single-fixture*; atribuição estágio→modelo 100% nas configs reportadas. |

Estatuto epistêmico para o corpo do relatório: **exploratório**, ao lado da inversão POL-007 (limite do motor) e da suficiência de vocabulário do Classifier — medição que informa uma direção (a estabilidade do veredito de violação responde ao Classifier), sem certificar configuração robusta.
