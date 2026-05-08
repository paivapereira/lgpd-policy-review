# Session Handoff

> Estado operacional do projeto **agora**. Sobrescrito ao final de cada sessão.
> Não é registro histórico — para isso, ver `docs/learning-log.md`.
> Primeira leitura ao abrir nova conversa de Chat.

## Última atualização

**2026-05-07, sessão #06 (PR de cleanup pós-renomeação mergeado: cinco logical units fechados, escopo da Política sincronizado em três documentos, placement híbrido `structuredContent`+`content` adotado, naming convention MCP documentada nas specs, versão alvo do Claude Code declarada)**

## Onde estamos

Final efetivo da semana 1 do cronograma de seis semanas. A #05 entregou a spec do `policy-reader` integralmente, o `_template.md` derivado dela e o stub do `policy/SCHEMA.md`; a #06 fechou o débito técnico que sobrou da #05 e absorveu as quatro edições mínimas do feedback de review crítico. O `semgrep-runner.md` e o ADR-0002 seguem deslizados para sessões #07 e #08 respectivamente.

PR `docs/session-06-cleanup` mergeado em `main` via squash (commit `6945840`). Cinco logical units no branch antes do squash, granularidade fina preservada para revisão; main agora carrega um único commit consolidado.

Decisões estruturais da #06: (a) logs históricos (`learning-log.md`, `session-handoff.md`) preservados intactos durante propagação de renomeação — log é registro fiel da evolução, não documento sob refatoração; (b) placement híbrido `structuredContent` + `content` adotado para CallToolResult tanto em sucesso quanto em erro, alinhado ao comportamento atual do Claude Code 2.0.22+ que prioriza `structuredContent` quando ambos os canais estão presentes; (c) naming convention `mcp__<server>__<tool>` documentada na §4 das specs como handle gerado pelo runtime, relevante para `allowed-tools` em frontmatter, `mcp_servers`/`allowed-tools` em AgentDefinition e matchers de hooks PreToolUse/PostToolUse.

Item 7 do plano original do PR (ajustes adicionais à `proposta-tcc2.md` após resposta técnica da Profa. Alinne) ficou sem trigger nesta sessão — o retorno ainda não chegou. Próxima oportunidade de absorção fica para o próximo PR de docs ou para sessão dedicada quando o retorno vier.

Validação meta da sessão: discrepância no handoff anterior identificada e corrigida durante a execução (handoff dizia "architecture-overview §6 ou §8" para sync de escopo; documento tem 7 seções e o local correto era §7.3). Lição registrada no learning-log: handoff é instrumento de continuidade, hipótese a verificar contra o estado atual do documento, não verdade canônica.

## Branch atual

`main`. Limpa, sincronizada com origin. Branch `docs/session-06-cleanup` mergeado e pode ser deletado localmente (`git branch -d docs/session-06-cleanup`) sem prejuízo — squash já está em main.

## Próximo passo concreto

**Sessão #07: redação completa de `docs/specs/semgrep-runner.md`.**

Diferente do `policy-reader`, este componente não tem decisões prévias acumuladas das sessões #03-#05 — é design real durante a redação. Pontos a decidir explicitamente:

- **Unidade de invocação:** arquivo, diff de PR, projeto inteiro? Detector consome o diff de um PR — provavelmente unidade é o conjunto de arquivos modificados, mas a tool pode ser per-file ou batch.
- **Regras como argumento ou pré-instaladas:** o caller (Detector) escolhe quais regras aplicar a cada invocação, ou o server expõe um set fixo curado pelo projeto?
- **Streaming de findings vs retorno em bloco:** Semgrep pode rodar minutos em codebases grandes. Streaming via MCP é viável tecnicamente mas adiciona complexidade ao caller.
- **Representação de localização:** file+line+col simples, range completo (start_line, start_col, end_line, end_col), com ou sem snippet do código matched, com ou sem context (linhas antes/depois)?
- **Tratamento de timeouts longos:** Semgrep não trivialmente cancelável; falha por timeout é caso explícito no contrato de erro?
- **Contrato de erro específico:** classes esperadas além das três canônicas (validation/business/system)? `RULE_NOT_FOUND`, `INVALID_RULE_SYNTAX`, `SCAN_TIMEOUT`, `BINARY_NOT_AVAILABLE`?

Aplicação dos 26 princípios destilados na #05 — segunda aplicação. `_template.md` permanece "em formação até validação na redação do `semgrep-runner.md`"; ajustes ao template esperados quando emergirem assimetrias entre os dois servers.

**Sessões #08 e seguintes (visão geral):**

