# ADR-0014 — MCP connection lifecycle and resilience in the coordinator driver

**Status.** Proposed (DRAFT for review — surfaced by the MC-C Phase 2b G2b agent-loop gate, PR #92; evidence in `scripts/smoke_tests/coordinator_live/RESULTS.md` "GATE G2b"). **Acceptance is conditional on the D1 verification gate** (see Decision). Session # to be filled on acceptance.
**Date.** 2026-06-01
**Aprovação.** Pending — draft submitted for Chat review; not yet registered via a PR.
**Supersedes.** Nothing.
**Superseded by.** Nothing.
**Related.** ADR-0002 (MCP conventions; Option B error envelope, Decision 3 + 2026-05-17 amendment — the `{errorCode, message, isRetryable, details}` contract this ADR consumes from the stream). ADR-0010 (Semgrep installation — `SEMGREP_BINARY_UNAVAILABLE` as the canonical system/transient failure). ADR-0012 (subagent tool governance — capability vs availability; Deferral B assigns the coordinator-owned gate to Milestone C). ADR-0008 (task decomposition + two-scope verification gate). ADR-0011 (Windows-stdio subprocess transport — the *subprocess*-layer analogue, distinct layer). DD-d (`detector.md` §6.2 / `coordinator.md` §5). `.claude/rules/sdk-mcp-conventions.md` (layer-aware discriminator: read `errorCode` from `tool_use_result.structuredContent`, ignore `isError` under Option B).

---

## Context

The coordinator runs the five Branch-B stages as **five independent one-shot `query()` calls** (`run.py` `run_pipeline`), one per stage, each spawning only its own `mcp_servers`:

| Stage | `mcp_servers` | Server kind | Cold-start race? |
|---|---|---|---|
| Triager | `{}` | none | No |
| Detector | `{"semgrep-runner": ...}` | out-of-process FastMCP (subprocess) | **Yes** |
| Classifier | `{"policy-reader": ...}` | out-of-process FastMCP (subprocess) | **Yes** |
| Matcher | `{"policy-reader": ...}` | out-of-process FastMCP (subprocess) | **Yes** |
| Reporter | `{"reporter_tools": ...}` | in-process `create_sdk_mcp_server` | No (G1 PASS) |

**The gap, observed at G2b (the agent-loop gate).** The one-shot `query()` path has **no MCP readiness-wait**. When the Detector's `query()` spawns `semgrep-runner` (a subprocess FastMCP server with **~3.5 s intrinsic cold-start** — FastMCP boot + imports + rules load; verified `uv run` ≈ venv-direct, so it is *not* `uv` overhead and a faster launch cannot win it), the model acts on **turn 1** before the server connects: the init `SystemMessage` reports `mcp_servers: [{'name':'semgrep-runner','status':'pending'}]` and `tools: ['Read','StructuredOutput']` — `scan_diff` is never registered — so the Detector emits `findings=[]`. This is **real in production, not a test artifact**: the Triager declares `mcp_servers={}`, so `semgrep-runner` is first and only spawned by the Detector's own `query()`, always cold; the CI coordinator races identically. Sub-causes B (FastMCP banner on stdout) and C (`uv` stdout noise) were ruled out by observation — stdout is pure JSON-RPC, banner on stderr. (Full triage: `RESULTS.md` "GATE G2b".)

**The mechanism gap.** MCP readiness and recovery — `get_mcp_status()` and `reconnect_mcp_server()` — exist **only on the streaming `ClaudeSDKClient`**, never on the one-shot `query()`. The constraint is mechanical: all control requests gate on streaming mode (`_internal/query.py:510-511` `if not self.is_streaming_mode: raise Exception("Control requests require streaming mode")`), and `ClaudeSDKClient` is hard-coded `is_streaming_mode=True` (`client.py:227`). The one-shot `query()` has no control channel and fires the prompt regardless of MCP readiness.

**The other half — recovery (DD-d).** Independently, `detector.md` §6.2 / `coordinator.md` §5 (l.428) mandate that **retryable** `scan_diff` errors (`SCAN_TIMEOUT`, `SEMGREP_EXECUTION_FAILED`) be retried *before* escalating `DetectorScanFailed`. The Phase-2b hook ships **escalate-all** (`subagents/detector/hooks.py`): it raises `DetectorScanFailed` on any `errorCode`, carrying `is_retryable` verbatim, but does **not** act on it — the retry loop was explicitly deferred to Fase 3.

**No existing ADR governs the coordinator's SDK-transport / agent-loop driver.** ADR-0012 governs how subagents *reach* MCP servers (capability vs availability) but not the driver loop; ADR-0011 is subprocess transport *inside* the semgrep-runner (git/semgrep CLI), a different layer; ADR-0002/0004 cover the FastMCP wire format and the SDK pin, not the driver. This ADR is the first to cover the driver-transport / agent-loop resilience surface. (`coordinator.md` already carries a forward note for a `WaitForMcpServers` mechanism.)

**Readiness and recovery are two halves of one apparatus** — *wait for `connected` before acting* and *retry on transient failure* — both requiring the streaming `ClaudeSDKClient` control channel (`get_mcp_status` / `reconnect_mcp_server`). They belong in one decision, not two loose follow-ups.

---

## Decision

### D1 — MCP-consuming stages run on the streaming `ClaudeSDKClient`, gated on readiness

The three stages that spawn a subprocess MCP server — **Detector, Classifier, Matcher** — migrate from the one-shot `query()` to the streaming `ClaudeSDKClient`. Each stage:

1. opens the session: `async with ClaudeSDKClient(options) as client:` (`client.py:619-627`; auto-connects with an empty stream and keeps the session open);
2. **waits for readiness**: polls `await client.get_mcp_status()` (`client.py:473`) until the target server's `status == "connected"` (`McpServerConnectionStatus = Literal["connected","failed","needs-auth","pending","disabled"]`, `types.py:707-709`), bounded by a poll interval + max attempts/timeout; on `"failed"` it calls `await client.reconnect_mcp_server(target)` (`client.py:402`);
3. sends the prompt: `await client.query(prompt)`;
4. consumes to the terminal `ResultMessage` via `async for msg in client.receive_response():` (`client.py:567`, self-terminates on `ResultMessage`), under a stage-level timeout (the iterator hangs if no `ResultMessage` arrives — `client.py:579`).

**Triager (`mcp_servers={}`) and Reporter (in-process server, no cold-start race — G1 PASS) stay on the one-shot `query()`.** Migrating either is needless surface; their stage paths are unchanged.

The driver spine `run_branch_b_stage` keeps its capture/discrimination logic **verbatim** — `ResultMessage` capture without `break`, `stop_reason=="refusal"` precedence, the `subtype` match table, the `on_tool_result` hook (Detector), `verify_passthrough` (Classifier), Pydantic validation, scratchpad write, and the `except DetectorScanFailed: raise` carve-out. Only the **transport prologue** (open client → wait-for-connected → `query` → switch the iterator to `receive_response()`) and the connection-failure arm of the existing `try/except` change. The per-stage `_*_options()` (the quintupla canonica + `output_format`) pass to `ClaudeSDKClient(options=...)` unchanged.

### D1 verification gate — readiness must actually re-present the tool to the model (UNVERIFIED; observe before committing the design)

D1 rests on a **causal assumption that is inference, not observation**: that polling `get_mcp_status()` to `"connected"` *before* `client.query(prompt)` makes `scan_diff` available **to the model** when it acts. What G2b actually observed is `tools: ['Read','StructuredOutput']` in the **init** `SystemMessage` — the tool set the model saw at session start. It is **not** verified whether `ClaudeSDKClient` re-presents an updated tool set to the model after a server connects late, or whether the model acts on that init snapshot. The server handshake advertises `tools: {listChanged: true}` (the MCP protocol *supports* dynamic tool-list updates), but **protocol support ≠ the SDK relay re-presenting the updated list to the model before it acts** — precisely the relay-behavior class that cost four round-trips in the Phase-2b saga when assumed instead of observed.

**Gate (must pass before D1 is load-bearing — `gates.md` / `mcp-testing.md`):** a smoke probe opens `ClaudeSDKClient`, waits for the target server `"connected"` via `get_mcp_status()`, **then** confirms `scan_diff` is in the tools **available to the model** (a turn that actually calls the tool, or whatever the SDK exposes as the live tool set) — not merely in the server *status*.
- **Pass** → D1 is the fix as written.
- **Fail** (the model acts on the init snapshot) → D1 needs a different shape: guarantee `"connected"` **before** the initial stream that fixes the tool snapshot, or **re-prompt after `connected`** so the model re-derives its tool set. This is a design fork D1 resolves *empirically*, not by assumption.

This is **distinct from** the mock-fidelity risk below (which verifies the API *shape*); this gate verifies the **causal assumption** that readiness-wait resolves the race. Until it passes, D1 is a proposal, not a solution (see Status + "Proposes to close").

### D2 — Recovery: retry retryable `scan_diff` errors *within the live session*, driven by `isRetryable`

The escalate-all hook remains the deterministic detector (it carries `is_retryable`). Recovery happens **inside one live `ClaudeSDKClient` session per stage** — the `async with` opens the session **once** and **wraps** the bounded retry loop (not the reverse). On `DetectorScanFailed` with `is_retryable is True` and budget not exhausted, the driver **reconnects the server in place** (`await client.reconnect_mcp_server(target)`, then re-waits readiness) and **re-issues the prompt on the same open session**; on `is_retryable is False` or budget exhausted it lets `DetectorScanFailed` propagate. The decision is driven by `isRetryable`, not the exception type (`coordinator.md` §5, l.443). **The retry `try/except` must wrap the message-consumption loop**, because the hook raises `DetectorScanFailed` *during* consumption (`subagents/detector/hooks.py:51`), not in the discrimination tail — wrapping only the tail would let a retryable scan-error escape the retry (see Appendix). Generalizes to the Matcher's `policy-reader` tool errors (same Option-B envelope).

**Two recovery mechanisms, and only one is correct here.**
- *Reconnect* — `reconnect_mcp_server()` on an already-open client: reconnects the server **without tearing down the session**; the `~3.5 s` cold-start is paid once. **This is what the retry uses.**
- *Re-spawn* — closing and reopening the `ClaudeSDKClient`: pays the full cold-start **again, every attempt**, and discards the very session `reconnect_mcp_server` operates on.

Therefore the `async with ClaudeSDKClient(...)` lives **outside** the `for attempt` loop (see Appendix). Putting it inside (re-spawn per attempt) would both nullify the readiness investment and contradict the in-session `reconnect`. This also pins Deferral B's default: the per-stage session is persistent across that stage's retries (not per-attempt).

### D3 — Readiness-wait and retry budget are error mechanics → they live in the §3.0bis driver spine only

Per anti-drift rule #3 ("error handling pattern lives ONLY in §5/§3.0bis"), the wait-for-connected loop and the bounded retry-on-`isRetryable` are implemented **inside or immediately around `run_branch_b_stage`** and specced in §5 — never scattered into the per-stage `_*_options()` bodies or the §3.1–§3.4 stage bodies. Implementing the retry per-stage in `run_pipeline` would duplicate mechanics and violate the rule.

### D4 — A readiness/connection failure maps to the existing `CoordinatorStreamFailure`

When a target server never reaches `"connected"` within the readiness budget (or `reconnect` fails), the stage raises `CoordinatorStreamFailure(stage=stage)` — a no-result stream failure, which the existing class already models. **No new exception type** is introduced for this path (consistent with the ADR-0013-earmarked exception-hierarchy work staying separate).

### D5 — The test surface migrates to a mock streaming client for MCP stages

The MCP-consuming stages get a **mock `ClaudeSDKClient`** — an async context manager exposing `get_mcp_status()` (scriptable status sequence, e.g. `pending → connected`, or stuck `pending` to exercise the readiness-timeout), `query()`, `receive_response()` (replaying the *same* scripted message list the current `make_query` yields — `sdk.result`/`assistant_tool_use`/`scan_error` constructors are reused verbatim), and `reconnect_mcp_server()` (call-counted for the retry test). `make_query` / `make_sequential_query` **stay** for the Triager + Reporter (`coordinator.run.query`). Consequently the "install the SAME fn at both `coordinator.driver.query` and `coordinator.run.query`" e2e pattern **splits** into heterogeneous patch targets (client mock for the driver's MCP stages; `make_query` for the Reporter) — the single largest test-rewrite cost.

---

## Deferrals (revisit-with-condition, ADR-0002 A–I pattern)

### Deferral A — concrete readiness + retry budgets

**Decision:** the readiness poll interval, max attempts/timeout, and the retry budget for `SCAN_TIMEOUT`/`SEMGREP_EXECUTION_FAILED` ship with provisional values; they are not fixed by this ADR.
**Revisit condition:** calibrate empirically against the live `g2b_mcp_middle_live.py` re-run and MC-D timing (the ~3.5 s cold-start is the floor for the readiness budget).

### Deferral B — session sharing *across stages* (the per-stage session itself is fixed by D2)

**Decision:** default to **one persistent `ClaudeSDKClient` session per stage** — opened once at stage entry, spanning that stage's readiness wait *and* all its retries (D2), closed at stage exit. This is settled by D2 (not per-attempt — re-spawn is forbidden) and is **not** cross-stage. It preserves the per-stage tool isolation ADR-0012 establishes (each stage sees only its own servers; least-privilege). What remains deferred is only whether to share **one session across stages**.
**Revisit condition:** if repeated per-stage cold-start cost dominates wall-clock, evaluate a single `ClaudeSDKClient` **shared across stages** (warm each server once) — but only if the tool-isolation regression is acceptable, since a cross-stage session would expose every stage to every server. The streaming client holds a persistent anyio task group from `connect()` to `disconnect()` and cannot cross async contexts (`client.py:58-64`), so a cross-stage session also constrains the whole pipeline to one task scope.

---

## Consequences

**Positive.**
- `scan_diff` / `policy-reader` are reliably registered before the stage acts — the Detector actually scans, the Classifier reads vocabularies, the Matcher runs check-all. The G2b agent-loop arm unblocks.
- Transient/system failures (`SCAN_TIMEOUT`, `SEMGREP_EXECUTION_FAILED`, `SEMGREP_BINARY_UNAVAILABLE` — ADR-0010) are recovered under budget instead of failing the run; permanent/business errors still escalate immediately (`isRetryable`-driven).
- The `{"output"}` wrapper on the **list-shaped `DetectorOutput`** (`findings: [...]`, the #502/#571-prone shape) becomes **observable for the first time** — the readiness fix is the precondition. The driver keeps doing **no unwrap**; if the wrapper fires live, that is a fail-action handled in this PR (G2b "GATE G2b" wrapper status remains *not observed* until then).

**Cost / risk.**
- Transport migration touches the driver spine, three stages, and the conftest mocks; the "same fn at both" e2e pattern splits (D5) — the largest mechanical cost.
- **Mock-fidelity risk** (`.claude/rules/verification-before-inference.md`): the client surface (`connect`/`get_mcp_status`/`receive_response`/`reconnect_mcp_server` + the `McpServerStatus` shape) must be **smoke-tested against `claude-agent-sdk==0.2.87`** before the mock commits to a shape (`gates.md` / `mcp-testing.md`) — the same discipline that produced the G2b evidence.
- `receive_response()` hangs without a `ResultMessage` → the stage imposes its own timeout. The single-async-context constraint (`client.py:58-64`) means each per-stage client lives entirely within one task scope.

**Verification (ADR-0008, two scopes).**
- Task-level (red-first): readiness-timeout (status stuck `pending`) → `CoordinatorStreamFailure`; a scripted `SCAN_TIMEOUT`-then-success → exactly one `reconnect_mcp_server` call + green; the preserved-spine regression (the existing `test_driver.py` discrimination anchors stay green through the transport swap).
- Milestone-level: re-run `scripts/smoke_tests/coordinator_live/g2b_mcp_middle_live.py` — ARM D scans (populated `DetectorOutput`, `{"output"}` wrapper observed/handled), ARMs E/F/G green.

**Proposes to close (conditional on the D1 verification gate).** This ADR *proposes* to close the MC-C Phase 2b G2b deferred debt — both the readiness race and the DD-d recovery loop — under one decision. It is a **draft**: it closes nothing until accepted **and** the D1 verification gate passes (a proposed ADR proposes; it does not close). Ships as a **separate reliability PR** (`.claude/rules/git-conventions.md`, no PR-mista), architecturally distinct from the Phase-2b prompt/hook/passthrough flesh.

---

## Appendix — implementation sketch (faithful to the read API)

```python
# inside / around run_branch_b_stage, for MCP-consuming stages only (D1+D2+D3)
async def _run_mcp_stage(options, *, target, prompt, budget, stage, ...):
    async with ClaudeSDKClient(options) as client:        # D1: ONE session per stage (NOT per attempt)
        await _wait_for_connected(client, target, stage)  # D1 (b) readiness gate, once
        for attempt in range(budget):                     # D2: retry WITHIN the live session
            try:                                          # the try MUST wrap the CONSUMPTION loop,
                await client.query(prompt)                # not just _discriminate_and_capture: the
                last_result = None                        # on_tool_result hook raises DetectorScanFailed
                async for message in client.receive_response():   # DURING consumption (hooks.py:51),
                    if on_tool_result is not None:        # not in the discrimination tail. If the try
                        on_tool_result(message)           # wrapped only the tail, a retryable scan-error
                    if isinstance(message, ResultMessage):  # would escape the retry loop unhandled.
                        last_result = message
                return _discriminate_and_capture(last_result, ...)   # refusal/subtype/validate/verify/scratchpad — all preserved
            except DetectorScanFailed as exc:             # D2: retry-vs-escalate by isRetryable
                if exc.is_retryable and attempt + 1 < budget:
                    await client.reconnect_mcp_server(target)        # RECONNECT in-session — NO re-spawn
                    await _wait_for_connected(client, target, stage) # re-wait after reconnect
                    continue
                raise                                     # non-retryable / budget exhausted
        raise CoordinatorStreamFailure(stage=stage)       # defensive: budget exhausted without a result


async def _wait_for_connected(client, target, stage):     # D1 (b) readiness gate; D4 on timeout
    for _ in range(READINESS_ATTEMPTS):
        status = await client.get_mcp_status()            # McpStatusResponse (streaming-only)
        srv = next((s for s in status["mcpServers"] if s["name"] == target), None)
        if srv and srv["status"] == "connected":
            return
        if srv and srv["status"] == "failed":
            await client.reconnect_mcp_server(target)
        await anyio.sleep(READINESS_POLL_S)
    raise CoordinatorStreamFailure(stage=stage)           # D4: never reached 'connected'
```

*Notes:* the `async with` opens **one session per stage** and **wraps** the retry loop — D2 recovery reconnects **in-session** (`reconnect_mcp_server`, `client.py:402`), **never re-spawns** (the cold-start is paid once). **The retry `try/except` wraps the consumption loop, not only `_discriminate_and_capture`**: the Detector's `on_tool_result` hook (`inspect_scan_diff_result`) raises `DetectorScanFailed` *during* message consumption (`subagents/detector/hooks.py:51`), not in the discrimination tail — so a `try` around the tail alone would let a retryable scan-error escape the retry unhandled. (Verified against the real hook, not inferred from the driver comment.) `get_mcp_status()`/`reconnect_mcp_server()` are streaming-only (`client.py:473`/`402`; control requests require streaming mode, `_internal/query.py:510-511`); `receive_response()` self-terminates on `ResultMessage` (`client.py:605-606`) but can hang otherwise → impose a stage timeout. **The whole sketch is contingent on the D1 verification gate** (that readiness-wait actually re-presents `scan_diff` to the model); `READINESS_*` / `budget` are Deferral A; cross-stage session sharing is Deferral B.
