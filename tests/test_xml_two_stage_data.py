"""Temporal and observed-outcome safeguards for isolated XML experiments."""
import pandas as pd
import pytest

from src.recommendation_experiments.xml_two_stage_data import (
    calculate_observed_metrics, explicit_target, normalize_raw_rows, sorted_xml_files, load_case,
)


def raw_courses():
    return normalize_raw_rows(pd.DataFrame([
        dict(STUDENT_COURSE_ID="1", STUDENT_ID="s", DEGREE_ID="d", PART_ID=20251,
             COURSE_ID="a", COURSE_NAME_SL="A", COURSE_CREDITS=3, POINTS=4,
             REGISTER_STATUS="R", FINISH_STATUS="P", IN_GPA="Y", IN_AGPA="Y", IN_CREDITS="Y"),
        dict(STUDENT_COURSE_ID="2", STUDENT_ID="s", DEGREE_ID="d", PART_ID=20251,
             COURSE_ID="b", COURSE_NAME_SL="B", COURSE_CREDITS=3, POINTS=0,
             REGISTER_STATUS="E", FINISH_STATUS="F", IN_GPA="Y", IN_AGPA="Y", IN_CREDITS="Y"),
        dict(STUDENT_COURSE_ID="3", STUDENT_ID="s", DEGREE_ID="d", PART_ID=20251,
             COURSE_ID="c", COURSE_NAME_SL="C", COURSE_CREDITS=2, POINTS=None,
             REGISTER_STATUS="R", FINISH_STATUS="W", IN_GPA="N", IN_AGPA="N", IN_CREDITS="N"),
    ]))


def status():
    return dict(gpa_points=2.0, end_agpa_points=2.7, semester_reg_courses=3,
                semester_reg_credits=8, total_reg_credits=30, start_agpa_points=2.8)


def test_actual_gpa_uses_failed_zero_and_excludes_withdrawal_without_fabricating_points():
    raw = raw_courses()
    clean = raw.iloc[:2].copy()
    result = calculate_observed_metrics(raw, clean, status())
    assert result["actual_plan_gpa"] == 2.0
    assert result["actual_total_credits"] == 8
    assert result["gpa_bearing_credits"] == 6
    assert result["actual_raw_course_count"] == 3
    assert result["actual_cleaned_course_count"] == 2
    assert result["courses"][2]["actual_points"] is None
    assert result["courses"][2]["gpa_included"] is False


def test_missing_points_invalidates_observed_gpa_instead_of_partial_average():
    raw = raw_courses()
    raw.loc[0, "points"] = float("nan")
    result = calculate_observed_metrics(raw, raw.iloc[:2], status())
    assert result["actual_plan_gpa"] is None
    assert result["actual_gpa_status"] == "missing_gpa_bearing_points"


def test_raw_clean_points_conflict_invalidates_evaluation():
    raw = raw_courses()
    clean = raw.iloc[:2].copy()
    clean.loc[0, "points"] = 3.0
    result = calculate_observed_metrics(raw, clean, status())
    assert result["actual_gpa_status"] == "raw_clean_conflict"
    assert result["actual_plan_gpa"] is None
    assert result["raw_clean_conflicts"]


def test_missing_eligible_cleaned_membership_invalidates_actual_accuracy():
    raw = raw_courses()
    result = calculate_observed_metrics(raw, raw.iloc[1:2], status())
    assert result["actual_gpa_status"] == "raw_clean_conflict"
    assert result["actual_plan_gpa"] is None
    assert result["raw_clean_conflicts"][0]["field"] == "missing_cleaned_membership"


def test_unexplained_cleaned_membership_invalidates_actual_accuracy():
    raw = raw_courses()
    extra = raw.iloc[:1].copy()
    extra["student_course_id"] = "unknown"
    extra["course_id"] = "unknown"
    cleaned = pd.concat([raw.iloc[:2], extra], ignore_index=True)
    result = calculate_observed_metrics(raw, cleaned, status())
    assert result["actual_gpa_status"] == "raw_clean_conflict"
    assert result["actual_plan_gpa"] is None


def test_duplicate_actual_course_is_not_silently_deduplicated():
    raw = pd.concat([raw_courses(), raw_courses().iloc[:1]], ignore_index=True)
    with pytest.raises(ValueError, match="Duplicate"):
        calculate_observed_metrics(raw, raw.iloc[:2], status())


def test_target_is_explicit_never_xml_inferred():
    assert explicit_target("a.xml", {"a.xml": 20252}) == 20252
    with pytest.raises(ValueError, match="target"):
        explicit_target("a.xml", {})
    with pytest.raises(ValueError):
        explicit_target("a.xml", {"a.xml": 20254})


