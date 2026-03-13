# TDD Plan: p17-release-crew

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

All tests are written in **pytest** following the project's existing pattern. LLM calls are mocked using `unittest.mock.patch` on `crewai.Agent` and `crewai.Crew` constructors where needed. Deterministic tool calls use real file-system fixtures via `tmp_path` (pytest). Subprocess calls (`npm install`, `tsc --noEmit`, `npm test`) are mocked via `unittest.mock.patch("subprocess.run")`.

Coverage target: ≥80% line coverage per all new files, ≥70% branch coverage. Tests must fail (red) before implementation begins; passing tests signal the green phase.

---

## Test Cases

### Crew Factory

#### Test: Factory returns a real crewai.Crew instance

- **Maps to:** Requirement "Release Crew factory replaces stub" → Scenario "Factory returns a real crew"
- **Type:** unit
- **Given:** `tmp_path` contains `reports/governance/quality-gates.json` with valid JSON
- **When:** `create_release_crew(str(tmp_path))` is called
- **Then:** returned value is an instance of `crewai.Crew`
- **File:** `tests/test_release_crew.py`

#### Test: Crew has 4 agents and 6 tasks

- **Maps to:** Requirement "Release Crew factory replaces stub" → AC: exact agent/task counts
- **Type:** unit
- **Given:** valid `output_dir` with gate report present
- **When:** `create_release_crew(output_dir)` is called
- **Then:** `len(crew.agents) == 4` and `len(crew.tasks) == 6`
- **File:** `tests/test_release_crew.py`

#### Test: Pre-flight guard raises RuntimeError when gate report missing

- **Maps to:** Requirement "Release Crew factory replaces stub" → Scenario "Pre-flight guard fires"
- **Type:** unit
- **Given:** `output_dir` does not contain `reports/governance/quality-gates.json`
- **When:** `create_release_crew(output_dir)` is called
- **Then:** `RuntimeError` is raised with a message referencing `quality-gates.json`
- **File:** `tests/test_release_crew.py`

#### Test: Crew creates docs/ and docs/codemods/ directories

- **Maps to:** Requirement "Release Crew factory replaces stub" → AC: directory creation
- **Type:** unit
- **Given:** `output_dir` exists but `docs/` and `docs/codemods/` are absent
- **When:** `create_release_crew(output_dir)` is called
- **Then:** `docs/` and `docs/codemods/` exist in `output_dir`
- **File:** `tests/test_release_crew.py`

---

### Agent 36 — Semver Agent

#### Test: create_semver_agent returns a crewai.Agent

- **Maps to:** Requirement "Agent 36 – Semver Agent" → AC: factory return type
- **Type:** unit
- **Given:** a model string and a valid `output_dir`
- **When:** `create_semver_agent(model, output_dir)` is called
- **Then:** returned value is an instance of `crewai.Agent`
- **File:** `tests/test_semver_agent.py`

#### Test: Agent configured with GateStatusReader and VersionCalculator tools

- **Maps to:** Requirement "Agent 36 – Semver Agent" → AC: tool assignment
- **Type:** unit
- **Given:** a model string and an `output_dir`
- **When:** `create_semver_agent(model, output_dir)` is called
- **Then:** the agent's `tools` list contains instances of `GateStatusReader` and `VersionCalculator`
- **File:** `tests/test_semver_agent.py`

---

### Agent 37 — Release Changelog Agent

#### Test: create_release_changelog_agent returns a crewai.Agent

- **Maps to:** Requirement "Agent 37 – Release Changelog Agent" → AC: factory return type
- **Type:** unit
- **Given:** a model string and a valid `output_dir`
- **When:** `create_release_changelog_agent(model, output_dir)` is called
- **Then:** returned value is an instance of `crewai.Agent`
- **File:** `tests/test_release_changelog_agent.py`

#### Test: Agent configured with ComponentInventoryReader, QualityReportParser, ProseGenerator

