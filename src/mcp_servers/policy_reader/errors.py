"""Startup-time errors raised by the policy-reader loader.

Messages are written in Brazilian Portuguese because they surface to the
operator on stderr at server boot — same audience as the rest of the
system's end-user output (see CLAUDE.md, "Languages").
"""


class PolicyLoadError(Exception):
    """Raised by `loader.load_policy` when the Policy artefact cannot be
    loaded or fails cross-file validation. Caught at the bootstrap layer in
    `server._bootstrap`, which prints the message to stderr and exits non-zero
    before `mcp.run()` — see canonical.md §5.4 and §6.5.
    """
