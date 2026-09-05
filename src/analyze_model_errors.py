import json

import numpy as np
import pandas as pd

try:
    from .evaluate_plan_gpa import aggregate_plan_gpa, predict_course_points
    from .feature_contract import (
        MODEL_FEATURES,
        TARGET_GRADE,
        learn_category_levels,
        load_category_levels,
        prepare_model_matrix,
        training_weights,
    )
    from .grade_scale import GradeScale
    from .paths import (
        CATEGORY_LEVELS_PATH,
        GRADE_MODEL_PATH,
        GRADE_SCALE_PATH,
        MODEL_ERROR_ANALYSIS_SUMMARY_PATH,
        MODEL_ERROR_BY_DEGREE_PATH,
        MODEL_ERROR_BY_YEAR_PATH,
        MODEL_ERROR_BY_YEAR_DEGREE_PATH,
        MODEL_ERROR_COURSE_SEGMENTS_PATH,
        MODEL_ERROR_PLAN_SEGMENTS_PATH,
        MODEL_METADATA_PATH,
        MODEL_SHAP_FAMILY_PATH,
        MODEL_SHAP_IMPORTANCE_PATH,
        TEMPORAL_TEST_FEATURES_PATH,
        TEMPORAL_TRAIN_FEATURES_PATH,
    )
    from .train_models import shared_parameters, train_one
except ImportError:
    from evaluate_plan_gpa import aggregate_plan_gpa, predict_course_points
    from feature_contract import (
        MODEL_FEATURES,
        TARGET_GRADE,
        learn_category_levels,
        load_category_levels,
        prepare_model_matrix,
        training_weights,
    )
    from grade_scale import GradeScale
    from paths import (
        CATEGORY_LEVELS_PATH,
        GRADE_MODEL_PATH,
        GRADE_SCALE_PATH,
        MODEL_ERROR_ANALYSIS_SUMMARY_PATH,
        MODEL_ERROR_BY_DEGREE_PATH,
        MODEL_ERROR_BY_YEAR_PATH,
        MODEL_ERROR_BY_YEAR_DEGREE_PATH,
        MODEL_ERROR_COURSE_SEGMENTS_PATH,
        MODEL_ERROR_PLAN_SEGMENTS_PATH,
        MODEL_METADATA_PATH,
        MODEL_SHAP_FAMILY_PATH,
        MODEL_SHAP_IMPORTANCE_PATH,
        TEMPORAL_TEST_FEATURES_PATH,
        TEMPORAL_TRAIN_FEATURES_PATH,
    )
    from train_models import shared_parameters, train_one


EXTRA_ANALYSIS_COLUMNS = [
    "degree_name_sl_status",
    "course_history_missing",
    "gpa_trend_missing",
    "gpa_prev_1",
]

MIN_RELIABLE_DEGREE_PLANS = 100
SHAP_SAMPLE_ROWS = 30_000


def one_way_effect_size(frame, group_column, value_column):
    clean = frame[[group_column, value_column]].dropna()
    values = clean[value_column].to_numpy(dtype="float64")
    grand_mean = float(values.mean())
    grouped = clean.groupby(group_column, sort=False)[value_column]
    counts = grouped.size().to_numpy(dtype="float64")
    means = grouped.mean().to_numpy(dtype="float64")
    ss_between = float(np.sum(counts * np.square(means - grand_mean)))
    ss_total = float(np.sum(np.square(values - grand_mean)))
    ss_within = ss_total - ss_between
    group_count = len(counts)
    residual_df = len(clean) - group_count
    mean_square_within = ss_within / residual_df
    eta_squared = ss_between / ss_total
    omega_squared = max(
        0.0,
        (ss_between - (group_count - 1) * mean_square_within)
        / (ss_total + mean_square_within),
    )
    return {
        "groups": int(group_count),
        "rows": int(len(clean)),
        "eta_squared": eta_squared,
        "omega_squared": omega_squared,
    }


