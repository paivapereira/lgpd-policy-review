# Session handoff — patch pós-sessão #29

Aplicar como direct commit em `main` sobre `docs/session-handoff.md`.
Commit message sugerida (ASCII-fied):
`docs: close session #29 — canonical-sync-D + T05 skeleton (PR #XX + PR #YY)`

---

## Bloco 1 — Marcar T05 como fechada e adicionar canonical-sync-D como fechada

**Locate** o item D na lista de tasks de Milestone B (ainda marcado como
pendente):

```
D. **T05 — server skeleton + rule set loader** (Code, ~1.5-2h). **Próxima sessão Code.** Pré-requisitos satisfeitos:
```

**Substitute by:**

```
D. **T05 — server skeleton + rule set loader** — **Fechada em sessão #29.**
   PR `feat/semgrep-runner-skeleton` mergeada em main. 4 commits internos
   (squash-merge): bootstrap modules (errors, models, loader com
   compute_rules_version SHA-256 determinístico), server skeleton com
   scan_diff stub retornando NOT_IMPLEMENTED envelope, placeholder rule +
   .mcp.json entry, tests (anchor + AS-1..AS-8). 10 arquivos, 650 insertions.
   Gates: 64 passing (53 policy_reader + 11 semgrep_runner), ruff clean,
   mypy clean. T06 destravado.
```

---

## Bloco 2 — Adicionar canonical-sync-D como item fechado

**Locate** o item C (Provisão B) na lista de tasks de Milestone B:

```
C. **Provisão B — `feat/fixtures/recognizers-pack-br`.** **Fechada em sessão #28**
```

**Add** ANTES do item C (novo item entre B e C):

```
B.5. **canonical-sync-D — `chore/canonical-sync-D-semgrep-runner`** — **Fechada
   em sessão #29.** PR mergeada em main. 3 commits internos: canonical.md sync
   (Cluster 1 description prosa unificada; Cluster 2 output structure 7 decisões
   mixed-direction; Cluster 3 §5 reorganizado per _template.md com substituição
   atômica; Bloco 4 boas práticas Semgrep em §2.2 e §4.2), compact.md sync
   (paridade com canonical pós-sync), tasks.md AS-7 companion edit. +90/-76 linhas
   canonical, +44/-30 compact, +1/-1 tasks.md. Decisão arquitetural latente
   resolvida: semgrep-runner como runner genérico (Opção C), validada via
   web_search contra docs Semgrep.
```

---

## Bloco 3 — Atualizar próxima sessão Code para T06 (e F1 housekeeping)

**Locate** o bloco "Próxima sessão Code" (item D atualizado pelo Bloco 1 acima
já reflete T05 como fechada). **Add** novo bloco após D:

```
**Próxima sessão Code recomendada: F1 housekeeping antes de T06.**

- **F1 — PR `docs/refresh-stale-state`** (Code, ~20-30min mecânico, sem deliberação).
  Resolve CLAUDE.md §"Status flags for the agent" (Milestone A fechado, 64 tests
  passando, 3/3 resources + tools policy-reader operacionais, semgrep-runner skeleton
  operacional), REQUIREMENTS.md RNF-001 (Pydantic 2.5→2.13.4; remove "em débito
  de sincronização"; ADR-0004 referenciado corretamente), policy-reader compact §5.3
  nota MVP removida/atualizada, DESIGN.md "Decisões arquiteturais críticas" adicionando
  ADRs 0006-0010, semgrep_version nos exemplos das specs uniformizado para 1.163.0
  (canonical:1.92.0 + compact:1.62.0 → ambos 1.163.0), rules_version compact §5.1
  exemplo uniformizado para forma sha256: (estava "rules-2026-04-1a7f3b").

E. **T06 — `scan_diff` completo** (Code, ~3h). Subprocess + 6 errorCodes + wire
   format Option B per canonical §5 + canonical §8.6 (per-call binary check em
   vez de startup; BINARY_UNAVAILABLE per-call). Pré-requisitos satisfeitos: T05
   mergeado, Provisão A mergeada, ADR-0010 ratificado. Notas para implementação:
   --metrics=off + --json + --baseline-commit <base_ref> como flags obrigatórias;
   NÃO passar --error (sistema informativo per RNF-002); timeout budget total via
   Python runtime (primitivo a decidir em T06) ortogonal ao --timeout interno do
   Semgrep CLI.
```

