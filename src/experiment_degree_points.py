from datetime import datetime, timezone
import gc
import json

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

try:
    from .feature_contract import (
        CATEGORY_MISSING,
        CATEGORY_UNKNOWN,
        CATEGORICAL_FEATURES,
        MODEL_FEATURES,
        NUMERIC_FEATURES,
        training_weights,
    )
    from .grade_scale import GradeScale
    from .paths import (
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
    from .train_models import EARLY_STOPPING_ROUNDS, MAX_BOOST_ROUNDS, shared_parameters
except ImportError:
    from feature_contract import (
        CATEGORY_MISSING,
        CATEGORY_UNKNOWN,
        CATEGORICAL_FEATURES,
        MODEL_FEATURES,
        NUMERIC_FEATURES,
        training_weights,
    )
    from grade_scale import GradeScale
    from paths import (
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
    from train_models import EARLY_STOPPING_ROUNDS, MAX_BOOST_ROUNDS, shared_parameters


PLAN_KEY = ["student_id", "degree_id", "part_id"]
HISTORY_SMOOTHING_K = 20.0

SPECIALTY_HISTORY_FEATURES = [
    "degree_history_avg_mark",
    "degree_history_fail_rate",
    "degree_history_avg_points",
    "degree_history_effective_support",
    "degree_history_missing",
    "degree_requirement_history_avg_mark",
    "degree_requirement_history_fail_rate",
    "degree_requirement_history_avg_points",
    "degree_requirement_history_effective_support",
    "degree_requirement_history_missing",
]

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


def _weighted_history_source(frame):
    weight = training_weights(frame).astype("float64")
    return pd.DataFrame(
        {
            "part_id": pd.to_numeric(frame["part_id"]),
            "degree_id": frame["degree_id"],
            "plan_requirement_type_id": frame["plan_requirement_type_id"],
            "history_count": weight,
            "history_mark_sum": weight
            * pd.to_numeric(frame["final_mark"]).astype("float64"),
            "history_fail_sum": weight
            * pd.to_numeric(frame["is_fail"]).astype("float64"),
            "history_points_sum": weight
            * pd.to_numeric(frame["points"]).astype("float64"),
        },
        index=frame.index,
    )


def _prior_aggregates(source, keys, prefix):
    value_columns = [
        "history_count",
        "history_mark_sum",
        "history_fail_sum",
        "history_points_sum",
    ]
    group_columns = [*keys, "part_id"]
    grouped = (
        source.groupby(group_columns, dropna=False, observed=True, as_index=False)[
            value_columns
        ]
        .sum()
        .sort_values(group_columns, kind="stable")
    )
    if keys:
        cumulative = grouped.groupby(
            keys,
            dropna=False,
            observed=True,
        )[value_columns].cumsum()
    else:
        cumulative = grouped[value_columns].cumsum()
    prior = cumulative - grouped[value_columns]
    prior.columns = [f"{prefix}_{column}" for column in value_columns]
    return pd.concat(
        [grouped[group_columns].reset_index(drop=True), prior.reset_index(drop=True)],
        axis=1,
    )


def _total_aggregates(source, keys, prefix):
    value_columns = [
        "history_count",
        "history_mark_sum",
        "history_fail_sum",
        "history_points_sum",
    ]
    if keys:
        totals = source.groupby(
            keys,
            dropna=False,
            observed=True,
            as_index=False,
        )[value_columns].sum()
    else:
        totals = pd.DataFrame([source[value_columns].sum()])
    return totals.rename(
        columns={column: f"{prefix}_{column}" for column in value_columns}
    )


def _merge_training_history(frame, source):
    result = frame.copy()
    result["_experiment_row_order"] = np.arange(len(result))
    specifications = [
        ([], "global"),
        (["degree_id"], "degree"),
        (["degree_id", "plan_requirement_type_id"], "degree_requirement"),
    ]
    for keys, prefix in specifications:
        result = result.merge(
            _prior_aggregates(source, keys, prefix),
            on=[*keys, "part_id"],
            how="left",
            sort=False,
        )
    return (
        result.sort_values("_experiment_row_order", kind="stable")
        .drop(columns="_experiment_row_order")
        .reset_index(drop=True)
    )


def _merge_frozen_test_history(test, source):
    result = test.copy()
    global_totals = _total_aggregates(source, [], "global").iloc[0]
    for column, value in global_totals.items():
        result[column] = value
    result = result.merge(
        _total_aggregates(source, ["degree_id"], "degree"),
        on="degree_id",
        how="left",
        sort=False,
    )
    return result.merge(
        _total_aggregates(
            source,
            ["degree_id", "plan_requirement_type_id"],
            "degree_requirement",
        ),
        on=["degree_id", "plan_requirement_type_id"],
        how="left",
        sort=False,
    )


def _safe_average(numerator, denominator):
    numerator = pd.to_numeric(numerator).to_numpy(dtype="float64")
    denominator = pd.to_numeric(denominator).to_numpy(dtype="float64")
    return np.divide(
        numerator,
        denominator,
        out=np.full(len(denominator), np.nan, dtype="float64"),
        where=denominator > 0,
    )


def _finish_specialty_history(frame):
    result = frame.copy()
    prefixes = ["global", "degree", "degree_requirement"]
    suffixes = [
        "history_count",
        "history_mark_sum",
        "history_fail_sum",
        "history_points_sum",
    ]
    for prefix in prefixes:
        for suffix in suffixes:
            column = f"{prefix}_{suffix}"
            result[column] = pd.to_numeric(result[column]).fillna(0.0)

    global_count = result["global_history_count"].to_numpy(dtype="float64")
    global_mark = _safe_average(
        result["global_history_mark_sum"],
        result["global_history_count"],
    )
    global_fail = _safe_average(
        result["global_history_fail_sum"],
        result["global_history_count"],
    )
    global_points = _safe_average(
        result["global_history_points_sum"],
        result["global_history_count"],
    )

    degree_count = result["degree_history_count"].to_numpy(dtype="float64")
    degree_denominator = degree_count + HISTORY_SMOOTHING_K
    degree_mark = np.where(
        global_count > 0,
        (
            result["degree_history_mark_sum"].to_numpy(dtype="float64")
            + HISTORY_SMOOTHING_K * global_mark
        )
        / degree_denominator,
        np.nan,
    )
    degree_fail = np.where(
        global_count > 0,
        (
            result["degree_history_fail_sum"].to_numpy(dtype="float64")
            + HISTORY_SMOOTHING_K * global_fail
        )
        / degree_denominator,
        np.nan,
    )
    degree_points = np.where(
        global_count > 0,
        (
            result["degree_history_points_sum"].to_numpy(dtype="float64")
            + HISTORY_SMOOTHING_K * global_points
        )
        / degree_denominator,
        np.nan,
    )

    requirement_count = result[
        "degree_requirement_history_count"
    ].to_numpy(dtype="float64")
    requirement_denominator = requirement_count + HISTORY_SMOOTHING_K
    requirement_mark = (
        result["degree_requirement_history_mark_sum"].to_numpy(dtype="float64")
        + HISTORY_SMOOTHING_K * degree_mark
    ) / requirement_denominator
    requirement_fail = (
        result["degree_requirement_history_fail_sum"].to_numpy(dtype="float64")
        + HISTORY_SMOOTHING_K * degree_fail
    ) / requirement_denominator
    requirement_points = (
        result["degree_requirement_history_points_sum"].to_numpy(dtype="float64")
        + HISTORY_SMOOTHING_K * degree_points
    ) / requirement_denominator

    result["degree_history_avg_mark"] = degree_mark
    result["degree_history_fail_rate"] = degree_fail
    result["degree_history_avg_points"] = degree_points
    result["degree_history_effective_support"] = degree_count
    result["degree_history_missing"] = degree_count == 0
    result["degree_requirement_history_avg_mark"] = requirement_mark
    result["degree_requirement_history_fail_rate"] = requirement_fail
    result["degree_requirement_history_avg_points"] = requirement_points
    result["degree_requirement_history_effective_support"] = requirement_count
    result["degree_requirement_history_missing"] = requirement_count == 0

    history_columns = [
        f"{prefix}_{suffix}" for prefix in prefixes for suffix in suffixes
    ]
    return result.drop(columns=history_columns)


def add_specialty_history_features(train, test):
    source = _weighted_history_source(train)
    enriched_train = _finish_specialty_history(
        _merge_training_history(train, source)
    )
    enriched_test = _finish_specialty_history(
        _merge_frozen_test_history(test, source)
    )
    return enriched_train, enriched_test


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
            result["predicted_mark"],
            result["grade_version_id"],
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
        fit,
        valid,
        variant,
        candidate,
    )
    raw_prediction = model.predict(
        valid_matrix,
        num_iteration=model.best_iteration,
    )
    predictions = course_predictions(
        valid,
        raw_prediction,
        variant["target"],
        grade_scale,
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


def validation_summary(results):
    baseline = results[results["variant"].eq("baseline_mark_temporal")][
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
    summary["improved_both_validation_years"] = summary["improved_folds"].eq(
        len(FOLDS)
    )
    return compared, summary.sort_values(
        "mean_plan_gpa_mae",
        ascending=True,
        kind="stable",
    ).reset_index(drop=True)


def select_variant(summary):
    eligible = summary[summary["improved_both_validation_years"]]
    selected_name = (
        eligible.iloc[0]["variant"]
        if not eligible.empty
        else "baseline_mark_temporal"
    )
    return next(variant for variant in VARIANTS if variant["name"] == selected_name)


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


def evaluate_selected_holdout(train, test, variant, rounds, candidate, grade_scale):
    model, levels, test_matrix = fit_experiment_model(
        train,
        None,
        variant,
        candidate,
        num_boost_round=rounds,
    )
    test_matrix = prepare_matrix(
        test,
        *feature_columns(variant["feature_profile"]),
        levels,
    )
    raw_prediction = model.predict(test_matrix)
    predictions = course_predictions(
        test,
        raw_prediction,
        variant["target"],
        grade_scale,
    )
    plans = aggregate_plans(predictions)
    metrics = prediction_metrics(test, predictions, plans, variant["target"])

    DEGREE_POINTS_SELECTED_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(DEGREE_POINTS_SELECTED_MODEL_PATH))
    DEGREE_POINTS_CATEGORY_LEVELS_PATH.write_text(
        json.dumps(levels, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return model, predictions, plans, metrics


def _json_default(value):
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def main():
    metadata = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
    candidate = metadata["grade_regressor"]["selected_candidate"]["candidate"]
    columns = list(
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
    train = pd.read_parquet(TEMPORAL_TRAIN_FEATURES_PATH, columns=columns)
    test = pd.read_parquet(TEMPORAL_TEST_FEATURES_PATH, columns=columns)
    train, test = add_specialty_history_features(train, test)
    grade_scale = GradeScale.from_parquet(GRADE_SCALE_PATH)

    rows = []
    completed = set()
    if DEGREE_POINTS_VALIDATION_PATH.exists():
        previous_results = pd.read_parquet(DEGREE_POINTS_VALIDATION_PATH)
        previous_results = previous_results.drop(
            columns=[
                "baseline_plan_gpa_mae",
                "plan_gpa_mae_delta_vs_baseline",
            ],
            errors="ignore",
        )
        rows = previous_results.to_dict(orient="records")
        completed = set(
            zip(
                previous_results["variant"],
                previous_results["validation_year"],
            )
        )
    for variant in VARIANTS:
        for fold in FOLDS:
            if (variant["name"], fold["year"]) in completed:
                continue
            fit = train[train["part_id"].le(fold["train_through"])]
            valid = train[
                train["part_id"].between(
                    fold["valid_from"],
                    fold["valid_through"],
                )
            ]
            print(f"Running {variant['name']} on {fold['year']}...", flush=True)
            result = evaluate_variant(
                fit,
                valid,
                fold,
                variant,
                candidate,
                grade_scale,
            )
            rows.append(result)
            print(
                f"  plan_MAE={result['plan_gpa_mae']:.6f} "
                f"points_MAE={result['course_points_mae']:.6f} "
                f"iteration={result['best_iteration']}",
                flush=True,
            )

    validation_results, summary = validation_summary(pd.DataFrame(rows))
    selected = select_variant(summary)
    selected_rounds = int(
        summary.loc[
            summary["variant"].eq(selected["name"]),
            "best_iteration",
        ].iloc[0]
    )
    print(
        f"Selected on 2023-2024: {selected['name']} ({selected_rounds} rounds)",
        flush=True,
    )
    previous_metadata = None
    if DEGREE_POINTS_EXPERIMENT_METADATA_PATH.exists():
        previous_metadata = json.loads(
            DEGREE_POINTS_EXPERIMENT_METADATA_PATH.read_text(encoding="utf-8")
        )
    can_reuse_holdout = (
        previous_metadata is not None
        and previous_metadata["selected_variant"]["name"] == selected["name"]
        and DEGREE_POINTS_HOLDOUT_COURSES_PATH.exists()
        and DEGREE_POINTS_HOLDOUT_PLANS_PATH.exists()
    )
    if can_reuse_holdout:
        holdout_predictions = pd.read_parquet(DEGREE_POINTS_HOLDOUT_COURSES_PATH)
        holdout_plans = pd.read_parquet(DEGREE_POINTS_HOLDOUT_PLANS_PATH)
        holdout_metrics = prediction_metrics(
            test,
            holdout_predictions,
            holdout_plans,
            selected["target"],
        )
    else:
        _, holdout_predictions, holdout_plans, holdout_metrics = (
            evaluate_selected_holdout(
                train,
                test,
                selected,
                selected_rounds,
                candidate,
                grade_scale,
            )
        )

    baseline_holdout = json.loads(PLAN_GPA_METRICS_PATH.read_text(encoding="utf-8"))[
        "overall"
    ]
    baseline_plans = pd.read_parquet(PLAN_GPA_EVALUATION_PATH)
    baseline_plans["degree_name"] = ""
    selected_by_degree = degree_metrics(holdout_plans, "selected")
    baseline_by_degree = degree_metrics(baseline_plans, "baseline").drop(
        columns="degree_name"
    )
    by_degree = selected_by_degree.merge(
        baseline_by_degree,
        on="degree_id",
        how="left",
    )
    by_degree["plan_gpa_mae_delta"] = (
        by_degree["selected_plan_gpa_mae"]
        - by_degree["baseline_plan_gpa_mae"]
    )

    experiment_metadata = {
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
        "selected_boost_rounds": selected_rounds,
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

    DEGREE_POINTS_VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    validation_results.to_parquet(DEGREE_POINTS_VALIDATION_PATH, index=False)
    summary.to_parquet(DEGREE_POINTS_VALIDATION_SUMMARY_PATH, index=False)
    holdout_predictions.to_parquet(DEGREE_POINTS_HOLDOUT_COURSES_PATH, index=False)
    holdout_plans.to_parquet(DEGREE_POINTS_HOLDOUT_PLANS_PATH, index=False)
    by_degree.to_parquet(DEGREE_POINTS_HOLDOUT_BY_DEGREE_PATH, index=False)
    DEGREE_POINTS_EXPERIMENT_METADATA_PATH.write_text(
        json.dumps(
            experiment_metadata,
            ensure_ascii=False,
            indent=2,
            default=_json_default,
        ),
        encoding="utf-8",
    )

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
        f"{experiment_metadata['holdout_2025']['mae_relative_change']:.2%}",
    )
    print("Saved under:", DEGREE_POINTS_VALIDATION_PATH.parent)


if __name__ == "__main__":
    main()
