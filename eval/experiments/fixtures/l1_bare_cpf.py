"""L1 (literal baseline) — bare `cpf` parameter, the G3 case `def collect(cpf)`.

Single-concern synthetic input: an official-document identifier as a bare
function parameter, no surrounding model fields. No real PII. Read (not executed)
by the Classifier in the category-exposure discriminant experiment.
"""
from __future__ import annotations


def collect(cpf: str) -> str:
    return cpf
