"""Official V2 inference and artifact isolation using only synthetic data."""

import ast
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest

from src import paths
from src.features.feature_contract import BASE_FEATURES, CATEGORICAL_FEATURES, NUMERIC_FEATURES
from src.recommendation import artifacts
from tests.recommendation_fixtures import synthetic_engine, synthetic_snapshot, synthetic_candidates


@pytest.fixture
def official_artifacts(tmp_path, monkeypatch):
    relative = {
        "GRADE_MODEL_PATH_V2": "models/grade_regressor_v2.txt",
        "FAIL_MODEL_PATH_V2": "models/fail_risk_classifier_v2.txt",
        "CATEGORY_LEVELS_PATH_V2": "data/artifacts/category_levels_v2.json",
        "MODEL_METADATA_PATH_V2": "models/model_metadata_v2.json",
        "GRADE_SCALE_PATH": "data/raw/v_acs_grade.parquet",
    }
    relocated = {}
    for name, text in relative.items():
        path = tmp_path / text
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Synthetic official model")
        relocated[name] = path
        monkeypatch.setattr(artifacts, name, path, raising=False)
    metadata = {
        "feature_engineering_version": 2,
        "feature_contract": {"model_features": BASE_FEATURES, "numeric_features": NUMERIC_FEATURES,
                             "categorical_features": CATEGORICAL_FEATURES, "feature_count": 47},
        "targets": {"grade_regressor": "final_mark"},
        "course_history": {"initial_history_cutoff": 20243},
        "grade_regressor": {"selected_candidate": {"candidate": {"name": "capacity_63"}}},
        "fail_risk_classifier": {"selected_candidate": {"candidate": {"name": "balanced_31"}}},
        "artifacts": {"grade_model": relative["GRADE_MODEL_PATH_V2"],
                      "fail_model": relative["FAIL_MODEL_PATH_V2"],
                      "category_levels": relative["CATEGORY_LEVELS_PATH_V2"],
                      "model_metadata": relative["MODEL_METADATA_PATH_V2"]},
    }
    relocated["MODEL_METADATA_PATH_V2"].write_text(json.dumps(metadata))
    levels = {c: ["__MISSING__", "__UNKNOWN__", "1", "T", "R"] for c in CATEGORICAL_FEATURES}
    relocated["CATEGORY_LEVELS_PATH_V2"].write_text(json.dumps(levels))
    pd.DataFrame({"grade_version_id": [1], "from_percent": [50.], "points": [2.],
                  "grade_show": ["C"], "finish_status": ["P"]}).to_parquet(relocated["GRADE_SCALE_PATH"])
    # Leave valid older artifacts present, but any access to them is forbidden.
    forbidden = []
    for name in ["GRADE_MODEL_PATH", "FAIL_MODEL_PATH", "MODEL_METADATA_PATH", "CATEGORY_LEVELS_PATH",
                 "DEGREE_POINTS_SELECTED_MODEL_PATH", "DEGREE_POINTS_CATEGORY_LEVELS_PATH",
                 "DEGREE_POINTS_EXPERIMENT_METADATA_PATH"]:
        for suffix in ["", "_V2"] if name.startswith("DEGREE_POINTS") else [""]:
            path = tmp_path / "forbidden" / (name + suffix + ".json")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(metadata))
            forbidden.append(path)
            monkeypatch.setattr(artifacts, name + suffix, path, raising=False)
    reads, model_reads, history_calls = [], [], []
    original_text, original_parquet = Path.read_text, pd.read_parquet

    def read_text(path, *args, **kwargs):
        assert path not in forbidden
        reads.append(path)
        return original_text(path, *args, **kwargs)

    def read_parquet(path, *args, **kwargs):
        assert Path(path) not in forbidden
        reads.append(Path(path))
        return original_parquet(path, *args, **kwargs)

    def booster(*, model_file):
        path = Path(model_file)
        assert path not in forbidden
        model_reads.append(path)
        return SimpleNamespace(feature_name=lambda: BASE_FEATURES.copy())

    def history(cutoff, **kwargs):
        history_calls.append((cutoff, kwargs))
        return SimpleNamespace(as_of_part=cutoff), None, {"dataset_version": "V2", "as_of_part": cutoff}

    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr(pd, "read_parquet", read_parquet)
    monkeypatch.setattr(lgb, "Booster", booster)
    monkeypatch.setattr(artifacts, "load_frozen_history", history)
    return relocated, metadata, reads, model_reads, history_calls


