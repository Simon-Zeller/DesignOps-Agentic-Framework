# Specification: retry-rollback-checkpoints

## Purpose

Defines the behavioral requirements for the retry, rollback, and checkpoint subsystems in the DAF pipeline orchestration layer (`run_first_publish_agent` in Agent 6 – First Publish Agent, DS Bootstrap Crew). Covers four correctness gaps identified in p18: pre-crew checkpointing, pre-retry restoration, rollback cascade invalidation, and CLI resume correctness.

## Requirements

---

### Requirement: PRE-CREW-CHECKPOINT — Checkpoint before every crew run

Agent 6 (First Publish Agent, DS Bootstrap Crew) MUST create a `CheckpointManager` snapshot of the output directory before every crew's `kickoff()` call, including Design-to-Code and Component Factory crews (currently using `_run_simple_crew` with no checkpoint).

#### Acceptance Criteria

- [ ] `CheckpointManager.create()` is called before `kickoff()` in `_run_simple_crew`
- [ ] The checkpoint phase number follows `_CREW_PHASE_MAP` in `first_publish.py`
- [ ] Design-to-Code crew gets a pre-run checkpoint at Phase 2
- [ ] Component Factory crew gets a pre-run checkpoint at Phase 2 (or its canonical phase mapping)
- [ ] The snapshot directory is not empty when output_dir contains files

#### Scenario: Design-to-Code crew happy path

- GIVEN the pipeline has completed Phase 1 (Token Engine) and output_dir contains token files
- WHEN `_run_simple_crew("design_to_code", ...)` is called
- THEN a checkpoint snapshot is created in `.daf-checkpoints/phase-2-*/` before `crew.kickoff()` executes
- AND the snapshot contains all current token files

#### Scenario: Component Factory crew happy path

- GIVEN Phase 2 (Design-to-Code) has completed and output_dir contains component source files
- WHEN `_run_simple_crew("component_factory", ...)` is called
- THEN a checkpoint snapshot is created before `crew.kickoff()` executes

#### Scenario: Crew kickoff still called after checkpoint creation

- GIVEN `_run_simple_crew` is called
- WHEN `CheckpointManager.create()` succeeds
- THEN `crew.kickoff()` is still executed (checkpoint is pre-run, not a replacement)

---

### Requirement: PRE-RETRY-RESTORE — Restore checkpoint before each retry attempt (Phases 4–6)

Agent 6 (First Publish Agent, DS Bootstrap Crew) MUST restore a checkpoint snapshot before each retry attempt in `_run_with_retry` (Phases 4–6). The snapshot used for restore MUST be the one created at the start of the first attempt for that crew.

#### Acceptance Criteria

- [ ] `_run_with_retry` creates a checkpoint at the start of attempt 1
- [ ] `_run_with_retry` calls `CheckpointManager.restore()` before each retry attempt (attempt 2+)
- [ ] `_cascade_invalidate(output_dir, phase)` is called after `restore()` and before `crew.kickoff()`
- [ ] The restored state reflects the output_dir state at the start of attempt 1, not an earlier phase
- [ ] On success (no retry needed), the checkpoint is left in place and not restored

#### Scenario: Phase 4 Documentation crew fails once and succeeds on retry

- GIVEN Phase 3 (Component Factory) has completed and `cm.create(phase=4)` was called before attempt 1
- WHEN `documentation` crew kickoff fails on attempt 1
- THEN `cm.restore(phase=4)` is called before attempt 2
- AND `_cascade_invalidate(output_dir, 4)` removes any Phase 4+ partial artifacts
- AND the documentation crew's `kickoff()` executes again on the clean state

#### Scenario: Phase 5 crew exhausts all retries

- GIVEN `max_retries=2` for Phase 5 crew
- WHEN both attempts fail
- THEN `cm.restore()` is called once (before attempt 2 only)
- AND the result has `status="failed"` and `retries_exhausted=True`
- AND the failure is non-fatal (pipeline continues per §3.4)

#### Scenario: Phase 4 crew succeeds on first attempt

- GIVEN Phase 4 crew's `kickoff()` returns success
- WHEN attempt 1 succeeds
- THEN `cm.restore()` is NOT called
- AND the crew result has `status="success"` and `retries_used=0`

