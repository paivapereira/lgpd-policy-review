"""Synthetic fixture — CPF collection via function parameter naming.

Pattern (a) of recognizers_pack_br: parameter naming.

Synthetic CPF: 238.547.961-37 (algorithmically valid check digits over an
arbitrary base; see README.md §Identificadores sintéticos for provenance).
"""


def create_user_account(cpf: str, full_name: str, email: str) -> dict:
    """Persist a new user with the given CPF and contact details."""
    return {"cpf": cpf, "full_name": full_name, "email": email}


user = create_user_account(
    cpf="238.547.961-37",
    full_name="Synthetic User",
    email="user@example.test",
)
