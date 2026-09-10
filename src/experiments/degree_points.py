from datetime import datetime, timezone
import hashlib
import json

import numpy as np
import pandas as pd

from ..feature_contract import FEATURE_ENGINEERING_VERSION, MODEL_FEATURES, require_current_features
from ..grade_scale import GradeScale
from ..paths import (
    DEGREE_POINTS_CATEGORY_LEVELS_PATH,
    DEGREE_POINTS_EXPERIMENT_METADATA_PATH,
    DEGREE_POINTS_HOLDOUT_BY_DEGREE_PATH,
    DEGREE_POINTS_HOLDOUT_COURSES_PATH,
    DEGREE_POINTS_HOLDOUT_PLANS_PATH,
    DEGREE_POINTS_SELECTED_MODEL_PATH,
    DEGREE_POINTS_VALIDATION_PATH,
    DEGREE_POINTS_VALIDATION_SUMMARY_PATH,
    GRADE_SCALE_PATH,
    MODEL_METADATA_PATH,
    PLAN_GPA_EVALUATION_PATH,
    PLAN_GPA_METRICS_PATH,
    PROJECT_ROOT,
    TEMPORAL_TEST_FEATURES_PATH,
    TEMPORAL_TRAIN_FEATURES_PATH,
)
from .modeling import (
    degree_metrics,
    evaluate_selected_holdout,
    evaluate_variant,
    feature_columns,
    prediction_metrics,
    select_variant,
    validation_summary,
)
from .specialty_history import (
    HISTORY_SMOOTHING_K,
    add_specialty_history_features,
)

        
BASELINE_VARIANT = "baseline_mark_temporal"

FOLDS = [
    {
        "year": 2023,
        "name": "train_through_2022_validate_2023",
        "train_through": 20223,
        "valid_from": 20231,
        "valid_through": 20233,
    },
    {
        "year": 2024,
        "name": "train_through_2023_validate_2024",
        "train_through": 20233,
        "valid_from": 20241,
        "valid_through": 20243,
    },
]

# This is the experiment catalog: feature profile × target × fit weight.
VARIANTS = [
    {
        "name": "baseline_mark_temporal",
        "feature_profile": "baseline",
        "target": "mark",
        "credit_weighted": False,
    },
    {
        "name": "degree_id_mark_temporal",
        "feature_profile": "degree_id",
        "target": "mark",
        "credit_weighted": False,
    },
    {
        "name": "degree_history_mark_temporal",
        "feature_profile": "degree_history",
        "target": "mark",
        "credit_weighted": False,
    },
    {
        "name": "mark_credit_weighted",
        "feature_profile": "baseline",
        "target": "mark",
        "credit_weighted": True,
    },
    {
        "name": "points_temporal",
        "feature_profile": "baseline",
        "target": "points",
        "credit_weighted": False,
    },
    {
        "name": "points_credit_weighted",
        "feature_profile": "baseline",
        "target": "points",
        "credit_weighted": True,
    },
    {
        "name": "degree_history_points_credit_weighted",
        "feature_profile": "degree_history",
        "target": "points",
        "credit_weighted": True,
    },
    {
        "name": "degree_history_points_temporal",
        "feature_profile": "degree_history",
        "target": "points",
        "credit_weighted": False,
    },
    {
        "name": "degree_id_points_credit_weighted",
        "feature_profile": "degree_id",
        "target": "points",
        "credit_weighted": True,
    },
    {
        "name": "degree_id_points_temporal",
        "feature_profile": "degree_id",
        "target": "points",
        "credit_weighted": False,
    },
]

INPUT_COLUMNS = list(
    dict.fromkeys(
        [
            "student_course_id",
            "student_id",
            "degree_id",
            "degree_name_sl_status",
            "part_id",
            "course_id",
            "course_credits",
            "grade_version_id",
            "plan_requirement_type_id",
            "final_mark",
            "points",
            "is_fail",
            *MODEL_FEATURES,
        ]
    )
)


