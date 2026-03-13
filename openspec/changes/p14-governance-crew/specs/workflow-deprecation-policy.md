# Specification: Workflow & Deprecation Policy

## Purpose

Defines the behavior of Agent 27 (Workflow Agent) and Agent 28 (Deprecation Agent), along with their tools. Agent 27 generates `governance/workflow.json` as a state machine encoding the change pipelines for tokens and components. Agent 28 generates `governance/deprecation-policy.json` and assigns lifecycle status (`stable`, `beta`, `experimental`) to each component.

## Requirements

### Requirement: workflow.json encodes two state machines

Agent 27 MUST generate `governance/workflow.json` containing exactly two state machine definitions: `token_change_pipeline` and `component_change_pipeline`. Each SHALL be represented as a list of state objects, where each state has a name, allowed transitions, and an optional quality gate check.

The `workflow_state_machine.py` tool SHALL accept quality gate thresholds from `pipeline-config.json` and return the serialized state machine dict. The `gate_mapper.py` tool SHALL map gate IDs (e.g., `"coverage_80"`, `"a11y_zero_critical"`) to the transitions where they act as guards.

#### Acceptance Criteria

- [ ] `governance/workflow.json` contains both `token_change_pipeline` and `component_change_pipeline` top-level keys.
- [ ] Each pipeline is a list of state objects with required keys: `state` (str), `transitions` (list), `gate_check` (str | null).
- [ ] Gate thresholds in workflow transitions match values from `pipeline-config.json`'s `qualityGates` section.
- [ ] `workflow_state_machine.py` returns a dict passing `json.dumps` without error.
- [ ] `gate_mapper.py` returns an empty mapping when no gates are configured (graceful degradation).

#### Scenario: Token change pipeline with gate checkpoint

- GIVEN `pipeline-config.json` sets `qualityGates.minCompositeScore: 70` and `a11yLevel: "AA"`
- WHEN Agent 27 runs Task T2
- THEN `token_change_pipeline` contains a state `"gate_check"` with `gate_check: "coverage_80"` guarding the transition to `"approved"`
- AND the gate threshold in the state description references `70`

#### Scenario: Empty quality gates config

- GIVEN `pipeline-config.json` has `qualityGates: {}` (no thresholds set)
- WHEN `gate_mapper.py` is called
- THEN it returns `{}` without error
- AND `governance/workflow.json` is written with gate_check fields set to `null`

---

### Requirement: deprecation-policy.json is generated from pipeline-config lifecycle section

Agent 28 MUST generate `governance/deprecation-policy.json` using the `deprecation_policy_generator.py` tool, parameterized by `pipeline-config.json`'s `lifecycle` section. The policy SHALL include: default grace period (in days), warning injection rules, migration guide requirement flag, and removal criteria.

#### Acceptance Criteria

- [ ] `governance/deprecation-policy.json` contains keys: `grace_period_days` (int), `warning_injection` (object), `migration_guide_required` (bool), `removal_criteria` (list of str).
- [ ] `grace_period_days` defaults to 90 if not specified in `pipeline-config.json`.
- [ ] `migration_guide_required` is `true` when `pipeline-config.json` lifecycle `defaultStatus` is `"stable"`.
- [ ] `deprecation_policy_generator.py` returns valid JSON-serializable dict for any valid `pipeline-config.json`.

#### Scenario: Standard deprecation policy generation

- GIVEN `pipeline-config.json` sets `lifecycle.defaultStatus: "stable"` and `lifecycle.gracePeriodDays: 60`
- WHEN Agent 28 runs Task T3
- THEN `governance/deprecation-policy.json` contains `grace_period_days: 60` and `migration_guide_required: true`

#### Scenario: Default grace period applied

- GIVEN `pipeline-config.json` does not specify `lifecycle.gracePeriodDays`
- WHEN `deprecation_policy_generator.py` runs
- THEN `grace_period_days` in the output is `90`

---

### Requirement: stability_classifier assigns lifecycle status per component

The `stability_classifier.py` tool SHALL assign `"stable"`, `"beta"`, or `"experimental"` status to each component based on: (1) the `defaultStatus` from `pipeline-config.json`, (2) the component's composite quality score from `quality-scorecard.json`, and (3) the component's explicit status if already set in the component index.

Rules:
- `experimental`: composite score < 70 OR explicitly tagged in component index
- `beta`: composite score ≥ 70 but < 80% test coverage (from quality-scorecard.json)
- `stable`: composite score ≥ 70 and ≥ 80% test coverage AND `defaultStatus` is `"stable"`

#### Acceptance Criteria

- [ ] Every component in the output directory appears in the stability classification result.
- [ ] Classification rules are applied in the specified priority order.
- [ ] `stability_classifier.py` returns a dict `{component_name: "stable" | "beta" | "experimental"}`.
- [ ] Classification result is referenced in `governance/deprecation-policy.json` under `component_statuses`.

#### Scenario: Beta classification for coverage below threshold

- GIVEN `Button` has composite score `75.0` (≥70, gate passed) but test coverage `72%` (< 80%)
- WHEN `stability_classifier.py` processes `Button`
- THEN `Button` is classified as `"beta"`

#### Scenario: Explicit experimental tag takes precedence

- GIVEN `DataGrid` has composite score `82.0` and 85% coverage
- AND `DataGrid` is explicitly tagged `experimental` in the component index
- WHEN `stability_classifier.py` processes `DataGrid`
- THEN `DataGrid` is classified as `"experimental"` (explicit tag takes precedence)
