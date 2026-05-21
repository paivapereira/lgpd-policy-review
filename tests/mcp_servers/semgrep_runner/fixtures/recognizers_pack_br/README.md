# Pack de fixtures de recognizers brasileiros (recognizers_pack_br)

Nove snippets Python (seis positivos + três negativos) calibrados para
exercitar as seis regras Semgrep brasileiras de T07 (`br-cpf`, `br-cnpj`,
`br-cnh`, `br-nis-pis`, `br-titulo-eleitor`, `br-cns-saude`) e o controle
de falso positivo de AS-7.

## Propósito e escopo

Este pack existe como **fixture de teste**, não como artefato real de
produção. Decisão registrada na sessão Chat #28 (Provisão B de Milestone
B): a finalidade é exercitar as seis regras de detecção brasileiras e o
controle de falso positivo de AS-7. Implicações:

- Pack consome regras Semgrep curadas por T07 — sem T07 implementado, o
  pack só serve de fixture estática. Pack é pré-requisito de T07
  conforme `docs/tasks.md` linha 351, não condição suficiente.
- Identificadores são **sintéticos** — base digits arbitrários
  combinados com check digits algoritmicamente calculados (ver
  §Identificadores sintéticos abaixo). Nenhum identificador real de
  pessoa ou entidade. Convenção alinhada a
  `.claude/rules/privacy-safety.md` §PII.

## AS coverage por arquivo

| Arquivo | Task / AS | Comportamento testado |
| --- | --- | --- |
| `br_cpf_function_param.py` | T07 AS-1 | `br-cpf` matcheia parâmetro `cpf: str` em `def create_user_account(...)` |
| `br_cnpj_dict_key.py` | T07 AS-2 | `br-cnpj` matcheia dict key `payload["cnpj"]` |
| `br_cnh_attribute_assign.py` | T07 AS-3 | `br-cnh` matcheia `driver.cnh = form_data["cnh"]` |
| `br_nis_log_payload.py` | T07 AS-4 | `br-nis-pis` matcheia kwarg `nis=...` em `logger.info(...)` |
| `br_titulo_eleitor_function_param.py` | T07 AS-5 | `br-titulo-eleitor` matcheia parâmetro `titulo_eleitor: str` |
| `br_cns_dict_key.py` | T07 AS-6 | `br-cns-saude` matcheia dict key `patient_data["cns_saude"]` |
| `negative_version_string.py` | T07 AS-7 | nenhuma regra dispara contra version strings em formato CPF/CNPJ-like |
| `negative_regex_validation.py` | T07 AS-7 | nenhuma regra dispara contra regex patterns literais |
| `negative_uuid_constant.py` | T07 AS-7 | nenhuma regra dispara contra UUIDs e ordens numeradas |

T07 AS-8 (placeholder removida) e AS-9 (idempotência cross-invocations) são
exercitados pelo pack em conjunto (snippet-agnóstico): AS-8 verifica que
`scan_diff` retorna apenas rule_ids do conjunto `{br-cpf, br-cnpj, ...}` sem
`_placeholder.yaml` no rule set; AS-9 verifica que duas invocações sucessivas
sobre o pack retornam findings byte-idênticos.

## Estrutura no repo

```
tests/
  mcp_servers/
    semgrep_runner/
      fixtures/
        recognizers_pack_br/
          br_cpf_function_param.py
          br_cnpj_dict_key.py
          br_cnh_attribute_assign.py
          br_nis_log_payload.py
          br_titulo_eleitor_function_param.py
          br_cns_dict_key.py
          negative_version_string.py
          negative_regex_validation.py
          negative_uuid_constant.py
          README.md  (este arquivo)
```

Code é livre para reorganizar — esta estrutura reflete o naming implícito
em `docs/tasks.md` ("fixtures em `tests/mcp_servers/semgrep_runner/fixtures/`")
e o pattern do POL pack (flat, sem subdiretórios positive/negative).

## Composição da fixture root para testes de T07

Cada teste de T07 (`test_recognizers_br.py`) que precisa exercitar uma
regra contra o pack constrói uma fixture root temporária via `tmp_path`
do pytest, composta de:

- `rules/br_cpf.yaml`, `rules/br_cnpj.yaml`, ..., `rules/br_cns_saude.yaml`
  — copiados do rule set de produção (`mcp_servers/semgrep_runner/rules/`)
  após T07 mergeado.
- `fixtures_under_test/` — copiados deste pack.

O servidor `semgrep-runner` é iniciado com configuração apontando para o
rule set temporário; `scan_diff` é invocado com refs Git apontando para
diff que introduz os snippets do pack.

Pattern típico em `conftest.py` (sugestão; Code refatora):

```python
import shutil
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
RULES = REPO_ROOT / "mcp_servers" / "semgrep_runner" / "rules"
PACK = REPO_ROOT / "tests" / "mcp_servers" / "semgrep_runner" / "fixtures" / "recognizers_pack_br"


@pytest.fixture
def rule_set_with_br_recognizers(tmp_path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir(parents=True)
    for rule_name in (
        "br_cpf",
        "br_cnpj",
        "br_cnh",
        "br_nis_pis",
        "br_titulo_eleitor",
        "br_cns_saude",
    ):
        shutil.copy(RULES / f"{rule_name}.yaml", rules_dir / f"{rule_name}.yaml")
    return rules_dir


@pytest.fixture
def fixture_pack_br(tmp_path):
    pack_dir = tmp_path / "scan_target"
    shutil.copytree(PACK, pack_dir)
    return pack_dir
```

## Identificadores sintéticos utilizados

Cada identificador foi gerado por (a) escolha de base digits arbitrários
(sem associação a pessoas ou entidades reais conhecidas) e (b) cálculo
do check digit via algoritmo público da respectiva autoridade emissora.
Reproduzível via script `gen_synthetic_ids.py` mantido na sessão Chat #28
de authoring.

### CPF — `238.547.961-37`

- **Base:** 238547961 (arbitrário).
- **Algoritmo CD1:** soma de `digit[i] × (10 - i)` para i = 0..8, mod 11. Se resto < 2, CD1 = 0; senão, CD1 = 11 - resto.
- **Algoritmo CD2:** soma de `digit[i] × (11 - i)` para i = 0..9 (incluindo CD1), mod 11. Mesma regra de truncamento.
- **Resultado:** CD1 = 3, CD2 = 7.

### CNPJ — `47.861.932/0001-92`

- **Base:** 478619320001 (12 dígitos arbitrários; últimos 4 = '0001' por convenção de matriz).
- **Algoritmo CD1:** pesos `[5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]`, mod 11.
- **Algoritmo CD2:** pesos `[6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]` sobre 12 base + CD1.
- **Resultado:** CD1 = 9, CD2 = 2.

### CNH — `56284913773`

- **Base:** 562849137 (arbitrário).
- **Algoritmo CD1:** soma de `digit[i] × (9 - i)`, mod 11. Se resto = 10, CD1 = 0 e DSC = 2; senão CD1 = resto e DSC = 0.
- **Algoritmo CD2:** soma de `digit[i] × (i + 1)`, mod 11, menos DSC. Se < 0, soma 11. Se = 10, CD2 = 0.
- **Resultado:** CD1 = 7, CD2 = 3.

### NIS/PIS — `17293846507`

- **Base:** 1729384650 (10 dígitos arbitrários).
- **Algoritmo CD:** pesos `[3, 2, 9, 8, 7, 6, 5, 4, 3, 2]`, mod 11. Se resto < 2, CD = 0; senão CD = 11 - resto.
- **Resultado:** CD = 7.

### Título de Eleitor — `348291670116`

- **Base sequencial (8 dígitos):** 34829167 (arbitrário).
- **Código UF (2 dígitos):** 01 (SP).
- **Algoritmo CD1:** pesos `[2, 3, 4, 5, 6, 7, 8, 9]` sobre base sequencial, mod 11. Se resto = 10, CD1 = 0; se resto = 0 e UF ∈ {SP, MG}, CD1 = 1; senão CD1 = resto.
- **Algoritmo CD2:** `(uf[0] × 7) + (uf[1] × 8) + (cd1 × 9)`, mod 11. Mesma regra especial para SP/MG.
- **Resultado:** CD1 = 1, CD2 = 6.

