# Specification: Theming Model

## Purpose

Defines the W3C DTCG `$extensions.com.daf.themes` convention used by the DAF pipeline to embed per-theme alias values inside semantic token files. This spec is the authoritative contract for how multi-theme token data is structured — all agents that read or write semantic token files MUST conform to it.

Affected crew: DS Bootstrap Crew (Agent 2 — Token Foundation Agent), Token Engine Crew (Agents 7–10).

---

## Requirements

### Requirement: Semantic Tokens Carry Per-Theme Alias Values

Every semantic token in `tokens/semantic.tokens.json` that has different resolved values across the themes declared in `Brand Profile.themes.modes[]` SHALL include a `$extensions.com.daf.themes` block mapping each theme mode name to a global-tier alias reference string.

The `$value` field on the token MUST equal the alias reference for the Brand Profile's default theme (i.e., the first entry in `themes.modes[]`).

Agents: Token Foundation Agent (2) writes this structure; Token Validation Agent (7) validates it; Token Compilation Agent (9) consumes it.

#### Acceptance Criteria

- [ ] Every semantic token with theme-variant values has a `$extensions.com.daf.themes` block
- [ ] The `$extensions.com.daf.themes` object has exactly one key per entry in `Brand Profile.themes.modes[]`
- [ ] Every value in the `com.daf.themes` map is a DTCG alias reference string of the form `{group.subgroup.step}` — never a raw hex code or dimension value
- [ ] The `$value` field of the token equals the reference for the default theme (first in `themes.modes[]`)
- [ ] Semantic tokens whose value does not vary across themes MAY omit `$extensions.com.daf.themes`
- [ ] Component-scoped tokens in `tokens/component.tokens.json` do NOT include `$extensions.com.daf.themes` — they reference semantic tokens, and theming is resolved at the semantic tier

#### Scenario: Two-theme profile produces correct extension block

- **WHEN** the Brand Profile declares `themes.modes: ["light", "dark"]`
- **AND** the semantic token `color.background.surface` maps to `color.neutral.100` in light mode and `color.neutral.900` in dark mode
- **THEN** `tokens/semantic.tokens.json` contains:
  ```json
  {
    "color": {
      "background": {
        "surface": {
          "$type": "color",
          "$value": "{color.neutral.100}",
          "$description": "Default page/surface background",
          "$extensions": {
            "com.daf.themes": {
              "light": "{color.neutral.100}",
              "dark": "{color.neutral.900}"
            }
          }
        }
      }
    }
  }
  ```
- **AND** `$value` equals `"{color.neutral.100}"` (the light/default theme alias)

#### Scenario: Three-theme profile includes all three entries

- **WHEN** the Brand Profile declares `themes.modes: ["light", "dark", "high-contrast"]`
- **THEN** every theme-variant semantic token's `$extensions.com.daf.themes` block has exactly three keys: `light`, `dark`, `high-contrast`
- **AND** the `high-contrast` entry references a high-contrast global palette alias (e.g., `color.neutral.1000` or `color.neutral.50`)

#### Scenario: Token with no theme variation omits extension block

- **WHEN** a semantic token such as `motion.duration.fast` has the same value in all themes
- **THEN** `tokens/semantic.tokens.json` contains no `$extensions.com.daf.themes` block on that token
- **AND** the token is valid and complete without the extension

#### Scenario: Component tokens never carry theme extensions

- **WHEN** `tokens/component.tokens.json` is inspected
- **THEN** no token object in the file contains a `$extensions.com.daf.themes` key

---

### Requirement: Token Validation Of Theme Extension Block Structure

The Token Validation Agent (7) SHALL validate the `$extensions.com.daf.themes` block on every semantic token that includes it, as part of the Token Engine Crew (Phase 2) validation pass.

#### Acceptance Criteria

- [ ] Validates that every key in `com.daf.themes` matches an entry in `Brand Profile.themes.modes[]`
- [ ] Validates that every value in `com.daf.themes` is a valid alias reference (starts with `{`, ends with `}`, and resolves against the global token tier)
- [ ] Validates that the `$value` field on the token equals the `com.daf.themes` entry for `themes.modes[0]` (the default theme)
- [ ] Reports validation failures as structured errors: `{ "token": "<path>", "error": "<description>", "severity": "fatal" }`
- [ ] A missing `com.daf.themes` block on a token that has theme-variant values (determined by cross-checking compiled output) is a Warning, not Fatal

#### Scenario: Mismatched key name triggers validation error

- **WHEN** a semantic token contains `$extensions.themes` (the old key, without the `com.daf` namespace)
- **THEN** the Token Validation Agent reports a fatal validation error identifying the token path and the incorrect extension key
- **AND** the pipeline does not proceed to Token Compilation Agent (9) for that token file

#### Scenario: Alias reference in theme extension fails to resolve

- **WHEN** the `com.daf.themes.dark` value is `"{color.neutral.99}"` but `color.neutral.99` does not exist in `tokens/base.tokens.json`
- **THEN** the Token Validation Agent reports a fatal error: phantom reference in theme extension
- **AND** the error includes the token path, the theme key, and the unresolvable reference string
