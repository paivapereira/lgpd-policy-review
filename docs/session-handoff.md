# Session handoff

**Última sessão fechada:** #14 (2026-05-13)
**Branch ativa:** `feat/policy-reader-skeleton` (3 commits acima de `main`, sem PR aberto)
**Próxima sessão:** #15

## Estado atual

Fase A da implementação do `policy-reader` MCP server completa. Skeleton validado empiricamente end-to-end via Claude Code — 5 superfícies (2 resources + 3 tools) registradas, `.mcp.json` em project-scope reconhecido pelo client, wire format conformante (com micro-débito de `mime_type` para resources documentado abaixo). Fase B (loader real + `get_clause` end-to-end + testes) deferida para #15.

Quatro decisões de stack/arquitetura tomadas na #14, três com ADRs pendentes:

1. **uv adotado como toolchain** (gerenciador de deps + Python) — pendente ADR-0004.
2. **FastMCP 3.x adotado** (resolve deferred decision "2.x vs 3.x" da #07) — pendente ADR-0004 (junto com uv) + verificação contra NVD/GitHub Advisories da claim de CVE em 2.x.
3. **Multi-tenant LGPD-only com mitigações para evolução multi-jurisdição** — pendente ADR-0005 + `SCHEMA.md §7` ajuste.
4. **Skeleton-first para o `policy-reader`** — decisão de design contida, não precisa de ADR.

Artefatos novos da #14 (na branch `feat/policy-reader-skeleton`, não em main):

- `pyproject.toml`, `uv.lock`, `.python-version` (3.12.7)
- `src/mcp_servers/__init__.py`, `src/mcp_servers/py.typed`
- `src/mcp_servers/policy_reader/__init__.py`, `src/mcp_servers/policy_reader/server.py`
- `.mcp.json`

Três commits na branch: `a5e715a`, `de9be95`, `501fe17`. PR só depois de Commit 7 ou 8 da #15.

## Pendências cross-sessão

### Documentação pendente — alta prioridade #15

**ADR-0005** — "LGPD-coupling em vocabulários jurisdicionais: decisão MVP e migration path". Estrutura rascunhada no chat da #14:

- *Context:* sistema desenhado pra multi-tenant LGPD; multi-jurisdição (GDPR, CCPA) é futuro pós-TCC; vocabulários jurisdicionais hardcoded em código simplificam MVP mas acoplam Layer 2 a LGPD.
- *Decision:* MVP v0.1.0 mantém vocabulários jurisdicionais (`Operation`, `Control`, `OutOfScopeReason`, `LawfulBasis`) hardcoded em `policy_loader.py` como `frozenset`/`tuple` (não `Enum`); campos Pydantic correspondentes tipados como `str` validados em `model_validator` contra esses sets. `AcceptedLaw` validado dinamicamente contra `header.accepted_law_identifiers` desde o MVP (não hardcoded). Marcadores `# JURISDICTIONAL — LGPD MVP, see ADR-0005` em cada ponto de coupling.
- *Consequences positive:* migration de (a)→(b) toca apenas (1) externalizar vocabulários para Layer 1 em formato a definir, (2) substituir validação contra set por validação contra Layer 1, (3) header ganha `legal_framework`. Campos Pydantic não mudam.
- *Consequences negative:* perda parcial de type safety estática nesses campos; validação ocorre em runtime.
- *Migration path:* sketch das três etapas — externalizar vocabulários ~1 sessão; header.legal_framework + dispatch ~0.5 sessão; adicionar segundo framework (e.g. GDPR) ~2-3 sessões. Total realista pós-TCC: ~7-8 sessões.

**`policy/SCHEMA.md §7` ajuste.** Adicionar à tabela atual de §7 uma coluna "Natureza" com dois valores (`estrutural` | `jurisdicional`), mais frase: *"Vocabulários `jurisdicionais` refletem a LGPD no MVP v0.1.0. Sua externalização para Layer 1 (vocabulários como dados, não código) é documentada em ADR-0005 como migration path pós-MVP."* Classificação: `ClauseType`, `ClauseStatus`, `VocabularyKind` são estruturais; `lawful_basis`, `operation`, `accepted_law_identifiers`, `reason` (em out_of_scope), `control` são jurisdicionais.

**ADR-0004** — "uv como toolchain + FastMCP 3.x". Pode ficar para #16 ou intercalado na #15 se houver fôlego. Deve cobrir:

- uv como deps + Python management (com nota sobre `--managed-python` no `init` não forçar download se há Python compatível no PATH).
- FastMCP 3.x adoption (component versioning, hot reload, OpenTelemetry; arquitetura nova "Providers and Transforms" invisível ao nosso uso; resolve deferred decision da #07).
- Verificação contra NVD/GitHub Advisories da claim de CVE em 2.x — se procede, cita; se não procede, remove dessa justificativa.
- Convenção `uv run python ...` vs venv ativado em README/onboarding.
- Update do `CLAUDE.md` para refletir stack atualizada (FastMCP 3.x, uv).

### Implementação Fase B — `policy-reader` semanas 4-5

Continua na branch `feat/policy-reader-skeleton` (segue aberta).

**Commit 5** — `src/mcp_servers/policy_reader/policy_loader.py` com Pydantic models alinhados com `SCHEMA.md`, discriminated union por `clause_type`, fail-fast validation no startup, três mitigações de ADR-0005:

- Campos jurisdicionais tipados como `str` (não Enum), validados em `model_validator` contra `frozenset` constants nomeadas (`_LGPD_OPERATIONS`, `_LGPD_CONTROLS`, `_LGPD_OUT_OF_SCOPE_REASONS`, `_LGPD_LAWFUL_BASES`).
- `AcceptedLaw` validado contra `header.accepted_law_identifiers` (não hardcoded).
- Marcadores `# JURISDICTIONAL — LGPD MVP, see ADR-0005` em cada constante.
- Arquitetura geral: Pydantic v2, `_STRICT` config com `extra="forbid"`, `_tombstone_iff_deprecated` model_validator em ambas branches do union, `load_policy(policy_dir)` retornando `LoadedPolicy(header, clauses)` indexado por clause_id, `PolicyLoadError` para abortar startup. CLI entry para sanity check durante development.

**Commit 6** — wire `get_clause` ao loader real. Substitui stub do `de9be95` por implementação que faz lookup no dict carregado, valida regex `^POL-\d{3}$`, retorna cláusula ou erro `INVALID_CLAUSE_ID_FORMAT` / `CLAUSE_NOT_FOUND` conforme compact §3. Trata caso `deprecated` (retorno com tombstone, não erro).

**Commit 7** — testes pytest cobrindo §8.2 (success active, invalid format, not found, success deprecated). Fixture YAML de cláusula deprecated em `tests/fixtures/` (POL-000 é active, não serve).

**Commit 8** — validação manual §8 via Claude Code. Documenta gaps no learning-log da #15.

**Commit 9 (closure #15)** — atualiza learning-log + handoff. Abre PR da branch (squash em main quando Commit 7 ou 8 passar).

### Env var pendente

`POLICY_READER_POLICY_DIR` deliberadamente fora do `.mcp.json` skeleton da #14. Adicionar junto com loader real no Commit 5 (com expansão `${POLICY_READER_POLICY_DIR}` no `.mcp.json` env block; server.py lê com default `./policy` relativo ao repo root).

### Micro-débito de `mime_type` em resources

FastMCP default deu `mimeType: "text/plain"` para os dois resources do `policy-reader` na #14, mas retornamos JSON estruturado. Fix de uma linha por resource: `@mcp.resource("policy://...", mime_type="application/json")`. Empacota junto com loader real no Commit 5 ou 6, não Commit 4b cosmético separado.

### CVE check em FastMCP 2.x

Claim de "3 CVEs não-patcheados em 2.x exigindo upgrade para 3.2.0+" veio de issue de terceiro (sooperset/mcp-atlassian, abril/2026). Não confirmado contra NVD/GitHub Advisories. Verificação pendente, vai pro Context do ADR-0004: se procede, cita CVE IDs; se não procede, remove essa justificativa e mantém component versioning + deferred decision resolution + hot reload como base.

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
- Stack atualizada na #14 (formalização pendente em ADR-0004 que vai sincronizar `CLAUDE.md`): **FastMCP 3.x** (`fastmcp>=3.2.0,<4.0`), Python 3.12.7, Claude Code v2.1.123+, **uv como toolchain de deps + Python**. `CLAUDE.md` ainda diz "FastMCP 2.x" — divergência consciente até ADR-0004.
- Comandos Python no projeto: `uv run python ...` ou venv ativado via `.venv\Scripts\Activate.ps1`. Convenção definitiva pendente ADR-0004.
- Formato dual de cláusulas: YAML operacional + Markdown rationale; Markdown prevalece em drift.
- Chat planeja/decide/revisa; Code materializa.
- Granularidade fina de commits no branch + squash no merge.
- Modo professor com tag de domínio para conceitos da prova.
- Validação YAML obrigatória antes de PR que toque schema ou cláusula.
- Specs governadas por ADR-0003: compact = consumed (always-loaded); canonical = reference (on-demand); §8.<final> com lifecycle three beats + resolution line.
- Skeleton-first em implementações novas: valida pressupostos da stack antes de empilhar lógica (aplicado e validado empiricamente na #14).

## Sugestão de abertura da próxima sessão (#15)

Abrir com **agenda dupla**, primeira hora dedicada a documentação pendente:

1. `policy/SCHEMA.md §7` ajuste (estrutural vs jurisdicional + nota apontando ADR-0005).
2. `docs/adr/0005-lgpd-coupling-in-jurisdictional-vocabularies.md` redigido conforme estrutura rascunhada na seção "Documentação pendente" acima.

Ambos vão direto em `main` via fluxo de doc (consistente com fechamento da #14). Branch `docs/adr-0005-lgpd-coupling` ou similar; PR enxuto; squash merge.

Após documentação, retoma branch `feat/policy-reader-skeleton` para Fase B:

3. Commit 5 — `policy_loader.py` com mitigações ADR-0005.
4. Commit 6 — `get_clause` end-to-end.
5. Commit 7 — testes pytest §8.2 (incluindo fixture deprecated).
6. Commit 8 — validação manual §8 via Claude Code.
7. PR + squash + handoff da #16.

Compact do policy-reader (`docs/specs/policy-reader/compact.md`, 397 linhas) continua leitura primária; canonical fica para escalation pontual quando comportamento específico exigir.
