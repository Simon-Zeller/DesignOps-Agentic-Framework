# TDD Plan: p03-brand-discovery-agent

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

This change introduces one CrewAI Agent, four deterministic tools, one Pydantic model, and one CLI command. Tests are written in **pytest**.

Three test types are used:

1. **Unit tests** — each tool is tested in isolation without a live LLM; the agent is tested by mocking the CrewAI LLM call and verifying tool orchestration
2. **Integration tests** — test the full Agent 1 task with a live Anthropic API call; gated behind `@pytest.mark.integration` and excluded from the default test run
3. **CLI tests** — test `daf generate` via Typer's `CliRunner` and `tmp_path` fixtures, verifying full end-to-end behavior including the Human Gate prompt

Coverage target: ≥80% line coverage, ≥70% branch coverage per PRD quality gate.

All tests live in `tests/test_brand_discovery_agent.py` unless otherwise noted.

---

## Test Cases

### BrandProfileSchemaValidator

#### Test: Valid minimal profile (name + archetype only) passes

- **Maps to:** Requirement "Brand Profile Schema Validation" → Scenario "Valid minimal profile passes validation"
- **Type:** unit
- **Given:** `{"name": "Acme", "archetype": "enterprise-b2b"}`
- **When:** `BrandProfileSchemaValidator().run(profile)` is called
- **Then:** returns `{"valid": True, "errors": []}`
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: Missing name field returns structured error

- **Maps to:** Requirement "Brand Profile Schema Validation" → Scenario "Missing required field fails validation"
- **Type:** unit
- **Given:** `{"archetype": "consumer-b2c"}` (no `name`)
- **When:** `BrandProfileSchemaValidator().run(profile)` is called
- **Then:** returns `{"valid": False, "errors": [{"field": "name", "message": ...}]}`
- AND the error message mentions `"name"`
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: Invalid archetype value is rejected

- **Maps to:** Requirement "Brand Profile Schema Validation" → Acceptance criteria
- **Type:** unit — parametrized over: `"b2b"`, `"ENTERPRISE"`, `""`, `"unknown"`
- **Given:** `{"name": "X", "archetype": <invalid>}`
- **When:** `BrandProfileSchemaValidator().run(profile)` is called
- **Then:** `errors` list contains an entry for field `"archetype"`
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: Invalid hex color is rejected (parametrized)

- **Maps to:** Requirement "Brand Profile Schema Validation" → Scenario "Invalid hex color value"
- **Type:** unit — parametrized over: `"zz9900"`, `"rgb(0,0,255)"`, `"red"`, `"#12345"`, `"#GGGGGG"`
- **Given:** `{"name": "X", "archetype": "enterprise-b2b", "colors": {"primary": <invalid>}}`
- **When:** `BrandProfileSchemaValidator().run(profile)` is called
- **Then:** `errors` contains an entry for `"colors.primary"`
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: Natural language color string passes validation

- **Maps to:** Requirement "Brand Profile Schema Validation" → Scenario "Natural language color description is allowed"
- **Type:** unit
- **Given:** `{"name": "X", "archetype": "enterprise-b2b", "colors": {"primary": "a warm corporate red"}}`
- **When:** `BrandProfileSchemaValidator().run(profile)` is called
- **Then:** `errors` is empty (natural language strings are valid)
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: scaleRatio outside [1.0, 2.0] is rejected (parametrized)

- **Maps to:** Requirement "Brand Profile Schema Validation" → Acceptance criteria
- **Type:** unit — parametrized over: `0.9`, `0.0`, `2.1`, `3.5`, `-1.0`
- **Given:** a profile with `typography.scaleRatio` set to each out-of-bounds value
- **When:** `BrandProfileSchemaValidator().run(profile)` is called
- **Then:** `errors` contains an entry for `"typography.scaleRatio"`
- **File:** `tests/test_brand_discovery_agent.py`

---

### ArchetypeResolver

#### Test: All five archetypes return complete defaults dicts

- **Maps to:** Requirement "Archetype Default Resolution" → Acceptance criteria
- **Type:** unit — parametrized over all 5 archetype values
- **Given:** archetype string as input
- **When:** `ArchetypeResolver().run(archetype)` is called
- **Then:** returned dict has non-None values for all optional §6 fields: `colors`, `typography`, `spacing`, `borderRadius`, `elevation`, `motion`, `themes`, `accessibility`, `componentScope`, `breakpoints`
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: enterprise-b2b defaults are AA, dense, comprehensive

