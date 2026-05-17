# policy-reader

**spec_version**: 0.1.0

## 1. Identidade e propósito

**Nome canônico.** `policy-reader`

**Função.** Servidor MCP que expõe a Política de Proteção de Dados versionada — sob o framework jurisdicional declarado em seu header (`legal_framework`) — como recurso consultável e como tool de avaliação de conformidade contextual, para uso pelo subagente Matcher no sistema de code review. O servidor é framework-agnóstico: serve qualquer Política cujo `policy_schema_version` esteja dentro de `compatible_schema_range` (handshake estrutural). O `legal_framework` declarado é exposto via handshake para validação do consumidor (ver §3.2).

**Posição na arquitetura.** Ver `docs/architecture-overview.md` §4.2 (MCP servers) e §5.5 (Matcher como consumidor).

**Consumidores autorizados.** Tools (`get_clause`, `find_clauses_by_law_article`, `check_applicability`) são acessadas exclusivamente pelo subagente Matcher. Resources (`policy://catalog`, `policy://schema-version`, `policy://vocabularies`) são consumidos pelo Matcher e, no caso específico de `policy://vocabularies`, também pelo Classifier (read-only, sem acesso às tools). Restrição materializada via configuração de `mcp_servers` no AgentDefinition de cada subagente (`architecture-overview.md` §5.7). Outros subagentes (Triager, Detector, Reporter) não têm este servidor em seu inventário.

**Stack e governança.** Implementação em FastMCP 3.x conforme ADR-0004. Decisões de design deste componente são governadas pelo ADR-0002, incluindo deferimentos registrados explicitamente.

## 2. Contrato com o artefato servido

### 2.1 Artefato e schema canônico

Este componente serve **Políticas de Proteção de Dados** em conformidade com o schema canônico do projeto. A Política é artefato declarativo independente, versionada em Git sob `policy/`, com ciclo de vida curado por papel jurídico e desacoplado da evolução deste componente.

O schema canônico é especificado em `policy/SCHEMA.md`. A versão exigida pela implementação atual deste componente é `policy_schema_version: 0.1.0`.

A Política em si carrega três eixos de identidade independentes:

- `policy_schema_version` — versão do schema (forma) que a Política instancia. Contrato estrutural com consumidores. Muda raramente.
- `policy_version` — versão do conteúdo das cláusulas. Trilha de auditoria. Muda a cada revisão de cláusula.
- `legal_framework` — identificador da jurisdição sob a qual a Política opera (e.g., `LGPD`, `GDPR`). Valor único (não lista), imutável durante a vida da instância. Governa o conjunto de vocabulários jurisdicionais carregados de `policy/vocabularies/<framework>/`.

**Multi-framework — escopo arquitetural.** Uma instância deste componente serve **uma única Política** sob **um único `legal_framework`**. Não há suporte a cross-framework simultâneo: a mesma instância não serve LGPD e GDPR ao mesmo tempo. Multi-framework é alcançado via múltiplas instâncias do servidor, uma por cliente/jurisdição, cada qual com sua Política sob `policy/`. Decisão de design registrada em ADR-0005 Decision 2.

A separação evita o anti-padrão "bumpamos schema major porque mudou um texto", que envenena a semântica do versionamento. O componente reporta os três campos via o resource `policy://schema-version` (handshake do consumidor) e inclui-os em retornos relevantes de tools, formando provenance temporal e jurisdicional auditável (ver §6 — Provenance e versionamento).

**MVP — escopo de schema.** A v0.1.0 do schema é o único schema suportado pela implementação atual deste componente. Suporte a schemas alternativos (clientes com Políticas estruturalmente distintas) é deferimento explícito registrado em ADR-0002. A distinguir de `legal_framework` alternativo, que é nativamente suportado via troca de vocabulários jurisdicionais sem alteração de schema (ver §2.2 e ADR-0005).

### 2.2 Comportamento contratual perante estados de cláusula

O schema da Política define o estado de cada cláusula via campo `status`. As operações do componente reagem a cada estado conforme tabela abaixo. Outros campos do schema (estrutura de `statutory_reference`, sub-ids em requirements, vocabulário canônico de classes) são governados por `policy/SCHEMA.md` e não geram comportamento diferenciado nas operações deste componente.

| Estado da cláusula | `get_clause` | `check_applicability` | `find_clauses_by_law_article` |
|---|---|---|---|
| `active` | Sucesso, retorna cláusula. | Sucesso, retorna veredito. | Cláusula incluída no resultado. |
| `deprecated` | Sucesso, retorna cláusula com bloco `tombstone` contendo `successors`, `effective_until`, `deprecation_reason`. | Erro business retryable `CLAUSE_DEPRECATED` com `successors` em `details`. | Cláusula **não** incluída no resultado. Cliente busca cláusulas operativas, não históricas. |

**Justificativa do dual deprecated em `get_clause` vs. `check_applicability`.** A semântica das tools é diferente, e o estado `deprecated` afeta cada uma diferente. `get_clause` é retrieval — leitura legítima de qualquer cláusula existente, inclusive para auditoria histórica. Tombstone é parte do dado. `check_applicability` é avaliação operacional — invocá-la sobre cláusula que não opera mais é falha de negócio recuperável. Mesma condição (deprecated), duas tools, dois retornos. Ver §5 — Contrato de erro para detalhe do payload.

**Justificativa da exclusão em `find_clauses_by_law_article`.** Busca reversa serve à pergunta "quais cláusulas operativas referenciam tal artigo da lei?". Incluir cláusulas deprecated obrigaria todo consumidor a filtrar defensivamente; excluí-las por padrão alinha o comportamento com o caso de uso modal. Recuperação de cláusulas deprecated é caso explícito via `get_clause` com `clause_id` conhecido.

**Comportamento contratual perante framework jurisdicional.** Conforme declarado em §2.1, o componente serve uma Política sob um framework por instância, e o valor de `legal_framework` é imutável durante a vida da instância. O componente é **agnóstico ao valor** de `legal_framework`: nenhum código contém ramificações por `LGPD` vs `GDPR` vs outros. Os vocabulários jurisdicionais (operações, bases legais, controles, motivos de fora de escopo) são lidos no startup do diretório `policy/vocabularies/<framework>/`, onde `<framework>` corresponde ao valor declarado no header da Política. Mudança de framework requer, em ordem: (a) Política nova ou clonada sob nova jurisdição, com header declarando `legal_framework: <new>` e `accepted_law_identifiers` apropriado; (b) população do diretório `policy/vocabularies/<new_framework>/` com os quatro YAMLs canônicos exigidos (`operation`, `lawful_basis`, `control`, `out_of_scope`); (c) restart do servidor. Nenhuma alteração de código é necessária. Ver §2.1 e ADR-0005 Decision 2.

## 3. Resources expostos

O componente expõe três resources, todos sob o scheme `policy://`. O scheme custom para artefato de domínio é convenção do projeto governada pela ADR-0002, Decisão 7.

### 3.1 `policy://catalog`

