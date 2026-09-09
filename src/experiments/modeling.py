import gc
import json

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from ..feature_contract import (
    CATEGORY_MISSING,
    CATEGORY_UNKNOWN,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    training_weights,
)
from ..train_models import EARLY_STOPPING_ROUNDS, MAX_BOOST_ROUNDS, shared_parameters
from .specialty_history import SPECIALTY_HISTORY_FEATURES


PLAN_KEY = ["student_id", "degree_id", "part_id"]


def feature_columns(profile):
    numeric = list(NUMERIC_FEATURES)
    categorical = list(CATEGORICAL_FEATURES)
    if profile == "degree_id":
        categorical.append("degree_id")
    if profile == "degree_history":
        numeric.extend(SPECIALTY_HISTORY_FEATURES)
    return numeric, categorical


def learn_levels(frame, categorical_features):
    levels = {}
    for column in categorical_features:
        values = frame[column].astype("string").fillna(CATEGORY_MISSING)
        observed = sorted(
            value
            for value in values.drop_duplicates().tolist()
            if value not in {CATEGORY_MISSING, CATEGORY_UNKNOWN}
        )
        levels[column] = [CATEGORY_MISSING, CATEGORY_UNKNOWN, *observed]
    return levels


def prepare_matrix(frame, numeric_features, categorical_features, levels):
    matrix = pd.DataFrame(
        {
            column: pd.to_numeric(frame[column], errors="coerce").astype("float32")
            for column in numeric_features
        },
        index=frame.index,
    )
    for column in categorical_features:
        values = frame[column].astype("string").fillna(CATEGORY_MISSING)
        values = values.where(values.isin(levels[column]), CATEGORY_UNKNOWN)
        matrix[column] = pd.Categorical(values, categories=levels[column])
    return matrix[[*numeric_features, *categorical_features]]


def fit_weights(frame, credit_weighted):
    weight = training_weights(frame).astype("float64")
    if credit_weighted:
        weight = weight * pd.to_numeric(frame["course_credits"]).astype("float64")
    return weight.to_numpy(dtype="float32")


def fit_experiment_model(
    fit,
    valid,
    variant,
    candidate,
    num_boost_round=MAX_BOOST_ROUNDS,
):
    import lightgbm as lgb

    numeric, categorical = feature_columns(variant["feature_profile"])
    levels = learn_levels(fit, categorical)
    fit_matrix = prepare_matrix(fit, numeric, categorical, levels)
    valid_matrix = None
    if valid is not None:
        valid_matrix = prepare_matrix(valid, numeric, categorical, levels)
    target_column = "final_mark" if variant["target"] == "mark" else "points"
    fit_target = pd.to_numeric(fit[target_column]).to_numpy(dtype="float64")
    parameters = {
        **shared_parameters(candidate),
        "objective": "regression",
        "metric": "l1",
    }
    train_set = lgb.Dataset(
        fit_matrix,
        label=fit_target,
        weight=fit_weights(fit, variant["credit_weighted"]),
        categorical_feature=categorical,
        free_raw_data=False,
    )
    valid_sets = None
    callbacks = [lgb.log_evaluation(period=0)]
    if valid is not None:
        valid_target = pd.to_numeric(valid[target_column]).to_numpy(dtype="float64")
        valid_set = lgb.Dataset(
            valid_matrix,
            label=valid_target,
            reference=train_set,
            categorical_feature=categorical,
            free_raw_data=False,
        )
        valid_sets = [valid_set]
        callbacks.append(
            lgb.early_stopping(
                EARLY_STOPPING_ROUNDS,
                first_metric_only=True,
                verbose=False,
            )
        )
    model = lgb.train(
        parameters,
        train_set,
        num_boost_round=num_boost_round,
        valid_sets=valid_sets,
        callbacks=callbacks,
    )
    return model, levels, valid_matrix


