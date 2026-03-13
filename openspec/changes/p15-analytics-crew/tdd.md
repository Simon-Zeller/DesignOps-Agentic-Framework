# TDD Plan: p15-analytics-crew

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

All tests are **unit tests** written in Python using `pytest`. LLM calls are avoided in unit tests — `crewai.Agent` is instantiated using a test API key (`ANTHROPIC_API_KEY=test-key`), and no `.kickoff()` is called at the unit level. Integration-level crew tests verify constructor behaviour and pre-flight guards only (matching the pattern established by `test_governance_crew.py`).

Framework: `pytest` + `tmp_path` fixture for isolated file-system state.

Coverage target per new module: ≥ 80% line coverage, ≥ 70% branch coverage.

---

## Test Cases

### Analytics Crew Factory

#### Test: Factory returns `crewai.Crew` when specs exist

- **Maps to:** Requirement "Analytics Crew factory replaces stub" → Scenario "Factory returns a real crew"
- **Type:** integration
- **Given:** `tmp_path/specs/button.spec.yaml` exists with minimal YAML content
- **When:** `create_analytics_crew(str(tmp_path))` is called
- **Then:** Return value is an instance of `crewai.Crew` (not `StubCrew`)
- **File:** `tests/test_analytics_crew.py`

#### Test: Factory raises `RuntimeError` when no spec files exist

- **Maps to:** Requirement "Analytics Crew factory replaces stub" → Scenario "Pre-flight guard fires with missing specs"
- **Type:** integration
- **Given:** `tmp_path` has no `specs/` directory
- **When:** `create_analytics_crew(str(tmp_path))` is called
- **Then:** `RuntimeError` is raised
- AND error message mentions `specs/*.spec.yaml`
- **File:** `tests/test_analytics_crew.py`

#### Test: Factory raises `RuntimeError` when `specs/` exists but is empty

- **Maps to:** Requirement "Analytics Crew factory replaces stub" → Scenario "Pre-flight guard fires with missing specs"
- **Type:** integration
- **Given:** `tmp_path/specs/` directory exists but contains no `.spec.yaml` files
- **When:** `create_analytics_crew(str(tmp_path))` is called
- **Then:** `RuntimeError` is raised
- **File:** `tests/test_analytics_crew.py`

#### Test: Crew has exactly 5 agents and 5 tasks

- **Maps to:** Requirement "Analytics Crew factory replaces stub" → Acceptance Criteria
- **Type:** integration
- **Given:** Valid `specs/` directory with one spec file
- **When:** `create_analytics_crew(str(tmp_path))` is called
- **Then:** `crew.agents` has length 5
- AND `crew.tasks` has length 5
- **File:** `tests/test_analytics_crew.py`

---

### Agent 31 – Usage Tracking Agent

#### Test: Factory returns a `crewai.Agent`

- **Maps to:** Requirement "Agent 31 – Usage Tracking" → Acceptance Criteria
- **Type:** unit
- **Given:** `ANTHROPIC_API_KEY` set to `"test-key"`, valid `output_dir`
- **When:** `create_usage_tracking_agent("claude-3-5-haiku-20241022", str(tmp_path))` is called
- **Then:** Return value is an instance of `crewai.Agent`
- **File:** `tests/test_usage_tracking_agent.py`

#### Test: Agent role contains "usage" keyword

- **Maps to:** Requirement "Agent 31 – Usage Tracking" → Acceptance Criteria
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_usage_tracking_agent(model, str(tmp_path))` is called
- **Then:** `agent.role.lower()` contains `"usage"`
- **File:** `tests/test_usage_tracking_agent.py`

#### Test: Agent uses Haiku model

- **Maps to:** Design "Model Tier Assignment" → Agent 31 Tier 3
- **Type:** unit
- **Given:** Model string `"claude-3-5-haiku-20241022"`
- **When:** `create_usage_tracking_agent(model, str(tmp_path))` is called
- **Then:** `agent.llm.model.lower()` contains `"haiku"`
- **File:** `tests/test_usage_tracking_agent.py`

#### Test: Agent includes required tools

- **Maps to:** Requirement "Agent 31 – Usage Tracking" → Acceptance Criteria (tools)
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_usage_tracking_agent(model, str(tmp_path))` is called
- **Then:** Tool set includes `ASTImportScanner`, `TokenUsageMapper`, `DependencyGraphBuilder`
- **File:** `tests/test_usage_tracking_agent.py`

