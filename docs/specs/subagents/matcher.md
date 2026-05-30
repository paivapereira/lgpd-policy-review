# matcher

**spec_version**: 0.1.0

> Spec do subagente Matcher. Segue a estrutura de `reporter.md` v0.4.0, `triager.md` v0.1.0 e `classifier.md` v0.1.0 como template hipótese (a destilação formal de `_template-subagent.md` permanece Fase 2, não materializada). Decisões de design ancoradas em `docs/architecture-overview.md` §3/§5.5/§5.7, `coordinator.md` §3.4, `docs/specs/policy-reader/canonical.md` §3.1/§3.2/§4.3/§5, `docs/REQUIREMENTS.md` RF-004/RF-005/RF-009, ADR-0005 (Decision 4) e ADR-0007 (Decision 3). Autorada na work-session #48, último subagente da ordem Triager → Detector → Classifier → **Matcher**. As decisões load-bearing estão consolidadas no **ledger DD-M (v3)** e foram **verificadas empiricamente contra o motor real** (`check_applicability` em `src/mcp_servers/policy_reader/tools.py`) via smoke-tests #48 e #48-b — não inferidas da spec. Revisão por Code (cross-doc) feita; fixes de severidade Crítico/Alto/Médio/Baixo (C1, C2, H1, H2, M1, M2, L1) **folded em 0.1.0 pré-merge** contra a impl (probes #48-b: `scripts/smoke_tests/check_applicability_48b/`). Bump aplica ao estado mergeado, não em-revisão.
>
> **Premissas verificadas (#48), não assumidas:** (a) `policy://catalog` existe e enumera `{clause_id, status, ...}` — é a fonte do check-all; (b) o gate-MVP de `operation` é enforçado pelo motor (operação ≠ `collection` → `not_applicable` antes do matching); (c) `consent_required` compara `legal_basis` por **igualdade de token canônico** (`consent`), não por prosa nem por categoria; (d) o fail-fast estrutural de `compatible_schema_range` é enforçado no boot do `policy-reader` (`loader.py`), não pelo Matcher.

---

## 1. Identidade e propósito

### 1.1 Nome canônico

`matcher`. Subagent. Não é MCP server, não expõe resources nem tools customizadas. **Consome** do server `policy-reader` os três resources que o `canonical.md` §1/§3.1 afirma serem consumidos pelo Matcher — `policy://catalog` (índice de cláusulas — fonte de enumeração), `policy://vocabularies` (tokens canônicos) e `policy://schema-version` (handshake; o Matcher **lê** mas não valida jurisdição no MVP — §8.4/DD-M22) — e invoca as três tools de avaliação **exclusivas do Matcher** — `check_applicability`, `get_clause`, `find_clauses_by_law_article`. É o **único** subagente com acesso às tools do `policy-reader` (a exclusividade das tools é a fronteira de ADR-0005 Decision 4; o grant dos resources é afirmação positiva de `canonical §1/§3.1`, não silêncio de D4).

### 1.2 Função

Para cada candidato de tratamento classificado pelo Classifier, o Matcher avalia conformidade contra a Política versionada e emite um **veredito por par candidato-cláusula**. É o único subagente que **emite vereditos**: o Triager decide relevância, o Detector localiza candidatos, o Classifier descreve contexto — o Matcher **julga**, e julga exclusivamente através de `check_applicability`, nunca por raciocínio próprio sobre o texto da cláusula (princípio de conduto, §2.4 / DD-M26).

Output: uma lista de `findings`, cada finding sendo um par `(candidato, cláusula)` com um dos quatro vereditos (`compliant`, `violation_candidate`, `indeterminate`, `not_applicable`), pronto para o Reporter consolidar no Report (shape em §3).

### 1.3 Posição na arquitetura

```
Triager → Detector → Classifier → [Matcher] → Reporter
```

Consome o `classifier_output` (lista de candidatos enriquecidos com `structured_context`), monta o conjunto de cláusulas a avaliar a partir de `policy://catalog`, e produz `findings` que o coordinator passa verbatim ao Reporter. O Matcher não persiste estado (sem dual sink); a persistência é do coordinator. Cross-ref `architecture-overview.md` §5.5.

### 1.4 Invocador e modo de invocação

Invocado **uma vez por run** pelo coordinator, via `query()` do `claude-agent-sdk`, em sessão única que recebe o `classifier_output` inteiro (todos os candidatos numa janela de contexto). O AgentDefinition aplica a quíntupla canônica de denial-on-miss (`permission_mode`, `setting_sources`, `strict_mcp_config`, `allowed_tools`, `mcp_servers`) + `system_prompt` (role) + `tools` (built-ins; ver §4.2 e DD-M30) + `output_format` + `max_turns`. Autoritativo: `coordinator.md` §3.4 (companion edit pendente — DD-M15/M30, §10.5).

### 1.5 Stack e governança

`claude-agent-sdk==0.2.87` (pin verificado #48). MCP server `policy-reader` (FastMCP, Option B — ADR-0002). Governança de resource por ADR-0005 (Decision 4: tools exclusivas do Matcher; resource `policy://vocabularies` compartilhado com o Classifier). Escopo MVP por ADR-0007 (Decision 3: somente `operation: collection` é avaliada). Honestidade epistêmica por RF-005; provenance por RF-009.

---

## 2. Input contract

### 2.1 Shape do input

O Matcher recebe `classifier_output`: lista de `ClassifiedCandidate`. Cada candidato carrega o **passthrough** do Detector (preservado verbatim ao longo da pipeline) e o `structured_context` produzido pelo Classifier:

```python
# ClassifiedCandidate (consumido pelo Matcher)
{
    # passthrough do Detector (identidade do locus)
    "file": "<path>",
    "line": <int>,
    "rule_id": "<identificador da regra do Detector>",
    "snippet": "<código>",
    # "surrounding_context": <str>   # presente, NÃO consumido pelo Matcher

    # structured_context produzido pelo Classifier (nomes reais — classifier.md §3.1)
    "structured_context": {
        "operation_type": "<token de operation>" | None,      # Optional — pode ser null (ambíguo)
        "data_categories": ["<token de POL-000>", ...],        # pode ser [] (genérico/ambíguo)
        "declared_legal_basis": "<token de lawful_basis>" | None,  # Optional, null-on-miss
        "declared_transformations": ["<...>", ...],            # NÃO consumido pelo Matcher
    }
}
```

> **Atenção (correção C1, review #48-b):** os nomes do `structured_context` são os do **output do Classifier** (`operation_type`, `declared_legal_basis`, `declared_transformations`) — `classifier.md` §3.1 (l.126-131), `models.py` StructuredContext. **NÃO** são os nomes do **input da tool** (`operation`, `legal_basis`, `destination` — `canonical §4.3`). O Matcher faz a tradução na projeção (§2.3). Não existe `destination` no output do Classifier; `declared_transformations` é descartado.

**Tokens canônicos, não prosa (DD-M11, verificado #48).** O Classifier normaliza para tokens canônicos: `data_categories` (POL-000), `operation_type` (vocabulário `operation`), `declared_legal_basis` (vocabulário `lawful_basis`, ou `null` se ausente — null-on-miss, `classifier.md` §3.3). O input `legal_basis` da tool é tipado como texto livre (`canonical §4.3 l.526, "valor textual livre, não vocabulário fechado"`), **mas o motor compara por igualdade contra o token canônico** `consent` (verificado #48, tools.py:382-423). Logo a fidelidade depende do Classifier ter normalizado: se um valor em prosa (ex.: `"consentimento explícito"`) escapar para `declared_legal_basis`, a projeção o passa à tool e o resultado é **falso `violation_candidate`** ("fora do vocabulário canônico") — verificado (#48, T1x). O Matcher passa verbatim e **não corrige** (conduto); é defense-in-depth contra violação de contrato do Classifier, não o caminho nominal (o Classifier emite token ou `null`, nunca prosa).

### 2.2 Construção do prompt pelo coordinator

```python
# Pseudocódigo do coordinator (autoritativo: coordinator.md §3.4)
prompt = build_matcher_prompt(classifier_output)
async for msg in query(prompt=prompt, options=matcher_agent_definition):
    ...
```

O coordinator monta o prompt com a lista inteira de candidatos. Não há fan-out por candidato no nível do coordinator — o fan-out (candidato × cláusula) acontece dentro da sessão do Matcher, via o loop de §4.3.

### 2.3 Postura de validação: `extra='ignore'` no recebido + projeção (DD-M11, fecha DD-C9)

O Matcher adota **`extra='ignore'`** sobre o `ClassifiedCandidate` recebido. Razão: manter adição de campo no Classifier **não-breaking** — é a premissa do bump-minor registrada em `classifier.md` §7.1. Antes de invocar `check_applicability`, o Matcher **projeta** o `structured_context` do Classifier para o input que a tool aceita — e a projeção é um **rename + drop**, não um subset de campos homônimos (correção C1):

```python
# projeção structured_context (Classifier) → input de check_applicability (tool)
tool_input = {
    "data_categories": sc["data_categories"],           # mesmo nome
    "operation": sc["operation_type"],                  # RENAME operation_type → operation
    "legal_basis": sc.get("declared_legal_basis"),      # RENAME declared_legal_basis → legal_basis
    # declared_transformations: DROP (a tool não o aceita)
    # destination: não existe no output do Classifier — não há o que projetar
}
```

O input da tool é `ConfigDict(extra='forbid')` (`canonical.md` §4.3): um campo a mais → `ValidationError` server-side, daí o drop de `declared_transformations`. As duas posturas são distintas e deliberadas: **tolerante** no recebido (evolução do Classifier), **estrita** no enviado à tool. **Antes da projeção**, o Matcher aplica o curto-circuito de contexto insuficiente (§4.4 / C2): se `operation_type is None` ou `data_categories == []`, não projeta nem chama a tool.

### 2.4 Princípio: o Matcher julga via tool, não improvisa (DD-M26)

O Matcher **não** lê o texto da cláusula para decidir conformidade, **não** reproduz a lógica de `applies_to`/`control` no raciocínio do modelo, e **não** gera prosa de veredito própria. A descrição de `check_applicability` é explícita (`canonical.md` §4.3 l.506): *"Do not attempt to reproduce this evaluation in agent reasoning."* O veredito, a `evidence`, o `reason` e o `verification_scope` são **gerados pela tool**; o Matcher os propaga verbatim. Esta é a separação de planos epistêmicos que sustenta o DD-21 e as regras imutáveis #1 (no-fabricated-certainty) e #2 (citação de `clause_id`). É o invariante load-bearing protegido por toda a spec.

### 2.5 Caminho upstream e lista vazia

Se o `classifier_output` for vazio (nenhum candidato sobreviveu ao Classifier), o Matcher emite `findings: []`. O caminho skip (Triager → Reporter, sem Detector/Classifier/Matcher) não chega ao Matcher — é resolvido pelo coordinator (ver `reporter.md` §2.3).

---

## 3. Output contract

### 3.1 Shape canônico do finding

Cada finding casa o schema de `reporter.md` §3.2 (vinculante — o output do Matcher **é** o input do Reporter):

```python
{
    # passthrough (identidade do locus) — verbatim do Detector
    "file": "<path>",
    "line": <int>,
    "snippet": "<código>",
    "rule_id": "<id da regra do Detector>",

    # contexto (passthrough do Classifier — operation_type é o nome real, DD-M10)
    "data_categories": ["<token>", ...],   # passthrough verbatim
    "operation_type": "collection",        # passthrough do Classifier (MVP: só collection chega a verdict)

    # veredito (verbatim de check_applicability)
    "verdict": "compliant" | "violation_candidate" | "indeterminate" | "not_applicable",
    "policy_clause_ref": "POL-NNN",        # SEMPRE presente nos 4 vereditos (DD-21)
    # + campos variantes por verdict (ver §3.2)

    # escalação humana (originado pelo Matcher, DD-M29)
    "requires_human_review": <bool>,       # opcional

    # provenance (trinca verbatim de check_applicability, DD-M23)
    "policy_schema_version": "0.1.0",
    "policy_version": "0.1.0",
    "legal_framework": "LGPD",
}
```

**Zero `candidate_ref` (DD-M19/M9).** O finding **não** carrega `candidate_ref`. A identidade do par é `(file, line, rule_id)` + `policy_clause_ref`. O `candidate_ref` que existia em `architecture-overview.md` §5.5 era stale e foi removido (Beat 2, #48). O output de `check_applicability` (`canonical.md` §4.3 l.540-583) **não** o emite.

### 3.2 Os quatro vereditos e seus campos variantes

Discriminados por `verdict`, mutuamente exclusivos (`canonical.md` §4.3 l.579-585). Todos os campos de prosa são **gerados pela tool** (§2.4):

| `verdict` | Significado | Campo(s) variante(s) |
|---|---|---|
| `compliant` | handling consistente com os requirements da cláusula | `evidence` |
| `violation_candidate` | handling **aparenta contradizer** a cláusula | `evidence` + `contradicted_requirement` (e.g. `R1`) |
| `indeterminate` | análise estática **não conclui** uma dimensão | `verification_scope {dimension, prescribed_treatment, verification_target}` |
| `not_applicable` | a cláusula **não governa** este handling | `reason` |

**Os três sub-casos de `not_applicable`** (`canonical.md` §4.3 l.585), distinguidos pela prosa de `reason`:
- **(i) escopo MVP** — `operation ≠ collection` → `not_applicable` antes do matching (ADR-0007 D3). **Enforçado pelo motor** (verificado #48, T3/T3b): tanto `storage` quanto `disclosure_by_transmission` retornam `not_applicable` com `reason` "fora do escopo MVP".
- **(ii) applicability mismatch** — `clause.applies_to` não intersecta o context em ≥1 dimensão.
- **(iii) definitional** — `clause_id` aponta para cláusula `definitional` (POL-000): declara vocabulário, não governa contexto operacional.

**`indeterminate` é cláusula-vinculado.** `verification_scope.prescribed_treatment` nomeia *o tratamento prescrito pela cláusula* — logo `indeterminate` pressupõe uma cláusula governante com tratamento prescrito. Uma **lacuna de cobertura** (handling com dado, nenhuma cláusula governante) **não** é `indeterminate`: não há `prescribed_treatment`. Ver §4.4 (DD-M8).

### 3.3 Encoding do `output_format` — enum-tag, nunca `oneOf` (DD-M13)

O `output_format` da invocação do Matcher codifica o finding como **objeto enum-tag**: `verdict: Literal[...]` + os campos variantes como opcionais `anyOf [T, null]` — **nunca** `oneOf` / discriminated-union no nível de schema, que desliga silenciosamente a gramática de structured output (DD-T16, `sdk_output_format_complex/RESULTS.md`). O "discriminated union" semântico de `reporter.md` §3.2/§9.3.f é o modelo **Pydantic de validação** do handler do Reporter (camada posterior), não a gramática wire-level.

**Orçamento de complexidade (verificado #48, doc Structured outputs):** máximo de **24 parâmetros opcionais** e **16 parâmetros de união** (`anyOf`/type-arrays) por schema strict; timeout de compilação 180s. O padrão enum-tag é opcional-pesado e união-pesado por construção (cada campo por-verdict é `anyOf[T,null]`) — **contar** os opcionais/uniões no schema do item de finding + envelope do Report e achatar/`required` onde der para ficar sob os limites.

### 3.4 Cardinalidade (DD-M6)

`len(findings) ≥ candidates_count`, sem invariante de igualdade. Re-derivada do mecanismo check-all (DD-M1, Beat 2 aplicado a `reporter.md` §2.2): o Matcher emite **um finding por par candidato-cláusula** sobre as cláusulas `active` do catálogo. Como POL-000 (`active`, definitional) está sempre no sweep, todo candidato recebe ≥1 finding (`not_applicable` definitional no mínimo) — garantindo o piso de cardinalidade e `policy_clause_ref` válido sem chamada especial (§4.4 / DD-M4).

### 3.5 Ordem de emissão — determinística (DD-M25)

Findings emitidos em ordem **determinística pretendida**: candidato (ordem do `classifier_output`, que preserva a ordem do Detector, que preserva o diff do Semgrep) × cláusula (ordem natural do catálogo por `clause_id`). O Reporter **não** re-sorta (`reporter.md` §3.4 l.287/289); a ordem upstream é determinística por construção. **Caveat de garantia (M-c):** o veredito **do motor** para um dado input é determinístico (templates f-string, não prosa gerada — verificado #48); mas **enumerar** todo par candidato×cláusula em ordem e **copiar** cada campo verbatim é comportamento do agente LLM, não garantia estrutural (o §5.3 admite que a fidelidade "pode degradar"). O mecanismo que *tornaria* a ordem/completude enforçável é a validação coordinator-side de que todo par `(candidato × cláusula-active)` está presente (reforçaria AC-M7/AC-M8) — **não implementada no MVP**, registrada como follow-up. Determinismo audit-replayable é o **alvo**; a enforçabilidade é coordinator-side.

### 3.6 `requires_human_review` — origem e regra (DD-M29)

Campo **originado pelo Matcher** (não vem de `check_applicability`; o output da tool não o carrega — `canonical.md` §4.3 l.540-583). Semântica: **"merece atenção humana / fila de revisão"**, NÃO "o sistema não decidiu" — é ortogonal à confiança do veredito. Regra determinística:

```
requires_human_review = True  quando:
    verdict ∈ {indeterminate, violation_candidate}
    OU (verdict == not_applicable E lacuna-de-cobertura: §4.4)
    OU (verdict == not_applicable E contexto-insuficiente: §4.4, curto-circuito C2)
```

`violation_candidate` é um flag *confiante* (aparenta violar → humano confirma); `indeterminate` já carrega a incerteza epistêmica em `verification_scope`; a lacuna-de-cobertura sinaliza necessidade de evolução da Política. O Reporter propaga verbatim (`reporter.md` l.326: ausência ≠ `false`). Fecha o forward-ref pré-registrado em `reporter.md` §3.2 l.825 (catch R2-G5).

---

## 4. Mecanismo de avaliação

### 4.1 Tools e resources consumidos

| Capacidade | Tipo | Uso no Matcher |
|---|---|---|
| `policy://catalog` | resource | **Enumeração** das cláusulas (`{clause_id, status, ...}`); filtra `status=="active"` client-side (DD-M1). |
| `policy://vocabularies` | resource | Contexto léxico. Candidato a vestigial no caminho de veredito (matching é server-side); **ADR-pinado** (D4), não removível sem emenda (DD-M27). |
| `check_applicability(clause_id, structured_context)` | tool | **Avaliação** — produz o veredito. Eixo do mecanismo. |
| `get_clause(clause_id)` | tool | Lookup de cláusula (auditoria; lookup de sucessor em deprecated — §6.5). |
| `find_clauses_by_law_article(lei, artigo)` | tool | **Autorizada, fora do caminho de seleção** (DD-M2). Insatisfazível pelo input do Matcher (sem `{lei, artigo}` no `structured_context`); mantida por estar referenciada em múltiplos docs desde a proposta original — remoção exige investigação dedicada (fora de escopo #48). |

O **catálogo é a fonte de enumeração** porque é o único resource que lista cláusulas; o catálogo **não** carrega `applies_to` (só os campos de índice), logo todo o matching de aplicabilidade fica dentro de `check_applicability` (consistente com o mecanismo A). Verificado #48.

### 4.2 AgentDefinition

Além da quíntupla canônica (`coordinator.md` §3.4):

- **`tools` field (DD-M30, verificado #48-b):** deve incluir os **built-ins de resource** `ReadMcpResourceTool` e `ListMcpResourcesTool`. O `tools` field governa os built-ins visíveis, e a #48-b mediu os três estados lado a lado contra o `policy-reader` real: sob `tools=[]` **e** sob `tools=["Read"]` o `ReadMcpResourceTool` está **ausente** (o modelo verbaliza "ReadMcpResourceTool is not available"; só os `mcp__policy-reader__*` sobrevivem, via `mcp_servers`); só sob `tools=["Read", "ReadMcpResourceTool", "ListMcpResourcesTool"]` (ou com o field omitido, pagando 1 turn de ToolSearch) o catálogo é lido. **Dois eixos ortogonais:** server tools (`mcp__*`) governados por `mcp_servers` sobrevivem a `tools=[]`; built-ins de resource governados pelo `tools` field **somem** com `tools=[]`. Logo `tools=["Read", "ReadMcpResourceTool", "ListMcpResourcesTool"]`. **Consequência cross-doc:** o `tools=[]` que o `coordinator.md` §3.4 (l.155, pivô do Gate 6) declara para o Matcher **quebra o check-all** — o Gate 6 estava certo para o Reporter (`emit_report` é server tool, visível sob `tools=[]`) e errado para o Matcher; e a afirmação de `classifier.md:45` ("Matcher lê resource sob `tools=[]` sem conflito") é **defeito empírico**. Ambos são companion edits (§10.5).
- **`allowed_tools`:** `mcp__policy-reader__check_applicability`, `mcp__policy-reader__get_clause`, `mcp__policy-reader__find_clauses_by_law_article`.
- **`mcp_servers`:** `{policy-reader: ...}`. O grant de resource é per-server (verificado #48, Check B: `ReadMcpResourceTool` alcança `policy://catalog` sob grant bare — **desde que** o built-in esteja no `tools` field, ver acima). A concessão de catalog ao Matcher é afirmação positiva de `canonical §1/§3.1` (resources consumidos pelo Matcher), não inferência por silêncio de D4 — D4 governa só a fronteira tools-exclusivas (correção M2).
- **`output_format`:** schema enum-tag do finding (§3.3). **Companion edit pendente** ao `coordinator.md` §3.4 (ausente hoje — item 1 da #47; DD-M15).
- **`max_turns = 30` (DD-M14):** A check-all é call-heavy — o número de chamadas é **`N × (C+1)`** (N candidatos × cláusulas active, +1 pela POL-000 sempre presente), não só função do catálogo: no MVP bundled `C=0` (só POL-000), logo o fator dominante é **N** (contagem de candidatos), não o tamanho do catálogo. 30 dá folga a N pequeno; **recalibrar empiricamente** quando N ou as substantivas per-client crescerem — o piso real depende de quantas chamadas `check_applicability` o modelo agrupa por turn (blocos `tool_use` paralelos), **não medido**. A migração para `find_clauses_by_applicability` (DD-M3) corta de N×C para N×K.

### 4.3 O loop check-all (DD-M1)

```
1. (startup do prompt) ler policy://catalog E policy://schema-version via ReadMcpResourceTool
   → de catalog: enumerar cláusulas; manter as de status == "active"   [POL-000 está entre elas]
   → de schema-version: reter a trinca {policy_schema_version, policy_version, legal_framework}
     (fonte da trinca do finding de curto-circuito — §4.4/§7.3/R1)

2. para cada candidato em classifier_output:
   a. (curto-circuito C2, §4.4) se operation_type is None OU data_categories == []:
        emitir UM finding not_applicable(POL-000) + requires_human_review=True
        (reason: "contexto insuficiente"); NÃO chamar a tool; próximo candidato.
   b. projetar structured_context → tool_input  (§2.3: operation_type→operation,
        declared_legal_basis→legal_basis, drop declared_transformations)
      (opcional, DD-M5) se operation_type != "collection": o motor retorna not_applicable
        de qualquer forma — pré-filtro local é otimização de custo/ruído, não correção.
   c. para cada clause_id em cláusulas_active:        [inclui POL-000 → backstop, §4.4]
        verdict = check_applicability(clause_id, tool_input)
        (se errorCode == CLAUSE_DEPRECATED: retry no successor — §6.5; raro sob sweep active-only)
        montar finding(candidato, clause_id, verdict)   (§3.1, §4.4 para gap/requires_human_review)

3. emitir findings em ordem determinística (§3.5) via output_format enum-tag (§3.3)
```

**Mecanismo A é interino e explícito (DD-M3).** A é determinística, não reproduz a avaliação no modelo (§2.4), e a C=0 bundled é trivial. O mecanismo *correto* a prazo é uma tool server-side `find_clauses_by_applicability(data_categories, operation) -> list[clause_id]` (filtra `applies_to` no servidor), registrada como **forward-ref obrigatório** à spec do `policy-reader`. O swap A → `find_clauses_by_applicability` quando chegarem cláusulas substantivas per-client é **bump de `spec_version`**, não mudança silenciosa.

### 4.4 Lógica de veredito e lacuna de cobertura (DD-M4 / DD-M8)

**Backstop POL-000 = o próprio sweep (DD-M4).** POL-000 é `active` e está no catálogo, logo **já é avaliado** no loop. Sendo definitional, sempre retorna `not_applicable` (sub-caso iii). Isto **é** o backstop — não há chamada POL-000 especial nem adicional (uma chamada separada duplicaria o finding POL-000 por candidato). A C=0 bundled, o sweep `= {POL-000}` é exatamente o backstop, automático.

**Lacuna de cobertura → `not_applicable` + `requires_human_review` (DD-M8).** Um candidato com `data_categories` não-vazio, `operation == collection`, e **nenhuma cláusula substantiva governante** (todas `not_applicable`, restando só POL-000) é uma **lacuna de cobertura da Política**. O veredito por-finding permanece `not_applicable` (estruturalmente honesto — `indeterminate` exigiria `prescribed_treatment` que a lacuna não tem; §3.2), **mas** o Matcher seta `requires_human_review=True` (§3.6) e o `reason` descreve a lacuna. Não é silencioso, não é `indeterminate`: é o sistema apontando a própria necessidade de evolução, no nível certo (escalação humana), não forjando um veredito.

Verificado #48 (probe §5): `applies_to` é interseção de conjuntos pura, **sem catch-all** (`[]` e `["*"]` ambos → `not_applicable`). Logo o sinal de lacuna **pertence ao Matcher** (detecta "nada casou" via o agregado de vereditos), não a uma cláusula. O sub-caso "sem base legal declarada" pode adicionalmente ser pego como `violation_candidate` por uma cláusula-base `consent_required` (verificado #48, T2) — decisão de **conteúdo de Política** de João, não do Matcher.

**Contexto insuficiente: `operation_type: null` ou `data_categories: []` (correção C2).** Ambos são **saídas válidas** do Classifier (`classifier.md` §3.3 — `operation_type` é `Optional`, contexto ambíguo; `data_categories: []` em contexto genérico), **não** violações de contrato. Mas a tool os rejeita: `operation_type: null`/ausente → `INVALID_OPERATION`; `data_categories: []` → `EMPTY_DATA_CATEGORIES` (verificado #48-b, casos C2a/C2b/C2c — todos errorCode de domínio via Option B, antes do `model_validate`). Como a tool não consegue produzir veredito para contexto sub-especificado, o Matcher **curto-circuita localmente** (§4.3 passo 2a): emite **um** finding `not_applicable` com `policy_clause_ref=POL-000` + `requires_human_review=True` + `reason` explícito de "contexto insuficiente para avaliação (operação ambígua / nenhuma categoria identificada)" — **sem** chamar a tool. Isto fecha a parte (a) de DD-C9 (degradação graciosa que o `classifier.md:175` pré-registrou).

**Fonte da trinca no finding de curto-circuito (correção R1).** A trinca de provenance é obrigatória em **todo** finding (`reporter.md:225-227`, AC-M11) e o Reporter faz cross-check top-level == per-finding (`reporter.md:285`). O finding de curto-circuito não tem retorno de tool de onde propagá-la — então **fonta a trinca de `policy://schema-version`** (que o Matcher já lê — §1.1 — e que **inclui** `{policy_schema_version, policy_version, legal_framework}` além de `compatible_schema_range`, `server.py:132-137`; o Matcher seleciona só os três da trinca). Como é a **mesma Política carregada**, os valores igualam o top-level → o cross-check de `reporter.md:285` passa. Isto dá ao read de `schema-version` em §1.1 um uso concreto: deixa de ser "lê mas não usa" e vira a fonte de trinca do único caminho originado pelo Matcher.

> **Ressalva de conduto (carve-out de DD-M26).** Este `not_applicable` é **originado pelo Matcher**, não propagado da tool — é a única exceção à fidelidade de conduto, ao lado do próprio `requires_human_review`. É legítimo porque NÃO é um juízo de conformidade fabricado: é um sinal de "**não avaliável**", deliberadamente distinto do `not_applicable` da tool ("a cláusula não governa"), e o `reason` o desambigua. O Matcher não inventa `compliant`/`violation_candidate`; só reporta honestamente que não pôde avaliar.

### 4.5 Coordinator captura

```python
# Pseudocódigo do coordinator (autoritativo: coordinator.md §3.4)
async for msg in query(prompt, options=matcher_agent_definition):
    if isinstance(msg, ResultMessage):
        findings = msg.structured_output   # validado contra o schema do finding
```

Erros de `check_applicability` chegam no stream como envelopes **Option B**: `isError=False` + `errorCode` em `structuredContent` (§6.2). Discriminar por **presença de `errorCode`**, nunca por `isError`.

---

## 5. System prompt

### 5.1 Texto canônico

> Você é o **Matcher** de um sistema de revisão de conformidade LGPD. Para cada candidato de tratamento de dados pessoais que você recebe, sua tarefa é **avaliar conformidade contra a Política**, emitindo um veredito por cláusula através da tool `check_applicability`.
>
> **Você julga exclusivamente via tool.** Você NÃO lê o texto da cláusula para decidir; NÃO reproduz a lógica de aplicabilidade ou de controle no seu raciocínio; NÃO inventa veredito, evidência, motivo ou escopo de verificação. O veredito e toda a sua prosa (`evidence`, `reason`, `verification_scope`) são produzidos por `check_applicability` — você os propaga **verbatim**, sem alterar, resumir ou reinterpretar. Se você se vir "raciocinando se a cláusula se aplica", pare: essa é a função da tool.
>
> **Mecanismo (check-all):**
> 1. Leia os resources `policy://catalog` e `policy://schema-version`. De `catalog`, considere apenas as cláusulas com `status == "active"`. De `schema-version`, retenha a trinca de provenance (`policy_schema_version`, `policy_version`, `legal_framework`) — você vai precisar dela para o finding de curto-circuito do passo 2 (que não chama a tool e portanto não tem trinca de onde copiar).
> 2. Para cada candidato, **antes de avaliar**: se `operation_type` for nulo/ausente, ou se `data_categories` for lista vazia, **não** chame a tool — emita um finding `not_applicable` (POL-000) com `requires_human_review: true` e `reason` de "contexto insuficiente", e siga para o próximo candidato.
> 3. Caso contrário, monte o input da tool **renomeando** os campos do candidato para o contrato de `check_applicability`: `operation_type` → `operation`, `declared_legal_basis` → `legal_basis`, `data_categories` igual; **descarte** `declared_transformations`. Os valores já vêm como tokens canônicos do Classifier; não os traduza para prosa.
> 4. Para cada cláusula ativa (incluindo POL-000), chame `check_applicability(clause_id, tool_input)` e registre o veredito retornado como um finding.
>
> **Tokens, não prosa.** `legal_basis` deve ser um token canônico (ex.: `consent`, `legitimate_interests`), nunca texto livre — o motor compara por igualdade exata contra o token.
>
> **Escopo MVP.** Somente `operation: collection` é avaliada; a tool retorna `not_applicable` para outras operações. Você não precisa filtrar previamente, mas pode pular a varredura de um candidato cuja `operation_type` não seja `collection` (otimização).
>
> **Escalação humana.** Marque `requires_human_review: true` quando o veredito for `indeterminate` ou `violation_candidate`; quando o candidato tiver dado pessoal mas **nenhuma cláusula substantiva** o governar (só POL-000 retornou `not_applicable`) — lacuna de cobertura; ou no caso de contexto insuficiente do passo 2. `requires_human_review` significa "merece olho humano", não "não decidi".
>
> **Erros da tool.** Um retorno com `errorCode` em `structuredContent` é erro de domínio (mesmo com `isError: false`). Para `CLAUSE_DEPRECATED`, reavalie sobre o `successor` indicado. Se você seguiu o passo 2, não verá `INVALID_OPERATION`/`EMPTY_DATA_CATEGORIES` por contexto **ausente**. Mas atenção: `INVALID_OPERATION` ou `INVALID_DATA_CATEGORY` com um valor **presente porém fora do vocabulário** (não nulo) é um candidato malformado — **não** o curto-circuite como "contexto insuficiente"; reporte a falha, não fabrique veredito de conformidade.
>
> Emita os findings na ordem em que iterou (candidato × cláusula). Não reordene.

### 5.2 Behaviors explícitos

- Propaga veredito e prosa da tool **verbatim** (conduto, DD-M26).
- Itera candidatos na ordem recebida; cláusulas na ordem do catálogo (DD-M25).
- Usa tokens canônicos; nunca prosa em `legal_basis` (DD-M11).
- Seta `requires_human_review` pela disjunção de §3.6 (DD-M29).
- Não persiste, não classifica, não detecta (§8.1).

### 5.3 Few-shot — nota meta

Exemplos few-shot de chamada de tool / montagem de finding podem ser adicionados ao prompt se a fidelidade de propagação degradar em teste (estratégia análoga ao Classifier §5.3). Devem usar tokens canônicos e cobrir os quatro vereditos + o caso de lacuna. Não-MVP enquanto a Política bundled for só POL-000.

---

## 6. Error handling

### 6.1 Estrutura canônica — dois eixos (DD-M17)

O §6 do Matcher trata **dois eixos** de erro:
- **(a) Erros consumidos de `check_applicability`** (domínio do `policy-reader`) — §6.2.
- **(b) Erros de stage do próprio Matcher** (orquestração / contrato do subagente) — §6.4.

### 6.2 Erros consumidos de `check_applicability` (Option B)

Discriminados por **presença de `errorCode` em `structuredContent`**, com `isError: false` em TODOS os retornos (Option B, ADR-0002; `.claude/rules/sdk-mcp-conventions.md`). **Nunca** discriminar por `isError` (sempre `false` — perderia o erro). Ler `errorCode` em `tool_use_result.structuredContent` da `UserMessage`, não no `content` do `ToolResultBlock` (que é só a string JSON).

| `errorCode` | Classe | `isRetryable` | Tratamento no Matcher |
|---|---|---|---|
| `INVALID_CLAUSE_ID_FORMAT` | validation | false | Bug de enumeração — não deveria ocorrer com IDs do catálogo. Falha alto. |
| `CLAUSE_NOT_FOUND` | business | false | Cláusula sumiu entre catálogo e chamada — falha alto. |
| `CLAUSE_DEPRECATED` | business | **true** | Retry no `successor` de `details.successors` (§6.5). |
| `INVALID_DATA_CATEGORY` | validation | false | Token de categoria fora do vocab — violação de contrato real do Classifier (não é o caso `[]`, que é curto-circuitado em §4.4). Falha alto. |
| `INVALID_OPERATION` | validation | false | **Dois sub-casos:** (a) `operation_type` **null/ausente** que escapou ao curto-circuito de §4.4 → tratar como contexto insuficiente, não fabricar veredito; (b) `operation_type` **token não-nulo fora-de-vocab** (Classifier emitiu lixo, ex.: `"collecting"`, em vez de `null`) → **violação de contrato real, falha alto** — simétrico a `INVALID_DATA_CATEGORY`. O curto-circuito (`is None`) **não** pega (b). |
| `EMPTY_DATA_CATEGORIES` | validation | false | Idem para `data_categories: []` — **saída válida do Classifier**, curto-circuitada em §4.4 antes da chamada; se chegar aqui, é o curto-circuito que falhou, não violação upstream. |

Verificado #48 (T7/T8/T9): os três retornaram `is_error=False` + `errorCode` em `structuredContent`; `CLAUSE_DEPRECATED` com `isRetryable: true` + `details.successors`.

### 6.3 Família de `ResultMessage.subtype` e `stop_reason`

Discriminação dupla `subtype` × `stop_reason` no caminho de terminação, **espelhando `classifier.md` §6.3 e `triager.md` §6.3** (acesso direto a `ResultMessage.stop_reason` em Python: `message.stop_reason == "refusal"`). **NÃO** repetir o caveat "TS-only" de `detector.md` §6.3 (stale — pendente de remoção, item 4; o acesso direto é a posição do projeto, confirmada na doc `agent-sdk/agent-loop` citada pelo Triager). Refusal → `SubagentRefusedTask`.

### 6.4 Erros de stage e hierarquia de exceções (DD-M18)

Erros de stage: `SubagentRefusedTask` (refusal), `SubagentValidationFailed` (output não casa o schema), `SubagentContractViolation` (violação do próprio contrato — e.g., reordenou/dropou passthrough), turns-exhausted.

**Hierarquia: base compartilhada `SubagentToolError`** (não exceção-irmã independente). Razões: é o padrão do próprio `claude-agent-sdk` (`ClaudeSDKError` base + subclasses, catch-all pela base — verificado #48); idioma Python para família de erros; é o padrão já estabelecido no codebase (`DetectorScanFailed` é **irmã** sob essa base via DD-D5 — não é a base); e baixo-risco porque o controle retry-vs-escalate se decide por `isRetryable`, não pelo tipo (`coordinator.md` §5 l.330). Locus provável `src/coordinator/errors.py`; promoção a ADR-0013 como follow-up. Defer registrado em `coordinator.md` §5 l.332-338. A reconciliação das classes de stage com as tabelas dos outros subagentes é **grep por nome, não por §-âncora** (numeração não-paralela entre specs — `coordinator.md` §5 l.344).

### 6.5 Retry de `CLAUSE_DEPRECATED` (DD-M7)

Em `CLAUSE_DEPRECATED`, reavaliar sobre o `successor` de `details.successors` (`get_clause` não é necessário — o `successor` já é um `clause_id`), bounded para evitar cadeia infinita. **Nota:** sob o sweep enumerando só cláusulas `active`, deprecated não entra na varredura normal — este caminho é defensivo (um `successor` que por acaso seja avaliado), raramente quente.

### 6.6 Casos que parecem erro mas não são

- **`not_applicable` em massa** não é erro — é o comportamento esperado para candidatos fora de escopo MVP ou sem cláusula governante (§4.4). O Reporter sumariza via `summary.counts`.
- **`operation_type: null` / `data_categories: []`** **não** são malformação — são saídas válidas do Classifier (`classifier.md` §3.3). O Matcher os curto-circuita para `not_applicable` + `requires_human_review` (§4.4 / C2), não os trata como violação upstream nem chama a tool com eles. **`INVALID_DATA_CATEGORY`** (token genuinamente fora do vocab) **é** violação de contrato real — falha alto.
- **Nota stale (M1):** `classifier.md:175` / DD-C9 pré-registraram a expectativa de "degradação graciosa para `not_applicable`/`indeterminate`" para valor fora-de-vocabulário. O motor real **rejeita hard na validação** (`INVALID_DATA_CATEGORY`/`INVALID_OPERATION`), antes do matching — a expectativa do Classifier está stale. Companion edit a `classifier.md` §3.3/DD-C9 (§10.5).
- **Falso `violation_candidate` por prosa em `declared_legal_basis`** (§2.1) é sintoma de contrato quebrado do Classifier (token não-normalizado), não erro do Matcher — defense-in-depth, não caminho nominal.

---

## 7. Provenance e versionamento

### 7.1 Versão da spec

`spec_version: 0.1.0`. Convenção major/minor/patch (`reporter.md` §7.1). Bump aplicável ao estado mergeado, não em-revisão. O swap de mecanismo de seleção (A → `find_clauses_by_applicability`, DD-M3) é bump documentado.

### 7.2 Versão do schema

`policy_schema_version` consumido verbatim do retorno da tool / da Política carregada. O Matcher **não** valida `compatible_schema_range` — esse fail-fast estrutural é enforçado no boot do `policy-reader` (`loader.py`; §8.4 / DD-M22).

### 7.3 Trinca de provenance jurídico-temporal (DD-M23)

Diferente do Triager e do Classifier (que **não** emitem trinca), o Matcher **propaga** `(policy_schema_version, policy_version, legal_framework)` **verbatim** do retorno de `check_applicability`, por finding — **nunca recomputa**. **Exceção (R1):** no finding de curto-circuito de contexto insuficiente (§4.4), que não chama a tool, a trinca vem verbatim de `policy://schema-version` (mesma Política → mesmos valores; o cross-check do Reporter passa). Em nenhum caminho o Matcher recomputa. Presente per-finding **e** top-level no Report (redundância deliberada, `reporter.md` §3.3; RF-009). Verificado #48: todos os outputs de sucesso da tool carregam a trinca.

### 7.4 Mutabilidade durante execução

A Política é imutável durante a sessão do `policy-reader` (carregada no boot). O catálogo, os vocabulários e os vereditos são estáveis dentro de um run. Reload exige restart do server.

---

## 8. Não-objetivos e fronteiras

### 8.1 Não-objetivos do Matcher

- **Não classifica** (não atribui `data_categories`/`operation` — isso é do Classifier; o Matcher consome).
- **Não detecta** (não localiza candidatos — isso é do Detector).
- **Não persiste** (sem dual sink; persistência é do coordinator).
- **Não decide seleção "most-specific-wins"** no MVP — o check-all avalia todas as cláusulas aplicáveis (lex specialis seria lógica adicional do Matcher, não comportamento da tool; verificado #48, T6: cláusulas são avaliadas em isolamento).
- **Não valida jurisdição (handshake)** no MVP — descartado por YAGNI co-versionado; o eixo estrutural já é server-side (§8.4/DD-M22).
- **Não corrige sub-modelagem do motor** (conduto — §8.3).

### 8.2 Não-objetivos do escopo

MVP v0.1.0: somente `operation: collection`; somente o framework `LGPD` carregado; Política bundled = só POL-000 (substantivas são autoradas per-client).

### 8.3 Fronteira epistêmica

O Matcher é **conduto fiel** de `check_applicability` (DD-M26). Ele reporta o que o motor decide, incluindo as **sub-modelagens conscientes** do MVP — não as conserta nem as mascara. Em particular (§8.4): o motor compara `consent_required` por token único contra `consent` e **não** consome o campo `category` (`personal_data` vs `sensitive_data`) de `lawful_basis`, logo trata dado sensível (Art. 11) com a régua de dado comum. A spec descreve o comportamento real; o gap é débito documentado, não bug escondido.

### 8.4 Decisões deferidas e débitos

- **DD-M3 — `find_clauses_by_applicability`** (forward-ref ao `policy-reader`): mecanismo de seleção correto a prazo; A é interino. Migração = bump de `spec_version`.
- **DD-M22 — handshake jurisdicional: descartado em sede de MVP (YAGNI), não "agnóstico" (correção H1).** Verificado #48-b contra a impl: o eixo **estrutural** (`compatible_schema_range`) tem dono server-side (`loader.py:102/168`, aborta o boot — o handshake que previne erro *real*); o eixo **jurisdicional** (`legal_framework`) está **genuinamente sem dono** (probe de boot com `synthetic_gdpr` bootou normal; grep em todo `src/` mostra zero comparação-e-abort; `src/coordinator/` não existe — Milestone C). No MVP **co-versionado** (servidor, Política e consumidor no mesmo release, Política única LGPD), um check `legal_framework == "LGPD"?` **sempre passa** — não previne erro alcançável (YAGNI, mesmo critério de DD-M3). Quando a arquitetura multi-client de ADR-0005 materializar, o handshake jurisdicional é um **check determinístico no código Python do coordinator** (um `if framework not in ACCEPTED: abort` no boot, antes do fan-out) — **não** lógica de agente no Matcher (preserva DD-M26). O Matcher **lê** `policy://schema-version` (§1.1) e propaga `legal_framework` verbatim (DD-M23), mas não valida. **Dívida datada e inalcançável agora:** se um `policy-reader` de framework X fosse apontado a um consumidor que espera Y, nada barraria — inatingível no MVP co-versionado. **Companion edits** (§10.5): `canonical §3.2/§6.3` (que atribuem o handshake ao Matcher) e o rótulo "framework-aware" de `arch §5.5` — anotar o defer, não negar o contrato.
- **Débito jurídico — `category` não-consumido (Art. 11)**: o motor não distingue base de dado comum vs sensível. Sub-modelagem MVP consciente; forward-ref a evolução pós-MVP (engine consome `category`). Registrado em `docs/tasks.md`.
- **`find_clauses_by_law_article` órfã de seleção** (DD-M2): autorizada mas sem uso no caminho de veredito; remoção pende investigação dedicada (fora de escopo #48).

---

## 9. Critérios de aceitação

> Espelham o comportamento **verificado contra o motor** no smoke-test #48 (in-memory `fastmcp.Client`, não persistido em dir) e #48-b (`scripts/smoke_tests/check_applicability_48b/`, persistido).

### 9.1 Happy-path
- **AC-M1.** Candidato `collection` + `dados_de_identificacao` + `legal_basis: consent` contra cláusula `consent_required` → finding `compliant` com `evidence` da tool. (T1)
- **AC-M2.** Mesmo candidato sem `legal_basis` → `violation_candidate` com `contradicted_requirement`. (T2)

### 9.2 Edge cases
- **AC-M3.** `operation_type != collection` → `not_applicable` (sub-caso i), sem matching. (T3/T3b)
- **AC-M4.** Cláusula cujo `applies_to` não intersecta o context → `not_applicable` (sub-caso ii). (T4)
- **AC-M5.** POL-000 (definitional) → `not_applicable` (sub-caso iii); presente em todo candidato como piso de cardinalidade. (T5)
- **AC-M6.** Candidato com dado, `collection`, e só POL-000 governando → `not_applicable` + `requires_human_review: true` + `reason` de lacuna. (§4.4)
- **AC-M6b.** Candidato com `operation_type: null` **ou** `data_categories: []` (saídas válidas do Classifier) → o Matcher **curto-circuita**: emite `not_applicable`(POL-000) + `requires_human_review: true` + `reason` de "contexto insuficiente", **sem** chamar a tool. (§4.4 / C2; verificado #48-b C2a/b/c que a tool rejeitaria)

### 9.3 Cross-check
- **AC-M7.** `len(findings) ≥ candidates_count`; um finding por par candidato-cláusula. (§3.4)
- **AC-M8.** Ordem de findings determinística *pretendida* (candidato × catálogo). **Garantido:** o veredito do motor para um input fixo é estável. **Não garantido por construção:** a enumeração/cópia completa pelo agente LLM — enforçável só via validação coordinator-side (§3.5, follow-up). O AC verifica a ordem quando a enumeração está completa, não que ela esteja sempre completa. (§3.5)
- **AC-M9.** Nenhum finding carrega `candidate_ref`; identidade é `(file, line, rule_id)` + `policy_clause_ref`. (§3.1)
- **AC-M10.** Duas cláusulas que casam o mesmo candidato produzem dois findings independentes (isolamento). (T6)

### 9.4 Provenance
- **AC-M11.** Trinca `(policy_schema_version, policy_version, legal_framework)` presente e verbatim em todo finding. (§7.3)

### 9.5 Error scenarios
- **AC-M12.** Se chamada diretamente com `data_categories: []` → tool retorna `EMPTY_DATA_CATEGORIES`; com `operation: null`/ausente → `INVALID_OPERATION` (errorCode em structuredContent, isError:false). O Matcher **não** chega aqui no caminho nominal (curto-circuita — AC-M6b); este AC fixa o comportamento da tool que justifica o curto-circuito. (#48-b C2a/b/c)
- **AC-M13.** Token fora do vocab → `INVALID_DATA_CATEGORY`. (T8)
- **AC-M14.** Cláusula deprecated → `CLAUSE_DEPRECATED` (isRetryable, successors); Matcher reavalia no successor. (T9)
- **AC-M15.** Refusal → `stop_reason == "refusal"` detectado direto em Python; `SubagentRefusedTask`. (§6.3)

---

## 10. Cross-references

### 10.1 Source-of-truth artifacts
- `docs/specs/policy-reader/canonical.md` §3.1 (catalog), §3.2 (schema-version), §3.3 (vocabularies), §4.3 (`check_applicability` — contrato, output, sub-casos, erros), §5 (contrato de erro), §6.4 (provenance).
- `docs/specs/subagents/reporter.md` §2.2 (estado consolidado + cardinalidade), §3.2 (shape do finding — **vinculante**), §3.3 (provenance), §3.4 (ordering).
- `docs/specs/subagents/classifier.md` §2/§3 (`structured_context` consumido), §7.1 (postura `extra` / DD-C9).
- `docs/specs/subagents/detector.md` §3.1 (passthrough `DetectorFinding`).
- `docs/specs/subagents/coordinator.md` §3.4 (invocação — companion edits pendentes), §5 (hierarquia de exceções).
- `docs/architecture-overview.md` §3, §5.5, §5.7 (Beat 2 aplicado #48).
- `.claude/rules/sdk-mcp-conventions.md` (Option B; discriminação por `errorCode`).
- `policy/` (Política bundled: `policy.yaml`, `clauses/POL-000.yaml`, `vocabularies/LGPD/*.yaml`).

### 10.2 ADRs aplicáveis
- ADR-0002 (Option B wire format).
- ADR-0005 Decision 4 (tools exclusivas do Matcher — fronteira de capability). O **grant dos resources** (catalog/vocabularies/schema-version) ao Matcher vem de `canonical §1/§3.1` (afirmação positiva), não de D4 (correção M2).
- ADR-0007 Decision 3 (escopo MVP `collection`).
- ADR-0013 (a criar — hierarquia de exceções de subagente; DD-M18).

### 10.3 Gates pré-implementação
- Smoke-test #48 (`check_applicability`, in-memory `fastmcp.Client` — **não persistido em dir**) — 13/13 + probe §5; **passado** (gate fechado).
- Smoke-test #48-b (`scripts/smoke_tests/check_applicability_48b/` — **persistido**) — probes C2/H1/H2; **passado**.
- Beat 2 (M19/M20) aplicado a arch/reporter (sem commit — PR é passo do autor).

### 10.4 DDs status (ledger v3)
Todos ratificados. M1 (check-all/catalog), M2 (find_clauses órfã de seleção, manter), M3 (find_clauses_by_applicability fwd-ref), M4 (backstop = sweep), M5 (pré-filtro = otimização), M6 (cardinalidade re-derivada), M7 (retry deprecated), M8 (gap → not_applicable + requires_human_review), M9 (assembly), **M10 (operation_type é passthrough no finding; rename `operation_type→operation` só na projeção pra tool — invertido na correção C1)**, **M11 (extra='ignore' + projeção rename+drop + tokens reais `operation_type`/`declared_legal_basis`/`declared_transformations`)**, **M12 (out-of-vocab → INVALID_*; nota stale M1 sobre classifier:175)**, M13 (enum-tag + orçamento), M14 (max_turns=30), M15 (companion edit coordinator §3.4), M16 (refusal espelha classifier/triager), M17 (dois eixos de erro), M18 (base SubagentToolError), M19 (drop candidate_ref — **aplicado**), M20 (seleção reconciliada — **aplicado**), M21 (ledger coordinator §10/reporter §10.5), **M22 (handshake jurisdicional descartado MVP por YAGNI; dono futuro = código do coordinator — correção H1)**, M23 (provenance verbatim), M24 (estrutura), M25 (ordem determinística), M26 (fidelidade de conduto + carve-out do not_applicable de contexto-insuficiente), **M27 (grant de resources via canonical §1/§3.1; vocabularies candidato-a-vestigial mas ADR-pinado)**, M28 (system prompt), M29 (requires_human_review — incl. contexto-insuficiente), **M30 (tools field precisa dos built-ins; `tools=[]` os esconde — verificado #48-b)**. **Novo: curto-circuito C2** (operation_type:null/data_categories:[] → not_applicable+requires_human_review) folded em M8/M29.

### 10.5 Companion edits a outros docs
**APLICADO pelo Code (sessão #48, working tree — PR `<branch-da-sessão>`, não commitado).** Achado de raiz: a concepção `tools`-field-não-governa-resource-built-in vivia em 5 loci. A distinção que fecha o assunto, agora cravada em cada um: há **dois tipos de "MCP tool" com governança oposta** — (1) **server tools** (`mcp__policy-reader__*`): governados por `mcp_servers` → **sobrevivem** a `tools=[]`; (2) **built-ins de acesso a resource** (`ReadMcpResourceTool`/`ListMcpResourcesTool`): governados pelo **`tools` field** → **invisíveis** se não listados (#48-b, persistido em `scripts/smoke_tests/check_applicability_48b/RESULTS.md`). O resultado empírico **bateu com DD-M30 exatamente** — nenhuma config precisou ser revista. Loci:

  1. **✅ `coordinator.md` §3.3 — config do Classifier.** `tools=["Read","Grep"]` → `["Read","Grep","ReadMcpResourceTool","ListMcpResourcesTool"]`, com comentário ligando à quebra (#48-b/§10 DD-9.1) e à consequência DD-M11. Era a quebra ativa; resolvida.
  2. **✅ `coordinator.md` §3.4 — config do Matcher.** `tools=[]` → `["Read","ReadMcpResourceTool","ListMcpResourcesTool"]` (Gate 6 vale só pro Reporter); + `output_format` (enum-tag) + `max_turns=30` (DD-M15/M14); tabela DD-9.1 (§2) atualizada.
  3. **✅ `coordinator.md` §3.3 nota "scoped access" + §2 tabela.** Adicionado o caveat availability ≠ capability (`mcp_servers` concede alcance; o built-in só fica visível se no `tools` field).
  4. **✅ `classifier.md` §1.4 (l.45) + §10.3 + Gate 6.** Argumento corrigido **preservando o Issue #361** (verdadeiro sobre `allowed_tools`; o defeito era estendê-lo ao `tools` field — campos distintos). §10.3 "Gate resource access" → **PASS** com ponteiro pro `RESULTS.md` (o probe exercitou o shape específico do Classifier, não só o do Matcher).
  5. **✅ §2 tabela DD-9.1 do `coordinator` + escopo do ADR-0012** atualizados; **⏳ 5a — ADR-0012 não autorado** (número reservado, 5 decisões de Milestone C, PR `chore/sync-adr-references` próprio; rationale a frio = anti-pattern PR-23). Só o **escopo** foi estendido (montagem mecânica) com a nuance capability-vs-availability carimbada. **Autoria deferida a sessão dedicada.**

  **§10 `coordinator` DD-9.1:** de "persistir pendente" → "evidência persistida" (`RESULTS.md`).

**Pendentes de sessões anteriores (NÃO deste PR — um PR por sessão).** Companion edits que a `matcher.md` mandou mas que pertencem a outras cadeias de trabalho; entram quando suas sessões/PRs forem fechados, não no PR do `tools` field:
- **`classifier.md` §3.3 / DD-C9 (M1 — concern separado do bloco acima)** — anotar que a expectativa de "degradação graciosa para `not_applicable`/`indeterminate`" para valor fora-de-vocab (l.175) está **stale**: o motor rejeita hard (`INVALID_DATA_CATEGORY`/`INVALID_OPERATION`) na validação. **[edit do Code]**
- **`canonical.md` §3.2/§6.3** + **`arch §5.5` (rótulo "framework-aware")** — anotar que o handshake jurisdicional consumer-side é **deferido em sede de MVP** (YAGNI co-versionado), dono futuro = código do coordinator (correção H1/DD-M22). Roteia pelo coordinator §10. **[edit do Code]**
- **`reporter.md:135`** — corrigir a mis-citação introduzida pelo próprio Beat 2: o check-all é **DD-M1/DD-M6**, não "DD-M3" (DD-M3 é a tool futura) — correção L2. **[edit do Code]**
- **`detector.md` §6.3 (L-c — confirmar antes)** — o §6.3 desta spec afirma que o caveat "TS-only" do `detector.md §6.3` está stale (acesso direto a `stop_reason` é a posição do projeto). Não verificado contra `detector.md` nesta rodada — **confirmar a redação atual do `detector.md §6.3` antes de afirmar stale no merge** (verificação-antes-de-inferência). **[edit do Code — confirmar]**
- **`docs/tasks.md`** — débito jurídico `category`/Art. 11; housekeeping canonical (#48) resolvido.
- **`session-handoff.md` l.63** — nota stale ("arch §5.5 candidate_ref NÃO relido") obsoleta pós-Beat 2; resolver no próximo session-close.

### 10.6 Defense candidates emergentes
- **Multi-instance review por complementaridade de trajetória** — o Chat (web + raciocínio) e o Code (repo + impl) cobriram conjuntamente o que cada um sozinho não pegaria (ex.: o handshake server-side só apareceu no `loader.py`, lido pelo Code; os limites de structured output só na doc, lidos pelo Chat). Material de Capítulo de Método.
- **Spec-vs-impl como fonte de verdade pós-implementação** — três discrepâncias do canonical (gate de operation, token de legal_basis, exemplo violation_candidate) só apareceram contra o motor, não contra a spec.
- **Separação de planos epistêmicos** (conduto fiel; o Matcher reporta, não fabrica) — sustenta o DD-21 e a postura de honestidade da banca.

### 10.7 Side findings pendentes
- `find_clauses_by_law_article` órfã de seleção (DD-M2) — investigação de remoção dedicada, fora de escopo #48.
- Sub-modelagem `category`/Art. 11 — evolução pós-MVP do motor.
