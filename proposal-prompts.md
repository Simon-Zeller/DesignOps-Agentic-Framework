# DAF Local — Proposal Prompts

> Ready-to-use prompts for `openspec propose` (or `/opsx:propose`).
> Execute in order — each proposal builds on the ones before it.
> Copy-paste a prompt directly into the proposal workflow.

---

## Quick Reference — Commands

For each proposal, run these two steps:

**Step 1 — Create the proposal** (paste the prompt text from the corresponding section below):
```
/opsx:propose
```

**Step 2 — Fast-forward through all remaining artifacts** (specs → design → tdd → tasks):
```
/opsx:ff
```

### Full Command List

| # | Change Name | Step 1: Propose | Step 2: Fast-forward |
|---|-------------|-----------------|----------------------|
| P01 | `p01-project-foundation` | `/opsx:propose p01-project-foundation` | `/opsx:ff p01-project-foundation` |
| P02 | `p02-interview-cli` | `/opsx:propose p02-interview-cli` | `/opsx:ff p02-interview-cli` |
| P03 | `p03-brand-discovery-agent` | `/opsx:propose p03-brand-discovery-agent` | `/opsx:ff p03-brand-discovery-agent` |
| P04 | `p04-token-foundation-agent` | `/opsx:propose p04-token-foundation-agent` | `/opsx:ff p04-token-foundation-agent` |
| P05 | `p05-theming-model` | `/opsx:propose p05-theming-model` | `/opsx:ff p05-theming-model` |
| P06 | `p06-primitive-spec-generation` | `/opsx:propose p06-primitive-spec-generation` | `/opsx:ff p06-primitive-spec-generation` |
| P07 | `p07-core-component-specs` | `/opsx:propose p07-core-component-specs` | `/opsx:ff p07-core-component-specs` |
| P08 | `p08-pipeline-config` | `/opsx:propose p08-pipeline-config` | `/opsx:ff p08-pipeline-config` |
| P09 | `p09-pipeline-orchestrator` | `/opsx:propose p09-pipeline-orchestrator` | `/opsx:ff p09-pipeline-orchestrator` |
| P10 | `p10-token-engine-crew` | `/opsx:propose p10-token-engine-crew` | `/opsx:ff p10-token-engine-crew` |
| P11 | `p11-design-to-code-crew` | `/opsx:propose p11-design-to-code-crew` | `/opsx:ff p11-design-to-code-crew` |
| P12 | `p12-component-factory-crew` | `/opsx:propose p12-component-factory-crew` | `/opsx:ff p12-component-factory-crew` |
| P13 | `p13-documentation-crew` | `/opsx:propose p13-documentation-crew` | `/opsx:ff p13-documentation-crew` |
| P14 | `p14-governance-crew` | `/opsx:propose p14-governance-crew` | `/opsx:ff p14-governance-crew` |
| P15 | `p15-analytics-crew` | `/opsx:propose p15-analytics-crew` | `/opsx:ff p15-analytics-crew` |
| P16 | `p16-ai-semantic-layer-crew` | `/opsx:propose p16-ai-semantic-layer-crew` | `/opsx:ff p16-ai-semantic-layer-crew` |
| P17 | `p17-release-crew` | `/opsx:propose p17-release-crew` | `/opsx:ff p17-release-crew` |
| P18 | `p18-retry-rollback-checkpoints` | `/opsx:propose p18-retry-rollback-checkpoints` | `/opsx:ff p18-retry-rollback-checkpoints` |
| P19 | `p19-exit-criteria` | `/opsx:propose p19-exit-criteria` | `/opsx:ff p19-exit-criteria` |

> **Workflow per proposal:**
> 1. `/opsx:propose <name>` — paste the prompt from below, creates the proposal artifact
> 2. `/opsx:ff <name>` — generates specs, design, tdd, and tasks in one shot
> 3. `/opsx:apply <name>` — implement the tasks (code gets written, branch merged, feature branch deleted local + remote)
> 4. `/opsx:archive <name>` — seal the change

---

## Dependency Map

```
P01 → P02 → P03
               ↘
P01 → P04 → P05 → P06 → P07 → P08
                              ↘
                          P09 (orchestrator, depends on all Bootstrap agents)
                               ↓
                              P10 (Token Engine)
                               ↓
                         P11 → P12 (Design-to-Code → Component Factory)
                               ↓
                         P13 → P14 (Documentation → Governance)
                               ↓
                         P15 → P16 (Analytics → AI Semantic Layer)
                               ↓
                              P17 (Release Crew)
                               ↓
                              P19 (Exit Criteria)

Cross-cutting (integrate after P09):
  P18 (Retry Protocol + Rollback + Checkpoints)
```

---

## P01 — Project Foundation & CLI Scaffolding

```
Implement the foundational Python project structure for DAF Local.

What to build:
- Python project with pyproject.toml (or equivalent) declaring CrewAI, Anthropic SDK, and CLI dependencies
- Main CLI entry point (`daf` command) using a CLI framework (e.g., Click or Typer)
- `daf init` command stub that will later host the interactive interview
- `daf init --profile <path>` flag for non-interactive mode (§13.5)
- `daf init --resume <path>` flag for resuming interrupted runs (§13.1)
- Basic project layout: src/daf/ with __init__.py, cli.py, and empty crew/agent/tool directories
- README with setup instructions

PRD References: §13.1 (Invocation), §9 (Tech Stack — CrewAI, Python, Anthropic)

Scope:
- IN: Project scaffolding, CLI entry point with subcommand routing, dependency declarations
- OUT: Interview logic (P02), agent implementations, CrewAI crew definitions

This is the skeleton that everything else plugs into.
```

---

## P02 — Interview CLI

