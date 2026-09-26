import json

import pandas as pd

from src.features.feature_contract import FEATURE_ENGINEERING_VERSION, require_current_features
from ..grade_scale import GradeScale
from ..paths import (
    DEGREE_POINTS_CATEGORY_LEVELS_PATH_V2,
    DEGREE_POINTS_EXPERIMENT_METADATA_PATH_V2,
    DEGREE_POINTS_HOLDOUT_COURSES_PATH_V2,
    DEGREE_POINTS_HOLDOUT_PLANS_PATH_V2,
    DEGREE_POINTS_SELECTED_MODEL_PATH_V2,
    GRADE_SCALE_PATH,
    MODEL_METADATA_PATH_V2,
    PLAN_GPA_EVALUATION_PATH_V2,
    PLAN_GPA_METRICS_PATH_V2,
    TEMPORAL_TEST_FEATURES_PATH_V2,
    TEMPORAL_TRAIN_FEATURES_PATH_V2,
)
from .degree_points_config import BASELINE_VARIANT, FOLDS, INPUT_COLUMNS, VARIANTS
from .experiment_io import (
    build_metadata,
    experiment_signature,
    load_cached_validation,
    print_summary,
    save_results,
)
from .modeling import (
    degree_metrics,
    evaluate_selected_holdout,
    evaluate_variant,
    prediction_metrics,
    select_variant,
    validation_summary,
)
from .specialty_history import add_specialty_history_features


def load_feature_frames():
    train = pd.read_parquet(TEMPORAL_TRAIN_FEATURES_PATH_V2, columns=INPUT_COLUMNS)
    test = pd.read_parquet(TEMPORAL_TEST_FEATURES_PATH_V2, columns=INPUT_COLUMNS)
    require_current_features(train.attrs)
    require_current_features(test.attrs)
    return add_specialty_history_features(train, test)


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
            )#fit_experiment_model()-> model.predict()-> course_predictions()-> aggregate_plans()-> prediction_metrics()
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
    if DEGREE_POINTS_EXPERIMENT_METADATA_PATH_V2.exists():
        previous_metadata = json.loads(
            DEGREE_POINTS_EXPERIMENT_METADATA_PATH_V2.read_text(encoding="utf-8")
        )
    can_reuse = (
        previous_metadata is not None
        and previous_metadata.get("experiment_signature") == signature
        and previous_metadata.get("feature_engineering_version") == FEATURE_ENGINEERING_VERSION
        and previous_metadata["selected_variant"]["name"] == selected["name"]
        and DEGREE_POINTS_HOLDOUT_COURSES_PATH_V2.exists()
        and DEGREE_POINTS_HOLDOUT_PLANS_PATH_V2.exists()
    )
    if can_reuse:
        predictions = pd.read_parquet(DEGREE_POINTS_HOLDOUT_COURSES_PATH_V2)
        plans = pd.read_parquet(DEGREE_POINTS_HOLDOUT_PLANS_PATH_V2)
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
        DEGREE_POINTS_SELECTED_MODEL_PATH_V2,
        DEGREE_POINTS_CATEGORY_LEVELS_PATH_V2,
    )
    return predictions, plans, metrics


def compare_holdout_by_degree(selected_plans):
    baseline_plans = pd.read_parquet(PLAN_GPA_EVALUATION_PATH_V2)
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


def main():
    for path in (
        TEMPORAL_TRAIN_FEATURES_PATH_V2,
        TEMPORAL_TEST_FEATURES_PATH_V2,
        MODEL_METADATA_PATH_V2,
        PLAN_GPA_EVALUATION_PATH_V2,
        PLAN_GPA_METRICS_PATH_V2,
    ):
        if not path.is_file():
            raise FileNotFoundError(f"Required Experiment V2 input missing: {path}")
    base_metadata = json.loads(MODEL_METADATA_PATH_V2.read_text(encoding="utf-8"))
    require_current_features(base_metadata)
    baseline_report = json.loads(PLAN_GPA_METRICS_PATH_V2.read_text(encoding="utf-8"))
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
        selected, rounds, summary, holdout_metrics, baseline_holdout, signature,
        train_parts=train["part_id"], test_parts=test["part_id"],
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