def course_metrics(frame):
    error = frame["predicted_mark"] - frame["actual_mark"]
    absolute_error = error.abs()
    return pd.Series(
        {
            "course_rows": len(frame),
            "mark_mae": absolute_error.mean(),
            "mark_rmse": np.sqrt(np.mean(np.square(error))),
            "mark_bias": error.mean(),
            "mark_within_5": absolute_error.le(5).mean(),
            "mark_within_10": absolute_error.le(10).mean(),
        }
    )


def plan_metrics(frame):
    absolute_error = frame["plan_gpa_absolute_error"]
    previous_available = frame["gpa_prev_1"].notna()
    previous_error = (
        frame.loc[previous_available, "gpa_prev_1"]
        - frame.loc[previous_available, "actual_plan_gpa"]
    ).abs()
    model_same_rows = frame.loc[previous_available, "plan_gpa_absolute_error"]
    return pd.Series(
        {
            "plans": len(frame),
            "plan_gpa_mae": absolute_error.mean(),
            "plan_gpa_rmse": np.sqrt(np.mean(np.square(frame["plan_gpa_error"]))),
            "plan_gpa_bias": frame["plan_gpa_error"].mean(),
            "plan_within_0_25": absolute_error.le(0.25).mean(),
            "plan_within_0_50": absolute_error.le(0.50).mean(),
            "plan_within_1_00": absolute_error.le(1.00).mean(),
            "previous_gpa_coverage": previous_available.mean(),
            "model_mae_on_previous_gpa_rows": model_same_rows.mean(),
            "previous_gpa_baseline_mae": previous_error.mean(),
            "improvement_over_previous_gpa": (
                1 - model_same_rows.mean() / previous_error.mean()
            ),
        }
    )


def selected_fold_iterations(metadata):
    iterations = {}
    for fold in metadata["grade_regressor"]["selected_candidate"]["folds"]:
        if "2023" in fold["fold"]:
            iterations[2023] = fold["best_iteration"]
        if "2024" in fold["fold"]:
            iterations[2024] = fold["best_iteration"]
    return iterations


def fit_historical_grade_model(train, cutoff_part, rounds, candidate):
    fit = train[train["part_id"].le(cutoff_part)]
    category_levels = learn_category_levels(fit)
    parameters = {
        **shared_parameters(candidate),
        "objective": "regression",
        "metric": "l1",
    }
    model = train_one(
        prepare_model_matrix(fit, category_levels),
        pd.to_numeric(fit[TARGET_GRADE]).to_numpy(dtype="float64"),
        training_weights(fit).to_numpy(dtype="float32"),
        parameters,
        num_boost_round=rounds,
    )
    return model, category_levels


def attach_analysis_columns(course_predictions, source):
    for column in EXTRA_ANALYSIS_COLUMNS:
        course_predictions[column] = source[column].to_numpy()
    course_predictions["academic_year"] = (
        pd.to_numeric(source["part_id"]).floordiv(10).to_numpy(dtype="int64")
    )
    return course_predictions


def make_out_of_time_predictions(train, test, metadata, grade_scale, final_model):
    iteration_by_year = selected_fold_iterations(metadata)
    selected_candidate = metadata["grade_regressor"]["selected_candidate"][
        "candidate"
    ]
    predictions = []
    for year, cutoff_part in [(2023, 20223), (2024, 20233)]:
        model, levels = fit_historical_grade_model(
            train,
            cutoff_part,
            iteration_by_year[year],
            selected_candidate,
        )
        evaluation = train[pd.to_numeric(train["part_id"]).floordiv(10).eq(year)]
        predicted = predict_course_points(evaluation, model, levels, grade_scale)
        predictions.append(attach_analysis_columns(predicted, evaluation))
        print(f"Built out-of-time predictions for {year}: {len(predicted)} rows")

    predicted_2025 = predict_course_points(
        test,
        final_model,
        load_category_levels(CATEGORY_LEVELS_PATH),
        grade_scale,
    )
    predictions.append(attach_analysis_columns(predicted_2025, test))
    print(f"Loaded holdout predictions for 2025: {len(predicted_2025)} rows")
    return pd.concat(predictions, ignore_index=True)