- **Maps to:** Requirement "Agent 37 – Release Changelog Agent" → AC: tool assignment
- **Type:** unit
- **Given:** a model string and an `output_dir`
- **When:** `create_release_changelog_agent(model, output_dir)` is called
- **Then:** the agent's `tools` list contains instances of `ComponentInventoryReader`, `QualityReportParser`, and `ProseGenerator`
- **File:** `tests/test_release_changelog_agent.py`

---

### Agent 38 — Codemod Agent

#### Test: create_codemod_agent returns a crewai.Agent

- **Maps to:** Requirement "Agent 38 – Codemod Agent" → AC: factory return type
- **Type:** unit
- **Given:** a model string and a valid `output_dir`
- **When:** `create_codemod_agent(model, output_dir)` is called
- **Then:** returned value is an instance of `crewai.Agent`
- **File:** `tests/test_codemod_agent.py`

#### Test: Agent configured with ASTPatternMatcher, CodemodTemplateGenerator, ExampleSuiteBuilder

- **Maps to:** Requirement "Agent 38 – Codemod Agent" → AC: tool assignment
- **Type:** unit
- **Given:** a model string and an `output_dir`
- **When:** `create_codemod_agent(model, output_dir)` is called
- **Then:** the agent's `tools` list contains instances of `ASTPatternMatcher`, `CodemodTemplateGenerator`, and `ExampleSuiteBuilder`
- **File:** `tests/test_codemod_agent.py`

---

### Agent 39 — Publish Agent

#### Test: create_publish_agent returns a crewai.Agent

- **Maps to:** Requirement "Agent 39 – Publish Agent" → AC: factory return type
- **Type:** unit
- **Given:** a model string and a valid `output_dir`
- **When:** `create_publish_agent(model, output_dir)` is called
- **Then:** returned value is an instance of `crewai.Agent`
- **File:** `tests/test_publish_agent.py`

#### Test: Agent configured with PackageJsonGenerator, DependencyResolver, TestResultParser, ReportWriter

- **Maps to:** Requirement "Agent 39 – Publish Agent" → AC: tool assignment
- **Type:** unit
- **Given:** a model string and an `output_dir`
- **When:** `create_publish_agent(model, output_dir)` is called
- **Then:** the agent's `tools` list contains instances of `PackageJsonGenerator`, `DependencyResolver`, `TestResultParser`, and `ReportWriter`
- **File:** `tests/test_publish_agent.py`

---

### Agent 40 — Rollback Agent

#### Test: create_rollback_agent returns a crewai.Agent

- **Maps to:** Requirement "Agent 40 – Rollback Agent" → AC: factory return type
- **Type:** unit
- **Given:** a model string and a valid `output_dir`
- **When:** `create_rollback_agent(model, output_dir)` is called
- **Then:** returned value is an instance of `crewai.Agent`
- **File:** `tests/test_rollback_agent.py`

#### Test: Agent configured with CheckpointCreator, RestoreExecutor, RollbackReporter

- **Maps to:** Requirement "Agent 40 – Rollback Agent" → AC: tool assignment
- **Type:** unit
- **Given:** a model string and an `output_dir`
- **When:** `create_rollback_agent(model, output_dir)` is called
- **Then:** the agent's `tools` list contains instances of `CheckpointCreator`, `RestoreExecutor`, and `RollbackReporter`
- **File:** `tests/test_rollback_agent.py`

#### Test: Agent 40 is NOT included in create_release_crew agents list

- **Maps to:** Requirement "Agent 40 – Rollback Agent" → AC: not in crew
- **Type:** unit
- **Given:** a valid `output_dir`
- **When:** `create_release_crew(output_dir)` is called
- **Then:** none of the crew's agents have role matching "rollback" or "checkpoint manager"
- **File:** `tests/test_release_crew.py`

---

### Tool — GateStatusReader

#### Test: Returns structured pass/fail counts from valid JSON

- **Maps to:** Requirement "Tool — GateStatusReader" → AC: return structure
- **Type:** unit
- **Given:** `reports/governance/quality-gates.json` contains 8 passed Fatal gates and 0 failed
- **When:** `GateStatusReader()._run("")` is called
- **Then:** result contains `{"fatal_passed": 8, "fatal_failed": 0}`
- **File:** `tests/test_gate_status_reader.py`