- **Maps to:** Requirement "Archetype Default Resolution" → Scenario "Enterprise archetype defaults fill all optional fields"
- **Type:** unit
- **Given:** `archetype = "enterprise-b2b"`
- **When:** `ArchetypeResolver().run(archetype)` is called
- **Then:** `result["accessibility"] == "AA"`, `result["componentScope"] == "comprehensive"`, `result["spacing"]["density"] == "compact"`, `result["borderRadius"] == "subtle"`
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: mobile-first defaults are AAA, starter, compact, mobile-first strategy

- **Maps to:** Requirement "Archetype Default Resolution" → Scenario "Mobile-first archetype sets AAA accessibility and starter scope"
- **Type:** unit
- **Given:** `archetype = "mobile-first"`
- **When:** `ArchetypeResolver().run(archetype)` is called
- **Then:** `result["accessibility"] == "AAA"`, `result["componentScope"] == "starter"`, `result["spacing"]["density"] == "compact"`, `result["breakpoints"]["strategy"] == "mobile-first"`
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: multi-brand defaults enable brandOverrides and all themes

- **Maps to:** Requirement "Archetype Default Resolution" → Scenario "Multi-brand archetype enables brand overrides"
- **Type:** unit
- **Given:** `archetype = "multi-brand"`
- **When:** `ArchetypeResolver().run(archetype)` is called
- **Then:** `result["themes"]["brandOverrides"] == True` and `"light"`, `"dark"`, `"high-contrast"` are all in `result["themes"]["modes"]`
- **File:** `tests/test_brand_discovery_agent.py`

---

### ConsistencyChecker

#### Test: Consistent profile returns empty findings list

- **Maps to:** Requirement "Consistency Checking" → Scenario "Valid consistent profile returns no findings"
- **Type:** unit
- **Given:** `{"archetype": "enterprise-b2b", "spacing": {"density": "compact", "baseUnit": 4}, "componentScope": "comprehensive", "accessibility": "AA"}`
- **When:** `ConsistencyChecker().run(profile)` is called
- **Then:** returns `[]`
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: Compact density with large base unit is caught as error

- **Maps to:** Requirement "Consistency Checking" → Scenario "Density contradiction is caught as error"
- **Type:** unit
- **Given:** `{"spacing": {"density": "compact", "baseUnit": 16}, ...}`
- **When:** `ConsistencyChecker().run(profile)` is called
- **Then:** returns a list containing `{"field": "spacing", "severity": "error", "message": ...}`
- AND `severity` is `"error"` (not `"warning"`)
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: mobile-first with comprehensive scope is a warning, not error

- **Maps to:** Requirement "Consistency Checking" → Scenario "Warning-level contradiction is preserved but allowed"
- **Type:** unit
- **Given:** `{"archetype": "mobile-first", "componentScope": "comprehensive", ...}`
- **When:** `ConsistencyChecker().run(profile)` is called
- **Then:** returns a list containing a finding with `"severity": "warning"` for `"componentScope"`
- AND no finding has `"severity": "error"`
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: multi-brand with brandOverrides false is a warning

- **Maps to:** Requirement "Consistency Checking" → Acceptance criteria
- **Type:** unit
- **Given:** `{"archetype": "multi-brand", "themes": {"brandOverrides": False}, ...}`
- **When:** `ConsistencyChecker().run(profile)` is called
- **Then:** returns a warning-severity finding for `"themes.brandOverrides"`
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: motion expressive with AAA accessibility is a warning

- **Maps to:** Requirement "Consistency Checking" → Acceptance criteria
- **Type:** unit
- **Given:** `{"motion": "expressive", "accessibility": "AAA", ...}`
- **When:** `ConsistencyChecker().run(profile)` is called
- **Then:** returns a warning-severity finding for `"motion"`
- **File:** `tests/test_brand_discovery_agent.py`

---

### DefaultFiller

#### Test: User-specified values are never overridden

- **Maps to:** Requirement "Default Filling" → Scenario "User-specified values are preserved"
- **Type:** unit
- **Given:** `profile = {"name": "Acme", "archetype": "enterprise-b2b", "colors": {"primary": "#1a73e8"}, "accessibility": "AAA"}` and enterprise defaults where `accessibility = "AA"`
- **When:** `DefaultFiller().run(profile, archetype_defaults)` is called
- **Then:** `result["colors"]["primary"] == "#1a73e8"` and `result["accessibility"] == "AAA"`
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: Minimal profile gains all optional fields

