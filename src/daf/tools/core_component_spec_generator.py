"""CoreComponentSpecGenerator — generates canonical spec YAMLs for all core UI components.

Agent 4 (Core Component Agent) in the DS Bootstrap Crew uses this module to produce
canonical specs/*.spec.yaml files for the three scope tiers:
  - starter        → 10 components
  - standard       → 19 components (starter + 9 delta)
  - comprehensive  → 26 components (standard + 7 delta)

Per the core-component-specs spec (p07):
  - All specs include: component, description, props, variants, states,
    tokenBindings, compositionRules, a11yRequirements
  - props entries include: type, required, default
  - token binding values use W3C DTCG alias format: {"$value": "{semantic.*}"}
  - composesFrom lists only primitive names (Box, Stack, Grid, Text, Icon,
    Pressable, Divider, Spacer, ThemeProvider)
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Scope tier component name lists
# ---------------------------------------------------------------------------

_STARTER_COMPONENTS: list[str] = [
    "Button", "Input", "Checkbox", "Radio", "Select",
    "Card", "Badge", "Avatar", "Alert", "Modal",
]

_STANDARD_DELTA: list[str] = [
    "Table", "Tabs", "Accordion", "Tooltip", "Toast",
    "Dropdown", "Pagination", "Breadcrumb", "Navigation",
]

_COMPREHENSIVE_DELTA: list[str] = [
    "DatePicker", "DataGrid", "TreeView", "Drawer",
    "Stepper", "FileUpload", "RichText",
]

SCOPE_TIERS: dict[str, list[str]] = {
    "starter": _STARTER_COMPONENTS,
    "standard": _STARTER_COMPONENTS + _STANDARD_DELTA,
    "comprehensive": _STARTER_COMPONENTS + _STANDARD_DELTA + _COMPREHENSIVE_DELTA,
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _tb(prop: str, alias: str) -> dict[str, str]:
    """Create a single token binding entry in DTCG alias format."""
    return {"prop": prop, "$value": f"{{{alias}}}"}


# ---------------------------------------------------------------------------
# Starter component spec dicts
# ---------------------------------------------------------------------------

_BUTTON_SPEC: dict[str, Any] = {
    "component": "Button",
    "description": (
        "An interactive button element that triggers actions or navigates. "
        "Supports multiple visual variants and semantic states. "
        "Built on the Pressable primitive for accessibility."
    ),
    "props": {
        "children": {
            "type": "React.ReactNode",
            "required": True,
            "default": None,
            "description": "Button label or content.",
        },
        "variant": {
            "type": "string",
            "required": False,
            "default": "primary",
            "description": "Visual style variant.",
        },
        "size": {
            "type": "string",
            "required": False,
            "default": "md",
            "description": "Size scale: sm | md | lg.",
        },
        "disabled": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Whether the button is non-interactive.",
        },
        "loading": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Shows a loading indicator and disables interaction.",
        },
        "onClick": {
            "type": "() => void",
            "required": False,
            "default": None,
            "description": "Click / Enter / Space handler.",
        },
        "type": {
            "type": "string",
            "required": False,
            "default": "button",
            "description": "HTML button type: button | submit | reset.",
        },
    },
    "variants": ["primary", "secondary", "ghost", "danger", "link"],
    "states": {
        "default": "Resting state with primary fill or stroke.",
        "hover": "Darkened or highlighted background on cursor hover.",
        "focus": "Visible focus ring using focus.ring token.",
        "disabled": "Reduced opacity; pointer-events: none.",
        "loading": "Spinner visible; interaction blocked.",
    },
    "tokenBindings": [
        _tb("backgroundColor", "color.interactive.primary.default"),
        _tb("color", "color.interactive.primary.foreground"),
        _tb("borderRadius", "scale.border-radius.md"),
        _tb("paddingX", "scale.spacing.component.padding.x.md"),
        _tb("paddingY", "scale.spacing.component.padding.y.sm"),
        _tb("fontSize", "scale.typography.size.body.md"),
        _tb("focusRingColor", "color.focus.ring"),
    ],
    "compositionRules": {
        "composesFrom": ["Pressable", "Text", "Icon"],
        "allowedChildren": ["Text", "Icon"],
        "forbiddenNesting": ["Button"],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "button",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "Enter", "action": "Activates the button"},
            {"key": "Space", "action": "Activates the button"},
        ],
        "ariaAttributes": ["aria-disabled", "aria-busy"],
    },
}


_INPUT_SPEC: dict[str, Any] = {
    "component": "Input",
    "description": (
        "A single-line text input field. Supports controlled and uncontrolled modes, "
        "validation states, and left/right icon slots."
    ),
    "props": {
        "value": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Controlled value.",
        },
        "defaultValue": {
            "type": "string",
            "required": False,
            "default": "",
            "description": "Uncontrolled initial value.",
        },
        "placeholder": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Placeholder text shown when value is empty.",
        },
        "disabled": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Whether the input is non-interactive.",
        },
        "onChange": {
            "type": "(value: string) => void",
            "required": False,
            "default": None,
            "description": "Called on every keystroke with the new value.",
        },
        "type": {
            "type": "string",
            "required": False,
            "default": "text",
            "description": "HTML input type: text | email | password | number | url.",
        },
        "id": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Associates with a <label> element.",
        },
    },
    "variants": ["default", "filled", "outline"],
    "states": {
        "default": "Resting state with border-color.input.default token.",
        "hover": "Heightened border color.",
        "focus": "Highlighted border and focus ring.",
        "disabled": "Dimmed background; reduced opacity.",
        "error": "Error border color and error icon.",
        "success": "Success border color and success icon.",
    },
    "tokenBindings": [
        _tb("borderColor", "color.border.input.default"),
        _tb("backgroundColor", "color.interactive.surface.input"),
        _tb("color", "color.text.primary"),
        _tb("placeholderColor", "color.text.placeholder"),
        _tb("borderRadius", "scale.border-radius.sm"),
        _tb("paddingX", "scale.spacing.component.padding.x.md"),
        _tb("paddingY", "scale.spacing.component.padding.y.sm"),
        _tb("focusRingColor", "color.focus.ring"),
        _tb("errorBorderColor", "color.semantic.error.border"),
        _tb("successBorderColor", "color.semantic.success.border"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Text", "Icon"],
        "allowedChildren": [],
        "forbiddenNesting": ["Input"],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "textbox",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "Tab", "action": "Moves focus to/from the input"},
            {"key": "Escape", "action": "Clears value if a clear button is present"},
        ],
        "ariaAttributes": ["aria-label", "aria-describedby", "aria-invalid", "aria-required"],
    },
}


_CHECKBOX_SPEC: dict[str, Any] = {
    "component": "Checkbox",
    "description": (
        "A binary toggle control that allows the user to select or deselect an option. "
        "Supports indeterminate state for parent checkboxes in a tree."
    ),
    "props": {
        "checked": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Controlled checked state.",
        },
        "defaultChecked": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Uncontrolled initial checked state.",
        },
        "indeterminate": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Visual indeterminate state (partially selected).",
        },
        "disabled": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Whether the checkbox is non-interactive.",
        },
        "onChange": {
            "type": "(checked: boolean) => void",
            "required": False,
            "default": None,
            "description": "Called when the checked state changes.",
        },
        "label": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Visible label text associated with the checkbox.",
        },
    },
    "variants": ["default", "indeterminate"],
    "states": {
        "default": "Unchecked resting state.",
        "hover": "Highlighted border and background.",
        "focus": "Visible focus ring.",
        "disabled": "Dimmed and non-interactive.",
        "checked": "Filled with checkmark icon.",
        "error": "Error border color; invalid selection.",
        "success": "Confirmation state after successful form submission.",
    },
    "tokenBindings": [
        _tb("borderColor", "color.border.interactive.default"),
        _tb("backgroundColor", "color.interactive.surface.control"),
        _tb("checkedBackgroundColor", "color.interactive.primary.default"),
        _tb("checkmarkColor", "color.interactive.primary.foreground"),
        _tb("focusRingColor", "color.focus.ring"),
        _tb("errorBorderColor", "color.semantic.error.border"),
        _tb("successBorderColor", "color.semantic.success.border"),
    ],
    "compositionRules": {
        "composesFrom": ["Pressable", "Box", "Icon", "Text"],
        "allowedChildren": [],
        "forbiddenNesting": ["Checkbox"],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "checkbox",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "Space", "action": "Toggles the checked state"},
            {"key": "Tab", "action": "Moves focus to/from the checkbox"},
        ],
        "ariaAttributes": ["aria-checked", "aria-disabled", "aria-label", "aria-describedby"],
    },
}


_RADIO_SPEC: dict[str, Any] = {
    "component": "Radio",
    "description": (
        "A mutually exclusive selection control. Always used within a RadioGroup "
        "to enforce single-selection semantics."
    ),
    "props": {
        "checked": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Controlled checked state.",
        },
        "defaultChecked": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Uncontrolled initial checked state.",
        },
        "value": {
            "type": "string",
            "required": True,
            "default": None,
            "description": "The value submitted in a form when this radio is selected.",
        },
        "disabled": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Whether the radio is non-interactive.",
        },
        "onChange": {
            "type": "(value: string) => void",
            "required": False,
            "default": None,
            "description": "Called when this radio is selected.",
        },
        "label": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Visible label text.",
        },
    },
    "variants": ["default"],
    "states": {
        "default": "Unselected resting state.",
        "hover": "Highlighted border.",
        "focus": "Visible focus ring.",
        "disabled": "Dimmed and non-interactive.",
        "checked": "Filled dot visible inside the radio circle.",
        "error": "Error border color.",
        "success": "Success state after form validation.",
    },
    "tokenBindings": [
        _tb("borderColor", "color.border.interactive.default"),
        _tb("backgroundColor", "color.interactive.surface.control"),
        _tb("dotColor", "color.interactive.primary.default"),
        _tb("focusRingColor", "color.focus.ring"),
        _tb("errorBorderColor", "color.semantic.error.border"),
        _tb("successBorderColor", "color.semantic.success.border"),
    ],
    "compositionRules": {
        "composesFrom": ["Pressable", "Box", "Icon", "Text"],
        "allowedChildren": [],
        "forbiddenNesting": ["Radio"],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "radio",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "Space", "action": "Selects the radio button"},
            {"key": "ArrowUp", "action": "Moves selection to previous radio in group"},
            {"key": "ArrowDown", "action": "Moves selection to next radio in group"},
        ],
        "ariaAttributes": ["aria-checked", "aria-disabled", "aria-label"],
    },
}


_SELECT_SPEC: dict[str, Any] = {
    "component": "Select",
    "description": (
        "A dropdown selection widget that allows the user to choose one option "
        "from a list. Opens a listbox on activation."
    ),
    "props": {
        "value": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Controlled selected value.",
        },
        "defaultValue": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Uncontrolled initial selected value.",
        },
        "options": {
            "type": "Array<{value: string; label: string; disabled?: boolean}>",
            "required": True,
            "default": None,
            "description": "List of selectable options.",
        },
        "placeholder": {
            "type": "string",
            "required": False,
            "default": "Select an option",
            "description": "Text shown when no option is selected.",
        },
        "disabled": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Disables the entire select.",
        },
        "onChange": {
            "type": "(value: string) => void",
            "required": False,
            "default": None,
            "description": "Called when the selected value changes.",
        },
    },
    "variants": ["default", "outline", "filled"],
    "states": {
        "default": "Closed, no selection or placeholder shown.",
        "hover": "Highlighted trigger border.",
        "focus": "Visible focus ring on trigger.",
        "disabled": "Dimmed trigger; listbox cannot be opened.",
        "open": "Listbox visible with option list.",
        "error": "Error border on trigger.",
        "success": "Success border after validation.",
    },
    "tokenBindings": [
        _tb("borderColor", "color.border.input.default"),
        _tb("backgroundColor", "color.interactive.surface.input"),
        _tb("color", "color.text.primary"),
        _tb("dropdownBackgroundColor", "color.surface.overlay"),
        _tb("focusRingColor", "color.focus.ring"),
        _tb("errorBorderColor", "color.semantic.error.border"),
        _tb("successBorderColor", "color.semantic.success.border"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Text", "Icon", "Pressable"],
        "allowedChildren": [],
        "forbiddenNesting": ["Select"],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "combobox",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "Enter", "action": "Opens or closes the listbox; selects focused option"},
            {"key": "Space", "action": "Opens the listbox"},
            {"key": "ArrowDown", "action": "Moves focus to next option in listbox"},
            {"key": "ArrowUp", "action": "Moves focus to previous option in listbox"},
            {"key": "Escape", "action": "Closes the listbox without selection"},
            {"key": "Home", "action": "Moves focus to first option"},
            {"key": "End", "action": "Moves focus to last option"},
        ],
        "ariaAttributes": [
            "aria-haspopup", "aria-expanded", "aria-controls",
            "aria-activedescendant", "aria-label",
        ],
    },
}


_CARD_SPEC: dict[str, Any] = {
    "component": "Card",
    "description": (
        "A surface container that groups related content and actions. "
        "Provides elevation, border, and radius tokens. "
        "Accepts arbitrary children through named slots or direct children."
    ),
    "props": {
        "children": {
            "type": "React.ReactNode",
            "required": True,
            "default": None,
            "description": "Card body content.",
        },
        "elevation": {
            "type": "string",
            "required": False,
            "default": "md",
            "description": "Shadow elevation: none | sm | md | lg.",
        },
        "padding": {
            "type": "string",
            "required": False,
            "default": "md",
            "description": "Internal padding token key.",
        },
        "onClick": {
            "type": "() => void",
            "required": False,
            "default": None,
            "description": "Makes the card interactive (clickable card pattern).",
        },
    },
    "variants": ["default", "outlined", "elevated", "filled"],
    "states": {
        "default": "Resting card surface.",
        "hover": "Slightly elevated shadow and border highlight (when interactive).",
        "focus": "Focus ring visible when card is interactive.",
    },
    "tokenBindings": [
        _tb("backgroundColor", "color.surface.card"),
        _tb("borderColor", "color.border.subtle"),
        _tb("borderRadius", "scale.border-radius.lg"),
        _tb("boxShadow", "scale.elevation.md"),
        _tb("padding", "scale.spacing.component.padding.x.md"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack"],
        "allowedChildren": "*",
        "forbiddenNesting": [],
        "slots": ["header", "body", "footer"],
    },
    "a11yRequirements": {
        "role": None,
        "focusable": False,
        "keyboardInteractions": [],
        "ariaAttributes": ["aria-label"],
    },
}


_BADGE_SPEC: dict[str, Any] = {
    "component": "Badge",
    "description": (
        "A compact status indicator that communicates categorical information. "
        "Non-interactive; used to annotate other UI elements with labels or counts."
    ),
    "props": {
        "label": {
            "type": "string",
            "required": True,
            "default": None,
            "description": "Text content of the badge.",
        },
        "variant": {
            "type": "string",
            "required": False,
            "default": "default",
            "description": "Semantic variant: default | info | success | warning | error.",
        },
        "size": {
            "type": "string",
            "required": False,
            "default": "md",
            "description": "Size: sm | md.",
        },
    },
    "variants": ["default", "info", "success", "warning", "error"],
    "states": {
        "default": "Base appearance.",
    },
    "tokenBindings": [
        _tb("backgroundColor", "color.semantic.badge.default.background"),
        _tb("color", "color.semantic.badge.default.foreground"),
        _tb("borderRadius", "scale.border-radius.full"),
        _tb("paddingX", "scale.spacing.component.padding.x.sm"),
        _tb("fontSize", "scale.typography.size.label.sm"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Text"],
        "allowedChildren": [],
        "forbiddenNesting": ["Badge"],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "status",
        "focusable": False,
        "keyboardInteractions": [],
        "ariaAttributes": ["aria-label"],
    },
}


_AVATAR_SPEC: dict[str, Any] = {
    "component": "Avatar",
    "description": (
        "Displays a user's photo, initials, or a fallback icon. "
        "Used in profiles, comments, team members, and navigation."
    ),
    "props": {
        "src": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Image URL.",
        },
        "alt": {
            "type": "string",
            "required": False,
            "default": "",
            "description": "Alt text for the image.",
        },
        "initials": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Fallback initials shown when no image is available.",
        },
        "size": {
            "type": "string",
            "required": False,
            "default": "md",
            "description": "Avatar size: xs | sm | md | lg | xl.",
        },
        "variant": {
            "type": "string",
            "required": False,
            "default": "circle",
            "description": "Shape variant: circle | square.",
        },
    },
    "variants": ["circle", "square"],
    "states": {
        "default": "Resting state showing image or initials.",
        "loading": "Skeleton shimmer while image loads.",
    },
    "tokenBindings": [
        _tb("backgroundColor", "color.surface.avatar.default"),
        _tb("color", "color.text.inverse"),
        _tb("borderRadius", "scale.border-radius.full"),
        _tb("fontSize", "scale.typography.size.label.md"),
        _tb("size", "scale.sizing.avatar.md"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Text", "Icon"],
        "allowedChildren": [],
        "forbiddenNesting": ["Avatar"],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "img",
        "focusable": False,
        "keyboardInteractions": [],
        "ariaAttributes": ["aria-label"],
    },
}


_ALERT_SPEC: dict[str, Any] = {
    "component": "Alert",
    "description": (
        "A contextual notification banner that communicates important information "
        "inline on the page. Come in semantic variants: info, success, warning, error."
    ),
    "props": {
        "title": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Optional bold heading.",
        },
        "description": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Detail message text.",
        },
        "variant": {
            "type": "string",
            "required": False,
            "default": "info",
            "description": "Semantic variant: info | success | warning | error.",
        },
        "onDismiss": {
            "type": "() => void",
            "required": False,
            "default": None,
            "description": "If provided, renders a dismiss button.",
        },
    },
    "variants": ["info", "success", "warning", "error"],
    "states": {
        "default": "Visible alert at rest.",
        "dismissed": "Alert removed from DOM after dismiss animation.",
    },
    "tokenBindings": [
        _tb("backgroundColor", "color.semantic.alert.info.background"),
        _tb("borderColor", "color.semantic.alert.info.border"),
        _tb("color", "color.semantic.alert.info.foreground"),
        _tb("borderRadius", "scale.border-radius.md"),
        _tb("paddingX", "scale.spacing.component.padding.x.md"),
        _tb("paddingY", "scale.spacing.component.padding.y.sm"),
        _tb("iconColor", "color.semantic.alert.info.icon"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Text", "Icon"],
        "allowedChildren": [],
        "forbiddenNesting": [],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "alert",
        "focusable": False,
        "keyboardInteractions": [],
        "ariaAttributes": ["aria-live", "aria-atomic"],
    },
}


_MODAL_SPEC: dict[str, Any] = {
    "component": "Modal",
    "description": (
        "An overlay dialog that captures user focus for critical interactions or "
        "confirmations. Features a backdrop, header, body, and footer slots. "
        "Traps focus while open and restores focus to the trigger on close."
    ),
    "props": {
        "open": {
            "type": "boolean",
            "required": True,
            "default": False,
            "description": "Whether the modal is visible.",
        },
        "onClose": {
            "type": "() => void",
            "required": True,
            "default": None,
            "description": "Called when the modal requests to be closed (Escape, backdrop click).",
        },
        "title": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Modal heading text.",
        },
        "size": {
            "type": "string",
            "required": False,
            "default": "md",
            "description": "Width variant: sm | md | lg | full.",
        },
        "children": {
            "type": "React.ReactNode",
            "required": False,
            "default": None,
            "description": "Modal body content.",
        },
    },
    "variants": ["default", "fullscreen", "centered"],
    "states": {
        "open": "Modal visible with backdrop.",
        "closed": "Modal removed from DOM or hidden.",
    },
    "tokenBindings": [
        _tb("backgroundColor", "color.surface.overlay"),
        _tb("borderRadius", "scale.border-radius.lg"),
        _tb("boxShadow", "scale.elevation.lg"),
        _tb("backdropColor", "color.overlay.backdrop"),
        _tb("paddingX", "scale.spacing.component.padding.x.lg"),
        _tb("paddingY", "scale.spacing.component.padding.y.md"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Text", "Pressable"],
        "allowedChildren": "*",
        "forbiddenNesting": ["Modal"],
        "slots": ["header", "body", "footer"],
    },
    "a11yRequirements": {
        "role": "dialog",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "Escape", "action": "Closes the modal"},
            {"key": "Tab", "action": "Cycles focus within modal (focus trap)"},
            {"key": "Shift+Tab", "action": "Reverse cycles focus within modal"},
        ],
        "ariaAttributes": ["aria-modal", "aria-labelledby", "aria-describedby"],
    },
}


# ---------------------------------------------------------------------------
# Standard-delta component spec dicts
# ---------------------------------------------------------------------------

_TABLE_SPEC: dict[str, Any] = {
    "component": "Table",
    "description": (
        "A data table for displaying tabular information with optional sorting, "
        "filtering, and row selection."
    ),
    "props": {
        "columns": {
            "type": "Array<{key: string; header: string; sortable?: boolean}>",
            "required": True,
            "default": None,
            "description": "Column definitions.",
        },
        "data": {
            "type": "Array<Record<string, unknown>>",
            "required": True,
            "default": None,
            "description": "Array of row data objects.",
        },
        "onSort": {
            "type": "(key: string, direction: 'asc' | 'desc') => void",
            "required": False,
            "default": None,
            "description": "Sort handler.",
        },
    },
    "variants": ["default", "striped", "compact"],
    "states": {
        "default": "Rendered table at rest.",
        "sortedAsc": "Column sorted ascending.",
        "sortedDesc": "Column sorted descending.",
        "rowHover": "Row highlighted on hover.",
        "rowSelected": "Row selected.",
    },
    "tokenBindings": [
        _tb("headerBackgroundColor", "color.surface.table.header"),
        _tb("rowBackgroundColor", "color.surface.table.row"),
        _tb("stripedRowBackgroundColor", "color.surface.table.row.alternate"),
        _tb("borderColor", "color.border.subtle"),
        _tb("color", "color.text.primary"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Text"],
        "allowedChildren": [],
        "forbiddenNesting": [],
        "slots": ["header", "body", "footer"],
    },
    "a11yRequirements": {
        "role": "table",
        "focusable": False,
        "keyboardInteractions": [
            {"key": "Tab", "action": "Moves focus to sortable column headers"},
            {"key": "Enter", "action": "Activates sort on focused column header"},
        ],
        "ariaAttributes": ["aria-sort", "aria-label", "aria-rowcount"],
    },
}


_TABS_SPEC: dict[str, Any] = {
    "component": "Tabs",
    "description": (
        "A tabbed navigation component for switching between multiple content panels. "
        "Follows the WAI-ARIA Tabs pattern."
    ),
    "props": {
        "items": {
            "type": "Array<{id: string; label: string; content: React.ReactNode}>",
            "required": True,
            "default": None,
            "description": "Tab definitions with labels and panel content.",
        },
        "activeTab": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Controlled active tab id.",
        },
        "onChange": {
            "type": "(id: string) => void",
            "required": False,
            "default": None,
            "description": "Called when active tab changes.",
        },
    },
    "variants": ["default", "enclosed", "underline"],
    "states": {
        "default": "Tabs at rest.",
        "active": "Selected tab with active indicator.",
        "hover": "Hovered tab indicator.",
        "focus": "Focused tab ring.",
        "disabled": "Non-interactive dimmed tab.",
    },
    "tokenBindings": [
        _tb("activeTabColor", "color.interactive.primary.default"),
        _tb("tabTextColor", "color.text.secondary"),
        _tb("activeTabTextColor", "color.text.primary"),
        _tb("borderColor", "color.border.subtle"),
        _tb("focusRingColor", "color.focus.ring"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Pressable", "Text"],
        "allowedChildren": "*",
        "forbiddenNesting": ["Tabs"],
        "slots": ["tablist", "tabpanel"],
    },
    "a11yRequirements": {
        "role": "tablist",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "ArrowRight", "action": "Moves focus to next tab"},
            {"key": "ArrowLeft", "action": "Moves focus to previous tab"},
            {"key": "Home", "action": "Moves focus to first tab"},
            {"key": "End", "action": "Moves focus to last tab"},
            {"key": "Enter", "action": "Activates focused tab"},
        ],
        "ariaAttributes": ["aria-selected", "aria-controls", "aria-labelledby"],
    },
}


_ACCORDION_SPEC: dict[str, Any] = {
    "component": "Accordion",
    "description": (
        "An expandable/collapsible list of sections. Each section has a trigger "
        "and a content panel. Supports single or multiple open panels."
    ),
    "props": {
        "items": {
            "type": "Array<{id: string; trigger: string; content: React.ReactNode}>",
            "required": True,
            "default": None,
            "description": "Accordion section definitions.",
        },
        "allowMultiple": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Whether multiple panels can be open simultaneously.",
        },
        "defaultOpen": {
            "type": "string[]",
            "required": False,
            "default": None,
            "description": "Section ids open by default.",
        },
    },
    "variants": ["default", "flush", "outlined"],
    "states": {
        "default": "All panels collapsed.",
        "open": "Panel expanded showing content.",
        "closed": "Panel collapsed.",
        "hover": "Trigger element hovered.",
        "focus": "Trigger focused.",
    },
    "tokenBindings": [
        _tb("triggerBackgroundColor", "color.surface.accordion.trigger"),
        _tb("triggerColor", "color.text.primary"),
        _tb("borderColor", "color.border.subtle"),
        _tb("contentBackgroundColor", "color.surface.accordion.content"),
        _tb("focusRingColor", "color.focus.ring"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Pressable", "Text"],
        "allowedChildren": "*",
        "forbiddenNesting": [],
        "slots": ["trigger", "content"],
    },
    "a11yRequirements": {
        "role": "region",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "Enter", "action": "Toggles the panel open/closed"},
            {"key": "Space", "action": "Toggles the panel open/closed"},
        ],
        "ariaAttributes": ["aria-expanded", "aria-controls", "aria-labelledby"],
    },
}


_TOOLTIP_SPEC: dict[str, Any] = {
    "component": "Tooltip",
    "description": (
        "A small informational overlay that appears near an anchor element on hover "
        "or focus. Contains short descriptive text only."
    ),
    "props": {
        "content": {
            "type": "string",
            "required": True,
            "default": None,
            "description": "Tooltip text content.",
        },
        "placement": {
            "type": "string",
            "required": False,
            "default": "top",
            "description": "Position relative to anchor: top | bottom | left | right.",
        },
        "children": {
            "type": "React.ReactElement",
            "required": True,
            "default": None,
            "description": "Anchor element that triggers the tooltip.",
        },
    },
    "variants": ["default", "dark", "light"],
    "states": {
        "hidden": "Tooltip not visible.",
        "visible": "Tooltip shown near anchor.",
    },
    "tokenBindings": [
        _tb("backgroundColor", "color.surface.tooltip"),
        _tb("color", "color.text.inverse"),
        _tb("borderRadius", "scale.border-radius.sm"),
        _tb("paddingX", "scale.spacing.component.padding.x.sm"),
        _tb("paddingY", "scale.spacing.component.padding.y.xs"),
        _tb("fontSize", "scale.typography.size.label.sm"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Text"],
        "allowedChildren": [],
        "forbiddenNesting": ["Tooltip"],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "tooltip",
        "focusable": False,
        "keyboardInteractions": [
            {"key": "Escape", "action": "Hides the tooltip"},
        ],
        "ariaAttributes": ["aria-describedby"],
    },
}


_TOAST_SPEC: dict[str, Any] = {
    "component": "Toast",
    "description": (
        "A transient notification that appears at the screen edge to inform users "
        "of background operations or system events. Auto-dismisses."
    ),
    "props": {
        "message": {
            "type": "string",
            "required": True,
            "default": None,
            "description": "Notification message text.",
        },
        "variant": {
            "type": "string",
            "required": False,
            "default": "info",
            "description": "Semantic variant: info | success | warning | error.",
        },
        "duration": {
            "type": "number",
            "required": False,
            "default": 5000,
            "description": "Auto-dismiss delay in milliseconds.",
        },
        "onDismiss": {
            "type": "() => void",
            "required": False,
            "default": None,
            "description": "Called when the toast is dismissed.",
        },
    },
    "variants": ["info", "success", "warning", "error"],
    "states": {
        "default": "Toast visible at rest.",
        "dismissed": "Toast in exit animation.",
    },
    "tokenBindings": [
        _tb("backgroundColor", "color.semantic.toast.info.background"),
        _tb("color", "color.semantic.toast.info.foreground"),
        _tb("borderRadius", "scale.border-radius.md"),
        _tb("boxShadow", "scale.elevation.md"),
        _tb("iconColor", "color.semantic.toast.info.icon"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Text", "Icon"],
        "allowedChildren": [],
        "forbiddenNesting": [],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "status",
        "focusable": False,
        "keyboardInteractions": [],
        "ariaAttributes": ["aria-live", "aria-atomic"],
    },
}


_DROPDOWN_SPEC: dict[str, Any] = {
    "component": "Dropdown",
    "description": (
        "A contextual menu triggered by a button or other anchor element. "
        "Presents a list of actions or navigation links."
    ),
    "props": {
        "trigger": {
            "type": "React.ReactElement",
            "required": True,
            "default": None,
            "description": "Element that opens the dropdown on click.",
        },
        "items": {
            "type": "Array<{label: string; onClick: () => void; disabled?: boolean; icon?: React.ReactNode}>",
            "required": True,
            "default": None,
            "description": "Menu item definitions.",
        },
        "placement": {
            "type": "string",
            "required": False,
            "default": "bottom-start",
            "description": "Position relative to trigger.",
        },
    },
    "variants": ["default", "compact"],
    "states": {
        "default": "Dropdown closed.",
        "open": "Dropdown menu visible.",
        "itemHover": "Menu item hovered.",
        "itemFocus": "Menu item focused.",
        "itemDisabled": "Non-interactive menu item.",
    },
    "tokenBindings": [
        _tb("menuBackgroundColor", "color.surface.overlay"),
        _tb("menuBorderColor", "color.border.subtle"),
        _tb("itemHoverBackgroundColor", "color.interactive.surface.hover"),
        _tb("itemColor", "color.text.primary"),
        _tb("menuBorderRadius", "scale.border-radius.md"),
        _tb("boxShadow", "scale.elevation.md"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Pressable", "Text", "Icon"],
        "allowedChildren": [],
        "forbiddenNesting": ["Dropdown"],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "menu",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "ArrowDown", "action": "Moves focus to next menu item"},
            {"key": "ArrowUp", "action": "Moves focus to previous menu item"},
            {"key": "Enter", "action": "Activates the focused menu item"},
            {"key": "Escape", "action": "Closes the dropdown"},
            {"key": "Tab", "action": "Closes the dropdown"},
            {"key": "Home", "action": "Moves focus to first menu item"},
            {"key": "End", "action": "Moves focus to last menu item"},
        ],
        "ariaAttributes": ["aria-haspopup", "aria-expanded", "aria-controls"],
    },
}


_PAGINATION_SPEC: dict[str, Any] = {
    "component": "Pagination",
    "description": (
        "A navigation control for paging through multi-page data sets. "
        "Shows current page, total pages, and prev/next controls."
    ),
    "props": {
        "currentPage": {
            "type": "number",
            "required": True,
            "default": None,
            "description": "Current page (1-indexed).",
        },
        "totalPages": {
            "type": "number",
            "required": True,
            "default": None,
            "description": "Total number of pages.",
        },
        "onPageChange": {
            "type": "(page: number) => void",
            "required": True,
            "default": None,
            "description": "Called when user navigates to a different page.",
        },
    },
    "variants": ["default", "compact", "full"],
    "states": {
        "default": "Navigation at rest.",
        "hover": "Page button hovered.",
        "focus": "Page button focused.",
        "active": "Current page highlighted.",
        "disabled": "Prev/Next button when at boundary.",
    },
    "tokenBindings": [
        _tb("activePageBackgroundColor", "color.interactive.primary.default"),
        _tb("activePageColor", "color.interactive.primary.foreground"),
        _tb("pageButtonHoverBackgroundColor", "color.interactive.surface.hover"),
        _tb("pageButtonColor", "color.text.secondary"),
        _tb("focusRingColor", "color.focus.ring"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Pressable", "Text"],
        "allowedChildren": [],
        "forbiddenNesting": [],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "navigation",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "Tab", "action": "Moves focus between page controls"},
            {"key": "Enter", "action": "Navigates to focused page"},
        ],
        "ariaAttributes": ["aria-label", "aria-current"],
    },
}


_BREADCRUMB_SPEC: dict[str, Any] = {
    "component": "Breadcrumb",
    "description": (
        "A hierarchical navigation trail showing the current location within "
        "the application structure. The last item represents the current page."
    ),
    "props": {
        "items": {
            "type": "Array<{label: string; href?: string}>",
            "required": True,
            "default": None,
            "description": "Breadcrumb trail. Last item is current page (no href).",
        },
        "separator": {
            "type": "React.ReactNode",
            "required": False,
            "default": "/",
            "description": "Separator between crumbs.",
        },
    },
    "variants": ["default", "compact"],
    "states": {
        "default": "Breadcrumb trail at rest.",
        "hover": "Link item hovered.",
        "focus": "Link item focused.",
    },
    "tokenBindings": [
        _tb("linkColor", "color.text.link"),
        _tb("currentColor", "color.text.secondary"),
        _tb("separatorColor", "color.text.tertiary"),
        _tb("fontSize", "scale.typography.size.body.sm"),
        _tb("focusRingColor", "color.focus.ring"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Pressable", "Text"],
        "allowedChildren": [],
        "forbiddenNesting": [],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "navigation",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "Tab", "action": "Moves focus between breadcrumb links"},
            {"key": "Enter", "action": "Navigates to focused link"},
        ],
        "ariaAttributes": ["aria-label", "aria-current"],
    },
}


_NAVIGATION_SPEC: dict[str, Any] = {
    "component": "Navigation",
    "description": (
        "A primary navigation component for top-level or sidebar navigation. "
        "Supports nested items, active state tracking, and collapsible groups."
    ),
    "props": {
        "items": {
            "type": "Array<{id: string; label: string; href?: string; icon?: React.ReactNode; children?: NavItem[]}>",
            "required": True,
            "default": None,
            "description": "Navigation item tree.",
        },
        "activeId": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Id of the currently active item.",
        },
        "orientation": {
            "type": "string",
            "required": False,
            "default": "vertical",
            "description": "Layout orientation: horizontal | vertical.",
        },
    },
    "variants": ["sidebar", "topbar", "compact"],
    "states": {
        "default": "Navigation at rest.",
        "active": "Current page item highlighted.",
        "hover": "Item hovered.",
        "focus": "Item focused.",
        "expanded": "Collapsible group open.",
        "collapsed": "Collapsible group closed.",
    },
    "tokenBindings": [
        _tb("activeItemBackgroundColor", "color.interactive.primary.subtle"),
        _tb("activeItemColor", "color.interactive.primary.default"),
        _tb("itemHoverBackgroundColor", "color.interactive.surface.hover"),
        _tb("itemColor", "color.text.secondary"),
        _tb("focusRingColor", "color.focus.ring"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Pressable", "Text"],
        "allowedChildren": "*",
        "forbiddenNesting": [],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "navigation",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "Tab", "action": "Moves focus between navigation items"},
            {"key": "Enter", "action": "Navigates to focused item or toggles group"},
            {"key": "ArrowDown", "action": "Moves to next item (vertical orientation)"},
            {"key": "ArrowUp", "action": "Moves to previous item (vertical orientation)"},
        ],
        "ariaAttributes": ["aria-label", "aria-current", "aria-expanded"],
    },
}


# ---------------------------------------------------------------------------
# Comprehensive-delta component spec dicts
# ---------------------------------------------------------------------------

_DATEPICKER_SPEC: dict[str, Any] = {
    "component": "DatePicker",
    "description": (
        "A calendar-based date selection control. Presents a calendar grid "
        "in a popup dialog. Supports single-date and date-range modes."
    ),
    "props": {
        "value": {
            "type": "string | null",
            "required": False,
            "default": None,
            "description": "Controlled ISO date string (YYYY-MM-DD).",
        },
        "onChange": {
            "type": "(date: string | null) => void",
            "required": False,
            "default": None,
            "description": "Called when selected date changes.",
        },
        "minDate": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Minimum selectable ISO date.",
        },
        "maxDate": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Maximum selectable ISO date.",
        },
        "placeholder": {
            "type": "string",
            "required": False,
            "default": "Select date",
            "description": "Trigger placeholder text.",
        },
    },
    "variants": ["default", "range", "inline"],
    "states": {
        "default": "Closed trigger at rest.",
        "open": "Calendar popup visible.",
        "dayHover": "Calendar day hovered.",
        "dayFocus": "Calendar day focused.",
        "daySelected": "Selected date highlighted.",
        "dayDisabled": "Out-of-range day.",
        "error": "Invalid date entered.",
    },
    "tokenBindings": [
        _tb("triggerBorderColor", "color.border.input.default"),
        _tb("daySelectedBackgroundColor", "color.interactive.primary.default"),
        _tb("dayHoverBackgroundColor", "color.interactive.surface.hover"),
        _tb("todayIndicatorColor", "color.interactive.primary.subtle"),
        _tb("calendarBackgroundColor", "color.surface.overlay"),
        _tb("focusRingColor", "color.focus.ring"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Pressable", "Text", "Icon"],
        "allowedChildren": [],
        "forbiddenNesting": [],
        "slots": ["trigger", "calendar"],
    },
    "a11yRequirements": {
        "role": "dialog",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "ArrowLeft", "action": "Move to previous day"},
            {"key": "ArrowRight", "action": "Move to next day"},
            {"key": "ArrowUp", "action": "Move to same day previous week"},
            {"key": "ArrowDown", "action": "Move to same day next week"},
            {"key": "Enter", "action": "Select focused date"},
            {"key": "Escape", "action": "Close the calendar"},
            {"key": "Home", "action": "Move to first day of month"},
            {"key": "End", "action": "Move to last day of month"},
        ],
        "ariaAttributes": ["aria-modal", "aria-label", "aria-selected", "aria-disabled"],
    },
}


_DATAGRID_SPEC: dict[str, Any] = {
    "component": "DataGrid",
    "description": (
        "An advanced tabular data component with sorting, filtering, column resizing, "
        "row selection, pagination, and virtualization for large datasets."
    ),
    "props": {
        "columns": {
            "type": "Array<GridColumn>",
            "required": True,
            "default": None,
            "description": "Column definitions with sorting, filtering, and render config.",
        },
        "rows": {
            "type": "Array<Record<string, unknown>>",
            "required": True,
            "default": None,
            "description": "Row data array.",
        },
        "pageSize": {
            "type": "number",
            "required": False,
            "default": 25,
            "description": "Rows per page for built-in pagination.",
        },
        "onSelectionChange": {
            "type": "(selectedIds: string[]) => void",
            "required": False,
            "default": None,
            "description": "Called when row selection changes.",
        },
    },
    "variants": ["default", "compact", "comfortable"],
    "states": {
        "default": "Grid at rest.",
        "rowHover": "Row highlighted on hover.",
        "rowSelected": "Row selected state.",
        "cellFocus": "Cell focused.",
        "sortedAsc": "Column header sorted ascending.",
        "sortedDesc": "Column header sorted descending.",
        "loading": "Data loading skeleton.",
        "empty": "No rows to display.",
    },
    "tokenBindings": [
        _tb("headerBackgroundColor", "color.surface.table.header"),
        _tb("rowBackgroundColor", "color.surface.table.row"),
        _tb("selectedRowBackgroundColor", "color.interactive.primary.subtle"),
        _tb("borderColor", "color.border.subtle"),
        _tb("focusRingColor", "color.focus.ring"),
        _tb("headerColor", "color.text.secondary"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Text"],
        "allowedChildren": [],
        "forbiddenNesting": [],
        "slots": ["toolbar", "header", "body", "footer"],
    },
    "a11yRequirements": {
        "role": "grid",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "ArrowLeft", "action": "Move focus left one cell"},
            {"key": "ArrowRight", "action": "Move focus right one cell"},
            {"key": "ArrowUp", "action": "Move focus up one row"},
            {"key": "ArrowDown", "action": "Move focus down one row"},
            {"key": "Enter", "action": "Activate cell or sort column header"},
            {"key": "Home", "action": "Move focus to first cell in row"},
            {"key": "End", "action": "Move focus to last cell in row"},
        ],
        "ariaAttributes": ["aria-rowcount", "aria-colcount", "aria-sort", "aria-selected"],
    },
}


_TREEVIEW_SPEC: dict[str, Any] = {
    "component": "TreeView",
    "description": (
        "A hierarchical tree navigation component for displaying nested data "
        "structures such as file systems or category trees."
    ),
    "props": {
        "items": {
            "type": "Array<TreeNode>",
            "required": True,
            "default": None,
            "description": "Recursive tree node definitions.",
        },
        "selectedId": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "Currently selected node id.",
        },
        "onSelect": {
            "type": "(id: string) => void",
            "required": False,
            "default": None,
            "description": "Called when a node is selected.",
        },
        "defaultExpanded": {
            "type": "string[]",
            "required": False,
            "default": None,
            "description": "Node ids expanded by default.",
        },
    },
    "variants": ["default", "compact"],
    "states": {
        "default": "Tree at rest, all collapsed.",
        "nodeSelected": "Selected node highlighted.",
        "nodeHover": "Node hovered.",
        "nodeFocus": "Node focused.",
        "expanded": "Branch node expanded.",
        "collapsed": "Branch node collapsed.",
    },
    "tokenBindings": [
        _tb("selectedNodeBackgroundColor", "color.interactive.primary.subtle"),
        _tb("selectedNodeColor", "color.interactive.primary.default"),
        _tb("nodeHoverBackgroundColor", "color.interactive.surface.hover"),
        _tb("nodeColor", "color.text.primary"),
        _tb("focusRingColor", "color.focus.ring"),
        _tb("indentSize", "scale.spacing.md"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Pressable", "Text", "Icon"],
        "allowedChildren": "*",
        "forbiddenNesting": [],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "tree",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "ArrowDown", "action": "Move focus to next visible node"},
            {"key": "ArrowUp", "action": "Move focus to previous visible node"},
            {"key": "ArrowRight", "action": "Expand collapsed node or move to first child"},
            {"key": "ArrowLeft", "action": "Collapse expanded node or move to parent"},
            {"key": "Enter", "action": "Select the focused node"},
            {"key": "Home", "action": "Move focus to first node"},
            {"key": "End", "action": "Move focus to last visible node"},
        ],
        "ariaAttributes": [
            "aria-expanded", "aria-selected", "aria-level",
            "aria-setsize", "aria-posinset",
        ],
    },
}


_DRAWER_SPEC: dict[str, Any] = {
    "component": "Drawer",
    "description": (
        "A slide-in panel anchored to the edge of the viewport. "
        "Used for navigation, filters, details, or side-by-side workflows. "
        "Traps focus while open."
    ),
    "props": {
        "open": {
            "type": "boolean",
            "required": True,
            "default": False,
            "description": "Whether the drawer is open.",
        },
        "onClose": {
            "type": "() => void",
            "required": True,
            "default": None,
            "description": "Called when the drawer requests to close.",
        },
        "placement": {
            "type": "string",
            "required": False,
            "default": "right",
            "description": "Anchor edge: left | right | top | bottom.",
        },
        "size": {
            "type": "string",
            "required": False,
            "default": "md",
            "description": "Width/height: sm | md | lg | full.",
        },
    },
    "variants": ["default", "overlay", "push"],
    "states": {
        "open": "Drawer visible.",
        "closed": "Drawer hidden.",
    },
    "tokenBindings": [
        _tb("backgroundColor", "color.surface.overlay"),
        _tb("boxShadow", "scale.elevation.lg"),
        _tb("backdropColor", "color.overlay.backdrop"),
        _tb("borderColor", "color.border.subtle"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Text", "Pressable"],
        "allowedChildren": "*",
        "forbiddenNesting": ["Drawer", "Modal"],
        "slots": ["header", "body", "footer"],
    },
    "a11yRequirements": {
        "role": "dialog",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "Escape", "action": "Closes the drawer"},
            {"key": "Tab", "action": "Cycles focus within drawer (focus trap)"},
            {"key": "Shift+Tab", "action": "Reverse cycles focus within drawer"},
        ],
        "ariaAttributes": ["aria-modal", "aria-labelledby", "aria-describedby"],
    },
}


_STEPPER_SPEC: dict[str, Any] = {
    "component": "Stepper",
    "description": (
        "A visual progress indicator showing steps in a multi-step workflow. "
        "Communicates current step, completed steps, and upcoming steps."
    ),
    "props": {
        "steps": {
            "type": "Array<{id: string; label: string; description?: string}>",
            "required": True,
            "default": None,
            "description": "Step definitions.",
        },
        "activeStep": {
            "type": "number",
            "required": True,
            "default": None,
            "description": "Zero-indexed current step.",
        },
        "orientation": {
            "type": "string",
            "required": False,
            "default": "horizontal",
            "description": "Layout orientation: horizontal | vertical.",
        },
    },
    "variants": ["default", "compact", "numbered"],
    "states": {
        "completed": "Steps before activeStep.",
        "active": "Current step in progress.",
        "pending": "Steps after activeStep.",
    },
    "tokenBindings": [
        _tb("completedStepColor", "color.interactive.primary.default"),
        _tb("activeStepColor", "color.interactive.primary.default"),
        _tb("pendingStepColor", "color.border.subtle"),
        _tb("connectorColor", "color.border.subtle"),
        _tb("stepLabelColor", "color.text.primary"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Text", "Icon"],
        "allowedChildren": [],
        "forbiddenNesting": [],
        "slots": [],
    },
    "a11yRequirements": {
        "role": "list",
        "focusable": False,
        "keyboardInteractions": [],
        "ariaAttributes": ["aria-label", "aria-current"],
    },
}


_FILEUPLOAD_SPEC: dict[str, Any] = {
    "component": "FileUpload",
    "description": (
        "A file picker and drop zone component for uploading files. "
        "Supports drag-and-drop, file type filtering, and multiple file selection."
    ),
    "props": {
        "accept": {
            "type": "string",
            "required": False,
            "default": None,
            "description": "MIME type filter (e.g., 'image/*,.pdf').",
        },
        "multiple": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Whether multiple files can be selected.",
        },
        "onFiles": {
            "type": "(files: File[]) => void",
            "required": True,
            "default": None,
            "description": "Called with the selected/dropped File objects.",
        },
        "maxSize": {
            "type": "number",
            "required": False,
            "default": None,
            "description": "Maximum file size in bytes.",
        },
    },
    "variants": ["dropzone", "button"],
    "states": {
        "idle": "Awaiting user interaction.",
        "dragging": "File dragged over drop zone.",
        "uploading": "File upload in progress.",
        "error": "Upload failed or invalid file.",
        "success": "Upload completed successfully.",
    },
    "tokenBindings": [
        _tb("dropzoneBorderColor", "color.border.dashed"),
        _tb("dropzoneBackgroundColor", "color.surface.subtle"),
        _tb("draggingBorderColor", "color.interactive.primary.default"),
        _tb("draggingBackgroundColor", "color.interactive.primary.subtle"),
        _tb("errorBorderColor", "color.semantic.error.border"),
        _tb("successBorderColor", "color.semantic.success.border"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Text", "Icon", "Pressable"],
        "allowedChildren": [],
        "forbiddenNesting": [],
        "slots": ["dropzoneContent"],
    },
    "a11yRequirements": {
        "role": "button",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "Enter", "action": "Opens the file picker dialog"},
            {"key": "Space", "action": "Opens the file picker dialog"},
        ],
        "ariaAttributes": ["aria-label", "aria-describedby", "aria-busy"],
    },
}


_RICHTEXT_SPEC: dict[str, Any] = {
    "component": "RichText",
    "description": (
        "A rich text editor with a formatting toolbar. Supports bold, italic, "
        "underline, lists, links, and headings. Based on a headless editor core."
    ),
    "props": {
        "value": {
            "type": "string",
            "required": False,
            "default": "",
            "description": "Controlled HTML or markdown content.",
        },
        "onChange": {
            "type": "(value: string) => void",
            "required": False,
            "default": None,
            "description": "Called when content changes.",
        },
        "placeholder": {
            "type": "string",
            "required": False,
            "default": "Start typing...",
            "description": "Placeholder shown in empty editor.",
        },
        "readOnly": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Disables editing, renders as rich text display.",
        },
    },
    "variants": ["default", "minimal", "full"],
    "states": {
        "default": "Editor ready for input.",
        "focus": "Editor actively focused.",
        "readOnly": "Non-editable display mode.",
        "error": "Invalid content state.",
    },
    "tokenBindings": [
        _tb("backgroundColor", "color.surface.editor"),
        _tb("borderColor", "color.border.input.default"),
        _tb("color", "color.text.primary"),
        _tb("toolbarBackgroundColor", "color.surface.toolbar"),
        _tb("focusRingColor", "color.focus.ring"),
        _tb("fontSize", "scale.typography.size.body.md"),
    ],
    "compositionRules": {
        "composesFrom": ["Box", "Stack", "Text", "Pressable", "Icon"],
        "allowedChildren": [],
        "forbiddenNesting": [],
        "slots": ["toolbar", "content"],
    },
    "a11yRequirements": {
        "role": "textbox",
        "focusable": True,
        "keyboardInteractions": [
            {"key": "Tab", "action": "Moves focus to/from the editor"},
            {"key": "Ctrl+B", "action": "Toggle bold formatting"},
            {"key": "Ctrl+I", "action": "Toggle italic formatting"},
            {"key": "Ctrl+U", "action": "Toggle underline formatting"},
            {"key": "Ctrl+Z", "action": "Undo last change"},
        ],
        "ariaAttributes": ["aria-label", "aria-multiline", "aria-readonly"],
    },
}


# ---------------------------------------------------------------------------
# Component spec map
# ---------------------------------------------------------------------------

COMPONENT_SPEC_MAP: dict[str, dict[str, Any]] = {
    "Button": _BUTTON_SPEC,
    "Input": _INPUT_SPEC,
    "Checkbox": _CHECKBOX_SPEC,
    "Radio": _RADIO_SPEC,
    "Select": _SELECT_SPEC,
    "Card": _CARD_SPEC,
    "Badge": _BADGE_SPEC,
    "Avatar": _AVATAR_SPEC,
    "Alert": _ALERT_SPEC,
    "Modal": _MODAL_SPEC,
    # Standard delta
    "Table": _TABLE_SPEC,
    "Tabs": _TABS_SPEC,
    "Accordion": _ACCORDION_SPEC,
    "Tooltip": _TOOLTIP_SPEC,
    "Toast": _TOAST_SPEC,
    "Dropdown": _DROPDOWN_SPEC,
    "Pagination": _PAGINATION_SPEC,
    "Breadcrumb": _BREADCRUMB_SPEC,
    "Navigation": _NAVIGATION_SPEC,
    # Comprehensive delta
    "DatePicker": _DATEPICKER_SPEC,
    "DataGrid": _DATAGRID_SPEC,
    "TreeView": _TREEVIEW_SPEC,
    "Drawer": _DRAWER_SPEC,
    "Stepper": _STEPPER_SPEC,
    "FileUpload": _FILEUPLOAD_SPEC,
    "RichText": _RICHTEXT_SPEC,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_component_specs(
    scope: str,
    output_dir: str = ".",
    component_overrides: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Generate canonical component spec YAMLs for the given scope tier.

    Args:
        scope: One of 'starter', 'standard', 'comprehensive'.
        output_dir: Base directory; specs are written to <output_dir>/specs/.
        component_overrides: Optional mapping of PascalCase component name to
            a dict of top-level key overrides applied *after* the default spec.
            Keys present in the override are shallow-merged into the spec dict.
            Out-of-scope component names are silently ignored.

    Returns:
        A dict mapping each PascalCase component name to the absolute path of
        its written spec YAML file.

    Raises:
        ValueError: If scope is not one of the valid tier names.
    """
    valid_scopes = list(SCOPE_TIERS.keys())
    if scope not in SCOPE_TIERS:
        raise ValueError(
            f"Invalid scope '{scope}'. Valid values are: {', '.join(valid_scopes)}"
        )

    component_names = SCOPE_TIERS[scope]
    overrides: dict[str, Any] = component_overrides or {}

    specs_dir = Path(output_dir) / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, str] = {}
    for name in component_names:
        spec = copy.deepcopy(COMPONENT_SPEC_MAP[name])
        if name in overrides:
            spec.update(overrides[name])
        out_path = specs_dir / f"{name}.spec.yaml"
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(
                spec,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        result[name] = str(out_path.resolve())

    return result


# ---------------------------------------------------------------------------
# CrewAI BaseTool
# ---------------------------------------------------------------------------


class _CoreComponentSpecGeneratorInput(BaseModel):
    scope: str = Field(
        description="Scope tier: 'starter' (10), 'standard' (19), or 'comprehensive' (26)."
    )
    output_dir: str = Field(description="Base directory; specs/ subdirectory will be created.")
    component_overrides_json: str = Field(
        default="{}",
        description="JSON string mapping component names to top-level override dicts.",
    )


class CoreComponentSpecGenerator(BaseTool):
    """Generate canonical component spec YAMLs for a given scope tier."""

    name: str = "CoreComponentSpecGenerator"
    description: str = (
        "Generates canonical *.spec.yaml files for core UI components. "
        "Select a scope tier: 'starter' (10 components), 'standard' (19), "
        "or 'comprehensive' (26). Writes one YAML per component to output_dir/specs/. "
        "Returns a summary string with the count and directory path."
    )
    args_schema: type[BaseModel] = _CoreComponentSpecGeneratorInput

    def _run(
        self,
        scope: str,
        output_dir: str,
        component_overrides_json: str = "{}",
    ) -> str:
        try:
            overrides: dict[str, Any] = json.loads(component_overrides_json)
        except json.JSONDecodeError as exc:
            return f"Error parsing component_overrides_json: {exc}"

        try:
            result = generate_component_specs(
                scope=scope,
                output_dir=output_dir,
                component_overrides=overrides,
            )
        except ValueError as exc:
            return str(exc)

        specs_dir = str(Path(output_dir).resolve() / "specs")
        return f"Generated {len(result)} component specs in {specs_dir}"
