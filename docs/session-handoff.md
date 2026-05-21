# Session-handoff update — pós-sessão #28

Aplicação como **direct commit em main** sobre `docs/session-handoff.md` per ADR-0001 Decision 6 (allowlist de direct-commit para metadocumentos).

**Mensagem de commit sugerida:**

```
docs(session-handoff): close sessao #28 — Provisoes A+B mergeadas, T05 destravado

Bloco 1: marcar Provisao A (item B da lista de trilhas pos-#27) como fechada.
Bloco 2: criar sub-lista "Concluido em sessao #28" cobrindo fechamento de Provisao A + Provisao B juntos (reconciliando omissao do update pos-A).
Bloco 3: registrar debito residual de canonical examples drift (br-cpf-leak vs br-cpf bare).
Bloco 4: marcar Provisao B (item C) como fechada.
Bloco 5: marcar T07 (item F) como destravado.
Bloco 6: reorganizar lista "Resolver em sessoes subsequentes a #27" como "Resolver em sessoes subsequentes a #28" com T05 como proxima sessao Code.
Bloco 7: adicionar pendencia critica de sweep cross-doc das regras imutaveis antes de Milestone C arrancar.
```

ASCII-fied per padrão estabelecido na Provisão B (PS 5.1 + HEREDOC). Conteúdo dos blocos preserva acentos.

**Ordem de aplicação:** sequencial 1 → 7. Cada bloco é independente; aplicação parcial é segura (próxima sessão pode retomar onde parou).

---

## Bloco 1: Marcar Provisão A como fechada

**Locate:**

```markdown
B. **Provisão A — `chore/canonical-sync-C-semgrep-runner`** (Chat dedicada, ~3.5h total: ~2h Chat + ~1.5h Code). 4 commits internos: canonical sync Option B + compact sync cirúrgico + README pin Semgrep + ADR-0001 Decision 2 amendment in-place. **Bloqueia T06.**
```

**Substitute by:**

```markdown
B. **Provisão A — `chore/canonical-sync-C-semgrep-runner`.** **Fechada em sessão #28** (Chat dedicada de prep + três rounds de Code review independente + sessão Code de aplicação). PR squash-mergeada em main com 5 commits internos pré-squash: ADR-0001 Decision 2 amendment in-place (Presidio → Semgrep + pins formais FastMCP 3.2.4/Pydantic 2.13.4/MCP 1.27.1/Semgrep 1.163.0); canonical sync to Option B (§4.2 + §4.3 exemplos + §5 intro alinhada + §8.5 AS); compact sync cirúrgico (errorCodes 4→6, classes validation+system→business+system, retryability SCAN_TIMEOUT+SEMGREP_EXECUTION_FAILED, BINARY_UNAVAILABLE timing startup→per-call, wire format Option B, escalation pointers órfãos canonical §5.3/§5.4, §5.1 Errors list via Edit 2.7 cirúrgico emergente em aplicação); README Setup section + Stack realignment + Status estreitado; CLAUDE.md §Stack consolidação Static analysis + Brazilian recognizers (remove Presidio) + Pydantic 2.13.4 pin + FastMCP 3.2.4 pin. 18 edits aplicados; +202/-69 linhas vs main. T06 destravado.
```

---

## Bloco 2: Criar sub-lista "Concluído em sessão #28" cobrindo Provisão A + B juntos

