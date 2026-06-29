<!--
RELATÓRIO DE GARANTIA DE QUALIDADE (QA) — MVP lgpd-policy-review (fonte Markdown)
Este documento é um relatório de QA do produto mínimo viável: compila a evidência de
verificação produzida ao longo do projeto (testes automatizados, smoke tests de framework,
avaliação empírica), os portões de qualidade aprovados, os defeitos descobertos e corrigidos,
a matriz de cobertura requisito->evidência e uma revisão cross-doc de consistência.

Convenções:
- Português do Brasil (ADR-0001 Decisão 3 — saídas voltadas a leitor humano).
- Artefatos do próprio repositório citados por caminho/nome + seção (`caminho/arquivo.py`).
- Números de teste e de portão são empíricos: re-executados ou lidos da evidência versionada
  no repositório na data efetiva (ver §0). Quando a fonte é evidência live já registrada
  (não re-executada nesta rodada), o texto o declara explicitamente.
- Identificadores de achado cross-doc (XDOC-NN) são estáveis nesta versão do relatório.
- Este relatório APONTA divergências cross-doc; não edita os documentos da tese. As correções
  propostas ficam registradas como insumo para uma sessão de housekeeping dedicada.
-->

# Relatório de Garantia de Qualidade (QA) — Produto Mínimo Viável `lgpd-policy-review`

**Autor:** João Guilherme de Mello Paiva Pereira
**Projeto:** `lgpd-policy-review` — *code review* automatizado de conformidade com Política de Proteção de Dados versionada (TCC, Engenharia de Software — UTFPR)
**Tipo de documento:** Relatório de QA (compilação de evidência de verificação + revisão cross-doc)
**Data efetiva:** 5 de junho de 2026
**Revisão:** 28 de junho de 2026 — inventariada a investigação de robustez a modelo (ablação por estágio) como experimento exploratório (Quadro 9 e §Fontes primárias de evidência). O corpo do relatório com data efetiva de 5 de junho não foi re-verificado nesta revisão.
**Estado do sistema avaliado:** MVP com as três camadas implementadas; guarda *fail-loud* de `legal_framework` mergeada (PR #112, *commit* `05d8a18`).

---

## 0. SUMÁRIO EXECUTIVO DE QUALIDADE

Este relatório compila e audita a evidência de qualidade do MVP. O veredito de QA, no nível de produto mínimo viável, é **aprovado com ressalvas declaradas**: as três camadas estão implementadas, exercitadas de ponta a ponta e cobertas por uma suíte de regressão verde; as ressalvas são fronteiras de escopo deliberadas e débitos de baixo risco — todas documentadas, nenhuma silenciosa.

**Indicadores de qualidade, verificados na data efetiva (Quadro 0).**

| Indicador | Resultado | Fonte |
| :--- | :--- | :--- |
| Suíte automatizada `pytest` (padrão) | **307 *passed*, 2 *deselected*** (374 s) | re-execução nesta rodada |
| Testes coletados (incluindo `live`) | **309** | `pytest --collect-only` |
| `ruff check src tests` | **limpo** | re-execução nesta rodada |
| `ruff check .` (repositório inteiro) | 3 *F401* (imports não usados) em `scripts/smoke_tests/` — probes exploratórios, auto-corrigíveis | re-execução nesta rodada |
| `ruff format --check` | **não limpo** — 114 arquivos reformatáveis (débito aberto, §6.3) | re-execução nesta rodada |
| `mypy --strict` | **Success: no issues found in 46 source files** | re-execução nesta rodada |
| Motor determinístico de avaliação (`eval/harness/gate_run.json`) | **13/13 casos *engine-runnable* com *match*** (SKIP-001 é *pipeline-only*) | evidência versionada |
| Portões de marco (A, B, Camada-3 local K=2, Camada-3 CI) | **4/4 PASS** | `docs/process/milestone{A,B}.md`, `camada3-mvp.md` |

**O que está sólido.** A camada de fundação (Política + dois servidores MCP) e a camada multiagente (coordenador + cinco subagentes) estão cobertas por 309 testes verdes, `mypy --strict` limpo e quatro portões de marco aprovados, incluindo uma execução de CI ao vivo (`workflow_dispatch` *run* 26983111920). A lógica de quatro vereditos do motor de conformidade converge campo a campo entre execuções independentes (Camada-3 local, K=2). Os seis reconhecedores brasileiros são exercitados positiva e negativamente contra Semgrep real.

**Ressalvas declaradas (todas detalhadas adiante).**
1. **Independência jurisdicional é demonstrada no nível da decisão, não do Report.** A troca LGPD→GDPR inverte o veredito na superfície da ferramenta `check_applicability`, mas o Report consolidado é travado em `legal_framework: Literal["LGPD"]`, e a guarda *fail-loud* (#112) **recusa** emitir Report sob *framework* não-LGPD em vez de rotulá-lo errado (RF-008 parcial no nível do Report; §7, achado XDOC-01).
2. **Inversão de sensibilidade na POL-007 (Art. 11 LGPD)** é um limite real do motor, diagnosticado com causa-raiz e correção projetada, deixado como trabalho futuro por decisão de escopo (§6.2).
3. **Posicionamento informativo** cobre o caminho *Step Summary* (`workflow_dispatch`); o comentário *inline* em *pull request* de produção está diferido a Milestone D (`if: false`).
4. **Cross-doc:** 16 divergências de documentação identificadas (4 ALTA, 8 MEDIA, 4 BAIXA), a principal sendo a promessa de "Report válido sob GDPR" no relatório parcial §2.5, que a guarda #112 contradiz (§8).

**Nota de método deste relatório.** A compilação de evidência (inventário de `tests/`, `scripts/`, `eval/`; arqueologia de defeitos; matriz de cobertura; revisão cross-doc) foi conduzida por um conjunto de agentes de leitura que examinaram os artefatos reais do repositório, e cada afirmação factual aqui foi confrontada contra o arquivo-fonte (princípio `verification-before-inference`). Os números de portão de qualidade estática do Quadro 0 foram re-executados localmente nesta rodada.

**Lista de quadros.** Quadro 0 — Indicadores de qualidade. Quadro 1 — Testes automatizados por área. Quadros 2–6 — Inventário por camada. Quadro 7 — Smoke tests de framework. Quadro 8 — Casos do motor de avaliação. Quadro 9 — Experimentos empíricos. Quadro 10 — Portões de marco. Quadro 11 — Portão de qualidade estática. Quadro 12 — Defeitos corrigidos. Quadro 13 — Matriz de cobertura RF/RNF. Quadro 14 — Achados cross-doc.

**Siglas.** ADR — *Architecture Decision Record*; CI — Integração Contínua; LGPD — Lei Geral de Proteção de Dados; GDPR — *General Data Protection Regulation*; MCP — *Model Context Protocol*; MVP — Produto Mínimo Viável; PR — *Pull Request*; RF/RNF — Requisito Funcional/Não-Funcional; SDK — *Software Development Kit*.

---

## 1. OBJETIVO E ESCOPO DO RELATÓRIO

### 1.1 Objetivo

Este relatório responde a três perguntas de QA sobre o MVP, na ordem:

a) **O que foi testado e como?** — compilar o inventário completo de verificação produzido durante o projeto, distribuído por três superfícies: a suíte automatizada (`tests/`), os *smoke tests* de framework (`scripts/`) e a avaliação empírica (`eval/`).

b) **A qualidade foi atestada por portões reproduzíveis?** — consolidar os portões de marco aprovados e o portão de qualidade estática, com a evidência reproduzível de cada um.

c) **A documentação é consistente com o código?** — uma revisão cross-doc que confronta o que os documentos afirmam contra a realidade atual do repositório, registrando divergências como achados com correção proposta.

