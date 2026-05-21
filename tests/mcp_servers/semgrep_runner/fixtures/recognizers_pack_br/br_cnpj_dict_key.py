"""Synthetic fixture — CNPJ collection via dict key access.

Pattern (b) of recognizers_pack_br: dict key access.

Synthetic CNPJ: 47.861.932/0001-92 (algorithmically valid check digits over
an arbitrary base; see README.md §Identificadores sintéticos for provenance).
"""


def register_company(payload: dict) -> dict:
    """Register a company from an incoming JSON-like payload."""
    return {
        "cnpj": payload["cnpj"],
        "trade_name": payload["trade_name"],
    }


incoming = {
    "cnpj": "47.861.932/0001-92",
    "trade_name": "Acme Synthetic Ltda",
}
result = register_company(incoming)
