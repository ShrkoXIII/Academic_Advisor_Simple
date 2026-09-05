from itertools import combinations

import numpy as np
import pandas as pd

try:
    from .feature_contract import load_category_levels, prepare_model_matrix
    from .grade_scale import GradeScale
    from .paths import (
        CATEGORY_LEVELS_PATH,
        COURSE_HISTORY_STATE_PATH,
        FAIL_MODEL_PATH,
        GRADE_MODEL_PATH,
        GRADE_SCALE_PATH,
    )
    from .temporal_features import (
        COURSE_HISTORY_COLUMNS,
        PLAN_CONTEXT_COLUMNS,
        compute_plan_context_features,
        load_course_history_state,
    )
except ImportError:
    from feature_contract import load_category_levels, prepare_model_matrix
    from grade_scale import GradeScale
    from paths import (
        CATEGORY_LEVELS_PATH,
        COURSE_HISTORY_STATE_PATH,
        FAIL_MODEL_PATH,
        GRADE_MODEL_PATH,
        GRADE_SCALE_PATH,
    )
    from temporal_features import (
        COURSE_HISTORY_COLUMNS,
        PLAN_CONTEXT_COLUMNS,
        compute_plan_context_features,
        load_course_history_state,
    )


STUDENT_SNAPSHOT_COLUMNS = [
    "student_id",
    "degree_id",
    "faculty_id",
    "grade_version_id",
    "gpa_prev_1",
    "gpa_prev_2",
    "gpa_trend_delta",
    "gpa_trend_missing",
    "start_agpa_points",
    "start_total_in_courses",
    "start_total_in_credits",
    "prior_total_reg_courses",
    "prior_total_reg_credits",
    "prior_total_fail_courses",
    "prior_total_fail_credits",
    "prior_fail_credit_ratio",
    "prior_registered_semesters",
    "observed_gap_semesters",
    "diploma_gpa",
    "diploma_type_id",
    "degree_credits_count",
]

CANDIDATE_COURSE_COLUMNS = [
    "course_id",
    "course_credits",
    "attempt_number",
    "plan_course_type_id",
    "plan_requirement_type_id",
    "plan_year_order",
    "plan_semester_order",
    "plan_credits_count",
]


def enumerate_plan_indices(
    candidate_courses,
    min_credits,
    max_credits,
    max_courses,
):
    credits = pd.to_numeric(
        candidate_courses["course_credits"], errors="coerce"
    ).to_numpy(dtype="float64")
    plan_indices = []
    for course_count in range(1, min(max_courses, len(candidate_courses)) + 1):
        for selected in combinations(range(len(candidate_courses)), course_count):
            total_credits = float(credits[list(selected)].sum())
            if min_credits <= total_credits <= max_credits:
                plan_indices.append(selected)
    return plan_indices


def build_plan_rows(candidate_courses, plan_indices, student_snapshot, part_id):
    candidates = candidate_courses.reset_index(drop=True)
    plans = []
    for plan_id, selected in enumerate(plan_indices):
        plan = candidates.iloc[list(selected)].copy()
        plan["plan_id"] = plan_id
        plans.append(plan)
    rows = pd.concat(plans, ignore_index=True)

    for column, value in student_snapshot.items():
        if column in rows.columns:
            rows[column] = rows[column].fillna(value)
        else:
            rows[column] = value
    rows["part_id"] = int(part_id)
    rows["part_semester"] = int(part_id) % 10
    return rows


