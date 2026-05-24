# Pack alternativo de rule set sintético (alternative_rule_set_synthetic)

Pack isolado com 1 regra Semgrep alternativa + 1 snippet positivo + este
README. Alvo de `SEMGREP_RUNNER_ROOT` durante mini-exercise do gate
Milestone B (sessão Chat #34+).

## Propósito

Exercita **RF-008 rule-set-axis** — propriedade arquitetural "substituir
rule set sem refactor em `src/`". O gate manual aponta
`SEMGREP_RUNNER_ROOT` para o subdiretório `rules/` deste pack, executa
`scan_diff` via Inspector contra o snippet positivo, e confirma que
`synthetic-iban` é carregada e dispara — sem nenhuma modificação em
`src/mcp_servers/semgrep_runner/` ou em `mcp_servers/semgrep_runner/rules/`.

Convenção redefinida na sessão Chat #34: manual exercise via MCP Inspector
fica dispensado para RF-001/RF-002 (cobertas integralmente por pytest
task-level T05–T07) e fica reservado a RF-008 — propriedade não-testável
funcionalmente por pytest.

## Conteúdo

```
alternative_rule_set_synthetic/
├── rules/
│   └── synthetic_iban.yaml          ← alvo de SEMGREP_RUNNER_ROOT
├── synthetic_iban_function_param.py ← snippet positivo
└── README.md                        ← este arquivo
```

- `rules/synthetic_iban.yaml` — 1 regra Semgrep alternativa
  (`synthetic-iban`) detectando coleta candidata de IBAN em parâmetro
  de função Python. Estrutura paralela a `br_cpf.yaml` do rule set de
  produção (mesmas keys top-level, mesmo `pattern-either` com 2
  patterns untyped + typed); conteúdo divergente (IBAN sintético).
- `synthetic_iban_function_param.py` — snippet positivo Python que
  dispara `synthetic-iban` via parâmetro `iban: str` em
  `def process_payment(...)`.

## Layout: por que `rules/` em subdir?

Decisão de layout do pack ratificada na sessão Chat #34 pré-criação. O
loader `semgrep-runner` consome `SEMGREP_RUNNER_ROOT` como sendo o
**diretório de regras em si** (não um parent que contém `rules/`) —
confirmado em [loader.py:36-59](../../../../../src/mcp_servers/semgrep_runner/loader.py#L36-L59).

Pack isola o rule-set-target do loader (`rules/synthetic_iban.yaml`) dos
auxiliares de exercise (snippet `.py`, README). Separação espelha
convenção de produção: regras BR em
[mcp_servers/semgrep_runner/rules/](../../../../../mcp_servers/semgrep_runner/rules/),
snippets BR em
[tests/mcp_servers/semgrep_runner/fixtures/recognizers_pack_br/](../recognizers_pack_br/).
Pack alternativo replica a convenção dentro do próprio diretório.

Inspector exercise aponta:

```
SEMGREP_RUNNER_ROOT=<repo>/tests/mcp_servers/semgrep_runner/fixtures/alternative_rule_set_synthetic/rules/
```

Não confundir com o pack root — apontar o env var para o pack root faria
o loader encontrar zero `*.yaml` (snippet `.py` e README seriam ignorados
pelo glob) e disparar `RulesLoadError("Rule set vazio...")`.

## Não é pack de produção

- Não estender com regras adicionais sem refatoração de propósito
  declarada em sessão Chat. Escopo mínimo (1 regra + 1 snippet) é
  deliberado: o gate exercita a propriedade arquitetural "trocar rule
  set sem refactor em `src/`", não cobertura adicional de detecção.
- Não é consumido por nenhum teste pytest. Pack vive isolado, exclusivo
  do exercise manual. Modificar `test_recognizers_br.py` ou
  `conftest.py` para apontar para este pack seria desvio de escopo.
- Identificador `iban` é sintético/exemplar — escolhido por ser
  identificador financeiro europeu (fora do domínio LGPD brasileiro),
  evidenciando a substituibilidade do rule set. Nenhum IBAN real é
  usado; o snippet declara apenas o parâmetro `iban: str` sem valor
  literal de conta.

## Relação ao pack BR

Paralelo estrutural a
[recognizers_pack_br/](../recognizers_pack_br/) (Latin square de
9 snippets exercitando 6 regras `br-*` de produção). Conteúdo divergente:
pack BR é cobertura de produção (rule set real consumido pelo Detector
em Milestone C); este pack é fixture pontual para gate arquitetural
RF-008.

Convenção de identificadores sintéticos alinhada a
[`.claude/rules/privacy-safety.md`](../../../../../.claude/rules/privacy-safety.md)
§PII — identificadores apenas sintéticos, sem dados reais.
