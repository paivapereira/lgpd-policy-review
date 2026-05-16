# Proposta de Orientação — TCC2

**Aluno:** João Pereira  
**Curso:** Engenharia de Software (segunda graduação) — UTFPR Câmpus Dois Vizinhos  
**Formação prévia:** Direito (15+ anos de prática jurídica)  
**Atuação profissional:** Analista de Negócios na Vilt Group (terceirizada Adobe)  
**Orientadora pretendida:** Profa. Alinne Cristinne Corrêa Souza  
**Período de execução proposto:** maio–junho de 2026  
**Modalidade de entrega:** fluxo contínuo (entrega TCC2 até 15/06; defesa até 30/06)

---

## 1. Tema

Sistema de code review automatizado em pull requests que verifica conformidade do tratamento de dados pessoais com uma Política versionada derivada da LGPD.

A contribuição central do trabalho é tratar a **Política como artefato de primeira classe**: um arquivo declarativo em YAML, versionado em Git, que codifica obrigações da Lei 13.709/2018 em cláusulas verificáveis por software, com versionamento explícito do esquema e do conteúdo. A Política é fonte de verdade do que constitui conformidade, e o sistema multi-agente é apenas uma das máquinas possíveis para consumi-la — pode ser revisada por jurista sem conhecimento de agentes, validada em CI, ou consumida por qualquer cliente que implemente o protocolo MCP (Model Context Protocol).

## 2. Contextualização e problema

A Lei Geral de Proteção de Dados (Lei 13.709/2018) impõe obrigações sobre o tratamento de dados pessoais que precisam ser verificadas no software que coleta, transforma e armazena esses dados. Ferramentas de análise estática como Semgrep e detectores de informação pessoalmente identificável como Microsoft Presidio cobrem casos genéricos, mas duas lacunas persistem.

A primeira é a ausência de tratamento adequado a identificadores brasileiros — CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde. Ferramentas mainstream cobrem identificadores anglófonos (SSN, NHS Number, ITIN), e a tradução para o contexto brasileiro vem sendo feita ad hoc por cada equipe.

A segunda, mais profunda, é a ausência de uma camada intermediária entre a Lei (texto natural ambíguo) e as regras de detecção (sintáticas, sem contexto jurídico). A literatura técnica de "Policy as Code" cobre Open Policy Agent/Rego para infraestrutura, mas não há equivalente consolidado para verificar obrigações de proteção de dados em código de aplicação. Cada equipe acaba reescrevendo regras dispersas, sem rastreabilidade de qual artigo da Lei justifica qual verificação, sem versionamento do entendimento jurídico que evolui ao longo do tempo, e sem distinção clara entre "o sistema verifica" e "o sistema sabe qual é a regra".

## 3. Objetivo geral

Projetar e implementar um sistema de code review automatizado que, integrado a pull requests, verifica a conformidade do tratamento de dados pessoais com uma Política versionada derivada da LGPD, demonstrando a viabilidade da Política versionada como artefato declarativo independente do mecanismo que a interpreta.

## 4. Objetivos específicos

a) Especificar e implementar um esquema YAML versionado para a Política, com mecanismo de tombstone para evolução das cláusulas ao longo do tempo, mantendo rastreabilidade legal entre cláusula e artigo da Lei.

b) Implementar dois servidores MCP — `policy-reader` para acesso estruturado à Política e `semgrep-runner` para detecção sintática — desacoplando o conhecimento jurídico da capacidade de detecção.

c) Projetar e implementar um sistema multi-agente com cinco subagentes especializados (Triager, Detector, Classifier, Matcher, Reporter), aplicando o princípio de single responsibility por agente, com tools restritas por função.

d) Construir recognizers para identificadores brasileiros (CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde), endereçando lacuna real das ferramentas internacionais existentes.

e) Integrar o sistema a GitHub Actions, postando *findings* como inline comments em pull requests, sem bloquear merge no MVP — posicionamento operacional informativo, condizente com a honestidade epistêmica de que análise estática verifica conformidade declarativa, não efetiva.

f) Validar empiricamente o sistema contra benchmark sintético de aproximadamente 200 *snippets* rotulados por veredito esperado.

## 5. Justificativa

A relevância prática é direta: a LGPD está em vigor desde 2020 e gera obrigações de auditoria contínua sobre código de aplicação em qualquer organização brasileira que processe dados pessoais — universo que inclui praticamente toda empresa de software no país. Ferramentas que automatizam essa verificação reduzem custo operacional e melhoram cobertura.

A relevância acadêmica está na proposta de tratar a Política como artefato declarativo de primeira classe, versionável e auditável independentemente do mecanismo que a interpreta. Esse desenho é o que separa o sistema proposto de SAST com regras hardcoded, e é a contribuição que pretende ser defensável como inovação.

O perfil do aluno é qualificação rara para o problema. A construção da ponte entre obrigação jurídica (texto natural da Lei) e cláusula verificável (estrutura processável por agente) é exatamente onde se concentra o desafio do trabalho — e exige simultaneamente formação jurídica sólida e capacidade técnica em engenharia de software. O aluno traz 15+ anos de prática jurídica, segunda graduação em Engenharia de Software em curso na UTFPR, e atuação profissional como Analista de Negócios em equipe que opera plataformas de coleta de dados em escala (Adobe Experience Platform).

