# TDD Plan: p16-ai-semantic-layer-crew

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

All tests are **unit tests** written in Python using `pytest`. LLM calls are avoided in unit tests — `crewai.Agent` is instantiated using a test API key (`ANTHROPIC_API_KEY=test-key`), and no `.kickoff()` is called at the unit level. Integration-level crew tests verify constructor behaviour and pre-flight guards only (matching the pattern established by `test_analytics_crew.py`).

Framework: `pytest` + `tmp_path` fixture for isolated file-system state.

Coverage target per new module: ≥ 80% line coverage, ≥ 70% branch coverage.

---

## Test Cases

### AI Semantic Layer Crew Factory

#### Test: Factory returns `crewai.Crew` when specs exist

- **Maps to:** Requirement "AI Semantic Layer Crew factory replaces stub" → Scenario "Factory returns a real crew"
- **Type:** integration
- **Given:** `tmp_path/specs/button.spec.yaml` exists with minimal YAML content
- **When:** `create_ai_semantic_layer_crew(str(tmp_path))` is called
- **Then:** Return value is an instance of `crewai.Crew` (not `StubCrew`)
- **File:** `tests/test_ai_semantic_layer_crew.py`

#### Test: Factory raises `RuntimeError` when no spec files exist

- **Maps to:** Requirement "AI Semantic Layer Crew factory replaces stub" → Scenario "Pre-flight guard fires with missing specs"
- **Type:** integration
- **Given:** `tmp_path` has no `specs/` directory
- **When:** `create_ai_semantic_layer_crew(str(tmp_path))` is called
- **Then:** `RuntimeError` is raised
- AND error message mentions `specs`
- **File:** `tests/test_ai_semantic_layer_crew.py`

#### Test: Factory raises `RuntimeError` when `specs/` exists but is empty

- **Maps to:** Requirement "AI Semantic Layer Crew factory replaces stub" → Scenario "Pre-flight guard fires with missing specs"
- **Type:** integration
- **Given:** `tmp_path/specs/` directory exists but contains no `.spec.yaml` files
- **When:** `create_ai_semantic_layer_crew(str(tmp_path))` is called
- **Then:** `RuntimeError` is raised
- **File:** `tests/test_ai_semantic_layer_crew.py`

#### Test: Crew has exactly 5 agents and 5 tasks

- **Maps to:** Requirement "AI Semantic Layer Crew factory replaces stub" → Acceptance Criteria
- **Type:** integration
- **Given:** Valid `specs/` directory with one spec file
- **When:** `create_ai_semantic_layer_crew(str(tmp_path))` is called
- **Then:** `crew.agents` has length 5
- AND `crew.tasks` has length 5
- **File:** `tests/test_ai_semantic_layer_crew.py`

---

### Agent 41 – Registry Maintenance Agent

#### Test: Factory returns a `crewai.Agent`

- **Maps to:** Requirement "Agent 41 – Registry Maintenance" → Acceptance Criteria
- **Type:** unit
- **Given:** `ANTHROPIC_API_KEY` set to `"test-key"`, valid `output_dir`
- **When:** `create_registry_maintenance_agent("claude-3-5-haiku-20241022", str(tmp_path))` is called
- **Then:** Return value is an instance of `crewai.Agent`
- **File:** `tests/test_registry_maintenance_agent.py`

#### Test: Agent role contains "registry" keyword

- **Maps to:** Requirement "Agent 41 – Registry Maintenance" → Acceptance Criteria
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_registry_maintenance_agent(model, str(tmp_path))` is called
- **Then:** `agent.role.lower()` contains `"registry"`
- **File:** `tests/test_registry_maintenance_agent.py`

#### Test: Agent uses Haiku model

- **Maps to:** Design "Model Tier Assignment" → Agent 41 Tier 3
- **Type:** unit
- **Given:** Model string `"claude-3-5-haiku-20241022"`
- **When:** `create_registry_maintenance_agent(model, str(tmp_path))` is called
- **Then:** `agent.llm.model.lower()` contains `"haiku"`
- **File:** `tests/test_registry_maintenance_agent.py`

#### Test: Agent includes required tools

- **Maps to:** Requirement "Agent 41 – Registry Maintenance" → Acceptance Criteria (tools)
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_registry_maintenance_agent(model, str(tmp_path))` is called
- **Then:** Tool set includes `SpecIndexer`, `ExampleCodeGenerator`, `RegistryBuilder`
- **File:** `tests/test_registry_maintenance_agent.py`