def load_feature_frames():
    train = pd.read_parquet(TEMPORAL_TRAIN_FEATURES_PATH, columns=INPUT_COLUMNS)
    test = pd.read_parquet(TEMPORAL_TEST_FEATURES_PATH, columns=INPUT_COLUMNS)
    require_current_features(train.attrs)
    require_current_features(test.attrs)
    return add_specialty_history_features(train, test)


def experiment_signature():
    """Invalidate cached runs when data, feature code, or baseline changes."""
    digest = hashlib.sha256()
    inputs = [
        TEMPORAL_TRAIN_FEATURES_PATH, TEMPORAL_TEST_FEATURES_PATH,
        MODEL_METADATA_PATH, GRADE_SCALE_PATH,
        *sorted((PROJECT_ROOT / "src" / "experiments").glob("*.py")),
        PROJECT_ROOT / "src" / "feature_contract.py",
        PROJECT_ROOT / "src" / "train_models.py",
    ]
    for path in inputs:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def load_cached_validation(signature):
    if not DEGREE_POINTS_VALIDATION_PATH.exists():
        return [], set()
    previous = pd.read_parquet(DEGREE_POINTS_VALIDATION_PATH).drop(
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


def run_validation(train, candidate, grade_scale, signature):
    rows, completed = load_cached_validation(signature)
    for variant in VARIANTS:
        for fold in FOLDS:
            if (variant["name"], fold["year"]) in completed:
                continue
            fit = train[train["part_id"].le(fold["train_through"])]
            valid = train[
                train["part_id"].between(
                    fold["valid_from"], fold["valid_through"]
                )
            ]
            print(f"Running {variant['name']} on {fold['year']}...", flush=True)
            result = evaluate_variant(
                fit, valid, fold, variant, candidate, grade_scale
            )
            result["experiment_signature"] = signature
            rows.append(result)
            print(
                f"  plan_MAE={result['plan_gpa_mae']:.6f} "
                f"points_MAE={result['course_points_mae']:.6f} "
                f"iteration={result['best_iteration']}",
                flush=True,
            )
    return validation_summary(
        pd.DataFrame(rows), BASELINE_VARIANT, len(FOLDS)
    )


def selected_round_count(summary, selected):
    return int(
        summary.loc[
            summary["variant"].eq(selected["name"]), "best_iteration"
        ].iloc[0]
    )


def load_or_train_holdout(
    train,
    test,
    selected,
    rounds,
    candidate,
    grade_scale,
    signature,
):
    previous_metadata = None
    if DEGREE_POINTS_EXPERIMENT_METADATA_PATH.exists():
        previous_metadata = json.loads(
            DEGREE_POINTS_EXPERIMENT_METADATA_PATH.read_text(encoding="utf-8")
        )
    can_reuse = (
        previous_metadata is not None
        and previous_metadata.get("experiment_signature") == signature
        and previous_metadata.get("feature_engineering_version") == FEATURE_ENGINEERING_VERSION
        and previous_metadata["selected_variant"]["name"] == selected["name"]
        and DEGREE_POINTS_HOLDOUT_COURSES_PATH.exists()
        and DEGREE_POINTS_HOLDOUT_PLANS_PATH.exists()
    )
    if can_reuse:
        predictions = pd.read_parquet(DEGREE_POINTS_HOLDOUT_COURSES_PATH)
        plans = pd.read_parquet(DEGREE_POINTS_HOLDOUT_PLANS_PATH)
        metrics = prediction_metrics(
            test, predictions, plans, selected["target"]
        )
        return predictions, plans, metrics

    _, predictions, plans, metrics = evaluate_selected_holdout(
        train,
        test,
        selected,
        rounds,
        candidate,
        grade_scale,
        DEGREE_POINTS_SELECTED_MODEL_PATH,
        DEGREE_POINTS_CATEGORY_LEVELS_PATH,
    )
    return predictions, plans, metrics


def compare_holdout_by_degree(selected_plans):
    baseline_plans = pd.read_parquet(PLAN_GPA_EVALUATION_PATH)
    baseline_plans["degree_name"] = ""
    selected = degree_metrics(selected_plans, "selected")
    baseline = degree_metrics(baseline_plans, "baseline").drop(
        columns="degree_name"
    )
    result = selected.merge(baseline, on="degree_id", how="left")
    result["plan_gpa_mae_delta"] = (
        result["selected_plan_gpa_mae"] - result["baseline_plan_gpa_mae"]
    )
    return result


def build_metadata(selected, rounds, summary, holdout_metrics, baseline_holdout, signature):
    numeric_features, categorical_features = feature_columns(
        selected["feature_profile"]
    )
    return {
        "feature_engineering_version": FEATURE_ENGINEERING_VERSION,
        "experiment_signature": signature,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_protocol": (
            "Select only variants improving Plan GPA MAE in both 2023 and 2024; "
            "evaluate the selected variant once on the untouched 2025 holdout."
        ),
        "history_protocol": {
            "training": "strictly prior academic parts",
            "holdout_2025": "frozen after 2024",
            "pre_2022_weight": 0.25,
            "from_2022_weight": 1.0,
            "smoothing_k": HISTORY_SMOOTHING_K,
        },
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
            "model": DEGREE_POINTS_SELECTED_MODEL_PATH.relative_to(
                PROJECT_ROOT
            ).as_posix(),
            "category_levels": DEGREE_POINTS_CATEGORY_LEVELS_PATH.relative_to(
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
    DEGREE_POINTS_VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    validation_results.to_parquet(DEGREE_POINTS_VALIDATION_PATH, index=False)
    summary.to_parquet(DEGREE_POINTS_VALIDATION_SUMMARY_PATH, index=False)
    holdout_predictions.to_parquet(DEGREE_POINTS_HOLDOUT_COURSES_PATH, index=False)
    holdout_plans.to_parquet(DEGREE_POINTS_HOLDOUT_PLANS_PATH, index=False)
    by_degree.to_parquet(DEGREE_POINTS_HOLDOUT_BY_DEGREE_PATH, index=False)
    DEGREE_POINTS_EXPERIMENT_METADATA_PATH.write_text(
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
    print("Saved under:", DEGREE_POINTS_VALIDATION_PATH.parent)


def main():
    base_metadata = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
    require_current_features(base_metadata)
    baseline_report = json.loads(PLAN_GPA_METRICS_PATH.read_text(encoding="utf-8"))
    require_current_features(baseline_report)
    candidate = base_metadata["grade_regressor"]["selected_candidate"]["candidate"]
    train, test = load_feature_frames()
    grade_scale = GradeScale.from_parquet(GRADE_SCALE_PATH)
    signature = experiment_signature()

    validation_results, summary = run_validation(train, candidate, grade_scale, signature)
    selected = select_variant(summary, VARIANTS, BASELINE_VARIANT)
    rounds = selected_round_count(summary, selected)
    print(f"Selected on 2023-2024: {selected['name']} ({rounds} rounds)")

    holdout_predictions, holdout_plans, holdout_metrics = load_or_train_holdout(
        train, test, selected, rounds, candidate, grade_scale, signature
    )
    baseline_holdout = baseline_report["overall"]
    by_degree = compare_holdout_by_degree(holdout_plans)
    metadata = build_metadata(
        selected, rounds, summary, holdout_metrics, baseline_holdout, signature
    )
    save_results(
        validation_results,
        summary,
        holdout_predictions,
        holdout_plans,
        by_degree,
        metadata,
    )
    print_summary(summary, selected, holdout_metrics, baseline_holdout, metadata)


if __name__ == "__main__":
    main()
