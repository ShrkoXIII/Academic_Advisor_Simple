"""Cache and persistence contracts for the degree/points experiment."""

import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path

import pandas as pd
import numpy as np


def test_signature_hashes_current_dependencies_deterministically(tmp_path, monkeypatch):
    from src.experiments import experiment_io

    root = tmp_path
    paths = {
        "TEMPORAL_TRAIN_FEATURES_PATH": root / "train.parquet",
        "TEMPORAL_TEST_FEATURES_PATH": root / "test.parquet",
        "MODEL_METADATA_PATH": root / "model_metadata.json",
        "GRADE_SCALE_PATH": root / "grade_scale.parquet",
    }
    for name, path in paths.items():
        path.write_bytes(name.encode())
        monkeypatch.setattr(experiment_io, name, path)
    monkeypatch.setattr(experiment_io, "PROJECT_ROOT", root)
    code_paths = [
        root / "src" / "experiments" / "a.py",
        root / "src" / "experiments" / "b.py",
        root / "src" / "features" / "feature_contract.py",
        root / "src" / "modeling" / "train_models.py",
        root / "src" / "modeling" / "training_config.py",
    ]
    for path in code_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(path.name.encode())

    ordered = [*paths.values(), *code_paths]
    expected = hashlib.sha256(b"".join(path.read_bytes() for path in ordered)).hexdigest()
    assert experiment_io.experiment_signature() == expected
    assert experiment_io.experiment_signature() == expected
    assert len(expected) == 64

    feature_contract = root / "src" / "features" / "feature_contract.py"
    feature_contract.write_bytes(b"changed contract")
    assert experiment_io.experiment_signature() != expected


def test_validation_cache_reuses_only_matching_signature(tmp_path, monkeypatch):
    from src.experiments import experiment_io

    path = tmp_path / "validation.parquet"
    monkeypatch.setattr(experiment_io, "DEGREE_POINTS_VALIDATION_PATH", path)
    assert experiment_io.load_cached_validation("current") == ([], set())

    pd.DataFrame({"variant": ["old"], "validation_year": [2023]}).to_parquet(path)
    assert experiment_io.load_cached_validation("current") == ([], set())

    pd.DataFrame({
        "variant": ["old", "new"],
        "validation_year": [2023, 2024],
        "experiment_signature": ["previous", "current"],
        "baseline_plan_gpa_mae": [0.5, 0.4],
        "plan_gpa_mae_delta_vs_baseline": [0.1, -0.1],
    }).to_parquet(path)
    rows, completed = experiment_io.load_cached_validation("current")
    assert rows == [{
        "variant": "new",
        "validation_year": 2024,
        "experiment_signature": "current",
    }]
    assert completed == {("new", 2024)}
    assert experiment_io.load_cached_validation("missing") == ([], set())


def test_metadata_retains_protocol_and_artifact_contract():
    from src.experiments.degree_points_config import VARIANTS
    from src.experiments.experiment_io import build_metadata
    from src.features.feature_contract import FEATURE_ENGINEERING_VERSION
    from src.paths import PROJECT_ROOT, DEGREE_POINTS_SELECTED_MODEL_PATH, DEGREE_POINTS_CATEGORY_LEVELS_PATH

    selected = VARIANTS[-1]
    summary = pd.DataFrame([{"variant": selected["name"], "mean_plan_gpa_mae": 0.4}])
    metadata = build_metadata(
        selected, 17, summary, {"plan_gpa_mae": 0.4}, {"mae": 0.5}, "signature"
    )
    assert metadata["feature_engineering_version"] == FEATURE_ENGINEERING_VERSION
    assert metadata["experiment_signature"] == "signature"
    assert datetime.fromisoformat(metadata["created_at_utc"])
    assert "both 2023 and 2024" in metadata["selection_protocol"]
    assert metadata["history_protocol"] == {
        "training": "strictly prior academic parts",
        "holdout_2025": "frozen after 2024",
        "pre_2022_weight": 0.25,
        "from_2022_weight": 1.0,
        "smoothing_k": 20.0,
    }
    assert metadata["selected_variant"] == selected
    assert metadata["selected_boost_rounds"] == 17
    assert metadata["variant_catalog"] == VARIANTS
    assert metadata["feature_contract"]["profile"] == selected["feature_profile"]
    assert metadata["feature_contract"]["model_features"] == [
        *metadata["feature_contract"]["numeric_features"],
        *metadata["feature_contract"]["categorical_features"],
    ]
    assert metadata["validation_summary"] == summary.to_dict(orient="records")
    assert metadata["holdout_2025"] == {
        "selected": {"plan_gpa_mae": 0.4},
        "baseline": {"mae": 0.5},
        "mae_delta": -0.09999999999999998,
        "mae_relative_change": -0.19999999999999996,
    }
    assert metadata["artifacts"] == {
        "model": DEGREE_POINTS_SELECTED_MODEL_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "category_levels": DEGREE_POINTS_CATEGORY_LEVELS_PATH.relative_to(PROJECT_ROOT).as_posix(),
    }
    json.dumps(metadata)


def test_save_results_preserves_parquet_and_json_outputs(tmp_path, monkeypatch):
    from src.experiments import experiment_io

    outputs = {
        "DEGREE_POINTS_VALIDATION_PATH": tmp_path / "results" / "validation_results.parquet",
        "DEGREE_POINTS_VALIDATION_SUMMARY_PATH": tmp_path / "results" / "validation_summary.parquet",
        "DEGREE_POINTS_HOLDOUT_COURSES_PATH": tmp_path / "results" / "holdout_courses.parquet",
        "DEGREE_POINTS_HOLDOUT_PLANS_PATH": tmp_path / "results" / "holdout_plans.parquet",
        "DEGREE_POINTS_HOLDOUT_BY_DEGREE_PATH": tmp_path / "results" / "holdout_by_degree.parquet",
        "DEGREE_POINTS_EXPERIMENT_METADATA_PATH": tmp_path / "results" / "experiment_metadata.json",
    }
    for name, path in outputs.items():
        monkeypatch.setattr(experiment_io, name, path)
    frames = [pd.DataFrame({"value": [number]}) for number in range(5)]
    experiment_io.save_results(*frames, {"rounds": np.int64(17)})

    for path, expected in zip(list(outputs.values())[:5], frames):
        pd.testing.assert_frame_equal(pd.read_parquet(path), expected)
    assert json.loads(outputs["DEGREE_POINTS_EXPERIMENT_METADATA_PATH"].read_text(
        encoding="utf-8"
    )) == {"rounds": 17}


def test_base_modeling_package_has_no_experiment_imports():
    root = Path(__file__).resolve().parents[1] / "src" / "modeling"
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(not alias.name.startswith("src.experiments") for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("src.experiments")
                assert not (
                    node.level >= 2 and (node.module or "").split(".")[0] == "experiments"
                )
