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