# Política de Proteção de Dados — Schema canônico

**Status:** em redação na semana 2 do cronograma de TCC2 (12/05–18/05/2026), em paralelo à implementação dos servidores MCP.

**Versão alvo:** `policy_schema_version: 0.1.0`.

Este arquivo é o esqueleto inicial. Conteúdo definitivo vai cobrir: estrutura completa do YAML da Política, vocabulário POL-000 (sete classes de dados), regras de identidade unidirecional de `clause_id`, hierarquia de `article_source`, sub-ids em requirements e exceptions, ciclo de vida com tombstone (`successors`, `effective_until`, `deprecation_reason`), enum de `operation` e vocabulário de `prescribed_treatment` consumidos por `check_applicability`, e formato sumarizado de `article_sources_summary` no resource `policy://catalog`.

Spec do componente que serve este schema: `docs/specs/policy-reader.md`.