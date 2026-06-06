# Session handoff — pos-QA + Caminho 1 mergeado (relatorio v2 em revisao final)

> Template-overwrite, nao patch cumulativo. Tratar como hipotese a verificar contra o repo (git log, leitura de arquivo), nao como estado autoritativo. Primeira acao de qualquer sessao Code: confirmar git state, nao assumir. O `relatorio-qa.md` (data efetiva 2026-06-05) e o inventario de debitos verificado mais recente; em divergencia com este handoff, o QA prevalece e os numeros sao re-lidos.

## Onde estamos

MVP completo e atestado com ressalvas declaradas (ver `relatorio-qa.md` §0). As tres camadas estao implementadas, exercitadas de ponta a ponta e cobertas por suite verde. O Caminho 1 (guarda fail-loud de `legal_framework`) **foi mergeado** — PR #112, commit `05d8a18` (confirmado pelo QA; corrige o XDOC-12, que apontava este handoff como stale). O caminho critico tecnico do entregavel 15/06 esta concluido; o que resta e redacao e reconciliacao do relatorio, mais housekeeping de baixo risco.

Estado estatico verificado (QA, re-executado na data efetiva): pytest 307 passed / 309 collected (2 live deselected); mypy --strict limpo (46 arquivos); ruff check src tests limpo; ruff check . com 3 F401 em probes; ruff format --check com 114 arquivos reformataveis (debito aberto); 4/4 portoes de marco PASS (inclui CI run 26983111920); motor de avaliacao 13/13 casos engine-runnable com match.

### Relatorio TCC2

- v2 em voo: branch `docs/relatorio-tcc2-v2-e-qa`, PR #113. As edicoes de revisao estao especificadas no prompt `prompt-trelatorio-rev-v1.md` (E1-E7: objetivo (f), citacoes OPA + Ferrara&Spoto, frase de novidade, Camada 3 "dispara mas pula", nota da Figura 2, 309/307, numeracao do Triager). Prompt com pre-flight de verificacao de string (HALT se nao bater, dado o v2).
- Rascunho de avaliacao em `docs/eval/avaliacao-secao-rascunho-numero-independente.md` — insumo, ja alinhado a reescrita do §2.5 (XDOC-01). Falta INTEGRAR ao corpo.
- §3 Conclusoes: a escrever, depois da revisao cross-doc.
- Custo: US$ 5,15 conta inteira (junho ate 05), caching ativo. RESSALVA: agregado (pipeline + Chat + Code), NAO isolavel ao pipeline sem filtrar por chave de API/workspace. O relatorio hoje NAO cita custo — manter assim, ou so citar com o filtro.

## TODO

