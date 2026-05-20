# policy-reader — compact spec

> **Esta é uma destilação operacional de `canonical.md`, otimizada para consumo por agente de implementação. Em caso de conflito, `canonical.md` prevalece. Escalation pointers inline (`**See canonical §X.Y if:**`) marcam pontos onde abrir a canonical é necessário para decidir corretamente.**

**Spec version:** 0.1.0
**Canonical source:** [canonical.md](./canonical.md)

---

## 1. Identity

**Server name:** `policy-reader`
**Function:** MCP server that exposes the versioned Data Protection Policy — under the jurisdictional framework declared in its header (`legal_framework`) — as queryable resource and as compliance-evaluation tool, consumed by the Matcher subagent in the code review system. Framework-agnostic: serves any Policy whose `policy_schema_version` is within `compatible_schema_range` (structural handshake). The declared `legal_framework` is exposed via handshake for consumer validation (see §4.2).
**Authorized consumers:** Tools (`get_clause`, `find_clauses_by_law_article`, `check_applicability`) — Matcher subagent, exclusively. Resources (`policy://catalog`, `policy://schema-version`, `policy://vocabularies`) — Matcher; `policy://vocabularies` additionally consumed by Classifier (read-only, no tool access). Enforced via `mcp_servers` config in each subagent's AgentDefinition.

## 2. Wire format

All `CallToolResult` returns use hybrid placement: structured payload in `structuredContent`, human-readable prose in `content[0].text`. See ADR-0002 §1.

For domain errors (validation, business, system — see §3), the envelope `{errorCode, message, isRetryable, details}` is serialized in `structuredContent` with wire `isError: false`. The formal success-vs-error discriminator is presence of the `errorCode` field in `structuredContent`. Wire `isError: true` is reserved for MCP protocol-level failures (schema-invalid input, nonexistent tool). See ADR-0002 §3 (amendment) for the constraint that motivates this convention.

## 3. Error contract

Three error classes (see ADR-0002 §3 for class semantics). Empty result and `indeterminate` verdict are **not errors** — they carry no `errorCode` field in `structuredContent`. Wire convention in §2.

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

**Dynamic `accepted_values` content:** for `INVALID_DATA_CATEGORY` and `INVALID_OPERATION`, `accepted_values` is populated from the loaded Policy at runtime — `INVALID_OPERATION` from `policy/vocabularies/<framework>/operation.yaml` (resource `policy://vocabularies`); `INVALID_DATA_CATEGORY` from POL-000 of the Policy (governed by `policy/SCHEMA.md`). Content varies per loaded Policy; payload **shape** (`{invalid_value, accepted_values}` / `{provided, accepted_values}`) is stable.

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

Three resources, all under `policy://` scheme (custom scheme convention per ADR-0002 §7).

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
**Read semantics:** idempotent. Serves as **dual handshake** (structural + jurisdictional).
**Content:**

```yaml
{
  policy_schema_version: 0.1.0,
  policy_version: <versão do conteúdo da Política>,
  legal_framework: <LGPD | GDPR | ...>,   # único, imutável durante a sessão; governa policy/vocabularies/<framework>/
  compatible_schema_range: 0.1.x
}
```

**Handshake protocol:** consumer reads this resource before invoking any tool.
- **Structural:** verify `policy_schema_version` is within `compatible_schema_range`; abort if not.
- **Jurisdictional:** verify `legal_framework` is in the consumer's accepted-frameworks list (configured in its AgentDefinition); abort if not.

Either failure is fail-fast — consumer must not invoke tools. This resource declares what the Policy instantiates; the consumer decides locally (component does not reject consumers).

### 4.3 `policy://vocabularies`

**URI:** `policy://vocabularies` (static, no parameters)
**Read semantics:** idempotent. Content determined at startup by `legal_framework` in the Policy header; immutable during session. Reload requires restart.
**Content:** object aggregating the four jurisdictional vocabularies loaded from `policy/vocabularies/<framework>/*.yaml`:

```yaml
{
  operation:     {schema_version, framework, values: [...]},   # operações de tratamento
  lawful_basis:  {schema_version, framework, values: [...]},   # com campo `category`: personal_data | sensitive_data
  control:       {schema_version, framework, values: [...]},   # e.g., consent_required, anonymization_required
  out_of_scope:  {schema_version, framework, values: [...]}    # motivos de exclusão de categoria em cláusulas definitional
}
```

