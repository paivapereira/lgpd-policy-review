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

Ao final da sessão, o aluno solicitou esboço de visão sistêmica
para identificar gaps entre proposta-tcc.md original e decisões da
sessão #03. Cinco tensões foram nomeadas e fechadas: (1) severidade
fora do MVP; (2) subagentes redesenhados conforme princípio
"single responsibility per agent" — cinco subagentes nomeados;
(3) etapa 0 de triagem de relevância de PR mora como subagente
Triager, não como hook; (4) classificação pode/consent/anon/
proibido vive nas cláusulas (não compete com vereditos);
(5) AEP fora do MVP, recognizers brasileiros mantidos. Posicionamento
de output: Report informativo (não bloqueia merge) no MVP, com
bloqueio condicional como evolução pós-validação empírica de FPR.
A sessão #04 inverte plano original: redige primeiro
`docs/architecture-overview.md` (visão sistêmica), depois retoma
spec do `lgpd-policy-reader` + ADR-0002.

## Branch atual

`main`. Limpa, sincronizada com origin.

## Próximo passo concreto

**Sessão 4: redação do `docs/architecture-overview.md`** consolidando
a visão sistêmica do projeto inteiro com as decisões da sessão #03
absorvidas. Estrutura sugerida:

1. **Visão de negócio** — uma frase explicando o que o sistema entrega
2. **Arquitetura em três camadas** — Política / multi-agente / CI-CD,
   diagrama mermaid (não ASCII)
3. **Fluxo de execução** — etapas 0-4, diagrama mermaid de fluxograma
4. **Componentes mapeados** — Política, MCP servers
   (`lgpd-policy-reader` e `semgrep-runner`), subagentes (cinco),
   hooks, recognizers brasileiros, benchmark, integração CI/CD
5. **Subagentes detalhados** — para cada um: responsabilidade
   (frase única sem "e"), tools permitidas, output esperado
6. **Posicionamento operacional** — Report como informativo no MVP,
   bloqueio condicional como evolução futura
7. **Fronteiras explícitas** — conformidade declarativa vs efetiva,
   PR-scoped vs system-wide, MVP vs trabalho futuro

Saída esperada: PR com `docs/architecture-overview.md` mergeado,
documento subido ao project knowledge para ficar acessível em todas
as sessões subsequentes.

**Sessão 5: redação do spec `docs/specs/lgpd-policy-reader.md` +
ADR-0002**, agora com a visão sistêmica firmada. Conteúdo já
acordado na sessão #03 (schema YAML v0.1.0, vocabulário de classes
em POL-000, resources, tools, contratos de erro, Output Report).
ADR-0002 com seção de deferimentos.

**Sessão 6: implementação do `lgpd-policy-reader` em FastMCP**,
com contrato fechado em spec.

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
  - **(novo) Subagentes do sistema multi-agente: cinco + coordinator.**
  Coordinator orquestra. Triager (etapa 0, decide proceed/skip),
  Detector (etapa 1, invoca Semgrep via MCP), Classifier (etapa 2,
  extrai structured_context por candidato), Matcher (etapa 3,
  descobre cláusulas e dispara check_applicability), Reporter
  (etapa 4, agrega vereditos no JSON do Report via tool customizada
  emit_report). Princípio: single responsibility per agent —
  responsabilidade nominal sem "e", tools restritas, system prompt
  focado. Severity-classifier e fix-proposer da proposta original
  saem do MVP (severidade fora; fix-proposer pode entrar em v2).
- **(novo) Etapa 0 (triagem de relevância) mora como subagente
  Triager**, não como hook PreToolUse do Claude Code. Razão:
  decisão é semi-semântica (paths + keywords + algum julgamento),
  trabalho de subagente; hook fica reservado para enforcement
  determinístico genuíno.
- **(novo) Output do Report no MVP é informativo, não bloqueia
  merge.** GitHub Action posta findings como inline comments no
  PR; merge não é travado por `violation_candidate`. Bloqueio
  condicional fica como evolução pós-validação empírica de FPR
  do sistema. Decisão pragmática para escopo de TCC com benchmark
  sintético de ~200 snippets — bloquear merge prematuramente força
  defesa de FPR em vez de demonstração de valor.
- **(novo) Classificação pode/consent/anon/proibido vive nas
  cláusulas da Política, não em campo separado nem em veredito.**
  Cláusula expressa exigência via `requirements`; veredito do
  agente reporta resultado de comparar código contra essas
  exigências. Fonte de verdade é a cláusula; veredito é derivação
  computada. Princípio anti-duplicação aplicado.
- **(novo) AEP fora do MVP, evolução pós-prova/pós-TCC.**
  Recognizers brasileiros (CPF, CNPJ, CNH, NIS/PIS, título de
  eleitor, CNS-saúde) mantidos como diferencial competitivo do MVP.

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