"""Synthetic contracts for API ownership, ordering, and partial diagnostics."""
from copy import deepcopy
from decimal import Decimal
import importlib

import pandas as pd
import pytest


def course_request():
    identity = {"student_id": "S", "degree_id": "D", "part_id": 20251}
    row = {"COURSE_ID": "C", "COURSE_NAME_SL": "Synthetic course", "COURSE_CREDITS": "3",
           "ATTEMPTS_COUNT": 0, "REQUIREMENT_TYPE_ID": "R", "REQUIREMENT_ID": "G",
           "CREDITS_COUNT": "12", "REQUIREMENT_PASSED_CREDITS": "6", "YEAR_ORDER": 1,
           "SEMESTER_ORDER": 1, "IS_REQUESTABLE": "Y", "ALLOW_REGISTER": "Y",
           "STATUS_REASON_CODE": "REQUESTABLE", "FINISH_STATUS": None}
    return {**identity, "source_contexts": {"courses": dict(identity)},
            "courses_api_response": {"success": True, "data": {
                "availableCourses": [row], "allowRegisterAllOptional": "N", "registserRule": {
                    "LOAD_TYPE": "CREDIT", "MIN_CREDITS": "0", "MAX_CREDITS": "18",
                    "MIN_STUDY_CREDITS": "0", "MAX_STUDY_CREDITS": "18",
                    "GRAD_MIN_LIMIT": "0", "GRAD_MAX_LOAD": "18"}}},
            "integration_context": {"registration_policy": {
                "source": "synthetic_policy", "part_id": 20251, "attempts_scope_confirmed": True,
                "load_profile": "study", "requirement_group_modes": {"G": "strict_remaining"}}}}


def course_rows(request):
    return request["courses_api_response"]["data"]["availableCourses"]


def course_catalog(request):
    return pd.DataFrame([{"degree_id": "D", "course_id": row["COURSE_ID"], "course_type_id": "T",
                          "requirement_type_id": row["REQUIREMENT_TYPE_ID"],
                          "course_credits": row["COURSE_CREDITS"], "credits_count": row["CREDITS_COUNT"],
                          "year_order": row["YEAR_ORDER"], "semester_order": row["SEMESTER_ORDER"]}
                         for row in course_rows(request)]).drop_duplicates("course_id")


def courses(request, *, catalog=True):
    adapter = importlib.import_module("src.api.adapters.courses")
    return adapter.adapt_courses(request, catalog=course_catalog(request) if catalog else None)


@pytest.mark.parametrize("legacy,canonical,names", [
    ("courses_adapter", "adapters.courses", ("adapt_courses", "group_identity", "_course")),
    ("courses_adapter", "validators.courses", ("_check_source_duplicates", "_rules")),
    ("history_adapter", "adapters.history", ("adapt_history_delta",)),
])
def test_legacy_helpers_reexport_canonical_implementations(legacy, canonical, names):
    old = importlib.import_module("src.api." + legacy)
    new = importlib.import_module("src.api." + canonical)
    for name in names:
        assert getattr(old, name) is getattr(new, name)


def test_course_mapping_preserves_exact_values_and_nullable_rule():
    result = courses(course_request())
    assert result.public() == {
        "validation_status": "valid", "validation_completed": True, "errors": [],
        "checks": {"identity": "php_attested", "catalog": "verified"}, "unavailable_fields": [],
        "summary": {"source_count": 1, "candidate_count": 1, "rejected_count": 0, "duplicate_count": 0}}
    assert result.normalized["candidates"] == [{
        "course_id": "C", "course_name": "Synthetic course", "course_credits": Decimal("3"),
        "attempt_number": 1, "plan_requirement_type_id": "R", "plan_year_order": 1,
        "plan_semester_order": 1, "plan_credits_count": Decimal("12"),
        "requirement_group_id": '["D","G"]', "previous_course_status": "NEW", "plan_course_type_id": "T"}]
    assert result.normalized["requirement_group_policies"] == {'["D","G"]': Decimal("6")}
    assert result.normalized["registration_rules"]["MAX_NEW_COURSES"] is None


def test_missing_catalog_retains_partial_candidate_diagnostics():
    result = courses(course_request(), catalog=False)
    assert result.status == "partial" and result.errors == []
    assert result.normalized["candidates"][0]["plan_course_type_id"] is None
    assert result.checks == {"identity": "php_attested", "catalog": "unavailable"}
    assert result.unavailable_fields == ["plan_course_type_id"]


@pytest.mark.parametrize("failure", ["identity", "numeric", "duplicate"])
def test_ineligible_rows_cannot_hide_source_errors(failure):
    request = course_request()
    row = course_rows(request)[0]
    if failure == "identity":
        row.update(STUDENT_ID="other", ALLOW_REGISTER="N")
        code, status = "IDENTITY_MISMATCH", 422
    elif failure == "numeric":
        row.update(ATTEMPTS_COUNT="1.5", ALLOW_REGISTER="N")
        code, status = "INVALID_NUMBER", 422
    else:
        course_rows(request).append(dict(row, ALLOW_REGISTER="N"))
        code, status = "CONFLICTING_DUPLICATE", 409
    result = courses(request)
    assert result.errors[0]["code"] == code
    assert result.http_status == status and result.normalized is None


