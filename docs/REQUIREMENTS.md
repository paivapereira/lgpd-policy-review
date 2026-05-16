# Requirements — Sistema de code review de Proteção de Dados assistido por agentes

**Escopo.** Contrato de aceitação global do sistema descrito em `docs/proposta-tcc2.md`. Cada item declara capacidade externa observável; é verificável por inspeção do comportamento do sistema sem julgamento subjetivo. Detalhes internos (contratos de componente, formato de payload, semântica de tools) vivem nas specs e ADRs referenciadas, não aqui.

**Convenção.** `RF-NNN` para requisitos funcionais; `RNF-NNN` para não-funcionais. IDs são citáveis em `docs/tasks.md` e em mensagens de commit (e.g., `Refs: RF-005`). Cada item tem descrição, critério de aceitação no formato Dado/Quando/Então (RFs) ou referência arquitetural (RNFs), e refs ao material-fonte.

**Source-of-truth.** Arquitetura em `docs/architecture-overview.md` e `docs/adr/`. Esquema e camadas da Política em `policy/SCHEMA.md`. Contratos de componente em `docs/specs/<componente>/canonical.md` e `compact.md`. Entrypoint de leitura para implementação em `docs/DESIGN.md`. Este documento aponta, não duplica.

**Terminologia.** Termos com inicial maiúscula (Política, Report, Matcher, Detector, Classifier, Triager, Reporter) são técnicos do projeto, definidos no glossário de `docs/architecture-overview.md`. "Política versionada de Proteção de Dados" é o artefato declarativo sob `policy/` que codifica o framework jurisdicional declarado no header — LGPD é instância exemplar do MVP, não invariante do sistema.

---

## Requisitos funcionais

### RF-001 — Detecção de coleta de dados pessoais

**Descrição.** Sistema identifica pontos de coleta de dados pessoais no diff de um pull request e os reporta com localização (arquivo, linha), snippet do código ou payload, e identificador da regra de detecção que disparou. Coleta inclui captura via parâmetros de função, definição de campos em formulários, eventos de instrumentação (clique, page view, cadastro), payloads estruturados de plataforma de dados (e.g., schemas tipo CDP/AEP) e demais padrões sintáticos reconhecidamente associados a entrada de dado de usuário. A linguagem do código-fonte é parametrizável pelo conjunto de regras carregado — não há comprometimento com Python.

**Critério.**
- **Dado** um pull request contendo construção sintática que recebe dado pessoal nomeado (e.g., função com parâmetro `cpf`, campo de payload `properties.email`, definição de evento com atributo `user.phone`),
- **quando** o sistema executa contra esse PR,
- **então** o Report final carrega ao menos um finding apontando essa linha como ponto de coleta candidato, com `rule_id` identificando o reconhecedor disparado e `file`/`line`/`snippet` preenchidos.

**Refs.** `architecture-overview.md` §4.4, §5.3; `docs/specs/semgrep-runner/`.

---

### RF-002 — Cobertura de identificadores brasileiros

**Descrição.** Sistema detecta os seis identificadores brasileiros canônicos como categorias nominadas de dado pessoal: CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde. Esta é a lacuna técnica explicitamente endereçada pela contribuição do trabalho em relação a ferramentas internacionais (Microsoft Presidio, regras Semgrep mainstream), que cobrem apenas identificadores anglófonos.

**Critério.**
- **Dado** PR contendo coleta de qualquer um dos seis identificadores brasileiros (campo, parâmetro ou atributo nomeado de forma reconhecível pelo conjunto de regras),
- **quando** o sistema executa,
- **então** o finding correspondente carrega `data_categories` contendo o nome canônico do identificador detectado (e.g., `cpf`, `cnpj`, `titulo_de_eleitor`).

**Refs.** `proposta-tcc2.md` §4.d, §2; `architecture-overview.md` §4.4.

---

### RF-003 — Classificação contextual de candidatos

**Descrição.** Para cada candidato detectado, o sistema extrai contexto estruturado com quatro campos: `operation_type` (operação sobre o dado), `data_categories` (categorias semânticas do dado coletado), `declared_legal_basis` (base legal explicitamente declarada no código ou em comentário/docstring próxima, quando presente), `declared_transformations` (transformações como anonimização, hash, criptografia, quando declaradas). Valores em campos governados por vocabulário jurisdicional são restringidos aos vocabulários publicados pela Política via `policy://vocabularies` — extração que falha em mapear para o vocabulário do framework declarado resulta em campo nulo, não em invenção.

**Critério.**
- **Dado** candidato detectado pelo Detector,
- **quando** o Classifier processa,
- **então** o candidato enriquecido carrega os quatro campos de `structured_context`; valores em `operation_type`, `declared_legal_basis` e demais campos de vocabulário jurisdicional pertencem ao conjunto exposto por `policy://vocabularies` do framework declarado, ou são nulos.

**Refs.** `architecture-overview.md` §5.4; ADR-0005 Decision 4; `docs/specs/policy-reader/canonical.md` §3.3.

