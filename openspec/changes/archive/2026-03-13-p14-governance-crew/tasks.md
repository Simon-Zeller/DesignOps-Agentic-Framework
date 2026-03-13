# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

## 0. Pre-flight

- [x] 0.1 Create feature branch: `feat/p14-governance-crew`
- [x] 0.2 Verify clean working tree (`git status`)
- [x] 0.3 Confirm `pytest`, `ruff`, and `pyright` are available in the environment

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write failing tests FIRST, before any production code. Each test maps to a case from tdd.md. -->

### 1a. Agent tests

- [x] 1.1 Create `tests/test_ownership_agent.py` — tests for Agent 26 role, tools (DomainClassifier, RelationshipAnalyzer, OrphanScanner), Sonnet model tier
- [x] 1.2 Create `tests/test_workflow_agent.py` — tests for Agent 27 role, tools (WorkflowStateMachine, GateMapper), Haiku model tier
- [x] 1.3 Create `tests/test_deprecation_agent.py` — tests for Agent 28 role, tools (LifecycleTagger, DeprecationPolicyGenerator, StabilityClassifier, DeprecationTagger)
- [x] 1.4 Create `tests/test_rfc_agent.py` — tests for Agent 29 role, tools (RFCTemplateGenerator, ProcessDefinitionBuilder)
- [x] 1.5 Create `tests/test_quality_gate_agent.py` — tests for Agent 30 role, tools (GateEvaluator, ThresholdGate, ReportWriter, TestSuiteGenerator)

### 1b. Tool tests

- [x] 1.6 Create `tests/test_domain_classifier.py` — classification, multi-domain scoring, orphan detection, empty list edge case
- [x] 1.7 Create `tests/test_relationship_analyzer.py` — cross-domain detection, missing file fallback
- [x] 1.8 Create `tests/test_workflow_state_machine.py` — state machine generation, empty gates produces null gate_checks, JSON-serializable output
- [x] 1.9 Create `tests/test_gate_mapper.py` — gate ID to workflow transition mapping
- [x] 1.10 Create `tests/test_stability_classifier.py` — beta/experimental/stable rules, explicit tag precedence
- [x] 1.11 Create `tests/test_lifecycle_tagger.py` — lifecycle_status metadata injection via BaseTool
- [x] 1.12 Create `tests/test_deprecation_policy_generator.py` — grace period default, migration_guide_required logic
- [x] 1.13 Create `tests/test_rfc_template_generator.py` — required sections present, idempotency
- [x] 1.14 Create `tests/test_process_definition_builder.py` — rfc_required_for always contains new_primitive and breaking_token_change
- [x] 1.15 Create `tests/test_gate_evaluator.py` — all gates pass scenario, coverage gate fails independently, missing a11y file returns False, all False when scorecard absent
- [x] 1.16 Create `tests/test_report_writer.py` — file written, valid JSON, contains expected component names
- [x] 1.17 Create `tests/test_test_suite_generator.py` — describe block present, kebab-case sanitized to camelCase, empty component list handled

### 1c. Crew integration tests

- [x] 1.18 Create `tests/test_governance_crew.py` — RuntimeError when component-index.json absent, successful instantiation when present

### 1d. Red phase verification

- [x] 1.19 Run `pytest tests/test_ownership_agent.py tests/test_workflow_agent.py tests/test_deprecation_agent.py tests/test_rfc_agent.py tests/test_quality_gate_agent.py -x` — confirm all FAIL (ImportError expected)
- [x] 1.20 Run `pytest tests/test_domain_classifier.py tests/test_relationship_analyzer.py tests/test_workflow_state_machine.py tests/test_gate_mapper.py tests/test_stability_classifier.py -x` — confirm all FAIL
- [x] 1.21 Run `pytest tests/test_lifecycle_tagger.py tests/test_deprecation_policy_generator.py tests/test_rfc_template_generator.py tests/test_process_definition_builder.py -x` — confirm all FAIL
- [x] 1.22 Run `pytest tests/test_gate_evaluator.py tests/test_report_writer.py tests/test_test_suite_generator.py tests/test_governance_crew.py -x` — confirm all FAIL
- [x] 1.23 **Git checkpoint:** `git add -A && git commit -m "test: scaffold failing tests for p14-governance-crew"`

