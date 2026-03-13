# Design: p17-release-crew

## Technical Approach

Replace the `StubCrew` in `src/daf/crews/release.py` with a real `crewai.Crew` containing five agents wired as tasks T1→T2→T3→T4→T5→T6. Agents 36–39 form the sequential task chain inside the crew. Agent 40 (Rollback) is constructed separately by Agent 6 (First Publish) at pipeline start and invoked as a utility at every phase boundary — it is not wired into the Release Crew's task flow.

Each agent follows the established `create_<agent>_agent(model, output_dir) -> Agent` factory pattern. New deterministic helper tools are added to `src/daf/tools/`. Existing tools (`gate_evaluator.py`, `report_writer.py`, `checkpoint_manager.py`, `prose_generator.py`, `example_code_generator.py`) are reused where their interface matches; new narrow-purpose tools are introduced for capabilities with no existing equivalent.

The Rollback Agent's checkpoint lifecycle is:
1. **Snapshot** — called by Agent 6 before every crew run; writes a snapshot of the output folder to `checkpoints/<phase>/`
2. **Restore** — called by Agent 6 when a crew exhausts its 2-attempt retry budget; restores the output folder from the snapshot and marks subsequent phases as requiring re-run
3. **Report** — writes `reports/rollback-log.json` describing what was restored and why

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| Choose semantic version number from gate results | Deterministic (`version_calculator.py`) | Version derivation is a rule (`v1.0.0` if all Fatal gates pass, else `v0.x.0`); no LLM judgment required |
| Read and normalise quality gate report | Deterministic (`gate_status_reader.py`, `quality_report_parser.py`) | Structured JSON parsing; deterministic |
| Write `docs/changelog.md` prose | Agent-driven (Agent 37, Sonnet) | Grouping, tone, and narrative summary benefit from LLM prose quality |
| Read component inventory for changelog | Deterministic (`component_inventory_reader.py`) | Inventory is a structured JSON read; deterministic |
| Generate codemod example scripts | Agent-driven (Agent 38, Haiku) | Pattern-to-pattern transformation guidance is well-suited to LLM generation |
| AST pattern matching for codemod inputs | Deterministic (`ast_pattern_matcher.py`) | Regex/heuristic scan of TS/TSX source; deterministic |
| Codemod template scaffolding | Deterministic (`codemod_template_generator.py`, `example_suite_builder.py`) | Fixed template structure; deterministic |
| Assemble `package.json` fields | Deterministic (`package_json_generator.py`, `dependency_resolver.py`) | Package manifest assembly is rule-based from spec inputs |
| Run `npm install`, `tsc --noEmit`, `npm test` | Deterministic (`dependency_resolver.py` wrapping npm CLI) | CLI execution; deterministic |
| Parse test results | Deterministic (`test_result_parser.py`) | JSON/TAP output parsing; deterministic |
| Write `reports/generation-summary.json` final_status | Deterministic (`report_writer.py`) | Deterministic — derived from tool outputs |
| Checkpoint snapshot/restore | Deterministic (`checkpoint_creator.py`, `restore_executor.py`) | File system operations; deterministic |
| Rollback narrative report | Deterministic (`rollback_reporter.py`) | Structured log of what was restored and why; no prose needed |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Agent 36 – Semver Agent | Tier 3 – Haiku | `claude-3-haiku-*` | Simple rule application over structured JSON; minimal reasoning required |
| Agent 37 – Release Changelog Agent | Tier 2 – Sonnet | `claude-3-5-sonnet-*` | Produces coherent prose grouped by category; moderate writing quality needed |
| Agent 38 – Codemod Agent | Tier 3 – Haiku | `claude-3-haiku-*` | Template-driven code generation from deterministic AST inputs |
| Agent 39 – Publish Agent | Tier 3 – Haiku | `claude-3-haiku-*` | Orchestrates deterministic tool calls; decision logic is minimal |
| Agent 40 – Rollback Agent | Tier 3 – Haiku | `claude-3-haiku-*` | Snapshot/restore is fully deterministic; LLM is only invoked for the rollback narrative |

## Architecture Decisions

### Decision: Rollback Agent lives outside Release Crew task flow

