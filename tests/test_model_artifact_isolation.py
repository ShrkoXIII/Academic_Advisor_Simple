"""Official artifacts stay separate from configured experiment persistence."""

import ast
import hashlib
from importlib.util import resolve_name
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import paths


OFFICIAL = {
    "GRADE_MODEL_PATH": "models/grade_regressor.txt",
    "FAIL_MODEL_PATH": "models/fail_risk_classifier.txt",
    "MODEL_METADATA_PATH": "models/model_metadata.json",
    "CATEGORY_LEVELS_PATH": "data/artifacts/category_levels.json",
}
EXPERIMENT = {
    "DEGREE_POINTS_SELECTED_MODEL_PATH": "models/experiments/degree_points/selected_model.txt",
    "DEGREE_POINTS_CATEGORY_LEVELS_PATH": "models/experiments/degree_points/selected_category_levels.json",
    "DEGREE_POINTS_EXPERIMENT_METADATA_PATH": "data/evaluation/experiments/degree_points/experiment_metadata.json",
    "DEGREE_POINTS_VALIDATION_PATH": "data/evaluation/experiments/degree_points/validation_results.parquet",
    "DEGREE_POINTS_VALIDATION_SUMMARY_PATH": "data/evaluation/experiments/degree_points/validation_summary.parquet",
    "DEGREE_POINTS_HOLDOUT_COURSES_PATH": "data/evaluation/experiments/degree_points/selected_holdout_course_predictions.parquet",
    "DEGREE_POINTS_HOLDOUT_PLANS_PATH": "data/evaluation/experiments/degree_points/selected_holdout_plan_predictions.parquet",
    "DEGREE_POINTS_HOLDOUT_BY_DEGREE_PATH": "data/evaluation/experiments/degree_points/selected_holdout_by_degree.parquet",
}


@pytest.mark.parametrize("name, relative", [*OFFICIAL.items(), *EXPERIMENT.items()])
@pytest.mark.parametrize("version", ["", "_V2"])
def test_artifact_namespaces(name, relative, version):
    expected = Path(relative)
    if version:
        expected = expected.with_name(f"{expected.stem}_v2{expected.suffix}")
    actual = getattr(paths, name + version)
    assert actual == paths.PROJECT_ROOT / expected
    if name in OFFICIAL:
        assert "experiments" not in actual.relative_to(paths.PROJECT_ROOT).parts


def isolation_violations(source, package, *, allow_recommendation=False):
    """Find experiment imports and artifact references, including aliases."""
    violations = []
    for node in ast.walk(ast.parse(source)):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = resolve_name("." * node.level + module, package)
            names = [module, *(f"{module}.{alias.name}" for alias in node.names)]
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Name):
            names = [node.id]
        elif isinstance(node, ast.Attribute):
            names = [node.attr]
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            names = [node.value.replace("\\", "/")]
        if any(
            name == "src.experiments" or name.startswith("src.experiments.")
            or (not allow_recommendation and (
                name == "src.recommendation" or name.startswith("src.recommendation.")
            ))
            or name.startswith("DEGREE_POINTS_")
            or "models/experiments/" in name
            or "data/evaluation/experiments/" in name
            for name in names
        ):
            violations.append(node.lineno)
    return violations


@pytest.mark.parametrize("source, package", [
    ("import src.experiments.modeling as helper", "src.modeling"),
    ("from src.experiments import modeling as helper", "src.evaluation"),
    ("from ..experiments.modeling import prepare_matrix", "src.features"),
    ("from .. import experiments as helper", "src.data"),
    ("from src import experiments as helper", "src.modeling"),
    ("from src.recommendation import AcademicPlanRecommender", "src.evaluation"),
    ("from ...experiments import modeling", "src.data.nested"),
    ("from src.paths import DEGREE_POINTS_SELECTED_MODEL_PATH_V2 as model", "src.modeling"),
    ("model = paths.DEGREE_POINTS_CATEGORY_LEVELS_PATH", "src.evaluation"),
    ("model = 'models/experiments/degree_points/selected_model_v2.txt'", "src.evaluation"),
    ("meta = 'data/evaluation/experiments/degree_points/experiment_metadata.json'", "src.data"),
])
def test_dependency_checker_detects_forbidden_imports_and_paths(source, package):
    assert isolation_violations(source, package)


def test_dependency_checker_allows_official_and_local_imports():
    source = "from ..paths import GRADE_MODEL_PATH_V2\nfrom .training_config import training_weights"
    assert isolation_violations(source, "src.modeling") == []


def test_xml_recommendation_exception_does_not_allow_direct_experiment_imports():
    assert isolation_violations(
        "from src.recommendation import AcademicPlanRecommender", "src.evaluation",
        allow_recommendation=True,
    ) == []
    assert isolation_violations(
        "from src.experiments import modeling", "src.evaluation",
        allow_recommendation=True,
    )


@pytest.mark.parametrize("package", ["data", "features", "modeling", "evaluation"])
def test_official_packages_do_not_depend_on_experiments(package):
    violations = {}
    for path in (paths.PROJECT_ROOT / "src" / package).rglob("*.py"):
        parent_package = ".".join(path.parent.relative_to(paths.PROJECT_ROOT).parts)
        # This serving evaluator may import Official Recommendation V2.
        # It is not the official V2 baseline GPA/error evaluator; see the policy.
        allow_recommendation = path.relative_to(paths.PROJECT_ROOT).as_posix() == (
            "src/evaluation/evaluate_xml_recommendations.py"
        )
        found = isolation_violations(
            path.read_text(encoding="utf-8-sig"), parent_package,
            allow_recommendation=allow_recommendation,
        )
        if found:
            violations[path.relative_to(paths.PROJECT_ROOT).as_posix()] = found
    assert violations == {}


