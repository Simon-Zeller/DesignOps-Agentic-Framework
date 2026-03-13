"""Keyboard Nav Scaffolder — generates onKeyDown handler stubs for ARIA role patterns."""
from __future__ import annotations


_HANDLER_TEMPLATES: dict[str, str] = {
    "dialog": """\
const handleKeyDown = (e: React.KeyboardEvent) => {{
  switch (e.key) {{
    case 'Escape':
      {close_cb}();
      // Restore focus to trigger element
      break;
    case 'Tab':
      // Focus trap: cycle within modal
      break;
    default:
      break;
  }}
}};""",

    "listbox": """\
const handleKeyDown = (e: React.KeyboardEvent) => {{
  switch (e.key) {{
    case 'ArrowDown':
      e.preventDefault();
      // Move focus to next option
      break;
    case 'ArrowUp':
      e.preventDefault();
      // Move focus to previous option
      break;
    case 'Enter':
      // Select focused option
      break;
    case 'Escape':
      // Close listbox
      break;
    default:
      break;
  }}
}};""",

    "combobox": """\
const handleKeyDown = (e: React.KeyboardEvent) => {{
  switch (e.key) {{
    case 'ArrowDown':
      e.preventDefault();
      // Open dropdown or move to next option
      break;
    case 'ArrowUp':
      e.preventDefault();
      // Move to previous option
      break;
    case 'Enter':
      // Confirm selection
      break;
    case 'Escape':
      // Close dropdown
      break;
    default:
      break;
  }}
}};""",

    "menu": """\
const handleKeyDown = (e: React.KeyboardEvent) => {{
  switch (e.key) {{
    case 'ArrowDown':
      e.preventDefault();
      // Focus next menu item
      break;
    case 'ArrowUp':
      e.preventDefault();
      // Focus previous menu item
      break;
    case 'Enter':
    case ' ':
      // Activate focused menu item
      break;
    case 'Escape':
      // Close menu
      break;
    default:
      break;
  }}
}};""",

    "tabs": """\
const handleKeyDown = (e: React.KeyboardEvent) => {{
  switch (e.key) {{
    case 'ArrowRight':
      // Focus next tab
      break;
    case 'ArrowLeft':
      // Focus previous tab
      break;
    case 'Home':
      // Focus first tab
      break;
    case 'End':
      // Focus last tab
      break;
    default:
      break;
  }}
}};""",

    "button": """\
const handleKeyDown = (e: React.KeyboardEvent) => {{
  switch (e.key) {{
    case 'Enter':
    case ' ':
      e.preventDefault();
      {press_cb}();
      break;
    default:
      break;
  }}
}};""",
}


def scaffold_keyboard_handlers(
    component_type: str,
    callbacks: dict[str, str],
) -> str:
    """Generate a keyboard handler stub for *component_type*.

    Args:
        component_type: One of ``"dialog"``, ``"listbox"``, ``"combobox"``, ``"menu"``,
                        ``"tabs"``, ``"button"``.
        callbacks: Mapping of callback role → function name in the component,
                   e.g. ``{"close": "onClose"}``.

    Returns:
        A TypeScript ``onKeyDown`` handler stub string.
    """
    template = _HANDLER_TEMPLATES.get(component_type.lower())
    if template is None:
        return f"// No keyboard handler template for component type: {component_type!r}"

    close_cb = callbacks.get("close", "onClose")
    press_cb = callbacks.get("press", "onPress")

    return template.format(close_cb=close_cb, press_cb=press_cb)
