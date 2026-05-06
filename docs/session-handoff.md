# Session Handoff

> Estado operacional do projeto **agora**. Sobrescrito ao final de cada sessão.
> Não é registro histórico — para isso, ver `docs/learning-log.md`.
> Primeira leitura ao abrir nova conversa de Chat.

## Última atualização

**2026-05-05, sessão 4 (architecture-overview, proposta-tcc2 e sync de CLAUDE/README mergeados; e-mail para orientadora redigido)**

## Onde estamos

Final da semana 1 do cronograma de seis semanas. Quatro PRs
mergeados nesta sessão: `docs/architecture-overview.md` (visão
sistêmica do sistema em sete seções, com glossário, fluxo, matriz
de tools, posicionamento operacional e fronteiras epistêmicas),
`docs/proposta-tcc2.md` (proposta de orientação reescrita do zero
a partir do architecture-overview, com SDD como metodologia formal
e cronograma de seis semanas), e sincronização do `CLAUDE.md` e do
`README.md` com a arquitetura pós-sessão #03 (recognizers
brasileiros corrigidos, immutable rules reformuladas em torno do
vocabulário canônico do architecture-overview, working methodology
referenciando docs/specs/ e docs/adr/, frase de negócio canônica
no README, link para architecture-overview, stack expandida).

Decisão estrutural da sessão: adoção de Spec-Driven Development
como metodologia formal de execução do TCC. Web search confirmou
SDD como padrão estabelecido em 2025-2026 com Claude Code,
cobrindo simultaneamente Domínios 1, 3 e 4 da prova nos primitivos
canônicos. Cronograma reorganizado para agrupar specs por categoria
coerente (dois MCP servers juntos na semana 1, cinco subagentes
juntos na semana 3) com ciclo curto specify→implement por categoria
— meio termo entre spec-tudo-primeiro (waterfall) e um-por-vez-rígido.

E-mail para Profa. Alinne Cristinne Corrêa Souza redigido
(orientou TCC1 do mesmo aluno, conhecida). Envio agendado para
06/05/2026. Anexos: proposta-tcc2.md e architecture-overview.md,
ambos exportados em PDF via GitHub print-to-PDF. WhatsApp
follow-up curto após o envio.

## Branch atual

`main`. Limpa, sincronizada com origin.

## Próximo passo concreto

**Sessão 5: redação das specs dos dois MCP servers
(`docs/specs/lgpd-policy-reader.md` e `docs/specs/semgrep-runner.md`)
+ ADR-0002.** Conforme semana 1 da fase Specify do cronograma da
proposta-tcc2. Conteúdo do `lgpd-policy-reader` já acordado na
sessão #03 (schema YAML v0.1.0, vocabulário de classes em POL-000,
resources, tools, contratos de erro, Output Report). `semgrep-runner`
ainda sem decisões prévias — vai exigir trabalho de design durante
a redação. ADR-0002 com seção de deferimentos explícita.

Antes da redação técnica, dois itens institucionais a executar
fora desta sessão: (1) envio do e-mail à Profa. Alinne, agendado
para 06/05; (2) abertura de PR enxuto caso haja ajustes finais
necessários após primeiro contato com a orientadora.

**Sessões 6–8:** implementação dos dois MCP servers em FastMCP +
recognizers brasileiros (semana 2); specs dos cinco subagentes
e do coordinator (semana 3); implementação dos subagentes (semana 4).

**Sessões 9–10:** GitHub Action e integração end-to-end + benchmark
sintético (semana 5); validação empírica e redação do relatório
técnico de TCC2 (semana 6).

## Pendências não-bloqueantes

- **Envio do e-mail para Profa. Alinne — 06/05.** Texto pronto.
  Anexos a exportar em PDF via GitHub.
- Migração de conta GitHub para Team (ativa branch protection
  configurada em "Evaluate" mode)
- `~/.claude/CLAUDE.md` user-scope com preferências pessoais
  cross-projeto

## Estado da infraestrutura

- Repo: em `C:\Users\joaoguilherm.pereira\dev\lgpd-policy-review`
- VS Code: extensões instaladas e validadas (Python, Ruff, GitLens,
  Markdown All in One, Even Better TOML, YAML)
- Python 3.12.7 via pyenv-win, sem competição no PATH
- gh CLI autenticado como `paivapereira` via OAuth
- Claude Code CLI 2.1.123 autenticado, extensão VS Code funcional
- `.python-version` na raiz com `3.12.7`
- ADR-0001 e architecture-overview no project knowledge para
  contexto autoritativo entre sessões
- Branch protection ruleset criado em "Evaluate" mode (não enforça
  até migração para Team)

## Convenção de atualização

Último ato de toda sessão: editar este arquivo, commitar como
`docs: update session-handoff post-session-N`, push direto para main.
Não vai por PR — formalmente respaldado pela decisão 6 do ADR-0001
(direct-commit allowlist permanente).

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
- Schema YAML v0.1.0 da Política, resources e tools do
  `lgpd-policy-reader`, contratos de erro, vereditos do
  `check_applicability` — todos fechados na sessão #03 e absorvidos
  pelo architecture-overview
- Cinco subagentes single-responsibility (Triager, Detector,
  Classifier, Matcher, Reporter) + coordinator, com matriz de tools
  formalizada em architecture-overview §5.7
- Output do Report informativo no MVP (não bloqueia merge);
  bloqueio condicional como evolução pós-validação empírica
- AEP fora do MVP, sem reabertura prevista neste ciclo;
  recognizers brasileiros sintáticos cobrem o trabalho
- **(sessão #04) Spec-Driven Development como metodologia formal**
- **(sessão #04) Frase de negócio canônica fixada em três lugares**
  (architecture-overview, proposta-tcc2, README)
- **(sessão #04) Cronograma de seis semanas até 15/06**, organizado
  por categoria coerente de specs com ciclo curto specify→implement