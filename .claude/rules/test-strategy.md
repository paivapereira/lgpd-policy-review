---
paths: "tests/**/*.py"
---

# Test Strategy

Conventions distilled empirically through sessions #19-#22 (T01,
T02a, T02b implementation).

## Assertion strictness scales with the role of the test

Two distinct roles:

### Tests that DEFINE a contract (anchors)

Anchor tests exist to exercise an invariant of the contract by code.
Without the anchor, the invariant lives only in the spec, and an
implementation that violates the invariant by coincidence (e.g.,
filtering substantive-only when the result happens to be
definitional-only) passes silently.

**Assertion style:** strict. Exact ordering, exact counts, exact set
membership, exact rendered text.

Example from T02b: `test_polymorphic_mix_at_art_5` asserts
`len(clauses) == 3`, `_ids(payload) == ["POL-000", "POL-901",
"POL-902"]` exact ordering, `types == {"definitional", "substantive"}`
exact, rendered text exact match.

### Tests that EXERCISE a contract (acceptance scenarios)

Acceptance scenario tests validate one facet of the contract under
realistic conditions (real fixtures, real packs). Multiple AS
exercise different dimensions; each AS focuses on one dimension.

**Assertion style:** subset / inclusion. Asserts presence of expected
items and absence of items that should be excluded, without requiring
exact count match against the fixture.

Example from T02b: `test_as1_matches_by_artigo` asserts
`"POL-001" in returned_ids`, `"POL-004" in returned_ids`,
`"POL-003" not in returned_ids` (deprecated). Does NOT assert
`len == 2` because future pack extensions might add active clauses
at the same Art. 7º without breaking the AS.

## Granularity calibration by failure dimension

When an AS covers multiple sub-cases (e.g., AS-2 "prefix-hierarchical
match semantics" covers both narrow-query and broad-query
sub-scenarios), prefer **splitting into multiple test functions**
(one per sub-case) over a single function with multiple assertion
blocks.

Empirical justification (sessão #22): T02b's AS-2 was split into
`test_as2_narrow_query_excludes_general_stored` and
`test_as2_broad_query_matches_general_and_specific_stored`. The bug
in `_matches` (incorrect short-circuit `if spec is None: return True`)
was caught only by AS-2 narrow on first run. Other AS (AS-1, AS-3,
AS-4, AS-5, anchor) all passed by coincidence. Without the split, the
bug would have landed silently in main.

Rule: **granularity is calibrated by failure dimension expected, not
by scenario count.** Two sub-cases that exercise different code paths
warrant two functions even if both share the same fixture.

## Anchor test as second-line defense

For every tool with a non-trivial contract invariant (polymorphic
output, anti-uniformization, structural ordering), add at least one
anchor test labeled distinctly from acceptance scenarios. Without the
anchor, the invariant relies on the spec being read correctly — an
implementation that violates by coincidence passes all AS.

Convention: anchor test names do NOT start with `test_as*_`. They are
labeled by what they validate (e.g., `test_polymorphic_mix_at_art_5`,
`test_documents_fastmcp_tool_call_shape`).

## Fixture composition discipline

Fixtures that mutate shared state (e.g.,
`policy_root_with_pack_clauses` extended across T02a / T02b / T03 to
include more pack clauses) should be extended in conftest only when
the extension doesn't break previous-task asserts. Verify by reading
previous-task tests directly before extending. If the extension would
break asserts (e.g., asserts based on clause count), create a new
fixture instead of mutating. T02b made this decision deliberately
(see learning-log #22 DD-4 reversion).
