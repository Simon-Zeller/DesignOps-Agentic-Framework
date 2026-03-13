# Specification: Token Integrity & Diff

## Purpose

Defines the behavioral requirements for Agent 10 (Token Integrity Agent) and Agent 11 (Token Diff Agent). Covers cross-tier reference graph validation, cycle detection, orphan/phantom reference scanning, tier-skip enforcement, and structured diff generation for downstream crews.

---

## Requirements

### Requirement: Cross-tier reference graph integrity

Agent 10 (Token Integrity Agent) in the Token Engine Crew MUST build a full reference graph across all three staged tier files and validate it for structural correctness: no circular references, no phantom references (targets that do not exist), and no tier-skip violations (component tokens must only reference semantic tokens; semantic tokens must only reference global tokens).

#### Acceptance Criteria

- [ ] Agent 10 loads all three staged tier files into a single merged key namespace before graph traversal.
- [ ] A circular reference (token A references token B which references token A) is detected as a fatal violation.
- [ ] A phantom reference (token references a key that does not exist in any tier) is detected as a fatal violation.
- [ ] A tier-skip violation (component token directly references global token, bypassing semantic tier) is detected as a fatal violation.
- [ ] All fatal violations are written to `tokens/validation-rejection.json`, appended to any existing failures from Agent 8, before the crew exits non-zero.
- [ ] Orphaned tokens (defined but never referenced) are written to `tokens/integrity-report.json` as warnings — they do NOT trigger a retry.
- [ ] If no fatal integrity violations exist, the crew continues to task T5.

#### Scenario: Clean reference graph

- GIVEN all token references form a valid DAG (directed acyclic graph) within correct tier boundaries
- WHEN Agent 10 runs task T4
- THEN no fatal violations are recorded
- AND `tokens/integrity-report.json` is written with `fatal_count: 0`
- AND the crew continues to task T5

#### Scenario: Circular reference detected

- GIVEN token `semantic.color.text.primary` references `{semantic.color.interactive.default}` which in turn references `{semantic.color.text.primary}`
- WHEN Agent 10 traverses the reference graph
- THEN a fatal violation is recorded with `check: "circular_reference"` and the full cycle path in `detail`
- AND `tokens/validation-rejection.json` is written (or updated) with `fatal_count >= 1`
- AND Token Engine Crew exits non-zero

#### Scenario: Phantom reference detected

- GIVEN token `semantic.color.surface.brand` references `{color.brand.nonexistent}` which does not exist in any tier file
- WHEN Agent 10 traverses the reference graph
- THEN a fatal violation is recorded with `check: "phantom_reference"` and the missing key in `detail`

#### Scenario: Tier-skip violation detected

- GIVEN a component-scoped token directly references a global token: `{color.neutral.100}` (skipping the semantic tier)
- WHEN Agent 10 validates tier discipline
- THEN a fatal violation is recorded with `check: "tier_skip"`
- AND the `token_path` and `target_path` are included in `detail`

#### Scenario: Orphaned global token

- GIVEN a global token `color.neutral.050` is defined but never referenced by any semantic or component token
- WHEN Agent 10 scans for orphans
- THEN a warning entry is written to `tokens/integrity-report.json` with type `"orphan"`
- AND the crew does NOT exit non-zero for this reason alone

---

### Requirement: Integrity report output

Agent 10 MUST write `tokens/integrity-report.json` regardless of whether violations were found. This file is consumed by the Analytics Crew for quality reporting.

#### Acceptance Criteria

- [ ] `tokens/integrity-report.json` is always written after task T4 completes.
- [ ] The report includes: `fatal_count`, `warning_count`, `violations[]` (fatal entries), `warnings[]` (orphan/deprecated entries), and a `graph_stats` summary (total_nodes, total_edges, max_depth).
- [ ] `violations[]` and `warnings[]` may be empty arrays but must be present.

#### Scenario: Report written on clean run