```
Implement the interactive terminal interview that collects brand information from the user.

What to build:
- 11-step sequential interview flow as defined in §13.2:
  1. Project name (required)
  2. Archetype selection — present 5 options: Enterprise B2B, Consumer B2C, Mobile-First, Multi-Brand, Custom (required)
  3. Colors — primary, secondary, neutral, semantic (success/warning/error/info)
  4. Typography — fontFamily, headingFontFamily, scaleRatio, baseSize
  5. Spacing — baseUnit, density (compact/default/spacious)
  6. Visual style — borderRadius, elevation, motion
  7. Themes — modes, default, brands (if multi-brand)
  8. Accessibility — AA or AAA
  9. Component scope — starter, standard, comprehensive
  10. Breakpoints — strategy, count
  11. Component overrides (advanced, optional)
- For non-required steps: show the archetype-derived default, allow Enter to accept or override
- Accept both hex values (#1a73e8) and natural language descriptions ("a professional blue") for colors
- Input validation per §13.3: non-empty required fields, valid hex, scaleRatio 1.0–2.0, baseSize 8–24, valid archetype
- Session persistence: write .daf-session.json after each step, detect on re-run and offer resume (§13.3)
- Output: write raw brand-profile.json conforming to §6 schema
- Non-interactive mode: `daf init --profile ./path.json` skips interview, passes file directly (§13.5)

PRD References: §13 (full section), §6 (Brand Profile Schema), §4.1 (DS Archetypes)

Scope:
- IN: Interactive Q&A flow, input validation, session persistence, file output, --profile bypass
- OUT: Brand Profile validation/enrichment (that's Agent 1 in P03), archetype default resolution logic (P03)

The CLI is deliberately "dumb" — all intelligence (contradiction detection, enrichment, defaults) lives in the Brand Discovery Agent.
```

---

## P03 — Brand Discovery Agent

```
Implement Agent 1 (Brand Discovery Agent) from the DS Bootstrap Crew.

What to build:
- CrewAI Agent definition with role "Brand profile validator and enricher"
- Tools:
  - Brand Profile Schema Validator — validate against §6 JSON schema
  - Archetype Resolver — resolve archetype selection into concrete defaults for unspecified fields per §4.1 archetypes:
    - Enterprise B2B: conservative palette, readable type scale, dense layouts, comprehensive scope, AA
    - Consumer B2C: vibrant palette, expressive type scale, spacious layouts, standard scope, AA
    - Mobile-First: compact density, touch-optimized spacing, limited breakpoints, starter scope, AAA
    - Multi-Brand: neutral base + brand override layers, standard scope, all themes, AA
    - Custom: no defaults — all fields required
  - Consistency Checker — detect contradictions (e.g., "compact density" + "spacious spacing")
  - Default Filler — fill sensible defaults for any unspecified optional fields
- Input: raw brand-profile.json from interview CLI (P02)
- Output: validated, enriched brand-profile.json
- Human Gate: pause for user approval of finalized Brand Profile before generation begins (§5)
- Model tier: Tier 2 — Sonnet (§3.7, analytical reasoning, not large code generation)

PRD References: §4.1 (Agent 1 spec), §5 (Human Gate Policy — Brand Profile Approval), §6 (Brand Profile Schema), §3.7 (Model Assignment)

Scope:
- IN: Agent definition, all 4 tools, validation logic, enrichment logic, human gate integration
- OUT: Token generation (P04), spec generation (P06), pipeline config (P08)

This agent is the gatekeeper — nothing generates until the Brand Profile passes through it and receives human approval.
```

---

## P04 — Token Foundation Agent

```
Implement Agent 2 (Token Foundation Agent) from the DS Bootstrap Crew.

What to build:
- CrewAI Agent definition with role "Initial token set generator"
- Generate the complete initial token set from the validated Brand Profile:
  - Color palette: primitive tier (raw palette) + semantic tier (purpose-mapped colors) with automatic contrast-safe pairing
  - Typography scale: modular scale calculated from brand type preferences (scaleRatio, baseSize, fontFamily)
  - Spacing scale: based on baseUnit (4px or 8px grid) and density setting
  - Elevation/shadow scale: mapped from elevation preference (flat/subtle/layered)
  - Border radius scale: mapped from borderRadius preference (none/subtle/moderate/rounded/pill)
  - Motion/easing curves: mapped from motion preference (none/reduced/standard/expressive)
  - Breakpoint definitions: from strategy and count
  - Opacity scale
- All three tiers in W3C DTCG format:
  - tokens/base.tokens.json (global tier)
  - tokens/semantic.tokens.json (semantic tier)
  - tokens/component.tokens.json (component-scoped tier)
- Tools: Color Palette Generator, Modular Scale Calculator, Contrast-Safe Pairer, W3C DTCG Formatter
- Output is RAW (pre-validation) — Token Engine Crew (P10) validates and compiles
- Model tier: Tier 2 — Sonnet (§3.7)

PRD References: §4.1 (Agent 2 spec), §3.5 (Theming Model — token structure), §3.7 (Model Assignment)

Scope:
- IN: Agent definition, all 4 tools, DTCG formatting, all scale generators
- OUT: Multi-theme $extensions in tokens (P05), token validation (P10)

This agent produces the raw material. The tokens it writes are NOT final — they go through the Token Engine Crew for validation, integrity checking, and compilation.
```

---

## P05 — Theming Model & Multi-Theme Tokens

```
Implement the theming model defined in §3.5 for multi-theme and multi-brand token support.

What to build:
- Extend the Token Foundation Agent (P04) to generate per-theme values using $extensions:
  ```json
  "$extensions": {
    "com.daf.themes": {
      "light": "{color.neutral.100}",
      "dark": "{color.neutral.900}",
      "high-contrast": "{color.neutral.1000}"
    }
  }
  ```
- Theme modes from Brand Profile: light, dark, high-contrast (or custom)
- Multi-brand support (§3.5 "Multi-brand" section):
  - Base semantic tokens + per-brand override files under tokens/brands/
  - Brand override files contain only tokens that differ from base
  - Merge strategy: base + brand override → brand-specific compiled output
- ThemeProvider spec generation (ties into Primitive Scaffolding Agent, P06):
  - Runtime theme switching via CSS class on root element (NOT JS token toggling)
  - useTheme() hook exposing theme and brand properties
  - Root element class pattern: "theme-dark brand-a"
- File structure for multi-brand:
  tokens/brands/brand-a.tokens.json, brand-b.tokens.json, etc.
  tokens/compiled/brand-a/variables-light.css, etc.
- Brand names sourced from Brand Profile themes.brands array

PRD References: §3.5 (Theming Model — full section), §4.1 (Agent 2 — multi-brand mentions), §4.2 (Agent 9 — per-theme compilation)

Scope:
- IN: $extensions format, multi-brand override file structure, ThemeProvider spec requirements, brand-aware compilation prep
- OUT: Actual CSS compilation (P10, Token Engine), ThemeProvider TSX implementation (P11, Design-to-Code)

This sets the contract for how themes flow through the entire system — from token authoring to CSS output to runtime switching.
```