---

### Agent 42 – Token Resolution Agent

#### Test: Factory returns a `crewai.Agent`

- **Maps to:** Requirement "Agent 42 – Token Resolution" → Acceptance Criteria
- **Type:** unit
- **Given:** `ANTHROPIC_API_KEY` set to `"test-key"`, valid `output_dir`
- **When:** `create_token_resolution_agent("claude-3-5-haiku-20241022", str(tmp_path))` is called
- **Then:** Return value is an instance of `crewai.Agent`
- **File:** `tests/test_token_resolution_agent.py`

#### Test: Agent role contains "token" keyword

- **Maps to:** Requirement "Agent 42 – Token Resolution" → Acceptance Criteria
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_token_resolution_agent(model, str(tmp_path))` is called
- **Then:** `agent.role.lower()` contains `"token"`
- **File:** `tests/test_token_resolution_agent.py`

#### Test: Agent uses Haiku model

- **Maps to:** Design "Model Tier Assignment" → Agent 42 Tier 3
- **Type:** unit
- **Given:** Model string `"claude-3-5-haiku-20241022"`
- **When:** `create_token_resolution_agent(model, str(tmp_path))` is called
- **Then:** `agent.llm.model.lower()` contains `"haiku"`
- **File:** `tests/test_token_resolution_agent.py`

#### Test: Agent includes required tools

- **Maps to:** Requirement "Agent 42 – Token Resolution" → Acceptance Criteria (tools)
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_token_resolution_agent(model, str(tmp_path))` is called
- **Then:** Tool set includes `TokenGraphTraverser` and `SemanticMapper`
- **File:** `tests/test_token_resolution_agent.py`

---

### Agent 43 – Composition Constraint Agent

#### Test: Factory returns a `crewai.Agent`

- **Maps to:** Requirement "Agent 43 – Composition Constraint" → Acceptance Criteria
- **Type:** unit
- **Given:** `ANTHROPIC_API_KEY` set to `"test-key"`, valid `output_dir`
- **When:** `create_composition_constraint_agent("claude-3-5-sonnet-20241022", str(tmp_path))` is called
- **Then:** Return value is an instance of `crewai.Agent`
- **File:** `tests/test_composition_constraint_agent.py`

#### Test: Agent role contains "composition" keyword

- **Maps to:** Requirement "Agent 43 – Composition Constraint" → Acceptance Criteria
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_composition_constraint_agent(model, str(tmp_path))` is called
- **Then:** `agent.role.lower()` contains `"composition"`
- **File:** `tests/test_composition_constraint_agent.py`

#### Test: Agent uses Sonnet model

- **Maps to:** Design "Model Tier Assignment" → Agent 43 Tier 2
- **Type:** unit
- **Given:** Model string `"claude-3-5-sonnet-20241022"`
- **When:** `create_composition_constraint_agent(model, str(tmp_path))` is called
- **Then:** `agent.llm.model.lower()` contains `"sonnet"`
- **File:** `tests/test_composition_constraint_agent.py`

#### Test: Agent includes required tools

- **Maps to:** Requirement "Agent 43 – Composition Constraint" → Acceptance Criteria (tools)
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_composition_constraint_agent(model, str(tmp_path))` is called
- **Then:** Tool set includes `CompositionRuleExtractor` and `TreeValidator`
- **File:** `tests/test_composition_constraint_agent.py`

---

### Agent 44 – Validation Rule Agent

#### Test: Factory returns a `crewai.Agent`

- **Maps to:** Requirement "Agent 44 – Validation Rule" → Acceptance Criteria
- **Type:** unit
- **Given:** `ANTHROPIC_API_KEY` set to `"test-key"`, valid `output_dir`
- **When:** `create_validation_rule_agent("claude-3-5-haiku-20241022", str(tmp_path))` is called
- **Then:** Return value is an instance of `crewai.Agent`
- **File:** `tests/test_validation_rule_agent.py`

#### Test: Agent role contains "validation" or "rule" keyword

