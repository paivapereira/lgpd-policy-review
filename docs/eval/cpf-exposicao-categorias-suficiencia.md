# Caso de avaliacao — Exposicao de `data_categories` e suficiencia de vocabulario sem demonstracao

**Tipo**: decisao de design validada empiricamente nos casos medidos + hipotese de escopo adiada (nao refutada) por medicao.
**Status**: exposicao implementada na branch `feat/expose-data-categories-vocab` (commit 51516e6); PR e merge pendentes. O `policy://examples` (few-shot dedicado) fica adiado do escopo de implementacao por suficiencia medida — nao refutado em geral (ver secao 5).
**Evidencia**: experimento `category_exposure_discriminant.py` (medicao live, 42 chamadas de modelo, root `policies/eval-lgpd`), dados crus em `eval/experiments/output/discriminant_raw.json`.

---

## 1. Resumo

Um run live do pipeline completo revelou que o Classifier devolvia
`data_categories: []` para todo candidato, colapsando o resultado a
`not_applicable`/POL-000. A causa-raiz era estrutural: o resource
`policy://vocabularies` nao expunha o vocabulario de categorias de dados, embora
o prompt do Classifier instruisse o modelo a classificar usando esse vocabulario.
O Classifier, obedecendo a disciplina de "nao inventar tokens fora do
vocabulario", devolvia lista vazia — comportamento correto diante de um
vocabulario ausente, nao defeito do modelo.

Corrigida a exposicao, abriu-se uma pergunta de design com consequencia de
escopo: bastaria expor a **lista** de categorias, ou o Classifier tambem
precisaria de **demonstracao** (exemplos de mapeamento codigo->categoria, que
seriam materializados num resource futuro `policy://examples`, de custo alto)?
Um experimento discriminante mediu as duas condicoes sobre cinco casos. Nos casos
medidos, a lista sozinha bastou — inclusive nas duas inferencias nao-literais
testadas — com acerto consistente e sem excecoes de classificacao; a demonstracao
nao adicionou poder. Em consequencia, o `policy://examples` foi **adiado** do
escopo de implementacao: a evidencia mostra que ele nao era necessario para os
casos medidos, o que e diferente de prova de que seria desnecessario em geral
(ver secao 5 para o residuo nao testado).

Este documento registra o caso como exemplo de avaliacao com desfecho positivo:
uma decisao de design confirmada nos casos medidos e uma peca de trabalho adiada
por metodo, com o limite da conclusao declarado.

---

## 2. Contexto tecnico

O Classifier e o terceiro estagio do pipeline. Sua funcao e extrair, para cada
candidato detectado, um contexto estruturado — entre outros campos, as
`data_categories` (categorias de dado pessoal que o codigo toca). Esses tokens
nao sao livres: pertencem a um vocabulario canonico definido pela clausula
POL-000 da Politica (nove tokens, entre eles `dados_de_identificacao`,
`dados_de_perfil_comportamental`, `dados_de_localizacao`,
`dados_de_documentos_oficiais`, alem das categorias sensiveis `dados_de_saude` e
`dados_biometricos`).

A disciplina do Classifier e deliberada: classificar apenas com tokens do
vocabulario publicado, e devolver vazio quando nenhum token e mapeavel — nunca
inventar. Essa disciplina depende de o vocabulario estar efetivamente disponivel
ao modelo via resource. Quando o vocabulario de categorias nao era exposto, a
disciplina produzia o resultado correto para a informacao disponivel (vazio),
mas inutil para o pipeline.

Ha duas formas distintas de prover vocabulario a um classificador, e a distincao
e o eixo do experimento. A primeira e a **restricao** (a lista de tokens validos
— o conjunto de respostas permitidas). A segunda e a **demonstracao** (exemplos
resolvidos de codigo mapeado a token — o ensino de como escolher entre as
respostas). Sao camadas ortogonais: a lista diz *quais* respostas sao validas; a
demonstracao ensina *como* mapear um caso novo a uma delas. A pergunta de escopo
era qual das duas o Classifier precisava.

---

## 3. O experimento

O experimento mediu se expor a lista de categorias (restricao) basta para
classificacao **correta**, ou se e tambem necessaria a demonstracao. Desenho:

Duas condicoes, identicas exceto pela presenca da demonstracao. **C1**
(names-only) expoe apenas os nomes dos tokens — a configuracao de producao.
**C2** (names + `canonical_examples`) acrescenta a cada token os exemplos
canonicos do POL-000 — a camada de demonstracao. A unica diferenca entre as duas
foi confirmada em processo, antes de qualquer chamada de modelo: nomes identicos,
presenca de exemplos como unico delta.

