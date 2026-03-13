# Specification

## Purpose

Define the behavioral requirements for the AI Semantic Layer Crew (Agents 41–45) implementation. This spec covers the five agents, their supporting tools, the crew factory, and the crew-level retry/failure contract as defined in PRD §4.9 and §3.4.

---

## Requirements

### Requirement: AI Semantic Layer Crew factory replaces stub

The `create_ai_semantic_layer_crew(output_dir)` function in `src/daf/crews/ai_semantic_layer.py` MUST return a `crewai.Crew` instance (not a `StubCrew`), configured with five agents and five tasks wired T1→T2→T3→T4→T5.

#### Acceptance Criteria

- [ ] `create_ai_semantic_layer_crew(output_dir)` returns an instance of `crewai.Crew`
- [ ] The returned crew has exactly 5 agents and 5 tasks
- [ ] Tasks are ordered T1→T5 with `context` chaining
- [ ] The function raises `RuntimeError` if no `*.spec.yaml` files exist in `<output_dir>/specs/`
- [ ] The `registry/` directory is created if it does not exist before any agent runs

#### Scenario: Factory returns a real crew

- GIVEN a valid `output_dir` containing a `specs/` directory with at least one `.spec.yaml` file
- WHEN `create_ai_semantic_layer_crew(output_dir)` is called
- THEN a `crewai.Crew` instance is returned
- AND the crew has 5 agents
- AND the crew has 5 tasks in order T1→T5

#### Scenario: Pre-flight guard fires with missing specs

- GIVEN an `output_dir` whose `specs/` directory is absent or empty
- WHEN `create_ai_semantic_layer_crew(output_dir)` is called
- THEN a `RuntimeError` is raised
- AND the error message references the missing `specs/*.spec.yaml` files

---

### Requirement: Agent 41 – Registry Maintenance

Agent 41 (Registry Maintenance Agent, AI Semantic Layer Crew) MUST read all canonical spec YAMLs and generated TSX source to produce a complete component registry at `registry/components.json`.

Tools used: `SpecIndexer`, `ExampleCodeGenerator`, `RegistryBuilder`.

#### Acceptance Criteria

