import json
from dataclasses import dataclass
from pathlib import Path

try:
    from .paths import (
        CATEGORY_LEVELS_PATH,
        COURSE_HISTORY_STATE_PATH_V2,
        DEGREE_POINTS_EXPERIMENT_METADATA_PATH,
        DEGREE_POINTS_EXPERIMENT_REPORT_PATH,
        DEGREE_POINTS_HOLDOUT_PLANS_PATH,
        DEGREE_POINTS_SELECTED_MODEL_PATH,
        DEGREE_POINTS_VALIDATION_SUMMARY_PATH,
        FAIL_MODEL_PATH,
        GRADE_MODEL_PATH,
        MODEL_METADATA_PATH,
        MODEL_ERROR_ANALYSIS_SUMMARY_PATH,
        MODEL_ERROR_BY_DEGREE_PATH,
        MODEL_ERROR_BY_YEAR_DEGREE_PATH,
        MODEL_ERROR_BY_YEAR_PATH,
        MODEL_ERROR_REPORT_PATH,
        MODEL_IMPROVEMENT_TABLE_REPORT_PATH,
        MODEL_SHAP_IMPORTANCE_PATH,
        OUTLIER_STUDENTS_AUDIT_PATH_V2,
        PLAN_GPA_COURSE_PREDICTIONS_PATH,
        PLAN_GPA_EVALUATION_PATH,
        PLAN_GPA_METRICS_PATH,
        PROJECT_ROOT,
        STUDENT_COURSE_WITHOUT_OUTLIERS_PATH_V2,
        TEMPORAL_TEST_FEATURES_PATH_V2,
        TEMPORAL_TEST_PATH_V2,
        TEMPORAL_TEST_ROSTER_PATH_V2,
        TEMPORAL_TRAIN_FEATURES_PATH_V2,
        TEMPORAL_TRAIN_PATH_V2,
        TEMPORAL_TRAIN_ROSTER_PATH_V2,
    )
except ImportError:
    from paths import (
        CATEGORY_LEVELS_PATH,
        COURSE_HISTORY_STATE_PATH_V2,
        DEGREE_POINTS_EXPERIMENT_METADATA_PATH,
        DEGREE_POINTS_EXPERIMENT_REPORT_PATH,
        DEGREE_POINTS_HOLDOUT_PLANS_PATH,
        DEGREE_POINTS_SELECTED_MODEL_PATH,
        DEGREE_POINTS_VALIDATION_SUMMARY_PATH,
        FAIL_MODEL_PATH,
        GRADE_MODEL_PATH,
        MODEL_METADATA_PATH,
        MODEL_ERROR_ANALYSIS_SUMMARY_PATH,
        MODEL_ERROR_BY_DEGREE_PATH,
        MODEL_ERROR_BY_YEAR_DEGREE_PATH,
        MODEL_ERROR_BY_YEAR_PATH,
        MODEL_ERROR_REPORT_PATH,
        MODEL_IMPROVEMENT_TABLE_REPORT_PATH,
        MODEL_SHAP_IMPORTANCE_PATH,
        OUTLIER_STUDENTS_AUDIT_PATH_V2,
        PLAN_GPA_COURSE_PREDICTIONS_PATH,
        PLAN_GPA_EVALUATION_PATH,
        PLAN_GPA_METRICS_PATH,
        PROJECT_ROOT,
        STUDENT_COURSE_WITHOUT_OUTLIERS_PATH_V2,
        TEMPORAL_TEST_FEATURES_PATH_V2,
        TEMPORAL_TEST_PATH_V2,
        TEMPORAL_TEST_ROSTER_PATH_V2,
        TEMPORAL_TRAIN_FEATURES_PATH_V2,
        TEMPORAL_TRAIN_PATH_V2,
        TEMPORAL_TRAIN_ROSTER_PATH_V2,
    )


@dataclass(frozen=True)
class ProjectStage:
    number: int
    name: str
    artifacts: tuple[Path, ...]

    @property
    def complete(self):
        return all(path.exists() for path in self.artifacts)


