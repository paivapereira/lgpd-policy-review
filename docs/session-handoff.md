# Handoff #32 → #33

## Estado atual (pós-housekeeping pre-T07 mergeado)

PR #57 mergeada: `chore/housekeeping-pre-t07` — cleanup de drifts cross-doc.
8 commits internos pre-squash colapsados via squash-merge no GitHub UI. Hash
do squash a registrar pós-pull `<TBD>`. 83 tests passing preservados; ruff
clean; mypy Success em 16 source files de `src/`.

PR #56 (T06 scan_diff completo) mergeada anteriormente na mesma sessão #32.
Milestone B substantialmente avançado em T05+T06; T07 (Detector subagent) é
a próxima task topológica de Milestone B — primeiro consumer real de
`scan_diff` via FastMCP Client.

Sessão #32 encerrada formalmente neste handoff. Sessão #33 reservada para
prep T07.

## DDs/decisões load-bearing que persistem como contexto pós-housekeeping

1. **Convenção bare ratificada para rule_id Semgrep.** `br-cpf`, `br-cnpj`,
   `br-cnh`, `br-nis-pis`, `br-titulo-eleitor`, `br-cns-saude` — uma regra
   por identificador, cobrindo N padrões via `pattern-either`. Canonical
   examples agora coerentes com convenção tasks.md T07 e com filenames
   `br_cpf.yaml` em `mcp_servers/semgrep_runner/rules/`. T07 implementação
   deve usar este vocabulário.

2. **Severity convention para regras BR ratificada.** `warning` para
   identificadores comuns (CPF, CNPJ, CNH, NIS, título eleitor); `error`
   apenas para casos com razão semântica forte (e.g., CNS-saúde sob LGPD
   Art. 11 sensíveis). Coerente com Chat review T07 prescrito em tasks.md.
   Decisão antecipada em #32 housekeeping; T07 implementa.

3. **mypy + ruff agora em `[dependency-groups.dev]`.** Pin oficial
   (`mypy>=1.18`, `ruff>=0.13`) via `uv.lock`. Workaround `uv run --with
   mypy mypy` aposentado. Comandos canônicos a partir de #33:
   - `uv run mypy src/` para checagem do código de aplicação.
   - `uv run ruff check .` para lint.
   - `uv run pytest -q` para tests.

4. **`[tool.mypy] exclude`** apontando para
   `tests/mcp_servers/semgrep_runner/fixtures/recognizers_pack_br/`.
   Fixtures Semgrep são deliberadamente type-incorrect pelo padrão stdlib
   (structured logging via kwargs); excluídos do strict checking. Novos
   fixtures adicionados em T07 ou em Provisão futura herdam o exclude
   automaticamente — sem necessidade de `# type: ignore` per-snippet.

5. **`.claude/rules/windows-tooling.md` extendido com ASCII commit
   convention** (5 seções: Principle/Justification/How to apply/Scope +
   header). Rule auto-carregada pelo Code em sessões futuras quando os
   path-scoped triggers casam. Code não precisa receber lembrete no
   prompt — convenção materializada.

6. **Gate de regressão exclusion-aware com 5 exclusões cumulativas.**
   Pattern operacional consolidado para grep-based regression checks
   em PRs cross-doc futuras:
   ```bash
   git grep -nE "<token>" -- . \
     ':!docs/learning-log.md' \
     ':!docs/session-handoff.md' \
     ':!docs/adr/' \
     ':!docs/DESIGN.md' \
     ':!src/mcp_servers/policy_reader/models.py'
   ```
   Exclusões justificadas como audit trail intencional (learning-log,
   handoff, ADRs) ou audit trail cross-doc legítimo preservado em sites
   não-tocados pela PR (DESIGN.md ADR-0005 rename note; models.py docstring
   nova). Padrão a aplicar em futuras housekeepings cross-doc.

7. **`policy/clauses/POL-000.yaml` + Provisão B (fixture pack BR)
   mergeados.** Disponíveis como fixtures base para T07:
   - POL pack para tests de Detector que precisem invocar policy-reader
     em integração.
   - Recognizer pack BR para tests de scan_diff invocado pelo Detector
     subagent.

