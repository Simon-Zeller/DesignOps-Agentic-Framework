# TDD Plan: p11-design-to-code-crew

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

All new tools are pure Python functions with no LLM calls — they are unit-tested in complete isolation using `pytest`. All agents are tested using CrewAI agent mocking with pre-recorded tool outputs (fixture-based). The Design-to-Code Crew integration test wires all five agents together against a minimal spec fixture set, verifying file output without making real LLM calls (using `pytest-mock` to replace LLM calls with deterministic responses).

**Frameworks:** `pytest`, `pytest-mock`, `unittest.mock`
**Fixtures:** `tests/fixtures/specs/` — minimal spec YAMLs for Button, Box (primitive), and a complex component. `tests/fixtures/tokens/` — compiled token fixture `flat.json`.
**Coverage gate:** ≥80% line coverage per file (hard gate); ≥70% branch coverage (soft target).

---

## Test Cases

### Scope Analyzer (`scope_analyzer.py`)

#### Test: Primitive classification by known name

- **Maps to:** Requirement "Component spec discovery and classification" → Scenario "Primitives spec set"
- **Type:** unit
- **Given:** A spec dict with `component: Box` and no `variants` or `state` fields
- **When:** `classify_component(spec)` is called
- **Then:** Returns `"primitive"`
- **File:** `tests/test_scope_analyzer.py`

#### Test: Complex classification by variant count

- **Maps to:** Requirement "Component spec discovery and classification" → Scenario "Complex component detection"
- **Type:** unit
- **Given:** A spec dict with `variants: [a, b, c, d, e]` (5 entries)
- **When:** `classify_component(spec)` is called
- **Then:** Returns `"complex"`
- **File:** `tests/test_scope_analyzer.py`

#### Test: Simple classification for under-threshold component

- **Maps to:** Requirement "Component spec discovery and classification"
- **Type:** unit
- **Given:** A spec with `variants: [primary, secondary]` and no `state` field
- **When:** `classify_component(spec)` is called
- **Then:** Returns `"simple"`
- **File:** `tests/test_scope_analyzer.py`

---

### Dependency Graph Builder (`dependency_graph_builder.py`)

#### Test: Topological ordering respects composedOf dependencies

- **Maps to:** Requirement "Dependency-ordered priority queue construction" → Scenario "Correct primitive-first ordering"
- **Type:** unit
- **Given:** Specs `{'Button': {'composedOf': ['Pressable', 'Text']}, 'Pressable': {}, 'Text': {}}`
- **When:** `build_dependency_graph(specs)` and `topological_sort(graph)` are called
- **Then:** `Pressable` and `Text` appear before `Button` in the sorted list
- **File:** `tests/test_dependency_graph_builder.py`

#### Test: Circular dependency raises error

- **Maps to:** Requirement "Dependency-ordered priority queue construction" → Scenario "Circular dependency"
- **Type:** unit
- **Given:** Specs `{'CompA': {'composedOf': ['CompB']}, 'CompB': {'composedOf': ['CompA']}}`
- **When:** `build_dependency_graph(specs)` is called
- **Then:** Raises `CircularDependencyError` identifying both components
- **File:** `tests/test_dependency_graph_builder.py`

---

### Priority Queue Builder (`priority_queue_builder.py`)

#### Test: Primitives precede simple, simple precede complex

- **Maps to:** Requirement "Dependency-ordered priority queue construction"
- **Type:** unit
- **Given:** A classified component list with one `primitive`, one `simple`, one `complex` (in alphabetical order)
- **When:** `build_priority_queue(classified_components, topo_order)` is called
- **Then:** The queue is ordered primitive → simple → complex
- **File:** `tests/test_priority_queue_builder.py`

---

### Spec Parser (`spec_parser.py`)

#### Test: Parses valid spec YAML to structured dict

- **Maps to:** All spec-reading requirements
- **Type:** unit
- **Given:** A valid `button.spec.yaml` fixture with `variants`, `states`, `composedOf`, and `tokens` fields
- **When:** `parse_spec(path)` is called
- **Then:** Returns a dict with `component`, `variants`, `states`, `composedOf`, `tokens` keys populated
- **File:** `tests/test_spec_parser.py`

#### Test: Malformed YAML returns warning, not exception

- **Maps to:** Requirement "Component spec discovery and classification" (malformed YAML branch)
- **Type:** unit
- **Given:** A file containing invalid YAML (`key: [unclosed`)
- **When:** `parse_spec(path)` is called
- **Then:** Returns `None` and logs a warning (does not raise)
- **File:** `tests/test_spec_parser.py`

---

