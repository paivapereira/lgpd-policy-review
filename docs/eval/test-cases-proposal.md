# Proposta — Casos de teste da avaliação empírica (frente paralela)

**Branch:** `eval/test-cases-exploratory` (exploratória, descartável; NÃO mergeada).
**Data:** 2026-06-01.
**Escopo:** desenhar e **materializar** o conjunto de casos de teste para a
avaliação empírica do sistema (seção de validação de
`docs/process/relatorio-tcc2-parcial.md` / `docs/DESIGN.md`), onde o software é
avaliado rodando sobre PRs sintéticos. Frente **paralela** à implementação — não
altera o motor; apenas as instâncias de Política de avaliação, vocabulário,
gêmeo GDPR, harness e código sintético.

> **Topologia (B).** O seed do produto `policy/` permanece **POL-000-only** (o
> fallback default do loader; preserva `test_bootstrap.py:91`). As instâncias de
> avaliação são raízes de Política completas sob **`policies/eval-lgpd/`** (LGPD)
> e **`policies/eval-gdpr/`** (GDPR). `eval/` é o **avaliador** (harness,
> catálogo, PRs sintéticos). Ver §7.7.

> **Status de verificação.** Todas as afirmações de comportamento abaixo foram
> **verificadas empiricamente** contra o motor real
> (`src/mcp_servers/policy_reader/tools.py`) pelo gate engine-level
> (`eval/harness/run_engine_cases.py`, **13/13 OK** — §6). Onde não há base no
> contrato, está escrito "não há base no contrato".

---

## 1. A distinção que não pode ser colapsada

| | Política de avaliação (este trabalho) | Fixture pack do policy-reader |
|---|---|---|
| Onde | `policies/eval-lgpd/` (LGPD) + `policies/eval-gdpr/` (GDPR) | `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/` |
| Natureza | **artefato real**, apresentado à banca | fixture de contrato de `check_applicability` |
| Rationale | sim (`policies/eval-lgpd/rationale/POL-00N.md`) | não (README §"Propósito": "não há rationale") |
| Paridade SCHEMA §8 | exigida | "não se aplica a fixtures" (README) |
| `policy_version` | bumpado na instância (0.1.0 → 0.2.0) | "permanece 0.1.0, sem bump" (README) |
| Semântica de `consent_required` | decidida conscientemente (ver §4) | **estrito "exige consent"** — NÃO herdar às cegas |

O pacote `POL-001..POL-004` usa `consent_required` no sentido estrito "exige o
token `consent`" (README §"Tokens"). A Política de avaliação **não herda** essa
escolha sem decidir: ver a decisão de `control` em §4.

### Numbering (sem colisão)

O fixture pack ocupa **POL-001..POL-004** (em `tests/`). A Política de avaliação
**retoma de POL-005** e segue em diante. Justificativa: 001–004 estão
semanticamente ocupados (consent/anonymization/deprecated/not-applicable);
começar em 005 mantém um mapeamento auditável sem sobreposição de números entre
o que é fixture de contrato e o que é Política real. (POL-000 é a definitional
universal, compartilhada — o seed é a fonte canônica; cada instância carrega uma
cópia para autossuficiência do loader.)

---

## 2. Frame respeitado (com citações de contrato)

- **Escopo MVP = só `operation: collection`.** Outras operações →
  `not_applicable` por escopo. *Base:* ADR-0007 D1/D3; `tools.py:313`
  (`if context.operation != "collection": ... NotApplicableVerdict`).
- **Quatro vereditos do Matcher** (`compliant`, `violation_candidate`,
  `indeterminate`, `not_applicable`) + **skip do Triager** (etapa 0, não é
  veredito). *Base:* canonical §4.3; `triager.md` §1.2/§3.1; `matcher.md` §3.2.
- **`check_applicability` recebe UM `clause_id`** e dá veredito sobre AQUELA
  cláusula — não descobre cláusulas. *Base:* canonical §4.3; `tools.py:227`.
  O **Matcher** monta o conjunto candidato lendo `policy://catalog` e varrendo
  **todas as cláusulas `active`** (check-all, `matcher.md` §4.3 DD-M1); se uma
  categoria não é governada por nenhuma substantiva, **todas** retornam
  `not_applicable` e o Matcher seta `requires_human_review=True` (lacuna de
  cobertura, `matcher.md` §4.4 DD-M8) — **verificado** em PROBE-UNGOV-001 (§3).
