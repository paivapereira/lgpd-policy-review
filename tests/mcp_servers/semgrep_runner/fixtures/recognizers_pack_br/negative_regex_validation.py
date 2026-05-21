"""Synthetic fixture — false positive control: regex pattern literals used
for input validation.

Recognizer rules MUST NOT match this snippet because the strings are regex
pattern literals embedded inside validation logic, not values flowing into
a collection sink. Although the patterns describe the canonical format of
Brazilian identifiers, no identifier value is being collected here — the
module only checks format conformance.

This negative exercises AS-7 of T07.
"""

import re

CPF_REGEX = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
CNPJ_REGEX = re.compile(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")
CNH_REGEX = re.compile(r"^\d{11}$")


def is_valid_cpf_format(value: str) -> bool:
    """Check whether a string matches the canonical CPF format. No collection."""
    return bool(CPF_REGEX.match(value))


def is_valid_cnpj_format(value: str) -> bool:
    """Check whether a string matches the canonical CNPJ format. No collection."""
    return bool(CNPJ_REGEX.match(value))


def is_valid_cnh_format(value: str) -> bool:
    """Check whether a string matches the canonical CNH format. No collection."""
    return bool(CNH_REGEX.match(value))
