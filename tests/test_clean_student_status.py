from pathlib import Path
import sys

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import src.data.clean_student_status as status_module  # noqa: E402


def make_status_row(**overrides):
    row = {
        "student_status_id": "100.0",
        "student_id": "1.111",
        "part_id": 20241,
        "degree_id": "10.111",
        "degree_name_sl": "  Computer Science  ",
        "start_part_id": 20201,
        "finish_part_id": 20252,
        "grade_version_id": "1.0",
        "prev_gpa_points": 2.5,
        "gpa_percent": 75,
        "gpa_points": 3.0,
        "start_agpa_points": 2.5,
        "start_total_in_courses": 8,
        "start_total_in_credits": 24,
        "end_total_in_courses": 12,
        "end_total_in_credits": 36,
        "end_agpa_points": 3.0,
        "semester_reg_courses": 4,
        "semester_reg_credits": 12,
        "semester_pass_courses": 4,
        "semester_pass_credits": 12,
        "semester_fail_courses": 0,
        "semester_fail_credits": 0,
        "total_semesters": 3,
        "total_reg_courses": 8,
        "total_reg_credits": 24,
        "total_pass_courses": 8,
        "total_pass_credits": 24,
        "total_fail_courses": 0,
        "total_fail_credits": 0,
        "reg_total_semesters": 3,
        "finish_status": " active ",
        "degree_credits_count": 132,
        "start_level_name_short": "  Y2 ",
        "end_level_name_short": " Y2  ",
        "permanent_status_id": 2,
        "study_mode": " c ",
    }
    row.update(overrides)
    return row


@pytest.fixture
def enrollment_features():
    frame = pd.DataFrame(
        [
            {
                "student_status_id": "A-3",
                "student_id": "A",
                "part_id": 20232,
                "semester_reg_courses": 4,
                "gpa_points": 3.2,
                "prev_gpa_points": 0.0,
                "total_reg_courses": 4,
                "total_reg_credits": 12,
                "start_total_in_courses": 4,
                "start_total_in_credits": 12,
            },
            {
                "student_status_id": "A-1",
                "student_id": "A",
                "part_id": 20221,
                "semester_reg_courses": 4,
                "gpa_points": 0.0,
                "prev_gpa_points": 0.0,
                "total_reg_courses": 0,
                "total_reg_credits": 0,
                "start_total_in_courses": 0,
                "start_total_in_credits": 0,
            },
            {
                "student_status_id": "A-2",
                "student_id": "A",
                "part_id": 20231,
                "semester_reg_courses": 0,
                "gpa_points": 4.0,
                "prev_gpa_points": 0.0,
                "total_reg_courses": 4,
                "total_reg_credits": 12,
                "start_total_in_courses": 4,
                "start_total_in_credits": 12,
            },
            {
                "student_status_id": "B-1",
                "student_id": "B",
                "part_id": 20201,
                "semester_reg_courses": 3,
                "gpa_points": 3.0,
                "prev_gpa_points": 2.7,
                "total_reg_courses": 5,
                "total_reg_credits": 15,
                "start_total_in_courses": 5,
                "start_total_in_credits": 15,
            },
            {
                "student_status_id": "C-1",
                "student_id": "C",
                "part_id": 20201,
                "semester_reg_courses": 3,
                "gpa_points": 3.0,
                "prev_gpa_points": 2.7,
                "total_reg_courses": 0,
                "total_reg_credits": 0,
                "start_total_in_courses": 0,
                "start_total_in_credits": 0,
            },
        ]
    )
    return status_module.add_enrollment_features(frame)


@pytest.mark.parametrize(
    "student_id, part_id, expected_gpa, expected_gap",
    [
        ("A", 20221, None, None),
        ("A", 20231, 0.0, 2),
        ("A", 20232, 0.0, 2),
        ("B", 20201, 2.7, None),
        ("C", 20201, None, None),
    ],
)
def test_add_enrollment_features_tracks_only_observed_history(
    enrollment_features,
    student_id,
    part_id,
    expected_gpa,
    expected_gap,
):
    row = enrollment_features.loc[
        enrollment_features["student_id"].eq(student_id)
        & enrollment_features["part_id"].eq(part_id)
    ].iloc[0]

    actual_gpa = row["last_enrolled_gpa"]
    actual_gap = row["observed_gap_semesters"]
    assert (
        pd.isna(actual_gpa) if expected_gpa is None else actual_gpa == expected_gpa
    )  # NOTE: a current or non-enrolled GPA must never replace prior enrolled GPA.
    assert (
        pd.isna(actual_gap) if expected_gap is None else actual_gap == expected_gap
    )  # NOTE: gaps are meaningful only after an observed enrollment.