- **Sessão #08:** ADR-0002 expandido com seis decisões arquiteturais — quatro originais (escopo de schema, hot reload, anotações declarativas, browseability humana) + duas absorvidas do feedback de review crítico (a definir após reler o documento de feedback) + a decisão de placement híbrido formalizada como decisão arquitetural (em vez de só convenção registrada nas specs).
- **Semana 2 (sessões #09-#10):** redação completa de `policy/SCHEMA.md` em paralelo à implementação do `policy-reader` em FastMCP. SCHEMA.md fica concreto enquanto a implementação valida ou ajusta decisões. Implementação inclui handshake do resource `policy://schema-version`, três tools com `inputSchema`, contrato de erro com placement híbrido, testes pytest.
- **Semana 3:** specs dos cinco subagentes + coordinator, com derivação de `_template-subagent.md` durante a primeira spec.
- **Semanas 4-5:** implementação dos subagentes, integração GitHub Action, recognizers brasileiros.
- **Semana 6:** benchmark sintético, validação empírica, redação do relatório técnico de TCC2 (entrega 15/06).

## Decisões fechadas (referência rápida)

Cumulativo, em ordem cronológica reversa. Detalhes em `learning-log.md` na entry da sessão correspondente.

- **(sessão #06) Logs históricos preservados durante propagação de renomeação** (`learning-log.md`, `session-handoff.md` ficaram intactos; só arquivos vivos receberam substituição)
- **(sessão #06) Sync da decisão de escopo restrito da Política em três documentos** (`policy-reader.md` §7.2 canônica, `architecture-overview.md` §7.3 nova linha de tabela, `proposta-tcc2.md` §8 item adicional em "Fora do escopo")
- **(sessão #06) Placement híbrido `structuredContent` + `content` para CallToolResult** (sucesso e erro; payload estruturado em `structuredContent`, prosa humana em `content[0].text`; alinhado a Claude Code 2.0.22+)
- **(sessão #06) Convenção de erro do projeto sobreposta ao protocolo MCP** (`errorCode`/`message`/`isRetryable`/`details` materializa "validation/business/system" e decisão de retry; único campo de erro nativo do MCP é o booleano `isError`)
- **(sessão #06) `_template.md` declarado escopo a componentes MCP** (subagentes terão `_template-subagent.md` derivado na primeira spec de subagente da semana 3)
- **(sessão #06) Versão alvo Claude Code CLI v2.1.123 ou superior** (validado localmente; floor empírico, não pin nem floor genérico)
- **(sessão #06) Naming convention `mcp__<server>__<tool>` documentada nas specs** (forma usada em `allowed-tools`, `mcp_servers` em AgentDefinition, e matchers de hooks)
- **(sessão #05) Renomeação `lgpd-policy-reader` → `policy-reader`** (componente agnóstico ao conteúdo)
- **(sessão #05) Spec do `policy-reader.md` v0.1.0 fechada** em oito seções
- **(sessão #05) `_template.md` v0.1.0 derivado e estabilizado**, marcado como "em formação até segunda aplicação"
- **(sessão #05) Escopo restrito da Política do MVP** a `consent_required` e `anonymization_required`
- **(sessão #05) `clause_id` formato `POL-NNN`** (três dígitos zero-padded, regex `^POL-\d{3}$`)
- **(sessão #05) Vocabulário de `lei` no MVP via header `accepted_law_identifiers`** do arquivo da Política
- **(sessão #05) Estrutura de `verification_scope`** em vereditos `indeterminate`: dimension, prescribed_treatment, policy_clause_ref, verification_target
- **(sessão #05) Princípio universal de review pass spec ↔ architecture-overview** (§8.<final> de toda spec)
- **(sessão #05) Filtragem de feedback de review crítico:** sete itens no cronograma (três triviais #06 — todos absorvidos; quatro arquiteturais ADR-0002 #08; um para semana 3); oito itens fora (estética ou pendência de prova pós-cronograma)
- **(sessão #04) Spec-Driven Development como metodologia formal**
- **(sessão #04) Frase de negócio canônica fixada em três lugares** (architecture-overview, proposta-tcc2, README)
- **(sessão #04) Cronograma de seis semanas até 15/06**, organizado por categoria coerente de specs com ciclo curto specify→implement
- **(sessão #03) Output do Report informativo no MVP** (não bloqueia merge; bloqueio condicional como evolução pós-validação empírica)
- **(sessão #03) AEP fora do MVP**, sem reabertura prevista neste ciclo; recognizers brasileiros sintáticos cobrem o trabalho

## Pendências não-bloqueantes

- **Provenance temporal nos exemplos de `check_applicability`** — `policy_schema_version` e `policy_version` declarados na §6.4 da spec do `policy-reader` mas omitidos dos exemplos de §4. Débito técnico identificado durante a #06, deferido. Tocar em uma das duas próximas oportunidades: junto com a redação do `semgrep-runner.md` se ele expuser provenance equivalente, ou no PR de implementação do `policy-reader` quando os exemplos virarem testes.
- **`policy/SCHEMA.md` redação completa em paralelo à implementação** (semana 2)
- **ADR-0002 expandido (sessão #08)** com quatro decisões arquiteturais originais + decisões absorvidas do feedback de review + placement híbrido formalizado
- **Consolidação de `docs/spec-authoring-principles.md`** (sessão pós-#07, após validação dos 26 princípios na redação do `semgrep-runner.md`)
- **Decisão operacional sobre onde mora o template canônico** (`.claude/skills/spec-author/SKILL.md` referenciando `docs/specs/_template.md`, ou alternativa). Resolução natural quando o template estabilizar pós-#07.
- **Migração de conta GitHub para Team** (ativa branch protection configurada em "Evaluate" mode)
- **`~/.claude/CLAUDE.md` user-scope com preferências pessoais cross-projeto**
- **Aguardando retorno técnico da Profa. Alinne** sobre proposta-tcc2 e architecture-overview. Se chegar antes da sessão #07, ajustes podem entrar como item 0 da sessão; se chegar depois, vão para PR dedicado de docs.