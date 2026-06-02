# eval/experiments

Exploratory **measurement** harnesses (live, opt-in). Unlike `eval/harness/`
(deterministic engine sweep, no model) and `tests/` (pass/fail invariants),
scripts here drive the real model over K runs and print **raw distributions**.
They are *measurements*, not assertions: they never draw the final conclusion —
the reading is done by a human over the raw numbers.

## category_exposure_discriminant.py

**Question.** Does exposing the `data_categories` **list** on
`policy://vocabularies` suffice for the Classifier to classify **correctly**, or
does it also need **demonstration** (`canonical_examples`, the future
`policy://examples`)?

**Two conditions** — the *only* difference is the payload shape served by
`policy://vocabularies` (confirmed in-process before any model call):

| Condition | `POLICY_READER_EXPOSE_CATEGORY_EXAMPLES` | `data_categories` payload |
|---|---|---|
| C1 | unset (production default) | names-only — `{name}` per token |
| C2 | `1` (experiment-only) | names **+** `canonical_examples` per token |

**Policy root.** `policies/eval-lgpd` (has POL-005/006/007). NOT the real
`policy/` (POL-000 only), which would confound an empty classification with
"no governing clause" (plan R1).

**Vehicle.** Clones the isolated-live-Classifier template of
`scripts/smoke_tests/coordinator_live/g2b_mcp_middle_live.py` (Arm E). It
**imports** the production driver/options/prompt builder (`_run_mcp_stage`,
`_classifier_options`, `build_classifier_prompt`); it does not reimplement them.

### Input matrix (single-concern fixtures)

Inputs are hand-crafted `DetectorFinding`s over `fixtures/` (full control — not
bound to what Semgrep fires). Fixtures are **single-concern** so each case
measures one signal cleanly.

| Case | K | Fixture | Provenance | Ground truth |
|---|---|---|---|---|
| L1-cpf-bare | 3 | `l1_bare_cpf.py` | the G3 case `def collect(cpf)` | `dados_de_identificacao` **OR** `dados_de_documentos_oficiais` (R6) |
| L2-cpf-rich | 3 | `l2_rich_identification.py` | mirrors `eval/prs/COMP-001/users.py` | `dados_de_identificacao` **OR** `dados_de_documentos_oficiais` (R6) |
| N1-behavioral | 5 | `n1_behavioral.py` | `eval/prs/INDET-001/analytics_ingest.py`, **`cpf` removed** | `dados_de_perfil_comportamental` (strict) |
| N2-location | 5 | `n2_location.py` | `eval/prs/PROBE-UNGOV-001/geo.py`, **`cpf` removed** | `dados_de_localizacao` (strict) |
| TN-generic | 5 | `tn_generic_helper.py` | the Classifier prompt's own miss-total example | `[]` (abstention is correct) |

> **Why the `cpf` is removed from N1/N2.** The real INDET-001 / PROBE-UNGOV
> fixtures carry a `cpf` parameter solely to give the *Detector* a Semgrep
> trigger in the full pipeline. For an isolated Classifier measurement of
> *non-literal* inference, that `cpf` would let the model also emit an
> identification token and contaminate the strict single ground truth. Removing
> it isolates the discriminating signal. **L1/L2 keep `cpf`** — there it *is* the
> signal (the R6-ambiguous literal case).

### Outcomes (per run, vs ground truth)

- `correto` — non-empty emitted set ⊆ acceptable token(s); for TN, `correto` ==
  emitted is `[]`.
- `abstem` — emitted `[]` when a category was expected.
- `errado` — emitted non-empty but not ⊆ acceptable (missing token, or a
  hallucinated/extra category).
- `erro_execucao` — the stage raised (SDK/schema/passthrough). Never hidden,
  never retried.
- A cell whose K runs disagree is flagged `<<INCONSIST` — that is a datum, not a
  bug to re-run away.

### Run

```powershell
uv run python eval/experiments/category_exposure_discriminant.py
```

Pre-reqs: authenticated Claude Code session; `.mcp.json` at repo root. The script
prints the policy root in use and the total model-call count, and writes raw
per-run data to `output/discriminant_raw.json` (committed as data — the
interpreted conclusion is deliberately NOT committed; it lives in the Chat).
