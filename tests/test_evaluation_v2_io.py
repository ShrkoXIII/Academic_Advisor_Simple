"""Evaluation I/O isolation with real temporary files and synthetic models."""

import json
from pathlib import Path
import runpy

import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest

from src import paths
from src.evaluation import analyze_model_errors as analysis
from src.evaluation import evaluate_plan_gpa as evaluation
from src.features.feature_contract import (
    BASE_FEATURES, CATEGORICAL_FEATURES, NUMERIC_FEATURES,
    learn_category_levels, save_category_levels,
)


INPUTS = {
    "TEMPORAL_TRAIN_FEATURES_PATH": "data/features/temporal_train_features_v2.parquet",
    "TEMPORAL_TEST_FEATURES_PATH": "data/features/temporal_test_features_v2.parquet",
    "GRADE_MODEL_PATH": "models/grade_regressor_v2.txt",
    "CATEGORY_LEVELS_PATH": "data/artifacts/category_levels_v2.json",
    "MODEL_METADATA_PATH": "models/model_metadata_v2.json",
}
PLAN_OUTPUTS = {
    "PLAN_GPA_COURSE_PREDICTIONS_PATH": "data/evaluation/plan_gpa_course_predictions_2025_v2.parquet",
    "PLAN_GPA_EVALUATION_PATH": "data/evaluation/plan_gpa_evaluation_2025_v2.parquet",
    "PLAN_GPA_METRICS_PATH": "data/evaluation/plan_gpa_metrics_2025_v2.json",
}
ERROR_OUTPUTS = {
    "MODEL_ERROR_BY_YEAR_PATH": "data/evaluation/error_analysis/model_error_by_year_v2.parquet",
    "MODEL_ERROR_BY_DEGREE_PATH": "data/evaluation/error_analysis/model_error_by_degree_v2.parquet",
    "MODEL_ERROR_BY_YEAR_DEGREE_PATH": "data/evaluation/error_analysis/model_error_by_year_and_degree_v2.parquet",
    "MODEL_ERROR_PLAN_SEGMENTS_PATH": "data/evaluation/error_analysis/plan_error_segments_v2.parquet",
    "MODEL_ERROR_COURSE_SEGMENTS_PATH": "data/evaluation/error_analysis/course_error_segments_v2.parquet",
    "MODEL_SHAP_IMPORTANCE_PATH": "data/evaluation/error_analysis/grade_model_shap_importance_v2.parquet",
    "MODEL_SHAP_FAMILY_PATH": "data/evaluation/error_analysis/grade_model_shap_families_v2.parquet",
    "MODEL_ERROR_ANALYSIS_SUMMARY_PATH": "data/evaluation/error_analysis/analysis_summary_v2.json",
}