---

### Agent 32 – Token Compliance Agent

#### Test: Factory returns a `crewai.Agent`

- **Maps to:** Requirement "Agent 32 – Token Compliance" → Acceptance Criteria
- **Type:** unit
- **Given:** `ANTHROPIC_API_KEY` set to `"test-key"`, valid `output_dir`
- **When:** `create_token_compliance_agent("claude-3-5-haiku-20241022", str(tmp_path))` is called
- **Then:** Return value is an instance of `crewai.Agent`
- **File:** `tests/test_token_compliance_agent.py`

#### Test: Agent role contains "compliance" keyword

- **Maps to:** Requirement "Agent 32 – Token Compliance" → Acceptance Criteria
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_token_compliance_agent(model, str(tmp_path))` is called
- **Then:** `agent.role.lower()` contains `"compliance"`
- **File:** `tests/test_token_compliance_agent.py`

#### Test: Agent uses Haiku model

- **Maps to:** Design "Model Tier Assignment" → Agent 32 Tier 3
- **Type:** unit
- **Given:** Model string `"claude-3-5-haiku-20241022"`
- **When:** `create_token_compliance_agent(model, str(tmp_path))` is called
- **Then:** `agent.llm.model.lower()` contains `"haiku"`
- **File:** `tests/test_token_compliance_agent.py`

#### Test: Agent includes required tools

- **Maps to:** Requirement "Agent 32 – Token Compliance" → Acceptance Criteria (tools)
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_token_compliance_agent(model, str(tmp_path))` is called
- **Then:** Tool set includes `TokenComplianceScannerTool` and `TokenUsageMapper`
- **File:** `tests/test_token_compliance_agent.py`

---

### Agent 33 – Drift Detection Agent

#### Test: Factory returns a `crewai.Agent`

- **Maps to:** Requirement "Agent 33 – Drift Detection" → Acceptance Criteria
- **Type:** unit
- **Given:** `ANTHROPIC_API_KEY` set to `"test-key"`, valid `output_dir`
- **When:** `create_drift_detection_agent("claude-3-5-sonnet-20241022", str(tmp_path))` is called
- **Then:** Return value is an instance of `crewai.Agent`
- **File:** `tests/test_drift_detection_agent.py`

#### Test: Agent role contains "drift" keyword

- **Maps to:** Requirement "Agent 33 – Drift Detection" → Acceptance Criteria
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_drift_detection_agent(model, str(tmp_path))` is called
- **Then:** `agent.role.lower()` contains `"drift"`
- **File:** `tests/test_drift_detection_agent.py`

#### Test: Agent uses Sonnet model

- **Maps to:** Design "Model Tier Assignment" → Agent 33 Tier 2
- **Type:** unit
- **Given:** Model string `"claude-3-5-sonnet-20241022"`
- **When:** `create_drift_detection_agent(model, str(tmp_path))` is called
- **Then:** `agent.llm.model.lower()` contains `"sonnet"`
- **File:** `tests/test_drift_detection_agent.py`

#### Test: Agent includes required tools

- **Maps to:** Requirement "Agent 33 – Drift Detection" → Acceptance Criteria (tools)
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_drift_detection_agent(model, str(tmp_path))` is called
- **Then:** Tool set includes `StructuralComparator`, `DriftReporter`, `DocPatcher`
- **File:** `tests/test_drift_detection_agent.py`

---

### Agent 34 – Pipeline Completeness Agent

#### Test: Factory returns a `crewai.Agent`

- **Maps to:** Requirement "Agent 34 – Pipeline Completeness" → Acceptance Criteria
- **Type:** unit
- **Given:** `ANTHROPIC_API_KEY` set to `"test-key"`, valid `output_dir`
- **When:** `create_pipeline_completeness_agent("claude-3-5-haiku-20241022", str(tmp_path))` is called
- **Then:** Return value is an instance of `crewai.Agent`
- **File:** `tests/test_pipeline_completeness_agent.py`

#### Test: Agent role contains "completeness" keyword

