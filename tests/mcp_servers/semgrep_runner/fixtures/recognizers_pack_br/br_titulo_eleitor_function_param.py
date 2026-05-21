"""Synthetic fixture — Titulo de Eleitor collection via function parameter naming.

Pattern (a) of recognizers_pack_br: parameter naming.

Synthetic Titulo de Eleitor: 348291670116 (algorithmically valid check digits
over an arbitrary base + UF code 01 = SP; see README.md §Identificadores
sintéticos for provenance).
"""


def verify_voter_registration(titulo_eleitor: str, zone: str) -> bool:
    """Verify whether a voter title is registered in the given zone."""
    return titulo_eleitor[8:10] == zone[:2]


is_valid = verify_voter_registration(
    titulo_eleitor="348291670116",
    zone="01-SP",
)
