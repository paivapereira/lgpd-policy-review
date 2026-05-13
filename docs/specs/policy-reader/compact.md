# policy-reader — compact spec

> **Esta é uma destilação operacional de `canonical.md`, otimizada para consumo por agente de implementação. Em caso de conflito, `canonical.md` prevalece. Escalation pointers inline (`**See canonical §X.Y if:**`) marcam pontos onde abrir a canonical é necessário para decidir corretamente.**

**Spec version:** 0.1.0
**Canonical source:** [canonical.md](./canonical.md)

---

## 1. Identity

**Server name:** `policy-reader`
**Function:** MCP server that exposes the versioned Data Protection Policy as queryable resource and as compliance-evaluation tool, consumed by the Matcher subagent in the code review system.
**Authorized consumer:** Matcher subagent, exclusively. Enforced via `mcp_servers` config in Matcher's AgentDefinition.

## 2. Wire format

All `CallToolResult` returns use hybrid placement: structured payload in `structuredContent`, human-readable prose in `content[0].text`. See ADR-0002 §1. Error envelope shape — see §3 below.

## 3. Error contract

Three error classes (see ADR-0002 §3 for class semantics). Empty result and `indeterminate` verdict are **not errors** — they return `isError: false`.

| `errorCode` | Class | Retryable | Emitting tools | Condition | `details` shape |
|---|---|---|---|---|---|
| `INVALID_CLAUSE_ID_FORMAT` | validation | false | `get_clause`, `check_applicability` | `clause_id` não casa com regex `^POL-\d{3}$` | `{provided, expected_format}` |
| `CLAUSE_NOT_FOUND` | business | false | `get_clause`, `check_applicability` | `clause_id` tem formato válido mas não existe na Política atual | `{clause_id}` |
| `CLAUSE_DEPRECATED` | business | true | `check_applicability` | `clause_id` aponta para cláusula com `status: deprecated` | `{clause_id, successors, deprecation_reason}` |
| `INVALID_LAW_IDENTIFIER` | validation | false | `find_clauses_by_law_article` | `lei` fora do vocabulário declarado em `accepted_law_identifiers` da Política | `{provided, accepted_values}` |
| `INVALID_DATA_CATEGORY` | validation | false | `check_applicability` | Elemento de `data_categories` fora do vocabulário POL-000 | `{invalid_value, accepted_values}` |
| `INVALID_OPERATION` | validation | false | `check_applicability` | `operation` fora do enum declarado em `policy/SCHEMA.md` | `{provided, accepted_values}` |
| `EMPTY_DATA_CATEGORIES` | validation | false | `check_applicability` | `data_categories` é lista vazia | `{}` |

**Empty error class declaration:** system errors are intentionally absent — Policy I/O failures are caught at startup, not at request runtime. See canonical §5.4 if implementing additional system error handling.

**Error payload shape (all errorCodes):**

```yaml
{
  errorCode: <string>,    # MAIÚSCULAS_SNAKE, inglês, estável
  message: <string>,      # português, humano-legível
  isRetryable: <boolean>,
  details: <object>       # forma específica por errorCode (ver tabela)
}
```

## 4. Resources

Two resources, both under `policy://` scheme (custom scheme convention per ADR-0002 §7).

### 4.1 `policy://catalog`

**URI:** `policy://catalog` (static, no parameters)
**Read semantics:** idempotent. Reflects current state of versioned Policy. Reload requires server restart.
**Content:** index of clauses. Each item:

```yaml
{
  clause_id: <string POL-NNN>,
  title: <string>,
  status: active | deprecated,
  article_sources_summary: <list, forma exata em policy/SCHEMA.md>,
  successors: [POL-NNN, ...]  # presente APENAS quando status: deprecated
}
```

Ordering: natural order of `clause_id` (POL-001, POL-002, ...). No pagination in v0.1.0.

### 4.2 `policy://schema-version`

**URI:** `policy://schema-version` (static, no parameters)
**Read semantics:** idempotent. Serves as version **handshake**.
**Content:**

```yaml
{
  policy_schema_version: 0.1.0,
  policy_version: <versão do conteúdo da Política>,
  compatible_schema_range: 0.1.x
}
```

**Handshake protocol:** consumer reads this resource before invoking any tool; aborts fail-fast if `policy_schema_version` is outside `compatible_schema_range`.

## 5. Tools

Three tools. Naming convention: `mcp__policy-reader__<tool>` (runtime-generated). Local names below.

### 5.1 `get_clause`

**Description (English, no markdown, this is the actual tool description seen by the model):**

> Retrieve a single Policy clause by its stable `clause_id`. Use this when the caller already knows the exact identifier. Do not use this to search clauses by law article — use `find_clauses_by_law_article`. Do not use this to evaluate whether a clause applies to a context — use `check_applicability`.
>
> Returns the clause object with `clause_id`, `title`, `article_source`, `applicability_scope`, `requirements`, `exceptions`, and `status`. If the clause is `deprecated`, returns it successfully with a `tombstone` block containing `successors`, `effective_until`, and `deprecation_reason`. Deprecated clauses are not errors here — auditing historical decisions is a legitimate use case.
>
> Returns business error `CLAUSE_NOT_FOUND` (non-retryable) if `clause_id` does not match any clause.

