"""PrimitiveSpecGenerator — generates all 9 primitive spec YAMLs.

Agent 3 (Primitive Scaffolding Agent) in the DS Bootstrap Crew uses this
module to produce canonical specs/*.spec.yaml files for all 9 composition
primitives: Box, Stack, HStack, VStack, Grid, Text, Icon, Pressable, Divider,
Spacer, and ThemeProvider (11 files total).

Per the primitive-spec-generation spec (p06):
  - All specs must include: component, description, props, tokenBindings,
    compositionRules, a11yRequirements
  - token binding values use W3C DTCG alias format: {"$value": "{semantic.*}"}
  - Layout containers (Box/Stack/HStack/VStack/Grid/ThemeProvider): allowedChildren = "*"
  - Leaf primitives (Text/Icon/Divider/Spacer): allowedChildren = []
  - ThemeProvider: tokenBindings = []
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


_THEME_PROVIDER_SPEC: dict[str, Any] = {
    "component": "ThemeProvider",
    "description": (
        "React context provider that manages the active theme and brand for the "
        "design system. Applies theme and brand CSS classes to document.documentElement. "
        "Renders no visible UI and consumes no design tokens directly."
    ),
    "props": {
        "defaultTheme": {
            "type": "string",
            "required": False,
            "description": (
                "Initial theme name. Defaults to OS prefers-color-scheme preference "
                "if a matching name exists in availableThemes, otherwise availableThemes[0]."
            ),
        },
        "defaultBrand": {
            "type": "string | null",
            "required": False,
            "default": None,
            "description": "Initial brand name. null means no brand class is applied.",
        },
        "availableThemes": {
            "type": "string[]",
            "required": True,
            "description": "Valid theme names. ThemeProvider applies one theme-<name> class at a time.",
        },
        "availableBrands": {
            "type": "string[]",
            "required": True,
            "description": "Valid brand names. ThemeProvider applies zero or one brand-<name> class.",
        },
        "children": {
            "type": "React.ReactNode",
            "required": True,
            "description": "React children rendered within the theme context.",
        },
    },
    "tokenBindings": [],
    "exports": ["ThemeProvider", "useTheme"],
    "hooks": {
        "useTheme": {
            "returns": "ThemeContextValue",
            "description": (
                "Returns current theme state and setter functions from the nearest "
                "ThemeProvider. Throws if called outside a ThemeProvider."
            ),
            "interface": {
                "theme": "string",
                "brand": "string | null",
                "setTheme": "(theme: string) => void",
                "setBrand": "(brand: string | null) => void",
                "availableThemes": "string[]",
                "availableBrands": "string[]",
            },
        }
    },
    "notes": [
        "ThemeProvider renders a React.Fragment — no DOM wrapper.",
        "Theme/brand CSS classes are applied to document.documentElement.",
        "MediaQueryList listener for prefers-color-scheme is cleaned up on unmount.",
        "Client component only — no SSR support in v1.",
        "CSS class prefix 'theme-' is hardcoded for v1.",
    ],
    "compositionRules": {
        "allowedChildren": "*",
        "forbiddenNesting": [],
    },
    "a11yRequirements": {
        "role": None,
        "focusable": False,
        "ariaAttributes": [],
    },
}


def generate_theme_provider_spec(output_dir: str = ".") -> str:
    """Generate specs/ThemeProvider.spec.yaml in output_dir.

    Returns the absolute path to the written spec file.
    """
    specs_dir = Path(output_dir) / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    spec_path = specs_dir / "ThemeProvider.spec.yaml"
    with open(spec_path, "w", encoding="utf-8") as f:
        yaml.dump(
            _THEME_PROVIDER_SPEC,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
    return str(spec_path)


# ---------------------------------------------------------------------------
# Common props shared by all primitives
# ---------------------------------------------------------------------------

_COMMON_PROPS: dict[str, Any] = {
    "className": {
        "type": "string",
        "required": False,
        "description": "Additional CSS class names to apply to the root element.",
    },
    "style": {
        "type": "React.CSSProperties",
        "required": False,
        "description": "Inline style overrides — use sparingly; prefer token-based styling.",
    },
    "testId": {
        "type": "string",
        "required": False,
        "description": "data-testid attribute for automated testing.",
    },
}

# ---------------------------------------------------------------------------
# Primitive spec constants
# ---------------------------------------------------------------------------

_BOX_SPEC: dict[str, Any] = {
    "component": "Box",
    "description": (
        "The foundational layout primitive. Renders a div with full token-driven "
        "spacing, sizing, color, and border control. The universal building block "
        "for all layout compositions."
    ),
    "props": {
        **_COMMON_PROPS,
        "children": {
            "type": "React.ReactNode",
            "required": False,
            "description": "Content rendered inside the Box.",
        },
        "padding": {
            "type": "string | number",
            "required": False,
            "description": "Padding applied uniformly. Resolved against scale.spacing tokens.",
        },
        "paddingX": {
            "type": "string | number",
            "required": False,
            "description": "Horizontal padding (left + right).",
        },
        "paddingY": {
            "type": "string | number",
            "required": False,
            "description": "Vertical padding (top + bottom).",
        },
        "margin": {
            "type": "string | number",
            "required": False,
            "description": "Margin applied uniformly.",
        },
        "background": {
            "type": "string",
            "required": False,
            "description": "Background color token key.",
        },
        "borderRadius": {
            "type": "string",
            "required": False,
            "description": "Border radius token key.",
        },
        "as": {
            "type": "React.ElementType",
            "required": False,
            "default": "div",
            "description": "Polymorphic element type override.",
        },
    },
    "tokenBindings": [
        {"prop": "padding", "$value": "{scale.spacing.md}"},
        {"prop": "margin", "$value": "{scale.spacing.md}"},
        {"prop": "background", "$value": "{semantic.color.surface.default}"},
        {"prop": "borderRadius", "$value": "{semantic.border.radius.md}"},
    ],
    "compositionRules": {
        "allowedChildren": "*",
        "forbiddenNesting": [],
    },
    "a11yRequirements": {
        "role": None,
        "focusable": False,
        "ariaAttributes": [],
    },
}

_STACK_SPEC: dict[str, Any] = {
    "component": "Stack",
    "description": (
        "Vertical flex container with uniform gap between children. The default "
        "directional layout primitive for stacking elements along the block axis."
    ),
    "props": {
        **_COMMON_PROPS,
        "children": {
            "type": "React.ReactNode",
            "required": False,
            "description": "Elements to stack vertically.",
        },
        "gap": {
            "type": "string | number",
            "required": False,
            "description": "Gap between stacked items. Resolved against scale.spacing tokens.",
        },
        "align": {
            "type": "'start' | 'center' | 'end' | 'stretch'",
            "required": False,
            "default": "stretch",
            "description": "Cross-axis alignment (align-items).",
        },
        "justify": {
            "type": "'start' | 'center' | 'end' | 'between' | 'around'",
            "required": False,
            "default": "start",
            "description": "Main-axis justification (justify-content).",
        },
    },
    "tokenBindings": [
        {"prop": "gap", "$value": "{scale.spacing.md}"},
    ],
    "compositionRules": {
        "allowedChildren": "*",
        "forbiddenNesting": [],
    },
    "a11yRequirements": {
        "role": None,
        "focusable": False,
        "ariaAttributes": [],
    },
}

_HSTACK_SPEC: dict[str, Any] = {
    "component": "HStack",
    "description": (
        "Horizontal flex container. Arranges children along the inline axis with "
        "uniform gap. Shorthand for Stack with direction='horizontal'."
    ),
    "props": {
        **_COMMON_PROPS,
        "children": {
            "type": "React.ReactNode",
            "required": False,
            "description": "Elements to arrange horizontally.",
        },
        "gap": {
            "type": "string | number",
            "required": False,
            "description": "Gap between items. Resolved against scale.spacing tokens.",
        },
        "align": {
            "type": "'start' | 'center' | 'end' | 'baseline' | 'stretch'",
            "required": False,
            "default": "center",
            "description": "Cross-axis alignment.",
        },
        "justify": {
            "type": "'start' | 'center' | 'end' | 'between' | 'around'",
            "required": False,
            "default": "start",
            "description": "Main-axis justification.",
        },
        "wrap": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Whether children wrap to additional rows.",
        },
    },
    "tokenBindings": [
        {"prop": "gap", "$value": "{scale.spacing.md}"},
    ],
    "compositionRules": {
        "allowedChildren": "*",
        "forbiddenNesting": [],
    },
    "a11yRequirements": {
        "role": None,
        "focusable": False,
        "ariaAttributes": [],
    },
}

_VSTACK_SPEC: dict[str, Any] = {
    "component": "VStack",
    "description": (
        "Explicit vertical flex container (alias for Stack). Prefer Stack for most "
        "vertical layouts; use VStack when code clarity benefits from explicit naming."
    ),
    "props": {
        **_COMMON_PROPS,
        "children": {
            "type": "React.ReactNode",
            "required": False,
            "description": "Elements to stack vertically.",
        },
        "gap": {
            "type": "string | number",
            "required": False,
            "description": "Gap between items. Resolved against scale.spacing tokens.",
        },
        "align": {
            "type": "'start' | 'center' | 'end' | 'stretch'",
            "required": False,
            "default": "stretch",
            "description": "Cross-axis alignment.",
        },
        "justify": {
            "type": "'start' | 'center' | 'end' | 'between' | 'around'",
            "required": False,
            "default": "start",
            "description": "Main-axis justification.",
        },
    },
    "tokenBindings": [
        {"prop": "gap", "$value": "{scale.spacing.md}"},
    ],
    "compositionRules": {
        "allowedChildren": "*",
        "forbiddenNesting": [],
    },
    "a11yRequirements": {
        "role": None,
        "focusable": False,
        "ariaAttributes": [],
    },
}

_GRID_SPEC: dict[str, Any] = {
    "component": "Grid",
    "description": (
        "CSS Grid container. Provides a two-dimensional layout surface for "
        "building complex compositions with explicit column and row control."
    ),
    "props": {
        **_COMMON_PROPS,
        "children": {
            "type": "React.ReactNode",
            "required": False,
            "description": "Grid items.",
        },
        "columns": {
            "type": "number | string",
            "required": False,
            "default": 1,
            "description": "Number of columns or a grid-template-columns value.",
        },
        "rows": {
            "type": "number | string",
            "required": False,
            "description": "Number of rows or a grid-template-rows value.",
        },
        "gap": {
            "type": "string | number",
            "required": False,
            "description": "Gap between grid cells. Resolved against scale.spacing tokens.",
        },
        "columnGap": {
            "type": "string | number",
            "required": False,
            "description": "Gap between columns.",
        },
        "rowGap": {
            "type": "string | number",
            "required": False,
            "description": "Gap between rows.",
        },
    },
    "tokenBindings": [
        {"prop": "gap", "$value": "{scale.spacing.md}"},
        {"prop": "columnGap", "$value": "{scale.spacing.md}"},
        {"prop": "rowGap", "$value": "{scale.spacing.md}"},
    ],
    "compositionRules": {
        "allowedChildren": "*",
        "forbiddenNesting": [],
    },
    "a11yRequirements": {
        "role": None,
        "focusable": False,
        "ariaAttributes": [],
    },
}

_TEXT_SPEC: dict[str, Any] = {
    "component": "Text",
    "description": (
        "Typography primitive. Renders inline or block text with full token-driven "
        "font size, weight, line height, and color control. Maps to the typographic "
        "scale established by the Token Foundation Agent."
    ),
    "props": {
        **_COMMON_PROPS,
        "children": {
            "type": "React.ReactNode",
            "required": True,
            "description": "Text content or inline React nodes.",
        },
        "variant": {
            "type": "'display' | 'heading' | 'subheading' | 'body' | 'caption' | 'label'",
            "required": False,
            "default": "body",
            "description": "Typographic variant mapping to the modular scale.",
        },
        "as": {
            "type": "React.ElementType",
            "required": False,
            "default": "span",
            "description": "Polymorphic element type override (p, h1–h6, span, etc.).",
        },
        "color": {
            "type": "string",
            "required": False,
            "description": "Text color token key.",
        },
        "align": {
            "type": "'left' | 'center' | 'right' | 'justify'",
            "required": False,
            "description": "Text alignment.",
        },
        "truncate": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Truncate with ellipsis when text overflows.",
        },
    },
    "tokenBindings": [
        {"prop": "color", "$value": "{semantic.color.text.primary}"},
        {"prop": "fontSize", "$value": "{scale.typography.body.fontSize}"},
        {"prop": "lineHeight", "$value": "{scale.typography.body.lineHeight}"},
    ],
    "compositionRules": {
        "allowedChildren": [],
        "forbiddenNesting": [],
    },
    "a11yRequirements": {
        "role": None,
        "focusable": False,
        "ariaAttributes": ["aria-label"],
    },
}

_ICON_SPEC: dict[str, Any] = {
    "component": "Icon",
    "description": (
        "SVG icon primitive. Renders a named icon from the design system icon set "
        "at a token-controlled size and color. Always paired with an accessible "
        "label when used without adjacent text."
    ),
    "props": {
        **_COMMON_PROPS,
        "name": {
            "type": "string",
            "required": True,
            "description": "Icon name from the design system icon registry.",
        },
        "size": {
            "type": "'xs' | 'sm' | 'md' | 'lg' | 'xl'",
            "required": False,
            "default": "md",
            "description": "Icon size mapped to scale.icon tokens.",
        },
        "color": {
            "type": "string",
            "required": False,
            "description": "Icon fill color token key. Defaults to currentColor.",
        },
        "label": {
            "type": "string",
            "required": False,
            "description": "Accessible label (aria-label). Required when icon is standalone.",
        },
        "decorative": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "If true, marks icon as aria-hidden (purely decorative icon).",
        },
    },
    "tokenBindings": [
        {"prop": "size", "$value": "{scale.icon.md}"},
        {"prop": "color", "$value": "{semantic.color.icon.default}"},
    ],
    "compositionRules": {
        "allowedChildren": [],
        "forbiddenNesting": [],
    },
    "a11yRequirements": {
        "role": "img",
        "focusable": False,
        "ariaAttributes": ["aria-label", "aria-hidden"],
    },
}

_PRESSABLE_SPEC: dict[str, Any] = {
    "component": "Pressable",
    "description": (
        "Interactive touch/click target primitive. Provides press state management "
        "(idle → hover → active → disabled) without imposing visual styling. "
        "Compose inside to build Buttons, Links, Cards, and any other interactive surface."
    ),
    "props": {
        **_COMMON_PROPS,
        "children": {
            "type": "React.ReactNode | ((state: PressState) => React.ReactNode)",
            "required": True,
            "description": "Content or render-prop receiving press state.",
        },
        "onPress": {
            "type": "(event: PressEvent) => void",
            "required": False,
            "description": "Called when the pressable is activated.",
        },
        "onPressStart": {
            "type": "(event: PressEvent) => void",
            "required": False,
            "description": "Called when press interaction begins.",
        },
        "onPressEnd": {
            "type": "(event: PressEvent) => void",
            "required": False,
            "description": "Called when press interaction ends.",
        },
        "disabled": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Disabled state — prevents interaction and applies disabled styling.",
        },
        "as": {
            "type": "React.ElementType",
            "required": False,
            "default": "button",
            "description": "Polymorphic element override (button, a, div).",
        },
    },
    "tokenBindings": [
        {"prop": "focusRingColor", "$value": "{semantic.color.focus.ring}"},
        {"prop": "disabledOpacity", "$value": "{semantic.opacity.disabled}"},
    ],
    "compositionRules": {
        "allowedChildren": "*",
        "forbiddenNesting": ["Pressable"],
    },
    "a11yRequirements": {
        "role": "button",
        "focusable": True,
        "ariaAttributes": ["aria-disabled", "aria-pressed", "aria-label"],
    },
}

_DIVIDER_SPEC: dict[str, Any] = {
    "component": "Divider",
    "description": (
        "Horizontal or vertical rule for visually separating content. "
        "Renders an <hr> (horizontal) or a styled div (vertical). "
        "Uses a single semantic border token for consistent separation weight."
    ),
    "props": {
        **_COMMON_PROPS,
        "orientation": {
            "type": "'horizontal' | 'vertical'",
            "required": False,
            "default": "horizontal",
            "description": "Direction of the divider.",
        },
        "decorative": {
            "type": "boolean",
            "required": False,
            "default": True,
            "description": "If true, renders as aria-hidden (presentational separators).",
        },
    },
    "tokenBindings": [],
    "compositionRules": {
        "allowedChildren": [],
        "forbiddenNesting": [],
    },
    "a11yRequirements": {
        "role": "separator",
        "focusable": False,
        "ariaAttributes": ["aria-hidden", "aria-orientation"],
    },
}

_SPACER_SPEC: dict[str, Any] = {
    "component": "Spacer",
    "description": (
        "Flexible whitespace primitive. Inserts a token-controlled gap between "
        "siblings in a flex or grid container without adding semantic structure. "
        "Prefer gap/padding tokens on layout containers when possible."
    ),
    "props": {
        **_COMMON_PROPS,
        "size": {
            "type": "string | number",
            "required": False,
            "description": "Size of the space. Resolved against scale.spacing tokens.",
        },
        "axis": {
            "type": "'horizontal' | 'vertical' | 'both'",
            "required": False,
            "default": "vertical",
            "description": "Which axis the spacer expands along.",
        },
    },
    "tokenBindings": [],
    "compositionRules": {
        "allowedChildren": [],
        "forbiddenNesting": [],
    },
    "a11yRequirements": {
        "role": None,
        "focusable": False,
        "ariaAttributes": ["aria-hidden"],
    },
}

# ---------------------------------------------------------------------------
# Registry: all 11 primitive specs (name → dict)
# ---------------------------------------------------------------------------

_ALL_SPECS: dict[str, dict[str, Any]] = {
    "Box": _BOX_SPEC,
    "Stack": _STACK_SPEC,
    "HStack": _HSTACK_SPEC,
    "VStack": _VSTACK_SPEC,
    "Grid": _GRID_SPEC,
    "Text": _TEXT_SPEC,
    "Icon": _ICON_SPEC,
    "Pressable": _PRESSABLE_SPEC,
    "Divider": _DIVIDER_SPEC,
    "Spacer": _SPACER_SPEC,
    "ThemeProvider": _THEME_PROVIDER_SPEC,
}


# ---------------------------------------------------------------------------
# Public generator
# ---------------------------------------------------------------------------


def generate_all_primitive_specs(output_dir: str = ".") -> dict[str, str]:
    """Generate specs/*.spec.yaml for all 11 composition primitives.

    Writes 11 YAML files to ``<output_dir>/specs/``. Any existing files are
    overwritten with identical content (idempotent). The ``specs/``
    subdirectory is created if it does not exist.

    Args:
        output_dir: Base directory under which ``specs/`` will be created.

    Returns:
        A dict mapping each component name (e.g. ``"Box"``) to the absolute
        path of the written spec file (e.g. ``"/tmp/run/specs/Box.spec.yaml"``).
    """
    specs_dir = Path(output_dir) / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, str] = {}
    for component_name, spec_dict in _ALL_SPECS.items():
        spec_path = specs_dir / f"{component_name}.spec.yaml"
        with open(spec_path, "w", encoding="utf-8") as f:
            yaml.dump(
                spec_dict,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        result[component_name] = str(spec_path.resolve())

    return result


# ---------------------------------------------------------------------------
# CrewAI Tool
# ---------------------------------------------------------------------------


class _PrimitiveSpecGeneratorInput(BaseModel):
    output_dir: str = Field(
        default=".",
        description="Base directory under which specs/ will be created.",
    )


class PrimitiveSpecGenerator(BaseTool):
    """CrewAI tool that generates all 11 primitive spec YAMLs in one call.

    Agent 3 (Primitive Scaffolding Agent) uses this tool to fulfill Task T3:
    write canonical specs/*.spec.yaml files for all 9 composition primitives
    plus ThemeProvider. The tool is fully deterministic — no LLM calls.
    """

    name: str = "PrimitiveSpecGenerator"
    description: str = (
        "Generate canonical spec YAML files for all 11 design-system primitives "
        "(Box, Stack, HStack, VStack, Grid, Text, Icon, Pressable, Divider, Spacer, "
        "ThemeProvider) in the given output directory. Returns a summary string "
        "describing how many files were written and where."
    )
    args_schema: type[BaseModel] = _PrimitiveSpecGeneratorInput

    def _run(self, output_dir: str = ".", **kwargs: Any) -> str:
        result = generate_all_primitive_specs(output_dir)
        n = len(result)
        specs_dir = str(Path(output_dir).resolve() / "specs")
        return f"Generated {n} primitive specs in {specs_dir}"