- **`policy_clause_ref` obrigatório nos quatro vereditos.** *Base:* `matcher.md`
  §3.1 (DD-21); `models.py` (todos os 4 verdict models têm `policy_clause_ref`).
- **Categorias de POL-000 são FUNCIONAIS e neutras de framework**; sensibilidade
  é o booleano `special_category`, não uma categoria. *Base:* POL-000.md §1
  "Princípio metodológico"; SCHEMA §5.3; ADR-0005 D3.

### Semântica do motor (verificada em `tools.py`, lida em 2026-06-01)

`_verdict_for_control` (`tools.py:357-448`):

- `consent_required` → `compliant` **sse** `legal_basis == "consent"`
  (igualdade exata de token); ausente → `violation_candidate` (omissão);
  presente ≠ `consent` → `violation_candidate` (valor não-canônico).
- `anonymization_required` → **sempre `indeterminate`** (o `structured_context`
  não tem campo para declarar transformação efetiva; canonical §7.3).
- qualquer outro `control` → **`raise AssertionError`** (`tools.py:444-448`).

Fail-fast antes do controle (`tools.py:260-331`): formato de id → categorias
não-vazias → categorias ∈ POL-000 → operação ∈ vocab → existência → deprecated →
**definitional → `not_applicable`** (iii) → **operação ≠ collection →
`not_applicable`** (i, MVP) → **mismatch de `applies_to` → `not_applicable`**
(ii) → controle.

---

## 3. Catálogo de casos (por desfecho)

Os QUATRO campos do Classifier estão na coluna *Classifier* na ordem
`operation_type × data_categories × declared_legal_basis × declared_transformations`.
O Matcher projeta `operation_type→operation`, `declared_legal_basis→legal_basis`
e **descarta** `declared_transformations` antes da tool (`matcher.md` §2.3). A
coluna **obtido (pipeline)** está **vazia** de propósito — preenchida só na
execução do pipeline completo (LLM + MCP). A coluna **regra** cita o ponto do
motor que produz o veredito. **Construtibilidade** declara se é expressável com
o contrato atual.

> O resultado **engine-level** (gate determinístico) de cada caso está em §6 —
> distinto da coluna "obtido (pipeline)", que aguarda a execução LLM.

### 3.1 Descartado pelo Triager (etapa 0 — não é veredito)

| ID | Descrição | Classifier | Cláusula | Esperado + regra | obtido (pipeline) | Construtibilidade |
|---|---|---|---|---|---|---|
| SKIP-001 | PR só de documentação | n/a (antes do Detector) | nenhuma | `skip` (Triager); coordinator → Reporter, `run_outcome: skipped_by_triager`; **sem veredito** | | Construível **só no pipeline** (Triager é LLM). Não exercitável pelo harness engine-level. *Base:* `triager.md` §3.1; `coordinator.md` run_outcome. |

### 3.2 compliant

| ID | Descrição | Classifier | Cláusula | Esperado + regra | obtido (pipeline) | Construtibilidade |
|---|---|---|---|---|---|---|
| COMP-001 | Coleta de identificação com consentimento | `collection × [dados_de_identificacao] × consent × []` | POL-005 | `compliant` — `consent_required` + `legal_basis=="consent"` (`tools.py:383`) | | Construível. |

### 3.3 violation_candidate

| ID | Descrição | Classifier | Cláusula | Esperado + regra | obtido (pipeline) | Construtibilidade |
|---|---|---|---|---|---|---|
| VIOL-001 | Coleta de identificação **sem base legal** (vitrine E2E) | `collection × [dados_de_identificacao] × null × []` | POL-005 | `violation_candidate` (omissão), `contradicted_requirement: R1` (`tools.py:396`) | | Construível. É o "violação plantada" do critério E2E (DESIGN.md:53). |
| VIOL-002 | Coleta de identificação com base ≠ consent | `collection × [dados_de_identificacao] × legitimate_interests × []` | POL-005 | `violation_candidate` (valor não-canônico) (`tools.py:410`) | | Construível. |

