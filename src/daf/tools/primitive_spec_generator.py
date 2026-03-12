"""PrimitiveSpecGenerator — generates ThemeProvider.spec.yaml.

Agent 4 (Primitive Spec Generator) in the DS Bootstrap Crew produces a
ThemeProvider.spec.yaml that the Design-to-Code Crew (Phase 3) uses as the
canonical source for generating ThemeProvider.tsx and useTheme.ts.

Per the theme-provider spec (p05), the generated YAML must declare:
  - props: defaultTheme, defaultBrand, availableThemes, availableBrands, children
  - tokenBindings: []  (ThemeProvider consumes no design tokens)
  - exports: ["ThemeProvider", "useTheme"]
"""
from __future__ import annotations

from pathlib import Path

import yaml


_THEME_PROVIDER_SPEC: dict = {
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