**`inputSchema`:**

| Field | Type | Required | Description |
|---|---|---|---|
| `clause_id` | string | yes | `^POL-\d{3}$` |

**Output structure (success):**

```yaml
{
  clause_id: POL-027,
  title: <string>,
  status: active,
  article_source: [{lei, artigo, inciso, ...}],   # estrutura em policy/SCHEMA.md
  applicability_scope: [<data_category>, ...],     # vocabulário em policy/SCHEMA.md
  requirements: [{id: R1, text: ...}, ...],
  exceptions: [{id: E1, text: ...}, ...]
}

# Quando status: deprecated, adiciona:
tombstone: {
  successors: [POL-NNN, ...],
  effective_until: <ISO date>,
  deprecation_reason: <string>
}
```

**Errors:** `INVALID_CLAUSE_ID_FORMAT`, `CLAUSE_NOT_FOUND` (ver tabela §3).

**Example — active clause:**

```json
Input:  {"clause_id": "POL-027"}
Output: {
  "isError": false,
  "structuredContent": {
    "clause_id": "POL-027",
    "title": "Consentimento para coleta de dados de identificação",
    "status": "active",
    "article_source": [{"lei": "LGPD", "artigo": 7, "inciso": 1}],
    "applicability_scope": ["dados_de_identificacao"],
    "requirements": [{"id": "R1", "text": "Consentimento explícito antes da coleta."}],
    "exceptions": []
  },
  "content": [{"type": "text", "text": "POL-027: Consentimento para coleta de dados de identificação (LGPD Art. 7º, I)."}]
}
```

**Example — deprecated clause:**

```json
Input:  {"clause_id": "POL-014"}
Output: {
  "isError": false,
  "structuredContent": {
    "clause_id": "POL-014",
    "status": "deprecated",
    "tombstone": {
      "successors": ["POL-031", "POL-032"],
      "effective_until": "2026-06-30",
      "deprecation_reason": "Cláusula original dividida em duas após reforma legislativa."
    },
    "article_source": [...],
    "requirements": [...]
  },
  "content": [{"type": "text", "text": "POL-014 (deprecated): sucessores POL-031, POL-032."}]
}
```

### 5.2 `find_clauses_by_law_article`

**Description (English, no markdown):**

> Find Policy clauses that reference a given law article (or sub-section of it). Use this when the caller needs to enumerate clauses applicable to a specific law fragment without knowing clause identifiers. Do not use this when `clause_id` is known — use `get_clause`. Do not use to evaluate applicability — use `check_applicability`.
>
> Specification is hierarchical and progressive: `lei` and `artigo` are required; `paragrafo`, `inciso`, `alinea` are optional and narrow the search. A clause matches when ANY element of its `article_source` list starts hierarchically with the given specification (matching `lei` first, then `artigo`, then optional fields in order). Clauses with multiple legal anchors thus match if any anchor is in scope.
>
> Returns a list of clause objects (same structure as `get_clause` success, without `tombstone` — deprecated clauses are excluded). Empty list is not an error: if no clauses match, returns `[]` with `isError: false`.

**`inputSchema`:**

| Field | Type | Required | Description |
|---|---|---|---|
| `lei` | string | yes | Vocabulary in `accepted_law_identifiers` of Policy header |
| `artigo` | integer | yes | |
| `paragrafo` | integer | no | |
| `inciso` | integer | no | Canonical form is integer, not Roman numeral |
| `alinea` | string | no | e.g., `"a"`, `"b"` |

**Output structure (success):** list of clause objects (active only, no `tombstone`). Result list ordered by natural `clause_id` order — same convention as `policy://catalog`.

**Errors:** `INVALID_LAW_IDENTIFIER` (ver tabela §3). Empty match returns `[]`, not error.

**Example — broad search:**

```json
Input:  {"lei": "LGPD", "artigo": 7}
Output: {
  "isError": false,
  "structuredContent": [
    {"clause_id": "POL-027", "article_source": [{"lei": "LGPD", "artigo": 7, "inciso": 1}], ...},
    {"clause_id": "POL-028", "article_source": [{"lei": "LGPD", "artigo": 7, "inciso": 2}], ...}
  ],
  "content": [{"type": "text", "text": "2 cláusulas encontradas para LGPD Art. 7º."}]
}
```

**Example — empty result:**

```json
Input:  {"lei": "LGPD", "artigo": 50}
Output: {
  "isError": false,
  "structuredContent": [],
  "content": [{"type": "text", "text": "Nenhuma cláusula referencia LGPD Art. 50."}]
}
```

### 5.3 `check_applicability`

**Description (English, no markdown):**

