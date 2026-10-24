"""The pilot keeps real baseline diagnostics separate from valid recommendations."""
import copy
import importlib
import importlib.util
import json

import pandas as pd
import pytest

from tests.recommendation_fixtures import synthetic_engine
from tools.recommendation_pilot_20251 import adapter


def engine_module():
    name = "tools.recommendation_pilot_20251.engine"
    assert importlib.util.find_spec(name) is not None, "Pilot baseline bridge is missing"
    return importlib.import_module(name)


def test_pilot_bridge_is_available():
    engine_module()


def payloads(count=4):
    info = {"STUDENT_ID": "S", "DEGREE_ID": "D", "STATUS_SEMESTER_ID": "20251",
            "STUDENT_STATUS_ID": "target", "FACULTY_ID": "F", "GRADE_VERSION_ID": "1",
            "START_AGPA_POINTS": "2.5", "START_TOTAL_IN_COURSES": "10",
            "START_TOTAL_IN_CREDITS": "30", "DEGREE_CREDITS_COUNT": "120",
            "TOTAL_REG_COURSES": "31", "TOTAL_REG_CREDITS": "97.5",
            "TOTAL_FAIL_COURSES": "7", "TOTAL_FAIL_CREDITS": "19.25",
            "REG_TOTAL_SEMESTERS": "9", "SEMESTER_REG_COURSES": "3"}
    student = {"success": True, "data": {"studentDegreeInfo": info,
        "studentAcademicInfo": {"DIPLOMA_GPA": "88.5", "DIPLOMA_TYPE_ID": "T"},
        "studentSummaryInfo": None}}
    courses = {"success": True, "data": {"allowRegisterAllOptional": "N",
        "registserRule": {"LOAD_TYPE": "CREDIT", "MIN_CREDITS": "1", "MAX_CREDITS": "18",
                         "MIN_STUDY_CREDITS": "1", "MAX_STUDY_CREDITS": "18", "MAX_NEW_COURSES": "10"},
        "availableCourses": [{"COURSE_ID": chr(65 + i), "COURSE_NAME_SL": f"Course {i}",
            "COURSE_CREDITS": "3", "ATTEMPTS_COUNT": "0", "REQUIREMENT_TYPE_ID": "R",
            "REQUIREMENT_ID": "G", "CREDITS_COUNT": "120", "REQUIREMENT_PASSED_CREDITS": "0",
            "YEAR_ORDER": "1", "SEMESTER_ORDER": "1", "IS_REQUESTABLE": "Y",
            "ALLOW_REGISTER": "Y", "STATUS_REASON_CODE": "REQUESTABLE", "FINISH_STATUS": None,
            "LAST_REGISTER_SEMESTER_ID": None, "PASSED_PREREQUISITES": ","} for i in range(count)]}}
    return student, courses


@pytest.fixture
def bridge(tmp_path):
    module = engine_module()
    student = {"sample_id": "sample", "student_id": "S", "degree_id": "D", "part_id": 20251}
    folder = tmp_path / "snapshots/after_backend_fix/api_data" / "students" / "sample"
    folder.mkdir(parents=True)
    sp, cp = payloads()

    def save(student_payload=sp, courses_payload=cp):
        for name, payload in (("student_response", student_payload), ("courses_response", courses_payload)):
            path = folder / (name + ".json")
            path.write_text(json.dumps(payload), encoding="utf-8")
            path.with_suffix(".meta.json").write_text(json.dumps({"sha256": adapter.sha256(path),
                "bytes": path.stat().st_size, "identity": {k: student[k] for k in ("student_id", "degree_id", "part_id")}}))

    save()
    instance = module.PilotEngine(root=tmp_path)
    instance._baseline = synthetic_engine()
    instance._catalog = pd.DataFrame({"degree_id": ["D"] * 4, "course_id": list("ABCD"),
        "course_type_id": ["T"] * 4, "requirement_type_id": ["R"] * 4,
        "course_credits": [3.] * 4, "credits_count": [120.] * 4,
        "year_order": [1] * 4, "semester_order": [1] * 4})
    return module, instance, student, sp, cp, save


