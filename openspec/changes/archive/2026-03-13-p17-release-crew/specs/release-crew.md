# Specification

## Purpose

Define the behavioral requirements for the Release Crew (Agents 36–40) implementation. This spec covers the five agents, their supporting tools, the crew factory, and the crew-level retry/failure contract as defined in PRD §4.8 and §3.4. Agent 40 (Rollback) is cross-cutting and specified separately — it is instantiated by Agent 6 (First Publish), not as part of the Release Crew task flow.

---

## Requirements

### Requirement: Release Crew factory replaces stub

The `create_release_crew(output_dir)` function in `src/daf/crews/release.py` MUST return a `crewai.Crew` instance (not a `StubCrew`), configured with four agents (Agents 36–39) and six tasks wired T1→T2→T3→T4→T5→T6.

#### Acceptance Criteria

- [ ] `create_release_crew(output_dir)` returns an instance of `crewai.Crew`
- [ ] The returned crew has exactly 4 agents (Agents 36–39; Agent 40 is excluded)
- [ ] The crew has exactly 6 tasks ordered T1→T6 with `context` chaining
- [ ] The function raises `RuntimeError` if `reports/governance/quality-gates.json` does not exist in `output_dir`
- [ ] The `docs/` and `docs/codemods/` directories are created if absent before any agent runs

#### Scenario: Factory returns a real crew

- GIVEN a valid `output_dir` containing `reports/governance/quality-gates.json`
- WHEN `create_release_crew(output_dir)` is called
- THEN a `crewai.Crew` instance is returned
- AND the crew has 4 agents
- AND the crew has 6 tasks in order T1→T6

#### Scenario: Pre-flight guard fires with missing gate report

- GIVEN an `output_dir` where `reports/governance/quality-gates.json` is absent
- WHEN `create_release_crew(output_dir)` is called
- THEN a `RuntimeError` is raised
- AND the error message references the missing `quality-gates.json`

---

### Requirement: Agent 36 – Semver Agent

Agent 36 (Semver Agent, Release Crew) MUST determine the semantic version number by reading quality gate results and applying conventional version semantics. The version MUST be written to `reports/generation-summary.json` under a `version` key.

Tools used: `GateStatusReader`, `VersionCalculator`.

#### Acceptance Criteria

- [ ] `create_semver_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] The agent is configured with `GateStatusReader` and `VersionCalculator` tools
- [ ] When all 8 Fatal gate checks pass, the version is `v1.0.0`
- [ ] When any Fatal gate check fails, the version is `v0.x.0` (where `x` is incremented per scope)
- [ ] When `quality-gates.json` is missing, the version falls back to `v0.1.0-experimental` with a logged warning
- [ ] The derived version is written to `reports/generation-summary.json` as `{"version": "v1.0.0"}`

#### Scenario: All Fatal gates pass → stable version

- GIVEN `reports/governance/quality-gates.json` shows all 8 Fatal checks as `passed`
- WHEN Agent 36 runs T1
- THEN `reports/generation-summary.json` contains `{"version": "v1.0.0"}`

#### Scenario: One or more Fatal gates fail → pre-release version

- GIVEN `reports/governance/quality-gates.json` shows `typescript_compilation` as `failed`
- WHEN Agent 36 runs T1
- THEN the version written is `v0.x.0` (not `v1.0.0`)

#### Scenario: Gate report absent → experimental fallback

- GIVEN `reports/governance/quality-gates.json` does not exist
- WHEN Agent 36 runs T1
- THEN the version written is `v0.1.0-experimental`
- AND a warning is recorded in `reports/generation-summary.json` under `warnings`

---

### Requirement: Agent 37 – Release Changelog Agent

Agent 37 (Release Changelog Agent, Release Crew) MUST write `docs/changelog.md` as structured prose grouped by category. The changelog is the *what* document — it inventories release contents, not design rationale.

Tools used: `ComponentInventoryReader`, `QualityReportParser`, `ProseGenerator`.

#### Acceptance Criteria

- [ ] `create_release_changelog_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] The agent is configured with `ComponentInventoryReader`, `QualityReportParser`, and `ProseGenerator` tools
- [ ] `docs/changelog.md` is written after T2 completes as valid Markdown (not empty)
- [ ] The changelog MUST include a component inventory section listing each component with status and quality score
- [ ] The changelog MUST include a token category summary (count per category)
- [ ] The changelog MUST include a quality gate summary (pass/fail per gate)
- [ ] The changelog MUST include a known issues section listing failed components

#### Scenario: Full pipeline with all components passing

- GIVEN all components have `status: "passed"` in the quality gate report
- WHEN Agent 37 runs T2
- THEN `docs/changelog.md` contains a component inventory with all components listed
- AND the gate summary section shows all 8 Fatal checks as `passed`
- AND the known issues section is empty or states "No known issues"

#### Scenario: Some components failed

- GIVEN `Button` has `status: "failed"` in the quality gate report
- WHEN Agent 37 runs T2
- THEN `docs/changelog.md` lists `Button` in the known issues section
- AND the known issues section includes the failure reason

#### Scenario: Changelog file already exists (idempotent)

