# <component-name>

**spec_version**: 0.1.0

> Esqueleto canônico para specs de componentes do projeto, derivado da redação de `policy-reader.md` na sessão #05. Princípios de redação destilados durante o exercício estão documentados em formato compacto no `learning-log.md`.

> Este template assume componente que expõe contrato MCP (resources e/ou tools). Para componentes do tipo subagente — Triager, Detector, Classifier, Matcher, Reporter, coordinator — derivar `_template-subagent.md` na primeira spec de subagente da semana 3 (mesmo método de destilação aplicado a este template).

## 1. Identidade e propósito

**Nome canônico.** `<component-name>`

**Função.** <Uma sentença ancorada na frase de negócio canônica do projeto. Identifica o que o componente faz e quem o consome.>

**Posição na arquitetura.** Ver `docs/architecture-overview.md` §<seção>.

**Consumidores autorizados.** <Lista exclusiva. Quando aplicável, nomear mecanismo de enforcement (ex: configuração de `mcp_servers` no AgentDefinition, `allowed-tools` em skill frontmatter).>

**Stack e governança.** Implementação em <stack> conforme ADR-<XXXX>. Decisões de design governadas por ADR-<YYYY>.

## 2. Contrato com o artefato servido

### 2.1 Artefato e schema canônico

<Uma sentença declarando o que o componente serve e onde o artefato vive. Identifica o papel curador (jurídico, ML, dados) quando aplicável.>

O schema canônico é especificado em <`caminho/para/SCHEMA.md`>. A versão exigida pela implementação atual deste componente é `<schema_version>`.

<Se o artefato carregar versionamento próprio com mais de um eixo, descrever aqui cada eixo, sua função semântica e como o componente reporta. Caso contrário, suprimir este parágrafo.>

**MVP — escopo de schema.** <Declarar se o componente suporta um único schema canônico ou múltiplos, e se há variantes deferidas registrar referência ao ADR correspondente.>

### 2.2 Comportamento contratual perante estados do artefato

<Tabela cruzando estados do artefato (linhas) com operações expostas pelo componente (colunas). Cada célula declara o comportamento observável. Estados sem comportamento diferenciado podem ser omitidos da tabela — incluí-los apenas quando o comportamento muda.>

<Para cada estado que produz comportamento não-trivial, justificativa curta logo após a tabela explicando *por que* o comportamento é o que é. Justificativa nomeia a regra de negócio ou a propriedade de design que motivou a decisão. Justificativa não é redundante com a tabela — ela existe para o leitor da spec entender se a decisão se aplica a casos análogos no futuro.>

## 3. Resources expostos

<Se o componente não expõe resources MCP, omitir esta seção inteira e notar a ausência na §4 ou §7 quando relevante.>

<Frase introdutória curta: número de resources expostos, scheme adotado, referência ao ADR onde o scheme é justificado.>

### 3.<n> `<scheme>://<path>`

**URI.** <URI literal, marcando se é estática ou parametrizada com `{placeholder}`.>

**Conteúdo.** <Estrutura do payload em prosa + lista de campos. Para resources com itens (catálogos, listas), descrever estrutura de cada item. Para resources com objeto único, descrever os campos do objeto. Convenções de ordenação, presença condicional de campos, e limites de tamanho declarados explicitamente quando relevantes.>

**Semântica de leitura.** <Idempotente? Estado atual ou snapshot? Reload disparado por quê? Cacheável pelo consumidor?>

**Casos de erro.** <Erros de protocolo (Nível 1) e erros de domínio (Nível 2) que o consumidor pode encontrar ao ler. Resources tipicamente têm semântica de erro mais pobre que tools — explicitar quais condições viram erro e quais viram conteúdo válido (ex: lista vazia ≠ erro).>

## 4. Tools expostas

<Frase introdutória curta: número de tools expostas, princípio de nomeação, qualquer convenção transversal (ex: idioma da descrição, formato de identificador).>

