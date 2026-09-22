"""Rebuild only the explicit data/features V2 files and record safety evidence."""

import hashlib
import importlib
import json
from pathlib import Path

import pandas as pd

from src import paths


REPORT_DIR = paths.PROJECT_ROOT / "reports" / "data_features_v2_20260921" / "common_student_policy"
STAGES = [
    ("src.data.clean_degree_course", ["CLEAN_DEGREE_COURSE_PATH_V2"]),
    ("src.data.clean_student_course", ["PRE_COMMON_STUDENT_COURSE_PATH_V2"]),
    ("src.data.clean_student_status", ["PRE_COMMON_STUDENT_STATUS_PATH_V2"]),
    ("src.data.filter_common_students", ["CLEAN_STUDENT_COURSE_PATH_V2", "CLEAN_STUDENT_STATUS_PATH_V2"]),
    ("src.data.build_student_course_enriched", ["STUDENT_COURSE_ENRICHED_PATH_V2"]),
    ("src.data.clean_student_diploma", ["CLEAN_STUDENT_DIPLOMA_PATH_V2", "STUDENT_COURSE_DIPLOMA_PATH_V2"]),
    ("src.data.clean_outliers", ["STUDENT_COURSE_WITHOUT_OUTLIERS_PATH_V2", "OUTLIER_STUDENTS_AUDIT_PATH_V2"]),
    ("src.data.build_temporal_split", ["TEMPORAL_TRAIN_PATH_V2", "TEMPORAL_TEST_PATH_V2"]),
    ("src.data.build_registration_roster", ["CLEAN_REGISTRATION_ROSTER_PATH_V2", "TEMPORAL_TRAIN_ROSTER_PATH_V2", "TEMPORAL_TEST_ROSTER_PATH_V2"]),
    ("src.features.build_temporal_features", ["TEMPORAL_TRAIN_FEATURES_PATH_V2", "TEMPORAL_TEST_FEATURES_PATH_V2", "COURSE_HISTORY_STATE_PATH_V2"]),
]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def compare(status, course):
    keys = ["student_id", "degree_id", "part_id"]
    status_ids = set(status.student_id.dropna())
    course_ids = set(course.student_id.dropna())
    status_keys = status[keys].drop_duplicates()
    course_keys = course[keys].drop_duplicates()
    key_comparison = status_keys.merge(course_keys, on=keys, how="outer", indicator=True, validate="one_to_one")
    counts = key_comparison._merge.value_counts()
    matched = course.merge(status_keys, on=keys, how="inner", validate="many_to_one")
    matched_ids = set(matched.student_id.dropna())
    return {
        "student_level": {
            "status": len(status_ids), "course": len(course_ids),
            "both": len(status_ids & course_ids),
            "status_only": len(status_ids - course_ids),
            "course_only": len(course_ids - status_ids),
        },
        "key_level": {
            "status": len(status_keys), "course": len(course_keys),
            "both": int(counts.get("both", 0)),
            "status_only": int(counts.get("left_only", 0)),
            "course_only": int(counts.get("right_only", 0)),
        },
        "rows": {"status": len(status), "course": len(course)},
        "inner_merge": {
            "course_rows_before": len(course),
            "course_rows_after": len(matched),
            "dropped_rows": len(course) - len(matched),
            "dropped_percentage": round((len(course) - len(matched)) / len(course) * 100, 4) if len(course) else 0,
            "students_before": len(course_ids),
            "students_after": len(matched_ids),
            "students_completely_lost": len(course_ids - matched_ids),
        },
    }


def main():
    outputs = {getattr(paths, name) for _, names in STAGES for name in names}
    for path in outputs:
        base_name = next(name[:-3] for name, value in vars(paths).items() if name.endswith("_V2") and value == path)
        assert path == paths.versioned_path(getattr(paths, base_name))
        assert path.is_relative_to(paths.DATA_DIR) and not path.is_relative_to(paths.RAW_DIR)
        assert not path.is_relative_to(paths.FROZEN_HISTORY_DIR)
        assert path.stem.endswith("_v2")
    existing_v2 = {p for p in paths.DATA_DIR.rglob("*") if p.is_file() and p.stem.endswith("_v2")}
    unknown = existing_v2 - outputs
    if unknown:
        raise ValueError(f"Unlisted V2 files require review before deletion: {sorted(unknown)}")
    if not paths.CLEAN_STUDENT_COURSE_PATH_V2.is_file() or not paths.CLEAN_STUDENT_STATUS_PATH_V2.is_file():
        raise FileNotFoundError("The current V2 clean tables are needed for the before comparison")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    before = compare(pd.read_parquet(paths.CLEAN_STUDENT_STATUS_PATH_V2), pd.read_parquet(paths.CLEAN_STUDENT_COURSE_PATH_V2))
    protected = sorted(
        [p for p in paths.DATA_DIR.rglob("*") if p.is_file() and p not in outputs]
        + [p for p in paths.MODEL_DIR.rglob("*") if p.is_file()]
    )
    before_hashes = {str(p.relative_to(paths.PROJECT_ROOT)): digest(p) for p in protected}
    (REPORT_DIR / "protected_before_sha256.json").write_text(json.dumps(before_hashes, indent=2), encoding="utf-8")
    targets = sorted(existing_v2)
    (REPORT_DIR / "deleted_v2_targets.json").write_text(
        json.dumps([str(p.relative_to(paths.PROJECT_ROOT)) for p in targets], indent=2), encoding="utf-8"
    )
    print("Explicit V2 deletion targets:")
    for path in targets:
        print(path.relative_to(paths.PROJECT_ROOT))
    for path in targets:
        path.unlink()

    for module_name, names in STAGES:
        print("Running", module_name, flush=True)
        importlib.import_module(module_name).main()
        for name in names:
            path = getattr(paths, name)
            if not path.is_file():
                raise AssertionError(f"Stage did not produce {path}")
    after = compare(pd.read_parquet(paths.CLEAN_STUDENT_STATUS_PATH_V2), pd.read_parquet(paths.CLEAN_STUDENT_COURSE_PATH_V2))
    pre_common = compare(pd.read_parquet(paths.PRE_COMMON_STUDENT_STATUS_PATH_V2), pd.read_parquet(paths.PRE_COMMON_STUDENT_COURSE_PATH_V2))
    if pre_common != before:
        raise AssertionError("Independent cleaners changed the pre-policy baseline; stop before interpreting downstream output")
    if after["student_level"]["status_only"] or after["student_level"]["course_only"]:
        raise AssertionError("Final V2 tables contain students from only one source")
    after_hashes = {str(p.relative_to(paths.PROJECT_ROOT)): digest(p) for p in protected}
    changed = [name for name, value in before_hashes.items() if after_hashes.get(name) != value]
    if changed:
        raise AssertionError(f"Protected files changed: {changed}")
    result = {
        "before": before, "after": after, "pre_common_metrics_match_previous_v2": True,
        "deleted_v2_files": len(targets), "rebuilt_v2_files": len(outputs),
        "protected_files_checked": len(protected), "protected_files_changed": changed,
        "raw_files_checked": sum(name.startswith("data\\raw\\") for name in before_hashes),
        "stages": [module for module, _ in STAGES],
    }
    (REPORT_DIR / "rebuild_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("Rebuild result:", json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
