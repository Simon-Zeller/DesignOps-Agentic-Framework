# TDD Plan: p02-interview-cli

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

This proposal is pure Python CLI logic — no CrewAI agents, no LLM calls. Tests use **pytest** with Click's `CliRunner` (via Typer's test utilities) for unit tests and temporary directories (`tmp_path`) for file I/O tests. No subprocess overhead required.

Three test types are used:

1. **Unit tests** — test individual modules (`validator.py`, `session.py`, `archetypes.py`, `interview.py`) in isolation
2. **Integration tests** — invoke the full `daf init` command via Typer's `CliRunner`, exercising the full path from CLI to file write
3. **Parametrized boundary tests** — cover the full §13.3 validation rule set in a single parametrized test function

Coverage target: ≥80% line coverage, ≥70% branch coverage per PRD quality gate.

---

## Test Cases

### Archetype Defaults

#### Test: All 5 archetypes have complete defaults

- **Maps to:** Requirement "Interactive Interview Flow" → Scenario "Accept all defaults"
- **Type:** unit
- **Given:** `ARCHETYPE_DEFAULTS` dict imported from `daf.archetypes`
- **When:** each archetype key is accessed
- **Then:** the returned dict covers all optional §6 fields: `colors`, `typography`, `spacing`, `borderRadius`, `elevation`, `motion`, `themes`, `accessibility`, `componentScope`, `breakpoints`
- **File:** `tests/test_archetypes.py`

#### Test: enterprise-b2b defaults match PRD archetype profile

- **Maps to:** Requirement "Interactive Interview Flow" → Scenario "Accept all defaults"
- **Type:** unit
- **Given:** `ARCHETYPE_DEFAULTS["enterprise-b2b"]`
- **When:** individual fields are read
- **Then:** `accessibility` is `"AA"`, `spacing.density` is `"compact"` or `"default"`, `componentScope` is `"comprehensive"`
- **File:** `tests/test_archetypes.py`

---

### Structural Validator

#### Test: Valid complete profile passes validation

- **Maps to:** Requirement "Structural Validation" → Scenario "Happy path"
- **Type:** unit
- **Given:** a dict conforming to all §6 required fields and §13.3 rules
- **When:** `validate_profile(data)` is called
- **Then:** returns an empty list (no errors)
- **File:** `tests/test_validator.py`

#### Test: Missing required field `name` returns error

- **Maps to:** Requirement "Structural Validation" → Scenario "Required field empty"
- **Type:** unit
- **Given:** a profile dict with `name` set to `""`
- **When:** `validate_profile(data)` is called
- **Then:** the returned list contains an error mentioning `"name"`
- **File:** `tests/test_validator.py`

#### Test: Invalid hex returns error (parametrized)

- **Maps to:** Requirement "Structural Validation" → Scenario "Invalid hex color"
- **Type:** unit — parametrized over: `"#GGGGGG"`, `"#12345"`, `"red"`, `"rgb(255,0,0)"`, `""`
- **Given:** a profile with `colors.primary` set to each invalid value
- **When:** `validate_profile(data)` is called
- **Then:** the returned list contains an error mentioning `"colors.primary"` for each invalid input
- **File:** `tests/test_validator.py`

#### Test: Natural language color description passes validation

- **Maps to:** Requirement "Structural Validation" → Scenario "Natural language color accepted"
- **Type:** unit
- **Given:** a profile with `colors.primary` set to `"a warm coral red"`
- **When:** `validate_profile(data)` is called
- **Then:** no error is returned for `colors.primary`
- **File:** `tests/test_validator.py`

#### Test: Valid 6-digit and 3-digit hex values pass (parametrized)

- **Maps to:** Requirement "Structural Validation" → Scenario "Invalid hex color" (inverse)
- **Type:** unit — parametrized over: `"#1a73e8"`, `"#FF0000"`, `"#fff"`, `"#000"`, `"#ABC"`
- **Given:** a profile with `colors.primary` set to each valid hex value
- **When:** `validate_profile(data)` is called
- **Then:** no error is returned for `colors.primary`
- **File:** `tests/test_validator.py`

#### Test: Scale ratio 1.0 and 2.0 are valid boundaries

- **Maps to:** Requirement "Structural Validation" → Scenario "Scale ratio out of bounds" (inverse)
- **Type:** unit — parametrized over: `1.0`, `1.25`, `1.5`, `2.0`
- **Given:** a profile with `typography.scaleRatio` set to each value
- **When:** `validate_profile(data)` is called
- **Then:** no error is returned for `typography.scaleRatio`
- **File:** `tests/test_validator.py`

#### Test: Scale ratio outside [1.0, 2.0] returns error (parametrized)

- **Maps to:** Requirement "Structural Validation" → Scenario "Scale ratio out of bounds"
- **Type:** unit — parametrized over: `0.9`, `2.1`, `0.0`, `-1.0`, `5.0`
- **Given:** a profile with `typography.scaleRatio` set to each out-of-bounds value
- **When:** `validate_profile(data)` is called
- **Then:** the returned list contains an error mentioning `"scaleRatio"`
- **File:** `tests/test_validator.py`