### 3.4 indeterminate

| ID | Descrição | Classifier | Cláusula | Esperado + regra | obtido (pipeline) | Construtibilidade |
|---|---|---|---|---|---|---|
| INDET-001 | Coleta de perfil comportamental (anonimização não observável) | `collection × [dados_de_perfil_comportamental] × null × []` | POL-006 | `indeterminate` — `anonymization_required` sempre indeterminado (`tools.py:425`); `verification_scope.dimension=upstream_state` | | Construível. **Indeterminate genuíno** (RF-005). |

### 3.5 not_applicable

| ID | Descrição | Classifier | Cláusula | Esperado + regra | obtido (pipeline) | Construtibilidade |
|---|---|---|---|---|---|---|
| NA-MVP-001 | Operação `storage` (≠ collection) | `storage × [dados_de_identificacao] × consent × []` | POL-005 | `not_applicable` (i, escopo MVP) (`tools.py:313`; ADR-0007 D3) | | Construível. |
| NA-MISMATCH-001 | Categoria fora do `applies_to` (contato vs identificação) | `collection × [dados_de_contato] × consent × []` | POL-005 | `not_applicable` (ii, mismatch) (`tools.py:322`) | | Construível. |
| NA-DEF-001 | Avaliar POL-000 (definitional) | `collection × [dados_de_identificacao] × consent × []` | POL-000 | `not_applicable` (iii, definitional) (`tools.py:300`) | | Construível. Piso de cardinalidade do sweep. |

### 3.6 Sondas de fronteira (edge)

| ID | Descrição | Classifier | Cláusula | Esperado + regra | obtido (pipeline) | Construtibilidade |
|---|---|---|---|---|---|---|
| B-FALSEPOS-001 | Identificação com base **válida** não-consent (contract_performance, Art. 7º V) | `collection × [dados_de_identificacao] × contract_performance × []` | POL-005 | `violation_candidate` — **falso positivo** do `consent_required` estrito (`tools.py:410`) | | Construível. Motiva ADR-0015 (ver §4/§7). |
| B-SENS-OK-001 | Saúde (sensível) com base **comum** `consent` | `collection × [dados_de_saude] × consent × []` | POL-007 | `compliant` no motor — **gate de sensibilidade AUSENTE** (motor não consome `category`; `matcher.md` §8.3) | | Construível; juridicamente frágil (Art. 11 exige base sensível). |
| B-SENS-INV-001 | Saúde com base sensível **correta** `explicit_consent` (Art. 11 I) | `collection × [dados_de_saude] × explicit_consent × []` | POL-007 | `violation_candidate` no motor — **INVERSÃO** (a base correta é punida: `explicit_consent != "consent"`) | | Construível. Revela a sub-modelagem do Art. 11. |

> **Nota — `lawful_basis_required` (POL-008) não é caso de catálogo.** O controle
> proposto não é implementado pelo motor (`AssertionError`); seu caso de
> demonstração foi **removido do catálogo** na topologia B e vive staged em
> `eval/proposed/POL-008.yaml`, fora de toda raiz carregada. É evolução (§4,
> ADR-0015), não um caso de avaliação do MVP. Ver §7.8.

### 3.7 Sonda: categoria não-governada (policy_clause_ref órfão?)

| ID | Descrição | Classifier | Cláusula | Esperado + regra | obtido (pipeline) | Construtibilidade |
|---|---|---|---|---|---|---|
| PROBE-UNGOV-001 | Coleta de `dados_de_localizacao` — **nenhuma** cláusula governa (sonda mantida de propósito) | `collection × [dados_de_localizacao] × consent × []` | nenhuma (sweep) | **`coverage_gap`** — todas as active → `not_applicable`; Matcher seta `requires_human_review` (`matcher.md` DD-M8) | | Construível. **Descoberta:** §7.2. |

### 3.8 Swap GDPR (muda de veredito por vocabulário, não por código)