def feature_rows(parts):
    count = len(parts) * 8
    frame = pd.DataFrame({
        **{name: np.ones(count) for name in NUMERIC_FEATURES},
        **{name: ["1"] * count for name in CATEGORICAL_FEATURES},
        "student_course_id": np.arange(count),
        "student_id": list(range(8)) * len(parts),
        "degree_id": ["D1", "D2"] * (count // 2),
        "degree_name_sl_status": ["First", "Second"] * (count // 2),
        "part_id": np.repeat(parts, 8),
        "course_id": ["C"] * count,
        "course_name_sl": ["Course"] * count,
        "course_credits": [3.0] * count,
        "final_mark": [40, 60, 70, 80, 90, 55, 65, 85] * len(parts),
        "points": [0, 2, 2, 3, 4, 2, 2, 3] * len(parts),
        "gpa_points": [2.0] * count,
        "gpa_prev_1": [1, 2, 3, 4, 1.5, 2.5, 3.5, 0.5] * len(parts),
        "course_history_missing": [False, True] * (count // 2),
        "gpa_trend_missing": [True, False] * (count // 2),
    })
    frame.attrs["feature_engineering_version"] = 2
    return frame


class SyntheticGradeModel:
    def predict(self, matrix, pred_contrib=False):
        if pred_contrib:
            return np.tile(np.arange(1, len(BASE_FEATURES) + 2), (len(matrix), 1))
        return matrix["gpa_prev_1"].to_numpy(dtype=float) * 10 + 50

    def feature_name(self):
        return BASE_FEATURES

    def feature_importance(self, importance_type):
        return np.ones(len(BASE_FEATURES))


@pytest.fixture
def isolated_io(tmp_path, monkeypatch):
    legacy, versioned = {}, {}
    for name, relative_path in {**INPUTS, **PLAN_OUTPUTS, **ERROR_OUTPUTS}.items():
        old = tmp_path / getattr(paths, name).relative_to(paths.PROJECT_ROOT)
        new = tmp_path / relative_path
        old.parent.mkdir(parents=True, exist_ok=True)
        old.write_bytes(b"Preserved V1 artifact")
        legacy[name], versioned[name] = old, new
        for module in [evaluation, analysis]:
            monkeypatch.setattr(module, name, old, raising=False)
            monkeypatch.setattr(module, name + "_V2", new, raising=False)
    for module in [evaluation, analysis]:
        monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path, raising=False)
    train, test = feature_rows([20221, 20231, 20243]), feature_rows([20251, 20252])
    for name, frame in [("TEMPORAL_TRAIN_FEATURES_PATH", train),
                        ("TEMPORAL_TEST_FEATURES_PATH", test)]:
        for path in [legacy[name], versioned[name]]:
            path.parent.mkdir(parents=True, exist_ok=True)
            frame.to_parquet(path, index=False)
    metadata = {
        "feature_engineering_version": 2,
        "grade_regressor": {"selected_candidate": {
            "candidate": {"name": "synthetic", "num_leaves": 31,
                          "min_data_in_leaf": 20, "feature_fraction": 0.9,
                          "bagging_fraction": 0.9, "lambda_l1": 0.0,
                          "lambda_l2": 1.0},
            "folds": [{"fold": "validate_2023", "best_iteration": 3},
                      {"fold": "validate_2024", "best_iteration": 5}],
        }},
    }
    for path in [legacy["MODEL_METADATA_PATH"], versioned["MODEL_METADATA_PATH"]]:
        path.write_text(json.dumps(metadata), encoding="utf-8")
    for path in [legacy["CATEGORY_LEVELS_PATH"], versioned["CATEGORY_LEVELS_PATH"]]:
        save_category_levels(learn_category_levels(train), path)
    versioned["GRADE_MODEL_PATH"].write_text("Synthetic V2 grade model", encoding="utf-8")
    scale = tmp_path / "data/raw/v_acs_grade.parquet"
    scale.parent.mkdir(parents=True)
    pd.DataFrame({
        "grade_version_id": [1, 1, 1], "from_percent": [50, 75, 90],
        "points": [2.0, 3.0, 4.0], "grade_show": ["C", "B", "A"],
        "finish_status": ["P", "P", "P"],
    }).to_parquet(scale, index=False)
    for module in [evaluation, analysis]:
        monkeypatch.setattr(module, "GRADE_SCALE_PATH", scale)

    def load_model(model_file):
        # Read the requested file so a missing V2 model cannot be hidden by the double.
        assert Path(model_file).read_text() == "Synthetic V2 grade model"
        return SyntheticGradeModel()

    monkeypatch.setattr(lgb, "Booster", load_model)
    fits = []

    def synthetic_fit(matrix, target, weights, parameters, num_boost_round):
        fits.append((matrix.index.tolist(), num_boost_round))
        return SyntheticGradeModel()

    def forbidden_training(*args, **kwargs):
        raise AssertionError("Real LightGBM training is prohibited in I/O tests")

    monkeypatch.setattr(analysis, "train_one", synthetic_fit)
    monkeypatch.setattr(lgb, "train", forbidden_training)
    before = {name: path.read_bytes() for name, path in legacy.items()}
    before["grade_scale"] = scale.read_bytes()
    reads = []
    original_read = pd.read_parquet
    original_read_text = Path.read_text

    def record_read(path, *args, **kwargs):
        reads.append(Path(path))
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(pd, "read_parquet", record_read)

    def record_read_text(path, *args, **kwargs):
        reads.append(path)
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", record_read_text)
    return legacy, versioned, before, scale, reads, fits


def assert_preserved(legacy, before, scale):
    assert {name: path.read_bytes() for name, path in legacy.items()} == {
        name: value for name, value in before.items() if name != "grade_scale"
    }
    assert scale.read_bytes() == before["grade_scale"]


def test_plan_evaluation_reads_and_writes_v2_with_shared_grade_scale(isolated_io):
    legacy, versioned, before, scale, reads, fits = isolated_io
    evaluation.main()
    assert reads == [versioned["MODEL_METADATA_PATH"],
                     versioned["TEMPORAL_TEST_FEATURES_PATH"],
                     versioned["GRADE_MODEL_PATH"],
                     versioned["CATEGORY_LEVELS_PATH"], scale]
    assert_preserved(legacy, before, scale)
    assert all(versioned[name].is_file() for name in PLAN_OUTPUTS)
    report = json.loads(versioned["PLAN_GPA_METRICS_PATH"].read_text())
    assert report["dataset_version"] == "V2"
    assert report["feature_engineering_version"] == 2
    assert report["sources"] == {
        "test_features": INPUTS["TEMPORAL_TEST_FEATURES_PATH"],
        "grade_model": INPUTS["GRADE_MODEL_PATH"],
        "category_levels": INPUTS["CATEGORY_LEVELS_PATH"],
        "model_metadata": INPUTS["MODEL_METADATA_PATH"],
        "grade_scale": "data/raw/v_acs_grade.parquet",
    }
    assert report["overall"]["plans"] == 16
    plans = pd.read_parquet(versioned["PLAN_GPA_EVALUATION_PATH"])
    row = plans.set_index(["student_id", "degree_id", "part_id"]).loc[(0, "D1", 20251)]
    assert row.actual_plan_gpa == 0
    assert row.predicted_plan_gpa == 2
    assert not fits


def test_error_analysis_uses_v2_in_historical_holdout_and_shap_paths(isolated_io):
    legacy, versioned, before, scale, reads, fits = isolated_io
    analysis.main()
    assert reads == [versioned["MODEL_METADATA_PATH"],
                     versioned["TEMPORAL_TRAIN_FEATURES_PATH"],
                     versioned["TEMPORAL_TEST_FEATURES_PATH"],
                     versioned["GRADE_MODEL_PATH"], scale,
                     versioned["CATEGORY_LEVELS_PATH"],
                     versioned["CATEGORY_LEVELS_PATH"]]
    assert_preserved(legacy, before, scale)
    assert fits == [(list(range(8)), 3), (list(range(16)), 5)]
    assert all(versioned[name].is_file() for name in ERROR_OUTPUTS)
    assert versioned["GRADE_MODEL_PATH"].read_text() == "Synthetic V2 grade model"
    summary = json.loads(versioned["MODEL_ERROR_ANALYSIS_SUMMARY_PATH"].read_text())
    assert summary["dataset_version"] == "V2"
    assert summary["feature_engineering_version"] == 2
    assert summary["sources"] == {
        "train_features": INPUTS["TEMPORAL_TRAIN_FEATURES_PATH"],
        "test_features": INPUTS["TEMPORAL_TEST_FEATURES_PATH"],
        "grade_model": INPUTS["GRADE_MODEL_PATH"],
        "category_levels": INPUTS["CATEGORY_LEVELS_PATH"],
        "model_metadata": INPUTS["MODEL_METADATA_PATH"],
        "grade_scale": "data/raw/v_acs_grade.parquet",
    }
    assert summary["rows"] == {"course_predictions": 32, "plans": 32, "degrees": 2}
    assert summary["prediction_protocol"] == {
        "2023": "trained through 2022", "2024": "trained through 2023",
        "2025": "trained through 2024",
    }
    importance = pd.read_parquet(versioned["MODEL_SHAP_IMPORTANCE_PATH"])
    assert len(importance) == 47
    assert importance.shap_share.sum() == pytest.approx(1)


@pytest.mark.parametrize("module, missing_input", [
    *[(evaluation, name) for name in INPUTS if name != "TEMPORAL_TRAIN_FEATURES_PATH"],
    *[(analysis, name) for name in INPUTS],
])
def test_missing_v2_input_fails_without_v1_fallback_or_output(
    isolated_io, monkeypatch, module, missing_input,
):
    legacy, versioned, before, scale, reads, fits = isolated_io
    missing = versioned[missing_input].with_name("missing_" + versioned[missing_input].name)
    monkeypatch.setattr(module, missing_input + "_V2", missing, raising=False)
    with pytest.raises(FileNotFoundError, match=missing.name):
        module.main()
    assert_preserved(legacy, before, scale)
    assert not any(versioned[name].exists() for name in {**PLAN_OUTPUTS, **ERROR_OUTPUTS})


@pytest.mark.parametrize("module, names", [
    (evaluation, {**{name: path for name, path in INPUTS.items()
                     if name != "TEMPORAL_TRAIN_FEATURES_PATH"}, **PLAN_OUTPUTS}),
    (analysis, {**INPUTS, **ERROR_OUTPUTS}),
])
def test_direct_import_resolves_v2_and_intentionally_shared_scale(module, names):
    namespace = runpy.run_path(module.__file__, run_name="evaluation_io_import_check")
    for name, relative_path in names.items():
        assert namespace.get(name + "_V2") == paths.PROJECT_ROOT / relative_path
        assert name not in namespace
    assert namespace["GRADE_SCALE_PATH"] == paths.PROJECT_ROOT / "data/raw/v_acs_grade.parquet"
    assert not hasattr(paths, "GRADE_SCALE_PATH_V2")
