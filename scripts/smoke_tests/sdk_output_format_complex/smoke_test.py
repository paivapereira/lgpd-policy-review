"""Smoke-test DD-T16 — output_format aceita schema complexo (uniao no root, $defs)?

O sdk_output_format_lockdown provou que output_format funciona com schema FLAT
(TriagerDecisionStub, 2 campos). DD-T16 (triager.md:198, aberto) pergunta o que o
lockdown NAO cobriu: o SDK aceita JSON Schema complexo no output_format? Tres
construcoes que os subagentes Branch B (incl. Matcher) vao precisar:

  A) uniao discriminada no ROOT (TriagerDecision = Proceed | Skip) -> oneOf/anyOf
     + discriminator no topo. Maior risco: structured output costuma restringir
     o root a objeto.
  B) $defs + anyOf aninhado (ClassifierOutput: findings[Finding] com Optional[str])
     -> $defs/Finding, anyOf [string,null].
  C) uniao EMBRULHADA num objeto ({result: Proceed|Skip}) -> fallback prescrito se
     A falhar. Testado proativamente: se A falha e C passa, a receita ja esta dada.

Decide o desenho da saida do Matcher (verdicts nos 4 tipos) ANTES de autorar matcher.md.

AVISO: teste de DESCOBERTA. Ler o structured_output no DUMP, nao so o exit/verdict
(licao das v3/v4: auto-veredito mente). Os modelos sao STAND-INS estruturais —
produzem as MESMAS construcoes JSON Schema dos reais (uniao no root, $defs, anyOf),
mas nao sao o TriagerDecision/ClassifierOutput verbatim. Trocar pelos reais quando
codados para fidelidade exata; a pergunta ESTRUTURAL de DD-T16 ja e respondida aqui.

Execucao (PowerShell):
    uv run --with claude-agent-sdk==0.2.87 python \\
        scripts\\smoke_tests\\sdk_output_format_complex\\smoke_test.py

Auth: Claude Code CLI. Config espelha sdk_output_format_lockdown (lockdown total,
sem betas, permission_mode dontAsk) — fiel ao que ja convergiu no flat.
"""

from __future__ import annotations

import asyncio
import sys
import traceback
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, TypeAdapter


# --- Stand-ins estruturais (NAO os modelos reais; mesma forma de schema) ---- #

class Proceed(BaseModel):
    decision: Literal["proceed"]
    rationale: str


class Skip(BaseModel):
    decision: Literal["skip"]
    rationale: str


TriagerUnion = Annotated[Union[Proceed, Skip], Field(discriminator="decision")]
SCHEMA_A = TypeAdapter(TriagerUnion).json_schema()            # uniao no root


class Finding(BaseModel):
    rule_id: str
    data_categories: list[str]
    snippet: Optional[str] = None                              # -> anyOf [string, null]
    relevance_summary: Optional[str] = None


class ClassifierOutput(BaseModel):
    findings: list[Finding]                                    # -> $defs/Finding
    provenance: dict


SCHEMA_B = ClassifierOutput.model_json_schema()                # $defs + anyOf aninhado


class TriagerWrapped(BaseModel):
    result: TriagerUnion                                       # uniao embrulhada


SCHEMA_C = TriagerWrapped.model_json_schema()


def banner(t: str) -> None:
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def sub(t: str) -> None:
    print("\n" + "-" * 70 + f"\n{t}\n" + "-" * 70)


SCENARIOS = [
    ("A_root_union", SCHEMA_A,
     "Decida proceed ou skip para o diff trivial 'docs: typo fix'. Devolva a decisao estruturada."),
    ("B_defs_nested", SCHEMA_B,
     "Liste achados de PII para um trecho contendo um CPF. Devolva findings + provenance estruturados."),
    ("C_wrapped_union", SCHEMA_C,
     "Decida proceed ou skip para o diff trivial 'docs: typo fix'. Devolva o resultado em 'result'."),
]


