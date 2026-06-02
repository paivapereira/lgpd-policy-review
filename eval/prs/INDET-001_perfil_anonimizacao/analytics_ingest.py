"""Synthetic PR — INDET-001 (indeterminate).

Collects behavioral-profile data (tracking_id, browsing events) for analytics.
The clause POL-006 (anonymization_required) governs dados_de_perfil_comportamental
x collection; the engine cannot observe whether effective anonymization happened
upstream, so it returns indeterminate with verification_scope.

DETECTION CAVEAT (reported as a finding): behavioral fields are NOT covered by
the 6 BR Semgrep recognizers (which match cpf/cnpj/cnh/nis/titulo_eleitor/
cns_saude). So in the FULL pipeline this PR needs a BR trigger to produce a
candidate at all — here a `cpf` parameter is included as the user key. At the
ENGINE level the harness supplies data_categories=[dados_de_perfil_comportamental]
directly. See open tension "RF-002 coverage of behavioral data".

NOTE: CPF below is a synthetic, non-real value (privacy-safety rule).
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BehaviorEvent(Base):
    __tablename__ = "behavior_events"

    id = Column(Integer, primary_key=True)
    tracking_id = Column(String(64))      # perfil comportamental
    cookie_id = Column(String(64))        # perfil comportamental
    historico_navegacao = Column(String)  # perfil comportamental
    segmento_marketing = Column(String)   # inferência comportamental


def ingest_profile(cpf: str, tracking_id: str, eventos: list[str]) -> None:
    # Coleta de perfil comportamental para formação de perfil (Art. 12, §2º).
    # A anonimização efetiva (se houver) ocorre em pipeline upstream — não
    # observável neste diff. Comentário declara intenção, não prova:
    # transformacao: "anonimizado no pipeline de ingestao"  (NAO verificavel)
    event = BehaviorEvent(tracking_id=tracking_id)
    _ = (cpf, eventos, event)
