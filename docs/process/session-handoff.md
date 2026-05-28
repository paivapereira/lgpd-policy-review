# Session Handoff — pós MC-F (sessão #44 / "#43+")

## Estado do repo (main)

**MC-F mergeada** — PR #73, squash `c5e7751`. Drift reporter↔coordinator morto (G1/G5 verdes).

**Specs de subagente:**
- `coordinator.md` v3 — refs de módulo do Reporter migradas para `src/subagents/reporter/`; §3.1 com `output_format` (forma envelopada) + `max_turns=20`; §3.1 nota de tolerância a tipos não-padrão no loop; §10 three-beats Beat 2 = applied (**Beat 3 = verified ainda pendente**).
- `reporter.md` **v0.4.0** — MERGED. Locus em `src/subagents/reporter/`; `scope: TriagerInput` no contrato (§2.2/§2.3/§3.1/§4.3); forward-refs §5.4/§8.4 fechadas; few-shots §5.1 com shape canônico; §10.6 changelog 0.4.0 + nota técnica do `output_format` envelopado.
- `triager.md` v0.1.0 — inalterada.

**arch-overview** — §3 mermaid: `skip → Reporter` (MC-B aplicada). §5.2 **ainda não tocada** (acoplada a DD-T05; ver abaixo).

**Não autoradas:** `detector.md`, `classifier.md`, `matcher.md`.

## Próxima sessão — Classifier spec

**Inversão deliberada da ordem #37** (era Detector→Classifier; agora Classifier→Detector). Justificativa dupla: (i) Classifier resolve DD-T05 e desbloqueia o companion edit órfão arch §5.2; (ii) a Classifier consome o output da Detector (`[{file, line, rule_id, snippet, surrounding_context}]`), então autorar a consumidora antes da produtora força clareza de contrato. **Registrar como desvio consciente da ordem #37**, não silencioso.

- Carregar `reporter.md` **0.4.0** + `triager.md` 0.1.0 como anexos no primeiro turno (comparação estrutural quer ambos visíveis).
- **DD-T05 é o eixo da sessão**: `changed_paths` pré-computado no coordinator (injetado no scope de cada query) vs redescoberto por cada subagent via `Glob`. É decisão de state-passing entre stages — consequência de proveniência (fonte única vs conjuntos potencialmente divergentes por subagent).

### Companion edit ACOPLADO à Classifier (não housekeeping independente)
- **arch-overview §5.2** — input "Diff do PR, lista de paths alterados" → "PR scope (`pr_number`, `base_ref`, `head_ref`, `repo_url`); paths via `Glob`". Aplicar **junto com a decisão de DD-T05**. Se a Classifier decidir pré-computar `changed_paths` no coordinator, este edit é revertido/ajustado. **NÃO aplicar antes da spec.**

## Pendências catalogadas (não-bloqueantes)

- **Follow-up Triager §10.5 item 1** (`output_format` shape) — catalogado em `tasks.md §Companion edits cross-doc` (Commit 6 de MC-F). A prescrição nua é shorthand; o contrato wire-level é a forma envelopada `{"type": "json_schema", "schema": ...}` (confirmada em `smoke_test.py` 0.2.87, anotada em reporter §10.6). Numa sessão futura que tocar a Triager: marcar item 1 como shorthand com cross-ref — alinhamento de proveniência, não decisão aberta. A próxima spec carrega reporter 0.4.0, então o risco de herdar a forma nua está mitigado pela anotação.
- **Beat 3 (verified) do coordinator §10 three-beats** — review independente Chat do patch do mermaid pós-aplicação. Pendente.

## DDs abertas que próximas specs herdam

- **DD-T05** (`changed_paths`): Classifier decide. Acopla arch §5.2.
- **DD-T14** (`reasoning` field): T11+ catálogo MC-D, com/sem campo.
- **DD-T16** (oneOf/discriminator + SDK `output_format`): primeira impl T11+ que tentar discriminated union testa empiricamente; fallback shape unificado.

## Provisões pré-existentes ainda pendentes

- **MC-E** (pin `claude-agent-sdk>=0.2.0,<1.0` em pyproject.toml + amendment ADR-0001): independente; quando conveniente.
- **MC-C** (ADR-0012 stale → ADR-0011 sync): branch própria.
- **agent-contracts.md**: índice de sistema fechado, só após as 5 specs estáveis.

## Side findings p/ smoke-test futuro

- **dontAsk em Python** (~20min): doc diz "TypeScript only", funciona em Python (Gate 1 + sdk_output_format_lockdown PASS). Discriminar: doc stale / no-op silencioso / undocumented funcional. Antes do ADR-0012 retroativo sobre defesa em camadas do coordinator §6.
- **DD-T11 Haiku gate**: smoke-test análogo a sdk_output_format_lockdown com `model="claude-haiku-4-5-20251001"`. Pós-validação funcional.

## Sequência subsequente (pós-Classifier)

Detector → Matcher → coordinator-flesh-completo → ADR-0012 retroativo Milestone C → decomposição de tasks T11+ → benchmark de PRs sintéticos → gate milestone-level.

## Stack / ambiente (invariante)

Python 3.12.7 (pyenv-win), Node 24, `claude-agent-sdk` 0.2.87 pinned, `pydantic` 2.13.4. Windows 11 corp, PowerShell 5.1, sem admin local. Pattern A'' (system_prompt direto, sem AgentDefinition). Quíntupla lockdown: `permission_mode=dontAsk`, `setting_sources=[]`, `strict_mcp_config=True`, `allowed_tools` whitelist, `mcp_servers` dict. Modelo: Opus 4.7 adaptive thinking para tudo em desenvolvimento. Commit subjects internos ASCII (PS 5.1 + HEREDOC); PR title via UI preserva acentos.