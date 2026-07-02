<!--
APÊNDICE D — índice das specs + citações do corpo (fonte Markdown para conversão .docx ABNT)
Fonte: docs/specs/ @ commit 61a6585247867da4f4a19f27a12ebc8a1fa7ba14 (mesmo pin do Apêndice E — índice das ADRs).
Critério de inclusão: seções de docs/specs/ citadas POR SEÇÃO (§) no corpo do relatório; a rodada
final deste levantamento deve ser refeita sobre o TEXTO FINAL do relatório (o levantamento é
mecanizável: grep por ".md §" no fonte). Citações feitas por outros apêndices (REQUIREMENTS.md, architecture-overview.md) às specs NÃO
geram trecho — ficam cobertas pelos permalinks. Trechos são reprodução verbatim; supressões são
marcadas com [...]; notas editoriais deste apêndice aparecem entre colchetes em itálico.
-->

# APÊNDICE D — Especificações dos componentes: índice e citações

As especificações de componente vivem em `docs/specs/` — seis specs de subagentes/coordenador e, para cada servidor MCP, o par canônica+compacta (ADR-0003) — somando ~6.600 linhas, extensão inviável para anexação integral. Na forma de trechos selecionados autorizada pelo preâmbulo destes Apêndices, este apêndice adota um critério objetivo de inclusão: **reproduz, verbatim, as seções das specs que o corpo deste relatório cita por seção (§)**, cada trecho precedido da indicação de onde o corpo o cita e de qual afirmação ele sustenta. Seções não citadas permanecem acessíveis pelos permalinks do índice (D.1). Supressões dentro de um trecho são marcadas com `[...]`; o título da seção aparece no cabeçalho da entrada e não é repetido dentro do trecho; notas editoriais deste apêndice aparecem *[entre colchetes, em itálico]*. As specs são redigidas em português com identificadores e termos técnicos em inglês (ADR-0006).

## D.1 — Índice das especificações

As specs assinaladas com † são citadas por seção (§) no corpo deste relatório e têm trechos reproduzidos em D.2; as demais são citadas no corpo apenas como conjunto (`docs/specs/subagents/`) ou por nome de arquivo.

**`subagents/coordinator.md`** † — Main loop Python que encadeia as cinco chamadas `query()` ao Claude Agent SDK (prompt chaining estrito, pattern A''), com a quíntupla de lockdown por estágio, o contrato de terminação e a tool `emit_report`.
<https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/specs/subagents/coordinator.md>

**`subagents/triager.md`** † — Subagente que decide `proceed`/`skip` da análise a partir do diff do PR, com saída estruturada flat enum-tag e sem acesso a MCP servers.
<https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/specs/subagents/triager.md>

**`subagents/detector.md`** † — Subagente que localiza pontos de tratamento candidatos no diff via `scan_diff` (princípio strip-opinion/keep-provenance), sem acesso ao `policy-reader`.
<https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/specs/subagents/detector.md>

**`subagents/classifier.md`** † — Subagente que enriquece candidatos com `structured_context` de quatro campos, restrito soft aos vocabulários publicados via `policy://vocabularies`, com null-on-miss.
<https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/specs/subagents/classifier.md>

**`subagents/matcher.md`** — Subagente que avalia candidatos classificados contra as cláusulas ativas via `check_applicability` e emite os quatro vereditos com trinca de proveniência; único autorizado às tools decisórias do `policy-reader`.
<https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/specs/subagents/matcher.md>

**`subagents/reporter.md`** † — Subagente terminal que serializa verbatim o estado consolidado pelo coordenador e o emite via tool customizada `emit_report` (dual sink), sem sintetizar, reclassificar ou recomputar.
<https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/specs/subagents/reporter.md>

**`policy-reader/canonical.md` + `compact.md`** — Servidor MCP de acesso estruturado à Política: três resources (`policy://catalog`, `policy://schema-version`, `policy://vocabularies`) e três tools (`get_clause`, `find_clauses_by_law_article`, `check_applicability`), com contrato de erro em três classes.
<https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/specs/policy-reader/canonical.md> · <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/specs/policy-reader/compact.md>

