# Session Handoff

> Estado operacional do projeto **agora**. Sobrescrito ao final de cada sessão.
> Não é registro histórico — para isso, ver `docs/learning-log.md`.
> Primeira leitura ao abrir nova conversa de Chat.

## Última atualização

**2026-05-06, sessão #05 (specs §1-§8 do policy-reader e _template emergente; 26 princípios em formação; SCHEMA stub criado)**

## Onde estamos

Final do que era originalmente "fechamento da semana 1" do cronograma de seis semanas. O cronograma teve overflow controlado: a meta original previa specs completas dos dois MCP servers + ADR-0002 na semana 1; o que entregamos nesta sessão foi a spec do `policy-reader` integralmente, mais o `_template.md` derivado dela, mais stub do `policy/SCHEMA.md`. O `semgrep-runner.md` e o ADR-0002 deslizam para sessões #07 e #08 respectivamente, com a sessão #06 dedicada a cleanup.

Decisão estrutural da sessão: renomeação do componente de `lgpd-policy-reader` para `policy-reader` (componente agnóstico ao conteúdo; LGPD é o que a Política do MVP carrega, não o que o componente conhece). Cleanup de propagação adiado para PR enxuto na sessão #06.

Decisão de produto: escopo da Política do MVP restrito a duas dimensões avaliáveis por análise estática — `consent_required` e `anonymization_required`. Outras dimensões da LGPD (transfer restrictions, retention, direitos do titular, dados de menores, tratamento compartilhado) ficam fora do MVP. Registrado na §7.2 da spec; sync para architecture-overview e proposta-tcc2 fica para o PR de cleanup; trilha de auditoria em ADR-0002.

Validação metodológica: pareamento template↔spec funcionou — extraiu padrões cedo, sem precisar de sessão dedicada para refatorar template. Revisão sistemática §1-§8 detectou três contradições silenciosas que teriam virado bugs em implementação.

Resposta da Profa. Alinne via WhatsApp confirmou recebimento e indicou que vai analisar o e-mail. Aguardando retorno técnico sobre proposta-tcc2 e architecture-overview.

## Branch atual

`main`. Limpa, sincronizada com origin.

## Próximo passo concreto

**Sessão #06: PR enxuto de cleanup pós-renomeação e sync de escopo restrito da Política.**

Conteúdo do PR:

