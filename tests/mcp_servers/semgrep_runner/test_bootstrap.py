"""T05 acceptance tests — server skeleton + rule set loader.

Each `test_as_*` covers one acceptance scenario from `docs/tasks.md` T05.
AS-7 here (`test_as7_scan_diff_registered_with_canonical_description`)
pins the byte-identity invariant between the tool description registered
by FastMCP and the literal in `docs/specs/semgrep-runner/compact.md` §5.1
/ canonical §4.2 — this invariant survives the T06 substitution because
the wrapper docstring in `server.py` is unchanged. The T05 anchor
(`test_documents_fastmcp_scan_diff_stub_shape`) and T05's AS-8
(`test_as8_scan_diff_stub_returns_not_implemented_envelope`) were
removed by T06 §3.J: both pinned the obsolete `NOT_IMPLEMENTED` stub
shape that T06 replaced. End-to-end wire format (Option B) is now
tested in `test_scan_diff.py::test_as11_wire_format_option_b`.

Fixtures never touch the real `mcp_servers/semgrep_runner/rules/` of the
repo — tests that mutate rule files build under `tmp_path` and pass the
path explicitly to `load_rules` or `server._bootstrap`.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client

from mcp_servers.semgrep_runner import server
from mcp_servers.semgrep_runner.errors import RulesLoadError
from mcp_servers.semgrep_runner.loader import (
    compute_rules_version,
    load_rules,
    resolve_runner_root,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_valid_rule(path: Path, rule_id: str) -> None:
    """Write a syntactically-valid Semgrep rule YAML with a unique id.

    Output mirrors the shape of `mcp_servers/semgrep_runner/rules/_placeholder.yaml`:
    one rule per file, single-line `message`, `INFO` severity, Python target
    language, opaque pattern token. Used by AS-3/AS-5/AS-6 fixtures to populate
    `tmp_path / "rules"` with valid baselines before mutating one element.
    """
    path.write_text(
        f"rules:\n"
        f"  - id: {rule_id}\n"
        f"    message: Test rule {rule_id}\n"
        f"    severity: INFO\n"
        f"    languages: [python]\n"
        f"    pattern: __TEST_{rule_id.upper()}__\n",
        encoding="utf-8",
    )


# Literal extracted byte-for-byte from `docs/specs/semgrep-runner/compact.md`
# §5.1. AS-7 asserts byte-identity between this constant and the description
# returned by `client.list_tools()`. Pos canonical-sync-D (sessão #29),
# canonical §4.2 carries the same text — drift between the two specs has been
# resolved.
_EXPECTED_SCAN_DIFF_DESCRIPTION = """Scans the Git diff between base_ref and head_ref using the project's curated Semgrep rule set, returning findings that match any rule in the set. Use this when the caller has the BASE and HEAD refs of a pull request and needs to identify candidate sites for downstream classification. The rule set is server-side curated and not callable-parameterizable; it is fixed at server build time. The MVP rule set covers Brazilian personal data identifiers (CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde), but the component itself is domain-agnostic — rule set substitution is the supported path for different jurisdictions or detection domains.

Findings are single-file: the MVP does not perform cross-file taint analysis. Each finding carries rule provenance (rule_id), location (file path, line range), and code snippet. Empty findings list is a valid success outcome — the diff was scanned and no rules matched.

