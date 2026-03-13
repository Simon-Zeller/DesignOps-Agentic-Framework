# Specification

## Purpose

This spec governs the `ConfigGenerator` tool, the `ProjectScaffolder` tool, and the Agent 5 (Pipeline Configuration Agent) module. It defines the behavioral requirements for generating `pipeline-config.json` and the project scaffolding files (`tsconfig.json`, `vitest.config.ts`, `vite.config.ts`) as produced by the DS Bootstrap Crew (Agent 5, Task T5, §4.1 and §3.8).

---

## Requirements

### Requirement: pipeline-config.json schema completeness

The `ConfigGenerator` tool SHALL generate a `pipeline-config.json` file that conforms to the full schema defined in PRD §3.8. The DS Bootstrap Crew's Agent 5 (Pipeline Configuration Agent) drives this tool as part of Task T5. The Governance Crew (Phase 4b, Agents 28–31) reads this file as its primary input seed.

All six top-level sections MUST be present: `qualityGates`, `lifecycle`, `domains`, `retry`, `models`, `buildConfig`.

#### Acceptance Criteria

- [ ] `generate_pipeline_config(brand_profile, output_dir)` writes `pipeline-config.json` to `output_dir`
- [ ] The output file contains all six top-level keys: `qualityGates`, `lifecycle`, `domains`, `retry`, `models`, `buildConfig`
- [ ] `qualityGates.a11yLevel` equals the Brand Profile's `accessibility.level` field (`"AA"` or `"AAA"`)
- [ ] `qualityGates.minCompositeScore` is `70` when `a11yLevel` is `"AA"` and `85` when `a11yLevel` is `"AAA"`
- [ ] `qualityGates.minTestCoverage` is `80` for `starter`/`standard` scope and `75` for `comprehensive` scope
- [ ] `qualityGates.blockOnWarnings` is `false` (default; not overridden by a11y level)
- [ ] `lifecycle.defaultStatus` is `"stable"` for all scope tiers
- [ ] `lifecycle.betaComponents` is an empty list for `starter`/`standard` scope
- [ ] `lifecycle.betaComponents` contains all 7 Comprehensive-delta components for `comprehensive` scope
- [ ] `lifecycle.deprecationGracePeriodDays` is `90`
- [ ] `domains.categories` always includes `["forms", "layout", "feedback"]`
- [ ] `domains.categories` includes `"navigation"` and `"data-display"` for `standard`/`comprehensive` scope
- [ ] `domains.categories` includes `"data-entry"` for `comprehensive` scope only
- [ ] `domains.autoAssign` is `true`
- [ ] `retry.maxComponentRetries` is `3`
- [ ] `retry.maxCrewRetries` is `2`
- [ ] `models.tier1`, `models.tier2`, `models.tier3` are populated from env vars or PRD defaults
- [ ] `buildConfig.tsTarget` is `"ES2020"`
- [ ] `buildConfig.moduleFormat` is `"ESNext"`
- [ ] `buildConfig.cssModules` is `false`
- [ ] The function returns the absolute path to the written file as a string
- [ ] Calling the function twice with the same arguments is idempotent — the file is overwritten without error

#### Scenario: AA accessibility → score 70, standard scope → coverage 80

- GIVEN a Brand Profile with `accessibility.level: "AA"` and `scope: "standard"`
- WHEN `generate_pipeline_config(brand_profile, output_dir)` is called
- THEN `pipeline-config.json` contains `qualityGates.minCompositeScore: 70`
- AND `qualityGates.minTestCoverage: 80`
- AND `qualityGates.a11yLevel: "AA"`

#### Scenario: AAA accessibility → score 85

- GIVEN a Brand Profile with `accessibility.level: "AAA"` and `scope: "starter"`
- WHEN `generate_pipeline_config(brand_profile, output_dir)` is called
- THEN `pipeline-config.json` contains `qualityGates.minCompositeScore: 85`
- AND `qualityGates.a11yLevel: "AAA"`

