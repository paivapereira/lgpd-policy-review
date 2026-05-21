## Diff aplicável pós-Chat #27 (encerramento)

### Bloco 1: Atualizar item B de "Resolver em sessão #26" para refletir conclusão em #27

**Locate:**

```markdown
B. **Decomposição formal de Milestone B em Chat dedicada.** Pré-requisito procedural satisfeito em sessão #26: decisão Semgrep-on-Windows fechada via ADR-0010 (`semgrep==1.163.0` via `uv tool install`, validado por smoke test em ambiente corporativo Windows). Tema B atacável sem fricção em sessão Chat futura; ~1-1.5h Chat.
```

**Substitute by:**

```markdown
B. **Decomposição formal de Milestone B em Chat dedicada.** **Fechado em sessão #27.** `docs/tasks.md` v1.2 autorado contendo Milestone B com Capacidade entregue + RFs cobertas (RF-001, RF-002) + Provisões A e B pré-implementação + tasks T05/T06/T07 + gate milestone-level placeholder. Estimativa final: ~13-14h totais (~5h pré-implementação + ~6.5-7.5h implementação + ~1h gate). Decisões substantivas: Python only no MVP (JS adiado para janela 15/06-30/06 em §"Pós-Milestone B aberto"); `rules_version` = hash determinístico do diretório `rules/`; T06 unificada não-splitada; canonical-sync-C cirúrgico não re-derivação (per ADR-0003 D1); ADR-0001 Decision 2 amendment in-place reconciliando stack real (FastMCP 3.2.4 / Pydantic 2.13.4 / MCP 1.27.1 / Semgrep substituindo Presidio). Materializado em diff aplicável de 4 blocos para `docs/tasks.md`, com 2 fixes adicionais do Chat review pós-autoria (typo aspas em §Status + sync §Source-of-truth para incluir `docs/specs/semgrep-runner/`). Aplicação via PR mecânica subsequente, ~30-40min Code.
```

### Bloco 2: Registrar artefatos de sessão #27 na lista "Concluído em sessão #26"

**Add** como nova sub-lista logo após os bullets de "Concluído em sessão #26" (introduzidos pelo Bloco 2 do Diff aplicável pós-Chat #26):

```markdown
**Concluído em sessão #27:**
- Autoria formal de Milestone B em `docs/tasks.md` v1.2 — diff aplicável de 4 blocos + 2 fixes pós-Chat-review. Aplicação via PR mecânica `docs/tasks-milestone-b-decomposition` (Code ~30-40min).
- Cinco drifts load-bearing detectados via verificação direta cruzando canonical+compact+ADR-0001+uv.lock — quatro no contract surface canonical/compact do semgrep-runner (errorCodes 4 vs 6, classes validation+system vs business+system, retryability SCAN_TIMEOUT/SEMGREP_EXECUTION_FAILED, timing de BINARY_UNAVAILABLE startup vs per-call, wire format pre-amendment) + um fundacional em ADR-0001 (Presidio menção drifted vs Semgrep real + ausência de pins de stack na decisão). Quatro deles consolidados como commits internos da Provisão A; o ADR-0001 amendment como quarto commit interno da mesma PR.
- Entry de sessão #27 adicionada ao `docs/learning-log.md` com defense candidates emergentes incluindo "sessão de autoria de milestone como gatilho natural para sweep de drift adjacente" e "uv.lock como fonte autoritativa secundária para reconciliar ADRs de stack".
```

### Bloco 3: Atualizar status global — Milestone B sai de "deferido" e entra em "autorado"

**Localizar** a entry que diz "Milestone B autoria deferida" (ou equivalente; depende do estado atual do session-handoff) e **substituir** por:

```markdown
- **Milestone B (semgrep-runner standalone validado)** — **autorado** (#27, `docs/tasks.md` v1.2, Provisões A+B + T05/T06/T07 + gate milestone-level placeholder). Implementação destrava após PR mecânica de tasks.md mergear + Provisão A mergear (bloqueia T06) + Provisão B mergear (bloqueia T07). Custo total estimado: ~13-14h.
```

### Bloco 4: Atualizar "Resolver pós-Milestone B aberto" para refletir authoring de B + acrescentar pendência JS

**Locate:**

```markdown
**Resolver pós-Milestone B aberto:**

- Decomposição formal de Milestones C e D em sessões Chat dedicadas sequenciais.
```

**Substitute by:**

```markdown
**Resolver após Milestone B fechar (gate milestone-level):**

- Decomposição formal de Milestone C (pipeline multi-agente operacional local) em sessão Chat dedicada.
- Decomposição formal de Milestone D (CI/CD + validação empírica) em sessão Chat dedicada, sequencial a C.
- (Opcional, janela 15/06 entrega → 30/06 defesa) **Cobertura JS/TS para recognizers BR**: adicionar `languages: [javascript, typescript]` a regras BR existentes ou criar regras paralelas, com fixture pack JS análogo ao Python. ~6-7h totais. Materialização nessa janela fortalece narrativa defensiva do TCC ao demonstrar empiricamente RF-008 generalizada para detecção sintática sem ampliar escopo do MVP. Detalhes em `docs/tasks.md` §"Pós-Milestone B aberto".
```

### Bloco 5: Adicionar trilhas próximas como pendências organizadas por horizonte

**Add** como nova seção logo após o Bloco 4:

```markdown
**Resolver em sessões subsequentes a #27 (ordem natural — A precede E/F/G; B pode rodar antes ou em paralelo a C; D destrava após A):**

A. **PR mecânica `docs/tasks-milestone-b-decomposition`** (Code, ~30-40min). Aplica 4 blocos do diff aplicável de #27 + 2 fixes do Chat review. Não bloqueia T05 mas cristaliza referência.

B. **Provisão A — `chore/canonical-sync-C-semgrep-runner`** (Chat dedicada, ~3.5h total: ~2h Chat + ~1.5h Code). 4 commits internos: canonical sync Option B + compact sync cirúrgico + README pin Semgrep + ADR-0001 Decision 2 amendment in-place. **Bloqueia T06.**

C. **Provisão B — `feat/fixtures/recognizers-pack-br`** (Chat dedicada, ~2-2.5h total). Seis snippets positivos + negativos para os identificadores BR + README com AS coverage. Não bloqueia T05 nem T06. **Bloqueia T07.**

D. **T05 (Code, ~1.5-2h)** — server skeleton + rule set loader. Destrava após A.

E. **T06 (Code, ~3h)** — `scan_diff` completo: subprocess + 6 errorCodes + wire format Option B. Destrava após D + B.

F. **T07 (Code, ~2-2.5h)** — six recognizers brasileiros + validação contra fixture pack BR. Destrava após E + C.

G. **Gate milestone-level Milestone B** (Chat dedicada, ~1h). Manual exercise via MCP Inspector contra RF-001 + RF-002 sobre série de seis PRs sintéticos. Destrava após T05-T07 fecharem gate task-level. Pré-requisito procedural: binário `semgrep==1.163.0` instalado via `uv tool install` no ambiente do gate.
```