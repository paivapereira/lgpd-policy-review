# SDK and MCP conventions

## isError vs is_error (layer-aware)
`isError` (camelCase) em MCP servers full-fledged via FastMCP ou MCP Python SDK (`policy-reader`, `semgrep-runner`) per MCP protocol spec. `is_error` (snake_case) em handlers de `@tool` do `claude-agent-sdk` (custom tools in-process, e.g., `reporter_tools`) per Python idiom; SDK traduz para `isError` no wire automaticamente.
