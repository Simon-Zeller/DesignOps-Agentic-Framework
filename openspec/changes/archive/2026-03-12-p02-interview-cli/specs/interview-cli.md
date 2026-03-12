# Specification

## Purpose

This spec defines the behavioral requirements for the P02 Interview CLI — the 11-step brand interview that collects user input and produces a raw `brand-profile.json`. This is the sole user-facing entry point to the DAF pipeline (§13) and the only interactive component before autonomous generation begins.

The output of this interview is consumed exclusively by DS Bootstrap Crew / Agent 1 (Brand Discovery Agent) as its raw input.

---

## Requirements

### Requirement: Interactive Interview Flow

The `daf init` command MUST present an 11-step sequential interview in the terminal. Steps 1–2 are required. Steps 3–11 MUST display an archetype-derived default and allow the user to accept (Enter) or override.

#### Acceptance Criteria

- [ ] Running `daf init` presents exactly 11 prompts in sequence (steps 1–11 per §13.2)
- [ ] Steps 3–11 display the archetype-derived default value before prompting
- [ ] Pressing Enter without input on steps 3–11 accepts the displayed default
- [ ] All 5 archetypes (`enterprise-b2b`, `consumer-b2c`, `mobile-first`, `multi-brand`, `custom`) are presented as selectable options at step 2
- [ ] Multi-choice prompts (archetype, density, radius, themes, scope) use an enumerated selection format, not free text

#### Scenario: Happy path — full interview

- GIVEN the user is in a directory without an existing `.daf-session.json`
- WHEN the user runs `daf init` and answers all 11 steps
- THEN the CLI presents each step in sequence
- AND each optional step shows the archetype-derived default
- AND pressing Enter accepts the default without error
- AND `brand-profile.json` is written after step 11

#### Scenario: Accept all defaults

- GIVEN the user selects archetype "enterprise-b2b" at step 2
- WHEN the user presses Enter for all subsequent optional steps (3–11)
- THEN each field is populated with the enterprise-b2b archetype defaults
- AND `brand-profile.json` is written with a valid, complete profile

#### Scenario: Override a default

- GIVEN the user selects archetype "consumer-b2c" at step 2
- WHEN the user types a custom primary color `#E91E63` at step 3
- THEN the profile's `colors.primary` is set to `"#E91E63"` (not the b2c default)
- AND all other fields retain their consumer-b2c defaults

---

### Requirement: Session Persistence and Resume

The CLI MUST write a `.daf-session.json` file after each completed step. If the process is interrupted, re-running `daf init` in the same directory MUST offer resume from the last completed step.

#### Acceptance Criteria

- [ ] `.daf-session.json` is written to `cwd` after each step completes
- [ ] `.daf-session.json` contains all answers collected so far plus the last completed step number
- [ ] Running `daf init` when `.daf-session.json` exists asks: "Resume from step N (y) or start over (n)?"
- [ ] Choosing resume skips already-answered steps and continues from step N+1
- [ ] Choosing start over deletes `.daf-session.json` and begins from step 1
- [ ] `.daf-session.json` is deleted after `brand-profile.json` is successfully written

#### Scenario: Resume after interruption

- GIVEN the user completed steps 1–5 and the process was interrupted
- WHEN the user runs `daf init` again in the same directory
- THEN the CLI detects `.daf-session.json` and prompts to resume or restart
- AND choosing resume continues from step 6 with steps 1–5 already populated

#### Scenario: Start over after interruption

- GIVEN `.daf-session.json` exists from a prior interrupted session
- WHEN the user runs `daf init` and chooses to start over
- THEN `.daf-session.json` is deleted
- AND the interview begins fresh from step 1

#### Scenario: Successful completion deletes session file

- GIVEN the user completes all 11 steps and `brand-profile.json` is written
- THEN `.daf-session.json` is deleted from the current directory
- AND only `brand-profile.json` remains

---

### Requirement: Structural Validation

The CLI MUST validate the assembled profile against the §13.3 structural rules before writing `brand-profile.json`. Field-level errors MUST cause re-prompting of the failing field in interactive mode.

#### Acceptance Criteria

- [ ] Step 1 (project name) cannot be empty; the CLI re-prompts until a non-empty string is entered
- [ ] Hex color values satisfy `/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/`; invalid values cause re-prompt
- [ ] `typography.scaleRatio` must be a number between 1.0 and 2.0 inclusive; out-of-range values cause re-prompt
- [ ] `typography.baseSize` must be an integer between 8 and 24 inclusive; out-of-range values cause re-prompt
- [ ] Natural language color descriptions (non-hex strings) are stored verbatim without error
- [ ] `archetype` must be one of the defined enum values; selection UI prevents invalid values

#### Scenario: Invalid hex color

- GIVEN the user is at step 3 (colors)
- WHEN the user enters `#ZZZZZZ` as the primary color
- THEN the CLI prints a validation error: "Invalid hex color — must be 3 or 6 hex digits (e.g., #FF0000)"
- AND re-prompts for the primary color without advancing to the next field

#### Scenario: Natural language color accepted

