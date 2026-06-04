"""Pure renderers: Report payload / CoordinatorError -> Markdown summary string.

No I/O and no destination choice (E1 / DD-P4-2): callers print the returned
string; the workflow YAML redirects stdout to $GITHUB_STEP_SUMMARY. The payload
shape is the emit_report ReportPayload captured by the coordinator
(`src/coordinator/run.py` _build_consolidated_state): `run_outcome`,
`summary{counts, total}`, the provenance triple, and `findings[]` each carrying
`policy_clause_ref` / `verdict` / `rule_id` / `data_categories` / `file` / `line`.

Honors the immutable domain rules: every finding row cites its `clause_id`
(rule 2); the error renderer emits no fabricated verdict (rule 1).

Contract of record: plano Passo 4 v3 ratificado (sem spec em docs/specs/).
"""
from __future__ import annotations

from typing import Any

_VERDICTS: tuple[str, ...] = (
    "compliant",
    "violation_candidate",
    "indeterminate",
    "not_applicable",
)

# per-verdict prose carrying the system's stated reasoning (honest, not fabricated)
_NOTE_FIELDS: tuple[str, ...] = ("evidence", "reason", "contradicted_requirement")


def render_report_summary(payload: dict[str, Any]) -> str:
    """Render a successful run's Report payload as a Markdown summary string."""
    run_outcome = str(payload["run_outcome"])
    summary = payload["summary"]
    counts = summary["counts"]
    total = summary["total"]
    findings = payload["findings"]

    lines: list[str] = ["## LGPD Policy Review", ""]
    lines.append(f"**run_outcome:** `{run_outcome}` — {total} finding(s)")
    lines.append(
        f"**Política:** {payload['legal_framework']} · "
        f"policy_version `{payload['policy_version']}` · "
        f"schema `{payload['policy_schema_version']}`"
    )
    lines.append("")
    lines.append("**Vereditos:** " + " · ".join(f"{v} {counts[v]}" for v in _VERDICTS))
    lines.append("")

    if not findings:
        if run_outcome == "skipped_by_triager":
            reason = payload.get("triager_skip_reason") or "sem motivo declarado"
            lines.append(f"_PR pulado pelo Triager (etapa 0): {reason}._")
        else:
            lines.append("_Nenhum finding substantivo._")
        return "\n".join(lines)

    lines.append("| Cláusula | Veredito | Regra | Local | Categorias |")
    lines.append("|---|---|---|---|---|")
    for finding in findings:
        location = f"{finding['file']}:{finding['line']}"
        categories = ", ".join(finding.get("data_categories") or [])
        lines.append(
            f"| {finding['policy_clause_ref']} | {finding['verdict']} "
            f"| {finding['rule_id']} | `{location}` | {categories} |"
        )

    notes = _render_notes(findings)
    if notes:
        lines.append("")
        lines.extend(notes)
    return "\n".join(lines)


def _render_notes(findings: list[dict[str, Any]]) -> list[str]:
    """One bullet per finding that carries stated reasoning prose."""
    out: list[str] = []
    for finding in findings:
        note = next((str(finding[k]) for k in _NOTE_FIELDS if finding.get(k)), None)
        if note is not None:
            out.append(f"- **{finding['policy_clause_ref']}** ({finding['verdict']}): {note}")
    return out


def render_error_summary(stage: str, coverage_gap: str, cause_type: str) -> str:
    """Render a CoordinatorError as an honest, verdict-free Markdown summary."""
    return "\n".join(
        [
            "## LGPD Policy Review — execução interrompida",
            "",
            f"**Estágio:** `{stage}`",
            f"**Causa:** `{cause_type}`",
            f"**Cobertura:** {coverage_gap}",
            "",
            "_O sistema não pôde concluir a análise; nenhum veredito é emitido "
            "(sem certeza fabricada). Verificação manual necessária._",
        ]
    )
