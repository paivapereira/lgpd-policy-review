# Handoff #32 → #33

## Estado atual (pós-T06 mergeado)

PR #56 mergeado: `feat(semgrep-runner): T06 — scan_diff completo (subprocess + X1 mapping + Option B)`. 83 tests passing (53 policy_reader baseline + 9 test_bootstrap pós-cleanup + 21 test_scan_diff). Ruff All checks passed. Mypy Success em 8 source files (escopo `src/mcp_servers/semgrep_runner/`).

Milestone B (semgrep-runner core) substantialmente avançado: T05 (skeleton + rule loader + stub) e T06 (`scan_diff` completo) ambos em main. Próxima task da Milestone B é T07 (Detector subagent) — primeiro consumer real de `scan_diff` via FastMCP Client.

## DDs implementadas em T06 (22 novas + 1 invariante canonical §4.2)

DD-T06-1 a DD-T06-21 ratificadas em prompt v5.1 antes de implementação. DD-T06-22 e DD-T06-23 emergiram como implementation surprises:

- **DD-T06-22** (ratificada em GATE 1 pós-pre-flight): parse stdout JSON best-effort em ramo de erro para enrichment de `details.stderr_excerpt`; failure de parse = fallback transparente para stderr cru.
- **DD-T06-23** (ratificada em halt de 3.A): snippet derivado por filesystem read em `_read_snippet(location, repo_root)` porque Semgrep OSS sem `SEMGREP_APP_TOKEN` emite `extra.lines = "requires login"` em vez de código real; canonical §8 veta token.

## Decisões load-bearing que merecem persistir como contexto

1. **Exit code mapping X1 (ratificado em GATE 1).** Exits 4 e 5 documentados em CLI reference são empíricamente inalcançáveis em Semgrep 1.163.0; removidos do mapping per CLAUDE.md "no defensive code". Pre-flight 3.E confirmou: "rule parse error" cai em exit 2, "unparseable YAML" cai em exit 7 (colapsado em wrapper "invalid configuration"). Mapping final: `0→success; 7,8→INVALID_RULE_SET; 2,3,13,99,outros→SEMGREP_EXECUTION_FAILED`.

2. **DD-T06-6 refinada — shallow signal em JSON, não stderr.** Pre-flight 3.G descobriu que Semgrep em shallow repo com `--baseline-commit` produz `errors[].message: "Exception in BaselineHandler initialization: ..."` em stdout JSON, com stderr vazio. Lazy layer DD-T06-6 inspeciona `errors[].message` via 4 substrings (`BaselineHandler initialization`, `shallow`, `merge-base`, `cannot find common ancestor`).

3. **6 companion edits cross-doc aplicados.** Canonical §4.2 caller invariants; §5.3 quinto caso JSON errors[]; §5.4 INVALID_RULE_SET expansão (exits 7|8) + SEMGREP_EXECUTION_FAILED clarificação + footnote¹ com pin de versão; §8.6 exit code mapping subsection; README git ≥ 2.30; tasks.md §T06 AS-13 psutil → `_pid_alive_windows`. Bundling justificado como "novas decisões contratuais, não pre-existing debt".

4. **AS-7 namespace collision T05 vs T06 fechado.** T05's AS-7 (description byte-identity) preservado em `test_bootstrap.py`; T06's AS-7 (`SEMGREP_BINARY_UNAVAILABLE` per-call) em `test_scan_diff.py`. Naming convention `test_as7_*` (sem underscore extra) consistente com T05.

5. **Splittability T06 rejeitada com justificativa empírica.** Excedeu janela ADR-0008 (~3-4h vs 1-3h prescrito) mas split em T06a/T06b violaria coverage de AS-11 (wire format Option B precisa happy path + ≥1 error path), duplicaria mock infra (AS-6/AS-7/AS-13 compartilham), e descartaria pre-flight 3.H (subprocess cleanup só faz sentido com Fase 3 tocando subprocess). Awareness > tacit assumption per §11 do prompt v5.1.

## Lessons metodológicas (defense candidate forte para Capítulo de Método)

**Convergência multi-round NÃO-monotônica em quantidade de catches; severidade conceitual decai monotonicamente.** Trajetória v1→v5.1: v1 (4 bloqueadores estruturais) → v2 (4 bloqueadores Windows-factual) → v3 (0 bloqueadores; mas C1 reframe — DD-T06-21 reinventava canonical §4.2 line 148) → v4 (1 bloqueador colateral AS-7 namespace, emergiu como subproduto de fix v3) → v5 (cirúrgicos) → v5.1 (cosméticos). Triangulação real requer ≥1 round verificacional após cada round de fix substancial. Review coerência interna ratifica mas pode mascarar reinvenção de contrato; review verificacional (que abre arquivos reais do projeto) é complementar necessário, não redundante.

**Verification-before-inference aplicada recursivamente.** Ao código (pre-flight 3.A-3.H verifica empíricamente); ao prompt (cada DD pergunta "isto já está em canonical/spec/tasks?"); à interpretação de catches anteriores (revisitar S2 v3 com leitura literal evitaria erro mecânico em v4); aos companion edits (Fase 2 cita texto literal antes de propor diff).

