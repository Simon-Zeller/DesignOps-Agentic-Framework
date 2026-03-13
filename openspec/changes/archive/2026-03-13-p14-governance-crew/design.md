# Design: p14-governance-crew

## Technical Approach

The Governance Crew replaces the no-op stub in `src/daf/crews/governance.py` with a real CrewAI `Crew` that sequences five agents (26–30) across tasks T1–T5. The crew reads `pipeline-config.json` (written by Agent 5 in Phase 1) as its primary input seed, plus the compiled token files and component index from the shared output directory.

Task sequence:

1. **T1 — Ownership Assignment** (Agent 26): Reads the component index (from `docs/component-index.json` produced by the Documentation Crew in Phase 4a) and the pipeline-config `domains` section. Classifies each component and token category into a logical domain. Detects orphans (components unassignable to any domain). Writes `governance/ownership.json`.

2. **T2 — Workflow Definition** (Agent 27): Reads `pipeline-config.json` quality gate thresholds and `governance/ownership.json` domain structure. Generates `governance/workflow.json` as a state machine definition encoding the pipelines a token change and a new component must traverse, with gate check points.

3. **T3 — Deprecation Policy** (Agent 28): Reads `pipeline-config.json` lifecycle config and the component set. Generates `governance/deprecation-policy.json` with default grace periods, warning injection rules, migration guide requirements, and removal criteria. Tags any components bearing experimental/beta status in `governance/ownership.json`.

4. **T4 — RFC Templates** (Agent 29): Reads `governance/workflow.json` to determine when RFCs are required (new primitive, breaking token change, workflow modification). Generates `docs/templates/rfc-template.md` and writes `governance/process.json` encoding the RFC process definition.

5. **T5 — Quality Gate Enforcement** (Agent 30): Reads `reports/quality-scorecard.json` (from Agent 20), `docs/` (from Documentation Crew), and `governance/` directory. Evaluates each quality gate independently (coverage ≥ 80%, zero a11y critical violations, no phantom token refs, all components have docs, all have usage examples). Writes `governance/quality-gates.json` with per-component pass/fail per gate. Generates the four project-level test suites: `tests/tokens.test.ts`, `tests/a11y.test.ts`, `tests/composition.test.ts`, `tests/compliance.test.ts`.

All new tools are deterministic Python modules with no LLM calls. Agents call them as CrewAI tools. The only LLM reasoning is Agent 26's domain classification (ambiguous components) and Agent 30's quality report narrative. All other operations are verifiable and unit-testable.

The crew factory signature `create_governance_crew(output_dir: str) -> Crew` is preserved from the stub, so the pipeline orchestrator requires no changes.

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| Classify component/token into domain from known domain list | Deterministic (`domain_classifier.py`) | Rule-based keyword matching against component name, category, and relationships — no interpretation needed for standard components |
| Detect orphaned components (no domain match) | Deterministic (`orphan_scanner.py` extended) | Set subtraction: components not covered by any domain rule |
| Analyze cross-domain relationships | Deterministic (`relationship_analyzer.py`) | Graph traversal of component dependencies from `component-index.json` |
| Assign ambiguous multi-domain components to primary domain | Agent 26 (LLM: Sonnet) | Context-sensitive judgment when a component spans two domains equally (e.g., DataGrid spans "data-display" and "forms") |
| Generate workflow state machine definition | Deterministic (`workflow_state_machine.py`) | Template-driven state machine for standard token-change and component-change pipelines; parameterized by quality gate thresholds from `pipeline-config.json` |
| Map quality gates to workflow checkpoints | Deterministic (`gate_mapper.py`) | Lookup of gate IDs to workflow state transition guards; deterministic join |
| Compute lifecycle status for components | Deterministic (`stability_classifier.py`) | Rule-based: experimental if < 3 months old or below 70 quality score; beta if passes 70 but < 80% coverage; stable otherwise |
| Tag tokens/components with deprecation metadata | Deterministic (`deprecation_tagger.py`) | Field injection from known schema; already implemented |
| Generate deprecation policy config from lifecycle rules | Deterministic (`deprecation_policy_generator.py`) | Template expansion driven by `pipeline-config.json` lifecycle section |
| Generate RFC template markdown | Deterministic (`rfc_template_generator.py`) | Fixed-structure Markdown template, parameterized by workflow gate thresholds and approval criteria |
| Define RFC process entries (when required, approval criteria) | Agent 29 (LLM: Haiku) | RFC trigger conditions and approval criteria require light contextual judgment to tailor to the system's scope and complexity |
| Apply 80% coverage threshold per component | Deterministic (`threshold_gate.py` extended) | Numerical comparison; already implemented for 70/100 gate |
| Evaluate phantom ref gate | Deterministic (reads `reports/quality-scorecard.json`) | Parse existing phantom-ref scan results; no new tool needed |
| Evaluate docs completeness gate | Deterministic (`gate_evaluator.py`) | Cross-reference component list against `docs/` directory listing |
| Generate quality gate report narrative | Agent 30 (LLM: Haiku) | Synthesizes per-component gate failures into actionable human-readable summary |
| Generate project-level TypeScript test suites | Deterministic (`test_suite_generator.py`) | Fixed template per test file; parameterized by component names and token paths; no generative reasoning needed |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Agent 26: Ownership Agent | Tier-2 | Claude Sonnet | Needs contextual judgment to disambiguate multi-domain components; must read component-index.json and reason about functional category |
| Agent 27: Workflow Agent | Tier-3 | Claude Haiku | Fully deterministic tool orchestration — reads thresholds, drives template tools, assembles state machine output |
| Agent 28: Deprecation Agent | Tier-3 | Claude Haiku | Rule-based classification and policy generation; all logic is deterministic tool orchestration |
| Agent 29: RFC Agent | Tier-3 | Claude Haiku | RFC trigger conditions and template generation are template-driven; light judgment for process definitions |
| Agent 30: Quality Gate Agent | Tier-3 | Claude Haiku | Gate evaluation is pure arithmetic and file-existence checks; LLM only collects tool results and writes the summary report |