- GIVEN `docs/changelog.md` already exists with prior content
- WHEN Agent 37 runs T2
- THEN the existing file is overwritten with fresh content
- AND the new changelog reflects the current pipeline run's gate results

---

### Requirement: Agent 38 – Codemod Agent

Agent 38 (Codemod Agent, Release Crew) MUST generate example adoption codemod scripts in `docs/codemods/` that demonstrate migration from ad-hoc UI patterns to design system equivalents. Scripts are human-readable examples, not executable transforms.

Tools used: `ASTPatternMatcher`, `CodemodTemplateGenerator`, `ExampleSuiteBuilder`.

#### Acceptance Criteria

- [ ] `create_codemod_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] The agent is configured with `ASTPatternMatcher`, `CodemodTemplateGenerator`, and `ExampleSuiteBuilder` tools
- [ ] At least one file is written to `docs/codemods/` after T3 completes
- [ ] Each codemod file MUST contain a "before" snippet and an "after" snippet
- [ ] The `ASTPatternMatcher` tool MUST scan `src/components/` and `src/primitives/` for codemod migration targets
- [ ] Raw HTML element usages (e.g. `<button>`, `<input>`) MUST be represented as migration targets where corresponding design system components exist
- [ ] Hardcoded color values (hex, rgb) MUST be represented as migration targets where semantic token equivalents exist

#### Scenario: Components and raw HTML found

- GIVEN `src/components/button/Button.tsx` exists (a `Button` design system component)
- AND the scanned source contains `<button` usage patterns
- WHEN Agent 38 runs T3
- THEN `docs/codemods/button-migration.md` (or equivalent) is written
- AND the file shows a "before" example using raw `<button>`
- AND the file shows an "after" example using `<Button>` from the design system

#### Scenario: No raw HTML or hardcoded colors found

- GIVEN the scanned source contains no raw HTML element usages and no hardcoded colors
- WHEN Agent 38 runs T3
- THEN `docs/codemods/` contains at least a `README.md` noting no migrations are needed

#### Scenario: `src/components/` does not exist

- GIVEN the `src/components/` directory is absent from `output_dir`
- WHEN Agent 38 runs T3
- THEN the agent writes a minimal `docs/codemods/README.md` noting no source to scan
- AND does not raise an exception

---

### Requirement: Agent 39 – Publish Agent

Agent 39 (Publish Agent, Release Crew) MUST assemble the final `package.json` and execute the full validation sequence (`npm install`, `tsc --noEmit`, `npm test`). It MUST parse all results into `reports/generation-summary.json` and set the definitive `final_status`.

Tools used: `PackageJsonGenerator`, `DependencyResolver`, `TestResultParser`, `ReportWriter`.

#### Acceptance Criteria

- [ ] `create_publish_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] The agent is configured with `PackageJsonGenerator`, `DependencyResolver`, `TestResultParser`, and `ReportWriter` tools
- [ ] `package.json` is written with valid JSON after T4 completes (not `{"stub": true}`)
- [ ] `package.json` MUST include `name`, `version`, `main`, `types`, `exports`, `peerDependencies`, and `scripts`
- [ ] The `version` field in `package.json` MUST match the version written by Agent 36
- [ ] `src/index.ts` barrel export is written (or a pre-existing one is preserved)
- [ ] After T5, `reports/generation-summary.json` MUST contain `final_status` set to one of: `"success"`, `"partial"`, `"failed"`
- [ ] If `npm` is not found on `$PATH`, `DependencyResolver` returns `{"status": "npm_unavailable"}` and `final_status` is set to `"partial"` (not `"failed"`)
- [ ] If `npm install` fails, `final_status` is `"failed"` and `npm_build` gate is recorded as `failed` in the summary
- [ ] If `tsc --noEmit` fails, `final_status` is `"failed"` and `typescript_compilation` gate is recorded as `failed`
- [ ] If `npm test` fails, `final_status` is `"partial"` (test failures are Warning, not Fatal per §8)

#### Scenario: All validation steps succeed

- GIVEN `npm install`, `tsc --noEmit`, and `npm test` all exit with code 0
- WHEN Agent 39 runs T5
- THEN `reports/generation-summary.json` has `final_status: "success"`
- AND `package.json` exists with valid content (non-stub)

#### Scenario: npm not available

- GIVEN `npm` is not found on `$PATH`
- WHEN Agent 39 runs T5
- THEN `reports/generation-summary.json` has `final_status: "partial"`
- AND a `warnings` entry notes `npm_unavailable`
- AND no exception is raised

#### Scenario: TypeScript compilation fails

- GIVEN `tsc --noEmit` exits with a non-zero code
- WHEN Agent 39 runs T5
- THEN `reports/generation-summary.json` has `final_status: "failed"`
- AND the `typescript_compilation` gate is recorded as `failed`

#### Scenario: Test failures only (non-fatal)

- GIVEN `npm install` and `tsc --noEmit` succeed
- AND `npm test` exits with a non-zero code
- WHEN Agent 39 runs T5
- THEN `reports/generation-summary.json` has `final_status: "partial"`
- AND the test failure count is recorded in the summary

