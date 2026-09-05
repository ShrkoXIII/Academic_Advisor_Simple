import json

import pandas as pd


TARGET_GRADE = "final_mark"
TARGET_FAIL = "is_fail"

CATEGORY_MISSING = "__MISSING__"
CATEGORY_UNKNOWN = "__UNKNOWN__"

CATEGORICAL_FEATURES = [
    "plan_course_type_id",
    "plan_requirement_type_id",
    "diploma_type_id",
    "grade_version_id",
    "part_semester",
]

NUMERIC_FEATURES = [
    # Student history available before the target semester.
    "gpa_prev_1", # drop
    "gpa_prev_2", # drop
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
    # Pre-university and course/plan properties.
    "diploma_gpa",
    "course_credits",
    "attempt_number",
    "plan_year_order",# drop
    "plan_semester_order",# drop
    "plan_credits_count",
    "degree_credits_count",
    # Course difficulty learned strictly from earlier semesters.
    "course_history_avg_mark",
    "course_history_fail_rate",
    "course_history_avg_attempt",
    "course_history_retake_rate",
    "course_history_effective_support",
    "course_history_fallback_level",
    "course_history_missing",
    # Full-plan context and target-course leave-one-out peer context.
    "plan_course_count",
    "plan_total_credits",
    "plan_credit_weighted_fail_rate",
    "plan_credit_weighted_avg_mark",
    "plan_credit_weighted_avg_attempt",
    "plan_difficulty_credit_load",
    "peer_course_count",
    "peer_total_credits",
    "peer_credit_weighted_fail_rate",
    "peer_credit_weighted_avg_mark",
    "peer_credit_weighted_avg_attempt",
    "peer_difficulty_credit_load",
    "peer_max_fail_rate",
    "peer_difficulty_missing",
]

MODEL_FEATURES = [*NUMERIC_FEATURES, *CATEGORICAL_FEATURES]

# Documentation guard: these columns are deliberately outside MODEL_FEATURES.
LEAKAGE_COLUMNS = [
    "final_mark",
    "is_fail",
    "points",
    "grade_id",
    "course_outcome_status",
    "gpa_points",
    "prev_gpa_points",
    "end_agpa_points",
    "end_total_in_courses",
    "end_total_in_credits",
    "semester_pass_courses",
    "semester_pass_credits",
    "semester_fail_courses",
    "semester_fail_credits",
    "total_pass_courses",
    "total_pass_credits",
    "finish_part_id",
    "finish_status",
]

RAW_ID_COLUMNS = [
    "student_course_id",
    "student_status_id",
    "student_id",
    "course_id",
    "degree_id",
    "faculty_id",
    "plan_degree_course_id",
]


def learn_category_levels(frame):
    levels = {}
    for column in CATEGORICAL_FEATURES:
        observed = (
            frame[column]
            .astype("string")
            .fillna(CATEGORY_MISSING)
            .drop_duplicates()
            .tolist()
        )
        observed = sorted(
            value
            for value in observed
            if value not in {CATEGORY_MISSING, CATEGORY_UNKNOWN}
        )
        levels[column] = [CATEGORY_MISSING, CATEGORY_UNKNOWN, *observed]
    return levels


def prepare_model_matrix(frame, category_levels):
    matrix = pd.DataFrame(index=frame.index)
    for column in NUMERIC_FEATURES:
        matrix[column] = pd.to_numeric(frame[column], errors="coerce").astype(
            "float32"
        )

    for column in CATEGORICAL_FEATURES:
        values = frame[column].astype("string").fillna(CATEGORY_MISSING)
        values = values.where(values.isin(category_levels[column]), CATEGORY_UNKNOWN)
        matrix[column] = pd.Categorical(
            values,
            categories=category_levels[column],
        )
    return matrix[MODEL_FEATURES]


def training_weights(frame):
    year = pd.to_numeric(frame["part_id"], errors="coerce").floordiv(10)
    return year.lt(2022).map({True: 0.25, False: 1.0}).astype("float32")


def save_category_levels(category_levels, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(category_levels, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_category_levels(path):
    return json.loads(path.read_text(encoding="utf-8"))
