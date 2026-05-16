# Session handoff

## Handoff de fechamento da #17 (consolidado e final)

**Sessão fechada:** #17 (Chat) — 2026-05-15
**Próxima sessão:** #18 (Chat) — Authoring de `docs/tasks.md` sob ADR-0008 (as amended 2026-05-16) + sessão Chat pré-implementação de POL-001
**Estado do git:** main em `914b00f` (PR #24 mergeado, último). PR #23 e PR #24 ambos em main; branches `docs/adr-retroactive-conventions` e `docs/adr-0008-sdd-calibration` podem ser deletadas.

---

### Estado consolidado dos artefatos pós-#17

Em main já — Fase 1 (PR #22 mergeado em sessão #16):
- `docs/architecture-overview.md` v final pós-multi-cliente
- `docs/adr/0001-bootstrap.md` (drift simbólico em §2: pyenv-win e FastMCP unpinned; substantive authority delegada a ADR-0004; editorial sync da prosa é opcional)
- `docs/adr/0002-mcp-conventions-and-deferments.md`
- `docs/adr/0003-dual-spec-architecture.md`
- `docs/adr/0005-multi-client-policy-architecture.md`
- `docs/specs/policy-reader/canonical.md` + `compact.md`
- `docs/specs/semgrep-runner/canonical.md` + `compact.md`
- `policy/SCHEMA.md` (camada estrutural + jurisdicional)
- `policy/clauses/POL-000.yaml` + `policy/rationale/POL-000.md`
- `policy/vocabularies/LGPD/{operation,lawful_basis,control,out_of_scope}.yaml`
- `docs/DESIGN.md`

Em main já — pós-#17 (PR #23 mergeado como `f63ddf7`):
- `docs/REQUIREMENTS.md` v1.0 — 9 RFs + 2 RNFs, source-of-truth de capacidades observáveis
- `docs/adr/0006-language-conventions.md` — PT em docs técnicos + EN em vocabulários jurisdicionais
- Patches em specs do `policy-reader` (`collect` → `collection`)
- (ADR-0007 foi adicionado e revertido dentro do PR — não consta em main; squash message inclui o título por ter agregado todos os commits do branch)

Em main já — pós-#17 (PR #24 mergeado como `914b00f`):
- `docs/adr/0008-task-decomposition-and-verification.md` — calibração SDD para Opus 4.7
- Pointer em `CLAUDE.md`
- §7 + §11 atualizados em `docs/proposta-tcc2.md` (Rajasekaran 2026 + Building Effective Agents 2025)

---

### Hashes da #17 (audit trail interno)

Sobrevive a squash-merge — após merge dos PRs, hashes individuais somem do main, mas ficam registrados aqui.

**PR #23** (`docs/adr-retroactive-conventions`) — squash em main como `f63ddf7`:
- `4953a9b` — docs(specs): fix collect → collection token in policy-reader example
- `9d0d38a` — docs(adr): add ADR-0006 — language conventions
- `1a5bed5` — docs(adr): add ADR-0007 — MVP collection-only scope (revertido)
- `09d4914` — docs: scope PR-23 cleanup — revert ADR-0007, calibrate ADR-0006

**PR #24** (`docs/adr-0008-sdd-calibration`) — squash em main como `914b00f`:
- `2ece0f3` — docs: add ADR-0008 calibrating SDD task decomposition for Opus 4.7

(Hash do próprio handoff omitido — só conhecido pós-`git commit`.)

---

### Defaults arquiteturais consolidados (intactos pós-#17)

Estado **realizado** (não plano em progresso). Referência canônica em ADR-0005, herdado da Fase 1.

- Camada 1 (Política) é per-cliente; substituível por cliente sem alteração de código (ADR-0005 Decision 1).
- `legal_framework` é campo top-level único do header da Política, imutável durante sessão do server (ADR-0005 Decision 2).
- `accepted_law_identifiers` é lista de leis citáveis intra-jurisdição (e.g., `[LGPD, Marco_Civil]` numa Política brasileira).
- POL-000 é vocabulário universal (semântico, não estatutário); vive em `policy/clauses/`, estrutura governada por `policy/SCHEMA.md` §5 (ADR-0005 Decision 3).
- Quatro vocabulários jurisdicionais (`operation`, `lawful_basis`, `control`, `out_of_scope`) vivem em `policy/vocabularies/<framework>/*.yaml`.
- `policy-reader` expõe três resources (`policy://catalog`, `policy://schema-version`, `policy://vocabularies`) e três tools (`get_clause`, `find_clauses_by_law_article`, `check_applicability`).
- `policy://vocabularies` é compartilhado Matcher+Classifier (read-only resource); tools do `policy-reader` continuam exclusivas Matcher (ADR-0005 Decision 4).
- `check_applicability` retorna trinque de provenance `(policy_schema_version, policy_version, legal_framework)` em todo sucesso (ADR-0005 Decision 5).
- Sucessão de cláusulas é intra-Política (intra-`legal_framework`), via `successors` no bloco `tombstone` (ADR-0005 Decision 6).
- Mecanismo interno de reasoning de `check_applicability` é deferido para Fase 2 (ADR-0005 Decision 7).
- `semgrep-runner` rule set é bundled no projeto no MVP; per-cliente é deferimento explícito (ADR-0005 Decision 8).

---

### Pendências organizadas por horizonte

**Imediato (operacional seu):**
- Deletar branches mergeadas: `git push origin --delete docs/adr-retroactive-conventions docs/adr-0008-sdd-calibration` (e `git branch -d` no local).

**Sessão #18 (Chat) — agenda:**
- Authoring de `docs/tasks.md` v1.0 sob governança de ADR-0008 (as amended 2026-05-16). Conteúdo:
  - Estrutura por Milestones (A, B, C)
  - Milestone A detalhado: ~5 tasks + pré-implementação POL-001
  - Milestones B e C como placeholders ("specs a redigir, tasks a decompor após A")
  - Cada **milestone** carrega: RFs/RNFs cobertos + Dado/Quando/Então herdados de REQUIREMENTS.md + gate milestone-level (manual exercise via MCP Inspector validando cada acceptance criterion)
  - Cada **task** dentro de milestone carrega: nome, dependências, files previstos, função entregue (sem RF binding individual — ADR-0008 §2 amended), gate task-level (function-specific pytest + independent Chat review)
- Estimativa: 2-3 horas. PR dedicado de redação.

**Proposta Milestone A para #18 (insumo, não decisão).**

Esboço produzido em discussão pré-#18 (mesma sessão da emenda ADR-0008). #18 pode reformular livremente; objetivo é evitar re-derivação cold da estrutura.

*RFs/RNFs cobertos pelo Milestone A* (acceptance via Dado/Quando/Então das RFs em `docs/REQUIREMENTS.md`):
- **RF-001** (detecção de coleta) — `semgrep-runner`
- **RF-002** (6 BR identifiers: CPF/CNPJ/CNH/NIS-PIS/título/CNS) — `semgrep-runner` rule content
- **RF-004** (avaliação de conformidade, escopo `collection`) — `policy-reader.check_applicability`
- **RF-005** (veredito `indeterminate` honesto) — `policy-reader.check_applicability`
- **RF-009** (provenance trinque) — `policy-reader` handshake + `check_applicability`
- **RNF-001** parcial — stack/reprodutibilidade observável no startup loader
- **RF-007** e **RF-008** *mechanism-only* — validação de `accepted_law_identifiers` + `legal_framework` reportado em handshake e trinque. E2E delivery dessas duas fica para Milestones B/C (exige pipeline E2E + GDPR fixture).

*Fora de Milestone A* (depende de Milestones B/C, sem design fechado ainda):
- RF-003 (Classifier), RF-006 (Report JSON via Reporter), RF-007 E2E (cliente A vs B), RF-008 E2E (LGPD→GDPR rerun), RNF-002 (GitHub Action informativo).

*Tasks propostas (5, ordem topológica):*

1. **T01 — policy-reader bootstrap.** Loader (`policy.yaml` + `clauses/*.yaml` + `vocabularies/<framework>/*.yaml`) + resource `policy://schema-version` (trinque handshake) + abort-on-failure de startup. Função: server inicia limpo ou falha cedo; consumidor lê trinque antes de invocar tools.
2. **T02 — policy-reader retrieval.** Resource `policy://catalog` + tools `get_clause` e `find_clauses_by_law_article` (matching hierárquico `article_source`, validação de `lei` contra `accepted_law_identifiers`). Função: consumidor descobre cláusulas por ID ou por artigo de lei.
3. **T03 — policy-reader evaluation.** Resource `policy://vocabularies` + tool `check_applicability` (4 vereditos enumerados; MVP retorna `not_applicable` always até cláusulas substantivas existirem, com trinque de provenance em sucesso). Função: emitir veredito estruturado para um par (clause, structured_context).
4. **T04 — semgrep-runner core.** Loader (binary discovery, version check, `rules_version` via hash do rule set) + tool `scan_diff` (git ref resolve, subprocess + parse JSON, all-or-nothing timeout). Rule set bundled com 1-2 regras canário. Função: scan diff-aware retorna findings estruturados ou erro tipado.
5. **T05 — Brazilian recognizers.** 6 regras Semgrep (CPF/CNPJ/CNH/NIS-PIS/título de eleitor/CNS) substituem o rule set canário do T04 + fixtures de detecção positiva e negativa por identifier. Função: rule set bundled cobre os 6 identifiers com `data_categories` correto em cada finding.

*Pendências bloqueantes antes do primeiro Code session* (resolver em Chat dedicado ou inline em #18):

- **Decisão Semgrep-on-Windows** — onde Semgrep roda no ambiente Windows corporativo sem WSL (Docker / pip native / remote worker / CI-only). Bloqueia T04 — sem essa decisão, a forma do `loader` e do `scan_diff` muda radicalmente.
- **POL-001 a POL-005** (estimado) — POL-001 já é pré-implementação confirmada (ordem: ADR-0007 antes, POL-001 depois). POL-002 a POL-005 são em aberto: T03 sobrevive com `not_applicable` always, mas o **gate milestone-level** (Inspector exercitando RF-004 e RF-005 com vereditos diversos) precisa de cláusulas substantivas que exercitem `compliant`/`violation_candidate`/`indeterminate`. Decisão pendente: autorar POL-001..POL-005 numa sessão Chat ou apenas POL-001 e diferir.

*Gate milestone-level proposto* (roteiro Inspector cross-tool):
- RF-001: `scan_diff` em diff com chamada de função suspeita → finding emitido com `rule_id`.
- RF-002: `scan_diff` em diff cobrindo cada um dos 6 BR identifiers → 6 findings com `data_categories` correto.
- RF-004/-005: `check_applicability` sobre fixtures cobrindo os 4 vereditos (depende de POL-001..POL-005).
- RF-009: cada retorno de `check_applicability` + handshake carregam trinque `(policy_schema_version, policy_version, legal_framework)`.
- RF-007/-008 mechanism: `find_clauses_by_law_article` com `lei` fora de `accepted_law_identifiers` retorna `INVALID_LAW_IDENTIFIER`; handshake reporta `legal_framework` correto.

*Estimativa por task:* T01 1-2h · T02 2-3h · T03 2-3h · T04 2-3h · T05 2-3h. Total **9-14h, 3-5 sessões Code**.

**Sessões Chat dedicadas (antes de Fase 2 começar — ordem importa):**

1. **ADR-0007** (escopo MVP collection-only) com rationale real do mapa de tagueamento como motivação primária. Argumentos secundários (foundational data-flow position, signal density, compliance-domain breadth) podem complementar, não substituir. Estimativa: 45-90 min.

2. **POL-001** — cláusula sobre consentimento na coleta de dados pessoais. Critério: conteúdo suficiente para exercitar os quatro vereditos de `check_applicability` (compliant, violation_candidate, indeterminate, not_applicable) nos testes de T03. Trabalho jurídico-textual, não de Code. Estimativa: 1 sessão.

   Ordem deliberada: ADR-0007 antes de POL-001. ADR-0007 fixa que T03 só avalia `collection` — isso enquadra o escopo da cláusula que POL-001 vai precisar cobrir, evitando reautoria depois.

**Etapa 2 (Chat, após Milestone A completo):**
- Specs leves dos 5 subagentes (`docs/specs/subagents/<nome>.md`). Formato mais leve que canonical+compact dos MCPs — contrato comportamental + esboço de AgentDefinition (`mcp_servers`, `allowed-tools`) + decisões de prompt principais. 1-2 páginas por subagente.
- Discussão Matcher como evaluator iterativo (Rajasekaran-pattern). Decisão informada pelo aprendizado empírico de Milestone A. Possível materialização em ADR-0009 (a reservar) se a decisão for substantiva. Estimativa: 1-2 sessões Chat para o pacote completo.

**Etapa 4 (Chat, após Milestone B completo):**
- Spec leve do CI/CD (workflow YAML + posting via API) e do Reporter (`emit_report`). Pode ser meia-sessão. Documento único provável.

**Fase 2 Code (consumindo tasks.md):**

Numeração T01-T10 abaixo é **indicativa** — autorada definitivamente em #18 sob restrição de 8-12 tasks total da ADR-0008. Ranges podem deslocar conforme decomposição real.

- Milestone A — MCPs standalone validados (T01-T05, estimativa 4-5 sessões Code de 2-4h)
- Milestone B — multi-agente operacional (T06-T08, estimativa 3-4 sessões)
- Milestone C — CI/CD + benchmark + validação (T09-T10, estimativa 2-3 sessões)

**Sessão Code curta de cleanup editorial (oportunística, baixa prioridade):**
- Drift "LGPD" → "Proteção de Dados" em `architecture-overview`, `proposta-tcc2`
- Drift "trinque" → "trinca" cross-doc
- ADR-0001 §2 sync com estado real (pyenv-win → uv; FastMCP unpinned → 3.x). Apenas drift simbólico da prosa — substantive authority em ADR-0004; sweep editorial sem urgência.
- ADR-0001 D3/D4: drift `clause_id` "LGPD-Art-7-I" → `POL-NNN` (formato evoluiu; precisa amendment ou supersede)
- Token `store` → `storage` em [`docs/specs/policy-reader/compact.md`](docs/specs/policy-reader/compact.md) §5.3 exemplo violation_candidate (drift análogo ao `collect`/`collection` consertado em PR #23, mas em outra cláusula do exemplo)

**Adiar para sessão #20+:**
- Semântica de `last_revision` em `policy/policy.yaml`
- Semântica de `schema_version` no header dos YAMLs de vocabulário
- Validação cruzada per-cliente (vocabulary × Semgrep metadata) — só quando ADR de per-client rule set materializar
- Decisão sobre rule set per-cliente do `semgrep-runner`
- `mime_type` declaration em resources

---

### Decisões metodológicas calibradas nesta sessão

- **Granularidade de tasks calibrada para Opus 4.7** sob ADR-0008: 8-12 tasks médias (1-3h) em vez de 15-25 finas (30-60min), com referência empírica explícita a Rajasekaran 2026.
- **Estrutura por Milestones interna**: A (MCPs standalone), B (multi-agente), C (CI/CD + validação). Não recorte de entrega — Milestones são checkpoints empíricos dentro do escopo declarado em `proposta-tcc2 §3, §6`.
- **Calibração proporcional de Specify**: specs canonical+compact denso para MCP servers (decididas em sessões #07-#13); specs leves para subagentes (a redigir após Milestone A); spec curta para CI/CD (a redigir após Milestone B). Defensável academicamente como adaptação de SDD ao objeto.
- **Authoring de cláusulas emerge sob demanda**: POL-001 quando T03 pedir; POL-002+ quando task futura pedir. Pattern "cláusula nasce quando teste pede".
- **Authoring de cláusula é trabalho Chat, não Code**: provenance jurídico-textual, formação do autor.
- **Authoring de `tasks.md` também é Chat, não Code**: preserva independência do gate tripartite (ADR-0008 D3) — Code que consome tasks não pode ter sido o mesmo agente que as escreveu, sob risco de quebrar a separação no nível do plano.
- **Discussão Matcher-evaluator adiada**: decisão arquitetural amadurece com base empírica de Milestone A, não com especulação prévia.

---

### Sintomas operacionais observados nesta sessão (meta-aprendizado)

Vale registrar como padrão pra calibrar comportamento futuro:

- **Generator (Chat sem filesystem) introduz drift factual** que Code (com filesystem) pega: token `collection`/`coleta`, exemplos errados em RF-004, self-contradiction T05/T07 vs ADR-0008 D3, path errado de ADR-0003 no draft do handoff. Padrão recorrente; reforça empiricamente o D3 de ADR-0008 (revisão multi-instância) com evidência da própria sessão de calibração — o ADR previu o sintoma e o sintoma se manifestou na mesma sessão.
- **Disciplina de scope** retomada nesta sessão (cleanup do PR-23, pause-and-ask do PR-24) contrasta com sessão anterior onde Code expandiu scope silenciosamente.
- **Pause-and-ask funcionando** como gate de qualidade: 3 pauses nesta sessão (leftover POL-000 em ADR-0006; conflict de branch base em PR-24; race-condition de push do handoff vs merge dos PRs no GitHub UI). Todas resolveram bem com input curto seu.
- **Race-condition push vs merge:** durante o commit do próprio handoff, PR #23 e PR #24 foram mergeados via GitHub UI em paralelo. Push rejeitado, rebase com conflito, resolvido sobrescrevendo com versão atualizada que reflete merged-state. Padrão a antecipar: handoff que registra PRs pendentes pode ficar stale entre commit e push se o usuário operar em paralelo. Mitigação prática: redigir handoff como descrição de estado pós-merge, não pre-merge.

---

### Próximo passo recomendado

**Abertura da #18.** Quando você abrir, sugestão de prompt curto:

> Session #18 - Authoring de tasks.md sob ADR-0008 (as amended 2026-05-16). Ver handoff #17 + emenda registrada no learning-log #17 sub-seção "Refinamento intra-sessão". Foco: Milestone A detalhado (5 tasks + POL-001 pré), Milestones B/C como placeholders. Two-scope gate: task-level (function-specific pytest + Chat review) + milestone-level (manual exercise validando cada RF acceptance criterion declarada no milestone).

Posso abrir com explicação do two-scope gate emendado se você quiser revisar antes de redigirmos, ou ir direto pra redação se já estiver internalizado.

---

Sessão #17 produtiva e densa. Você sai com REQUIREMENTS estabelecido, duas convenções formalizadas em ADRs (linguagem + decomposição), provenance arquitetural intacta, e Code desbloqueado assim que tasks.md materializar na #18. Boa sessão.
