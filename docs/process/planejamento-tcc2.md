# Planejamento TCC2 — 28/maio — 15/junho de 2026

**Status:** ratificado em sessão de coordenação (28/mai). Substitui o
draft de bootstrap `plano-coordenacao-tcc2.md` da sessão #42, incorporando
calibração de probabilidade, buffer explícito, gate operacional de
"spec fechada", catalogação de prompts dos subagentes como artefato
distinto, modificação da estratégia de delegação T11+ ao Code, e
capacidade efetiva com dois PCs em uso simultâneo.

**Autoria:** sessão de coordenação a partir do draft #42 + review crítico
da sessão fresca.

---

## 1. Estado real em 28/mai

### Cronograma original vs realidade

A `docs/process/proposta-tcc2.md` §9 catalogou 6 semanas terminando 15/jun:

| Semana | Período | Entregáveis catalogados | Estado real em 28/mai |
|--------|---------|------------------------|------------------------|
| 1 | 05–11/mai | Specs MCP servers + ADR-0002 | ✓ feito (Milestone B mergeado) |
| 2 | 12–18/mai | Implementação MCP servers + recognizers BR | ✓ feito (Milestone B PASS empírico) |
| 3 | 19–25/mai | Specs dos 5 subagentes + coordinator | ⚠ parcial — Reporter spec 0.3.0 + coordinator v3 mergeados |
| 4 | 26/mai – 1/jun | Implementação subagentes + coordinator + emit_report | ✗ bloqueada — depende de semana 3 fechar |
| 5 | 2 – 8/jun | GitHub Action + integração e2e + benchmark sintético | ✗ bloqueada |
| 6 | 9 – 15/jun | Validação empírica + redação TCC2 + entrega | ✗ bloqueada |

**Slip identificado: ~1.5 semana.** Este plano absorve semanas 3-6 do
cronograma original em 18 dias úteis + 1 dia de entrega.

### Artefatos já mergeados (consolidados)

- Milestone A (policy-reader) — completo.
- Milestone B (semgrep-runner) — completo, gate PASS.
- `docs/architecture-overview.md`, `docs/REQUIREMENTS.md`, `docs/tasks.md`.
- `docs/specs/subagents/coordinator.md` v3 (mergeado em 28/mai).
- `docs/specs/subagents/reporter.md` v0.3.0.
- 11 ADRs autoradas (ADR-0001 a ADR-0011).
- ~150 entries de `docs/process/learning-log.md`, incluindo entry #42.
- `docs/process/session-handoff.md` substituído pela versão #42.

---

## 2. Escopo final ratificado (15/jun)

João tem carta branca do orientador. Entregável definido:

1. **Software funcionando (POC MVP)** — coordinator + 5 subagentes
   executando pipeline end-to-end contra PRs sintéticos via GitHub
   Action. Cobertura de 2-3 cenários load-bearing, não exaustiva de
   RF-001 a RF-008.
2. **Relatório técnico TCC2** seguindo modelo institucional UTFPR
   (`Modelo_RelatórioTécnicodeTCC2DOC.pdf`): 3 capítulos (Introdução,
   Desenvolvimento, Conclusões) + Referências, ~15-25 páginas finais.

### Camada 3-MVP — ratificada

Reduz Camada 3 completa (~25-45h) para versão MVP (~15-25h) preservando
defensibilidade acadêmica:

**Incluído:**

- 3 PRs sintéticos cobrindo cenários load-bearing (compliant; violation;
  skip).
- GitHub Action funcional para esses 3 PRs (matrix simples).
- Harness Python local rodando 3 PRs sintéticos + comparação contra
  `.expected-report.json`.
- 2 validações e2e completas (debug + prompt refinement quando
  necessário).
- Gate milestone-level documentado QUALITATIVAMENTE: critério explícito
  de PASS/FAIL em prosa, evidência manual de cobertura.

**Deferido para "Future Work" / Capítulo 3:**

