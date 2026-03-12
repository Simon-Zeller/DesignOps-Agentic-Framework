"""Brand Profile Pydantic model — mirrors the §6 JSON schema."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ColorsConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    primary: str | None = None
    secondary: str | None = None
    accent: str | None = None
    neutral: str | None = None
    background: str | None = None
    surface: str | None = None
    text: str | None = None


class TypographyConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    scaleRatio: float | None = None
    baseSize: int | None = None
    headingFont: str | None = None
    bodyFont: str | None = None
    monoFont: str | None = None


class SpacingConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    density: str | None = None
    baseUnit: int | None = None


class BreakpointsConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    strategy: str | None = None


class ThemesConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    modes: list[str] | None = None
    brandOverrides: bool | None = None


class BrandProfile(BaseModel):
    """Complete brand profile: required identity fields + optional §6 design fields.

    Annotation fields (_filled_fields, _warnings, _color_notes) are carried via
    Field aliases so they round-trip through model_validate / model_dump(by_alias=True).
    Use Python field names (filled_fields, warnings, color_notes) in code.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    # Required
    name: str
    archetype: str

    # Optional §6 design fields
    colors: ColorsConfig | None = None
    typography: TypographyConfig | None = None
    spacing: SpacingConfig | None = None
    borderRadius: str | None = None
    elevation: str | None = None
    motion: str | None = None
    themes: ThemesConfig | None = None
    accessibility: str | None = None
    componentScope: str | None = None
    breakpoints: BreakpointsConfig | None = None

    # Annotation fields set by Agent 1 tools (use alias for dict interop)
    filled_fields: list[str] | None = Field(default=None, alias="_filled_fields")
    warnings: list[str] | None = Field(default=None, alias="_warnings")
    color_notes: dict[str, str] | None = Field(default=None, alias="_color_notes")

    def model_post_init(self, __context: object) -> None:
        # Coerce nested dicts passed as plain dicts into sub-models
        if isinstance(self.colors, dict):
            object.__setattr__(self, "colors", ColorsConfig(**self.colors))
        if isinstance(self.typography, dict):
            object.__setattr__(self, "typography", TypographyConfig(**self.typography))
        if isinstance(self.spacing, dict):
            object.__setattr__(self, "spacing", SpacingConfig(**self.spacing))
        if isinstance(self.themes, dict):
            object.__setattr__(self, "themes", ThemesConfig(**self.themes))
        if isinstance(self.breakpoints, dict):
            object.__setattr__(
                self, "breakpoints", BreakpointsConfig(**self.breakpoints)
            )