**URI.** `policy://catalog` (estática, sem parâmetros).

**Conteúdo.** Índice de cláusulas da Política. Cada item carrega:

- `clause_id` — identificador opaco com prefixo `POL-`.
- `title` — rótulo humano-legível da cláusula.
- `status` — `active` ou `deprecated`.
- `article_sources_summary` — lista compacta de referências aos artigos da lei que a cláusula invoca, em forma sumarizada (forma exata definida em `policy/SCHEMA.md`). Estrutura completa de `statutory_reference` vive na cláusula em si, recuperável via `get_clause`.
- `successors` — lista de `clause_id` sucessores, **presente apenas quando** `status: deprecated`. Ausente para cláusulas ativas.

A ordem dos itens segue ordem natural do `clause_id` (POL-001, POL-002, ...). Não há paginação na v0.1.0 — escala assumida da Política do MVP é < 200 cláusulas.

**Semântica de leitura.** Idempotente. Reflete o estado atual da Política versionada. Reload da Política é disparado exclusivamente por restart do server (decisão MVP — ver §6.5). Hot reload é deferimento registrado em ADR-0002. Dentro de uma sessão de server, o conteúdo do catálogo é imutável.

**Casos de erro.** Falha de I/O ao ler arquivo da Política sob `policy/` (disco, permissão, arquivo ausente) é erro de protocolo (Nível 1 MCP), não erro de domínio. O catálogo nunca está logicamente "vazio" — Política sem cláusulas é configuração inválida do artefato, detectada no startup do server, não em request runtime.

### 3.2 `policy://schema-version`

**URI.** `policy://schema-version` (estática, sem parâmetros).

**Conteúdo.** Objeto com quatro campos:

- `policy_schema_version` — versão do schema instanciado pela Política atual. No MVP, sempre `0.1.0`.
- `policy_version` — versão do conteúdo das cláusulas da Política atual.
- `legal_framework` — identificador da jurisdição declarada no header da Política (e.g., `LGPD`, `GDPR`). Valor único, imutável durante a sessão do server. Governa o conjunto de vocabulários jurisdicionais carregados (ver §3.3).
- `compatible_schema_range` — intervalo de versões de schema que esta implementação do componente sabe servir. No MVP, `0.1.x`.

**Semântica de leitura.** Idempotente. Serve como **handshake duplo** do consumidor antes de invocar tools:

**Validação estrutural.** Consumidor verifica que `policy_schema_version` está dentro de `compatible_schema_range`. Falha aborta — consumidor não sabe servir a forma desta Política.

**Validação jurisdicional.** Consumidor verifica que `legal_framework` está em sua própria lista de frameworks aceitos (configurada no AgentDefinition do consumidor). Falha aborta — consumidor não sabe operar sob esta jurisdição.

Falha de qualquer uma das duas validações é fail-fast — consumidor não deve tentar tools.

**Onde mora a validação.** Este resource não rejeita consumidores; apenas declara o que a Política instancia. A decisão de prosseguir ou abortar é local ao consumidor: cada subagente (Matcher, Classifier) carrega no seu AgentDefinition a lista de frameworks que aceita operar e o range de schemas que sabe consumir, e compara contra os campos deste resource. O componente não conhece — nem precisa conhecer — a configuração de cada consumidor.

**Casos de erro.** Equivalentes a `policy://catalog`: I/O do arquivo da Política. Sem casos de erro de domínio.

### 3.3 `policy://vocabularies`

**URI.** `policy://vocabularies` (estática, sem parâmetros).

**Conteúdo.** Objeto agregando os quatro vocabulários jurisdicionais carregados de `policy/vocabularies/<framework>/*.yaml`, onde `<framework>` corresponde ao valor de `legal_framework` declarado no header da Política:

- `operation` — vocabulário canônico de operações de tratamento (e.g., coleta, armazenamento, compartilhamento).
- `lawful_basis` — vocabulário canônico de bases legais admitidas, com campo `category` distinguindo `personal_data` de `sensitive_data`.
- `control` — vocabulário canônico de controles que a Política pode exigir (e.g., `consent_required`, `anonymization_required`).
- `out_of_scope` — vocabulário canônico de motivos pelos quais uma categoria candidata foi excluída da classificação em cláusulas `definitional` (e.g., absorvida em classe existente, atributo de regime de tratamento, fora do escopo geográfico do MVP).

Cada vocabulário é objeto com campos `schema_version`, `framework`, e `values[]`, conforme estrutura definida em `policy/SCHEMA.md` §10.

**Semântica de leitura.** Idempotente. Conteúdo determinado em startup pelo valor de `legal_framework` no header da Política; imutável durante a sessão do server. Reload exige restart do server, paralelo a `policy://catalog` e `policy://schema-version`.

**Consumidores autorizados.** Matcher (junto com as tools do componente) e Classifier (read-only, sem acesso às tools). Materializa o princípio Resource vs Tool registrado em ADR-0005 Decision 4: o Classifier consome o vocabulário como contexto léxico para categorização lexical de operações detectadas, sem ganhar capacidade de invocar tools de avaliação contextual (exclusivas do Matcher).

**Casos de erro.** Falha de I/O ao ler qualquer dos quatro arquivos YAML sob `policy/vocabularies/<framework>/` é erro de protocolo (Nível 1 MCP) detectado no startup — server falha o boot e relata erro de configuração. Sem casos de erro de domínio em runtime: consumo do resource numa sessão estabelecida é idempotente.

## 4. Tools expostas

O componente expõe três tools. Descrições em inglês conforme convenção do projeto registrada em ADR-0001 (modelo processa inglês com mais densidade).

**Naming convention.** As três tools deste server aparecem para o agente (Claude Code ou Agent SDK) com os handles:

- `mcp__policy-reader__get_clause`
- `mcp__policy-reader__find_clauses_by_law_article`
- `mcp__policy-reader__check_applicability`

O namespace `mcp__<server>__<tool>` é gerado pelo runtime ao expor tools de um MCP server configurado em `.mcp.json`. O nome simples (e.g., `get_clause`) é a forma usada nas subseções a seguir; a forma prefixada é a forma usada em `allowed-tools` de skill frontmatter, em `mcp_servers`/`allowed-tools` do AgentDefinition do Matcher, e em matchers de hooks `PreToolUse`/`PostToolUse` que filtram tools deste server.

### 4.1 `get_clause`

**Descrição (tool description).**

```
Retrieve a single Policy clause by its stable `clause_id`.

Use this when the caller already knows the exact identifier (typically recovered from `policy://catalog`, from a previous `find_clauses_by_law_article` call, or from a `successors` field returned by a `CLAUSE_DEPRECATED` error). Do not use this to search clauses by law article — for that, use `find_clauses_by_law_article`. Do not use this to evaluate whether a clause applies to a code-handling context — for that, use `check_applicability`.