### Antes da entrega (15/06) — alto valor, baixo risco
- [ ] XDOC-01: reconciliar §2.5 (contradicao "Report valido sob GDPR"). [prompt E2/E4] — INEGOCIAVEL
- [ ] XDOC-02: tempo verbal "parcial/restando" -> concluido (RESUMO, §2.3, §3, AP. E)
- [ ] XDOC-03/04: flags falsas no CLAUDE.md ("134 passing", "CI not configured", "subagents not implemented", "early development")
- [ ] XDOC-11: "~200 snippets" residual -> reenquadrar [objetivo (f) no prompt]
- [ ] XDOC-16: AP. D "ADR-0001 a 0010" -> corpo vai ate 0016 (sem 0013)
- [ ] XDOC-14/15: linha de cronograma da janela corrente; ADR-0011 "Proposto" -> embarcado
- [ ] ADR do Caminho 1 (§6.3 #3): registrar leitura pre-flight do header como excecao de fronteira
- [ ] 3x F401 (§5): `uv run ruff check . --fix`

### Se houver janela — medio, baixo risco
- [ ] XDOC-05..10: spec drifts (coordinator/classifier/reporter vs codigo) — sessao housekeeping propria
- [ ] [verificar] CLAUDE.md vs ADR-0001 D4: sweep das regras imutaveis (D-5 deferido; distinto de XDOC-03/04)
- [ ] [verificar] isError/is_error consistencia entre servidores FastMCP (vs XDOC-10?)
- [ ] [verificar] §10.5 matcher.md (governanca tool/resource, sessao #48) foi commitado? Se nao, e drift (talvez ja XDOC-05/06)
- [ ] [verificar] higiene do registro de debitos: remover bullets resolvidos de tasks.md §Companion e dos §10.5

### NAO tocar antes da entrega
- [ ] ruff format (114 arquivos): so DECIDIR politica de CI; reformat e pos-entrega (diff gigante, polui blame)
- [ ] Reporter single-failed-emit (§6.3 #4): contido por ReportNotEmitted, nao observado em 10 corridas
- [ ] POL-007 inversao Art. 11: decisao de escopo tomada — apresentar como rigor na defesa, nao corrigir
- [ ] Loader cross-valida control / TimeoutExpired->GIT_REF_NOT_FOUND: estruturais, mitigados por construcao

### Backlog pos-entrega (frentes proprias)
- [ ] Caminho 2 (multiframework Report): relaxar `Literal["LGPD"]` (matcher/models.py:60, reporter/models.py:61) -> conjunto validado; restaurar cross-check #2; validator finding.legal_framework==header. Dependencia: atualizar `_SUPPORTED_LEGAL_FRAMEWORKS` da guarda (deliberado, red-first afirmando que GDPR emite)
- [ ] Evolucao {type, value} do control (SCHEMA §6.3) + do_not_collect e lawful_basis_required (ADR-0015)
- [ ] find_clauses_by_applicability (otimizacao de custo; hoje check-all/sweep)
- [ ] Report JSON como artifact + inline-em-PR de producao (Milestone D)
- [ ] Frente AEP/DULE (definir Camada-AEP-MVP) + superficie de deteccao do Detector (config/schema AEP, nao so codigo)
- [ ] Avaliacao de sensibilidade ao modelo (K>=5, protocolo antes de rodar)

## Design registrado — control {type, value} / do_not_collect / DULE (para a frente AEP)

Decidido em Chat, a materializar como emenda de ADR (provavel ADR-0015) na sessao de planejamento AEP, com pre-flight de grep em SCHEMA §6.3, ADR-0015 e matcher.md §8.3:

- Qualquer control novo e trabalho de motor primeiro, dado depois. `_verdict_for_control` (tools.py) so trata `consent_required`/`anonymization_required`; ramo final `raise AssertionError`. Regra do repo: control nao-implementado NAO entra em vocabulario carregado (foot-gun de crash do sweep) — por isso POL-008 vive em `eval/proposed/`. Logo `do_not_collect` exige ramo novo no motor; nao e data-only (corrige inferencia anterior).
- Forma `{type, value}`: `type` = conjunto FECHADO de semanticas que o motor sabe avaliar (um ramo cada); `value` = dado. Tipos propostos: `requires_legal_basis`, `lawful_basis_required` (ADR-0015, sensivel a `special_category`), `requires_transformation` (pode dar `indeterminate` se a transformacao nao for visivel no diff — precedente do `anonymization_required`, que retorna sempre indeterminate), `do_not_collect` (proibicao: casa -> violation_candidate, sem avaliar base). Linha de ouro: type novo = motor+schema+teste+ADR; instancia nova de type existente = dado puro.
- do_not_collect vs lawful_basis_required sao dois modelos de Art. 11 e coexistem: proibicao para o sensivel vedado (a maioria, exceto genero — observacao do Joao), base-exigida-sensivel para hipoteses com caminho permitido. do_not_collect e o candidato natural a primeiro morador da forma {type,value}.
- DULE = fonte de obrigacao, nao framework. Entra via `accepted_law_identifiers` + clausulas; C-labels mapeiam nos mesmos types. Honestidade obrigatoria: controles DULE invisiveis no diff (cripto em repouso, retencao) -> `indeterminate`. A superficie de DETECCAO (Detector reconhecer transferencia a terceiro no codigo AEM/AEP) e item separado e maior; a forma {type,value} resolve o vocabulario, nao a deteccao.

## Referencias de artefato

- `relatorio-qa.md` — inventario de debitos verificado + matriz de cobertura RF/RNF + 16 achados cross-doc (XDOC-01..16). Fonte autoritativa do estado atual.
- `prompt-trelatorio-rev-v1.md` — prompt Code das edicoes E1-E7 do relatorio.
- `docs/eval/avaliacao-secao-rascunho-numero-independente.md` — insumo da secao de avaliacao.
- Referencias novas (justificativa/novidade): OPEN POLICY AGENT (2024); FERRARA; SPOTO, Static Analysis for GDPR Compliance, ITASEC 2018.

## Pauta da proxima sessao

Avaliacao de sensibilidade ao modelo (Opus/Sonnet/Haiku). NAO rodar com K baixo. Decidir ANTES de executar: K por celula (>=5, licao PROBE/INDET); pipeline-inteiro-por-modelo vs por-estagio (a segunda e mais util — barato no Triager/Detector, capaz no Matcher — mas exige parametrizar modelo por estagio; confirmar se ja e possivel); metricas (fidelidade ao veredito esperado, estabilidade intra-modelo por convergencia K, custo, latencia). Pre-flight: confirmar como o pipeline seleciona modelo hoje. Ganho de combinar com o Caminho 2. Candidata a §3 trabalho futuro ou secao de avaliacao extra.

## Proximo passo imediato

Joao: aplicar as edicoes do relatorio (prompt E1-E7) e fechar a revisao cross-doc comecando por XDOC-01 (§2.5) -> escrever §3 Conclusoes. Os XDOC-03/04 (CLAUDE.md), F401 e a ADR do Caminho 1 sao ganhos baratos no caminho. Verificar completude de §2.1/§2.2/§2.3 no arquivo.