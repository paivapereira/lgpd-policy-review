"""Classifier constants — single source for the policy-reader server name and the two
resources the system prompt loads first (classifier.md §5.1).
"""
from __future__ import annotations

POLICY_READER_SERVER = "policy-reader"

# Loaded first via ReadMcpResourceTool (classifier.md §5.1). vocabularies bound the
# valid tokens for operation_type / data_categories / declared_legal_basis; examples are
# optional jurisdictional mapping references (empty/error/absent treated identically).
VOCABULARIES_URI = "policy://vocabularies"
EXAMPLES_URI = "policy://examples"
