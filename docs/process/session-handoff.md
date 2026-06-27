# Session handoff — Roteiro de fala da defesa (TCC2 João Pereira)

**Para:** próxima sessão Chat (nova conversa, sem o histórico de imagens).
**Objetivo da próxima sessão:** escrever o **roteiro de fala** (narração) da defesa, slide a slide.
**Estado dos slides:** FECHADOS (19 slides, montados no PowerPoint, template UTFPR). Não reabrir
o conteúdo dos slides salvo erro factual. O trabalho agora é a FALA por cima deles.

---

## Como trabalhar (disciplina desta dupla)

- **Verificar antes de inferir.** Fonte autoritativa = `relatorio-tcc2_Joao_revisado.pdf` (anexá-lo
  na nova conversa). NÃO afirmar número, nome de arquivo, linha ou veredito de memória — ler do PDF
  ou do repo. Handoff é hipótese a verificar, não verdade.
- **Estilo:** PT-BR direto, prosa sem floreio, sem reafirmação para agradar. Pode discordar com razão
  (João pediu pushback explícito). "Martelo" = decisão final dele.
- **Honestidade epistêmica acima de retórica:** o roteiro nunca deve fazer o sistema parecer mais do
  que é. A força da defesa é admitir limites com precisão.
- **Repo público:** `paivapereira/lgpd-policy-review`. Demo ancorada no run #3 (commit `fe51f12`),
  GitHub Actions run 26983111920 (`workflow_dispatch`, ~4m35s, 3 jobs verdes).

---

## O TRABALHO em uma frase

Sistema multiagente de *code review* que verifica conformidade do tratamento de dados pessoais num
*pull request* contra uma **Política de proteção de dados versionada** (artefato declarativo YAML),
independente do mecanismo que a interpreta e da jurisdição que codifica (LGPD como instância; gêmea
GDPR prova a independência). Arquitetura em três camadas: (1) Política versionada; (2) coordenador +
cinco subagentes sobre dois servidores MCP; (3) integração GitHub Actions. Metodologia: Spec-Driven
Development com verificação em dois escopos. Diferencial técnico: seis reconhecedores brasileiros
(CPF, CNPJ, CNH, NIS/PIS, título de eleitor, CNS-saúde).

João é **advogado + engenheiro** — o duplo repertório é a alma do trabalho e deve transparecer na fala
(não como currículo, mas nos momentos onde a leitura jurídica decide o design).

---

## ESTRUTURA DOS 19 SLIDES (ordem final)

1. Capa
2. Sumário (espelha o relatório)
3. Introdução — O Problema
4. Objetivo Geral — A Proposta
5. Justificativa — A Solução: arquitetura em camadas desacopláveis (Camadas 1/2/3)
6. Demonstração — O Software em execução (setup dos 3 casos)
7. Print job COMP-001 (GitHub job summary)
8. Print job VIOL-001
9. Print job SKIP-001
10. Desenvolvimento, Metodologia e Avaliação — SDD + ciclo + V&V constitutiva
11. Desenvolvimento... — verificação escopada (Tarefa/Marco/Substrato) + QA consolida
12. Marco A: policy-reader
13. Marco B: semgrep-runner
14. Marco C: pipeline multiagente
15. Camada 3: integração CI/CD
16. Núcleo reprodutível e fronteira de escalação
17. Relatório de Garantia de Qualidade
18. Considerações finais
19. Capa final

**Tempo:** ~20 min, 17 slides de conteúdo = APERTADO. Regra de ouro: **não ler bullets**, falar por
cima. Se estourar no ensaio, backup nesta ordem: slide 17 (QA, narrar ~40s), depois slide 11. NÃO
comprimir demo (6–9) nem fronteira (16). Slides mais densos: 6, 10–11, 15, 16, 17.

---

## FALAS OBRIGATÓRIAS (conteúdo que SAIU do slide e VIVE na narração)

Estes pontos foram deliberadamente tirados dos slides 15 e 16 para aliviar densidade. Se não forem
ditos, o slide afirma algo sem sustentá-lo. São de cumprimento obrigatório:

### Slide 15 (Camada 3) — o slide foi enxugado; a fala precisa cobrir:
- **`workflow_dispatch`**: o "CI" do slide é disparo MANUAL, não trigger de PR de produção. Dizer
  "disparado manualmente via *workflow_dispatch*". NUNCA implicar que o `pull_request` de produção
  funciona — ele é trabalho futuro (fora do TCC; não mencionar "Milestone D" na defesa).
- **Campos estáveis do field-scoped** (o slide diz só "os campos que devem ser estáveis"): enumerar na
  fala — desfecho (`run_outcome`), contagens por veredito, multiconjunto (veredito × `rule_id`), e a
  trinca de proveniência.
- **Por que K=2 é piso** (CRÍTICO — blindagem): "uma rodada é só observação; convergência exige K≥2.
  K=2 não prova estabilidade, é o piso para poder falar em convergência." Sem isto, a banca pergunta
  "por que só duas rodadas?" e o bullet fica no ar.
- Detalhe opcional de fala: *runner* Ubuntu.

### Slide 16 (Núcleo/fronteira) — mantido no tamanho anterior; reforçar na fala:
- **Flip de jurisdição**: o MESMO código, sob o vocabulário GDPR, inverte o veredito — porque o token
  de base legal muda (LGPD usa `consent`; a gêmea GDPR usa `consent_gdpr`, que o motor `== "consent"`
  rejeita). Prova a independência de jurisdição da Política.
- **Mecanismo da POL-007** (momento advogado-engenheiro — DIZER, não ler): o motor compara `consent`
  por igualdade literal e NÃO consulta a *flag* `special_category` da categoria. Então dado de saúde
  com `consent` comum passa como `compliant` — juridicamente INSUFICIENTE: Art. 11 da LGPD exige
  consentimento DESTACADO. E `explicit_consent` (o correto) é reprovado. A inversão é completa e
  sistemática. Enquadrar como achado honesto: diagnosticado, causa-raiz, correção projetada, deixado
  como trabalho futuro por risco de regressão sob prazo — NÃO como desculpa.
- **13/13 é o motor determinístico** (sem modelo, reprodutível por construção) — distinto da
  convergência K=2 do pipeline (com modelo). Não deixar "13/13" soar como "tudo converge": a fronteira
  é qualitativa e NÃO converge sempre (o experimento pipeline_e2e teve PROBE-UNGOV 4-contra-1).

### Outras falas obrigatórias (demais slides):

- **Slide 6–9 (demo):** VIOL-001 e COMP-001 são arquivos/frameworks DISTINTOS (VIOL = Django
  `models.py:28`; COMP = Pydantic `users.py:26`). Frase segura: "mesma operação, mesma cláusula
  POL-005 (LGPD Art. 7º I); o veredito depende só da base legal declarada." `legal_basis` é declarado
  textualmente no diff. Se perguntarem "e se mentir?": é **verificação declarativa, não efetiva** —
  avalia o que o diff DECLARA, não o comportamento em produção (isto está no slide 6, reforçar).
  - O `data_categories` no rodapé dos prints COMP/VIOL mostra um *advisory mismatch* — é
    **field-scoped por design** (advisory, não reprova). Se a banca apontar, é resposta pronta, não
    defeito. (Em COMP-001, `username` adiciona `dados_de_autenticacao`, explicando a divergência.)
  - SKIP-001: `run_outcome: skipped_by_triager`, PR só-docs, sem veredito. Os "3 warnings Node.js 20
    deprecated" nos prints são ruído de infra do GitHub, IRRELEVANTES — ignorar se aparecer.
  - O job `production (pull_request)` aparece como DEFERRED/skipped nos prints — se perguntarem,
    confirmar que é trabalho futuro, fora do escopo do MVP.

- **Slide 10 (método):** frase-âncora para DECORAR (vai na fala, é o coração do método):
  "A verificação e validação são parte constitutiva do ciclo — a fase de Validação do SDD, não uma
  etapa posterior; sem ela, o ciclo estaria incompleto. A avaliação assim produzida é adequada às
  afirmações qualitativas do MVP e explícita quanto aos seus limites."
  NÃO dizer "suficiente" cru (completude de método ≠ suficiência de evidência; abriria flanco no K=2).

