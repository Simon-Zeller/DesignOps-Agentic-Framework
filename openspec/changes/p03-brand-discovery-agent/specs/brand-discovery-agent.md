# Specification

## Purpose

Behavioral requirements for the Brand Discovery Agent (Agent 1, DS Bootstrap Crew) and its four associated tools. This spec covers: JSON Schema validation of raw brand profiles, archetype default resolution, semantic consistency checking, default field filling, the `daf generate` CLI command, and Human Gate 1 (Brand Profile Approval).

Agent 1 is the first CrewAI agent in the pipeline. It transforms the raw output of the P02 interview CLI into a validated, enriched, fully-specified `brand-profile.json` that all 8 downstream crews depend on (§3.6).

---

## Requirements

### Requirement: Brand Profile Schema Validation

The `BrandProfileSchemaValidator` tool MUST validate the raw `brand-profile.json` against the §6 schema before any enrichment occurs.

#### Acceptance Criteria

- [ ] Validation rejects profiles missing `name` or `archetype` with field-level error messages
- [ ] Validation rejects profiles where `archetype` is not one of the five defined values
- [ ] Validation rejects profiles with malformed hex color values (non-`#RRGGBB` / `#RGB` strings)
- [ ] Validation rejects profiles where `typography.scaleRatio` is outside `[1.0, 2.0]`
- [ ] Validation rejects profiles where `typography.baseSize` is outside `[8, 24]`
- [ ] Validation accepts profiles with only `name` and `archetype` (all other fields optional)
- [ ] Validation returns a structured list of `{ field: str, message: str }` objects, not a single string
- [ ] Validation errors in the first step halt task execution before tools 2–4 run

#### Scenario: Valid minimal profile passes validation

- GIVEN a `brand-profile.json` containing only `name: "Acme"` and `archetype: "enterprise-b2b"`
- WHEN `BrandProfileSchemaValidator` runs
- THEN validation returns success with zero errors
- AND execution proceeds to `ArchetypeResolver`

#### Scenario: Missing required field fails validation

- GIVEN a `brand-profile.json` with `archetype: "consumer-b2c"` but no `name`
- WHEN `BrandProfileSchemaValidator` runs
- THEN validation returns `[{ "field": "name", "message": "Required field missing" }]`
- AND the CLI prints the field-level errors and exits with code 1

#### Scenario: Invalid hex color value

- GIVEN a `brand-profile.json` with `colors.primary: "zz9900"` (missing `#`)
- WHEN `BrandProfileSchemaValidator` runs
- THEN validation returns `[{ "field": "colors.primary", "message": "Invalid hex color: must be #RGB or #RRGGBB" }]`

#### Scenario: Natural language color description is allowed

- GIVEN a `brand-profile.json` with `colors.primary: "a warm corporate red"`
- WHEN `BrandProfileSchemaValidator` runs
- THEN validation returns success (natural language strings are valid per §13.3)
- AND the string is stored verbatim for the agent's LLM to annotate

---

### Requirement: Archetype Default Resolution

The `ArchetypeResolver` tool MUST return a complete defaults dictionary for every optional §6 field, keyed by archetype.

#### Acceptance Criteria

- [ ] Returns a complete defaults dict for all five archetypes: `enterprise-b2b`, `consumer-b2c`, `mobile-first`, `multi-brand`, `custom`
- [ ] Every optional §6 field has a value in the returned defaults dict (no `None` values)
- [ ] `enterprise-b2b` defaults: conservative palette, readable type scale, dense layouts, comprehensive scope, AA accessibility
- [ ] `consumer-b2c` defaults: vibrant palette, expressive type scale, spacious layouts, standard scope, AA accessibility
- [ ] `mobile-first` defaults: compact density, touch-optimized spacing, limited breakpoints, starter scope, AAA accessibility
- [ ] `multi-brand` defaults: neutral base palette, standard scope, all themes enabled, AA accessibility
- [ ] `custom` defaults: universal baseline (8px base unit, default density, AA, standard scope, moderate radius)

#### Scenario: Enterprise archetype defaults fill all optional fields

- GIVEN a profile with `archetype: "enterprise-b2b"` and no other optional fields
- WHEN `ArchetypeResolver` runs
- THEN it returns a dict where `spacing.density = "compact"`, `componentScope = "comprehensive"`, `accessibility = "AA"`, `borderRadius = "subtle"`
- AND all §6 optional fields have non-null default values

#### Scenario: Mobile-first archetype sets AAA accessibility and starter scope

- GIVEN a profile with `archetype: "mobile-first"`
- WHEN `ArchetypeResolver` runs
- THEN `accessibility = "AAA"`, `componentScope = "starter"`, `spacing.density = "compact"`, `breakpoints.strategy = "mobile-first"`

#### Scenario: Multi-brand archetype enables brand overrides

