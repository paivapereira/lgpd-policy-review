"""Synthetic PR — PROBE-UNGOV-001 (ungoverned-category probe).

Collects LOCATION data (dados_de_localizacao). NO clause in the eval Policy
governs this category ON PURPOSE — the probe asks what the Matcher does when no
substantive clause governs the candidate. Decision already taken by the author:
KEEP the probe even if it reveals a hole; do NOT "fix" it by authoring a
localizacao clause.

Engine-level finding (verified by the harness sweep): every active clause
returns not_applicable — POL-000 (definitional, ref POL-000) + POL-005/006/007
(category mismatch, each ref its own id). Aggregate -> coverage_gap; the Matcher
(matcher.md DD-M8) would set requires_human_review=true. There is NO orphan
policy_clause_ref: each finding references the clause that was evaluated; POL-000
is the always-present backstop ref. The "hole" is that the gap is a pure
AGGREGATE signal — at the engine level an ungoverned category is
indistinguishable from any other not_applicable mismatch.

The `cpf` parameter triggers `br-cpf` so the full pipeline produces a candidate
(location fields are not BR-recognized — same RF-002 caveat as INDET-001).

NOTE: CPF below is a synthetic, non-real value (privacy-safety rule).
"""
from __future__ import annotations


def track_location(cpf: str, latitude: float, longitude: float, ip_address: str) -> dict:
    # Coleta de dados de localizacao do titular. Nenhuma clausula da Politica
    # de avaliacao governa esta categoria (sonda deliberada).
    return {
        "cpf": cpf,
        "latitude": latitude,
        "longitude": longitude,
        "ip_address": ip_address,
        "geo_ip": True,
    }
