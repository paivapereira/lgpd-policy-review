# Session Handoff

> Estado operacional do projeto **agora**. Sobrescrito ao final de cada sessão.
> Não é registro histórico — para isso, ver `docs/learning-log.md`.
> Primeira leitura ao abrir nova conversa de Chat.

## Última atualização

**2026-05-02, sessão 1 (bootstrap)**

## Onde estamos

Semana 1 de 8-10. Setup e infraestrutura concluídos. Repositório nascido,
CLAUDE.md raiz commitado, primeiro PR mergeado via squash, ambiente
local validado, fluxo branch → PR → merge testado.

Nenhum código de produção escrito ainda. Nenhum teste rodando.
Nenhum servidor MCP iniciado.

## Branch atual

`main`. Limpa, sincronizada com origin.

## Próximo passo concreto

ADR-0001 do bootstrap. Documenta:
- Decisão de stack canônica (Python 3.12, claude-agent-sdk, FastMCP, Ruff,
  mypy strict, pytest+pytest-asyncio, GitHub Actions)
- Decisão de monorepo
- Decisão de licença MIT (com nota futura sobre CC-BY para policy/)
- Três regras imutáveis do CLAUDE.md (escalonamento humano,
  citação de clause IDs, schema-versioned policy compatibility)
- Decisão de idiomas (EN para código/CLAUDE.md, PT para Política e outputs)
- Justificativa de commits diretos em main durante bootstrap

Estrutura `docs/adr/` será criada junto. Formato: arquivo único
`0001-bootstrap.md`, padrão MADR ou nygard simples — decidir no início
da próxima sessão.

## Pendências não-bloqueantes

- `.python-version` na raiz com `3.12.7` (5 minutos)
- Branch protection em main no GitHub (3 minutos via web)
- `~/.claude/CLAUDE.md` user-scope com preferências pessoais
- **Captação de orientador na UTFPR** — prazo crítico,
  abrir essa frente em até 14 dias

## Decisões fechadas (não revisitar)

- Repositório: monorepo `paivapereira/lgpd-policy-review`, privado, MIT
- Stack: ver CLAUDE.md seção "Stack (canonical)"
- Idiomas: ver CLAUDE.md seção "Languages"
- Workflow git: feature branches + PR + squash merge + delete branch
- Conventional Commits

## Estado da infraestrutura

- Repo: criado, em `C:\Users\joaoguilherm.pereira\dev\lgpd-policy-review`
- VS Code: extensões instaladas e validadas (Python, Ruff, GitLens,
  Markdown All in One, Even Better TOML, YAML)
- Python 3.12.7 via pyenv-win, sem competição no PATH (3.14 desinstalado)
- gh CLI autenticado como `paivapereira` via OAuth
- Claude Code CLI 2.1.123 autenticado, extensão VS Code funcional
- Testes empíricos de adherence ao CLAUDE.md: passaram (sessão 1)

## Convenção de atualização

Último ato de toda sessão: editar este arquivo, commitar como
`docs: update session-handoff post-session-N`, push direto para main.
Não vai por PR — esse arquivo é metadocumental, não tem revisão.