"""Pydantic models for the Policy artefact served by policy-reader.

Mirrors `policy/SCHEMA.md`. Models capture only the structure exercised by
T01 (loader + handshake); fields whose detailed shape lives in SCHEMA §6
("Provisório") use loose types so refinement in later tasks (T02a/T02b/T03/T04)
or in Milestone B (when POL-001 is authored) does not become rework.

Naming convention: the field carrying hierarchical legal references is
`statutory_reference` (matches `policy/SCHEMA.md` §5.1/§6.1 and the real
artefact `policy/clauses/POL-000.yaml`). The compact spec still writes
`article_source` in places — that drift is pinned in `docs/tasks.md`
§Companion edits cross-doc and is applied here per `tasks.md` line 7.
"""
from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"
_CLAUSE_ID_PATTERN = r"^POL-\d{3}$"


class StatutoryReferenceEntry(BaseModel):
    """One entry in a `statutory_reference` list (SCHEMA §5.1).

    `lei` membership in the Policy header's `accepted_law_identifiers` is a
    cross-file invariant — validated in `loader.load_policy`, not here, since
    the model has no view of the header.
    """

    model_config = ConfigDict(extra="forbid")

    lei: str = Field(min_length=1)
    artigo: int = Field(ge=1)
    paragrafo: int | None = Field(default=None, ge=1)
    inciso: int | None = Field(default=None, ge=1)
    alinea: str | None = Field(default=None, min_length=1)


class PolicyHeader(BaseModel):
    """Top-level `policy/policy.yaml` (SCHEMA §3)."""

    model_config = ConfigDict(extra="forbid")

    policy_schema_version: Annotated[str, Field(pattern=_SEMVER_PATTERN)]
    policy_version: Annotated[str, Field(pattern=_SEMVER_PATTERN)]
    legal_framework: str = Field(min_length=1)
    accepted_law_identifiers: list[str] = Field(min_length=1)
    policy_owner: str = Field(min_length=1)
    effective_date: date
    last_revision: date

    @model_validator(mode="after")
    def _dates_ordered(self) -> PolicyHeader:
        if self.effective_date > self.last_revision:
            raise ValueError(
                "effective_date não pode ser posterior a last_revision",
            )
        return self


class Vocabulary(BaseModel):
    """One of the four jurisdictional vocabulary files
    (`policy/vocabularies/<framework>/{operation,lawful_basis,control,out_of_scope}.yaml`).

    `framework` consistency with `PolicyHeader.legal_framework` is validated
    cross-file in `loader.load_policy`. Per-vocabulary refinement of
    `values[]` is deferred to T02b/T03/T04 — this task carries only the
    structural envelope of SCHEMA §10.2.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Annotated[str, Field(pattern=_SEMVER_PATTERN)]
    framework: str = Field(min_length=1)
    values: list[dict[str, Any]] = Field(min_length=1)


class Tombstone(BaseModel):
    """Required block when `status == "deprecated"` (SCHEMA §4.6)."""

    model_config = ConfigDict(extra="forbid")

    successors: list[str]
    effective_until: date
    deprecation_reason: str = Field(min_length=1)


class ClauseCommon(BaseModel):
    """Fields shared by every clause in `policy/clauses/*.yaml` (SCHEMA §4)."""

    model_config = ConfigDict(extra="forbid")

    clause_id: Annotated[str, Field(pattern=_CLAUSE_ID_PATTERN)]
    title: str = Field(min_length=1)
    clause_type: Literal["definitional", "substantive"]
    status: Literal["active", "deprecated"] = "active"
    policy_schema_version: Annotated[str, Field(pattern=_SEMVER_PATTERN)]
    statutory_reference: list[StatutoryReferenceEntry] = Field(min_length=1)
    tombstone: Tombstone | None = None

    @model_validator(mode="after")
    def _tombstone_iff_deprecated(self) -> ClauseCommon:
        if self.status == "deprecated" and self.tombstone is None:
            raise ValueError(
                f"Cláusula {self.clause_id} com status 'deprecated' exige "
                "bloco 'tombstone' (SCHEMA §4.6)",
            )
        if self.status == "active" and self.tombstone is not None:
            raise ValueError(
                f"Cláusula {self.clause_id} com status 'active' não pode "
                "carregar bloco 'tombstone' (SCHEMA §4.6)",
            )
        return self


class DefinitionalClause(ClauseCommon):
    """SCHEMA §5. Defines vocabularies (currently only POL-000)."""

    model_config = ConfigDict(extra="forbid")

    clause_type: Literal["definitional"] = "definitional"
    defines: dict[str, Any]
    out_of_scope: list[dict[str, Any]] = Field(default_factory=list)


class SubstantiveClause(ClauseCommon):
    """SCHEMA §6. Prescribes a `control` for a (categories × operation) tuple.

    SCHEMA.md §6 is explicitly marked "Provisório" — refinement waits on
    POL-001 being authored. `extra="allow"` keeps later fields loadable
    without touching this model when SCHEMA §6 stabilises.
    """

    model_config = ConfigDict(extra="allow")

    clause_type: Literal["substantive"] = "substantive"
    applies_to: dict[str, Any]
    control: str
    requirements: list[dict[str, Any]] = Field(default_factory=list)
    exceptions: list[dict[str, Any]] = Field(default_factory=list)


Clause = DefinitionalClause | SubstantiveClause


class LoadedPolicy(BaseModel):
    """Aggregate produced by `loader.load_policy` and consumed by handlers
    registered in `server.py`."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    header: PolicyHeader
    clauses: dict[str, Clause]
    vocabularies: dict[str, Vocabulary]


class ErrorEnvelope(BaseModel):
    """Canonical error envelope shape for tool returns (canonical §5.1).

    Field names are camelCase deliberately — they are JSON keys consumed by
    downstream agents and must match the contract in canonical §5.1 / §5.4
    verbatim. The Python attribute names follow the same casing because
    `model_dump()` is used directly on the wire (no alias indirection).

    Wire-shape convention adopted by this project (Option B from T02a):
    the envelope is serialised into `structuredContent` of the wire
    `CallToolResult`; `content[0].text` reproduces `message` as a human
    fallback; wire `isError` stays `False` and is reserved for protocol-level
    failures (input schema rejection, tool-not-found). Consumers discriminate
    success vs domain error by the presence of `errorCode` in
    `structuredContent`. Canonical §5.1 prescribes `isError: True` for domain
    failures, but FastMCP 3.2.4 has no public path that simultaneously emits
    `isError: True` and a structured payload — pinned as cross-doc debt
    (DD-6 in T02a session notes).
    """

    model_config = ConfigDict(extra="forbid")

    errorCode: str = Field(min_length=1)
    message: str = Field(min_length=1)
    isRetryable: bool
    details: dict[str, Any] = Field(default_factory=dict)