A pergunta complementar **"o que ainda não está coberto?"** é respondida honestamente em duas frentes: a matriz de cobertura requisito→evidência (§7), que marca cada RF/RNF como *full*, *partial*, *indirect* ou *deferred* com nota de lacuna; e o registro de defeitos e limites conhecidos (§6).

### 1.2 Escopo e fronteiras

Está **dentro** do escopo: inventário de testes, portões, defeitos corrigidos e limites conhecidos, matriz de cobertura e revisão cross-doc. Está **fora** do escopo: a edição dos documentos da tese (a revisão cross-doc aponta achados e propõe correções, mas não as aplica — decisão registrada no cabeçalho); a re-execução dos testes `live` que consomem chave de API (a evidência live é citada da que já está versionada no repositório, não re-executada); e a calibração quantitativa de taxa de falsos positivos, que o próprio MVP delimita como trabalho futuro.

---

## 2. ESTRATÉGIA DE VERIFICAÇÃO

A verificação do projeto opera em duas dimensões ortogonais — **escopo** (o que cada portão valida) e **camada de evidência** (quão forte é a observação) —, e adota um arranjo de revisão entre instâncias.

### 2.1 Dois escopos de verificação (ADR-0008)

- **Escopo de tarefa.** Cada unidade de trabalho é validada por testes automatizados (`pytest`) e por revisão independente. Os testes atestam a correção de funções e contratos isolados.
- **Escopo de marco.** Ao fechar um marco, um exercício funcional valida cada critério de aceitação (Dado/Quando/Então) pela superfície canônica do componente — para servidores MCP, via cliente MCP real. Atesta a capacidade externamente observável, que os testes de unidade não exercem por construção.

### 2.2 Três camadas de evidência

A distinção entre **reprodutibilidade** e **determinismo** exige separar três superfícies de execução, de força crescente (taxonomia consolidada em `docs/eval/avaliacao-secao-rascunho-numero-independente.md`):

1. **Replay** — comparação de uma saída contra um *baseline* committado. Atesta regressão (a saída não mudou), não comportamento.
2. **Motor determinístico sobre entrada pré-classificada** — execução de `check_applicability` sobre uma classificação fornecida. Atesta o *flip* de veredito **dada** uma classificação fixa, mas assume a estabilidade da classificação a montante.
3. **Pipeline *live* sobre o código real** — execução da cadeia completa (Triager→Detector→Classifier→Matcher→Reporter) sobre o trecho de código. É a única camada que mede o comportamento do agente de ponta a ponta, inclusive a estabilidade da classificação.

Esta separação é central ao relatório: afirmações de estabilidade só são defensáveis na terceira camada, e o motivo pelo qual certos casos resistem ao portão estrito é, ele mesmo, um resultado (§9).

### 2.3 Arranjo gerador–revisor

As especificações são redigidas em uma instância e revisadas por outra independente; o código é implementado em uma instância e revisado por outra. O arranjo capturou defeitos materiais antes da incorporação ao repositório — empiricamente, o portão de marco da Milestone A descobriu quatro defeitos que a suíte de 53 testes verdes não pegava (§4). Este próprio relatório de QA é uma instância de revisão independente do conjunto do trabalho.

---

## 3. INVENTÁRIO DE TESTES

Esta seção é o núcleo do relatório: compila as três superfícies de teste do projeto.

### 3.1 Suíte automatizada (`tests/`) — 309 testes

A suíte coleta **309** testes; **307** rodam por padrão e **2** (marcados `live`) são desmarcados via `addopts = -m 'not live'` no `pyproject.toml`, por exigirem sessão autenticada do Claude Agent SDK e Semgrep no PATH. Distribuição por área:

**Quadro 1 — Testes automatizados por área**

| Área | Arquivos | Testes | Cobre |
| :--- | :---: | :---: | :--- |
| `tests/mcp_servers/` (Camada 1+2 — servidores MCP) | 8 | **142** | `policy-reader` (55) + `semgrep-runner` (87) |
| `tests/coordinator/` (Camada 2 — orquestrador) | 14 | **85** | pipeline de encadeamento determinístico + drivers + derivações |
| `tests/subagents/` (Camada 2 — subagentes) | 13 | **62** | contratos de I/O dos cinco subagentes |
| `tests/ci/` + `tests/harness/` (Camada 3 — CI) | 4 | **20** | *entrypoint* CI + lógica de comparação do portão |
| **Total** | **39** | **309** | (307 padrão + 2 `live`) |

#### 3.1.1 Camada 1+2 — `policy-reader` MCP (55 testes)

O servidor de acesso estruturado à Política. Cobre o contrato *fail-loud* do *loader* e a matriz de quatro vereditos.

**Quadro 2 — `tests/mcp_servers/policy_reader/`**

| Arquivo | Testes | Cobre |
| :--- | :---: | :--- |
| `test_bootstrap.py` | 11 | Carga *fail-loud* (toda condição de Política malformada aborta com mensagem em pt-BR nomeando o artefato); versionamento de dois eixos + `compatible_schema_range`; *handshake* `policy://schema-version` (AS-1..AS-8) |
| `test_check_applicability.py` | 17 | Matriz de quatro vereditos (`compliant`/`violation_candidate`/`indeterminate`/`not_applicable`) sobre POL-001..004; `indeterminate` carrega `verification_scope` (não fabrica veredito); envelopes de erro Opção B; trinca de proveniência em todo caminho de veredito |
| `test_get_clause.py` | 9 | Recuperação de cláusula com *payload* polimórfico (definitional/substantive/deprecated-com-tombstone); envelopes `INVALID_CLAUSE_ID_FORMAT`/`CLAUSE_NOT_FOUND`; forma canônica da chamada FastMCP 3.2.4 |
| `test_find_clauses.py` | 7 | *Matching* prefix-hierárquico por {lei, artigo, inciso}; exclusão de *deprecated*; lista vazia é sucesso; envelope `INVALID_LAW_IDENTIFIER`; invariante anti-uniformização (tipo de cláusula polimórfico) |
| `test_resources.py` | 11 | Recursos read-only `policy://catalog` (ordem natural, cinco campos, `successors` sse *deprecated*) e `policy://vocabularies` (quatro vocabulários jurisdicionais + `data_categories` estrutural, *framework-agnostic*); idempotência byte-a-byte |

#### 3.1.2 Camada 2 — `semgrep-runner` MCP + reconhecedores BR (87 testes)

O servidor de detecção sintática e os seis reconhecedores brasileiros — o diferencial técnico do trabalho.

**Quadro 3 — `tests/mcp_servers/semgrep_runner/`**

| Arquivo | Testes | Cobre |
| :--- | :---: | :--- |
| `test_recognizers_br.py` | 49 | **RF-002.** Os seis reconhecedores (`br-cpf`/`cnpj`/`cnh`/`nis-pis`/`titulo-eleitor`/`cns-saude`) detectados positivamente (um contexto sintático validado por *Latin-square* cada); três fixtures negativas (literais `re.compile`; constantes UUID/ISO/número-de-pedido; strings com forma de identificador reusadas como versão/release) → zero achados; anti-*cross-talk* de 30 parametrizações; nomenclatura kebab-case; esquema de severidade (`br-cns-saude` = ERROR, Art. 11 sensível) |
| `test_scan_diff.py` | 29 | **RF-001.** Scan sensível a *diff* (`--baseline-commit`) com proveniência/localização/snippet; os seis `errorCode` canônicos (§5.4) sob Opção B; ordenação determinística; idempotência; trinca de proveniência; transporte stdio; endurecimento Windows (AS-13/AS-14b); normalização de `rule_id` (T-G3) |
| `test_bootstrap.py` | 9 | Contrato *fail-loud* do *loader* de regras; hash determinístico `rules_version` (sensível a conteúdo+nome); descrição da tool byte-idêntica à *spec* (AS-1..AS-7) |

