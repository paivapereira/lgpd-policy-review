# Session handoff

**Última sessão fechada:** #12 (2026-05-12)
**Branch ativa:** `docs/specs-dual-strategy` (9 commits ahead de `main`, push após Commit 9)
**Próxima sessão:** #13

## Estado atual

Estratégia dual canonical+compact cristalizada para as duas MCP servers. Canonicals receberam taxonomia A-G aplicada; compacts derivados sob frame consumed/reference. PR template com checklist de paridade canonical↔compact em `.github/`.

Artefatos:

- `docs/specs/policy-reader/canonical.md`: 673 linhas.
- `docs/specs/policy-reader/compact.md`: 397 linhas.
- `docs/specs/semgrep-runner/canonical.md`: 440 linhas.
- `docs/specs/semgrep-runner/compact.md`: 202 linhas.
- `docs/_drafts/spec-authoring-principles.md`: 4 princípios extraídos (Resource vs Tool, Schema fora, Spec descreve, Split de tool).
- `.github/PULL_REQUEST_TEMPLATE.md`: 18 linhas.

Implementação ainda não começou. Próxima fase é skeleton + lógica das duas servers (planejado para semanas 4-5 do cronograma TCC).

## Pendências cross-sessão

### ADR-0003 retrospectivo

Acumula dois conteúdos substantivos:

1. **Reframe consumed/reference da arquitetura de docs.** Compact é o que Code consome em implementação; canonical é referência on-demand. Decisão tomada mid-sessão #12, mudou critério de sucesso da estratégia dual. Vale registro formal em ADR retrospectivo.
2. **§8.\<final\> lifecycle pós-aplicação dos patches.** ADR-0002 Decisão 5 mandata forma "three beats" sem distinguir tempo de autoria vs pós-aplicação. Sessão #12 manteve forma "three beats" pós-aplicação por leitura conservadora; ADR-0003 deve registrar a decisão e o ciclo de vida formal.

Não inclui: article_source matching semantics (decisão de design contida na spec, nota inline no canonical do policy-reader em Commit 9).

### Sweep da dívida `_drafts/`

Quando o draft `docs/_drafts/spec-authoring-principles.md` promover para `docs/spec-authoring-principles.md` (sem `_drafts/`), 6 cross-doc links precisam de sweep:

- 2 em `docs/specs/policy-reader/canonical.md` (§4.1 Schema fora; §7.1 Spec descreve o quê)
- 2 em `docs/specs/semgrep-runner/canonical.md` (§3 Resource vs Tool; §7 Split de tool)
- 0 em `docs/specs/policy-reader/compact.md`
- 2 em `docs/specs/semgrep-runner/compact.md` (§4 Resource vs Tool; §5.1 Split de tool)

Comando do sweep (executar no momento da promoção):

```powershell
Get-ChildItem docs\specs -Filter canonical.md -Recurse | ForEach-Object {
  (Get-Content $_.FullName) -replace '_drafts/spec-authoring-principles', 'spec-authoring-principles' | Set-Content $_.FullName
}
Get-ChildItem docs\specs -Filter compact.md -Recurse | ForEach-Object {
  (Get-Content $_.FullName) -replace '_drafts/spec-authoring-principles', 'spec-authoring-principles' | Set-Content $_.FullName
}
```

Promoção do draft acontece quando algumas cláusulas substantivas exercitarem o SCHEMA e os princípios estabilizarem (handoff #10).

### Implementação semana 4-5

Fase próxima do projeto, ancorada nos compacts cristalizados. Não é pendência stricto sensu — é next phase. Quando começar, abrir branch nova a partir de `main` (após merge da `docs/specs-dual-strategy`).

## Convenções operacionais consolidadas

- Conventional Commits, branches `feat/fix/docs/<short>`, squash merge no PR.
- Sem trailer `Co-Authored-By` (gravado na memória do Claude Code).
- Stack em `CLAUDE.md`: FastMCP 2.x, Python 3.12.7, Claude Code v2.1.123+.
- Formato dual de cláusulas: YAML operacional + Markdown rationale; Markdown prevalece em drift.
- Chat planeja/decide/revisa; Code materializa.
- Granularidade fina de commits no branch + squash no merge.
- Modo professor com tag de domínio para conceitos da prova.
- Validação YAML obrigatória antes de PR que toque schema ou cláusula (PyYAML 6.0.3 instalado `--user`).

## Notas para a próxima sessão

- Compacts foram validados empiricamente para skeleton de implementação. Pendente: validação empírica para lógica completa (`check_applicability` four-verdict generation, `scan_diff` execution flow). Pode emergir necessidade de revisão pontual durante implementação.
- Friction notes do proxy test do policy-reader sugeriram princípios candidates (cap cognitive load, sanity wrap-aware, anti-regras enumeradas, etc.). Não foram adicionados ao draft nesta sessão (decisão registrada no learning-log #12); ficam para consolidação futura quando o draft estabilizar.

## Sugestão de abertura da próxima sessão (#13)

Resolver ADR-0003 retrospectivo, que acumula dois conteúdos substantivos da sessão #12: reframe consumed/reference da arquitetura de docs, e §8.\<final\> lifecycle pós-aplicação dos patches. Decisão sobre formato (ADR único cobrindo ambos vs dois ADRs separados) cabe na abertura da sessão — leitura inicial sugere ADR único, porque ambos são meta-decisões sobre como specs são estruturadas e versionadas.

Em paralelo, decidir se a implementação semana 4-5 começa imediatamente após ADR-0003 ou se vale uma sessão dedicada a consolidação do draft `_drafts/spec-authoring-principles.md` antes. Implementação não bloqueia ADR-0003 sancionar; ambas podem rodar em paralelo se houver fôlego.