def test_failed_course_keeps_group_consistency_before_later_rows():
    request = course_request()
    first = course_rows(request)[0]
    second = dict(first, COURSE_ID="C2", CREDITS_COUNT="13")
    first["COURSE_NAME_SL"] = ""
    course_rows(request).append(second)
    result = courses(request)
    assert [error["code"] for error in result.errors] == ["MISSING_FIELD", "CONFLICTING_GROUP"]
    assert result.normalized["candidates"] == [] and result.summary["candidate_count"] == 0


def test_reason_error_precedes_fatal_temporal_status_error():
    request = course_request()
    course_rows(request)[0].update(ATTEMPTS_COUNT=1, STATUS_REASON_CODE="UNRESOLVED",
                                   FINISH_STATUS="F", LAST_REGISTER_SEMESTER_ID=20251)
    result = courses(request)
    assert [error["code"] for error in result.errors] == ["UNRESOLVED_REASON", "FUTURE_SOURCE"]
    assert result.normalized["candidates"] == []


@pytest.mark.parametrize("mode,expected", [("strict_remaining", "0.2"), ("approved_overflow", "0.4")])
def test_group_credit_arithmetic_preserves_decimal_precision(mode, expected):
    request = course_request()
    course_rows(request)[0].update(COURSE_CREDITS="0.2", CREDITS_COUNT="0.3", REQUIREMENT_PASSED_CREDITS="0.1")
    policy = request["integration_context"]["registration_policy"]
    policy.update(requirement_group_modes={"G": mode}, group_overflow_credits={"G": "0.2"})
    result = courses(request)
    assert result.errors == []
    assert result.normalized["requirement_group_policies"] == {'["D","G"]': Decimal(expected)}


def test_late_rule_failure_retains_candidate_summary_without_normalized_output():
    request = course_request()
    request["courses_api_response"]["data"]["registserRule"]["MIN_CREDITS"] = "19"
    result = courses(request)
    assert [error["code"] for error in result.errors] == ["CONFLICTING_RULES"]
    assert result.normalized is None and result.summary["candidate_count"] == 1
    assert result.checks == {"identity": "php_attested", "catalog": "verified"}


def history_request(*, finalized=True):
    request = {"part_id": 20252, "rows": []}
    if finalized:
        request["finalization"] = {"finalized_part_id": 20252, "approval_reference": "synthetic-approval"}
    return request


class PreviewManager:
    def __init__(self, *, conflict=False):
        self.calls = []
        self.conflict = conflict

    def preview_delta(self, *, history_payload):
        self.calls.append(deepcopy(history_payload))
        if self.conflict:
            raise ValueError("synthetic private lineage details")
        return {"status": "new_delta", "history_as_of_part": 20251, "base_history_sha256": "a" * 64}


def history(request, manager=None):
    return importlib.import_module("src.api.adapters.history").adapt_history_delta(request, manager=manager)


def test_history_preview_preserves_payload_and_never_claims_publication():
    manager = PreviewManager()
    result = history(history_request(), manager)
    assert result.status == "valid" and result.errors == []
    assert result.checks == {"aggregates": "verified", "lineage": "verified", "finalization": "admin_attested"}
    assert manager.calls == [{"delta_part": 20252, "aggregates": [], "finalized": True}]
    assert result.summary["published"] is False and result.summary["activated"] is False
    assert result.summary["row_count"] == 0 and result.summary["delta_sha256"] == result.normalized.delta_sha256


def test_history_finalization_failure_retains_prior_aggregate_check():
    request = history_request()
    request["finalization"]["finalized_part_id"] = 20253
    manager = PreviewManager()
    result = history(request, manager)
    assert [error["code"] for error in result.errors] == ["FINALIZATION_CONFLICT"]
    assert result.checks == {"aggregates": "verified", "lineage": "unavailable", "finalization": "unavailable"}
    assert result.normalized is None and result.summary == {} and manager.calls == []


def test_history_preview_conflict_retains_normalized_delta_and_safe_summary():
    result = history(history_request(), PreviewManager(conflict=True))
    assert result.http_status == 409 and result.status == "invalid"
    assert result.errors == [{"code": "DELTA_CONFLICT",
                             "message": "Delta conflicts with recorded lineage or semester order.", "component": "input"}]
    assert result.normalized is not None and result.summary["row_count"] == 0
    assert result.checks == {"aggregates": "verified", "lineage": "unavailable", "finalization": "admin_attested"}


def test_history_without_proof_stays_partial_after_lineage_preview():
    manager = PreviewManager()
    result = history(history_request(finalized=False), manager)
    assert result.status == "partial" and result.errors == []
    assert result.checks["finalization"] == "unavailable"
    assert manager.calls == [{"delta_part": 20252, "aggregates": []}]
