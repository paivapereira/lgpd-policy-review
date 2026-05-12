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

<!-- Próximos princípios extraídos das specs vêm aqui durante a migração (commits 4 e 5) -->
