# Caso de avaliação — Inversão de sensibilidade na POL-007 (Art. 11 LGPD)

**Tipo**: limite conhecido do motor, documentado com causa-raiz e correção projetada.
**Status**: não corrigido no MVP (decisão consciente de escopo — ver §6).
**Evidência**: Reports `B-SENS-OK-001` e `B-SENS-INV-001` (pipeline determinístico, `eval/harness/reports/`).

---

## 1. Resumo

A avaliação empírica do sistema sobre casos de fronteira revelou que o motor de
verificação (`check_applicability`) produz vereditos **invertidos** para dados
pessoais sensíveis (`special_category`) sob a cláusula POL-007. Concretamente, o
motor aprova (`compliant`) uma base legal juridicamente **insuficiente** e reprova
(`violation_candidate`) a base legal juridicamente **correta** exigida pelo Art. 11
da LGPD.

O achado não decorre de erro na cláusula — a POL-007 está juridicamente correta. A
causa é uma sub-modelagem do motor: a decisão de conformidade não consulta a flag de
sensibilidade do dado, tratando dado sensível como dado comum.

Este documento registra o caso como exemplo de avaliação, com a causa-raiz
diagnosticada e a correção projetada, deixando a implementação como trabalho futuro
por decisão de escopo do MVP.

---

## 2. Contexto jurídico

A LGPD distingue dados pessoais comuns de dados pessoais **sensíveis**. Dado de
saúde é dado sensível (`special_category`, na taxonomia do POL-000). O regime de
base legal difere entre as duas classes:

- Para dado comum, o Art. 7º admite consentimento entre várias hipóteses, e o
  consentimento, quando usado, é o consentimento geral.
- Para dado sensível, o Art. 11, I exige **consentimento específico e destacado**
  para finalidades específicas — um consentimento *qualificado*, mais estrito que o
  consentimento comum. Não é o mesmo ato jurídico que o consentimento do Art. 7º.

A cláusula POL-007 modela corretamente essa exigência: governa `dados_de_saude`
(categoria marcada `special_category: true` no POL-000) sob coleta, exigindo
consentimento conforme o Art. 11, I.

A distinção que importa para o achado: juridicamente, o consentimento qualificado do
Art. 11 corresponde a uma base legal distinta do consentimento comum — neste sistema,
o token `explicit_consent` versus o token `consent`.

---

## 3. O comportamento do motor

O motor de verificação, ao avaliar um control `consent_required`, compara a base
legal declarada no código (`legal_basis`) contra o **literal canônico exato**
`consent`, do vocabulário `lawful_basis` do POL-000. A regra é deliberadamente
simples: se a base declarada é exatamente `consent`, o veredito é `compliant`; caso
contrário (ausência, ou valor fora do vocabulário canônico), é `violation_candidate`.

Esta comparação **não consulta a categoria do dado**. O motor não verifica se a
categoria avaliada é `special_category`; não distingue `consent` de
`explicit_consent`; não aplica o regime mais estrito do Art. 11 quando o dado é
sensível. A flag de sensibilidade existe no POL-000, mas não é lida no ponto de
decisão (`_verdict_for_control`).

---

## 4. O achado — a inversão

A avaliação confrontou a POL-007 com dois casos sintéticos de coleta de dado de
saúde, variando apenas a base legal declarada. Os vereditos emitidos, extraídos
verbatim dos Reports:

### Caso B-SENS-OK — base comum para dado sensível

O código declara `legal_basis = "consent"` (consentimento comum) para coleta de
`dados_de_saude`.

- **Veredito do motor**: `compliant`.
- **Evidência registrada**: *"Cláusula POL-007 (LGPD Art. 11, I) exige consentimento
  (R1: valor canônico 'consent' do vocabulário lawful_basis de POL-000); context
  declara legal_basis='consent'."*
- **Avaliação jurídica**: **incorreto**. Consentimento comum é base insuficiente
  para dado sensível (Art. 11, I exige consentimento específico e destacado). O motor
  aprovou uma conformidade que o Direito não reconhece.

### Caso B-SENS-INV — base qualificada (correta) para dado sensível

O código declara `legal_basis = "explicit_consent"` (o consentimento destacado que o
Art. 11 exige) para coleta de `dados_de_saude`.

- **Veredito do motor**: `violation_candidate`.
- **Evidência registrada**: *"Cláusula POL-007 (LGPD Art. 11, I) exige consentimento
  (R1: valor canônico 'consent' do vocabulário lawful_basis de POL-000); context
  declara legal_basis='explicit_consent', fora do vocabulário canônico."*
