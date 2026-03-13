# TDD Plan: p14-governance-crew

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

All tests use **pytest** with fixture-based isolation. No live LLM calls — all agent tests mock the CrewAI `Agent` constructor and verify the agent's configuration (role, goal, tools, model). Tool tests are pure unit tests with no external dependencies.

**Frameworks:** pytest, `unittest.mock`, `pathlib`, `json`

**Approach:**
- **Agent tests**: Verify `role`, `goal`, `backstory` strings, `tools` list types, and `llm` model name — not execution behavior.
- **Tool tests**: Call tool functions/`_run` methods directly with synthetic inputs; assert output schema and edge cases.
- **Crew integration test**: Call `create_governance_crew(tmp_path)` and verify it raises `RuntimeError` when pre-flight fails; verify it returns a `Crew` (or equivalent) when pre-flight passes.
- **No e2e tests** in this change — end-to-end pipeline tests are handled at the orchestrator level.

## Test Cases

### Agent 26: Ownership Agent

#### Test: ownership agent has correct role and tools

- **Maps to:** specs/ownership-domain-classification.md → Requirement "Domain classifier assigns every component to exactly one domain"
- **Type:** unit
- **Given:** `create_ownership_agent(model, output_dir)` is called with a mock model
- **When:** the returned agent's properties are inspected
- **Then:** `agent.role` contains `"ownership"` (case-insensitive), `agent.tools` contains instances of `DomainClassifier`, `RelationshipAnalyzer`, `OrphanScanner`
- **File:** `tests/test_ownership_agent.py`

#### Test: ownership agent assigned Sonnet model tier

- **Maps to:** design.md → Model Tier Assignment (Agent 26: Tier-2 Sonnet)
- **Type:** unit
- **Given:** `create_ownership_agent(model, output_dir)` is called with a Sonnet model string
- **When:** the returned agent's `llm` is inspected
- **Then:** the model name includes `"sonnet"` (case-insensitive)
- **File:** `tests/test_ownership_agent.py`

---

### Agent 27: Workflow Agent

#### Test: workflow agent has correct role and tools

- **Maps to:** specs/workflow-deprecation-policy.md → Requirement "workflow.json encodes two state machines"
- **Type:** unit
- **Given:** `create_workflow_agent(model, output_dir)` is called
- **When:** the returned agent's properties are inspected
- **Then:** `agent.tools` contains instances of `WorkflowStateMachine`, `GateMapper`
- **File:** `tests/test_workflow_agent.py`

#### Test: workflow agent assigned Haiku model tier

- **Maps to:** design.md → Model Tier Assignment (Agent 27: Tier-3 Haiku)
- **Type:** unit
- **Given:** `create_workflow_agent(model, output_dir)` is called with a Haiku model string
- **When:** the returned agent's `llm` is inspected
- **Then:** the model name includes `"haiku"` (case-insensitive)
- **File:** `tests/test_workflow_agent.py`

---

### Agent 28: Deprecation Agent

#### Test: deprecation agent has correct role and tools

- **Maps to:** specs/workflow-deprecation-policy.md → Requirement "deprecation-policy.json is generated from pipeline-config lifecycle section"
- **Type:** unit
- **Given:** `create_deprecation_agent(model, output_dir)` is called
- **When:** the returned agent's properties are inspected
- **Then:** `agent.tools` contains instances of `LifecycleTagger`, `DeprecationPolicyGenerator`, `StabilityClassifier`, `DeprecationTagger`
- **File:** `tests/test_deprecation_agent.py`

---

### Agent 29: RFC Agent

#### Test: rfc agent has correct role and tools

- **Maps to:** specs/rfc-quality-gates.md → Requirement "RFC template and process definition are generated from workflow structure"
- **Type:** unit
- **Given:** `create_rfc_agent(model, output_dir)` is called
- **When:** the returned agent's properties are inspected
- **Then:** `agent.tools` contains instances of `RFCTemplateGenerator`, `ProcessDefinitionBuilder`
- **File:** `tests/test_rfc_agent.py`

