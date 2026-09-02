from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
MERGED_DIR = DATA_DIR / "merged"


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
