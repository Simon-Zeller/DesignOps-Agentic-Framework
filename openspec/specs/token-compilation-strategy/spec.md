# Specification: Token Compilation Strategy

## Purpose

Defines how the Token Compilation Agent (Agent 9, Token Engine Crew) uses Style Dictionary to compile DTCG token files into per-theme CSS custom property files. This spec governs transform pipeline configuration, output file naming, CSS class-scoping structure, and multi-brand merge logic.

Affected crew: Token Engine Crew (Agent 9 — Token Compilation Agent).

---

## Requirements

### Requirement: Per-Theme CSS File Generation

The Token Compilation Agent (9) SHALL produce one CSS custom property file per theme declared in `Brand Profile.themes.modes[]`, plus a default `variables.css` file matching the default theme.

#### Acceptance Criteria

- [ ] Produces `tokens/compiled/variables.css` — CSS custom properties using default theme values (alias for `variables-<default-theme>.css`)
- [ ] Produces one `tokens/compiled/variables-<theme-name>.css` file per entry in `themes.modes[]`
- [ ] Each CSS file contains the identical set of custom property names (no property is missing from any theme file)
- [ ] Custom property names follow the kebab-case path of the semantic token: `color.background.surface` → `--color-background-surface`
- [ ] Values in each theme file are resolved raw values (hex codes, px, ms — not alias strings); all references are fully resolved before writing
- [ ] The agent fails fast with a structured error if any semantic token reference cannot be resolved for a given theme

#### Scenario: Two-theme profile produces correct file set

- **WHEN** `Brand Profile.themes.modes` is `["light", "dark"]`
- **THEN** the following files are written:
  - `tokens/compiled/variables.css` (light values — the default)
  - `tokens/compiled/variables-light.css`
  - `tokens/compiled/variables-dark.css`

#### Scenario: CSS custom property names are consistent across all theme files

- **WHEN** two theme CSS files are compared
- **THEN** both contain an identical set of `--` property declarations (same names, different values)
- **AND** no property present in one file is absent from the other

#### Scenario: Default variables.css matches default theme

- **WHEN** the default theme is `"light"`
- **THEN** the contents of `variables.css` are identical to `variables-light.css`

---

### Requirement: CSS Class-Scoped Output Structure

Each non-default theme CSS file SHALL scope its custom property declarations under a `.theme-<name>` CSS class selector rather than `:root`. The default `variables.css` MUST use `:root` scope.

#### Acceptance Criteria

- [ ] `variables.css` (and `variables-<default>.css`) uses `:root { ... }` as the selector
- [ ] All other `variables-<theme>.css` files use `.theme-<name> { ... }` as the selector (e.g., `.theme-dark { --color-background-surface: #1a1a1a; }`)
- [ ] No `!important` declarations are used; specificity is managed via class application by `ThemeProvider`
- [ ] The CSS class name prefix `theme-` is hardcoded for v1 (custom prefix is a future enhancement)

#### Scenario: Dark theme file uses class selector

- **WHEN** `tokens/compiled/variables-dark.css` is inspected
- **THEN** it begins with `.theme-dark {`
- **AND** all custom properties are declared within that single rule block

#### Scenario: Default theme file uses :root selector

- **WHEN** `tokens/compiled/variables.css` is inspected
- **THEN** it begins with `:root {`

---

### Requirement: Multi-Brand Compilation With Override Merge

When `Brand Profile.archetype` is `"multi-brand"` and `themes.brands[]` is non-empty, the Token Compilation Agent (9) SHALL merge each brand override file with the base semantic token file and compile the merged result into a brand-scoped subdirectory.

#### Acceptance Criteria

- [ ] For each brand in `themes.brands[]`, reads `tokens/brands/<brand-name>.tokens.json` as the override file
- [ ] Merges override file onto base `tokens/semantic.tokens.json`: override values take precedence; tokens absent from the override file retain base values
- [ ] Writes compiled output to `tokens/compiled/<brand-name>/variables.css` and one file per theme mode
- [ ] Brand-scoped CSS files use `.theme-<name>.brand-<brand-name>` compound selector (e.g., `.theme-dark.brand-a { ... }`)
- [ ] Default brand output (no override applied) continues to use `.theme-<name>` selectors without a brand class
- [ ] Merge errors (unresolvable references in override file) are reported as fatal errors with token path and brand name

#### Scenario: Brand override produces compound class selector

- **WHEN** `Brand Profile.themes.brands` is `["brand-a"]` and `tokens/brands/brand-a.tokens.json` exists
- **THEN** `tokens/compiled/brand-a/variables-dark.css` contains selectors of the form:
  `.theme-dark.brand-a { --color-background-surface: #0d0d0d; }`

#### Scenario: Tokens absent from override retain base values

- **WHEN** `brand-a.tokens.json` overrides `color.background.surface` but not `color.text.default`
- **THEN** `tokens/compiled/brand-a/variables-dark.css` contains the base dark value for `--color-text-default`
- **AND** contains the brand-a override value for `--color-background-surface`

#### Scenario: Non-multi-brand archetype skips brand compilation

- **WHEN** `Brand Profile.archetype` is `"enterprise-b2b"` (not multi-brand)
- **THEN** no `tokens/compiled/<brand-name>/` subdirectories are created
- **AND** the Token Compilation Agent completes without error

---

### Requirement: Style Dictionary Transform Pipeline Configuration

The Token Compilation Agent (9) SHALL configure and invoke Style Dictionary with a custom transform group that handles the `com.daf.themes` extension and produces the required CSS scoping.

#### Acceptance Criteria

- [ ] Registers a custom Style Dictionary transform named `daf/theme-resolver` that, for a given theme mode, extracts the appropriate alias from `$extensions.com.daf.themes` and resolves it against the global token tier
- [ ] Registers a custom Style Dictionary format named `daf/css-theme-scope` that wraps declarations in the correct selector (`:root` for default, `.theme-<name>` for others)
- [ ] Does NOT use the built-in `css/variables` format directly for themed output — uses `daf/css-theme-scope`
- [ ] The Style Dictionary version used by the generated package is pinned in the package's `package.json` to avoid transform API breakage
- [ ] Style Dictionary invocation is wrapped in a retry-safe function: if invocation fails, the agent reports the error with Style Dictionary version, config dump, and error message before triggering the Token Engine retry protocol

#### Scenario: Custom transform resolves per-theme alias

- **WHEN** the `daf/theme-resolver` transform runs for theme `"dark"`
- **AND** the token has `$extensions.com.daf.themes.dark: "{color.neutral.900}"`
- **THEN** the transform replaces the token's effective `$value` with the resolved hex value of `color.neutral.900` from the global tier
- **AND** the resolved value (not the alias string) is written to the CSS file

#### Scenario: Token without theme extension passes through unchanged

- **WHEN** the `daf/theme-resolver` transform runs for a token with no `$extensions.com.daf.themes` block
- **THEN** the token's original `$value` is used as-is for all theme compilations
