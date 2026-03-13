# Proposal: p11-design-to-code-crew

## Intent

The pipeline orchestrator (p09) sequences all 9 crews end-to-end, and the Token Engine Crew (p10) now produces validated, compiled token files from raw DTCG input. However, the Design-to-Code Crew — Phase 3 of the pipeline — remains a no-op stub. Its stub creates empty `src/primitives/`, `src/components/`, and `reports/` directories with placeholder files but performs no spec analysis, no code generation, no render validation, and no generation reporting.

This means canonical component specs produced by the Bootstrap Crew (Agents 4–5 via p06 and p07) are never consumed for code generation. Downstream crews (Component Factory, Documentation, Governance, Analytics, Release) all depend on TSX source, test files, and Storybook stories that simply do not exist — rendering Phases 4–6 entirely symbolic.

This change delivers the real Design-to-Code Crew: 5 agents (12–16) that classify the generation scope, extract structural intent from each spec YAML, generate TypeScript/TSX source + tests + stories, validate render output, and assemble generation results into a structured report — producing the production code that all downstream crews depend on.

## Scope

### In scope

- **Agent 12: Scope Classification Agent** (`src/daf/agents/scope_classification.py`) — analyses the Brand Profile and all `specs/*.spec.yaml` files to classify the generation workload: primitives vs. stateful components vs. complex multi-variant components.  Builds a prioritised generation queue (primitives → simple → complex).
- **Agent 13: Intent Extraction Agent** (`src/daf/agents/intent_extraction.py`) — for each component spec, extracts layout structure, spacing model, breakpoint behaviour, interactive states, slot definitions, and a11y attribute requirements. Outputs a structured intent manifest per component.
- **Agent 14: Code Generation Agent** (`src/daf/agents/code_generation.py`) — generates production-quality TypeScript/TSX source, unit tests (`.test.tsx`), and Storybook stories (`.stories.tsx`) from intent manifests. Enforces zero hardcoded values (compiled tokens only), primitive composition, all spec variants, lint compliance, and `data-testid` attributes.
- **Agent 15: Render Validation Agent** (`src/daf/agents/render_validation.py`) — renders each generated component and every declared variant headlessly via Playwright. Verifies non-empty visual output per variant, absence of render errors and React exceptions, minimum dimension thresholds, and distinct rendering of interactive states. Captures baseline screenshots to `screenshots/`.
- **Agent 16: Result Assembly Agent** (`src/daf/agents/result_assembly.py`) — assembles the structured generation report per component (files generated, confidence score, warnings), writes `reports/generation-summary.json`, and maps spec → code → test → story for downstream crews.
- **Design-to-Code Crew factory** (`src/daf/crews/design_to_code.py`) — replaces the stub with a real CrewAI `Crew` that sequences tasks T1→T5 using all five agents.
- **New tools** (under `src/daf/tools/`):
  - `scope_analyzer.py` — classifies components as primitives / simple / complex based on spec fields and dependency graph.
  - `dependency_graph_builder.py` — resolves inter-component dependencies from `allowedChildren` and `composedOf` spec fields; produces topological order.
  - `priority_queue_builder.py` — converts dependency-ordered component list into a prioritised generation queue.
  - `spec_parser.py` — parses `*.spec.yaml` into structured Python dicts, validates required fields, resolves token bindings.
  - `layout_analyzer.py` — extracts layout model (flexbox/grid/absolute), spacing rhythm, and breakpoint config from spec.
  - `a11y_attribute_extractor.py` — maps spec-declared a11y requirements to concrete ARIA attributes and keyboard handler stubs.
  - `code_scaffolder.py` — renders TSX + test + story file triplets from intent manifests using Jinja2 templates.
  - `eslint_runner.py` — runs ESLint (via subprocess) on generated TSX files and returns structured lint results.
  - `story_template_generator.py` — generates Storybook CSF3 story files with one story per declared variant and one per interactive state.
  - `pattern_memory_store.py` — persists and retrieves generation patterns (prop shapes, token mappings, slot structures) across component generations within a single pipeline run.
  - `playwright_renderer.py` — drives headless Playwright to render React components and capture screenshots.
  - `render_error_detector.py` — parses Playwright console output for React exceptions, render errors, and hydration warnings.
  - `dimension_validator.py` — checks rendered component bounding boxes against minimum thresholds (no zero-width/zero-height elements).
  - `confidence_scorer.py` — computes a 0–100 confidence score per generated component based on spec completeness, lint cleanliness, variant coverage, and render pass rate.
  - `report_writer.py` — serialises structured generation results to `reports/generation-summary.json`.
- **Tests** — unit tests for every new tool and agent; integration test for the full Design-to-Code Crew flow (spec-in, TSX/tests/stories-out, report written).

### Out of scope

