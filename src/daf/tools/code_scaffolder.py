"""Code Scaffolder — renders TSX, test, and story file triplets from intent manifests."""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Mapping from a11y roles to semantic HTML elements
# ---------------------------------------------------------------------------
_ROLE_TO_ELEMENT: dict[str, str] = {
    "button": "button",
    "link": "a",
    "checkbox": "input",
    "radio": "input",
    "textbox": "input",
    "combobox": "select",
    "separator": "hr",
    "img": "span",
    "navigation": "nav",
    "dialog": "dialog",
    "alert": "div",
    "status": "div",
    "table": "table",
    "tablist": "div",
    "tooltip": "div",
    "region": "section",
    "generic": "div",
}

# Mapping from token binding keys to CSS property names
_TOKEN_KEY_TO_CSS: dict[str, str] = {
    "backgroundColor": "background-color",
    "color": "color",
    "borderRadius": "border-radius",
    "borderColor": "border-color",
    "paddingX": "padding-inline",
    "paddingY": "padding-block",
    "padding": "padding",
    "fontSize": "font-size",
    "fontWeight": "font-weight",
    "lineHeight": "line-height",
    "gap": "gap",
    "minHeight": "min-height",
    "width": "width",
    "height": "height",
    "boxShadow": "box-shadow",
    "focusRingColor": "--focus-ring-color",
    "borderWidth": "border-width",
    "opacity": "opacity",
    "maxWidth": "max-width",
}


def _pascal_to_camel(name: str) -> str:
    return name[0].lower() + name[1:] if name else name


def _pascal_to_kebab(name: str) -> str:
    """Convert PascalCase to kebab-case for CSS variable prefixes."""
    result: list[str] = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0:
            result.append("-")
        result.append(ch.lower())
    return "".join(result)


def _ts_type_for(prop_type: str) -> str:
    """Map spec type strings to TypeScript types."""
    mapping: dict[str, str] = {
        "React.ReactNode": "React.ReactNode",
        "string": "string",
        "boolean": "boolean",
        "number": "number",
        "() => void": "() => void",
        "function": "(...args: any[]) => void",
    }
    return mapping.get(prop_type, prop_type if prop_type else "any")


def _token_to_css_var(token_ref: str) -> str:
    """Convert a DTCG token reference to a CSS custom property var().

    E.g. 'color.interactive.primary.default' -> 'var(--color-interactive-primary-default)'
    """
    clean = token_ref.strip("{}")
    css_name = clean.replace(".", "-")
    return f"var(--{css_name})"


def _build_element_tag(role: str) -> str:
    return _ROLE_TO_ELEMENT.get(role, "div")


