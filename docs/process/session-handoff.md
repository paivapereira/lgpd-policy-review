# Session handoff — pos-Caminho-1 (guarda legal_framework na branch; relatorio em redacao)

> Template-overwrite, nao patch cumulativo. Tratar como hipotese a verificar contra o repo (git log, leitura de arquivo), nao como estado autoritativo. Primeira acao de qualquer sessao Code: confirmar git state, nao assumir. Em particular: confirmar se o PR do Caminho 1 ja foi mergeado em `main` antes de tratar a guarda como existente.

## Onde estamos

A frente de avaliacao esta FECHADA (Camada-3-MVP). A coleta de evidencia dos fixtures diferidos foi feita (T-eval, evidence-only). O bug de mislabel do `legal_framework` foi diagnosticado e corrigido pelo Caminho 1, que esta na branch aguardando merge. O caminho critico tecnico do entregavel 15/06 permanece concluido; o que resta e redacao e reconciliacao do relatorio, mais um PR a mergear.

### Caminho 1 — guarda fail-loud (NA BRANCH, NAO MERGEADO)

Branch `feat/coordinator-framework-guard`. Dois commits: `bec44e5` (test, red — reproduz o bug: pipeline emitia Report sob GDPR) e `c138f2c` (feat, green). Quatro arquivos: `src/coordinator/errors.py` (nova `UnsupportedLegalFramework`), `src/coordinator/run.py` (+29 linhas: leitura do header no init via `load_policy(resolve_policy_root())`; guarda antes do `_run_reporter_stage`; `_coverage_gap` estendido; constante `_SUPPORTED_LEGAL_FRAMEWORKS = {"LGPD"}`), `tests/coordinator/test_coordinator_errors.py` (taxonomia), `tests/coordinator/test_run_framework_guard.py` (ancoras).

Comportamento: sob root nao-LGPD a guarda recusa com `UnsupportedLegalFramework(stage="framework_guard")` e `CoordinatorError(coverage_gap=...)`, ANTES do Reporter — os estagios Triager->Detector->Classifier->Matcher rodam e `03-classifier.json` e escrito (observabilidade live-GDPR preservada; confirmado em exercicio manual sob eval-gdpr real). Falha de leitura do header -> `CoordinatorStartupError(stage="startup")`. Trio verde: pytest 307 passed, ruff check limpo, mypy --strict limpo (46 arquivos). Sem `Co-Authored-By`. Joao abre PR + squash-merge via UI.

Verificar antes de assumir: `git log --oneline` de `main` para confirmar se o squash entrou; se entrou, registrar o hash do squash.

### Relatorio TCC2

- Rascunho da secao de avaliacao em `docs/eval/avaliacao-secao-rascunho-numero-independente.md` (untracked) — metodo (dois escopos), taxonomia de tres camadas, read-surface (independencia jurisdicional na tool, nao no Report, ADR-0007), e os dois quadros preenchidos com a coleta live. Falta INTEGRAR ao relatorio (e insumo, nao a secao final no documento).
- §3 Conclusoes: NAO escrito. Planejado para depois da revisao cross-doc.
- Completude de §2.1 (Funcionalidades), §2.2 (Persistencia), §2.3 (Tecnologias): NAO confirmada. Joao precisa verificar no arquivo; se em stub, sobem para pendencia de redacao.
- Evidencia de custo disponivel (prints): US$ 5,15 conta inteira (junho ate 05), caching ativo. RESSALVA: e custo agregado (pipeline + Chat + Code), NAO isolavel ao pipeline sem filtrar por chave de API/workspace. Nao citar como "custo do pipeline" sem o filtro.

## Revisao cross-doc pendente (antes do §3) — contradicoes a reconciliar