#### Test: Base size 8 and 24 are valid boundaries

- **Maps to:** Requirement "Structural Validation"
- **Type:** unit — parametrized over: `8`, `12`, `16`, `24`
- **Given:** a profile with `typography.baseSize` set to each value
- **When:** `validate_profile(data)` is called
- **Then:** no error for `typography.baseSize`
- **File:** `tests/test_validator.py`

#### Test: Base size outside [8, 24] returns error (parametrized)

- **Maps to:** Requirement "Structural Validation"
- **Type:** unit — parametrized over: `7`, `25`, `0`, `100`
- **Given:** a profile with `typography.baseSize` set to each invalid value
- **When:** `validate_profile(data)` is called
- **Then:** the returned list contains an error mentioning `"baseSize"`
- **File:** `tests/test_validator.py`

#### Test: Invalid archetype enum returns error

- **Maps to:** Requirement "Structural Validation"
- **Type:** unit
- **Given:** a profile with `archetype` set to `"fantasy-theme"`
- **When:** `validate_profile(data)` is called
- **Then:** the returned list contains an error mentioning `"archetype"`
- **File:** `tests/test_validator.py`

---

### Session Persistence

#### Test: Session is saved after first step

- **Maps to:** Requirement "Session Persistence and Resume" → Scenario "Resume after interruption"
- **Type:** unit
- **Given:** a `SessionManager` instantiated with a `tmp_path` directory
- **When:** `session.save(step=1, answers={"name": "TestDS"})` is called
- **Then:** `.daf-session.json` exists in `tmp_path`
- AND contains `"last_step": 1` and `"answers": {"name": "TestDS"}`
- **File:** `tests/test_session.py`

#### Test: Session load returns saved state

- **Maps to:** Requirement "Session Persistence and Resume" → Scenario "Resume after interruption"
- **Type:** unit
- **Given:** a `.daf-session.json` with `last_step: 5` and partial answers
- **When:** `session.load()` is called
- **Then:** returns the saved state dict with `last_step` and `answers` keys
- **File:** `tests/test_session.py`

#### Test: Session is deleted after successful write

- **Maps to:** Requirement "Session Persistence and Resume" → Scenario "Successful completion deletes session file"
- **Type:** unit
- **Given:** `.daf-session.json` exists in `tmp_path`
- **When:** `session.delete()` is called
- **Then:** `.daf-session.json` no longer exists in `tmp_path`
- **File:** `tests/test_session.py`

#### Test: `session.load()` returns None when no file exists

- **Maps to:** Requirement "Session Persistence and Resume"
- **Type:** unit
- **Given:** no `.daf-session.json` in `tmp_path`
- **When:** `session.load()` is called
- **Then:** returns `None`
- **File:** `tests/test_session.py`

---

### `brand-profile.json` Output

#### Test: Output file is valid JSON with all required fields

- **Maps to:** Requirement "Output — `brand-profile.json`" → Scenario "Successful write"
- **Type:** integration
- **Given:** `CliRunner` with `mix_stderr=False`, `tmp_path` as cwd
- **When:** `daf init` is invoked with simulated inputs for all 11 steps
- **Then:** `brand-profile.json` exists in `tmp_path`
- AND `json.loads(content)` succeeds without error
- AND all required §6 fields are present: `name`, `archetype`, `colors`, `typography`, `spacing`, `borderRadius`, `elevation`, `motion`, `themes`, `accessibility`, `componentScope`, `breakpoints`
- **File:** `tests/test_interview.py`

#### Test: Output file is pretty-printed (indent=2)

- **Maps to:** Requirement "Output — `brand-profile.json`" → Acceptance criteria
- **Type:** integration
- **Given:** a completed interview via CliRunner
- **When:** `brand-profile.json` is read as text
- **Then:** the file contains newlines (multi-line JSON, not single-line)
- **File:** `tests/test_interview.py`

#### Test: Exit code is 0 after successful write

- **Maps to:** Requirement "Output — `brand-profile.json`" → Scenario "Successful write"
- **Type:** integration
- **Given:** CliRunner invoking `daf init` with complete inputs
- **When:** the command completes
- **Then:** exit code is `0`
- AND stdout contains `brand-profile.json`
- **File:** `tests/test_interview.py`

#### Test: Existing `brand-profile.json` is overwritten

- **Maps to:** Requirement "Output — `brand-profile.json`" → Scenario "Write to existing file"
- **Type:** integration
- **Given:** `brand-profile.json` already exists in `tmp_path` with different content
- **When:** `daf init` completes a new interview
- **Then:** `brand-profile.json` reflects the new answers (file is overwritten)
- AND exit code is `0`
- **File:** `tests/test_interview.py`

---

### Non-interactive Mode (`--profile`)

#### Test: Valid profile file exits 0 with confirmation