Cinco casos, cobrindo o espectro de dificuldade. Dois **literais** (L1, L2): o
campo `cpf`, cujo nome praticamente coincide com a categoria — o caso facil. Dois
**nao-literais** (N1, N2): campos cujo nome nao tem sobreposicao lexical com a
categoria — campos de rastreamento e historico de navegacao que um humano mapeia
a perfil comportamental (N1), e latitude/longitude/IP que mapeiam a localizacao
(N2). Esses dois sao os que de fato discriminam "lista basta" de "precisa de
demonstracao", porque exigem inferencia semantica, nao correspondencia de nome.
Um **controle verdadeiro-negativo** (TN): um acesso generico cuja classificacao
correta e abstencao (`[]`), guardando contra o modelo classificar em excesso.

**Divulgacao do controle de input (reprodutibilidade).** Os casos nao-literais
N1 e N2 nao usaram os fixtures crus do `eval/prs`. Usaram fixtures de
preocupacao-unica curados, derivados de INDET-001 e PROBE-UNGOV-001 com o gatilho
`cpf` **removido de proposito** (documentado em `eval/experiments/README.md`).
Razao: os fixtures originais carregam um `cpf` apenas para dar ao Detector um
gatilho Semgrep no pipeline completo; numa medicao isolada do Classifier sobre
inferencia *nao-literal*, esse `cpf` deixaria o modelo emitir tambem um token de
identificacao e contaminaria o ground truth estrito unico. Remove-lo isola o
sinal discriminante. Os casos L1/L2 mantiveram o `cpf` — ali ele *e* o sinal (o
caso literal). E um controle legitimo, mas significa que os inputs nao-literais
foram curados, nao retirados crus do conjunto de PRs.

A barra de sucesso foi classificacao **correta** contra o ground truth (nao
apenas saida nao-vazia), distinguindo quatro desfechos: correto, abstencao
indevida, erro de classificacao, e inconsistencia entre execucoes. Cada caso foi
executado multiplas vezes (cinco para os nao-literais e o controle, tres para os
literais), reportando a distribuicao, nao um resultado unico — porque o modelo e
nao-deterministico e a consistencia e, ela propria, um dado.

O experimento rodou contra a Politica de avaliacao `policies/eval-lgpd` (com
clausulas substantivas), nao contra a Politica semente (apenas POL-000), para que
um resultado vazio nao fosse confundido com ausencia de clausula governante.

**Categorias deliberadamente fora do experimento.** As categorias sensiveis
(`dados_de_saude`, `dados_biometricos`) foram excluidas da matriz de proposito,
para nao tocar o caso da inversao POL-007 (documentado separadamente). A matriz
tambem nao incluiu nenhum token de mapeamento idiossincratico (categoria cujo
significado o modelo nao pudesse inferir do nome). Esse recorte limita o alcance
da conclusao (secao 5).

---

## 4. Resultado

A tabela abaixo reproduz a distribuicao de desfechos por caso e condicao, sobre
as execucoes de cada celula.

| Caso | Execucoes | Ground truth | C1 (lista) | C2 (lista + exemplos) |
|---|---|---|---|---|
| L1 — `cpf` nu | 3 | identificacao ou documentos oficiais (R6) | correto: 3 | correto: 3 |
| L2 — `cpf` em modelo rico | 3 | identificacao ou documentos oficiais (R6) | correto: 3 | correto: 3 |
| N1 — campos comportamentais | 5 | perfil comportamental | correto: 5 | correto: 5 |
| N2 — campos de localizacao | 5 | localizacao | correto: 5 | correto: 5 |
| TN — acesso generico | 5 | abstencao (`[]`) | correto: 5 | correto: 4 · erro de transporte: 1 |

Tres leituras factuais dos numeros:

Os casos nao-literais (N1, N2) — o teste decisivo — acertaram em todas as
execucoes ja sob C1, a condicao que oferece apenas a lista. A demonstracao (C2)
nao os melhorou; note-se que ela nao *poderia* aparecer como melhoria, porque o
acerto sob C1 ja estava no teto (5/5). O Classifier inferiu corretamente, a
partir do nome dos campos e do contexto, que dados de rastreamento sao perfil
comportamental e que coordenadas e IP sao localizacao — sem qualquer exemplo de
mapeamento, nas duas categorias transparentes testadas.

A unica celula nao-correta foi uma falha de **transporte**, nao de classificacao:
uma das execucoes do controle sob C2 teve o stream de comunicacao interrompido
antes de qualquer resposta do modelo. Registrada honestamente como erro de
execucao, nao re-executada. As outras quatro execucoes do controle abstiveram
corretamente.

Nos casos do `cpf`, o modelo emitiu `dados_de_documentos_oficiais` em todas as
execucoes, nunca `dados_de_identificacao`. Duas observacoes factuais, sem
sobre-leitura: primeiro, `cpf` e literalmente um `canonical_example` de
`dados_de_documentos_oficiais` no POL-000, de modo que essa saida e o mapeamento
literal natural do campo, nao evidencia de um juizo ponderado entre categorias
(o experimento nunca testou se o modelo extrai `identificacao` de campos como
`nome`/`username`, porque o candidato foi sempre a linha do `cpf`). Segundo, o
ground truth canonico do COMP-001 em `eval/cases.yaml:46` e
`dados_de_identificacao`; a saida do modelo **diverge** desse token canonico e
pontua "correto" apenas pela regra R6 (aceitar ambos os tokens, dado que o CPF e
legitimamente ambiguo entre identificacao e documento oficial). Essa tensao entre
a saida do modelo e o ground truth canonico fica registrada, nao suavizada.