- **Maps to:** Requirement "Agent 44 – Validation Rule" → Acceptance Criteria
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_validation_rule_agent(model, str(tmp_path))` is called
- **Then:** `agent.role.lower()` contains `"validation"` or `"rule"`
- **File:** `tests/test_validation_rule_agent.py`

#### Test: Agent uses Haiku model

- **Maps to:** Design "Model Tier Assignment" → Agent 44 Tier 3
- **Type:** unit
- **Given:** Model string `"claude-3-5-haiku-20241022"`
- **When:** `create_validation_rule_agent(model, str(tmp_path))` is called
- **Then:** `agent.llm.model.lower()` contains `"haiku"`
- **File:** `tests/test_validation_rule_agent.py`

#### Test: Agent includes required tools

- **Maps to:** Requirement "Agent 44 – Validation Rule" → Acceptance Criteria (tools)
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_validation_rule_agent(model, str(tmp_path))` is called
- **Then:** Tool set includes `RuleCompiler`
- **File:** `tests/test_validation_rule_agent.py`

---

### Agent 45 – Context Serializer Agent

#### Test: Factory returns a `crewai.Agent`

- **Maps to:** Requirement "Agent 45 – Context Serializer" → Acceptance Criteria
- **Type:** unit
- **Given:** `ANTHROPIC_API_KEY` set to `"test-key"`, valid `output_dir`
- **When:** `create_context_serializer_agent("claude-3-5-sonnet-20241022", str(tmp_path))` is called
- **Then:** Return value is an instance of `crewai.Agent`
- **File:** `tests/test_context_serializer_agent.py`

#### Test: Agent role contains "context" or "serializer" keyword

- **Maps to:** Requirement "Agent 45 – Context Serializer" → Acceptance Criteria
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_context_serializer_agent(model, str(tmp_path))` is called
- **Then:** `agent.role.lower()` contains `"context"` or `"serializer"`
- **File:** `tests/test_context_serializer_agent.py`

#### Test: Agent uses Sonnet model

- **Maps to:** Design "Model Tier Assignment" → Agent 45 Tier 2
- **Type:** unit
- **Given:** Model string `"claude-3-5-sonnet-20241022"`
- **When:** `create_context_serializer_agent(model, str(tmp_path))` is called
- **Then:** `agent.llm.model.lower()` contains `"sonnet"`
- **File:** `tests/test_context_serializer_agent.py`

#### Test: Agent includes required tools

- **Maps to:** Requirement "Agent 45 – Context Serializer" → Acceptance Criteria (tools)
- **Type:** unit
- **Given:** Valid `output_dir`
- **When:** `create_context_serializer_agent(model, str(tmp_path))` is called
- **Then:** Tool set includes `ContextFormatter`, `TokenBudgetOptimizer`, `MultiFormatSerializer`
- **File:** `tests/test_context_serializer_agent.py`

---

### SpecIndexer Tool

#### Test: `SpecIndexer` parses props from YAML

- **Maps to:** Requirement "Agent 41 – Registry Maintenance" → Scenario "Registry built from spec and TSX sources"
- **Type:** unit
- **Given:** A YAML spec file defining a `Button` with props `variant` and `disabled`
- **When:** `SpecIndexer(output_dir).index()` is called
- **Then:** Result includes a `Button` entry with `props` containing `variant` and `disabled`
- **File:** `tests/test_spec_indexer.py`

#### Test: `SpecIndexer` returns empty list when `specs/` is absent

- **Maps to:** Requirement "Agent 41 – Registry Maintenance" → Acceptance Criteria
- **Type:** unit
- **Given:** `output_dir` has no `specs/` directory
- **When:** `SpecIndexer(output_dir).index()` is called
- **Then:** An empty list is returned without raising
- **File:** `tests/test_spec_indexer.py`

---

### ExampleCodeGenerator Tool

#### Test: `ExampleCodeGenerator` returns a non-empty JSX string for a simple spec

- **Maps to:** Requirement "Agent 41 – Registry Maintenance" → Acceptance Criteria (usageExamples)
- **Type:** unit
- **Given:** A component spec dict with `name: "Button"`, `props: [{name: "variant", type: "string"}]`
- **When:** `ExampleCodeGenerator.generate(spec)` is called
- **Then:** Returned string contains `<Button`
- **File:** `tests/test_example_code_generator.py`

---

### RegistryBuilder Tool

#### Test: `RegistryBuilder` writes valid JSON to `registry/components.json`

- **Maps to:** Requirement "Agent 41 – Registry Maintenance" → Acceptance Criteria
- **Type:** unit
- **Given:** A list of component spec dicts
- **When:** `RegistryBuilder(output_dir).build(components)` is called
- **Then:** `registry/components.json` exists and is valid JSON
- AND the JSON is not `{"stub": true}`
- **File:** `tests/test_registry_builder.py`

#### Test: `RegistryBuilder` creates `registry/` directory if absent

- **Maps to:** Requirement "AI Semantic Layer Crew factory replaces stub" → Acceptance Criteria
- **Type:** unit
- **Given:** `output_dir/registry/` does not exist
- **When:** `RegistryBuilder(output_dir).build(components)` is called
- **Then:** `registry/` is created and `components.json` is written
- **File:** `tests/test_registry_builder.py`

---

### TokenGraphTraverser Tool

#### Test: `TokenGraphTraverser` resolves a semantic token to its hex value

- **Maps to:** Requirement "Agent 42 – Token Resolution" → Scenario "Global token references semantic token"
- **Type:** unit
- **Given:** `tokens/semantic.tokens.json` contains `color.primary` with `$value: "{color.blue-500}"` and `tokens/global.tokens.json` defines `color.blue-500` as `#0070f3`
- **When:** `TokenGraphTraverser(output_dir).traverse()` is called
- **Then:** Result entry for `color-primary` has `resolvedValue` of `#0070f3`
- **File:** `tests/test_token_graph_traverser.py`