def test_real_baseline_diagnostics_never_become_unverified_recommendations(bridge):
    _, engine, student, _, _, _ = bridge
    result = engine.evaluate_student(student, target_credits=6)
    a = result["experiments"]["A"]
    assert result["status"] == a["status"] == "PREDICTION_AVAILABLE"
    assert a["plan_status"] == "PROVISIONAL_PLAN"
    assert a["cumulative_gpa_status"] == "UNAVAILABLE"
    assert a["plans"] == []
    assert len(a["diagnostic_plans"]) == 6
    first = a["diagnostic_plans"][0]
    assert first["total_credits"] == 6
    assert first["expected_plan_gpa"] == 2
    assert first["expected_failed_credits"] == pytest.approx(.6)
    assert first["validity"] == "UNVERIFIED"
    assert first["projected_cumulative_gpa"] is None
    assert first["is_expected_cumulative_improvement"] is None
    assert result["experiments"]["C"]["diagnostic_plans"] == []
    assert first["plan_difficulty_balance"]["source_experiment"] == "A"
    assert len(a["course_predictions"]) == 12
    assert {r["plan_id"] for r in a["course_predictions"]} == set(range(6))
    assert all("course_history_fallback_level" in r for r in a["course_predictions"])
    json.dumps(result, allow_nan=False)


def test_snapshot_keeps_mandated_values_and_unknown_gap(bridge):
    module, _, student, _, _, _ = bridge
    inputs = adapter.load_student_inputs(student, root=bridge[1].root)
    snapshot, issues = module.build_snapshot(inputs)
    assert snapshot["prior_total_reg_courses"] == 31
    assert snapshot["prior_total_reg_credits"] == 97.5
    assert snapshot["prior_total_fail_courses"] == 7
    assert snapshot["prior_total_fail_credits"] == 19.25
    assert snapshot["prior_registered_semesters"] == 9
    assert snapshot["diploma_gpa"] == 88.5
    assert snapshot["diploma_type_id"] == "T"
    assert snapshot["observed_gap_semesters"] is None
    assert "STUDENT_GAP_UNAVAILABLE" in issues
    assert "current_gpa_credits" not in snapshot


def test_historical_gpa_lags_use_prior_registered_semesters_only(bridge):
    module, engine, student, sp, cp, save = bridge
    sp["data"]["studentSummaryInfo"] = [
        {"STUDENT_ID": "S", "DEGREE_ID": "D", "PART_ID": "20241", "STUDENT_STATUS_ID": "old1",
         "SEMESTER_REG_COURSES": "2", "GPA_POINTS": "2.2"},
        {"STUDENT_ID": "S", "DEGREE_ID": "D", "PART_ID": "20242", "STUDENT_STATUS_ID": "old2",
         "SEMESTER_REG_COURSES": "3", "GPA_POINTS": "2.8"}]
    save(sp, cp)
    snapshot, _ = module.build_snapshot(adapter.load_student_inputs(student, root=engine.root))
    assert snapshot["gpa_prev_1"] == 2.8
    assert snapshot["gpa_prev_2"] == 2.2
    assert snapshot["observed_gap_semesters"] == 0
    sp["data"]["studentSummaryInfo"][1]["PART_ID"] = "20251"
    save(sp, cp)
    assert "FUTURE_STUDENT_HISTORY" in engine.evaluate_student(student, target_credits=6)["issues"]


def test_explicit_credit_limit_does_not_silently_lower_target(bridge):
    _, engine, student, _, cp, save = bridge
    cp["data"]["registserRule"]["MAX_CREDITS"] = "3"
    save(courses_payload=cp)
    result = engine.evaluate_student(student, target_credits=6)
    assert result["status"] == "NO_MATCHING_PLAN"
    assert result["search"]["evaluated_plan_count"] == 0
    assert result["experiments"]["A"]["diagnostic_plans"] == []


def test_unconfirmed_zero_new_course_limit_does_not_invent_a_hard_cap(bridge):
    _, engine, student, _, cp, save = bridge
    cp["data"]["registserRule"]["MAX_NEW_COURSES"] = "0"
    save(courses_payload=cp)
    result = engine.evaluate_student(student, target_credits=6)
    assert result["status"] == "PREDICTION_AVAILABLE"
    assert result["experiments"]["A"]["plan_status"] == "PROVISIONAL_PLAN"
    assert result["search"]["evaluated_plan_count"] == 6
    assert "MAX_NEW_COURSES_POLICY_UNCONFIRMED" in result["issues"]


