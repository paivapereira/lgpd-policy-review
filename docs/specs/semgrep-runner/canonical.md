# semgrep-runner

**spec_version**: 0.1.0

## 1. Identidade e propósito

**Nome canônico.** `semgrep-runner`

**Função.** Servidor MCP que expõe a execução de Semgrep diff-aware sobre o
checkout de um pull request como tool, retornando candidatos de tratamento
de dados pessoais detectados pelo conjunto curado de regras do projeto, para
uso pelo subagente Detector no sistema de code review.

**Posição na arquitetura.** Ver `docs/architecture-overview.md` §4.2 (MCP
servers) e §5.2 (Detector como consumidor).

**Consumidores autorizados.** Subagente Detector, exclusivamente. Restrição
materializada via configuração de `mcp_servers` no AgentDefinition do
Detector (`architecture-overview.md` §5.7). Outros subagentes não têm este
servidor em seu inventário de tools.

**Stack e governança.** Implementação em FastMCP 3.x conforme ADR-0004.
Invocação do binário Semgrep via subprocess. Decisões de design deste
componente são governadas pelo ADR-0002.

## 2. Contrato com o artefato servido

### 2.1 Artefato e versionamento

Este componente serve **detecção sintática de candidatos a tratamento de
dados pessoais**, materializada por um conjunto curado de regras Semgrep
versionadas em Git sob `mcp_servers/semgrep_runner/rules/`. As regras são
artefato declarativo do projeto, com ciclo de vida desacoplado da evolução
deste componente — adicionar uma regra de detecção de novo identificador
brasileiro não exige mudança no código do server.

O conjunto de regras carrega versão própria reportada via `rules_version` em
todo finding emitido. Mecanismo de geração — ver §6.

**MVP — escopo de regras.** O MVP cobre regras Semgrep single-file: cada
regra matcha em uma única região contígua de um único arquivo. Suporte a
findings interfile (regras com taint analysis cross-file via metavariáveis
e traces) é deferimento explícito registrado em ADR-0002.

**MVP — escopo do rule set per-cliente.** O MVP carrega um único rule set
bundled no projeto, com recognizers brasileiros como caso-piloto, comum a
todas as invocações do servidor. Rule set per-cliente — diretórios
separados governados por identidade do cliente, análogo a como
`policy-reader` é per-cliente via troca de Política sob `policy/`
(ADR-0005 Decision 1) — é deferimento explícito registrado em §7.

### 2.2 Motor de execução

O componente delega análise estática ao binário `semgrep` instalado no PATH
do ambiente de execução. Funcionalidade nativa de diff-aware scan via
`--baseline-commit` é o mecanismo central usado pela tool exposta — o
componente não reimplementa diferenciação de findings, delega ao Semgrep.

**Flags obrigatórias do subprocess Semgrep.** Independente da combinação de `base_ref`/`head_ref` ou do estado do rule set, o componente sempre invoca `semgrep scan` com três flags constantes:

- `--json` — Output em JSON conforme schema versionado em `semgrep-interfaces/semgrep_output_v1.jsonschema`. Forma de parsing estável; output text e SARIF são reservados para consumo humano, não para o componente.
- `--metrics=off` — Desabilita telemetria opcional do Semgrep. Decisão arquitetural fechada em ADR-0010: componente opera sem integração Semgrep AppSec Platform (`SEMGREP_APP_TOKEN` não é lido). Passar `--metrics=off` materializa essa decisão de modo robusto, independente do estado do token.
- `--baseline-commit <base_ref>` — Habilita diff-aware scan nativo do Semgrep. Mecanismo central usado pela tool (parágrafo anterior); sem este flag, o componente reimplementaria diff awareness.

O componente **não passa `--error`** ao subprocess. Comportamento default do Semgrep (exit 0 mesmo com findings) é o desejado: findings vivem no payload retornado pelo componente, não no exit code do subprocess. Esta decisão alinha com RNF-002 (sistema informativo, não-bloqueante).

Versão mínima aceita do binário: `semgrep` 1.x. Pin formal:
`semgrep==1.163.0`, instalado via `uv tool install` conforme ADR-0010.