- GIVEN the user is at step 3 (colors)
- WHEN the user enters `"a warm coral red"` as the primary color
- THEN no validation error is raised
- AND `brand-profile.json` contains `"primary": "a warm coral red"`
- AND resolution to hex is deferred to DS Bootstrap Crew / Agent 1 (Brand Discovery Agent)

#### Scenario: Scale ratio out of bounds

- GIVEN the user is at step 4 (typography)
- WHEN the user enters `3.5` as the scale ratio
- THEN the CLI prints: "Scale ratio must be between 1.0 and 2.0"
- AND re-prompts for the scale ratio

#### Scenario: Required field empty

- GIVEN the user is at step 1 (project name)
- WHEN the user presses Enter without typing anything
- THEN the CLI prints: "Project name is required"
- AND re-prompts for the project name

---

### Requirement: Output — `brand-profile.json`

The CLI MUST write a single file `brand-profile.json` in the current working directory, conforming to the §6 schema.

#### Acceptance Criteria

- [ ] `brand-profile.json` is written to `Path.cwd() / "brand-profile.json"` after step 11 passes validation
- [ ] The file is valid JSON (parseable by `json.loads`)
- [ ] All required §6 top-level fields are present: `name`, `archetype`, `colors`, `typography`, `spacing`, `borderRadius`, `elevation`, `motion`, `themes`, `accessibility`, `componentScope`, `breakpoints`
- [ ] The file is pretty-printed (indent=2) for human readability
- [ ] A success message is printed: path to `brand-profile.json` and instruction to run the next stage

#### Scenario: Successful write

- GIVEN the user completes all 11 steps without error
- WHEN the interview finishes
- THEN `brand-profile.json` is written to the current directory
- AND the CLI prints: "Brand profile written to ./brand-profile.json"
- AND exits with code 0

#### Scenario: Write to existing file

- GIVEN `brand-profile.json` already exists in the current directory
- WHEN the interview completes
- THEN the existing file is overwritten (no confirmation prompt — last run wins)
- AND exits with code 0

---

### Requirement: Non-interactive Mode (`--profile`)

`daf init --profile <path>` MUST skip the interview, load the provided file, apply structural validation, and exit cleanly. Full semantic validation is deferred to DS Bootstrap Crew / Agent 1.

#### Acceptance Criteria

- [ ] `daf init --profile ./my-profile.json` loads the file and applies §13.3 structural validation
- [ ] If the file does not exist, the CLI exits with code 1 and prints a clear error
- [ ] If the file fails structural validation, the CLI exits with code 1 and prints each failing field
- [ ] If the file passes validation, the CLI prints a confirmation and exits with code 0
- [ ] The file is NOT written or mutated — `--profile` is read-only passthrough
- [ ] No `.daf-session.json` is created in `--profile` mode

#### Scenario: Valid profile file

- GIVEN a valid `brand-profile.json` conforming to §6
- WHEN the user runs `daf init --profile ./brand-profile.json`
- THEN the CLI loads the file, validates it structurally, prints "Profile loaded: ./brand-profile.json"
- AND exits with code 0

#### Scenario: File not found

- GIVEN the path `./missing.json` does not exist
- WHEN the user runs `daf init --profile ./missing.json`
- THEN the CLI prints "Error: file not found: ./missing.json"
- AND exits with code 1

#### Scenario: File fails structural validation

- GIVEN a JSON file with `"archetype": "invalid-type"`
- WHEN the user runs `daf init --profile ./bad-profile.json`
- THEN the CLI prints: "Validation error: archetype must be one of [enterprise-b2b, consumer-b2c, mobile-first, multi-brand, custom]"
- AND exits with code 1

---

### Requirement: Step 11 — Component Overrides (Advanced)

Step 11 MUST offer component override entry without requiring inline field-by-field prompting. If the user opts in, the CLI SHOULD open `$EDITOR` with a pre-populated JSON template. If unavailable, the step MUST be skippable without error.

#### Acceptance Criteria

- [ ] Step 11 asks: "Add component overrides? (y/N)" — default is N
- [ ] Accepting the default (N / Enter) skips component overrides; `componentOverrides` is omitted from `brand-profile.json`
- [ ] If the user types `y` and `$EDITOR` is set, the editor opens with a JSON template pre-populated with example overrides
- [ ] If the user saves valid JSON and closes the editor, `componentOverrides` is parsed and added to the profile
- [ ] If the user saves invalid JSON, the CLI prints a warning and skips overrides (does not crash)
- [ ] If `$EDITOR` is not set, the CLI prints: "No editor configured (set $EDITOR to add overrides)" and skips component overrides

#### Scenario: Skip overrides (default)

- GIVEN the user is at step 11
- WHEN the user presses Enter (accepting "N")
- THEN no `componentOverrides` key is added to `brand-profile.json`
- AND the interview proceeds to write the output file

#### Scenario: Editor not available

- GIVEN `$EDITOR` is not set in the environment
- WHEN the user types `y` at step 11
- THEN the CLI prints: "No editor configured (set $EDITOR to add overrides). Skipping component overrides."
- AND the interview proceeds without `componentOverrides`