> Evaluate whether a Policy clause applies to a specific code-handling context, and produce a structured verdict. This is the core evaluation tool. Use this when the caller has identified a candidate clause and needs a verdict on whether it governs a specific context.
>
> The caller provides `structured_context` describing the handling (data classes, operation, optional legal basis, optional destination). Returns one of four verdicts:
>
> - `compliant` — handling is consistent with clause requirements.
> - `violation_candidate` — handling appears to contradict the clause; carries evidence.
> - `indeterminate` — static analysis cannot conclude; carries `verification_scope`.
> - `not_applicable` — the clause does not govern this handling in this context.
>
> If the clause is `deprecated`, returns business error `CLAUSE_DEPRECATED` (retryable) — caller should retry with a successor `clause_id` from `details.successors`.

**Note (MVP):** initial implementation returns `not_applicable` for any input. This is the legitimate verdict while no substantive clause exists. POL-001 will exercise the four-verdict enum.

**`inputSchema`:**

| Field | Type | Required | Description |
|---|---|---|---|
| `clause_id` | string | yes | `^POL-\d{3}$` |
| `structured_context.data_categories` | array<string> | yes | Non-empty; vocabulary in POL-000 |
| `structured_context.operation` | enum string | yes | Enum in `policy/SCHEMA.md` |
| `structured_context.legal_basis` | string | no | Free text; absence = code does not declare basis |
| `structured_context.destination` | string | no | e.g., `external_service`, `internal_database` |

**Output structure (success) — varies by verdict:**

```yaml
# Veredito compliant
{
  verdict: compliant,
  policy_clause_ref: POL-NNN,
  evidence: <texto curto>,
  policy_schema_version: 0.1.0,
  policy_version: <versão>
}

# Veredito violation_candidate
{
  verdict: violation_candidate,
  policy_clause_ref: POL-NNN,
  evidence: <texto>,
  contradicted_requirement: R1,   # sub-id do requirement contradito
  policy_schema_version, policy_version
}

# Veredito indeterminate
{
  verdict: indeterminate,
  policy_clause_ref: POL-NNN,
  verification_scope: {
    dimension: <enum: upstream_state | ...>,
    prescribed_treatment: <enum: consent_required | anonymization_required>,
    verification_target: <texto em português>
  },
  policy_schema_version, policy_version
}

# Veredito not_applicable
{
  verdict: not_applicable,
  policy_clause_ref: POL-NNN,
  evidence: <texto explicando por que a cláusula não governa>,
  policy_schema_version, policy_version
}
```

**Note:** `evidence` and `verification_target` are **generated by the component**, not provided by the caller. Generation mechanism (template, model call, hybrid) is implementation-free.

**Errors:** `INVALID_CLAUSE_ID_FORMAT`, `CLAUSE_NOT_FOUND`, `CLAUSE_DEPRECATED`, `INVALID_DATA_CATEGORY`, `INVALID_OPERATION`, `EMPTY_DATA_CATEGORIES` (ver tabela §3).

**Example — compliant:**

```json
Input: {
  "clause_id": "POL-027",
  "structured_context": {
    "data_categories": ["dados_de_identificacao"],
    "operation": "collect",
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
    "policy_version": "..."
  },
  "content": [{"type": "text", "text": "POL-027 compliant: base legal declarada coerente com requirement."}]
}
```

**Example — violation_candidate:**

```json
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
    "policy_version": "..."
  },
  "content": [{"type": "text", "text": "POL-031 violation_candidate: base legal declarada não está entre as hipóteses do Art. 11."}]
}
```

**Example — indeterminate:**

```json
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
      "verification_target": "Confirmar se consentimento do titular foi obtido antes desta transmissão."
    },
    "policy_schema_version": "0.1.0",
    "policy_version": "..."
  },
  "content": [{"type": "text", "text": "POL-027 indeterminate: análise estática não decide; verificar consentimento upstream."}]
}
```

**Example — deprecated error:**

```json
Input: {"clause_id": "POL-014", "structured_context": {...}}
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
  "content": [{"type": "text", "text": "POL-014 deprecated: tentar com POL-031 ou POL-032."}]
}
```

**See canonical §4.3 if:** the four-verdict enum or the structure of `verification_scope` feels ambiguous. The canonical has long-form prose distinguishing why `indeterminate` is a success and what `verification_target` should look like.

**See canonical §6.4 if:** unsure why `policy_schema_version` and `policy_version` are in every `check_applicability` success but not in `get_clause` or `find_clauses_by_law_article`. Provenance temporal is required when the return is a verdict that will be cited in a Report.

## 6. Initialization

Policy is loaded at server **startup**. File I/O errors during load abort startup (no runtime I/O errors during tool calls). Reload requires restart — hot reload is deferred (ADR-0002).

Vocabulary POL-000 and `operation` enum read from `policy/SCHEMA.md` at startup.

**See canonical §6.5 if:** considering hot reload or in-session Policy mutation. Explicitly deferred for MVP.