- **Maps to:** Requirement "Default Filling" → Scenario "All optional fields are filled for minimal profile"
- **Type:** unit
- **Given:** `{"name": "Acme", "archetype": "consumer-b2c"}` and consumer-b2c defaults
- **When:** `DefaultFiller().run(profile, archetype_defaults)` is called
- **Then:** the returned profile contains all §6 optional fields with non-None values
- AND `result["_filled_fields"]` is a non-empty list containing the names of all filled fields
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: _filled_fields annotation tracks what was defaulted

- **Maps to:** Requirement "Default Filling" → Acceptance criteria
- **Type:** unit
- **Given:** profile with `archetype` and `name` only
- **When:** `DefaultFiller().run(profile, archetype_defaults)` is called
- **Then:** `result["_filled_fields"]` includes `"spacing.density"`, `"componentScope"`, and other omitted fields
- AND does NOT include `"name"` or `"archetype"` (user-specified)
- **File:** `tests/test_brand_discovery_agent.py`

---

### BrandProfile Pydantic Model

#### Test: Valid complete profile constructs successfully

- **Maps to:** Requirement "Brand Discovery Agent (Agent 1) — Task T1" → Acceptance criteria
- **Type:** unit
- **Given:** a dict with all §6 fields populated
- **When:** `BrandProfile(**data)` is instantiated
- **Then:** no ValidationError is raised
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: Extra fields beyond §6 schema are stripped

- **Maps to:** Requirement "Brand Discovery Agent (Agent 1) — Task T1" → Acceptance criteria
- **Type:** unit
- **Given:** a dict conforming to §6 plus extra keys `{"_internal_note": "...", "hallucinated_field": 42}`
- **When:** `BrandProfile(**data)` is instantiated
- **Then:** the model instance does not have `_internal_note` or `hallucinated_field` attributes
- **File:** `tests/test_brand_discovery_agent.py`

---

### `daf generate` CLI Command

#### Test: Missing brand-profile.json exits with code 1 and clear error

- **Maps to:** Requirement "`daf generate` CLI Command" → Scenario "Missing profile file"
- **Type:** unit (CLI)
- **Given:** a `tmp_path` directory with no `brand-profile.json`
- **When:** `runner.invoke(app, ["generate"])` is called from `tmp_path`
- **Then:** exit code is 1 and output contains `"No brand-profile.json found"`
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: --profile flag loads from specified path

- **Maps to:** Requirement "`daf generate` CLI Command" → Acceptance criteria
- **Type:** unit (CLI, mocked agent)
- **Given:** a valid `brand-profile.json` at a custom path; agent task is mocked to return a valid `BrandProfile`
- **When:** `runner.invoke(app, ["generate", "--profile", str(profile_path)])` is called
- **Then:** exit code is 0 (with `--yes`) and the enriched profile is written
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: --yes flag skips Human Gate prompt

- **Maps to:** Requirement "`daf generate` CLI Command" → Scenario "Non-interactive mode with --yes flag"
- **Type:** unit (CLI, mocked agent)
- **Given:** a valid `brand-profile.json`; agent task is mocked to return a valid `BrandProfile`
- **When:** `runner.invoke(app, ["generate", "--yes"])` is called
- **Then:** no prompt is shown, exit code is 0, `brand-profile.json` is written
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: Human Gate approval (y) writes final profile

- **Maps to:** Requirement "`daf generate` CLI Command" → Scenario "Successful generate with gate approval"
- **Type:** unit (CLI, mocked agent)
- **Given:** a valid `brand-profile.json`; agent task is mocked to return a valid `BrandProfile`
- **When:** `runner.invoke(app, ["generate"], input="y\n")` is called
- **Then:** exit code is 0, `brand-profile.json` is written with the enriched content, output contains confirmation message
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: Human Gate rejection (N) does not write profile

- **Maps to:** Requirement "`daf generate` CLI Command" → Acceptance criteria
- **Type:** unit (CLI, mocked agent)
- **Given:** a valid `brand-profile.json`; agent task is mocked to return a valid `BrandProfile`
- **When:** `runner.invoke(app, ["generate"], input="N\n")` is called
- **Then:** exit code is 1, no `brand-profile.json` is written, output contains rejection guidance
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: Enter (empty input) at Human Gate is treated as rejection

- **Maps to:** Requirement "Human Gate 1 — Brand Profile Approval" → Acceptance criteria
- **Type:** unit (CLI, mocked agent)
- **Given:** a valid mocked agent response
- **When:** `runner.invoke(app, ["generate"], input="\n")` is called
- **Then:** exit code is 1 (Enter = no = rejection)
- **File:** `tests/test_brand_discovery_agent.py`

---

### Human Gate Summary Display

#### Test: Gate shows (default) vs (specified) labels