---

### Requirement: CASCADE-INVALIDATION — Forward cascade after rollback

Agent 6 (First Publish Agent, DS Bootstrap Crew) MUST call `_cascade_invalidate(output_dir, from_phase)` after any checkpoint restore, ensuring all phase-boundary artifacts produced by phases > `from_phase` are removed before the restarted crew runs.

#### Acceptance Criteria

- [ ] `_cascade_invalidate(output_dir, from_phase)` exists in `first_publish.py`
- [ ] It removes artifact directories for all phases > `from_phase`, per `_PHASE_ARTIFACT_DIRS`
- [ ] It does NOT remove the `.daf-checkpoints/` directory itself
- [ ] It does NOT remove artifacts belonging to phases ≤ `from_phase`
- [ ] If a directory listed in `_PHASE_ARTIFACT_DIRS` does not exist, it is silently skipped (no error)
- [ ] `_cascade_invalidate` is called in `_run_phase13_crew` after Phase 0 checkpoint restore
- [ ] `_cascade_invalidate` is called in `_run_with_retry` after each retry restore

#### Scenario: Rollback to Phase 0 in cross-phase retry (Token Engine → Token Validation)

- GIVEN Phase 1 crew was rejected by Token Validation and Phase 2 partial artifacts exist in output_dir
- WHEN `_run_phase13_crew` restores the Phase 0 checkpoint
- THEN `_cascade_invalidate(output_dir, 0)` removes Phase 1+ artifact directories
- AND the Token Foundation task is re-invoked on a clean output_dir

#### Scenario: Phase 4 retry cascade

- GIVEN Phase 4 Documentation crew failed and `cm.restore(phase=4)` was called
- WHEN `_cascade_invalidate(output_dir, 4)` is called
- THEN Phase 4 partial documentation artifacts in `docs/` are removed
- AND Phase 1–3 artifacts (tokens, components) are preserved

#### Scenario: Target directory does not exist

- GIVEN `_cascade_invalidate(output_dir, 3)` is called
- WHEN a Phase 4+ artifact directory listed in `_PHASE_ARTIFACT_DIRS` does not exist in output_dir
- THEN no exception is raised
- AND all other listed directories that do exist are removed

---

### Requirement: RESUME-RESTORE — Restore checkpoint before resuming pipeline

The CLI `daf init --resume <output_dir>` MUST restore the last valid checkpoint to the output directory before invoking `run_first_publish_agent`, ensuring the resumed phase starts from a clean known-good state.

#### Acceptance Criteria

- [ ] After `CheckpointManager.get_last_valid_checkpoint()` returns a valid entry, `cm.restore(output_dir, phase)` is called before `run_first_publish_agent`
- [ ] `run_first_publish_agent` is invoked with `start_phase=checkpoint["phase"] + 1` (unchanged from current)
- [ ] If `cm.restore()` raises `CheckpointCorruptError`, the CLI prints a clear error and exits with a non-zero code
- [ ] If `get_last_valid_checkpoint()` returns `None`, the CLI still prints "No valid checkpoints found" and exits (unchanged from current)

#### Scenario: Successful resume from Phase 3 checkpoint

- GIVEN the pipeline crashed mid-Phase 4 and a valid Phase 3 checkpoint exists in `.daf-checkpoints/`
- WHEN the user runs `daf init --resume ./my-design-system`
- THEN `CheckpointManager.restore()` is called with `phase=3`
- AND the output directory is reset to its Phase 3 state
- AND `run_first_publish_agent` is called with `start_phase=4`

#### Scenario: Resume with corrupt checkpoint

- GIVEN a Phase 2 checkpoint exists but its manifest files are missing from the snapshot
- WHEN the user runs `daf init --resume ./my-design-system`
- THEN `cm.restore()` raises `CheckpointCorruptError`
- AND the CLI prints an error message instructing the user to restart from Phase 1
- AND the CLI exits with a non-zero exit code

#### Scenario: Resume with no checkpoints

- GIVEN the output directory contains no `.daf-checkpoints/` directory
- WHEN the user runs `daf init --resume ./my-design-system`
- THEN `get_last_valid_checkpoint()` returns `None`
- AND the CLI prints "No valid checkpoints found" (existing behavior, unchanged)
