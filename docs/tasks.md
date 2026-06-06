# Tasks — Implementação Fase 2

**Status.** Milestone A fechado em sessão #25 (gate milestone-level via MCP Inspector CLI mode; evidence pack em docs/process/milestoneA.md). Milestone B fechado em sessão #35 (gate milestone-level PASS empírico contra RF-008 rule-set-axis; evidence em docs/process/milestoneB.md; PRs #59 + #60 mergeadas). Milestone C em autoria de design — coordinator.md skeleton v2 aplicado via PR #63 sob A'' (system_prompt direto sem AgentDefinition) + (b2) (subagentes mantêm acesso direto a policy://vocabularies via ReadMcpResourceTool per ADR-0005 D4) + quíntupla canônica do lockdown agent CI/CD-headless + quatro camadas de enforcement (defense candidate D2.3); Gate 1 PASS empírico (sessão Code #38, claude-agent-sdk==0.2.87, script tracked em scripts/smoke_tests/sdk_tooluseblock_shape/); specs leves dos cinco subagentes em redação ordem Reporter → Triager → Detector → Classifier → Matcher (sessão #38+); tasks T11+ a decompor pós-specs. Milestone D referenciado nominalmente; autoria deferida.

**Governance.** ADR-0008 amended (2026-05-16) — granularidade de 8-12 tasks de 1-3h agrupadas em milestones; gate task-level (function tests + revisão Chat independente) e gate milestone-level (manual exercise contra RFs). Tasks neste documento ancoram função; milestones ancoram capability declarada em `docs/REQUIREMENTS.md`.

**Source-of-truth.** `docs/REQUIREMENTS.md` (RFs/RNFs sob §2 do ADR-0008); specs canonical+compact em `docs/specs/policy-reader/` e `docs/specs/semgrep-runner/`; `docs/architecture-overview.md`; `policy/SCHEMA.md`; `policy/policy.yaml`; `policy/clauses/POL-000.yaml`. Em divergência entre canonical.md e SCHEMA.md/YAML real, este documento adota o lado dos artefatos reais e anota o débito (ver §Companion edits cross-doc no fim).

**Convenção de IDs.** T01-T0NN sequencial cross-milestone (não reinicia por milestone). Cada task carrega cinco subseções: Função entregue, Dependências, Files previstos (sugestão — Code organiza o resto), Acceptance scenarios task-level (function-specific, não RF-shaped), Gate task-level.

---

## Milestone A — policy-reader standalone validado

**Capacidade entregue.** Servidor MCP `policy-reader` operacional como artefato standalone: carrega Política versionada no startup, expõe três resources (`policy://catalog`, `policy://schema-version`, `policy://vocabularies`) e três tools (`get_clause`, `find_clauses_by_law_article`, `check_applicability`) conforme `docs/specs/policy-reader/canonical.md`. Validável end-to-end via MCP Inspector cross-tool, sem dependência de outros componentes do sistema.

**RFs/RNFs cobertas no gate milestone-level.** RF-004-parcial (avaliação de conformidade sobre `collection`; entrega end-to-end requer Matcher subagent em Milestone C, mas T03 entrega o motor de veredito e o filtro de escopo MVP), RF-005 (veredito `indeterminate` como honestidade epistêmica), RF-007-parcial (composição intra-jurisdição via `accepted_law_identifiers` no nível do componente; observabilidade end-to-end requer pipeline multi-agente), RF-008-parcial (substituição de framework no nível do componente; substituição end-to-end requer Milestone C), RF-009 (provenance temporal e jurisdicional em vereditos).

**RNF-001 não bound a Milestone A.** Reprodutibilidade é propriedade sistêmica observável em CI cross-system (Milestone D), não capability de um servidor isolado. Loader determinístico é precondição implícita atendida pelos AS de T01, mas não constitui critério de gate milestone-level próprio.

**Gate milestone-level.** A redigir em sessão Chat dedicada após Tasks T01-T04 completarem gate task-level. Mecanismo conforme ADR-0008 §3: manual exercise via MCP Inspector exercitando cada RF acima, com cenários Dado/Quando/Então redigidos com Tasks já implementadas como referência operacional. Placeholder neste documento; detalhamento em sessão futura.

### Pré-implementação Milestone A — provisão a fechar fora deste documento

Uma provisão precede o início de T03 especificamente. Não bloqueia T01, T02a, T02b ou T04 — Code pode começar Milestone A pelo topo sem que esteja fechada.

**POL-001 — pacote teste de quatro cláusulas para check_applicability.** A Política atualmente contém apenas POL-000 (vocabulário estruturador de classes de dados, sem cláusulas substantivas avaliáveis). T03 precisa de cláusulas substantivas mínimas para exercitar os quatro vereditos de `check_applicability` com fixtures reais. Pack mergeado em `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/` como fixture de teste isolada — sem rationale files, sem bump de `policy_version`, sem estabilização de SCHEMA §6. Detalhamento operacional (AS coverage por arquivo, pattern de fixture root assembly via `tmp_path`, ressalvas) no README do próprio pack. Design intent das quatro cláusulas abaixo, mantido como registro histórico da decisão.

Pacote mínimo proposto, quatro cláusulas, cada uma calibrada para um veredito específico de `check_applicability` ou um caso modal de `get_clause` / `find_clauses_by_law_article`. Estrutura `substantive` conforme `policy/SCHEMA.md` §6:

- **POL-001 — Coleta com requisito de base legal explícita.** Status `active`. Governa categoria de dados de POL-000.yaml a ser confirmada na redação canônica (sugestão: categoria de identificação se existir nominalmente em POL-000.yaml; análoga caso contrário). `operation: collection`. Requirement: `legal_basis` não-nulo, valor pertencente ao vocabulário `policy/vocabularies/LGPD/lawful_basis.yaml`. Exercita verdict `compliant` quando context declara base válida; exercita `violation_candidate` quando context omite a base ou declara valor fora do vocabulário.

- **POL-002 — Coleta com requisito de anonimização (controle).** Status `active`. Governa categoria de dados de POL-000.yaml a ser confirmada na redação canônica. `operation: collection`. Requirement: controle `anonymization_required` (token canônico do vocabulário `control` LGPD). Exercita verdict `indeterminate` quando context tem categoria e operação matching mas não há mecanismo de declarar transformação efetiva no inputSchema da tool — análise estática local não decide, dimensão fica para verificação manual. Exercita `violation_candidate` se redação posterior introduzir mecanismo de declaração que indique ausência explícita.

- **POL-003 — Cláusula deprecated com sucessor.** Status `deprecated`. Bloco `tombstone` com `successors: [POL-004]`, `effective_until: <data a definir na redação>`, `deprecation_reason: <texto a redigir>`. `statutory_reference` populado para exercitar AS-3 de T02b (exclusão de deprecated em busca por artigo). Exercita: `get_clause` retornando bloco tombstone completo (T02a AS-2); `find_clauses_by_law_article` excluindo do resultado (T02b AS-3); `check_applicability` retornando `CLAUSE_DEPRECATED` retryable com `details` completo (T03 AS-7).

- **POL-004 — Sucessor de POL-003 cobrindo categoria distinta.** Status `active`. Governa categoria de dados distinta de POL-001 e POL-002, escolhida para que context típico de teste das demais cláusulas não case POL-004. Exercita verdict `not_applicable` em T03 AS-4 (cláusula não governa o context).

Validação na redação canônica: nomes de categorias substituídos por valores reais de `policy/clauses/POL-000.yaml`; valores de `legal_basis`, `operation` e `control` consumidos do vocabulário jurisdicional carregado, não hardcoded; estrutura `substantive` completa contra `policy/SCHEMA.md` §6.

---

### T01 — Loader + handshake schema-version

**Função entregue.** Loader que lê `policy/policy.yaml`, `policy/clauses/*.yaml` e `policy/vocabularies/<framework>/*.yaml` no startup do servidor; valida estrutura contra `policy/SCHEMA.md` (estrutural) e contra vocabulários jurisdicionais (semântico — valores de campos governados); valida coerência cross-arquivo (cláusulas × header) conforme SCHEMA.md §4.5 e §3.1; popula estado interno do servidor; aborta antes de `mcp.run()` em qualquer falha de I/O ou validação. Loader aceita root parametrizado (env var `POLICY_READER_ROOT` ou parâmetro de construção) para suporte a fixtures de teste e ao AS-5 de T04 (substituição GDPR). Resource `policy://schema-version` retorna trinca `(policy_schema_version, policy_version, legal_framework)` + `compatible_schema_range`, conforme spec canonical §3.2.

**Dependências.** Nenhuma upstream. Pré-implementação ratificada: ADR-0004 (FastMCP 3.x + uv) ✓; ADR-0007 (escopo MVP) ✓.

**Files previstos** (sugestão; Code organiza o resto):
- `src/mcp_servers/policy_reader/loader.py` (novo)
- `src/mcp_servers/policy_reader/models.py` (novo — Pydantic do header da Política, vocabulário e cláusula)
- `src/mcp_servers/policy_reader/server.py` (existente como stub do skeleton — substituir implementação de `policy://schema-version`)
- `tests/mcp_servers/policy_reader/test_bootstrap.py` (novo — primeira task a estabelecer o diretório `tests/`)

**Acceptance scenarios task-level.**

- **AS-1 — Startup OK em Política válida.** Dado o estado atual de `policy/` (`policy.yaml` + `clauses/POL-000.yaml` + `vocabularies/LGPD/{operation,lawful_basis,control,out_of_scope}.yaml`, todos presentes e válidos), quando o servidor é iniciado, então `mcp.run()` é alcançado sem exceção e o estado interno carrega header da Política, lista de cláusulas e mapping de vocabulários jurisdicionais.

- **AS-2 — Startup aborta em arquivo de vocabulário faltante.** Dado `policy/vocabularies/LGPD/operation.yaml` ausente (e demais arquivos íntegros, via fixture com root parametrizado), quando o servidor é iniciado, então o processo termina com exit code não-zero antes de `mcp.run()` ser chamado, com mensagem descritiva no stderr identificando o arquivo ausente.

- **AS-3 — Startup aborta em violação estrutural de SCHEMA.md (header).** Dado `policy/policy.yaml` com header inválido (e.g., `legal_framework` ausente, ou `policy_schema_version` fora de `compatible_schema_range`), quando o servidor é iniciado, então o processo termina com exit code não-zero e mensagem citando o campo violado e a regra de SCHEMA.md infringida.

- **AS-4 — Startup aborta em divergência incompatível cláusula × header.** Dado fixture com cláusula em `policy/clauses/POL-XYZ.yaml` declarando `policy_schema_version` incompatível com o `policy_schema_version` do header de `policy.yaml` (por exemplo, header `0.1.0` e cláusula `0.2.0` fora do `compatible_schema_range`), quando o servidor é iniciado, então o processo termina com exit code não-zero antes de `mcp.run()`, com mensagem identificando a cláusula divergente. Conforme SCHEMA.md §4.5 (cláusula carrega `policy_schema_version` redundante por design; divergência incompatível aborta carregamento).

- **AS-5 — Startup aborta em cláusula citando lei fora de `accepted_law_identifiers`.** Dado fixture com header declarando `accepted_law_identifiers: [LGPD]` e cláusula contendo `statutory_reference` com entrada `{lei: CDC, artigo: X}`, quando o servidor é iniciado, então o processo termina com exit code não-zero antes de `mcp.run()`, com mensagem identificando a cláusula e a lei inválida. Conforme SCHEMA.md §3.1 e ADR-0005 Decision 1 (`accepted_law_identifiers` é vocabulário fechado para `statutory_reference.lei` em todas as cláusulas).