#### Test: `TokenGraphTraverser` handles empty token files without raising

- **Maps to:** Requirement "Agent 42 – Token Resolution" → Scenario "Empty token files"
- **Type:** unit
- **Given:** All `tokens/*.tokens.json` files are empty objects `{}`
- **When:** `TokenGraphTraverser(output_dir).traverse()` is called
- **Then:** Returns an empty list without raising
- **File:** `tests/test_token_graph_traverser.py`

---

### SemanticMapper Tool

#### Test: `SemanticMapper` assigns correct tier labels

- **Maps to:** Requirement "Agent 42 – Token Resolution" → Acceptance Criteria (tier)
- **Type:** unit
- **Given:** A traversal result entry from a file named `semantic.tokens.json`
- **When:** `SemanticMapper.map(traversal_result)` is called
- **Then:** Entry `tier` is `"semantic"`
- **File:** `tests/test_semantic_mapper.py`

---

### CompositionRuleExtractor Tool

#### Test: `CompositionRuleExtractor` reads from composition audit if present

- **Maps to:** Requirement "Agent 43 – Composition Constraint" → Scenario "Composition rules from audit report"
- **Type:** unit
- **Given:** `reports/composition-audit.json` contains rules for `Card` restricting children to `["Text", "Button"]`
- **When:** `CompositionRuleExtractor(output_dir).extract()` is called
- **Then:** Result entry for `Card` has `allowedChildren: ["Text", "Button"]`
- **File:** `tests/test_composition_rule_extractor.py`

#### Test: `CompositionRuleExtractor` falls back to spec YAML when audit absent

- **Maps to:** Requirement "Agent 43 – Composition Constraint" → Scenario "Fallback to spec when audit absent"
- **Type:** unit
- **Given:** `reports/composition-audit.json` is absent
- AND `specs/modal.spec.yaml` defines `slots: [header, body, footer]`
- **When:** `CompositionRuleExtractor(output_dir).extract()` is called
- **Then:** Result entry for `Modal` has `requiredSlots: ["header", "body", "footer"]`
- AND no error is raised
- **File:** `tests/test_composition_rule_extractor.py`

---

### TreeValidator Tool

#### Test: `TreeValidator` returns `valid: True` for a conforming component tree

- **Maps to:** Requirement "Agent 43 – Composition Constraint" → Scenario "Valid example passes validation"
- **Type:** unit
- **Given:** A component tree `{type: "Tabs", children: [{type: "TabPanel"}]}` and rules that allow `TabPanel` as a child of `Tabs`
- **When:** `TreeValidator.validate(tree, rules)` is called
- **Then:** Result is `{"valid": True, "violations": []}`
- **File:** `tests/test_tree_validator.py`

