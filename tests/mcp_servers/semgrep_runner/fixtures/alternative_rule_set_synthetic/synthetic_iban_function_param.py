"""
Fixture sintetica para gate Milestone B (RF-008 rule-set-axis).

Snippet positivo que dispara a regra synthetic-iban. NAO usa IBAN real --
identificador inventado, sem correspondencia a conta bancaria existente.
Convencao espelha .claude/rules/privacy-safety.md aplicada ao pack BR
(identificadores SINTETICOS apenas, sem dados pessoais reais).
"""


def process_payment(iban: str) -> None:
    """Process payment using customer IBAN."""
    # Coleta de dado pessoal financeiro -- alvo da regra synthetic-iban.
    pass
