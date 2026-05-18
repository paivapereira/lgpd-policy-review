# Session Management

Heuristic distilled in sessão #22 about when to use fresh sessions vs
persistent sessions across Chat and Code.

## Rule

Context worth preserving vs discarding is a function of **output
type**, not session role (Chat vs Code):

- **Outputs verifiable empirically** (code with gates: pytest, ruff,
  mypy; diff review against contracts) → **fresh session per cycle**.
  Avoids silent cross-contamination that gates may not detect.
- **Outputs that depend on narrative continuity** (decisions,
  ratifications, multi-round review, prep deliberation, learning-log
  drafting) → **persistent session across multiple Code cycles**.
  Each decision builds on prior decisions; fresh restart loses
  rationale.

## Concrete application

- Sessão Chat persiste durante prep de prompt + execução Code +
  Chat review + close (learning-log + handoff).
- Sessões Code rotacionam: uma sessão por feature task, uma por
  cleanup, uma por housekeeping mecânico.
- Chat fresh só após o ciclo completo da task fechar (PR mergeada,
  learning-log atualizado, handoff atualizado).

## Exception

Housekeeping and cosmetic edits don't require strict session
discipline — they're verifiable by direct diff inspection. May be
done in any session, in any order, by any tool (Chat, Code, manual
edit). The pattern formalizes when discipline matters; it doesn't
impose discipline universally.

## False-alarm correction (sessão #22.5)

If a user thinks they violated the session-discipline pattern (e.g.,
opened a Code session that already carried context instead of a
fresh one), the resolution is **not** to redo — it's to verify the
diff is clean. The pattern is descriptive of a property
(auditability), not a ritual.

## Reference

Learning-log entries for sessions #19, #20, #21, #22 carry empirical
baseline for this heuristic.