def build_plan_frame(course_predictions):
    plans = aggregate_plan_gpa(course_predictions)
    plan_context = course_predictions.drop_duplicates(
        ["student_id", "degree_id", "part_id"]
    )[
        [
            "student_id",
            "degree_id",
            "part_id",
            "degree_name_sl_status",
            "gpa_prev_1",
        ]
    ]
    plans = plans.merge(
        plan_context,
        on=["student_id", "degree_id", "part_id"],
        how="left",
    )
    plans["academic_year"] = (
        pd.to_numeric(plans["part_id"]).floordiv(10).astype("int64")
    )
    return plans


def build_year_analysis(course_predictions, plans):
    course = (
        course_predictions.groupby("academic_year", sort=True)
        .apply(course_metrics, include_groups=False)
        .reset_index()
    )
    plan = (
        plans.groupby("academic_year", sort=True)
        .apply(plan_metrics, include_groups=False)
        .reset_index()
    )
    return course.merge(plan, on="academic_year")


def build_degree_analysis(course_predictions, plans):
    course = (
        course_predictions.groupby("degree_id", sort=False)
        .apply(course_metrics, include_groups=False)
        .reset_index()
    )
    plan = (
        plans.groupby("degree_id", sort=False)
        .apply(plan_metrics, include_groups=False)
        .reset_index()
    )
    names = (
        plans.groupby("degree_id", sort=False)["degree_name_sl_status"]
        .first()
        .rename("degree_name")
        .reset_index()
    )
    result = names.merge(course, on="degree_id").merge(plan, on="degree_id")
    result["enough_support"] = result["plans"].ge(MIN_RELIABLE_DEGREE_PLANS)
    return result.sort_values(
        ["enough_support", "plans"],
        ascending=[False, False],
        kind="stable",
    ).reset_index(drop=True)


def build_year_degree_analysis(course_predictions, plans):
    group_columns = ["academic_year", "degree_id"]
    course = (
        course_predictions.groupby(group_columns, sort=False)
        .apply(course_metrics, include_groups=False)
        .reset_index()
    )
    plan = (
        plans.groupby(group_columns, sort=False)
        .apply(plan_metrics, include_groups=False)
        .reset_index()
    )
    names = (
        plans.groupby(group_columns, sort=False)["degree_name_sl_status"]
        .first()
        .rename("degree_name")
        .reset_index()
    )
    result = names.merge(course, on=group_columns).merge(plan, on=group_columns)
    result["enough_support"] = result["plans"].ge(30)
    return result.sort_values(
        ["academic_year", "plans"],
        ascending=[True, False],
        kind="stable",
    ).reset_index(drop=True)


def segment_metrics(frame, segment, level):
    metrics = plan_metrics(frame)
    metrics["segment"] = segment
    metrics["level"] = str(level)
    return metrics


def build_plan_segments(plans):
    frames = []
    definitions = {
        "actual_plan_gpa": pd.cut(
            plans["actual_plan_gpa"],
            [-0.01, 0.001, 1, 2, 3, 4.01],
            labels=["0", "0-1", "1-2", "2-3", "3-4"],
        ),
        "course_count": pd.cut(
            plans["course_count"],
            [0, 1, 3, 5, 7, np.inf],
            labels=["1", "2-3", "4-5", "6-7", "8+"],
        ),
    }
    for segment, labels in definitions.items():
        work = plans.assign(_segment_level=labels)
        for level, group in work.groupby("_segment_level", observed=True, sort=False):
            frames.append(segment_metrics(group, segment, level))
    return pd.DataFrame(frames)[
        ["segment", "level", *plan_metrics(plans).index.tolist()]
    ]


