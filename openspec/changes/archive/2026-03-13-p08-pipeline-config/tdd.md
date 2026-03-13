# TDD Plan: p08-pipeline-config

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

This change introduces two deterministic tool modules and one Agent 5 factory module. Tests are written in **pytest** following the pattern established by p06 and p07.

Three test types are used:

1. **Unit tests** — `generate_pipeline_config()` and `scaffold_project_files()` are tested in isolation using a `tmp_path` fixture; no LLM calls; assertions are structural and value-level
2. **Parametrized tests** — scope tier and a11y level combinations are parametrized to avoid test duplication
3. **Structural tests** — CrewAI tool and agent factory are tested without live API calls; presence of tools, model configuration, task description completeness, and class hierarchy are verified

Integration tests (live Anthropic API) are excluded from the default test run via `@pytest.mark.integration`. Coverage target: ≥80% line coverage, ≥70% branch coverage.

Test files:
- `tests/test_config_generator.py` — `generate_pipeline_config()`, all scope/a11y combinations, schema completeness, model env var resolution, error cases
- `tests/test_project_scaffolder.py` — `scaffold_project_files()`, file presence, content validation, coverage threshold injection, error cases
- `tests/test_pipeline_config_agent.py` — `ConfigGenerator` BaseTool subclass, `ProjectScaffolder` BaseTool subclass, `create_pipeline_config_agent()`, `create_pipeline_config_task()` factories

---

## Test Cases

### ConfigGenerator — schema completeness and field derivation

#### Test: Generated config contains all six top-level keys

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Acceptance criteria (schema completeness)
- **Type:** unit
- **Given:** a minimal valid Brand Profile with `scope: "starter"` and `accessibility.level: "AA"`
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** `pipeline-config.json` is written and contains keys `qualityGates`, `lifecycle`, `domains`, `retry`, `models`, `buildConfig`
- **File:** `tests/test_config_generator.py`

#### Test: AA accessibility → minCompositeScore 70, standard scope → coverage 80

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Scenario "AA accessibility → score 70, standard scope → coverage 80"
- **Type:** unit
- **Given:** Brand Profile with `accessibility.level: "AA"` and `scope: "standard"`
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** `qualityGates.minCompositeScore` is `70`
- AND `qualityGates.minTestCoverage` is `80`
- AND `qualityGates.a11yLevel` is `"AA"`
- **File:** `tests/test_config_generator.py`

#### Test: AAA accessibility → minCompositeScore 85

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Scenario "AAA accessibility → score 85"
- **Type:** unit
- **Given:** Brand Profile with `accessibility.level: "AAA"` and `scope: "starter"`
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** `qualityGates.minCompositeScore` is `85`
- AND `qualityGates.a11yLevel` is `"AAA"`
- **File:** `tests/test_config_generator.py`

#### Test: Comprehensive scope → betaComponents list, wider domains, coverage 75

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Scenario "Comprehensive scope → beta components and wider domain categories"
- **Type:** unit
- **Given:** Brand Profile with `scope: "comprehensive"` and `accessibility.level: "AA"`
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** `lifecycle.betaComponents` equals `["DatePicker", "DataGrid", "TreeView", "Drawer", "Stepper", "FileUpload", "RichText"]`
- AND `domains.categories` contains `"data-entry"`
- AND `domains.categories` contains `"navigation"` and `"data-display"`
- AND `qualityGates.minTestCoverage` is `75`
- **File:** `tests/test_config_generator.py`

#### Test: Starter scope → empty betaComponents, minimal domain categories

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Scenario "Starter scope → empty beta list and minimal domain categories"
- **Type:** unit
- **Given:** Brand Profile with `scope: "starter"`
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** `lifecycle.betaComponents` is `[]`
- AND `"navigation"` is NOT in `domains.categories`
- AND `"data-entry"` is NOT in `domains.categories`
- AND `"forms"`, `"layout"`, `"feedback"` ARE in `domains.categories`
- **File:** `tests/test_config_generator.py`

#### Test: Fixed fields always have correct defaults

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Acceptance criteria (fixed defaults)
- **Type:** unit
- **Given:** any valid Brand Profile
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** `qualityGates.blockOnWarnings` is `False`
- AND `lifecycle.defaultStatus` is `"stable"`
- AND `lifecycle.deprecationGracePeriodDays` is `90`
- AND `domains.autoAssign` is `True`
- AND `retry.maxComponentRetries` is `3`
- AND `retry.maxCrewRetries` is `2`
- AND `buildConfig.tsTarget` is `"ES2020"`
- AND `buildConfig.moduleFormat` is `"ESNext"`
- AND `buildConfig.cssModules` is `False`
- **File:** `tests/test_config_generator.py`