---

## P06 — Primitive Spec Generation

```
Implement Agent 3 (Primitive Scaffolding Agent) from the DS Bootstrap Crew.

What to build:
- CrewAI Agent definition with role "Base component spec author"
- Generate canonical spec YAMLs (specs/*.spec.yaml) for all 9 base primitives (11 exports):
  1. Box — layout container, token-bound spacing/color
  2. Stack (exports HStack + VStack) — flex layout with gap
  3. Grid — CSS grid layout
  4. Text — typography primitive, token-bound font/color/size
  5. Icon — SVG icon wrapper with size/color tokens
  6. Pressable — interactive base (button/link behavior), focus management
  7. Divider — horizontal/vertical separator
  8. Spacer — fixed or flexible spacing element
  9. ThemeProvider — theme/brand context provider (see P05 for requirements)
- Each spec YAML must define:
  - Props with types and defaults
  - Token bindings (reference semantic tokens only, never global — per §3.5 component contract)
  - Allowed children constraints
  - Composition rules
  - A11y requirements (ARIA roles, keyboard behavior)
- Tools: Primitive Spec Template Library, Token Binding Schema
- Specs reference only tokens from the foundation (no hardcoded values)
- Output: specs/*.spec.yaml files (read by Design-to-Code Crew in Phase 3)
- Model tier: Tier 2 — Sonnet

PRD References: §4.1 (Agent 3 spec), §7 (Component Scope Tiers — "9 base primitives, 11 exports"), §3.6 (Crew I/O — Bootstrap writes specs)

Scope:
- IN: Agent definition, spec YAML schema, all 9 primitive specs, token binding references
- OUT: Component spec generation (P07), code generation from these specs (P11)

These specs are the source of truth — Design-to-Code generates TSX directly from them.
```

---

## P07 — Core Component Spec Generation

```
Implement Agent 4 (Core Component Agent) from the DS Bootstrap Crew.

What to build:
- CrewAI Agent definition with role "Component spec author"
- Generate canonical spec YAMLs for the component set based on Brand Profile's componentScope:
  - Starter (10): Button, Input, Checkbox, Radio, Select, Card, Badge, Avatar, Alert, Modal
  - Standard (+9 = 19): + Table, Tabs, Accordion, Tooltip, Toast, Dropdown, Pagination, Breadcrumb, Navigation
  - Comprehensive (+6 = 25+): + DatePicker, DataGrid, TreeView, Drawer, Stepper, FileUpload, RichText
- Each spec YAML must define:
  - Props with types and defaults
  - Variants (e.g., Button: primary, secondary, ghost, danger)
  - Interactive states (hover, focus, active, disabled)
  - Token bindings (semantic tier only)
  - Composition from primitives (how the component uses Box, Stack, Text, etc.)
  - Slot definitions
  - A11y requirements
- Incorporate componentOverrides from Brand Profile (§6) for component-specific design decisions:
  e.g., DataGrid.columnResize, DatePicker.dateFormat, Modal.closeOnOverlayClick, Button.variants
- Tools: Component Spec Template Library, Variant Schema Generator, State Machine Definer
- Model tier: Tier 2 — Sonnet

PRD References: §4.1 (Agent 4 spec), §7 (Component Scope Tiers — full table), §6 (Brand Profile — componentOverrides)

Scope:
- IN: Agent definition, scope-tier logic, all component specs (up to 25+), variant/state definitions, componentOverrides integration
- OUT: Code generation from these specs (P11), spec validation (P12)

The component specs complete the "what to build" picture. Everything after this is execution.
```

---

## P08 — Pipeline Configuration & Project Scaffolding

```
Implement Agent 5 (Pipeline Configuration Agent) from the DS Bootstrap Crew.

What to build:
- CrewAI Agent definition with role "Downstream crew configurator and project scaffolder"
- Generate pipeline-config.json per §3.8 schema:
  - qualityGates: minCompositeScore (default 70), minTestCoverage (default 80), a11yLevel (from Brand Profile), blockOnWarnings (default false)
  - lifecycle: defaultStatus, betaComponents (complex Comprehensive-tier components), deprecationGracePeriodDays (default 90)
  - domains: categories (inferred from component scope, e.g., forms, navigation, feedback, layout, data-display), autoAssign (default true)
  - retry: maxComponentRetries (default 3), maxCrewRetries (default 2 for Phases 4–6)
  - models: tier1, tier2, tier3 (from env vars or defaults per §3.7)
  - buildConfig: tsTarget, moduleFormat, cssModules
- Generate project scaffolding files required by all downstream crews:
  - tsconfig.json — TypeScript compiler configuration
  - vitest.config.ts — test runner configuration
  - vite.config.ts — library-mode build configuration
- Tools: Config Generator, Threshold Calculator, Domain Inferrer, Project Scaffolder
- These files must exist before Phase 2 so downstream crews can compile and test
- Model tier: Tier 3 — Haiku (simple configuration derivation)

PRD References: §3.8 (Pipeline Configuration Schema — full schema), §4.1 (Agent 5 spec), §3.6 (Crew I/O — Bootstrap writes pipeline-config, tsconfig, vitest, vite configs)

Scope:
- IN: Agent definition, pipeline-config.json generation, tsconfig/vitest/vite config generation
- OUT: Governance Crew reads pipeline-config as its seed (P14), all downstream crews use project scaffolding

This bridges user intent (Brand Profile) to operational configuration (Governance) and ensures the build toolchain exists for all subsequent phases.
```

---

## P09 — Pipeline Orchestrator (First Publish Agent)