- **Slide 11 (verificação escopada):** o achado metodológico recorrente — cobertura unitária verde
  NUNCA é suficiente; o exercício de wire real / pipeline live / CI é cobertura independente e
  complementar. Re-rodar portões após qualquer fix downstream é obrigatório.

- **Slide 12 (Marco A):** "ajustes invisíveis à suíte de unidade" = 4 defeitos que 53 testes verdes
  não pegaram. UM é o achado de advogado: a convenção jurídica de citação ("Art. 7º" vs "Art. 12" —
  cardinal a partir de 10, sem o "º" ordinal). É o primeiro momento advogado-engenheiro; vale citar
  como par do POL-007.

- **Slide 13 (Marco B):** o defeito Windows-stdio substantivo, invisível a 132 testes que usavam
  transporte EM MEMÓRIA; o gate usou stdio real (subprocess). Anti-pattern de confiabilidade:
  colapsar erro transiente em erro de negócio.

- **Slide 17 (QA):** veredito "aprovado com ressalvas declaradas". As ressalvas NÃO são silenciosas.
  Se citar a revisão cross-doc: ela PEGOU divergências no relatório parcial e no CLAUDE.md e elas
  foram corrigidas na v2 — enquadrar como "a revisão funcionou", não como erro atual.

- **Slide 18 (considerações finais):** terminar a fala no último bullet — "regras jurídicas como
  artefatos auditáveis... aproximando Direito e Engenharia de Software" — com PAUSA. É o fecho. NÃO
  abordar trabalhos futuros (decisão do João: encerrar na conclusão).

---

## COERÊNCIA TEMÁTICA (o fio condutor — nomear ao longo da fala)

O mesmo princípio — não afirmar o que não se sustenta — atravessa quatro escalas:
- **Produto:** o sistema emite `indeterminate` no que não pode decidir (demo).
- **Método:** avaliação "adequada e explícita quanto aos limites" (slide 10).
- **Fronteira:** "convergência não garantida, e isso é resultado, não falha" (slide 16).
- **QA:** "aprovado com ressalvas declaradas" (slide 17).
→ Fecho: "aproximando Direito e Engenharia de Software" (slide 18).
Esse fio é a tese do trabalho espelhada em quatro níveis. Vale explicitá-lo pelo menos uma vez.

---

## TERMINOLOGIA OFICIAL (usar exatamente)

- "núcleo reprodutível" e "fronteira de escalação" (termos do relatório; NÃO "casos complexos").
- "Marco A/B/C" (não "Milestone"); "Camada 3" (amarra na Fig. 1 do relatório).
- "O Software" como rótulo do artefato em execução (slides de demo).
- Estrangeirismos em itálico (*pipeline*, *gate*, *baseline*, *workflow_dispatch*, *runner*,
  *field-scoped*, *advisory*).
- "afirmações" (não "claims"); "Política" maiúscula (o artefato); "Report" (a saída consolidada).

---

## PENDÊNCIAS / A CONFIRMAR

- **Referências:** não há slide de Referências (fecha em Considerações finais → capa final). João deve
  confirmar com a orientadora (Profa. Dra. Alinne C. Corrêa Souza) se a banca exige o slide mesmo sem
  citações visíveis nos slides. Se exigir, entra entre 18 e 19, só com o efetivamente citado (LGPD,
  MCP/Anthropic) — não inventar lista.
- **Ensaio cronometrado** ainda não feito — é o juiz final do tempo.
- Correções de texto já aplicadas pelo João: slide 6 (tipo "vi—nculado" + remoção do bullet
  declarativo), slide 10 ("claims"→"afirmações"), slide 15 (enxugado).

---

## O QUE A PRÓXIMA SESSÃO DEVE PRODUZIR

Roteiro de fala slide a slide: para cada slide, (a) a mensagem central em 1–2 frases, (b) os pontos de
fala obrigatórios acima quando aplicáveis, (c) transições entre slides, (d) tempo-alvo. Mais: um banco
de **prováveis perguntas da banca** com respostas curtas (K=2, "e se mentir?", POL-007, por que
workflow_dispatch e não PR real, independência de jurisdição no nível da decisão vs Report).