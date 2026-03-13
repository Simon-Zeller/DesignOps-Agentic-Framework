## Why

The `PrimitiveSpecGenerator` tool currently generates a single `ThemeProvider.spec.yaml` (delivered by p05). The DS Bootstrap Crew's Agent 3 (Primitive Scaffolding Agent, §3.3) must generate canonical spec YAMLs for the **complete set of 9 composition primitives** — Box, Stack (HStack/VStack), Grid, Text, Icon, Pressable, Divider, Spacer, and ThemeProvider — before the Design-to-Code Crew (Phase 3) can produce any TSX source. Without these specs, the Design-to-Code Crew has no contract to generate from and Phase 3 cannot begin. This change delivers the full primitive spec set and the agent wiring required to produce it.

## What Changes

- **New**: `generate_all_primitive_specs()` function in `primitive_spec_generator.py` — orchestrates generation of all 9 primitive spec YAMLs to `specs/` in a single call
- **New**: Individual spec definitions for Box, Stack (HStack/VStack), Grid, Text, Icon, Pressable, Divider, and Spacer — each with props, token bindings, composition rules, and a11y requirements aligned with the PRD §3.3
- **New**: `PrimitiveSpecGenerator` CrewAI tool class wrapping `generate_all_primitive_specs()` — makes the bulk generator callable by Agent 3 (Task T3)
- **Modified**: Agent 3 (`DS Bootstrap Crew`) wiring — Task T3 switches from the single `generate_theme_provider_spec` invocation to `PrimitiveSpecGenerator` tool for the full set
- **New**: Formal spec for the `primitive-spec-generation` capability covering required fields, token binding rules, composition constraints, and a11y annotation requirements per primitive

## Capabilities

### New Capabilities

- `primitive-spec-generation`: Rules and acceptance criteria for how `PrimitiveSpecGenerator` generates all 9 primitive spec YAMLs — required YAML fields, token binding conventions, composition rules format, a11y requirement annotations, and the `generate_all_primitive_specs()` contract

### Modified Capabilities

- `token-foundation-agent`: No requirement changes — token binding references used in primitive specs must resolve against the global/semantic token namespace established by Agent 2; spec documents this constraint explicitly

## Impact

- **DS Bootstrap Crew — Agent 3** (Task T3): Primary implementation target; switches to `PrimitiveSpecGenerator` tool
- **Design-to-Code Crew** (Agents 13–16, §3.5): All downstream code generation unblocked once all 9 spec YAMLs exist in `specs/`
- **Component Factory Crew** (Agents 17–20): Composition Validation Agent (19) relies on the primitive registry encoded in these specs to verify that components compose from primitives correctly
- **AI Semantic Layer** (Agent 41, Registry Maintenance): Primitive spec YAMLs are a direct input to the component registry — all 9 must be present for registry integrity
- **No breaking changes** to existing crew I/O contracts; `specs/` output gains 8 new files (ThemeProvider.spec.yaml already exists), all additive
- **Exit criteria**: Fatal check 5 (CSS/token references resolve) indirectly affected — primitive specs must reference only valid global/semantic token keys; no change to check count or severity classification
