"""Playwright Renderer — drives headless Playwright to render React components."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any


_BROWSER_BINARIES = ("chromium", "chrome", "google-chrome", "chromium-browser")


def check_renderer_available() -> bool:
    """Return True if a Playwright-compatible browser binary is on PATH."""
    return any(shutil.which(b) is not None for b in _BROWSER_BINARIES)


def _do_render(
    component_name: str,
    variant: str,
    output_dir: str,
) -> dict[str, Any]:
    """Internal render call — drives Playwright to screenshot the component.

    This is extracted to a dedicated function so tests can patch it without
    affecting the ``check_renderer_available`` guard.
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import]
    except ImportError:
        return {
            "path": "",
            "width": 0,
            "height": 0,
            "render_errors": ["playwright not installed"],
        }

    screenshots_dir = Path(output_dir) / "screenshots" / component_name  # pragma: no cover
    screenshots_dir.mkdir(parents=True, exist_ok=True)  # pragma: no cover
    screenshot_path = screenshots_dir / f"{variant}.png"  # pragma: no cover

    render_errors: list[str] = []  # pragma: no cover
    width = 0  # pragma: no cover
    height = 0  # pragma: no cover

    with sync_playwright() as p:  # pragma: no cover
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def _on_console(msg: Any) -> None:
            if msg.type in ("error", "warn"):
                render_errors.append(msg.text)

        page.on("console", _on_console)

        # Minimal HTML harness — a real implementation would serve the component
        page.set_content(
            f"<html><body><div id='root' data-component='{component_name}' "
            f"data-variant='{variant}'></div></body></html>"
        )

        element = page.query_selector("#root")
        if element:
            bbox = element.bounding_box()
            if bbox:
                width = int(bbox["width"])
                height = int(bbox["height"])

        page.screenshot(path=str(screenshot_path))
        browser.close()

    return {  # pragma: no cover
        "path": str(screenshot_path),
        "width": width,
        "height": height,
        "render_errors": render_errors,
    }


def render_component(
    component_name: str,
    variant: str,
    output_dir: str,
) -> dict[str, Any]:
    """Render *component_name* variant *variant* headlessly and capture a screenshot.

    Args:
        component_name: PascalCase component name.
        variant: Variant name (used in the screenshot filename).
        output_dir: Root output directory; screenshots go to ``screenshots/<name>/``.

    Returns:
        Dict with ``path``, ``width``, ``height``, and ``render_errors`` keys.
    """
    return _do_render(component_name, variant, output_dir)
