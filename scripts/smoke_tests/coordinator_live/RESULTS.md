# RESULTS — coordinator_live (Milestone C live composition gates)

Live `query()` probes of the coordinator composition against the real
`claude-agent-sdk==0.2.87`, Windows 11 / PS 5.1, authenticated Claude Code
session. Per `gates.md`: the gate's existence + outcome is the persisted
evidence (the run itself is not reproducible-deterministic — it is an LLM).
The hermetic, replayable assertions live in the mock-SDK pytest suite
(`tests/coordinator/`); these probes confirm the *composition* the mock cannot.

---

## GATE G1 — walking-skeleton composition (Phase 1) — PASS (skip path)

**Probe:** `g1_skip_path_live.py`. The un-de-risked thing (session-handoff §5)
is the composition of `query() + output_format + driver capture loop + the
in-process reporter factory + emit_report dispatch + dual-sink capture +
CoordinatorResult`. The skip path exercises ALL of it except the
MCP-server-consuming middle (Detector/Classifier/Matcher) — so it needs neither
the semgrep binary nor a connected policy-reader.

**Empirical question:** does the real driver + config + factory +
`CoordinatorResult` derivation compose into a green round-trip live (stub
prompts, real SDK)?

**Result (run 2026-05-31):**

| Observable | Value |
|---|---|
| return type | `CoordinatorReport` |
| `run_outcome` | `skipped_by_triager` |
| Triager (live, output_format) | emitted valid `TriagerDecision` (skip + reason) |
| `99-report.json` written by handler (dual-sink #1) | **True** |
| payload captured via `ToolUseBlock.input` (dual-sink #2) | **True** |
| `scan_provenance` in payload | **absent** (correct for skip path) |
| logging | structured to **stderr**; stdout clean (§3.0) |

**Verdict: PASS** — the real `create_sdk_mcp_server` factory + `emit_report`
tool dispatch + closure-captured atomic write + the §3.5 capture loop +
`derive_run_outcome`/summary + the §3.6 `CoordinatorResult` envelope all compose
live. No `permission_denials`. The empirical SDK behaviors pinned in
`sdk_l2_capture/RESULTS.md` held under composition.

**Deferred to G2b (proceed path):** the full Triager→Detector→Classifier→Matcher
→Reporter live run requires real `policy-reader` + `semgrep-runner` connections
and the semgrep binary (ADR-0010). It belongs to Phase 2b, when those stages have
real prompts/tools. The skip-path arm is the correct Phase-1 scope — it confirms
the novel composition piece (the in-process reporter factory live) without the
MCP middle that Phase 2b authors.

---

## GATE G2a — close the ends: Triager + Reporter (Phase 2a) — PASS

**Probe:** `g2a_ends_live.py`. Three ISOLATED live arms against the real
`claude-agent-sdk==0.2.87` (Windows 11 / PS 5.1, authenticated session) — NO
semgrep, NO MCP middle (that is G2b). The hermetic, replayable cross-check
assertions live in `tests/subagents/reporter/test_emit_report.py` +
`tests/coordinator/test_triager_stage.py` + `test_reporter_stage.py` (97 green);
this probe confirms the *composition* the mock cannot: the §5.1 Triager prompt
under `system_prompt=None` (DD-4) emitting valid decisions live, and emit_report
round-tripping through the real in-process `reporter_tools` server. Arms are
isolated at the stage (driver / `_run_reporter_stage`), NOT `run_pipeline` — a
live proceed must NOT fall through to the Detector (semgrep = G2b).

**Empirical questions:** (1) does the rendered §5.1 Triager prompt under SDK
minimal system-prompt mode (DD-4) emit a valid `TriagerDecision` live for both a
proceed-signalling and a skip-signalling worktree? (2) does emit_report round-trip
live through the real server with the four §4.8 cross-checks executing (all pass
on a valid payload) + the atomic write + `ToolUseBlock.input` capture?

**Result (run 2026-05-31):**

| Arm | Observable | Value |
|---|---|---|
| A — Triager proceed | `decision` | `proceed` (valid `TriagerDecision`, output_format) |
| A | `relevance_summary` | concrete pt — cites `src/app/registration.py` + CPF/email |
| B — Triager skip | `decision` | `skip` (valid `TriagerDecision`) |
| B | `skip_reason` | concrete pt — cites `docs/` only, no app code |
| C — Reporter | payload captured verbatim (no recompute) | **True** |
| C | `99-report.json` written (dual-sink #1) | **True** |
| C | `report_id` round-trips (closure cross-check #4 passed) | **True** |

**Verdict: PASS** — the rendered §5.1 prompt + `system_prompt=None` (DD-4) produces
valid proceed AND skip decisions live (the wiring the hermetic suite cannot prove);
emit_report round-trips live through the real in-process server with the §4.8
cross-checks executing and the DD-2 content-channel envelope in place. The
cross-check NEGATIVE cases (each errorCode firing + the DD-2 channel) are pinned
hermetically by the 7 `test_emit_report_*` anchors; the §9.2 tri-axial / anti-pattern
branches by `test_reporter_stage.py`.

**Note (Phase-3 debt, surfaced this session):** a live *invalid*-payload Reporter
run would expose the §3.5 ↔ §6.7/§9.2.a retry contradiction (the coordinator flips
`emit_report_seen` on EVERY emit_report block, so the model's retry-after-error path
would raise `MultipleReportEmissions` and capture the *rejected* payload). NOT
exercised here by design — reconciling §3.5 with the retry semantics (correlate
`ToolUseBlock`↔`ToolResultBlock.is_error`; count/capture only SUCCESSFUL emits) is
deferred to Phase 3 (ADR pending) and registered in `docs/tasks.md`.

**Deferred to G2b (proceed path):** the full Triager→Detector→Classifier→Matcher→
Reporter live run requires real `policy-reader` + `semgrep-runner` + the semgrep
binary (ADR-0010) — Phase 2b.

---

## GATE G2b — MCP middle: Detector + Classifier + Matcher (Phase 2b) — PARTIALLY-GATED

Outcome (per `gates.md` — the gate's existence + outcome IS the persisted evidence):
**deterministic tool-boundary arms PASS; the agent-loop arm is BLOCKED by a pre-existing
driver-layer (MC-A) MCP-readiness gap that this gate EXPOSED.** Two layers:

- **Deterministic tool-boundary arms** — MCP Inspector CLI (`mcp-testing.md`), reproducible,
  NO LLM. Confirm the server contracts the JSON handoff depends on.
- **Agent-loop composition arm** — `g2b_mcp_middle_live.py`, real SDK. RAN and EXPOSED the
  readiness gap (below). The hermetic, replayable assertions live in `tests/coordinator/` +
  `tests/subagents/` (127 green: prior 97 + 30 Phase-2b incl. the Bug-2 anchor).

**Empirical question (G2b):** do the projection renames, the Classifier passthrough zip, the
Detector scan-diff error inspection, and the Matcher short-circuit/curto-circuito behave
correctly across the JSON handoff — and does the `{"output"}` wrapper stay quiet on real
`DetectorOutput`/`MatcherOutput`?

### Deterministic arms (Inspector CLI `--config .mcp.json`) — PASS (run 2026-05-31)

| Arm | Observable (verbatim) | Result |
|---|---|---|
| `scan_diff` Option-B error (`--server semgrep-runner ... --tool-name scan_diff --tool-arg base_ref=nonexistent-ref-aaaa --tool-arg head_ref=HEAD`) | `isError:false` + `structuredContent={errorCode:"GIT_REF_NOT_FOUND", isRetryable:false, details:{ref_param,...}}` | **PASS** — the exact nested shape the Detector hook reads (DD-d); `isRetryable:false` matches canonical §5.4 |
| `policy://vocabularies` (`--server policy-reader --method resources/read --uri policy://vocabularies`) | top-level JSON object keyed `operation`/`lawful_basis`/`control`/`out_of_scope`, each `{schema_version, framework, values[]}` | **PASS** — Classifier resource-load reachable |
| `check_applicability` projection (`--tool-name check_applicability --tool-arg clause_id=POL-000 --tool-arg 'structured_context={"data_categories":["dados_de_documentos_oficiais"],"operation":"collection","legal_basis":"consent"}'`) | accepts the projected `{data_categories, operation, legal_basis}` structured_context; returns `structuredContent={verdict:"not_applicable", policy_clause_ref:"POL-000", policy_schema_version, policy_version, legal_framework}`, `isError:false`, **NO `{"output"}` wrapper** | **PASS** — projection contract + verdict envelope (incl. the per-finding trinca) |

Note: `check_applicability` with a non-canonical `data_categories` token (`"cpf"`) returns
Option-B `errorCode:"INVALID_DATA_CATEGORY"` — confirming the Matcher's fail-loud path for a
genuinely out-of-vocab value (matcher §6.2), distinct from the `is None`/`[]` short-circuit.

**DD-d nested `structuredContent` (open assumption) — RESOLVED.** The server emits the error
payload under `structuredContent` (verbatim above); `claude-agent-sdk==0.2.87` relays
`data["tool_use_result"]` verbatim from the CLI wire (`_internal/message_parser.py:83`) into
`UserMessage.tool_use_result`. So the hook's discriminator
(`tool_use_result["structuredContent"]["errorCode"]`) is sound; the defensive `or {}` guards
make any CLI-relay surprise non-fatal regardless.

**`{"output"}` wrapper — see the agent-loop section below.** It is **NOT** closed by G0; the
honest status is "not observed on the real list-shaped `DetectorOutput`" (gated with the race).

### Agent-loop arm (`g2b_mcp_middle_live.py`, real SDK) — BLOCKED by a driver readiness gap

ARM D was run live (Detector on a synthetic-CPF git repo + real semgrep). **It did NOT scan.**
Observed (instrumented; init `SystemMessage`):
`mcp_servers: [{'name':'semgrep-runner','status':'pending'}]`, `tools: ['Read','StructuredOutput']`
— `scan_diff` **never registered**. The model emitted on turn 1 (`tool_use_result` = `None`,
then the str `'Structured output provided successfully'` — the SDK structured-output ack, the
same shared-channel value that caused Bug-2) before the server connected → `findings=[]`.

**Root cause — cold-start race (observed, not inferred; three sub-causes triaged):**
- **NOT** a FastMCP-banner-on-stdout corruption (sub-cause B): probed the server with a real
  `initialize` — STDOUT is pure JSON-RPC, the banner is on STDERR — across `uv run`,
  `uv run --project` (foreign cwd), AND venv-direct. **NOT** a `uv`-stdout issue (sub-cause C):
  stdout clean via the exact agent-loop command.
- **IS** a readiness race (sub-cause A): the server handshakes cleanly but takes **~3.5 s
  intrinsic** (uv 3.3 s ≈ venv-direct 3.6 s → FastMCP boot + imports + rules load, NOT uv —
  so a faster launch can't win it), and the one-shot **`query()` path has no MCP
  readiness-wait** (readiness/recovery — `get_mcp_status` / `reconnect_mcp_server` — exist
  ONLY on the streaming `ClaudeSDKClient`, client.py:405/474).

**Real in production, not a test artifact** (read from `run.py`): `run_pipeline` issues **5
independent one-shot `query()` calls**, one per stage, each spawning ONLY its own
`mcp_servers` — Triager `{}` (run.py:155), Detector `{semgrep-runner}` (167), Classifier/
Matcher `{policy-reader}` (179/197), Reporter `{reporter_tools}` (209). The Triager declares
no servers, so semgrep-runner is first/only spawned by the **Detector's own `query()`** —
always cold. The CI coordinator races identically. (The "warm during Triager" hypothesis is
refuted: the Triager has `mcp_servers={}`.)

**`--project` note:** the probe launches semgrep-runner via `uv run --project <ABS>` + an
`os.chdir` into the synthetic repo. This is a **foreign-cwd robustness aid** (uv resolves the
env from the project while the server's cwd = the scanned repo; verified) — it is **NOT** the
race fix. The race is **OPEN / deferred**, not mitigated by `--project`.

**`{"output"}` wrapper — NOT OBSERVED (gated with the race).** G0 proved the wrapper quiet on
the **Matcher** `Finding` enum-tag schema — but `DetectorOutput` has `findings: [...]` (a
**top-level list**, exactly the shape that historically triggers the #502/#571 wrapper).
Because the race prevented any scan, the Detector **never produced a populated `DetectorOutput`
in the agent-loop**, so the wrapper was NOT observed on the real list-shaped output. To verify
when the readiness fix lets the scan run; remains a possible fail-action of the reliability PR
— **NOT** closed by G0.

### Verdict: PARTIALLY-GATED

- **PASS (in scope):** the three tool-boundary contracts (verbatim above); DD-d resolved;
  hermetic gate green (127); ruff + mypy --strict clean; Bug-2 (the `tool_use_result`
  shared-channel non-dict crash) fixed (`a3da204`) and validated live (the run completed
  instead of crashing). **Learning:** `tool_use_result` is a SHARED channel — it carries SDK
  structured-output acks (`'Structured output provided successfully'`) as well as MCP tool
  envelopes; `isinstance(dict)` is the correct discriminator (a non-dict is never an Option-B
  envelope).
- **BLOCKED (out of scope — exposed, deferred):** the agent-loop scan + the `{"output"}`
  observation, by a **driver-layer (MC-A) MCP-readiness gap**. Architecturally distinct from
  Phase-2b's prompt/hook/passthrough flesh; fixing it (move MCP-consuming stages to a
  `ClaudeSDKClient` readiness-wait) touches the driver transport, all 5 stages, and the
  conftest mocks — a **separate reliability PR**.
- **Fase-3 debt — UNIFIED under ONE ADR:** "MCP connection lifecycle & resilience in the
  driver" covers BOTH halves of one apparatus — **readiness** (wait for `'connected'` before
  acting; this race) and **recovery** (retry `SCAN_TIMEOUT`/`SEMGREP_EXECUTION_FAILED`; the
  DD-d retry-loop). Both need `get_mcp_status`/`reconnect` via `ClaudeSDKClient`; both are
  driver-layer. Registered in project memory `mc-c-phase2b-deferred-debts`.

---

## GATE D1 — readiness verification + mock-fidelity (Phase 3, ADR-0014) — PASS

The **first technical action of Phase 3** (session-handoff §2 step 1): a SMOKE gate
(not a hermetic test — an LLM is non-deterministic; per `gates.md` the persisted
evidence is the gate's existence + outcome here). It validates — by **observation, not
inference** — the causal assumption ADR-0014 D1 rests on, **before** any migration code.
Two probes, both against the real `claude-agent-sdk==0.2.87`, Windows 11 / PS 5.1,
authenticated session, semgrep 1.163.0 (ADR-0010). Run 2026-06-01.

### Probe 1 — mock-fidelity smoke (`d1_mock_fidelity_smoke.py`, NO LLM)

`.claude/rules/verification-before-inference.md` / handoff §6: observe the REAL
`ClaudeSDKClient` MCP-control surface so the Phase-3 conftest mock (ADR-0014 D5) mirrors
the wire shape, not the type signature (a mock that lies + a green test is worse than a
red one — the `tool_use_result` nested-shape bit the 2b saga the same way).

| Surface | Observed (verbatim) |
|---|---|
| `get_mcp_status()` return | `dict`, single top key `mcpServers` → nested `{"mcpServers":[...]}` (confirms the §6-flagged shape) |
| entry while `pending` | `{'name':'semgrep-runner','status':'pending','config':{...},'scope':'dynamic'}` — **no** `tools`/`serverInfo` |
| entry while `connected` | adds `'serverInfo':{'name':'semgrep-runner','version':'3.2.4'}` + `'tools':[{'name':'scan_diff','annotations':{}}]` |
| `reconnect_mcp_server(name)` return | `None` (NoneType); raises on failure; post-call status `connected` |
| cold-start (calibration, Deferral A) | `pending` polls 0–6, `connected` poll 7 ≈ **3.5 s** — confirms the ADR's ~3.5 s readiness floor |

### Probe 2 — D1 verification gate (`d1_readiness_gate.py`, real SDK + real semgrep)

**Empirical question:** does opening a streaming `ClaudeSDKClient` and polling
`get_mcp_status()` to `'connected'` **before** `client.query(prompt)` make `scan_diff`
available **to the model** — i.e., does the model **act with** the tool (vs G2b, where the
one-shot `query()` fired on turn 1 with `tools:['Read','StructuredOutput']`, `scan_diff`
never registered, `findings=[]`)? Per the gate's contract, `get_mcp_status→'connected'` is
**necessary-not-sufficient** (server-emits ≠ model-receives; the handshake's
`tools.listChanged:true` is protocol support, not a relay guarantee). The gate passes
**only** if the model actually **calls** `scan_diff`.

| Observable | G2b (one-shot `query()`) | D1 gate (`ClaudeSDKClient` + wait-for-connected) |
|---|---|---|
| init `SystemMessage` `mcp_servers` | `[{...,'status':'pending'}]` | `[{'name':'semgrep-runner','status':'connected'}]` |
| init `SystemMessage` model `tools` | `['Read','StructuredOutput']` | **`['Read','StructuredOutput','mcp__semgrep-runner__scan_diff']`** |
| model emits `ToolUseBlock` `scan_diff` | **never** (acted turn 1) | **YES** — `name='mcp__semgrep-runner__scan_diff'` |
| `scan_diff` executes | never | **YES** — semgrep 1.163.0, `files_scanned:1`, ~8.3 s |
| `ResultMessage.subtype` | (n/a) | `success` |

Reproduced across **two runs** (the model-receives observables are stable; semgrep is
deterministic). The init tool snapshot the model acts on now **includes** `scan_diff` — the
exact inversion of G2b. The ADR D1 redirect condition (model acts on a tool-less init
snapshot) **did not fire**.

**Verdict: PASS.** Readiness-wait **does** re-present `scan_diff` to the model. ADR-0014 D1
is the fix **as written** (open client → wait-for-connected → `query` → `receive_response`);
no redesign needed. This resolves **DD-3.2** (the D1 gate desfecho): PASS → ADR D1 proceeds;
no REDIRECT. (Acceptance of ADR-0014 from DRAFT remains a Chat/user step, handoff §8 — the
gate clears the condition; it does not itself flip the Status field.)

### Downstream observation (NOT the gate's question) — `findings:[]`, now newly observable

With readiness fixed, the scan ran for the first time in the agent loop — and the
**`scan_diff` tool itself returned `"findings":[]`** (raw `structuredContent`:
`{rules_version, semgrep_version:'1.163.0', scan_metadata:{base_ref,head_ref,files_scanned:1,
elapsed_seconds:8.3}, findings:[]}`). The model **faithfully transcribed** it:
`DetectorOutput={'findings':[],'provenance':{...threaded correctly...}}`, validated clean,
`subtype=success`. So:
- This is **not** a readiness failure, **not** a model-transcription error, **not** the
  `{"output"}` wrapper — the wrapper stayed **quiet** on the list-shaped `DetectorOutput`
  (but only the **empty-list** case; the non-empty-list wrapper risk #502/#571 is **still
  unobserved**, because semgrep matched nothing).
- It surfaces a genuinely new, **deterministic** fact: the synthetic-CPF probe repo
  (`cpf = '529.982.247-25'`, added line) does **not** trigger the BR-CPF recognizer via
  `scan_diff` **diff-mode** here (`files_scanned:1`, zero findings). The g2b probe **assumed**
  this fixture would detect (ARM D), but the race had prevented anyone from ever validating
  it; ARM E used a hand-built finding, never real semgrep.

**RESOLVED — probe-fixture mismatch** (Detector/semgrep-runner layer, orthogonal to the
readiness/recovery ADR; investigated 2026-06-01). The `br-cpf` rule (`rules/br_cpf.yaml`)
matches `def $FN(..., cpf, ...)` / `def $FN(..., cpf: $T, ...)` — a function **parameter**
named `cpf`, a **purely syntactic** match (DD-T07-3a, ratified 1-pattern-per-rule; matching
the CPF *value* in assignment / dict-key / attribute contexts is a **documented post-MVP
gap**). But `_make_cpf_repo` writes `cpf` as a **local variable** (`def register(user): cpf =
'529.982.247-25'`), so the rule correctly matches nothing — the synthetic CPF *value* is
irrelevant (the rule never inspects it). Confirmed deterministically (semgrep `br_cpf.yaml`):
the local-var form → **0** findings; `def register(user, cpf):` → **1** `br-cpf` finding.
Cross-checked against the passing `test_as1_br_cpf_matches_function_param` (positive fixture
`br_cpf_function_param.py` = `def create_user_account(cpf: str, ...)`). So **not** a recognizer
bug, **not** diff-mode, **not** readiness.

**Fix (PR-B, before G3):** make `_make_cpf_repo` (g2b + the D1 gate inherit it; and the now-stale
g2b ARM-D "BLOCKED by readiness" docstring) add a function with a `cpf` **parameter** in the head
commit, so `scan_diff` diff-mode flags the added `def` line → populated `DetectorOutput` → G3
exercises the full pipeline AND finally observes the non-empty-list `{"output"}` wrapper
(#502/#571, still unobserved). Register the fixture-fix debt in `docs/tasks.md` §Companion.

---

# Phase 2a — CONSOLIDATE BRIEF for the next Code session (MC-C continuation)

> Written at the end of the Phase 0+1 session (context budget). Per
> `.claude/rules/session-management.md`, Phase 2a runs in a **fresh Code
> session**; this is the Code-side handoff. The Chat-side handoff #51 +
> learning-log #51 are separate (Chat-curated) — do NOT edit `docs/process/*`.
> **FIRST ACTION next session:** `git log main --oneline -6` and `git branch -a`
> — re-verify state; do NOT trust the SHAs below if the PRs have merged.

## Where things are (verify with git, don't assume)
- Full 5-phase plan: `C:\Users\paiva\.claude\plans\quero-que-analise-as-graceful-steele.md` (read first).
- Stacked branches: `feat/mc-c-phase0-typegraph` (Phase 0 + A9/A2/§923 docs) and `feat/mc-c-phase1-skeleton` (Phase 1, stacked on phase0).
- Commits (pre-merge): `a1a4f07` A9+§923+A2 docs → `79d5c5b` Phase 0 typegraph → `95b9e52` Phase 1 skeleton → (this brief's commit).
- `main` already has the spec flesh (#86 coordinator, #87 M19/M20). A9/A2/§923 are in the **Phase 0 PR** (commit `a1a4f07`), NOT in main until it merges.
- Independent reviews (2 watch-points) + merges are the USER's; do NOT assume done.

## Environment gotchas (each costs real time if missed)
- **Imports are BARE** (uv editable src-layout): `from coordinator.x import …`, `from subagents.y.models import …` — never a `src.` prefix.
- **Mock the SDK by patching WHERE USED:** `monkeypatch.setattr("coordinator.driver.query", …)` (Branch B stages) AND `"coordinator.run.query"` (Reporter stage) — both, for e2e.
- pytest `asyncio_mode="auto"` (async tests need no decorator). Run: `uv run pytest tests/coordinator tests/subagents -q`.
- Gates each phase: `uv run ruff check src/coordinator src/subagents tests/...` + `uv run mypy --strict src/coordinator src/subagents` clean.
- **semgrep binary is ABSENT here** → the 55 `semgrep_runner` failures in a full `pytest` are ENVIRONMENTAL, not regressions (110 non-semgrep tests green). G2b proceed-path live needs `uv tool install semgrep==1.163.0` (ADR-0010) — ask the user to install at G2b.
- mock-SDK fixture (`tests/coordinator/conftest.py`, `sdk` fixture): `sdk.result(subtype=,stop_reason=,structured_output=,permission_denials=,errors=,num_turns=)`, `sdk.assistant_tool_use(name,input)`, `sdk.system()`, `sdk.user()`, `sdk.make_query(script, raise_after=)`, `sdk.sequential(scripts)->(fn,state)`.

## READY — inherit, do NOT rewrite
- `coordinator/errors.py` (14 exceptions + `SubagentToolError` base + `DetectorScanFailed`).
- `coordinator/models.py` (`CoordinatorReport/Error/Result`); `coordinator/config.py` (`load_mcp_config`, typed `McpServerConfig`).
- `coordinator/driver.py` (`run_branch_b_stage` §3.0bis + `write_scratchpad`) — DONE (13 tests).
- `coordinator/run.py` — FULL main loop already wired: §3.0 init; 5 stages with REAL per-stage `ClaudeAgentOptions` (§3.1–§3.5 verbatim); `derive_run_outcome`; `aggregate_summary`; **§3.5 Reporter tri-axial capture (permission_denials→error_max_turns→emit_report_seen) + `ToolUseBlock.input` dual-sink**; §3.6 `CoordinatorResult`; stderr logging.
- `subagents/*/models.py` (all 5; single-source `Finding`/`TriagerInput`/`ScanProvenance` — do NOT duplicate).
- `subagents/reporter/tools.py` `create_reporter_server` factory — handler validates + atomic-writes + acks. **The 4 cross-checks are STUBBED** (the 2a TODO).
- `subagents/reporter/constants.py` (`EMIT_REPORT_DESCRIPTION` canonical §4.2 — done).
- 5 `system_prompts.py` STUBS + `coordinator/prompts.py` `build_*_prompt` STUBS (functional, thread the contract).
- 80 tests green; G0 PASS; G1 PASS (skip-path).

## Phase 2a MATERIALIZES (the work — flesh, don't re-scaffold)
1. `subagents/triager/system_prompts.py` — replace stub with canonical `TRIAGER_SYSTEM_PROMPT` (triager §5.1: 4 few-shots, XML). Enrich `build_triager_prompt` per §5.1.
2. `subagents/reporter/system_prompts.py` — replace stub with canonical `REPORTER_SYSTEM_PROMPT` (reporter §5.1: XML + the 1 few-shot example_input/example_tool_call).
3. `subagents/reporter/tools.py` — fill the 4 cross-checks in `emit_report_handler`, IN ORDER, BEFORE the atomic write:
   - #1 `policy_clause_ref` regex `^POL-\d{3}$` per finding → `CLAUSE_REF_FORMAT`.
   - #2 trinca top-level == per-finding → `PROVENANCE_MISMATCH`.
   - #3 counts == aggregation(findings) → `COUNTS_DISAGREE_WITH_FINDINGS`; total == sum(counts) → `TOTAL_NOT_SUM_OF_COUNTS` (TWO distinct codes — **A9: these live in the HANDLER, not a SummaryModel validator**).
   - #4 `report_id == expected_report_id` (closure) → `REPORT_ID_MISMATCH`.
   - **BUG TO FIX from the Phase 1 stub:** `_validation_error_envelope` currently puts the structured error in `structuredContent`. Per `.claude/rules/sdk-mcp-conventions.md`, an SDK `@tool` server's `structuredContent` is **dropped** by the bridge — structured error must go in `content` as a JSON string + `is_error: True`. Fix all error envelopes accordingly (cross-ref `sdk_tool_error_channel/RESULTS.md`).

## Red-first anchors for 2a (write RED against the STUB handler FIRST)
- `test_emit_report_counts_disagree` → `COUNTS_DISAGREE_WITH_FINDINGS` + `TOTAL_NOT_SUM_OF_COUNTS` (highest value — A9 auditability).
- `test_emit_report_id_mismatch` → `REPORT_ID_MISMATCH` (closure).
- `test_emit_report_clause_ref_regex` → `CLAUSE_REF_FORMAT`; `test_emit_report_trinca_mismatch` → `PROVENANCE_MISMATCH`.
- `test_emit_report_dual_sink` (99-report.json == captured `block.input`).
- Triager: `test_triager_prompt_renders_all_refs` + `test_as*_triager_proceed/skip/refusal` (mock-SDK canned decisions).
- ALREADY covered in Phase 1 (don't redo): §3.5 tri-axial + `test_skeleton_reporter_not_emitted` (`test_walking_skeleton.py`). 2a adds the HANDLER cross-check anchors + the prompts.

## Watch-points carried into 2a
- **A9:** `SummaryModel` stays PERMISSIVE on `total==sum` (`test_summary_model_is_permissive_on_total_sum`). Do NOT add a `model_validator`. Closure: `grep -n model_validator docs/specs/subagents/reporter.md` → exactly 2 hits (§386, §923), both NEGATING.
- **`{"output"}` wrapper:** G0 proved enum-tag does NOT trigger it on real Matcher/DetectorOutput. Driver does NO unwrap — keep it; re-confirm live at G2b.
- **Per-stage `tools`:** strict-equality `#48-b` anchors are Phase 2b (Classifier/Matcher). 2a touches only Triager (`tools=["Read","Glob"]`) + Reporter (`tools=[]`); options already wired in `run.py`.

## Gate state (do NOT re-run — it's evidence)
- **G0 PASS** — `sdk_output_format_complex/RESULTS.md`. **G1 PASS (skip-path)** — this file above. Proceed-path live = **G2b** (needs semgrep).
- **G2a (this phase):** mock suite for the 4 handler cross-checks + a live "ends" probe (`coordinator_live/`, needs NO semgrep — Triager `mcp_servers={}`, Reporter in-process) confirming Triager proceed+skip live and the emit_report cross-checks fire.

## Open NON-code items (Chat/user territory)
- learning-log #50 commit (append; ADR-0001 D6 direct-to-main) — recommended; user/Chat commits.
- handoff #51 — Chat rewrites from this brief. A9/A2/§923 — DONE (`a1a4f07`, in Phase 0 PR).
