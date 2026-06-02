"""N2 (non-literal inference) — location fields whose NAMES share no lexical
token with the category `dados_de_localizacao`.

Derived from eval/prs/PROBE-UNGOV-001_localizacao/geo.py with the `cpf` trigger
REMOVED on purpose: this isolates non-literal geo inference (the discriminating
signal). Read (not executed) by the Classifier. No real PII.
"""
from __future__ import annotations


def track_location(latitude: float, longitude: float, ip_address: str) -> dict:
    return {
        "latitude": latitude,
        "longitude": longitude,
        "ip_address": ip_address,
        "geo_ip": True,
    }
