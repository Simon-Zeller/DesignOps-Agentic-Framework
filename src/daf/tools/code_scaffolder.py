"""Code Scaffolder — renders TSX, test, and story file triplets from intent manifests."""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# TSX template
# ---------------------------------------------------------------------------
_TSX_TEMPLATE = """\
import React from 'react';
import type {{ CSSProperties }} from 'react';

export interface {name}Props {{
  className?: string;
  style?: CSSProperties;
{variant_union}  children?: React.ReactNode;
  'data-testid'?: string;
{aria_props}}}

/**
 * {name} component.
 * Token bindings:
{token_comment} */
export function {name}({{
  className,
  style,
{variant_destructure}  children,
  'data-testid': testId = '{name_lower}',
{aria_destructure}}}: {name}Props) {{
  const computedStyle: CSSProperties = {{
{token_style}    ...style,
  }};

  return (
    <div
      className={{className}}
      style={{computedStyle}}
      data-testid={{testId}}
{aria_attrs}    >
      {{children}}
    </div>
  );
}}
"""

_STORY_TEMPLATE = """\
import type {{ Meta, StoryObj }} from '@storybook/react';
import {{ {name} }} from './{name}';

const meta: Meta<typeof {name}> = {{
  title: 'Components/{name}',
  component: {name},
}};

export default meta;
type Story = StoryObj<typeof {name}>;

{story_exports}
"""

_TEST_TEMPLATE = """\
import React from 'react';
import {{ render, screen }} from '@testing-library/react';
import {{ {name} }} from './{name}';

describe('{name}', () => {{
  it('renders without crashing', () => {{
    render(<{name} />);
    expect(screen.getByTestId('{name_lower}')).toBeInTheDocument();
  }});

{variant_tests}
}});

// @accessibility-placeholder"""


def _pascal_to_camel(name: str) -> str:
    return name[0].lower() + name[1:] if name else name


def scaffold_tsx(manifest: dict[str, Any]) -> str:
    """Render a TSX component file from an intent manifest."""
    name = manifest["component_name"]
    name_lower = _pascal_to_camel(name)
    token_bindings = manifest.get("token_bindings", [])
    aria = manifest.get("aria", {})
    variants = manifest.get("variants", [])

    token_comment_lines = "\n".join(
        f" *   {b['key']}: {b['token']}" for b in token_bindings
    )
    token_style_lines = "\n".join(
        f"    // {b['key']}: tokens['{b['token']}']," for b in token_bindings
    )
    aria_attrs_lines = ""
    aria_props_lines = ""
    aria_destructure_lines = ""
    if aria.get("role") and aria["role"] not in ("generic", ""):
        aria_props_lines = f"  role?: string;\n  'aria-label'?: string;\n"
        aria_destructure_lines = "  role,\n  'aria-label': ariaLabel,\n"
        aria_attrs_lines = "      role={role}\n      aria-label={ariaLabel}\n"

    variant_union = ""
    variant_destructure = ""
    if variants:
        union = " | ".join(f"'{v}'" for v in variants)
        variant_union = f"  variant?: {union};\n"
        variant_destructure = "  variant,\n"

    return _TSX_TEMPLATE.format(
        name=name,
        name_lower=name_lower,
        token_comment=token_comment_lines or " *   (none)",
        token_style=token_style_lines + "\n" if token_style_lines else "",
        aria_props=aria_props_lines,
        aria_destructure=aria_destructure_lines,
        aria_attrs=aria_attrs_lines,
        variant_union=variant_union,
        variant_destructure=variant_destructure,
    )


def scaffold_stories(manifest: dict[str, Any]) -> str:
    """Render a Storybook CSF3 stories file from an intent manifest."""
    name = manifest["component_name"]
    variants = manifest.get("variants", [])

    story_exports: list[str] = []
    for variant in variants:
        export_name = variant[0].upper() + variant[1:]
        story_exports.append(
            f"export const {export_name}: Story = {{\n"
            f"  args: {{ variant: '{variant}' }},\n"
            f"}};"
        )

    if not story_exports:
        story_exports.append(
            f"export const Default: Story = {{\n"
            f"  args: {{}},\n"
            f"}};"
        )

    return _STORY_TEMPLATE.format(
        name=name,
        story_exports="\n\n".join(story_exports),
    )


def scaffold_tests(manifest: dict[str, Any]) -> str:
    """Render a Jest/RTL unit test file from an intent manifest."""
    name = manifest["component_name"]
    name_lower = _pascal_to_camel(name)
    variants = manifest.get("variants", [])

    variant_test_lines: list[str] = []
    for variant in variants:
        variant_test_lines.append(
            f"  it('renders {variant} variant', () => {{\n"
            f"    render(<{name} variant='{variant}' />);\n"
            f"    expect(screen.getByTestId('{name_lower}')).toBeInTheDocument();\n"
            f"  }});"
        )

    return _TEST_TEMPLATE.format(
        name=name,
        name_lower=name_lower,
        variant_tests="\n\n".join(variant_test_lines) + "\n" if variant_test_lines else "",
    )