---

### Agent 30: Quality Gate Agent

#### Test: quality gate agent has correct role and tools

- **Maps to:** specs/rfc-quality-gates.md → Requirement "Quality Gate Agent evaluates five independent gates per component"
- **Type:** unit
- **Given:** `create_quality_gate_agent(model, output_dir)` is called
- **When:** the returned agent's properties are inspected
- **Then:** `agent.tools` contains instances of `GateEvaluator`, `ThresholdGate`, `ReportWriter`, `TestSuiteGenerator`
- **File:** `tests/test_quality_gate_agent.py`

---

### Tool: domain_classifier

#### Test: component classified into correct domain by keyword match

- **Maps to:** specs/ownership-domain-classification.md → Scenario "Standard component classification"
- **Type:** unit
- **Given:** `domains = {"forms": ["input", "button", "select"], "navigation": ["breadcrumb", "nav"]}` and components `["Button", "Breadcrumb"]`
- **When:** `domain_classifier.classify(components, domains)` is called
- **Then:** returns `{"Button": "forms", "Breadcrumb": "navigation"}`
- **File:** `tests/test_domain_classifier.py`

#### Test: multi-domain component assigned to highest score domain

- **Maps to:** specs/ownership-domain-classification.md → Scenario "Multi-domain ambiguity resolved by score"
- **Type:** unit
- **Given:** `DataGrid` matches `data-display` (score: 3) and `forms` (score: 1)
- **When:** `domain_classifier.classify(["DataGrid"], domains)` is called
- **Then:** returns `{"DataGrid": "data-display"}`
- **File:** `tests/test_domain_classifier.py`

#### Test: unmatched component classified as orphan

- **Maps to:** specs/ownership-domain-classification.md → Scenario "Orphan detection"
- **Type:** unit
- **Given:** `MegaMenu` matches no domain keywords
- **When:** `domain_classifier.classify(["MegaMenu"], domains)` is called
- **Then:** returns `{"MegaMenu": "__orphan__"}`
- **File:** `tests/test_domain_classifier.py`

---

### Tool: relationship_analyzer

#### Test: cross-domain dependency detected from component index

- **Maps to:** specs/ownership-domain-classification.md → Scenario "Cross-domain dependency detected"
- **Type:** unit
- **Given:** a temp `component-index.json` with `Select` depending on `Popover`; `Select` in `forms`, `Popover` in `layout`
- **When:** `relationship_analyzer.analyze(index_path, domain_map)` is called
- **Then:** result contains `{"component": "Select", "depends_on": "Popover", "component_domain": "forms", "dependency_domain": "layout"}`
- **File:** `tests/test_relationship_analyzer.py`

#### Test: missing component-index.json returns empty list

- **Maps to:** specs/ownership-domain-classification.md → Scenario "Missing component-index.json fallback"
- **Type:** unit
- **Given:** `component-index.json` does not exist
- **When:** `relationship_analyzer.analyze(missing_path, {})` is called
- **Then:** returns `[]` without raising
- **File:** `tests/test_relationship_analyzer.py`

---

### Tool: workflow_state_machine

#### Test: token change pipeline contains gate check state

- **Maps to:** specs/workflow-deprecation-policy.md → Scenario "Token change pipeline with gate checkpoint"
- **Type:** unit
- **Given:** `quality_gates = {"minCompositeScore": 70, "a11yLevel": "AA"}`
- **When:** `workflow_state_machine.generate(quality_gates)` is called
- **Then:** returned dict contains `"token_change_pipeline"` and `"component_change_pipeline"` keys; at least one state has `"gate_check"` not null
- **File:** `tests/test_workflow_state_machine.py`

#### Test: empty quality gates produces workflow with null gate checks

- **Maps to:** specs/workflow-deprecation-policy.md → Scenario "Empty quality gates config"
- **Type:** unit
- **Given:** `quality_gates = {}`
- **When:** `workflow_state_machine.generate({})` is called
- **Then:** result is valid JSON-serializable dict; all `gate_check` fields are `null`
- **File:** `tests/test_workflow_state_machine.py`

