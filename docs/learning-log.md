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
- ADR-0007 (MVP collection-only scope) — redação em sessão Chat dedicada com rationale do mapa de tagueamento como motivação primária.
- `docs/tasks.md` (Commit 1.5.2 original do plano da Fase 1.5) — agora calibrada por ADR-0008 para 8-12 tasks médias com gate tripartite.

### Próximo passo

Sessão #18 abre com agenda dupla: (a) discussão sobre Matcher como evaluator iterativo (decisão arquitetural significativa de Fase 2); (b) preparação para sessão dedicada de ADR-0007. tasks.md fica para sessão #19 ou intercalado conforme disponibilidade.
