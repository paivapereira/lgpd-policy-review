"""Startup loader for the policy-reader MCP server.

Reads the Policy artefact (`policy.yaml` + `clauses/*.yaml` +
`vocabularies/<framework>/*.yaml`) into validated Pydantic models,
performs cross-file validation against `policy/SCHEMA.md`, and returns a
`LoadedPolicy` consumed by the resource/tool handlers registered in
`server.py`.

All failures raise `PolicyLoadError` with a Portuguese message identifying
the offending file and the SCHEMA rule violated. The bootstrap layer in
`server.py` translates that exception into a non-zero exit before
`mcp.run()` is reached — see canonical.md §6.5 ("Política sem alteração de
versão durante execução"): I/O failures belong to startup, not runtime.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version
from pydantic import ValidationError

from .errors import PolicyLoadError
from .models import (
    Clause,
    DefinitionalClause,
    LoadedPolicy,
    PolicyHeader,
    StatutoryReferenceEntry,
    SubstantiveClause,
    Vocabulary,
)

# Structural range this component implementation knows how to serve. Stored
# as `packaging.SpecifierSet` for compatibility with the canonical semver
# vocabulary; the str form (">=0.1.0,<0.2.0") is what gets exposed via the
# `policy://schema-version` resource per `docs/tasks.md` T01.
COMPATIBLE_SCHEMA_RANGE: SpecifierSet = SpecifierSet(">=0.1.0,<0.2.0")

_VOCABULARY_FILES: tuple[str, ...] = (
    "operation",
    "lawful_basis",
    "control",
    "out_of_scope",
)


def resolve_policy_root(explicit: Path | None = None) -> Path:
    """Resolve the Policy root directory. Precedence: explicit argument >
    `POLICY_READER_ROOT` env var > `<repo>/policy` discovered from
    `__file__`. The env var path is the recommended hook for test fixtures
    and for the GDPR substitution exercise in T04 AS-5.
    """
    if explicit is not None:
        return explicit
    env = os.environ.get("POLICY_READER_ROOT")
    if env:
        return Path(env)
    # src/mcp_servers/policy_reader/loader.py → parents[3] is repo root
    return Path(__file__).resolve().parents[3] / "policy"


def _read_yaml(path: Path) -> Any:
    if not path.is_file():
        raise PolicyLoadError(
            f"Arquivo da Política ausente ou não é arquivo regular: {path}",
        )
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise PolicyLoadError(
            f"YAML inválido em {path}: {exc}",
        ) from exc


def _load_header(root: Path) -> PolicyHeader:
    raw = _read_yaml(root / "policy.yaml")
    if not isinstance(raw, dict):
        raise PolicyLoadError(
            "policy.yaml deve ser um mapeamento YAML no nível superior "
            "(SCHEMA §3.1)",
        )
    try:
        header = PolicyHeader.model_validate(raw)
    except ValidationError as exc:
        raise PolicyLoadError(
            f"Header inválido em policy.yaml (SCHEMA §3.1): {exc}",
        ) from exc

    try:
        header_version = Version(header.policy_schema_version)
    except InvalidVersion as exc:
        raise PolicyLoadError(
            f"policy_schema_version inválida no header: "
            f"{header.policy_schema_version!r} ({exc})",
        ) from exc

    if header_version not in COMPATIBLE_SCHEMA_RANGE:
        raise PolicyLoadError(
            f"policy_schema_version {header.policy_schema_version!r} no "
            f"header está fora de compatible_schema_range "
            f"({COMPATIBLE_SCHEMA_RANGE}) — esta implementação do "
            "policy-reader não serve esta Política (SCHEMA §3.2)",
        )

    return header


def _load_vocabularies(
    root: Path, framework: str,
) -> dict[str, Vocabulary]:
    vocab_dir = root / "vocabularies" / framework
    if not vocab_dir.is_dir():
        raise PolicyLoadError(
            f"Diretório de vocabulários jurisdicionais ausente: {vocab_dir} "
            f"(esperado para legal_framework={framework!r}, SCHEMA §10.1)",
        )

    loaded: dict[str, Vocabulary] = {}
    for name in _VOCABULARY_FILES:
        path = vocab_dir / f"{name}.yaml"
        if not path.is_file():
            raise PolicyLoadError(
                f"Arquivo de vocabulário jurisdicional ausente: "
                f"{name}.yaml em {vocab_dir} (SCHEMA §10.1)",
            )
        raw = _read_yaml(path)
        if not isinstance(raw, dict):
            raise PolicyLoadError(
                f"{path} deve ser um mapeamento YAML no nível superior "
                "(SCHEMA §10.2)",
            )
        try:
            vocab = Vocabulary.model_validate(raw)
        except ValidationError as exc:
            raise PolicyLoadError(
                f"Vocabulário inválido em {path} (SCHEMA §10.2): {exc}",
            ) from exc
        if vocab.framework != framework:
            raise PolicyLoadError(
                f"Vocabulário em {path} declara framework="
                f"{vocab.framework!r}, divergente do legal_framework="
                f"{framework!r} do header (SCHEMA §10.2)",
            )
        loaded[name] = vocab

    return loaded


def _validate_clause_schema_version(clause: Clause) -> None:
    """AS-4: each clause carries a redundant `policy_schema_version` field
    (SCHEMA §4.5). Divergence outside `compatible_schema_range` aborts
    loading. Header has already been checked against the same range in
    `_load_header`, so this validates structural compatibility of every
    clause with the component implementation.
    """
    try:
        clause_version = Version(clause.policy_schema_version)
    except InvalidVersion as exc:
        raise PolicyLoadError(
            f"Cláusula {clause.clause_id}: policy_schema_version inválida "
            f"{clause.policy_schema_version!r} ({exc})",
        ) from exc
    if clause_version not in COMPATIBLE_SCHEMA_RANGE:
        raise PolicyLoadError(
            f"Cláusula {clause.clause_id}: policy_schema_version "
            f"{clause.policy_schema_version!r} fora de "
            f"compatible_schema_range ({COMPATIBLE_SCHEMA_RANGE}) — "
            "divergência incompatível cláusula × header (SCHEMA §4.5)",
        )


def _collect_statutory_references(
    clause: Clause,
) -> list[tuple[str, StatutoryReferenceEntry]]:
    """Walk every `statutory_reference` reachable from a clause (top-level
    and nested in `defines.entries[]` / `out_of_scope[]` for definitional
    clauses), returning a list of `(location, entry)` pairs so the
    cross-file validator can name the offending site in error messages.
    """
    refs: list[tuple[str, StatutoryReferenceEntry]] = []

    for entry in clause.statutory_reference:
        refs.append(("statutory_reference top-level", entry))

    if isinstance(clause, DefinitionalClause):
        entries = clause.defines.get("entries", []) if isinstance(
            clause.defines, dict,
        ) else []
        if isinstance(entries, list):
            for idx, defn_entry in enumerate(entries):
                if not isinstance(defn_entry, dict):
                    continue
                nested = defn_entry.get("statutory_reference", [])
                if not isinstance(nested, list):
                    continue
                for raw_ref in nested:
                    try:
                        parsed = StatutoryReferenceEntry.model_validate(raw_ref)
                    except ValidationError as exc:
                        raise PolicyLoadError(
                            f"Cláusula {clause.clause_id}: "
                            f"defines.entries[{idx}].statutory_reference "
                            f"contém entrada inválida — {exc}",
                        ) from exc
                    refs.append(
                        (
                            f"defines.entries[{idx}].statutory_reference",
                            parsed,
                        ),
                    )

        for idx, oos in enumerate(clause.out_of_scope):
            nested = oos.get("statutory_reference", [])
            if not isinstance(nested, list):
                continue
            for raw_ref in nested:
                try:
                    parsed = StatutoryReferenceEntry.model_validate(raw_ref)
                except ValidationError as exc:
                    raise PolicyLoadError(
                        f"Cláusula {clause.clause_id}: "
                        f"out_of_scope[{idx}].statutory_reference contém "
                        f"entrada inválida — {exc}",
                    ) from exc
                refs.append(
                    (f"out_of_scope[{idx}].statutory_reference", parsed),
                )

    return refs


def _validate_clause_laws(
    clause: Clause, accepted: list[str],
) -> None:
    """AS-5: every `lei` cited in any `statutory_reference` (including
    nested ones) must be in the header's `accepted_law_identifiers`
    (SCHEMA §7, ADR-0005 Decision 1).
    """
    accepted_set = set(accepted)
    for location, entry in _collect_statutory_references(clause):
        if entry.lei not in accepted_set:
            raise PolicyLoadError(
                f"Cláusula {clause.clause_id}: {location} cita lei "
                f"{entry.lei!r}, fora de accepted_law_identifiers="
                f"{sorted(accepted_set)} (SCHEMA §7)",
            )


def _load_clauses(
    root: Path, accepted: list[str],
) -> dict[str, Clause]:
    clauses_dir = root / "clauses"
    if not clauses_dir.is_dir():
        raise PolicyLoadError(
            f"Diretório de cláusulas ausente: {clauses_dir} (SCHEMA §2)",
        )
    clause_files = sorted(clauses_dir.glob("POL-*.yaml"))
    if not clause_files:
        raise PolicyLoadError(
            "Política sem cláusulas é configuração inválida do artefato "
            f"(diretório {clauses_dir} sem POL-*.yaml; canonical §3.1)",
        )

    loaded: dict[str, Clause] = {}
    for path in clause_files:
        raw = _read_yaml(path)
        if not isinstance(raw, dict):
            raise PolicyLoadError(
                f"{path} deve ser um mapeamento YAML no nível superior "
                "(SCHEMA §4)",
            )
        clause_type = raw.get("clause_type")
        try:
            if clause_type == "definitional":
                clause: Clause = DefinitionalClause.model_validate(raw)
            elif clause_type == "substantive":
                clause = SubstantiveClause.model_validate(raw)
            else:
                raise PolicyLoadError(
                    f"{path}: clause_type {clause_type!r} inválido — "
                    "esperado 'definitional' ou 'substantive' (SCHEMA §4.3)",
                )
        except ValidationError as exc:
            raise PolicyLoadError(
                f"Cláusula inválida em {path}: {exc}",
            ) from exc

        if clause.clause_id in loaded:
            raise PolicyLoadError(
                f"clause_id duplicado: {clause.clause_id} aparece em "
                f"{path} e em outro arquivo já carregado",
            )

        _validate_clause_schema_version(clause)
        _validate_clause_laws(clause, accepted)
        loaded[clause.clause_id] = clause

    return loaded


def load_policy(root: Path) -> LoadedPolicy:
    """Read and validate the Policy artefact rooted at `root`.

    Order of validation (fail-fast on first failure of each step):
        1. header file present, parseable, valid against `PolicyHeader`,
           `policy_schema_version` within `COMPATIBLE_SCHEMA_RANGE`
        2. jurisdictional vocabulary files present (one per name in
           `_VOCABULARY_FILES`), parseable, valid against `Vocabulary`,
           `framework` matches header's `legal_framework`
        3. clauses dir non-empty, every YAML parseable, valid against the
           discriminated `Clause` union, redundant `policy_schema_version`
           within the same range, every `lei` (top-level and nested) in
           `header.accepted_law_identifiers`
    """
    header = _load_header(root)
    vocabularies = _load_vocabularies(root, header.legal_framework)
    clauses = _load_clauses(root, header.accepted_law_identifiers)
    return LoadedPolicy(
        header=header,
        clauses=clauses,
        vocabularies=vocabularies,
    )