---

### Tool: gate_mapper

#### Test: gate IDs are mapped to workflow transitions

- **Maps to:** specs/workflow-deprecation-policy.md → Requirement "workflow.json encodes two state machines"
- **Type:** unit
- **Given:** a workflow dict with gate transitions and `gates = ["coverage_80", "a11y_zero_critical"]`
- **When:** `gate_mapper.map_gates(workflow, gates)` is called
- **Then:** output dict maps each gate ID to one or more workflow state names
- **File:** `tests/test_gate_mapper.py`

---

### Tool: stability_classifier

#### Test: beta classification for coverage below threshold

- **Maps to:** specs/workflow-deprecation-policy.md → Scenario "Beta classification for coverage below threshold"
- **Type:** unit
- **Given:** component `Button` with composite `75.0`, coverage `0.72`
- **When:** `stability_classifier.classify(components, scorecard, config)` is called
- **Then:** `Button` is classified as `"beta"`
- **File:** `tests/test_stability_classifier.py`

#### Test: explicit experimental tag takes precedence

- **Maps to:** specs/workflow-deprecation-policy.md → Scenario "Explicit experimental tag takes precedence"
- **Type:** unit
- **Given:** `DataGrid` with composite `82.0`, coverage `0.85`, but `experimental` tag in component index
- **When:** classifier processes `DataGrid`
- **Then:** result is `"experimental"`
- **File:** `tests/test_stability_classifier.py`

---

### Tool: deprecation_policy_generator

#### Test: grace period defaults to 90 when not specified

- **Maps to:** specs/workflow-deprecation-policy.md → Scenario "Default grace period applied"
- **Type:** unit
- **Given:** `lifecycle_config = {}` (no gracePeriodDays)
- **When:** `deprecation_policy_generator.generate(lifecycle_config, component_statuses)` is called
- **Then:** result contains `"grace_period_days": 90`
- **File:** `tests/test_deprecation_policy_generator.py`

#### Test: migration guide required when defaultStatus is stable

- **Maps to:** specs/workflow-deprecation-policy.md → Scenario "Standard deprecation policy generation"
- **Type:** unit
- **Given:** `lifecycle_config = {"defaultStatus": "stable", "gracePeriodDays": 60}`
- **When:** generator runs
- **Then:** result contains `"grace_period_days": 60` and `"migration_guide_required": True`
- **File:** `tests/test_deprecation_policy_generator.py`

---

### Tool: lifecycle_tagger

#### Test: lifecycle tagger tags a component with experimental status

- **Maps to:** specs/workflow-deprecation-policy.md → Requirement "stability_classifier assigns lifecycle status per component"
- **Type:** unit
- **Given:** a component dict and status `"experimental"`
- **When:** `LifecycleTagger._run(component=..., status="experimental")` is called
- **Then:** returned dict contains `"lifecycle_status": "experimental"`
- **File:** `tests/test_lifecycle_tagger.py`

---

### Tool: rfc_template_generator

#### Test: generated template contains required sections

- **Maps to:** specs/rfc-quality-gates.md → Scenario "RFC process generation"
- **Type:** unit
- **Given:** `process_config = {"rfc_required_for": ["new_primitive", "breaking_token_change"]}`
- **When:** `RFCTemplateGenerator._run(process_config=...)` is called
- **Then:** output string contains `"## Detailed Design"`, `"## Motivation"`, `"## Summary"`
- **File:** `tests/test_rfc_template_generator.py`

#### Test: template generation is idempotent

- **Maps to:** specs/rfc-quality-gates.md → Scenario "Template is idempotent"
- **Type:** unit
- **Given:** identical `process_config` input on two calls
- **When:** `RFCTemplateGenerator._run(...)` is called twice
- **Then:** both outputs are equal
- **File:** `tests/test_rfc_template_generator.py`

---

### Tool: process_definition_builder

#### Test: process definition always includes new_primitive and breaking_token_change