#### Test: Model identifiers resolved from environment variables

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Scenario "Model identifiers from environment variables"
- **Type:** unit
- **Given:** `DAF_TIER1_MODEL=claude-opus-4-custom` is set; `DAF_TIER2_MODEL` and `DAF_TIER3_MODEL` are unset
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** `models.tier1` is `"claude-opus-4-custom"`
- AND `models.tier2` is `"claude-sonnet-4-20250514"`
- AND `models.tier3` is `"claude-haiku-4-20250414"`
- **File:** `tests/test_config_generator.py`

#### Test: Output is valid JSON

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Acceptance criteria (file validity)
- **Type:** unit
- **Given:** any valid Brand Profile
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** the written file can be parsed with `json.loads()` without error
- **File:** `tests/test_config_generator.py`

#### Test: Function returns absolute path to written file

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Acceptance criteria (return type)
- **Type:** unit
- **Given:** any valid Brand Profile and a `tmp_path`
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** the return value is a string
- AND the path exists on disk
- AND the path is absolute
- **File:** `tests/test_config_generator.py`

#### Test: Idempotent — second call overwrites without error

- **Maps to:** Requirement "Retry and idempotency safety" → Scenario "Idempotent re-run produces identical output"
- **Type:** unit
- **Given:** `generate_pipeline_config` has already been called once
- **When:** `generate_pipeline_config` is called again with identical arguments
- **Then:** no exception is raised
- AND the written file has the same contents as after the first call
- **File:** `tests/test_config_generator.py`

---

### ConfigGenerator — error cases

#### Test: Missing accessibility key raises error

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Scenario "Missing Brand Profile fields cause ValueError"
- **Type:** unit
- **Given:** a Brand Profile dict missing the `accessibility` key
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** `KeyError` or `ValueError` is raised
- **File:** `tests/test_config_generator.py`

#### Test: Missing scope key raises error

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Scenario "Missing Brand Profile fields cause ValueError"
- **Type:** unit
- **Given:** a Brand Profile dict missing the `scope` key
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** `KeyError` or `ValueError` is raised
- **File:** `tests/test_config_generator.py`

---

### ProjectScaffolder — file presence and content

#### Test: All three scaffolding files are written

- **Maps to:** Requirement "Project scaffolding files are valid and well-formed" → Scenario "Scaffolding files are written correctly"
- **Type:** unit
- **Given:** `pipeline-config.json` exists in `tmp_path` (written by `generate_pipeline_config`)
- **When:** `scaffold_project_files(brand_profile, str(tmp_path))` is called
- **Then:** `tsconfig.json` exists in `tmp_path`
- AND `vitest.config.ts` exists in `tmp_path`
- AND `vite.config.ts` exists in `tmp_path`
- AND the returned dict has exactly 3 keys: `"tsconfig.json"`, `"vitest.config.ts"`, `"vite.config.ts"`
- **File:** `tests/test_project_scaffolder.py`

#### Test: tsconfig.json contains required compiler options

- **Maps to:** Requirement "Project scaffolding files are valid and well-formed" → Acceptance criteria (tsconfig.json)
- **Type:** unit
- **Given:** scaffolding files have been written
- **When:** `tsconfig.json` is parsed with `json.loads()`
- **Then:** `compilerOptions.target` is `"ES2020"`
- AND `compilerOptions.module` is `"ESNext"`
- AND `compilerOptions.jsx` is `"react-jsx"`
- AND `compilerOptions.strict` is `True`
- AND `compilerOptions.moduleResolution` is `"bundler"`
- AND `include` contains `"src"`
- **File:** `tests/test_project_scaffolder.py`

#### Test: vitest.config.ts reflects coverage threshold from pipeline-config.json

- **Maps to:** Requirement "Project scaffolding files are valid and well-formed" → Scenario "vitest.config.ts reflects coverage threshold from pipeline-config.json"
- **Type:** unit
- **Given:** `pipeline-config.json` contains `qualityGates.minTestCoverage: 85`
- **When:** `scaffold_project_files(brand_profile, str(tmp_path))` is called
- **Then:** the content of `vitest.config.ts` contains the string `"85"` (the threshold value)
- **File:** `tests/test_project_scaffolder.py`