def test_exact_plan_bound_is_reproducible_and_marked_partial(bridge):
    _, engine, student, _, _, _ = bridge
    first = engine.evaluate_student(student, target_credits=6, max_plans=2)
    second = engine.evaluate_student(student, target_credits=6, max_plans=2)
    assert first["search"]["evaluated_plan_count"] == 2
    assert first["search"]["truncated"] is True
    assert first["search"]["global_optimum_guaranteed"] is False
    assert first["search"]["plan_set_sha256"] == second["search"]["plan_set_sha256"]
    assert [r["courses"][0]["course_id"] for r in first["experiments"]["A"]["diagnostic_plans"]] == ["A", "A"]


def test_denied_and_unauthorized_exception_courses_are_excluded(bridge):
    _, engine, student, _, cp, save = bridge
    cp["data"]["availableCourses"][0]["ALLOW_REGISTER"] = "N"
    cp["data"]["availableCourses"][1]["STATUS_REASON_CODE"] = "EXCEPTION"
    cp["data"]["availableCourses"][2]["STATUS_REASON_CODE"] = "DEAN"
    save(courses_payload=cp)
    result = engine.evaluate_student(student, target_credits=3)
    assert result["candidate_count"] == 1
    assert {r["course_id"] for r in result["experiments"]["A"]["course_predictions"]} == {"D"}


@pytest.mark.parametrize("mutation,code", [
    ("catalog_credit", "CATALOG_CONFLICT"), ("course_identity", "IDENTITY_MISMATCH"),
    ("duplicate", "CONFLICTING_DUPLICATE"), ("bad_diploma", "INVALID_NUMBER"),
    ("prior_current", "FUTURE_COURSE_SOURCE")])
def test_conflicting_sources_block_before_predictions(bridge, mutation, code):
    _, engine, student, sp, cp, save = bridge
    if mutation == "catalog_credit":
        cp["data"]["availableCourses"][0]["COURSE_CREDITS"] = "4"
    elif mutation == "course_identity":
        cp["data"]["availableCourses"][0]["STUDENT_ID"] = "other"
    elif mutation == "duplicate":
        duplicate = copy.deepcopy(cp["data"]["availableCourses"][0])
        duplicate["COURSE_CREDITS"] = "5"
        cp["data"]["availableCourses"].append(duplicate)
    elif mutation == "bad_diploma":
        sp["data"]["studentAcademicInfo"]["DIPLOMA_GPA"] = "NaN"
    else:
        cp["data"]["availableCourses"][0]["LAST_REGISTER_SEMESTER_ID"] = "20251"
    save(sp, cp)
    result = engine.evaluate_student(student, target_credits=6)
    assert result["status"] == "BLOCKED"
    assert code in result["issues"]
    assert result["experiments"]["A"]["diagnostic_plans"] == []


def test_input_mutation_changes_shared_fingerprint(bridge):
    _, engine, student, sp, cp, save = bridge
    first = engine.evaluate_student(student, target_credits=6)
    sp["data"]["studentDegreeInfo"]["TOTAL_REG_CREDITS"] = "98"
    save(sp, cp)
    second = engine.evaluate_student(student, target_credits=6)
    assert first["input_fingerprints"] != second["input_fingerprints"]
    assert first["search"]["shared_inputs_sha256"] != second["search"]["shared_inputs_sha256"]


def test_original_inference_preserves_missing_faculty_without_synthetic_id(bridge):
    module, engine, student, sp, cp, save = bridge
    sp["data"]["studentDegreeInfo"]["FACULTY_ID"] = None
    save(sp, cp)
    snapshot, issues = module.build_snapshot(adapter.load_student_inputs(student, root=engine.root))
    assert snapshot["faculty_id"] is None
    assert "FACULTY_ID_UNAVAILABLE" in issues
    result = engine.evaluate_student(student, target_credits=6)
    assert len(result["experiments"]["A"]["diagnostic_plans"]) == 6