- Matrix completa de 6-8 PRs sintéticos.
- Gate milestone-level automatizado e quantitativo (precision/recall/F1).
- Edge cases de prompt regression.
- Multi-cliente expansion (ADR-0005).
- Recognizers BR completos (6 tipos; MVP entrega o que existe do
  Milestone A).

A decisão de scope-discipline é academicamente legítima se o Capítulo 3
documentar o defer com critério explícito — pattern já praticado em
ADR-0005 D4 (cascading deferido), ADR-0007 (MVP collection-only) e
Provisão MC-E (`claude-agent-sdk` adoption deferida).

---

## 3. Critical path e capacidade efetiva

### Dois sub-paths que se encontram em "impl coordinator + emit_report"

**Sub-path Chat (specs subagentes → coordinator-flesh-completo):**

```
Triager-sanity (destila _template-subagent.md)
    → Detector spec
        → Classifier spec
            → Matcher spec
                → coordinator.md v4 (integra learnings)
```

**Sub-path Code (skeleton → impl subagentes → impl coordinator):**

```
Skeleton + emit_report stub
    → Impl Triager (após Triager spec)
        → Impl Detector (após Detector spec)
            → Impl Classifier (após Classifier spec)
                → Impl Matcher (após Matcher spec)
                    → Impl coordinator (após coordinator v4)
                        → emit_report real
                            → GitHub Action funcional
```

**Janela de encontro:** impl coordinator depende de coordinator v4 (final
sub-path Chat) + impl de todos os subagentes (final sub-path Code). Os
dois sub-paths progridem em paralelo até esse ponto.

### Tudo que NÃO está nos sub-paths roda em paralelo

- Redação do relatório TCC2 §1.1-1.4 + §2.3 (material já existe em
  massa).
- PRs sintéticos autoria (3 cenários).
- GitHub Action skeleton yaml.
- Code reviews independentes de specs (após autoria mergear).
- Provisão MC-C (ADR-0012 stale → ADR-0011).
- arch-overview Beat 2 (companion edit).

### Capacidade efetiva com dois PCs em uso simultâneo

PC1 = foreground Chat (autoria spec, decisão arquitetural).
PC2 = Code rodando assíncrono + Chat secundário (redação relatório,
revisão de output Code).

O que dois PCs habilitam:

- Code rodando em PC2 sem monitoramento close-loop, enquanto Chat
  foreground em PC1. Minutos de espera de Code viram tempo útil em PC1.
- Duas sessões Chat mantidas contextualmente sem fechar/reabrir: PC1
  autoria spec; PC2 redação relatório.
- Code em PC2 + Chat de coordenação em PC1 em momentos de revisão.

O que dois PCs **não** resolvem:

- Autoria de Matcher spec e coordinator-flesh-completo simultaneamente
  (mesmo cérebro humano, critical path conceitual indivisível).
- Decisões substantivas em sequência (D7 → D4 → D5).

Paralelização do humano-coordinator é eficaz quando tarefas são
independentes e output de uma não bloqueia decisão da outra — mesmo
princípio que governa parallel subagent execution no sistema.

---

## 4. Cronograma 3-semana detalhado

### Semana 1 — 28/mai a 2/jun (6 dias)

**Sub-path Chat (critical, PC1):**

| Sessão | Escopo | Custo |
|--------|--------|-------|
| Triager-sanity | Redigir `docs/specs/subagents/triager.md` + destilar `_template-subagent.md` + decidir 4 itens deferidos da Reporter spec §8.4 | 30-60min |
| Detector autoria | Redigir `docs/specs/subagents/detector.md` (heurística snippet + integração semgrep-runner) | 45-90min |
| Iteração Detector (se necessário) | Second-pass se Code review apontar gap | 30-60min |

**Sub-path Code (paralelo, PC2):**