#### 3.1.3 Camada 2 — subagentes (62 testes)

Trava o contrato de I/O dos cinco subagentes em duas altitudes: âncoras de modelo (Fase-0, formas de saída estruturada Pydantic) e âncoras de prompt/hook (Fase-2). Invariante dominante: segurança de saída estruturada (formas *enum-tag*, **nunca** `oneOf`/discriminador — uma união na raiz desliga silenciosamente a decodificação restrita do SDK; `extra='forbid'`; vocabulário sem valor de PII no esquema).

**Quadro 4 — `tests/subagents/`**

| Arquivo | Testes | Subagente / Cobre |
| :--- | :---: | :--- |
| `triager/test_triager_models.py` | 4 | **Triager.** XOR direcional proceed↔`relevance_summary` / skip↔`skip_reason` por *model_validator*; *no-oneOf-at-root* (DD-T16) |
| `triager/test_triager.py` | 1 | Renderização do *prompt* §5.1 (exemplos JSON sobrevivem ao `.format()`) |
| `detector/test_detector_models.py` | 4 | **Detector.** `DetectorFinding` com exatamente 5 campos, sem `rule_severity`/`rule_message` (opinião descartada, DD-D1); proveniência por-envelope, não por-finding (DD-D3) |
| `detector/test_detector_hooks.py` | 6 | Hook *escalate-all* levanta `DetectorScanFailed` em **todo** `errorCode` (findings nunca disfarçam erro); `findings:[]` é estado válido |
| `detector/test_detector_prompt.py` | 3 | Prompt prescreve *strip-opinion*, não-fabricação em erro de scan, *few-shots* |
| `classifier/test_classifier_models.py` | 4 | **Classifier.** RF-003: escalares required+nullable (`null` explícito, não omissão); listas default `[]`; vocabulário *soft* (DD-C2, sem Enum rígido → sem token de valor no grammar) |
| `classifier/test_classifier_passthrough.py` | 3 | Verificador *localize-not-judge* posicional dos 5 campos do *upstream*; *drift*/*length-mismatch* → `SubagentContractViolation` |
| `classifier/test_classifier_prompt.py` | 4 | Prompt: *resource-load-first*, quatro campos, `null` ≠ invenção |
| `matcher/test_matcher_models.py` | 7 | **Matcher.** Contrato de quatro vereditos *enum-tag* (DD-M13); presença de campo por-veredito por *model_validator*; orçamento de complexidade (≤16 anyOf, ≤24 opcionais) |
| `matcher/test_matcher_evaluation.py` | 6 | Prompt prescreve *check-all*, *short-circuit* por contexto insuficiente, escalonamento de *coverage-gap*, retry de cláusula deprecated, projeção de renomes (*documents-only*; comportamento LLM exercitado *live* em G2b) |
| `reporter/test_reporter_models.py` | 7 | **Reporter.** `ReportPayload`: `report_id` uuid4 validado; `run_outcome` Literal de quatro tokens; caminho de skip; `SummaryModel` permissivo em total==soma (mantém errorCode alcançável) |
| `reporter/test_emit_report.py` | 7 | Handler `emit_report`: seis *cross-checks* (REPORT_ID_MISMATCH, CLAUSE_REF_FORMAT `^POL-\d{3}$`, PROVENANCE_MISMATCH, COUNTS_DISAGREE, TOTAL_NOT_SUM, PYDANTIC_VALIDATION); canal de erro DD-2 (erro em `content`, não `structuredContent`); *dual-sink* `99-report.json` |
| `test_schemas_roundtrip.py` | 6 | Todo modelo que alimenta `output_format`/`emit_report` é objeto JSON `additionalProperties:false` e serializável |

#### 3.1.4 Camada 2 — coordenador (85 testes)

Verifica o *pipeline* de encadeamento determinístico que orquestra os cinco subagentes sobre o Claude Agent SDK. Três estratos: âncoras de contrato estático (taxonomia tipada de 15 exceções, cada uma com `stage` para *blame*; *whitelist* `.mcp.json`); coluna de captura/discriminação dos drivers; e e2e de composição sob SDK *mockado*.

**Quadro 5 — `tests/coordinator/` (seleção; 14 arquivos, 85 testes)**

| Arquivo | Testes | Cobre |
| :--- | :---: | :--- |
| `test_coordinator_errors.py` | 18 | Taxonomia tipada de 15 exceções (inclui `UnsupportedLegalFramework` da guarda #112); atribuição de `stage` parametrizada |
| `test_driver.py` | 13 | Driver Branch-B: `ResultMessage` capturado sem *break*; recusa checada **antes** do subtype; matriz subtype→exceção tipada |
| `test_mcp_stage.py` | 13 | Driver MCP *streaming* (ADR-0014 D1 readiness + D2 recovery): *wait-for-connected*; reconnect-and-retry em *scan error* retryable; veredito estruturado propaga sem reconnect |
| `test_reporter_stage.py` | 7 | Discriminação tri-axial do Reporter (§9.2): duplo-emit pós-sucesso → `MultipleReportEmissions`; pós-falha → `ReportNotEmitted` (ADR-0016) |
| `test_run_derivations.py` | 7 | Derivações determinísticas: quatro tokens de `run_outcome`; agregação de `summary`; forma de estado consolidado (RF-009) |
| `test_pipeline_contract.py` | 6 | E2E de contrato Fase-2b via driver real (SDK mock): handoff estágio-a-estágio; *scan error* → halt com *coverage gap* |
| `test_coordinator_config.py` | 5 | Parse *fail-loud* da *whitelist* (carrega só `{policy-reader, semgrep-runner}`; aborta em servidor inesperado/ausente/arquivo faltante) |
| `test_run_framework_guard.py` | 3 | **Guarda #112:** sob raiz eval-gdpr os quatro estágios rodam e a guarda recusa antes do Reporter → `UnsupportedLegalFramework(stage='framework_guard')`; regressão eval-lgpd emite Report |
| `test_walking_skeleton.py` | 3 | Composição: caminho skip (Triager→Reporter) vs proceed (cinco estágios); `ReportNotEmitted` tipado |
| `test_stage_options.py` | 2 | Listas exatas de `tools`/`allowed_tools` de Classifier/Matcher (ordenação deliberada) |
| `test_triager_stage.py` | 3 | Estágio Triager: proceed/skip capturado; sucesso+recusa → `SubagentRefusedTask` |
| `test_provenance_derivation.py` | 1 | Âncora de regressão do *desync* de proveniência (PR #101): trinca top-level derivada dos *findings* (0.2.0), não do default 0.1.0 |
| `test_coordinator_models.py` | 3 | União de terminação `CoordinatorResult = CoordinatorReport \| CoordinatorError` (a fronteira que o chamador consome) |
| `test_g3_live_e2e.py` | 1 `live` | Capstone G3: pipeline completo contra SDK + MCP **reais**; retorna `CoordinatorReport`, Detector acha `cpf`, piso `not_applicable` POL-000, `counts==aggregation` |

#### 3.1.5 Camada 3 — CI + harness (20 testes)

**Quadro 6 — `tests/ci/` + `tests/harness/`**

| Arquivo | Testes | Cobre |
| :--- | :---: | :--- |
| `tests/harness/test_camada3_compare.py` | 10 | Lógica determinística de comparação *field-scoped* do portão Camada-3: eixos ESTRITO (run_outcome, counts/total, proveniência, *multiset* (verdict, rule_id)), ADVISORY (`data_categories`, nunca reprova) e EXCLUÍDO (report_id, scope, file/line, prosa); caminho outcome-only SKIP-001 |
| `tests/ci/test_format_summary.py` | 5 | Renderizador puro do *Step Summary*: surfaceia run_outcome, quatro contagens, trinca, `clause_id`+`rule_id`+localização por finding; **teste negativo:** caminho de erro não fabrica veredito (regra imutável 1) |
| `tests/ci/test_run_review.py` | 4 | *Entrypoint* source-agnostic (env→`run_pipeline`→stdout); contrato de exit code (0=Report não-bloqueante RNF-002, 1=erro terminal, 2=invocação inválida) |
| `tests/harness/test_camada3_gate_live.py` | 1 `live` | Exercício e2e do portão Camada-3 sobre COMP-001 (uma das duas validações live ratificadas); afirma uma vez, surfaceia o diff, nunca re-roda divergência |

### 3.2 Smoke tests de framework (`scripts/smoke_tests/`)

Antes de comprometer implementação a uma forma de chamada de framework não ancorada por testes, o projeto roda um *smoke test* que produz evidência empírica (`.claude/rules/gates.md`: "smoke-test the framework before committing"). São **14** probes de comportamento do Claude Agent SDK / FastMCP / `check_applicability`, cada um arquivado com `RESULTS.md`. Diferem dos testes de `tests/` por não serem regressão automatizada: são experimentos de descoberta de contrato de framework, cujo resultado ratificou uma decisão de design.

**Quadro 7 — Smoke tests de framework (`scripts/smoke_tests/`)**

| Smoke test | Questão empírica | Desfecho | O que ratificou |
| :--- | :--- | :--- | :--- |
| `sdk_tooluseblock_shape` | `ToolUseBlock.input` é o canal canônico para capturar payload de tool custom? | PASS | Padrão de captura §3.5 (filtrar por `block.name`); *lockdown* quintuplo reusado por todo subagente |
| `sdk_reporter_gates` | Pydantic-class vs JSON-Schema em `@tool`; efeito do campo `tools`; forma de `ResultMessage` em max_turns | TC1 PARCIAL / TC2 PASS / TC3 PASS | Usar `model_json_schema()`; setar `tools`; discriminar `ReporterTurnsExhausted` por subtype + try/except |
| `sdk_mcp_visibility` | Tools MCP governadas por `mcp_servers` ou pelo campo `tools`? | PASS (via `mcp_servers`) | Detector `tools=['Read']` ainda vê `scan_diff`; coordenador deve inspecionar `permission_denials` |
| `sdk_tools_empty_list` | `tools=[]` é *lockdown* total ou igual a `None`? | PASS (lockdown) | Reporter/Matcher usam `tools=[]` sem perder visibilidade de tool MCP |
| `sdk_output_format_lockdown` | `output_format` existe em 0.2.87 e converge sob lockdown? | PASS (Branch-B viável) | Desbloqueou todo o design Branch-B dos subagentes |
| `sdk_output_format_complex` | `output_format` aceita `oneOf`/união na raiz? | `oneOf` → grammar **desligado** | **DD-T16:** codificar variância de veredito como objeto *enum-tag*, nunca união discriminada |
| `sdk_tool_error_channel` (v1–v4) | Como payloads de erro sobrevivem a cada camada até o stream? | `@tool` dropa `structuredContent` (usar `content`); FastMCP preserva (Opção B) | `.claude/rules/sdk-mcp-conventions.md` Eixo 2; `scan_diff` mantém `-> ToolResult` |
| `check_applicability_48b` | `ReadMcpResourceTool` visível por config? `check_applicability` em saídas-borda do Classifier? *loader* gatekeepa por framework? | PASS / EMPTY+INVALID / não-gatekeepa | Matcher `tools=['Read','ReadMcpResourceTool',...]`; sem abort server-side de framework |
| `sdk_l2_capture` | Como o SDK reporta recusa de segurança? `permission_denials` é `[]` ou `None`? | subtype mente; `stop_reason=='refusal'` é o discriminador; `[]` | Loop de captura canônico do coordenador (sem break, checar refusal antes de subtype) |
| `coordinator_live` G1 | Composição green do caminho skip live? | PASS (2026-05-31) | Gateou MC-C Fase 1 (walking skeleton) |
| `coordinator_live` G2a | Triager rende proceed/skip live + `emit_report` round-trip com 4 cross-checks? | PASS | Gateou Fase 2a; registrou débito de retry-semantics do §3.5 |
| `coordinator_live` G2b | Projeção/passthrough/scan-error através do MCP middle real? | PARCIAL — **expôs a corrida de cold-start** | Originou o ADR-0014 (readiness + resilience) |
| `coordinator_live` D1 | *wait-for-connected* re-apresenta `scan_diff` ao modelo? | PASS (2026-06-01, ×2) | ADR-0014 D1 é o fix como escrito (sem redesign) |
| `coordinator_live` G3 | Pipeline completo compõe e2e, wrapper `{output}` fica quieto na 1ª lista populada? | PASS (capstone) | Fechou MC-C Fase 3; **fronteira:** G3 prova composição, **não** detecção substantiva (bundle só-POL-000) |

> **Cautela de leitura, registrada nos próprios artefatos:** os *exit codes* de `sdk_output_format_complex` e `sdk_tool_error_channel` v3/v4 **mentem** (bugs heurísticos conhecidos) — a prosa do `RESULTS.md` é autoritativa, não o código de saída. E **GATE G3 PASS ≠ "o pipeline detecta violações"**: com bundle só-POL-000, todo veredito é `not_applicable` por construção.

### 3.3 Avaliação empírica (`eval/`)

A pasta `eval/` é o **avaliador**, mantido separado da semente de produto `policy/` (só-POL-000). As raízes completas de Política de avaliação vivem em `policies/eval-lgpd/` (POL-000/005/006/007 ativas) e `policies/eval-gdpr/` (gêmea GDPR, token `consent_gdpr`).

#### 3.3.1 Harness determinístico (`eval/harness/run_engine_cases.py`)

Roda **sem modelo** e **sem wire MCP**, in-process, em duas camadas; *exit 0* sse todo caso *engine-runnable* casou e todo Report emitido validou. **Camada 1** exercita a lógica de quatro vereditos de `check_applicability`; **Camada 2** monta Reports consolidados reusando as **próprias derivações importadas** do coordenador (`derive_run_outcome` + `aggregate_summary` + `_build_consolidated_state`, fonte única de verdade), validados contra `ReportPayload`. A última corrida está persistida em `eval/harness/gate_run.json` (**13/13** casos com *match*).

**O que o harness NÃO cobre, por construção:** a decisão de skip do Triager, o scan do Detector, a extração do Classifier, a enumeração/ordenação LLM do Matcher e o `emit_report` *live* do Reporter — as camadas LLM/MCP. O *locus* (file/line/snippet) é sintético no harness; a camada de veredito (verdict, `policy_clause_ref`, evidência, proveniência, summary, run_outcome) é real. `report_id` (uuid4) é o único campo não-determinístico.

**Quadro 8 — Casos do motor de avaliação (`eval/cases.yaml` → `gate_run.json`)**

| Caso | Veredito esperado | Engine | Papel |
| :--- | :--- | :---: | :--- |
| COMP-001 | `compliant` | ✓ | Coleta de identificação com consentimento; vitrine + PR sintético + baseline |
| VIOL-001 | `violation_candidate` | ✓ | Coleta sem base legal (omissão); vitrine E2E de violação plantada |
| VIOL-002 | `violation_candidate` | ✓ | Base não-canônica (`legitimate_interests`) |
| INDET-001 | `indeterminate` | ✓ | Perfil comportamental (`anonymization_required`); indeterminado genuíno (estado upstream não-observável) |
| NA-MVP-001 | `not_applicable` | ✓ | Operação `storage` ≠ collection (escopo MVP, ADR-0007) |
| NA-MISMATCH-001 | `not_applicable` | ✓ | Categoria fora do `applies_to` (probe de cláusula única) |
| NA-DEF-001 | `not_applicable` | ✓ | POL-000 definitional (piso de cardinalidade do sweep) |
| **B-FALSEPOS-001** | `violation_candidate` | ✓ | **Sonda de borda:** falso positivo do `consent_required` estrito (base válida `contract_performance` punida) → motiva ADR-0015 |
| **B-SENS-OK-001** | `compliant` | ✓ | **Sonda de borda:** saúde + `consent` comum → aprovado (gate de sensibilidade ausente; juridicamente frágil) |
| **B-SENS-INV-001** | `violation_candidate` | ✓ | **Sonda de borda:** saúde + `explicit_consent` correto → reprovado (a inversão; §6.2) |
| PROBE-UNGOV-001 | `coverage_gap` | ✓ | Categoria não-governada (localização) varrida sobre todas as ativas → tudo `not_applicable` |
| SWAP-001-LGPD | `compliant` | ✓ | Lado LGPD do swap; mesmo código |
| SWAP-001-GDPR | `violation_candidate` | ✓ | Lado GDPR; mesmo código, *flip* por vocabulário; **sem Report consolidado no MVP** (só o veredito é gateado) |
| SKIP-001 | (skip do Triager) | — | *Pipeline-only* (precisa do Triager LLM); `match=null` no gate |

#### 3.3.2 Experimentos (`eval/experiments/`)

**Quadro 9 — Experimentos empíricos (opt-in, medições não asserções)**

| Experimento | Pergunta | Achado |
| :--- | :--- | :--- |
| `category_exposure_discriminant.py` | Expor a lista `data_categories` basta para o Classifier classificar certo, ou precisa de demonstração (`canonical_examples`)? | A lista **sozinha bastou** nas categorias medidas, incluindo inferências não-literais (comportamental, localização: 5/5); `policy://examples` **diferido** por suficiência medida, não refutado. 42 chamadas; uma falha de transporte registrada honestamente (não re-rodada) |
| `pipeline_e2e_eval_lgpd.py` | Caracterização do pipeline completo sobre os PRs sintéticos, K por PR, marcando CONVERGENTE/DIVERGENTE vs GT | **28 corridas.** COMP/VIOL/INDET/SWAP-LGPD/SKIP todas CONVERGENTE; **PROBE-UNGOV 4-vs-1** — a divergente teve CPF→`dados_de_identificacao`→POL-005→`violation_candidate`. É a contaminação do gatilho de detecção |
| `numero-independente` (`docs/eval/avaliacao-secao-rascunho-...md`) | Por que os seis casos se dividem em núcleo reprodutível vs fronteira de escalação? | Duas causas (não três): (1) contaminação do gatilho CPF, oscilando entre categoria governada/não-governada (INDET, PROBE-UNGOV); (2) trava ADR-0007 do artefato de saída (SWAP). **Lição:** veredito correto **não** certifica classificação exata, e K=2 pode convergir por acaso |
| `convergence_harness.py` — ablação por estágio (*scratch* da fase de QA, jun/2026; `docs/eval/model-robustness-ablation.md`) | O veredito *gated* depende do modelo? Em qual estágio da pipeline de cinco agentes a capacidade do modelo afeta a estabilidade da decisão? | **Indício direcional, não conclusivo.** Falso-negativo em VIOL-001/POL-005 só com **Classifier-Haiku** (A 1/3, B 2/10); cai a **0/10** quando o Classifier sobe a Sonnet, **com ou sem** Matcher-Sonnet (Config E isola: Classifier-Sonnet + Matcher-Haiku já dá 0/10). Advisory de categoria colapsa 5/10→10/10 ao subir o Classifier. Ótimo observado: **E** (Classifier+Reporter Sonnet, resto Haiku) ao menor custo ($0,230/run). **Régua:** `0/10` ≠ zero — teto IC95% ~30% (regra 3/K); *single-clause*/*single-fixture*; atribuição estágio→modelo 100% nas configs reportadas |