- GIVEN a profile with `archetype: "multi-brand"`
- WHEN `ArchetypeResolver` runs
- THEN `themes.brandOverrides = true` and `themes.modes` includes `"light"`, `"dark"`, and `"high-contrast"`

---

### Requirement: Consistency Checking

The `ConsistencyChecker` tool MUST detect semantic contradictions in the profile and return structured findings with severity levels.

#### Acceptance Criteria

- [ ] Returns a list of `{ field: str, message: str, severity: "error" | "warning" }` objects
- [ ] Returns empty list for a fully consistent profile (no false positives)
- [ ] `"compact"` density paired with `"spacious"` spacing base unit (≥12px) is flagged as `error`
- [ ] `accessibility: "AAA"` paired with `archetype: "consumer-b2c"` is flagged as `warning` (unusual but not invalid)
- [ ] `archetype: "mobile-first"` paired with `componentScope: "comprehensive"` is flagged as `warning`
- [ ] `motion: "expressive"` paired with `accessibility: "AAA"` is flagged as `warning` (AAA requires reduced motion option)
- [ ] `archetype: "multi-brand"` with `themes.brandOverrides: false` is flagged as `warning`
- [ ] `error`-severity findings halt task execution; `warning`-severity findings are included in enriched profile as annotations
- [ ] Each finding message is human-readable and actionable (not just a code)

#### Scenario: Valid consistent profile returns no findings

- GIVEN an enterprise profile with `density: "compact"`, `componentScope: "comprehensive"`, `accessibility: "AA"`
- WHEN `ConsistencyChecker` runs
- THEN it returns an empty list

#### Scenario: Density contradiction is caught as error

- GIVEN a profile with `spacing.density: "compact"` and `spacing.baseUnit: 16`
- WHEN `ConsistencyChecker` runs
- THEN it returns `[{ "field": "spacing", "message": "Compact density with a 16px base unit is contradictory — compact typically uses 4px.", "severity": "error" }]`
- AND the CLI prints the contradiction and exits with code 1 without writing `brand-profile.json`

#### Scenario: Warning-level contradiction is preserved but allowed

- GIVEN a profile with `archetype: "mobile-first"` and `componentScope: "comprehensive"`
- WHEN `ConsistencyChecker` runs
- THEN it returns `[{ "field": "componentScope", "message": "Mobile-first archetype with comprehensive scope is unusual — comprehensive components may not be optimized for mobile-first density.", "severity": "warning" }]`
- AND execution continues
- AND the warning appears in the enriched profile's `_warnings` annotation
- AND the warning is shown to the user at the Human Gate

---

### Requirement: Default Filling

The `DefaultFiller` tool MUST merge archetype defaults into the raw profile, filling only fields the user left unspecified.

#### Acceptance Criteria

- [ ] User-specified fields are never overridden by archetype defaults
- [ ] Every optional §6 field receives a value in the returned profile (no `None` / missing fields)
- [ ] The result is always a fully-specified, complete `brand-profile.json`
- [ ] The tool records which fields were filled (not user-specified) in a `_filled_fields: list[str]` annotation for the Human Gate display

#### Scenario: User-specified values are preserved

- GIVEN an enterprise profile where the user specified `colors.primary: "#1a73e8"` and `accessibility: "AAA"`
- WHEN `DefaultFiller` runs with enterprise defaults (`accessibility: "AA"`)
- THEN `colors.primary = "#1a73e8"` and `accessibility = "AAA"` (user values retained)
- AND all other optional fields are filled with enterprise defaults

#### Scenario: All optional fields are filled for minimal profile

- GIVEN a profile with only `name` and `archetype: "consumer-b2c"`
- WHEN `DefaultFiller` runs
- THEN the returned profile contains all §6 fields with non-null values
- AND `_filled_fields` lists all the fields that received defaults

---

### Requirement: Brand Discovery Agent (Agent 1) — Task T1

Agent 1 (DS Bootstrap Crew, Agent 1) MUST orchestrate the four tools in sequence and return a validated, enriched `BrandProfile` Pydantic model.

#### Acceptance Criteria

- [ ] Task T1 runs tools in order: `BrandProfileSchemaValidator` → `ArchetypeResolver` → `ConsistencyChecker` → `DefaultFiller`
- [ ] Task output conforms to the `BrandProfile` Pydantic model (§6 schema)
- [ ] Agent uses Claude Sonnet (Tier 2) as defined in §3.7
- [ ] Agent annotates natural language color descriptions with hex intent notes (LLM-driven)
- [ ] Agent generates a human-readable enrichment narrative listing what defaults were applied and why
- [ ] Task fails fast on `error`-severity validation or consistency findings without proceeding to later tools
- [ ] Task output is written as the final `brand-profile.json` only after Human Gate approval

