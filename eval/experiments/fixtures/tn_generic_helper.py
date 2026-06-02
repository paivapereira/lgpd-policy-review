"""TN (true-negative control) — a generic attribute access that maps to NO
category. Mirrors the Classifier's own embedded miss-total example.

Correct outcome here is `[]` (abstention), not a category: `obj` is a generic
domain object and `name` may or may not be personal data in this context. Read
(not executed) by the Classifier. No real PII.
"""
from __future__ import annotations


def helper(obj):
    # Helper interno; obj e um objeto generico de dominio, name pode ou nao ser
    # dado pessoal neste contexto generico.
    tmp = obj.name
    return tmp