1. Renomeação `lgpd-policy-reader` → `policy-reader` em seis arquivos: `architecture-overview.md`, `learning-log.md` (entradas anteriores à #05), `session-handoff.md` (já feito nesta sobrescrita), `proposta-tcc2.md`, `CLAUDE.md`, `README.md`.

2. Sync da decisão de escopo restrito da Política: `architecture-overview.md` §6 ou §8 ganha linha curta; `proposta-tcc2.md` §8 ganha linha curta. Coerência cruzada com a §7.2 da spec do `policy-reader.md`.

3. Caso necessário após resposta técnica da Profa. Alinne, ajustes adicionais à `proposta-tcc2.md` no mesmo PR.

Após o cleanup, abertura de §1 do `docs/specs/semgrep-runner.md` ainda na sessão #06 se houver tempo, ou início clean da sessão #07.

**Sessões #07 e seguintes:**

- **Sessão #07:** redação completa de `docs/specs/semgrep-runner.md`. Design real — `semgrep-runner` não tem decisões prévias e exige trabalho de design durante a redação. Pontos a decidir: unidade de invocação, regras como argumento ou pré-instaladas, streaming de findings ou retorno em bloco, representação de localização (file+line+col, range, snippet), tratamento de timeouts longos, contrato de erro específico do runner. Aplicação dos 26 princípios do `_template.md`; ajustes ao template quando emergirem.

- **Sessão #08:** ADR-0002 com seção de deferimentos explícita. Conteúdo: scheme `policy://` adotado por convenção (com base em web search da #03), browseability humana de cláusulas individuais, hot reload da Política, suporte a schemas alternativos, anotações declarativas de tratamento no código, escopo ampliado da Política (transfer restrictions, retention, direitos do titular), mapa cross-PR longitudinal. Cláusula sobre versionamento da própria spec do `policy-reader`. Critérios de revisita explícitos por deferimento.

- **Sessão pós-#07 (datada conforme andamento):** consolidação dos 26 princípios em `docs/spec-authoring-principles.md` canônico, com nome + regra + racional + exemplo por princípio. Documento citável pelo relatório de TCC2 como contribuição metodológica.

**Cronograma realista revisado:**

| Semana original | Período | Estado |
|:---:|:---|:---|
| 1 (Specify) | 05/05 – 11/05 | Parcial: `policy-reader.md` + `_template.md` + `SCHEMA.md` stub. Cleanup #06 + `semgrep-runner.md` #07 + ADR-0002 #08 deslizam. |
| 2 (Implement) | 12/05 – 18/05 | Implementação dos dois MCP servers + redação de `policy/SCHEMA.md` em paralelo + recognizers brasileiros. Pode acumular sobre semana 1 estendida se sessão #08 terminar tarde. |
| 3 (Specify) | 19/05 – 25/05 | Specs dos cinco subagentes e do coordenador. |
| 4 (Implement) | 26/05 – 01/06 | Implementação dos subagentes, coordenador e tool customizada `emit_report`. |
| 5 (Implement + Validate) | 02/06 – 08/06 | GitHub Action; integração end-to-end; benchmark sintético. |
| 6 (Validate) | 09/06 – 15/06 | Validação empírica; redação do relatório técnico de TCC2; entrega. |

Folga existente em semanas 2 e 4 absorve overflow da semana 1 sem ameaçar a entrega de 15/06.

## Decisões fechadas (não revisitar)

- Repositório: monorepo `paivapereira/lgpd-policy-review`, privado, MIT (código)
- Política sob `policy/` terá licença separada (CC-BY provável), decidido em ADR futuro antes de v1.0 ou abertura pública
- Stack: ver CLAUDE.md seção "Stack (canonical)" e ADR-0001 §2
- Idiomas: ver CLAUDE.md seção "Languages" e ADR-0001 §3
- Workflow git: feature branches + PR + squash merge + delete branch (ADR-0001 §5)
- Direct-commit allowlist permanente: apenas `docs/session-handoff.md` e `docs/learning-log.md` (ADR-0001 §6)
- Conventional Commits
- Formato de ADR: Nygard expandido para decisões compostas; MADR reservado para futuras decisões com trade-off comparativo real
- Schema YAML v0.1.0 da Política, resources e tools do `policy-reader`, contratos de erro, vereditos do `check_applicability` — todos fechados na sessão #03 e absorvidos pelo architecture-overview e pela spec do `policy-reader.md` redigida na #05
- Cinco subagentes single-responsibility (Triager, Detector, Classifier, Matcher, Reporter) + coordinator, com matriz de tools formalizada em architecture-overview §5.7
- Output do Report informativo no MVP (não bloqueia merge); bloqueio condicional como evolução pós-validação empírica
- AEP fora do MVP, sem reabertura prevista neste ciclo; recognizers brasileiros sintáticos cobrem o trabalho
- (sessão #04) Spec-Driven Development como metodologia formal
- (sessão #04) Frase de negócio canônica fixada em três lugares (architecture-overview, proposta-tcc2, README)
- (sessão #04) Cronograma de seis semanas até 15/06, organizado por categoria coerente de specs com ciclo curto specify→implement
- **(sessão #05) Renomeação `lgpd-policy-reader` → `policy-reader`** (componente agnóstico ao conteúdo)
- **(sessão #05) Spec do `policy-reader.md` v0.1.0 fechada** em oito seções
- **(sessão #05) `_template.md` v0.1.0 derivado e estabilizado**, marcado como "em formação até segunda aplicação"
- **(sessão #05) Escopo restrito da Política do MVP** a `consent_required` e `anonymization_required` (cleanup propagacional na #06)
- **(sessão #05) `clause_id` formato `POL-NNN`** (três dígitos zero-padded, regex `^POL-\d{3}$`)
- **(sessão #05) Vocabulário de `lei` no MVP via header `accepted_law_identifiers`** do arquivo da Política
- **(sessão #05) Estrutura de `verification_scope`** em vereditos `indeterminate`: dimension, prescribed_treatment, policy_clause_ref, verification_target
- **(sessão #05) Princípio universal de review pass spec ↔ architecture-overview** (§8.<final> de toda spec)

## Pendências não-bloqueantes

- PR de cleanup da sessão #06 (renomeação em seis arquivos + sync de escopo restrito da Política em `architecture-overview.md` e `proposta-tcc2.md`)
- `policy/SCHEMA.md` redação completa em paralelo à implementação (semana 2)
- ADR-0002 (sessão #08)
- Consolidação de `docs/spec-authoring-principles.md` (sessão pós-#07)
- Decisão de onde mora o template canônico operacionalmente: `.claude/skills/spec-author/SKILL.md` referenciando `docs/specs/_template.md`, ou alternativa. Resolução natural quando o template estabilizar pós-#07.
- Migração de conta GitHub para Team (ativa branch protection configurada em "Evaluate" mode)
- `~/.claude/CLAUDE.md` user-scope com preferências pessoais cross-projeto
- Aguardando retorno técnico da Profa. Alinne sobre proposta-tcc2 e architecture-overview

## Estado da infraestrutura

- Repo: em `C:\Users\joaoguilherm.pereira\dev\lgpd-policy-review`
- VS Code: extensões instaladas e validadas (Python, Ruff, GitLens, Markdown All in One, Even Better TOML, YAML)
- Python 3.12.7 via pyenv-win, sem competição no PATH
- gh CLI autenticado como `paivapereira` via OAuth
- Claude Code CLI 2.1.123 autenticado, extensão VS Code funcional
- `.python-version` na raiz com `3.12.7`
- ADR-0001, architecture-overview, `docs/specs/policy-reader.md`, `docs/specs/_template.md` no project knowledge para contexto autoritativo entre sessões
- `policy/SCHEMA.md` stub no repositório, redação completa pendente para semana 2
- Branch protection ruleset criado em "Evaluate" mode (não enforça até migração para Team)

## Convenção de atualização

Último ato de toda sessão: editar este arquivo, commitar como `docs: update session-handoff post-session-N`, push direto para main. Não vai por PR — formalmente respaldado pela decisão 6 do ADR-0001 (direct-commit allowlist permanente).