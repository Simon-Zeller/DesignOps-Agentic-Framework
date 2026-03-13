## Context

The `primitive_spec_generator.py` module currently contains a single function, `generate_theme_provider_spec()`, which writes one hardcoded `ThemeProvider.spec.yaml`. This was a targeted delivery from p05 (theming model) to unblock the Design-to-Code Crew for ThemeProvider specifically.

Agent 3 (Primitive Scaffolding Agent, DS Bootstrap Crew, §3.3) is responsible for Task T3: Author primitive specs. Its contract is to write canonical `specs/*.spec.yaml` files for all 9 composition primitives before Phase 3 begins. Currently, 8 of 9 required spec files are missing, which means the Design-to-Code Crew (Phase 3) cannot generate any primitive beyond ThemeProvider.

The `PrimitiveSpecGenerator` is listed in the PRD as Agent 3's tool ("Primitive Spec Template Library, Token Binding Schema"), but it is not yet wired into `agents/token_foundation.py` or any crew Task T3 definition.

**Current state summary:**
- `generate_theme_provider_spec()` exists; produces one spec YAML
- No spec YAMLs for Box, Stack, HStack, VStack, Grid, Text, Icon, Pressable, Divider, Spacer
- No `PrimitiveSpecGenerator` CrewAI Tool class
- Agent 3 Task T3 not yet wired (`brand_discovery.py` and `token_foundation.py` cover Agents 1–2 only)

## Goals / Non-Goals

**Goals:**
- Add spec definitions for all 8 remaining primitives (Box, Stack/HStack/VStack, Grid, Text, Icon, Pressable, Divider, Spacer) in `primitive_spec_generator.py`
- Introduce `generate_all_primitive_specs(output_dir)` as the single entry point for producing all 9 `specs/*.spec.yaml` files
- Wrap the generator as a `PrimitiveSpecGenerator` CrewAI `BaseTool` subclass, making it callable from Agent 3's Task T3
- Add Agent 3 and its Task T3 to the DS Bootstrap Crew in a new `agents/primitive_scaffolding.py` module (or extend the existing one)
- Achieve full test coverage for all 9 spec outputs

**Non-Goals:**
- Generating component specs (Agent 4, p07) — only the 9 primitives are in scope
- Validating token binding key resolution at generation time — deferred to Token Validation Agent 7 (Phase 2)
- Code generation (Design-to-Code Crew, Phase 3)
- ThemeProvider behavior changes — spec content from p05 is not modified; `_THEME_PROVIDER_SPEC` dict is reused as-is

## Decisions

### 1. Deterministic tool, no LLM involvement

**Decision:** `primitive_spec_generator.py` remains fully deterministic (no LLM calls). All 9 primitive specs are hardcoded Python dicts.

**Rationale:** Primitive specs encode structural contracts — props, token binding keys, composition rules — that are well-defined by the PRD and design system architecture. There is no ambiguity that benefits from LLM reasoning at generation time. The PRD assigns LLM reasoning to agent-level decisions; tools are explicitly deterministic.

**Alternative considered:** LLM-assisted spec generation (Haiku) to auto-fill token binding key names from a running token namespace. Rejected: introduces non-determinism, adds latency, and creates a coupling between Phase 1 spec generation and Phase 2 token validation that the architecture explicitly avoids.

### 2. Single `generate_all_primitive_specs(output_dir)` entry point

**Decision:** One function generates all 9 specs. It overwrites any existing file (idempotent). Returns a `dict[str, str]` mapping component names to absolute output paths.

**Rationale:** Agent 3's Task T3 is a single atomic task ("Author primitive specs"). A single function invocation matches the task granularity and keeps the CrewAI Tool implementation simple. Individual generators remain private (`_generate_box_spec()`, etc.) for testability.

**Alternative considered:** Separate public functions per primitive (matching the p05 pattern). Rejected: creates a fragile tool with 9 entry points. The CrewAI tool would need a parameter to select which primitives to generate, adding complexity without benefit.

### 3. Token binding key format

**Decision:** Token binding values use the W3C DTCG alias format: `{"$value": "{semantic.color.surface.default}"}`. Keys reference semantic-tier tokens only. No global-tier tokens (`color.primary.500`) are referenced directly in primitive specs.

**Rationale:** Consistent with the key architectural pattern: "Components consume only semantic tokens — never global tokens directly" (§3.3). This is enforced at runtime by Token Compliance Agent 32; the spec must express the same constraint.

