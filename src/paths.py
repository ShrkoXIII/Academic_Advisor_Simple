from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
MERGED_DIR = DATA_DIR / "merged"
TEMPORAL_DIR = DATA_DIR / "temporal"
FEATURE_DIR = DATA_DIR / "features"
ARTIFACT_DIR = DATA_DIR / "artifacts"
EVALUATION_DIR = DATA_DIR / "evaluation"
MODEL_DIR = PROJECT_ROOT / "models"


STUDENT_COURSE_PATH = RAW_DIR / "v_crg_student_course_raw.parquet"
STUDENT_STATUS_PATH = RAW_DIR / "v_add_student_degree_status.parquet"
DEGREE_COURSE_PATH = RAW_DIR / "v_acd_degree_course.parquet"
ACADEMIC_INFO_PATH = RAW_DIR / "v_add_academic_info.parquet"
GRADE_SCALE_PATH = RAW_DIR / "v_acs_grade.parquet"

COURSE_REQUEST_PATH = RAW_DIR / "v_crg_std_cor_temp_request.parquet"
COURSE_OFFER_PATH = RAW_DIR / "v_sch_course_offers.parquet"
COURSE_PREREQUISITE_PATH = RAW_DIR / "v_cor_course_prerequisite.parquet"


CLEAN_STUDENT_COURSE_PATH = CLEAN_DIR / "student_course.parquet"
CLEAN_STUDENT_STATUS_PATH = CLEAN_DIR / "student_status.parquet"
CLEAN_DEGREE_COURSE_PATH = CLEAN_DIR / "degree_course.parquet"
STUDENT_COURSE_ENRICHED_PATH = CLEAN_DIR / "student_course_enriched.parquet"
CLEAN_STUDENT_DIPLOMA_PATH = CLEAN_DIR / "student_diploma.parquet"
STUDENT_COURSE_DIPLOMA_PATH = (
    MERGED_DIR / "student_course_enriched_with_diploma.parquet"
)
STUDENT_COURSE_WITHOUT_OUTLIERS_PATH = (
    MERGED_DIR / "student_course_enriched_without_outliers.parquet"
)
OUTLIER_STUDENTS_AUDIT_PATH = MERGED_DIR / "outlier_students.parquet"
TEMPORAL_TRAIN_PATH = TEMPORAL_DIR / "temporal_train.parquet"
TEMPORAL_TEST_PATH = TEMPORAL_DIR / "temporal_test.parquet"
CLEAN_REGISTRATION_ROSTER_PATH = CLEAN_DIR / "registration_roster.parquet"
TEMPORAL_TRAIN_ROSTER_PATH = TEMPORAL_DIR / "temporal_train_roster.parquet"
TEMPORAL_TEST_ROSTER_PATH = TEMPORAL_DIR / "temporal_test_roster.parquet"
TEMPORAL_TRAIN_FEATURES_PATH = FEATURE_DIR / "temporal_train_features.parquet"
TEMPORAL_TEST_FEATURES_PATH = FEATURE_DIR / "temporal_test_features.parquet"
COURSE_HISTORY_STATE_PATH = ARTIFACT_DIR / "course_history_state.pkl"
CATEGORY_LEVELS_PATH = ARTIFACT_DIR / "category_levels.json"
GRADE_MODEL_PATH = MODEL_DIR / "grade_regressor.txt"
FAIL_MODEL_PATH = MODEL_DIR / "fail_risk_classifier.txt"
MODEL_METADATA_PATH = MODEL_DIR / "model_metadata.json"
PLAN_GPA_COURSE_PREDICTIONS_PATH = (
    EVALUATION_DIR / "plan_gpa_course_predictions_2025.parquet"
)
PLAN_GPA_EVALUATION_PATH = EVALUATION_DIR / "plan_gpa_evaluation_2025.parquet"
PLAN_GPA_METRICS_PATH = EVALUATION_DIR / "plan_gpa_metrics_2025.json"
ERROR_ANALYSIS_DIR = EVALUATION_DIR / "error_analysis"
MODEL_ERROR_BY_YEAR_PATH = ERROR_ANALYSIS_DIR / "model_error_by_year.parquet"
MODEL_ERROR_BY_DEGREE_PATH = ERROR_ANALYSIS_DIR / "model_error_by_degree.parquet"
MODEL_ERROR_BY_YEAR_DEGREE_PATH = (
    ERROR_ANALYSIS_DIR / "model_error_by_year_and_degree.parquet"
)
MODEL_ERROR_PLAN_SEGMENTS_PATH = ERROR_ANALYSIS_DIR / "plan_error_segments.parquet"
MODEL_ERROR_COURSE_SEGMENTS_PATH = ERROR_ANALYSIS_DIR / "course_error_segments.parquet"
MODEL_SHAP_IMPORTANCE_PATH = ERROR_ANALYSIS_DIR / "grade_model_shap_importance.parquet"
MODEL_SHAP_FAMILY_PATH = ERROR_ANALYSIS_DIR / "grade_model_shap_families.parquet"
MODEL_ERROR_ANALYSIS_SUMMARY_PATH = ERROR_ANALYSIS_DIR / "analysis_summary.json"
REPORT_DIR = PROJECT_ROOT / "reports"
MODEL_ERROR_REPORT_PATH = REPORT_DIR / "model_error_analysis.md"

DEGREE_POINTS_EXPERIMENT_DIR = EVALUATION_DIR / "experiments" / "degree_points"
DEGREE_POINTS_VALIDATION_PATH = (
    DEGREE_POINTS_EXPERIMENT_DIR / "validation_results.parquet"
)
DEGREE_POINTS_VALIDATION_SUMMARY_PATH = (
    DEGREE_POINTS_EXPERIMENT_DIR / "validation_summary.parquet"
)
DEGREE_POINTS_HOLDOUT_COURSES_PATH = (
    DEGREE_POINTS_EXPERIMENT_DIR / "selected_holdout_course_predictions.parquet"
)
DEGREE_POINTS_HOLDOUT_PLANS_PATH = (
    DEGREE_POINTS_EXPERIMENT_DIR / "selected_holdout_plan_predictions.parquet"
)
DEGREE_POINTS_HOLDOUT_BY_DEGREE_PATH = (
    DEGREE_POINTS_EXPERIMENT_DIR / "selected_holdout_by_degree.parquet"
)
DEGREE_POINTS_EXPERIMENT_METADATA_PATH = (
    DEGREE_POINTS_EXPERIMENT_DIR / "experiment_metadata.json"
)
DEGREE_POINTS_MODEL_DIR = MODEL_DIR / "experiments" / "degree_points"
DEGREE_POINTS_SELECTED_MODEL_PATH = DEGREE_POINTS_MODEL_DIR / "selected_model.txt"
DEGREE_POINTS_CATEGORY_LEVELS_PATH = (
    DEGREE_POINTS_MODEL_DIR / "selected_category_levels.json"
)
DEGREE_POINTS_EXPERIMENT_REPORT_PATH = REPORT_DIR / "degree_points_experiment.md"
MODEL_IMPROVEMENT_TABLE_REPORT_PATH = REPORT_DIR / "model_improvement_table.md"
