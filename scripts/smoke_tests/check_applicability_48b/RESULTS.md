# Smoke-test #48-b — RESULTS

Persisted evidence for the resource-tool visibility gate (matcher.md DD-M30;
classifier.md §10.3 "Gate resource access"; coordinator.md §10 DD-9.1).

## H2 — `ReadMcpResourceTool` visibility by `tools` config

**Question.** Is the built-in `ReadMcpResourceTool` visible to the model under
each `tools` field configuration, with the real `policy-reader` registered in
`mcp_servers` and `ReadMcpResourceTool`/`ListMcpResourcesTool` present in
`allowed_tools`?

**Setup.** Real `policy-reader` over stdio (`uv run python -m
mcp_servers.policy_reader.server`). `allowed_tools` always includes the two
resource built-ins; only the `tools` field varies. Observable = did the model
emit a `ReadMcpResourceTool` ToolUseBlock and obtain catalog content, or
verbalize that the tool is unavailable.

**Command (reproducible).**

    uv run --with claude-agent-sdk==0.2.87 python scripts/smoke_tests/check_applicability_48b/h2_probe.py

SDK: `claude-agent-sdk==0.2.87`. Auth: Claude Code CLI.

**Result.**

| config | `tools` | read catalog? | attempts | verbalizes absence | turns |
|---|---|---|---|---|---|
| H2-empty | `[]` | **NO** | 0 | yes | 1 |
| H2-read | `["Read"]` | **NO** | 0 | yes | 1 |
| H2-listed | `["Read", "ReadMcpResourceTool", "ListMcpResourcesTool"]` | **YES** | 1 | no | 2 |
| H2-omitted | (omitted) | **YES** (via `ToolSearch`) | 1 | no | 3 |

Verbatim under `tools=["Read"]`: *"I cannot call ReadMcpResourceTool — it is
unavailable in this environment. The only tools exposed to me are `Read`,
`mcp__policy-reader__check_applicability`,
`mcp__policy-reader__find_clauses_by_law_article`, and
`mcp__policy-reader__get_clause`."*

## Verdict — PASS

Two orthogonal axes, confirmed empirically:

- **Server tools** (`mcp__policy-reader__*`) are governed by `mcp_servers` and
  **survive `tools=[]`** (listed as available under both NO-READ configs).
- **Resource built-ins** (`ReadMcpResourceTool`/`ListMcpResourcesTool`) are
  governed by the **`tools` field** and **disappear** unless listed there —
  `allowed_tools` membership is not sufficient (Issue #361: `allowed_tools`
  does not control availability).

**Consequence (applied to the specs).** Any subagent that reads a resource via
`ReadMcpResourceTool` under a non-empty `tools` field must list the two resource
built-ins:

- **Matcher** (coordinator.md §3.4) — `tools=["Read", "ReadMcpResourceTool",
  "ListMcpResourcesTool"]`. The check-all reads `policy://catalog`; `tools=[]`
  (PR #67 Gate 6) breaks it. Gate 6's `tools=[]` is correct only for the
  Reporter (`emit_report` is a server tool).
- **Classifier** (coordinator.md §3.3) — `tools=["Read", "Grep",
  "ReadMcpResourceTool", "ListMcpResourcesTool"]`. Reads `policy://vocabularies`
  at startup. The extra `Grep` is a base built-in, orthogonal to resource-tool
  visibility (H2-listed differs only by `Grep`, which does not affect the
  result).

The `tools=[]` "sem conflito" claim previously in classifier.md:45 was an
empirical defect, now corrected.

## Companion probe (C2 / H1)

`probe.py` (pure in-process, no SDK/auth) covers:
- **C2** — `check_applicability` returns `EMPTY_DATA_CATEGORIES` for
  `data_categories: []` and `INVALID_OPERATION` for `operation: null`/absent
  (the two valid Classifier edge outputs the Matcher short-circuits — matcher.md §4.4).
- **H1** — the loader boots the synthetic-GDPR fixture without a jurisdictional
  gate (no server-side `legal_framework` abort), confirming the jurisdictional
  handshake is dropped-by-YAGNI in the co-versioned MVP (matcher.md DD-M22).
