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