---

## Bloco 4 — Registrar débitos cross-doc da sessão #29

**Locate** a seção "Débitos residuais não-bloqueantes" (ou equivalente; título
pode variar per versão atual do handoff).

**Add** ao final desta seção:

```
**Débitos catalogados em review cross-doc pós-#28 (sessão #29). 3 PRs propostas:**

- **PR `docs/refresh-stale-state`** (~30-45min Code). Cobre: F1 (CLAUDE.md status
  flags), F3 (REQUIREMENTS.md RNF-001 stack stale), G1 (policy-reader compact
  §5.3 nota MVP), G6 (DESIGN.md ADRs 0006-0010), G8/G9 (semgrep_version +
  rules_version exemplos uniformizados). **Prioritária — F1 afeta mental model
  de todo agente a partir de hoje.**

- **PR `docs/adr-foundational-amendments`** (~1h Chat + Code). Amendments in-place:
  F2 (ADR-0001 D3 format de ID: LGPD-Art-7-I → POL-NNN opaco), G2 (ADR-0005 D1+D2:
  article_source → statutory_reference), G7 (ADR-0002 D4: INVALID_REF_RESOLUTION
  system → GIT_REF_NOT_FOUND business), G10 (ADR-0002 D7: policy://vocabularies
  adicionado), G11 (ADR-0008 companion edit: CLAUDE.md → .claude/rules/spec-driven-workflow.md),
  G12 (ADR-0003 tamanhos canonical: 673/440 → 960/517 + nota empírica).

- **PR `docs/canonical-sync-E-policy-reader`** (~30-45min Code). Sync interno
  specs policy-reader: G3 (INVALID_OPERATION source: policy/SCHEMA.md →
  policy/vocabularies/<framework>/operation.yaml, 2 ocorrências), G4 (POL-000
  source: policy/SCHEMA.md → policy/clauses/POL-000.yaml, 3 ocorrências),
  G13 (verificar _format_stat_ref vs _format_law_reference via tools.py).

**Sweep regras imutáveis (ADR-0001 Decision 4 ↔ CLAUDE.md §"Immutable domain rules")
— crítica antes de Milestone C arrancar.** Deliberação semântica Chat dedicada
(~1.5h). Duas das três regras diferem substantivamente (F2: ID format LGPD-Art-7-I
vs POL-NNN; F4: "two-axis" vs "três eixos").

**proposta-tcc2.md §7** — amendment cirúrgico pontual: "FastMCP 2.x"→"FastMCP 3.x",
"Pydantic 2.5"→"Pydantic 2.13.x", "tripartite"→"two-scope" (ADR-0008 amendment
companion edit aplicado no lugar errado). §6 sobre "dois eixos" defensável como
histórico — não atualizar.
```

---

## Bloco 5 — Atualizar estado do Milestone B no topo do handoff

**Locate** a linha de status do Milestone B (provavelmente no topo do handoff
ou em seção de "Estado atual"). Forma provável:

```
Milestone B em progresso — T05 pendente (próxima sessão Code).
```

**Substitute by:**

```
Milestone B em progresso — T05 mergeada; próxima sessão Code é F1 housekeeping
(docs/refresh-stale-state, ~30min) seguida de T06 (scan_diff completo, ~3h).
PRs mergeadas em Milestone B até sessão #29: Provisão A, Provisão B,
canonical-sync-D, T05 skeleton. Pendentes: T06, T07, gate milestone-level.
```

---

## Validação pós-aplicação

```bash
# T05 marcada como fechada
git grep -n "Fechada em sessão #29" docs/session-handoff.md  # >= 2 matches

# canonical-sync-D registrada
git grep -n "canonical-sync-D" docs/session-handoff.md  # >= 1 match

# F1 housekeeping antes de T06
git grep -n "docs/refresh-stale-state" docs/session-handoff.md  # >= 1 match

# Débitos cross-doc catalogados
git grep -n "review cross-doc" docs/session-handoff.md  # >= 1 match

# T06 como próxima sessão Code
git grep -n "T06.*scan_diff completo" docs/session-handoff.md  # >= 1 match

# Sweep regras imutáveis mantida como crítica
git grep -n "antes de Milestone C arrancar" docs/session-handoff.md  # >= 1 match
```