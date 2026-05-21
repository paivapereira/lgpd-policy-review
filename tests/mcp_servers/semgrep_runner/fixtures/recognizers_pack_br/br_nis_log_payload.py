"""Synthetic fixture — NIS/PIS collection via structured log payload.

Pattern (d) of recognizers_pack_br: log payload structured.

Synthetic NIS/PIS: 17293846507 (algorithmically valid check digit over an
arbitrary base; see README.md §Identificadores sintéticos for provenance).
"""

import logging

logger = logging.getLogger(__name__)


def process_benefit_claim(claim: dict) -> None:
    """Process a social benefit claim and emit a structured log record."""
    logger.info(
        "benefit_claim_received",
        nis=claim["nis"],
        amount=claim["amount"],
        claim_type=claim["type"],
    )


process_benefit_claim({
    "nis": "17293846507",
    "amount": 1500.00,
    "type": "auxilio_brasil_synthetic",
})
