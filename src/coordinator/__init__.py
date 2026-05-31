"""Coordinator package — the Python main loop that orchestrates the five
pipeline subagents (Triager -> Detector -> Classifier -> Matcher -> Reporter)
via sequential `claude-agent-sdk` `query()` calls (pattern A'').

Milestone C. Canonical spec: `docs/specs/subagents/coordinator.md`.
"""