**Nota.** O update do session-handoff pós-merge da Provisão A não foi aplicado pela sessão Code de A (omissão procedural identificada pelo Code review pré-aplicação da Provisão B em sessão #28). A criação desta sub-lista cobre os dois fechamentos juntos para reconciliar a omissão.

**Add** como nova sub-lista logo após a sub-lista "Concluído em sessão #27":

```markdown
**Concluído em sessão #28:**
- Provisão A — PR `chore/canonical-sync-C-semgrep-runner` squash-mergeada com 5 commits internos endereçando seis drifts catalogados em #27 (errorCodes count, classes, retryability, BINARY_UNAVAILABLE timing, wire format pre-amendment, ADR-0001 stack fundacional) + três drifts emergentes detectados em prep Chat de #28 (compact §5.3/§5.4 escalation pointers órfãos, exemplo timeout com `files_scanned_before_timeout` fora do schema canonical, atribuição cross-doc imprecisa em tasks.md linha 236) + um drift cross-doc detectado em Code review round 2 (CLAUDE.md §Stack ainda citando Presidio após ADR-0001 amendment apontar CLAUDE.md como autoridade do listing) + dois drifts laterais detectados em Code review round 3 (CLAUDE.md Pydantic 2.5+ vs uv.lock 2.13.4; FastMCP 3.x → 3.2.4) + um drift residual descoberto durante aplicação (compact §5.1 Errors list — Edit 2.7 cirúrgico). T06 destravado.
- Provisão B — PR `feat/fixtures/recognizers-pack-br` squash-mergeada (10 creates, single commit, 529 insertions) destravando T07. Pack BR em `tests/mcp_servers/semgrep_runner/fixtures/recognizers_pack_br/`: 6 snippets positivos (Latin square sobre 4 padrões × 6 identificadores) + 3 snippets negativos para AS-7 (version strings, regex validation literals, UUID-like constants) + README com AS coverage table + provenance algorítmica dos identificadores sintéticos + assimetrias deliberadas + ressalvas conhecidas. Latin square ratificado em Chat #28 pós-Code-review com base em três sinais coerentes de tasks.md (linha 248 explícita "seis snippets positivos (um por identificador)" + AS-1..AS-6 singulares + AS-9 idempotência); matriz completa 6×4 deferida como evolução pós-MVP. Identificadores sintéticos gerados via algoritmos públicos de check digit (CPF mod 11, CNPJ mod 11 com pesos duplos, CNH mod 11 com DSC, NIS mod 11, Título com regra especial SP/MG, CNS definitivo soma mod 11 = 0); provenance documentada no README do pack. CPF (`238.547.961-37`) e CNPJ (`47.861.932/0001-92`) sintéticos compartilhados entre snippet positivo e negativo de design intencional — exerce discriminação AST-aware por contexto sintático, não por string content.
- Defense candidates emergentes registrados (onze total, cumulativos com #27): (1) multi-round Code review independente em contexto clean como independent evaluator iterativo — cinco rodadas atingiram convergência empírica; (2) Code aplicador como verificador final irreduzível a reviewers anteriores — opera com arquivo INTEIRO em contexto vs fragmentos visíveis em prep; (3) validation criteria são código, não documentação acessória — gates auto-verificáveis merecem mesmo rigor de revisão cruzada que substitute_by; (4) handoff updates pós-merge são também código — esquecer de aplicar produz drift entre estado documental e estado real; Code review pre-apply da PR seguinte é mecanismo natural de detecção; (5) escalation pointers como dead links silenciosos — pointers `See <doc> §<X.Y>` quebram silenciosamente sob refactor da fonte; (6) lockfile como fonte autoritativa secundária para reconciliar ADRs de stack — reforço de #27; (7) nomes lógicos vs paths físicos — `[project].name` não implica path físico; inferência morfológica é fonte recorrente de erro; (8) scratchpad files + provenance pattern para edits cross-doc — quando Chat não tem o arquivo destino, fragmento transcrito + invariante semântico + Code validation como fallback; (9) regras imutáveis precisam de mecanismo de sync explícito — sweep dedicado é remediação ex-post; (10) fixture packs como contract codification — README é predicate sobre output, não documentação; (11) Latin square parcial como cobertura mínima contract-driven sob AS singulares.
- Correção da contagem de #27 no learning-log: seis drifts catalogados em #27 (cinco no contract surface + um fundacional), não cinco. Mais sete drifts adicionais detectados ao longo de #28 (três em prep Chat + três cross-doc em rounds 2-3 + um residual em aplicação + dois em pre-apply de Provisão B).
- Três rounds de Code review independente validaram cada delta da Provisão A antes de aplicação; uma rodada Code review pré-aplicação da Provisão B detectou e fechou omissão procedural do update do session-handoff de Provisão A + ratificou explicitamente decisão de Latin square + flagou drift residual em canonical examples (br-cpf-leak vs br-cpf bare).
```

---

## Bloco 3: Acrescentar débito residual de canonical examples sync

**Add** como nova entry na seção apropriada de pendências (sequencial a outras entries do mesmo tipo; pode ir junto com `docs/tasks-attribution-fix` se essa entry já existir):

```markdown
- **PR mecânica `docs/canonical-examples-sync`** (Code, ~10min). Drift detectado em Code review pré-aplicação da Provisão B (sessão #28): `docs/specs/semgrep-runner/canonical.md` linhas 122, 181, 194 usam rule_id sufixados semanticamente (`br-cpf-leak`, `br-cnpj-in-log`) nos exemplos, enquanto T07 e o fixture pack BR (Provisão B) fixam naming bare (`br-cpf`, `br-cnpj`, ...). Trocar sufixos pelos bare names nos três exemplos. Candidata a companion edit alongside o hedge §4.4 architecture-overview.md ("Regras Semgrep ou módulos equivalentes" → "Regras Semgrep em formato YAML") em PR mecânica única quando uma das duas docs for tocada por outro motivo. Não bloqueia T07; cosmético de provenance documental. Per ADR-0003 Decision 1, exemplos canonical são parte do contract surface — drift entre exemplos canonical e implementação real deveria ser sync-driven.
```

---

## Bloco 4: Marcar Provisão B como fechada

**Locate:**

```markdown
C. **Provisão B — `feat/fixtures/recognizers-pack-br`** (Chat dedicada, ~2-2.5h total). Seis snippets positivos + negativos para os identificadores BR + README com AS coverage. Não bloqueia T05 nem T06. **Bloqueia T07.**
```

**Substitute by:**

```markdown
C. **Provisão B — `feat/fixtures/recognizers-pack-br`.** **Fechada em sessão #28** (Chat dedicada de prep + uma rodada Code review pré-aplicação + sessão Code de aplicação). PR squash-mergeada em main com single commit consolidando 10 creates: seis snippets positivos cobrindo identificadores brasileiros canônicos (CPF, CNPJ, CNH, NIS/PIS, Título de Eleitor, CNS-saúde) via Latin square sobre quatro padrões sintáticos (parameter naming, dict key access, attribute assignment, log payload structured); três snippets negativos para AS-7 (version strings em formato CPF-like, regex validation literals, UUID-like constants); README com AS coverage table + provenance algorítmica dos identificadores sintéticos + assimetrias deliberadas + ressalvas conhecidas. T07 destravado.
```

---

## Bloco 5: Marcar T07 como destravado

**Locate:**

```markdown
F. **T07 (Code, ~2-2.5h)** — six recognizers brasileiros + validação contra fixture pack BR. Destrava após E + C.
```

**Substitute by:**

```markdown
F. **T07 (Code, ~2-2.5h)** — six recognizers brasileiros + validação contra fixture pack BR. **Pré-requisito C satisfeito** (Provisão B mergeada em #28). Destrava após T06 fechar gate task-level.
```

---

## Bloco 6: Reorganizar lista de trilhas como "Resolver em sessões subsequentes a #28" com T05 como próxima sessão Code

**Locate:**

```markdown
**Resolver em sessões subsequentes a #27 (ordem natural — A precede E/F/G; B pode rodar antes ou em paralelo a C; D destrava após A):**

A. **PR mecânica `docs/tasks-milestone-b-decomposition`** (Code, ~30-40min). Aplica 4 blocos do diff aplicável de #27 + 2 fixes do Chat review. Não bloqueia T05 mas cristaliza referência.

B. **Provisão A — `chore/canonical-sync-C-semgrep-runner`.** **Fechada em sessão #28** (Chat dedicada de prep + três rounds de Code review independente + sessão Code de aplicação). PR squash-mergeada em main com 5 commits internos pré-squash: ADR-0001 Decision 2 amendment in-place (Presidio → Semgrep + pins formais FastMCP 3.2.4/Pydantic 2.13.4/MCP 1.27.1/Semgrep 1.163.0); canonical sync to Option B (§4.2 + §4.3 exemplos + §5 intro alinhada + §8.5 AS); compact sync cirúrgico (errorCodes 4→6, classes validation+system→business+system, retryability SCAN_TIMEOUT+SEMGREP_EXECUTION_FAILED, BINARY_UNAVAILABLE timing startup→per-call, wire format Option B, escalation pointers órfãos canonical §5.3/§5.4, §5.1 Errors list via Edit 2.7 cirúrgico emergente em aplicação); README Setup section + Stack realignment + Status estreitado; CLAUDE.md §Stack consolidação Static analysis + Brazilian recognizers (remove Presidio) + Pydantic 2.13.4 pin + FastMCP 3.2.4 pin. 18 edits aplicados; +202/-69 linhas vs main. T06 destravado.

C. **Provisão B — `feat/fixtures/recognizers-pack-br`.** **Fechada em sessão #28** (Chat dedicada de prep + uma rodada Code review pré-aplicação + sessão Code de aplicação). PR squash-mergeada em main com single commit consolidando 10 creates: seis snippets positivos cobrindo identificadores brasileiros canônicos (CPF, CNPJ, CNH, NIS/PIS, Título de Eleitor, CNS-saúde) via Latin square sobre quatro padrões sintáticos (parameter naming, dict key access, attribute assignment, log payload structured); três snippets negativos para AS-7 (version strings em formato CPF-like, regex validation literals, UUID-like constants); README com AS coverage table + provenance algorítmica dos identificadores sintéticos + assimetrias deliberadas + ressalvas conhecidas. T07 destravado.

D. **T05 (Code, ~1.5-2h)** — server skeleton + rule set loader. Destrava após A.

E. **T06 (Code, ~3h)** — `scan_diff` completo: subprocess + 6 errorCodes + wire format Option B. **Pré-requisitos satisfeitos** (D = T05 destravado após PR mecânica de tasks.md em #27; B = Provisão A mergeada em #28). Pronta para implementação assim que T05 fechar gate task-level.

F. **T07 (Code, ~2-2.5h)** — six recognizers brasileiros + validação contra fixture pack BR. **Pré-requisito C satisfeito** (Provisão B mergeada em #28). Destrava após T06 fechar gate task-level.

G. **Gate milestone-level Milestone B** (Chat dedicada, ~1h). Manual exercise via MCP Inspector contra RF-001 + RF-002 sobre série de seis PRs sintéticos. Destrava após T05-T07 fecharem gate task-level. Pré-requisito procedural: binário `semgrep==1.163.0` instalado via `uv tool install` no ambiente do gate.
```

**Substitute by:**

```markdown
**Resolver em sessões subsequentes a #28 (ordem natural — T05 → T06 → T07 → gate milestone-level; T07 e T05 paralelizáveis após T05 fechar):**

D. **T05 — server skeleton + rule set loader** (Code, ~1.5-2h). **Próxima sessão Code.** Pré-requisitos satisfeitos:
   - Branch base `main` limpa pós-merge de Provisão A + Provisão B.
   - Canonical do `semgrep-runner` em Option B (Provisão A mergeada em #28).
   - ADR-0010 (Semgrep installation strategy) ratificado; binário `semgrep==1.163.0` disponível no ambiente local via `uv tool install`.
   - `docs/tasks.md` linhas 258-296 detalha AS-1 a AS-9 + Files previstos + Acceptance scenarios + Gate task-level.
   - Pattern mirror estrutural de `src/mcp_servers/policy_reader/` (loader, server, models) disponível como referência.
   - Stub de tool `scan_diff` retornando envelope `NOT_IMPLEMENTED` em sucesso per AS-8 de T05 — desaparece em T06.
   - Per canonical §8.6, ausência do binário `semgrep` no PATH NÃO aborta o startup; verificação per-call vive em T06 (não em T05).

E. **T06 — `scan_diff` completo** (Code, ~3h). Subprocess + 6 errorCodes + wire format Option B per canonical §5 + canonical §8.6 (per-call binary check). Destrava após T05 fechar gate task-level. Pré-requisito Provisão A satisfeito.

F. **T07 — six recognizers brasileiros** (Code, ~2-2.5h). Six rules Semgrep YAML em `mcp_servers/semgrep_runner/rules/` + validação contra fixture pack BR. Destrava após T06 fechar gate task-level. Pré-requisito Provisão B satisfeito.

G. **Gate milestone-level Milestone B** (Chat dedicada, ~1h). Manual exercise via MCP Inspector contra RF-001 + RF-002 sobre série de seis PRs sintéticos. Destrava após T05-T07 fecharem gate task-level. Pré-requisito procedural: binário `semgrep==1.163.0` instalado via `uv tool install` no ambiente do gate.

**Débitos residuais não-bloqueantes (PRs mecânicas Code; podem rodar a qualquer momento ou consolidar em PR única quando uma docs for tocada por outro motivo):**

- **PR mecânica `docs/tasks-attribution-fix`** (Code, ~5min). Detectada em #28: tasks.md linha 236 atribuição imprecisa ("§6 da spec" cita texto que reside apenas no compact, não no canonical). Mover o item para a descrição do "compact sync cirúrgico" ou apagar (já endereçado em Provisão A).
- **PR mecânica `docs/canonical-examples-sync`** (Code, ~10min). Detectada em Code review pré-aplicação da Provisão B (#28): canonical.md linhas 122, 181, 194 usam `br-cpf-leak`, `br-cnpj-in-log` (sufixados), divergindo do naming bare fixado por T07 e pelo fixture pack BR. Candidata a companion edit alongside o hedge §4.4 architecture-overview.md em PR consolidada (~15min total).
- **Verificação de canonical §5.1 título contra `_template.md`** (Code, ~5min). Pendência herdada de tasks.md linha 236.
- **(Opcional) Convenção ASCII-fied commit message em PS 5.1.** Detectada em #28 Provisão B aplicação: pattern admitido para evitar fricção HEREDOC com acentos; conteúdo dos arquivos preserva acentuação per ADR-0001 Decision 3. Candidata a item curto em `.claude/rules/windows-tooling.md`.
```

---

## Bloco 7: Adicionar pendência crítica de sweep das regras imutáveis antes de Milestone C

**Add** como nova entry na seção apropriada de pendências (pode ir alongside o débito de tasks-attribution-fix ou criar nova subseção "Resolver antes de Milestone C arrancar"):

```markdown
**Resolver antes de Milestone C arrancar (pendência arquitetural crítica):**

- **Sweep cross-doc das regras imutáveis** (Chat dedicada, estimativa ~1.5h). Reconciliar drift entre ADR-0001 Decision 4 (três regras: human escalation on legal-policy conflict, citation of stable clause IDs `LGPD-Art-7-I`, schema-versioned policy compatibility) e CLAUDE.md §"Immutable domain rules" (três regras distintas: no fabricated certainty 4 verdicts, citation of stable clause IDs `POL-` prefix, two-axis policy versioning). Detectado em sessão #28 via Code review round 3 da Provisão A (R3). Reconciliação substantiva: deliberar qual conjunto é canônico (ou se houve bifurcação legítima entre "regras de decisão" e "regras de output"), atualizar o doc drifted, possivelmente amendment ADR-0001 Decision 4 in-place espelhando pattern de Decision 2 amendment 2026-05-21. **Crítica antes de Milestone C arrancar — regras imutáveis governam subagent behavior em Milestone C.** Defense candidate emergente: "regras imutáveis precisam de mecanismo de sync explícito ou bifurcam silenciosamente sob evolução paralela dos dois documentos".
```

---

## Validação pós-aplicação dos 7 blocos

Após aplicar todos os 7 blocos como direct commit em main, rodar grep checks de sanidade:

```powershell
# Bloco 1: Provisão A marcada como fechada
git grep -n "Fechada em sessão #28" docs/session-handoff.md  # esperado: >= 2 matches (Bloco 1 + Bloco 4)

# Bloco 2: sub-lista "Concluído em sessão #28" criada
git grep -n "Concluído em sessão #28:" docs/session-handoff.md  # esperado: 1 match
git grep -nE "5 commits internos|10 creates" docs/session-handoff.md  # esperado: >= 2 matches

# Bloco 3: débito canonical-examples-sync registrado
git grep -n "docs/canonical-examples-sync" docs/session-handoff.md  # esperado: 1 match

# Bloco 4: Provisão B marcada como fechada (cobrindo seção)
git grep -n "feat/fixtures/recognizers-pack-br" docs/session-handoff.md  # esperado: >= 2 matches (mantida em vários lugares por citação)

# Bloco 5: T07 com pré-requisito C marcado
git grep -nE "Pré-requisito C satisfeito|T07 destravado" docs/session-handoff.md  # esperado: >= 2 matches

# Bloco 6: T05 como próxima sessão Code
git grep -n "Próxima sessão Code" docs/session-handoff.md  # esperado: 1 match
git grep -n "Resolver em sessões subsequentes a #28" docs/session-handoff.md  # esperado: 1 match

# Bloco 7: sweep das regras imutáveis registrado
git grep -n "Sweep cross-doc das regras imutáveis" docs/session-handoff.md  # esperado: 1 match
git grep -n "antes de Milestone C arrancar" docs/session-handoff.md  # esperado: 1 match

# Sanity: ausência de referências obsoletas
git grep -n "Resolver em sessões subsequentes a #27" docs/session-handoff.md  # esperado: 0 matches (substituído por #28 em Bloco 6)
```

Se algum grep retornar abaixo do esperado, investigar e reaplicar o bloco correspondente.

---

## Fim do documento

João aplica os 7 blocos como direct commit em main. Após aplicação, próxima sessão Code arranca em T05 com contexto completo no handoff — Code abre o handoff, lê item D, e tem todos os pré-requisitos satisfeitos enumerados explicitamente.