| ID | Descrição | Classifier | Cláusula | Esperado + regra | obtido (pipeline) | Construtibilidade |
|---|---|---|---|---|---|---|
| SWAP-001-LGPD | Identificação + consentimento, raiz `policies/eval-lgpd/` | `collection × [dados_de_identificacao] × consent × []` | POL-005 (LGPD) | `compliant` (`consent`==token) | | Construível. |
| SWAP-001-GDPR | **Mesmo código**, raiz `policies/eval-gdpr/` | `collection × [dados_de_identificacao] × consent_gdpr × []` | POL-005 (GDPR) | `violation_candidate` — vocab GDPR nomeia consentimento `consent_gdpr`; motor (`== "consent"`) rejeita | | Construível. **Flip por vocabulário de base legal.** Revela acoplamento do token `consent` ao LGPD (§7.4). |

Cobertura: os quatro vereditos (COMP/VIOL/INDET/NA) + skip do Triager (SKIP-001).
Tudo construível exceto SKIP-001 (pipeline-only). `lawful_basis_required` (POL-008)
é evolução staged fora do catálogo (§4, §7.8), não um caso de avaliação.

---

## 4. Decisão sobre o enum de `control` (Passo 4)

**Problema.** O fixture pack usa `consent_required` no sentido estrito "exige o
token `consent`". Mas vários casos compliant declaram bases variadas
(`legal_obligation`, `contract_performance`) que são **bases válidas do Art. 7º**
e deveriam ser conformes — o que `consent_required` não exprime. Verificado:
B-FALSEPOS-001 (`contract_performance` → `violation_candidate`).

**Decisão (materializada, a ratificar).** Introduzir um terceiro `control`,
**`lawful_basis_required`**: a coleta exige **alguma** base legal válida, com um
**gate comum-vs-sensível derivado de `special_category`** (categoria sensível
exige base do Art. 11). Materialização **na topologia B**:

- **NÃO** entra em nenhum vocab `control.yaml` carregado (nem o seed `policy/`,
  nem `policies/eval-lgpd/`, nem `policies/eval-gdpr/`). Razão: o loader **não**
  valida `control` contra o vocab e `SubstantiveClause.control` é `str` livre
  (`models.py:141`); pôr o token num vocab carregado seria um foot-gun (uma
  cláusula que o use crasha o sweep com `AssertionError`);
- decisão e **mudança de motor necessária** registradas em **ADR-0015** (Status:
  Proposed; rationale a ratificar pelo redator; §2 da ADR traz o sketch da
  branch nova de `_verdict_for_control`);
- cláusula de demonstração **POL-008** autorada em `eval/proposed/` — **FORA** do
  catálogo de avaliação (`eval/cases.yaml`) e de toda raiz carregada.

**Construtibilidade da decisão.** O token no vocabulário é dado; a **semântica do
veredito vive em código** (`_verdict_for_control`). Logo `lawful_basis_required`
**não é construível** sem a mudança de motor de ADR-0015. Esta é a fronteira
"vocabulário é dado, veredito é código" — a descoberta central do Passo 4.

---

## 5. Mudanças materializadas nesta branch (topologia B)

### 5.1 Seed do produto `policy/` — RESTAURADO a POL-000-only
- Permanece o seed: `clauses/POL-000.yaml`, `rationale/POL-000.md`, `SCHEMA.md`,
  `policy.yaml` (0.1.0), `vocabularies/LGPD/{control,lawful_basis,operation,out_of_scope}.yaml`.
- `policy.yaml` e `control.yaml` restaurados a `main` (`git checkout main -- ...`);
  as eval clauses saíram de `policy/`. Preserva `test_bootstrap.py:91` e o estado
  "bundled = POL-000 only" do CLAUDE.md.

### 5.2 Instância LGPD de avaliação (`policies/eval-lgpd/` — raiz completa)
- **+** `clauses/{POL-005,POL-006,POL-007}.yaml` (+ `rationale/POL-00N.md`) —
  consent_required (identificação), anonymization_required (perfil),
  consent_required (saúde, sensível).
- **+** `clauses/POL-000.yaml` + `vocabularies/LGPD/*` — **cópias do seed** para
  autossuficiência do loader (POL-000 e os 4 vocabs precisam estar na raiz).
- **+** `policy.yaml` — `policy_version: 0.2.0` (legítimo na instância; o seed
  fica 0.1.0).