@pytest.mark.parametrize(
    "parts, registered_parts, expected_gaps",
    [
        ([20221, 20222], {20221, 20222}, {20222: 0}),
        ([20221, 20223], {20221, 20223}, {20223: 1}),
        ([20222, 20223, 20231], {20222, 20231}, {20231: 0}),
        ([20221, 20231], {20221, 20231}, {20231: 1}),
        ([20221, 20222, 20223, 20231, 20232], {20221, 20232}, {20232: 2}),
        ([20221, 20222, 20223, 20231], {20221, 20223, 20231}, {20223: 1, 20231: 0}),
    ],
)
def test_observed_gap_counts_regular_semesters_between_enrollments(
    parts, registered_parts, expected_gaps
):
    raw = pd.DataFrame([
        make_status_row(
            student_status_id=str(part),
            part_id=part,
            semester_reg_courses=4 if part in registered_parts else 0,
        )
        for part in reversed(parts)
    ])

    result = status_module.clean_student_status(raw).set_index("part_id")

    for part, expected in expected_gaps.items():
        assert result.loc[part, "observed_gap_semesters"] == expected


def test_optional_non_enrollment_does_not_increase_gap():
    raw = pd.DataFrame([
        make_status_row(student_status_id="1", part_id=20222, semester_reg_courses=4),
        make_status_row(student_status_id="2", part_id=20223, semester_reg_courses=0),
        make_status_row(student_status_id="3", part_id=20231, semester_reg_courses=0),
    ])

    result = status_module.clean_student_status(raw).set_index("part_id")

    assert result.loc[20223, "observed_gap_semesters"] == 0
    assert result.loc[20231, "observed_gap_semesters"] == 1


@pytest.mark.parametrize("invalid_part", [20214, 20224, 20254])
def test_semester_four_is_excluded_before_enrollment_history(invalid_part):
    raw = pd.DataFrame([
        make_status_row(student_status_id="1", part_id=20211, gpa_points=2.1),
        make_status_row(student_status_id="2", part_id=20212, gpa_points=2.2),
        make_status_row(student_status_id="3", part_id=20213, gpa_points=2.3),
        make_status_row(student_status_id="invalid", part_id=invalid_part, gpa_points=0.0),
        make_status_row(student_status_id="4", part_id=20261, gpa_points=3.0),
    ])
    before = raw.copy(deep=True)

    result = status_module.clean_student_status(raw)
    expected = status_module.clean_student_status(raw[raw.student_status_id.ne("invalid")])
    assert result.part_id.tolist() == [20211, 20212, 20213, 20261]
    assert result.iloc[-1].last_enrolled_gpa == 2.3
    assert_frame_equal(result, expected)
    assert_frame_equal(raw, before)


def test_only_semester_four_rows_produce_empty_clean_status():
    raw = pd.DataFrame([make_status_row(part_id=20214)])

    result = status_module.clean_student_status(raw)
    assert result.empty
    assert result.columns.tolist() == status_module.FINAL_COLUMNS


@pytest.mark.parametrize("invalid_part", [20210, 20215])
def test_other_invalid_semesters_remain_strict(invalid_part):
    raw = pd.DataFrame([make_status_row(part_id=invalid_part)])
    with pytest.raises(ValueError, match="part_id"):
        status_module.clean_student_status(raw)


def test_enrolled_optional_semester_updates_last_enrolled_gpa():
    raw = pd.DataFrame([
        make_status_row(student_status_id="1", part_id=20221, gpa_points=2.5),
        make_status_row(student_status_id="2", part_id=20223, gpa_points=2.8),
        make_status_row(student_status_id="3", part_id=20231, gpa_points=3.0),
    ])

    result = status_module.clean_student_status(raw).set_index("part_id")

    assert result.loc[20231, "last_enrolled_gpa"] == 2.8
    assert result.loc[20231, "observed_gap_semesters"] == 0


