# semgrep-runner — compact spec

> **Esta é uma destilação operacional de `canonical.md`, otimizada para consumo por agente de implementação. Em caso de conflito, `canonical.md` prevalece. Escalation pointers inline (`**See canonical §X.Y if:**`) marcam pontos onde abrir a canonical é necessário para decidir corretamente.**

**Spec version:** 0.1.0
**Canonical source:** [canonical.md](./canonical.md)

---

## 1. Identity

**Server name:** `semgrep-runner`
**Function:** MCP server that exposes diff-aware Semgrep execution over a Git diff range. Consumed by the Detector subagent in the code review system.
**Authorized consumer:** Detector subagent, exclusively. Enforced via `mcp_servers` config in Detector's AgentDefinition.

## 2. Wire format

All `CallToolResult` returns use hybrid placement: structured payload in `structuredContent`, human-readable prose in `content[0].text`. See ADR-0002 §1. Error envelope shape — see §3 below.

## 3. Error contract

Two error classes are non-empty in this component — **business** and **system**. Validation class is intentionally empty (positive declaration per ADR-0002 Decision 4): `base_ref` and `head_ref` are validated as non-empty strings by the FastMCP runtime via `inputSchema` before reaching component code. **See canonical §5 if:** implementing input validation beyond FastMCP runtime checks.

Empty `findings` list is **not an error** — returns wire `isError: false` with `{scan_metadata, findings: []}` in `structuredContent`. Wire format follows Option B per ADR-0002 §3 amendment 2026-05-17: wire `isError: false` on all returns from this component; discrimination by presence of `errorCode` in `structuredContent`. **See canonical §4.2 if:** unsure why wire `isError: true` is not used for domain-class errors.

| `errorCode` | Class | Retryable | Emitting tool | Condition | `details` shape |
|---|---|---|---|---|---|
| `GIT_REF_NOT_FOUND` | business | false | `scan_diff` | `base_ref` or `head_ref` is syntactically valid but does not exist in the current repo | `{ref_param, ref_value, hint}` |
| `INSUFFICIENT_GIT_HISTORY` | business | false | `scan_diff` | Shallow clone prevents Semgrep from resolving merge-base between refs for diff-aware scan | `{hint: "increase actions/checkout fetch-depth"}` |
| `SCAN_TIMEOUT` | system | true | `scan_diff` | Scan exceeded `SEMGREP_RUNNER_TIMEOUT_SECONDS` (default 300s); subprocess terminated with SIGKILL after grace period | `{timeout_seconds, elapsed_seconds, partial_findings_discarded: true}` |
| `SEMGREP_BINARY_UNAVAILABLE` | system | false | `scan_diff` | Binary `semgrep` not on PATH at tool invocation time (per-call check, canonical §8.6) | `{searched_paths}` |
| `SEMGREP_EXECUTION_FAILED` | system | true | `scan_diff` | Semgrep terminated with fatal exit code (2) without categorized cause | `{exit_code, stderr_excerpt}` |
| `INVALID_RULE_SET` | system | false | `scan_diff` | Project-curated rules have syntactic bug (Semgrep exit 4 or 5) | `{exit_code, stderr_excerpt}` |

**Error payload shape (all errorCodes):**

```yaml
{
  errorCode: <string>,    # MAIÚSCULAS_SNAKE, English, stable
  message: <string>,      # Portuguese, human-readable
  isRetryable: <boolean>,
  details: <object>       # shape per errorCode (see table)
}
```

The envelope ships inside `structuredContent` with wire `isError: false` per Option B (canonical §4.2; ADR-0002 §3 amendment 2026-05-17). Binary discovery is NOT a startup concern — `SEMGREP_BINARY_UNAVAILABLE` is emitted per-call at tool invocation (canonical §8.6; ADR-0010).

## 4. Resources

`semgrep-runner` **does not expose resources**.

The Semgrep rule set is server-internal input, not consumer-navigable content. The Detector consumes findings produced by `scan_diff` (§5); it does not enumerate, read, or reason over rule content before scan invocation.

Principle applied: Resource vs Tool — discriminação pela leitura cognitiva. The asymmetry vs `policy-reader` (which exposes two resources) is deliberate and is the case-test for the principle.

## 5. Tools

