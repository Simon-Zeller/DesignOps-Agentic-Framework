# Specification: Token Ingestion & Validation

## Purpose

Defines the behavioral requirements for Agent 7 (Token Ingestion Agent) and Agent 8 (Token Validation Agent) in the Token Engine Crew. Covers normalisation of raw token files, DTCG schema compliance, naming convention enforcement, WCAG contrast verification, and the structured rejection contract that drives cross-phase retry.

---

## Requirements

### Requirement: Token file ingestion and normalisation

Agents 7 (Token Ingestion Agent) in the Token Engine Crew MUST read all three raw token tier files produced by Agent 2 (Token Foundation Agent) — `tokens/base.tokens.json`, `tokens/semantic.tokens.json`, `tokens/component.tokens.json` — normalise them to W3C DTCG format using `WC3DTCGFormatter`, and stage them to `tokens/staged/` before any validation occurs.

#### Acceptance Criteria

- [ ] Agent 7 reads all three tier files from `tokens/` in the shared output folder.
- [ ] Agent 7 writes normalised copies to `tokens/staged/base.tokens.json`, `tokens/staged/semantic.tokens.json`, `tokens/staged/component.tokens.json`.
- [ ] If any tier file is absent, Agent 7 raises a fatal error and the Token Engine Crew exits non-zero without writing any staged files.
- [ ] Duplicate token keys within a single tier file are detected and reported; the crew exits non-zero if duplicates are present.
- [ ] All subsequent Token Engine agents read from `tokens/staged/` not `tokens/`.

#### Scenario: Valid three-tier token set

- GIVEN raw token files exist at `tokens/base.tokens.json`, `tokens/semantic.tokens.json`, `tokens/component.tokens.json` with valid DTCG structure
- WHEN Agent 7 runs task T1
- THEN three normalised files are written to `tokens/staged/`
- AND each file is a valid W3C DTCG JSON document
- AND no error is raised

#### Scenario: Missing tier file

- GIVEN `tokens/semantic.tokens.json` does not exist
- WHEN Agent 7 runs task T1
- THEN Agent 7 raises a fatal error with a message identifying the missing file
- AND no staged files are written
- AND Token Engine Crew exits non-zero

#### Scenario: Duplicate token key within a tier

- GIVEN `tokens/base.tokens.json` contains the key `color.brand.primary` declared twice
- WHEN Agent 7 runs task T1
- THEN Agent 7 detects the duplicate key
- AND reports it in the error output
- AND the crew exits non-zero without staging files

---

### Requirement: DTCG schema compliance validation

Agent 8 (Token Validation Agent) in the Token Engine Crew MUST validate all staged token files against the pinned W3C DTCG JSON Schema. Any token missing required fields (`$type`, `$value`) or using unsupported field names SHALL be reported as a fatal validation failure.

#### Acceptance Criteria

- [ ] Every token node in all three staged tier files is validated against the DTCG schema.
- [ ] Tokens missing `$type` or `$value` produce a fatal violation entry in the rejection output.
- [ ] Tokens with unrecognised fields (not in the DTCG spec) produce a warning violation entry.
- [ ] If no fatal violations exist, `tokens/validation-rejection.json` is NOT written (or is deleted if it existed from a prior run).
- [ ] If fatal violations exist, `tokens/validation-rejection.json` is written with the schema defined in the design doc.

#### Scenario: Fully DTCG-compliant staged tokens

- GIVEN all staged token files conform to the W3C DTCG schema
- WHEN Agent 8 runs task T2
- THEN no `tokens/validation-rejection.json` is written
- AND Agent 8 returns a success status

#### Scenario: Token missing `$type` field

- GIVEN a token in `tokens/staged/base.tokens.json` has a `$value` but no `$type`
- WHEN Agent 8 runs task T2
- THEN a fatal violation is recorded for that token path
- AND `tokens/validation-rejection.json` is written with `fatal_count >= 1`
- AND the Token Engine Crew exits non-zero

#### Scenario: Token with only unrecognised extra field

- GIVEN a token has a valid `$type` and `$value` but also an unrecognised field `$foo`
- WHEN Agent 8 runs task T2
- THEN a warning violation is recorded (not fatal)
- AND `fatal_count` in the rejection file is 0
- AND the crew does NOT exit non-zero for this reason alone

---

### Requirement: Token naming convention enforcement

Agent 8 MUST run `NamingLinter` against all staged token files to enforce: consistent casing (kebab-case or dot-notation per tier convention), no abbreviations from a known abbreviation blocklist, and required category prefix per tier (global tokens must start with a recognised primitive category).

