# Session handoff — pós-#07

**Estado.** PR #8 (`docs/specs-semgrep-runner`) mergeado em `main` via squash.
`docs/specs/semgrep-runner.md` v0.1.0 publicada (segunda spec do projeto).
`docs/architecture-overview.md` §4.2 e §5.2 sincronizadas. Branch `main` limpo.
Fim da semana 1 do cronograma de seis.

**Próxima sessão (#08).** ADR-0002 expandido — consolida em ADR formal as
decisões materializadas em `policy-reader.md` e `semgrep-runner.md`: placement
híbrido `structuredContent` + `content[0].text`, naming `mcp__<server>__<tool>`,
contrato de erro com classes business/system, declaração explícita de validation
vazio quando aplicável, forma "três beats" do review pass (§8.<final>) como
convenção operacional do princípio 26.

**Próximo grande bloco — semana 3.** Specs dos três subagentes (Detector,
Classifier, Matcher) e do coordinator. Template próprio a estabelecer durante a
primeira spec — assimetria com `_template.md` de componentes MCP registrada na
§2 do `semgrep-runner.md`.

**Reagendado.** Consolidação dos 26 princípios em
`docs/spec-authoring-principles.md` (originalmente pendência do handoff #06)
reagendada para #09 ou janela de limpeza entre semanas. ADR-0002 tem prioridade
pedagógica e cognitiva maior na #08.

**Pendência externa.** Retorno técnico da Profa. Alinne sobre `proposta-tcc2.md`
continua aguardando. Quando chegar, ajustes + response letter ganham slot
próprio.

**Forward-references vivos no repo.** Citações a
`docs/spec-authoring-principles.md` e a ADR-0002 referenciam documentos
não-existentes. Risco de orfandade se #08 e #09 não materializarem.