Token Semgrep AppSec Platform (`SEMGREP_APP_TOKEN`) **não é requerido**.
Componente opera com Semgrep open-source sem login — ver §7.

## 3. Resources expostos

Este componente **não expõe resources MCP**.

A decisão é deliberada e simétrica ao tratamento de regras Semgrep como
insumo interno do server, não como conteúdo navegável pelo caller. O
Detector consome findings produzidos pela tool em §4; não enumera, lê, ou
raciocina sobre o conteúdo das regras antes de invocar o scan. Princípio
aplicado: Resource vs Tool — discriminação pela leitura cognitiva. A
assimetria em relação a `policy-reader` (que expõe ambos) é deliberada e
caso-teste do princípio.

## 4. Tools expostas

### 4.1 Naming convention

Tool exposta por este server segue convenção `mcp__semgrep-runner__<tool>`
gerada pelo runtime MCP. O handle completo é o usado em `allowed-tools` no
frontmatter do AgentDefinition do Detector e em matchers de hooks. Dentro
do código do server, o nome local da tool é `scan_diff`.

### 4.2 `scan_diff`

**Description (inglês, sem markdown).**

Scans the Git diff between base_ref and head_ref using the project's curated Semgrep rule set, returning findings that match any rule in the set. Use this when the caller has the BASE and HEAD refs of a pull request and needs to identify candidate sites for downstream classification. The rule set is server-side curated and not callable-parameterizable; it is fixed at server build time. The MVP rule set covers Brazilian personal data identifiers (CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde), but the component itself is domain-agnostic — rule set substitution is the supported path for different jurisdictions or detection domains.

Findings are single-file: the MVP does not perform cross-file taint analysis. Each finding carries rule provenance (rule_id), location (file path, line range), and code snippet. Empty findings list is a valid success outcome — the diff was scanned and no rules matched.

Returns success with findings list (possibly empty) on completion. Returns business error if Git refs are unresolvable, system error if the scan times out or the Semgrep binary fails. Operation is synchronous and may take seconds to minutes depending on diff size.

Tempo máximo de execução configurável via variável de ambiente
`SEMGREP_RUNNER_TIMEOUT_SECONDS`; default 300s. Excedido o limite,
retorna `SCAN_TIMEOUT` (ver §5).

**Distinção: timeout do processo vs. timeout interno do Semgrep.** `SEMGREP_RUNNER_TIMEOUT_SECONDS` (default 300s) governa o **budget total** do subprocess Semgrep, materializado via o mecanismo de timeout do runtime que invoca o subprocess (decisão de T06 sobre primitivo Python específico — `subprocess.run`, `Popen` + `wait`, `asyncio` — sem implicação para o contrato). Após expiração, o processo recebe SIGTERM seguido de SIGKILL e o componente emite `SCAN_TIMEOUT`. Este timeout é **ortogonal** ao flag `--timeout` do Semgrep CLI (default 5s por rule por arquivo, multiplicado por `--timeout-threshold` default 3): o flag interno governa quanto tempo uma única rule pode rodar em um único arquivo; o componente **não passa `--timeout`** ao subprocess, deixando o default do Semgrep. Caller que precisa controle fino do budget interno é responsabilidade futura (deferimento explícito ADR-0002 ou T06+).

**Input.**

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `base_ref` | string | sim | Git ref (commit hash, branch name, or tag) representing the baseline against which new findings are computed. |
| `head_ref` | string | sim | Git ref representing the current PR state to scan. |

**Output em sucesso.**

```yaml
{
  rules_version: <string>,          # top-level provenance estática (hash do rule set, ver §6)
  semgrep_version: <string>,        # top-level provenance estática (versão do binário invocado)
  scan_metadata: {                  # dynamic per-scan
    base_ref: <string>,             # 40-char hex commit hash, resolvido do input
    head_ref: <string>,             # 40-char hex commit hash, resolvido do input
    files_scanned: <int>,           # contagem de arquivos distintos no diff
    elapsed_seconds: <float>        # tempo decorrido do scan
  },
  findings: [
    {
      rule_id: <string>,            # identificador da regra Semgrep que disparou
      rule_severity: <enum>,        # info | warning | error — lowercase normalizado de Semgrep uppercase
      rule_message: <string>,       # texto da regra (campo message do YAML Semgrep)
      location: {
        path: <string>,             # relativo ao repo root
        start_line: <int>,          # 1-indexed
        start_col: <int>,           # 1-indexed
        end_line: <int>,            # 1-indexed
        end_col: <int>              # 1-indexed
      },
      snippet: <string>             # excerpt no location do finding
    },
    ...
  ]
}
```

