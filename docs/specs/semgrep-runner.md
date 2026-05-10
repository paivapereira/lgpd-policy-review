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

**Stack e governança.** Implementação em FastMCP 2.x conforme ADR-0001.
Invocação do binário Semgrep via subprocess. Decisões de design deste
componente são governadas pelo ADR-0002 (em redação na sessão #08).

## 2. Contrato com o artefato servido

### 2.1 Artefato e versionamento

Este componente serve **detecção sintática de candidatos a tratamento de
dados pessoais**, materializada por um conjunto curado de regras Semgrep
versionadas em Git sob `mcp_servers/semgrep_runner/rules/`. As regras são
artefato declarativo do projeto, com ciclo de vida desacoplado da evolução
deste componente — adicionar uma regra de detecção de novo identificador
brasileiro não exige mudança no código do server.

O conjunto de regras carrega versão própria reportada via `rules_version` em
todo finding emitido. Mecanismo de geração da versão (hash do conteúdo do
diretório, semver explícito declarado em metadata, ou híbrido) é decisão de
implementação livre — ver §6.

**MVP — escopo de regras.** O MVP cobre regras Semgrep single-file: cada
regra matcha em uma única região contígua de um único arquivo. Suporte a
findings interfile (regras com taint analysis cross-file via metavariáveis
e traces) é deferimento explícito registrado em ADR-0002.

### 2.2 Motor de execução

O componente delega análise estática ao binário `semgrep` instalado no PATH
do ambiente de execução. Funcionalidade nativa de diff-aware scan via
`--baseline-commit` é o mecanismo central usado pela tool exposta — o
componente não reimplementa diferenciação de findings, delega ao Semgrep.

Versão mínima aceita do binário: `semgrep` 1.x. Versão exata validada
durante implementação (semana 4-5); pin ou floor formal fica para a fase
de implementação.

Token Semgrep AppSec Platform (`SEMGREP_APP_TOKEN`) **não é requerido**.
Componente opera com Semgrep open-source sem login — ver §7.

## 3. Resources expostos

Este componente **não expõe resources MCP**.

A decisão é deliberada e simétrica ao tratamento de regras Semgrep como
insumo interno do server, não como conteúdo navegável pelo caller. O
Detector consome findings produzidos pela tool em §4; não enumera, lê, ou
raciocina sobre o conteúdo das regras antes de invocar o scan. Resource
catalogável só existe quando há leitura cognitiva do conteúdo pelo agente
consumidor (ver `docs/spec-authoring-principles.md` quando consolidado;
princípio aplicado: TS 2.2 do exam guide — "resources for catalogs, tools
for actions" — pela negativa).

## 4. Tools expostas

### 4.1 Naming convention

Tool exposta por este server segue convenção `mcp__semgrep_runner__<tool>`
gerada pelo runtime MCP. O handle completo é o usado em `allowed-tools` no
frontmatter do AgentDefinition do Detector e em matchers de hooks. Dentro
do código do server, o nome local da tool é `scan_diff`.

### 4.2 `scan_diff`

**Description (inglês, sem markdown).**

> Scans the pull request diff for new findings introduced by HEAD relative
> to BASE, using the project's curated detection rule set for personal data
> handling candidates. Returns findings with location, code snippet, and
> rule provenance. Use this tool when the agent has the BASE and HEAD git
> refs of a pull request and needs to identify candidate sites for further
> classification. Operation is synchronous and may take seconds to minutes
> depending on diff size.

Tempo máximo de execução configurável via variável de ambiente
`SEMGREP_RUNNER_TIMEOUT_SECONDS`; default 300s. Excedido o limite,
retorna `SCAN_TIMEOUT` (ver §5).

**Input.**

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `base_ref` | string | sim | Git ref (commit hash, branch name, or tag) representing the baseline against which new findings are computed. |
| `head_ref` | string | sim | Git ref representing the current PR state to scan. |

**Output em sucesso.**

```yaml
{
  scan_metadata: {
    rules_version: <hash ou semver do rule set>,
    semgrep_version: <versão do binário usado>,
    base_ref: <commit hash resolvido de base_ref>,
    head_ref: <commit hash resolvido de head_ref>,
    elapsed_seconds: <tempo de execução>
  },
  findings: [
    {
      rule_id: <string, ex: "br-cpf-leak">,
      rule_severity: <enum: info | warning | error>,
      rule_message: <texto curto da regra>,
      location: {
        path: <relativo ao repo root>,
        start_line: <int, 1-indexed>,
        start_col: <int, 1-indexed>,
        end_line: <int, 1-indexed>,
        end_col: <int, 1-indexed>
      },
      snippet: <string com o código matched>
    }
  ]
}
```

**Empty result.** `findings: []` com sucesso é estado normal — significa que
o diff não introduziu candidatos detectáveis pelas regras curadas. Não
indica falha de scan. `scan_metadata` está sempre presente, mesmo quando
`findings` é vazio, para manter provenance auditável.

**Convenção de wire format.** Sucesso retorna `isError: false` no
`CallToolResult` protocolar. O payload acima vive em `structuredContent`;
prosa humana resumindo o resultado vive em `content[0].text` em português —
placement híbrido conforme convenção do projeto fechada na #06.

**Condições de erro específicas.** Ver §5.

**Exemplos.** Ver §4.3.

### 4.3 Exemplos

*Caso normal — scan retorna candidatos em dois arquivos diferentes.*

```
Input: { "base_ref": "main", "head_ref": "feat/onboarding-cpf" }

Output: {
  "isError": false,
  "structuredContent": {
    "scan_metadata": {
      "rules_version": "sha256:b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0",
      "semgrep_version": "1.92.0",
      "base_ref": "a3f5b1c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2",
      "head_ref": "9d8e7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d",
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
    "scan_metadata": {
      "rules_version": "sha256:b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0",
      "semgrep_version": "1.92.0",
      "base_ref": "a3f5b1c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2",
      "head_ref": "1c2b3a4f5e6d7c8b9a0f1e2d3c4b5a6f7e8d9c0b",
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

*Erro modal — scan excedeu `SEMGREP_RUNNER_TIMEOUT_SECONDS` (default 300s). `isError: true` no nível protocolar; payload categorizado em `structuredContent`; prosa em `content[0].text`.*

```
Input: { "base_ref": "main", "head_ref": "feat/large-refactor" }

Output: {
  "isError": true,
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

## 5. Contrato de erro

`isError` é o sinal protocolar do MCP — boolean nativo do `CallToolResult`,
lido pelo runtime do client (Claude Code, Agent SDK) para classificar o
resultado da tool call. Cada `errorCode` listado abaixo materializa um
cenário de falha de domínio do `semgrep-runner` e vive **dentro** do
payload do `CallToolResult`, não no nível protocolar. Em erros, `isError:
true` no nível protocolar; payload categorizado (`errorCode`, `message`,
`isRetryable`, `details`) em `structuredContent`; prosa equivalente em
português em `content[0].text` — placement híbrido conforme convenção do
projeto. `isError: false` nunca carrega `errorCode`; sucesso retorna o
payload definido em §4.

Validation errors de domínio são **vazios** neste componente. Os dois
inputs (`base_ref`, `head_ref`) são strings não-vazias declaradas em
`inputSchema`; o runtime FastMCP rejeita inputs sintaticamente inválidos
antes de chegar ao código do componente. Ausência de validation errors é
declaração positiva, não omissão.

| `errorCode` | Classe | `isRetryable` | Quando ocorre | `details` |
|---|---|---|---|---|
| `GIT_REF_NOT_FOUND` | business | false | `base_ref` ou `head_ref` é sintaticamente válido mas não existe no repositório atual. | `{ref_param, ref_value, hint}` |
| `INSUFFICIENT_GIT_HISTORY` | business | false | Shallow clone impede o Semgrep de resolver merge-base entre os refs para diff-aware scan. | `{hint: "increase actions/checkout fetch-depth"}` |
| `SCAN_TIMEOUT` | system | true | Scan excedeu `SEMGREP_RUNNER_TIMEOUT_SECONDS`. Subprocess Semgrep terminado com SIGKILL após grace period. | `{timeout_seconds, elapsed_seconds, partial_findings_discarded: true}` |
| `SEMGREP_BINARY_UNAVAILABLE` | system | false | Binário `semgrep` não encontrado no PATH no momento da invocação. | `{searched_paths}` |
| `SEMGREP_EXECUTION_FAILED` | system | true | Semgrep terminou com exit code de erro fatal (2) sem causa categorizada. | `{exit_code, stderr_excerpt}` |
| `INVALID_RULE_SET` | system | false | Regras curadas pelo projeto têm bug sintático (Semgrep exit 4 ou 5). | `{exit_code, stderr_excerpt}` |

### 5.1 Casos que parecem erro mas não são

**Empty findings.** Scan rodou com sucesso, atravessou o diff, nenhuma
regra matcheou. **Estado normal**, retornado como `{scan_metadata: {...},
findings: []}` com `isError: false`.

**Diff vazio.** `base_ref == head_ref` ou commits idênticos. Semgrep roda,
não tem nada para escanear, retorna sucesso com lista vazia. Mesmo
tratamento.

**Findings em arquivos preexistentes.** Filtrados nativamente pelo
`--baseline-commit` do Semgrep antes de chegar ao caller. Não emergem como
findings visíveis.

## 6. Provenance e versionamento

O componente carrega três eixos de versão independentes, todos refletidos
em `scan_metadata` de cada finding emitido:

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
do diretório `rules/` (determinístico, automático) e semver explícito em
metadata (legível, manual) são duas alternativas viáveis; decisão fechada
durante implementação na semana 4-5.

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
como parâmetro. Set fixo curado pelo projeto. Caso emerja necessidade de
modos distintos de scan (ex: fast vs full), resposta canônica é split de
tool com descriptions autônomas, não parametrização.

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

<!-- redigir critérios como condições observáveis (princípio 25), não
     atividades. Cada critério precisa ser verificável por teste ou
     inspeção. Cobrir:
     - tool retorna findings com schema correto em caso normal
     - tool retorna empty findings em diff sem matches
     - tool retorna SCAN_TIMEOUT em scan que excede limite
     - tool retorna GIT_REF_NOT_FOUND para ref inexistente
     - tool retorna INSUFFICIENT_GIT_HISTORY em shallow clone
     - rules_version reportado em todo finding
     - paths em findings são relativos ao repo root
-->

### 8.<final> Review pass do architecture-overview

<!-- princípio 26: última sub-seção de toda spec. Antes de mergear, varrer
     architecture-overview.md procurando decisões obsoletas ou contradições
     com esta spec. Pontos a verificar:
     - §4.2 (descrição do semgrep-runner) ainda condizente?
     - §5.2 (Detector como consumidor) menciona scan_diff corretamente?
     - §7.3 (MVP versus trabalho futuro) precisa absorver "findings
       interfile" e "subset configurável" como deferimentos?
-->