```
Implement Agent 6 (First Publish Agent) from the DS Bootstrap Crew — the master orchestrator.

What to build:
- CrewAI Agent definition with role "Pipeline orchestrator"
- Orchestrate the full 6-phase pipeline by invoking all downstream crews in strict sequence:
  Phase 1: DS Bootstrap (self — agents 1–5 already ran)
  Phase 2: Token Engine Crew
  Phase 3: Design-to-Code Crew → Component Factory Crew (ordered)
  Phase 4a: Documentation Crew → 4b: Governance Crew (strictly ordered — Governance depends on docs existing)
  Phase 5: AI Semantic Layer Crew + Analytics Crew (no mutual dependency, either order)
  Phase 6: Release Crew
- Intra-phase ordering rules per §3.1:
  - Phase 3: Design-to-Code before Component Factory
  - Phase 4: Documentation before Governance (Quality Gate Agent checks "all components have docs")
  - Phase 5: No ordering constraint between AI Semantic Layer and Analytics
- Instantiate the Rollback Agent (40) at pipeline start (before any crew runs) — hold direct reference as utility agent (§4.8, Agent 40 spec)
- Aggregate results and final status from all crews
- Tools: Crew Sequencer, Result Aggregator, Status Reporter
- Human Gate: Output Review after pipeline completes (§5) — user sees generation report, has 4 options:
  1. Approve
  2. Re-run full pipeline
  3. Re-run from phase (--from-phase N)
  4. Re-run specific components (--retry-components X,Y)
- Model tier: Tier 2 — Sonnet (orchestration reasoning)

PRD References: §4.1 (Agent 6 spec), §3.1 (Pipeline — phase ordering, intra-phase ordering), §5 (Human Gate Policy — Output Review), §4.8 (Agent 40 — instantiated by Agent 6)

Scope:
- IN: Agent definition, crew sequencing logic, phase ordering enforcement, human gate for output review, re-run options
- OUT: Integrates with Retry Protocol (P18) for cross-phase retry routing, integrates with Rollback Agent (P18) for checkpoints

This is the conductor. It doesn't generate anything itself — it runs the crews in order, handles results, and gates the final output.
```

---

## P10 — Token Engine Crew

```
Implement the Token Engine Crew (Crew 2) — all 5 agents (7–11).

What to build:

Agent 7 — Token Ingestion Agent (Tier 3 Haiku):
- Role: Canonical token gatekeeper
- Receive raw tokens from Token Foundation Agent, normalize to W3C DTCG, detect duplicates and naming conflicts, stage for validation
- Tools: DTCG Schema Validator, JSON Normalizer, Duplicate Detector

Agent 8 — Token Validation Agent (Tier 2 Sonnet):
- Role: Token schema and naming enforcer
- Validate: DTCG schema compliance, naming conventions (consistent casing, category prefixes, no abbreviations), WCAG contrast ratios for all foreground/background color pairs
- Does NOT check cross-tier reference integrity (that's Agent 10)
- Tools: WCAG Contrast Calculator, Naming Linter, DTCG Schema Validator

Agent 9 — Token Compilation Agent (Deterministic):
- Role: Multi-platform, multi-theme compiler operator
- Invoke Style Dictionary for all configured targets: CSS Custom Properties, SCSS variables, TypeScript constants, flat JSON, plus any additional targets from Brand Profile (Tailwind, Swift, Android XML, Compose)
- Produce separate CSS file per theme (variables-light.css, variables-dark.css, variables-high-contrast.css, etc.) per §3.5
- For multi-brand: compile base + brand override → brand-specific output under tokens/compiled/brand-a/, etc.
- Tools: Style Dictionary Compiler, Theme Resolver, Custom Compiler Plugins

Agent 10 — Token Integrity Agent (Deterministic):
- Role: Cross-tier reference graph enforcer
- Build full reference graph across all 3 tiers. Enforce tier discipline: component → semantic → global (no tier skipping). Detect circular refs, orphaned tokens (defined but unreferenced), phantom refs (reference to nonexistent token)
- Tools: Reference Graph Walker, Circular Ref Detector, Orphan Scanner, Phantom Ref Scanner

Agent 11 — Token Diff Agent (Deterministic):
- Role: Change documentation feeder
- Generate structured diff (added/modified/removed/deprecated) written to tokens/diff.json
- Initial generation: all tokens classified as "added" — consistent diff format regardless of first-run vs re-generation
- Tools: JSON Diff Engine, Deprecation Tagger

Crew-level:
- Task sequence: T1 Ingest → T2 Validate → T3 Compile → T4 Integrity check → T5 Diff
- NFRs: compilation <30s for 5K tokens, full pipeline <90s
- I/O Contract (§3.6): Reads raw tokens/*.tokens.json from Phase 1, writes validated tokens + compiled/* + diff.json

PRD References: §4.2 (full section), §3.5 (Theming — per-theme compilation), §3.6 (Crew I/O — Token Engine row), §3.7 (Model Assignment), §8 (Exit Criteria — checks 1–6 are token-related)

Scope:
- IN: All 5 agent definitions, all tools, CrewAI Crew definition, task sequencing
- OUT: Compiled tokens consumed by Design-to-Code (P11), diff consumed by Documentation (P13)
```

---

## P11 — Design-to-Code Crew

```
Implement the Design-to-Code Crew (Crew 3) — all 5 agents (12–16).

What to build:

Agent 12 — Scope Classification Agent (Tier 3 Haiku):
- Role: Generation scope classifier
- Analyze Brand Profile + component scope → classify workload: token-only (primitives), complex state machines, multi-variant. Prioritize generation queue: dependencies first (primitives → simple → complex)
- Tools: Scope Analyzer, Dependency Graph Builder, Priority Queue

Agent 13 — Intent Extraction Agent (Tier 2 Sonnet):
- Role: Structural intent analyst
- For each spec YAML: extract layout structure, spacing model, breakpoint behavior, interactive states, slot definitions, a11y attribute requirements. Output a structured intent manifest per component
- Tools: Spec Parser, Layout Analyzer, A11y Attribute Extractor

Agent 14 — Code Generation Agent (Tier 1 Opus):
- Role: Canonical component coder
- Generate from intent manifests: component source (.tsx), unit tests (.test.tsx), Storybook stories (.stories.tsx)
- Component source must: use only compiled tokens (zero hardcoded values), compose from primitives, support all variants, pass lint, include data-testid attributes
- Stories must showcase every variant and interactive state
- Use pattern memory for cross-component consistency
- Tools: Code Scaffolder, ESLint Runner, Story Template Generator, Pattern Memory Store

Agent 15 — Render Validation Agent (Deterministic):
- Role: Visual smoke test and baseline capture
- Headless render of every component + every variant via Playwright. Verify: non-empty output, no React exceptions, dimensions > 0, interactive states render distinctly. Capture baseline screenshots to screenshots/
- Tools: Playwright Headless Renderer, Screenshot Capture, Render Error Detector, Dimension Validator

Agent 16 — Result Assembly Agent (Tier 3 Haiku):
- Role: Generation report assembler
- Per-component summary: what was generated, confidence score, warnings. Write reports/generation-summary.json
- Tools: Summary Generator, Confidence Scorer, Report Writer

Crew-level:
- Task sequence: T1 Classify → T2 Extract intent → T3 Generate → T4 Render validate → T5 Assemble report
- NFRs: single component <5 min, starter batch <20 min, comprehensive <60 min
- I/O Contract (§3.6): Reads specs/*.spec.yaml + tokens/compiled/*, writes src/**/*.tsx + tests + stories + screenshots + reports/generation-summary.json

PRD References: §4.3 (full section), §3.6 (Crew I/O — Design-to-Code row), §3.7 (Model Assignment — Agent 14 is Tier 1), §9 (Tech Stack — React + TypeScript, Vitest, Playwright)

Scope:
- IN: All 5 agent definitions, all tools, Crew definition, task sequence, Playwright integration for renders
- OUT: Generated source consumed by Component Factory Crew (P12)
```

