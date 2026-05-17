# ADR-0002: MCP server conventions and deferred decisions

## Status

Accepted — 2026-05-10, session #09.

## Context

Two MCP server specs reached v0.1.0 during sessions #05 and #07:
`docs/specs/policy-reader/canonical.md` and `docs/specs/semgrep-runner/canonical.md`. Both
were written before this ADR existed, and both reference ADR-0002 as
the governing record for two distinct kinds of decision:

1. Project-wide conventions that emerged organically during spec
   authoring (placement of structured payloads, naming, error
   contract, review form, versioning, URI scheme). These need formal
   status so that future spec authors apply them without re-deriving
   from prior specs.

2. Component-level deferments — features the specs deliberately
   exclude from MVP, listed in their §7.1 sections with the marker
   "Registrado em ADR-0002." These need a single ledger with revisit
   criteria so that "deferred" does not silently become "abandoned."

This ADR consolidates both. It introduces no new design. Each decision
below was already materialized in one or both specs by the time this
ADR was written; the ADR's role is to lift conventions out of the
spec text where they were repeated and to gather deferments into one
place.

The form is deliberately lighter than ADR-0001. Each decision carries
brief rationale and consequences; each deferment carries description,
why-deferred, and revisit criterion. Detail lives in the specs and in
the learning-log; this ADR is the index.

## Decisions at a glance

### Part 1 — Conventions

| # | Decision | Read when |
|---|----------|-----------|
| 1 | `CallToolResult` payload placement: hybrid `structuredContent` + `content` | Implementing any MCP tool return; reviewing tool spec §4 |
| 2 | MCP server and tool naming convention | Naming a new MCP server or tool; writing `mcp__server__tool` references; aligning `.mcp.json` keys with AgentDefinition `tools` lists |
| 3 | Three-class error contract (`validation`, `business`, `system`) | Implementing any tool error path; designing new `errorCode` values; deciding `isRetryable` semantics |
| 4 | Positive declaration of empty error classes | Reviewing or authoring spec §5; deciding whether to omit an empty class |
| 5 | "Three beats" review pass form in §8.<final> | Reviewing a spec against `architecture-overview.md`; authoring a new spec's review section |
| 6 | Specification versioning | Bumping `spec_version`; deciding major/minor/patch for a spec change; preparing 0.x → 1.0 promotion |
| 7 | Custom URI schemes for domain resources | Adding a new resource; designing resource URI; deciding between `policy://` (or analogous) vs generic schemes |

### Part 2 — Deferments (A–I)

Referenced by letter elsewhere in the project. See Part 2 section
below for descriptions, why-deferred, and revisit criteria.

## Part 1 — Project conventions

### 1. CallToolResult payload placement: hybrid structuredContent + content

Every tool in the project places its structured payload in
`structuredContent` of the `CallToolResult`. The `content` array
carries a single `TextContent` block whose `text` field reproduces
the same information in human-readable prose (the `message` on
errors; the `evidence` or summary on successes). Both channels are
populated on every return; never one without the other.