- **Maps to:** Requirement "Agent 34 – Pipeline Completeness" → Acceptance Criteria
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_pipeline_completeness_agent(model, str(tmp_path))` is called
- **Then:** `agent.role.lower()` contains `"completeness"`
- **File:** `tests/test_pipeline_completeness_agent.py`

#### Test: Agent uses Haiku model

- **Maps to:** Design "Model Tier Assignment" → Agent 34 Tier 3
- **Type:** unit
- **Given:** Model string `"claude-3-5-haiku-20241022"`
- **When:** `create_pipeline_completeness_agent(model, str(tmp_path))` is called
- **Then:** `agent.llm.model.lower()` contains `"haiku"`
- **File:** `tests/test_pipeline_completeness_agent.py`

#### Test: Agent includes `PipelineStageTracker` tool

- **Maps to:** Requirement "Agent 34 – Pipeline Completeness" → Acceptance Criteria (tools)
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_pipeline_completeness_agent(model, str(tmp_path))` is called
- **Then:** Tool set includes `PipelineStageTracker`
- **File:** `tests/test_pipeline_completeness_agent.py`

---

### Agent 35 – Breakage Correlation Agent

#### Test: Factory returns a `crewai.Agent`

- **Maps to:** Requirement "Agent 35 – Breakage Correlation" → Acceptance Criteria
- **Type:** unit
- **Given:** `ANTHROPIC_API_KEY` set to `"test-key"`, valid `output_dir`
- **When:** `create_breakage_correlation_agent("claude-3-5-sonnet-20241022", str(tmp_path))` is called
- **Then:** Return value is an instance of `crewai.Agent`
- **File:** `tests/test_breakage_correlation_agent.py`

#### Test: Agent role contains "breakage" keyword

- **Maps to:** Requirement "Agent 35 – Breakage Correlation" → Acceptance Criteria
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_breakage_correlation_agent(model, str(tmp_path))` is called
- **Then:** `agent.role.lower()` contains `"breakage"`
- **File:** `tests/test_breakage_correlation_agent.py`

#### Test: Agent uses Sonnet model

- **Maps to:** Design "Model Tier Assignment" → Agent 35 Tier 2
- **Type:** unit
- **Given:** Model string `"claude-3-5-sonnet-20241022"`
- **When:** `create_breakage_correlation_agent(model, str(tmp_path))` is called
- **Then:** `agent.llm.model.lower()` contains `"sonnet"`
- **File:** `tests/test_breakage_correlation_agent.py`

#### Test: Agent includes `DependencyChainWalker` tool

- **Maps to:** Requirement "Agent 35 – Breakage Correlation" → Acceptance Criteria (tools)
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_breakage_correlation_agent(model, str(tmp_path))` is called
- **Then:** Tool set includes `DependencyChainWalker`
- **File:** `tests/test_breakage_correlation_agent.py`

---

### Tool: `ASTImportScanner`

#### Test: Scan returns empty result for empty directory

- **Maps to:** Requirement "Agent 31 – Usage Tracking" → Scenario "No TSX files present"
- **Type:** unit
- **Given:** `src/` does not exist under `tmp_path`
- **When:** `ASTImportScanner().run(str(tmp_path))` (or equivalent `_run` call) is invoked
- **Then:** Result is a dict with empty `imports` list; no exception raised
- **File:** `tests/test_ast_import_scanner.py`

#### Test: Scan detects import in TSX file

- **Maps to:** Requirement "Agent 31 – Usage Tracking" → Scenario "All tokens used"
- **Type:** unit
- **Given:** `tmp_path/src/Button.tsx` contains `import { Box } from "../primitives/Box"`
- **When:** Scanner runs against `tmp_path`
- **Then:** Result imports list contains `{"from": "Button", "imports": ["Box"]}`
- **File:** `tests/test_ast_import_scanner.py`

---

### Tool: `TokenUsageMapper`

#### Test: Detects dead token (defined but not used)

- **Maps to:** Requirement "Agent 31 – Usage Tracking" → Scenario "Dead token detected"
- **Type:** unit
- **Given:** `tokens/semantic.tokens.json` defines key `color-background-subtle`; no TSX file references `var(--color-background-subtle)`
- **When:** `TokenUsageMapper` runs
- **Then:** `dead_tokens` list in result contains `"color-background-subtle"`
- **File:** `tests/test_token_usage_mapper.py`

#### Test: No dead tokens when all tokens referenced

