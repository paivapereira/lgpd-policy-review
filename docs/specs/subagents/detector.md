# detector

**spec_version**: 0.1.0

> Spec leve do subagent Detector. Segue a estrutura de `classifier.md` v0.1.0, `reporter.md` v0.4.0 e `triager.md` v0.1.0 como template hipótese (a destilação formal de `_template-subagent.md` permanece Fase 2, não materializada). Decisões de design ancoradas em `docs/architecture-overview.md` §5.3, `coordinator.md` §3.2/§3.3, `docs/specs/semgrep-runner/canonical.md` (tool `scan_diff`), `docs/REQUIREMENTS.md` (RF de detecção — ver §1.2), ADR-0001, ADR-0002 e ADR-0010. Autorada na work-session **#46** (continuação natural da inversão #37: Classifier autorado primeiro como consumidor, Detector agora como produtor). Esta spec **ratifica** o `DetectorFinding` que a Classifier pinou como forward-ref (DD-C7) contra a âncora arch §5.3; onde diverge, reconcilia explicitamente (ver §3). Esta spec **não decide DD-T05** (`changed_paths`): o Detector opera de `base_ref`/`head_ref` via `scan_diff` e é neutro a `changed_paths` (ver §2.2, §8.1, §10.4).
>
> **Verificação externa (work-session #46).** Os fatos de SDK/MCP/Semgrep desta spec foram conferidos contra documentação oficial vigente (spec MCP 2025-11-25; docs do Agent SDK; docs do Semgrep) por estarem além do cutoff de conhecimento Jan/2026. Achados materiais codificados: convenção canônica `isError:true` para tool errors e o desvio deliberado do projeto (Option B, ADR-0002); fricção `isError`+`outputSchema` confirmada persistente em 2026; forma envelopada do `output_format`; precedência de refusal sobre schema; existência do MCP oficial do Semgrep (content-based, não diff-over-refs — ver §8.4).

## 1. Identidade e propósito

### 1.1 Nome canônico

`detector`. Subagent. Não é MCP server, não expõe resources, não expõe tools customizadas. **Consome** a tool `scan_diff` do MCP server `semgrep-runner` (`docs/specs/semgrep-runner/canonical.md` §4.2) — único subagente autorizado a consumir esse servidor (`semgrep-runner` canonical §1, "Consumidores autorizados"). Usa `Read` para inspeção complementar do código em torno de cada finding (geração de `surrounding_context`, ver §3.4).

### 1.2 Função

Identifica **pontos de tratamento candidatos** em um diff de pull request. Para os refs `base_ref`/`head_ref` do PR, invoca `scan_diff`, e para cada finding retornado emite um registro estruturado com localização, regra disparada, snippet e contexto circundante. Output: lista de candidatos `[{file, line, rule_id, snippet, surrounding_context}]` envelopada com a provenance do scan (shape concreto em §3).

Materializa **RF-001 — "Detecção de coleta de dados pessoais"** (`docs/REQUIREMENTS.md:15-24`). **RF-002** ("Cobertura de identificadores brasileiros: CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde", `docs/REQUIREMENTS.md:28-37`) **não** é responsabilidade da Detector spec — é requisito de cobertura do **rule set curado pelo `semgrep-runner`** (mais o `data_categories` emitido pelo Classifier, RF-002 critério ~linha 35); herdado, não materializado aqui. A capacidade externa observável de RF-001 é a presença da lista de candidatos (possivelmente vazia) com os cinco campos por candidato, consumível pelo Classifier downstream. (Padrão idêntico ao `classifier.md` §1.2, que cita RF-003 verbatim em `docs/REQUIREMENTS.md:41`. Frase canônica confirmada verbatim #46 — critério RF-001 (`docs/REQUIREMENTS.md:22`): "o Report final carrega ao menos um finding apontando essa linha como ponto de coleta candidato, com `rule_id` identificando o reconhecedor disparado e `file`/`line`/`snippet` preenchidos".)

A fronteira load-bearing: **o Detector localiza possibilidade, não decide violação.** A separação "detecta possibilidade vs avalia conformidade" é o que o separa do Matcher (`docs/architecture-overview.md` §5.3). Sem acesso ao `policy-reader`, o Detector é fisicamente impedido de "adivinhar" cláusulas aplicáveis e contaminar o output com pré-julgamento (arch §5.3, linha citada verbatim em §8.3).

### 1.3 Posição na arquitetura

**Etapa 2** do pipeline do coordinator (`coordinator.md` §3.2, "Etapa 2 — Detector"; numbering 1-based incluindo Triager: Triager=1, Detector=2, Classifier=3, Matcher=4) — equivalente à **Etapa 1** do fluxo de `docs/architecture-overview.md` §3 ("Etapa 1 — Detector"; numbering pós-Triager). A dualidade é herdada das duas fontes; ambas designam o mesmo estágio: invocado após o Triager decidir `proceed`, antes do Classifier. O Classifier consome o output do Detector (`classifier.md` §2.1).

Tools permitidas: built-in `Read` (sobre arquivos do diff) **mais** a tool MCP `scan_diff` do `semgrep-runner`. Sem `Glob`, sem `policy-reader`, sem `Grep`, sem `Write`/`Edit`/`Bash`. Matriz canônica em `docs/architecture-overview.md` §5.7 (tabela "Matriz tools × subagentes", linhas ~219-231 — confirmado: Detector tem `tools=["Read"]`, `allowed_tools=["Read", "mcp__semgrep-runner__scan_diff"]`, `mcp_servers={"semgrep-runner": ...}`).

> 💡 **Conceito Claude relevante (Domínio 2 — Tool Design & MCP Integration, Task Statement 2.3).** Scoped tool access: o Detector recebe só as tools do seu papel (`Read` + `scan_diff`). A ausência de `policy-reader` no inventário **é** o firewall epistêmico — não é economia de tokens, é impossibilidade física de pré-julgamento. Distinção load-bearing da prova: `tools` (built-in availability — aqui `["Read"]`) vs `allowed_tools`/allowlist (denial-on-miss, onde entra `mcp__semgrep-runner__scan_diff`); a tool MCP é habilitada por `mcp_servers`, não pelo campo `tools`. Espelha o pattern "Read-only analysis" da tabela de combinações canônicas (`agent-sdk`), aqui estendido com uma tool MCP de domínio.

### 1.4 Output format e governança

Branch B (output_format, sem custom tool — ver §4). O `output_format` do Detector emite o envelope `DetectorOutput` (§3.2).

`max_turns` provisional. Aritmética do trabalho do Detector: 1 chamada `scan_diff` + N leituras `Read` (uma por finding, para `surrounding_context`) + 1 emissão final ≈ **2 + N turns**. Um cap constante implica um **threshold**: PRs com N acima de ~(cap − 2) degradam para `error_max_turns` → `SubagentUnresponsive` (§6.4) → escalação pelo coordinator. **Isso é o backstop desejado** para isolar PRs patológicos, não falha silenciosa nem output parcial. Valor provisional sugerido: **`max_turns=30`** (headroom para ~28 candidatos antes do backstop; o Detector faz 1 `Read`/finding, perfil de turns mais leve que o Classifier que faz `Read`+`Grep`/candidato e usa `20`). O valor **30 é provisional** (judgment do autor; declarado no skeleton coordinator §3.2 — C3), ratificável em T11+ contra catálogo de PRs com N grande; o que **não** vale é deixar implícito que um cap baixo "é seguro" para N grande. Floor calibrado em T11+ contra catálogo de PRs com N grande (measure-before-tune). `max_budget_usd` disponível como cap complementar, não exercitado no MVP. **Nota de drift — ✅ aplicado (C3):** `output_format` (envelope `DetectorOutput.model_json_schema()`) e `max_turns=30` do Detector estão agora declarados no skeleton de `coordinator.md` §3.2 (stage Detector); a `build_detector_prompt(pr_metadata, triager_output)` já existia e foi mantida (§2.3). Companion edit §10.5(1) fechado quanto a esses dois campos.

Governança: ADR-0001 (stack canônica), ADR-0002 (convenções MCP — relevante porque o Detector consome `scan_diff` sob Option B; ver §6.2), ADR-0010 (estratégia de instalação Semgrep, locus adjacente ao gap build-vs-reuse de §8.4). Companion-spec'd por `coordinator.md` §3.2 (skeleton de invocação do Detector) e §3.3 (`build_detector_prompt`), e por `docs/specs/semgrep-runner/canonical.md` (contrato da tool consumida).

### 1.5 Grammar compilation latency

`output_format` configurado num schema compilável; doc de **nível API** (`build-with-claude/structured-outputs`) reporta que grammars compiladas são cacheadas por 24h a partir do último uso. Implicação para CI workers efêmeros: primeiro PR após cold start pode pagar a compilação. Não-bloqueante; possível warm-up futuro. Mesma consideração de `classifier.md` §1.5 / `triager.md` §1.5.

> **Incerteza registrada (escopo incerto — work-session #46).** A doc de nível API descreve constrained decoding via grammar; a doc do Agent SDK descreve `output_format` como validação pós-hoc com re-prompt (subtype `error_max_structured_output_retries` em exaustão). Não está resolvido na doc se o `output_format` do SDK usa a grammar por baixo (constrained) ou é retry-puro (validação + re-prompt). **Esta spec não afirma o mecanismo — só importa a consideração de cache 24h, herdada da Classifier.** Se um smoke-test futuro mostrar que o SDK é retry-puro, a nota de grammar latency desta spec **e** de `classifier.md` §1.5 precisa de ajuste cross-doc (não estão erradas hoje; ancoram em doc de nível API).

## 2. Input contract

### 2.1 Shape do input

O Detector recebe os refs do PR sob análise. **`DetectorInput` abaixo é tipo notacional** para clareza desta spec — **não** é objeto validado em runtime: o Detector é Branch B e **não** valida input via Pydantic (não há `DetectorInput.model_validate(...)` em lugar nenhum; comparar com a ausência de `ClassifierInput` Pydantic análogo). Em runtime, o Detector recebe um **prompt string** construído pelo coordinator a partir de `pr_metadata` (ver §2.3). Shape notacional dos refs, ancorado em `docs/architecture-overview.md` §5.3:

```python
class DetectorInput(BaseModel):
    base_ref: str   # Git ref baseline (provável merge-base PR↔target)
    head_ref: str   # Git ref do estado atual do PR a escanear
```

Estes refs são repassados verbatim como argumentos de `scan_diff` (`semgrep-runner` canonical §4.2). O Detector **não** resolve refs, não computa merge-base, não valida existência de ref antes da chamada — isso é responsabilidade de pré-invocação do caller (coordinator) e/ou tratado pelo `scan_diff` via `GIT_REF_NOT_FOUND`/`INSUFFICIENT_GIT_HISTORY` (ver §6.2).

### 2.2 Ausente do input — `changed_paths`

O Detector **não** recebe nem consome lista de paths alterados. Opera dos refs via `scan_diff`, que executa o diff-aware scan internamente (`--baseline-commit`, `semgrep-runner` canonical §2.2). Consequência de contrato: **DD-T05 (`changed_paths` no scope compartilhado) é ortogonal ao Detector** — sua resolução (coordinator pré-computa vs Triager descobre via `Glob`) não toca esta spec. Registrado, não reaberto (ver §10.4, DD-T05). Idêntico em postura ao Classifier (`classifier.md` §2.1, "Ausente do input — `changed_paths`").

### 2.3 Construção do prompt pelo coordinator

O coordinator constrói o prompt da `query()` chamando `build_detector_prompt` definido em `coordinator.md` §3.3 (locus canônico autoritativo). **A função já existe no skeleton** com signature `build_detector_prompt(pr_metadata, triager_output)` (`coordinator.md` ~linha 94) — **não** é "a criar". Implicação de reconciliação: `base_ref`/`head_ref` chegam via `pr_metadata` (estado top-level do run), **não** via um `DetectorInput` separado (que é notacional, §2.1). O companion edit (§10.5) é *reconciliar a signature existente* + confirmar que `pr_metadata` carrega os refs — não criar a função.

```python
# Pseudocódigo do coordinator (autoritativo: coordinator.md §3.3)
prompt = build_detector_prompt(pr_metadata, triager_output)  # refs vêm de pr_metadata
async for msg in query(prompt=prompt, options=detector_options):
    ...  # coordinator inspeciona o stream (ver §6.2)
```

### 2.4 Princípio: Detector localiza, não julga

O Detector opera sobre o resultado sintático do `scan_diff` e sobre o código local (via `Read`). Não consulta a Política, não avalia aplicabilidade de cláusula, não emite veredito. O `rule_id` e o `snippet` são localizadores; o `surrounding_context` é material descritivo para o Classifier downstream extrair `structured_context`. Confundir localização com avaliação reintroduziria o acoplamento código↔política que a arquitetura separa deliberadamente (**RF-008** — "Substituição de framework jurisdicional sem alteração de código", `docs/REQUIREMENTS.md:110`, confirmado verbatim #46; arch §5.3). Esta fronteira é o invariante load-bearing protegido por toda a spec (ver §3.3, §8.3).

## 3. Output contract

> Esta seção é o keystone da spec. Codifica DD-D1 (ratificação do shape + mapeamento strip-opinion/keep-provenance), DD-D2 (budget de `surrounding_context`) e DD-D3 (envelope + placement da provenance). Ver §10.4 para o estado das decisões.

### 3.1 Shape do candidato — `DetectorFinding` (DD-D1)

Shape de cada candidato, ancorado verbatim em `docs/architecture-overview.md` §5.3 e idêntico ao pinado pela Classifier (`classifier.md` §2.1, DD-C7 — **ratificado aqui sem divergência**):

```python
class DetectorFinding(BaseModel):
    file: str                 # path relativo ao repo
    line: int                 # linha do ponto de tratamento candidato
    rule_id: str              # identificador da regra Semgrep que disparou
    snippet: str              # trecho do código/payload
    surrounding_context: str  # contexto além das linhas do snippet (ver §3.4)
```

> **Ratificação da forward-ref (fecha DD-C7 da Classifier).** A Classifier pinou este shape como provisão de proveniência preventiva, declarando que a Detector spec o ratificaria ou reconciliaria contra arch §5.3. **Ratificado verbatim, sem reconciliação necessária** — os cinco campos batem. O Classifier consome este shape como input (`classifier.md` §2.1) e enriquece com `structured_context`; sua verificação posicional de passthrough (G4, `classifier.md` §9.3) checa `{file, line, rule_id, snippet}` — `surrounding_context` é gerado pelo Detector (§3.4) e não está no invariante de identidade posicional do Classifier (registrado para evitar drift "Classifier mutou meu campo": o campo viaja, mas não é passthrough-identity-checked downstream).

### 3.2 Envelope de saída — `DetectorOutput` (DD-D3)

O Detector emite um **envelope**, não uma lista nua:

```python
class ScanProvenance(BaseModel):
    rules_version: str        # versão do rule set curado (semgrep-runner §6)
    semgrep_version: str      # versão do binário Semgrep (semgrep-runner §6)
    scan_metadata: ScanMetadata  # base_ref, head_ref resolvidos, files_scanned, elapsed_seconds

class DetectorOutput(BaseModel):
    findings: list[DetectorFinding]
    provenance: ScanProvenance
```

**Decisão (DD-D3): provenance é per-scan, no nível do envelope — não per-finding.** Provenance é propriedade do **scan inteiro**: `rules_version`, `semgrep_version` e `scan_metadata` são idênticos para todos os findings de uma invocação, então pertencem ao envelope. Per-finding seria semanticamente errado — sugeriria `rules_version` distinto entre findings do mesmo scan, falso por construção. Distinta também, em propósito e granularidade, da **Trinca de provenance** policy/legal que o projeto preserva per-finding (`coordinator.md:174`: `policy_schema_version`, `policy_version`, `legal_framework`) — aquela é jurídico-temporal per-finding; esta é de execução de scan per-scan.

`ScanProvenance` espelha as três chaves de provenance do `scan_diff` (`semgrep-runner` canonical §6): `rules_version` e `semgrep_version` (provenance estática top-level) + `scan_metadata` aninhado (provenance dinâmica por-scan). O Detector **repassa** esses campos do output do `scan_diff` para o seu envelope sem transformação.

> 💡 **Conceito Claude relevante (Domínio 5 — Context Management & Reliability).** Provenance/citations: o envelope preserva a cadeia de auditoria que o `semgrep-runner` §6 estabelece — "este finding foi gerado pela regra X (rule set Y) por Semgrep Z sobre o diff A→B". Dropar a provenance no boundary Detector→Classifier mataria essa cadeia para o Reporter downstream. Carregar num envelope per-scan e roteá-la ao locus de auditoria é o pattern; per-finding seria duplicação ruidosa (e estouro do context window com N cópias idênticas).

### 3.3 Mapeamento `scan_diff` → `DetectorFinding` (DD-D1: strip-opinion / keep-provenance)

O finding emitido pelo `scan_diff` é mais rico que o `DetectorFinding` (`semgrep-runner` canonical §8.1): carrega `{rule_id, rule_severity, rule_message, location{path, start_line, start_col, end_line, end_col}, snippet}`. A transformação para `DetectorFinding` **não é passthrough** — é governada pelo princípio:

> **Princípio do boundary do Detector: strip-opinion, keep-provenance.** O Detector descarta a *opinião de detecção* do Semgrep e preserva a *proveniência* do Semgrep.

Mapeamento per-finding (`scan_diff` finding → `DetectorFinding`):

| Campo do `scan_diff` finding | Destino no `DetectorFinding` | Tratamento |
|---|---|---|
| `location.path` | `file` | renomeado/achatado |
| `location.start_line` | `line` | achatado (descarta `start_col`, `end_line`, `end_col`) |
| `rule_id` | `rule_id` | passthrough |
| `snippet` | `snippet` | passthrough |
| `rule_severity` | — | **descartado** (opinião de detecção) |
| `rule_message` | — | **descartado** (opinião de detecção) |
| (gerado pelo Detector) | `surrounding_context` | **adicionado** via `Read` (§3.4) |

Elevação de provenance per-scan (envelope `scan_diff` → `DetectorOutput`, **não** per-finding):

| Campo do envelope `scan_diff` | Destino | Tratamento |
|---|---|---|
| `rules_version` / `semgrep_version` / `scan_metadata` | `DetectorOutput.provenance` | **preservado** no envelope (§3.2), repassado verbatim |

Justificativa do descarte de `rule_severity` e `rule_message`: são o pré-julgamento de detecção do Semgrep (severidade da regra, mensagem "possível tratamento de CPF detectado"). Carregá-los downstream contaminaria o output com framing de detecção — viola o firewall epistêmico de §1.2/§2.4/§8.3 (arch §5.3, "fisicamente impedido de contaminar o output com pré-julgamento"). A severidade de **conformidade** é derivada downstream pelo Matcher contra a Política, não herdada da severidade da **regra Semgrep**. DD-D1 não é decisão nova: é a articulação principista do que arch §5.3 já normatiza.

### 3.4 `surrounding_context`: geração e budget (DD-D2)

**Geração.** Para cada finding, o Detector usa `Read` sobre `file` numa **janela simétrica** em torno de `line` (±N linhas), produzindo `surrounding_context` como o texto dessa janela. Propósito: dar ao Classifier downstream material para extrair `structured_context` (imports, definições de função, declarações de base legal em comentários/docstrings próximas) sem que o Classifier precise re-`Read` o arquivo na maioria dos casos.

**Budget — bound no produtor (Detector).** O `surrounding_context` é limitado **no Detector**, não truncado downstream em `build_classifier_prompt`. Razão: o pattern do projeto é producer-bounded output — Triager, Classifier e Reporter emitem shapes Pydantic-validados onde o bound é responsabilidade do produtor. Truncar no consumer introduziria assimetria inédita e empurraria o concern para downstream (qualquer consumer alternativo futuro teria que re-implementar o truncamento). Fecha o forward-ref G6 catalogado em `classifier.md` §10.7 ("Side findings pendentes": "surrounding_context sem budget (G6) — forward-ref à Detector spec", confirmado verbatim #46).

**Critério de calibração de N (não "tune depois" abstrato).** N vive numa banda:
- **Floor:** menor janela que deixa o Classifier extrair `structured_context` (`operation_type`, `data_categories`, `declared_legal_basis`) **sem** disparar `Read` adicional na maioria dos casos. Janela pequena demais força re-leitura → mais turns/custo no Classifier.
- **Ceiling:** orçamento de tokens do prompt do Classifier. Janela grande demais × N infla o prompt downstream (risco lost-in-the-middle no Classifier).

N é **provisional** no MVP, calibrado em T11+ sobre o catálogo de PRs sintéticos (measure-before-tune, mesmo padrão do `max_turns`). **Valor inicial proposto: ±10 linhas** (janela simétrica em torno de `line`) — baseline concreto para T11+ ter o que medir, não delegação 100% ao futuro. A banda floor/ceiling é o **contrato**; ±10 é o **ponto de partida** da calibragem, ajustável por evidência (se o Classifier dispara `Read` adicional com frequência → subir; se o prompt do Classifier infla → descer).

> 💡 **Conceito Claude relevante (Domínio 5 — Context Management & Reliability).** Trade-off de janela de contexto explicitado: bound no produtor com banda floor/ceiling resolve de forma principista a tensão entre janela pequena (força re-leitura, mais turns) e janela grande (infla prompt downstream, lost-in-the-middle). Melhor material de defesa que um número mágico.

### 3.5 Desempacotamento pelo coordinator

O coordinator desempacota o `DetectorOutput`:
- `findings: list[DetectorFinding]` → passado ao Classifier. **O input contract do Classifier permanece `list[DetectorFinding]`** (`classifier.md` §2.1), intacto — o envelope é desempacotado antes, o Classifier não vê `provenance`.
- `provenance: ScanProvenance` → persistido no scratchpad `02-detector.json` (gravado pelo coordinator, §4) **e** repassado ao Reporter para citação na cadeia de auditoria do Report final.

**Invariante de boundary (coordinator).** O `DetectorOutput` é desempacotado pelo coordinator **antes** da invocação do Classifier. O Classifier consome `list[DetectorFinding]` puro (`classifier.md` §2.1); passar o envelope inteiro ao Classifier é **contract violation do coordinator** (não do Detector). Isto não é descritivo — é load-bearing: o Classifier roda `ConfigDict(extra="forbid")` nos modelos de **output** (`classifier.md:127,134,145`, confirmado #46 — ver §7.1), então o envelope vazado a montante não tem locus válido e o pipeline quebra. O invariante "coordinator desempacota antes" é o que protege o contrato.

**Forward-ref ao Reporter (DD-D3) — Resolvido (C2/Opção B).** O Reporter **0.5.0** carrega `scan_provenance` top-level opcional (`reporter.md` §3/§4.3), de mesma model que `DetectorOutput.provenance`; o coordinator roteia `DetectorOutput.provenance` ao estado consolidado / prompt do Reporter (`coordinator.md` §3.2/§3.5). Contexto histórico: o `ReportPayload` pré-0.5.0 carregava só a Trinca policy/legal (`policy_schema_version`/`policy_version`/`legal_framework`) per-finding; a adição foi um **minor bump da spec do Reporter** (0.4.0 → 0.5.0) que fechou este débito antes da implementação T11+. Aceitar lista pura (sem envelope) quebraria o pattern de provenance trickle-down e mataria o trinque de auditoria de `semgrep-runner` §6.

### 3.6 Lista vazia é caso válido, não erro

Quando `scan_diff` retorna `findings: []` (diff não introduziu candidatos detectáveis — sucesso, `semgrep-runner` canonical §8.2), o Detector emite `DetectorOutput(findings=[], provenance=...)`. **Não é erro.** Propaga ao Classifier → Matcher → Reporter; o coordinator não tem branching condicional para esse caso (`coordinator.md:110`: "zero candidatos é caso válido; `findings: []` propaga ao Classifier → Matcher → Reporter" — verbatim). Crítico: este caso **não pode** ser aliasado com erro de scan (ver §6.2).

### 3.7 Casos que parecem erro mas não são

- **`findings: []` com provenance presente.** Scan rodou, zero candidatos. Válido (§3.6).
- **`surrounding_context` capturando código não relacionado ao finding.** Não é erro — a janela é sintática (±N linhas), não semântica; o Classifier reconcilia.
- **Mesmo PR re-escaneado retorna `surrounding_context` idêntico mas findings em ordem distinta.** `scan_diff` garante ordem estável por `(location.path, location.start_line)` ascendente (`semgrep-runner/canonical.md:150`, "ordem estável entre invocações"); o Detector preserva essa ordem. Divergência de ordem seria contract violation (§6), não caso normal.
- **`data_categories` futuro do Classifier diverge do `rule_id` do Detector.** Não é erro do Detector — `rule_id` é heurística sintática; categorização é downstream (`classifier.md` §3.4).

## 4. Output mechanism

> Análogo Branch B de §4 do Reporter ("Tool `emit_report`"). Detector opera em Branch B (output_format), sem tool customizada. Asymmetry deliberada, paralela a `triager.md` §4 e `classifier.md` §4.

### 4.1 Não há custom tool

O Detector **não** define `@tool`, **não** instancia `create_sdk_mcp_server`, **não** registra MCP server in-process. Output emitido nativamente via runtime do SDK quando o modelo produz texto que valida contra o schema de `output_format` (o envelope `DetectorOutput`). O `semgrep-runner` registrado em `mcp_servers` é server **out-of-process** consumido como tool (`scan_diff`) — não é o mecanismo de output.

### 4.2 Mecânica do output

1. Coordinator chama `query(prompt=..., options=detector_options)` com `output_format` configurado para `DetectorOutput`.
2. Modelo invoca `scan_diff(base_ref, head_ref)` via a tool MCP (um `ToolUseBlock` `mcp__semgrep-runner__scan_diff` + seu `ToolResultBlock`). Namespace com hífen confirmado no allowlist (`coordinator.md:98`) e justificado canônicamente (`coordinator.md:415`: servers existentes `policy-reader`/`semgrep-runner` mantêm hífen).
3. Para cada finding, modelo emite `ToolUseBlock`s `Read` (janela de `surrounding_context`) + `ToolResultBlock`s.
4. Quando o modelo emite texto parseável e validável contra o schema de `DetectorOutput`, o agentic loop encerra e o SDK emite `ResultMessage` com `subtype="success"` e `structured_output` populado.
5. Se o JSON falha validação, o SDK injeta retry transparentemente (não visível como turn explícito).
6. Se retries esgotam, o SDK emite `ResultMessage` com `subtype="error_max_structured_output_retries"` (tabela §6.3).

### 4.3 `output_format` — forma wire

`output_format={"type": "json_schema", "schema": DetectorOutput.model_json_schema()}` — forma envelopada, **confirmada empiricamente** no smoke-test do projeto (`reporter.md` §10.6, SDK 0.2.87) e **verificada corrente** na doc oficial do Agent SDK (work-session #46). Não é a forma nua. Herdada verbatim, não inferida.

### 4.4 Scratchpad

O coordinator grava `02-detector.json` (output desempacotado: findings + provenance) no scratchpad da run, para audit trail e consumo pelo Classifier/Reporter. O Detector é stateless e não persiste (§7.4); a persistência é do coordinator (§3.5). Convenção confirmada (`coordinator.md:84,108,137,172`: `01-triager.json` / `02-detector.json` / `03-classifier.json` / `04-matcher.json`).

## 5. System prompt

### 5.1 Estrutura

O system prompt do Detector instrui (esqueleto; texto final destilado na implementação T11+):

1. **Papel e fronteira.** "Você localiza pontos de tratamento candidatos num diff. Você NÃO decide se há violação, NÃO consulta política, NÃO emite veredito."
2. **Procedimento.** Invocar `scan_diff(base_ref, head_ref)`; para cada finding retornado, `Read` a janela de ±N linhas em torno de `location.start_line` em `location.path` para compor `surrounding_context`; emitir o envelope `DetectorOutput`.
3. **Mapeamento strip-opinion (§3.3).** "NÃO carregue `rule_severity` nem `rule_message` para o output. Use `location.path`→`file`, `location.start_line`→`line`."
4. **Regra de não-fabricação (immutable; §6.2).** "Se `scan_diff` retornar erro (campo `errorCode` presente), NÃO invente findings, NÃO emita `findings: []` como se o scan tivesse rodado limpo. Reporte que o scan falhou." Costura no immutable rule de `CLAUDE.md` ("No fabricated certainty").
5. **`<examples>`.** Few-shot (§5.2).

### 5.2 Few-shot examples (behavior anchors)

Três exemplares cobrindo classes distintas (padrão few-shot do projeto, 3-5 exemplares com `<example>` XML; `classifier.md` §5.1, `triager.md` §5):

- **Exemplo A — caso normal.** `scan_diff` retorna 2 findings em arquivos distintos → Detector `Read` o contexto de cada → emite `DetectorOutput` com 2 `DetectorFinding` + provenance. Demonstra o mapeamento (severity/message ausentes do output) e o envelope.
- **Exemplo B — empty result.** `scan_diff` retorna `findings: []` → Detector emite `DetectorOutput(findings=[], provenance=...)`. Demonstra que vazio é válido, não erro, e que provenance ainda é emitida.
- **Exemplo C — scan com erro.** `scan_diff` retorna envelope com `errorCode` (ex.: `SCAN_TIMEOUT`) → Detector **não** fabrica findings, **não** emite `findings: []` enganoso; sinaliza o estado de falha. Behavior anchor para a regra de não-fabricação (§6.2). Few-shot que contradiz o invariante seria sinal conflitante — este reforça.

> **Nota de fixtures (privacy-safety).** Os `snippet`/`surrounding_context` dos fixtures de few-shot e dos cenários de teste (incluindo o gatilho de refusal em §9.7) devem usar **CPF/CNPJ sintéticos** (`.claude/rules/privacy-safety.md`), que disparam as heurísticas de detecção/safety sem PII real. T11+ não improvisa com dados pessoais reais.

> 💡 **Conceito Claude relevante (Domínio 4 — Prompt Engineering & Structured Output).** Few-shot como behavior anchors particionando o espaço de comportamento (normal / vazio / erro). O Exemplo C é o mais load-bearing: ancora o reconhecimento prompt-level do erro do `scan_diff`, que é **forçado** porque o `scan_diff` opera sob Option B (wire `isError:false` sempre — §6.2). Sem esse anchor, o modelo veria o errorCode como sucesso e poderia fabricar.

## 6. Error handling

### 6.1 Estrutura canônica

Detector Branch B não tem envelope de erro customizado — diferente do Reporter (`reporter.md` §6.1, que emite erros via `emit_report` com `isError: true`). A propagação de erro acontece no coordinator. Idêntico em estrutura a `triager.md` §6.1 e `classifier.md` §6.1 — **com uma diferença material:** o Detector consome uma tool (`scan_diff`) que tem seu próprio envelope de erro (§6.2). Triager e Classifier não invocam tool de ação com envelope de erro de domínio.

### 6.2 Propagação de erro do `scan_diff` (DD-D5)

`scan_diff` usa **Option B** (`semgrep-runner` canonical §4.3/§5; ADR-0002): wire `isError: false` em **todos** os retornos — sucesso, empty result, e erros de domínio (business/system). Discriminação por **presença do campo `errorCode`** em `structuredContent`. Wire `isError: true` fica reservado para falhas de protocolo do FastMCP.

> **Por que Option B (contexto, não decisão desta spec).** ADR-0002 (linhas 151-205) registra Option B como desvio deliberado da convenção canônica MCP, motivado por FastMCP 3.2.4 não expor caminho público combinando `isError:true` + `structuredContent`, e nota que a tensão estrutural entre validação de `outputSchema` e inspeção de `isError` permanece intrínseca a qualquer SDK que valida `outputSchema` antes. **Verificação externa (work-session #46) confirma que essa fricção segue viva em 2026** (relatos de frameworks/gateways validando erroneamente respostas `isError:true` contra `outputSchema`). A convenção canônica MCP (spec 2025-11-25) é `isError:true` para tool execution errors, justamente para o modelo ver e recuperar — Option B é o trade-off do projeto, e a recomendação "não reverter" é coerente com o ADR. Esta spec **trabalha com** o contrato Option B do `scan_diff`; não o redecide.

**Consequência (DD-D5): o modelo do Detector vê o erro do `scan_diff` como tool result de sucesso no nível wire.** Não há exceção de runtime, não há `isError:true` de MCP. Portanto:

**Mecanismo de propagação — inspeção determinística do stream pelo coordinator.** O coordinator inspeciona o `ToolResultBlock` de `mcp__semgrep-runner__scan_diff` no message stream e discrimina por presença de `errorCode`. **Não é via nova nem mecanismo inédito — é o pattern de stream-inspection já ratificado do coordinator aplicado a um novo caso de uso.** Precedente: a passagem `ReportNotEmitted` no `coordinator.md` (enforcement via inspeção do message stream em Python, não via PostToolUse hook — decisão #37, ratificada #38) e a captura do payload do Reporter via inspeção de `ToolUseBlock` no stream. **Citado por âncora semântica, não por linha** (decisão de design #46): os dois reviews divergiram no número de linha do `ReportNotEmitted` — sinal de que linha nua drifta conforme o coordinator evolui; a referência canônica é a âncora semântica (`ReportNotEmitted` / captura de payload do Reporter). O projeto já decidiu duas vezes que sinal reliability-critical não deve depender do modelo discriminar.

Discriminação e roteamento pelo coordinator (por `errorCode` + `isRetryable`, `semgrep-runner` canonical §5):
- **`SCAN_TIMEOUT`** (system, `isRetryable: true`) → retry sob orçamento de retry do coordinator; sem findings parciais (`scan_diff` all-or-nothing, `semgrep-runner` §7).
- **`GIT_REF_NOT_FOUND`**, **`INSUFFICIENT_GIT_HISTORY`** (business, `isRetryable: false`) → escalação; caller precisa corrigir o ref. Halt + `CoordinatorError` no envelope externo (coordinator §3.6); não emite Report.
- **`SEMGREP_BINARY_UNAVAILABLE`** (system, non-retryable), **`SEMGREP_EXECUTION_FAILED`**, **`INVALID_RULE_SET`** → escalação / `CoordinatorError` (envelope externo, coordinator §3.6) conforme retryability da tabela §5 do `semgrep-runner`.

**Nunca aliasar erro com `findings: []`.** Colapsar um erro de scan em `findings: []` violaria o compromisso verbatim do coordinator de que `findings: []` é caso válido que propaga (§3.6). O coordinator distingue "scan rodou limpo, zero candidatos" de "scan falhou" pela presença de `errorCode` no tool result.

**Defesa em profundidade — duas superfícies distintas, ambas necessárias.** Os dois mecanismos cobrem superfícies diferentes e juntos formam a defesa: (a) **inspeção de stream** cobre o lado do coordinator — determinística, independente do modelo, pega o erro mesmo que o prompt falhe; (b) **regra prompt-level de não-fabricação** (§5.1 item 4) cobre o lado do output do modelo — impede `findings: []` fabricado mesmo que a inspeção falhasse. Não são redundantes (cobrem loci distintos); são complementares. A regra de prompt é necessária porque o reconhecimento do erro sob Option B é forçado ao prompt (o canal `isError` nativo está fechado).

**Triangulação defensiva (refinamento via DD-D3, não pré-requisito).** Se o envelope `DetectorOutput` tiver `provenance.scan_metadata` ausente/incompleto **e** o tool result carregar `errorCode`, o coordinator tem dois sinais redundantes — mesma lógica triangular do Reporter (`subtype=success` AND `emit_report_seen=False` AND `permission_denials=[]`, `reporter.md` §6.5). Vale documentar o cross-check. **Nota:** DD-D5 é implementável standalone — a inspeção do tool result não depende do envelope existir; a triangulação é refinamento que o envelope habilita.

**Exceção tipada proposta.** Erro non-retryable de `scan_diff` (ou retryable esgotado) propaga como exceção tipada do coordinator, paralela a `SubagentValidationFailed`/`SubagentUnresponsive`/`SubagentRefusedTask`. Nome sugerido: **`DetectorScanFailed`**. **`⚠ CROSS-DOC`** isto é adição à taxonomia de exceções do coordinator — companion edit (§10.5); confirmar se o coordinator prefere exceção nova ou reuso de `CoordinatorError` (envelope externo, coordinator §3.6) sem exceção dedicada.

> 💡 **Conceito Claude relevante (Domínio 2 — MCP / Domínio 5 — Reliability).** `isError` flag + structured error metadata + `isRetryable` (D2) casado com error propagation + escalation (D5). O ponto fino: sob Option B o canal nativo `isError` está fechado, então o erro estruturado (`errorCode` + `isRetryable`) é lido por inspeção determinística, e o roteamento retry-vs-escalate decorre de `isRetryable`. Aplicação determinística do pattern de stream-inspection do coordinator ao caso "tool MCP retorna erro de domínio sob Option B" — o método já está normado; novo é só o sítio.

### 6.3 Família de `ResultMessage.subtype` e `stop_reason`

Dois eixos independentes, herdados verbatim de `classifier.md` §6.3 / `triager.md` §6.3 (lista canônica de subtypes em `agent-sdk/agent-loop`; lista de stop_reasons em `build-with-claude/handling-stop-reasons`):

**Eixo 1 — `ResultMessage.subtype`** (de `agent-sdk/agent-loop`):

| `subtype`                              | Significado                                                | `result` populado | Tratamento no coordinator                    |
|----------------------------------------|------------------------------------------------------------|-------------------|----------------------------------------------|
| `success`                              | Task completa; `structured_output` populado.               | Sim               | Consumir + verificar `stop_reason` (eixo 2). |
| `error_max_turns`                      | Estourou `max_turns` antes de emitir output validável.     | Não               | Levantar `SubagentUnresponsive`.             |
| `error_max_budget_usd`                 | Estourou `max_budget_usd` (se configurado).                | Não               | Levantar `SubagentUnresponsive`.             |
| `error_during_execution`               | Erro interrompeu o loop (API failure, cancelled).          | Não               | Levantar `SubagentExecutionError`.           |
| `error_max_structured_output_retries`  | SDK esgotou retries tentando produzir JSON válido.         | Não               | Levantar `SubagentValidationFailed`.         |

**Eixo 2 — `ResultMessage.stop_reason`** (de `build-with-claude/handling-stop-reasons`):

| `stop_reason` | Aplicabilidade ao Detector |
|---|---|
| `end_turn` | Caminho normal de sucesso. |
| `max_tokens` | `structured_output` pode estar incompleto (muitos findings). |
| `tool_use` | Intermediário (`scan_diff`/`Read`); não aparece em `ResultMessage`. |
| `pause_turn` | Plausível: `scan_diff` é tool potencialmente longa (scan de segundos a minutos, `semgrep-runner` §4.2). Diferente de Triager/Classifier que não têm tool de ação longa. |
| `refusal` | **Crítico**: pode coexistir com `subtype=success` e `structured_output` ausente/incompleto. `snippet`/`surrounding_context` carregam identificadores pessoais (CPF/CNPJ — **sintéticos** em fixtures, §5.2) — gatilho plausível de safety. |
| `model_context_window_exceeded` | Plausível para PRs grandes com muitos findings + janelas de contexto volumosas. |

**Subtype `error_max_structured_output_retries`** — exaustão de validação-retry do SDK → classe Validation → `SubagentValidationFailed`. Nome do subtype pinado em `classifier.md` §6.3; herdado verbatim.

**Caso crítico — `subtype=success` com `stop_reason=refusal`.** Doc oficial (verificada work-session #46): a saída pode não casar o schema porque a mensagem de refusal tem precedência sobre as constraints. O coordinator discrimina `stop_reason="refusal"` mesmo dentro de `subtype="success"` e trata como classe Refusal → `SubagentRefusedTask`. Acesso direto a `stop_reason` no `ResultMessage` em Python é **confirmado empiricamente**: o campo está presente no `ResultMessage` do `claude-agent-sdk==0.2.87` (presente desde 0.1.46). O caveat anterior de que seria TypeScript-only era factualmente stale — `triager.md`/`classifier.md`/`matcher.md` §6.3 já assertam o acesso direto (`message.stop_reason == "refusal"`). A detecção de refusal é leitura direta do campo, não varredura de stream events; a propagação mora no coordinator (Branch B). Doc oficial também nota: ao receber `refusal`, resetar o contexto antes de continuar.

### 6.4 Classes de erro relevantes

Quatro classes SDK-native, herdadas de `classifier.md` §6.2 / `triager.md` §6.2 (todas propagadas pelo coordinator):

| Classe | Locus | Quem detecta | Quem propaga |
|---|---|---|---|
| Validation | SDK runtime | SDK (schema validation / retry exhaustion) | Coordinator (`SubagentValidationFailed`) |
| Budget | SDK runtime | SDK (`max_turns`/`max_budget_usd`) | Coordinator (`SubagentUnresponsive`) |
| Refusal | Modelo | Modelo (safety refusal) | Coordinator (`SubagentRefusedTask`) |
| System | OS-level | Coordinator (try/except sobre `query`) | Coordinator (re-raise tipado) |

**Mais** a propagação de erro de tool (`scan_diff` errorCode) de §6.2 — **não é uma quinta classe SDK-native**, é erro de domínio de uma tool MCP surfaçado por inspeção determinística e roteado pelo coordinator (`DetectorScanFailed` proposto). Contract violation do próprio Detector (ex.: reordenamento de findings vs `scan_diff`, mutação de passthrough, fabricação) → `SubagentContractViolation`.

### 6.5 Não há família intra-handler

Reporter §6.3 documenta 7 errorCodes intra-handler (Branch A). Detector não tem locus análogo — Branch B sem handler executando lógica entre input e output. Validation-retry é gerenciado pelo SDK transparentemente. Asymmetry deliberada vs Reporter; sinal para a destilação do template (§6.3 do template é condicional ao branch). Idêntico a `classifier.md` §6.4.

### 6.6 Casos que parecem erro mas não são

- **`findings: []` com provenance.** Não é erro — empty result válido (§3.6).
- **`pause_turn` durante `scan_diff`.** Não é erro — scan longo é esperado (`semgrep-runner` §4.2).
- **`surrounding_context` divergente em re-run.** Não é erro — `Read` é determinístico sobre o mesmo estado, mas o modelo pode escolher janela ligeiramente distinta; não-determinismo de LM.
- **`num_turns` variável com N.** Não é erro — turns escalam com número de findings (§1.4).

## 7. Provenance e versionamento

### 7.1 Versão da spec

`spec_version: 0.1.0`. SemVer (alinhada a `reporter.md` §7.1, `classifier.md` §7.1, `triager.md` §7.1). Bump rules:

- **Patch (0.1.x):** correções de redação, esclarecimentos, sem mudança de contrato.
- **Minor (0.x.0):** adição de campo ao **envelope `DetectorOutput`** (o coordinator desempacota antes — §3.5 — e o Classifier nunca vê o envelope, logo não-breaking ao consumer); adição a `ScanProvenance` (não-breaking ao Classifier pela mesma razão; **mas** ver ressalva sobre o Reporter abaixo); novos casos em §9; novos exemplares few-shot em §5.2.
- **Major (x.0.0):** **adição/remoção/rename de campo a `DetectorFinding`**; mudança de semântica de campo existente; troca de Branch B para Branch A; mudança no shape consumido de `scan_diff`.

> **Mecanismo confirmado verbatim (work-session #46).** Leitura de `classifier.md:127,134,145` fecha o eixo: as três são `extra="forbid"` em modelos de **output** do Classifier (`StructuredContext`/`ClassifiedCandidate`/`ClassifierOutput`), não de input — confirmado por `classifier.md:135` ("Campos verbatim do DetectorFinding (passthrough, preservados sem mutação)") e por `classifier.md:153` ("validação do **próprio output** pelo coordinator"). Não existe `DetectorFinding.model_validate` em lugar nenhum. A quebra é, portanto, **acoplamento de passthrough** no `ClassifiedCandidate` — não validação de input. A severidade major decorre adicionalmente da convenção `classifier.md` §7.1 ("mudança no shape consumido do Detector"). Ambas as razões convergem na mesma classificação; manter **major** alinha com o pattern fail-loud (G2 da Classifier) — degradar para minor toleraria drop silencioso de campo.

### 7.2 Provenance servida

O envelope carrega a provenance do scan (`ScanProvenance`, §3.2) — repasse da provenance estática + dinâmica do `scan_diff` (`semgrep-runner` §6). O Detector não gera provenance própria (não tem versão de rule set nem de binário — isso é do `semgrep-runner`); serve a do scan e a deixa rastreável downstream. Forward-ref ao Reporter para citação (§3.5).

### 7.3 Provenance da spec vs provenance da execução

Distinção: `spec_version` (versão deste contrato) é metadado da implementação (constante em `src/subagents/detector/__init__.py`, análogo a `classifier.md` §9.4). `ScanProvenance` é provenance de **execução** (qual rule set / binário / refs produziram estes findings). Não confundir.

### 7.4 Stateless

O Detector não persiste estado próprio. `02-detector.json` é gravado pelo coordinator (§4.4). Cada execução é independente; sem memória entre PRs.

## 8. Não-objetivos e fronteiras

### 8.1 Não-objetivos de responsabilidade

- **Não decide violação.** Localiza possibilidade; avaliação é do Matcher (firewall epistêmico, §1.2/§2.4/§8.3).
- **Não consulta `policy-reader`.** Sem esse server no inventário (§1.3). Fisicamente impedido de pré-julgar cláusulas.
- **Não carrega `rule_severity`/`rule_message`.** Strip-opinion (§3.3).
- **Não computa nem consome `changed_paths`.** Opera de `base_ref`/`head_ref` via `scan_diff` (§2.2). DD-T05 ortogonal — registrado, não reaberto.
- **Não resolve/valida refs.** Repassa a `scan_diff`; erros de ref tratados via errorCode (§6.2).
- **Não persiste estado.** Stateless (§7.4).
- **Não modifica filesystem.** `Read` + `scan_diff` apenas; sem `Write`/`Edit`/`Bash`.

### 8.2 Não-objetivos de escopo (herdados de `scan_diff`)

- **Não faz análise cross-file (taint).** MVP single-file; herda o limite do `scan_diff` (`semgrep-runner` §7 / ADR-0002).
- **Não retorna findings parciais em timeout.** Herda all-or-nothing do `scan_diff` — `SCAN_TIMEOUT` descarta parciais (`semgrep-runner` §7). Honestidade epistêmica > parcial enganoso.
- **Não faz streaming de findings.** `scan_diff` retorna em bloco (`semgrep-runner` §7).
- **Não cobre PRs cross-repository.** Diff de PR única.

### 8.3 Fronteira epistêmica

O Detector localiza via detecção sintática (`scan_diff`) + inspeção de contexto (`Read`). Não tem janela para: aplicabilidade jurídica (Matcher), comportamento runtime do código, histórico do repositório. Citação verbatim do invariante (arch §5.3, ~linha 177): *"Sem acesso ao `policy-reader`, o Detector é fisicamente impedido de 'adivinhar' cláusulas aplicáveis e contaminar o output com pré-julgamento."*

Assimetria de erro: o Detector deve preferir reportar candidato duvidoso (falso-positivo, recoverable — o Classifier/Matcher filtram downstream) a omitir candidato real (falso-negativo, silencioso). O `scan_diff` ruleset curado já encapsula essa calibragem; o Detector não adiciona filtro de relevância sobre os findings do scan.

### 8.4 Build-vs-reuse — MCP oficial do Semgrep (não-objetivo desta spec)

Registro de escopo (decisão do servidor MCP, **não** do subagente; não é DD do Detector): existe um MCP server oficial do Semgrep (migrado para o binário `semgrep`, `semgrep mcp`), mas suas tools (`semgrep_scan` etc.) são **content-based** (recebem `code_files:[{path,content}]`), **não** diff-aware sobre `base_ref`/`head_ref`. Diff-over-refs é capacidade de CLI/CI (`--baseline-commit`), não exposta como tool MCP oficial. Logo o `scan_diff` caseiro do `semgrep-runner` cobre um gap real. **Locus correto deste registro:** `docs/specs/semgrep-runner/canonical.md` §7 (que hoje lista não-objetivos do servidor mas **não** menciona build-vs-reuse — adição válida, confirmado na revisão) ou nota de revisão futura do ADR-0010 — housekeeping separado, fora desta spec. Citado aqui só para rastreabilidade.

## 9. Cenários de teste

Critérios de aceitação (catálogo de PRs sintéticos, T11+):

### 9.1 Happy path
- [ ] `scan_diff` retorna N findings → Detector emite `DetectorOutput` com N `DetectorFinding` + um bloco `provenance`.
- [ ] Cada `DetectorFinding` carrega `file`, `line`, `rule_id`, `snippet`, `surrounding_context`.
- [ ] Ordem dos findings preservada de `scan_diff` (`(path, start_line)` ascendente).

### 9.2 Empty result
- [ ] `scan_diff` `findings: []` → `DetectorOutput(findings=[], provenance=...)`, `isError`-equivalente ausente. Não é erro.
- [ ] `provenance` presente mesmo com `findings` vazio.

### 9.3 Fidelidade do mapeamento (DD-D1)
- [ ] `rule_severity` e `rule_message` **ausentes** do output.
- [ ] `location.path`→`file`; `location.start_line`→`line`; `start_col`/`end_line`/`end_col` descartados.
- [ ] `rule_id` e `snippet` idênticos ao `scan_diff`.

### 9.4 Provenance (DD-D3)
- [ ] Envelope carrega `rules_version`, `semgrep_version`, `scan_metadata` — **um** bloco per-scan, não N cópias per-finding.
- [ ] `provenance` repassada verbatim do `scan_diff` (sem transformação).
- [ ] Coordinator persiste `provenance` em `02-detector.json` e a torna disponível ao Reporter.

### 9.5 `surrounding_context` budget (DD-D2)
- [ ] `surrounding_context` gerado via `Read` de janela em torno de `line`.
- [ ] Tamanho dentro da banda floor/ceiling (§3.4); não ilimitado.

### 9.6 Propagação de erro de scan (DD-D5)
- [ ] `scan_diff` `errorCode=SCAN_TIMEOUT` → coordinator detecta via inspeção de stream → retry (isRetryable).
- [ ] `scan_diff` `errorCode=GIT_REF_NOT_FOUND` → escalação / `CoordinatorError` (envelope externo, coordinator §3.6); **não** `findings: []`.
- [ ] Detector **não** fabrica findings nem emite `findings: []` enganoso sob erro de scan (regra prompt-level §5.1).
- [ ] Triangulação: `provenance.scan_metadata` ausente AND `errorCode` presente → cross-check redundante (§6.2).

### 9.7 Discriminação de subtype/refusal
- [ ] Coordinator discrimina `subtype="error_max_structured_output_retries"` → `SubagentValidationFailed`.
- [ ] Coordinator discrimina `stop_reason="refusal"` dentro de `subtype="success"` → `SubagentRefusedTask` (PR com CPF/CNPJ **sintéticos** como gatilho, §5.2).
- [ ] `error_max_turns` (PR patológico em N) → `SubagentUnresponsive`, sem output parcial.

### 9.8 Provenance da spec / persistência
- [ ] `spec_version` consultável (constante em `src/subagents/detector/__init__.py`).
- [ ] Mudança no shape de `DetectorFinding` dispara bump **major**; adição ao envelope `DetectorOutput`/`ScanProvenance`, bump **minor** (per §7.1).
- [ ] Ausência de arquivos persistidos **pelo Detector** (`02-detector.json` gravado pelo coordinator).

## 10. Cross-references

### 10.1 Source-of-truth artifacts
- **Função e posição:** `docs/architecture-overview.md` §3, §5.3; matriz de tools §5.7 (~219-231).
- **Capacidade externa:** `docs/REQUIREMENTS.md` **RF-001** (:15-24, detecção); RF-002 (:28-37) herdado do rule set, não materializado aqui.
- **Skeleton de invocação + tool-set:** `coordinator.md` §3.2 (skeleton), §3.3 (`build_detector_prompt` — **já existe**, signature `(pr_metadata, triager_output)`; reconciliar, não criar).
- **Tool consumida:** `docs/specs/semgrep-runner/canonical.md` §4.2 (`scan_diff`), §5 (errorCodes), §6 (provenance), §7 (não-objetivos), §8 (acceptance), :150 (ordering).
- **Input contract (Detector output) consumido pelo Classifier:** `classifier.md` §2.1 (DD-C7, ratificado aqui).
- **Branch B reference:** `triager.md` §4, §6.3; `classifier.md` §4, §6.3 (mecanismo gêmeo).
- **Branch A reference:** `reporter.md` §4, §6 (contraste arquitetural).
- **`output_format` wire form:** `reporter.md` §10.6 + smoke-test; doc oficial Agent SDK (verificada #46).
- **Stream-inspection precedent:** `coordinator.md`, passagem `ReportNotEmitted` + captura de payload do Reporter (**citar por âncora semântica, não por linha** — reviews divergiram no número; pattern ratificado #37/#38).
- **Trinca de provenance policy/legal:** `coordinator.md:174`.

### 10.2 ADRs aplicáveis
- **ADR-0001** — stack canônica.
- **ADR-0002** — convenções MCP + Option B (relevante ao consumo de `scan_diff`; §6.2).
- **ADR-0010** — estratégia de instalação Semgrep; locus adjacente ao registro build-vs-reuse (§8.4).
- **Matriz de tools:** não há ADR dedicado; matriz autoritativa em `arch` §5.7 (confirmado na revisão).

### 10.3 Requisitos
- **RF-001** (detecção, `docs/REQUIREMENTS.md:15-24`) materializado; **RF-008** (troca de framework sem alteração de código, :110) protegido pelo firewall epistêmico (§2.4). Assimetria falso-positivo/falso-negativo análoga ao Triager (`triager.md` §8.3) e à honestidade epistêmica do Matcher (RF-005). (Frases de RF-001/RF-008 confirmadas verbatim #46.)

### 10.4 Estado das decisões de design (DDs)
- **DD-D1** — *fechada por design.* Ratificação do `DetectorFinding` (arch §5.3) + mapeamento strip-opinion/keep-provenance. Articulação principista do firewall já normado; descarta `rule_severity`/`rule_message`. §3.1, §3.3.
- **DD-D2** — *fechada por design.* Budget de `surrounding_context` bound no produtor (Detector), janela simétrica via `Read`, banda floor/ceiling, N provisional T11+. Fecha o forward-ref G6 da Classifier. §3.4.
- **DD-D3** — *fechada por design.* Envelope `DetectorOutput = {findings, provenance}`; provenance per-scan no nível do envelope (não per-finding); coordinator desempacota (findings→Classifier, provenance→scratchpad+Reporter). Forward-ref ao Reporter **resolvido (C2/Opção B): Reporter 0.5.0 carrega `scan_provenance` top-level** (§10.5(5)). §3.2, §3.5.
- **DD-D4** — *fechada por herança.* Branch B (`output_format`), envelope wire form herdado de `reporter.md` §10.6. §4.
- **DD-D5** — *fechada por design.* Propagação de erro de `scan_diff` via inspeção determinística do stream pelo coordinator (pattern ratificado #37/#38 aplicado a novo caso); roteamento retry/escalate por `isRetryable`; nunca aliasar com `findings: []`; regra prompt-level de não-fabricação; triangulação via DD-D3 como cross-check (refinamento, não pré-requisito). Exceção `DetectorScanFailed` proposta. §6.2.
- **DD-T05** (`changed_paths`) — *neutra ao Detector, registrada não reaberta.* Detector opera de refs via `scan_diff`. §2.2.

### 10.5 Companion edits / forward-refs pendentes
1. `coordinator.md` §3.2 — **✅ aplicado (C3):** `output_format` (`DetectorOutput.model_json_schema()`) e `max_turns=30` declarados no skeleton do stage Detector. A signature `build_detector_prompt(pr_metadata, triager_output)` já existente foi mantida (refs via `pr_metadata`; §2.3) — não recriada. (Confirmação final de que `pr_metadata` carrega `base_ref`/`head_ref` é reconciliação de impl T11+.)
2. `coordinator.md` §3.2 — allowlist do Detector confirmada: built-in `Read` + `mcp__semgrep-runner__scan_diff`; sem `Glob`/`Grep`/`policy-reader` (arch §5.7).
3. `coordinator.md` — taxonomia de exceções: avaliar `DetectorScanFailed` (ou reuso de `CoordinatorError`, envelope externo, coordinator §3.6) para erro non-retryable de `scan_diff` (§6.2). **Decisão do coordinator, pendente.**
4. `coordinator.md` — convenção de scratchpad `02-detector.json` confirmada (:84,108,137,172).
5. **Reporter — ✅ aplicado (C2/Opção B).** Reporter **0.5.0** adicionou `scan_provenance` top-level opcional ao `ReportPayload` (`reporter.md` §3/§4.3), mesma model que `DetectorOutput.provenance`; o coordinator a roteia ao Reporter (`coordinator.md` §3.2/§3.5). O minor bump (0.4.0 → 0.5.0) fechou o débito pré-registrado em §3.5.
6. `docs/REQUIREMENTS.md` — RF-001 fixado (§1.2); confirmar frase verbatim na revisão.
7. **Housekeeping separado:** registrar o gap build-vs-reuse (MCP oficial do Semgrep content-based) em `semgrep-runner/canonical.md` §7 ou nota de revisão do ADR-0010 (§8.4). Fora desta spec.
8. `docs/tasks.md` §Tasks T11+ — prever implementação do Detector: `src/subagents/detector/models.py` (`DetectorFinding`/`ScanProvenance`/`DetectorOutput`; `DetectorInput` é notacional, sem validação runtime — §2.1), `prompt.py` (template §5 + few-shot com fixtures sintéticos), `__init__.py` (`spec_version="0.1.0"`); tests cobrindo §9.
9. **Conflito §7.1 — fechado por verificação verbatim #46.** `classifier.md:127,134,145` são modelos de **output** (Review A correto): mecanismo de quebra por adição a `DetectorFinding` = acoplamento de passthrough no `ClassifiedCandidate` (`classifier.md:135`/`:153`), não validação de input; severidade **major** mantida (convenção `classifier.md` §7.1 + fail-loud G2). Sem pendência.

### 10.6 Notas de autoria (work-session #46)
- Spec autorada após verificação externa de SDK/MCP/Semgrep contra doc oficial vigente (achados no blockquote de cabeçalho e §6.2/§8.4).
- DD-D1/D4/T05 fechados por herança/articulação; D2/D3/D5 fechados por design com reframings do review do Code (D5 não-ortogonal mas aplicação de pattern ratificado; D5 standalone vs D3 refinamento; D3 por granularidade per-scan; D2 com critério floor/ceiling explícito + N inicial ±10).
- **Rodada de reconciliação cross-doc (dois reviews do Code).** Folded: RF-002→**RF-001** (RF-002 é cobertura, do rule set); dualidade de numbering Etapa 2 coordinator / Etapa 1 arch; `build_detector_prompt` **já existe** (reconciliar signature, não criar); `DetectorInput` é tipo notacional (Branch B não valida input via Pydantic); §3.5 promovido a **invariante de boundary**; `ScanProvenance` no Reporter é **adição confirmada** (minor bump do Reporter); §7.1 reescrito — adição a `DetectorFinding` é **major** (mecanismo = acoplamento de passthrough, não validação de input); N=±10 inicial; max_turns=30 provisional com aritmética 2+N explícita; tabela §3.3 split em per-finding vs per-scan; defesa-em-profundidade reframed como superfícies complementares; fixtures com PII **sintética** (privacy-safety). ~12 dos ~15 `⚠ CROSS-DOC` fechados pela verificação dos reviews.
- **Conflitos de review — estado final.** (i) `extra="forbid"` input vs output: **fechado por verificação verbatim #46** (Review A no mecanismo — modelos de output, quebra por passthrough; severidade **major** mantida por convenção + fail-loud). (ii) número de linha do `ReportNotEmitted` (reviews divergiram): resolvido por **âncora semântica** em vez de linha nua.
- **`⚠` remanescentes — decisões futuras genuínas, nenhum resíduo de pesquisa:** (1) ~~declaração de `output_format`/`max_turns` no skeleton~~ **✅ aplicado (C3)**: `coordinator.md` §3.2 agora os declara (`output_format=DetectorOutput.model_json_schema()`, `max_turns=30`); (2) taxonomia `DetectorScanFailed` vs `CoordinatorError` (decisão do coordinator); (3) valor final de `max_turns` (30 provisional — ratificável em T11+). [Resolvido: detecção de refusal em Python — `stop_reason` é campo direto do `ResultMessage` (SDK 0.2.87, verificado), não TS-only.]
