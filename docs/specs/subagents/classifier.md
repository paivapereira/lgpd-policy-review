# classifier

**spec_version**: 0.1.0

> Spec leve do subagent Classifier. Segue a estrutura de `reporter.md` v0.4.0 e `triager.md` v0.1.0 como template hipótese (a destilação formal de `_template-subagent.md` permanece Fase 2, não materializada). Decisões de design ancoradas em `docs/architecture-overview.md` §5.4, `coordinator.md` §3.3, `docs/specs/policy-reader/canonical.md` §3.3, `docs/REQUIREMENTS.md` RF-003 e ADR-0005 Decision 4. Autorada na work-session #45 (inversão deliberada da ordem #37: Classifier antes de Detector — registrada no session-handoff pós-MC-F). Revisada por Code (review cross-doc); fixes de severidade Alto/Médio/Baixo folded em 0.1.0 pré-merge (bump rules aplicam ao estado mergeado, não em-revisão — per Reporter spec defense candidate #4 / `triager.md` precedent). Segunda rodada de design folded em 0.1.0: few-shot positivo migrado para resource de camada 1 `policy://examples` (DD-C10, decisão de pureza de camada — examples são vocab-token-bound, seguem o vocabulário; **por analogia** ao princípio de camada de ADR-0005 D8, que decide *regras de detecção*, não examples — a decisão formal para examples é a **Decisão 9** a ser criada no amendment de ADR-0005 que acompanha o PR autônomo de `policy://examples`). Esta spec **não decide DD-T05** (`changed_paths`): `changed_paths` não pertence ao contrato do Classifier (ver §2.1, §8.1, §10.5); DD-T05 é decisão coordinator/Triager catalogada separadamente.

## 1. Identidade e propósito

### 1.1 Nome canônico

`classifier`. Subagent. Não é MCP server, não expõe resources, não expõe tools customizadas. **Consome** os resources `policy://vocabularies` (tokens válidos) e `policy://examples` (exemplos de mapeamento per-jurisdição; DD-C10) do server `policy-reader` (read-only, sem acesso às tools do componente) — distinção load-bearing detalhada em §1.4 e §3.3.

### 1.2 Função

Para cada candidato de tratamento detectado pelo Detector, extrai **contexto estruturado** descritivo: o que o código faz com o dado (`operation_type`), que categorias de dado pessoal toca (`data_categories`), que base legal o código declara, se declara (`declared_legal_basis`), e que transformações declara aplicar (`declared_transformations`). Output: a mesma lista de candidatos, enriquecida com um campo `structured_context` por candidato (shape concreto em §3).

Materializa **RF-003** (`docs/REQUIREMENTS.md:41`): *"Para cada candidato detectado, o sistema extrai contexto estruturado com quatro campos... Valores em campos governados por vocabulário jurisdicional são restringidos aos vocabulários publicados pela Política via `policy://vocabularies` — extração que falha em mapear para o vocabulário do framework declarado resulta em campo nulo, não em invenção."*

A capacidade externa observável de RF-003 é a presença dos quatro campos de `structured_context` em cada candidato enriquecido, com os campos de vocabulário pertencendo ao conjunto publicado ou sendo nulos. O Classifier é o subagente que produz essa capacidade; o output não é externamente observável por si — é consumido pelo Matcher (etapa 4) e, via Matcher → Reporter, contribui para os campos `operation_type` e `data_categories` de cada finding do Report (RF-006).

### 1.3 Posição na arquitetura

Etapa 3 do fluxo descrito em `docs/architecture-overview.md` §3 e §5.4. Invocado pelo coordinator após o Detector (etapa 2) e antes do Matcher (etapa 4). Recebe a lista de candidatos do Detector; emite a lista enriquecida consumida pelo Matcher.

Tools permitidas: `Read` (sobre arquivos do projeto, para inspecionar imports, definições de função, contexto além das linhas do snippet), `Grep` (para buscar declarações de base legal, transformações ou anonimização em comentários e docstrings próximas), e as duas built-in genéricas de acesso a resource MCP — `ListMcpResourcesTool` e `ReadMcpResourceTool` — para ler `policy://vocabularies` **e `policy://examples`** do `policy-reader`. Sem `semgrep-runner`, sem `Glob`, sem `Write`/`Edit`/`Bash`. Matriz canônica em `docs/architecture-overview.md` §5.4 e tool-set verbatim em `coordinator.md` §3.3.

> 💡 **Conceito Claude relevante (Domínio 2 — Tool Design & MCP Integration, Task Statement 2.2).** A inclusão de `policy://vocabularies` **sem** acesso às tools do `policy-reader` (`get_clause`, `find_clauses_by_law_article`, `check_applicability`) materializa o princípio **Resource vs Tool** (ADR-0005 Decision 4, textbook case): vocabulários jurisdicionais são catálogo idempotente compartilhável por múltiplos consumidores; cláusulas são consultas direcionadas com semântica de ação, exclusivas do Matcher. O Classifier ganha **visibilidade** ao vocabulário sem ganhar **capacidade de inferir veredito**. A fronteira "Classifier descreve, Matcher julga" é preservada em nível de capability — ver nota de granularidade per-server em §3.3.

A omissão deliberada de `Glob` (presente no Triager, ausente aqui) é decisão de single-responsibility: o Classifier não descobre paths nem enumera o diff — opera sobre a lista de candidatos pré-localizados pelo Detector, lendo arquivos específicos via `Read` por `file` de cada candidato. `Grep` é a ferramenta de inspeção fina reservada a este subagent (busca de base legal em comentários/docstrings); `Glob` (enumeração de paths) não tem função no contrato do Classifier. `changed_paths` não é insumo do Classifier (ver §2.1 + §8.1).

Routing downstream — `classifier_output` invoca o Matcher (etapa 4) — é responsabilidade exclusiva do coordinator e não é re-decidido nesta spec.

### 1.4 Invocador e modo de invocação

Único invocador autorizado: **coordinator**, via `claude_agent_sdk.query()` em pattern A'' (system prompt direto em `ClaudeAgentOptions`, sem `AgentDefinition`). Pattern justificado em `coordinator.md` §1.4 (decisão template-wide do sistema multi-agente).

Lockdown agent CI/CD-headless materializado pela **quíntupla canônica de denial-on-miss** (locus canônico de enumeração: `coordinator.md` §2; também em `reporter.md` §1.4 e `triager.md` §1.4):

1. `permission_mode="dontAsk"` — denial determinístico de tools fora do allowlist.
2. `setting_sources=[]` — isolamento de `CLAUDE.md`, output styles e demais settings de filesystem.
3. `strict_mcp_config=True` — confinamento ao `mcp_servers` declarado.
4. `allowed_tools=["Read", "Grep", "ListMcpResourcesTool", "ReadMcpResourceTool"]` — whitelist explícita. **Diferença vs Triager** (`["Read", "Glob"]`): troca `Glob` por `Grep` (inspeção fina vs enumeração de paths) e **adiciona** as duas built-in de resource MCP.
5. `mcp_servers={"policy-reader": POLICY_READER_CONFIG}` — **dict não-vazio** (contraste com Triager `{}`): o Classifier precisa do `policy-reader` registrado para que `ReadMcpResourceTool` consiga resolver `policy://vocabularies` e `policy://examples`. Registrar o server **não** concede as tools de ação — essas ficam fora do `allowed_tools` (item 4), barradas pela whitelist sob `dontAsk`. `POLICY_READER_CONFIG` é **constante single-source** (G1): referenciada (não redefinida) pelo Classifier e pelo Matcher — ambos consomem o mesmo server. Locus exato a estabelecer/confirmar antes da Fase 3 (provável `coordinator/config.py`, onde o skeleton §3.3 já a referencia pelo nome); shape (`McpStdioServerConfig`: `command`/`args`/`cwd`, PATH vs path absoluto) é decisão de infra compartilhada, não do Classifier. Carimbado como obrigação de referência em §10.5(1).

**Eixo `tools` — availability, ortogonal à quíntupla.** A query do Classifier declara `tools=["Read", "Grep", "ReadMcpResourceTool", "ListMcpResourcesTool"]` no skeleton de `coordinator.md` §3.3. `tools` é eixo **ortogonal** à quíntupla (per `coordinator.md` §2, ratificado em Reporter §1.4 + §1.5): a quíntupla governa *denial-on-miss* (whitelist `allowed_tools` sob `dontAsk`); `tools` governa *availability* — quais built-ins entram no contexto do modelo. O Issue #361 permanece verdadeiro — `allowed_tools` "does not remove tools from Claude's toolset" e *não* controla availability — **mas isso vale para `allowed_tools`, não dispensa o campo `tools`**: `ReadMcpResourceTool`/`ListMcpResourcesTool` são built-ins cuja *availability* é governada pelo `tools` field. O server registrado em `mcp_servers` concede o **alcance** ao resource (capability), mas o built-in só entra no contexto do modelo se também estiver em `tools`. Sob `tools` não-vazio sem ele, o modelo verbaliza "ReadMcpResourceTool is not available" e o read de vocabulário falha (#48-b; `coordinator.md` §10 DD-9.1) — emitindo tokens não-canônicos que quebram a comparação de `consent` no Matcher. **Correção (review #48-b):** a afirmação anterior de que o Matcher invocaria `ReadMcpResourceTool` sob `tools=[]` "sem conflito — precedente consistente" era **defeito empírico**; `tools=[]` esconde o built-in, e tanto o Matcher quanto este Classifier listam os dois built-ins no `tools` field (coordinator §3.3/§3.4). Confirmação empírica do acoplamento veio do #48-b (shape `tools=[]` do Matcher); o Gate resource access de §10.3 ainda deve **persistir** o caso do shape específico do Classifier.

**Eixo ortogonal à quíntupla — structured contract via `output_format`** (Branch B, compartilhado com o Triager, não com o Reporter):

```python
output_format = {
    "type": "json_schema",
    "schema": ClassifierOutput.model_json_schema(),
}
```

Forma **envelopada** verbatim — `{"type": "json_schema", "schema": ...}`, não a forma nua (que é shorthand). Confirmada corrente contra a doc oficial (`agent-sdk/structured-outputs`, `build-with-claude/structured-outputs`, abril/2026) e empiricamente contra `scripts/smoke_tests/sdk_output_format_lockdown/` (SDK 0.2.87); anotação de proveniência em `reporter.md` §10.6. A quíntupla governa **denial-on-miss**; `output_format` governa o **shape do output** (validation-retry loop delegado ao runtime do SDK). Categorias semânticas distintas. **Nota de drift — ✅ aplicado (C3):** o skeleton de `coordinator.md` §3.3 agora declara `output_format={"type": "json_schema", "schema": ClassifierOutput.model_json_schema()}` (paridade com §3.1 Triager e §3.2 Detector). Débito fechado quanto ao `output_format`; ver §10.5(1).