---

## P12 — Component Factory Crew

```
Implement the Component Factory Crew (Crew 4) — all 4 agents (17–20).

What to build:

Agent 17 — Spec Validation Agent (Tier 2 Sonnet):
- Role: Canonical spec gatekeeper
- Validate every spec against JSON Schema: required fields, all token refs resolve, valid state transitions (no impossible states), nesting rules, complete prop types
- Tools: JSON Schema Validator, Token Ref Checker, State Machine Validator

Agent 18 — Composition Agent (Tier 2 Sonnet):
- Role: Structural integrity enforcer
- Verify every component composes from base primitives (Box, Stack, Grid, Text, Icon, Pressable). Check: allowed children, forbidden nesting (no Pressable-in-Pressable), required slots filled, composition depth within limits
- Tools: Composition Rule Engine, Primitive Registry, Nesting Validator

Agent 19 — Accessibility Agent (Tier 1 Opus):
- Role: A11y-first enforcer
- Review and PATCH every component in place for: ARIA roles/attributes per state, keyboard nav (Tab, Enter, Escape, Arrow keys), focus management (trap, restore, programmatic), screen-reader announcements
- APPEND a11y test blocks to existing .test.tsx files (not separate files) — wrap in describe('Accessibility', () => {})
- Read brand-profile.json for target a11y level (AA vs AAA) — AAA = stricter contrast, more keyboard coverage, mandatory focus-visible
- Post-patch re-validation: patched source is re-compiled (tsc --noEmit) and re-rendered. If this fails, retry feeds error back to this agent (ties into Retry Protocol P18)
- Tools: axe-core Rule Reference, ARIA Generator, Keyboard Nav Scaffolder, Focus Trap Validator

Agent 20 — Quality Scoring Agent (Deterministic):
- Role: Component health assessor
- Composite score (0–100) per component, weighted:
  - Test coverage: 25% (line coverage %)
  - A11y pass rate: 25% (axe-core rules passing %)
  - Token compliance: 20% (token values vs hardcoded %)
  - Composition depth: 15% (primitives-only = full marks)
  - Spec completeness: 15% (required fields present %)
- Gate at 70/100 composite — below = flagged
- Note: Governance Quality Gate Agent (30) also enforces 80% min test coverage as a separate individual gate. Both must pass.
- Tools: Coverage Reporter, Score Calculator, Threshold Gate

Crew-level:
- Task sequence: T1 Validate specs → T2 Verify composition → T3 A11y enforcement/patching → T4 Re-validate patched code → T5 Score and gate
- NFR: <60s per component
- I/O Contract (§3.6): Reads specs + src + tokens + brand-profile, writes reports/quality-scorecard.json + reports/a11y-audit.json + reports/composition-audit.json, patches src/ in place

PRD References: §4.4 (full section), §3.4 (Retry Protocol — a11y post-patch re-validation), §3.6 (Crew I/O), §3.7 (Model Assignment — Agent 19 is Tier 1)

Scope:
- IN: All 4 agent definitions, all tools, Crew definition, in-place patching logic, composite scoring formula
- OUT: Quality scores consumed by Governance (P14) and Analytics (P15), a11y audit consumed by Release (P17)
```

---

## P13 — Documentation Crew

```
Implement the Documentation Crew (Crew 5) — all 5 agents (21–25).

What to build:

Agent 21 — Doc Generation Agent (Tier 1 Opus):
- Role: Automated documentation writer
- Per component: prop table (types, defaults, required), variant showcase, usage examples (≥2 per component: basic + advanced), token binding reference
- Project README (docs/README.md): installation, quick start, component list, token overview, links to docs
- Tools: Spec-to-Doc Renderer, Prop Table Generator, Example Code Generator, README Template

Agent 22 — Token Catalog Agent (Tier 2 Sonnet):
- Role: Visual token documentation builder
- Generate docs/tokens.md: every token with resolved value, tier, usage context, visual representation (hex + description for colors, size progression for type scale, size values for spacing). Organized by category
- Tools: Token Value Resolver, Scale Visualizer, Usage Context Extractor

Agent 23 — Generation Narrative Agent (Tier 1 Opus):
- Role: Design decision narrator
- Write docs/decisions/generation-narrative.md: why the DS looks the way it does — archetype selection rationale, Brand Profile → token decisions, modular scale choice, a11y tier implications, human gate overrides. The "why" document (not "what" — that's the Release Changelog)
- Tools: Decision Log Reader, Brand Profile Analyzer, Prose Generator

Agent 24 — Decision Record Agent (Tier 2 Sonnet):
- Role: ADR archivist
- Generate Architecture Decision Records in docs/decisions/: archetype selection, token scale algorithm, composition model, a11y tier implications. Standard format: Context → Decision → Consequences
- Tools: Decision Extractor, ADR Template Generator

Agent 25 — Search Index Agent (Deterministic):
- Role: Discoverability operator
- Build docs/search-index.json: full-text index across docs, components, tokens, decisions. Searchable/filterable by category and status
- Tools: Search Index Builder, Metadata Tagger

Crew-level:
- Task sequence: T1 Component docs → T2 Token catalog → T3 Generation narrative → T4 ADRs → T5 Search index
- NFR: <5 min total
- I/O Contract (§3.6): Reads specs + src + tokens + reports/generation-summary.json + brand-profile (optional) + tokens/diff.json (optional), writes docs/**/*.md + docs/search-index.json
- IMPORTANT: Must complete BEFORE Governance Crew (Phase 4b) — Quality Gate Agent (30) checks "all components have docs"

PRD References: §4.5 (full section), §3.1 (Phase 4 ordering — Documentation before Governance), §3.6 (Crew I/O — Documentation row)

Scope:
- IN: All 5 agent definitions, all tools, Crew definition, Markdown output generation
- OUT: Docs consumed by Governance's doc-completeness check (P14), drift detection (P15)
```

