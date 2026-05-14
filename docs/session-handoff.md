# Session handoff

**Última sessão fechada:** #15 (Chat) — 2026-05-14
**Próxima sessão:** #16 (Code) — Fase 1: Multi-client architecture rewrite
**Branch ativa atual:** main (limpa, working tree clean)
**Branch nova a abrir para #16:** `arch/multi-client-policy-rewrite` (ramificar de main)

## Estado atual

Decisão arquitetural da #15 (Chat): adoção completa da arquitetura multi-cliente declarada na proposta-tcc2. Política versionada (Camada 1) é personalizada por cliente, com vocabulários jurisdicionais como dados em `policy/vocabularies/<framework>/`. Camadas 2 (sistema multi-agente) e 3 (CI/CD) são genéricas, lendo configuração da Camada 1 em runtime. LGPD é instância exemplar do MVP, não framework default codificado.

Esta sessão (Code, Fase 1) NÃO toca em código de implementação. Trabalho exclusivamente em docs e arquitetura. Implementação fica para Fase 2 (sessão #17 ou posterior, após Fase 1.5 que adiciona requirements.md e tasks.md).

## Pendências cross-sessão herdadas da #14

- [adiar para Fase 2] ADR-0004 (uv + FastMCP 3.x).
- [resolver nesta sessão — Commit 2] ADR-0005 reformulado para arquitetura multi-cliente completa.
- [adiar para Fase 2] CVE 2.x check.
- [adiar para Fase 2] mime_type micro-débito em resources.
- [adiar para promoção do draft] sweep `_drafts/`.

## Defaults arquiteturais consolidados (decisões #15 Chat)

Os Commits 1-5 abaixo assumem estes defaults. Code aplica sem perguntar. Se algum default produzir incoerência específica no documento, Code pausa e pergunta antes de prosseguir.

- `legal_framework` é campo top-level do header da Política, valor único (não lista). Imutável durante sessão do server.
- `accepted_law_identifiers` permanece como lista (leis citáveis dentro da jurisdição: e.g., `[LGPD, Marco_Civil]` numa Política brasileira).
- POL-000 (vocabulário de categorias de dados pessoais) é semântico universal, não jurisdicional. Mesma estrutura funciona em qualquer framework; conteúdo das categorias é por-cliente mas a noção é universal.
- Diretório de vocabulários jurisdicionais: `policy/vocabularies/<framework>/`.
- Quatro arquivos por framework: `operation.yaml`, `lawful_basis.yaml`, `control.yaml`, `out_of_scope.yaml`.
- `policy/SCHEMA.md` separa explicitamente camada estrutural (universal, vive no projeto) de camada de vocabulários (per-cliente, vive na Política do cliente).
- `policy-reader` ganha resource novo `policy://vocabularies` expondo os quatro vocabulários jurisdicionais. Resource read-only, idempotente.
- Matriz 5.7 do `architecture-overview` atualizada: Classifier ganha acesso a `policy://vocabularies` (resource read-only do policy-reader). Tools do policy-reader continuam exclusivas ao Matcher.
- `check_applicability` retorna `legal_framework` em sucesso, junto com `policy_schema_version` e `policy_version` (trinque de provenance).
- Sucessão de cláusulas é intra-Política (não cross-framework).
- Mecanismo interno de reasoning do `check_applicability` (data-driven puro vs híbrido) NÃO é prescrito pela SPEC nesta sessão — decisão de implementação fica para Fase 2. SPEC declara apenas o contrato observável.
- `semgrep-runner` rule set: decisão de "per-cliente vs do projeto" adiada para Fase 2 via deferimento explícito em §7.1 do canonical. MVP mantém rule set no projeto, com identificadores brasileiros como caso-piloto.

## Plano de ação Fase 1 — Docs

Sequência estrita; cada commit depende do anterior. Após Commit 5.5, closure (Commits 6 e 7 — learning-log + handoff), push, abrir PR.

### Comando inicial

```powershell
git checkout main
git pull
git checkout -b arch/multi-client-policy-rewrite
```

### Commit 1 — architecture-overview.md

**Goal.** Reescrever para refletir arquitetura multi-cliente. Camada 1 personalizada por cliente; Camadas 2 e 3 genéricas.

**Source material a ler antes.** `docs/architecture-overview.md` atual, `docs/proposta-tcc2.md` §6 (Arquitetura proposta).

**Mudanças mínimas (sem reescrita total — patches cirúrgicos):**

- §4.1 (Camada 1 — Política versionada): explicitar que é personalizada por cliente. Substruturar em rationale, clauses, policy.yaml, SCHEMA.md (este último em camada estrutural universal + vocabulários per-cliente em `policy/vocabularies/<framework>/`).
- §4.2 (Camada 2 — MCP servers): policy-reader serve a Política do cliente; ganha resource `policy://vocabularies`; semgrep-runner mantém rule set do projeto no MVP com deferimento.
- §5.4 (Classifier): ganhar acesso read-only a `policy://vocabularies`. Justificar com princípio Resource vs Tool.
- §5.5 (Matcher): inalterado em escopo, mas comportamento agora explicitamente framework-aware via consumo dinâmico de vocabulários.
- §5.6 (Reporter): Report ganha `legal_framework` como campo top-level.
- §5.7 (matriz tools × subagentes): atualizar coluna do Classifier para incluir `policy://vocabularies` (resource, não tool).
- Todas as menções a "LGPD" como assumido viram exemplos ("e.g., LGPD") ou são removidas onde implicarem hardcoding.

**Acceptance criteria.**

- Matriz §5.7 atualizada coerentemente com a mudança do Classifier.
- Nenhuma menção a "LGPD" como invariante sistêmico.
- Camada 1 documentada como sendo per-cliente em §4.1.
- Resource `policy://vocabularies` mencionado em §4.2 e §5.4.
- Mensagem do commit em Conventional Commits, escopo `docs(architecture)`.

**Commit message.**

```
docs(architecture): rewrite overview for multi-client policy support

- Layer 1 explicitly per-client, with structural vs jurisdictional separation in SCHEMA.md
- policy-reader gains policy://vocabularies resource (read-only)
- Classifier gains read access to policy://vocabularies (resource, not tool)
- Report carries legal_framework as top-level provenance field
- Remove all hardcoded assumptions of LGPD as framework default

Refs ADR-0005 (next commit), session #15 chat.
```

### Commit 2 — ADR-0005

**Goal.** Redigir ADR-0005 na versão completa (não a versão parcial planejada na #14).

**Source material.** `docs/adr/0001-*.md`, `docs/adr/0002-*.md`, `docs/adr/0003-*.md` para estilo. Histórico do chat #14 e #15 para substância.

**Estrutura.**

- **Title.** "ADR-0005 — Architecture for multi-client policy support: vocabularies as data, LGPD as instance"
- **Status.** Accepted
- **Context.** Arquitetura declarada em proposta-tcc2 §6 implica multi-cliente. Implementação herdada da #14 (skeleton + mitigações) ainda assumia LGPD em vocabulários jurisdicionais. Esta ADR formaliza a separação estrutural/jurisdicional em escopo completo, antecipando a Fase 2.
- **Decision.** Lista as decisões do bloco "Defaults arquiteturais" acima como decisões formais do ADR. Cada uma com 1-2 frases de justificativa.
- **Consequences positive.** Troca de framework não toca código. Coerência entre proposta-tcc2 e implementação. Princípio Resource vs Tool exercitado em caso-livro. Multi-tenant arquiteturalmente honesto.
- **Consequences negative.** Quatro arquivos de vocabulário por framework. Perda parcial de type safety estática em campos jurisdicionais (mitigado por validação runtime contra dados Layer 1). Classifier ganha visibilidade ao policy-reader — fronteira anterior "só Matcher consulta Política" é relaxada para "só Matcher consulta tools da Política; resources são compartilháveis".
- **Migration path.** Não aplicável (greenfield, ADR concretiza a arquitetura antes da implementação real).
- **Supersedes.** Nada formalmente; complementa ADR-0002 (deferimentos de design pendentes).

**Acceptance criteria.**

- Formato consistente com ADR-0001/0002.
- Todas as decisões do bloco "Defaults arquiteturais" deste handoff aparecem como decisões formais.
- Referências cruzadas a `architecture-overview.md` §4.1, §4.2, §5.7.

**Commit message.**

```
docs(adr): add ADR-0005 — multi-client architecture for policy support

Formalize separation of structural vs jurisdictional layers in SCHEMA.md,
externalize jurisdictional vocabularies to policy/vocabularies/<framework>/,
expose them via policy://vocabularies resource for shared consumption by
Classifier and Matcher. Closes architectural gap between proposta-tcc2 §6
and inherited implementation.

Refs architecture-overview §4.1, §4.2, §5.7.
```

### Commit 3 — SCHEMA.md + policy/vocabularies/LGPD/

**Goal.** Refatorar `policy/SCHEMA.md` em camada estrutural universal + camada de vocabulários jurisdicionais externalizada. Criar `policy/vocabularies/LGPD/` como caso-piloto.

**Source material.** `policy/SCHEMA.md` atual.

**Mudanças no SCHEMA.md.**

- Adicionar §1.x ou nota de cabeçalho explicando layering (estrutural vs jurisdicional).
- §3 (header global): adicionar `legal_framework` como campo top-level obrigatório.
- §7 (vocabulários fechados): adicionar coluna Natureza (`estrutural` | `jurisdicional`). Marcar quais são quais.
- §7 nota arquitetural: explicitar que vocabulários `jurisdicional` vivem em `policy/vocabularies/<framework>/*.yaml`, não em SCHEMA.md.
- §9 (apêndices com enums): manter como referência humana mas adicionar nota "Conteúdo canônico vive em `policy/vocabularies/LGPD/*.yaml`. Este apêndice é cópia legível humana, não fonte programática."
- Adicionar §10 (ou similar): "Layout multi-cliente" descrevendo a estrutura `policy/vocabularies/<framework>/`.

**Arquivos novos a criar.**

- `policy/vocabularies/LGPD/operation.yaml` — enum atual de `operation` (§9.2 do SCHEMA.md).
- `policy/vocabularies/LGPD/lawful_basis.yaml` — enum atual de `lawful_basis` (§9.1).
- `policy/vocabularies/LGPD/control.yaml` — enum atual de `control` (§9.5 — `consent_required`, `anonymization_required`).
- `policy/vocabularies/LGPD/out_of_scope.yaml` — enum atual de `reason` (§9.4).

**Formato dos arquivos.** YAML simples, lista de valores com descrição curta opcional:

```yaml
# policy/vocabularies/LGPD/operation.yaml
schema_version: 0.1.0
framework: LGPD
values:
  - name: collection
    description: Coleta de dados pessoais do titular.
  - name: storage
    description: Armazenamento de dados pessoais.
  # ...
```

**Acceptance criteria.**

- SCHEMA.md compila como Markdown válido.
- §7 tabela tem nova coluna preenchida.
- Quatro arquivos YAML criados em `policy/vocabularies/LGPD/` com conteúdo extraído fielmente de §9 do SCHEMA.md atual.
- `policy/policy.yaml` (header) recebe campo `legal_framework: LGPD` se ainda não tem.

**Commit message.**

```
docs(schema): layer SCHEMA.md into structural + jurisdictional, externalize LGPD vocabularies

- Add legal_framework as top-level field in policy.yaml header
- §7 (vocabularies) marked with Natureza column: estrutural vs jurisdicional
- Create policy/vocabularies/LGPD/ with 4 files (operation, lawful_basis, control, out_of_scope)
- §9 appendix kept as human reference; canonical source moves to YAML files

Refs ADR-0005.
```

### Commit 4 — policy-reader canonical + compact

**Goal.** Aplicar 12 patches ao canonical do policy-reader (9 discutidos em mensagem do chat #15 do dia 2026-05-14 com anchors old_str/new_str declarativos, mais 3 adicionados depois). Compact derivado.

**Source material.** Versão atual de `docs/specs/policy-reader/canonical.md` e `compact.md`. Os patches detalhados estão consolidados abaixo; se Code precisar de contexto adicional, pausar e pedir.

**Patches a aplicar no canonical.**

1. **§1 (Identidade).** Substituir prosa que diz "Política de Proteção de Dados versionada" por versão que inclui "sob o framework jurisdicional declarado em seu header". Ajuste cosmético.

2. **§2.1 (Artefato e schema).** Substituir "dois eixos de versão independentes" por "três eixos de identidade independentes": adicionar `legal_framework` à lista, com descrição. Acrescentar parágrafo sobre "Multi-framework — escopo arquitetural" deixando claro que uma instância serve uma Política sob um framework; cross-framework simultâneo não é suportado.

3. **§2.2 (Comportamento contratual perante estados).** Adicionar subseção "Comportamento contratual perante framework jurisdicional" no fim da §2.2: componente é agnóstico ao valor de `legal_framework`; vocabulários jurisdicionais são lidos de `policy/vocabularies/<framework>/` no startup; mudança de framework requer (a) Política nova/clonada, (b) população de vocabularies, (c) header com `legal_framework: <new>`, (d) restart. Nenhuma alteração de código.

4. **§3.2 (`policy://schema-version`).** Substituir bloco que descreve "três campos" pelo bloco com quatro: adicionar `legal_framework` ao payload (valor único, não lista, imutável durante sessão). Substituir handshake protocol pra incluir validação dupla: schema dentro do range AND framework na lista do consumidor. Adicionar parágrafo "Onde mora a validação de framework": responsabilidade do consumidor (Matcher), não do componente. Simétrico ao tratamento de `compatible_schema_range`.

5. **§3.3 (NOVA seção).** Resource `policy://vocabularies`. URI estática, sem parâmetros. Conteúdo: objeto com `{operation, lawful_basis, control, out_of_scope}` carregados de `policy/vocabularies/<framework>/*.yaml`. Idempotente. Read-only. Consumido por Classifier (validação de estrutura de output) e Matcher (validação de input de `check_applicability`). Justificar com princípio "Resource vs Tool" — vocabulários são catálogo lido por múltiplos agentes; tools são actions de escopo restrito.

6. **§4.2 (`find_clauses_by_law_article`).** Adicionar parágrafo "Independência de framework" no fim da seção: tool é insensível ao valor de `legal_framework`; vocabulário aceito de `lei` é o de `accepted_law_identifiers` do header. Nenhum framework é privilegiado pelo código.

7. **§4.3 (`check_applicability`).** Substituir referência de `operation` em `inputSchema` de "Enum declarado em `policy/SCHEMA.md`" para "Vocabulário declarado em `policy/vocabularies/<framework>/operation.yaml` da Política carregada. Vocabulários jurisdicionais são lidos como dados em startup; não hardcoded no código do componente." Mesma mudança para `lawful_basis` se aparecer. Adicionar parágrafo "Framework-awareness desta tool" no fim da §4.3: reasoning sobre aplicabilidade não codifica regras específicas a framework; rules vivem na Política como combinações `applies_to × control × exceptions`; componente aplica reasoning genérico. Validação dinâmica via `INVALID_DATA_CATEGORY` e `INVALID_OPERATION` reporta `accepted_values` extraídos dos vocabulários da Política carregada.

8. **§6.4 (Provenance temporal).** Substituir lista de campos de provenance em retornos bem-sucedidos: ao invés de `policy_schema_version` + `policy_version`, agora trinque `policy_schema_version` + `policy_version` + `legal_framework`. Substituir frase "provenance temporal" por "provenance temporal e jurisdicional". Adicionar justificativa: em audit trails multi-jurisdição, sem `legal_framework` no veredito o auditor não saberia sob qual lei a decisão foi tomada — campo é não-opcional.

9. **§7.1 (Não-objetivos).** Adicionar item: "Múltiplas Políticas ou múltiplos frameworks em uma única instância do componente. Uma instância serve uma Política sob um framework, imutáveis durante a sessão. Servir LGPD + GDPR simultaneamente exige duas instâncias do componente, distinguidas no Matcher via configuração de `mcp_servers` (uma entrada por instância). Hot-swap de Política ou framework durante a sessão é deferimento explícito — ver ADR-0002."

10. **§8.1 (Checklist Resources).** Adicionar checkbox: "`policy://schema-version` retorna `legal_framework` como quarto campo do payload, valor único declarado pelo header da Política carregada."

11. **§8.1 (Checklist Resources).** Adicionar checkbox sobre novo resource: "`policy://vocabularies` retorna objeto com 4 vocabulários jurisdicionais carregados de `policy/vocabularies/<framework>/*.yaml`. Read-only, idempotente."

12. **§8.6 (Provenance) e §8.7 (Implementação).** §8.6: adicionar checkbox sobre `check_applicability` carregar `legal_framework` além das versões (trinque). §8.7: adicionar dois checkboxes — vocabulários lidos de `policy/vocabularies/<framework>/*.yaml` no startup (não hardcoded); trocar `legal_framework` da Política requer só Política nova + restart (verificável por exercício de clone sob framework alternativo).

**Compact derivado.** Após canonical estar fechado, regenerar `compact.md` aplicando taxonomia A-G como nos Commits 6-7 da sessão #11. Manter escalation pointers onde fazem sentido (não inflar — princípio "pointers só onde prosa local insuficiente" do learning-log). Acrescentar coverage de `policy://vocabularies` no §4 (Resources) do compact.

**Acceptance criteria.**

- Canonical contém os 12 patches listados.
- Compact derivado tem paridade canonical↔compact conforme PR template de `.github/PULL_REQUEST_TEMPLATE.md`.
- §8 (checklist) atualizado com os 4 novos checkboxes.
- Sem menção a "LGPD" como assumido em prose contratual (sempre via referência ao framework do header).

**Commit message.**

```
docs(spec): rewrite policy-reader for multi-framework, add policy://vocabularies resource

- §2.1: three identity axes (schema_version, content_version, legal_framework)
- §3.2: schema-version handshake now includes legal_framework
- §3.3: new resource policy://vocabularies (read-only, consumed by Classifier + Matcher)
- §4.3: check_applicability vocabularies read from policy/vocabularies/<framework>/
- §6.4: provenance temporal expanded to trinque
- §7.1: non-objective — multi-policy/multi-framework per instance
- compact.md derived under canonical+compact dual strategy

Refs ADR-0005, architecture-overview §4.2 §5.4 §5.7.
```

### Commit 5 — semgrep-runner canonical + compact

**Goal.** Ajustes mínimos pra coerência com nova arquitetura. Rule set per-cliente fica como deferimento.

**Mudanças.**

- §2.1 — adicionar parágrafo: "Rule set per-cliente é deferimento explícito (§7.1)."
- §7.1 — novo item de deferimento: "Rule set per-cliente. MVP carrega rule set bundled no projeto. Per-cliente exige diretório `policy/<cliente>/semgrep_rules/` ou similar; decisão de design fica para ADR futuro quando primeiro cliente fora do escopo LGPD-brasileiro materializar."
- §8 — checklist sem mudança substantiva (verificar se há algo a adicionar).

**Compact.** Atualizar §7 com o novo deferimento. Adicionar see-canonical pointer se necessário.

**Acceptance criteria.**

- Deferimento de rule set per-cliente registrado em §7.1.
- Paridade canonical↔compact.

**Commit message.**

```
docs(spec): note semgrep-runner rule-set scope under multi-client architecture

Add explicit deferral of per-client rule set (§7.1). MVP retains bundled
rule set with Brazilian recognizers; per-client extension deferred to
future ADR.

Refs ADR-0005, architecture-overview §4.2.
```

### Commit 5.5 — DESIGN.md

**Goal.** Wrapper acionável de 30-50 linhas que serve como entrypoint para leitura dos docs distribuídos. Não duplica conteúdo; roteiriza acesso. Função análoga a CLAUDE.md (que orienta comportamento do agente) mas escopo de SDD (orienta leitura para implementação).

**Source material a ler antes.** Estado pós-Commit 5 dos seguintes arquivos: `architecture-overview.md`, `policy/SCHEMA.md`, `specs/policy-reader/compact.md`, `specs/semgrep-runner/compact.md`, ADRs 0001-0005.

**Conteúdo do arquivo a criar em `docs/DESIGN.md`.**

```markdown
# DESIGN — sistema de code review LGPD assistido por agentes

## Visão

Sistema de code review automatizado que verifica conformidade de Pull Requests contra uma Política de Proteção de Dados versionada. Arquitetura em três camadas: (1) Política como artefato versionado, personalizável por cliente, com vocabulários jurisdicionais como dados; (2) sistema multi-agente coordinator-subagentes consumindo a Política em runtime; (3) integração CI/CD via GitHub Action.

LGPD é instância exemplar do MVP; arquitetura é framework-agnóstica. Cliente troca de jurisdição (LGPD → GDPR) reescrevendo a Política em `policy/`, sem alteração de código do sistema.

## Roteiro de leitura para implementação

**Antes de qualquer implementação:**
1. `docs/architecture-overview.md` inteiro — três camadas, matriz §5.7 de tools por subagente
2. `policy/SCHEMA.md` — forma das cláusulas, separação estrutural vs jurisdicional

**Quando implementar `policy-reader`:**
- Spec normativa: `docs/specs/policy-reader/compact.md`
- Em ambiguidade contratual ou ordering: `docs/specs/policy-reader/canonical.md`
- Decisões herdadas: ADR-0001 (FastMCP stack), ADR-0002 (MCP conventions), ADR-0005 (multi-cliente)
- Vocabulários carregados em startup: `policy/vocabularies/LGPD/*.yaml`

**Quando implementar `semgrep-runner`:**
- Spec normativa: `docs/specs/semgrep-runner/compact.md`
- Em ambiguidade contratual: `docs/specs/semgrep-runner/canonical.md`
- Decisões herdadas: ADR-0001, ADR-0002
- Rule set bundled: `mcp_servers/semgrep_runner/rules/` (per-cliente é deferimento — ADR-0005)

**Quando implementar subagentes (Triager, Detector, Classifier, Matcher, Reporter):**
- Responsabilidades e tools permitidas: `architecture-overview.md` §5.2-§5.6
- Matriz tools × subagentes: `architecture-overview.md` §5.7
- AgentDefinitions com `mcp_servers` e `allowed-tools`: a redigir em Fase 2

## Decisões arquiteturais críticas

- **ADR-0001** — Stack: FastMCP 2.x, Python 3.12.7, uv
- **ADR-0002** — MCP conventions: hybrid placement, custom URI schemes (`policy://`), três classes de erro
- **ADR-0003** — Spec architecture: dual canonical+compact com escalation pointers
- **ADR-0005** — Multi-cliente: vocabulários jurisdicionais como dados em `policy/vocabularies/<framework>/`, expostos via resource `policy://vocabularies`

## Validação global

Sistema integrado completo: rodar `policy-review` (GitHub Action ou CLI local) sobre PR sintética contendo violação plantada (e.g., persistência de CPF sem anonimização), obter Report JSON com finding correto incluindo `clause_id`, `verdict`, `evidence`, e provenance `(policy_schema_version, policy_version, legal_framework)`.

Teste de generalização: substituir `policy/policy.yaml` e `policy/vocabularies/` por versão GDPR equivalente, rerodar mesma PR, obter Report válido sob framework distinto sem alteração de código.
```

**Acceptance criteria.**

- Arquivo em `docs/DESIGN.md` no formato acima, ajustado se necessário pra refletir estado real pós-Commit 5.
- Todos os pointers para arquivos resolvem (sem broken links).
- Validação global descreve cenário verificável, não aspiracional.

**Commit message.**

```
docs: add DESIGN.md as actionable entrypoint for SDD workflow

Lightweight wrapper (40-line guide) routing implementation reading
across distributed docs (architecture-overview, specs, ADRs, SCHEMA).
No content duplication — pointers only. Equivalent to AGENTS.md
pattern but scoped to SDD instead of agent behavior.

Refs Fase 1.5 (requirements+tasks) and Fase 2 (implementation).
```

### Closure — Commits 6 e 7

**Commit 6 — learning-log.**

Atualizar `docs/learning-log.md` com entry da sessão #16 (Code, Fase 1) seguindo formato das sessões anteriores: conceitos da prova exercitados, decisões substantivas, artefatos produzidos, próximo passo.

Conceitos da prova exercitados a citar:

- D2 — Resource vs Tool (caso-livro com `policy://vocabularies` compartilhado).
- D2 — Tool authorization: Classifier ganha resource sem ganhar tools (princípio "only what they need").
- D5 — Provenance/citations: trinque (schema_version, content_version, legal_framework).
- D1 — Task decomposition: docs revision em 5 commits sequenciais por artefato.
- D3 — Project-level vs client-level configuration: policy/ vira parametrização per-cliente.

**Commit message.**

```
docs(log): close session #16 — Fase 1 (multi-client architecture rewrite) complete
```

**Commit 7 — session-handoff.**

Reescrever este handoff. Estado novo:

- Última sessão fechada: #16 (Code, Fase 1).
- Branch ativa: `arch/multi-client-policy-rewrite` com 7 commits, aguardando PR.
- Próxima sessão: #16.5 (Chat) — Fase 1.5: redigir `docs/requirements.md` e `docs/tasks.md`.

### Push e PR

```powershell
git push -u origin arch/multi-client-policy-rewrite
gh pr create --base main --head arch/multi-client-policy-rewrite `
  --title "docs: multi-client architecture rewrite (Fase 1)" `
  --body "Closes architectural gap between proposta-tcc2 §6 and inherited implementation. See ADR-0005. Fase 1.5 (requirements+tasks) in next branch."
```

PR review e merge depois — sessão #16 fechada com PR aberto, não com PR mergeado, caso queira revisitar antes de irrevogável.

## Plano de ação Fase 1.5 — Requirements e Tasks (sessão de Chat)

Sessão de Chat (não Code) dedicada a redigir dois artefatos que fecham o gap SDD restante: requirements verificáveis derivados da proposta-tcc2, e tasks decompostas para Fase 2. Branch separada `docs/requirements-and-tasks` ramificando de main após PR da Fase 1 mergeado. Custo estimado: 10-16h, uma ou duas sessões.

**Justificativa.** O trio `requirements / design / tasks` é a forma de SDD informal que sobrevive sem framework (Spec Kit ou similar). Design já existe distribuído pós-Fase 1 (DESIGN.md como entrypoint). Faltam requirements (contrato de aceitação global verificável) e tasks (decomposição executável que substitui a decisão one-shot-vs-decomposto da Fase 2 original).

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

**Source material.** SPECs pós-Fase 1 (`compact.md` de cada server), `architecture-overview.md`, DESIGN.md, requirements.md recém-redigido.

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
- 4 tasks — uma por surface (policy://catalog, policy://schema-version, policy://vocabularies, mais checklist cruzado)
- 3 tasks — uma por tool (get_clause, find_clauses_by_law_article, check_applicability)
- 2-3 tasks — testes unitários e integração end-to-end
- semgrep-runner: 1 task loader, 2 tasks tool + testes

Total estimado: 15-25 tasks. Numeração T001-T0NN, prefixadas `PR-` para policy-reader e `SR-` para semgrep-runner se preferir clareza.

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

**Input para Code.** `docs/tasks.md` é o source-of-truth da Fase 2. Code consome task a task em ordem topológica, validando critério de aceitação de cada antes de marcar como done. Prompt da sessão: *"Executar T001 do tasks.md. Validar critério de aceitação antes de fechar. Pausar e perguntar se algo na task estiver ambíguo."*

Decisão one-shot vs tasks granulares — deferida da #14 — fica resolvida automaticamente: tasks já são granulares por design da Fase 1.5. Cada task é one-shot dentro de si.

**Estado de partida.** PR da Fase 1.5 mergeado em main. Branch `feat/policy-reader-skeleton` já mergeada em main (sessão #15 closure). Code começa nova branch `feat/policy-reader-implementation` ramificando de main.

**Custo estimado.** Com tasks decompostas: 1 sessão por bloco de 3-5 tasks paralelizáveis ou em sequência curta. Total para policy-reader: 2-3 sessões. Total para semgrep-runner: 1-2 sessões. End-to-end + integração CI/CD: 1 sessão. Estimativa total da Fase 2: 4-6 sessões.

## Pendências para sessão #18+

- ADR-0004 (uv + FastMCP 3.x).
- CVE 2.x check.
- mime_type micro-débito em resources.
- Sweep `_drafts/` na promoção do draft `spec-authoring-principles.md`.
- Decisão sobre rule set per-cliente do semgrep-runner (quando primeiro cliente não-LGPD materializar).
- ADR-0003 retrospectivo (reframe consumed/reference + §8.<final> lifecycle).