#### Test: Returns safe default when file is absent

- **Maps to:** Requirement "Tool — GateStatusReader" → AC: safe default
- **Type:** unit
- **Given:** `reports/governance/quality-gates.json` does not exist
- **When:** `GateStatusReader()._run("")` is called
- **Then:** result contains `{"fatal_passed": 0, "fatal_failed": 0, "gates": []}`
- **File:** `tests/test_gate_status_reader.py`

---

### Tool — VersionCalculator

#### Test: Returns v1.0.0 when all Fatal gates pass

- **Maps to:** Requirement "Tool — VersionCalculator" → AC: stable version
- **Type:** unit
- **Given:** input `{"fatal_failed": 0}`
- **When:** `VersionCalculator()._run(...)` is called
- **Then:** returns `"v1.0.0"`
- **File:** `tests/test_version_calculator.py`

#### Test: Returns v0.1.0 when any Fatal gate fails

- **Maps to:** Requirement "Tool — VersionCalculator" → AC: pre-release version
- **Type:** unit
- **Given:** input `{"fatal_failed": 2}`
- **When:** `VersionCalculator()._run(...)` is called
- **Then:** returns a string starting with `"v0."`
- **File:** `tests/test_version_calculator.py`

#### Test: Returns v0.1.0-experimental on malformed input

- **Maps to:** Requirement "Tool — VersionCalculator" → AC: experimental fallback
- **Type:** unit
- **Given:** input is `None` or malformed JSON
- **When:** `VersionCalculator()._run(...)` is called
- **Then:** returns `"v0.1.0-experimental"`
- **File:** `tests/test_version_calculator.py`

---

### Tool — ComponentInventoryReader

#### Test: Returns component list from reports and specs

- **Maps to:** Requirement "Agent 37 – Release Changelog Agent" → AC: inventory completeness
- **Type:** unit
- **Given:** `specs/button.spec.yaml` and `specs/input.spec.yaml` exist in `output_dir`
- **When:** `ComponentInventoryReader()._run("")` is called
- **Then:** returned data includes entries for `Button` and `Input`
- **File:** `tests/test_component_inventory_reader.py`

#### Test: Returns empty list when specs directory is absent

- **Maps to:** Requirement "Agent 37 – Release Changelog Agent" → edge case
- **Type:** unit
- **Given:** `specs/` directory does not exist
- **When:** `ComponentInventoryReader()._run("")` is called
- **Then:** returns `{"components": []}`
- **File:** `tests/test_component_inventory_reader.py`

---

### Tool — QualityReportParser

#### Test: Parses quality gate JSON into structured summary

- **Maps to:** Requirement "Tool — GateStatusReader" / Agent 37 changelog
- **Type:** unit
- **Given:** `reports/governance/quality-gates.json` with mixed pass/fail entries
- **When:** `QualityReportParser()._run("")` is called
- **Then:** returned dict includes `passed_gates`, `failed_gates`, and `warnings`
- **File:** `tests/test_quality_report_parser.py`

---

### Tool — ASTPatternMatcher

#### Test: Detects raw HTML elements in TSX source

- **Maps to:** Requirement "Agent 38 – Codemod Agent" → AC: raw HTML detection
- **Type:** unit
- **Given:** `src/components/` contains a `.tsx` file with `<button` usage
- **When:** `ASTPatternMatcher()._run("")` is called
- **Then:** returned data includes a `button` migration target
- **File:** `tests/test_ast_pattern_matcher.py`

#### Test: Detects hardcoded hex color values in TSX source

- **Maps to:** Requirement "Agent 38 – Codemod Agent" → AC: hardcoded color detection
- **Type:** unit
- **Given:** `src/components/` contains a `.tsx` file with `color: "#333333"`
- **When:** `ASTPatternMatcher()._run("")` is called
- **Then:** returned data includes a color migration target for `#333333`
- **File:** `tests/test_ast_pattern_matcher.py`

#### Test: Returns empty targets when no source exists