| Sessão | Escopo | Custo |
|--------|--------|-------|
| Provisão MC-C | ADR-0012 stale → ADR-0011, branch isolada | 15-20min |
| Skeleton código | `src/coordinator/{models,constants,system_prompts,tools,__main__}.py` + `src/subagents/*.py` type stubs com docstrings + **emit_report stub funcional**, briefing T02b-style | 45-60min |
| T11.Reporter decomposition | Proxy test #1 do método de delegação | 30-45min |
| T11.Triager decomposition | Proxy test #2 (após Triager spec mergeada); só se #1 passar | 30-45min |
| GitHub Action skeleton | `.github/workflows/lgpd-review.yml` com matrix placeholder + secrets + invocação stub | 30-45min |
| Code review Detector | Após autoria, lentes "cross-doc rigoroso + arquitetural gaps" | 30-45min |
| Benchmark planning + PR sintético #1 | Decisão Chat curta dos 3 cenários + Code redige primeiro PR sintético | 1-2h |

**Relatório TCC2 (PC2 dedicado):**

| Sessão | Escopo | Custo |
|--------|--------|-------|
| Draft TCC2 §1.1-1.4 + §2.3 | Seções com material existente (proposta-tcc2.md §1+§3+§5 + arch-overview + ADRs) | 2-3h |

**Total semana 1:** ~7-10h Chat + ~4-6h Code distribuídos.

### Semana 2 — 3 a 9/jun (7 dias)

**Sub-path Chat (critical, PC1):**

| Sessão | Escopo | Custo |
|--------|--------|-------|
| Classifier autoria | Redigir `docs/specs/subagents/classifier.md` (vocab access strategy + vocab membership decision) | 1-1.5h |
| Iteração Classifier (se necessário) | Second-pass se Code review apontar gap | 30-60min |
| Matcher prep | Sessão Chat decidindo 5+ questões load-bearing antes de autoria (ADR-0007 verdict semantics, multi-clause, `requires_human_review`, etc.) | 30-45min |
| Matcher autoria | Redigir `docs/specs/subagents/matcher.md` | 1.5-2.5h |
| Matcher second-pass | Provável (Matcher é wildcard arquitetural) | 1-2h |
| coordinator-flesh-completo | Integra learnings das 5 specs no coordinator.md v3 → v4 | 1.5-2h |

**Sub-path Code (paralelo, PC2):**