### 5.3 Instância GDPR de avaliação (`policies/eval-gdpr/` — raiz completa)
- **+** `policy.yaml` (legal_framework GDPR), `clauses/POL-000.yaml` (categorias
  **reusadas**, re-ancoradas em GDPR), `clauses/POL-005.yaml`,
  `vocabularies/GDPR/{operation,lawful_basis,control,out_of_scope}.yaml`.
  `lawful_basis` usa **`consent_gdpr`** (driver do flip); `control.yaml` sem
  `lawful_basis_required` (consistente com o seed).

### 5.4 Proposta bloqueada por motor (`eval/proposed/`)
- **+** `POL-008.yaml` (+ `POL-008.rationale.md`) — `lawful_basis_required`;
  staged, FORA do catálogo e de toda raiz carregada.

### 5.5 ADR
- **+** `docs/adr/0015-control-vocabulary-lawful-basis-required.md` (Proposed).

### 5.6 Avaliador (`eval/`)
- **+** `cases.yaml` (catálogo máquina-legível; roots `eval-lgpd`/`eval-gdpr`),
  `harness/run_engine_cases.py` (harness determinístico de **duas camadas**:
  veredito + Reports consolidados), `harness/README.md`, `harness/gate_run.json`
  (evidência do gate de veredito).
- **+** `harness/reports/<CASE>.report.json` — Reports consolidados VÁLIDOS
  (validados contra `ReportPayload`), montados reusando as derivações do
  coordinator (`derive_run_outcome`/`aggregate_summary`/`_build_consolidated_state`)
  sobre os findings do motor, **sem LLM** (ver §6).
- **+** `prs/{COMP-001,VIOL-001,INDET-001,SWAP-001,PROBE-UNGOV-001,SKIP-001}/` —
  código sintético (Django, SQLAlchemy, Pydantic, FastAPI, payloads) com gatilhos
  BR reais; o `.expected-report.json` de cada PR é um Report **válido** gerado
  pelo harness (não mais o formato `findings_assert` inventado).

### 5.7 Documentação
- **+** este arquivo (`docs/eval/test-cases-proposal.md`).

**Não houve:** merge, commit na main, PR, alteração de `src/` (motor), alteração
de POL-000, alteração do seed `policy/` além da restauração ao estado de `main`.

---

## 6. Gate de construtibilidade (engine-level) — VERIFICADO

`uv run python eval/harness/run_engine_cases.py` → **13/13 cases engine-runnable
OK** (1 pipeline-only pulado: SKIP-001). Resultado obtido == esperado para todos.
Evidência persistida em `eval/harness/gate_run.json`. Isto **verifica** (não
infere) a coluna "regra" do catálogo; a coluna "obtido (pipeline)" permanece
vazia (full pipeline LLM+MCP não rodado, por instrução).

```
COMP-001 compliant · VIOL-001/002 violation_candidate · INDET-001 indeterminate
NA-MVP/MISMATCH/DEF not_applicable · B-FALSEPOS violation_candidate
B-SENS-OK compliant · B-SENS-INV violation_candidate
PROBE-UNGOV coverage_gap · SWAP-LGPD compliant · SWAP-GDPR violation_candidate
```

PROBE-UNGOV-001 detalhe (sweep): POL-000/005/006/007 **todas** `not_applicable`
→ `coverage_gap`. Nenhum `policy_clause_ref` órfão (cada finding referencia a
cláusula avaliada; POL-000 é o backstop sempre presente).

### 6.1 Reports consolidados (camada 2 — sem LLM)

O mesmo harness monta **Reports consolidados reais** sem o modelo, reusando as
funções do coordinator (importadas, nunca reimplementadas — fonte de verdade
única): para cada candidato LGPD, varre as cláusulas active, monta um `Finding`
por par, e chama `derive_run_outcome` + `aggregate_summary` +
`_build_consolidated_state` (`src/coordinator/run.py`), validando contra
`ReportPayload` (o inputSchema de `emit_report`). **10/10 Reports válidos**,
emitidos em `eval/harness/reports/<CASE>.report.json` (e no `.expected-report.json`
de cada PR sintético).