- **Maps to:** Requirement "Agent 38 – Codemod Agent" → Scenario "src/components/ does not exist"
- **Type:** unit
- **Given:** `src/components/` does not exist in `output_dir`
- **When:** `ASTPatternMatcher()._run("")` is called
- **Then:** returns `{"targets": []}` without raising an exception
- **File:** `tests/test_ast_pattern_matcher.py`

---

### Tool — CodemodTemplateGenerator

#### Test: Generates a codemod markdown file for a given migration target

- **Maps to:** Requirement "Agent 38 – Codemod Agent" → AC: before/after snippets
- **Type:** unit
- **Given:** input is `{"element": "button", "ds_component": "Button"}`
- **When:** `CodemodTemplateGenerator()._run(...)` is called
- **Then:** the output string contains both a "before" and "after" code block
- **File:** `tests/test_codemod_template_generator.py`

---

### Tool — ExampleSuiteBuilder

#### Test: Writes codemod files to docs/codemods/

- **Maps to:** Requirement "Agent 38 – Codemod Agent" → AC: file written to docs/codemods/
- **Type:** unit
- **Given:** `docs/codemods/` directory exists and a list of codemod entries is provided
- **When:** `ExampleSuiteBuilder()._run(...)` is called
- **Then:** at least one `.md` file is written inside `docs/codemods/`
- **File:** `tests/test_example_suite_builder.py`

---

### Tool — PackageJsonGenerator

#### Test: Generates a valid package.json with required fields

- **Maps to:** Requirement "Agent 39 – Publish Agent" → AC: package.json fields
- **Type:** unit
- **Given:** input includes `{"name": "my-ds", "version": "v1.0.0"}`
- **When:** `PackageJsonGenerator()._run(...)` is called
- **Then:** the returned JSON string contains `name`, `version`, `main`, `types`, `exports`, `peerDependencies`, `scripts`
- **File:** `tests/test_package_json_generator.py`

#### Test: Version field matches the semver input

- **Maps to:** Requirement "Agent 39 – Publish Agent" → AC: version consistency
- **Type:** unit
- **Given:** input version is `"v1.0.0"`
- **When:** `PackageJsonGenerator()._run(...)` is called
- **Then:** the `version` field in the generated JSON is `"1.0.0"` (stripped of `v` prefix)
- **File:** `tests/test_package_json_generator.py`

---

### Tool — DependencyResolver

#### Test: Returns npm_unavailable when npm is not on PATH

- **Maps to:** Requirement "Tool — DependencyResolver" → AC: graceful degradation
- **Type:** unit
- **Given:** `subprocess.run` is mocked to raise `FileNotFoundError`
- **When:** `DependencyResolver()._run("npm install")` is called
- **Then:** returns a dict with `{"status": "npm_unavailable"}`
- **File:** `tests/test_dependency_resolver.py`

#### Test: Returns success when command exits 0

- **Maps to:** Requirement "Tool — DependencyResolver" → AC: success case
- **Type:** unit
- **Given:** `subprocess.run` is mocked to return exit code 0 and stdout `"installed"`
- **When:** `DependencyResolver()._run("npm install")` is called
- **Then:** returns `{"status": "success", "stdout": "installed"}`
- **File:** `tests/test_dependency_resolver.py`

#### Test: Returns failed dict when command exits non-zero

- **Maps to:** Requirement "Tool — DependencyResolver" → AC: failure case
- **Type:** unit
- **Given:** `subprocess.run` is mocked to return exit code 1 and stderr `"error: cannot find module"`
- **When:** `DependencyResolver()._run("npm install")` is called
- **Then:** returns `{"status": "failed", "exit_code": 1, "stderr": "error: cannot find module"}`
- **File:** `tests/test_dependency_resolver.py`

#### Test: Never raises unhandled exception on any subprocess outcome

- **Maps to:** Requirement "Tool — DependencyResolver" → AC: no unhandled exception
- **Type:** unit
- **Given:** `subprocess.run` raises an arbitrary `OSError`
- **When:** `DependencyResolver()._run("npm install")` is called
- **Then:** no exception propagates; returns a dict with `{"status": "npm_unavailable"}`
- **File:** `tests/test_dependency_resolver.py`