Returns the clause object with `clause_id`, `title`, `statutory_reference` (hierarchical structure of law references), `applicability_scope` (data classes covered, drawn from the canonical vocabulary), `requirements` (numbered sub-items the clause demands), `exceptions` (numbered sub-items that suspend requirements), and `status`.

If the clause is `deprecated`, this tool returns it successfully with a `tombstone` block containing `successors` (list of replacement `clause_id`s), `effective_until` (ISO date), and `deprecation_reason`. Deprecated clauses are not errors here — auditing historical decisions and following successor chains are legitimate use cases.

If the `clause_id` does not match any clause, returns business error `CLAUSE_NOT_FOUND` (non-retryable).
```

**`inputSchema`.**

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `clause_id` | string | sim | Identificador opaco com prefixo `POL-` seguido de inteiro de três dígitos zero-padded (ex: `POL-027`). Formato validado por regex `^POL-\d{3}$` no schema. |

**Output em sucesso.** Objeto com a estrutura completa da cláusula conforme schema canônico (`policy/SCHEMA.md`):

```yaml
clause_id: POL-027
title: <rótulo humano-legível>
status: active            # ou: deprecated
statutory_reference:      # estrutura hierárquica — ver SCHEMA.md
  - lei: LGPD
    artigo: 7
    inciso: 1
applicability_scope:      # vocabulário canônico — ver SCHEMA.md (POL-000)
  - dados_de_identificacao
  - dados_de_contato
requirements:
  - id: R1
    text: <exigência humana-legível>
exceptions:
  - id: E1
    text: <exceção humana-legível>
# Quando status: deprecated, adicionalmente:
tombstone:
  successors: [POL-031, POL-032]
  effective_until: 2026-12-31
  deprecation_reason: <texto curto>
```

Estrutura interna dos campos governada por `policy/SCHEMA.md` (princípio aplicado: schema fora, comportamento dentro).

**Condições de erro específicas.**

| `errorCode` | Classe | `isRetryable` | Quando ocorre | `details` |
|---|---|---|---|---|
| `INVALID_CLAUSE_ID_FORMAT` | validation | false | `clause_id` não casa com regex `^POL-\d{3}$`. | `{provided, expected_format}` |
| `CLAUSE_NOT_FOUND` | business | false | `clause_id` tem formato válido mas não existe na Política atual. | `{clause_id}` |

Tabela completa de `errorCode` do componente em §5 (Contrato de erro).

**Exemplos.**

*Caso normal — recuperação de cláusula ativa.*

```
Input: { "clause_id": "POL-027" }
Output: { "isError": false, "content": [{ ...estrutura da cláusula POL-027... }] }
```

*Caso de cláusula deprecated.*

```
Input: { "clause_id": "POL-014" }
Output: { "isError": false, "content": [{
  "clause_id": "POL-014",
  "status": "deprecated",
  "tombstone": {
    "successors": ["POL-031", "POL-032"],
    "effective_until": "2026-06-30",
    "deprecation_reason": "Cláusula original dividida em duas após reforma legislativa."
  },
  ...resto da cláusula...
}]}
```

*Caso de erro — cláusula inexistente.*

```
Input: { "clause_id": "POL-999" }
Output: { "isError": true, "content": [{
  "errorCode": "CLAUSE_NOT_FOUND",
  "message": "Cláusula POL-999 não encontrada na Política versão atual.",
  "isRetryable": false,
  "details": { "clause_id": "POL-999" }
}]}
```

### 4.2 `find_clauses_by_law_article`

**Descrição (tool description).**

```
Find Policy clauses that reference a given law article (or sub-section of it).

Use this when the caller needs to enumerate clauses applicable to a specific piece of law, without knowing clause identifiers in advance. Typical flow: the caller has structured context describing handling of personal data and needs to discover which clauses operate over the relevant law article. Do not use this when the caller already knows the `clause_id` — use `get_clause` instead. Do not use this to evaluate whether a clause applies to a context — use `check_applicability`.

Specification is hierarchical and progressive. `lei` and `artigo` are required; `paragrafo`, `inciso`, `alinea` are optional and narrow the search. A clause matches when ANY element of its `statutory_reference` list starts hierarchically with the given specification (matching `lei` first, then `artigo`, then optional fields in order). Clauses with multiple legal anchors thus match if any anchor is in scope. Example: a query for `{lei: LGPD, artigo: 7}` returns all active clauses whose statutory_reference begins with LGPD Art. 7º, regardless of inciso. A query for `{lei: LGPD, artigo: 7, inciso: 1}` returns only clauses tied specifically to inciso 1.

Returns a list of clause objects (same structure as `get_clause` returns, without the `tombstone` block — deprecated clauses are excluded from results since this tool is for discovering operative clauses).

Empty result is not an error: if no clauses in the current Policy match the specification, returns an empty list with `isError: false`.
```

**`inputSchema`.**

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `lei` | string | sim | Identificador da lei. Vocabulário fechado declarado pelo header `accepted_law_identifiers` da Política. Valores aceitos definidos em `policy/SCHEMA.md`. |
| `artigo` | integer | sim | Número do artigo. Inteiro positivo. |
| `paragrafo` | integer | não | Número do parágrafo, quando o caller deseja restringir a parágrafo específico. |
| `inciso` | integer | não | Número do inciso (forma canônica é inteiro, não numeral romano — renderização para romano é responsabilidade da camada de apresentação). |
| `alinea` | string | não | Letra da alínea (ex: `"a"`, `"b"`). |

**Output em sucesso.** Lista de objetos de cláusula. Cada item da lista carrega a estrutura completa de cláusula conforme §4.1 em sucesso (sem o bloco `tombstone`, já que cláusulas deprecated são excluídas). Lista pode ser vazia.

A ordem dos itens segue ordem natural do `clause_id`. Não há paginação na v0.1.0.

**Condições de erro específicas.**

| `errorCode` | Classe | `isRetryable` | Quando ocorre | `details` |
|---|---|---|---|---|
| `INVALID_LAW_IDENTIFIER` | validation | false | `lei` não casa com o vocabulário declarado pelo header `accepted_law_identifiers` da Política. | `{provided, accepted_values}` |

Sem outros casos de erro de domínio: lei desconhecida vira lista vazia, não erro; especificação de artigo inexistente vira lista vazia.

**Exemplos.**

*Caso normal — busca ampla por artigo.*

```
Input: { "lei": "LGPD", "artigo": 7 }
Output: { "isError": false, "content": [
  { "clause_id": "POL-027", "statutory_reference": [{lei: "LGPD", artigo: 7, inciso: 1}], ... },
  { "clause_id": "POL-028", "statutory_reference": [{lei: "LGPD", artigo: 7, inciso: 2}], ... },
  { "clause_id": "POL-029", "statutory_reference": [{lei: "LGPD", artigo: 7, inciso: 5}], ... }
]}
```

*Caso de busca estreita.*

```
Input: { "lei": "LGPD", "artigo": 7, "inciso": 1 }
Output: { "isError": false, "content": [
  { "clause_id": "POL-027", "statutory_reference": [{lei: "LGPD", artigo: 7, inciso: 1}], ... }
]}
```

*Caso de empty result.*

```
Input: { "lei": "LGPD", "artigo": 50 }
Output: { "isError": false, "content": [] }
```

*Caso de erro — lei fora do vocabulário.*

```
Input: { "lei": "CodigoPenal", "artigo": 1 }
Output: { "isError": true, "content": [{
  "errorCode": "INVALID_LAW_IDENTIFIER",
  "message": "Identificador de lei 'CodigoPenal' não está no vocabulário aceito.",
  "isRetryable": false,
  "details": { "provided": "CodigoPenal", "accepted_values": ["LGPD"] }
}]}
```

**Independência de framework.** Esta tool é agnóstica ao valor de `legal_framework`: opera sobre o índice de cláusulas da Política carregada, qualquer que seja a jurisdição. O vocabulário aceito de `lei` no input é determinado pelo campo `accepted_law_identifiers` do header da Política — não codificado na tool. Trocar de framework (e.g., de `LGPD` para `GDPR`) não altera o comportamento da tool, apenas o conjunto de identificadores de lei aceitos e o conjunto de cláusulas indexadas, ambos derivados da Política carregada.

### 4.3 `check_applicability`

**Descrição (tool description).**

```
Evaluate whether a Policy clause applies to a specific code-handling context, and produce a structured verdict.

