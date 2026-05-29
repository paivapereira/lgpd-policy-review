# RESULTS — smoke_test sdk_tool_error_channel (v1–v4)

Descoberta empírica das convenções de erro SDK/MCP por camada, consumidas pelo
coordinator via `query()` stream. Verificado contra `claude-agent-sdk==0.2.87` +
`fastmcp==3.2.4`, auth Claude Code CLI, Windows 11 / PS 5.1. Sessão Code item 3.

> **AVISO — os exit codes de v3 e v4 MENTEM.** A heurística de veredito embutida
> nos scripts tem bugs conhecidos (profundidade-1 em v3; timing de conexão lido
> como PROBE C em v4). Decisão: documentar aqui, **não** consertar o código do
> teste. Ler o "achado real" abaixo, não o exit code.

## v1 — SDK `@tool`, caminho de erro
- **Hipótese:** `@tool` consegue carregar `structuredContent` junto com erro?
- **Exit:** 1 (`EIXO2_PARCIAL`).
- **Achado real:** `is_error: True` (snake_case) sobrevive ao stream como
  discriminador; `structuredContent` é **dropado** no bridge in-process. Só
  `content` (string) + flag chegam ao consumidor.

## v2 — SDK `@tool`, sucesso vs erro
- **Hipótese:** o drop de `structuredContent` é específico do erro?
- **Exit:** 1 (`SDK_NUNCA_PROPAGA`).
- **Achado real:** `structuredContent` é dropado nos **dois** caminhos — é
  propriedade do bridge `@tool`, não do caminho de erro. Sucesso preserva
  `content` como lista de text-blocks; erro colapsa para string `'Error: ...'`.
  Conclusão: payload estruturado de `@tool` (ex.: `emit_report`) vai serializado
  no `content`, não em `structuredContent`.

## v3 — FastMCP stdio via `query()` stream
- **Hipótese:** `structuredContent` de FastMCP sobrevive ao stream do coordinator?
- **Exit:** 1 (`ERRORCODE_VIA_CONTENT`) — **MENTE** (bug profundidade-1: o veredito
  checava `"sentinel" in tur` no top-level, mas o dado está em
  `tur["structuredContent"]`, profundidade-2).
- **Achado real:** `OPTION_B_VIÁVEL`. `structuredContent` sobrevive **íntegro**
  como dict aninhado em `tool_use_result.structuredContent` da `UserMessage`. O
  `ToolResultBlock.content` carrega só a string JSON. → Option B é viável no
  coordinator via `query()`.

## v4 — FastMCP, outputSchema declarado violado por envelope de erro
- **Hipótese (guarda):** um `outputSchema` estrito de sucesso rejeita o envelope
  de erro Option B?
- **Exit:** 4 (`SETUP_FAIL`) — **MENTE** (timing de conexão stdio no agent loop;
  o server `probe` não conectou na janela das `ToolSearch`, não PROBE C).
- **Resolução (via FastMCP Client in-memory, fora do agent loop):**
  - `-> ScanSuccess` (Pydantic) + envelope de erro → **`ToolError: Output
    validation error`** → wire `isError: true` → **quebra Option B**.
  - `-> ToolResult` (escape hatch, o caminho real) → **não levanta**;
    `structured_content` com `errorCode` sobrevive; `is_error=False`.
- **Achado real:** tensão do ADR-0002 confirmada. O `scan_diff` real já usa
  `-> ToolResult` ([server.py:74](../../../src/mcp_servers/semgrep_runner/server.py#L74));
  não regredir para modelo Pydantic de sucesso. Guarda no código:
  `_envelope_tool_result` ([_envelope.py](../../../src/mcp_servers/semgrep_runner/_envelope.py)).

## Limite do observado (não inferir além)
A combinação do `scan_diff` real (`-> ToolResult`) **através do `query()`
stream** não foi exercitada num run único. v3 provou que o stream preserva
`structuredContent` de FastMCP; v4 (via Client in-memory) provou que
`-> ToolResult` não levanta nem estripa o envelope de erro. A conclusão de que
as duas se compõem é forte — cada metade está verificada — mas é **composição,
não observação direta**. Aceito como suficiente; registrado para que ninguém
leia isto como prova end-to-end de um único caminho.

## Consequências registradas
- `.claude/rules/sdk-mcp-conventions.md` — Eixo 2 + Consequência prática + Constraint.
- `docs/specs/subagents/coordinator.md` §5 — locus da Peça 1 (`tool_use_result.structuredContent`).
- GUARD em `_envelope_tool_result` + comentário na assinatura de `scan_diff`.
- Follow-up: promover a constraint Option-B/outputSchema a ADR-0013 (catalogado em `docs/tasks.md`).