- **AS-6 — Startup aborta em Política sem cláusulas.** Dado fixture com `policy/policy.yaml` válido e diretório `policy/clauses/` vazio, quando o servidor é iniciado, então o processo termina com exit code não-zero antes de `mcp.run()`, com mensagem citando "Política sem cláusulas é configuração inválida do artefato". Conforme canonical.md §3.1.

- **AS-7 — Handshake retorna trinca completa.** Dado servidor iniciado em AS-1, quando `policy://schema-version` é lido, então o `ReadResourceResult` retorna `contents: [TextResourceContents]` cujo `text` é JSON serializando exatamente `{policy_schema_version, policy_version, legal_framework, compatible_schema_range}` com valores casando o header de `policy.yaml`, e `mimeType: "application/json"`.

- **AS-8 — Handshake idempotente.** Dado servidor iniciado, quando o resource é lido duas vezes em sequência, então os dois payloads são byte-idênticos.

**Gate task-level.**

*Automated.* AS-1 a AS-8 implementados em `tests/mcp_servers/policy_reader/test_bootstrap.py`; passam sob `uv run pytest`. AS-2 a AS-6 usam fixtures temporárias com root parametrizado, isoladas — não alteram `policy/` real do repo.

*Chat review.* Sessão Chat independente lê o diff e verifica: o loader consome `policy/SCHEMA.md` como contrato de validação (não duplica regras inline em código); validação cross-arquivo (AS-4 e AS-5) executa após carregamento de header e antes de exposição do estado, com mensagens citando cláusula e regra violada; `models.py` usa Pydantic 2.13.x e valida campos governados por vocabulário via `model_validator` ou validator function contra os valores carregados em runtime — não tenta usar `Literal[...]` populado dinamicamente, que é estático em definition time; registro de `policy://schema-version` em `server.py` segue convenção FastMCP 3.2.x (`@mcp.resource` decorator, retorno como `ReadResourceResult` com `contents: [TextResourceContents]`); ausência de qualquer hardcoding de `legal_framework` específico (nada de `if framework == "LGPD"` no loader — o framework vem do header e parametriza qual subdir de `vocabularies/` carregar).

---

### T02a — Tool de retrieval pontual: get_clause

**Função entregue.** Tool `get_clause(clause_id)` retorna cláusula completa (active com estrutura plena conforme `policy/SCHEMA.md` §6, ou deprecated com bloco tombstone conforme §6 + §7) ou erro de input (formato inválido, não-encontrado). Migração das tools que estão hoje registradas inline em `server.py:56-105` (skeleton) para módulo dedicado `tools.py`, mantendo registro em `server.py` via `@mcp.tool` apontando para a função. Contrato detalhado em `docs/specs/policy-reader/canonical.md` §4.1.

**Dependências.** T01 (loader popula o estado consumido). Não depende de POL-001 estar mergeado — fixtures são isoladas.

**Files previstos** (sugestão):
- `src/mcp_servers/policy_reader/tools.py` (novo — recebe as funções migradas de server.py inline)
- `src/mcp_servers/policy_reader/models.py` (modificar — Pydantic do payload de retorno e error de `get_clause`)
- `src/mcp_servers/policy_reader/server.py` (modificar — substituir implementação inline por import + decorador apontando para `tools.get_clause`)
- `tests/mcp_servers/policy_reader/test_get_clause.py` (novo)

**Acceptance scenarios task-level.**

- **AS-1 — Retorna cláusula active.** Dado `clause_id` de cláusula active existente em fixture (estrutura conforme `policy/SCHEMA.md` §6), quando a tool é invocada, então retorno carrega estrutura completa conforme spec §4.1, `isError: false`.

- **AS-2 — Retorna cláusula deprecated com tombstone.** Dado `clause_id` de cláusula deprecated em fixture (estrutura emulando POL-003 do pacote teste, conforme `policy/SCHEMA.md` §7), quando a tool é invocada, então retorno carrega bloco `tombstone` populado com `successors`, `effective_until`, `deprecation_reason`.

- **AS-3 — Erro de formato.** Dado `clause_id` que não casa `^POL-\d{3}$` (e.g., `"POL-1"`, `"pol-001"`, `"foo"`, `""`), quando a tool é invocada, então retorno tem `isError: true` e payload `{errorCode: "INVALID_CLAUSE_ID_FORMAT", message, isRetryable: false, details}` conforme spec §5.4.

- **AS-4 — Erro de não-encontrado.** Dado `clause_id` com formato válido mas inexistente (e.g., `POL-999`), quando a tool é invocada, então `errorCode: CLAUSE_NOT_FOUND`, `isRetryable: false`.

**Gate task-level.**

*Automated.* AS-1 a AS-4 em `tests/mcp_servers/policy_reader/test_get_clause.py`; passam sob `uv run pytest`. Fixtures de cláusulas em `tests/mcp_servers/policy_reader/fixtures/`, isoladas por cenário.

*Chat review.* Sessão Chat independente verifica: tool description em inglês segue a convenção observada em canonical.md §4.1-4.3 — prosa inline com elementos when-to-use, do-not-use, formato de output e condições de erro, sem seções nomeadas obrigatórias; migração de server.py inline para tools.py preserva o registro via `@mcp.tool` no server.py (tool ainda descoberta pelo runtime FastMCP); error payload conforme spec §5.

---

### T02b — Tool de retrieval filtrada: find_clauses_by_law_article

**Função entregue.** Tool `find_clauses_by_law_article(specification)` retorna lista de cláusulas active matching a specification por semântica prefix-hierarchical (match casa quando algum elemento do `statutory_reference` da cláusula stored começa hierarquicamente com a specification — conforme canonical.md §4.2), excluindo deprecated do resultado; erro quando `lei` está fora de `accepted_law_identifiers` do header.

**Dependências.** T01 (estado da Política), T02a (migração de tools.py já feita; este AS adiciona a segunda função ao módulo).

**Files previstos** (sugestão):
- `src/mcp_servers/policy_reader/tools.py` (modificar — adicionar `find_clauses_by_law_article`)
- `src/mcp_servers/policy_reader/models.py` (modificar — Pydantic da specification, payload de retorno, error)
- `src/mcp_servers/policy_reader/server.py` (modificar — registrar a segunda tool)
- `tests/mcp_servers/policy_reader/test_find_clauses.py` (novo)

**Acceptance scenarios task-level.**

- **AS-1 — Busca por artigo retorna lista matching.** Dado specification `{lei: LGPD, artigo: 7}` e fixture com cláusulas active cujo `statutory_reference` contém entrada matching, quando a tool é invocada, então retorno é lista não-vazia contendo todas as cláusulas active casando lei e artigo.

- **AS-2 — Semântica de match prefix-hierarchical.** Dado fixture com duas cláusulas active: cláusula X com `statutory_reference: [{lei: LGPD, artigo: 5}]` (sem inciso) e cláusula Y com `statutory_reference: [{lei: LGPD, artigo: 5, inciso: 1}]`, quando a tool é invocada com specification `{lei: LGPD, artigo: 5, inciso: 1}` (mais específica que a entrada de X), então o retorno contém Y mas **não** X — query mais específica que o stored não casa. Quando invocada com `{lei: LGPD, artigo: 5}` (equivalente ao stored de X e prefixo do stored de Y), o retorno contém **ambas** X e Y. Match casa quando o elemento stored começa hierarquicamente com a specification (specification ≤ stored), conforme canonical.md §4.2.

- **AS-3 — Deprecated excluído.** Dado fixture contendo cláusula deprecated cujo `statutory_reference` casaria a specification por prefix-hierarchical, quando a tool é invocada, então a cláusula deprecated não aparece no retorno.

- **AS-4 — Lista vazia, não erro.** Dado specification válida sem cláusulas correspondentes em fixture, quando a tool é invocada, então retorno é `[]` e `isError: false`.

- **AS-5 — Lei fora do vocabulário.** Dado specification `{lei: GDPR, artigo: 6}` em Política com `accepted_law_identifiers: [LGPD]`, quando a tool é invocada, então `errorCode: INVALID_LAW_IDENTIFIER`, `isRetryable: false`.

**Gate task-level.**

*Automated.* AS-1 a AS-5 em `tests/mcp_servers/policy_reader/test_find_clauses.py`; passam sob `uv run pytest`. Fixtures isoladas por cenário, podem reusar parcialmente as de T02a.

*Chat review.* Sessão Chat independente verifica: tool description segue convenção observada em canonical §4.2; semântica prefix-hierarchical de AS-2 implementada explicitamente — não por coincidência de igualdade campo-a-campo, mas por algoritmo que verifica "specification é prefixo do stored"; o split entre `get_clause` e `find_clauses_by_law_article` permanece em duas tools separadas (não unificadas com flag); validação de `INVALID_LAW_IDENTIFIER` consulta `accepted_law_identifiers` do header carregado, não uma lista hardcoded em código; AS-3 está implementado por filtro explícito sobre `status: deprecated`, não por inferência.

---

### T03 — Tool check_applicability: 4 vereditos + provenance

**Função entregue.** Tool `check_applicability(clause_id, structured_context)` retorna veredito no conjunto `{compliant, violation_candidate, indeterminate, not_applicable}` com trinca de provenance `(policy_schema_version, policy_version, legal_framework)` em todo retorno em sucesso. Implementa honestidade epistêmica via `indeterminate` quando análise estática não decide (RF-005). Implementa filtro de escopo MVP via `not_applicable` para `operation ≠ collection` antes do matching de cláusulas, evitando invocação de matching fora de escopo (RF-004, ADR-0007). Erros de input conforme spec §5.4. `CLAUSE_DEPRECATED` retryable com `details` completo quando cláusula referenciada está deprecated.

**Dependências.** T01 (estado da Política), T02a (módulo `tools.py` já estabelecido). Pré-implementação obrigatória: pack POL-001..POL-004 disponível em `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/` (estrutura e pattern de fixture root assembly via `tmp_path` documentados no README do pack).

**Files previstos** (sugestão):
- `src/mcp_servers/policy_reader/tools.py` (modificar — adicionar `check_applicability`)
- `src/mcp_servers/policy_reader/models.py` (modificar — Pydantic de `structured_context`, `verdict`, `verification_scope`, `evidence`, `contradicted_requirement`)
- `src/mcp_servers/policy_reader/server.py` (modificar — registrar tool)
- `tests/mcp_servers/policy_reader/test_check_applicability.py` (novo)

**Nota sobre nomenclatura do `structured_context`.** O inputSchema da tool segue `docs/specs/policy-reader/canonical.md` §4.3 — campos `data_categories`, `operation`, `legal_basis`, `destination`. `legal_basis` é declarado como string livre no inputSchema, não vocabulário fechado — a validação contra `policy/vocabularies/<framework>/lawful_basis.yaml` é responsabilidade da camada que produz o `structured_context` (Classifier), não da tool. Existe drift cross-doc entre estes nomes e os campos descritos em `docs/REQUIREMENTS.md` RF-003 (`operation_type`, `declared_legal_basis`, `declared_transformations`), que descrevem a saída do Classifier antes de adapter. Este documento adota canonical.md por ser o contrato da tool sob teste; sync RF-003 ↔ canonical §4.3 é débito anotado em Companion edits cross-doc.

**Acceptance scenarios task-level.**

- **AS-1 — Veredito compliant.** Dado POL-001 active requerendo `legal_basis` não-nulo, e `structured_context` `{operation: collection, data_categories: [<categoria casando POL-001>], legal_basis: "<string declarada como base legal>", destination: "external_service"}` (campo `destination` opcional per canonical §4.3 — aceito sem efeito sobre o veredito), quando a tool é invocada com `clause_id: POL-001`, então `verdict: compliant`, trinca de provenance presente no payload, `isError: false`.

