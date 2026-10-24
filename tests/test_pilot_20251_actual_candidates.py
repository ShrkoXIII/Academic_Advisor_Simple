"""Diagnostic augmentation must keep outcomes and archived API rows separate."""
from copy import deepcopy
import importlib
import json

import pandas as pd
import pytest


def augment(*args, **kwargs):
    return importlib.import_module("tools.recommendation_pilot_20251.actual_candidates").augment_candidates(*args, **kwargs)


@pytest.fixture
def inputs():
    original = pd.DataFrame([{"course_id": "10.0", "course_credits": 3., "attempt_number": 1,
        "plan_course_type_id": "1", "plan_requirement_type_id": "2", "plan_year_order": 1.,
        "plan_semester_order": 1., "plan_credits_count": 12., "course_name": "API course"}])
    student = {"student_id": "S", "degree_id": "20.0", "part_id": 20251}
    catalog = pd.DataFrame([{"degree_id": "20", "course_id": course, "course_credits": 3.,
        "course_type_id": "1", "requirement_type_id": 2, "year_order": 1,
        "semester_order": 1, "credits_count": 12., "course_name_sl": "Catalog " + course}
        for course in ["10", "11", "12"]])
    history = pd.DataFrame({"student_id": ["S", "S", "S", "S", "X"],
        "degree_id": ["other", "20", "20", "20", "20"], "course_id": ["11"] * 5,
        "part_id": [20242, 20243, 20251, 20252, 20243], "attempt_number": [1, 2, 99, 200, 50]})
    return original, student, catalog, history


def test_missing_actual_is_added_once_and_existing_numeric_id_is_not_duplicated(inputs):
    original, student, catalog, history = inputs
    registrations = [{"course_id": "010", "course_credits": 3},
                     {"course_id": "11.00", "course_credits": 3}, {"course_id": 11, "course_credits": 3}]
    result, report = augment(original, student, registrations, catalog, history)
    assert result.course_id.tolist() == ["10.0", "11"]
    assert result.attempt_number.tolist() == [1, 3]
    assert report["actual_course_count"] == 2
    assert report["injected_course_ids"] == ["11"]
    assert report["candidate_coverage_before"] == .5
    assert report["candidate_coverage_after"] == 1.


def test_original_prefix_and_all_inputs_are_unchanged_and_provenance_is_sidecar(inputs):
    original, student, catalog, history = inputs
    snapshots = [frame.copy(deep=True) for frame in (original, catalog, history)]
    registrations = [{"course_id": "12", "course_credits": 3}]
    registration_copy = deepcopy(registrations)
    result, report = augment(original, student, registrations, catalog, history,
        catalog_source={"path": "catalog.parquet", "sha256": "catalog-hash"},
        history_source={"path": "prior.parquet", "sha256": "history-hash"})
    pd.testing.assert_frame_equal(result.iloc[:1].reset_index(drop=True), original, check_dtype=False)
    for frame, snapshot in zip((original, catalog, history), snapshots):
        pd.testing.assert_frame_equal(frame, snapshot)
    assert registrations == registration_copy
    assert "candidate_source" not in result
    assert report["candidate_provenance"]["10"]["candidate_source"] == "API"
    injected = report["candidate_provenance"]["12"]
    assert injected["candidate_source"] == "ACTUAL_INJECTED"
    assert injected["historical_eligibility_unverified"] is True
    assert injected["official_requestability"] == "UNVERIFIED"
    assert injected["catalog_temporal_validity"] == "UNVERIFIED"
    assert set(injected["field_sources"]) == set(result.columns)
    assert injected["field_sources"]["course_credits"]["catalog_source"]["sha256"] == "catalog-hash"
    assert injected["field_sources"]["attempt_number"]["history_source"]["sha256"] == "history-hash"


def test_target_outcomes_are_allowlisted_out_and_cannot_change_candidates(inputs):
    original, student, catalog, history = inputs
    first = [{"course_id": "11", "course_credits": 3, "final_mark": 0,
              "actual_mark": 0, "finish_status": "F", "attempt_number": 999, "points": 0}]
    second = [{"course_id": "11", "course_credits": 3, "final_mark": 100,
               "actual_mark": 100, "finish_status": "S", "attempt_number": 1000, "points": 4}]
    a, report_a = augment(original, student, first, catalog, history)
    b, report_b = augment(original, student, second, catalog, history)
    pd.testing.assert_frame_equal(a, b)
    assert report_a == report_b
    assert not {"final_mark", "actual_mark", "finish_status", "points", "grade_id"} & set(a)
    assert report_a["target_outcomes_used"] is False
    assert a.loc[a.course_id.eq("11"), "attempt_number"].item() == 3


def test_injected_courses_have_stable_normalized_id_order_without_resorting_api(inputs):
    original, student, catalog, history = inputs
    a, report = augment(original, student, [{"course_id": "12", "course_credits": 3},
        {"course_id": "11", "course_credits": 3}], catalog, history)
    b, _ = augment(original, student, [{"course_id": "11.0", "course_credits": 3},
        {"course_id": "012", "course_credits": 3}], catalog, history)
    assert a.course_id.tolist() == ["10.0", "11", "12"]
    pd.testing.assert_frame_equal(a, b)


