"""Synthetic fixture — false positive control: identifier-shaped strings
used semantically for versioning, release tagging, and build numbering.

Recognizer rules `br-cpf`, `br-cnpj`, `br-cnh`, `br-nis-pis`,
`br-titulo-eleitor`, `br-cns-saude` MUST NOT match this snippet because:

- The variable names (APP_VERSION, RELEASE_TAG, BUILD_NUMBER) are not
  identifier-related.
- The strings are not flowing into a collection sink (function parameter
  named `cpf`/`cnpj`/..., dict key named `cpf`/..., attribute assignment
  to `obj.cpf = ...`, or structured log payload keyword).

This negative exercises AS-7 of T07: pattern-based Semgrep rules must
distinguish syntactic format from semantic context.

Note (design intencional): `238.547.961-37` e `47.861.932/0001-92` neste
arquivo são os MESMOS identificadores sintéticos usados em
`br_cpf_function_param.py` e `br_cnpj_dict_key.py` respectivamente.
Reuso deliberado: exerce discriminação por contexto sintático (variable
name + collection sink), não por string content. Não é duplicação acidental.
See README §Identificadores sintéticos compartilhados entre positivos e
negativos for full rationale.
"""

APP_VERSION = "123.456.789-00"  # internal versioning scheme; looks like CPF but is not
RELEASE_TAG = "release-238.547.961-37"  # release tag that embeds a CPF-shaped substring
BUILD_NUMBER = "47.861.932/0001-92"  # build numbering; looks like CNPJ but is not


def get_release_info() -> dict:
    """Return release metadata. Does not collect identifiers."""
    return {"version": APP_VERSION, "tag": RELEASE_TAG, "build": BUILD_NUMBER}
