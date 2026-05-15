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
- `AgentDefinitions` (`mcp_servers`, `allowed-tools`): a redigir em Fase 2 — ainda não existem.

## Decisões arquiteturais críticas

- **ADR-0001** — Stack: FastMCP 2.x, Python 3.12.7, uv.
- **ADR-0002** — MCP conventions: hybrid placement, custom URI schemes (`policy://`), três classes de erro.
- **ADR-0003** — Spec architecture: dual canonical+compact com escalation pointers; paridade restrita a contract surfaces.
- **ADR-0005** — Multi-cliente: vocabulários jurisdicionais como dados em `policy/vocabularies/<framework>/`, expostos via resource `policy://vocabularies`.

## Validação global

Sistema integrado completo: rodar `policy-review` (GitHub Action ou CLI local) sobre PR sintética contendo violação plantada (e.g., persistência de CPF sem anonimização), obter Report JSON com finding correto incluindo `clause_id`, `verdict`, `evidence`, e trinque de provenance `(policy_schema_version, policy_version, legal_framework)`.

Teste de generalização: substituir `policy/policy.yaml` e `policy/vocabularies/LGPD/` por versão GDPR equivalente, rerodar a mesma PR, obter Report válido sob framework distinto sem alteração de código do sistema.
