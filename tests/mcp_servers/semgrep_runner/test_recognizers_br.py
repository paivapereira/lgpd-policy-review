"""Acceptance scenarios for T07 — six Brazilian recognizers (`br-*`) rule pack.

AS-1..AS-9 per `docs/tasks.md` §T07. Subset-assertion style for AS-1..AS-6
per `.claude/rules/test-strategy.md` (acceptance scenarios assert
inclusion, not strict count); AS-7/AS-8/AS-9 admit strict assertions
(empty findings, set membership, byte identity over `findings` list).

Naming convention: `test_as<N>_*` consistent with T05/T06; anchors
labelled by what they validate (`test_anchor_*`).

DD-T07-3a was ratified at GATE 1 to alternative (a) — each `br-*` rule
declares exactly one Semgrep pattern (the Latin-square-validated one
for its identifier). Transitivity to other syntactic contexts is a
documented gap (pendência pós-MVP); see plan doc.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from mcp_servers.semgrep_runner import tools
from mcp_servers.semgrep_runner.loader import load_rules

from .conftest import (
    BR_SLUGS,
    PRODUCTION_RULES_DIR,
    _build_br_rules_dir,
    _build_pack_repo,
)


def _short_rule_id(finding: dict[str, Any]) -> str:
    """Last dot-segment of Semgrep's rule_id (Semgrep prefixes with file path)."""
    rid: str = finding.get("rule_id", "")
    return rid.rsplit(".", 1)[-1] if rid else ""

# Mapping from rule slug to the BR pack fixture that exercises its
# Latin-square-validated pattern.
SLUG_TO_FIXTURE: dict[str, str] = {
    "br_cpf": "br_cpf_function_param.py",
    "br_cnpj": "br_cnpj_dict_key.py",
    "br_cnh": "br_cnh_attribute_assign.py",
    "br_nis_pis": "br_nis_log_payload.py",
    "br_titulo_eleitor": "br_titulo_eleitor_function_param.py",
    "br_cns_saude": "br_cns_dict_key.py",
}

# DD-T07-4: WARNING for five identifiers; ERROR only for br-cns-saude
# (categoria sensível sob LGPD Art. 11).
SLUG_TO_EXPECTED_SEVERITY: dict[str, str] = {
    "br_cpf": "warning",
    "br_cnpj": "warning",
    "br_cnh": "warning",
    "br_nis_pis": "warning",
    "br_titulo_eleitor": "warning",
    "br_cns_saude": "error",
}

# DD-T07-2a: kebab-case rule_id with `br-` prefix.
SLUG_TO_RULE_ID: dict[str, str] = {
    "br_cpf": "br-cpf",
    "br_cnpj": "br-cnpj",
    "br_cnh": "br-cnh",
    "br_nis_pis": "br-nis-pis",
    "br_titulo_eleitor": "br-titulo-eleitor",
    "br_cns_saude": "br-cns-saude",
}

NEGATIVE_FIXTURES: tuple[str, ...] = (
    "negative_regex_validation.py",
    "negative_uuid_constant.py",
    "negative_version_string.py",
)


# ---------------------------------------------------------------------------
# AS-1..AS-6 — positive detection per identifier (subset assertion)
# ---------------------------------------------------------------------------