This is the core evaluation tool. Use this when the caller has identified a candidate clause (typically via `find_clauses_by_law_article` or by reading `policy://catalog`) and needs to determine whether the clause governs a specific context and, if so, with what verdict. Do not use this to retrieve clause content — use `get_clause`. Do not attempt to reproduce this evaluation in agent reasoning by reading the clause manually — the evaluation has structured rules over `structured_context` that the agent should not improvise.

The caller provides `structured_context` describing the handling: the data classes involved (drawn from the canonical vocabulary), the operation performed, the legal basis declared (when present), and the destination of the data (when relevant). Returns one of four verdicts:

- `compliant` — handling is consistent with the clause requirements.
- `violation_candidate` — handling appears to contradict the clause; carries evidence pointing to the contradicting elements.
- `indeterminate` — static analysis cannot conclude; carries `verification_scope` with the dimension to verify and the treatment prescribed by the clause.
- `not_applicable` — the clause does not govern this handling in this context.

If the clause is `deprecated`, returns business error `CLAUSE_DEPRECATED` (retryable) with `successors` in `details` — the caller should retry with a successor `clause_id`. See §5 (Contrato de erro) for full error contract.
```

**`inputSchema`.**

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `clause_id` | string | sim | Identificador da cláusula a avaliar. Formato `POL-NNN`. |
| `structured_context` | object | sim | Contexto estruturado do handling. Campos descritos abaixo. |
| `structured_context.data_categories` | array de string | sim | Classes de dados envolvidas. Cada elemento deve pertencer ao vocabulário canônico declarado em POL-000 (`policy/SCHEMA.md`). Lista não-vazia. |
| `structured_context.operation` | string (enum) | sim | Tipo de operação sobre o dado. Vocabulário canônico definido em `policy/vocabularies/<framework>/operation.yaml`, exposto ao consumidor via resource `policy://vocabularies` (ver §3.3). |
| `structured_context.legal_basis` | string | não | Base legal declarada pelo código (quando presente). Valor textual livre — não vocabulário fechado. Ausência sinaliza que o código não declara base. |
| `structured_context.destination` | string | não | Destino do dado quando relevante (ex: `external_service`, `internal_database`, `client_browser`). Ausência sinaliza não-aplicabilidade. |

**Output em sucesso.** Objeto com veredito e estrutura associada. A estrutura varia conforme o veredito:

```yaml
# Veredito compliant
{
  verdict: compliant,
  policy_clause_ref: POL-027,
  evidence: <texto curto explicando o casamento entre context e clause>
}

# Veredito violation_candidate
{
  verdict: violation_candidate,
  policy_clause_ref: POL-027,
  evidence: <texto identificando o ponto de contradição>,
  contradicted_requirement: R1   # sub-id do requirement contradito
}

# Veredito indeterminate
{
  verdict: indeterminate,
  policy_clause_ref: POL-027,
  verification_scope: {
    dimension: upstream_state,                # vocabulário em SCHEMA.md
    prescribed_treatment: consent_required,   # control.yaml em policy://vocabularies; MVP cobre consent_required e anonymization_required
    verification_target: <texto em português indicando onde verificar>
  }
}

# Veredito not_applicable
{
  verdict: not_applicable,
  policy_clause_ref: POL-027,
  evidence: <texto explicando por que a cláusula não governa este contexto>
}
```

**Nota sobre `evidence` e `verification_target`.** Os campos de prosa (`evidence` em `compliant`, `violation_candidate`, `not_applicable`; `verification_target` em `indeterminate`) são gerados pelo componente como parte do veredito. Mecanismo de geração é decisão de implementação livre para evoluir (template, geração por modelo, híbrido) sem mudar a interface — ver §7.1. Caller não fornece esses campos.

**Condições de erro específicas.**

| `errorCode` | Classe | `isRetryable` | Quando ocorre | `details` |
|---|---|---|---|---|
| `INVALID_CLAUSE_ID_FORMAT` | validation | false | `clause_id` não casa com regex `^POL-\d{3}$`. | `{provided, expected_format}` |
| `CLAUSE_NOT_FOUND` | business | false | `clause_id` não existe na Política atual. | `{clause_id}` |
| `CLAUSE_DEPRECATED` | business | true | `clause_id` aponta para cláusula deprecated. Caller deve retry com successor. | `{clause_id, successors, deprecation_reason}` |
| `INVALID_DATA_CATEGORY` | validation | false | `data_categories` contém elemento fora do vocabulário POL-000. | `{invalid_value, accepted_values}` |
| `INVALID_OPERATION` | validation | false | `operation` fora do enum declarado. | `{provided, accepted_values}` |
| `EMPTY_DATA_CATEGORIES` | validation | false | `data_categories` é lista vazia. | `{}` |

**Notas sobre o conteúdo de `accepted_values`.** Para `INVALID_DATA_CATEGORY` e `INVALID_OPERATION`, o campo `accepted_values` é populado dinamicamente a partir do vocabulário carregado da Política: `INVALID_OPERATION` enxerga os valores de `policy/vocabularies/<framework>/operation.yaml` (resource `policy://vocabularies`); `INVALID_DATA_CATEGORY` enxerga os valores do vocabulário canônico de classes declarado em POL-000 da Política (governado por `policy/SCHEMA.md`). O conteúdo da lista varia conforme a Política carregada; a **forma do payload** (`{invalid_value, accepted_values}` / `{provided, accepted_values}`) é estável.

