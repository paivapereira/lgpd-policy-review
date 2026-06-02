# eval/harness — how to run the evaluation

Two granularities, by design. The **engine harness** is deterministic and runs
today; the **full pipeline** needs the live model + MCP servers and is
documented but not run here (per the task: "deixar montável e documentado como
rodar").

## 1. Engine harness (deterministic, model-free) — RUNS TODAY

Exercises the core of the system — the four-verdict logic of
`check_applicability` — in-process (Pattern A from
`scripts/smoke_tests/check_applicability_48b/probe.py`): `load_policy(root)` +
`tools.check_applicability(clause_id, structured_context, state)`, reading the
verdict from `result.structured_content` (Option B).

```powershell
# from repo root
uv run python eval/harness/run_engine_cases.py            # table
uv run python eval/harness/run_engine_cases.py --json     # machine output
```

- Reads `eval/cases.yaml` (the machine-readable catalog).
- Cases with `engine_runnable: true` are executed; `false` (e.g. SKIP-001) are
  skipped (they need the model).
- Topology B: LGPD cases load `policies/eval-lgpd/`; GDPR cases load
  `policies/eval-gdpr/`. The product seed `policy/` (POL-000-only) is not used by
  the evaluator.
- `coverage_gap` (mode `sweep`) = every active clause returned `not_applicable`
  while the context has data and `operation == collection` (the ungoverned-
  category probe; matcher.md DD-M8).
- Exit code 0 iff every engine-runnable case matched its expected outcome.
- `lawful_basis_required` (POL-008, ADR-0015) is NOT exercised here: the control
  is unimplemented by the engine, so POL-008 is staged in `eval/proposed/`, kept
  out of the catalog and out of every loaded root. If an unimplemented control
  ever reaches a loaded root, the engine crashes loudly (intended fail-fast).

The last gate run is persisted in `eval/harness/gate_run.json` (evidence; the
gate's existence and outcome, per `.claude/rules/gates.md`).

**What layer 1 does NOT cover** (by construction): the Triager skip decision, the
Detector's Semgrep scan, the Classifier's extraction of `structured_context`, the
Matcher's LLM enumeration/ordering, and the Reporter's live `emit_report`. Those
are the LLM/MCP layers. The Reporter's deterministic *derivations*, however, ARE
covered — see layer 2.

## 1b. Consolidated Reports (layer 2, deterministic) — RUNS TODAY

The same run also assembles real consolidated Reports without the LLM, by reusing
the coordinator's own derivations (imported, never reimplemented — single source
of truth):

- For each candidate-bearing LGPD case, sweep all active clauses (Matcher
  check-all, DD-M1) → one Matcher `Finding` per (candidate × clause) built from
  the engine verdict → `derive_run_outcome` + `aggregate_summary` +
  `_build_consolidated_state` (all `src/coordinator/run.py`) → validate against
  `ReportPayload` (the `emit_report` inputSchema).
- Written to `eval/harness/reports/<CASE>.report.json`; for a case with a
  synthetic PR, also to `<pr_dir>/.expected-report.json` (that PR's expected
  baseline, valid against the real contract).
- Which cases emit a Report: `engine_runnable` + `policy_root: eval-lgpd` +
  not a single-clause contract probe (`NA-MISMATCH-001`/`NA-DEF-001`).
- **run_outcome coverage (no model):** `success_with_findings` and
  `success_all_not_applicable`. `skipped_by_triager` (needs the Triager) and
  `success_no_candidates` (needs the Detector to find zero) are **pipeline-only**.
- **GDPR Reports are NOT emittable in the MVP:** `Finding`/`ReportPayload` pin
  `legal_framework: Literal["LGPD"]` (`src/subagents/{matcher,reporter}/models.py`).
  The GDPR swap *verdict* is still covered by layer 1; only the consolidated
  Report is LGPD-locked until a minor bump.
- **Locus is synthetic:** `file`/`line`/`snippet`/`rule_id` of each finding are
  synthetic in the engine harness (the Detector/Classifier supply real loci in
  the pipeline). The *verdict* layer (verdict, `policy_clause_ref`, evidence,
  provenance, summary, run_outcome) is real and deterministic.
- **`report_id` is the only non-deterministic field** (uuid4, required by the
  model pattern). Every other field is reproducible; baseline diffs of the
  committed Reports should ignore `report_id`.
- `requires_human_review` is left unset (it is Matcher-layer logic, not engine).

The highest-value baseline is the POL-007 inversion: `B-SENS-OK` (saúde + bare
`consent`) → `compliant`, vs `B-SENS-INV` (saúde + correct `explicit_consent`) →
`violation_candidate`. Those two Reports document the Art.11 sub-modelagem
empirically, before the ADR-0015 fix.

## 2. Full pipeline (live model + MCP servers) — DOCUMENTED, not run here

The consolidated Report is produced by `run_pipeline` (Triager → Detector →
Classifier → Matcher → Reporter). Entry point (verified in
`src/coordinator/run.py`):

```python
from coordinator.run import run_pipeline
from coordinator.models import ...  # CoordinatorReport | CoordinatorError
# scope is a TriagerInput {pr_number, base_ref, head_ref, repo_url}
result = await run_pipeline(scope, scratchpad_root=Path(".scratchpad"))
```

Prerequisites (from the smoke-test gates and specs):
- An authenticated Claude Agent SDK session and `semgrep` on PATH (the suite
  marks these `-m live`; `pyproject.toml` excludes live by default).
- `.mcp.json` declaring `policy-reader` and `semgrep-runner` (the coordinator
  whitelists exactly these two — `EXPECTED_SERVERS`).
- Policy root: set `POLICY_READER_ROOT` to choose the instance —
  `policies/eval-lgpd/` (LGPD) or `policies/eval-gdpr/` (GDPR swap). The loader
  precedence is explicit-arg > `POLICY_READER_ROOT` > `<repo>/policy` (the seed
  fallback) (loader.py:51-63).
- A synthetic git repo whose `base_ref`/`head_ref` bracket the PR diff (the
  `eval/prs/*` files are the diffs to plant). `scan_diff` resolves refs and runs
  Semgrep `--baseline-commit`.

The full-pipeline outcome of each case is what fills the **"obtido (pipeline)"**
column of the catalog in `docs/eval/test-cases-proposal.md` — left empty until
that run is performed.

### GDPR swap run

```powershell
$env:POLICY_READER_ROOT = "policies/eval-gdpr"   # GDPR side of SWAP-001
# ... run_pipeline over the SAME eval/prs/SWAP-001 diff ...
$env:POLICY_READER_ROOT = "policies/eval-lgpd"   # LGPD side (same diff)
```

Same diff, two roots → verdict flips compliant ↔ violation_candidate by
lawful_basis vocabulary (`consent` vs `consent_gdpr`).

## 3. Detection note (for full-pipeline realism)

The Detector only flags the 6 BR recognizers (Python): `br-cpf`, `br-cnpj`,
`br-cnh`, `br-nis-pis`, `br-titulo-eleitor`, `br-cns-saude`. Every synthetic PR
that must produce a candidate therefore contains at least one BR identifier
(usually `cpf`). Categories like `dados_de_identificacao`, `_localizacao`,
`_perfil_comportamental` are surfaced by the **Classifier** (which reads the
file), not by the Detector. This is why behavioral/location cases carry a `cpf`
trigger — see the per-PR docstrings and the open tension on RF-002 coverage.