- **AS-2 — Veredito violation_candidate.** Dado POL-001 (mesma cláusula de AS-1), e `structured_context` que omite `legal_basis` (campo nulo), quando a tool é invocada, então `verdict: violation_candidate`, payload contém `evidence` (snippet ou referência do que foi observado) e `contradicted_requirement` (qual requirement da cláusula foi contrariado), trinca de provenance presente.

- **AS-3 — Veredito indeterminate.** Dado POL-002 active requerendo controle `anonymization_required`, e `structured_context` com `operation: collection` e `data_categories` matching POL-002 (sem campo correspondente a "transformação declarada" no inputSchema da tool), quando a tool é invocada, então `verdict: indeterminate`, payload contém `verification_scope` com sub-campos `dimension`, `prescribed_treatment` e `verification_target` populados com strings não-vazias descrevendo que efetividade de anonimização upstream não é verificável por análise estática local, trinca de provenance presente.

- **AS-4 — Veredito not_applicable (cláusula não governa o context).** Dado POL-004 active governando categoria distinta de POL-001 e POL-002, e `structured_context` com `data_categories` que não casa POL-004, quando a tool é invocada com `clause_id: POL-004`, então `verdict: not_applicable`, payload contém `reason` descritiva citando o não-casamento entre context e escopo da cláusula, trinca de provenance presente.

- **AS-5 — Veredito not_applicable (escopo MVP).** Dado `structured_context` com `operation` em qualquer valor do vocabulário diferente de `collection` (e.g., `use`, `storage`, `disclosure_by_transmission`, `erasure`) e POL-001 active, quando a tool é invocada, então `verdict: not_applicable`, `reason` cita explicitamente escopo MVP v0.1.0 e ADR-0007 (formato exato a definir; conteúdo semântico: "operation outside MVP scope — only `collection` is evaluated"). O matching da cláusula não é invocado neste path — verificável por spy/mock no método de matching durante o teste.

- **AS-6 — Provenance idêntica ao header.** Dado qualquer veredito em sucesso (AS-1 a AS-5), quando o payload é inspecionado, então `policy_schema_version`, `policy_version` e `legal_framework` são exatamente os valores carregados do header de `policy.yaml` em T01, sem transformação ou normalização que altere os valores.

- **AS-7 — Cláusula deprecated.** Dado `clause_id` de cláusula deprecated (POL-003), quando a tool é invocada, então (per Option B — wire `isError: false`; envelope em `structured_content`) `errorCode: CLAUSE_DEPRECATED`, `isRetryable: true`, `details` contém `{clause_id, successors, deprecation_reason}` conforme spec §5.4 — não apenas `successors`.

- **AS-8 — Erros de validação de input.** Dado `structured_context` com `data_categories` contendo valor fora de POL-000.yaml, ou `operation` fora do vocabulário carregado, ou `data_categories: []`, quando a tool é invocada, então (per Option B — wire `isError: false`; envelope em `structured_content`) errorCode em `{INVALID_DATA_CATEGORY, INVALID_OPERATION, EMPTY_DATA_CATEGORIES}` conforme caso, `isRetryable: false`, message em português descrevendo o erro.

**Gate task-level.**

*Automated.* AS-1 a AS-8 em `tests/mcp_servers/policy_reader/test_check_applicability.py`; passam sob `uv run pytest`. Fixtures consomem o pack mergeado em `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/` via pattern de assembly de fixture root descrito no README do pack.

*Chat review.* Sessão Chat independente verifica: o filtro de `operation ≠ collection` (AS-5) executa estrutural e demonstravelmente antes do matching, não como side-effect; o mecanismo interno de reasoning de `check_applicability` (regra hardcoded em código, single LLM call, híbrido, ou qualquer outro) está livre por ADR-0005 Decision 7 — documentação em docstring é recomendada para auditabilidade futura mas não obrigatória pela ADR; em todos os casos de AS-3, `verification_scope` carrega os três sub-campos populados, nunca placeholder ou string vazia; a trinca de provenance vem de fonte única — o header carregado por T01 — e nunca é derivada ou duplicada em campo separado do código; em AS-7, `details` carrega os três campos do contrato de erro, não só `successors`.

---

### T04 — Resources catalog + vocabularies

**Função entregue.** Dois resources read-only sobre o estado da Política carregado em T01. `policy://catalog` retorna índice de cláusulas (active e deprecated, com cinco campos por item conforme canonical §3.1: `clause_id`, `title`, `status`, `article_sources_summary`, `successors` condicional; ordenados naturalmente POL-NNN; sem paginação no MVP). `policy://vocabularies` retorna objeto agregando os quatro vocabulários jurisdicionais (`operation`, `lawful_basis`, `control`, `out_of_scope`) com estrutura `{schema_version, framework, values[]}` por vocabulário. Contratos em spec §3.1 e §3.3.

**Nota sobre `article_sources_summary`.** Nem SCHEMA.md nem canonical.md especificam a forma sumarizada exata (lista de strings renderizadas, lista de objetos compactados, etc.). Esta é uma Code-decision do summary shape; o AS-2 valida apenas presença e não-vazio, e o gate Chat-review confirma que a escolha é sensata e consistente entre todos os items.

**Dependências.** T01 (estado da Política carregado e disponível, incluindo o suporte a root parametrizado introduzido em T01 para viabilizar AS-5 desta task).

**Files previstos** (sugestão):
- `src/mcp_servers/policy_reader/server.py` (modificar — registrar dois resources adicionais via `@mcp.resource`)
- `src/mcp_servers/policy_reader/models.py` (modificar se necessário — payloads dos resources)
- `tests/mcp_servers/policy_reader/test_resources.py` (novo)

**Acceptance scenarios task-level.**

- **AS-1 — Catalog lista cláusulas em ordem natural.** Dado fixture com Política contendo POL-000, POL-001, POL-002, POL-003 (deprecated) e POL-004 (root parametrizado apontando para o diretório de fixture, não para `policy/` real), quando `policy://catalog` é lido, então retorno é lista de cinco itens ordenados como POL-000, POL-001, POL-002, POL-003, POL-004.

- **AS-2 — Catalog item carrega os cinco campos contratuais.** Dado a mesma fixture, quando o resource é lido, então cada item carrega `clause_id` (matching `^POL-\d{3}$`), `title` (string não-vazia), `status` (em `{active, deprecated}`) e `article_sources_summary` (campo populado e não-vazio); items com `status: deprecated` carregam adicionalmente `successors` (lista de `clause_id`s) e items com `status: active` **não** carregam o campo `successors`.

- **AS-3 — Catalog idempotente.** Dado servidor iniciado, quando o resource é lido duas vezes em sequência, então os dois payloads são byte-idênticos.

- **AS-4 — Vocabularies agrega os quatro.** Dado servidor iniciado com `legal_framework: LGPD`, quando `policy://vocabularies` é lido, então retorno é objeto com chaves `{operation, lawful_basis, control, out_of_scope}`, cada uma carregando `{schema_version, framework, values: [...]}` populado a partir dos arquivos correspondentes de `policy/vocabularies/LGPD/`.

- **AS-5 — Vocabularies framework-agnóstico.** Dado fixture com `legal_framework: GDPR` e `policy/vocabularies/GDPR/` populado em diretório temp (root parametrizado em T01 aponta para essa fixture), quando o servidor é iniciado contra essa fixture e o resource é lido, então `values[]` reflete o conteúdo de `policy/vocabularies/GDPR/`, sem qualquer modificação em `server.py`, `loader.py`, `tools.py` ou `models.py` em relação à execução LGPD. Este AS verifica o argumento de RF-008 no nível do componente.

- **AS-6 — Vocabularies idempotente.** Dado servidor iniciado, quando o resource é lido duas vezes em sequência, então os dois payloads são byte-idênticos.

**Gate task-level.**

*Automated.* AS-1 a AS-6 em `tests/mcp_servers/policy_reader/test_resources.py`; passam sob `uv run pytest`. AS-1, AS-2 e AS-5 usam fixtures isoladas em diretórios temp via root parametrizado de T01; não exigem `policy/clauses/POL-001..004` nem `policy/vocabularies/GDPR/` no repo real.

*Chat review.* Sessão Chat independente verifica: ambos os resources são read-only e idempotentes em código (sem mutação de estado interno); `policy://vocabularies` consome o estado carregado em T01, não relê os arquivos YAML a cada invocação; `policy://catalog` aplica ordenação natural explicitamente (sem dependência de ordem de iteração de dict, que não é garantida cross-version-Python para todo caso); no payload do catalog, o campo `successors` aparece se-e-somente-se `status: deprecated`, nunca em items active; a forma escolhida para `article_sources_summary` é consistente entre todos os items e legível por humano (justificativa documentada em docstring ou comentário); ambos resources retornam `ReadResourceResult` com `contents: [TextResourceContents]` e `mimeType: "application/json"`.

---

## Milestone B — semgrep-runner standalone validado

**Capacidade entregue.** Servidor MCP `semgrep-runner` operacional como artefato standalone: carrega conjunto curado de regras Semgrep no startup, expõe uma tool (`scan_diff`) que executa Semgrep diff-aware sobre refs Git de um pull request e retorna findings estruturados com provenance completa, conforme `docs/specs/semgrep-runner/canonical.md`. Recognizers brasileiros — CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde — implementados como regras Semgrep YAML em `mcp_servers/semgrep_runner/rules/`. Validável end-to-end via MCP Inspector, sem dependência de outros componentes do sistema.

**RFs/RNFs cobertas no gate milestone-level.** RF-001 (detecção de coleta de dados pessoais com localização, snippet e `rule_id` em PR sob escopo), RF-002 (cobertura empírica dos seis identificadores brasileiros canônicos via regras de detecção e fixture pack sintético).

**RNF-001 não bound a Milestone B.** Reprodutibilidade é propriedade sistêmica observável em CI cross-system (Milestone D). Loader determinístico + `rules_version` estável são precondições implícitas atendidas pelos AS de T05, mas não constituem critério de gate milestone-level próprio.

**Gate milestone-level.** A redigir em sessão Chat dedicada após T05-T07 completarem gate task-level. Mecanismo conforme ADR-0008 §3: manual exercise via MCP Inspector exercitando RF-001 e RF-002 sobre série de seis pull requests sintéticos (um por identificador BR), validando cada Dado/Quando/Então. Pré-requisito procedural: binário `semgrep==1.163.0` instalado via `uv tool install` no ambiente do gate, conforme ADR-0010. Placeholder neste documento; detalhamento em sessão futura.

### Pré-implementação Milestone B — provisões a fechar fora deste documento

Duas provisões precedem o início de tasks específicas. Nenhuma bloqueia T05 — Code pode começar Milestone B pelo topo enquanto Provisão B é deliberada em paralelo.

**Provisão A — PR `chore/canonical-sync-C-semgrep-runner` (consolidada).** Bloqueia T06. Não bloqueia T05. Consolida quatro débitos cross-doc em PR única com commits internos separados, conforme `.claude/rules/git-conventions.md` admite quando o diff é clean e Chat-revisable.

Commits internos propostos:

1. **canonical sync.** `docs/specs/semgrep-runner/canonical.md` migrado para Option B do amendment §3 do ADR-0002: §4.3 exemplos com wire `isError: false` em sucesso E erro (drift atual: exemplo de SCAN_TIMEOUT mostra `"isError": true`); §8.5 wire format bullets atualizados para refletir discriminação por presença de `errorCode` em `structuredContent`, não por wire flag; §8.<final> review pass contra prosa, eliminando referências remanescentes a wire `isError: true` em erros de domínio. Adicionalmente, §6 da spec é alinhada a §8.6: a frase "version checked against minimum (see ADR-0001). Failure: server fails to start" é removida ou reescrita para refletir verificação per-call em T06 (canonical §8.6 + ADR-0010 são autoritativos).

2. **compact sync cirúrgico.** `docs/specs/semgrep-runner/compact.md` recebe edits dirigidos aos contract surfaces drifted, não re-derivação total — ADR-0003 Decision 1 prescreve paridade restrita a contract surfaces (tool descriptions, output schemas, error codes, anti-uses, when-to-use guidance), não prose. Drifts a sincronizar: (a) §3 tabela de errorCodes — substituir os 4 atuais (`INVALID_BASE_REF`, `INVALID_HEAD_REF`, `SCAN_TIMEOUT`, `SEMGREP_EXECUTION_FAILED`) pelos 6 do canonical §5 (`GIT_REF_NOT_FOUND`, `INSUFFICIENT_GIT_HISTORY`, `SCAN_TIMEOUT`, `SEMGREP_BINARY_UNAVAILABLE`, `SEMGREP_EXECUTION_FAILED`, `INVALID_RULE_SET`); (b) classes — `validation+system` → `business+system` (validation é vazio neste componente por declaração positiva, ADR-0002 Decision 4); (c) retryability — `SCAN_TIMEOUT` non-retryable → retryable, `SEMGREP_EXECUTION_FAILED` non-retryable → retryable (alinha com ADR-0002 Decision 3 "system — isRetryable: true in almost all cases"); (d) timing de `SEMGREP_BINARY_UNAVAILABLE` — caught at startup → per-call (canonical §8.6 + ADR-0010 são autoritativos); (e) wire format em §3 e §5 — alinhar a Option B amended.

3. **README pin de Semgrep.** Seção "Setup" do README documenta `uv tool install semgrep==1.163.0` como prerequisite alongside Python 3.12.7 via pyenv-win e Node 24, conforme ADR-0010 §"Consequences" item negativo (mitigação).

4. **ADR-0001 Decision 2 amendment in-place.** Espelha o pattern de amendment de ADR-0008 (2026-05-16). Adicionar bloco "Amendment scope (data)" no topo do ADR, declarando que Decision 2 foi atualizada para refletir o pivô Presidio → Semgrep formalizado em ADR-0010 e os pins reais de `uv.lock` (FastMCP 3.2.4, Pydantic 2.13.4, MCP 1.27.1). Rationale do amendment in-place: ADR-0001 Decision 2 foi authorada como sugestão de stack ainda sem deliberação (canonical package recomendado), não como decisão técnica deliberada; o pivô para Semgrep e os pins explícitos emergiram durante implementação e nunca foram amended retroativamente, gerando drift fundacional na documentação técnica do TCC. Decision 2 reescrita com a stack real; demais decisões intactas. Companion edits dentro do próprio ADR para aplicar.

Custo estimado: ~2h Chat de deliberação dos quatro commits + ~1.5h Code aplicando = ~3.5h total.

**Provisão B — PR `feat/fixtures/recognizers-pack-br`.** Bloqueia T07. Não bloqueia T05 nem T06 (ambos usam regra placeholder simples de T05). Análogo ao pack POL-001..004 da Fase 1.5 de Milestone A.

Pacote mínimo proposto: seis snippets positivos sintéticos (um por identificador BR canônico), cada um cobrindo padrão representativo de coleta em Python — parameter naming (`def f(cpf: str)`), dict key access (`payload['cpf']`), attribute assignment (`user.cpf = ...`), log payload structured (`logger.info(msg, cpf=...)`). Pelo menos uma cobertura para cada um dos seis identificadores; combinações alternativas (e.g., variações com e sem máscara, com e sem hífen, formatos válidos vs inválidos do check digit) deliberadas em sessão Chat dedicada. Adicionalmente, snippets negativos (false positive control) — strings que casariam regex ingênuo mas não são identificador real, e.g., `version="123.456.789-00"`. README do pack documenta AS coverage por arquivo, análogo ao README de POL-001..004.

Decisão de escopo registrada: linguagem do MVP é Python apenas. Cobertura JS é pendência de evolução documentada em §"Pós-Milestone B aberto"; o argumento arquitetural de RF-008 generalizado para detecção sintática é defensável pela propriedade de "expandir cobertura sem refactor de código", validada em uma linguagem; demonstração empírica em segunda linguagem é evolução opcional, não invariante do MVP.

Identificadores SINTÉTICOS apenas — algoritmicamente válidos (passam check digit) mas fictícios; nunca personagens reais ou dados pessoais reais coletados. Conferir convenção em `.claude/rules/privacy-safety.md` durante a redação dos snippets.

Custo estimado: ~1.5-2h Chat de deliberação dos snippets/padrões + ~30min Code aplicando = ~2-2.5h total.

---

### T05 — Server skeleton + rule set loader

**Função entregue.** Estrutura `src/mcp_servers/semgrep_runner/` em FastMCP 3.2.x, mirror estrutural de `src/mcp_servers/policy_reader/`. Loader que lê arquivos de regra Semgrep YAML de `mcp_servers/semgrep_runner/rules/` no startup, valida que cada arquivo é YAML sintaticamente parseável (validação semântica das regras é responsabilidade do Semgrep em runtime — `INVALID_RULE_SET` é detectado em T06 quando subprocess executa, não no loader). Calcula `rules_version` como hash determinístico do diretório `rules/`, decisão fechada nesta task entre as três alternativas listadas em canonical §6 (hash determinístico vs semver manual vs combinação): hash determinístico é mais simples, não exige manutenção manual no rule set, alinha com o pattern de constantes hardcoded em `loader.py` do `policy-reader` (`_VOCABULARY_FILES` é fixo no design). Tool `scan_diff` registrada como stub que retorna envelope `NOT_IMPLEMENTED` em sucesso — desaparece em T06. Per canonical §8.6, ausência do binário `semgrep` no PATH NÃO aborta o startup; verificação per-call vive em T06.

**Dependências.** Nenhuma upstream. Pré-implementação ratificada: ADR-0004 (FastMCP 3.x + uv) ✓; ADR-0010 (Semgrep 1.163.0 via `uv tool install`) ✓.

**Files previstos** (sugestão; Code organiza o resto):
- `src/mcp_servers/semgrep_runner/__init__.py` (novo)
- `src/mcp_servers/semgrep_runner/loader.py` (novo — `load_rules`, `compute_rules_version`, `resolve_runner_root`)
- `src/mcp_servers/semgrep_runner/errors.py` (novo — `RulesLoadError` exception, análogo a `PolicyLoadError`)
- `src/mcp_servers/semgrep_runner/models.py` (novo — Pydantic placeholder `LoadedRules`)
- `src/mcp_servers/semgrep_runner/server.py` (novo — FastMCP instance, `_bootstrap`, registro do `scan_diff` stub via `@mcp.tool`)
- `mcp_servers/semgrep_runner/rules/_placeholder.yaml` (novo — regra Semgrep que casa literal de teste, removida em T07)
- `tests/mcp_servers/semgrep_runner/test_bootstrap.py` (novo)

**Acceptance scenarios task-level.**

- **AS-1 — Startup OK em diretório `rules/` populado.** Dado o estado de `mcp_servers/semgrep_runner/rules/` contendo ao menos um arquivo YAML válido (no mínimo o `_placeholder.yaml`), quando o servidor é iniciado, então `mcp.run()` é alcançado sem exceção e o estado interno carrega lista de arquivos de regra e `rules_version` computado.

- **AS-2 — Startup aborta com diretório `rules/` ausente.** Dado fixture com root parametrizado apontando para diretório sem subdir `rules/`, quando o servidor é iniciado, então o processo termina com exit code não-zero antes de `mcp.run()` ser chamado, com mensagem descritiva no stderr identificando o diretório ausente.

- **AS-3 — Startup aborta com arquivo YAML sintaticamente inválido em `rules/`.** Dado fixture com root parametrizado e `rules/broken.yaml` contendo conteúdo não-parseável (chave duplicada ou indentação inválida), quando o servidor é iniciado, então o processo termina com exit code não-zero antes de `mcp.run()`, com mensagem citando o arquivo e o erro de parsing.

- **AS-4 — Startup aborta com `rules/` vazio.** Dado fixture com root parametrizado e diretório `rules/` existente mas sem arquivos YAML, quando o servidor é iniciado, então o processo termina com exit code não-zero com mensagem citando "Rule set vazio é configuração inválida". Análogo ao AS-6 de T01 (Política sem cláusulas).

- **AS-5 — `rules_version` determinístico.** Dado fixture com `rules/` populado e estável, quando `compute_rules_version` é invocado duas vezes em sequência sem alteração no diretório, então os dois retornos são byte-idênticos.

- **AS-6 — `rules_version` muda com conteúdo.** Dado `rules_version` v1 computado contra fixture inicial, quando um novo arquivo YAML é adicionado em `rules/` (ou um existente é editado), `compute_rules_version` é re-invocado, e o retorno difere de v1.

- **AS-7 — Tool `scan_diff` registrada com description final.** Dado servidor iniciado em AS-1, quando o cliente MCP invoca `list_tools`, então a lista carrega `scan_diff` com a description exatamente conforme canonical §4.2 / compact §5.1 (formas paritárias pós canonical-sync-D; texto em inglês, sem markdown, três parágrafos em prosa plana), independentemente de a implementação ainda ser stub.

- **AS-8 — Stub de `scan_diff` retorna envelope claro.** Dado servidor iniciado em AS-1, quando `scan_diff` é invocada com refs válidos, então (per Option B — wire `isError: false`) retorna envelope `{errorCode: "NOT_IMPLEMENTED", message, isRetryable: false, details: {task: "T05"}}` em `structuredContent`, sinalizando que a tool aguarda implementação completa em T06.

**Gate task-level.**

*Automated.* AS-1 a AS-8 em `tests/mcp_servers/semgrep_runner/test_bootstrap.py`; passam sob `uv run pytest`. AS-2 a AS-6 usam fixtures temporárias com root parametrizado via `tmp_path`, isoladas — não alteram `mcp_servers/semgrep_runner/rules/` real do repo.

*Chat review.* Sessão Chat independente verifica: o loader segue o pattern de `policy_reader/loader.py` em organização (helpers privados `_read_yaml`, `_load_*` + orquestrador público `load_rules`) e exception handling (`RulesLoadError` análogo a `PolicyLoadError`; bootstrap em `server.py` traduz para `sys.exit(1)` antes de `mcp.run()`); resolução de root via env var `SEMGREP_RUNNER_ROOT` análoga a `POLICY_READER_ROOT`; `compute_rules_version` documenta em docstring a decisão de hash determinístico citando as três alternativas de canonical §6 e a justificativa pela escolhida; registro de `scan_diff` em `server.py` via decorator `@mcp.tool` da FastMCP 3.2.x retornando `ToolResult`; ausência de qualquer verificação de PATH do binário `semgrep` no startup (canonical §8.6 prescreve per-call); consulta a `.claude/rules/mcp-testing.md` durante o desenho dos testes para padrões corretos de exercício MCP via Inspector ou direct call.

---

### T06 — Tool `scan_diff`: contrato completo (subprocess + 6 errorCodes + wire format)

