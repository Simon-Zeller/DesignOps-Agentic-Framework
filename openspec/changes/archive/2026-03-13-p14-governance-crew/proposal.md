# Proposal: p14-governance-crew

## Intent

The Governance Crew (Phase 4b) is defined in PRD §4.6 with 5 agents (26–30) but is currently implemented as a stub: `create_governance_crew` in `src/daf/crews/governance.py` simply writes empty JSON files and placeholder TypeScript stubs. No real agent logic, tool orchestration, or CrewAI task wiring exists.

This change implements the full Governance Crew — replacing the stub with a production-ready CrewAI crew housing all 5 agents, their tools, and the tasks that connect them. The crew generates the team adoption kit: ownership maps, workflow definitions, deprecation policy, RFC templates, and quality gate enforcement (including the four project-level test suites that encode exit criteria as executable tests).

Without this change, the pipeline produces governance artifacts that are syntactically empty, quality gates are never evaluated, and the generated design system is not governance-ready at handoff.

## Scope

### In scope

- **5 agent implementations** (Agents 26–30): `ownership.py`, `workflow.py`, `deprecation.py`, `rfc.py`, `quality_gate.py` in `src/daf/agents/`
- **Missing tools** for those agents:
  - Agent 26 (Ownership): `domain_classifier.py`, `relationship_analyzer.py` (orphan_scanner.py already exists)
  - Agent 27 (Workflow): `workflow_state_machine.py`, `gate_mapper.py`
  - Agent 28 (Deprecation): `lifecycle_tagger.py`, `deprecation_policy_generator.py`, `stability_classifier.py` (deprecation_tagger.py already exists)
  - Agent 29 (RFC): `rfc_template_generator.py`, `process_definition_builder.py`
  - Agent 30 (Quality Gate): `gate_evaluator.py`, `report_writer.py`, `test_suite_generator.py` (threshold_gate.py already exists)
- **Crew wiring**: Replace the `StubCrew` in `governance.py` with a fully wired `Crew` with 5 tasks (T1–T5) in dependency order
- **Unit tests** for all 5 agents and all new tools (TDD-first: tests written before implementation)

### Out of scope

- Changes to `pipeline-config.json` schema (Agent 5 output — defined in §3.8, covered by a dedicated change)
- Modifications to Documentation Crew (Phase 4a), which must complete before Quality Gate Agent runs
- Changes to any other crew's output contracts
- Visual regression or Playwright tooling (owned by Render Validation layer)

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| Governance Crew (Phase 4b) | Agent 26: Ownership Agent | Full implementation — replaces stub |
| Governance Crew (Phase 4b) | Agent 27: Workflow Agent | Full implementation — replaces stub |
| Governance Crew (Phase 4b) | Agent 28: Deprecation Agent | Full implementation — replaces stub |
| Governance Crew (Phase 4b) | Agent 29: RFC Agent | Full implementation — replaces stub |
| Governance Crew (Phase 4b) | Agent 30: Quality Gate Agent | Full implementation — replaces stub |
| DS Bootstrap Crew | Agent 5: Pipeline Configuration Agent | Read-only consumer — `pipeline-config.json` is this crew's input seed (no changes to Agent 5) |
| Component Factory Crew | Agent 20: Quality Scoring Agent | Read-only dependency — Agent 30 reads `quality-scorecard.json` to apply the 80% coverage threshold (§4.6); no changes to Agent 20 |

## PRD References

- **§4.6** — Governance Crew specification (5 agents, tasks T1–T5, outputs)
- **§3.6** — Crew I/O contracts (input: `pipeline-config.json`; outputs: `governance/*.json`, `docs/templates/`, `tests/*.test.ts`)
- **§3.4** — Retry protocol (max 2 retries per crew for Phases 4–6)
- **§3.8** — `pipeline-config.json` schema (input seed consumed by this crew)
- **§5** — Human gates (no new gates added; this crew runs unattended)
- **§8** — Exit criteria: Agent 30 generates the four test suites that encode 4 of the 8 Fatal checks (`tokens.test.ts`, `a11y.test.ts`, `composition.test.ts`, `compliance.test.ts`)

## Pipeline Impact

- [ ] Pipeline phase ordering
- [x] Crew I/O contracts (§3.6) — outputs `governance/ownership.json`, `governance/workflow.json`, `governance/deprecation-policy.json`, `governance/quality-gates.json`, `docs/templates/rfc-template.md`, `tests/tokens.test.ts`, `tests/a11y.test.ts`, `tests/composition.test.ts`, `tests/compliance.test.ts`
- [ ] Retry protocol (§3.4)
- [ ] Human gate policy (§5)
- [x] Exit criteria (§8) — Agent 30's test suites are what `npm test` runs to verify the 4 Fatal token/a11y/composition/compliance checks
- [ ] Brand Profile schema (§6)

## Approach

1. **Write agent tests first (TDD)**: For each of the 5 agents, create a test file that asserts the agent's CrewAI role, goal, tool list, and backstory before the agent module exists.
2. **Write tool tests**: For each new tool module, write unit tests covering happy-path output schema and edge cases before implementing.
3. **Implement tools**: Build each tool as a deterministic `BaseTool` subclass; tools do the work, agents orchestrate.
4. **Implement agents**: Each agent module follows the pattern established by `quality_scoring.py` — `create_<name>_agent(model, output_dir)` returning a `crewai.Agent`.
5. **Wire the crew**: Replace the `StubCrew` factory in `governance.py` with a `crewai.Crew` containing 5 `Task` objects in T1→T2→T3→T4→T5 order, reading `pipeline-config.json` as input seed.
6. **Validate outputs**: Run tests; confirm `governance/*.json` and `tests/*.test.ts` are non-stub after crew execution.

Agent 30 (Quality Gate Agent) depends on Phase 4a (Documentation Crew) having completed — enforced by Phase 4 ordering in the orchestrator (PRD §3.5). No changes to the orchestrator are needed; the ordering already exists.

## Risks

- **Quality Gate circular dependency**: Agent 30 checks "all components have docs," which requires Documentation Crew outputs. If the orchestrator does not strictly enforce Phase 4a before 4b, the gate will produce false negatives. Mitigation: add an assertion in the crew's pre-flight that verifies the `docs/` directory is non-empty before Task T5 runs.
- **Test suite generation**: The 4 generated TypeScript test files (`tokens.test.ts`, etc.) must be syntactically valid TypeScript. The `test_suite_generator.py` tool needs to emit well-formed output; a simple template approach is safer than freeform LLM generation for this.
- **Pipeline-config.json schema drift**: If Agent 5's output schema changes, Agent 26's domain classification logic will break. Mitigation: Agent 26 reads `pipeline-config.json` with a validated schema check and raises an explicit error on unexpected shape.
