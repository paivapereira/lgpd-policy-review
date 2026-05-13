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

Three error classes (see ADR-0002 §3 for class semantics). Empty `findings` list is **not an error** — returns `isError: false`.

| `errorCode` | Class | Retryable | Emitting tool | Condition | `details` shape |
|---|---|---|---|---|---|
| `INVALID_BASE_REF` | validation | false | `scan_diff` | `base_ref` cannot be resolved to a commit by the host repo | `{provided, error}` |
| `INVALID_HEAD_REF` | validation | false | `scan_diff` | `head_ref` cannot be resolved to a commit by the host repo | `{provided, error}` |
| `SCAN_TIMEOUT` | system | false | `scan_diff` | Scan exceeded `SEMGREP_RUNNER_TIMEOUT_SECONDS` (default 300s) | `{timeout_seconds, partial_findings_discarded: true, files_scanned_before_timeout}` |
| `SEMGREP_EXECUTION_FAILED` | system | false | `scan_diff` | Semgrep CLI returned non-zero exit code other than findings-found, or produced unparseable output | `{exit_code, stderr_excerpt, files_attempted}` |

**Empty error class declaration:** the system error class is intentionally narrow. Binary discovery failures (`semgrep` not in PATH, version below minimum) are caught at server **startup**, not at request runtime — server fails to start. See canonical §6 if implementing alternative discovery paths.

**Error payload shape (all errorCodes):**

```yaml
{
  errorCode: <string>,    # MAIÚSCULAS_SNAKE, English, stable
  message: <string>,      # Portuguese, human-readable
  isRetryable: <boolean>,
  details: <object>       # shape per errorCode (see table)
}
```

## 4. Resources

`semgrep-runner` **does not expose resources**.

The Semgrep rule set is server-internal input, not consumer-navigable content. The Detector consumes findings produced by `scan_diff` (§5); it does not enumerate, read, or reason over rule content before scan invocation.

Principle applied: `_drafts/spec-authoring-principles.md` § Resource vs Tool — discriminação pela leitura cognitiva. The asymmetry vs `policy-reader` (which exposes two resources) is deliberate and is the case-test for the principle.

## 5. Tools

One tool. Naming convention: `mcp__semgrep-runner__scan_diff` (runtime-generated).

### 5.1 `scan_diff`

**Description (English, no markdown, this is the actual tool description seen by the model):**

> Run Semgrep over the Git diff between `base_ref` and `head_ref` of the current repository, using the project-curated rule set. Returns the list of findings emitted by Semgrep for files touched in the diff. Use this when the caller needs to identify static-analysis candidates in a code change before downstream classification by the Matcher.
>
> The rule set is fixed at server build time and is not callable-parameterizable. Findings are single-file: the MVP does not perform cross-file taint analysis. Static analysis identifies candidates for downstream verification — it does not produce compliance verdicts.
>
> Returns success with a list of findings (possibly empty) on completion. Returns business/validation error if refs are unresolvable, system error if the scan times out or the Semgrep binary fails.

**Note:** `scan_diff` does not accept `rule_set` as a parameter. For potential future modes (e.g., fast vs full scan), see `_drafts/spec-authoring-principles.md` § Split de tool, não parametrização condicional — the canonical response is tool split, not parameter.

**`inputSchema`:**

| Field | Type | Required | Description |
|---|---|---|---|
| `base_ref` | string | yes | Git ref (commit hash, branch name, tag) for the diff baseline |
| `head_ref` | string | yes | Git ref for the diff head |

**Output structure (success):**

