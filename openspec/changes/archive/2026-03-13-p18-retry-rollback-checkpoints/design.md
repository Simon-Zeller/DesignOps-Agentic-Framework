# Design: p18-retry-rollback-checkpoints

## Technical Approach

Four targeted changes to `src/daf/agents/first_publish.py` and `src/daf/cli.py` close the gaps between the PRD §3.4 specification and the current implementation:

1. **`_run_simple_crew` — pre-run checkpoint**: Add `cm: CheckpointManager` and `phase: int` parameters. Call `cm.create(output_dir, phase)` before `crew.kickoff()` so a clean-state snapshot exists before every Phase 2–3 crew executes.

2. **`_run_with_retry` — pre-retry restore**: Add `cm: CheckpointManager` and `phase: int` parameters. On the first attempt, call `cm.create(output_dir, phase)`. On each subsequent attempt (after a failure), call `cm.restore(output_dir, phase)` followed by `_cascade_invalidate(output_dir, phase)` before re-running the crew.

3. **`_cascade_invalidate` — rollback cascade policy**: A new deterministic helper in `first_publish.py`. Given a phase number, it removes well-known phase-boundary output paths produced by phases > the given phase value, ensuring downstream artifacts from a prior (failed) attempt cannot be re-read by a restarted crew.

4. **CLI `--resume` — checkpoint restore before re-run**: After `CheckpointManager.get_last_valid_checkpoint()` returns a valid entry, call `cm.restore()` to reset the output directory to the snapshot state before invoking `run_first_publish_agent`. This guarantees the resumed phase starts from a clean slate.

All changes are in pure Python; no new agents, crews, or LLM calls are introduced. The Rollback Agent (40) as an LLM agent is unchanged — these are corrections to the deterministic orchestration layer in Agent 6's helper functions.

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| Create checkpoint before crew runs | Deterministic (tool: `CheckpointManager.create`) | File I/O is not an LLM concern; always create snapshot at the same point |
| Restore checkpoint on retry | Deterministic (tool: `CheckpointManager.restore`) | Deterministic filesystem operation; restoring to the exact snapshot is not a decision requiring LLM judgment |
| Cascade invalidation of downstream artifacts | Deterministic (new `_cascade_invalidate` helper) | Which artifact directories to delete after a rollback is spec-defined, not agent-determined |
| Resume: restore then re-run | Deterministic (cli.py + `CheckpointManager.restore`) | CLI orchestration logic; no LLM involvement in deciding where to resume |

## Model Tier Assignment

No new or modified agents. All changes are to deterministic helper functions called by Agent 6 (First Publish Agent, Tier 2 – Claude Sonnet, unchanged).

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Agent 6 – First Publish Agent | Tier 2 | claude-sonnet-4-20250514 | Unchanged — this change only affects the Python orchestration helpers, not the agent's LLM configuration |

## Architecture Decisions

### Decision: Per-crew pre-run checkpoint, not per-phase-group checkpoint

**Context:** The current implementation creates checkpoints at phase _group_ boundaries (after Phase 1 completes, after Phase 3's Component Factory, after Phase 4's Governance, etc.). The PRD §3.4 says "Before each crew runs, the Rollback Agent snapshots the current output folder state." Design-to-Code and Component Factory both use `_run_simple_crew` with no checkpoint at all.

**Decision:** Create a checkpoint before _every_ individual crew's `kickoff()` call, including the two Phase 2–3 `_run_simple_crew` calls. The phase number used for the checkpoint name follows `_CREW_PHASE_MAP` (see File Changes).

**Consequences:** 9 checkpoint directories instead of 5. For a Standard-scope design system (~5 MB output), this adds ~45 MB peak checkpoint storage per run. Checkpoints are cleaned up on pipeline success by the existing `cm.cleanup()` call, so the overhead is temporary.

### Decision: Restore to the attempt-start snapshot, not to the phase-group boundary

**Context:** `_run_with_retry` for Phases 4–6 retries entire crews. On a retry, the crew should start from the state before the failed attempt, not from the previous phase group's boundary. Using the attempt-start snapshot is stricter and exactly what the PRD specifies.

**Decision:** In `_run_with_retry`, create a snapshot at the start of attempt 1, then restore to that same snapshot before each subsequent attempt.

