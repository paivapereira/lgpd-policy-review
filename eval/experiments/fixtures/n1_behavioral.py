"""N1 (non-literal inference) — behavioral-profile fields whose NAMES share no
lexical token with the category `dados_de_perfil_comportamental`.

Derived from eval/prs/INDET-001_perfil_anonimizacao/analytics_ingest.py with the
`cpf` trigger REMOVED on purpose: this isolates non-literal behavioral inference
(the discriminating signal). Plain annotated class — no ORM dependency — since
the file is Read (not executed) by the Classifier. No real PII.
"""
from __future__ import annotations


class BehaviorEvent:
    tracking_id: str       # identificador de rastreamento
    cookie_id: str         # identificador de cookie
    historico_navegacao: str
    segmento_marketing: str