#### Scenario: Full enrichment flow — happy path

- GIVEN a raw `brand-profile.json` with `name: "Acme"`, `archetype: "enterprise-b2b"`, `colors.primary: "#003366"`, no other optional fields
- WHEN Agent 1 Task T1 executes
- THEN validation passes, archetype defaults are loaded, no consistency errors, all fields filled
- AND the agent annotates `colors.primary` with `"Archetype default: not applicable (user-specified)"`
- AND the enriched profile contains all §6 fields
- AND the enrichment narrative describes the enterprise defaults applied

#### Scenario: LLM color annotation for natural language input

- GIVEN a profile with `colors.primary: "a deep ocean blue"`
- WHEN Agent 1 Task T1 executes
- THEN the agent adds `_color_notes.primary: "Natural language: interpreted as a deep, desaturated blue (hex will be resolved by Token Foundation Agent)"` to the profile annotations
- AND the raw string `"a deep ocean blue"` is preserved in `colors.primary` for downstream resolution

#### Scenario: Task fails on schema error

- GIVEN a profile with `typography.scaleRatio: 3.5` (outside `[1.0, 2.0]` bound)
- WHEN Agent 1 Task T1 executes
- THEN `BrandProfileSchemaValidator` returns a validation error
- AND the task raises a `ValidationError` with the field path and reason
- AND the CLI prints the error and exits with code 1

---

### Requirement: `daf generate` CLI Command

The `daf generate` command MUST load a raw `brand-profile.json`, invoke Agent 1, and run the Human Gate prompt.

#### Acceptance Criteria

- [ ] `daf generate` with no flags loads `brand-profile.json` from the current working directory
- [ ] `daf generate --profile <path>` loads the profile from the specified path
- [ ] `daf generate --yes` skips the Human Gate approval prompt (auto-approves)
- [ ] If `brand-profile.json` does not exist in cwd and `--profile` is not given, the command exits with a clear error message: "No brand-profile.json found. Run `daf init` first."
- [ ] On Agent 1 task failure, the CLI prints structured errors and exits with code 1
- [ ] On successful Agent 1 completion (before gate), the enriched profile is not written until gate approval
- [ ] On gate approval, final `brand-profile.json` is written and CLI prints: "Brand profile approved. Run `daf generate` to start generation." (pipeline trigger deferred to P06)
- [ ] On gate rejection, CLI exits with code 1 and prints: "Profile rejected. Edit your answers and re-run `daf init`."

#### Scenario: Successful generate with gate approval

- GIVEN a valid `brand-profile.json` in the current directory
- WHEN `daf generate` is run
- THEN Agent 1 enriches the profile and prints a formatted summary
- AND the CLI prompts: "Approve this brand profile and start generation? [y/N]"
- WHEN the user types `y`
- THEN the enriched `brand-profile.json` is written
- AND the CLI prints a confirmation message and exits with code 0

#### Scenario: Non-interactive mode with --yes flag

- GIVEN a valid `brand-profile.json` and the `--yes` flag
- WHEN `daf generate --yes` is run
- THEN Agent 1 enriches the profile
- AND the enriched profile is written without prompting
- AND the CLI exits with code 0

#### Scenario: Missing profile file

- GIVEN no `brand-profile.json` in the current directory and no `--profile` flag
- WHEN `daf generate` is run
- THEN the CLI prints: "No brand-profile.json found. Run `daf init` first."
- AND the CLI exits with code 1

---

### Requirement: Human Gate 1 — Brand Profile Approval

The Human Gate (§5, Gate 1) MUST present the enriched profile as a human-readable summary and require explicit approval before proceeding.

#### Acceptance Criteria

- [ ] Gate displays: project name, archetype, all color values (with hex where available), typography summary, spacing density, component scope, accessibility level, themes, and any consistency warnings
- [ ] Gate clearly marks which fields were filled by archetype defaults vs. specified by the user
- [ ] Gate shows any `warning`-severity consistency findings
- [ ] Gate prompt requires explicit `y` input to approve; any other input (including Enter) is treated as rejection
- [ ] On approval: final `brand-profile.json` is written; pipeline is not yet triggered (P06 concern)
- [ ] On rejection: no file is written; CLI exits code 1 with guidance

#### Scenario: Gate shows filled-vs-specified distinction

- GIVEN an enriched profile where `componentScope` was filled from archetype defaults and `colors.primary` was user-specified
- WHEN the Human Gate displays the summary
- THEN `componentScope` is shown with a `(default)` label
- AND `colors.primary` is shown with a `(specified)` label

#### Scenario: Gate shows consistency warnings

- GIVEN an enriched profile with one warning: "Mobile-first with comprehensive scope"
- WHEN the Human Gate displays the summary
- THEN the warning is shown in the summary under a "Warnings" section
- AND the user can still approve despite warnings
