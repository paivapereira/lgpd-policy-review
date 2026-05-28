# Session Handoff — pós sessão #43

## Estado do repo (main)

**Specs de subagent mergeadas:**
- `docs/specs/subagents/coordinator.md` v3
- `docs/specs/subagents/reporter.md` v0.3.0 — **migration pendente p/ 0.4.0 (MC-F)**
- `docs/specs/subagents/triager.md` v0.1.0 — MERGED sessão #43

**Ainda não autoradas:** detector.md, classifier.md, matcher.md.

**Template descartado.** Decisão da sessão #43: não destilar `_template-subagent.md`. Razão: as próximas specs terão as duas anteriores no contexto + review cross-doc, que já estabelecem padrão e coerência. Template seria terceira fonte de verdade com custo de sincronização e risco de virar gabarito (pressionar specs a caber no molde em vez de servir o concern). O valor cognitivo da "destilação" já foi colhido nos defense candidates #5 e #6.

**agent-contracts.md adiado para pós-cinco-specs.** Útil como índice de navegação de sistema fechado (leitor: Claude, contra lost-in-the-middle), mas só ganha valor quando os cinco agentes estão estáveis e a produção é mecânica. Durante autoria, coerência cross-doc vem do processo (specs no contexto + verificação verbatim + citação de locus canônico inline nas §10), não de documento-âncora — que recriaria lost-in-the-middle em escala menor. Não produzir agora.

## Próximas sessões (ordem)

### 1. (Code) PR de housekeeping — pré próxima spec. NÃO paralelizar com a spec.

Agrupar num PR único, mergear ANTES de abrir a próxima spec (evita drift de versão em cross-refs):

- **Provisão MC-F** — Reporter 0.3.0 → 0.4.0 + module migration. **Bloqueia qualquer spec/task que cite módulos do Reporter.** Escopo (5 edits + sync):
  1. reporter.md §1.5: `src/coordinator/{models,constants,system_prompts,tools}.py` → `src/subagents/reporter/{...}.py` + nota §10 changelog.
  2. reporter.md §5.4: remover forward-ref; substituir por texto sobre `TriagerSkip.skip_reason` → `triager_skip_reason` mapping (preserva top-level shape per §2.3).
  3. reporter.md §3.1: `"scope": {...}` → `"scope": TriagerInput`.
  4. reporter.md §4.3 inputSchema: row `scope` dict opaco → `TriagerInput (Pydantic)`.
  5. reporter.md §8.4: remover bullet "Estruturação Pydantic de scope".
  6. Catalogar MC-F em `docs/tasks.md` §Provisões.
- **coordinator.md §3.1**: adicionar `output_format=TriagerDecision.model_json_schema()` + `max_turns=20` ao invocation do Triager (verbo "adicionar", não "confirmar").
- **coordinator.md §5**: nota sobre tolerar tipos de message não-padrão (RateLimitEvent) no loop; ref coordinator §11 AC2.
- **arch-overview §3 mermaid**: `T -->|skip| END` → `T -->|skip| R[Reporter]` (Provisão MC-B; já catalogada coordinator §10 + tasks.md).
- **scripts/smoke_tests/sdk_output_format_lockdown/README.md SF-2**: corrigir "não observado antes" (falso; coordinator §11 AC2 documenta RateLimitEvent desde Gate 1).

### 2. (Chat fresco) Próxima spec de subagent — Classifier ou Detector

- Carregar reporter.md **0.4.0** (pós-MC-F) + triager.md 0.1.0 como anexos no primeiro turno (comparação estrutural quer ambos visíveis desde o início).
- **Classifier resolve DD-T05** (changed_paths). A decisão da Classifier determina o companion edit pendente abaixo.
- Detector é alternativa se preferir; mas Classifier desbloqueia DD-T05 mais cedo.

### 3. Companion edit ACOPLADO à próxima spec (não é housekeeping independente)

- **arch-overview §5.2** (input "Diff do PR, lista de paths alterados" → "PR scope 4 campos; paths via Glob"): aplicar **junto com a decisão de DD-T05** na Classifier spec. Se Classifier decidir pré-computar `changed_paths` no coordinator, este edit é revertido/ajustado. NÃO aplicar antes da spec.

### 4. (Depois) Demais specs + agent-contracts no final

- Detector, Matcher (as que faltarem).
- agent-contracts.md como índice de sistema fechado, mecânico, derivado das 5 specs estáveis.
- Início de T11+ implementação (só depois de MC-F mergeado).

## DDs abertas que próximas specs herdam

- **DD-T05** (changed_paths): Classifier spec decide. Acopla companion edit arch §5.2.
- **DD-T14** (reasoning field): T11+ catálogo MC-D, com/sem campo.
- **DD-T16** (oneOf/discriminator + SDK output_format): primeira implementação T11+ que tentar discriminated union testa empiricamente; fallback shape unificado.

## Side findings p/ smoke-test futuro

- **dontAsk em Python** (~20min, 2 variantes): antes de ADR-0012 retroativo sobre defesa em camadas do coordinator §6. Doc diz "TypeScript only", funciona em Python (Gate 1 + sdk_output_format_lockdown PASS). Discriminar: doc stale / no-op silencioso / undocumented funcional.
- **DD-T11 Haiku gate:** smoke-test análogo a sdk_output_format_lockdown com `model="claude-haiku-4-5-20251001"`. Pós-validação funcional do sistema.

## Provisões pré-existentes ainda pendentes

- MC-B (mermaid patch) — incluída no PR de housekeeping acima.
- MC-E (pin `claude-agent-sdk>=0.2.0,<1.0` em pyproject.toml + ADR-0001 amendment) — independente; quando conveniente.

## Stack / ambiente (invariante)

Python 3.12.7 (pyenv-win), Node 24, `claude-agent-sdk` 0.2.87 pinned, `pydantic` 2.13.4. Windows 11 corp, PowerShell 5.1, sem admin local. Pattern A'' (system_prompt direto, sem AgentDefinition). Quíntupla lockdown: permission_mode=dontAsk, setting_sources=[], strict_mcp_config=True, allowed_tools whitelist, mcp_servers dict. Modelo: Opus 4.7 adaptive thinking para tudo em desenvolvimento.