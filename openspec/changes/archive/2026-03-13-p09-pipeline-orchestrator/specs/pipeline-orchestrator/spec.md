# Specification

## Purpose

This spec governs the pipeline orchestration layer introduced in p09: Agent 6 (First Publish Agent), Agent 40 (Rollback Agent), their supporting tools (`CrewSequencer`, `CheckpointManager`, `ResultAggregator`, `StatusReporter`), the downstream crew stub modules, and the CLI integration that wires Human Gate 1 approval to the full pipeline run and presents Human Gate 2.

---

## Requirements

### Requirement: Agent 6 sequences all 9 crews in the correct phase order

Agent 6's `CrewSequencer` tool SHALL invoke all 8 downstream crews in the phase order defined in PRD §3.1. Phase 3 MUST run Design-to-Code before Component Factory. Phase 4 MUST run Documentation before Governance. Phase 5 crews (AI Semantic Layer and Analytics) have no mutual dependency and MAY run in either order.

Affected crew: **DS Bootstrap Crew** — Agent 6: First Publish Agent (§4.1)

#### Acceptance Criteria

- [ ] `CrewSequencer.run_sequence(output_dir)` invokes crews in this order: Token Engine → Design-to-Code → Component Factory → Documentation → Governance → AI Semantic Layer → Analytics → Release
- [ ] Documentation Crew completes before Governance Crew starts (Phase 4 ordering enforced)
- [ ] Design-to-Code Crew completes before Component Factory Crew starts (Phase 3 ordering enforced)
- [ ] `CrewSequencer` returns a list of `CrewResult` objects in invocation order
- [ ] The sequence is not interruptible mid-phase — a phase always runs to completion or exhausted retries before the next phase starts

#### Scenario: Happy path — all crews succeed

