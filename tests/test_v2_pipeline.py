"""Exercise V2 entrypoints with real temporary Parquet files and V1 sentinels."""
import importlib
from pathlib import Path

import pandas as pd

from src import paths
from src.features.temporal_features import load_course_history_state
from tests.test_clean_degree_course import raw_degree_courses  # noqa: F401
from tests.test_clean_student_course import valid_course_row  # noqa: F401
from tests.test_clean_student_status import make_status_row
from tests.test_v2_paths import ARTIFACT_NAMES


STAGES = [
    "src.data.clean_student_course", "src.data.clean_student_status",
    "src.data.filter_common_students", "src.data.clean_degree_course",
    "src.data.build_student_course_enriched",
    "src.data.clean_student_diploma", "src.data.clean_outliers",
    "src.data.build_temporal_split", "src.data.build_registration_roster",
    "src.features.build_temporal_features",
]


def test_full_v2_chain_uses_only_new_intermediates_and_preserves_v1(
    tmp_path, monkeypatch, valid_course_row, raw_degree_courses,
):
    def local(path):
        return tmp_path / path.relative_to(paths.PROJECT_ROOT)

    # Invalid V1 sentinel content makes any accidental V1 read fail immediately.
    protected = []
    for name in ARTIFACT_NAMES:
        original = local(getattr(paths, name))
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes(b"V1 must remain untouched")
        protected.append(original)

    parts = [20243, 20251, 20253]
    courses = []
    for part in parts:
        row = dict(valid_course_row)
        row.update({"Student Course ID": str(part), "Part ID": part})
        courses.append(row)
    course_only = dict(valid_course_row)
    course_only.update({"Student Course ID": "90002", "Student ID": "S2", "Part ID": 20243})
    courses.append(course_only)
    # Keep status-only history: the first course must see the prior GPA of 2.25.
    status_rows = [
        make_status_row(student_status_id=str(part), student_id="S1", degree_id="D1",
                        part_id=part, gpa_points=2.25 if part == 20242 else 3.0)
        for part in [20242, *parts]
    ]
    status_rows.append(make_status_row(student_status_id="90003", student_id="S3", degree_id="D1", part_id=20243))
    status = pd.DataFrame(status_rows)
    raw = {
        paths.STUDENT_COURSE_PATH: pd.DataFrame(courses),
        paths.STUDENT_STATUS_PATH: status,
        paths.DEGREE_COURSE_PATH: raw_degree_courses,
        paths.ACADEMIC_INFO_PATH: pd.DataFrame({
            "student_id": ["S1"], "diploma_gpa": [3.0], "diploma_type_id": [1],
        }),
    }
    for path, frame in raw.items():
        target = local(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(target, index=False)
    raw_bytes = {local(path): local(path).read_bytes() for path in raw}

    feature_reads = []
    for stage in STAGES:
        module = importlib.import_module(stage)
        for name, value in vars(module).copy().items():
            if isinstance(value, Path) and value.is_relative_to(paths.PROJECT_ROOT):
                monkeypatch.setattr(module, name, local(value))
        if stage == "src.features.build_temporal_features":
            original_read = pd.read_parquet

            def capture_read(path, *args, **kwargs):
                feature_reads.append(Path(path))
                return original_read(path, *args, **kwargs)

            with monkeypatch.context() as patch:
                patch.setattr(pd, "read_parquet", capture_read)
                module.main()
        else:
            module.main()

    for name in ARTIFACT_NAMES:
        # Category levels are produced by training, which is outside this run.
        if name != "CATEGORY_LEVELS_PATH":
            assert local(getattr(paths, name + "_V2")).is_file(), name
    assert local(paths.PRE_COMMON_STUDENT_COURSE_PATH_V2).is_file()
    assert local(paths.PRE_COMMON_STUDENT_STATUS_PATH_V2).is_file()
    assert set(pd.read_parquet(local(paths.PRE_COMMON_STUDENT_COURSE_PATH_V2)).student_id) == {"S1", "S2"}
    assert set(pd.read_parquet(local(paths.PRE_COMMON_STUDENT_STATUS_PATH_V2)).student_id) == {"S1", "S3"}
    assert set(pd.read_parquet(local(paths.CLEAN_STUDENT_COURSE_PATH_V2)).student_id) == {"S1"}
    assert set(pd.read_parquet(local(paths.CLEAN_STUDENT_STATUS_PATH_V2)).student_id) == {"S1"}
    assert local(paths.CLEAN_STUDENT_STATUS_PATH_V2) in feature_reads
    assert local(paths.STUDENT_STATUS_PATH) not in feature_reads
    train = pd.read_parquet(local(paths.TEMPORAL_TRAIN_FEATURES_PATH_V2))
    test = pd.read_parquet(local(paths.TEMPORAL_TEST_FEATURES_PATH_V2))
    assert train.part_id.tolist() == [20243]
    assert test.part_id.tolist() == [20251]
    assert train.gpa_prev_1.tolist() == [2.25]
    assert train.prior_total_reg_courses.tolist() == [8]
    assert train.prior_total_reg_credits.tolist() == [24]
    assert train.prior_total_fail_courses.tolist() == [0]
    assert train.prior_total_fail_credits.tolist() == [0]
    assert load_course_history_state(local(paths.COURSE_HISTORY_STATE_PATH_V2)).as_of_part == 20243
    assert all(path.read_bytes() == b"V1 must remain untouched" for path in protected)
    assert all(path.read_bytes() == content for path, content in raw_bytes.items())
