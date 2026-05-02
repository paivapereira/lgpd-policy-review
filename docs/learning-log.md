# Learning Log — TCC LGPD Code Review

Registro denso por sessão de estudo. Não é prosa: tópicos.
Cada entry serve dois propósitos: (a) fixação de conceitos da prova
Claude Certified Architect Foundations (junho 2026); (b) memória
operacional do projeto.

Formato por entry:
- Data e tema
- Conceitos da prova exercitados (tag de domínio)
- Decisões tomadas
- Artefatos criados (arquivos, commits, configs)
- Validações empíricas
- Próximo passo

---

## 2026-05-01 — bootstrap-claude-md-d3

### Conceitos da prova exercitados

**Domínio 3 — Claude Code Configuration & Workflows (20%)**

- CLAUDE.md hierarchy: quatro níveis cumulativos
  (enterprise > user > project > subdirectory) + CLAUDE.local.md gitignored
- Mecânica de loading: upward search a partir do CWD; project-root
  CLAUDE.md sobrevive a `/compact`; subdirectory CLAUDE.md é lazy
  (recarrega só quando agente lê arquivo daquele subdir)
- Override por especificidade em conflito; coexistência cumulativa
  no resto
- Anti-padrões mapeados: arquivos > 200 linhas reduzem adherence;
  procedimentos multi-step pertencem a skills, não CLAUDE.md;
  preferências pessoais pertencem a user-scope, não project
- Distinção entre CLAUDE.md (instrução para agente), README
  (descrição para humano), AGENTS.md (padrão cross-vendor
  emergente), e auto-memory (notas que o agente escreve para si)
- Importação via `@path/file.md` — DRY para humano, não economia
  de tokens

**Domínio 5 — Context Management & Reliability (15%)**

- Padrão de provenance: agente cita `arquivo:linha` em vez de
  parafrasear regra. Validado empiricamente nesta sessão.

### Decisões tomadas

- Repositório monorepo, nome `lgpd-policy-review`, privado durante
  desenvolvimento, licença MIT
- Stack canônica: Python 3.12.7 (pyenv-win), Claude Agent SDK,
  FastMCP, Presidio com recognizers BR, Ruff, mypy strict,
  pytest + pytest-asyncio, GitHub Actions
- Idiomas: código/CLAUDE.md/commits em inglês; Política em PT;
  outputs do sistema em PT
- Três regras imutáveis traduzindo a tese:
  - Escalonamento humano em conflito Lei × Política
  - Citação de clause IDs estáveis em todo finding
  - Compatibilidade `policy_schema_version` declarada
- Convenções: Conventional Commits; main protegida; feature
  branches `feat/`, `fix/`, `docs/`
- Python 3.14 desinstalado para evitar competição no PATH

### Artefatos criados

