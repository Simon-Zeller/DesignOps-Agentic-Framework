# Proposal: p07-core-component-specs

## Intent

The DS Bootstrap Crew's Agent 4 (Core Component Agent, §4.1) is responsible for generating canonical spec YAMLs for every component in the scope tier selected by the user. No tool implementation or agent wiring for Agent 4 currently exists in the codebase. Without these specs, the Design-to-Code Crew (Phase 3) has no contract to generate TSX source from for any non-primitive component — Phase 3 cannot proceed for any Starter, Standard, or Comprehensive component.

This change delivers the Python infrastructure needed for Agent 4 to produce `*.spec.yaml` files for all components in a scope tier, plus the CrewAI agent wiring that connects Agent 4 into the DS Bootstrap Crew pipeline.

## Scope

### In scope

- A `CoreComponentSpecGenerator` CrewAI `BaseTool` that generates all component spec YAMLs for a given scope tier (Starter, Standard, or Comprehensive) into `specs/`
- Python spec definitions (dict constants) for all 10 Starter-tier components: Button, Input, Checkbox, Radio, Select, Card, Badge, Avatar, Alert, Modal
- Python spec definitions for the 9 additional Standard-tier components: Table, Tabs, Accordion, Tooltip, Toast, Dropdown, Pagination, Breadcrumb, Navigation
- Python spec definitions for the 6 additional Comprehensive-tier components introduced in §4.1: DatePicker, DataGrid, TreeView, Drawer, Stepper, FileUpload, RichText
- A `ComponentOverride` mechanism so that `componentOverrides` from the Brand Profile can patch per-component spec defaults before YAML is written
- `create_core_component_agent()` and `create_core_component_task()` factory functions in `src/daf/agents/core_component.py`, following the pattern established by `token_foundation.py` and `primitive_scaffolding.py`
- Export of new factories from `src/daf/agents/__init__.py`
- An `openspec/specs/core-component-specs/spec.md` capability spec defining required YAML fields, variant schema, state machine conventions, token binding rules, and a11y annotation requirements per component
- Test coverage following the TDD-first workflow: all tests red before implementation, green after

### Out of scope

- TSX code generation from the produced specs (Design-to-Code Crew, Phase 3)
- Wiring Agent 4 into a full `DSBootstrapCrew` class — crew assembly is deferred to a future change
- Validating the component specs against Token Engine output (Token Engine Crew, Phase 2)
- Any modifications to the existing primitive spec generator or the 9 primitive specs produced by p06

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| DS Bootstrap Crew | Agent 4: Core Component Agent | Primary target — new implementation |
| DS Bootstrap Crew | Agent 3: Primitive Scaffolding Agent | No code changes; specs produced by Agent 3 are a composition dependency referenced in all new component specs |
| Design-to-Code Crew | Agent 12: Scope Classification Agent | Unblocked: can now classify generation scope once component specs exist in `specs/` |
| Design-to-Code Crew | Agent 13: Intent Extraction Agent | Unblocked: can parse component spec YAMLs to extract structural intent |
| Design-to-Code Crew | Agent 14: Code Generation Agent | Unblocked for all Starter/Standard/Comprehensive components |
| Component Factory Crew | Agent 17: Spec Validation Agent | Directly consumes the new `*.spec.yaml` files for validation |
| Component Factory Crew | Agent 18: Composition Agent | Relies on `compositionRules` fields in the new specs to verify primitive usage |
| AI Semantic Layer Crew | Agent 41: Registry Maintenance | Component registry integrity requires all spec YAMLs to be present |

## PRD References

- §3.3 — Agentic vs. Deterministic decision log: code generation from specs is agentic, but spec authoring uses deterministic tool assistance
- §3.6 — DS Bootstrap Crew I/O contract: Bootstrap writes `specs/*.spec.yaml`; Design-to-Code reads them
- §4.1 — DS Bootstrap Crew, Agent 4: Core Component Agent goals, tools, scope tiers, and component list
- §4.3 — Design-to-Code Crew: Unblocked by presence of component specs
- §4.4 — Component Factory Crew: Spec Validation (Agent 17) and Composition (Agent 18) consume specs
- §4.7 — AI Semantic Layer Crew: Registry Maintenance (Agent 41) requires all specs present

## Pipeline Impact

- [ ] Pipeline phase ordering
- [x] Crew I/O contracts (§3.6) — DS Bootstrap Crew output `specs/*.spec.yaml` gains all component specs; downstream crews unblocked
- [ ] Retry protocol (§3.4)
- [ ] Human gate policy (§5)
- [ ] Exit criteria (§8)
- [ ] Brand Profile schema (§6)

## Approach

Follow the same pattern established by p06 (primitive spec generation):

1. **Define spec dict constants** for each tier's components. Each dict encodes: `component`, `description`, `props` (name/type/default/required), `variants` (list of variant names), `states` (interactive state machine), `tokenBindings` (DTCG alias-format references to semantic tokens), `compositionRules` (`composesFrom` primitives, `allowedChildren`, `forbiddenNesting`, `slots`), and `a11yRequirements` (`role`, `focusable`, `keyboardInteractions`, `ariaAttributes`).

2. **Implement `generate_component_specs(scope, overrides, output_dir)`** — a deterministic function that selects the correct component set for the scope tier, applies any `componentOverrides` from the Brand Profile, serializes each spec to YAML, and writes to `output_dir/specs/`. Returns a `dict[str, str]` mapping component name to absolute path.

3. **Wrap in `CoreComponentSpecGenerator(BaseTool)`** — a CrewAI tool so Agent 4 can invoke the generator. Tool input accepts `scope` (one of `starter | standard | comprehensive`) and an optional `component_overrides` JSON string.

4. **Implement Agent 4 module** (`src/daf/agents/core_component.py`) — `create_core_component_agent()` returns a `crewai.Agent` with role `"Core Component Agent"`, Tier 2 model (Claude Sonnet, per §3.7), and `tools=[CoreComponentSpecGenerator()]`. `create_core_component_task()` returns the corresponding `crewai.Task`.

5. **Write capability spec** at `openspec/specs/core-component-specs/spec.md` covering the YAML contract: required fields per component, variant naming conventions, token binding rules (semantic tier only, no global token refs), state machine constraints, a11y annotation requirements.

## Risks

- **Spec completeness vs. completeness-of-implementation trade-off:** Defining high-quality specs for 25+ components up front is a significant authoring effort. The risk is that specs are too generic (missing component-specific nuances) or too prescriptive (breaking Design-to-Code flexibility). Mitigation: use Starter-tier components as the validation target for p07; Standard and Comprehensive specs are included but only Starter tests are exhaustive.
- **Token binding accuracy:** Component token bindings must reference only valid semantic token keys — but the full semantic token namespace is not finalized until Token Engine Crew runs (Phase 2). The specs define *intent* bindings (e.g., `{color.interactive.primary}`) that must resolve against whatever the Token Foundation Agent generated. Mitigation: the capability spec defines a binding convention using stable semantic tier prefixes that Token Foundation Agent (p04) is already committed to producing.
- **componentOverrides complexity:** The Brand Profile supports per-component overrides (`componentOverrides` field). Implementing a general-purpose patch mechanism adds complexity. Mitigation: keep the override mechanism shallow — only allow overriding top-level spec fields (e.g., default variant, disabled states), not deep prop rewrites.