## 6. Arquitetura proposta

O sistema é estruturado em três camadas:

**Camada 1 — Política versionada.** Artefato declarativo em YAML sob `policy/`, versionada em dois eixos independentes (`policy_schema_version` para o esquema do arquivo, `policy_version` para o conteúdo das cláusulas).

**Camada 2 — Sistema multi-agente.** Um agente coordenador orquestra cinco subagentes especializados — Triager (decide se um pull request é relevante para análise), Detector (identifica pontos de tratamento candidatos via Semgrep), Classifier (extrai contexto estruturado por candidato), Matcher (avalia conformidade contra cláusulas da Política), Reporter (agrega vereditos em relatório JSON consolidado). Dois servidores MCP suportam a camada: `policy-reader` (acesso à Política) e `semgrep-runner` (detecção sintática).

**Camada 3 — Integração CI/CD.** GitHub Action que dispara o sistema em pull requests, recebe o relatório JSON e posta *findings* como inline comments. Informativa no MVP — não bloqueia merge.

A separação em camadas permite que a Política seja revisada por jurista sem conhecimento de agentes, que o sistema multi-agente seja substituído sem reescrever a Política, e que a integração CI/CD seja portada para outras plataformas (GitLab CI, Jenkins) com adaptador, não reescrita.

O documento `architecture-overview.md`, anexo a esta proposta, detalha cada componente, contrato de subagente, fluxo de execução e fronteiras epistêmicas do sistema.

## 7. Metodologia

O trabalho adota *Spec-Driven Development* (SDD) como metodologia formal de execução. SDD é um *workflow* estruturado de desenvolvimento assistido por agentes de IA, no qual especificações em formato textual estruturado são o artefato primário do projeto e o código se torna saída derivada das especificações. O fluxo canônico de SDD compreende quatro fases — *Specify* (redação de especificações), *Plan* (decomposição em tarefas), *Implement* (execução com agentes), *Validate* (verificação contra critérios de aceitação previamente definidos) — e tem suporte bibliográfico em referências da indústria recente, incluindo guia oficial da Anthropic sobre práticas de codificação assistida por agentes e o toolkit GitHub Spec Kit.

A escolha de SDD é dupla: alinha-se ao caráter inerentemente especificativo do problema (a Política é spec do que é conformidade; os contratos de subagente são specs do que cada agente faz) e mitiga o risco principal de projetos solo de curta duração — retrabalho por decisão tomada cedo demais. Especificações revisadas antes de qualquer linha de código têm custo de retificação ordens de magnitude menor que código revisado em produção.

Os artefatos produzidos por fase incluem: documentos de arquitetura e Architecture Decision Records (fase *Specify*); especificações detalhadas dos componentes individuais (transição *Specify* → *Plan*); código fonte dos servidores MCP, subagentes, integração CI/CD e *recognizers* brasileiros (fase *Implement*); benchmark sintético rotulado e relatório de validação empírica (fase *Validate*).

A pilha tecnológica adotada é Python 3.12 como linguagem principal, FastMCP 2.x para implementação dos servidores MCP, Pydantic 2.5 para validação de esquemas, Semgrep como motor de detecção sintática, GitHub Actions para integração CI/CD, e Inspect AI como framework de avaliação. O versionamento é em Git com convenção *Conventional Commits*. A abordagem de detecção é híbrida em duas etapas — Semgrep determinístico para detecção estável de candidatos, agentes baseados em modelos de linguagem para classificação contextual e avaliação de conformidade contra a Política.

Calibração de granularidade da fase Plan. A literatura recente da Anthropic (RAJASEKARAN, 2026) documentou empiricamente que decomposição fina prescrita por frameworks como GitHub Spec Kit, originalmente motivada por limitações de coerência em contexto longo de modelos como Claude Sonnet 4.5, perdeu valor com modelos mais capazes da família Opus 4.6+. Este trabalho, executado com Claude Opus 4.7, adota SDD com calibração explícita: decomposição em 8-12 tasks de granularidade média (1-3 horas), com critério de aceitação amarrado aos requisitos funcionais consolidados em `docs/REQUIREMENTS.md` e gate de verificação tripartite (testes automatizados, revisão independente por instância separada de Claude conforme padrão multi-instance review do Domínio 4 do Claude Certified Architect Foundations exam guide, e exercício manual operado pelo autor). A escolha materializa o princípio "find the simplest solution possible, and only increase complexity when needed" (ANTHROPIC, 2025) e é formalizada em ADR-0008.

## 8. Escopo e fronteiras

**Dentro do escopo do MVP:** Política versionada com esquema 0.1.0; servidores MCP `policy-reader` e `semgrep-runner`; cinco subagentes operacionais; *recognizers* para os seis identificadores brasileiros listados; GitHub Action funcional; benchmark sintético de validação; relatório técnico de TCC2.