**Branch A vs Branch B.** O Classifier opera em **Branch B** (`output_format=json_schema`), como o Triager. Devolve dado estruturado validado (lista enriquecida) consumido pelo coordinator, sem dual sink, sem closure capture, sem side effect além da emissão. Branch A (custom tool via `@tool` + `create_sdk_mcp_server`, pattern do Reporter `emit_report`) é apropriado quando há dual sink ou side effect auditável intra-handler — não é o caso aqui. Heterogeneidade per concern, não inconsistência (ver DD-C3).

> 💡 **Conceito Claude relevante (Domínio 4 — Prompt Engineering & Structured Output, Task Statements 4.2 + 4.3).** O `output_format=json_schema` encapsula o validation-retry loop no runtime do SDK em vez de implementá-lo no agente. O SDK valida `ResultMessage.structured_output` contra o schema e dispara retry automático em mismatch; em estouro de retries, emite `ResultMessage` com `subtype="error_max_structured_output_retries"` (tabela canônica em §6.3). Match mechanism to concern: o Classifier não tem dual sink que justifique Branch A.

### 1.5 Stack e governança

Stack: Python 3.12.7, `claude-agent-sdk` ≥ 0.2.87 (baseline empírico; piso definitivo em `pyproject.toml` na Provisão MC-E), `pydantic` 2.13.4.

**Modelo de inferência.** Claude Opus 4.7 com adaptive thinking, herdado do default do coordinator. Otimização de modelo (cost/latency) deferida para pós-validação funcional, seguindo o princípio de não introduzir variável adicional enquanto o sistema não estiver 100% funcional (paralelo a `triager.md` §1.5 + DD-T11).

**Locus físico (implementação).** Classifier mora em `src/subagents/classifier/` (convenção `src/subagents/<name>/` per DD-T15).

**Locus de runtime.** O Classifier **não** mantém estado próprio; cada invocação é uma `query()` independente, configurada em runtime pelo coordinator com a lista de candidatos do Detector como prompt input. Sem factory pattern, sem closure capture, sem MCP server in-process, sem arquivo persistente próprio. O `policy-reader` é server **out-of-process** registrado em `mcp_servers`, consumido via `ReadMcpResourceTool` — não instanciado pelo Classifier.

**Aritmética de turns.** O Classifier executa, por candidato: leitura do vocabulário (`ReadMcpResourceTool` no startup, uma vez por query), `Read`/`Grep` para inspecionar o contexto do candidato, e a produção final estruturada (lista inteira), mais retries implícitos do SDK em mismatch contra schema. Para N candidatos a inspeção escala com N — orçamento de turns substantivamente maior que o do Triager (que faz uma decisão PR-level). Inclinação inicial: `max_turns=20` provisional, cap generoso deliberado para calibragem em T11+ (catálogo de PRs sintéticos, Provisão MC-D), seguindo measure-before-tune. Ratchet possível ao fim de T11+ se a distribuição empírica revelar piso seguro (ver DD-C6). `max_budget_usd` disponível como cap complementar, não exercitado no MVP. **Salto não-escalável admitido (G5):** o valor é uma **constante**, mas o trabalho escala com N (inspeção `Read`/`Grep` por candidato + emissão final). Para N grande (ex.: 30 candidatos), uma constante de 20 estoura. Decisão consciente para o MVP — *não* introduzir uma fórmula `base + k*N` agora, porque `k` (turns por candidato) é desconhecido pré-T11 e chutar a fórmula viola measure-before-tune. Backstop determinístico no lugar: PR patológico em N atinge `error_max_turns` → `SubagentUnresponsive` (§6.3) → escalação pelo coordinator, **não** falha silenciosa nem output parcial. A fórmula de escala (constante vs `base+k*N` vs cap-com-truncação de N) é decidida em T11+ sobre dados reais (DD-C6). **Nota de drift — ✅ aplicado (C3):** como o `output_format` (§1.4), o `max_turns=20` está agora declarado no skeleton de `coordinator.md` §3.3 (provisional, não escala com N — backstop `error_max_turns`). Débito fechado; ver §10.5(1).

**Grammar compilation latency** (first-hit per schema). Doc oficial (`build-with-claude/structured-outputs`): compiled grammars são cacheados por 24h a partir do último uso. Implicação para CI workers efêmeros: primeiro PR após cold start paga a compilação. Não-bloqueante; possível warm-up futuro. Mesma consideração de `triager.md` §1.5.

Governança: governado por ADR-0001 (stack canônica) e ADR-0005 Decision 4 (resource access scoping — Classifier consome `policy://vocabularies`, sem tools do `policy-reader`); companion-spec'd por `coordinator.md` §3.3 (skeleton de invocação do Classifier) e por `docs/specs/policy-reader/canonical.md` §3.3 (Classifier listado como consumidor autorizado do resource).

## 2. Input contract

### 2.1 Shape do input

O Classifier recebe a lista de candidatos emitida pelo Detector (etapa 2). Shape de cada candidato, ancorado verbatim em `docs/architecture-overview.md` §5.3:

```python
class DetectorFinding(BaseModel):
    file: str               # path relativo ao repo
    line: int               # linha do ponto de tratamento candidato
    rule_id: str            # identificador da regra Semgrep que disparou
    snippet: str            # trecho do código/payload
    surrounding_context: str  # contexto além das linhas do snippet
```