Vocabulary structure (`schema_version`, `framework`, `values[]`) governed by `policy/SCHEMA.md` §10.

**Authorized consumers:** Matcher (alongside tools) and Classifier (read-only, no tool access — Resource vs Tool, ADR-0005 Decision 4).

**Error cases:** I/O failure on any of the four YAMLs at startup aborts boot (protocol-level config error). No runtime errors during session.

## 5. Tools

Three tools. Naming convention: `mcp__policy-reader__<tool>` (runtime-generated). Local names below.

### 5.1 `get_clause`

**Description (English, no markdown, this is the actual tool description seen by the model):**

> Retrieve a single Policy clause by its stable `clause_id`. Use this when the caller already knows the exact identifier. Do not use this to search clauses by law article — use `find_clauses_by_law_article`. Do not use this to evaluate whether a clause applies to a context — use `check_applicability`.
>
> Returns a polymorphic clause object with `clause_id`, `clause_type` (`substantive` or `definitional`), `policy_schema_version`, `title`, `status`, and `statutory_reference`. Substantive clauses carry `applies_to`, `control`, `requirements`, and `exceptions`. Definitional clauses carry `defines` and `out_of_scope`. If the clause is `deprecated`, returns it successfully with an additional `tombstone` block containing `successors`, `effective_until`, and `deprecation_reason`. Deprecated clauses are not errors here — auditing historical decisions is a legitimate use case.
>
> Returns business error `CLAUSE_NOT_FOUND` (non-retryable) if `clause_id` does not match any clause.

**`inputSchema`:**

| Field | Type | Required | Description |
|---|---|---|---|
| `clause_id` | string | yes | `^POL-\d{3}$` |

**Output structure (success) — polymorphic by `clause_type`:**

```yaml
# Substantive clause
{
  clause_id: POL-NNN,
  clause_type: substantive,
  policy_schema_version: 0.1.0,
  title: <string>,
  status: active,
  statutory_reference: [{lei, artigo, inciso, ...}],   # estrutura em policy/SCHEMA.md
  applies_to: {
    personal_data_categories: [<category>, ...],         # vocabulário em POL-000
    operation: [<operation>, ...]                        # vocabulário em policy/vocabularies/<framework>/operation.yaml
  },
  control: <control>,                                    # vocabulário em policy/vocabularies/<framework>/control.yaml
  requirements: [{id: R1, text: ...}, ...],
  exceptions: [{id: E1, text: ...}, ...]
}

# Definitional clause
{
  clause_id: POL-NNN,
  clause_type: definitional,
  policy_schema_version: 0.1.0,
  title: <string>,
  status: active,
  statutory_reference: [{lei, artigo, ...}],
  defines: {                              # SCHEMA.md §5.2-5.3
    vocabulary_kind: <string>,
    entries: [
      {name, definition, canonical_examples, statutory_reference, special_category},
      ...
    ]
  },
  out_of_scope: [                         # SCHEMA.md §5.4
    {topic, statutory_reference, reason, fallback},
    ...
  ]
}

# Quando status: deprecated em qualquer tipo, adiciona:
tombstone: {
  successors: [POL-NNN, ...],
  effective_until: <ISO date>,
  deprecation_reason: <string>
}
```

**Discriminator note:** consumers MUST branch on `clause_type` before reading type-specific fields. Substantive-only fields (`applies_to`, `control`, `requirements`, `exceptions`) are absent on definitional clauses; definitional-only fields (`defines`, `out_of_scope`) are absent on substantive clauses.

**Errors:** `INVALID_CLAUSE_ID_FORMAT`, `CLAUSE_NOT_FOUND` (ver tabela §3). Examples of error envelopes live in canonical §4.1 and §5; not duplicated here.

**Example — active substantive clause:**

```json
Input:  {"clause_id": "POL-027"}
Output: {
  "isError": false,
  "structuredContent": {
    "clause_id": "POL-027",
    "clause_type": "substantive",
    "policy_schema_version": "0.1.0",
    "title": "Consentimento para coleta de dados de identificação",
    "status": "active",
    "statutory_reference": [{"lei": "LGPD", "artigo": 7, "inciso": 1}],
    "applies_to": {
      "personal_data_categories": ["dados_de_identificacao"],
      "operation": ["collection"]
    },
    "control": "consent_required",
    "requirements": [{"id": "R1", "text": "Consentimento explícito antes da coleta."}],
    "exceptions": []
  },
  "content": [{"type": "text", "text": "POL-027: Consentimento para coleta de dados de identificação (LGPD Art. 7º, I)."}]
}
```

