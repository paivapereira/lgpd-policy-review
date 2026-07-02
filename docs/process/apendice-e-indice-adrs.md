<!--
APÊNDICE E — índice condensado das ADRs (fonte Markdown para conversão .docx ABNT)
Fonte: docs/adr/ @ commit 61a6585247867da4f4a19f27a12ebc8a1fa7ba14 (último commit que
alterou docs/adr/ — squash do PR #124, ratificação das ADRs 0011/0013/0015). Os links dos
demais apêndices do relatório ainda pinam 61e358b; alinhar todos ao pin final antes da
versão entregue. Se qualquer ADR mudar
antes da versão final do relatório, atualizar o pin dos permalinks e regerar as linhas
de decisão afetadas. Cada linha de decisão foi extraída da íntegra da ADR e verificada
por revisão independente contra o artefato (fidelidade extrativa, sem racional).
-->

# APÊNDICE E — Decisões arquiteturais (ADRs): índice condensado

O repositório registra dezesseis *Architecture Decision Records* (ADR-0001 a ADR-0016) sob `docs/adr/`, totalizando cerca de 2.700 linhas. Na forma de trechos selecionados autorizada pelo preâmbulo destes Apêndices, este índice apresenta, para cada ADR: o título original (as ADRs são redigidas em inglês, por convenção do próprio projeto — ADR-0006), o status transcrito fielmente do artefato, a decisão condensada em uma linha, as emendas registradas e o permalink para a íntegra versionada. As ADRs assinaladas com † são citadas no corpo deste relatório. Os status refletem os artefatos no commit pinado, já incorporada a ratificação de 2026-07-02 (PR #124), que aceitou as ADRs 0013 e 0015 e emendou a ADR-0011 — fechando o achado XDOC-15 do relatório de QA (Apêndice F, Quadro 14).

**Balanço.** Dezesseis ADRs aceitas. Treze foram aceitas ao longo do desenvolvimento (0001–0010, 0012, 0014, 0016); as três restantes (0011, 0013, 0015) foram ratificadas/emendadas pelo autor em 2026-07-02 (PR #124), com uma distinção honesta preservada nos próprios artefatos: na ADR-0011 o eixo D2 e na ADR-0015 a mudança de engine estão decididos, mas com implementação declaradamente diferida a trabalho futuro.

---

**ADR-0001 — Bootstrap of the lgpd-policy-review project** †
**Status:** Aceita (2026-05-01, sessão #01); emendas in-place posteriores.
**Decisão:** Estabelecer o bootstrap: monorepo privado único com código sob MIT e stack canônica pinada (Python 3.12.7, `claude-agent-sdk`, FastMCP, Pydantic, Semgrep); inglês para código e português para conteúdo legal; e três regras de domínio imutáveis registradas em `CLAUDE.md`, com fluxo git de Conventional Commits e squash-merge.
**Emendas:** Decisão 2 em 2026-05-21 (pins formais `fastmcp==3.2.4`, `pydantic==2.13.4`, `mcp==1.27.1`, `semgrep==1.163.0`; pivô Presidio → Semgrep por ADR-0010) e em 2026-05-30 (pin `claude-agent-sdk==0.2.87`); Decisão 3 em 2026-05-22 (IDs opacos `POL-NNN` em vez de `LGPD-Art-7-I`); Decisão 4 em 2026-05-24 (sync das regras imutáveis com `CLAUDE.md`).
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0001-bootstrap.md>

**ADR-0002 — MCP server conventions and deferred decisions**
**Status:** Aceita (sessão #09, 2026-05-10).
**Decisão:** Consolida sete convenções de projeto para servidores MCP — payload híbrido `structuredContent` + `content`, nomenclatura `mcp__<server>__<tool>`, contrato de erro em três classes (`validation`, `business`, `system`), versionamento de specs e esquemas de URI customizados (`policy://`) — e registra em ledger único os deferimentos A–I com critérios de revisita.
**Emendas:** 2026-05-17, Decisão 3: envelope de erro serializado em `structuredContent` com wire `isError: false` (restrição do FastMCP 3.2.4); a presença de `errorCode` passa a ser o discriminador sucesso/erro.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0002-mcp-conventions-and-deferments.md>

**ADR-0003 — Dual-spec architecture: consumed/reference frame and §8.\<final\> lifecycle**
**Status:** Aceita (retrospectiva — decisões das sessões #11 e #12, formalizadas em 2026-05-13).
**Decisão:** Adota o frame consumido/referência para as specs duais — `compact.md` é o artefato que o agente implementador consome e `canonical.md` é referência sob demanda, com paridade restrita a superfícies de contrato — e formaliza o ciclo de vida da seção §8.\<final\> das specs.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0003-dual-spec-architecture.md>

**ADR-0004 — uv adoption and FastMCP 3.x pin** †
**Status:** Aceita (sessão #17, 2026-05-16); ratificação retrospectiva do estado de facto desde a sessão #14 (2026-05-12).
**Decisão:** Adota `uv` como ferramenta unificada de gestão de dependências e de versão de Python (`pyproject.toml` PEP 621, `uv.lock` versionado, `uv sync`, backend `uv_build`, `.python-version` fixando 3.12.7); e fixa FastMCP na linha 3.x (`>=3.2.0,<4.0`).
**Relações:** Supersede parcialmente a ADR-0001 §2 — gestão de versão de Python (pyenv-win → uv) e versão do FastMCP (sem pin → `>=3.2.0,<4.0`).
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0004-uv-and-fastmcp-3x.md>

**ADR-0005 — Architecture for multi-client policy support: vocabularies as data, LGPD as instance** †
**Status:** Aceita (sessão #16, 2026-05-14).
**Decisão:** Separa `policy/SCHEMA.md` em camada estrutural universal e camada jurisdicional per-cliente, com quatro vocabulários YAML por framework em `policy/vocabularies/<framework>/`; declara `legal_framework` como campo de cabeçalho obrigatório e imutável na sessão; expõe o recurso compartilhado `policy://vocabularies` e torna a jurisdição não opcional nos vereditos.
**Emendas:** 2026-05-22, Decisões 1 e 2: campo `article_source` corrigido para o nome canônico `statutory_reference`.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0005-multi-client-policy-architecture.md>

**ADR-0006 — Language conventions: Portuguese technical docs, English jurisdictional-vocabulary tokens**
**Status:** Aceita (retrospectiva — convenções herdadas das sessões #04–#11 e #16, formalizada na sessão #17, 2026-05-15).
**Decisão:** Documentação técnica não-ADR (specs, `architecture-overview`, DESIGN, REQUIREMENTS, `SCHEMA.md`, learning-log, handoff) é redigida em português; tokens dos vocabulários jurisdicionais (campo `name:` de `operation.yaml`, `lawful_basis.yaml`, `control.yaml`, `out_of_scope.yaml`) são inglês snake_case, com rótulo em português no campo `description:`.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0006-language-conventions.md>

**ADR-0007 — MVP scope: evaluation limited to operation_type collection** †
**Status:** Aceita (sessão #18, 2026-05-16; adiada da sessão #17 após limpeza do PR-23).
**Decisão:** O MVP avalia conformidade apenas para candidatos com `operation_type: collection`; a Política retém cláusulas sobre operações não-collection como membros de primeira classe; `check_applicability` retorna `not_applicable` com razão estruturada atribuindo o veredito ao escopo do MVP para candidatos fora de escopo.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0007-mvp-collection-only-scope.md>

**ADR-0008 — Task decomposition granularity and verification gate** †
**Status:** Aceita (sessão #17, 2026-05-15); emendada in-place na mesma sessão (2026-05-16), antes de qualquer tarefa autorada sob ela.
**Decisão:** Decompõe a implementação em tarefas de 1–3h agrupadas em milestones; vincula a aceitação de capacidade aos RFs/RNFs de `docs/REQUIREMENTS.md` no escopo de milestone; e estabelece gate de verificação em dois escopos — testes automatizados e revisão independente por tarefa, exercício manual por milestone.
**Emendas:** 2026-05-16, Decisões 1–3 refinadas: vínculo de RF movido do escopo de tarefa para o de milestone; gate de verificação dividido em nível de tarefa e nível de milestone.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0008-task-decomposition-and-verification.md>

**ADR-0009 — Domain boundaries: share functions, not types, between distinct domains**
**Status:** Aceita (sessão #22, 2026-05-17).
**Decisão:** O helper compartilhado `_format_law_reference(lei, artigo, paragrafo, inciso, alinea)` recebe cinco parâmetros posicionais em vez de `StatutoryReferenceEntry`; entre domínios distintos compartilha-se a função — compartilhar o tipo exige justificativa semântica explícita.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0009-domain-boundaries-function-vs-type.md>

**ADR-0010 — Semgrep installation strategy** †
**Status:** Aceita (sessão #26, 2026-05-20).
**Decisão:** Instalar Semgrep via `uv tool install semgrep==1.163.0` como ferramenta isolada de escopo de usuário; pin de versão documentado no README e replicado no CI; sem integração com Semgrep cloud; descoberta do binário via PATH inalterada.
**Emendas:** 2026-06-04, in-place: normalização do `rule_id` no mapper (último segmento pontuado de `check_id`) e obrigação de reavaliar a normalização a cada bump de versão do Semgrep.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0010-semgrep-installation-strategy.md>

**ADR-0011 — Windows-stdio handle inheritance: characterization and error-class separation in the git wrappers**
**Status:** Aceita — emendada em 2026-07-02: D1 (hardening `stdin=subprocess.DEVNULL`) implementado no PR #59 (squash `25d8c52`) e validado no portão da Milestone B; D2 (separação de classes de erro) ratificado como design, com implementação diferida. Fecha o achado XDOC-15 (Apêndice F).
**Decisão:** Caracteriza a hipótese do hang Windows-stdio (herança de handles; `stdin=subprocess.DEVNULL` como prática defensiva geral) e adota, nos wrappers git, exceções customizadas (`GitOperationTimeout`, `GitBinaryUnavailable`) capturadas em `scan_diff`, que emite os errorCodes `GIT_OPERATION_TIMEOUT` (retryable) e `GIT_BINARY_UNAVAILABLE`.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0011-windows-stdio-handle.md>

**ADR-0012 — Two-axis MCP tool governance in subagent configuration (capability vs availability)**
**Status:** Aceita (retrospectiva — D1–D4 tomadas na sessão #48, 2026-05-29, e verificadas empiricamente; D5 herdada da revisão documental do mesmo período).
**Decisão:** Governar o ferramental MCP dos subagentes em dois eixos ortogonais — capacidade via `mcp_servers` e disponibilidade via campo `tools` —, listando explicitamente `ReadMcpResourceTool`/`ListMcpResourcesTool` nos subagentes que leem recursos, e impondo regras load-bearing na camada engine/hook, não em prosa.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0012-subagent-tool-governance.md>

**ADR-0013 — Coordinator error taxonomy and termination contract**
**Status:** Aceita — ratificada pelo autor em 2026-07-02 (rascunho montado em 2026-06-07 como montagem mecânica de decisões já materializadas em código; Decision 5 ratificada como princípio geral; os dois companion edits permanecem follow-ups em aberto).
**Decisão:** Formaliza a taxonomia de exceções do coordenador em dois eixos ortogonais (família `SubagentToolError` vs. exceções SDK/contrato, todas com campo `stage`); terminação como união discriminada `CoordinatorReport | CoordinatorError` com `coverage_gap`; retry decidido pelo campo `is_retryable`; e postura fail-loud sem sucesso silencioso.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0013-coordinator-error-taxonomy-and-termination.md>

**ADR-0014 — MCP connection lifecycle and resilience in the coordinator driver** †
**Status:** Aceita (gate de verificação D1 PASS; merge do PR-A #95, `df78441`, 2026-06-01; sessão #52).
**Decisão:** Detector, Classifier e Matcher migram do `query()` one-shot para o `ClaudeSDKClient` streaming com espera de prontidão via `get_mcp_status()`; erros retryable de `scan_diff` são repetidos na mesma sessão via `reconnect_mcp_server()` conforme `isRetryable`; falha de prontidão/conexão mapeia para `CoordinatorStreamFailure`.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0014-mcp-connection-lifecycle-and-resilience.md>

**ADR-0015 — Control vocabulary: `lawful_basis_required` and the sensitivity gate**
**Status:** Aceita — ratificada pelo autor em 2026-07-02, como redigida (rascunho na branch `eval/test-cases-exploratory`, 2026-06-01); a Decision 3 mantém o token fora de todo vocabulário carregado até a mudança do engine — *engine change* e migração da POL-008 seguem trabalho futuro.
**Decisão:** Propõe introduzir `lawful_basis_required` como terceiro token do vocabulário `control`, com gate de sensibilidade derivado de `special_category`; a adição do token é pareada com mudança obrigatória no engine (`_verdict_for_control`); até o engine mudar, o token fica fora de todo vocabulário carregado.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0015-control-vocabulary-lawful-basis-required.md>

**ADR-0016 — Reporter single-emission guard counts successful emissions, not attempts**
**Status:** Aceita (autorada 2026-06-02; ratificada pelo autor em 2026-06-03, com smoke de confirmação).
**Decisão:** O guard de emissão única do Reporter conta e aborta emissões bem-sucedidas, não tentativas, usando o sink `99-report.json` como sinal de sucesso: segunda emissão com arquivo presente gera `MultipleReportEmissions`; ausente, permite o retry de validação; rede de segurança pós-loop levanta `ReportNotEmitted` se nenhum Report foi commitado.
**Íntegra:** <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/adr/0016-reporter-guard-counts-successful-emissions.md>
