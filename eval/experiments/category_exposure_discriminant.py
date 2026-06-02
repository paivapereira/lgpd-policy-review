"""Category-exposure discriminant — does exposing the data_categories LIST on
`policy://vocabularies` suffice for the Classifier to classify CORRECTLY, or
does it also need DEMONSTRATION (canonical_examples)?

THIS IS A MEASUREMENT, NOT A SEARCH FOR A RESULT.
- The matrix and the exposure are FROZEN. Do not tweak inputs/prompt/exposure to
  "improve" a result; if something seems to need changing, STOP and report.
- Every planned run is recorded; nothing is re-run to pick a better result. An
  inconsistent result across runs IS a datum (outcome "INCONSIST"), not an error.
- This script does NOT draw the final conclusion ("list suffices" / "needs
  examples" / "needs a dedicated policy://examples"). It prints raw numbers and
  stops; the reading is done by a human over the raw data.

Conditions (the ONLY difference is the presence of canonical_examples in the
`policy://vocabularies` payload — nothing else changes):
  C1 = names-only                  (POLICY_READER_EXPOSE_CATEGORY_EXAMPLES unset)
  C2 = names + canonical_examples  (POLICY_READER_EXPOSE_CATEGORY_EXAMPLES=1)

Policy root: policies/eval-lgpd (NOT the real policy/, which has only POL-000 and
would confound an empty classification with "no governing clause"; plan R1).

Vehicle: clones the isolated-live-Classifier template of
scripts/smoke_tests/coordinator_live/g2b_mcp_middle_live.py (Arm E). It IMPORTS
the production stage driver / options / prompt builder; it does NOT reimplement
them. Inputs are hand-crafted DetectorFinding objects over single-concern
fixtures under eval/experiments/fixtures/ (provenance in README.md).

Outcome classification (per run, against ground truth):
  - correto : non-empty emitted set is a subset of the acceptable token(s)
              (TN: correct == emitted is []).
  - abstem  : emitted == [] when a non-empty category was expected.
  - errado  : emitted is non-empty but not a subset of acceptable (missing the
              token, or a hallucinated/extra category).
  - erro_execucao : the stage raised (SDK error / schema / passthrough). Never
              hidden, never retried.
R6: for the `cpf` cases (L1/L2) the acceptable set is BOTH
{dados_de_identificacao, dados_de_documentos_oficiais} (cpf is legitimately
ambiguous). N1/N2 keep a single strict ground-truth token.

Pre-reqs: authenticated Claude Code session; .mcp.json at repo root.
Run (PowerShell, no WSL):
  uv run python eval/experiments/category_exposure_discriminant.py
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coordinator.config import load_mcp_config
from coordinator.driver import _run_mcp_stage
from coordinator.prompts import build_classifier_prompt
from coordinator.run import _classifier_options
from subagents.classifier.models import ClassifierOutput
from subagents.classifier.passthrough import verify_classifier_passthrough
from subagents.detector.models import DetectorFinding

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CFG = ".mcp.json"
_EVAL_LGPD_ROOT = _PROJECT_ROOT / "policies" / "eval-lgpd"
_EXPOSE_ENV = "POLICY_READER_EXPOSE_CATEGORY_EXAMPLES"
_OUTPUT = Path(__file__).resolve().parent / "output" / "discriminant_raw.json"

# cpf is legitimately ambiguous between these two categories (R6).
_IDENT_PAIR = frozenset({"dados_de_identificacao", "dados_de_documentos_oficiais"})


@dataclass
class Case:
    case_id: str
    label: str
    k: int
    finding: DetectorFinding
    acceptable: frozenset[str]
    expect_empty: bool = False


def _matrix() -> list[Case]:
    return [
        Case(
            case_id="L1-cpf-bare",
            label="literal baseline: bare `cpf` parameter (G3 case)",
            k=3,
            acceptable=_IDENT_PAIR,
            finding=DetectorFinding(
                file="eval/experiments/fixtures/l1_bare_cpf.py",
                line=9,
                rule_id="br-cpf",
                snippet="def collect(cpf):",
                surrounding_context=(
                    "def collect(cpf):\n"
                    "    return cpf\n"
                    "# Identificador oficial (cpf) como parametro nu; "
                    "nenhum outro campo no escopo."
                ),
            ),
        ),
        Case(
            case_id="L2-cpf-rich",
            label="literal, rich model: `cpf` among identification fields",
            k=3,
            acceptable=_IDENT_PAIR,
            finding=DetectorFinding(
                file="eval/experiments/fixtures/l2_rich_identification.py",
                line=15,
                rule_id="br-cpf",
                snippet="    cpf: str",
                surrounding_context=(
                    "class UserRegistration(BaseModel):\n"
                    "    nome: str\n"
                    "    username: str\n"
                    "    data_de_nascimento: str\n"
                    "    cpf: str\n"
                    "# Modelo de cadastro: campos de identificacao do titular."
                ),
            ),
        ),
        Case(
            case_id="N1-behavioral",
            label="non-literal: behavioral fields -> perfil_comportamental",
            k=5,
            acceptable=frozenset({"dados_de_perfil_comportamental"}),
            finding=DetectorFinding(
                file="eval/experiments/fixtures/n1_behavioral.py",
                line=14,
                rule_id="experiment-probe",
                snippet="    tracking_id: str",
                surrounding_context=(
                    "class BehaviorEvent:\n"
                    "    tracking_id: str\n"
                    "    cookie_id: str\n"
                    "    historico_navegacao: str\n"
                    "    segmento_marketing: str\n"
                    "# Modelo de eventos de comportamento para analytics."
                ),
            ),
        ),
        Case(
            case_id="N2-location",
            label="non-literal: location fields -> dados_de_localizacao",
            k=5,
            acceptable=frozenset({"dados_de_localizacao"}),
            finding=DetectorFinding(
                file="eval/experiments/fixtures/n2_location.py",
                line=11,
                rule_id="experiment-probe",
                snippet=(
                    "def track_location(latitude: float, longitude: float, "
                    "ip_address: str) -> dict:"
                ),
                surrounding_context=(
                    "def track_location(latitude, longitude, ip_address):\n"
                    "    return {\n"
                    "        'latitude': latitude,\n"
                    "        'longitude': longitude,\n"
                    "        'ip_address': ip_address,\n"
                    "        'geo_ip': True,\n"
                    "    }"
                ),
            ),
        ),
        Case(
            case_id="TN-generic",
            label="true-negative control: generic attribute -> [] (abstain)",
            k=5,
            acceptable=frozenset(),
            expect_empty=True,
            finding=DetectorFinding(
                file="eval/experiments/fixtures/tn_generic_helper.py",
                line=12,
                rule_id="experiment-probe",
                snippet="    tmp = obj.name",
                surrounding_context=(
                    "def helper(obj):\n"
                    "    # Helper interno; obj e um objeto generico de "
                    "dominio, name pode ou nao ser dado pessoal.\n"
                    "    tmp = obj.name\n"
                    "    return tmp"
                ),
            ),
        ),
    ]


def _classify(emitted: list[str], case: Case) -> str:
    s = set(emitted)
    if case.expect_empty:
        return "correto" if not s else "errado"
    if not s:
        return "abstem"
    return "correto" if s <= set(case.acceptable) else "errado"


def _confirm_exposure_delta() -> None:
    """In-process, NO model call: prove the only difference between C1 and C2 is
    the presence of canonical_examples (the names are identical)."""
    from mcp_servers.policy_reader import tools
    from mcp_servers.policy_reader.loader import load_policy

    state = load_policy(_EVAL_LGPD_ROOT)
    os.environ.pop(_EXPOSE_ENV, None)
    c1 = tools._data_categories_vocabulary(state)
    os.environ[_EXPOSE_ENV] = "1"
    c2 = tools._data_categories_vocabulary(state)
    os.environ.pop(_EXPOSE_ENV, None)

    c1_names = [v["name"] for v in c1["values"]]
    c2_names = [v["name"] for v in c2["values"]]
    c1_has_ex = any("canonical_examples" in v for v in c1["values"])
    c2_has_ex = all("canonical_examples" in v for v in c2["values"])
    print(f"[exposure-delta] C1 names ({len(c1_names)}): {c1_names}")
    print(f"[exposure-delta] C1 carries canonical_examples: {c1_has_ex}")
    print(f"[exposure-delta] C2 carries canonical_examples (all entries): {c2_has_ex}")
    assert c1_names == c2_names, "names differ between conditions (must be identical)"
    assert not c1_has_ex, "C1 must be names-only"
    assert c2_has_ex, "C2 must carry canonical_examples on every entry"
    print("[exposure-delta] CONFIRMED: only canonical_examples presence differs.\n")


async def _run_one(case: Case, condition: str, idx: int) -> tuple[list[str], str]:
    cfg = load_mcp_config(_CFG)
    run_path = Path(tempfile.mkdtemp(prefix=f"exp-{case.case_id}-{condition}-"))
    try:
        out = await _run_mcp_stage(
            stage="classifier",
            prompt=build_classifier_prompt([case.finding]),
            options=_classifier_options(cfg),
            output_model=ClassifierOutput,
            scratchpad_name="classifier.json",
            run_path=run_path,
            run_id=f"exp-{case.case_id}-{condition}-{idx}",
            target="policy-reader",
            verify_passthrough=verify_classifier_passthrough,
            upstream=[case.finding],
        )
    except Exception as exc:  # honest capture: never hidden, never retried
        return [], f"erro_execucao: {type(exc).__name__}: {exc}"
    assert isinstance(out, ClassifierOutput)
    emitted = (
        list(out.classified[0].structured_context.data_categories)
        if out.classified
        else []
    )
    return emitted, _classify(emitted, case)


def _dist(outcomes: list[str]) -> str:
    norm = ["erro_exec" if o.startswith("erro_execucao") else o for o in outcomes]
    counts = Counter(norm)
    flag = "  <<INCONSIST" if len({*norm}) > 1 else ""
    body = " ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
    return body + flag


def _print_table(cases: list[Case], raw: dict[str, Any]) -> None:
    print("\n" + "=" * 78)
    print("RESULTS — outcome distribution over K runs per (case x condition)")
    print("(NO conclusion drawn here — raw numbers only)")
    print("=" * 78)
    for case in cases:
        c = raw["cases"][case.case_id]
        gt = "[] (abstain)" if case.expect_empty else " | ".join(sorted(case.acceptable))
        print(f"\n{case.case_id}  (K={case.k})  GT: {gt}")
        print(f"    C1 names-only      : {_dist(c['C1']['outcomes'])}")
        print(f"    C2 names+examples  : {_dist(c['C2']['outcomes'])}")


def _save(raw: dict[str, Any]) -> None:
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")


async def _main() -> int:
    if not _EVAL_LGPD_ROOT.is_dir():
        print(f"FATAL: eval-lgpd root not found: {_EVAL_LGPD_ROOT}")
        return 2
    os.environ["POLICY_READER_ROOT"] = str(_EVAL_LGPD_ROOT)
    print(f"[root] POLICY_READER_ROOT = {os.environ['POLICY_READER_ROOT']}")
    _confirm_exposure_delta()

    cases = _matrix()
    raw: dict[str, Any] = {
        "policy_reader_root": str(_EVAL_LGPD_ROOT),
        "conditions": {
            "C1": "names-only (production default)",
            "C2": "names + canonical_examples (experiment-only env var)",
        },
        "cases": {
            case.case_id: {
                "label": case.label,
                "k": case.k,
                "ground_truth": (
                    "[] (abstention)"
                    if case.expect_empty
                    else sorted(case.acceptable)
                ),
                "C1": {"runs": [], "outcomes": []},
                "C2": {"runs": [], "outcomes": []},
            }
            for case in cases
        },
    }

    total_calls = 0
    for condition in ("C1", "C2"):
        if condition == "C2":
            os.environ[_EXPOSE_ENV] = "1"
        else:
            os.environ.pop(_EXPOSE_ENV, None)
        env_state = os.environ.get(_EXPOSE_ENV, "<unset>")
        print(f"\n=== Condition {condition}  ({_EXPOSE_ENV}={env_state}) ===")
        for case in cases:
            for idx in range(case.k):
                emitted, outcome = await _run_one(case, condition, idx)
                total_calls += 1
                raw["cases"][case.case_id][condition]["runs"].append(emitted)
                raw["cases"][case.case_id][condition]["outcomes"].append(outcome)
                print(f"  [{condition}] {case.case_id} {idx + 1}/{case.k}: "
                      f"{emitted}  ->  {outcome}")

    raw["total_model_calls"] = total_calls
    _print_table(cases, raw)
    _save(raw)
    print(f"\n[done] policy root in use : {_EVAL_LGPD_ROOT}")
    print(f"[done] total model calls  : {total_calls}")
    print(f"[done] raw data saved     : {_OUTPUT}")
    print("[done] NO conclusion drawn here — the reading is for the Chat, over "
          "the raw numbers above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