#### Test: `TreeValidator` returns violation for forbidden nesting

- **Maps to:** Requirement "Agent 43 – Composition Constraint" → Acceptance Criteria
- **Type:** unit
- **Given:** Rules forbidding `Card` nested inside `Card`
- AND a tree `{type: "Card", children: [{type: "Card"}]}`
- **When:** `TreeValidator.validate(tree, rules)` is called
- **Then:** Result has `valid: False` and `violations` contains an entry for the nested `Card`
- **File:** `tests/test_tree_validator.py`

---

### RuleCompiler Tool

#### Test: `RuleCompiler` writes valid JSON to `registry/compliance-rules.json`

- **Maps to:** Requirement "Agent 44 – Validation Rule" → Acceptance Criteria
- **Type:** unit
- **Given:** `registry/components.json` and `registry/tokens.json` with minimal content
- **When:** `RuleCompiler(output_dir).compile()` is called
- **Then:** `registry/compliance-rules.json` is written as valid JSON
- AND content is not `{"stub": true}`
- **File:** `tests/test_rule_compiler.py`

#### Test: `RuleCompiler` produces rules from all four required categories

- **Maps to:** Requirement "Agent 44 – Validation Rule" → Acceptance Criteria (categories)
- **Type:** unit
- **Given:** Non-empty component and token registries
- **When:** `RuleCompiler(output_dir).compile()` is called
- **Then:** The `rules` array contains at least one entry per category: `tokenUsage`, `composition`, `accessibility`, `namingConventions`
- **File:** `tests/test_rule_compiler.py`

#### Test: `RuleCompiler` handles empty registries without raising

- **Maps to:** Requirement "Agent 44 – Validation Rule" → Scenario "Empty rule sources"
- **Type:** unit
- **Given:** `registry/components.json` and `registry/tokens.json` contain empty arrays
- **When:** `RuleCompiler(output_dir).compile()` is called
- **Then:** `registry/compliance-rules.json` is written with `{"rules": []}`
- AND no error is raised
- **File:** `tests/test_rule_compiler.py`

---

### TokenBudgetOptimizer Tool

#### Test: `TokenBudgetOptimizer` does not truncate when content fits within limit

- **Maps to:** Requirement "Agent 45 – Context Serializer" → Scenario "Serialization of Starter scope design system"
- **Type:** unit
- **Given:** Registry content totalling fewer than 8000 tokens
- **When:** `TokenBudgetOptimizer.optimize(content, max_tokens=8000)` is called
- **Then:** Returned content is identical to input
- **File:** `tests/test_token_budget_optimizer.py`

#### Test: `TokenBudgetOptimizer` removes usage examples first when over budget

- **Maps to:** Requirement "Agent 45 – Context Serializer" → Scenario "Token budget overflow triggers optimisation"
- **Type:** unit
- **Given:** Registry content totalling over 8000 tokens with `usageExamples` fields
- **When:** `TokenBudgetOptimizer.optimize(content, max_tokens=8000)` is called
- **Then:** `usageExamples` fields are removed or truncated before other fields
- AND total token count of result is ≤ 8000
- **File:** `tests/test_token_budget_optimizer.py`

---

### MultiFormatSerializer Tool

#### Test: `MultiFormatSerializer` writes all three output files

- **Maps to:** Requirement "Agent 45 – Context Serializer" → Acceptance Criteria
- **Type:** unit
- **Given:** Optimized registry content and `output_dir`
- **When:** `MultiFormatSerializer(output_dir).serialize(content)` is called
- **Then:** `.cursorrules`, `copilot-instructions.md`, and `ai-context.json` are all written
- **File:** `tests/test_multi_format_serializer.py`

#### Test: `MultiFormatSerializer` writes valid JSON for `ai-context.json`

- **Maps to:** Requirement "Agent 45 – Context Serializer" → Acceptance Criteria
- **Type:** unit
- **Given:** Optimized registry content
- **When:** `MultiFormatSerializer(output_dir).serialize(content)` is called
- **Then:** `ai-context.json` parses as valid JSON and is not `{"stub": true}`
- **File:** `tests/test_multi_format_serializer.py`

#### Test: `MultiFormatSerializer` writes non-empty Markdown for `copilot-instructions.md`