**Função entregue.** Implementação completa de `scan_diff(base_ref, head_ref)` substituindo o stub de T05. Invoca subprocess Semgrep com flag `--baseline-commit` para diff-aware scan. Parseia output JSON do Semgrep. Monta payload `{scan_metadata, findings}` conforme canonical §4.2-4.3. Implementa os seis errorCodes do canonical §5 com retryability conforme tabela §5 e ADR-0002 Decision 3. Timeout via env `SEMGREP_RUNNER_TIMEOUT_SECONDS` (default 300s) com SIGTERM + grace period + SIGKILL (Windows equivalente via `subprocess.Popen.kill()` — sem signal POSIX nativo). Per canonical §8.6, verificação de disponibilidade do binário `semgrep` no PATH ocorre per-call no entry point da tool, emitindo `SEMGREP_BINARY_UNAVAILABLE` se ausente; não aborta processo. Wire format conforme ADR-0002 amendment §3 Option B: sucesso e erro ambos com wire `isError: false`; envelope em `structuredContent` discriminado pela presença de `errorCode`.

**Dependências.** T05 (bootstrap, rule set loader, `rules_version`). **Pré-implementação obrigatória.** Provisão A (canonical-sync-C + README pin + ADR-0001 amendment + drift residuais) mergeada antes do início desta task. Sem isso, T06 implementa contra spec drifted pré-Option B.

**Files previstos** (sugestão):
- `src/mcp_servers/semgrep_runner/tools.py` (novo — `scan_diff` implementation, subprocess management, timeout handling)
- `src/mcp_servers/semgrep_runner/models.py` (modificar — Pydantic de `ScanMetadata`, `Finding`, `Location`, error envelopes)
- `src/mcp_servers/semgrep_runner/server.py` (modificar — substituir delegação ao stub de T05 por delegação a `tools.scan_diff`)
- `tests/mcp_servers/semgrep_runner/test_scan_diff.py` (novo)

**Acceptance scenarios task-level.**

- **AS-1 — Caso normal: findings emitidos.** Dado fixture Git repo construído em `tmp_path` com diff entre `base_ref` e `head_ref` contendo snippet que casa a regra `_placeholder.yaml` carregada por T05, quando a tool é invocada, então `structuredContent` carrega `{scan_metadata, findings}` com `findings` não-vazia; cada finding tem `rule_id`, `rule_severity` em `{info, warning, error}`, `rule_message`, `location` com `path` relativo ao repo root, `start_line/start_col/end_line/end_col` inteiros 1-indexed, e `snippet` string preenchida; wire `isError: false`.

- **AS-2 — Empty findings é estado normal.** Dado fixture Git repo com diff entre refs válidos que não casa nenhuma regra carregada, quando a tool é invocada, então retorno carrega `scan_metadata` completo e `findings: []`, wire `isError: false`.

- **AS-3 — Diff vazio.** Dado `base_ref == head_ref` (commits idênticos), quando a tool é invocada, então retorno é `{scan_metadata: {...}, findings: []}`, wire `isError: false`, sem erro.

- **AS-4 — `GIT_REF_NOT_FOUND`.** Dado `base_ref` ou `head_ref` sintaticamente válido mas inexistente no repo (e.g., commit hash que nunca existiu), quando a tool é invocada, então (per Option B) `structuredContent` carrega `{errorCode: "GIT_REF_NOT_FOUND", message, isRetryable: false, details: {ref_param, ref_value, hint}}`, wire `isError: false`.

- **AS-5 — `INSUFFICIENT_GIT_HISTORY`.** Dado fixture Git repo shallow (clone com `--depth=1`) ou condição equivalente mockada, quando a tool é invocada com refs que exigiriam merge-base resolution, então retorno carrega `errorCode: "INSUFFICIENT_GIT_HISTORY"`, `isRetryable: false`, `details: {hint: "increase actions/checkout fetch-depth"}`.

- **AS-6 — `SCAN_TIMEOUT`.** Dado `SEMGREP_RUNNER_TIMEOUT_SECONDS=1` no env e fixture com diff que ultrapassa 1s (ou regra com sleep injection), quando a tool é invocada, então retorno carrega `errorCode: "SCAN_TIMEOUT"`, `isRetryable: true` (alinha com ADR-0002 Decision 3), `details: {timeout_seconds: 1, elapsed_seconds, partial_findings_discarded: true}`.

- **AS-7 — `SEMGREP_BINARY_UNAVAILABLE` per-call.** Dado servidor iniciado em condições normais (PATH contém `semgrep` no startup), e em seguida o PATH é manipulado in-test para remover `semgrep`, quando a tool é invocada após a manipulação, então retorno carrega `errorCode: "SEMGREP_BINARY_UNAVAILABLE"`, `isRetryable: false`, `details: {searched_paths}`. Este AS valida o pin de canonical §8.6: verificação per-call, não startup; ausência não aborta o processo.

- **AS-8 — `SEMGREP_EXECUTION_FAILED`.** Dado mock do subprocess Semgrep retornando exit code 2 (Semgrep fatal error não-categorizado) com stderr não-vazio, quando a tool é invocada, então retorno carrega `errorCode: "SEMGREP_EXECUTION_FAILED"`, `isRetryable: true`, `details: {exit_code: 2, stderr_excerpt}`.

- **AS-9 — `INVALID_RULE_SET`.** Dado fixture com regra em `rules/broken_rule.yaml` que é YAML parseável (passou T05 AS-3) mas semanticamente inválida para Semgrep (pattern com sintaxe Semgrep inválida que dispara exit 4 ou 5), quando a tool é invocada, então retorno carrega `errorCode: "INVALID_RULE_SET"`, `isRetryable: false`, `details: {exit_code, stderr_excerpt}`.

- **AS-10 — Provenance em `scan_metadata`.** Dado qualquer retorno em sucesso (AS-1, AS-2, AS-3), quando o payload é inspecionado, então `scan_metadata` carrega `rules_version` (matching o valor computado por T05), `semgrep_version` (string da versão do binário invocado), `base_ref` e `head_ref` como commits hashes 40-char hex resolvidos (não branch names ou tags), e `elapsed_seconds` (float não-negativo).

- **AS-11 — Wire format Option B amended.** Dado sucesso (AS-1) e erros (AS-4 a AS-9), quando os payloads protocolares são inspecionados, então: em sucesso, `structuredContent` carrega `{scan_metadata, findings}` sem campo `errorCode`, e `content[0].text` é prosa em português resumindo o resultado; em erro, `structuredContent` carrega `{errorCode, message, isRetryable, details}`, e `content[0].text` reproduz `message`; em ambos os casos, wire `isError: false` no nível do `CallToolResult` protocolar.

- **AS-12 — `--baseline-commit` em uso (filtro diff-aware).** Dado fixture Git repo onde `base_ref` é commit pré-existente e `head_ref` é HEAD após adicionar arquivo NOVO que casa a regra, E onde existe arquivo PRÉ-EXISTENTE (committado em `base_ref` ou antes) que também casaria a regra, quando a tool é invocada, então `findings` carrega apenas o finding do arquivo NOVO; o finding pré-existente NÃO aparece, confirmando uso de `--baseline-commit` e não scan completo (canonical §8.6).

- **AS-13 — Subprocess limpo após timeout.** Dado AS-6 disparou SCAN_TIMEOUT, quando o helper `_pid_alive_windows` (conftest, via `tasklist /FI`) é consultado no teardown do teste, então o PID do subprocess não está mais ativo — `Popen.kill()` (TerminateProcess no Windows, invocado internamente por `subprocess.run` em `TimeoutExpired`) completou a terminação. Teste marcado Windows-only via `@pytest.mark.skipif`; ambiente target é Windows 11 corporate (CLAUDE.md §Stack), POSIX dispatch dispensado para evitar dep nova de psutil (`.claude/rules/windows-tooling.md`).

**Gate task-level.**

*Automated.* AS-1 a AS-13 em `tests/mcp_servers/semgrep_runner/test_scan_diff.py`; passam sob `uv run pytest`. AS-1, AS-2, AS-3, AS-12 usam fixture Git repo real construído em `tmp_path` via `git init/add/commit`; AS-4 usa fixture com commit válido + ref inexistente; AS-5 usa shallow clone fixture ou mock; AS-7 usa monkeypatching de PATH; AS-8 e AS-9 usam mocking de subprocess com exit codes específicos; AS-6 e AS-13 usam timeout curto em env + regra com sleep injection.

*Chat review.* Sessão Chat independente verifica: tool description em `server.py` segue exatamente o texto canonical §4.2 (não paráfrase, não modificação); contrato de erro em código consome a tabela canonical §5 sem hardcoding duplicado de errorCodes em strings literais (enum ou constantes em `models.py`); per-call binary check em `tools.py` ocorre antes de qualquer operação que dependa do binário; SIGTERM precede SIGKILL no path de timeout com grace period explícito (configurável ou hardcoded com rationale documentado); wire format Option B é padrão (wire `isError: false` em todos os retornos); subprocess está garantidamente terminado em todos os paths; `--baseline-commit` é flag obrigatório passado ao subprocess; consulta a `.claude/rules/windows-tooling.md` para padrões corretos de subprocess invocation em PowerShell 5.1 sem WSL — encoding de stdout/stderr, path handling de fixture Git, signal semantics em Windows (SIGKILL não existe nativo; equivalente é `subprocess.Popen.kill()`).

---

### T07 — Six recognizers brasileiros

**Função entregue.** Substituir o `rules/_placeholder.yaml` de T05 por seis regras Semgrep YAML em `mcp_servers/semgrep_runner/rules/`, uma por identificador brasileiro canônico de RF-002: `br_cpf.yaml`, `br_cnpj.yaml`, `br_cnh.yaml`, `br_nis_pis.yaml`, `br_titulo_eleitor.yaml`, `br_cns_saude.yaml`. Cada regra cobre padrões representativos de coleta em Python — parameter naming, dict key access, attribute assignment, log payload structured — capturados pelo fixture pack BR (Provisão B). Validação empírica de cada regra contra positivos e negativos do pack. Linguagem do MVP: Python (RF-001 declara linguagem parametrizável pelo rule set; restringir a Python no MVP é decisão de escopo registrada em §"Pós-Milestone B aberto" como pendência de evolução conhecida).

**Dependências.** T06 (tool `scan_diff` funcional). **Pré-implementação obrigatória.** Provisão B (fixture pack BR mergeado em `tests/mcp_servers/semgrep_runner/fixtures/recognizers_pack_br/`).

**Files previstos** (sugestão):
- `mcp_servers/semgrep_runner/rules/br_cpf.yaml` (novo)
- `mcp_servers/semgrep_runner/rules/br_cnpj.yaml` (novo)
- `mcp_servers/semgrep_runner/rules/br_cnh.yaml` (novo)
- `mcp_servers/semgrep_runner/rules/br_nis_pis.yaml` (novo)
- `mcp_servers/semgrep_runner/rules/br_titulo_eleitor.yaml` (novo)
- `mcp_servers/semgrep_runner/rules/br_cns_saude.yaml` (novo)
- `mcp_servers/semgrep_runner/rules/_placeholder.yaml` (deletar — sai do rule set ao final desta task)
- `tests/mcp_servers/semgrep_runner/test_recognizers_br.py` (novo)

**Acceptance scenarios task-level.**