### Layout Analyzer (`layout_analyzer.py`)

#### Test: Extracts flexbox layout model

- **Maps to:** Requirement "Structured intent manifest extraction" → Scenario "Full manifest for a Button component"
- **Type:** unit
- **Given:** A spec dict with `layout: {type: flex, direction: row, align: center}`
- **When:** `extract_layout(spec)` is called
- **Then:** Returns `{model: "flex", direction: "row", align: "center"}`
- **File:** `tests/test_layout_analyzer.py`

#### Test: Defaults to flex when layout field is absent

- **Maps to:** Requirement "Structured intent manifest extraction" (absent field defaults)
- **Type:** unit
- **Given:** A spec dict with no `layout` field
- **When:** `extract_layout(spec)` is called
- **Then:** Returns `{model: "flex", direction: "row", align: "stretch"}`
- **File:** `tests/test_layout_analyzer.py`

---

### A11y Attribute Extractor (`a11y_attribute_extractor.py`)

#### Test: Maps button role to correct ARIA attributes

- **Maps to:** Requirement "Structured intent manifest extraction" (aria field)
- **Type:** unit
- **Given:** A spec with `a11y: {role: button}`
- **When:** `extract_a11y_attributes(spec)` is called
- **Then:** Returns `{role: "button", attrs: ["aria-label", "aria-disabled"], keyboard: ["Enter", "Space"]}`
- **File:** `tests/test_a11y_attribute_extractor.py`

---

### Code Scaffolder (`code_scaffolder.py`)

#### Test: Renders TSX skeleton with component name and token placeholders

- **Maps to:** Requirement "TSX source generation from intent manifest"
- **Type:** unit
- **Given:** An intent manifest for `Button` with two token bindings
- **When:** `scaffold_tsx(manifest)` is called
- **Then:** Returns a string containing `export function Button`, `data-testid`, and each token placeholder slot
- **File:** `tests/test_code_scaffolder.py`

#### Test: Renders story file with correct exports per variant

- **Maps to:** Requirement "Storybook story file generation" → Scenario "Button story coverage"
- **Type:** unit
- **Given:** An intent manifest for `Button` with `variants: [primary, secondary, ghost]`
- **When:** `scaffold_stories(manifest)` is called
- **Then:** The returned string contains named exports `Primary`, `Secondary`, `Ghost`
- **File:** `tests/test_code_scaffolder.py`

#### Test: Test skeleton includes accessibility placeholder

- **Maps to:** Requirement "Unit test file generation" → Scenario "Accessibility placeholder presence"
- **Type:** unit
- **Given:** Any intent manifest
- **When:** `scaffold_tests(manifest)` is called
- **Then:** The last non-empty line of the returned string is `// @accessibility-placeholder`
- **File:** `tests/test_code_scaffolder.py`

---

### ESLint Runner (`eslint_runner.py`)

#### Test: Returns structured violations from ESLint JSON output

- **Maps to:** Requirement "TSX source generation" → Scenario "Hardcoded value detected by lint retry"
- **Type:** unit
- **Given:** A temp file with `color: '#1a1a1a'` and a mocked ESLint subprocess returning JSON violation output
- **When:** `run_eslint(file_path)` is called
- **Then:** Returns a list of violation dicts with `rule`, `message`, and `line` fields
- **File:** `tests/test_eslint_runner.py`

#### Test: Returns empty list for clean file

- **Maps to:** Requirement "TSX source generation" (happy path lint)
- **Type:** unit
- **Given:** A temp file with no violations and mocked ESLint returning `[]`
- **When:** `run_eslint(file_path)` is called
- **Then:** Returns `[]`
- **File:** `tests/test_eslint_runner.py`

---

### Story Template Generator (`story_template_generator.py`)

#### Test: Generates one story per variant

- **Maps to:** Requirement "Storybook story file generation" → Scenario "Button story coverage"
- **Type:** unit
- **Given:** `variants: [primary, secondary, ghost]`, `component_name: Button`
- **When:** `generate_stories(component_name, variants, states)` is called
- **Then:** Output contains `export const Primary`, `export const Secondary`, `export const Ghost`
- **File:** `tests/test_story_template_generator.py`

---

### Pattern Memory Store (`pattern_memory_store.py`)

#### Test: Stores and retrieves prop shapes across components

- **Maps to:** Requirement "Pattern memory consistency" → Scenario "Consistent prop shape for related components"
- **Type:** unit
- **Given:** Pattern memory is initialised; `Card` prop shape stored with `padding: SpacingToken`
- **When:** `retrieve_similar_patterns("CardHeader")` is called
- **Then:** Returns the `Card` prop shape as a context hint
- **File:** `tests/test_pattern_memory_store.py`