def course_predictions(frame, raw_prediction, target, grade_scale):
    result = frame[
        [
            "student_course_id",
            "student_id",
            "degree_id",
            "degree_name_sl_status",
            "part_id",
            "course_id",
            "course_credits",
            "grade_version_id",
            "final_mark",
            "points",
        ]
    ].copy()
    result = result.rename(
        columns={"final_mark": "actual_mark", "points": "actual_points"}
    )
    if target == "mark":
        result["predicted_mark"] = np.clip(raw_prediction, 0, 100)
        predicted_points, _ = grade_scale.convert(
            result["predicted_mark"], result["grade_version_id"]
        )
        result["predicted_points"] = predicted_points
    else:
        result["predicted_mark"] = np.nan
        result["predicted_points"] = np.clip(raw_prediction, 0, 4)
    result["point_error"] = result["predicted_points"] - result["actual_points"]
    result["actual_quality_points"] = (
        result["course_credits"] * result["actual_points"]
    )
    result["predicted_quality_points"] = (
        result["course_credits"] * result["predicted_points"]
    )
    return result


def aggregate_plans(predictions):
    plans = predictions.groupby(PLAN_KEY, as_index=False, sort=False).agg(
        degree_name=("degree_name_sl_status", "first"),
        course_count=("course_id", "size"),
        total_credits=("course_credits", "sum"),
        actual_quality_points=("actual_quality_points", "sum"),
        predicted_quality_points=("predicted_quality_points", "sum"),
    )
    plans["actual_plan_gpa"] = (
        plans["actual_quality_points"] / plans["total_credits"]
    )
    plans["predicted_plan_gpa"] = (
        plans["predicted_quality_points"] / plans["total_credits"]
    )
    plans["plan_gpa_error"] = (
        plans["predicted_plan_gpa"] - plans["actual_plan_gpa"]
    )
    plans["plan_gpa_absolute_error"] = plans["plan_gpa_error"].abs()
    return plans


def prediction_metrics(frame, predictions, plans, target):
    point_error = predictions["point_error"].to_numpy(dtype="float64")
    plan_error = plans["plan_gpa_error"].to_numpy(dtype="float64")
    metrics = {
        "course_rows": int(len(predictions)),
        "plans": int(len(plans)),
        "course_points_mae": float(np.mean(np.abs(point_error))),
        "course_points_rmse": float(np.sqrt(np.mean(np.square(point_error)))),
        "plan_gpa_mae": float(np.mean(np.abs(plan_error))),
        "plan_gpa_credits_weighted_mae": float(
            np.average(
                np.abs(plan_error),
                weights=plans["total_credits"].to_numpy(dtype="float64"),
            )
        ),
        "plan_gpa_rmse": float(np.sqrt(np.mean(np.square(plan_error)))),
        "plan_gpa_bias": float(np.mean(plan_error)),
        "plan_within_0_25": float(np.mean(np.abs(plan_error) <= 0.25)),
        "plan_within_0_50": float(np.mean(np.abs(plan_error) <= 0.50)),
        "plan_within_1_00": float(np.mean(np.abs(plan_error) <= 1.00)),
    }
    if target == "mark":
        predicted_mark = predictions["predicted_mark"].to_numpy(dtype="float64")
        actual_mark = pd.to_numeric(frame["final_mark"]).to_numpy(dtype="float64")
        metrics["course_mark_mae"] = float(
            mean_absolute_error(actual_mark, predicted_mark)
        )
        metrics["course_mark_rmse"] = float(
            np.sqrt(mean_squared_error(actual_mark, predicted_mark))
        )
    else:
        metrics["course_mark_mae"] = None
        metrics["course_mark_rmse"] = None
    return metrics


