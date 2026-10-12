"""Canonical API ownership and compatibility remain independent of HTTP startup."""
import ast
import importlib
from pathlib import Path
import subprocess
import sys

import pytest


API_ROOT = Path(__file__).resolve().parents[1] / "src" / "api"


@pytest.mark.parametrize("legacy,canonical,name", [
    ("student_adapter", "adapters.student", "adapt_student"),
    ("courses_adapter", "adapters.courses", "adapt_courses"),
    ("history_adapter", "adapters.history", "adapt_history_delta"),
])
def test_legacy_adapters_reexport_the_canonical_function(legacy, canonical, name):
    old = importlib.import_module("src.api." + legacy)
    current = importlib.import_module("src.api." + canonical)
    assert getattr(old, name) is getattr(current, name)
    assert getattr(current, name).__module__ == "src.api." + canonical
    # The old import path must stay a compatibility shim, so future fixes have
    # one owner and cannot accidentally diverge between callers.
    tree = ast.parse((API_ROOT / (legacy + ".py")).read_text(encoding="utf8"))
    assert not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                   for node in ast.walk(tree))


@pytest.mark.parametrize("name", [
    "ApiError", "ValidationResult", "identifier", "number", "part",
    "response_data", "identity", "check_record_identity", "binding", "sourced", "json_safe",
])
def test_validation_compatibility_retains_class_and_function_identity(name):
    legacy = importlib.import_module("src.api.validation")
    canonical = importlib.import_module("src.api.validators.common")
    assert getattr(legacy, name) is getattr(canonical, name)


def test_transport_independent_layers_do_not_import_http_or_service():
    files = [*API_ROOT.joinpath("adapters").glob("*.py"),
             *API_ROOT.joinpath("validators").glob("*.py")]
    assert files, "Canonical adapters and validators must exist."
    forbidden = {"fastapi", "starlette", "pydantic", "httpx", "requests"}
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(alias.name.split(".")[0] in forbidden for alias in node.names), path
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module.split(".")[0] not in forbidden, path
                assert module not in {"app", "service", "backend_client", "src.api.app",
                                      "src.api.service", "src.api.backend_client"}, path


def test_service_uses_canonical_adapter_functions():
    service = importlib.import_module("src.api.service")
    for module, name in [("student", "adapt_student"), ("courses", "adapt_courses"),
                         ("history", "adapt_history_delta")]:
        canonical = importlib.import_module("src.api.adapters." + module)
        assert getattr(service, name) is getattr(canonical, name)


def test_canonical_imports_do_not_require_http_dependencies_or_start_transport():
    # A fresh interpreter prevents earlier HTTP tests from masking eager imports.
    script = """
import sys
from src.api.adapters.student import adapt_student
from src.api.adapters.courses import adapt_courses
from src.api.adapters.history import adapt_history_delta
from src.api.validators.common import ApiError, ValidationResult
from src.api.service import ApiService
assert 'fastapi' not in sys.modules
assert 'starlette' not in sys.modules
assert 'pydantic' not in sys.modules
assert 'src.api.app' not in sys.modules
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True,
                            text=True, timeout=30, cwd=API_ROOT.parents[1])
    assert result.returncode == 0, result.stderr