- **Maps to:** Requirement "Agent 31 – Usage Tracking" → Scenario "All tokens used"
- **Type:** unit
- **Given:** All token keys defined in `tokens/` are referenced in at least one TSX file
- **When:** `TokenUsageMapper` runs
- **Then:** `dead_tokens` is empty
- **File:** `tests/test_token_usage_mapper.py`

---

### Tool: `StructuralComparator`

#### Test: Detects prop in spec+code missing from docs

- **Maps to:** Requirement "Agent 33 – Drift Detection" → Scenario "Prop in spec+code, missing from docs"
- **Type:** unit
- **Given:** Spec YAML has prop `disabled`; TSX has `disabled?: boolean`; Markdown has no mention of `disabled`
- **When:** `StructuralComparator` compares the three sources
- **Then:** Result contains drift item `{prop: "disabled", in_spec: true, in_code: true, in_docs: false}`
- **File:** `tests/test_structural_comparator.py`

#### Test: Detects prop in spec missing from code

- **Maps to:** Requirement "Agent 33 – Drift Detection" → Scenario "Prop in spec, missing from code"
- **Type:** unit
- **Given:** Spec YAML has prop `loading`; TSX does not export `loading`; Markdown mentions `loading`
- **When:** `StructuralComparator` compares the three sources
- **Then:** Result contains drift item `{prop: "loading", in_spec: true, in_code: false, in_docs: true}`
- **File:** `tests/test_structural_comparator.py`

#### Test: No drift for consistent component

- **Maps to:** Requirement "Agent 33 – Drift Detection" → Scenario "Consistent component"
- **Type:** unit
- **Given:** Spec, TSX, and Markdown all describe the same set of props
- **When:** `StructuralComparator` compares the three sources
- **Then:** Result drift list is empty for that component
- **File:** `tests/test_structural_comparator.py`

---

### Tool: `PipelineStageTracker`

#### Test: Fully complete component has score 1.0

- **Maps to:** Requirement "Agent 34 – Pipeline Completeness" → Scenario "Fully complete component"
- **Type:** unit
- **Given:** `Button.spec.yaml`, `src/components/Button.tsx`, `tests/Button.test.tsx`, `docs/components/button.md`, and successful a11y marker all exist under `tmp_path`
- **When:** `PipelineStageTracker` checks `Button`
- **Then:** `completeness_score == 1.0` and `stuck_at is None`
- **File:** `tests/test_pipeline_stage_tracker.py`

#### Test: Component stuck at code_generated stage

- **Maps to:** Requirement "Agent 34 – Pipeline Completeness" → Scenario "Component stuck at code generation"
- **Type:** unit
- **Given:** `DatePicker.spec.yaml` exists but `src/components/DatePicker.tsx` does not
- **When:** `PipelineStageTracker` checks `DatePicker`
- **Then:** `stuck_at == "code_generated"` and `completeness_score < 1.0`
- **File:** `tests/test_pipeline_stage_tracker.py`

---

### Tool: `DependencyChainWalker`

#### Test: Root-cause failure has no upstream failing deps

- **Maps to:** Requirement "Agent 35 – Breakage Correlation" → Scenario "Root-cause failure"
- **Type:** unit
- **Given:** `dependency_graph.json` has `Button` with no dependencies; `Button` is in the failures set
- **When:** `DependencyChainWalker` processes the failures
- **Then:** `Button` entry has `classification: "root-cause"` and `dependency_chain: ["Button"]`
- **File:** `tests/test_dependency_chain_walker.py`

#### Test: Downstream failure has failing dep in chain

- **Maps to:** Requirement "Agent 35 – Breakage Correlation" → Scenario "Downstream failure"
- **Type:** unit
- **Given:** `dependency_graph.json` has `Card` → depends on `Button`; both `Button` and `Card` are in the failures set
- **When:** `DependencyChainWalker` processes the failures
- **Then:** `Card` entry has `classification: "downstream"`, `dependency_chain` includes `Button`, and `root_cause_component == "Button"`
- **File:** `tests/test_dependency_chain_walker.py`

#### Test: No failures produces empty result

- **Maps to:** Requirement "Agent 35 – Breakage Correlation" → Scenario "No failures present"
- **Type:** unit
- **Given:** Empty failures set
- **When:** `DependencyChainWalker` processes the failures
- **Then:** Result `failures` list is empty; no exception raised
- **File:** `tests/test_dependency_chain_walker.py`

