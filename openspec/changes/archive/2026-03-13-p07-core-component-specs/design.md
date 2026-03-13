# Design: p07-core-component-specs

## Technical Approach

The DS Bootstrap Crew's Agent 4 (Core Component Agent) needs a deterministic tool that serializes canonical component spec YAMLs for a given scope tier, wrapped in a CrewAI `BaseTool` so the agent can invoke it as part of Task T4. The implementation mirrors the pattern established by p06 (`primitive_spec_generator.py` + `primitive_scaffolding.py`):

1. **Spec dict constants** — Python dicts encoding the full spec contract for each of the 25+ components across all three scope tiers. These live in a new `src/daf/tools/core_component_spec_generator.py` module.
2. **`generate_component_specs(scope, output_dir, component_overrides)`** — a deterministic function that selects the component set for the requested scope tier, applies any Brand Profile `componentOverrides`, serializes each spec to YAML, and writes to `output_dir/specs/`. Returns `dict[str, str]` mapping component name → absolute path.
3. **`CoreComponentSpecGenerator(BaseTool)`** — CrewAI tool wrapper. The `_run()` method accepts `scope` and `component_overrides_json` arguments, calls `generate_component_specs()`, and returns a human-readable summary string.
4. **Agent 4 module** — `src/daf/agents/core_component.py` with `create_core_component_agent()` and `create_core_component_task()` factories, following the pattern of `token_foundation.py` and `primitive_scaffolding.py`.
5. **Capability spec** — `openspec/specs/core-component-specs/spec.md` documents the YAML contract that all generated component specs must conform to.

**Scope tier composition:**
- `starter` → 10 components (Button, Input, Checkbox, Radio, Select, Card, Badge, Avatar, Alert, Modal)
- `standard` → Starter + 9 more (Table, Tabs, Accordion, Tooltip, Toast, Dropdown, Pagination, Breadcrumb, Navigation)
- `comprehensive` → Standard + 7 more (DatePicker, DataGrid, TreeView, Drawer, Stepper, FileUpload, RichText)

Each component spec dict encodes: `component`, `description`, `props`, `variants`, `states`, `tokenBindings`, `compositionRules` (including `composesFrom` primitives), and `a11yRequirements`.

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| Component spec dict definitions | **Deterministic** | Spec contracts are well-defined by the PRD and design system architecture. No ambiguity that benefits from LLM reasoning. |
| YAML serialization and file I/O | **Deterministic** | Pure data transformation. |
| Scope tier selection | **Deterministic** | Controlled by Brand Profile `scope` field. No reasoning needed — it is a direct lookup. |
| `componentOverrides` patching | **Deterministic** | Shallow field-level patch applied before serialization. No inference. |
| Agent 4 task orchestration (deciding when to invoke the tool, what scope to pass) | **Agent (Tier 2 Sonnet)** | Agent reads the validated Brand Profile and decides scope + overrides. Deterministic tool executes the actual generation. |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Agent 4: Core Component Agent | Tier 2 — Analytical | `claude-sonnet-4-20250514` (default), overridable via `DAF_TIER2_MODEL` | Agent reads Brand Profile and decides scope + overrides. Analytical (Tier 2) is appropriate — no large code generation, just structured decision-making. Consistent with §3.7 Tier 2 assignment rationale. |

## Architecture Decisions

### Decision: Deterministic tool, no LLM involvement in spec generation

**Context:** Component specs encode structural contracts — props, variants, state machines, token bindings, composition rules — that are fully specified by the PRD for each component. Agent 4's role is to produce these contracts, not to invent them.

**Decision:** `core_component_spec_generator.py` is fully deterministic. All component spec dicts are hardcoded Python constants. The LLM (Agent 4) decides *which* tool invocation to make (scope, overrides) and interprets the result, but never authors spec content.

**Consequences:** Spec content is auditable, testable, and version-controllable as Python source. Token binding key names must be expressed as stable semantic-tier aliases (enforced by convention, validated by Token Validation Agent in Phase 2).

---

### Decision: Scope-accumulative tier model

**Context:** The three scope tiers share components. Standard adds to Starter; Comprehensive adds to Standard. No component appears in multiple tier-delta sets.

**Decision:** Internal implementation uses three lists: `STARTER_COMPONENTS` (10), `STANDARD_DELTA` (9), `COMPREHENSIVE_DELTA` (7). `generate_component_specs(scope)` accumulates: `comprehensive` = all three lists; `standard` = first two; `starter` = first list only. Avoids duplicating spec dicts across tier constants.

**Consequences:** Adding a future Comprehensive-delta component requires adding one dict to `COMPREHENSIVE_DELTA` only. Existing Starter/Standard specs are never touched for tier-expansion changes.

---

### Decision: `componentOverrides` as a shallow patch

**Context:** The Brand Profile supports a `componentOverrides` field (§4.1) allowing per-component design decisions (e.g., override default variant, disable states, change border-radius token binding).

**Decision:** `component_overrides` is a `dict[str, dict]` where keys are component names and values are top-level field patches. The patch is applied with `spec_dict.update(override_dict)` — a shallow merge. Deep-key merging (e.g., overriding a specific prop within `props`) is not supported in this change.