**Example — deprecated clause (substantive):**

```json
Input:  {"clause_id": "POL-014"}
Output: {
  "isError": false,
  "structuredContent": {
    "clause_id": "POL-014",
    "clause_type": "substantive",
    "policy_schema_version": "0.1.0",
    "status": "deprecated",
    "tombstone": {
      "successors": ["POL-031", "POL-032"],
      "effective_until": "2026-06-30",
      "deprecation_reason": "Cláusula original dividida em duas após reforma legislativa."
    },
    "statutory_reference": [{"lei": "LGPD", "artigo": 11}],
    "applies_to": {"personal_data_categories": ["dados_de_saude"], "operation": ["storage"]},
    "control": "consent_required",
    "requirements": [{"id": "R1", "text": "..."}],
    "exceptions": []
  },
  "content": [{"type": "text", "text": "POL-014 (deprecated): sucessores POL-031, POL-032."}]
}
```

### 5.2 `find_clauses_by_law_article`

**Description (English, no markdown):**

> Find Policy clauses that reference a given law article (or sub-section of it). Use this when the caller needs to enumerate clauses applicable to a specific law fragment without knowing clause identifiers. Do not use this when `clause_id` is known — use `get_clause`. Do not use to evaluate applicability — use `check_applicability`.
>
> Specification is hierarchical and progressive: `lei` and `artigo` are required; `paragrafo`, `inciso`, `alinea` are optional and narrow the search. A clause matches when ANY element of its `statutory_reference` list starts hierarchically with the given specification (matching `lei` first, then `artigo`, then optional fields in order). Clauses with multiple legal anchors thus match if any anchor is in scope.
>
> Returns an object with a `clauses` field — list of polymorphic clause objects (same structure as `get_clause` success, without `tombstone` — deprecated clauses are excluded). The result list MAY mix `clause_type: definitional` and `clause_type: substantive`; consumers MUST NOT filter or coerce by `clause_type` to uniformize the list. Empty list is not an error: returns `{clauses: []}` with `isError: false`.

**`inputSchema`:**

| Field | Type | Required | Description |
|---|---|---|---|
| `lei` | string | yes | Vocabulary in `accepted_law_identifiers` of Policy header |
| `artigo` | integer | yes | |
| `paragrafo` | integer | no | |
| `inciso` | integer | no | Canonical form is integer, not Roman numeral |
| `alinea` | string | no | e.g., `"a"`, `"b"` |

**Output structure (success):** object `{clauses: [<clause>, ...]}`, where each `<clause>` carries the polymorphic structure of `get_clause` success (active only, no `tombstone`). Result list ordered by natural `clause_id` order — same convention as `policy://catalog`. List MAY be polymorphic (mixed `clause_type`).

**Errors:** `INVALID_LAW_IDENTIFIER` (ver tabela §3). Empty match returns `{clauses: []}`, not error. Examples of error envelopes live in canonical §4.2 and §5; not duplicated here.

**Example — broad search, polymorphic result (Art. 5 governs both vocabulary definition and substantive principles):**

```json
Input:  {"lei": "LGPD", "artigo": 5}
Output: {
  "isError": false,
  "structuredContent": {
    "clauses": [
      {
        "clause_id": "POL-000",
        "clause_type": "definitional",
        "policy_schema_version": "0.1.0",
        "statutory_reference": [{"lei": "LGPD", "artigo": 5}],
        "defines": {"vocabulary_kind": "personal_data_categories", "entries": [{"name": "dados_de_identificacao", "...": "..."}, "..."]},
        "out_of_scope": [{"topic": "origem_racial_ou_etnica", "...": "..."}, "..."]
      },
      {
        "clause_id": "POL-005",
        "clause_type": "substantive",
        "policy_schema_version": "0.1.0",
        "statutory_reference": [{"lei": "LGPD", "artigo": 5}],
        "applies_to": {"personal_data_categories": ["dados_de_identificacao"], "operation": ["collection"]},
        "control": "consent_required",
        "requirements": [{"id": "R1", "text": "..."}],
        "exceptions": []
      }
    ]
  },
  "content": [{"type": "text", "text": "2 cláusulas encontradas para LGPD Art. 5º (1 definitional, 1 substantive)."}]
}
```

**Example — empty result:**