#### Scenario: Comprehensive scope → beta components and wider domain categories

- GIVEN a Brand Profile with `scope: "comprehensive"`
- WHEN `generate_pipeline_config(brand_profile, output_dir)` is called
- THEN `lifecycle.betaComponents` contains exactly `["DatePicker", "DataGrid", "TreeView", "Drawer", "Stepper", "FileUpload", "RichText"]`
- AND `domains.categories` contains `"forms"`, `"layout"`, `"feedback"`, `"navigation"`, `"data-display"`, and `"data-entry"`
- AND `qualityGates.minTestCoverage` is `75`

#### Scenario: Starter scope → empty beta list and minimal domain categories

- GIVEN a Brand Profile with `scope: "starter"`
- WHEN `generate_pipeline_config(brand_profile, output_dir)` is called
- THEN `lifecycle.betaComponents` is an empty list `[]`
- AND `domains.categories` contains `"forms"`, `"layout"`, `"feedback"` and does NOT contain `"navigation"` or `"data-display"`

#### Scenario: Model identifiers from environment variables

- GIVEN environment variables `DAF_TIER1_MODEL=claude-opus-4-custom`, unset `DAF_TIER2_MODEL`, unset `DAF_TIER3_MODEL`
- WHEN `generate_pipeline_config(brand_profile, output_dir)` is called
- THEN `models.tier1` is `"claude-opus-4-custom"`
- AND `models.tier2` is the PRD default `"claude-sonnet-4-20250514"`
- AND `models.tier3` is the PRD default `"claude-haiku-4-20250414"`

#### Scenario: Missing Brand Profile fields cause ValueError

- GIVEN a Brand Profile dict missing the `accessibility` key
- WHEN `generate_pipeline_config(brand_profile, output_dir)` is called
- THEN a `ValueError` (or `KeyError`) is raised with a descriptive message identifying the missing field

---

### Requirement: Project scaffolding files are valid and well-formed

The `ProjectScaffolder` tool SHALL write `tsconfig.json`, `vitest.config.ts`, and `vite.config.ts` to the output directory. These files are required by Phase 2+ crews for TypeScript compilation, test execution, and build validation (§3.6, §4.1). Their absence is a precondition violation that causes fatal errors in downstream crews.

#### Acceptance Criteria

- [ ] `scaffold_project_files(brand_profile, output_dir)` writes all three files to `output_dir`
- [ ] The function returns a `dict[str, str]` mapping each filename to its absolute path
- [ ] `tsconfig.json` is valid JSON and contains at minimum: `compilerOptions.target`, `compilerOptions.module`, `compilerOptions.jsx`, `compilerOptions.strict`, `include`
- [ ] `tsconfig.json` sets `strict: true`, `jsx: "react-jsx"`, `target: "ES2020"`, `module: "ESNext"`, `moduleResolution: "bundler"`
- [ ] `vitest.config.ts` is valid TypeScript source containing a default export with `environment: "jsdom"`, `globals: true`
- [ ] `vitest.config.ts` coverage configuration reads `minTestCoverage` from the written `pipeline-config.json` file in `output_dir`
- [ ] `vite.config.ts` is valid TypeScript source containing a library-mode build config with `entry: "src/index.ts"`, `formats: ["es", "cjs"]`
- [ ] `vite.config.ts` marks React and React-DOM as external
- [ ] Calling the function twice with the same arguments is idempotent — files are overwritten without error
- [ ] The function fails with a clear error if `pipeline-config.json` does not already exist in `output_dir` (because `ConfigGenerator` must run first)

#### Scenario: Scaffolding files are written correctly

- GIVEN an output directory where `pipeline-config.json` already exists (written by `ConfigGenerator`)
- WHEN `scaffold_project_files(brand_profile, output_dir)` is called
- THEN `tsconfig.json` exists at `output_dir/tsconfig.json`
- AND `vitest.config.ts` exists at `output_dir/vitest.config.ts`
- AND `vite.config.ts` exists at `output_dir/vite.config.ts`
- AND the returned dict has exactly 3 keys: `"tsconfig.json"`, `"vitest.config.ts"`, `"vite.config.ts"`