**Framework-awareness desta tool.** `check_applicability` é framework-aware via consumo dinâmico de `policy://vocabularies` no startup: a tool não contém ramificações por jurisdição (e.g., `if framework == "LGPD"`), apenas consome o vocabulário carregado. Trocar de framework muda o conjunto de operações válidas (input) e o vocabulário de controles citados em `prescribed_treatment` (output), sem mudar o comportamento codificado da tool. O retorno em sucesso carrega o trinque de provenance (`policy_schema_version`, `policy_version`, `legal_framework`), conforme §6.4. Exemplos abaixo já refletem o trinque.

**Exemplos.**

*Caso compliant — código declara base legal coerente com a cláusula.*

```
Input: {
  "clause_id": "POL-027",
  "structured_context": {
    "data_categories": ["dados_de_identificacao"],
    "operation": "collection",
    "legal_basis": "consentimento explícito"
  }
}
Output: {
  "isError": false,
  "structuredContent": {
    "verdict": "compliant",
    "policy_clause_ref": "POL-027",
    "evidence": "Cláusula POL-027 (LGPD Art. 7º, I) exige consentimento; código declara base 'consentimento explícito'.",
    "policy_schema_version": "0.1.0",
    "policy_version": "0.1.0",
    "legal_framework": "LGPD"
  },
  "content": [
    {
      "type": "text",
      "text": "Cláusula POL-027 (LGPD Art. 7º, I) exige consentimento; código declara base 'consentimento explícito'."
    }
  ]
}
```

*Caso violation_candidate — código viola requirement direto.*

```
Input: {
  "clause_id": "POL-031",
  "structured_context": {
    "data_categories": ["dados_de_saude"],
    "operation": "store",
    "legal_basis": "interesse legítimo"
  }
}
Output: {
  "isError": false,
  "structuredContent": {
    "verdict": "violation_candidate",
    "policy_clause_ref": "POL-031",
    "evidence": "Cláusula POL-031 (LGPD Art. 11) exige consentimento ou hipóteses específicas para dados sensíveis; código declara base 'interesse legítimo', que não está entre as hipóteses do Art. 11.",
    "contradicted_requirement": "R1",
    "policy_schema_version": "0.1.0",
    "policy_version": "0.1.0",
    "legal_framework": "LGPD"
  },
  "content": [
    {
      "type": "text",
      "text": "Cláusula POL-031 (LGPD Art. 11) exige consentimento ou hipóteses específicas para dados sensíveis; código declara base 'interesse legítimo', que não está entre as hipóteses do Art. 11."
    }
  ]
}
```

*Caso indeterminate — depende de upstream.*

```
Input: {
  "clause_id": "POL-027",
  "structured_context": {
    "data_categories": ["dados_de_identificacao"],
    "operation": "transmit",
    "destination": "external_service"
  }
}
Output: {
  "isError": false,
  "structuredContent": {
    "verdict": "indeterminate",
    "policy_clause_ref": "POL-027",
    "verification_scope": {
      "dimension": "upstream_state",
      "prescribed_treatment": "consent_required",
      "verification_target": "Confirmar se consentimento do titular foi obtido antes desta transmissão. Cláusula POL-027 (LGPD Art. 7º, I) exige consentimento explícito para coleta e transmissão de dados de identificação."
    },
    "policy_schema_version": "0.1.0",
    "policy_version": "0.1.0",
    "legal_framework": "LGPD"
  },
  "content": [
    {
      "type": "text",
      "text": "Confirmar se consentimento do titular foi obtido antes desta transmissão. Cláusula POL-027 (LGPD Art. 7º, I) exige consentimento explícito para coleta e transmissão de dados de identificação."
    }
  ]
}
```

*Caso de erro — cláusula deprecated.*

```
Input: { "clause_id": "POL-014", "structured_context": {...} }
Output: {
  "isError": true,
  "structuredContent": {
    "errorCode": "CLAUSE_DEPRECATED",
    "message": "Cláusula POL-014 está deprecated. Sucessores: POL-031, POL-032.",
    "isRetryable": true,
    "details": {
      "clause_id": "POL-014",
      "successors": ["POL-031", "POL-032"],
      "deprecation_reason": "Cláusula original dividida após reforma legislativa."
    }
  },
  "content": [
    {
      "type": "text",
      "text": "Cláusula POL-014 está deprecated. Sucessores: POL-031, POL-032."
    }
  ]
}
```

## 5. Contrato de erro

### 5.1 Estrutura canônica do payload de erro

Quando uma tool retorna falha, o resultado MCP tem `isError: true`. O objeto canônico de erro é serializado em `structuredContent` (canal nativo MCP para JSON estruturado), com a estrutura abaixo:

```yaml
{
  errorCode: <string>,    # constante estável em inglês, formato MAIÚSCULAS_SNAKE
  message: <string>,      # mensagem humana em português, para logs e exibição
  isRetryable: <boolean>, # se nova chamada com input ajustado pode ter sucesso
  details: <object>       # campos específicos por errorCode; pode ser objeto vazio
}
```

O campo `content` do `CallToolResult` carrega um único bloco `TextContent` cuja chave `text` reproduz `message`. Placement híbrido `structuredContent` + `content` é convenção do projeto registrada em ADR-0002 §1.

A separação inglês/português é deliberada. `errorCode` é constante de máquina — orchestrator faz comparação programática (`if errorCode == "CLAUSE_DEPRECATED"`), idioma estável evita bugs por capitalização ou tradução. `message` é destinada a humanos: logs do sistema, mensagens posteriores ao dev no PR review, depuração. Mistura inversa quebra ambos os usos.

`details` é estruturado por `errorCode` (cada código tem sua forma) e carrega informação que o caller precisa para a próxima ação. Sem `details` rico, erro retryable vira erro não-retryable na prática (caller não tem como ajustar a chamada).

O contrato dos quatro campos é convenção deste projeto sobreposta ao protocolo MCP — o único campo de erro nativo do `CallToolResult` é o booleano `isError`, que sinaliza falha mas não distingue classes (validation/business/system, ver §5.2) nem decisão de retry. A convenção materializa essas distinções programaticamente.

### 5.2 Classes de erro

O componente emite erros em três classes, com semânticas distintas:

**Validation.** Input chegou sintaticamente válido (passou no `inputSchema` MCP) mas falhou em regra semântica do server (vocabulário fechado violado, formato derivado, presença de campo obrigatório contextual). **Sempre `isRetryable: false`** — caller reformulando com a mesma lógica vai falhar de novo. Próxima ação é repensar a chamada.

**Business.** Input válido sintática e semanticamente, mas regra de domínio rejeita. **Pode ser `isRetryable: true` ou `false`**, decidido por caso. Retryable significa "ajuste com base em `details` e tente de novo" (ex: `CLAUSE_DEPRECATED` com sucessor em `details`). Não-retryable significa "registre e siga, não há ajuste possível com a mesma intenção" (ex: `CLAUSE_NOT_FOUND`).

**System.** Falha transiente de infraestrutura. Disco, I/O, lock, recurso indisponível. **Quase sempre `isRetryable: true`** com backoff. Não há raciocínio sobre o conteúdo — caller decide quando, não como, repetir.

