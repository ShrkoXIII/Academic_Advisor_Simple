"""Synthetic, source-attested academic semantics; no university/student I/O."""
from copy import deepcopy

import pandas as pd
import pytest

from src.api.courses_adapter import adapt_courses
from src.api.settings import ApiSettings
from src.api.student_adapter import adapt_student
from src.features.temporal_features import add_student_history_features
from tests.api_fixtures import catalog, grade_scale, payloads


def student_request(*, timing="beginning_of_semester", total=111):
    request = payloads(complete=True)
    info = request["student_api_response"]["data"]["studentDegreeInfo"]
    info["TOTAL_REG_CREDITS"] = total
    values = request["integration_context"]["student_values"]
    values.pop("current_gpa_credits")
    values.pop("prior_total_reg_credits")
    request["integration_context"]["total_reg_credits_source"] = {
        "source": "synthetic_official_gpa_ledger",
        "target_part": 20251, "as_of_part": 20243 if timing == "beginning_of_semester" else 20251,
        "timing": timing, "rules_reference": "synthetic_approved_inclusion_rules_v1",
    }
    return request


def student_result(request):
    return adapt_student(request, settings=ApiSettings(), grade_scale=grade_scale())


def course_request(attempts, finish_status, *, previous_part=None, supplement=None):
    request = payloads(complete=True)
    row = deepcopy(request["courses_api_response"]["data"]["availableCourses"][0])
    row.update(ATTEMPTS_COUNT=attempts, FINISH_STATUS=finish_status,
               LAST_REGISTER_SEMESTER_ID=previous_part)
    request["courses_api_response"]["data"]["availableCourses"] = [row]
    request["integration_context"]["previous_course_statuses"] = {}
    if supplement is not None:
        request["integration_context"]["previous_course_statuses"][row["COURSE_ID"]] = {
            "value": supplement, "source": "synthetic_previous_registration_ledger", "as_of_part": 20243,
        }
    return request


def course_result(request):
    return adapt_courses(request, catalog=catalog(request))


def test_official_beginning_total_supplies_gpa_denominator_and_existing_feature():
    result = student_result(student_request())
    assert result.errors == []
    assert result.normalized["current_gpa_credits"] == 111
    assert result.normalized["prior_total_reg_credits"] == 111
    assert result.normalized["start_total_in_credits"] == 108
    assert result.summary["gpa_credit_provenance"] == {
        "denominator": "php_attested_total_reg_credits_beginning",
        "prior_total_reg_credits": "php_attested_total_reg_credits_beginning",
    }


def test_official_beginning_total_preserves_training_feature_definition():
    request = student_request()
    result = student_result(request)
    status = pd.DataFrame([{
        "student_status_id": "synthetic-status", "student_id": "synthetic-student", "degree_id": "synthetic-degree",
        "part_id": 20251, "semester_reg_courses": 6, "gpa_points": None,
        "last_enrolled_gpa": None, "total_reg_courses": 42, "total_reg_credits": 111,
        "total_fail_courses": 1, "total_fail_credits": 3, "reg_total_semesters": 8,
    }])
    training, _ = add_student_history_features(status[["student_status_id"]],
                                             status[["student_status_id"]].iloc[:0], status)
    assert result.normalized["prior_total_reg_credits"] == training.iloc[0]["prior_total_reg_credits"]
    assert result.normalized["prior_fail_credit_ratio"] == training.iloc[0]["prior_fail_credit_ratio"]


@pytest.mark.parametrize("field", ["current_gpa_credits", "prior_total_reg_credits"])
def test_official_total_rejects_conflicting_sourced_supplement(field):
    request = student_request()
    request["integration_context"]["student_values"][field] = {
        "value": 108, "source": "synthetic_ledger", "as_of_part": 20243,
    }
    result = student_result(request)
    assert any(error["code"] == "CONFLICTING_STUDENT_SOURCE" and error["field"] == field
               for error in result.errors)