- **Maps to:** specs/rfc-quality-gates.md → Acceptance Criteria for RFC process
- **Type:** unit
- **Given:** minimal `workflow_config` input
- **When:** `ProcessDefinitionBuilder._run(workflow_config=...)` is called
- **Then:** result's `"rfc_required_for"` list contains `"new_primitive"` and `"breaking_token_change"`
- **File:** `tests/test_process_definition_builder.py`

---

### Tool: gate_evaluator

#### Test: component passing all gates returns all true

- **Maps to:** specs/rfc-quality-gates.md → Scenario "Component passes all gates"
- **Type:** unit
- **Given:** `Button` with coverage `0.85`, zero a11y critical violations, no phantom refs, present in docs, has usage example
- **When:** `GateEvaluator._run(component="Button", ...)` is called
- **Then:** all five gate keys are `True`
- **File:** `tests/test_gate_evaluator.py`

#### Test: coverage gate fails independently when below 80%

- **Maps to:** specs/rfc-quality-gates.md → Scenario "Coverage gate fails independently"
- **Type:** unit
- **Given:** `Navigation` with coverage `0.75` (below 0.80); other gates passing
- **When:** `GateEvaluator._run(component="Navigation", ...)` is called
- **Then:** `coverage_80` is `False`; other gates may still be `True`
- **File:** `tests/test_gate_evaluator.py`

#### Test: missing a11y audit file returns False gate, not exception

- **Maps to:** specs/rfc-quality-gates.md → Scenario "Missing a11y-audit.json"
- **Type:** unit
- **Given:** `a11y_audit` data is `None` (file not found)
- **When:** `GateEvaluator._run(component="Card", a11y_audit=None, ...)` is called
- **Then:** `a11y_zero_critical` is `False` and no exception is raised
- **File:** `tests/test_gate_evaluator.py`

---

### Tool: test_suite_generator

#### Test: generated tokens.test.ts contains describe block

- **Maps to:** specs/rfc-quality-gates.md → Scenario "Test suite generated for Starter tier"
- **Type:** unit
- **Given:** component list `["Button", "Input"]` and token paths `["global.color"]`
- **When:** `TestSuiteGenerator._run(suite="tokens", components=[...], token_paths=[...])` is called
- **Then:** output string contains `"describe("`, a valid `import` statement, and `"test("` or `"it("`
- **File:** `tests/test_test_suite_generator.py`

#### Test: kebab-case component names sanitized to camelCase identifiers

- **Maps to:** specs/rfc-quality-gates.md → Scenario "Component name with hyphen sanitized"
- **Type:** unit
- **Given:** component list includes `"date-picker"`
- **When:** generator processes the list
- **Then:** the output TypeScript uses `"datePicker"` as an identifier and `"date-picker"` as the describe string
- **File:** `tests/test_test_suite_generator.py`

---

### Tool: report_writer

#### Test: report writer serializes gate results to JSON file

- **Maps to:** design.md → Architecture Decision "governance/quality-gates.json records per-gate, per-component results"
- **Type:** unit
- **Given:** gate results dict for two components, a tmp output path
- **When:** `ReportWriter._run(results=..., output_path=...)` is called
- **Then:** a file is written at the output path; `json.loads(file.read_text())` succeeds and contains expected component names
- **File:** `tests/test_report_writer.py`

---

### Crew: Governance Crew pre-flight guard

#### Test: crew raises RuntimeError when component-index.json is absent

- **Maps to:** specs/rfc-quality-gates.md → Scenario "Pre-flight blocks on missing file"
- **Type:** integration
- **Given:** `tmp_path` with no `docs/component-index.json` file
- **When:** `create_governance_crew(str(tmp_path))` is called
- **Then:** `RuntimeError` is raised with message containing `"Documentation Crew output not found"`
- **File:** `tests/test_governance_crew.py`

#### Test: crew instantiates successfully when component-index.json is present