### 5.3 Casos que parecem erro mas não são

Três condições produzem retorno bem-sucedido (`isError: false`) mesmo que "intuitivamente" pareçam falha:

**Empty result.** `find_clauses_by_law_article` invocada com especificação para a qual a Política não tem cláusulas operativas correspondentes retorna lista vazia com `isError: false`. Vazio é informação acionável: caller sabe que pode prosseguir sem cláusulas para esse artigo.

**Veredito `indeterminate` em `check_applicability`.** É o output legítimo de "análise estática não consegue decidir esta dimensão". Sucesso do sistema sendo honesto, não falha. Modelar como erro destruiria a fronteira epistêmica do componente.

**Cláusula `deprecated` em `get_clause`.** Retorno é sucesso com bloco `tombstone` no payload. Auditoria histórica e seguimento de cadeia de sucessores são casos de uso legítimos. (Em `check_applicability`, a mesma condição vira erro `CLAUSE_DEPRECATED` retryable, porque a semântica da tool é diferente — ver §2.2.)

### 5.4 Tabela consolidada de `errorCode`

| `errorCode` | Classe | Retryable | Tools que emitem | Condição | Forma de `details` |
|---|---|---|---|---|---|
| `INVALID_CLAUSE_ID_FORMAT` | validation | false | `get_clause`, `check_applicability` | `clause_id` não casa com regex `^POL-\d{3}$`. | `{provided, expected_format}` |
| `CLAUSE_NOT_FOUND` | business | false | `get_clause`, `check_applicability` | `clause_id` tem formato válido mas não existe na Política atual. | `{clause_id}` |
| `CLAUSE_DEPRECATED` | business | true | `check_applicability` | `clause_id` aponta para cláusula com `status: deprecated`. | `{clause_id, successors, deprecation_reason}` |
| `INVALID_LAW_IDENTIFIER` | validation | false | `find_clauses_by_law_article` | `lei` não casa com vocabulário declarado pelo header `accepted_law_identifiers` da Política. | `{provided, accepted_values}` |
| `INVALID_DATA_CATEGORY` | validation | false | `check_applicability` | Elemento de `data_categories` fora do vocabulário POL-000. | `{invalid_value, accepted_values}` |
| `INVALID_OPERATION` | validation | false | `check_applicability` | `operation` fora do enum declarado em `policy/SCHEMA.md`. | `{provided, accepted_values}` |
| `EMPTY_DATA_CATEGORIES` | validation | false | `check_applicability` | `data_categories` é lista vazia. | `{}` |

A tabela acima é exaustiva para a v0.1.0 da spec. **A classe system é vazia neste componente — ausência de system errors é declaração positiva, não omissão.** A Política é carregada apenas no startup do server (§6.5), de modo que falhas de I/O sobre o arquivo da Política durante runtime não ocorrem; corrupção ou indisponibilidade durante carregamento inicial aborta o startup do server, fora do contrato de erro de tools.

Erros de protocolo MCP (Nível 1 — schema do `inputSchema` violado, tool inexistente, conexão) não aparecem nesta tabela. Eles são tratados pelo protocolo, não pelo componente.

### 5.5 Princípio de evolução do contrato

Adicionar `errorCode` ao contrato é mudança **minor** da spec (`spec_version` 0.1.0 → 0.2.0). Remover ou mudar semântica de `errorCode` existente é mudança **major** (incompatível com callers existentes). Versionamento da spec governado por ADR-0002 §6.

## 6. Provenance e versionamento

### 6.1 Versão da spec

Versão atual: `spec_version: 0.1.0`. Convenção semver governada por ADR-0002 §6. Em fase de redação ativa (até primeira implementação rodar end-to-end), a spec permanece em `0.1.x`; estabilização para `1.0.0` requer ADR dedicado.

### 6.2 Versão do componente

Implementação do `policy-reader` é versionada independentemente da spec. Componente declara sua versão via metadados padrão MCP no startup. Versão do componente NÃO aparece em retornos de tools — não é provenance do veredito. (Provenance do veredito é versão da Política, não do leitor.)

### 6.3 Versão da Política — handshake

O resource `policy://schema-version` (estrutura e semântica em §3.2) é o ponto de handshake versional do consumidor com o componente. Sua função no contrato de provenance é registrar contra qual versão de schema o consumidor opera, permitindo fail-fast quando incompatível.

### 6.4 Provenance temporal e jurisdicional em retornos de `check_applicability`

Cada retorno bem-sucedido de `check_applicability` carrega, como campos adicionais do objeto de veredito, o **trinque de provenance** (`policy_schema_version`, `policy_version`, `legal_framework`):

- `policy_schema_version` — versão do schema (forma) que a Política instancia. Estável entre múltiplos vereditos da mesma sessão.
- `policy_version` — versão do conteúdo das cláusulas. Estável entre múltiplos vereditos da mesma sessão.
- `legal_framework` — identificador da jurisdição sob a qual a Política opera (e.g., `LGPD`, `GDPR`). Valor único, imutável durante a sessão do server (ADR-0005 Decision 2).

Estes três campos são **provenance temporal e jurisdicional**: identificam contra qual versão da Política e sob qual jurisdição o veredito foi emitido. Permitem ao Reporter agregar Reports auditáveis (ver `architecture-overview.md` §5.6 — Reporter) e a auditores post-hoc reproduzir a decisão. O `legal_framework` no veredito é **não-opcional**: em auditoria multi-jurisdição assíncrona, o auditor não tem acesso ao contexto de execução (qual instância do server estava ativa, qual Política foi carregada), então o framework precisa ser **carregado** no veredito, não inferido — o registro é a única fonte estruturalmente confiável. Materializa ADR-0005 Decision 5 (provenance trinque é não-opcional em vereditos).

Justificativa: `get_clause` e `find_clauses_by_law_article` são retrieval — consumidor sabe que está lendo o estado atual e o agregador pode incluir os três campos a partir do handshake (§3.2). `check_applicability` emite veredito que será citado em Report — o trinque precisa estar no veredito diretamente, não inferido do contexto.

### 6.5 Política sem alteração de versão durante execução

O componente carrega a Política no startup. Mudanças no arquivo da Política durante a execução do server não são refletidas (mecanismo de hot reload é deferimento — ver ADR-0002). Consequência: dentro de uma mesma sessão de server, todos os retornos carregam o mesmo `policy_version`. Reload exige restart.

Esta restrição é deliberada para o MVP: simplifica reprodutibilidade (versão imutável durante a sessão) e evita complexidade de invalidação de cache. Custo: pequeno overhead operacional para o jurídico atualizar Política em produção. Aceitável para MVP.

## 7. Não-objetivos e fronteiras

### 7.1 Não-objetivos do componente

Os comportamentos abaixo estão fora do escopo desta spec. Implementação do componente NÃO deve introduzi-los. Cada um tem registro de razão e, quando aplicável, referência a deferimento futuro.