def test_post_semester_total_129_does_not_silently_subtract_registered_18():
    request = student_request(timing="end_of_semester", total=129)
    result = student_result(request)
    assert any(error["code"] == "GPA_DENOMINATOR_DERIVATION_UNPROVEN" for error in result.errors)
    assert result.normalized["current_gpa_credits"] is None


def test_post_semester_denominator_requires_complete_additive_authoritative_count():
    request = student_request(timing="end_of_semester", total=129)
    evidence = request["integration_context"]["total_reg_credits_source"]
    evidence.update(semester_complete=True, additive_credit_accounting=True, semester_gpa_counted_credits=18)
    result = student_result(request)
    assert result.errors == []
    assert result.normalized["current_gpa_credits"] == 111
    assert result.normalized["prior_total_reg_credits"] == 111
    assert result.summary["gpa_credit_provenance"]["denominator"] == "php_attested_total_reg_credits_derived"


def test_post_semester_derivation_honors_confirmed_exclusions():
    request = student_request(timing="end_of_semester", total=129)
    request["integration_context"]["total_reg_credits_source"].update(
        semester_complete=True, additive_credit_accounting=True, semester_gpa_counted_credits=15)
    result = student_result(request)
    assert result.errors == []
    assert result.normalized["current_gpa_credits"] == 114  # Registered 18 includes three excluded credits.


@pytest.mark.parametrize("changes", [
    {"semester_complete": False}, {"additive_credit_accounting": False},
    {"semester_gpa_counted_credits": None}, {"rules_reference": ""},
])
def test_post_semester_derivation_rejects_missing_finalization_or_rules(changes):
    request = student_request(timing="end_of_semester", total=129)
    request["integration_context"]["total_reg_credits_source"].update({
        "semester_complete": True, "additive_credit_accounting": True,
        "semester_gpa_counted_credits": 18, **changes})
    assert student_result(request).errors


@pytest.mark.parametrize("field,value", [("target_part", 20252), ("as_of_part", 20242),
                                         ("as_of_part", 20251), ("source", ""), ("timing", "unknown")])
def test_official_total_rejects_wrong_snapshot_or_unverified_semantics(field, value):
    request = student_request()
    request["integration_context"]["total_reg_credits_source"][field] = value
    result = student_result(request)
    assert result.errors
    assert result.normalized["current_gpa_credits"] is None


@pytest.mark.parametrize("total,semester_count", [(129, 19), (12, 18)])
def test_derived_gpa_count_cannot_exceed_registered_or_cumulative_count(total, semester_count):
    request = student_request(timing="end_of_semester", total=total)
    request["integration_context"]["total_reg_credits_source"].update(
        semester_complete=True, additive_credit_accounting=True, semester_gpa_counted_credits=semester_count)
    assert student_result(request).errors


def test_unattested_totals_and_completed_credits_never_supply_denominator():
    request = student_request()
    request["integration_context"].pop("total_reg_credits_source")
    result = student_result(request)
    assert any(error["code"] == "GPA_DENOMINATOR_TEMPORALLY_AMBIGUOUS" for error in result.errors)
    assert result.normalized["current_gpa_credits"] is None
    assert result.normalized["prior_total_reg_credits"] is None


def test_missing_official_total_requires_sourced_override():
    request = student_request()
    request["student_api_response"]["data"]["studentDegreeInfo"].pop("TOTAL_REG_CREDITS")
    assert student_result(request).errors


def test_legacy_sourced_override_keeps_separate_model_feature_provenance():
    result = student_result(payloads(complete=True))
    assert result.errors == []
    assert result.normalized["current_gpa_credits"] == 108
    assert result.normalized["prior_total_reg_credits"] == 111
    assert result.summary["gpa_credit_provenance"] == {
        "denominator": "sourced_override", "prior_total_reg_credits": "sourced_supplement",
    }


