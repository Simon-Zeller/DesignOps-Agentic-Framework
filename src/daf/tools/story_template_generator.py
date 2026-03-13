"""Story Template Generator — generates Storybook CSF3 story files."""
from __future__ import annotations

from typing import Sequence

_STORY_FILE_TEMPLATE = """\
import type {{ Meta, StoryObj }} from '@storybook/react';
import {{ {name} }} from './{name}';

const meta: Meta<typeof {name}> = {{
  title: 'Components/{name}',
  component: {name},
}};

export default meta;
type Story = StoryObj<typeof {name}>;

{stories}
"""


def generate_stories(
    component_name: str,
    variants: Sequence[str],
    states: Sequence[str] | None = None,
) -> str:
    """Generate a Storybook CSF3 story file with one named export per variant.

    If *variants* is empty, a single ``Default`` story is emitted.

    Args:
        component_name: PascalCase component name.
        variants: List of variant names (e.g. ``['primary', 'secondary']``).
        states: Optional list of interactive state names (used for naming, not exported separately).

    Returns:
        String content for the ``*.stories.tsx`` file.
    """
    story_blocks: list[str] = []

    for variant in variants:
        export_name = variant[0].upper() + variant[1:]
        story_blocks.append(
            f"export const {export_name}: Story = {{\n"
            f"  args: {{ variant: '{variant}' }},\n"
            f"}};"
        )

    if not story_blocks:
        story_blocks.append(
            "export const Default: Story = {\n"
            "  args: {},\n"
            "};"
        )

    return _STORY_FILE_TEMPLATE.format(
        name=component_name,
        stories="\n\n".join(story_blocks),
    )
