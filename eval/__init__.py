"""Evaluation harnesses (not part of the installed `mcp-servers` dist).

Marked a package so `eval.harness.*` resolves under `python -m` (cwd=repo-root)
and in tests via a path shim. Existing file-path invocations
(`uv run python eval/harness/run_engine_cases.py`) are unaffected — __init__ is
not executed in file-path mode.
"""
