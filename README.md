# lgpd-policy-review

Sistema de code review automatizado em pull requests que verifica conformidade do tratamento de dados pessoais com uma Política versionada derivada da LGPD, construído sobre Claude Agent SDK, Claude Code e Model Context Protocol (MCP).

> **Status:** Repositório em desenvolvimento. Documentação completa, arquitetura detalhada e instruções de execução serão publicadas após a defesa.

## Contexto

Trabalho de Conclusão de Curso do Bacharelado em Engenharia de Software da Universidade Tecnológica Federal do Paraná (UTFPR), apresentado em 2026.

- **Autor:** João Guilherme de Mello Paiva Pereira
- **Orientador:** *________*
- **Defesa prevista:** 2026

## Visão geral

O sistema trata a Política como artefato de primeira classe — arquivo declarativo em YAML, versionado em Git, que codifica obrigações da Lei 13.709/2018 em cláusulas verificáveis por software, com versionamento explícito do esquema e do conteúdo. O sistema multi-agente é apenas uma das máquinas possíveis para consumir a Política, que pode ser revisada por jurista sem conhecimento de agentes ou consumida por qualquer cliente que implemente o protocolo MCP.

A arquitetura está organizada em três camadas:

- **Política versionada** — artefato declarativo em YAML sob `policy/`, fonte de verdade de conformidade.
- **Sistema multi-agente** — coordenador orquestrando cinco subagentes especializados (Triager, Detector, Classifier, Matcher, Reporter), com dois servidores MCP de suporte (`policy-reader` e `semgrep-runner`) e recognizers para identificadores brasileiros.
- **Integração CI/CD** — GitHub Action que dispara o sistema em pull requests e posta findings como inline comments (informativo no MVP, sem bloquear merge).

A visão sistêmica completa, com fluxo de execução, contratos de subagente e fronteiras epistêmicas, está documentada em [`docs/architecture-overview.md`](docs/architecture-overview.md).

## Stack

Python 3.12, Claude Agent SDK, FastMCP, Semgrep, Microsoft Presidio com recognizers brasileiros customizados, Pydantic, Inspect AI, GitHub Actions.

## Metodologia

O desenvolvimento segue *Spec-Driven Development* — especificações textuais sob `docs/specs/` e decisões arquiteturais sob `docs/adr/` são artefatos primários do projeto, e o código é saída derivada.

## Licença

Código distribuído sob [Licença MIT](LICENSE). Conteúdo da Política LGPD em `policy/` é trabalho derivado de literatura técnica e legislação pública brasileira; revisão de licenciamento específico para o documento de política está prevista para versão 1.0.

## Status acadêmico

Projeto em fase de desenvolvimento. Não publicar uso em produção sem revisão por desenvolvedor sênior.