```yaml
{
  rules_version: <string>,         # hash or semver of the curated rule set (see §6)
  semgrep_version: <string>,       # version of the Semgrep CLI invoked
  scan_metadata: {
    base_ref: <string>,            # 40-char hex commit hash, resolved from input
    head_ref: <string>,            # 40-char hex commit hash, resolved from input
    files_scanned: <int>,          # count of distinct files touched in diff
    duration_seconds: <float>
  },
  findings: [
    {
      rule_id: <string>,           # Semgrep rule identifier
      severity: <enum: ERROR | WARNING | INFO>,
      file_path: <string>,         # repo-relative
      line_start: <int>,
      line_end: <int>,
      message: <string>,           # rule's message field
      code_snippet: <string>       # excerpt at finding location
    },
    ...
  ]
}
```

**Findings list semantics:** ordered by `(file_path, line_start)` ascending. Empty list (`findings: []`) is a valid success — means Semgrep ran successfully and found no matches in the diff. This is **not** an error.

**Errors:** `INVALID_BASE_REF`, `INVALID_HEAD_REF`, `SCAN_TIMEOUT`, `SEMGREP_EXECUTION_FAILED` (see table §3).

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
      "duration_seconds": 4.21
    },
    "findings": [
      {
        "rule_id": "python.lang.security.audit.weak-hash.weak-hash",
        "severity": "WARNING",
        "file_path": "src/users/export.py",
        "line_start": 42,
        "line_end": 42,
        "message": "Use of MD5 is insecure for hashing passwords.",
        "code_snippet": "    return hashlib.md5(password.encode()).hexdigest()"
      },
      {
        "rule_id": "python.flask.security.audit.no-csrf-protection",
        "severity": "ERROR",
        "file_path": "src/users/export.py",
        "line_start": 87,
        "line_end": 95,
        "message": "Endpoint missing CSRF protection.",
        "code_snippet": "@app.route('/export', methods=['POST'])\ndef export_users():..."
      }
    ]
  },
  "content": [{"type": "text", "text": "scan_diff: 2 findings em 3 arquivos (4.21s)."}]
}
```

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
      "duration_seconds": 1.87
    },
    "findings": []
  },
  "content": [{"type": "text", "text": "scan_diff: nenhum finding em 2 arquivos (1.87s)."}]
}
```

**Example — timeout (system error, partial discarded):**

```json
Input: {"base_ref": "main", "head_ref": "feature/large-refactor"}
Output: {
  "isError": true,
  "structuredContent": {
    "errorCode": "SCAN_TIMEOUT",
    "message": "Scan excedeu 300s. Findings parciais descartados — semântica all-or-nothing.",
    "isRetryable": false,
    "details": {
      "timeout_seconds": 300,
      "partial_findings_discarded": true,
      "files_scanned_before_timeout": 47
    }
  },
  "content": [{"type": "text", "text": "scan_diff timeout em 300s; 47 arquivos parcialmente escaneados, descartados."}]
}
```

**Semantic note on timeout:** `partial_findings_discarded: true` is always set when `SCAN_TIMEOUT` fires. The component **does not** return partial findings — all-or-nothing semantics. Caller cannot retry with same input expecting partial; retry would require splitting the diff (caller's responsibility).

**See canonical §5.3 if:** unsure why `SCAN_TIMEOUT` is non-retryable. The reasoning chain involves all-or-nothing semantics + assumption that timeout configuration is stable.

**See canonical §5.4 if:** unsure how `SEMGREP_EXECUTION_FAILED` distinguishes from `SCAN_TIMEOUT`. Both are system errors; the distinction matters for caller-side telemetry.

## 6. Initialization

At server startup:
- Semgrep CLI binary discovered in PATH; version checked against minimum (see ADR-0001). Failure: server fails to start.
- Curated rule set loaded from project-bundled directory; `rules_version` computed and held for the session lifetime.
- `SEMGREP_RUNNER_TIMEOUT_SECONDS` read from environment (default: 300).

No `policy/SCHEMA.md`-equivalent vocabulary load — `semgrep-runner` has no external schema artifact. Rule content is the artifact, and is server-internal (see §4).

**See canonical §6 if:** considering alternative binary discovery paths or rule set hot-reload. Both are explicit deferrals for the MVP.