---

## 5. Leitura e decisao de escopo

A logica de leitura foi fixada antes da medicao: se os casos nao-literais
acertassem sob C1, a lista bastaria para esses casos. Foi o que ocorreu. A
conclusao, **escopada ao que foi medido**: expor a lista de categorias e
suficiente para o Classifier classificar corretamente nas categorias
transparentes testadas (documento oficial — o token que o `cpf` de fato
produziu, nunca `identificacao` —, perfil comportamental e localizacao),
inclusive em inferencia nao-literal; nesses casos a demonstracao
via `canonical_examples` nao adicionou poder.

A consequencia de escopo e que o resource `policy://examples` — que exigiria um
PR autonomo e uma emenda de decisao arquitetural, de custo elevado — fica
**adiado** do escopo de implementacao imediato, porque a evidencia mostra que ele
nao era necessario para os casos medidos. Importante distinguir duas afirmacoes
que e tentador colapsar: a **decisao de prazo** (nao construir o `policy://examples`
agora) esta sustentada; a **afirmacao geral** (o `policy://examples` e desnecessario
em qualquer caso) **nao** esta, e o experimento nao a prova.

O residuo nao testado, que delimita a conclusao:

- **Categorias sensiveis** (`dados_de_saude`, `dados_biometricos`) — excluidas da
  matriz de proposito; nao se mediu se a lista basta para elas.
- **Tokens idiossincraticos** — categorias cujo significado o modelo nao infira
  do nome. As tres categorias testadas sao semanticamente transparentes; a lista
  pode nao bastar para uma categoria opaca.
- **Politicas futuras** — vocabularios de outras Politicas (ou versoes futuras da
  LGPD) cujos tokens sejam menos transparentes que os atuais.

Para qualquer um desses, a questao "lista basta ou precisa de demonstracao"
permanece aberta, e o `policy://examples` permanece como opcao disponivel, nao
descartada. A razao tecnica do resultado obtido e interpretavel (hipotese
explicativa, nao algo que o experimento provou): as tres categorias testadas tem
nomes que descrevem o que governam, e o modelo traz conhecimento de mundo
suficiente para mapea-las sem exemplos. A demonstracao so seria necessaria onde
o mapeamento fosse idiossincratico — o que esta fora do que esta matriz mediu.

---

## 6. Significancia para a avaliacao

Este caso ilustra duas propriedades do metodo de avaliacao, ambas positivas.

A primeira e o valor de medir antes de construir. Uma hipotese de design
plausivel — "o Classifier precisara de exemplos de mapeamento" — foi testada em
vez de assumida, e a medicao mostrou que, para os casos medidos, ela nao se
sustentava. Construir o `policy://examples` por suposicao teria consumido esforco
substancial para ganho nulo nesses casos. O metodo de separar a condicao de
controle (lista) do tratamento (lista + demonstracao), e exigir que o tratamento
provasse adicionar poder antes de ser adotado, e o que permitiu adiar a peca com
seguranca — mantendo-a disponivel para o residuo nao testado.

A segunda e o rigor do desenho experimental: a condicao de controle nao foi
contaminada com a demonstracao (os exemplos ficaram atras de uma chave
experimental, ausentes na configuracao de producao, confirmado em processo antes
de qualquer chamada de modelo); os casos discriminantes foram inferencias
genuinamente nao-literais (e nao o caso facil do nome coincidente); a barra de
sucesso foi classificacao correta e nao mera saida nao-vazia; cada caso foi
medido em multiplas execucoes com a inconsistencia tratada como dado; e o unico
desfecho nao-correto foi corretamente atribuido a falha de transporte, nao a erro
de classificacao — distincao que o registro honesto preservou em vez de mascarar
com uma re-execucao. A limitacao a registrar e o efeito-teto: como o controle (C1)
ja foi perfeito, o experimento conclui "tratamento nao foi necessario nestes
casos", nunca "tratamento nao adiciona nada em geral"; com duas categorias
nao-literais e uma falha de transporte, a forca da conclusao e "consistente e sem
excecoes de classificacao nos casos medidos", nao mais que isso.

O contraste com o caso POL-007 (documentado separadamente) e instrutivo: la, a
avaliacao revelou um limite do motor que ficou registrado como trabalho futuro;
aqui, a avaliacao confirmou uma decisao de design nos casos medidos e adiou
trabalho futuro. Ambos sao resultados legitimos de uma avaliacao rigorosa — o que
os une e que a medicao, nao a suposicao, determinou a conclusao, e em ambos o
limite da conclusao foi declarado em vez de extrapolado.