- **run_outcomes cobertos sem modelo:** `success_with_findings`,
  `success_all_not_applicable`. **Pipeline-only:** `skipped_by_triager` (precisa
  do Triager) e `success_no_candidates` (precisa o Detector achar zero).
- **GDPR não emite Report no MVP:** `Finding`/`ReportPayload` fixam
  `legal_framework: Literal["LGPD"]` — o Report consolidado é LGPD-locked; o
  *veredito* GDPR (SWAP-001-GDPR) continua coberto pelo gate. Achado a registrar
  (mesma família de minor-bump do ADR-0007).
- **Baseline da inversão POL-007:** os Reports `B-SENS-OK` (compliant) e
  `B-SENS-INV` (violation_candidate) documentam empiricamente a sub-modelagem do
  Art. 11 ANTES da correção (ADR-0015) — é o baseline contra o qual o laudo
  pós-correção será comparado.
- `report_id` (uuid4) é o único campo não-determinístico; comparações de baseline
  devem ignorá-lo. Locus do finding (file/line/snippet/rule_id) é sintético no
  harness engine-level; a camada de veredito é real.

---

## 7. Tensões e decisões em aberto (NÃO resolvidas — dependem de você)

### 7.1 Gate de sensibilidade (cláusula sabe exigir base sensível p/ `special_category=true`?)
**Hoje: não.** O motor avalia `consent_required` por igualdade contra `consent`
e **não consome** `category` de `lawful_basis` (`matcher.md` §8.3; verificado em
B-SENS-OK / B-SENS-INV — o motor aceita `consent` comum p/ saúde e **rejeita** o
`explicit_consent` correto). Opções: (a) implementar `lawful_basis_required` com
o gate (ADR-0015); (b) manter o débito documentado e avaliar saúde só por
`consent_required` estrito (assumindo a inversão); (c) fazer o motor consumir
`category` mesmo em `consent_required`. **Trade-off:** (a) é o mais correto mas
exige mudança de motor (sai do MVP "parado"); (b) é honesto mas frágil à banca;
(c) muda a semântica de uma cláusula existente. **Decisão sua.**

### 7.2 Categoria não-governada (policy_clause_ref órfão — o que a sonda revelou)
A sonda PROBE-UNGOV-001 revelou que **não há órfão**: o Matcher tem comportamento
**definido** (todas `not_applicable` → `coverage_gap` + `requires_human_review`),
e cada finding referencia a cláusula avaliada (POL-000 incluso). A **fragilidade
real** é dupla: (i) a lacuna é um sinal **agregado** (todas `not_applicable`) —
nenhum finding isolado distingue "categoria não-governada" de "mismatch com
cláusula existente"; (ii) com o seed bundled = só POL-000, **todo** candidato de
coleta seria `coverage_gap`, tornando o sinal vazio — só deixa de ser vazio numa
instância com substantivas (como `policies/eval-lgpd/`). **Decisão:** manter a
sonda como está (já é a sua decisão) e decidir se o `reason` da lacuna deve ser
distinguível por máquina (hoje é só prosa). **Não "consertei" criando cláusula de
localização.**

### 7.3 PII real em fixture de teste
Todo CPF/dado nos PRs sintéticos é **sintético** (ex.: `"000.000.000-00"`), por
`.claude/rules/privacy-safety.md`. **Decisão sua:** se quiser PRs mais realistas
para a banca, definir uma convenção de valores sintéticos válidos-em-formato
(checksum-válido mas não atribuíveis) — ou manter placeholders. Recomendo manter
sintético; nunca PII real.

### 7.4 Acoplamento do token `consent` ao LGPD no motor (revelado pelo swap)
O motor compara `legal_basis == "consent"` (literal LGPD). O gêmeo GDPR nomeia o
consentimento `consent_gdpr`, então **nenhuma** cláusula `consent_required` do
GDPR retorna `compliant` (SWAP-001-GDPR → violation). Isso **faz o swap funcionar**
(flip de veredito), mas é também um achado: o motor **não** é totalmente
framework-agnóstico no controle (canonical afirma agnosticismo via vocab; o
controle `consent_required` é hardcoded ao token LGPD). **Decisão sua:** (a) aceitar
como propriedade do MVP (o gêmeo é prova de conceito de swap de dados, e o flip é
didático); (b) generalizar o motor para ler o "token de consentimento" do vocab
por jurisdição; (c) nomear o consentimento GDPR como `consent` (sem flip — mas aí
o caso de swap precisa de outro mecanismo). Hoje materializei (a)+(c-invertido):
`consent_gdpr` para produzir o flip pedido.

