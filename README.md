# lgpd-policy-review

Sistema de code review automatizado em pull requests que verifica conformidade do tratamento de dados pessoais com uma Política versionada derivada da LGPD, construído sobre Claude Agent SDK, Claude Code e Model Context Protocol (MCP).

> **Status:** Repositório em desenvolvimento. Documentação completa e arquitetura detalhada do sistema multi-agente serão publicadas após a defesa. Instruções de setup do ambiente de desenvolvimento estão em §Setup; execução do sistema multi-agente em pull requests reais é parte da arquitetura ainda não exposta neste repositório.

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

Python 3.12.7, Claude Agent SDK, FastMCP 3.2.4, Pydantic 2.13.4, MCP 1.27.1 (transitivo via FastMCP), Semgrep 1.163.0 com regras de recognizers brasileiros customizadas, Inspect AI, GitHub Actions. Pins formais em `pyproject.toml` (constraints declarativas) + `uv.lock` (versões resolvidas) na raiz do repositório; Semgrep pinado conforme [ADR-0010](docs/adr/0010-semgrep-installation-strategy.md) (binário externo, fora do `uv.lock` do projeto).

## Setup (desenvolvimento)

Pré-requisitos do ambiente de desenvolvimento. Estas instruções cobrem reprodução de builds e execução de testes; orquestração do sistema multi-agente em PRs reais será documentada após a defesa.

**Dependências de runtime:**

- **Python 3.12.7** via [pyenv-win](https://github.com/pyenv-win/pyenv-win), pinado em `.python-version`.
- **Node 24** via npm em diretório de usuário (não requer admin local).
- **Semgrep 1.163.0** via `uv tool install`, isolado do `uv.lock` do projeto ([ADR-0010](docs/adr/0010-semgrep-installation-strategy.md)).
- **Git >= 2.30** no PATH. Requerido por `semgrep-runner`/`scan_diff` para uso de `--baseline-commit`, que depende de `git diff --merge-base` introduzido em git 2.30 (Semgrep issue [semgrep/semgrep#5891](https://github.com/semgrep/semgrep/issues/5891)).

**Instalação em PowerShell 5.1 (Windows 11 sem admin local):**

```powershell
# Executar na raiz do repositório.

# 1. Python 3.12.7 via pyenv-win (assume pyenv-win já instalado)
pyenv install 3.12.7
pyenv local 3.12.7

# 2. uv (project manager Python)
pip install uv

# 3. Dependências do projeto (pyproject.toml + uv.lock na raiz)
uv sync

# 4. Semgrep CLI (user-scope, isolado)
uv tool install semgrep==1.163.0

# 5. Verificação
semgrep --version  # esperado: 1.163.0
```

**Fontes autoritativas dos pins:**

- `pyproject.toml` na raiz — constraints declarativas (lower/upper bounds aceitáveis). A chave `[project].name = "mcp-servers"` é o identificador lógico do pacote do projeto, não path de subdiretório.
- `uv.lock` na raiz — versões determinísticas resolvidas (`uv sync` cristaliza aqui).
- ADR-0010 — pin de Semgrep (não está em `uv.lock` por ser binário externo via `uv tool install`).

Em caso de divergência entre versões instaladas localmente e o que `uv.lock` registra, `uv.lock` é fonte determinística — sincronize com `uv sync`.

## Metodologia

O desenvolvimento segue *Spec-Driven Development* — especificações textuais sob `docs/specs/` e decisões arquiteturais sob `docs/adr/` são artefatos primários do projeto, e o código é saída derivada.

## Licença

Código distribuído sob [Licença MIT](LICENSE). Conteúdo da Política LGPD em `policy/` é trabalho derivado de literatura técnica e legislação pública brasileira; revisão de licenciamento específico para o documento de política está prevista para versão 1.0.

## Status acadêmico

Projeto em fase de desenvolvimento. Não publicar uso em produção sem revisão por desenvolvedor sênior.