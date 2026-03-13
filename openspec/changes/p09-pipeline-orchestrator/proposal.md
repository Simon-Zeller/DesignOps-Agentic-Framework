# Proposal: p09-pipeline-orchestrator

## Intent

The DS Bootstrap Crew (Agents 1–5) is now fully implemented. Agents produce a validated Brand Profile, raw token files, canonical spec YAMLs, and the pipeline scaffolding config. However, nothing yet invokes the downstream crews. Agent 6 (First Publish Agent, §4.1) is the missing capstone: the orchestrator that sequences all 9 crews, manages phase-boundary checkpoints, routes retry loops, and drives the two human gates to completion.

Without Agent 6, the `daf init` command can collect a Brand Profile and run the Bootstrap agents, but it cannot advance past Phase 1. The full generation pipeline — Token Engine → Design-to-Code → Component Factory → Documentation → Governance → AI Semantic Layer → Analytics → Release — is never triggered. This change delivers that orchestration layer.

## Scope

### In scope

- **Agent 6: First Publish Agent** (`src/daf/agents/first_publish.py`) — CrewAI agent that orchestrates the full crew sequence (Phases 1–6) and aggregates final status.
- **CrewSequencer tool** (`src/daf/tools/crew_sequencer.py`) — deterministic tool that invokes each crew in dependency order, enforces phase ordering, and propagates I/O contracts between phases.
- **ResultAggregator tool** (`src/daf/tools/result_aggregator.py`) — collects per-crew execution results and assembles the final `reports/generation-summary.json`.
- **StatusReporter tool** (`src/daf/tools/status_reporter.py`) — emits structured progress updates (phase start, phase complete, retry triggered, failure) to stdout/log.
- **Agent 40: Rollback Agent** (`src/daf/agents/rollback.py`) — cross-cutting agent instantiated by Agent 6 at pipeline start; writes and restores phase-boundary checkpoints.
- **CheckpointManager tool** (`src/daf/tools/checkpoint_manager.py`) — creates timestamped snapshots of the output folder at each phase boundary and restores them on demand.
- **Retry routing logic** — Agent 6 detects Phase 2 validation failures and re-invokes Phase 1 agents with structured rejection context (§3.4, cross-phase retry routing).
- **CLI wiring** — `daf init` advances from Brand Profile approval (Human Gate 1) to full pipeline execution via Agent 6, then presents the Output Review gate (Human Gate 2).
- **Resume support** — `daf init --resume <output-dir>` restores from the last valid checkpoint and re-runs from the next phase.

### Out of scope

- Implementing the downstream crews themselves (Token Engine, Design-to-Code, etc.) — they are stubbed as CrewAI Crew objects returning placeholder output until their respective changes are delivered.
- The per-crew agent implementations (Agents 7–45).
- Any UI beyond CLI output.
- Parallel crew execution (§3.1 specifies strictly sequential phases).

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| DS Bootstrap | Agent 6: First Publish Agent | **New implementation** — orchestrates all downstream crews |
| Release | Agent 40: Rollback Agent | **New implementation** — checkpoint management; instantiated by Agent 6 outside Release Crew task flow |
| All downstream crews | Agents 7–45 (stubs) | Minimal impact — stub Crew objects added so Agent 6 can call them; no agent logic yet |
| DS Bootstrap (existing) | Agents 1–5 | Integration point — Agent 6 picks up their outputs via the shared output folder contract (§3.6) |

## PRD References

- §3.1 — Sequential pipeline phases and intra-phase ordering
- §3.4 — Retry protocol, cross-phase retry routing, rollback cascade policy, resume-on-failure
- §3.6 — Crew I/O contracts (file-based handoff between phases)
- §4.1 — DS Bootstrap Crew: Agent 6 First Publish Agent; Agent 40 Rollback Agent
- §4.8 — Release Crew: Agent 40 specification (cross-cutting, instantiated by Agent 6)
- §5 — Human Gate Policy (Gate 1: Brand Profile Approval; Gate 2: Output Review)

## Pipeline Impact

- [x] Pipeline phase ordering — Agent 6 enforces the 6-phase sequential order with intra-phase ordering (3: D2C before Component Factory; 4: Documentation before Governance)
- [x] Crew I/O contracts (§3.6) — CrewSequencer validates that each crew's required inputs exist before invoking it; fails-fast on missing preconditions
- [x] Retry protocol (§3.4) — Agent 6 implements cross-phase retry routing; CheckpointManager supports rollback cascade
- [x] Human gate policy (§5) — CLI wires Gate 1 (existing) → pipeline → Gate 2 (new output review prompt)
- [ ] Exit criteria (§8) — not affected; exit criteria checks are inside individual crews
- [ ] Brand Profile schema (§6) — not affected

## Approach

1. **Stub downstream crews** — add minimal `create_<crew>_crew()` factory functions for each of the 8 downstream crews. Each stub returns a CrewAI `Crew` with a single no-op task that writes a placeholder output file. This allows Agent 6 to sequence real calls without requiring downstream crew implementations.

2. **CheckpointManager tool** — wraps `shutil.copytree` to snapshot the output folder to a `.daf-checkpoints/<phase>-<timestamp>/` directory before each phase. Restore by copying back. Maintains a `checkpoints.json` manifest.

3. **CrewSequencer tool** — given a list of `(phase, crew)` pairs derived from §3.1, executes each in order. Before each crew runs, calls `CheckpointManager.create()`. After each crew runs, validates required outputs exist (using the I/O contracts table from §3.6). On failure, triggers retry or calls `CheckpointManager.restore()` and propagates the cascade.

4. **ResultAggregator tool** — reads per-crew result structs and merges them into `reports/generation-summary.json`. Tracks per-component status throughout the pipeline.

5. **Agent 6 (First Publish Agent)** — CrewAI Agent (Tier 2, Sonnet) with tools: `CrewSequencer`, `ResultAggregator`, `StatusReporter`. Its single task drives the full sequence from Phase 1 completion to Release Crew completion.

6. **Agent 40 (Rollback Agent)** — CrewAI Agent (Tier 3, Haiku) with tools: `CheckpointManager`. Instantiated by Agent 6 at pipeline start into `src/daf/agents/rollback.py`.

7. **CLI integration** — `daf init` after Brand Profile Human Gate 1 approval calls Agent 6's task. After completion, presents the generation report summary and prompts Gate 2 (approve / re-run options).

## Risks

- **Stub crews produce empty output folders** — downstream crew stubs must write the minimum expected files from §3.6 so the I/O contract validator doesn't fail-fast. Stubs will write empty but present files.
- **Checkpoint disk usage** — each phase snapshot copies the entire output folder. For Comprehensive scope this may be large. Mitigated by `.daf-checkpoints/` being gitignored and snapshots only kept per current run.
- **Retry routing complexity** — the cross-phase retry loop (Phase 1 ↔ Phase 2) requires Agent 6 to hold references to specific Phase 1 agents and call them outside of their original crew context. This is modelled as direct function calls to `run_<agent>_task()`, not a new Crew instance.
- **Resume correctness** — resume logic must validate checkpoint integrity before restoring. An incomplete snapshot (e.g., from a crash mid-copy) must be detected and rejected, with a fallback to Phase 1 restart.