---

### RF-004 — Avaliação de conformidade contra a Política (escopo MVP restrito a coleta)

**Descrição.** Sistema avalia candidatos com `operation_type: collection` (token canônico do vocabulário `policy/vocabularies/<framework>/operation.yaml`, exposto via `policy://vocabularies`) contra cláusulas aplicáveis da Política e emite veredito no conjunto `{compliant, violation_candidate, indeterminate, not_applicable}`. Candidatos com outras operações (`use`, `transfer`, `storage`, etc.) retornam `verdict: not_applicable` com razão explícita de escopo MVP — comportamento que preserva a arquitetura para expansão futura sem refatoração. Cláusulas que governam operações fora de `collection` permanecem na Política como audit trail e provenance histórica, mas não disparam matching no MVP v0.1.0.

**Critério.**
- **Dado** candidato com `operation_type: collection` e Política contendo cláusula aplicável,
- **quando** o Matcher avalia,
- **então** o finding contém `clause_id` da cláusula aplicada e `verdict` em `{compliant, violation_candidate, indeterminate, not_applicable}`.

- **Dado** candidato com `operation_type` em qualquer valor do vocabulário diferente de `collection` (e.g., `use`, `transfer`, `storage`, `deletion`),
- **quando** o Matcher avalia,
- **então** `verdict: not_applicable` com `reason: "operation outside MVP scope (v0.1.0): only 'collection' is evaluated"`, sem invocar matching de cláusulas.

**Refs.** `architecture-overview.md` §5.5; `docs/specs/policy-reader/canonical.md` §4; ADR retroativo sobre escopo de operações na v0.1.0 (a redigir, registrado em `session-handoff.md`).

---

### RF-005 — Honestidade epistêmica via veredito `indeterminate`

**Descrição.** Quando a verificação de conformidade requer dimensão fora da análise estática de PR (estado runtime de consentimento, anonimização aplicada upstream em pipeline invisível, configuração de outro serviço, qualidade criptográfica de transformação declarada, etc.), o sistema retorna `verdict: indeterminate` com `verification_scope` nomeando a dimensão a verificar manualmente, em vez de chutar conformidade. Este comportamento é design deliberado, não limitação envergonhada — protege o posicionamento de TCC de "conformidade declarativa, não efetiva" e blinda a defesa contra crítica de falso-positivo/falso-negativo em dimensões que análise estática não tem como observar.

**Critério.**
- **Dado** candidato cuja conformidade depende de observação que análise estática de PR não consegue fazer (e.g., cláusula exige anonimização efetiva e o código declara `# anonimizado upstream` sem trecho de transformação visível no diff),
- **quando** o Matcher avalia,
- **então** `verdict: indeterminate` e `verification_scope` declara os três sub-campos `dimension`, `prescribed_treatment`, `verification_target` com strings não-vazias descrevendo a dimensão a verificar.

**Refs.** `docs/specs/policy-reader/canonical.md` §4.3, §7.3; `architecture-overview.md` §7.1; `proposta-tcc2.md` §8.

---

### RF-006 — Report agregado em JSON estruturado

**Descrição.** Sistema consolida todos os vereditos do PR em um Report JSON único, auditável, emitido via tool customizada `emit_report` exclusiva do subagente Reporter. Cada finding do Report contém minimamente: localização (`file`, `line`), `rule_id`, `data_categories`, `operation_type`, `verdict`, e `clause_id` quando `verdict ∈ {compliant, violation_candidate, indeterminate}` (omitido em `not_applicable`), além de `evidence` ou `verification_scope` conforme o veredito, e a trinca de provenance da Política (ver RF-009). O Report é o único output observável externamente — todos os demais artefatos são internos ao pipeline.

**Critério.**
- **Dado** PR processado até a etapa do Reporter sem falha terminal,
- **quando** o Reporter emite via `emit_report`,
- **então** a saída é objeto JSON validável contra schema declarado, contendo lista `findings` (possivelmente vazia se Triager decidiu skip ou se nenhum candidato foi detectado), e cada elemento da lista carrega os campos mínimos acima.

**Refs.** `architecture-overview.md` §4.3 (tool `emit_report`), §5.6 (Reporter); `docs/specs/reporter/` (a redigir em Fase 2).

---

### RF-007 — Composição intra-jurisdição da Política

**Descrição.** A Política aceita múltiplas leis dentro da jurisdição declarada via `accepted_law_identifiers` no header global. Adicionar ou remover uma lei na composição (e.g., cliente que opera sob LGPD apenas vs. cliente que opera sob LGPD + Código de Defesa do Consumidor + Resoluções do Banco Central) é alteração apenas na Política do cliente, sem modificação de código no sistema. Cláusulas que citam leis fora da composição declarada são inativadas para esse cliente — a validação rejeita Política que cita lei ausente da composição declarada.

