import pandas as pd

from cleaning_utils import (
    clean_column_names,
    clean_id_columns,
    to_float,
    to_integer,
)
from paths import (
    CLEAN_STUDENT_COURSE_PATH,
    CLEAN_STUDENT_STATUS_PATH,
    STUDENT_STATUS_PATH,
)


EXCLUDED_PERMANENT_STATUS_IDS = [1, 4, 11, 12, 15, 16, 41]
STATUS_COURSE_KEYS = ["student_id", "degree_id", "part_id"]

FINAL_COLUMNS = [
    "student_status_id",
    "student_id",
    "part_id",
    "degree_id",
    "start_part_id",
    "finish_part_id",
    "grade_version_id",
    "prev_gpa_points",
    "last_enrolled_gpa",
    "observed_gap_semesters",
    "gpa_points",
    "start_agpa_points",
    "start_total_in_courses",
    "start_total_in_credits",
    "end_total_in_courses",
    "end_total_in_credits",
    "end_agpa_points",
    "semester_reg_courses",
    "semester_reg_credits",
    "semester_pass_courses",
    "semester_pass_credits",
    "semester_fail_courses",
    "semester_fail_credits",
    "total_semesters",
    "total_reg_courses",
    "total_reg_credits",
    "total_pass_courses",
    "total_pass_credits",
    "total_fail_courses",
    "total_fail_credits",
    "reg_total_semesters",
    "finish_status",
    "degree_credits_count",
    "start_level_name_short",
    "end_level_name_short",
]


def add_enrollment_features(df):
    df = df.sort_values(
        ["student_id", "part_id", "student_status_id"],
        kind="stable",
    ).copy()

    registered = df["semester_reg_courses"].gt(0)

    previous_enrolled_gpa = (
        df["gpa_points"]
        .where(registered)
        .groupby(df["student_id"], sort=False)
        .ffill() # Fill missing values with the previous enrolled GPA
        .groupby(df["student_id"], sort=False)
        .shift() # Shift the previous enrolled GPA to not change the current semester's GPA
    )

    first_row = ~df["student_id"].duplicated()
    strong_prior_history = (
        df["reg_total_semesters"].gt(1)
        | df["start_total_in_credits"].gt(0)
        | df["start_total_in_courses"].gt(0)
    )
    use_initial_fallback = (
        first_row
        & df["part_id"].eq(20201)
        & strong_prior_history
        & previous_enrolled_gpa.isna()
    )
    df["last_enrolled_gpa"] = previous_enrolled_gpa.mask(
        use_initial_fallback,
        df["prev_gpa_points"],
    )

    enrollment_blocks = registered.groupby(df["student_id"], sort=False).cumsum()
    gap_streak = (
        (~registered)
        .astype("Int64")
        .groupby([df["student_id"], enrollment_blocks], sort=False)
        .cumsum()
    )
    previous_gap = gap_streak.groupby(df["student_id"], sort=False).shift()
    seen_enrollment_before = (
        registered.groupby(df["student_id"], sort=False)
        .cummax()
        .groupby(df["student_id"], sort=False)
        .shift(fill_value=False)
    )
    df["observed_gap_semesters"] = (
        gap_streak.where(~registered, previous_gap)
        .where(seen_enrollment_before)
        .astype("Int64")
    )

    return df


def clean_student_status(df, course_keys=None):
    df = clean_column_names(df)

    df["permanent_status_id"] = to_integer(df["permanent_status_id"])
    df = df[
        ~df["permanent_status_id"].isin(EXCLUDED_PERMANENT_STATUS_IDS)
    ].copy()

    df["finish_status"] = (
        df["finish_status"].astype("string").str.strip().str.upper()
    )
    df = df[df["finish_status"].ne("WITHDRAWN").fillna(True)].copy()

    df["part_id"] = to_integer(df["part_id"])
    df = df[df["part_id"] > 20193].copy()

    df["study_mode"] = (
        df["study_mode"].astype("string").str.strip().str.upper()
    )
    df = df[df["study_mode"].eq("C")].copy()

    id_columns = [
        "student_status_id",
        "student_id",
        "degree_id",
        "grade_version_id",
    ]
    df = clean_id_columns(df, id_columns)
    df = df[df["degree_id"].notna()].copy()

    if course_keys is not None:
        status_key_index = pd.MultiIndex.from_frame(df[STATUS_COURSE_KEYS])
        course_key_index = pd.MultiIndex.from_frame(course_keys)
        df = df.loc[status_key_index.isin(course_key_index)].copy()

    df["start_part_id"] = to_integer(df["start_part_id"])
    df["finish_part_id"] = to_integer(df["finish_part_id"])

    count_columns = [
        "start_total_in_courses",
        "end_total_in_courses",
        "semester_reg_courses",
        "semester_pass_courses",
        "semester_fail_courses",
        "total_semesters",
        "total_reg_courses",
        "total_pass_courses",
        "total_fail_courses",
        "reg_total_semesters",
    ]
    for column in count_columns:
        df[column] = to_integer(df[column])

    float_columns = [
        "prev_gpa_points",
        "gpa_percent",
        "gpa_points",
        "start_agpa_points",
        "start_total_in_credits",
        "end_total_in_credits",
        "end_agpa_points",
        "semester_reg_credits",
        "semester_pass_credits",
        "semester_fail_credits",
        "total_reg_credits",
        "total_pass_credits",
        "total_fail_credits",
        "degree_credits_count",
    ]
    for column in float_columns:
        df[column] = to_float(df[column])

    for column in ["start_level_name_short", "end_level_name_short"]:
        df[column] = df[column].astype("string").str.strip()

    df = add_enrollment_features(df)
    df = df[FINAL_COLUMNS].copy()
    df = df.sort_values(
        ["student_id", "degree_id", "part_id", "student_status_id"],
        kind="stable",
    ).reset_index(drop=True)

    return df


def main():
    df = pd.read_parquet(STUDENT_STATUS_PATH)
    course_keys = pd.read_parquet(
        CLEAN_STUDENT_COURSE_PATH,
        columns=STATUS_COURSE_KEYS,
    ).drop_duplicates()
    df = clean_student_status(df, course_keys)

    null_report = df.isna().sum().to_frame("null_count")
    null_report["null_percent"] = (
        null_report["null_count"] / len(df) * 100
    ).round(2)
    null_report = null_report.sort_values("null_count", ascending=False)

    print("Rows after the agreed filters:", len(df))
    print("\nNull report:")
    print(null_report.to_string())

    CLEAN_STUDENT_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CLEAN_STUDENT_STATUS_PATH, index=False)
    print("\nSaved:", CLEAN_STUDENT_STATUS_PATH)


if __name__ == "__main__":
    main()