---

## P14 — Governance Crew

```
Implement the Governance Crew (Crew 6) — all 5 agents (26–30).

What to build:

Agent 26 — Ownership Agent (Tier 2 Sonnet):
- Role: Component domain mapper
- Generate governance/ownership.json: assign each component and token category to logical domains (forms, navigation, feedback, layout, data-display). Flag multi-domain components. Detect orphans
- Tools: Domain Classifier, Relationship Analyzer, Orphan Detector

Agent 27 — Workflow Agent (Tier 2 Sonnet):
- Role: Contribution pipeline definer
- Generate governance/workflow.json as a state machine: token change pipeline, new component pipeline, quality gates at each step
- Tools: Workflow State Machine Generator, Gate Mapper

Agent 28 — Deprecation Agent (Tier 2 Sonnet):
- Role: Lifecycle policy definer
- Generate governance/deprecation-policy.json: default grace period, warning injection rules, migration guide requirements, removal criteria. Tag experimental/unstable components with lifecycle status
- Tools: Lifecycle Tagger, Deprecation Policy Generator, Stability Classifier

Agent 29 — RFC Agent (Tier 2 Sonnet):
- Role: Decision process definer
- Generate docs/templates/rfc-template.md: when RFC is required (new primitive, breaking token change), template structure, required sections, approval criteria
- Tools: RFC Template Generator, Process Definition Builder

Agent 30 — Quality Gate Agent (Deterministic + Tier 2 reasoning):
- Role: Gate threshold enforcer and test author
- Individual pass/fail gates (distinct from Agent 20's composite score):
  - 80% min test coverage per component (line coverage)
  - A11y audit pass (zero critical violations)
  - All token references resolve
  - All components have docs (requires Documentation Crew output — Phase 4a)
  - All components have ≥1 usage example
- Both 70/100 composite (Agent 20) AND all individual gates must pass
- Generate project-level test suites:
  - tests/tokens.test.ts — token JSON validity, DTCG schema, reference resolution
  - tests/a11y.test.ts — all interactive components have ARIA roles
  - tests/composition.test.ts — all components compose from primitives
  - tests/compliance.test.ts — no hardcoded values
- These tests are what `npm test` runs for exit criteria verification
- Tools: Gate Evaluator, Threshold Config, Report Writer, Test Suite Generator

Crew-level:
- Task sequence: T1 Assign ownership → T2 Define workflows → T3 Set deprecation → T4 Generate RFC templates → T5 Evaluate quality gates + generate test suites
- Input: reads pipeline-config.json (from P08 Agent 5) as seed, plus brand-profile, specs, quality-scorecard
- I/O Contract (§3.6): writes governance/*.json + docs/templates/* + tests/*.test.ts
- REQUIRES Documentation Crew to have completed first (Phase 4a → 4b ordering)

PRD References: §4.6 (full section), §3.1 (Phase 4 strict ordering), §3.6 (Crew I/O — Governance row), §3.8 (Pipeline Config — Governance reads it)

Scope:
- IN: All 5 agent definitions, all tools, Crew definition, pipeline-config consumption, test suite generation
- OUT: Test suites consumed by Release Crew's npm test (P17), quality gates consumed by Analytics (P15)
```

---

## P15 — Analytics Crew

```
Implement the Analytics Crew (Crew 7) — all 5 agents (31–35).

What to build:

Agent 31 — Usage Tracking Agent (Tier 2 Sonnet):
- Role: Internal usage analyzer
- Scan all generated component source via AST: which tokens are actually used (vs defined but unused), which primitives consumed by which components, cross-component import relationships. Identify unused tokens and unreferenced primitives
- Tools: AST Import Scanner, Token Usage Mapper, Dependency Graph Builder

Agent 32 — Token Compliance Agent (Deterministic):
- Role: Hardcoded value hunter
- Static AST analysis of all source for: hardcoded color values (hex, rgb, hsl), spacing values (px, rem, em), font sizes, deprecated token refs. Report every violation with file, line, suggested token replacement
- Write reports/token-compliance.json
- Tools: AST Analyzer, Token Map, Violation Reporter

Agent 33 — Drift Detection Agent (Tier 2 Sonnet):
- Role: Spec ↔ code ↔ docs consistency checker and fixer
- Compare three representations: canonical spec (YAML) vs generated code (TSX) vs generated docs (Markdown). Flag inconsistencies: prop in spec not in code, variant in code not documented, token in docs that doesn't exist
- Authoritative source: spec is always authoritative over code and docs
- Auto-fix: update docs to match code. Non-fixable (code missing spec prop): report with recommended action ("re-run Design-to-Code for component X")
- Write reports/drift-report.json
- Tools: Structural Comparator, Cross-Reference Checker, Drift Reporter, Doc Patcher

Agent 34 — Pipeline Completeness Agent (Tier 3 Haiku):
- Role: Pipeline completeness tracker
- Track each component through: created → spec validated → code generated → a11y passed → tests written → docs generated → fully complete. Flag stuck components. Recommend interventions
- Tools: Pipeline Stage Tracker, Completeness Calculator, Intervention Recommender

Agent 35 — Breakage Correlation Agent (Tier 2 Sonnet):
- Role: Cross-component failure investigator
- Analyze all test failures (exhausted-retry + final npm test). Trace dependency chains: if Button fails, check if Card (uses Button) also fails. Classify each failure as root-cause or downstream
- Tools: Failure Correlator, Dependency Chain Walker, Root Cause Analyzer

Crew-level:
- Task sequence: T1 Usage scan → T2 Token compliance → T3 Drift detection → T4 Pipeline completeness → T5 Breakage correlation
- I/O Contract (§3.6): reads specs + src + docs + tokens, writes reports/token-compliance.json + reports/drift-report.json
- No mutual dependency with AI Semantic Layer Crew — Phase 5 crews can run in either order

PRD References: §4.7 (full section), §3.1 (Phase 5 — no ordering constraint), §3.6 (Crew I/O — Analytics row), §8 (Exit Criteria — checks 10, 12, 13)

Scope:
- IN: All 5 agent definitions, all tools, Crew definition, AST analysis integration, drift auto-fixing
- OUT: Reports consumed by Release Crew (P17) and Output Review gate (P09)
```