**Pre-flight ambicioso paga dividendo iterativo.** 3 surfaces empíricas substantivas que toda deliberação Chat v1→v5.1 não pegou: exits 4/5 unreachable (3.E); shallow signal em JSON (3.G); snippet "requires login" (3.A). Pattern relevante para `.claude/rules/review-patterns.md` amendment: anomalias de pre-flight devem ser cross-checked contra spec **exemplo** (não só spec contract) antes de classificar como "não-bloqueante" — gap empírico↔contratual emerge ao mapear, não ao verificar isoladamente.

**GATE 1 não é único — gates intermediários por sub-fase 3.A→3.J capturam surpresas em camadas diferentes.** DD-T06-22 emergiu em pre-flight + GATE 1; DD-T06-23 emergiu em halt de 3.A. Múltiplos gates absorvem iterativamente sem comprometer trajetória.

## Conceitos de prova exercitados em T06

- **D1** (Agentic Architecture): GATE 1 + Fase 3 faseada por classe de errorCode + halt-and-escalate em gate intermediário aplicado a feature task pela primeira vez.
- **D2** (Tool Design & MCP): errorCode discrimination via Pydantic Literal; 8-exit-code → 2-errorCode mapping; anchor `isRetryable` byte-by-byte vs canonical §5.4; wire format Option B universal.
- **D4** (Prompt Engineering): iterative refinement v1→v5.1 com multi-instance review + cross-check externo; Pydantic gating do Semgrep JSON com validation-retry implícita.
- **D5** (Context Management): subprocess error propagation com cleanup empírico; provenance via JSON top-level version; verification-before-inference recursive.

## Próximo passo: T07 — Detector subagent

Detector é o primeiro **consumer real** de `scan_diff` via FastMCP Client. Resolve empíricamente:

1. **`repo_root` como parâmetro explícito vs cwd implícito** (DD-T06-3 + DD-T06-19). T07 expõe se contract implícito é viável ou se Provisão A precisa amendment para inputSchema explícito (evolution candidate em canonical §7).
2. **Findings ordering cross-component.** Anchor T06 exercita invariante via `tools.scan_diff` direto; T07 consome via Client e processa sequencialmente — segunda-line de validação que ordering sobrevive serialização Option B.
3. **Wire format Option B em consumer multi-tool.** T07 invoca `policy_reader.check_applicability` + `policy_reader.get_clause` + `semgrep_runner.scan_diff` — primeiro teste real de Option B cross-server, com Detector discriminando sucesso vs erro via `errorCode` presence.
4. **Caso real de `errors[]` non-empty em exit 0?** DD-T06-20 ignora; T07 pode revelar caso onde rules dropped silenciosamente afeta classificação. Se emergir, promover Opção B (escalation threshold) ou Opção C (campo `warnings` em scan_metadata) per canonical §7.

Estimativa T07: 2-3h se thin orchestrator; 4-5h se lógica LGPD applicability scoring for não-trivial. Pre-flight T07 vai verificar shape de FastMCP Client multi-server em ambiente local antes de implementação.

**Sugestão de início para sessão #33:** começar com leitura de `docs/tasks.md` §T07 + canonical do Detector (se existir; senão, especificar Detector como spec nova em ADR/canonical antes de implementar — pattern Provisão A).

## Housekeeping debt aberto

Issue separada para mypy fixtures `tests/mcp_servers/semgrep_runner/fixtures/recognizers_pack_br/br_nis_log_payload.py` (3 errors pre-existentes de PR #52 T07 prep). Opções: (a) `pyproject.toml` exclude module; (b) `# type: ignore[call-arg]` inline nas linhas. Out-of-scope T06.

## Artefatos chave

- PR #56 (mergeado): T06 scan_diff completo.
- `prompt-t06-v5.1.md`: prompt final usado em implementação. Appendix de 25 catches.
- Trajetória completa Chat #32: `2026-05-23-01-39-38-session-32-prep-t06-v3.txt` (transcript) cobrindo v1→v5.1 + Fase 1 pre-flight + Fase 2 plan + DD-T06-23 halt + ratificação implementação.
- Learning log entry: `learning-log-T06.md` para append em `docs/learning-log.md`.

## Status da prova (Claude Certified Architect — Foundations)

T06 exercitou conceitos dos 4 domínios principais (D1 27% + D2 18% + D4 20% + D5 15% = 80% do peso da prova). D3 (Claude Code Configuration & Workflows, 20%) é exercitado continuamente pelo uso do projeto mas não tem implementação direta em T06; será exercitado em CI/CD setup (Milestone D) com `-p` + `--output-format json` + integração com workflow.

Trajetória prep T06 com 5 rounds de iteração + halt-and-escalate em GATE 1 e gate 3.A é defense candidate forte para Capítulo de Método. Documentar como pattern auditável.

## Próximo halt esperado em #33

Pre-flight T07 ou plan mode T07. Sessão #32 oficialmente encerrada.