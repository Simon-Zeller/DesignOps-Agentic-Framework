# Design: p09-pipeline-orchestrator

## Technical Approach

Agent 6 (First Publish Agent) is the pipeline capstone. It owns one CrewAI Task — `orchestrate_full_pipeline` — whose description instructs it to invoke the `CrewSequencer` tool to run all 8 downstream crews in sequence, handle retry routing, present the Output Review gate, and write the final `reports/generation-summary.json` via `ResultAggregator`.

Agent 40 (Rollback Agent) is instantiated by Agent 6 before the first downstream crew runs. Agent 6 holds a Python reference to Agent 40's `CheckpointManager` tool and calls `CheckpointManager.create(phase)` at every phase boundary. This is a direct intra-process call, not a new CrewAI task — Agent 40 is a lightweight utility agent whose only job is checkpoint I/O.

The implementation introduces two module groups:

**New tools** (deterministic):
- `CheckpointManager` — folder snapshots via `shutil.copytree`
- `CrewSequencer` — drives the phase sequence, validates I/O contracts, routes retries
- `ResultAggregator` — merges per-crew result dicts into `generation-summary.json`
- `StatusReporter` — structured stdout progress (phase start/complete/retry/failure)

**New agents** (LLM):
- `first_publish.py` — Agent 6, orchestrates the sequence, decides retry context, frames output review summary
- `rollback.py` — Agent 40, evaluates checkpoint integrity, determines rollback scope

**New crew stubs** (`src/daf/crews/`):
- One module per downstream crew (8 modules). Each returns a `CrewAI.Crew` with a single no-op task that writes the minimum expected output files from the §3.6 I/O contracts. Stubs allow Agent 6 to sequence real calls before downstream crews are implemented.

**CLI integration** (`src/daf/cli.py` — modified):
- After Brand Profile Human Gate 1 approval, `daf init` calls `run_first_publish_agent(output_dir)` which invokes Agent 6's orchestration task.
- After Agent 6 completes, the CLI presents the generation report summary and prompts Gate 2: approve / re-run full / re-run from phase / re-run components.

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| Invoking downstream crews in order | **Deterministic** (`CrewSequencer`) | Phase ordering is fixed in §3.1; no reasoning needed |
| Validating crew I/O contracts before invoking a crew | **Deterministic** (`CrewSequencer`) | File-existence checks; no judgement |
| Creating/restoring phase checkpoints | **Deterministic** (`CheckpointManager`) | Pure filesystem operations |
| Determining whether to retry vs. fail after a Phase 1–3 validation rejection | **Agent** (Agent 6) | Requires reading the structured rejection and deciding whether the retry context is materially different from the last attempt |
| Constructing accumulated retry context for re-invoked agents | **Agent** (Agent 6) | Synthesizes original task + prior rejections into coherent additional context |
| Determining whether a checkpoint is valid/corrupt (on resume) | **Agent** (Agent 40) | Integrity assessment involves judging partial writes, missing files, and incomplete states |
| Determining rollback scope on cascade | **Agent** (Agent 40) | Must reason about which downstream artifacts depend on the restored phase |
| Merging per-crew results into `generation-summary.json` | **Deterministic** (`ResultAggregator`) | Structured merge; no semantic reasoning |
| Emitting progress messages to stdout | **Deterministic** (`StatusReporter`) | Templated output |
| Framing the Output Review gate summary for the CLI user | **Agent** (Agent 6) | Narrative synthesis: quality scores, pass/fail summary, known issues, recommended actions |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Agent 6: First Publish Agent | **Tier 2** | `claude-sonnet-4-20250514` | Analytical: reads structured results, decides retry context, synthesises output review summary. Heavy reasoning but not generative. |
| Agent 40: Rollback Agent | **Tier 3** | `claude-haiku-4-20250414` | Classification: determines checkpoint validity and rollback scope from structured manifest data. Lightweight reasoning. |

## Architecture Decisions

### Decision: Crew stubs write minimum required output files

**Context:** Agent 6 must sequence real CrewAI `Crew.kickoff()` calls so the orchestration logic is testable without each crew being implemented. But `CrewSequencer` validates I/O contracts — if a crew doesn't write expected files, it fails fast.

**Decision:** Each stub crew's no-op task writes the minimum files listed in the §3.6 "Writes" column for that crew. Files are empty (or contain a `{"stub": true}` JSON marker for JSON files) but present. The `CrewSequencer` I/O contract check is presence-only at this stage.

**Consequences:** Agent 6 integration tests can run end-to-end with stubs. When a real crew is implemented (e.g., p10-token-engine), its module replaces the stub import in `src/daf/crews/token_engine.py` without touching Agent 6.

---