---

## P16 — AI Semantic Layer Crew

```
Implement the AI Semantic Layer Crew (Crew 9) — all 5 agents (41–45).

What to build:

Agent 41 — Registry Maintenance Agent (Tier 1 Opus):
- Role: Knowledge graph builder
- Build registry/components.json: for every component, record all props (types, defaults), variants, states, slots, token bindings, a11y attributes, usage examples. Raw structured data consumed by Agent 45
- Tools: Spec Indexer, Example Generator, Registry Builder

Agent 42 — Token Resolution Agent (Tier 2 Sonnet):
- Role: Semantic intent mapper
- Build registry/tokens.json: for every token, record resolved value per platform, tier, semantic purpose, related tokens, natural language description. Enable intent-to-token resolution ("I need a muted background" → correct token)
- Tools: Token Graph Traverser, Semantic Mapper, Natural Language Describer

Agent 43 — Composition Constraint Agent (Tier 2 Sonnet):
- Role: Valid tree definer
- Build registry/composition-rules.json: per component, record allowed children, forbidden nesting, required slots, max depth, valid/invalid composition tree examples
- Tools: Composition Rule Extractor, Tree Validator, Example Tree Generator

Agent 44 — Validation Rule Agent (Tier 2 Sonnet):
- Role: Compliance rule exporter
- Build registry/compliance-rules.json: exportable rules for AI assistants/linters — token usage, composition rules, a11y requirements, naming conventions
- Tools: Rule Compiler, Validation Schema Generator

Agent 45 — Context Serializer Agent (Tier 2 Sonnet):
- Role: AI context packager
- Package registry + token graph + composition rules + compliance rules into:
  - .cursorrules (for Cursor)
  - copilot-instructions.md (for GitHub Copilot)
  - ai-context.json (generic LLM consumption)
- Optimize for token budget constraints
- Tools: Context Formatter, Token Budget Optimizer, Multi-Format Serializer

Crew-level:
- Task sequence: T1 Component registry → T2 Token graph → T3 Composition rules → T4 Compliance rules → T5 AI context packaging
- I/O Contract (§3.6): reads specs + primitives + components + tokens + composition-audit, writes registry/*.json + .cursorrules + copilot-instructions.md + ai-context.json
- No mutual dependency with Analytics Crew — either order in Phase 5

PRD References: §4.9 (full section), §3.6 (Crew I/O — AI Semantic Layer row), §3.7 (Agent 41 is Tier 1), §8 (Exit Criteria — check 14: component registry valid)

Scope:
- IN: All 5 agent definitions, all tools, Crew definition, multi-format context serialization
- OUT: AI context files included in final package output (P17)

This crew makes the design system "AI-native" — consumable by coding assistants from day one.
```

---

## P17 — Release Crew

```
Implement the Release Crew (Crew 8) — agents 36–39 (Agent 40/Rollback is in P18).

What to build:

Agent 36 — Semver Agent (Tier 3 Haiku):
- Role: Version calculator
- Determine version: v1.0.0 if all quality gates pass, v0.x.0 if experimental/incomplete. Apply conventional semver semantics
- Tools: Gate Status Reader, Version Calculator

Agent 37 — Release Changelog Agent (Tier 2 Sonnet):
- Role: Release inventory author
- Write docs/changelog.md: full component inventory (name, status, quality score), token category summary (count per category, compilation targets), quality gate pass/fail summary, known issues and failed components. The "what" document (not "why" — that's Agent 23's Generation Narrative). Coherent prose grouped by category
- Tools: Component Inventory Reader, Quality Report Parser, Prose Generator

Agent 38 — Codemod Agent (Tier 2 Sonnet):
- Role: Adoption helper generator
- Generate example codemod scripts for common adoption patterns: raw <button> → <Button>, raw <input> → <Input>, hardcoded color: #333 → var(--color-text-primary). Adoption codemods (not migration codemods). Serve as templates for future version-to-version migrations
- Tools: AST Pattern Matcher, Codemod Template Generator, Example Suite Builder

Agent 39 — Publish Agent (Tier 2 Sonnet):
- Role: Package assembler and final validator
- Assemble package.json: correct dependencies, peer deps, entry points, TypeScript config, export maps
- Execute full validation sequence:
  1. npm install (verify dependencies resolve)
  2. npm run build / tsc --noEmit (TypeScript compiles)
  3. npm test (run ALL project-level and component-level tests)
- Parse test results. Report failures in reports/generation-summary.json
- This is the LAST agent before Output Review gate — its pass/fail = final pipeline status
- Tools: Package.json Generator, Dependency Resolver, npm CLI, Test Result Parser

Crew-level:
- Task sequence: T1 Calculate version → T2 Generate changelog → T3 Generate codemods → T4 Assemble package → T5 npm install + build + test → T6 Validate final status
- I/O Contract (§3.6): reads entire output folder, writes package.json, src/index.ts, docs/changelog.md, barrel index.ts files, updates reports/generation-summary.json
- NFRs: Final npm test must cover all §8 exit criteria
- Retry: if crew fails, First Publish Agent retries entire crew up to 2 times (§3.4, Phases 4–6 retry model)

PRD References: §4.8 (Agents 36–39), §3.6 (Crew I/O — Release row), §8 (Exit Criteria — checks 7, 8 are Fatal build checks), §5 (Output Review gate follows this crew)

Scope:
- IN: Agents 36–39 definitions, all tools, Crew definition, npm toolchain integration, final validation sequence
- OUT: Final output folder ready for Output Review gate (P09), Rollback Agent is separate (P18)
```

---

## P18 — Retry Protocol, Rollback & Checkpoint System