#### 3.3.3 PRs sintéticos (`eval/prs/`) e cláusula proposta (`eval/proposed/`)

Seis fixtures de *pull request*, cada uma um *diff* plantado em uma stack distinta: `COMP-001` (Pydantic), `VIOL-001` (Django, violação plantada), `INDET-001` (SQLAlchemy, anonimização alegada em comentário não-verificável), `PROBE-UNGOV-001` (lat/long/ip + gatilho `cpf`), `SWAP-001` (FastAPI, mesmo código sob duas raízes), `SKIP-001` (só-docs). A cláusula `POL-008` (`lawful_basis_required`, prova de conceito do ADR-0015) é mantida **fora** de toda raiz carregada e do catálogo — o motor MVP levanta `AssertionError` em controles não-implementados (*fail-loud* deliberado), então POL-008 fica *staged* em `eval/proposed/`.

---

## 4. PORTÕES DE QUALIDADE DE MARCO

Quatro portões de marco, todos PASS. O achado metodológico recorrente: **cobertura unit verde nunca é suficiente** — o exercício de wire real / pipeline live / CI é cobertura independente e complementar que pega defeitos empilhados (fix em camada-N revela defeito mascarado em camada-N+1), por isso re-rodar portões após qualquer fix downstream é obrigatório, não cerimônia.