#### Scenario: vitest.config.ts reflects coverage threshold from pipeline-config.json

- GIVEN `pipeline-config.json` in `output_dir` contains `qualityGates.minTestCoverage: 85`
- WHEN `scaffold_project_files(brand_profile, output_dir)` is called
- THEN `vitest.config.ts` contains a coverage threshold value of `85`

#### Scenario: Missing pipeline-config.json causes failure

- GIVEN an output directory without a `pipeline-config.json` file
- WHEN `scaffold_project_files(brand_profile, output_dir)` is called
- THEN a `FileNotFoundError` (or `ValueError`) is raised with a message indicating that `ConfigGenerator` must run first

---

### Requirement: Agent 5 Task T5 produces all four output files

The DS Bootstrap Crew's Agent 5 (Pipeline Configuration Agent) SHALL, when executing Task T5, invoke both `ConfigGenerator` and `ProjectScaffolder` in the correct order and confirm all four output files exist. This fulfills the BS Crew I/O contract (§3.6), which requires `pipeline-config.json`, `tsconfig.json`, `vitest.config.ts`, and `vite.config.ts` to be present in the output folder before Phase 2 begins.

#### Acceptance Criteria

- [ ] `create_pipeline_config_agent()` returns a `crewai.Agent` instance with role `"Pipeline Configuration Agent"`
- [ ] The agent is configured with model `DAF_TIER2_MODEL` env var or default Sonnet
- [ ] The agent has both `ConfigGenerator` and `ProjectScaffolder` in its `tools` list
- [ ] `create_pipeline_config_task(output_dir, brand_profile_path)` returns a `crewai.Task` instance
- [ ] The task description instructs the agent to invoke `ConfigGenerator` before `ProjectScaffolder`
- [ ] The task expected output describes the four files that must be written
- [ ] When run with a valid Brand Profile, all four files are present in `output_dir` after task completion
- [ ] When `context_tasks` is provided, the created task includes them as `context`

#### Scenario: Task T5 produces all four files

- GIVEN a valid `brand-profile.json` exists at `brand_profile_path`
- AND an empty `output_dir` is provided
- WHEN `create_pipeline_config_task(output_dir, brand_profile_path)` is executed by Agent 5
- THEN `output_dir/pipeline-config.json` exists and is valid JSON
- AND `output_dir/tsconfig.json` exists and is valid JSON
- AND `output_dir/vitest.config.ts` exists and is non-empty
- AND `output_dir/vite.config.ts` exists and is non-empty

#### Scenario: Task T5 runs after Task T1 (Brand Discovery) via context_tasks

- GIVEN Agent 1's brand discovery task (`task_t1`) has completed
- WHEN `create_pipeline_config_task(output_dir, brand_profile_path, context_tasks=[task_t1])` is created
- THEN the task's `context` field includes `task_t1`
- AND the task description references reading from `brand_profile_path`

---

### Requirement: Retry and idempotency safety

Agent 5 and its tools MUST be safe to re-invoke without corrupting existing output. If Agent 6 (First Publish Agent) triggers a re-run of Agent 5 due to a downstream Phase 2 rejection, all four output files SHALL be overwritten cleanly without leaving partial or corrupt state.

#### Acceptance Criteria

- [ ] Re-running `generate_pipeline_config` with the same inputs overwrites `pipeline-config.json` atomically (write to temp then rename)
- [ ] Re-running `scaffold_project_files` with the same inputs overwrites all three scaffolding files without error
- [ ] No partial files exist if either tool raises an exception mid-write

#### Scenario: Idempotent re-run produces identical output

- GIVEN `generate_pipeline_config(brand_profile, output_dir)` has already been called once
- WHEN it is called again with identical arguments
- THEN `pipeline-config.json` has the same contents as after the first call
- AND no `FileExistsError` or `PermissionError` is raised