**Context:** Agent 40 must be active from the very first phase of the pipeline, before the Release Crew is ever instantiated. If it were wired as T6 in the Release Crew, it would only be available after all other phases have completed, making it useless for mid-pipeline failure recovery.

**Decision:** Agent 40 is instantiated directly by Agent 6 (First Publish Agent) at pipeline start and stored as a named reference on the orchestrator. Agent 6 calls `rollback_agent.snapshot()` before each crew delegation and `rollback_agent.restore()` on exhausted-retry failure. The `create_release_crew()` factory does **not** include Agent 40 in its `agents` list.

**Consequences:** Agent 40 is not exercised during the Release Crew's own crew-level retry cycle; it is only exercised at the outer orchestration level. Its tests live in `test_rollback_agent.py` and are driven through `first_publish.py` integration tests.

### Decision: Publish Agent wraps npm CLI as a deterministic tool with graceful degradation

**Context:** `npm install`, `tsc --noEmit`, and `npm test` require a Node.js environment. CI environments for Python-only projects may not have Node installed.

**Decision:** `dependency_resolver.py` wraps the npm CLI via `subprocess.run`. If `npm` is not found on `$PATH`, the tool returns `{"status": "npm_unavailable", "reason": "npm not found"}` without raising an exception. Agent 39 records this in `generation-summary.json` as a Warning (not Fatal). Tests mock `subprocess.run` via `unittest.mock`.

**Consequences:** The pipeline remains runnable in Python-only test environments. The `npm_unavailable` status is visible in the output review gate so users know validation was skipped. Real deployment environments are expected to have Node available.

### Decision: Codemod scripts are adoption examples, not executable transforms

**Context:** PRD §4.8 explicitly calls these "adoption codemods" that demonstrate migration from ad-hoc patterns to design system components. Making them fully executable jsfmt/codemod transforms would require AST rewriting infrastructure that is out of scope.

**Decision:** Agent 38 generates human-readable example scripts in `docs/codemods/` with line-commented pseudo-transforms. Each file shows: before snippet, after snippet, and a brief explanation. The `ast_pattern_matcher.py` tool scans the generated source for patterns (raw `<button>`, hardcoded hex colors) and feeds them to Agent 38 as concrete migration targets.

**Consequences:** Adoption codemods are immediately useful as documentation and as templates for future version-to-version migration scripting, without the complexity of a runnable codemod pipeline.

## Data Flow

```
[Governance Crew]
  └─writes──► reports/governance/quality-gates.json
                   │
                   ▼
             [Release Crew – T1: Semver Agent]
               reads: quality-gates.json
               writes: reports/generation-summary.json (version field)
                   │
                   ▼
             [Release Crew – T2: Changelog Agent]
               reads: quality-gates.json, src/components/**, specs/*.spec.yaml
               writes: docs/changelog.md
                   │
                   ▼
             [Release Crew – T3: Codemod Agent]
               reads: src/components/**, src/primitives/**
               writes: docs/codemods/*.md
                   │
                   ▼
             [Release Crew – T4: Publish Agent (assemble)]
               reads: specs/*.spec.yaml, pyproject.toml (for version)
               writes: package.json, src/index.ts, barrel index.ts files
                   │
                   ▼
             [Release Crew – T5: Publish Agent (validate)]
               runs: npm install && tsc --noEmit && npm test
               writes: reports/generation-summary.json (final_status)
                   │
                   ▼
             [Release Crew – T6: Final status validation]
               reads: reports/generation-summary.json
               writes: reports/generation-summary.json (validated, complete)
                   │
                   ▼
             [Human Gate 2 – Output Review]
```

```
[DS Bootstrap – Agent 6 (First Publish)]
  instantiates──► Agent 40 (Rollback Agent) at pipeline start
                       │
              before each crew run:
                  snapshot(output_dir) → checkpoints/<phase>/
              on exhausted-retry failure:
                  restore(checkpoint) → output_dir
                  report() → reports/rollback-log.json
```

## Retry & Failure Behavior

The Release Crew applies the **Phase 4–6 crew-level retry** boundary (PRD §3.4): if any task in the crew fails, Agent 6 re-runs the entire crew up to **2 attempts**. There is no per-agent retry within the crew.

