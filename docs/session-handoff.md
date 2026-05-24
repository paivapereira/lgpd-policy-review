# Session Handoff #33 → #34

**De:** Sessão #33 (T07 prompt prep + Code implementation + merge)
**Para:** Sessão #34
**Data:** 2026-05-23
**Estado:** Milestone B implementation completa; gate milestone-level pendente

---

## 1. Estado factual do repo

- **Branch atual:** `main`
- **Tests:** 132 passing, 0 failed, 0 skipped (83 baseline + 49 T07)
- **mypy strict:** Success em 16 src/ files
- **ruff:** clean
- **Último PR mergeado:** `feat/semgrep-runner-T07` (2 commits split code-vs-docs)
- **Rule set produção:** `mcp_servers/semgrep_runner/rules/` contém 6 regras BR (`br_cpf.yaml`, `br_cnpj.yaml`, `br_cnh.yaml`, `br_nis_pis.yaml`, `br_titulo_eleitor.yaml`, `br_cns_saude.yaml`); `_placeholder.yaml` removido
- **Conftest do componente:** estendido com fixtures `br_rules_dir` + `br_pack_repo` (paralelo ao pattern POL pack)

## 2. Tasks completas em Milestone B

- T05 (rule loader + bootstrap + placeholder) — mergeada
- T06 (scan_diff implementation + framework integration) — mergeada
- Housekeeping #57 — mergeada
- **T07 (six BR recognizers + placeholder removal)** — mergeada nesta sessão

**Milestone B implementation está COMPLETA.** Falta apenas o gate milestone-level (auditoria de critérios + ratificação contra proposta-tcc2.md §B).

## 3. Próximo halt — três caminhos candidatos para sessão #34

### (A) Gate milestone-level Milestone B
- Auditoria de completude contra proposta-tcc2.md §B + critérios milestone-level declarados em tasks.md
- Validação de RF-001, RF-002, RF-008 (cobertura BR), RNF aplicáveis ao componente
- Decisão formal: Milestone B fechado, prosseguir para C; ou pendências de C-blocker descobertas → housekeeping antes
- **Recomendado próximo** se quiser fechar B formalmente antes de qualquer outra atividade

### (B) Pre-Milestone-C housekeeping
- CLAUDE.md §Status flags stale: declara "64 passing", real é 132
- Eventual sync cirúrgico de docs (canonical, compact) refletindo as DDs T07 ratificadas (DD-T07-3a 1-pattern, NEW DD-T07-AS3 subset assertion, DD-T07-16 metadata schema) se canonical for material para Classifier/Matcher em Milestone C
- Verificação se cross-references entre `recognizers_pack_br/README.md` (sync feito em T07 §3.F) e outros docs ficaram coerentes pós-merge
- ADR draft eventual sobre subset vs strict assertion style se virar pattern recorrente

### (C) Authoring direto de tasks.md §Milestone C
- Sessão dedicada per ADR-0008 §1 (autoria de milestones futuros após gate do anterior — risco de drift se feita pré-gate)
- Estrutura preliminar em tasks.md §"Milestones C, D — autoria deferida" já lista decomposição tentativa (5 AgentDefinitions + `.mcp.json` + Coordinator + Reporter custom tool)
- **Não recomendado direto** — ADR-0008 prescreve gate antes; respeitar metodologia

### Inclinação para escolha
**(A) → (B) → (C)**, nessa ordem. Gate primeiro fecha Milestone B com auditabilidade; housekeeping pre-C limpa débitos catalogados sem alargar escopo; authoring de C com framework limpo.

Se (A) revelar pendências C-blocker, vira (A) → (B) parcial → re-(A) → (C).

## 4. DDs em aberto que afetam Milestone C

Antecipando: design de Milestone C terá decisões substantivas sobre:

- **AgentDefinition shape canonical** para os 5 subagentes (Triager, Detector, Classifier, Matcher, Reporter) + Coordinator. Web search obrigatório para sintaxe atualizada do `claude-agent-sdk` (cutoff Jan/2026; SDK move rápido).
- **`.mcp.json` shape** + per-subagent `mcp_servers` subset (DD canonical já antecipada em §5.7 matriz de architecture-overview.md).
- **`emit_report` custom tool** schema (output do sistema).
- **Coordinator dispatch mechanism**: `Task` tool em `allowedTools` do Coord + system prompt orientativo (não procedural).
- **Scratchpad files** para handoff entre subagentes (Domínio 5 prova).

Não precisam ser decididas no handoff. Apenas catalogadas para sessão #34 dedicada a authoring.

## 5. Convenções importantes para sessões futuras