```json
Input:  {"lei": "LGPD", "artigo": 50}
Output: {
  "isError": false,
  "structuredContent": {"clauses": []},
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
| `structured_context.operation` | enum string | yes | Vocabulary in `policy/vocabularies/<framework>/operation.yaml` (resource `policy://vocabularies`, see §4.3) |
| `structured_context.legal_basis` | string | no | Free text; absence = code does not declare basis |
| `structured_context.destination` | string | no | e.g., `external_service`, `internal_database` |

**Output structure (success) — varies by verdict. Trinque de provenance (`policy_schema_version`, `policy_version`, `legal_framework`) trailing every successful return; see §4.2 and canonical §6.4.**

```yaml
# Veredito compliant
{
  verdict: compliant,
  policy_clause_ref: POL-NNN,
  evidence: <texto curto>,
  policy_schema_version: 0.1.0,
  policy_version: <versão>,
  legal_framework: <LGPD | GDPR | ...>
}

# Veredito violation_candidate
{
  verdict: violation_candidate,
  policy_clause_ref: POL-NNN,
  evidence: <texto>,
  contradicted_requirement: R1,   # sub-id do requirement contradito
  policy_schema_version, policy_version, legal_framework
}

# Veredito indeterminate
{
  verdict: indeterminate,
  policy_clause_ref: POL-NNN,
  verification_scope: {
    dimension: <enum: upstream_state | ...>,
    prescribed_treatment: <enum: consent_required | anonymization_required>,   # vocabulário em policy/vocabularies/<framework>/control.yaml (resource policy://vocabularies)
    verification_target: <texto em português>
  },
  policy_schema_version, policy_version, legal_framework
}

# Veredito not_applicable
{
  verdict: not_applicable,
  policy_clause_ref: POL-NNN,
  reason: <texto explicando por que a cláusula não governa>,
  policy_schema_version, policy_version, legal_framework
}
```

**Note:** `evidence` (em `compliant`, `violation_candidate`), `reason` (em `not_applicable`), and `verification_target` (em `indeterminate`) are **generated by the component**, not provided by the caller. Generation mechanism (template, model call, hybrid) is implementation-free.

**Errors:** `INVALID_CLAUSE_ID_FORMAT`, `CLAUSE_NOT_FOUND`, `CLAUSE_DEPRECATED`, `INVALID_DATA_CATEGORY`, `INVALID_OPERATION`, `EMPTY_DATA_CATEGORIES` (ver tabela §3).

**Example — compliant:**

```json
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
  "content": [{"type": "text", "text": "POL-027 compliant: base legal declarada coerente com requirement."}]
}
```

**Example — violation_candidate:**

```json
Input: {
  "clause_id": "POL-031",
  "structured_context": {
    "data_categories": ["dados_de_saude"],
    "operation": "storage",
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
  "content": [{"type": "text", "text": "POL-031 violation_candidate: base legal declarada não está entre as hipóteses do Art. 11."}]
}
```

**Example — indeterminate:**

```json
Input: {
  "clause_id": "POL-027",
  "structured_context": {
    "data_categories": ["dados_de_identificacao"],
    "operation": "disclosure_by_transmission",
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
    "policy_version": "0.1.0",
    "legal_framework": "LGPD"
  },
  "content": [{"type": "text", "text": "POL-027 indeterminate: análise estática não decide; verificar consentimento upstream."}]
}
```

**Example — deprecated error:**

```json
Input: {"clause_id": "POL-014", "structured_context": {...}}
Output: {
  "isError": false,
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

**See canonical §6.4 if:** unsure why the trinque (`policy_schema_version`, `policy_version`, `legal_framework`) is in every `check_applicability` success but not in `get_clause` or `find_clauses_by_law_article`. Provenance temporal e jurisdicional is required when the return is a verdict that will be cited in a Report.

## 6. Initialization

Policy is loaded at server **startup**. File I/O errors during load abort startup (no runtime I/O errors during tool calls). Reload requires restart — hot reload is deferred (ADR-0002).

Vocabulary POL-000 (data categories) read from `policy/SCHEMA.md`; jurisdictional vocabularies (`operation`, `lawful_basis`, `control`, `out_of_scope`) read from `policy/vocabularies/<framework>/*.yaml` at startup, governed by `legal_framework` in the Policy header. No vocabulary hardcoded in the component. Changing `legal_framework` requires a new/cloned Policy + populated `policy/vocabularies/<new_framework>/` + restart; no code change.

**See canonical §6.5 if:** considering hot reload or in-session Policy mutation. Explicitly deferred for MVP.
