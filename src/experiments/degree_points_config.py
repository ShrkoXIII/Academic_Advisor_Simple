"""Configuration for the degree/points experiment."""

from src.features.feature_contract import BASE_FEATURES


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
            *BASE_FEATURES,
        ]
    )
)
