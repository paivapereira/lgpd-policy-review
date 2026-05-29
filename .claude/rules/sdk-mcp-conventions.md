---
description: Convenções de erro SDK/MCP por camada (casing + discriminador)
paths:
  - "src/coordinator/**"
  - "src/subagents/**"
  - "src/mcp_servers/**"
---

# Convenções de erro SDK e MCP (layer-aware)

Dois eixos divergem por camada. Ambos importam; a casing sozinha não basta.

## Eixo 1 — casing do campo
- **Servidores MCP full-fledged** (FastMCP / MCP Python SDK): `isError`
  (camelCase), per wire format do protocolo MCP. Usado por `policy-reader`,
  `semgrep-runner`.
- **Handlers `@tool` do `claude-agent-sdk`** (SDK MCP servers in-process via
  `create_sdk_mcp_server`): retornam `is_error` (snake_case) no dict de
  resultado, per idioma Python; o SDK normaliza para `isError` canônico no
  `CallToolResult`. Usado por `emit_report` / tools do `reporter`.

## Eixo 2 — semântica do discriminador (a parte que morde)
- **FastMCP servers** (`policy-reader`, `semgrep-runner`) seguem **Option B**
  (ADR-0002 §3, amendment 2026-05-17): wire `isError: false` em TODOS os
  retornos — sucesso, empty, e erro de domínio. Discrimine sucesso-vs-erro
  pela **presença de `errorCode` em `structuredContent`**, NÃO pelo flag
  `isError`. Checar `isError` nesses servers sempre vê `false` e perde o erro.
- **SDK `@tool` servers** (`emit_report`) sinalizam erro com `is_error: True`
  nativo — o flag É o discriminador e sobrevive ao stream. Mas
  `structuredContent` de `@tool` in-process é **dropado** no bridge do SDK
  (sucesso E erro; verificado smoke-test `sdk_tool_error_channel` v1/v2): só
  `content` + o flag chegam ao consumidor. Payload estruturado precisa ir
  **serializado no `content`** (JSON string), não em `structuredContent`.

## Consequência prática para o coordinator
- Lendo `semgrep-runner` / `policy-reader` via `query()` stream: discrimine por
  presença de `errorCode` em **`tool_use_result.structuredContent`** da
  `UserMessage` (não no `ToolResultBlock`, cujo `content` é só a string JSON;
  verificado v3). Ignore `isError` (sempre `false` sob Option B).
- Lendo `emit_report`: discrimine pelo flag `is_error`/`isError` (nativo);
  estrutura vai no `content` serializado, não em `structuredContent`.

**Constraint de impl (FastMCP Option B).** Tools Option B (`scan_diff`, tools do
`policy-reader`) devem retornar via `ToolResult` (`fastmcp.tools.base`) com
`structured_content=...`, **não** via anotação `-> ModeloPydanticDeSucesso`. Um
`outputSchema` estrito de sucesso faz o FastMCP rejeitar o envelope de erro com
`ToolError` → wire `isError: true`, quebrando a Option B (verificado v4). O
`scan_diff` real já usa `-> ToolResult` — não regredir.

Cross-ref: ADR-0002 §3, `coordinator.md` §5, `semgrep-runner` canonical §5.