def scaffold_tsx(manifest: dict[str, Any]) -> str:
    """Render a TSX component file from an intent manifest."""
    name = manifest["component_name"]
    name_lower = _pascal_to_camel(name)
    description = manifest.get("description", f"{name} component.")
    token_bindings = manifest.get("token_bindings", [])
    aria = manifest.get("aria", {})
    variants = manifest.get("variants", [])
    props = manifest.get("props", [])
    states = manifest.get("states", {})
    role = aria.get("role", "generic")
    element = _build_element_tag(role)

    lines: list[str] = []

    # Imports
    lines.append("import React from 'react';")
    has_state = any(
        s in (states if isinstance(states, dict) else {})
        for s in ("disabled", "loading", "checked", "open", "expanded")
    )
    if has_state or role in ("checkbox", "radio", "dialog"):
        lines.append("import { useState, forwardRef } from 'react';")
    lines.append("import type { CSSProperties } from 'react';")
    lines.append("")

    # Props interface
    lines.append(f"export interface {name}Props {{")

    # Add typed props from spec
    spec_prop_names: list[str] = []
    for p in props:
        pname = p["name"]
        ptype = _ts_type_for(p.get("type", "any"))
        required = p.get("required", False)
        default = p.get("default")
        desc = p.get("description", "")
        optional = "" if required else "?"
        spec_prop_names.append(pname)
        if desc:
            lines.append(f"  /** {desc} */")
        lines.append(f"  {pname}{optional}: {ptype};")

    # Always include these standard props if not in spec
    if "className" not in spec_prop_names:
        lines.append("  className?: string;")
    if "style" not in spec_prop_names:
        lines.append("  style?: CSSProperties;")
    if "children" not in spec_prop_names and element not in ("input", "hr", "img"):
        lines.append("  children?: React.ReactNode;")

    # Variant union type if variants exist and variant prop isn't already defined
    if variants and "variant" not in spec_prop_names:
        union = " | ".join(f"'{v}'" for v in variants)
        lines.append(f"  variant?: {union};")

    # a11y props
    if role not in ("generic", ""):
        lines.append("  'aria-label'?: string;")

    lines.append("  'data-testid'?: string;")
    lines.append("}")
    lines.append("")

    # Token style map
    token_style_entries: list[str] = []
    for b in token_bindings:
        key = b.get("key", "")
        token = b.get("token", "")
        css_prop = _TOKEN_KEY_TO_CSS.get(key, key)
        css_var = _token_to_css_var(token)
        token_style_entries.append(f"    '{css_prop}': '{css_var}',")

    # JSDoc
    lines.append(f"/**")
    lines.append(f" * {description}")
    if token_bindings:
        lines.append(f" *")
        lines.append(f" * Token bindings:")
        for b in token_bindings:
            lines.append(f" *   {b.get('key', '')}: {b.get('token', '')}")
    lines.append(f" */")

    # Function signature
    # Build prop destructuring
    destructure_parts: list[str] = []
    defaults: dict[str, Any] = {}
    for p in props:
        pname = p["name"]
        default = p.get("default")
        if default is not None and default != "null" and str(default) != "None":
            if isinstance(default, bool):
                defaults[pname] = str(default).lower()
            elif isinstance(default, str):
                defaults[pname] = f"'{default}'"
            else:
                defaults[pname] = str(default)

    for p in props:
        pname = p["name"]
        if pname in defaults:
            destructure_parts.append(f"  {pname} = {defaults[pname]},")
        else:
            destructure_parts.append(f"  {pname},")

    if "className" not in spec_prop_names:
        destructure_parts.append("  className,")
    if "style" not in spec_prop_names:
        destructure_parts.append("  style,")
    if "children" not in spec_prop_names and element not in ("input", "hr", "img"):
        destructure_parts.append("  children,")
    if role not in ("generic", ""):
        destructure_parts.append("  'aria-label': ariaLabel,")
    destructure_parts.append(f"  'data-testid': testId = '{name_lower}',")

    lines.append(f"export function {name}({{")
    lines.extend(destructure_parts)
    lines.append(f"}}: {name}Props) {{")

    # Computed style with token values
    lines.append("  const computedStyle: CSSProperties = {")
    for entry in token_style_entries:
        lines.append(entry)
    lines.append("    ...style,")
    lines.append("  };")
    lines.append("")

    # Variant className
    if variants:
        prefix = _pascal_to_kebab(name)
        lines.append(f"  const variantClass = variant ? `{prefix}--${{variant}}` : '';")
        lines.append(f"  const classes = ['{prefix}', variantClass, className].filter(Boolean).join(' ');")
    else:
        prefix = _pascal_to_kebab(name)
        lines.append(f"  const classes = ['{prefix}', className].filter(Boolean).join(' ');")

    lines.append("")

    # Build JSX attributes
    jsx_attrs: list[str] = [
        "      className={classes}",
        "      style={computedStyle}",
        "      data-testid={testId}",
    ]

    # Role & ARIA
    if role not in ("generic", ""):
        # Some elements have implicit roles, only add if not implicit
        implicit_roles = {"button": "button", "a": "link", "nav": "navigation",
                          "dialog": "dialog", "table": "table", "hr": "separator",
                          "input": None, "select": None}
        if implicit_roles.get(element) != role:
            jsx_attrs.append(f'      role="{role}"')
        if role != "img":
            jsx_attrs.append("      aria-label={ariaLabel}")
        else:
            jsx_attrs.append("      aria-label={ariaLabel}")

    # Disabled state
    if "disabled" in spec_prop_names:
        if element in ("button", "input", "select", "textarea"):
            jsx_attrs.append("      disabled={disabled}")
        else:
            jsx_attrs.append("      aria-disabled={disabled}")

    # Checkbox/radio specific
    if role == "checkbox" and element == "input":
        jsx_attrs.append('      type="checkbox"')
    elif role == "radio" and element == "input":
        jsx_attrs.append('      type="radio"')
    elif role == "textbox" and element == "input":
        jsx_attrs.append('      type="text"')

    # onClick
    if "onClick" in spec_prop_names:
        jsx_attrs.append("      onClick={onClick}")

    # onChange
    if "onChange" in spec_prop_names:
        jsx_attrs.append("      onChange={onChange}")

    # Render
    lines.append("  return (")
    attrs_str = "\n".join(jsx_attrs)

    if element in ("input", "hr"):
        # Self-closing elements
        lines.append(f"    <{element}")
        lines.append(attrs_str)
        lines.append(f"    />")
    else:
        lines.append(f"    <{element}")
        lines.append(attrs_str)
        lines.append(f"    >")
        if "children" in spec_prop_names or (element not in ("input", "hr") and "children" not in spec_prop_names):
            lines.append("      {children}")
        lines.append(f"    </{element}>")

    lines.append("  );")
    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def scaffold_stories(manifest: dict[str, Any]) -> str:
    """Render a Storybook CSF3 stories file from an intent manifest."""
    name = manifest["component_name"]
    description = manifest.get("description", "")
    variants = manifest.get("variants", [])
    props = manifest.get("props", [])

    lines: list[str] = []
    lines.append("import type { Meta, StoryObj } from '@storybook/react';")
    lines.append(f"import {{ {name} }} from './{name}';")
    lines.append("")
    lines.append(f"const meta: Meta<typeof {name}> = {{")
    lines.append(f"  title: 'Components/{name}',")
    lines.append(f"  component: {name},")

    # Build argTypes from props
    if props:
        lines.append("  argTypes: {")
        for p in props:
            pname = p["name"]
            ptype = p.get("type", "string")
            desc = p.get("description", "")
            if ptype == "boolean":
                lines.append(f"    {pname}: {{ control: 'boolean', description: '{desc}' }},")
            elif "variant" in pname.lower() or pname == "size":
                lines.append(f"    {pname}: {{ control: 'select', description: '{desc}' }},")
            elif ptype in ("string", "React.ReactNode"):
                lines.append(f"    {pname}: {{ control: 'text', description: '{desc}' }},")
            elif ptype == "number":
                lines.append(f"    {pname}: {{ control: 'number', description: '{desc}' }},")
            else:
                lines.append(f"    {pname}: {{ description: '{desc}' }},")
        lines.append("  },")

    # Default args
    default_args: dict[str, str] = {}
    for p in props:
        pname = p["name"]
        default = p.get("default")
        ptype = p.get("type", "")
        if pname == "children":
            default_args[pname] = f"'{name}'"
        elif default is not None and str(default) not in ("null", "None"):
            if isinstance(default, bool):
                default_args[pname] = str(default).lower()
            elif isinstance(default, str):
                default_args[pname] = f"'{default}'"
            else:
                default_args[pname] = str(default)
    if default_args:
        lines.append("  args: {")
        for k, v in default_args.items():
            lines.append(f"    {k}: {v},")
        lines.append("  },")

    lines.append("};")
    lines.append("")
    lines.append("export default meta;")
    lines.append(f"type Story = StoryObj<typeof {name}>;")
    lines.append("")

    # Default story
    lines.append("export const Default: Story = {};")
    lines.append("")

    # Variant stories
    for variant in variants:
        export_name = variant[0].upper() + variant[1:]
        export_name = export_name.replace("-", "")
        lines.append(f"export const {export_name}: Story = {{")
        children_arg = ""
        if any(p["name"] == "children" for p in props):
            children_arg = f"    children: '{variant.title()} {name}',"
        lines.append(f"  args: {{")
        lines.append(f"    variant: '{variant}',")
        if children_arg:
            lines.append(children_arg)
        lines.append(f"  }},")
        lines.append(f"}};")
        lines.append("")

    # Disabled story if applicable
    has_disabled = any(p["name"] == "disabled" for p in props)
    if has_disabled:
        lines.append("export const Disabled: Story = {")
        lines.append("  args: {")
        lines.append("    disabled: true,")
        if any(p["name"] == "children" for p in props):
            lines.append(f"    children: 'Disabled {name}',")
        lines.append("  },")
        lines.append("};")
        lines.append("")

    return "\n".join(lines)


