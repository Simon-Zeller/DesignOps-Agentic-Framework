# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

## 0. Pre-flight

- [ ] 0.1 Create feature branch: `feat/p16-ai-semantic-layer-crew`
- [ ] 0.2 Verify clean working tree (`git status`)
- [ ] 0.3 Confirm `ANTHROPIC_API_KEY` is set in environment for integration test runs

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write failing tests FIRST, before any production code.
     Each test maps to a case from tdd.md. -->

### Crew factory tests
- [ ] 1.1 Create `tests/test_ai_semantic_layer_crew.py` with:
  - `test_crew_raises_runtime_error_when_no_spec_files_exist`
  - `test_crew_raises_runtime_error_when_specs_dir_empty`
  - `test_crew_returns_crewai_crew_when_specs_exist`
  - `test_crew_has_five_agents_and_five_tasks`
  - `test_crew_creates_registry_directory`

### Agent factory tests
- [ ] 1.2 Create `tests/test_registry_maintenance_agent.py` — factory return type, role keyword, Haiku model, tools
- [ ] 1.3 Create `tests/test_token_resolution_agent.py` — factory return type, role keyword, Haiku model, tools
- [ ] 1.4 Create `tests/test_composition_constraint_agent.py` — factory return type, role keyword, Sonnet model, tools
- [ ] 1.5 Create `tests/test_validation_rule_agent.py` — factory return type, role keyword, Haiku model, tools
- [ ] 1.6 Create `tests/test_context_serializer_agent.py` — factory return type, role keyword, Sonnet model, tools

### Tool tests
- [ ] 1.7 Create `tests/test_spec_indexer.py` — parses props from YAML, returns empty list when specs absent
- [ ] 1.8 Create `tests/test_example_code_generator.py` — returns JSX string for simple spec
- [ ] 1.9 Create `tests/test_registry_builder.py` — writes valid JSON, creates `registry/` dir, handles spec with no props
- [ ] 1.10 Create `tests/test_token_graph_traverser.py` — resolves semantic token, handles empty files, handles missing `tokens/`
- [ ] 1.11 Create `tests/test_semantic_mapper.py` — assigns correct tier labels
- [ ] 1.12 Create `tests/test_composition_rule_extractor.py` — reads audit when present, falls back to spec YAML
- [ ] 1.13 Create `tests/test_tree_validator.py` — returns valid for conforming tree, returns violation for forbidden nesting
- [ ] 1.14 Create `tests/test_rule_compiler.py` — writes valid JSON, four required categories, handles empty registries
- [ ] 1.15 Create `tests/test_context_formatter.py` — basic format structure tests
- [ ] 1.16 Create `tests/test_token_budget_optimizer.py` — no truncation within limit, removes usage examples first when over budget
- [ ] 1.17 Create `tests/test_multi_format_serializer.py` — writes all three files, valid JSON, non-empty Markdown, handles missing upstream file

- [ ] 1.18 Verify **all new tests FAIL** (`pytest tests/test_ai_semantic_layer_crew.py tests/test_registry_maintenance_agent.py ... -x`)
- [ ] 1.19 **Git checkpoint:** `git add -A && git commit -m "test: scaffold failing tests for p16-ai-semantic-layer-crew"`

## 2. Implementation (TDD — Green Phase)

### 2A. Deterministic Tools

