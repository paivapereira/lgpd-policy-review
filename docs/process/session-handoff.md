# Session-handoff: autoria de matcher.md (#48)

**O que é:** primeira autoria da spec do Matcher (etapa 4 do pipeline). NÃO é
consolidação nem edit cirúrgico — é destilação de spec, padrão das specs
existentes (triager/detector/classifier/reporter).

**Confirmar no GATE 0 (estado de entrada — não assumir):**
- O PR da #47 foi mergeado? `git log` / `git status`. Se sim, os 3 fios
  (item-3 §5, sdk_tool_error_channel, sdk_output_format_complex) estão em `main`.
- Item 1 (`output_format`+`max_turns` em §3.2/§3.3) e item 4 EDIT (§6.3)
  permanecem NÃO aplicados ao fim da #47 — confirmar se alguma sessão
  intermediária os aplicou.

**Achados da #47 que são o ponto de partida (verificados verbatim salvo nota):**

*Output shape — já pinado, não inventar.*
- Matcher produz findings no shape de `reporter.md §2.2`: `file, line, snippet,
  rule_id, data_categories, operation_type, verdict, policy_clause_ref,
  requires_human_review?, policy_schema_version, policy_version, legal_framework`.
- ZERO `candidate_ref` no `reporter.md` (verificado) — bookkeeping interno do
  Matcher, não vai ao Report. Sem passo de re-expansão: o Matcher tem os campos
  do passthrough do Detector + structured_context do Classifier + seu verdict.
- Cardinalidade: um finding por par candidato-cláusula, `len ≥ candidates_count`
  (reporter §2.2 l.135). C1 do review ("não compõe") REENQUADRADO: compõe.

*Seleção de cláusula — especificada, ratificar não inventar.*
- `classifier.md:175` (forward-ref obrigatório): `check_applicability`/`get_clause`
  sobre `applies_to` derivado de `data_categories`. NÃO `find_clauses_by_law_article`
  (precisa de {lei,artigo} ausente do structured_context).
- Degradação graciosa: sem cláusula casada → `not_applicable`/`indeterminate`.
  Proibido Enum hard (anti-padrão removido do Reporter §4.8).
- COMPANION EDIT: `reporter.md:135` tem nota parentética citando a tool errada
  (`find_clauses_by_law_article`) — corrigir ao autorar (é nota ilustrativa, não
  contrato; o Reporter não pina mecanismo de seleção).

*Encoding output_format — constraint dura (DD-T16, verificado).*
- Os 4 verdicts (`compliant|violation_candidate|indeterminate|not_applicable`)
  = objeto enum-tag: `verdict: Literal[...]` + opcionais por verdict
  (`anyOf [T,null]`). NUNCA união discriminada (`oneOf` desliga a gramática
  silenciosamente: success + structured_output=None + JSON não-conforme).
  Evidência: `sdk_output_format_complex/RESULTS.md`.
- O `output_format`+`max_turns` da invocação do Matcher (§3.4 do coordinator) é
  o mesmo gap do item 1 (Detector/Classifier) — coordenar.

**Obrigações pré-registradas ao Matcher** (ledger do review + forward-refs):
postura Pydantic `extra` do structured_context consumido; `policy_clause_ref`
nos 4 verdicts incl. `not_applicable` (reporter:221/274); semântica de
`requires_human_review` (Reporter só propaga); `verification_scope` 3-campos
(reporter §3.2); quíntupla tools=[]+allowlist policy-reader + output_format/
max_turns (coordinator §3.4); trinca de provenance verbatim por finding.

**Pré-leitura verbatim:** `reporter.md §2.2/§3.2`, `classifier.md §2/§3/:175`,
`detector.md §2.1` (DetectorFinding passthrough), `coordinator.md §3.4`,
ADR-0005 (Resource-vs-Tool, Decision 9 sobre seleção de cláusula — verificar se
foi criada), `canonical.md` do policy-reader (signatures de `get_clause`/
`check_applicability`/`find_clauses_by_law_article`).

**Fora de escopo:** item 1, item 4 EDIT, A4, ADR-0013, reconciliação de
taxonomia — todos pendentes da #47, não puxar para a autoria do Matcher salvo
o que o Matcher genuinamente bloqueia.

**Limite do observado:** `reporter.md`/`classifier.md` lidos verbatim na #47;
`architecture-overview.md §5.5` ({candidate_ref}) NÃO relido — irrelevante para
o veredito (o vinculante é o input do Reporter), mas confirmar se quiser
zero-inferência. DD-T16 testado com stand-ins estruturais, não os modelos reais.