def test_as1_br_cpf_matches_function_param(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AS-1. The `br-cpf` rule emits at least one finding against
    `br_cpf_function_param.py`, the Latin-square-validated positive
    fixture for CPF (parameter naming pattern). Subset assertion per
    `.claude/rules/test-strategy.md`.
    """
    rules_dir = _build_br_rules_dir(tmp_path, ("br_cpf",))
    repo, base_sha, head_sha = _build_pack_repo(
        tmp_path, ("br_cpf_function_param.py",)
    )
    monkeypatch.chdir(repo)
    state = load_rules(rules_dir)
    result = tools.scan_diff(base_sha, head_sha, state)

    assert result.structured_content is not None
    findings = result.structured_content["findings"]
    rule_ids_short = {_short_rule_id(f) for f in findings}
    assert "br-cpf" in rule_ids_short
    assert any(
        f["location"]["path"] == "br_cpf_function_param.py" for f in findings
    )


def test_as2_br_cnpj_matches_dict_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AS-2. The `br-cnpj` rule emits >=1 finding against
    `br_cnpj_dict_key.py` (dict_key pattern, Latin square).
    """
    rules_dir = _build_br_rules_dir(tmp_path, ("br_cnpj",))
    repo, base_sha, head_sha = _build_pack_repo(
        tmp_path, ("br_cnpj_dict_key.py",)
    )
    monkeypatch.chdir(repo)
    state = load_rules(rules_dir)
    result = tools.scan_diff(base_sha, head_sha, state)
    assert result.structured_content is not None
    findings = result.structured_content["findings"]
    assert "br-cnpj" in {_short_rule_id(f) for f in findings}
    assert any(f["location"]["path"] == "br_cnpj_dict_key.py" for f in findings)


def test_as3_br_cnh_matches_attribute_assign(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AS-3. The `br-cnh` rule emits >=1 finding against
    `br_cnh_attribute_assign.py` (attribute pattern, Latin square). The
    fixture deliberately has two attribute writes to `.cnh` (linha 14
    AnnAssign in `__init__` + linha 21 simple Assign); Semgrep
    `$OBJ.cnh = $V` casa ambos. Subset assertion per
    `.claude/rules/test-strategy.md`.
    """
    rules_dir = _build_br_rules_dir(tmp_path, ("br_cnh",))
    repo, base_sha, head_sha = _build_pack_repo(
        tmp_path, ("br_cnh_attribute_assign.py",)
    )
    monkeypatch.chdir(repo)
    state = load_rules(rules_dir)
    result = tools.scan_diff(base_sha, head_sha, state)
    assert result.structured_content is not None
    findings = result.structured_content["findings"]
    assert "br-cnh" in {_short_rule_id(f) for f in findings}
    assert any(
        f["location"]["path"] == "br_cnh_attribute_assign.py" for f in findings
    )


def test_as4_br_nis_pis_matches_log_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AS-4. The `br-nis-pis` rule emits >=1 finding against
    `br_nis_log_payload.py` (log_payload pattern, Latin square).
    """
    rules_dir = _build_br_rules_dir(tmp_path, ("br_nis_pis",))
    repo, base_sha, head_sha = _build_pack_repo(
        tmp_path, ("br_nis_log_payload.py",)
    )
    monkeypatch.chdir(repo)
    state = load_rules(rules_dir)
    result = tools.scan_diff(base_sha, head_sha, state)
    assert result.structured_content is not None
    findings = result.structured_content["findings"]
    assert "br-nis-pis" in {_short_rule_id(f) for f in findings}
    assert any(f["location"]["path"] == "br_nis_log_payload.py" for f in findings)


def test_as5_br_titulo_eleitor_matches_function_param(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AS-5. The `br-titulo-eleitor` rule emits >=1 finding against
    `br_titulo_eleitor_function_param.py` (parameter pattern, Latin square).
    """
    rules_dir = _build_br_rules_dir(tmp_path, ("br_titulo_eleitor",))
    repo, base_sha, head_sha = _build_pack_repo(
        tmp_path, ("br_titulo_eleitor_function_param.py",)
    )
    monkeypatch.chdir(repo)
    state = load_rules(rules_dir)
    result = tools.scan_diff(base_sha, head_sha, state)
    assert result.structured_content is not None
    findings = result.structured_content["findings"]
    assert "br-titulo-eleitor" in {_short_rule_id(f) for f in findings}
    assert any(
        f["location"]["path"] == "br_titulo_eleitor_function_param.py"
        for f in findings
    )


def test_as6_br_cns_saude_matches_dict_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AS-6. The `br-cns-saude` rule emits >=1 finding against
    `br_cns_dict_key.py` (dict_key pattern, Latin square). Severity ERROR
    per DD-T07-4 (categoria sensível sob LGPD Art. 11); the severity
    invariant itself is anchored at `test_anchor_severity_scheme`.
    """
    rules_dir = _build_br_rules_dir(tmp_path, ("br_cns_saude",))
    repo, base_sha, head_sha = _build_pack_repo(tmp_path, ("br_cns_dict_key.py",))
    monkeypatch.chdir(repo)
    state = load_rules(rules_dir)
    result = tools.scan_diff(base_sha, head_sha, state)
    assert result.structured_content is not None
    findings = result.structured_content["findings"]
    assert "br-cns-saude" in {_short_rule_id(f) for f in findings}
    assert any(f["location"]["path"] == "br_cns_dict_key.py" for f in findings)


# ---------------------------------------------------------------------------
# AS-7 — false positive control (negatives produce zero findings)
# ---------------------------------------------------------------------------

def test_as7_negative_regex_validation_no_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    br_rules_dir: Path,
) -> None:
    """AS-7. All 6 BR rules together must produce zero findings against
    `negative_regex_validation.py` — strings are regex literals inside
    `re.compile` calls, not identifier values flowing to a sink.
    """
    repo, base_sha, head_sha = _build_pack_repo(
        tmp_path, ("negative_regex_validation.py",)
    )
    monkeypatch.chdir(repo)
    state = load_rules(br_rules_dir)
    result = tools.scan_diff(base_sha, head_sha, state)
    assert result.structured_content is not None
    assert result.structured_content["findings"] == []


def test_as7_negative_uuid_constant_no_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    br_rules_dir: Path,
) -> None:
    """AS-7. All 6 BR rules together must produce zero findings against
    `negative_uuid_constant.py` — UUIDs, ISO date ranges, and order
    numbers do not match canonical BR identifier formats AND the variable
    names are not identifier-related.
    """
    repo, base_sha, head_sha = _build_pack_repo(
        tmp_path, ("negative_uuid_constant.py",)
    )
    monkeypatch.chdir(repo)
    state = load_rules(br_rules_dir)
    result = tools.scan_diff(base_sha, head_sha, state)
    assert result.structured_content is not None
    assert result.structured_content["findings"] == []


def test_as7_negative_version_string_no_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    br_rules_dir: Path,
) -> None:
    """AS-7. All 6 BR rules together must produce zero findings against
    `negative_version_string.py` — strongest negative: this file
    deliberately reuses the synthetic CPF/CNPJ strings from positives but
    in non-collection contexts (APP_VERSION, RELEASE_TAG, BUILD_NUMBER).
    Strong AST discrimination signal.
    """
    repo, base_sha, head_sha = _build_pack_repo(
        tmp_path, ("negative_version_string.py",)
    )
    monkeypatch.chdir(repo)
    state = load_rules(br_rules_dir)
    result = tools.scan_diff(base_sha, head_sha, state)
    assert result.structured_content is not None
    assert result.structured_content["findings"] == []