#### Test: Returns empty on no matching patterns

- **Maps to:** Requirement "Pattern memory consistency" (no prior context)
- **Type:** unit
- **Given:** Empty pattern memory
- **When:** `retrieve_similar_patterns("NewComponent")` is called
- **Then:** Returns `[]` without raising
- **File:** `tests/test_pattern_memory_store.py`

---

### Playwright Renderer (`playwright_renderer.py`)

#### Test: Returns render_available False when browser not found

- **Maps to:** Requirement "Headless render validation" → Scenario "Playwright unavailable"
- **Type:** unit
- **Given:** `playwright_renderer.py` with mocked `shutil.which` returning `None` for all browsers
- **When:** `check_renderer_available()` is called
- **Then:** Returns `False`
- **File:** `tests/test_playwright_renderer.py`

#### Test: Returns screenshot path on successful render

- **Maps to:** Requirement "Baseline screenshot capture" → Scenario "Baseline screenshot naming"
- **Type:** unit (with Playwright mock)
- **Given:** Mocked Playwright context returning a 100×50 screenshot for `Button--primary`
- **When:** `render_component("Button", "primary", output_dir)` is called
- **Then:** Returns `{"path": "screenshots/Button/primary.png", "width": 100, "height": 50, "render_errors": []}`
- **File:** `tests/test_playwright_renderer.py`

---

### Render Error Detector (`render_error_detector.py`)

#### Test: Detects React exception in console log

- **Maps to:** Requirement "Headless render validation" → Scenario "React exception in console"
- **Type:** unit
- **Given:** Console log string containing `"Error: Cannot read properties of undefined"`
- **When:** `detect_render_errors(console_log)` is called
- **Then:** Returns `[{type: "react_exception", message: "Cannot read properties of undefined"}]`
- **File:** `tests/test_render_error_detector.py`

#### Test: Returns empty list for clean console log

- **Maps to:** Requirement "Headless render validation" (happy path)
- **Type:** unit
- **Given:** Console log with only `"React DevTools"` and normal log output
- **When:** `detect_render_errors(console_log)` is called
- **Then:** Returns `[]`
- **File:** `tests/test_render_error_detector.py`

---

### Dimension Validator (`dimension_validator.py`)

#### Test: Fails zero-size render

- **Maps to:** Requirement "Headless render validation" → Scenario "Variant produces zero-size output"
- **Type:** unit
- **Given:** Bounding box `{width: 0, height: 0}`
- **When:** `validate_dimensions(bbox, min_width=4, min_height=4)` is called
- **Then:** Returns `{passed: False, reason: "zero-dimension render"}`
- **File:** `tests/test_dimension_validator.py`

#### Test: Passes valid bounding box

- **Maps to:** Requirement "Headless render validation" (happy path)
- **Type:** unit
- **Given:** Bounding box `{width: 120, height: 40}`
- **When:** `validate_dimensions(bbox, min_width=4, min_height=4)` is called
- **Then:** Returns `{passed: True, reason: None}`
- **File:** `tests/test_dimension_validator.py`

---

### Confidence Scorer (`confidence_scorer.py`)

#### Test: Perfect score for fully passing component

- **Maps to:** Requirement "Per-component confidence scoring" → Scenario "Perfect score"
- **Type:** unit
- **Given:** All sub-scores at 1.0: spec completeness, lint pass, variant coverage, render pass, compilation pass
- **When:** `compute_confidence(scores)` is called
- **Then:** Returns `100`
- **File:** `tests/test_confidence_scorer.py`

#### Test: Excludes render sub-score when Playwright unavailable

- **Maps to:** Requirement "Per-component confidence scoring" (Playwright fallback)
- **Type:** unit
- **Given:** `render_available: False`, all other sub-scores at 1.0
- **When:** `compute_confidence(scores)` is called
- **Then:** Returns `100` (render weight excluded and remaining weights scaled proportionally)
- **File:** `tests/test_confidence_scorer.py`

#### Test: Low confidence flag set below 60

- **Maps to:** Requirement "Per-component confidence scoring" (low_confidence threshold)
- **Type:** unit
- **Given:** Sub-scores producing a total of 55
- **When:** `compute_confidence(scores)` is called
- **Then:** Returns `{score: 55, low_confidence: True, high_confidence: False}`
- **File:** `tests/test_confidence_scorer.py`

---

### Report Writer (`report_writer.py`)

#### Test: Writes valid JSON to generation-summary.json

