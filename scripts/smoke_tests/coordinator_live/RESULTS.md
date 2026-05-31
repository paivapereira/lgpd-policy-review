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