#### Test: vite.config.ts marks React as external

- **Maps to:** Requirement "Project scaffolding files are valid and well-formed" → Acceptance criteria (vite.config.ts)
- **Type:** unit
- **Given:** scaffolding files have been written
- **When:** the content of `vite.config.ts` is read
- **Then:** the string `"react"` appears in the external dependencies section
- AND the string `'"es"'` or `"'es'"` appears in the formats list
- AND the string `'"cjs"'` or `"'cjs'"` appears in the formats list
- **File:** `tests/test_project_scaffolder.py`

#### Test: Function returns dict with absolute paths to existing files

- **Maps to:** Requirement "Project scaffolding files are valid and well-formed" → Acceptance criteria (return type)
- **Type:** unit
- **Given:** `pipeline-config.json` exists in `tmp_path`
- **When:** `scaffold_project_files(brand_profile, str(tmp_path))` is called
- **Then:** all values in the returned dict are absolute paths to existing files
- **File:** `tests/test_project_scaffolder.py`

#### Test: Idempotent — second call overwrites without error

- **Maps to:** Requirement "Retry and idempotency safety" → Scenario "Idempotent re-run produces identical output"
- **Type:** unit
- **Given:** `scaffold_project_files` has already been called once
- **When:** `scaffold_project_files` is called again with identical arguments
- **Then:** no exception is raised
- AND all three files exist with content identical to the first call
- **File:** `tests/test_project_scaffolder.py`

---

### ProjectScaffolder — error cases

#### Test: Missing pipeline-config.json raises error

- **Maps to:** Requirement "Project scaffolding files are valid and well-formed" → Scenario "Missing pipeline-config.json causes failure"
- **Type:** unit
- **Given:** an empty `tmp_path` directory without `pipeline-config.json`
- **When:** `scaffold_project_files(brand_profile, str(tmp_path))` is called
- **Then:** `FileNotFoundError` or `ValueError` is raised
- AND the error message mentions `pipeline-config.json` or `ConfigGenerator`
- **File:** `tests/test_project_scaffolder.py`

---

### Agent 5 — factory and structural tests

#### Test: create_pipeline_config_agent returns Agent with correct role

- **Maps to:** Requirement "Agent 5 Task T5 produces all four output files" → Acceptance criteria (agent factory)
- **Type:** unit (structural, no LLM)
- **Given:** no special setup
- **When:** `create_pipeline_config_agent()` is called
- **Then:** the returned object is a `crewai.Agent` instance
- AND `agent.role` is `"Pipeline Configuration Agent"`
- AND `agent.tools` contains one `ConfigGenerator` instance
- AND `agent.tools` contains one `ProjectScaffolder` instance
- **File:** `tests/test_pipeline_config_agent.py`

#### Test: create_pipeline_config_agent uses DAF_TIER2_MODEL env var

- **Maps to:** Requirement "Agent 5 Task T5 produces all four output files" → Acceptance criteria (model config)
- **Type:** unit (structural)
- **Given:** `DAF_TIER2_MODEL=claude-sonnet-4-custom` is set in environment
- **When:** `create_pipeline_config_agent()` is called
- **Then:** `agent.llm` (or equivalent model config) contains `"claude-sonnet-4-custom"`
- **File:** `tests/test_pipeline_config_agent.py`

#### Test: create_pipeline_config_task returns Task with correct structure

- **Maps to:** Requirement "Agent 5 Task T5 produces all four output files" → Acceptance criteria (task factory)
- **Type:** unit (structural)
- **Given:** a valid `output_dir` string and `brand_profile_path` string
- **When:** `create_pipeline_config_task(output_dir=".", brand_profile_path="./brand-profile.json")` is called
- **Then:** the returned object is a `crewai.Task` instance
- AND the task description mentions both `ConfigGenerator` and `ProjectScaffolder` (or their invocation)
- AND the task description mentions the expected output files
- **File:** `tests/test_pipeline_config_agent.py`

#### Test: create_pipeline_config_task includes context_tasks when provided

- **Maps to:** Requirement "Agent 5 Task T5 produces all four output files" → Scenario "Task T5 runs after Task T1 via context_tasks"
- **Type:** unit (structural)
- **Given:** a mock upstream `Task` object `task_t1`
- **When:** `create_pipeline_config_task(output_dir=".", brand_profile_path="./brand-profile.json", context_tasks=[task_t1])` is called
- **Then:** the returned task's `context` field contains `task_t1`
- **File:** `tests/test_pipeline_config_agent.py`

