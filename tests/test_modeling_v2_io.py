"""Exercise Modeling V2 I/O with temporary files and no LightGBM fitting."""

import json
from pathlib import Path
import runpy

import numpy as np
import pandas as pd
import pytest

from src import paths
from src.features.feature_contract import (
    BASE_FEATURES,
    CATEGORICAL_FEATURES,
    FEATURE_ENGINEERING_VERSION,
    NUMERIC_FEATURES,
)
from src.modeling import train_models


IO_PATHS = [
    ("TEMPORAL_TRAIN_FEATURES_PATH", "data/features/temporal_train_features_v2.parquet"),
    ("TEMPORAL_TEST_FEATURES_PATH", "data/features/temporal_test_features_v2.parquet"),
    ("GRADE_MODEL_PATH", "models/grade_regressor_v2.txt"),
    ("FAIL_MODEL_PATH", "models/fail_risk_classifier_v2.txt"),
    ("CATEGORY_LEVELS_PATH", "data/artifacts/category_levels_v2.json"),
    ("MODEL_METADATA_PATH", "models/model_metadata_v2.json"),
]


@pytest.mark.parametrize("name, relative_path", IO_PATHS)
def test_modeling_io_constants_resolve_to_isolated_v2_files(name, relative_path):
    versioned_name = name + "_V2"
    assert hasattr(paths, versioned_name), f"Missing V2 constant: {versioned_name}"
    expected = paths.PROJECT_ROOT / relative_path
    assert getattr(paths, versioned_name) == expected
    assert getattr(train_models, versioned_name, None) == expected
    assert expected != getattr(paths, name)


def feature_rows(parts):
    frame = pd.DataFrame({
        **{column: np.ones(len(parts)) for column in NUMERIC_FEATURES},
        **{column: ["known"] * len(parts) for column in CATEGORICAL_FEATURES},
        "part_id": parts,
        "final_mark": [40, 80] * (len(parts) // 2),
        "is_fail": [1, 0] * (len(parts) // 2),
    })
    frame.attrs["feature_engineering_version"] = FEATURE_ENGINEERING_VERSION
    return frame


@pytest.fixture
def isolated_io(tmp_path, monkeypatch):
    monkeypatch.setattr(train_models, "PROJECT_ROOT", tmp_path)
    legacy, versioned = {}, {}
    for name, relative_path in IO_PATHS:
        old_path = tmp_path / getattr(paths, name).relative_to(paths.PROJECT_ROOT)
        new_path = tmp_path / relative_path
        old_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.write_bytes(b"Preserved V1 artifact")
        legacy[name] = old_path
        versioned[name] = new_path
        # Supply legacy globals to catch any regression to old reads/writes.
        monkeypatch.setattr(train_models, name, old_path, raising=False)
        monkeypatch.setattr(train_models, name + "_V2", new_path, raising=False)

    train = feature_rows([20211, 20221, 20231, 20232, 20241, 20243])
    test = feature_rows([20251, 20252])
    for prefix, frame in [("TRAIN", train), ("TEST", test)]:
        name = f"TEMPORAL_{prefix}_FEATURES_PATH"
        frame.to_parquet(legacy[name], index=False)
        versioned[name].parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(versioned[name], index=False)
    before = {name: path.read_bytes() for name, path in legacy.items()}
    return legacy, versioned, before


class SyntheticModel:
    best_iteration = 3

    def __init__(self, objective):
        self.objective = objective

    def predict(self, matrix, num_iteration=None):
        value = 75.0 if self.objective == "regression" else 0.25
        return np.full(len(matrix), value)

    def save_model(self, filename):
        Path(filename).write_text(f"Synthetic {self.objective} model", encoding="utf-8")

    def feature_name(self):
        return BASE_FEATURES

    def feature_importance(self, importance_type):
        return np.ones(len(BASE_FEATURES))


def test_main_reads_v2_and_writes_only_v2_with_correct_metadata(
    isolated_io, monkeypatch,
):
    legacy, versioned, before = isolated_io

    def synthetic_fit(fit_X, fit_y, fit_weight, parameters, *args, **kwargs):
        return SyntheticModel(parameters["objective"])

    # Keep fold selection, category preparation, metrics, and file I/O real;
    # replace only model fitting, which the task explicitly prohibits running.
    monkeypatch.setattr(train_models, "train_one", synthetic_fit)
    reads = []
    original_read = pd.read_parquet

    def record_read(path, *args, **kwargs):
        reads.append(Path(path))
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(train_models.pd, "read_parquet", record_read)
    train_models.main()

    assert reads == [
        versioned["TEMPORAL_TRAIN_FEATURES_PATH"],
        versioned["TEMPORAL_TEST_FEATURES_PATH"],
    ]
    assert {name: path.read_bytes() for name, path in legacy.items()} == before
    assert versioned["GRADE_MODEL_PATH"].read_text() == "Synthetic regression model"
    assert versioned["FAIL_MODEL_PATH"].read_text() == "Synthetic binary model"
    levels = json.loads(versioned["CATEGORY_LEVELS_PATH"].read_text())
    assert set(levels) == set(CATEGORICAL_FEATURES)
    metadata = json.loads(versioned["MODEL_METADATA_PATH"].read_text())
    assert metadata["artifacts"] == {
        "grade_model": "models/grade_regressor_v2.txt",
        "fail_model": "models/fail_risk_classifier_v2.txt",
        "category_levels": "data/artifacts/category_levels_v2.json",
        "model_metadata": "models/model_metadata_v2.json",
    }
    assert metadata["course_history"] == {
        "training_walk_forward": True,
        "initial_history_cutoff": 20243,
        "test_protocol": "sequential_roll_forward",
        "test_history_cutoffs": {"20251": 20243, "20252": 20251},
        "update_after_finalized_outcomes": True,
        "smoothing_k": 20,
    }


@pytest.mark.parametrize("missing_input", [
    "TEMPORAL_TRAIN_FEATURES_PATH", "TEMPORAL_TEST_FEATURES_PATH",
])
def test_missing_v2_input_fails_without_reading_v1_or_writing_models(
    isolated_io, monkeypatch, missing_input,
):
    legacy, versioned, before = isolated_io
    missing_path = versioned[missing_input].with_name("missing_" + versioned[missing_input].name)
    monkeypatch.setattr(train_models, missing_input + "_V2", missing_path)

    def forbidden_fit(*args, **kwargs):
        raise AssertionError("Missing V2 input reached model fitting")

    monkeypatch.setattr(train_models, "train_one", forbidden_fit)
    with pytest.raises(FileNotFoundError, match=missing_path.name):
        train_models.main()
    assert {name: path.read_bytes() for name, path in legacy.items()} == before
    assert not any(versioned[name].exists() for name in [
        "GRADE_MODEL_PATH", "FAIL_MODEL_PATH", "CATEGORY_LEVELS_PATH", "MODEL_METADATA_PATH",
    ])


def test_direct_script_import_resolves_v2_paths_without_running_training():
    namespace = runpy.run_path(train_models.__file__, run_name="modeling_v2_import_check")
    for name, relative_path in IO_PATHS:
        assert namespace.get(name + "_V2") == paths.PROJECT_ROOT / relative_path
        assert name not in namespace
