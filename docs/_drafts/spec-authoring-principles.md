# Spec-authoring principles (draft)

**Status:** Draft. Conteúdo em consolidação durante a sessão #11 — dumps de meta-redação extraídos das specs `policy-reader` e `semgrep-runner` durante migração para estrutura dual canonical+compact.

**Consolidação final:** prevista para sessão futura, após algumas cláusulas substantivas exercitarem o SCHEMA e os princípios de redação se estabilizarem (handoff #10).

## Princípios extraídos

### Resource vs Tool — discriminação pela leitura cognitiva

**Âncora externa:** TS 2.2 do exam guide *Claude Certified Architect — Foundations* — "resources for catalogs, tools for actions".

**Forma operacional pela negativa:** Resource catalogável só existe quando há leitura cognitiva do conteúdo pelo agente consumidor. Se a invocação produz um resultado novo a cada chamada (action sobre input), o vetor é tool. Se o conteúdo existe independentemente da invocação e é navegável (catalog), o vetor é resource.

**Aplicação no projeto.**

- `policy-reader` expõe Política como **ambos**: `policy://catalog` (resource — vocabulário e cláusulas existem antes de qualquer leitura) e `get_clause` / `find_clauses_by_law_article` / `check_applicability` (tools — operações sobre cláusulas).
- `semgrep-runner` expõe **só tools**: `scan_diff` é ação, não há findings, regras compiladas ou outro conteúdo pré-existente a catalogar como resource.

A assimetria entre os dois servers é caso-teste do princípio.

### Schema fora, comportamento dentro

**Origem:** `docs/specs/policy-reader/canonical.md` §4.1 (estado pré-Commit 4, linha 143).

**Princípio.** Quando o componente serve um artefato de domínio que tem schema canônico próprio, a spec do componente **referencia** a estrutura do schema, **não duplica**. Estrutura interna de campos (formato exato, vocabulário fechado, regras de derivação) vive no schema canônico do artefato; spec do componente descreve apenas comportamento contratual perante a estrutura.

**Aplicação no projeto.**

- `policy-reader` spec referencia `policy/SCHEMA.md` para estrutura de `article_source`, vocabulário de `applicability_scope`, enum de `operation`, regra de formato de `clause_id`. Não duplica nenhum desses.
- `semgrep-runner` não tem schema externo análogo a `policy/SCHEMA.md` no MVP — case-test ausente. Pode emergir se o componente vier a expor `findings` segundo schema canônico de regras Semgrep.

### Spec descreve o quê, não como

**Origem:** `docs/specs/policy-reader/canonical.md` §7.1 (estado pré-Commit 4, linha 591).

**Princípio.** Spec do componente descreve **contrato observável**: o que tools recebem, o que retornam, em que condições erram. Spec **não** prescreve **mecanismo de implementação**: algoritmo interno, escolha entre regra determinística vs LLM-call vs híbrido, estratégia de cache, formato de storage. Implementação tem liberdade para evoluir mecanismo sem mudar contrato; mudança de mecanismo não é mudança de spec.

**Aplicação no projeto.**

- `policy-reader.check_applicability` retorna veredito estruturado; como o componente decide o veredito (regra determinística sobre `structured_context`, LLM-call interno, híbrido) é decisão de implementação livre.
- Campos de prosa em retornos (`evidence`, `verification_target`) são gerados pelo componente — mecanismo (template, LLM, híbrido) também é livre.

<!-- Próximos princípios extraídos das specs vêm aqui durante a migração (commits 4 e 5) -->
