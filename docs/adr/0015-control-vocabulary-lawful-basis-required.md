# ADR-0015 — Control vocabulary: `lawful_basis_required` and the sensitivity gate

**Status.** Accepted — ratified by the author on 2026-07-02 (draft authored on branch `eval/test-cases-exploratory`, 2026-06-01; mechanical assembly of empirically-verified engine facts plus a decision space, per the project's ADR-authoring convention — Code assembles and cross-references, the author decides). Ratified as drafted: Decisions 1–3 stand, including Decision 3's constraint that the token stays out of every loaded vocabulary until the engine change ships. Verified at ratification (2026-07-02): `_verdict_for_control` still has no `lawful_basis_required` branch, so the engine change and the POL-008 migration remain future work (see Migration). The open verdict-wording question in Consequences is resolved by Decision 1 as written (sensitive governed category with a common basis → `violation_candidate`).
**Date.** 2026-06-01
**Supersedes.** Nothing.
**Superseded by.** Nothing.
**Related.** ADR-0007 (MVP collection-only scope — the verdict surface this control plugs into), ADR-0005 (multi-client: `control` is a jurisdictional vocabulary, data not code), ADR-0006 (English snake_case tokens), SCHEMA §6.3/§9.5 (`control` evolution path), `matcher.md` §8.3 (the `category`-not-consumed debt this ADR would pay down), `docs/eval/test-cases-proposal.md` (the eval cases that motivate it).

## Context

The MVP `control` vocabulary has exactly two tokens (`policy/vocabularies/LGPD/control.yaml`, SCHEMA §9.5): `consent_required` and `anonymization_required`. The engine (`src/mcp_servers/policy_reader/tools.py` `_verdict_for_control`, **read on 2026-06-01**) evaluates them as:

- `consent_required` → `compliant` iff `context.legal_basis == "consent"` (exact token equality); absence → `violation_candidate` (omission); any other value → `violation_candidate` (non-canonical value).
- `anonymization_required` → **always** `indeterminate` (the `structured_context` has no field to declare an effective upstream transformation).
- any other control → `raise AssertionError` (the MVP is closed to two controls; the branch fails loudly rather than falling through).

Two limitations surface the moment a realistic client Policy is authored (the evaluation Policy of this branch):

1. **`consent_required` is over-strict for non-consent bases.** Many lawful collections declare a basis other than consent — `legal_obligation` (Art. 7º, II — KYC, fiscal), `contract_performance` (Art. 7º, V), `legitimate_interests` (Art. 7º, IX). All are valid Art. 7º bases. Against a `consent_required` clause the engine marks every one of them `violation_candidate` — a false positive of conformance. The fixture pack (`tests/.../clauses_pack_check_applicability/`) uses `consent_required` precisely in this strict "requires consent" sense; inheriting that semantics into the evaluation Policy would bake the false positive into the banca demonstration.

2. **The engine does not distinguish common from sensitive bases.** `_verdict_for_control` compares against the single token `consent` and never reads the `category` field (`personal_data` vs `sensitive_data`) of the `lawful_basis` vocabulary. For a clause over a sensitive class (`special_category: true`, e.g. POL-007 on `dados_de_saude`), the engine returns `compliant` for the juridically-insufficient common token `consent`, and `violation_candidate` for the juridically-correct sensitive token `explicit_consent` (Art. 11, I) — it **inverts** the legally expected answer. This is the `category`-not-consumed debt already registered in `matcher.md` §8.3.

A third constraint is structural: `control` is a **jurisdictional vocabulary** (ADR-0005), read as data from `control.yaml`; the **verdict semantics** of each token live in engine **code** (`_verdict_for_control`). Adding a token to the YAML is therefore necessary but **not sufficient** — and worse than inert: because the loader does not validate `clause.control` against the vocabulary (`loader.py` cross-validates `lei`, schema version, and clause shape, but not `control`), a clause using an unimplemented control loads fine and then crashes the engine at evaluation time.

## Decision (ratified by the author on 2026-07-02)

### 1. Introduce `lawful_basis_required` as a third `control` token

Semantics: the governed collection requires **some** valid lawful basis from the `lawful_basis` vocabulary, with a **sensitivity gate** derived from `special_category` of the governed category:

- governed category common (`special_category: false`) → any `category: personal_data` basis → `compliant`;
- governed category sensitive (`special_category: true`) → require a `category: sensitive_data` basis → `compliant`; a common basis → `violation_candidate`;
- `legal_basis` absent → `violation_candidate` (omission);
- `legal_basis` present but not a vocabulary token → `violation_candidate` (non-canonical value).

This keeps `consent_required` for clauses that genuinely require consent (consent is stricter than "any basis"), and adds `lawful_basis_required` for clauses where any adequate basis suffices.

### 2. The token addition is paired with a mandatory engine change

Adding `lawful_basis_required` to `control.yaml` is data; it is inert until `_verdict_for_control` gains a branch for it. The minimal engine change (sketch, not yet implemented):

```python
# in _verdict_for_control, before the final AssertionError:
if clause.control == "lawful_basis_required":
    lb_vocab = _load_lawful_basis_vocabulary(state)   # name -> category
    governed_special = _any_special_category(clause, state)  # via POL-000 special_category
    basis = context.legal_basis
    if basis is None:
        return violation(... "omite legal_basis")
    if basis not in lb_vocab:
        return violation(... "fora do vocabulário lawful_basis")
    if governed_special and lb_vocab[basis] != "sensitive_data":
        return violation(... "categoria sensível exige base do Art. 11")
    return compliant(...)
```

This requires a new vocabulary loader (`_load_lawful_basis_vocabulary`, reading the `category` field already present in `lawful_basis.yaml`) and a helper resolving `special_category` from POL-000 for the clause's governed categories. It is additive to the engine, does not change the tool interface (`check_applicability` input/output unchanged), and is testable in isolation.

### 3. Until the engine change ships, the token is kept out of every loaded vocabulary

`lawful_basis_required` is NOT added to any loaded `control.yaml` — neither the product seed `policy/` nor the eval instances `policies/eval-lgpd/` / `policies/eval-gdpr/`. Because the loader does not validate `control` and `SubstantiveClause.control` is a free `str`, a clause using the token would load fine and then crash the Matcher's active-clause sweep (`AssertionError`); adding the token to a loaded vocab would be a latent foot-gun. The decision is published only in this ADR, in `docs/eval/test-cases-proposal.md`, and in the demonstration clause **POL-008**, which lives in `eval/proposed/` — OUTSIDE the eval catalog (`eval/cases.yaml`) and outside every loaded root, so the engine harness never invokes it. If a future loaded policy ever uses an unimplemented control, the engine raises `AssertionError` loudly — the intended fail-fast, not a silent miss.

## Alternatives considered

- **A. Object form `control: {type, value}`** (the SCHEMA §6.3 evolution path). More general (supports encryption-at-rest, retention, DPIA later) but a larger schema change (would bump `policy_schema_version`). `lawful_basis_required` as a flat token is the smaller step and composes with the object form later.
- **B. Keep `consent_required` and author clauses only where consent truly applies.** Avoids the engine change but cannot express "any valid basis" at all — the documentos/KYC case stays unmodelable, and the false positive of (1) persists for any non-consent collection.
- **C. Make the engine treat any vocabulary basis as compliant for `consent_required`.** Rejected: conflates "requires consent" with "requires any basis"; consent is genuinely stricter and the distinction is legally meaningful.

## Consequences

**Positive.** The evaluation Policy can express the common lawful-collection case without false positives; the sensitivity gate pays down the `category`-not-consumed debt (`matcher.md` §8.3); `control` remains data, with its semantics versioned in code under this ADR.

**Negative / open.** Requires an engine change before any loaded clause can use it; the gate's exact verdict wording and the `verification`/`indeterminate` interaction (does a sensitive clause with a present-but-common basis return `violation_candidate` or `indeterminate`?) need ratification. Until then the token is deliberately kept out of every loaded `control.yaml` (it lives only in this ADR, the proposal doc, and the staged POL-008) to avoid the foot-gun of a clause using an unimplemented control and crashing the sweep.

**Migration.** When the engine branch lands, add `lawful_basis_required` to the relevant loaded `control.yaml`, move `eval/proposed/POL-008.yaml` into `policies/eval-lgpd/clauses/`, add `policies/eval-lgpd/rationale/POL-008.md`, and bump that instance's `policy_version`.