- **Maps to:** Requirement "Generation summary report assembly" → Scenario "Full successful run"
- **Type:** unit
- **Given:** A structured per-component result list for 10 components, all generated successfully
- **When:** `write_generation_summary(results, output_dir)` is called
- **Then:** `reports/generation-summary.json` exists and `json.loads` succeeds
- **AND:** `total_components == 10`, `generated == 10`, `failed == 0`
- **File:** `tests/test_report_writer.py`

#### Test: Partial failure correctly reflected

- **Maps to:** Requirement "Generation summary report assembly" → Scenario "Partial failure run"
- **Type:** unit
- **Given:** 10 components where 1 has `files_written: []`
- **When:** `write_generation_summary(results, output_dir)` is called
- **Then:** `generated == 9`, `failed == 1`
- **File:** `tests/test_report_writer.py`

#### Test: Report written even when all components fail

- **Maps to:** Requirement "Generation summary report assembly" → Scenario "Report always written on crew exit"
- **Type:** unit
- **Given:** 3 components, all with `files_written: []`
- **When:** `write_generation_summary(results, output_dir)` is called
- **Then:** `reports/generation-summary.json` is written, is valid JSON, and `failed == 3`
- **File:** `tests/test_report_writer.py`

---

### Agent Tests (with LLM mocking)

#### Test: Scope Classification Agent produces priority queue JSON

- **Maps to:** Requirement "Component spec discovery and classification"
- **Type:** unit (mocked LLM)
- **Given:** Three fixture specs (Box primitive, Button simple, DataGrid complex) in a temp `specs/` directory; LLM responses mocked
- **When:** Scope Classification Agent runs task T1
- **Then:** `scope_classifier_output.json` is written with `components` ordered: Box, Button, DataGrid
- **File:** `tests/test_scope_classification_agent.py`

#### Test: Intent Extraction Agent produces manifests for all queued components

- **Maps to:** Requirement "Structured intent manifest extraction"
- **Type:** unit (mocked LLM)
- **Given:** Scope classifier output with Box and Button; compiled token fixture; LLM responses mocked
- **When:** Intent Extraction Agent runs task T2
- **Then:** `intent_manifests.json` is written with two manifests, each having `component_name`, `layout`, `token_bindings`, `aria`
- **File:** `tests/test_intent_extraction_agent.py`

#### Test: Code Generation Agent writes three files per component

- **Maps to:** Requirement "TSX source generation" → Scenario "Successful Button TSX generation"
- **Type:** unit (mocked LLM)
- **Given:** Intent manifest for Button; compiled token fixture; mocked LLM returning valid TSX
- **When:** Code Generation Agent runs task T3
- **Then:** `src/components/Button/Button.tsx`, `src/components/Button/Button.test.tsx`, `src/components/Button/Button.stories.tsx` are written
- **File:** `tests/test_code_generation_agent.py`

#### Test: Code Generation Agent writes rejection file on unresolvable token

- **Maps to:** Requirement "Structured rejection on unresolvable generation" → Scenario "Unresolvable token reference"
- **Type:** unit (mocked LLM)
- **Given:** Intent manifest with `token_bindings` referencing a non-existent key
- **When:** Code Generation Agent runs task T3
- **Then:** `reports/generation-rejection.json` is written with `rejected_components[0].reason == "unresolvable_token_ref"`
- **File:** `tests/test_code_generation_agent.py`

#### Test: Render Validation Agent sets render_available False in Playwright-less env

- **Maps to:** Requirement "Headless render validation" → Scenario "Playwright unavailable"
- **Type:** unit (mocked Playwright check)
- **Given:** `playwright_renderer.check_renderer_available()` mocked to return False
- **When:** Render Validation Agent runs task T4
- **Then:** All components in the result dict have `render_available: False`
- **File:** `tests/test_render_validation_agent.py`

#### Test: Result Assembly Agent writes complete and valid generation-summary.json

- **Maps to:** Requirement "Generation summary report assembly" → Scenario "Full successful run"
- **Type:** unit (mocked LLM)
- **Given:** Pre-populated per-component result dicts for 3 components (all generated, all render passing)
- **When:** Result Assembly Agent runs task T5
- **Then:** `reports/generation-summary.json` is valid JSON with `total_components: 3`, `generated: 3`, `failed: 0`
- **File:** `tests/test_result_assembly_agent.py`

---

### Integration Test (Design-to-Code Crew)

#### Test: Full crew run writes expected file tree from fixture specs

