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