**`semgrep-runner/canonical.md` + `compact.md`** — Servidor MCP de detecção sintática diff-aware (`scan_diff` sobre `base_ref`/`head_ref`), com o rule pack brasileiro (seis reconhecedores) e seis errorCodes canônicos.
<https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/specs/semgrep-runner/canonical.md> · <https://github.com/paivapereira/lgpd-policy-review/blob/61a6585247867da4f4a19f27a12ebc8a1fa7ba14/docs/specs/semgrep-runner/compact.md>

## D.2 — Citações do corpo do relatório

### D.2.1 — `coordinator.md`

**§2 — Arquitetura de execução**

*Citado em:* §2.1 do relatório — "Cada subagente atua como agente principal de sua própria chamada, possuindo prompt, ferramentas e permissões específicos para sua função"; e §2.2 — "Trata-se de um script em Python responsável exclusivamente por encadear as cinco chamadas ao SDK, sem utilizar mecanismos de despacho de agentes".

*Trecho:*

Coordinator não é AgentDefinition. É script Python que executa cinco chamadas sequenciais `query()` do `claude-agent-sdk`. Em cada chamada, `ClaudeAgentOptions` declara a **quíntupla canônica do lockdown agent CI/CD-headless** (5 elementos de denial-on-miss), juntamente com `system_prompt` (role definition, separado) e `tools` (context restriction; eixo ortogonal — ver nota abaixo):

[...]

Não há `agents={}`, não há AgentDefinition, não há Agent tool dispatch. Cada subagente é o main agent da sua própria query; pattern é prompt chaining estrito (D1.6 do exam guide canônico).

Trade-off A' vs A'' registrado em learning-log #38: A' (AgentDefinition + Agent tool dispatch) paga custo de surface SDK sem usar o benefício (dispatch só compensa quando o main agent escolhe entre múltiplos subagentes). A'' elimina indireção, reduz error propagation surface (um modo de falha por etapa, não dois) e reduz token cost por etapa (sem main-agent reasoning + dispatch overhead).

**§3.5 — Etapa 5 — Reporter**

*Citado em:* §2.2 do relatório — o Reporter "dispõe exclusivamente da ferramenta personalizada `emit_report`, sem acesso às demais ferramentas do ambiente, ou seja, sua configuração remove inclusive as ferramentas nativas do contexto do modelo".

*Trecho:*

[...]

```python
    async for msg in query(
        prompt=build_reporter_prompt(matcher_output_or_skip),
        options=ClaudeAgentOptions(
            system_prompt=REPORTER_SYSTEM_PROMPT,
            tools=[],                      # PR #67 Gate 6: remove built-ins do contexto
            allowed_tools=["mcp__reporter_tools__emit_report"],
            mcp_servers={"reporter_tools": reporter_sdk_server},
            permission_mode="dontAsk",
            setting_sources=[],
            strict_mcp_config=True,
            max_turns=3,                   # DD-10.4: retry budget; aritmética canônica em Reporter spec §1.5
        ),
    ):
```

[...]

### D.2.2 — `triager.md`

**§1.5 — Stack e governança**

*Citado em:* §2.3 do relatório — a camada de agentes foi construída sobre o Claude Agent SDK (a partir da versão 0.2.87), "responsável por fornecer o laço agêntico, a configuração de execução por chamada, os mecanismos de saída estruturada e o suporte a servidores de ferramentas em processo"; e a adoção de um único modelo (Claude Opus 4.7) com otimização de custo deliberadamente postergada.

*Trecho:*

Stack: Python 3.12.7, `claude-agent-sdk` ≥ 0.2.87 (baseline empírico validado em smoke-tests Gate 1, Gate 6 e `sdk_output_format_lockdown`; piso definitivo a fixar em `pyproject.toml` na Provisão MC-E), `pydantic` 2.13.4.

