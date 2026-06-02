"""Synthetic PR — VIOL-001 (violation_candidate). E2E showcase.

Collects identification data (and a CPF) with NO declared lawful basis.
The `cpf` parameter triggers `br-cpf`; the Classifier surfaces
dados_de_identificacao and finds NO declared legal basis (declared_legal_basis
= null).

Governing clause: POL-005 (consent_required, dados_de_identificacao x
collection). Expected verdict: violation_candidate (omission of legal_basis),
contradicted_requirement R1. This is the "planted violation" the thesis
end-to-end criterion describes (DESIGN.md:53 — persistir dado sem base).

NOTE: CPF below is a synthetic, non-real value (privacy-safety rule).
"""
from __future__ import annotations

from django.db import models


class Lead(models.Model):
    """Captura de lead de marketing — nenhuma base legal declarada."""

    nome = models.CharField(max_length=200)
    nome_social = models.CharField(max_length=200, blank=True)
    data_de_nascimento = models.DateField()


def capture_lead(nome: str, cpf: str, data_de_nascimento: str) -> Lead:
    # Sem declaração de base legal: coleta de dados de identificação para
    # marketing sem consentimento nem outra hipótese do Art. 7º.
    lead = Lead(nome=nome, data_de_nascimento=data_de_nascimento)
    lead.save()
    return lead