**Consequences:** Each Phase 4–6 crew that needs a retry will re-run on an identical output state to attempt 1, preventing partial writes from a failed attempt from affecting the retry.

### Decision: `_cascade_invalidate` uses hard-coded path prefixes, not agent output manifests

**Context:** A cascade-correct rollback requires deleting all Phase > N artifacts. A general solution would parse crew output manifests. A narrow solution deletes well-known directory prefixes per phase.

**Decision:** Use narrow, explicit phase-to-directory mappings consistent with the Crew I/O contracts in §3.6. This is safe because the output directory layout is fixed by the PRD spec and does not vary between runs.

**Consequences:** Simpler implementation with no runtime dependencies. Any future changes to crew output paths must also update `_PHASE_ARTIFACT_DIRS` in `first_publish.py`.

### Decision: CLI `--resume` restores checkpoint before resuming

**Context:** `cli.py` line 58 calls `run_first_publish_agent(resume, start_phase=N)` after finding the last valid checkpoint for phase N-1. If the process crashed mid-phase, the output directory is in an unknown partial state. The PRD requires "re-runs it from scratch with a clean slate."

**Decision:** Call `cm.restore(output_dir=resume, phase=checkpoint["phase"])` before `run_first_publish_agent`, so the output directory matches the snapshot before re-running.

**Consequences:** The resumed phase always starts from a known-good state. This adds one filesystem restore operation to the resume path (O(n files), typically < 1 second for standard scope).

## Data Flow

```
[CLI --resume] ──reads──► CheckpointManager.get_last_valid_checkpoint()
                                     │
                                     ▼
               CheckpointManager.restore(phase=N)  ←── restores snapshot
                                     │
                                     ▼
               run_first_publish_agent(start_phase=N+1)
```

```
[_run_simple_crew] ──before kickoff──► CheckpointManager.create(phase)
                                                 │
                              failure?           │
                    ┌──────────────────┘
                    ▼
        [restore not applied — _run_simple_crew is single-attempt]
        [Caller (_run_phase13_crew) handles retry via its own checkpoint]
```

```
[_run_with_retry attempt 1] ──► CheckpointManager.create(phase)
                                          │
                              attempt 2+  │ failure
                    ┌─────────────────────┘
                    ▼
        CheckpointManager.restore(phase) + _cascade_invalidate(output_dir, phase)
        ──► crew.kickoff() (fresh state)
```

## Retry & Failure Behavior

- **`_run_simple_crew`**: Still single-attempt (no change to retry count). The pre-run checkpoint enables the _caller_ (`_run_phase13_crew`) to restore to a known-good state before the retry re-invokes the token foundation task + re-runs the crew. This was already architecturally intended but the snapshot was missing.
- **`_run_with_retry`**: Phase 4-6 retries now operate on a clean snapshot state (attempt-start restore). If all retries are exhausted, the final failure is non-fatal (existing behaviour unchanged). The checkpoint created at attempt 1 is left in place for potential `--resume` use.
- **Cascade invalidation**: If `_cascade_invalidate` itself fails (e.g., permission error), it raises and the pipeline halts with a clear error. No silent partial invalidation.
- **CLI `--resume` with corrupt checkpoint**: If `cm.restore()` raises `CheckpointCorruptError`, the existing CLI error path catches it; the user is prompted to restart from Phase 1 (per PRD §3.4).

## File Changes

- `src/daf/agents/first_publish.py` (modified) — add `cm` and `phase` params to `_run_simple_crew` and `_run_with_retry`; add `_cascade_invalidate` helper; add `_CREW_PHASE_MAP` and `_PHASE_ARTIFACT_DIRS` constants; update `run_first_publish_agent` call sites
- `src/daf/cli.py` (modified) — add `cm.restore()` call before `run_first_publish_agent` in the `--resume` path; handle `CheckpointCorruptError`
- `tests/test_first_publish_agent.py` (modified) — add four new test cases: pre-run checkpoint on `_run_simple_crew`, pre-retry restore on `_run_with_retry`, cascade invalidation, and resume restore
- `tests/test_cli_init.py` (modified) — add test for resume path calling `cm.restore()` before re-running the agent
