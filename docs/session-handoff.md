# Session handoff

**Última sessão fechada:** #17 (Chat) — 2026-05-15
**Próxima sessão:** #18 (Chat) — Matcher como evaluator iterativo + preparação ADR-0007
**Branch ativa atual:** `arch/multi-client-policy-rewrite` (8 commits incluindo este handoff, aguardando push e PR)
**Branch nova a abrir para #16.5:** `docs/requirements-and-tasks` (ramificar de main após PR da Fase 1 mergeado)

## Estado atual

Arquitetura multi-cliente cristalizada em ADR-0005 e materializada em 7 commits documentais na branch `arch/multi-client-policy-rewrite`. Camada 1 (Política) é per-cliente, com vocabulários jurisdicionais externalizados em `policy/vocabularies/<framework>/`; Camadas 2 (MCP servers) e 3 (CI/CD) são framework-agnósticas. LGPD é instância exemplar do MVP, não framework default codificado. Implementação real (Fase 2) é greenfield, ancorada em `docs/specs/policy-reader/compact.md` e `docs/specs/semgrep-runner/compact.md`. `docs/DESIGN.md` serve como entrypoint acionável de leitura para a Fase 2.

Push da branch + abertura do PR em main são ação manual pós-Commit 7 (`git push -u origin arch/multi-client-policy-rewrite` + `gh pr create --base main --head arch/multi-client-policy-rewrite ...`). Após merge do PR, a branch `arch/multi-client-policy-rewrite` torna-se histórica; main absorve os 8 commits via squash. A branch da Fase 1.5 (`docs/requirements-and-tasks`) ramifica de main pós-merge.

## Onde encontrar detalhes do que a Fase 1 cristalizou

- **Decisões arquiteturais formais:** `docs/adr/0005-multi-client-policy-architecture.md` (8 Decisions).
- **Componentes, camadas, matriz tools × subagentes:** `docs/architecture-overview.md`.
- **Forma da Política, layering estrutural vs jurisdicional:** `policy/SCHEMA.md`.
- **Processo de cristalização e calibrações metodológicas da sessão #16:** `docs/learning-log.md` (entry 2026-05-14).
- **Entrypoint operacional para implementação:** `docs/DESIGN.md` (roteiro de leitura por componente).

## Pendências cross-sessão (organizado por horizonte de resolução)