- **Maps to:** Requirement "Human Gate 1 — Brand Profile Approval" → Scenario "Gate shows filled-vs-specified distinction"
- **Type:** unit (CLI, mocked agent)
- **Given:** enriched profile with `_filled_fields: ["componentScope"]` and user-specified `colors.primary`
- **When:** Human Gate summary is rendered
- **Then:** output contains `"componentScope"` with `"(default)"` label and `"colors.primary"` without `"(default)"` label
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: Gate shows consistency warnings when present

- **Maps to:** Requirement "Human Gate 1 — Brand Profile Approval" → Scenario "Gate shows consistency warnings"
- **Type:** unit (CLI, mocked agent)
- **Given:** enriched profile with `_warnings: ["Mobile-first with comprehensive scope is unusual"]`
- **When:** Human Gate summary is rendered
- **Then:** output contains a `"Warnings"` section and the warning message
- **File:** `tests/test_brand_discovery_agent.py`

---

### Integration Tests (LLM-gated)

#### Test: Full Agent 1 task enriches a valid minimal profile

- **Maps to:** Requirement "Brand Discovery Agent (Agent 1) — Task T1" → Scenario "Full enrichment flow — happy path"
- **Type:** integration (`@pytest.mark.integration`)
- **Given:** `{"name": "Acme Corp", "archetype": "enterprise-b2b", "colors": {"primary": "#003366"}}`
- **When:** `BrandDiscoveryAgent` Task T1 is run with a live Anthropic API call
- **Then:** returned `BrandProfile` has all §6 fields populated
- AND `accessibility == "AA"` (enterprise default)
- AND `componentScope == "comprehensive"` (enterprise default)
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: Agent annotates natural language color description

- **Maps to:** Requirement "Brand Discovery Agent (Agent 1) — Task T1" → Scenario "LLM color annotation for natural language input"
- **Type:** integration (`@pytest.mark.integration`)
- **Given:** a profile with `colors.primary: "a deep ocean blue"`
- **When:** Agent 1 Task T1 runs
- **Then:** the returned profile or annotations contain a note about the natural language color interpretation
- AND `colors.primary` is preserved as `"a deep ocean blue"` (not replaced with a hex value)
- **File:** `tests/test_brand_discovery_agent.py`

---

## Edge Case Tests

#### Test: Unknown archetype value is caught by schema validator

- **Maps to:** Requirement "Brand Profile Schema Validation" → Acceptance criteria
- **Type:** unit
- **Given:** `{"name": "X", "archetype": "startup"}`
- **When:** `BrandProfileSchemaValidator().run(profile)` is called
- **Then:** returns an error for `"archetype"` field
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: Empty profile dict is rejected with multiple required-field errors

- **Maps to:** Requirement "Brand Profile Schema Validation" → Acceptance criteria
- **Type:** unit
- **Given:** `{}`
- **When:** `BrandProfileSchemaValidator().run(profile)` is called
- **Then:** errors list contains entries for both `"name"` and `"archetype"`
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: DefaultFiller with custom archetype uses universal baseline

- **Maps to:** Requirement "Archetype Default Resolution" → Acceptance criteria
- **Type:** unit
- **Given:** `{"name": "X", "archetype": "custom"}` — no optional fields
- **When:** `ArchetypeResolver` then `DefaultFiller` run in sequence
- **Then:** all optional fields are filled with the custom universal baseline values
- AND the result is a complete, non-null profile
- **File:** `tests/test_brand_discovery_agent.py`

#### Test: ConsistencyChecker with fully consistent multi-brand profile returns no findings

- **Maps to:** Requirement "Consistency Checking" → Scenario "Valid consistent profile returns no findings"
- **Type:** unit
- **Given:** a multi-brand profile with `themes.brandOverrides: True` and all other fields consistent
- **When:** `ConsistencyChecker().run(profile)` is called
- **Then:** returns `[]`
- **File:** `tests/test_brand_discovery_agent.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------| 
| Line coverage | ≥80% | PRD quality gate requirement |
| Branch coverage | ≥70% | Covers conditional logic in ConsistencyChecker predicate list |
| Tool unit tests | 100% of tools covered | All 4 tools have happy path + error case tests |
| CLI command paths | 100% of branches | Approval, rejection, --yes, --profile, missing file |

Integration tests (`@pytest.mark.integration`) are excluded from coverage measurement in CI — they require a live Anthropic API key and are run manually or in a dedicated integration suite.

---

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_brand_discovery_agent.py` | new | All unit and integration tests for Agent 1, four tools, Pydantic model, `daf generate` CLI, and Human Gate |
