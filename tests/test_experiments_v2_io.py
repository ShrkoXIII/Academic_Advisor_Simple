"""Exercise the experiment coordinator with V2 caches and temporary artifacts."""

import hashlib
import json
from pathlib import Path
import shutil

import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest

from src import paths
from src.experiments import degree_points as experiment
from src.experiments import experiment_io
from src.experiments.degree_points_config import VARIANTS
from src.features.feature_contract import CATEGORICAL_FEATURES, NUMERIC_FEATURES


INPUTS = {
    "TEMPORAL_TRAIN_FEATURES_PATH": "data/features/temporal_train_features_v2.parquet",
    "TEMPORAL_TEST_FEATURES_PATH": "data/features/temporal_test_features_v2.parquet",
    "MODEL_METADATA_PATH": "models/model_metadata_v2.json",
    "PLAN_GPA_EVALUATION_PATH": "data/evaluation/plan_gpa_evaluation_2025_v2.parquet",
    "PLAN_GPA_METRICS_PATH": "data/evaluation/plan_gpa_metrics_2025_v2.json",
}
OUTPUTS = {
    "DEGREE_POINTS_VALIDATION_PATH": "data/evaluation/experiments/degree_points/validation_results_v2.parquet",
    "DEGREE_POINTS_VALIDATION_SUMMARY_PATH": "data/evaluation/experiments/degree_points/validation_summary_v2.parquet",
    "DEGREE_POINTS_HOLDOUT_COURSES_PATH": "data/evaluation/experiments/degree_points/selected_holdout_course_predictions_v2.parquet",
    "DEGREE_POINTS_HOLDOUT_PLANS_PATH": "data/evaluation/experiments/degree_points/selected_holdout_plan_predictions_v2.parquet",
    "DEGREE_POINTS_HOLDOUT_BY_DEGREE_PATH": "data/evaluation/experiments/degree_points/selected_holdout_by_degree_v2.parquet",
    "DEGREE_POINTS_EXPERIMENT_METADATA_PATH": "data/evaluation/experiments/degree_points/experiment_metadata_v2.json",
    "DEGREE_POINTS_SELECTED_MODEL_PATH": "models/experiments/degree_points/selected_model_v2.txt",
    "DEGREE_POINTS_CATEGORY_LEVELS_PATH": "models/experiments/degree_points/selected_category_levels_v2.json",
}


def feature_rows(parts):
    count = len(parts) * 2
    frame = pd.DataFrame({
        **{name: np.ones(count) for name in NUMERIC_FEATURES},
        **{name: ["1"] * count for name in CATEGORICAL_FEATURES},
        "student_course_id": np.arange(count), "student_id": ["A", "B"] * len(parts),
        "degree_id": ["D"] * count, "degree_name_sl_status": ["Degree"] * count,
        "part_id": np.repeat(parts, 2), "course_id": ["C"] * count,
        "course_credits": [3.0] * count, "final_mark": [70.0] * count,
        "is_fail": [0] * count, "points": [2.0] * count,
    })
    frame.attrs["feature_engineering_version"] = 2
    return frame


class SyntheticModel:
    best_iteration = 5

    def predict(self, matrix, **kwargs):
        return np.full(len(matrix), 2.5)

    def save_model(self, filename):
        Path(filename).write_text("Synthetic selected model", encoding="utf-8")