- **Browseability humana de cláusulas individuais** (`policy://clauses/{id}` como resource adicional). Eliminado por redundância com `get_clause`. Pode ser revisitado se a Política crescer o suficiente para justificar leitor humano dedicado. Registrado em ADR-0002.

- **Hot reload da Política em runtime**. Componente carrega Política no startup; mudanças exigem restart. Deferimento por simplicidade do MVP (§6.5). Registrado em ADR-0002.

- **Suporte a schemas alternativos** (Políticas com estrutura distinta da v0.1.0). Componente serve apenas o schema canônico. Generalização para múltiplos schemas é deferimento explícito. Registrado em ADR-0002. Não confundir com suporte a `legal_framework` alternativo, que é nativamente suportado via troca de vocabulários jurisdicionais — ver bullet abaixo sobre múltiplas instâncias e ADR-0005.

- **Emissão do Report consolidado**. Estrutura do Report é definida em outro lugar (`architecture-overview.md` §5.6 — Reporter); este componente fornece os componentes do Report (versões da Política, vereditos) mas não os agrega.

- **Anotações declarativas de tratamento no código** (sugestão de reconhecimento de comentários ou decoradores indicando consentimento obtido, anonymização aplicada, etc.). Deferimento explícito como evolução pós-MVP. Registrado em ADR-0002.

- **Mecanismo interno de avaliação do `check_applicability`**. Spec define contrato; mecanismo é decisão de implementação livre (princípio aplicado: spec descreve o quê, não como).

- **Múltiplas Políticas ou múltiplos frameworks jurisdicionais em uma única instância do componente**. Uma instância serve uma Política sob um framework, ambos imutáveis durante a sessão. Servir LGPD + GDPR simultaneamente exige duas instâncias do componente, distinguidas no Matcher via configuração de `mcp_servers` (uma entrada por instância). Hot-swap de Política ou de `legal_framework` durante a sessão é deferimento explícito — registrado em ADR-0002. Decisão arquitetural de servir-uma-Política-por-instância governada por ADR-0005 Decision 2.

### 7.2 Não-objetivos do escopo da Política do MVP

A v0.1.0 da Política cobre exclusivamente cláusulas com tratamento prescrito em duas dimensões avaliáveis por análise estática de payload:

- `consent_required` (consentimento explícito do titular)
- `anonymization_required` (anonymização do dado antes do tratamento)

Outras dimensões da LGPD ficam **fora do escopo do MVP**:

- Restrições de transferência internacional (Art. 33+).
- Limites de retenção temporal (Art. 15-16).
- Direitos do titular (acesso, portabilidade, eliminação — Art. 18+).
- Tratamento de dados pessoais por crianças e adolescentes (Art. 14).
- Comunicação e tratamento compartilhado entre controladores (Art. 26+).

Inclusão de dimensões adicionais é evolução pós-MVP, registrada em ADR-0002. Critério de revisita: validação empírica do MVP completa + demanda concreta documentada.

A escolha das duas dimensões iniciais reflete viabilidade técnica (análise estática de PR consegue avaliar) e relevância em literatura brasileira de proteção de dados, onde consentimento e anonimização aparecem como dimensões frequentemente discutidas. Validação empírica da cobertura efetiva contra base de PRs reais é parte do trabalho de validação do MVP (semana 6 do cronograma da `proposta-tcc2.md`).

### 7.3 Fronteira epistêmica — conformidade declarativa, não efetiva

O componente avalia o que o código **declara** fazer, não o que ele **efetivamente faz** em produção. Análise estática de pull request examina:

- Declaração de base legal (quando presente).
- Transformações visíveis no diff (anonymização chamada, redaction aplicada).
- Estrutura de controle (presença de checks de consentimento identificáveis sintaticamente).

Análise estática NÃO examina:

- Estado runtime de consentimento.
- Anonymização aplicada em pipeline upstream invisível.
- Retenção configurada em outro serviço.
- Comportamento real em produção.

Quando a verificação requer dimensão fora da análise estática, o componente retorna `verdict: indeterminate` com `verification_scope` nomeando a dimensão (§4.3). Isto é honestidade epistêmica explícita: sistema não finge certeza não justificada.

### 7.4 Decisões deferidas

ADR-0002 documenta integralmente as decisões deferidas relacionadas a este componente, com critérios de revisita explícitos. Implementação deste componente referencia ADR-0002 quando precisar justificar ausência de feature mencionada acima.

## 8. Critérios de aceitação

A implementação do `policy-reader` está completa quando todos os critérios abaixo forem demonstravelmente verdadeiros. Cada critério é verificável por teste automatizado ou inspeção direta.

### 8.1 Resources

- [ ] `policy://catalog` retorna lista de itens conforme estrutura §3.1 para uma Política de teste com pelo menos uma cláusula `active` e uma `deprecated`.
- [ ] Cláusulas `deprecated` no catálogo carregam `successors`; cláusulas `active` não.
- [ ] `policy://schema-version` retorna objeto com `policy_schema_version`, `policy_version`, `legal_framework`, `compatible_schema_range` conforme §3.2; campo `legal_framework` reflete exatamente o valor declarado no header da Política carregada.
- [ ] `policy://vocabularies` retorna objeto agregando os quatro vocabulários jurisdicionais (`operation`, `lawful_basis`, `control`, `out_of_scope`) carregados de `policy/vocabularies/<framework>/*.yaml` no startup, conforme §3.3. Read-only, idempotente.

### 8.2 Tools — `get_clause`

- [ ] Retorna cláusula `active` em sucesso, com estrutura completa conforme §4.1.
- [ ] Retorna cláusula `deprecated` em sucesso, com bloco `tombstone` contendo `successors`, `effective_until`, `deprecation_reason`.
- [ ] Retorna `INVALID_CLAUSE_ID_FORMAT` para `clause_id` que não casa com `^POL-\d{3}$`.
- [ ] Retorna `CLAUSE_NOT_FOUND` para `clause_id` com formato válido mas inexistente.

### 8.3 Tools — `find_clauses_by_law_article`

- [ ] Retorna lista de cláusulas matching com especificação `{lei, artigo}` (busca ampla).
- [ ] Retorna lista narrowed com especificação `{lei, artigo, inciso}` (busca estreita).
- [ ] Exclui cláusulas `deprecated` do resultado.
- [ ] Retorna lista vazia (não erro) para especificação válida sem cláusulas correspondentes.
- [ ] Retorna `INVALID_LAW_IDENTIFIER` para `lei` fora do vocabulário do header da Política.

### 8.4 Tools — `check_applicability`

- [ ] Retorna `verdict: compliant` para context que casa com requirements da cláusula.
- [ ] Retorna `verdict: violation_candidate` com `evidence` e `contradicted_requirement` para context que viola requirement.
- [ ] Retorna `verdict: indeterminate` com `verification_scope` completo (`dimension`, `prescribed_treatment`, `verification_target`) quando análise estática não decide.
- [ ] Retorna `verdict: not_applicable` quando cláusula não governa o context.
- [ ] Retornos em sucesso carregam o trinque de provenance (`policy_schema_version`, `policy_version`, `legal_framework`) conforme §6.4.
- [ ] Retorna `CLAUSE_DEPRECATED` (retryable) com `successors` em `details` para `clause_id` deprecated.
- [ ] Retorna erros de validation (`INVALID_DATA_CATEGORY`, `INVALID_OPERATION`, `EMPTY_DATA_CATEGORIES`) para inputs com vocabulário ou estrutura inválida.

