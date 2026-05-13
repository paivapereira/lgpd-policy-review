# Session handoff

**Última sessão fechada:** #13 (2026-05-13)
**Branch ativa:** `main` (limpa)
**Próxima sessão:** #14

## Estado atual

Ciclo de meta-decisões de spec design fechado. Três ADRs em vigor: ADR-0001 (workflow conventions), ADR-0002 (MCP conventions and deferments), ADR-0003 (dual-spec architecture and §8.<final> lifecycle). Specs em paridade: policy-reader e semgrep-runner com canonical + compact cristalizados e §8.<final> consistente com o lifecycle prescrito.

Artefatos vigentes:

- `docs/adr/0001-bootstrap.md`
- `docs/adr/0002-mcp-conventions-and-deferments.md`
- `docs/adr/0003-dual-spec-architecture.md`
- `docs/architecture-overview.md`
- `docs/specs/policy-reader/canonical.md` (673 linhas) + `compact.md` (397 linhas)
- `docs/specs/semgrep-runner/canonical.md` (440 linhas) + `compact.md` (202 linhas)
- `docs/specs/_template.md` (esqueleto canônico de spec MCP)
- `policy/SCHEMA.md` (v0.1.0) + `policy/policy.yaml` (header v0.1.0)
- `policy/clauses/POL-000.*` (definitional, v0.1.0)
- `docs/_drafts/spec-authoring-principles.md` (4 princípios extraídos)
- `.github/PULL_REQUEST_TEMPLATE.md` (canonical↔compact parity checklist)

Implementação ainda não começou. Próxima fase é skeleton + lógica das duas MCP servers (semanas 4-5 do cronograma TCC).

## Pendências cross-sessão

### Implementação semana 4-5

Próximo grande bloco. Ancorada nos compacts cristalizados na sessão #11. Branch nova a partir de `main`. Ordem provável: `policy-reader` primeiro (já tem POL-000 + SCHEMA.md prontos para alimentar `check_applicability` em modo cláusula-única), `semgrep-runner` em seguida. Decisão sobre paralelizar fica para abertura da #14.

POL-001 (primeira cláusula `substantive`, candidata: tratamento de `dados_de_autenticacao`) entra no escopo da semana 4-5 quando o `check_applicability` do `policy-reader` exigir uma cláusula real para exercitar o fluxo. Não precede a implementação; é puxada quando o teste de aceitação §8 do policy-reader pedir.

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

Promoção do draft acontece quando algumas cláusulas substantivas exercitarem o SCHEMA e os princípios estabilizarem.

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
- Specs governadas por ADR-0003: compact = consumed (always-loaded); canonical = reference (on-demand); §8.<final> com lifecycle three beats + resolution line.

## Sugestão de abertura da próxima sessão (#14)

Abrir implementação do `policy-reader` MCP server. Primeira decisão da sessão: estrutura de diretórios sob `mcp_servers/policy_reader/` (provavelmente `server.py`, `policy_loader.py`, `tools/`, `tests/`), respeitando o stack canônico em CLAUDE.md. Compact do policy-reader em mão (`docs/specs/policy-reader/compact.md`, 397 linhas) é o artefato de leitura primária; canonical fica para escalation. Critério de aceitação da sessão: skeleton implementado, sem necessariamente passar todos os critérios §8 — mínimo é `mcp__policy-reader__get_clause(POL-000)` retornar wire format conformante.
