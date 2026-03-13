# Design: p11-design-to-code-crew

## Technical Approach

The Design-to-Code Crew replaces the no-op stub in `src/daf/crews/design_to_code.py` with a real CrewAI `Crew` that sequences five agents (12–16) across tasks T1–T5. The crew takes two inputs from the shared output directory: `specs/*.spec.yaml` written by the Bootstrap Crew and `tokens/compiled/**` written by the Token Engine Crew.

The crew follows a strict linear pipeline:

1. **T1 — Scope Classification** (Agent 12): Reads all spec YAMLs and the brand profile, classifies each component as a primitive or a stateful/multi-variant component, and builds a dependency-ordered priority queue (primitives first).
2. **T2 — Intent Extraction** (Agent 13): Iterates the priority queue and, for each component spec, extracts a structured intent manifest covering layout model, spacing rhythm, breakpoint behaviour, interactive states, slot definitions, and a11y attribute requirements.
3. **T3 — Code Generation** (Agent 14): For each intent manifest, generates three production files using Jinja2 templates and LLM-assisted code: `Component.tsx`, `Component.test.tsx`, and `Component.stories.tsx`. Runs ESLint on each generated file and retries with lint feedback if violations are found (max 2 lint-retry cycles per file).
4. **T4 — Render Validation** (Agent 15): Drives headless Playwright to render each generated component. Validates non-empty output, absent React exceptions, minimum dimension thresholds, and distinct interactive states. Captures baseline screenshots.
5. **T5 — Result Assembly** (Agent 16): Aggregates per-component results into a confidence-scored generation report and writes `reports/generation-summary.json`.

All 15 new tools are deterministic Python modules with no LLM calls; agents call them as CrewAI tools. This keeps LLM reasoning bounded to classification, intent extraction, and code synthesis — all other operations are verifiable, repeatable, and unit-testable.

The crew factory signature (`create_design_to_code_crew(output_dir: str) -> Crew`) is preserved from the stub, so the pipeline orchestrator (`src/daf/agents/pipeline_config.py` / `first_publish.py`) requires no code changes.

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| Classify components as primitive/simple/complex | Deterministic (`scope_analyzer.py`) | Rule-based: presence of `variants`, `state`, `children` fields in spec YAML |
| Build topological dependency order | Deterministic (`dependency_graph_builder.py`) | Graph traversal of `allowedChildren` / `composedOf` spec fields |
| Assemble priority generation queue | Deterministic (`priority_queue_builder.py`) | Stable sort on classification tier and dependency depth |
| Parse spec YAML to typed dict | Deterministic (`spec_parser.py`) | Structural transformation, no ambiguity |
| Extract layout model from spec | Agent 13 (LLM: Sonnet) | Layout model can be implicit in spec; requires interpretation of spacing rhythm and breakpoint intent |
| Map a11y requirements to ARIA/keyboard stubs | Deterministic (`a11y_attribute_extractor.py`) | ARIA role mapping is rule-based (WAI-ARIA spec) |
| Generate TSX / test / story source | Agent 14 (LLM: Opus) | Production-quality React code with zero hardcoded values and full variant coverage requires generative reasoning |
| Scaffold initial file structure from intent | Deterministic (`code_scaffolder.py`) | Template-driven: known file skeletons with placeholder slots |
| Lint generated TSX files | Deterministic (`eslint_runner.py`) | Subprocess call; output is parsed JSON |
| Generate story file from variant list | Deterministic (`story_template_generator.py`) | CSF3 boilerplate templating; one story per variant |
| Persist/retrieve generation patterns | Deterministic (`pattern_memory_store.py`) | In-memory dict scoped to a pipeline run; no LLM involvement |
| Render component headlessly | Deterministic (`playwright_renderer.py`) | Playwright subprocess; pure I/O |
| Detect render errors | Deterministic (`render_error_detector.py`) | Parses Playwright console output with regex patterns |
| Validate rendered dimensions | Deterministic (`dimension_validator.py`) | Checks bounding-box numbers against minimum thresholds |
| Decide whether a render failure is fatal | Agent 15 (LLM: Haiku) | Distinguishes warning-level visual quirks from blocking render failures |
| Compute per-component confidence score | Deterministic (`confidence_scorer.py`) | Weighted formula: spec completeness, lint pass rate, variant coverage, render pass rate |
| Serialise generation report | Deterministic (`report_writer.py`) | JSON dump with fixed schema |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Agent 12: Scope Classification Agent | Tier-3 | Claude Haiku | Structured analysis of spec YAML fields; classification rules are deterministic; LLM is used only for ambiguous specs missing classification signals |
| Agent 13: Intent Extraction Agent | Tier-2 | Claude Sonnet | Interpretive reasoning over layout semantics, implicit spacing models, and a11y intent; requires language understanding beyond pure rule application |
| Agent 14: Code Generation Agent | Tier-1 | Claude Opus | Highest complexity task in the pipeline; must produce production TypeScript with zero hardcoded values, correct primitive composition, and full variant coverage across potentially 25+ components |
| Agent 15: Render Validation Agent | Tier-3 | Claude Haiku | Pass/fail classification of deterministic tool output; no generative reasoning required |
| Agent 16: Result Assembly Agent | Tier-3 | Claude Haiku | Structured aggregation and JSON serialisation from collected tool results |

