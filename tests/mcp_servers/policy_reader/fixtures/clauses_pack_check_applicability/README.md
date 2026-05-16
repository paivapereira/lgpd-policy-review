# Pacote de cláusulas de teste — check_applicability (POL-001..POL-004)

Quatro cláusulas substantive calibradas para exercitar os quatro vereditos
de `check_applicability` (T03 de `docs/tasks.md`) e os casos modais de
tombstone em `get_clause` (T02a AS-2) e `find_clauses_by_law_article`
(T02b AS-3).

## Propósito e escopo

Estas cláusulas existem como **fixture de teste**, não como artefato
jurídico da Política real do MVP. Decisão registrada na sessão #18 de
authoring: a finalidade é exercitar o contrato de `check_applicability` e
casos modais de retrieval, não validar conteúdo jurídico defensável.
Implicações:

- Não há `policy/rationale/POL-00X.md` para estas cláusulas (paridade
  obrigatória de SCHEMA §8 não se aplica a fixtures).
- `policy/policy.yaml` real **não** referencia estas cláusulas —
  `policy_version` permanece `0.1.0`, sem bump.
- `policy/SCHEMA.md` §6 permanece "em refinamento" — estabilização ocorre
  quando cláusulas substantive reais forem mergeadas, não com estas
  fixtures.

## AS coverage por arquivo

| Arquivo | Task / AS | Veredito ou comportamento testado |
| --- | --- | --- |
| POL-001.yaml | T03 AS-1 | `compliant` com `legal_basis: "consent"` |
| POL-001.yaml | T03 AS-2 | `violation_candidate` com `legal_basis: null` ou ≠ `consent` |
| POL-001.yaml | T02b AS-1 | matching de busca por Art. 7º, I (junto com POL-004) |
| POL-002.yaml | T03 AS-3 | `indeterminate` (inputSchema da tool não comporta declarar transformação) |
| POL-003.yaml | T02a AS-2 | `get_clause` retorna bloco tombstone completo |
| POL-003.yaml | T02b AS-3 | `find_clauses_by_law_article` exclui deprecated com Art. 7º, I |
| POL-003.yaml | T03 AS-7 | `check_applicability` retorna `CLAUSE_DEPRECATED` retryable com `details` completo |
| POL-004.yaml | T03 AS-4 | `not_applicable` (context com categoria que não casa `dados_de_documentos_oficiais`) |
| POL-004.yaml | T02b AS-1 | matching de busca por Art. 7º, I (junto com POL-001) |

## Estrutura sugerida no repo

```
tests/
  mcp_servers/
    policy_reader/
      fixtures/
        clauses_pack_check_applicability/
          POL-001.yaml
          POL-002.yaml
          POL-003.yaml
          POL-004.yaml
          README.md  (este arquivo)
```

Code é livre para reorganizar — esta estrutura apenas reflete o naming
implícito em `docs/tasks.md` ("fixtures em `tests/mcp_servers/policy_reader/fixtures/`").

## Composição da fixture root para testes

Cada teste que precisa destas cláusulas constrói uma fixture root temporária
via `tmp_path` do pytest, composta de:

- `policy.yaml` — copiado de `policy/policy.yaml` real
- `clauses/POL-000.yaml` — copiado de `policy/clauses/POL-000.yaml` real
  (necessário porque as cláusulas deste pack referenciam categorias de
  POL-000)
- `clauses/POL-001.yaml` … `clauses/POL-004.yaml` — copiados deste pack
- `vocabularies/LGPD/{operation,lawful_basis,control,out_of_scope}.yaml` —
  copiados de `policy/vocabularies/LGPD/` reais

O servidor é iniciado com `POLICY_READER_ROOT` apontando para a root
temporária.

Pattern típico em `conftest.py` (sugestão; Code refatora):