def build_course_segments(course_predictions):
    frames = []
    mark_band = pd.cut(
        course_predictions["actual_mark"],
        [-0.01, 49, 59, 69, 79, 89, 100],
        labels=["0-49", "50-59", "60-69", "70-79", "80-89", "90-100"],
    )
    definitions = {
        "actual_mark": mark_band,
        "course_history_missing": course_predictions["course_history_missing"],
        "gpa_trend_missing": course_predictions["gpa_trend_missing"],
    }
    for segment, labels in definitions.items():
        work = course_predictions.assign(_segment_level=labels)
        for level, group in work.groupby("_segment_level", observed=True, sort=False):
            metrics = course_metrics(group)
            metrics["segment"] = segment
            metrics["level"] = str(level)
            frames.append(metrics)
    return pd.DataFrame(frames)[
        ["segment", "level", *course_metrics(course_predictions).index.tolist()]
    ]


def feature_family(feature):
    if feature.startswith("course_history_"):
        return "course_history"
    if feature.startswith("peer_") or feature in {
        "plan_course_count",
        "plan_total_credits",
        "plan_credit_weighted_fail_rate",
        "plan_credit_weighted_avg_mark",
        "plan_credit_weighted_avg_attempt",
        "plan_difficulty_credit_load",
    }:
        return "plan_load"
    if feature.startswith("diploma_"):
        return "pre_university"
    if feature in {"grade_version_id", "part_semester"}:
        return "calendar_and_policy"
    if feature in {
        "course_credits",
        "attempt_number",
        "plan_year_order",
        "plan_semester_order",
        "plan_credits_count",
        "degree_credits_count",
        "plan_course_type_id",
        "plan_requirement_type_id",
    }:
        return "course_and_degree_plan"
    return "student_history"


def build_shap_importance(model, test):
    sample = test.sample(
        n=min(SHAP_SAMPLE_ROWS, len(test)),
        random_state=42,
    )
    matrix = prepare_model_matrix(
        sample,
        load_category_levels(CATEGORY_LEVELS_PATH),
    )
    contributions = model.predict(matrix, pred_contrib=True)
    mean_absolute_shap = np.abs(contributions[:, :-1]).mean(axis=0)
    gain = model.feature_importance(importance_type="gain")
    importance = pd.DataFrame(
        {
            "feature": model.feature_name(),
            "mean_absolute_shap_mark": mean_absolute_shap,
            "gain": gain,
        }
    )
    importance["shap_share"] = (
        importance["mean_absolute_shap_mark"]
        / importance["mean_absolute_shap_mark"].sum()
    )
    importance["gain_share"] = importance["gain"] / importance["gain"].sum()
    importance["family"] = importance["feature"].map(feature_family)
    importance = importance.sort_values(
        "mean_absolute_shap_mark",
        ascending=False,
        kind="stable",
    ).reset_index(drop=True)
    families = (
        importance.groupby("family", as_index=False)
        .agg(
            mean_absolute_shap_mark=("mean_absolute_shap_mark", "sum"),
            shap_share=("shap_share", "sum"),
            gain_share=("gain_share", "sum"),
        )
        .sort_values("shap_share", ascending=False)
        .reset_index(drop=True)
    )
    return importance, families