async def probe(name: str, schema: dict, prompt: str) -> dict:
    from claude_agent_sdk import ClaudeAgentOptions, query

    sub(f"CENARIO {name}")
    # Gate 1 — init aceita o schema?
    try:
        options = ClaudeAgentOptions(
            system_prompt="Devolva apenas JSON estruturado conforme o schema.",
            allowed_tools=[],
            permission_mode="dontAsk",
            setting_sources=[],
            strict_mcp_config=True,
            mcp_servers={},
            max_turns=20,  # folga p/ validation-retry interno do SDK (SF-3 do lockdown)
            output_format={"type": "json_schema", "schema": schema},
        )
    except Exception as exc:
        print(f"  INIT RAISED: {type(exc).__name__}: {exc}")
        return {"name": name, "init_raised": repr(exc)}

    final_subtype = None
    structured = None
    raised = None
    try:
        async for msg in query(prompt=prompt, options=options):
            mt = type(msg).__name__
            st = getattr(msg, "subtype", "")
            so = getattr(msg, "structured_output", None)
            print(f"  msg {mt} subtype={st!r} structured_output={so!r}")
            if mt == "ResultMessage":
                final_subtype = st
                structured = so
    except Exception as exc:
        raised = repr(exc)
        traceback.print_exc()

    # bug #571: output embrulhado em {"output": {...}}
    wrapped = isinstance(structured, dict) and set(structured.keys()) == {"output"}
    target = structured.get("output") if wrapped else structured

    # valida contra o modelo (best-effort; ler o raw no dump tambem)
    validates = None
    if target is not None and final_subtype == "success":
        try:
            if name == "B_defs_nested":
                ClassifierOutput.model_validate(target)
            elif name == "C_wrapped_union":
                TriagerWrapped.model_validate(target)
            else:
                TypeAdapter(TriagerUnion).validate_python(target)
            validates = True
        except Exception as exc:
            validates = f"FALHA: {type(exc).__name__}: {exc}"

    return {"name": name, "subtype": final_subtype, "structured": structured,
            "wrapped": wrapped, "validates": validates, "raised": raised}


def verdict_for(r: dict) -> str:
    if r.get("init_raised"):
        return "REJEITADO_INIT — SDK recusou o shape na construcao do ClaudeAgentOptions."
    if r.get("raised"):
        return "INDETERMINADO — query levantou; ler traceback."
    st = r.get("subtype")
    if st == "success" and r.get("validates") is True and not r.get("wrapped"):
        return "ACEITO — converge para success e valida contra o schema."
    if st == "success" and r.get("wrapped"):
        return "ACEITO_COM_WRAP — converge, mas embrulhado em {'output':...} (bug #571); precisa unwrap."
    if st == "success":
        return f"SUCCESS_MAS_NAO_VALIDA — success mas structured nao casa o schema: {r.get('validates')}"
    if st == "error_max_structured_output_retries":
        return "NAO_CONVERGE — SDK aceita o param mas nao converge neste shape (retries esgotados)."
    return f"INCONCLUSIVO — subtype={st!r}; ler structured_output no dump."


async def main() -> int:
    banner("DD-T16 — output_format com schema complexo (uniao no root, $defs)")
    try:
        import claude_agent_sdk  # noqa: F401
    except Exception as exc:
        print(f"IMPORT FAIL: {exc}")
        return 4

    results = [await probe(n, s, p) for n, s, p in SCENARIOS]

    sub("VEREDITOS POR CENARIO")
    vmap = {}
    for r in results:
        v = verdict_for(r)
        vmap[r["name"]] = v
        print(f"  {r['name']}: {v}")

    sub("SINTESE DD-T16 (para o desenho da saida do Matcher)")
    a, c = vmap["A_root_union"], vmap["C_wrapped_union"]
    if a.startswith("ACEITO"):
        print("UNIAO NO ROOT ACEITA -> TriagerDecision e os verdicts do Matcher podem")
        print("usar uniao discriminada direta no root do output_format. Sem mudanca.")
        union_ok = True
    elif c.startswith("ACEITO"):
        print("UNIAO NO ROOT FALHA, EMBRULHADA FUNCIONA -> PRESCRICAO: envelopar a uniao")
        print("num objeto ({result|verdict: ...}). Matcher E Triager: saida = objeto no")
        print("root, nao uniao. Companion edit a triager.md se o spec assume root union.")
        union_ok = True
    else:
        print("UNIAO NO ROOT E EMBRULHADA FALHAM -> repensar contrato de saida (enum +")
        print("campos opcionais? validation-retry custom?). BLOQUEIA o desenho do Matcher.")
        union_ok = False

    print(f"\n$defs/anyOf aninhado (Classifier/findings): {vmap['B_defs_nested']}")
    defs_ok = vmap["B_defs_nested"].startswith("ACEITO")

    print("\n>>> Ler o structured_output de cada cenario no dump acima; o veredito")
    print(">>> automatico e best-effort e ja mentiu em testes anteriores desta sessao.")
    return 0 if (union_ok and defs_ok) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