**Alternative considered:** Inline resolved values (`#FFFFFF`) as placeholders. Rejected: defeats the entire token-first architecture and would create broken references in the Design-to-Code Crew's input.

### 4. ThemeProvider spec reuse

**Decision:** `_THEME_PROVIDER_SPEC` dict from p05 is reused without modification. `generate_all_primitive_specs()` calls `generate_theme_provider_spec()` internally for the ThemeProvider entry.

**Rationale:** Avoids duplication, preserves the existing tested contract from p05. The spec content is correct per the theme-provider spec.

### 5. CrewAI Tool implementation: `BaseTool` subclass

**Decision:** `PrimitiveSpecGenerator` extends `crewai.tools.BaseTool`. The `_run()` method accepts an optional `output_dir` string argument and calls `generate_all_primitive_specs()`.

**Rationale:** Consistent with the project's existing CrewAI tool pattern (see `src/daf/tools/`). `BaseTool` provides schema validation, error wrapping, and compatibility with Agent task wiring.

### 6. Module placement

**Decision:** Agent 3 implementation lives in a new `src/daf/agents/primitive_scaffolding.py` module. The `PrimitiveSpecGenerator` `BaseTool` class lives in `src/daf/tools/primitive_spec_generator.py` alongside the existing generator functions.

**Rationale:** Follows the established pattern: `agents/brand_discovery.py` for Agent 1, `agents/token_foundation.py` for Agent 2. Agent 3 gets its own module.

## Risks / Trade-offs

**[Risk] Token binding key drift** — If Token Foundation Agent (Agent 2) changes its output token namespace, hardcoded binding keys in primitive specs will become phantom references.
→ **Mitigation:** Token binding keys are validated by the Token Validation Agent (Agent 7) in Phase 2. The retry protocol feeds failures back to Agent 3 via structured rejections (max 3 retries). No compile-time validation is added here — it would couple Phase 1 to Phase 2's namespace.

**[Risk] ThemeProvider spec divergence** — A future change to `theme-provider` spec requirements would require updates in two places: `_THEME_PROVIDER_SPEC` dict and the `specs/theme-provider/spec.md`.
→ **Mitigation:** Accepted. The spec YAML is the authoritative source for code generation; the `openspec/specs/` files are design-time contracts. A future p-change modifying ThemeProvider requirements would update both in the same diff.

**[Risk] Overwriting an existing `ThemeProvider.spec.yaml`** — If p05 already produced a `ThemeProvider.spec.yaml` in an output directory, calling `generate_all_primitive_specs()` will silently overwrite it.
→ **Mitigation:** Overwrite is intentional and correct — deterministic generation is idempotent. The spec content is identical (same dict, no change from p05). Document this as expected behavior in the function docstring.

**[Trade-off] Hardcoded primitive specs vs. template-driven generation** — Hardcoding 9 dict constants means future primitive additions require code changes.
→ **Accepted:** The primitive set is architecturally fixed at 9 (plus ThemeProvider). The PRD defines no extensibility mechanism for primitives. A template system would be over-engineering.

## Data Flow

```
Brand Profile JSON (output of Agent 1)
        │
        ▼
Agent 3: Primitive Scaffolding Agent (DS Bootstrap Crew, Task T3)
  └── Tool: PrimitiveSpecGenerator (deterministic)
        └── generate_all_primitive_specs(output_dir="<run_dir>")
              ├── specs/Box.spec.yaml
              ├── specs/Stack.spec.yaml
              ├── specs/HStack.spec.yaml
              ├── specs/VStack.spec.yaml
              ├── specs/Grid.spec.yaml
              ├── specs/Text.spec.yaml
              ├── specs/Icon.spec.yaml
              ├── specs/Pressable.spec.yaml
              ├── specs/Divider.spec.yaml
              ├── specs/Spacer.spec.yaml
              └── specs/ThemeProvider.spec.yaml
                          │
                          ▼
            Design-to-Code Crew (Phase 3, Agent 13+)
              reads specs/*.spec.yaml → generates src/primitives/*.tsx
```

Agent 3 runs after Task T2 (Token Foundation, Agent 2) completes. Token binding keys in the generated specs reference the semantic token namespace that Agent 2 has written to `tokens/semantic.tokens.json`. No inline validation — Phase 2 (Token Engine Crew) performs the reference integrity check.

## Open Questions

- None.  Agent 3's scope, tool contract, and output format are fully defined by PRD §3.3 and the token-first architecture constraints already established in p04/p05.