- **Maps to:** Requirement "Agent 45 – Context Serializer" → Acceptance Criteria
- **Type:** unit
- **Given:** Non-empty registry content
- **When:** `MultiFormatSerializer(output_dir).serialize(content)` is called
- **Then:** `copilot-instructions.md` content length > 0
- **File:** `tests/test_multi_format_serializer.py`

---

## Edge Case Tests

#### Test: Crew creates `registry/` directory when absent

- **Maps to:** Requirement "AI Semantic Layer Crew factory replaces stub" → Acceptance Criteria
- **Type:** integration
- **Given:** `tmp_path` has no `registry/` subdirectory
- AND `specs/` with one spec file exists
- **When:** `create_ai_semantic_layer_crew(str(tmp_path))` is called
- **Then:** `registry/` directory is created within `output_dir`
- **File:** `tests/test_ai_semantic_layer_crew.py`

#### Test: `TokenGraphTraverser` handles missing `tokens/` directory

- **Maps to:** Requirement "Agent 42 – Token Resolution" → edge case
- **Type:** unit
- **Given:** `output_dir` has no `tokens/` subdirectory
- **When:** `TokenGraphTraverser(output_dir).traverse()` is called
- **Then:** Returns an empty list without raising
- **File:** `tests/test_token_graph_traverser.py`

#### Test: `RegistryBuilder` handles spec with no props

- **Maps to:** Requirement "Agent 41 – Registry Maintenance" → edge case
- **Type:** unit
- **Given:** A component spec dict with `name: "Divider"` and no `props` key
- **When:** `RegistryBuilder(output_dir).build([divider_spec])` is called
- **Then:** `registry/components.json` contains `Divider` with `props: []` and no error
- **File:** `tests/test_registry_builder.py`

#### Test: `MultiFormatSerializer` handles missing upstream registry gracefully

- **Maps to:** Requirement "Agent 45 – Context Serializer" → Scenario "Missing upstream registry file"
- **Type:** unit
- **Given:** `registry/tokens.json` does not exist
- AND other registry files exist
- **When:** `MultiFormatSerializer(output_dir).serialize(content)` is called with partial content
- **Then:** All three output files are written using available data
- AND no unhandled exception is raised
- **File:** `tests/test_multi_format_serializer.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------| 
| Line coverage | ≥80% | PRD quality gate requirement |
| Branch coverage | ≥70% | Covers conditional logic paths |
| A11y rules passing | 100% critical | Zero critical a11y violations |

---

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_ai_semantic_layer_crew.py` | new | Integration tests for crew factory — pre-flight, Crew type, agent/task count |
| `tests/test_registry_maintenance_agent.py` | new | Unit tests for Agent 41 — factory return type, role, model, tools |
| `tests/test_token_resolution_agent.py` | new | Unit tests for Agent 42 — factory return type, role, model, tools |
| `tests/test_composition_constraint_agent.py` | new | Unit tests for Agent 43 — factory return type, role, model, tools |
| `tests/test_validation_rule_agent.py` | new | Unit tests for Agent 44 — factory return type, role, model, tools |
| `tests/test_context_serializer_agent.py` | new | Unit tests for Agent 45 — factory return type, role, model, tools |
| `tests/test_spec_indexer.py` | new | Unit tests for SpecIndexer tool |
| `tests/test_example_code_generator.py` | new | Unit tests for ExampleCodeGenerator tool |
| `tests/test_registry_builder.py` | new | Unit tests for RegistryBuilder tool |
| `tests/test_token_graph_traverser.py` | new | Unit tests for TokenGraphTraverser tool |
| `tests/test_semantic_mapper.py` | new | Unit tests for SemanticMapper tool |
| `tests/test_composition_rule_extractor.py` | new | Unit tests for CompositionRuleExtractor tool |
| `tests/test_tree_validator.py` | new | Unit tests for TreeValidator tool |
| `tests/test_rule_compiler.py` | new | Unit tests for RuleCompiler tool |
| `tests/test_context_formatter.py` | new | Unit tests for ContextFormatter tool |
| `tests/test_token_budget_optimizer.py` | new | Unit tests for TokenBudgetOptimizer tool |
| `tests/test_multi_format_serializer.py` | new | Unit tests for MultiFormatSerializer tool |
