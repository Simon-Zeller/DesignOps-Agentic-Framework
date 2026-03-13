# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

## 0. Pre-flight

- [x] 0.1 Create feature branch: `feat/p08-pipeline-config`
- [x] 0.2 Verify clean working tree (`git status`)
- [x] 0.3 Verify existing test suite passes (`pytest tests/ -x -q`)

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write failing tests FIRST, before any production code.
     Each test maps to a case from tdd.md. -->

### 1a. ConfigGenerator tests

- [x] 1.1 Create `tests/test_config_generator.py` with the following failing test stubs:
  - `test_generated_config_has_all_top_level_keys`
  - `test_aa_accessibility_standard_scope_thresholds`
  - `test_aaa_accessibility_raises_composite_score_to_85`
  - `test_comprehensive_scope_produces_beta_components_and_domains`
  - `test_starter_scope_empty_beta_and_minimal_domains`
  - `test_standard_scope_has_navigation_not_data_entry`
  - `test_fixed_default_fields`
  - `test_model_identifiers_from_env_vars`
  - `test_model_defaults_when_no_env_vars_set`
  - `test_output_is_valid_json`
  - `test_returns_absolute_path_to_written_file`
  - `test_idempotent_second_call_overwrites_without_error`
  - `test_missing_accessibility_key_raises_error`
  - `test_missing_scope_key_raises_error`
  - `test_comprehensive_beta_list_has_exactly_7_names`

### 1b. ProjectScaffolder tests

- [x] 1.2 Create `tests/test_project_scaffolder.py` with the following failing test stubs:
  - `test_all_three_scaffolding_files_written`
  - `test_tsconfig_contains_required_compiler_options`
  - `test_vitest_config_reflects_coverage_threshold`
  - `test_vite_config_marks_react_as_external`
  - `test_returns_dict_with_absolute_paths`
  - `test_idempotent_second_call_overwrites_without_error`
  - `test_missing_pipeline_config_raises_error`
  - `test_tsconfig_is_valid_json`

### 1c. Agent 5 structural tests

- [x] 1.3 Create `tests/test_pipeline_config_agent.py` with the following failing test stubs:
  - `test_create_agent_returns_agent_with_correct_role`
  - `test_create_agent_uses_tier2_model_env_var`
  - `test_create_task_returns_task_instance`
  - `test_create_task_includes_context_tasks`
  - `test_config_generator_is_valid_basetool`
  - `test_project_scaffolder_is_valid_basetool`

- [x] 1.4 Verify all new tests FAIL (red phase confirmation — `ImportError` or `NotImplementedError` is expected)
- [x] 1.5 **Git checkpoint:** `git add -A && git commit -m "test: scaffold failing tests for p08-pipeline-config"`

## 2. Implementation (TDD — Green Phase)

### 2a. Capability spec

- [x] 2.1 Create `openspec/specs/pipeline-config/spec.md` — copy from `openspec/changes/p08-pipeline-config/specs/pipeline-config/spec.md` (promotes the change‐spec to the canonical specs location)

### 2b. ConfigGenerator tool

- [x] 2.2 Create `src/daf/tools/config_generator.py`:
  - `generate_pipeline_config(brand_profile: dict, output_dir: str) -> str` pure function
  - Inference rules: `a11yLevel` → `minCompositeScore` mapping (AA→70, AAA→85)
  - Scope → `minTestCoverage` mapping (starter/standard→80, comprehensive→75)
  - Scope → `betaComponents` list (comprehensive→7 Comprehensive-delta names, else `[]`)
  - Scope → `domains.categories` accumulation (starter=3, standard=5, comprehensive=6)
  - Fixed defaults: `blockOnWarnings=False`, `defaultStatus="stable"`, `deprecationGracePeriodDays=90`, `autoAssign=True`, `maxComponentRetries=3`, `maxCrewRetries=2`, `tsTarget="ES2020"`, `moduleFormat="ESNext"`, `cssModules=False`
  - Model env var resolution: `os.environ.get("DAF_TIER1_MODEL", "claude-opus-4-20250514")` etc.
  - Writes to `{output_dir}/pipeline-config.json` with `json.dumps(..., indent=2)`
  - Returns absolute path string
  - `ConfigGenerator(BaseTool)` wrapper with `brand_profile_json` and `output_dir` Pydantic input schema

### 2c. ProjectScaffolder tool

