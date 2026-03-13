# Specification: Scope Classification & Intent Extraction

## Purpose

Defines the behavioral requirements for Agent 12 (Scope Classification Agent) and Agent 13 (Intent Extraction Agent) in the Design-to-Code Crew. Covers component classification into generation tiers, dependency resolution, priority queue construction, and the extraction of structured intent manifests from canonical spec YAMLs.

---

## Requirements

### Requirement: Component spec discovery and classification

Agent 12 (Scope Classification Agent) in the Design-to-Code Crew MUST discover all component spec YAMLs in `specs/primitives/` and `specs/components/` and classify each component into one of three generation tiers: `primitive`, `simple`, or `complex`.

Classification rules:
- `primitive` — spec has no `variants` array and no `state` field, or is listed in the known primitives set (Box, Stack, HStack, VStack, Grid, Text, Icon, Pressable, Divider, Spacer, ThemeProvider).
- `complex` — spec has a `variants` array with 3+ entries OR has a `state` field with 2+ distinct named states OR is explicitly tagged `complexity: complex`.
- `simple` — all other components (has variants or state but below the complex threshold).

#### Acceptance Criteria

- [ ] Agent 12 discovers all `*.spec.yaml` files in `specs/primitives/` and `specs/components/` (recursive).
- [ ] Each discovered spec is classified as `primitive`, `simple`, or `complex` based on the classification rules.
- [ ] The classification result per component is recorded in the `scope_classifier_output` passed to Agent 13.
- [ ] If no spec files are found, Agent 12 raises a fatal error and the Design-to-Code Crew exits non-zero.
- [ ] If a spec file cannot be parsed (malformed YAML), Agent 12 logs a warning and skips that spec; it does not halt classification of remaining specs.

#### Scenario: Primitives spec set

- GIVEN `specs/primitives/` contains `box.spec.yaml`, `text.spec.yaml`, `pressable.spec.yaml`
- WHEN Agent 12 runs task T1
- THEN all three are classified as `primitive`
- AND they appear first in the priority queue

#### Scenario: Complex component detection

- GIVEN `specs/components/data-grid.spec.yaml` has a `variants` array with 5 entries
- WHEN Agent 12 runs task T1
- THEN `data-grid` is classified as `complex`

#### Scenario: No specs found

- GIVEN `specs/` directory is empty
- WHEN Agent 12 runs task T1
- THEN Agent 12 raises a fatal error with message "No spec YAMLs found in specs/"
- AND the Design-to-Code Crew exits non-zero

---

### Requirement: Dependency-ordered priority queue construction

Agent 12 (Scope Classification Agent) MUST build a dependency-ordered generation queue using `dependency_graph_builder.py` and `priority_queue_builder.py`. The queue MUST order components so that dependencies always appear before their dependants.

#### Acceptance Criteria

- [ ] The dependency graph is built from `allowedChildren` and `composedOf` fields in each spec.
- [ ] The generation queue is topologically sorted: no component appears before a component it depends on.
- [ ] Primitives always appear before simple components; simple appear before complex components, regardless of alphabetical order.
- [ ] Circular dependencies are detected by `dependency_graph_builder.py` and reported as a fatal error; the crew exits non-zero.
- [ ] The final priority queue is written to `scope_classifier_output.json` in the crew's working context.

#### Scenario: Correct primitive-first ordering

- GIVEN `button.spec.yaml` has `composedOf: [Pressable, Text]`
- AND both `pressable.spec.yaml` and `text.spec.yaml` exist as primitives
- WHEN Agent 12 builds the dependency queue
- THEN `Pressable` and `Text` appear before `Button` in the queue

#### Scenario: Circular dependency

- GIVEN `comp-a.spec.yaml` has `composedOf: [CompB]`
- AND `comp-b.spec.yaml` has `composedOf: [CompA]`
- WHEN Agent 12 calls `dependency_graph_builder.py`
- THEN a circular dependency error is raised identifying both components
- AND the Design-to-Code Crew exits non-zero

---

### Requirement: Structured intent manifest extraction per component

Agent 13 (Intent Extraction Agent) in the Design-to-Code Crew MUST produce a structured intent manifest for each component in the priority queue. The manifest MUST capture all fields required by Agent 14 for code generation.

Required manifest fields:
- `component_name` — canonical name from spec
- `tier` — `primitive` | `simple` | `complex`
- `layout` — extracted layout model (`flex`, `grid`, or `absolute`), direction, and alignment defaults
- `spacing` — spacing rhythm (scale steps used for padding/margin/gap)
- `breakpoints` — responsive breakpoint config if declared
- `variants` — list of variant names and their differentiating prop values
- `states` — list of interactive state names (hover, focus, disabled, active, loading, etc.)
- `slots` — named composition slots with allowed child types
- `aria` — extracted ARIA role, required attributes, and any conditional attributes per state
- `keyboard_handlers` — list of key events required (Tab, Enter, Escape, Arrow keys) per state
- `token_bindings` — map of CSS property → token reference path (e.g., `color` → `semantic.color.brand.primary`)
- `props` — all declared props with types and defaults

#### Acceptance Criteria

- [ ] For every component in the priority queue, Agent 13 produces one manifest dict with all required fields populated.
- [ ] Fields absent from the spec YAML are set to their documented defaults (e.g., `breakpoints: []` if not declared).
- [ ] Token bindings reference paths resolvable in `tokens/compiled/flat.json`; unresolvable bindings are flagged as warnings (not errors).
- [ ] All manifests are stored in `intent_manifests.json` in the crew's working context before T3 begins.
- [ ] If `tokens/compiled/flat.json` is absent, Agent 13 raises a fatal error (tokens must be compiled before Phase 3).

#### Scenario: Full manifest for a Button component

- GIVEN `button.spec.yaml` declares `variants: [primary, secondary, ghost]`, `states: [hover, focus, disabled]`, `composedOf: [Pressable, Text]`, and token bindings for bg-color and text-color
- WHEN Agent 13 processes the Button intent
- THEN the manifest contains `variants: [primary, secondary, ghost]`, `states: [hover, focus, disabled]`, `slots: [{name: children, allowedTypes: [Text]}]`, and `token_bindings: {background-color: semantic.color.btn.bg, color: semantic.color.btn.text}`

#### Scenario: Missing token binding reference

- GIVEN a spec declares `token: semantic.color.btn.nonexistent`
- AND this key does not exist in `tokens/compiled/flat.json`
- WHEN Agent 13 extracts intent
- THEN the unresolvable binding is added to `manifest.token_warnings`
- AND extraction continues (not a fatal error)

#### Scenario: Absent compiled tokens

- GIVEN `tokens/compiled/flat.json` does not exist
- WHEN Agent 13 runs task T2
- THEN Agent 13 raises a fatal error: "Compiled tokens not found — ensure Token Engine Crew has completed"
- AND the Design-to-Code Crew exits non-zero