**Rationale.** Web search during session #06 confirmed Claude Code
2.0.22+ prioritizes `structuredContent` when both channels are
present (Issue #9962 on `anthropics/claude-code`). Dual placement
provides forward-compatible structure for callers that consume
parsed payloads, while preserving readability for logs, debugging,
and any caller that ignores `structuredContent`. Single-channel
placement (only one or only the other) loses one audience.

**Consequences.** Spec authors must define both forms in §4 of every
tool. Drift between the two channels (structured says X, prose says
Y) is a contract bug, treated as a test failure during implementation.
`isError` at the protocol level remains the canonical error signal;
`errorCode` inside `structuredContent` is the domain-level category
(see Decision 3).

### 2. MCP server and tool naming convention

Server names use hyphens as word separators: `policy-reader`,
`semgrep-runner`. Tool names use lowercase snake_case: `get_clause`,
`scan_diff`, `check_applicability`. The runtime-exposed handle takes
the canonical form `mcp__<server>__<tool>` (two underscores as
delimiter), where the server segment is exactly the key declared in
`.mcp.json`.

**Rationale.** Three configurations reference the same identifier:
`.mcp.json` keys, `tools` lists in AgentDefinition frontmatter, and
hook matchers in `.claude/hooks/`. A single convention across the
three removes a class of misconfiguration. Hyphenated server names
follow the convention used by Anthropic reference servers
(`server-filesystem`, `server-git`); the `mcp__<server>__<tool>`
form is what Claude Code generates when exposing MCP tools to the
model.

**Consequences.** Specs authored before this ADR may carry
`semgrep_runner` (underscore) in `mcp__server__tool` references,
inherited from an earlier convention; such drift is patched on
detection. Future servers follow the hyphen convention.

### 3. Three-class error contract

All tool errors place a structured payload in `structuredContent`
with the following shape:

- `errorCode` — English, stable constant identifier (e.g.
  `INVALID_CLAUSE_ID_FORMAT`, `SCAN_TIMEOUT`).
- `message` — Portuguese, human-readable.
- `isRetryable` — boolean.
- `details` — object, shape per `errorCode`.

Each `errorCode` belongs to exactly one of three classes:

- **validation** — `isRetryable: false` always. Caller must adjust
  the input before retrying.
- **business** — `isRetryable` decided case-by-case. Example:
  `CLAUSE_DEPRECATED` is retryable because `details.successors`
  gives the caller a path to retry with a different `clause_id`.
- **system** — `isRetryable: true` in almost all cases. Transient
  infrastructure failure (binary unavailable, subprocess timeout;
  filesystem read error during startup is the exception that
  aborts before the contract takes effect).

Empty result and `indeterminate` verdict are **not errors**. They
are valid successful returns with semantic meaning, distinguished
from errors by `isError: false` at the protocol level.

**Rationale.** Maps directly to the "transient vs business vs
permission" vocabulary of Domain 2 of the certification scope.
Without explicit `isRetryable` and structured `details`, every
retryable error degenerates to non-retryable in practice — the
caller has no machine-readable way to decide whether to retry
as-is, retry with adjusted input, or escalate. Distinguishing
empty/indeterminate from error preserves the epistemic honesty of
the system: an empty result is a valid answer, not a failure.

**Consequences.** Every tool spec carries a consolidated table of
`errorCode` values with class, retryability, emitting tools,
condition, and shape of `details`. Specs without business or system
errors declare this positively (see Decision 4).

---

**Amendment (2026-05-17).** Wire placement of the error envelope
adapted to FastMCP framework constraint.

The original formulation of this decision implicitly assumed the MCP
specification's documented shape for tool errors: wire `isError: true`
on the `CallToolResult` simultaneously with the structured envelope
in `structuredContent`. The MCP specification permits this shape; the
FastMCP 3.2.4 framework — adopted in ADR-0004 — does not expose a
public API path that produces it. The framework offers two mutually
exclusive return paths: a tool returning a `dict` produces wire
`isError: false` with `structuredContent` populated; a tool raising
`ToolError(s)` produces wire `isError: true` with the message in
`content[0].text` and `structuredContent: None`. There is no public
path that combines `isError: true` with a structured envelope.

This was confirmed empirically during session #20 via direct reading
of the FastMCP source under the pinned version (`fastmcp==3.2.4`,
`uv.lock`): `fastmcp/tools/base.py::to_mcp_result` (line 124) and
`fastmcp/tools/base.py::convert_result` (line 270) are the two
public-API functions converting tool return values into the wire
`CallToolResult`. Neither sets `isError`. Grep across
`fastmcp/tools/` for `isError|is_error` under the pinned version
returns zero matches.

The wire flag is set elsewhere by the framework —
`mcp.server.lowlevel.server::_make_error_result` (line 467) is
called on schema-validation failures (input or output) and on
unexpected tool return types, and the success path at line 576
sets `isError=False` explicitly when populating
`structuredContent`. Neither path combines `isError: true` with a
populated `structuredContent`. There is therefore no code path —
public or internal — in either `fastmcp/tools/` or
`mcp.server.lowlevel.server` that produces the combination the
original MCP-spec-documented shape requires.

The pattern is also recognized in the broader MCP ecosystem as a
recurring concern documented in independent issues across
implementations: `IBM/mcp-context-forge` #4042 (gateway-level
validation prioritizing one channel over the other) and
`modelcontextprotocol/typescript-sdk` #654 (`isError: true` set
by tool ignored when `structuredContent` validation runs first
and rejects empty schema). Similar reports appear in other SDK
implementations. The pattern repeats across SDKs and gateways,
not only FastMCP.