- §2.5 promete "obter um Report valido sob o novo framework [GDPR]" — FALSO (mislabel silencioso). Migrar para "decisao jurisdicional observavel na superficie do check_applicability". Esta e a unica contradicao INTERNA ao relatorio (metodo nega o que os resultados mostram) — prioridade.
- §3-parcial afirma "resta a especificacao do Matcher, a implementacao integrada e a validacao empirica" — todos FEITOS. Reescrever no §3 final.
- proposta-tcc2 prometia "~200 snippets"; entregue = 6 fixtures + qualitativa (reducao Camada-3-MVP). Enquadrar como decisao de escopo documentada.
- Quadro 3 (cronograma) marca 10-15/jun como "Planejado" — atualizar para executado.

## Debitos abertos

1. **Spec drift coordinator.md §5:** excecoes 13->15. Ancora de teste atualizada; tabela §5 + `docs/tasks.md §Companion` NAO. Housekeeping.
2. **ruff format vs ruff check:** repo nao e `ruff format`-clean; decidir se CI adota `ruff format --check`.
3. **ADR do Caminho 1:** registrar a leitura direta do header no coordinator como excecao de pre-flight ratificada (SDK sem leitura de resource deterministica). Housekeeping.

## Backlog de producao (pos-relatorio; NAO sao pendencias de 15/06)

- **Report JSON como artifact do workflow.** Hoje descartado (Actions "Artifacts: -"); o parecer so existe no Step Summary do dispatch. Barato (o Report ja e gerado).
- **Inline-comment em PR (modo producao, `pull_request`).** Hoje DEFERRED to Milestone D. Maior.
- **Caminho 2 — multiframework Report.** Relaxar `legal_framework: Literal["LGPD"]` (`matcher/models.py:60`, `reporter/models.py:61`) -> conjunto validado; restaurar cross-check #2; adicionar validator `finding.legal_framework == header`. Revisitar `run_engine_cases._emits_report` + campo STRICT em `camada3_compare` + testes que afirmam o Literal + emenda ADR-0007. Necessario para qualquer cliente nao-LGPD. **Dependencia:** atualizar `_SUPPORTED_LEGAL_FRAMEWORKS` da guarda do Caminho 1 (deliberado, com teste red-first afirmando que GDPR agora emite).
- **Evolucao `{type, value}` do vocabulario `control`** (SCHEMA §6.3) — pre-requisito para os C-labels do DULE.
- **Frente AEP/DULE — Milestone proprio,** nao um item. Tres sub-tamanhos: Caminho 2 (pequeno, mapeado) / vocabulario `control` + autoria de clausulas DULE (medio, e a tese exercitada) / Detector lendo config/schema do AEP alem de codigo (grande, decisao arquitetural propria). Primeiro movimento: definir uma Camada-AEP-MVP. Lembrar: o sistema verifica codigo de PR (plano de codigo), nao os campos governados pelo DULE em runtime (plano de dados) — complementa, nao substitui, o enforcement do AEP.

## Pauta da proxima sessao

**Avaliacao de sensibilidade ao modelo (Opus/Sonnet/Haiku).** Valiosa para o relatorio e para producao. NAO rodar com K baixo. Decisoes a tomar ANTES de qualquer execucao: K por celula (minimo 5, licao PROBE/INDET); pipeline-inteiro-por-modelo vs por-estagio (a segunda e mais util para producao — modelo barato no Triager/Detector, capaz no Matcher — mas exige o pipeline parametrizar modelo por estagio; confirmar se ja e possivel); metricas (fidelidade ao veredito esperado, estabilidade intra-modelo por convergencia K, custo, latencia). Pre-flight: confirmar como o pipeline seleciona modelo hoje. Ganho de combinar com o Caminho 2 (rodar sobre LGPD + GDPR de uma vez). Candidata a §3 trabalho futuro ou a secao de avaliacao extra.

## Proximo passo imediato

Joao: abrir PR do Caminho 1 + squash via UI. Depois, revisao cross-doc do relatorio (comecando pela reconciliacao do §2.5) -> §3 Conclusoes. Verificar §2.1/§2.2/§2.3.