## Architecture Decisions

### Decision: Per-component lint-retry loop inside Agent 14 (max 2 cycles)

**Context:** ESLint violations in generated TypeScript are common on first pass. Without an inline correction loop, every lint failure would escalate to Agent 6's cross-phase retry, triggering a full T3 re-run.

**Decision:** Agent 14 runs `eslint_runner.py` after each file is generated. If violations are found, it feeds the lint output back to the LLM with a correction prompt (max 2 retries per file). If the file still fails after 2 retries, it writes the file with a lint-failure annotation in the generation report (Warning, not Fatal) and continues to the next component.

**Consequences:** Reduces unnecessary full-crew retries for fixable lint issues. The 2-retry cap prevents runaway LLM loops on systems that produce persistent violations. Components with persistent lint failures are tracked in `generation-summary.json` for operator visibility.

---

### Decision: Pattern Memory Store is scoped to a single pipeline run

**Context:** Agent 14 generates up to 25+ components sequentially. Without memory, each component is generated in isolation, leading to prop shape inconsistencies and token mapping drift across components.

**Decision:** `pattern_memory_store.py` is an in-memory dict initialised at crew start and passed as a shared tool to all Agent 14 task calls. It persists patterns (prop shapes, token bindings, slot structures) across component generations and is discarded when the crew exits.

**Consequences:** Consistency within a single run is improved without requiring a persistent database. Cross-run consistency is not addressed by this change (out of scope); future runs start fresh.

---

### Decision: Playwright fallback mode for environments without browser binaries

**Context:** Headless rendering requires Playwright browser binaries, which may not be available in all CI environments.

**Decision:** `playwright_renderer.py` performs a binary availability check on startup. If no browser is found, it sets `render_available=False` and returns a degenerate result (no screenshot, no dimension data, `render_available=False` flag). Agent 15 treats a degenerate result as a Warning (not Fatal) in the generation report.

**Consequences:** The pipeline runs to completion in browser-less environments with reduced validation coverage. The generation-summary.json records `render_available=False` per component, enabling operators to identify components that were not render-validated.

---

### Decision: Generated test files do not include Accessibility Agent appends yet

**Context:** The Accessibility Agent (19) is in the Component Factory Crew (p12), not the Design-to-Code Crew. Its appended a11y `describe` blocks are added to `.test.tsx` files *after* Phase 3.

**Decision:** Code Generation Agent (14) produces `.test.tsx` files with a clear `// @accessibility-placeholder` comment block at the end, marking the insertion point for Agent 19's additions. Agent 14 does not generate a11y test content.

**Consequences:** Test files produced in Phase 3 are well-formed but incomplete for a11y coverage. Agent 19 (p12) will look for `// @accessibility-placeholder` and append after it.

## Data Flow

```
[DS Bootstrap Crew (p06/p07)]
  ──writes──► specs/primitives/*.spec.yaml
  ──writes──► specs/components/**/*.spec.yaml
              │
              ├─────────────────────────────────────────────────────┐
              ▼                                                     ▼
[Token Engine Crew (p10)]                          [Design-to-Code Crew (p11)]
  ──writes──► tokens/compiled/variables.css          reads specs/*.spec.yaml ◄──┘
  ──writes──► tokens/compiled/tokens.ts              reads tokens/compiled/** ◄─┘
  ──writes──► tokens/compiled/flat.json              reads brand-profile.json
                                                      │
                                                      ├── writes ──► src/primitives/*.tsx
                                                      ├── writes ──► src/primitives/*.test.tsx
                                                      ├── writes ──► src/primitives/*.stories.tsx
                                                      ├── writes ──► src/components/**/*.tsx
                                                      ├── writes ──► src/components/**/*.test.tsx
                                                      ├── writes ──► src/components/**/*.stories.tsx
                                                      ├── writes ──► reports/generation-summary.json
                                                      └── writes ──► screenshots/*

[Component Factory Crew (p12)]
  reads ──► src/primitives/**
  reads ──► src/components/**
  reads ──► reports/generation-summary.json
```