The amendment adopts the following convention. For errors of domain
classes (validation, business, system per the original Decision 3),
the envelope `{errorCode, message, isRetryable, details}` is serialized
in `structuredContent` of the `CallToolResult` with wire `isError: false`.
The `content` array carries a single `TextContent` block reproducing
`message`, per Decision 1. The formal success-versus-error discriminator
is presence of the `errorCode` field in `structuredContent`: successful
returns carry positive payloads (clause, list, verdict) without
`errorCode`; error returns carry the envelope with `errorCode` populated.
Wire `isError: true` is reserved for MCP protocol-level failures
produced by the framework (schema-invalid `inputSchema`, nonexistent
tool, transport-level errors), not by the component.

**Rationale for the amendment.** Adopting the framework's two-path
constraint while preserving the structured-envelope contract of the
original Decision 3 prioritizes two properties: (a) the four-field
envelope shape that callers depend on for retry routing, and (b) the
three-class error taxonomy that maps to the certification scope's
"transient vs business vs permission" vocabulary. The cost is
relinquishing the wire `isError` flag as the formal discriminator;
the implicit discriminator (presence of `errorCode`) is structurally
equivalent and machine-checkable from the same `structuredContent`
payload the caller already parses.

**Revisit trigger.** Reopen this amendment when (a) FastMCP exposes
a public API path producing wire `isError: true` with a structured
envelope simultaneously, OR (b) the project migrates off FastMCP to
a framework with that shape available, OR (c) the MCP specification
formally adopts the implicit-discriminator pattern as preferred
practice across SDKs and gateways.

**Companion edits.** `docs/specs/policy-reader/canonical.md` §4.1,
§4.2, §4.3, §5.1, §5.3 and `docs/specs/policy-reader/compact.md` §2,
§5.1, §5.2, §5.3 updated in the same PR (`feat/canonical-sync-B`)
to reflect the amended convention in examples and in normative prose,
and in the same PR the `applicability_scope` field of clause output
is migrated to the polymorphic `applies_to` form per the empirical
shape of `models.py` since T01 (Cluster A of canonical-sync-B). In
the same PR, clause-shape examples across canonical §4.1, §4.2 and
compact §5.1, §5.2 are aligned to the empirical shape of definitional
clauses (`defines: {vocabulary_kind, entries: [...]}`,
`out_of_scope: [{topic, statutory_reference, reason, fallback}, ...]`
per SCHEMA.md §5.2-5.4 and POL-000.yaml), and the `operation`
vocabulary in examples uses the canonical tokens `storage` and
`disclosure_by_transmission` per SCHEMA.md §9.2 (replacing
pre-existing `store` and `transmit` drift). These shape corrections
are bundled here because canonical-sync-B is the first pass through
§4.1/§4.2 since the empirical clause shape stabilized; they are not
part of the isError amendment proper. The original Decision 3 text
above remains the contract for envelope shape, class semantics, and
`isRetryable` discipline; the amendment governs only wire placement.

### 4. Positive declaration of empty error classes

When a tool's contract has no `errorCode` in one of the three
classes, the spec states this explicitly rather than omitting the
row from the consolidated table. Example from
`semgrep-runner.scan_diff`: the spec declares that this tool emits
no validation errors because `base_ref` and `head_ref` are Git ref
strings validated by Git itself during subprocess invocation,
surfacing as the system-class `INVALID_REF_RESOLUTION` when invalid.

**Rationale.** An absent class in an error table can mean either
"not yet thought through" or "deliberately empty"; the reader should
not have to guess. The positive
declaration also surfaces the mechanism by which validation happens
elsewhere (downstream tool, OS, protocol), preventing a future
contributor from adding a redundant validation layer.

**Consequences.** Every spec's error contract section declares all
three classes, even when one or more is empty. Implementation tests
verify the declared classes are actually exhaustive.

### 5. "Three beats" review pass form in §8.<final>

Every spec carries a §8.<final> "Review pass do architecture-overview"
section. For each inconsistency detected between the spec under
authorship and `docs/architecture-overview.md`, the section records
three beats in prose:

1. The text currently in the overview.
2. Why that text is inconsistent with the decisions of this spec.
3. The proposed patch (concrete substitute text).

When no inconsistency is detected, the section states this positively
(see Decision 4's pattern).

**Rationale.** Operational form of principle #26 (review pass against
the architecture-overview as part of every spec). Three-beat
structure forces the reviewer to articulate the contradiction
precisely (beat 1 quotes the text, beat 2 explains the conflict,
beat 3 proposes the fix), and surfaces patches as already-formed
proposals rather than "things to do later." Without the form, review
passes tend to produce lists of vague concerns that decay into TODO
debt.

**Consequences.** Sync of the overview to the spec happens as a
dedicated commit on the spec's branch, applying the patches verbatim.
The form is replicable across future component specs.

### 6. Specification versioning

Every component spec in `docs/specs/` carries a `spec_version` field
following semantic versioning. The semantics per level:

- **major** when the component contract changes incompatibly:
  signature of an existing tool, structure of an existing successful
  return, semantics of an existing `errorCode`, or closed canonical
  vocabulary.
- **minor** when adding an optional field to an existing return, a
  new `errorCode`, a new example in a description, or a new tool or
  resource that does not remove or alter existing ones.
- **patch** when fixing typos, improving prose, or reorganizing
  sections without changing the contract.

Specs remain in `0.x` until the first end-to-end implementation of
the component passes its §8 acceptance criteria. Promotion to `1.0`
requires a dedicated ADR for that component.

**Rationale.** Specs are contracts. Without an explicit versioning
rule, "the spec changed" is ambiguous between "wording was improved"
and "callers will break." Locking the semantics of major, minor, and
patch removes that ambiguity. The `0.x` reservation matches the
convention of many open-source projects (FastMCP, Pydantic, Semgrep
itself): `0.x` signals that the contract is still being validated
empirically, not that the documentation is incomplete. The
dedicated-ADR requirement for `1.0` forces a deliberate moment of
"we have learned enough to commit to this contract."

**Consequences.** Each spec's §6.1 carries the current version and
a short note on the next planned promotion. This Decision closes the
forward-reference in `policy-reader.md` §5.5.

### 7. Custom URI schemes for domain resources

Each MCP server that exposes resources representing a domain
artifact uses a custom URI scheme matching the artifact name, rather
than the generic `mcp://`, `file://`, or `http://`. Concretely,
`policy-reader` exposes resources under `policy://`
(`policy://catalog`, `policy://schema-version`). Future servers
follow the same pattern (a hypothetical rules-serving component
would use `rules://`).