@pytest.fixture
def isolated_io(tmp_path, monkeypatch):
    legacy, versioned = {}, {}
    for name, relative in {**INPUTS, **OUTPUTS}.items():
        old = tmp_path / getattr(paths, name).relative_to(paths.PROJECT_ROOT)
        new = tmp_path / relative
        old.parent.mkdir(parents=True, exist_ok=True)
        old.write_bytes(b"Preserved V1 artifact")
        legacy[name], versioned[name] = old, new
        for module in [experiment, experiment_io]:
            monkeypatch.setattr(module, name, old, raising=False)
            monkeypatch.setattr(module, name + "_V2", new, raising=False)
    monkeypatch.setattr(experiment_io, "PROJECT_ROOT", tmp_path)
    for source in (paths.PROJECT_ROOT / "src/experiments").glob("*.py"):
        target = tmp_path / "src/experiments" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for relative in ["src/features/feature_contract.py", "src/modeling/train_models.py",
                     "src/modeling/training_config.py"]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(paths.PROJECT_ROOT / relative, target)
    for name, frame in [
        ("TEMPORAL_TRAIN_FEATURES_PATH", feature_rows([20221, 20231, 20243])),
        ("TEMPORAL_TEST_FEATURES_PATH", feature_rows([20251, 20252])),
    ]:
        for path in [legacy[name], versioned[name]]:
            frame.to_parquet(path, index=False)
    candidate = {"name": "chosen_from_v2_metadata", "num_leaves": 17,
                 "min_data_in_leaf": 4, "feature_fraction": 0.9,
                 "bagging_fraction": 0.8, "lambda_l1": 0.0, "lambda_l2": 1.0}
    for path, selected in [(versioned["MODEL_METADATA_PATH"], candidate),
                           (legacy["MODEL_METADATA_PATH"], {**candidate, "num_leaves": 31})]:
        path.write_text(json.dumps({"feature_engineering_version": 2,
                                   "grade_regressor": {"selected_candidate": {"candidate": selected}}}),
                        encoding="utf-8")
    baseline = pd.DataFrame({
        "degree_id": ["D"], "total_credits": [3.0], "plan_gpa_error": [1.0],
        "plan_gpa_absolute_error": [1.0],
    })
    for path in [legacy["PLAN_GPA_EVALUATION_PATH"], versioned["PLAN_GPA_EVALUATION_PATH"]]:
        baseline.to_parquet(path, index=False)
    for path, mae in [(legacy["PLAN_GPA_METRICS_PATH"], 99),
                      (versioned["PLAN_GPA_METRICS_PATH"], 1)]:
        path.write_text(json.dumps({"feature_engineering_version": 2, "overall": {"mae": mae}}),
                        encoding="utf-8")
    scale = tmp_path / "data/raw/v_acs_grade.parquet"
    scale.parent.mkdir(parents=True)
    pd.DataFrame({"grade_version_id": [1], "from_percent": [50], "points": [2.0],
                  "grade_show": ["C"], "finish_status": ["P"]}).to_parquet(scale, index=False)
    for module in [experiment, experiment_io]:
        monkeypatch.setattr(module, "GRADE_SCALE_PATH", scale)
    signature = experiment_io.experiment_signature()
    winner = "degree_history_points_temporal"
    cached = []
    for variant in VARIANTS:
        for year in [2023, 2024]:
            mae = 0.2 if variant["name"] == winner else (0.5 if variant["name"] == "baseline_mark_temporal" else 0.6)
            cached.append({"variant": variant["name"], "feature_profile": variant["feature_profile"],
                           "target": variant["target"], "credit_weighted": variant["credit_weighted"],
                           "validation_year": year, "plan_gpa_mae": mae,
                           "plan_gpa_rmse": mae, "plan_gpa_bias": mae,
                           "course_points_mae": mae, "best_iteration": 5,
                           "experiment_signature": signature})
    pd.DataFrame(cached).to_parquet(versioned["DEGREE_POINTS_VALIDATION_PATH"], index=False)
    # Matching V1 metadata must never enable reuse of V1 holdout predictions.
    legacy["DEGREE_POINTS_EXPERIMENT_METADATA_PATH"].write_text(json.dumps({
        "feature_engineering_version": 2, "experiment_signature": signature,
        "selected_variant": {"name": winner},
    }), encoding="utf-8")
    before = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in legacy.items()}
    input_before = {name: path.read_bytes() for name, path in versioned.items() if name in INPUTS}
    fits = []

    def synthetic_train(parameters, dataset, num_boost_round, **kwargs):
        fits.append((parameters["num_leaves"], num_boost_round))
        return SyntheticModel()

    monkeypatch.setattr(lgb, "train", synthetic_train)
    reads = []
    original_parquet = pd.read_parquet
    original_text = Path.read_text

    def record_parquet(path, *args, **kwargs):
        reads.append(Path(path))
        assert Path(path) not in legacy.values(), f"Experiment read V1: {path}"
        return original_parquet(path, *args, **kwargs)

    def record_text(path, *args, **kwargs):
        reads.append(path)
        assert path not in legacy.values(), f"Experiment read V1: {path}"
        return original_text(path, *args, **kwargs)

    monkeypatch.setattr(pd, "read_parquet", record_parquet)
    monkeypatch.setattr(Path, "read_text", record_text)
    return legacy, versioned, before, input_before, scale, reads, fits


