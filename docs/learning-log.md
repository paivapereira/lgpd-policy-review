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
- docs/learning-log.md (este arquivo)
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
  `docs/session-handoff.md` e `docs/learning-log.md` vão direto em
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

- **`docs/proposta-tcc2.md` redigido e mergeado** (PR via fluxo
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
- `docs/proposta-tcc2.md` (PR mergeado)
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

**Próximo passo.** Ver `docs/session-handoff.md`.

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

**Foco.** Fechamento da arquitetura multi-cliente declarada em `docs/proposta-tcc2.md` §6 via reescrita documental coordenada em 7 commits sequenciais na branch `arch/multi-client-policy-rewrite`. Sem código de implementação — toda a sessão viveu na camada de docs (`architecture-overview.md`, ADR-0005, `SCHEMA.md`, specs canonical+compact dos dois servers, `DESIGN.md` novo, learning-log, session-handoff). Materializa a separação estrutural/jurisdicional já implícita na proposta e cristaliza-a antes do início da Fase 2.

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
- Atualização de `docs/proposta-tcc2.md` §7 com calibração SDD e §11 com duas novas referências.
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

**Companion edits aplicadas na mesma transação:** `CLAUDE.md` §"Working methodology" reescrito; `docs/session-handoff.md` (pendência #18 e prompt de abertura) atualizados; este registro.

**ADR-0004 também aterrissou na mesma extensão da sessão.** uv + FastMCP 3.x — número reservado desde #14, decisão substantiva agora registrada. Ratifica de-facto state operado desde #14 (pyproject.toml com uv_build, .python-version pinning 3.12.7, uv.lock versionado, FastMCP 3.x na skeleton). Rationale: lockfile reprodutibilidade (primário, gatilho "vai ser usado por outras pessoas na empresa"), Python version isolation (secundário que virou primário após falha empírica de pyenv-win com 3.14 paralelo), performance/no-admin/CLI familiarity (terciários). Supersede parcial de ADR-0001 §2. Companion edits: CLAUDE.md §"Stack (canonical)" ganhou bullet de dependency manager e versão de FastMCP; três entradas em session-handoff atualizadas (pendência ADR-0004 removida, drift de ADR-0001 reframed como editorial não-bloqueante).

**Justificativa de emenda in-place vs novo ADR-0009.** ADR-0008 fresco (24h); #18 (primeiro consumidor) ainda não rodou; greenfield sem deployment ou tasks.md autorada. ADR-0005 precedente usou refinement-via-novo-ADR mas operava sobre consumidor herdado (código semente da #14 + specs mergeadas). Aqui in-place preserva single-source-of-truth para Claude (consumidor primário de ADRs neste projeto) sem custo de migração; expectativa de imutabilidade não acionada porque nenhum artefato downstream foi autorado sob a versão original.

**Conceito de prova exercitado lateralmente.** Conflação capability×function no scope errado é forma específica de **abstraction leak no boundary**: §2 do original misturava dois eixos de design (decomposition strategy + acceptance criteria scope) que deveriam ter ficado ortogonais. Decoupling reverte a leak. Padrão destilável: quando uma decisão arquitetural produz fricção sistemática em aplicação (per-task RF binding produziu friction em 3+ pontos da primeira proposta de tasks), a hipótese default é conflação no nível da decisão, não no nível das tasks.

## 2026-05-16 — sessão #18 — ADR-0007 redigido, PR de access layer em ADRs, validação operacional do D4.6

### Conceitos da prova exercitados

**Domínio 1 — Agentic Architecture & Orchestration (27%)**

- **D1.6 Task decomposition — scope discipline via flag-and-continue.** Code descobriu durante Task 5 do PR-30 que ADR-0001 carrega `## Pendências decorrentes` (linha 271, 4 bullets) estruturalmente paralela à `Follow-up patches` removida do ADR-0002 no mesmo PR. Padrão aplicado: surfaced o achado, não agiu, deixou decisão para o autor. Conscientemente classificada como out-of-scope do PR editorial; migrada para `session-handoff.md` como pendência operacional para sessão futura. Contraste explícito com session #17 (Code expandiu escopo silenciosamente gerando ADR-0006/0007 não solicitados). ADR-0008 amended formaliza isso como pattern de pause-and-ask.

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- **D3 `.claude/rules/` vs `.claude/skills/` vs `.claude/commands/`.** Discussão extensa sobre o primitivo correto para automação de geração de ADR/handoff/learning-log. Conclusão: rules path-scoped para convenções aplicáveis automaticamente quando Code toca o path (`docs/adr/**`, `docs/learning-log.md`); skills para procedimentos pesados com `context: fork`; commands para invocação explícita. Decisão deliberada: camada mecânica vai para rules; camada deliberativa permanece em Chat. Anti-padrão identificado: skill que "gera ADR completo" reintroduziria o problema de ADR-0007 (Code racionalizando rationale).
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
- **Processo de cristalização da sessão #18:** `docs/learning-log.md` (entry 2026-05-16).

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
`docs/session-handoff.md` para pre-flight pins detalhados.

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

**Para aplicar:** apendar este conteúdo ao final de `docs/learning-log.md`, abaixo
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
  1. Sync `docs/session-handoff.md` ↔ split Milestone A/B (legado pré-T04).
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