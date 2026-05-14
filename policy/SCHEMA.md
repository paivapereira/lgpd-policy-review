# policy/SCHEMA.md — Schema canônico da Política versionada

**schema_version:** `0.1.0`
**Status:** ativo, em refinamento (§6 sobre cláusula `substantive` é destilada do esqueleto aprovado, não de instância concreta; refinamento previsto quando POL-001 for redigida)
**Última revisão:** 2026-05-14 (sessão #16)

---

## 1. Propósito e audiência

Documento de arquitetura da Política — especifica forma, vocabulários e regras de evolução. Audiência: redator jurídico (consulta para escrever cláusulas), redator técnico (consulta para implementar carregamento), auditor e banca de TCC. **Não é consumido pelo agente MCP em runtime** — o `policy-reader` parseia YAML (`policy/clauses/*.yaml` + `policy/policy.yaml`), não Markdown. Validação programática de carregamento é responsabilidade do servidor, implementada via Pydantic/JSON Schema derivados deste documento na fase de implementação (semana 5).

## 2. Layout no repositório

```
policy/
├── SCHEMA.md                  # este documento (camada estrutural universal)
├── policy.yaml                # header global (legal_framework, versões, metadata)
├── clauses/                   # destilação operacional consumida pelo MCP
│   ├── POL-000.yaml
│   └── ...
├── rationale/                 # canônico jurídico consumido por humano
│   ├── POL-000.md
│   └── ...
└── vocabularies/              # vocabulários jurisdicionais (per-cliente)
    └── <framework>/           # e.g., LGPD/
        ├── operation.yaml
        ├── lawful_basis.yaml
        ├── control.yaml
        └── out_of_scope.yaml
```

### 2.1 Layering: estrutural universal vs jurisdicional per-cliente

A Política tem duas camadas com regras de versionamento, audiência e fonte canônica distintas.

**Camada estrutural (universal).** SCHEMA.md, `clauses/` e `rationale/` definem mecanismo: forma da Política, envelope de cláusula, vocabulários estruturais (e.g., `clause_state`, `vocabulary_kind`), regras de validação. Esta camada é universal — não depende do framework jurisdicional. Vive no projeto.

**Camada jurisdicional (per-cliente).** `policy.yaml` (header com `legal_framework`, `accepted_law_identifiers`, versões) e `policy/vocabularies/<framework>/*.yaml` carregam conteúdo: qual lei, quais operações de tratamento, quais bases legais, quais controles, quais motivos de out-of-scope são reconhecíveis na jurisdição declarada. Esta camada é per-cliente — substituí-la (LGPD → GDPR) não exige alteração estrutural.

Decisão arquitetural formal: ADR-0005 (Architecture for multi-client policy support).

## 3. Header global — `policy/policy.yaml`

### 3.1 Campos

| Campo | Tipo | Descrição |
|---|---|---|
| `policy_schema_version` | string semver | Versão do schema com a qual esta Política é compatível |
| `policy_version` | string semver | Versão agregada do conteúdo |
| `legal_framework` | string | Framework jurisdicional sob o qual a Política opera (valor único, e.g., `LGPD`). Imutável durante sessão do server. Determina qual `policy/vocabularies/<framework>/` é carregado pelo `policy-reader` em startup. |
| `accepted_law_identifiers` | array de string | Vocabulário fechado de leis citáveis em `statutory_reference.lei`. Ver §9.3 |
| `policy_owner` | string | Papel jurídico responsável (declarativo, não vinculante) |
| `effective_date` | string ISO 8601 | A partir de quando esta versão vale |
| `last_revision` | string ISO 8601 | Data da última modificação |

### 3.2 Regras de versionamento

**`policy_schema_version`** (este schema) — semver:
- **major**: remove campo obrigatório, restringe enum existente, ou altera semântica de campo de forma que cláusulas válidas em versão anterior deixam de ser válidas.
- **minor**: adiciona campo opcional, adiciona valor de enum (callers podem ignorar), ou introduz nova `clause_type`.
- **patch**: typo, clarificação textual, reorganização sem alterar semântica.
- Promoção a `1.0` exige ADR dedicada (regra herdada de ADR-0002 D6).
- Qualquer mudança major (mesmo pre-1.0) exige ADR explicando quebra e migration path.

**`policy_version`** (conteúdo da Política) — semver independente:
- **major**: cláusula removida (não deprecated — efetivamente apagada) ou semântica de cláusula existente alterada incompatibilidade.
- **minor**: cláusula nova publicada com `status: active`, ou alteração em cláusula que muda comportamento sem quebrar callers.
- **patch**: correção textual em rationale, atualização de fonte, ajuste de exemplo canônico em cláusula `definitional` sem alteração do critério.

**`legal_framework`** (jurisdição da Política) — não-semver, valor único:
- Imutável durante sessão do `policy-reader`. Não há mecanismo de hot-swap.
- Trocar de framework (e.g., LGPD → GDPR) é exercício de substituição de dados: nova Política com header declarando `legal_framework: GDPR`, nova `policy/vocabularies/GDPR/*.yaml`, restart do server. Sem alteração de código.
- Mudança de `legal_framework` em uma Política existente é antipadrão — equivale a Política nova sob jurisdição distinta. Ver ADR-0005 Decision 2.

**Provenance temporal e jurisdicional.** Os três campos juntos (`policy_schema_version`, `policy_version`, `legal_framework`) identificam univocamente o estado da Política e a jurisdição no momento de uma decisão. Retornos de `check_applicability` carregam o trinque para reprodutibilidade e auditoria multi-jurisdição.

## 4. Campos comuns a toda cláusula

### 4.1 `clause_id`
string, formato `^POL-\d{3}$`. Identificador opaco. **Unidirecional**: adicionar é OK, virar `tombstone` é OK, renomear não é. Em caso de necessidade de novo nome, criar nova cláusula e marcar a antiga como `deprecated` com `successors` apontando.

### 4.2 `title`
string em português. Rótulo humano-legível, sem repetir o prefixo `POL-NNN`.

### 4.3 `clause_type`
enum: `definitional` (estrutura em §5) | `substantive` (estrutura em §6).

### 4.4 `status`
enum: `active` | `deprecated`. Default `active`. Cláusulas `deprecated` permanecem no diretório — auditoria histórica é caso de uso legítimo. `deprecated` obriga bloco `tombstone` (§4.6).

### 4.5 `policy_schema_version`
string semver. **Aparece em cada cláusula, redundante com o do header global, por design.** Fail-fast: divergência incompatível entre cláusula e header aborta carregamento do `policy-reader` no startup.

### 4.6 `tombstone`
Objeto. Obrigatório quando `status: deprecated`; ausente quando `active`.

| Campo | Tipo | Descrição |
|---|---|---|
| `successors` | array de `clause_id` | Cláusulas sucessoras. Lista vazia `[]` permitida com `deprecation_reason` justificando ausência. |
| `effective_until` | string ISO 8601 | A partir de quando a cláusula deixou de ser operativa. |
| `deprecation_reason` | string em português | Justificativa da deprecação. |

## 5. Cláusula `definitional`

Cláusula que define vocabulário canônico usado por cláusulas `substantive`. POL-000 é a instância de referência do MVP v0.1.0; estrutura desta seção destilada dela.

### 5.1 `statutory_reference` (top-level)
Array de objetos. Aponta para artigo(s) com natureza definitória.

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `lei` | string | sim | Vocabulário em `accepted_law_identifiers` (§9.3). |
| `artigo` | inteiro | sim | Número do artigo. |
| `paragrafo` | inteiro | não | Omitido quando ausente. |
| `inciso` | inteiro | não | Inteiro literal (renderizado como romano em apresentação humana). Omitido quando ausente. |
| `alinea` | string minúscula | não | Omitido quando ausente. |

### 5.2 `defines`

| Campo | Tipo | Descrição |
|---|---|---|
| `vocabulary_kind` | enum | Tipo de vocabulário definido. Lista em §9.6. |
| `entries` | array | Lista de entradas. Forma depende de `vocabulary_kind`. |

### 5.3 Forma de `defines.entries[]` quando `vocabulary_kind: personal_data_categories`

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `name` | string snake_case sem diacríticos | sim | Identificador canônico da classe. Token referenciado em `applies_to.personal_data_categories` de cláusulas `substantive`. |
| `definition` | string em português | sim | Definição operacional, suficiente para classifier decidir "isto cai aqui ou não". |
| `canonical_examples` | array de string | sim | Mínimo de três exemplos. |
| `statutory_reference` | array | sim | Mesma forma de §5.1. |
| `special_category` | boolean | sim | `true` se a classe contém dado sensível pelo Art. 5º II LGPD. Governa qual `control` é exigível por cláusulas `substantive` que operam sobre a classe. |

### 5.4 `out_of_scope`
Array. Tópicos declaradamente fora do escopo. Declaração positiva — silenciar sobre o que ficou fora obscurece a fronteira epistêmica.

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `topic` | string snake_case | sim | Tópico excluído. |
| `statutory_reference` | array | sim | Pode ser lista vazia `[]` quando o tópico não tem ancoragem em artigo específico. |
| `reason` | enum | sim | Vocabulário fechado em §9.4. |
| `fallback` | string ou `null` | sim | Nome de entry de POL-000, OU `unmodeled_special_category_fallback`, OU `null`. |

## 6. Cláusula `substantive`

**Provisório.** Esta seção é destilada do esqueleto aprovado na sessão #10, não de instância concreta. Refinamento previsto quando POL-001 for redigida.

Cláusula que prescreve `control` para combinação `personal_data_categories × operation`, ancorada em artigo(s) específico(s).

### 6.1 `statutory_reference` (top-level)
Array. Mesma forma de §5.1. Tipicamente inclui inciso/alínea específicos. Múltiplos itens admitidos para intersecção de obrigações.

### 6.2 `applies_to`

| Campo | Tipo | Descrição |
|---|---|---|
| `personal_data_categories` | array de string | Refs a `name` de entries de POL-000. |
| `operation` | array de string | Refs a valores do enum `operation` (§9.2). |

### 6.3 `control`
Enum (MVP) ou objeto (caminho evolutivo). MVP v0.1.0 admite apenas dois valores: `consent_required`, `anonymization_required` (lista em §9.5). Quando cláusulas precisarem prescrever mais que lawful basis (criptografia em repouso, retenção, DPIA), `control` migra para forma `{type, value}` — adição é additive, não quebra callers.

### 6.4 `requirements`
Array. Cada item:

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | string `^R\d+$` | Sub-id sequencial. Referenciado em `contradicted_requirement` de `check_applicability`. |
| `text` | string em português | Prosa descrevendo a obrigação. |

### 6.5 `exceptions`
Array. Cada item:

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | string `^E\d+$` | Sub-id sequencial. |
| `text` | string em português | Prosa descrevendo a hipótese de exceção. |

## 7. Vocabulários fechados

| Vocabulário | Onde aparece | Natureza | Canonical |
|---|---|---|---|
| `lawful_basis` | input de `check_applicability`, retornos de tools | jurisdicional | `policy/vocabularies/LGPD/lawful_basis.yaml` |
| `operation` | `applies_to.operation` e input de `check_applicability` | jurisdicional | `policy/vocabularies/LGPD/operation.yaml` |
| `accepted_law_identifiers` | header global; referenciado por `statutory_reference.lei` | jurisdicional | `policy/policy.yaml` (header) |
| `reason` | `out_of_scope[].reason` em cláusulas `definitional` | jurisdicional | `policy/vocabularies/LGPD/out_of_scope.yaml` |
| `control` | campo top-level de cláusulas `substantive` | jurisdicional | `policy/vocabularies/LGPD/control.yaml` |
| `vocabulary_kind` | `defines.vocabulary_kind` em cláusulas `definitional` | estrutural | `policy/SCHEMA.md` §9.6 |

**Nota arquitetural.** Vocabulários `jurisdicional` têm canonical em `policy/vocabularies/<framework>/*.yaml` (lidos como dados em startup do `policy-reader`, não hardcoded em código do componente). `accepted_law_identifiers` é declarado pelo header de `policy.yaml`. `vocabulary_kind` é estrutural e permanece no SCHEMA.md §9.6 — universal a qualquer framework. `personal_data_categories` continua extensível pela Política via cláusula `definitional` (atualmente POL-000), independente de framework: a categorização é semântica, não jurisdicional (ver ADR-0005 Decision 3). As subseções §9.1, §9.2, §9.4 e §9.5 abaixo são referência humana — em divergência com o YAML canonical, o YAML prevalece.

## 8. Correspondência YAML ↔ Markdown rationale

Princípio geral aplicado a toda cláusula da Política. Documentado integralmente em `policy/rationale/POL-000.md` §7. Em resumo: Markdown é canônico jurídico (prevalece em drift); YAML é destilação operacional (corrigido quando drift detectado); paridade verificada por teste automatizado na fase de implementação do `policy-reader`.

## 9. Apêndices

### 9.1 Enum completo de `lawful_basis`

**Canonical:** `policy/vocabularies/LGPD/lawful_basis.yaml`. Esta subseção é referência humana; em caso de divergência, o YAML prevalece e esta tabela é corrigida.

**Bases para dados pessoais (Art. 7º LGPD × Art. 6(1) GDPR).**

| LGPD | GDPR | snake_case | Termo LGPD em PT |
|---|---|---|---|
| Art. 7º, I | Art. 6(1)(a) | `consent` | consentimento do titular |
| Art. 7º, II | Art. 6(1)(c) | `legal_obligation` | cumprimento de obrigação legal ou regulatória |
| Art. 7º, III | Art. 6(1)(e) | `public_administration_policy` | execução de políticas públicas |
| Art. 7º, IV | — | `research_by_research_body` | estudos por órgão de pesquisa |
| Art. 7º, V | Art. 6(1)(b) | `contract_performance` | execução de contrato |
| Art. 7º, VI | Art. 6(1)(f) | `regular_exercise_of_rights` | exercício regular de direitos |
| Art. 7º, VII | Art. 6(1)(d) | `vital_interests` | proteção da vida |
| Art. 7º, VIII | Art. 9(2)(h) | `health_protection` | tutela da saúde |
| Art. 7º, IX | Art. 6(1)(f) | `legitimate_interests` | legítimo interesse |
| Art. 7º, X | — | `credit_protection` | proteção do crédito |

**Bases para dados pessoais sensíveis (Art. 11 LGPD × Art. 9(2) GDPR).**

| LGPD | GDPR | snake_case | Termo LGPD em PT |
|---|---|---|---|
| Art. 11, I | Art. 9(2)(a) | `explicit_consent` | consentimento específico e destacado |
| Art. 11, II, "a" | Art. 9(2)(b)/(g) | `legal_obligation_sensitive` | obrigação legal (sensíveis) |
| Art. 11, II, "b" | Art. 9(2)(g) | `public_administration_policy_sensitive` | políticas públicas compartilhadas |
| Art. 11, II, "c" | Art. 9(2)(j) | `research_by_research_body_sensitive` | estudos por órgão de pesquisa |
| Art. 11, II, "d" | Art. 9(2)(f) | `regular_exercise_of_rights_sensitive` | exercício regular de direitos |
| Art. 11, II, "e" | Art. 9(2)(c) | `vital_interests_sensitive` | proteção da vida |
| Art. 11, II, "f" | Art. 9(2)(h) | `health_protection_sensitive` | tutela da saúde |
| Art. 11, II, "g" | Art. 9(2)(g) | `fraud_prevention_and_subject_safety` | prevenção à fraude e segurança do titular |

### 9.2 Enum completo de `operation`

**Canonical:** `policy/vocabularies/LGPD/operation.yaml`. Esta subseção é referência humana; em caso de divergência, o YAML prevalece e esta tabela é corrigida.

União de LGPD Art. 5º X e GDPR Art. 4(2). Ambos os róis são exemplificativos — schema admite `other` como fallback, obrigando campo livre `operation_description` quando usado.

| snake_case | Equivalente PT | Fonte |
|---|---|---|
| `collection` | coleta | GDPR Art. 4(2); LGPD Art. 5º X |
| `recording` | produção; recepção | GDPR Art. 4(2); LGPD Art. 5º X |
| `organisation` | classificação | GDPR Art. 4(2) |
| `structuring` | estruturação | GDPR Art. 4(2) |
| `storage` | armazenamento; arquivamento | GDPR Art. 4(2); LGPD Art. 5º X |
| `adaptation` | adaptação | GDPR Art. 4(2) |
| `alteration` | modificação | GDPR Art. 4(2); LGPD Art. 5º X |
| `retrieval` | acesso; extração | GDPR Art. 4(2); LGPD Art. 5º X |
| `consultation` | acesso (consulta) | GDPR Art. 4(2) |
| `use` | utilização | GDPR Art. 4(2); LGPD Art. 5º X |
| `disclosure_by_transmission` | transmissão; comunicação | GDPR Art. 4(2); LGPD Art. 5º X |
| `dissemination` | difusão; distribuição | GDPR Art. 4(2); LGPD Art. 5º X |
| `making_available` | disponibilização | GDPR Art. 4(2) |
| `alignment` | combinação por chave | GDPR Art. 4(2) |
| `combination` | combinação genérica | GDPR Art. 4(2) |
| `restriction` | bloqueio | GDPR Art. 4(2)/(3); LGPD Art. 5º XIII |
| `erasure` | eliminação (lógica) | GDPR Art. 4(2); LGPD Art. 5º X e XIV |
| `destruction` | eliminação (física) | GDPR Art. 4(2); LGPD Art. 5º X |
| `evaluation` | avaliação; controle | LGPD Art. 5º X |
| `international_transfer` | transferência internacional | LGPD Art. 33; GDPR Cap. V |
| `sharing` | uso compartilhado | LGPD Art. 7º §5º |
| `other` | (fallback exemplificativo) | — |

### 9.3 `accepted_law_identifiers`
MVP v0.1.0: apenas `LGPD` (Lei nº 13.709/2018). Evolução prevista: `MARCO_CIVIL_INTERNET` (Lei 12.965/2014) quando cláusulas substantivas precisarem.

### 9.4 `reason` (em `out_of_scope[]`)

**Canonical:** `policy/vocabularies/LGPD/out_of_scope.yaml`. Esta subseção é referência humana; em caso de divergência, o YAML prevalece e esta tabela é corrigida.

MVP v0.1.0 (sete valores, todos materializados em POL-000):
- `unmodeled_special_category` — falha o critério de reconhecibilidade técnica (sensíveis difusos do Art. 5º II).
- `absorbed_into_existing_class` — espécie absorvida por classe já modelada.
- `regime_attribute_not_class` — categoria é regime de tratamento, não classe.
- `treatment_attribute_not_class` — categoria é atributo de operação, não classe.
- `not_personal_data_per_definition` — fora do escopo da LGPD por definição.
- `out_of_lgpd_scope_when_truly_anonymous` — fora do escopo enquanto efetivamente anonimizado.
- `out_of_geographic_scope` — fora do escopo geográfico do MVP.

### 9.5 `control`

**Canonical:** `policy/vocabularies/LGPD/control.yaml`. Esta subseção é referência humana; em caso de divergência, o YAML prevalece e esta tabela é corrigida.

MVP v0.1.0 (dois valores):
- `consent_required` — Política exige consentimento como base legal.
- `anonymization_required` — Política exige anonimização antes de uso/persistência.

Caminho evolutivo: forma objeto `{type, value}` quando cláusulas precisarem prescrever mais que lawful basis. Documentado em §6.3.

### 9.6 `vocabulary_kind`
MVP v0.1.0: apenas `personal_data_categories`. Estrutural — universal a qualquer framework.

## 10. Layout multi-cliente

A Política é personalizada por cliente. Cada cliente do sistema mantém sua própria Política sob o framework jurisdicional aplicável. LGPD é instância exemplar do MVP, não framework default codificado.

### 10.1 Estrutura `policy/vocabularies/<framework>/`

Cada framework jurisdicional suportado tem um diretório dedicado com exatamente quatro arquivos YAML, fonte canônica programática dos vocabulários jurisdicionais:

| Arquivo | Vocabulário | Quantidade no MVP LGPD |
|---|---|---|
| `operation.yaml` | `operation` | 22 valores (LGPD Art. 5º X ∪ GDPR Art. 4(2)) |
| `lawful_basis.yaml` | `lawful_basis` | 18 valores (Art. 7º + Art. 11) |
| `control.yaml` | `control` | 2 valores no MVP (`consent_required`, `anonymization_required`) |
| `out_of_scope.yaml` | `reason` (out_of_scope) | 7 valores |

### 10.2 Formato dos arquivos

Cabeçalho comum:

```yaml
schema_version: "0.1.0"
framework: LGPD
values:
  - name: <snake_case>
    [campos específicos do vocabulário]
```

Campos por entry variam conforme o vocabulário — ver os YAMLs em `policy/vocabularies/LGPD/` para a forma canônica.

### 10.3 Troca de framework

Substituir o framework de uma Política (LGPD → GDPR, p.ex.) é exercício de substituição de dados:

1. Nova Política sob `policy/` com `legal_framework: GDPR` no header.
2. Novo diretório `policy/vocabularies/GDPR/` com os quatro YAMLs equivalentes.
3. Cláusulas em `clauses/` reautoradas sob o novo framework (sucessão é intra-Política, não cross-framework — ver ADR-0005 Decision 6).
4. Restart do `policy-reader`.

Nenhuma alteração de código do sistema. Decisão arquitetural formal: ADR-0005.