---

### Tool — TestResultParser

#### Test: Parses passing test output into structured summary

- **Maps to:** Requirement "Agent 39 – Publish Agent" → AC: test result parsing
- **Type:** unit
- **Given:** `stdout` contains a typical Vitest success output with 10 tests passing
- **When:** `TestResultParser()._run(stdout)` is called
- **Then:** returns `{"passed": 10, "failed": 0, "skipped": 0}`
- **File:** `tests/test_test_result_parser.py`

#### Test: Parses failing test output into structured summary

- **Maps to:** Requirement "Agent 39 – Publish Agent" → AC: test failure (non-fatal)
- **Type:** unit
- **Given:** `stdout` contains a Vitest output with 8 passing and 2 failing
- **When:** `TestResultParser()._run(stdout)` is called
- **Then:** returns `{"passed": 8, "failed": 2, "skipped": 0}`
- **File:** `tests/test_test_result_parser.py`

---

### Tool — CheckpointCreator

#### Test: Snapshot creates checkpoints/<phase_name>/ directory

- **Maps to:** Requirement "Agent 40 – Rollback Agent" → AC: snapshot writes to checkpoints/
- **Type:** unit
- **Given:** `output_dir` exists with some files; `checkpoints/` does not exist
- **When:** `CheckpointCreator()._run("token-engine")` is called
- **Then:** `checkpoints/token-engine/` is created in `output_dir`
- **File:** `tests/test_checkpoint_creator.py`

#### Test: Snapshot copies output_dir contents into checkpoint directory

- **Maps to:** Requirement "Agent 40 – Rollback Agent" → AC: state is captured
- **Type:** unit
- **Given:** `output_dir` contains `reports/generation-summary.json`
- **When:** `CheckpointCreator()._run("ds-bootstrap")` is called
- **Then:** `checkpoints/ds-bootstrap/reports/generation-summary.json` exists
- **File:** `tests/test_checkpoint_creator.py`

---

### Tool — RestoreExecutor

#### Test: Restore copies checkpoint contents back to output_dir

- **Maps to:** Requirement "Agent 40 – Rollback Agent" → Scenario "Snapshot and restore cycle"
- **Type:** unit
- **Given:** `checkpoints/token-engine/` contains a snapshot with `reports/generation-summary.json`
- **When:** `RestoreExecutor()._run("token-engine")` is called
- **Then:** `output_dir/reports/generation-summary.json` is restored from the snapshot
- **File:** `tests/test_restore_executor.py`

#### Test: Raises FileNotFoundError when snapshot does not exist

- **Maps to:** Requirement "Agent 40 – Rollback Agent" → Scenario "No snapshot available"
- **Type:** unit
- **Given:** `checkpoints/ds-bootstrap/` does not exist
- **When:** `RestoreExecutor()._run("ds-bootstrap")` is called
- **Then:** `FileNotFoundError` is raised
- **File:** `tests/test_restore_executor.py`

---

### Tool — RollbackReporter

#### Test: Writes rollback-log.json with restore details

- **Maps to:** Requirement "Agent 40 – Rollback Agent" → AC: rollback-log.json written
- **Type:** unit
- **Given:** input is `{"restored_phase": "token-engine", "failed_crew": "design-to-code", "reason": "exhausted retries"}`
- **When:** `RollbackReporter()._run(...)` is called
- **Then:** `reports/rollback-log.json` is written with the input data
- **File:** `tests/test_rollback_reporter.py`

---

## Edge Case Tests

#### Test: Semver fallback writes warning entry when gate file is absent

- **Maps to:** Requirement "Agent 36 – Semver Agent" → Scenario "Gate report absent → experimental fallback"
- **Type:** unit
- **Given:** `reports/governance/quality-gates.json` does not exist
- **When:** `GateStatusReader()._run("")` is called
- **Then:** the result includes a `warnings` field indicating the fallback
- **File:** `tests/test_gate_status_reader.py`

#### Test: ComponentInventoryReader handles malformed spec YAML gracefully