## 2. Implementation (TDD — Green Phase)

### 2a. Tool implementations

- [x] 2.1 Create `src/daf/tools/domain_classifier.py` — keyword-based component→domain classification with scoring; returns `"__orphan__"` for unmatched; make tests/test_domain_classifier.py pass
- [x] 2.2 Create `src/daf/tools/relationship_analyzer.py` — reads `docs/component-index.json`, returns cross-domain dependency list; make tests/test_relationship_analyzer.py pass
- [x] 2.3 Create `src/daf/tools/workflow_state_machine.py` — generates `token_change_pipeline` and `component_change_pipeline` state machine dicts from quality gate thresholds; make tests/test_workflow_state_machine.py pass
- [x] 2.4 Create `src/daf/tools/gate_mapper.py` — maps gate IDs to workflow state transition guards; make tests/test_gate_mapper.py pass
- [x] 2.5 Create `src/daf/tools/stability_classifier.py` — classifies stable/beta/experimental per component using score, coverage, and explicit tags; make tests/test_stability_classifier.py pass
- [x] 2.6 Create `src/daf/tools/lifecycle_tagger.py` — BaseTool that injects `lifecycle_status` into a component dict; make tests/test_lifecycle_tagger.py pass
- [x] 2.7 Create `src/daf/tools/deprecation_policy_generator.py` — template-driven deprecation policy from lifecycle config; make tests/test_deprecation_policy_generator.py pass
- [x] 2.8 Create `src/daf/tools/rfc_template_generator.py` — BaseTool that generates RFC Markdown template with required sections; make tests/test_rfc_template_generator.py pass
- [x] 2.9 Create `src/daf/tools/process_definition_builder.py` — BaseTool that builds RFC process definition JSON; make tests/test_process_definition_builder.py pass
- [x] 2.10 Create `src/daf/tools/gate_evaluator.py` — BaseTool evaluating five per-component gates independently; make tests/test_gate_evaluator.py pass
- [x] 2.11 Create `src/daf/tools/report_writer.py` — BaseTool serializing gate results to `governance/quality-gates.json`; make tests/test_report_writer.py pass
- [x] 2.12 Create `src/daf/tools/test_suite_generator.py` — generates four TypeScript test suite files from templates with component name sanitization; make tests/test_test_suite_generator.py pass

### 2b. Agent implementations

- [x] 2.13 Create `src/daf/agents/ownership.py` — `create_ownership_agent(model, output_dir)` using DomainClassifier, RelationshipAnalyzer, OrphanScanner; Sonnet model; make tests/test_ownership_agent.py pass
- [x] 2.14 Create `src/daf/agents/workflow.py` — `create_workflow_agent(model, output_dir)` using WorkflowStateMachine, GateMapper; Haiku model; make tests/test_workflow_agent.py pass
- [x] 2.15 Create `src/daf/agents/deprecation.py` — `create_deprecation_agent(model, output_dir)` using LifecycleTagger, DeprecationPolicyGenerator, StabilityClassifier, DeprecationTagger; Haiku model; make tests/test_deprecation_agent.py pass
- [x] 2.16 Create `src/daf/agents/rfc.py` — `create_rfc_agent(model, output_dir)` using RFCTemplateGenerator, ProcessDefinitionBuilder; Haiku model; make tests/test_rfc_agent.py pass
- [x] 2.17 Create `src/daf/agents/quality_gate.py` — `create_quality_gate_agent(model, output_dir)` using GateEvaluator, ThresholdGate, ReportWriter, TestSuiteGenerator; Haiku model; make tests/test_quality_gate_agent.py pass

### 2c. Crew wiring

- [x] 2.18 Replace the `StubCrew` in `src/daf/crews/governance.py` with a real CrewAI `Crew`:
  - Add pre-flight guard: raise `RuntimeError` if `docs/component-index.json` is absent or empty
  - Wire 5 tasks (T1–T5) in sequential order using the 5 new agents
  - Preserve the `create_governance_crew(output_dir: str)` signature
  - Make `tests/test_governance_crew.py` pass

### 2d. Green phase verification