def summarize_scored_plans(scored_courses, max_expected_failed_credits):
    work = scored_courses.copy()
    credits = pd.to_numeric(work["course_credits"], errors="coerce")
    work["_quality_points"] = credits * work["predicted_grade_points"]
    work["_expected_failed_credits"] = credits * work["fail_probability"]
    work["_expected_passed_credits"] = credits * (1 - work["fail_probability"])
    work["_mark_credit_sum"] = credits * work["predicted_mark"]
    work["_log_pass_probability"] = np.log1p(
        -work["fail_probability"].clip(0, 1 - 1e-12)
    )

    summaries = (
        work.groupby("plan_id", sort=False)
        .agg(
            plan_course_count=("course_id", "size"),
            plan_total_credits=("course_credits", "sum"),
            expected_quality_points=("_quality_points", "sum"),
            expected_failed_credits=("_expected_failed_credits", "sum"),
            expected_passed_credits=("_expected_passed_credits", "sum"),
            mark_credit_sum=("_mark_credit_sum", "sum"),
            log_pass_probability=("_log_pass_probability", "sum"),
            max_course_fail_probability=("fail_probability", "max"),
            historical_weighted_fail_rate=(
                "plan_credit_weighted_fail_rate",
                "first",
            ),
            historical_weighted_avg_mark=(
                "plan_credit_weighted_avg_mark",
                "first",
            ),
            historical_difficulty_credit_load=(
                "plan_difficulty_credit_load",
                "first",
            ),
        )
        .reset_index()
    )
    summaries["credit_weighted_predicted_mark"] = (
        summaries["mark_credit_sum"] / summaries["plan_total_credits"]
    )
    summaries["plan_any_fail_probability"] = 1 - np.exp(
        summaries["log_pass_probability"]
    )
    summaries = summaries[
        summaries["expected_failed_credits"].le(max_expected_failed_credits)
    ]
    return summaries.sort_values(
        [
            "expected_quality_points",
            "expected_failed_credits",
            "expected_passed_credits",
        ],
        ascending=[False, True, False],
        kind="stable",
    ).reset_index(drop=True)


def _optional_course_name(row):
    for column in ["course_name_sl", "plan_course_name_sl", "course_name"]:
        if column in row.index and pd.notna(row[column]):
            return str(row[column])
    return None


def format_recommendations(summaries, scored_courses, top_n):
    recommendations = []
    for rank, summary in summaries.head(top_n).iterrows():
        plan_rows = scored_courses[
            scored_courses["plan_id"].eq(summary["plan_id"])
        ].sort_values(
            ["fail_probability", "predicted_mark"],
            ascending=[False, True],
            kind="stable",
        )
        hardest = plan_rows.iloc[0]
        courses = []
        for _, course in plan_rows.iterrows():
            courses.append(
                {
                    "course_id": str(course["course_id"]),
                    "course_name": _optional_course_name(course),
                    "course_credits": float(course["course_credits"]),
                    "predicted_mark": round(float(course["predicted_mark"]), 2),
                    "fail_probability": round(float(course["fail_probability"]), 4),
                    "predicted_grade": str(course["predicted_grade"]),
                    "predicted_grade_points": round(
                        float(course["predicted_grade_points"]), 2
                    ),
                    "historical_fail_rate": (
                        None
                        if pd.isna(course["course_history_fail_rate"])
                        else round(float(course["course_history_fail_rate"]), 4)
                    ),
                }
            )

        course_count = int(summary["plan_course_count"])
        total_credits = float(summary["plan_total_credits"])
        historical_fail_rate = summary["historical_weighted_fail_rate"]
        historical_text = (
            "غير متاح"
            if pd.isna(historical_fail_rate)
            else f"{float(historical_fail_rate):.1%}"
        )
        recommendations.append(
            {
                "rank": rank + 1,
                "plan_id": int(summary["plan_id"]),
                "course_count": course_count,
                "total_credits": round(total_credits, 2),
                "expected_quality_points": round(
                    float(summary["expected_quality_points"]), 3
                ),
                "expected_failed_credits": round(
                    float(summary["expected_failed_credits"]), 3
                ),
                "expected_passed_credits": round(
                    float(summary["expected_passed_credits"]), 3
                ),
                "credit_weighted_predicted_mark": round(
                    float(summary["credit_weighted_predicted_mark"]), 2
                ),
                "plan_any_fail_probability": round(
                    float(summary["plan_any_fail_probability"]), 4
                ),
                "max_course_fail_probability": round(
                    float(summary["max_course_fail_probability"]), 4
                ),
                "load_explanation": {
                    "historical_credit_weighted_fail_rate": (
                        None
                        if pd.isna(historical_fail_rate)
                        else round(float(historical_fail_rate), 4)
                    ),
                    "historical_credit_weighted_avg_mark": (
                        None
                        if pd.isna(summary["historical_weighted_avg_mark"])
                        else round(float(summary["historical_weighted_avg_mark"]), 2)
                    ),
                    "historical_difficulty_credit_load": (
                        None
                        if pd.isna(summary["historical_difficulty_credit_load"])
                        else round(
                            float(summary["historical_difficulty_credit_load"]), 3
                        )
                    ),
                    "highest_risk_course_id": str(hardest["course_id"]),
                    "text": (
                        f"الخطة تضم {course_count} مواد بإجمالي "
                        f"{total_credits:g} ساعة؛ معدل الرسوب التاريخي الموزون "
                        f"بالساعات {historical_text}."
                    ),
                },
                "courses": courses,
            }
        )
    return recommendations