- GIVEN a valid output directory with DS Bootstrap Crew outputs present (brand-profile.json, tokens/*.tokens.json, specs/*.spec.yaml, pipeline-config.json)
- WHEN `CrewSequencer.run_sequence(output_dir)` is called
- THEN all 8 downstream crews are invoked in the correct order
- AND each crew receives the output directory as its working context
- AND a `CrewResult` with `status="success"` is returned for each crew

#### Scenario: Phase 4 ordering enforced

- GIVEN Documentation Crew stub is configured to write `docs/README.md`
- WHEN `CrewSequencer.run_sequence(output_dir)` reaches Phase 4
- THEN Documentation Crew is invoked and completes
- AND only after `docs/README.md` exists does Governance Crew start

#### Scenario: Missing required input causes fail-fast

- GIVEN the `specs/` directory is absent from the output directory
- WHEN `CrewSequencer.run_sequence(output_dir)` is called
- THEN Design-to-Code Crew is NOT invoked
- AND a `CrewResult` with `status="failed"` and `reason="missing_required_input: specs/"` is returned for Design-to-Code Crew
- AND all subsequent phases are skipped

---

### Requirement: CrewSequencer validates crew I/O contracts before each invocation

The `CrewSequencer` tool SHALL check that all required input files for a crew (as defined in PRD §3.6) exist in the output directory before invoking that crew. If any required input file is missing, the crew SHALL NOT be invoked and the sequencer SHALL return a `CrewResult` with `status="failed"`.

#### Acceptance Criteria

- [ ] `CrewSequencer` has a hard-coded I/O contract table matching PRD §3.6 (required reads per crew)
- [ ] Before each crew invocation, all required input paths are checked for existence
- [ ] Missing inputs produce a `CrewResult(status="failed", reason="missing_required_input: <path>")` without invoking the crew
- [ ] Optional inputs (§3.6 "Reads (optional)") do NOT block invocation if absent

#### Scenario: Token Engine Crew — required tokens present

- GIVEN `tokens/base.tokens.json`, `tokens/semantic.tokens.json`, and `tokens/component.tokens.json` all exist in the output directory
- WHEN `CrewSequencer` evaluates preconditions for Token Engine Crew
- THEN Token Engine Crew is invoked

#### Scenario: Token Engine Crew — required token missing

- GIVEN `tokens/semantic.tokens.json` is absent from the output directory
- WHEN `CrewSequencer` evaluates preconditions for Token Engine Crew
- THEN Token Engine Crew is NOT invoked
- AND `CrewResult(status="failed", reason="missing_required_input: tokens/semantic.tokens.json")` is returned

---

### Requirement: CheckpointManager creates and restores phase-boundary snapshots

The `CheckpointManager` tool SHALL snapshot the output directory at each phase boundary. Each snapshot SHALL include all files in the output directory except the `.daf-checkpoints/` subdirectory. Snapshots SHALL be restorable, allowing the pipeline to retry from any phase.

Affected crew: **DS Bootstrap Crew** — Agent 40: Rollback Agent; Agent 6: First Publish Agent (§4.1, §4.8)

#### Acceptance Criteria

- [ ] `CheckpointManager.create(output_dir, phase)` copies all output directory contents (excluding `.daf-checkpoints/`) to `<output_dir>/.daf-checkpoints/<phase>-<iso-timestamp>/`
- [ ] `CheckpointManager.create()` appends an entry to `<output_dir>/.daf-checkpoints/checkpoints.json` with `{phase, timestamp, path, file_manifest: {path: size}}`
- [ ] `CheckpointManager.restore(output_dir, phase)` validates the checkpoint's manifest (all files present, sizes match), then copies checkpoint contents back to `output_dir`
- [ ] `CheckpointManager.restore()` raises `CheckpointCorruptError` if any file is missing or its size differs from the manifest
- [ ] `CheckpointManager.get_last_valid_checkpoint(output_dir)` returns the checkpoint entry for the highest phase number whose manifest passes validation
- [ ] `CheckpointManager.get_last_valid_checkpoint()` returns `None` if no valid checkpoint exists
- [ ] Snapshots do NOT include the `.daf-checkpoints/` directory itself (no recursive nesting)
- [ ] On successful full pipeline completion, `CheckpointManager.cleanup(output_dir)` removes all checkpoints to free disk space

#### Scenario: Snapshot created after Phase 1

- GIVEN a populated output directory containing `brand-profile.json` and `tokens/base.tokens.json`
- WHEN `CheckpointManager.create(output_dir, phase=1)` is called
- THEN a snapshot directory is created at `<output_dir>/.daf-checkpoints/phase-1-<timestamp>/`
- AND `checkpoints.json` contains one entry with `phase=1` and a file manifest listing all copied files
- AND `.daf-checkpoints/` is NOT included in the snapshot

#### Scenario: Corrupt checkpoint detected on restore

- GIVEN a checkpoint at `phase=2` where `tokens/compiled/variables.css` was recorded in the manifest but has since been deleted
- WHEN `CheckpointManager.restore(output_dir, phase=2)` is called
- THEN `CheckpointCorruptError` is raised identifying the missing file

#### Scenario: Resume with no valid checkpoints

- GIVEN `checkpoints.json` lists a checkpoint but all its manifest files are missing
- WHEN `CheckpointManager.get_last_valid_checkpoint(output_dir)` is called
- THEN `None` is returned

---

### Requirement: Agent 6 implements bounded cross-phase retry routing

Agent 6 (First Publish Agent, §4.1) SHALL implement the retry protocol for Phases 1–3 as defined in PRD §3.4. When the Token Validation Agent (8) rejects Token Foundation Agent (2) output, Agent 6 SHALL restore the Phase 1 pre-run checkpoint via the Rollback Agent (40), then re-invoke the Token Foundation Agent task function directly with accumulated rejection context, then re-run the Token Engine Crew. This loop SHALL NOT exceed 3 attempts per rejection boundary. On exhaustion, the component SHALL be marked `failed` and the pipeline SHALL continue.

Affected crews: **DS Bootstrap Crew** (Agent 6), **Token Engine Crew** (Agent 8), via cross-phase retry routing (§3.4)

#### Acceptance Criteria

- [ ] Agent 6 detects a `CrewResult` with `status="rejected"` from Token Engine Crew and extracts the structured rejection (which checks failed, errors, suggested fix)
- [ ] Agent 6 calls `RollbackAgent.restore(checkpoint=pre_phase2)` before each retry
- [ ] Agent 6 calls `run_token_foundation_task(brand_profile, output_dir, retry_context=accumulated_rejections)` with the rejection appended to the context
- [ ] The retry loop is bounded to `pipeline_config.retry.maxComponentRetries` (default 3)
- [ ] After exhausting retries, Agent 6 writes `{"status": "failed", "retries_exhausted": true, "last_rejection": ...}` to `reports/generation-summary.json` for the failing boundary
- [ ] The pipeline continues to Phase 3 even when Phase 1↔2 retries are exhausted
- [ ] Retry context accumulates: attempt N sees rejections from attempts 1 through N-1

#### Scenario: Phase 2 rejects Phase 1 — first retry succeeds

- GIVEN Token Foundation Agent (2) produces a token set with a naming convention violation
- AND Token Validation Agent (8) returns `status="rejected"` with `{failed_checks: ["naming"], ...}`  
- WHEN Agent 6 receives the rejection (attempt 1)
- THEN Agent 6 restores the pre-Phase-2 checkpoint
- AND calls `run_token_foundation_task(..., retry_context=[rejection_1])`
- AND re-runs Token Engine Crew
- AND the corrected token set passes validation
- AND `CrewResult(status="success")` is recorded for Token Engine Crew

#### Scenario: Phase 2 rejects Phase 1 — all retries exhausted

- GIVEN Token Validation Agent (8) rejects Token Foundation output on all 3 attempts
- WHEN the third retry fails
- THEN `generation-summary.json` records `{phase: 2, status: "failed", retries_exhausted: true}`
- AND the pipeline advances to Phase 3 without blocking

#### Scenario: Phases 4–6 crew retry (two-attempt limit)

- GIVEN Documentation Crew (Phase 4a) fails on the first attempt
- WHEN Agent 6 retries the entire Documentation Crew
- THEN on success on the second attempt, `CrewResult(status="success")` is recorded
- AND the pipeline continues to Governance Crew
- AND the retry count for Phase 4 crews is bounded at 2 (not 3)

---

### Requirement: ResultAggregator assembles generation-summary.json

The `ResultAggregator` tool SHALL merge per-crew `CrewResult` objects into a single `reports/generation-summary.json` conforming to the schema expected by the Release Crew (PRD §4.8) and the Output Review gate (PRD §5).

#### Acceptance Criteria

- [ ] `ResultAggregator.aggregate(crew_results, output_dir)` writes `reports/generation-summary.json`
- [ ] The output file contains a top-level `pipeline` key with `status` (`"success"` / `"partial"` / `"failed"`), `started_at`, `completed_at`, `phase_results` (array)
- [ ] Each entry in `phase_results` contains: `phase` (int), `crew` (str), `status`, `retries_used`, `artifacts_written` (list of paths)
- [ ] `pipeline.status` is `"success"` if all crews returned `status="success"` or `status="partial"`; `"partial"` if some Phase 4–6 crews failed; `"failed"` if any Phase 1–3 boundary exhausted retries
- [ ] The function is idempotent — calling it twice overwrites without error

#### Scenario: All crews succeed

- GIVEN 8 `CrewResult` objects all with `status="success"`
- WHEN `ResultAggregator.aggregate(crew_results, output_dir)` is called
- THEN `generation-summary.json` is written with `pipeline.status = "success"`

#### Scenario: Phase 5 analytics crew fails

- GIVEN Analytics Crew returns `CrewResult(status="failed")` but all Phase 1–3 crews succeeded
- WHEN `ResultAggregator.aggregate(...)` is called
- THEN `generation-summary.json` contains `pipeline.status = "partial"`

---

### Requirement: Downstream crew stub modules write minimum required output files

Each of the 8 downstream crew stub modules in `src/daf/crews/` SHALL implement a `create_<crew>_crew(output_dir)` factory function that returns a CrewAI `Crew`. When the crew's task executes, it SHALL write the minimum set of output files defined in the §3.6 "Writes" column for that crew, using empty content or `{"stub": true}` JSON markers. This ensures `CrewSequencer` I/O contract checks pass for downstream phases.

#### Acceptance Criteria

- [ ] `src/daf/crews/token_engine.py` exports `create_token_engine_crew(output_dir)` returning a `Crew`
- [ ] `src/daf/crews/design_to_code.py` exports `create_design_to_code_crew(output_dir)` returning a `Crew`
- [ ] `src/daf/crews/component_factory.py` exports `create_component_factory_crew(output_dir)` returning a `Crew`
- [ ] `src/daf/crews/documentation.py` exports `create_documentation_crew(output_dir)` returning a `Crew`
- [ ] `src/daf/crews/governance.py` exports `create_governance_crew(output_dir)` returning a `Crew`
- [ ] `src/daf/crews/ai_semantic_layer.py` exports `create_ai_semantic_layer_crew(output_dir)` returning a `Crew`
- [ ] `src/daf/crews/analytics.py` exports `create_analytics_crew(output_dir)` returning a `Crew`
- [ ] `src/daf/crews/release.py` exports `create_release_crew(output_dir)` returning a `Crew`
- [ ] When each stub crew runs, it writes all files listed in the §3.6 "Writes" column for that crew
- [ ] Stub output files are either empty text files or `{"stub": true}` JSON; they are NOT valid design system artifacts

#### Scenario: Token Engine stub writes required outputs

- GIVEN a valid output directory with raw token files
- WHEN `create_token_engine_crew(output_dir)` returns a crew and `crew.kickoff()` is called
- THEN `tokens/compiled/` directory is created with at minimum `variables.css` and `variables-light.css`
- AND `tokens/diff.json` exists

---

### Requirement: CLI wires Human Gate 1 to pipeline execution and presents Human Gate 2

The `daf init` command SHALL present Human Gate 1 (Brand Profile approval) before starting Agent 6's orchestration. After Agent 6 completes, the CLI SHALL present Human Gate 2 (Output Review) by displaying the `generation-summary.json` summary and prompting the user to approve or select a re-run option (PRD §5).

#### Acceptance Criteria

- [ ] After Brand Profile approval at Gate 1, `daf init` calls `run_first_publish_agent(output_dir)` which executes Agent 6's orchestration task
- [ ] `daf init --resume <output-dir>` invokes `CheckpointManager.get_last_valid_checkpoint(output_dir)` and resumes from the next phase without re-running Phase 1
- [ ] `daf init --resume <output-dir>` with no valid checkpoints prints an informative error and prompts for full restart
- [ ] After Agent 6 completes, the CLI displays a Gate 2 summary including: pipeline status, components passed/failed, quality scores, known issues
- [ ] Gate 2 prompts the user for: `[A]pprove`, `[R]e-run full pipeline`, `[P]hase re-run (specify phase)`, `[C]omponent re-run (specify names)`
- [ ] Selecting `A` exits with code 0
- [ ] Selecting `R` re-runs from Phase 1 (calls `daf init` with same profile)
- [ ] Gate 2 prompt response is non-destructive — the output folder is not modified until the user selects an action

#### Scenario: Happy path — approve at Gate 2

- GIVEN the pipeline completes with `pipeline.status = "success"`
- AND the CLI displays the Gate 2 summary
- WHEN the user enters `A`
- THEN the CLI prints `Design system generation complete. Output ready at <output_dir>.`
- AND exits with code 0

#### Scenario: Resume from valid checkpoint

- GIVEN a previous run reached Phase 3 before crashing, and a valid Phase 3 checkpoint exists
- WHEN `daf init --resume <output-dir>` is called
- THEN `CheckpointManager.get_last_valid_checkpoint()` returns the Phase 3 checkpoint
- AND Agent 6's `CrewSequencer` starts from Phase 4 (Documentation Crew)
- AND Phases 1–3 are NOT re-run

#### Scenario: Resume with no checkpoints — prompt for restart

- GIVEN `daf init --resume /path/to/output` is called
- AND `.daf-checkpoints/checkpoints.json` does not exist or all checkpoints are corrupt
- WHEN `CheckpointManager.get_last_valid_checkpoint()` returns `None`
- THEN the CLI prints: `No valid checkpoints found at /path/to/output. Run 'daf init' to start a new generation.`
- AND exits with code 1
