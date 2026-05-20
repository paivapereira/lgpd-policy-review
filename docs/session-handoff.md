## Diff aplicável pós-merge PR #47 (sessão #25 close)

### Bloco 1: Corrigir seção "Pendências cross-sessão (organizado por horizonte de resolução)"

**Substituir** o bloco escrito no commit 7 da PR #47 que dizia "Em curso em sessão #26" — toda a housekeeping aconteceu na própria #25, esse texto ficou desatualizado no momento em que foi escrito.

**Substituir:**

```markdown
**Concluído em sessão #25:**
- Gate milestone-level Milestone A via MCP Inspector CLI mode. Todas as 5 RFs ancoradas empiricamente. Evidence pack em `docs/milestoneA.md`.

**Em curso em sessão #26 (PR `chore/housekeeping-post-t04`):**
- Consolidação de 8 débitos (4 pré-existentes do handoff §Companion edits cross-doc + 4 emergentes do gate #25) em PR única com 7 commits internos. Inclui gate report novo e este sync.

**Resolver em sessão #27 (Chat dedicada):**
- Decomposição formal de Milestone B. Pré-requisito: decisão Semgrep-on-Windows (Docker, pip native, remote worker, CI-only) precede — afeta forma das tasks de Milestone B.
- Atualização de `docs/learning-log.md` para sessão #25 (closure de milestone) + consolidação de defense candidates cumulativos pós-Milestone A.
```

**Por:**

```markdown
**Concluído em sessão #25:**
- Gate milestone-level Milestone A via MCP Inspector CLI mode. Todas as 5 RFs ancoradas empiricamente. Evidence pack em `docs/milestoneA.md`.
- PR #47 `chore/housekeeping-post-t04` mergeada — 7 commits internos, pytest 53/53 verde em cada, 8 débitos consolidados (4 pré-existentes do handoff §Companion edits cross-doc + 4 emergentes do gate). §Companion edits cross-doc agora vazia. Smoke test pós-merge confirmou fix #8 em runtime (POL-002 catalog rendering: `"LGPD Art. 12, §2º"` — cardinal no 12, ordinal preservado no §2).
- Entry sessão #25 adicionada ao `docs/learning-log.md` (closure cumulativa de Milestone A).

**Resolver em sessão #26 (Chat dedicada) — ordem A→B recomendada:**

A. **Migração de defense candidates cumulativos para `.claude/rules/` e/ou ADRs breves.** 18 candidates totais acumulados (11 de #19-#24 + 7 de #25). Sessão metodológica retrospectiva ~1h Chat + ~30min Code aplicando em PRs mecânicas.

B. **Decomposição formal de Milestone B em Chat dedicada.** Pré-requisito procedural: **decisão Semgrep-on-Windows precede** (Docker, pip native, remote worker, CI-only) — afeta forma das tasks de Milestone B. ~1-1.5h Chat se Semgrep decision já tomada; +30min se precisar decidir antes.

Não-bloqueio: A pode rodar antes de B sem custo; B requer Semgrep decision precedendo.

**Resolver pós-Milestone B aberto:**

- Decomposição formal de Milestones C e D em sessões Chat dedicadas sequenciais.
```

### Bloco 2: Atualizar entry de status global de Milestone A

**Localizar** a entry de Milestone A status global e **substituir**:

```markdown
- **Gate milestone-level Milestone A** — **fechada** (#25, manual exercise via MCP Inspector CLI mode contra RFs 004-parcial / 005 / 007-parcial / 008-parcial / 009; evidence pack em `docs/milestoneA.md`).
```

**Por:**

```markdown
- **Gate milestone-level Milestone A** — **fechada** (#25, manual exercise via MCP Inspector CLI mode contra RFs 004-parcial / 005 / 007-parcial / 008-parcial / 009; evidence pack em `docs/milestoneA.md`).
- **Housekeeping cross-doc pós-T04** — **fechada** (#25, PR #47, 7 commits internos squash-preservados, 8 débitos consolidados, smoke test runtime validado).
- **Milestone A** — **encerrada em todos os níveis** (task-level T01-T04 + milestone-level + housekeeping cross-doc).
```

### Bloco 3: Atualizar narrativa histórica do bloco "Oito débitos consolidados"

**Substituir:**

```markdown
**Oito débitos consolidados em PR `chore/housekeeping-post-t04`** (sessão #26, em curso): 4 pré-existentes ... + 4 emergentes do gate #25 ...
```

**Por:**

```markdown
**Oito débitos consolidados em PR #47 `chore/housekeeping-post-t04`** (sessão #25, mergeada): 4 pré-existentes (sync handoff A/B split, sync canonical §3.1/§4.3, rename `_format_first_stat_ref` → `_format_stat_ref`, sync canonical `article_sources_summary` shape) + 4 emergentes do gate #25 (explicit resource names, structuredContent casing, matching scope clarification, conditional ordinal rendering + canonical/compact examples sync).
```