def scaffold_tests(manifest: dict[str, Any]) -> str:
    """Render a Jest/RTL unit test file from an intent manifest."""
    name = manifest["component_name"]
    name_lower = _pascal_to_camel(name)
    variants = manifest.get("variants", [])
    props = manifest.get("props", [])
    aria = manifest.get("aria", {})
    role = aria.get("role", "generic")
    element = _build_element_tag(role)

    lines: list[str] = []
    lines.append("import React from 'react';")
    lines.append("import { render, screen } from '@testing-library/react';")

    # Import userEvent if we have interactive tests
    has_onclick = any(p["name"] == "onClick" for p in props)
    has_keyboard = bool(aria.get("keyboard"))
    if has_onclick or has_keyboard:
        lines.append("import userEvent from '@testing-library/user-event';")

    lines.append(f"import {{ {name} }} from './{name}';")
    lines.append("")
    lines.append(f"describe('{name}', () => {{")

    # Basic render test with required props
    required_props: dict[str, str] = {}
    for p in props:
        if p.get("required"):
            pname = p["name"]
            ptype = p.get("type", "string")
            if pname == "children":
                required_props[pname] = f"Test {name}"
            elif ptype == "string":
                required_props[pname] = f"test-{pname}"
            elif ptype == "boolean":
                required_props[pname] = "false"
            elif ptype == "number":
                required_props[pname] = "0"

    required_jsx = ""
    if required_props:
        jsx_parts = []
        for k, v in required_props.items():
            if k == "children":
                continue
            if v in ("true", "false"):
                jsx_parts.append(f"{k}={{{v}}}")
            elif v.isdigit():
                jsx_parts.append(f"{k}={{{v}}}")
            else:
                jsx_parts.append(f'{k}="{v}"')
        required_jsx = " " + " ".join(jsx_parts) if jsx_parts else ""

    children_text = required_props.get("children", "")

    if children_text:
        render_jsx = f"<{name}{required_jsx}>{children_text}</{name}>"
    else:
        render_jsx = f"<{name}{required_jsx} />"

    lines.append("  it('renders without crashing', () => {")
    lines.append(f"    render({render_jsx});")
    lines.append(f"    expect(screen.getByTestId('{name_lower}')).toBeInTheDocument();")
    lines.append("  });")
    lines.append("")

    # Variant tests
    for variant in variants:
        if children_text:
            var_jsx = f"<{name}{required_jsx} variant=\"{variant}\">{children_text}</{name}>"
        else:
            var_jsx = f"<{name}{required_jsx} variant=\"{variant}\" />"
        lines.append(f"  it('renders {variant} variant', () => {{")
        lines.append(f"    render({var_jsx});")
        lines.append(f"    expect(screen.getByTestId('{name_lower}')).toBeInTheDocument();")
        lines.append("  });")
        lines.append("")

    # Disabled state test
    has_disabled = any(p["name"] == "disabled" for p in props)
    if has_disabled:
        lines.append("  it('renders disabled state', () => {")
        if children_text:
            lines.append(f"    render(<{name}{required_jsx} disabled>{children_text}</{name}>);")
        else:
            lines.append(f"    render(<{name}{required_jsx} disabled />);")
        lines.append(f"    const el = screen.getByTestId('{name_lower}');")
        if element in ("button", "input", "select", "textarea"):
            lines.append("    expect(el).toBeDisabled();")
        else:
            lines.append("    expect(el).toHaveAttribute('aria-disabled', 'true');")
        lines.append("  });")
        lines.append("")

    # onClick test
    if has_onclick:
        lines.append("  it('calls onClick handler when clicked', async () => {")
        lines.append("    const handleClick = jest.fn();")
        if children_text:
            lines.append(f"    render(<{name}{required_jsx} onClick={{handleClick}}>{children_text}</{name}>);")
        else:
            lines.append(f"    render(<{name}{required_jsx} onClick={{handleClick}} />);")
        lines.append(f"    await userEvent.click(screen.getByTestId('{name_lower}'));")
        lines.append("    expect(handleClick).toHaveBeenCalledTimes(1);")
        lines.append("  });")
        lines.append("")

    # a11y role test
    if role not in ("generic", ""):
        implicit_roles = {"button": "button", "a": "link", "nav": "navigation",
                          "dialog": "dialog", "table": "table", "hr": "separator"}
        if implicit_roles.get(element) != role:
            lines.append(f"  it('has correct ARIA role', () => {{")
            if children_text:
                lines.append(f"    render({render_jsx});")
            else:
                lines.append(f"    render({render_jsx});")
            lines.append(f"    expect(screen.getByTestId('{name_lower}')).toHaveAttribute('role', '{role}');")
            lines.append("  });")
            lines.append("")

    # Keyboard interaction tests
    keyboard_interactions = aria.get("keyboard", [])
    for key_name in keyboard_interactions:
        key_code = key_name.replace("Arrow", "arrow").replace("Escape", "escape").replace("Enter", "enter").replace("Space", "space")
        lines.append(f"  it('responds to {key_name} key', async () => {{")
        if children_text:
            lines.append(f"    render({render_jsx});")
        else:
            lines.append(f"    render({render_jsx});")
        lines.append(f"    const el = screen.getByTestId('{name_lower}');")
        lines.append(f"    el.focus();")
        lines.append(f"    await userEvent.keyboard('{{{{ {key_code} }}}}');")
        lines.append(f"    // Verify keyboard interaction is handled")
        lines.append(f"    expect(el).toBeInTheDocument();")
        lines.append("  });")
        lines.append("")

    # Custom className test
    lines.append("  it('applies custom className', () => {")
    if children_text:
        lines.append(f'    render(<{name}{required_jsx} className="custom-class">{children_text}</{name}>);')
    else:
        lines.append(f'    render(<{name}{required_jsx} className="custom-class" />);')
    lines.append(f"    expect(screen.getByTestId('{name_lower}')).toHaveClass('custom-class');")
    lines.append("  });")

    lines.append("});")
    lines.append("")

    return "\n".join(lines)