- **Avaliação jurídica**: **incorreto**. O código fez o juridicamente correto
  (consentimento qualificado para dado sensível). O motor reprovou a conformidade
  adequada porque `explicit_consent` não casa com o literal `consent`.

### A inversão

| Base legal declarada | Avaliação jurídica | Veredito do motor | Correto? |
|---|---|---|---|
| `consent` (comum) | insuficiente para sensível | `compliant` | não — aprovou o errado |
| `explicit_consent` (qualificado) | adequado (Art. 11, I) | `violation_candidate` | não — reprovou o certo |

O motor dá `compliant` para o juridicamente errado e `violation_candidate` para o
juridicamente certo. A inversão é completa e sistemática.

---

## 5. Causa-raiz

A causa não está na cláusula, mas na decisão do motor. A POL-007 carrega a
informação de que governa uma categoria sensível, e o POL-000 marca `dados_de_saude`
com `special_category: true`. Porém essa informação **não chega ao ponto de
decisão**: `_verdict_for_control`, ao avaliar `consent_required`, pergunta apenas se
`legal_basis == "consent"`, sem nunca perguntar se a categoria é sensível.

Em uma frase: o motor modela "consentimento exigido", mas não modela "consentimento
**qualificado** exigido para dado sensível". É uma sub-modelagem do regime do Art. 11,
não um defeito de implementação da regra que existe — a regra que existe está
correta para dado comum; ela simplesmente não cobre o caso sensível.

A separação entre correção da cláusula e correção do motor é o ponto central: a
cláusula é policy-correta; o motor é sub-modelado. As duas dimensões são auditáveis
separadamente porque cada veredito carrega a proveniência (qual cláusula, qual
versão de Política o produziu).

---

## 6. Correção projetada

A correção é um **gate de sensibilidade** em `_verdict_for_control`: antes de comparar
a base legal contra `consent`, verificar se alguma das categorias do candidato é
`special_category: true`. Em caso afirmativo, o token canônico aceito passa a ser o
consentimento qualificado (`explicit_consent`), não o comum (`consent`). A lógica
resultante:

| Categoria | `legal_basis` declarado | Veredito alvo |
|---|---|---|
| comum | `consent` | `compliant` |
| comum | ausente / outro | `violation_candidate` |
| **sensível** | `consent` (comum) | **`violation_candidate`** (insuficiente) |
| **sensível** | `explicit_consent` (qualificado) | **`compliant`** |

A implementação tocaria dois pontos (o token sensível já existe): (a)
`_verdict_for_control` passa a ler a flag `special_category` da categoria avaliada;
(b) quando a categoria é sensível, o token canônico aceito passa a ser
`explicit_consent` — que **já está** no vocabulário `lawful_basis` (Art. 11, I,
`category: sensitive_data`); falta apenas o motor consumi-lo, não adicioná-lo. A
decisão ramifica conforme a sensibilidade. Aplicada,
a correção inverte os dois Reports B-SENS de volta ao juridicamente correto:
B-SENS-OK passa a `violation_candidate`, B-SENS-INV passa a `compliant`.

---

## 7. Decisão de escopo — por que fica como trabalho futuro

A correção não foi implementada no MVP por decisão consciente de escopo, sob duas
considerações:

- **Risco de regressão sob prazo.** `_verdict_for_control` é o núcleo do motor; toda
  a suíte de vereditos de avaliação depende dele. Alterá-lo exige revalidar o conjunto
  inteiro, e o custo dessa revalidação excede a janela de entrega do trabalho.
- **Valor do achado preservado independentemente da correção.** Os dois Reports
  B-SENS constituem evidência empírica completa da sub-modelagem. O achado — com
  causa-raiz e correção projetada — é cientificamente íntegro sem a implementação;
  documentá-lo demonstra o rigor da avaliação tanto quanto corrigi-lo demonstraria.

A correção fica registrada como trabalho futuro de baixo risco conceitual (a lógica
está especificada acima) e custo de validação conhecido.

---

## 8. Significância para a avaliação

Este caso ilustra uma propriedade do método de avaliação adotado: o sistema foi
confrontado não apenas com casos de conformidade direta, mas com casos de fronteira
(dado sensível, base legal variando entre comum e qualificada), e a avaliação revelou
um limite real do motor que a inspeção do código sozinha não teria exposto. O sistema,
fiel ao seu princípio de não mascarar incerteza, registra o veredito que de fato
produz — e a avaliação registra honestamente que esse veredito está, neste caso,
juridicamente invertido, com a causa diagnosticada e a correção projetada.