def test_loader_reads_only_official_v2_artifacts(official_artifacts):
    files, metadata, reads, models, history = official_artifacts
    components = artifacts.load_recommendation_artifacts(history_as_of_part=20243)
    assert models == [files["GRADE_MODEL_PATH_V2"], files["FAIL_MODEL_PATH_V2"]]
    assert set(reads) == {files["CATEGORY_LEVELS_PATH_V2"], files["MODEL_METADATA_PATH_V2"], files["GRADE_SCALE_PATH"]}
    assert history == [(20243, {"root": paths.FROZEN_HISTORY_DIR_V2, "dataset_version": "V2"})]
    assert len(components) == 7
    provenance = components[-1]
    assert provenance["dataset_version"] == "V2"
    assert provenance["grade_model_target"] == "final_mark"
    assert provenance["expected_points_method"] == "predicted_mark_to_grade_scale"
    for key, name in {"grade_model": "GRADE_MODEL_PATH_V2", "fail_model": "FAIL_MODEL_PATH_V2",
                      "category_levels": "CATEGORY_LEVELS_PATH_V2", "model_metadata": "MODEL_METADATA_PATH_V2",
                      "grade_scale": "GRADE_SCALE_PATH"}.items():
        assert provenance[key]["path"] == str(files[name].resolve())
        assert len(provenance[key]["sha256"]) == 64


@pytest.mark.parametrize("missing", ["GRADE_MODEL_PATH_V2", "FAIL_MODEL_PATH_V2", "CATEGORY_LEVELS_PATH_V2",
                                    "MODEL_METADATA_PATH_V2", "GRADE_SCALE_PATH"])
def test_missing_official_artifact_never_falls_back(official_artifacts, monkeypatch, missing):
    files, _, _, _, _ = official_artifacts
    absent = files[missing].with_name("missing_" + files[missing].name)
    monkeypatch.setattr(artifacts, missing, absent)
    with pytest.raises(FileNotFoundError, match=absent.name):
        artifacts.load_recommendation_artifacts(history_as_of_part=20243)


@pytest.mark.parametrize("problem", ["version", "features", "target", "candidate", "model_features", "categories"])
def test_loader_rejects_incompatible_official_contract(official_artifacts, monkeypatch, problem):
    files, metadata, _, _, _ = official_artifacts
    if problem == "version":
        metadata["feature_engineering_version"] = 1
    elif problem == "features":
        metadata["feature_contract"]["model_features"] = BASE_FEATURES[::-1]
    elif problem == "target":
        metadata["targets"]["grade_regressor"] = "points"
    elif problem == "candidate":
        metadata["grade_regressor"]["selected_candidate"]["candidate"]["name"] = "experiment"
    elif problem == "model_features":
        monkeypatch.setattr(lgb, "Booster", lambda **kw: SimpleNamespace(feature_name=lambda: BASE_FEATURES[:-1]))
    else:
        files["CATEGORY_LEVELS_PATH_V2"].write_text("{}")
    files["MODEL_METADATA_PATH_V2"].write_text(json.dumps(metadata))
    with pytest.raises(ValueError):
        artifacts.load_recommendation_artifacts(history_as_of_part=20243)


