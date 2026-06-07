# Session handoff — relatorio fechado no texto; execution-model mergeado; 2 follow-ups spun-out

> Template-overwrite, nao patch cumulativo. Tratar como hipotese a verificar contra o repo (git
> log, leitura de arquivo). Primeira acao de sessao Code: confirmar git state. `relatorio-qa.md`
> segue como inventario de debitos do relatorio; em divergencia, re-ler o arquivo.

## Estado do repo (informado no fim da sessao)

Em `main`, arvore limpa, em sincronia com `origin/main`. Merges recentes: relatorio (#118-#119) e
`docs/execution-model.md` (#120, `f95d54b`). Branches de trabalho deletadas/podadas.

## Onde estamos

Duas frentes fecharam nesta sessao:

1. **Texto do relatorio — FECHADO.** Todos os eixos de consistencia resolvidos e verificados:
   novidade reposicionada (combinacao, nao primazia; reconhece PrivGuard/Sen/Wang), contribuicao
   alinhada do resumo ao §3, destino dos achados (relatorio do GitHub Actions, sem inline),
   numeracao de etapas 1-5, contagem de testes 309/307, eixos (versionamento dois semver + framework
   como identidade), tempo verbal de relatorio final. Nao ha mais contradicao interna nem claim
   refutavel no texto.
2. **Documento de execucao — CRIADO e MERGEADO.** `docs/execution-model.md` (#120): runbook
   as-built ancorado arquivo:linha, par de runtime do `architecture-overview.md`, 2 diagramas,
   tabela-contrato por etapa, carimbo de proveniencia point-in-time. Produzido via Workflow
   plan->gate->ultracode com verificacao adversarial (pegou 2 erros factuais no draft + recontou
   errorCodes). CLAUDE.md tambem corrigido (flags stale XDOC-03/04; Regra 3 imutavel intocada).

## TODO

### ENTREGA (15/06) — o que ainda separa o relatorio da submissao (NAO e redacao)
- [ ] **Conferir as referencias Sen/Wang contra a fonte** (autoria, paginacao, DOI) — TOPO. Sen et
      al., IEEE S&P 2014 (Bootstrapping privacy compliance...); Wang et al., USENIX Security 2022
      (PrivGuard, p. 3753-3770). Conferir em IEEE Xplore e usenix.org. Unico ponto com info
      reconstruida de busca.
- [ ] Diagramacao final (Word): contagem de paginas no RESUMO ("___ f."), data/banca placeholders, TOC.
- [ ] Confirmar com a orientadora o titulo do §3 (finais/conclusoes, nao "parciais").

### FOLLOW-UPS spun-out desta sessao (trabalho separado, sem data — abrir sessao propria)
- [ ] **Housekeeping cross-doc** — 6 divergencias as-built registradas em `docs/tasks.md` §Companion
      edits cross-doc: architecture-overview "tres eixos"; coordenador-como-agente com tool de
      despacho; numeracao Etapa 0-4 vs 1-5; "Reporter agrega" (e o coordenador); nota DD-M22 (guard
      de framework como futuro, ja implementado); specs com lag (reporter.md §1.5, classifier.md
      §4.3). PR de housekeeping DEDICADO, nao inline. NB: agora que `execution-model.md` e mais fiel
      ao as-built que `architecture-overview.md`, a decisao e se o overview e corrigido para apontar
      ao execution-model em vez de divergirem.
- [ ] **Task de testes** — ledger de cobertura/staleness salvo em memoria de projeto do Code
      (`project_funcionamento_coverage_gaps.md`). Gaps de "funcionamento sem teste": wrap de excecao
      untyped -> CoordinatorError; `run_review.py` sem caller vivo; build de Report GDPR;
      `success_all_not_applicable` sem e2e; check-all do Matcher so via prompt-content; recognizers
      BR alem de CPF nao exercitados na layer-2; fallback zero-finding de `_effective_provenance`.
      Task SEPARADA com gate proprio. Testes foram explicitamente fora de escopo na criacao do doc.

### POS-ENTREGA — repositorio (menores)
- [ ] ADR do Caminho 1: registrar a leitura pre-flight do header como excecao de fronteira.
- [ ] 3x F401 em probes: `uv run ruff check . --fix`.
- [ ] CLAUDE.md: inconsistencia de caminho "Repository state" `src/mcp_servers/` vs "Stack"/"What
      does NOT belong" `mcp_servers/`. Debito conhecido, parqueado.

### NAO tocar antes da entrega
- ruff format (114 arquivos): so decidir politica de CI; reformat pos-entrega.
- Reporter single-failed-emit: contido por ReportNotEmitted.
- POL-007 inversao Art. 11: decisao de escopo tomada — apresentar como rigor na defesa.

### BACKLOG (pos-entrega, frentes proprias)
- [ ] Caminho 2 (multiframework Report): relaxar `Literal["LGPD"]`; restaurar cross-check #2;
      atualizar `_SUPPORTED_LEGAL_FRAMEWORKS` (red-first afirmando que GDPR emite).
- [ ] Evolucao {type, value} do control + do_not_collect + lawful_basis_required (ADR-0015) — motor-primeiro.
- [ ] find_clauses_by_applicability (otimizacao de custo).
- [ ] Persistencia do Report JSON como artifact + destilacao em "linha de planilha" (Milestone D).
      INLINE-EM-PR ESTA FORA (decisao firme) — nao reintroduzir.
- [ ] Frente AEP/DULE (Camada-AEP-MVP) + superficie de deteccao do Detector.
- [ ] Avaliacao de sensibilidade ao modelo (K>=5, protocolo antes de rodar).
- [ ] Benchmark quantitativo (15-20 fixtures, K=5, taxa de concordancia).

## Design registrado — control {type, value} / do_not_collect / DULE (frente AEP)

A materializar como emenda de ADR na sessao AEP, com pre-flight de grep em SCHEMA §6.3, ADR-0015,
matcher.md §8.3:
- Control novo e MOTOR-PRIMEIRO, dado depois. `_verdict_for_control` (tools.py) so trata
  consent_required / anonymization_required; ramo final `raise AssertionError`. Control nao
  implementado NAO entra em vocabulario carregado (foot-gun de crash do sweep).
- Forma {type, value}: type = conjunto FECHADO de semanticas (um ramo cada); value = dado. Tipos:
  requires_legal_basis, lawful_basis_required (sensivel a special_category), requires_transformation
  (indeterminate se invisivel no diff), do_not_collect (proibicao).
- do_not_collect e lawful_basis_required sao dois modelos de Art. 11 e coexistem. DULE = fonte de
  obrigacao, nao framework. Controles invisiveis no diff -> indeterminate. Deteccao no Detector e
  item separado e maior.

## Referencias de artefato

- `docs/execution-model.md` — runbook as-built (visao de execucao; par do architecture-overview).
- `relatorio-qa.md` — inventario de debitos do relatorio + XDOC-01..16.
- Pesquisa de estado da arte (PrivGuard, PrivFramework, Fides, GDPR-Bench-Android, RegCheck, Catala,
  Rules-as-Code) — insumo de futura secao de trabalho relacionado; fonte das refs Sen/Wang.
- `docs/tasks.md` §Companion edits cross-doc — debito as-built (6 divergencias).
- Memoria de projeto do Code: `project_funcionamento_coverage_gaps.md` — ledger da task de testes.

## Pauta candidata da proxima sessao

Tres opcoes, todas frentes proprias com sessao FRESCA (threads longas acumulam inferencia stale):
(a) sensibilidade ao modelo — decidir ANTES de rodar: K>=5 por celula; inteiro-por-modelo vs
por-estagio (confirmar se da para parametrizar modelo por estagio); metricas (fidelidade, estabilidade,
custo, latencia); pre-flight de como o pipeline seleciona modelo hoje. (b) housekeeping cross-doc.
(c) task de testes. Nenhuma e bloqueante da entrega.

## Proximo passo imediato

Joao: conferir as refs Sen/Wang contra a fonte e fechar a diagramacao (paginas, data/banca, TOC).
Com isso o relatorio esta pronto para submissao. Tudo o mais e pos-entrega.