# TDD Plan: p09-pipeline-orchestrator

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

All new code uses **pytest** (the project's existing test framework). Tests are arranged in three tiers:

- **Unit tests** — test each tool in isolation using a temporary directory (`tmp_path` fixture). No CrewAI `Crew.kickoff()` calls; stub implementations are invoked via their Python factory functions.
- **Integration tests** — test Agent 6's `CrewSequencer` end-to-end across all 8 stub crews using a populated `tmp_path` output directory. CrewAI agents are mocked at the `Agent.execute_task()` boundary to avoid LLM calls in CI.
- **CLI integration tests** — test `daf init --resume` via Typer's `CliRunner` with a pre-populated checkpoint directory.

No visual or accessibility tests apply to this change (no UI components are generated here). Coverage target: ≥80% line coverage per PRD quality gate, ≥70% branch coverage.

---

## Test Cases

### CheckpointManager

#### Test: `test_checkpoint_create_writes_snapshot_and_manifest`

- **Maps to:** Requirement "CheckpointManager creates and restores phase-boundary snapshots" → Scenario "Snapshot created after Phase 1"
- **Type:** unit
- **Given:** A `tmp_path` output directory containing `brand-profile.json` and `tokens/base.tokens.json`
- **When:** `CheckpointManager.create(output_dir=tmp_path, phase=1)` is called
- **Then:** A directory `tmp_path/.daf-checkpoints/phase-1-<timestamp>/` exists containing `brand-profile.json` and `tokens/base.tokens.json`; `checkpoints.json` has one entry with `phase=1`, a non-empty `file_manifest`
- **File:** `tests/test_checkpoint_manager.py`

#### Test: `test_checkpoint_does_not_include_checkpoints_dir`

- **Maps to:** Requirement "CheckpointManager ..." → Acceptance Criteria "Snapshots do NOT include `.daf-checkpoints/`"
- **Type:** unit
- **Given:** An output directory that already has a `.daf-checkpoints/` directory from a prior run
- **When:** `CheckpointManager.create(output_dir, phase=2)` is called
- **Then:** The new snapshot does NOT contain a `.daf-checkpoints/` subdirectory
- **File:** `tests/test_checkpoint_manager.py`

#### Test: `test_checkpoint_restore_overwrites_output_dir`

- **Maps to:** Requirement "CheckpointManager ..." → Scenario "Corrupt checkpoint detected on restore" (inverse — valid restore)
- **Type:** unit
- **Given:** A snapshot at `phase=1` with `brand-profile.json` containing `{"name": "Original"}`; `brand-profile.json` in `output_dir` has since been overwritten with `{"name": "Modified"}`
- **When:** `CheckpointManager.restore(output_dir, phase=1)` is called
- **Then:** `output_dir/brand-profile.json` contains `{"name": "Original"}`
- **File:** `tests/test_checkpoint_manager.py`

#### Test: `test_checkpoint_restore_raises_on_corrupt`

- **Maps to:** Requirement "CheckpointManager ..." → Scenario "Corrupt checkpoint detected on restore"
- **Type:** unit
- **Given:** A checkpoint manifest records `tokens/compiled/variables.css` but that file has been deleted from the snapshot directory
- **When:** `CheckpointManager.restore(output_dir, phase=2)` is called
- **Then:** `CheckpointCorruptError` is raised with a message identifying `tokens/compiled/variables.css`
- **File:** `tests/test_checkpoint_manager.py`

#### Test: `test_get_last_valid_checkpoint_returns_highest_valid_phase`

- **Maps to:** Requirement "CheckpointManager ..." → Scenario "Resume with no valid checkpoints" (inverse — with valid checkpoints)
- **Type:** unit
- **Given:** Checkpoints exist for phases 1, 2, and 3; phase 2 snapshot is corrupt (a manifest file is deleted); phases 1 and 3 are intact
- **When:** `CheckpointManager.get_last_valid_checkpoint(output_dir)` is called
- **Then:** Returns the phase 3 checkpoint entry
- **File:** `tests/test_checkpoint_manager.py`

#### Test: `test_get_last_valid_checkpoint_returns_none_when_all_corrupt`

- **Maps to:** Requirement "CheckpointManager ..." → Scenario "Resume with no valid checkpoints"
- **Type:** unit
- **Given:** `checkpoints.json` lists one entry but all manifest files are missing from the snapshot
- **When:** `CheckpointManager.get_last_valid_checkpoint(output_dir)` is called
- **Then:** `None` is returned
- **File:** `tests/test_checkpoint_manager.py`

#### Test: `test_checkpoint_cleanup_removes_all_snapshots`

- **Maps to:** Requirement "CheckpointManager ..." → Acceptance Criteria "On successful completion, `cleanup()` removes all checkpoints"
- **Type:** unit
- **Given:** Three snapshots exist at phases 1, 2, 3
- **When:** `CheckpointManager.cleanup(output_dir)` is called
- **Then:** `tmp_path/.daf-checkpoints/` no longer exists
- **File:** `tests/test_checkpoint_manager.py`

---

### CrewSequencer

#### Test: `test_crew_sequencer_invokes_all_eight_crews_in_order`

- **Maps to:** Requirement "Agent 6 sequences all 9 crews" → Scenario "Happy path — all crews succeed"
- **Type:** integration
- **Given:** An output directory populated with DS Bootstrap outputs (brand-profile.json, tokens/*.tokens.json, specs/*.spec.yaml, pipeline-config.json); all 8 stub crews patched to record invocation order and write minimum outputs
- **When:** `CrewSequencer.run_sequence(output_dir)` is called
- **Then:** Returns a list of 8 `CrewResult` objects; invocation order matches: Token Engine, Design-to-Code, Component Factory, Documentation, Governance, AI Semantic Layer, Analytics, Release
- **File:** `tests/test_crew_sequencer.py`

#### Test: `test_crew_sequencer_enforces_documentation_before_governance`

- **Maps to:** Requirement "Agent 6 sequences all 9 crews" → Scenario "Phase 4 ordering enforced"
- **Type:** integration
- **Given:** All stub crews configured
- **When:** `CrewSequencer.run_sequence(output_dir)` is called
- **Then:** Documentation Crew's completion timestamp is strictly less than Governance Crew's start timestamp
- **File:** `tests/test_crew_sequencer.py`

#### Test: `test_crew_sequencer_fails_fast_on_missing_input`

- **Maps to:** Requirement "CrewSequencer validates crew I/O contracts" → Scenario "Token Engine Crew — required token missing"
- **Type:** unit
- **Given:** An output directory where `tokens/semantic.tokens.json` is absent
- **When:** `CrewSequencer.run_sequence(output_dir)` is called
- **Then:** Returns a list where Token Engine Crew has `CrewResult(status="failed", reason="missing_required_input: tokens/semantic.tokens.json")`; Design-to-Code and all subsequent crews have `status="skipped"`
- **File:** `tests/test_crew_sequencer.py`

#### Test: `test_crew_sequencer_optional_inputs_do_not_block`

- **Maps to:** Requirement "CrewSequencer validates crew I/O contracts" → Acceptance Criteria "Optional inputs do NOT block invocation"
- **Type:** unit
- **Given:** An output directory where `tokens/diff.json` (optional read for Documentation Crew) is absent but all required inputs exist
- **When:** `CrewSequencer.run_sequence(output_dir)` reaches Documentation Crew
- **Then:** Documentation Crew is invoked successfully
- **File:** `tests/test_crew_sequencer.py`

---

### ResultAggregator

#### Test: `test_result_aggregator_all_success_writes_summary`

- **Maps to:** Requirement "ResultAggregator assembles generation-summary.json" → Scenario "All crews succeed"
- **Type:** unit
- **Given:** 8 `CrewResult` objects all with `status="success"`, `retries_used=0`, non-empty `artifacts_written`
- **When:** `ResultAggregator.aggregate(crew_results, output_dir)` is called
- **Then:** `reports/generation-summary.json` is written; `pipeline.status == "success"`; `phase_results` has 8 entries
- **File:** `tests/test_result_aggregator.py`

#### Test: `test_result_aggregator_phase56_failure_yields_partial`

- **Maps to:** Requirement "ResultAggregator ..." → Scenario "Phase 5 analytics crew fails"
- **Type:** unit
- **Given:** 7 `CrewResult` objects with `status="success"`, Analytics Crew with `status="failed"`
- **When:** `ResultAggregator.aggregate(...)` is called
- **Then:** `pipeline.status == "partial"`
- **File:** `tests/test_result_aggregator.py`

#### Test: `test_result_aggregator_phase13_failure_yields_failed`

- **Maps to:** Requirement "ResultAggregator ..." → Acceptance Criteria "`pipeline.status` is `"failed"` if any Phase 1–3 boundary exhausted retries"
- **Type:** unit
- **Given:** Token Engine Crew returns `CrewResult(status="failed", retries_used=3, retries_exhausted=True)`
- **When:** `ResultAggregator.aggregate(...)` is called
- **Then:** `pipeline.status == "failed"`
- **File:** `tests/test_result_aggregator.py`

#### Test: `test_result_aggregator_is_idempotent`

- **Maps to:** Requirement "ResultAggregator ..." → Acceptance Criteria "Calling twice overwrites without error"
- **Type:** unit
- **Given:** `reports/generation-summary.json` already exists
- **When:** `ResultAggregator.aggregate(...)` is called again with different results
- **Then:** No exception is raised; the file is overwritten with the new content
- **File:** `tests/test_result_aggregator.py`

---

### Agent 6 — Retry Routing

#### Test: `test_first_publish_agent_retries_phase2_on_rejection`

- **Maps to:** Requirement "Agent 6 implements bounded cross-phase retry routing" → Scenario "Phase 2 rejects Phase 1 — first retry succeeds"
- **Type:** integration
- **Given:** Token Engine Crew stub returns `CrewResult(status="rejected", rejection={...})` on first call and `CrewResult(status="success")` on second call
- **When:** `run_first_publish_agent(output_dir)` is called
- **Then:** `CheckpointManager.restore()` is called once (before the retry); `run_token_foundation_task()` is called with the rejection in `retry_context`; the second Token Engine invocation returns success
- **File:** `tests/test_first_publish_agent.py`

#### Test: `test_first_publish_agent_marks_failed_after_three_retries`

- **Maps to:** Requirement "Agent 6 implements bounded cross-phase retry routing" → Scenario "Phase 2 rejects Phase 1 — all retries exhausted"
- **Type:** integration
- **Given:** Token Engine Crew stub always returns `status="rejected"` (3 times)
- **When:** `run_first_publish_agent(output_dir)` is called
- **Then:** `generation-summary.json` records `{phase: 2, status: "failed", retries_exhausted: true}`; the pipeline continues and invokes Design-to-Code Crew
- **File:** `tests/test_first_publish_agent.py`

#### Test: `test_first_publish_agent_phases46_crew_retry_bounded_at_two`

- **Maps to:** Requirement "Agent 6 ..." → Scenario "Phases 4–6 crew retry (two-attempt limit)"
- **Type:** integration
- **Given:** Documentation Crew stub fails on first call, succeeds on second
- **When:** `run_first_publish_agent(output_dir)` runs Phase 4
- **Then:** Documentation Crew is called exactly twice; Governance Crew starts after Documentation succeeds; retry count in `generation-summary.json` for Documentation Crew is `1`
- **File:** `tests/test_first_publish_agent.py`

#### Test: `test_first_publish_agent_retry_context_accumulates`

- **Maps to:** Requirement "Agent 6 ..." → Acceptance Criteria "Retry context accumulates: attempt N sees rejections 1 through N-1"
- **Type:** unit (with mock for `run_token_foundation_task`)
- **Given:** Token Engine Crew rejects twice with different rejection objects (`rejection_1`, `rejection_2`)
- **When:** The third call to `run_token_foundation_task()` is captured
- **Then:** The `retry_context` argument contains both `rejection_1` and `rejection_2`
- **File:** `tests/test_first_publish_agent.py`

---

### Crew Stubs

#### Test: `test_token_engine_stub_writes_required_outputs`

- **Maps to:** Requirement "Downstream crew stub modules write minimum required output files" → Scenario "Token Engine stub writes required outputs"
- **Type:** unit
- **Given:** A `tmp_path` output directory with raw token files
- **When:** `create_token_engine_crew(output_dir).kickoff()` is called
- **Then:** `tokens/compiled/variables.css`, `tokens/compiled/variables-light.css`, and `tokens/diff.json` all exist in `output_dir`
- **File:** `tests/test_crew_stubs.py`

#### Test: `test_all_crew_stubs_write_minimum_outputs`

- **Maps to:** Requirement "Downstream crew stub modules ..." → Acceptance Criteria (all crews)
- **Type:** integration (parametrized)
- **Given:** Each crew stub's required input files are pre-populated in `tmp_path`
- **When:** `create_<crew>_crew(output_dir).kickoff()` is called for each of the 8 stubs (parametrized)
- **Then:** All files listed in the §3.6 "Writes" column for that crew are present in `output_dir`
- **File:** `tests/test_crew_stubs.py`

---

### CLI Integration

#### Test: `test_cli_resume_from_valid_checkpoint`

- **Maps to:** Requirement "CLI wires Human Gate 1 ..." → Scenario "Resume from valid checkpoint"
- **Type:** integration
- **Given:** A `tmp_path` output directory with a valid Phase 3 checkpoint (all 3 phase checkpoints written, manifests intact); `first_publish_agent` is patched to record which phase it starts from
- **When:** `CliRunner().invoke(app, ["init", "--resume", str(tmp_path)])` is called
- **Then:** Agent 6's `CrewSequencer` starts from Phase 4; Phases 1–3 are not re-invoked
- **File:** `tests/test_cli_init.py`

#### Test: `test_cli_resume_no_checkpoints_exits_nonzero`

- **Maps to:** Requirement "CLI wires Human Gate 1 ..." → Scenario "Resume with no checkpoints — prompt for restart"
- **Type:** integration
- **Given:** A `tmp_path` output directory with no `.daf-checkpoints/` directory
- **When:** `CliRunner().invoke(app, ["init", "--resume", str(tmp_path)])` is called
- **Then:** Exit code is 1; stdout contains `"No valid checkpoints found"`
- **File:** `tests/test_cli_init.py`

#### Test: `test_cli_gate2_approve_exits_zero`

- **Maps to:** Requirement "CLI wires Human Gate 1 ..." → Scenario "Happy path — approve at Gate 2"
- **Type:** integration
- **Given:** `run_first_publish_agent` is patched to return a successful result; user input is `"A\n"`
- **When:** `CliRunner().invoke(app, ["init"], input="A\n")` is called (post-Gate-1 approval)
- **Then:** Exit code is 0; stdout contains `"Design system generation complete"`
- **File:** `tests/test_cli_init.py`

---

## Edge Case Tests

#### Test: `test_checkpoint_manager_handles_empty_output_dir`

- **Maps to:** Requirement "CheckpointManager ..." → edge case: empty directory
- **Type:** unit
- **Given:** An empty `tmp_path` directory
- **When:** `CheckpointManager.create(output_dir, phase=1)` is called
- **Then:** Snapshot directory is created (empty); manifest has zero files; no exception
- **File:** `tests/test_checkpoint_manager.py`

#### Test: `test_crew_sequencer_empty_required_input_list_does_not_block`

- **Maps to:** Requirement "CrewSequencer validates crew I/O contracts" — edge case: crew has no required inputs
- **Type:** unit
- **Given:** A hypothetical crew entry with an empty required-input list
- **When:** `CrewSequencer` evaluates preconditions
- **Then:** Crew is invoked without contract failure
- **File:** `tests/test_crew_sequencer.py`

#### Test: `test_result_aggregator_empty_crew_result_list_raises`

- **Maps to:** Requirement "ResultAggregator ..." — edge case: no results passed
- **Type:** unit
- **Given:** An empty list of `CrewResult` objects
- **When:** `ResultAggregator.aggregate([], output_dir)` is called
- **Then:** `ValueError` is raised with a descriptive message
- **File:** `tests/test_result_aggregator.py`

#### Test: `test_first_publish_agent_instantiates_rollback_agent_at_start`

- **Maps to:** Design decision "Agent 40 is instantiated by Agent 6 at pipeline start, before any crew runs"
- **Type:** unit
- **Given:** `rollback.create_rollback_agent()` is patched with a spy
- **When:** `run_first_publish_agent(output_dir)` is called
- **Then:** `create_rollback_agent()` is called exactly once, before the first `CrewSequencer.run_sequence()` invocation
- **File:** `tests/test_first_publish_agent.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Line coverage | ≥80% | PRD quality gate requirement |
| Branch coverage | ≥70% | Covers retry routing conditionals and checkpoint validation paths |
| A11y rules passing | N/A | No UI components in this change |

---

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_checkpoint_manager.py` | new | Unit tests for `CheckpointManager` tool |
| `tests/test_crew_sequencer.py` | new | Unit + integration tests for `CrewSequencer` tool |
| `tests/test_result_aggregator.py` | new | Unit tests for `ResultAggregator` tool |
| `tests/test_first_publish_agent.py` | new | Integration tests for Agent 6 orchestration and retry logic |
| `tests/test_crew_stubs.py` | new | Parametrized tests verifying all 8 stub crews write minimum outputs |
| `tests/test_cli_init.py` | modified | Add `--resume` flag tests and Gate 2 prompt tests |