def test_unknown_group_completion_stays_unavailable_while_predictions_remain_diagnostic(bridge):
    _, engine, student, sp, cp, save = bridge
    for row in cp["data"]["availableCourses"]:
        row["REQUIREMENT_PASSED_CREDITS"] = None
    cp["data"]["allowRegisterAllOptional"] = "Y"
    save(sp, cp)
    result = engine.evaluate_student(student, target_credits=6)
    assert "REQUIREMENT_GROUP_CREDITS_UNAVAILABLE" in result["issues"]
    assert len(result["experiments"]["A"]["diagnostic_plans"]) == 6
    assert result["policy_evidence"]["optional_overflow_allowed"] is True
    assert result["experiments"]["A"]["plans"] == []


def test_missing_degree_credit_count_stays_unknown_in_original_feature_matrix(bridge):
    module, engine, student, sp, cp, save = bridge
    sp["data"]["studentDegreeInfo"]["DEGREE_CREDITS_COUNT"] = None
    save(sp, cp)
    snapshot, issues = module.build_snapshot(adapter.load_student_inputs(student, root=engine.root))
    assert snapshot["degree_credits_count"] is None
    assert "DEGREE_CREDITS_COUNT_UNAVAILABLE" in issues
    result = engine.evaluate_student(student, target_credits=6)
    assert len(result["experiments"]["A"]["diagnostic_plans"]) == 6
    assert engine._baseline.grade_model.matrices[-1].degree_credits_count.isna().all()


def test_course_source_failure_retains_student_history_diagnostics(bridge):
    _, engine, student, sp, cp, save = bridge
    cp["data"]["availableCourses"][0]["LAST_REGISTER_SEMESTER_ID"] = "20251"
    save(sp, cp)
    result = engine.evaluate_student(student, target_credits=6)
    assert "STUDENT_GAP_UNAVAILABLE" in result["issues"]
    assert "FUTURE_COURSE_SOURCE" in result["issues"]


def test_unknown_grade_scale_version_is_an_explicit_blocker(bridge):
    _, engine, student, sp, cp, save = bridge
    sp["data"]["studentDegreeInfo"]["GRADE_VERSION_ID"] = "999"
    save(sp, cp)
    result = engine.evaluate_student(student, target_credits=6)
    assert "UNSUPPORTED_GRADE_VERSION" in result["issues"]
    assert result["experiments"]["A"]["course_predictions"] == []


def test_impossible_fractional_target_stops_at_state_budget_without_false_no_plan_proof(bridge):
    _, engine, student, sp, _, save = bridge
    _, cp = payloads(count=26)
    for row in cp["data"]["availableCourses"]:
        row["COURSE_CREDITS"] = "1"
    engine._catalog = pd.concat([engine._catalog.iloc[:1]] * 26, ignore_index=True)
    engine._catalog["course_id"] = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    engine._catalog["course_credits"] = 1.
    save(sp, cp)
    # No subset of integer credits reaches 12.5, but proving this by the
    # original traversal would visit millions of states without the budget.
    result = engine.evaluate_student(student, target_credits=12.5)
    assert result["status"] == "BLOCKED"
    assert "SEARCH_BUDGET_EXHAUSTED" in result["issues"]
    assert result["search"]["visited_search_states"] == 200000
    assert result["search"]["state_budget"] == 200000
    assert result["search"]["search_budget_exhausted"] is True
    assert result["search"]["truncated"] is True
    assert result["search"]["complete_plan_space_examined"] is False
    assert result["search"]["total_plan_count"] is None
    assert result["experiments"]["A"]["diagnostic_plans"] == []


def test_state_budget_preserves_exact_plans_already_found(bridge):
    module, original, student, _, _, _ = bridge
    limited = module.PilotEngine(root=original.root, max_search_states=8)
    limited._baseline, limited._catalog = original._baseline, original._catalog
    result = limited.evaluate_student(student, target_credits=6)
    assert result["status"] == "PREDICTION_AVAILABLE"
    assert result["experiments"]["A"]["plan_status"] == "PROVISIONAL_PLAN"
    assert result["search"]["search_budget_exhausted"] is True
    assert result["search"]["visited_search_states"] == 8
    assert result["search"]["evaluated_plan_count"] == 1
    assert result["search"]["scanned_exact_plan_count"] == 1
    assert result["search"]["truncated"] is True
    assert result["search"]["total_plan_count"] is None
    plan = result["experiments"]["A"]["diagnostic_plans"][0]
    assert [row["course_id"] for row in plan["courses"]] == ["A", "B"]
    assert plan["total_credits"] == 6
    assert plan["validity"] == "UNVERIFIED"