**Consequences:** Simple overrides (default variant, disabled state flag) work. Complex overrides (replacing a single prop within a multi-prop array) require a future change. Documented as a known limitation in the capability spec.

---

### Decision: One module per abstraction layer (tool vs. agent)

**Context:** `primitive_spec_generator.py` contains both the spec dicts/functions and the `PrimitiveSpecGenerator` BaseTool class. This keeps the file long but cohesive.

**Decision:** Follow the same file structure for p07: `core_component_spec_generator.py` holds the spec constants, `generate_component_specs()`, and `CoreComponentSpecGenerator(BaseTool)`. Agent-layer code (`create_core_component_agent()`, `create_core_component_task()`) lives in `agents/core_component.py`.

**Consequences:** Consistent with established project patterns. A future refactor separating tool logic from generation functions is not blocked by this layout.

---

### Decision: Token binding key format (semantic tier only)

**Context:** The PRD is explicit: "Components consume only semantic tokens — never global tokens directly" (§3.3, §3.5). The Token Compliance Agent (32) enforces this at Phase 5.

**Decision:** All `tokenBindings` in component spec dicts reference semantic-tier DTCG alias keys only (e.g., `{color.interactive.primary.default}`, `{spacing.component.padding.md}`). No global-tier keys (e.g., `{color.blue.500}`) appear in any component spec.

**Consequences:** The binding keys must align with the semantic token namespace produced by the Token Foundation Agent. The Token Validation Agent (8) validates this in Phase 2. The retry protocol feeds failures back to Agent 4 via structured rejections if bindings don't resolve.

## Data Flow

```
Brand Profile JSON (validated by Agent 1)
          │  scope, componentOverrides
          ▼
Agent 4: Core Component Agent (DS Bootstrap Crew, Task T4)
  — Reads Brand Profile for scope tier and componentOverrides
  — Invokes: CoreComponentSpecGenerator tool (deterministic)
          │
          ▼
generate_component_specs(scope, output_dir, component_overrides)
  ├── specs/Button.spec.yaml
  ├── specs/Input.spec.yaml
  ├── specs/Checkbox.spec.yaml
  ├── specs/Radio.spec.yaml
  ├── specs/Select.spec.yaml
  ├── specs/Card.spec.yaml
  ├── specs/Badge.spec.yaml
  ├── specs/Avatar.spec.yaml
  ├── specs/Alert.spec.yaml
  ├── specs/Modal.spec.yaml          ← always (starter+)
  ├── specs/Table.spec.yaml
  ├── specs/Tabs.spec.yaml
  ├── ...                            ← standard+ (9 more)
  ├── specs/DatePicker.spec.yaml
  └── ...                            ← comprehensive+ (7 more)
          │
          ▼
[DS Bootstrap Crew output folder] specs/*.spec.yaml
          │
          ├──► Design-to-Code Crew (Phase 3)
          │      Agent 12: Scope Classification
          │      Agent 13: Intent Extraction
          │      Agent 14: Code Generation
          │
          ├──► Component Factory Crew (Phase 3)
          │      Agent 17: Spec Validation
          │      Agent 18: Composition Validation
          │
          └──► AI Semantic Layer Crew (Phase 5)
                 Agent 41: Registry Maintenance
```

## Retry & Failure Behavior

Agent 4 is a Phase 1 agent (DS Bootstrap Crew). Per §3.4, retry at this phase boundary is managed by the First Publish Agent (6). If the component specs fail validation in Phase 2 (Token Validation Agent 8 reports unresolved token binding references):

1. Token Validation Agent produces a structured rejection listing which binding keys in which component specs failed to resolve.
2. First Publish Agent feeds the rejection back to Agent 4 as additional context (appended to the original Task T4 description).
3. Agent 4 re-invokes `CoreComponentSpecGenerator` with updated `component_overrides` to patch the failing binding keys. (Since token keys are hardcoded in the tool, the agent must pass override values that replace the failing keys.)
4. Maximum **3 retry attempts** per the retry protocol (§3.4). After 3 failures, the component is marked `failed` in the generation report.

**Tool-level failure:** `generate_component_specs()` raises `ValueError` if `scope` is not one of `starter | standard | comprehensive`. The CrewAI `BaseTool` wrapper catches this and returns the error message as the tool output string, allowing the agent to self-correct on the next attempt.

**Idempotency:** Calling `generate_component_specs()` twice with the same arguments overwrites existing YAML files. This is intentional — deterministic generation must be idempotent. Documented in function docstring.

## File Changes

- `src/daf/tools/core_component_spec_generator.py` (new) — spec dict constants for all 25+ components, `generate_component_specs()` function, `CoreComponentSpecGenerator(BaseTool)` class
- `src/daf/agents/core_component.py` (new) — `create_core_component_agent()` and `create_core_component_task()` factory functions
- `src/daf/agents/__init__.py` (modified) — export `create_core_component_agent` and `create_core_component_task`
- `src/daf/tools/__init__.py` (modified) — export `CoreComponentSpecGenerator` and `generate_component_specs`
- `tests/test_core_component_spec_generator.py` (new) — unit tests for the generator function and all spec dicts
- `tests/test_core_component_agent.py` (new) — unit tests for the CrewAI tool and Agent 4 module
- `openspec/specs/core-component-specs/spec.md` (new) — capability spec for the component YAML contract