# ---------------------------------------------------------------------------
# AS-8, AS-9 — placeholder removal, idempotency
# ---------------------------------------------------------------------------

def test_as8_placeholder_removed_only_br_rule_ids_in_findings(
    monkeypatch: pytest.MonkeyPatch,
    br_pack_repo: tuple[Path, str, str],
) -> None:
    """AS-8. Two-layer assertion: (1) structural — production rule set
    contains exactly the six `br_*.yaml` files and nothing else (most
    notably no `_placeholder.yaml`); (2) runtime — scanning the full
    pack via production rules yields findings whose rule_ids are all in
    the {br-cpf, ..., br-cns-saude} set, none starting with `_`. The
    structural assertion is the load-bearing one — the runtime check is
    weaker because the T05 placeholder's pattern doesn't match any
    BR-pack snippet, so it would silently pass even if the file
    remained.
    """
    yaml_files = {p.name for p in PRODUCTION_RULES_DIR.glob("*.yaml")}
    expected_files = {f"{slug}.yaml" for slug in BR_SLUGS}
    assert yaml_files == expected_files, (
        f"production rule set diverges from the six BR rules: "
        f"unexpected={yaml_files - expected_files}; "
        f"missing={expected_files - yaml_files}"
    )

    repo, base_sha, head_sha = br_pack_repo
    monkeypatch.chdir(repo)
    state = load_rules(PRODUCTION_RULES_DIR)
    result = tools.scan_diff(base_sha, head_sha, state)
    assert result.structured_content is not None
    findings = result.structured_content["findings"]
    rule_ids_short = {_short_rule_id(f) for f in findings}
    expected = set(SLUG_TO_RULE_ID.values())
    leaked_placeholders = {rid for rid in rule_ids_short if rid.startswith("_")}
    assert leaked_placeholders == set(), (
        f"placeholder-style rule_ids leaked: {leaked_placeholders}"
    )
    unexpected = rule_ids_short - expected
    assert unexpected == set(), f"unexpected rule_ids: {unexpected}"


def test_as9_idempotency_byte_identical_findings_list(
    monkeypatch: pytest.MonkeyPatch,
    br_pack_repo: tuple[Path, str, str],
) -> None:
    """AS-9. Two successive `scan_diff` invocations over the same diff
    return byte-identical `findings` lists. Loads production rule set
    (alignment with AS-8 end-state). Compares only the `findings` list
    (not `scan_metadata.elapsed_seconds`, which varies). Confirms the
    `(location.path, location.start_line)` ascending ordering of
    canonical §5.1 / compact §5.1 is deterministic.
    """
    repo, base_sha, head_sha = br_pack_repo
    monkeypatch.chdir(repo)
    state = load_rules(PRODUCTION_RULES_DIR)
    r1 = tools.scan_diff(base_sha, head_sha, state)
    r2 = tools.scan_diff(base_sha, head_sha, state)
    assert r1.structured_content is not None
    assert r2.structured_content is not None
    s1 = json.dumps(r1.structured_content["findings"], sort_keys=True)
    s2 = json.dumps(r2.structured_content["findings"], sort_keys=True)
    assert s1 == s2


# ---------------------------------------------------------------------------
# Anchors
# ---------------------------------------------------------------------------