- **T1 (Semver)** failure: gate report unreadable or malformed → falls back to `v0.1.0-experimental`, logs warning. Does not block T2–T6.
- **T2 (Changelog)** failure: `docs/changelog.md` not written → crew fails; crew-level retry applies. On second failure the crew is marked `failed` in `generation-summary.json`; pipeline continues (non-fatal per §3.4).
- **T3 (Codemod)** failure: `docs/codemods/` not populated → crew fails; same crew-level retry as T2.
- **T4 (Publish assemble)** failure: `package.json` not assembled → crew fails; same retry.
- **T5 (npm validation)** failure:
  - `npm` not found → `npm_unavailable` Warning; pipeline continues.
  - `npm install` fails → recorded as Fatal `npm_build` gate failure; `final_status: "failed"`.
  - `tsc --noEmit` fails → recorded as Fatal `typescript_compilation` gate failure.
  - `npm test` failures → Warning only (per §8: test failures are Warning, not Fatal).
- **T6 (final status)** failure: defensive check only; at this point `generation-summary.json` must exist or T5 has already failed.

## File Changes

**New — tools:**
- `src/daf/tools/gate_status_reader.py` (new) — reads and normalises `reports/governance/quality-gates.json`
- `src/daf/tools/version_calculator.py` (new) — derives semver string from gate pass/fail results
- `src/daf/tools/component_inventory_reader.py` (new) — reads component inventory from `reports/` and `specs/`
- `src/daf/tools/quality_report_parser.py` (new) — parses quality gate and generation reports into structured data
- `src/daf/tools/ast_pattern_matcher.py` (new) — heuristic scan of TS/TSX source for codemod migration patterns
- `src/daf/tools/codemod_template_generator.py` (new) — generates adoption codemod example files
- `src/daf/tools/example_suite_builder.py` (new) — aggregates codemod examples into a structured suite
- `src/daf/tools/package_json_generator.py` (new) — assembles `package.json` from spec inputs and version
- `src/daf/tools/dependency_resolver.py` (new) — wraps npm CLI (`npm install`, `tsc --noEmit`, `npm test`) with graceful degradation
- `src/daf/tools/test_result_parser.py` (new) — parses TAP/JSON test output into structured pass/fail summary
- `src/daf/tools/checkpoint_creator.py` (new) — snapshots output folder to `checkpoints/<phase>/`
- `src/daf/tools/restore_executor.py` (new) — restores output folder from a named checkpoint
- `src/daf/tools/rollback_reporter.py` (new) — writes `reports/rollback-log.json`

**New — agents:**
- `src/daf/agents/semver.py` (new) — Agent 36 factory
- `src/daf/agents/release_changelog.py` (new) — Agent 37 factory
- `src/daf/agents/codemod.py` (new) — Agent 38 factory
- `src/daf/agents/publish.py` (new) — Agent 39 factory

**Modified — agents:**
- `src/daf/agents/rollback.py` (modified) — replace stub with real `checkpoint_creator`, `restore_executor`, `rollback_reporter` tool wiring
- `src/daf/agents/first_publish.py` (modified) — wire Rollback Agent instantiation and phase-boundary snapshot/restore calls

**Modified — crew:**
- `src/daf/crews/release.py` (modified) — replace `StubCrew` with real `crewai.Crew` (Agents 36–39, Tasks T1–T6)

**New — tests:**
- `tests/test_semver_agent.py`
- `tests/test_release_changelog_agent.py`
- `tests/test_codemod_agent.py`
- `tests/test_publish_agent.py`
- `tests/test_rollback_agent.py`
- `tests/test_release_crew.py`
- `tests/test_gate_status_reader.py`
- `tests/test_version_calculator.py`
- `tests/test_component_inventory_reader.py`
- `tests/test_quality_report_parser.py`
- `tests/test_ast_pattern_matcher.py`
- `tests/test_codemod_template_generator.py`
- `tests/test_example_suite_builder.py`
- `tests/test_package_json_generator.py`
- `tests/test_dependency_resolver.py`
- `tests/test_test_result_parser.py`
- `tests/test_checkpoint_creator.py`
- `tests/test_restore_executor.py`
- `tests/test_rollback_reporter.py`
