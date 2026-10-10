"""Actual two-stage core integration using deterministic models, never trained assets."""
from copy import deepcopy
from decimal import Decimal
import json
import subprocess
import sys

import pandas as pd
import pytest

from src.api.service import ApiService
from src.api.settings import ApiSettings
from src.api.validation import ApiError
from src.features.temporal_features import add_student_history_features, compute_student_gpa_history, CourseHistoryState
from src.recommendation.two_stage_engine import TwoStagePlanRecommender
from tests.api_fixtures import payloads, catalog, grade_scale
from tests.test_two_stage_activation import approve_manifest
from tests.two_stage_fixtures import synthetic_artifacts, history_manager, new_history_delta


def api_engine(root):
    request = payloads(complete=True)
    rows = request["courses_api_response"]["data"]["availableCourses"]
    # Small exact-search case: three optional courses of two credits must not
    # fit their remaining four-credit cap, even together with six main credits.
    request["courses_api_response"]["data"]["availableCourses"] = (
        [row for row in rows if row["REQUIREMENT_ID"] == "5.111"] +
        [row for row in rows if row["REQUIREMENT_ID"] == "6.111"][:5])
    request["target_credits"] = 12
    artifacts = synthetic_artifacts()
    artifacts = type(artifacts)(artifacts.stage1, artifacts.stage2, grade_scale(), artifacts.manifest)
    approve_manifest(artifacts.manifest)
    manager = history_manager(root)
    engine = TwoStagePlanRecommender.from_loaded_artifacts(artifacts, manager)
    api = ApiService(engine=engine, catalog=catalog(request), grade_scale=grade_scale())
    return api, artifacts, request


def test_api_calls_actual_core_with_33_and_47_features_and_group_caps(tmp_path):
    api, artifacts, request = api_engine(tmp_path)
    result = api.recommend(request)
    assert result["status"] == "ok"
    assert result["metadata"]["production_ranking_strategy"] == "pareto v1 -> pareto v1"
    assert len(result["recommendations"]) == 3
    assert artifacts.stage1.grade_model.matrices[0].shape[1] == 33
    assert artifacts.stage2.grade_model.matrices[0].shape[1] == 47
    optional_ids = {row["COURSE_ID"] for row in request["courses_api_response"]["data"]["availableCourses"]
                    if row["REQUIREMENT_ID"] == "5.111"}
    for plan in result["recommendations"]:
        assert sum(Decimal(str(course["course_credits"])) for course in plan["courses"] if course["course_id"] in optional_ids) <= 4


def test_original_gpa_calculation_and_helper_are_identical_on_full_schema():
    frame = pd.DataFrame({"student_status_id": list("abcdef"), "student_id": ["S"] * 6,
        "degree_id": ["D"] * 6, "part_id": [20221, 20222, 20231, 20232, 20233, 20241],
        "semester_reg_courses": [2, 0, 1, 0, 2, 1], "gpa_points": [2.5, 0, 3., None, 3.5, None],
        "last_enrolled_gpa": [None, 2.5, None, 3., None, None], "total_reg_courses": [0, 2, 2, 3, 3, 5],
        "total_reg_credits": [0., 6, 6, 9, 9, 15], "total_fail_courses": [0] * 6,
        "total_fail_credits": [0.] * 6, "reg_total_semesters": [1, 1, 2, 2, 3, 4]})
    original, _ = add_student_history_features(frame[["student_status_id"]], frame.iloc[:0][["student_status_id"]], frame)
    pure = compute_student_gpa_history(frame)
    pd.testing.assert_frame_equal(original[pure.columns], pure.reset_index(drop=True))


def test_all_history_identity_rows_checked_even_when_first_schema_incomplete():
    request = payloads(complete=True)
    rows = request["student_api_response"]["data"]["studentSummaryInfo"]
    rows[0].pop("GPA_POINTS")
    rows[-1]["STUDENT_ID"] = "other"
    assert any(error["code"] == "IDENTITY_MISMATCH" for error in ApiService().validate_student(request).errors)


def test_supplement_conflict_with_original_beginning_fail_total_is_rejected():
    request = payloads(complete=True)
    request["integration_context"]["student_values"]["prior_total_fail_credits"]["value"] = 99
    assert any(error["code"] == "CONFLICTING_STUDENT_SOURCE" for error in ApiService().validate_student(request).errors)