## Architecture Decisions

### Decision: Agent 30 pre-flight check for Documentation Crew completion

**Context:** PRD §3.5 specifies that Phase 4 is strictly ordered: Documentation Crew (4a) runs before Governance Crew (4b). The Quality Gate Agent (30) checks "all components have docs," which only makes sense if documentation exists. If the orchestrator fails to enforce this ordering, Agent 30 will silently flag all components as failing the docs gate.

**Decision:** The `create_governance_crew` factory adds a pre-flight guard that checks `docs/component-index.json` exists and is non-empty before instantiating any tasks. If the file is absent, the crew raises a `RuntimeError` with message `"Documentation Crew output not found — ensure Phase 4a completes before Phase 4b"`. This is a fail-fast guard, not a retry loop.

**Consequences:** The crew is not instantiated if documentation is missing, producing a clear error message. The orchestrator's Phase 4 ordering is still the primary enforcement mechanism; the guard is a defensive belt-and-suspenders check.

---

### Decision: Test suite generator uses fixed templates, not LLM generation

**Context:** Agent 30 must produce four TypeScript test files (`tokens.test.ts`, `a11y.test.ts`, `composition.test.ts`, `compliance.test.ts`) that encode the exit criteria as executable tests. These files must be syntactically valid TypeScript that imports the generated package and uses Vitest APIs.

**Decision:** `test_suite_generator.py` uses string templates with `{component_names}` and `{token_paths}` substitution. Each of the four test files has a fixed template that is parameterized with the actual component list and token paths read from the output directory. No LLM involvement in test generation.

**Consequences:** Tests are syntactically valid and predictable. Template changes require updating `test_suite_generator.py` rather than prompting. The suite generates correct import paths because it reads the actual output directory structure. Edge cases (e.g., component names with special characters) are sanitized before substitution.

---

### Decision: `governance/quality-gates.json` records per-gate, per-component results independently of `quality-scorecard.json`

**Context:** `quality-scorecard.json` (from Agent 20) records composite scores and sub-scores including raw test coverage. Agent 30 must apply the 80% coverage threshold. The question is whether Agent 30 writes a new file or amends `quality-scorecard.json`.

**Decision:** Agent 30 writes `governance/quality-gates.json` as a separate artifact, never modifying `quality-scorecard.json`. The gate file records `{"component": str, "gates": {"coverage_80": pass/fail, "a11y_zero_critical": pass/fail, "no_phantom_refs": pass/fail, "has_docs": pass/fail, "has_usage_example": pass/fail}}` per component.

**Consequences:** `quality-scorecard.json` remains Agent 20's sole responsibility (clean ownership boundary). `quality-gates.json` is entirely Governance Crew output. Downstream consumers (Release Crew) read both files independently.

---

### Decision: `relationship_analyzer.py` reads `docs/component-index.json`, not re-scans TSX

**Context:** Agent 26 needs component relationship data (which components depend on which) to detect cross-domain dependencies. This data could be derived by re-scanning TSX files or by reading the component index already built by the Documentation Crew.

**Decision:** `relationship_analyzer.py` reads `docs/component-index.json` (produced by Agent 22 in the Documentation Crew) rather than re-scanning source. If `component-index.json` is absent, it falls back to a flat component list from the output `src/` directory with no relationship data, logging a Warning.

