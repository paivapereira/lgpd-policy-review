"""Startup loader for the semgrep-runner MCP server.

Reads the curated Semgrep rule set from a parametrizable rules
directory (`mcp_servers/semgrep_runner/rules/` by default), validates
that every YAML file is syntactically parseable, and computes
`rules_version` as a deterministic hash of the directory contents.
Returns a `LoadedRules` consumed by the tool handlers registered in
`server.py`.

Semantic validation of rule content (Semgrep rule schema) is NOT
performed here — Semgrep itself surfaces semantic errors at scan time
via the `INVALID_RULE_SET` errorCode (T06).

Per canonical §8.6 / ADR-0010, the Semgrep binary availability is NOT
checked here either — that check is per-call at the `scan_diff` entry
point in T06. The loader's scope is the rule set artefact only.

All failures raise `RulesLoadError` with a Portuguese message
identifying the offending path or condition. The bootstrap layer in
`server.py` translates that exception into a non-zero exit before
`mcp.run()` is reached.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

import yaml

from .errors import RulesLoadError
from .models import LoadedRules


def resolve_runner_root(explicit: Path | None = None) -> Path:
    """Resolve the rule set root directory. Precedence: explicit argument >
    `SEMGREP_RUNNER_ROOT` env var > `<repo>/mcp_servers/semgrep_runner/rules`
    discovered from `__file__`. The env var path is the recommended hook for
    test fixtures.

    Mirrors `policy_reader.loader.resolve_policy_root` in function shape
    (explicit > env > default precedence); differs in semantics — the
    returned path here IS the rules directory itself, not a parent.
    `semgrep-runner` has no header file, no vocabularies dir, no sibling
    artefacts; the curated rule set IS the artefact.
    """
    if explicit is not None:
        return explicit
    env = os.environ.get("SEMGREP_RUNNER_ROOT")
    if env:
        return Path(env)
    # src/mcp_servers/semgrep_runner/loader.py → parents[3] is repo root
    return (
        Path(__file__).resolve().parents[3]
        / "mcp_servers"
        / "semgrep_runner"
        / "rules"
    )


def _read_yaml(path: Path) -> Any:
    if not path.is_file():
        raise RulesLoadError(
            f"Arquivo de regra ausente ou não é arquivo regular: {path}",
        )
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise RulesLoadError(
            f"YAML inválido em {path}: {exc}",
        ) from exc


def compute_rules_version(rules_root: Path) -> str:
    """Deterministic hash of the rules directory contents.

    Algorithm: SHA-256 over the aggregated content of every `*.yaml`
    file in `rules_root`, ordered lexicographically by basename, with
    CRLF→LF normalisation (protects against Git auto-CRLF on Windows),
    and with each filename included in the hash input (protects against
    silent rename). Output: `"sha256:<64-char hex>"`.

    Alternatives considered (canonical §6):
      (a) manual semver in a `rules_version.yaml` file — requires human
          maintenance, drift target;
      (b) combined semver + hash — adds discipline without gain over
          pure hash;
      (c) deterministic hash — chosen here. Trade-off: opaque hash vs
          human-readable "v0.3.2", in exchange for correctness by
          construction.

    Forward-compat: `rules/` is flat by project convention. If a future
    layout introduces subdirectories (e.g. `rules/recognizers/`), swap
    `glob("*.yaml")` for `rglob("*.yaml")` AND swap `path.name` for
    `path.relative_to(rules_root).as_posix()` in the hash input to
    preserve the anti-rename property under hierarchy.
    """
    h = hashlib.sha256()
    for path in sorted(rules_root.glob("*.yaml")):
        content = path.read_bytes().replace(b"\r\n", b"\n")
        h.update(path.name.encode("utf-8"))
        h.update(b"\n")
        h.update(content)
        h.update(b"\n")
    return f"sha256:{h.hexdigest()}"


def load_rules(rules_root: Path) -> LoadedRules:
    """Read and validate the curated Semgrep rule set rooted at `rules_root`.

    Order of validation (fail-fast on first failure):
        1. `rules_root` exists and is a directory.
        2. Rule set is non-empty. Empty rule set raises a domain-specific
           `RulesLoadError` in Portuguese BEFORE the `LoadedRules` model
           is constructed (the `min_length=1` on `rule_files` is defence
           in depth, not the primary check — see DD-T05-12 / models.py).
        3. Every `*.yaml` file is YAML-parseable. Semantic validation of
           rule content (Semgrep rule schema) is deferred to runtime —
           Semgrep itself raises `INVALID_RULE_SET` during `scan_diff`
           execution in T06.
    """
    if not rules_root.is_dir():
        raise RulesLoadError(
            f"Diretório de regras ausente: {rules_root}",
        )

    rule_files = sorted(rules_root.glob("*.yaml"))
    if not rule_files:
        raise RulesLoadError(
            "Rule set vazio é configuração inválida "
            f"(diretório {rules_root} sem arquivos *.yaml)",
        )

    for path in rule_files:
        # Validates YAML syntax; the parsed content is discarded — semantic
        # validation of Semgrep rule structure belongs to the subprocess at
        # scan time (T06), not to this loader.
        _read_yaml(path)

    return LoadedRules(
        rules_version=compute_rules_version(rules_root),
        rule_files=[str(p) for p in rule_files],
        rules_root=str(rules_root),
    )