- [x] 2.19 Run `pytest tests/test_ownership_agent.py tests/test_workflow_agent.py tests/test_deprecation_agent.py tests/test_rfc_agent.py tests/test_quality_gate_agent.py` — all PASS
- [x] 2.20 Run `pytest tests/test_domain_classifier.py tests/test_relationship_analyzer.py tests/test_workflow_state_machine.py tests/test_gate_mapper.py tests/test_stability_classifier.py` — all PASS
- [x] 2.21 Run `pytest tests/test_lifecycle_tagger.py tests/test_deprecation_policy_generator.py tests/test_rfc_template_generator.py tests/test_process_definition_builder.py` — all PASS
- [x] 2.22 Run `pytest tests/test_gate_evaluator.py tests/test_report_writer.py tests/test_test_suite_generator.py tests/test_governance_crew.py` — all PASS
- [x] 2.23 **Git checkpoint:** `git add -A && git commit -m "feat: implement p14-governance-crew agents, tools, and crew wiring"`

## 3. Refactor (TDD — Refactor Phase)

- [x] 3.1 Review all new tool modules: ensure no code duplication across similar tools (e.g., `deprecation_tagger.py` and `lifecycle_tagger.py` should share no reimplemented logic)
- [x] 3.2 Review agent modules: ensure factory function naming is consistent with existing agents (`quality_scoring.py`, `accessibility.py`, etc.)
- [x] 3.3 Review `governance.py`: ensure pre-flight guard is readable and the task definitions reference agents by their correct factory names
- [x] 3.4 Confirm all tests still PASS after refactor
- [x] 3.5 Review against design.md decisions — verify architecture decisions are reflected in implementation (separate quality-gates.json, relationship_analyzer reads component-index.json)
- [x] 3.6 **Git checkpoint:** `git add -A && git commit -m "refactor: clean up p14-governance-crew implementation"`

## 4. Integration & Quality

- [x] 4.1 Run `ruff check src/daf/agents/ownership.py src/daf/agents/workflow.py src/daf/agents/deprecation.py src/daf/agents/rfc.py src/daf/agents/quality_gate.py src/daf/crews/governance.py src/daf/tools/domain_classifier.py src/daf/tools/relationship_analyzer.py src/daf/tools/workflow_state_machine.py src/daf/tools/gate_mapper.py src/daf/tools/stability_classifier.py src/daf/tools/lifecycle_tagger.py src/daf/tools/deprecation_policy_generator.py src/daf/tools/rfc_template_generator.py src/daf/tools/process_definition_builder.py src/daf/tools/gate_evaluator.py src/daf/tools/report_writer.py src/daf/tools/test_suite_generator.py` — zero warnings
- [x] 4.2 Run `pyright src/daf/agents/ownership.py src/daf/agents/workflow.py src/daf/agents/deprecation.py src/daf/agents/rfc.py src/daf/agents/quality_gate.py src/daf/crews/governance.py` — zero errors
- [x] 4.3 Fix all lint and type errors
- [x] 4.4 Run full test suite: `pytest tests/` — all pass; no regressions in existing tests
- [x] 4.5 Verify test coverage ≥ 80% for all new modules: `pytest tests/ --cov=src/daf --cov-report=term-missing`
- [x] 4.6 **Git checkpoint:** `git add -A && git commit -m "chore: fix lint and type errors for p14-governance-crew"` (skip if no changes)

## 5. Final Verification & Push

- [x] 5.1 `git status` — confirm zero untracked files, zero unstaged changes
- [x] 5.2 `git log --oneline main..HEAD` — review all commits on this branch
- [x] 5.3 Rebase on latest main if needed: `git fetch origin && git rebase origin/main`
- [x] 5.4 Push feature branch: `git push origin feat/p14-governance-crew`

## 6. Delivery

- [x] 6.1 All tasks above are checked
- [x] 6.2 Merge feature branch into main: `git checkout main && git merge feat/p14-governance-crew`
- [x] 6.3 Push main: `git push origin main`
- [x] 6.4 Delete local feature branch: `git branch -d feat/p14-governance-crew`
- [x] 6.5 Delete remote feature branch: `git push origin --delete feat/p14-governance-crew`
- [x] 6.6 Verify clean state: `git branch -a` (feature branch gone), `git status` (clean)