### Decision: Checkpoints stored in `.daf-checkpoints/` inside the output directory

**Context:** Checkpoints need to survive process crashes and be accessible on `--resume`. They must not pollute the design system output or be committed to git.

**Decision:** Checkpoints are written to `<output_dir>/.daf-checkpoints/<phase>-<iso-timestamp>/` with a manifest at `<output_dir>/.daf-checkpoints/checkpoints.json`. The `.daf-checkpoints/` directory is added to the generated `.gitignore`. A checkpoint is the entire contents of `<output_dir>` except `.daf-checkpoints/` itself (to avoid recursive copies).

**Consequences:** Disk usage scales with output size × number of phases (max 9 checkpoints per run). Checkpoints are cleaned up on successful pipeline completion. Corrupt checkpoint detection uses the manifest: a checkpoint is valid only if all its expected files are present and their sizes match the manifest record.

---

### Decision: Cross-phase retry as direct function calls, not new Crew instances

**Context:** When the Token Validation Agent (8, Phase 2) rejects Token Foundation Agent (2, Phase 1) output, Agent 6 must re-invoke Agent 2 with the rejection context. CrewAI Crews are designed for fresh instantiation — re-running a Phase 1 Crew risks resetting state unintentionally.

**Decision:** The cross-phase retry loop calls the Phase 1 agent task function directly: `run_token_foundation_task(brand_profile, output_dir, retry_context=rejection)`. These functions are the same underlying implementations used by the DS Bootstrap Crew's task sequence. Agent 6 holds a reference to them imported from `daf.agents.*`. The Rollback Agent restores the pre-Phase-2 checkpoint before each re-run to prevent artifact corruption (§3.4 rollback cascade).

**Consequences:** Agent 6 has direct imports from Phase 1 agent modules. This is intentional — Agent 6 is the orchestrator and owns the full pipeline view. Circular imports are avoided by keeping agent modules self-contained (no cross-agent imports).

---

### Decision: Resume detects last valid checkpoint, not last phase

**Context:** `--resume <output-dir>` should re-run from the next incomplete phase. The "next phase" is determined by what checkpoints exist and are valid, not by reading any pipeline state file.

**Decision:** On `--resume`, `CheckpointManager.get_last_valid_checkpoint()` reads `checkpoints.json`, iterates checkpoints in phase order, and returns the last one whose manifest integrity check passes. The pipeline re-runs from the phase immediately after that checkpoint. If no valid checkpoints exist (e.g., crash before Phase 1 completed), the CLI reports the issue and asks the user whether to restart from Phase 1.

**Consequences:** Resume is robust to process crashes at any point (including mid-checkpoint). There is no separate "pipeline state" file to keep in sync.

## Data Flow

```
[CLI: daf init]
  ──Gate 1 approval──►
  [DS Bootstrap Crew — Agents 1-5]
    writes ──► brand-profile.json
    writes ──► tokens/base.tokens.json (raw)
    writes ──► tokens/semantic.tokens.json (raw)
    writes ──► tokens/component.tokens.json (raw)
    writes ──► specs/*.spec.yaml
    writes ──► pipeline-config.json
    writes ──► tsconfig.json, vitest.config.ts, vite.config.ts

  [Agent 6: First Publish Agent + Agent 40: Rollback Agent]
    ─── Phase boundary: CheckpointManager.create(phase=1) ───►

  [Token Engine Crew — Agents 7-11]
    reads  ◄─── tokens/*.tokens.json (raw)
    writes ──► tokens/base.tokens.json (validated)
    writes ──► tokens/compiled/* (CSS, SCSS, TS, JSON)
    writes ──► tokens/diff.json

    ─── Phase boundary: CheckpointManager.create(phase=2) ───►

  [Design-to-Code Crew — Agents 12-16]
    reads  ◄─── specs/*.spec.yaml
    reads  ◄─── tokens/compiled/*
    writes ──► src/primitives/*.tsx + *.test.tsx + *.stories.tsx
    writes ──► src/components/**/*.tsx + *.test.tsx + *.stories.tsx
    writes ──► reports/generation-summary.json
    writes ──► screenshots/*

  [Component Factory Crew — Agents 17-20]
    reads  ◄─── specs/*.spec.yaml
    reads  ◄─── src/**/*.tsx
    reads  ◄─── tokens/semantic.tokens.json
    patches ──► src/ (a11y fixes in-place)
    writes ──► reports/quality-scorecard.json
    writes ──► reports/a11y-audit.json
    writes ──► reports/composition-audit.json

    ─── Phase boundary: CheckpointManager.create(phase=3) ───►

  [Documentation Crew — Agents 21-25]
    reads  ◄─── specs/*.spec.yaml, src/**/*.tsx, tokens/*.tokens.json
    writes ──► docs/**/*.md
    writes ──► docs/search-index.json

  [Governance Crew — Agents 26-30]
    reads  ◄─── brand-profile.json, pipeline-config.json, specs/, reports/
    reads  ◄─── docs/ (verifies all components have docs)
    writes ──► governance/*.json
    writes ──► tests/*.test.ts
    writes ──► docs/templates/*

    ─── Phase boundary: CheckpointManager.create(phase=4) ───►

  [AI Semantic Layer Crew — Agents 41-45]
    reads  ◄─── specs/, src/, tokens/, reports/composition-audit.json
    writes ──► registry/*.json
    writes ──► .cursorrules, copilot-instructions.md, ai-context.json

  [Analytics Crew — Agents 31-35]
    reads  ◄─── specs/, src/, docs/, tokens/
    writes ──► reports/token-compliance.json
    writes ──► reports/drift-report.json

    ─── Phase boundary: CheckpointManager.create(phase=5) ───►

  [Release Crew — Agents 36-40]
    reads  ◄─── entire output folder
    writes ──► package.json, src/index.ts, docs/changelog.md
    writes ──► (updates) reports/generation-summary.json

    ─── Pipeline complete ──►

  [Agent 6: ResultAggregator ──► reports/generation-summary.json]
  [CLI ──► Gate 2: Output Review prompt]
```