**Modelo de inferência.** Claude Opus 4.7 com adaptive thinking (`thinking: {type: "adaptive"}`), herdado do default do coordinator. Escolha calibrada para fase de desenvolvimento e validação funcional: otimização de modelo (cost/latency via Haiku 4.5) é decisão deferida para pós-produção (ver DD-T11 em §8.4), seguindo o princípio de não introduzir variável adicional na investigação enquanto o sistema não estiver 100% funcional.

[...]

> 💡 **Conceito Claude relevante (Domínio 1 — Agentic Architecture & Orchestration, Task Statement 1.1).** Loop termination tem dois mecanismos coexistentes neste subagent. (i) **Convergência semântica** via `output_format=json_schema`: o SDK encerra o agentic loop quando o modelo produz output que valida contra o schema declarado — stop implícito. (ii) **Budget hard** via `max_turns` (e/ou `max_budget_usd`): stop explícito por estouro. Os dois são complementares — (i) é o caminho feliz, (ii) é o cinto de segurança. Spec do Triager documenta a distinção para que callers (coordinator) saibam discriminar os subtypes de `ResultMessage` correspondentes (ver §6.3).

### D.2.3 — `detector.md`

**§1.2 — Função**

*Citado em:* §2.2 do relatório — o Detector "identifica potenciais pontos de tratamento de dados no diff, materializando o RF-001", com a cobertura dos identificadores brasileiros (RF-002) implementada pelas regras do `semgrep-runner`, não pelo subagente.

*Trecho:*

Identifica **pontos de tratamento candidatos** em um diff de pull request. Para os refs `base_ref`/`head_ref` do PR, invoca `scan_diff`, e para cada finding retornado emite um registro estruturado com localização, regra disparada, snippet e contexto circundante. Output: lista de candidatos `[{file, line, rule_id, snippet, surrounding_context}]` envelopada com a provenance do scan (shape concreto em §3).