- [ ] 2.1 Create `src/daf/tools/spec_indexer.py` — `SpecIndexer` class: reads `specs/*.spec.yaml`, returns structured component metadata list
- [ ] 2.2 Create `src/daf/tools/example_code_generator.py` — `ExampleCodeGenerator` class: generates JSX usage examples from spec prop definitions
- [ ] 2.3 Create `src/daf/tools/registry_builder.py` — `RegistryBuilder` class: assembles and writes `registry/components.json`; creates `registry/` dir if absent
- [ ] 2.4 Create `src/daf/tools/token_graph_traverser.py` — `TokenGraphTraverser` class: reads `tokens/*.tokens.json`, resolves reference chains, returns flat token list with resolved values
- [ ] 2.5 Create `src/daf/tools/semantic_mapper.py` — `SemanticMapper` class: assigns tier labels, groups by category, returns enriched token list
- [ ] 2.6 Create `src/daf/tools/composition_rule_extractor.py` — `CompositionRuleExtractor` class: reads `reports/composition-audit.json` with fallback to `specs/*.spec.yaml`
- [ ] 2.7 Create `src/daf/tools/tree_validator.py` — `TreeValidator` class: validates component tree dict against composition rules; returns `{valid, violations}`
- [ ] 2.8 Create `src/daf/tools/rule_compiler.py` — `RuleCompiler` class: reads registry files, aggregates rules into four categories, writes `registry/compliance-rules.json`
- [ ] 2.9 Create `src/daf/tools/context_formatter.py` — `ContextFormatter` class: transforms registry JSON into `.cursorrules` and `copilot-instructions.md` format strings
- [ ] 2.10 Create `src/daf/tools/token_budget_optimizer.py` — `TokenBudgetOptimizer` class: counts tokens (character-based approximation), applies priority-ordered truncation strategy
- [ ] 2.11 Create `src/daf/tools/multi_format_serializer.py` — `MultiFormatSerializer` class: writes `.cursorrules`, `copilot-instructions.md`, `ai-context.json` to `output_dir`
- [ ] 2.12 Verify tool tests pass (`pytest tests/test_spec_indexer.py tests/test_registry_builder.py ...`)
- [ ] 2.13 **Git checkpoint:** `git add -A && git commit -m "feat(ai-semantic-layer): implement deterministic tools"`

### 2B. Agent Factories

- [ ] 2.14 Create `src/daf/agents/registry_maintenance.py` — `create_registry_maintenance_agent(model, output_dir) → crewai.Agent`; role "Knowledge graph builder"; tools: `SpecIndexer`, `ExampleCodeGenerator`, `RegistryBuilder`; model: Haiku
- [ ] 2.15 Create `src/daf/agents/token_resolution.py` — `create_token_resolution_agent(model, output_dir) → crewai.Agent`; role "Semantic intent mapper"; tools: `TokenGraphTraverser`, `SemanticMapper`; model: Haiku
- [ ] 2.16 Create `src/daf/agents/composition_constraint.py` — `create_composition_constraint_agent(model, output_dir) → crewai.Agent`; role "Valid tree definer"; tools: `CompositionRuleExtractor`, `TreeValidator`; model: Sonnet
- [ ] 2.17 Create `src/daf/agents/validation_rule.py` — `create_validation_rule_agent(model, output_dir) → crewai.Agent`; role "Compliance rule exporter"; tools: `RuleCompiler`; model: Haiku
- [ ] 2.18 Create `src/daf/agents/context_serializer.py` — `create_context_serializer_agent(model, output_dir) → crewai.Agent`; role "AI context packager"; tools: `ContextFormatter`, `TokenBudgetOptimizer`, `MultiFormatSerializer`; model: Sonnet
- [ ] 2.19 Update `src/daf/agents/__init__.py` — export all five new agent factories
- [ ] 2.20 Verify agent tests pass (`pytest tests/test_registry_maintenance_agent.py ...`)
- [ ] 2.21 **Git checkpoint:** `git add -A && git commit -m "feat(ai-semantic-layer): implement agent factories 41-45"`

### 2C. Crew Factory

- [ ] 2.22 Rewrite `src/daf/crews/ai_semantic_layer.py`:
  - Remove `StubCrew` import and stub `_run` function
  - Add pre-flight guard: `RuntimeError` if `specs/*.spec.yaml` absent
  - Ensure `registry/` directory is created
  - Instantiate agents 41–45 with correct model tier strings
  - Define tasks T1–T5 with sequential `context` chaining
  - Return `crewai.Crew(agents=[...], tasks=[...], verbose=False)`