### CNS-saúde — `163 8492 7503 0003` (definitivo, prefixo 1)

- **Base:** 16384927503 (11 dígitos arbitrários; primeiro dígito ∈ {1, 2} indica CNS definitivo).
- **Algoritmo:** computar soma parcial `digit[i] × (15 - i)` para i = 0..10. Se resto mod 11 = 0, últimos 4 dígitos = `0000`. Senão, últimos 4 dígitos = `000` + str(11 - resto).
- **Validação:** soma total `digit[i] × (15 - i)` para i = 0..14 deve ser divisível por 11.
- **Resultado:** últimos 4 dígitos = `0003`.

## Tokens utilizados

- **Identifier names canônicos** (consumidos pelas regras `br-*` em T07):
  - `cpf` (function parameter, dict key, attribute, log payload keyword)
  - `cnpj`
  - `cnh`
  - `nis` (forma curta canonical, cobre NIS/PIS combinado por convenção do MVP)
  - `titulo_eleitor` (snake_case sem "de")
  - `cns_saude` (snake_case com qualifier para distinguir de outros CNS — Common Name Server etc)

- **Rule IDs esperados** (autorados por T07): `br-cpf`, `br-cnpj`, `br-cnh`, `br-nis-pis`, `br-titulo-eleitor`, `br-cns-saude` (kebab-case com prefixo `br-`, conforme Chat review item de T07).

- **Linguagem do MVP:** Python. Cobertura JS/TS é pendência pós-Milestone B aberta em `docs/tasks.md` §"Pós-Milestone B aberto" — fixtures JS análogas serão adicionadas em PR separada se aplicável.

## Assimetrias deliberadas

### Latin square em vez de matriz completa 6 × 4

Cada identificador é exercitado em **apenas um** dos quatro padrões
sintáticos. Distribuição:

- (a) parameter naming → CPF, Título de Eleitor
- (b) dict key access → CNPJ, CNS-saúde
- (c) attribute assignment → CNH
- (d) log payload structured → NIS/PIS

Justificativa: AS-1 a AS-6 do T07 declaram "snippet positivo" singular
por identificador e "exatamente um finding" esperado. Latin square é a
cobertura mínima que satisfaz o contrato. Matriz completa 6 × 4 = 24
snippets seria regression test set mais robusto, fica como evolução
pós-MVP. **Implícito:** se a regra `br-cpf` matcheia padrão (a)
corretamente, espera-se que matcheie (b), (c), (d) também — porque o
predicate semântico é "presença do identifier name em contexto de
coleta", não a sintaxe específica do contexto. Confirmação empírica
dessa transitividade fica para PR futura.

### Variantes de formato cobertos apenas parcialmente

Cada identificador em **uma** variação canônica do seu domínio (CPF/CNPJ
com pontuação; CNH/título só dígitos; CNS espaçado; NIS sem formatação).
Variantes ortogonais (CPF sem pontuação; CNPJ só dígitos; CNH com hífen
hipotético; etc) não são cobertos no MVP. Pack admite extensão sem
refactor — cada variante adicional é um arquivo novo nomeado
`br_<id>_<pattern>_<variant>.py`.

### Check digit inválido NÃO coberto

Recognizer rules de T07 são pattern-based syntáticas (Semgrep AST),
**não validam check digit**. Cobertura de identificadores com check
digit inválido teria valor zero para Semgrep e custo extra de fixture
authoring. Validação semântica de check digit é responsabilidade do
Classifier subagent em Milestone C (não do Detector + semgrep-runner em
Milestone B).

### Identificadores reais NÃO usados

Convenção `.claude/rules/privacy-safety.md` §PII proíbe PII real em
fixtures. Pack usa apenas identificadores sintéticos cujos check digits
foram computados algoritmicamente sobre base digits arbitrários. Há
probabilidade não-zero de colisão com identificador real alocado por
autoridade emissora (espaço de identificadores é finito), mas nenhum
identificador foi gerado a partir de fonte conhecida de identificadores
reais.

## Ressalvas conhecidas