- **Maps to:** specs/rfc-quality-gates.md → Acceptance Criteria for pre-flight guard
- **Type:** integration
- **Given:** `tmp_path` with `docs/component-index.json` containing `{"Button": {}}` and all required report stubs
- **When:** `create_governance_crew(str(tmp_path))` is called
- **Then:** a non-None Crew-like object is returned without error
- **File:** `tests/test_governance_crew.py`

## Edge Case Tests

#### Test: domain_classifier handles empty component list

- **Maps to:** specs/ownership-domain-classification.md → Requirement "Domain classifier assigns every component to exactly one domain"
- **Type:** unit
- **Given:** empty component list `[]`
- **When:** `domain_classifier.classify([], domains)` is called
- **Then:** returns `{}` without error
- **File:** `tests/test_domain_classifier.py`

#### Test: workflow_state_machine output is JSON-serializable

- **Maps to:** specs/workflow-deprecation-policy.md → Acceptance Criteria "workflow_state_machine.py returns a dict passing json.dumps without error"
- **Type:** unit
- **Given:** any valid quality_gates dict
- **When:** `json.dumps(workflow_state_machine.generate(quality_gates))` is called
- **Then:** no `TypeError` is raised
- **File:** `tests/test_workflow_state_machine.py`

#### Test: test_suite_generator handles empty component list

- **Maps to:** specs/rfc-quality-gates.md → Requirement "Test suite generator produces four valid TypeScript test files"
- **Type:** unit
- **Given:** empty component list and empty token paths
- **When:** each of the four suite types is generated
- **Then:** output is a non-empty string containing valid TypeScript structure without component-specific describe blocks
- **File:** `tests/test_test_suite_generator.py`

#### Test: gate_evaluator returns all False when quality-scorecard.json is absent

- **Maps to:** specs/rfc-quality-gates.md → Acceptance Criteria "gate_evaluator.py returns all gates as false if a required data file is missing"
- **Type:** unit
- **Given:** `scorecard = None`
- **When:** `GateEvaluator._run(component="Modal", scorecard=None, ...)` is called
- **Then:** all five gate values are `False`; no exception
- **File:** `tests/test_gate_evaluator.py`

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Line coverage | ≥80% | PRD quality gate requirement (§8) |
| Branch coverage | ≥70% | Covers conditional classification logic paths |
| A11y rules passing | 100% critical | Zero critical a11y violations |

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_ownership_agent.py` | new | Agent 26 configuration tests |
| `tests/test_workflow_agent.py` | new | Agent 27 configuration tests |
| `tests/test_deprecation_agent.py` | new | Agent 28 configuration tests (agent-level; tool coverage in separate file) |
| `tests/test_rfc_agent.py` | new | Agent 29 configuration tests |
| `tests/test_quality_gate_agent.py` | new | Agent 30 configuration tests |
| `tests/test_domain_classifier.py` | new | domain_classifier tool: classification, scoring, orphan detection |
| `tests/test_relationship_analyzer.py` | new | relationship_analyzer tool: cross-domain detection, fallback |
| `tests/test_workflow_state_machine.py` | new | workflow_state_machine tool: state machine generation |
| `tests/test_gate_mapper.py` | new | gate_mapper tool: gate-to-transition mapping |
| `tests/test_stability_classifier.py` | new | stability_classifier tool: stable/beta/experimental rules |
| `tests/test_lifecycle_tagger.py` | new | lifecycle_tagger tool: BaseTool metadata injection |
| `tests/test_deprecation_policy_generator.py` | new | deprecation_policy_generator tool: template expansion |
| `tests/test_rfc_template_generator.py` | new | rfc_template_generator tool: Markdown output validation |
| `tests/test_process_definition_builder.py` | new | process_definition_builder tool: JSON process definition |
| `tests/test_gate_evaluator.py` | new | gate_evaluator tool: per-component per-gate evaluation |
| `tests/test_report_writer.py` | new | report_writer tool: file output and JSON serialization |
| `tests/test_test_suite_generator.py` | new | test_suite_generator tool: TypeScript template generation |
| `tests/test_governance_crew.py` | new | Crew factory pre-flight guard integration tests |