- Repositório `paivapereira/lgpd-policy-review` no GitHub
- README.md inicial (commit 68e69c5 via servidor GitHub)
- CLAUDE.md raiz com 74 linhas, hash 522229b
- docs/learning-log.md (este arquivo)
- Pasta de trabalho `C:\Users\joaoguilherm.pereira\dev\`

### Validações empíricas

Após push do CLAUDE.md, dois testes na extensão Claude Code do VS Code:

**Teste 1 — recall das regras imutáveis.** Pergunta: "Quais são as
regras imutáveis deste projeto?". Agente localizou CLAUDE.md via
Glob, leu o arquivo, citou linhas específicas (`CLAUDE.md:36-44`,
`CLAUDE.md:40`, `CLAUDE.md:42`, `CLAUDE.md:44`), traduziu para PT
respeitando regra de idioma de output, manteve identificadores
técnicos em inglês (`requires_human=true`, `policy_schema_version`,
`LGPD-Art-7-I`). Aderência total.

**Teste 2 — adherence sob pressão.** Pedido: "Vamos adicionar
Flask". Agente reconheceu que CLAUDE.md:27 lista Flask como
alternativa que requer ADR explícito; suspendeu execução; pediu
ADR; questionou caso de uso confrontando com arquitetura
descrita no README; sugeriu FastAPI como alternativa coerente com
async stack já declarado. Pushback comportou-se exatamente como
prescrito. Auto-memory atualizada para reforçar padrão.

### Próximo passo

ADR-0001 documentando o bootstrap (decisões de setup, escolha
da stack canônica, três regras imutáveis com racional). Estrutura
`docs/adr/` ainda não existe — criar junto.

### Pendências (não bloqueantes)

- Captação de orientador na UTFPR (prazo crítico, 2 semanas)
- `.python-version` na raiz fixando 3.12.7
- Branch protection em main no GitHub
- `~/.claude/CLAUDE.md` user-scope com preferências cross-projeto---

## 2026-05-02 — adr-0001-d5-provenance

### Conceitos da prova exercitados

**Domínio 5 — Context Management & Reliability (15%)**

- **Provenance verification em ação.** Padrão de trabalho aplicado
  meta-conversacionalmente: rascunho do ADR-0001 marcado com
  `[verificar]` em pontos onde Chat inferiu justificativa em vez
  de recuperar do registro real. Após validação via
  `conversation_search` sobre Sessão #01 e #02, três justificativas
  reescritas antes do commit (MIT, FastMCP, decisão 6).
- **Anti-padrão por contraste.** Output confiante fabricado para
  preencher gap em vez de explicitar incerteza é o anti-padrão
  central que o ADR-0001 evitou. Mesmo padrão vai aparecer no
  design do code review system: findings sem clause ID rejeitados
  por validação, confidence scoring vs sentiment como proxy
  inválido.
- **Context budget e densidade de relevância.** Discussão sobre
  lost-in-the-middle, densidade > tamanho absoluto, custo de
  redundância no project knowledge. Recomendação adotada:
  `proposta-tcc.md` tem redundância com o exam guide PDF na
  seção "Mapeamento aos 5 domínios" e merece enxugamento futuro.
  Ideia de `docs/CONTEXT.md` como manifest curto adiada para
  quando project knowledge ficar pesado.

### Conceitos fora do escopo da prova

- **ADRs e formato Nygard.** Origem (Michael Nygard, 2011), cinco
  seções clássicas (Title, Status, Context, Decision, Consequences),
  versão expandida para decisão composta (sub-decisões inline com
  decisão + rationale + consequência cada). Comparação com MADR
  (Markdown ADR): MADR brilha quando há trade-off comparativo real
  entre opções consideradas; Nygard expandido brilha para registros
  agregados como bootstrap.
- **`conversation_search` como ferramenta de meta-chat.** Permite
  recuperar contexto de sessões anteriores dentro do mesmo project.
  Ferramenta de UI da Claude Chat, não cobre nenhum task statement
  da prova.

### Decisões tomadas

- **Formato de ADR adotado: Nygard expandido.** Decisão composta
  estruturada como subseções por sub-decisão, cada uma com decisão
  + rationale + consequência inline. MADR fica reservado para
  futuras ADRs com trade-off comparativo real.
- **ADR-0001 do bootstrap finalizado.** Seis sub-decisões:
  monorepo + MIT, stack canônica, idiomas, três regras imutáveis,
  workflow git, direct-commit allowlist permanente.
- **Direct-commit allowlist permanente.** Apenas
  `docs/session-handoff.md` e `docs/learning-log.md` vão direto em
  `main`. Não é exceção de bootstrap; é convenção permanente
  baseada em ausência de signal de revisão. Adicionar terceiro
  arquivo à allowlist requer ADR específico.
- **Política `policy/` terá licença separada.** MIT cobre código;
  conteúdo jurídico-textual ficará sob CC-BY (provável), decidido
  em ADR específico antes de v1.0 ou abertura pública do repo.
- **ADRs aprovados sobem ao project knowledge.** Curadoria via
  `docs/adr/INDEX.md` quando passar de ~15 ADRs.

### Artefatos criados

- `docs/adr/` estrutura criada.
- `docs/adr/0001-bootstrap.md` (267 linhas), mergeado via PR padrão
  (squash + delete-branch). PR #3.
- ADR-0001 subido ao project knowledge para contexto autoritativo
  futuro.
- Rascunho v1 do ADR (com três `[verificar]`) → v2 final
  (justificativas reescritas em três pontos). Trail da revisão
  registrado na própria seção 6 do ADR ("Why this is not a
  bootstrap exception").

### Validações empíricas

- **`conversation_search` recuperou Sessão #02 sobre MIT vs Apache.**
  Resultado: decisão consciente com três fatores ponderados (sem
  intent comercial, sem patentes, MIT em whitelist Adobe), não
  default. Inferência genérica do rascunho substituída pelo
  raciocínio real.
- **`conversation_search` recuperou Sessão #01 sobre origem do
  stack.** Resultado: FastMCP entrou como parte do pacote canônico
  recomendado para projetos multi-agent em Python (junto com
  `claude-agent-sdk`, `pydantic`, `inspect-ai`), não como vencedor
  de comparação isolada contra raw SDK. Inferência comparativa do
  rascunho substituída por adoção em pacote.
- **Leitura cruzada do session-handoff exibiu contradição na
  decisão 6 do rascunho.** "Primeiro PR mergeado via squash" no
  handoff implica que CLAUDE.md inicial foi via PR, não direct
  commit; o rascunho descrevia uma "exceção do bootstrap" que não
  existia. Decisão reescrita como convenção permanente.
- **Segundo passe do fluxo PR validado.** ADR-0001 mergeado via
  branch `docs/adr-0001-bootstrap` → PR → squash → delete. Mesma
  mecânica da sessão 1; consistência da decisão 5 confirmada.

### Próximo passo

Decidir entre duas frentes para a sessão 3:

- **(a) Primeiro MCP server `lgpd-policy-reader` em FastMCP.**
  Cobre Domínio 2 (Tool Design & MCP Integration, peso 18%)
  inteiro numa só implementação: tool descriptions diferenciadas,
  structured error responses, tool_choice forçado, `.mcp.json`
  project-scope com `${VARS}` expandidos, MCP resources como
  catálogo navegável.
- **(b) Estrutura inicial de `policy/` com schema YAML mínimo.**
  Cobre mais Domínio 5 (provenance, schema versioning,
  policy_schema_version compatibility) e tem componente jurídico
  fora do escopo da prova.

Recomendação atual: **(a)**, por densidade de conceitos da prova
por hora investida. Decisão fica para abertura da sessão 3.

### Pendências (não bloqueantes)

- Captação de orientador na UTFPR (prazo crítico,
  ~13 dias remanescentes)
- `.python-version` na raiz fixando 3.12.7
- Branch protection em main no GitHub
- `~/.claude/CLAUDE.md` user-scope com preferências cross-projeto
- Considerar enxugamento futuro da seção "Mapeamento aos 5 domínios"
  da `proposta-tcc.md` para reduzir redundância com o exam guide