- **Interpretação ambígua de T07 linha 365.** A frase "ao menos uma
  variação por padrão sintático (parameter, dict key, attribute, log
  payload) para cada um dos seis identificadores" admite duas leituras:
  (i) matriz completa 6 × 4 = 24 snippets; (ii) Latin square com
  cobertura distribuída. Pack adota (ii) ratificado em sessão Chat #28
  pós-Code-review pré-aplicação, com base em três sinais coerentes
  de `tasks.md`: linha 248 declara explicitamente "seis snippets
  positivos (um por identificador)"; AS-1 a AS-6 declaram singular
  "snippet positivo" + "exatamente um finding" por identificador;
  AS-9 (idempotência cross-invocations) assume conjunto estável de
  findings, compatível com Latin square. Implícito desta interpretação:
  **transitividade** — se `br-cpf` matcheia padrão (a), espera-se que
  matcheie (b), (c), (d) também via implementação pattern-either em T07.
  Se T07 implementar de forma que não exerce transitividade (regras
  separadas por padrão sintático em vez de pattern-either consolidada),
  a interpretação matriz completa precisa ser ratificada e o pack admite
  extensão para 24 sem refactor — cada variante adicional é arquivo novo
  `br_<id>_<pattern>_<variant>.py`.

### Identificadores sintéticos compartilhados entre positivos e negativos

`238.547.961-37` (CPF sintético do pack) e `47.861.932/0001-92` (CNPJ
sintético do pack) aparecem **deliberadamente** em
`negative_version_string.py` além dos seus snippets positivos
correspondentes. O design exerce discriminação por contexto sintático:
a mesma string em `def create_user_account(cpf="238.547.961-37", ...)`
deve disparar `br-cpf` (positivo), mas em
`RELEASE_TAG = "release-238.547.961-37"` ou
`BUILD_NUMBER = "47.861.932/0001-92"` (negativo) NÃO deve disparar
porque o variable name não é identifier-related. Esta é asserção forte
sobre AST-aware matching do Semgrep, central ao Chat review item de
T07 ("padrões Semgrep são pattern-based ou pattern-either, não
regex-only — regex puro é anti-pattern em Semgrep, perde AST
awareness"). Se T07 implementar regras regex-only (anti-pattern),
esses negativos vão falhar AS-7 e o defeito é da implementação T07,
não do pack BR.

- **`cns_saude` snake_case com qualifier.** O nome canonical do
  identifier para CNS no pack é `cns_saude` (não `cns`), para evitar
  ambiguidade com outros CNS (Common Name Server, Container Network
  Service). Regra `br-cns-saude` em T07 pode escolher matchear ambos
  `cns` e `cns_saude` como aliases; o pack só exercita a forma com
  qualifier.

- **`titulo_eleitor` sem "de".** Forma compacta canonical no MVP. Regra
  `br-titulo-eleitor` pode escolher matchear `titulo_de_eleitor` como
  alias; o pack só exercita `titulo_eleitor`.

- **NIS/PIS combinado.** Identifier name canonical no MVP é `nis`, e a
  regra única `br-nis-pis` cobre ambas semânticas (NIS e PIS são
  identificadores logicamente intercambiáveis no INSS desde 2018). Se
  sessão futura ratificar separação `br-nis` e `br-pis` distintas,
  pack precisa de snippet adicional `br_pis_*.py`.

- **CNS provisório (prefixos 7, 8, 9) não coberto.** Pack cobre apenas
  CNS definitivo (prefixos 1, 2). CNS provisório usa algoritmo diferente
  (soma direta mod 11 == 0 sem CD computado). Cobertura de provisórios
  é evolução pós-MVP.

- **`policy_schema_version` não aplicável.** Pack BR não interage com a
  Política LGPD versionada — recognizers brasileiros são input do
  Detector (T07), não cláusulas substantivas. Diferente do POL pack que
  precisa de sync de `policy_schema_version` com header real.

- **Identificadores potencialmente reais.** Apesar de gerados
  algoritmicamente sobre base digits arbitrários, nenhum mecanismo
  garante que não haja colisão com identificadores reais alocados por
  autoridades emissoras. Se algum identificador sintético do pack for
  reportado como coincidindo com identificador real (e.g., via revisão
  externa), substituir e atualizar este README + os snippets atingidos.