**Rationale.** Web search during session #03 confirmed that the MCP
runtime accepts any URI scheme registered by the server; there is
no required prefix. A custom scheme makes resource URIs
self-describing when they appear in logs, traces, or AgentDefinition
`mcp_servers` configurations — `policy://catalog` communicates the
artifact type without context, whereas `mcp://policy-reader/catalog`
would require the reader to know what `policy-reader` serves.
Generic schemes (`file://`, `http://`) would falsely imply a storage
or transport mechanism that does not exist (the Policy is not an
HTTP-accessible URL, nor a directly-readable file from the
consumer's perspective).

**Consequences.** Spec authors choose the scheme during §3
(Resources) of any spec that exposes resources, and document it in
that section. Components that expose no resources (e.g.,
`semgrep-runner`) are unaffected. This Decision closes the
forward-reference in `policy-reader.md` §3.

## Part 2 — Component-level deferments

Each deferment below is a feature whose absence from MVP is
deliberate. The spec that defers it lists the deferment in its §7.1
with reference to this ADR. The form is: description, why deferred,
revisit criterion.

### policy-reader

**A. Browseable individual clauses via `policy://clauses/{id}`
resource.** Eliminated from MVP because `get_clause` (tool) already
serves the same retrieval. *Revisit when:* the Policy grows beyond
~50 clauses and a human reader (legal counsel, auditor) needs to
navigate clauses directly without invoking the MCP server,
justifying a parametrized resource for human-facing browsing.

**B. Hot reload of the Policy at runtime.** Component loads the
Policy on startup; changes require restart. Deferred because the
MVP runs the server on a per-PR basis (no long-lived process to
reload), and hot reload introduces cache invalidation complexity.
*Revisit when:* the server moves to a long-lived deployment
(always-on for an organization), or when Policy revision frequency
exceeds the acceptable restart cadence.

**C. Support for alternative Policy schemas.** Component serves
only `policy_schema_version: 0.1.0`. Generalization to multiple
coexisting schema majors is deferred. *Revisit when:* a v0.2.0 of
the schema is designed AND there is at least one consumer Policy
still on v0.1.0 that cannot be migrated immediately; or when the
project gains a second consumer organization with a structurally
different Policy.

**D. Declarative annotations of data treatment in code.**
Recognition of code-level annotations (comments, decorators)
indicating consent obtained, anonymization applied, or other
treatment-relevant facts is deferred as a post-MVP evolution.
*Revisit when:* empirical validation of MVP shows a measurable rate
of `indeterminate` verdicts that could be resolved by declarative
annotations the developer would reasonably add, AND when the
annotation format has been designed in coordination with
`policy/SCHEMA.md`.

**E. Expanded Policy scope.** The Policy v0.1.0 is restricted to
`consent_required` and `anonymization_required`. Other LGPD
dimensions (transfer restrictions Art. 33+; retention limits
Art. 15-16; data subject rights Art. 18+; minors Art. 14; shared
processing Art. 26+) are deferred. *Revisit when:* empirical MVP
validation is complete AND a concrete demand is documented for a
specific additional dimension, including the static-analysis
approach to evaluate it (because extending the Policy requires
extending the verification surface, not just the data).

### semgrep-runner

**F. Cross-file findings (taint analysis).** MVP covers single-file
Semgrep rules only. Rules with `taint-mode` and cross-file traces
are deferred. *Revisit when:* the rule set's false-negative rate
against the empirical benchmark exceeds an acceptable threshold AND
the missing detections are demonstrably cross-file patterns.

**G. Configurable rule subset per call.** Tool accepts no `rule_set`
parameter; the curated server-side set applies to every invocation.
*Revisit when:* a documented use case emerges for distinct scan
modes (e.g., fast vs full, public-PR vs internal). Canonical
resolution will be tool split with autonomous descriptions, not
parametrization of `scan_diff`.

**H. Semgrep AppSec Platform integration.** Component operates with
Semgrep open-source only; `SEMGREP_APP_TOKEN` is not read; findings
are not synchronized to Semgrep cloud. *Revisit when:* the project
adopts an organizational Semgrep license AND there is a documented
need to correlate findings across repositories or visualize them in
the platform dashboard.

**I. Graceful cancellation of the Semgrep subprocess.** Timeout
sends SIGTERM followed by SIGKILL after grace period; there is no
mechanism to preserve partial state on cancellation. *Revisit
when:* Semgrep itself gains support for graceful cancellation in
diff-aware mode (upstream), OR when a use case for partial findings
emerges that overrides the epistemic-honesty argument against
partial scans (currently strong — see `semgrep-runner.md` §7).

## Aggregated consequences

- **Conventions stop being repeated in specs.** Specs already
  written carry the conventions inline; future specs reference this
  ADR in their §1 (Stack and governance) and skip the re-derivation.
  This reduces spec length and removes a drift surface (when two
  specs state the same convention with slightly different wording).
- **Deferments are tracked in one place.** Implementation can
  reference this ADR by letter (A through I) when a feature comes up
  in PR review or sprint planning. The revisit criteria are
  machine-checkable in the sense that "when X then revisit" can be
  monitored.
- **Documents that referenced ADR-0002 as forward-reference
  resolve.** The §1, §3, §5.5, §6.5, §7.1, and §7.4 of
  `policy-reader.md`; the §1, §2.1, §2.2, §6, and §7 of
  `semgrep-runner.md`; and the open questions in the
  session-handoff all collapse to a single live ADR.
- **A boundary is established between ADR-0002 and a future
  roadmap ADR.** Product-level evolutions (severity, fix-proposer,
  merge blocking, cross-PR longitudinal map, AEP, additional Policy
  dimensions at the system level) belong to a future roadmap ADR or
  to `docs/roadmap.md`, not to this one. The heuristic registered
  in session #03's learning-log applies: consolidate roadmap when
  deferments cross ≥3 ADRs.