- **Maps to:** Requirement "Non-interactive Mode (`--profile`)" → Scenario "Valid profile file"
- **Type:** integration
- **Given:** a valid `brand-profile.json` written to `tmp_path`
- **When:** `daf init --profile <path>` is invoked via CliRunner
- **Then:** exit code is `0`
- AND stdout contains the path or "Profile loaded"
- **File:** `tests/test_cli_init.py`

#### Test: Non-existent file exits 1 with error message

- **Maps to:** Requirement "Non-interactive Mode (`--profile`)" → Scenario "File not found"
- **Type:** integration
- **Given:** `./missing.json` does not exist
- **When:** `daf init --profile ./missing.json` is invoked via CliRunner
- **Then:** exit code is `1`
- AND output contains "not found" or "does not exist"
- **File:** `tests/test_cli_init.py`

#### Test: Invalid profile file exits 1 with field-level errors

- **Maps to:** Requirement "Non-interactive Mode (`--profile`)" → Scenario "File fails structural validation"
- **Type:** integration
- **Given:** a JSON file with `"archetype": "invalid-type"` written to `tmp_path`
- **When:** `daf init --profile <path>` is invoked
- **Then:** exit code is `1`
- AND output contains "archetype" in the error message
- **File:** `tests/test_cli_init.py`

#### Test: `--profile` does not create `.daf-session.json`

- **Maps to:** Requirement "Non-interactive Mode (`--profile`)" → Acceptance criteria
- **Type:** integration
- **Given:** a valid profile file in `tmp_path`
- **When:** `daf init --profile <path>` is invoked
- **Then:** `.daf-session.json` is NOT created in `tmp_path`
- **File:** `tests/test_cli_init.py`

---

### Step 11 — Component Overrides

#### Test: Skipping overrides (default N) omits `componentOverrides` from output

- **Maps to:** Requirement "Step 11 — Component Overrides" → Scenario "Skip overrides (default)"
- **Type:** unit
- **Given:** interview state with all steps 1–10 complete, no overrides
- **When:** `build_profile(state)` is called
- **Then:** the returned dict does not contain the `componentOverrides` key
- **File:** `tests/test_interview.py`

#### Test: Missing `$EDITOR` skips overrides without error

- **Maps to:** Requirement "Step 11 — Component Overrides" → Scenario "Editor not available"
- **Type:** unit
- **Given:** environment variable `EDITOR` is not set
- **When:** `collect_overrides()` is called (the step 11 handler)
- **Then:** returns `None` (no overrides)
- AND no exception is raised
- **File:** `tests/test_interview.py`

---

## Edge Case Tests

#### Test: `name` with only whitespace is rejected

- **Maps to:** Requirement "Structural Validation" → Scenario "Required field empty"
- **Type:** unit
- **Given:** a profile with `name` set to `"   "` (whitespace only)
- **When:** `validate_profile(data)` is called
- **Then:** the returned list contains an error for `"name"` (whitespace-only is treated as empty)
- **File:** `tests/test_validator.py`

#### Test: Session save is idempotent (overwrite same step)

- **Maps to:** Requirement "Session Persistence and Resume"
- **Type:** unit
- **Given:** `.daf-session.json` exists with `last_step: 3`
- **When:** `session.save(step=3, answers={"name": "Updated"})` is called again
- **Then:** `.daf-session.json` is overwritten with the new content (no error, no duplicate)
- **File:** `tests/test_session.py`

#### Test: All `colors.*` fields are validated independently

- **Maps to:** Requirement "Structural Validation" — color sub-fields
- **Type:** unit — parametrized over: `colors.secondary`, `colors.neutral`, `colors.semantic.success`, `colors.semantic.warning`, `colors.semantic.error`, `colors.semantic.info`
- **Given:** a profile with the given color field set to `"#INVALID"`
- **When:** `validate_profile(data)` is called
- **Then:** an error is returned for that specific field path
- **File:** `tests/test_validator.py`

#### Test: Session manager uses `cwd` by default

- **Maps to:** Requirement "Session Persistence and Resume"
- **Type:** unit
- **Given:** `SessionManager` instantiated without an explicit path
- **When:** `session.save(...)` is called
- **Then:** `.daf-session.json` is written in the current working directory
- **File:** `tests/test_session.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Line coverage | ≥80% | PRD quality gate requirement (§3.8 `qualityGates.minTestCoverage`) |
| Branch coverage | ≥70% | Covers if/else paths in validator, session resume logic, `--profile` flag routing |
| A11y rules passing | N/A | CLI-only change — no UI component output |

---

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_archetypes.py` | new | Archetype defaults completeness and accuracy |
| `tests/test_validator.py` | new | Full §13.3 validation rule set, parametrized edge cases |
| `tests/test_session.py` | new | `SessionManager` save/load/delete lifecycle, cwd behavior |
| `tests/test_interview.py` | new | Full interview flow via CliRunner, output file assertions, step 11 overrides |
| `tests/test_cli_init.py` | modified | Extend existing stub tests with real `--profile` path validation behavior |
