"""Synthetic PR — SWAP-001 (jurisdiction swap; RF-008).

THE SAME CODE is evaluated under two Policies:
  - LGPD eval instance (policies/eval-lgpd/) -> SWAP-001-LGPD -> compliant
  - GDPR twin (policies/eval-gdpr/)          -> SWAP-001-GDPR -> violation_candidate

The flip is driven by the lawful_basis VOCABULARY, not by the code: the LGPD
vocabulary's consent token is `consent`, the GDPR twin's is `consent_gdpr`
(policies/eval-gdpr/vocabularies/GDPR/lawful_basis.yaml). The Classifier normalizes
this code's declared consent to the per-jurisdiction token; the engine compares
by exact equality against the literal `consent` (tools.py:383). So under GDPR
the normalized token `consent_gdpr` != "consent" -> violation_candidate.

This both demonstrates RF-008 (data-driven framework swap) AND reveals that the
engine's consent check is coupled to the LGPD token `consent` (open tension).

The `cpf` parameter triggers `br-cpf`; the Classifier surfaces
dados_de_identificacao. Governing clause: POL-005 in each Policy.

NOTE: CPF below is a synthetic, non-real value (privacy-safety rule).
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class SignupPayload(BaseModel):
    nome: str
    username: str
    data_de_nascimento: str


@app.post("/signup")
def signup(payload: SignupPayload, cpf: str) -> dict[str, str]:
    # Base legal declarada: consentimento do titular.
    # (LGPD Art. 7, I -> token `consent`; GDPR Art. 6(1)(a) -> token
    #  `consent_gdpr` no vocabulario do gemeo GDPR.)
    # legal_basis: consent
    return {"nome": payload.nome, "cpf": cpf, "legal_basis": "consent"}
