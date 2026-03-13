# Proposal: p08-pipeline-config

## Intent

Agent 5 (Pipeline Configuration Agent) is the final generative agent in the DS Bootstrap Crew and the last piece needed before the full Phase 1 pipeline can produce a complete, compilable output folder. It bridges the validated Brand Profile (from Agent 1) and downstream crews by producing two categories of artifacts:

1. **`pipeline-config.json`** — the configuration seed that governs how downstream crews operate: quality gate thresholds, lifecycle defaults, domain categories for ownership, retry limits, model tier assignments, and build settings. The Governance Crew (Phase 4b) reads this file as its primary input seed and expands it into the full governance artifacts.
2. **Project scaffolding files** — `tsconfig.json`, `vitest.config.ts`, `vite.config.ts` — required by Phase 2+ crews for TypeScript compilation (`tsc --noEmit`), test execution (vitest), and library-mode build validation (vite). These files must exist before Phase 2 so that validation agents can compile and test without waiting for the Release Crew.

Without Agent 5, the downstream Governance Crew has no configuration seed, and Phase 2+ crews cannot compile or test generated code. This change completes Agent 5 and closes out the DS Bootstrap Crew's generative layer (Agents 1–5). Agent 6 (First Publish Agent, the cross-cutting retry orchestrator) is a separate concern.

## Scope

### In scope

- `src/daf/tools/config_generator.py` — deterministic tool: derives `pipeline-config.json` from Brand Profile inputs, applying threshold inference rules (e.g., AAA accessibility level → stricter contrast gate, comprehensive scope → `beta` lifecycle default for complex components)
- `src/daf/tools/project_scaffolder.py` — deterministic tool: writes `tsconfig.json`, `vitest.config.ts`, and `vite.config.ts` templates to the output directory; values are parameterised from the Brand Profile (e.g., TypeScript target, module format)
- `src/daf/agents/pipeline_config.py` — Agent 5 factory with `create_pipeline_config_agent()` and `create_pipeline_config_task()`, Tier 2 (Sonnet), following the established pattern from `token_foundation.py`, `primitive_scaffolding.py`, and `core_component.py`
- `openspec/specs/pipeline-config/spec.md` — capability spec documenting the full `pipeline-config.json` schema (§3.8), scaffolded file contracts, and Agent 5's inference rules
- Unit tests for all tool functions and the agent task

### Out of scope

- Agent 6 (First Publish Agent) — cross-cutting retry orchestrator, will be a separate change
- Full DS Bootstrap Crew wiring (`crew.py` combining Agents 1–6 into a runnable `Crew`) — a separate pipeline integration change
- The Governance Crew's expansion of `pipeline-config.json` into full governance artifacts — Phase 4b

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| DS Bootstrap | Agent 5: Pipeline Configuration Agent | Implemented in this change |
| Governance | Agents 28–31 (Quality Gate, Lifecycle Policy, Dependency, Contribution Workflow) | Consumers of `pipeline-config.json`; all behaviour is seeded from Agent 5's output |
| Design-to-Code | Agent 14: Code Generation Agent | Requires `tsconfig.json` present before `tsc --noEmit` validation can run in Phase 3 |
| Component Factory | Agent 15: Render Validation Agent, Agent 17: Spec Validation Agent | Require `vitest.config.ts` and `vite.config.ts` for test and build validation |
| Release | Agent 37: Build Agent | Consumes all three scaffolding files during final package assembly |

## PRD References

- §3.8 — Pipeline Configuration Schema (defines the full `pipeline-config.json` structure and field semantics)
- §3.6 — Crew I/O Contracts (Bootstrap Crew I/O contract explicitly lists `pipeline-config.json`, `tsconfig.json`, `vitest.config.ts`, `vite.config.ts` as BS Crew writes)
- §4.1 — Agent 5: Pipeline Configuration Agent (role, goal, tools list, and output contract)
- §3.7 — Model Assignment Strategy (Tier 2 Analytical — Sonnet — appropriate for structured inference from Brand Profile inputs)
- §3.4 — Retry Protocol (Agent 5's `retry` fields in `pipeline-config.json` govern the bounded retry loops described here)

## Pipeline Impact

- [ ] Pipeline phase ordering
- [x] Crew I/O contracts (§3.6) — Bootstrap Crew now produces `pipeline-config.json`, `tsconfig.json`, `vitest.config.ts`, `vite.config.ts`
- [ ] Retry protocol (§3.4)
- [ ] Human gate policy (§5)
- [x] Exit criteria (§8) — `tsconfig.json` presence is a precondition for the Fatal check "TypeScript compilation passes"
- [ ] Brand Profile schema (§6)

## Approach

Follow the deterministic-tool + agent-wrapper pattern established by p06 and p07:

1. **`ConfigGenerator(BaseTool)`** — pure Python function `generate_pipeline_config(brand_profile: dict) -> dict` that applies hardcoded inference rules to produce the `pipeline-config.json` dict, then serialises it to disk. Rules include: `a11yLevel` → `minCompositeScore` threshold mapping, `scope: comprehensive` → beta lifecycle for complex components, Brand Profile `themes` array → no additional model config. Tool wrapper accepts `brand_profile_json` and `output_dir` arguments.

2. **`ProjectScaffolder(BaseTool)`** — pure Python function `scaffold_project_files(brand_profile: dict, output_dir: str) -> dict[str, str]` that writes the three template files (tsconfig.json, vitest.config.ts, vite.config.ts) using parameterised templates. Returns a map of filename → absolute path.

3. **Agent 5 module** — `create_pipeline_config_agent()` constructs a Tier 2 Sonnet agent with both tools. `create_pipeline_config_task()` constructs Task T5, taking `output_dir`, `brand_profile_path` (path to the Agent 1 output), and optional `context_tasks` (upstream tasks from Agents 1–4).

4. **Capability spec** — `openspec/specs/pipeline-config/spec.md` documents the full output contract: `pipeline-config.json` schema (field types, valid values, defaults), `tsconfig.json` base configuration, `vitest.config.ts` expected exports, `vite.config.ts` library-mode settings.

## Risks

- **Threshold inference brittleness** — A11y level and scope tier are coarse proxies for quality gate calibration. Edge cases (e.g., AAA + starter scope, or custom archetypes) may produce thresholds that are either too strict or too permissive. Mitigation: all thresholds include documented defaults; Agent 5's task description explicitly instructs the agent to validate that the inferred values are internally consistent before writing.
- **Scaffolding file drift** — `tsconfig.json`, `vitest.config.ts`, and `vite.config.ts` templates must remain compatible with the React + TypeScript stack targeted by Phase 3. If the stack changes in a future change, these templates are a maintenance point. Mitigation: the capability spec documents each template's contract explicitly, making drift visible.
- **Schema stability** — The Governance Crew (Phase 4b) is tightly coupled to the `pipeline-config.json` schema (§3.8). Changes to field names or types in this change break the Governance Crew's input contract. Mitigation: treat the §3.8 schema as frozen for this change; any extensions require a separate proposal.