- GIVEN the reference graph is clean with no violations
- WHEN Agent 10 completes task T4
- THEN `tokens/integrity-report.json` is written with `fatal_count: 0`, `warning_count: 0`, empty arrays, and valid `graph_stats`

---

### Requirement: Structured token diff generation

Agent 11 (Token Diff Agent) in the Token Engine Crew MUST generate a structured diff of the token set — classifying every token as `added`, `modified`, `removed`, or `deprecated` — and write it to `tokens/diff.json` for consumption by the Documentation Crew (changelog) and Analytics Crew (compliance reports).

#### Acceptance Criteria

- [ ] Agent 11 reads `tokens/staged/*.tokens.json` as the "current" state.
- [ ] If a prior `tokens/diff.json` exists from a previous run, Agent 11 uses the prior compiled tokens as the baseline. If no prior exists, every token is classified as `added`.
- [ ] `tokens/diff.json` has the schema: `{ generated_at, is_initial_generation, added[], modified[], removed[], deprecated[] }`.
- [ ] Each entry in `added[]` contains: `token_path`, `tier`, `type`, `value`.
- [ ] Each entry in `modified[]` contains: `token_path`, `tier`, `old_value`, `new_value`.
- [ ] Each entry in `removed[]` contains: `token_path`, `tier`.
- [ ] Each entry in `deprecated[]` contains: `token_path`, `tier`, `deprecated_since`.
- [ ] `tokens/diff.json` is always written after task T5, even on first generation (full `added` inventory).

#### Scenario: Initial generation — all tokens classified as added

- GIVEN no prior `tokens/diff.json` exists
- WHEN Agent 11 runs task T5
- THEN `tokens/diff.json` is written with `is_initial_generation: true`
- AND every token appears in the `added[]` array
- AND `modified[]`, `removed[]`, `deprecated[]` are all empty arrays

#### Scenario: Re-generation with modified token

- GIVEN a prior generation exists with token `color.brand.primary` having `$value: "#005FCC"`
- AND the new staged tokens have `color.brand.primary` with `$value: "#0066FF"`
- WHEN Agent 11 runs task T5
- THEN the token appears in `modified[]` with `old_value: "#005FCC"` and `new_value: "#0066FF"`
- AND `is_initial_generation` is `false`

#### Scenario: Re-generation with removed token

- GIVEN a prior generation included token `color.brand.secondary`
- AND the new staged tokens do not contain `color.brand.secondary`
- WHEN Agent 11 generates the diff
- THEN `color.brand.secondary` appears in `removed[]`

---

### Requirement: Deprecation tagging

Agent 11 MAY invoke `DeprecationTagger` to apply `$extensions.com.daf.deprecated` metadata to tokens that have been superseded based on deprecation markers in the Brand Profile or change annotations. Deprecated tokens appear in the `deprecated[]` diff section.

#### Acceptance Criteria

- [ ] If the Brand Profile includes a `deprecatedTokens` list, each listed token path is processed by `DeprecationTagger`.
- [ ] `DeprecationTagger` injects `$extensions.com.daf.deprecated: { since: "<version>", reason: "<text>" }` into the staged token file.
- [ ] Deprecated tokens are included in `tokens/diff.json` under `deprecated[]`.
- [ ] Deprecated tokens still appear as valid tokens in the compiled outputs (they are not removed, only annotated).

#### Scenario: Brand Profile specifies a deprecated token

- GIVEN `brand-profile.json` includes `deprecatedTokens: [{ path: "color.brand.accent", since: "1.0.0", reason: "replaced by color.brand.highlight" }]`
- WHEN Agent 11 runs the deprecation tagger
- THEN `color.brand.accent` in the staged token file has `$extensions.com.daf.deprecated` injected
- AND the token appears in `deprecated[]` in `tokens/diff.json`
- AND the token is still present in `tokens/compiled/tokens.json`
