# Tasks — Implementação Fase 2

**Status.** Milestone A v1.1 (sessão #18, Chat authoring; v0 → v1 absorveu auditoria Code + avaliação Chat; v1 → v1.1 absorve terceira passada Code em sessão limpa). Pronto para implementação Code. Milestones B-D referenciados nominalmente; autoria deferida para após gate milestone-level de Milestone A completar.

**Governance.** ADR-0008 amended (2026-05-16) — granularidade de 8-12 tasks de 1-3h agrupadas em milestones; gate task-level (function tests + revisão Chat independente) e gate milestone-level (manual exercise contra RFs). Tasks neste documento ancoram função; milestones ancoram capability declarada em `docs/REQUIREMENTS.md`.

**Source-of-truth.** `docs/REQUIREMENTS.md` (RFs/RNFs sob §2 do ADR-0008); specs canonical+compact em `docs/specs/policy-reader/`; `docs/architecture-overview.md`; `policy/SCHEMA.md`; `policy/policy.yaml`; `policy/clauses/POL-000.yaml`. Em divergência entre canonical.md e SCHEMA.md/YAML real, este documento adota o lado dos artefatos reais e anota o débito (ver §Companion edits cross-doc no fim).

**Convenção de IDs.** T01-T0NN sequencial cross-milestone (não reinicia por milestone). Cada task carrega cinco subseções: Função entregue, Dependências, Files previstos (sugestão — Code organiza o resto), Acceptance scenarios task-level (function-specific, não RF-shaped), Gate task-level.

---

## Milestone A — policy-reader standalone validado

**Capacidade entregue.** Servidor MCP `policy-reader` operacional como artefato standalone: carrega Política versionada no startup, expõe três resources (`policy://catalog`, `policy://schema-version`, `policy://vocabularies`) e três tools (`get_clause`, `find_clauses_by_law_article`, `check_applicability`) conforme `docs/specs/policy-reader/canonical.md`. Validável end-to-end via MCP Inspector cross-tool, sem dependência de outros componentes do sistema.

**RFs/RNFs cobertas no gate milestone-level.** RF-004-parcial (avaliação de conformidade sobre `collection`; entrega end-to-end requer Matcher subagent em Milestone C, mas T03 entrega o motor de veredito e o filtro de escopo MVP), RF-005 (veredito `indeterminate` como honestidade epistêmica), RF-007-parcial (composição intra-jurisdição via `accepted_law_identifiers` no nível do componente; observabilidade end-to-end requer pipeline multi-agente), RF-008-parcial (substituição de framework no nível do componente; substituição end-to-end requer Milestone C), RF-009 (provenance temporal e jurisdicional em vereditos).

**RNF-001 não bound a Milestone A.** Reprodutibilidade é propriedade sistêmica observável em CI cross-system (Milestone D), não capability de um servidor isolado. Loader determinístico é precondição implícita atendida pelos AS de T01, mas não constitui critério de gate milestone-level próprio.

**Gate milestone-level.** A redigir em sessão Chat dedicada após Tasks T01-T04 completarem gate task-level. Mecanismo conforme ADR-0008 §3: manual exercise via MCP Inspector exercitando cada RF acima, com cenários Dado/Quando/Então redigidos com Tasks já implementadas como referência operacional. Placeholder neste documento; detalhamento em sessão futura.

### Pré-implementação Milestone A — provisão a fechar fora deste documento

Uma provisão precede o início de T03 especificamente. Não bloqueia T01, T02a, T02b ou T04 — Code pode começar Milestone A pelo topo sem que esteja fechada.

**POL-001 — pacote teste de quatro cláusulas para check_applicability.** A Política atualmente contém apenas POL-000 (vocabulário estruturador de classes de dados, sem cláusulas substantivas avaliáveis). T03 precisa de cláusulas substantivas mínimas para exercitar os quatro vereditos de `check_applicability` com fixtures reais ou cláusulas mergeadas. Proposta de pacote abaixo; redação canônica é trabalho jurídico-textual de sessão Chat dedicada, ancorada em ADR-0007 já ratificado (escopo MVP collection-only, commit 893c0f7).

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

**Dependências.** T01 (estado da Política), T02a (módulo `tools.py` já estabelecido). Pré-implementação obrigatória: POL-001 pacote teste (quatro cláusulas) disponível em `policy/clauses/` ou como fixture em `tests/.../fixtures/` se ainda não mergeado.

**Files previstos** (sugestão):
- `src/mcp_servers/policy_reader/tools.py` (modificar — adicionar `check_applicability`)
- `src/mcp_servers/policy_reader/models.py` (modificar — Pydantic de `structured_context`, `verdict`, `verification_scope`, `evidence`, `contradicted_requirement`)
- `src/mcp_servers/policy_reader/server.py` (modificar — registrar tool)
- `tests/mcp_servers/policy_reader/test_check_applicability.py` (novo)

**Nota sobre nomenclatura do `structured_context`.** O inputSchema da tool segue `docs/specs/policy-reader/canonical.md` §4.3 — campos `data_categories`, `operation`, `legal_basis`, `destination`. `legal_basis` é declarado como string livre no inputSchema, não vocabulário fechado — a validação contra `policy/vocabularies/<framework>/lawful_basis.yaml` é responsabilidade da camada que produz o `structured_context` (Classifier), não da tool. Existe drift cross-doc entre estes nomes e os campos descritos em `docs/REQUIREMENTS.md` RF-003 (`operation_type`, `declared_legal_basis`, `declared_transformations`), que descrevem a saída do Classifier antes de adapter. Este documento adota canonical.md por ser o contrato da tool sob teste; sync RF-003 ↔ canonical §4.3 é débito anotado em Companion edits cross-doc.

**Acceptance scenarios task-level.**

- **AS-1 — Veredito compliant.** Dado POL-001 active requerendo `legal_basis` não-nulo, e `structured_context` `{operation: collection, data_categories: [<categoria casando POL-001>], legal_basis: "<string declarada como base legal>", destination: <valor>}`, quando a tool é invocada com `clause_id: POL-001`, então `verdict: compliant`, trinca de provenance presente no payload, `isError: false`.

- **AS-2 — Veredito violation_candidate.** Dado POL-001 (mesma cláusula de AS-1), e `structured_context` que omite `legal_basis` (campo nulo), quando a tool é invocada, então `verdict: violation_candidate`, payload contém `evidence` (snippet ou referência do que foi observado) e `contradicted_requirement` (qual requirement da cláusula foi contrariado), trinca de provenance presente.

- **AS-3 — Veredito indeterminate.** Dado POL-002 active requerendo controle `anonymization_required`, e `structured_context` com `operation: collection` e `data_categories` matching POL-002 (sem campo correspondente a "transformação declarada" no inputSchema da tool), quando a tool é invocada, então `verdict: indeterminate`, payload contém `verification_scope` com sub-campos `dimension`, `prescribed_treatment` e `verification_target` populados com strings não-vazias descrevendo que efetividade de anonimização upstream não é verificável por análise estática local, trinca de provenance presente.

- **AS-4 — Veredito not_applicable (cláusula não governa o context).** Dado POL-004 active governando categoria distinta de POL-001 e POL-002, e `structured_context` com `data_categories` que não casa POL-004, quando a tool é invocada com `clause_id: POL-004`, então `verdict: not_applicable`, payload contém `reason` descritiva citando o não-casamento entre context e escopo da cláusula, trinca de provenance presente.

- **AS-5 — Veredito not_applicable (escopo MVP).** Dado `structured_context` com `operation` em qualquer valor do vocabulário diferente de `collection` (e.g., `use`, `storage`, `disclosure_by_transmission`, `erasure`) e POL-001 active, quando a tool é invocada, então `verdict: not_applicable`, `reason` cita explicitamente escopo MVP v0.1.0 e ADR-0007 (formato exato a definir; conteúdo semântico: "operation outside MVP scope — only `collection` is evaluated"). O matching da cláusula não é invocado neste path — verificável por spy/mock no método de matching durante o teste.

- **AS-6 — Provenance idêntica ao header.** Dado qualquer veredito em sucesso (AS-1 a AS-5), quando o payload é inspecionado, então `policy_schema_version`, `policy_version` e `legal_framework` são exatamente os valores carregados do header de `policy.yaml` em T01, sem transformação ou normalização que altere os valores.

- **AS-7 — Cláusula deprecated.** Dado `clause_id` de cláusula deprecated (POL-003), quando a tool é invocada, então `isError: true`, `errorCode: CLAUSE_DEPRECATED`, `isRetryable: true`, `details` contém `{clause_id, successors, deprecation_reason}` conforme spec §5.4 — não apenas `successors`.

- **AS-8 — Erros de validação de input.** Dado `structured_context` com `data_categories` contendo valor fora de POL-000.yaml, ou `operation` fora do vocabulário carregado, ou `data_categories: []`, quando a tool é invocada, então `isError: true`, errorCode em `{INVALID_DATA_CATEGORY, INVALID_OPERATION, EMPTY_DATA_CATEGORIES}` conforme caso, `isRetryable: false`, message em português descrevendo o erro.

**Gate task-level.**

*Automated.* AS-1 a AS-8 em `tests/mcp_servers/policy_reader/test_check_applicability.py`; passam sob `uv run pytest`. Fixtures de POL-001..POL-004 em `tests/mcp_servers/policy_reader/fixtures/` se POL-001 ainda não estiver mergeado em `policy/clauses/` no momento da implementação.

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

## Companion edits cross-doc

PRs separados, fora do escopo de implementação Code de Milestone A. Não bloqueantes, mas anotados aqui para não perder o débito.

**Sync `docs/session-handoff.md`.** A entrada "Plano de ação Fase 2" do handoff descreve "Milestone A — MCPs standalone validados (T01-T05)" agrupando policy-reader e semgrep-runner. Este `tasks.md` divide em Milestone A (policy-reader) e Milestone B (semgrep-runner) por capability boundary. Atualizar handoff na mesma PR que promove `tasks.md` para evitar drift.

**Sync `docs/specs/policy-reader/canonical.md`.** Quatro débitos identificados pelas três passadas de auditoria de v0/v1:

- Nome do campo de referência legal em cláusulas: canonical §4.1 cita `article_source` (singular); `policy/SCHEMA.md` §5.1/§6.1 e `policy/clauses/POL-000.yaml` (artefato real) usam `statutory_reference`. Adotar `statutory_reference` no canonical.
- Nomes dos campos do `structured_context` no inputSchema de `check_applicability` (§4.3): canonical usa `operation` e `legal_basis`; `docs/REQUIREMENTS.md` RF-003 usa `operation_type` e `declared_legal_basis` (saída do Classifier). Decidir lado canônico — se manter canonical, RF-003 documenta o adapter Classifier→tool; se mover para RF-003, atualizar inputSchema da tool.
- Campo de payload em `not_applicable`: canonical §4.3 exemplo usa `evidence`; ADR-0007 Decision 3 (mergeada) introduz `reason`. Atualizar canonical para refletir ADR-0007.
- Versão de FastMCP: canonical §1 e §8.7 declaram "FastMCP 2.x conforme ADR-0001"; `pyproject.toml` linha 10 tem `fastmcp>=3.2.0,<4.0`; CLAUDE.md confirma 3.x; ADR-0004 governa. Sync FastMCP 2.x → 3.x no canonical.

---

## Milestones B, C, D — autoria deferida

Estrutura e tasks dos milestones subsequentes são autoradas em sessões Chat dedicadas após o gate milestone-level de Milestone A completar. Razão metodológica: ADR-0008 §1 calibra tarefas a 1-3h sob escopo de capability estabilizada — pré-autoria de milestones futuros corre o risco de drift contra learnings emergentes da implementação de Milestone A.

Escopo proposto a seguir é estrutura preliminar, não normativa até autoria formal. Boundaries entre tasks dentro de cada milestone ficam para a sessão de autoria correspondente:

- **Milestone B — semgrep-runner standalone validado.** RFs: 001, 002. Loader + tool `scan_diff` + recognizers dos seis identificadores brasileiros. Decomposição em duas ou mais tasks (boundaries a calibrar em autoria — server core vs recognizers BR é uma divisão plausível, mas não fechada aqui). Pré-implementação: decisão Semgrep-on-Windows (Docker, pip native, remote worker, CI-only) precede e afeta forma das tasks.

- **Milestone C — Pipeline multi-agente operacional local.** RFs: 003, 004-pleno, 006, 008-pleno. Decomposição tentativa: cinco AgentDefinitions com `mcp_servers` e `allowed-tools` por papel + `.mcp.json` do projeto; custom tool `emit_report` + Reporter; coordinator com Task tool dispatch, scratchpad para handoff entre subagentes, error propagation.

- **Milestone D — CI/CD + validação empírica.** RFs: 006-integração, RNF-001, RNF-002, proposta-tcc2 §4.f. Decomposição tentativa: GitHub Action workflow YAML + posting de findings via API como inline review comments, não-bloqueante; benchmark sintético ~200 snippets + execução de validação + Report consolidado.