@pytest.mark.parametrize(
    "excluded_field, excluded_value",
    [
        ("permanent_status_id", 1),
        ("finish_status", " withdrawn "),
        ("study_mode", " E "),
        ("degree_id", " none "),
    ],
)
def test_business_filters_remove_only_the_matching_row(excluded_field, excluded_value):
    raw = pd.DataFrame([
        make_status_row(student_status_id="101", student_id="1.111"),
        make_status_row(student_status_id="102", student_id="2.111", **{excluded_field: excluded_value}),
    ])

    result = status_module.clean_student_status(raw)

    assert result["student_status_id"].tolist() == ["101"]


@pytest.mark.parametrize("permanent_status_id", [1, 4, 11, 12, 15, 16, 41])
def test_every_excluded_permanent_status_id_is_filtered(permanent_status_id):
    raw = pd.DataFrame([
        make_status_row(student_status_id="101", student_id="1.111"),
        make_status_row(student_status_id="102", student_id="2.111", permanent_status_id=permanent_status_id),
    ])

    assert status_module.clean_student_status(raw)["student_status_id"].tolist() == ["101"]


@pytest.mark.parametrize(
    "excluded_field, excluded_value",
    [
        ("permanent_status_id", 1),
        ("finish_status", " withdrawn "),
        ("study_mode", " E "),
        ("degree_id", " none "),
    ],
)
def test_filtered_row_still_supplies_prior_enrollment_history(excluded_field, excluded_value):
    raw = pd.DataFrame([
        make_status_row(student_status_id="101", part_id=20221, gpa_points=2.5),
        make_status_row(student_status_id="102", part_id=20222, gpa_points=2.8, **{excluded_field: excluded_value}),
        make_status_row(student_status_id="103", part_id=20231, gpa_points=3.0),
    ])

    result = status_module.clean_student_status(raw)

    assert result["student_status_id"].tolist() == ["101", "103"]
    assert result.loc[1, "last_enrolled_gpa"] == 2.8
    assert result.loc[1, "observed_gap_semesters"] == 0


def test_clean_student_status_preserves_columns_and_normalizes_ids_and_text():
    raw = pd.DataFrame(
        [
            make_status_row(
                student_status_id="101",
                part_id=20221,
                semester_reg_courses=4,
                gpa_points=2.5,
            ),
            make_status_row(
                student_status_id="102",
                part_id=20231,
                semester_reg_courses=0,
                gpa_points=0,
            ),
            make_status_row(student_status_id="103", part_id=20232),
        ]
    )

    result = status_module.clean_student_status(raw)

    assert result["student_status_id"].tolist() == ["101", "102", "103"]
    assert result.columns.tolist() == status_module.FINAL_COLUMNS  # NOTE: downstream feature code depends on the exact output contract.
    assert result.loc[2, "last_enrolled_gpa"] == 2.5
    assert result.loc[2, "observed_gap_semesters"] == 2
    assert result.loc[0, "degree_name_sl"] == "Computer Science"  # NOTE: display categories must not keep source whitespace.
    assert result.loc[0, "student_id"] == "1.111"
    assert result.loc[0, "grade_version_id"] == "1"


def test_part_id_cutoff_still_excludes_20193():
    raw = pd.DataFrame([
        make_status_row(student_status_id="1", part_id=20193),
        make_status_row(student_status_id="2", part_id=20201),
    ])

    assert status_module.clean_student_status(raw)["part_id"].tolist() == [20201]


def test_main_reads_only_status_and_writes_complete_clean_status(tmp_path, monkeypatch):
    raw = pd.DataFrame([make_status_row()])
    raw_path = tmp_path / "raw_status.parquet"
    output_path = tmp_path / "nested" / "student_status.parquet"
    raw.to_parquet(raw_path, index=False)
    monkeypatch.setattr(status_module, "STUDENT_STATUS_PATH", raw_path)
    monkeypatch.setattr(status_module, "PRE_COMMON_STUDENT_STATUS_PATH_V2", output_path)

    status_module.main()

    expected = status_module.clean_student_status(raw)
    assert output_path.exists()  # NOTE: main must create its destination directory and artifact.
    assert_frame_equal(
        pd.read_parquet(output_path),
        expected,
        check_column_type=False,
    )  # NOTE: compare persisted values/dtypes while ignoring Parquet's non-semantic column-index dtype.
