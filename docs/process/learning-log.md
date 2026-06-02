# Learning Log — TCC LGPD Code Review

Registro denso por sessão de estudo. Não é prosa: tópicos.
Cada entry serve dois propósitos: (a) fixação de conceitos da prova
Claude Certified Architect Foundations (junho 2026); (b) memória
operacional do projeto.

Formato por entry:
- Data e tema
- Conceitos da prova exercitados (tag de domínio)
- Decisões tomadas
- Artefatos criados (arquivos, commits, configs)
- Validações empíricas
- Próximo passo

---

## 2026-05-01 — bootstrap-claude-md-d3

### Conceitos da prova exercitados

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- CLAUDE.md hierarchy: quatro níveis cumulativos
  (enterprise > user > project > subdirectory) + CLAUDE.local.md gitignored
- Mecânica de loading: upward search a partir do CWD; project-root
  CLAUDE.md sobrevive a `/compact`; subdirectory CLAUDE.md é lazy
  (recarrega só quando agente lê arquivo daquele subdir)
- Override por especificidade em conflito; coexistência cumulativa
  no resto
- Anti-padrões mapeados: arquivos > 200 linhas reduzem adherence;
  procedimentos multi-step pertencem a skills, não CLAUDE.md;
  preferências pessoais pertencem a user-scope, não project
- Distinção entre CLAUDE.md (instrução para agente), README
  (descrição para humano), AGENTS.md (padrão cross-vendor
  emergente), e auto-memory (notas que o agente escreve para si)
- Importação via `@path/file.md` — DRY para humano, não economia
  de tokens

**Domínio 5 — Context Management & Reliability (15%)**

- Padrão de provenance: agente cita `arquivo:linha` em vez de
  parafrasear regra. Validado empiricamente nesta sessão.

### Decisões tomadas

- Repositório monorepo, nome `lgpd-policy-review`, privado durante
  desenvolvimento, licença MIT
- Stack canônica: Python 3.12.7 (pyenv-win), Claude Agent SDK,
  FastMCP, Presidio com recognizers BR, Ruff, mypy strict,
  pytest + pytest-asyncio, GitHub Actions
- Idiomas: código/CLAUDE.md/commits em inglês; Política em PT;
  outputs do sistema em PT
- Três regras imutáveis traduzindo a tese:
  - Escalonamento humano em conflito Lei × Política
  - Citação de clause IDs estáveis em todo finding
  - Compatibilidade `policy_schema_version` declarada
- Convenções: Conventional Commits; main protegida; feature
  branches `feat/`, `fix/`, `docs/`
- Python 3.14 desinstalado para evitar competição no PATH

### Artefatos criados

- Repositório `paivapereira/lgpd-policy-review` no GitHub
- README.md inicial (commit 68e69c5 via servidor GitHub)
- CLAUDE.md raiz com 74 linhas, hash 522229b
- docs/process/learning-log.md (este arquivo)
- Pasta de trabalho `C:\Users\joaoguilherm.pereira\dev\`

### Validações empíricas

Após push do CLAUDE.md, dois testes na extensão Claude Code do VS Code:

**Teste 1 — recall das regras imutáveis.** Pergunta: "Quais são as
regras imutáveis deste projeto?". Agente localizou CLAUDE.md via
Glob, leu o arquivo, citou linhas específicas (`CLAUDE.md:36-44`,
`CLAUDE.md:40`, `CLAUDE.md:42`, `CLAUDE.md:44`), traduziu para PT
respeitando regra de idioma de output, manteve identificadores
técnicos em inglês (`requires_human=true`, `policy_schema_version`,
`LGPD-Art-7-I`). Aderência total.

**Teste 2 — adherence sob pressão.** Pedido: "Vamos adicionar
Flask". Agente reconheceu que CLAUDE.md:27 lista Flask como
alternativa que requer ADR explícito; suspendeu execução; pediu
ADR; questionou caso de uso confrontando com arquitetura
descrita no README; sugeriu FastAPI como alternativa coerente com
async stack já declarado. Pushback comportou-se exatamente como
prescrito. Auto-memory atualizada para reforçar padrão.

### Próximo passo

ADR-0001 documentando o bootstrap (decisões de setup, escolha
da stack canônica, três regras imutáveis com racional). Estrutura
`docs/adr/` ainda não existe — criar junto.

### Pendências (não bloqueantes)

- Captação de orientador na UTFPR (prazo crítico, 2 semanas)
- `.python-version` na raiz fixando 3.12.7
- Branch protection em main no GitHub
- `~/.claude/CLAUDE.md` user-scope com preferências cross-projeto---

## 2026-05-02 — adr-0001-d5-provenance

### Conceitos da prova exercitados

**Domínio 5 — Context Management & Reliability (15%)**

- **Provenance verification em ação.** Padrão de trabalho aplicado
  meta-conversacionalmente: rascunho do ADR-0001 marcado com
  `[verificar]` em pontos onde Chat inferiu justificativa em vez
  de recuperar do registro real. Após validação via
  `conversation_search` sobre Sessão #01 e #02, três justificativas
  reescritas antes do commit (MIT, FastMCP, decisão 6).
- **Anti-padrão por contraste.** Output confiante fabricado para
  preencher gap em vez de explicitar incerteza é o anti-padrão
  central que o ADR-0001 evitou. Mesmo padrão vai aparecer no
  design do code review system: findings sem clause ID rejeitados
  por validação, confidence scoring vs sentiment como proxy
  inválido.
- **Context budget e densidade de relevância.** Discussão sobre
  lost-in-the-middle, densidade > tamanho absoluto, custo de
  redundância no project knowledge. Recomendação adotada:
  `proposta-tcc.md` tem redundância com o exam guide PDF na
  seção "Mapeamento aos 5 domínios" e merece enxugamento futuro.
  Ideia de `docs/CONTEXT.md` como manifest curto adiada para
  quando project knowledge ficar pesado.

### Conceitos fora do escopo da prova

- **ADRs e formato Nygard.** Origem (Michael Nygard, 2011), cinco
  seções clássicas (Title, Status, Context, Decision, Consequences),
  versão expandida para decisão composta (sub-decisões inline com
  decisão + rationale + consequência cada). Comparação com MADR
  (Markdown ADR): MADR brilha quando há trade-off comparativo real
  entre opções consideradas; Nygard expandido brilha para registros
  agregados como bootstrap.
- **`conversation_search` como ferramenta de meta-chat.** Permite
  recuperar contexto de sessões anteriores dentro do mesmo project.
  Ferramenta de UI da Claude Chat, não cobre nenhum task statement
  da prova.

### Decisões tomadas

- **Formato de ADR adotado: Nygard expandido.** Decisão composta
  estruturada como subseções por sub-decisão, cada uma com decisão
  + rationale + consequência inline. MADR fica reservado para
  futuras ADRs com trade-off comparativo real.
- **ADR-0001 do bootstrap finalizado.** Seis sub-decisões:
  monorepo + MIT, stack canônica, idiomas, três regras imutáveis,
  workflow git, direct-commit allowlist permanente.
- **Direct-commit allowlist permanente.** Apenas
  `docs/process/session-handoff.md` e `docs/process/learning-log.md` vão direto em
  `main`. Não é exceção de bootstrap; é convenção permanente
  baseada em ausência de signal de revisão. Adicionar terceiro
  arquivo à allowlist requer ADR específico.
- **Política `policy/` terá licença separada.** MIT cobre código;
  conteúdo jurídico-textual ficará sob CC-BY (provável), decidido
  em ADR específico antes de v1.0 ou abertura pública do repo.
- **ADRs aprovados sobem ao project knowledge.** Curadoria via
  `docs/adr/INDEX.md` quando passar de ~15 ADRs.
  - **Cláusula POL-000 de definições declarando vocabulário de classes
  de dados.** Sete classes em v0.1.0. Compartilhada entre
  `structured_context` e `applicability_scope`. Versionada com o
  schema da política.
- **Output do sistema: Report JSON consolidado por execução.**
  Definido como saída estrutural, não feature acessória. Schema
  explícito vai no spec. Agregação inter-execução (mapa de dados
  longitudinal) deferida com condição clara para revisitar.

### Artefatos criados

- `docs/adr/` estrutura criada.
- `docs/adr/0001-bootstrap.md` (267 linhas), mergeado via PR padrão
  (squash + delete-branch). PR #3.
- ADR-0001 subido ao project knowledge para contexto autoritativo
  futuro.
- Rascunho v1 do ADR (com três `[verificar]`) → v2 final
  (justificativas reescritas em três pontos). Trail da revisão
  registrado na própria seção 6 do ADR ("Why this is not a
  bootstrap exception").

### Validações empíricas

- **`conversation_search` recuperou Sessão #02 sobre MIT vs Apache.**
  Resultado: decisão consciente com três fatores ponderados (sem
  intent comercial, sem patentes, MIT em whitelist Adobe), não
  default. Inferência genérica do rascunho substituída pelo
  raciocínio real.
- **`conversation_search` recuperou Sessão #01 sobre origem do
  stack.** Resultado: FastMCP entrou como parte do pacote canônico
  recomendado para projetos multi-agent em Python (junto com
  `claude-agent-sdk`, `pydantic`, `inspect-ai`), não como vencedor
  de comparação isolada contra raw SDK. Inferência comparativa do
  rascunho substituída por adoção em pacote.
- **Leitura cruzada do session-handoff exibiu contradição na
  decisão 6 do rascunho.** "Primeiro PR mergeado via squash" no
  handoff implica que CLAUDE.md inicial foi via PR, não direct
  commit; o rascunho descrevia uma "exceção do bootstrap" que não
  existia. Decisão reescrita como convenção permanente.
- **Segundo passe do fluxo PR validado.** ADR-0001 mergeado via
  branch `docs/adr-0001-bootstrap` → PR → squash → delete. Mesma
  mecânica da sessão 1; consistência da decisão 5 confirmada.

### Próximo passo

Decidir entre duas frentes para a sessão 3:

- **(a) Primeiro MCP server `lgpd-policy-reader` em FastMCP.**
  Cobre Domínio 2 (Tool Design & MCP Integration, peso 18%)
  inteiro numa só implementação: tool descriptions diferenciadas,
  structured error responses, tool_choice forçado, `.mcp.json`
  project-scope com `${VARS}` expandidos, MCP resources como
  catálogo navegável.
- **(b) Estrutura inicial de `policy/` com schema YAML mínimo.**
  Cobre mais Domínio 5 (provenance, schema versioning,
  policy_schema_version compatibility) e tem componente jurídico
  fora do escopo da prova.

Recomendação atual: **(a)**, por densidade de conceitos da prova
por hora investida. Decisão fica para abertura da sessão 3.

### Pendências (não bloqueantes)

- Captação de orientador na UTFPR (prazo crítico,
  ~13 dias remanescentes)
- `.python-version` na raiz fixando 3.12.7
- Branch protection em main no GitHub
- `~/.claude/CLAUDE.md` user-scope com preferências cross-projeto
- Considerar enxugamento futuro da seção "Mapeamento aos 5 domínios"
  da `proposta-tcc.md` para reduzir redundância com o exam guide

### Ajustes pós-revisão D2 (Domínio 2 — Tool Design & MCP Integration)

- **D2.2 — catálogo navegável é resource, não tool.** Política inteira
  vira resource (`policy://catalog`, URI estável, GET-like, sem args);
  acesso pontual a cláusula vira tool (`get_clause(id)`) ou resource
  parametrizado (`policy://clauses/{id}`). Confundir as duas primitivas
  é o erro mais comum de quem aprendeu MCP só por implementação.
- **D2.5 — `tool_choice` tem três modos, não dois.** `auto` (modelo
  decide), `any` (força alguma tool, útil para garantir output
  estruturado), e `{"type": "tool", "name": "X"}` (força tool
  específica, útil em primeiro passo de pipeline determinístico).
- **D2.4 — `.mcp.json` viaja com o repo, mas execução exige opt-in
  local.** Cada desenvolvedor que clona o repo aprova individualmente
  a execução do server na primeira vez (proteção contra `command`
  malicioso). Configuração ≠ execução automática. Distrator clássico
  da prova: "configurando em `.mcp.json` o server roda automaticamente
  para todo dev que clona". Falso.
- **D2.5 — Edit é default, Read+Write é fallback consciente.** Edit é
  mais seguro porque falha visivelmente em mismatch em vez de produzir
  arquivo corrompido. Justifica fallback para Read+Write apenas quando
  (a) match genuinamente ambíguo, ou (b) edição estrutural demais para
  match cirúrgico. Usar Read+Write "porque é mais simples" é
  anti-padrão.

## Sessão 3 — Arquitetura conceitual do lgpd-policy-reader: quatro decisões

**Data:** 2026-05-04

### Conceitos da prova exercitados

- **D2.1 — tool descriptions sem overlap.** Teste de mesa para descrição
  saudável: "se eu apagar o nome e ler só a descrição, dá para inferir o
  nome unicamente?". Aplicado para eliminar `find_related_law_articles`
  (nome ambíguo, descrição inevitavelmente sobreposta com `get_clause`)
  e substituir por `find_clauses_by_law_article` (busca reversa
  estruturada por artigo da lei → cláusulas da política).

- **D2.2 — resource vs tool, critério correto.** O critério é
  **mecanismo de acesso**, não propriedade do objeto: resource é
  endereçável por URI estável, idempotente, sem side-effects, acessado
  por `resources/read`; tool é invocação computacional dentro do
  agentic loop, com input schema, output schema e `isError`.
  Caracterizar como "passivo vs ativo" parece descrever o mesmo, mas
  falha em casos de borda — exatamente onde a tensão `get_clause`
  vs `policy://clauses/{id}` aparecia. Eliminado o resource
  parametrizado por redundância com a tool.

- **D2.3 — `isError` flag e três classes que parecem erro.**
  Validation error (input mal formado, agente reformula),
  business error (input válido, regra de negócio falhou — pode ser
  retryable como CLAUSE_DEPRECATED com successors no `details`, ou
  não-retryable como CLAUSE_NOT_FOUND), e system error (transiente
  de infraestrutura). Crucialmente: **empty result não é erro**
  (lista vazia com `isError: false` é informação acionável) e
  **indeterminate não é erro** (resposta legítima sobre limites do
  que análise estática consegue concluir).

- **D5 — schema versioning vs content versioning como dois campos.**
  Schema version é contrato com consumidores e muda raramente
  (forma dos campos); content version é trilha de auditoria e muda
  toda vez que cláusula é revista. Misturar leva a "bumpamos schema
  major porque mudou um texto", envenenando a semântica do
  versionamento. Decisão: dois campos no header do YAML
  (`policy_schema_version` e `policy_version`), e
  `policy://schema-version` resource carrega ambos +
  `compatible_schema_range` para fail-fast handshake.

- **D5 — stable identifiers e regra unidirecional.** `clause_id`
  pode ser adicionado, pode virar tombstone quando o referente
  externo desaparece, mas **não pode ser renomeado** por motivação
  estética interna. Tombstone preserva a verdade histórica: agente
  encontrando id antigo num log expõe a divergência (id deprecated,
  successors, motivo), não reescreve retroativamente a decisão
  original — fazer reinterpretação automática é revisionismo
  histórico. Em sistema regulado, isso é problema mais sério do
  que o erro original.

- **D5 — escalation pattern via indeterminate +
  requires_human_review.** Quando análise estática não consegue
  decidir (dependência de estado runtime ou comportamento
  upstream), tool retorna `verdict: "indeterminate"` com
  `verification_scope` indicando a dimensão que requer
  verificação manual. Equivalente, no domínio de code review do
  projeto, ao handoff estruturado que o exam guide cita para
  customer service (customer ID + root cause + recommended
  action). Mesmo padrão: três caminhos, não dois.

- **D5 — error propagation por categoria.** Três categorias com
  `isRetryable` explícito permitem ao orchestrator decidir caminho
  diferente por classe: validation → reformule input; business
  não-retryable → registre veredito e siga; business retryable
  (deprecated) → substitua argumento; system → backoff/escalação.
  Sem essa estrutura, agent fica num try/except genérico que perde
  o sinal.

- **Ponte D1.4 ↔ D2 — programmatic enforcement vs prompt-based
  guidance.** O design de `check_applicability` com
  `structured_context` estruturado (não texto livre) é o mesmo
  padrão do exam guide: `get_customer` antes de `process_refund`,
  hook PostToolUse normalizando timestamps no server. Sempre que
  confiabilidade importa mais que flexibilidade do raciocínio, a
  lógica migra do prompt para o código.

  - **D5 — scratchpad files + provenance.** Sistemas multi-step com IA
  precisam de artefato durável de execução. Output do agente é o
  arquivo estruturado (Report JSON), não o conteúdo da última
  mensagem. Carrega versão de schema e política consultadas para
  reprodutibilidade. Sem isso, achados ficam reféns do contexto
  efêmero do agente.

- **D4 — structured output via tool_use forçado.** Report JSON sai
  melhor com tool `emit_report` cujo input schema é o objeto desejado
  do que com prompt pedindo "responda em JSON". Validação garantida
  pelo schema; sem isso, validation-retry loop torcendo o JSON sair
  bem formado.

### Conceitos fora do escopo da prova

- **Conformidade declarativa vs efetiva como fronteira do sistema.**
  Análise estática de PR vê: declaração de base legal, transformações
  visíveis no código, estrutura de controle. Não vê: consentimento
  runtime, hash em pipeline upstream, retenção em outro serviço. O
  sistema entrega o primeiro tipo; o segundo é DPIA / auditoria
  operacional, escopo diferente. Reframe nominal explícito evita
  prometer o que não pode entregar.

- **Modelagem de escopo (PR-scoped vs system-wide).** PR-scoped
  parece menos ambicioso mas é estritamente mais preciso — agente
  analisa sempre o mesmo tipo de unidade com o mesmo contexto
  disponível. System-wide auditing exige improvisar análise
  sistêmica que análise estática não tem como fazer bem; é
  exponencialmente mais caro e menos confiável.

- **Hierarquia legislativa brasileira para modelagem de
  `article_source`.** Título → Capítulo → Seção → Artigo →
  Parágrafo / Inciso → Alínea. Item (subdivisão de alínea) existe
  em algumas leis tributárias mas não na LGPD; ficou fora de
  v0.1.0. Inciso modelado como inteiro (semântica), não como
  numeral romano (renderização) — evita bugs de comparação
  lexicográfica vs numérica.

- **Convenção de URI scheme em MCP.** Anthropic não publica padrão
  fechado; convenção é "scheme descritivo do domínio"
  (`note://`, `config://`, `stock://`, `file://`). Único reservado
  é `ui://` (SEP-1865, MCP Apps Extension, fora do escopo).
  Adotado `policy://` para o servidor e `doc://internal/` como
  convenção do projeto. Validado via web search durante a sessão.

  ### Refinamentos de design (final da sessão)

- **Política declara classes, não campos; exigências, não técnicas.**
  PII não é propriedade do campo isolado, é do contexto de tratamento.
  LGPD evita classificação rígida tipo "campo X é PII"; nossa política
  segue o mesmo princípio. Vocabulário de classes (sete em v0.1.0) é
  declarado em cláusula POL-000 de definições e compartilhado entre
  classificador e cláusulas — sem shared schema, sistema produz
  outputs sintaticamente válidos mas semanticamente quebrados.
  Técnicas de anonimização (hash, k-anonymity, etc.) ficam em
  diretrizes internas linkadas, não na política — política exige
  resultado, técnica decide como.

- **Sistema produz Report JSON consolidado por execução.**
  Agregação intra-execução: 14 pontos de tratamento analisados → 1
  relatório estruturado anexado ao PR. Estrutura: `report_id`,
  versões de schema e política consultadas (provenance),
  `scope`, `summary` agregado, `findings` detalhado.
  Implementação natural via tool_use forçado com schema explícito
  (D4 — structured output). Relatório como scratchpad durável de
  execução (D5) — auditável post-hoc, reprodutível, pesquisável.

- **Agregação longitudinal (mapa de dados cross-PR) fica deferida.**
  Coisa diferente do relatório por execução. Custo alto: storage
  persistente entre rodadas, reconciliação com mudanças retroativas,
  versionamento de findings sob políticas distintas, audiência
  diferente (DPO/auditoria vs dev/revisor). Em escopo de TCC, vira
  cilada de scope creep. Forma boa de extender no futuro: segundo
  produto que consome relatórios do primeiro como input batch — não
  feature adicional do primeiro. Padrão coordinator-subagent em
  versão batch (D1, ressonância distante). Condição para revisitar:
  pipeline em produção ≥3 meses + demanda explícita de DPO por
  inventário cross-PR recorrente.

### Decisões tomadas

- **Schema YAML v0.1.0 da Política fechado.** Estrutura completa
  acordada incluindo dois campos de versão, `clause_id` opaco com
  prefixo `POL-`, `article_source` como lista hierárquica
  completa, sub-ids em requirements e exceptions, ciclo de vida
  com tombstone (`status: deprecated` + `successors` +
  `effective_until` + `deprecation_reason`).

- **Resources expostos: dois.** `policy://catalog` (índice com
  `clause_id`, `title`, `status`, `article_sources_summary`,
  `successors` quando deprecated) e `policy://schema-version`
  (com `compatible_schema_range`). `policy://clauses/{id}`
  eliminado por redundância — discussão registrada em ADR-0002
  para futuro debate caso browseability humana vire requisito.

- **Tools expostas: três.** `get_clause`,
  `find_clauses_by_law_article` (busca reversa estruturada),
  `check_applicability` com `structured_context` de quatro
  campos. `list_exceptions` eliminada (redundante com
  `get_clause`).

- **Quatro vereditos no output do `check_applicability`.**
  `compliant`, `violation_candidate`, `indeterminate`,
  `not_applicable`. Indeterminação carrega `verification_scope`
  com a dimensão a verificar manualmente.

- **Contratos de erro: três categorias.** Validation, business,
  system. `errorCode` em inglês (constante estável), `message`
  em português (humano). `isRetryable` explícito. Empty e
  indeterminate **não** são erros. Deprecated tem comportamento
  distinto em `get_clause` (dado válido com tombstone) vs
  `check_applicability` (erro retryable com successors no
  `details`).

- **Escopo do sistema: PR-scoped + conformidade declarativa.**
  Sistema é triagem por ponto de tratamento no diff de PR, não
  auditoria sistêmica. Honestidade epistêmica explícita sobre
  o que análise estática consegue concluir.

- **Roadmap fica em seção dedicada do ADR-0002, não em doc
  separado.** Heurística para revisitar: criar
  `docs/roadmap.md` consolidado quando deferimentos cruzarem
  ≥3 ADRs.

### Artefatos criados

Nenhum arquivo de código nem documento committado — sessão
inteira de design conceitual. Os artefatos derivados (spec
em `docs/specs/lgpd-policy-reader.md` e ADR-0002) serão
redigidos na sessão 4. As decisões ficam registradas no
session-handoff até serem absorvidas pelos artefatos.

### Validações empíricas

- **Validação por perguntas socráticas, rodada 1.** Stable
  identifiers (mecânica de tombstone) e resource vs tool. Em
  ambos os casos, a intuição estava no caminho certo mas o
  vocabulário inicial estava errado: a regra unidirecional
  ficou implícita, e "passivo vs ativo" descrevia o objeto
  em vez do mecanismo de acesso. Reframes absorvidos.

- **Validação por perguntas socráticas, rodada 2.** Cenário
  hipotético de divisão de cláusula (LGPD-7-IX → IX-A + IX-B)
  com 12 referências externas. Mecânica de tombstone +
  successors saiu correta. Hesitação no "imagino" do final
  pegou exatamente o ponto de não-revisionismo histórico —
  refinamento explícito consolidado.

- **Reframe de escopo emergente da pergunta do usuário.** A
  dúvida "ele indica quais dados podem ou não ser coletados?"
  expôs ambiguidade que o sistema fingia ter resolvido.
  Resposta forçou nominar conformidade declarativa vs
  efetiva, separar code review de DPIA, e explicitar os
  quatro vereditos com indeterminate como classe legítima.
  Reframe condicionou o output do `check_applicability`.

- **Web search por URI scheme MCP confirmou ausência de
  padrão fechado.** `policy://` adotado por convenção do
  projeto, MCP-friendly mas não normativo.

### Próximo passo

Sessão 4: redação de `docs/specs/lgpd-policy-reader.md` (primeiro)
seguida de `docs/adr/0002-lgpd-policy-reader-architecture.md`
(segundo, formato Nygard expandido com seção de deferimentos
explícita). Cada um vai por PR padrão. ADR sobe ao project knowledge
após merge. Sessão 5 começa implementação em FastMCP.

### Pendências (não bloqueantes)

- Captação de orientador na UTFPR (~12 dias remanescentes — se até
  quarta-feira não houver e-mail enviado, vira item 1 da sessão 4
  antes da redação)
- `.python-version` na raiz fixando 3.12.7
- Branch protection em main (depende de migração para Team)
- `~/.claude/CLAUDE.md` user-scope com preferências cross-projeto

- **(novo) Vocabulário de classes de dados declarado em cláusula
  POL-000 de definições.** Sete classes em v0.1.0:
  `dados_de_identificação`, `dados_de_contato`, `dados_de_navegação`,
  `dados_comportamentais`, `dados_sensíveis`, `dados_de_localização`,
  `dados_financeiros`. Vocabulário compartilhado entre `data_categories`
  do `structured_context` e `applicability_scope` das cláusulas. Política
  declara classes e exigências; técnica de implementação (ex: hash
  SHA-256) vive em diretrizes internas linkadas via
  `internal_directive_links`, não na política.
- **(novo) Output do sistema é Report JSON consolidado por execução.**
  Estrutura inclui `report_id`, `policy_schema_version`,
  `policy_version`, `scope` (ex: `pr-127`), `summary` agregado por
  veredito, `findings` lista detalhada por ponto de tratamento.
  Agregação intra-execução, não inter-execução. Mapa de dados
  longitudinal (cross-PR) fica deferido — registrado em ADR-0002.

  ### Adendo de fim de sessão — visão sistêmica e tensões resolvidas

Solicitação tardia do aluno por esboço de visão sistêmica revelou
cinco tensões entre proposta-tcc.md original e decisões da sessão #03.
Resolvê-las exigiu reabrir conceitualmente partes do desenho de
subagentes e do output operacional do sistema.

#### Conceitos da prova exercitados (Domínio 1)

- **D1.2 + D1.3 — single responsibility per agent.** Critério prático
  para decidir granularidade de subagentes: se a responsabilidade não
  cabe em uma frase sem "e", divide. Tools restritas focam o
  raciocínio do subagente e reduzem alucinação. Aplicado para quebrar
  o "claude-analyzer" monolítico da proposta original em três
  subagentes (Classifier, Matcher) + Reporter, e adicionar Triager
  para etapa 0. Resultado: cinco subagentes com fronteiras nominais
  claras, mais alinhado com o coordinator-subagent canônico do que
  o desenho original.

- **D1.4 — programmatic enforcement vs subagente decisor.** Etapa 0
  de triagem de relevância poderia ser hook PreToolUse (enforcement
  determinístico) ou subagente Triager (decisão semi-semântica).
  Critério aplicado: hook é apropriado para regras puramente
  sintáticas/determinísticas; quando há julgamento envolvido (paths +
  keywords + algum raciocínio), trabalho é de subagente. Hook ficou
  reservado para casos onde compliance não pode ter falha
  probabilística.

#### Refinamentos de design

- **Classificação pertence à Política, não ao sistema.** Tentativa
  inicial do aluno de definir vereditos como "pode/consent/anon/
  proibido" foi reframe corrigido: essas categorias **vivem nas
  cláusulas via `requirements`**, não em campo independente. Vereditos
  do agente reportam o resultado de comparar código contra
  exigências da cláusula. Anti-padrão evitado: duplicação de
  informação entre fonte de verdade (cláusula) e cache (campo
  global). Princípio: quando dois lugares parecem ter "a mesma"
  informação, um é fonte e outro é derivação — declare qual é qual,
  ou eles divergem em produção.

- **Severidade eliminada do MVP.** Sem critério defensável para
  CRITICAL/HIGH/MEDIUM/LOW em escopo de TCC com benchmark sintético.
  Severity-classifier subagente sai. Pode entrar como evolução
  pós-validação empírica.

- **Output operacional posicionado como informativo.** Report posta
  como inline comments, não bloqueia merge. Princípio aplicado:
  sistemas de IA que bloqueiam ações precisam de calibração empírica
  de FPR, não apenas correção formal. MVP em 8-10 semanas com
  benchmark de ~200 snippets não tem dados para defender bloqueio.
  Posicionamento honesto blinda contra crítica de banca e abre
  caminho para evolução incremental.

- **Fluxo de execução em cinco etapas (0-4).** Triagem → detecção
  determinística → classificação estruturada → matching contra
  política → agregação no Report. Cada etapa mapeada para um
  subagente específico, exceto coordinator que orquestra.

#### Decisões tomadas (adendo)

- Cinco subagentes nomeados: Triager, Detector, Classifier, Matcher,
  Reporter. Severity-classifier e fix-proposer fora do MVP.
- Etapa 0 como subagente Triager, não hook PreToolUse.
- Report informativo no MVP; bloqueio condicional como evolução
  pós-validação empírica.
- Classificação pode/consent/anon/proibido vive nas cláusulas
  (requirements), não em campo separado.
- AEP fora do MVP; recognizers brasileiros mantidos.

#### Mudança de plano para sessão #04

Plano original era redigir spec do `lgpd-policy-reader` + ADR-0002.
Reordenado: sessão #04 redige `docs/architecture-overview.md`
(visão sistêmica do projeto inteiro). Spec + ADR-0002 vão para
sessão #05. Razão: aluno mostrou estar raciocinando sobre o
componente `lgpd-policy-reader` em isolamento, e isso explicou tanto
a confusão sobre `check_applicability` quanto a etapa 0 que apareceu
tarde. Ancorar visão sistêmica antes de detalhar componentes
preserva consistência conceitual.

#### Reflexão metodológica

Esse padrão — aluno levanta dúvida tarde na sessão que reabre
desenho — é sinal de que o ritmo de "decisões concretas em sequência"
funciona melhor quando intercalado com "checagem de visão sistêmica"
a cada N decisões. Próximas sessões podem incorporar momento
explícito de "step back and check the whole picture" antes da
redação de artefatos longos.

---

## 2026-05-05 — sessao-04-architecture-proposta-sync

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1.6 Task Decomposition aplicado em duas dimensões.** Primeiro
  no design da pipeline do sistema: prompt chaining (pipeline fixa
  de cinco subagentes em ordem determinística) escolhido sobre
  decomposição adaptativa porque o problema é cobertura sistemática
  de pontos de tratamento em diff (revisão multi-aspecto previsível),
  não investigação aberta. Segundo no design do cronograma do
  próprio TCC: meio termo entre "spec-tudo-primeiro" (waterfall com
  nome de SDD) e "um-por-vez-rígido", agrupando specs por categoria
  coerente (dois MCP servers juntos, cinco subagentes juntos) com
  ciclo curto specify→implement por categoria. Conceito comum nos
  dois: granularidade de decomposição é função do problema e do
  feedback disponível, não da sofisticação aparente.

- **D1.2 + D1.3 Coordinator-subagent + Single Responsibility.** Cinco
  subagentes nomeados com responsabilidade nominal sem "e", tools
  restritas, system prompt focado. Materializado em matriz
  tools × subagentes na seção 5.7 do architecture-overview — coluna
  em branco do Coordinator (só despacha) e linha em branco de
  Write/Edit/Bash (sistema é apenas leitor) são deliberadas e
  protegidas por regra de ADR para qualquer alteração.

- **D1.4 Programmatic Enforcement vs Subagent Decision.** Reaplicado:
  etapa 0 (triagem de relevância) mora como subagente Triager, não
  como hook PreToolUse, porque envolve julgamento semi-semântico.
  Hook fica reservado para enforcement determinístico genuíno (ex:
  validar formato JSON do Report antes de `emit_report` retornar).

**Domínio 2 — Tool Design & MCP Integration (18%)**

- **D2.6 Tool Authorization formalizado em matriz.** Matriz 5.7 do
  architecture-overview é spec de tool authorization que vai virar
  configuração de AgentDefinition na implementação. Princípio:
  cada subagente recebe apenas tools relevantes ao papel — `emit_report`
  exclusiva ao Reporter, `lgpd-policy-reader` exclusivo ao Matcher,
  `semgrep-runner` exclusivo ao Detector. Restrição materializa
  invariantes arquiteturais (ex: Detector não pode "espiar" cláusulas
  para inferir veredito).

- **D2.2 MCP Resources vs Tools.** Política aparece duas vezes no
  mesmo MCP server: como resource (`policy://catalog` — GET-like,
  navegável, sem args) e como tool (`get_clause` — parametrizada,
  ação ativa). Quando ambos cabem, resource é catálogo, tool é
  acesso pontual.

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- **D3.1 CLAUDE.md design — heurística "all-session vs on-demand".**
  Aplicada na decisão de adicionar seção "Working methodology" curta
  ao CLAUDE.md em vez de detalhar SDD lá. Princípio operacional ("se
  pediram para implementar, verifique se há spec") é all-session;
  detalhe de SDD (quatro fases, framework bibliográfico) é on-demand
  e fica em architecture-overview ou em skill futuro. CLAUDE.md
  prescreve comportamento; architecture-overview descreve metodologia.

**Domínio 5 — Context Management & Reliability (15%)**

- **D5 Provenance + Reliability via fronteiras explícitas.** Seção 7
  do architecture-overview ("Fronteiras explícitas") declara o que o
  sistema *não é* e *não pretende provar*. Reliability inclui
  honestidade sobre limites, não só acurácia dentro deles. Sistema
  reliable é o que diz `indeterminate` quando indeterminado, não o
  que chuta `compliant` para parecer útil.

- **D5 Lost-in-the-Middle aplicado inversamente.** Decisão de não
  postar inline comment para findings `compliant` ou `not_applicable`
  (seção 6.1 do architecture-overview): se o PR enche de comments
  confirmando conformidade, o revisor humano para de ler — e o
  `violation_candidate` real fica perdido no meio. Heurística
  "informação importante no início e no fim, ruído no meio é
  descartado" se aplica ao revisor de PR exatamente como ao modelo
  lendo contexto longo.

- **D5 Scratchpad/Structured Summary entre sessões.** Validação
  empírica: abertura desta sessão fez "primeira leitura ao abrir
  nova conversa" do session-handoff conforme convenção do projeto.
  Padrão recomendado pelo Domínio 5 — começar nova sessão com
  summary estruturado é mais confiável que tentar `--resume` com
  tool results stale.

### Decisões tomadas

- **`docs/architecture-overview.md` redigido e mergeado** (PR via
  fluxo padrão). Estrutura final em sete seções: visão de negócio,
  três camadas com mermaid, fluxo de execução com mermaid,
  componentes mapeados, subagentes detalhados (5.1 a 5.6 + matriz
  5.7), posicionamento operacional, fronteiras explícitas. Glossário
  de cinco termos (MCP, Política versionada, Subagente, Tools, Hook)
  e seção "Como ler este documento" antes da seção 1, para servir
  leitor externo (orientadora).

- **Frase de negócio canônica fixada.** "Sistema de code review
  automatizado em pull requests que verifica conformidade do
  tratamento de dados pessoais com uma Política versionada derivada
  da LGPD." Aparece idêntica no architecture-overview, na
  proposta-tcc2 e no README — mesmo objeto, mesma descrição, três
  lugares.

- **Spec-Driven Development adotado como metodologia formal.**
  Decisão fundamentada em web search confirmando estado da arte
  pós-cutoff: SDD com Claude Code virou padrão estabelecido em
  2025-2026 (guia oficial Anthropic, GitHub Spec Kit, frameworks
  community). Cobre os Domínios 1, 3 e 4 da prova simultaneamente
  no uso canônico dos primitivos. Argumento dual: alinha-se ao
  caráter especificativo do problema e mitiga risco de retrabalho
  por decisão tomada cedo demais. Ressalva específica registrada:
  como advogado, a tendência do aluno é over-specify; SDD precisa
  ser servo da clareza, não fim em si.

- **Cinco tensões da sessão #03 absorvidas no architecture-overview**
  como decisões fechadas: severidade fora do MVP, cinco subagentes
  single-responsibility, Triager como subagente (não hook),
  classificação pode/consent/anon/proibido nas cláusulas (não em
  veredito), AEP fora do MVP. Output como informativo, não bloqueia
  merge.

- **Cronograma reorganizado por categoria coerente.** Em vez de
  spec-tudo-primeiro (risco de waterfall) ou um-por-vez-rígido
  (sem revisão holística), fases de Specify agrupam componentes
  que se beneficiam de revisão conjunta: semana 1 = specs dos dois
  MCP servers + ADR-0002; semana 3 = specs dos cinco subagentes;
  implementação imediatamente após cada bloco de spec.

- **`docs/process/proposta-tcc2.md` redigido e mergeado** (PR via fluxo
  padrão). Reescrita do zero a partir do architecture-overview,
  removendo enquadramento prova-primeiro/TCC-subproduto da
  proposta-tcc.md original (preservada fora de docs/ como
  referência interna). Estrutura: tema, contextualização, objetivo
  geral, seis objetivos específicos, justificativa, arquitetura
  proposta (com link para architecture-overview), metodologia SDD,
  escopo e fronteiras, cronograma de seis semanas, resultados
  esperados, referências preliminares. Modalidade de entrega
  identificada corretamente como "Relatório Técnico de Ferramenta
  ou Produto de Software" (modelo institucional UTFPR Câmpus
  Dois Vizinhos).

- **CLAUDE.md e README sincronizados com arquitetura
  pós-sessão #04** (PR via fluxo padrão). CLAUDE.md: recognizers
  brasileiros corrigidos (saiu RG, entraram NIS/PIS, título de
  eleitor, CNS-saúde); immutable rule 1 reformulada em torno de
  "no fabricated certainty + quatro vereditos" em vez de
  "escalation em conflito Lei vs diretriz" (vocabulário antigo
  pressupunha desenho que não foi adotado); immutable rule 2
  atualizada para clause_id opaco com prefixo POL- e explicação
  do papel separado de article_source; immutable rule 3 expandida
  para explicar dois eixos independentes de versionamento; seção
  Working methodology nova apontando para docs/specs/ e docs/adr/;
  status flags atualizados. README: frase de negócio canônica,
  arquitetura em três camadas explicitada, stack expandida com
  Semgrep e Inspect AI, link para architecture-overview.

- **E-mail para Profa. Alinne Cristinne Corrêa Souza redigido**
  (envio agendado para 06/05). Tom direto e curto seguindo o
  padrão do e-mail de TCC1 do mesmo aluno. Anexos: proposta-tcc2
  e architecture-overview, ambos exportados em PDF a partir do
  GitHub.

### Artefatos criados

- `docs/architecture-overview.md` (PR mergeado)
- `docs/process/proposta-tcc2.md` (PR mergeado)
- `CLAUDE.md` reescrita parcial substantiva (PR mergeado)
- `README.md` reescrita parcial substantiva (PR mergeado)
- `proposta-tcc.md` original preservada fora de docs/ como
  referência de estudo (sem versionamento Git)

### Validações empíricas

- **Web search confirmou estado da arte de SDD com Claude Code
  pós-cutoff de janeiro/2026.** Anthropic publicou guia oficial,
  GitHub Spec Kit consolidado, ecossistema de plugins community
  (Pimzino, alexop.dev workflow). Hipótese inicial de "SDD não cai
  na prova" corrigida: SDD em si não é nomeado como conceito, mas
  é o uso canônico dos primitivos do Domínio 3 (CLAUDE.md, skills,
  commands) e do Domínio 1 (Task tool, subagent decomposition).

- **Inversão de planejamento da sessão validada empiricamente.**
  A sessão #03 fechou quatro decisões em sequência, e o aluno pediu
  esboço de visão sistêmica ao final, expondo cinco tensões. Adiar
  redação para sessão dedicada (decisão da sessão #03) provou-se
  correta: redigir architecture-overview *antes* da spec do
  lgpd-policy-reader gerou seis seções de detalhamento adicionais
  (subagentes, posicionamento operacional, fronteiras epistêmicas)
  que teriam sido pulados num spec de componente isolado.

- **Adendo de revisão pós-redação detectou três bugs no
  architecture-overview.** Releitura crítica antes do PR identificou:
  (1) inconsistência factual em 5.7 ("coluna em branco do Coordinator"
  com ✓ na linha "Despacho de subagentes"); (2) referência ambígua em
  4.1 ("(sessão 5)" sendo lida como "seção 5 deste documento"); (3)
  jargão de processo vazando ("sessão #02", "sessão #03" cinco vezes
  em doc destinado a leitor externo). Os três corrigidos antes do
  merge.

### Próximo passo

**Sessão 5 (próxima):** redigir specs dos dois MCP servers
(`lgpd-policy-reader` e `semgrep-runner`) + ADR-0002, conforme
cronograma da proposta-tcc2 (semana 1, fase Specify). Antes da
redação técnica, dois itens institucionais: enviar e-mail para
Profa. Alinne (agendado), e abrir PR enxuto se houver ajustes
finais necessários após primeiro contato com a orientadora.

### Pendências (não bloqueantes)

- Captação de orientadora (e-mail agendado para 06/05; mensagem
  WhatsApp como follow-up curto)
- Migração GitHub para Team (ativa branch protection)
- `~/.claude/CLAUDE.md` user-scope com preferências cross-projeto
---

## 2026-05-06 — sessão #05 — specs §1-§8 do policy-reader e _template emergente

### Conceitos da prova exercitados

**Domínio 2 — Tool Design & MCP Integration (18%)**

- **D2.1 Resource vs Tool — heurística operacional.** Heurística A: muta estado → tool. Heurística B: leitura por chave estável → resource. Heurística C: leitura por filtro complexo → tool. Caso `find_clauses_by_law_article` validou que mesmo com chave estruturada, ausência de identidade canônica + necessidade de validação rica + erro estruturado puxam a decisão para tool. Princípio extraído: "tem chave estável" é primeira aproximação; quando colide com input validation ou erro estruturado, tool ganha.

- **D2.2 Tool descriptions como prompt engineering.** Cinco elementos canônicos exercitados na redação de `get_clause`, `find_clauses_by_law_article`, `check_applicability`: verbo de ação no início, diferenciação explícita de tools similares (Use this when... Do not use this when... — for that, use `<other>`), formato e estrutura do output, condições de erro relevantes, side effects. Convenção fixada para o projeto: descriptions em inglês (modelo processa com mais densidade).

- **D2.3 isError flag e três classes de erro.** Validation (sintaticamente válido, semanticamente inválido, sempre não-retryable), business (regra de domínio rejeita, retryable conforme caso, com `details` rico carregando recovery), system (transiente, quase sempre retryable). Empty result não é erro. Indeterminate não é erro. Deprecated tem comportamento dual (sucesso em `get_clause`, erro retryable em `check_applicability`).

- **D2.4 inputSchema com especificação progressiva e vocabulário fechado.** `find_clauses_by_law_article` com required (`lei`, `artigo`) + opcional (`paragrafo`, `inciso`, `alinea`) modela busca hierárquica por prefixo de especificação. Vocabulário fechado violado = validation error com `accepted_values` em `details`; dado aberto sem correspondência = empty result.

- **D2.5 MCP resources reduzem exploratory tool calls.** `policy://catalog` como discovery sem invocação — agente lista resources, vê o índice, decide próxima ação sem chamar tool. `policy://schema-version` como handshake fail-fast antes de qualquer tool.

**Domínio 5 — Context Management & Reliability (15%)**

- **D5.1 Provenance/citations em vereditos.** `check_applicability` carrega `policy_schema_version` e `policy_version` em retornos de sucesso; `get_clause` e `find_clauses_by_law_article` não precisam (retrieval). Provenance é assimétrica entre retrieval e veredito.

- **D5.2 Escalation pattern com handoff estruturado.** Veredito `indeterminate` materializa o padrão do exam guide (customer ID + root cause + recommended action) via `verification_scope` com `dimension`, `prescribed_treatment`, `verification_target`. Sem handoff estruturado, "indeterminate" é honestidade vazia. Distinção crítica: `not_applicable` ≠ `indeterminate` (saber a resposta vs. não conseguir decidir).

- **D5.3 Stable identifiers + presentation layer separation.** Inciso modelado como inteiro (estrutura), renderização para numeral romano (apresentação). Mesmo princípio que rege `clause_id` opaco vs. `title` humano-legível: estrutura é para máquina, renderização é função de saída.

- **D5.4 Error propagation por categoria.** Três classes (validation/business/system) com `isRetryable` explícito permitem ao orchestrator rotear: validation → reformule input; business retryable → ajuste argumento; business não-retryable → registre veredito e siga; system → backoff.

- **D5.5 Internal consistency check em documentos longos.** Revisão sistemática §1-§8 detectou três contradições silenciosas (mecanismo de reload §3.1 vs §6.5; `POLICY_LOAD_FAILURE` na tabela vs. carga só no startup; `evidence` ambíguo entre input e output). Princípio meta: toda spec passa por revisão de coerência interna antes de implementação.

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- **D3.1 CLAUDE.md vs .claude/skills/ vs .claude/rules/.** Heurística canônica: sempre útil → CLAUDE.md (curto); útil só em fração de sessões → skill com `context: fork` e `allowed-tools`; útil só ao tocar certos paths → rules com `paths` em frontmatter. Aplicação: `_template.md` vai como skill `spec-author` (on-demand para autoria), não como CLAUDE.md (poluiria sessões de coding/refactoring/debugging).

- **D3.2 Project conventions encapsuladas em workflow.** Combinação de três primitivos do D3 — arquivo canônico (`docs/specs/_template.md`) + skill (`.claude/skills/spec-author/SKILL.md`) + referência via CLAUDE.md (uma linha apontando) — virou padrão de spec-authoring do projeto. Decisão de implementação ainda pendente para final da semana 2.

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1.1 Subagent tool restriction.** Matriz §5.7 do architecture-overview confirma: Matcher é único subagente com `policy-reader` no inventário. Restrição materializada via configuração de `mcp_servers` no AgentDefinition, não confiada à boa-fé do modelo. Casa com "preventing cross-specialization misuse" do exam guide.

- **D1.2 Tool descriptions inferem encadeamento.** Matcher não tem orquestração rígida — lê descriptions, vê que `find_clauses_by_law_article` produz `clause_id`, vê que `check_applicability` consome, encadeia. Tool descriptions bem desenhadas tornam sequência inferível pelo modelo sem regras explícitas.

**Domínio 4 — Prompt Engineering & Structured Output (20%)**

- **D4.1 Few-shot examples como anchors de comportamento.** Exemplos da seção "Exemplos" de cada tool servem como few-shot que vai literalmente para o prompt do Matcher: caso normal, variante de estado relevante (deprecated, indeterminate), erro modal. Não exaustivo — ilustrativo.

- **D4.2 Structured output via tool_use forçado.** `check_applicability` retorna veredito com schema explícito por variante (compliant, violation_candidate, indeterminate, not_applicable cada um com sua estrutura). Validação garantida pelo schema, sem validation-retry loop torcendo JSON sair bem formado.

### Conceitos fora do escopo da prova

- **SDD recursivo.** SDD bem feito tem estrutura recursiva: você especifica componentes seguindo princípios que foram especificados pelo próprio exercício de especificar. Princípios em formação durante redação, validados em segunda aplicação, consolidados em documento canônico apenas após validação. Loop de descobrimento → uso → consolidação.

- **Componente agnóstico ao conteúdo.** Renomeação de `lgpd-policy-reader` para `policy-reader` separou função (componente) de conteúdo (Política). Componente conhece schema; não conhece LGPD. Tese acadêmica fica defensável: arquitetura de policy-as-code para regimes de proteção de dados, com LGPD como caso real validado.

- **Schema-as-contract vs implementation-as-server.** Schema do artefato é contrato cruzado entre curador (jurídico) e implementação (server); separar contratos permite que mudar implementação não force revisar contrato. `policy/SCHEMA.md` é contrato; `docs/specs/policy-reader.md` é spec do server que serve o contrato.

- **Frame frontal em documentos lidos por LLM.** Início da spec (~150 palavras) molda como o resto é interpretado. Lost-in-the-middle empobrece o miolo. Critérios de aceitação no fim balanceiam o frame inicial.

- **Não-objetivos como proteção contra scope creep.** Função real de §7 não é "lista do que falta", é "decisão do que o componente decidiu não ser". Diferente de incompletude — é design.

- **Fronteira epistêmica vs não-objetivo.** Não-objetivo é decisão (poderia ser feito, decidiu-se não). Fronteira epistêmica é limite fundamental da abordagem (análise estática nunca consegue avaliar conformidade efetiva, não importa quanto trabalho).

### Decisões tomadas

- **Renomeação `lgpd-policy-reader` → `policy-reader`.** Componente agnóstico ao conteúdo. Cleanup de propagação para `architecture-overview.md`, `learning-log.md`, `session-handoff.md`, `proposta-tcc2.md`, `CLAUDE.md`, `README.md` agendado para sessão #06 via PR enxuto.

- **`docs/specs/policy-reader.md` v0.1.0 redigido e mergeado.** Oito seções fechadas — identidade e propósito, contrato com o artefato servido, resources expostos (2), tools expostas (3), contrato de erro, provenance e versionamento, não-objetivos e fronteiras, critérios de aceitação. PR via fluxo padrão.

- **`docs/specs/_template.md` v0.1.0 redigido e mergeado.** Esqueleto canônico derivado de `policy-reader.md`. Marcado como "em formação até validação na redação do `semgrep-runner.md`". Estrutura de oito seções estabilizada.

- **`policy/SCHEMA.md` stub criado.** Cinco linhas, status "em redação na semana 2", lista do que vai cobrir, link para `policy-reader.md`. Pasta `policy/` criada no repositório.

- **Escopo restrito da Política do MVP.** v0.1.0 cobre apenas duas dimensões avaliáveis por análise estática: `consent_required` e `anonymization_required`. Outras dimensões da LGPD (transfer restrictions, retention, direitos do titular, dados de menores, tratamento compartilhado) ficam fora do MVP. Registrado em `policy-reader.md` §7.2 nesta sessão; sync para `architecture-overview.md` e `proposta-tcc2.md` no PR de cleanup da sessão #06; trilha de auditoria em ADR-0002 (semana 1, sessão #08).

- **Resolução de P1 — estrutura de `verification_scope`.** Vereditos `indeterminate` carregam `dimension` (vocabulário fechado: upstream_state, runtime_behavior, external_system, human_review), `prescribed_treatment` (vocabulário fechado em SCHEMA.md, MVP cobre consent_required e anonymization_required), `policy_clause_ref` (clause_id), `verification_target` (texto livre em português gerado pelo componente).

- **Resolução de P2 — `declared_treatment` opcional rejeitado.** `inputSchema` não reserva slot para anotações declarativas futuras. Adicionar campo opcional comunica capacidade ao agente mesmo quando ignorado tecnicamente. Quando feature de anotações declarativas (deferimento ADR-0002) for implementada, será bump minor com semântica clara.

- **Resolução de P3 — ambiguidade em `find_clauses_by_law_article`.** Especificação progressiva via campos opcionais hierárquicos. Match por prefix sobre `article_source`. Lista vazia é resultado válido (não erro) quando especificação não corresponde a nenhuma cláusula operativa.

- **Resolução de P4 — `article_sources_summary`.** Forma exata empurrada para `policy/SCHEMA.md` da semana 2. Decisão entre lista de strings renderizadas vs. lista de objetos estruturados fica para o redator do schema. Estrutura interna canônica de `article_source` confirmada como objetos com inteiros (não numerais romanos).

- **Vocabulário de `lei` no MVP via header da Política.** Campo `accepted_law_identifiers` no header do arquivo YAML declara vocabulário aceito; componente valida em runtime. Coerente com tese de componente agnóstico ao conteúdo.

- **`clause_id` formato `POL-NNN`** (três dígitos zero-padded, regex `^POL-\d{3}$`). Decisão fechada na spec; herdada por `policy/SCHEMA.md`.

- **`evidence` e `verification_target` gerados pelo componente.** Mecanismo de geração (template, geração por modelo, híbrido) é decisão de implementação livre — Princípio 17 (spec descreve o quê, não como).

- **`POLICY_LOAD_FAILURE` removido da tabela de erros.** Política carregada apenas no startup (decisão §6.5); falha de I/O em runtime não ocorre. Tabela §5.4 fica internamente coerente.

- **Princípio do review pass spec ↔ architecture-overview.** §8.<final> de toda spec executa varredura no architecture-overview procurando decisões obsoletas ou contradições. Loop bidirecional, não duplicação.

### Artefatos criados

- `docs/specs/policy-reader.md` (v0.1.0, oito seções, mergeado)
- `docs/specs/_template.md` (v0.1.0, esqueleto canônico, mergeado)
- `policy/SCHEMA.md` (stub, mergeado)
- **26 princípios de spec-authoring em formação:**

  1. **Frame frontal** — início da spec (~150 palavras) molda como o resto é interpretado.
  2. **Função em uma sentença** — componente que não cabe em uma sentença ainda não está conhecido.
  3. **Schema fora, comportamento dentro** — componente referencia o schema do artefato servido, nunca duplica.
  4. **Resource é estado servido, não comportamento** — §3 limita-se a estrutura, semântica de leitura, casos de erro.
  5. **Sem erro de domínio é caso comum** — resources frequentemente só têm erros de protocolo; explicitar a ausência serve ao agente.
  6. **Tool description em inglês, sem markdown** — modelo processa inglês com mais densidade.
  7. **Validação sintática na descrição, executável no código** — spec carrega regras legíveis; código carrega validações.
  8. **Output com variantes em-bloco** — variantes condicionais documentadas com comentário inline na estrutura.
  9. **Exemplos cobrem estados, não inputs** — caso normal, variante de estado relevante, erro modal — não exaustivo.
  10. **Empty result é declaração explícita** — sem isso, agente trata vazio como falha de busca.
  11. **Especificação progressiva via campos opcionais** — para chaves hierárquicas, required nos níveis altos + optional nos baixos.
  12. **Vocabulário fechado vs dado aberto** — vocabulário fechado violado é validation error; dado aberto sem correspondência é empty result.
  13. **Output com variantes semânticas, não estruturais** — cada veredito/estado merece estrutura própria.
  14. **Campos opcionais sinalizam ausência semântica** — ausência é informação relevante, não campo esquecido.
  15. **Vocabulário fechado de evidência > texto livre** — para campos roteáveis, enum; texto livre só onde especificidade requer prosa.
  16. **Encadeamento de tools anunciado na descrição** — tools que se beneficiam de uso encadeado declaram na descrição.
  17. **Spec descreve o quê, não como** — mecanismo interno é decisão de implementação; spec descreve interface.
  18. **Tabela por tool e tabela consolidada são audiências diferentes** — §4.<n> serve ao implementador; §5.4 serve ao orchestrator.
  19. **`details` estruturado por `errorCode` é parte do contrato** — sem forma garantida, retryable colapsa em não-retryable.
  20. **"Casos que parecem erro mas não são" exige sub-seção** — força articulação de fronteiras epistêmicas.
  21. **Provenance é assimétrica entre retrieval e veredito** — leituras não precisam carregar versão; vereditos precisam.
  22. **Imutabilidade durante sessão é decisão MVP** — hot reload é trade-off, não requisito.
  23. **Não-objetivo é proteção, não documentação de incompletude** — "X é fora do escopo porque Y" ≠ "X ainda não foi feito".
  24. **Fronteira epistêmica ≠ não-objetivo** — não-objetivo é decisão; fronteira epistêmica é limite fundamental.
  25. **Critério é condição observável, não atividade** — "Tool retorna X em Y" é critério; "tool implementada" não é.
  26. **Review pass do architecture-overview é universal** — última sub-seção de toda spec; loop bidirecional.

### Validações empíricas

- **Pareamento template ↔ spec funcionou.** Estratégia de redigir versão concreta + versão genérica em paralelo permitiu extrair padrões cedo, e o template estabilizou junto com a spec sem precisar de sessão dedicada para refatorar. Comparação com hipótese alternativa (redigir spec inteira primeiro, extrair template depois): pareamento foi superior porque evidenciou inconsistências de princípio durante redação, não em revisão.

- **Revisão sistemática §1-§8 detectou três contradições silenciosas.** Mecanismo de reload entre §3.1 e §6.5; `POLICY_LOAD_FAILURE` na tabela vs. carga só no startup; ambiguidade de `evidence` (input ou output). Sem revisão deliberada, todas viraram bugs em implementação. Princípio meta para o projeto: toda spec passa por revisão de coerência interna antes de implementação.

- **Empurrar decisões para SCHEMA.md preservou agnosticismo do componente.** Vocabulário POL-000, enum de `operation`, vocabulário de `prescribed_treatment`, forma de `article_sources_summary`, regra unidirecional de `clause_id`, hierarquia de `article_source` — tudo migrado para SCHEMA.md mantém spec do `policy-reader` focada em comportamento contratual.

- **Reframe da preocupação substantiva sobre `indeterminate` modal.** Aluno levantou preocupação de que `indeterminate` seria caso modal e que isso quebraria a utilidade do veredito. Reframe registrado: arquitetura de quatro vereditos preservada; `verification_scope` rico transforma `indeterminate` em prescrição prática (escalation pattern com handoff estruturado). Não é falha do design; é honestidade epistêmica do sistema.

### Próximo passo

Sessão #06: PR enxuto de cleanup (renomeação `lgpd-policy-reader` → `policy-reader` em seis arquivos + sync de escopo restrito da Política em `architecture-overview.md` e `proposta-tcc2.md`). Após cleanup, abertura de §1 do `docs/specs/semgrep-runner.md`.

Sessão #07: redação completa de `docs/specs/semgrep-runner.md` (design real — sem decisões prévias). Aplicação dos 26 princípios; ajustes ao `_template.md` quando emergirem.

Sessão #08: ADR-0002 com seção de deferimentos explícita (browseability humana de cláusulas, hot reload, schemas alternativos, anotações declarativas, escopo ampliado da Política, mapa cross-PR longitudinal).

### Pendências (não bloqueantes)

- PR de cleanup da sessão #06 (renomeação + sync de escopo restrito da Política)
- `policy/SCHEMA.md` redação completa em paralelo à implementação (semana 2)
- ADR-0002 (sessão #08)
- Migração de conta GitHub para Team (ativa branch protection)
- `~/.claude/CLAUDE.md` user-scope com preferências cross-projeto

## 2026-05-07 — sessão #06 — cleanup pós-renomeação + placement híbrido MCP

### Conceitos da prova exercitados

**Domínio 2 — Tool Design & MCP Integration (18%)**

- **D2.3 `isError` flag e canais de output do `CallToolResult`.** Spec MCP atual (2025-11-25, confirmado via web search) define três campos relevantes para o caller: `content` (array de ContentBlock, obrigatório), `isError` (booleano opcional), `structuredContent` (objeto JSON opcional, mais recente na linha do tempo do spec). Erros de execução de tool reportam-se via `isError: true` no result, NÃO como erro de protocolo JSON-RPC — caso contrário o LLM não consegue ver o erro para autocorrigir. Erros de protocolo (tool name desconhecido, falha de schema validation no JSON-RPC) usam o canal `error.code` numérico.

- **D2.4 Placement híbrido `structuredContent` + `content`.** Decidido como convenção do projeto após web search confirmar que Claude Code 2.0.22+ prioriza `structuredContent` quando ambos os canais estão presentes (Issue #9962 do repo `anthropics/claude-code`). Convenção: payload estruturado (errorCode/message/isRetryable/details em erro; verdict/policy_clause_ref/evidence em sucesso) mora em `structuredContent`; `content[0]` carrega `TextContent` cuja chave `text` reproduz a `message` ou `evidence` em prosa humana — fallback de retrocompatibilidade e legibilidade em logs.

- **D2.5 Três classes de erro como materialização de "transient vs business vs permission".** Validation (sempre `isRetryable: false`) + business (decidido caso a caso) + system (quase sempre `isRetryable: true`) mapeia para o vocabulário do exam guide. Sem `isRetryable` explícito e `details` estruturado, erro retryable vira não-retryable na prática (caller não tem como ajustar a chamada).

- **D2.6 Naming convention `mcp__<server>__<tool>`.** Handle gerado pelo runtime quando expõe tools de um MCP server configurado em `.mcp.json`. Distingue tools MCP de built-in (Read/Write/Edit/Bash/Grep/Glob têm nome simples; tools MCP têm prefixo). Forma usada em três lugares: `allowed-tools` em frontmatter de skill, `mcp_servers`/`allowed-tools` no AgentDefinition do consumidor, e `matcher` de hooks PreToolUse/PostToolUse.

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1.1 (re-aplicação) Subagent tool restriction granular vs all-or-nothing.** Restrição via `mcp_servers` no AgentDefinition é all-or-nothing por server inteiro; restrição via `allowed-tools` é granular por tool individual. A versão granular EXIGE o naming `mcp__<server>__<tool>` — sem ele, não há como referenciar uma tool específica de um server. Implicação para o policy-reader: Matcher pode receber só `mcp__policy-reader__check_applicability` se um dia decidirmos que `find_clauses_by_law_article` não deve ser invocável por ele.

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- **D3.3 Hook matchers consomem o namespace MCP.** PostToolUse/PreToolUse com matcher tipo `^mcp__policy-reader__` filtra hooks para qualquer tool de um server específico. Sem documentar o naming na spec, autor de hook fica caçando a forma em outra fonte.

- **D3.4 Versão de tooling como floor empírico, não pin nem floor genérico.** CLAUDE.md declara "Claude Code CLI v2.1.123 or higher (validated locally; older versions not verified)". Pin exato força revisão a cada update sem ganho real; floor genérico ("≥ 2.0") afirma compatibilidade não testada; floor empírico declara o que sabe que funciona e expõe o limite.

**Domínio 5 — Context Management & Reliability (15%)**

- **D5.6 Error propagation por categoria viabiliza local recovery.** Casa com "local recovery before escalation" do exam guide. Matcher recebendo `CLAUSE_DEPRECATED` (business retryable) com `successors` em `details` faz retry com sucessor antes de escalar; recebendo `CLAUSE_NOT_FOUND` (business não-retryable) registra e segue; recebendo erro `system` faz backoff. Sem metadado estruturado, todas essas situações colapsam em "deu erro, escala".

- **D5.7 Fronteira epistêmica via escopo restrito da Política.** Decisão de cobrir só `consent_required` e `anonymization_required` na v0.1.0 da Política, com outras dimensões (transferência internacional, retenção, direitos do titular, dados de menores, tratamento compartilhado) explicitamente fora do MVP, é fronteira epistêmica declarativa. Protege a defesa do TCC contra "mas e retenção?" e protege evolução pós-MVP de virar refém de promessas que o MVP não fez.

### Decisões tomadas

- **Renomeação `lgpd-policy-reader` → `policy-reader` propagada em 4 arquivos vivos** (CLAUDE.md, README.md, architecture-overview.md, proposta-tcc2.md), 18 substituições via `sed`. Logs históricos (`learning-log.md`, `session-handoff.md`) **preservados intactos** por princípio: log é registro fiel da evolução do pensamento, não documento sob refatoração. Apagar o nome antigo nas entries pré-#05 falsificaria a história e destruiria o contraste que justifica a entry da renomeação na #05.

- **Sync da decisão de escopo restrito da Política propagado em 2 documentos.** Architecture-overview §7.3 ganhou nova linha na tabela "MVP versus trabalho futuro" + atualização do parágrafo introdutório de "Cinco evoluções" para "Seis" e "quatro/quinta" para "cinco/sexta" para manter contagem coerente. Proposta-tcc2 §8 ganhou item adicional em "Fora do escopo do MVP" nominando as dimensões da LGPD não cobertas. Frase canônica replicada literalmente do "Critério de revisita" da §7.2 da spec do policy-reader — coerência verbal cruzada, não só semântica.

- **Placement híbrido `structuredContent` + `content` adotado para CallToolResult em sucesso e erro.** Aplicado a §5.1 (texto canônico do payload de erro) e aos quatro exemplos da §4 (compliant, violation_candidate, indeterminate, CLAUSE_DEPRECATED). Wire format antigo (objeto JSON naked dentro de `content[]` sem discriminator `type`) era não-conformante ao spec MCP; novo formato usa `structuredContent` para o objeto e `content[0]` como TextContent fiel ao texto humano-legível.

- **Frase de convenção de erro consolidada em §5.1 do _template.md (placeholder) e do policy-reader.md (concreta).** Declara que o contrato `errorCode`/`message`/`isRetryable`/`details` é convenção do projeto sobreposta ao protocolo MCP — único campo de erro nativo do CallToolResult é o booleano `isError`.

- **Nota de escopo no topo do _template.md.** Template atual cobre apenas componentes que expõem contrato MCP (resources e/ou tools). Para subagentes (Triager, Detector, Classifier, Matcher, Reporter, coordinator), `_template-subagent.md` será derivado na primeira spec de subagente da semana 3, mesmo método de destilação.

- **Versão alvo do Claude Code declarada em CLAUDE.md "Stack (canonical)".** Linha "Claude Code CLI version: v2.1.123 or higher (validated locally; older versions not verified)". Inserida em Stack, não em Status flags — versão de tooling externo é tipologia ambiental, status flags são sobre estado de artefatos do repo (tests, CI, MCP servers).

- **Naming convention `mcp__<server>__<tool>` documentada na §4 do _template.md (genérica) e do policy-reader.md (concreta com os três handles listados nominalmente).** Local da declaração casa com onde o leitor está pensando "como referencio essas tools de fora".

### Artefatos criados

- PR `docs/session-06-cleanup` mergeado em `main` via squash (commit `6945840`)
- 6 arquivos modificados, 107 inserções, 51 deleções
- 5 logical units commitados separadamente no branch antes do squash (renomeação; sync de escopo; placement híbrido em specs+exemplos; nota de escopo do template; versão Claude Code; naming MCP)

### Validações empíricas

- **Web search confirmou spec MCP atual.** modelcontextprotocol.io/specification/2025-11-25 confirma três campos em CallToolResult; Issue #9962 do `anthropics/claude-code` documenta priorização de structuredContent sobre content em Claude Code 2.0.22+. Hipótese inicial implícita no handoff ("serializar dentro de content") corrigida para placement híbrido com base em evidência empírica do comportamento do client.

- **Bug de wire format detectado durante redação do item 3, não durante implementação.** Os quatro exemplos da §4 do policy-reader (objeto JSON naked dentro de `content[]`) não eram conformantes ao spec MCP. Detecção aconteceu enquanto redigíamos a frase de convenção de §5.1 — perceber que a frase nova ia contradizer os exemplos existentes forçou a identificação. Princípio meta: redigir frase canônica primeiro, depois conferir consistência com exemplos, é boa heurística de revisão.

- **Discrepância no handoff identificada e corrigida.** Handoff dizia "architecture-overview §6 ou §8" para o sync de escopo restrito; documento tem 7 seções e o local correto é §7.3 (tabela "MVP versus trabalho futuro"). Lição: handoff é instrumento de continuidade, mas precisa ser tratado como hipótese a verificar contra o estado atual do documento, não como verdade canônica.

- **Granularidade de commits durante o branch preservada apesar do squash final.** Cinco commits separados no branch (um por logical unit), squash único no merge. Granularidade fina viabilizou revisão por unidade durante a sessão; squash mantém log de main legível. Padrão de Conventional Commits funciona naturalmente com este fluxo.

- **MODO PROFESSOR aplicado conscientemente em dois pontos da sessão.** Antes do item 3 (placement em CallToolResult), conceito do Domínio 2 explicado com três opções de placement antes da escolha. Antes do item 6 (naming convention), conexão tripla com D1/D2/D3 explicada antes da redação. Validação curta após cada explicação ("está claro?") preveniu prosseguir sobre dúvida latente.

### Próximo passo

Sessão #07: redação completa de `docs/specs/semgrep-runner.md`. Diferente do `policy-reader`, este componente não tem decisões prévias acumuladas das sessões #03-#05 — é design real durante a redação. Pontos a decidir: unidade de invocação (arquivo, diff, projeto inteiro), regras como argumento ou pré-instaladas, streaming de findings ou retorno em bloco, representação de localização (file+line+col, range, snippet), tratamento de timeouts longos, contrato de erro específico do runner. Segunda aplicação dos 26 princípios destilados na #05 — template `_template.md` permanece "em formação" até esta validação; ajustes ao template esperados quando emergirem assimetrias entre os dois servers.

## 2026-05-09 — sessão #07 — redação da spec semgrep-runner

**Entrega.** `docs/specs/semgrep-runner.md` v0.1.0; sync de
`docs/architecture-overview.md` §4.2 e §5.2; PR #8 mergeado.

**Decisões fechadas (Bloco A → C → B → D).**
- Tool única `scan_diff(base_ref, head_ref)`. Split prematuro evitado: um caller, uma operação canônica.
- Rule set server-side curado, não argumento. Detector não escolhe regras; simetria com tratamento da Política no `policy-reader`.
- Retorno em bloco, sem streaming. Justificativa: agentic loop consome `CallToolResult` atômico.
- Timeout via env `SEMGREP_RUNNER_TIMEOUT_SECONDS` default 300s. `SCAN_TIMEOUT` modal sem findings parciais.
- Output com range completo + snippet + rule provenance, path relativo ao repo root, sem context lines artificiais.
- Seis errorCodes (2 business, 4 system). Validation vazio com declaração positiva.

**Princípios dos 26 que ganharam peso real.** #4, #5, #6, #7, #9, #10, #13, #17, #19, #20, #21, #23, #24, #25, #26. Pegada nova: #5 e #7 emergiram juntos sustentando "validation vazio é declaração, não omissão".

**Conceitos da prova exercitados.**
- D2 — `isError` (sinal protocolar nativo do MCP) vs `errorCode` (categoria de domínio dentro do payload). Distinção forçada à tona por pergunta no chat; virou parágrafo de abertura da §5.
- D2.1 — split prematuro como anti-pattern. Critério canônico: autonomia das descriptions, não similaridade de input/output.
- D2.2 — leitura do Semgrep MCP oficial como design reference. Decisão consciente de não consumir (caso de uso é IDE-oriented, não CI-oriented; pedagogia da prova exige build-your-own).
- D5.4 — structured error response habilita escalation algorítmica em vez de heurística. `errorCode` + `isRetryable` + `details` estruturado é o que torna a decisão local-vs-escalation decidível pelo coordinator.

**Meta-lições operacionais.**
- Revisão por padrão > revisão por anedota. Quando emerge regra implícita ("§8 é observação, não mecanismo"), varrer a seção inteira procurando outros itens que violam — não só corrigir os apontados. Captura do Claude Code no §8.6.3 sustentou.
- Hash de commit em corpo de outro commit é frágil — squash invalida. Referência semântica (`§8.<final> review pass`) sobrevive.
- Forma "três beats" do review pass (texto atual / por que inconsistente / patch proposto) emergiu no §8.<final>; replicável em futuras specs.

**Notas de calibração (fora do PR).**
- Assimetria §6 ("três eixos de versão") vs `scan_metadata` (cinco campos): `elapsed_seconds` é métrica de execução, não provenance. Mantido.
- `rule_severity: info` não exercitado em exemplos. Princípio #9 (estados, não enums). Mantido.
- Forward-reference a ADR-0002: débito implícito, risco de orfandade se #08-#09 não materializarem.

**Meta — primeira sessão com Claude Code.**
- Plan mode via `claude --permission-mode plan` no startup eliminou ambiguidade do keybinding Shift+Tab no Windows.
- Modelo "diff completo antes de Edit" foi mais valioso que "conteúdo redigido isolado" — capturou erros de coerência interna que apresentação isolada esconderia. Default para próximas sessões.
- Atos com consequência de versionamento (commit, push, PR) decididos explicitamente na #07. Para sessões de implementação iterativa (semana 4-5+), revisitar — provavelmente diluir tutela.
- Convenção do repo: omitir trailer `Co-Authored-By` em mensagens de commit. Memória gravada pelo Claude Code via feedback durante a sessão.
- Calibração da divisão Chat-vs-Code funcionou: Chat para planejar/decidir/revisar, Code para materializar. Manter.

**Artefatos.** PR #8; commits b144de4..910c9ed; branch `docs/specs-semgrep-runner` mergeada e excluída do remote (squash).

**Próximo passo.** Sessão #08 — ADR-0002 expandido. Ver session-handoff para detalhes.

## 2026-05-10 — sessão #09 — redação da ADR-0002

**Entrega.** `docs/adr/0002-mcp-conventions-and-deferments.md` v1.0;
PR #9 mergeado. Forward-references conceituais para ADR-0002 nas
specs do `policy-reader` e `semgrep-runner` resolvidas — texto das
specs ainda carrega ponteiros desatualizados, patch mecânico
agendado para #10.

**Decisões fechadas (sete convenções).**
- D1: Placement híbrido `structuredContent` + `content[0].text` em
  todo `CallToolResult`. Materializado em ambas as specs.
- D2: Server names com hyphen (`policy-reader`, `semgrep-runner`);
  tool names em lowercase snake_case; handle canônico
  `mcp__<server>__<tool>`. Inconsistência atual em
  `semgrep-runner.md` (underscore) vira follow-up patch.
- D3: Contrato de erro de três classes (validation / business /
  system) com `errorCode` + `message` + `isRetryable` + `details`.
  Empty result e `indeterminate` verdict explicitamente NÃO são
  erros.
- D4: Declaração positiva quando uma classe de erro está vazia
  (princípios #5 + #7 dos 26).
- D5: Forma "três beats" do review pass em §8.<final> (texto
  atual / por que inconsistente / patch proposto) como materialização
  operacional do princípio #26.
- D6: Versionamento de spec em semver, `0.x` até primeira
  implementação end-to-end passar §8 de aceitação, promoção a `1.0`
  exige ADR dedicado. Fecha forward-reference de `policy-reader.md`
  §5.5.
- D7: Schemes custom por artefato de domínio (`policy://` para o
  `policy-reader`). Fecha forward-reference de `policy-reader.md`
  §3.

**Decisões fechadas (nove deferimentos com critério de revisita).**
Cinco do `policy-reader` (A–E: browseability humana, hot reload,
schemas alternativos, anotações declarativas, escopo ampliado da
Política). Quatro do `semgrep-runner` (F–I: cross-file findings,
rule subset configurável, integração AppSec Platform, cancelamento
gracioso). Cada um com condição de revisita machine-checkable, não
prazo arbitrário.

**Princípios dos 26 que ganharam peso real.** #5 e #7 (empty
validation como declaração positiva, agora promovido a convenção
formal D4); #26 (review pass §8.<final> promovido a convenção
formal D5 com forma "três beats" prescrita).

**Conceitos da prova exercitados.**
- **Domínio 2 — Tool Design & MCP Integration (18%) — saturado.**
  D1 (placement híbrido) + D2 (naming convention) + D3 (três
  classes de erro + `isRetryable` + `details`) + D4 (declaração
  positiva) cobrem juntos a parte estrutural inteira do Domínio 2.
  Distinção `isError` protocolar vs `errorCode` de domínio
  reafirmada e formalizada. Material direto para questão de
  prova sobre desenho de contrato MCP.
- **Domínio 5 — Context Management & Reliability (15%) —
  escalation patterns institucionalizados.** Os nove deferimentos
  A–I com critério de revisita explícito são escalation patterns
  materializados como governança: cada deferimento declara a
  dimensão fora da capacidade atual e a condição que justificaria
  revisita. Honestidade epistêmica não como atitude, como
  artefato auditável.

**Meta-lições operacionais.**
- ADR enxuto funciona quando não há trade-off comparativo real.
  ADR-0001 precisou de essay-por-decisão porque cada decisão tinha
  alternativa séria (MIT vs Apache, squash vs merge, PR vs direct).
  ADR-0002 é consolidação de convenções já materializadas — formato
  curto (parágrafo de rationale + parágrafo de consequences) cabe.
  Heurística para futuros ADRs: peso do formato segue peso da
  deliberação original.
- Fluxo de deliberação por lista numerada (sete pontos do Chat
  prompt) → resposta abreviada (1.a, 2.a, 3.a...) → consolidação
  final em um único draft foi eficiente. Custo: zero ambiguidade
  na transição entre Chat (deliberar) e Code (executar).
- Convenção de naming de arquivos em `docs/adr/` digna de uma linha
  em CLAUDE.md ou skill. Erro mecânico de hoje (arquivo nomeado
  `adr-0002-...md` em vez de `0002-...md` causou pathspec mismatch,
  commit vazio, branch sem commits, `gh pr create` quebrado) é
  exatamente o tipo de coisa que regra escrita evita. Pendência
  para próxima janela de cleanup.

**Notas de calibração.**
- Mapa cross-PR longitudinal mantido fora do ADR-0002. Fronteira
  ADR (decisões de design de componente) vs roadmap consolidado
  (evoluções produto-nível) preservada. Heurística do learning-log
  da #03 (consolidar roadmap quando deferimentos cruzarem ≥3 ADRs)
  segue válida.
- Itens do feedback de review crítico da #05 (scratchpad pattern
  #13, justificativa FastMCP 2.x vs 3.x, nominação preliminar de
  hooks) NÃO entraram em ADR-0002. Justificativa: são decisões
  arquiteturais cross-component (não específicas de `policy-reader`
  ou `semgrep-runner`) e cabem mais naturalmente em ADR de
  arquitetura na semana 3 (specs de subagentes e coordinator).

**Artefatos.** PR #9; commits da branch
`docs/adr-0002-mcp-conventions-and-deferments` (squash em main).
`docs/adr/0002-mcp-conventions-and-deferments.md` publicado.

**Próximo passo.** Sessão #10 — PR de follow-up patches da ADR-0002
(três patches mecânicos em `policy-reader.md` e `semgrep-runner.md`,
mais verificação de declaração positiva de classes vazias), seguido
de redação completa de `policy/SCHEMA.md` v0.1.0. Ver
session-handoff para detalhes.

---

## 2026-05-10 — sessão #10 — POL-000 + SCHEMA.md + policy.yaml

**Entregas.** PRs #12 (POL-000 v0.1.0), #13 (SCHEMA.md + policy.yaml v0.1.0), #14 (cleanup snake_case da spec do policy-reader) mergeados em `main`.

**Decisões fechadas.**
- Inversão policy-first: schema destilado de POL-000 (primeira instância), não inventado a priori.
- Modelo B (taxonomia funcional flat) — nove classes reconhecíveis por padrão técnico em código brasileiro; critério de entrada: três exemplos canônicos plausíveis por classe.
- Tratamento α-2 dos sensíveis difusos do Art. 5º II: não modelar como classes; delegar a `unmodeled_special_category_fallback`. Dado genético absorvido em `dados_de_saude`.
- Formato dual canônico: Markdown jurídico (`policy/rationale/`) + YAML operacional (`policy/clauses/`). Markdown prevalece em drift; paridade verificada por teste automatizado na semana 5.
- Header global em `policy/policy.yaml` separado. `policy_schema_version` redundante em cada cláusula para fail-fast.
- Dois eixos semver independentes: `policy_schema_version` (schema) e `policy_version` (conteúdo). Regras de bump em SCHEMA §3.2.
- `clause_type: definitional | substantive` como discriminador. POL-000 é única definitional do MVP.
- Renomeações terminológicas (alinhamento GDPR/ICO/ISO): `legal_basis` → `lawful_basis`; `data_categories` → `personal_data_categories`; `dados_sensiveis_art5_ii` → `special_category` booleano; `prescribed_treatment` → `control` (ISO/IEC 27701, decisão do João pela extensibilidade); `article_source` → `statutory_reference`; `sensitive_diffuse_fallback` → `unmodeled_special_category_fallback`; `dimension` → `verification_aspect`. Enum `operation` normalizado (21 valores + `other`).
- Caminho evolutivo de `control` aberto: MVP enum simples; evolução para objeto `{type, value}` quando cláusulas precisarem prescrever mais que lawful basis. Additive, não quebra callers.
- Inciso modelado como inteiro no YAML, renderização para romano em apresentação humana (decisão da #05 materializada).

**Princípios articulados que ganharam peso real.**
- Markdown canônico jurídico, YAML destilação operacional — uma fonte canônica e seu derivado, não duas representações independentes.
- Schema destilado de instâncias — SCHEMA.md §6 marcada provisória até POL-001 existir.
- Aderência a terminologia oficial do domínio (auditor jurídico) sobre cunhagem própria reduz fricção de validação.
- Presentation layer separation (D5): estrutura é para máquina, renderização é função de saída.
- Declaração positiva de escopo: `out_of_scope` em POL-000 e marca "provisório" em SCHEMA §6 materializam o princípio.

**Conceitos da prova exercitados.**
- **Domínio 2 — Tool Design & MCP Integration (18%).** Vocabulary design com terminologia oficial GDPR/ICO/ISO; `other`+detail pattern para vocabulários exemplificativos (operation, com obrigatoriedade de `operation_description`); declaração positiva de escopo.
- **Domínio 3 — Claude Code Configuration & Workflows (20%).** Convenção de commits sem trailer Co-Authored-By gravada na memória do Code; analogia entre `clause_id` opaco unidirecional e learning-log append-only.
- **Domínio 4 — Prompt Engineering & Structured Output (20%).** Schema destilado de instâncias (Pydantic/JSON Schema design); vocabulários fechados (enum `lawful_basis`, `operation`, `control`); validation-retry implícito pelo formato dual (drift detectado → Markdown prevalece, YAML é corrigido).
- **Domínio 5 — Context Management & Reliability (15%).** Provenance temporal (dois eixos de versão identificam estado); stable identifiers (`clause_id` opaco, regra unidirecional); presentation layer separation; **error propagation through aparente safe transformation** — caso da linha 384 do cleanup PR #14, onde substituição mecânica de acento em identificador semanticamente inválido (`dados_sensiveis` — não é classe em POL-000) preservaria o erro sob aparência canônica. Lição: critério de transformação automatizada precisa verificar premissas, ou diff visual precisa preceder o commit, não suceder.

**Nota meta — evolução do desenho das classes.** Sessão #03 registrou "sete classes em v0.1.0". A redação efetiva de POL-000 fechou em nove (acréscimo de `dados_de_documentos_oficiais` como classe separada de identificação, e `dados_de_perfil_comportamental` cobrindo Art. 12 §2º LGPD). O registro da #03 fica intacto — princípio análogo ao da regra unidirecional de `clause_id`.

**Nota meta — calibração tardia do SCHEMA.md.** Primeiro rascunho saiu prolixo (~500 linhas) por interpretação inadequada do consumidor — tratado como "documento que cobre tudo exaustivamente" quando o consumidor real é humano de referência. Após pergunta do João sobre quem consome, comprimiu para ~258 linhas mantendo Apêndices densos. Lição: validar consumidor antes de redigir documento, não depois.

**Próximo passo.** Ver `docs/process/session-handoff.md`.

---

## Sessão #12 — 2026-05-12

**Foco:** destilamento dual canonical+compact das duas specs MCP; aplicação completa da taxonomia A-G; validação empírica do compact via proxy test; ajustes derivados.

### Conceitos da prova exercitados

- **D1 — Task decomposition.** Comparação de patterns para classificação A-G: prompt chaining sequencial (Chat→Code→Chat) vs dynamic adaptive decomposition em single-agent (Chat classifica + Code aplica patch mecânico). Escolha por single-agent quando subtask não exige ferramenta exclusiva.
- **D1 — Plan mode vs direct execution.** Trade-off explícito: plan mode em commits substantivos (decisões editoriais, ex. Commit 4 e 6); direct execution em commits mecânicos (cortes pré-aprovados, ex. Commit 5 e 7). Heurística destilada.
- **D1 — Hooks PostToolUse (conceitual).** Sanity checks pós-modificação dos pacotes são análogos a hooks: ferramenta termina → check determinístico roda → decisão prosseguir/parar. Pattern equivalente ao hook PostToolUse para validação determinística.
- **D2 — Resource vs Tool discrimination.** Princípio articulado (Resource vs Tool — discriminação pela leitura cognitiva); aplicado em policy-reader (ambos) e semgrep-runner (só tools). Asimetria entre os dois servers é caso-teste do princípio.
- **D2 — Tool description design.** Descriptions em inglês, contendo when-to-use, what-it-returns e anti-uses (frases tipo "Do not use this for X — use Y instead"). Anti-uses entram no checklist de paridade canonical↔compact (Commit 8).
- **D2 — Split de tool, não parametrização condicional.** Origem: §7 do semgrep-runner canonical, articulando o "porque não há `rule_set` parameter".
- **D2 — Convenção `mcp__<server>__<tool>`** referenciada nos dois compacts; convenção governada por ADR-0002 §2.
- **D3 — CLAUDE.md hierarchy** preservada sem modificação; sessão exercitou que CLAUDE.md + compact é suficiente para skeleton de implementação (proxy test, zero canonical opens).
- **D3 — .claude/skills/ não-uso.** Decisão consciente: compact spec vive como file (`docs/specs/<component>/compact.md`), não como skill. Skill faria sentido se a compact fosse referenciada por descrição em vez de path explícito. Anotação para futuro: skill pattern emerge se houver repetição de compact reading em workflows distintos.
- **D4 — Validation-retry loops com critério categórico.** Aplicado nos sanity checks de Commits 4-7 (range de count + Select-String exhaustivo); aplicado no proxy test (0 silent errors + ≤ 2 GAP markers + canonical opens alinhados a pointers). Calibração registrada: critério categórico vence critério agregado.
- **D4 — Structured output via tool_use schema.** Pacotes declarativos com `old_str`/`new_str` exatos são instâncias do mesmo pattern aplicado a edição de arquivo. Code aplica via str_replace, validation confirma execução fiel.
- **D4 — Few-shot via examples generosos.** Compact spec design favorece example-based learning: exemplo por veredito em `check_applicability` (4 exemplos), exemplo de timeout dedicado em `scan_diff`. Cap em cognitive-load content, livre em uniform reference examples.
- **D5 — Lost-in-the-middle.** Paginação do Commit 4 em duas passadas (§1-§4 e §5-§8) para mitigar degradação atencional na canônica de 691 linhas. Princípio destilável: classificação editorial sobre artefato fixo requer paginação acima de ~500 linhas; abaixo, single-pass.
- **D5 — Position-aware input ordering.** Compact spec design coloca contract surfaces no início (§1-§3: identity, wire format, error contract) e initialization no fim. Tools (médio) ficam na zona U-shape, mitigado por delimitadores claros (## headers).
- **D5 — Escalation patterns.** Reframe consumed/reference do compact (sempre lido por Code) vs canonical (referência on-demand) materializa o pattern escalation: small-always-loaded + large-on-demand. Mesmo padrão de `/compact` do Claude Code e scratchpad em multi-agent systems.
- **D5 — Scratchpad pattern.** Canonical funciona como read-only scratchpad / extended-context resource. Compact:canonical :: tool_description:resource_content.
- **D5 — Provenance/audit trail.** Decisão de manter §8.\<final\> em forma "three beats" pós-aplicação dos patches (em vez de reduzir a ponteiro de commit hash) é aplicação do princípio: documentação de drift detectado-e-resolvido tem valor de auditoria mesmo após resolução.

### Decisões substantivas

- **Taxonomia A-G aplicada** aos canonicals (Commits 4 e 5). 22 cortes em policy-reader (de 690 para 673), 9 cortes em semgrep-runner (de 449 para 440). Calibração da estimativa #08: superestimação por fator ~3 em linhas absolutas.
- **Reframe consumed/reference.** Compact é o que Code consome em implementação; canonical é referência on-demand. Substitui frame "governança-paridade" implícito no plano #11 original. Implicação direta: alvo de redução de canonical (575 linhas, estimativa #08) é morto. Canonical fica do tamanho que precisar; compact é orçado pela métrica "Code implementa sem abrir canonical no caso modal".
- **Proxy test como método de validação empírica.** Aplicado ao compact do policy-reader (resultado: 0 silent errors, 1 GAP marker substantivo, 5 revisões cirúrgicas). NÃO aplicado ao semgrep-runner (compacto menor, lessons learned do policy-reader transferíveis diretamente). Custo do método: ~1h-1h30min por proxy test; vale para artefatos centrais.
- **Article_source matching semantics.** Per-element hierarchical prefix: cláusula matcha se ANY elemento de `article_source` começa hierarquicamente com a especificação. Decidido inline no compact (OP-3 do Commit 6), nota inline também no canonical (Commit 9). NÃO vira ADR — decisão de design contida na spec.
- **§8.\<final\> lifecycle.** Mantido em forma "three beats" pós-aplicação dos patches conforme ADR-0002 Decisão 5. Diferido para ADR-0003 retrospectivo a discussão sobre o ciclo de vida formal pós-aplicação.
- **PR template** em `.github/PULL_REQUEST_TEMPLATE.md` com checkbox bidirecional canonical↔compact (Commit 8). Foco estrito em paridade; ADR/learning-log/sweep ficam fora do checklist.
- **Princípios destilados:** 4 totais ao fim da sessão — Resource vs Tool, Schema fora-comportamento dentro, Spec descreve o quê-não como, Split de tool-não parametrização condicional.

### Calibrações empíricas

- **Estimativa de redução por taxonomia A-G:** fator ~3 de superestimação na #08. Causa: estimativa foi pré-leitura, sem inspeção linha a linha das categorias presentes. Lição: estimar redução por taxonomia A-G só pós-leitura sumária da spec.
- **File-line estimativa imprecisa quando operações atravessam paragraph-separators.** Commit 4 teve off-by-3 (-17 actual vs -14 expected); Commit 5 bateu exato. Diferença atribuída a blank-line collapses em operações de E (cortes de duplicação).
- **Compact spec budget:** cap cognitive load (~200-237 linhas em policy-reader, ~121 em semgrep-runner), livre uniform reference examples. Cognitive-load = pure instruction + schema YAML blocks; uniform reference = JSON examples sob header padronizado. Cap não é cap de file count; é cap de conteúdo com cognitive load acumulativo.
- **Sanity check wrap-aware obrigatório.** Em arquivos hard-wrapped (canonical com ~72-80 char wrap), `Select-String -Pattern` matcha por linha física, não por linha lógica. Padrões devem usar substring contígua dentro de uma linha lógica. Falso positivo capturado no Commit 5 (preservação §6 de "Hash do diretório" que atravessa wrap entre L308 e L309).
- **Anti-regras em proxy test devem enumerar artefatos colaterais previsíveis.** Sessão #12 pegou `__pycache__` em mcp_servers/ no nível pai (package wrapper criado pelo Code), não previsto nas anti-regras. Princípio operacional: prompt de proxy test inclui lista explícita de "não cria X, Y, Z" para Python (package wrappers, lock files, cache dirs).
- **Critério de aprovação em validação empírica:** leitura crítica das categorias, não contagem agregada. "≤ 1 open question" como critério tosco foi insuficiente; 4 open questions reportadas decomposeram em 1 gap real + 1 minor unstated + 2 false positives, mudando veredito de fail para pass. Princípio: critério categórico bem-formado distingue categorias de severidade, não soma valores.
- **Escalation pointers podem ser over-anxious.** Pointer §5.1 do compact do policy-reader (sobre dual-deprecated semantics) disparou no proxy test sem necessidade — prosa local já bastava. Princípio destilado: pointer só justificado quando prosa local explicitamente insuficiente; condição do "if" deve ser estado epistêmico realista, não "se o leitor for cauteloso".
- **Cross-doc links em fase de draft carregam dívida de path enumerável.** 6 links totais ao fim da sessão (recontados: 2 em policy-reader canonical, 2 em semgrep-runner canonical, 0 em policy-reader compact, 2 em semgrep-runner compact).
- **Validação empírica precisa de canal narrativo aberto além das métricas.** Friction notes opcionais no relatório do proxy test (parte do prompt) revelaram as 5 revisões cirúrgicas. Métricas hard sozinhas teriam dado veredito "pass" + zero ação.

### Artefatos produzidos

- 9 commits da sessão #11 (`4e78f03` → este Commit 9): pre-fix, restructure, draft seed, A-G policy-reader, A-G semgrep-runner, compact policy-reader, compact semgrep-runner, PR template, fechamento.
- `docs/specs/policy-reader/canonical.md`: 673 linhas (de 690).
- `docs/specs/policy-reader/compact.md`: 397 linhas (novo).
- `docs/specs/semgrep-runner/canonical.md`: 440 linhas (de 449).
- `docs/specs/semgrep-runner/compact.md`: 202 linhas (novo).
- `.github/PULL_REQUEST_TEMPLATE.md`: criado (18 linhas).

### Próximo passo

- ADR-0003 retrospectivo (sessão #13 ou posterior): reframe consumed/reference + §8.\<final\> lifecycle. Dois conteúdos.
- Implementação semana 4-5: skeleton + lógica das duas MCP servers, agora ancorados nos compacts cristalizados.

## 2026-05-13 — sessão #13 — ADR-0003 dual-spec architecture

**Foco.** Fechamento do ciclo de meta-decisões de spec design. ADR único cobrindo dois conteúdos acumulados da sessão #12: reframe consumed/reference da arquitetura de docs, e ciclo de vida formal de §8.<final> pós-aplicação dos patches. Companion patches retrofitam policy-reader §8.8 (backfill retrospectivo) e atualizam semgrep-runner §8.<final> (resolution line).

### Conceitos da prova exercitados

- **D5 — Escalation patterns.** Decisão 1 do ADR formaliza compact (always-loaded) + canonical (on-demand) como instância do pattern small-always-loaded + large-on-demand. Same pattern de `/compact` do Claude Code e scratchpad files em multi-agent systems. Vocabulário "consumed/reference" mantido como nome local; "always-loaded/on-demand" intercalado entre parênteses no primeiro uso para amarrar ao vocabulário canônico da prova.
- **D5 — Provenance/audit trail.** Decisão 2 do ADR materializa a tese de que documentação de drift detectado-e-resolvido tem valor de auditoria mesmo após resolução. Três beats não colapsam em hash pointer; resolution line preserva o commit ref como fechamento, não como substituto.
- **D5 — Position-aware input ordering aplicado ao próprio ADR.** Context curto no início, Decisões no meio (zona U-shape mitigada por headers `### N`), Aggregated consequences e Companion patches no fim. Auditor lê do começo e do fim; o meio é detalhe técnico.
- **D2 — Tool design lateralmente.** Companion patches do policy-reader resgatam dois beats que registram drift entre spec e overview na convenção de naming de MCP servers (`policy-reader` vs `lgpd-policy-reader`) — convenção que ADR-0002 D2 formalizou posteriormente.

### Decisões substantivas

- **ADR único cobrindo ambos os conteúdos.** Não dois ADRs separados. Justificativa: ambas as decisões compartilham consumidor (Code + humano) e subject (estrutura e auditoria de spec); fragmentar prejudicaria a leitura do meta-layer.
- **Proxy test mencionado em passing, não promovido a Decisão 3.** Método é técnica operacional, não decisão arquitetural; ossificá-lo em ADR engessaria iteração futura. Fica no learning-log #12.
- **Companion patches dentro do mesmo PR do ADR.** Não follow-up patches separados. Materializar a Decisão 2 no mesmo commit em que ela é prescrita é teste de coerência operacional.
- **Backfill retrospectivo do policy-reader §8.8.** A spec ficou para trás da formalização do pattern "três beats" — authored em #05-#06, antes da forma cristalizar no semgrep-runner em #07 e ser formalizada em ADR-0002 D5 em #09. Reconstrução fiel a partir do diff de `git show 6945840`. Honestidade epistêmica preservada pela declaração explícita de retrospectividade no parágrafo de abertura da seção.
- **ADR-0002 Decisão 5 não amendada in-place.** Lifecycle vive em ADR-0003; leitor da Decisão 5 chega lá pelo "Related" header do ADR-0003. Justificativa: ADRs registram decisão original imutável; refinamento posterior abre ADR novo que cita.

### Calibrações empíricas

- **Verificação do handoff revelou drift de numeração entre Chat e learning-log.** Sessão aberta como "#11" pelo aluno; handoff em project knowledge registrava #12 fechada e #13 como próxima. Causa: chat numbering vs work-session numbering divergiram durante #11-#12 (extenso, parcialmente parallelizado). Lição: ao abrir nova sessão de Chat, primeira ação é confirmar o número contra o handoff, não contra a memória.
- **Resolution line exige investigação de git log; não dá para inferir de hash recente.** Tentativa inicial do aluno foi reutilizar `687a9f7` (Commit 8 da sessão #12, PR template) como ref para ambas resolution lines — hash que estava à mão na tela. Mas o ref correto é o commit do squash-merge que aplicou os patches na overview (`6945840` para policy-reader, `f7ec4b1` para semgrep-runner), descoberto via `git log --no-pager --oneline --follow docs/architecture-overview.md`. Lição operacional: resolution line não é "última coisa que aconteceu"; é "commit que materializou o patch específico". Confunde-las quebra a cadeia de auditoria.
- **Descoberta tardia de anomalia no policy-reader §8.8.** Boilerplate de template em vez de três beats. Detectada apenas após confirmação dos refs de companion patches, ao tentar formular o str_replace exato — não no levantamento inicial. Lição: levantamento de pendência por handoff + learning-log é necessário mas não suficiente; estado real dos arquivos precisa ser inspecionado antes de fechar pacote do Code. Procedimento operacional para ADRs retrospectivos: view de cada arquivo afetado antes de redigir o str_replace, não só leitura do project knowledge.

### Artefatos produzidos

- `docs/adr/0003-dual-spec-architecture.md` (56 linhas, novo).
- `docs/specs/policy-reader/canonical.md` §8.8 backfilled (boilerplate removido, três parágrafos retrospectivos + resolution line `6945840` adicionados).
- `docs/specs/semgrep-runner/canonical.md` §8.<final> resolution line atualizada (frase "próximo commit nesta branch" substituída por ref `f7ec4b1`).
- PR #17 mergeado em main via squash. Branch `docs/adr-0003-dual-spec-architecture` deletada.

### Próximo passo

Implementação semana 4-5 do cronograma TCC: skeleton + lógica das duas MCP servers, ancorados nos compacts cristalizados na sessão #11. Branch nova a partir de main; provavelmente componente por componente (policy-reader primeiro, semgrep-runner em seguida) ou em paralelo se houver fôlego.

## 2026-05-13 — sessão #14 — policy-reader skeleton (Fase A) + decisões de stack

**Foco.** Abertura da fase de implementação. Bootstrap do pacote `mcp-servers` via uv, registro de tools e resources do `policy-reader` como stubs, declaração project-scope via `.mcp.json`, e validação empírica end-to-end com Claude Code. Fase A (skeleton) completa; Fase B (loader + tools reais) deferida para sessão #15. Quatro decisões de stack/arquitetura tomadas no caminho, três delas com ADRs pendentes.

### Conceitos da prova exercitados

- **D2 — MCP server bootstrap com FastMCP.** Instanciação via `FastMCP("policy-reader")` (server identity em kebab-case conforme ADR-0002 D2), decoradores `@mcp.tool` (3.x permite sem parens) e `@mcp.resource(uri)`, retorno tipado em `dict[str, Any]` deixa FastMCP gerar `CallToolResult` com placement híbrido (structuredContent + content[0].text) automaticamente.
- **D2 — Discriminação tools vs resources no wire format.** Validação empírica revelou: tools retornam JSON direto via `CallToolResult`; resources retornam `{"contents":[{"uri":..., "mimeType":"text/plain", "text":"..."}]}` via `ReadResourceResult` com payload JSON serializado como string dentro do `text`. São primitives diferentes no MCP spec; consumer de resource precisa de `json.loads(text)` para destrinchar. FastMCP default deu `text/plain` para resources estruturados — micro-débito documentado para fix junto com loader real (declaração explícita `mime_type="application/json"`).
- **D2 — Tool description como prompt real do agente.** Docstring de função decorada com `@mcp.tool` (sem `description=` explícito) é literalmente o input do agente na hora de decidir invocação. Convenção ADR-0002 aplicada: inglês, with when-to-use + what-it-returns + anti-uses. Anti-uses ("Do not use this for X — use Y instead") é o controle mais subestimado contra ambiguidade entre tools similares.
- **D2 — Project vs user scope em `.mcp.json`.** Três escopos coexistem: `~/.claude/settings.json` (user, pessoal cross-projeto), `.mcp.json` no project root (project, versionado em git, compartilhado), `.claude/settings.local.json` (local, per-machine overrides, ignorado pelo git). Trust decidido per-user no primeiro contato com `.mcp.json` versionado — Claude Code pergunta antes de spawnar subprocess. Aceito como "use this and all future MCP servers in this project" persiste em `.claude/settings.local.json`.
- **D1 — Skeleton-first vs tool-completo-por-iteração.** Discussão explícita de task decomposition na abertura da sessão. Argumento contra tool-completo: proxy test da #11 validou cognitive load do compact, não wire format implementation. Quatro pressupostos não-validados na sessão (FastMCP+Pydantic+Python produz wire format conformante; `.mcp.json` resolve launch; handle `mcp__policy-reader__<tool>` parseado com hyphen no server name; tool descriptions exibidas) deflados em 1-2h com skeleton; deflação tardia teria custado sunk cost de loader+lógica em cima de pressupostos errados. Pattern: validação empírica determinística pós-toolchain antes de empilhar lógica.
- **D5 — Fail-fast validation at server startup.** Decisão de design do `policy_loader.py` (a implementar em #15): qualquer cláusula falhando validação aborta o startup, server recusa servir Política corrompida. Pattern alinha-se com §4.5 do SCHEMA.md ("Fail-fast: divergência incompatível entre cláusula e header aborta carregamento do `policy-reader` no startup"). Alternativa "carrega o que der e loga warning" rejeitada como reliability ruim.
- **D1 — Starting fresh session over resuming stale context.** Sessão encerrada antes de Commit 5 explicitamente para abrir #15 fresh em vez de continuar carregando contexto acumulado da #14. Aplicação direta de task statement 1.7 de D1: "Starting a new session with a structured summary is more reliable than resuming with stale tool results." Handoff estruturado é o mecanismo de transferência.

### Decisões substantivas

- **Toolchain: uv adotado.** Substitui `pip install --user` ad-hoc de sessões anteriores. Razões: lockfile (`uv.lock` versionado) garante reprodutibilidade bit-a-bit entre desenvolvedores e CI; gerenciamento de Python embutido remove dependência de pyenv-win para colaboradores; velocidade (10-100× pip); compatível com restrição corporativa (install em diretório de usuário, sem admin). Pendente: ADR-0004 formalizando.
- **FastMCP 3.x adotado em vez de 2.x.** `uv add fastmcp` sem cap resolveu 3.2.4. ADR-0001 fixou "2.x" como stack canônica, mas learning-log da #07 já registrava "justificativa FastMCP 2.x vs 3.x" como deferred decision. Decidido formalizar 3.x: arquitetura nova "Providers and Transforms" é invisível ao nosso caso de uso (`@tool`/`@resource` decorators continuam idênticos); component versioning (`@tool(version="X")`) casa com nosso eixo `policy_version`; hot reload em dev; OpenTelemetry nativo. CVE em 2.x mencionado em fonte de terceiro mas não confirmado contra NVD/GitHub Advisories — verificação pendente, vai pro Context do ADR-0004 se procedente. Constraint atualizado para `fastmcp>=3.2.0,<4.0` (floor de 3.2.0 onde os supostos CVEs ficaram patcheados, cap em `<4.0` previne pulo silencioso de major).
- **Multi-tenant LGPD-only com mitigações para evolução multi-jurisdição.** Discussão arquitetural disparada por questionamento de João: "vocabulários jurisdicionais (Operation, Control, OutOfScopeReason, LawfulBasis) não deveriam estar em Layer 1?". Análise revelou que SPECs já estão design-intent corretas em pontos críticos (`accepted_law_identifiers` consumido do header, decidido na #04; specs apontam para SCHEMA.md como fonte para vocabulários). Mas implementação proposta do `policy_loader.py` duplicava esses dados como enum estático em código. Decisão: manter (a) multi-tenant LGPD-only no MVP v0.1.0 com três mitigações no `policy_loader.py` que reduzem custo de migração futura para (b) multi-jurisdição: (1) campos jurisdicionais tipados como `str` em vez de `Enum` em modelos Pydantic, (2) validação dinâmica via `model_validator` contra constantes nomeadas (`frozenset` no módulo), (3) marcadores `# JURISDICTIONAL — LGPD MVP, see ADR-0005` em cada ponto de coupling. `AcceptedLaw` validado dinamicamente contra `header.accepted_law_identifiers` desde o MVP (não hardcoded). Pendente: ADR-0005 formalizando + SCHEMA.md §7 ajuste distinguindo vocabulários estruturais vs jurisdicionais.
- **Skeleton-first para o `policy-reader` em vez de tool-completo-por-iteração.** Quatro pressupostos não-validados deflados antes de empilhar lógica. Híbrido aplicado: skeleton de todos os tools/resources com stub data, depois iteração tool-por-tool começando com `get_clause` (deferida para #15). Validação empírica end-to-end via Claude Code completa para os cinco surfaces.
- **`.mcp.json` em project-scope, sem env var no skeleton.** Server declarado em `.mcp.json` no root do repo (versionado em git). Env var `POLICY_READER_POLICY_DIR` deliberadamente fora do skeleton — server.py ainda não carrega Política, declarar agora geraria impressão errada de funcionalidade. Adicionada junto com loader real no Commit 5.

### Calibrações empíricas

- **uv `--managed-python` no `init` não força download de Python managed se há Python compatível visível no PATH.** Comportamento observado: `uv add fastmcp` usou pyenv-win Python (`C:\Users\...\pyenv-win\versions\3.12.7\python.exe`) em vez de baixar managed. Implicação: a história de "reprodutibilidade para colegas sem pyenv-win" fica parcialmente comprometida no setup atual — novos colaboradores precisarão *ou* ter pyenv-win com 3.12.7, *ou* deixar uv baixar quando rodar `uv sync` em máquina sem 3.12.7+. Vai pro Context do ADR-0004.
- **PowerShell 5.1 default code page é cp1252; lê arquivo UTF-8 como cp1252 e exibe `ã` como `Ã£`.** Não é problema do arquivo. Fix: `chcp 65001` muda console para UTF-8 (vale uma vez por janela). `Get-Content -Encoding UTF8 arquivo` força leitura UTF-8 sem mudar console.
- **Git CRLF→LF auto-conversion ativa por default no Windows.** Warning "CRLF will be replaced by LF" em cada `git add` de arquivo novo é informacional, não erro. Arquivos no repo ficam LF; checkout local reconverte para CRLF transparentemente. Eliminar warning requer `.gitattributes` com regras explícitas (não feito; não bloqueia).
- **`fastmcp inspect` é CLI 3.x para verificar metadata sem rodar server stdio "vivo".** Output mostra Name, Version, Generation, contagem de Tools/Prompts/Resources/Templates. Validação cheap antes de empacotar commit. Significado exato de "Generation: N" no output não confirmado — possivelmente counter interno de re-registros; investigação deferida, não bloqueia.
- **Server iniciado "nu" no terminal (`uv run python -m ...`) trava aguardando JSON-RPC em stdin, com erros de parse JSON quando recebe linhas vazias.** Comportamento correto, não bug. stdio transport sempre vai parecer assim sem cliente do outro lado. FastMCP 3.x trouxe `fastmcp call` e `fastmcp list` CLIs para invocação manual sem cliente MCP.
- **Tetralogia do MCP primitive registry: Tools, Resources, Prompts, Templates.** Output do `fastmcp inspect` lista os quatro. Prompts (terceiro primitive, templates reutilizáveis de mensagem) e Resource Templates (resources parametrizados via URI patterns) descartados pro MVP em ADR-0002 mas valem internalizar por ser vocabulário de prova.
- **51 tools no contexto do Claude Code atual (40 Postman + 8 AEM + 3 policy-reader + 0 Gmail/Drive pendentes de auth).** Tool inventory bloat afeta seleção; modelo lê todas as descriptions a cada turn. Não bloqueia agora mas vale considerar quais MCPs ficam ligados durante development do `check_applicability` na sessão de implementação real (Commit 6+).
- **João questionou estado de contexto/sessão antes de iniciar Commit 5 (`policy_loader.py`).** Pergunta válida; análise honesta levou ao encerramento da sessão para abrir #15 fresh. Aplicação prática do conceito D1 task statement 1.7. Sintomas detectados: respostas mais longas que necessário, repetição de conceitos já estabelecidos, tentação de overengineer crescente.

### Artefatos produzidos

- Branch `feat/policy-reader-skeleton` (aberta, sem PR ainda) com 3 commits:
  - `a5e715a` feat: bootstrap mcp-servers package with uv and policy-reader skeleton
  - `de9be95` feat(policy-reader): register 2 resources and 3 tools as skeleton stubs
  - `501fe17` feat(policy-reader): declare project-scope MCP server registration
- `pyproject.toml` declarando pacote `mcp-servers` com FastMCP 3.x (`fastmcp>=3.2.0,<4.0`), Pydantic, PyYAML + pytest dev
- `uv.lock` versionado (74 packages resolvidos)
- `.python-version` pinado em 3.12.7
- `src/mcp_servers/__init__.py`, `src/mcp_servers/py.typed`
- `src/mcp_servers/policy_reader/__init__.py`, `src/mcp_servers/policy_reader/server.py` (133 linhas, skeleton com 2 resources + 3 tools, descriptions em inglês conforme ADR-0002)
- `.mcp.json` em project-scope declarando `policy-reader`

### Próximo passo

Sessão #15 abre com **agenda dupla, primeira hora dedicada a artefatos de documentação pendentes**: (a) `SCHEMA.md §7` ajuste distinguindo vocabulários estruturais vs jurisdicionais, (b) ADR-0005 redigindo "LGPD-coupling em vocabulários jurisdicionais: decisão MVP e migration path". Ambos têm structure rascunhada no chat da #14, registrada no handoff. Após esses, retoma branch `feat/policy-reader-skeleton` para Fase B: Commit 5 do `policy_loader.py` com as três mitigações decididas, depois Commit 6 (`get_clause` real), Commit 7 (testes pytest §8.2 incluindo fixture deprecated), Commit 8 (validação manual §8 via Claude Code), Commit 9 (closure #15). PR só após Commit 7 ou 8. Pendente também: ADR-0004 (uv + FastMCP 3.x) — pode ficar para #16 ou intercalado na #15 se houver fôlego.

---

## Sessão #12 — 2026-05-12

**Foco:** destilamento dual canonical+compact das duas specs MCP; aplicação completa da taxonomia A-G; validação empírica do compact via proxy test; ajustes derivados.

### Conceitos da prova exercitados

- **D1 — Task decomposition.** Comparação de patterns para classificação A-G: prompt chaining sequencial (Chat→Code→Chat) vs dynamic adaptive decomposition em single-agent (Chat classifica + Code aplica patch mecânico). Escolha por single-agent quando subtask não exige ferramenta exclusiva.
- **D1 — Plan mode vs direct execution.** Trade-off explícito: plan mode em commits substantivos (decisões editoriais, ex. Commit 4 e 6); direct execution em commits mecânicos (cortes pré-aprovados, ex. Commit 5 e 7). Heurística destilada.
- **D1 — Hooks PostToolUse (conceitual).** Sanity checks pós-modificação dos pacotes são análogos a hooks: ferramenta termina → check determinístico roda → decisão prosseguir/parar. Pattern equivalente ao hook PostToolUse para validação determinística.
- **D2 — Resource vs Tool discrimination.** Princípio articulado (Resource vs Tool — discriminação pela leitura cognitiva); aplicado em policy-reader (ambos) e semgrep-runner (só tools). Asimetria entre os dois servers é caso-teste do princípio.
- **D2 — Tool description design.** Descriptions em inglês, contendo when-to-use, what-it-returns e anti-uses (frases tipo "Do not use this for X — use Y instead"). Anti-uses entram no checklist de paridade canonical↔compact (Commit 8).
- **D2 — Split de tool, não parametrização condicional.** Origem: §7 do semgrep-runner canonical, articulando o "porque não há `rule_set` parameter".
- **D2 — Convenção `mcp__<server>__<tool>`** referenciada nos dois compacts; convenção governada por ADR-0002 §2.
- **D3 — CLAUDE.md hierarchy** preservada sem modificação; sessão exercitou que CLAUDE.md + compact é suficiente para skeleton de implementação (proxy test, zero canonical opens).
- **D3 — .claude/skills/ não-uso.** Decisão consciente: compact spec vive como file (`docs/specs/<component>/compact.md`), não como skill. Skill faria sentido se a compact fosse referenciada por descrição em vez de path explícito. Anotação para futuro: skill pattern emerge se houver repetição de compact reading em workflows distintos.
- **D4 — Validation-retry loops com critério categórico.** Aplicado nos sanity checks de Commits 4-7 (range de count + Select-String exhaustivo); aplicado no proxy test (0 silent errors + ≤ 2 GAP markers + canonical opens alinhados a pointers). Calibração registrada: critério categórico vence critério agregado.
- **D4 — Structured output via tool_use schema.** Pacotes declarativos com `old_str`/`new_str` exatos são instâncias do mesmo pattern aplicado a edição de arquivo. Code aplica via str_replace, validation confirma execução fiel.
- **D4 — Few-shot via examples generosos.** Compact spec design favorece example-based learning: exemplo por veredito em `check_applicability` (4 exemplos), exemplo de timeout dedicado em `scan_diff`. Cap em cognitive-load content, livre em uniform reference examples.
- **D5 — Lost-in-the-middle.** Paginação do Commit 4 em duas passadas (§1-§4 e §5-§8) para mitigar degradação atencional na canônica de 691 linhas. Princípio destilável: classificação editorial sobre artefato fixo requer paginação acima de ~500 linhas; abaixo, single-pass.
- **D5 — Position-aware input ordering.** Compact spec design coloca contract surfaces no início (§1-§3: identity, wire format, error contract) e initialization no fim. Tools (médio) ficam na zona U-shape, mitigado por delimitadores claros (## headers).
- **D5 — Escalation patterns.** Reframe consumed/reference do compact (sempre lido por Code) vs canonical (referência on-demand) materializa o pattern escalation: small-always-loaded + large-on-demand. Mesmo padrão de `/compact` do Claude Code e scratchpad em multi-agent systems.
- **D5 — Scratchpad pattern.** Canonical funciona como read-only scratchpad / extended-context resource. Compact:canonical :: tool_description:resource_content.
- **D5 — Provenance/audit trail.** Decisão de manter §8.\<final\> em forma "three beats" pós-aplicação dos patches (em vez de reduzir a ponteiro de commit hash) é aplicação do princípio: documentação de drift detectado-e-resolvido tem valor de auditoria mesmo após resolução.

### Decisões substantivas

- **Taxonomia A-G aplicada** aos canonicals (Commits 4 e 5). 22 cortes em policy-reader (de 690 para 673), 9 cortes em semgrep-runner (de 449 para 440). Calibração da estimativa #08: superestimação por fator ~3 em linhas absolutas.
- **Reframe consumed/reference.** Compact é o que Code consome em implementação; canonical é referência on-demand. Substitui frame "governança-paridade" implícito no plano #11 original. Implicação direta: alvo de redução de canonical (575 linhas, estimativa #08) é morto. Canonical fica do tamanho que precisar; compact é orçado pela métrica "Code implementa sem abrir canonical no caso modal".
- **Proxy test como método de validação empírica.** Aplicado ao compact do policy-reader (resultado: 0 silent errors, 1 GAP marker substantivo, 5 revisões cirúrgicas). NÃO aplicado ao semgrep-runner (compacto menor, lessons learned do policy-reader transferíveis diretamente). Custo do método: ~1h-1h30min por proxy test; vale para artefatos centrais.
- **Article_source matching semantics.** Per-element hierarchical prefix: cláusula matcha se ANY elemento de `article_source` começa hierarquicamente com a especificação. Decidido inline no compact (OP-3 do Commit 6), nota inline também no canonical (Commit 9). NÃO vira ADR — decisão de design contida na spec.
- **§8.\<final\> lifecycle.** Mantido em forma "three beats" pós-aplicação dos patches conforme ADR-0002 Decisão 5. Diferido para ADR-0003 retrospectivo a discussão sobre o ciclo de vida formal pós-aplicação.
- **PR template** em `.github/PULL_REQUEST_TEMPLATE.md` com checkbox bidirecional canonical↔compact (Commit 8). Foco estrito em paridade; ADR/learning-log/sweep ficam fora do checklist.
- **Princípios destilados:** 4 totais ao fim da sessão — Resource vs Tool, Schema fora-comportamento dentro, Spec descreve o quê-não como, Split de tool-não parametrização condicional.

### Calibrações empíricas

- **Estimativa de redução por taxonomia A-G:** fator ~3 de superestimação na #08. Causa: estimativa foi pré-leitura, sem inspeção linha a linha das categorias presentes. Lição: estimar redução por taxonomia A-G só pós-leitura sumária da spec.
- **File-line estimativa imprecisa quando operações atravessam paragraph-separators.** Commit 4 teve off-by-3 (-17 actual vs -14 expected); Commit 5 bateu exato. Diferença atribuída a blank-line collapses em operações de E (cortes de duplicação).
- **Compact spec budget:** cap cognitive load (~200-237 linhas em policy-reader, ~121 em semgrep-runner), livre uniform reference examples. Cognitive-load = pure instruction + schema YAML blocks; uniform reference = JSON examples sob header padronizado. Cap não é cap de file count; é cap de conteúdo com cognitive load acumulativo.
- **Sanity check wrap-aware obrigatório.** Em arquivos hard-wrapped (canonical com ~72-80 char wrap), `Select-String -Pattern` matcha por linha física, não por linha lógica. Padrões devem usar substring contígua dentro de uma linha lógica. Falso positivo capturado no Commit 5 (preservação §6 de "Hash do diretório" que atravessa wrap entre L308 e L309).
- **Anti-regras em proxy test devem enumerar artefatos colaterais previsíveis.** Sessão #12 pegou `__pycache__` em mcp_servers/ no nível pai (package wrapper criado pelo Code), não previsto nas anti-regras. Princípio operacional: prompt de proxy test inclui lista explícita de "não cria X, Y, Z" para Python (package wrappers, lock files, cache dirs).
- **Critério de aprovação em validação empírica:** leitura crítica das categorias, não contagem agregada. "≤ 1 open question" como critério tosco foi insuficiente; 4 open questions reportadas decomposeram em 1 gap real + 1 minor unstated + 2 false positives, mudando veredito de fail para pass. Princípio: critério categórico bem-formado distingue categorias de severidade, não soma valores.
- **Escalation pointers podem ser over-anxious.** Pointer §5.1 do compact do policy-reader (sobre dual-deprecated semantics) disparou no proxy test sem necessidade — prosa local já bastava. Princípio destilado: pointer só justificado quando prosa local explicitamente insuficiente; condição do "if" deve ser estado epistêmico realista, não "se o leitor for cauteloso".
- **Cross-doc links em fase de draft carregam dívida de path enumerável.** 6 links totais ao fim da sessão (recontados: 2 em policy-reader canonical, 2 em semgrep-runner canonical, 0 em policy-reader compact, 2 em semgrep-runner compact).
- **Validação empírica precisa de canal narrativo aberto além das métricas.** Friction notes opcionais no relatório do proxy test (parte do prompt) revelaram as 5 revisões cirúrgicas. Métricas hard sozinhas teriam dado veredito "pass" + zero ação.

### Artefatos produzidos

- 9 commits da sessão #11 (`4e78f03` → este Commit 9): pre-fix, restructure, draft seed, A-G policy-reader, A-G semgrep-runner, compact policy-reader, compact semgrep-runner, PR template, fechamento.
- `docs/specs/policy-reader/canonical.md`: 673 linhas (de 690).
- `docs/specs/policy-reader/compact.md`: 397 linhas (novo).
- `docs/specs/semgrep-runner/canonical.md`: 440 linhas (de 449).
- `docs/specs/semgrep-runner/compact.md`: 202 linhas (novo).
- `.github/PULL_REQUEST_TEMPLATE.md`: criado (18 linhas).

### Próximo passo

- ADR-0003 retrospectivo (sessão #13 ou posterior): reframe consumed/reference + §8.\<final\> lifecycle. Dois conteúdos.
- Implementação semana 4-5: skeleton + lógica das duas MCP servers, agora ancorados nos compacts cristalizados.

---

## 2026-05-14 — sessão #16 — Fase 1 (multi-client architecture rewrite) complete

**Foco.** Fechamento da arquitetura multi-cliente declarada em `docs/process/proposta-tcc2.md` §6 via reescrita documental coordenada em 7 commits sequenciais na branch `arch/multi-client-policy-rewrite`. Sem código de implementação — toda a sessão viveu na camada de docs (`architecture-overview.md`, ADR-0005, `SCHEMA.md`, specs canonical+compact dos dois servers, `DESIGN.md` novo, learning-log, session-handoff). Materializa a separação estrutural/jurisdicional já implícita na proposta e cristaliza-a antes do início da Fase 2.

### Conceitos da prova exercitados

**Domínio 2 — Tool Design & MCP Integration.**

- **Resource vs Tool em caso-livro.** `policy://vocabularies` ganhou existência como recurso compartilhável (consumido por Classifier e Matcher) enquanto as tools do `policy-reader` (`get_clause`, `find_clauses_by_law_article`, `check_applicability`) continuaram exclusivas do Matcher. Materializa a discriminação app-controlled context (resources) vs model-controlled invocation (tools): vocabulário é catálogo idempotente lido por múltiplos agentes; cláusula é consulta direcionada com semântica de ação. Princípio Resource vs Tool aplicado aqui em forma de caso-livro — assimetria com `semgrep-runner` (que não expõe resources) é o caso-teste do princípio.
- **Tool authorization granular.** Classifier ganhou visibilidade ao resource `policy://vocabularies` sem ganhar acesso às tools — `mcp_servers` da AgentDefinition reflete somente o que o subagente precisa, princípio "only what they need". Matriz §5.7 de `architecture-overview.md` ganhou linha dedicada para resource compartilhado, distinta da linha de tools.
- **Handshake protocol como pattern.** `policy://schema-version` evoluiu de handshake simples (estrutural via `compatible_schema_range`) para handshake duplo (estrutural + jurisdicional via `legal_framework`). Componente declara; consumidor (Matcher) decide. Validação de framework é responsabilidade do consumidor, não do componente — simétrica ao tratamento de `compatible_schema_range`. Padrão de design replicável para outros pontos de provenance multi-axial.

**Domínio 5 — Context Management & Reliability.**

- **Provenance trinque.** `(policy_schema_version, policy_version, legal_framework)` carregado em cada retorno de `check_applicability`, em cada veredito do Matcher e no `Report` final do Reporter. Materializa o princípio "provenance carried, not inferred" para auditoria multi-jurisdição assíncrona — sem `legal_framework` no veredito o auditor não saberia sob qual lei a decisão foi tomada. Campo não-opcional por design, não por convenção.
- **Forma estável de payload vs conteúdo variável.** `accepted_values` em `INVALID_DATA_CATEGORY` e `INVALID_OPERATION` permanece com a mesma forma (lista de strings); o conteúdo vem dinamicamente dos vocabulários da Política carregada. Separação modeling × parametrization: o contrato congelado, o dado parametrizado. Implementação da Fase 2 vai materializar isso lendo `policy/vocabularies/<framework>/*.yaml` no startup e injetando em respostas de erro — não hardcoded.
- **Lost-in-the-middle mitigado proativamente.** `/compact` disparado no Code antes do Commit 4 (24+ edits no canonical em 8 grupos por seção). Sem o compact, o turno acumulado dos Commits 1-3 teria empurrado patches do início do Commit 4 para a zona U-shape do contexto. Aplicação do padrão "compactar em ~60%, não em 95%" — preservei estado (branch, hashes aplicados, decisões substantivas, pendências) e descartei diffs verbatim e turnos de review já encerrados.

**Domínio 1 — Agentic Architecture & Orchestration.**

- **Fixed sequential pipeline (prompt chaining).** Os 7 commits da Fase 1 são pipeline determinística: cada um consome o output do anterior (Commit 4 só faz sentido pós-Commit 3 que externalizou os vocabulários; Commit 5.5 só faz sentido pós-Commits 1-5 que produziram os pointers). Alternativa (dynamic adaptive decomposition em single-agent) descartada porque o handoff da sessão #15 já congelou o plano — re-decidir a sequência em runtime teria adicionado custo sem ganho. Pattern: quando o plano está fechado em handoff estruturado, chaining vence orchestrator-workers.
- **Separação de planos epistêmicos.** Detector raciocina no plano sintático (Semgrep sobre diff), Classifier no plano lexical (vocabulário da Política via `policy://vocabularies`), Matcher no plano jurídico (`check_applicability`). Coordinator agencia a tradução entre planos. Materializa task decomposition por responsabilidade disjunta — cada subagente tem vocabulário próprio, sem sobreposição. Princípio cristalizado em bloco dedicado de `DESIGN.md` (Commit `d466f37`).

**Domínio 3 — Claude Code Configuration & Workflows.**

- **Plan mode aplicado seletivamente.** Commits 2 (ADR-0005), 4 (policy-reader rewrite) e 5.5 (DESIGN.md novo) entraram em plan mode — alto grau de liberdade editorial, escolhas substantivas a alinhar antes de escrever. Demais commits (1, 3, 5) em direct execution — patches literais do handoff. Heurística: plan mode quando o output tem mais de uma forma defensável; direct execution quando o handoff já especificou a forma única.
- **`/compact` proativo com preservação explícita.** Antes do Commit 4 invoquei `/compact` listando o que preservar (branch, hashes, decisões, pendências) e o que descartar (diffs verbatim, turnos de revisão encerrados). Padrão "compactar em ~60%" exercitado — sem instrução de preservação, `/compact` tende ao extremo de 95% e perde estado operacional.

**Domínio 4 — Prompt Engineering & Structured Output.**

- **Multi-instance review como mecanismo de captura de drift.** Chat (revisor) e Code (gerador) operam com reasoning contexts independentes; cada patch passou pelo crivo do chat antes da aplicação. Capturou drift do `succeeds`/`treatment_observations` no Commit 2 e drift do `out_of_scope` no Grupo 3 do Commit 4 (description inicial divergia do conteúdo real do YAML — corrigido pós-review). Sem o review separado, ambos teriam entrado.
- **Few-shot anchoring via exemplos consistentes.** §4.3 de `policy-reader/canonical.md` pós-Patch F5 carrega três exemplos de output de `check_applicability` com mesmo formato do trinque de provenance — anchor confiável para o implementador da Fase 2 que vai escrever o Matcher. Few-shot generoso (3 exemplos, não 1) é decisão deliberada de spec design.

### Conceitos fora do escopo da prova (registro)

- **Schema-as-contract vs implementation-as-server reforçado.** A separação estrutural × jurisdicional no `SCHEMA.md` materializa o princípio em duas camadas: estrutural universal (vive no projeto, schema-as-contract) e jurisdicional per-cliente (vive na Política do cliente, implementation-as-data). Pattern replicável quando emergir um terceiro eixo de variabilidade.
- **ADR como concretização arquitetural pré-implementação.** ADR-0005 escrito antes da Fase 2 (greenfield) — pattern "register before, not after". Contrasta com ADRs retrospectivos (0003 foi pós-aplicação). Padrão "register before" aplicável quando a arquitetura está fechada conceitualmente mas a implementação ainda não tocou nela — caso típico de greenfield com Spec-Driven Development.
- **Plan mode é literal.** "Exceto patches óbvios" não vale como atalho: Patch 1 do Commit 3 escapou da revisão por essa lógica e teve que ser recuperado. Lição: plan mode antes de patches contratuais é não-negociável, mesmo quando o patch parece mecânico.

### Calibrações metodológicas

- **Agrupamento por seção em commits densos de spec reduz drift entre revisor e executor.** Os patches originais do Commit 4 viraram 8 grupos por seção do arquivo (§1, §2.1, §2.2, §3.2, §3.3, §4.2, §4.3, §6.4/§7.1/§8), não 17+ rodadas individuais. Overhead de coordenação aceitável; ganho de coerência substancial — revisor vê todos os edits que tocam uma seção em uma única passagem, evita drift de terminologia entre patches contíguos. Metodologia destilável para commits densos futuros (Fase 1.5 `requirements.md` e `tasks.md` podem se beneficiar).
- **Handoff literal vs coerência interna é decisão no momento da aplicação.** Trailers de commit messages podem ser ajustados (`Refs ADR-0005 (next commit)` → `Refs ADR-0005`) quando o "next commit" envelheceria mal após squash-merge. Princípio: handoff é template, não contrato verbatim — coerência atemporal prevalece sobre fidelidade literal.
- **Nome de campo é invariante de schema; valor de campo é dado variável.** `description` (não `description_pt`) foi a escolha — o nome do campo independe do idioma do conteúdo. Argumento articulado pelo João. Pattern aplicável a qualquer schema bilíngue: estrutura em inglês, conteúdo na língua-alvo, sem refletir o idioma no nome do campo.
- **Coerência terminológica cross-doc é provenance secundária.** Quando `architecture-overview`, ADR-0005 e `DESIGN.md` divergem em uma frase de uma palavra, o auditor (humano ou Matcher futuro) tem que decidir qual prevalece. Convenção adotada: doc canônico (`architecture-overview`) lidera; demais ecoam. Aplicado em Commit 5.5 § Visão com a frase verbatim de §1 da overview.

### Decisões substantivas

Conteúdo canônico das decisões em ADR-0005; aqui só o registro do processo de cristalização.

- **ADR-0005 aceito como concretização arquitetural completa.** Versão original planejada na #14 era parcial (só LGPD-coupling em vocabulários jurisdicionais). Versão final cobre arquitetura multi-cliente inteira (Camada 1 per-cliente, vocabulários externalizados, `policy://vocabularies` como resource, trinque de provenance, multi-instance non-objective). Decisão tomada na abertura da #16: "se vamos abrir essa caixa, abrimos por inteiro".
- **`policy://vocabularies` como resource compartilhado Matcher+Classifier.** Tools do `policy-reader` continuam exclusivas Matcher. Boundary anterior "só Matcher consulta Política" relaxado para "só Matcher consulta tools da Política; resources são compartilháveis". Fronteira preservada porque resource não dá ao Classifier capacidade de inferir veredito — só capacidade de descrever no vocabulário correto.
- **POL-000 mantido como vocabulário universal (não jurisdicional).** Categorização de dados pessoais é semântica, não estatutária — POL-000 funciona em qualquer framework com conteúdo per-cliente. Permanece em `clauses/` (camada estrutural), não migra para `vocabularies/<framework>/`. Decisão registrada em ADR-0005 Decision 3.
- **`legal_framework` top-level único e imutável durante sessão do server.** Multi-framework simultâneo via múltiplas instâncias do server (cada uma com sua Política), não dentro de uma instância. Hot-swap durante sessão é deferimento explícito. Decisão registrada em ADR-0005 Decision 2.
- **§8.9 separada de §8.8 no canonical do `policy-reader`.** Em vez de mesclar a nova review-pass com a existente (sessão #12/#13), criei §8.9 nova com fechamento atemporal `Commit 4 da branch arch/multi-client-policy-rewrite`. Preserva histórico ADR-0003 Decision 2 (three beats lifecycle pós-aplicação) e sobrevive a squash-merge porque a branch aparece no PR title/body.
- **`semgrep-runner` per-cliente fica deferido a ADR futuro.** Generalização de regras sintáticas (namespace de `rule_id` cross-cliente, provenance de regras, semântica de detecção) é problema distinto do problema jurisdicional do `policy-reader` que motivou ADR-0005. Adiamento explícito em §7 do canonical, espelhado no compact §6. Decisão registrada em ADR-0005 Decision 8.

### Pendências para sessão #18+ ou ADR futuro

- Semântica de `last_revision` em `policy.yaml` — formal vs informativo, atualização manual vs automática, comportamento em CI.
- Semântica de `schema_version` no header dos YAMLs de vocabulário — coerência com `policy_schema_version` do header global, regras de bump quando vocabulário evoluir.
- Validação cruzada per-cliente (vocabulary × Semgrep metadata) quando materializar ADR de per-client rule set — `rule_id` que cita um valor de `operation` precisa que esse valor exista em `policy/vocabularies/<framework>/operation.yaml`.
- Formalização em ADR retroativo da convenção "português para docs técnicos não-ADR" (specs, `architecture-overview`, `DESIGN.md`, `SCHEMA.md`). Atualmente convenção implícita herdada das sessões #04-#11.
- ADR-0004 (uv + FastMCP 3.x) — número reservado desde sessão #14, decisão pendente. Inclui CVE 2.x check pendente desde #14 (confirmar contra NVD/GitHub Advisories).
- `mime_type` micro-débito em resources — FastMCP 3.x default é `text/plain`, declarar `application/json` no loader real.

### Artefatos produzidos

Branch `arch/multi-client-policy-rewrite` com 6 commits aplicados + 2 a aplicar (esta entry + handoff reescrito):

- `2612f99` — `docs(architecture)`: overview rewrite (7 patches cirúrgicos em §4.1, §4.2, §5.4, §5.5, §5.6, §5.7, §1).
- `c08bbd4` — `docs(adr)`: ADR-0005 multi-client architecture (354 linhas, 8 Decisions).
- `a54f99a` — `docs(schema)`: SCHEMA layered + `policy/vocabularies/LGPD/` (4 YAMLs, 49 valores totais: 22 `operation`, 18 `lawful_basis`, 2 `control`, 7 `out_of_scope`).
- `8583499` — `docs(spec)`: `policy-reader` canonical + compact (24+ edits no canonical em 8 grupos por seção, 13 edits no compact preservando paridade em contract surfaces).
- `823b03b` — `docs(spec)`: `semgrep-runner` per-client deferral (2 edits no canonical em §2.1 e §7, 1 edit no compact em §6).
- `d466f37` — `docs`: `DESIGN.md` entrypoint SDD (49 linhas, novo — wrapper de pointers para implementação Fase 2).
- Commit 6 (esta entry) — `docs(log)`: close session #16.
- Commit 7 (próximo) — `docs`: session-handoff reescrito para estado pós-Fase 1.

### Próximo passo

Fase 1.5 (Chat) — `docs/requirements.md` e `docs/tasks.md` em branch nova `docs/requirements-and-tasks` ramificando de main após PR da Fase 1 mergeado. Custo estimado 10-16h, uma ou duas sessões de Chat. Detalhamento em `session-handoff.md` (a reescrever no Commit 7).

Fase 2 (Code) começa depois, consumindo `tasks.md` task-a-task em ordem topológica. Estimativa 4-6 sessões de Code para policy-reader + semgrep-runner + integração CI/CD.

---

## 2026-05-15 — sessão #17 — REQUIREMENTS.md, calibração SDD via Rajasekaran 2026

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1.6 Task decomposition — limites de utilidade documentados.** Discussão sobre quando decomposition prescrita por framework deixa de agregar valor. Rajasekaran 2026 demonstrou empiricamente que sprint construct e fine-grained decomposition de Spec Kit-style frameworks viraram dead weight com Opus 4.6+. Lição aplicada: tasks.md migra de 15-25 fine para 8-12 médias, formalizado em ADR-0008.
- **D1.7 Session management — close limpo > resume com contexto sujo.** Decisão consciente de fechar #17 antes de discutir Matcher, em vez de empurrar Matcher pra dentro de sessão já longa com risco de degradar. Aplicação prática de "starting a new session with structured summary is more reliable than resuming with stale tool results".

**Domínio 4 — Prompt Engineering & Structured Output (20%)**

- **D4.6 Multi-instance review.** ADR-0008 Decision 3 formaliza independent review pass por Chat separada como gate de verificação. Padrão prescrito pelo exam guide, validado empiricamente por Rajasekaran 2026 no contexto adversarial generator-evaluator.

**Domínio 5 — Context Management & Reliability (15%)**

- **D5 Provenance via citation chain.** REQUIREMENTS.md → tasks.md → commit. ADR-0008 Decision 2 preserva essa chain ao amarrar acceptance de task ao RF/RNF upstream, evitando drift entre requirement e task statements.
- **D5 Context anxiety.** Conceito novo emergente em Rajasekaran 2026 — modelo encerrando trabalho prematuramente perto do que acredita ser limite de contexto. Vale internalizar como vocabulário de prova.

### Decisões substantivas

Conteúdo canônico de cada decisão em ADR correspondente; aqui só registro do processo.

- **REQUIREMENTS.md mergeado em PR #23 com 9 RFs + 2 RNFs.** Restrição MVP a operation_type: collection materializada em RF-004. Refs a ADR-0007 mantida como deferred citation matching pattern de ADR-0004 em RNF-001.
- **ADR-0006 (language conventions) aceito após calibração.** Closed-list em Decision 1 softened; POL-000 reframed em Decision 2 como camada arquitetural separada (não exceção); contagens de vocabulário corrigidas contra realidade dos YAMLs; leftover bullet de Aggregated > Negative reescrito.
- **ADR-0007 (MVP collection-only scope) deferido conscientemente.** Rationale do Code original ("research signal density") identificado como racionalização post-hoc; rationale real (sistema como ferramenta acessória a mapa de tagueamento de coleta) não foi capturado. Redação fica para sessão Chat dedicada antes de Fase 2.
- **ADR-0008 (task decomposition and verification) materializado nesta sessão.** SDD calibrado para Opus 4.7+: tasks médias amarradas a RFs, gate tripartite. Referência primária a Rajasekaran 2026.

### Validações empíricas

- **Independent review pass por Chat funcionou em PR #23.** Auditoria do João pegou drift que minha geração (Chat com contexto curto) introduziu — exemplos errados de operation tokens (`use, transfer, storage, deletion`) que não existiam no vocabulário canônico. Padrão D4.6 validado em prática real do projeto antes mesmo de ser formalizado.
- **Pause-and-ask pelo Code disciplinou expansão de escopo.** Sessão de cleanup do PR-23 manteve disciplina (descobertas que mereciam decisão consultaram, descobertas fora de escopo foram apenas flagged), contrastando com sessão anterior onde Code expandiu escopo silenciosamente gerando ADR-0006 e ADR-0007 não solicitados.

### Artefatos produzidos

- PR #23 (`docs/requirements-and-tasks`) mergeado em main, contendo:
  - `docs/REQUIREMENTS.md` v1.0 (9 RFs + 2 RNFs).
  - `docs/adr/0006-language-conventions.md` (Portuguese non-ADR docs convention + English jurisdictional vocab tokens).
  - Patches em `docs/specs/policy-reader/canonical.md` e `compact.md` (collect → collection).
- ADR-0008 a materializar em PR dedicado nesta sessão de fechamento.
- Atualização de `docs/process/proposta-tcc2.md` §7 com calibração SDD e §11 com duas novas referências.
- Atualização de `CLAUDE.md` com pointer a ADR-0008.

### Pendências para sessão #18+

- Discussão sobre Matcher como evaluator iterativo (Rajasekaran-pattern aplicado ao Matcher real da Fase 2): trade-off custo 2x tokens vs ganho em verdict accuracy.
- `docs/tasks.md` (Commit 1.5.2 original do plano da Fase 1.5) — agora calibrada por ADR-0008 para 8-12 tasks médias com gate tripartite.

### Próximo passo

Sessão #18 abre com agenda dupla: (a) discussão sobre Matcher como evaluator iterativo (decisão arquitetural significativa de Fase 2); (b) preparação para sessão dedicada de ADR-0007. tasks.md fica para sessão #19 ou intercalado conforme disponibilidade.

### Refinamento intra-sessão (continuação 2026-05-16)

Discussão pré-#18 sobre cobertura RF-por-task no Milestone A revelou conflação no ADR-0008 §2-§3 original: capability (externamente observável, RF-shaped, milestone-scope em prática) e function (output de unit de trabalho, test-shaped, task-scope) ambas amarradas ao task-level. Tasks internas (loader, AgentDefinition, scaffolding) sem correspondência 1:1 com capability eram forçadas a (a) inventar partial RF coverage ou (b) operar sem acceptance. Sintoma já visível na primeira proposta de Milestone A: 3 das 5 tasks (T01 loader, T02 retrieval tools, T04 resources) ficaram sem RF citado, e T07 (emit_report) cobria RF-006 sem declarar.

**Emenda aplicada in-place no mesmo dia.** Decisões 1-3 refinadas:

- §1: capability vive no milestone; task entrega função coerente dentro de seu milestone (loader, resource, tool, recognizer set, integration step).
- §2: RF binding migra para milestone scope. Tasks não bindam RFs individualmente.
- §3: gate split em **task-level** (function-specific pytest + independent Chat review) e **milestone-level** (manual exercise validando cada Dado/Quando/Então das RFs declaradas em §2). Tripartite per-task original colapsa em duas mecânicas no scope correto.
- Header do ADR ganha bloco "Amendment scope (2026-05-16)" registrando rationale, perímetro e justificativa.

**Companion edits aplicadas na mesma transação:** `CLAUDE.md` §"Working methodology" reescrito; `docs/process/session-handoff.md` (pendência #18 e prompt de abertura) atualizados; este registro.

**ADR-0004 também aterrissou na mesma extensão da sessão.** uv + FastMCP 3.x — número reservado desde #14, decisão substantiva agora registrada. Ratifica de-facto state operado desde #14 (pyproject.toml com uv_build, .python-version pinning 3.12.7, uv.lock versionado, FastMCP 3.x na skeleton). Rationale: lockfile reprodutibilidade (primário, gatilho "vai ser usado por outras pessoas na empresa"), Python version isolation (secundário que virou primário após falha empírica de pyenv-win com 3.14 paralelo), performance/no-admin/CLI familiarity (terciários). Supersede parcial de ADR-0001 §2. Companion edits: CLAUDE.md §"Stack (canonical)" ganhou bullet de dependency manager e versão de FastMCP; três entradas em session-handoff atualizadas (pendência ADR-0004 removida, drift de ADR-0001 reframed como editorial não-bloqueante).

**Justificativa de emenda in-place vs novo ADR-0009.** ADR-0008 fresco (24h); #18 (primeiro consumidor) ainda não rodou; greenfield sem deployment ou tasks.md autorada. ADR-0005 precedente usou refinement-via-novo-ADR mas operava sobre consumidor herdado (código semente da #14 + specs mergeadas). Aqui in-place preserva single-source-of-truth para Claude (consumidor primário de ADRs neste projeto) sem custo de migração; expectativa de imutabilidade não acionada porque nenhum artefato downstream foi autorado sob a versão original.

**Conceito de prova exercitado lateralmente.** Conflação capability×function no scope errado é forma específica de **abstraction leak no boundary**: §2 do original misturava dois eixos de design (decomposition strategy + acceptance criteria scope) que deveriam ter ficado ortogonais. Decoupling reverte a leak. Padrão destilável: quando uma decisão arquitetural produz fricção sistemática em aplicação (per-task RF binding produziu friction em 3+ pontos da primeira proposta de tasks), a hipótese default é conflação no nível da decisão, não no nível das tasks.

## 2026-05-16 — sessão #18 — ADR-0007 redigido, PR de access layer em ADRs, validação operacional do D4.6

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1.6 Task decomposition — scope discipline via flag-and-continue.** Code descobriu durante Task 5 do PR-30 que ADR-0001 carrega `## Pendências decorrentes` (linha 271, 4 bullets) estruturalmente paralela à `Follow-up patches` removida do ADR-0002 no mesmo PR. Padrão aplicado: surfaced o achado, não agiu, deixou decisão para o autor. Conscientemente classificada como out-of-scope do PR editorial; migrada para `session-handoff.md` como pendência operacional para sessão futura. Contraste explícito com session #17 (Code expandiu escopo silenciosamente gerando ADR-0006/0007 não solicitados). ADR-0008 amended formaliza isso como pattern de pause-and-ask.

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- **D3 `.claude/rules/` vs `.claude/skills/` vs `.claude/commands/`.** Discussão extensa sobre o primitivo correto para automação de geração de ADR/handoff/learning-log. Conclusão: rules path-scoped para convenções aplicáveis automaticamente quando Code toca o path (`docs/adr/**`, `docs/process/learning-log.md`); skills para procedimentos pesados com `context: fork`; commands para invocação explícita. Decisão deliberada: camada mecânica vai para rules; camada deliberativa permanece em Chat. Anti-padrão identificado: skill que "gera ADR completo" reintroduziria o problema de ADR-0007 (Code racionalizando rationale).
- **D3 Plan mode vs direct execution.** Prompt do PR-30 desenhado como direct execution (não plan mode) por critério explícito: trabalho mecânico, sem multiple valid approaches a deliberar, com pausas pré-identificadas para input humano. Heurística destilada: plan mode para *o que fazer*; direct execution para *como aplicar exatamente isso*.
- **D3 CLAUDE.md ↔ ADR drift surface.** Code identificou no relatório de simulação que CLAUDE.md duplica trechos de ADRs (escopo MVP, language conventions), criando surface de drift. Decisão registrada como tópico para sessão Chat dedicada (não cleanup mecânico): trade-off entre CLAUDE.md sempre carregado (precisa ser self-sufficient) vs single-source-of-truth nos ADRs.

**Domínio 4 — Prompt Engineering & Structured Output (20%)**

- **D4.6 Multi-instance review como gate operacional — escala documentada.** Session #17 reportou *uma* validação empírica deste padrão. Esta sessão adiciona **seis em um único PR**, cada uma com classe distinta. Material para defesa de TCC: D4.6 deixa de ser prescrição teórica para ter evidência operacional concreta de defeitos materiais capturados antes do merge.

**Domínio 5 — Context Management & Reliability (15%)**

- **D5 Lost-in-the-middle empiricamente endereçado.** Simulação de one-shot pelo Code reportou ADR-0005 (350 linhas, 8 Decisions) como "denso e útil para defesa de TCC; para Code, sinal baixo após o primeiro parse." Intervenção: "Decisions at a glance" index no topo (após Context, antes de Decision). Move informação do meio para o início sem alterar conteúdo. Aplicado a ADR-0001, ADR-0002, ADR-0005 — os três acima do threshold de >3 Decisions.
- **D5 Front-load routing, defer content.** Padrão `DESIGN.md` validado empiricamente (Code: "o melhor sinal/ruído de tudo"). Mesmo padrão aplicado intra-ADR via Decision index, e intra-MCP via `policy://catalog` vs `get_clause`.
- **D5 Provenance integrity via verbatim labels.** Cinco rounds de drift por reformulação pelo Chat (ADR-0005 rows 3/5; ADR-0002 rows 2/7; ADR-0001 ordering). Padrão destilado: Decision labels em índice são metadado *sobre* decisão deliberada, não interpretação *da* decisão; reformulação criativa pelo Chat — mesmo bem-intencionada — quebra essa fronteira. Falha sistemática quando Chat opera por reconstrução a partir de `project_knowledge_search` em vez de leitura direta.
- **D5 State-of-world maintenance em Consequences blocks.** Code identificou que remoção de `## Follow-up patches` do ADR-0002 deixou dangling reference + claim factual obsoleto em Decision 2 Consequences. Distinção destilada: Decision blocks são imutáveis sob editorial rules (mudar exige supersedes); Consequences blocks são descritivos de estado e merecem update quando estado muda. Regra editorial preservada.

### Decisões substantivas

Conteúdo canônico em ADR correspondente ou em commits de PR-30; aqui só registro do processo.

- **ADR-0007 (MVP collection-only scope) redigido em sessão dedicada Chat.** Rationale primário substituído: motivação real é "sistema é instrumentação para mapa de tagueamento de coleta de eventos de captura; coleta é o objeto natural do recorte porque é o que o sistema lê". Argumento "signal density 200 snippets / 22 operações" do draft original do Code descartado conscientemente como racionalização post-hoc. Decision 2 (Política mantém cláusulas non-collection) e Decision 3 (`check_applicability` retorna `not_applicable` com structured reason) preservadas com calibrações: removido lock-in literal da reason string; suavizado o "additive" de Decision 3 para "expansão é mechanism-side, não interface-side".
- **Pattern "Decisions at a glance" estabelecido para ADRs >3 Decisions.** Tabela de 3 colunas (#, Decision, Read when) inserida após `## Context` e antes de `## Decision`. Critério de inclusão de ADR: estritamente Decisions > 3. ADR-0003 (2 Decisions), ADR-0006 (3 Decisions, com tabela Scope summary já in-band), ADR-0007 (3 Decisions), ADR-0008 (amendment block já front-loaded) conscientemente fora de escopo. Decisão deliberada de **não aplicar uniforme**.
- **Pattern "ADRs não carregam todo-list operacional" emergente.** `## Follow-up patches` do ADR-0002 removida (todos 4 patches verificados aplicados). `## Pendências decorrentes` do ADR-0001 flagged para auditoria em sessão futura. Pendências operacionais vivem em `session-handoff.md`, não em ADR. Codificável em `.claude/rules/adr.md`.
- **Pattern "Decision labels verbatim-from-heading".** Estabelecido após 5 rounds de drift. Operacionalmente: índices são gerados pelo Code lendo o ADR diretamente; Chat propõe template e regras de origem, não escreve as labels.
- **Decisão de tooling preservada: rationale de `uv`** validado contra recuperação de sessão #14. Lockfile como artefato de provenance, gerenciamento de Python sem dependência de PATH, portabilidade via `pyproject.toml` PEP 621.

### Validações empíricas

- **Defense-in-depth em PR-30 capturou 6 defeitos antes do merge.** Pattern: Chat propõe → prompt instrui verificação verbatim → Code pausa em divergência → autor sanciona. Sem essa estrutura, 6 defeitos teriam mergeado, dois dos quais criariam contradição interna no projeto (`transient` vs `system` em ADR-0002 row 3; `schema` vs `spec` versioning em ADR-0002 row 6, este último colidindo com Immutable Rule 3 do ADR-0001).
- **D4.6 multi-instance review validado em escala operacional.** Seis catches distribuídos em quatro classes:
  - *Drift de reformulação* (5 casos): ADR-0005 row 3 (content drop), ADR-0005 row 5 (mechanism vs principle), ADR-0002 row 2 (content drop), ADR-0002 row 7 (general reduced to example), ADR-0001 expected ordering shift.
  - *Erro factual* (1 caso): ADR-0002 row 3, `transient` por `system`.
  - *Terminologia load-bearing* (1 caso): ADR-0002 row 6, `schema` por `spec` versioning.
  - *Drift de estado-do-mundo* (1 caso): ADR-0002 Decision 2 Consequences, claim factual obsoleto + dangling cross-reference.
  - *Descoberta fora de escopo* (1 caso): ADR-0001 `## Pendências decorrentes` paralelo ao Follow-up patches removido.
- **ADR-0003 (dual canonical+compact com escalation pointers) validado empiricamente.** Relatório de simulação one-shot do Code: "Não precisei [da canonical]. Compact teve densidade suficiente." Padrão prescrito → padrão exercitado em uso real → padrão confirmado.
- **ADR-0008 §3 (manual exercise gate) freou one-shot disguised.** Relatório de simulação: "isso me freou de assumir one-shot sem alertar você." Decisão burocrática na #17 evitou drift na #18.
- **DESIGN.md como entrypoint pattern validado.** Code: "o melhor sinal/ruído de tudo." Cinquenta linhas que orquestram a leitura dos outros docs.
- **ADR-0006 Decision 2 (English snake_case tokens em vocabulários) validada como anti-drift mechanism.** Investigação dos Follow-up patches do ADR-0002 confirmou que specs hoje citam "registrada em ADR-0002 §1" / "ADR-0002 §6" — referências resolvidas substituindo os forward-references originais. Padrão "specs citam ADR por ID, não duplicam" funcionou.
- **Pause-and-ask pelo Code cumprido em todas as 5 pauses do prompt PR-30.** Disciplina mecânica preservada; contraste com session anterior (sessão pré-#17) onde Code expandiu escopo silenciosamente.

### Artefatos produzidos

- **ADR-0007** (`docs/adr/0007-mvp-collection-only-scope.md`) redigido em sessão Chat dedicada com rationale autêntico do mapa de tagueamento. Status: Accepted (session #18, deferred from session #17 after PR-23 cleanup).
- **PR #30** (`docs/adr-access-layer`) com 3 commits:
  - `4840935` — ADR-0005 Decisions at a glance index (8 rows).
  - `cd348b5` — ADR-0002 Decisions at a glance index (Part 1, 7 rows) + remoção da seção `## Follow-up patches` + reescrita do parágrafo Consequences de Decision 2 para refletir estado-do-mundo atual.
  - `dc914cf` — ADR-0001 Decisions at a glance index (6 rows) + entry em `session-handoff.md` flagging `## Pendências decorrentes` como pendência para auditoria.
- **`session-handoff.md`** atualizado com entrada "Auditoria de seções todo-list em ADRs antigos" cobrindo os 4 bullets do ADR-0001 `## Pendências decorrentes`.

### Pendências para sessão #19+

- **`docs/tasks.md`** — em andamento na sessão #19. Governança: ADR-0008 (as amended 2026-05-16). Estrutura: Milestones A/B/C; Milestone A detalhado com ~5 tasks médias amarradas a RFs no scope milestone-level + gate tripartite. Pré-implementação POL-001 deve aparecer no plano da sessão.
- **`.claude/rules/adr.md`** — priorizada após acumulação de 5 regras emergentes nesta sessão:
  1. ADRs com >3 Decisions levam Decisions at a glance index após Context.
  2. Decision labels em índices são verbatim-from-heading; reformulação criativa pelo Chat é proibida.
  3. Decision indexes são gerados pelo Code lendo o ADR diretamente; Chat propõe template e regras de origem, não escreve labels.
  4. Decision blocks imutáveis sob editorial rules (mudar exige supersedes); Consequences blocks atualizáveis quando estado-do-mundo muda.
  5. ADRs não carregam seções de pendências operacionais (`Follow-up patches`, `Pendências decorrentes`, análogos). Pendências vivem em `session-handoff.md`.
- **Auditoria de `ADR-0001 ## Pendências decorrentes`** — 4 bullets (.python-version, branch protection, ~/.claude/CLAUDE.md user-scope, advisor outreach UTFPR). Alguns mecanicamente verificáveis, outros (advisor outreach) exigem confirmação manual. Decisão por bullet: remover se aplicado, migrar se ainda em aberto.
- **Análogas `.claude/rules/learning-log.md` e `.claude/rules/handoff.md`** — pendentes, derivam o mesmo padrão.
- **CLAUDE.md ↔ ADR drift surface** — discussão arquitetural sobre single-source-of-truth vs sempre-carregado. Sessão Chat dedicada, não cleanup mecânico.
- **Branch local cleanup** — `git push origin --delete docs/adr-access-layer` + `git branch -d docs/adr-access-layer` após merge do PR-30.

# Session handoff

**Última sessão fechada:** #18 (Chat) — 2026-05-16
**Próxima sessão:** #19 (Code) — implementação de T01 de Milestone A
**Branch ativa atual:** `docs/tasks-and-fixtures` (PR em main, em mergeação)
**Branch nova a abrir para #19:** `feat/policy-reader-implementation` (ramificar de main pós-merge)

## Estado atual

Fase 1.5 fechada. `docs/REQUIREMENTS.md` (9 RFs + 2 RNFs), `docs/adr/0004-uv-fastmcp-3x.md`, `docs/adr/0007-mvp-collection-only-scope.md`, `docs/adr/0008-task-decomposition-and-verification.md` (amended 2026-05-16) e `docs/tasks.md` v1.1 estão em main ou na PR em mergeação. Pacote POL-001..POL-004 está em `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/` como fixture isolada de teste — sem rationale, sem bump de `policy_version`, sem estabilização de SCHEMA §6. Implementação real (Fase 2) começa em Milestone A: cinco tasks (T01-T04 + T02b) para o `policy-reader` standalone, validáveis via MCP Inspector cross-tool, ancoradas em `docs/specs/policy-reader/canonical.md`.

Quatro débitos cross-doc no canonical.md estão anotados em `docs/tasks.md` §Companion edits para PR separada em sessão Chat dedicada: nome do campo `statutory_reference`, naming dos campos do `structured_context` no inputSchema de `check_applicability`, payload `reason` (vs `evidence`) em `not_applicable` conforme ADR-0007 Decision 3, e versão de FastMCP (canonical 2.x → real 3.x conforme ADR-0004). Estes débitos não bloqueiam Code de Milestone A — implementação adota o lado dos artefatos reais (já pinned em `tasks.md`), canonical alinha depois.

## Onde encontrar detalhes do que a Fase 1.5 cristalizou

- **Plano executável de Fase 2:** `docs/tasks.md` (Milestone A com cinco tasks; B/C/D referenciados, autoria deferida pós-gate milestone-level de A).
- **Contrato de aceitação global:** `docs/REQUIREMENTS.md` (RFs/RNFs com critério Dado/Quando/Então).
- **Governance de task decomposition e verificação:** `docs/adr/0008-task-decomposition-and-verification.md` (amended) — granularidade 8-12 tasks de 1-3h, gate task-level (function tests + Chat review independente) + gate milestone-level (manual exercise contra RFs).
- **Escopo MVP operacional:** `docs/adr/0007-mvp-collection-only-scope.md` (apenas `operation: collection` invoca matching no MVP v0.1.0; outras 21 operações do vocabulário retornam `not_applicable` com `reason` MVP-scope).
- **Stack management:** `docs/adr/0004-uv-fastmcp-3x.md` (uv como gerenciador, FastMCP 3.x).
- **Pack teste de check_applicability:** `tests/mcp_servers/policy_reader/fixtures/clauses_pack_check_applicability/README.md` (AS coverage por arquivo, pattern de fixture root assembly, ressalvas).
- **Processo de cristalização da sessão #18:** `docs/process/learning-log.md` (entry 2026-05-16).

## Pre-flight pins para a sessão #19 (Code, T01)

Cinco decisões pre-flight identificadas pela terceira passada Code de auditoria de `tasks.md` v1.1. Não vão para `tasks.md` (que é estável); vão para a descrição da PR de Milestone A ou para o prompt de abertura da sessão Code.

1. **Payload de `get_clause` (T02a) usa `statutory_reference`**, não `article_source`. Nome do campo segue o artefato real (`policy/SCHEMA.md` §5.1, `policy/clauses/POL-000.yaml`); canonical.md alinha em PR separada (Companion edit #1).
2. **Mecanismo de reasoning de `check_applicability` (T03) é regra programática determinística para Milestone A**. ADR-0005 Decision 7 dá liberdade entre regra/LLM/híbrido; tensão com pytest é estrutural — single LLM call vira teste flaky, AS-1..AS-5 de T03 assumem determinismo `(clause_id, structured_context) → veredito` idempotente. LLM-call fica para evolução pós-MVP quando regime de testes for ajustado.
3. **Validação de vocabulário runtime via `model_validator` ou validator function**, não `Literal[...]` dinâmico. `INVALID_OPERATION` e `INVALID_DATA_CATEGORY` (T03 AS-8) exigem validar `structured_context` contra vocabulários carregados em startup. Pydantic 2 `Literal` é estático em definition time — caminho correto: `inputSchema` declara `operation: str`, função body consulta estado carregado.
4. **`ReadResourceResult` shape validado empiricamente com MCP Inspector** na primeira hora de T01. Skeleton retorna `dict[str, Any]`; FastMCP 3.x auto-wrappa em `ReadResourceResult` com `contents: [TextResourceContents]`, mas o tipo concreto pós-wrap e o `mimeType` default precisam confirmação contra T01 AS-7 e T04 AS-4.
5. **`compatible_schema_range` em formato packaging-compatible**. Recomendação: trocar `policy/policy.yaml` para `compatible_schema_range: ">=0.1.0,<0.2.0"` (parseado nativamente por `packaging.specifiers.SpecifierSet`) em vez de manter `"0.1.x"` (que exige parser regex custom). Edit pequeno em `policy.yaml`, na mesma branch de implementação de T01.

## Pendências cross-sessão (organizado por horizonte de resolução)

**Resolver antes da #19 começar:**

- Merge da PR de `tasks.md` + pack POL-001..004 + handoff sync. Sem isso, branch de Code parte de main stale.

**Resolver em sessão Chat paralela (não bloqueia Milestone A):**

- PR de canonical.md sync (4 débitos listados em `docs/tasks.md` §Companion edits).
- Decisão Semgrep-on-Windows (Docker, pip native, remote worker, CI-only) — afeta forma de T05 em Milestone B, irrelevante para Milestone A.

**Resolver na #19 (Code, T01):**

- Edit em `policy/policy.yaml` para `compatible_schema_range: ">=0.1.0,<0.2.0"` (pre-flight pin #5).
- Validação empírica do `ReadResourceResult` shape (pre-flight pin #4).

**Resolver em #20+ ou ADR futuro:**

- Decomposição formal de Milestone B (semgrep-runner) em sessão Chat dedicada, após gate milestone-level de A completar. Decisão Semgrep-on-Windows precede.
- Decomposição formal de Milestone C (pipeline multi-agente) e Milestone D (CI/CD + validação empírica) em sessões Chat dedicadas, sequencialmente.
- Semântica de `last_revision` em `policy/policy.yaml` — formal vs informativo, atualização manual vs automática.
- Validação cruzada per-cliente (vocabulary × Semgrep metadata) quando materializar ADR de per-client rule set.
- ADR retroativo formalizando convenção "português para docs técnicos não-ADR".
- Promoção do draft `_drafts/spec-authoring-principles.md` para `docs/`.

## Defaults arquiteturais consolidados (pós-Fase 1.5)

Estado **realizado** (não plano em progresso). Referência canônica de cada item em ADR citado.

**Da Fase 1 (ADR-0005 — multi-client architecture):**

- Camada 1 (Política) é per-cliente; substituível por cliente sem alteração de código.
- `legal_framework` é campo top-level único do header, imutável durante sessão do server.
- POL-000 é vocabulário universal (semântico, não estatutário); vive em `policy/clauses/`, estrutura governada por `policy/SCHEMA.md` §5.
- Quatro vocabulários jurisdicionais (`operation`, `lawful_basis`, `control`, `out_of_scope`) vivem em `policy/vocabularies/<framework>/*.yaml`.
- `policy-reader` expõe três resources (`policy://catalog`, `policy://schema-version`, `policy://vocabularies`) e três tools (`get_clause`, `find_clauses_by_law_article`, `check_applicability`).
- `policy://vocabularies` é compartilhado Matcher+Classifier (read-only resource).
- `check_applicability` retorna trinca de provenance `(policy_schema_version, policy_version, legal_framework)` em todo sucesso.
- Sucessão de cláusulas é intra-Política, via `successors` no bloco `tombstone`.
- Mecanismo interno de reasoning de `check_applicability` é deferido (regra/LLM/híbrido livre para Code).
- `semgrep-runner` rule set é bundled no projeto no MVP.

**Da Fase 1.5 (ADR-0004 + ADR-0007 + ADR-0008 amended):**

- Stack management via `uv` + lockfile `uv.lock` versionado (ADR-0004).
- FastMCP 3.x como runtime MCP, Pydantic 2.13.x para validação (ADR-0004).
- Escopo MVP v0.1.0 de `check_applicability` é exclusivamente `operation: collection`. Outras 21 operações do vocabulário retornam `verdict: not_applicable` com `reason` MVP-scope, sem invocar matching (ADR-0007).
- Granularidade de Fase 2: 8-12 tasks de 1-3h agrupadas em milestones; cada milestone entrega capability declarada em REQUIREMENTS.md, cada task entrega função coerente (ADR-0008 amended §1).
- RFs/RNFs binding é milestone-level, não task-level (ADR-0008 amended §2).
- Gate de verificação em dois scopes: task-level (function tests + Chat review independente) e milestone-level (manual exercise contra RFs) (ADR-0008 amended §3).
- Bibliografia metodológica de referência: Rajasekaran (2026) "Harness design for long-running application development", Anthropic Engineering; Anthropic (2025) "Building Effective Agents" (ADR-0008 §4).

## Plano de ação Fase 2 — Code (sessões #19+)

**Input para Code.** `docs/tasks.md` v1.1 é o source-of-truth da Fase 2. Code consome task a task em ordem topológica (T01 → T02a → T02b → T03 → T04 para Milestone A; ordem subsequente conforme autoria dos próximos milestones), validando gate task-level conforme ADR-0008 §3 antes de marcar como done.

**Prompt de abertura da sessão #19 (Code, T01):**

> Implementar T01 de docs/tasks.md (loader + handshake policy://schema-version) para o policy-reader. Validar AS-1 a AS-8 em pytest sob uv run pytest antes de fechar. Ler antes: docs/tasks.md T01 inteira (Função, Dependências, Files, AS, Gate), docs/specs/policy-reader/canonical.md §3.2, policy/SCHEMA.md §3.1 + §4.5 + §6. Pre-flight pins do session-handoff aplicam — em particular: ReadResourceResult validado com Inspector (pin 4), compatible_schema_range trocado para ">=0.1.0,<0.2.0" no policy.yaml (pin 5), modelos Pydantic com model_validator runtime (pin 3). Após implementação, abrir sessão Chat separada para gate review do diff. Pausar e perguntar se algo na task estiver ambíguo.

**Estado de partida.** PR da Fase 1.5 (tasks.md + pack + handoff) mergeada em main. Code começa nova branch `feat/policy-reader-implementation` ramificando de main.

**Custo estimado.** Com cinco tasks de 1-3h cada, Milestone A é 8-12h de implementação cobrindo as cinco com gate task-level (pytest + Chat review por task). Gate milestone-level (manual exercise contra RFs 004-parcial, 005, 007-parcial, 008-parcial, 009) é sessão Chat dedicada de ~1-2h adicional, executada após T01-T04 fecharem. Total Milestone A: 10-14h, distribuídas em 4-6 sessões de Code de 2-3h cada.

## Hashes da Fase 1.5 (audit trail interno)

Branch `docs/tasks-and-fixtures` em PR. Hashes sobrevivem a squash-merge — após merge do PR, hashes individuais somem do main, mas ficam registrados aqui:

- `<TBD>` — docs(tasks): add tasks.md v1.1 for Milestone A implementation
- `<TBD>` — test(policy-reader): add POL-001..004 fixture pack for check_applicability
- `<TBD>` — docs: sync session-handoff.md to Milestone A/B split + Fase 1.5 close
- `<TBD>` — docs(log): close session #18 — tasks.md authoring + POL fixture pack

(Hashes preenchidos após `git log` da branch antes do merge.)


### Nota de calibração metodológica

O fluxo desta sessão (Chat-delibera / prompt-com-pausas-explícitas / Code-executa-com-verificação / autor-sanciona) operou em escala documentada (5 pausas, 6 catches) sem nenhum defeito mergeado. Contraste empírico com sessão pré-#17 (Code expandindo escopo silenciosamente). A diferença operacional é a *estrutura do prompt*, não a capacidade do modelo: pausas pré-identificadas, verificações obrigatórias, pedido explícito de leitura direta em vez de inferência. Vale carregar "o prompt do PR-30" como referência operacional para futuros prompts de Code que tocarão artefatos sensíveis — candidato a exemplo no arquivo `.claude/rules/adr.md` quando aquela rule for redigida, ou a slash command em `.claude/commands/`.

## 2026-05-16 — sessão #19 — T01 (Loader + handshake policy://schema-version) + 
PR cleanup cross-doc

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1.6 Task decomposition — calibração via Rajasekaran 2026 contestada e 
  defendida.** Sessão abriu com pergunta sobre "task por task vs Milestone 
  inteira" referenciando o paper "Harness design for long-running application 
  development". Confirmado via leitura direta do paper: V1 → V2 (Opus 4.5 → 
  4.6) removeu *sprints internos* mantendo planner+evaluator. ADR-0008 não 
  conflita — o "Chat review independente" é human-in-the-loop deliberado, 
  ancorado em audit trail acadêmico, não scaffold para impedir o Code de 
  perder coerência. Padrão generator/evaluator do paper *valida* a separação 
  Code/Chat de ADR-0008 §3.

**Domínio 2 — Tool Design & MCP Integration (18%)**

- **D2 Resource vs Tool em handler concreto.** `policy://schema-version` 
  implementado como resource (idempotente, sem args, reflete estado). 
  Descoberta empírica do Code: `mcp.read_resource(uri)` em FastMCP 3.2.4 
  retorna tipo interno do framework (`ResourceResult.content` / 
  `.mime_type`); `.to_mcp_result(uri)` produz tipo canônico MCP 
  (`ReadResourceResult.contents: [TextResourceContents]` com `.text` / 
  `.mimeType`). AS-7 referenciava wire-shape MCP literalmente — sem essa 
  distinção, teste verde teria mascarado incompatibilidade com qualquer 
  outro cliente MCP. Anchor test `test_documents_fastmcp_read_resource_shape` 
  permanece na suíte como detector de breaking change futuro.
- **D2 Custom URI scheme (`policy://`).** Materialização do princípio 
  registrado em ADR-0002 §7 — scheme custom, três resources sob ele, 
  semântica idempotente.
- **D2 isError flag e classes de erro (preparação para T02a-T03).** Não 
  exercitado diretamente em T01 (resources não usam isError; tools sim), 
  mas o `PolicyLoadError` único em T01 dá precedente para a categoria 
  system que T03 vai precisar mapear via errorCode.

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- **D3 Plan mode em ação.** Prompt v4 de T01 estruturado em duas fases com 
  gate de OK entre elas (Plano → autor sanciona → Implementação). Cinco DDs 
  identificadas na Fase 1, todas decisões substantivas que mereceram 
  deliberação Chat antes de Code implementar. Padrão "plan mode para *o que 
  fazer*; direct execution para *como aplicar exatamente isso*" (destilado 
  na #17) operou como prescrito.
- **D3 CLAUDE.md como prescritivo vivo.** PR de cleanup pré-T01 atualizou 
  CLAUDE.md §Immutable rule 2 substituindo `article_source` por 
  `statutory_reference`. Regra imutável carregando nome de campo errado 
  era exatamente o tipo de drift que vira contaminação sistêmica.

**Domínio 4 — Prompt Engineering & Structured Output (20%)**

- **D4.6 Multi-instance review como gate operacional — três rounds.** 
  (a) Gate Chat review da PR de cleanup capturou o argumento "ampliar escopo 
  porque a forma editorial ficou mais limpa" e o recusou — separação entre 
  correção editorial e governance de escopo de PR. (b) Gate Chat review do 
  plano de T01 capturou cinco DDs antes do diff. (c) Gate Chat review do 
  diff de T01 confirmou aplicação das DDs e validou achado empírico do 
  wire-shape MCP. Três rounds, três classes distintas de catches.

**Domínio 5 — Context Management & Reliability (15%)**

- **D5 Front-load routing, defer content — falha capturada empiricamente.** 
  Prompt v1 de T01 ignorou DESIGN.md como entrypoint, copiando reading list 
  literal do handoff. Autor pegou a falha questionando. v2 reorganizada em 
  torno do DESIGN.md como mapa. Lição: front-load routing só funciona se 
  invocado nos prompts; senão entrypoint vira documento órfão.
- **D5 Provenance via PRs sequenciais.** Cleanup cross-doc → main → T01 → 
  main. PRs encadeadas (alternativa rejeitada) confundiriam audit trail 
  para banca. Decisão favoreceu trilha linear auditável.
- **D5 Anchor test para detectar breaking change.** Padrão "build the canary 
  that screams first" aplicado a wire-shape FastMCP. Asserts mínimos sobre 
  dois tipos de retorno — falha primeiro se release futura mudar wrap.

### Conceitos fora do escopo da prova

- **PR encadeadas vs sequenciais (git workflow).** Discussão sobre ramificar 
  T01 da branch de cleanup antes do merge vs esperar merge e ramificar de 
  main. Resolvida em favor de sequencial por audit trail; PR encadeada 
  funciona tecnicamente mas exige reasoning sobre estado intermediário.
- **`git stash -u` para preservar untracked.** Detalhe operacional do 
  workflow para recuperar T01 quando branch de cleanup virou zumbi.

### Decisões tomadas

- **Pin 5 do session-handoff (`compatible_schema_range` em `policy.yaml`) 
  descartado por achado empírico.** Sessão Chat capturou que o campo *não 
  existe* no `policy.yaml` real — é constante do componente, não da 
  Política. Recomendação do pin originada por confusão entre exemplo de 
  resource e fonte do valor. Substituído por diretiva técnica dentro do 
  prompt: `COMPATIBLE_SCHEMA_RANGE = SpecifierSet(">=0.1.0,<0.2.0")` 
  module-level em `loader.py`.
- **Pin 3 (model_validator runtime) cortado do prompt por redundância.** 
  Restrição já está em tasks.md T01 §Gate task-level Chat review 
  praticamente verbatim. Repetir no prompt era duplicação.
- **Pin 4 (validação empírica do shape FastMCP) mantido com método 
  refinado.** Inspector manual substituído por unit test exploratório via 
  `mcp.read_resource(...)` dentro do loop pytest. Achado empírico do Code 
  validou o método: distinguir tipo interno do FastMCP vs wire-shape MCP 
  canônico.
- **PR cleanup cross-doc escopo: incluir CLAUDE.md + REQUIREMENTS.md; 
  excluir canonical/compact (pinned), semgrep-runner canonical (silêncio 
  em tasks.md não autoriza), proposta-tcc2 (artefato histórico), 
  metadocs (tasks.md, handoff, ADRs, learning-log).**
- **Forma editorial da substituição FastMCP: "FastMCP 2.x conforme 
  ADR-0001" → "FastMCP 3.x conforme ADR-0004".** Sugestão do autor; 
  superou as três opções (a/b/c) do Code por preservar citation accuracy 
  (cada ADR citada para a decisão que efetivamente tomou).
- **Cinco DDs de T01 aprovadas:** (1) `SubstantiveClause` flexível 
  com `extra="allow"`; (2) AS-5 valida lei em todos os 
  `statutory_reference` aninhados; (3) `packaging>=24` declarado 
  explícito em deps; (4) `_STATE` module-level + `_bootstrap()` em vez 
  de factory; (5) `pytest-asyncio>=0.24` + `asyncio_mode = "auto"`.

### Artefatos produzidos

- **PR cleanup-stale-references** (mergeada em main). Dois commits 
  separados: `chore(docs): rename article_source to statutory_reference 
  per SCHEMA.md` + `chore(docs): update FastMCP version references to 
  3.x per ADR-0004`. Cinco arquivos tocados: `DESIGN.md`, 
  `architecture-overview.md`, `CLAUDE.md`, `REQUIREMENTS.md`.
- **PR T01** (mergeada em main). Branch `feat/policy-reader-implementation`. 
  Implementação: `loader.py` (novo), `models.py` (novo), `errors.py` (novo), 
  `server.py` (modificado), `tests/.../conftest.py` (novo), 
  `tests/.../test_bootstrap.py` (novo, 11 testes), `pyproject.toml` 
  (adições: packaging, pytest-asyncio, types-PyYAML, 
  `asyncio_mode = "auto"`).

### Validações empíricas

- **Gate task-level ADR-0008 §3 cumprido em escala documentada.** 
  Pytest verde (11/11), ruff verde, mypy verde, Chat review independente 
  realizado em sessão separada da que codou (esta Chat = Chat review; 
  Code session = implementação).
- **Wire-shape FastMCP 3.2.4 empiricamente capturado.** Anchor test 
  permanece na suíte como sinal de alerta para release futura.
- **Pattern "consertar na fonte" em vez de "workaround no prompt" 
  validado.** Autor recusou múltiplas tentativas (minhas) de adicionar 
  notas no prompt cobrindo débitos conhecidos. Cleanup cross-doc em PR 
  separada antes de T01 produziu prompt v3 mais limpo. Caveat: nem todo 
  débito é consertável na fonte (canonical/compact ficaram pinned), e v4 
  do prompt acabou ganhando uma nota curta sobre o débito residual em 
  compact.md. Pattern funciona quando o conserto na fonte é viável; 
  caso contrário, nota explícita curta é o segundo-melhor.

### Pendências para sessão #20+ ou ADR futuro

- **T02a (get_clause).** Próxima task topológica de Milestone A.
- **PR Chat dedicada de canonical sync.** Quatro débitos de tasks.md 
  §Companion edits cross-doc + um quinto descoberto pelo Code 
  (`tasks.md` l.229 cita canonical §8.7 que aparentemente não existe 
  na numeração atual). Janela ótima: entre T03 e T04, ou após T04 mas 
  antes do gate milestone-level.
- **Decomposição formal de Milestone B em sessão Chat dedicada.** Após 
  gate milestone-level de A. Decisão Semgrep-on-Windows precede.

### Nota de calibração metodológica

Sessão #19 operou em três turnos distintos com gates intermediários: 
preparação (definir prompt T01 com cinco rounds de pushback do autor sobre 
escopo, leitura obrigatória, pre-flight pins), execução Code (T01 
implementada), gate Chat review (esta sessão). A estrutura "prompt forte 
com pause-and-ask + Code executa Fase 1 → autor valida DDs → Code executa 
Fase 2 → Chat review independente" exercitou o que ADR-0008 §3 prescreve 
em forma operacional, materializando padrão do paper Rajasekaran 
(generator + evaluator separados) com customização para human-in-the-loop 
acadêmico. Defense candidate strong: contrastar com fluxo pré-#17 (Code 
expandindo escopo silenciosamente) — diferença operacional é a 
*estrutura do prompt*, não a capacidade do modelo.

---

## 2026-05-17 — sessão #20 — T02a + canonical-sync-A + canonical-sync-A.2

**Foco.** Implementação de T02a (`get_clause` + migração `server.py` inline →
`tools.py`); descoberta de AS não-executável durante validação empírica de
wire-shape (FastMCP 3.2.4 sem caminho público para `isError: true` +
`structuredContent` simultâneo); adaptação Option B; duas PRs mecânicas de
sync cross-doc (`canonical-sync-A` em policy-reader spec; `canonical-sync-A.2`
em semgrep-runner spec).

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1 multi-agent coordinator-subagent com human-in-the-loop.** Padrão de
  T01 escalou para três rounds de prep (v1 Chat → integração com sugestão
  Code → v2 → três correções factuais do autor → v3 final). Cada round
  reduziu superfície de erro do prompt; v3 capturou três erros factuais que
  v2 carregava (PR cleanup pré-T01 tocou cinco docs, não dois ou quatro;
  helper de teardown tem dois nomes diferentes em server.py vs conftest.py;
  débito FastMCP em canonical ainda existe).
- **D1 escalation pattern materializado em escala documentada.** Code de
  T02a Fase 2 detectou AS não-executável no primeiro ato exploratório
  (validação empírica de wire-shape de tool em FastMCP 3.2.4 via in-memory
  Client). Parou antes de implementar errado, propôs três opções de
  adaptação com recomendação. Chat validou externamente via web search
  (issue #4202 do IBM mcp-context-forge confirmou prática estabelecida no
  ecossistema). Autor ratificou Option B. Código prosseguiu. Defense
  candidate forte para Capítulo 4 do TCC.
- **D1 task decomposition + scope discipline.** Três PRs distintas em uma
  sessão (T02a feature; canonical-sync-A mecânica três commits;
  canonical-sync-A.2 mecânica um commit). Cada uma com escopo único e diff
  visual auditável. Anti-pattern "PR mista" evitado por scope discipline
  explícita no prompt.

**Domínio 2 — Tool Design & MCP Integration (18%)**

- **D2 tool description anatomy.** Prosa inline com when-to-use,
  do-not-use, formato de output, condições de erro — sem seções nomeadas
  obrigatórias. Convenção canonical §4.1 aplicada em `get_clause`.
- **D2 output polimórfico via Pydantic discriminated union.**
  `DefinitionalClause | SubstantiveClause` carregado em T01 projetado
  direto via `clause.model_dump(mode="json", exclude_none=True)` para
  `structuredContent`. POL-000 (definitional) carrega `defines`/
  `out_of_scope`; POL-001 (substantive) carrega `applies_to`/`control`/
  `requirements`/`exceptions`; POL-003 (deprecated) adiciona `tombstone`.
  Polimorfismo visível no payload sem código de adaptação.
- **D2 error envelope estruturado + discriminador implícito.**
  `ErrorEnvelope` Pydantic com `{errorCode, message, isRetryable, details}`
  per canonical §5.1. Discriminador entre sucesso e erro: presença do
  campo `errorCode` no `structuredContent`. Documentado em
  `ErrorEnvelope.__doc__` e em anchor test.
- **D2 isError flag — gap entre MCP spec teórica e FastMCP 3.2.4 wire
  real.** MCP spec permite `isError: true` + `structuredContent` simultâneo;
  FastMCP 3.2.4 expõe dois caminhos públicos mutuamente exclusivos
  (`return dict` → `isError=False` + `structuredContent` populado; `raise
  ToolError` → `isError=True` + `content[0].text` apenas). Convenção
  Option B adotada: envelope sempre em `structuredContent`; wire `isError`
  reservado para protocol-level failures.
- **D2 built-in tools.** Code usou Read/Write/Edit/Grep/Bash em todas as
  três sub-sessões. Catch específico em canonical-sync-A: três passadas de
  `Edit replace_all` com delimitadores diferentes (backtick, JSON key,
  YAML key) em vez de `replace_all` global ingênuo, para preservar
  `article_sources_summary` (campo composto plural cuja forma exata é
  diferida em T04).

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- **D3 plan mode pattern materializado em todas as três sub-sessões.**
  "Plan → gate de OK → Implementation" em T02a; "verify state → mechanical
  edit → gate" em canonical-sync-A; idem em A.2. Plan mode em commits
  substantivos; direct execution em commits mecânicos (heurística
  destilada na #12 reaplicada).
- **D3 `uvx tool` vs `uv run --with tool`.** Code de canonical-sync-A
  descobriu que `uv run ruff` e `uv run mypy` retornam "program not found"
  porque ferramentas não estão em dev-deps via `uv sync`. Workaround
  adotado: `uvx ruff` (download isolado, para tools que rodam stand-alone
  como linters) e `uv run --with mypy mypy` (injeta no venv do projeto,
  necessário para mypy enxergar packages instalados). Distinção
  load-bearing para CI/CD scenarios.

**Domínio 4 — Prompt Engineering & Structured Output (20%)**

- **D4 JSON schema mínimo + validação canônica.** `inputSchema` MCP de
  `get_clause` carrega apenas `clause_id: str` (sem `pattern` constraint
  no schema). Validação de `^POL-\d{3}$` dentro da função, emitindo
  errorCode canônico `INVALID_CLAUSE_ID_FORMAT` com `details: {provided,
  expected_format}` per canonical §5.4. Decisão consciente: schema
  validation pelo framework rejeitaria com errorCode genérico, perdendo
  contrato.
- **D4 Pydantic discriminated union sobrevivente cross-task.** Modelo de
  T01 (`Clause = DefinitionalClause | SubstantiveClause` discriminado por
  `clause_type`) reutilizado direto em T02a sem refactor.
- **D4 `model_dump(mode="json", exclude_none=True)`.** Projeção limpa de
  Pydantic para JSON wire format; `exclude_none=True` remove
  `tombstone: None` de cláusulas active. Trade-off: remove TODO campo
  None, não só tombstone — vale auditar em T04 quando catalog expor mais
  campos nullable com semântica.

**Domínio 5 — Context Management & Reliability (15%)**

- **D5 error propagation com payload estruturado.** Discriminador implícito
  por presença de campo (`'errorCode' in structuredContent`) em vez de
  flag explícito do wire — padrão alinhado com escalation que a prova
  cobra como cenário.
- **D5 scope discipline em PRs.** Três PRs mecânicas separadas
  (`canonical-sync-A` em três commits, `canonical-sync-A.2` em um commit)
  vs uma PR mista — Pareto front review-ability vs blast radius. A.2 foi
  descoberta DURANTE execução de A (Code flagou outro débito FastMCP
  análogo em semgrep-runner spec), validando que PRs mecânicas pequenas
  descobrem débitos análogos durante execução, padrão superior a sweep
  única tentativa de capturar tudo upfront.
- **D5 anchor test como regressão de wire-shape.**
  `test_documents_fastmcp_tool_call_shape` em `test_get_clause.py`
  complementa `test_documents_fastmcp_read_resource_shape` de T01. Família
  cobre os dois shapes de retorno do componente (resource via
  `read_resource`, tool via `call_tool`). Documenta convenção Option B
  como regressão executável: se framework expor caminho que preserve
  `isError` + envelope estruturado simultâneo, anchor falha primeiro.

### Decisões fechadas

**T02a — seis DDs.**

- **DD-1.** Payload de retorno em sucesso via `clause.model_dump(mode=
  "json", exclude_none=True)` direto sobre instância carregada por T01.
  Polimorfismo visível.
- **DD-2.** `ErrorEnvelope` com `details: dict[str, Any]` aberto, não
  union discriminada. Helpers funcionais por errorCode em `tools.py`
  privados a T02a; promoção para módulo compartilhado quando segundo
  consumidor (T02b/T03) demonstrar reuso real.
- **DD-3.** Validação `^POL-\d{3}$` dentro da função (não em
  `inputSchema` MCP); emite `INVALID_CLAUSE_ID_FORMAT` estruturado.
- **DD-4.** `content[0].text` com templates inline pequenos por caso
  (active substantive, active definitional, deprecated, erro); sem helper
  genérico compartilhado. Renderização literal de inciso (`"inciso 1"`,
  não `"inciso I"`) — romano fica para Reporter pós-Milestone C.
- **DD-5.** `tools.py` com uma função pública (`get_clause`); thin
  wrapper `@mcp.tool` em `server.py` chamando `tools.get_clause(clause_id,
  _STATE)`. `find_clauses_by_law_article` e `check_applicability`
  permanecem stubs inline em `server.py` até T02b/T03 migrarem cada um na
  sua sessão.
- **DD-6 (dois itens cross-doc descobertos).**
  - (a) `applicability_scope` (flat list em canonical §4.1) vs
    `applies_to` (dict polimórfico em SCHEMA §6 + T01 model + fixtures).
    T02a adota `applies_to`; diferença anotada como débito cross-doc
    novo.
  - (b) `isError`-semantics em canonical §5.1 não realizável em FastMCP
    3.2.4 via API pública. Convenção Option B adotada: envelope em
    `structuredContent`; wire `isError` reservado para protocol-level.
    Validação externa via issue #4202 do IBM mcp-context-forge.
    Discriminador implícito por presença de `errorCode`.

**canonical-sync-A.**

- Três commits separados em uma PR — escopo semanticamente disjunto
  justifica split. (Opção A vs commit único Opção B; Opção A escolhida
  por scope discipline.)
- Forma editorial FastMCP consolidada de #19 aplicada com discriminação
  gramatical: §1 (citação modifica versão diretamente) → substituição
  inteira `"FastMCP 2.x conforme ADR-0001"` → `"FastMCP 3.x conforme
  ADR-0004"`; §8.7 (citação modifica Stack, versão em parêntese) → troca
  apenas versão, preserva ADR-0001.
- `article_sources_summary` preservado em ambos os docs (composto plural,
  forma exata diferida em T04).
- `effective_date` e `last_revision` em `policy.yaml` quoted como strings
  ISO 8601 per SCHEMA §3.1.

**canonical-sync-A.2.**

- Mesma forma editorial mecânica aplicada a
  `docs/specs/semgrep-runner/canonical.md`. Duas substituições (L22 regra
  #1, L415 regra #2). `compact.md` do semgrep-runner não tem débito
  FastMCP — explicit non-finding documentado no relatório.

### Artefatos produzidos

- **PR T02a** (branch `feat/policy-reader-get-clause`, mergeada em main).
  Implementação: `src/mcp_servers/policy_reader/tools.py` (novo,
  `get_clause` pure function + helpers privados), `models.py` (modificado
  com `ErrorEnvelope`), `server.py` (thin wrapper `@mcp.tool` delegando
  para `tools.get_clause`). Testes:
  `tests/mcp_servers/policy_reader/test_get_clause.py` (novo, 9 testes:
  anchor wire-shape + AS-1.a POL-000 definitional + AS-1.b POL-001
  substantive + AS-2 POL-003 deprecated + AS-3 parametrizado 4 IDs
  inválidos + AS-4 not found); `conftest.py` (fixture
  `policy_root_with_pack_clauses`). Gate: pytest 20/20, ruff clean,
  mypy clean.
- **PR canonical-sync-A** (branch `feat/canonical-sync-A`, três commits
  separados, mergeada em main). 3 arquivos tocados: `docs/specs/
  policy-reader/canonical.md`, `docs/specs/policy-reader/compact.md`,
  `policy/policy.yaml`. 20 substituições total (16 + 2 + 2). Gate: pytest
  20/20, ruff clean, mypy clean, PyYAML coerce ISO strings.
- **PR canonical-sync-A.2** (branch
  `feat/canonical-sync-A.2-semgrep-runner`, um commit, mergeada em main).
  1 arquivo tocado: `docs/specs/semgrep-runner/canonical.md`. 2
  substituições. Gate: pytest 20/20 (regressão policy-reader zero), ruff
  clean, mypy clean.

### Validações empíricas

- **Wire-shape FastMCP 3.2.4 para tool calls empiricamente capturado.**
  Caminho público: `fastmcp.Client(server.mcp).call_tool(name, args)` →
  `fastmcp.client.client.CallToolResult` com snake_case attrs. Tool
  retorna dict → wire `isError=False` + `structuredContent=dict`; tool
  raise `ToolError(s)` → wire `isError=True` + `content[0].text=s` +
  `structuredContent=None`. Não há caminho público que combine ambos.
  Confirmado via leitura de `fastmcp/tools/base.py:124-137 to_mcp_result`
  + `Tool.convert_result` em base.py:340-401 + `mcp/server/lowlevel/
  server.py _make_error_result`. Validação externa: issue #4202 do IBM
  mcp-context-forge confirma prática estabelecida ("Forces non-compliant
  implementations").
- **Convenção Option B materializada em três lugares.** Anchor test +
  `ErrorEnvelope.__doc__` + relatório de gate de T02a. Pendente:
  documentação formal em canonical §5.1/§5.2 + amendment ADR-0002 (vão
  para canonical-sync-B).
- **Polimorfismo `DefinitionalClause | SubstantiveClause` sobrevivente
  cross-task.** Modelo de T01 reusado direto em T02a sem refactor. AS-1
  com dois cenários (POL-000 + POL-001) captura regressão polimórfica
  cedo, antes que T03/T04 introduzam pressão sobre o modelo.
- **Pattern "PR mecânica pequena descobre débitos análogos durante
  execução".** Code de canonical-sync-A flagged que
  `docs/specs/semgrep-runner/` tinha mesmo débito FastMCP 2.x. Antes
  desse achado, varredura era considerada completa em quatro débitos
  conhecidos do policy-reader. Lição: PRs mecânicas valem mais que sweep
  única-tentativa para capturar todos os débitos upfront — varredura
  incremental por escopo descobre o que sweep única não capturaria.
- **Gate task-level ADR-0008 §3 cumprido em escala estendida.** T02a +
  duas PRs mecânicas, todas com gate verde. Pytest 20/20 em todas as
  três; ruff/mypy clean em todas. Chat review independente sobre cada uma.
- **Padrão "consertar na fonte" testado em escala maior.** Cleanup
  canonical-sync-A.2 disparado por achado de A foi conserto-na-fonte de
  débito que A.2 só descobriu durante execução. PR-A original não
  precisou de "nota no prompt cobrindo débito semgrep-runner" porque A.2
  pegou direto.

### Pendências para sessão #21+ ou ADR futuro

- **canonical-sync-B do policy-reader.** Sessão Chat dedicada antes de
  T02b. Cobre dois itens com decisão de design + um amendment ADR:
  - `applicability_scope` → `applies_to` em canonical §4.1 (cobertura
    polimórfica `DefinitionalClause | SubstantiveClause` required;
    granularidade da exposição de sub-campos
    `personal_data_categories`/`operation`; paralelismo com
    `check_applicability.structured_context` §4.3).
  - `isError`-semantics em canonical §5.1 + §5.2 (documentação Option B;
    descrição do constraint FastMCP — explícita vs implícita;
    discriminador formal — declarar em §2 e/ou §5.1).
  - Amendment a ADR-0002 (MCP conventions) refletindo Option B.
- **Possível canonical-sync-B do semgrep-runner.** Deliberar na prep de
  Milestone B. Code de A.2 leu §1 e §8.6 do canonical e não encontrou
  análogos aos achados de policy-reader, mas varredura completa só na
  prep de Milestone B.
- **DX residual — linters como dev deps em `pyproject.toml`.** Workaround
  atual via `uvx ruff` e `uv run --with mypy mypy` funciona, mas dev deps
  oficiais reduzem fricção. Sessão Code curta (~15min) em janela
  futura.
- **Limpeza dos bullets em `tasks.md` §Companion edits cross-doc dos
  débitos fechados** (article_source, FastMCP 2.x em policy-reader e
  semgrep-runner, e em algum momento applicability_scope +
  isError-semantics pós-canonical-sync-B). Sessão Chat de housekeeping
  pós-canonical-sync-B.
- **T02b** (`find_clauses_by_law_article`). Próxima task topológica de
  Milestone A. Pré-leitura consome canonical já limpo pós-canonical-sync-B.
- **Itens deferidos T03** (já listados em `tasks.md` §Companion edits):
  `operation`/`legal_basis` vs `operation_type`/`declared_legal_basis`;
  `evidence` vs `reason` em `not_applicable`. Resolver pós-T03 quando
  spec for empiricamente validado.
- **Decomposição formal de Milestone B em sessão Chat dedicada.** Após
  gate milestone-level de A. Decisão Semgrep-on-Windows precede.

### Nota de calibração metodológica

Sessão #20 operou quatro turnos com gates intermediários:

1. **Prep T02a em Chat** (v1 → integração com sugestão Code → v2 → três
   correções factuais do autor → v3 final). Padrão de iteração coordenado
   onde cada round reduziu superfície de erro. v1 tinha erro factual
   (afirmava que PR cleanup tocou dois docs) que v2 corrigiu para "quatro
   docs prescritivos"; v3 corrigiu para "cinco arquivos" após João medir.
   Lição: prep iterativa entre Chat principal + Code secundário superou
   prep monolítica.

2. **Execução Code de T02a** (Fase 1 plano com 6 DDs explícitas + DD-6
   levantada como nova; gate de OK; Fase 2 com AS não-executável detectado
   no primeiro ato exploratório → escalation pattern → web search
   validação no Chat → ratificação Option B → implementação completa).
   Primeira aplicação do escalation pattern em escala documentada do
   projeto. Code parou ANTES de implementar errado, propôs três opções,
   recomendou a viável. Material defense candidate forte: contraste
   empírico com fluxo onde Code implementa primeiro e descobre problema
   depois (Code → Chat de bug fix retroativo).

3. **Chat review independente de T02a + execução de canonical-sync-A**
   (prompt mecânico curto, Code executou com discriminação gramatical
   correta em §1 vs §8.7 do canonical policy-reader; flagou catch
   específico do `article_sources_summary` como composto preservado).

4. **canonical-sync-A.2 follow-up** (descoberto na execução de A; escopo
   idêntico aplicado a semgrep-runner spec; explicit non-finding sobre
   compact.md do semgrep-runner documentado).

Padrão emergente da sessão: **scope discipline funciona como
contracampo da escalation pattern**. Quando Code escala (AS
não-executável em T02a), Chat decide; quando Code descobre débito lateral
(FastMCP em semgrep-runner durante A), Chat NÃO estende escopo de A —
abre A.2 separada. Escalar é mecanismo para resolver; descobrir é
mecanismo para registrar. Funções distintas, ambos legítimos, ambos
operados via prompt structure.

Defense candidate forte para Capítulo de Método do TCC: três PRs
distintas em uma sessão, todas mecânicas no que se propunham, todas verde
no gate, materializaram o anti-pattern "PR mista" como evitável por
disciplina estrutural explícita.

### Próximo passo

Sessão #21 (Chat) — prep de canonical-sync-B do policy-reader (decisão
de design). Estrutura proposta: ~1h Chat de prep + ~30min Code de
aplicação + ~30min Chat review. Após merge: T02b. Ver
`docs/process/session-handoff.md` para pre-flight pins detalhados.

---

## 2026-05-17 — sessão #21 — canonical-sync-B (Option B documentado + polimorfismo + drift estrutural)

**Foco.** Sessão Chat de prep + execução Code + cinco rounds de review
independente fechando canonical-sync-B do policy-reader spec. Bundle
único (PR #38, dois commits squash-merged em main) cobrindo três eixos
de drift cross-doc: isError-semantics adaptada para Option B em
canonical/compact + amendment ADR-0002 §3 com line-number provenance;
polimorfismo `applicability_scope` → `applies_to` materializado em
canonical/compact com discriminação por `clause_type`; vocabulário de
`operation` migrado para tokens canônicos (`storage`,
`disclosure_by_transmission`) per SCHEMA.md §9.2. PR #38 hash de squash:
`<TBD>`.

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1.6 Task decomposition — bundle vs split em PR mecânica.** Decisão
  consciente de bundle Cluster A (polimorfismo `applies_to`) + Cluster B
  (isError-semantics) na mesma PR canonical-sync-B em vez de split em
  duas PRs sequenciais. Trigger: catch do Code na rodada 1 de review
  indicando que publicar Draft 2 com `applicability_scope` (Cluster A
  pendente) e depois reeditá-lo em Cluster A produziria double-edit
  visível no diff, gerando ruído no Code review futuro ("schema
  desatualizado") que disputaria atenção com o feedback substantivo
  sobre Option B. Bundle elimina double-edit; custo é PR maior (13+
  edits vs 8). Trade-off ratificado por scope discipline + review
  efficiency.
- **D1.7 Session state management — close limpo via three-property
  test.** Sessão #21 fechou cobrindo (a) artefato físico endereçável
  (PR #38 mergeada com squash hash registrado neste log); (b) próximo
  handoff decidido e enumerado (sessão #22 Chat prep T02b com três DDs
  já mapeadas); (c) defense candidates registrados antes da sessão
  terminar (esta entry). Pattern "close limpo > resume com contexto
  sujo" do exam guide materializado em escala documentada.

**Domínio 2 — Tool Design & MCP Integration (18%)**

- **D2 isError flag — adaptação documentada framework-vs-spec.**
  ADR-0002 §3 amendment in-place documenta Option B como adaptação
  consciente do contrato MCP à realidade FastMCP 3.2.4. Citation chain
  rastreável: linha 124 (`to_mcp_result`) e 270 (`convert_result`) de
  `fastmcp/tools/base.py`, linha 467 (`_make_error_result`) e 576
  (success path com `isError=False`) de `mcp.server.lowlevel.server`,
  todas sob `fastmcp==3.2.4` pinado em `uv.lock`. Issues externas
  ancoradas em fonte primária verificada via web fetch: #4042 do
  IBM/mcp-context-forge (gateway-level validation prioritizing one
  channel) e #654 do modelcontextprotocol/typescript-sdk (`isError`
  ignored when `structuredContent` validation runs first). Defense
  candidate forte para o Capítulo de Método — adaptation defensável
  contra audit jurídico/banca porque rationale carrega revisit trigger
  ("reopen when FastMCP exposes public API path producing wire
  `isError: true` with structured envelope simultaneously, OR project
  migrates off FastMCP, OR MCP spec adopts implicit-discriminator
  pattern as preferred practice").
- **D2 structured output — discriminador implícito por presença de
  campo.** Sob Option B, o discriminador formal entre sucesso e erro
  passa a ser **presença do campo `errorCode` em `structuredContent`**,
  não wire `isError`. Sucesso carrega payload positivo (cláusula,
  lista, veredito) sem `errorCode`; erro carrega envelope com
  `errorCode` populado. Materializado em canonical §5.1, §5.3 (este
  reformulado para colocar discriminador no centro em vez de manter a
  premissa stale "isError: false = não erro"), compact §2, ADR-0002 §3
  amendment.
- **D2 polimorfismo via Pydantic discriminated union projetado na
  superfície da tool.** `clause_type: substantive | definitional` é
  discriminator literal em RFC 2119-style ("consumers MUST branch on
  `clause_type` before reading type-specific fields"). Substantive
  carrega `applies_to`/`control`/`requirements`/`exceptions`;
  definitional carrega `defines`/`out_of_scope`. Anti-uniformização
  declarada normativa em canonical §4.2 tool description ("consumers
  MUST NOT filter or coerce by `clause_type` to uniformize") porque
  `find_clauses_by_law_article` produz primeira lista heterogênea em
  superfície de retorno do componente (busca casando Art. 5 retorna
  POL-000 + substantivas). Defense candidate para a prova como exemplo
  prático de "JSON schema com discriminator field" sobrevivendo
  cross-task sem refactor.
- **D2 object-wrap em `structuredContent`.** MCP spec define
  `structuredContent` como `object`, não array. Compact §5.2 carregava
  débito de array raiz (`structuredContent: [...]`); canonical-sync-B
  migra para `structuredContent: {clauses: [...]}` consistente em
  ambos. Conceito relevante para a prova: tool design conforme MCP
  wire format.

**Domínio 4 — Prompt Engineering & Structured Output (20%)**

- **D4.6 Multi-instance review pattern em escala empírica documentada.**
  Cinco rounds independentes de Chat ↔ Code review sobre o mesmo
  conjunto de artefatos, cada round capturando classe distinta de
  issue load-bearing:
  - **Round 1 (pre-apply).** Code review do compilado inicial pegou
    três classes: companion edits faltantes (§5.3 reformulação,
    tool descriptions object-wrap, §8.5 acceptance criterion); Cluster
    A cross-contaminando Draft 2 (recommendation: bundle); claims
    externas não-verificadas (`fastmcp/tools/base.py` funções, issue
    #4202).
  - **Round 2 (pre-apply).** Code review do compilado revisado pegou
    quatro patches empíricos: `defines` shape inventado (real é
    objeto com `vocabulary_kind`+`entries[]`); `out_of_scope` shape
    inventado (real é lista de dicts com `topic`/`statutory_reference`/
    `reason`/`fallback`); `operation: store` (real é `storage`);
    `control: purpose_declared` (não existe no vocabulário —
    `consent_required` ou `anonymization_required` são os dois
    canônicos no MVP).
  - **Round 3 (pre-apply).** Code review final pegou drift adicional
    de `transmit` (real é `disclosure_by_transmission`) em dois sites
    e imprecisão de atribuição de `_make_error_result` ao path de
    `ToolError` (real: chamado em três sites protocolares
    independentes do path de exceções de tool).
  - **Round 4 (durante apply).** Code durante execução do compilado
    flagou três sites onde o compilado declarava no amendment
    ADR-0002 §3.1 que `applicability_scope` → `applies_to` e
    `transmit` → `disclosure_by_transmission` seriam fechados, mas
    a edit list mecânica não enumerava dois desses sites:
    canonical.md:137 tool description (não estava em escopo do Edit
    1.2), canonical.md:622 e compact.md:412 (drift `store` →
    `storage` em exemplos `violation_candidate` de §4.3 não
    enumerados em Patch C original).
  - **Round 5 (pós-commit).** Chat review independente do diff
    `5926a03` capturou duas should-fix de exaustividade entre prose
    declarativa e enumeração mecânica: canonical.md:137 omitia
    `control` na lista de campos polimórficos (Finding 2.1);
    compact.md:24 carregava frase stale `isError: false` como
    discriminador (Finding 8); mais dois cosméticos ratificados como
    deferred para PR de housekeeping (Findings 7.1/7.2 wordsmithing
    issues externas; Finding 9 POL-005 placeholder semântico).
  - **Round 6 (delta pós-follow-up).** Validação 4/4 PASS do commit
    `1bbc6fe` cobrindo Findings 2.1, 8, 11, 7.3. PR liberada para
    squash merge.
  
  Cinco classes distintas de issue capturadas em seis rounds, todos
  pré-merge. Métrica derivada para o Capítulo de Método:
  catches/round × superfície-revisada cresce monotônica até saturar
  (round 6 retornou 0 findings novos). Generator + evaluator
  separados validado em escala empírica documentada — Rajasekaran
  2026 pattern aplicado em human-in-the-loop acadêmico, single
  generator (Chat de prep) + multi-round evaluator (Code review
  pre-apply + Code apply + Chat review independente pos-commit +
  Chat review delta).

**Domínio 5 — Context Management & Reliability (15%)**

- **D5 provenance via verificação direta com line numbers.** ADR-0002
  amendment ancorado em fonte primária verificada com line numbers
  precisos: `fastmcp/tools/base.py:124,270` (`to_mcp_result`,
  `convert_result`); `mcp/server/lowlevel/server.py:467,576`
  (`_make_error_result`, success path); `policy/clauses/POL-000.yaml`
  e `policy/SCHEMA.md` §5.2-5.4, §9.2 para shapes empíricos;
  issues externas (#4042, #654) verificadas via web fetch. Nenhuma
  claim por inferência de contexto histórico. Citation chain rastreável
  até source verificável. É o pattern D5 cobra como "scratchpad files"
  + "context extraction" aplicado em escala de ADR.
- **D5 sanity greps como verificação de exaustividade.** Padrão
  operacional emergente desta sessão: greps de exaustividade fazem
  parte do compilado de uma PR mecânica, não da varredura pós-fato.
  Em canonical-sync-B, os sanity greps pós-apply (`"operation":
  "(store|transmit)"` retornando zero matches; `applicability_scope`
  retornando zero matches; `isError.*false.*not.*errors` retornando
  zero matches pós-follow-up) confirmaram exaustividade do bundle.
  Forma operacional concreta do que D5 chama "context extraction" +
  "scratchpad". Generalizável para futuras PRs cross-doc.
- **D5 robustez de citation chain a estado upstream evoluir.** Finding
  7.3 do Chat review pós-commit capturou que as duas issues citadas
  no amendment (`IBM/mcp-context-forge #4042`,
  `modelcontextprotocol/typescript-sdk #654`) estão ambas em estado
  CLOSED nos respectivos issue trackers. Patch 4 do follow-up commit
  acrescentou frase reconhecendo isso e separando fix-status
  (downstream patch concreto) de pattern-recurrence (tensão estrutural
  schema-vs-content). Defense candidate D5: ADRs duram, issues mudam
  de estado; tese do amendment deve sobreviver a "patches downstream
  specific bugs were fixed". Pattern materializado em prosa explícita
  do amendment.

### Decisões fechadas

**P3 forma do amendment ADR-0002 §3 — contrato no canonical, rationale
no ADR.** Trade-off considerado: (P1) canonical "limpo" sem mencionar
constraint perde rastreabilidade; (P2) canonical honest com constraint
inline mistura contrato vs rationale; (P3) canonical declara convenção
objetivamente, ADR amendment carrega rationale + revisit trigger +
referências externas. Ratificado P3 por (a) consistência arquitetural
com cut estabelecido (canonical = contrato; ADR = rationale histórico);
(b) padrão de amendment in-place herdado de ADR-0008 amended
2026-05-16 — Pin #6 do handoff de prep já se inclinava para amendment
in-place vs ADR novo (ADR-0002 fresco demais para succession; consumidor
primário é Claude, não auditor humano com expectativa de imutabilidade
acionada); (c) defense acadêmica para Capítulo de Método (canonical
estável como documento de contrato; ADR como audit trail de adaptações
framework-vs-spec).

**Bundle Cluster A + B em PR única vs split em duas PRs sequenciais.**
Ratificado bundle único (PR #38). Razão substantiva: catch do Code na
rodada 1 indicou que publicar exemplos com `applicability_scope`
desatualizado seguidos de reedit em Cluster A produziria double-edit
visível, gerando ruído review. Custo: PR maior (16 edits totais);
ganho: review única, código pós-sync-B consome spec coerente em todos
os eixos. Padrão register-able para futuras PRs mecânicas: bundle
quando split produziria double-edit no mesmo arquivo.

**Compact não carrega exemplos de erro (decisão deliberada).**
Frase adicionada em compact §5.1 e §5.2: "Examples of error envelopes
live in canonical §4.x and §5; not duplicated here." Compact é
destilação operacional; tabela §3 + canonical §4.x cobrem forma do
envelope. Princípio aplicado: compact é forma navegacional; canonical
é instância autoritativa.

**Linguagem RFC 2119 (MUST NOT) em canonical §4.2 anti-uniformização.**
Manter tom normativo deliberadamente. "Consumers MUST NOT filter or
coerce by `clause_type` to uniformize the list" é invariante de
protocolo, não sugestão estilística. Pattern reaplicável para futuras
invariantes load-bearing em tool descriptions.

### Artefatos produzidos

**PR #38 (`feat/canonical-sync-B`), mergeada em main via squash com
hash `<TBD>`.** Dois commits pré-squash (registrados aqui como audit
trail interno, sobrevivem ao squash apenas via este log):

- `5926a03` — `feat(canonical-sync-B): align canonical+compact+ADR-0002
  to Option B and empirical clause shape`. 3 arquivos, +445 / -87.
  13 edits originais + 3 patches de exaustividade (Edits 1.8, 1.9, 2.6
  identificados pelo Code durante apply).
- `1bbc6fe` — `fix(canonical-sync-B): close exhaustiveness drift caught
  by independent review`. 4 patches do Chat review pós-commit
  (Findings 2.1, 8, 11, 7.3).

Total mergeado: ~20 edits em três arquivos:

- `docs/specs/policy-reader/canonical.md` — 9 edits cobrindo §4.1
  (Output prose polimórfico + 4 exemplos + tool description com
  `control`), §4.2 (description object-wrap + anti-uniformização +
  Output prose + 4 exemplos polimórficos), §4.3 (paralelismo cross-ref
  §4.1↔§4.3 + flip `isError` deprecated + `transmit` →
  `disclosure_by_transmission` em indeterminate + `store` → `storage`
  em violation_candidate), §5.1 (reescrita Option B), §5.3
  (reformulação em torno do discriminador formal `errorCode` presence).
- `docs/specs/policy-reader/compact.md` — 6 edits cobrindo §2 (Wire
  format com parágrafo Option B), §3 (reformulação stale
  `isError: false` para discriminador `errorCode`), §5.1 (description
  polimórfica + Output structure com shapes empíricos + 2 exemplos),
  §5.2 (description object-wrap + 2 exemplos polimórficos), §5.3
  (flip `isError` deprecated + `transmit` → `disclosure_by_transmission`
  em indeterminate + `store` → `storage` em violation_candidate).
- `docs/adr/0002-mcp-conventions-and-deferments.md` — 1 edit cobrindo
  amendment in-place ao Decision 3 com nove parágrafos (constraint
  FastMCP + linha de provenance + ecosystem references + adoption
  statement + rationale + revisit trigger + CLOSED status acknowledgment
  + companion edits enumerados).
- `src/mcp_servers/policy_reader/models.py` — docstring `ErrorEnvelope`
  alinhada com canonical §5.1 pós-amendment (Patch 3 do follow-up).

### Validações empíricas

- **Gate task-level ADR-0008 §3 cumprido em escala documentada.**
  pytest 20/20 verde em ambos os commits (pré e pós follow-up);
  ruff `All checks passed!`; mypy `--strict src/` `no issues found in
  7 source files`. Tests em `tests/` carregam pré-existências
  (não tocados nesta PR; pytest configurado sem `--strict` em tests é
  estado prévio do repo).
- **Sanity greps de exaustividade retornaram zero matches.** Três
  comandos rodados pós-apply: (a) `grep -nE '"operation":\s*"(store|transmit)"'
  docs/specs/policy-reader/` retornou zero; (b) `grep -n
  'applicability_scope' docs/specs/policy-reader/` retornou zero;
  (c) pós-follow-up `grep -nE 'isError.*false.*not.*errors|not.*errors.*isError'
  docs/specs/policy-reader/` retornou zero. Confirmação operacional
  de varredura completa.
- **Pattern "consertar na fonte" reaplicado em escala maior.**
  canonical-sync-A fechou drift textual (regex-replaceable). 
  canonical-sync-B fechou drift estrutural (shape de exemplos, prosa
  polimórfica, amendment ADR). Mesma disciplina source-of-fix
  aplicada a dois tipos diferentes de drift. Material defense
  candidate strong: contraste empírico com hipotética PR-mista que
  bundleasse correções estruturais + nova feature.
- **Multi-round Chat ↔ Code review materializou D4.6 em escala
  empírica.** Cinco classes distintas de issue capturadas em seis
  rounds independentes, todos pré-merge. Métrica derivável:
  catches/round × superfície decrescente (round 6 retornou 0 findings
  novos = saturação atingida). Quantificável para argumentação no
  Capítulo de Método.
- **Citation chain do ADR-0002 amendment verificado via fontes
  primárias.** Quatro line numbers (`fastmcp/tools/base.py:124,270`,
  `mcp/server/lowlevel/server.py:467,576`) confirmados pelo Chat
  reviewer pós-commit contra `.venv` pinado `fastmcp==3.2.4`. Duas
  issues externas (#4042, #654) verificadas via web fetch durante a
  redação do compilado e ratificadas na rodada delta. Provenance
  rastreável até fonte verificável; nenhuma claim por inferência.

### Pendências para sessão #22+ ou PR futura

**Resolver na #22 (Chat — prep do prompt T02b):**

- **DD-T02b-1: helpers compartilhados de envelope.** T02b é o segundo
  consumidor de `_envelope_tool_result` + builders per-errorCode.
  DD-6 de T02a registrou "extrair para módulo compartilhado quando
  segundo consumidor aterrissar". T02b decide na Fase 1: extrair para
  `tools/_envelope.py` agora ou manter inline em `tools.py` até T03
  (cinco errorCodes adicionais) gerar pressão real. Inclinação
  prévia: manter inline; YAGNI aos quatro errorCodes atuais.
- **DD-T02b-2: modelagem do `specification` de input.** Três caminhos:
  (a) parâmetros nomeados na assinatura (`def
  find_clauses_by_law_article(lei, artigo, paragrafo=None, inciso=None,
  alinea=None)`); (b) Pydantic model dedicado em `models.py`; (c) dict
  com validação inline. Inclinação prévia: (a), por simplicidade e
  por bater com stub já em `server.py:125-152`.
- **DD-T02b-3: lista heterogênea polimórfica como invariante de
  implementação.** §4.2 da spec carrega
  `consumers MUST NOT filter or coerce by clause_type to uniformize`
  como invariante de protocolo. Brief T02b precisa adicionar como
  invariante de implementação: algoritmo de matching
  prefix-hierarchical não filtra por `clause_type`, nenhum refactor
  futuro pode "limpar" a lista. Candidato a AS de teste explícito
  (e.g., AS-6 cobrindo busca por Art. 5 retornando POL-000 definitional
  + alguma substantive simultaneamente).
- **AS-2 fixtures sintéticas.** Pack POL-001..004 não cobre
  prefix-hierarchical (todas as cláusulas têm inciso/parágrafo).
  T02b precisa de fixtures sintéticas inline em
  `test_find_clauses.py` via `_write_yaml` no `tmp_path` — duas
  cláusulas com `{lei, artigo}`-only refs vs `{lei, artigo, inciso}`
  refs para exercitar a semântica de match.
- **Pré-leitura obrigatória:** docs/specs/policy-reader/canonical.md
  §4.2 + §5 pós-canonical-sync-B (spec limpa); preview de prompt T02b
  que Code preview-ou no documento anexado em #21 (já carrega 60% do
  framing).

**Resolver em sessão #23+ (Code — execução T02b):**

- `find_clauses_by_law_article` implementação completa. Pré-leitura
  consome canonical já limpo pós-canonical-sync-B (Pin satisfeito).

**Resolver em janela futura sem urgência:**

- **DX residual:** linters (ruff, mypy) como dev deps oficiais em
  `pyproject.toml`. Workaround `uvx ruff` e `uv run --with mypy mypy`
  funciona. Sessão Code curta (~15min).
- **Itens deferidos T03** (já listados em `tasks.md` §Companion edits):
  `operation`/`legal_basis` vs `operation_type`/`declared_legal_basis`;
  `evidence` vs `reason` em `not_applicable`. Resolver pós-T03 quando
  spec for empiricamente validado.
- **Decisão Semgrep-on-Windows** (Docker, pip native, remote worker,
  CI-only) — afeta forma de Milestone B; antecede decomposição formal.
- **Cosméticos diferidos do round 5 review:** Findings 6.1 (ADR
  caracterização `_make_error_result` com 4 call sites em vez de 3);
  7.1, 7.2 (wordsmithing das issues externas no amendment); 9
  (POL-005 placeholder semanticamente contrived em Art. 5). Todos
  cosméticos, sem urgência, viajam com próxima PR que tocar respectivo
  arquivo.

**Resolver em prep de Milestone B (canonical-sync-C):**

- **Drift análogo no template `docs/specs/_template.md`** — linha 107
  ainda carrega `### 5.3 Casos que parecem erro mas não são` (título
  antigo de policy-reader §5.3, renomeado nesta PR para "Discriminador
  formal entre sucesso e erro"). Template precisa de sync quando
  algum motivo o tocar.
- **Drift análogo no semgrep-runner spec** — `docs/specs/semgrep-runner/canonical.md`
  linha 283 ainda usa título antigo análogo; spec inteira do
  semgrep-runner não foi migrada para Option B. Trigger natural:
  prep de Milestone B (semgrep-runner implementation) deliberará
  canonical-sync-C que propaga amendment §3 para essa spec também.

**Resolver pós-Milestone B:**

- **Decomposição formal de Milestone C** (pipeline multi-agente) e
  **Milestone D** (CI/CD + validação empírica) em sessões Chat
  dedicadas, sequencialmente.

### Nota de calibração metodológica

Sessão #21 operou seis rounds Chat ↔ Code review independente sobre
artefato único (PR #38 canonical-sync-B), capturando cinco classes
distintas de issue load-bearing pré-merge. Round 1-3 pre-apply, round
4 durante apply, round 5 Chat review pós-commit, round 6 validação
delta pós-follow-up. Padrão emergente: granularidade do escopo de
review escala inversamente à proximidade do merge. Rounds iniciais
amplos (catch macro de classes inteiras); rounds finais delta-focados
(validar fechamento das classes anteriores). Round 6 retornou 0
findings novos = saturação atingida = PR pronta para merge.

Defense candidate forte para o Capítulo 4 do TCC (Capítulo de Método):
métrica quantificável é catches load-bearing por hora de operação
humana investida, ou catches/round × superfície-revisada. Sem o
pattern multi-round, single-instance self-review do gerador (Chat)
perderia consistentemente os mesmos catches que o reviewer
independente (Code) acertou. Argumentação reproduzível: gravar
ordinal-por-ordinal das classes capturadas em cada round, calcular
densidade de catches/superfície revisada, plotar curva de saturação.
Para canonical-sync-B, a curva satura no round 6; trabalho subsequente
seria mover catches cosméticos de defer-pending para zero, custo
diminuendo monotônica.

Adicional: bundle Cluster A + B em PR única (vs split) ratificou
disciplina "consertar na fonte" em escala maior. PR-A (canonical-sync-A)
fechou drift textual; PR-A.2 (canonical-sync-A.2) fechou drift textual
adicional descoberto durante A; PR-B (canonical-sync-B) fechou drift
estrutural + amendment ADR. Padrão "PR mecânica descobre débito
análogo durante execução" reaplicado em escala maior: round 4 Code
durante apply descobriu drift adicional não enumerado no edit list
original (Edits 1.8, 1.9, 2.6); round 5 Chat reviewer pós-commit
descobriu drift adicional não capturado por nenhuma rodada anterior
(Findings 2.1, 8). Lição: PR mecânica em escala maior precisa de
sanity greps no compilado (preventivo), não só pós-apply (curativo).

### Próximo passo

Sessão #22 (Chat) — prep do prompt T02b, três DDs a deliberar
(helpers compartilhados, modelagem de specification, invariante
anti-uniformização). Produz prompt mecânico para sessão Code #23+
executar T02b. Pré-leitura obrigatória: canonical §4.2 + §5 limpos
pós-sync-B; preview de prompt T02b já redigido em #21 (60% do
framing). Custo estimado: ~1h Chat de prep. Após #22 fechar, sessão
Code #23+ implementa T02b (~2-3h, gate task-level ADR-0008 §3).

## 2026-05-17 — sessão #22 — prep prompt T02b + cleanup render romano (#22.5) + 
T02b find_clauses_by_law_article (#23 Code) + Chat review independente

**Foco.** Sessão Chat persistente cobrindo o ciclo T02b completo: refinamento 
iterativo do prompt de Code (v1 → v2 → v3 → execução) com três rodadas Chat ↔ 
Code, sessão Code #22.5 dedicada à PR de cleanup mecânico 
`fix/render-romano-in-T02a` pré-T02b, sessão Code #23 implementando T02b Fase 1 
(plano) + Fase 2 (código), e Chat review independente dos quatro arquivos 
modificados antes da PR. Bundle conceitual único cobrindo a primeira aplicação 
em escala documentada do pattern "uma sessão Chat persistente sustenta múltiplos 
ciclos Code rotativos". PRs: `fix/render-romano-in-T02a` em `<TBD>` (sessão 
#22.5), `feat/policy-reader-find-clauses` em `<TBD>` (sessão #23, após merge da 
cleanup).

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1 multi-agent coordinator-subagent com human-in-the-loop — três rodadas 
  Chat ↔ Code aplicadas a prompt prep, não a execução.** Primeira sessão a 
  exercitar o pattern coordinator-subagent sobre redação iterativa de prompt: 
  Code redigiu draft inicial v1 do prompt T02b (durante a sessão T02a anterior), 
  Chat refinou para v2 com seis correções factuais/estruturais, Code reviewou v2 
  e pegou a lacuna do drift romano vs literal de inciso que escapou ao Chat, 
  Chat refinou para v3 absorbendo a DD-5 com quatro opções, João ratificou v3 
  com sub-sub-decisão (d.1) sobre assinatura semântica do helper compartilhado, 
  Chat refinou para final. Padrão: cada rodada captura uma classe distinta de 
  catch (factual macro → transversal cross-component → semântico de tipos). 
  Material defense candidate forte para Capítulo de Método.

- **D1 scope discipline cross-PR — descritivo de propriedade desejada, não 
  ritual.** Quando João abriu inadvertidamente a sessão Code de cleanup na 
  mesma sessão da prep anterior (falso alarme — sessão era nova mas com nome 
  parecido), o reflexo inicial foi "refazer em sessão fresh para preservar 
  pattern". Chat refinou: scope discipline é descritiva de **auditabilidade de 
  blame por PR**, não ritual de "sessão fresh para cada PR". Se o diff está 
  limpo (verificável independentemente via Chat review do diff), a propriedade 
  está atendida independente da sessão Code que produziu. Cinco checks 
  estruturais propostos para validar o diff direto antes de ratificar; todos 
  passaram. Quarta aplicação do pattern PR sequencial em escala (#19, #20, #21, 
  #22.5 → #23) consolida defense candidate.

- **D1 session state management — heurística refinada sobre sessões persistentes 
  vs fresh.** Originalmente projetei o ciclo como "sessão Chat #22 prep → 
  sessão Chat #23 review T02b" com handoff entre as duas. João corrigiu: Chat 
  persiste sobre múltiplos ciclos Code, sessão fresh só após PR de T02b 
  mergear. Refinamento: contexto que vale preservar vs descartar não é função 
  do papel (Chat vs Code), é função do **tipo de output**. Code produz código 
  (output verificável independentemente, então sessão fresh evita 
  cross-contamination silenciosa que gates podem não pegar). Chat produz 
  decisões e ratificações (output que ganha qualidade com histórico narrativo 
  cumulativo). Heurística destilada: sessões fresh para outputs verificáveis 
  empiricamente; sessões persistentes para outputs narrativos. Pattern a 
  formalizar em CLAUDE.md ou ADR futuro.

- **D1 task decomposition — DD reversion fundamentada vs inércia.** Plano que 
  Code esboçou em sessão Code anterior (#22.5 que ficou esboçada antes do 
  cleanup) recomendava criar fixture nova `policy_root_with_pack_clauses_full` 
  ao lado da existente, argumentando "risk de regression silenciosa em T02a 
  tests". Em sessão Code #23 (Fase 1 plano), Code reverteu para "estender 
  fixture existente incluindo POL-004", com dois argumentos novos: (i) 
  coerência intra-fixture (POL-003 declara `successors: [POL-004]`; POL-004 
  ausente da fixture é inconsistência conceitual); (ii) verificação direta de 
  T02a tests confirmou asserções por `clause_id` específico, não por count — 
  POL-004 não rompe nenhuma. Coerência justifica mudança; verificação direta 
  neutraliza o risco original. Defense candidate: **reversão fundamentada de 
  recomendação prévia ≠ inércia**, quando os argumentos da reversão são 
  empíricos.

**Domínio 2 — Tool Design & MCP Integration (18%)**

- **D2 tool description com anti-uniformization rule literal no docstring.** 
  Server.py wrapper de `find_clauses_by_law_article` carrega no docstring final 
  "The list MAY mix `clause_type: definitional` and `clause_type: substantive` 
  when the same article is referenced by both kinds; consumers MUST NOT filter 
  or coerce by `clause_type` to uniformize the list." Literal do canonical 
  §4.2 line 362. Exemplo de como a invariante de contrato declarada na spec 
  vira parte do docstring que é consumido pelo cliente MCP via 
  `inputSchema`/`description`.

- **D2 discriminador polimórfico `clause_type` no output schema.** A 
  invariante anti-uniformização é exercitada por código no anchor de teste 
  `test_polymorphic_mix_at_art_5` sobre fixture sintética que carrega 
  POL-000 (definitional, real) + POL-901 + POL-902 (substantive, sintéticas). 
  Query `{lei: LGPD, artigo: 5}` retorna lista heterogênea de 3 elementos 
  com `types == {"definitional", "substantive"}`. **Sem o anchor, a 
  invariante ficaria só na spec** — implementação que filtrasse 
  definitional-only ou substantive-only passaria todos os outros 5 AS por 
  coincidência. Padrão D2 cobrado pela prova como "schema design — output 
  discriminator preservation".

- **D2 isError flag Option B canonicalizada — segunda aplicação operacional.** 
  T02b consumiu sem DD: envelope em `structured_content` com `errorCode`, 
  `content[0].text == message`, wire `isError: false`. Convenção Option B 
  já documentada em canonical §5.1 + §5.3 + ADR-0002 §3 amendment 
  (canonical-sync-B / #21). Segundo consumidor (`INVALID_LAW_IDENTIFIER`) 
  aplicou direto. Convenção operacional ratificada por uso, não por mais um 
  round de DD.

- **D2 errorCode `INVALID_LAW_IDENTIFIER` com `details` dinâmico do header.** 
  `accepted_values` do envelope vem de `state.header.accepted_law_identifiers` 
  (não hardcoded), com `sorted()` defensivo para determinismo. Pin do brief 
  capturou esse requisito; teste AS-5 valida `details == {"provided": "GDPR", 
  "accepted_values": ["LGPD"]}` literal. Quando T04 introduzir framework swap, 
  `accepted_values` automaticamente reflete o header carregado.

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- **D3 plan mode com gate de OK explícito — quarta aplicação em escala.** 
  Sessão Code #23 Fase 1 entregou plano com 8 DDs enumeradas (DD-1 a DD-8), 
  recomendação por DD justificada, mapping AS tabular, riscos enumerados, 
  alvos de edição escopados. Estrutura permite ratificação granular: João 
  ratificou DDs 1-3 e 5-8, mudou DD-4 (reversion já discutida acima), anotou 
  observação cosmética sobre AS-4 (canonical line 472 sem º), e aprovou. 
  Padrão "gate de OK pode ser cirúrgico, não binário" materializado em 
  escala.

- **D3 CLAUDE.md / convenções como prescritivos vivos.** Quatro convenções 
  novas formalizadas em texto durante esta sessão: (a) "sessões fresh para 
  outputs verificáveis, persistentes para narrativos" (D1 acima); (b) 
  "assertion strictness escala inversamente com expansibilidade do fixture" 
  (testes que **definem** contrato usam asserções estritas com ordem exata; 
  testes que **exercitam** contrato usam subset — formalizado para T03+); 
  (c) range `POL-9NN` reservado para fixtures sintéticas de teste, separado 
  de `POL-001..POL-099` (cláusulas reais) e do pack `POL-001..POL-004`; 
  (d) "compartilhar função de formatação entre dois domínios é OK; 
  compartilhar tipo requer justificativa semântica" (DD-5 sub-sub d.1 sobre 
  helper signature). Pendência: codificar (a), (b) e (d) em ADR ou regras 
  `.claude/rules/` em janela futura.

**Domínio 4 — Prompt Engineering & Structured Output (20%)**

- **D4.6 multi-instance review com escalation progressiva — três rounds 
  capturando classes distintas.** Round 1 (Code → Chat): Chat pegou seis 
  correções factuais/estruturais em v1 do prompt (AS-1 query drift, anchor 
  polimórfico que não testava mix, render rules underspecified, deprecated 
  framing, fixture composição incompleta, verificação obrigatória de estado 
  real). Round 2 (Chat → Code): Code validou as seis com referências de 
  linha específicas e achou lacuna nova que Chat não tinha visto sozinho — 
  drift romano vs literal de inciso entre `tools.py` T02a e canonical-sync-B 
  pós-#21. Round 3 (Code → Chat → João): Chat propôs opção (d) PR sequencial 
  pequena que Code não tinha considerado (recomendava bundle (c) por 
  argumento de tamanho); João ratificou (d) com sub-sub-decisão (d.1) 
  sobre assinatura do helper compartilhado pinando impedância semântica 
  stored vs query. **Três classes distintas de catches por round.** 
  Saturação atingida em 3 rounds (curva de saturação para PR de tamanho 
  médio).

- **D4 validation-retry implícito via AS-2 narrow — granularidade calibrada 
  por dimensão de falha.** Bug do `_matches` (curto-circuito 
  `if spec is None: return True` ignorava specs mais profundas) só foi 
  pego pelo AS-2 narrow no primeiro run da Fase 2. Sem split AS-2 em 
  narrow/broad — se ficasse apenas AS-2 broad como o brief original 
  pinava menos explicitamente — todos os outros 5 testes passariam por 
  coincidência. AS-1 (query `{artigo: 7}` sem opcionais), AS-3 (mesma 
  query), AS-4 (lista vazia, não exercita matching), AS-5 (erro antes do 
  matching), anchor polimórfico (broad query). **AS-2 narrow é o teste 
  único** que força a comparação de campo opcional não-trivial entre 
  spec e stored. Defense candidate forte: granularidade de teste calibrada 
  por **dimensão de falha esperada**, não por count de cenários — exatamente 
  o que D4 cobra em validation-retry loops aplicado em forma estática.

- **D4 prompt engineering com structured phases iterado a quatro 
  versões.** v1 (esqueleto baseado em T02a, 270 linhas) → v2 (DD-5 
  adicionada, 540 linhas) → v3 (sub-sub d.1 pinada, 583 linhas) → 
  execução (DD-5 colapsada pós-cleanup, ~380 linhas). Cada versão 
  preservou estrutura Fase 1 plan / gate / Fase 2 execute / Post-Fase 2 / 
  Guard-rails; deltas foram cirúrgicos via `str_replace` em vez de 
  regeneração. Pattern de versionamento via deltas reduz risco de 
  introdução acidental de mudanças não-relacionadas — material defense 
  para "estrutura > capacidade do modelo".

**Domínio 5 — Context Management & Reliability (15%)**

- **D5 canary check via pin de pré-condição.** Brief de execução T02b 
  pinou: "Se `_format_law_reference` **não** estiver em `tools.py` após 
  `git pull origin main`, abort e levanta com João antes de prosseguir." 
  Asserção barata no início da Fase 1 que pega erro caro (Code 
  reimplementar helper em paralelo porque acha que não existe) antes 
  de o erro se propagar. Build the canary that screams first — princípio 
  aplicado em T01 para wire-shape FastMCP, replicado aqui para estado 
  de `main`. Padrão reusável: sessões T03+ que dependerem de helpers 
  consolidados em sessões anteriores carregam canary pin equivalente.

- **D5 provenance via leitura direta vs inferência — pin obrigatório 
  na Fase 1.** Brief v1 originalmente carregava afirmações herdadas do 
  Code da T02a sobre estado de `conftest.py`, `server.py:125-152`, 
  `tools.py`. Pin #6 das seis correções iniciais forçou: "verificar 
  essas afirmações lendo os arquivos direto; se divergente do brief, 
  parar e levantar antes de planejar". Code da Fase 1 cumpriu o pin com 
  10 verificações tabuladas direto contra os arquivos. Achado menor: 
  range de linhas `server.py:125-152` afirmado pelo brief é na verdade 
  `141-168` no estado real (drift menor não-bloqueante). Confirmação 
  empírica de que herdar afirmações entre sessões sem verificação 
  produz drift; pin "lê direto, não infere" funciona em escala.

- **D5 escalation pattern — bug do `_matches` pego, validado, e 
  corrigido sem rerun.** Code da Fase 2 reportou: "Bug pego pelo AS-2 
  narrow no primeiro run. Versão original fazia curto-circuito... 
  Corrigi para semântica equivalente sem curto-circuito; a falha de 
  teste validou o algoritmo por código — sem o AS-2, o bug teria 
  escapado." Padrão clássico de generator/evaluator (Rajasekaran 2026): 
  o test escreveu primeiro o que o código deveria fazer, o código 
  falhou no que o teste exigia, o código corrigiu. **Sem escalation 
  para Chat** — Code resolveu localmente porque o teste especificou o 
  comportamento esperado com precisão suficiente. Contraste empírico 
  com T02a (#20) onde AS não-executável precisou escalation: lá o 
  contrato do framework FastMCP era a fonte do problema; aqui o 
  contrato canonical §4.2 era a fonte da solução.

- **D5 débito cosmético cross-doc anotado em três lugares.** Inconsistência 
  em canonical §4.2 line 472 (`"Nenhuma cláusula referencia LGPD Art. 50."` 
  sem ordinal `º`) vs linhas 431/459 (com ordinal). Implementação de T02b 
  escolheu consistência interna (`_format_law_reference` sempre emite 
  `º`) e asserção do AS-4 acompanha (`"Art. 50º."` com `º`). Débito 
  registrado em: (i) relatório do Code Fase 2; (ii) Chat review 
  independente; (iii) este learning-log. Anotação tripla previne perda 
  de rastro entre sessões. Pendência para sessão Chat de housekeeping 
  cross-doc futura.

### Conceitos fora do escopo da prova

- **PR sequencial vs PR encadeada — git workflow.** Discussão em #22.5 
  sobre (A) Code abre PR de cleanup → João mergeia em main → Code 
  ramifica T02b de main vs (B) Code ramifica T02b de branch de cleanup 
  sem mergear primeiro. (B) exige rebase pós-squash, frágil; (A) limpo 
  com gate Chat-review independente sobre cada PR. (A) escolhida, 
  consistente com pattern #19 (cleanup → main → T01) e #21 
  (canonical-sync-B → main → T02b).

- **`git stash -u` para preservar untracked pré-checkout** — pin 
  operacional herdado de #19, aplicado em #22.5 para preservar working 
  state durante checkout entre branches.

### Decisões tomadas

- **DD-1 (helper extraction):** (a) manter inline em `tools.py` por 
  YAGNI. T03 com 5 errorCodes adicionais será o gatilho real de 
  extração para `_envelope.py`. `tools.py` cresceu de ~150 para ~285 
  linhas em T02b — ainda manejável.

- **DD-2 (algoritmo prefix-hierarchical):** semântica "specification ≤ 
  stored" implementada via `_matches(lei, artigo, paragrafo, inciso, 
  alinea, entry)`. Sem curto-circuito em `spec is None`; loop verifica 
  todos os níveis. Filtro de deprecated estrutural via `c.status == 
  "active"`, parte do contrato canonical §4.2 (não AS-driven).

- **DD-3 (modelagem da specification):** parâmetros nomeados na 
  função pública (5 args). Sem dataclass `_LawArticleSpec` privada 
  (simplificação vs plano da sessão Code anterior). YAGNI aos 5 args.

- **DD-4 (fixture):** estender `policy_root_with_pack_clauses` para 
  incluir POL-004 (reversão fundamentada vs plano anterior; ver D1 
  acima). Coerência intra-fixture com `successors: [POL-004]` 
  preservada.

- **DD-5 (render romano):** colapsada após PR `fix/render-romano-in-T02a` 
  (#22.5) mergear. Helper `_format_law_reference` em `tools.py` é 
  single source of truth para rendering de referência legal. T02b 
  consome direto em `_render_query_text`; sem duplicação.

- **DD-5 sub-sub (assinatura do helper):** (d.1) helper aceita 5 
  parâmetros soltos, não `StatutoryReferenceEntry`. Justificativa 
  semântica: `StatutoryReferenceEntry` representa estado armazenado; 
  reusar para render de query confunde domínios deliberadamente 
  distintos. Compartilha função de formatação, não tipo. Convenção a 
  formalizar para T03+.

- **DD-6 (output wrapper):** `{"clauses": [<model_dump(mode="json", 
  exclude_none=True), ...>]}` com sort por `clause_id`. 
  Ordenação lexicográfica funciona porque IDs são zero-padded.

- **DD-7 (envelope INVALID_LAW_IDENTIFIER):** `accepted_values` 
  dinâmico do header com `sorted()` defensivo. `{provided!r}` produz 
  aspas simples casando canonical §4.2 line 485 literal.

- **DD-8 (rendering content[0].text):** três regras destiladas 
  (campos opcionais da query, singular/plural por count, breakdown 
  só em mistura de tipos). `_render_query_text` consome 
  `_format_law_reference` para o componente "lei + opcionais", 
  aplica regras de count/breakdown.

- **Convenção POL-9NN:** range reservado para fixtures sintéticas 
  de teste. Documentada em docstring do helper 
  `_write_synthetic_art5_root` e no pack README. Sem ADR (overhead 
  desproporcional).

- **Filtro de deprecated em `find_clauses_by_law_article` é 
  contratual per canonical §4.2 line 362.** AS-3 é o teste do 
  contrato, não o driver dele. Pin reforçado em três lugares do 
  brief de execução para prevenir framing errôneo como "edge case".

### Validações empíricas

- **Gate task-level ADR-0008 §3 cumprido em escala consolidada.** 
  Para `fix/render-romano-in-T02a` (#22.5): pytest 20/20, ruff verde, 
  mypy clean, Chat review independente desta sessão sobre 5 checks 
  estruturais do diff direto. Para `feat/policy-reader-find-clauses` 
  (#23): pytest 27/27 (11 T01 + 8 T02a com parametrize + 7 T02b + 1 
  wire-shape anchor), ruff verde, mypy clean, Chat review independente 
  sobre 4 arquivos modificados (este review).

- **AS-2 narrow pegou bug do `_matches` em primeiro run.** Confirmação 
  empírica de que granularidade de teste calibrada por dimensão de 
  falha funciona — bug que escaparia silencioso em 5 dos 6 testes foi 
  capturado pelo único teste que exercita a dimensão.

- **Anchor polimórfico exercitou anti-uniformization rule por código.** 
  Sem o anchor, a invariante canonical §4.2 line 362 ficaria só na 
  spec; com o anchor, implementação que filtrasse `clause_type` falha 
  em código.

- **Pattern PR sequencial cross-PR aplicado pela quarta vez.** #19 
  (cleanup cross-doc → T01), #20 (canonical-sync-A → continue), #21 
  (canonical-sync-B → T02b), #22.5 (fix/render-romano-in-T02a → T02b). 
  Convenção descritiva da propriedade desejada (auditabilidade de blame 
  por PR), não ritual de processo.

- **Sessão Chat persistente sustentou 3 sub-eventos sem degradação 
  observável.** Prep → cleanup → T02b execução + review. Contraste 
  com hipótese de "Chat fresh por sub-evento" — fluxo persistente 
  preservou continuidade narrativa de decisões (DDs cumulativas, 
  defense candidates encadeados) sem cross-contamination. Heurística 
  refinada (D1 acima) explica quando o pattern é seguro.

- **Reversão fundamentada DD-4 sem inércia.** Plano Code #22.5 dizia 
  "fixture nova"; plano Code #23 disse "estender existente" com 
  argumentos novos. Mudança ratificada pelo Chat. Não foi 
  "esqueceu da decisão anterior" — foi "encontrou argumentos melhores 
  via verificação direta de asserções T02a".

### Pendências para sessão #24+ ou PR futura

**Pré-merge de T02b:**

- João abre PR `feat/policy-reader-find-clauses` → `main` com a 
  mensagem que Code sugeriu. Mergeia squash. Registra hash neste 
  log substituindo `<TBD>`.

**Resolver em sessão #24 (Chat fresh — prep do prompt T03):**

- **DD-T03-X**: composição da fixture para AS-1..AS-7 de T03 (pack 
  POL-001..POL-004 completo, incluindo POL-002 que ficou de fora de 
  T02b). Análogo ao DD-T02b-4 mas em escala maior (4 vereditos × 4 
  cláusulas).
- **Algoritmo de matching de `check_applicability`.** Mecanismo 
  interno deferido (regra/LLM/híbrido) conforme handoff de Fase 1.5; 
  decisão substantiva nesta prep.
- **Filtro de escopo MVP via `not_applicable` para `operation ≠ 
  collection`** per ADR-0007. Implementação antes ou depois do 
  matching de cláusulas? Decisão na prep.
- **`structured_context` modelagem — Pydantic em models.py ou 
  parâmetros nomeados?** Análogo à DD-T02b-3 mas com mais campos 
  (4 campos: `data_categories`, `operation`, `legal_basis`, 
  `destination`).
- **Provenance trinque `(policy_schema_version, policy_version, 
  legal_framework)` em todo sucesso** per canonical §6.4. Onde 
  injetar — no envelope de sucesso, ou em layer separado?
- **Refator de envelope helpers para `_envelope.py`** (gatilho real 
  agora — T03 introduz 5 errorCodes). DD-T03 dedicada.

**Resolver em sessão Chat de housekeeping cross-doc futura:**

- **`tasks.md` §Companion edits cross-doc stale** — lista menciona 
  itens resolvidos por PRs #36-#39. Atualizar para refletir estado 
  real. Anotado em três sessões anteriores; ainda pendente.
- **canonical §4.2 line 472 sem ordinal `º`** — débito cosmético 
  descoberto durante T02b. Anotado em três lugares (relatório Code, 
  Chat review, este log) para evitar perda de rastro.
- **Convenções a formalizar em `.claude/rules/` ou ADR:** (a) 
  sessões fresh vs persistentes por tipo de output; (b) assertion 
  strictness vs subset; (d) função compartilhada vs tipo 
  compartilhado entre domínios. (c) POL-9NN já documentada em 
  docstring + pack README.

**Resolver pós-T03:**

- **T04** (`policy://vocabularies` + framework swap) — exercita 
  framework-awareness via consumo dinâmico do vocabulário carregado.
- **Gate milestone-level Milestone A** — sessão Chat dedicada após 
  T03+T04 fecharem, ~1-2h, manual exercise via MCP Inspector 
  validando cada Dado/Quando/Então de RFs 004-parcial, 005, 
  007-parcial, 008-parcial, 009.

**Resolver em janela futura sem urgência:**

- **DX residual:** linters (ruff, mypy) como dev deps oficiais em 
  `pyproject.toml`. Workaround `uvx ruff` / `uv run --with mypy mypy` 
  funciona. Sessão Code curta (~15min).
- **Decomposição formal de Milestone B em sessão Chat dedicada.** 
  Após gate milestone-level de A. Decisão Semgrep-on-Windows 
  precede.

### Nota de calibração metodológica

Sessão #22 operou em escala estendida: três rodadas de prep do prompt 
com classes distintas de catches por round (factual macro → 
transversal → semântico); ciclo Chat persistente sustentando 
sessão Code #22.5 (cleanup) + sessão Code #23 (T02b) sem fresh entre 
elas; bug do `_matches` capturado por AS-2 narrow no primeiro run, 
sem escalation porque o teste especificou o comportamento com 
precisão; cinco convenções novas formalizadas em texto (sessões 
persistentes vs fresh por output type, assertion strictness, função 
vs tipo compartilhado, POL-9NN, render contratual vs AS-driven). 
Defense candidates novos para Capítulo de Método do TCC:

1. **Multi-instance review com escalation progressiva**: três rounds, 
   três classes de catches, curva de saturação atingida em PR média. 
   Material reproduzível via "ordinal-por-ordinal das classes capturadas 
   por round, plotar densidade catches/superfície".
2. **AS-2 narrow como teste único pegando bug que escaparia 
   silencioso em 5/6 testes**: granularidade de teste calibrada por 
   dimensão de falha esperada, não por cenário. Empírico 
   quantificável.
3. **Reversão fundamentada de recomendação prévia ≠ inércia**: 
   DD-4 fixture mudou de "fixture nova" para "estender existente" 
   entre planos Code #22.5 e #23, com argumentos novos via 
   verificação direta. Não foi esquecimento; foi recalibração.
4. **Heurística sessões fresh vs persistentes por tipo de output**: 
   refinamento sobre quando Chat sustenta múltiplos ciclos Code. 
   Originalmente projetei por papel (Chat fresh por evento); 
   refinado para por tipo de output (verificável vs narrativo).
5. **Scope discipline cross-PR como propriedade descritiva, não 
   ritual**: falso alarme em #22.5 (João achou que tinha aberto 
   sessão errada) capturou que a propriedade desejada é 
   auditabilidade de blame por PR, atendida pelo Chat review do 
   diff. Pattern do projeto é descritivo, não normativo absoluto.
6. **Canary check via pin de pré-condição**: "se 
   `_format_law_reference` não estiver em main, abort". Replicação 
   do princípio "build the canary that screams first" (T01 
   wire-shape FastMCP) para estado de main entre sessões.

O método deste projeto está se estabilizando suficientemente para 
virar contribuição metodológica autônoma do TCC, não só ferramenta 
operacional. Capítulo de Método ganha cinco defense candidates 
empíricos desta sessão.

### Próximo passo

Sessão #24 (Chat fresh) — prep do prompt T03 (`check_applicability`, 
quatro vereditos + provenance trinque + escopo MVP via 
`not_applicable` para `operation ≠ collection`). Pré-leitura consome 
canonical §4.3 + ADR-0007 + pack POL-001..004 completo (incluindo 
POL-002 que ficou de fora de T02b). DD-T03 substantiva: refator de 
envelope helpers para `_envelope.py` (gatilho real agora — T03 
introduz 5 errorCodes). Custo estimado: ~1h Chat prep + ~3-4h Code 
implementação (T03 é a maior task de Milestone A em complexidade).

Pre-flight para #24 a documentar no session-handoff: três DDs 
estruturais (matching algorithm, structured_context modeling, 
provenance injection) + uma DD operacional (escopo MVP antes ou 
depois do matching) + um refator (envelope helpers).

---
## 2026-05-17 — sessão #22 — prep prompt T02b + cleanup render romano + 
T02b find_clauses_by_law_article + Chat review + housekeeping pré-T03

**Foco.** Sessão Chat persistente cobrindo o ciclo T02b completo + 
housekeeping pré-T03: refinamento iterativo do prompt T02b (v1 → v2 → v3 
→ execução) com três rodadas Chat ↔ Code, sessão Code dedicada à PR de 
cleanup mecânico `fix/render-romano-in-T02a`, sessão Code implementando 
T02b Fase 1 (plano) + Fase 2 (código), Chat review independente dos 
quatro arquivos modificados, e três PRs de housekeeping pré-T03 
(cosmetic debts + ADR-0009 + rules migration). Pattern emergente: 
**sessão Chat persistente sustenta múltiplos ciclos Code rotativos** sem 
fresh entre eles, conforme heurística destilada nesta sessão e 
formalizada em `.claude/rules/session-management.md` (PR-3 da housekeeping).

**Hashes mergeados em main:**
- `<TBD-PR39>` (PR #39) — refactor(policy-reader): unify law-reference 
  rendering with Roman inciso (squash de `fix/render-romano-in-T02a` — 
  sessão Code de cleanup)
- `fd6b833` (PR #40) — feat(policy-reader): T02b — tool 
  `find_clauses_by_law_article` com semântica prefix-hierarchical 
  (squash de `feat/policy-reader-find-clauses` — sessão Code de execução)
- `8f537d1` (PR #41) — chore: housekeeping cosmetic debts and status 
  flags refresh
- `cc275dc` (PR #42) — docs(adr): ADR-0009 — domain boundaries, share 
  functions not types
- `2ee1556` (PR #43) — chore: migrate three CLAUDE.md sections to 
  `.claude/rules/` and author two new rules

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1 multi-agent coordinator-subagent com human-in-the-loop — três 
  rodadas Chat ↔ Code aplicadas a prompt prep.** Primeira sessão a 
  exercitar o pattern coordinator-subagent sobre redação iterativa de 
  prompt: Code redigiu draft inicial v1 do prompt T02b (durante a sessão 
  T02a anterior), Chat refinou para v2 com seis correções 
  factuais/estruturais, Code reviewou v2 e pegou a lacuna do drift 
  romano vs literal de inciso que escapou ao Chat, Chat refinou para v3 
  absorbendo a DD-5 com quatro opções, João ratificou v3 com 
  sub-sub-decisão (d.1) sobre assinatura semântica do helper 
  compartilhado, Chat refinou para final. Padrão: cada rodada captura 
  uma classe distinta de catch (factual macro → transversal 
  cross-component → semântico de tipos). Material defense candidate forte 
  para Capítulo de Método.

- **D1 multi-instance review com classes distintas em um round.** Review 
  do Code sobre spec v1 de housekeeping capturou quatro classes em uma 
  única rodada: (a) factual desatualizado sobre feature 
  `.claude/rules/*.md` (Code cutoff Jan/2026, feature em v2.0.64), (b) 
  framing rotulado erradamente ("migração" cobrindo authoring novo), (c) 
  categorização ADR vs rules (questionou se ADR-0009 deveria ser 
  rule), (d) bundling vs separação (3 PRs vs PR única). Indicador 
  empírico de **convergência de critérios entre instâncias ao longo de 
  sessões** — reviewer (Code) está internalizando padrões do projeto 
  cada vez mais autonomamente. Defense candidate registrado.

- **D1 scope discipline cross-PR — propriedade descritiva, não ritual.** 
  Quando João abriu inadvertidamente sessão Code de cleanup achando que 
  ficara na sessão anterior (falso alarme — sessão era nova mas com nome 
  parecido), o reflexo inicial foi "refazer em sessão fresh para 
  preservar pattern". Chat refinou: scope discipline é descritiva de 
  auditabilidade de blame por PR, não normativa de "sessão fresh por 
  PR". Se o diff está limpo (verificável via Chat review do diff 
  direto), a propriedade está atendida independente da sessão Code que 
  produziu. Cinco checks estruturais propostos para validar o diff 
  direto; todos passaram. Pattern PR sequencial aplicado pela quarta vez 
  em escala documentada (#19, #20, #21, #22-cleanup), agora formalizado 
  em `.claude/rules/git-conventions.md` na PR-3 da housekeeping.

- **D1 session state management — heurística destilada e formalizada.** 
  Originalmente projetei o ciclo como "sessão Chat #22 prep → sessão 
  Chat #23 review T02b" com handoff entre as duas. João corrigiu: Chat 
  persiste sobre múltiplos ciclos Code, sessão fresh só após PR de T02b 
  mergear. Refinamento: contexto que vale preservar vs descartar não é 
  função do papel (Chat vs Code), é função do tipo de output. Code 
  produz código (output verificável independentemente, então sessão 
  fresh evita cross-contamination silenciosa). Chat produz decisões e 
  ratificações (output que ganha qualidade com histórico narrativo 
  cumulativo). Heurística destilada em texto na PR-3 da housekeeping 
  como `.claude/rules/session-management.md`.

- **D1 task decomposition — DD reversion fundamentada vs inércia.** 
  Plano que Code esboçou em sessão anterior recomendava criar fixture 
  nova `policy_root_with_pack_clauses_full` ao lado da existente. Em 
  sessão Code de execução T02b (Fase 1 plano), Code reverteu para 
  "estender fixture existente incluindo POL-004", com dois argumentos 
  novos: (i) coerência intra-fixture (POL-003 declara 
  `successors: [POL-004]`; POL-004 ausente da fixture é inconsistência 
  conceitual); (ii) verificação direta de T02a tests confirmou 
  asserções por `clause_id` específico, não por count. Coerência 
  justifica mudança; verificação direta neutraliza o risco original. 
  Defense candidate: reversão fundamentada de recomendação prévia ≠ 
  inércia, quando os argumentos da reversão são empíricos.

**Domínio 2 — Tool Design & MCP Integration (18%)**

- **D2 tool description com anti-uniformization rule literal no 
  docstring.** `server.py` wrapper de `find_clauses_by_law_article` 
  carrega no docstring final "The list MAY mix 
  `clause_type: definitional` and `clause_type: substantive` when the 
  same article is referenced by both kinds; consumers MUST NOT filter or 
  coerce by `clause_type` to uniformize the list." Literal do canonical 
  §4.2 line 362. Exemplo de como a invariante de contrato declarada na 
  spec vira parte do docstring que é consumido pelo cliente MCP via 
  `inputSchema`/`description`.

- **D2 discriminador polimórfico `clause_type` no output schema.** A 
  invariante anti-uniformização é exercitada por código no anchor de 
  teste `test_polymorphic_mix_at_art_5` sobre fixture sintética que 
  carrega POL-000 (definitional, real) + POL-901 + POL-902 (substantive, 
  sintéticas). Query `{lei: LGPD, artigo: 5}` retorna lista heterogênea 
  de 3 elementos com `types == {"definitional", "substantive"}`. **Sem 
  o anchor, a invariante ficaria só na spec** — implementação que 
  filtrasse definitional-only ou substantive-only passaria todos os 
  outros 5 AS por coincidência. Padrão D2 cobrado pela prova como 
  "schema design — output discriminator preservation".

- **D2 isError flag Option B canonicalizada — segunda aplicação 
  operacional.** T02b consumiu sem DD: envelope em 
  `structured_content` com `errorCode`, `content[0].text == message`, 
  wire `isError: false`. Convenção Option B já documentada em canonical 
  §5.1 + §5.3 + ADR-0002 §3 amendment (canonical-sync-B / #21). Segundo 
  consumidor (`INVALID_LAW_IDENTIFIER`) aplicou direto. Convenção 
  operacional ratificada por uso, não por mais um round de DD.

- **D2 errorCode `INVALID_LAW_IDENTIFIER` com `details` dinâmico do 
  header.** `accepted_values` do envelope vem de 
  `state.header.accepted_law_identifiers` (não hardcoded), com 
  `sorted()` defensivo para determinismo. Pin do brief capturou esse 
  requisito; teste AS-5 valida `details == {"provided": "GDPR", 
  "accepted_values": ["LGPD"]}` literal. Quando T04 introduzir framework 
  swap, `accepted_values` automaticamente reflete o header carregado.

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- **D3 plan mode com gate de OK explícito — quarta aplicação em 
  escala.** Sessão Code de execução T02b Fase 1 entregou plano com 8 DDs 
  enumeradas (DD-1 a DD-8), recomendação por DD justificada, mapping AS 
  tabular, riscos enumerados, alvos de edição escopados. Estrutura 
  permite ratificação granular: João ratificou DDs 1-3 e 5-8, mudou 
  DD-4 (reversion já discutida acima), anotou observação cosmética 
  sobre AS-4 (canonical line 472 sem º), e aprovou. Padrão "gate de OK 
  pode ser cirúrgico, não binário" materializado em escala. 
  Formalizado em `.claude/rules/spec-driven-workflow.md` na PR-3 da 
  housekeeping.

- **D3 `.claude/rules/` com `paths:` frontmatter como mecanismo 
  scope-condicional vs CLAUDE.md always-loaded.** Critério oficial 
  (escopo de aplicação, não tipo de conteúdo) aplicado às três migrações 
  na PR-3 da housekeeping: `spec-driven-workflow.md`, `privacy-safety.md`, 
  `git-conventions.md` sem `paths` (universais); `test-strategy.md` com 
  `paths: "tests/**/*.py"` (condicional). Adoção da forma oficial 
  documentada (`paths:`) com fallback registrado para `globs:` (issue 
  #17204) caso parsing falhe empiricamente. Validação direta da feature 
  via web search da documentação Anthropic (https://code.claude.com/docs/en/memory, 
  abril/2026); triangulação cross-instância sobre cutoff (Code reportou 
  Jan/2026; Chat verificou que `.claude/rules/` existe desde v2.0.64; 
  CLAUDE.md atual declara v2.1.123+).

- **D3 CLAUDE.md ↔ ADR ↔ rules — divisão por escopo de aplicação.** 
  Decisão arquitetural formalizada nesta sessão (e aplicada via 
  housekeeping PR-3): CLAUDE.md always-loaded para project overview + 
  immutable rules + status flags; `.claude/rules/<topic>.md` com `paths:` 
  para regras de processo com escopo condicional via glob; ADRs para 
  decisões com consequência runtime auditável. Critério threshold 
  registrado em ADR-0009 §"Out of scope for ADR vs in scope for 
  .claude/rules/": "se a decisão sobrevive a um overhaul de code-style 
  sem mudar comportamento, é rule; se mudar a decisão exige refactor 
  runtime com possível regressão, é ADR".

**Domínio 4 — Prompt Engineering & Structured Output (20%)**

- **D4.6 multi-instance review com escalation progressiva — três rounds 
  capturando classes distintas.** Round 1 (Code → Chat): Chat pegou seis 
  correções factuais/estruturais em v1 do prompt T02b (AS-1 query drift, 
  anchor polimórfico que não testava mix, render rules underspecified, 
  deprecated framing, fixture composição incompleta, verificação 
  obrigatória de estado real). Round 2 (Chat → Code): Code validou as 
  seis com referências de linha específicas e achou lacuna nova que Chat 
  não tinha visto sozinho — drift romano vs literal de inciso entre 
  `tools.py` T02a e canonical-sync-B pós-#21. Round 3 (Code → Chat → 
  João): Chat propôs opção (d) PR sequencial pequena que Code não tinha 
  considerado (recomendava bundle (c) por argumento de tamanho); João 
  ratificou (d) com sub-sub-decisão (d.1) sobre assinatura do helper 
  compartilhado pinando impedância semântica stored vs query. **Três 
  classes distintas de catches por round.** Saturação atingida em 3 
  rounds (curva de saturação para PR de tamanho médio).

- **D4 validation-retry implícito via AS-2 narrow — granularidade 
  calibrada por dimensão de falha.** Bug do `_matches` (curto-circuito 
  `if spec is None: return True` ignorava specs mais profundas) só foi 
  pego pelo AS-2 narrow no primeiro run da Fase 2. Sem split AS-2 em 
  narrow/broad — se ficasse apenas AS-2 broad como o brief original 
  pinava menos explicitamente — todos os outros 5 testes passariam por 
  coincidência. AS-1 (query `{artigo: 7}` sem opcionais), AS-3 (mesma 
  query), AS-4 (lista vazia, não exercita matching), AS-5 (erro antes do 
  matching), anchor polimórfico (broad query). **AS-2 narrow é o teste 
  único** que força a comparação de campo opcional não-trivial entre 
  spec e stored. Defense candidate forte: granularidade de teste 
  calibrada por dimensão de falha esperada, não por count de cenários. 
  Formalizado em `.claude/rules/test-strategy.md` na PR-3 da housekeeping.

- **D4 prompt engineering com structured phases iterado a quatro 
  versões.** v1 (esqueleto baseado em T02a, 270 linhas) → v2 (DD-5 
  adicionada, 540 linhas) → v3 (sub-sub d.1 pinada, 583 linhas) → 
  execução (DD-5 colapsada pós-cleanup, ~380 linhas). Cada versão 
  preservou estrutura Fase 1 plan / gate / Fase 2 execute / Post-Fase 2 / 
  Guard-rails; deltas foram cirúrgicos via `str_replace` em vez de 
  regeneração. Pattern de versionamento via deltas reduz risco de 
  introdução acidental de mudanças não-relacionadas.

**Domínio 5 — Context Management & Reliability (15%)**

- **D5 canary check via pin de pré-condição.** Brief de execução T02b 
  pinou: "Se `_format_law_reference` **não** estiver em `tools.py` após 
  `git pull origin main`, abort e levanta com João antes de prosseguir." 
  Asserção barata no início da Fase 1 que pega erro caro (Code 
  reimplementar helper em paralelo porque acha que não existe) antes 
  de o erro se propagar. Build the canary that screams first — princípio 
  aplicado em T01 para wire-shape FastMCP, replicado aqui para estado 
  de `main`. Padrão reusável: sessões T03+ que dependerem de helpers 
  consolidados em sessões anteriores carregam canary pin equivalente.

- **D5 provenance via leitura direta vs inferência — pin obrigatório 
  na Fase 1.** Brief v1 originalmente carregava afirmações herdadas do 
  Code da T02a sobre estado de `conftest.py`, `server.py:125-152`, 
  `tools.py`. Pin #6 das seis correções iniciais forçou: "verificar 
  essas afirmações lendo os arquivos direto; se divergente do brief, 
  parar e levantar antes de planejar". Code da Fase 1 cumpriu o pin com 
  10 verificações tabuladas direto contra os arquivos. Achado menor: 
  range de linhas `server.py:125-152` afirmado pelo brief é na verdade 
  `141-168` no estado real (drift menor não-bloqueante). Confirmação 
  empírica de que herdar afirmações entre sessões sem verificação 
  produz drift; pin "lê direto, não infere" funciona em escala.

- **D5 triangulação cross-instância sobre cutoff.** Durante review do 
  housekeeping spec v1, Code questionou se mecanismo 
  `.claude/rules/<topic>.md` com `paths:` frontmatter existia (cutoff 
  Code Jan/2026, mecanismo introduzido em Claude Code v2.0.64). 
  Resolução: Chat fez web search durante deliberação anterior 
  (https://code.claude.com/docs/en/memory + issues GitHub #13905, #17204 
  + ClaudeLog independente), Code ratificou epistemicamente ("não 
  conheço" ≠ "não existe"), João confirmou versão local v2.1.123+. 
  Três fontes externas + validação local = canary robusto. Pattern de 
  triangulação cross-instância sobre claims fora do cutoff comum: 
  defense candidate.

- **D5 escalation pattern — bug do `_matches` pego, validado, e 
  corrigido sem rerun.** Code da Fase 2 reportou: "Bug pego pelo AS-2 
  narrow no primeiro run. Versão original fazia curto-circuito... 
  Corrigi para semântica equivalente sem curto-circuito; a falha de 
  teste validou o algoritmo por código — sem o AS-2, o bug teria 
  escapado." Padrão clássico de generator/evaluator (Rajasekaran 2026): 
  o test escreveu primeiro o que o código deveria fazer, o código 
  falhou no que o teste exigia, o código corrigiu. **Sem escalation 
  para Chat** — Code resolveu localmente porque o teste especificou o 
  comportamento esperado com precisão suficiente. Contraste empírico 
  com T02a (#20) onde AS não-executável precisou escalation: lá o 
  contrato do framework FastMCP era a fonte do problema; aqui o 
  contrato canonical §4.2 era a fonte da solução.

- **D5 débito cosmético cross-doc anotado em múltiplos lugares, fechado 
  na housekeeping.** Inconsistência em canonical §4.2 line 472 
  (`"Nenhuma cláusula referencia LGPD Art. 50."` sem ordinal `º`) vs 
  linhas 431/459 (com ordinal). Implementação de T02b escolheu 
  consistência interna (`_format_law_reference` sempre emite `º`) e 
  asserção do AS-4 acompanha. Débito registrado em: (i) relatório do 
  Code Fase 2, (ii) Chat review independente, (iii) learning-log, (iv) 
  spec da housekeeping. Anotação quádrupla preveniu perda de rastro. 
  PR-1 da housekeeping (Edit 2) fechou em main; sanity check de Edit 3 
  expandiu cobertura para 6 instâncias análogas (canonical 631/640, 
  compact 302/421/427).

### Conceitos fora do escopo da prova

- **PR sequencial vs PR encadeada — git workflow.** Discussão sobre 
  (A) Code abre PR de cleanup → João mergeia em main → Code ramifica 
  T02b de main vs (B) Code ramifica T02b de branch de cleanup sem 
  mergear primeiro. (B) exige rebase pós-squash, frágil; (A) limpo com 
  gate Chat-review independente sobre cada PR. (A) escolhida; pattern 
  formalizado em `.claude/rules/git-conventions.md` na PR-3 da 
  housekeeping.

- **`git stash -u` para preservar untracked pré-checkout** — pin 
  operacional herdado de #19, aplicado na sessão Code de cleanup para 
  preservar working state durante checkout entre branches.

- **`git merge-tree` pairwise para validar PR independence** — Code da 
  housekeeping aplicou para confirmar que as três PRs 
  (`chore/cosmetic-debts-and-status-flags`, 
  `docs/adr-0009-domain-boundaries`, 
  `chore/rules-migration-and-authoring`) eram independentes (exit 0, 
  sem markers em todas as três combinações). Pattern útil para PRs 
  paralelas; vale anotar para uso futuro.

### Decisões tomadas

**Sobre T02b (sessão Code de execução):**

- DD-1 (helper extraction): (a) manter inline em `tools.py` por YAGNI. 
  T03 com 5 errorCodes adicionais será o gatilho real de extração para 
  `_envelope.py`. 
- DD-2 (algoritmo prefix-hierarchical): semântica "specification ≤ 
  stored" implementada via `_matches`. Sem curto-circuito em `spec is 
  None`; loop verifica todos os níveis. Filtro de deprecated estrutural 
  via `c.status == "active"`, parte do contrato canonical §4.2.
- DD-3 (modelagem da specification): parâmetros nomeados na função 
  pública. Sem dataclass privada (simplificação vs plano anterior).
- DD-4 (fixture): estender `policy_root_with_pack_clauses` para incluir 
  POL-004 (reversão fundamentada vs plano anterior).
- DD-5 (render romano): colapsada após PR de cleanup mergear. Helper 
  `_format_law_reference` em `tools.py` é single source of truth.
- DD-5 sub-sub (assinatura do helper): (d.1) 5 parâmetros soltos, não 
  `StatutoryReferenceEntry`. Justificativa semântica. Formalizado em 
  ADR-0009.
- DD-6 (output wrapper): `{"clauses": [...]}` com sort por `clause_id`. 
  Ordenação lexicográfica funciona porque IDs são zero-padded.
- DD-7 (envelope `INVALID_LAW_IDENTIFIER`): `accepted_values` dinâmico 
  do header com `sorted()` defensivo. `{provided!r}` produz aspas 
  simples casando canonical §4.2 line 485 literal.
- DD-8 (rendering `content[0].text`): três regras destiladas. 
  `_render_query_text` consome `_format_law_reference`.

**Sobre housekeeping pré-T03 (sessão Code de housekeeping):**

- 3 PRs em vez de bundle único (Code review do spec v1 capturou que 
  bundling heterogêneo prejudica reviewability). PR-1 cosmetic + 
  status flags (Edits 1-5), PR-2 ADR-0009 standalone (Edit 11), PR-3 
  rules migration + authoring (Edits 6-10 + remoções no CLAUDE.md).
- Adoção de `paths:` frontmatter na forma oficial documentada, com 
  fallback registrado para `globs:` (issue #17204) caso parsing falhe.
- 3 convenções migradas pura (`spec-driven-workflow.md`, 
  `privacy-safety.md`, `git-conventions.md`) e 2 rules novas authoreed 
  (`session-management.md`, `test-strategy.md`).
- ADR-0009 com seção "Out of scope for ADR vs in scope for 
  .claude/rules/" delimitando threshold para futuras decisões 
  borderline.

**Convenções formalizadas (em rules da PR-3):**

- Sessões fresh vs persistentes por tipo de output 
  (`session-management.md`).
- Assertion strictness em testes — estrita para anchors (definem 
  contrato), subset para AS (exercitam contrato) (`test-strategy.md`).
- Granularidade de teste calibrada por dimensão de falha 
  (`test-strategy.md`).
- Plan mode pattern (Fase 1 / gate / Fase 2) obrigatório para tasks 
  com múltiplos DDs (`spec-driven-workflow.md`).
- Source-of-truth precedence: artefatos reais > docs em divergência 
  mecânica (`spec-driven-workflow.md`).
- Companion edits cross-doc como living debt registry 
  (`spec-driven-workflow.md`).
- PR sequencial vs PR mista anti-pattern (`git-conventions.md`).
- Convenção POL-9NN para fixtures sintéticas de teste (documentada em 
  docstring de `_write_synthetic_art5_root` + pack README).
- Função compartilhada entre domínios vs tipo compartilhado (ADR-0009).
- Filtro de deprecated em `find_clauses_by_law_article` é contratual 
  per canonical §4.2, não AS-driven (pinado no docstring de 
  `tools.find_clauses_by_law_article`).

### Validações empíricas

- **Gate task-level ADR-0008 §3 cumprido em escala consolidada.** 
  Cleanup: pytest 20/20, ruff/mypy clean, Chat review de 5 checks 
  estruturais do diff. T02b: pytest 27/27, ruff/mypy clean, Chat review 
  de 4 arquivos modificados. Housekeeping PR-1: 27 testes preservados, 
  greps verificados, CLAUDE.md mantém abaixo de 200 linhas. 
  Housekeeping PR-2: ADR-0009 criado isoladamente, sem efeito em 
  testes. Housekeeping PR-3: 27 testes preservados, seções migradas 
  removidas do CLAUDE.md (87 → 69 linhas), 5 arquivos em 
  `.claude/rules/` criados.

- **AS-2 narrow pegou bug do `_matches` em primeiro run.** Confirmação 
  empírica de que granularidade de teste calibrada por dimensão de 
  falha funciona — bug que escaparia silencioso em 5 dos 6 testes foi 
  capturado pelo único teste que exercita a dimensão.

- **Anchor polimórfico exercitou anti-uniformization rule por código.** 
  Sem o anchor, a invariante canonical §4.2 line 362 ficaria só na 
  spec; com o anchor, implementação que filtrasse `clause_type` falha 
  em código.

- **Pattern PR sequencial cross-PR aplicado pela quarta vez.** #19 
  (cleanup cross-doc → T01), #20 (canonical-sync-A → continue), #21 
  (canonical-sync-B → T02b), #22 cleanup (fix/render-romano-in-T02a → 
  T02b). Convenção descritiva da propriedade desejada (auditabilidade 
  de blame por PR), formalizada em `.claude/rules/git-conventions.md`.

- **Sessão Chat persistente sustentou 6 sub-eventos sem degradação 
  observável.** Prep T02b (3 rodadas) → cleanup → T02b execução + 
  review → review housekeeping spec (1 round Code → Chat) → 
  housekeeping aplicação 3 PRs. Contraste com hipótese de "Chat fresh 
  por sub-evento" — fluxo persistente preservou continuidade narrativa 
  de decisões (DDs cumulativas, defense candidates encadeados, 
  refinamentos iterativos do spec). Heurística refinada formalizada 
  em `.claude/rules/session-management.md`.

- **Reversão fundamentada DD-4 sem inércia.** Plano Code anterior dizia 
  "fixture nova"; plano Code da execução T02b disse "estender 
  existente" com argumentos novos. Mudança ratificada pelo Chat. Não 
  foi "esqueceu da decisão anterior" — foi "encontrou argumentos 
  melhores via verificação direta de asserções T02a".

- **Three-way validation sobre cutoff Code/Chat/Anthropic docs.** 
  Question de Code sobre feature `.claude/rules/` triangulada com 
  documentação oficial Anthropic + issues GitHub + fonte independente 
  + confirmação local de versão do João. Canary robusto contra claims 
  fora do cutoff comum.

### Pendências para sessão #23+ ou PR futura

**Resolver na #23 (Chat fresh — prep do prompt T03):**

- Cinco pre-flight pins documentados no session-handoff (DDs 
  antecipadas: envelope extraction, reasoning mechanism, scope filter, 
  structured_context modeling, provenance injection).
- Rascunho do prompt T03 com Fase 1 + gate + Fase 2 + guard-rails. 
  Estrutura reusa pattern T01/T02a/T02b. Custo estimado: ~1-1.5h Chat 
  de prep (T03 é a maior task em complexidade).

**Resolver em sessão Code de execução T03 (#24+):**

- Implementação completa de `check_applicability` em `tools.py` + thin 
  wrapper em `server.py` + Pydantic `StructuredContext` em `models.py` 
  (se DD-T03-4 ratificar) + refator de envelope helpers para 
  `_envelope.py` (se DD-T03-1 ratificar extração) + testes em 
  `test_check_applicability.py` cobrindo AS-1..AS-8.
- Gate task-level ADR-0008 §3 conforme `.claude/rules/spec-driven-workflow.md`.

**Resolver pós-T03:**

- **T04** (`policy://vocabularies` + framework swap) — exercita 
  framework-awareness via consumo dinâmico do vocabulário carregado.
- **Sync canonical §4.3 `evidence` → `reason`** após T03 implementar e 
  empiricamente validar (canonical-sync-C ou housekeeping cross-doc 
  futura).
- **Sync RF-003 ↔ canonical §4.3 field naming** após T03 implementar e 
  empiricamente validar.

**Resolver em sessão Chat de housekeeping cross-doc futura (sem 
urgência):**

- **Variantes "LGPD Art. N" sem ordinal `º` em prosa** — descobertas 
  pelo Code durante Edit 3 da housekeeping (canonical §4.2 line 472 
  cobriu o pattern `Art\. [0-9]+\.` mas variantes inline em prosa 
  passaram fora do scope do grep). Não bloqueia nada; cosmético 
  textual em docs. Sessão Chat de housekeeping cross-doc futura 
  resolve.

**Resolver em janela futura sem urgência:**

- **DX residual:** linters (ruff, mypy) como dev deps oficiais em 
  `pyproject.toml`. Workaround `uvx ruff` / `uv run --with mypy mypy` 
  funciona. Sessão Code curta (~15min) em qualquer janela.
- **Itens deferidos T03 herdados de Fase 1.5** (já listados em 
  `tasks.md` §Companion edits): `operation`/`legal_basis` vs 
  `operation_type`/`declared_legal_basis`; `evidence` vs `reason` em 
  `not_applicable`. Resolver pós-T03 quando spec for empiricamente 
  validado.
- **Decomposição formal de Milestone B em sessão Chat dedicada.** 
  Após gate milestone-level de A. Decisão Semgrep-on-Windows precede.

### Nota de calibração metodológica

Sessão #22 operou em escala estendida documentada: três rodadas de 
prep do prompt T02b com classes distintas de catches por round 
(factual macro → transversal → semântico); ciclo Chat persistente 
sustentando 6 sub-eventos (prep T02b, cleanup, T02b execução, T02b 
review, review housekeeping spec, housekeeping aplicação 3 PRs) sem 
degradação; bug do `_matches` capturado por AS-2 narrow no primeiro 
run sem escalation; oito convenções novas formalizadas em texto 
auditável (5 rules + 1 ADR + 2 pinadas em docstrings/pack README); 
triangulação cross-instância sobre cutoff (Code/Chat/Anthropic 
docs/versão local) validando feature do Claude Code; review do Code 
sobre housekeeping spec capturou 4 classes em 1 round, sinal de 
convergência metodológica entre instâncias.

Defense candidates consolidados em #22 (alguns iniciados em sessões 
anteriores, todos com baseline empírico em #22):

1. **Multi-instance review com escalation progressiva** — três rounds, 
   três classes de catches, curva de saturação em PR média.
2. **AS-2 narrow como teste único pegando bug do `_matches` que 
   escaparia silencioso em 5/6 testes** — granularidade calibrada por 
   dimensão de falha esperada.
3. **Reversão fundamentada DD-4** (fixture nova → estender existente) 
   com argumentos novos via verificação direta ≠ inércia.
4. **Heurística sessões fresh vs persistentes por tipo de output** — 
   refinamento empírico sobre quando Chat sustenta múltiplos ciclos 
   Code.
5. **Scope discipline cross-PR como propriedade descritiva** 
   (auditabilidade de blame), não ritual normativo — falso alarme 
   capturou isso.
6. **Canary check via pin de pré-condição** — replicação do "build the 
   canary that screams first" (#19 wire-shape FastMCP) para estado de 
   main entre sessões.
7. **Triangulação cross-instância sobre cutoff** — Code/Chat/docs 
   externas/versão local concordando contra mesma source de verdade.
8. **Convergência metodológica entre instâncias** — review do Code 
   sobre housekeeping spec capturou 4 classes em 1 round, indicador de 
   internalização autônoma dos critérios do projeto.

O método está se estabilizando suficientemente para virar 
contribuição metodológica autônoma do TCC, não só ferramenta 
operacional. Capítulo de Método ganha oito defense candidates 
empíricos desta sessão, mais a formalização canônica de oito 
convenções em rules/ADR auditáveis.

### Próximo passo

Sessão #23 (Chat fresh) — prep do prompt T03 (`check_applicability`, 
quatro vereditos + provenance trinque + escopo MVP via 
`not_applicable` para `operation ≠ collection`). Pré-leitura consome 
canonical §4.3 + ADR-0007 + pack POL-001..004 completo (incluindo 
POL-002 que ficou de fora de T02b). DD-T03 substantiva: refator de 
envelope helpers para `_envelope.py` (gatilho real agora — T03 
introduz 5 errorCodes). Custo estimado: ~1h Chat prep + ~3-4h Code 
implementação (T03 é a maior task de Milestone A em complexidade).

Pre-flight para #23 a documentar no session-handoff: cinco DDs 
antecipadas (envelope extraction, reasoning mechanism, scope filter, 
structured_context modeling, provenance injection) + uma DD 
operacional (escopo MVP antes ou depois do matching) + um refator 
(envelope helpers).

---

## 2026-05-18 — sessão #23 — prep prompt T03 + ciclo T03 fechado + housekeeping cross-doc pós-T03 despachado para Code

**Foco.** Sessão Chat persistente cobrindo dois sub-ciclos completos
sequenciais: (a) ciclo T03 — prep do prompt em 3 versões iterativas
(v1 → v2 → v3) com 3 reviews independentes em sessões Code clean,
sanção do plano da Fase 1 (GATE 1), Fase 2 execução pelo Code, Chat
review do diff pós-Fase 2.E com 2 correções pré-PR aplicadas
(`destination` em StructuredContext + teste para DD-T03-12), body do
PR redigido, T03 mergeada em main com 43/43 testes verdes; (b) ciclo
de housekeeping cross-doc pós-T03 — análise de bloqueio +
classificação mecânico vs design dos 5 débitos cross-doc residuais,
aplicação no workspace Chat via `str_replace` cirúrgicos para
validação, descoberta de 4º site implícito em compact §5.3 linha 376
durante leitura adjacente, decisão de migrar execução final para Code
via prompt versionado (v1 → v2 pós-review do Code) usando 10 pares
verbatim `old_str`/`new_str`. Maior sessão Chat documentada do
projeto em volume de sub-eventos (14+) preservando continuidade
narrativa do início ao fim sem fresh entre eles.

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1.4 Escalation patterns — `indeterminate` como honest escalation
  estruturada.** Veredito `indeterminate` em `check_applicability`
  materializa "policy gap identification" do exam guide: o componente
  não tenta adivinhar; devolve sinal estruturado com
  `verification_scope` (dimension, prescribed_treatment,
  verification_target) que o consumidor humano precisa para verificar
  manualmente upstream. Framing semântico cristalizado no docstring
  de `check_applicability` (1 frase per refinamento de Fase 2.C):
  "is a first-class verdict per canonical §7.3 — signals static
  analysis cannot decide this dimension; does not represent
  evaluation failure". Defense narrative full ("indeterminate como
  sinal de evolução da Política") mora aqui no learning-log e migra
  para o Capítulo de Método.

- **D1.6 Task decomposition — 10 DDs sancionadas + 2 emergentes
  durante execução T03 + 5 débitos de housekeeping decompostos em
  10 sub-edits cirúrgicos.** Plano sancionado no GATE 1 carregou 10
  DDs deliberadas em Chat (DD-T03-1 a DD-T03-10). Fase 1 do Code
  descobriu terceira ocorrência de drift 1 em `compact.md` linha
  371, gerando DD-T03-11 como adição construtiva (escalou sync
  pós-T03 de 2 para 3 sites). Fase 2.C produziu DD-T03-12 —
  `DefinitionalClause` → `not_applicable` como caminho de retorno
  adicional (5 paths, não 4). Em housekeeping, leitura adjacente
  descobriu 4º site implícito em compact §5.3 linha 376 (nota
  genérica que ficaria imprecisa após edit do bloco YAML linha
  371) — escalou drift 1 de 3 para 4 sites. Decomposição
  prompt-housekeeping em 10 sub-edits (Edits 1, 2a, 2b, 3, 4, 5,
  6, 7, 8, 9) materializou granularidade adequada: 1 substituição
  textual por sub-edit; débitos com múltiplos sites tratados em
  edits separados; débito #2 (DD-T03-12 nota nova) isolado em
  edit dedicado após review do Code apontar bundle indesejado em
  v1.

- **D1.7 Session state management — Chat persistente sustentou 14+
  sub-eventos sem fresh entre eles.** Sessão #23 cobriu: (T03)
  prep v1 → review #1 (Code clean) → prep v2 → review #2 + #3
  (Code clean independentes) → prep v3 → GATE 1 (Fase 1 Code) →
  Chat review diff (Fase 2.E Code) → correções pré-PR → body PR
  → T03 mergeada → (housekeeping) análise de bloqueio →
  classificação mecânico/design → ratificação 5 decisões → 4
  leituras adjacentes (canonical §4.3, compact §5.3, tasks.md
  T03, test Anchor 1) → aplicação 5 débitos no workspace Chat →
  decisão de migrar para Code → prompt v1 → review do Code do
  prompt → prompt v2. Quatorze ciclos Chat ↔ Code, todos
  preservando continuidade narrativa (DDs cumulativas, defense
  candidates encadeados, leituras feitas em uma fase reusadas em
  outra). Heurística "Chat persistente por tipo de output
  narrativo" formalizada em `.claude/rules/session-management.md`
  reconfirmada empiricamente em escala consideravelmente maior
  que #22 (6 sub-eventos) e do que a primeira metade da própria
  #23 antes do housekeeping (7 sub-eventos).

- **D1 Multi-agent coordinator-subagent com human-in-the-loop —
  reviews independentes em sessões Code clean, em dois objetos
  distintos.** Três reviews da prep T03 (Code clean × 3,
  contextos isolados); um review do prompt-housekeeping (Code
  clean). Pattern de generator (Chat redator) → evaluator (Code
  reviewer independente sem ver rounds prévios) materializado
  duas vezes na mesma sessão sobre artefatos diferentes —
  primeira vez em #23 que o pattern foi exercitado em prompt
  (artefato narrativo) e não só em código (artefato verificável).
  Convergência empírica registrada em "Validações empíricas".

**Domínio 2 — Tool Design & MCP Integration (18%)**

- **D2 Tool description anatomy.** Docstring de `check_applicability`
  em `server.py` cobre 4 vereditos com semântica de cada um, 6
  errorCodes (4 novos + 2 reaproveitados de T02a), trinca de
  provenance, framing semântico de `indeterminate`. Convenção
  canonical §4.3 aplicada sem seções nomeadas obrigatórias.

- **D2 Error envelope estruturado + discriminador implícito.** T03
  adiciona 4 errorCodes novos (`CLAUSE_DEPRECATED`,
  `INVALID_DATA_CATEGORY`, `INVALID_OPERATION`,
  `EMPTY_DATA_CATEGORIES`) ao `ErrorEnvelope` Pydantic existente.
  `accepted_values` em INVALID_DATA_CATEGORY/INVALID_OPERATION é
  dinâmico — carregado de POL-000 e do operation vocabulary runtime
  via helpers `_load_*_vocabulary` em `_envelope.py`, não hard-coded.

- **D2 isError flag — Option B reforçada via novo anchor e
  housekeeping cross-doc.** Anchor
  `test_deprecated_clause_returns_envelope_not_tombstone` protege
  assimetria `check_applicability(POL-003)` (envelope retryable) vs
  `get_clause(POL-003)` (sucesso com tombstone). Sexto sítio de
  cristalização de Option B (sítios prévios: canonical §5.1/§5.3,
  compact §2, `models.py` `ErrorEnvelope.__doc__`, anchor wire-shape
  de T02a, ADR-0002 §3 amendment). Housekeeping pós-T03 adiciona
  drift sync em tasks.md AS-7/AS-8 — phrasing `isError: true`
  lógico substituído por wire literal "(per Option B — wire
  `isError: false`; envelope em `structured_content`)". Sétimo
  sítio (tasks.md) cristaliza a convenção em superfície
  prescriptiva, não só descritiva.

- **D2 MCP resources como vocabulário runtime.** POL-000 (única
  `DefinitionalClause` carregada no MVP) consumida runtime via
  `_load_data_categories_vocabulary(state)` em `_envelope.py`.
  Convenção formalizada: validations de vocabulário consomem POL-000
  via helper, não inline em `check_applicability`. Análogo para
  `operation` via `state.vocabularies["operation"].values`. Type
  narrowing via `isinstance(pol_000, DefinitionalClause)` necessário
  para mypy strict (union `Clause = DefinitionalClause |
  SubstantiveClause`).

- **D2 output polimórfico via Pydantic discriminated union plain.**
  `Verdict = Compliant | ViolationCandidate | Indeterminate |
  NotApplicable` discriminada por `Literal[verdict]` em cada
  variant. Precedente reusado de `Clause` em `models.py:146`. Sem
  `Annotated[Union[...], Field(discriminator="verdict")]` — JSON
  schema generation não é deliverable de T03 (FastMCP gera
  inputSchema da assinatura da tool, não dos models de output).
  Plain union basta; refinamento opcional adiável se T04 ou
  Milestone C exigir.

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- **D3 `.claude/rules/` convocadas nominalmente em vez de
  re-explicar.** v3 do prompt T03 é ~30% menor que v1 em volume
  porque `test-strategy.md` §"Granularity calibration" e
  §"Anchor test as second-line defense" são chamadas por nome em
  DD-T03-7/DD-T03-9, e `spec-driven-workflow.md` é chamada para
  plan-mode + source-of-truth precedence. Materializa o benefício
  empírico do housekeeping pré-T03 (PRs #41-43): cristalização
  canônica de convenções em rules permite redação subsequente mais
  enxuta. Defense candidate.

- **D3 Plan mode + pause-and-ask + str_replace cirúrgico
  housekeeping.** Fase 1 do Code seguiu o pattern da
  `.claude/rules/spec-driven-workflow.md`: leitura obrigatória →
  plano com 10 DDs ratificadas + 1 emergente (DD-T03-11) → GATE 1
  → Fase 2 com gates intermediários (mypy 2.A, pytest 2.B, etc).
  Pause-and-ask cumprido em todas as pré-deliberações. Para
  housekeeping cross-doc, prompt usou `str_replace` cirúrgico com
  10 pares verbatim `old_str`/`new_str` em vez de substituição de
  arquivo inteiro — pattern alternativo aplicável quando cleanup
  é mecânico (sem decisões de design) e auditabilidade de cada
  edit importa mais que velocidade. Vantagens auditáveis: (a)
  diff resultante mostra apenas os sites tocados; (b) `old_str`
  funciona como canary de drift — se o estado de main divergiu
  do que o Chat assumiu, o `str_replace` falha cedo em vez de
  produzir resultado silenciosamente incorreto; (c) Code não
  precisa inferir contexto além do par.

- **D3 CLAUDE.md status flags autoritativos pós-housekeeping.** v3
  do prompt T03 enxugou "Estado herdado" para "leia CLAUDE.md
  status flags + state real de tools.py/models.py/conftest.py" em
  vez de enumerar 5+ bullets do que existia em cada arquivo.
  Pattern materializa o ganho do housekeeping pré-T03 — status
  flags em CLAUDE.md são fonte autoritativa única do estado de
  cada componente; prompts subsequentes referenciam, não duplicam.

**Domínio 4 — Prompt Engineering & Structured Output (20%)**

- **D4.1 Few-shot examples como anchors de comportamento.** Os 4
  exemplos da canonical §4.3 (compliant, violation_candidate,
  indeterminate, CLAUSE_DEPRECATED) foram a base para os 4 verdict
  models em `models.py` e para os helpers de evidência/reason em
  `tools.py`. Format demonstration via exemplos textuais → schema
  Pydantic + reasoning rules.

- **D4.2 Structured output via tool_use forçado + Pydantic
  discriminated union.** `check_applicability` retorna union de 4
  variantes discriminadas por `Literal[verdict]` no
  `structured_content`. Validation por construção via Pydantic; o
  caller (Milestone C Matcher) consumirá o type sem ambiguidade.
  Provenance trinque inline em cada variante (DD-T03-5).

- **D4 JSON Schema + Pydantic — Opção 1 do review #1.** Tensão Issue
  B de review #1 sobre `StructuredContext` resolvida: wrapper de
  `server.py` assina `structured_context: dict[str, Any]` (FastMCP
  gera inputSchema do dict, não-aninhado); `tools.py` valida
  semanticamente (4 errorCodes per spec §5.4) ANTES de construir
  `StructuredContext` Pydantic. `StructuredContext` é tipo interno
  pós-validação, NÃO exportado como contrato MCP. Decisão sobre
  subir para contrato externo deferred para Milestone C quando
  Matcher consumir.

- **D4 Multi-instance review com escalation progressiva — 5 rounds
  + 1 round sobre artefato prompt.** Round 1 (review v1 do prompt
  T03, Code clean): 2 materiais alta severidade (consent token
  comparison, `StructuredContext` ambiguidade
  wrapper/Pydantic). Round 2 (review v2 do prompt T03, Code
  clean): 0 materiais; 3 refinamentos textuais minor. Round 3
  (review v2 do prompt T03 independente, Code clean): 2 materiais
  média severidade (`applies_to.operation` não checado,
  `isError: true` drift em tasks.md). Round 4 (Fase 1 Code): 1
  emergente construtiva (DD-T03-11 escalou drift 1 para 3
  sítios). Round 5 (Chat review do diff pós-Fase 2.E): 2
  materiais (destination ausente em StructuredContext, cobertura
  faltante para DD-T03-12). Round 6 (review do prompt-housekeeping
  v1, Code clean independente): 5 observações (numeração
  dessincronizada entre §Context e headings, shell mismatch
  PowerShell vs bash, Edit 2 bundla 2 débitos, falta canary
  externo para CI/scripts, limitação single-line do sanity grep).
  Trend de convergência: severidade decai monotonicamente até
  verificação empírica direta tomar lugar de review textual.
  **Pattern novo materializado em #23: prompt como artefato
  auditável com mesma rigor que código** — versionamento
  iterativo (v1 → v2) com review independente entre versões é
  pattern válido para output narrativo, não só para código.

**Domínio 5 — Context Management & Reliability (15%)**

- **D5 Provenance/citations ubíqua via helper centralizado.**
  Helper `_provenance_from(state) -> Provenance(TypedDict)` em
  `_envelope.py` é fonte única do trinque
  (`policy_schema_version`, `policy_version`, `legal_framework`).
  Injetado inline via `**unpack` em TODOS os 4 vereditos de
  sucesso. Anchor parametrizado
  `test_provenance_trinque_in_every_verdict_path` garante por
  construção (igualdade exata vs header, não substring).
  Materializa ADR-0005 Decision 5 (provenance non-opcional) +
  canonical §6.4. Refinamento técnico de Fase 2.C: `Provenance`
  é `TypedDict`, não `dict[str, str]`, porque mypy strict bloqueia
  `**unpack` em construtor que tem `verdict: Literal[...]`
  (colapso de tipo shadowing o discriminador). Solução mínima.
  Housekeeping pós-T03 adiciona 5º setup ao Anchor 1 cobrindo
  sub-caso "MVP scope `not_applicable`" — garantia por construção
  expandida de 4 para 5 paths de sucesso.

- **D5 Escalation patterns — `indeterminate` como honest escalation
  estruturada.** Cobertura cruzada com D1.4 acima. Pattern
  adicional para D5 especificamente: o ramo `indeterminate` é o
  sinal estável que o consumidor (Matcher em Milestone C) usa para
  "honest escalation" para revisão humana, não para retry
  automatizado. Sub-caso de policy gap identification +
  escalation criteria do exam guide.

- **D5 Source-of-truth precedence aplicada a 4 drifts em
  housekeeping cross-doc.** Drift 1 (`reason` vs `evidence` em
  `not_applicable`): ADR-0007 D3 + tasks.md AS-4/AS-5 vs canonical
  §4.3 linha 562 + 566 + compact §5.3 linha 371 + linha 376
  (descoberta nova). ADR + 2 AS vs 4 sites descritivos → ADR wins
  (camada normativa mais alta + explicitude do MVP scope). Drift
  2 (`isError: true` lógico em tasks.md AS-7/AS-8): wire é Option
  B per 6+ sítios cristalizados; tasks.md AS é o sítio que recebe
  sync. Drift 3 implícito (`destination` em canonical §4.3 sem
  cobertura em tasks.md AS): canonical wins per source-of-truth
  precedence; `destination: str | None = None` adicionado em
  `StructuredContext` pós-review do Chat de T03; AS-1 estendida
  no housekeeping para exercitar. Drift 4 (DD-T03-12 — caminho
  emergente `DefinitionalClause` → `not_applicable` não
  documentado em canonical §4.3): teste já em main; canonical
  precisa documentar — nota inline nova adicionada no
  housekeeping. Pattern operacional consolidado: **drift cumulativo
  é detectado por leitura adjacente ao site de edição, não por
  enumeração prévia**. DD-T03-11 começou com 2 sites enumerados
  em Chat (canonical 562 + 566), escalou para 3 na Fase 1 do
  Code (compact 371), e agora para 4 na fase de housekeeping
  (compact 376 implícito). Reviewers independentes em rounds
  sucessivos continuam agregando enquanto a leitura toca o estado
  real do código.

### Conceitos fora do escopo da prova

- **TypedDict para `**unpack` ergonômico.** `Provenance(TypedDict)`
  resolve fricção real do mypy strict sem alterar contrato wire.
  Refino dentro do escopo do plano sancionado; sem ADR ceremony per
  ADR-0005 D7 (reasoning mechanism livre). Pattern: refino técnico
  que preserva contrato observável + resolve fricção do toolchain +
  não introduz coupling novo = aceitável sem ratificação.

- **DD emergente vs refinamento tactical — critério de
  classificação.** Provenance TypedDict não muda o set de retornos
  observáveis pelo caller (estrutura wire preservada) → refinamento
  tactical aceito sem ratificação. DefinitionalClause →
  `not_applicable` muda o set de retornos (5 paths, não 4) → DD
  emergente que exige teste de cobertura próprio. Critério
  cristalizado para o Capítulo de Método.

- **Plan-mode admite refinamento técnico sem voltar ao Chat.** Code
  aplicou TypedDict e DefinitionalClause path em Fase 2.C sem
  re-deliberar com Chat. Defensável porque (a) preserva contrato
  observável (TypedDict) ou (b) é caminho funcional necessário para
  evitar crash (DefinitionalClause). Mas DD-T03-12 (DefinitionalClause)
  exigiu cobertura própria — Chat review do diff capturou o gap e
  o Code adicionou teste pós-correção.

- **Cirurgia textual via `str_replace` pares verbatim como pattern
  alternativo a substituição de arquivo inteiro.** Aplicável quando
  cleanup é mecânico (sem decisões de design) e auditabilidade de
  cada edit importa mais que velocidade. Materializado no
  prompt-housekeeping com 10 pares verbatim. Trade-off: prompt fica
  mais longo (10 pares ocupam espaço); mas ganho de auditabilidade
  compensa. Cada `old_str` funciona como canary de drift; se o
  estado de main divergiu do que o Chat assumiu, o `str_replace`
  falha cedo. Pattern complementar ao precedente de #20-#21
  (canonical-sync-A/B com substituições cirúrgicas via
  str_replace) — mas agora **prompt-formalized** para Code
  execution, não execução direta do Chat.

- **Limitação de single-line substring matching em sanity grep.**
  `grep "evidence" file.md | grep "not_applicable"` só detecta
  co-ocorrência em linha única. Aceitável para sites onde o
  pattern crítico (`evidence: <`) é canonicamente single-line.
  Para sites multi-linha ou prosa adjacente, requer abordagem
  mais sofisticada (e.g., `grep -A`/`-B`, awk multi-line, ou
  cross-reference manual). Identificado no review do
  prompt-housekeeping v1 como limitação não documentada;
  documentado no v2.

### Decisões tomadas

**Sobre o prompt T03 (sessão Chat #23 primeiro sub-ciclo):**

- 10 DDs sancionadas no GATE 1: DD-T03-1 (extrair `_envelope.py`),
  DD-T03-2 (rule-based + token canônico `consent`), DD-T03-3 (filtro
  MVP entre lookup e applicability match), DD-T03-4 (wrapper dict;
  `StructuredContext` interno pós-validação), DD-T03-5 (provenance
  via `_provenance_from`), DD-T03-6 (discriminated union plain),
  DD-T03-7 (AS-5 via behavioral proxy — Opção A), DD-T03-8 (ordem
  fail-fast), DD-T03-9 (2 anchors obrigatórios: trinque + assimetria
  deprecated), DD-T03-10 (loaders de vocabulário em `_envelope.py`,
  defensive access).

- DD-T03-11 emergente (Fase 1 Code): sync drift 1 escalado para 3
  ocorrências (compact §5.3 linha 371 descoberta).

- DD-T03-12 emergente (Fase 2.C Code, ratificada via Chat review do
  diff): `DefinitionalClause` → `not_applicable` como caminho de
  retorno adicional (5 paths, não 4). Teste de cobertura próprio
  obrigatório.

- Refinamento técnico (Fase 2.C): `Provenance(TypedDict)` em vez de
  `dict[str, str]` para `**unpack` em verdict constructors mypy
  strict.

**Sobre housekeeping pós-T03 (sessão Chat #23 segundo sub-ciclo):**

- DD-T03-11 escalada para 4 sites (compact §5.3 linha 376 descoberta
  durante leitura adjacente). Sync agora cobre canonical §4.3 bloco
  YAML + nota prosa, compact §5.3 bloco YAML + nota genérica
  expandida.

- DD-T03-12 canonical sync — nota inline em canonical §4.3
  documentando os 3 sub-casos de `not_applicable` (MVP scope +
  applicability mismatch + definitional clause). Sem subseção
  dedicada porque §4.3 é prosa contínua, não estruturada por
  veredito.

- Drift 2 (tasks.md AS-7/AS-8): phrasing Opção (c) escolhida —
  preservar estrutura original + adicionar parêntese "(per Option B
  — wire `isError: false`; envelope em `structured_content`)". Mais
  enxuto que Opção (b) verbosa; preserva legibilidade da ementa da
  AS.

- Gap `destination`: Opção (ii) escolhida — estender AS-1 brief +
  setup do teste em vez de criar AS-9 dedicada. Coerente com
  test-strategy.md "AS exercita contrato, não driver de mais
  testes". `destination: "external_service"` como valor canônico
  per canonical §4.3 linha 525 + linha 654.

- AS-5 trinque assertion: aplicar 5º setup ao Anchor 1 cobrindo
  MVP scope `not_applicable`. Ids ajustados para diferenciar
  `not_applicable_mismatch` (POL-004) de `not_applicable_mvp_scope`
  (POL-001 + operation: "use").

- Despachar execução final para Code via prompt versionado em vez
  de aplicar direto do Chat. Razão: João explicitou "evito
  substituir arquivo inteiro em cleanup". Solução: `str_replace`
  cirúrgico com 10 pares verbatim, com 2 versões iterativas (v1 +
  v2 pós-review do Code aplicando 5 melhorias).

**Sobre o método (cristalizadas nesta sessão):**

- **Multi-instance review com escalation progressiva** — 6 rounds
  capturaram classes distintas de erros até convergência. Cada
  round consultou fontes diferentes (specs textuais vs YAMLs reais
  vs README do pack vs Pydantic ValidationError emergente vs
  reading adjacent do estado real durante housekeeping).

- **Verificação direta vence inferência (segunda materialização).**
  v1 do prompt T03 errou DD-T03-2 ao inferir do brief; review #1
  do Code leu fixtures + README do pack direto e pegou o bug.
  Pattern reconfirmado em housekeeping: leitura adjacente em
  compact §5.3 linha 376 descobriu site implícito que enumeração
  prévia não tinha capturado.

- **Critério DD emergente vs refinamento tactical.** Alteração do
  set de retornos observáveis pelo caller separa as duas
  categorias. Aplicado em #23: Provenance TypedDict (tactical, sem
  cobertura obrigatória); DefinitionalClause path (emergente,
  cobertura obrigatória via teste).

- **Drift cumulativo é detectado por leitura adjacente ao site de
  edição, não por enumeração prévia.** DD-T03-11 escalou 2 → 3 →
  4 sites em rounds sucessivos. Pattern operacional para
  housekeeping cross-doc.

- **Prompt como artefato auditável.** Versionamento iterativo +
  review independente entre versões é pattern válido para output
  narrativo, não só para código. Materializado em #23 com
  prompt-housekeeping v1 → v2 pós-review do Code.

- **Cirurgia textual via str_replace cirúrgico > substituição de
  arquivo inteiro para cleanup mecânico cross-doc.** Cada `old_str`
  funciona como canary de drift. Aplicável quando cleanup é
  mecânico sem decisões de design.

### Artefatos produzidos

- `prompt-t03-v1.md` (~330 linhas) → `prompt-t03-v2.md` (~430
  linhas, mais detalhado) → `prompt-t03-v3.md` (~430 linhas, mais
  enxuto após recuos calibrados). Versionamento iterativo
  materializa multi-instance review.

- Plano da Fase 1 do Code sancionado em GATE 1 (10 DDs + DD-T03-11
  emergente + canary pre-flight executado).

- `pr-body-t03.md` (~150 linhas) com 12 DDs tabuladas + drifts
  pós-T03 + notas metodológicas.

- PR `feat/policy-reader-check-applicability` mergeada em main via
  squash. Squash hash `<TBD — preencher pós-pull>`. Diff:
  +509/-98 linhas em 6 arquivos:
  - `src/mcp_servers/policy_reader/models.py` (+ `StructuredContext`,
    `VerificationScope`, 4 verdict models, alias `Verdict`).
  - `src/mcp_servers/policy_reader/_envelope.py` (novo módulo;
    7 errorCode builders + `_provenance_from` + 2 vocabulary
    loaders).
  - `src/mcp_servers/policy_reader/tools.py` (`check_applicability`
    público + 4 envelope helpers movidos para `_envelope.py` +
    2 helpers privados de reason template + `_render_verdict_text`).
  - `src/mcp_servers/policy_reader/server.py` (wrapper substituindo
    skeleton stub; assinatura corrigida `dict[str, Any] →
    ToolResult`).
  - `tests/mcp_servers/policy_reader/conftest.py` (fixture estendida
    aditivamente para incluir POL-002).
  - `tests/mcp_servers/policy_reader/test_check_applicability.py`
    (novo; 8 AS com AS-2 split em AS-2a/AS-2b + 2 anchors + 1 teste
    para DD-T03-12).

- 16 testes novos em `test_check_applicability.py` (parametrize
  expandido: 8 funções base + AS-8 ×3 + Anchor 1 ×4 + 1 definitional
  test). Total da suite: 43/43 (27 prévios + 16 novos).

- `prompt-housekeeping-post-t03-v1.md` → `prompt-housekeeping-post-t03-v2.md`
  (~620 linhas, com 10 pares verbatim `str_replace`, pre-flight
  canary, gates pós-edit, PR body draft). v2 incorpora 5 melhorias
  do review do Code: numeração consistente, shell anotado, Edit 2
  splitado em 2a + 2b, canary externo CI/scripts, limitação
  single-line do sanity grep documentada.

### Validações empíricas

- **Gate task-level ADR-0008 §3 cumprido em escala documentada.**
  pytest 43/43 verde; ruff clean; mypy clean (7 source files); Chat
  review independente do diff realizado em sessão de Chat persistente
  com identificação de 2 issues pré-PR (destination ausente,
  DD-T03-12 sem cobertura) — ambos corrigidos antes da abertura do
  PR. Diff coerente com plano sancionado.

- **Multi-instance review trend de convergência em 6 rounds.**
  Severidade dos catches decai monotonicamente:
  - Review #1 (v1 prompt T03, Code clean): 2 materiais alta
    (consent token, StructuredContext ambiguidade).
  - Review #2 (v2 prompt T03, Code clean): 0 materiais; 3 minor
    textuais.
  - Review #3 (v2 prompt T03, Code clean independente): 2
    materiais média (applies_to.operation, isError drift
    tasks.md).
  - Fase 1 (Code): 1 emergente construtiva (drift 1 escalado
    para 3 sítios).
  - Chat review diff (Fase 2.E): 2 materiais (destination,
    DD-T03-12 cobertura).
  - Review prompt-housekeeping v1 (Code clean independente): 5
    observações classes distintas (numeração, shell, bundle
    Edit 2, canary externo, limitação grep).

  Seis rounds, cada um capturando classe distinta de erro.
  Pattern: review independente continua agregando enquanto o
  redator e o reviewer consultarem fontes diferentes. Convergência
  empírica até o ponto onde verificação direta sobre o estado real
  toma lugar de review textual.

- **Pattern "consertar na fonte" vs "workaround no prompt".** Drift
  `isError: true` em tasks.md foi consertado em v1 pinando como
  drift cross-doc residual; recuado em v3 quando se reconheceu que
  Option B está cristalizada em 5 sítios suficientes para o Code
  reconhecer sem pin. Em vez disso, o pin migrou para body do PR
  como item de housekeeping cross-doc pós-T03 (sync tasks.md).
  Materializado: housekeeping executa o sync. Pattern fechado.

- **Verificação direta vence inferência (segunda materialização
  T03 + terceira materialização housekeeping).** v1 do prompt T03
  errou ao inferir o algoritmo de `consent_required` a partir do
  brief; review #1 leu POL-001/POL-004 YAMLs + README do pack
  diretamente e pegou a comparação contra token canônico `consent`.
  Pattern reconfirmado em housekeeping: descoberta de compact §5.3
  linha 376 (4º site do drift 1) durante leitura adjacente, não em
  enumeração prévia. Three-strike rule materializado — pattern
  consolidado para o Capítulo de Método.

- **Chat persistente sustentou 14+ sub-eventos sem fresh entre
  eles.** Maior escala de Chat persistente documentada no projeto.
  Heurística "Chat persistente por tipo de output narrativo"
  formalizada em `session-management.md` confirmada empiricamente
  em escala consideravelmente maior. Critério: o output continua
  sendo narrativo durante housekeeping (decisões, ratificações,
  prompt redação) — não há transição para output verificável que
  exigisse fresh.

- **str_replace cirúrgico viável para cleanup cross-doc mecânico.**
  Aplicado no workspace Chat durante housekeeping para validar os
  5 débitos antes de gerar o prompt para Code. 9 substituições
  (depois 10 no prompt v2 com Edit 2 splitado) executadas sem
  erro; pytest 43/43 mantido; sintaxe Python do test file
  validada via `ast.parse`. Validação empírica de que o pattern
  funciona em escala — não só conceitual.

### Pendências para sessão #24+

**Em execução no momento do fechamento de #23:**

- Code aplicando `prompt-housekeeping-post-t03-v2.md` em branch
  `docs/housekeeping-post-t03` ramificando de main pós-T03. 10
  edits cirúrgicos sequenciais + canary greps pré/pós + gate
  pytest 44/44 esperado (43 prévios + 1 novo do 5º setup do Anchor
  1). Custo estimado: ~30-45min. Após merge, T03-housekeeping
  fechada.

**Resolver em sessão #24 (Chat fresh) — prep prompt T04:**

- T04 entrega `policy://catalog` + `policy://vocabularies` + framework
  swap via vocabulário carregado.
- Pré-leitura consome canonical §3.1 (`policy://catalog`) + §3.3
  (`policy://vocabularies`) + SCHEMA §10.3 (troca de framework) +
  ADR-0005 D3 (vocabulários jurisdicionais) + D4
  (`policy://vocabularies` como surface canônica).
- `_envelope.py` herda naturalmente (additive); `_load_*_vocabulary`
  helpers podem subir para externo se T04 expor via resource.
- Hipótese: T04 introduz `policy://vocabularies` como resource que
  expõe vocabulários jurisdicionais via
  `policy/vocabularies/<framework>/*.yaml`. Cláusulas reais
  hipotéticas para GDPR podem virar fixture de teste de framework
  swap.
- Bonus: canonical §4.3 agora documenta DD-T03-12 (pós-merge do
  housekeeping); prep T04 pode ler §4.3 sem ruído de drift.

**Resolver pós-T04:**

- **Gate milestone-level Milestone A.** Sessão Chat dedicada
  ~1-2h. Manual exercise via MCP Inspector exercitando cada RF de
  `docs/REQUIREMENTS.md` (RFs 004-parcial, 005, 007-parcial,
  008-parcial, 009) usando Tasks T01-T04 implementadas como
  referência operacional. Pré-requisito: T04 fechada.

- **Decomposição formal de Milestone B em sessão Chat dedicada.**
  Após gate milestone-level de A. Decisão Semgrep-on-Windows
  precede.

### Nota de calibração metodológica (defense candidates de #23)

Onze defense candidates consolidados em #23 para o Capítulo de Método
do TCC (sete da primeira metade T03 + quatro novos do housekeeping):

1. **Multi-instance review com escalation progressiva — trend
   empírico de convergência em 6 rounds.** Severidade decai
   monotonicamente até verificação direta sobre o estado real
   tomar lugar de review textual. Pattern: review independente
   continua agregando enquanto o redator e o reviewer consultarem
   fontes diferentes.

2. **DD emergente vs refinamento tactical — critério de
   classificação.** Alteração do set de retornos observáveis pelo
   caller separa as duas categorias. Materializado em #23:
   Provenance TypedDict (tactical, sem cobertura obrigatória);
   DefinitionalClause path (emergente, cobertura obrigatória via
   teste).

3. **Verificação direta vence inferência (terceira materialização
   após #19 e primeira metade #23).** v1 do prompt T03 errou
   DD-T03-2 ao inferir do brief; review #1 do Code leu fixtures +
   README do pack direto e pegou o bug. Housekeeping descobriu 4º
   site do drift 1 em compact §5.3 linha 376 durante leitura
   adjacente. Three-strike rule materializado — pattern: leitura
   textual de spec ≠ leitura direta de fixture; ambas necessárias.

4. **Plan-mode admite refinamento técnico durante execução sem
   voltar ao Chat.** Critério: preserva contrato observável +
   resolve fricção real do toolchain + não introduz coupling novo.
   TypedDict materializa o critério; DefinitionalClause path
   também, mas com cobertura própria por mudar o set de retornos.

5. **`.claude/rules/` carregadas automaticamente reduzem
   boilerplate em prompts subsequentes.** v3 do prompt T03 é ~30%
   menor que v1 porque convoca rules nominalmente em vez de
   re-explicar. Materializa o ganho do housekeeping pré-T03.

6. **Chat persistente sustentando 14+ sub-eventos sem fresh entre
   eles.** Escala consideravelmente maior que #22 (6 sub-eventos)
   e que primeira metade de #23 (7 sub-eventos); pattern por tipo
   de output confirmado em escala documentada.

7. **Cumulative drift discovery via reviews independentes.**
   Compact §5.3 linha 371 como terceiro site de drift 1
   descoberto na Fase 1 do Code; linha 376 como quarto site
   descoberto em housekeeping. Reviewers independentes capturam o
   que o redator não enxerga; cumulativo entre rounds.

8. **Drift cumulativo é detectado por leitura adjacente ao site
   de edição, não por enumeração prévia.** DD-T03-11 escalou
   2 → 3 → 4 sites em rounds sucessivos. Pattern operacional para
   housekeeping cross-doc.

9. **Prompt como artefato auditável com mesma rigor que código.**
   Versionamento iterativo (v1 → v2) com review independente
   entre versões é pattern válido para output narrativo, não só
   para código. Materializado em #23 com prompt-housekeeping v1 →
   v2 pós-review do Code.

10. **Cirurgia textual via str_replace cirúrgico > substituição de
    arquivo inteiro para cleanup mecânico cross-doc.** Cada
    `old_str` funciona como canary de drift. Aplicável quando
    cleanup é mecânico sem decisões de design.

11. **Escolha do mecanismo de edit (substitution vs replacement
    vs patch) é decisão arquitetural, não detalhe operacional.**
    Cada um tem signature de auditabilidade diferente. Aplicado
    explicitamente em housekeeping pós-T03 (str_replace
    cirúrgico) em contraste com substituição de arquivo inteiro
    que João explicitou evitar.

O método deste projeto está se estabilizando suficientemente para
virar contribuição metodológica autônoma do TCC, não só ferramenta
operacional. Capítulo de Método ganha onze defense candidates
empíricos desta sessão, mais o registro de DD emergente (TypedDict
vs DefinitionalClause path) como pattern operacional, mais a
formalização de prompt como artefato auditável.

### Hashes da sessão #23 (audit trail)

Branches mergeadas em main durante #23:

- `<TBD — preencher pós-pull>` — feat(policy-reader): T03 —
  check_applicability with 4-verdict enum, provenance trinque,
  MVP-scope filter (squash de
  `feat/policy-reader-check-applicability`, PR #<TBD>, #23 primeiro
  sub-ciclo).
- `<TBD — preencher pós-merge>` — docs(policy-reader):
  T03-housekeeping — cross-doc cleanup pós-T03 (squash de
  `docs/housekeeping-post-t03`, PR #<TBD>, #23 segundo sub-ciclo —
  em execução no Code no fechamento da sessão Chat).

### Próximo passo

Sessão #24 (Chat fresh) — prep prompt T04 (`policy://catalog` +
`policy://vocabularies` + framework swap). Pré-requisito: merge da
PR T03-housekeeping. Quando housekeeping fechar, canonical §4.3
estará sincronizada (DD-T03-11 sites 1+2 + DD-T03-12 documentada),
compact §5.3 sincronizada (sites 3+4), tasks.md AS-7/AS-8/AS-1
sincronizadas, e Anchor 1 do test estendido com 5º setup. Prep T04
lê §3.1 + §3.3 sem ruído residual.

Custo estimado de T04: ~1-1.5h Chat prep + ~2-3h Code execução.
Menor que T03 — resources são aditivos sobre o existente; sem 4
verdict models nem 6 errorCodes a desenhar; mas DD-T04-2
(`policy://vocabularies` shape: 1 resource vs 4) e framework swap
têm complexidade própria.

# Learning-log entry — sessão #24

**Para aplicar:** apendar este conteúdo ao final de `docs/process/learning-log.md`, abaixo
da última entry existente (#23 close). Seções abaixo são literais — copiar
verbatim, ajustando apenas o hash de squash de T04 quando você fizer `git pull`
após o merge para popular o `<TBD>` no audit trail.

---

## 2026-05-19 — sessão #24 — T04 (`policy://catalog` + `policy://vocabularies` + framework swap) — prep iterativo v1→v2→v3 + GATE 1 + Fase 2 + Chat review + close

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **GATE com condição de halt explícita parametrizada por outcome empírico.**
  v3 do prompt T04 introduziu DD-T04-13 (`policy://catalog` return type
  top-level list vs wrapped dict) como unknown empírico do framework FastMCP
  3.x — anchor wire-shape de T01 cobria apenas `dict` via
  `policy://schema-version`. v3 prescreveu smoke test obrigatório com
  mecanismo operacional concreto (`uv run python -c '...'` ad-hoc, sem
  artefato persistido) em Fase 1.A, com condição de halt explícita: "se
  FastMCP rejeitar top-level list, v4 do prompt antes de Fase 2, NÃO
  improvisar". Resultado: rota A confirmada empiricamente (`OK: [1, 2, 3]`).
  Materializa exam point "escalation patterns" sob ângulo refinado: gates em
  planos precisam de **halt condition explícita parametrizada por outcome**,
  não só de prosseguimento condicional. Defense candidate adicional para o
  Capítulo de Método.

- **DDs emergentes em GATE 1 + débitos emergentes em Chat review pós-Fase 2
  como dois exemplos de pause-and-ask.** Code em GATE 1 apresentou DD-T04-14
  (pattern wire-access alinhado a T01: `server.mcp.read_resource(uri)
  .to_mcp_result(uri)`) + 2 Observações (drift 2 spirit-satisfied via
  disambiguation estrutural; `canonical_examples` mínimo 3 do SCHEMA §5.3
  faltando no stub GDPR proposto) em vez de improvisar. Chat review
  pós-implementação identificou canonical §3.1 sync emergente (shape de
  `article_sources_summary` é Code-decision que merece documentação no
  contrato observável). Ambos materializam o pause-and-ask do plan-mode
  pattern sobre alternativa de improviso silencioso. Pattern recorrente:
  planos sancionados em prep deliberativa absorvem DDs adicionais durante
  leitura direta do código em Fase 1.A, não como falha do prompt, mas como
  GATE funcionando como projetado.

**Domínio 2 — Tool Design & MCP Integration (18%)**

- **Resource vs Tool distinction operacionalizada.** T04 implementa 2
  resources (`policy://catalog`, `policy://vocabularies`); zero novos
  errorCodes em `_envelope.py` porque resources não emitem erros de
  domínio em runtime (canonical §3.1/§3.3 — I/O failures abortam boot,
  Nível 1 MCP detectado no startup). Confirma a separação de surfaces
  registrada em ADR-0005 D4: Classifier consome `policy://vocabularies`
  como contexto léxico (read-only resource) sem ganhar capacidade de
  invocar tools de avaliação (`check_applicability` é exclusivo do
  Matcher). Materializa "MCP tool and resource design — Resources for
  content catalogs, tools for actions" do exam guide.

- **MCP resource semantics: idempotent reads, URI estática, sem
  inputSchema.** AS-3/AS-6 de T04 testam idempotência byte-idêntica sobre
  `result.contents[0].text` (raw JSON string), não sobre dict parsed —
  asserção mais estrita que pega regression hipotética de key reordering
  durante serialização JSON. Pattern wire-access do projeto:
  `server.mcp.read_resource(uri).to_mcp_result(uri)` produzindo
  `TextResourceContents` com `mimeType: "application/json"` explícito
  (espelhado de `policy://schema-version` operacional desde T01).

- **Ausência declarada de system errors em runtime como decisão de
  design.** Canonical §5.4 declara classe `system` vazia: Política
  carregada só no startup, falhas de I/O abortam boot, runtime livre de
  domain errors. Pattern transferível: mover transient failures para um
  momento onde retry é gratuito (startup) e deixar runtime sem casos
  transientes. Resources de T04 herdam o mesmo pattern: erro de I/O em
  `policy://vocabularies` aborta boot, runtime é livre de domain errors.

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- **Path-scoped rule loading via glob frontmatter.**
  `.claude/rules/test-strategy.md` com `paths: "tests/**/*.py"` no
  frontmatter carrega só quando Code edita test files casando o glob;
  economia de contexto cross-cutting sobre file types que CLAUDE.md
  hierárquico não consegue cobrir bem (test files espalhados em múltiplos
  diretórios). Materializa Task Statement 3.3 ("path-specific rules for
  conditional convention loading").

- **Plan-mode + GATE + Fase 2 como deliberação obrigatória para tasks com
  múltiplas DDs.** T04 com 13 DDs sancionadas no GATE 1 + 1 emergente
  (DD-T04-14). Materializa Task Statement 3.4 ("plan mode for tasks with
  multiple design decisions or architectural impact"). Refinamento técnico
  durante Fase 2 admitido sob 3 critérios (preserva contrato + resolve
  fricção real + sem coupling novo); em T04 esse mecanismo NÃO foi
  exercido — a única DD emergente (T04-14) entrou em GATE 1 antes de
  Fase 2, e os 2 Observations também.

- **Rule auto-loading vs disciplina deliberada no Chat — fragility
  observada empiricamente.** Bloqueante v2 do prompt T04 (sub-decisão de
  rename `_format_first_stat_ref` → `_format_stat_ref` violava
  `.claude/rules/git-conventions.md` §"PR sequencing pattern") só foi
  capturado por **Reviewer C, em sessão Code com a rule carregada
  automaticamente em contexto**. Chat tinha a rule no contexto desta
  sessão via anexação manual mas falhou em aplicá-la em deliberation
  quando propôs o rename. Pattern: `.claude/rules/` são auto-aplicáveis
  pelo Code (carregamento automático em qualquer sessão) mas exigem
  disciplina deliberada de invocação no Chat (carregamento manual via
  anexação não é o mesmo que aplicação durante raciocínio). Defense
  candidate metodológico forte: "rules automáticas não substituem
  disciplina deliberada de invocação em prep de prompt".

**Domínio 4 — Prompt Engineering & Structured Output (20%)**

- **Validation-retry loop manual via multi-instance review com 3 rounds.**
  Prompt T04 evoluiu v1 → v2 → v3 com 3 rounds de review:
  - **v1 → v2:** 2 reviewers independentes em sessões Code separadas
    convergiram nos 3 bloqueantes (assinatura de `_format_law_reference`
    quebrava ao receber objeto em vez de 5 posicionais; return type de
    `policy://catalog` list vs dict não-flagado; anchor 2 não realizável
    via fixture filesystem porque loader sorta `clauses_dir.glob()` antes
    de iterar).
  - **v2 → v3:** 1 reviewer (Reviewer C) com `.claude/rules/git-conventions.md`
    carregada automaticamente pegou bloqueante adicional (PR sequencing
    violation no rename embutido em DD-T04-1).
  - **v3 → GATE 1 sancionado.** 13 DDs ratificadas + DD-T04-14 emergente
    + 2 Observations.
  Materializa Task Statement 4.4 ("validation, retry, and feedback loops
  for extraction quality") aplicado ao prompt-as-artifact.

- **Multi-instance review — convergência em itens críticos + divergência
  em refinamentos.** v1 → 2 reviewers convergiram em 3 bloqueantes (alta
  confiança de qualidade). v2 → só 1 reviewer pegou bloqueante novo
  específico do repo (PR sequencing pattern). Refinamentos não-bloqueantes
  divergiram entre reviewers (Reviewer A propôs 3 refinos, Reviewer B
  propôs 5, Reviewer C propôs 6; sobreposição apenas no bloqueante
  comum). Pattern empírico: **convergência em itens críticos é signal
  forte de qualidade**; **divergência em refinamentos é signal de
  cobertura adicional**, não de inconsistência. Refinamento do defense
  candidate #1 do #23 ("multi-instance review com escalation progressiva
  — trend empírico de convergência em 6 rounds") — agora com evidência
  empírica de assimetria entre itens críticos e refinamentos.

**Domínio 5 — Context Management & Reliability (15%)**

- **Smoke test FastMCP como pattern para resolução de unknown empírico
  antes de Fase 2.** DD-T04-13 era unknown empírico — anchor wire-shape
  de T01 cobria apenas dict via `policy://schema-version`. v3 prescreveu
  smoke test obrigatório com mecanismo operacional concreto em Fase 1.A
  + halt condition explícita. Pattern: framework unknown ≠ Code-decision
  durante implementação. Defense candidate metodológico: "halt-pre-fase-2
  evita improviso silencioso quando contrato observável depende de
  comportamento de framework não-coberto por anchors existentes".

- **Verificação direta vence inferência — quinta materialização.**
  Pattern reconfirmado em 4 momentos durante #24:
  - **Reviewer 2 de v1 → v2** leu `tools.py` real e identificou que
    `_format_law_reference(ref)` quebrava — assinatura recebe 5
    posicionais, não objeto. v3 corrigiu para `_format_first_stat_ref(ref)`.
  - **Code em Fase 1.A** leu `loader.py` direto para confirmar que
    `clauses_dir.glob("POL-*.yaml")` é sortado antes de iterar,
    calibrando design do anchor 2 (DD-T04-10 reescrito como unit test
    direto sobre função pura).
  - **Code em GATE 1** leu `test_bootstrap.py:62-67` direto para
    confirmar pattern wire-access `server.mcp.read_resource(uri)
    .to_mcp_result(uri)`, originando DD-T04-14 emergente (prompt v3
    havia prescrito `client.read_resource()` por inferência da API
    genérica de MCP — não era o pattern operacional do projeto).
  - **Chat review pós-implementação** leu `tools.py` para confirmar
    consumo correto de `_format_first_stat_ref` em `get_catalog` e
    identificar drift de canonical §3.1 sync.
  Three-strike rule cristalizada como **pattern recorrente** — rule
  candidate para `.claude/rules/`.

- **Diferimento via §Companion edits cross-doc como pattern operacional
  de scope discipline.** Em T04 exercido 2x:
  - **Antecipado em prep:** rename de `_format_first_stat_ref` é
    "naming inconsistency em helper compartilhado" per
    `.claude/rules/git-conventions.md`; v3 diferiu como débito anotado
    em `docs/tasks.md` §Companion edits cross-doc, despachado em PR de
    housekeeping separada pós-T04 para preservar blame auditability
    per PR. DD-T04-1 simplificada (sub-decisão de rename removida).
  - **Emergente pós-implementação:** canonical §3.1 sync sobre shape de
    `article_sources_summary` identificada por Chat review e anotada
    como 4º item de §Companion edits cross-doc antes do PR T04 ser
    aberto, em commit separado (`1acae30`).
  Materializa `spec-driven-workflow.md` §"Companion edits cross-doc as
  living debt registry" como mecanismo concreto de preservação de
  scope. Defense candidate metodológico: "anotar débito emergente
  imediatamente vs confiar em memória — verificação direta vence
  inferência aplicada a registro de débito".

### Decisões cristalizadas

- **T04 fechada.** PR #46 mergeada em main; commit squash hash
  `<TBD — preencher pós-pull>`. Implementação: +558/-19 linhas em 11
  arquivos (1 commit feat + 1 commit docs annotation).
- **Milestone A task-level completo.** T01-T04 todas fechadas com gate
  task-level (function tests + Chat review independente). Pytest cumulativo:
  53/53 verde (44 herdados T01/T02a/T02b/T03 + 9 novos T04).
- **`tools.py` pós-T04 = 5 funções públicas** (`get_clause`,
  `find_clauses_by_law_article`, `check_applicability`, `get_catalog`,
  `get_vocabularies`). `server.py` puramente decoradores thin wrappers.
- **`_envelope.py` intocado em T04 — tech debt validada por não-promoção.**
  Docstring topo de `_envelope.py` (T03) declarava "reavaliar separação se
  T04 introduzir 3+ helpers não-relacionados a envelope"; T04 confirmou
  empiricamente que o módulo permanece coeso. Validação retroativa da
  decisão de coabitação em #23.
- **`models.py` intocada em T04** — payloads de resource são dict literais,
  não wrappers Pydantic (DD-T04-12). Materializa princípio "Pydantic models
  agregam valor para validação semântica/polimorfismo/contrato externo, não
  para serializações mecânicas".
- **DD-T04-14 (pattern wire-access) como exemplo de DD emergente em GATE 1.**
  Espelha DD-T03-11 emergente em GATE 1 do T03 segundo sub-ciclo. Pattern
  recorrente: planos sancionados em prep deliberativa absorvem DDs
  adicionais durante leitura direta do código em Fase 1.A do Code, antes
  de Fase 2.
- **Smoke test obrigatório com halt condition em Fase 1.A como pattern
  para unknown empírico.** v3 do prompt T04 introduziu o pattern; rota A
  confirmada. Pattern transferível para futuras tasks onde contrato
  observável depende de comportamento de framework não-coberto por anchors
  existentes.
- **Quatro débitos em `docs/tasks.md` §Companion edits cross-doc pós-T04**
  aguardando housekeeping (detalhados em Pendências abaixo).

### Pendências para sessão #25+

**Resolver em sessão Code curta (~1h, não bloqueia gate milestone-level):**

- **Housekeeping cross-doc pós-T04.** 4 débitos em `docs/tasks.md`
  §Companion edits cross-doc:
  1. Sync `docs/process/session-handoff.md` ↔ split Milestone A/B (legado pré-T04).
  2. Sync canonical.md `structured_context` campos + `evidence`/`reason`
     em §4.3 (2 sub-itens legado pré-T04 — `evidence`/`reason` é o drift
     1 do housekeeping pós-T03 que ficou parcial, mais o débito de
     campos do `structured_context` herdado da Fase 1).
  3. Rename `_format_first_stat_ref` → `_format_stat_ref` em `tools.py`
     (3 call sites + 1 novo introduzido por T04; ~7 linhas de
     `str_replace` cirúrgico).
  4. Sync canonical.md §3.1 sobre shape de `article_sources_summary`
     (emergente T04: lista de strings renderizadas via formatter
     compartilhado, uma string por entrada de `statutory_reference`).
  Despacho recomendado: PR única `chore/housekeeping-post-t04`
  consolidando os 4 com commits separados internamente, conforme
  `.claude/rules/git-conventions.md` admite quando "o diff é clean,
  verificável por direct Chat review". Custo: ~1h Code. Alternativa: 4
  PRs separadas — custo ~3-4h, sem yield material adicional.

**Resolver em sessão Chat dedicada (~1-2h):**

- **Gate milestone-level Milestone A.** Manual exercise via MCP
  Inspector contra cada RF declarada em §"RFs/RNFs cobertas no gate
  milestone-level" do Milestone A em `docs/tasks.md`:
  - RF-004-parcial (avaliação de conformidade sobre `collection` —
    entrega end-to-end requer Matcher subagent em Milestone C, mas T03
    entrega motor de veredito + filtro de escopo MVP).
  - RF-005 (veredito `indeterminate` como honestidade epistêmica).
  - RF-007-parcial (composição intra-jurisdição via
    `accepted_law_identifiers` no nível do componente).
  - RF-008-parcial (substituição de framework no nível do componente
    — exercitada por AS-5 de T04 via fixture synthetic_gdpr).
  - RF-009 (provenance temporal e jurisdicional em verdicts).
  Pré-requisito procedural: confirmar MCP Inspector funcional no
  ambiente Windows do João + Política de teste apontando para
  `tests/.../fixtures/synthetic_gdpr/` para exercitar RF-008.

**Resolver pós-gate milestone-level Milestone A:**

- **Decomposição formal de Milestone B em sessão Chat dedicada.**
  Pré-requisito: decisão Semgrep-on-Windows (Docker, pip native, remote
  worker, CI-only) — afeta forma das tasks de Milestone B.
- **Migração de convenções novas (#23-#24) para rules/ADR.** Lista
  cumulativa #23-#24:
  - DD emergente vs tactical (#23) — critério de classificação por
    alteração do set de retornos observáveis pelo caller.
  - Multi-instance review trend (#23, refinado em #24 com assimetria
    convergência crítica vs divergência refinamento).
  - Verificação direta vence inferência — quinta materialização
    cristalizou pattern recorrente (#19, primeira metade #23,
    housekeeping #23, prep #24, Chat review #24).
  - Drift cumulativo via leitura adjacente (#23).
  - Prompt como artefato auditável (#23, refinado em #24 com 3 rounds
    de versionamento v1→v2→v3).
  - Cirurgia textual cleanup (#23).
  - **GATE com halt condition explícita parametrizada por outcome
    empírico (#24)** — novo.
  - **Smoke test pre-Fase 2 para framework unknown empírico (#24)** —
    novo.
  - **Diferimento via §Companion edits como pattern operacional de
    scope discipline (#24)** — novo.
  - **Rule auto-loading vs disciplina deliberada no Chat (#24)** —
    novo, defense candidate metodológico.
  Sessão Chat de housekeeping metodológico pós-Milestone A. Custo
  estimado: ~1h Chat prep + ~30min Code aplicação em ~3 PRs mecânicas.

**Resolver em janela futura sem urgência:**

- **DX residual:** linters (ruff, mypy) como dev deps oficiais em
  `pyproject.toml`. Workaround `uvx ruff` / `uv run --with mypy mypy`
  funciona. Sessão Code curta (~15min) em qualquer janela.

### Hashes da sessão #24 (audit trail)

Branches mergeadas em main durante #24:

- `<TBD — preencher pós-pull>` — feat(policy-reader): T04 — resources
  catalog + vocabularies + framework swap (squash de
  `feat/policy-reader-resources-t04`, PR #46, #24 ciclo Chat persistente
  + sequência de sessões Code: prep iterativo v1→v2→v3, Fase 1.A com
  smoke tests + canary, GATE 1 sancionado, Fase 2 implementação, Chat
  review com débito emergente anotado, push e merge).

Branches abertas para sessão #25+:

- `chore/housekeeping-post-t04` (sessão Code curta) — 4 débitos
  cross-doc consolidados em PR única ou 4 PRs separadas, decisão na
  hora da sessão.

### Onde encontrar detalhes do que #24 cristalizou

- **Prep do prompt T04 — versionamento iterativo:** `prompt-t04-v1.md` →
  `prompt-t04-v2.md` → `prompt-t04-v3.md` (~530 → ~720 → ~720 linhas;
  iteração materializa multi-instance review e prompt-as-artifact).
  Artefatos auditáveis preservados em histórico Chat de #24.
- **Plano da Fase 1 do Code sancionado em GATE 1:** preservado no
  histórico Chat de #24. 13 DDs originais + DD-T04-14 emergente + 2
  Observations (drift 2 spirit-satisfied, canonical_examples mínimo 3).
- **Body do PR T04:** preservado no histórico Chat de #24 com tabela
  das 14 DDs ratificadas + gate outputs + 3 débitos anotados em
  §Companion edits cross-doc (depois 4 com adição do canonical §3.1
  sync via commit `1acae30`).
- **Detalhamento metodológico:** este entry — defense candidates #24.
- **Implementação T04:** +558/-19 linhas em 11 arquivos.

### Nota de calibração metodológica (defense candidates de #24)

Cinco defense candidates novos consolidados em #24 para o Capítulo de
Método do TCC:

1. **Validation-retry loop manual via multi-instance review com 3 rounds
   — convergência empírica em bloqueantes críticos, divergência em
   refinamentos.** v1 → 2 reviewers convergiram em 3 bloqueantes; v2 →
   1 reviewer (Code com rule carregada automaticamente) pegou bloqueante
   adicional específico do repo; v3 → sancionado em GATE 1. Pattern:
   convergência em itens críticos é signal forte de qualidade;
   divergência em refinamentos é signal de cobertura adicional, não de
   inconsistência. Refinamento empírico do defense candidate #1 do #23.

2. **GATE com condição de halt explícita parametrizada por outcome
   empírico (smoke test).** v3 do prompt T04 introduziu DD-T04-13 com
   smoke test FastMCP obrigatório em Fase 1.A + halt condition explícita
   ("se rejeitar, v4 antes de Fase 2"). Pattern: gates em planos precisam
   de halt explícito quando contrato observável depende de comportamento
   de framework não-coberto por anchors existentes.

3. **Rule auto-loading vs disciplina deliberada no Chat — fragility
   observada empiricamente.** Bloqueante v2 (PR sequencing violation no
   rename) só foi capturado por Reviewer C com `git-conventions.md`
   carregada automaticamente em sessão Code. Chat tinha a rule via
   anexação manual mas falhou em aplicá-la em deliberation. Pattern:
   `.claude/rules/` são auto-aplicáveis pelo Code mas exigem disciplina
   deliberada de invocação no Chat para evitar gap.

4. **Diferimento via §Companion edits cross-doc como pattern operacional
   de scope discipline.** Em T04 exercido 2x: rename antecipado em prep
   (DD-T04-1 simplificada via diferimento); canonical §3.1 sync emergente
   em Chat review pós-implementação. Materializa
   `spec-driven-workflow.md` §"Companion edits cross-doc as living debt
   registry" como mecanismo concreto de preservação de scope.

5. **Verificação direta vence inferência — quinta materialização
   documentada cristaliza pattern recorrente.** Pattern reconfirmado em
   4 momentos durante #24: leitura de helper real (Reviewer 2 v1→v2),
   leitura do loader (Code Fase 1.A para anchor 2), leitura de
   test_bootstrap (Code GATE 1 para DD-T04-14 emergente), leitura de
   tools.py (Chat review pós-implementação). Rule candidate para
   `.claude/rules/` — promoção formal pendente em housekeeping
   metodológico pós-Milestone A.

### Próximo passo

Sessão #25 — duas alternativas válidas:

**Alternativa A (recomendada):** Chat fresh dedicada ~1-2h para **gate
milestone-level de Milestone A** via MCP Inspector contra RFs 004-parcial
/ 005 / 007-parcial / 008-parcial / 009. Pré-requisito procedural:
confirmar MCP Inspector funcional no ambiente Windows do João. Pode
descobrir débitos adicionais durante manual exercise que merecem entrar
no housekeeping antes de Milestone B.

**Alternativa B:** Code curta ~1h para housekeeping cross-doc
consolidando os 4 débitos em PR única `chore/housekeeping-post-t04` (ou
4 PRs separadas, decisão na hora). Limpa débito de prep antes de
exercitar funcionalmente.

Ordem recomendada A → B porque gate milestone-level pode revelar
débitos adicionais que entram no housekeeping consolidado. Mas B → A é
também válido se você preferir entrar no gate com workspace limpo de
débitos cosméticos. Decisão na hora.

## #25 — 2026-05-19 — Finalização Milestone A: gate milestone-level + housekeeping completa

**Escopo da sessão.** Sessão única consolidando duas atividades inicialmente previstas como #25 (gate) + #26 (housekeeping): gate milestone-level Milestone A via MCP Inspector + PR #47 `chore/housekeeping-post-t04` com 8 débitos consolidados + smoke test pós-merge validando fix #8 em runtime. Encerra Milestone A em todos os níveis (task-level + milestone-level).

**Conceitos da prova exercitados.**

*Domínio 1 — Agentic Architecture (parcial).* Dependency injection via env var no momento de spawn do servidor MCP (`POLICY_READER_ROOT` apontando para Política diferente entre LGPD e GDPR). Equivalente conceitual ao pattern "explicit context passing" cobrado em D1 para subagent context management, aplicado aqui ao nível de processo MCP.

*Domínio 2 — Tool Design & MCP Integration.* Exercitado de forma intensiva: leitura de tool descriptions como o cliente LLM vê (`tools/list`), inspeção de `ReadResourceResult` vs `CallToolResult` shape, distinção semântica tool (verbo, ação, com efeito) vs resource (substantivo, dado, idempotente), MCP Inspector CLI mode como padrão idiomático para CI, env var no `.mcp.json` equivalente como mecanismo de configuração. 4 dos 8 débitos da PR caíram diretamente em D2 (resource names, structuredContent casing, matching scope clarification, tool description quality).

*Domínio 3 — Claude Code Configuration & Workflows.* CLI mode do MCP Inspector análogo ao `claude -p --output-format json` cobrado em D3 — spawn ephemeral, JSON stdout, exit, comando reproduzível. Pattern de gate documentado como sequência de comandos auditáveis.

*Domínio 4 — Prompt Engineering & Structured Output.* Validação contra os 4 vereditos enumerados de `check_applicability` (compliant, violation_candidate, indeterminate, not_applicable) + 2 erros estruturados (CLAUSE_DEPRECATED retryable, INVALID_LAW_IDENTIFIER non-retryable). Cada veredito carrega campo discriminador exclusivo (evidence vs reason vs verification_scope vs contradicted_requirement), exemplificando structured output com discriminator. `text` em `content[0]` como renderização redundante do `structuredContent` para cliente LLM sem capacidade de parsing programático — pattern de "two consumers, one payload".

*Domínio 5 — Context Management & Reliability.* Taxonomia empírica de erros consolidada: wire/schema error (Pydantic, isError true, texto livre) vs domain error non-retryable (INVALID_LAW_IDENTIFIER, envelope estruturado, isRetryable false) vs domain error retryable (CLAUSE_DEPRECATED, envelope com details.successors, isRetryable true). Provenance trinque `(policy_schema_version, policy_version, legal_framework)` em todos os 6 vereditos exercitados. Provenance arquitetural adicional (`reason` citando ADR-0007 D3) — duas camadas de auditabilidade.

**Decisões tomadas.**

- Pivô **MCP Inspector UI → CLI mode** no meio da Fase A.2 (UI v0.21.2 com bug de UX: clicar item de resource não dispara `resources/read`). CLI mode revelou-se superior para gate auditável: spawn ephemeral, JSON puro, comandos arquiváveis como evidência. Decisão aplicada para todo o resto do gate e validada em retrospectiva como melhor para reprodutibilidade defensiva no TCC.
- Caminho **(a) — copiar POL-001..POL-004 para `policy/clauses/` temporariamente** em vez de montar Política standalone separada para exercitar `check_applicability`. Mais rápido (~10s) que opção (b) ou (c); revertido ao final via `Remove-Item` + verificação `git status` clean.
- **Ordem A→B confirmada** (gate antes de housekeeping) — gate emergiu 4 débitos novos (#5-#8); housekeeping consolidou os 8 ao final, evitando segunda PR de cleanup.
- **Atomicidade ADR-0003** preservada — commit 2 do PR #47 sincroniza canonical.md + compact.md examples no mesmo commit que o fix de impl (`_format_law_reference`), respeitando paridade canonical↔compact.
- **session-handoff.md mantido como diff-log meta-document** — pattern inaugurado em #24 (com blocos editáveis em code-blocks markdown) consolidado em #25; refactor para handoff plano deferido como custo sem yield claro.
- **PowerShell 5.1 + UTF-8 sem BOM via `[System.IO.File]::WriteAllText(..., UTF8Encoding $false)`** — `Out-File -Encoding utf8` injeta BOM em PS 5.1 nativo; pattern correto para subjects de commit em UTF-8.

**Artefatos produzidos.**

- `docs/process/milestoneA.md` — gate report Milestone A (5 RFs ancoradas empiricamente, 5 fases A.1-A.5 documentadas, 8 débitos enumerados, insumo metodológico). Commit 6 da PR #47.
- PR #47 `chore/housekeeping-post-t04` — 7 commits internos, pytest 53/53 verde em cada commit individualmente, 8 débitos consolidados, §Companion edits cross-doc esvaziado.
- `docs/specs/policy-reader/canonical.md` §3.1 + §4.3 sync (shape `article_sources_summary`, 4 campos de `StructuredContext`, discriminação evidence/reason/verification_scope).
- `docs/specs/policy-reader/canonical.md` §4.1/§4.2/§4.3 + `docs/specs/policy-reader/compact.md` §5.2/§5.3 — examples renderizados sincronizados com fix de ordinal condicional.
- `src/mcp_servers/policy_reader/tools.py` — `_format_first_stat_ref` → `_format_stat_ref` (rename semântico); `_format_law_reference` corrigido para ordinal condicional N≤9.
- `src/mcp_servers/policy_reader/server.py` — 3 decorators `@mcp.resource` com `name=` explícito (Policy Clause Catalog / Jurisdictional Vocabularies / Policy Schema Handshake); 2 typos corrigidos em docstring de `check_applicability` (`structured_content` → `structuredContent`); 1 clarificação adicionada em docstring de `find_clauses_by_law_article` (matching scope top-level apenas).

**Defense candidates emergentes (cumulativos a migrar para `.claude/rules/` ou ADR em sessão metodológica pós-Milestone A).**

- **Gate manual exercise produz débito que automated test não pega.** Empirizado: 4 débitos #5-#8 descobertos em #25 contra 53/53 pytest verde pré-gate. Confirma decisão ADR-0008 amended (separação task-level vs milestone-level).
- **CLI mode supera UI quando reproducibilidade é critério.** Empirizado pelo pivô no meio do gate. Gate como sequência de comandos arquiváveis vs cliques perdidos no tempo. Defense candidate forte para Capítulo de Método do TCC.
- **Multi-instance review escala via complementaridade de trajetória de leitura.** Empirizado em 5 instâncias independentes sobre o prompt do Code em 3 iterações (v1→v2→v3→v4): 10 achados não-triviais disjuntos detectados. Cada instância nova percorreu trajetória diferente (review-T04 = contexto vivido, review-clean = rigor procedural, review-2-models = auditoria semântica de models.py, review-2-canonical = canonical examples, review-3-compact = paridade canonical↔compact). Cobertura conjunta dominou cobertura individual. Refinamento do pattern de #23-#24 ("convergência crítica vs divergência refinamento") para nova dimensão: **direcionar reviewers para fatiamentos diferentes do mesmo artefato escala mais que N instâncias indiferenciadas**.
- **Verificação direta vence inferência — sexta materialização.** Materializada novamente nesta sessão: (a) inferi structure do repositório do handoff sem listar (paths errados); (b) inferi 3 campos de `StructuredContext` em vez de pedir `models.py` — review pegou o 4º campo (`destination`); (c) confiei em memória de bordas de docstring sem ler — review pegou typo de `structured_content` em 2 lugares. Pattern operacional consolidado: **ler antes de inferir, em todas as etapas**.
- **Atomicidade de débito atravessa paridade de specs (operacionalização ADR-0003).** Quando débito afeta documentação em arquivos com paridade prescrita, sync deve ocorrer no mesmo commit que a impl. Sair sem o sync introduz drift novo na própria PR que existia para fechar drift.
- **session-handoff.md como diff-log meta-document — pattern consolidado.** Inaugurado #24, replicado #25 sem fricção. Diff blocks aplicáveis em code-blocks markdown preservam blame-traceability cross-sessão. Vale tornar explícito num `.claude/rules/session-handoff-format.md` ou ADR breve.
- **PowerShell 5.1 + UTF-8 puro para commit messages.** `Out-File -Encoding utf8` injeta BOM em PS 5.1 nativo (comportamento corrigido apenas em PS 7+ com `utf8NoBOM`). Pattern correto: `[System.IO.File]::WriteAllText($path, $body, [System.Text.UTF8Encoding]::new($false))`. Vale virar nota em `.claude/rules/windows-tooling.md` ou similar.

**Débitos resolvidos nesta sessão (mergeados via PR #47).**

8 débitos consolidados:
1. Sync session-handoff.md ↔ split Milestone A/B (pré-existente)
2. Sync canonical.md §4.3 `structured_context` + `evidence`/`reason`/`verification_scope` (pré-existente)
3. Rename `_format_first_stat_ref` → `_format_stat_ref` (pré-existente)
4. Sync canonical.md §3.1 shape de `article_sources_summary` (pré-existente)
5. Explicit `name=` em decorators de resource (emergente do gate)
6. `structured_content` casing em docstring de `check_applicability` (emergente do gate)
7. Matching scope clarification em docstring de `find_clauses_by_law_article` (emergente do gate)
8. Ordinal condicional `º` apenas para artigos/parágrafos ≤9 + sync canonical/compact examples (emergente do gate, jurídico-defensivo)

**Métricas operacionais.**

- pytest cumulativo: 53/53 verde antes e depois da PR; verde em cada commit individual da PR
- Cobertura RFs Milestone A: 5/5 ancoradas empiricamente (RF-004-parcial, RF-005, RF-007-parcial, RF-008-parcial, RF-009)
- §Companion edits cross-doc em tasks.md: esvaziado (4 bullets removidos cumulativamente nos commits 5 e 7)
- Smoke test pós-merge: POL-002 catalog rendering `"LGPD Art. 12, §2º"` confirmado (cardinal no 12, ordinal preservado no §2) — fix #8 validado end-to-end

**Próximo passo.**

Sessão #26 Chat dedicada. Dois temas independentes (ordem A→B recomendada):

A. **Migração de defense candidates cumulativos para `.claude/rules/` e/ou ADRs breves** — 11 candidates acumulados de #19-#24 + 7 novos de #25 = 18 candidates totais. Sessão metodológica retrospectiva ~1h Chat + ~30min Code aplicando em PRs mecânicas.

B. **Decomposição formal de Milestone B em Chat dedicada.** Pré-requisito procedural: **decisão Semgrep-on-Windows precede** (Docker, pip native, remote worker, CI-only) — afeta forma das tasks de Milestone B. ~1-1.5h Chat se decisão Semgrep já tomada; +30min se precisar decidir antes.

Não-bloqueio: A pode rodar antes de B sem custo; B requer Semgrep decision precedendo.

## #27 — 2026-05-21 — Autoria formal de Milestone B em Chat dedicada

**Escopo da sessão.** Sessão Chat dedicada decompondo Milestone B em Provisões A+B (pré-implementação) + tasks T05/T06/T07 (implementação) + gate milestone-level (placeholder), conforme governance ADR-0008 amended. Resultado materializado em diff aplicável de 4 blocos para `docs/tasks.md`; aplicação via PR mecânica subsequente. Sessão também resolveu 2 achados load-bearing do Chat review independente pós-aplicação dos blocos.

**Conceitos da prova exercitados.**

*Domínio 1 — Agentic Architecture & Orchestration.* D1.6 task decomposition aplicada a um segundo milestone, replicando padrão calibrado em ADR-0008 §1 (1-3h por task, 8-12 tasks agrupadas em milestones). Boundary deliberada entre Provisão A (canonical-sync-C + compact sync + README + ADR-0001 amendment, consolidados) vs Provisão B (fixture pack BR, independente) vs T05 (skeleton+loader, sem fricção bloqueante) vs T06 (scan_diff mechanics completo) vs T07 (content layer: six BR recognizers). Padrão "mechanics vs content" análogo a Milestone A (T01 loader + T02-T04 mechanics + POL-001..004 pack content). D1.7 session state management: close limpo desta sessão Chat com diff aplicável endereçável + handoff explicitando próximas trilhas independentes.

*Domínio 2 — Tool Design & MCP Integration.* D2 Resource vs Tool exercitado como caso-teste empírico: semgrep-runner expõe APENAS tool (`scan_diff`), zero resources, em assimetria deliberada vs policy-reader (3+3). Princípio "rule set é insumo interno do server, não conteúdo navegável pelo caller" materializa o critério de discriminação. D2 isError flag + Option B amendment + empty error class: drift sistêmico canonical/compact detectado em #27 (4 vs 6 errorCodes, classes erradas, retryability invertida, runtime vs startup do BINARY_UNAVAILABLE, wire format pre-amendment) — Provisão A cobre o sync cirúrgico. D2 tool description quality: T05 AS-7 valida que description em `list_tools` é byte-idêntica ao texto canonical §4.2.

*Domínio 3 — Claude Code Configuration & Workflows.* D3 `.claude/rules/` como contrato decisional consumível em runtime de implementação: referência nominal a `windows-tooling.md` (T06 gate Chat review), `mcp-testing.md` (T05 gate), `privacy-safety.md` (T07 gate + Provisão B), `verification-before-inference.md` (todos os gates) como pontos onde Code deve consultar a rule durante a sessão. Rules consolidadas em #26 ganham segunda materialização em #27 sem fricção.

*Domínio 5 — Context Management & Reliability.* D5 Provenance via citation chain preservada: REQUIREMENTS.md (RF-001, RF-002) → Milestone B (capability) → T05-T07 (tasks) → commits futuros. D5 Error propagation: 6 errorCodes do canonical §5 com retryability discriminada por classe (business non-retryable em GIT_REF_NOT_FOUND/INSUFFICIENT_GIT_HISTORY; system retryable em SCAN_TIMEOUT/SEMGREP_EXECUTION_FAILED; system non-retryable em SEMGREP_BINARY_UNAVAILABLE/INVALID_RULE_SET). D5 escalation pattern aplicado em estilo Chat: cinco drifts load-bearing detectados via leitura cruzada de docs autoritativos (canonical, compact, ADR-0002, ADR-0003, loader.py, uv.lock) — escalation honesta de "não posso inferir, preciso ler" forçou descoberta em vez de propagação silenciosa para tasks.

**Decisões tomadas.**

- **Milestone B = Provisões A+B + T05+T06+T07 + gate milestone-level.** Estrutura ratificada após deliberação 4-rounds entre Chat e usuário. Custo estimado ~13-14h totais (~5h pré-implementação + ~6.5-7.5h implementação + ~1h gate).
- **Python only no MVP, JS adiado para janela 15/06-30/06** (entre entrega e defesa). RF-001 declara linguagem parametrizável pelo rule set; provar arquitetura em uma linguagem é suficiente; demonstração empírica em segunda linguagem é evolução opcional fortalecendo narrativa defensiva sem inflar escopo do MVP. ~6-7h estimadas para JS pós-MVP, registradas em §"Pós-Milestone B aberto" do tasks.md.
- **`rules_version` = hash determinístico do diretório `rules/`.** Decisão fechada em T05 entre as três alternativas listadas em canonical §6 (hash, semver manual, combinação). Hash é mais simples, sem manutenção manual, alinha com pattern de constantes hardcoded em `policy_reader/loader.py` (`_VOCABULARY_FILES` é fixo no design).
- **T06 unificada (não split T06a/T06b).** 13 ASes, ~3h estimado, borda superior do range ADR-0008 §1, com nota explícita. Split artificial deixaria scan_diff em estado intermediário ruim — happy path implementado e error envelope pendente significaria caminho de erro accidental que T06b precisaria refatorar.
- **canonical-sync-C escopo: cirúrgico, não re-derivação total.** ADR-0003 Decision 1 prescreve paridade restrita a contract surfaces (tool descriptions, output schemas, error codes, anti-uses, when-to-use guidance), não prose. Compact sync atinge contract surfaces drifted; prose intacta. Reduz custo da Provisão A de re-derivação total (~2.5h) para sync cirúrgico (~2h Chat + ~1.5h Code = ~3.5h).
- **ADR-0001 Decision 2 amendment in-place, não sucessor.** Espelha pattern de ADR-0008 (2026-05-16). Decision 2 original foi authorada como sugestão de stack ainda sem deliberação técnica (canonical package recomendado, não decisão deliberada); pivô Presidio→Semgrep e pins reais (`uv.lock`: FastMCP 3.2.4, Pydantic 2.13.4, MCP 1.27.1) emergiram durante implementação e nunca foram amended. Companion edit dentro do próprio ADR.
- **Provisão A consolidada em PR única com 4 commits internos** (canonical sync + compact sync + README pin + ADR-0001 amendment), conforme `.claude/rules/git-conventions.md` admite quando diff é clean e Chat-revisable. Bloqueia T06; não bloqueia T05.
- **Provisão B como PR independente** (fixture pack BR). Não bloqueia T05 nem T06 (ambos usam placeholder rule de T05); bloqueia T07. Análogo ao pack POL-001..004 de Milestone A em estrutura e governance.

**Artefatos produzidos.**

- `docs/tasks.md` reescrito (237 → 414 linhas; +177 linhas líquidas): §Status atualizado para refletir #25 close + #27 authoring; §Milestone B novo com Capacidade entregue + RFs cobertas + Gate milestone-level placeholder + Pré-implementação (Provisões A e B) + T05/T06/T07 completas; §Companion edits cross-doc reorganizado em "consolidados em Provisão A" + "resolver pós-T07"; §Pós-Milestone B aberto novo (pendência JS); §Milestones C, D — autoria deferida atualizada (B removido da lista).
- Diff aplicável de 4 blocos posteriormente materializado em PR mecânica `docs/tasks-milestone-b-decomposition` (Code ~30-40min).
- Chat review independente pós-aplicação produziu 2 achados load-bearing: typo aspas em §Status header (linha 3) + §Source-of-truth desatualizada (linha 7 não incluía `docs/specs/semgrep-runner/`). Ambos cosméticos no esforço de fix mas load-bearing na consistência.

**Defense candidates emergentes (cumulativos a migrar para `.claude/rules/` ou ADR breve em sessão metodológica futura).**

- **Sessão de autoria de novo milestone é gatilho natural para sweep de drift em documentação adjacente.** Empirizado em #27: cinco drifts load-bearing detectados que sessões anteriores (#21+) não capturaram — quatro no contract surface canonical/compact do semgrep-runner (errorCodes, classes, retryability, BINARY_UNAVAILABLE timing) + um fundacional em ADR-0001 (Presidio→Semgrep + pins de stack). Pattern: drift se acumula linearmente em silos não-revisitados, em proporção à atividade não-tocada na superfície. Defense candidate forte para Capítulo de Método.
- **uv.lock como fonte autoritativa secundária para reconciliar ADRs de stack.** Empirizado em #27: grep direto do `uv.lock` confirmou pins reais (FastMCP 3.2.4, Pydantic 2.13.4, MCP 1.27.1) e ausência de Presidio. Reconciliou ADR-0001 (sugestão de stack pré-deliberação) com realidade implementada. Pattern: para qualquer ADR que cita stack, `uv.lock` é evidence pack auditável; drift entre ADR e `uv.lock` é débito fundacional que merece amendment in-place quando emergente. Materialização: nota em `.claude/rules/spec-driven-workflow.md` ou em nova rule `adr-stack-reconciliation.md`.
- **Headers metadocumentais (Source-of-truth, Status, Convenção de IDs) drifta junto com autoria de conteúdo novo.** Achado do Chat review #27: §Source-of-truth continuou apontando apenas para `docs/specs/policy-reader/` mesmo após autoria de Milestone B introduzir referências ativas a `docs/specs/semgrep-runner/`. Pattern: blocos de cabeçalho escapam da varredura quando o foco de autoria está em conteúdo novo. Sweep explícito de headers como item final de qualquer sessão de autoria de milestone — materialização em `.claude/rules/spec-driven-workflow.md` ou check-list de close.
- **Sync cirúrgico vs re-derivação total em paridade canonical↔compact: escolha governada por ADR-0003 Decision 1.** Empirizado em #27: drift sistêmico detectado no compact poderia justificar re-derivação total, mas ADR-0003 prescreve paridade restrita a contract surfaces (não prose), tornando sync cirúrgico a operação correta. Pattern: extensão da operação de sync vinculada ao tipo de drift (contract vs prose), não à severidade aparente. Materialização: nota em `.claude/rules/spec-driven-workflow.md`.

**Métricas operacionais.**

- Documentos consultados/lidos diretamente na sessão: 15 (canonical+compact do semgrep-runner; tasks.md; REQUIREMENTS.md; architecture-overview.md §4.2+§4.4+§5.3; ADR-0001, ADR-0002 §3 amendment, ADR-0003, ADR-0008, ADR-0010; loader.py do policy-reader; server.py do policy-reader; uv.lock — grep; pack POL-001..004 + README do pack; print de listagem de .claude/rules/).
- Drifts load-bearing detectados via verificação direta: 5 (4 contract surface canonical/compact + 1 fundacional ADR-0001).
- Tamanho final de tasks.md: 414 linhas (de 237; +177 líquidas para Milestone B).
- Estimativa de custo Milestone B: ~13-14h totais; comparable a Milestone A (10-14h declaradas em #18).
- Chat review pós-autoria: 2 achados load-bearing, 0 substantivos estruturais. Fix time ~1 min combinado.

**Próximo passo.**

Trilhas independentes a partir desta sessão #27 fechada. Ordem natural: PR mecânica primeiro (cristaliza o plano), Provisão A e Provisão B em paralelo (Chat dedicadas), T05 destrava após PR mecânica fechar.

A. **PR mecânica `docs/tasks-milestone-b-decomposition`.** Sessão Code curta (~30-40min) aplicando os 4 fixes do Chat review pós-autoria (typo aspas Status + sync §Source-of-truth) + integração final dos 4 blocos do diff aplicável. Não bloqueia T05 mas deve fechar primeiro para cristalizar referência.

B. **Provisão A — `chore/canonical-sync-C-semgrep-runner` em sessão Chat dedicada (~3.5h total).** Deliberação dos 4 commits internos: canonical sync (Option B amendment §3 + §6/§8.6 alignment + §5.1 título se ainda drifted); compact sync cirúrgico (errorCodes, classes, retryability, BINARY_UNAVAILABLE timing, wire format); README pin Semgrep; ADR-0001 Decision 2 amendment in-place (stack real: Semgrep+FastMCP 3.2.4+Pydantic 2.13.4+MCP 1.27.1). **Bloqueia T06.**

C. **Provisão B — `feat/fixtures/recognizers-pack-br` em sessão Chat dedicada (~2-2.5h total).** Deliberação dos snippets/padrões + redação dos seis snippets positivos + negativos + README. Não bloqueia T05 nem T06.

D. **T05 (Code, ~1.5-2h)** — server skeleton + rule set loader. Destrava após (A) fechar.

E. **T06 (Code, ~3h)** — `scan_diff` completo. Destrava após (D) done + (B) mergeada.

F. **T07 (Code, ~2-2.5h)** — six recognizers brasileiros. Destrava após (E) done + (C) mergeada.

G. **Gate milestone-level Milestone B (Chat dedicada, ~1h)** — manual exercise via MCP Inspector contra RF-001 + RF-002. Destrava após T05-T07 fecharem gate task-level.

## #28 — 2026-05-21 — Fechamento das Provisões A+B de Milestone B + multi-round Code review como independent evaluator iterativo

**Escopo da sessão.** Sessão Chat dedicada de longa duração (~6h Chat efetiva + ~2h Code efetiva, distribuídas em janela de ~24h) que fechou as duas Provisões pré-implementação de Milestone B: (i) Provisão A — PR `chore/canonical-sync-C-semgrep-runner`, sync cirúrgico cobrindo cinco drifts catalogados em #27 (errorCodes count, classes, retryability, BINARY_UNAVAILABLE timing, wire format pre-amendment) + um drift fundacional (ADR-0001 stack pre-Presidio/Semgrep pivot) + três drifts emergentes detectados em prep Chat (compact §5.3/§5.4 escalation pointers órfãos, `files_scanned_before_timeout` fora do schema, atribuição cross-doc imprecisa em tasks.md:236) + um drift cross-doc detectado em Code review round 2 (CLAUDE.md §Stack ainda citando Presidio) + dois drifts laterais detectados em Code review round 3 (CLAUDE.md Pydantic 2.5+ e FastMCP 3.x sem pins) + um drift residual descoberto durante aplicação (compact §5.1 Errors list — Edit 2.7 cirúrgico aprovado em sessão); (ii) Provisão B — PR `feat/fixtures/recognizers-pack-br`, fixture pack BR com 10 creates (6 snippets positivos Latin square + 3 snippets negativos AS-7 + README). Sessão exercitou pela primeira vez no projeto o pattern de multi-round Code review independente em contexto clean como gate iterativo pré-aplicação (três rounds para Provisão A + uma rodada para Provisão B), com convergência empirizada.

**Conceitos da prova exercitados.**

*Domínio 1 — Agentic Architecture & Orchestration.* D1.5 close limpo de sessão Chat replicado em ciclo completo: prep Chat → artefato endereçável (`.md` exportado para outputs) → multi-round Code review → sessão Code de aplicação com pause-and-ask em achado emergente → ratificação Chat → push + squash-merge. Pattern análogo a session resumption via `--resume`, mas materializado via artefato exportável em vez de session-id MCP nativo. D1.6 task boundaries observadas: Provisão A consolidou cinco débitos cross-doc em PR única com 5 commits internos pre-squash (auditability per logical change durante Chat review); Provisão B materializou como single commit consolidando 10 creates (sem decomposition porque é creation coeso). Padrão "PR única com N commits internos" admitido por `.claude/rules/git-conventions.md` quando diff é clean e Chat-revisado — explicitação na PR description preserva audit trail pós-squash.

*Domínio 2 — Tool Design & MCP Integration.* D2 isError flag + Option B propagation: propagação completa do amendment §3 do ADR-0002 (2026-05-17) para o `semgrep-runner` em quatro pontos do canonical (§4.2 wire format intro + §4.3 exemplos + §5 intro + §8.5 acceptance criteria) e em três pontos do compact (§3 cabeçalho + §3 error payload shape + §5.1 exemplo timeout). Decisão central da propagação: wire `isError: false` em TODOS os retornos do componente (sucesso + empty result + erros de domínio); discriminação semântica por presença do campo `errorCode` em `structuredContent`; wire `isError: true` reservado para falhas de protocolo emitidas pelo FastMCP (input rejeitado por `inputSchema`, tool inexistente, transport-level errors). Limitação técnica herdada do FastMCP 3.2.4 confirmada empiricamente em sessão #20 via leitura direta de `fastmcp/tools/base.py`; `semgrep-runner` herda exatamente como `policy-reader` porque ambos usam FastMCP. D2 three-class error contract realinhado: errorCodes 4→6, classes validation+system→business+system (validation vazia declarada positivamente per ADR-0002 Decision 4), retryability discriminada por classe. D2 positive declaration of empty error class refinada: validation class vazia neste componente é endereçada não como omissão, mas como "rejection pelo runtime FastMCP via `inputSchema` ANTES de chegar ao componente — essa rejeição emite wire `isError: true` per a reserva acima, não erro de domínio classe validation". D2 framework-vs-spec adaptation: exercício prático da decisão "MCP spec documenta `isError: true` + `structuredContent`, mas FastMCP 3.2.4 não expõe o caminho público — relinquir wire discriminator, manter envelope shape, discriminação por `errorCode` presence". Defense candidate forte para Capítulo de Discussão do TCC.

*Domínio 3 — Claude Code Configuration & Workflows.* D3 CLAUDE.md hierarchy + governance: edit cirúrgico em CLAUDE.md (Commit 5 da Provisão A) materializa sync do file auto-loaded por toda sessão Claude Code, com cuidado especial reconhecido ("edits aqui pedem cuidado explícito"). Ciclo de provenance fechado: ADR é decisão; CLAUDE.md é instrução operacional; sync periódica é o invariante que mantém os dois alinhados. D3 ADR amendment in-place pattern espelhado de ADR-0008 (amended 2026-05-16) em ADR-0001 Decision 2: Status line ganha sufixo "amended in-place YYYY-MM-DD" + nova seção `## Amendment scope (data)` declarando o que foi amended + texto original substituído (não preserva original side-by-side; só registra que houve amendment com rationale). D3 `.claude/rules/` como contrato decisional: `privacy-safety.md` (always-loaded, sem `paths` frontmatter) consumido durante autoring do pack BR enforçando invariante de PII sintética cross-session; `git-conventions.md` consumido em raciocínio sobre squash-merge vs commits internos; `windows-tooling.md` referenciado para padrões de subprocess em PS 5.1 (T06 future).

*Domínio 4 — Prompt Engineering & Structured Output.* D4 validation-retry loops aplicado explicitamente: validation criteria (grep checks por commit) como gates auto-verificáveis sobre o substitute_by, exercitando o pattern de structured output validation antes de proceder. Empirizado em Provisão A: gate auto-verificável detectou divergência entre Edit 2.7 (escopo emergente em sessão Code) e tabela de erros esperados, forçando pause-and-ask + decisão Chat + retake do gate. D4 multi-instance review pattern materializado em cinco rodadas independentes (Code review rounds 1+2+3 para Provisão A, Code review pré-aplicação para Provisão B, Code application como reviewer final). Cada round em contexto clean do repositório, atingindo ground truth que single-instance self-review não atinge. Empirizado: round 1 detectou B1 (paths errados) + B2 (canonical §5 órfã) + 3 médios; round 2 detectou R1 (CLAUDE.md Presidio drift); round 3 detectou Pydantic e FastMCP drifts laterais + suspeita Locate; sessão Code de aplicação detectou Edit 2.7 emergente; sessão Code pre-aplicação de Provisão B detectou omissão de handoff de A + necessidade de ratificação explícita do Latin square + drift residual canonical examples. **Pattern: cada round detecta classe ortogonal de defeito porque cada round opera com contexto e foco diferentes.** D4 fixture packs como contract codification: README do pack BR codifica em forma de arquivo (snippet + AS coverage table) o contrato que recognizer rules de T07 devem satisfazer — README é predicate sobre output da T07, não documentação acessória.

*Domínio 5 — Context Management & Reliability.* D5 Provenance via citation chain reforçada em superfície ampla: ADR-0001 ↔ ADR-0002 §3 amendment ↔ ADR-0010 ↔ canonical §4.2/§5/§8.5 ↔ compact §3/§5.1/§6 ↔ README §Stack/§Setup ↔ CLAUDE.md §Stack — todas as decisões com cross-link explícito em cada Substitute by. Cinco eixos cross-doc reconciliados em uma única PR. D5 lockfile como fonte autoritativa secundária: `uv.lock` citado conjuntamente com `pyproject.toml` no amendment ADR-0001 (declarative source vs resolved source). Wire-format Option B do ADR-0002 §3 amendment foi calibrada contra `fastmcp/tools/base.py` na versão observada em `uv.lock` — pin de FastMCP 3.2.4 carrega peso normativo além de reprodutibilidade. D5 escalation pointers como interface cross-doc: dois pointers órfãos detectados em `compact.md` apontando para `canonical §5.3` e `canonical §5.4` inexistentes (canonical tem apenas §5 + §5.1) — dead links silenciosos sob refactor da fonte canonical. Endereçados em Edit 2.5 do Commit 2. Defense candidate emergente fortíssimo. D5 Code aplicador como verificador final em multi-round review: o último aplicador é também o último reviewer porque opera com arquivo INTEIRO em contexto, não com fragmentos visíveis em prep. Empirizado em três achados detectados na aplicação que três rounds Chat-review prévios não capturaram: drift §5.1 Errors list (Edit 2.7), omissão de handoff de A detectada em Code pre-apply de B, ratificação explícita Latin square detectada em Code pre-apply de B. D5 validation criteria são código: três desvios menores entre grep checks da spec e resultado pós-aplicação (Microsoft Presidio em ADR-0001, "presença do campo" em canonical, count errorCodes em compact) revelaram que critérios de validation foram redigidos como side-channels independentes do substitute_by — três rounds Code review não capturaram porque revisaram Locate + Substitute by sem cross-check explícito de validation criteria. Generalização: validation criteria são gates auto-verificáveis, merecem mesmo rigor de revisão cruzada que substitute_by.

**Decisões tomadas.**

- **Option B é obrigatória para `semgrep-runner`.** Limitação técnica é do FastMCP 3.2.4 (SDK que constrói ambos servidores MCP), não do Semgrep (subprocess CLI invocado pela tool `scan_diff`). Não há grau de liberdade para "recomendação Semgrep" — Semgrep não é o framework MCP. Decisão herdada de ADR-0002 §3 amendment 2026-05-17 + materializada em quatro pontos do canonical e três pontos do compact via Provisão A.

- **ADR-0001 Decision 2 amendment in-place, espelhando ADR-0008.** Decisão 2 reescrita para refletir pivô Presidio→Semgrep formalizado em ADR-0010 + pins formais (`fastmcp==3.2.4`, `pydantic==2.13.4`, `mcp==1.27.1`, `semgrep==1.163.0`). Original sobrevive em git history pre-amendment. Decisions 1, 3, 4, 5, 6 intactas.

- **Canonical sync cirúrgico, não re-derivação total**, per ADR-0003 Decision 1. Edits em quatro pontos contract-surface do canonical (§4.2 + §4.3 + §5 intro + §8.5); prose em §6, §7, §8.1-§8.4, §8.6 preservada. Compact sync em seis pontos cobrindo §3 (cabeçalho + tabela + payload shape) + §5.1 (timeout example + dead pointers) + §6 (initialization + obsolete pointer). Edit 2.7 cirúrgico (§5.1 Errors list pós-tabela) adicionado em sessão Code de aplicação como sétimo edit do Commit 2, escopo natural mesmo arquivo e mesma classe de drift.

- **Latin square parcial no pack BR ratificado explicitamente em Chat pós-Code-review pré-aplicação da Provisão B.** Seis snippets positivos cobrindo seis identificadores × quatro padrões distribuídos (não matriz completa 6×4=24). Justificativa: três sinais coerentes em tasks.md — linha 248 explícita "seis snippets positivos (um por identificador)", AS-1 a AS-6 singulares "snippet positivo + exatamente um finding", AS-9 (idempotência) assume conjunto estável. Asserção forte de transitividade (`br-cpf` matcheia padrão a, espera-se que matcheie b/c/d via pattern-either em T07) registrada como ressalva no README. Se T07 implementar regras separadas por padrão sintático em vez de pattern-either consolidada, transitividade não vale e interpretação matriz completa precisa ser ratificada — pack admite extensão para 24 sem refactor.

- **Identificadores sintéticos compartilhados positivo↔negativo é design intencional.** `238.547.961-37` (CPF) e `47.861.932/0001-92` (CNPJ) aparecem tanto em snippets positivos quanto em `negative_version_string.py`. Exerce discriminação AST-aware do Semgrep por contexto sintático (variable name + collection sink), não por string content. Documentado em nova subseção do README + docstring de `negative_version_string.py` para evitar leitura como duplicação acidental por Chat reviewer de T07.

- **Edit 5.3 (FastMCP pin no CLAUDE.md) aplicado, não deferido.** Simetria com Edit 5.2 (Pydantic): se Pydantic 2.5+ → 2.13.4 foi ajustado pelo mesmo motivo (deixar drifted dilui amendment ADR-0001 a poucas linhas de distância), FastMCP merece o mesmo tratamento. Inconsistência de aplicar 5.2 sem 5.3 enfraqueceria o pattern.

- **PR única com 5 commits internos pre-squash + squash-merge na main.** Auditability per logical change preservada na PR description e nos commits internos visíveis no review; main fica bisectable por unidade-PR per ADR-0001 Decision 5. Provisão B como single commit (creation coeso).

- **ASCII-fied commit message da Provisão B aceito.** Trade-off PS 5.1 + HEREDOC + UTF-8 é fricção conhecida do ambiente corporativo Windows. Conteúdo dos arquivos preserva todos os acentos (norma Brazilian Portuguese de ADR-0001 Decision 3 satisfeita); commit message é metadado de history, não output ao usuário no sentido normativo. Squash-merge colapsa o commit message em subject auto-gerado pelo GitHub UI a partir do PR title (que é escrito com acentos via UI), então o que sobrevive em main é o squash message. `--amend` evitado para não introduzir risco adicional pré-push.

- **R3 (drift cross-doc das regras imutáveis ADR-0001 Decision 4 ↔ CLAUDE.md §"Immutable domain rules") deferido para sweep Chat dedicado.** Reconciliação substantiva exige deliberação sobre qual conjunto é canônico (ou se bifurcação é legítima entre "regras de decisão" e "regras de output"), não correção cirúrgica. ~1.5h Chat estimada. Registrado no handoff como pendência crítica antes de Milestone C arrancar (regras imutáveis governam subagent behavior em Milestone C).

- **Débitos mecânicos residuais registrados.** PR mecânica `docs/tasks-attribution-fix` (~5min) — tasks.md linha 236 atribuição imprecisa; PR mecânica `docs/canonical-examples-sync` (~10min) — canonical examples usam rule_id sufixados (br-cpf-leak vs br-cpf bare) + companion edit alongside hedge §4.4 architecture-overview.md (~15min consolidado se rodarem juntas); verificação canonical §5.1 título contra `_template.md` (~5min).

**Artefatos produzidos.**

- **PR `chore/canonical-sync-C-semgrep-runner`** (Provisão A) — squash-mergeada em main; 5 commits internos pré-squash (ADR-0001 amendment + canonical sync + compact sync + README Setup + CLAUDE.md sync); 18 edits aplicados; 5 arquivos modificados; +202/-69 linhas vs main. Validation: todos os grep checks aprovados; três desvios menores documentados como inconsistências entre validation criteria e substitute_by (não defeitos de aplicação).
- **PR `feat/fixtures/recognizers-pack-br`** (Provisão B) — single commit consolidando 10 creates; 529 insertions; arquivo único `tests/mcp_servers/semgrep_runner/fixtures/recognizers_pack_br/` com 6 snippets positivos Latin square + 3 snippets negativos AS-7 + README com AS coverage table + provenance de identificadores sintéticos + assimetrias deliberadas + ressalvas. Validation: 9/9 Python AST parse; naming convention OK; 6/6 identificadores presentes; CPF/CNPJ shared 3× cada confirmando design intencional. Commit ASCII-fied em metadado (PS 5.1/HEREDOC) com conteúdo preservando acentos.
- **Documento `provisao-a-diff-aplicavel-FINAL.md`** (1059 linhas, 68K) — artefato endereçável consumido por sessão Code de aplicação. Inclui Locate/Substitute by para todos os 18 edits + grep checks + Pré-flight pins + Update do handoff (não aplicado pela sessão Code de A; aplicado por Provisão B Bloco 2).
- **Documento `provisao-b-diff-aplicavel-FINAL.md`** (928 linhas, 48K) — artefato endereçável consumido por sessão Code de aplicação. Inclui conteúdo inline dos 10 arquivos + grep checks + Pré-flight pins + Update do handoff cobrindo fechamento de A + B juntos (reconciliando omissão de A).
- **Script `gen_synthetic_ids.py`** mantido em `/home/claude/` da sessão Chat #28 — geração reproduzível dos 6 identificadores sintéticos via algoritmos públicos de check digit. Não commitado ao repo (script é provenance de Chat, não código de produção); algoritmos resumidos no README do pack BR.
- **PR descriptions + squash-merge commit messages** propostos para ambas as PRs, copiados pelo João nos respectivos commits de main.

**Defense candidates emergentes (cumulativos com #27, consolidados em onze itens, a migrar para `.claude/rules/` ou ADR breve em sessão metodológica futura).**

- **Multi-round Code review independente em contexto clean como independent evaluator iterativo.** Empirizado em #28 com cinco rodadas atingindo convergência: round 1 detectou bloqueadores factuais (paths errados em três pontos do diff aplicável + canonical §5 órfã) que três Chat reviews diferentes não atingiram; round 2 detectou drift cross-doc adicional (CLAUDE.md Presidio); round 3 detectou drifts laterais (Pydantic e FastMCP pins) + suspeita de Locate transcrito errado; sessão Code de aplicação detectou drift emergente (§5.1 Errors list); sessão Code pre-aplicação seguinte detectou omissão procedural (handoff de A não aplicado). **Pattern: cada round detecta classe ortogonal de defeito porque cada round opera com contexto e foco diferentes.** Pattern análogo a multi-instance review (Domínio 4) + independent evaluator de Rajasekaran 2026 + ADR-0008 Decision 3, aplicado a artefato de governance (não a código). Generalização: para PRs cross-doc multi-arquivo de moderada-a-alta complexidade, multi-round Code review em contexto clean é cost-effective comparado a tempo de retrabalho pós-merge.

- **Code aplicador como verificador final, irreduzível a reviewers anteriores.** Empirizado em três achados de #28: (a) drift §5.1 Errors list (Edit 2.7), detectado durante aplicação porque Code tem arquivo INTEIRO em contexto enquanto Chat reviews tiveram fragmentos visíveis em prep; (b) omissão de handoff de A, detectada por Code pre-apply de B via grep "Concluído em sessão #28"; (c) ratificação explícita Latin square, identificada por Code pre-apply de B via leitura cruzada de tasks.md linha 248 + 365 + AS-1..AS-6. Pattern: o último aplicador é também o último reviewer; não é redundância com reviewers anteriores, é cobertura de superfície diferente.

- **Validation criteria são código, não documentação acessória.** Três desvios menores entre grep checks da spec da Provisão A e resultado pós-aplicação revelaram que critérios de validation foram redigidos como side-channels independentes do substitute_by. Três rounds Code review não capturaram porque cada round revisou Locate + Substitute by; validation criteria foram tratadas como prosa periférica. Pattern de remediação: incluir grep checks no scope explícito do Code review em rounds futuros de Chat-revised diffs. Validation criteria são gates auto-verificáveis (código), merecem mesmo rigor de revisão cruzada que substitute_by.

- **Handoff updates pós-merge são também código — esquecer de aplicar produz drift entre estado documental e estado real do projeto.** Empirizado em #28: update do session-handoff pós-merge da Provisão A não foi aplicado pela sessão Code de A (que respeitou estritamente "responsabilidade termina nos 5 commits locais + grep checks"). Code review pre-apply da Provisão B detectou a omissão via grep "Concluído em sessão #28" — sub-lista que deveria existir não existia. Pattern: handoff updates pós-merge são parte do mesmo contrato que a PR fecha; Code review pre-apply da PR seguinte é mecanismo natural de detecção dessa classe de omissão. Materialização: adicionar checklist explícita ao protocolo Code de aplicação ("após push + merge, aplicar handoff update; se não aplicar, registrar como débito explícito").

- **Escalation pointers como dead links silenciosos.** Empirizado em #28: dois pointers no compact (`See canonical §5.3 if`, `See canonical §5.4 if`) apontavam para seções inexistentes do canonical (canonical tem apenas §5 + §5.1). Pattern: pointers no estilo `See <doc> §<X.Y>` quebram silenciosamente quando a seção referenciada é renumerada ou eliminada na fonte. Defense candidate forte para Capítulo de Discussão. Mecanismo de proteção possível: CI check de existência das âncoras referenciadas; ou rule explícita "renumbering de seção exige sync de todos os pointers para esse documento".

- **Lockfile como fonte autoritativa secundária para reconciliar ADRs de stack.** Reforço de defense candidate de #27, aplicado em #28: `uv.lock` citado conjuntamente com `pyproject.toml` no amendment ADR-0001 Decision 2. Pyproject declara constraint declarativa (lower/upper bounds); uv.lock registra versão determinística resolvida; ambos são fontes complementares, não redundantes. Em divergência real, uv.lock prevalece como fato. Pattern aplicável a qualquer ADR de stack onde a versão de dependência tem peso normativo (Option B amendment foi calibrada contra FastMCP 3.2.4 específico).

- **Nomes lógicos vs paths físicos.** `[project].name = "mcp-servers"` em metadado declarativo `pyproject.toml` não implica path físico `mcp_servers/`. Inferência morfológica é fonte recorrente de erro de provenance em multi-doc edits onde Chat não tem o filesystem em contexto. Empirizado em #28: Provisão A round 1 detectou três pontos com `mcp_servers/pyproject.toml` errados (paths reais são raiz do repositório). Defesa: glob/ls real antes de citar paths em decisões registradas; quando Chat não tem filesystem em contexto, escala para Code via pause-and-ask em vez de inferir.

- **Scratchpad files + provenance pattern para edits cross-doc.** Quando Chat não tem o arquivo destino em contexto (e.g., CLAUDE.md durante Provisão A round 2), pattern admitido: Chat propõe substituição baseada em fragmento transcrito + invariante semântico; Code valida no contexto real antes de aplicar. Barato quando Code já validou o fragmento original. Aplicado em Commit 5 da Provisão A. Pattern oposto a "exigir contexto completo antes de propor edit" — admite gradação de risco com fallback explícito a pause-and-ask.

- **Regras imutáveis precisam de mecanismo de sync explícito ou bifurcam silenciosamente.** Drift R3 entre ADR-0001 Decision 4 (três regras: human escalation, citation `LGPD-Art-7-I`, schema-versioned policy compatibility) e CLAUDE.md §"Immutable domain rules" (três regras distintas: no fabricated certainty 4 verdicts, citation `POL-` prefix, two-axis policy versioning) mostra que duas representações coexistentes do mesmo objeto conceitual bifurcam sob evolução paralela dos dois documentos. Sweep dedicado é remediação ex-post; rule architectural seria "imutáveis vivem em um source-of-truth, outros docs incluem por link/include, não por cópia". Pendência crítica antes de Milestone C arrancar — regras imutáveis governam subagent behavior em Milestone C.

- **Fixture packs como contract codification.** README do pack BR codifica em forma de arquivo (snippet + AS coverage table) o contrato que recognizer rules de T07 devem satisfazer — README é predicate sobre output da T07, não documentação acessória. Cada AS especifica veredito esperado (matching rule_id) sobre o `scan_diff` output. Pattern análogo ao POL pack README de Milestone A. Generalização: fixture packs em projetos spec-driven são contratos operacionalizados, com README como interface entre fixture e task.

- **Latin square parcial como cobertura mínima contract-driven.** Sob AS que declaram "snippet positivo" singular + "exatamente um finding" por identificador, Latin square é suficiência; matriz completa é robustez opcional. Decisão de superfície mínima driven pelo contrato, não por preferência estilística. Pattern aplicável a qualquer fixture pack onde o contrato declara cobertura singular por item — extensão para matriz completa é evolução, não pré-requisito.

- **ASCII-fied commit messages em ambiente Windows PS 5.1 como convenção pragmática.** Empirizado em #28 Provisão B: Code optou por ASCII-fy commit message (remoção de acentos + em-dashes) por cautela com bash HEREDOC sob PS 5.1, preservando acentos no conteúdo dos arquivos. Trade-off aceitável: norma Brazilian Portuguese de ADR-0001 Decision 3 aplica a outputs ao usuário (conteúdo); commit messages são metadado de history. Squash-merge colapsa o commit message interno em subject auto-gerado pelo GitHub UI a partir do PR title, então acentos no metadado interno têm vida útil curta. Pattern candidato a item curto em `.claude/rules/windows-tooling.md` se afetar futuras sessões Code.

**Métricas operacionais.**

- **Custo total Chat:** ~6h efetivas distribuídas em janela de ~24h, cobrindo prep das duas Provisões (~3h) + três rounds de Code review independente Provisão A (~1.5h Chat de processing dos achados) + uma rodada Code review pré-aplicação Provisão B (~30min Chat de processing) + fechamentos pós-aplicação (~1h).
- **Custo total Code:** ~2h efetivas distribuídas em duas sessões — aplicação Provisão A (~1.6h, 5 commits internos + Edit 2.7 emergente + grep checks finais) + aplicação Provisão B (~30min, 10 creates + validation).
- **Documentos consultados ou referenciados diretamente:** ~18 (canonical+compact semgrep-runner, ADR-0001/0002/0003/0008/0010, tasks.md, README.md raiz, CLAUDE.md, session-handoff.md, learning-log.md, pyproject.toml, uv.lock, privacy-safety.md, README pack POL-001..004, POL-000.yaml referência, fastmcp/tools/base.py via inferência).
- **Drifts detectados ao longo da sessão:** 12 totais — seis catalogados em #27 (cinco contract surface + um fundacional) + três emergentes na prep Chat de Provisão A (escalation pointers órfãos + schema mismatch em exemplo + atribuição cross-doc imprecisa) + um cross-doc adicional em Code review round 2 (CLAUDE.md Presidio) + dois laterais em Code review round 3 (Pydantic + FastMCP pins) + um residual na aplicação (Edit 2.7 §5.1 Errors list) + dois detectados em Code review pre-aplicação Provisão B (omissão de handoff de A + ratificação Latin square necessária + drift canonical examples herdado).
- **Edits aplicados em PR Provisão A:** 18 obrigatórios + 0 opcionais (Edit 5.3 FastMCP aplicado) = 18 totais distribuídos em 5 commits internos.
- **Arquivos criados em PR Provisão B:** 10 (6 snippets positivos + 3 negativos + 1 README).
- **Defense candidates acumulados:** 11 itens (4 herdados de #27, 7 novos ou refinados em #28).
- **Tamanho dos artefatos endereçáveis:** 1059 linhas (Provisão A FINAL.md, 68K) + 928 linhas (Provisão B FINAL.md, 48K).
- **Rodadas de review independente:** 5 total (3 Chat reviews + 1 Code review pre-apply Provisão B + 1 Code aplicação como verificador final em cada PR).

**Próximo passo.**

Próxima sessão Chat encerrada — Milestone B pré-implementação fechada. Próxima sessão é **Code de implementação de T05** (server skeleton + rule set loader).

T05 destravado por:
- Provisão A mergeada (canonical em Option B; ADR-0001 stack realinhado).
- PR mecânica `docs/tasks-milestone-b-decomposition` mergeada (T05 com AS especificados em tasks.md linhas 258-296).
- ADR-0010 (Semgrep installation strategy) ratificado.

T05 não depende de Provisão B (que destrava T07).

Custo estimado T05: ~1.5-2h Code. Pattern: mirror estrutural de `src/mcp_servers/policy_reader/` (loader, server, models). Stub de tool `scan_diff` retornando envelope `NOT_IMPLEMENTED` em sucesso (per AS-8 de T05) — desaparece em T06. Per canonical §8.6, ausência do binário `semgrep` no PATH NÃO aborta o startup; verificação per-call vive em T06.

Trilhas paralelas / débitos residuais não-bloqueantes (registradas no handoff Bloco 3 da Provisão B):
- PR mecânica `docs/tasks-attribution-fix` (~5min Code).
- PR mecânica `docs/canonical-examples-sync` + companion §4.4 hedge architecture-overview.md (~15min Code consolidado).
- Sweep cross-doc das regras imutáveis ADR-0001 Decision 4 ↔ CLAUDE.md §"Immutable domain rules" (Chat dedicada ~1.5h). **Pendência crítica antes de Milestone C arrancar.**
- Verificação canonical §5.1 título contra `_template.md` (~5min Code).
- (Opcional) Adicionar convenção ASCII-fied commit message em PS 5.1 a `.claude/rules/windows-tooling.md`.

## 2026-05-22 — sessão #29 — canonical-sync-D + T05 skeleton

**Entregas.**
- PR `chore/canonical-sync-D-semgrep-runner` mergeada: canonical.md (+90/-76),
  compact.md (+44/-30), tasks.md AS-7 (+1/-1).
- PR `feat/semgrep-runner-skeleton` (T05) mergeada: 10 arquivos, 650 insertions,
  64 tests passando (53 policy_reader baseline + 11 semgrep_runner).
- prompt-t05-v3.1.md gerado (output local; Bloco 6 aplicado pós-merge canonical-sync-D).
- Review cross-doc pós-#28 realizada (13 achados novos catalogados; 3 PRs
  de housekeeping propostas).

**Decisões fechadas.**

*canonical-sync-D:*
- Opção C ratificada (validada via web_search contra docs Semgrep): semgrep-runner
  é runner genérico; rule set MVP cobre personal data BR. Framing "domain-agnostic"
  é adjetivo arquitetural na description.
- Description prosa unificada (3 parágrafos, ~190 palavras, byte-idêntica entre
  canonical §4.2 e compact §5.1). Blockquote removido; prosa plana per pattern
  policy-reader.
- 7 decisões de output structure: rules_version/semgrep_version top-level
  (compact-side placement); rule_severity lowercase, rule_message, location
  aninhado com start/end col, snippet, elapsed_seconds (canonical-side naming).
  Mixed-direction sync documentado na commit message.
- §5 canonical reorganizado per _template.md: §5.1 estrutura canônica do payload,
  §5.2 classes de erro (validation vazia como declaração positiva), §5.3 casos
  que parecem erro mas não são (4 casos incl. stderr não-vazio em exit 0),
  §5.4 tabela consolidada (coluna "Tools que emitem" adicionada per template),
  §5.5 princípio de evolução. Substituição atômica única (range ## 5 até ## 6
  exclusive) eliminou ordering hazard da v1.
- 3 boas práticas Semgrep ancoradas em canonical §2.2 e §4.2: --metrics=off
  e --json como flags obrigatórias do subprocess; timeout process budget vs
  --timeout interno são ortogonais (sem impl-spec como subprocess.run — neutro
  de primitivo per Rev1 U1-S1).

*T05:*
- 12 DDs ratificadas (T05-1 a T05-12).
- compute_rules_version: SHA-256 prefixo sha256:, normalização CRLF→LF, filename
  no input do hash (protege contra rename silencioso), glob *.yaml flat com
  docstring de forward-compat (rglob + path.relative_to para hierarquia futura).
- Empty rules dir: raise RulesLoadError em pt-BR ANTES de Pydantic (DD-T05-12,
  mirror de policy_reader/loader.py:262-267). _bootstrap captura APENAS
  RulesLoadError; ValidationError propaga uncaught.
- tools.py / _envelope.py inline em server.py para T05 (DD-T05-11 — premature
  scaffolding evitado; T06 introduz com conteúdo real).
- Test count real: 64 (não 62 estimado) porque AS-6 parametrizado em 3 gera
  3 test functions no pytest.

**Conceitos da prova exercitados.**

- 💡 D4 — Prompt Engineering: validation-retry loop manual (prompt T05 v1→v2→v3→v3.1;
  multi-instance review em 2 configurações sessão hot vs sessão fresh; convergência
  empírica entre reviewers como sinal de saturação e critério de parada).
- 💡 D4 — Prompt Engineering: few-shot via referência estrutural — prompt T05 aponta
  para tests/mcp_servers/policy_reader/ como pattern operativo em vez de exemplos
  inline; Code reproduz estrutura em semgrep_runner por espelhamento.
- 💡 D2 — Tool Design: tool description como prompt do agente em cada turn —
  inspect.getdoc() normaliza docstring para list_tools(); AS-7 valida byte-identity
  de toda a cadeia (compact.md → docstring → inspect.getdoc() → list_tools()).
- 💡 D2 — Tool Design: isError reserved para protocol-level; discriminação de domínio
  por presença de errorCode em structuredContent (Option B) — materializado no
  NOT_IMPLEMENTED envelope do stub T05.
- 💡 D1 — Agentic Architecture: escalation via canary embutido em prompt —
  cláusula de flag de DD-T05-9 disparou conforme intenção (Code parou antes de
  Fase 2 e devolveu decisão para camada humana); zero código bugado mergeado.
- 💡 D1 — Agentic Architecture: skeleton-first task decomposition — T05 entrega
  esqueleto com gate task-level próprio; T06 preenche; cada um com critério de
  aceitação independente. _STATE assert no stub protege bootstrap order para T06.
- 💡 D1 — Agentic Architecture: GATE 1 explícito como separation generator/evaluator
  (Rajasekaran) — Code é generator do plano; João é evaluator; sem essa separação
  Code regride para "implementa e descobre problema depois".
- 💡 D5 — Context Management: provenance arquitetural via web_search — viabilidade
  de Opção C confirmada contra docs Semgrep antes de ratificar (não inferida de
  evidência interna do projeto). Pattern: external claims exigem external
  verification.
- 💡 D5 — Context Management: specs auto-contidas como lost-in-the-middle defense
  (sub-decisão A do Cluster 3 — não cross-ref entre specs componentes).
- 💡 D3 — Claude Code Configuration: template-driven spec authoring —
  _template.md como contrato de discovery; estrutura fixa garante que toda spec
  carrega o mesmo set de informações no mesmo lugar.

**Defense candidates emergentes (Capítulo de Método).**
- Iterative prompt refinement via multi-instance review (v1→v2→v3) com
  convergência empírica como sinal de saturação.
- Review multi-instância em duas configurações (hot vs fresh) captura classes
  complementares de achado: hot tem vantagem em design/framing; fresh tem
  vantagem em verificação direta (grep, find, glob).
- Escalation via pre-flight check materializada em prompt como contrato
  decisional — cláusula de flag de DD-T05-9 disparou conforme intenção.
- Drift entre formas da spec pode ser lossy quando destilação roda sem
  cross-check contra AS list (compact omitiu start_col/end_col vs canonical).
- Substituição atômica vs incremental em diff aplicável: incremental quando
  decisões individuais ainda precisam de debate; atômico quando deliberação
  está fechada e o que sobra é mecânica de aplicação.
- Peer review independente de artefatos de especificação (não só de código)
  como gate de qualidade pré-execução — canonizável como workflow independente.
- Mixed-direction sync: diferentes eixos do mesmo diff sincronizam em direções
  opostas (compact-side placement para provenance; canonical-side naming para
  findings fields). Commit message precisa nomear cada direção explicitamente.

**Artefatos.**
- `/mnt/user-data/outputs/prompt-t05-v1.md` (430 linhas)
- `/mnt/user-data/outputs/prompt-t05-v2.md` (589 linhas)
- `/mnt/user-data/outputs/prompt-t05-v3.md` (613 linhas)
- `/mnt/user-data/outputs/prompt-t05-v3.1.md` (611 linhas)
- `/mnt/user-data/outputs/canonical-sync-d-diff-aplicavel.md` (645 linhas, v1)
- `/mnt/user-data/outputs/canonical-sync-d-diff-aplicavel-v2.md` (728 linhas, v2)
- PR `chore/canonical-sync-D-semgrep-runner` (merged, hash head 3c069a2→bf53959)
- PR `feat/semgrep-runner-skeleton` (merged, hash head 89bf1c7)

**Próximo passo.**

Antes de T06: F1 housekeeping — PR `docs/refresh-stale-state` (~20min Code
mecânico): CLAUDE.md status flags (Milestone A fechado, 64 tests, 3/3 resources
+ tools, semgrep-runner skeleton operacional), REQUIREMENTS.md RNF-001
(Pydantic 2.5→2.13.4, débitos removidos), policy-reader compact §5.3 nota MVP
removida/atualizada, DESIGN.md ADRs 0006-0010 adicionados, semgrep_version nos
exemplos das specs uniformizados para 1.163.0, rules_version compact exemplo
→ forma sha256:.

T06 (~3h Code): scan_diff completo — subprocess Semgrep + 6 errorCodes + wire
format Option B per canonical §5. Pré-requisitos: T05 mergeado ✓, Provisão A
mergeada ✓, ADR-0010 ratificado ✓, binário semgrep==1.163.0 disponível via
uv tool install ✓.

Débitos cross-doc catalogados (3 PRs propostas, não urgentes antes de T06
exceto F1): docs/refresh-stale-state, docs/adr-foundational-amendments,
docs/canonical-sync-E-policy-reader. Sweep regras imutáveis (ADR-0001 D4 ↔
CLAUDE.md §Immutable domain rules) crítico antes de Milestone C arrancar.

## 2026-05-22 — sessão #30 — housekeeping consolidated pós-Milestone A (PR #55) + multi-round review (3 rounds) sobre artefato-prompt

**Foco.** Sessão Chat persistente longa de ~6h efetiva cobrindo: (i) inventário e priorização dos 15 débitos catalogados nos dois rounds de cross-doc review pós-#28 (achados anexados por João); (ii) redação do prompt T30-Hk v1 → v2 → v3 sob 2 rounds de Chat review independente entre versões; (iii) GATE 1 do Code com 10 DDs + 2 escalações (DD-7 ajuste numérico, DD-8 confirmação semântica); (iv) execução Code em 3 commits internos sob 1 PR consolidada (PR #55); (v) gates pós-merge + reporte. Padrão verification-before-inference materializou em 3 escalas: snapshot vs main (pre-flight), `wc -l` vs claim numérico (DD-7), e empirical vs estimativa (count de tokens em new_str).

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1 multi-instance review com escalation progressiva sobre artefato-prompt — 3 rounds com classes distintas de bug por round.** Round 1 (v1 review): 4 bugs estruturais — ADR-0001 status format inexistente assumido como `**Status.** Accepted.\n**Date.** ...` quando ADR-0001 usa heading H2 `## Status`; proposta-tcc2 §7 new_str gramaticalmente quebrada por old_str truncado; backtick em PS 5.1 dentro de aspas duplas tratado como escape; filename ADR-0003 errado. Round 2 (v2 review): 2 bugs finos — Edit 2.A.7 old_str sem markdown `**Note (MVP):**`+ backticks em `not_applicable` (defeito reproduzido em v1+v2 sem ser detectado); contagens de regressão erradas pós-Amendment scope porque blocks H2 preservam tokens como audit trail intencional. Round 3 (v3 GATE 1): 0 bugs estruturais; apenas DD-7 ajuste numérico (959 vs 960) pego empiricamente por Code via `wc -l`. Severidade decai monotonicamente; verificação empírica direta toma lugar de review textual. **Defense candidate forte** — pattern documentado em learning-log #21+, agora materializado em escala maior (3 rounds + 17 sites + 2 reviewers independentes).

- **D1 Task decomposition cross-PR — escopo de auditoria como limite descritivo, não normativo.** Cross-doc review original (#29) cobriu `docs/` apenas. Code descobriu na #30 que `src/mcp_servers/policy_reader/models.py:11` tem docstring stale citando "compact spec still writes article_source in places". Drift escapou as duas rodadas de auditoria porque não estavam no escopo declarado. **Defense candidate**: auditoria não é teorema de completude, é amostragem disciplinada. Próximas auditorias devem declarar escopo explicitamente; ciclos paralelos cobrindo `src/` (docstrings, comments) podem virar prática.

- **D1.6 PR consolidada com N commits internos pre-squash — terceira materialização do pattern.** Provisão A em #28, T05 skeleton em #29, PR #55 housekeeping em #30. Pattern admitido por `.claude/rules/git-conventions.md` quando diff é clean e Chat-revisable. Blame por commit some no squash, audit trail vive em PR description. **Defense candidate sobre granularidade adaptativa de PR**: 1 PR para 3 categorias homogêneas de cleanup (refresh stale state + ADR amendments + canonical-sync-E) com cross-doc review numa pegada só vs 3 PRs separadas — trade-off ratificado por escopo homogêneo (mecânico, sem deliberação).

**Domínio 2 — Tool Design & MCP Integration (18%)**

- **D2 tool description quality preservada por canonical-sync-E.** Edit 2.C.6 (G13) verificou empiricamente que `_format_stat_ref` REALMENTE existe em `src/mcp_servers/policy_reader/tools.py:592` como wrapper Pydantic-aware sobre `_format_law_reference` (linha 550, ADR-0009). Achado original do cross-doc review classificou G13 como "INCERTO" pendendo leitura direta de `tools.py`. Esta sessão materializou a verificação direta — o nome no canonical §3.1 estava correto; o que estava errado era só a ref cruzada `(canonical §4.1)` dangling. **Defense candidate sobre verification-before-inference em diagnóstico**: marker "INCERTO" pode resolver para "naming drift" OU "ref dangling com naming correto" — Code lê o arquivo antes de concluir.

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- **D3 `.claude/rules/` autoritativos pós-housekeeping — segunda materialização do pattern.** Primeira em prep T03 (#23). Aqui em prep T30-Hk: `windows-tooling.md` (commit messages ASCII), `git-conventions.md` (PR consolidada com N commits), `spec-driven-workflow.md` (plan-mode + GATE 1 + pause-and-ask), `verification-before-inference.md` (DD-7 materialização), `review-patterns.md` (multi-instance review independente). Cinco rules invocadas nominalmente sem re-explicar conteúdo. Materializa o benefício de rules como contrato decisional consumível em runtime de implementação. **Defense candidate**: cristalização canônica de convenções em rules permite redação subsequente mais enxuta — o prompt v3 (803 linhas) seria proporcionalmente maior sem essa cristalização prévia.

- **D3 CLAUDE.md status flags como source-of-truth — refresh pós-Milestone A.** Edit 2.A.1 atualizou §"Status flags" de "Milestone A in progress (T01, T02a, T02b operational; T03, T04 pending) / Tests: 27 passing" para "Milestone A closed in session #25 (...); Tests: 64 passing (...)". Cada sessão a partir desta lê o estado correto sem inferir das frases-fonte fixas. **Defense candidate sobre cadência de refresh**: §"Status flags" tem semi-vida curta (cada milestone fecha em ~5-8 sessões); refresh mecânico como housekeeping dedicada (não acoplado a feature work) preserva o status flags como autoridade.

**Domínio 4 — Prompt Engineering & Structured Output (20%)**

- **D4 off-by-one em estimativa de contagem em new_str narrativo.** Chat (prep) estimou que Amendment scope de ADR-0005 conteria 3 ocorrências de `article_source`; Code contou empiricamente 4 (Chat não contou a menção "the field name `article_source` was a residue of a pre-#16 envelope sketch"). Pequeno mas registrável. **Defense candidate menor**: estimativas em prosa multilingual densa onde o token é citado em múltiplos contextos sintáticos são facilmente off-by-one; preferir contar empiricamente ao redigir gates de regressão em vez de inferir do new_str. Adicionalmente, gates qualitativos `git grep -c` que reportam o número visto são robustos a essa off-by-one (não bloqueiam pause-and-ask falso); gates quantitativos com count esperado fixo ("esperado: 3 matches") são frágeis.

- **D4 GATE 1 com pause-and-ask específico para edit semanticamente frágil.** Prompt T30-Hk §3 declarou que Edit 2.A.8.b (proposta-tcc2 §7 — `tripartite → two-scope`) deve ter `old_str`/`new_str` ratificados como sub-bullet do plano antes de aplicar. Code cumpriu na DD-8. Pattern aplicável a qualquer edit cujo new_str reorganiza prose multilingual densa em vez de substituir um token por outro. **Defense candidate sobre granularidade de GATE 1**: gate não é binário (planejou tudo / não planejou); gate pode ser cirúrgico (planejou tudo + ratifique especificamente os N edits frágeis enumerados).

**Domínio 5 — Context Management & Reliability (15%)**

- **D5 verification-before-inference generalizado para claims numéricos — DD-7.** Prompt v3 declarava `"empirical sizes are 960 and 517 respectively"`. Code rodou `wc -l docs/specs/policy-reader/canonical.md` no pre-flight, detectou 959, escalou no GATE 1. Ratificação Chat usou 959. **Defense candidate forte**: pattern verification-before-inference, originalmente codificado em `.claude/rules/verification-before-inference.md` para `old_str`/`new_str` cirúrgicos, **opera também sobre qualquer claim numérico que o prompt afirma como verdade** — line counts, ocorrências esperadas, tamanho de payload, contagens em geral. Generalização explícita registrada.

- **D5 achados cross-doc como inputs verificáveis, não autoridade.** O achado de cross-doc review do João declarava "G12: tamanhos canonical 673/440 → 960/517". Code descobriu na pre-flight que o número real era 959, não 960. **Defense candidate sobre tratamento de achados**: achado é input ao processo, não output autoritativo. Replicar pattern em futuras housekeepings — verificar claims do achado contra estado real antes de aplicar.

- **D5 Amendment scope blocks com audit trail intencional — gates exclusion-aware.** Edits 2.B.1 (ADR-0001 D3) e 2.B.2 (ADR-0005 D1+D2) usam pattern Amendment scope H2 paralelo ao Context. Por design, o bloco preserva citações do estado original (`"originally prescribed cláusula IDs in 'stable Portuguese form (e.g., LGPD-Art-7-I)'"`) como audit trail. Consequência: gates de regressão `git grep -nE 'LGPD-Art-7-I'` retornam matches legítimos. Pattern correto: `git grep -nE 'TOKEN' . -- ':!arquivo-com-audit-trail.md'` + `git grep -c "TOKEN" arquivo` qualitativo. **Defense candidate forte**: gates de regressão precisam ser exclusion-aware quando edits preservam tokens originais como audit trail intencional. Replicar em toda futura PR que use Amendment scope.

- **D5 Patch documento como fóssil — handoff é template-overwrite forward-looking.** O `docs/process/session-handoff.md` em main pós-#29 (db2d2c8) era "patch documento" estilizado com "Locate/Substitute by" referenciando ancorras inexistentes em `tasks.md` (lista A-G que nunca existiu naquele formato). Provavelmente proposta de uma sessão Chat anterior nunca materializada como reestruturação real do tasks.md. Identificado no Chat review v2 do prompt T30-Hk durante prep. **Defense candidate forte**: handoff é template-overwrite por sessão, forward-looking, prosa direta — não patch acumulativo. Esta sessão #30 abandona o vocabulário "Locate/Substitute" no handoff novo da #31 justamente por causa desse anti-pattern detectado. Documentos de coordenação entre sessões precisam ter convenção de forma explícita e estável; mudança silenciosa de forma sem decisão deliberada acumula débito documental.

### Decisões

- **Sweep regras imutáveis** deferido para Chat dedicada antes de Milestone C arrancar (não-bloqueante para T06+T07; bloqueante para C). Discrepâncias entre CLAUDE.md §"Immutable domain rules" e ADR-0001 Decision 4 catalogadas no handoff da #31.
- **proposta-tcc2.md §6 sobre "dois eixos"** não atualizada — defensável como histórico (documento entregue à banca).
- **`models.py:11` docstring stale**, **mypy não em dev-deps**, **architecture-overview §4.4 hedge**, **drift br-cpf-leak/br-cnpj-in-log** — todos catalogados no handoff #31 como débitos não-bloqueantes baixa-prioridade para próxima housekeeping.
- **Estilo do session-handoff.md**: abandonado vocabulário "Locate/Substitute by" do template pré-#30 em favor de prosa direta forward-looking. Decisão materializada no handoff #31 pós-merge da PR #55.

### Artefatos

- PR `#55` — `chore: post-Milestone A housekeeping cleanup` (mergeado via squash). Squash hash a registrar quando handoff #31 for commitado em main.
- Commits internos pre-squash: `3fbbc9b` (refresh stale state, 8 arquivos, +39/-28), `487ca49` (ADR amendments, 5 arquivos, +38/-14), `014c694` (canonical-sync-E policy-reader, 2 arquivos, +6/-6).
- 15 arquivos modificados no total na PR, +83/-48 linhas, 100% docs/markdown.
- Prompt-artefatos em `/mnt/user-data/outputs/`: `prompt-t30-housekeeping.md` (v1, 725 linhas), `prompt-t30-housekeeping-v2.md` (776 linhas), `prompt-t30-housekeeping-v3.md` (803 linhas) — três versões como evidência de multi-instance review iterativo.
- Dois Chat reviews independentes do prompt (entre v1→v2 e entre v2→v3), anexados como documentos pelo João nas mensagens do Chat persistente da sessão #30.
- Plano GATE 1 do Code com 10 DDs (DD-1 a DD-10) e 2 escalações para Chat (DD-7 numérica + DD-8 ratificação semântica do new_str da §7 proposta-tcc2).
- Novo `docs/process/session-handoff.md` substituindo o pós-#29 como direct commit em main (close formal da #30 + abertura da #31 T06).

### Próximo passo

Sessão Chat de prep T06 (~1h). Pre-leitura conforme handoff #31 §"Pre-flight para sessão Chat de prep T06". Redigir prompt T06 com pattern análogo ao T30-Hk: pre-flight verification + plan-mode + GATE 1 + Fase 2 com gates intermediários por errorCode classe. Custo estimado: prep + Code + review = ~5h totais distribuídos em 2-3 sessões.

Pre-flight em particular: verificação direta empírica antes de redigir (estado real de `server.py`, `loader.py`, `errors.py` pós-T05; conta empírica de linhas; estado de `tools.py` para qual escolha de primitivo de timeout — não inferir). Aplicar a lição DD-7 da #30: qualquer claim numérico no prompt T06 (linha esperada, count de tests, count de errorCodes implementados) deve ser verificado empiricamente antes de ser declarado autoridade.

# Learning Log — entrada T06

Anexar a `docs/process/learning-log.md` no projeto, abaixo das entradas anteriores (T05, Provisão A, etc).

---

## 2026-05-23 — T06 scan_diff completo (PR #56)

### Conceitos da prova exercitados

**D1 — Agentic Architecture & Orchestration (27%).**
- GATE 1 + Fase 3 faseada por classe de errorCode aplicada a feature task pela primeira vez (não housekeeping). Halt-and-escalate em pre-flight (3.E mapping divergente; 3.G shallow signal em JSON) + gate 3.A (snippet "requires login") absorveu DD-T06-22 e DD-T06-23 sem rework arquitetural.
- Pattern de stop_reason implícito materializado: Code parou em cada gate intermediário (3.A→3.J), escalou ao Chat quando surface empírica não estava em DD prévia, aguardou ratificação humana.
- Sub-fases independentes (10 sub-fases de Fase 3) com gate intermediário cada — análogo a coordenador-subagent pattern em multi-instância, mas single-turn dentro do mesmo Code.

**D2 — Tool Design & MCP Integration (18%).**
- errorCode discrimination com 6 codes via Pydantic Literal; mapping de 8 exit codes Semgrep (X1 ratificado) para 2 errorCodes via tabela explícita em canonical §8.6.
- Wire format Option B universal (`isError: false` em todos retornos; discriminação via `errorCode` em `structuredContent`) implementado via wrappers `_envelope_tool_result` + `_scan_success_tool_result` em `_envelope.py`.
- Anchor `isRetryable byte-by-byte vs canonical §5.4` detecta drift sem precisar end-to-end — anchor invariant de contrato per `.claude/rules/test-strategy.md`.
- Pydantic com `ConfigDict(extra="ignore")` em `_SemgrepRunOutput` — tolera campos volátil cross-Semgrep-versions sem regredir contrato.

**D4 — Prompt Engineering & Structured Output (20%).**
- Iterative prompt refinement v1→v5.1 (~5 rounds independentes; multi-instance review Chat + Code clean alternados). Trajetória: v1 (395 linhas, 4 bloqueadores) → v2 (520, 4 bloqueadores) → v3 (590, 0 bloqueadores; C1 reframe DD-T06-21 anti-pattern) → v4 (620, 1 bloqueador colateral AS-7 namespace) → v5 (625, sexta companion edit) → v5.1 (640, surgical fixes).
- Cross-check contra docs oficiais externas (Semgrep CLI reference, ATD schema, issues #5891/#11114/#8254/#435742) + canonical interna + tasks.md como third-line of defense.
- Pydantic gating do Semgrep JSON output com validation-retry implícita (parse failure → SEMGREP_EXECUTION_FAILED com `parse_error` em details, em vez de propagar exception).

**D5 — Context Management & Reliability (15%).**
- Subprocess error propagation com cleanup empírico verificado (zero zombies em pre-flight 3.H via `tasklist /FI`); provenance via JSON top-level `version` field (pattern do próprio Semgrep MCP server).
- Verification-before-inference aplicada recursivamente: ao código (pre-flight verifica exit codes empíricamente); ao prompt (DD-T06-21 era invariante canonical já declarada, não decisão nova); à interpretação de catches anteriores (S2 v3 não era "migrar AS-7", era "evitar duplicar `_EXPECTED_*`"); aos companion edits (texto literal citado antes de propor diff).
- Scratchpad efetivo em pre-flight (`$smokeDir`, `$shallowDir`) com cleanup delegado ao operador per §10.

### Decisões load-bearing

1. **Exit code mapping X1 (ratificado em GATE 1).** Exits 4 e 5 documentados em CLI reference removidos por **empíricamente inalcançáveis** em Semgrep 1.163.0 — pre-flight 3.E revelou que Semgrep colapsa "rule parse error" em exit 2 e "unparseable YAML" em exit 7. CLAUDE.md "no defensive code for impossible scenarios" aplicado. Granularidade perdida ("Rule parse error" cai em SEMGREP_EXECUTION_FAILED em vez de INVALID_RULE_SET) é trade-off aceitável: caller já recebe `stderr_excerpt` para diagnóstico específico.

2. **Snippet via filesystem read (DD-T06-23, halt em 3.A).** Semgrep OSS sem `SEMGREP_APP_TOKEN` emite `extra.lines = "requires login"`, não código real. Canonical §4.2 + §4.3 exemplo declaram snippet como código real, required. Canonical §8 veta token. Solução: helper `_read_snippet(location, repo_root)` em `tools.py` lê o arquivo do disco. Não-defensivo: baseado em descoberta empírica de Fase 3, não em hipótese.

3. **6 companion edits bundled (não pre-existing debt).** Distinção descritiva de `.claude/rules/git-conventions.md`: PR sequencing favorece separação para *debt*; *novas decisões* pertencem ao PR que as estabelece. Bundling justificado em §9 do PR body explicitamente.

4. **Splittability rejected (per ADR-0008 §1).** T06 estimado ~3-4h excede janela 1-3h. Rejeição argumentada: AS-11 (wire format Option B) precisa happy path + ≥1 error path para parametrize cross-errorCode; AS-7/AS-13 compartilham mock infra com AS-6; pre-flight 3.H (subprocess cleanup) descarta investimento se Fase 3 não toca subprocess. Awareness > tacit assumption.

### Defense candidate metodológico (novo, para Capítulo de Método)

**Convergência multi-round NÃO-monotônica em quantidade de catches; severidade conceitual decai monotonicamente.**

Trajetória observada v1→v5.1:
- v1: 4 bloqueadores estruturais (function signatures, scope creep)
- v2: 4 bloqueadores (Windows-specific factual + editorial)
- v3: 0 bloqueadores; 4 refinamentos (mas DD-T06-21 reinventava canonical §4.2 — anti-pattern não detectado por review de coerência interna; só review verificacional capturou em v4)
- v4: 1 bloqueador colateral mecânico (AS-7 namespace collision T05 vs T06) — emergiu como subproduto do fix S2 v3
- v5: catches cirúrgicos da reversão (counts, naming)
- v5.1: catches cosméticos (math, polimentos)

**Insight:** triangulação real requer ≥1 round verificacional após cada round de fix substancial. Review coerência interna ratifica mas pode mascarar reinvenção de contrato; review verificacional (que abre arquivos reais do projeto) é complementar necessário, não redundante.

**Aplicação recursiva de verification-before-inference:**
- Ao código (pre-flight 3.A-3.H).
- Ao prompt (DDs perguntam "isto já está em canonical/spec/tasks?").
- À interpretação de catches anteriores (revisitar S2 v3 com leitura literal de `tasks.md` evitaria reinterpretar para erro mecânico em v4).
- Aos companion edits (Fase 2 cita texto literal dos arquivos alvo antes de propor diff).

**Pre-flight ambicioso paga dividendo iterativo.** As 3 surfaces empíricas que toda deliberação Chat v1→v5.1 não pegou:
- Exits 4/5 unreachable (descoberto em pre-flight 3.E).
- Shallow signal em JSON `errors[].message`, não stderr (descoberto em pre-flight 3.G).
- Snippet "requires login" em OSS (descoberto em mapping de Fase 3.A).

Pattern relevante para `.claude/rules/review-patterns.md` futura amendment: anomalias de pre-flight devem ser cross-checked contra spec **exemplo** (não só spec contract) antes de classificar como "não-bloqueante" — gap entre fato empírico e shape contratual emerge ao mapear, não ao verificar isoladamente.

**Custo total:** ~3-4h Chat de iteração (5 rounds) para prompt de feature task de ~3-4h Code. Trade-off: tempo de prep dobra tempo de implementation, mas risk de implementation com surprise crítica decai substantivelmente. Defesa empírica: zero rework arquitetural em Fase 3 apesar de 2 implementation surprises absorvidas (DD-T06-22, DD-T06-23).

### Artefatos

- **PR #56 (mergeado):** feat(semgrep-runner): T06 — scan_diff completo (subprocess + X1 mapping + Option B).
- **Prompt T06 v5.1:** `prompt-t06-v5.1.md` em outputs da sessão Chat #32. Appendix de 25 catches (13 v4→v5 + 12 v5→v5.1) para auto-check durante implementação.
- **Sessão Chat #32:** prep T06 completo (v1→v5.1 + plan ratification + DD-T06-23 ratification em halt de 3.A).
- **Tests:** 83 passing total. Baseline 64 pós-T05 + 19 novos (21 test_scan_diff − 2 stubs removidos de test_bootstrap). Reportar count real validou estimativa de Fase 2 (~77; veio 83 por contagem pytest com parametrize expandido).
- **Gate outputs:** pytest 83 passed em 78s; ruff All checks passed!; mypy Success em 8 source files (escopo `src/mcp_servers/semgrep_runner/`).

### Companion edits aplicados

1. `canonical.md` §4.2 — caller invariants (cwd repo root, refs presentes, git ≥ 2.30).
2. `canonical.md` §5.3 — quinto caso (JSON `errors[]` em exit 0 distinto de stderr).
3. `canonical.md` §8.6 — exit code mapping subsection (X1 table).
4. `canonical.md` §5.4 — INVALID_RULE_SET row (exits 7|8) + SEMGREP_EXECUTION_FAILED row clarificada + footnote¹ com pin de versão Semgrep 1.163.0.
5. `README.md` — git ≥ 2.30 prerequisite na setup section.
6. `tasks.md` §T06 AS-13 — psutil → `_pid_alive_windows` (alinha spec à implementação real).

### Housekeeping debt aberto

- Issue separada para `pyproject.toml` exclude OR `# type: ignore[call-arg]` em fixtures `tests/mcp_servers/semgrep_runner/fixtures/recognizers_pack_br/br_nis_log_payload.py` (3 mypy errors pre-existentes de PR #52 T07 prep; fixtures são código-alvo Semgrep, não Python aplicação).

### Próximo passo: T07 — Detector subagent (consumer real de `scan_diff`)

T07 resolverá empíricamente os seguintes itens que T06 preservou como evolution candidates:

- **`repo_root` como parâmetro explícito** (vs cwd implícito DD-T06-3 + DD-T06-19): T07 será o primeiro caller real e expõe se contract implícito é viável em produção ou se Provisão A precisa amendment para inputSchema explícito.
- **Validação cross-component da invariante de findings ordering**: anchor `test_anchor_findings_ordering_path_startline_ascending` exercita a invariante via `tools.scan_diff` direto; T07 consome via FastMCP Client e processa findings sequencialmente — segunda-line de validação que ordering sobrevive serialização Option B.
- **Pattern de wire format Option B em consumer multi-tool**: T07 invoca `policy_reader.check_applicability` + `policy_reader.get_clause` + `semgrep_runner.scan_diff` em sequência; primeiro teste real de Option B cross-server (Detector consome 3 tools de 2 servers e discrimina sucesso vs erro via `errorCode` presence).
- **Use case para `errors[]` non-empty em exit 0**: DD-T06-20 ignora; T07 pode descobrir caso real onde rules dropped silenciosamente afeta classificação. Se emergir, considerar promover Opção B (escalation threshold) ou C (campo `warnings` em scan_metadata) per canonical §7 evolution candidates.

Estimativa T07: 2-3h se Detector for thin orchestrator; 4-5h se houver lógica de decisão complexa (LGPD applicability scoring). Pre-flight T07 vai verificar shape de FastMCP Client multi-server em ambiente local antes de implementação.

## 2026-05-23 — sessão #32 (continuação) — Housekeeping cross-doc pre-T07 (PR #57)

**Foco.** Sessão Chat persistente longa cobrindo, pós-merge T06: inventário dos
débitos catalogados nos handoffs #31 e #32 (este último incompleto na seção de
débitos abertos); redação multi-round dos documentos de plano (v1 mecânicos +
v1 deliberativos → v2 patches → FINAL implementação); 4 rounds Chat ↔ Code
review independente sobre artefato-prompt; ratificação João das 4 decisões
deliberativas (D-1 a D-4); execução Code dos 8 commits internos pre-squash;
squash-merge final via GitHub UI.

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%).**
- **Plan mode externalizado como artefato pre-sancionado.** Code não rodou
  plan-mode ad-hoc com 8 sub-decisões; recebeu documento autossuficiente
  `housekeeping-pre-t07-IMPL.md` (767 linhas) com `old_str`/`new_str`
  byte-exact + grep checks empíricos + halt conditions explícitas + ordering
  ratificado. Code executou top-to-bottom em modo de implementação direta,
  com escalation embutida (halt-and-report em cada divergência). Pattern
  evoluído a partir do plan-mode pattern interno do Code (#23+) — agora o
  plan vive como documento auditável externo, sancionado por multi-round
  review pré-aplicação.
- **Halt-and-escalate em Code review sobre artefato-prompt.** Rounds 1 e 2
  do Code review independente identificaram bloqueadores (R1 heading órfã,
  R2 grep word boundary, R7 audit trail exclusions) que Chat sozinho não
  pegou. Cada halt produziu patch cirúrgico no Chat → revisão por Code →
  ratificação ou novo halt. Severidade decay monotônica em 4 rounds (v1 →
  v2 → FINAL → aplicação): 2 BLOCK em v1, 1 BLOCK em v2, 0 BLOCK em FINAL,
  0 problemas em aplicação.

**Domínio 3 — Claude Code Configuration & Workflows (20%).**
- **`.claude/rules/windows-tooling.md` extendido com ASCII commit
  convention.** Materialização de pattern observado em duas sessões (#28
  Provisão B + #30 PR #55) sobre fricção PS 5.1 + bash HEREDOC + UTF-8 em
  commit messages. Rule é auto-carregada pelo Code em sessões futuras —
  reduzem risco de reinventar a roda. Defense candidate latente: lições
  cristalizadas no learning-log NÃO são carregadas pelo Code em runtime;
  apenas `.claude/rules/` é. Promoção learning-log → rule é movimento
  arquitetural deliberado, não automático.
- **`[tool.mypy]` section materializada com `exclude` regex.** Antes da
  PR #57, `pyproject.toml` não tinha `[tool.mypy]` section — workaround
  era `uv run --with mypy mypy` que respeitava apenas defaults. Edit
  M-4 criou seção com `exclude` apontando para diretório de fixtures
  Semgrep deliberadamente type-incorrect pelo padrão stdlib. Aplicação
  do pattern oficial mypy (docs `mypy.readthedocs.io`): `exclude` para
  diretórios de test data, `# type: ignore` para violations individuais
  em código real. Decisão arquitetural materializada no pyproject.

**Domínio 4 — Prompt Engineering & Structured Output (20%).**
- **Validation-retry loop manual sobre artefato-prompt em 4 rounds.**
  Chat v1 → Code review (R1 + R2 BLOCK) → Chat v2 patches → Code review
  v2 (R7 BLOCK + observações) → Chat FINAL consolidado → aplicação Code
  com 0 issues. Pattern verifiable: cada round catalogou catches por
  classe (estruturais, factuais, smoke check de gates), severidade
  decay monotônico, convergência empírica em 0 issues no round final.
  Custo total ~6h Chat + ~1h Code = ~7h para 8 commits substantivos —
  trade-off ratificado: tempo de prep dobra tempo de implementation,
  mas risk de implementation com surprise crítica decai a zero.
- **Verification-before-inference aplicada a artefato-prompt
  recursivamente.** Chat verificou empiricamente cada `old_str` contra
  anexos enviados por João antes de declarar o plano final. Anexos
  pedidos em vez de inferir (5 arquivos: tasks.md, models.py,
  br_nis_log_payload.py, pyproject.toml, windows-tooling.md + output
  literal mypy). Defense candidate cristalizado em três escalas:
  (i) Chat verifica anexos antes de redigir, (ii) Code verifica
  grep counts pré-aplicação antes de aplicar, (iii) Code review v1
  verifica empiricamente os 9 grep checks declarados pelo Chat v1.

**Domínio 5 — Context Management & Reliability (15%).**
- **Audit trail exclusions em gates de regressão — segunda
  materialização.** Pattern inaugurado em #30 (learning-log +
  session-handoff já excluídos como audit trail intencional). Em #32
  o padrão escalou: gate de `article_source` (P-7) precisou de 5
  exclusões cumulativas — `learning-log.md`, `session-handoff.md`,
  `docs/adr/`, `docs/DESIGN.md` (preserva rename note ADR-0005),
  `src/mcp_servers/policy_reader/models.py` (preserva novo audit
  trail "migration from `article_source`...canonical-sync-E"). Padrão
  generalizado: **gates de regressão são exclusion-aware com dois
  vetores distintos** — (a) edits que preservam tokens originais como
  audit trail intencional (vetor #30), (b) audit trails legítimos
  cross-doc preservam tokens em sites não-tocados pela PR (vetor #32).
- **Error propagation estruturada cross-system entre Chat e Code.**
  Cada Code review v1, v2, FINAL produziu artefato (transcript)
  estruturado por ressalvas numeradas (R1, R2, R7) + classificação
  bloqueante/não-bloqueante + recomendação operacional. Chat absorveu
  o output como input estruturado, não como prosa livre — viabilizou
  patches cirúrgicos endereçando cada ressalva por número. Pattern
  análogo ao `errorCode + message + isRetryable + details` do contrato
  MCP, materializado no protocolo de revisão multi-agente sobre
  artefato-prompt.
- **Provenance via cascading decision.** D-1 ratificado bare cobre
  implicitamente R3 (uniformização de severity em M-5b), porque a
  uniformização só aplica sob a hipótese D-1=bare (regra
  single-purpose por identificador). Sub-decisão dependente herda
  ratificação da decisão superior no grafo de design. Defense
  candidate: ratificação cascading reduz custo de governance em
  decisões interdependentes — pattern transferível para futuras
  prep-sessions com múltiplas DDs encadeadas.

### Decisões fechadas

- **D-1 ratificado bare** (`br-cpf`, `br-cnpj`, etc.). Canonical
  alinhado à convenção tasks.md. Tasks.md, Provisão B (mergeada),
  T07 §Files previstos todos coerentes.
- **D-2 ratificado: mypy + ruff em dev-deps com pin** (`mypy>=1.18`,
  `ruff>=0.13`). Workaround `uv run --with mypy mypy` aposentado;
  agora `uv run mypy` direto funciona em qualquer ambiente após
  `uv sync`.
- **D-3 ratificado: ASCII commit message convention adicionada a
  `.claude/rules/windows-tooling.md`** como seção nova (38 linhas, 4
  sub-seções Principle/Justification/How to apply/Scope).
- **D-4 ratificado Opção A: exclude no `[tool.mypy]`** apontando para
  diretório de fixtures Semgrep. Alternativa Opção B (inline
  `# type: ignore`) rejeitada por escalabilidade (Provisão B + T07 vão
  expandir o pack).
- **D-5 deferido** (sweep regras imutáveis ADR-0001 D4 ↔ CLAUDE.md
  §"Immutable domain rules"). Bloqueante para Milestone C, não para
  T07. Sessão Chat dedicada ~1.5h antes do início de C.
- **Severity uniformization em M-5b** (`error` → `warning` para
  `br-cnpj`) ratificada implicitamente via D-1 bare. Coerente com
  prescrição tasks.md T07 Chat review: "warning para identificadores
  comuns; error apenas se houver razão semântica forte".
- **Catálogo de débitos é também código.** Lição cristalizada em
  Edit M-2: `tasks.md §Companion edits cross-doc` é registry vivo —
  bullets que ficam stale pós-merge de PRs cross-doc (canonical-sync-D
  resolveu §5.1 título; catálogo não foi atualizado) precisam ser
  removidos. Pattern análogo ao "Companion edits cross-doc as living
  debt registry" de `.claude/rules/spec-driven-workflow.md`, mas no
  sentido reverso: limpar débitos *resolvidos* tão importante quanto
  adicionar *novos*. Promoção formal para rule pendente.

### Lessons metodológicas (defense candidates fortes para Capítulo de Método)

1. **Documento de implementação como evolução do plan-mode pattern.**
   Plan-mode interno do Code (`spec-driven-workflow.md`) cobre tasks
   single-Code-session com decisões emergentes ratificadas via GATE 1
   intra-session. Documento de implementação cobre PRs multi-arquivo
   com decisões PRÉ-sancionadas via multi-round Chat ↔ Code review
   externo. Os dois patterns são complementares — plan-mode interno
   para tasks de implementação (T01-T07); documento de implementação
   externo para PRs de housekeeping/governance/refactor. Cristalização
   da distinção como contribuição metodológica forte.

2. **Multi-round Chat ↔ Code review sobre artefato-prompt — convergência
   empírica em 4 rounds.** v1 (2 BLOCK + observações) → v2 (1 BLOCK + ⚠️
   informativos) → FINAL (0 BLOCK) → aplicação (0 issues). Severity
   decay monotônico empiricamente observado em quatro rounds, replicando
   pattern de #28 (cinco rounds) em domínio diferente. Sustenta hipótese
   de #28: triangulação real requer ≥1 round verificacional após cada
   round de fix substancial; review coerência interna ratifica mas pode
   mascarar reinvenção de contrato; review verificacional (que abre
   arquivos reais) é complementar necessário, não redundante.

3. **Gate de regressão exclusion-aware com dois vetores.** Pattern #30
   coberto (audit trail intencional via edit). Pattern #32 acresce:
   audit trails cross-doc legítimos que sobrevivem a edits (DESIGN.md
   ADR-0005 summary rename note, models.py docstring nova). Total cinco
   exclusões cumulativas: `learning-log.md`, `session-handoff.md`,
   `docs/adr/`, `docs/DESIGN.md`, `src/mcp_servers/policy_reader/models.py`.
   Pattern operacional consolidado: gates de regressão grep-based
   precisam de catálogo de exclusões mantido junto com o gate —
   exclusões NÃO são bug, são auditability features.

4. **Provenance multi-camada do artefato-plano.** Sessão #32 produziu 4
   documentos sequenciais com responsabilidades distintas:
   - `housekeeping-mechanical-fixes.md` v1 (503 linhas): 6 edits
     mecânicos com diffs aplicáveis e análise individual.
   - `housekeeping-deliberation.md` v1 (510 linhas): 5 itens
     deliberativos com recomendação fundamentada + alternativas.
   - `housekeeping-patches-v2.md` (254 linhas): 6 patches sobre v1
     endereçando Code review R1+R2.
   - `housekeeping-pre-t07-IMPL.md` FINAL (767 linhas): documento
     consolidado autossuficiente para Code executar.

   Cada documento tem audit trail próprio. Documentos de origem (v1,
   v2 patches) viram histórico Chat sem necessidade de preservação em
   main; FINAL.md é descartável pós-merge (lições absorvidas neste
   learning-log + handoff). Pattern: artefato-plano não é monolito; é
   stream de documentos com semântica de iteração explícita.

5. **Ratificação cascading reduz custo de governance.** D-1 (bare)
   ratificou implicitamente R3 (severity uniformization em M-5b) porque
   uniformização só aplica sob D-1=bare. Pattern transferível para
   futuras prep-sessions: decisões interdependentes podem ser organizadas
   em grafo, com ratificação flowing top-down. Reduz N decisões
   independentes em K decisões com cascata implícita. Documentação
   explícita do grafo de dependências é pré-requisito (feito em
   `housekeeping-deliberation.md` §D-1 ⚠️ trade-off block).

### Métricas operacionais

- **Commits internos pre-squash:** 8 (D-2, M-4, M-1+companion, M-2, M-3,
  M-5, M-6, D-3). Ordering D-2 antes de M-4 ratificada (permite gates
  pós-M-4 usar `uv run mypy` direto).
- **Arquivos modificados:** 6 (architecture-overview.md, tasks.md,
  canonical.md semgrep-runner, models.py policy-reader, pyproject.toml,
  windows-tooling.md). Cobertura cross-doc + src + config + rules.
- **Pytest baseline preservado:** 83 passing (53 policy_reader + 9
  test_bootstrap + 21 test_scan_diff). Zero regression funcional.
- **Mypy pós-PR:** Success em 16 source files (src/) + 8 source files
  (tests reais); 0 source files em fixtures (excluded via [tool.mypy]).
- **Rounds Chat ↔ Code review sobre artefato-prompt:** 4
  (v1 → v2 → FINAL → aplicação). Severity decay monotônica.
- **Custo total:** ~6h Chat + ~1h Code = ~7h. Trade-off prep:Code = 6:1
  para PR de housekeeping cross-doc com decisões deliberativas.
- **Catálogo de débitos resolvidos nesta PR:** 7
  (mypy fixtures BR + architecture-overview §4.4 hedge + canonical
  examples sufixados + canonical §5.1 título stale + tasks.md linha 236
  atribuição + tasks.md linha 387 catálogo stale + models.py:11
  docstring stale). Mais 2 débitos DX/governance (mypy/ruff dev-deps +
  ASCII commit convention).

### Artefatos

- **PR `#57` `chore/housekeeping-pre-t07`** (squash-mergeada em main,
  hash a registrar pós-pull `<TBD>`).
- **8 commits internos pre-squash** (hashes registrados pelo Code):
  - `c34449f` chore(deps): pin mypy and ruff in dev-deps
  - `4e03cfa` chore(mypy): exclude recognizer pack fixtures from mypy
  - `0cecdeb` docs(architecture-overview): remove §4.4 hedge + stale companion debt
  - `d796c52` docs(tasks): cleanup stale §5.1 title debt
  - `6230cc3` docs(tasks): drop stale §5.1 cross-ref from canonical-sync-C
  - `7c41ba5` docs(canonical): align examples to br-identifier bare convention
  - `d8ba621` docs(models): refresh stale article_source docstring
  - `09ddb56` docs(rules): add ASCII commit message convention
- **Documentos produzidos em `/mnt/user-data/outputs/` da sessão Chat
  (audit trail descartável pós-merge):**
  - `housekeeping-mechanical-fixes.md` v1 (503 linhas)
  - `housekeeping-deliberation.md` v1 (510 linhas)
  - `housekeeping-patches-v2.md` (254 linhas)
  - `housekeeping-pre-t07-IMPL.md` FINAL (767 linhas)
- **Code review transcripts** (anexados pelo João via mensagem em Chat
  session #32): review v1 + review v2 + confirmação de aplicação.

### Próximo passo

Sessão Chat #33 — **prep T07 (Detector subagent)**, primeiro consumer
real de `scan_diff` via FastMCP Client.

**Pre-flight verificação direta antes de redigir o prompt T07:**

- Estado real de `src/mcp_servers/semgrep_runner/server.py` pós-T06: que
  tool é exposta? Apenas `scan_diff` ou há mais? Confirmar via leitura
  direta, não inferir.
- Pattern de import do FastMCP Client no projeto: `from fastmcp import
  Client` ou similar? Como T07 vai consumir `scan_diff`? Confirmar
  contra documentação FastMCP 3.x e contra código existente.
- AgentDefinition pattern para Detector — primeira AgentDefinition do
  projeto. Pre-leitura `architecture-overview.md` §5.2 (Detector como
  consumidor de `semgrep-runner`) + canonical.md §1 + `.mcp.json` do
  projeto (mecanismo de exposição cross-process).
- Provisão B (fixture pack BR) já mergeada — Code pode usar como base
  para fixtures de teste do Detector. Confirmar via listagem direta de
  `tests/mcp_servers/semgrep_runner/fixtures/recognizers_pack_br/`.
- Decisão substantiva pré-prompt: T07 é apenas Detector (single
  AgentDefinition) ou também inclui Coordinator stub para invocar o
  Detector? Boundary clarification para escopo da task.

**Custo estimado T07:** prep Chat ~2-3h (multi-round se justificado) +
Code ~3-4h. Pattern análogo a T06: pre-flight ambicioso + plan-mode + GATE
1 + Fase 2 com gates intermediários.

**Débitos deferidos para futuro:**

- **Sweep regras imutáveis** (ADR-0001 D4 ↔ CLAUDE.md §"Immutable
  domain rules") — Chat dedicada ~1.5h antes do início de Milestone C.
  Bloqueante para C, não para T07.
- **Cobertura de detecção em JavaScript/TypeScript** — pós-Milestone B
  gate milestone-level, dentro da janela 15/06-30/06 caso haja capacidade.
- **Promoção de rules emergentes para `.claude/rules/`**:
  catálogo-de-débitos-é-código (cristalizada em #32); audit-trail
  exclusion-aware gates (cristalizada em #30, replicada em #32); plan
  externalizado vs interno (cristalizado em #32). Sessão metodológica
  retrospectiva dedicada quando o número de candidates justificar.

---

**Nota sobre numeração de sessões.** Sessão #32 começou como prep+aplicação
T06 (PR #56, primeira metade) e estendeu para housekeeping cross-doc
pre-T07 (PR #57, segunda metade) sem fechamento intermediário formal. Para
fins de catalogação, esta entrada cobre apenas a segunda metade; a entrada
T06 (PR #56) é anexada separadamente ao learning-log conforme handoff
#32→#33 anterior previa. Sessão #33 está reservada para prep T07.

# Session #33 — 2026-05-23 — T07 Implementation Complete (Milestone B closes)

## Status

- **Branch merged:** `feat/semgrep-runner-T07` → `main`
- **Tests:** 132 passing (83 baseline + 49 T07), 0 failed, 0 skipped
- **mypy strict + ruff:** clean em 16 src/ files
- **Milestone B implementation:** completo (T05 + T06 + T07 + housekeeping #57)
- **Rule set BR:** 6 regras em `mcp_servers/semgrep_runner/rules/` (sem `_placeholder.yaml`)

## Conceitos da prova exercitados

### D1 — Agentic Architecture & Orchestration (27%)
- AgentDefinition shape preparation (mental model — materialização deferred a Milestone C).
- Coordinator-subagent pattern: discussão prévia + decisão de não materializar Coordinator stub em T07 (escopo do MVP).
- Subagent context isolation princípio aplicado mentalmente (Detector recebe `base_ref`/`head_ref` explícitos quando vier).

### D2 — Tool Design & MCP Integration (18%)
- Rule pack como **data** consumida pelo MCP tool `scan_diff`; design das regras afeta downstream shape de findings.
- `metadata.category` + `metadata.identifier` schema antecipando consumo pelo Classifier em Milestone C via RF-003.
- `.mcp.json` global vs AgentDefinition scope per-subagent: princípio "expose broadly, restrict narrowly" ratificado.
- FastMCP Client vs direct `tools.scan_diff` call: T06 estabeleceu direct call como pattern default; Client reservado para E2E wire format validation (AS-11 T06).

### D4 — Prompt Engineering & Structured Output (20%)
- **Multi-instance review canônico** materializado: 2 reviews independentes da v1 (19 catches absorvidos em v2), 2 reviews da v2 (17 catches absorvidos em v3), 1 review da v3 (1 blocker + 3 refinamentos em v4).
- Iteração de prompt versionada v1→v4 espelhando T06 (v1→v5.1).
- Subset assertion style (`.claude/rules/test-strategy.md` autoload) aplicado em AS-1..AS-6 (NEW DD-T07-AS3); strict equality reservado para AS-7/8/9 e ANC-3.
- JSON schema implícito em metadata schema das regras (category + identifier slugs).
- Latin square design no pack BR como técnica de cobertura mínima — transitividade implícita declarada como gap explícito.

### D5 — Context Management & Reliability (15%)
- **Tasks.md como scratchpad canonical authoritative** — handoff e learning-log são audit trail. Em divergência, tasks.md vence (lição do redirect macro: handoff dizia "T07 = Detector", tasks.md prescrevia rule pack).
- Verification-before-inference recursivo: errei em 3 escalas (path `src/.../rules/` por simetria visual; handoff §5.2 vs §5.3; T07 escopo macro).
- Halt-and-escalate funcionando: Code escalou DD-T07-3a via GATE 1 ao descobrir empíricamente que 4-pattern produzia findings extras (compositional behavior diferente de component behavior).

## Decisões substantivas (DDs)

| ID | Decisão | Locus |
|----|---------|-------|
| DD-T07-3a | **1-pattern per rule** (não 4-pattern como v4 prescrevia); Latin square strict; transitividade gap explícito | GATE 1 Code (empíria 1.E_intra) |
| DD-T07-3b | Sintaxes DSL específicas ratificadas empíricamente em 1.E(a)-(d) | Pre-flight Code |
| NEW DD-T07-AS3 | AS-1..AS-6 subset assertion (`"br-X" in rule_ids`); strict count reservado para AS-7/8/9 e ANC-3 | GATE 1 Code (`.claude/rules/test-strategy.md`) |
| DD-T07-4 | WARNING × 5; ERROR × 1 (br-cns-saude per LGPD Art. 11) | handoff §2 |
| DD-T07-5 | Mensagem PT-BR template documental | GATE 1 |
| DD-T07-13 | Só forma canonical (`cns_saude`, `nis`, `titulo_eleitor`); aliases pós-MVP | GATE 1 |
| DD-T07-16 | `metadata.category: pii-collection-br` + `metadata.identifier: <slug>` | GATE 1 |

## Companion edits aplicados

- `docs/tasks.md` §T07 AS-9: `line_start` → `start_line` (bug pré-existente herdado por v1 do prompt).
- `docs/tasks.md` §T07 AS-1..AS-6: "exatamente um finding" → "ao menos um finding" (alinha subset assertion convention).
- `tests/mcp_servers/semgrep_runner/fixtures/recognizers_pack_br/README.md` §Composição: shape sync `fixture_pack_br -> Path` → `br_pack_repo -> tuple[Path, str, str]`.

## Defense candidates metodológicos (para TCC)

1. **Tasks.md como scratchpad canonical authoritative**. Handoff e learning-log são audit trail. Em divergência, tasks.md vence. Redirect macro de T07 (handoff dizia "Detector", tasks.md prescrevia rule pack) materializa o princípio.

2. **Multi-instance review canônico exige diversidade de framing**, não apenas múltiplas execuções da mesma instrução. Review B explícito como "clean session, verify-everything-against-source" detectou blockers que Review A (contexto T06) não pegou. Single-pass review do mesmo Chat que produziu v1 teria deixado passar pelo menos 2 blockers.

3. **Verification-depth stratification.** Layer-1 review (consulta docs) converge para refinamentos; layer-2 review (lê código) surface blockers; layer-3 (execução empírica via pre-flight Code) surface compositional behavior errors. Severity decay monotônica quantitativa pode mascarar blockers se profundidade varia por round.

4. **Compositional verification ≠ component verification.** Pre-flight de v4 validou primitivas Semgrep DSL em isolation (1.E(a)-(d), cada pattern contra seu fixture Latin-square). Code descobriu empíricamente que composite 4-pattern emergia behavior diferente (3 findings em CNH attribute fixture porque self.cnh: str = "" + driver.cnh = ... em fixture). Pre-flight deveria incluir "test as deployed" sub-fase.

5. **Correções carregam risco proporcional ao scope da mudança.** Rewrite de §2 em v3 (corrigindo P1-#2 smoke pollution de v2) introduziu novo blocker P1-#1 v3 (import path `from tests.mcp_servers...` quebra em Python standalone porque `tests/__init__.py` não existe). Quando o foco está no defeito original, a superfície empírica completa não é re-verificada.

6. **prep:Code ratio escala não-linearmente com complexity gradient da task.** T06 (framework integration) foi ~1h Chat prep + 7h Code = 1:7. T07 (detection semantics herdando framework T06 pronto) foi ~6h Chat prep + 1h Code = 6:1. Tasks de detection-semantics com Latin square implícito justificam prep mais profunda; tasks de framework integration concentram custo em Code empírico.

7. **Estimativa Code dispersa.** v4 prescreveu 4-6h; GATE 1 Code revisou para 2.5-3.5h após DD-T07-3a 1-pattern decision; real foi ~1h. **Superestimação 2.5-6×.** Uncertainty premium da multi-round Chat prep não se traduz proporcionalmente em Code time. Defense: prep:Code ratio reflete verification-depth-modes distribution, não cost-of-rework amortization sozinho.

8. **prep:Code não é só amortização de cost-of-rework Code-side — é distribuição de verification-depth-modes**. Chat faz layer-1 + layer-2 documental; Code faz layer-3 empírica. Cada modo pega catches que os outros não pegam.

## Artefatos da sessão

- `prompt-t07-v1.md`, `v2.md`, `v3.md`, `v4.md` (versioned, em outputs Chat).
- Plan GATE 1 do Code com 3 ratificações.
- PR `feat/semgrep-runner-T07` merged em `main` (2 commits split code-vs-docs).
- 6 regras YAML BR em produção.
- `tests/mcp_servers/semgrep_runner/test_recognizers_br.py` com 15 funções, 49 pytest items.
- `tests/mcp_servers/semgrep_runner/conftest.py` estendido com `br_rules_dir` + `br_pack_repo`.

## Drift catalogados (não bloqueantes — débito para housekeeping)

- **Handoff #32→#33 + learning-log #32 declaravam "T07 = Detector subagent"**; tasks.md §T07 prescrevia rule pack BR. Audit trail divergente de scratchpad canonical. Ratifica princípio: tasks.md vence.
- **Micro-drift §5.2 (Triager) vs §5.3 (Detector)** no handoff #32→#33. Não bloqueante.
- **CLAUDE.md §Status flags stale**: declara "64 passing (53 policy_reader + 11 semgrep_runner + AS-1..AS-8)". Real pré-T07 era 83; pós-T07 é 132. Atualizar em housekeeping pre-T08 ou pós-Milestone B gate.

## Métrica cumulativa T07

- **4 rounds Chat** (v1→v4) + 1 round Code (GATE 1).
- **~40 catches absorvidos cumulativamente** (19 v1→v2; 17 v2→v3; 4 v3→v4; 1 v4→Code).
- **Tempo total sessão #33**: ~6h Chat prep + 1h Code = ~7h. Comparável ao T06 e ao housekeeping #57.
- **Custo de blockers descobertos por layer**: layer-2 review (Review B) detectou 2 blockers; layer-3 (Code empírico) detectou 1 blocker (4-pattern compositional behavior). Sem essas duas camadas, T07 entraria em produção com 3 problemas estruturais.

## Próximo passo

- **Gate milestone-level Milestone B**: auditoria de completude vs proposta-tcc2.md §B; checklist de critérios; decisão sobre direct progression vs housekeeping pre-C.
- Sessão #34 candidate: gate audit OU pre-C housekeeping OU authoring direto de tasks.md §Milestone C. Decidido no handoff #33→#34.

# Session #34 — 2026-05-24 — Gate Milestone B: descoberta de defeito em scan_diff via stdio transport

## Status

- **Branch aberta:** `chore/gate-milestone-b-rule-set-fixture` (não mergeada).
- **Commits na branch:** `19e0536` (pack alternativo synthetic_iban), `84672a5` (gate exercise script).
- **Gate Milestone B:** FAIL — não por defeito do gate, mas por defeito empírico em `scan_diff` que o gate revelou.
- **Tests:** 132 passing inalterado (defeito invisível ao pytest existente).
- **Decisão de fluxo:** fix em PR separada (sessão Code #35); ADR pos-hoc após escopo de fix consolidado; re-rodar gate após merge do fix.

## Conceitos da prova exercitados

### D2 — Tool Design & MCP Integration (18%)
- **In-memory client vs stdio transport client — distinção fundamental.** AS-11 do T06 valida envelope shape via `Client(server.mcp)` no mesmo processo Python — sem serialização, sem subprocess, sem pipe stdio real. Para validação de wire format protocolar fiel, stdio transport é o único caminho. AS-11 deu falsa segurança sobre comportamento sob transport real; defeito do `subprocess.run` em `_resolve_ref` só se manifesta quando o servidor MCP roda como subprocess do cliente externo com stdin pipe herdado.
- **MCP Inspector CLI v atual — limitação de client-side request timeout.** Default insuficiente para cold start de `scan_diff` em Windows; override via `MCP_SERVER_REQUEST_TIMEOUT` não teve efeito documentado. FastMCP `Client(timeout=...)` expõe o parâmetro explicitamente, viabilizando exercise fiel sem o cliente Node.
- **Equivalência cliente↔cliente sob mesma surface protocolar.** Argumento que justifica MCP como protocolo aberto materializado empiricamente: trocar Inspector (Node) por FastMCP Client (Python) preserva fidelidade protocolar — ambos consomem o mesmo wire format stdio contra o mesmo servidor.
- **`StdioTransport(command, args, env, cwd)` da FastMCP 3.2.4** — API confirmada via inspeção empírica (`inspect.getsource`); aceita `cwd` e `env` parametrizáveis, viabilizando exercise com rule set alternativo via `SEMGREP_RUNNER_ROOT` injetado e cwd apontando para repo Git de fixture.

### D5 — Context Management & Reliability (15%)
- **Error propagation defeituoso — `TimeoutExpired` classificada como business error.** `tools.py:_resolve_ref` captura `subprocess.SubprocessError` (superclass de `TimeoutExpired`) e traduz para `None` → `GIT_REF_NOT_FOUND` (business, isRetryable=False). Cadeia inteira: bug de portabilidade Windows-stdio (transient, subprocess deadlock por handle inheritance) → erro semântico de ref inexistente (business, irrecuperável). Anti-pattern canônico que D5 cobra em "transient vs business vs permission errors". Fix correto distingue classes: `TimeoutExpired` → transient (eventualmente retryable ou system error), `CalledProcessError` exit-code-mapped → business. Fix mínimo (`stdin=DEVNULL`) elimina manifestação; fix arquitetural separa classes.
- **Progressive narrowing de hipóteses na sessão.** Sequência metodológica empírica: suspeita ampla ("MCP timeout") → isolamento de transport (Inspector vs FastMCP Client) → isolamento cliente vs servidor (script vs Inspector) → isolamento cliente MCP vs invocação direta (`scan_diff` standalone com `state` injetado manualmente) → revelação do defeito empírico no transport via comparação `subprocess.run` com vs sem `stdin=DEVNULL`. Cada passo eliminou um eixo. Pattern de escalation que D5 cobra: não chutar solução, isolar onde o erro está.
- **Handle inheritance em pipe stdio + subprocess sem `stdin=` explícito.** Causa raiz invisível ao código-fonte do consumidor: o defeito está na interação entre transport stdio do MCP (parent recebe pipe stdin do cliente) + comportamento default do `subprocess.run` (filho herda handles do parent quando `stdin=` não é especificado). Pytest com in-memory client não tem pipe stdin a herdar; defeito não aparece. Categoria de bug que **só** gate manual com transport real pode capturar.

### D3 — Claude Code Configuration & Workflows (20%)
- **`.claude/rules/review-patterns.md` Justificativa #2 materializada.** "Exercise contra wire real expõe debt que pytest cobre por coincidência" — citada literalmente pelo Code no halt-and-escalate. Pattern de project-level rule consumida via CLAUDE.md hierarchy aplicada como argumento de halt structurally significant.
- **Disciplina de "gate descobre defeito → Chat planeja → Code executa".** Pattern empírico das sessões #21-#25 reafirmado: Code identifica defeito + escopo de fix + propõe sequência, mas para na fronteira "modificar `src/`" (proibido pelo prompt da sessão de gate); Chat decide direção; sessão Code subsequente executa. Disciplina materializada via halt-and-escalate, não via tentativa unilateral de Code resolver tudo na mesma sessão.

## Decisões de sessão

- **Pack alternativo `alternative_rule_set_synthetic`** criado conforme planejado. Layout ratificado: subdir `rules/` (alvo de `SEMGREP_RUNNER_ROOT`) + snippet + README no pack root. Smoke check verde antes do exercise (`load_rules` apontando para o pack carrega regra `synthetic-iban` sem erro; `rules_version = sha256:ffb1ac00...`).
- **Mudança de mecanismo do exercise**: Inspector CLI → FastMCP Client via stdio transport. Argumento defensivo: client-side timeout default do Inspector insuficiente; override via env var sem efeito; FastMCP `Client(timeout=...)` é cliente MCP Python contra mesmo servidor via mesmo wire format stdio. Equivalência cliente↔cliente preserva fidelidade protocolar.
- **Caminho 4** (Code redige o script com repo em contexto) escolhido sobre Caminho 1 (in-memory client), Caminho 2 (eu redijo stdio script), Caminho 3 (cavar Inspector). Code tem visibilidade da API exata da FastMCP 3.2.4 instalada e do pattern AS-11 para referência negativa (o que NÃO replicar).
- **Próximo fluxo decidido**: fix em PR separada com tests novos primeiro; ADR pos-hoc após escopo de fix consolidado (pode aparecer mais loci do mesmo defeito); ADR-0001 Decision 2 amendment é precedente projetual de ADR retroativo. Branch atual `chore/gate-milestone-b-rule-set-fixture` mantida aberta — ela existe como evidência da descoberta, não como deliverable; merge dela vem **junto** ou **depois** do merge do fix.
- **Tests novos do fix inline em `test_scan_diff.py`** como AS-14, complementar a AS-11. Razão: AS-14 não é feature nova, é cobertura empírica do mesmo contrato sob cliente faltante. Agrupar por componente sob teste, não por mecanismo de teste.

## Artefatos da sessão

- Branch `chore/gate-milestone-b-rule-set-fixture` (não mergeada):
  - `tests/mcp_servers/semgrep_runner/fixtures/alternative_rule_set_synthetic/rules/synthetic_iban.yaml`
  - `tests/mcp_servers/semgrep_runner/fixtures/alternative_rule_set_synthetic/synthetic_iban_function_param.py`
  - `tests/mcp_servers/semgrep_runner/fixtures/alternative_rule_set_synthetic/README.md`
  - `scripts/gate_milestone_b_exercise.py` (artefato de exercise, não teste pytest)
- Diagnóstico empírico do Code (apagado após uso, registrado prosa-only no halt):
  - `subprocess.run([git, ...], cwd=cwd, capture_output=True, text=True, timeout=5)` → timeout, partial_stdout=""
  - `subprocess.run([git, ...], cwd=cwd, capture_output=True, text=True, timeout=5, stdin=subprocess.DEVNULL)` → rc=0, stdout=<sha>
- Outputs Chat extensos: prompt de pack (com delta pós-pre-flight), prompt de gate script, três rodadas de diagnóstico de timeout, halt-and-escalate report do Code, plano de sequência pós-descoberta.

## Catches do gate (não bloqueantes para sessão #35)

| # | Item | Severidade | Locus |
|---|------|-----------|-------|
| 1 | `summarize_phase` fallback `scan_metadata.base_ref or base_ref` em `gate_milestone_b_exercise.py:168-169` — INV-5 mede "input refs bem formados" se scan retornar erro, não strictamente "servidor ecoou refs resolvidos". Nuance metodológica a registrar no gate report eventual. | Cosmético | `scripts/gate_milestone_b_exercise.py` |
| 2 | Verificar se `subprocess.run` do próprio Semgrep em `tools.py` também sofre do mesmo handle inheritance — provavelmente sim, mas trava menos visível por `--metrics=off` e config mais auto-contida. Pre-flight do prompt de fix deve verificar. | Substantivo, defensivo | `src/mcp_servers/semgrep_runner/tools.py` invocação Semgrep |
| 3 | `_is_shallow_repository` (também `subprocess.run` git) tem o mesmo padrão; fix se aplica simetricamente. | Substantivo | `src/mcp_servers/semgrep_runner/tools.py:_is_shallow_repository` |

## Métrica acumulada sessão #34

- **Tempo Chat:** ~4h prep + diagnóstico (estimativa).
- **Tempo Code:** ~1h (pack + gate script + halt-and-escalate report).
- **Ratio:** ~4:1 Chat:Code mantido.
- **Rounds de prompt:** 2 prompts grandes para Code (pack, gate script) + 1 prompt curto de diagnóstico (probe.py via heredoc PowerShell).
- **Catches por layer:**
  - Layer-1 (docs/prompt): catch do layout do pack (subdir rules/ ratificado em Chat pré-execution); catch da divergência `SEMGREP_RUNNER_ROOT` (Code halt-and-escalate em pre-flight).
  - Layer-2 (script): catch do `summarize_phase` fallback durante review Chat do output do Code.
  - Layer-3 (execução empírica): **defeito de portabilidade Windows-stdio descoberto exclusivamente aqui** — pytest, code review, e prompt design todos invisíveis a esta categoria de bug.

## Próximo passo

Sessão Chat #35 — prep do prompt Code para PR de fix em `tools.py`. Pre-leitura conforme handoff #34→#35. Escopo: `stdin=subprocess.DEVNULL` em ambos `subprocess.run` que invocam git (`_resolve_ref`, `_is_shallow_repository`) + verificação se `subprocess.run` do próprio Semgrep tem mesmo padrão (provavelmente sim — incluir preventivamente). Separação `TimeoutExpired` vs `CalledProcessError` para classificação correta de error class (D5 transient vs business): incluir na mesma PR ou diferir? Decisão de sessão #35. AS-14 inline em `test_scan_diff.py` validando `scan_diff` sob stdio transport real (Client externo, não in-memory). Após merge: re-rodar `scripts/gate_milestone_b_exercise.py` esperando PASS; redigir `docs/process/milestoneB.md`; ADR pos-hoc; mergear branch atual `chore/gate-milestone-b-rule-set-fixture` em conjunto com (ou após) PR do fix.

Custo estimado distribuído em 2-3 sessões: ADR ~1h Chat dedicada (pos-hoc, sessão própria); PR de fix ~1h Code + ~30min Chat review; re-rodar gate ~5min; redigir milestoneB.md ~45min; atualizar este learning-log com PASS confirmation ~15min.

# Learning-log entry — sessão #35

**Para aplicar:** apendar este conteúdo ao final de `docs/process/learning-log.md`, abaixo da entry #34. Squash hashes a popular pós-merges (PR #59 e PR chore subsequente).

---

## 2026-05-24 — sessão #35 — T-fix scan_diff stdin isolation (PR #59) + gate Milestone B PASS empírico

**Foco.** Sessão Chat de prep prompt T-fix v1→v3 com multi-instance review canônico + Code aplicação da PR #59 (`fix/scan-diff-stdin-isolation-windows-stdio`) + briefing T-gate-script-fix para patch cirúrgico ao gate script + validação empírica do gate Milestone B PASS contra branch combinada local. Pattern de fechamento de cadeia: defeito empírico descoberto na #34 → fix + cobertura unit na #35 → gate empírico re-rodado pós-fix → defeito de aferição emerge (mascarado por defeito upstream) → patch → PASS empírico.

### Status

- **PR #59** (`fix/scan-diff-stdin-isolation-windows-stdio` → main, squash hash `<TBD — preencher pós-merge>`): 1 commit `6f9bc44`. Diff: `tools.py +3 / test_scan_diff.py +134`. Status ao fechar #35: aprovada pelo Chat; aguardando merge manual.
- **Branch local `chore/gate-milestone-b-rule-set-fixture`**: 3 commits internos (`19e0536` pack alternativo + `84672a5` gate script v1 + `34b6c05` patch script #35). Não pushed; aguarda rebase pós-merge PR #59 + abertura de PR própria.
- **Tests:** 134 passing esperado em Windows local pós-merge PR #59 (132 baseline + AS-14 cross-platform + AS-14b Windows-only); 133 em Linux/macOS (AS-14b skipped).
- **Gate Milestone B:** PASS empírico contra branch combinada `test/gate-on-fix-v2` (5/5 invariantes verdes). Evidência consolidada em `gate_b_output.json` (untracked working dir).
- **mypy strict + ruff:** clean.

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1.6 Task decomposition — bundle vs split via review independente.** Decisão load-bearing de **deferir Fix-4 inteiro** (separação `TimeoutExpired` vs `OSError` vs business nos wrappers git) para ADR-0011 + PR posterior. Trigger: convergência de dois reviews independentes da v2 do prompt (R1 C5 + R2 N-C1) mostrando type breakage arquitetural — Fix-4 retornar ErrorEnvelope dos helpers quebra type contract de `_resolve_ref → str | None` e `_is_shallow_repository → bool`; callers em `scan_diff` esperam `is None`, não Pydantic object. Solução requer signature change OU custom exception types raised + caught — decisão arquitetural não-trivial que merece ADR antecedente. Bundle inadequado dentro de PR mecânica de fix. Materializa exam guide *"selecting task decomposition patterns appropriate to the workflow"*. Defense candidate forte: quando decisão arquitetural não-trivial emerge dentro de PR mecânica, split + defer + ADR; não force bundle.

- **D1.7 Session state management — validação antecipada via branch temporária descartável.** Pattern de criar branch `test/gate-on-fix-v2` localmente combinando `fix/scan-diff-stdin-isolation-windows-stdio` + `chore/gate-milestone-b-rule-set-fixture` (não-pushed) + rodar gate + descartar. Reduz risk pós-merge da PR #59 sem comprometer trunk autoritativo. Análogo conceitual a `fork_session` aplicado ao Git workflow. Sequência empírica: PR #59 fix + AS-14b unit cobre uma propriedade (timing); branch combinada + gate empírico cobre outra (RF-008 wire-real) — ortogonais, não substituíveis (ver D5 abaixo).

- **D1.5 Hooks — `.claude/rules/` materializadas como instruction layer.** Briefing T-gate-script-fix citou `.claude/rules/review-patterns.md` Justificativa #2 ("exercise contra wire real expõe debt que pytest cobre por coincidência") como ancoragem do diagnóstico. Pattern de project-level rule consumida via CLAUDE.md hierarchy aplicada como argumento de design.

**Domínio 2 — Tool Design & MCP Integration (18%)**

- **D2 Tool description anatomy — convergência > consistência local.** Pin 2 da Code session #35 venceu inclinação do Chat sobre forma do assertion INV-1 do gate. Chat propôs `endswith("rules.<bare-name>")` baseado em convenção de diretório do projeto. Code clean leu `test_recognizers_br.py:36-39` e identificou idioma efetivamente usado nos tests existentes: `_short_rule_id(finding) = rid.rsplit(".", 1)[-1]`. Code propôs alinhamento ao idioma do projeto via `rsplit(".", 1)[-1] == "<bare-name>"` em vez do `endswith`. Chat ratificou. Defense candidate adicional: prompts T-* devem instruir Code a verificar convenções locais antes de aplicar proposições do Chat. Pattern "Code lê + propõe align" produz código melhor que "Chat infere + Code aplica".

- **D2 isError flag — Option B materializado em wire real (não in-memory).** Gate Milestone B é o primeiro exercício empírico contra wire stdio real do projeto. AS-11 + 132 tests baseline usam `Client(server.mcp)` in-memory; gate usa `StdioTransport(command=sys.executable, args=["-m", "mcp_servers.semgrep_runner.server"])` com Client externo. Wire format Option B (isError=false uniforme; discriminação via presença de errorCode em structuredContent) validado empíricamente em ambos paths (success com findings e potencial error). INV-4 (wire is_error False em ambas as phases) deu PASS pré-patch — confirma que Option B funciona consistentemente sob transport real.

- **D2 errorCode discrimination + canonical shape.** Defeito de leitura de campo no `summarize_phase` (lia `rules_version`/`semgrep_version` de `scan_metadata` aninhado em vez de top-level no structuredContent) ilustra que conhecimento empírico do contract canonical §5.1 importa. Patch alinhou leitura ao shape declarado: ambos os campos são irmãos de `scan_metadata`, não filhos.

- **D2 MCP server configuration — env var injection via StdioTransport.** RF-008 (substituibilidade de rule set via `SEMGREP_RUNNER_ROOT`) validado empíricamente: Phase 1 spawn sem override → loader resolve default BR rule set; Phase 2 spawn com `SEMGREP_RUNNER_ROOT` override → loader resolve pack alternativo synthetic_iban. `rules_version` distinto entre phases (INV-2 PASS) prova que o env injection funcionou.

**Domínio 4 — Prompt Engineering & Structured Output (20%)**

- **D4 Multi-instance review canônico com diversidade de framing.** Trajetória v1→v2→v3 do prompt T-fix absorveu 30+ catches em 3 rounds independentes. Dois reviewers diferentes para a v2:
  - **R1 (clean session)** — sem contexto da #34. Pegou catches factuais e arquiteturais: C1 comando `git rev-parse` faltando `^{commit}`; C2 errorCodes em `_envelope.py` (não `errors.py`); S1 Fix-4 reduzido a 2 classes (CalledProcessError unreachable sem `check=True`); S4 DD-Tfix-1 cerimonial.
  - **R2 (sessão #34 que diagnosticou)** — com contexto profundo. Pegou catches de design e cobertura: C1 AS-14 cross-platform como falso verde em Linux/macOS; C2 mecânica vendida como certeza fabricada; C4 env={} risk em StdioTransport.
  - **Convergência crítica:** R1 C5 + R2 N-C1 ambos mostraram que Fix-4 era type-broken arquiteturalmente. Single-instance review não pegaria a intersecção. Defense candidate forte: diversidade de framing (não só múltipla execução) é o que produz cobertura real em multi-instance review.

- **D4 Calibração de cerimônia proporcional à complexidade.** Comparação intra-sessão #35:
  - **Prompt T-fix v3** (PR #59): ~470 linhas; 9 Pins; 2 DDs; GATE 1 estruturado com 7 outputs esperados; 11 halt-triggers numerados. Custo: feature + design + cobertura nova.
  - **Briefing T-gate-script-fix**: ~180 linhas; 4 Pins simples; 1 DD; GATE 1 leve com 6 halt-triggers. Custo: patch cirúrgico com 2 loci e diff literal.
  - Razão proporcional. Skill discriminada do exam guide: *"dynamic adaptive decomposition based on intermediate findings"*. Tratar todas as tasks com o mesmo cerimonial é miscalibração.

- **D4 Prompt como artefato auditável + iteração versionada.** v1 (520 linhas) → v2 (640) → v3 (470). Changelog explícito em cada versão. Trajetória bate com pattern empírico T06 v1→v5.1 e T07 v1→v4: crescimento em rounds intermediários quando catches substantivos emergem; encolhimento na convergência quando escopo se cristaliza. v3 é tipicamente última iteração; convergência observada na #35.

**Domínio 5 — Context Management & Reliability (15%)**

- **D5 Defeito empilhado em layers — pattern canônico materializado.** Sequência empírica completa em duas sessões sequenciais:
  1. **132 tests passing** (cobertura unit completa pré-#34) — defeito invisível.
  2. **Gate Milestone B #34** (cliente externo via stdio transport) — defeito de `subprocess.run` sem `stdin=` emerge.
  3. **PR #59 fix + AS-14b** — corrige manifestação + adiciona regression unit Windows-only.
  4. **Gate Milestone B re-rodado pós-fix #35** — expõe defeitos de aferição do `summarize_phase` que estavam mascarados (script lia campos de lugar errado, mas gate falhava antes de chegar à leitura).
  5. **Patch ao script + Gate Milestone B pós-patch** — 5 invariantes verdes; cobertura unit + cobertura E2E ambas verdes simultaneamente.
  - Layer-1 (transport) e layer-2 (script de aferição) defeitos só ambos visíveis após resolver layer-1 primeiro. Defense candidate forte para Capítulo de Método: validação de cobertura tem que assumir que defeitos podem estar empilhados; PASS em um nível não atesta correção em outros níveis.

- **D5 Honestidade epistêmica em §2 do prompt.** v2 reescreveu §2 com hipótese explícita ("hipótese principal: handle inheritance do anonymous pipe Windows interfere com `subprocess.Popen.wait()`") em vez de afirmação fabricada ("git aguarda input"). Razão: git `rev-parse --verify` não lê stdin; explicação original era especulativa. v3 manteve. CLAUDE.md immutable rule de honestidade epistêmica materializada em artefato de prompt. ADR-0011 pos-hoc cobrirá caracterização Win32 fina; esta PR não vende o fix como resolução semântica completa — só elimina manifestação atual. Commit message e PR description #59 codificam essa distinção em §2.4 do prompt.

- **D5 Misclassificação `TimeoutExpired → GIT_REF_NOT_FOUND` documentada como débito conhecido.** PR #59 elimina a *manifestação* (handle inheritance) mas não corrige a *estrutura* (TimeoutExpired colapsada como business). Decisão de deferir Fix-4 ratifica que essa distinção merece registro explícito — commit/PR description deixam claro o escopo. ADR-0011 + PR posterior endereçam o eixo de design.

- **D5 Insight emergente — cascading inheritance em sub-processes do semgrep-core.** R-3 da Code session #35: mesmo com Fix-3 (stdin=DEVNULL no semgrep subprocess), o semgrep propriamente dito spawna sub-processes (semgrep-core, file scanners) que herdam handles do semgrep parent. Em teoria, handle inheritance poderia propagar para sub-sub-processes. Empíricamente não vimos hang com fix aplicado; é ortogonal ao defeito atual. Input registrado para ADR-0011 (E-1) cobertura Win32 fina.

### Decisões load-bearing

1. **Fix-4 deferido inteiramente para ADR-0011 + PR posterior.** Critério: type breakage arquitetural confirmado por dois reviews independentes (R1 C5 + R2 N-C1). PR #59 mantém escopo cirúrgico (Fix-1/2/3 + AS-14 + AS-14b + Companion opcional). Misclassificação `TimeoutExpired → GIT_REF_NOT_FOUND` documentada como débito conhecido em §2.4 do prompt + commit message + PR description. Precedente projetual de ADR pos-hoc: ADR-0001 D2 (Presidio→Semgrep), ADR-0004 (uv migration).

2. **AS-14 cross-platform + AS-14b Windows-only (split por propriedade testada).** AS-14 valida happy path sob StdioTransport real (cross-platform). AS-14b valida invariante de timing (`elapsed < 10s`) — Windows-only via `@pytest.mark.skipif(sys.platform != "win32", ...)`. Razão: defeito é Windows-stdio específico; AS-14 cross-platform como única cobertura seria falso verde em Linux/macOS CI futuras (handle inheritance não causa hang em POSIX); AS-14b explicitamente regressão. Naming `test_as14b_*` alinha com AS-13 precedent (Windows-only test que validates mechanism invariant).

3. **Threshold AS-14b = 10.0s.** Análise factual: defeito é ~22-23s (10s `_is_shallow` timeout + 10s `_resolve_ref(base)` timeout + 2-3s cold-start); success path é ~5-8s (2-3s cold-start + <1s cada git rev-parse + 1-3s scan); margem 10s separa claramente sem rejeitar CI fria. Risk de flake em CI Windows extremamente fria → ajustar em PR follow-up se materializar.

4. **Bare-name match para INV-1 via `rsplit(".", 1)[-1]` (não `endswith`).** Pin 2 da Code session #35 venceu inclinação Chat. Razão: idioma do projeto (`_short_rule_id` em `test_recognizers_br.py:36-39`) usa `rsplit`; convergência cross-código reduz surface de drift. Aplicado em patch ao gate script (`34b6c05`).

5. **1 commit único na PR #59 (não 2-commit split).** Pin 6 da Code session #35 confirmou que "2-commit split code-vs-docs" não está codificado em `.claude/rules/git-conventions.md` — era preferência do prompt, não regra. Com DD-Tfix-1 (Companion-1 CLAUDE.md status flag) deferido por escopo, não havia commit-docs separado de qualquer forma.

6. **Companion-1 deferido para housekeeping própria.** CLAUDE.md `§Status flags` drift ≥6 linhas em 3 bullets distintos (não só contagem de tests). Critério "≤2 linhas" não satisfeito. Encaminhamento: sweep housekeeping própria antes de Milestone C arrancar.

7. **Patch ao gate script aplicado diretamente em `chore/gate-milestone-b-rule-set-fixture`** (opção (a) do briefing). Audit trail limpo; branch chore é onde o script vive autoritativamente. `test/gate-on-fix-v2` é descartável (criada para validação local).

### Defense candidates emergentes (cumulativos com sessões prévias, registrar para Capítulo de Método)

- **Defeito empilhado em layers requer cobertura de aferição empírica em cada layer.** Pattern materializado em duas fases sequenciais (#34 descobre layer-1; #35 corrige layer-1 + descobre layer-2 + corrige layer-2). PASS em pytest unit nunca atesta correção em layers downstream; gate empírico com wire protocolar real é cobertura independente, complementar, não substituível.

- **Convergência cross-código vence consistência local em decisões de naming/idioma.** Pin 2 da #35 ratificou empíricamente — Chat propõe baseado em inferência; Code lê convenção real do projeto e propõe align. Pattern operacional: prompts T-* devem instruir Code a verificar convenções locais antes de aplicar proposições do Chat.

- **Validação antecipada via branch temporária combinada é cheap insurance pré-merge.** Pattern `test/gate-on-fix-v2` = `fix/<branch>` + merge `chore/<related-branch>` + validar + descartar. Análogo conceitual a `fork_session` aplicado ao Git workflow. Aplicar quando há dependência entre PRs ainda não mergeadas.

- **Calibração de cerimônia proporcional à complexidade da task.** Briefing cirúrgico (T-gate-script-fix ~180 linhas) vs prompt elaborado (T-fix v3 ~470 linhas) na mesma sessão demonstra que cerimônia uniforme é miscalibração. Skill discriminada do exam guide D4.

- **Type breakage emerge em pseudo-código elaborado, não em prompt abstrato.** v1 do T-fix mantinha Fix-4 abstrato; v2 elaborou pseudo-código concreto e o type breakage emergiu (E em ambos reviews). Pattern operacional: prompts que cobrem mudança de signature ou contract devem incluir pseudo-código concreto em v1 já — não esperar v2 para exposição.

- **Honestidade epistêmica em prompts via "hipótese principal" vs "afirmação".** v2 reescreveu §2 com hipótese explícita em vez de mecânica fabricada. CLAUDE.md immutable rule materializada em artefato auditável. Pattern: quando mecânica fina não está totalmente caracterizada, declarar como hipótese e diferir caracterização para ADR pos-hoc.

### Artefatos da sessão

- **PR `#59`** — `fix/scan-diff-stdin-isolation-windows-stdio` → main (squash hash a registrar pós-merge `<TBD>`). 1 commit `6f9bc44` pre-squash. Diff: `tools.py +3 / test_scan_diff.py +134`.
- **Branch `chore/gate-milestone-b-rule-set-fixture`** local com 3 commits internos: `19e0536` (pack alternativo synthetic_iban — sessão #34), `84672a5` (gate script v1 — sessão #34), `34b6c05` (patch script — sessão #35). Não pushed; aguarda PR posterior.
- **Prompt-artefatos em `/mnt/user-data/outputs/` da sessão Chat:**
  - `prompt-tfix-v1.md` (~520 linhas)
  - `prompt-tfix-v2.md` (~640 linhas)
  - `prompt-tfix-v3.md` (~470 linhas)
  - `briefing-tgatescriptfix.md` (~180 linhas)
  - `handoff-35-36.md` (este handoff)
  - `learning-log-35.md` (este learning-log)
  - `milestoneB-draft.md` (draft com `<TBD>` para hashes)
- **Code review transcripts** anexados pelo João no Chat persistente da sessão #35:
  - R1 review v1 (clean session) — 13 catches.
  - R2 review v1 (sessão #34 que diagnosticou) — 13 catches.
  - R1 review v2 — 6 catches (1 crítico C5, 1 médio M6, 4 cosméticos/menores).
  - R2 review v2 — 10 catches (1 crítico N-C1, 2 substantivos N-S1/N-S2, 4 cosméticos N-Cos1-4).
- **Code GATE 1 reports** anexados pelo João:
  - PR #59 pre-flight (9 Pins) + ratificação Chat.
  - Gate script patch pre-flight (4 Pins) + DD-GATE1-1 ratificação Chat.
- **Evidência empírica do gate Milestone B:**
  - `gate_b_output.json` (consolidated PASS, 5/5 invariantes verdes, untracked working dir).
  - `gate_b_stderr.log` (verbose per-phase, untracked working dir).

### Métricas operacionais

- **Catches absorvidos cumulativamente** no prompt T-fix v1→v3: ~30+ (13 v1→v2 R1 + 13 v1→v2 R2 + 6 v2→v3 R1 + 10 v2→v3 R2; alguns convergentes).
- **Catches no briefing T-gate-script-fix:** 1 absorção em GATE 1 (DD-GATE1-1: forma do Patch 2 — Pin 2 venceu Chat).
- **Rounds Chat ↔ Code:** 3 rounds de review do prompt T-fix (v1, v2, v3) + 2 rounds de review do briefing (GATE 1 + ratificação) + 1 round de revalidação gate Milestone B.
- **Tempo total sessão #35:** ~3-4h Chat + ~2.5h Code = ~5.5-6.5h. Ratio Chat:Code ≈ 1.5:1. Proporcionalmente mais Code-pesado vs sessões prep T06/T07 (6:1) — esperado para sessão de execução + validação.
- **Tests:** baseline 132 → 134 pós-merge PR #59 (em Windows local; 133 Linux/macOS).
- **Gate Milestone B:** FAIL #34 → FAIL #35 pré-patch → PASS pós-patch (5/5 invariantes verdes).
- **Custo de blockers descobertos por layer:** layer-1 review (R1 verificacional) detectou 13+1 críticos arquiteturais (Fix-4 type breakage); layer-2 review (R2 diagnostic-context) detectou 13+10 críticos de design/cobertura (AS-14 falso verde cross-platform); layer-3 (Code empírico) detectou 1 catch operacional (idioma do projeto em INV-1). Sem essas três camadas, PR #59 entraria com Fix-4 type-broken OU AS-14 falso verde OU INV-1 quebrado em produção.

### Próximo passo

Sessão Chat #36 — abre com:
1. Confirmação do merge da PR #59 (squash hash a registrar).
2. Task (C) push + PR de `chore/gate-milestone-b-rule-set-fixture` (rebase sobre main pós-fix; deve ser limpo).
3. Task (D) população dos `<TBD>` no `milestoneB-draft.md` + integração ao repo.

Sessões subsequentes:
- (E) ADR-0011 — sessão Chat própria, ~2-3h.
- (F) PR posterior implementando ADR-0011 (E-2) — ~3-5h Code.
- (G) Housekeeping CLAUDE.md `§Status flags` + sweep imutável-rules — sessão própria pre-Milestone C.

Custo estimado próximas 4-5 sessões: ~12-18h distribuído.

---

**Fim da entry #35.** Integrar ao `docs/process/learning-log.md` no repo via direct commit (per ADR-0001 Decision 6: learning-log + session-handoff são as duas exceções ao PR workflow).

---

obs learning-log-35.md:

§Status: "PR #59... <TBD>" → hash real; "Branch local chore/...: 3 commits" → "PR #60 mergeada em main como b4ec3fe"; remover "Não pushed".
§Artefatos "PR #59": preencher <TBD>.
§Artefatos "Branch chore/...": substituir por "PR #60 — chore(gate-milestone-b): gate empírico RF-008 rule-set-axis → main, squash hash b4ec3fe. 3 commits internos pre-squash: 19e0536 (pack), 84672a5 (script v1), <hash> (patch — pós-rebase regerou SHA de 34b6c05 original)."

# Learning Log — entry sessão #37

Anexar ao final de `docs/process/learning-log.md` via direct commit
(per ADR-0001 D6).

---

## #37 — 2026-05-25 — Autoria de design de Milestone C: header + coordinator-skeleton + plano de specs leves dos subagentes

**Escopo da sessão.** Sessão Chat dedicada à autoria de design de
Milestone C. Diferente de #27 (decomposição de tasks de Milestone B
sob spec preexistente do semgrep-runner), esta sessão operou em
território de design ainda não materializado — specs dos cinco
subagentes + coordinator + custom tool `emit_report` + `.mcp.json`
do projeto. Resultado: header de Milestone C decomposto em capability
+ RFs + provisões; coordinator-skeleton produzido como artefato Chat;
plano de ordem híbrida de redação das 6 specs (coordinator-skeleton →
Reporter-flesh → Triager-sanity → Detector → Classifier → Matcher →
coordinator-flesh-completo) ratificado.

Quatro outputs Chat materializados em `/mnt/user-data/outputs/`:
coordinator-skeleton-37.md; tasks-md-milestone-c-diff-37.md;
session-handoff-37-to-38.md; este entry.

**Conceitos da prova exercitados.**

*Domínio 1 — Agentic Architecture & Orchestration.* D1.2 + D1.3
coordinator-subagent + single responsibility aplicados concretamente
ao desenho do coordinator como Python main loop (não AgentDefinition)
após pesquisa empírica do SDK em `platform.claude.com/docs/en/agent-sdk/subagents`
que revelou restrição "subagents cannot spawn their own subagents".
D1.6 task decomposition aplicada em duas dimensões: pipeline fixa de 5
etapas (prompt chaining) escolhida sobre dynamic decomposition por
alinhamento explícito com Task Statement 1.6 do exam guide
(multi-aspect review of a diff é exemplo canônico de prompt chaining).
D1.3 subagent context isolation materializado em decisão de scratchpad
audit-only + state passing inline (output da etapa N injetado no
prompt da N+1 via JSON serializado; subagentes em contexto fresco a
cada query).

*Domínio 2 — Tool Design & MCP Integration.* D2.2 resource vs tool
exercitada em decisão sobre vocabularies single load point:
`policy://vocabularies` declarado universalmente compartilhável em
arch-overview §5.4, coordinator ganha acesso pontual como exceção
ratificada via three-beats. D2.3 tool distribution + scoped access
materializado em whitelist `EXPECTED_SERVERS = {"policy-reader", "semgrep-runner"}`
no parser do `.mcp.json`: fail loud em server fora do whitelist
impede surpresa silenciosa. D2 custom tool + in-process MCP server:
`emit_report` via `@tool` + `create_sdk_mcp_server(name="reporter-tools")`
exposta apenas no Reporter AgentDefinition; tool authorization é
mecanismo que materializa invariante arquitetural "Reporter como
único locus emissor" (§4.3 arch-overview).

*Domínio 3 — Claude Code Configuration & Workflows.* D3 `.mcp.json`
como single source consumido por Claude Code dev + coordinator
runtime (decisão M2). Whitelist é blindagem contra dev adicionar
server por motivo Claude Code e esquecer de remover. D3 `.claude/rules/`
referência nominal a `git-conventions.md` (PR `chore/sync-adr-references`
como diff clean Chat-revisable) + `mcp-testing.md` (AS de teste do
whitelist em task futura).

*Domínio 5 — Context Management & Reliability.* D5 scratchpad pattern
calibrado para A' (Python orquestrando query() separadas): pattern do
exam guide endereça context degradation em agentes long-running, não
em multiple query() com contexto fresco. Reframe pós-Code review: em
A', scratchpad é audit/provenance + crash recovery + CI artifact, não
context degradation mitigation. Conceito mais preciso aqui é Task
Statement 5.3 (structured error context + partial results enabling
intelligent recovery). D5 provenance via citation chain preservada:
trinca `(policy_schema_version, policy_version, legal_framework)`
propagada verbatim do policy-reader até cada finding do Report
(RNF-002 bound a Milestone C). D5 error propagation aplicada a
pipeline multi-agente: Pydantic validation falha → halt; MCP isError
→ retry vs halt por errorCode; ReportNotEmitted (Reporter sem
emit_report) → erro estruturado via inspeção message stream em
Python, não hook.

**Decisões tomadas.**

- **Capability + RFs do gate de Milestone C.** RF-003 pleno + RF-004
  pleno + RF-005 pleno + RF-006 + RF-007 pleno + RF-008 pleno +
  RNF-002. Cobertura mais larga do que "tentative" original de
  tasks.md (003, 004-pleno, 006, 008-pleno) — RF-005 pleno e RF-007
  pleno adicionados por análise; RNF-002 adicionada por antecipação de
  evolução SDR β.
- **Coordinator pattern A'** (Python prompt chaining, query() por
  etapa, agents={} contendo só o subagente da vez). Não-AgentDefinition.
  Trade-off ratificado contra A (main agentic): pipeline fixa
  determinística favorece prompt chaining per Task Statement 1.6.
- **Scratchpad S2'** (filesystem audit-only via coordinator write;
  state passing inline JSON; subagentes sem Read sobre scratchpad).
  Vence S2-canônica do exam guide por simplificar tool authorization
  sem perda funcional na pipeline fixa (Code review absorvido).
- **`.mcp.json` M2** single source + whitelist obrigatório
  `EXPECTED_SERVERS = {"policy-reader", "semgrep-runner"}` com fail
  loud.
- **emit_report dual sink** (`@tool` em `src/coordinator/tools.py`;
  grava `99-report.json` + retorna payload via tool result; captura
  pelo coordinator via inspeção message stream em Python; enforcement
  ReportNotEmitted via Python, não hook).
- **Vocabularies single load point** em coordinator §3.0 (acesso
  pontual a `policy://vocabularies`, exceção ratificada via three-beats
  Beat 1 a arch-overview §5.1 + §5.7).
- **Halt-conditions caminho (i)** — Reporter sempre invocado, mesmo
  em skip path (Triager) ou findings vazios (Detector zero
  candidates). Preserva §4.3 "Reporter como único locus emissor" sob
  substituição de arch-overview §3 mermaid (`skip → END` → `skip →
  Reporter`).
- **SDR como serializador downstream (pattern β)** — Report JSON é
  canônico; transformação Report → SDR CSV (LGPD Art. 37 audit) é
  consumer downstream (GitHub Action ou job de governança), não
  responsabilidade do sistema multi-agente. Três garantias de design
  no MVP preservam compatibilidade: superset de campos, audit
  metadata top-level (`report_id`, `report_emitted_at`), separação
  Reporter ↔ serializadores externos.
- **Multi-spec em `docs/specs/subagents/`** com coordinator.md como
  hub do workflow. Pattern dual canonical+compact de ADR-0003
  abandonado por aplicabilidade (subagent specs têm contract surface
  comportamental, não wire format MCP; já são compact-sized 1-2
  páginas). Justificativa registrada em coordinator.md skeleton
  header + a ratificar em ADR-0012 retroativo.
- **Template como hipótese de trabalho destilado no Reporter-flesh**
  per `docs/specs/_template.md` §método-de-destilação caminho (b).
  Caminho (a) "decidir clareza estrutural suficiente, autorar
  template upfront" rejeitado como overconfident.
- **Ordem híbrida de redação:** coordinator-SKELETON (sessão #37) →
  Reporter-FLESH (#38; destila template) → Triager-SANITY (#38) →
  Detector → Classifier → Matcher (#38-#39) →
  coordinator-FLESH-COMPLETO (#39+).
- **Cross-reference rules 1-6 ratificadas** como anti-drift discipline
  para multi-spec; Rule 6 explicitamente: §3 (Output) de cada
  subagent spec é canonical I/O boundary citado verbatim downstream
  (Rule 6 corrigida pós-Code review item 3 — typo §4 do draft).

**Defense candidates emergentes.**

- **Pattern "pre-flight grep Code" para design proposals tocando docs
  autoritativos preexistentes.** Empirizado em #37: três rounds de
  Code review pegaram (i) env vars fabricados (POLICY_DIR/RULES_DIR
  em vez de reais POLICY_READER_ROOT/SEMGREP_RUNNER_ROOT); (ii)
  divergência metodológica silenciosa contra `_template.md` (template
  upfront vs destilação); (iii) conflitos diretos com arch-overview
  §5.1 (coordinator carregando vocabularies viola "sem acesso direto
  a MCP servers") + arch-overview §3 mermaid (skip → END) ↔ RF-006
  literal (findings vazio possível "se Triager decidiu skip OU se
  nenhum candidato foi detectado" implica pipeline atravessa
  Reporter). Reframe operacional do Code (não disciplinar): Chat
  opera em proposta conversacional, Code opera em verificação contra
  repo verbatim. Mecanismo: design proposals tocando docs
  autoritativos ⇒ pre-flight grep Code ~5min antes de skeleton se
  materializar, com Chat passando lista de docs autoritativos
  relevantes (arch-overview, REQUIREMENTS.md, ADRs específicos).
  Defense candidate forte para Capítulo de Método, agregado ao
  pattern "Chat propõe / Code verifica" desde #21+.

- **Pattern "argumentação assimétrica entre Chat e Code estabiliza
  decisão de design quando ambos lados têm mérito".** Empirizado em
  #37 na deliberação sobre vocabularies load (a) vs (b): Chat
  oscilou 3 vezes (inclinação inicial (a) com argumento exam-guide
  impreciso → pivô para (b) "regra bit-stable" → pivô final (a) com
  argumento "cleaner prompts" trazido pelo Code). Reframe: Chat
  oscilando em judgment calls de gap pequeno NÃO é falha de opinião;
  é absorção legítima de argumentos novos emergentes do Code review.
  Decisão final ancora em ponderação cumulativa, não em primeira
  inclinação preservada por orgulho. Custo: rounds adicionais de
  review. Ganho: decisão mais robusta defensavelmente.

- **Pattern "template upfront é overconfident; destilação preserva
  método registrado".** Empirizado em #37 quando Code identificou
  `docs/specs/_template.md` §7-8 prescrevendo "derivar
  `_template-subagent.md` na primeira spec de subagente da semana 3
  (mesmo método de destilação aplicado a este template)". Eu propus
  template upfront com 10 seções; Code identificou que estrutura
  emerge da primeira spec redigida, não de intuição prévia, mesmo
  quando arch-overview §5 estabeleceu fronteiras. Defense candidate:
  "método de destilação registrado é mais conservador que template
  upfront em domínio onde estrutura não está empiricamente validada".

**Validações empíricas.**

- **Multi-round Code review com 3 reviews independentes em sequência
  produziu 8+ catches load-bearing distribuídos em 4 classes.**
  Review 1 (pós-Bloco 2): factual em env vars + reframe conceitual
  do scratchpad (exam guide pattern aplicado impropriamente). Review
  2 (pós-Bloco 3 template): método de destilação ignorado + ADR-0003
  silenciosamente abandonado + seções faltantes (§Critérios de
  aceitação + §Review pass three-beats) + 5 refinamentos pontuais.
  Review 3 (pós-skeleton): conflitos diretos com arch-overview
  (vocabularies + halt-conditions) + drift de auto-consistência
  (Rule 6 cita §4, template tem §3) + whitelist defensivo + clarity
  + ADR numbering drift no repo. Padrão emergente: granularidade do
  review escala com proximidade da materialização do artefato.
  Reviews iniciais (conceituais) catch macro; reviews finais
  (skeleton concreto) catch micro + drift de auto-consistência.

- **Reframing do meta-padrão "invenção arquitetural silenciosa" para
  "divisão de trabalho funcionando".** Catch importante do Code
  (não auto-flagelação): Chat opera em proposta conversacional, Code
  opera em verificação contra repo verbatim. Drift que cruza
  fronteira só aparece no segundo. Mecanismo operacional emergente
  documentado: pre-flight grep Code com lista de docs autoritativos.
  Não é disciplina pessoal corrigível por esforço — é especificação
  de processo divisão de trabalho.

- **Cross-reference rule 6 (Output como canonical I/O boundary)
  catch própria.** Skeleton ratificou rules 1-6 anti-drift e
  imediatamente caiu em uma (Rule 6 citou §4 quando template tem
  Output em §3). Leitura irônica do Code; conserto trivial mas catch
  load-bearing antes de Reporter-flesh herdar drift de cross-ref.

- **ADR numbering drift detectado e catalogado.** session-handoff
  §(E)+(F) e milestoneB.md citam "ADR-0012 pos-hoc" para
  Windows-stdio E-2, que foi absorvido em ADR-0011 mergeada.
  Housekeeping `chore/sync-adr-references` proposto antes de
  Milestone C citar ADR-0012 em qualquer artefato novo.

**Métricas operacionais.**

- 3 rounds Code review distribuídos pela sessão, 8+ catches
  load-bearing absorvidos.
- 4 outputs Chat materializados (~1100 linhas combinadas).
- 0 commits em main durante a sessão; toda materialização em
  `/mnt/user-data/outputs/`. Sessão Chat pura.
- Custo estimado: ~3.5-4h Chat. Ratio Chat:Code = ∞:0 (sem Code
  execution; Code reviews assíncronos consumidos pelo Chat).
- 7 decisões load-bearing fechadas (Bloco 1 capability+RFs; Bloco 2
  cinco decisões arquiteturais; Bloco 3 estrutura+ordem); 3 decisões
  adiadas para sessões posteriores (gate milestone-level mechanism;
  schema "Report vazio" para Reporter-flesh; tasks T11+).

**Artefatos produzidos.**

Quatro outputs Chat em `/mnt/user-data/outputs/`:

- `coordinator-md-skeleton-37.md` — skeleton do
  `docs/specs/subagents/coordinator.md` patcheado conforme decisões
  sessão #37 + 3 rounds Code review.
- `tasks-md-milestone-c-diff-37.md` — diff aplicável de 4 blocos
  para `docs/tasks.md`, materializando header de Milestone C.
- `session-handoff-37-to-38.md` — handoff para sessão #38, listando
  estado factual + 13 tasks pendentes ordenadas + pre-flight para
  Reporter-flesh.
- `learning-log-entry-37.md` — este entry.

Pendência crítica para sessão Code curta antes de #38: aplicar 4
outputs ao repo via 4 ações independentes (direct commits + 1 PR
mecânica). Detalhamento em handoff §4.

**Próximo passo.**

Sequência operacional antes de sessão #38:

1. Apply coordinator-skeleton (direct commit ou PR; decisão pendente).
2. Apply tasks.md diff (PR `docs/tasks-milestone-c-header`).
3. (Opcional) Apply housekeeping ADR-0012 stale → ADR-0011 (PR
   `chore/sync-adr-references`).
4. Apply learning-log + session-handoff (direct commits).

Sessão #38 Chat — Reporter-flesh-first. Custo estimado ~1-1.5h Chat
normal; ~2-2.5h se template hipótese sessão #37 quebrar em alguma
seção. Triager-sanity pode caber na mesma sessão se tempo permitir.

Sessões subsequentes (#38-#39): Detector → Classifier → Matcher,
depois coordinator-flesh-completo, depois companion edits
arch-overview, depois ADR-0012 retroativo, depois decomposição de
tasks T11+, depois benchmark de PRs sintéticos, depois gate
milestone-level.

---

## Sessão #38 — 2026-05-26 (entry parcial: DD-21 ratchet)

**Modo de operação.** Chat dedicada. Decisão arquitetural única
(DD-21) ratificada e aplicada via Code session curta. Branch
`docs/dd-21-policy-clause-ref` separada de
`docs/coordinator-context-tightening` por audit chain (DD-21 é
tema distinto do cleanup de coordinator §3.2/§3.5/§5).

**Decisões fechadas.**

- **DD-21 ratificada — Opção A.** `policy_clause_ref` propagado
  verbatim do `policy-reader` (canonical §4.3) em vez de renomear
  para `clause_id` no Report. Campo presente em todos os 4
  vereditos, incluindo `not_applicable`.

- **DD-3.3 ratchet implícito.** DD-3.3 (sessão #38 Chat, sem
  persistência no repo) prescrevia omissão de `clause_id` em
  `not_applicable`; substituída por DD-21. Versão corrente:
  presença incondicional do `policy_clause_ref` em todos os 4
  vereditos + nomenclatura preservada do `policy-reader`.

**Justificativa em quatro eixos.**

1. **Arquitetural** — separação de planos epistêmicos (DESIGN.md
   tese central) materializada visualmente no JSON do Report.
2. **Empírica** — impl real do `policy-reader` (Milestone B PASS;
   `src/mcp_servers/policy_reader/models.py` linhas 237/252/268/286
   declaram `policy_clause_ref: str` obrigatório em todas as 4
   variantes de veredito) é ground truth; precede RF-006 (redigido
   Fase 1) em maturidade.
3. **Audit substantivo** — LGPD Art. 37 / SDR β precisa de
   `policy_clause_ref` em `not_applicable` para registrar qual
   cláusula foi avaliada-e-descartada.
4. **Cronológico-epistêmico** — impl validada > doc pre-impl.

**Edits aplicados ao repo (branch `docs/dd-21-policy-clause-ref`).**

- `docs/REQUIREMENTS.md` linhas 61, 86, 117 — 3 renames `clause_id`
  → `policy_clause_ref`; em RF-006 também remove cláusula de
  omissão em `not_applicable`.
- `docs/architecture-overview.md` linhas 201, 245 — 2 renames; a
  ref em §4.2 `clauses/` (linha 105) preserva `clause_id` por ser
  identidade da cláusula na Política, não ref ao campo no Report.
- `docs/process/learning-log.md` — esta entry.

**Achado empírico durante execução.** Plano Chat estimou ~17
ocorrências de `clause_id` em `docs/REQUIREMENTS.md`; grep real
retornou 3 (inflação de memória, não drift de doc). Stop condition
do plano disparou; escalation devolveu OK para prosseguir com
escopo reduzido (decomposição determinística: todos os 3 renames
inequivocamente Report/Matcher refs).

**Não aplicado neste PR.** Demais ocorrências de `clause_id` em
specs do `policy-reader` (`canonical.md`, `compact.md`),
learning-log histórico, tasks.md, ADRs — são refs à identidade
da cláusula na Política, ou histórico de raciocínio que preserva
o original para audit. Diretrizes forward-looking para futura
redação de Reporter spec §3.2/§6.3/§8.3 e Matcher spec output
Pydantic model catalogadas em sessão Chat, não materializadas
neste repo.

**Próximo passo.** Reporter-flesh e Matcher-flesh seguem
cronograma original. DD-7.1, DD-7.4, findings #3-#8 retomados em
próxima sessão Chat após merge deste PR.

---

## Gate 6 — `tools=[]` em SDK 0.2.87 (sessão Code dedicada, 2026-05-26)

**Hipótese.** `tools=[]` (lista vazia explícita) em
`ClaudeAgentOptions` remove todos built-ins do contexto do modelo,
deixando apenas MCP tools de `mcp_servers={...}` + `allowed_tools=[...]`
visíveis. Equivale a "allowlist vazia". Não verificado pela doc canônica
do SDK — `tools: list[str] | ToolsPreset | None = None` não especifica
semântica de lista vazia. Precedent conceitual ambíguo: `setting_sources`
mudou semântica em 0.1.60 (`[]` passou de "default" para "carregar nada").

**Resultado.** **PASS_H_EMPTY_LOCKDOWN** — hipótese principal ratificada
empiricamente. Smoke-test em
`scripts/smoke_tests/sdk_tools_empty_list/` rodou 3 cenários × 2 runs (6
queries) via `uv run --with claude-agent-sdk==0.2.87`. Discriminação
behavioral, não inspeção de SystemMessage.

**Evidência.** Por cenário (2 runs cada):

| Scenario              | echo (run1, run2) | bash (run1, run2) | verbalize_absence  | num_turns |
|-----------------------|-------------------|-------------------|--------------------|-----------|
| S1_baseline_none      | 1, 1              | **1, 1**          | False, False       | 4, 4      |
| S2_hypothesis_empty   | 1, 1              | **0, 0**          | True, True         | 2, 2      |
| S3_sanity_read_only   | 1, 1              | 0, 0              | True, True         | 2, 2      |

S2 (`tools=[]`) comportamento idêntico a S3 (`tools=['Read']`), ratifica
hipótese principal. S1 (`tools=None`) baseline com Bash attempted como
controle positivo. Verbalização de S2 qualitativamente indistinguível de
S3 (e.g., S2 run2: *"For the second task: I cannot call the Bash
tool..."*).

**Implicação para finding #3 do review V2.** Pivot procede. Coordinator
§3.4 (Reporter) e §3.5 (Matcher) podem substituir `tools=["Read"]` por
`tools=[]` em PR separado per pattern de PR sequencing. Mudança alinha
o coordinator com recomendação Anthropic oficial
(`platform.claude.com/docs/en/agent-sdk/custom-tools`) sobre context
restriction via `tools` field em vez de `disallowed_tools=[...]`.

**Side findings.** (a) `ToolSearch` aparece apenas em S1 (`tools=None`);
S2 e S3 carregam schema MCP inline (num_turns=2 vs 4) — `tools=[]` herda
benefício de turn economy. (b) `permission_denials=[]` em S2/S3 porque
modelo não TENTA Bash (signal de contexto, não de execution). (c)
Smoke-test mantém pattern empírico de discriminação behavioral usado em
#38, #38b, #38c; introspecção de `SystemMessage.tools` foi considerada
mas evitada (shape do SDK menos estável que comportamento do modelo).

**Próximo passo.** Smoke-test consolidado em
`scripts/smoke_tests/sdk_tools_empty_list/{smoke_test.py, README.md}`
para reprodutibilidade pós-upgrade do SDK. Edit cirúrgico a
`coordinator.md` §3.4 e §3.5 substituindo `tools=["Read"]` por
`tools=[]` é proposto para PR separado (não escopo deste Gate). Demais
findings (#1, #2, #4-#8) do review V2 continuam em backlog Chat.

# Learning Log — entry sessões #41 + #42

Anexar ao final de `docs/process/learning-log.md` via direct commit
(per ADR-0001 D6).

---

## #41 + #42 — 2026-05-26/27 — Reporter-FLESH consolidado + Reporter spec 0.3.0 + coordinator v3 sub-packaging

**Escopo da sessão.** Duas sessões Chat consolidadas em uma entry por
continuidade temática: #41 materializou Reporter spec v0.1.0 → v0.2.0
(consolidação de Reporter draft com 10 diretrizes forward-looking +
3 achados de review independentes); #42 fez second-pass review (catch
crítico do cross-check #3 vocab membership como semântica do Matcher,
não shape do Reporter) levando a Reporter spec 0.3.0 mergeada, depois
sub-packaging do coordinator com 6 surgical edits prescritos em §10.5
da Reporter spec + Edit 3 estendido em second-pass do próprio
coordinator (factory pattern alinhado a Reporter spec §4.8).

Resultado tangível: `docs/specs/subagents/reporter.md` v0.3.0
mergeada; `docs/specs/subagents/coordinator.md` v3 produzido como
output Chat aguardando direct commit em
`chore/sync-coordinator-with-reporter-0.3.0`.

**Conceitos da prova exercitados.**

*Domínio 1 — Agentic Architecture & Orchestration.* D1.2 + D1.3
coordinator-subagent materializados em factory pattern com closure
capture. `create_reporter_server(run_path, expected_report_id)` envolve
`@tool` decorator + `create_sdk_mcp_server`, capturando run_path (sink
#1 do dual sink) e expected_report_id (cross-check #4 intra-handler)
via Python closure. Module-level `@tool` definition (skeleton v2
original) seria incompatível com runtime parameters — handler seria
criado uma vez na importação, sem acesso aos parâmetros do run.
Factory pattern resolve. Defense candidate forte para o Capítulo de
Método: "restrições do SDK formam o desenho da arquitetura" — closure
capture não é otimização, é único caminho viável dado que `run_path`
muda a cada execução do pipeline.

*Domínio 2 — Tool Design & MCP Integration.* D2.3 scoped tool access
exercitada via **distinção load-bearing entre denial-on-miss e
availability**, com surface concreta na issue #361 do SDK Python
(*"It [allowed_tools] does not remove tools from Claude's toolset"*).
Quíntupla canônica restruturada em §2 do coordinator: 5 elementos
ortogonais de denial-on-miss (`permission_mode` + `setting_sources` +
`strict_mcp_config` + `allowed_tools` + `mcp_servers`) separados de
`system_prompt` (role definition) e `tools` (context restriction;
eixo ortogonal availability). Defesa em profundidade requer ambos os
eixos: `tools=[]` (per Gate 6 / PR #67 evidência empírica em
`scripts/smoke_tests/sdk_tools_empty_list/`) remove built-ins do
contexto do modelo, enquanto `allowed_tools` whitelist com
`permission_mode="dontAsk"` garante denial de tentativas fora do
allowlist. ToolAnnotations declaradas no @tool (`readOnlyHint=False`,
`destructiveHint=False`, `idempotentHint=False`, `openWorldHint=False`)
aplicadas a `emit_report` per Reporter spec §4.6.

*Domínio 4 — Prompt Engineering & Structured Output.* D4.2 few-shot
strategy materializada com 3 exemplares no Reporter spec §6.6 cobrindo
três estados de pipeline: normal-com-findings, skip-path, findings-zero.
Bug-magnet de exemplar wrap structure detectado em second-pass review:
sintaxe `emit_report(payload={...})` (wrap em chave `payload`)
divergente da assinatura real `emit_report({...})` (schema flat
correspondendo direto a `ReportPayload.model_json_schema()`).
Falha em corrigir produziria failure mode `PYDANTIC_VALIDATION`
cryptic em runtime — o erro aparece longe da causa, e o modelo,
seguindo o exemplar, replicaria a estrutura errada sistematicamente.
Defense candidate forte: **severidade subestimada de bug-magnet em
few-shot exemplars**, especialmente quando a falha é silenciosa-via-
schema-validation em vez de loud-via-tool-error.

*Domínio 5 — Context Management & Reliability.* D5 structured error
metadata materializada em §4.4 + §4.5 do Reporter spec (envelopes
estruturados com errorCategory, errorCode, is_retryable, details).
Atomic write-then-rename via `os.replace` (Windows-native) garante
durabilidade do 99-report.json sem corromper estado em crash mid-write.
**Aritmética de retry budget** com locus authoritative em §1.5 da
Reporter spec (`max_turns=3` = 1 initial emit + até 2 retries) e
cross-refs em outros loci (§4.4, §4.5, coordinator §3.5) — pattern
de "single source of truth + references" aplicável a parâmetros
operacionais que aparecem em múltiplos contextos.

**Defense candidates emergentes (8 patterns).**

1. **Cross-doc rigoroso vs arquitetural-gaps como lentes ortogonais
   de review.** João forneceu dois reviews independentes da Reporter
   v0.2.0 (cross-doc rigoroso pegando inconsistências factuais entre
   seções; arquitetural-gaps pegando decisões load-bearing ausentes).
   Convergência em catch comum = validação cruzada; divergência cobre
   área maior. Pattern: usar duas lentes ortogonais para validar specs
   substantivas, não duas instâncias da mesma lente.

2. **Catch que escapa às duas lentes mas emerge da coerência intra-
   spec.** Cross-check #3 (vocab membership) estava em §4.8 (handler
   logic) como parte dos cross-checks intra-handler. Mas §8.3 (lista
   positiva de o-que-o-Reporter-faz) descrevia o mesmo cross-check
   sob óptica do que **o Reporter não faz** — vocab membership é
   responsabilidade do Matcher per §2.4 + §8.3. Inconsistência
   interna emergia da releitura intra-spec. Linha de pergunta: "esta
   afirmação em §N contradiz alguma afirmação em §M para M ≠ N±1?"

3. **Severidade subestimada de bug-magnet em few-shot exemplars.**
   Detalhado acima sob D4. Material para `.claude/rules/few-shot-discipline.md`
   se padrão materializar em 2+ specs.

4. **Bump rules sobre estado mergeado, não em-revisão.** Os 4 fixes
   pós-second-pass do Reporter spec (§8.3 renumbering, §10.3 Gate 4
   stale ref, §5.1 M3 incompleto, §7.2 "ou inline em tools.py" stale)
   foram aplicados consolidadamente no **mesmo bump 0.3.0** sem subir
   para 0.3.1, porque a 0.2.0 ainda não havia sido mergeada. Bump
   rules aplicam-se ao estado mergeado, não ao em-revisão. Reduz
   ruído de bump-churn pré-merge.

5. **Renumeração-com-propagação-incompleta como classe de drift.**
   Decisão de remover cross-check #3 do Reporter spec (passou de 5
   para 4 cross-checks) exigiu pass de grep cross-doc por TODOS os
   números antigos: §4.8 tabela (5→4), §6.3 (sem `VOCAB_OUT_OF_FRAMEWORK`),
   §9.3 (sem teste vocab), §8.3 lista positiva (numeração #4a/4b/5
   stale), §10.3 Gate 4 ref stale. Falha em 2 dos loci escapou ao
   first-pass e foi pego no second-pass review. Material para
   `.claude/rules/refactoring-discipline.md`: "refactor de listas
   numeradas requer grep cross-doc por TODOS os números antigos antes
   de fechar PR".

6. **Reflow Markdown 3 classes de bugs latentes.** Script de reflow
   do coordinator (890 → 501 linhas) detectou três bugs distintos em
   uma única implementação: (a) regex `^#` falso-positivo matching
   `#37` (ref a sessão) como heading — fix `^#{1,6}\s` ATX strict; (b)
   regex `[-*+]` falso-positivo matching `+ ` como continuação de
   prose hard-wrap como list item — fix omitir `+` do alphabet de
   markers para docs que usam `+` como prose connector; (c) blank line
   intra-list quebrando paragraph-split-by-blank-line — fix walking
   line-by-line com state machine de tipo de linha. Os três convergem
   para princípio: **classification-by-context é mais robusta que
   classification-by-pattern em transformações estruturais de
   markdown**. Material para `.claude/rules/markdown-reflow-discipline.md`
   ou `scripts/utils/reflow.py` quando estes forem autorados.

7. **Minimal-spec interpretation expõe gaps arquiteturais latentes.**
   Edit 3 da §10.5 da Reporter spec prescreveu: *"substituir literal
   'Emit the consolidated Report JSON' por referência ao
   EMIT_REPORT_DESCRIPTION canônico"*. Aplicação literal-minimal
   substituiu **apenas** a string, deixando §7 do coordinator com
   `@tool` module-level + `create_sdk_mcp_server` module-level —
   incompatível com `create_reporter_server(run_path, run_id)` que
   §3.0 chama em runtime. Inconsistência arquitetural exposta pela
   aplicação minimal, pega em second-pass review do coordinator.
   Três respostas possíveis ao gap detectado: (i) aplicar minimal
   silenciosamente → bug latente em main; (ii) aplicar minimal +
   relatar gap como observação → reviewer decide; (iii) estender o
   edit unilateralmente → overreach. Caminho (ii) ratificado como
   defensável: preserva autoridade da spec, mas exerce **honestidade
   epistêmica do aplicador**. Caminho (A) escolhido pelo João
   estendeu Edit 3 no mesmo PR. Material forte para Capítulo de
   Método.

8. **Revisão temporal-deslocada do mesmo agente como classe de catch
   independente.** Sessão #41 abriu com 3 achados de review do
   próprio Reporter draft autorado em sessão anterior (postura A
   sobre quíntupla canônica preservando 5 elementos; §9.6 removido
   como duplicação de coordinator §10 three-beats; Gate numbering
   4→5 reordenado). Distância temporal entre autoria e leitura captura
   classes distintas de drift que self-review-imediato não pega
   (semântico interno, redação afastada). Pattern complementar a
   multi-instance review do exam guide D4.6: o segundo passe não
   precisa ser de outra instância — outra **sessão temporal** do
   mesmo agente já captura drift.

**Métricas operacionais.**

- 4 iterações de revisão consolidadas em 0.3.0 (consolidação inicial
  + 3 achados first-pass + 1 catch crítico second-pass + 4 fixes
  renumeração) sem bump-churn intermediário.
- Reporter spec final 0.3.0: 946 linhas. coordinator v3 final: 517
  linhas (vs v2 com 890 linhas; reflow contribuiu 44% da redução +
  6 edits substantivos + Edit 3 estendido).
- 2 sessões Chat consolidadas (#41 ~3-4h consolidação + materialização;
  #42 ~2-3h reviews + coordinator sub-packaging).
- 0 commits em main durante as sessões Chat; materialização via
  outputs em `/mnt/user-data/outputs/`. Aplicação ao repo via direct
  commits curtos (Reporter spec 0.3.0 já mergeada; coordinator v3
  pending).
- 8 defense candidates registrados (acima); todos com material
  reaproveitável para Capítulo de Método.

**Artefatos produzidos (sessões #41 + #42).**

Outputs Chat em `/mnt/user-data/outputs/`:

- `reporter.md` v0.3.0 (#41 consolidation + #42 second-pass; 946
  linhas) — **mergeada em main** em `docs/specs/subagents/reporter.md`.
- `coordinator.md` v3 (#42 sub-packaging; 517 linhas) — **pending
  merge** em `docs/specs/subagents/coordinator.md` via
  `chore/sync-coordinator-with-reporter-0.3.0`.
- Script `reflow_v2.py` (#42 utility; 90 linhas) — utility one-off
  para o reflow do coordinator; **não promovido ao repo** (aguardar
  validação empírica em 2+ specs antes de mover para
  `scripts/utils/`).
- Este entry (#42 learning-log).
- session-handoff #41+#42 → próxima-sessão (Triager-sanity).

**Próximo passo.**

Sequência operacional antes da próxima sessão Chat:

1. Apply coordinator v3 (direct commit em `chore/sync-coordinator-with-reporter-0.3.0`).
2. Apply este learning-log entry (direct commit em main per ADR-0001 D6).
3. Apply session-handoff (direct commit em main per ADR-0001 D6).

Próxima sessão Chat: **Triager-sanity** (~30-60min Chat). Escopo
duplo: (a) redigir `docs/specs/subagents/triager.md` com base no
template hipótese que emergiu da Reporter spec 0.3.0; (b) sanity-
check do template — destilar `_template-subagent.md` se sinal de
boa cobertura, ou patchar template se Triager forçar seções vazias
que sinalizam over-fit ao Reporter.

Itens deferidos do Reporter spec §8.4 a decidir forçadamente na
sessão Triager (per spec §8.4):

- Callouts 💡 inheritance no template-subagent (Reporter spec teve
  callouts pedagógicos; padrão para todos os subagentes?).
- `requires_human_review` semantic forward-ref ao Matcher spec
  (Reporter spec declarou campo presente no Report; Matcher spec
  ainda não autorou semantics de quando o campo é true).
- Pydantic structuring de `scope` (decidido como string flat no
  Reporter spec; opcionalmente migrar para tipo nominado quando
  Matcher precisar discriminar).

Sessões subsequentes pós-Triager-sanity: Detector → Classifier →
Matcher (~3-4 sessões Chat, complexidade crescente) → coordinator-
flesh-completo → companion edits arch-overview (three-beats Beat 2)
→ ADR-0012 retroativo Milestone C → decomposição de tasks T11+ →
benchmark de PRs sintéticos → gate milestone-level.

## #43 — 2026-05-28 — Triager spec v0.1.0 (autoria + 5 rodadas de review cross-doc)

**Artefato principal:** `docs/specs/subagents/triager.md` v0.1.0 (~800 linhas), MERGED.
**Sessões Chat:** continuação da #43 (autoria iniciada em sessão anterior, compactada).
**Pattern:** terceira subagent spec (após coordinator v3, reporter v0.3.0). Branch B (`output_format=json_schema`), primeiro subagent sem custom tool.

### Conceitos da prova exercitados

- **D1 Agentic Architecture** — agentic loop termination (2 mecanismos: convergência semântica via output_format + budget hard via max_turns/max_budget_usd); `ResultMessage.subtype` (5 valores canônicos); coordinator-subagent orchestration; pattern A'' (sem AgentDefinition).
- **D2 Tool Design & MCP** — tool scoping per subagent (`Read`+`Glob` sem `Grep`); "Read-only analysis" como pattern canônico (tabela Common tool combinations); asymmetry `tools=["Read","Glob"]` (Triager) vs `tools=[]` (Reporter); strict_mcp_config + mcp_servers={}.
- **D4 Prompt Engineering & Structured Output** — `output_format=json_schema` + validation-retry loop nativo do SDK; discriminated union via Pydantic (anyOf, limite 16, custo exponencial); few-shot 3-5 exemplares com `<example>` XML tags; tool_use JSON schema.
- **D5 Context Management & Reliability** — error propagation (subtype × stop_reason, 2 eixos); refusal handling (`stop_reason="refusal"` dentro de `subtype="success"`); provenance/versioning coupling.

### Decisões documentadas (DDs) — 13 fechadas, 3 abertas

- Fechadas por design: T01 (Branch B), T02 (discriminated union), T03 (Read+Glob), T04 (quíntupla+eixo), T06 (max_turns=20 provisional), T07 (PR-level), T08 (sem trinque jurídico), T09 (4 few-shot), T10 (não toca requires_human_review), T12 (loop termination 2 mecanismos), T13 (subtypes canônicos), T15 (layout `src/subagents/<name>/`).
- Fechada via deferment-para-produção: **T11** (Opus 4.7 adaptive em dev; Haiku 4.5 candidato pós-validação funcional — doc ticket-routing recomenda Haiku, mas otimização de modelo introduz variável durante calibragem).
- Abertas (aguardam evidência T11+): **T05** (changed_paths → Classifier spec), **T14** (reasoning field no schema), **T16** (oneOf/discriminator + SDK output_format).

### Decisões de arquitetura ratificadas pelo João

- **Modelo:** Opus 4.7 adaptive thinking para tudo durante desenvolvimento; sem otimização de custo prematura.
- **Layout:** convenção uniforme `src/subagents/<name>/` (não Branch A→coordinator/, Branch B→subagents/). Implica migration do Reporter → Provisão MC-F.
- **Timing MC-F:** PR housekeeping pré-T11+ (caminho (a)), não durante implementação.
- **Report.scope = TriagerInput literalmente** (caminho (i)): versioning coupling deliberado entre TriagerInput e Report payload; rejeitadas alternativas (mapper layer / sparse field-set).
- **dontAsk em Python:** registrar como side finding (caminho (a)), não smoke-test agora.

### Defense candidates (12) — material p/ Capítulo de Método

1. Heterogeneidade per concern em output mechanisms (Branch A vs B).
2. Validation-retry loop como capability nativa do runtime (delegar onde a evidência de robustez existe).
3. Smoke-test gate como caminho mais curto vs changelog spelunking.
4. Verificação cross-doc para falsificar inferência de revisores (capturou: D1/D3 falsos positivos meus; "read-only trio" fabricado por reviewer; refusal absorption claim errado; misframe Reporter §5.4).
5. Template-hipótese exposto por single-responsibility extrema (§4/§6/§7 condicionais).
6. Assimetria deliberada como sinal arquitetural, não débito.
7. Calibração phase-aware (max_turns=20 + modelo Opus em dev; measure-before-tune).
8. Convergência informativa com pattern canônico Anthropic (ticket-routing) — ancoragem, não cargo-cult.
9. Contrato observável documentado supera contrato observável inferido (5 subtypes + 7 stop_reasons verbatim da doc).
10. Refusal como classe de erro estruturalmente distinta de validation failure (2 eixos da ResultMessage).
11. Débito catalogado como Provisão é menos custoso que débito implícito (DD-T15 → MC-F).
12. Acoplamento explícito ratificado supera ambiguidade deferida (Report.scope = TriagerInput).

### Pesquisa em docs oficiais (7 páginas)

agent-sdk/structured-outputs, build-with-claude/structured-outputs, handling-stop-reasons, agent-sdk/agent-loop, use-case-guides/ticket-routing, prompt-engineering/multishot-prompting, build-with-claude/effort, tool-combinations. Achados load-bearing: lista canônica de subtypes/stop_reasons; anyOf limite 16 + custo exponencial; Haiku 4.5 recomendado p/ ticket-routing; effort não suporta Haiku; grammar compilation cache 24h.

### Side findings pendentes

- **`dontAsk` em Python:** doc diz "TypeScript only" mas funciona em Python (Gate 1 + sdk_output_format_lockdown PASS). 3 hipóteses (doc stale / no-op silencioso / undocumented funcional). Smoke-test ~20min antes de ADR-0012 retroativo sobre defesa em camadas.
- **SF-2 RateLimitEvent:** README do smoke-test afirma "não observado antes" — falso, coordinator §11 AC2 documenta desde Gate 1. Companion edit corrige.

### Processo

5 rodadas de review cross-doc do Code. Convergência limpa. Cada rodada expôs débito invisível anterior (quíntupla mal-enumerada, MC-F scope incompleto, errorCode count 6→7, misframe §5.4) e converteu em edit concreto — defense candidate #11 demonstrado em tempo real pelo próprio processo.

### Próximo passo

1. (Esta sessão) learning-log #43 + session-handoff. ✓
2. (Próxima Code) Provisão MC-F + companion edits da sessão #43.
3. (Sessão fresca) Fase 2 — destilação `_template-subagent.md` a partir de Reporter v0.4.0 + Triager v0.1.0 estáveis.

## #44 — 2026-05-28 — MC-F housekeeping: Reporter 0.4.0 + migração de locus + companion edits (PR #73)

> Materializa o "#43+ housekeeping" antecipado pelo handoff pós-#43. Confirmar o número de work-session contra o contador antes de commitar (lição #11/#12: chat-numbering ≠ work-session-numbering pode driftar).

**Escopo.** Sessão Chat de prep (4 versões de prompt) + sessão Code de execução (GATE 0 pre-flight → plan-mode GATE 1 → Fase 2 faseada) + review cross-doc convergente entre as duas. PR única, mecânica, 100% docs/specs (sem código). Fecha a Provisão MC-F, desbloqueando a próxima spec de subagente.

**Artefato principal:** PR #73 — squash `c5e7751` em `main`. 6 commits internos (`b0d1dc4` → `d66db74`), +73/-31, 5 arquivos.

### Conceitos da prova exercitados

**D5 — Context Management & Reliability (15%).** Domínio dominante desta sessão.
- **Provenance/citations.** T6 corrigiu um provenance bug no README do smoke-test (`RateLimitEvent` declarado "não observado" quando já tinha locus documentado em coordinator §11 AC2). A correção citou a observação prévia em vez de polir a frase.
- **Exclusion-aware regression gates (line-level).** G1 distinguiu refs vivas de audit trail *dentro* dos arquivos editados (reporter:5 #41/#42, reporter §10, coordinator:5) — exclusão por linha, não por file-glob.
- **State passing / shared state.** DD-T05 (`changed_paths` pré-computado vs redescoberto via Glob) confirmada como decisão de passagem de estado entre stages — deferida à Classifier.

**D4 — Prompt Engineering & Structured Output (20%).**
- **`output_format=json_schema` (forma wire-level).** T1 confirmou empiricamente, contra `smoke_test.py` (SDK 0.2.87, lines 110-113), que a forma aceita é envelopada `{"type": "json_schema", "schema": ...}` — não a forma nua da prescrição da Triager §10.5 item 1, que é shorthand. Achado registrado em reporter §10.6; follow-up à Triager catalogado.
- **Few-shot examples como behavior anchors.** D4-1/D4-2 corrigiram o shape de `scope` em few-shots que contradiziam o tipo `TriagerInput` declarado — anti-pattern de structured output (exemplo que contradiz o schema é sinal conflitante ao modelo).
- **Multi-instance review.** v1→v4 do prompt + GATE 1 do plano: convergência monotônica, sem regressão de catch.

**D1 — Agentic Architecture & Orchestration (27%).** Tangencial.
- **Dual loop-termination.** T1 adicionou `max_turns=20` (budget hard) ao lado de `output_format` (convergência semântica) no invocation do Triager — os dois mecanismos coexistentes do Task Statement 1.1.
- **Tolerância a tipos não-padrão no loop.** T2 documentou log-and-continue para `RateLimitEvent` no `async for` de todos os stages (propriedade stage-agnóstica do coordinator).

**D2 — Tool Design & MCP (18%).** Leve — a migração de locus dos módulos (`src/subagents/reporter/`) é organização de código mais que tool design; o aperto `scope: dict` → `TriagerInput` toca contract typing.

### Decisões

| ID | Decisão | Resolução |
|----|---------|-----------|
| DD-HK-1 | Migração total (módulos Reporter + refs do coordinator → `src/subagents/reporter/`) | Ratificação retroativa de DD-T15; pró-split rejeitado (contradiz triager.md §1.5 em main) |
| DD-HK-4 | Corrigir shape de `scope` nos few-shots, restrito a `scope` (findings deferidos à Matcher) | Incluído |
| C-AUDIT | coordinator:5 Status: anotação in-line preservando 0.3.0 + locus histórico, nomeando os 3 módulos | Opção (b) |
| T6 | Texto prescrito Triager §10.5 item 6; ref `§5/#2 acima` substituída por `§3.1 nesta PR` | Substituição (c) |
| T1 (empírico) | `output_format` forma envelopada (não nua) | Confirmado contra smoke_test.py 0.2.87 |
| DD-T05 | `changed_paths` permanece **aberta**, deferida à Classifier | Próxima sessão |
| Ordem de specs | Classifier **antes** de Detector | Inversão deliberada da ordem #37 (Detector→Classifier) |

### Defense candidates metodológicos (para TCC)

Os quatro abaixo são corolários de **um** princípio: *todo locus que afirma um fato precisa de uma cadeia de proveniência verificável até a fonte; drift documental é proveniência distribuída quebrada.*

1. **Audit semantics são relativas ao evento, não ao token.** reporter:5 (sujeito do bump → ganha entrada nova F-STATUS) vs coordinator:5 (sujeito do sync histórico → anotação preservando 0.3.0). Mesmo problema (Status load-bearing, sem prefix-swap cego), tratamento oposto. "Preservar verbatim" não é regra uniforme.
2. **Provenance bug canônico (T6).** Claim de novidade ("nunca observado") sem verificação contra o registro. Correção = citar o locus prévio, não polir a frase. Regra geral: claims de proveniência (primeiro/único/inédito) exigem verificação contra registro, não tratamento editorial.
3. **Não importar referência quebrada por fidelidade cega (T6 opção c).** O texto prescrito da Triager carregava `§5/#2 acima` (refs inexistentes fora do contexto da Triager). Aplicar a própria disciplina de proveniência ao texto prescrito — recursão.
4. **Fato estabelecido precisa propagar a todos os loci (Commit 6).** A forma envelopada confirmada em T1 → §10.6 (reporter) → follow-up tasks.md (Triager §10.5 item 1). O locus não-atualizado vira a próxima fonte de drift — exatamente como a forma nua sobreviveu até aqui.

5. **Meta — multi-instance review converge porque as instâncias particionam o espaço de erro.** v1 errou *escopo* (5-7 vs ~18 loci); v2 acertou arquitetura mas *duplicou/subcontou*; v3 fechou *completude*; v4 pegou *audit semantics*; GATE 1 pegou *fidelidade de execução* (T6 invertido, T2 no stage errado). Degradação monotônica do tipo de catch, sem regressão. Não é repetição da mesma verificação com mais cuidado — é cobertura por loci de atenção ortogonais. A defesa contra drift documental não é uma regra única, é um conjunto de gates com framings ortogonais.

### Próximo passo

**Sessão Chat — Classifier spec** (resolve DD-T05; desbloqueia o companion edit órfão arch §5.2). Inversão deliberada da ordem #37 — registrada como tal, não silenciosa. Carregar `reporter.md` 0.4.0 + `triager.md` 0.1.0 como anexos. Sequência subsequente: Detector → Matcher → coordinator-flesh-completo → ADR-0012 retroativo → decomposição T11+ → benchmark PRs sintéticos → gate milestone-level.


## #45 — 2026-05-28 — Classifier spec v0.1.0 autorada a mergeable

- **Work-session:** #45 (contra o contador; #44 era MC-F). Inversão consciente da ordem #37 (Classifier antes de Detector) — registrada no session-handoff.
- **Artefato:** docs/specs/subagents/classifier.md v0.1.0 (Branch B, consome policy://vocabularies + policy://examples). Mergeable após 3 rodadas de review cross-doc (Code).
- **Conceitos da prova exercitados:**
  - D2 (Tool/MCP): Resource vs Tool como fronteira de *capability* (Classifier lê vocab sem tools decisionais); scoped access per-server, não per-resource; `tools` (availability) vs `allowed_tools` (denial-on-miss) — MCP resource tools habilitadas por mcp_servers, não pelo campo tools.
  - D4 (Structured Output): output_format envelopado; required-nullable vs optional (null explícito p/ audit, RF-003); objeto-wrapper evita root-array + eixo DD-T16; few-shot dividido por camada.
  - D5 (Reliability): error_max_structured_output_retries; verificação posicional de ordem/identidade (SubagentContractViolation); degradação graciosa vs falha alta.
- **Decisões fechadas:** DD-C2 (membership soft+null, sem Enum), DD-C3 (Branch B), DD-C4 (shape + escalares required-nullable), DD-C10 (few-shot positivo → policy://examples, camada 1, por analogia a ADR-0005 D8), DD-C12 (ordem/identidade = contrato hard posicional). DD-C1 (=DD-T05) declarada fora-de-contrato do Classifier.
- **Decisões deferidas:** DD-C5 (carimbo de versão de vocab), DD-C6 (max_turns escala — constante 20 no MVP + backstop), DD-C7 (DetectorFinding ratif.), DD-C8 (reasoning field), DD-C9 (postura do Matcher), DD-C11 resíduo (tool-result vs in-prompt, A/B T11+).
- **Companion edits catalogados (§10.5):** coordinator §3.3 (output_format + max_turns + POLICY_READER_CONFIG locus + capture loop rico + SubagentContractViolation em src/coordinator/errors.py); detector.md (ratificar DetectorFinding); matcher.md (DD-C9); ADR-0012 retroativo; **policy://examples como PR autônomo** (policy-reader §3 + ADR-0005 Decisão 9 + SCHEMA §2 + seed LGPD ≥2) — prereq de merge.
- **Defense candidates (Cap. Método):** (1) cross-doc falsifica inferência de revisor em tempo real — leitura verbatim de triager.md derrubou meu argumento de blast-radius em DD-C1; (6) pureza vs pragmatismo — melhoria de camada (DD-C10) não está completa até a obrigação que preserva a funcionalidade deslocada (seed ≥2) estar fechada de forma concreta, não condicional. Material mais nítido da sessão.
- **Erro corrigido:** citação de ADR-0005 D8 como autoridade para examples (D8 decide *regras*) → reformulada como analogia + Decisão 9 forthcoming.
- **Próximo passo:** PR autônomo do policy://examples (com seed ≥2) merge primeiro; depois Classifier ramifica do main corrigido → Fase 0 smoke (gate-of-gates) antes de qualquer linha de produção. DD-T05 fica para sessão coordinator/Triager.

## #46 — 2026-05-29 — Detector spec v0.1.0 autorada a mergeable (verificação externa pós-cutoff + reconciliação de dois reviews)

> Continuação natural da inversão #37: Classifier (consumidor) autorado em #45, Detector (produtor) agora. Sessão Chat pura. Confirmar nº de work-session contra o contador antes de commitar (lição #11/#12): topo do learning-log era #45, session-handoff "pós #45" → esta é **#46**, sem drift chat↔work-session.

**Escopo.** Sessão Chat de ponta a ponta sobre `docs/specs/subagents/detector.md`: (1) pre-flight verbatim dos DDs contra os docs âncora (método da Classifier, prep-first — não redigir prosa antes de fechar os DDs load-bearing); (2) verificação externa contra doc oficial vigente (SDK/MCP/Semgrep) por estar além do cutoff Jan/2026; (3) autoria da spec completa (10 seções) com os 5 DDs codificados; (4) reconciliação de **dois** reviews cross-doc do Code (um da sessão-DD, um clean) com dois conflitos genuínos; (5) micropatches de fechamento após adjudicação verbatim. PR a materializar: `feat/detector-spec` (a aplicar pelo Code). 0 commits em main na sessão; output em `/mnt/user-data/outputs/`.

**Artefato principal:** `detector.md` v0.1.0 mergeable. Branch B, consome `scan_diff` do `semgrep-runner` + `Read`. 5 DDs fechados; 3 `⚠` remanescentes (decisões futuras do coordinator), 0 resíduo de pesquisa.

### Conceitos da prova exercitados

**D2 — Tool Design & MCP Integration (18%).** Domínio dominante.
- **`isError` flag — convenção canônica vs desvio do projeto.** Spec MCP 2025-11-25: tool execution errors (business/system) reportados com `isError:true` para o modelo ver e se autocorrigir; só protocol errors ficam fora da visão do modelo. O `scan_diff` usa **Option B** (wire `isError:false` sempre, discriminar por `errorCode`) — desvio deliberado (ADR-0002), justificado por fricção FastMCP que a verificação externa **confirmou persistente em 2026** (ContextForge, edgartools mis-validando `isError:true` contra `outputSchema`). Consequência: o reconhecimento de erro é forçado ao prompt + inspeção determinística do stream pelo coordinator.
- **Scoped tool access como firewall.** `tools=["Read"]` + allowlist `mcp__semgrep-runner__scan_diff`; sem `policy-reader`/`Glob`/`Grep`. A ausência **é** o firewall epistêmico (impossibilidade física de pré-julgar cláusulas), não economia de tokens. Distinção `tools` (built-in availability) vs `allowed_tools` (denial-on-miss); tool MCP habilitada por `mcp_servers`.
- **Tríade tools/resources/prompts.** MCP oficial do Semgrep (`semgrep mcp`, migrado para o binário) expõe `semgrep_scan` (tool, content-based), `semgrep://rule/schema` (resource), `write_custom_semgrep_rule` (prompt) — exemplo concreto. Build-vs-reuse: o oficial é content-based, não diff-over-refs → `scan_diff` caseiro cobre gap real (registro em §8.4, fora dos DDs).

**D5 — Context Management & Reliability (15%).**
- **Provenance/citations — trickle-down via envelope.** `DetectorOutput = {findings, provenance}`; provenance **per-scan** no envelope (não per-finding — duplicar N× seria semanticamente errado). Preserva a cadeia "regra X / rule set Y / Semgrep Z / diff A→B" através do boundary Detector→Classifier→Reporter, em vez de morrer no primeiro hop.
- **Error propagation + escalation.** Roteamento por `isRetryable`: `SCAN_TIMEOUT` (retryable) → retry; `GIT_REF_NOT_FOUND` (non-retryable) → escalação / `run_outcome="error"`. Nunca aliasar erro com `findings:[]` (colidiria com o caso-válido empty-result).
- **Stream-inspection determinística** como pattern ratificado (#37/#38: `ReportNotEmitted`, captura de payload do Reporter) aplicado a novo sítio. Sinal reliability-critical não depende do modelo discriminar.
- **Context window budget.** `surrounding_context` bound no produtor, banda floor (Classifier extrai sem re-`Read`) / ceiling (não inflar prompt downstream / lost-in-the-middle); N=±10 inicial.
- **Refusal handling.** `stop_reason="refusal"` pode coexistir com `subtype="success"` (refusal tem precedência sobre schema — verificado verbatim). Caveat de impl: acesso direto a `stop_reason` em result message pode ser TS-only; Python pode exigir varredura de stream.

**D4 — Prompt Engineering & Structured Output (20%).**
- **`output_format=json_schema`** forma envelopada confirmada corrente; validation-retry → subtype `error_max_structured_output_retries` em exaustão.
- **Contract versioning — severidade = blast radius, não esforço.** Adição de campo a `DetectorFinding` é **major** (não minor) porque é o shape consumido pelo Classifier: mecanismo = acoplamento de passthrough no `ClassifiedCandidate` (`extra="forbid"` no output); manter major alinha com fail-loud (vs drop silencioso).
- **Few-shot como behavior anchors** particionando o espaço (normal / vazio / erro); Exemplo C ancora o reconhecimento prompt-level do erro sob Option B.

**D1 — Agentic Architecture & Orchestration (27%).** Tangencial.
- Branch B (output_format, sem custom tool); tabela subtype × stop_reason; coordinator-subagent com desempacotamento de envelope no boundary.
- **Multi-instance review** com classes ortogonais: dois reviews do Code (sessão-DD + clean) particionaram o espaço de erro — o da sessão-DD pegou numbering/`build_detector_prompt`/etapa, o clean foi fundo no `extra="forbid"`/invariantes.

### DDs fechados

- **DD-D1** (ratificação `DetectorFinding` + mapeamento strip-opinion/keep-provenance) — por articulação do firewall já normado em arch §5.3.
- **DD-D2** (budget `surrounding_context`) — bound no produtor, janela ±10 simétrica, banda floor/ceiling, calibragem T11+.
- **DD-D3** (envelope + provenance per-scan) — coordinator desempacota; Classifier recebe `list[DetectorFinding]` puro; provenance → scratchpad `02-detector.json` + Reporter.
- **DD-D4** (output mechanism) — Branch B, herança do envelope wire form (reporter §10.6).
- **DD-D5** (propagação de erro do `scan_diff`) — inspeção determinística do stream; roteamento por `isRetryable`; defesa em profundidade (stream + regra prompt-level de não-fabricação); triangulação via DD-D3.
- **DD-T05** (`changed_paths`) — neutra ao Detector, registrada não reaberta.

### Decisões de reconciliação (dois reviews)

- **Conflito 1 — `extra="forbid"` mecanismo (A: output / B: input).** Fechado por leitura verbatim #46 (`classifier.md:127,134,145` + :135 + :153): Review A correto — modelos de **output**, quebra por **acoplamento de passthrough** no `ClassifiedCandidate`, não validação de input. Severidade **major** mantida (B): convenção `classifier.md` §7.1 + fail-loud.
- **Conflito 2 — número de linha do `ReportNotEmitted` (A: 280/408 / B: 245-256).** Resolvido por **âncora semântica** em vez de linha nua — o conflito é a prova de que linha drifta.
- **Correções factuais folded:** RF-002→**RF-001** (RF-002 é cobertura, do rule set); `build_detector_prompt` **já existe** com signature `(pr_metadata, triager_output)` → reconciliar, não criar; `DetectorInput` é tipo notacional (Branch B não valida input via Pydantic); dualidade Etapa 2 (coordinator) / Etapa 1 (arch); `ScanProvenance` no Reporter é adição confirmada (minor bump dele).

### Defense candidates (método — material p/ Capítulo de Método)

1. **Reconciliação de reviews divergentes como pattern, não só achado.** Separar **severidade** de **mecanismo** no §7.1 tornou o conflito decidível: a severidade era major por convenção independentemente de quem estava certo; só o mecanismo estava em disputa, e era fechável por leitura verbatim. Desacoplar o que é adjudicável do que não é.
2. **Verificação externa contra doc pós-cutoff como provisão de proveniência.** Cutoff Jan/2026, prova Mar/2026, SDK muda rápido → verificar antes de inferir; achados materiais codificados na spec (Option B vs canônico, fricção persistente, forma do output_format, refusal precedence). Não inferir sintaxe de SDK da memória.
3. **`⚠` markers como disciplina de proveniência.** Marcar explicitamente o não-verificado (número de RF, loci de linha, namespace) em vez de reconstruir da memória — exatamente a lição dos #11/#12 e do provenance bug T6. ~12 dos ~15 fechados pela verificação dos reviews; os 3-4 restantes são decisões futuras genuínas.
4. **Âncora semântica > linha nua sob drift.** Quando dois reviews divergem no número de linha, o número é o problema; citar por âncora semântica imuniza contra evolução do arquivo referenciado.
5. **Contract versioning por blast radius.** A severidade do bump é função do impacto no consumer (passthrough + `extra="forbid"`), não do esforço da mudança. Um campo "só adicionado" pode ser major.
6. **strip-opinion / keep-provenance** como princípio de boundary — descartar a opinião do Semgrep (`rule_severity`/`rule_message`) preservando a proveniência (versions/refs). Articula o firewall epistêmico que arch §5.3 já normatiza.

### `⚠` remanescentes (3-4 decisões futuras, não resíduo)

- `output_format`/`max_turns` no skeleton `coordinator.md` §3.3 (companion edit).
- Taxonomia `DetectorScanFailed` vs `run_outcome="error"` (decisão do coordinator).
- Valor de `max_turns` (30 provisional vs herdar 20 — `⚠ DECISÃO` do autor).
- Detecção de refusal em Python (stop_reason TS-only — risco de impl, smoke-test do coordinator).

### Próximo passo

1. (Code) Aplicar `detector.md` v0.1.0 ao repo via PR `feat/detector-spec`.
2. (Companion edits do coordinator) declarar `output_format`/`max_turns` no §3.3; reconciliar signature de `build_detector_prompt`; decidir taxonomia `DetectorScanFailed`; registrar scratchpad `02-detector.json`.
3. (Reporter) minor bump + emenda do schema do Report para aceitar/citar `ScanProvenance` (forward-ref DD-D3).
4. (Housekeeping separado) registrar build-vs-reuse (MCP oficial Semgrep) em `semgrep-runner/canonical.md` §7 ou nota ADR-0010.
5. (Sessão fresca) **Matcher spec** — próximo subagente na sequência do handoff pós-#45 (Detector → Matcher → coordinator-flesh-completo → ADR-0012 retroativo → decomposição T11+ → benchmark PRs sintéticos → gate milestone-level).

## #47 — 2026-05-29 — Consolidação coordinator pré-Matcher (parcial) + verificação empírica de canais MCP/SDK

> Contador: topo era #46 (Detector spec); session-handoff "consolidação coordinator (pré-Matcher)" → esta é **#47**, sem drift chat↔work-session (confirmado contra o arquivo).

**Conceitos da prova exercitados**
- D1 — `stop_reason` em `ResultMessage` (Python, acesso direto, 0.1.46+); refusal; error propagation.
- D2 — convenção `isError`/`is_error` por camada; Option B (ADR-0002); canal de erro de tool por tipo de server; Resource-vs-Tool capability boundary (ADR-0005); `outputSchema` × envelope de erro.
- D3 — `.claude/rules/` frontmatter com `paths:` glob; fronteira Chat↔Code (mecânico vs deliberativo); companion-edits-as-debt-registry.
- D4 — `output_format` json_schema envelope; `oneOf`/discriminator NÃO compila gramática vs `anyOf` nullable que compila; validation-retry; beta header structured-outputs.
- D5 — `run_outcome="error"` + coverage-gap; provenance; verification-before-inference; RESULTS.md como scratchpad de proveniência.

**Decisões**
- Item 3 RESOLVIDO: `DetectorScanFailed` exceção tipada `(stage, tool, errorCode, isRetryable, details)`, projetada externamente como `run_outcome="error"`; hierarquia (irmã vs base) deferida ao Matcher. 3 peças ao coordinator §5 + 2 follow-ups (`tasks.md`).
- `sdk-mcp-conventions.md` expandida a dois eixos (casing + discriminador) + constraint Option-B/outputSchema.
- DD-T16 RESOLVIDO: saída Branch B = objeto enum-tag (`verdict: Literal[...]` + opcionais `anyOf [T,null]`), **nunca** união discriminada. `oneOf` desliga a gramática silenciosamente (success + `structured_output=None` + JSON não-conforme).
- Versão SDK `0.2.87` confirmada real (changelog público do GitHub estava stale); item 4 (refusal Python) mecânicamente resolvido — `stop_reason` no `ResultMessage`.
- Contrato Matcher pré-identificado: output shape pinado por `reporter.md §2.2` (sem `candidate_ref`); seleção de cláusula especificada em `classifier.md:175` (`check_applicability`/`applies_to`, não `find_clauses_by_law_article`).

**Artefatos** (pendentes de commit — PR único da #47)
- `coordinator.md §5` (item 3, 3 peças) · `docs/tasks.md` (2 follow-ups)
- `.claude/rules/sdk-mcp-conventions.md` (dois eixos)
- `_envelope.py` + `server.py` (GUARD Option-B)
- `scripts/smoke_tests/sdk_tool_error_channel/` (v1–v4 + RESULTS.md)
- `scripts/smoke_tests/sdk_output_format_complex/` (smoke_test + RESULTS.md; probe de mecanismo dobrado no RESULTS, `_probe_*` removido)

**Observação de processo**
- Verificação corrigiu inferência ~7×: changelog stale (0.2.87), contagens de refs, §-âncoras não-paralelas, bug de profundidade do veredito v3, timing de stdio do v4, a redação do Eixo 2 sobre `emit_report`, e o `"reason"`-vs-`"rationale"` que afinou o mecanismo DD-T16. A disciplina segurou; os exit codes automáticos mentiram em 4 dos smoke-tests (documentado nos RESULTS).

**Próximo passo**
- Commit/PR único da #47 (3 fios: item-3, sdk_tool_error_channel, sdk_output_format_complex).
- #48 = autoria de `matcher.md` (handoff dedicado).
- Pendentes não-resolvidos: item 1 (`output_format`+`max_turns` §3.2/§3.3, agora com sub-task de smoke-testar schemas reais enum-tag); item 4 EDIT (remover caveat "TS-only" dos §6.3 + restaurar tabela H2 — mecanismo confirmado, edit não aplicado); A4 (`config.py`); ADR-0013; reconciliação de taxonomia.

## 2026-05-29 — Sessão #48: autoria + hardening da matcher.md (último subagente)

### Conceitos da prova exercitados
- **D1 — Agentic Architecture.** Coordinator NÃO é agente: é código Python que liga output→input entre `query()`s. Consequência de design ratificada (H1/DD-M22): handshake jurisdicional, se existir, é `if framework not in ACCEPTED: abort` no boot do coordinator, não lógica de agente no Matcher.
- **D2 — Tool Design & MCP.** Achado central da sessão: **dois tipos de "MCP tool" com governança oposta** — (1) server tools (`mcp__*`) governados por `mcp_servers`, sobrevivem a `tools=[]`; (2) built-ins de acesso a resource (`ReadMcpResourceTool`/`ListMcpResourcesTool`) governados pelo `tools` field, invisíveis se não listados. Issue #361 da SDK fala de `allowed_tools` (verdadeiro), NÃO do `tools` field — distinção que quatro docs haviam conflado. Option B (errorCode em structuredContent, isError=false). `extra='forbid'` no input da tool → projeção rename+drop.
- **D3 — Claude Code Config.** `tools` field como eixo de availability ortogonal à quíntupla de denial-on-miss. `tools=[]` (Gate 6) correto pro Reporter (emit_report é server tool), errado pro Matcher/Classifier (precisam dos built-ins de resource). `output_format` enum-tag, `max_turns`.
- **D4 — Structured Output.** enum-tag (`Literal` + `anyOf[T,null]`), nunca `oneOf`/discriminated-union no schema wire-level. Orçamento: 24 opcionais / 16 uniões / 180s.
- **D5 — Context & Reliability.** Trinca de provenance verbatim por finding; honestidade epistêmica (não marcar gate PASS sem evidência do shape específico); determinismo do motor (templates f-string) vs enumeração do LLM (não garantida por construção).

### Decisões load-bearing ratificadas
- **C1** — input contract: nomes reais do Classifier (`operation_type`/`declared_legal_basis`/`declared_transformations`), projeção = rename+drop, DD-M10 invertido (passthrough no finding; rename só na projeção pra tool).
- **C2** — curto-circuito de contexto insuficiente: `operation_type:null` / `data_categories:[]` são saídas VÁLIDAS do Classifier → Matcher emite `not_applicable`+`requires_human_review` sem chamar a tool (carve-out declarado de DD-M26).
- **H1 (opção c)** — handshake jurisdicional descartado por YAGNI no MVP co-versionado; eixo estrutural já server-side; dono futuro = código do coordinator. NÃO "agnóstico".
- **H2/DD-M30** — Matcher e Classifier listam os built-ins de resource no `tools` field. Verificado #48-b.
- **R1** — finding de curto-circuito fonta a trinca de `policy://schema-version` (loop e system prompt instruídos a ler o resource no startup).
- **M-a** — `INVALID_OPERATION` tem dois sub-casos: null/ausente → contexto insuficiente; token fora-de-vocab → falha alto (simétrico a INVALID_DATA_CATEGORY).

### Lição de método (candidato a Capítulo de Método)
**O achado do `tools` field atravessou quatro camadas de revisão, e cada uma corrigiu um modo de erro DIFERENTE do mesmo fato:**
1. #48-b mediu (shape do Matcher, `tools=[]`).
2. Eu (Chat) propaguei incompleto — corrigi só a prosa de `classifier:45`, deixei a config gêmea do Classifier intocada.
3. Sessão clean (review sem contexto) pegou a config gêmea quebrada (`coordinator:119`).
4. Code refinou a raiz conceitual — preservou o Issue #361 (verdadeiro sobre `allowed_tools`), consertou só a extensão indevida (ao `tools` field); e RECUSOU marcar o gate PASS até o shape específico do Classifier ser medido e persistido.

**Corolário aprendido:** "verificação-antes-de-inferência" tem dois modos de falha simétricos — **inferir o que não se mediu** (foi o erro de C1: autorei §2 contra memória sem reler classifier.md) e **não propagar o que se mediu** (foi o erro do H1-Classifier: medi o Matcher e não estendi ao subagente irmão que depende do mesmo mecanismo). Quando uma medição derruba uma crença, a crença tem de ser caçada em TODOS os loci onde foi escrita, não só onde a medição calhou de tocar.

**Custo concreto:** C1 e H1 foram o mesmo erro de origem (autorar contra o ledger/memória em vez de reler os artefatos que o próprio ledger marcou "a confirmar na autoria"). Custou um ciclo inteiro de review+probe. A spec saiu robusta, mas o caminho curto era a releitura na escrita.

### Artefatos
- `matcher.md` 0.1.0 (spec do último subagente; vive em Chat/outputs, não no repo) — C1/C2/H1/H2/M1/M2/L1/L2 + R1/R2/R3/M-a/M-b/M-c + cascata tools-field, todos folded.
- `scripts/smoke_tests/check_applicability_48b/` — `probe.py` (C2/H1 in-process) + `h2_probe.py` (H2 live, 4 shapes de `tools`) + **`RESULTS.md` persistido** (gate resource-access fechado).
- Edits no working tree (não commitados): `coordinator.md` (§3.3/§3.4/§2/§3.3-nota/§10), `classifier.md` (§1.4/§10.3/§10.5-escopo-ADR/Gate 6).
- Smoke-test #48 (`check_applicability`, in-memory, não persistido) — 13/13 + probe §5.

### Próximo passo
- Abrir PR `<branch-da-sessão>` (um PR por sessão): coordinator.md + classifier.md + RESULTS.md novo. Confirmar working tree dirty antes do `git add` — deixar Beat 2/housekeeping de sessões anteriores FORA. Mencionar no corpo que o gate resource-access foi exercitado live.
- `matcher.md` 0.1.0 mergeia por seu caminho de specs-fora-do-repo.
- ADR-0012 retroativo: autoria deferida a sessão dedicada (escopo já carimbado; rationale é Chat/João, não Code a frio).
- Pendentes de outras sessões (não deste PR): M1 (classifier §3.3), jurisdictional defer (canonical §3.2/§6.3 + arch §5.5), reporter:135 (L2), detector §6.3 (confirmar antes), tasks.md, session-handoff l.63.

## #49 — 2026-05-30 — Reconciliação cross-doc C1–C14 + três PRs (housekeeping, dep-add, Branch B output-contract)

**Escopo da sessão.** Sessão de verificação e reconciliação (não de
autoria nova). Fechou o parecer cross-doc de 14 inconsistências (C1–C14)
distribuídas pelas 6 specs de subagente, em três PRs sequenciais
mergeados, deixando os pré-requisitos de contrato do coordinator-flesh
(MC-A) resolvidos.

Resultado tangível, três PRs:
- **PR #82** `chore/cross-spec-housekeeping` (commit b0cb389) — reconciliou
  C4, C5, C6, C7, C8, C9, C11, C14 + correção da citação `tools.py:263-279`
  nas três pontas (ADR-0012 D5, classifier:175). 8 docs, +28/−14.
- **MC-E** `chore/add-claude-agent-sdk` — pin `claude-agent-sdk==0.2.87`
  em pyproject/uv.lock + 2ª emenda in-place ao ADR-0001 D2 (formalização
  de pin pós-resolução, mesmo tipo da emenda 2026-05-21). Fechou o
  forward-ref carregado pelas specs (reporter §1.5) + MC-E.
- **`docs/branch-b-output-contract`** — fechou C1, C2, C3 (+ P4). Contrato
  de structured output do Branch B como superfície única. 7 docs,
  +168/−76.

**Conceitos da prova exercitados.**

*Domínio 4 — Prompt Engineering & Structured Output.* Verificado contra
doc oficial (abr/2026): `output_format` no SDK é o dict
`{"type":"json_schema","schema":...}` (campo de `ClaudeAgentOptions`);
no nível da Messages API migrou para `output_config.format` e o beta
header `structured-outputs-2025-11-13` não é mais necessário — mas o
campo do SDK não mudou, logo as specs estão corretas. Structured outputs
são GA em Opus 4.7 (o modelo do projeto), removendo risco latente.
Limites de complexidade confirmados verbatim: 24 parâmetros opcionais,
16 de união (`anyOf`/type-arrays, custo exponencial), timeout de
compilação 180s — **por request**, logo cada subagente (`query()`
separada) tem o orçamento inteiro. Achado empírico do projeto corroborado:
`oneOf`/discriminated-union no root desliga silenciosamente o constrained
decoding; a doc lista `anyOf` como o mecanismo de união suportado, não
`oneOf`. Encoding correto = enum-tag (`Literal` + `anyOf[T,null]`).
Property-ordering: campos `required` saem primeiro.

*Domínio 5 — Context Management & Reliability.* C2/Opção B materializou
provenance trickle-down ao nível arquitetural: o Report passou a carregar
proveniência de **execução** (`scan_provenance` top-level/per-scan) ao
lado da proveniência **legal** (trinca per-finding) — as duas metades da
reprodutibilidade de um achado de conformidade. Report auto-suficiente
para auditoria = propriedade-tese.

*Domínio 3 — Claude Code Configuration & Workflows.* Padrão de review
consolidado: **review = plan mode**. Uma sessão de review aberta em plan
mode é fisicamente incapaz de escrever em arquivo (trava de permissão),
ao contrário do prompt "não edite" que o agente pode ignorar. Lição
aprendida ao vivo: uma sessão clean lançada sem plan mode *implementou* em
vez de revisar — o trabalho era separável (branch própria, uncommitted),
mas o episódio fixou o padrão.

**Decisões de design fechadas.**
- **C1 — `MatcherOutput = {findings: list[Finding]}`**: envelope
  objeto-no-topo, paridade com `ClassifierOutput{classified}` e
  `DetectorOutput{findings, provenance}`. Array-at-root é frágil de
  gramática.
- **C1 — reencode do Triager**: `TriagerDecision` deixou de ser
  discriminated-union (oneOf no root, DD-T16) e virou flat enum-tag —
  modelo wire flat (`decision: Literal` + dois `Optional`), xor migrado
  para `model_validator` (validação), não mais gramática. DD-T02
  **preservada** (nomes direcionais mantidos; só o enforcement amoleceu,
  paralelo ao soft-membership do Classifier). DD-T16 **fechada**.
- **C2 = Opção B (rotear ScanProvenance ao Report)**: `scan_provenance`
  top-level opcional no ReportPayload, presente em todo caminho com scan
  (incl. `success_no_candidates`), ausente só em `skipped_by_triager`.
  Reporter 0.4.0→0.5.0 (minor; campo opcional). Reporter permanece
  passthrough puro (coordinator injeta). Opção A (scratchpad-only) seria
  legítima mas exigiria rebaixar a redação do detector (que já se
  pré-comprometera com "obrigatório") — não era doc-custo-zero.
- **C3**: `output_format` + `max_turns` declarados no coordinator §3.2
  (Detector: `DetectorOutput`, 30) e §3.3 (Classifier: `ClassifierOutput`,
  20). Simetria nos quatro stages Branch B.
- **MC-E**: exact-pin (não range) por reprodutibilidade; nota de
  proveniência registrando wheels por-plataforma com Claude Code CLI
  embutido (declarative vs resolved source, espírito do ADR-0001 D2).
- **P4.1**: invariante PHI-em-schema em `.claude/rules/privacy-safety.md`
  — schemas carregam vocabulário de categoria, jamais valor de dado
  pessoal; verdade por construção, declarada (doc avisa que schema é
  cacheado sem proteção ZDR).

**Princípio de processo (reforçado, vale carregar).**
- **Três níveis de review cumpridos no PR Branch B**: revisão do plano
  (pré-implementação, G1–G6) → implementação com auto-surfaçagem →
  cross-doc por testemunha neutra em plan mode. A testemunha neutra achou
  dois itens que as sessões imersas não viram (matcher §1.4/§10.1 "pendente"
  stale; reporter §2.2 omitindo `scan_provenance` da dict do estado
  consolidado). Validou o terceiro nível de review.
- **Verificação verbatim > inferência**, de novo: a citação `tools.py`
  estava errada em dois loci (268-279 no ADR-0012 D5, 262-273 no classifier);
  o span real (263-279) só apareceu por dump de linha. Mesma classe de erro
  que o caveat TS-only do detector (C7).
- **Squash-merge ⇒ coesão temática do PR é a granularidade de auditoria**:
  motivo de não enfiar o débito 6b (resíduo TS-only cross-ref no matcher)
  no PR Branch B — é de outra superfície (família C7), vira housekeeping.

**Débitos abertos (não-bloqueantes; catálogo do próximo housekeeping).**
1. matcher §6.3 + §10.5(4): resíduo "TS-only pendente de remoção"; detector
   §6.3 já corrigido (PR #82). Fechar cross-ref. (= 6b do cross-doc review.)
2. coordinator §3.4: comentário inline `# enum-tag finding schema` poderia
   citar "envelope MatcherOutput" (cosmético).
3. Antes do PR: grep `TS-only\|TypeScript-only` em `docs/specs/` p/ outros
   resíduos C7.
4. C10 (numeração de "Etapa" tripla) e C13 (DD-T05 changed_paths + arch §5.2)
   — baixa prioridade, não-bloqueantes.

**Próximo passo:** coordinator-flesh-completo (MC-A, 6ª e última spec de
subagente) — C1 ✅, C2 ✅ materializado no schema do Report, C3 declarado;
C12 (`config.py` single-source dos `*_CONFIG`) land junto. Caminho crítico.


## Sessão #50 — 2026-05-31 — coordinator-flesh (MC-A) + companion DD-M22 + abertura de planejamento T11

**Conceitos da prova exercitados**
- D1 (Agentic Architecture & Orchestration): driver único de capture loop (`run_branch_b_stage`) como spine de prompt chaining A''; discriminação `subtype` × `stop_reason` (refusal-first); walking skeleton como técnica de validar *composição* de agentic loops antes de comportamento.
- D2 (Tool Design & MCP): §3 (Output) de cada subagente como I/O boundary canônico citado verbatim (anti-drift); dois eixos de governança de tool (built-ins via `tools` field vs server tools via `mcp_servers`) — ADR-0012; handshake estrutural vs jurisdicional (resource `policy://schema-version`).
- D4 (Structured Output): grafo de modelos Pydantic restritos por vocabulário; ACs das specs como contratos executáveis (contract-first); ressalva do wrapper `{"output":{...}}` em schema complexo.
- D5 (Context Management & Reliability): projeção de erro em envelope externo (`CoordinatorError`) vs token de payload; padrão de honestidade de reliability (não afirmar enforcement que a arquitetura não entrega — o defer do G6); provenance verbatim; âncora de contexto = artefato single-source, não transcrição de deliberação.

**Decisões (ratificadas)**
- #1 `ReporterPermissionDenied` **estrito** — qualquer `permission_denials` truthy → halt (integridade do run > salvar Report, sob lockdown). Convergidos 4 loci: coordinator §3.5 código + §5 prosa + reporter §6.4 tabela + §6.5 ordering.
- #2 G6 **deferido** — `verify_passthrough=None` no Matcher no MVP (matcher §3.5/AC-M8: ordem não é garantia estrutural; verificação coordinator-side é follow-up). Classifier 1:1 posicional **fica** no MVP (assimetria legítima 1:1 vs 1:N).
- #3 `error_max_budget_usd` **já canônico** (detector/triager §6.3 → `SubagentUnresponsive`); não é fork. O `match` arm do driver estava correto; a "decisão aberta" da proposta era premissa falsa (auto-contradição com o próprio código).
- #4 `CoordinatorError` **mínimo + provisional** — `cause`/`coverage_gap`/`stage`; `partial_scratchpad_path` e audit rico deferidos a Milestone D (acoplam ao contrato da GitHub Action + retenção do scratchpad §8). `coverage_gap` do `DetectorScanFailed` = "cobertura zero, scan não rodou" (não "parcial").
- G9 logging — **stderr** estruturado (trace); **stdout reservado** ao payload do Report (modo `-p` CI); scratchpad como replay; campos alinhados a `CoordinatorError`.
- M19/M20 **Beat 3 verified** — leitura verbatim confirmou aplicação em arch (§3 l.66/l.82, §5.5 l.197/l.201, §5.7) + reporter §2.2. Three-beats reconciliado (header "AGUARDA REVISÃO" era stale).
- DD-M22 companion **aplicado** — rótulo "framework-aware" anotado em arch §5.5 + canonical §3.2/§1/§6.3: handshake estrutural fica server-side; jurisdicional defere (dono futuro = código do coordinator, não Matcher). "Anotar o defer, não negar o contrato."

**Aprendizados**
- Reframe: o skeleton v3 estava **mais materializado** que a tabela de pendências sugeria (Reporter §3.5, §6 enforcement, `tools` field já feitos) — o flesh real eram 6 gaps concentrados, não reescrita.
- Cross-doc review profundo pega o que o raso não pega: o 2º review do Code derrubou minha recomendação de G6 ("agrupamento contíguo") lendo matcher §3.5/AC-M8 — o 1º review tinha ratificado meu erro. Leitura verbatim > inferência, sempre.
- Taxonomia de exceção tem **dois eixos** que não se misturam: base `SubagentToolError` cobre só tool-errors (`DetectorScanFailed` + futuras do Matcher; ADR-0013 a criar); SDK-class (`Refused`/`Validation`/`Unresponsive`/`Execution`) + `SubagentContractViolation` são eixo distinto, fora dessa base.
- Decomposição de implementação: unidades irredutíveis (grafo de tipos, composição/integração, caminhos de erro) fazem-se **integradas**; só comportamento per-stage decompõe limpo. O default linear de agentes otimiza progresso local sobre coesão global — daí o churn.

**Artefatos**
- `coordinator.md` flesh: 18 edits (driver §3.0bis, `CoordinatorResult` §3.6, predicado estrito §3.5, +3 exceções §5, config single-source, logging, etc.) — branch `docs/coordinator-flesh-mc-a`, **aguarda commit**. Companions: detector.md (`run_outcome="error"` → `CoordinatorError`, grep zero), reporter.md (truthiness §6.4/§6.5).
- Companion bucket: branch `docs/companion-edits-m22-beat3` (coordinator §10 Beat 3, arch §5.5, canonical §3.2/§1/§6.3) — **aguarda commit**.
- Docs de trabalho (não-repo): proposta integrada do flesh, doc de edits, doc de edits do companion.

**Próximo passo**
- T11+ em **sessão própria de planejamento de implementação** — explorar métodos e eixos de fatiamento, **chegar a decidir lá** (não decidido aqui). Ver session-handoff para o briefing de entrada (decisões herdadas, 2 bifurcações abertas, estado empírico do SDK, ambiente).

---

## Nota de processo (Code, MC-C Phase 2a) — 2026-05-31 — red-first auditável só no grão do commit

> Anotada pela sessão Code da Phase 2a (não é o entry da sessão MC-C #51, que é
> curado pelo Chat). Lição de PROCESSO, não débito de produto.

- red-first só é auditável se observável no **grão do commit**. O commit
  `082ec82` (Phase 2a) contém âncoras E impl juntos; o "RED" existe só nas
  docstrings dos testes, não no histórico git — a vermelhidão é reconstruível
  mas não auditável commit-a-commit.
- Daqui pra frente (Fases 2b/3): âncoras red entram em commit **SEPARADO** do
  impl que as fecha — ex. `test: anchors RED` seguido de `feat: impl → GREEN`.
- Considerar formalizar como regra em `CLAUDE.md` ou `.claude/rules/`.
- Não reescrever `082ec82`: o tree já é hermeticamente verde e correto;
  reescrever história por uma propriedade que o conteúdo já garante não compensa.

  ## #51 — MC-C Phase 2b (MCP middle) — 2026-06-01

**Escopo:** Detector → Classifier → Matcher flesh + a saga de debugging do G2b 
agent-loop. PR #92 (partially-gated). ADR-0014 (draft, Fase 3).

### Conceitos da prova exercitados
- **D1 — query() one-shot vs ClaudeSDKClient streaming.** query() é fire-and-stream, 
  sem controle de sessão; readiness/reconnect de MCP (get_mcp_status, 
  reconnect_mcp_server) só existem no ClaudeSDKClient (control requests gate em 
  streaming mode, query.py:510-511). Descoberto ao diagnosticar o race — o driver 
  usa query() per-stage, que não espera readiness.
- **D2 — tool_use_result é canal COMPARTILHADO.** Carrega tanto o ack de structured 
  output do SDK ('Structured output provided successfully', uma str) quanto envelopes 
  de tool MCP (dict). isinstance(dict) é o discriminador correto. Assumir canal 
  dedicado = o crash do Bug-2.
- **D2 — MCP server lifecycle per-stage vs per-session.** 5 query() independentes, 
  cada um spawna só seus mcp_servers. Isolamento per-stage (menor-privilégio de tools, 
  ADR-0012) colide com readiness quando o server tem cold-start lento.
- **D2 — stdio transport: stdout é sagrado (só JSON-RPC).** Banner do FastMCP vai pro 
  stderr corretamente; foi descartado como causa por observação, mas a regra ficou: 
  qualquer ruído no stdout corromperia o handshake.
- **D5 — reliability: readiness + recovery são um aparato só.** Esperar 'connected' 
  (readiness) e re-tentar transient (recovery) ambos precisam de controle de sessão. 
  Unificados sob um ADR, não dois follow-ups soltos.
- **D1/D5 — reconnect ≠ re-spawn.** Reconectar server numa sessão viva (barato) vs 
  fechar+reabrir o cliente (cold-start completo). Confundir os dois no retry-loop 
  multiplica o custo — pego no review do ADR-0014.

### Decisões
- DD-a/b/c resolvidas por leitura de spec autoritativa (não decreto): hook em 
  detector/hooks.py; passthrough 5-campos incl. surrounding_context (coordinator §3.3 
  l.205, não o §4.3 stale); tools equality order-sensitive.
- DD-d = escalate-all, ratificada — MAS re-rotulada de "resolved" para divergência 
  deliberada de invariante de spec (detector §6.2 + coordinator §5 l.428 mandam 
  retry-antes-do-raise; impl atrasa a spec, spec não está over-specified). Retry-loop 
  deferido pra Fase 3.
- G2b = PARTIALLY-GATED (categoria nova): determinísticos PASS, agent-loop bloqueado 
  por gap de readiness da camada driver. Race real em produção, não artefato de teste 
  (Triager declara mcp_servers={}, semgrep-runner sempre frio no Detector).
- {"output"} wrapper: NÃO observado no DetectorOutput de lista (scan nunca rodou); NÃO 
  fechado por G0 (G0 só cobriu o enum-tag do Matcher). Gated junto com o race.

### Lições de processo (transversais — as que mais importam)
- **Observar antes de AGIR, e antes de DECIDIR.** A saga teve 4 diagnósticos, cada um 
  revisado pela observação seguinte: cwd era red herring; o crash era o ack-string; 
  "server não registrou" era cold-start (não os 3 suspeitos óbvios); o race é real 
  (não artefato). Segurei o conserto em todas as 4 bifurcações. Aplicado 
  PREVENTIVAMENTE ao ADR-0014: a suposição causal "readiness-wait resolve o race" é 
  inferência não-observada → virou D1 verification gate antes de comprometer o design.
- **A verdade da integração vive no ponto de consumo, sob o transporte real.** 
  Hermético prova a lógica; Inspector-CLI prova o contrato do server; só o agent-loop 
  prova o relay SDK→CLI→stdio. Os 3 bugs (ack-string, lifecycle, race) só apareceram 
  no agent-loop. "Gated" só é honesto quando a camada que o gate interroga rodou — o 
  "implemented and gated" inicial foi prematuro por confundir Inspector-CLI com loop.
- **"Verificado" precisa nomear QUAL ponta.** A OPEN ASSUMPTION do nested-shape foi 
  marcada RESOLVED com evidência do lado do servidor (Inspector-CLI), mas o shape que 
  importa é o que chega ao consumidor (hook via relay). Servidor-emite ≠ 
  consumidor-recebe quando há relay no meio.
- **Red-first auditável só no grão do commit** (herdado do #50/2a, aplicado: 2b separou 
  test:RED → feat:impl em commits distintos, ao contrário do 082ec82 monolítico).
- **Co-Authored-By drift:** Code adicionou o trailer contra git-conventions nos 2 
  primeiros commits da 2b; corrigido prospectivamente (memória no-coauthor-trailer), 
  não reescrevi história.
- **shell/PS (fora do escopo da prova):** inline-Python pesado em PS 5.1 → arquivo .py 
  temporário, não python -c com aspas aninhadas (o {p['baseRefName']} vazado). PR body 
  via arquivo UTF-8, não HEREDOC.

### Artefatos
- PR #92 (feat/mc-c-phase2b-mcp-middle, partially-gated). Commits ac19182 (RED) → 
  c3943f0 (impl) → 4e391ba (G2b evidence) → a3da204 (Bug-2 fix) → 56bf2dc (G2b 
  partially-gated).
- ADR-0014 (draft, Fase 3): MCP connection lifecycle & resilience. Readiness + recovery 
  unificados; D1 verification gate pendente.
- Memórias: mc-c-phase2b-deferred-debts (race+retry sob 1 ADR + §4.3 doc-lag), 
  no-coauthor-trailer.
- RESULTS.md "GATE G2b" (determinísticos PASS + race documentado).

### Próximo passo
- Merge #92 (considerar review de contexto fresco antes — saga longa, autor saturado).
- Sequenciamento: levar o plano completo das 5 fases pro Chat — o que resta de MC-C 
  antes da Fase 3, e se reliability vem antes ou depois. Inclinação: Fase 3 (D1 
  verification gate primeiro) antes, porque sem ela nada roda end-to-end e a 
  verificação pode redirecionar o ADR.
- Housekeeping PR (doc-lag §4.5/§6.1/§6.2/coordinator §3.1 + §4.3) — trivial, a 
  qualquer momento.

  # Learning log — entrada de 2026-06-02

> Formato tópicos, append-only. Esta é a entrada da sessão exploratória de
> avaliação (test-cases + harness + achados de pipeline). Acrescentar ao
> `docs/learning-log.md` existente; não sobrescrever entradas anteriores.

## 2026-06-02 — Exploratório de avaliação (PR #99) + planejamento da frente ADR

### Conceitos da prova exercitados

- **D1 — Agentic Architecture**: teste de *composição* vs *teste de unidade de
  estágio* (`test_g3_live_e2e` verifica que a cadeia compõe e invariantes valem,
  não valores exatos; valores ficam no gate determinístico). Enforcement
  programático vs compliance probabilística — `run_outcome`/`counts` derivados em
  Python pelo coordinator, não pelo Reporter-LLM (lógica crítica sai do prompt e
  vira código).
- **D2 — Tool Design & MCP**: resource derivado (computado, ex. `policy://catalog`)
  vs resource servido de arquivo curado (ex. `policy://examples`, Camada 1). Resource
  ausente quebrando agente downstream (Classifier sem `data_categories` exposto).
  Raiz de Política como unidade de configuração mutuamente exclusiva selecionada por
  `POLICY_READER_ROOT` (motivo de `policy/` não conter `policies/`).
- **D4 — Prompt Engineering / Structured Output**: distinção *constraint* (vocab/enum:
  saída válida) vs *demonstration* (few-shot: saída correta) — um não substitui o
  outro. Null-on-miss correto (Classifier devolve `[]` em vez de inventar token).
  Few-shot herda regra de camada: disciplina agnóstica no prompt (Camada 2), exemplos
  jurisdição-bound em resource (Camada 1). Retry inútil quando a informação não está
  na fonte (vs erro de formato).
- **D5 — Context Management & Reliability**: provenance mal-rastreada (assumir dois
  artefatos idênticos quando divergiram — vocab seed vs vocab enriquecido). Error
  propagation honesta (incerteza do Classifier propaga como `requires_human_review`,
  não vira veredito falso). Priorização sob orçamento fixo (escalation/cutoff: o que
  destrava + o que o artefato final precisa; resto vira trabalho futuro documentado).
  Surface-the-gap: documentar limite > corrigir mal sob prazo.

### Decisões

- Topologia B mergeada (PR #99), mas **será substituída** por `policy/` única
  (`_seed` + instâncias irmãs) na frente ADR. Motivo: instâncias e seed como irmãs
  sob um diretório-mãe; default por config do loader, não por natureza.
- ADR-0015 será implementado (inclui GDPR / `legal_framework`).
- Inversão POL-007 fica **documentada** (achado + causa + correção projetada), não
  corrigida — risco zero de prazo, seção forte de avaliação.
- CI mínima (pipeline num PR posta Report), não robusta.
- `policy://examples` (item 7) **condicional** ao discriminante do passo 1
  (measure-before-tune): só entra se a lista de tokens não bastar.
- Caminho crítico das 2 semanas: 1 (expor `data_categories` + medir) → 2 (reestrutura
  `policy/`) → harness live eval-lgpd → 6 (`rule_id` limpo) → CI mínima.

### Artefatos

- PR #99 (`eval/test-cases-exploratory` → main): instâncias eval-lgpd/eval-gdpr,
  harness 2 camadas (gate 13/13 + 10/10 Reports válidos), `cases.yaml`, PRs
  sintéticos, ADR-0015 Proposed, `test-cases-proposal.md`.
- `docs/eval/pol-007-inversao-sensibilidade.md` — achado documentado.
- 10 Reports determinísticos baseline (`eval/harness/reports/`), incl. B-SENS-OK/INV
  (o antes da correção POL-007).
- 1 Report de pipeline live (G3): confirma ambiente pronto, expõe `data_categories: []`
  do Classifier e `rule_id` poluído com path absoluto.
- `session-handoff-adr.md` — estado para retomar.

### Achados de pipeline (só visíveis com LLM rodando, não no harness determinístico)

- Classifier devolve `data_categories: []` — causa **estrutural**: `get_vocabularies`
  omite categorias + `policy://examples` não existe. Não é bug do modelo.
- `rule_id` poluído com caminho absoluto da máquina (Semgrep deriva do path; regras
  `br_*.yaml` sem `id:` explícito) — propaga até o Report final.
- Report consolidado é LGPD-locked (`Finding`/`ReportPayload` fixam
  `legal_framework: Literal["LGPD"]`): swap GDPR demonstrável só no veredito, não no
  Report.

### Erro de método registrado

- Afirmei na §6(b) do doc POL-007 que faltava o token `explicit_consent`; o Code leu
  `lawful_basis.yaml` e o token **já existia**. Violação de "verificação antes de
  inferência" — inferi estrutura sem ler o arquivo. Correção pendente no doc.

### Próximo passo

Abrir sessão ADR pelo **Passo 1**: expor `data_categories` no `get_vocabularies` +
experimento discriminante (cpf nu vs cpf rico). Resultado decide se item 7 entra nas
2 semanas. Antes: corrigir §6(b) do doc POL-007 e limpar corpo do PR #99, depois
mergear.