def evaluate_variant(fit, valid, fold, variant, candidate, grade_scale):
    model, _, valid_matrix = fit_experiment_model(
        fit, valid, variant, candidate
    )
    raw_prediction = model.predict(
        valid_matrix, num_iteration=model.best_iteration
    )
    predictions = course_predictions(
        valid, raw_prediction, variant["target"], grade_scale
    )
    plans = aggregate_plans(predictions)
    metrics = prediction_metrics(valid, predictions, plans, variant["target"])
    result = {
        "variant": variant["name"],
        "feature_profile": variant["feature_profile"],
        "target": variant["target"],
        "credit_weighted": variant["credit_weighted"],
        "fold": fold["name"],
        "validation_year": fold["year"],
        "fit_rows": int(len(fit)),
        "best_iteration": int(model.best_iteration),
        **metrics,
    }
    del model, valid_matrix, predictions, plans
    gc.collect()
    return result


def validation_summary(results, baseline_name, fold_count):
    baseline = results[results["variant"].eq(baseline_name)][
        ["validation_year", "plan_gpa_mae"]
    ].rename(columns={"plan_gpa_mae": "baseline_plan_gpa_mae"})
    compared = results.merge(baseline, on="validation_year", how="left")
    compared["plan_gpa_mae_delta_vs_baseline"] = (
        compared["plan_gpa_mae"] - compared["baseline_plan_gpa_mae"]
    )
    summary = compared.groupby(
        ["variant", "feature_profile", "target", "credit_weighted"],
        as_index=False,
        sort=False,
    ).agg(
        mean_plan_gpa_mae=("plan_gpa_mae", "mean"),
        mean_plan_gpa_rmse=("plan_gpa_rmse", "mean"),
        mean_plan_gpa_bias=("plan_gpa_bias", "mean"),
        mean_course_points_mae=("course_points_mae", "mean"),
        mean_delta_vs_baseline=("plan_gpa_mae_delta_vs_baseline", "mean"),
        best_iteration=("best_iteration", "mean"),
        improved_folds=(
            "plan_gpa_mae_delta_vs_baseline",
            lambda values: int((values < 0).sum()),
        ),
    )
    summary["best_iteration"] = summary["best_iteration"].round().astype("int64")
    summary["improved_all_validation_years"] = summary["improved_folds"].eq(
        fold_count
    )
    return compared, summary.sort_values(
        "mean_plan_gpa_mae", ascending=True, kind="stable"
    ).reset_index(drop=True)


def select_variant(summary, variants, baseline_name):
    eligible = summary[summary["improved_all_validation_years"]]
    selected_name = eligible.iloc[0]["variant"] if not eligible.empty else baseline_name
    return next(variant for variant in variants if variant["name"] == selected_name)


def degree_metrics(plans, prefix):
    grouped = plans.groupby("degree_id", as_index=False, sort=False).agg(
        degree_name=("degree_name", "first"),
        plans=("plan_gpa_absolute_error", "size"),
        plan_gpa_mae=("plan_gpa_absolute_error", "mean"),
        plan_gpa_bias=("plan_gpa_error", "mean"),
        plan_within_0_50=("plan_gpa_absolute_error", lambda x: x.le(0.50).mean()),
    )
    return grouped.rename(
        columns={
            column: f"{prefix}_{column}"
            for column in grouped.columns
            if column not in {"degree_id", "degree_name"}
        }
    )


def evaluate_selected_holdout(
    train,
    test,
    variant,
    rounds,
    candidate,
    grade_scale,
    model_path,
    category_levels_path,
):
    model, levels, _ = fit_experiment_model(
        train, None, variant, candidate, num_boost_round=rounds
    )
    test_matrix = prepare_matrix(
        test, *feature_columns(variant["feature_profile"]), levels
    )
    raw_prediction = model.predict(test_matrix)
    predictions = course_predictions(
        test, raw_prediction, variant["target"], grade_scale
    )
    plans = aggregate_plans(predictions)
    metrics = prediction_metrics(test, predictions, plans, variant["target"])

    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(model_path))
    category_levels_path.write_text(
        json.dumps(levels, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return model, predictions, plans, metrics