class AcademicPlanRecommender:
    def __init__(
        self,
        grade_model,
        fail_model,
        category_levels,
        course_history_state,
        grade_scale,
    ):
        self.grade_model = grade_model
        self.fail_model = fail_model
        self.category_levels = category_levels
        self.course_history_state = course_history_state
        self.grade_scale = grade_scale

    @classmethod
    def load(
        cls,
        grade_model_path=GRADE_MODEL_PATH,
        fail_model_path=FAIL_MODEL_PATH,
        category_levels_path=CATEGORY_LEVELS_PATH,
        course_history_state_path=COURSE_HISTORY_STATE_PATH,
        grade_scale_path=GRADE_SCALE_PATH,
    ):
        import lightgbm as lgb

        return cls(
            grade_model=lgb.Booster(model_file=str(grade_model_path)),
            fail_model=lgb.Booster(model_file=str(fail_model_path)),
            category_levels=load_category_levels(category_levels_path),
            course_history_state=load_course_history_state(course_history_state_path),
            grade_scale=GradeScale.from_parquet(grade_scale_path),
        )

    def recommend(
        self,
        student_snapshot,
        candidate_courses,
        part_id,
        min_credits,
        max_credits,
        max_courses,
        max_expected_failed_credits,
        top_n=5,
    ):
        plan_indices = enumerate_plan_indices(
            candidate_courses,
            min_credits,
            max_credits,
            max_courses,
        )
        if not plan_indices:
            return []

        plan_rows = build_plan_rows(
            candidate_courses,
            plan_indices,
            student_snapshot,
            part_id,
        )
        history = self.course_history_state.apply(plan_rows)
        for column in COURSE_HISTORY_COLUMNS:
            plan_rows[column] = history[column].to_numpy()

        plan_context = compute_plan_context_features(
            plan_rows,
            group_columns=["plan_id"],
        )
        for column in PLAN_CONTEXT_COLUMNS:
            plan_rows[column] = plan_context[column].to_numpy()

        matrix = prepare_model_matrix(plan_rows, self.category_levels)
        plan_rows["predicted_mark"] = np.clip(
            self.grade_model.predict(matrix),
            0,
            100,
        )
        plan_rows["fail_probability"] = np.clip(
            self.fail_model.predict(matrix),
            0,
            1,
        )
        grade_points, grade_labels = self.grade_scale.convert(
            plan_rows["predicted_mark"],
            plan_rows["grade_version_id"],
        )
        plan_rows["predicted_grade_points"] = grade_points
        plan_rows["predicted_grade"] = grade_labels

        summaries = summarize_scored_plans(
            plan_rows,
            max_expected_failed_credits,
        )
        return format_recommendations(summaries, plan_rows, top_n)
