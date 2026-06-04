"""Make the repo-root `scripts` package importable in CI-adapter tests.

`scripts/` is dev/CI glue, deliberately NOT part of the installed `mcp-servers`
dist (uv_build packages only `src/`), so it is not on pytest's path by default.
Append (not prepend) the repo root: the editable `src/` finder keeps precedence,
so `import mcp_servers` still resolves to `src/mcp_servers/` (the package), never
the repo-root `mcp_servers/` rules-data dir.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.append(str(_ROOT))