**Consequences:** No new TSX parsing logic needed. The tool depends on Phase 4a ordering (same as Agent 30's pre-flight). The fallback ensures the Governance Crew can still run with degraded (no cross-domain relationship) data if Phase 4a had a partial failure.

## Data Flow

```
[DS Bootstrap Crew]
  Agent 5 ──writes──► pipeline-config.json ──reads──► Agent 26, 27, 28, 29, 30

[Documentation Crew (Phase 4a)]
  Agent 22 ──writes──► docs/component-index.json ──reads──► Agent 26, 30

[Component Factory Crew]
  Agent 20 ──writes──► reports/quality-scorecard.json ──reads──► Agent 30

[Governance Crew (Phase 4b)] ──writes──►
  governance/ownership.json         (Agent 26)
  governance/workflow.json          (Agent 27)
  governance/deprecation-policy.json (Agent 28)
  governance/quality-gates.json     (Agent 30)
  docs/templates/rfc-template.md    (Agent 29)
  governance/process.json           (Agent 29)
  tests/tokens.test.ts              (Agent 30)
  tests/a11y.test.ts                (Agent 30)
  tests/composition.test.ts         (Agent 30)
  tests/compliance.test.ts          (Agent 30)

[Release Crew] ──reads──► governance/ + tests/*.test.ts
```

## Retry & Failure Behavior

The Governance Crew falls within Phases 4–6, so it is subject to the **max 2 crew-level retry** boundary defined in PRD §3.4. A retry is triggered when the crew's aggregate output fails post-crew validation (e.g., `governance/quality-gates.json` is malformed or missing required keys).

Individual task failures:
- **T1–T4 failures**: Structured rejection fed back to the responsible agent with the validation error. Max 2 agent-level correction attempts per task before escalating to crew-level retry.
- **T5 (Quality Gate Agent) failures**: If test suite generation produces invalid TypeScript (detected by running `tsc --noEmit` on the test files), Agent 30 re-generates the affected file from the template with sanitized inputs. Max 2 correction attempts.
- **Pre-flight failure** (docs missing): Immediate `RuntimeError` — not retried. Requires operator intervention to ensure Phase 4a completed.

On crew-level retry, all tasks re-run from T1. The pre-flight check is re-evaluated on retry (defensive against race conditions in distributed execution).

## File Changes

**New agent files:**
- `src/daf/agents/ownership.py` (new) — Agent 26: Ownership Agent
- `src/daf/agents/workflow.py` (new) — Agent 27: Workflow Agent
- `src/daf/agents/deprecation.py` (new) — Agent 28: Deprecation Agent
- `src/daf/agents/rfc.py` (new) — Agent 29: RFC Agent
- `src/daf/agents/quality_gate.py` (new) — Agent 30: Quality Gate Agent

**New tool files:**
- `src/daf/tools/domain_classifier.py` (new) — keyword-based component→domain classification
- `src/daf/tools/relationship_analyzer.py` (new) — cross-domain dependency graph from component-index.json
- `src/daf/tools/workflow_state_machine.py` (new) — state machine generator for token/component change pipelines
- `src/daf/tools/gate_mapper.py` (new) — maps gate IDs to workflow transition guards
- `src/daf/tools/lifecycle_tagger.py` (new) — assigns stable/beta/experimental status
- `src/daf/tools/deprecation_policy_generator.py` (new) — template-driven deprecation policy config
- `src/daf/tools/stability_classifier.py` (new) — rule-based stability status classifier
- `src/daf/tools/rfc_template_generator.py` (new) — Markdown RFC template generator
- `src/daf/tools/process_definition_builder.py` (new) — RFC process definition JSON builder
- `src/daf/tools/gate_evaluator.py` (new) — per-component, per-gate pass/fail evaluator
- `src/daf/tools/report_writer.py` (new) — quality gate report narrative serializer
- `src/daf/tools/test_suite_generator.py` (new) — generates the four TypeScript test suite files

**Modified files:**
- `src/daf/crews/governance.py` (modified) — replace StubCrew with real CrewAI Crew (5 agents, 5 tasks)

**New test files (TDD-first):**
- `tests/test_ownership_agent.py` (new)
- `tests/test_workflow_agent.py` (new)
- `tests/test_deprecation_agent.py` (new)
- `tests/test_rfc_agent.py` (new)
- `tests/test_quality_gate_agent.py` (new)
- `tests/test_domain_classifier.py` (new)
- `tests/test_relationship_analyzer.py` (new)
- `tests/test_workflow_state_machine.py` (new)
- `tests/test_gate_mapper.py` (new)
- `tests/test_lifecycle_tagger.py` (new)
- `tests/test_deprecation_policy_generator.py` (new)
- `tests/test_stability_classifier.py` (new)
- `tests/test_rfc_template_generator.py` (new)
- `tests/test_process_definition_builder.py` (new)
- `tests/test_gate_evaluator.py` (new)
- `tests/test_report_writer.py` (new)
- `tests/test_test_suite_generator.py` (new)
