# Specification: Token Compilation

## Purpose

Defines the behavioral requirements for Agent 9 (Token Compilation Agent). Covers Style Dictionary invocation, per-theme CSS file generation, multi-platform target compilation, and the compiler output I/O contract consumed by downstream crews.

---

## Requirements

### Requirement: Multi-platform token compilation

Agent 9 (Token Compilation Agent) in the Token Engine Crew MUST invoke `StyleDictionaryCompiler` to compile all staged token files into every configured output target: CSS Custom Properties, SCSS variables, TypeScript constants, and flat JSON. Compilation MUST succeed for the crew to advance to task T4.

#### Acceptance Criteria

- [ ] Agent 9 reads `tokens/staged/*.tokens.json` as the compiler input.
- [ ] Agent 9 writes `tokens/compiled/variables.css` (default theme CSS).
- [ ] Agent 9 writes `tokens/compiled/variables.scss`.
- [ ] Agent 9 writes `tokens/compiled/tokens.ts` (TypeScript constants).
- [ ] Agent 9 writes `tokens/compiled/tokens.json` (flat resolved JSON).
- [ ] If Style Dictionary raises a compilation error, Agent 9 propagates the error and Token Engine Crew exits non-zero.
- [ ] All compiled files are non-empty.

#### Scenario: Valid staged tokens compile successfully

- GIVEN `tokens/staged/` contains three valid DTCG tier files
- WHEN Agent 9 runs task T3
- THEN all four compiled output files are written to `tokens/compiled/`
- AND each file is non-empty
- AND no error is raised

#### Scenario: Style Dictionary encounters unresolvable reference

- GIVEN a staged token contains `$value: "{color.brand.nonexistent}"` that cannot be resolved
- WHEN Agent 9 invokes the compiler
- THEN Style Dictionary raises a reference resolution error
- AND Agent 9 propagates the error with the unresolvable path in the detail
- AND Token Engine Crew exits non-zero

---

### Requirement: Per-theme CSS file generation

Agent 9 MUST produce a separate CSS Custom Property file per theme declared in the Brand Profile. Each theme file uses the same property names as the default `variables.css` but resolves values from the `$extensions.com.daf.themes.<theme>` extension field of each semantic token.

#### Acceptance Criteria

- [ ] Agent 9 reads the themes list from the Brand Profile (`brand-profile.json`).
- [ ] For each theme in the list, Agent 9 writes `tokens/compiled/variables-{theme}.css` where `{theme}` is the theme identifier (e.g., `light`, `dark`, `high-contrast`).
- [ ] Each per-theme CSS file contains only the custom properties whose values differ from the default theme (or all properties if a full override is configured).
- [ ] The default `variables.css` matches the Brand Profile's `defaultTheme` value.
- [ ] A Brand Profile declaring themes `["light", "dark"]` produces exactly `variables-light.css` and `variables-dark.css`.

#### Scenario: Brand Profile declares two themes

- GIVEN `brand-profile.json` has `themes: ["light", "dark"]` and `defaultTheme: "light"`
- WHEN Agent 9 runs task T3
- THEN `tokens/compiled/variables-light.css` is written
- AND `tokens/compiled/variables-dark.css` is written
- AND `tokens/compiled/variables.css` contains the resolved light-theme values

#### Scenario: Brand Profile declares three themes including high-contrast

- GIVEN `brand-profile.json` has `themes: ["light", "dark", "high-contrast"]`
- WHEN Agent 9 runs task T3
- THEN three per-theme CSS files are written: `variables-light.css`, `variables-dark.css`, `variables-high-contrast.css`

#### Scenario: Semantic token missing theme extension for a declared theme

- GIVEN a semantic token does not have an `$extensions.com.daf.themes.dark` value but `dark` is in the themes list
- WHEN Agent 9 resolves that token for the dark theme
- THEN Agent 9 falls back to the token's default `$value`
- AND emits a warning (not fatal) identifying the token path and the missing theme key

---

### Requirement: Compiled output I/O contract compliance

The files written by Agent 9 MUST conform to the I/O contract defined in PRD §3.6 so that downstream crews (Design-to-Code, Component Factory, Analytics) can read them without modification.

#### Acceptance Criteria

- [ ] `tokens/compiled/tokens.json` is a flat, resolved JSON object (no DTCG `$` prefix keys; plain `key: value` pairs).
- [ ] `tokens/compiled/tokens.ts` exports a typed `const tokens` object compatible with TypeScript strict mode.
- [ ] `tokens/compiled/variables.css` contains only `:root { --token-name: value; }` declarations with no other selectors.
- [ ] All values in the compiled outputs are fully resolved (no unresolved `{reference}` syntax).

#### Scenario: Downstream crew reads compiled tokens

- GIVEN Agent 9 has successfully compiled tokens to `tokens/compiled/`
- WHEN a downstream agent in the Design-to-Code Crew reads `tokens/compiled/tokens.json`
- THEN the JSON is a flat key-value mapping with no DTCG `$` prefix fields
- AND all values are primitive strings or numbers (fully resolved)
