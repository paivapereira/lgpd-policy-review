# DESIGN — sistema de code review LGPD assistido por agentes

## Visão

Sistema de code review automatizado em pull requests que verifica conformidade do tratamento de dados pessoais com uma Política versionada que codifica o framework jurisdicional declarado (LGPD no MVP). Arquitetura em três camadas: (1) Política como artefato declarativo em `policy/`, personalizável por cliente, com vocabulários jurisdicionais como dados em `policy/vocabularies/<framework>/`; (2) sistema multi-agente coordinator-subagentes consumindo a Política em runtime via MCP; (3) integração CI/CD via GitHub Action. LGPD é instância exemplar do MVP — arquitetura é framework-agnóstica. Cliente troca de jurisdição (LGPD → GDPR) reescrevendo a Política, sem alteração de código.

## Separação de planos

O sistema opera em três planos epistêmicos disjuntos: o Detector raciocina no plano sintático (regras Semgrep sobre o diff), o Classifier no plano lexical (mapeia achados sintáticos em vocabulário da Política via `policy://vocabularies`), o Matcher no plano jurídico (avalia conformidade via `check_applicability`). Cada subagente tem vocabulário próprio; o coordinator agencia a tradução entre planos. `semgrep-runner` não consome `policy://vocabularies` — o acoplamento semântico mora no Classifier.

## Roteiro de leitura para implementação

**Antes de qualquer implementação:**

1. `docs/architecture-overview.md` §4.1-§4.4 (camadas e componentes inventariados), §5.7 (matriz tools × subagentes).
2. `policy/SCHEMA.md` §2.1 (layering estrutural vs jurisdicional), §3 (header global da Política).

**Quando implementar `policy-reader`:**

- Spec normativa: `docs/specs/policy-reader/compact.md`.
- Em ambiguidade contratual ou ordering: `docs/specs/policy-reader/canonical.md`.
- Decisões herdadas: ADR-0001 (stack), ADR-0002 (MCP conventions), ADR-0005 (multi-cliente).
- Vocabulários jurisdicionais lidos em startup: `policy/vocabularies/LGPD/*.yaml`.

**Quando implementar `semgrep-runner`:**

- Spec normativa: `docs/specs/semgrep-runner/compact.md`.
- Em ambiguidade contratual: `docs/specs/semgrep-runner/canonical.md`.
- Decisões herdadas: ADR-0001, ADR-0002.
- Escopo do rule set (bundled no MVP, per-cliente deferido): `docs/specs/semgrep-runner/canonical.md` §7, ADR-0005.

**Quando implementar subagentes (Triager, Detector, Classifier, Matcher, Reporter):**

- Responsabilidades e tools permitidas: `docs/architecture-overview.md` §5.2-§5.6.
- Matriz tools × subagentes: `docs/architecture-overview.md` §5.7.
- `AgentDefinitions` (`mcp_servers`, `allowed-tools`): implementadas em `src/coordinator/run.py`; specs normativas em `docs/specs/subagents/`.

## Decisões arquiteturais críticas

- **ADR-0001** — Stack: Python 3.12.7, uv. Decision 2 amended 2026-05-21 (Semgrep+FastMCP 3.2.4+Pydantic 2.13.4+MCP 1.27.1 pins); Decision 3 amended 2026-05-22 (cláusula IDs `POL-NNN` opacos, framework-agnostic).
- **ADR-0002** — MCP conventions: hybrid placement, custom URI schemes (`policy://`), três classes de erro. §3 amended 2026-05-17 (Option B wire format: `isError: false` discriminado por presença de `errorCode` em `structuredContent`).
- **ADR-0003** — Spec architecture: dual canonical+compact com escalation pointers; paridade restrita a contract surfaces.
- **ADR-0004** — FastMCP 3.x.
- **ADR-0005** — Multi-cliente: vocabulários jurisdicionais como dados em `policy/vocabularies/<framework>/`, expostos via resource `policy://vocabularies`. D1+D2 amended 2026-05-22 (`article_source` → `statutory_reference`).
- **ADR-0006** — Language conventions: tokens canônicos do vocabulário `operation` em inglês; POL-000 segue convenção português; código/comments/identifiers em inglês.
- **ADR-0007** — Escopo MVP: matching de cláusulas restrito a `operation: collection`; demais operações retornam `not_applicable` com razão explícita.
- **ADR-0008** — Task decomposition: 8-12 tasks de 1-3h agrupadas em milestones; verificação two-scope (task-level: function tests + revisão Chat; milestone-level: manual exercise contra RFs). Amended 2026-05-16.
- **ADR-0009** — Domain boundaries: share functions not types — `_format_law_reference` aceita 5 positional args, não `StatutoryReferenceEntry`.
- **ADR-0010** — Semgrep install discipline: `uv tool install semgrep==1.163.0`; per-call binary check em `scan_diff` (não startup).

## Validação global

Sistema integrado completo: rodar `policy-review` (GitHub Action ou CLI local) sobre PR sintética contendo violação plantada (e.g., coleta de CPF sem base legal declarada), obter Report JSON com finding correto incluindo `clause_id`, `verdict`, `evidence`, e trinque de provenance `(policy_schema_version, policy_version, legal_framework)`.

Teste de generalização: substituir `policy/policy.yaml` e `policy/vocabularies/LGPD/` por versão GDPR equivalente e observar a decisão jurisdicional na superfície da tool `check_applicability` (flip de veredito por cláusula), sem alteração de código do sistema. No MVP, o coordenador recusa fail-loud (`UnsupportedLegalFramework`; ADR-0007) emitir Report consolidado sob framework ≠ LGPD, em vez de coagir o rótulo silenciosamente; Report multi-jurisdição é trabalho futuro.