**Retry routing (cross-phase, §3.4):**
```
[Token Validation Agent (8)] ──rejects──► Agent 6
  Agent 6 ──restore checkpoint(phase=0)──► [Agent 40: Rollback]
  Agent 6 ──retry context──► [Token Foundation Agent (2): direct call]
  Agent 6 ──re-run──► [Token Engine Crew — Agents 7-11]
  (up to 3 attempts per component, 2 per crew for Phases 4-6)
```

## Retry & Failure Behavior

**Phases 1–3 (per-component retry):**
- `CrewSequencer` catches a crew's structured rejection result.
- Agent 6 reads the rejection, evaluates whether the retry context differs from the previous attempt, and constructs accumulated context.
- For cross-phase rejection (Phase 2 rejects Phase 1 output), Agent 6 calls `CheckpointManager.restore(phase=1_pre)`, re-invokes the originating Phase 1 agent task function with accumulated rejection context, then re-runs the Phase 2 crew from scratch.
- After 3 failed component attempts: component is marked `failed` in `generation-summary.json`, the Rollback Agent preserves its last best attempt, and the pipeline continues with remaining components.

**Phases 4–6 (per-crew retry):**
- If a crew fails (e.g., Doc Generation Agent produces invalid Markdown), Agent 6 retries the entire crew up to 2 attempts.
- Phase 4–6 failures are non-fatal. On exhaustion, the crew is marked `failed` in the report and the pipeline continues.

**Catastrophic failure (process crash):**
- `--resume <output-dir>` restores from the last valid checkpoint and re-runs from the next phase.
- If no valid checkpoint exists, the CLI prompts for full Phase 1 restart.

## File Changes

- `src/daf/agents/first_publish.py` (new) — Agent 6: First Publish Agent
- `src/daf/agents/rollback.py` (new) — Agent 40: Rollback Agent (cross-cutting)
- `src/daf/tools/crew_sequencer.py` (new) — deterministic phase sequencer
- `src/daf/tools/checkpoint_manager.py` (new) — snapshot/restore tool
- `src/daf/tools/result_aggregator.py` (new) — merges crew results into generation-summary.json
- `src/daf/tools/status_reporter.py` (new) — structured stdout progress reporter
- `src/daf/crews/__init__.py` (new) — exports all crew factories
- `src/daf/crews/token_engine.py` (new) — stub crew for Phase 2 (Token Engine Crew)
- `src/daf/crews/design_to_code.py` (new) — stub crew for Phase 3a (Design-to-Code Crew)
- `src/daf/crews/component_factory.py` (new) — stub crew for Phase 3b (Component Factory Crew)
- `src/daf/crews/documentation.py` (new) — stub crew for Phase 4a (Documentation Crew)
- `src/daf/crews/governance.py` (new) — stub crew for Phase 4b (Governance Crew)
- `src/daf/crews/ai_semantic_layer.py` (new) — stub crew for Phase 5a (AI Semantic Layer Crew)
- `src/daf/crews/analytics.py` (new) — stub crew for Phase 5b (Analytics Crew)
- `src/daf/crews/release.py` (new) — stub crew for Phase 6 (Release Crew)
- `src/daf/cli.py` (modified) — wire Gate 1 → Agent 6 → Gate 2; implement `--resume` flag