@pytest.mark.parametrize("mutation,reason", [
    ("missing", "CATALOG_COURSE_MISSING"),
    ("duplicate", "CATALOG_COURSE_AMBIGUOUS"),
    ("credits", "CATALOG_CREDIT_CONFLICT"),
    ("structure", "CATALOG_STRUCTURE_INVALID"),
    ("history", "ATTEMPT_HISTORY_INVALID"),
])
def test_unproven_structure_or_history_is_rejected_with_reason_and_other_rows_survive(inputs, mutation, reason):
    original, student, catalog, history = inputs
    if mutation == "missing":
        catalog = catalog.loc[catalog.course_id.ne("11")]
    elif mutation == "duplicate":
        catalog = pd.concat([catalog, catalog.loc[catalog.course_id.eq("11")]])
    elif mutation == "credits":
        catalog.loc[catalog.course_id.eq("11"), "course_credits"] = 4
    elif mutation == "structure":
        catalog.loc[catalog.course_id.eq("11"), "requirement_type_id"] = None
    else:
        history.loc[history.part_id.eq(20243) & history.student_id.eq("S"), "attempt_number"] = None
    result, report = augment(original, student, [{"course_id": "11", "course_credits": 3},
        {"course_id": "12", "course_credits": 3}], catalog, history)
    assert result.course_id.tolist() == ["10.0", "12"]
    assert report["rejected_courses"] == [{"course_id": "11", "reason": reason}]
    assert report["actual_courses_in_augmented_candidates"] == 1
    assert report["candidate_coverage_after"] == .5


def test_missing_history_source_does_not_fabricate_first_attempt(inputs):
    original, student, catalog, history = inputs
    result, report = augment(original, student, [{"course_id": "12", "course_credits": 3}],
        catalog, history.drop(columns="part_id"))
    assert len(result) == len(original)
    assert report["rejected_courses"][0]["reason"] == "ATTEMPT_HISTORY_INVALID"


def test_fractional_target_and_unknown_history_course_cannot_be_silently_accepted(inputs):
    original, student, catalog, history = inputs
    with pytest.raises(ValueError):
        augment(original, {**student, "part_id": 20251.5}, [{"course_id": "12", "course_credits": 3}], catalog, history)
    history.loc[history.student_id.eq("S") & history.part_id.eq(20243), "course_id"] = None
    result, report = augment(original, student, [{"course_id": "12", "course_credits": 3}], catalog, history)
    assert len(result) == len(original)
    assert report["rejected_courses"][0]["reason"] == "ATTEMPT_HISTORY_INVALID"


def test_valid_empty_prior_history_proves_first_cleaned_attempt_and_other_degree_attempts_count(inputs):
    original, student, catalog, history = inputs
    history = history.loc[history.degree_id.eq("other")]
    result, report = augment(original, student, [{"course_id": "11", "course_credits": 3},
        {"course_id": "12", "course_credits": 3}], catalog, history)
    assert result.attempt_number.tolist() == [1, 2, 1]
    assert report["history_latest_part"] == 20242


def test_conflicting_duplicate_actual_credits_are_rejected_without_overriding_catalog(inputs):
    original, student, catalog, history = inputs
    result, report = augment(original, student, [{"course_id": "11", "course_credits": 3},
        {"course_id": "11.0", "course_credits": 4}], catalog, history)
    assert result.course_id.tolist() == ["10.0"]
    assert report["rejected_courses"] == [{"course_id": "11", "reason": "ACTUAL_REGISTRATION_CREDIT_CONFLICT"}]


def test_raw_api_actual_rejected_by_existing_policy_is_never_reintroduced(inputs):
    original, student, catalog, history = inputs
    result, report = augment(original, student, [{"course_id": "11", "course_credits": 3},
        {"course_id": "12", "course_credits": 3}], catalog, history,
        original_api_course_ids=["10.00", "11.0"])
    assert result.course_id.tolist() == ["10.0", "12"]
    assert report["injected_course_ids"] == ["12"]
    assert report["actual_courses_excluded_by_original_policy"] == ["11"]
    assert report["original_candidate_count"] == 2
    assert report["augmented_candidate_count"] == 3
    assert report["original_model_candidate_count"] == 1
    assert report["augmented_model_candidate_count"] == 2
    assert report["candidate_coverage_before"] == .5
    assert report["candidate_coverage_after"] == 1.
    assert report["model_candidate_coverage_before"] == 0.
    assert report["model_candidate_coverage_after"] == .5


def test_nonfinite_float_conversion_cannot_reach_predictor(inputs):
    original, student, catalog, history = inputs
    catalog["course_credits"] = catalog.course_credits.astype(object)
    catalog.loc[catalog.course_id.eq("11"), "course_credits"] = "1e1000"
    result, report = augment(original, student, [{"course_id": "11", "course_credits": "1e1000"}], catalog, history)
    assert result.course_id.tolist() == ["10.0"]
    assert report["rejected_courses"][0]["reason"] in {"ACTUAL_REGISTRATION_CREDIT_CONFLICT", "CATALOG_STRUCTURE_INVALID"}
    json.dumps(report, allow_nan=False)


def test_sources_are_read_only_fingerprinted_and_history_is_strictly_prior(inputs, tmp_path):
    _, _, catalog, history = inputs
    catalog_path, history_path = tmp_path / "catalog.parquet", tmp_path / "history.parquet"
    catalog.to_parquet(catalog_path)
    history.to_parquet(history_path)
    original_bytes = [path.read_bytes() for path in (catalog_path, history_path)]
    module = importlib.import_module("tools.recommendation_pilot_20251.actual_candidates")
    sources = module.ActualCandidateSources(catalog_path=catalog_path, history_path=history_path)
    read_catalog, read_history = sources.load()
    assert read_history.part_id.tolist() == [20242, 20243, 20243]
    assert len(read_catalog) == 3
    assert all(len(sources.metadata[name]["sha256"]) == 64 for name in ("catalog_source", "history_source"))
    assert sources.metadata["history_as_of_part"] == 20243
    assert [path.read_bytes() for path in (catalog_path, history_path)] == original_bytes
    json.dumps(sources.metadata, allow_nan=False)
