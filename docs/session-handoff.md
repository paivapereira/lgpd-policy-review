# Session Handoff

> Estado operacional do projeto **agora**. Sobrescrito ao final de cada sessão.
> Não é registro histórico — para isso, ver `docs/learning-log.md`.
> Primeira leitura ao abrir nova conversa de Chat.

## Última atualização

**2026-05-04, sessão 3 (arquitetura conceitual do lgpd-policy-reader fechada)**

## Onde estamos

Semana 2 de 8-10. As quatro decisões arquiteturais do MCP server
`lgpd-policy-reader` foram tomadas: schema YAML v0.1.0 da Política,
resources expostos, tools expostas, contratos de erro por tool.
Nenhum código foi escrito — sessão foi inteira de design conceitual,
com Domínio 2 (peso 18%) coberto em decisão concreta e Domínio 5
(peso 15%) emergindo forte através de schema versioning, stable
identifiers, conformidade declarativa vs efetiva e escalation
patterns. Domínio 1.4 entrou como ponte conceitual (programmatic
enforcement vs prompt-based guidance) no design do `check_applicability`.

A redação dos artefatos (spec + ADR) foi conscientemente adiada para
a sessão 4. Quatro decisões consecutivas em sequência geram fadiga
incompatível com a redação cuidadosa que ADR Nygard expandido + spec
exigem.

Reframe importante registrado nesta sessão: o sistema verifica
**conformidade declarativa**, não efetiva. Análise estática de PR
não vê estado runtime nem comportamento upstream — onde a verificação
exige isso, o sistema retorna `indeterminate` + dimensão a verificar
manualmente, em vez de fingir certeza. Esse reframe condicionou o
design da tool `check_applicability` e do output da matriz de erros.

## Branch atual

`main`. Limpa, sincronizada com origin.

## Próximo passo concreto

**Sessão 4: redação do spec + ADR-0002.** Em ordem (inverter leva a
duplicação):

1. **Redigir `docs/specs/lgpd-policy-reader.md`.** Documento descritivo
   consolidando as quatro decisões: schema YAML v0.1.0 da Política
   (estrutura completa, exemplo de cláusula ativa e tombstone, e
   **cláusula POL-000 de definições declarando o vocabulário de
   classes de dados** — `dados_de_identificação`, `dados_de_contato`,
   `dados_de_navegação`, `dados_comportamentais`, `dados_sensíveis`,
   `dados_de_localização`, `dados_financeiros`); resources expostos
   (`policy://catalog`, `policy://schema-version`) com payload schema;
   tools expostas (`get_clause`, `find_clauses_by_law_article`,
   `check_applicability`) com assinatura completa e
   `structured_context` da terceira tool; matriz de erros por tool
   com `errorCategory`, `errorCode`, `isRetryable` e distinção
   empty/indeterminate como não-erros; e **seção "Output: Report"
   descrevendo o JSON consolidado por execução** (`report_id`,
   `policy_schema_version`, `policy_version`, `scope`, `summary`,
   `findings`) — saída estrutural do sistema, scratchpad versionado.

2. **Redigir `docs/adr/0002-lgpd-policy-reader-architecture.md`** no
   formato Nygard expandido. Quatro sub-decisões alinhadas às
   quatro decisões da sessão 3, cada uma com Decisão + Rationale +
   Consequência. Seção de **deferimentos** explícita com a lista
   já acordada (list_exceptions, policy://clauses/{id} browseável,
   paginação, item legislativo, DSL para requirements, severidade,
   tags, related_clauses, expansão do structured_context).

3. **PR padrão** (feature branch + PR + squash + delete) para spec
   e para ADR. ADR sobe ao project knowledge após merge.

Saída esperada da sessão 4: dois PRs mergeados, ADR-0002 no project
knowledge, repositório pronto para a sessão 5 começar a implementação
no Claude Code.

Sessão 5: implementação do `lgpd-policy-reader` em FastMCP, já com
contrato fechado em spec.

## Pendências não-bloqueantes

- **Captação de orientador na UTFPR — prazo crítico, ~12 dias
  remanescentes.** Se até quarta-feira não houver e-mail enviado,
  vira o item 1 da sessão 4 antes da redação.
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
  FastMCP 2.x (decidido sessão 2)
- **(novo) Schema YAML v0.1.0 da Política**: dois campos de versão
  (`policy_schema_version` e `policy_version`), `clause_id` opaco
  com prefixo `POL-`, `article_source` como lista incluindo
  `paragraph`/`inciso`/`alinea` (inciso como inteiro), sub-ids em
  requirements e exceptions, ciclo de vida com `status: active|
  deprecated` + `successors` para tombstone
- **(novo) Resources expostos**: `policy://catalog` (índice navegável
  com `successors` para deprecated) e `policy://schema-version` (com
  `compatible_schema_range` para fail-fast). `policy://clauses/{id}`
  eliminado por redundância com `get_clause`
- **(novo) Tools expostas**: `get_clause(clause_id)`,
  `find_clauses_by_law_article(law, article, paragraph?, inciso?,
  alinea?)`, `check_applicability(clause_id, structured_context)`
  com `structured_context` de quatro campos (`operation_type`,
  `data_categories`, `declared_legal_basis`,
  `declared_transformations`) e output carregando
  `verification_scope` + `requires_human_review`. `list_exceptions`
  e `find_related_law_articles` originais eliminadas
- **(novo) Contratos de erro**: três categorias
  (validation/business/system) com `isError` flag, `errorCode`
  estável em inglês, `message` em português, `isRetryable`
  explícito, empty result e indeterminate **não** são erros,
  deprecated tem comportamento distinto em `get_clause` (dado
  válido) vs `check_applicability` (erro retryable com successors
  no `details`)
- **(novo) Escopo do sistema**: análise estática de PR (PR-scoped),
  não auditoria sistêmica. Sistema verifica conformidade
  declarativa, não efetiva. Quatro vereditos por ponto de
  tratamento: `compliant`, `violation_candidate`, `indeterminate`,
  `not_applicable`

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

## Convenção de atualização

Último ato de toda sessão: editar este arquivo, commitar como
`docs: update session-handoff post-session-N`, push direto para main.
Não vai por PR — formalmente respaldado pela decisão 6 do ADR-0001
(direct-commit allowlist permanente).