---

## Edge Case Tests

#### Test: `ASTImportScanner` handles malformed TSX without raising

- **Maps to:** Requirement "Agent 31 – Usage Tracking" → error robustness
- **Type:** unit
- **Given:** A TSX file with invalid syntax (e.g. unclosed JSX tag)
- **When:** `ASTImportScanner` runs against `tmp_path`
- **Then:** The malformed file is skipped; no `SyntaxError`/`ParseError` propagates; other files are still scanned
- **File:** `tests/test_ast_import_scanner.py`

#### Test: `StructuralComparator` handles missing Markdown file gracefully

- **Maps to:** Requirement "Agent 33 – Drift Detection" → error robustness
- **Type:** unit
- **Given:** Spec and TSX exist for `ProgressBar` but no Markdown doc file
- **When:** `StructuralComparator` compares sources for `ProgressBar`
- **Then:** All props are reported as `in_docs: false`; no `FileNotFoundError`
- **File:** `tests/test_structural_comparator.py`

#### Test: `DependencyChainWalker` handles missing `dependency_graph.json`

- **Maps to:** Requirement "Agent 35 – Breakage Correlation" → error robustness
- **Type:** unit
- **Given:** `dependency_graph.json` does not exist under `output_dir`
- **When:** `DependencyChainWalker` runs
- **Then:** All failures are classified as `root-cause` (no dependency info); no exception raised
- **File:** `tests/test_dependency_chain_walker.py`

#### Test: `TokenUsageMapper` handles missing `tokens/` directory

- **Maps to:** Requirement "Agent 31 – Usage Tracking" → error robustness
- **Type:** unit
- **Given:** `tokens/` directory does not exist
- **When:** `TokenUsageMapper` runs
- **Then:** Result is empty; no `FileNotFoundError`
- **File:** `tests/test_token_usage_mapper.py`

#### Test: Crew stub compatibility — `test_crew_stubs.py` still passes

- **Maps to:** Regression — Analytics Crew I/O contract (§3.6)
- **Type:** integration
- **Given:** The real crew factory is now in place
- **When:** `test_all_crew_stubs_write_minimum_outputs` runs for `analytics`
- **Then:** The test is updated to reflect the real crew (or the analytics row is removed to a dedicated test, analogous to how the governance stub test was removed)
- **File:** `tests/test_crew_stubs.py` (modified — remove analytics from parametrize list)

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Line coverage | ≥ 80% | PRD quality gate requirement |
| Branch coverage | ≥ 70% | Covers pre-flight guard + empty/non-empty conditional paths |
| New agent factory modules | 100% reachable paths | Constructor-level tests cover all factory branches |
| New tool modules | ≥ 80% | Happy path + one edge case per public method |

---

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_analytics_crew.py` | modified | Replace stub assertions; add pre-flight guard test + crew structure assertions |
| `tests/test_usage_tracking_agent.py` | new | Agent 31 factory tests (role, model, tools) |
| `tests/test_token_compliance_agent.py` | new | Agent 32 factory tests (role, model, tools) |
| `tests/test_drift_detection_agent.py` | new | Agent 33 factory tests (role, model, tools) |
| `tests/test_pipeline_completeness_agent.py` | new | Agent 34 factory tests (role, model, tools) |
| `tests/test_breakage_correlation_agent.py` | new | Agent 35 factory tests (role, model, tools) |
| `tests/test_ast_import_scanner.py` | new | `ASTImportScanner` tool: empty dir, TSX import detection, malformed file |
| `tests/test_token_usage_mapper.py` | new | `TokenUsageMapper` tool: dead tokens, all-used, missing tokens dir |
| `tests/test_structural_comparator.py` | new | `StructuralComparator` tool: drift variants, consistent component, missing doc |
| `tests/test_pipeline_stage_tracker.py` | new | `PipelineStageTracker` tool: complete, stuck at stage, empty component list |
| `tests/test_dependency_chain_walker.py` | new | `DependencyChainWalker` tool: root-cause, downstream, no failures, missing graph |
| `tests/test_crew_stubs.py` | modified | Remove analytics row from parametrize list (graduated to real crew) |
