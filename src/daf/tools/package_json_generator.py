"""Agent 39 – PackageJsonGenerator tool (Release Crew, Phase 6).

Assembles package.json from an input dict. Strips v-prefix from version.
Ensures name, version, main, types, exports, peerDependencies, scripts fields.
Writes file to output_dir/package.json and returns the JSON string.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field


class PackageJsonGenerator(BaseTool):
    """Assemble and write package.json from spec inputs."""

    name: str = Field(default="package_json_generator")
    description: str = Field(
        default=(
            "Accepts a JSON string with at least 'name' and 'version' keys. "
            "Assembles a full package.json with required fields and writes it to "
            "output_dir/package.json. Returns the generated JSON string."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, spec_json: str = "", **kwargs: Any) -> str:
        try:
            spec: dict[str, Any] = json.loads(spec_json)
        except (json.JSONDecodeError, TypeError):
            spec = {}

        name = spec.get("name", "design-system")
        raw_version = str(spec.get("version", "0.1.0"))
        version = raw_version.lstrip("v")

        package = {
            "name": name,
            "version": version,
            "main": spec.get("main", "./dist/index.js"),
            "types": spec.get("types", "./dist/index.d.ts"),
            "exports": spec.get("exports", {
                ".": {
                    "import": "./dist/index.js",
                    "types": "./dist/index.d.ts",
                }
            }),
            "peerDependencies": spec.get("peerDependencies", {
                "react": ">=17",
                "react-dom": ">=17",
            }),
            "scripts": spec.get("scripts", {
                "build": "tsc",
                "test": "vitest",
                "lint": "eslint src",
            }),
        }

        # Merge any extra fields from spec
        for key, value in spec.items():
            if key not in package:
                package[key] = value

        result = json.dumps(package, indent=2)
        pkg_path = Path(self.output_dir) / "package.json"
        pkg_path.write_text(result, encoding="utf-8")
        return result
