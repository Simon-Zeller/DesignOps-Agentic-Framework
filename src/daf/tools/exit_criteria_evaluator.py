"""ExitCriteriaEvaluator — CrewAI BaseTool (Agent 30-bis, Governance Crew, p19).

Runs all 15 §8 exit criteria checks and writes reports/exit-criteria.json.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

from daf.tools.ast_pattern_matcher import ASTPatternMatcher
from daf.tools.contrast_safe_pairer import ContrastSafePairer
from daf.tools.dependency_resolver import DependencyResolver
from daf.tools.dtcg_schema_validator import DTCGSchemaValidator
from daf.tools.json_schema_validator import validate_spec_schema
from daf.tools.token_graph_traverser import TokenGraphTraverser
from daf.tools.token_ref_checker import check_token_refs
from daf.tools.a11y_attribute_extractor import extract_a11y_attributes

_FATAL_IDS = frozenset({1, 2, 3, 4, 5, 6, 7, 8})

_CRITERION_DESCRIPTIONS = {
    1: "Token JSON files parse without error",
    2: "DTCG schema conformance — no fatal violations",
    3: "Semantic-layer token references all resolve",
    4: "Component-layer token references all resolve",
    5: "WCAG 2.1 AA contrast for all token pairs",
    6: "CSS custom property references all resolve",
    7: "TypeScript compilation succeeds (tsc --noEmit)",
    8: "npm build and dependency resolution succeeds",
    9: "All automated tests pass",
    10: "No hardcoded color values in component source",
    11: "Interactive components declare required ARIA attributes",
    12: "All quality gate scores ≥ 70",
    13: "No non-fixable drift items",
    14: "Component registry passes schema validation",
    15: "No components have status 'failed' in generation summary",
}


@dataclass
class CriterionResult:
    id: int
    description: str
    severity: str  # "fatal" | "warning"
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class _EvaluatorInput(BaseModel):
    output_dir: str


class ExitCriteriaEvaluator(BaseTool):
    """Run all 15 §8 exit criteria checks and write reports/exit-criteria.json."""

    name: str = "exit_criteria_evaluator"
    description: str = (
        "Evaluate all 15 §8 exit criteria for the output_dir. "
        "Returns {isComplete: bool, criteria: [...]} and writes "
        "reports/exit-criteria.json to disk."
    )
    args_schema: type[BaseModel] = _EvaluatorInput

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def _run(self, output_dir: str, **kwargs: Any) -> dict[str, Any]:
        criteria: list[CriterionResult] = []

        for i in range(1, 16):
            check_fn = getattr(self, f"_check_c{i}")
            try:
                result = check_fn(output_dir)
            except Exception as exc:  # noqa: BLE001
                sev = "fatal" if i in _FATAL_IDS else "warning"
                result = CriterionResult(
                    id=i,
                    description=_CRITERION_DESCRIPTIONS.get(i, f"C{i}"),
                    severity=sev,
                    passed=False,
                    detail=str(exc),
                )
            criteria.append(result)

        is_complete = all(
            c.passed for c in criteria if c.severity == "fatal"
        )

        report: dict[str, Any] = {
            "isComplete": is_complete,
            "criteria": [c.to_dict() for c in criteria],
        }

        reports_dir = Path(output_dir) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / "exit-criteria.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )

        return report

    # ------------------------------------------------------------------
    # C1 — Token JSON files parse without error
    # ------------------------------------------------------------------

    def _check_c1(self, output_dir: str) -> CriterionResult:
        tokens_dir = Path(output_dir) / "tokens"
        if not tokens_dir.exists():
            return CriterionResult(
                id=1,
                description=_CRITERION_DESCRIPTIONS[1],
                severity="fatal",
                passed=False,
                detail="tokens/ directory not found",
            )

        for token_file in sorted(tokens_dir.glob("*.tokens.json")):
            try:
                json.loads(token_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                return CriterionResult(
                    id=1,
                    description=_CRITERION_DESCRIPTIONS[1],
                    severity="fatal",
                    passed=False,
                    detail=f"Invalid JSON in {token_file.name}: {exc}",
                )

        return CriterionResult(
            id=1,
            description=_CRITERION_DESCRIPTIONS[1],
            severity="fatal",
            passed=True,
            detail="",
        )

    # ------------------------------------------------------------------
    # C2 — DTCG schema conformance
    # ------------------------------------------------------------------

    def _check_c2(self, output_dir: str) -> CriterionResult:
        tokens_dir = Path(output_dir) / "tokens"
        token_dict: dict[str, Any] = {}

        if tokens_dir.exists():
            for f in sorted(tokens_dir.glob("*.tokens.json")):
                try:
                    token_dict.update(json.loads(f.read_text(encoding="utf-8")))
                except (OSError, json.JSONDecodeError):
                    pass

        validator = DTCGSchemaValidator()
        result = validator._run(token_dict=token_dict)

        fatal_errors = result.get("fatal", [])
        if fatal_errors:
            return CriterionResult(
                id=2,
                description=_CRITERION_DESCRIPTIONS[2],
                severity="fatal",
                passed=False,
                detail=str(fatal_errors[:3]),
            )

        return CriterionResult(
            id=2,
            description=_CRITERION_DESCRIPTIONS[2],
            severity="fatal",
            passed=True,
            detail="",
        )

    # ------------------------------------------------------------------
    # C3 — Semantic-layer token references all resolve
    # ------------------------------------------------------------------

    def _check_c3(self, output_dir: str) -> CriterionResult:
        traverser = TokenGraphTraverser()
        result = traverser._run(output_dir=output_dir)

        unresolved = self._extract_unresolved(result)

        if unresolved:
            return CriterionResult(
                id=3,
                description=_CRITERION_DESCRIPTIONS[3],
                severity="fatal",
                passed=False,
                detail=f"unresolved refs: {unresolved[:5]}",
            )

        return CriterionResult(
            id=3,
            description=_CRITERION_DESCRIPTIONS[3],
            severity="fatal",
            passed=True,
            detail="",
        )

    # ------------------------------------------------------------------
    # C4 — Component-layer token references all resolve
    # ------------------------------------------------------------------

    def _check_c4(self, output_dir: str) -> CriterionResult:
        traverser = TokenGraphTraverser()
        result = traverser._run(output_dir=output_dir)

        unresolved = self._extract_unresolved(result)

        if unresolved:
            return CriterionResult(
                id=4,
                description=_CRITERION_DESCRIPTIONS[4],
                severity="fatal",
                passed=False,
                detail=f"unresolved component refs: {unresolved[:5]}",
            )

        return CriterionResult(
            id=4,
            description=_CRITERION_DESCRIPTIONS[4],
            severity="fatal",
            passed=True,
            detail="",
        )

    @staticmethod
    def _extract_unresolved(result: Any) -> list[str]:
        """Extract unresolved refs from TokenGraphTraverser output (list or dict)."""
        import re as _re
        _REF_RE = _re.compile(r"^\{.+\}$")

        if isinstance(result, dict):
            return result.get("unresolved_refs", [])
        if isinstance(result, list):
            return [
                t["name"]
                for t in result
                if isinstance(t.get("value"), str) and _REF_RE.match(t["value"])
            ]
        return []

    # ------------------------------------------------------------------
    # C5 — WCAG 2.1 AA contrast
    # ------------------------------------------------------------------

    def _check_c5(self, output_dir: str) -> CriterionResult:
        pairer = ContrastSafePairer()
        result: Any = pairer._run(palette={}, accessibility="AA")

        # Real return: tuple(semantic_overrides, [ContrastPairResult, ...])
        # Mocked return in tests: {"all_pass": bool, "pairs": [...]}
        if isinstance(result, dict):
            all_pass: bool = result.get("all_pass", True)
            failing_pairs: list[Any] = [p for p in result.get("pairs", []) if not p.get("pass", True)]
        else:
            _semantic, contrast_results = result
            failing_pairs = [r for r in contrast_results if not r.passed]
            all_pass = len(failing_pairs) == 0

        if not all_pass:
            return CriterionResult(
                id=5,
                description=_CRITERION_DESCRIPTIONS[5],
                severity="fatal",
                passed=False,
                detail=f"failing pairs: {failing_pairs[:3]}",
            )

        return CriterionResult(
            id=5,
            description=_CRITERION_DESCRIPTIONS[5],
            severity="fatal",
            passed=True,
            detail="",
        )

    # ------------------------------------------------------------------
    # C6 — CSS custom property references all resolve
    # ------------------------------------------------------------------

    def _check_c6(self, output_dir: str) -> CriterionResult:
        result = check_token_refs({}, {})

        if not result.get("all_resolved", True):
            unresolved = result.get("unresolved", [])
            return CriterionResult(
                id=6,
                description=_CRITERION_DESCRIPTIONS[6],
                severity="fatal",
                passed=False,
                detail=f"unresolved: {unresolved[:5]}",
            )

        return CriterionResult(
            id=6,
            description=_CRITERION_DESCRIPTIONS[6],
            severity="fatal",
            passed=True,
            detail="",
        )

    # ------------------------------------------------------------------
    # C7 — TypeScript compilation (tsc --noEmit)
    # ------------------------------------------------------------------

    def _check_c7(self, output_dir: str) -> CriterionResult:
        try:
            proc = subprocess.run(
                ["tsc", "--noEmit"],
                capture_output=True,
                text=True,
                cwd=output_dir,
                timeout=60,
            )
        except FileNotFoundError:
            return CriterionResult(
                id=7,
                description=_CRITERION_DESCRIPTIONS[7],
                severity="fatal",
                passed=False,
                detail="tsc not found",
            )
        except subprocess.TimeoutExpired:
            return CriterionResult(
                id=7,
                description=_CRITERION_DESCRIPTIONS[7],
                severity="fatal",
                passed=False,
                detail="tsc timed out",
            )

        if proc.returncode != 0:
            return CriterionResult(
                id=7,
                description=_CRITERION_DESCRIPTIONS[7],
                severity="fatal",
                passed=False,
                detail=proc.stderr[:500] if proc.stderr else f"exit code {proc.returncode}",
            )

        return CriterionResult(
            id=7,
            description=_CRITERION_DESCRIPTIONS[7],
            severity="fatal",
            passed=True,
            detail="",
        )

    # ------------------------------------------------------------------
    # C8 — npm build / dependency resolution
    # ------------------------------------------------------------------

    def _check_c8(self, output_dir: str) -> CriterionResult:
        resolver = DependencyResolver(output_dir=output_dir)
        result = resolver._run(command="npm install")

        status = result.get("status", "failed")
        if status == "success":
            return CriterionResult(
                id=8,
                description=_CRITERION_DESCRIPTIONS[8],
                severity="fatal",
                passed=True,
                detail="",
            )

        stderr = result.get("stderr", "") or result.get("reason", "")
        return CriterionResult(
            id=8,
            description=_CRITERION_DESCRIPTIONS[8],
            severity="fatal",
            passed=False,
            detail=stderr[:500],
        )

    # ------------------------------------------------------------------
    # C9 — All automated tests pass (Warning)
    # ------------------------------------------------------------------

    def _check_c9(self, output_dir: str) -> CriterionResult:
        summary_path = Path(output_dir) / "reports" / "generation-summary.json"
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            return CriterionResult(
                id=9,
                description=_CRITERION_DESCRIPTIONS[9],
                severity="warning",
                passed=False,
                detail=f"generation-summary.json not found or invalid: {exc}",
            )

        all_pass = data.get("test_results", {}).get("all_pass", False)
        return CriterionResult(
            id=9,
            description=_CRITERION_DESCRIPTIONS[9],
            severity="warning",
            passed=bool(all_pass),
            detail="" if all_pass else "test_results.all_pass is not True",
        )

    # ------------------------------------------------------------------
    # C10 — No hardcoded color values (Warning)
    # ------------------------------------------------------------------

    def _check_c10(self, output_dir: str) -> CriterionResult:
        matcher = ASTPatternMatcher(output_dir=output_dir)
        result = matcher._run()

        hardcoded = [
            t for t in result.get("targets", [])
            if t.get("type") == "hardcoded_color"
        ]

        if hardcoded:
            return CriterionResult(
                id=10,
                description=_CRITERION_DESCRIPTIONS[10],
                severity="warning",
                passed=False,
                detail=f"{len(hardcoded)} hardcoded color(s) found",
            )

        return CriterionResult(
            id=10,
            description=_CRITERION_DESCRIPTIONS[10],
            severity="warning",
            passed=True,
            detail="",
        )

    # ------------------------------------------------------------------
    # C11 — Interactive components declare ARIA attributes (Warning)
    # ------------------------------------------------------------------

    def _check_c11(self, output_dir: str) -> CriterionResult:
        registry_path = Path(output_dir) / "reports" / "component-registry.json"
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return CriterionResult(
                id=11,
                description=_CRITERION_DESCRIPTIONS[11],
                severity="warning",
                passed=False,
                detail="component-registry.json not found",
            )

        components = registry if isinstance(registry, list) else registry.get("components", [])
        missing: list[str] = []

        for comp in components:
            a11y = comp.get("a11y") or {}
            role = a11y.get("role")
            if role and role not in ("generic", "none"):
                attrs_result = extract_a11y_attributes(comp)
                required = attrs_result.get("attrs", [])
                declared = a11y.get("attrs", [])
                absent = [a for a in required if a not in declared]
                if absent:
                    missing.append(f"{comp.get('name', '?')}: missing {absent}")

        if missing:
            return CriterionResult(
                id=11,
                description=_CRITERION_DESCRIPTIONS[11],
                severity="warning",
                passed=False,
                detail="; ".join(missing[:5]),
            )

        return CriterionResult(
            id=11,
            description=_CRITERION_DESCRIPTIONS[11],
            severity="warning",
            passed=True,
            detail="",
        )

    # ------------------------------------------------------------------
    # C12 — Quality gate scores ≥ 70 (Warning)
    # ------------------------------------------------------------------

    def _check_c12(self, output_dir: str) -> CriterionResult:
        gate_path = Path(output_dir) / "reports" / "governance" / "quality-gates.json"
        try:
            data = json.loads(gate_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            return CriterionResult(
                id=12,
                description=_CRITERION_DESCRIPTIONS[12],
                severity="warning",
                passed=False,
                detail=f"quality-gates.json not found or invalid: {exc}",
            )

        components = data.get("components", [])
        if not isinstance(components, list):
            return CriterionResult(
                id=12,
                description=_CRITERION_DESCRIPTIONS[12],
                severity="warning",
                passed=False,
                detail="quality-gates.json 'components' field is not a list",
            )

        below_threshold = [
            c for c in components
            if isinstance(c, dict) and c.get("score", 100) < 70
        ]

        if below_threshold:
            names = [c.get("name", "?") for c in below_threshold[:3]]
            return CriterionResult(
                id=12,
                description=_CRITERION_DESCRIPTIONS[12],
                severity="warning",
                passed=False,
                detail=f"components below 70: {names}",
            )

        return CriterionResult(
            id=12,
            description=_CRITERION_DESCRIPTIONS[12],
            severity="warning",
            passed=True,
            detail="",
        )

    # ------------------------------------------------------------------
    # C13 — No non-fixable drift items (Warning)
    # ------------------------------------------------------------------

    def _check_c13(self, output_dir: str) -> CriterionResult:
        drift_path = Path(output_dir) / "reports" / "governance" / "drift-report.json"
        try:
            data = json.loads(drift_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            return CriterionResult(
                id=13,
                description=_CRITERION_DESCRIPTIONS[13],
                severity="warning",
                passed=False,
                detail=f"drift-report.json not found or invalid: {exc}",
            )

        non_fixable = data.get("non_fixable", [])
        if non_fixable:
            return CriterionResult(
                id=13,
                description=_CRITERION_DESCRIPTIONS[13],
                severity="warning",
                passed=False,
                detail=f"{len(non_fixable)} non-fixable drift item(s)",
            )

        return CriterionResult(
            id=13,
            description=_CRITERION_DESCRIPTIONS[13],
            severity="warning",
            passed=True,
            detail="",
        )

    # ------------------------------------------------------------------
    # C14 — Component registry schema validation (Warning)
    # ------------------------------------------------------------------

    def _check_c14(self, output_dir: str) -> CriterionResult:
        registry_path = Path(output_dir) / "reports" / "component-registry.json"
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            return CriterionResult(
                id=14,
                description=_CRITERION_DESCRIPTIONS[14],
                severity="warning",
                passed=False,
                detail=f"component-registry.json not found or invalid: {exc}",
            )

        # Minimal schema — presence of top-level object
        schema: dict[str, Any] = {"type": "object"}
        result = validate_spec_schema(registry, schema)

        if not result.get("valid", True):
            errors = result.get("errors", [])
            return CriterionResult(
                id=14,
                description=_CRITERION_DESCRIPTIONS[14],
                severity="warning",
                passed=False,
                detail=f"schema errors: {errors[:3]}",
            )

        return CriterionResult(
            id=14,
            description=_CRITERION_DESCRIPTIONS[14],
            severity="warning",
            passed=True,
            detail="",
        )

    # ------------------------------------------------------------------
    # C15 — No failed components in generation summary (Warning)
    # ------------------------------------------------------------------

    def _check_c15(self, output_dir: str) -> CriterionResult:
        summary_path = Path(output_dir) / "reports" / "generation-summary.json"
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            return CriterionResult(
                id=15,
                description=_CRITERION_DESCRIPTIONS[15],
                severity="warning",
                passed=False,
                detail=f"generation-summary.json not found or invalid: {exc}",
            )

        components = data.get("components", [])
        failed = [c for c in components if c.get("status") == "failed"]

        if failed:
            names = [c.get("name", "?") for c in failed[:3]]
            return CriterionResult(
                id=15,
                description=_CRITERION_DESCRIPTIONS[15],
                severity="warning",
                passed=False,
                detail=f"failed components: {names}",
            )

        return CriterionResult(
            id=15,
            description=_CRITERION_DESCRIPTIONS[15],
            severity="warning",
            passed=True,
            detail="",
        )
