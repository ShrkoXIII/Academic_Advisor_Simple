import json
from dataclasses import dataclass
from pathlib import Path

try:
    from .paths import (
        CATEGORY_LEVELS_PATH,
        COURSE_HISTORY_STATE_PATH,
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
        OUTLIER_STUDENTS_AUDIT_PATH,
        PLAN_GPA_COURSE_PREDICTIONS_PATH,
        PLAN_GPA_EVALUATION_PATH,
        PLAN_GPA_METRICS_PATH,
        PROJECT_ROOT,
        STUDENT_COURSE_WITHOUT_OUTLIERS_PATH,
        TEMPORAL_TEST_FEATURES_PATH,
        TEMPORAL_TEST_PATH,
        TEMPORAL_TEST_ROSTER_PATH,
        TEMPORAL_TRAIN_FEATURES_PATH,
        TEMPORAL_TRAIN_PATH,
        TEMPORAL_TRAIN_ROSTER_PATH,
    )
except ImportError:
    from paths import (
        CATEGORY_LEVELS_PATH,
        COURSE_HISTORY_STATE_PATH,
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
        OUTLIER_STUDENTS_AUDIT_PATH,
        PLAN_GPA_COURSE_PREDICTIONS_PATH,
        PLAN_GPA_EVALUATION_PATH,
        PLAN_GPA_METRICS_PATH,
        PROJECT_ROOT,
        STUDENT_COURSE_WITHOUT_OUTLIERS_PATH,
        TEMPORAL_TEST_FEATURES_PATH,
        TEMPORAL_TEST_PATH,
        TEMPORAL_TEST_ROSTER_PATH,
        TEMPORAL_TRAIN_FEATURES_PATH,
        TEMPORAL_TRAIN_PATH,
        TEMPORAL_TRAIN_ROSTER_PATH,
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
        "Clean and merge data",
        (
            STUDENT_COURSE_WITHOUT_OUTLIERS_PATH,
            OUTLIER_STUDENTS_AUDIT_PATH,
        ),
    ),
    ProjectStage(
        2,
        "Temporal split",
        (TEMPORAL_TRAIN_PATH, TEMPORAL_TEST_PATH),
    ),
    ProjectStage(
        3,
        "Full registration roster",
        (TEMPORAL_TRAIN_ROSTER_PATH, TEMPORAL_TEST_ROSTER_PATH),
    ),
    ProjectStage(
        4,
        "Temporal feature engineering",
        (
            TEMPORAL_TRAIN_FEATURES_PATH,
            TEMPORAL_TEST_FEATURES_PATH,
            COURSE_HISTORY_STATE_PATH,
            CATEGORY_LEVELS_PATH,
        ),
    ),
    ProjectStage(
        5,
        "LightGBM model training",
        (GRADE_MODEL_PATH, FAIL_MODEL_PATH, MODEL_METADATA_PATH),
    ),
    ProjectStage(
        6,
        "Plan recommendation engine",
        (
            PROJECT_ROOT / "src" / "recommendation.py",
            PROJECT_ROOT / "src" / "grade_scale.py",
        ),
    ),
    ProjectStage(
        7,
        "Observed-plan GPA evaluation",
        (
            PLAN_GPA_COURSE_PREDICTIONS_PATH,
            PLAN_GPA_EVALUATION_PATH,
            PLAN_GPA_METRICS_PATH,
        ),
    ),
    ProjectStage(
        8,
        "Error analysis by year, degree, and SHAP",
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
        9,
        "Degree and direct-points experiments",
        (
            DEGREE_POINTS_VALIDATION_SUMMARY_PATH,
            DEGREE_POINTS_HOLDOUT_PLANS_PATH,
            DEGREE_POINTS_EXPERIMENT_METADATA_PATH,
            DEGREE_POINTS_SELECTED_MODEL_PATH,
            DEGREE_POINTS_EXPERIMENT_REPORT_PATH,
            MODEL_IMPROVEMENT_TABLE_REPORT_PATH,
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