def test_mark_to_points_uses_versioned_grade_scale_and_shared_matrix():
    engine = synthetic_engine(grade=75., fail=.23)
    engine.grade_scale.pass_bands = pd.DataFrame({
        "grade_version_id": [1, 1, 2, 2], "from_percent": [50., 75., 50., 75.],
        "points": [1., 3., 1.5, 2.5], "grade_show": ["D", "B", "D2", "B2"],
    })
    prepared = engine.prepare_candidates(synthetic_snapshot(), synthetic_candidates(2), 20251)
    prepared["grade_version_id"] = [1, 2]
    prepared["plan_id"] = 0
    matrices = []

    def predict(matrix, **kwargs):
        matrices.append(matrix)
        return np.full(len(matrix), 75. if len(matrices) == 1 else .23)

    engine.grade_model.predict = engine.fail_model.predict = predict
    scored = engine.score_rows(prepared)
    assert scored.predicted_mark.tolist() == [75., 75.]
    assert scored.expected_points.tolist() == [3., 2.5]
    assert scored.expected_grade.tolist() == ["B", "B2"]
    assert scored.fail_probability.tolist() == [.23, .23]
    assert matrices[0] is matrices[1]
    assert list(matrices[0]) == BASE_FEATURES


@pytest.mark.parametrize("mark,fail,want_mark,want_points,want_fail", [
    (-5., -.2, 0., 0., 0.), (105., 1.4, 100., 4., 1.), (75., .23, 75., 3., .23),
])
def test_prediction_clipping(mark, fail, want_mark, want_points, want_fail):
    engine = synthetic_engine(grade=mark, fail=fail)
    prepared = engine.prepare_candidates(synthetic_snapshot(), synthetic_candidates(1), 20251).assign(plan_id=0)
    scored = engine.score_rows(prepared)
    assert scored.predicted_mark.iloc[0] == want_mark
    assert scored.expected_points.iloc[0] == want_points
    assert scored.fail_probability.iloc[0] == want_fail


@pytest.mark.parametrize("mark,fail", [(np.nan, .2), (np.inf, .2), (70., np.inf), (70., np.nan)])
def test_nonfinite_predictions_fail_before_clipping(mark, fail):
    engine = synthetic_engine(grade=mark, fail=fail)
    rows = engine.prepare_candidates(synthetic_snapshot(), synthetic_candidates(1), 20251).assign(plan_id=0)
    with pytest.raises(ValueError, match="non-finite"):
        engine.score_rows(rows)


def test_missing_feature_fails_and_unknown_categories_use_saved_levels():
    engine = synthetic_engine()
    rows = engine.prepare_candidates(synthetic_snapshot(), synthetic_candidates(1), 20251).assign(plan_id=0)
    with pytest.raises(ValueError, match="Missing.*BASE_FEATURES"):
        engine.score_rows(rows.drop(columns="gpa_prev_1"))
    rows["diploma_type_id"] = "not_in_saved_categories"
    engine.score_rows(rows)
    assert engine.grade_model.matrices[-1].diploma_type_id.iloc[0] == "__UNKNOWN__"


def test_exact_upper_bound_no_fallback_result_metadata():
    engine = synthetic_engine()
    candidates = synthetic_candidates(3)
    candidates["course_credits"] = [6., 6., 3.]
    plans, result = engine.recommend(synthetic_snapshot(), candidates, 20251, 3.5, min_credits=12, max_credits=18)
    assert plans.empty
    assert result["status"] == "no_matching_credit_plan"
    assert result["target_credits"] == 18
    assert (result["requested_min_credits"], result["requested_max_credits"]) == (12, 18)
    assert result["matching_plan_count"] == result["returned_plan_count"] == 0
    assert result["reason"] == "No candidate combination exactly matches target_credits=18."
    assert result["dataset_version"] == "V2"
    assert result["grade_model_target"] == "final_mark"
    assert result["expected_points_method"] == "predicted_mark_to_grade_scale"
    assert result["credit_policy"] == "upper_bound_exact"


def test_twenty_poor_plans_are_all_saved_and_top_three_returned(tmp_path):
    from src.recommendation.output import save_recommendations
    engine = synthetic_engine(grade=60.)
    result = save_recommendations(
        engine, tmp_path, student_snapshot=synthetic_snapshot(), candidate_courses=synthetic_candidates(6),
        part_id=20251, current_gpa=4., min_credits=3, max_credits=9, batch_size=2,
    )
    plans = pd.read_parquet(tmp_path / "plans.parquet")
    courses = pd.read_parquet(tmp_path / "courses.parquet")
    assert len(plans) == result["scored_plan_count"] == result["matching_plan_count"] == 20
    assert plans.total_credits.eq(9).all()
    assert plans.projected_cumulative_gpa.lt(4).all()
    assert result["returned_plan_count"] == 3
    assert result["plans_with_expected_improvement"] == 0
    assert not result["has_expected_improvement"]
    assert len(courses) == 60
    assert {"predicted_mark", "expected_points", "expected_grade", "fail_probability"} <= set(courses)


