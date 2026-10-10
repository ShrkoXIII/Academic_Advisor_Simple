from copy import deepcopy
import importlib

import pytest

from tests.api_fixtures import catalog, payloads, grade_scale


def service(request, **kwargs):
    cls = importlib.import_module("src.api.service").ApiService
    return cls(catalog=catalog(request), grade_scale=grade_scale(), **kwargs)


def test_complete_student_uses_previous_gpa_and_explicit_denominator():
    request = payloads(complete=True)
    result = service(request).validate_student(request)
    assert result.errors == []
    assert result.normalized["gpa_prev_1"] == 3.13
    assert result.normalized["gpa_prev_2"] == 2.72
    assert result.normalized["current_gpa_credits"] == 108
    assert result.normalized["prior_total_reg_credits"] == 111


def test_actual_sanitized_student_reports_missing_diploma_and_denominator():
    request = payloads()
    result = service(request).validate_student(request)
    assert {e["field"] for e in result.errors} >= {"diploma_gpa", "diploma_type_id", "current_gpa_credits"}


@pytest.mark.parametrize("component", ["student", "courses"])
@pytest.mark.parametrize("field,value", [("student_id", "other"), ("degree_id", "other"), ("part_id", 20252)])
def test_independent_source_bindings_reject_wrong_identity(component, field, value):
    request = payloads(complete=True)
    request["source_contexts"][component][field] = value
    result = getattr(service(request), "validate_" + component)(request)
    assert any(e["code"] == "IDENTITY_MISMATCH" for e in result.errors)


def test_target_outcomes_never_enter_snapshot():
    request = payloads(complete=True)
    first = service(request).validate_student(request).normalized
    info = request["student_api_response"]["data"]["studentDegreeInfo"]
    info.update(GPA_POINTS=999, END_AGPA_POINTS=999, END_TOTAL_IN_CREDITS=999, SEMESTER_FAIL_CREDITS=999)
    assert service(request).validate_student(request).normalized == first


def test_all_17_courses_and_attempt_conversion_preserve_group_identity():
    request = payloads(complete=True)
    result = service(request).validate_courses(request)
    assert result.errors == []
    assert len(result.normalized["candidates"]) == 17
    source = {r["COURSE_ID"]: r for r in request["courses_api_response"]["data"]["availableCourses"]}
    for row in result.normalized["candidates"]:
        assert row["attempt_number"] == int(source[row["course_id"]]["ATTEMPTS_COUNT"]) + 1
        assert row["plan_course_type_id"] == "3"
    assert result.checks["identity"] == "php_attested"


@pytest.mark.parametrize("value", [-1, "1.5", True, "NaN"])
def test_invalid_attempt_count_rejected(value):
    request = payloads(complete=True)
    request["courses_api_response"]["data"]["availableCourses"][0]["ATTEMPTS_COUNT"] = value
    assert service(request).validate_courses(request).errors


def test_identical_duplicates_removed_conflicts_rejected():
    request = payloads(complete=True)
    rows = request["courses_api_response"]["data"]["availableCourses"]
    rows.append(deepcopy(rows[0]))
    result = service(request).validate_courses(request)
    assert len(result.normalized["candidates"]) == 17
    rows[-1]["COURSE_CREDITS"] = "9"
    assert service(request).validate_courses(request).errors


def test_invalid_identity_is_checked_before_ineligible_filtering():
    request = payloads(complete=True)
    row = request["courses_api_response"]["data"]["availableCourses"][0]
    row.update(STUDENT_ID="other", IS_REQUESTABLE="N")
    assert any(e["code"] == "IDENTITY_MISMATCH" for e in service(request).validate_courses(request).errors)


def test_validation_independent_of_models_history_and_missing_catalog():
    cls = importlib.import_module("src.api.service").ApiService
    request = payloads(complete=True)
    api = cls()
    assert api.validate_student(request).normalized["gpa_prev_1"] == 3.13
    result = api.validate_courses(request)
    assert result.status == "partial"
    assert result.checks["catalog"] == "unavailable"
    assert result.summary["candidate_count"] == 17


def test_status_and_exception_information_are_not_inferred():
    request = payloads(complete=True)
    request["integration_context"]["previous_course_statuses"] = {}
    request["integration_context"]["registration_policy"]["approved_exception_course_ids"] = []
    codes = {e["code"] for e in service(request).validate_courses(request).errors}
    assert {"MISSING_PREVIOUS_STATUS", "UNRESOLVED_EXCEPTION"} <= codes


def test_duplicate_conflicting_eligibility_cannot_disappear_during_filtering():
    request = payloads(complete=True)
    rows = request["courses_api_response"]["data"]["availableCourses"]
    rows.append(dict(rows[0], ALLOW_REGISTER="N"))
    result = service(request).validate_courses(request)
    assert any(error["code"] == "CONFLICTING_DUPLICATE" for error in result.errors)
    assert result.http_status == 409


def test_matching_decimal_denominator_sources_do_not_conflict_after_float_conversion():
    request = payloads(complete=True)
    request["student_api_response"]["data"]["studentDegreeInfo"]["CURRENT_GPA_CREDITS"] = "108.1"
    request["integration_context"]["student_values"]["current_gpa_credits"]["value"] = "108.1"
    assert not service(request).validate_student(request).errors


def test_conflicting_historical_semester_aliases_rejected():
    request = payloads(complete=True)
    request["student_api_response"]["data"]["studentSummaryInfo"][0]["SEMESTER_ID"] = "20243"
    assert any(error["code"] == "IDENTITY_MISMATCH" for error in service(request).validate_student(request).errors)


def test_student_root_identity_is_checked_as_well_as_degree_info():
    request = payloads(complete=True)
    request["student_api_response"]["data"]["STUDENT_ID"] = "other"
    assert any(error["code"] == "IDENTITY_MISMATCH" for error in service(request).validate_student(request).errors)


def test_complete_schema_rejects_invalid_previous_gpa_and_fractional_counter():
    request = payloads(complete=True)
    rows = request["student_api_response"]["data"]["studentSummaryInfo"]
    for index, row in enumerate(rows):
        row.update(LAST_ENROLLED_GPA="99", TOTAL_REG_COURSES="42", TOTAL_REG_CREDITS="111",
                   TOTAL_FAIL_COURSES="1", TOTAL_FAIL_CREDITS="3", REG_TOTAL_SEMESTERS=str(index + 1))
    assert any(error["code"] == "INVALID_GPA" for error in service(request).validate_student(request).errors)
    for row in rows:
        row["LAST_ENROLLED_GPA"] = None
    rows[0]["REG_TOTAL_SEMESTERS"] = "1.5"
    assert any(error["code"] == "INVALID_NUMBER" for error in service(request).validate_student(request).errors)


@pytest.mark.parametrize("component", ["student", "courses"])
def test_response_wrapper_identity_cannot_conflict_with_data(component):
    request = payloads(complete=True)
    request[component + "_api_response"]["STUDENT_ID"] = "other"
    result = getattr(service(request), "validate_" + component)(request)
    assert any(error["code"] == "IDENTITY_MISMATCH" for error in result.errors)


def test_count_outside_model_float_range_is_input_error():
    request = payloads(complete=True)
    request["integration_context"]["student_values"]["prior_total_reg_courses"]["value"] = "1e1000"
    assert any(error["code"] == "INVALID_NUMBER" for error in service(request).validate_student(request).errors)