- **Maps to:** Full Design-to-Code Crew flow (T1→T5)
- **Type:** integration (mocked LLM, mocked Playwright)
- **Given:** A temp output directory with fixture specs (Box primitive, Button simple) and compiled token fixture
- **When:** `create_design_to_code_crew(output_dir).run()` is called
- **Then:** The following files exist: `src/primitives/Box.tsx`, `src/primitives/Box.test.tsx`, `src/primitives/Box.stories.tsx`, `src/components/Button/Button.tsx`, `src/components/Button/Button.test.tsx`, `src/components/Button/Button.stories.tsx`, `reports/generation-summary.json`
- **AND:** `generation-summary.json` is valid JSON with `total_components == 2`, `generated == 2`
- **File:** `tests/test_design_to_code_crew.py`

---

## Edge Case Tests

#### Test: Spec with no token bindings generates without crash

- **Maps to:** Requirement "TSX source generation" (empty token_bindings)
- **Type:** unit
- **Given:** An intent manifest with `token_bindings: {}`
- **When:** `scaffold_tsx(manifest)` is called
- **Then:** Returns a valid string (no exception)
- **File:** `tests/test_code_scaffolder.py`

#### Test: Component with no variants generates single default rendering

- **Maps to:** Requirement "TSX source generation" (primitive with no variants)
- **Type:** unit
- **Given:** An intent manifest with `variants: []` (Box primitive)
- **When:** `scaffold_tsx(manifest)` is called
- **Then:** Returns a valid string with `export function Box` and no variant conditional logic
- **File:** `tests/test_code_scaffolder.py`

#### Test: Dependency graph with isolated component (no deps, no dependants)

- **Maps to:** Requirement "Dependency-ordered priority queue construction"
- **Type:** unit
- **Given:** Specs with `CompA` having no `composedOf` and no component depending on it
- **When:** `build_dependency_graph(specs)` is called
- **Then:** `CompA` appears in the result without error; position is after primitives, before complex
- **File:** `tests/test_dependency_graph_builder.py`

#### Test: confidence_scorer with all zero sub-scores returns 0

- **Maps to:** Requirement "Per-component confidence scoring" (boundary)
- **Type:** unit
- **Given:** All sub-scores at 0.0
- **When:** `compute_confidence(scores)` is called
- **Then:** Returns `{score: 0, low_confidence: True, high_confidence: False}`
- **File:** `tests/test_confidence_scorer.py`

#### Test: Report writer creates reports/ directory if absent

- **Maps to:** Requirement "Generation summary report assembly" (directory creation)
- **Type:** unit
- **Given:** An output directory with no `reports/` subdirectory
- **When:** `write_generation_summary(results, output_dir)` is called
- **Then:** `reports/` is created and the file is written without error
- **File:** `tests/test_report_writer.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Line coverage (all new tool files) | ≥80% | PRD quality gate requirement |
| Line coverage (all new agent files) | ≥80% | PRD quality gate requirement |
| Branch coverage (tool files) | ≥70% | Covers conditional logic (fallback paths, error branches) |
| Integration test: file output assertions | 100% of expected files | Verifies crew I/O contract for downstream crews |

---

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_scope_classification_agent.py` | new | Agent 12 unit tests |
| `tests/test_intent_extraction_agent.py` | new | Agent 13 unit tests |
| `tests/test_code_generation_agent.py` | new | Agent 14 unit tests |
| `tests/test_render_validation_agent.py` | new | Agent 15 unit tests |
| `tests/test_result_assembly_agent.py` | new | Agent 16 unit tests |
| `tests/test_scope_analyzer.py` | new | Tool unit tests |
| `tests/test_dependency_graph_builder.py` | new | Tool unit tests |
| `tests/test_priority_queue_builder.py` | new | Tool unit tests |
| `tests/test_spec_parser.py` | new | Tool unit tests |
| `tests/test_layout_analyzer.py` | new | Tool unit tests |
| `tests/test_a11y_attribute_extractor.py` | new | Tool unit tests |
| `tests/test_code_scaffolder.py` | new | Tool unit tests |
| `tests/test_eslint_runner.py` | new | Tool unit tests |
| `tests/test_story_template_generator.py` | new | Tool unit tests |
| `tests/test_pattern_memory_store.py` | new | Tool unit tests |
| `tests/test_playwright_renderer.py` | new | Tool unit tests (Playwright mocked) |
| `tests/test_render_error_detector.py` | new | Tool unit tests |
| `tests/test_dimension_validator.py` | new | Tool unit tests |
| `tests/test_confidence_scorer.py` | new | Tool unit tests |
| `tests/test_report_writer.py` | new | Tool unit tests |
| `tests/test_design_to_code_crew.py` | new | Integration test (full crew, mocked LLM + Playwright) |
