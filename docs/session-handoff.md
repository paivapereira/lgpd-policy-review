# Session Handoff

> Estado operacional do projeto **agora**. Sobrescrito ao final de cada sessão.
> Não é registro histórico — para isso, ver `docs/learning-log.md`.
> Primeira leitura ao abrir nova conversa de Chat.

## Última atualização

**2026-05-06, sessão #05 (specs §1-§8 do policy-reader e _template emergente; 26 princípios em formação; SCHEMA stub criado; feedback de review crítico absorvido com escopo expandido para #06 e #08)**

## Onde estamos

Final do que era originalmente "fechamento da semana 1" do cronograma de seis semanas. O cronograma teve overflow controlado: a meta original previa specs completas dos dois MCP servers + ADR-0002 na semana 1; o que entregamos nesta sessão foi a spec do `policy-reader` integralmente, mais o `_template.md` derivado dela, mais stub do `policy/SCHEMA.md`. O `semgrep-runner.md` e o ADR-0002 deslizam para sessões #07 e #08 respectivamente, com a sessão #06 dedicada a cleanup expandido.

Decisão estrutural da sessão: renomeação do componente de `lgpd-policy-reader` para `policy-reader` (componente agnóstico ao conteúdo; LGPD é o que a Política do MVP carrega, não o que o componente conhece). Cleanup de propagação adiado para PR enxuto na sessão #06.

Decisão de produto: escopo da Política do MVP restrito a duas dimensões avaliáveis por análise estática — `consent_required` e `anonymization_required`. Outras dimensões da LGPD (transfer restrictions, retention, direitos do titular, dados de menores, tratamento compartilhado) ficam fora do MVP. Registrado na §7.2 da spec; sync para architecture-overview e proposta-tcc2 fica para o PR de cleanup; trilha de auditoria em ADR-0002.

Validação metodológica: pareamento template↔spec funcionou — extraiu padrões cedo, sem precisar de sessão dedicada para refatorar template. Revisão sistemática §1-§8 detectou três contradições silenciosas que teriam virado bugs em implementação.