#### Test: ConfigGenerator is a valid BaseTool subclass

- **Maps to:** Requirement "Agent 5 Task T5 produces all four output files" → Acceptance criteria (tool structure)
- **Type:** unit (structural)
- **Given:** no setup
- **When:** `ConfigGenerator()` is instantiated
- **Then:** the instance is a subclass of `crewai.tools.BaseTool`
- AND `tool.name` is a non-empty string
- AND `tool.description` is a non-empty string
- **File:** `tests/test_pipeline_config_agent.py`

#### Test: ProjectScaffolder is a valid BaseTool subclass

- **Maps to:** Requirement "Agent 5 Task T5 produces all four output files" → Acceptance criteria (tool structure)
- **Type:** unit (structural)
- **Given:** no setup
- **When:** `ProjectScaffolder()` is instantiated
- **Then:** the instance is a subclass of `crewai.tools.BaseTool`
- AND `tool.name` is a non-empty string
- AND `tool.description` is a non-empty string
- **File:** `tests/test_pipeline_config_agent.py`

---

## Edge Case Tests

#### Test: Standard scope → includes "navigation" and "data-display" but not "data-entry"

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Acceptance criteria (domain categories)
- **Type:** unit
- **Given:** Brand Profile with `scope: "standard"`
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** `domains.categories` contains `"navigation"` and `"data-display"`
- AND `"data-entry"` is NOT in `domains.categories`
- **File:** `tests/test_config_generator.py`

#### Test: Model defaults apply when no env vars are set

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Scenario "Model identifiers from environment variables"
- **Type:** unit
- **Given:** `DAF_TIER1_MODEL`, `DAF_TIER2_MODEL`, `DAF_TIER3_MODEL` are all unset
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** `models.tier1` is `"claude-opus-4-20250514"`
- AND `models.tier2` is `"claude-sonnet-4-20250514"`
- AND `models.tier3` is `"claude-haiku-4-20250414"`
- **File:** `tests/test_config_generator.py`

#### Test: tsconfig.json is valid JSON (not TypeScript)

- **Maps to:** Requirement "Project scaffolding files are valid and well-formed" → Acceptance criteria (tsconfig.json validity)
- **Type:** unit
- **Given:** scaffolding files have been written
- **When:** `tsconfig.json` is read and parsed with `json.loads()`
- **Then:** parsing succeeds without raising `json.JSONDecodeError`
- **File:** `tests/test_project_scaffolder.py`

#### Test: Comprehensive scope beta list contains exactly the 7 expected names

- **Maps to:** Requirement "pipeline-config.json schema completeness" → Scenario "Comprehensive scope → beta components"
- **Type:** unit
- **Given:** Brand Profile with `scope: "comprehensive"`
- **When:** `generate_pipeline_config(brand_profile, str(tmp_path))` is called
- **Then:** `lifecycle.betaComponents` has length `7`
- AND contains exactly: `DatePicker`, `DataGrid`, `TreeView`, `Drawer`, `Stepper`, `FileUpload`, `RichText`
- **File:** `tests/test_config_generator.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Line coverage (`config_generator.py`) | ≥80% | PRD quality gate; all inference paths exercised |
| Line coverage (`project_scaffolder.py`) | ≥80% | PRD quality gate; all file-write paths exercised |
| Line coverage (`agents/pipeline_config.py`) | ≥80% | PRD quality gate; factory functions and task wiring |
| Branch coverage | ≥70% | Covers scope-tier conditionals and env var branches |
| A11y rules passing | N/A | No UI output in this change |

---

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_config_generator.py` | new | Unit tests for `generate_pipeline_config()`: schema completeness, scope tier derivation, a11y threshold mapping, model env var resolution, idempotency, error handling |
| `tests/test_project_scaffolder.py` | new | Unit tests for `scaffold_project_files()`: file presence, tsconfig.json content, vitest threshold injection, vite.config.ts externals, idempotency, missing-pipeline-config error |
| `tests/test_pipeline_config_agent.py` | new | Structural tests for `ConfigGenerator` and `ProjectScaffolder` BaseTool subclasses, `create_pipeline_config_agent()` and `create_pipeline_config_task()` factories |
