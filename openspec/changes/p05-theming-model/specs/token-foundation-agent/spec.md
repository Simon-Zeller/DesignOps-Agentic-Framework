# Specification Delta: Token Foundation Agent

## Scope

Delta spec for `token-foundation-agent`. Updates the `WC3DTCGFormatter` tool requirement to use the correct `com.daf.themes` DTCG extension namespace (was `themes`). All other requirements in the base spec at `openspec/specs/token-foundation-agent/spec.md` remain unchanged.

---

## MODIFIED Requirements

### Requirement: W3C DTCG JSON Serialization

The `WC3DTCGFormatter` tool MUST serialize the assembled token data into three valid W3C DTCG JSON files and write them to the `tokens/` directory.

#### Acceptance Criteria

- [ ] `tokens/base.tokens.json` contains only global-tier tokens with raw `$value` fields (hex, px, ms, etc.)
- [ ] `tokens/semantic.tokens.json` contains only reference-valued tokens (`$value: "{group.token.step}"`) — no raw hex values in the semantic tier
- [ ] `tokens/component.tokens.json` contains component-scoped tokens referencing semantic tokens
- [ ] Every token object has `$value`, `$type`, and `$description` fields
- [ ] Semantic tokens for multi-theme profiles include `$extensions.com.daf.themes` mapping theme mode names to resolved alias references (key MUST be `com.daf.themes` — bare `themes` key is invalid)
- [ ] All `{...}` reference strings in semantic/component tiers resolve against the global-tier dict before files are written (self-check pass)
- [ ] Raises `ValueError` with the token path and broken reference string if any reference is unresolvable
- [ ] Creates the `tokens/` directory if it does not exist
- [ ] Writes valid UTF-8 JSON (2-space indented for readability)
- [ ] Returns a list of written file paths as strings

#### Scenario: Global tier uses raw values only

- **WHEN** a complete palette dict has `color.primary.500 = "#3D72B4"`
- **THEN** `tokens/base.tokens.json` contains `{ "color": { "primary": { "500": { "$value": "#3D72B4", "$type": "color", "$description": "..." } } } }`
- **AND** no `$value` field in `base.tokens.json` contains a `{...}` reference string

#### Scenario: Semantic tier uses reference values only

- **WHEN** a semantic overrides dict has `interactive.primary.background: "color.primary.700"`
- **THEN** `tokens/semantic.tokens.json` contains `{ "interactive": { "primary": { "background": { "$value": "{color.primary.700}", "$type": "color", "$description": "..." } } } }`
- **AND** no `$value` field in `semantic.tokens.json` is a plain hex code

#### Scenario: Self-check catches broken reference before write

- **WHEN** a semantic overrides dict has a typo producing reference `{color.priary.700}` (misspelled)
- **THEN** it raises `ValueError` before writing any file
- **AND** the error message identifies the token path and the unresolvable reference string

#### Scenario: Multi-theme semantic tokens include `$extensions.com.daf.themes`

- **WHEN** a profile has `themes.modes: ["light", "dark"]` and theme-aware semantic alias overrides
- **THEN** each affected semantic token in `tokens/semantic.tokens.json` includes:
  ```json
  "$extensions": { "com.daf.themes": { "light": "{color.neutral.50}", "dark": "{color.neutral.950}" } }
  ```
- **AND** the `$extensions` block uses the key `"com.daf.themes"` — NOT the bare key `"themes"`

#### Scenario: Bare `themes` key rejected

- **WHEN** internal formatter logic attempts to write `$extensions.themes` (without the `com.daf` namespace)
- **THEN** a `ValueError` is raised during the self-check pass before the file is written
- **AND** the error message specifies that the correct key is `com.daf.themes`