8. **Estado de débitos pós-PR #57.**
   - **Zero débitos mecânicos abertos** (todos os 7 catalogados nos
     handoffs #31+#32 fechados).
   - **D-5 deferido**: sweep cross-doc das regras imutáveis ADR-0001
     Decision 4 ↔ CLAUDE.md §"Immutable domain rules". Bloqueante para
     Milestone C, não para T07. Sessão Chat dedicada ~1.5h antes do início
     de C.
   - **JS/TypeScript coverage**: pós-Milestone B gate milestone-level,
     janela 15/06-30/06 caso haja capacidade. Detalhes em
     `tasks.md` §"Pós-Milestone B aberto".
   - **Promoções pendentes para `.claude/rules/`**: catálogo-de-débitos-
     é-código (cristalizada em #32 Edit M-2); gates de regressão
     exclusion-aware com dois vetores (cristalizada em #32 P-7);
     documento de implementação externo como evolução do plan-mode pattern
     (cristalizada em #32). Sessão metodológica retrospectiva dedicada
     quando o número de candidates acumulados justificar.

## Conceitos de prova exercitados na sessão #32 housekeeping

Detalhamento em `learning-log.md` entry "2026-05-23 — sessão #32
(continuação)". Resumo:

- **D1** (Agentic Architecture, 27%): plan mode externalizado como
  artefato pre-sancionado; halt-and-escalate em Code review sobre
  artefato-prompt.
- **D3** (Claude Code Configuration, 20%): `.claude/rules/windows-tooling.md`
  extendido; `[tool.mypy]` config materializada.
- **D4** (Prompt Engineering, 20%): validation-retry loop manual em 4
  rounds com severity decay monotônico; verification-before-inference
  recursiva.
- **D5** (Context Management, 15%): audit trail exclusions em gates de
  regressão (5 exclusões cumulativas); error propagation estruturada
  cross-system Chat ↔ Code; provenance via cascading decision.

## Pré-flight para sessão Chat de prep T07

Verificação direta empírica antes de redigir o prompt T07. Pattern
consolidado em sessões #28+: pre-flight verifica fatos do código real, não
infere a partir de docs ou memória.

**1. Estado real de `src/mcp_servers/semgrep_runner/`.**

```bash
# Listar tools expostas pelo server
grep -n "@mcp.tool" src/mcp_servers/semgrep_runner/server.py
# Confirmar: apenas scan_diff, ou há outras?

# Confirmar export do componente
cat src/mcp_servers/semgrep_runner/__init__.py
# Confirmar pattern de export

# Estado do bootstrap
grep -n "_bootstrap\|_STATE" src/mcp_servers/semgrep_runner/server.py
# Pattern análogo ao policy_reader/server.py?
```

**2. Pattern de import do FastMCP Client no projeto.**

```bash
# Buscar usos existentes de Client (T07 vai ser o primeiro consumer real)
git grep -nE "from fastmcp import Client|from fastmcp\.client" .
# Esperado: 0 ou poucos matches (Client é novo no projeto pós-T07)

# Confirmar versão FastMCP pinned em uv.lock
grep -A1 '"fastmcp"' uv.lock | head -5
# Esperado: 3.2.4 ou similar (per ADR-0001 amendment 2026-05-21)

# Buscar documentação FastMCP 3.x sobre Client se necessário
# Web search: "fastmcp Client tutorial site:gofastmcp.com"
```

**3. AgentDefinition pattern — primeira AgentDefinition do projeto.**

```bash
# Confirmar que ainda não há AgentDefinition no projeto
git grep -nE "AgentDefinition|agent_definition" -- . ':!docs/' ':!*.md'
# Esperado: 0 matches em código (Milestone C introduz)

# Pre-leitura obrigatória de architecture-overview
sed -n '/^## 5\./,/^## 6\./p' docs/architecture-overview.md
# Especialmente §5.2 Detector + §5.7 matriz de restrições por subagent

# Pre-leitura .mcp.json se existir
cat .mcp.json 2>/dev/null || echo "(no .mcp.json yet)"
# Confirmar exposição de semgrep-runner para Detector via mcp_servers field
```

**4. Provisão B (recognizer pack BR) — disponibilidade.**

```bash
# Confirmar pack mergeado
ls tests/mcp_servers/semgrep_runner/fixtures/recognizers_pack_br/

# Confirmar estrutura conforme T07 §Files previstos
ls tests/mcp_servers/semgrep_runner/fixtures/recognizers_pack_br/*.py | wc -l
# Esperado: ~9 arquivos (6 positivos + 3 negativos + README)

# Confirmar exclusão mypy ativa
uv run mypy tests/mcp_servers/semgrep_runner/fixtures/recognizers_pack_br/
# Esperado: Success: 0 source files
```

**5. Decisão substantiva pré-prompt.**

Antes de redigir o prompt T07, deliberar:

- **Escopo da T07**: apenas Detector (single AgentDefinition) ou também
  Coordinator stub para orquestrar invocação? Boundary clarification.
- **AgentDefinition em qual diretório**: `src/agents/` novo? ou inline
  em `src/coordinator.py`? Pattern do projeto pós-T07.
- **Tests fixture root assembly** análogo ao policy_reader pattern, ou
  algo diferente para subagent? Pre-leitura `tests/mcp_servers/policy_reader/
  test_bootstrap.py` para pattern operacional.
- **Carregamento de regras Semgrep `br_*.yaml`**: T07 cria os arquivos
  YAML em `mcp_servers/semgrep_runner/rules/` (substitui placeholder de
  T05)? Ou T07 é apenas o Detector subagent + tests, com criação de
  `br_*.yaml` em task separada T08? Boundary crítica — afeta
  ordem topológica de Milestone B e estimativa de custo.

**6. Custo estimado T07.**

Prep Chat ~2-3h (multi-round se justificado, espelha T06) + Code ~3-4h.
Pattern: pre-flight ambicioso + plan-mode + GATE 1 + Fase 2 com gates
intermediários conforme prescrito em
`.claude/rules/spec-driven-workflow.md`.

## Sugestão de início para sessão #33

Começar com pre-flight verification (passos 1-4 acima) sob commit limpo de
`main` pós-housekeeping. Resultado do pre-flight é input para deliberação
do passo 5 (boundary clarification). Boundary fechada → redação prompt T07
v1.

**Não pular pre-flight.** Padrão consolidado em #28+: anomalias de
pre-flight emergem ao mapear empiricamente, não ao verificar isoladamente
contra docs. Cada sessão Code pre-flight ambicioso pagou dividendos em
implementation surprises absorvidas sem rework arquitetural (T04 wire-shape,
T06 exits 4/5 unreachable, T06 shallow signal em JSON, T06 snippet
"requires login").

## Próximo halt esperado em #33

Pre-flight T07 verification report ou plan mode T07 (GATE 1 deliberation
com DDs). Sessão #32 oficialmente encerrada neste handoff.

## Artefatos chave da sessão #32

- **PR #56** (mergeado): T06 scan_diff completo. Detalhes em learning-log
  entry T06.
- **PR #57** (mergeado): housekeeping pre-T07 (8 commits internos).
  Hash squash `<TBD>`.
- **`prompt-t06-v5.1.md`**: prompt final de T06 implementação. Appendix
  de 25 catches. Referência para metodologia de prompt-redação T07.
- **`housekeeping-pre-t07-IMPL.md` FINAL** (767 linhas): documento de
  implementação consolidado. Audit trail descartável pós-merge; lições
  absorvidas no learning-log entry #32 (continuação).
- **Learning log entries**: T06 (anexar separadamente) + #32
  (continuação housekeeping, este handoff).

## Status da prova (Claude Certified Architect — Foundations)

Sessão #32 (T06 + housekeeping) exercitou conceitos dos 5 domínios:

- **D1 27%**: GATE 1 + Fase 3 faseada em T06; plan mode externalizado +
  halt-and-escalate em housekeeping.
- **D2 18%**: scan_diff completo em T06 (subprocess Semgrep + 6 errorCodes
  + Option B wire format).
- **D3 20%**: `.claude/rules/windows-tooling.md` extendido; `[tool.mypy]`
  config materializada; mypy/ruff em dev-deps.
- **D4 20%**: validation-retry em 5 rounds (T06 prompt) + 4 rounds
  (housekeeping artefato). Severity decay monotônico empiricamente
  observado em ambos.
- **D5 15%**: long context exercitado (housekeeping consumiu múltiplos
  arquivos cross-component); audit trail exclusions com 5 exclusões
  cumulativas; error propagation estruturada Chat ↔ Code.

Trajetória de sessão #32 (T06 + housekeeping) é defense candidate forte
para Capítulo de Método — multi-round validation-retry sobre dois tipos
de artefato distintos (código de aplicação T06; documento de plano
housekeeping) com mesmo pattern operacional, mesma convergência empírica,
mesma capacidade de absorver implementation surprises via halt-and-
escalate. Pattern generaliza além do tipo de output.