### 8.5 Contrato de erro

- [ ] Todos os retornos de erro têm estrutura canônica (`errorCode`, `message`, `isRetryable`, `details`) conforme §5.1.
- [ ] `errorCode` em inglês maiúsculas-snake; `message` em português humano-legível.
- [ ] `details` carrega forma esperada por `errorCode` conforme tabela §5.4.
- [ ] Empty result e veredito `indeterminate` retornam `isError: false`.

### 8.6 Provenance

- [ ] Handshake via `policy://schema-version` aborta consumidor com schema incompatível.
- [ ] `check_applicability` em sucesso carrega o trinque completo de provenance (`policy_schema_version`, `policy_version`, `legal_framework`), conforme §6.4.

### 8.7 Implementação

- [ ] Stack conforme ADR-0001 (FastMCP 3.x, Python 3.12.7).
- [ ] Política carregada no startup; restart necessário para reload.
- [ ] Vocabulário POL-000 (classes de dados) lido de `policy/SCHEMA.md`; vocabulários jurisdicionais (`operation`, `lawful_basis`, `control`, `out_of_scope`) lidos de `policy/vocabularies/<framework>/*.yaml` no startup, governados por `legal_framework` do header da Política (nenhum vocabulário hardcoded no componente).
- [ ] Troca de `legal_framework` da Política não exige alteração de código: instanciar Política nova/clonada sob nova jurisdição, popular `policy/vocabularies/<new_framework>/`, atualizar header, restart. Verificável por exercício de clone sob framework alternativo.

### 8.8 Review pass do `architecture-overview`

Review pass reconstruído retrospectivamente nos termos do ADR-0003 Decisão 2. A spec foi authored nas sessões #05-#06, antes da forma "três beats" cristalizar em §8.<final> do `semgrep-runner` (sessão #07) e ser formalizada em ADR-0002 Decisão 5. Duas classes de inconsistência foram detectadas entre esta spec e `architecture-overview.md` durante o cleanup da sessão #06; ambas foram sincronizadas no mesmo commit.

**Múltiplas seções — nome canônico do servidor MCP.** Texto pré-patch: ocorrências de `lgpd-policy-reader` em onze pontos do documento — glossário de MCP, §2 (Camada 2), §3 (Etapa 3), §4.1, §4.2 (cabeçalho do bloco e linha do `semgrep-runner`), §5.1 (Coordinator Tools permitidas), §5.3 (Detector Tools permitidas e Justificativa do escopo), §5.5 (Matcher Tools permitidas), §5.6 (Reporter Output) e §5.7 (matriz tools × subagentes). Esta spec §1 adota `policy-reader` como nome canônico; o prefixo `lgpd-` é redundância com o escopo do artefato servido (a Política sob `policy/` já é derivada da LGPD) e diverge da convenção dos reference servers da Anthropic. Patch aplicado: substituição mecânica de todas as ocorrências por `policy-reader`.

**§7.3 — tabela "MVP versus trabalho futuro".** Texto pré-patch: enumeração de cinco evoluções fora do MVP ("Cinco evoluções estão fora do MVP. Para quatro delas, o design não fecha portas... A quinta — AEP — fica fora do roadmap deste trabalho"), sem entrada para o escopo dimensional da Política. Esta spec §7 restringe a cobertura MVP a `consent_required` e `anonymization_required` (as duas dimensões avaliáveis por análise estática); transferência internacional, retenção, direitos do titular, dados de menores e tratamento compartilhado ficam fora. Patch aplicado: acréscimo de linha "Dimensões adicionais da LGPD na Política" à tabela, com critério de reabertura "Validação empírica do MVP completa + demanda concreta documentada"; ajuste das contagens de "Cinco/quatro/quinta" para "Seis/cinco/sexta".

Patches sincronizados em `architecture-overview.md` no commit `6945840` (PR #7, cleanup da sessão #06).

### 8.9 Review pass — sessão #16 (multi-cliente)

Review pass aplicado nos termos de ADR-0002 Decisão 5 durante o cleanup da sessão #16 (architecture rewrite para suporte multi-cliente, ADR-0005). Três classes de inconsistência foram detectadas entre esta spec e o estado pós-Commits 1–3 da branch `arch/multi-client-policy-rewrite`; todas foram sincronizadas no Commit 4.

**§3 — número de resources expostos.** Texto pré-patch: "O componente expõe dois resources" no header da §3, sem entrada para o vocabulário jurisdicional como recurso compartilhado entre Matcher e Classifier. Esta spec pós-Commit 4 expõe três resources (`policy://catalog`, `policy://schema-version`, `policy://vocabularies`); o novo `policy://vocabularies` (§3.3) materializa o princípio Resource vs Tool de ADR-0005 Decision 4 — Classifier consome como contexto léxico sem ganhar acesso às tools. Patch aplicado: header §3 atualizado para "três resources, todos sob o scheme `policy://`"; §3.3 nova com URI, conteúdo, semântica, consumidores autorizados e casos de erro.

**§2.1 — eixos de identidade da Política.** Texto pré-patch: "A Política em si carrega dois eixos de versão independentes" (`policy_schema_version`, `policy_version`), sem entrada para o eixo jurisdicional. ADR-0005 Decision 2 estabelece `legal_framework` como terceiro eixo de identidade, valor único, imutável durante a sessão da instância. Patch aplicado: lista de "dois eixos de versão" expandida para "três eixos de identidade" com inclusão de `legal_framework`; parágrafo "Multi-framework — escopo arquitetural" acrescentado declarando impossibilidade de cross-framework simultâneo numa mesma instância; provenance temporal expandida para "temporal e jurisdicional" em §2.1, §3.2, §4.3 e §6.4.

**§1 — consumidores autorizados do componente.** Texto pré-patch: "Subagente Matcher, exclusivamente" como descrição única de consumidor em §1, sem distinção entre tools e resources. A introdução do resource `policy://vocabularies` quebra essa simetria — tools permanecem exclusivas do Matcher, mas o resource é também consumido pelo Classifier (read-only). Patch aplicado: §1 reescrito para distinguir consumidores de tools (Matcher) de consumidores de resources (Matcher + Classifier para `policy://vocabularies`); §3.3 explicita os consumidores autorizados em subseção dedicada.

Demais ajustes (notas operacionais de payload em §4.3, atualização de checkboxes de aceitação em §8, sub-patches de terminologia em §2.1 e §7.1) são derivativos das três classes acima e foram aplicados no mesmo Commit 4.

Commit 4 da branch `arch/multi-client-policy-rewrite`.