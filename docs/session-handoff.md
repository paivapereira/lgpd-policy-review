# Session Handoff

> Estado operacional do projeto **agora**. Sobrescrito ao final de cada sessão.
> Não é registro histórico — para isso, ver `docs/learning-log.md`.
> Primeira leitura ao abrir nova conversa de Chat.

## Última atualização

**2026-05-02, sessão 2 (ADR-0001 mergeado)**

## Onde estamos

Semana 1 de 8-10. Bootstrap formalmente fechado: ADR-0001 documentando
todas as decisões fundacionais (monorepo, stack canônica, idiomas,
três regras imutáveis, workflow git, direct-commit allowlist) está
mergeado em `main`. Estrutura `docs/adr/` existe. Padrão de ADR
validado em uso real e disponível como referência para futuras decisões
arquiteturais.

Nenhum código de produção escrito ainda. Nenhum teste rodando.
Nenhum servidor MCP iniciado.

## Branch atual

`main`. Limpa, sincronizada com origin.

## Próximo passo concreto

**Decidir entre duas frentes para abrir a sessão 3.** Ambas avançam
o projeto; diferem em domínio da prova exercitado e em densidade
de conceitos por hora investida.

- **(a) Primeiro MCP server `lgpd-policy-reader` em FastMCP.** Cobre
  Domínio 2 inteiro (peso 18%) numa só implementação: tool
  descriptions diferenciadas (`get_clause` vs
  `find_related_law_articles` sem overlap), structured error
  responses (`errorCategory`, `isRetryable`), `tool_choice` forçado,
  `.mcp.json` project-scope com `${VARS}` expandidos, MCP resources
  como catálogo navegável da Política. Implementação termina em uma
  sessão; conecta direto à extensão Claude Code para teste empírico.
- **(b) Estrutura inicial de `policy/` com schema YAML mínimo.**
  Cobre mais Domínio 5 (provenance, schema versioning,
  `policy_schema_version` compatibility). Componente jurídico
  significativo fora do escopo da prova; mais lento e mais denso
  conceitualmente.

**Recomendação:** (a). Mais conceitos da prova por hora, e o MCP
server passa a ser ferramenta usável imediatamente para acelerar
sessões seguintes (consultar Política via extensão Claude Code
durante design da Política, não depois).

João decide ao abrir a sessão 3.

## Pendências não-bloqueantes

- **Captação de orientador na UTFPR** — prazo crítico,
  ~13 dias remanescentes
- `.python-version` na raiz com `3.12.7` (5 minutos)
- Branch protection em main no GitHub (3 minutos via web)
- `~/.claude/CLAUDE.md` user-scope com preferências pessoais
- Considerar enxugamento futuro da seção "Mapeamento aos 5 domínios"
  em `proposta-tcc.md` (redundância com exam guide PDF)

## Decisões fechadas (não revisitar)

- Repositório: monorepo `paivapereira/lgpd-policy-review`, privado,
  MIT (código)
- Política sob `policy/` terá licença separada (CC-BY provável),
  decidido em ADR futuro antes de v1.0 ou abertura pública
- Stack: ver CLAUDE.md seção "Stack (canonical)" e ADR-0001 §2
- Idiomas: ver CLAUDE.md seção "Languages" e ADR-0001 §3
- Workflow git: feature branches + PR + squash merge + delete branch
  (ADR-0001 §5)
- Direct-commit allowlist permanente: apenas
  `docs/session-handoff.md` e `docs/learning-log.md` (ADR-0001 §6)
- Conventional Commits
- Formato de ADR: Nygard expandido para decisões compostas; MADR
  reservado para futuras decisões com trade-off comparativo real

## Estado da infraestrutura

- Repo: em `C:\Users\joaoguilherm.pereira\dev\lgpd-policy-review`
- VS Code: extensões instaladas e validadas (Python, Ruff, GitLens,
  Markdown All in One, Even Better TOML, YAML)
- Python 3.12.7 via pyenv-win, sem competição no PATH
  (3.14 desinstalado)
- gh CLI autenticado como `paivapereira` via OAuth
- Claude Code CLI 2.1.123 autenticado, extensão VS Code funcional
- `docs/adr/0001-bootstrap.md` mergeado via PR padrão
- ADR-0001 subido ao project knowledge para contexto autoritativo
- Testes empíricos de adherence ao CLAUDE.md (sessão 1): passaram
- Padrão `conversation_search` para provenance verification (sessão 2):
  validado em uso real

## Convenção de atualização

Último ato de toda sessão: editar este arquivo, commitar como
`docs: update session-handoff post-session-N`, push direto para main.
Não vai por PR — formalmente respaldado pela decisão 6 do ADR-0001
(direct-commit allowlist permanente).