Feedback de review crítico recebido ao final da sessão (documento externo `compass_artifact_wf-f959a90b...md`). Filtragem aplicada: dos 15 itens do feedback, sete entram no cronograma atual por terem impacto bloqueante em sessões futuras (três triviais para a #06, quatro arquiteturais para o ADR-0002 da #08, um para a primeira spec de subagente da semana 3). Oito itens ficam fora do cronograma por serem otimização estética ou prioridade de prova sem impacto no TCC; alguns voltam como pendência pós-cronograma para preparação da prova de certificação.

Resposta da Profa. Alinne via WhatsApp confirmou recebimento e indicou que vai analisar o e-mail. Aguardando retorno técnico sobre proposta-tcc2 e architecture-overview.

## Branch atual

`main`. Limpa, sincronizada com origin.

## Próximo passo concreto

**Sessão #06: PR enxuto de cleanup pós-renomeação, sync de escopo restrito da Política, e quatro edições mínimas absorvidas do feedback de review.**

Conteúdo do PR:

1. Renomeação `lgpd-policy-reader` → `policy-reader` em seis arquivos: `architecture-overview.md`, `learning-log.md` (entradas anteriores à #05), `session-handoff.md` (já feito nesta sobrescrita), `proposta-tcc2.md`, `CLAUDE.md`, `README.md`.

2. Sync da decisão de escopo restrito da Política: `architecture-overview.md` §6 ou §8 ganha linha curta; `proposta-tcc2.md` §8 ganha linha curta. Coerência cruzada com a §7.2 da spec do `policy-reader.md`.

3. **Frase de convenção de erro** em §5.1 de `docs/specs/_template.md` e de `docs/specs/policy-reader.md` declarando que o contrato `errorCode`/`message`/`isRetryable`/`details` é convenção deste projeto serializada dentro do campo `content` do `CallToolResult`, sobreposta ao único campo de erro nativo do MCP que é o booleano `isError`.

4. **Nota no topo do `_template.md`** (após `spec_version`): "Este template assume componente que expõe contrato MCP (resources e/ou tools). Para componentes do tipo subagente — Triager, Detector, Classifier, Matcher, Reporter, coordinator — derivar `_template-subagent.md` na primeira spec de subagente da semana 3 (mesmo método de destilação aplicado a este template)."

5. **Versão alvo do Claude Code** em `CLAUDE.md` (Status flags ou seção apropriada): linha declarando "Claude Code v2.1.x ou superior" como alvo do projeto. Versão exata a confirmar contra o ambiente local antes do commit.

6. **Convenção de naming MCP** em §4 do `_template.md` e linha equivalente em `policy-reader.md` §4 ou §1: explicitar que tools deste server, quando consumidas por subagente Claude Code, são acessíveis via padrão `mcp__<server-name>__<tool-name>` (ex: `mcp__policy-reader__get_clause`). Padrão relevante para `allowed-tools` em frontmatter de subagente e para hook matchers.

7. Caso necessário após resposta técnica da Profa. Alinne, ajustes adicionais à `proposta-tcc2.md` no mesmo PR.

Após o cleanup, abertura de §1 do `docs/specs/semgrep-runner.md` ainda na sessão #06 se houver tempo, ou início clean da sessão #07.

**Sessões #07 e seguintes:**

- **Sessão #07:** redação completa de `docs/specs/semgrep-runner.md`. Design real — `semgrep-runner` não tem decisões prévias e exige trabalho de design durante a redação. Pontos a decidir: unidade de invocação, regras como argumento ou pré-instaladas, streaming de findings ou retorno em bloco, representação de localização (file+line+col, range, snippet), tratamento de timeouts longos, contrato de erro específico do runner. Aplicação dos 26 princípios do `_template.md`; ajustes ao template quando emergirem.

- **Sessão #08 — ADR-0002 com escopo expandido.** Conteúdo:

  - **Deferimentos originalmente planejados:** scheme `policy://` adotado por convenção (com base em web search da #03), browseability humana de cláusulas individuais, hot reload da Política, suporte a schemas alternativos, anotações declarativas de tratamento no código, escopo ampliado da Política, mapa cross-PR longitudinal. Critérios de revisita explícitos por deferimento. Cláusula sobre versionamento da própria spec do `policy-reader`.

  - **Quatro decisões arquiteturais novas absorvidas do feedback:**

    a. **Materialização de subagentes.** Decisão entre arquivos `.claude/agents/<name>.md` em project-scope (declarativo, comitado no Git, escolha default proposta) versus `AgentDefinition` programática via Claude Agent SDK (`agents` em `ClaudeAgentOptions`). Decisão default tem que listar quais campos do frontmatter serão usados (`name`, `description`, `tools`, `model`, `mcpServers`, possivelmente `memory: project`). Esta é a decisão arquitetural ausente número um e bloqueia semana 3.

    b. **Orquestração do coordinator.** Decisão entre Task tool dentro de sessão Claude Code (com `agents:` em `ClaudeAgentOptions`), subprocesso `claude -p --output-format json` chamado pelo GitHub Action, ou combinação híbrida. Esta decisão afeta `architecture-overview` §3 e §5, e bloqueia tanto semana 3 (spec do coordinator) quanto semana 5 (GitHub Action). Decisão precisa nominar como `stop_reason`, `session_id`, `total_cost_usd`, `usage`, `result` chegam ao consumidor.

    c. **Hooks operacionais nominados.** Nominação preliminar de quatro pontos de aplicação: PostToolUse com matcher `mcp__policy-reader__check_applicability` para validar veredito + clause_id antes do output retornar ao Matcher; PostToolUse em `emit_report` para validar que toda finding tem `clause_id`; Stop hook no Reporter para impedir terminação com `findings` vazios sem justificativa; SessionStart com matcher `compact` para reinjetar regras imutáveis após compaction. Detalhe de implementação fica para semana 4 — o ADR registra o compromisso e o evento de hook por regra imutável, transformando regras-promessa em invariantes-enforçáveis.

    d. **Scratchpad pattern entre subagentes.** Decisão sobre uso de `data/runs/<run_id>/progress.md` (ou equivalente) como artefato durável entre etapas do pipeline. Se decidirmos usar, isso afeta spec do Coordinator e do Reporter da semana 3. Se decidirmos não usar (passagem direta de estado via Task tool sem persistência intermediária), o Reporter precisa receber findings completos do Matcher em um único turno — o que tem implicação para janelas longas com diffs grandes.

  - **Justificativa adicional sobre stack:** parágrafo no ADR-0002 abordando explicitamente FastMCP 2.x como linha de manutenção estável vs. 3.x lançada em fevereiro/2026. Esta é uma decisão defensiva — banca pode perguntar.

- **Semana 3 (specs dos cinco subagentes):** primeira spec (provavelmente Matcher, que é o consumidor mais conhecido) deriva por destilação um `_template-subagent.md` por aplicação do mesmo método usado para o `_template.md` na #05. Subagentes não expõem resources nem tools próprios — eles consomem; seções 3 e 4 do template viram "Resources consumidos" e "Tools consumidas". Estrutura completa do template-subagent emerge da redação concreta, não da especulação a priori.

- **Sessão pós-#07 (datada conforme andamento):** consolidação dos 26 princípios em `docs/spec-authoring-principles.md` canônico, com nome + regra + racional + exemplo por princípio. Documento citável pelo relatório de TCC2 como contribuição metodológica.

**Cronograma realista revisado:**

| Semana original | Período | Estado |
|:---:|:---|:---|
| 1 (Specify) | 05/05 – 11/05 | Parcial: `policy-reader.md` + `_template.md` + `SCHEMA.md` stub. Cleanup expandido #06 + `semgrep-runner.md` #07 + ADR-0002 expandido #08 deslizam. |
| 2 (Implement) | 12/05 – 18/05 | Implementação dos dois MCP servers + redação de `policy/SCHEMA.md` em paralelo + recognizers brasileiros. Pode acumular sobre semana 1 estendida se sessão #08 terminar tarde. |
| 3 (Specify) | 19/05 – 25/05 | Specs dos cinco subagentes e do coordenador. Primeira spec deriva `_template-subagent.md` por destilação. Decisões arquiteturais do ADR-0002 já fechadas — aplicação direta. |
| 4 (Implement) | 26/05 – 01/06 | Implementação dos subagentes, coordenador e tool customizada `emit_report`. Hooks nominados no ADR-0002 implementados. |
| 5 (Implement + Validate) | 02/06 – 08/06 | GitHub Action; integração end-to-end; benchmark sintético. |
| 6 (Validate) | 09/06 – 15/06 | Validação empírica; redação do relatório técnico de TCC2; entrega. |

Folga existente em semanas 2 e 4 absorve overflow da semana 1 sem ameaçar a entrega de 15/06.

## Pendências pós-cronograma para preparação da prova de certificação

Itens do feedback de review identificados como otimização para a prova de certificação Claude Certified Architect (Foundations) que ficam fora do cronograma do TCC. Reservar tempo após a defesa de 15/06 e antes da prova:

- Materialização de pelo menos uma skill em `.claude/skills/<name>/SKILL.md` com frontmatter completo (`allowed-tools`, `disable-model-invocation`, `description` "pushy" com gatilhos concretos). Candidato natural: `redact-pii-from-paste`, hoje regra textual em CLAUDE.md.
- Materialização de pelo menos um slash command em `.claude/commands/<name>.md` (ex: `run-pipeline-dry.md`).
- Materialização de pelo menos um arquivo `.claude/agents/<name>.md` mesmo que stub, para exercitar frontmatter de subagente em project-scope.
- Materialização de hooks decididos no ADR-0002 (semana 4 do cronograma já cobre isso, mas validação adicional pós-defesa).
- Citações bibliográficas: Anthropic "Building Effective AI Agents", "Effective harnesses for long-running agents", `github/spec-kit`, panaversity SDD paper. Inclusão em `spec-authoring-principles.md` quando este existir.

Essas pendências cobrem o gap de Domínio 3 (Claude Code Configuration & Workflows) apontado no review. Não são requisito do TCC, mas são central à prova.

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
- **(sessão #05) Filtragem de feedback de review crítico:** sete itens no cronograma (três triviais #06, quatro arquiteturais ADR-0002, um para semana 3); oito itens fora (estética ou pendência de prova pós-cronograma)

## Pendências não-bloqueantes

- PR de cleanup expandido da sessão #06 (sete itens listados em "Próximo passo concreto")
- `policy/SCHEMA.md` redação completa em paralelo à implementação (semana 2)
- ADR-0002 expandido (sessão #08) com quatro decisões arquiteturais novas + deferimentos originais
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