def test_anchor_rule_ids_naming_kebab_case_br_prefix() -> None:
    """ANC-1. Every production BR rule YAML has rule_id exactly equal
    to `SLUG_TO_RULE_ID[slug]` (DD-T07-2a: kebab-case with `br-` prefix,
    lowercase, no underscores in the id itself — though slugs use
    underscores for filenames per DD-T07-2b).
    """
    for slug in BR_SLUGS:
        with (PRODUCTION_RULES_DIR / f"{slug}.yaml").open(encoding="utf-8") as fh:
            doc = yaml.safe_load(fh)
        assert "rules" in doc, f"{slug}.yaml missing top-level 'rules'"
        rules = doc["rules"]
        assert len(rules) == 1, f"{slug}.yaml has {len(rules)} rules; expected 1"
        rid = rules[0]["id"]
        expected = SLUG_TO_RULE_ID[slug]
        assert rid == expected, f"{slug}.yaml rule_id {rid!r} != {expected!r}"
        assert rid.startswith("br-"), f"{rid!r} missing br- prefix"
        assert rid == rid.lower(), f"{rid!r} not lowercase"
        assert "_" not in rid, f"{rid!r} has underscore (use hyphen)"


# ANC-3: 6 rules x 5 other-recognizer fixtures = 30 parametrized items.
_ANC3_PARAMS: list[tuple[str, str, str]] = [
    (rule_slug, other_slug, SLUG_TO_FIXTURE[other_slug])
    for rule_slug in BR_SLUGS
    for other_slug in BR_SLUGS
    if other_slug != rule_slug
]


@pytest.mark.parametrize(
    ("rule_slug", "other_slug", "other_fixture"),
    _ANC3_PARAMS,
    ids=[f"{r}-vs-{o}" for r, o, _ in _ANC3_PARAMS],
)
def test_anchor_cross_recognizer_no_cross_talk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rule_slug: str,
    other_slug: str,
    other_fixture: str,
) -> None:
    """ANC-3. A single `br-X` rule must NOT match any positive fixture of
    another recognizer `br-Y` (Y != X). 30 parametrized items (6 rules x
    5 other-recognizer fixtures). Items auto-activate as each rule YAML
    lands on disk through 3.B-3.C.
    """
    if not (PRODUCTION_RULES_DIR / f"{rule_slug}.yaml").exists():
        pytest.skip(f"{rule_slug}.yaml not yet implemented")
    rules_dir = _build_br_rules_dir(tmp_path, (rule_slug,))
    repo, base_sha, head_sha = _build_pack_repo(tmp_path, (other_fixture,))
    monkeypatch.chdir(repo)
    state = load_rules(rules_dir)
    result = tools.scan_diff(base_sha, head_sha, state)
    assert result.structured_content is not None
    assert result.structured_content["findings"] == []


def test_anchor_metadata_category_present_in_all_rules() -> None:
    """ANC-4. Three sub-invariants over the production rule set:
    (1) every YAML has `metadata.category`;
    (2) all six categories are identical (consistent cross-rules);
    (3) every YAML has `metadata.identifier` with a rule-specific slug,
        and the six identifiers are pairwise distinct.
    """
    categories: list[str] = []
    identifiers: list[str] = []
    for slug in BR_SLUGS:
        with (PRODUCTION_RULES_DIR / f"{slug}.yaml").open(encoding="utf-8") as fh:
            doc = yaml.safe_load(fh)
        rule = doc["rules"][0]
        assert "metadata" in rule, f"{slug}.yaml missing metadata"
        meta = rule["metadata"]
        assert "category" in meta, f"{slug}.yaml metadata missing 'category'"
        categories.append(meta["category"])
        assert "identifier" in meta, f"{slug}.yaml metadata missing 'identifier'"
        identifiers.append(meta["identifier"])
    assert len(set(categories)) == 1, (
        f"metadata.category not consistent across rules: {set(categories)}"
    )
    assert len(set(identifiers)) == len(BR_SLUGS), (
        f"metadata.identifier values not pairwise distinct: {identifiers}"
    )


@pytest.mark.parametrize(
    ("rule_slug", "expected_severity"),
    list(SLUG_TO_EXPECTED_SEVERITY.items()),
    ids=list(SLUG_TO_EXPECTED_SEVERITY.keys()),
)
def test_anchor_severity_scheme(rule_slug: str, expected_severity: str) -> None:
    """ANC-5. DD-T07-4: severity WARNING for five identifiers; ERROR
    only for `br-cns-saude` (categoria sensível sob LGPD Art. 11).
    YAML stores severity uppercase (WARNING/ERROR); compares
    case-insensitively against lowercase expected.
    """
    with (PRODUCTION_RULES_DIR / f"{rule_slug}.yaml").open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    yaml_severity: str = doc["rules"][0]["severity"]
    assert yaml_severity.lower() == expected_severity, (
        f"{rule_slug}.yaml severity {yaml_severity!r} != expected "
        f"{expected_severity!r}"
    )
