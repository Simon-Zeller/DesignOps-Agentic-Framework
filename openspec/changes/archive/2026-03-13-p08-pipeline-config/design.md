# Design: p08-pipeline-config

## Technical Approach

Agent 5 (Pipeline Configuration Agent) follows the deterministic-tool + agent-wrapper pattern established by p06 (`primitive_scaffolding.py`) and p07 (`core_component.py`). Two deterministic tools are built first; the agent wrapper invokes them via Task T5.

**`ConfigGenerator(BaseTool)`** — pure Python function `generate_pipeline_config(brand_profile: dict, output_dir: str) -> str` that derives the complete `pipeline-config.json` from the validated Brand Profile. All field values are inferred through hardcoded mapping rules:

- `qualityGates.a11yLevel` ← `brand_profile["accessibility"]["level"]`
- `qualityGates.minCompositeScore` ← `AA` → 70, `AAA` → 85
- `qualityGates.minTestCoverage` ← `brand_profile["scope"]`: `starter` → 80, `standard` → 80, `comprehensive` → 75 (more components, harder to reach 80%)
- `qualityGates.blockOnWarnings` ← `False` (default; AAA does not flip this automatically; it is an operational decision)
- `lifecycle.defaultStatus` ← `"stable"` for starter/standard; `"stable"` for comprehensive with `betaComponents` listing complex Comprehensive-delta components
- `lifecycle.betaComponents` ← hardcoded list of Comprehensive-delta components (`DatePicker`, `DataGrid`, `TreeView`, `Drawer`, `Stepper`, `FileUpload`, `RichText`) when scope is `comprehensive`; empty list otherwise
- `lifecycle.deprecationGracePeriodDays` ← 90 (fixed default)
- `domains.categories` ← derived from scope tier: always include `['forms', 'layout', 'feedback']`; `standard`/`comprehensive` add `['navigation', 'data-display']`; `comprehensive` adds `['data-entry']`
- `domains.autoAssign` ← `True`
- `retry.maxComponentRetries` ← 3; `retry.maxCrewRetries` ← 2 (PRD §3.4 fixed values)
- `models.tier1` ← env `DAF_TIER1_MODEL` or `"claude-opus-4-20250514"`, same for tier2/tier3
- `buildConfig.tsTarget` ← `"ES2020"`; `buildConfig.moduleFormat` ← `"ESNext"`; `buildConfig.cssModules` ← `False`

Serialises to `{output_dir}/pipeline-config.json` using `json.dumps` with indent 2. Returns the absolute path.

**`ProjectScaffolder(BaseTool)`** — pure Python function `scaffold_project_files(brand_profile: dict, output_dir: str) -> dict[str, str]` that writes three template files:

- `tsconfig.json` — standard React + TypeScript library config with `target: "ES2020"`, `module: "ESNext"`, `moduleResolution: "bundler"`, `jsx: "react-jsx"`, strict mode enabled, `include: ["src"]`
- `vitest.config.ts` — configures vitest with `environment: "jsdom"`, `globals: true`, `setupFiles: ["./src/test-setup.ts"]`, and coverage thresholds matching `minTestCoverage` from the derived `pipeline-config.json`
- `vite.config.ts` — library-mode build: `entry: "src/index.ts"`, `formats: ["es", "cjs"]`, `fileName: (format) => \`index.${format}.js\``; external React and React-DOM; generates type declarations

Returns a `dict[str, str]` mapping each filename → absolute path written.

**`create_pipeline_config_agent()`** constructs a Tier 2 Sonnet agent equipped with both `ConfigGenerator` and `ProjectScaffolder` tools.

