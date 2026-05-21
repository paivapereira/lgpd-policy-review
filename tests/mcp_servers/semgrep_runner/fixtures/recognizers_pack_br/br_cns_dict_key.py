"""Synthetic fixture — CNS-saude collection via dict key access.

Pattern (b) of recognizers_pack_br: dict key access.

Synthetic CNS-saude: '163 8492 7503 0003' (algorithmically valid; sum of
digits weighted 15..1 is divisible by 11; see README.md §Identificadores
sintéticos for provenance).
"""


def submit_health_record(patient_data: dict) -> str:
    """Submit a health record to the national health system."""
    cns = patient_data["cns_saude"]
    return f"record_submitted_for_{cns}"


patient = {
    "cns_saude": "163 8492 7503 0003",
    "first_name": "Synthetic",
    "last_name": "Patient",
}
record_id = submit_health_record(patient)
