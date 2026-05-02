# lgpd-policy-review

Sistema de code review automatizado com verificação de conformidade contra Política LGPD versionada, construído sobre Claude Agent SDK, Claude Code e Model Context Protocol (MCP).

> **Status:** Repositório em desenvolvimento. Documentação completa, arquitetura detalhada e instruções de execução serão publicadas após a defesa.

## Contexto

Trabalho de Conclusão de Curso do Bacharelado em Engenharia de Software da Universidade Tecnológica Federal do Paraná (UTFPR), apresentado em 2026.

- **Autor:** João Guilherme de Mello Paiva Pereira
- **Orientador:** *________*
- **Defesa prevista:** 2026

## Visão geral

A proposta é construir um sistema multi-agente que analise pull requests automaticamente e verifique conformidade com uma Política LGPD interna versionada (SemVer), tratando a Política como artefato de primeira classe — schema validável, evolução rastreável, decisões auditáveis. O sistema escala para humano quando a verificação automática é insuficiente.

Componentes principais:

- Política LGPD em formato estruturado (cláusulas com IDs estáveis, semver, changelog)
- Servidores MCP para acesso à Política e a recognizers de PII
- Pipeline CI/CD que dispara o agente em pull requests do GitHub
- Benchmark de validação (LGPD-Bench-BR) com casos sintéticos rotulados

## Stack

Python 3.12, claude-agent-sdk, FastMCP, Presidio, GitHub Actions.

## Licença

Código distribuído sob [Licença MIT](LICENSE). Conteúdo da Política LGPD em `policy/` é trabalho derivado de literatura técnica e legislação pública brasileira; revisão de licenciamento específico para o documento de política está prevista para versão 1.0.

## Status acadêmico

Projeto em fase de desenvolvimento. Não publicar uso em produção sem revisão por desenvolvedor sênior.