**`create_pipeline_config_task()`** constructs Task T5 which instructs the agent to:
1. Read the validated `brand-profile.json` from `output_dir`
2. Invoke `ConfigGenerator` with the Brand Profile JSON and `output_dir`
3. Invoke `ProjectScaffolder` with the Brand Profile JSON and `output_dir`
4. Return a summary confirming all four files written and their locations

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| Brand Profile field extraction (scope, a11yLevel, themes) | **Deterministic** | Direct key lookups — no reasoning needed |
| Quality gate threshold inference (scope + a11y → numeric thresholds) | **Deterministic** | Fixed mapping table; fully specified by the PRD |
| Beta component list selection | **Deterministic** | Hardcoded Comprehensive-delta list; scope is a direct lookup |
| Domain category inference from scope | **Deterministic** | Rule-based; scope tier is a controlled vocabulary |
| `pipeline-config.json` serialisation and file I/O | **Deterministic** | Pure data transformation |
| `tsconfig.json` / `vitest.config.ts` / `vite.config.ts` template rendering | **Deterministic** | Templates are fixed; only numeric thresholds are parameterised |
| Model tier env-var resolution | **Deterministic** | `os.environ.get` with hardcoded defaults |
| Agent task orchestration (deciding what inputs to pass, validating outputs) | **Agent (Tier 2 Sonnet)** | Agent reads the Brand Profile, decides what to pass to each tool, and validates the returned summary for completeness |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Agent 5: Pipeline Configuration Agent | Tier 2 — Analytical | `claude-sonnet-4-20250514` (default), overridable via `DAF_TIER2_MODEL` | Agent reads validated Brand Profile and coordinates two tool invocations. Appropriate for Tier 2 analytical reasoning — structured input, no large code generation. Consistent with §3.7 Tier 2 rationale. |

## Architecture Decisions

### Decision: All config inference is deterministic, not LLM-driven

**Context:** The `pipeline-config.json` schema (§3.8) is fully specified in the PRD, and every field's derivation rule can be expressed as a deterministic function of the Brand Profile. There are no ambiguous cases that require LLM reasoning.

**Decision:** Both `ConfigGenerator` and `ProjectScaffolder` are fully deterministic Python functions. The LLM (Agent 5) handles task orchestration — reading the Brand Profile path, deciding which tools to invoke, and validating the summary — but never authors config content.

**Consequences:** Config output is auditable, testable, and reproducible across runs. Value stability is guaranteed as long as the Brand Profile fields are stable. Changes to inference rules require code changes, not prompt changes.

---

### Decision: Scaffolding files use fixed templates, not Brand Profile-sensitive templates

**Context:** `tsconfig.json`, `vitest.config.ts`, and `vite.config.ts` need to be compatible with the React + TypeScript + Vitest + Vite stack that all downstream crews assume. The Brand Profile does not contain TypeScript or build configuration preferences — its `buildConfig` section only captures `tsTarget`, `moduleFormat`, and `cssModules`.

**Decision:** Templates are hardcoded to the standard DAF stack. The only Brand Profile-sensitive parameters are: `tsTarget` and `moduleFormat` (from the inferred `buildConfig`), and the coverage threshold in `vitest.config.ts` (from the inferred `minTestCoverage`). All other values are fixed.

**Consequences:** Simple, auditable template logic. The three files are always structurally valid for the DAF stack. If a future Brand Profile adds a `bundler` override field, a separate change updates the scaffolder.

---

### Decision: `ProjectScaffolder` also requires `pipeline-config.json` to already exist in order to read `minTestCoverage`

**Context:** `vitest.config.ts` embeds the coverage threshold from `pipeline-config.json`. The two tools must be invoked in order: `ConfigGenerator` first, then `ProjectScaffolder`.

**Decision:** Task T5's description explicitly sequences the tool calls. The agent is instructed to run `ConfigGenerator` first and confirm its output path before running `ProjectScaffolder`. `ProjectScaffolder` reads the written `pipeline-config.json` from disk (not passed in-memory) to get `minTestCoverage`, keeping the tool signatures independent and testable in isolation.

**Consequences:** Both tools can be unit tested independently. The agent's task description enforces call ordering through explicit instructions.

---

### Decision: `models` block in `pipeline-config.json` reads from environment variables at Agent 5 runtime