def assert_preserved(legacy, versioned, before, input_before):
    assert {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in legacy.items()} == before
    assert {name: versioned[name].read_bytes() for name in INPUTS} == input_before


def test_coordinator_uses_v2_baseline_cache_outputs_and_metadata_candidate(isolated_io):
    legacy, versioned, before, input_before, scale, reads, fits = isolated_io
    experiment.main()
    assert all(versioned[name].is_file() for name in OUTPUTS)
    assert all(versioned[name] in reads for name in INPUTS)
    assert scale in reads
    assert fits == [(17, 5)]  # All 20 validation rows were reused from V2 cache.
    assert_preserved(legacy, versioned, before, input_before)
    metadata = json.loads(versioned["DEGREE_POINTS_EXPERIMENT_METADATA_PATH"].read_text())
    assert metadata["dataset_version"] == "V2"
    assert metadata["selected_variant"]["name"] == "degree_history_points_temporal"
    assert metadata["holdout_2025"]["baseline"] == {"mae": 1}
    assert metadata["holdout_2025"]["selected"]["plan_gpa_mae"] == 0.5
    assert metadata["history_protocol"]["test_history_cutoffs"] == {"20251": 20243, "20252": 20251}
    assert metadata["sources"] == {
        "baseline_model_metadata": INPUTS["MODEL_METADATA_PATH"],
        "train_features": INPUTS["TEMPORAL_TRAIN_FEATURES_PATH"],
        "test_features": INPUTS["TEMPORAL_TEST_FEATURES_PATH"],
        "baseline_plan_gpa_metrics": INPUTS["PLAN_GPA_METRICS_PATH"],
        "baseline_plan_gpa_evaluation": INPUTS["PLAN_GPA_EVALUATION_PATH"],
        "grade_scale": "data/raw/v_acs_grade.parquet",
    }
    assert metadata["artifacts"] == {
        "model": OUTPUTS["DEGREE_POINTS_SELECTED_MODEL_PATH"],
        "category_levels": OUTPUTS["DEGREE_POINTS_CATEGORY_LEVELS_PATH"],
    }
    by_degree = pd.read_parquet(versioned["DEGREE_POINTS_HOLDOUT_BY_DEGREE_PATH"])
    assert by_degree.loc[0, "baseline_plan_gpa_mae"] == 1
    experiment.main()
    assert fits == [(17, 5)]  # V2 holdout reuse does not retrain.
    assert_preserved(legacy, versioned, before, input_before)


@pytest.mark.parametrize("missing_input", INPUTS)
def test_missing_v2_input_fails_without_using_v1(isolated_io, monkeypatch, missing_input):
    legacy, versioned, before, input_before, scale, reads, fits = isolated_io
    missing = versioned[missing_input].with_name("missing_" + versioned[missing_input].name)
    monkeypatch.setattr(experiment, missing_input + "_V2", missing, raising=False)
    with pytest.raises(FileNotFoundError, match=missing.name):
        experiment.main()
    assert_preserved(legacy, versioned, before, input_before)
    assert not fits


def test_path_constants_are_v2_and_grade_scale_is_shared():
    for name, relative in {**INPUTS, **OUTPUTS}.items():
        assert getattr(paths, name + "_V2", None) == paths.PROJECT_ROOT / relative
    assert experiment.GRADE_SCALE_PATH == paths.PROJECT_ROOT / "data/raw/v_acs_grade.parquet"
    assert experiment_io.GRADE_SCALE_PATH == experiment.GRADE_SCALE_PATH
    assert not hasattr(paths, "GRADE_SCALE_PATH_V2")