---

### Requirement: Agent 40 – Rollback Agent (cross-cutting)

Agent 40 (Rollback Agent) is instantiated by Agent 6 (First Publish Agent, DS Bootstrap Crew) at pipeline start. It MUST snapshot the output folder before each crew run and restore from the last known-good snapshot when a crew exhausts its retry budget.

Tools used: `CheckpointCreator`, `RestoreExecutor`, `RollbackReporter`.

#### Acceptance Criteria

- [ ] `create_rollback_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] The agent is configured with `CheckpointCreator`, `RestoreExecutor`, and `RollbackReporter` tools
- [ ] `CheckpointCreator.snapshot(phase_name)` writes the current state of `output_dir` to `checkpoints/<phase_name>/`
- [ ] `RestoreExecutor.restore(phase_name)` restores `output_dir` from `checkpoints/<phase_name>/`
- [ ] After any restore, `reports/rollback-log.json` is written describing what was restored and why
- [ ] Agent 40 is NOT included in the `create_release_crew()` agents list
- [ ] Agent 6 holds a direct reference to Agent 40 and calls it before/after each crew delegation

#### Scenario: Snapshot and restore cycle

- GIVEN the pipeline has run through the Token Engine Crew successfully
- AND a snapshot has been taken at `checkpoints/token-engine/`
- WHEN the Design-to-Code Crew exhausts its 2-attempt retry budget
- THEN `RestoreExecutor.restore("token-engine")` restores the output folder
- AND `reports/rollback-log.json` records the failed crew and the restored phase

#### Scenario: No snapshot available for restore

- GIVEN no snapshot exists for `checkpoints/ds-bootstrap/`
- WHEN a restore for `ds-bootstrap` is requested
- THEN `RestoreExecutor.restore("ds-bootstrap")` raises `FileNotFoundError`
- AND `RollbackReporter` records the failure in `reports/rollback-log.json`

#### Scenario: Checkpoint directory created on first use

- GIVEN `checkpoints/` does not exist in `output_dir`
- WHEN `CheckpointCreator.snapshot("ds-bootstrap")` is called
- THEN `checkpoints/ds-bootstrap/` is created
- AND the output folder state is copied into it

---

### Requirement: Tool — GateStatusReader

`GateStatusReader` MUST read `reports/governance/quality-gates.json` and return a structured dict summarising gate pass/fail counts.

#### Acceptance Criteria

- [ ] `GateStatusReader` is a `crewai.BaseTool` subclass
- [ ] Returns `{"fatal_passed": N, "fatal_failed": N, "warning_passed": N, "warning_failed": N, "gates": [...]}` structure
- [ ] Returns a safe default when the file is absent (all zeros, empty gates list)

---

### Requirement: Tool — VersionCalculator

`VersionCalculator` MUST derive a semver string from gate pass/fail input.

#### Acceptance Criteria

- [ ] `VersionCalculator` is a `crewai.BaseTool` subclass
- [ ] Returns `"v1.0.0"` when `fatal_failed == 0`
- [ ] Returns `"v0.1.0"` when `fatal_failed > 0` and no prior version is in context
- [ ] Returns `"v0.1.0-experimental"` when gate data is absent or malformed

---

### Requirement: Tool — DependencyResolver

`DependencyResolver` MUST wrap `npm install`, `tsc --noEmit`, and `npm test` as subprocess calls with graceful degradation when `npm` is unavailable.

#### Acceptance Criteria

- [ ] `DependencyResolver` is a `crewai.BaseTool` subclass
- [ ] Returns `{"status": "npm_unavailable"}` when `npm` is not on `$PATH`
- [ ] Returns `{"status": "success", "stdout": "..."}` when the command exits 0
- [ ] Returns `{"status": "failed", "exit_code": N, "stderr": "..."}` when the command exits non-zero
- [ ] Never raises an unhandled exception regardless of subprocess outcome
- [ ] Uses `subprocess.run` with a configurable `cwd` parameter

---

### Requirement: Crew-level retry behavior

The Release Crew MUST apply the Phase 4–6 crew-level retry boundary (PRD §3.4): if any task fails, Agent 6 re-runs the entire crew up to **2 attempts**.

#### Acceptance Criteria

- [ ] Phase 4–6 crew failures do not block the pipeline from completing
- [ ] After exhausting 2 retry attempts, the crew is marked `failed` in `reports/generation-summary.json` and the pipeline continues
- [ ] A `final_status` of `"failed"` in `generation-summary.json` does NOT prevent Human Gate 2 from presenting the output review

#### Scenario: Crew fails on first attempt, succeeds on second

- GIVEN the Release Crew's T2 fails on the first attempt (changelog not written)
- WHEN Agent 6 triggers a crew-level retry
- THEN the entire crew re-runs from T1
- AND if T2 succeeds on the second attempt, `final_status` reflects the successful outcome

#### Scenario: Crew exhausts retry budget

- GIVEN the Release Crew fails on both attempts
- WHEN the retry budget is exhausted
- THEN `reports/generation-summary.json` has `final_status: "failed"`
- AND the pipeline continues to Human Gate 2 with partial results