**Critério.**
- **Dado** cliente A com `accepted_law_identifiers: [LGPD]` e cliente B com `accepted_law_identifiers: [LGPD, CDC]`, ambos sob `legal_framework: LGPD`, com Política do B contendo cláusula que cita `article_source.lei: CDC`,
- **quando** ambos clientes executam o sistema sobre o mesmo PR que aciona essa cláusula,
- **então** o Report do cliente B contém finding referente à cláusula CDC e o Report do cliente A não; nenhum arquivo sob `src/` difere entre as duas execuções.

**Refs.** ADR-0005 Decisions 1 e 2; `policy/SCHEMA.md` §3 (header global); `architecture-overview.md` §4.1.

---

### RF-008 — Substituição de framework jurisdicional sem alteração de código

**Descrição.** Trocar o framework jurisdicional sob o qual o sistema opera (e.g., LGPD → GDPR para cliente europeu) é exercício de substituição de dados — Política, vocabulários jurisdicionais e regras de detecção aplicáveis à nova jurisdição — não exige modificação de código nos subagentes, MCP servers ou integração CI/CD. Esta é a propriedade arquitetural que separa o trabalho de SAST com regras hardcoded e materializa o argumento da Política como artefato de primeira classe.

**Critério.**
- **Dado** sistema rodando sob Política LGPD válida (`legal_framework: LGPD`, vocabulários em `policy/vocabularies/LGPD/`) e produzindo Report sobre PR de teste,
- **quando** o operador substitui `policy/policy.yaml` e o conteúdo de `policy/vocabularies/LGPD/` por equivalentes GDPR (`legal_framework: GDPR`, vocabulários em `policy/vocabularies/GDPR/`) e reinicia os MCP servers, sem editar nenhum arquivo sob `src/`,
- **então** rerodar o mesmo PR produz Report válido sob o novo framework, com `clause_id`s pertencentes à Política GDPR e `legal_framework: GDPR` na provenance de todo finding.

**Refs.** ADR-0005 Decisions 1, 2, 5; `DESIGN.md` (Validação global).

---

### RF-009 — Provenance temporal e jurisdicional em vereditos e Report

**Descrição.** Todo veredito emitido pelo sistema carrega trinca de provenance `(policy_schema_version, policy_version, legal_framework)` identificando exatamente sob qual versão da Política e qual framework foi produzido. A trinca aparece em cada finding e no header do Report agregado. Esta capacidade é o que torna o sistema auditável: um Report arquivado em CI hoje pode ser comparado anos depois com a versão da Política sob a qual foi produzido, distinguindo divergência de Política de divergência de código.

**Critério.**
- **Dado** veredito emitido pelo sistema (qualquer um dos quatro: `compliant`, `violation_candidate`, `indeterminate`, `not_applicable`),
- **quando** o Report é inspecionado,
- **então** o finding correspondente contém os três campos `policy_schema_version`, `policy_version` e `legal_framework` com valores idênticos aos declarados no header de `policy/policy.yaml` carregado pela instância do `policy-reader` durante a execução.

**Refs.** ADR-0005 Decision 5; `docs/specs/policy-reader/canonical.md` §4.3, §6.4.

---

## Requisitos não-funcionais

### RNF-001 — Stack tecnológica e reprodutibilidade

**Descrição.** Sistema é implementado em Python 3.12.7 sob gerenciamento `uv`, com FastMCP 3.x para servidores MCP, Pydantic 2.5 para validação de esquemas, Semgrep como motor de detecção sintática, GitHub Actions como runtime CI/CD, e Inspect AI como framework de validação empírica do benchmark sintético. Reprodutibilidade depende de lockfile commitado e ausência de instalações ad hoc.

**Critério.** Dependências declaradas em `pyproject.toml` e travadas em `uv.lock` versionado no repositório. Bump de versão major de qualquer dependência crítica exige ADR específico aprovado antes da atualização. ADRs governantes: ADR-0001 (configuração inicial — em débito de sincronização com `uv.lock` atual, FastMCP 3.x) e ADR-0004 (FastMCP 3.x e ajustes de stack — reservado, a redigir antes da primeira sessão de implementação).

**Refs.** ADR-0001, ADR-0004 (a redigir); `proposta-tcc2.md` §7.

---

### RNF-002 — Posicionamento operacional informativo

**Descrição.** Sistema posta findings como inline review comments no PR via API do GitHub e não bloqueia merge no MVP. Bloqueio condicional é evolução pós-validação empírica de taxa de falso-positivo, formalizada em ADR futuro quando o critério de ativação for definido. Esta restrição é posicionamento honesto, não limitação envergonhada: sistemas de IA que bloqueiam ações precisam de calibração empírica de FPR que um benchmark sintético de ~200 snippets em escopo de TCC não fornece.

**Critério.**
- **Dado** PR contendo finding `violation_candidate` reportado pelo sistema,
- **quando** o autor solicita merge,
- **então** o GitHub não impede a operação de merge com base no Report; o status check do workflow registra `success` sempre que a execução do sistema completa sem erro terminal, independente do conteúdo dos findings emitidos.

**Refs.** `architecture-overview.md` §6, §7.3; `proposta-tcc2.md` §4.e.