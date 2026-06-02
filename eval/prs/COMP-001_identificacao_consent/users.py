"""Synthetic PR — COMP-001 (compliant).

Collects identification data WITH a declared lawful basis of consent.
The `cpf` parameter triggers the Semgrep recognizer `br-cpf`
(pattern `def $FN(..., cpf: $T, ...)`), so the Detector produces a candidate;
the Classifier, reading this file, surfaces dados_de_identificacao (nome,
username, data_de_nascimento) and the declared legal basis `consent`.

Governing clause (LGPD eval Policy): POL-005 (consent_required,
dados_de_identificacao x collection). Expected verdict: compliant.

NOTE: CPF below is a synthetic, non-real value (privacy-safety rule).
"""
from __future__ import annotations

from pydantic import BaseModel


class UserRegistration(BaseModel):
    nome: str
    username: str
    data_de_nascimento: str
    cpf: str  # documento oficial — gatilho br-cpf no nível de campo Pydantic


def register_user(nome: str, username: str, cpf: str) -> dict[str, str]:
    """Coleta de dados de identificação no cadastro de usuário.

    Base legal: consentimento do titular (LGPD Art. 7º, I) — coletado no
    fluxo de onboarding antes desta chamada.
    """
    # legal_basis: consent  (consentimento do titular, Art. 7, I)
    record = {
        "nome": nome,
        "username": username,
        "cpf": cpf,  # synthetic: "000.000.000-00"
        "legal_basis": "consent",
    }
    return record