**Resolver na Fase 1.5 (#16.5 — Chat):**

- Conteúdo de `docs/requirements.md` (RFs/RNFs com critério Dado/Quando/Então).
- Conteúdo de `docs/tasks.md` (15-25 tasks granulares, formato Spec-Kit-inspirado).

**Resolver na Fase 2 (#17+ — Code, antes do primeiro código rodar):**

- ADR-0004 (uv + FastMCP 3.x) — número reservado desde sessão #14; inclui CVE 2.x check.
- ADR-0007 (escopo de operações MVP v0.1.0 — only `collection` evaluated against clauses) — número reservado em PR #23; redação diferida para sessão Chat dedicada. Rationale primária a registrar: sistema é ferramenta acessória a mapa de tagueamento de coleta de dados, não a política inteira de proteção de dados da empresa. Argumentos secundários (foundational data-flow position, signal density, compliance-domain breadth) podem complementar mas não substituir a motivação primária. Citado por REQUIREMENTS.md RF-004 e por docs/adr/0006 (referência cruzada).
- ADR-0008 (task decomposition granularity and verification gate) — materializado nesta sessão como governance da forma do `docs/tasks.md`. Não-bloqueante para implementação se `tasks.md` for redigido sob suas decisões.
- `mime_type` micro-débito em resources (declarar `application/json` no loader real).

**Adiar para sessão #18+:**

- Semântica de `last_revision` em `policy/policy.yaml` — formal vs informativo, atualização manual vs automática.
- Semântica de `schema_version` no header dos YAMLs de vocabulário — coerência com `policy_schema_version` do header global, regras de bump.
- Validação cruzada per-cliente (vocabulary × Semgrep metadata) — só relevante quando ADR de per-client rule set materializar.
- ADR retroativo formalizando convenção "português para docs técnicos não-ADR" (specs, `architecture-overview`, `DESIGN.md`, `SCHEMA.md`).
- Promoção do draft `_drafts/spec-authoring-principles.md` para `docs/` — sweep + atualização de cross-doc links.
- Decisão sobre rule set per-cliente do `semgrep-runner` (quando primeiro cliente não-LGPD materializar).

## Defaults arquiteturais consolidados (pós-Fase 1)

Estado **realizado** (não plano em progresso). Referência canônica de cada item em ADR-0005.

- Camada 1 (Política) é per-cliente; substituível por cliente sem alteração de código (ADR-0005 Decision 1).
- `legal_framework` é campo top-level único do header da Política, imutável durante sessão do server (ADR-0005 Decision 2).
- `accepted_law_identifiers` é lista de leis citáveis intra-jurisdição (e.g., `[LGPD, Marco_Civil]` numa Política brasileira).
- POL-000 é vocabulário universal (semântico, não estatutário); vive em `policy/clauses/`, estrutura governada por `policy/SCHEMA.md` §5 (ADR-0005 Decision 3).
- Quatro vocabulários jurisdicionais (`operation`, `lawful_basis`, `control`, `out_of_scope`) vivem em `policy/vocabularies/<framework>/*.yaml`.
- `policy-reader` expõe três resources (`policy://catalog`, `policy://schema-version`, `policy://vocabularies`) e três tools (`get_clause`, `find_clauses_by_law_article`, `check_applicability`).
- `policy://vocabularies` é compartilhado Matcher+Classifier (read-only resource); tools do `policy-reader` continuam exclusivas Matcher (ADR-0005 Decision 4).
- `check_applicability` retorna trinque de provenance `(policy_schema_version, policy_version, legal_framework)` em todo sucesso (ADR-0005 Decision 5).
- Sucessão de cláusulas é intra-Política (intra-`legal_framework`), via `successors` no bloco `tombstone` (ADR-0005 Decision 6).
- Mecanismo interno de reasoning de `check_applicability` é deferido para Fase 2 (ADR-0005 Decision 7).
- `semgrep-runner` rule set é bundled no projeto no MVP; per-cliente é deferimento explícito (ADR-0005 Decision 8).

## Plano de ação Fase 1.5 — Requirements e Tasks (sessão de Chat)

Sessão de Chat (não Code) dedicada a redigir dois artefatos que fecham o gap SDD restante: requirements verificáveis derivados da proposta-tcc2, e tasks decompostas para Fase 2. Branch separada `docs/requirements-and-tasks` ramificando de main após PR da Fase 1 mergeado. Custo estimado: 10-16h, uma ou duas sessões.

**Justificativa.** O trio `requirements / design / tasks` é a forma de SDD informal que sobrevive sem framework (Spec Kit ou similar). Design já existe distribuído pós-Fase 1 (`DESIGN.md` como entrypoint). Faltam requirements (contrato de aceitação global verificável) e tasks (decomposição executável que substitui a decisão one-shot-vs-decomposto da Fase 2 original).

### Commit 1.5.1 — docs/requirements.md

**Goal.** Extrair da proposta-tcc2 e da documentação arquitetural um conjunto enxuto de requisitos funcionais (RF) e não-funcionais (RNF), cada um com critério de aceitação observável.

**Source material.** `docs/proposta-tcc2.md` inteira, `docs/architecture-overview.md` pós-Fase 1, ADRs 0001-0005.

**Estrutura.**

- RF-001 a RF-NNN — requisitos funcionais. Cada um: descrição em 1-3 frases + critério de aceitação no formato "Dado X, quando Y, então Z".
- RNF-001 a RNF-NNN — requisitos não-funcionais. Cobrir: stack tech (ADR-0001), latência alvo, observabilidade mínima, reprodutibilidade, framework-agnosticismo (ADR-0005).
- Cobertura mínima esperada: detecção de tratamento, classificação de contexto, avaliação de conformidade, geração de Report, provenance temporal e jurisdicional, troca de framework sem alteração de código.

**Critério geral para aceitação como bem-formado.** Cada RF e RNF deve ser verificável por terceiro sem julgamento subjetivo. Critério ambíguo é defeito, refazer.

**Acceptance criteria.**

- Arquivo `docs/requirements.md` criado.
- Todo RF tem critério no formato "Dado / quando / então" com componentes observáveis.
- Todo RNF tem métrica ou referência arquitetural (e.g., RNF-stack referencia ADR-0001).
- Pelo menos um RF cobre framework-agnosticismo com cenário de troca LGPD → GDPR.

**Commit message.**

```
docs: add requirements.md with verifiable functional and non-functional requirements

Distilled from proposta-tcc2 and architecture-overview into numbered
RFs/RNFs with observable acceptance criteria (Given/When/Then format).
Includes explicit framework-agnostic requirement covering LGPD→GDPR
substitution scenario.

Refs ADR-0005, DESIGN.md validation global.
```

### Commit 1.5.2 — docs/tasks.md

**Goal.** Decompor implementação do `policy-reader` e `semgrep-runner` em tasks granulares executáveis pelo Code uma a uma, com dependências, file paths e critério de aceitação por task.

**Source material.** SPECs pós-Fase 1 (`compact.md` de cada server), `architecture-overview.md`, `DESIGN.md`, `requirements.md` recém-redigido.

**Formato (inspirado em Spec Kit, sem dependência dele).**

```
## T001 — Loader real da Política
**Depends on:** —
**Files:** src/mcp_servers/policy_reader/loader.py (novo)
**Parallel:** []
**Goal:** Implementar carregamento de policy/policy.yaml + policy/clauses/*.yaml + policy/vocabularies/<framework>/*.yaml em startup. Validação contra SCHEMA.md (estrutural) e contra vocabulários (jurisdicional).
**Acceptance:** Server inicia com Política LGPD válida; aborta startup com erro descritivo se schema inválido; carrega quatro vocabulários jurisdicionais como objetos Pydantic.

## T002 — Resource policy://schema-version
**Depends on:** T001
**Files:** src/mcp_servers/policy_reader/server.py (modificar)
**Parallel:** [T003]
**Goal:** [...]
**Acceptance:** [...]
```

**Granularidade alvo.** Cada task cabe em sessão de implementação de 30-60 minutos. Mais curta que isso é over-decomposed; mais longa que isso é under-decomposed.

**Decomposição mínima esperada.**

- 1 task — loader real
- 4 tasks — uma por surface (`policy://catalog`, `policy://schema-version`, `policy://vocabularies`, mais checklist cruzado)
- 3 tasks — uma por tool (`get_clause`, `find_clauses_by_law_article`, `check_applicability`)
- 2-3 tasks — testes unitários e integração end-to-end
- `semgrep-runner`: 1 task loader, 2 tasks tool + testes

Total estimado: 15-25 tasks. Numeração T001-T0NN, prefixadas `PR-` para `policy-reader` e `SR-` para `semgrep-runner` se preferir clareza.

**Acceptance criteria.**

- Arquivo `docs/tasks.md` ou diretório `docs/tasks/` criado.
- Toda task tem campos depends/files/parallel/goal/acceptance preenchidos.
- Toda acceptance é observável (resultado de teste, comportamento verificável manualmente).
- Ordem topológica respeitada (T001 → T002 não cria ciclo de dependência).

**Commit message.**

```
docs: decompose policy-reader and semgrep-runner implementation into tasks

15-25 numbered tasks with dependencies, file paths, and observable
acceptance per task. Granularity calibrated for 30-60min implementation
sessions. Replaces one-shot vs decomposed decision deferred from #14.

Refs DESIGN.md roteiro de leitura, requirements.md.
```

### Push e PR

```powershell
git push -u origin docs/requirements-and-tasks
gh pr create --base main --head docs/requirements-and-tasks `
  --title "docs: requirements and tasks for SDD-driven implementation" `
  --body "Closes SDD gap: verifiable requirements + decomposed tasks. Fase 2 (implementation) consumes tasks.md as input."
```

## Plano de ação Fase 2 — Code (sessão #17 ou posterior)

**Input para Code.** `docs/tasks.md` é o source-of-truth da Fase 2 sob governança de ADR-0008 (granularidade 8-12 tasks médias, acceptance amarrada a REQUIREMENTS.md RFs/RNFs, gate tripartite por task). Code consome task a task em ordem topológica, validando os três mecanismos do gate antes de marcar como done.

Decisão one-shot vs tasks granulares — deferida da #14 — fica resolvida automaticamente: tasks já são granulares por design da Fase 1.5. Cada task é one-shot dentro de si.

**Estado de partida.** PR da Fase 1.5 mergeado em main. Branch `feat/policy-reader-skeleton` já mergeada em main (sessão #15 closure, squash `6b8d4ea`). Code começa nova branch `feat/policy-reader-implementation` ramificando de main.

**Custo estimado.** Com tasks decompostas: 1 sessão por bloco de 3-5 tasks paralelizáveis ou em sequência curta. Total para `policy-reader`: 2-3 sessões. Total para `semgrep-runner`: 1-2 sessões. End-to-end + integração CI/CD: 1 sessão. Estimativa total da Fase 2: 4-6 sessões.

## Hashes da Fase 1 (audit trail interno)

Sobrevive a squash-merge — após merge do PR, hashes individuais somem do main, mas ficam registrados aqui:

- `2612f99` — docs(architecture): rewrite overview for multi-client policy support
- `c08bbd4` — docs(adr): add ADR-0005 — multi-client architecture for policy support
- `a54f99a` — docs(schema): layer SCHEMA.md into structural + jurisdictional, externalize LGPD vocabularies
- `8583499` — docs(spec): rewrite policy-reader for multi-framework, add policy://vocabularies resource
- `823b03b` — docs(spec): note semgrep-runner rule-set scope under multi-client architecture
- `d466f37` — docs: add DESIGN.md as actionable entrypoint for SDD workflow
- `05883c8` — docs(log): close session #16 — Fase 1 (multi-client architecture rewrite) complete

(Hash do próprio handoff omitido — só conhecido pós-`git commit`. O 8º commit da branch é o presente arquivo.)