**Ordenação de `findings`.** Lista ordenada por `(location.path, location.start_line)` ascendente. Ordem estável entre invocações sob o mesmo input — invariante para callers que processam findings sequencialmente.

**Empty result.** `findings: []` com sucesso é estado normal — significa que
o diff não introduziu candidatos detectáveis pelas regras curadas. Não
indica falha de scan. `scan_metadata` está sempre presente, mesmo quando
`findings` é vazio, para manter provenance auditável.

**Convenção de wire format.** Wire `isError: false` em TODOS os retornos
do componente — sucesso, empty result, e erros de domínio (classes
business/system). Discriminação semântica opera por presença do campo
`errorCode` em `structuredContent`: sucesso carrega `scan_metadata` +
`findings` sem `errorCode`; erro carrega `{errorCode, message,
isRetryable, details}` sem `findings` ou `scan_metadata`. Wire
`isError: true` fica reservado para falhas de protocolo MCP emitidas
pelo framework FastMCP — input sintaticamente inválido rejeitado por
`inputSchema`, tool inexistente, transport-level errors — não pelo
componente. Convenção segue ADR-0002 Decision 1 (placement híbrido
`structuredContent` + `content[0].text`) e ADR-0002 §3 amendment
2026-05-17 (Option B — discriminador implícito por `errorCode` adotado
para acomodar limitação framework-vs-spec do FastMCP 3.2.4 confirmada
em sessão #20).

**Condições de erro específicas.** Ver §5.

**Exemplos.** Ver §4.3.

### 4.3 Exemplos

*Caso normal — scan retorna candidatos em dois arquivos diferentes.*

```
Input: { "base_ref": "main", "head_ref": "feat/onboarding-cpf" }

Output: {
  "isError": false,
  "structuredContent": {
    "rules_version": "sha256:b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0",
    "semgrep_version": "1.92.0",
    "scan_metadata": {
      "base_ref": "a3f5b1c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2",
      "head_ref": "9d8e7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d",
      "files_scanned": 5,
      "elapsed_seconds": 47.3
    },
    "findings": [
      {
        "rule_id": "br-cpf-leak",
        "rule_severity": "warning",
        "rule_message": "Possível tratamento de CPF sem anonimização declarada",
        "location": {
          "path": "src/checkout/forms.py",
          "start_line": 42,
          "start_col": 9,
          "end_line": 42,
          "end_col": 38
        },
        "snippet": "user.cpf = request.form['cpf']"
      },
      {
        "rule_id": "br-cnpj-in-log",
        "rule_severity": "error",
        "rule_message": "CNPJ sendo escrito em log estruturado",
        "location": {
          "path": "src/billing/audit.py",
          "start_line": 87,
          "start_col": 5,
          "end_line": 87,
          "end_col": 56
        },
        "snippet": "logger.info('Empresa cadastrada', cnpj=company.cnpj)"
      }
    ]
  },
  "content": [
    {
      "type": "text",
      "text": "Scan concluído em 47.3s. Encontrados 2 candidatos: src/checkout/forms.py:42 (br-cpf-leak), src/billing/audit.py:87 (br-cnpj-in-log)."
    }
  ]
}
```

*Empty result — diff não introduziu candidatos detectáveis. `isError: false`, `scan_metadata` presente, `findings: []` (estado normal, não falha).*

```
Input: { "base_ref": "main", "head_ref": "docs/update-readme" }

Output: {
  "isError": false,
  "structuredContent": {
    "rules_version": "sha256:b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0",
    "semgrep_version": "1.92.0",
    "scan_metadata": {
      "base_ref": "a3f5b1c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2",
      "head_ref": "1c2b3a4f5e6d7c8b9a0f1e2d3c4b5a6f7e8d9c0b",
      "files_scanned": 1,
      "elapsed_seconds": 12.1
    },
    "findings": []
  },
  "content": [
    {
      "type": "text",
      "text": "Scan concluído em 12.1s. Nenhum candidato detectado no diff."
    }
  ]
}
```

*Erro de classe system — scan excedeu `SEMGREP_RUNNER_TIMEOUT_SECONDS` (default 300s). Wire `isError: false` (Option B); discriminação por presença de `errorCode` em `structuredContent`; prosa em `content[0].text` reproduz `message`.*

```
Input: { "base_ref": "main", "head_ref": "feat/large-refactor" }

Output: {
  "isError": false,
  "structuredContent": {
    "errorCode": "SCAN_TIMEOUT",
    "message": "Scan excedeu o limite de 300 segundos. Subprocess Semgrep terminado após grace period.",
    "isRetryable": true,
    "details": {
      "timeout_seconds": 300,
      "elapsed_seconds": 312.4,
      "partial_findings_discarded": true
    }
  },
  "content": [
    {
      "type": "text",
      "text": "Scan excedeu o limite de 300 segundos. Subprocess Semgrep terminado após grace period."
    }
  ]
}
```

*Erro de classe business — `base_ref` resolveu sintaticamente como ref mas não existe no repositório atual. Wire `isError: false`; envelope discriminado por presença de `errorCode`; `isRetryable: false` porque o caller precisa corrigir o ref antes de tentar novamente.*

```
Input: { "base_ref": "abc123nonexistent", "head_ref": "feat/onboarding-cpf" }

Output: {
  "isError": false,
  "structuredContent": {
    "errorCode": "GIT_REF_NOT_FOUND",
    "message": "Ref 'abc123nonexistent' não encontrada no repositório atual.",
    "isRetryable": false,
    "details": {
      "ref_param": "base_ref",
      "ref_value": "abc123nonexistent",
      "hint": "Verifique o valor passado; commits removidos por force-push, refs órfãs após cleanup de branches, ou shallow clone sem o histórico necessário são causas comuns."
    }
  },
  "content": [
    {
      "type": "text",
      "text": "Ref 'abc123nonexistent' não encontrada no repositório atual."
    }
  ]
}
```

## 5. Contrato de erro

Discriminação semântica sucesso-vs-erro opera por **presença do campo `errorCode` em `structuredContent`**: sucesso nunca carrega `errorCode`; erro carrega o envelope `{errorCode, message, isRetryable, details}` em `structuredContent`. Cada `errorCode` listado em §5.4 materializa cenário de falha de domínio do `semgrep-runner` e vive dentro do payload, não no nível protocolar.

Sub-seções abaixo: estrutura canônica do payload (§5.1), classes de erro (§5.2), casos que parecem erro mas não são (§5.3), tabela consolidada de `errorCode` (§5.4), princípio de evolução do contrato (§5.5).

### 5.1 Estrutura canônica do payload de erro

Quatro campos canônicos: `errorCode` (constante em inglês, MAIÚSCULAS_SNAKE, estável entre versões da spec), `message` (humana em português, prosa orientada ao operador ou agente que lê o erro), `isRetryable` (booleano que sinaliza ao caller se retry é caminho viável de remediação), `details` (objeto estruturado cuja forma depende de `errorCode` — ver tabela §5.4). A separação errorCode + message permite que o caller programaticamente roteie por código estável enquanto o humano lê a mensagem.

**Placement no `CallToolResult` MCP.** O envelope canônico mora em `structuredContent` (canal nativo do MCP para JSON estruturado), e `content[0]` carrega um `TextContent` cuja chave `text` reproduz `message` em prosa humana (fallback de legibilidade em logs e retrocompatibilidade com callers que só lêem `content`). O único campo de erro nativo do MCP é o booleano `isError` — wire `isError: true` é reservado para falhas de protocolo emitidas pelo framework FastMCP (input rejeitado por `inputSchema`, tool inexistente, transport-level), não pelo componente. Convenção de Option B materializada em ADR-0002 §3 amendment 2026-05-17: discriminação sucesso-vs-erro de domínio é semântica (presença de `errorCode`), não protocolar (flag `isError` permanece `false`).

### 5.2 Classes de erro

Três classes: **validation**, **business**, **system**. Definição operacional de cada uma e regra de `isRetryable` por classe:

- **validation** — Input sintaticamente válido mas semanticamente inválido contra vocabulário ou regra do componente. `isRetryable: false` por classe (retry sem mudar input não tem caminho de remediação; caller corrige input e reinvoca).
- **business** — Estado do mundo (refs Git, histórico, etc.) incompatível com a operação solicitada. `isRetryable: false` por classe (retry sem mudar estado do mundo não muda outcome; caller corrige estado e reinvoca, ou usa caminho alternativo).
- **system** — Falha em recurso externo (subprocess, binário, filesystem) ou em invariante interno do componente. `isRetryable` varia por errorCode específico: timeouts e falhas transient são retryable; binário ausente ou rule set inválido não são.

**A classe validation é vazia neste componente — ausência de validation errors é declaração positiva, não omissão.** Os dois inputs de `scan_diff` (`base_ref`, `head_ref`) são strings não-vazias declaradas em `inputSchema`; o runtime FastMCP rejeita inputs sintaticamente inválidos antes de chegar ao código do componente (rejeição emite wire `isError: true` pelo framework, não erro de domínio classe validation). Declaração positiva da classe vazia materializa princípio do ADR-0002 §4.

### 5.3 Casos que parecem erro mas não são

**Empty findings.** Scan rodou com sucesso, atravessou o diff, nenhuma regra matcheou. **Estado normal**, retornado como `{scan_metadata: {...}, findings: []}` com `isError: false`.

**Diff vazio.** `base_ref == head_ref` ou commits idênticos. Semgrep roda, não tem nada para escanear, retorna sucesso com lista vazia. Mesmo tratamento.

**Findings em arquivos preexistentes.** Filtrados nativamente pelo `--baseline-commit` do Semgrep antes de chegar ao caller. Não emergem como findings visíveis.

**Stderr não-vazio em exit code 0.** Semgrep emite warnings ocasionais no stderr para rules que não matcheam o target language ou para arquivos parcialmente parseáveis, mesmo quando o scan completa com sucesso (exit 0). Estado normal — warnings são descartadas pelo componente; payload retornado reflete apenas o scan structure (findings matched + scan_metadata). Não é erro. Comportamento observado contra Semgrep 1.163.0 (pin do projeto per ADR-0010).

### 5.4 Tabela consolidada de `errorCode`

| `errorCode` | Classe | `isRetryable` | Tools que emitem | Quando ocorre | `details` |
|---|---|---|---|---|---|
| `GIT_REF_NOT_FOUND` | business | false | `scan_diff` | `base_ref` ou `head_ref` é sintaticamente válido mas não existe no repositório atual. | `{ref_param, ref_value, hint}` |
| `INSUFFICIENT_GIT_HISTORY` | business | false | `scan_diff` | Shallow clone impede o Semgrep de resolver merge-base entre os refs para diff-aware scan. | `{hint: "increase actions/checkout fetch-depth"}` |
| `SCAN_TIMEOUT` | system | true | `scan_diff` | Scan excedeu `SEMGREP_RUNNER_TIMEOUT_SECONDS`. Subprocess Semgrep terminado com SIGKILL após grace period. | `{timeout_seconds, elapsed_seconds, partial_findings_discarded: true}` |
| `SEMGREP_BINARY_UNAVAILABLE` | system | false | `scan_diff` | Binário `semgrep` não encontrado no PATH no momento da invocação. | `{searched_paths}` |
| `SEMGREP_EXECUTION_FAILED` | system | true | `scan_diff` | Semgrep terminou com exit code de erro fatal (2) sem causa categorizada. | `{exit_code, stderr_excerpt}` |
| `INVALID_RULE_SET` | system | false | `scan_diff` | Regras curadas pelo projeto têm bug sintático (Semgrep exit 4 ou 5). | `{exit_code, stderr_excerpt}` |

A tabela acima é exaustiva para a v0.1.0 da spec. **A classe validation é vazia neste componente — ver §5.2 para declaração positiva.** Erros de protocolo MCP (Nível 1 — schema do `inputSchema` violado, tool inexistente, transport-level) não aparecem nesta tabela; são tratados pelo protocolo, não pelo componente.

### 5.5 Princípio de evolução do contrato

Adicionar `errorCode` ao contrato é mudança **minor** da spec (`spec_version` 0.1.0 → 0.2.0). Remover ou mudar semântica de `errorCode` existente é mudança **major** (incompatível com callers existentes). Versionamento da spec governado por ADR-0002 §6.

## 6. Provenance e versionamento

O componente carrega eixos de provenance distribuídos entre nível top-level do `structuredContent` (provenance estática — `rules_version` e `semgrep_version`, não mudam durante o lifetime do servidor para um dado rule set / binário) e `scan_metadata` aninhado (provenance dinâmica por-scan — `base_ref` e `head_ref` resolvidos, `files_scanned`, `elapsed_seconds`):

- `rules_version` — versão do rule set curado pelo projeto. Trilha de
  auditoria de regras de detecção. Muda quando regras são adicionadas,
  removidas, ou alteradas.
- `semgrep_version` — versão do binário Semgrep usado. Provenance da engine
  de execução. Muda quando o ambiente de execução é atualizado.
- `base_ref` / `head_ref` — commits resolvidos do PR sob análise (hashes
  completos, não branch names). Trilha de auditoria de qual estado do
  código foi escaneado.

A combinação dos três torna cada finding rastreável: este finding foi
gerado pela regra X (parte do rule set Y) executada por Semgrep Z sobre o
diff entre commits A e B.

Mecanismo de geração de `rules_version` é decisão de implementação. Hash
do diretório `rules/` (determinístico, automático), semver explícito em
metadata (legível, manual), ou combinação dos dois são alternativas
viáveis; decisão fechada durante implementação na semana 4-5.

## 7. Não-objetivos e fronteiras

**Streaming de findings durante scan.** Tool retorna em bloco. Streaming via
MCP não é suportado pela arquitetura: o agentic loop consome
`CallToolResult` atômico por iteração. Latência de scan é absorvida na
pipeline de CI, não distribuída pelo loop. Decisão arquitetural fechada na
#07.

**Findings parciais em caso de timeout.** `SCAN_TIMEOUT` retorna erro modal
sem findings. Findings parciais quebrariam a semântica de diff-aware do
`--baseline-commit` (HEAD escaneado mas baseline não terminado), tornando
findings potencialmente preexistentes em vez de novos. Honestidade
epistêmica > resultado parcial enganoso.

**Findings interfile (cross-file taint analysis).** MVP cobre apenas regras
single-file. Suporte a regras com `taint-mode` e traces cross-file é
deferimento registrado em ADR-0002.

**Subset configurável de regras por chamada.** Tool não aceita `rule_set`
como parâmetro. Set fixo curado pelo projeto. Para modos distintos de scan
(ex: fast vs full), princípio aplicado: split de tool, não parametrização
condicional de `scan_diff`.

**Rule set per-cliente.** MVP carrega rule set bundled no projeto com
recognizers brasileiros como caso-piloto. Per-cliente — diretório
`policy/<cliente>/semgrep_rules/` ou similar, análogo a como
`policy-reader` é per-cliente via troca de Política sob `policy/`
(ADR-0005 Decision 1) — fica para ADR futuro, quando o primeiro cliente
fora do escopo LGPD-brasileiro materializar. Motivo do adiamento:
generalização de regras de detecção sintática requer análise de domínio
(semântica de detecção, namespace de `rule_id` cross-cliente, provenance
de regras) distinta do problema jurisdicional do `policy-reader` que
motivou ADR-0005.

**Integração com Semgrep AppSec Platform.** Componente opera com Semgrep
open-source sem login. `SEMGREP_APP_TOKEN` não é lido. Findings não são
sincronizados para a plataforma cloud da Semgrep. Esta é decisão de escopo
do projeto — provenance de findings vive no GitHub PR e no rule set
versionado, não em sistema externo.

**Cancelamento gracioso do Semgrep.** Timeout dispara SIGTERM seguido de
SIGKILL após grace period. Não há mecanismo de cancelamento gracioso que
preserve estado parcial — Semgrep não foi projetado para cancelamento
intermediário em diff-aware scan.

**Análise estática como fronteira epistêmica.** Análise sintática nunca
consegue avaliar conformidade efetiva à LGPD — apenas identifica candidatos
para inspeção downstream pelo Classifier e Matcher. Esta é fronteira
fundamental da abordagem, não decisão deferida.

## 8. Critérios de aceitação

A implementação do `semgrep-runner` está completa quando todos os critérios
abaixo forem demonstravelmente verdadeiros. Cada critério é condição
observável, verificável por teste automatizado ou inspeção direta.

### 8.1 Tool `scan_diff` — caso normal

- [ ] Tool retorna sucesso com `isError: false` quando o diff entre `base_ref` e `head_ref` casa pelo menos uma regra do rule set curado. `structuredContent` carrega quatro chaves: `rules_version` e `semgrep_version` em top-level (provenance estática), `scan_metadata` (com `base_ref`, `head_ref`, `files_scanned`, `elapsed_seconds`), e `findings`.
- [ ] Cada item de `findings` carrega `rule_id`, `rule_severity` (∈ {`info`, `warning`, `error`}), `rule_message`, `location` (com `path`, `start_line`, `start_col`, `end_line`, `end_col`) e `snippet`.
- [ ] `location.path` é relativo ao repo root, não absoluto.
- [ ] `start_line`, `start_col`, `end_line`, `end_col` em `location` são inteiros 1-indexed.
- [ ] `scan_metadata.elapsed_seconds` reporta tempo de execução em segundos como número não-negativo.

### 8.2 Tool `scan_diff` — empty result

- [ ] Diff que não casa nenhuma regra retorna `{scan_metadata: {...}, findings: []}` com `isError: false`.
- [ ] `scan_metadata` continua presente quando `findings` é vazio (provenance preservada mesmo sem candidatos).
- [ ] `base_ref == head_ref` (diff vazio) retorna `findings: []` com `isError: false`, sem erro.

### 8.3 Contrato de erro

- [ ] Cada um dos seis `errorCode` da tabela §5 (`GIT_REF_NOT_FOUND`, `INSUFFICIENT_GIT_HISTORY`, `SCAN_TIMEOUT`, `SEMGREP_BINARY_UNAVAILABLE`, `SEMGREP_EXECUTION_FAILED`, `INVALID_RULE_SET`) é observável a partir do cenário descrito na coluna "Quando ocorre".
- [ ] Todo retorno de erro carrega `errorCode`, `message`, `isRetryable`, `details` em `structuredContent`.
- [ ] `errorCode` em MAIÚSCULAS_SNAKE em inglês; `message` em português humano-legível.
- [ ] `isRetryable` casa exatamente com a coluna correspondente da tabela §5 para cada `errorCode`.
- [ ] `details` segue a forma documentada na coluna `details` da tabela §5 para cada `errorCode`.
- [ ] Validation errors de domínio NÃO são emitidos pelo componente — input sintaticamente inválido é rejeitado pelo runtime FastMCP antes do código do componente.

### 8.4 Provenance

- [ ] Todo retorno de sucesso (incluindo empty result) carrega `rules_version` e `semgrep_version` em nível top-level de `structuredContent` (provenance estática); `scan_metadata: {base_ref, head_ref, files_scanned, elapsed_seconds}` aninhado (metadata dinâmica por scan).
- [ ] `base_ref` e `head_ref` em `scan_metadata` são commit hashes resolvidos (40 chars hex), não branch names ou tags.
- [ ] `rules_version` é estável entre execuções consecutivas quando o rule set não foi alterado — duas chamadas seguidas sem mudança em `mcp_servers/semgrep_runner/rules/` retornam o mesmo valor.
- [ ] `rules_version` muda quando o conteúdo de `mcp_servers/semgrep_runner/rules/` é alterado (regra adicionada, removida ou modificada).

### 8.5 Wire format (placement híbrido + Option B discriminator)

- [ ] Em sucesso: `structuredContent` carrega `{scan_metadata, findings}`; `content[0]` é um `TextContent` cuja chave `text` é prosa em português resumindo o resultado.
- [ ] Em erro de domínio (business ou system): `structuredContent` carrega `{errorCode, message, isRetryable, details}`; `content[0].text` reproduz `message`.
- [ ] Wire `isError: false` em TODOS os retornos do componente — sucesso, empty result, e erros de domínio. Wire `isError: true` fica reservado para falhas de protocolo emitidas pelo framework FastMCP (input rejeitado por `inputSchema`, tool inexistente, transport-level), não pelo componente.
- [ ] Discriminação semântica sucesso-vs-erro opera por presença de `errorCode` em `structuredContent`: sucesso nunca carrega `errorCode`; erro nunca carrega `findings` ou `scan_metadata`. Convenção alinhada a ADR-0002 §3 amendment 2026-05-17 (Option B).

### 8.6 Implementação

- [ ] Stack conforme ADR-0001 (FastMCP 3.x, Python 3.12.7).
- [ ] Tool retorna `SEMGREP_BINARY_UNAVAILABLE` quando o binário `semgrep` não está localizável no PATH no momento da invocação. Verificação ocorre por chamada; ausência não aborta o processo.
- [ ] `SCAN_TIMEOUT` é emitido após 300s quando `SEMGREP_RUNNER_TIMEOUT_SECONDS` está ausente do environment; após o valor configurado quando presente.
- [ ] Findings em arquivos não modificados pelo diff entre `base_ref` e `head_ref` não aparecem em `findings`, mesmo quando regras matcheariam neles ao escanear o repo inteiro.
- [ ] Quando `SCAN_TIMEOUT` é emitido, o subprocess Semgrep está garantidamente terminado — invocações subsequentes não competem com processos zumbis pelo binário.

### 8.<final> Review pass do architecture-overview

Review pass executado durante a redação desta spec. Quatro afirmações em
`architecture-overview.md` ficaram inconsistentes com decisões fechadas
neste documento; sync via commit dedicado nesta branch a seguir.

**§4.2 — input da tool.** Texto atual: "Recebe o diff do PR e a lista de
regras a aplicar". Esta spec §4.2 declara que `scan_diff` aceita apenas
`base_ref` e `head_ref`; o rule set é server-side e curado pelo projeto
(§7 desta spec rejeita explicitamente `rule_set` como parâmetro). Patch
proposto: substituir "lista de regras a aplicar" por menção aos refs.

**§4.2 — status da spec.** Texto atual: "Spec ainda não redigida — fica
para sessão posterior, depois do `policy-reader` estar implementado."
Obsoleto após esta spec. Patch proposto: substituir por referência a
`docs/specs/semgrep-runner/canonical.md`.

**§5.2 (Detector → Tools permitidas) — número e nome de tools.** Texto
atual: "MCP server `semgrep-runner` (tools de execução de regras Semgrep
e listagem de regras disponíveis)". Esta spec §3 declara que o componente
não expõe resources, e §4 expõe uma única tool (`scan_diff`) — sem tool
de listagem. Patch proposto: substituir por menção exclusiva a `scan_diff`.

**§5.2 (Detector → Input) — argumento "lista de regras".** Texto atual:
"Diff do PR, lista de regras Semgrep a aplicar (incluindo recognizers
brasileiros)". Inconsistente com a decisão de rule set server-side. Patch
proposto: substituir por refs do PR (`base_ref`, `head_ref`).

**§7.3 — sem patch necessário.** A tabela "MVP versus trabalho futuro"
cataloga evoluções produto-nível (severidade, fix-proposer, bloqueio de
merge, mapa cross-PR, AEP, dimensões adicionais da Política). Os
deferimentos internos deste componente listados em §7 desta spec (findings
interfile, subset configurável, integração AppSec Platform, cancelamento
gracioso) são escopo de ADR-0002, não evoluções produto-nível. Sem
contradição com §7.3.

Patches sincronizados em `architecture-overview.md` no commit `f7ec4b1` (PR #8).