One tool. Naming convention: `mcp__semgrep-runner__scan_diff` (runtime-generated).

### 5.1 `scan_diff`

**Description (English, no markdown, this is the actual tool description seen by the model):**

Scans the Git diff between base_ref and head_ref using the project's curated Semgrep rule set, returning findings that match any rule in the set. Use this when the caller has the BASE and HEAD refs of a pull request and needs to identify candidate sites for downstream classification. The rule set is server-side curated and not callable-parameterizable; it is fixed at server build time. The MVP rule set covers Brazilian personal data identifiers (CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde), but the component itself is domain-agnostic — rule set substitution is the supported path for different jurisdictions or detection domains.

Findings are single-file: the MVP does not perform cross-file taint analysis. Each finding carries rule provenance (rule_id), location (file path, line range), and code snippet. Empty findings list is a valid success outcome — the diff was scanned and no rules matched.

Returns success with findings list (possibly empty) on completion. Returns business error if Git refs are unresolvable, system error if the scan times out or the Semgrep binary fails. Operation is synchronous and may take seconds to minutes depending on diff size.

**Note:** `scan_diff` does not accept `rule_set` as a parameter. For potential future modes (e.g., fast vs full scan), the canonical response is tool split, not parametrization of `scan_diff`.

**`inputSchema`:**

| Field | Type | Required | Description |
|---|---|---|---|
| `base_ref` | string | yes | Git ref (commit hash, branch name, tag) for the diff baseline |
| `head_ref` | string | yes | Git ref for the diff head |

**Output structure (success):**

```yaml
{
  rules_version: <string>,         # top-level static provenance (hash of rule set, see §6)
  semgrep_version: <string>,       # top-level static provenance (version of Semgrep CLI invoked)
  scan_metadata: {                 # dynamic per-scan
    base_ref: <string>,            # 40-char hex commit hash, resolved from input
    head_ref: <string>,            # 40-char hex commit hash, resolved from input
    files_scanned: <int>,          # count of distinct files touched in diff
    elapsed_seconds: <float>       # scan elapsed time
  },
  findings: [
    {
      rule_id: <string>,           # Semgrep rule identifier
      rule_severity: <enum>,       # info | warning | error — lowercase normalized from Semgrep uppercase
      rule_message: <string>,      # rule's message field
      location: {
        path: <string>,            # repo-relative
        start_line: <int>,         # 1-indexed
        start_col: <int>,          # 1-indexed
        end_line: <int>,           # 1-indexed
        end_col: <int>             # 1-indexed
      },
      snippet: <string>            # excerpt at finding location
    },
    ...
  ]
}
```

**Findings list semantics:** ordered by `(location.path, location.start_line)` ascending. Order is stable across invocations under the same input. Empty list (`findings: []`) is a valid success — means Semgrep ran successfully and found no matches in the diff. This is **not** an error.

**Errors:** `GIT_REF_NOT_FOUND`, `INSUFFICIENT_GIT_HISTORY`, `SCAN_TIMEOUT`, `SEMGREP_BINARY_UNAVAILABLE`, `SEMGREP_EXECUTION_FAILED`, `INVALID_RULE_SET` (see table §3).

**Example — caso normal, two findings:**

```json
Input: {"base_ref": "main", "head_ref": "feature/user-export"}
Output: {
  "isError": false,
  "structuredContent": {
    "rules_version": "rules-2026-04-1a7f3b",
    "semgrep_version": "1.62.0",
    "scan_metadata": {
      "base_ref": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
      "head_ref": "f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1",
      "files_scanned": 3,
      "elapsed_seconds": 4.21
    },
    "findings": [
      {
        "rule_id": "python.lang.security.audit.weak-hash.weak-hash",
        "rule_severity": "warning",
        "rule_message": "Use of MD5 is insecure for hashing passwords.",
        "location": {
          "path": "src/users/export.py",
          "start_line": 42,
          "start_col": 5,
          "end_line": 42,
          "end_col": 60
        },
        "snippet": "    return hashlib.md5(password.encode()).hexdigest()"
      },
      {
        "rule_id": "python.flask.security.audit.no-csrf-protection",
        "rule_severity": "error",
        "rule_message": "Endpoint missing CSRF protection.",
        "location": {
          "path": "src/users/export.py",
          "start_line": 87,
          "start_col": 1,
          "end_line": 95,
          "end_col": 24
        },
        "snippet": "@app.route('/export', methods=['POST'])\ndef export_users():..."
      }
    ]
  },
  "content": [{"type": "text", "text": "scan_diff: 2 findings em 3 arquivos (4.21s)."}]
}
```

