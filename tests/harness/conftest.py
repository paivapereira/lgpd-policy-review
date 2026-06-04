"""Make the repo-root `eval` package importable in harness tests.

`eval/` is not part of the installed `mcp-servers` dist (uv_build packages only
`src/`). Append (not prepend) the repo root so the editable `src/` finder keeps
precedence (`import mcp_servers` still resolves to `src/mcp_servers/`). Mirrors
tests/ci/conftest.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.append(str(_ROOT))
