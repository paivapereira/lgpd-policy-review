
```markdown
# Session handoff

**Última sessão fechada:** #14 (2026-05-12)
**Próxima sessão:** #15 — Multi-client architecture rewrite (Fase 1 — docs)
**Branch ativa atual:** `feat/policy-reader-skeleton` (3 commits da Fase A da #14, sem PR — adiado pra após Fase 2)
**Branch nova a abrir para #15:** `arch/multi-client-policy-rewrite` (ramificar de `main`)

## Estado atual

Decisão arquitetural da #15 (Chat, antes da abertura da sessão de Code): adoção completa da arquitetura multi-cliente declarada na proposta-tcc2. Política versionada (Camada 1) é personalizada por cliente, com vocabulários jurisdicionais como dados em `policy/vocabularies/<framework>/`. Camadas 2 (sistema multi-agente) e 3 (CI/CD) são genéricas, lendo a configuração da Camada 1 em runtime. LGPD é instância exemplar do MVP, não framework default codificado.

Esta sessão NÃO toca em código de implementação. Trabalho exclusivamente em docs e arquitetura. Implementação fica para Fase 2 (sessão #16 ou posterior).

## Pendências cross-sessão herdadas da #14

- [adiar para Fase 2 — não bloqueia esta sessão] ADR-0004 (uv + FastMCP 3.x).
- [resolver nesta sessão — Commit 2] ADR-0005 reformulado para arquitetura multi-cliente completa (não a versão de mitigação parcial originalmente planejada).
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

Sequência estrita; cada commit depende do anterior. Após Commit 5, closure (Commits learning-log + handoff), push, abrir PR.

### Comando inicial

```powershell
git checkout main
git pull
git checkout -b arch/multi-client-policy-rewrite
```

### Commit 1 — architecture-overview.md

**Goal.** Reescrever para refletir arquitetura multi-cliente. Camada 1 personalizada por cliente; Camadas 2 e 3 genéricas.

**Source material a ler antes.** `docs/architecture-overview.md` atual, `docs/proposta-tcc2.md` §6 (Arquitetura proposta), histórico de chat #15 (esta conversa) se necessário.

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
- Nenhuma menção a "LGPD" como invariante sistêmico (todas viram exemplo ou referência a "framework declarado pela Política").
- Camada 1 documentada como sendo per-cliente em §4.1.
- Resource `policy://vocabularies` mencionado em §4.2 e §5.4.
- Mensagem do commit em Conventional Commits, escopo `docs(architecture)`.

**Commit message sugerida.**
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

**Source material.** `docs/adr/0001-*.md`, `docs/adr/0002-*.md`, `docs/adr/0003-*.md` (este último se já existir) para estilo. Histórico do chat #14 e #15 para substância.

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

**Mudanças no SCHEMA.md:**
- Adicionar §1.x ou nota de cabeçalho explicando layering (estrutural vs jurisdicional).
- §3 (header global): adicionar `legal_framework` como campo top-level obrigatório.
- §7 (vocabulários fechados): adicionar coluna Natureza (`estrutural` | `jurisdicional`). Marcar quais são quais.
- §7 nota arquitetural: explicitar que vocabulários `jurisdicional` vivem em `policy/vocabularies/<framework>/*.yaml`, não em SCHEMA.md.
- §9 (apêndices com enums): manter como referência humana mas adicionar nota "Conteúdo canônico vive em `policy/vocabularies/LGPD/*.yaml`. Este apêndice é cópia legível humana, não fonte programática."
- Adicionar §10 (ou similar): "Layout multi-cliente" descrevendo a estrutura `policy/vocabularies/<framework>/`.

**Arquivos novos a criar:**
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

**Goal.** Aplicar os 9 patches da spec-revision discutidos no chat #15, mais um novo: resource `policy://vocabularies`.

**Source material.** Versão atual do `docs/specs/policy-reader/canonical.md` e `compact.md`. Os 9 patches detalhados estão no chat #15 (mensagem do dia 2026-05-14, com anchors old_str/new_str declarativos). Code lê esse chat em sua memória de sessão; se não tiver acesso, pausa e pede ao usuário.

