# Synthetic PR — SKIP-001 (Triager skip; etapa 0, NÃO é veredito)

This PR changes **only documentation** — no application code, no data-handling.
It is the "discard by irrelevance" structuring scenario (relatorio-tcc2-parcial.md
§validação; planejamento-tcc2.md). The Triager (etapa 0) should emit
`decision: skip` with a `skip_reason`, and the coordinator short-circuits to the
Reporter (`run_outcome: skipped_by_triager`) — **no candidate, no verdict**.

PIPELINE-ONLY: the Triager is an LLM subagent (live model), so this case is NOT
exercised by the deterministic engine harness (`engine_runnable: false` in
`eval/cases.yaml`). It is exercised only by the full pipeline run
(`run_pipeline`), per `eval/harness/README.md`.

The diff for this synthetic PR consists solely of edits to this Markdown file
(and, in a real run, to other `docs/` files). To make it a real git diff for
`scan_diff` (which takes `base_ref`/`head_ref`), commit a docs-only change on a
branch off the synthetic-repo base. No `*.py` files are touched, so even if the
Triager (wrongly) said `proceed`, `scan_diff` would return `findings: []` and
the Reporter would emit `run_outcome: success_no_candidates`. Either way: no
substantive verdict — which is the correct outcome for an irrelevant PR.
