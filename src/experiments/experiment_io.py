"""Cache, metadata, and output for the degree/points experiment."""

from datetime import datetime, timezone
import hashlib
import json

import numpy as np
import pandas as pd

from src.features.feature_contract import FEATURE_ENGINEERING_VERSION
from ..paths import (
    DEGREE_POINTS_CATEGORY_LEVELS_PATH_V2,
    DEGREE_POINTS_EXPERIMENT_METADATA_PATH_V2,
    DEGREE_POINTS_HOLDOUT_BY_DEGREE_PATH_V2,
    DEGREE_POINTS_HOLDOUT_COURSES_PATH_V2,
    DEGREE_POINTS_HOLDOUT_PLANS_PATH_V2,
    DEGREE_POINTS_SELECTED_MODEL_PATH_V2,
    DEGREE_POINTS_VALIDATION_PATH_V2,
    DEGREE_POINTS_VALIDATION_SUMMARY_PATH_V2,
    GRADE_SCALE_PATH,
    MODEL_METADATA_PATH_V2,
    PLAN_GPA_EVALUATION_PATH_V2,
    PLAN_GPA_METRICS_PATH_V2,
    PROJECT_ROOT,
    TEMPORAL_TEST_FEATURES_PATH_V2,
    TEMPORAL_TRAIN_FEATURES_PATH_V2,
)
from .degree_points_config import VARIANTS
from .modeling import feature_columns
from .specialty_history import HISTORY_SMOOTHING_K


def experiment_signature():
    """Invalidate cached runs when data, feature code, or baseline changes."""
    digest = hashlib.sha256()
    inputs = [
        TEMPORAL_TRAIN_FEATURES_PATH_V2, TEMPORAL_TEST_FEATURES_PATH_V2,
        MODEL_METADATA_PATH_V2, GRADE_SCALE_PATH,
        *sorted((PROJECT_ROOT / "src" / "experiments").glob("*.py")),
        PROJECT_ROOT / "src" / "features" / "feature_contract.py",
        PROJECT_ROOT / "src" / "modeling" / "train_models.py",
        PROJECT_ROOT / "src" / "modeling" / "training_config.py",
    ]
    for path in inputs:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def load_cached_validation(signature):
    if not DEGREE_POINTS_VALIDATION_PATH_V2.exists():
        return [], set()
    previous = pd.read_parquet(DEGREE_POINTS_VALIDATION_PATH_V2).drop(
        columns=[
            "baseline_plan_gpa_mae",
            "plan_gpa_mae_delta_vs_baseline",
        ],
        errors="ignore",
    )
    if "experiment_signature" not in previous:
        return [], set()
    previous = previous[previous["experiment_signature"].eq(signature)]
    completed = set(zip(previous["variant"], previous["validation_year"]))
    return previous.to_dict(orient="records"), completed