### Hierarquia de canonicalidade dos docs
1. **tasks.md** = canonical authoritative scratchpad. Em divergência com qualquer outro doc, tasks.md vence.
2. Handoff + learning-log = audit trail. Útil mas não normativo.
3. ADRs + canonical specs + compact = canonical normativo para componentes implementados (semgrep-runner, policy-reader).

**Lição cara da sessão #33**: handoff dizia "T07 = Detector"; tasks.md prescrevia rule pack. Eu segui o handoff por 7 turnos antes de cruzar com tasks.md. Verifique escopo contra tasks.md ANTES de iniciar pre-flight.

### Multi-instance review canônico — framing diversification
- Para próximas prompts complexas (Milestone C terá vários), **instrua reviewers com framings distintos**: uma instância "contexto da task anterior", outra "clean session verify-everything-against-source".
- Diversidade > count.
- Layer-1 (docs) → refinements; layer-2 (código) → blockers; layer-3 (Code empírico via pre-flight) → compositional behavior errors.

### Pre-flight do Code deve incluir "test as deployed"
- v4 prescreveu 4 sub-experimentos validando primitivas Semgrep DSL em isolation; Code descobriu compositional behavior diferente quando 4 patterns viviam juntos numa `pattern-either`.
- Sub-fase "test composite as deployed" deveria estar em todo pre-flight de tasks que materializam composites.

### Estimate Code dispersa — não corrija expectativa
- T07 estimado em 4-6h (v4) → 2.5-3.5h (GATE 1) → 1h real. Superestimação ~3-6×.
- Padrão observado: detection semantics herdando framework pronto é Code-cheap; framework integration é Code-expensive.
- Para Milestone C tasks: framework integration de AgentDefinition + MCP routing provavelmente Code-expensive (T06-pattern); per-subagent prompt + tool restriction tunables provavelmente Code-cheap (T07-pattern).

### Convenções imutáveis
- 2-commit split code-vs-docs no PR
- Commit messages PT-BR; HEREDOC body ASCII-only (per `.claude/rules/windows-tooling.md`)
- Test naming `test_as<N>_*` (sem underscore extra); anchors `test_anchor_*`
- Branch naming `feat/<component>-T<NN>`
- ADR-0008 window: 1-3h por task; estouros forçam re-deliberação
- Subset assertion para tests que exercem contrato (`.claude/rules/test-strategy.md`); strict para tests que validam invariante

## 6. Pendências catalogadas (não bloqueantes)

| # | Item | Severidade | Locus sugerido |
|---|------|-----------|----------------|
| 1 | CLAUDE.md §Status flags stale ("64 passing" → "132 passing") | baixa | Pre-Milestone-C housekeeping (sessão #34 opção B) |
| 2 | Drift handoff/learning-log: "T07 = Detector" vs tasks.md rule pack | catalogado, não-corrigível retroativamente | Lição metodológica em §5 acima |
| 3 | Verificação se tasks.md §"Milestone C — autoria deferida" precisa ratificação antes de authoring formal | baixa | Início de sessão #34 (A) ou (C) |
| 4 | ADR draft eventual sobre subset vs strict assertion style se Milestone C reusar pattern | baixa | Eventual, não bloqueante |

## 7. Comandos canônicos para abrir sessão #34

```bash
# Baseline
git status
git log --oneline -10
uv run pytest -q
# Esperado: 132 passing

# Estado dos componentes Milestone B
ls mcp_servers/semgrep_runner/rules/
# Esperado: 6 br_*.yaml

ls mcp_servers/policy_reader/clauses/  # ou path equivalente
# Esperado: POL pack mergeado em Milestone A

# Sanity de docs
head -20 docs/tasks.md
head -30 docs/learning-log.md
# Confirmar que entry #33 está no topo
```

## 8. Métrica metodológica acumulada (para defense do TCC)

- **Tasks completas com gate ratificado**: 7 (Milestone A: T01-T04; Milestone B: T05, T06, T07).
- **Total sessões Chat**: ~33.
- **Tempo Chat:Code ratio cumulativo**: ~50h Chat / ~12h Code ≈ 4:1. Reflexivo da metodologia prep-heavy + deliberate Code.
- **Rounds prompt iteration médio por task**: T06 = 5; T07 = 4. Padrão estabilizando em 3-5 rounds com framework herdado.
- **Catches detectados por verification layer cumulativo**:
  - Layer-1 (docs): ~60% dos catches, todos refinement-level
  - Layer-2 (código de teste): ~30% dos catches, ~50% destes são blockers
  - Layer-3 (Code empírico): ~10% dos catches, 100% destes são compositional issues invisíveis pra layers 1-2

---

**Sessão #34 abre com:** decidir entre (A)/(B)/(C). Inclinação: (A).