Returns success with findings list (possibly empty) on completion. Returns business error if Git refs are unresolvable, system error if the scan times out or the Semgrep binary fails. Operation is synchronous and may take seconds to minutes depending on diff size."""


# ---------------------------------------------------------------------------
# AS-1 — Startup OK against the real rules dir
# ---------------------------------------------------------------------------

def test_as1_startup_ok_against_real_rules_dir() -> None:
    """AS-1. The current state of `mcp_servers/semgrep_runner/rules/` (real
    artefact, contains at least `_placeholder.yaml`) loads without
    exception; the resulting `LoadedRules` carries a non-empty
    `rule_files` list and a `rules_version` matching the `sha256:` prefix.
    """
    real_rules = resolve_runner_root()

    loaded = load_rules(real_rules)

    assert loaded.rules_root == str(real_rules)
    assert loaded.rule_files  # non-empty
    assert loaded.rules_version.startswith("sha256:")
    assert len(loaded.rules_version) == len("sha256:") + 64


# ---------------------------------------------------------------------------
# AS-2 — Missing rules dir aborts startup
# ---------------------------------------------------------------------------

def test_as2_aborts_on_missing_rules_dir(tmp_path: Path) -> None:
    """AS-2. Passing a path that does not exist as the rules root aborts
    with a Portuguese message identifying the missing directory.
    """
    missing = tmp_path / "nonexistent_rules"

    with pytest.raises(RulesLoadError, match=r"Diretório de regras ausente"):
        load_rules(missing)


# ---------------------------------------------------------------------------
# AS-3 — Invalid YAML in rules dir aborts startup
# ---------------------------------------------------------------------------

def test_as3_aborts_on_invalid_yaml_in_rules(tmp_path: Path) -> None:
    """AS-3. A directory containing one valid YAML and one syntactically
    broken YAML aborts startup with a message citing the broken file and
    the parsing error. The broken file uses indentation that PyYAML
    rejects with `yaml.YAMLError` (preferred over duplicate-key mutation,
    which PyYAML silences by default).
    """
    rules_root = tmp_path / "rules"
    rules_root.mkdir()
    _write_valid_rule(rules_root / "valid.yaml", "test_valid")
    (rules_root / "broken.yaml").write_text(
        "key1:\n  sub: value\n bad_indent: value\n",
        encoding="utf-8",
    )

    with pytest.raises(RulesLoadError, match=r"(?s)YAML inválido.*broken\.yaml"):
        load_rules(rules_root)


# ---------------------------------------------------------------------------
# AS-4 — Empty rules dir aborts startup
# ---------------------------------------------------------------------------

def test_as4_aborts_on_empty_rules_dir(tmp_path: Path) -> None:
    """AS-4. An empty rules directory aborts with the canonical pt-BR
    message "Rule set vazio é configuração inválida". The raise lives in
    `loader.load_rules` BEFORE the `LoadedRules` Pydantic model is
    constructed — `min_length=1` on `rule_files` is defence in depth,
    not the primary check (DD-T05-12).
    """
    rules_root = tmp_path / "rules"
    rules_root.mkdir()

    with pytest.raises(
        RulesLoadError, match=r"Rule set vazio é configuração inválida",
    ):
        load_rules(rules_root)


# ---------------------------------------------------------------------------
# AS-5 — rules_version deterministic between consecutive calls
# ---------------------------------------------------------------------------

def test_as5_rules_version_deterministic(tmp_path: Path) -> None:
    """AS-5. Two consecutive invocations of `compute_rules_version` against
    the same unchanged rules dir produce byte-identical strings.
    """
    rules_root = tmp_path / "rules"
    rules_root.mkdir()
    _write_valid_rule(rules_root / "rule_a.yaml", "rule_a")
    _write_valid_rule(rules_root / "rule_b.yaml", "rule_b")

    first = compute_rules_version(rules_root)
    second = compute_rules_version(rules_root)

    assert first == second
    assert first.startswith("sha256:")


# ---------------------------------------------------------------------------
# AS-6 — rules_version changes with content (add | edit | rename)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mutation", ["add", "edit", "rename"])
def test_as6_rules_version_changes_with_content(
    tmp_path: Path, mutation: str,
) -> None:
    """AS-6. Each parametrized mutation of a stable baseline produces a
    `rules_version` distinct from the baseline:

      - `add`     — introduces a third file alongside the baseline two.
      - `edit`    — mutates the payload of an existing file.
      - `rename`  — renames a file without altering its content; this
                    validates that `compute_rules_version` includes the
                    filename in the hash input (DD-T05-1 anti-rename
                    property).
    """
    rules_root = tmp_path / "rules"
    rules_root.mkdir()
    _write_valid_rule(rules_root / "rule_a.yaml", "rule_a")
    _write_valid_rule(rules_root / "rule_b.yaml", "rule_b")
    baseline = compute_rules_version(rules_root)

    if mutation == "add":
        _write_valid_rule(rules_root / "rule_c.yaml", "rule_c")
    elif mutation == "edit":
        _write_valid_rule(rules_root / "rule_a.yaml", "rule_a_edited")
    elif mutation == "rename":
        (rules_root / "rule_a.yaml").rename(rules_root / "rule_a_renamed.yaml")
    else:
        raise AssertionError(f"unknown mutation {mutation!r}")

    after = compute_rules_version(rules_root)

    assert after != baseline


# ---------------------------------------------------------------------------
# AS-7 — scan_diff registered with description byte-identical to compact §5.1
# ---------------------------------------------------------------------------

async def test_as7_scan_diff_registered_with_canonical_description(
    reset_server_state: None,
) -> None:
    """AS-7. After bootstrap, `client.list_tools()` exposes `scan_diff` with
    a `description` field byte-identical to the literal in
    `docs/specs/semgrep-runner/compact.md` §5.1 (three paragraphs of plain
    English prose, no markdown, paragraphs separated by blank lines).
    """
    server._bootstrap()

    async with Client(server.mcp) as client:
        tools = await client.list_tools()

    by_name = {t.name: t for t in tools}
    assert "scan_diff" in by_name
    assert by_name["scan_diff"].description == _EXPECTED_SCAN_DIFF_DESCRIPTION