#### Acceptance Criteria

- [ ] All token keys are checked against naming rules.
- [ ] A token key containing a blocked abbreviation (e.g., `bg`, `clr`, `btn`) produces a warning violation.
- [ ] A token key using inconsistent casing (e.g., `camelCase` in a context requiring `kebab-case`) produces a fatal violation.
- [ ] Naming violations are included in `tokens/validation-rejection.json` alongside schema violations.
- [ ] The list of blocked abbreviations is configurable via a constant in `naming_linter.py`.

#### Scenario: Token key contains blocked abbreviation

- GIVEN a token named `color.bg.primary` where `bg` is in the abbreviation blocklist
- WHEN Agent 8 runs the naming linter
- THEN a warning violation is emitted for that token path with detail "abbreviation: bg"
- AND the total `warning_count` in the rejection output increases by 1

#### Scenario: Token key uses wrong casing

- GIVEN a token named `colorBrandPrimary` (camelCase) in the global tier
- WHEN Agent 8 runs the naming linter
- THEN a fatal violation is emitted for that token path
- AND `fatal_count` increases by 1

---

### Requirement: WCAG contrast ratio verification

Agent 8 MUST verify WCAG contrast ratios for all foreground/background colour pairs declared in the staged semantic token tier. Pairs with contrast below 4.5:1 (AA-normal) are fatal; pairs below 3:1 (AA-large) for tokens annotated as large-text scale are fatal; pairs below 7:1 for tokens annotated as AAA are fatal. The Brand Profile's target a11y level drives which threshold applies.

#### Acceptance Criteria

- [ ] Agent 8 uses `ContrastSafePairer` (existing tool) to verify all declared colour pairs.
- [ ] The contrast check targets are derived from the semantic token tier's foreground/background pair declarations.
- [ ] Pairs failing the applicable WCAG threshold produce a fatal violation in the rejection output.
- [ ] Pairs meeting the threshold produce no violation.
- [ ] If no colour pair declarations are present in the staged tokens, the contrast check is skipped and a warning is emitted (not fatal).

#### Scenario: Foreground/background pair meets AA threshold

- GIVEN a semantic token pair `color.text.default` / `color.background.surface` with computed contrast ratio ≥ 4.5:1
- WHEN Agent 8 runs contrast verification
- THEN no violation is emitted for this pair

#### Scenario: Foreground/background pair fails AA threshold

- GIVEN a semantic token pair with computed contrast ratio of 3.2:1 (below 4.5:1 AA threshold)
- WHEN Agent 8 runs contrast verification
- THEN a fatal violation is emitted with detail including the actual ratio and required ratio
- AND `fatal_count` increases by 1

#### Scenario: No colour pair declarations present

- GIVEN the staged semantic tokens contain no foreground/background pair annotations
- WHEN Agent 8 runs contrast verification
- THEN a warning is emitted: "no colour pairs declared — contrast check skipped"
- AND `warning_count` increases by 1
- AND the crew does NOT exit non-zero for this reason alone

---

### Requirement: Cross-phase retry rejection contract

When Agent 8 detects fatal violations, the rejection file written to `tokens/validation-rejection.json` MUST conform to the schema agreed with Agent 6 (First Publish Agent) so that retry routing functions correctly.

#### Acceptance Criteria

- [ ] `tokens/validation-rejection.json` has the exact schema: `{ phase, agent, attempt, timestamp, failures[], fatal_count, warning_count }`.
- [ ] Each entry in `failures[]` has: `check`, `severity`, `token_path`, `detail`, `suggestion`.
- [ ] `fatal_count` equals the count of failures with `severity: "fatal"`.
- [ ] `warning_count` equals the count of failures with `severity: "warning"`.
- [ ] The file is deleted (or absent) when validation passes with zero fatal violations.
- [ ] Agent 6 reads this file after Token Engine Crew exits non-zero and only triggers retry when `fatal_count > 0`.

#### Scenario: Successful validation — rejection file absent

- GIVEN all staged tokens pass all validation checks (schema, naming, contrast)
- WHEN Agent 8 completes task T2
- THEN `tokens/validation-rejection.json` does not exist (or was deleted if present from a prior run)

#### Scenario: Fatal violation exists — Agent 6 retries

- GIVEN Agent 8 writes `tokens/validation-rejection.json` with `fatal_count: 2`
- WHEN Agent 6 reads the file after Token Engine exits non-zero
- THEN Agent 6 re-invokes Agent 2's task with the `failures[]` array as appended rejection context
- AND `attempt` in the next rejection file (if any) is incremented by 1
