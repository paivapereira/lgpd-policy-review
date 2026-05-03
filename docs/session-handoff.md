# Session Handoff

> Estado operacional do projeto **agora**. Sobrescrito ao final de cada sessão.
> Não é registro histórico — para isso, ver `docs/learning-log.md`.
> Primeira leitura ao abrir nova conversa de Chat.

## Última atualização

**2026-05-02, sessão 2 (ADR-0001 mergeado + revisão D2 completa)**

## Onde estamos

Semana 1 de 8-10. Bootstrap fechado em ADR-0001. Decisão (a) tomada:
próxima frente é o MCP server `lgpd-policy-reader` em FastMCP 2.x,
cobrindo Domínio 2 inteiro (peso 18%). Revisão conceitual completa do
D2 feita na sessão 2 (5 task statements: tool descriptions, resources
vs tools, structured errors, .mcp.json, tool_choice + built-in tools);
quatro ajustes de precisão registrados no learning-log.

Sessão 3 entra direto na arquitetura concreta: resources, tools,
schema da Política, contratos de erro. Sem código ainda — decisão
arquitetural primeiro, código no Claude Code depois.

Branch protection em main: configurada como ruleset mas em "Evaluate"
mode (limitação de GitHub Free para repo privado em conta pessoal);
fica ativa quando migrar para Team. Decisão 5 do ADR-0001 continua
valendo por convenção.

## Branch atual

`main`. Limpa, sincronizada com origin.

## Próximo passo concreto

**Sessão 3: arquitetura concreta do `lgpd-policy-reader`.** Quatro
decisões a tomar, na ordem:

1. **Schema mínimo da Política em YAML.** Estrutura de uma cláusula
   (clause_id, articleSource, requirements, applicabilityScope,
   exceptions, internalDirectiveLinks). Versão 0.1.0, suficiente
   para o server consumir.
2. **Lista exata de resources expostos.** Candidatos:
   `policy://catalog`, `policy://clauses/{clause_id}`,
   `policy://schema-version`. Critério: catálogo navegável vai aqui.
3. **Lista exata de tools expostas.** Candidatos: `get_clause`,
   `find_related_law_articles`, `check_applicability`,
   `list_exceptions`. Critério: ação computacional vai aqui.
   Descrições escritas com cuidado para evitar overlap (D2.1).
4. **Contratos de erro por tool.** Para cada tool acima: validation
   error vs business error vs valid empty result. `errorCategory` +
   `isRetryable` explícitos.

Saída da sessão 3: rascunho de spec do servidor em
`docs/specs/lgpd-policy-reader.md`, levado para o Claude Code na
sessão 4 para implementação. ADR-0002 registrando as decisões
arquiteturais nasce ao final da sessão 3, junto com o spec.

## Pendências não-bloqueantes

- **Captação de orientador na UTFPR** — prazo crítico,
  ~13 dias remanescentes
- Migração de conta GitHub para Team (ativa branch protection
  configurada hoje em "Evaluate" mode)
- `.python-version` na raiz com `3.12.7` (5 minutos)
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
- Frente de implementação atual: MCP server `lgpd-policy-reader` em
  FastMCP 2.x (decidido sessão 2 sobre alternativa "policy schema
  primeiro")

## Estado da infraestrutura

- Repo: em `C:\Users\joaoguilherm.pereira\dev\lgpd-policy-review`
- VS Code: extensões instaladas e validadas (Python, Ruff, GitLens,
  Markdown All in One, Even Better TOML, YAML)
- Python 3.12.7 via pyenv-win, sem competição no PATH
  (3.14 desinstalado)
- gh CLI autenticado como `paivapereira` via OAuth
- Claude Code CLI 2.1.123 autenticado, extensão VS Code funcional
- `docs/adr/0001-bootstrap.md` mergeado via PR padrão (PR #3)
- ADR-0001 subido ao project knowledge para contexto autoritativo
- Branch protection ruleset criado em "Evaluate" mode (não enforça
  até migração para Team)
- Testes empíricos de adherence ao CLAUDE.md (sessão 1): passaram
- Padrão `conversation_search` para provenance verification
  (sessão 2): validado em uso real
- Revisão Domínio 2 completa (sessão 2): cinco task statements +
  quatro ajustes de precisão no learning-log

## Convenção de atualização

Último ato de toda sessão: editar este arquivo, commitar como
`docs: update session-handoff post-session-N`, push direto para main.
Não vai por PR — formalmente respaldado pela decisão 6 do ADR-0001
(direct-commit allowlist permanente).
