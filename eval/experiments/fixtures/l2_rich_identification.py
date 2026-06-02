"""L2 (literal, rich model) — `cpf` as a named field amid identification fields.

Mirrors eval/prs/COMP-001_identificacao_consent/users.py (single concern:
identification data; no behavioral/location/health fields). No real PII. Read
(not executed) by the Classifier in the category-exposure discriminant.
"""
from __future__ import annotations

from pydantic import BaseModel


class UserRegistration(BaseModel):
    nome: str
    username: str
    data_de_nascimento: str
    cpf: str
