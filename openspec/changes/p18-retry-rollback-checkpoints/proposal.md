# Proposal: p18-retry-rollback-checkpoints

## Intent

The retry, rollback, and checkpoint machinery in the DAF pipeline has four implementation gaps relative to the PRD specification. These gaps are latent bugs that will cause data corruption or incorrect resume behaviour the first time the pipeline encounters a real failure in production:

1. **Pre-crew checkpoint gap (§3.4):** The PRD requires the Rollback Agent to snapshot the output folder _before every crew run_. The `_run_simple_crew` helper (used by Design-to-Code and Component Factory in Phases 2–3) creates no checkpoint before execution. If either crew fails there is no clean state to restore to.

2. **Pre-retry restore gap (§3.4):** `_run_with_retry` (Phases 4–6) does not restore a checkpoint before re-running a failed crew. A failed run may leave partial or corrupt artifacts; the retry executes on top of that corrupt state instead of a known-good snapshot.

3. **Rollback cascade not enforced (§3.4):** The PRD states that restoring a checkpoint must cascade forward — all phases after the restored phase are invalidated and re-run from scratch. Currently, when `_run_phase13_crew` restores a Phase 0 checkpoint and re-invokes the token foundation task, no mechanism prevents a downstream crew from reading stale Phase 2–3 artifacts left over from the previous (failed) attempt.

4. **Resume without restore (§3.4, CLI):** The `--resume` path in `cli.py` calls `run_first_publish_agent(resume, start_phase=N)` without first restoring the corresponding checkpoint snapshot. If the process crashed mid-phase, the output directory may be in a partial state; re-running from phase N atop that partial state is unsafe. The PRD says resume re-runs failed phases "from scratch with a clean slate."

These gaps do not affect the current test suite (which mocks checkpoint calls) but will cause incorrect behaviour in end-to-end runs. Before the pipeline can be used against real brand profiles, these four behaviours must match the specification exactly.

## Scope

### In scope

- Add a pre-run checkpoint call to `_run_simple_crew` using `CheckpointManager.create()` before each crew's `kickoff()`, with a per-crew phase mapping.
- Add a checkpoint restore in `_run_with_retry` before each retry attempt, restoring to the checkpoint created at the start of the most recent attempt's phase.
- Implement the rollback cascade invariant: introduce a `_cascade_invalidate(output_dir, from_phase)` helper that deletes phase-boundary artifacts for all phases > `from_phase`, ensuring stale artifacts are not silently reused after a rollback.
- Fix the `--resume` path in `cli.py` to call `CheckpointManager().restore()` before invoking `run_first_publish_agent`, so the output directory matches the last valid snapshot before re-running.
- Add unit tests for each of the four scenarios (TDD: red-green cycle).

### Out of scope

- Changes to the LLM-facing `Rollback Agent (40)` role, backstory, or tool list.
- Changes to `CheckpointCreator` or `RestoreExecutor` (Agent 40's tools) — they remain separate from `CheckpointManager`.
- The dual-checkpoint-system concern (CheckpointCreator vs CheckpointManager) — unifying them is a separate, larger refactor.
- Changes to any crew implementation (Token Engine, Design-to-Code, Component Factory, Documentation, Governance, AI Semantic Layer, Analytics, Release).
- Changes to Human Gate behaviour or the Brand Profile interview flow.
- Changes to the retry budget constants (`MAX_PHASE13_RETRIES`, `MAX_PHASE46_RETRIES`).

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| DS Bootstrap | Agent 6 – First Publish Agent | `run_first_publish_agent` gains pre-crew checkpoints; `_run_simple_crew` and `_run_with_retry` helpers updated; cascade invalidation added |
| DS Bootstrap | Agent 6 – First Publish Agent (resume path) | `cli.py` `daf init --resume` path restores checkpoint before re-running |
| Release | Agent 40 – Rollback Agent | No code change; behaviour now correctly exercised by Agent 6's calling pattern |

## PRD References

- §3.4 — Retry protocol: "Before each crew runs, the Rollback Agent snapshots the current output folder state."
- §3.4 — Rollback cascade policy: "When a checkpoint is restored, all crews after the restored phase are invalidated and must re-run."
- §3.4 — Resume-on-failure: "Resume does not retry the failed phase automatically — it re-runs it from scratch with a clean slate."
- §3.4 — Post-rollback: "The First Publish Agent (6) enforces this — it never resumes mid-sequence after a rollback."

## Pipeline Impact

- [ ] Pipeline phase ordering
- [ ] Crew I/O contracts (§3.6)
- [x] Retry protocol (§3.4) — fixes four gaps between spec and implementation
- [ ] Human gate policy (§5)
- [ ] Exit criteria (§8)
- [ ] Brand Profile schema (§6)

## Approach

1. **`_run_simple_crew` pre-run checkpoint**: Pass `cm: CheckpointManager` and a `phase` int into `_run_simple_crew`. At the start of the function, call `cm.create(output_dir, phase)` before `crew.kickoff()`. Wire the call sites in `run_first_publish_agent` with the appropriate phase numbers (Phase 2 for both Design-to-Code and Component Factory pre-snapshots).

2. **`_run_with_retry` pre-retry restore**: Pass `cm: CheckpointManager` and `phase` into `_run_with_retry`. At the top of each retry loop iteration, call `cm.create(output_dir, phase)` on the first attempt. On subsequent attempts (after a failure), call `cm.restore(output_dir, phase)` to reset to the snapshot taken before the first attempt, then re-run.

3. **Cascade invalidation**: Add `_cascade_invalidate(output_dir: str, from_phase: int) -> None` to `first_publish.py`. The function removes phase-boundary artifact directories for phases greater than `from_phase` from the output directory. Called by `_run_phase13_crew` after a checkpoint restore, and by `_run_with_retry` after a restore.

4. **CLI resume restore**: In `cli.py`, after finding the last valid checkpoint via `CheckpointManager().get_last_valid_checkpoint()`, call `cm.restore(output_dir=resume, phase=checkpoint["phase"])` before `run_first_publish_agent(resume, start_phase=checkpoint["phase"] + 1)`.

## Risks

- **Phase number mapping**: `_run_simple_crew` currently has no phase parameter. Assigning the wrong phase number to a crew could restore to an earlier checkpoint than intended. Mitigate by defining a `_CREW_PHASE_MAP` constant in `first_publish.py` that canonically maps crew names to phase integers.
- **Cascade invalidation too aggressive**: Deleting phase-boundary artifacts in a cascade wipes completed upstream work incorrectly if the phase mapping is wrong. Mitigate with narrow, path-specific deletion (only well-known phase artefact directories) and thorough unit tests.
- **Checkpoint storage cost**: Creating a checkpoint before every crew (9 crews) means 9 snapshots per run. For a Standard-scope design system (~30 files, ~5 MB total), this adds ~45 MB of checkpoint storage. Acceptable given the checkpoint cleanup after success; document the tradeoff.