- [x] 2.3 Create `src/daf/tools/project_scaffolder.py`:
  - `scaffold_project_files(brand_profile: dict, output_dir: str) -> dict[str, str]` pure function
  - Reads `{output_dir}/pipeline-config.json` to extract `qualityGates.minTestCoverage`; raises `FileNotFoundError` if file is absent
  - Writes `tsconfig.json` template (strict React+TS, target ES2020, module ESNext, moduleResolution bundler, jsx react-jsx)
  - Writes `vitest.config.ts` template (jsdom environment, globals, coverage threshold from `minTestCoverage`)
  - Writes `vite.config.ts` template (library mode, entry `src/index.ts`, formats `["es", "cjs"]`, react/react-dom external)
  - Returns `dict[str, str]` mapping filename → absolute path
  - `ProjectScaffolder(BaseTool)` wrapper with `brand_profile_json` and `output_dir` Pydantic input schema

### 2d. Agent 5 factory

- [x] 2.4 Create `src/daf/agents/pipeline_config.py`:
  - `create_pipeline_config_agent() -> Agent` — Tier 2 Sonnet, tools=[ConfigGenerator(), ProjectScaffolder()], role="Pipeline Configuration Agent"
  - `create_pipeline_config_task(output_dir: str, brand_profile_path: str, context_tasks: list[Task] | None = None) -> Task` — Task T5 description instructs agent to: (1) read brand-profile.json from brand_profile_path, (2) invoke ConfigGenerator, (3) invoke ProjectScaffolder, (4) confirm all four files written

### 2e. Update package exports

- [x] 2.5 Update `src/daf/tools/__init__.py` — add `ConfigGenerator` and `ProjectScaffolder` to exports
- [x] 2.6 Update `src/daf/agents/__init__.py` — add `create_pipeline_config_agent` and `create_pipeline_config_task` to exports

- [x] 2.7 Verify all tests PASS (green phase confirmation — `pytest tests/test_config_generator.py tests/test_project_scaffolder.py tests/test_pipeline_config_agent.py -v`)
- [x] 2.8 **Git checkpoint:** `git add -A && git commit -m "feat: implement p08-pipeline-config (Agent 5, ConfigGenerator, ProjectScaffolder)"`

## 3. Refactor (TDD — Refactor Phase)

- [x] 3.1 Review `config_generator.py` — extract inference rule tables as module-level constants (scope→coverage map, a11y→score map, scope→domains map) to remove inline conditionals
- [x] 3.2 Review `project_scaffolder.py` — ensure template strings are clean and readable; consider moving templates to module-level constants
- [x] 3.3 Review `pipeline_config.py` — verify task description is explicit about call ordering (ConfigGenerator before ProjectScaffolder); ensure expected output clearly lists all four files
- [x] 3.4 Ensure all tests still pass after refactor (`pytest tests/test_config_generator.py tests/test_project_scaffolder.py tests/test_pipeline_config_agent.py -v`)
- [x] 3.5 Review code against `design.md` architecture decisions — verify deterministic tool / agent boundary is maintained
- [x] 3.6 **Git checkpoint:** `git add -A && git commit -m "refactor: clean up p08-pipeline-config inference tables and templates"`

## 4. Integration & Quality

- [x] 4.1 Run full linter: `ruff check src/daf/tools/config_generator.py src/daf/tools/project_scaffolder.py src/daf/agents/pipeline_config.py`
- [x] 4.2 Run type checker: `pyright src/daf/tools/config_generator.py src/daf/tools/project_scaffolder.py src/daf/agents/pipeline_config.py`
- [x] 4.3 Fix all lint and type errors — zero warnings policy
- [x] 4.4 Run full test suite: `pytest tests/ -x -q`
- [x] 4.5 Verify no regressions in existing tests
- [x] 4.6 Check coverage: `pytest tests/test_config_generator.py tests/test_project_scaffolder.py tests/test_pipeline_config_agent.py --cov=src/daf/tools/config_generator --cov=src/daf/tools/project_scaffolder --cov=src/daf/agents/pipeline_config --cov-report=term-missing` — target ≥80% line coverage
- [x] 4.7 **Git checkpoint:** `git add -A && git commit -m "chore: fix lint and type errors for p08-pipeline-config"` (skip if no changes)

## 5. Final Verification & Push

- [ ] 5.1 `git status` — confirm zero untracked files, zero unstaged changes
- [ ] 5.2 `git log --oneline main..HEAD` — review all commits on this branch
- [ ] 5.3 Rebase on latest main if needed (`git fetch origin && git rebase origin/main`)
- [ ] 5.4 Push feature branch (`git push origin feat/p08-pipeline-config`)

## 6. Delivery

- [ ] 6.1 All tasks above are checked
- [ ] 6.2 Merge feature branch into main (`git checkout main && git merge feat/p08-pipeline-config`)
- [ ] 6.3 Push main (`git push origin main`)
- [ ] 6.4 Delete local feature branch (`git branch -d feat/p08-pipeline-config`)
- [ ] 6.5 Delete remote feature branch (`git push origin --delete feat/p08-pipeline-config`)
- [ ] 6.6 Verify clean state (`git branch -a` — feature branch gone, `git status` — clean)