def main():
    import lightgbm as lgb

    metadata = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
    read_columns = list(
        dict.fromkeys(
            [
                "part_id",
                TARGET_GRADE,
                "student_course_id",
                "student_id",
                "degree_id",
                "course_id",
                "course_name_sl",
                "course_credits",
                "grade_version_id",
                "points",
                "gpa_points",
                *MODEL_FEATURES,
                *EXTRA_ANALYSIS_COLUMNS,
            ]
        )
    )
    train = pd.read_parquet(TEMPORAL_TRAIN_FEATURES_PATH, columns=read_columns)
    test = pd.read_parquet(TEMPORAL_TEST_FEATURES_PATH, columns=read_columns)
    final_model = lgb.Booster(model_file=str(GRADE_MODEL_PATH))
    grade_scale = GradeScale.from_parquet(GRADE_SCALE_PATH)

    course_predictions = make_out_of_time_predictions(
        train,
        test,
        metadata,
        grade_scale,
        final_model,
    )
    plans = build_plan_frame(course_predictions)
    by_year = build_year_analysis(course_predictions, plans)
    by_degree = build_degree_analysis(course_predictions, plans)
    by_year_degree = build_year_degree_analysis(course_predictions, plans)
    plan_segments = build_plan_segments(plans)
    course_segments = build_course_segments(course_predictions)
    shap_importance, shap_families = build_shap_importance(final_model, test)

    summary = {
        "prediction_protocol": {
            "2023": "trained through 2022",
            "2024": "trained through 2023",
            "2025": "trained through 2024",
        },
        "minimum_reliable_degree_plans": MIN_RELIABLE_DEGREE_PLANS,
        "factor_effect_sizes": {
            "academic_year_on_plan_absolute_error": one_way_effect_size(
                plans,
                "academic_year",
                "plan_gpa_absolute_error",
            ),
            "degree_on_plan_absolute_error": one_way_effect_size(
                plans,
                "degree_id",
                "plan_gpa_absolute_error",
            ),
            "academic_year_on_plan_signed_error": one_way_effect_size(
                plans,
                "academic_year",
                "plan_gpa_error",
            ),
            "degree_on_plan_signed_error": one_way_effect_size(
                plans,
                "degree_id",
                "plan_gpa_error",
            ),
            "academic_year_on_course_absolute_mark_error": one_way_effect_size(
                course_predictions.assign(
                    absolute_mark_error=(
                        course_predictions["predicted_mark"]
                        - course_predictions["actual_mark"]
                    ).abs()
                ),
                "academic_year",
                "absolute_mark_error",
            ),
            "degree_on_course_absolute_mark_error": one_way_effect_size(
                course_predictions.assign(
                    absolute_mark_error=(
                        course_predictions["predicted_mark"]
                        - course_predictions["actual_mark"]
                    ).abs()
                ),
                "degree_id",
                "absolute_mark_error",
            ),
            "academic_year_on_course_signed_mark_error": one_way_effect_size(
                course_predictions.assign(
                    signed_mark_error=(
                        course_predictions["predicted_mark"]
                        - course_predictions["actual_mark"]
                    )
                ),
                "academic_year",
                "signed_mark_error",
            ),
            "degree_on_course_signed_mark_error": one_way_effect_size(
                course_predictions.assign(
                    signed_mark_error=(
                        course_predictions["predicted_mark"]
                        - course_predictions["actual_mark"]
                    )
                ),
                "degree_id",
                "signed_mark_error",
            ),
        },
        "rows": {
            "course_predictions": int(len(course_predictions)),
            "plans": int(len(plans)),
            "degrees": int(plans["degree_id"].nunique()),
        },
    }

    MODEL_ERROR_BY_YEAR_PATH.parent.mkdir(parents=True, exist_ok=True)
    by_year.to_parquet(MODEL_ERROR_BY_YEAR_PATH, index=False)
    by_degree.to_parquet(MODEL_ERROR_BY_DEGREE_PATH, index=False)
    by_year_degree.to_parquet(MODEL_ERROR_BY_YEAR_DEGREE_PATH, index=False)
    plan_segments.to_parquet(MODEL_ERROR_PLAN_SEGMENTS_PATH, index=False)
    course_segments.to_parquet(MODEL_ERROR_COURSE_SEGMENTS_PATH, index=False)
    shap_importance.to_parquet(MODEL_SHAP_IMPORTANCE_PATH, index=False)
    shap_families.to_parquet(MODEL_SHAP_FAMILY_PATH, index=False)
    MODEL_ERROR_ANALYSIS_SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\nError by academic year")
    print(by_year.to_string(index=False))
    print("\nSHAP feature families")
    print(shap_families.to_string(index=False))
    print("\nTop 15 SHAP features")
    print(shap_importance.head(15).to_string(index=False))
    print("\nFactor effect sizes")
    print(json.dumps(summary["factor_effect_sizes"], indent=2))
    print("\nSaved analysis under:", MODEL_ERROR_BY_YEAR_PATH.parent)


if __name__ == "__main__":
    main()
