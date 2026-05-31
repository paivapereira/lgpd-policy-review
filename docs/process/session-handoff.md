# Session Handoff — para sessão #50 (coordinator-flesh-completo)

> Reescrito ao fim da sessão #49. Substitui o handoff anterior por completo.
> Direct commit em main (ADR-0001 D6).

## Estado do repo (main, pós-merge)

Três PRs mergeados na #49, main limpo:
- **PR #82** `chore/cross-spec-housekeeping` — C4,C5,C6,C7,C8,C9,C11,C14 +
  citação tools.py:263-279.
- **MC-E** `chore/add-claude-agent-sdk` — `claude-agent-sdk==0.2.87` pinado;
  ADR-0001 D2 emendado in-place (2ª vez).
- **`docs/branch-b-output-contract`** — C1, C2, C3, P4.

As 6 specs de subagente (`docs/specs/subagents/{triager,detector,classifier,
matcher,reporter,coordinator}.md`) estão reconciliadas entre si quanto ao
contrato de structured output do Branch B. `reporter.md` em 0.5.0.

## Objetivo da sessão #50

**Coordinator-flesh-completo (MC-A)** — materializar
`docs/specs/subagents/coordinator.md` de skeleton para spec completa. É a 6ª
e última spec de subagente; destrava T11+ (implementação).

## Pré-condições (todas satisfeitas — confirmar, não assumir)

- **C1 ✅** — `MatcherOutput` definido (matcher §3.1bis); o
  `coordinator §3.4` que o referencia agora resolve.
- **C2 ✅** — `scan_provenance` no ReportPayload (reporter 0.5.0); o
  coordinator sabe que roteia `DetectorOutput.provenance` ao Reporter
  (§3.2/§3.5 já têm a nota de roteamento).
- **C3 ✅** — `output_format` + `max_turns` declarados nos quatro stages
  Branch B do coordinator (§3.1 Triager, §3.2 Detector, §3.3 Classifier,
  §3.4 Matcher).

## Landam DENTRO do flesh (não são pré-req; são parte do trabalho)

- **C3 materialização** — os campos estão declarados no skeleton; o flesh
  os integra ao loop real.
- **C12** — `config.py` single-source dos `*_CONFIG` (POLICY_READER_CONFIG,
  SEMGREP_RUNNER_CONFIG, reporter_sdk_server): hoje o elo
  `mcp_servers_dict` ↔ constantes é indefinido. O flesh estabelece o dono
  único. Locus provável `src/coordinator/config.py`.
- **Capture loop rico** — discriminação `subtype` × `stop_reason` (incl.
  `refusal` dentro de `subtype=success`), `model_validate` por stage, raise
  tipado, verificação posicional de ordem/identidade. A classe
  `SubagentContractViolation`/`SubagentValidationFailed` mora junto das
  exceções tipadas do coordinator (locus provável `src/coordinator/errors.py`).

## Verificação ANTES de escrever (disciplina da #47/#49)

As specs **não têm numeração de seção paralela** — o detector tem um §6.2
extra que desloca as demais. Âncora por CONTEÚDO, não por §/linha. Ler
verbatim cada locus do coordinator que o flesh toca antes de afirmar/editar.
Confirmar especialmente: que os 4 stages têm `output_format`+`max_turns`
(C3 aplicado), que o roteamento de `scan_provenance` está em §3.2/§3.5, e
que `MatcherOutput`/`DetectorOutput`/`ClassifierOutput` são os nomes
referenciados.

## Decisões abertas que o flesh PODE precisar fechar

- **DetectorScanFailed vs run_outcome="error"** — taxonomia de erro
  non-retryable de `scan_diff` (detector §10.5 item 3; decisão do
  coordinator, pendente).
- **DD-T05 / `changed_paths`** (C13) — Glob-by-subagent vs pré-computado;
  recomendação corrente é manter Glob (zero emenda ao Triager). Baixa
  prioridade; pode ficar deferida.

## Débitos NÃO deste flesh (housekeeping separado, próximo balde)

1. **6b** — matcher §6.3/§10.5(4) resíduo "TS-only pendente"; detector §6.3
   já corrigido (#82). Fechar cross-ref.
2. coordinator §3.4 comentário inline (cosmético).
3. grep `TS-only\|TypeScript-only` em docs/specs/ antes do PR.
4. C10 (numeração "Etapa") — baixa prioridade.

E, fora do flesh: **`policy://examples`** (DD-C10) — resource ainda não
existe; é pré-req do *merge da impl do Classifier*, não do flesh. PR
autônomo quando chegar a impl.

## Convenções operacionais (carregar sempre)

- Chat planeja/decide/revisa; Code materializa.
- Conventional Commits, squash-merge, sem `Co-Authored-By`.
- Commit fica com o João (ou autorização explícita ao Code).
- PowerShell: NÃO `-m` inline com `§`/`→` (mojibake) — usar `-F` UTF-8 ou
  GitLens. Edits de spec via applier Python guardado (exactly-once, UTF-8
  no-BOM, LF) ou Edit tool.
- **Review = plan mode** (trava de permissão, não pedido).
- ADR-0001 D6: learning-log + session-handoff são direct commit em main.