**Context:** Model tier assignments are configurable per-run via `DAF_TIER1_MODEL`, `DAF_TIER2_MODEL`, `DAF_TIER3_MODEL` environment variables (§3.7). These need to be captured in `pipeline-config.json` so that downstream crews (specifically the Governance Crew) can reference which models were used.

**Decision:** `ConfigGenerator` resolves model identifiers from environment variables at generation time using `os.environ.get(...)` with PRD-specified defaults (`claude-opus-4-20250514`, `claude-sonnet-4-20250514`, `claude-haiku-4-20250414`). The resolved values are written into `pipeline-config.json["models"]`.

**Consequences:** `pipeline-config.json` is a snapshot of the model configuration at generation time. If models change mid-run, the `pipeline-config.json` reflects the values at Phase 1 execution, not later phases. This is consistent with the checkpoint model (§3.4).

## Data Flow

```
[Interview CLI] ──raw brand-profile.json──► [Agent 1: Brand Discovery]
                                                       │
                                          validated brand-profile.json
                                                       │
                                                       ▼
                                     [Agent 5: Pipeline Configuration]
                                       (Task T5, this change)
                                                       │
                            ┌──────────────────────────┼────────────────────────┐
                            ▼                          ▼                        ▼
               pipeline-config.json           tsconfig.json           vitest.config.ts
                  vite.config.ts
                            │                          │                        │
                            ▼                          ▼                        ▼
               [Governance Crew, Phase 4b]    [Design-to-Code, Phase 3]  [Component Factory, Phase 3]
               (input seed for governance     (tsc --noEmit)             (vitest execution)
                artifacts)
```

## Retry & Failure Behavior

Agent 5 is in the DS Bootstrap Crew (Phase 1). Phase 1 agents do not have a per-agent retry boundary — the retry protocol (§3.4) applies at the Phase 1 ↔ Phase 2 boundary: the First Publish Agent (6) detects Phase 2 validation failures and re-invokes Phase 1 agents with rejection context.

For Agent 5 specifically:
- **Config generation failure** — if `ConfigGenerator` throws (e.g., malformed Brand Profile), the task fails and the error surfaces to the DS Bootstrap Crew. The crew-level error propagates to Agent 6 (First Publish Agent), which can re-invoke Agent 5 with corrective context or escalate to the user.
- **Scaffolding failure** — if `ProjectScaffolder` fails to write a file (e.g., permission error, disk full), the task fails immediately with a clear error message. This is non-recoverable without user intervention — Agent 6 escalates rather than retrying.
- **Phase 2 rejection loop** — if a Phase 2 crew fails because `tsconfig.json` is malformed (unlikely given templates, but possible), the First Publish Agent re-runs Agent 5 with the rejection context. Agent 5 re-invokes `ProjectScaffolder` to rewrite the scaffolding file.

Since Phase 4b (Governance Crew) is a Phases 4–6 crew, it uses the simpler "retry entire crew up to 2 attempts" model (§3.4). Agent 5's `pipeline-config.json` is only retried if the Governance Crew itself fails catastrophically — not because of schema issues in Agent 5's output.

## File Changes

- `src/daf/tools/config_generator.py` (new) — `ConfigGenerator(BaseTool)` + `generate_pipeline_config()` function
- `src/daf/tools/project_scaffolder.py` (new) — `ProjectScaffolder(BaseTool)` + `scaffold_project_files()` function
- `src/daf/agents/pipeline_config.py` (new) — `create_pipeline_config_agent()` + `create_pipeline_config_task()` factories
- `src/daf/tools/__init__.py` (modified) — export `ConfigGenerator`, `ProjectScaffolder`
- `src/daf/agents/__init__.py` (modified) — export `create_pipeline_config_agent`, `create_pipeline_config_task`
- `openspec/specs/pipeline-config/spec.md` (new) — capability spec for `pipeline-config.json` schema and scaffolded file contracts
- `tests/test_pipeline_config_agent.py` (new) — agent task integration tests
- `tests/test_config_generator.py` (new) — unit tests for `generate_pipeline_config()`
- `tests/test_project_scaffolder.py` (new) — unit tests for `scaffold_project_files()`