def test_nonregistered_semesters_preserve_gpa_and_current_gap():
    request = payloads(complete=True)
    rows = request["student_api_response"]["data"]["studentSummaryInfo"]
    rows[-2].update(SEMESTER_REG_COURSES="0", GPA_POINTS="0")
    rows[-1].update(SEMESTER_REG_COURSES="0", GPA_POINTS="0")
    result = ApiService().validate_student(request)
    assert result.normalized["gpa_prev_1"] == 2.86
    assert result.normalized["gpa_prev_2"] == 3.25
    assert result.normalized["observed_gap_semesters"] == 1


def test_future_supplement_and_history_rejected_before_models(tmp_path):
    api, artifacts, request = api_engine(tmp_path)
    request["integration_context"]["student_values"]["current_gpa_credits"]["as_of_part"] = 20251
    with pytest.raises(ApiError):
        api.recommend(request)
    assert not artifacts.stage1.grade_model.matrices and not artifacts.stage2.grade_model.matrices


def test_missing_optional_max_new_does_not_invent_a_limit():
    request = payloads(complete=True)
    request["courses_api_response"]["data"]["registserRule"].pop("MAX_NEW_COURSES")
    result = ApiService(catalog=catalog(request)).validate_courses(request)
    assert not result.errors
    assert result.normalized["registration_rules"]["MAX_NEW_COURSES"] is None


def test_independent_startup_load_failures_and_import_without_http_dependencies(tmp_path):
    def unavailable():
        raise FileNotFoundError("private")
    api = ApiService()
    artifacts = synthetic_artifacts()
    approve_manifest(artifacts.manifest)
    api.initialize(catalog_loader=unavailable, grade_scale_loader=unavailable,
                   history_loader=unavailable, model_loader=lambda: artifacts)
    assert api.health()["model_readiness"]["ready"] is True
    assert api.health()["history_readiness"]["ready"] is False
    script = "import sys; import src.api; from src.api.service import ApiService; assert 'fastapi' not in sys.modules; assert 'pydantic' not in sys.modules"
    completed = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stderr


def test_delta_replay_conflict_and_validation_never_changes_bundle(tmp_path):
    manager = history_manager(tmp_path)
    delta = new_history_delta()
    manager.update_history_from_payload(history_payload=delta)  # Own synthetic bundle only.
    api = ApiService(history_manager=manager)
    body = {"part_id": delta["delta_part"], "rows": delta["aggregates"],
            "finalization": {"finalized_part_id": 20251, "approval_reference": "synthetic_finalization"}}
    before = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = api.validate_delta(body)
    assert result.status == "valid" and result.summary["status"] == "already_applied"
    body["rows"][0]["mark_sum"] = 1700
    conflict = api.validate_delta(body)
    assert conflict.http_status == 409
    assert before == {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


def test_delta_aggregates_equal_individual_outcomes_without_estimated_points(tmp_path):
    from src.recommendation.history_update import apply_history_delta
    manager = history_manager(tmp_path)
    delta = new_history_delta()
    outcomes = pd.DataFrame({"part_id": [20251] * 20, "degree_id": ["D"] * 20, "faculty_id": ["F"] * 20,
        "course_id": ["C00"] * 20, "course_credits": [3] * 20, "plan_requirement_type_id": ["R"] * 20,
        "attempt_number": [1] * 20, "final_mark": [90] * 20})
    state = deepcopy(manager.capture(target_part=20251)._state)
    expected = deepcopy(state)
    expected.update(outcomes)
    actual = apply_history_delta(state, history_payload=delta)
    assert actual.global_sums == expected.global_sums
    for level in actual.tables:
        pd.testing.assert_frame_equal(actual.tables[level].sort_index(), expected.tables[level].sort_index())


def test_contract_nullable_history_remains_unknown_and_response_is_explicit(tmp_path):
    api, artifacts, request = api_engine(tmp_path)
    request["integration_context"]["student_values"].pop("prior_total_reg_courses")
    response = api.recommend(request)
    assert response["metadata"]["input_validation"]["student"] == "partial"
    assert "prior_total_reg_courses" in response["metadata"]["unavailable_student_fields"]
    assert artifacts.stage2.grade_model.matrices[0]["prior_total_reg_courses"].isna().all()