- [ ] 2.23 Update `src/daf/tools/__init__.py` — export all new tool classes
- [ ] 2.24 Verify crew tests pass (`pytest tests/test_ai_semantic_layer_crew.py`)
- [ ] 2.25 Run all new tests together: confirm green (`pytest tests/test_ai_semantic_layer_crew.py tests/test_registry_maintenance_agent.py tests/test_token_resolution_agent.py tests/test_composition_constraint_agent.py tests/test_validation_rule_agent.py tests/test_context_serializer_agent.py tests/test_spec_indexer.py tests/test_example_code_generator.py tests/test_registry_builder.py tests/test_token_graph_traverser.py tests/test_semantic_mapper.py tests/test_composition_rule_extractor.py tests/test_tree_validator.py tests/test_rule_compiler.py tests/test_context_formatter.py tests/test_token_budget_optimizer.py tests/test_multi_format_serializer.py`)
- [ ] 2.26 **Git checkpoint:** `git add -A && git commit -m "feat(ai-semantic-layer): implement AI Semantic Layer Crew agents 41-45"`

## 3. Refactor (TDD — Refactor Phase)

- [ ] 3.1 Review `ai_semantic_layer.py` against design.md — verify `_SONNET_MODEL` / `_HAIKU_MODEL` constants match design tier assignments
- [ ] 3.2 Review tool classes — ensure `primitive_registry.py` is reused for primitive data (Agent 41 decision, design.md §Architecture Decisions)
- [ ] 3.3 Extract any repeated file-path patterns into helper constants or properties within tool classes
- [ ] 3.4 Ensure all module docstrings reference the agent number, crew, and phase (`"""Agent 41 – Registry Maintenance Agent (AI Semantic Layer Crew, Phase 5)."""`)
- [ ] 3.5 Run full new test suite — confirm all still pass after refactor
- [ ] 3.6 **Git checkpoint:** `git add -A && git commit -m "refactor(ai-semantic-layer): clean up crew and tool implementation"`

## 4. Integration & Quality

- [ ] 4.1 Run full linter: `ruff check src/ tests/`
- [ ] 4.2 Fix all lint errors — zero warnings policy
- [ ] 4.3 Run type checker: `pyright src/`
- [ ] 4.4 Fix all type errors
- [ ] 4.5 Run **full test suite**: `pytest` — verify no regressions in existing tests
- [ ] 4.6 Check coverage: `pytest --cov=src/daf/crews/ai_semantic_layer --cov=src/daf/agents/registry_maintenance --cov=src/daf/agents/token_resolution --cov=src/daf/agents/composition_constraint --cov=src/daf/agents/validation_rule --cov=src/daf/agents/context_serializer --cov=src/daf/tools/spec_indexer --cov=src/daf/tools/registry_builder --cov=src/daf/tools/token_graph_traverser --cov=src/daf/tools/rule_compiler --cov=src/daf/tools/multi_format_serializer --cov-report=term-missing`
- [ ] 4.7 Confirm ≥80% line coverage on all new modules
- [ ] 4.8 **Git checkpoint:** `git add -A && git commit -m "chore: fix lint and type errors for p16-ai-semantic-layer-crew"` (skip if no changes)

## 5. Final Verification & Push

- [ ] 5.1 `git status` — confirm zero untracked files, zero unstaged changes
- [ ] 5.2 `git log --oneline main..HEAD` — review all commits on this branch
- [ ] 5.3 Rebase on latest main if needed: `git fetch origin && git rebase origin/main`
- [ ] 5.4 Push feature branch: `git push origin feat/p16-ai-semantic-layer-crew`

## 6. Delivery

- [ ] 6.1 All tasks above are checked
- [ ] 6.2 Merge feature branch into main: `git checkout main && git merge feat/p16-ai-semantic-layer-crew`
- [ ] 6.3 Push main: `git push origin main`
- [ ] 6.4 Delete local feature branch: `git branch -d feat/p16-ai-semantic-layer-crew`
- [ ] 6.5 Delete remote feature branch: `git push origin --delete feat/p16-ai-semantic-layer-crew`
- [ ] 6.6 Verify clean state: `git branch -a` — feature branch gone, `git status` — clean