Materializa **RF-001 — "Detecção de coleta de dados pessoais"** (`docs/REQUIREMENTS.md:15-24`). **RF-002** ("Cobertura de identificadores brasileiros: CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde", `docs/REQUIREMENTS.md:28-37`) **não** é responsabilidade da Detector spec — é requisito de cobertura do **rule set curado pelo `semgrep-runner`** (mais o `data_categories` emitido pelo Classifier, RF-002 critério ~linha 35); herdado, não materializado aqui. A capacidade externa observável de RF-001 é a presença da lista de candidatos (possivelmente vazia) com os cinco campos por candidato, consumível pelo Classifier downstream. (Padrão idêntico ao `classifier.md` §1.2, que cita RF-003 verbatim em `docs/REQUIREMENTS.md:41`. Frase canônica confirmada verbatim #46 — critério RF-001 (`docs/REQUIREMENTS.md:22`): "o Report final carrega ao menos um finding apontando essa linha como ponto de coleta candidato, com `rule_id` identificando o reconhecedor disparado e `file`/`line`/`snippet` preenchidos".)

A fronteira load-bearing: **o Detector localiza possibilidade, não decide violação.** A separação "detecta possibilidade vs avalia conformidade" é o que o separa do Matcher (`docs/architecture-overview.md` §5.3). Sem acesso ao `policy-reader`, o Detector é fisicamente impedido de "adivinhar" cláusulas aplicáveis e contaminar o output com pré-julgamento (arch §5.3, linha citada verbatim em §8.3).

**§2.4 — Princípio: Detector localiza, não julga**

*Citado em:* §2.2 do relatório — "Em conformidade com o princípio de 'localizar sem julgar' [...] A interpretação de conformidade é responsabilidade exclusiva do Matcher. Sem acesso ao `policy-reader`, o Detector limita-se a identificar possibilidades, sem inferir cláusulas aplicáveis".

*Trecho:*

O Detector opera sobre o resultado sintático do `scan_diff` e sobre o código local (via `Read`). Não consulta a Política, não avalia aplicabilidade de cláusula, não emite veredito. O `rule_id` e o `snippet` são localizadores; o `surrounding_context` é material descritivo para o Classifier downstream extrair `structured_context`. Confundir localização com avaliação reintroduziria o acoplamento código↔política que a arquitetura separa deliberadamente (**RF-008** — "Substituição de framework jurisdicional sem alteração de código", `docs/REQUIREMENTS.md:110`, confirmado verbatim #46; arch §5.3). Esta fronteira é o invariante load-bearing protegido por toda a spec (ver §3.3, §8.3).

**§3.3 — Mapeamento `scan_diff` → `DetectorFinding` (DD-D1: strip-opinion / keep-provenance)**

*Citado em:* §2.2 do relatório — "o Detector preserva a localização e a proveniência dos achados, mas descarta a severidade originalmente atribuída pelo Semgrep".

*Trecho:*

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

### D.2.4 — `classifier.md`

**§2.4 — Princípio: Classifier descreve, não julga**

*Citado em:* §2.2 do relatório — "preserva-se a fronteira arquitetural segundo a qual o Classifier descreve, mas não julga".

*Trecho:*

O Classifier opera sobre o **código local** e contra os **vocabulários jurisdicionais** publicados pela Política — não consulta cláusulas, não avalia aplicabilidade, não emite veredito. O `structured_context` é descrição factual do que o código faz e do que ele declara fazer, alinhada ao vocabulário do framework declarado, mas independente do que a Política exige cláusula a cláusula. Confundir extração com avaliação é o anti-padrão de classificador acoplado a regras — torna impossível trocar a Política sem reescrever o Classifier (RF-008). Esta fronteira é o invariante load-bearing protegido por toda a spec (ver §3.3, §8.3).

**§3.3 — Vocab membership: soft via system_prompt + null-on-miss, sem `Enum` (DD-C2)**

*Citado em:* §2.2 do relatório — "Os campos governados por vocabulários jurisdicionais são restritos aos vocabulários publicados pela Política. Quando o mapeamento não é possível, o sistema retorna valores nulos ou listas vazias, evitando a fabricação de informações inexistentes".

*Trecho:*

Os três campos governados por vocabulário — `operation_type`, `data_categories`, `declared_legal_basis` — são restringidos aos vocabulários expostos por `policy://vocabularies` (`docs/architecture-overview.md` §5.4: *"Valores em `operation_type`, `data_categories` e `declared_legal_basis` são restringidos aos vocabulários jurisdicionais"*). **Nota de camada:** `operation_type` e `declared_legal_basis` mapeiam aos vocabulários *jurisdicionais* (`operation`, `lawful_basis`); `data_categories` mapeia ao vocabulário *estrutural* de categorias (chave `data_categories`, derivado de POL-000, framework-neutro — ADR-0005 D3), co-localizado no mesmo resource (`policy-reader/canonical.md` §3.3) mas de camada distinta. `declared_transformations` é **free-form** (não governado por vocabulário).

A restrição é **soft** (via `system_prompt`) com **null-on-miss**, **não** validação hard via `Enum` Pydantic. Justificativa load-bearing:

- **RF-003 + `coordinator.md` §3.3:** *"campos nulos em `structured_context` são válidos per RF-003 (extração que falha em mapear ao vocabulário resulta em null, não em invenção)."* `Enum` hard rejeitaria não-membros em vez de nullá-los — conflito direto.
- **Invariante "Classifier descreve, Matcher julga":** validar membership hard é o Classifier **julgando** pertencimento — meio passo na direção do Matcher. A "Nota sobre scoped access" de `coordinator.md` §3.3 já fixa que a fronteira Resource-vs-Tool é preservada em **nível de capability**, não de validação.
- **Precedente do Reporter:** o cross-check #3 (vocabulary membership) foi **removido** do Reporter em #42 por contradizer §2.4 + §8.3 — *"vocab validation é semântica do Matcher upstream, não shape do Reporter"* (`reporter.md` §4.8). O Classifier está ainda mais a montante do Matcher que o Reporter; aplicar a mesma fronteira é consistência, não exceção.

Operacionalmente: o `system_prompt` (§5.1) instrui o modelo a carregar o vocabulário via `ReadMcpResourceTool` no início e usar os valores carregados para restringir `operation_type`, `data_categories` e `declared_legal_basis`; quando a extração não mapeia, o campo é `null` (escalares) ou exclui o item não-mapeável (listas). A spec **não** enforça membership programaticamente — depende de prompt discipline + a fronteira de capability da quíntupla. O Matcher é a autoridade downstream sobre semântica de membership.

[...]

### D.2.5 — `reporter.md`

**§1.2 — Função**

*Citado em:* §2.2 do relatório — "O Reporter limita-se a serializar esse estado sem sintetizar, reclassificar ou recomputar resultados".

*Trecho:*

Subagente terminal do pipeline. Recebe o estado consolidado pelo coordinator — vereditos do Matcher no caminho normal, estado de skip do Triager no caminho de skip — e o emite verbatim como Report JSON estruturado, via a tool customizada `emit_report`, para captura pelo coordinator e persistência em scratchpad. **Não sintetiza, não reclassifica, não computa discriminadores derivados** — `run_outcome`, `summary.counts` e demais campos pré-computados pelo coordinator são propagados sem transformação (inversão DD-7.3 / sessão #38).

**§1.5 — Stack e governança**

*Citado em:* §2.3 do relatório — a tool `emit_report` "não foi implementada com FastMCP. Em seu lugar, empregou-se o servidor em processo disponibilizado pelo Claude Agent SDK (`create_sdk_mcp_server`), uma vez que essa funcionalidade requer acesso ao escopo de execução e à captura de parâmetros disponíveis apenas no contexto da própria aplicação"; e (com `triager.md` §1.5) o suporte do SDK a servidores de ferramentas em processo.

*Trecho:*

[...]

**Por que `create_sdk_mcp_server` e não FastMCP.** CLAUDE.md declara FastMCP como stack canônico para custom MCP servers stdio (`policy-reader`, `semgrep-runner`). `reporter_tools` foge dessa regra deliberadamente: precisa de closure capture sobre `run_path` e `expected_report_id`, o que requer compartilhamento de escopo Python — impossível com FastMCP subprocess (sem shared memory). Doc Anthropic oficial (`platform.claude.com/docs/en/agent-sdk/custom-tools`) trata os dois constructs como casos de uso doc-validated distintos: **stdio MCP server** = "Local processes that communicate via stdin/stdout"; **in-process via `create_sdk_mcp_server`** = "Define custom tools directly in your application code instead of running a separate server process". `reporter_tools` cai legitimamente na segunda categoria.

[...]

**§2.4 — Princípio: Reporter não computa, não deriva, não infere**

*Citado em:* §2.2 do relatório — "As informações agregadas, como contagens por veredito e desfecho da execução, são previamente calculadas pelo coordenador em Python".

*Trecho:*

Toda quantidade derivada (`run_outcome`, `summary.counts`, `summary.total`) é **pré-computada pelo coordinator em Python**. Reporter recebe os valores prontos e os propaga verbatim ao payload do Report. Esta é a inversão DD-7.3 / sessão #38: lógica de discriminação determinística pertence ao coordinator; Reporter é puro passthrough + `emit_report` invocation.

Anti-pattern explícito: Reporter **NÃO** recomputa `run_outcome` a partir dos findings (mesmo que pudesse inferir corretamente em casos triviais); **NÃO** recomputa `counts` agregando findings; **NÃO** re-ordena findings (DD-19); **NÃO** decide se invoca `emit_report` em skip path baseado em sua própria avaliação. Coordinator é a fonte de verdade; Reporter é o serializador.

**§3.1 — Top-level shape**

*Citado em:* §2.2 do relatório — "Cada achado inclui, no mínimo, localização, regra acionada, categorias de dados, operação identificada, veredito, referência à cláusula avaliada — inclusive nos casos classificados como não aplicáveis — e a correspondente trinca de proveniência (reporter.md §3.1)". *[Nota deste apêndice: o §3.1 especifica o shape top-level do Report; os campos por achado que a frase enumera estão especificados em §3.2 e §3.3, reproduzidos na sequência como complemento necessário à verificação da afirmação.]*

*Trecho:*

Payload retornado pelo Reporter via `emit_report` (string JSON serializável; schema validado server-side via `ReportPayload` Pydantic model + cross-checks intra-handler — ver §4):

```python
{
    "report_id": "<uuid>",
    "report_schema_version": "0.1.0",
    "policy_schema_version": "0.1.0",
    "policy_version": "<...>",
    "legal_framework": "LGPD",
    "run_outcome": "success_with_findings"
                   | "success_no_candidates"
                   | "success_all_not_applicable"
                   | "skipped_by_triager",
    "triager_skip_reason": <str | None>,
    "scope": <TriagerInput; ver Triager spec §2.1>,
    "summary": {
        "counts": {
            "compliant": <int>,
            "violation_candidate": <int>,
            "indeterminate": <int>,
            "not_applicable": <int>,
        },
        "total": <int>,  # == sum(counts.values()); cross-check em §4.8
    },
    "findings": [<Finding>, ...],
    "scan_provenance": <ScanProvenance | None>,  # detector §3.2; provenance de EXECUÇÃO do scan, top-level/per-scan (C2)
}
```

[...]

**§3.2 — Schema do finding individual** *[incluído como complemento à citação de §3.1 — ver nota acima]*

*Trecho:*

Cada finding é discriminated union por `verdict`. Estrutura comum seguida de campos específicos por verdict.

**Campos comuns (todos os vereditos).**

```python
{
    "file": <str>,
    "line": <int>,
    "snippet": <str>,
    "rule_id": <str>,
    "data_categories": [<str>, ...],
    "operation_type": "collection",  # MVP v0.1.0 per ADR-0007; passthrough verbatim (valor ilustrativo — pode ser ≠ collection em not_applicable, §3.6)
    "verdict": <str>,
    "policy_clause_ref": "POL-NNN",  # obrigatório em todos 4 verdicts
                                      # (DD-21 ratificado PR #66; preservado
                                      # verbatim do output do policy-reader
                                      # check_applicability per canonical §4.3)
    "policy_schema_version": "0.1.0",
    "policy_version": "<...>",
    "legal_framework": "LGPD",
    "requires_human_review": <bool | undefined>,  # opcional
}
```

[...]

**Verdict `not_applicable`** (cláusula não governa este contexto).

```python
{
    ...common,
    "verdict": "not_applicable",
    "reason": "<texto explicando por que a cláusula não governa>",
    # policy_clause_ref OBRIGATÓRIO em not_applicable (DD-21 ratificado PR #66):
    # presença incondicional preserva audit trail substantivo — auditor LGPD
    # Art. 37 / SDR β precisa identificar qual cláusula foi avaliada-e-descartada,
    # não apenas que algum veredito não-aplicável foi emitido.
}
```

**§3.3 — Provenance trinca top-level + per-finding** *[incluído como complemento à citação de §3.1 — ver nota acima]*

*Trecho:*

Trinca de provenance (`policy_schema_version`, `policy_version`, `legal_framework`) aparece em **dois loci** do Report payload: top-level (provenance do run inteiro) e per-finding (redundante, propagada verbatim de cada veredito do Matcher).

A redundância é **deliberada**. RF-009 descritiva literal exige presença em "todo veredito emitido pelo sistema" + no header do Report. Custo da redundância: ~3 campos × N findings de overhead JSON. Ganho: (a) audit isolation — single finding extraído (e.g., para investigação de incidente, ou snapshot em ticket) preserva sua provenance; (b) detecção de inconsistência — coordinator/handler cross-check de igualdade entre top-level e per-finding (§4.8) sinaliza payload corrompido.