```
Implement the cross-cutting Retry Protocol (§3.4), Rollback Agent (Agent 40), and checkpoint/resume system.

What to build:

Retry Protocol (§3.4):
- Bounded retry loop: validation agent rejects → structured rejection → originating generator re-runs with accumulated context → re-validate → max 3 attempts per component per validation stage
- Retry context accumulates: attempt 2 sees original + rejection 1, attempt 3 sees original + rejection 1 + rejection 2
- Retry boundaries (generator ↔ validator):
  - Token Foundation (2) ↔ Token Validation (8): naming violation, contrast failure, broken reference
  - Code Generation (14) ↔ Spec Validation (17): missing props, invalid states, broken token refs
  - Code Generation (14) ↔ Render Validation (15): render failure, empty output, visual artifact
  - Code Generation (14) ↔ TypeScript Compiler: type errors, import errors
  - Accessibility (19) ↔ axe-core: critical a11y violation after patching
  - Accessibility (19) ↔ TypeScript Compiler + Render Validation (15): a11y patches introduced errors
- Cross-phase retry routing: First Publish Agent (6) detects Phase 2 validation failure → re-invokes Phase 1 agent with rejection → re-runs Phase 2 crew
- Phases 4–6 simpler model: retry entire crew up to 2 attempts (no per-agent retry)
- Components exhausting retries: marked "failed" in generation report with full error traces, not silently dropped. Pipeline Completeness Agent (34) flags them

Agent 40 — Rollback Agent (cross-cutting, Deterministic):
- Role: Generation checkpoint manager
- Instantiated by First Publish Agent (6) at pipeline start — NOT part of Release Crew task flow
- Before each crew runs: snapshot current output folder as timestamped checkpoint
- On catastrophic crew failure: restore to last known-good checkpoint
- Rollback cascade policy: when checkpoint restored, all crews after restored phase are invalidated and must re-run. First Publish Agent never resumes mid-sequence after rollback — replays subsequent phases (expensive but safe)
- On exhausted retries: preserve last best attempt via Rollback Agent
- Tools: Checkpoint Creator, Restore Executor, Rollback Reporter

Resume-on-failure (§3.4):
- Checkpoint system writes timestamped snapshots at each phase boundary
- `daf init --resume <output-folder>` detects last successful checkpoint, validates integrity (all expected files present and non-corrupt), resumes from next phase
- Resume does NOT retry the failed phase — re-runs from scratch with clean slate
- If checkpoint is corrupt/incomplete: report issue, ask user whether to restart from Phase 1

PRD References: §3.4 (Retry Protocol — full section), §4.8 (Agent 40 spec), §4.4 (Agent 19 post-patch re-validation), §4.1 (Agent 6 — orchestrator holds Agent 40 reference)

Scope:
- IN: Retry loop infrastructure, all retry boundaries, structured rejection protocol, context accumulation, Agent 40 definition, checkpoint/snapshot system, --resume flag, rollback cascade policy
- OUT: Integrates into Pipeline Orchestrator (P09), affects all crews with generator-validator pairs

This is the safety net — it ensures the pipeline degrades gracefully instead of failing catastrophically.
```

---

## P19 — Exit Criteria & Final Validation

```
Implement the 15-point exit criteria system from §8 that defines what "valid" means for a generated design system.

What to build:
- Validation framework that runs all 15 checks and classifies results as Fatal or Warning
- 8 Fatal checks (pipeline reports failure, isComplete: false):
  1. Token JSON parses without error (JSON.parse)
  2. Token JSON conforms to W3C DTCG schema (JSON Schema validation)
  3. All semantic token references resolve to global tokens (reference graph traversal)
  4. All component token references resolve to semantic tokens (reference graph traversal)
  5. All foreground/background color pairs meet WCAG target (contrast ratio calculation)
  6. CSS custom properties have no undefined references (regex + token map)
  7. TypeScript compiles with zero errors (tsc --noEmit)
  8. npm install and npm run build complete without errors (shell)
- 7 Warning checks (flagged in report, isComplete: true):
  9. All unit tests pass (Vitest)
  10. No hardcoded color/spacing values in source (AST scan)
  11. All interactive components have ARIA roles (AST scan)
  12. All components score ≥70/100 on quality gate (Quality Scoring Agent)
  13. Spec ↔ code ↔ docs consistency check passes (Drift Detection Agent)
  14. Component registry JSON is valid and complete (schema validation)
  15. One or more components marked "failed" in generation summary (generation report)
- Classification: test failures (check 9) are Warning NOT Fatal — generated tests may fail despite correct output. Build failures (check 8) remain Fatal
- Exit status: isComplete = true if all 8 Fatal pass, regardless of Warnings
- Integration points:
  - Checks 1–6 are verified by Token Engine Crew (P10) agents
  - Check 7 is run via tsc --noEmit (integrated in multiple crews)
  - Check 8 is run by Publish Agent (P17, Agent 39)
  - Checks 9–15 are gathered from various crew reports
- Final validation report aggregates all 15 checks with pass/fail and evidence

PRD References: §8 (Exit Criteria — full table), §4.8 (Agent 39 — final npm test), §5 (Output Review — user sees these results)

Scope:
- IN: Validation framework, all 15 check implementations, Fatal vs Warning classification, isComplete logic, aggregated report
- OUT: Report consumed by Output Review gate (P09) and included in output folder

This codifies the quality contract — the system's definition of "done" at the pipeline level.
```

---

## Execution Order Summary

| Order | Proposal | Depends On |
|-------|----------|------------|
| 1 | P01 — Project Foundation | — |
| 2 | P02 — Interview CLI | P01 |
| 3 | P03 — Brand Discovery Agent | P01 |
| 4 | P04 — Token Foundation Agent | P03 |
| 5 | P05 — Theming Model | P04 |
| 6 | P06 — Primitive Spec Generation | P03 |
| 7 | P07 — Core Component Spec Generation | P06 |
| 8 | P08 — Pipeline Configuration | P03 |
| 9 | P09 — Pipeline Orchestrator | P03–P08 |
| 10 | P10 — Token Engine Crew | P04, P05 |
| 11 | P11 — Design-to-Code Crew | P06, P07, P10 |
| 12 | P12 — Component Factory Crew | P11 |
| 13 | P13 — Documentation Crew | P11, P12 |
| 14 | P14 — Governance Crew | P08, P13 |
| 15 | P15 — Analytics Crew | P11, P12, P13 |
| 16 | P16 — AI Semantic Layer Crew | P11, P12 |
| 17 | P17 — Release Crew | P13–P16 |
| 18 | P18 — Retry, Rollback & Checkpoints | P09 (integrate after orchestrator exists) |
| 19 | P19 — Exit Criteria | P10–P17 (integrate across all validation points) |