@pytest.mark.parametrize("field", ["current_gpa_credits", "prior_total_reg_credits"])
def test_legacy_credit_snapshot_cannot_be_stale_for_target(field):
    request = payloads(complete=True)
    request["integration_context"]["student_values"][field]["as_of_part"] = 20242
    result = student_result(request)
    assert any(error["code"] == "GPA_DENOMINATOR_TEMPORALLY_AMBIGUOUS" and error["field"] == field
               for error in result.errors)


def test_zero_previous_attempts_and_null_finish_status_are_new_without_supplement():
    result = course_result(course_request(0, None))
    assert result.errors == []
    assert result.normalized["candidates"][0]["previous_course_status"] == "NEW"
    assert result.normalized["candidates"][0]["attempt_number"] == 1


@pytest.mark.parametrize("status,expected", [("F", "FAILED"), ("FE", "FAILED"), ("W", "WITHDRAWN")])
def test_repeated_course_uses_official_previous_status_without_supplement(status, expected):
    result = course_result(course_request(2, status))
    assert result.errors == []
    assert result.normalized["candidates"][0]["previous_course_status"] == expected
    assert result.normalized["candidates"][0]["attempt_number"] == 3


def test_repeat_missing_status_is_invalid_and_never_inferred_from_attempts():
    result = course_result(course_request(3, None))
    assert any(error["code"] == "MISSING_PREVIOUS_STATUS" for error in result.errors)
    assert result.normalized["candidates"][0]["previous_course_status"] == "UNKNOWN"


def test_repeat_missing_status_accepts_authoritative_prior_ledger():
    result = course_result(course_request(1, None, supplement="WITHDRAWN"))
    assert result.errors == []
    assert result.normalized["candidates"][0]["previous_course_status"] == "WITHDRAWN"


@pytest.mark.parametrize("status,supplement", [("F", None), ("W", None), (None, "FAILED"), (None, "UNKNOWN")])
def test_zero_attempts_conflicting_previous_outcome_is_rejected(status, supplement):
    result = course_result(course_request(0, status, supplement=supplement))
    assert any(error["code"] == "CONFLICTING_STATUS" for error in result.errors)
    assert result.normalized["candidates"] == []


@pytest.mark.parametrize("status,supplement", [("F", "WITHDRAWN"), (None, "NEW")])
def test_repeated_course_conflicting_official_and_supplemental_status_rejected(status, supplement):
    result = course_result(course_request(1, status, supplement=supplement))
    assert any(error["code"] == "CONFLICTING_STATUS" for error in result.errors)


@pytest.mark.parametrize("status", ["I", "IP", "nonsense"])
def test_unresolved_official_status_cannot_enable_repeat(status):
    assert course_result(course_request(1, status)).errors


def test_repeat_target_or_future_registration_status_is_rejected():
    result = course_result(course_request(1, "F", previous_part=20251))
    assert any(error["code"] == "FUTURE_SOURCE" for error in result.errors)


def test_matching_official_and_supplemental_status_preserves_canonical_mapping():
    result = course_result(course_request(1, "F", previous_part=20243, supplement="FAILED"))
    assert result.errors == []


def test_typed_http_contract_accepts_official_total_evidence_and_rejects_string_bool():
    from pydantic import ValidationError
    from src.api.schemas import StudentValidationRequest
    request = student_request(timing="end_of_semester", total=129)
    request.pop("courses_api_response")
    request.pop("target_credits")
    request.pop("history_as_of_part")
    evidence = request["integration_context"]["total_reg_credits_source"]
    evidence.update(semester_complete=True, additive_credit_accounting=True, semester_gpa_counted_credits="18")
    assert StudentValidationRequest.model_validate(request).integration_context.total_reg_credits_source.timing == "end_of_semester"
    evidence["semester_complete"] = "true"
    with pytest.raises(ValidationError):
        StudentValidationRequest.model_validate(request)