### Bloco 4: Atualizar defense candidates list

**Localizar** o item adicionado no commit 7 da PR #47:

```markdown
- (sessão #25-26) **Multi-instance review escala via complementaridade de trajetória de leitura** — refinamento adicional do pattern já catalogado em #23-#24. Empirizado em 5 instâncias sobre o prompt da PR #26 ao longo de 3 iterações (v1→v2→v3→v4): ...
```

**Substituir o tag de sessão de "#25-26" para "#25" apenas:**

```markdown
- (sessão #25) **Multi-instance review escala via complementaridade de trajetória de leitura** — refinamento adicional do pattern já catalogado em #23-#24. Empirizado em 5 instâncias sobre o prompt da PR #47 ao longo de 3 iterações (v1→v2→v3→v4): cada instância nova detectou subconjunto disjunto de 10 achados não-triviais totais; cobertura conjunta dominou cobertura individual de qualquer uma. Trajetórias materializadas: review-T04 (contexto vivido do código), review-clean (rigor procedural), review-2-models (auditoria semântica de `models.py`), review-2-canonical (auditoria de canonical examples), review-3-compact (auditoria de paridade canonical↔compact). Lição operacional: direcionar reviewers para fatiamentos diferentes do mesmo artefato escala mais que rodar N instâncias indiferenciadas.
```

**Adicionar** dois defense candidates novos não-capturados no commit 7 (emergiram nas notas de execução do Code + smoke test pós-PR):

```markdown
- (sessão #25) **PowerShell 5.1 + UTF-8 puro para commit messages.** `Out-File -Encoding utf8` injeta BOM em PS 5.1 nativo. Pattern correto: `[System.IO.File]::WriteAllText($path, $body, [System.Text.UTF8Encoding]::new($false))`. Materialização para `.claude/rules/windows-tooling.md` ou similar em sessão metodológica futura.
- (sessão #25) **Atomicidade de débito atravessa paridade de specs.** Operacionalização do ADR-0003: quando débito afeta documentação em arquivos com paridade prescrita (canonical↔compact), sync deve ocorrer no mesmo commit que a impl. Sair sem o sync introduz drift novo na própria PR que existia para fechar drift. Empirizado no commit 2 da PR #47 (canonical §4.1-§4.3 + compact §5.2-§5.3 syncados atomicamente com fix `_format_law_reference`).
- (sessão #25) **session-handoff.md como diff-log meta-document — pattern consolidado.** Inaugurado #24, replicado #25 sem fricção. Diff blocks aplicáveis em code-blocks markdown preservam blame-traceability cross-sessão. Materialização para `.claude/rules/session-handoff-format.md` ou ADR breve em sessão metodológica futura.
```

## Diff aplicável pós-Chat #26 (encerramento)

### Bloco 1: Atualizar item B de "Resolver em sessão #26" com pré-requisito procedural resolvido

**Locate:**

```markdown
B. **Decomposição formal de Milestone B em Chat dedicada.** Pré-requisito procedural: **decisão Semgrep-on-Windows precede** (Docker, pip native, remote worker, CI-only) — afeta forma das tasks de Milestone B. ~1-1.5h Chat se Semgrep decision já tomada; +30min se precisar decidir antes.
```

**Substitute by:**

```markdown
B. **Decomposição formal de Milestone B em Chat dedicada.** Pré-requisito procedural satisfeito em sessão #26: decisão Semgrep-on-Windows fechada via ADR-0010 (`semgrep==1.163.0` via `uv tool install`, validado por smoke test em ambiente corporativo Windows). Tema B atacável sem fricção em sessão Chat futura; ~1-1.5h Chat.
```

### Bloco 2: Registrar fechamento de Tema A (migração defense candidates → `.claude/rules/`)

**Add** logo após o último bullet da lista "**Concluído em sessão #25:**" (dentro do Bloco 1 da seção "Diff aplicável pós-merge PR #47") como uma nova sub-lista:

```markdown
**Concluído em sessão #26:**
- Tema A — migração de defense candidates cumulativos (#19-#25) para `.claude/rules/`. PR `feat/rules/method-consolidation` mergeada (7 commits, 7 rules em `.claude/rules/`). DD-6 (`/memory` verifica carregamento das 7 rules) satisfeita na própria sessão #26 antes do fechamento.
```

### Bloco 3: Registrar fechamento de Tema B (decisão Semgrep-on-Windows) e destravamento de Milestone B authoring

**Add** como segundo item da lista "**Concluído em sessão #26:**" introduzida no Bloco 2:

```markdown
- Tema B (procedural) — decisão Semgrep-on-Windows fechada via ADR-0010 (`semgrep==1.163.0` via `uv tool install`). Smoke test em ambiente corporativo Windows confirmou: 290 rules sobre 9 files, 0 findings, exit clean. Pré-requisito procedural de decomposição formal de Milestone B agora satisfeito; sessão Chat dedicada futura pode atacar Milestone B authoring sem fricção.
```