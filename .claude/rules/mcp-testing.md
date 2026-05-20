# MCP testing

## Principle

For MCP server validation, prefer CLI mode over UI when
reproducibility is a criterion. Gate exercises and CI integration
require commands that can be replayed; UI clicks are not
auditable.

## Justification

Materialized in session #25 (Milestone A gate). Initial gate
attempt used MCP Inspector UI; mid-exercise pivot to
`npx @modelcontextprotocol/inspector --cli ...` because UI clicks
could not be replayed against the same state for the evidence
pack. CLI commands archived in `docs/milestoneA.md` are
reproducible by any future reviewer.

## When to apply

- Milestone-level gates: CLI mode, commands archived as evidence.
- CI integration of MCP servers: CLI mode with JSON output
  piped to assertions.
- Initial development and exploratory debugging: UI is fine.
  Reproducibility is not the dominant criterion at that stage.

## How to apply

Basic invocation against a local server:

    npx @modelcontextprotocol/inspector --cli `
      uv run python -m mcp_servers.policy_reader.server `
      --method resources/list

Common flags:
- `--method <name>`: required in CLI mode. Examples:
  `resources/list`, `resources/read`, `tools/list`, `tools/call`.
- `--tool-name <name>` and `--tool-arg key=value`: for
  `tools/call`.
- `--config <path>`: load config file (typically `.mcp.json`).
- `--server <name>`: with `--config`, select a specific server
  entry.

Output is JSON by default. Suitable for piping to `jq` or to
test assertions.

## Reference

Official MCP Inspector documentation:
"CLI mode enables programmatic interaction with MCP servers
from the command line, ideal for scripting, automation, and
integration with coding assistants."
https://github.com/modelcontextprotocol/inspector