def test_xml_order_is_numeric_and_stable(tmp_path):
    for n in (12, 2, 10, 3):
        (tmp_path / f"exportdata ({n}).xml").write_text("<xml/>")
    assert [p.name for p in sorted_xml_files(tmp_path)] == [
        "exportdata (2).xml", "exportdata (3).xml", "exportdata (10).xml", "exportdata (12).xml",
    ]


def test_real_input_adapters_ignore_target_outcomes_and_keep_composite_identity(tmp_path, monkeypatch):
    from pandas.testing import assert_frame_equal
    from src.recommendation_experiments import xml_two_stage_data as data
    from tests.recommendation_fixtures import synthetic_snapshot, synthetic_engine
    snapshot = synthetic_snapshot()
    statuses = pd.DataFrame([
        {**snapshot, "student_status_id": str(part), "part_id": part, "gpa_points": gpa,
         "last_enrolled_gpa": float("nan"), "semester_reg_courses": 2, "semester_reg_credits": 18,
         "total_reg_courses": 20, "total_reg_credits": 60., "total_fail_courses": 1,
         "total_fail_credits": 3., "reg_total_semesters": index + 1, "end_agpa_points": gpa,
         "end_total_in_courses": 99, "end_total_in_credits": 999,
         "semester_pass_courses": 2, "semester_fail_courses": 0}
        for index, (part, gpa) in enumerate([(20242, 2.), (20243, 3.), (20251, 2.5), (20252, 1.)])
    ])
    catalog = pd.DataFrame([
        dict(degree_id="D", course_id=c, course_credits=9., course_name_sl=c,
             course_type_id="T", requirement_type_id="R", year_order=1, semester_order=1, credits_count=30)
        for c in ("A", "B")
    ])
    courses = pd.DataFrame([
        dict(student_course_id=str(i), student_id=s, degree_id=d, part_id=part, course_id=c,
             course_credits=9., points=points, final_mark=75, course_name_sl=c,
             faculty_id="F", attempt_number=attempt, register_status="R", finish_status="P",
             in_gpa="Y", in_agpa="Y", in_credits="Y")
        for i, (s, d, part, c, points, attempt) in enumerate([
            ("S", "D", 20243, "A", 2., 1), ("S", "D", 20251, "A", 3., 2),
            ("S", "D", 20251, "B", 2., 1), ("OTHER", "D", 20251, "A", 0., 1),
            ("S", "OTHER", 20251, "C", 0., 1), ("S", "D", 20252, "Z", 0., 1),
        ])
    ])
    xml = pd.DataFrame([
        dict(STUDENT_ID="S", COURSE_ID=c, COURSE_CREDITS=9., COURSE_NAME_SL=c,
             IS_REQUESTABLE="Y", PART_ID=20252, GPA_POINTS=0, END_AGPA_POINTS=0, FINAL_MARK=0)
        for c in ("A", "B")
    ])
    tables = dict(status=statuses, raw_status=normalize_raw_rows(statuses),
                  history=courses, raw_courses=normalize_raw_rows(courses), catalog=catalog,
                  diplomas=pd.DataFrame([dict(student_id="S", diploma_gpa=80., diploma_type_id="T")]))
    monkeypatch.setattr(data, "xml_rows", lambda p: (xml, False))
    path = tmp_path / "student.xml"
    original = load_case(path, 20251, tables)
    changed = {k: v.copy() for k, v in tables.items()}
    for key in ("status", "raw_status"):
        mask = changed[key].part_id.ge(20251)
        for col in ("gpa_points", "end_agpa_points", "end_total_in_courses", "end_total_in_credits",
                    "semester_pass_courses", "semester_fail_courses", "reg_total_semesters"):
            changed[key].loc[mask, col] = 0
    for key in ("history", "raw_courses"):
        mask = changed[key].part_id.ge(20251)
        changed[key].loc[mask, ["final_mark", "points"]] = 0
    xml.loc[:, ["PART_ID", "GPA_POINTS", "END_AGPA_POINTS", "FINAL_MARK"]] = 0
    poisoned = load_case(path, 20251, changed)
    assert_frame_equal(pd.DataFrame([original.snapshot]), pd.DataFrame([poisoned.snapshot]))
    assert_frame_equal(original.candidates, poisoned.candidates)
    engine = synthetic_engine()
    assert_frame_equal(engine.prepare_candidates(original.snapshot, original.candidates, 20251),
                       engine.prepare_candidates(poisoned.snapshot, poisoned.candidates, 20251))
    assert original.payload["observed"]["actual_plan_gpa"] == 2.5
    assert poisoned.payload["observed"]["actual_plan_gpa"] == 0
    assert set(original.actual_raw.course_id) == {"A", "B"}
    assert set(original.actual_raw.student_id) == {"S"}
    assert set(original.actual_raw.degree_id) == {"D"}
    assert set(original.actual_raw.part_id) == {20251}