def test_recommendation_source_has_no_experiment_or_legacy_path_dependency():
    forbidden = {"GRADE_MODEL_PATH", "FAIL_MODEL_PATH", "MODEL_METADATA_PATH", "CATEGORY_LEVELS_PATH",
                 "CLEAN_DEGREE_COURSE_PATH", "CLEAN_STUDENT_COURSE_PATH", "CLEAN_STUDENT_STATUS_PATH",
                 "CLEAN_STUDENT_DIPLOMA_PATH", "TEMPORAL_TRAIN_FEATURES_PATH", "TEMPORAL_TEST_FEATURES_PATH"}
    for path in (paths.PROJECT_ROOT / "src/recommendation").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or "", *(alias.name for alias in node.names)]
            elif isinstance(node, ast.Name):
                names = [node.id]
            elif isinstance(node, ast.Attribute):
                names = [node.attr]
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                names = [node.value]
            assert not any(n in forbidden or n.startswith("DEGREE_POINTS_") or n == "FrozenSpecialtyHistory"
                           or n.startswith("src.experiments") or n.startswith("experiments")
                           or "models/experiments/" in n for n in names), (path, node.lineno, names)


def test_importing_public_api_does_not_load_models(monkeypatch):
    def forbidden_load(**kwargs):
        raise AssertionError("Import must not load artifacts")
    monkeypatch.setattr(lgb, "Booster", forbidden_load)
    module = importlib.reload(importlib.import_module("src.recommendation"))
    assert module.AcademicPlanRecommender


@pytest.mark.parametrize("count", [1, 2, 3])
def test_default_top_three_returns_every_available_plan_when_fewer_exist(count):
    plans, result = synthetic_engine().recommend(
        synthetic_snapshot(), synthetic_candidates(count), 20251, 4., credits=3,
    )
    assert len(plans) == result["matching_plan_count"] == count
    assert result["returned_plan_count"] == count


def test_benchmark_adapter_uses_v2_inputs_with_a_tiny_synthetic_request(tmp_path, monkeypatch):
    from src.recommendation import benchmark as adapter
    catalog = pd.DataFrame({
        "degree_id": ["D"] * 25, "course_id": [f"C{i:02d}" for i in range(25)],
        "course_credits": [3.] * 25, "course_name_sl": ["Synthetic"] * 25,
        "course_type_id": ["T"] * 25, "requirement_type_id": ["R"] * 25,
        "year_order": [1] * 25, "semester_order": [1] * 25, "credits_count": [120] * 25,
    })
    snapshot = {**synthetic_snapshot(), "start_agpa_points": 3.}
    history = pd.DataFrame(columns=["student_id", "course_id", "part_id", "attempt_number"])
    sources = {adapter.CLEAN_DEGREE_COURSE_PATH_V2: catalog,
               adapter.TEMPORAL_TEST_FEATURES_PATH_V2: pd.DataFrame([snapshot]),
               adapter.CLEAN_STUDENT_COURSE_PATH_V2: history}
    reads = []
    real_read = pd.read_parquet

    def read(path, **kwargs):
        if path in sources:
            reads.append(path)
            return sources[path].copy()
        return real_read(path, **kwargs)

    monkeypatch.setattr(pd, "read_parquet", read)
    monkeypatch.setattr(adapter.AcademicPlanRecommender, "load", lambda **kwargs: synthetic_engine())
    monkeypatch.setattr(adapter, "peak_memory_mib", lambda: 1.)
    output = tmp_path / "synthetic_benchmark"
    adapter.benchmark(3, output, 1, 20243)
    result = json.loads((output / "result.json").read_text())
    assert reads == list(sources)
    assert result["dataset_version"] == "V2"
    assert result["target_credits"] == 18
    assert result["matching_plan_count"] == 0
    assert pd.read_parquet(output / "courses.parquet").empty