**Patches a aplicar.**
1. §1 — função do servidor: nota de framework declarado em header.
2. §2.1 — três eixos de identidade (`policy_schema_version`, `policy_version`, `legal_framework`).
3. §2.1 — parágrafo sobre multi-framework escopo arquitetural (single per instância).
4. §2.2 — subseção sobre framework-awareness.
5. §3.2 — `policy://schema-version` retorna quatro campos (adiciona `legal_framework`).
6. §3.2 — handshake protocol amplifica para incluir validação de framework.
7. §3.3 (novo) — resource `policy://vocabularies`. URI estática, retorna objeto com `{operation, lawful_basis, control, out_of_scope}` carregados de `policy/vocabularies/<framework>/*.yaml`. Idempotente. Read-only. Consumido por Classifier (validação de estrutura de output) e Matcher (validação de input de `check_applicability`).
8. §4.2 — `find_clauses_by_law_article`: nota de independência de framework.
9. §4.3 — `check_applicability`: vocabulários jurisdicionais lidos de `policy/vocabularies/<framework>/`, não de SCHEMA.md. Parágrafo sobre framework-awareness.
10. §6.4 — provenance temporal: trinque `(policy_schema_version, policy_version, legal_framework)` em retornos de `check_applicability`.
11. §7.1 — adicionar não-objetivo: multi-Política ou multi-framework por instância.
12. §8 — checklist de aceitação ganha checkboxes sobre `policy://vocabularies`, sobre trinque de provenance, sobre vocabulários lidos de dados.

**Compact derivado.** Após canonical estar fechado, regenerar/atualizar `compact.md` aplicando taxonomia A-G como nos Commits 6-7 da sessão #11. Manter escalation pointers onde fazem sentido (não inflar — princípio "pointers só onde prosa local insuficiente" do learning-log).

**Acceptance criteria.**
- Canonical contém os 12 patches listados.
- Compact derivado tem paridade canonical↔compact conforme PR template de `.github/PULL_REQUEST_TEMPLATE.md`.
- §8 (checklist) atualizado.
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

### Closure — Commits 6 e 7

**Commit 6 — learning-log.**

Atualizar `docs/learning-log.md` com entry da sessão #15 seguindo formato das sessões anteriores: conceitos da prova exercitados, decisões substantivas, artefatos produzidos, próximo passo.

Conceitos da prova exercitados a citar:
- D2 — Resource vs Tool (caso-livro com `policy://vocabularies` compartilhado).
- D2 — Tool authorization: Classifier ganha resource sem ganhar tools (princípio "only what they need").
- D5 — Provenance/citations: trinque (schema_version, content_version, legal_framework).
- D1 — Task decomposition: docs revision em 5 commits sequenciais por artefato.
- D3 — Project-level vs client-level configuration: policy/ vira parametrização per-cliente.

**Commit message.**
```
docs(log): close session #15 — Fase 1 (multi-client architecture rewrite) complete
```

**Commit 7 — session-handoff.**

Reescrever este handoff. Estado novo:
- Última sessão fechada: #15.
- Branch ativa: `arch/multi-client-policy-rewrite` com 7 commits, aguardando PR.
- Próxima sessão: #16 — Fase 2 (implementação).
- Decisão da Fase 2 (one-shot vs tasks): adiar para abertura da #16 com calibração via `get_clause` (alinhado com recomendação do chat #15 e #14).

### Push e PR

```powershell
git push -u origin arch/multi-client-policy-rewrite
gh pr create --base main --head arch/multi-client-policy-rewrite `
  --title "docs: multi-client architecture rewrite (Fase 1)" `
  --body "Closes architectural gap between proposta-tcc2 §6 and inherited implementation. See ADR-0005. Fase 2 (implementation) in next branch."
```

PR review e merge depois — sessão #15 fechada com PR aberto, não com PR mergeado, caso queira revisitar antes de irrevogável.

## Plano de ação Fase 2 — Code (próxima sessão, #16)

**Estado de partida.** PR da Fase 1 mergeado em `main`. Branch `feat/policy-reader-skeleton` (da #14) rebased ou descartada — provavelmente descartada, porque `policy_loader.py` proposto na #14 era LGPD-acoplado e a Fase 1 supera essa abordagem. Decisão pendente: rebasar vs recomeçar implementação.

**Calibração proposta.** Implementar `loader real + get_clause + testes` em modo one-shot (Code lendo `policy-reader/compact.md` + `policy/SCHEMA.md` + `policy/vocabularies/LGPD/` + `policy/policy.yaml`). Avaliar resultado contra §8 do canonical. Se ≥80% conforme: confiança calibrada para one-shot `find_clauses_by_law_article`, `check_applicability`, `policy://vocabularies`. Se <80%: decompor em tasks granulares para as três tools restantes.

Custo estimado se one-shot funcionar: 1-2 sessões para todo policy-reader. Se tasks: 3-4 sessões.

`semgrep-runner` implementação fica para sessão posterior (#17 ou #18), aproveitando lessons learned do policy-reader.

## Pendências para sessão #17+

- ADR-0004 (uv + FastMCP 3.x).
- CVE 2.x check.
- mime_type micro-débito em resources.
- Sweep `_drafts/` na promoção do draft `spec-authoring-principles.md`.
- Decisão sobre rule set per-cliente do semgrep-runner (quando primeiro cliente não-LGPD materializar).
- ADR-0003 retrospectivo (reframe consumed/reference + §8.<final> lifecycle).
```