Note: the example above uses Semgrep Registry rule IDs (`python.lang.security.audit.*`) for didactic value. The project MVP rule set carries rules with IDs in `br-cpf`, `br-cnpj`, etc. pattern (see T07).

**Example — empty result (no findings, success):**

```json
Input: {"base_ref": "main", "head_ref": "feature/docs-only"}
Output: {
  "isError": false,
  "structuredContent": {
    "rules_version": "rules-2026-04-1a7f3b",
    "semgrep_version": "1.62.0",
    "scan_metadata": {
      "base_ref": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
      "head_ref": "0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f",
      "files_scanned": 2,
      "elapsed_seconds": 1.87
    },
    "findings": []
  },
  "content": [{"type": "text", "text": "scan_diff: nenhum finding em 2 arquivos (1.87s)."}]
}
```

**Example — SCAN_TIMEOUT (system error, retryable):**

```json
Input: {"base_ref": "main", "head_ref": "feature/large-refactor"}
Output: {
  "isError": false,
  "structuredContent": {
    "errorCode": "SCAN_TIMEOUT",
    "message": "Scan excedeu o limite de 300 segundos. Subprocess Semgrep terminado após grace period.",
    "isRetryable": true,
    "details": {
      "timeout_seconds": 300,
      "elapsed_seconds": 312.4,
      "partial_findings_discarded": true
    }
  },
  "content": [{"type": "text", "text": "Scan excedeu o limite de 300 segundos. Subprocess Semgrep terminado após grace period."}]
}
```

**Semantic note on timeout retryability.** `isRetryable: true` for `SCAN_TIMEOUT` indicates the transient nature of timeout per the system-class default of ADR-0002 Decision 3 — a retry under unchanged input within the same timeout budget may succeed if the underlying cause was intermittent (kernel scheduler jitter, disk cache state, transient I/O contention). It does NOT indicate that callers should expect partial findings on retry: `partial_findings_discarded: true` is always set when `SCAN_TIMEOUT` fires (all-or-nothing semantics). Caller-side retry strategy may also legitimately split the diff to reduce per-scan duration below the timeout budget, which is the caller's responsibility, not the component's.

**See canonical §5 if:** unsure how the six `errorCode` values map to classes (business vs system) and retryability — the table in §5 is authoritative. **See canonical §7 if:** unsure why partial findings are never returned even when the timeout could in principle yield a partial scan (the all-or-nothing rationale lives there).

## 6. Initialization

At server startup:
- Curated rule set loaded from project-bundled directory `mcp_servers/semgrep_runner/rules/`; `rules_version` computed as deterministic hash of directory contents and held for the session lifetime.
- `SEMGREP_RUNNER_TIMEOUT_SECONDS` read from environment (default: 300s).

The Semgrep CLI binary is **NOT** discovered at startup. Binary availability is checked per-call at tool invocation time (canonical §8.6; ADR-0010); a missing binary surfaces as the `SEMGREP_BINARY_UNAVAILABLE` errorCode (system class, non-retryable) rather than aborting the server. Rationale: runtime resilience in CI environments where the binary may be installed asynchronously to server startup, plus auditability — a per-call failure mode is observable as a structured error in the agent loop rather than as a silent server crash. Version pinning is enforced via README + `uv tool install` per ADR-0010, not via runtime check.

No `policy/SCHEMA.md`-equivalent vocabulary load — `semgrep-runner` has no external schema artifact. Rule content is the artifact, and is server-internal (see §4).

**Per-client rule set.** MVP loads a single project-bundled rule set with Brazilian recognizers as pilot. Per-client rule set — separate directories governed by client identity, analogous to how `policy-reader` is per-client via Policy swap under `policy/` (ADR-0005 Decision 1) — is deferred to a future ADR, when the first non-LGPD-Brazilian client materializes. See canonical §2.1 and §7.
