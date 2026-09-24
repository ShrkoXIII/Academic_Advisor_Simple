"""Keep recommendation serving downstream of the data and model packages."""

import ast
import importlib
import importlib.util
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
UPSTREAM_PACKAGES = ("data", "features", "modeling", "evaluation", "experiments")


def _import_targets(node, package):
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        base = (
            importlib.util.resolve_name("." * node.level + (node.module or ""), package)
            if node.level
            else node.module or ""
        )
        return [base, *(f"{base}.{alias.name}" for alias in node.names)]
    return []


def test_upstream_packages_do_not_import_recommendation():
    for package_name in UPSTREAM_PACKAGES:
        for source in (SRC_ROOT / package_name).rglob("*.py"):
            package = ".".join(("src", *source.relative_to(SRC_ROOT).parts[:-1]))
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
            for node in ast.walk(tree):
                for target in _import_targets(node, package):
                    assert target != "src.recommendation" and not target.startswith(
                        "src.recommendation."
                    ), f"{source}:{node.lineno} imports {target}"


def test_course_plan_change_diagnostic_uses_package_location():
    source = SRC_ROOT / "diagnostics" / "analyze_course_plan_changes.py"
    assert source.is_file()
    assert not (SRC_ROOT / "analyze_course_plan_changes.py").exists()
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    assert any(
        isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "src.paths"
        for node in ast.walk(tree)
    )
    assert callable(importlib.import_module("src.diagnostics.analyze_course_plan_changes").main)