```python
import shutil
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_POLICY = REPO_ROOT / "policy"
PACK = REPO_ROOT / "tests" / "mcp_servers" / "policy_reader" / "fixtures" / "clauses_pack_check_applicability"

@pytest.fixture
def policy_root_with_test_clauses(tmp_path):
    root = tmp_path / "policy"
    (root / "clauses").mkdir(parents=True)
    shutil.copy(REAL_POLICY / "policy.yaml", root / "policy.yaml")
    shutil.copy(REAL_POLICY / "clauses" / "POL-000.yaml", root / "clauses" / "POL-000.yaml")
    for pol_id in ("POL-001", "POL-002", "POL-003", "POL-004"):
        shutil.copy(PACK / f"{pol_id}.yaml", root / "clauses" / f"{pol_id}.yaml")
    shutil.copytree(REAL_POLICY / "vocabularies", root / "vocabularies")
    return root
```

## Categorias de POL-000 utilizadas

- `dados_de_contato` (POL-000 §2.3) — POL-001
- `dados_de_perfil_comportamental` (POL-000 §2.9) — POL-002
- `dados_de_documentos_oficiais` (POL-000 §2.2) — POL-003, POL-004

Todas com `special_category: false`. Nenhuma alteração em POL-000 é
necessária.

## Tokens de vocabulário utilizados

- `operation`: `collection` (todas as quatro cláusulas)
- `control`: `consent_required` (POL-001, POL-003, POL-004),
  `anonymization_required` (POL-002)
- `lawful_basis` (referenciado nos requirement texts): `consent`
- `accepted_law_identifiers` (no header): `LGPD`

Nenhum token novo introduzido — pack consome inteiramente vocabulários
existentes em `policy/vocabularies/LGPD/`.

## Assimetrias deliberadas

**T02b AS-2 (semântica prefix-hierarchical) não é exercitada por este
pack.** AS-2 testa o caso em que query é mais específica que o
`statutory_reference` armazenado, o que requer cláusulas com referência
ao nível de `{lei, artigo}` puro (sem `inciso` nem `paragrafo`). Todas as
quatro cláusulas deste pack carregam ao menos um campo de especificidade
adicional além de lei+artigo — POL-001, POL-003 e POL-004 com `inciso: 1`,
POL-002 com `paragrafo: 2` — então uma query mais específica não pode ser
construída contra elas. Fixtures sintéticas para T02b AS-2 vivem em testes
específicos do T02b, separadas deste pack.

**`compliant` e `violation_candidate` de POL-002 não são exercitados.** O
inputSchema atual de `check_applicability` (canonical §4.3) não tem campo
para declarar transformação aplicada, então qualquer match contra POL-002
cai estruturalmente em `indeterminate`. Cobertura completa de POL-002 fica
para evolução pós-MVP, quando inputSchema for estendido com campo de
transformação declarada.

**POL-003 e POL-004 compartilham `applies_to`, `control` e
`statutory_reference` idênticos.** O diferencial entre as duas é apenas
redacional — POL-004 lista identificadores típicos (CPF, RG, CNH) e alinha
ao vocabulário canônico (`consent`). Deprecation por refino de redação é
narrativa defensável e mantém o pack na superfície mínima de teste, sem
introduzir tokens novos no vocabulary.

## Ressalvas conhecidas

- `policy_schema_version: "0.1.0"` em cada cláusula está alinhado ao header
  real. Se SCHEMA evoluir, bump simultâneo em todas as quatro.
- `effective_until: "2026-04-01"` em POL-003 é data sintética. Se algum
  teste validar coerência temporal entre `effective_until` da cláusula e
  `last_revision` do header da Política, ajustar para data anterior ao
  `last_revision` real de `policy.yaml`.
- POL-001, POL-003 e POL-004 todas apontam para Art. 7º, I LGPD. Isso é
  intencional — torna o pack útil para T02b AS-1 (lista matching) e T02b
  AS-3 (deprecated excluído de lista que contém actives matching).
