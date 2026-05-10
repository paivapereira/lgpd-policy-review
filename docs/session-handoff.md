# Session handoff — pós-#09

**Estado.** PR #9 (`docs/adr-0002-mcp-conventions-and-deferments`)
mergeado em `main` via squash. `docs/adr/0002-mcp-conventions-and-
deferments.md` v1.0 publicada — sete decisões de convenção
(placement híbrido `structuredContent` + `content`, naming
`mcp__<server>__<tool>` com hyphen, contrato de erro de três
classes, declaração positiva de empty error class, forma "três
beats" do review pass, versionamento de spec, schemes custom de
URI) e nove deferimentos com critério de revisita explícito
(cinco do `policy-reader`, quatro do `semgrep-runner`). Branch
`main` limpo. Forward-references conceituais para ADR-0002
resolvidas; texto das specs ainda não patchado.

**Próxima sessão (#10).** Pacote duplo. Primeiro, PR enxuto de
follow-up patches da ADR-0002 — três patches mecânicos: (i)
substituir `semgrep_runner` (underscore) por `semgrep-runner`
(hyphen) em `mcp__server__tool` references na spec e verificar
ausência no `architecture-overview.md`, (ii) trocar
forward-reference em `policy-reader.md` §3 por citação à ADR-0002
Decisão 7, (iii) trocar forward-reference em `policy-reader.md`
§5.5 por citação à ADR-0002 Decisão 6. Verificar também se alguma
seção de contrato de erro precisa adicionar declaração positiva de
classe vazia (Decisão 4). Depois do PR de patches mergeado, abrir
redação completa de `policy/SCHEMA.md` v0.1.0 — vocabulário
POL-000, enum de `operation`, vocabulário de `prescribed_treatment`,
forma de `article_sources_summary`, regra unidirecional de
`clause_id`, hierarquia de `article_source`. SCHEMA é trabalho
substantivo e provavelmente consome o resto da sessão sozinho.

**Próximo grande bloco — semana 2.** Implementação dos dois MCP
servers em FastMCP 2.x. Bloqueado por `policy/SCHEMA.md`: o
vocabulário POL-000 e o enum de `operation` vivem lá, e a
implementação do `policy-reader` precisa carregar a Política contra
esse schema. Cronograma da `proposta-tcc2.md` semana 2 começa
12/05.

**Reagendado.** Consolidação dos 26 princípios em
`docs/spec-authoring-principles.md` agora deslocada para
pós-SCHEMA — recomendação absorvida da Session #08 review é que
principles e enxugamento das specs venham depois da materialização
de SCHEMA (sem isso, principles e specs continuam apontando para
destinos que não existem). Provável sessão #11.

**Deliberação arquitetural pendente.** Três recomendações fortes do
review da Session #08 ainda não decididas: (a) colapso de
subagentes de cinco para três (Scanner = Triager+Detector+Classifier;
Matcher; Reporter), com justificativa "pipeline fixa = workflow,
não sistema agentic" alinhada com guidance pública da Anthropic;
(b) framing explícito do projeto como workflow (não multi-agent
system) na defesa de TCC; (c) estratégia dual canonical + compact
para specs (longa em `docs/specs/<componente>.md`, destilada em
`docs/specs/<componente>.compact.md`, com governance de drift).
Estas são decisões arquiteturais reais, candidatas a ADR-0003 (ou
desdobramento em dois ADRs). Janela natural: pós-principles,
pré-enxugamento.

**Pendência externa.** Retorno técnico da Profa. Alinne sobre
`proposta-tcc2.md` continua aguardando. Quando chegar, ajustes +
response letter ganham slot próprio.

**Forward-references vivos no repo.** Citações a
`docs/spec-authoring-principles.md` em `policy-reader.md` §5.5 e
`semgrep-runner.md` §3 continuam apontando para documento
não-existente. Risco de orfandade material reduzido agora que
ADR-0002 materializou — mas principles ainda é pendência.