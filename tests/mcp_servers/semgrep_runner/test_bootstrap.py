"""T05 acceptance tests — server skeleton + rule set loader.

Each `test_as_*` covers one acceptance scenario from `docs/tasks.md` T05.
The anchor `test_documents_fastmcp_scan_diff_stub_shape` (labelled
distinctly per `.claude/rules/test-strategy.md`) pins the wire shape
FastMCP produces for the T05 stub so that T06's substitution of the
real `scan_diff` payload fails first here if the wire envelope drifts.

Fixtures never touch the real `mcp_servers/semgrep_runner/rules/` of the
repo — tests that mutate rule files build under `tmp_path` and pass the
path explicitly to `load_rules` or `server._bootstrap`.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client
from mcp.types import TextContent

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
# Anchor — FastMCP wire shape for the T05 NOT_IMPLEMENTED stub (DD-T05-7)
# ---------------------------------------------------------------------------

async def test_documents_fastmcp_scan_diff_stub_shape(
    reset_server_state: None,
) -> None:
    """Anchor test pinning the wire shape FastMCP 3.x produces from the T05
    stub of `@mcp.tool scan_diff`, invoked via the in-memory `Client`.

    Locked-in observation against FastMCP 3.2.4:
      `Client(server.mcp).call_tool(name, args)` returns
      `fastmcp.client.client.CallToolResult` with snake_case attributes
      (`is_error`, `structured_content`, `content`).

    Shape pinned (Option B envelope per ADR-0002 §3 amendment 2026-05-17):
      - `is_error=False` — wire flag reserved for protocol failures.
      - `structured_content` carries the four canonical envelope fields
        (`errorCode`, `message`, `isRetryable`, `details`).
      - `content[0]` is a `TextContent` whose `text` reproduces `message`.

    T06 replaces the stub with the real `scan_diff` payload. The wire
    shape itself stays stable; only the payload contents change (six
    real errorCodes + success path). If FastMCP changes the wire shape
    in a future release, this anchor fails first and forces revision
    before T06 substitution.
    """
    server._bootstrap()

    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "scan_diff", {"base_ref": "main", "head_ref": "feature/x"},
        )

    assert result.is_error is False
    assert isinstance(result.structured_content, dict)
    assert result.structured_content["errorCode"] == "NOT_IMPLEMENTED"
    assert result.structured_content["message"]
    assert result.structured_content["isRetryable"] is False
    assert result.structured_content["details"] == {"task": "T06"}
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].text == result.structured_content["message"]


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


# ---------------------------------------------------------------------------
# AS-8 — Stub returns the NOT_IMPLEMENTED envelope (helper direct)
# ---------------------------------------------------------------------------

def test_as8_scan_diff_stub_returns_not_implemented_envelope() -> None:
    """AS-8. The private helper `_not_implemented_envelope()` returns a
    `ToolResult` carrying the four canonical envelope fields in
    `structured_content` and a `TextContent` reproducing the message in
    `content[0]`. Per DD-T05-11, the helper is tested directly (cleaner
    than parsing the `ToolResult` returned by the decorated `scan_diff`).
    The anchor test above exercises the end-to-end path through the
    FastMCP Client; this AS pins the helper contract that T06 will reuse.
    """
    result = server._not_implemented_envelope()

    assert result.structured_content == {
        "errorCode": "NOT_IMPLEMENTED",
        "message": (
            "Tool scan_diff ainda não implementada; "
            "implementação completa em T06."
        ),
        "isRetryable": False,
        "details": {"task": "T06"},
    }
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].text == result.structured_content["message"]