> **Forward-reference declarada.** A spec do Detector (`docs/specs/subagents/detector.md`) ainda não foi autorada (ver inversão de ordem #37 no session-handoff). Este shape **não é inventado**: é o output declarado em `architecture-overview.md` §5.3 (`[{file, line, rule_id, snippet, surrounding_context}]`), aqui pinado como provisão que a Detector spec **ratifica** quando autorada. Se a Detector spec divergir deste shape, a divergência é débito a reconciliar contra esta âncora arch §5.3 — não contra uma invenção do Classifier. Provisão de proveniência preventiva, padrão MC-F aplicado antes do fato (ver DD-C7).

**Ausente do input — `changed_paths`.** O Classifier **não** recebe nem consome lista de paths alterados. Opera sobre os `file` individuais carregados em cada `DetectorFinding`. Consequência de contrato: DD-T05 (`changed_paths` no scope compartilhado) é **ortogonal ao Classifier** — sua resolução (coordinator pré-computa vs Triager descobre via `Glob`) não toca esta spec. Catalogado em §10.5; status em §10.4 (DD-C1).

### 2.2 Construção do prompt pelo coordinator

O coordinator constrói o prompt da `query()` chamando `build_classifier_prompt(detector_output)` definido em `coordinator.md` §3.3 (locus canônico autoritativo). A função recebe a lista de `DetectorFinding` e a expande no template de §5.1; os candidatos viram texto estruturado no prompt (cada um com `file`/`line`/`rule_id`/`snippet`/`surrounding_context`).

```python
# Pseudocódigo do coordinator (autoritativo: coordinator.md §3.3)
prompt = build_classifier_prompt(detector_output)  # detector_output: list[DetectorFinding]
async for msg in query(prompt=prompt, options=classifier_options):
    ...
```

### 2.3 Caminho upstream e lista vazia

Diferente do Triager (primeira etapa, sem upstream), o Classifier consome estado da etapa anterior. **Lista vazia é caso válido, não erro:** quando o Detector retorna `findings: []` (zero candidatos), o Classifier emite lista enriquecida vazia que propaga ao Matcher → Reporter (`coordinator.md` §3.2: *"zero candidatos é caso válido; `findings: []` propaga ao Classifier → Matcher → Reporter"*). Não há branching condicional no coordinator para esse caso — o pipeline prossegue.

### 2.4 Princípio: Classifier descreve, não julga

O Classifier opera sobre o **código local** e contra os **vocabulários jurisdicionais** publicados pela Política — não consulta cláusulas, não avalia aplicabilidade, não emite veredito. O `structured_context` é descrição factual do que o código faz e do que ele declara fazer, alinhada ao vocabulário do framework declarado, mas independente do que a Política exige cláusula a cláusula. Confundir extração com avaliação é o anti-padrão de classificador acoplado a regras — torna impossível trocar a Política sem reescrever o Classifier (RF-008). Esta fronteira é o invariante load-bearing protegido por toda a spec (ver §3.3, §8.3).

## 3. Output contract

### 3.1 Shape canônico

Output emitido em `ResultMessage.structured_output` após validação do SDK contra o schema declarado em `output_format`. O Classifier devolve a lista de candidatos do Detector, cada um **enriquecido** com `structured_context`:

```python
from typing import Optional
from pydantic import BaseModel, ConfigDict

class StructuredContext(BaseModel):
    model_config = ConfigDict(extra="forbid")  # G2: fail-loud; ver §3.1 nota de postura
    operation_type: Optional[str]          # token do vocabulário operation, ou null
    data_categories: list[str]             # tokens do vocabulário de categorias; [] se nenhuma
    declared_legal_basis: Optional[str]    # token do vocabulário de base legal, ou null
    declared_transformations: list[str]    # transformações declaradas (free-form); [] se nenhuma

class ClassifiedCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Campos verbatim do DetectorFinding (passthrough, preservados sem mutação):
    file: str
    line: int
    rule_id: str
    snippet: str
    surrounding_context: str
    # Enriquecimento do Classifier:
    structured_context: StructuredContext

class ClassifierOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    classified: list[ClassifiedCandidate]
```

**Por que objeto-wrapper (`ClassifierOutput.classified`) e não array no nível raiz.** O `output_format=json_schema` espera, por convenção do SDK e robustez de grammar, um schema de objeto no topo. Envolver a lista em um campo (`classified`) evita array-at-root. Decisão consciente que também **evita** o eixo aberto da DD-T16 do Triager (aceitação de `oneOf`/`discriminator` no nível raiz): o output do Classifier **não é discriminated union** — é lista homogênea de objetos — então o risco da DD-T16 não se aplica aqui (ver DD-C4).

**Optionality e null vs vazio (emenda dos escalares).** Os dois campos escalares são `Optional[str]` **sem default** → em Pydantic 2 isso os mantém em `required` *e* tipa como `string | null`, forçando o modelo a emitir a chave com valor-ou-`null` explícito. Escolha deliberada: a doc oficial recomenda tornar campos *optional* (omitíveis) quando a info pode faltar, mas omissão é ausência silenciosa; RF-003 exige `null` **explícito e auditável** ("null, não invenção"). `required + nullable` materializa isso; `optional + default` permitiria omissão silenciosa, mais fraco para audit. Os dois campos de lista são `list[str]` **defaultando** `[]` (nunca `null`): `[]` significa "examinei, nada mapeável/declarado"; não há `Optional[list]`, pois um terceiro estado ("não consegui determinar") em lista adicionaria ambiguidade sem ganho — e cada `Optional` adicionaria um nó `anyOf` ao orçamento de grammar (ver §3.2).

**Postura `extra="forbid"` do próprio Classifier (G2).** Os modelos do Classifier usam `extra="forbid"`. Distinção load-bearing vs a postura do *consumer* (Matcher) tratada em §7.1/DD-C9: aqui se trata da validação do **próprio output** pelo coordinator (`ClassifierOutput.model_validate(message.structured_output)`, §4.3). Como o output é **grammar-constrained** pelo `output_format`, o modelo não deveria emitir chave extra; se emitir, é sinal de anomalia/drift e deve **falhar alto** (`SubagentValidationFailed`), não ser silenciosamente descartado (`extra="ignore"` perderia o sinal). Sem fragilidade de retry-noise: o coordinator só valida o `structured_output` final pós-`subtype=success`; os retries do SDK são internos e não chegam ao `model_validate`.

**Duplicados e identidade posicional (G10 + G4).** Candidatos com `(file, line, rule_id)` idêntico são possíveis (dois recognizers Semgrep na mesma linha). O Classifier **preserva ambos verbatim** (passthrough), um `ClassifiedCandidate` por `DetectorFinding` de entrada — não reconcilia, não deduplica. Consequência: `(file, line, rule_id)` **não é chave única**; a identidade para verificação de contrato é **posicional** (índice na lista), não por chave. Isto amarra a verificação de ordem do §4.3 (zip por posição, não por chave) e o cross-check do §9.3.

**Ordem e identidade são contrato, não soft-invariant (G4).** `classified[i]` corresponde ao `DetectorFinding[i]` de entrada, com os cinco campos de passthrough idênticos. O coordinator **verifica** isso por posição (§4.3) e levanta em divergência — a ordem/identidade entra como cross-check observável em §9.3, não fica como invariante implícito. Alternativa considerada e **rejeitada**: fazer o modelo emitir apenas a lista ordenada de `structured_context` (sem echo dos campos de passthrough) e o coordinator zipar sobre seus próprios `DetectorFinding` por posição. Rejeitada porque tornaria um reordenamento do modelo **indetectável** (o coordinator ziparia cegamente posição→finding); o echo do passthrough permite *detectar* reordenamento (`classified[i].file != input[i].file`), trocando um pouco de verbosidade/tokens por verificabilidade — escolha pró-audit, coerente com o resto da spec.

### 3.2 Schema produzido por `model_json_schema()`

Pydantic 2.x gera um schema de objeto com `$defs` para os submodelos. Os dois `Optional[str]` geram `anyOf: [{"type": "string"}, {"type": "null"}]` cada — **2 nós `anyOf`** no total. A doc oficial (`build-with-claude/structured-outputs`, tabela "Schema complexity limits") limita parâmetros com union types a 16 por request, "especialmente caros por custo exponencial de compilação". Dois nós ficam folgadíssimos abaixo do limite. As listas `list[str]` (sem `Optional`) adicionam **zero** nós `anyOf`. Verificação verbatim do schema gerado fica para T11+ (paridade spec ↔ schema).

### 3.3 Vocab membership: soft via system_prompt + null-on-miss, sem `Enum` (DD-C2)

Os três campos governados por vocabulário — `operation_type`, `data_categories`, `declared_legal_basis` — são restringidos aos vocabulários expostos por `policy://vocabularies` (`docs/architecture-overview.md` §5.4: *"Valores em `operation_type`, `data_categories` e `declared_legal_basis` são restringidos aos vocabulários jurisdicionais"*). **Nota de camada:** `operation_type` e `declared_legal_basis` mapeiam aos vocabulários *jurisdicionais* (`operation`, `lawful_basis`); `data_categories` mapeia ao vocabulário *estrutural* de categorias (chave `data_categories`, derivado de POL-000, framework-neutro — ADR-0005 D3), co-localizado no mesmo resource (`policy-reader/canonical.md` §3.3) mas de camada distinta. `declared_transformations` é **free-form** (não governado por vocabulário).

A restrição é **soft** (via `system_prompt`) com **null-on-miss**, **não** validação hard via `Enum` Pydantic. Justificativa load-bearing:

- **RF-003 + `coordinator.md` §3.3:** *"campos nulos em `structured_context` são válidos per RF-003 (extração que falha em mapear ao vocabulário resulta em null, não em invenção)."* `Enum` hard rejeitaria não-membros em vez de nullá-los — conflito direto.
- **Invariante "Classifier descreve, Matcher julga":** validar membership hard é o Classifier **julgando** pertencimento — meio passo na direção do Matcher. A "Nota sobre scoped access" de `coordinator.md` §3.3 já fixa que a fronteira Resource-vs-Tool é preservada em **nível de capability**, não de validação.
- **Precedente do Reporter:** o cross-check #3 (vocabulary membership) foi **removido** do Reporter em #42 por contradizer §2.4 + §8.3 — *"vocab validation é semântica do Matcher upstream, não shape do Reporter"* (`reporter.md` §4.8). O Classifier está ainda mais a montante do Matcher que o Reporter; aplicar a mesma fronteira é consistência, não exceção.

Operacionalmente: o `system_prompt` (§5.1) instrui o modelo a carregar o vocabulário via `ReadMcpResourceTool` no início e usar os valores carregados para restringir `operation_type`, `data_categories` e `declared_legal_basis`; quando a extração não mapeia, o campo é `null` (escalares) ou exclui o item não-mapeável (listas). A spec **não** enforça membership programaticamente — depende de prompt discipline + a fronteira de capability da quíntupla. O Matcher é a autoridade downstream sobre semântica de membership.

> **Obrigação à Matcher spec — cumprida.** A afirmação "o Matcher é a autoridade downstream sobre membership" foi forward-ref à `docs/specs/subagents/matcher.md` (mesmo padrão da DetectorFinding em §2.1); a spec, agora autorada, cumpre a obrigação em §2.2. O comportamento declarado **não** é degradação graciosa: o motor do `policy-reader` **valida membership de vocabulário hard** antes de avaliar `applies_to` — `data_categories` fora do vocabulário retornam `INVALID_DATA_CATEGORY`, `operation` fora retorna `INVALID_OPERATION` (ground truth `tools.py:263-279`); o erro é retornado no envelope e o coordinator decide o tratamento, não há resolução silenciosa para `not_applicable`/`indeterminate`. Isso **não** contradiz o `null`-on-miss do Classifier: o caminho normal é o Classifier nulificar valores fora-de-vocabulário (nunca emitir tokens inválidos ao Matcher), e a validação hard do motor é **segunda linha de defesa**, não o caminho normal (`matcher.md` §2.2). O Classifier continua portanto **sem** `Enum` hard próprio — introduzi-lo reintroduziria o anti-padrão removido do Reporter (§4.8) e duplicaria o backstop que já vive no motor. Catalogado como obrigação em §10.5 e como DD-C9 em §8.4/§10.4.

> 💡 **Conceito Claude relevante (Domínio 2 — Tool Design & MCP Integration).** Granularidade de scoping no SDK Python é **per-server**, não per-resource: `ReadMcpResourceTool` aceita qualquer `uri` do server registrado em `mcp_servers`. O Classifier consegue ler também `policy://catalog`, `policy://schema-version` e `policy://examples`, além do `vocabularies` designado pelo prompt. Defensável porque resources são read-only context (sem decisional capability): o Classifier pode "ver" o catálogo e a versão do schema, mas não pode emitir veredito nem retornar conteúdo cláusula-specific (`get_clause`, restrito ao Matcher pela whitelist). O invariante se sustenta no nível de capability, não no nível de resource (nuance a documentar em ADR-0012 retroativo; ver `coordinator.md` §3.3).

### 3.4 Casos que parecem erro mas não são

- **Campos `null` em `structured_context`.** Válido per RF-003. Extração que não mapeia ao vocabulário resulta em `null` (escalares) — não em invenção, não em erro.
- **Candidato parcialmente classificável.** Pipeline prossegue mesmo com candidatos cujo `structured_context` tem alguns campos preenchidos e outros nulos (`coordinator.md` §3.3).
- **Lista enriquecida vazia.** Quando o Detector emitiu `findings: []`, o Classifier emite `{"classified": []}`. Não é erro (ver §2.3).
- **Mesmo candidato classificado de forma divergente em re-execução.** Classifier é stateless e não-determinístico (modelo de LM). Divergência em re-run é esperada; coordinator não compara runs.
- **`data_categories` do Classifier difere do que o `rule_id` do Detector sugere.** Não é erro: o `rule_id` é heurística de detecção sintática; `data_categories` é categorização lexical contra o vocabulário, possivelmente mais fina ou mais conservadora. O Matcher reconcilia downstream.

## 4. Output mechanism

> Esta seção é o análogo Branch B de §4 do Reporter ("Tool `emit_report`"). Classifier opera em Branch B (output_format), sem tool customizada. Asymmetry deliberada, paralela a `triager.md` §4.

### 4.1 Não há custom tool

O Classifier **não** define `@tool`, **não** instancia `create_sdk_mcp_server`, **não** registra MCP server in-process. Output emitido nativamente via runtime do SDK quando o modelo produz texto que valida contra o schema de `output_format`. (O `policy-reader` registrado em `mcp_servers` é server **out-of-process** consumido como resource — não é o mecanismo de output.)

### 4.2 Mecânica do output

1. Coordinator chama `query(prompt=..., options=classifier_options)` com `output_format` configurado.
2. Modelo carrega `policy://vocabularies` via `ReadMcpResourceTool` (startup), depois emite uma sequência de `AssistantMessage` intercaladas com `ToolUseBlock`s (`Read`/`Grep`/`ReadMcpResourceTool`) e seus `ToolResultBlock`s.
3. Quando o modelo emite texto parseável e validável contra o schema, o agentic loop encerra e o SDK emite `ResultMessage` com `subtype="success"` e `structured_output` populado.
4. Se o JSON falha validação, o SDK injeta retry transparentemente (não visível como turn explícito).
5. Se retries esgotam, o SDK emite `ResultMessage` com `subtype="error_max_structured_output_retries"` (tabela em §6.3).

### 4.3 Coordinator captura

```python
# Pseudocódigo do coordinator (autoritativo: coordinator.md §3.3)
async for message in query(prompt=classifier_prompt, options=classifier_options):
    if isinstance(message, ResultMessage):
        if message.subtype == "success" and message.stop_reason != "refusal":
            classifier_output = ClassifierOutput.model_validate(message.structured_output)
            # G4 — verificação posicional de ordem/identidade (passthrough não pode driftar):
            if len(classifier_output.classified) != len(detector_output):
                raise SubagentContractViolation(stage="classifier", reason="length_mismatch")
            for i, (out, src) in enumerate(zip(classifier_output.classified, detector_output)):
                if (out.file, out.line, out.rule_id, out.snippet) != \
                   (src.file, src.line, src.rule_id, src.snippet):
                    raise SubagentContractViolation(stage="classifier", reason="passthrough_drift", index=i)
            break
        elif message.subtype == "success" and message.stop_reason == "refusal":
            # SDK marcou success mas modelo refusou; structured_output pode estar ausente
            raise SubagentRefusedTask(stage="classifier")
        else:
            raise SubagentValidationFailed(stage="classifier", subtype=message.subtype)
```

Validação Pydantic adicional no coordinator (`model_validate`) é defense-in-depth: o SDK valida contra JSON Schema antes de devolver, mas os tipos Python ricos (submodelos, optionality) só emergem após `model_validate`. **A verificação posicional (G4)** é uma segunda camada além do shape: o `model_validate` confirma *forma*, o zip-compare confirma *ordem e identidade* — que o modelo não reordenou, dropou, adicionou nem mutou os campos de passthrough. Por ser posicional (índice), funciona mesmo com `(file, line, rule_id)` duplicado (G10). `SubagentContractViolation` é classe nova vs o Triager (que não tem passthrough a verificar) — catalogada como companion edit ao módulo de erros do coordinator (§10.5(1)). Discriminação dupla `subtype` × `stop_reason` no caminho de sucesso é documentada na doc oficial (`agent-sdk/agent-loop`); ver §6.3. Fora a verificação posicional, pattern idêntico ao do Triager (`triager.md` §4.3) — consistência cross-subagent Branch B.

### 4.4 Sem dual sink — persistência é do coordinator, não do Classifier

Contraste com Reporter §4.7 (dual sink). O Classifier emite **single sink** via `ResultMessage.structured_output`. A gravação em `03-classifier.json` é feita **pelo coordinator** após captura (`coordinator.md` §3.3: *"Output Pydantic-validado, gravado em `03-classifier.json`"*), como audit artifact no scratchpad — decisão S2' de `coordinator.md` §4 (scratchpad audit-only; subagentes não têm `Read` sobre `.scratchpad/`). Não é dual sink do Classifier: o Classifier não escreve em disco; o coordinator persiste o que capturou. Distinção load-bearing para a destilação do template (§4 do template é condicional ao branch + locus de persistência).

## 5. System prompt

### 5.1 Texto canônico

> O SDK opera em "minimal system prompt" mode por default (`agent-sdk/modifying-system-prompts`). O prompt precisa ser auto-suficiente quanto a instrução de uso de tools (inclusive o carregamento do vocabulário via `ReadMcpResourceTool`) — não há herança de Claude Code preset. O bloco `<examples>` ao final é parte integral do prompt canônico (convenção alinhada a `reporter.md` §5.1 e `triager.md` §5.1).
>
> **Template renderizado via `.format()` / f-string Python.** Os candidatos do Detector são injetados em `{candidates_block}`; JSON literals nos exemplos usam double-brace (`{{...}}`) per escape syntax. Implementador T11+ ciente de que o template é format-string.

```
Você é o Classifier de um sistema de code review automatizado de conformidade
LGPD. Sua única função é EXTRAIR contexto estruturado e factual de cada ponto
de tratamento candidato detectado por uma etapa anterior. Você DESCREVE o que o
código faz e o que ele declara fazer. Você NÃO julga conformidade, NÃO consulta
cláusulas da Política, NÃO emite veredito. Julgamento é responsabilidade de uma
etapa posterior (o Matcher).

CARREGAMENTO DE RESOURCES (PRIMEIRO PASSO OBRIGATÓRIO)

Antes de classificar qualquer candidato, use ReadMcpResourceTool com
server='policy-reader' para carregar dois resources do framework declarado:

1. uri='policy://vocabularies' — os vocabulários jurisdicionais. Definem os
   valores VÁLIDOS para tres dos quatro campos: operation_type,
   data_categories e declared_legal_basis. Use os valores carregados para
   restringir o que você emite nesses campos. Se a leitura retornar erro ou
   vier vazia em runtime, NÃO improvise tokens, NÃO faça retry indefinido,
   NÃO aborte: opere com todos os campos de vocabulário em null/[] — mesma
   postura uniforme do policy://examples abaixo (nada mapeável = tudo null
   nos campos governados).
2. uri='policy://examples' — exemplos de mapeamento código→token específicos
   da jurisdição corrente. Use-os como REFERÊNCIA de como candidatos típicos
   desta jurisdição se traduzem em structured_context. Se o resource vier
   vazio, OU retornar erro, OU não existir (jurisdição sem exemplos
   autorados, ou recurso ainda não publicado), trate os três casos de forma
   IDÊNTICA: opere apenas com a disciplina abaixo e o exemplo de miss-total
   ao final deste prompt. NÃO invente exemplos. Crucial: a ausência de
   exemplos NÃO é sinal de que a disciplina pode ser relaxada — as regras de
   "describe / null-on-miss / só o que está declarado" valem integralmente
   com ou sem exemplos carregados.

Os tokens válidos e os exemplos de mapeamento NÃO estão neste prompt: vêm
dos resources carregados. Este prompt define apenas a forma e a disciplina;
o conteúdo jurisdicional é dado da Política.

TOOLS DISPONÍVEIS

- ReadMcpResourceTool: carregue policy://vocabularies e policy://examples
  (primeiro passo) e, se útil, policy://catalog ou policy://schema-version.
  Resources são somente-leitura; você não pode invocar tools de avaliação.
- Read: leia o conteúdo de arquivos para inspecionar imports, definições de
  função e contexto além das linhas do snippet de cada candidato. Leia apenas
  os arquivos referenciados pelos candidatos; não navegue o repositório inteiro.
- Grep: busque declarações de base legal, transformações (anonimização, hash,
  criptografia) ou anotações relevantes em comentários e docstrings próximas
  às linhas dos candidatos.

Você NÃO tem acesso a Glob, Bash, Write, Edit, nem às tools do policy-reader
(get_clause, find_clauses_by_law_article, check_applicability). Não tente
invocá-las.

OS QUATRO CAMPOS DE structured_context

Para cada candidato, extraia:

1. operation_type — a operação que o código realiza sobre o dado pessoal.
   Use APENAS um token do vocabulário operation carregado de
   policy://vocabularies. Se não conseguir mapear com confiança, emita null.
2. data_categories — lista das categorias de dado pessoal que o candidato
   toca. Use APENAS tokens do vocabulário de categorias carregado. Liste
   todas que identificar; lista vazia [] se nenhuma mapeável.
3. declared_legal_basis — a base legal EXPLICITAMENTE declarada no código
   ou em comentário/docstring próxima, quando presente. Use APENAS um token
   do vocabulário de base legal carregado. Se nenhuma base legal estiver
   declarada, emita null. NÃO infira base legal a partir do tipo de
   operação — só registre o que está declarado.
4. declared_transformations — lista de transformações que o código DECLARA
   aplicar (ex.: hashing, encryption, anonymization — termos técnicos
   universais, NÃO restritos a vocabulário jurisdicional). Liste o que
   estiver declarado; lista vazia [] se nenhuma.

Os tokens concretos válidos para os campos 1-3 estão nos vocabulários
carregados, não aqui — este prompt não os enumera (independência de camada:
trocar a Política troca os tokens sem editar este prompt).

PRINCÍPIOS

1. Descreva, não julgue. Você extrai o que o código faz e declara. Você não
   decide se é conforme ou não.
2. Null não é invenção. Se um campo de vocabulário não mapeia, emita null
   (escalares) ou exclua o item (listas). NUNCA invente um valor que não
   está no vocabulário nem declarado no código.
3. Só o que está declarado. Para declared_legal_basis e
   declared_transformations, registre apenas o que está EXPLÍCITO no código,
   comentário ou docstring. Ausência de declaração é null / [], não
   suposição.
4. Preserve os campos do candidato. Copie file, line, rule_id, snippet e
   surrounding_context verbatim; adicione apenas structured_context.

CANDIDATOS A CLASSIFICAR

{candidates_block}

FORMATO DO OUTPUT

Sua resposta final será validada contra um schema JSON. Emita um objeto com
uma chave "classified" cujo valor é a lista de candidatos enriquecidos, na
mesma ordem recebida. Cada elemento tem os cinco campos do candidato mais
structured_context com os quatro campos acima.

EXEMPLOS

Os exemplos POSITIVOS de mapeamento (candidato típico → tokens de
operation/categoria/base legal desta jurisdição) foram carregados de
policy://examples no primeiro passo. Trate-os como referência canônica de
como esta jurisdição mapeia código em structured_context. NÃO há exemplos
positivos com tokens neste prompt — eles são dado da Política (camada
jurisdicional), não do sistema.

O único exemplo embutido aqui é agnóstico de jurisdição: demonstra o
comportamento de miss-total (quando nada mapeia ao vocabulário), que vale
para qualquer framework e ancora o princípio "null não é invenção".

<examples>

<example>
Candidato:
  file: src/legacy/util.py
  line: 5
  rule_id: pii-name-var
  snippet: "tmp = obj.name"
  surrounding_context: "# Helper interno; obj é um objeto genérico de domínio, name pode ou não ser dado pessoal."

Após Read e Grep, você não conseguiu determinar com confiança qual operação
o código realiza sobre o dado nem se 'name' é dado pessoal neste contexto
genérico. Não há base legal nem transformação declarada.

Output (elemento de "classified"):
  {{"file": "src/legacy/util.py", "line": 5,
    "rule_id": "pii-name-var",
    "snippet": "tmp = obj.name",
    "surrounding_context": "# Helper interno; obj é um objeto genérico de domínio, name pode ou não ser dado pessoal.",
    "structured_context": {{
      "operation_type": null,
      "data_categories": [],
      "declared_legal_basis": null,
      "declared_transformations": []
    }}}}
</example>

</examples>
```

> 💡 **Conceito Claude relevante (Domínio 4 — Prompt Engineering & Structured Output, Task Statement 4.5).** Few-shot **dividido por camada**: a *disciplina* (describe / null-on-miss / only-declared) e o exemplo de miss-total — agnósticos de jurisdição — vivem no prompt (camada 2, `src/`); os *exemplos positivos de mapeamento*, que carregam tokens de jurisdição, vêm de `policy://examples` carregado em runtime (camada 1). O modelo recebe disciplina in-prompt + mapeamento jurisdicional via resource. Trade-off declarado: exemplo carregado-como-tool-result é âncora mais fraca que few-shot in-prompt — aceito em troca de independência de camada (RF-008); revisitar se a qualidade empírica de mapeamento sofrer em T11+ (DD-C11). O exemplo de miss-total embutido é deliberado: few-shot só com positivos ensinaria o modelo a sempre preencher, contradizendo RF-003.

### 5.2 Behaviors explícitos

- **Tom.** Extração técnica, sem hesitação verbal. Não pedir confirmação (não há usuário no loop).
- **Granularidade.** Um `structured_context` por candidato; preservar a ordem recebida.
- **Idioma.** Valores de `structured_context` são **tokens canônicos em inglês** (per ADR-0006, convenção do vocabulário). Não há prosa ao usuário neste subagent — diferente do Triager (cuja `relevance_summary`/`skip_reason` é português), o output do Classifier é puramente tokens + passthrough.
- **Não inventar contexto.** Decisão baseada apenas no candidato + leitura dos arquivos referenciados + vocabulário carregado. Sem acesso à Política (cláusulas), sem runtime, sem histórico do repo.

### 5.3 Few-shot strategy — nota meta

Os exemplares seguem as diretrizes da doc oficial (`prompt-engineering/multishot-prompting`): 3-5 exemplares diversos, wrapped em tags, cobrindo edge cases. **Distribuídos por camada** (DD-C10): o prompt em `src/` (camada 2) carrega **um** exemplar agnóstico — miss-total — mais a disciplina prosaica; os exemplares **positivos** de mapeamento (coleta com categorias; storage com base legal + transformação; transmissão de dado não-pessoal → `data_categories: []`) vivem em `policy://examples` (camada 1, per-jurisdição) e são carregados em runtime. Cobertura combinada permanece 3-5 diversos **condicionada ao seed** de `policy://examples` (≥2 positivos LGPD, obrigação §10.5(7)); a diferença é o *locus*: token-bearing → camada 1, agnóstico → camada 2. Sem o seed, a cobertura cai para 1 (só miss-total) — por isso o seed é obrigação carimbada, não suposição (G12/L1, DD-C11). Esta seção é nota meta — não duplica conteúdo. Formato canônico do resource `policy://examples` é decisão do `policy-reader` spec / SCHEMA (companion edit §10.5).

### 5.4 Unified prompt — sem branch conditional

Um único prompt cobre todos os candidatos. Não há "prompt de candidato mapeável" vs "não-mapeável" — o modelo emite `null`/`[]` dentro do mesmo shape. Paralelo a `triager.md` §5.4 e `reporter.md` §5.4.

## 6. Error handling

### 6.1 Estrutura canônica

Classifier Branch B não tem envelope de erro customizado — diferente do Reporter (`reporter.md` §6.1, que emite erros via `emit_report` com `isError: true`). O Classifier só falha via mecanismos nativos do SDK; a propagação de erro acontece no coordinator. Idêntico em estrutura a `triager.md` §6.1.

### 6.2 Classes de erro relevantes

| Classe       | Locus       | Quem detecta                          | Quem propaga                                 |
|--------------|-------------|---------------------------------------|----------------------------------------------|
| Validation   | SDK runtime | SDK (schema validation / retry exhaustion) | Coordinator (via `SubagentValidationFailed`) |
| Budget       | SDK runtime | SDK (max_turns / max_budget_usd)      | Coordinator (via `SubagentUnresponsive`)     |
| Refusal      | Modelo      | Modelo (safety refusal)               | Coordinator (via `SubagentRefusedTask`)      |
| System       | OS-level    | Coordinator (try/except sobre query)  | Coordinator (via re-raise tipado)            |

O Classifier não tem erros de **business** intra-handler (não há handler entre receber input e emitir output — Branch B). **Falha de leitura do resource `policy://vocabularies`** não é classe de erro nova do Classifier: per `docs/specs/policy-reader/canonical.md` §3.3, falha de I/O do vocabulário é erro de protocolo detectado no **startup do server** (o server falha o boot e o coordinator trata upstream); consumo do resource numa sessão estabelecida é idempotente, sem casos de erro de domínio em runtime. Se, contra a expectativa, o `ReadMcpResourceTool` falhar em runtime, o efeito observável é o modelo proceder sem vocabulário → campos de vocabulário tendem a `null` (degradação graciosa, coberta por RF-003), não crash. **A diferença entre os dois resources está em boot-time, não em runtime** (companion edit ao `policy-reader`, §10.5(7)): `vocabularies` ausente **impede o boot** do server (é necessário à *constraint*); `examples` ausente **permite o boot**, apenas perde a âncora positiva de mapeamento (é *aid* de qualidade). Em runtime de sessão estabelecida, ambos degradam graciosamente — `vocabularies` faltando → campos null; `examples` faltando/erro/vazio → disciplina-only (§5.1 trata os três casos idênticos). O contraste é só sobre o que aborta o startup do server.

A classe **Refusal** aplica via SDK-level `stop_reason="refusal"` — plausível para o Classifier porque candidatos carregam `snippet`/`surrounding_context` com possível PII real (fixtures com CPF literais, dados de teste). Coordinator discrimina mesmo dentro de `subtype="success"` (pseudocódigo §4.3).

### 6.3 Família de `ResultMessage.subtype` e `stop_reason`

Dois eixos independentes, listas canônicas verbatim da doc oficial (idênticas às de `triager.md` §6.3, por serem invariante Branch B do SDK — não duplicação de decisão, mas repetição da tabela invariante exigida pelo template).

**Eixo 1 — `ResultMessage.subtype`** (de `agent-sdk/agent-loop`):

| `subtype`                              | Significado                                                | `result` populado | Tratamento no coordinator                    |
|----------------------------------------|------------------------------------------------------------|-------------------|----------------------------------------------|
| `success`                              | Task completa; `structured_output` populado.               | Sim               | Consumir + verificar `stop_reason` (eixo 2). |
| `error_max_turns`                      | Estourou `max_turns` antes de emitir output validável.     | Não               | Levantar `SubagentUnresponsive`.             |
| `error_max_budget_usd`                 | Estourou `max_budget_usd` (se configurado).                | Não               | Levantar `SubagentUnresponsive`.             |
| `error_during_execution`               | Erro interrompeu o loop (API failure, cancelled).          | Não               | Levantar `SubagentExecutionError`.           |
| `error_max_structured_output_retries`  | SDK esgotou retries tentando produzir JSON válido.         | Não               | Levantar `SubagentValidationFailed`.         |

**Eixo 2 — `ResultMessage.stop_reason`** (de `build-with-claude/handling-stop-reasons`):

| `stop_reason`                       | Relevância para Classifier                                                |
|-------------------------------------|---------------------------------------------------------------------------|
| `end_turn`                          | Caminho feliz (com `subtype=success`).                                    |
| `max_tokens`                        | `structured_output` pode estar incompleto (lista grande de candidatos).   |
| `stop_sequence`                     | Não aplicável (Classifier não usa stop_sequences).                        |
| `tool_use`                          | Intermediário; não aparece em `ResultMessage`.                            |
| `pause_turn`                        | Não aplicável (sem server tools).                                         |
| `refusal`                           | **Crítico**: pode coexistir com `subtype=success` e `structured_output` ausente/incompleto. PRs com PII real são gatilho plausível. |
| `model_context_window_exceeded`     | Plausível para PRs grandes com muitos candidatos + leituras volumosas.    |

**Caso crítico — `subtype=success` com `stop_reason=refusal`.** A doc oficial: a saída pode não casar o schema porque a mensagem de refusal tem precedência sobre as constraints. Coordinator discrimina `stop_reason="refusal"` mesmo dentro de `subtype="success"` e trata como classe Refusal (§4.3).

### 6.4 Não há família intra-handler

Reporter §6.3 documenta 7 errorCodes intra-handler. Classifier não tem locus análogo — Branch B sem handler executando lógica entre input e output. Validation-retry é gerenciado pelo SDK transparentemente. Asymmetry deliberada vs Reporter; sinal para a destilação do template (§6.3 do template é condicional ao branch).

### 6.5 Casos que parecem erro mas não são

- **`structured_context` com campos nulos.** Não é erro — RF-003 (§3.4).
- **`data_categories` divergente do `rule_id`.** Não é erro — categorização lexical é mais fina que detecção sintática (§3.4).
- **Mesmo candidato re-classificado diferente em re-run.** Não é erro — não-determinismo de LM.
- **Lista enriquecida vazia.** Não é erro — propagação de `findings: []` do Detector (§2.3).

## 7. Provenance e versionamento

### 7.1 Versão da spec

`spec_version: 0.1.0`. Convenção SemVer (alinhada a `reporter.md` §7.1, `triager.md` §7.1). Bump rules:

- **Patch (0.1.x):** correções de redação, esclarecimentos, sem mudança de contrato.
- **Minor (0.x.0):** adição de campos a `StructuredContext`/`ClassifiedCandidate`; novos casos em §9; novos exemplares few-shot em §5.1.
- **Major (x.0.0):** mudança de contrato I/O (campos removidos/renomeados, semântica de `structured_context` alterada, troca de Branch B para Branch A, mudança no shape consumido do Detector ou produzido para o Matcher).

> **Ressalva sobre "minor" e a postura de validação do consumer.** A classificação de "adição de campo" como *minor* assume que o consumer (Matcher) tolera campos desconhecidos. Se o Matcher validar o `structured_context` recebido com Pydantic `extra="forbid"`, um campo novo **quebra** a validação — e a adição deixa de ser minor não-breaking para o consumer. A postura de validação do Matcher (`ignore`/`allow`/`forbid`) é, portanto, parte implícita deste contrato e deve ser declarada na Matcher spec (ligada à obrigação de §3.3 / DD-C9). Até lá, tratar adição de campo como potencialmente breaking ao consumer.

### 7.2 Versão do schema

`StructuredContext` / `ClassifiedCandidate` / `ClassifierOutput` acompanham `spec_version` (schema é parte do contrato I/O canônico desta spec). Locus físico: `src/subagents/classifier/models.py` (per DD-T15) quando T11+ implementar.

### 7.3 Não há trinque de provenance jurídico-temporal

Classifier **não** emite `(policy_schema_version, policy_version, legal_framework)`. Razão: o trinque é subset do RF-009 que aplica a vereditos do Matcher e ao Report do Reporter — o Classifier não consulta a Política (cláusulas), não emite veredito, e seu output não vai direto ao Report top-level (vai ao Matcher). O `structured_context` é descrição factual, não veredito com proveniência jurídica. Asymmetry vs Reporter §7.3 / Matcher; sinal para o template (§7 condicional à exposição ao Report externo).

**Decisão de provenance da categorização — deferida (DD-C5).** Há um argumento para o Classifier carimbar qual versão do vocabulário consultou (`policy://schema-version`) junto ao `structured_context`, de modo que a categorização seja auditável contra a versão de vocabulário sob a qual foi produzida. No MVP isso é coberto indiretamente: o Matcher consome o `structured_context` e estampa o trinque (incluindo `policy_schema_version`) por finding, e a versão de vocabulário e a de schema da Política são versionadas em conjunto pelo `policy-reader`. Carimbar no Classifier seria redundância (mais auditável) vs ruído (campo a mais sem consumidor no MVP). Deferido a T11+/benchmark (DD-C5).

### 7.4 Mutabilidade durante execução

Classifier é stateless e immutable per query. Sem hot reload, sem arquivo persistente próprio. Cada `query()` é fresh. O vocabulário é carregado por query via `ReadMcpResourceTool` (reflete o estado do `policy-reader` no momento da execução).

## 8. Não-objetivos e fronteiras

### 8.1 Não-objetivos do Classifier

Lista exaustiva do que o Classifier **não** faz, mesmo que pudesse:

- **Não detecta candidatos.** Responsabilidade do Detector (RF-001) via `semgrep-runner.scan_diff`. Classifier recebe candidatos prontos; não localiza pontos de tratamento.
- **Não avalia conformidade.** Responsabilidade do Matcher (RF-004). Classifier não consulta cláusulas, não emite veredito.
- **Não consulta cláusulas.** Sem as tools do `policy-reader` (`get_clause`, `find_clauses_by_law_article`, `check_applicability`) no allowlist.
- **Não valida membership de vocabulário de forma hard.** Restrição soft + null-on-miss; sem `Enum` (§3.3). Validação de membership é semântica do Matcher.
- **Não infere base legal.** Só registra `declared_legal_basis` quando explicitamente declarada; ausência → `null` (não suposição a partir do `operation_type`).
- **Não emite trinque de provenance jurídico-temporal.** Ver §7.3.
- **Não enumera paths nem consome `changed_paths`.** Opera sobre os `file` dos candidatos; sem `Glob`. `changed_paths` (DD-T05) é insumo do Triager/coordinator, não do Classifier (§2.1).
- **Não modifica filesystem.** Tools restritas a `Read` + `Grep` + resource read; sem `Write`/`Edit`/`Bash`.
- **Não persiste estado próprio.** Stateless per §7.4; a gravação de `03-classifier.json` é do coordinator (§4.4).

### 8.2 Não-objetivos do escopo

- **Não cobre PRs cross-repository** (alinhado a `architecture-overview.md` §7.2).
- **Não cobre análise temporal cross-PR.** Cada execução é independente.

### 8.3 Fronteira epistêmica

O Classifier extrai contexto a partir de **código local** (via `Read`/`Grep` sobre arquivos dos candidatos) + **vocabulário jurisdicional** (via `policy://vocabularies`). Não tem janela para:

- Estado runtime do sistema (consentimento efetivo, configuração de outro serviço).
- Comportamento downstream do código (o que de fato acontece com o dado coletado depois).
- A Política cláusula-a-cláusula (não consulta `get_clause`).

Implicação: o `structured_context` é **descrição do declarado e do observável estaticamente**, não avaliação. "Declared" nos nomes dos campos (`declared_legal_basis`, `declared_transformations`) é deliberado — o Classifier registra o que o código *afirma*, e o Matcher avalia se a afirmação procede contra a Política (incluindo, via RF-005, emitir `indeterminate` quando a verificação exige dimensão fora da análise estática). O invariante "Classifier descreve, Matcher julga" é a fronteira que torna a Política trocável sem reescrita do Classifier (RF-008).

### 8.4 Decisões deferidas

| ID      | Decisão                                                                                       | Razão do deferment                                                          | Quando reabre                                  |
|---------|-----------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|------------------------------------------------|
| DD-C5   | Carimbar versão de vocabulário consultada (`policy://schema-version`) no `structured_context` | Coberto indiretamente pelo trinque do Matcher no MVP; campo sem consumidor   | T11+/benchmark, se auditoria da categorização exigir |
| DD-C6   | `max_turns`: constante vs `base+k*N` vs cap-com-truncação                                     | Constante não escala com N (G5); `k` desconhecido pré-T11 — chutar fórmula fere measure-before-tune. Backstop: `error_max_turns` → escalação (§1.5) | Fim de T11+ (Provisão MC-D)                    |
| DD-C7   | Ratificação do shape `DetectorFinding` consumido                                              | Detector spec não autorada; shape pinado contra arch §5.3 como forward-ref   | Quando a Detector spec for autorada            |
| DD-C8   | `reasoning` field opcional (chain-of-thought estruturado antes da extração)                   | Benefício não medido; análogo a DD-T14 do Triager                            | T11+ com catálogo MC-D, com e sem o campo      |
| DD-C9   | Postura do Matcher sobre membership recebido + postura de validação do consumer (`extra=ignore/forbid`) | **Fechada** — `matcher.md` §2.2/§2.3/§6.6 (#48): fora-de-vocab → hard-reject (`INVALID_DATA_CATEGORY`/`INVALID_OPERATION`, `tools.py:263-279`); no-clause-match → `not_applicable` + `requires_human_review` (graciosa, DD-M8); consumer `extra="ignore"` + projeção rename+drop (DD-M11) | — |
| DD-C10  | Few-shot positivo como dado de camada 1 via `policy://examples` (não hardcoded no prompt) | **Fechada** nesta sessão (opção C): exemplos são vocab-token-bound → camada jurisdicional; mecanismo = resource dedicado. Autoridade = **analogia** ao princípio de ADR-0005 D8 (D8 decide *regras*); decisão formal = **Decisão 9** no amendment do PR autônomo de `policy://examples` | — (resource = PR autônomo, prereq de merge; §10.5(7)) |
| DD-C11  | Qualidade do few-shot positivo carregado: cold-start (MVP) + força tool-result vs in-prompt | **Cold-start resolvido, não condicional** (M1): o PR de `policy://examples` semeia LGPD com ≥2 positivos (os removidos do §5.1), preservando paridade com a rodada 1. Sem o seed, cold-start rodaria só com miss-total + prosa, abaixo da recomendação 3-5 do §5.3. Resíduo (tool-result é âncora mais fraca que in-prompt) fica para A/B | Seed carimbado em §10.5(7); A/B de força fica para T11+ |
| DD-C12  | Verificação de ordem/identidade entre input e output | **Fechada** (G4): contrato hard, verificado posicionalmente pelo coordinator (§4.3, §9.3); alternativa de output-só-structured_context rejeitada por tornar reordenamento indetectável | — |

## 9. Critérios de aceitação

### 9.1 Happy-path scenarios

- [ ] Candidato em `src/users/registration.py` com função recebendo `cpf`/`email` → `structured_context.operation_type == "collection"`, `data_categories` contém `cpf` e `email`, `declared_legal_basis == null` (sem declaração), `declared_transformations == []`.
- [ ] Candidato cujo `surrounding_context` declara base legal e o snippet aplica hash → `declared_legal_basis` é o token de vocabulário correspondente e `declared_transformations` contém `hashing`.
- [ ] Lista de N candidatos do Detector → `classified` tem exatamente N elementos, na mesma ordem, com os 5 campos do candidato preservados verbatim + `structured_context`.

### 9.2 Edge case scenarios

- [ ] Candidato cujo dado não mapeia a nenhuma categoria do vocabulário → `data_categories == []` (não invenção de categoria).
- [ ] Candidato em contexto genérico/ambíguo → `operation_type == null` (não chute), demais campos de vocabulário coerentemente nulos/vazios.
- [ ] Detector emitiu `findings: []` → Classifier emite `{"classified": []}`; pipeline prossegue (§2.3).
- [ ] Candidato com base legal NÃO declarada mas `operation_type` claro → `declared_legal_basis == null` (não inferida do tipo de operação; princípio 3 do §5.1).

### 9.3 Cross-check scenarios

- [ ] Todo elemento de `classified` carrega os quatro campos de `structured_context`.
- [ ] Valores não-nulos de `operation_type`, `data_categories` e `declared_legal_basis` pertencem ao vocabulário exposto por `policy://vocabularies` do framework declarado — **ou** são `null`/`[]` (RF-003). Nenhum valor fora-do-vocabulário e não-nulo.
- [ ] Nenhum candidato é **rejeitado** por valor fora do vocabulário (ausência de hard-enum: o efeito de um miss é `null`/exclusão do item, não erro de validação).
- [ ] Output passa `ClassifierOutput.model_validate(message.structured_output)` no coordinator sem `ValidationError`.
- [ ] Coordinator discrimina `subtype="success"` + `stop_reason="refusal"` e levanta `SubagentRefusedTask` em vez de consumir `structured_output` potencialmente ausente.
- [ ] **Ordem e identidade (G4):** `len(classified) == len(detector_output)` e, para todo `i`, os campos de passthrough de `classified[i]` (`file`, `line`, `rule_id`, `snippet`) são idênticos a `detector_output[i]`. Divergência (reordenamento, drop, adição, mutação de passthrough) levanta `SubagentContractViolation`. Verificação **posicional**, robusta a `(file, line, rule_id)` duplicado (§3.1, G10).

### 9.4 Provenance scenarios

- [ ] `spec_version` consultável em metadados da implementação (e.g., constante em `src/subagents/classifier/__init__.py`).
- [ ] Mudança no shape de `StructuredContext`/`ClassifiedCandidate` dispara bump de `spec_version` per §7.1.

### 9.5 Persistence scenarios

Não aplicável ao Classifier (stateless §7.4). Critério estrutural: ausência de arquivos persistidos **pelo Classifier**; `03-classifier.json` é gravado pelo coordinator (§4.4), verificável via inspeção do scratchpad no catálogo de PRs sintéticos.

## 10. Cross-references

### 10.1 Source-of-truth artifacts

- **Função e posição:** `docs/architecture-overview.md` §3, §5.4.
- **Capacidade externa:** `docs/REQUIREMENTS.md` RF-003 (Classificação contextual de candidatos).
- **Skeleton de invocação + tool-set:** `coordinator.md` §3.3 (locus canônico).
- **Resource scoping (Resource vs Tool):** ADR-0005 Decision 4; `docs/specs/policy-reader/canonical.md` §3.3 (Classifier listado como consumidor autorizado).
- **Input contract (Detector output):** `docs/architecture-overview.md` §5.3 (forward-ref ratificada pela Detector spec; ver DD-C7).
- **Lockdown pattern:** `coordinator.md` §2 (quíntupla canônica).
- **Branch B reference:** `triager.md` §1.4, §4, §6.3 (mecanismo gêmeo).
- **Branch A reference:** `reporter.md` §4 (`emit_report`, contraste arquitetural).
- **`output_format` wire form:** `reporter.md` §10.6 + smoke-test `sdk_output_format_lockdown`; confirmada corrente em `agent-sdk/structured-outputs` (doc oficial).
- **Lista canônica de subtypes:** `agent-sdk/agent-loop`. **Lista de stop_reasons:** `build-with-claude/handling-stop-reasons`.

### 10.2 ADRs aplicáveis

- **ADR-0001** — stack canônica.
- **ADR-0005 Decision 4** — resource access scoping (Classifier consome `policy://vocabularies`, sem tools).
- **ADR-0006** — convenção de tokens em inglês para vocabulários.
- **ADR-0008** — task decomposition (tasks T11+ implementam este spec).
- **ADR-0012 (retroativo, a redigir)** — nuance de scoped access per-server vs per-resource (§3.3); **e** a distinção *capability* (alcance per-server via `mcp_servers`) vs *availability* (built-ins de resource governados pelo campo `tools`) materializada em #48-b (§1.4; `coordinator.md` §10 DD-9.1). Rationale a redigir em sessão dedicada — não a frio.
- **ADR pendente** — pin `claude-agent-sdk` em `pyproject.toml` (Provisão MC-E).

### 10.3 Gates pré-implementação

Smoke-tests da Fase 0 (gate-of-gates; halt clause: falha → volta à spec antes de qualquer linha de produção):

- **Gate Branch B** — smoke-test `sdk_output_format_lockdown` (sessão #43) valida `output_format=json_schema` envelopado sob lockdown em SDK 0.2.87. **Mas validou o shape do Triager, não o do Classifier.** Gate adicional desta spec: confirmar que o shape específico do Classifier — `ClassifierOutput` com `$defs`, dois `Optional[str]` aninhados (2 nós `anyOf`), listas — é aceito pelo SDK. Não assumir paridade com o Triager.
- **Gate resource access — PASS** (#48-b, evidência persistida em `scripts/smoke_tests/check_applicability_48b/RESULTS.md`). A #48-b mediu os 4 estados de `tools` lado a lado contra o `policy-reader` real: sob `tools=[]` **e** `tools=["Read"]` o `ReadMcpResourceTool` está ausente (0 read attempts, modelo verbaliza "unavailable"); sob `tools=["Read","ReadMcpResourceTool","ListMcpResourcesTool"]` lê o catálogo (1 attempt). Os dois eixos saem limpos: server tools `mcp__policy-reader__*` sobrevivem a `tools=[]` (via `mcp_servers`), built-ins de resource somem sem entrada no `tools` field (`allowed_tools` não basta — Issue #361). Por isso o `tools` do Classifier inclui `ReadMcpResourceTool`/`ListMcpResourcesTool` (§1.4/§3.3). O shape testado é o do Matcher; o do Classifier difere só por `Grep` (built-in base, ortogonal à visibilidade dos built-ins de resource — não afeta o resultado).
- **Gate `policy://examples` existe + semeado** — o resource (PR autônomo, §10.5(7)) deve existir e conter ≥2 exemplares LGPD antes de Fase 1+ do Classifier. A Classifier impl ramifica do main com o resource já mergeado (evita a janela de 404 do G3).
- **Gate POL-000 vocab populado (G12)** — verificar que `policy://vocabularies` do POL-000 no estado atual tem os **três** vocabulários (`operation`, categorias, `lawful_basis`) com tokens suficientes para um smoke não-trivial. Se só categorias estiver populado, o smoke de Fase 5 forçaria `operation_type: null` em todo candidato (passa por shape, não exercita o caminho mapeável). Pré-condição: ou POL-000 cresce, ou Fase 5 usa fixture temporária.
- **Gate 6** — `sdk_tools_empty_list` (PR #67). Indireto: valida mecânica de `tools` em context restriction. Nota: o Classifier usa `tools=["Read","Grep","ReadMcpResourceTool","ListMcpResourcesTool"]` (não `[]`); o caso específico dos built-ins de resource é o **Gate resource access** acima (#48-b), não este.

### 10.4 DDs status

| DD      | Status                                                                                                  |
|---------|---------------------------------------------------------------------------------------------------------|
| DD-C1   | `changed_paths` (= DD-T05). **Aberta** — decisão coordinator/Triager; **Classifier neutro** (changed_paths fora do contrato, §2.1). Recomendação de análise: manter Glob-by-subagent (consistente com Triager v0.1.0 mergeada) vs pré-computado (emenda Triager 0.2.0 + coordinator §3.1). Ver §10.5. |
| DD-C2   | Vocab membership enforcement. **Fechada** via §3.3 — soft via system_prompt + null-on-miss, sem `Enum`. |
| DD-C3   | Output mechanism (Branch A vs B). **Fechada** via §1.4 + §4 — Branch B (`output_format` envelopado).     |
| DD-C4   | Shape de `structured_context`. **Fechada** via §3.1 — escalares `Optional[str]` required-nullable (`null` explícito em miss); listas `list[str]` default `[]`, sem `Optional[list]`; objeto-wrapper evita root-array e o eixo da DD-T16. |
| DD-C5   | Carimbo de versão de vocabulário. **Aberta** — deferida (§7.3).                                          |
| DD-C6   | `max_turns` (constante vs escala com N). **Aberta** — constante MVP não escala; backstop `error_max_turns`→escalação; fórmula deferida T11+ (§1.5, §8.4). |
| DD-C7   | Ratificação do shape `DetectorFinding`. **Aberta** — forward-ref até Detector spec (§2.1, §8.4).         |
| DD-C8   | `reasoning` field opcional. **Aberta** — deferida T11+ (§8.4).                                           |
| DD-C9   | Postura do Matcher sobre membership recebido + postura de validação do consumer. **Aberta** — forward-ref/obrigação à Matcher spec (§3.3, §7.1, §8.4). |
| DD-C10  | Few-shot positivo como camada 1 via `policy://examples`. **Fechada** (opção C) — exemplos vocab-token-bound seguem o vocabulário; autoridade por **analogia** a ADR-0005 D8 (que decide *regras*), formalizada como Decisão 9 no amendment do PR autônomo; §1.1, §5.1, §5.3, §10.5(7-8). |
| DD-C11  | Qualidade do few-shot carregado (cold-start + tool-result). **Cold-start fechado** via seed ≥2 (§10.5(7)); resíduo tool-result-vs-in-prompt **aberto** T11+ (§5.1, §8.4). |
| DD-C12  | Ordem/identidade input↔output. **Fechada** (G4) — contrato hard, verificação posicional no coordinator (§4.3, §9.3, §8.4). |

3 fechadas por design ratificado (DD-C2, DD-C3, DD-C4) + DD-C10 e DD-C12 fechadas nesta sessão + DD-C1 fora-de-contrato + DD-C11 cold-start fechado/resíduo aberto; abertas/deferidas: DD-C5, DD-C6, DD-C7, DD-C8, DD-C9, e o resíduo de DD-C11.

### 10.5 Companion edits e Provisões pendentes a outros docs

Catálogo de edits a aplicar fora desta spec após merge:

1. **`coordinator.md` §3.3 — patch consolidado da Fase 4 (não só `output_format`/`max_turns`).** O catálogo da rodada anterior listava apenas dois campos; o planning de implementação revelou que o patch ao skeleton §3.3 (linhas 112-147) é maior (G9). Conjunto completo a aplicar como um companion edit:
   - **✅ aplicado (C3):** `output_format={"type": "json_schema", "schema": ClassifierOutput.model_json_schema()}` (Branch B; DD-C3) agora declarado em `coordinator.md` §3.3.
   - **✅ aplicado (C3):** `max_turns=20` (DD-C6; ver §1.5 — constante generosa, não escala com N) declarado em `coordinator.md` §3.3.
   - **`POLICY_READER_CONFIG`** — confirmar/estabelecer o locus single-source da constante referenciada em §1.4 item 5 (G1): provável `coordinator/config.py`, importada por Classifier e Matcher, não redefinida. Carimbo de obrigação: a constante precisa de um único dono antes de Fase 3.
   - **Capture loop rico** — o skeleton atual é minimal; a Fase 4 implementa a discriminação `subtype` × `stop_reason` de §4.3 (incluindo `refusal` dentro de `subtype=success`) + `model_validate` + raise tipado + **verificação posicional de ordem/identidade** (G4, ver §4.3). A classe nova `SubagentContractViolation` mora junto das demais exceções tipadas do coordinator — locus provável `src/coordinator/errors.py` (pin equivalente ao do `POLICY_READER_CONFIG`); a confirmar/estabelecer na Fase 4.
   - **Lifecycle de `policy://examples` missing/empty** (G3) — garantir que o prompt e o capture tratam ausência do resource deterministicamente (degradação, não relaxamento).
   As notas de drift em §1.4 e §1.5 apontam para este item. **Estado (C3):** `output_format` + `max_turns` aplicados; `POLICY_READER_CONFIG` (locus single-source), capture loop rico e lifecycle de `policy://examples` **permanecem pendentes** (impl Fase 3/4).

2. **DD-C1 / DD-T05 — decisão coordinator/Triager, NÃO aplicar nesta spec.** Esta spec é neutra a DD-T05. A resolução afeta: (a) `architecture-overview.md` §5.2 (input do Triager); (b) `triager.md` §2.1/§2.4/§5.1 (modelo de descoberta de `changed_paths`) **se** a decisão for pré-computado — o que **emenda a Triager spec mergeada (0.1.0 → 0.2.0)**, custo não catalogado em `triager.md` §10.5(5), que só prevê a reversão do §5.2; (c) `coordinator.md` §3.1 (invocação do Triager). **Recomendação:** manter Glob-by-subagent (zero emenda ao Triager; §5.2 aplica como rascunhado) e catalogar a divergência Glob-vs-`scan_diff` como risco de proveniência a validar via smoke-test em T11+. Decisão a fechar em sessão coordinator/Triager, não nesta.

3. **`docs/specs/subagents/detector.md` (a autorar)** — ratificar `DetectorFinding = {file, line, rule_id, snippet, surrounding_context}` (arch §5.3) como output do Detector. Esta spec pina o shape como forward-ref (§2.1, DD-C7); a Detector spec confirma ou reconcilia contra a âncora arch §5.3.

4. **`docs/tasks.md` §Tasks T11+** — quando decompor, prever task(s) de implementação do Classifier:
   - `src/subagents/classifier/models.py` com `StructuredContext`/`ClassifiedCandidate`/`ClassifierOutput`.
   - `src/subagents/classifier/prompt.py` com o template de §5.1 (incluindo `<examples>` e o passo de carregamento do vocabulário).
   - `src/subagents/classifier/__init__.py` com `spec_version: str = "0.1.0"`.
   - Tests cobrindo §9.1–§9.4, incluindo o cross-check de ausência de hard-enum (§9.3) e o gate de resource access (§10.3).

5. **ADR-0012 retroativo (Milestone C)** — documentar a nuance de scoped access per-server vs per-resource do SDK Python (§3.3): registrar o server concede `ReadMcpResourceTool` sobre todos os resources daquele server, e a fronteira Resource-vs-Tool se sustenta em nível de capability (sem tools decisionais no allowlist), não de resource.

6. **`docs/specs/subagents/matcher.md` (autorada #48) — obrigação de membership + postura de validação (DD-C9): cumprida.** (a) **Fora-de-vocabulário** (`operation_type`/`data_categories` com token inválido) → o motor `policy-reader` **rejeita hard** (`INVALID_DATA_CATEGORY`/`INVALID_OPERATION`, `tools.py:263-279`) antes do matching; o Matcher não resolve silenciosamente (matcher §2.2/§6.6). Caso **distinto** de **no-clause-match** (token válido, nenhuma cláusula substantiva governa) → `not_applicable` + `requires_human_review` (lacuna de cobertura, graciosa — DD-M8; **não** validação hard, que reintroduziria o anti-padrão removido do Reporter §4.8; **não** `indeterminate`, que exigiria `prescribed_treatment` inexistente na lacuna). (b) postura de validação Pydantic do consumer: `extra="ignore"` no recebido + projeção rename+drop, `extra="forbid"` no enviado à tool (matcher §2.3, DD-M11) — adicionar campo no Classifier permanece minor não-breaking (ver §7.1).

7. **`docs/specs/policy-reader/canonical.md` — novo resource `policy://examples` (DD-C10). PR autônomo, prereq de merge desta spec.** Confirmado: o policy-reader hoje expõe 3 resources (`canonical.md:13`: catalog, schema-version, vocabularies); arch §5.4 lista só `vocabularies` consumido pelo Classifier; CLAUDE.md status "3 of 3". Logo este resource **não existe** — esta spec o propõe a montante do owner. Decisão de sequenciamento (ratificada): `policy://examples` vira **PR autônomo** (policy-reader §3 + lista de consumidores §3.3 + amendment ADR-0005 criando **Decisão 9** "examples as layer-1 resource, by analogy to D8" + SCHEMA §2, item 8) que **merge antes**; a Classifier spec/impl ramifica do main corrigido. Mergear a Classifier impl assertando resource inexistente é o anti-padrão PR-mista (companion debt grande, não cosmético — per `git-conventions.md`). **Obrigação concreta com piso (fecha o gap de cold-start, M1/L1):** o PR de `policy://examples` deve **semear LGPD com ≥2 exemplares positivos** — exatamente os dois positivos removidos do §5.1 na rodada 2 (caso de *collection* e caso de *storage com transformação declarada*), agora como dado de camada 1. Isso preserva **paridade de cold-start** com a rodada 1 (não troca sistema-funcional por promessa). Shape provisório por exemplo: `{snippet, surrounding_context, expected_structured_context}`; formato canônico é decisão do policy-reader spec. **Semântica de erro distinta de `vocabularies`** (§6.2): missing/empty para a jurisdição é tolerado (degradação para disciplina-only), não erro de boot.

8. **`policy/SCHEMA.md` §2 — novo artefato de camada jurisdicional `examples/<framework>/` (DD-C10).** Adicionar ao layout um diretório irmão de `vocabularies/<framework>/` sob a **camada jurisdicional per-cliente** (§2.1), contendo os exemplos de mapeamento da jurisdição. Trocar a Política (LGPD→GDPR) troca os exemplos junto com os vocabulários, zero `src/` — materializa RF-008 na dimensão de few-shot. **ADR-0005 D8 decide o caso das *regras de detecção*** (`mcp_servers/semgrep_runner/rules/` permanece camada 2: expertise de projeto, per-cliente deferido); o caso dos *examples* é decidido pela nova **Decisão 9** do amendment (item 7), **por analogia** ao princípio de D8 — não por D8 diretamente. A fronteira (statute-bound-data vs detection-expertise) é a mesma; examples caem no lado statute-bound (vocab-token-bound), regras no lado expertise.

### 10.6 Defense candidates emergentes desta sessão

Material para o Capítulo de Método do TCC (consolidação em entry de learning-log da sessão #45):

1. **Cross-doc falsifica inferência de revisor em tempo real (refinamento do defense candidate #4).** O fechamento de DD-C1 em "pré-computado" foi sustentado por um argumento de blast-radius (três subagentes sem `Glob`) que a leitura verbatim de `triager.md` §2.1 derrubou — só o Triager consome `changed_paths`, e ele tem `Glob`. A inferência plausível-mas-falsa foi capturada por leitura direta antes de propagar para companion edits. Empírico: a falsificação veio da fonte, não de revisão de segunda ordem.
2. **Autorar a consumidora antes da produtora força clareza de contrato — e revela o que NÃO é contrato.** Inverter a ordem #37 (Classifier antes de Detector) forçou a constatação de que `changed_paths` está fora do contrato do Classifier, desacoplando DD-T05 da spec. O ganho de clareza foi negativo (o que sai do contrato), não só positivo.
3. **Required-nullable vs optional sob structured output (D4).** A distinção entre campo omitível e campo `null`-explícito é decisão de design de schema com consequência de auditoria — `required + nullable` materializa RF-003 ("null, não invenção") onde `optional + default` permitiria omissão silenciosa. Verificação contra doc oficial pós-cutoff mudou o shape (escalares sem default).
4. **Objeto-wrapper como mitigação de risco de grammar (D4).** Envolver a lista em `ClassifierOutput.classified` evita simultaneamente array-at-root e o eixo aberto da DD-T16 (oneOf/discriminator no nível raiz). Decisão de robustez ancorada em limites documentados de schema.
5. **Few-shot é conteúdo de prompt — e prompt herda a regra de camada.** O furo capturado nesta sessão: exemplos few-shot com tokens de jurisdição cravados no `system_prompt` (camada 2) violam a independência de camadas tanto quanto vocabulário hardcoded violaria, porque few-shot *é* prompt. A correção (DD-C10) separa o que é agnóstico (disciplina + miss-total, camada 2) do que é jurisdição-bound (mapeamentos positivos, camada 1 via `policy://examples`). Defense candidate: a fronteira de camada não para na instrução — alcança os exemplos. Distinção fina que o ADR-0005 já antecipava ao separar dado statute-bound (vocab, camada 1) de expertise de detecção (regras, camada 2): examples caem no primeiro grupo por serem vocab-token-bound, regras no segundo.
6. **Pureza vs pragmatismo: melhoria de "correção" pode regredir "funcionalidade concreta".** A migração de camada da rodada 2 (DD-C10) — arquiteturalmente correta — introduziu um custo escondido (cold-start sem positivos no MVP) e scope creep (resource novo + amendment de ADR). Capturado no review como "trocar sistema concreto-funcional por promessa-a-cumprir". Lição de método: melhoria de pureza precisa carregar junto a obrigação que preserva a funcionalidade que ela desloca (aqui, o seed ≥2). Defense candidate sobre disciplina de trade-off: a melhoria não está completa até a regressão que ela cria estar fechada com obrigação concreta, não condicional.

### 10.7 Side findings pendentes

- **`ReadMcpResourceTool` em runtime sob lockdown.** A spec assume que registrar `policy-reader` em `mcp_servers` + listar apenas `ListMcpResourcesTool`/`ReadMcpResourceTool` no allowlist concede acesso de leitura ao resource **sem** conceder as tools de ação. Confirmado conceitualmente por `coordinator.md` §3.3 (nota de scoped access) e ADR-0005 D4; confirmação empírica deferida ao "Gate resource access" (§10.3).
- **`policy://schema-version` como insumo de DD-C5.** Se a decisão de carimbar versão de vocabulário reabrir, o resource já está acessível ao Classifier (per granularidade per-server); custo é só de shape + prompt, não de capability.
- **`surrounding_context` sem budget (G6) — forward-ref à Detector spec.** O shape do `DetectorFinding` (arch §5.3) não limita `surrounding_context`. Multiplicado por N + leituras `Read` redundantes, infla o context window. Não é decisão do Classifier (é do Detector / do `build_classifier_prompt`), mas registra-se a obrigação: ou a Detector spec limita o campo, ou `build_classifier_prompt` pré-trunca. Paralelo ao forward-ref do Matcher em §3.3.
- **Audit trail turn-by-turn (G7).** `03-classifier.json` captura o output final, mas `permission_mode="dontAsk"` + retries internos + refusal são audit-relevantes (artefato de pesquisa, banca). Captura de trace (tool_use/tool_result por turn, retries disparados) é provável concern do coordinator — esta spec referencia o locus mas **não confirmei** que `coordinator.md` cobre persistência de trace. A confirmar; se não cobre, é gap a levantar no coordinator.
- **Formato do conteúdo de `policy://vocabularies` / `policy://examples` (G8).** O prompt §5.1 diz "use os valores carregados" mas o modelo precisa parsear o que vier. Se for YAML denso multi-nível, a extração de tokens pode ser frágil. Fase 0 inspeciona (G12); se o conteúdo for difícil, a decisão é prompt-side (schema hint: "procure a chave X sob Y") vs resource-side (view simplificada) — compartilhada com o `policy-reader`, não do Classifier sozinho.
- **Refusal / falha → o que vai pro GitHub Action (G11).** §4.3 levanta `SubagentRefusedTask` / `SubagentValidationFailed` / `SubagentContractViolation`; o coordinator decide o reporting. "No fabricated certainty" pede Report com `run_outcome="error"` (não silêncio, não falso-verde). O mapeamento erro→Report é concern do coordinator + Reporter spec; esta spec referencia o locus, não o decide.
