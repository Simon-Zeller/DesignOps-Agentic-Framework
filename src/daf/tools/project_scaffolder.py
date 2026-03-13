"""ProjectScaffolder — generates project scaffolding files from pipeline-config.json.

Agent 5 (Pipeline Configuration Agent) in the DS Bootstrap Crew uses this module
after ConfigGenerator has written pipeline-config.json. It writes:
  - tsconfig.json       — React + TypeScript library compiler config
  - vitest.config.ts    — vitest configuration with coverage threshold from pipeline-config.json
  - vite.config.ts      — Vite library-mode build config

All templates are deterministic. The only parameterised value is minTestCoverage,
read from the previously written pipeline-config.json.
"""
from __future__ import annotations

import json
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Template constants (module-level for auditability)
# ---------------------------------------------------------------------------

_TSCONFIG_TEMPLATE: dict = {
    "compilerOptions": {
        "target": "ES2020",
        "module": "ESNext",
        "moduleResolution": "bundler",
        "jsx": "react-jsx",
        "strict": True,
        "esModuleInterop": True,
        "skipLibCheck": True,
        "declaration": True,
        "declarationMap": True,
        "sourceMap": True,
        "outDir": "dist",
        "rootDir": "src",
    },
    "include": ["src"],
    "exclude": ["node_modules", "dist"],
}

_VITEST_CONFIG_TEMPLATE = """\
import {{ defineConfig }} from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({{
  plugins: [react()],
  test: {{
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
    coverage: {{
      provider: "v8",
      reporter: ["text", "lcov"],
      thresholds: {{
        lines: {coverage},
        branches: {coverage},
        functions: {coverage},
        statements: {coverage},
      }},
    }},
  }},
}});
"""

_VITE_CONFIG_TEMPLATE = """\
import {{ defineConfig }} from "vite";
import react from "@vitejs/plugin-react";
import dts from "vite-plugin-dts";
import path from "path";

export default defineConfig({{
  plugins: [react(), dts({{ insertTypesEntry: true }})],
  build: {{
    lib: {{
      entry: path.resolve(__dirname, "src/index.ts"),
      formats: ["es", "cjs"],
      fileName: (format) => `index.${{format}}.js`,
    }},
    rollupOptions: {{
      external: ["react", "react-dom"],
      output: {{
        globals: {{
          react: "React",
          "react-dom": "ReactDOM",
        }},
      }},
    }},
  }},
}});
"""


# ---------------------------------------------------------------------------
# Pure function
# ---------------------------------------------------------------------------

def scaffold_project_files(brand_profile: dict, output_dir: str) -> dict[str, str]:
    """Write project scaffolding files (tsconfig.json, vitest.config.ts, vite.config.ts).

    Reads ``minTestCoverage`` from the already-written ``pipeline-config.json``
    in ``output_dir``. ``ConfigGenerator`` MUST be run first.

    Args:
        brand_profile: Validated Brand Profile dict (unused directly; kept for
            consistent tool signature with ConfigGenerator).
        output_dir: Directory containing ``pipeline-config.json`` and where
            scaffolding files will be written.

    Returns:
        Dict mapping filename → absolute path for each written file.

    Raises:
        FileNotFoundError: If ``pipeline-config.json`` is not found in ``output_dir``.
    """
    base = Path(output_dir).resolve()
    config_path = base / "pipeline-config.json"

    if not config_path.exists():
        raise FileNotFoundError(
            f"pipeline-config.json not found in {output_dir!r}. "
            "Run ConfigGenerator before ProjectScaffolder."
        )

    pipeline_config = json.loads(config_path.read_text())
    min_coverage: int = pipeline_config["qualityGates"]["minTestCoverage"]

    written: dict[str, str] = {}

    # tsconfig.json
    tsconfig_path = base / "tsconfig.json"
    tsconfig_path.write_text(json.dumps(_TSCONFIG_TEMPLATE, indent=2))
    written["tsconfig.json"] = str(tsconfig_path)

    # vitest.config.ts
    vitest_path = base / "vitest.config.ts"
    vitest_path.write_text(_VITEST_CONFIG_TEMPLATE.format(coverage=min_coverage))
    written["vitest.config.ts"] = str(vitest_path)

    # vite.config.ts
    vite_path = base / "vite.config.ts"
    vite_path.write_text(_VITE_CONFIG_TEMPLATE)
    written["vite.config.ts"] = str(vite_path)

    return written


# ---------------------------------------------------------------------------
# CrewAI BaseTool wrapper
# ---------------------------------------------------------------------------

class _ProjectScaffolderInput(BaseModel):
    brand_profile_json: str = Field(
        description="JSON string of the validated Brand Profile dict."
    )
    output_dir: str = Field(
        description=(
            "Directory containing pipeline-config.json and where scaffolding files "
            "will be written. ConfigGenerator must have been run first."
        )
    )


class ProjectScaffolder(BaseTool):
    """CrewAI tool that writes tsconfig.json, vitest.config.ts, and vite.config.ts.

    Reads the minTestCoverage value from the previously written pipeline-config.json
    to parameterise the vitest coverage thresholds.
    """

    name: str = "ProjectScaffolder"
    description: str = (
        "Writes project scaffolding files (tsconfig.json, vitest.config.ts, vite.config.ts) "
        "using standard DAF React+TypeScript+Vite+Vitest templates. "
        "Reads minTestCoverage from pipeline-config.json written by ConfigGenerator. "
        "Returns a JSON object mapping filename to absolute path."
    )
    args_schema: type[BaseModel] = _ProjectScaffolderInput

    def _run(self, brand_profile_json: str, output_dir: str) -> str:
        brand_profile = json.loads(brand_profile_json)
        result = scaffold_project_files(brand_profile, output_dir)
        return json.dumps(result)
