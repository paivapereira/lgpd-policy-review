"""Startup-time errors raised by the semgrep-runner loader.

Messages are written in Brazilian Portuguese because they surface to the
operator on stderr at server boot — same audience as the rest of the
system's end-user output (see CLAUDE.md, "Languages").
"""


class RulesLoadError(Exception):
    """Raised by `loader.load_rules` when the Semgrep rule set cannot be
    loaded. Caught at the bootstrap layer in `server._bootstrap`, which
    prints the message to stderr and exits non-zero before `mcp.run()` —
    analogous to `PolicyLoadError` in `policy_reader`.
    """