**Naming convention.** Tools deste server aparecem para o agente (Claude Code ou Agent SDK) com o handle `mcp__<server-name>__<tool-name>` — namespace gerado pelo runtime ao expor tools de um MCP server configurado em `.mcp.json`. O nome simples (`<tool-name>`) é a forma usada nas subseções a seguir; a forma prefixada é a forma usada em `allowed-tools` de skill frontmatter, em `mcp_servers`/`allowed-tools` do AgentDefinition consumidor, e em matchers de hooks `PreToolUse`/`PostToolUse` que filtram tools deste server.

### 4.<n> `<tool_name>`

**Descrição (tool description).**

```
<Verbo de ação no início. Uma frase declarando o que a tool faz, em inglês.>

<Diferenciação explícita das outras tools do mesmo server: "Use this when... Do not use this when... — for that, use `<other_tool>`". Quando há mais de uma tool similar, listar uma por linha. Quando não há tools similares, omitir esta sub-seção.>

<Estrutura do output em prosa: principais campos retornados, condições que mudam o que aparece. Não duplicar o outputSchema; orientar o agente a encadear a tool com a próxima ação.>

<Condições de erro relevantes ao caller que mudam o comportamento. Não listar todos os errorCodes — só os que afetam o raciocínio do agente sobre o que fazer a seguir. Tabela completa em §5.>

<Side effects, se houver. Tools de leitura idempotentes podem omitir.>
```

**`inputSchema`.**

<Tabela com colunas: Campo, Tipo, Obrigatório, Descrição. Descrição curta orientada ao agente — diz semântica, não repete o tipo.>

**Output em sucesso.** <Esqueleto da estrutura retornada quando `isError: false`. Para retornos governados por schema externo, referenciar o schema e mostrar o esqueleto pertinente. Para retornos com variantes (ex: estado-dependentes), mostrar cada variante em bloco próprio com comentário inline distinguindo o caso.>

**Condições de erro específicas.** <Tabela com colunas: `errorCode`, Classe, `isRetryable`, Quando ocorre, `details`. Listar apenas os erros específicos desta tool. Tabela completa em §5.>

**Exemplos.** <Dois a três exemplos curtos: caso normal, caso de variante relevante (ex: estado especial do dado), caso de erro mais comum. Cada exemplo mostra input e output. Não exaustivo — ilustrativo.>

> Notas de redação para autores de spec:
>
> - Para tools que aceitam especificação parcial de chave hierárquica, declarar a regra de match no campo Descrição (tipicamente "prefix match").
> - Para tools onde empty result é resultado válido, declarar explicitamente na Descrição — sem isso, o agente trata vazio como erro de busca.
> - Para campos com vocabulário fechado, o `inputSchema` deve referenciar o schema canônico onde o vocabulário é declarado, não duplicar a lista.
> - Para tools cujo output varia por estado/veredito, documentar cada variante separadamente em blocos próprios — cada veredito com sua estrutura. Não tentar unificar em "estrutura comum + campos condicionais"; isso esconde a variação semântica.
> - Para tools que podem falhar em estado intermediário do artefato (ex: dado deprecated), a condição precisa estar no Campo 4 (Condições de erro) com `isRetryable` explícito e `details` carregando o que o caller precisa para recuperar.

## 5. Contrato de erro

### 5.1 Estrutura canônica do payload de erro

<Forma do objeto retornado quando `isError: true`. Quatro campos canônicos: `errorCode` (constante em inglês), `message` (humana em idioma do projeto), `isRetryable`, `details` (estruturado por `errorCode`). Justificativa curta da separação errorCode/message.>

<Placement no `CallToolResult` MCP: declarar que o objeto canônico de erro mora em `structuredContent` (canal nativo para JSON estruturado), e que `content[0]` carrega um `TextContent` cuja chave `text` reproduz `message` em prosa humana (fallback de retrocompatibilidade e legibilidade em logs). O único campo de erro nativo do MCP é o booleano `isError` — o contrato dos quatro campos é convenção do projeto sobreposta ao protocolo, materializando classes de erro e decisão de retry programaticamente. Mesma convenção vale para retornos de sucesso com payload estruturado: `structuredContent` carrega o objeto de veredito, `content[0].text` reproduz a prosa humana correspondente.>

### 5.2 Classes de erro

<Três classes: validation, business, system. Definição operacional de cada uma e regra de `isRetryable` por classe. Classes específicas do componente, se houver, declaradas com referência cruzada.>