- [ ] `create_registry_maintenance_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] The agent is configured with `SpecIndexer`, `ExampleCodeGenerator`, and `RegistryBuilder` tools
- [ ] `registry/components.json` is written after T1 completes and is valid JSON (not `{"stub": true}`)
- [ ] Each component entry MUST include: `name`, `props` (with `type` and `default`), `variants`, `states`, `slots`, `tokenBindings`, `a11yAttributes`, and `usageExamples`
- [ ] All components found in `specs/*.spec.yaml` are represented in the registry
- [ ] Primitive components from `src/primitives/*.tsx` are included alongside spec-defined components

#### Scenario: Registry built from spec and TSX sources

- GIVEN `specs/button.spec.yaml` defines a `Button` component with props `variant` and `disabled`
- AND `src/components/button/Button.tsx` exists
- WHEN Agent 41 runs T1
- THEN `registry/components.json` contains a `Button` entry with `props` including `variant` and `disabled`
- AND the entry includes at least one `usageExamples` entry

#### Scenario: No TSX source present (spec-only)

- GIVEN `specs/badge.spec.yaml` exists but `src/components/badge/` is absent
- WHEN Agent 41 runs T1
- THEN `registry/components.json` contains a `Badge` entry built from spec data only
- AND the entry has an empty `tokenBindings` array (no source to scan)

#### Scenario: Spec directory absent

- GIVEN the `specs/` directory does not exist in `output_dir`
- WHEN `create_ai_semantic_layer_crew(output_dir)` is called
- THEN a `RuntimeError` is raised before any agent runs

---

### Requirement: Agent 42 – Token Resolution

Agent 42 (Token Resolution Agent, AI Semantic Layer Crew) MUST traverse the compiled token graph to produce `registry/tokens.json` with resolved values, semantic tiers, and natural-language descriptions.

Tools used: `TokenGraphTraverser`, `SemanticMapper`.

#### Acceptance Criteria

- [ ] `create_token_resolution_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] The agent is configured with `TokenGraphTraverser` and `SemanticMapper` tools
- [ ] `registry/tokens.json` is written after T2 completes and is valid JSON (not `{"stub": true}`)
- [ ] Each token entry MUST include: `name`, `resolvedValue` per platform and theme, `tier` (global/semantic/component), `semanticPurpose`, `relatedTokens` (same category), and `description` (natural language)
- [ ] All tokens in `tokens/*.tokens.json` are represented in the registry
- [ ] The registry supports intent-based resolution (e.g. querying for "muted background" returns relevant semantic tokens)

#### Scenario: Token resolution with multi-theme values

- GIVEN `tokens/semantic.tokens.json` defines `color.background.subtle` with `$extensions` containing light and dark theme values
- WHEN Agent 42 runs T2
- THEN `registry/tokens.json` contains `color-background-subtle` with `resolvedValue.light` and `resolvedValue.dark` populated
- AND `tier` is set to `"semantic"`

#### Scenario: Empty token files

- GIVEN `tokens/` directory exists but all `*.tokens.json` files are empty objects
- WHEN Agent 42 runs T2
- THEN `registry/tokens.json` is written with an empty array
- AND no error is raised

#### Scenario: Global token references semantic token

- GIVEN `tokens/global.tokens.json` defines a base color `blue-500` referenced by `tokens/semantic.tokens.json` as `color.primary`
- WHEN Agent 42 runs T2
- THEN `registry/tokens.json` entry for `color-primary` shows `resolvedValue` as the hex value from `blue-500`
- AND `relatedTokens` includes other primary-tier tokens

---

### Requirement: Agent 43 – Composition Constraint

Agent 43 (Composition Constraint Agent, AI Semantic Layer Crew) MUST build `registry/composition-rules.json` defining allowed children, forbidden nesting, required slots, maximum depth, and example trees for every component.

Tools used: `CompositionRuleExtractor`, `TreeValidator`, `ExampleTreeGenerator` (via `CompositionRuleExtractor`).

#### Acceptance Criteria

- [ ] `create_composition_constraint_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] The agent is configured with `CompositionRuleExtractor` and `TreeValidator` tools
- [ ] `registry/composition-rules.json` is written after T3 completes and is valid JSON (not `{"stub": true}`)
- [ ] Each component entry MUST include: `allowedChildren`, `forbiddenNesting`, `requiredSlots`, `maxDepth`, `validExample`, and `invalidExample`
- [ ] If `reports/composition-audit.json` is absent, rules are derived from `specs/*.spec.yaml` without error
- [ ] All generated `validExample` trees MUST pass `TreeValidator` validation

#### Scenario: Composition rules from audit report

- GIVEN `reports/composition-audit.json` contains composition rules for `Card` restricting children to `Text`, `Button`, `Image`
- WHEN Agent 43 runs T3
- THEN `registry/composition-rules.json` entry for `Card` has `allowedChildren: ["Text", "Button", "Image"]`
- AND `invalidExample` demonstrates a forbidden nesting (e.g. nested `Card` inside `Card`)

#### Scenario: Fallback to spec when audit absent

- GIVEN `reports/composition-audit.json` does not exist
- AND `specs/modal.spec.yaml` defines `slots: [header, body, footer]`
- WHEN Agent 43 runs T3
- THEN `registry/composition-rules.json` entry for `Modal` has `requiredSlots: ["header", "body", "footer"]`
- AND no error is raised

#### Scenario: Valid example passes validation

- GIVEN `registry/composition-rules.json` contains a `validExample` for `Tabs`
- WHEN `TreeValidator` validates the example tree
- THEN it returns `valid: true` with no violations

---

### Requirement: Agent 44 – Validation Rule

Agent 44 (Validation Rule Agent, AI Semantic Layer Crew) MUST compile all compliance rules into `registry/compliance-rules.json` in an exportable format consumable by AI assistants and linters.

Tools used: `RuleCompiler`.

#### Acceptance Criteria

- [ ] `create_validation_rule_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] The agent is configured with the `RuleCompiler` tool
- [ ] `registry/compliance-rules.json` is written after T4 completes and is valid JSON (not `{"stub": true}`)
- [ ] The rules file MUST include rules from at least four categories: `tokenUsage`, `composition`, `accessibility`, `namingConventions`
- [ ] Each rule entry MUST include: `id`, `category`, `severity` (`error`/`warning`), `description`, and `rationale`
- [ ] Rules reference the component registry and token registry produced by T1–T3

#### Scenario: Token usage rule compilation

- GIVEN `registry/tokens.json` contains semantic tokens for `color` and `spacing`
- WHEN Agent 44 runs T4
- THEN `registry/compliance-rules.json` includes a rule with `category: "tokenUsage"` and `severity: "error"` forbidding hardcoded hex color values

#### Scenario: A11y rule from registry

- GIVEN `registry/components.json` defines `Button` with `a11yAttributes: ["aria-label", "aria-disabled"]`
- WHEN Agent 44 runs T4
- THEN `registry/compliance-rules.json` includes a rule requiring `aria-label` to be set on `Button` instances that lack visible text
- AND the rule has `severity: "error"` (WCAG AA requirement)

#### Scenario: Empty rule sources

- GIVEN `registry/components.json` and `registry/tokens.json` exist but contain empty arrays
- WHEN Agent 44 runs T4
- THEN `registry/compliance-rules.json` is written with an empty `rules` array
- AND no error is raised

---

### Requirement: Agent 45 – Context Serializer

Agent 45 (Context Serializer Agent, AI Semantic Layer Crew) MUST package the four registry files into `.cursorrules`, `copilot-instructions.md`, and `ai-context.json`, applying token-budget optimisation for IDE-facing formats.

Tools used: `ContextFormatter`, `TokenBudgetOptimizer`, `MultiFormatSerializer`.

#### Acceptance Criteria

- [ ] `create_context_serializer_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] The agent is configured with `ContextFormatter`, `TokenBudgetOptimizer`, and `MultiFormatSerializer` tools
- [ ] `.cursorrules` is written after T5 completes and is non-empty (not a stub placeholder)
- [ ] `copilot-instructions.md` is written after T5 completes and is valid Markdown
- [ ] `ai-context.json` is written after T5 completes and is valid JSON (not `{"stub": true}`)
- [ ] `.cursorrules` and `copilot-instructions.md` MUST NOT exceed 8000 tokens each (IDE context limit)
- [ ] `ai-context.json` contains the full untruncated registry data
- [ ] When truncation is applied to `.cursorrules`, low-signal usage examples are removed first, then slot descriptions, then internal props

#### Scenario: Serialization of Starter scope design system

- GIVEN `registry/components.json` contains 10 components (Starter scope)
- AND total registry size is within 8000 tokens
- WHEN Agent 45 runs T5
- THEN `.cursorrules` contains all 10 components with full metadata
- AND no truncation is applied

#### Scenario: Token budget overflow triggers optimisation

- GIVEN `registry/components.json` contains 25+ components (Comprehensive scope) totalling over 8000 tokens
- WHEN Agent 45 runs T5
- THEN `TokenBudgetOptimizer` removes usage examples first, then abbreviates descriptions
- AND the resulting `.cursorrules` fits within 8000 tokens
- AND `ai-context.json` retains the full untruncated content

#### Scenario: Missing upstream registry file

- GIVEN `registry/tokens.json` was not written by T2 (an upstream task failure)
- WHEN Agent 45 runs T5
- THEN the agent logs the missing file
- AND `.cursorrules`, `copilot-instructions.md`, and `ai-context.json` are written with available data only
- AND no unhandled exception is raised
