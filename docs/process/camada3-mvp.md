# Camada-3-MVP — Gate de milestone (qualitativo)

**Status do gate qualitativo:**

- **Local (K=2): PASS.** Convergência estrita demonstrada nos três fixtures
  (COMP-001, VIOL-001, SKIP-001) sobre 2 rodadas live completas.
- **CI (Gates #1/#2): PENDENTE-CI.** O `workflow_dispatch` ainda não foi
  disparado; `lgpd-review.yml` é código não-exercitado no runner ubuntu.
- **Camada-3-MVP: NAO fechada.** O status só vira "fechada" quando a §9 (Gates
  #1/#2 — CI) for preenchida com o resultado de um dispatch real.

**Proveniência.** Implementação em três PRs squash-merged em `main` (`b9259c3`,
2026-06-04): #107 (entrypoint + formatador), #108 (companion edits B/C), #109
(harness gate + workflow). Contrato de implementação: plano Passo 4 v3 ratificado
(as peças de infra de CI não têm spec em `docs/specs/` — são adaptador de borda,
não superfície de contrato do pipeline; ver `docs/tasks.md` §Milestone D carve-out).

---

## 1. Escopo e método

O gate qualitativo da Camada-3-MVP exige (planejamento-tcc2.md §Camada-3-MVP):
Action funcional para os 3 fixtures, harness local field-scoped, **2 validações
e2e completas**, e veredito PASS/FAIL em prosa com evidência reproduzível.

**Mecanismo.** `eval/harness/camada3_gate.py` constrói, por fixture, um repo git
efêmero de dois commits (`make_pr_repo`: base vazia + head com os arquivos do
fixture), seta `POLICY_READER_ROOT=policies/eval-lgpd` (absoluto), roda o pipeline
REAL `coordinator.run.run_pipeline` (Triager→Detector→Classifier→Matcher→Reporter,
via SDK + MCP servers reais), e compara o Report live contra o baseline committado
`<pr_dir>/.expected-report.json` (gerado deterministicamente por
`run_engine_cases.py` — o gate **lê, nunca regenera**).

**Decisão de gate (field-scoped, plano v3 §Decisão de gate).**
- **ESTRITO** (mismatch reprova): `run_outcome`; `summary.counts` (4 vereditos) +
  `summary.total`; tripla de proveniência + `report_schema_version`; e o
  **multiset** `(verdict, rule_id)` por finding.
- **ADVISORY** (reportado, nunca reprova): `data_categories` (extraído pelo
  Classifier, estágio LLM).
- **EXCLUÍDO**: `report_id` (uuid4/run), `scope.*` (refs divergem por
  construção), prosa (`evidence`/`reason`/`snippet`), `file`/`line`.
- **outcome-only** (SKIP-001, sem baseline): PASS sse `run_outcome` em
  `{skipped_by_triager, success_no_candidates}` (ambos = sem veredito substantivo).

**Disposição de honestidade (plano §3.5 / G).** Cada rodada foi executada UMA vez
e reportada crua. Não houve re-roll. K=1 é uma observação; **convergência só
significa algo com K≥2** — por isso duas rodadas. Uma divergência entre rodadas é
dado a documentar, não falha a esconder.

---

## 2. Os dois runs crus (verbatim)

Capturado de `uv run python -m eval.harness.camada3_gate --case all`, executado
duas vezes (local, sessão autenticada + `semgrep 1.163.0` no PATH), 2026-06-04.
Linhas `RAW` emitidas pelo próprio gate em todo run (não só no mismatch) — é o que
torna a convergência auditável em vez de confiável-no-PASS.

```
########## ROUND 1 ##########
RAW COMP-001: run_outcome='success_with_findings' total=4 counts={'compliant': 1, 'violation_candidate': 0, 'indeterminate': 0, 'not_applicable': 3} multiset(verdict,rule_id)={('not_applicable', 'br-cpf'): 3, ('compliant', 'br-cpf'): 1} data_categories={('dados_de_documentos_oficiais', 'dados_de_identificacao'): 4}
### Gate COMP-001: PASS
- advisory: data_categories (advisory): {('dados_de_documentos_oficiais', 'dados_de_identificacao'): 4} != {('dados_de_identificacao',): 4}
RAW VIOL-001: run_outcome='success_with_findings' total=4 counts={'compliant': 0, 'violation_candidate': 1, 'indeterminate': 0, 'not_applicable': 3} multiset(verdict,rule_id)={('not_applicable', 'br-cpf'): 3, ('violation_candidate', 'br-cpf'): 1} data_categories={('dados_de_documentos_oficiais', 'dados_de_identificacao'): 4}
### Gate VIOL-001: PASS
- advisory: data_categories (advisory): {('dados_de_documentos_oficiais', 'dados_de_identificacao'): 4} != {('dados_de_identificacao',): 4}
RAW SKIP-001: run_outcome='skipped_by_triager' total=0 counts={'compliant': 0, 'violation_candidate': 0, 'indeterminate': 0, 'not_applicable': 0} multiset(verdict,rule_id)={} data_categories={}
### Gate SKIP-001: PASS
EXIT_R1=0

########## ROUND 2 ##########
RAW COMP-001: run_outcome='success_with_findings' total=4 counts={'compliant': 1, 'violation_candidate': 0, 'indeterminate': 0, 'not_applicable': 3} multiset(verdict,rule_id)={('not_applicable', 'br-cpf'): 3, ('compliant', 'br-cpf'): 1} data_categories={('dados_de_autenticacao', 'dados_de_documentos_oficiais', 'dados_de_identificacao'): 4}
### Gate COMP-001: PASS
- advisory: data_categories (advisory): {('dados_de_autenticacao', 'dados_de_documentos_oficiais', 'dados_de_identificacao'): 4} != {('dados_de_identificacao',): 4}
RAW VIOL-001: run_outcome='success_with_findings' total=4 counts={'compliant': 0, 'violation_candidate': 1, 'indeterminate': 0, 'not_applicable': 3} multiset(verdict,rule_id)={('not_applicable', 'br-cpf'): 3, ('violation_candidate', 'br-cpf'): 1} data_categories={('dados_de_documentos_oficiais', 'dados_de_identificacao'): 4}
### Gate VIOL-001: PASS
- advisory: data_categories (advisory): {('dados_de_documentos_oficiais', 'dados_de_identificacao'): 4} != {('dados_de_identificacao',): 4}
RAW SKIP-001: run_outcome='skipped_by_triager' total=0 counts={'compliant': 0, 'violation_candidate': 0, 'indeterminate': 0, 'not_applicable': 0} multiset(verdict,rule_id)={} data_categories={}
### Gate SKIP-001: PASS
EXIT_R2=0
```

Observação prévia (não numerada no K): antes da instrumentação de raw-evidence
(commit `781c5dd`), o Gate #3 isolado
(`uv run pytest -m live tests/harness/test_camada3_gate_live.py`) rodou COMP-001 e
deu PASS (2026-06-04, ~2m13s) — uma observação estrita concordante, mas sob versão
**anterior** do harness (mesmo caminho de comparação, binário diferente). Para
manter o K sob condição uniforme, **conto K=2 para os três** (R1+R2 sob o gate
instrumentado) e trato o Gate #3 como observação prévia concordante, não como uma
terceira observação equivalente.

---

## 3. Eixo estrito — convergência sobre K=2

| Caso | `(verdict, rule_id)` multiset R1 | R2 | `run_outcome` R1/R2 | Convergiu? |
|---|---|---|---|---|
| **COMP-001** | `{(not_applicable,br-cpf):3, (compliant,br-cpf):1}` | idêntico | success_with_findings / idem | **Sim** |
| **VIOL-001** | `{(not_applicable,br-cpf):3, (violation_candidate,br-cpf):1}` | idêntico | success_with_findings / idem | **Sim** |
| **SKIP-001** | `{}` | `{}` | skipped_by_triager / idem | **Sim** |

`counts`, `total` e a tripla de proveniência também idênticos entre rodadas em
todos os casos. **Os três convergiram sobre K=2 no eixo estrito** — estabilidade
demonstrada, não afirmada.

---

## 4. Eixo advisory — drift do COMP-001 (evidência POSITIVA do desenho)

O único movimento entre rodadas caiu no eixo advisory:

| Caso | `data_categories` R1 | R2 | drift entre rodadas? |
|---|---|---|---|
| **COMP-001** | `(documentos_oficiais, identificacao)` | `(autenticacao, documentos_oficiais, identificacao)` | **Sim — +`dados_de_autenticacao` na R2** |
| **VIOL-001** | `(documentos_oficiais, identificacao)` | `(documentos_oficiais, identificacao)` | não |

(Baseline engine = `(dados_de_identificacao,)`; ambas as rodadas diferem do
baseline — a extração live é mais rica. Tudo advisory.)

**Por que isto é força do desenho, não limitação.** O sistema exibiu
não-determinismo REAL de extração do Classifier (a R2 acrescentou
`dados_de_autenticacao` ao COMP-001), e o gate o **classificou corretamente como
inócuo** (advisory, não reprovou). Se `data_categories` estivesse no eixo estrito,
a R2 teria reprovado contra a R1 e contra o baseline — por pura variância de
extração LLM, não por regressão. Isto **valida empiricamente a Decisão A** do
plano (tirar `data_categories` do estrito porque é LLM-driven): a correção, que
parecia teórica no review do v2, foi confirmada por um drift observado que ela
absorveu sem reprovar. Enquadramento (tom RNF-002): "medimos a variância e
mostramos que o gate a trata corretamente" — não "o sistema é determinístico"
(que seria falso). Não-determinismo é **por-campo**; o gate respeita essa
granularidade.

---

## 5. Invariante de cluster (§0-causa-3) — por que o drift foi inócuo

Toda categoria que o Classifier extraiu nos 5 runs com findings —
`dados_de_identificacao`, `dados_de_documentos_oficiais`, `dados_de_autenticacao` —
pertence ao cluster que intersecta **apenas POL-005**. Nenhuma tocou POL-006
(`dados_de_perfil_comportamental`) ou POL-007 (`dados_de_saude`). Por isso o floor
`not_applicable:3` (POL-000/006/007) e os vereditos **não flliparam apesar** do
drift de categoria. É a fronteira do §0 funcionando na prática: drift **cosmético**
(categoria a mais no mesmo cluster governante) não vira drift **consequente**
(categoria que ativaria outra cláusula e mudaria counts/multiset). A teoria previu
a fronteira; o experimento a respeitou.

> Precondição registrada: esta estabilidade do floor vale **enquanto** o Classifier
> não extrair uma categoria que intersecte uma cláusula governante além de POL-005.
> Um drift para `dados_de_saude`/`dados_de_perfil_comportamental` flliparia o estrito
> e seria evento a investigar (§0-causa-3), nunca gate a afrouxar.

---

## 6. `rule_id` bare `br-cpf` — primeira confirmação e2e pós-#105

O blocker que sustentava esta etapa: o `rule_id` normalizado (`_normalize_rule_id`,
`src/mcp_servers/semgrep_runner/tools.py`) só estava ancorado por testes unit
pós-#105; os 28 runs do Passo 2 eram **pré-#105** (carregavam o caminho dotificado
completo) e foram corretamente desclassificados como evidência stale. Estes runs
são a **primeira observação do regime atual**: o `rule_id` emitiu **bare `br-cpf`**
em todos os runs com findings sob o gate instrumentado (COMP-001 ×2, VIOL-001 ×2);
a observação prévia do Gate #3 (COMP-001, pré-instrumentação) também emitiu bare
`br-cpf`, concordante. Blocker fechado sobre **K=2 por caso**, não K=1.

---

## 7. Nota de método honesta — previsão que não bateu

Durante a prep, a hipótese de maior risco apostava no **VIOL-001** divergir antes
do COMP-001 no multiset (caminho de violação tem mais superfície para o
§0-causa-2: drift de `legal_basis` flipando o veredito). **A previsão não bateu:**
nenhum multiset divergiu (nem COMP nem VIOL), e a variância de LLM que de fato
apareceu foi no `data_categories` do **COMP-001**, contida no eixo advisory.
Registro honesto: o sistema foi estável onde se esperava fragilidade; isso é dado
bom, não validação da intuição. O não-determinismo existe e é mensurável, mas
ficou no eixo advisory em todos os casos.

---

## 8. Simplificação base-vazia (demonstração vs produção)

O repo efêmero usa commit base **vazio**, então o "diff" escaneado pelo `scan_diff`
(`--baseline-commit <base>`) é o arquivo inteiro do fixture. Equivalente ao
incremental para fixtures de um arquivo (validado nos 28 runs do Passo 2). O
caminho `pull_request` de **produção** usaria merge-base real → diff incremental.
Diferença declarada entre superfície de demonstração (MVP) e de produção
(Milestone D), não escondida.

---

## 9. Gates #1/#2 — CI (PENDENTE-CI)

**[PENDENTE-CI — preencher após o primeiro `workflow_dispatch`.]**

Os runs da §2 são **locais**: exercitam o pipeline + o gate, mas **não** o setup do
runner ubuntu. O `lgpd-review.yml` (workflow_dispatch + matrix dos 3 fixtures) é
código sintaticamente são mas **nunca executado em CI**. Dois gates vivem só lá
(plano §7):

- **Gate #1 (auth + wheel).** `uv sync` resolve o wheel `manylinux` do
  `claude-agent-sdk==0.2.87` (CLI embutido, ADR-0001:103-110) e a sessão autentica
  via `secrets.ANTHROPIC_API_KEY`? Nota de eixo de auth: o run local autenticou via
  sessão **OAuth** local (sem `ANTHROPIC_API_KEY` no shell) — dev local é OAuth, CI
  é API key. O caminho-key no runner headless é exatamente o que o Gate #1 prova;
  **o local funcionar não prova que o CI funciona** (auth é onde os dois ambientes
  mais divergem).
- **Gate #2 (`--project` .mcp.json em CI).** O temp `.mcp.json` com
  `uv run --project <repo-root>` resolve os servers quando o cwd é o repo efêmero?
  (Verificado no repo: o `mcp_servers/` na raiz é dir de DADOS de regras — sem
  `__init__.py`, nunca importado como pacote; `src/mcp_servers/` é o pacote.
  **Hipótese a confirmar pelo Gate #2:** sob `--project` com o cwd no repo efêmero,
  esperamos que o rules-root resolva via `__file__` independente do cwd, sem
  shadowing — o dispatch confirma.)

**Procedimento (pós-merge deste doc + secret configurado):** disparar **um**
`workflow_dispatch` de `lgpd-review.yml`; confirmar os 3 arms PASS no Step Summary.

**Resultado do dispatch:** `<pendente>`
**Run URL / data:** `<pendente>`

Enquanto esta seção estiver com placeholder, o status no topo permanece
"Camada-3-MVP: NAO fechada".

---

## 10. Reprodutibilidade

Comandos replayáveis (mcp-testing.md — evidência reproduzível por qualquer
revisor), a partir da raiz do repo, com `semgrep 1.163.0` no PATH e sessão
autenticada:

```
# Gate local field-scoped, os 3 fixtures (uma rodada):
uv run python -m eval.harness.camada3_gate --case all

# Gate #3 isolado (COMP-001 live, via pytest):
uv run pytest -m live tests/harness/test_camada3_gate_live.py -s

# Lógica de comparação (determinística, sem LLM):
uv run pytest tests/harness/test_camada3_compare.py -q

# CI (Gates #1/#2): workflow_dispatch de .github/workflows/lgpd-review.yml
# (requer secret ANTHROPIC_API_KEY configurado no repositório).
```