def test_experiment_saves_preserve_official_v2_and_legacy_hashes(tmp_path, monkeypatch):
    from src.experiments import degree_points, experiment_io, modeling
    from src.experiments.degree_points_config import VARIANTS
    from src.grade_scale import GradeScale

    protected = []
    for name, relative in OFFICIAL.items():
        for version in ["", "_V2"]:
            path = tmp_path / relative
            if version:
                path = path.with_name(f"{path.stem}_v2{path.suffix}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"Dummy protected artifact: {name}{version}".encode())
            protected.append(path)
            for module in [paths, degree_points, experiment_io, modeling]:
                monkeypatch.setattr(module, name + version, path, raising=False)
    outputs = {}
    for name, relative in EXPERIMENT.items():
        legacy = tmp_path / relative
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_bytes(f"Dummy legacy experiment artifact: {name}".encode())
        protected.append(legacy)
        path = legacy.with_name(f"{legacy.stem}_v2{legacy.suffix}")
        outputs[name] = path
        for module in [degree_points, experiment_io]:
            monkeypatch.setattr(module, name, legacy, raising=False)
            monkeypatch.setattr(module, name + "_V2", path, raising=False)
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}
    for name in ["TEMPORAL_TRAIN_FEATURES_PATH_V2", "TEMPORAL_TEST_FEATURES_PATH_V2",
                 "PLAN_GPA_METRICS_PATH_V2", "PLAN_GPA_EVALUATION_PATH_V2", "GRADE_SCALE_PATH"]:
        relative = getattr(experiment_io, name).relative_to(paths.PROJECT_ROOT)
        monkeypatch.setattr(experiment_io, name, tmp_path / relative)
    monkeypatch.setattr(experiment_io, "PROJECT_ROOT", tmp_path)

    selected = next(v for v in VARIANTS if v["name"] == "degree_history_mark_temporal")
    numeric, categorical = modeling.feature_columns(selected["feature_profile"])
    frame = pd.DataFrame({
        **{name: [1.0] for name in numeric},
        **{name: ["1"] for name in categorical},
        "student_course_id": ["synthetic"], "student_id": ["S"],
        "degree_id": ["D"], "degree_name_sl_status": ["Synthetic degree"],
        "part_id": [20251], "course_id": ["C"], "course_credits": [3.0],
        "final_mark": [70.0], "points": [2.0],
    })
    levels = modeling.learn_levels(frame, categorical)

    class SyntheticModel:
        def predict(self, matrix):
            return np.full(len(matrix), 70.0)

        def save_model(self, filename):
            Path(filename).write_text("Synthetic experiment model", encoding="utf-8")

    # Only fitting is mocked; routing, conversion, aggregation and serialization are real.
    monkeypatch.setattr(modeling, "fit_experiment_model", lambda *a, **kw: (SyntheticModel(), levels, None))
    scale = GradeScale(pd.DataFrame({
        "grade_version_id": [1], "from_percent": [50], "points": [2.0], "grade_show": ["C"],
    }))
    predictions, plans, metrics = degree_points.load_or_train_holdout(
        frame, frame, selected, 1, {}, scale, "synthetic-signature",
    )
    summary = pd.DataFrame({"variant": [selected["name"]], "mean_plan_gpa_mae": [0.0]})
    metadata = experiment_io.build_metadata(
        selected, 1, summary, metrics, {"mae": 0.5}, "synthetic-signature",
        train_parts=[20243], test_parts=[20251],
    )
    by_degree = pd.DataFrame({"degree_id": ["D"]})
    experiment_io.save_results(summary, summary, predictions, plans, by_degree, metadata)

    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected} == before
    assert outputs["DEGREE_POINTS_SELECTED_MODEL_PATH"].read_text() == "Synthetic experiment model"
    assert json.loads(outputs["DEGREE_POINTS_CATEGORY_LEVELS_PATH"].read_text()) == levels
    for name, expected in [
        ("DEGREE_POINTS_VALIDATION_PATH", summary),
        ("DEGREE_POINTS_VALIDATION_SUMMARY_PATH", summary),
        ("DEGREE_POINTS_HOLDOUT_COURSES_PATH", predictions),
        ("DEGREE_POINTS_HOLDOUT_PLANS_PATH", plans),
        ("DEGREE_POINTS_HOLDOUT_BY_DEGREE_PATH", by_degree),
    ]:
        pd.testing.assert_frame_equal(pd.read_parquet(outputs[name]), expected)
    saved = json.loads(outputs["DEGREE_POINTS_EXPERIMENT_METADATA_PATH"].read_text())
    assert saved["dataset_version"] == "V2"
    assert saved["selected_variant"]["name"] == "degree_history_mark_temporal"
    assert saved["experiment_signature"] == "synthetic-signature"
    assert saved["selection_protocol"]
    assert saved["holdout_2025"]["selected"]["plan_gpa_mae"] == 0.0
    assert saved["artifacts"]["model"] == "models/experiments/degree_points/selected_model_v2.txt"
    assert saved["artifacts"]["category_levels"] == "models/experiments/degree_points/selected_category_levels_v2.json"