### 5.3 Casos que parecem erro mas não são

<Lista exaustiva de condições que produzem `isError: false` mesmo quando parecem falha. Cada caso com justificativa curta. Esta sub-seção é crítica: ausência leva o caller a tratar resultado válido como falha e gerar retry desnecessário ou desistência cedo demais.>

### 5.4 Tabela consolidada de `errorCode`

<Tabela com colunas: `errorCode`, Classe, Retryable, Tools que emitem, Condição, Forma de `details`. Listar todos os `errorCode` do componente, inclusive os que aparecem em múltiplas tools (uma linha por código, não por par tool×código).>

<Nota declarando que erros de protocolo MCP não aparecem nesta tabela — são domínio do protocolo, não do componente.>

### 5.5 Princípio de evolução do contrato

<Regra de versionamento da spec quando o contrato de erro muda. Adicionar código é minor; remover ou ressemantizar é major. Referenciar ADR governante.>

## 6. Provenance e versionamento

### 6.1 Versão da spec

<Versão atual e convenção major/minor/patch aplicada à spec deste componente. Critério para estabilização (de 0.x para 1.0).>

### 6.2 Versão do componente

<Como o componente reporta sua própria versão e em quais condições. Especificamente: a versão do componente aparece nos retornos? Justificar sim/não.>

### 6.3 Versão dos artefatos servidos — handshake

<Mecanismo pelo qual o consumidor descobre a versão dos artefatos servidos antes de invocar tools. Tipicamente um resource de schema-version. Estrutura, semântica de fail-fast, comportamento em incompatibilidade.>

### 6.4 Versão dos artefatos em retornos relevantes

<Em quais retornos a versão dos artefatos aparece como provenance temporal. Justificar a presença/ausência por tool — leituras (retrieval) geralmente não precisam; vereditos e decisões geralmente precisam.>

### 6.5 Mutabilidade dos artefatos durante execução

<Comportamento do componente perante mudanças nos artefatos durante a execução. Hot reload, restart, leitura por request — declarar e justificar para o MVP. Deferimentos referenciados ao ADR.>

## 7. Não-objetivos e fronteiras

### 7.1 Não-objetivos do componente

<Lista de comportamentos que o componente poderia fazer mas explicitamente não faz. Cada item carrega: descrição, razão (eliminado por redundância, deferido por simplicidade do MVP, fora do papel do componente), referência ao ADR de deferimento quando aplicável.>

### 7.2 Não-objetivos do escopo do artefato servido

<Quando o artefato servido (Política, ruleset, modelo) é restrito a subconjunto deliberado, declarar aqui o subconjunto e o que fica fora. Para componentes que servem artefatos de escopo aberto, omitir esta sub-seção.>

### 7.3 Fronteira epistêmica do componente

<O que o componente consegue concluir e o que não consegue, em termos de capacidade fundamental (não de implementação atual). Esta sub-seção existe para evitar que implementadores ou consumidores assumam capacidades que o componente não pode ter mesmo em versões futuras. Quando o componente tem mecanismo de honestidade epistêmica (indeterminate, low-confidence, escalation), referenciá-lo aqui.>

### 7.4 Decisões deferidas

<Referência ao ADR governante de deferimentos relacionados ao componente. Não duplicar conteúdo do ADR; apontar.>

## 8. Critérios de aceitação

A implementação está completa quando todos os critérios abaixo forem demonstravelmente verdadeiros. Cada critério é verificável por teste automatizado ou inspeção direta.

### 8.<n> <Categoria>

<Para cada categoria de funcionalidade da spec (resources, tools por nome, contrato de erro, provenance, implementação), lista de critérios verificáveis em formato checklist `[ ]`. Critério bem formado nomeia condição observável, não atividade. "Tool retorna X em condição Y" é critério; "tool implementada" não é.>

### 8.<final> Review pass do `architecture-overview`

Ao finalizar a redação desta spec, executar review pass no `architecture-overview.md` procurando:

- Decisões da spec que tornam afirmação do `architecture-overview` obsoleta (sync via PR enxuto).
- Afirmações do `architecture-overview` que esta spec contradisse (resolver via ADR ou ajuste).