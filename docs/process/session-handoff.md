# session-handoff — consolidação do coordinator (pré-Matcher)

> Sessão dedicada, inversão deliberada da sequência do handoff pós-#45 (Detector → ~~Matcher~~ → coordinator-flesh): insere-se uma **consolidação parcial do coordinator antes da Matcher**, para drenar o débito de companion-edits acumulado por três specs de subagente (Triager #?, Classifier #45, Detector #46) antes que a Matcher adicione uma quarta rodada. Registrada como inversão consciente, não desvio silencioso. NÃO é o coordinator-flesh completo — é drenagem de débito pré-registrado + validação de uma suposição cross-spec.

## Por que esta sessão existe (diagnóstico da #46)
O skeleton do `coordinator.md` está atrasado em relação às specs de subagente. Dois débitos viraram **padrão** (não pendência isolada):
1. `output_format` + `max_turns` ausentes do skeleton §3.3 — flagado por Classifier (#45) **e** Detector (#46). Segunda ocorrência.
2. Detecção de refusal (`stop_reason="refusal"` dentro de `subtype="success"`) deferida ao coordinator por **três** specs sobre uma suposição não-validada: acesso direto a `stop_reason` na `ResultMessage` pode ser TypeScript-only no Agent SDK (verificação externa #46); Python pode exigir varredura de stream events.
O coordinator é o ponto de convergência de débito do pattern coordinator-subagent — propriedade estrutural, não descuido. Drenar antes da Matcher evita herdar 4 subagentes de reconciliação de uma vez no flesh.

## Escopo travado (o que ESTA sessão faz)
Drenagem dos companion-edits pré-registrados pelos três subagentes + a validação de refusal. **Não** abre decisões de design novas do coordinator (orquestração, gates milestone-level, etc. — isso é o flesh, fica depois da Matcher).

1. **Declarar `output_format` + `max_turns` no skeleton §3.3** para os três subagentes Branch B (Triager, Classifier, Detector). Reconstruir verbatim o valor de cada (Triager e Classifier dos respectivos specs; Detector = `DetectorOutput`, `max_turns` 30 provisional **se** ratificado — ver `⚠ DECISÃO` em detector.md §1.4).
2. **Reconciliar signatures dos `build_*_prompt`** já existentes no skeleton com os inputs notacionais das specs. Confirmado em #46: `build_detector_prompt(pr_metadata, triager_output)` existe; confirmar análogos do Triager/Classifier e que `pr_metadata` carrega `base_ref`/`head_ref`.
3. **Decidir taxonomia de exceções de tool-error.** `DetectorScanFailed` (proposto em detector.md §6.2) vs reuso de `run_outcome="error"`. Decisão afeta como erro non-retryable de `scan_diff` (e, futuramente, de qualquer tool de subagente) propaga. Load-bearing — não despachar rápido.
4. **Validar a suposição de refusal em Python via smoke-test.** Construir o canário: o coordinator em Python consegue ler `stop_reason="refusal"` direto da `ResultMessage`, ou precisa varrer `message_delta`/stream events? Decide o mecanismo de discriminação de refusal que **três** specs deferem ao coordinator. "Build the canary that screams first" (precedente T01 wire-shape, Gate 6).
5. **(Se couber) teste de paridade de passthrough Detector↔Classifier.** Asserção de que os 5 campos do `DetectorFinding` batem posicionalmente no `ClassifiedCandidate` — faz o drop silencioso de campo falhar alto (G2). Pode ser deferido a T11+ se a sessão encher.

## Fora de escopo (NÃO tocar)
- Coordinator-flesh completo (orquestração, gate milestone-level, schema "Report vazio").
- Matcher spec (próxima sessão fresca, pós-consolidação).
- ADR-0012 retroativo / `chore/sync-adr-references` (housekeeping separado).
- Reporter scan-provenance (DD-D3) — é companion edit do PR `feat/detector-spec`, não desta consolidação; mas confirmar que não colide.

## Ler verbatim ANTES de editar (não reconstruir de memória)
- `coordinator.md` §3.2, §3.3 (skeletons dos subagentes; signatures dos `build_*_prompt`; taxonomia de exceções atual; loci de stream-inspection `ReportNotEmitted` + captura de payload — por **âncora semântica**, não linha, que drifta)
- `triager.md` §1.4, §4, §6.2/§6.3 (output_format, max_turns, classes de erro)
- `classifier.md` §1.4, §4, §6.2/§6.3 (idem; e §6.3 para o subtype `error_max_structured_output_retries`)
- `detector.md` §1.4, §4, §6.2/§6.3 (output_format `DetectorOutput`, max_turns provisional, `DetectorScanFailed`, propagação de erro do `scan_diff`)
- `reporter.md` §6 (Branch A — contraste; taxonomia de errorCodes intra-handler)
- ADR-0002 (Option B, convenções MCP — contexto da propagação de erro de tool)
- Doc oficial Agent SDK sobre `stop_reason` / `ResultMessage` em Python (item 4 — verificar corrente, cutoff Jan/2026)

## Estado de entrada (verificar contra repo, não assumir)
- `detector.md` v0.1.0 mergeable; PR `feat/detector-spec` + companion edits ao coordinator **podem já ter sido aplicados** ou não. Confirmar se os edits 1-3 do handoff pós-#46 já entraram (se sim, parte do escopo desta sessão já está feito).
- `classifier.md` v0.1.0: confirmar se mergeou em main.
- Contador de work-session: confirmar o nº desta sessão contra `docs/process/learning-log.md` (lição #11/#12), não memória.

## Saída esperada
- Edits ao `coordinator.md` §3.3 (output_formats + max_turns dos três; signatures reconciliadas) — prep Chat + execução Code.
- Decisão registrada da taxonomia de exceções (ADR ou nota no coordinator).
- Resultado do smoke-test de refusal-Python → mecanismo de discriminação fixado, com companion note às três specs se o mecanismo diferir do que elas assumem.
- learning-log entry + handoff para a sessão da Matcher.