- **AS-1 a AS-6 — Detecção positiva por identificador.** Uma AS por identificador BR. Dado fixture pack BR com snippet positivo para o identificador X (e.g., `recognizers_pack_br/br_cpf_function_param.py`), quando `scan_diff` é invocada com refs Git que introduzem esse snippet, então `findings` carrega ao menos um finding com `rule_id: "br-X"` (slug correspondente à regra), e ao menos um finding apontando para o arquivo do snippet via `location.path`. Asserção subset por `.claude/rules/test-strategy.md` — algumas fixtures têm múltiplos pontos de coleta cobertos pelo mesmo padrão (e.g., `br_cnh_attribute_assign.py` tem duas atribuições a `.cnh`), e o contrato "exatamente um" da forma original era contraditado pelo conteúdo das fixtures. Strict count fica para anchor tests se for invariante real. Variações cobertas conforme Provisão B README: Latin square (uma variação por padrão sintático distribuída pelos seis identificadores); transitividade implícita a outros contextos é gap documentado, pendência pós-MVP.

- **AS-7 — Negativos não disparam (false positive control).** Dado fixture pack BR com snippets negativos (strings que casariam regex ingênuo mas não são identificador real, e.g., `version_string_looks_like_cpf.py`), quando `scan_diff` é invocada com refs que introduzem esses snippets, então `findings: []` — nenhuma das 6 regras BR dispara contra os negativos.

- **AS-8 — Removida regra placeholder, sem ruído.** Dado `rules/_placeholder.yaml` deletado, quando `scan_diff` é invocada sobre o fixture pack BR completo, então `findings` carrega apenas findings das 6 regras BR (rule_ids no conjunto `{br-cpf, br-cnpj, br-cnh, br-nis-pis, br-titulo-eleitor, br-cns-saude}`); zero findings com `rule_id` começando em `_placeholder` ou similar (validates that the placeholder is fully out of the rule set).

- **AS-9 — Idempotência cross-invocations.** Dado fixture pack BR estável, quando `scan_diff` é invocada duas vezes em sequência com os mesmos refs, então os dois retornos têm `findings` byte-idênticos (mesma ordem, mesmos campos, mesmo conteúdo). Comparação é sobre a lista `findings` apenas — `scan_metadata.elapsed_seconds` varia entre invocações por design e não está no escopo da invariante de idempotência. Confirma que o ordering `(location.path, location.start_line)` ascending de compact §5.1 ("Findings list semantics") é implementado.

**Gate task-level.**

*Automated.* AS-1 a AS-9 em `tests/mcp_servers/semgrep_runner/test_recognizers_br.py`; passam sob `uv run pytest`. Fixtures consomem o pack mergeado em `tests/mcp_servers/semgrep_runner/fixtures/recognizers_pack_br/` via pattern de fixture root assembly análogo ao POL pack de Milestone A.

*Chat review.* Sessão Chat independente verifica: cada regra YAML segue convenção de naming `br-<identifier>` em `rule_id` (kebab-case, prefixo `br-` para identificadores brasileiros, slug coerente com `data_categories` que RF-003 vai consumir no Classifier em Milestone C); `languages: [python]` declarado explicitamente em cada regra; padrões Semgrep são pattern-based ou pattern-either, não regex-only (regex puro é anti-pattern em Semgrep, perde AST awareness); cada regra tem `severity` declarado com rationale (warning para identificadores comuns; error apenas se houver razão semântica forte, e.g., dados de saúde sob LGPD Art. 11 sensíveis); `metadata.category` consistente cross-regras para auditabilidade futura; `rule_message` em português conforme convenção de outputs ao usuário (ADR-0001 Decision 3); consulta a `.claude/rules/privacy-safety.md` durante construção do fixture pack confirma uso de identificadores SINTÉTICOS algoritmicamente válidos mas fictícios, sem personagens reais nem dados pessoais reais coletados.

---

## Milestone C — Pipeline multi-agente operacional local

**Capacidade entregue.** Pipeline multi-agente operacional como sistema
integrado executável localmente: coordinator Python orquestra cinco
subagentes (Triager → Detector → Classifier → Matcher → Reporter) via
chamadas sequenciais `query()` do `claude-agent-sdk` com
`system_prompt` direto em `ClaudeAgentOptions` (pattern A''),
configuradas como lockdown agent CI/CD-headless via quíntupla canônica
(`system_prompt` + `allowed_tools` + `permission_mode="dontAsk"` +
`setting_sources=[]` + `strict_mcp_config=True`); consumindo MCP
servers `policy-reader` e `semgrep-runner` via `.mcp.json` do projeto
com quatro camadas de enforcement (coordinator parsing + whitelist
EXPECTED_SERVERS; SDK isolation via `setting_sources=[]` +
`strict_mcp_config=True`; per-etapa `allowed_tools` allowlist;
`permission_mode="dontAsk"` denial enforcement de unmatched tools);
Classifier e Matcher acessam `policy://vocabularies` diretamente via
`ReadMcpResourceTool` (granularidade per-server per SDK Python);
handoff explícito de output entre etapas via scratchpad audit-only +
propagação estruturada de erros (contrato de exceptions
`CoordinatorStartupError`/`SubagentValidationFailed`/`SubagentUnresponsive`/
`ReportNotEmitted`/`MalformedToolUseBlock`); emitindo Report JSON
consolidado via tool customizada `emit_report` exposta exclusivamente
ao Reporter (dual sink: scratchpad audit + captura via
`ToolUseBlock.input` no message stream). Validável end-to-end via
execução manual de coordinator script contra PRs sintéticos no
repositório. Integração CI/CD (GitHub Action) permanece deferida para
Milestone D.

**RFs/RNFs cobertas no gate milestone-level.**
- RF-003 pleno (Classifier subagente real consumindo output do
  Detector).
- RF-004 pleno (Matcher subagente real avaliando candidatos via
  `check_applicability`, com filtro MVP-collection-only operando em
  runtime end-to-end).
- RF-005 pleno (`indeterminate` como veredito real emitido pelo Matcher
  contra context insuficiente para análise estática).
- RF-006 (Report agregado emitido via `emit_report` do Reporter; dual
  sink coordinator stream + scratchpad).
- RF-007 pleno (composição intra-jurisdição end-to-end demonstrável:
  duas Políticas com `accepted_law_identifiers` distintos produzem
  Reports diferentes sem alteração de código).
- RF-008 pleno (substituição de framework end-to-end demonstrável:
  pipeline inteira roda com Política mock GDPR sem alterar `src/`).
- RF-009 (rastreabilidade: trinca `(policy_schema_version,
  policy_version, legal_framework)` propagada do `policy-reader` até
  cada finding do Report; provenance temporal e jurisdicional
  preservada por construção do Matcher).

**RFs precondicionais** (entregues em Milestones A+B, consumidas por C
mas não bound ao gate de C): RF-001 (detecção sintática via
semgrep-runner), RF-002 (identificadores brasileiros).

**RNF-001 e RNF-002 não bound a Milestone C.** RNF-001
(reprodutibilidade) é propriedade sistêmica observável em CI
cross-system (Milestone D). RNF-002 (posicionamento operacional
informativo / não-bloqueio de merge) é observável apenas na camada
de integração CI/CD (status check do workflow), pertence a
Milestone D.

**Gate milestone-level.** A redigir em sessão Chat dedicada após
tasks T11+ completarem gate task-level. Mecanismo conforme ADR-0008
§3: manual exercise via harness Python (script
`scripts/exercise_pipeline.py` ou análogo) invocando o coordinator
com `--base-ref`, `--head-ref`, `--policy-dir`, `--rules-dir`, contra
série de PRs sintéticos check-ados no repositório (branches
`synthetic/pr-<cenário>`). Validação compara Report JSON emitido
contra Report esperado também versionado no repo. Cobertura: um
cenário por RF declarada acima (Dado/Quando/Então). Placeholder neste
documento; detalhamento + catálogo de PRs sintéticos em sessão futura.