### 7.5 Cláusula deprecated na Política de avaliação (sim/não)
**Não autorei nenhuma.** Trade-offs: (a favor) exercita tombstone em `get_clause`
e `CLAUSE_DEPRECATED` em `check_applicability`; (contra) o sweep do Matcher só
enumera `active` (`matcher.md` §4.3), então uma deprecated **nunca** entra no
caminho nominal de veredito — só seria exercitada por chamada direta; e o fixture
pack já cobre deprecation (POL-003). **Decisão sua:** autorar POL-009 deprecated
(p.ex. sucessora de POL-005) em `policies/eval-lgpd/` se quiser exercitar a
máquina de deprecação na instância real; caso contrário, deixar para o fixture pack.

### 7.6 Cobertura de tokens de operação não-collection em `operation.yaml`
`operation.yaml` tem 22 tokens; o MVP avalia só `collection` (ADR-0007). Os outros
21 só aparecem como `not_applicable` (i) — exercitado por NA-MVP-001 (`storage`).
**Decisão sua:** (a) deixar como está (um token não-collection basta para o caso
i); (b) autorar uma cláusula governando uma operação não-collection (ADR-0007 D2
permite: a Política retém cláusulas de operações não avaliadas) para demonstrar
que a Política é mais ampla que o MVP — útil à banca, mas a cláusula nunca produz
veredito substantivo no MVP.

### 7.7 Topologia seed vs instância (RESOLVIDO nesta sessão)
A primeira materialização pôs as eval clauses em `policy/`, o que quebrava
`test_bootstrap.py:91` (`== {"POL-000"}`) e confundia **produto** (seed) com
**instância de cliente**. **Resolvido (topologia B, decidido com você):** o seed
`policy/` volta a POL-000-only (preserva o teste e o estado CLAUDE.md, **sem
editar o teste**); as instâncias de avaliação vivem em `policies/eval-lgpd/` e
`policies/eval-gdpr/`; o harness aponta `POLICY_READER_ROOT` para elas. O gêmeo
GDPR já tinha de viver fora de `policy/` (um framework por instância), então a
topologia é simétrica. **Em aberto para você (futuro, não bloqueante):** se uma
instância de cliente real entra versionada em `policies/<cliente>/` no repo ou
fora dele (dado potencialmente sensível — cf. `data/raw/`, `evaluation/private/`).

### 7.8 Casos concluídos como NÃO construíveis
- **`lawful_basis_required` / POL-008**: não construível sem mudança de motor
  (ADR-0015). Por isso POL-008 está staged em `eval/proposed/`, **fora do
  catálogo** — é prova de conceito da evolução, não um caso de avaliação do MVP
  (na rodada anterior era o caso `B-ENGINEGAP-008`; removido na topologia B).
- **SKIP-001** (Triager skip): construível **só no pipeline** (Triager é LLM);
  não exercitável pelo harness engine-level.
- **Pós-MVP — compliant/violation de anonimização:** o `structured_context` não
  tem campo de transformação declarada, então `anonymization_required` **nunca**
  produz `compliant`/`violation_candidate`, só `indeterminate` (fixture README
  "assimetrias deliberadas"; canonical §4.3). Construir esses exigiria estender o
  inputSchema da tool — fora do contrato atual.

---

## 8. Como inspecionar e como rodar

Ver `eval/harness/README.md`. Resumo: `uv run python eval/harness/run_engine_cases.py`
(determinístico, roda hoje, 13/13); o pipeline completo (LLM+MCP) está documentado
e preenche a coluna "obtido (pipeline)" quando executado, com `POLICY_READER_ROOT`
escolhendo LGPD (`policies/eval-lgpd/`) ou GDPR (`policies/eval-gdpr/`).