## Retry & Failure Behavior

**Intra-T3 lint-retry loop (Agent 14):** On ESLint failure, Agent 14 retries the affected file up to 2 times with lint context injected into the generation prompt. After 2 retries, the file is written as-is with a `lint_warnings` entry in the generation report (Warning-level). This never triggers the cross-phase retry protocol.

**Cross-phase retry (Agent 6 ↔ Agent 14):** If Agent 14 produces a structured rejection — missing token refs or unresolvable spec intent — it writes `reports/generation-rejection.json` with the failed component name, missing refs, and reason codes. Agent 6 (First Publish Agent) reads this file after Phase 3 completes, and if fatal rejection entries are present, it re-invokes the Design-to-Code Crew with the rejection context for up to 2 crew-level retries (§3.4). On each retry, the rejection context is accumulated (not replaced) so Agent 14 has full history.

**Render validation failure (Agent 15):** A component that fails render validation (non-empty check, dimension check, React exception) is marked `render_failed: true` in `generation-summary.json`. This is a Warning (not Fatal) per PRD §8. The Component Factory Crew (p12) will attempt to validate the source regardless; if compilation also fails, Agent 6 triggers a cross-phase retry.

**Playwright unavailable:** Treated as Warning per the fallback mode decision above. `render_available: false` is set; downstream crews receive the generated source without screenshot baselines.

## File Changes

### New — Agents
- `src/daf/agents/scope_classification.py` (new) — Agent 12: Scope Classification Agent
- `src/daf/agents/intent_extraction.py` (new) — Agent 13: Intent Extraction Agent
- `src/daf/agents/code_generation.py` (new) — Agent 14: Code Generation Agent
- `src/daf/agents/render_validation.py` (new) — Agent 15: Render Validation Agent
- `src/daf/agents/result_assembly.py` (new) — Agent 16: Result Assembly Agent

### Modified — Crews
- `src/daf/crews/design_to_code.py` (modified) — replace stub with real CrewAI `Crew` sequencing T1→T5

### New — Tools
- `src/daf/tools/scope_analyzer.py` (new) — scope classification logic
- `src/daf/tools/dependency_graph_builder.py` (new) — topological dependency ordering
- `src/daf/tools/priority_queue_builder.py` (new) — generation queue assembly
- `src/daf/tools/spec_parser.py` (new) — YAML spec to structured dict
- `src/daf/tools/layout_analyzer.py` (new) — layout/spacing/breakpoint extraction
- `src/daf/tools/a11y_attribute_extractor.py` (new) — ARIA attribute mapping
- `src/daf/tools/code_scaffolder.py` (new) — Jinja2 file template rendering
- `src/daf/tools/eslint_runner.py` (new) — ESLint subprocess runner
- `src/daf/tools/story_template_generator.py` (new) — CSF3 story file generation
- `src/daf/tools/pattern_memory_store.py` (new) — run-scoped pattern cache
- `src/daf/tools/playwright_renderer.py` (new) — headless Playwright rendering
- `src/daf/tools/render_error_detector.py` (new) — React exception/error detection
- `src/daf/tools/dimension_validator.py` (new) — bounding-box threshold checks
- `src/daf/tools/confidence_scorer.py` (new) — per-component confidence formula
- `src/daf/tools/report_writer.py` (new) — generation-summary.json serialiser

### New — Tests
- `tests/test_scope_classification_agent.py` (new)
- `tests/test_intent_extraction_agent.py` (new)
- `tests/test_code_generation_agent.py` (new)
- `tests/test_render_validation_agent.py` (new)
- `tests/test_result_assembly_agent.py` (new)
- `tests/test_scope_analyzer.py` (new)
- `tests/test_dependency_graph_builder.py` (new)
- `tests/test_priority_queue_builder.py` (new)
- `tests/test_spec_parser.py` (new)
- `tests/test_layout_analyzer.py` (new)
- `tests/test_a11y_attribute_extractor.py` (new)
- `tests/test_code_scaffolder.py` (new)
- `tests/test_eslint_runner.py` (new)
- `tests/test_story_template_generator.py` (new)
- `tests/test_pattern_memory_store.py` (new)
- `tests/test_playwright_renderer.py` (new)
- `tests/test_render_error_detector.py` (new)
- `tests/test_dimension_validator.py` (new)
- `tests/test_confidence_scorer.py` (new)
- `tests/test_report_writer.py` (new)
- `tests/test_design_to_code_crew.py` (new) — integration test