STAGES = [
    ProjectStage(
        1,
        "Clean and merge data (V2)",
        (
            STUDENT_COURSE_WITHOUT_OUTLIERS_PATH_V2,
            OUTLIER_STUDENTS_AUDIT_PATH_V2,
        ),
    ),
    ProjectStage(
        2,
        "Temporal split (V2)",
        (TEMPORAL_TRAIN_PATH_V2, TEMPORAL_TEST_PATH_V2),
    ),
    ProjectStage(
        3,
        "Full registration roster (V2)",
        (TEMPORAL_TRAIN_ROSTER_PATH_V2, TEMPORAL_TEST_ROSTER_PATH_V2),
    ),
    ProjectStage(
        4,
        "Temporal feature engineering (V2)",
        (
            TEMPORAL_TRAIN_FEATURES_PATH_V2,
            TEMPORAL_TEST_FEATURES_PATH_V2,
            COURSE_HISTORY_STATE_PATH_V2,
        ),
    ),
    ProjectStage(
        5,
        "LightGBM model training (V1)",
        (GRADE_MODEL_PATH, FAIL_MODEL_PATH, MODEL_METADATA_PATH, CATEGORY_LEVELS_PATH),
    ),
    ProjectStage(
        6,
        "Observed-plan GPA evaluation (V1)",
        (
            PLAN_GPA_COURSE_PREDICTIONS_PATH,
            PLAN_GPA_EVALUATION_PATH,
            PLAN_GPA_METRICS_PATH,
        ),
    ),
    ProjectStage(
        7,
        "Error analysis by year, degree, and SHAP (V1)",
        (
            MODEL_ERROR_BY_YEAR_PATH,
            MODEL_ERROR_BY_DEGREE_PATH,
            MODEL_ERROR_BY_YEAR_DEGREE_PATH,
            MODEL_SHAP_IMPORTANCE_PATH,
            MODEL_ERROR_ANALYSIS_SUMMARY_PATH,
            MODEL_ERROR_REPORT_PATH,
        ),
    ),
    ProjectStage(
        8,
        "Degree and direct-points experiments (V1)",
        (
            DEGREE_POINTS_VALIDATION_SUMMARY_PATH,
            DEGREE_POINTS_HOLDOUT_PLANS_PATH,
            DEGREE_POINTS_EXPERIMENT_METADATA_PATH,
            DEGREE_POINTS_SELECTED_MODEL_PATH,
            DEGREE_POINTS_EXPERIMENT_REPORT_PATH,
            MODEL_IMPROVEMENT_TABLE_REPORT_PATH,
        ),
    ),
    ProjectStage(
        9,
        "Plan recommendation engine (V1)",
        (
            PROJECT_ROOT / "src" / "recommendation" / "engine.py",
            PROJECT_ROOT / "src" / "grade_scale.py",
        ),
    ),
]

NEXT_MILESTONES = [
    "Complete historical recommendation-policy backtesting",
    "Academic-expert review",
    "API and user-interface integration",
    "Production monitoring and retraining policy",
]


def relative(path):
    return path.relative_to(PROJECT_ROOT)


def print_model_metrics():
    if not MODEL_METADATA_PATH.exists():
        return
    metadata = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
    grade = metadata["grade_regressor"]["test_2025_metrics"]
    fail = metadata["fail_risk_classifier"]["test_2025_metrics"]
    print("\n2025 holdout metrics")
    print(
        "  GradeRegressor: "
        f"MAE={grade['mae']:.3f}, RMSE={grade['rmse']:.3f}, "
        f"within_10={grade['within_10']:.2%}"
    )
    print(
        "  FailRiskClassifier: "
        f"PR-AUC={fail['pr_auc']:.3f}, ROC-AUC={fail['roc_auc']:.3f}, "
        f"Brier={fail['brier']:.4f}, "
        f"ECE={fail['calibration_error_10_bins']:.4f}"
    )
    if PLAN_GPA_METRICS_PATH.exists():
        plan_metrics = json.loads(
            PLAN_GPA_METRICS_PATH.read_text(encoding="utf-8")
        )["overall"]
        print(
            "  Observed-plan GPA: "
            f"MAE={plan_metrics['mae']:.4f}, "
            f"RMSE={plan_metrics['rmse']:.4f}, "
            f"bias={plan_metrics['bias']:+.4f}, "
            f"within_0.50={plan_metrics['within_0_50']:.2%}"
        )
    if DEGREE_POINTS_EXPERIMENT_METADATA_PATH.exists():
        experiment = json.loads(
            DEGREE_POINTS_EXPERIMENT_METADATA_PATH.read_text(encoding="utf-8")
        )
        selected = experiment["holdout_2025"]["selected"]
        baseline = experiment["holdout_2025"]["baseline"]
        print(
            "  Experimental ExpectedPointsRegressor: "
            f"Plan MAE={selected['plan_gpa_mae']:.4f} "
            f"(baseline={baseline['mae']:.4f}, "
            f"change={experiment['holdout_2025']['mae_relative_change']:.2%})"
        )


def main():
    print("Academic Advisor - project build status\n")
    print("Start here: START_HERE.md")
    print("Full pipeline: PIPELINE_README.md\n")
    print(
        "VERSION BOUNDARY: data/features write V2; "
        "modeling/evaluation/experiments/recommendation use V1 artifacts.\n"
    )
    for stage in STAGES:
        status = "DONE" if stage.complete else "PENDING"
        print(f"[{status:7}] {stage.number}. {stage.name}")
        for artifact in stage.artifacts:
            marker = "+" if artifact.exists() else "-"
            print(f"          {marker} {relative(artifact)}")

    print_model_metrics()
    print("\nNext milestones")
    for milestone in NEXT_MILESTONES:
        print(f"  [ ] {milestone}")
    print("\nDetailed checklist: PROJECT_TRACKER.md")


if __name__ == "__main__":
    main()