- Implementing the Component Factory Crew (Agents 17–20) — which validates and scores the generated output; that is the next change (p12).
- Modifying existing specs or token files — the Design-to-Code Crew is read-and-generate only; spec authoring remains with the Bootstrap Crew.
- Cross-phase retry routing from Agent 14 back to upstream agents — the retry protocol is managed by Agent 6 (First Publish Agent). This change only ensures Agent 14 produces structured rejection payloads that Agent 6 can consume.
- Visual regression diffing against prior baselines — this is a first-run generation; Render Validation captures baselines only (§4.3 Render Validation Agent).
- Platform-specific output targets beyond React/TypeScript (e.g., SwiftUI, Jetpack Compose).

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| Design-to-Code | Agent 12: Scope Classification Agent | **New implementation** — replaces stub task |
| Design-to-Code | Agent 13: Intent Extraction Agent | **New implementation** — replaces stub task |
| Design-to-Code | Agent 14: Code Generation Agent | **New implementation** — replaces stub task |
| Design-to-Code | Agent 15: Render Validation Agent | **New implementation** — replaces stub task |
| Design-to-Code | Agent 16: Result Assembly Agent | **New implementation** — replaces stub task |
| DS Bootstrap | Agent 4: Primitive Scaffolding Agent | Integration point — Design-to-Code reads `specs/primitives/*.spec.yaml` as primary input |
| DS Bootstrap | Agent 5: Core Component Agent | Integration point — Design-to-Code reads `specs/components/*.spec.yaml` as primary input |
| DS Bootstrap | Agent 6: First Publish Agent | Retry routing — Agent 6 detects Code Generation failures and re-invokes Agent 14 with rejection context (§3.4) |
| Token Engine | Agents 7–11 | Upstream dependency — `tokens/compiled/**` files are consumed by Agent 14 for token bindings; must be present and valid before Phase 3 |
| Component Factory | Agents 17–20 | Downstream consumers — they now receive real TSX source, tests, and stories instead of stubs |
| Documentation | Agents 21–25 | Downstream consumers — rely on generated component source for doc extraction and story counting |
| Analytics | Agents 36–40 | Token compliance reports and quality metrics operate against real generated code |

## PRD References

- §3.1 — Pipeline phases: Phase 3 (Design-to-Code) position, inputs (`specs/*.spec.yaml`, `tokens/compiled/*`), and outputs (`src/primitives/**`, `src/components/**`, `reports/generation-summary.json`, `screenshots/*`)
- §3.4 — Cross-phase retry routing: Code Generation Agent (14) ↔ Token Foundation Agent (2) / Primitive Scaffolding Agent (4) retry paths
- §3.6 — Crew I/O contracts: Design-to-Code inputs and outputs; Component Factory pick-up of `src/` files
- §4.3 — Design-to-Code Crew: all 5 agents (12–16), tasks T1–T5, NFRs (<5 min per component, <20 min starter scope, <60 min comprehensive)
- §4.3 (Render Validation Agent) — baseline capture policy: first run = baseline only, no regression comparison
- §8 — Exit criteria: Fatal check F7 (TypeScript compilation of generated source), Warning W1 (test failures in generated tests)

## Pipeline Impact

- [x] Pipeline phase ordering — Design-to-Code Crew replaces a stub in Phase 3; pipeline sequencing in Agent 6 is unchanged
- [x] Crew I/O contracts (§3.6) — Design-to-Code now writes real TSX source, test files, stories, and screenshots; downstream crews (Component Factory, Documentation, Governance) will consume real artifacts
- [x] Retry protocol (§3.4) — Agent 14 produces structured rejection payloads (failed component names, lint errors, missing token refs) that enable Agent 6 to trigger targeted per-component retry
- [ ] Human gate policy (§5) — not affected
- [x] Exit criteria (§8) — Fatal check F7 (TypeScript compilation) is enabled by this crew's output; Warning W1 (generated test failures) is produced by Agent 15
- [ ] Brand Profile schema (§6) — Brand Profile is read (for scope tier and a11y level) but its schema is not modified

## Approach

1. **New tools first (TDD)** — implement all 15 new tools with full unit test coverage before wiring agents. Tools are pure, deterministic functions that can be tested in isolation.
2. **Five agents** — implement Agents 12–16 as CrewAI `Agent` objects with tool bindings. Tier assignment:
   - Agent 12 (Scope Classification): Tier-3 Haiku — structured analysis of spec files, low ambiguity.
   - Agent 13 (Intent Extraction): Tier-2 Sonnet — interpretive reasoning over layout, state, and a11y semantics.
   - Agent 14 (Code Generation): Tier-1 Opus — highest complexity; produces production TypeScript with zero hardcoded values and full variant coverage.
   - Agent 15 (Render Validation): Tier-3 Haiku — deterministic pass/fail checks driven by tool output.
   - Agent 16 (Result Assembly): Tier-3 Haiku — structured aggregation and JSON serialisation.
3. **Design-to-Code Crew factory** — replace the stub in `src/daf/crews/design_to_code.py` with a real CrewAI `Crew` sequencing T1→T5. Preserve the factory function signature (`create_design_to_code_crew(output_dir)`) so the pipeline orchestrator requires no changes.
4. **Integration test** — one end-to-end test that feeds a minimal spec YAML + compiled token fixture and asserts that TSX source, test file, story file, and `generation-summary.json` are written correctly.

## Risks

- **Playwright availability in CI** — headless rendering requires a Playwright browser install; risk that the test environment lacks browsers. Mitigation: `playwright_renderer.py` tool detects absence and falls back to a no-render mode that skips screenshot capture and dimension checks (render validation is demoted to Warning, not Fatal).
- **LLM non-determinism in Code Generation Agent** — Agent 14 (Opus) may produce subtly different TypeScript on each run. Mitigation: pattern memory store (`pattern_memory_store.py`) accumulates accepted patterns within a run; unit tests use fixture-based expected outputs for critical structural assertions.
- **Spec completeness variance** — real spec YAMLs from p06/p07 may contain fields not covered by the intent extraction model. Mitigation: `spec_parser.py` normalises unknown fields to a `metadata` passthrough dict and logs warnings; unknown fields never cause hard failures.
- **Generated test fragility** — PRD §8 classifies test failures as Warning (not Fatal) for exactly this reason; generated tests may fail on first run due to environment or snapshot mismatches. Mitigation: `confidence_scorer.py` penalises failing tests in the confidence score without blocking the pipeline.
