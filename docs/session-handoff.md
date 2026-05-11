# Session handoff — pós-sessão #10

**Última atualização:** 2026-05-10
**Estado de `main`:** pós-merge dos PRs #12 (POL-000), #13 (SCHEMA + policy.yaml), #14 (cleanup spec).

## Estado da Política

POL-000 v0.1.0 (cláusula `definitional` — vocabulário de nove classes funcionais de dados pessoais) está publicada em `policy/clauses/POL-000.yaml` + `policy/rationale/POL-000.md`. Schema canônico em `policy/SCHEMA.md` v0.1.0. Header global em `policy/policy.yaml` v0.1.0.

**Vocabulários canônicos estabelecidos.**
- `personal_data_categories` — nove classes, extensível pela Política via cláusula `definitional`.
- `lawful_basis` — fechado no schema (SCHEMA §9.1), 10 valores Art. 7º + 8 valores Art. 11.
- `operation` — fechado no schema (SCHEMA §9.2), 21 valores + `other` para não-taxatividade.
- `control` — fechado no schema (SCHEMA §9.5), MVP com dois valores; caminho evolutivo para `{type, value}` documentado.

## Próximo grande bloco — semana 2 do cronograma (começa 12/05)

**1. Conclusão da review/destilação das specs MCP.** Trabalho iniciado na sessão #08, retomado para destilação. As specs atuais (`docs/specs/policy-reader.md`, `docs/specs/semgrep-runner.md`) serão compactadas — reduzir número de linhas, preservar substância. Materializa a "estratégia dual canonical+compact para specs" que estava listada entre as três deliberações pendentes da review #08; agora promovida de pendência aberta para trabalho ativo.

**2. Implementação dos MCP servers — FastMCP 2.x.** `policy-reader` (expõe a Política via `get_clause`, `find_clauses_by_law_article`, `check_applicability`) e `semgrep-runner` (detecção sintática). Começa com POL-000 apenas. `check_applicability` implementado inicialmente como stub que sempre retorna `not_applicable` — veredito legítimo enquanto não houver cláusula `substantive`. POL-001 minimalista (fixture que exercita os quatro vereditos do enum) entra quando chegar a hora de implementar `check_applicability` de forma substantiva — sessão curta, ~60 min, opção B sugerida (`dados_de_saude` × `collection` → `consent_required`, juridicamente sólida e exercita `special_category: true`) ou alternativa a decidir naquele momento.

Destravados pela publicação de POL-000 v0.1.0 + SCHEMA + policy.yaml mergeados em `main`.

## Pendências documentais

**Correção semântica da linha 384 do `docs/specs/policy-reader.md`.** Cleanup PR #14 preservou `dados_sensíveis` com acento porque trocar por `dados_sensiveis` (snake_case sem acento) preservaria identificador inválido — `dados_sensiveis` não é classe em POL-000. Correção em PR follow-up: substituir por `dados_de_saude` (carrega `special_category: true`, serve como exemplo intuitivo de `violation_candidate`) ou outra classe deliberadamente escolhida. Pequeno, mas semântico — merece deliberação separada.

**Forward-references vivos a `docs/spec-authoring-principles.md`** em `policy-reader.md §5.5` e `semgrep-runner.md §3`. Documento referenciado ainda não existe; consolidação prevista para sessão futura, depois que algumas cláusulas substantivas exercitem o SCHEMA e os princípios de redação se estabilizem.

**Duas deliberações arquiteturais pendentes da review da sessão #08.** Candidatas a ADR-0003:
- Colapso 5→3 subagentes (`Scanner = Triager + Detector + Classifier`; `Matcher`; `Reporter`). Decisão pertinente antes da implementação — afeta diretamente quantos agentes serão codados.
- Framing workflow vs multi-agent system na defesa do TCC. Decisão de narrativa do TCC, não de implementação; pode ser postergada.

## Pendências externas

Retorno técnico da Profa. Alinne sobre `docs/proposta-tcc2.md` — aguardando.

## Convenções operacionais consolidadas

- Conventional Commits, branches `feat/fix/docs/<short>`, squash merge no PR.
- Sem trailer `Co-Authored-By` (gravado na memória do Claude Code).
- Stack em `CLAUDE.md`: FastMCP 2.x, Python 3.12.7, Claude Code v2.1.123+.
- Formato dual de cláusulas: YAML operacional + Markdown rationale; Markdown prevalece em drift.
- Chat planeja/decide/revisa; Code materializa.
- Granularidade fina de commits no branch + squash no merge.
- Modo professor com tag de domínio para conceitos da prova.
- Validação YAML obrigatória antes de PR que toque schema ou cláusula (PyYAML 6.0.3 instalado `--user`).

## Sugestão de abertura da próxima sessão (#11)

Continuar a destilação das specs MCP iniciada na #08 — primeira coisa do próximo bloco. Em paralelo ou logo em seguida, decidir se a deliberação sobre colapso 5→3 subagentes entra como ADR-0003 antes da implementação (recomendado: o desenho dos agentes afeta o código a ser escrito) ou se pode ser decidida durante o processo. A deliberação sobre framing workflow vs multi-agent é decidível depois — não bloqueia código.