**Fora do escopo do MVP, mantidos como roadmap pós-trabalho:** classificação de severidade dos *findings*, subagente *fix-proposer* para sugestão automática de correção, bloqueio condicional de *merge* sob critério de taxa de falso-positivo validada em base real, mapa de dados longitudinal cruzando informações entre múltiplos pull requests, dimensões da LGPD além de consentimento (`consent_required`) e anonimização (`anonymization_required`) — transferência internacional, retenção, direitos do titular, dados de menores e tratamento compartilhado — não cobertas pela Política v0.1.0.

**Fronteira epistêmica explícita:** o sistema verifica conformidade *declarativa*, não *efetiva*. Análise estática de pull request examina o que o código declara fazer com dados pessoais, não o comportamento de tempo de execução em produção. Quando a verificação exige observação que análise estática não consegue realizar, o sistema retorna o veredito `indeterminate` indicando a dimensão a ser verificada manualmente, em vez de fingir certeza não justificada.

## 9. Cronograma

O cronograma cobre as seis semanas entre o início efetivo da execução e a entrega do relatório técnico de TCC2 em 15 de junho de 2026. As fases referenciam o ciclo de SDD descrito na seção 7. A organização agrupa specs por categoria coerente — dois MCP servers em conjunto, cinco subagentes em conjunto — permitindo revisão holística de decisões cruzadas dentro de cada categoria, com ciclo curto de implementação imediatamente após cada bloco de especificação.

| Semana | Período | Entregáveis principais | Fase SDD |
| :----: | :------ | :--------------------- | :------- |
| 1 | 05/05 – 11/05 | Especificações dos dois servidores MCP (`policy-reader` e `semgrep-runner`); ADR-0002 | Specify |
| 2 | 12/05 – 18/05 | Implementação dos dois servidores MCP; conjunto de *recognizers* brasileiros (CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde) | Implement |
| 3 | 19/05 – 25/05 | Especificações dos cinco subagentes e do coordenador | Specify |
| 4 | 26/05 – 01/06 | Implementação dos subagentes, coordenador e tool customizada `emit_report` | Implement |
| 5 | 02/06 – 08/06 | GitHub Action; integração *end-to-end*; construção do benchmark sintético | Implement + Validate |
| 6 | 09/06 – 15/06 | Validação empírica; redação do relatório técnico de TCC2; entrega | Validate |

Estado atual à data desta proposta: a fase de *Specify* em nível arquitetural está concluída — `architecture-overview.md` (anexo) e ADR-0001 (configuração inicial do projeto) já redigidos e versionados. As especificações detalhadas dos componentes individuais e a implementação serão produzidas no período coberto pelo cronograma acima.

## 10. Resultados esperados

Ao término do trabalho, espera-se entregar: o sistema funcional descrito nas seções 6 e 7, executável sobre pull requests reais; a Política versionada inicial em esquema 0.1.0, codificando um conjunto representativo de cláusulas da LGPD; o conjunto de *recognizers* brasileiros como diferencial técnico; o benchmark sintético rotulado e os resultados da validação empírica; e o relatório técnico documentando o trabalho.

O trabalho será documentado segundo o modelo institucional de **Relatório Técnico de Ferramenta ou Produto de Software** adotado pela UTFPR Câmpus Dois Vizinhos para a disciplina de TCC2.

## 11. Referências preliminares

ANTHROPIC. **Best practices for agentic coding**. Anthropic Engineering, 2025. Disponível em: https://www.anthropic.com/engineering.

ANTHROPIC. **Building Effective Agents**. Anthropic Research, 2025. Disponível em: <https://www.anthropic.com/research/building-effective-agents>.

ANTHROPIC. **Model Context Protocol Specification**. 2024. Disponível em: https://modelcontextprotocol.io.

BÖCKELER, Birgitta. **Understanding Spec-Driven Development**. martinfowler.com, 2025.

BRASIL. **Lei nº 13.709, de 14 de agosto de 2018**. Lei Geral de Proteção de Dados Pessoais (LGPD). Diário Oficial da União, Brasília, DF, 15 ago. 2018.

GITHUB. **spec-kit: Toolkit to help you get started with Spec-Driven Development**. GitHub Repository, 2025. Disponível em: https://github.com/github/spec-kit.

NYGARD, Michael T. **Documenting Architecture Decisions**. 2011. Disponível em: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions.

OPEN POLICY AGENT. **Policy as Code with Rego**. Disponível em: https://www.openpolicyagent.org.

PRIVADO.AI. **Static analysis for data privacy**. Disponível em: https://www.privado.ai.

RAJASEKARAN, P. **Harness design for long-running application development**. Anthropic Engineering, 24 mar. 2026. Disponível em: <https://www.anthropic.com/engineering/harness-design-long-running-apps>.

SEMGREP. **Semgrep — Lightweight static analysis for many languages**. Disponível em: https://semgrep.dev.

---

**Anexo único:** `architecture-overview.md` — visão sistêmica detalhada da arquitetura proposta, incluindo contratos de subagentes, fluxo de execução, posicionamento operacional e fronteiras epistêmicas.