- **Maps to:** Requirement "Agent 37 – Release Changelog Agent" → edge case: malformed input
- **Type:** unit
- **Given:** `specs/broken.spec.yaml` contains invalid YAML
- **When:** `ComponentInventoryReader()._run("")` is called
- **Then:** the broken spec is skipped; other specs are still included; no exception raised
- **File:** `tests/test_component_inventory_reader.py`

#### Test: ExampleSuiteBuilder writes README when no migration targets exist

- **Maps to:** Requirement "Agent 38 – Codemod Agent" → Scenario "No raw HTML found"
- **Type:** unit
- **Given:** codemod targets list is empty
- **When:** `ExampleSuiteBuilder()._run(...)` is called
- **Then:** `docs/codemods/README.md` is written stating no migrations are needed
- **File:** `tests/test_example_suite_builder.py`

#### Test: PackageJsonGenerator strips v-prefix from version string

- **Maps to:** Requirement "Agent 39 – Publish Agent" → AC: version consistency
- **Type:** unit
- **Given:** input version is `"v0.1.0-experimental"`
- **When:** `PackageJsonGenerator()._run(...)` is called
- **Then:** the `version` field in the generated JSON is `"0.1.0-experimental"`
- **File:** `tests/test_package_json_generator.py`

#### Test: Release Crew retry behavior — crew-level failure marks generation-summary

- **Maps to:** Requirement "Crew-level retry behavior" → Scenario "Crew exhausts retry budget"
- **Type:** integration
- **Given:** `create_release_crew(output_dir)` is called with a valid `output_dir`
- **AND:** the crew's `kickoff()` raises an exception (simulating failure)
- **When:** the mock caller (simulating Agent 6) exhausts 2 retry attempts
- **Then:** `reports/generation-summary.json` has `final_status == "failed"` (set by caller)
- **File:** `tests/test_release_crew.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Line coverage | ≥80% | PRD quality gate requirement |
| Branch coverage | ≥70% | Covers conditional logic paths (npm_unavailable, missing files, gate fallback) |
| A11y rules passing | N/A | No frontend output in this change |

---

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_release_crew.py` | new | Crew factory: real Crew returned, 4 agents, 6 tasks, pre-flight guard, directory creation, Agent 40 exclusion |
| `tests/test_semver_agent.py` | new | Agent 36 factory: return type, tool assignment |
| `tests/test_release_changelog_agent.py` | new | Agent 37 factory: return type, tool assignment |
| `tests/test_codemod_agent.py` | new | Agent 38 factory: return type, tool assignment |
| `tests/test_publish_agent.py` | new | Agent 39 factory: return type, tool assignment |
| `tests/test_rollback_agent.py` | new | Agent 40 factory: return type, tool assignment, exclusion from crew |
| `tests/test_gate_status_reader.py` | new | Tool: valid JSON, missing file, warning on fallback |
| `tests/test_version_calculator.py` | new | Tool: v1.0.0, v0.x.0, experimental fallback |
| `tests/test_component_inventory_reader.py` | new | Tool: component list from specs, empty specs, malformed YAML |
| `tests/test_quality_report_parser.py` | new | Tool: structured summary from gate JSON |
| `tests/test_ast_pattern_matcher.py` | new | Tool: raw HTML detection, hex color detection, absent src/ |
| `tests/test_codemod_template_generator.py` | new | Tool: before/after snippet generation |
| `tests/test_example_suite_builder.py` | new | Tool: file writing, README on empty targets |
| `tests/test_package_json_generator.py` | new | Tool: required fields, version stripping |
| `tests/test_dependency_resolver.py` | new | Tool: npm_unavailable, success, failure, no unhandled exception |
| `tests/test_test_result_parser.py` | new | Tool: pass/fail parsing |
| `tests/test_checkpoint_creator.py` | new | Tool: snapshot creates directory, copies files |
| `tests/test_restore_executor.py` | new | Tool: restore from snapshot, FileNotFoundError on missing snapshot |
| `tests/test_rollback_reporter.py` | new | Tool: rollback-log.json written with details |
| `tests/test_first_publish_agent.py` | modified | Add integration tests for Agent 40 wiring and snapshot/restore calls |