**Quadro 10 — Portões de marco**

| Portão | Mecanismo | Desfecho | Evidência |
| :--- | :--- | :--- | :--- |
| **Milestone A** — `policy-reader` | MCP Inspector CLI (modo CLI, replayável), exercício manual A.1–A.5 contra `policy/` real + stub GDPR | **PASS** — 5 RFs ancorados; *framework swap* LGPD→GDPR com zero alteração em `src/`. **Quatro defeitos (#5–#8) descobertos pelo portão**, nenhum dos quais os 53 testes verdes pegavam | `docs/process/milestoneA.md` (#25); defeitos em PR #47 |
| **Milestone B** — `semgrep-runner` (RF-008) | FastMCP Client + StdioTransport spawnando o servidor como subprocess real; duas fases (BR default vs pack alternativo via `SEMGREP_RUNNER_ROOT`); 5 invariantes | **PASS (5/5)** após trajetória de dois atos: o portão FALHOU em #34, expondo o *bug* de *handle inheritance* Windows-stdio invisível a 132 testes in-memory; fix PR #59; re-run expôs defeitos de aferição mascarados (PR #60) | `docs/process/milestoneB.md` (#34→#35) |
| **Camada-3-MVP local (K=2)** | `eval/harness/camada3_gate.py`: repo git efêmero por fixture, pipeline **real** vs baseline committado, *field-scoped* | **PASS** — convergência estrita em COMP-001/VIOL-001/SKIP-001 sobre K=2; único movimento foi *drift* advisory de `data_categories` no COMP-001 R2, corretamente absorvido | `docs/process/camada3-mvp.md` §2–§8 (RAW verbatim, 2026-06-04) |
| **Camada-3-MVP CI (Gates #1/#2)** | `workflow_dispatch` de `lgpd-review.yml` (matrix dos 3 fixtures) em runner ubuntu — auth por API key + `--project`/cwd-efêmero | **PASS** — *run* 26983111920 (2026-06-04, ~4m35s); 3 arms PASS; job de produção (`pull_request`) skipped por design (`if: false`) | `docs/process/camada3-mvp.md` §9; [run 26983111920](https://github.com/paivapereira/lgpd-policy-review/actions/runs/26983111920) |

---

## 5. PORTÃO DE QUALIDADE ESTÁTICA

Re-executado localmente nesta rodada (data efetiva).

**Quadro 11 — Portão de qualidade estática**

| Verificação | Comando | Resultado |
| :--- | :--- | :--- |
| Testes | `uv run pytest` | **307 passed, 2 deselected** (374 s) |
| Tipos | `uv run mypy src` (strict) | **Success: no issues found in 46 source files** |
| Lint (código) | `uv run ruff check src tests` | **All checks passed** |
| Lint (repositório) | `uv run ruff check .` | 3 *F401* (`json`, `tempfile`, `pathlib.Path` não usados) em `scripts/smoke_tests/check_applicability_48b/probe.py` e `coordinator_live/d1_readiness_gate.py` — probes exploratórios, auto-corrigíveis com `--fix` |
| Formatação | `uv run ruff format --check .` | **114 arquivos reformatáveis** (29 já formatados) — **débito aberto** (§6.3 #2) |

**Leitura.** A *superfície de produto* (`src/`) e a suíte (`tests/`) são lint-limpas e `mypy --strict`-limpas. Os três *F401* residuais são em scripts de probe descartáveis, não em código embarcado. A não-conformidade com `ruff format` é débito conhecido e indeciso (adotar ou não `ruff format --check` em CI), não uma regressão de comportamento.

---

## 6. DEFEITOS DESCOBERTOS E LIMITES CONHECIDOS

A arqueologia de defeitos confrontou `git log`, os ADRs nomeados (0011/0014/0015/0016), os *diffs* dos fix-commits, o `learning-log` e o `session-handoff` contra os artefatos reais. Padrão transversal: **cada defeito substantivo foi pego por um exercício empírico de camada-3 (portão manual de marco, agent-loop live ou harness de avaliação) DEPOIS de `pytest`/`ruff`/`mypy` estarem verdes** — a lição recorrente de que o exercício empírico wire-level é cobertura independente, não substituível.

### 6.1 Defeitos corrigidos

**Quadro 12 — Defeitos descobertos e corrigidos**

| Ref | Defeito | Camada | Detectado por | Fix |
| :--- | :--- | :--- | :--- | :--- |
| PR #59 / ADR-0011 | *Hang* Windows-stdio: `subprocess.run` sem `stdin=` deadlocka sob transporte stdio real (*handle inheritance*); `TimeoutExpired` misclassificado como `GIT_REF_NOT_FOUND` | 2 (`semgrep-runner`) | **portão manual Milestone B** — invisível a 132 testes in-memory | `stdin=subprocess.DEVNULL` em 3 sites; regressão AS-14/AS-14b |
| PR #95 / ADR-0014 D1 | Corrida de cold-start: Detector age antes de `semgrep-runner` conectar → `scan_diff` não registrado → `findings=[]` | 3 (driver coord.) | **portão e2e agent-loop G2b** | Migrar estágios MCP a `ClaudeSDKClient` *streaming* com *wait-for-connected* |
| PR #95 / ADR-0014 D2 | Erros de scan retryable escalavam de imediato (hook *escalate-all*) | 3 (recovery) | divergência spec/impl em G2b | Retry in-session limitado por `isRetryable` (reconnect, re-issue) |
| PR #101 | *Desync* de proveniência top-level → `MultipleReportEmissions` determinístico em raiz não-default | 3 (Reporter) | **e2e live** COMP-001 sobre eval-lgpd | Derivar trinca dos `findings` (top==per-finding por construção) |
| PR #102 / ADR-0016 | Guarda de emissão única contava tentativas, não sucessos — estrangulava o retry de validação legítimo (2/5 halt) | 3 (Reporter) | **diagnóstico de 5 corridas live** (2/5→0/5) | Contar emissões bem-sucedidas via sink `99-report.json` |
| PR #105 / ADR-0010 amend. | `rule_id` não normalizado: prefixo de caminho dotificado do Semgrep vaza, instável entre contextos | 2 (`semgrep-runner`) | **cenário de avaliação live G3** (regra fora da árvore escaneada) | `_normalize_rule_id = check_id.rsplit('.',1)[-1]` |
| PR #112 | *Mislabel* silencioso de `legal_framework`: Report rotulado LGPD sob raiz GDPR | 3 (coordenador) | **teste** (âncoras red em `test_run_framework_guard.py`); surgiu na redação do §2.5 | Guarda *fail-loud* `UnsupportedLegalFramework(stage='framework_guard')` antes do Reporter |

### 6.2 Limites conhecidos (documentados, decisão consciente de escopo)

- **Inversão de sensibilidade na POL-007 (Art. 11 LGPD)** — `docs/eval/pol-007-inversao-sensibilidade.md`. O motor (`_verdict_for_control`) avalia `consent_required` por igualdade exata contra o literal `consent`, sem consultar a flag `special_category` da categoria. Para dado de saúde (sensível), `consent` comum retorna `compliant` (juridicamente insuficiente — Art. 11 exige consentimento destacado) e `explicit_consent` correto retorna `violation_candidate`: **a inversão é completa e sistemática**. A cláusula é policy-correta; o motor é sub-modelado. As duas dimensões são auditáveis separadamente porque cada veredito carrega proveniência. Correção projetada (gate de sensibilidade em `_verdict_for_control` + token `lawful_basis_required` do ADR-0015) deixada como trabalho futuro por risco de regressão sob prazo; o achado é cientificamente íntegro sem a implementação, e os dois Reports B-SENS são a evidência empírica completa. Status: **documentado / não-corrigido por decisão de escopo**.
- **Loader não cross-valida `clause.control`** — um controle não-implementado carrega bem e só quebra no sweep do Matcher com `AssertionError`. **Mitigado por construção** (o token fica fora de toda `control.yaml` carregada; POL-008 vive em `eval/proposed/`); a `AssertionError` é o *fail-loud* pretendido. Fix estrutural (loader validando `control` contra o vocabulário) não implementado.
- **Misclassificação `TimeoutExpired → GIT_REF_NOT_FOUND`** (ADR-0011 D2) — PR #59 eliminou a manifestação (hang), mas a estrutura que colapsa erro transiente em erro de negócio persiste; design do fix estrutural registrado, implementação diferida.

### 6.3 Débitos abertos (housekeeping; não bloqueiam a entrega)

1. **Spec drift `coordinator.md` §5:** tabela de exceções 13→15 (âncora de teste atualizada; tabela §5 + `docs/tasks.md` §Companion não) — ver XDOC-05.
2. **`ruff format`** indeciso: repo não é `ruff format`-clean; decidir se CI adota `ruff format --check`.
3. **ADR do Caminho 1:** registrar a leitura direta do header da Política no coordenador como exceção de *pre-flight* ratificada.
4. **Reporter single-failed-emit-then-voluntary-end:** caminho latente de falso-sucesso silencioso, **contido** pela rede de segurança `ReportNotEmitted` (não observado em 10 corridas), resolução diferida.

---

## 7. MATRIZ DE COBERTURA REQUISITO → EVIDÊNCIA

Cada RF/RNF mapeado para a evidência concreta que o cobre, com nível honesto e nota de lacuna.

**Quadro 13 — Matriz de cobertura RF/RNF**

| Req | Resumo | Nível | Coberto por / Lacuna |
| :--- | :--- | :--- | :--- |
| **RF-001** | Detecção de coleta no *diff* (file/line/snippet/rule_id) | **full** | `test_scan_diff.py` (29) + `test_recognizers_br.py` AS-1..6 + `DetectorFinding` model + gate_run.json. *Lacuna:* *locus* real no Report só pelo caminho live (COMP-001); o harness injeta *locus* sintético |
| **RF-002** | Seis identificadores BR; `data_categories` carrega nome canônico | **partial** | Os seis reconhecedores **disparam** com cobertura plena no Semgrep. *Lacuna:* o nome canônico em `data_categories` é **inferência do Classifier (LLM)**, não derivado do `rule_id` — `DetectorFinding` não tem `data_categories`; no portão é ADVISORY; realismo medido (não asserido) pelo experimento live |
| **RF-003** | Classificação contextual: 4 campos, vocab-bound ou null | **partial** | Forma dos 4 campos + passthrough ancorados hermeticamente. *Lacuna:* pertença ao vocabulário é *soft* (DD-C2, comportamento LLM), medida não asserida; nenhum teste padrão força valor não-vocab a `null` |
| **RF-004** | Avaliação de conformidade (MVP=collection); `not_applicable` p/ outras ops | **full** | gate_run.json (matriz de quatro vereditos, todos casam) + `test_check_applicability.py`. Escopo MVP `not_applicable` por igualdade de razão (ADR-0007) |
| **RF-005** | Honestidade epistêmica: `indeterminate` + `verification_scope` (3 sub-campos) | **full** | INDET-001 + `test_as3` + *model_validator* do Matcher. *Lacuna:* só a dimensão `upstream_state`/anonimização é exercitada |
| **RF-006** | Report JSON agregado via `emit_report`; campos mínimos; `clause_ref` incondicional | **full** | `test_emit_report.py` (6 cross-checks) + validação de 10 Reports contra `ReportPayload` + `clause_ref` em todo veredito |
| **RF-007** | Composição intra-jurisdição via `accepted_law_identifiers` | **indirect** | *Plumbing* de `statutory_reference` + filtragem por artigo testados. *Lacuna:* o cenário de dois clientes (LGPD vs LGPD+CDC) sobre o mesmo PR e a rejeição de lei fora da composição **não** são diretamente ancorados |
| **RF-008** | Troca de framework (LGPD→GDPR) sem alterar `src/` | **partial** | **full no nível do veredito** (SWAP-001-GDPR, `legal_framework=GDPR`, zero edição de `src/`) e do recurso `policy://vocabularies`. *Lacuna:* Report consolidado **travado** em `Literal["LGPD"]` + guarda #112 recusa Report GDPR → **parcial no nível do Report**, diferido a *minor bump* |
| **RF-009** | Trinca de proveniência em todo finding e header | **full** | gate_run.json (toda detail carrega a trinca) + cross-check PROVENANCE_MISMATCH + portão STRICT. *Lacuna:* valor `GDPR` na trinca nunca chega a um Report (trava de RF-008) |
| **RNF-001** | Stack pinada + reprodutibilidade | **indirect** | `.python-version`, `uv.lock`, CI pina versões, ADRs gateiam bumps. *Lacuna:* sem teste que asserte versões instaladas; `semgrep_version` hardcoded em fixtures |
| **RNF-002** | Posicionamento informativo (posta summary, não bloqueia merge) | **partial** | Contrato de exit não-bloqueante + caminho *Step Summary* (`workflow_dispatch`) cobertos. *Lacuna:* comentário *inline*/PR de produção é `if: false` (INERTE) → **diferido a Milestone D** |

**Síntese:** *full* 5 (RF-001/004/005/006/009), *partial* 4 (RF-002/003/008, RNF-002), *indirect* 2 (RF-007, RNF-001). As três tensões honestas mais relevantes: (a) realismo de `data_categories` cavalga no Classifier, não no Detector; (b) o swap de framework é real no veredito mas o Report é travado em LGPD; (c) o posicionamento informativo cobre o *Step Summary*, não o comentário *inline* de produção.

---

## 8. REVISÃO CROSS-DOC

Revisão de consistência entre a documentação e a realidade atual do repositório. Foram avaliados 23 achados-candidatos por três revisores e verificados um a um contra os arquivos-fonte; **nenhum** foi descartado como leitura equivocada, e duas sub-alegações exageradas foram aparadas sem invalidar o achado-pai. Resultado: **16 achados** (4 ALTA, 8 MEDIA, 4 BAIXA). As correções propostas ficam como insumo — este relatório não edita os documentos da tese (decisão registrada no cabeçalho).

**Quadro 14 — Achados cross-doc (resumo)**

| ID | Sev. | Documento | Síntese |
| :--- | :--- | :--- | :--- |
| **XDOC-01** | ALTA | `relatorio-tcc2-parcial.md` §2.5 | Promete "Report válido sob GDPR"; a guarda #112 **recusa** Report sob não-LGPD. Contradição método-vs-resultado |
| **XDOC-02** | ALTA | `relatorio-tcc2-parcial.md` (RESUMO, §2.3, §3, AP. E) | Tempo "parcial/restando": Matcher especificado, pipeline implementado, Camada-3 aprovada — tudo **feito** |
| **XDOC-03** | ALTA | `CLAUDE.md` §Status flags | "134 passing" / "CI not configured" / "Subagents not implemented" — todos falsos (307; CI existe; subagentes implementados) |
| **XDOC-04** | ALTA | `CLAUDE.md` §Repository state | "early development... directories do not exist yet" — oposto da realidade (mid-to-late MVP) |
| XDOC-05 | MEDIA | `coordinator.md` §5/§3.0 | Tabela de exceções 13 vs 15 no código (`UnsupportedLegalFramework`, `SubagentToolError` ausentes); pre-flight não documentado |
| XDOC-06 | MEDIA | `coordinator.md` §6/§3.2-3.4 | `EXPECTED_SERVERS` é `frozenset`; halt em servidor ausente; slices são atributos lowercase de `McpServersConfig`, não constantes UPPERCASE |
| XDOC-07 | MEDIA | `coordinator.md` §3.0bis | Driver único na spec; código tem dois transportes (`run_branch_b_stage` + `_run_mcp_stage`, ADR-0014) |
| XDOC-08 | MEDIA | `coordinator.md` §3.1 | `system_prompt=TRIAGER_SYSTEM_PROMPT` na spec; código usa `system_prompt=None` (DD-4) |
| XDOC-09 | MEDIA | `classifier.md` §4.3/§9.3 | Compara 4 campos; código passa 5 (`surrounding_context` incluído) |
| XDOC-10 | MEDIA | `reporter.md` §4.5/§6.1 | Envelope de erro mostra `structuredContent`; o bridge `@tool` o **dropa** — erro vai em `content` (Eixo 2) |
| XDOC-11 | MEDIA | `relatorio` §3.1 / RNF-002 / `architecture-overview` | "~200 snippets" prometidos; entregue ~6-8 fixtures + harness (redução documentada, número literal residual) |
| XDOC-12 | MEDIA | `session-handoff.md` | "Caminho 1 NÃO MERGEADO" — está mergeado (#112, `05d8a18`) |
| XDOC-13 | BAIXA | `classifier.md`/`reporter.md` | Ordem de campos; kwarg `reason=` inexistente; `tools=[]` já aplicado (marcado pendente) |
| XDOC-14 | BAIXA | `relatorio` §2.6 Quadro 3 | Linha 03-09/jun marcada "Planejado" mas a data efetiva está dentro da janela e o trabalho está feito (linhas futuras devem permanecer "Planejado") |
| XDOC-15 | BAIXA | ADR-0011 Status | "Proposto" mas o hardening (PR #59) já embarcou e rodou no gate B |
| XDOC-16 | BAIXA | `relatorio` AP. D | "ADR-0001 a 0010" — o corpo vai até 0016 (sem 0013) |

### 8.1 Detalhamento dos achados ALTA

**XDOC-01 (a contradição central).** O §2.5 promete, como segundo critério global, "obter um Report válido sob o novo *framework* [GDPR]". O código contradiz: `run.py:79` fixa `_SUPPORTED_LEGAL_FRAMEWORKS = frozenset({"LGPD"})`; `run.py:443-447` levanta `UnsupportedLegalFramework` imediatamente antes do Reporter; `legal_framework: Literal["LGPD"]` (`reporter/models.py:61`, `matcher/models.py:60`) torna um Report rotulado GDPR estruturalmente inexprimível. A independência jurisdicional **é** observável — mas na superfície da ferramenta `check_applicability` (caso SWAP-001-GDPR no gate), não em um Report GDPR. *Correção proposta:* reescrever o critério para "decisão jurisdicional observável na superfície de `check_applicability`; o coordenador recusa, *fail-loud*, emitir Report sob framework ≠ LGPD em vez de coagir o rótulo; Report multi-jurisdição é trabalho futuro". Esta reescrita já está alinhada ao rascunho `numero-independente`.

**XDOC-02/03/04 (tempo verbal e status defasados).** O relatório parcial está redigido em tempo "parcial/restando", e o `CLAUDE.md` declara estado de desenvolvimento inicial — ambos defasados frente a um MVP completo. As correções promovem essas passagens para o estado concluído e atualizam os *status flags* (307 testes; CI configurada; subagentes implementados; guarda #112 mergeada). Observação para o XDOC-14: as linhas de cronograma com **datas futuras** relativas a 2026-06-05 devem permanecer "Planejado" — só a linha da janela corrente (03-09/jun) é inconsistente.

---

## 9. AVALIAÇÃO POR CAMADA E POR VEREDITO

### 9.1 Por camada

- **Camada 1 — Política / `policy-reader`.** Madura. *Loader* *fail-loud* com mensagens pt-BR nomeando o artefato; matriz de quatro vereditos coberta determinística e ao vivo; versionamento de dois eixos validado na carga. Risco residual: o loader não cross-valida `control` (§6.2), mitigado por construção.
- **Camada 2 — `semgrep-runner` + reconhecedores BR.** Madura. RF-002 é o diferencial técnico, coberto por 49 testes positivos/negativos contra Semgrep real; RF-001 por 29 testes com git+Semgrep reais. O endurecimento Windows-stdio (PR #59) fechou o defeito de classe empírica-only.
- **Camada 2 — subagentes + coordenador.** Madura no contrato; o comportamento LLM (extração do Classifier, enumeração do Matcher) é por natureza estocástico e exercitado *live* (G2b/G3), não por regressão determinística. A taxonomia tipada de 15 exceções e a guarda *fail-loud* materializam a regra imutável 1 (sem certeza fabricada): todo caminho de falha é tipado e atribuído a um `stage`, e um scan falho escala como `DetectorScanFailed` com *coverage gap* "cobertura zero", nunca como resultado vazio silencioso.
- **Camada 3 — CI.** Funcional no MVP (`workflow_dispatch`, *Step Summary*, exit não-bloqueante). O comentário *inline* em PR de produção é `if: false` (INERTE), diferido a Milestone D — fronteira honesta, não limitação envergonhada.

### 9.2 Por veredito (a fronteira honesta)

Os seis casos de avaliação se dividem em dois níveis, e essa divisão **é** um resultado sobre a regra imutável 1:

- **Núcleo reprodutível** (COMP-001, VIOL-001, SKIP-001) — convergem campo a campo entre execuções independentes e sustentam o portão estrito de CI (K=2).
- **Fronteira de escalação** (SWAP-001, INDET-001, PROBE-UNGOV-001) — avaliados qualitativamente. Resistem ao portão estrito por **duas** causas: (1) **contaminação do gatilho de detecção** — um CPF não-alvo oscila entre `dados_de_identificacao` (governada → `violation_candidate`) e `dados_de_documentos_oficiais` (não-governada → `not_applicable`), desestabilizando contagens/multiset mesmo quando o veredito-alvo é estável; (2) **trava do artefato de saída (ADR-0007)** — o braço GDPR não emite Report fiel, então o *flip* é lido na ferramenta de política.

Dois aprendizados empíricos sustentam a honestidade do método: **veredito correto não certifica classificação exata** (PROBE-UNGOV-001: `dados_de_localizacao` extraída nas 5 execuções, mas nunca isoladamente), e **convergência K=2 pode ser coincidência** (INDET-001: a execução de validação divergiu das duas do matrix). Isso fundamenta empiricamente por que o portão estrito é reservado ao núcleo cuja classificação a montante é inequívoca — decisão imposta pelos dados, não de conveniência.

---

## 10. CONCLUSÃO DE QA

No nível de produto mínimo viável, a qualidade do `lgpd-policy-review` está **atestada com ressalvas declaradas**. As três camadas estão implementadas e exercitadas de ponta a ponta; a suíte de 309 testes (307 padrão verde) cobre cada camada; `mypy --strict` é limpo; quatro portões de marco passaram, incluindo uma execução de CI ao vivo; e os 13 casos do motor de avaliação casam o veredito esperado. O diferencial técnico (reconhecedores brasileiros) e a propriedade central (decisão acompanha a Política versionada) estão demonstrados — esta última no nível da decisão, com a fronteira do artefato de saída declarada com precisão.

**Riscos residuais para a defesa, em ordem de prioridade:**
1. **Reconciliar o §2.5 do relatório parcial** (XDOC-01) antes de qualquer apresentação — é a única contradição interna em que o método nega o que os resultados mostram. A reescrita proposta está pronta e alinhada ao rascunho `numero-independente`.
2. **Atualizar o tempo verbal e os *status flags*** (XDOC-02/03/04): o relatório fala em "parcial" sobre um MVP completo.
3. **Decidir a moldura da inversão POL-007** na defesa: apresentá-la como evidência de rigor de avaliação (limite real, causa-raiz e correção projetada), não como falha — é exatamente o que a honestidade epistêmica do sistema prescreve.

**Recomendações de QA, sem urgência de entrega:** aplicar as correções cross-doc MEDIA/BAIXA em uma sessão de housekeeping dedicada (sem misturar com feature); decidir o gate `ruff format` em CI; e, se houver janela, ancorar diretamente o cenário de dois clientes do RF-007 (hoje *indirect*) e a inversão de RF-008 no nível do Report (quando o `Literal["LGPD"]` for relaxado para um conjunto validado).

Nenhuma dessas ressalvas é silenciosa: cada uma está documentada, com causa-raiz e caminho de correção. É essa a propriedade que o trabalho se propõe a sustentar — não a ausência de limites, mas a honestidade sobre eles.

---

## APÊNDICE — Comandos de reprodutibilidade

A partir da raiz do repositório, com `semgrep 1.163.0` no PATH (e sessão autenticada para os passos *live*):

```powershell
# Suíte padrão (sem live) + cobertura coletada
uv run pytest                              # 307 passed, 2 deselected
uv run pytest --collect-only -q            # 309 collected (2 live)

# Portão de qualidade estática
uv run ruff check src tests                # limpo
uv run mypy src                            # strict: 46 files, sem issues
uv run ruff format --check .               # débito: 114 reformatáveis

# Motor determinístico de avaliação (sem modelo, sem custo)
uv run python eval/harness/run_engine_cases.py          # tabela
uv run python eval/harness/run_engine_cases.py --json   # 13/13 match

# Portão Camada-3 local (live — requer sessão autenticada + semgrep)
uv run python -m eval.harness.camada3_gate --case all
uv run pytest -m live tests/harness/test_camada3_gate_live.py -s

# Lógica de comparação do portão (determinística, sem LLM)
uv run pytest tests/harness/test_camada3_compare.py -q

# Portão B (RF-008 substituibilidade de rule set, stdio real)
uv run python scripts/gate_milestone_b_exercise.py

# CI (Gates #1/#2): workflow_dispatch de .github/workflows/lgpd-review.yml
# (requer secret ANTHROPIC_API_KEY no repositório)
```

**Fontes primárias de evidência (versionadas):** `eval/harness/gate_run.json`; `docs/process/milestoneA.md`, `milestoneB.md`, `camada3-mvp.md`; `docs/eval/pol-007-inversao-sensibilidade.md`, `cpf-exposicao-categorias-suficiencia.md`, `avaliacao-secao-rascunho-numero-independente.md`, `model-robustness-ablation.md` (esta com harness e dados crus em *scratch*, não versionados — ver §7 do próprio artefato); `eval/harness/reports/*.report.json`; [CI run 26983111920](https://github.com/paivapereira/lgpd-policy-review/actions/runs/26983111920).
