# session-handoff — pós #45 (Classifier spec mergeable)

## Estado
- classifier.md v0.1.0 mergeable (3 rodadas de review fechadas). Fica pendente de merge ATRÁS do PR de policy://examples.
- Nada de src/ tocado nesta sessão — só spec.

## Próximo trabalho: PR autônomo policy://examples (prereq de merge da Classifier)
Ler verbatim ANTES de autorar (não reconstruir):
- docs/specs/policy-reader/canonical.md (inteiro — hoje 3 resources: catalog, schema-version, vocabularies)
- policy/SCHEMA.md §2 (layout da camada jurisdicional)
- docs/adr/0005-multi-client-policy-architecture.md (estado das Decisões 1-8)
- policy/vocabularies/<framework>/ do POL-000 (tokens reais p/ o seed)

Edits do PR (§10.5(7-8) da classifier.md):
1. policy-reader/canonical.md §3 — 4º resource `policy://examples`; §3.3 — Classifier como consumidor autorizado.
2. ADR-0005 — **Decisão 9** "examples as layer-1 resource, by analogy to D8" (D8 decide regras; examples é caso novo).
3. policy/SCHEMA.md §2 — `examples/<framework>/` irmão de `vocabularies/<framework>/` na camada jurisdicional.
4. Seed: `policy/examples/LGPD/` com **≥2 positivos** — os dois removidos do classifier.md §5.1 rodada 2 (caso collection; caso storage+transformação). **Tokens VERIFICADOS contra o vocabulário POL-000, não inferidos.** Shape provisório: {snippet, surrounding_context, expected_structured_context}.
5. Semântica de erro: missing/empty tolerado (não falha boot) — distinto de vocabularies.

## Aberto, fora deste PR
- DD-T05 (changed_paths): sessão coordinator/Triager. Recomendação registrada (manter Glob-by-subagent).
- Após policy://examples mergear: Classifier ramifica do main → Fase 0 smoke (gate-of-gates) → impl. Migra de Chat para Code.

## Atenção (lição #11/#12)
Confirmar nº da work-session contra o contador (learning-log), não memória, antes de commitar.