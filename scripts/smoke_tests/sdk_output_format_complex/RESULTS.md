# RESULTS — smoke_test sdk_output_format_complex (DD-T16)

Descoberta empírica: `output_format` aceita JSON Schema complexo? O
`sdk_output_format_lockdown` provou o caminho com schema FLAT (2 campos);
DD-T16 (`triager.md:198`, aberto) pergunta o que o flat não cobriu — união
discriminada no root, `$defs`/`anyOf` aninhado, união embrulhada. Decide o
encoding da saída dos subagentes Branch B (Triager, Matcher). Verificado contra
`claude-agent-sdk==0.2.87`, lockdown total (`allowed_tools=[]`,
`setting_sources=[]`, `mcp_servers={}`, `strict_mcp_config=True`,
`permission_mode="dontAsk"`, sem `betas`), auth Claude Code CLI,
Windows 11 / PS 5.1. Sessão Code #47.

> **AVISO — o exit code (1) e a síntese automática "BLOQUEIA o desenho do
> Matcher" MENTEM** (mesma classe de bug dos v3/v4 do `sdk_tool_error_channel`).
> O cenário B passa e o Matcher tem caminho claro. O vedado é só a codificação
> via `oneOf`/discriminator, não structured output complexo em geral. Ler os
> achados, não o exit.

## Cenários (stand-ins estruturais, não os modelos reais)

| Cenário | Construto JSON Schema | subtype | structured_output |
|---|---|---|---|
| A — root union | `oneOf` + discriminator no ROOT | success | **None** |
| C — wrapped union | objeto no root, mas `result` = `oneOf` + discriminator | success | **None** |
| B — $defs/nested | objeto, `$defs`/`$ref`, array-de-objetos, `anyOf [str,null]` | success | **populado e valida ✅** |

O elemento que A e C compartilham e B não tem é `oneOf` + discriminator
(união discriminada do Pydantic). Falha no root (A) **e** aninhado num objeto
(C). O `anyOf [T, null]` (nulabilidade), `$defs`/`$ref` e arrays de objetos do
B funcionam. Bate com o subset de structured outputs da Anthropic: `anyOf`
para nulabilidade é suportado; `oneOf`/discriminator estilo-OpenAPI não.

## Mecanismo — confirmado por probe (não inferido)

Probe de cenário único (A) dumpando o conteúdo do `AssistantMessage`. Dump
decisivo:

    AssistantMessage TextBlock:
      {"decision":"proceed","reason":"Trivial documentation typo fix ..."}
    ResultMessage subtype='success' structured_output=None

O modelo emitiu **`"reason"`**, mas o schema exigia **`"rationale"`**. Se a
constrained decoding (gramática do structured output) estivesse ativa, o
modelo NÃO conseguiria emitir um nome de campo fora do schema — a gramática
forçaria `rationale` e `structured_output` viria populado (como em B). Logo:

- `oneOf` no root faz o SDK **desligar o enforcement de gramática inteiro**.
- O JSON que aparece é dirigido pelo **prompt** ("devolva JSON"), não pelo
  schema — por isso tem campo errado.
- **Falha silenciosa tripla:** sem constrained decoding, sem
  `structured_output`, sem erro. Pior que "produziu o JSON certo mas não
  surfou" — o JSON nem é conforme.

Conclusão: **estrutural / gramática-dura, não comportamental.** `oneOf` não é
promptável-around. O contraste A-vs-B (mesmo SDK, mesma config) é a prova: o
schema de B com objeto/`$defs`/nullable foi aplicado e validado; o `oneOf` de
A não aplicou nada.

## Recomendação de desenho (Matcher e Triager)

Codificar variância como **objeto único com campo-enum + opcionais**, NÃO como
união discriminada:

    verdict: Literal["compliant","violation_candidate","indeterminate","not_applicable"]
    + campos opcionais por verdict (anyOf [T, null])

É a forma do cenário B — comprovadamente enforçada. Aplica-se aos 4 verdicts
do Matcher e à decisão do Triager.

- **DD-T16 responde POSITIVAMENTE** para o Matcher: há caminho claro.
- O fallback "embrulhar a união num objeto" (cenário C) **não salva** — a
  união continua sendo `oneOf` dentro do objeto, e dá `None` igual.
- **Companion-edit debt (não desta sessão):** `triager.md:198`
  (`TriagerDecision = Proceed | Skip`) é união discriminada. Se o schema de
  saída do Triager for gerado desse modelo, bate no mesmo `None`. Vira
  enum-tag flat object. Flagado, não aplicado aqui.

## Limite do observado

O mecanismo (gramática-off por `oneOf`) foi observado **diretamente** (o campo
`"reason"` prova), não composto. Não observado: os modelos reais
(`TriagerDecision`/`ClassifierOutput` verbatim — os stand-ins reproduzem os
construtos JSON Schema, não os modelos exatos); profundidade de aninhamento
além do B; comportamento em versão de SDK diferente de 0.2.87; e é um run por
cenário, não distribuição estatística. A pergunta ESTRUTURAL de DD-T16 está
respondida; fidelidade exata fica para quando os modelos reais existirem.

## Consequências registradas

- Saída do Matcher = objeto enum-tag (`verdict` Literal + opcionais), nunca
  `oneOf` — anotado no session-handoff da #48.
- Companion-edit a `triager.md:198` (união → enum-tag) — débito catalogado.
- Evidência: `smoke_test.py` (cenários A/B/C) + dump do probe de mecanismo
  (dobrado nesta seção; `_probe_oneof_mechanism.py` removido após consolidação).

Cross-ref: `sdk_tool_error_channel/RESULTS.md` (achado-irmão — o que o SDK
silenciosamente NÃO surfa ao consumidor: lá `structuredContent` de `@tool`,
aqui structured output sob `oneOf`); DD-T16 em `triager.md:198`;
`.claude/rules/sdk-mcp-conventions.md` (convenções de saída SDK/MCP por camada).