def build_metadata(
    selected, rounds, summary, holdout_metrics, baseline_holdout, signature,
    *, train_parts=(), test_parts=(),
):
    numeric_features, categorical_features = feature_columns(
        selected["feature_profile"]
    )
    history_protocol = {
        "training": "strictly prior academic parts",
        "holdout_2025": "sequential_roll_forward",
        "pre_2022_weight": 0.25,
        "from_2022_weight": 1.0,
        "smoothing_k": HISTORY_SMOOTHING_K,
    }
    if len(train_parts):
        initial_cutoff = int(pd.to_numeric(pd.Series(train_parts)).max())
        parts = sorted(set(pd.to_numeric(pd.Series(test_parts)).astype(int)))
        history_protocol["initial_history_cutoff"] = initial_cutoff
        history_protocol["test_history_cutoffs"] = {
            str(part): previous for previous, part in zip([initial_cutoff, *parts], parts)
        }
    return {
        "dataset_version": "V2",
        "feature_engineering_version": FEATURE_ENGINEERING_VERSION,
        "sources": {
            "baseline_model_metadata": MODEL_METADATA_PATH_V2.relative_to(PROJECT_ROOT).as_posix(),
            "train_features": TEMPORAL_TRAIN_FEATURES_PATH_V2.relative_to(PROJECT_ROOT).as_posix(),
            "test_features": TEMPORAL_TEST_FEATURES_PATH_V2.relative_to(PROJECT_ROOT).as_posix(),
            "baseline_plan_gpa_metrics": PLAN_GPA_METRICS_PATH_V2.relative_to(PROJECT_ROOT).as_posix(),
            "baseline_plan_gpa_evaluation": PLAN_GPA_EVALUATION_PATH_V2.relative_to(PROJECT_ROOT).as_posix(),
            "grade_scale": GRADE_SCALE_PATH.relative_to(PROJECT_ROOT).as_posix(),
        },
        "experiment_signature": signature,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_protocol": (
            "Select only variants improving Plan GPA MAE in both 2023 and 2024; "
            "evaluate the selected variant once on the untouched 2025 holdout."
        ),
        "history_protocol": history_protocol,
        "selected_variant": selected,
        "selected_boost_rounds": rounds,
        "variant_catalog": VARIANTS,
        "feature_contract": {
            "profile": selected["feature_profile"],
            "numeric_features": numeric_features,
            "categorical_features": categorical_features,
            "model_features": [*numeric_features, *categorical_features],
        },
        "validation_summary": summary.to_dict(orient="records"),
        "holdout_2025": {
            "selected": holdout_metrics,
            "baseline": baseline_holdout,
            "mae_delta": holdout_metrics["plan_gpa_mae"] - baseline_holdout["mae"],
            "mae_relative_change": (
                holdout_metrics["plan_gpa_mae"] / baseline_holdout["mae"] - 1
            ),
        },
        "artifacts": {
            "model": DEGREE_POINTS_SELECTED_MODEL_PATH_V2.relative_to(
                PROJECT_ROOT
            ).as_posix(),
            "category_levels": DEGREE_POINTS_CATEGORY_LEVELS_PATH_V2.relative_to(
                PROJECT_ROOT
            ).as_posix(),
        },
    }


def _json_default(value):
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def save_results(
    validation_results,
    summary,
    holdout_predictions,
    holdout_plans,
    by_degree,
    metadata,
):
    DEGREE_POINTS_VALIDATION_PATH_V2.parent.mkdir(parents=True, exist_ok=True)
    validation_results.to_parquet(DEGREE_POINTS_VALIDATION_PATH_V2, index=False)
    summary.to_parquet(DEGREE_POINTS_VALIDATION_SUMMARY_PATH_V2, index=False)
    holdout_predictions.to_parquet(DEGREE_POINTS_HOLDOUT_COURSES_PATH_V2, index=False)
    holdout_plans.to_parquet(DEGREE_POINTS_HOLDOUT_PLANS_PATH_V2, index=False)
    by_degree.to_parquet(DEGREE_POINTS_HOLDOUT_BY_DEGREE_PATH_V2, index=False)
    DEGREE_POINTS_EXPERIMENT_METADATA_PATH_V2.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )


def print_summary(summary, selected, holdout_metrics, baseline_holdout, metadata):
    print("\nValidation summary")
    print(
        summary[
            [
                "variant",
                "mean_plan_gpa_mae",
                "mean_delta_vs_baseline",
                "improved_folds",
                "best_iteration",
            ]
        ].to_string(index=False)
    )
    print("\n2025 holdout")
    print("Selected variant:", selected["name"])
    print("Selected Plan GPA MAE:", round(holdout_metrics["plan_gpa_mae"], 6))
    print("Baseline Plan GPA MAE:", round(baseline_holdout["mae"], 6))
    print(
        "Relative MAE change:",
        f"{metadata['holdout_2025']['mae_relative_change']:.2%}",
    )
    print("Saved under:", DEGREE_POINTS_VALIDATION_PATH_V2.parent)