**Gate pré-coordinator-flesh (concluído).** Gate 1 PASS empírico
documentado em `docs/specs/subagents/coordinator.md` §11 (PR #63),
ratchet via smoke-test em
`scripts/smoke_tests/sdk_tooluseblock_shape/smoke_test.py` contra
`claude-agent-sdk==0.2.87`. Três TCs (`ToolUseBlock.input` shape;
quíntupla canônica end-to-end; underscore naming resolve) passaram +
achados AC1 (tool search ON por default; stream contém
`ToolUseBlock`s intermediários) e AC2 (tipos de message no stream)
absorvidos no skeleton. Não bloqueia mais nenhuma autoria de spec.

### Pré-implementação Milestone C — provisões a fechar fora deste documento

**Provisão MC-A — autoria das specs leves dos seis agentes**
(coordinator + 5 subagentes) em `docs/specs/subagents/`. Pattern
multi-spec com coordinator.md como hub do workflow (decisão sessão
#37, ratificada #38). Cinco convenções de cross-reference + Rule 6
(Output como canonical I/O boundary) ratificadas em coordinator.md §9.
Ordem de redação híbrida:

1. ✓ coordinator-SKELETON v2 (sessões #37+#38; aplicado via PR #63 como
   `docs/specs/subagents/coordinator.md`)
2. Reporter-FLESH (sessão #38; destila `_template-subagent.md`)
3. Triager-SANITY (sessão #38; testa se template super-fitou)
4. Detector → Classifier → Matcher (sessões #38-#39; complexidade
   crescente)
5. coordinator-FLESH-COMPLETO (sessão #39+; integra learnings das 5
   specs)

Bloqueia início de tasks T11+. Não bloqueia housekeeping ADR (Provisão
MC-C), companion edit arch-overview (Provisão MC-B), nem adoção de
dependência SDK (Provisão MC-E).

**Provisão MC-B — companion edit arch-overview (three-beats Beat 2)**.
Patch único aplicável em `docs/architecture-overview.md` §3 mermaid:
substituir `T -->|skip| END[Sem ação]` por `T -->|skip| R[Reporter]`,
catalogado em coordinator.md §10. Aplicar em sessão Code curta
(~10-15min) após coordinator-flesh-completo. Bloqueia tasks T11+
(skeleton do coordinator cita three-beats Beat 2 como pendente).

(Provisão MC-B encolhida vis-à-vis proposta #37: decisão (b2) da
sessão #38 elimina os dois patches anteriores §5.1 + §5.7 que tocavam
acesso de coordinator a `policy://vocabularies`. Sob (b2), coordinator
não acessa o resource; Classifier e Matcher mantêm acesso direto via
`ReadMcpResourceTool` per ADR-0005 Decision 4.)

**Provisão MC-C — housekeeping ADR-0012 stale → ADR-0011**. PR isolada
`chore/sync-adr-references` substituindo refs stale "ADR-0012" por
"ADR-0011" (Windows-stdio E-2 foi absorvido em ADR-0011 mergeada).
Targets:

- `docs/process/milestoneB.md` linhas 50, 102, 106, 107, 112, 114 (todas
  refs stale, substituição mecânica).
- `docs/process/learning-log.md` — múltiplas linhas com triagem caso-a-caso:
  forward refs legítimas a "ADR-0012 retroativo Milestone C" são
  **preservadas** (apontam para ADR futura); refs stale para
  Windows-stdio E-2 substituídas por "ADR-0011".

Libera número ADR-0012 para retroativo Milestone C. Sessão Code
~15-20min. Não bloqueia Reporter-flesh, mas obrigatória antes de
ADR-0012 ser citada em qualquer artefato novo.

**Provisão MC-D — benchmark de PRs sintéticos para gate milestone-level**.
Catálogo de 6-8 branches `synthetic/pr-<cenário>` no repo, cada uma
com Dado/Quando/Então de uma RF declarada. Análogo a fixture pack BR
de Milestone B em estrutura. A redigir em sessão Chat dedicada após
specs dos subagentes fecharem (sessões #39-#40). Bloqueia gate
milestone-level, não tasks T11+ individuais.

**Provisão MC-E — adoção de `claude-agent-sdk` como dependência**. PR
mecânica `chore/add-claude-agent-sdk-dependency`:

- `pyproject.toml` ganha `claude-agent-sdk>=0.2.0,<1.0` em
  `[project.dependencies]` (baseline empírico 0.2.87 do smoke-test
  Gate 1; piso 0.2.0 confortável acima do mínimo `>=0.1.59` para
  `setting_sources=[]` documentado em coordinator.md §8 (evolução
  SDK); teto `<1.0` blindagem contra major bump hipotético
  que pode quebrar surface estável atual).
- `uv.lock` regenerado via `uv lock`.
- ADR-0001 (stack canônica) ganha amendment registrando adição.

Bloqueia início de tasks T11+ (T11 importará `claude_agent_sdk`).
Não bloqueia Reporter-flesh nem demais redações de spec. Sessão Code
~15-20min, single commit. Catalogada como provisão nova em sessão
#38 após Code Eureka achado lateral (uv.lock zero matches para
`claude-agent-sdk` antes do smoke-test).

**Provisão MC-F — Reporter spec 0.3.0 → 0.4.0 + module locus migration
(aplicada nesta PR / sessão #43+)**. Ratificação retroativa de DD-T15:
migração de locus dos módulos do Reporter `src/coordinator/{models,
constants,system_prompts,tools}.py` → `src/subagents/reporter/...`,
fechamento de forward-refs de `scope` (§5.4, §8.4 do reporter.md) e
correção do shape de `scope` em few-shots §5.1. Companion edits
aplicados a `coordinator.md` §inicial / §3.0 / §3.1 / §7 / §10 (T1+T2
em §3.1, C-1/C-2/C-3 + C-AUDIT, T5a..T5c markers), `docs/architecture-overview.md`
§3 mermaid (Provisão MC-B aplicada em paralelo: `T -->|skip| END` →
`T -->|skip| R[Reporter]`), e `scripts/smoke_tests/sdk_output_format_lockdown/README.md`
SF-2 (provenance bug corrigido). Catalogada originalmente em
`docs/specs/subagents/triager.md` §10.5 item 7.

### Tasks T11+

**Status.** A decompor após specs leves dos subagentes fecharem
(Provisão MC-A) E adoção de dependência SDK completar (Provisão
MC-E). Decomposição tentativa em sessão Chat dedicada (§(L) do
handoff #37→#38); provavelmente 5-7 tasks de 1-3h cada cobrindo:
`emit_report` custom tool + Reporter query implementation; Triager +
Detector queries; Classifier + Matcher queries (com `ReadMcpResourceTool`
para vocabularies); coordinator main loop com state passing + error
propagation + `.mcp.json` parsing + whitelist + quíntupla canônica
em cada query; smoke-test end-to-end com PR sintético mínimo.

Granularidade final deliberada em sessão Chat dedicada de
decomposição, análoga à #27 que decompôs Milestone B em T05-T07.

---

## Companion edits cross-doc

PRs separados ou commits internos de PRs principais, fora do escopo de implementação Code de uma task específica. Não bloqueantes para a task à qual estão anexados, anotados aqui para não perder o débito.

**Divergências as-built descobertas ao redigir `docs/funcionamento.md` (consolidar em housekeeping arch-overview/specs futuro; não corrigidas inline por disciplina de escopo):**

- **arch-overview "três eixos"** — `docs/architecture-overview.md:46` ("Versionada em três eixos independentes") conflama versionamento com identidade. Versionamento é em **dois** eixos semver (`policy_schema_version`, `policy_version`); `legal_framework` é eixo de **identidade** não-semver (`policy/SCHEMA.md:71-76`; ADR-0005). O relatório já foi corrigido para "identidade em três eixos" (#118); a arch-overview ainda diz "Versionada".
- **arch-overview coordenador-como-agente** — §5.1/§5.7 (`docs/architecture-overview.md:234`) descrevem o coordenador como agente com a tool "Despacho de subagentes". As-built é um *script* Python sem ferramenta de despacho, ausente da matriz (`src/coordinator/run.py:358-448`; relatório §2.2/§2.3 já corrigido).
- **arch-overview numeração de etapas** — §3 usa Etapa 0-4; o relatório e `docs/funcionamento.md` usam Etapa 1-5; a string user-facing em `scripts/ci/format_summary.py:51` rotula o Triager "(etapa 0)". Três numerações divergentes — reconciliar.
- **arch-overview "Reporter agrega"** — §4.3/§5.6 atribuem a agregação ao Reporter; as-built a agregação é do coordenador (`derive_run_outcome`/`aggregate_summary`/`_build_consolidated_state`, `src/coordinator/run.py:95-148`); o Reporter serializa verbatim.
- **arch-overview §5.5 nota DD-M22** — trata o handshake jurisdicional como futuro ("quando ADR-0005 materializar"); as-built já implementado como `UnsupportedLegalFramework` (`src/coordinator/run.py:443-447`; `src/coordinator/errors.py:72-87`; ADR-0007).
- **specs com lag** — `docs/specs/subagents/reporter.md` §1.5 marca os módulos do Reporter como "a criar"/inexistentes, mas existem e estão implementados (`src/subagents/reporter/`); `docs/specs/subagents/classifier.md` §4.3 descreve passthrough de 4 campos, mas o real é 5 (`src/subagents/classifier/passthrough.py:19`).
- **Quadro 1 / matriz × Matcher Read** — o Quadro 1 do relatório e a matriz de `architecture-overview` §5.7 mostram o Matcher sem `Read`, mas `_matcher_options` concede `Read` no SDK (`src/coordinator/run.py:224`); o uso de FS é vedado apenas por *system prompt*. Reconciliar com nota/footnote (já anotado em `docs/funcionamento.md` §3).

**Consolidados em Provisão A de Milestone B** (PR `chore/canonical-sync-C-semgrep-runner`, ver §Milestone B § Pré-implementação):

- canonical sync do `semgrep-runner` (Option B amendment §3 ADR-0002 + §6 vs §8.6 alignment).
- compact sync cirúrgico do `semgrep-runner` (6 errorCodes, classes, retryability, runtime vs startup do BINARY_UNAVAILABLE, wire format).
- README pin de Semgrep: documenta `uv tool install semgrep==1.163.0` como prerequisite na seção Setup, alongside Python 3.12.7 via pyenv-win e Node 24, conforme ADR-0010.
- ADR-0001 Decision 2 amendment in-place: alinha stack canônica à realidade — Semgrep (substitui Presidio menção); FastMCP 3.2.4 pin formal; Pydantic 2.13.4 pin formal; MCP 1.27.1 pin formal. Espelha pattern de amendment in-place de ADR-0008 (2026-05-16).

**Pendências cross-doc abertas pós-sessão #38** (consolidar em
Provisão MC-B de Milestone C — companion edit arch-overview):

- **arch-overview §3 mermaid** — substituir `T -->|skip| END[Sem ação]`
  por `T -->|skip| R[Reporter]` (three-beats em coordinator.md §10).

(Patches §5.1 e §5.7 anteriormente catalogados em proposta #37 foram
**removidos** sob decisão (b2) da sessão #38: coordinator não acessa
`policy://vocabularies`; Classifier e Matcher mantêm acesso direto
via `ReadMcpResourceTool` per ADR-0005 Decision 4 textbook case.)

**Pendência ADR (consolidar em Provisão MC-C — housekeeping):**

- Refs stale "ADR-0012" em `docs/process/milestoneB.md` linhas 50, 102, 106,
  107, 112, 114 apontando para Windows-stdio E-2 (que foi absorvido
  em ADR-0011 mergeada). Substituir mecanicamente por "ADR-0011".
- Refs stale "ADR-0012" em `docs/process/learning-log.md` (múltiplas linhas
  — triagem caso-a-caso). Preservar forward refs legítimas a
  "ADR-0012 retroativo Milestone C"; substituir refs stale para
  Windows-stdio E-2 por "ADR-0011".

Libera ADR-0012 para retroativo Milestone C (ADR cobre divergências
metodológicas + decisões load-bearing A'', (b2), M2, S2', dual sink
emit_report, quíntupla canônica, quatro camadas de enforcement
D2.3).

**Pendência de dependência (consolidar em Provisão MC-E):**

- Adicionar `claude-agent-sdk>=0.2.0,<1.0` em `pyproject.toml` +
  regenerar `uv.lock`. Bloqueia início de tasks T11+ (T11 importará
  `claude_agent_sdk`); não bloqueia redação de specs.

**Débito técnico catalogado (não bloqueia Milestone C; investigação
em sessão Code curta dedicada):**

- **Convenção `is_error`/`isError` em FastMCP servers existentes.**
  SDK Python do `claude-agent-sdk` usa `is_error: True` (snake_case);
  SDK TypeScript e wire format MCP usam `isError: true` (camelCase).
  FastMCP 3.2.4 (pinada em RNF-001) tem convenção própria. Servers
  existentes `policy-reader` e `semgrep-runner` foram implementados
  em Milestones A+B antes desta divergência ser catalogada;
  investigação `grep -r "isError\|is_error" src/` + checagem da
  convenção FastMCP recomendada pode revelar débito latente. Sessão
  Code curta ~20-30min; sem bloqueio até que apareça empiricamente.

**Pendência ADR-0005 (exposição estrutural de `data_categories`;
consolidar com a futura decisão de `policy://examples`, DD-C10):**

- Expor `data_categories` estrutural via `policy://vocabularies` (PR
  `feat/expose-data-categories-vocab`) adiciona um vocab framework-neutro a
  um resource cujo contrato ADR-0005 D4 descreve como jurisdicional; emenda à
  ADR-0005 (distinção estrutural-vs-jurisdicional) pendente — provável
  consolidação com a decisão futura de `policy://examples` (DD-C10), para uma
  emenda única em vez de duas fragmentadas.
- Companheiro `docs/architecture-overview.md` §5.4: descreve os três campos
  governados (`operation_type`, `data_categories`, `declared_legal_basis`)
  como restringidos aos "vocabulários jurisdicionais" — frase imprecisa para
  `data_categories` (estrutural, derivado de POL-000). Corrigir na mesma
  emenda consolidada, não inline (a nota de camada provisória já está em
  `classifier.md` §3.3 apontando para `policy-reader/canonical.md` §3.3).

**Follow-up MC-F (a aplicar em sessão futura que tocar a Triager spec):**

- **Follow-up Triager §10.5 item 1 (pós-MC-F):** a prescrição
  `output_format=TriagerDecision.model_json_schema()` é shorthand;
  o contrato wire-level é a forma envelopada `{"type": "json_schema",
  "schema": ...}`, confirmada em `scripts/smoke_tests/sdk_output_format_lockdown/smoke_test.py`
  (0.2.87) e anotada em `reporter.md` §10.6. Numa sessão futura que
  tocar a Triager spec, marcar item 1 como shorthand com cross-ref —
  alinhamento de proveniência, não decisão aberta.

**Follow-ups da consolidação coordinator §5 (DD-D5 / `DetectorScanFailed`):**

- ADR-0013: promover a nota de precedente DD-D5 (erro de tool de subagente)
  a ADR curto. Gatilho: precedente que vira contrato para o Matcher
  (ainda não escrito). Fonte: coordinator §5 nota de precedente + detector
  §6.2 DD-D5.
- Reconciliação de taxonomia de exceções: SubagentRefusedTask,
  SubagentContractViolation, SubagentExecutionError ausentes da tabela §5
  do coordinator. Passada dedicada no flesh; grepar por nome.

**Débito de spec do policy-reader (auto-correção pós-impl; smoke-test
sessão #48 — engine é a verdade pós-implementação, não roteia pelo
coordinator §10):**

- ✅ *(aplicado neste passo)* `canonical.md` §4.3, descrição de
  `legal_basis`: "semanticamente comparada" → **igualdade exata de
  token** contra `consent`; normalização atribuída explicitamente ao
  Classifier upstream. O motor (`tools.py:382-423`) compara token, não
  semântica.
- ✅ *(aplicado neste passo)* `canonical.md` §4.3, exemplo `compliant`:
  `legal_basis` em prosa PT `"consentimento explícito"` → token
  `consent`; `evidence` realinhada. A prosa rejeitada pelo motor
  produziria `violation_candidate`, não `compliant` (smoke-test #48,
  caso T1x).
- ✅ *(aplicado neste passo)* `canonical.md` §4.3, exemplo
  `indeterminate`: anotado como aspiracional/pós-MVP. Sob MVP v0.1.0,
  `operation: disclosure_by_transmission` → `not_applicable` pelo gate
  de escopo (l.585 sub-caso (i), ADR-0007 D3); confirmado smoke-test #48
  (T3/T3b). Resolve a contradição interna §4.3 (sub-caso (i) vs exemplo)
  a favor do gate-MVP.
- ✅ *(aplicado #48; aprovado por João)* `canonical.md` §4.3, exemplo
  `violation_candidate` (~l.634-663): `operation: storage` →
  `collection` (corrige o curto-circuito do gate-MVP que tornava o
  exemplo inalcançável); `legal_basis` prosa `"interesse legítimo"` →
  token `legitimate_interests`; `evidence` realinhada ao mecanismo real
  do engine (≠ token canônico `consent`).
- ⚠️ *(achado #48 — relevante para `matcher.md`, não para o exemplo)*
  **O engine MVP v0.1.0 NÃO consome o campo `category`
  (personal_data vs sensitive_data) de `lawful_basis.yaml`.** Para
  `control: consent_required`, `tools.py:382-423` compara `legal_basis`
  por igualdade exata contra o token único `consent` — não há lógica de
  Art. 11 (dado sensível exige base da categoria `sensitive_data`).
  Consequência: o engine sinalizaria como `violation_candidate` até o
  `explicit_consent` (a base legalmente correta para dado sensível),
  pois ≠ `consent`. A distinção de categoria de base legal é limitação
  conhecida do MVP; `matcher.md` deve descrever o control
  `consent_required` como comparação de token único, não como
  reasoning de categoria.

**Débito doc-lag MC-C Phase 2a (doc atrás da impl verificada; consolidar numa
sessão housekeeping futura — a correção do texto é o que minor-bumpa
`reporter.md`, mantendo DD-3: a impl Phase 2a NÃO bumpa):**

- `reporter.md` §4.5 + §6.1 (envelope de erro) ainda colocam o payload
  estruturado em `structuredContent`. Per `.claude/rules/sdk-mcp-conventions.md`
  Eixo 2 (verificado em `sdk_tool_error_channel` v1/v2), o bridge do `@tool`
  in-process **dropa** `structuredContent` — a impl (MC-C Phase 2a) serializa
  `{errorCode, message, isRetryable, details}` no `content` (JSON string) + flag
  `is_error: True`. §4.5/§6.1 absorveram o Eixo 1 (casing) mas não o Eixo 2
  (canal). Corrigir o texto dos dois loci.
- `coordinator.md` §3.1 (pseudocódigo) declara `system_prompt=TRIAGER_SYSTEM_PROMPT`
  estático no stage Triager. A impl (MC-C Phase 2a, DD-4) renderiza o template
  §5.1 via `build_triager_prompt` (triager §2.2) e o entrega como turn prompt,
  com `system_prompt=None` (SDK minimal mode, §5.1 nota) — passar o template raw
  embarcaria `{pr_number}`/`{{…}}` literais no system prompt. Alinhar o
  pseudocódigo §3.1 ao wiring real.
- `reporter.md` §6.2 — reescrever o critério de `isRetryable` em termos
  **mecânicos** (erro transitório / re-execução idêntica segura), não
  **cognitivos** (modelo-pode-reconstruir, L700). A semântica do flag é
  retry-automático-de-infra (a orquestração re-executa a chamada idêntica),
  ortogonal ao validation-retry loop conduzido pelo modelo via `content` (DD-2).
  Sob a definição mecânica, `PYDANTIC_VALIDATION=False` em §6.3 está CORRETO e a
  impl (`tools.py:85-87`) é fiel — o débito é só de prosa. Corrigir no mesmo
  housekeeping PR de §4.5/§6.1/coordinator §3.1 — mesmo minor-bump.

**Débito de contradição spec-interna MC-C Phase 2a — RESOLVIDO (ADR-0016 / PR (c)).** A guarda
de emissão-única passou a contar emissões BEM-SUCEDIDAS (sinal `99-report.json`, escrito pelo
handler só no sucesso): 2ª emissão após SUCESSO é redundância (halt); 2ª após FALHA da 1ª é
retry de validação legítimo (reporter §6.7/§9.2.a), permitido. A âncora AS-IS virou
`test_reporter_second_emit_after_{success_raises,failure_allowed}`; a rede de segurança pós-loop
(`allowed_retry` sem `99-report.json` -> `ReportNotEmitted`) impede sucesso silencioso falso.

**Débito de produto MC-C → Phase 3 (reliability hardening; categoria DISTINTA do
doc-lag e da contradição acima — é um errorCode de §6.3 declarado mas não
implementado, não um desalinhamento doc↔impl):**

- **`SCRATCHPAD_WRITE_FAIL` não implementado.** `reporter.md` §6.3 (L716)
  declara um 7º errorCode `SCRATCHPAD_WRITE_FAIL` (system-class) que o handler
  não emite: `_atomic_write_json` (`tools.py:36-42`) não tem try/except — uma
  falha de `os.replace` levanta exceção crua em vez de envelope estruturado.
  Consistente com o escopo auto-declarado da 2a (só cross-checks #1-#4), mas é o
  único ponto onde a escrita do `99-report.json` pode falhar silenciosamente.
  Phase 3: envolver `_atomic_write_json` em try/except e emitir envelope DD-2 com
  errorCode system-class em vez de exceção crua.

**Débito de conformidade de proveniência (limite conhecido ACEITO, introduzido pelo fix
do desync top-vs-finding — PR `fix/reporter-provenance-desync`; NÃO corrigir agora):**

- **Proveniência top-level nos caminhos SEM findings usa fallback (possivelmente estale).**
  O fix faz `run_pipeline` derivar a trinca top-level dos *findings* (o header da Política
  echoado por cada veredito do Matcher via `check_applicability`), eliminando o
  `MultipleReportEmissions` determinístico do caminho substantivo de eval-lgpd. Mas em
  `skipped_by_triager` / `success_no_candidates` não há finding de onde derivar, então
  `_effective_provenance` (`run.py`) cai nos parâmetros `policy_*` (default `0.1.0`), que
  podem divergir da Política carregada (e.g. eval-lgpd `0.2.0`). Inócuo: o cross-check #2 do
  `emit_report` é vácuo com zero findings (nada a comparar) e não halta — só o rótulo de
  versão no Report pode ficar estale. Conformidade total exigiria o coordinator ler o header
  da Política (resource `policy://schema-version` / `policy://catalog`) nesses caminhos —
  follow-up, fora do escopo do fix de halt. A entrada de (c) (contradição §3.5 emit-counting
  vs retry) permanece intacta acima — não é resolvida aqui.

**Débito de lint pré-existente (NÃO-MC-C; cleanup trivial em chore PR dedicado):**

- **F401 `json` não-usado em `scripts/smoke_tests/check_applicability_48b/probe.py:21`.**
  Presente em `main` ANTES da Phase 2a (confirmado por stash de todo o trabalho
  da 2a — o erro sobrevive), logo fora do escopo do PR da feature. `ruff check .`
  (repo inteiro) acusa; `ruff check src tests` (escopo da feature) está limpo.
  Fix trivial: `ruff check --fix` ou remover a linha. Atenção de sequência: se o
  CI roda `ruff check .`, o primeiro run do PR da feature fica vermelho por este
  motivo fora de escopo — resolver por fora ou num chore PR dedicado antes do merge.

---

## Pós-Milestone B aberto

Pendências de evolução conhecidas que NÃO bloqueiam progresso para Milestone C nem fazem parte do escopo formal do MVP, mas que estão registradas para serem endereçadas dentro da janela 15/06 (entrega) — 30/06 (defesa) caso haja capacidade. Materialização nessa janela fortalece a narrativa defensiva do TCC ao demonstrar empiricamente capacidade de evolução do sistema sem ampliar escopo do que foi entregue.

- **Cobertura de detecção em JavaScript/TypeScript.** Adicionar `languages: [javascript, typescript]` a regras BR existentes ou criar regras paralelas, com fixture pack JS análogo ao Python (positivos cobrindo destructuring, dot/bracket access, JSX form fields, payload schemas estilo Segment/AEP, Node req handlers; negativos para false positive control). ~6-7h totais (3h regras + 2h fixture pack JS + 1.5h tests + 1h gate análogo). Demonstra empiricamente RF-008 generalizada para detecção sintática (a propriedade arquitetural "expandir cobertura sem refactor de código" provada em duas linguagens), fortalecendo argumento de Capítulo de Resultados do TCC. Pré-requisito procedural: Milestone B gate milestone-level fechado.

---

## Milestone D — autoria deferida

Estrutura e tasks de Milestone D são autoradas em sessão Chat dedicada
após o gate milestone-level de Milestone C completar. Razão
metodológica: ADR-0008 §1 calibra tarefas a 1-3h sob escopo de
capability estabilizada — pré-autoria corre risco de drift contra
learnings emergentes da implementação do milestone corrente.

Escopo proposto a seguir é estrutura preliminar, não normativa até
autoria formal. Boundaries entre tasks dentro do milestone ficam para
a sessão de autoria correspondente:

- **Milestone D — CI/CD + validação empírica.** RFs: 006-integração,
  RNF-001, RNF-002, proposta-tcc2 §4.f. Decomposição tentativa:
  GitHub Action workflow YAML + posting de findings via API como
  inline review comments, não-bloqueante; benchmark sintético ~200
  snippets + execução de validação + Report consolidado; potencialmente
  `--strict-mcp-config` flag CLI (equivalente CLI ao
  `strict_mcp_config=True` programático já em uso pelo coordinator)
  apontando para `.github/mcp-ci.json` dedicada, isolando config CI
  contra interferência de configs locais do runner.

- **Carve-out Camada-3-MVP (entregue agora, não em Milestone D).** A GitHub
  Action de validação (`workflow_dispatch` + matrix dos 3 fixtures
  COMP-001/VIOL-001/SKIP-001, output summary, harness field-scoped contra
  `.expected-report.json`, gate qualitativo) e o shared core
  (`scripts/ci/run_review.py`, `scripts/ci/format_summary.py`,
  `eval/harness/camada3_gate.py`) são entregues na Camada-3-MVP per
  `planejamento-tcc2.md` §Camada-3-MVP. Permanece em Milestone D:
  `pull_request` em produção com posting via API e checkout de head, inline
  comments, benchmark sintético ~200 snippets (`proposta-tcc2` §4.f), gate
  quantitativo precision/recall/F1, `.github/mcp-ci.json` +
  `--strict-mcp-config` CLI. Contrato de implementação das peças novas de
  infra: o plano Passo 4 v3 ratificado — não exigem spec em `docs/specs/`,
  que é superfície de contrato do pipeline (subagentes + MCP servers), não
  do adaptador de borda CI.