| Sessão | Escopo | Custo |
|--------|--------|-------|
| T11.Detector + T11.Classifier decomposition | Sequenciais após cada spec mergear (se proxy #1+#2 da semana 1 passou) | 30-45min cada |
| T11.Matcher decomposition | Após Matcher mergeada | 30-45min |
| Impl Triager | Implementação após spec mergeada + skeleton existe | 4-8h |
| Impl Detector | Implementação após spec mergeada | 4-8h |
| PR sintético #2 (violation) | Code redige após Triager-sanity confirmar cenários | 1-2h |
| PR sintético #3 (skip) | Code redige | 1-2h |
| Code review Classifier | Lentes "cross-doc rigoroso + arquitetural gaps" | 30-45min |

**Relatório TCC2 (PC2 dedicado):**

| Sessão | Escopo | Custo |
|--------|--------|-------|
| Draft TCC2 §2.1 + §2.2 + §2.4 partial | Funcionalidades macro + Persistência (Política + scratchpad) + Testes/Avaliação (estratégia, antes dos resultados) | 2-3h |

**Total semana 2:** ~10-15h Chat + ~12-20h Code.

### Semana 3 — 10 a 13/jun (4 dias)

**Convergência crítica (Chat + Code intercalados):**

| Sessão | Escopo | Custo |
|--------|--------|-------|
| Prompts subagentes — autoria | Redigir prompts reais em `src/coordinator/system_prompts.py` (artefato derivado das specs, decisão substantiva) | 2-4h Chat |
| Impl Classifier + Matcher + coordinator | Implementação após specs e prompts | 12-20h Code |
| Impl emit_report real + GitHub Action funcional | Custom tool + workflow yaml integrado | 3-6h Code |
| Harness local + 1ª validação e2e | Rodar 3 PRs sintéticos contra coordinator real | 4-8h Code |
| Prompt refinement (provável) | Debug ciclos quando validação e2e expor regressions | 3-8h Chat+Code |
| 2ª validação e2e | Confirmação pós-refinement | 2-4h Code |

**Relatório TCC2:**

| Sessão | Escopo | Custo |
|--------|--------|-------|
| §2.4 conclusion + §3 Conclusões | Resultados empíricos + dificuldades + próximos passos | 3-5h |

**Total semana 3:** ~25-45h convergindo no entregável. Mais densa de
todas; absorve qualquer slip das semanas 1-2.

### Buffer + finalização — 14/jun (1 dia)

| Sessão | Escopo | Custo |
|--------|--------|-------|
| Figuras + tabelas + revisão final | Diagramas mermaid renderizados, tabelas de resultados, formatação UTFPR | 3-5h |
| Buffer absorção de imprevisto | Reservado para slip operacional inevitável | até 8h |

**Critério de uso:** 14/jun é finalização tranquila SE semanas 1-3
fecharem no plano. SE houver slip relevante na semana 3 (validação e2e
expondo regression cascateante, ou §3 do relatório precisando reescrita
substancial), 14/jun absorve em vez de gerar slip para 15/jun.

### Entrega — 15/jun

Revisão final + upload UTFPR. **Não é dia de execução técnica.**

---

## 5. Cardápio operacional — paralelizável agora vs bloqueado

### Disparáveis hoje em PC2 (sem depender de spec nova)

- Provisão MC-C (ADR-0012 stale → ADR-0011) — 15-20min.
- Skeleton de código + emit_report stub funcional — 45-60min.
- GitHub Action skeleton yaml — 30-45min.
- PR sintético #1 autoria (cenário compliant) — 1-2h.
- Redação TCC2 §1.1-1.4 + §2.3 (Chat dedicado em PC2 enquanto PC1 faz
  Triager-sanity) — 2-3h primeiro draft.

### Disparáveis após Triager-sanity fechar

- Detector spec autoria (PC1) — depende de `_template-subagent.md`
  destilado.
- Decisão dos 3 cenários load-bearing dos PRs sintéticos (PC1 curto).
- PRs sintéticos #2 e #3 autoria (PC2 Code).
- T11.Reporter decomposition (PC2 Code, proxy test #1).

### Disparáveis após Triager + Detector specs mergeadas

- Impl Triager (PC2 Code, 4-8h).
- Impl Detector (PC2 Code, 4-8h).
- T11.Triager decomposition (proxy test #2).

### Bloqueado pelo critical path Chat (specs)

- coordinator-flesh-completo — depende das 5 specs mergeadas.
- Impl Classifier — depende de Classifier spec.
- Impl Matcher — depende de Matcher spec.
- **Prompts dos subagentes (autoria)** — depende das specs mergeadas;
  decisão substantiva, não Code mecânico.

### Bloqueado pelo critical path Code (impl)

- Impl coordinator integrado — depende de coordinator v4 + impl
  subagentes.
- emit_report custom tool real — depende de coordinator v4.
- Validação e2e — depende de impl completa + emit_report real +
  GitHub Action funcional + 3 PRs sintéticos prontos.
- Prompt refinement — depende de validação e2e ter rodado.
- 2ª validação e2e — depende de prompt refinement.

### Bloqueado por validação e2e

- Relatório TCC2 §2.4 conclusion (resultados empíricos).
- Relatório TCC2 §3 Conclusões (resultados + dificuldades + next steps).
- Figuras de resultados, tabelas finais, formatação UTFPR completa.

---

## 6. Gate operacional — "spec fechada"

Critério explícito para quando parar de iterar uma spec e mover adiante:

1. Todos os campos load-bearing preenchidos (decisões arquiteturais,
   tool surface, formato de input/output).
2. Decisões deferidas catalogadas com justificativa explícita (§8.x da
   spec).
3. Suficiente para impl proceder sem necessidade de volta a Chat para
   decisão arquitetural não-trivial.
4. Code review independente sem flag crítica.

Critério, não impressão. Reporter v0.3.0 atende todos os 4; vira
referência operacional para Triager/Detector/Classifier/Matcher.

**Iterações orçadas no cronograma:** Reporter teve 3 iterações.
Subagentes subsequentes orçados em 1.2-1.5 iteração média. Detector e
Classifier provavelmente 1ª iteração + Code review independente (~20min
Chat absorvendo). Matcher provavelmente 1ª + Chat second-pass (~1-2h).

---

## 7. Prompts dos subagentes — artefato distinto

A spec é referência técnica do subagente. O **prompt do subagente** (em
`src/coordinator/system_prompts.py`) é artefato distinto, derivado da
spec mas com restrições próprias:

- Formato de input/output esperado pelo coordinator.
- Gestão de contexto (escalation patterns, scratchpad usage).
- Instrução de tool use (qual ferramenta chamar, quando, com que
  argumentos).
- Few-shot examples se a spec indicar necessidade.

Redação dos prompts requer Chat dedicado (catalogado na semana 3 como
2-4h). Não é Code mecânico — é tradução das decisões arquiteturais da
spec para instruções operacionais ao LLM. Risco de subestimar se tratado
como subitem de impl.

---

## 8. Critérios de slip ratchet

Critérios objetivos de quando re-planejar:

**Ratchet 1 (final semana 1, 2/jun):** se NÃO fecharem até 2/jun:

- Triager spec mergeada + `_template-subagent.md` destilado.
- Detector spec mergeada.
- Skeleton código aplicado (com emit_report stub).
- Relatório TCC2 §1.1-1.4 + §2.3 em draft funcional.
- T11.Reporter decomposition validada (proxy test #1).
- 1 PR sintético criado por Code.

→ Re-planejar semana 2 com escopo reduzido (mais que 2 desses 6 não
fechando aciona ratchet).

**Ratchet 2 (final semana 2, 9/jun):** se Matcher + coordinator-flesh-
completo NÃO fecharem até 9/jun → reduzir Camada 3-MVP para 2 PRs
sintéticos OU começar relatório §3 com material parcial.

**Ratchet 3 (semana 3, 12/jun):** se 1ª validação e2e PASS não fechar
até 12/jun → priorizar relatório TCC2 finalização + entregar POC com 1
cenário validado em vez de 2-3.

---

## 9. Riscos top-5 + probabilidade calibrada

### Probabilidade de fechar TUDO em 15/jun

- Com paralelização disciplinada (dois PCs + relatório semana 1):
  **~45-55%**.
- Sem paralelização do relatório (deixando para última semana):
  **~25-35%**.
- Com paralelização mas Matcher virando mini-Reporter (4 iterações):
  **~30-40%**.
- Cenário desastre (Matcher slip + validação e2e expor problemas +
  capacity reduction): **~10-20%**.

Calibração revisada de 60-70% do draft #42 → 45-55% considerando
probabilidade conjunta dos 5 riscos abaixo + ausência de buffer puro
expressivo. Slip ratchets são o mecanismo principal de defesa, não
otimismo de execução.

### Riscos

**Risco 1 — Matcher virar mini-Reporter (4+ iterações).** Reporter
consumiu ~5-7h sozinha (3 iterações + 1 catch crítico). Matcher tem
decisões load-bearing concentradas: ADR-0007 verdict semantics (4
valores), ADR-0011 cascading, `not_applicable` semantics,
`requires_human_review` deferred da Reporter §8.4, multi-clause logic.
Se 2+ exigirem ratchet, Matcher consome semana 2 inteira.

*Mitigação:* sessão Matcher prep (~30-45min) decidindo 5+ questões
ANTES de autoria. Catalogada na semana 2.

**Risco 2 — Triager-sanity não destila template limpo.** Se template
precisar refactor no meio de Detector ou Classifier, retrabalho cascateia.

*Mitigação:* Triager-sanity é a primeira sessão substantiva pós-
coordenação; sinal cedo. Refactor cabe na semana 1 sem comprometer
semanas 2-3.

**Risco 3 — Validação e2e expor prompt regression cascateante.**
Primeira execução full-stack tipicamente expõe problemas que specs não
previram. 2-3 ciclos de prompt refinement por subagente até estável.

*Mitigação:* validação e2e contra apenas 3 PRs sintéticos load-bearing
(Camada 3-MVP), não matrix completa. Refinement ciclos cabem na semana
3 se forem 1-2 specs; se forem 3+, estouro do prazo aciona ratchet 3.

**Risco 4 — Code retornar artefatos ruins** (skeleton ruim, decomposição
T11+ ruim, PR sintético ruim, GitHub Action ruim). Paralelização vira
ilusão se Chat reescreve do zero.

*Mitigação:* primeiro artefato Code de cada classe é proxy test —
skeleton código, T11.Reporter decomposition (+T11.Triager como
confirmação antes de generalizar), PR sintético #1. Se retornarem
bons, escala; se ruins, abandona paralelização daquela classe.
Briefing T02b-style obrigatório.

**Risco 5 — Capacidade cognitiva.** 4-5h/dia sustentáveis em 18 dias +
Vilt + prep prova certificação Claude Architect (março/2026) + vida
pessoal é carga alta. Quebra de saúde tira tudo do mapa.

*Mitigação:* honestidade epistêmica sobre fadiga; buffer 14/jun absorve
slip operacional inevitável; slip de 1-2 dias na semana 1 sinaliza
ajustar paralelização.

---

## 10. Decisões ratificadas

**D1 — Camada 3-MVP escopo final.** 3 PRs sintéticos (compliant +
violation + skip), GitHub Action funcional, harness local, 2 validações
e2e, gate milestone qualitativo. — Ratificado.

**D2 — Relatório TCC2 começa semana 1.** Sessão Chat dedicada ~2-3h
drafta 50-60% das seções 1.1-1.4 + 2.1 + 2.3 ainda esta semana.
— Ratificado.

**D3 — Skeleton de código semana 1, briefing T02b-style obrigatório.**
**Inclui emit_report stub funcional** (adendo ao plano original — é
prerequisite do ROI 4). — Ratificado.

**D7 (reordenada para vir antes de D4 e D5) — Code para decomposição
T11+ por delegação com proxy test em DOIS casos.** T11.Reporter como
proxy #1; T11.Triager como proxy #2 (não generalizar com amostra de 1).
Se ambos voltarem bons, escala para Detector/Classifier/Matcher. Se
qualquer um ruim, mantém só Code reviews + companion edits. — Ratificado
com modificação.

**D4 — Code review independente para Detector + Classifier; Chat
second-pass para Matcher.** Reporter pattern (Chat second-pass) só para
Matcher pela complexidade arquitetural. Detector + Classifier usam first-
pass Chat + Code review independente (briefing "cross-doc rigoroso +
arquitetural gaps"). — Ratificado.

**D5 — Impl Triager + Detector em paralelo às specs Classifier/Matcher
(semana 2).** Depende de skeleton existir + emit_report stub funcional
+ proxy tests #1 e #2 do Code passarem. — Ratificado.

**D6 — Slip ratchets quantitativos.** Três ratchets catalogados em §8.
— Ratificado.

**D8 — ADR-0012 retroativo Milestone C.** Deferido para após coordinator-
flesh-completo (semana 2 final ou semana 3 início). Briefing forte para
Code redigir draft; Chat valida. — Ratificado.

---

## 11. Próximos passos imediatos pós-coordenação

**Dia 1 (28/mai, hoje):**

1. Code session — Provisão MC-C (ADR-0012 stale → ADR-0011) — 15-20min.
2. Code session — skeleton de código + emit_report stub com briefing
   T02b-style — 45-60min.
3. Code session — reorganizar `docs/` criando `docs/process/` e mover
   metadocumentos (briefing separado) — 30-45min.

**Dia 2 (29/mai):**

4. Chat session (PC1) — Triager-sanity — 30-60min. Output: spec do
   Triager + `_template-subagent.md` destilado + decisão dos 4 itens
   deferidos da Reporter spec §8.4.
5. Code session (PC2) — T11.Reporter decomposition (proxy test #1) —
   30-45min.

**Dia 3 (30/mai):**

6. Chat session (PC2 paralelo) — draft relatório TCC2 §1.1-1.4 + §2.3
   — 2-3h.
7. Chat session (PC1) — Detector autoria — 45-90min. Pode ser dia
   seguinte se capacidade não absorver.
8. Code session (PC2) — Code review Detector (após autoria mergear) —
   30-45min.

### Critério de validação operacional (fim semana 1)

Se até 2/jun tiver:

- Triager spec mergeada + `_template-subagent.md` destilado.
- Detector spec mergeada.
- Skeleton código aplicado (com emit_report stub).
- Relatório TCC2 §1.1-1.4 + §2.3 em draft funcional.
- T11.Reporter decomposition validada (proxy test #1).
- 1 PR sintético criado por Code.

→ Plano está na pista; segue semana 2 conforme cronograma.

Se mais de 2 desses 6 NÃO fecharem → ratchet 1 aciona; re-planejar
semana 2 com escopo reduzido.

---

## 12. Defense candidates para learning-log

Patterns emergentes registrados para o Capítulo de Método do TCC2:

**Recalibração de cronograma proporcional a slip detectado, sem
abandono de critério acadêmico.** Cronograma original previu 6 semanas
+ redução de scope para "future work" defensível. Slip de ~1.5 semana
detectado na semana 4 dispara re-planejamento com Camada 3-MVP definida
+ redação do relatório paralelizada + critérios de slip ratchet pré-
acordados + buffer explícito. Pattern reaproveitável: **scope discipline
+ scope discrimination + slip ratchets quantitativos + buffer
operacional**.

**Critical path discipline materializada em projeto acadêmico.**
Identificação explícita de nós serializados vs paralelizáveis;
delegação ao Code apenas no que NÃO está no critical path; proxy tests
em dois casos antes de generalizar paralelização. Pattern do exam guide
D1.6 (task decomposition) aplicado ao próprio metaprojeto de TCC.

**Coordenação Chat-Code como instância do pattern coordinator-subagent.**
Chat é coordinator (planejamento, decisão arquitetural, validação);
Code é subagent especializado (decomposição mecânica, drafts derivativos,
cross-doc reviews). Mesmo pattern arquitetural do produto materializado
na divisão de trabalho humano-LLM. Dois PCs em uso simultâneo são
paralelização do humano-coordinator — instância de parallel subagent
execution aplicada ao agente humano.

**Gate operacional explícito ("spec fechada") como antídoto a iteração
indefinida.** Reporter spec teve 3 iterações + 1 catch crítico. Sem
critério explícito de parada, cada spec subsequente vira mini-Reporter.
Critério em §6 deste plano (campos load-bearing + decisões deferidas
catalogadas + suficiência para impl + Code review sem flag crítica)
substitui impressão por checklist.

---

**Status do documento:** ratificado. Sessão de coordenação executa
imediatamente §11 (próximos passos) e usa §8 (ratchets) como mecanismo
de defesa.

**Custo estimado de execução do plano se seguido:** ~70-110h
distribuídas em 18 dias úteis = 4-6h/dia sustentáveis. Cabe SE foco
absoluto + nenhum bloqueio externo + Matcher não virar mini-Reporter.

**Probabilidade subjetiva de fechar TUDO em 15/jun:** ~45-55%.
