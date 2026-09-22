from pathlib import Path

import pytest

from src import paths


ARTIFACT_NAMES = [
    "CLEAN_STUDENT_COURSE_PATH", "CLEAN_STUDENT_STATUS_PATH",
    "CLEAN_DEGREE_COURSE_PATH", "STUDENT_COURSE_ENRICHED_PATH",
    "CLEAN_STUDENT_DIPLOMA_PATH", "STUDENT_COURSE_DIPLOMA_PATH",
    "STUDENT_COURSE_WITHOUT_OUTLIERS_PATH", "OUTLIER_STUDENTS_AUDIT_PATH",
    "TEMPORAL_TRAIN_PATH", "TEMPORAL_TEST_PATH", "CLEAN_REGISTRATION_ROSTER_PATH",
    "TEMPORAL_TRAIN_ROSTER_PATH", "TEMPORAL_TEST_ROSTER_PATH",
    "TEMPORAL_TRAIN_FEATURES_PATH", "TEMPORAL_TEST_FEATURES_PATH",
    "COURSE_HISTORY_STATE_PATH", "CATEGORY_LEVELS_PATH",
]

PRE_COMMON_NAMES = ["PRE_COMMON_STUDENT_COURSE_PATH", "PRE_COMMON_STUDENT_STATUS_PATH"]


@pytest.mark.parametrize("version, expected", [
    (None, "outlier_students_v2.parquet"),
    ("v3", "outlier_students_v3.parquet"),
])
def test_versioned_path_preserves_parent_and_extension(version, expected):
    original = Path("data/merged/outlier_students.parquet")
    assert hasattr(paths, "versioned_path"), "Missing versioned_path helper"
    result = paths.versioned_path(original) if version is None else paths.versioned_path(original, version)
    assert result == original.parent / expected
    assert result.parent == original.parent
    assert result.suffix == original.suffix
    assert result.stem == Path(expected).stem


@pytest.mark.parametrize("extension", [".json", ".pkl", ".txt", ".parquet"])
def test_versioned_path_supports_artifact_extensions(extension):
    assert hasattr(paths, "versioned_path"), "Missing versioned_path helper"
    assert paths.versioned_path(Path("artifacts") / ("state" + extension)) == Path("artifacts") / ("state_v2" + extension)


@pytest.mark.parametrize("name", ARTIFACT_NAMES + PRE_COMMON_NAMES)
def test_v2_artifacts_are_separate_from_originals(name):
    original = getattr(paths, name)
    assert hasattr(paths, name + "_V2"), "Missing isolated artifact constant"
    v2 = getattr(paths, name + "_V2")
    assert v2 != original
    assert v2.parent == original.parent
    assert v2.name == original.stem + "_v2" + original.suffix
