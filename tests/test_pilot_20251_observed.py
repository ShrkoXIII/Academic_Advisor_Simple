"""Actual target outcomes are a read-only display join, never prediction inputs."""
import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from tools.recommendation_pilot_20251.observed import ObservedPlanStore


STUDENT = {"sample_id": "sample-1", "student_id": "s", "degree_id": "d", "part_id": 20251}


def sources(tmp_path, roster=None, outcomes=None):
    registration = [dict(student_course_id="r1", student_id="s", degree_id="d", part_id=20251,
                         course_id="c1", course_credits=3, register_status="R", finish_status="F")]
    results = [dict(student_course_id="r1", student_id="s", degree_id="d", part_id=20251,
                    course_id="c1", course_credits=3, course_name_sl="اسم المادة", final_mark=0,
                    points=0, grade_id="g", grade_version_id="v", course_outcome_status="fail")]
    roster_path, outcome_path = tmp_path / "roster.parquet", tmp_path / "outcomes.parquet"
    pd.DataFrame(registration if roster is None else roster).to_parquet(roster_path, index=False)
    pd.DataFrame(results if outcomes is None else outcomes).to_parquet(outcome_path, index=False)
    return roster_path, outcome_path


def test_exact_identity_and_registration_attempt_join_preserves_real_zero(tmp_path):
    roster_path, outcome_path = sources(tmp_path)
    roster = pd.read_parquet(roster_path)
    other = roster.assign(student_course_id="other", degree_id="other-degree", course_id="not-selected")
    future = roster.assign(student_course_id="future", part_id=20252, course_id="future-course")
    pd.concat([roster, other, future], ignore_index=True).to_parquet(roster_path, index=False)
    store = ObservedPlanStore(roster_path, outcome_path)
    actual = store.get(STUDENT)
    assert actual["status"] == "AVAILABLE"
    assert actual["course_count"] == 1 and actual["total_credits"] == 3
    assert actual["graded_course_count"] == 1
    assert actual["courses"][0]["actual_mark"] == 0
    assert actual["courses"][0]["actual_points"] == 0
    assert actual["courses"][0]["course_name"] == "اسم المادة"
    assert actual["part_id"] == 20251 and actual["degree_id"] == "d"
    assert actual["source"]["join_key"] == "student_course_id + student_id + degree_id + part_id + course_id + course_credits"
    assert actual["source"]["used_for_prediction"] is False
    assert len(actual["source"]["roster_sha256"]) == 64


def test_ungraded_registration_remains_in_actual_plan_without_zero_imputation(tmp_path):
    roster_path, outcome_path = sources(tmp_path)
    roster = pd.read_parquet(roster_path)
    extra = roster.assign(student_course_id="r2", course_id="c2", finish_status="W", course_credits=2)
    pd.concat([roster, extra], ignore_index=True).to_parquet(roster_path, index=False)
    actual = ObservedPlanStore(roster_path, outcome_path).get(STUDENT)
    assert actual["status"] == "PARTIAL"
    assert actual["course_count"] == 2 and actual["total_credits"] == 5
    assert actual["graded_course_count"] == 1
    ungraded = next(c for c in actual["courses"] if c["course_id"] == "c2")
    assert ungraded["actual_mark"] is None and ungraded["actual_points"] is None
    assert ungraded["result_status"] == "NO_FINAL_RESULT"
    assert ungraded["finish_status"] == "W"


def test_duplicate_course_registration_is_explicitly_unavailable(tmp_path):
    roster_path, outcome_path = sources(tmp_path)
    roster = pd.read_parquet(roster_path)
    pd.concat([roster, roster.assign(student_course_id="second-attempt")]).to_parquet(roster_path, index=False)
    actual = ObservedPlanStore(roster_path, outcome_path).get(STUDENT)
    assert actual["status"] == "UNAVAILABLE"
    assert actual["reason"] == "AMBIGUOUS_REGISTRATION"
    assert actual["courses"] == []


@pytest.mark.parametrize("change,reason", [
    ({"student_course_id": "different-attempt"}, "NO_FINAL_RESULT"),
    ({"course_id": "different-course"}, "OUTCOME_IDENTITY_MISMATCH"),
    ({"course_credits": 4}, "OUTCOME_IDENTITY_MISMATCH"),
    ({"degree_id": "other-degree"}, "NO_FINAL_RESULT"),
    ({"final_mark": 101}, "INVALID_FINAL_MARK"),
])
def test_mismatched_or_invalid_outcome_does_not_become_an_actual_grade(tmp_path, change, reason):
    roster_path, outcome_path = sources(tmp_path)
    pd.read_parquet(outcome_path).assign(**change).to_parquet(outcome_path, index=False)
    actual = ObservedPlanStore(roster_path, outcome_path).get(STUDENT)
    assert actual["status"] == "PARTIAL" and actual["course_count"] == 1
    assert actual["courses"][0]["actual_mark"] is None
    assert actual["courses"][0]["result_status"] == reason


def test_duplicate_outcomes_are_not_arbitrarily_selected(tmp_path):
    roster_path, outcome_path = sources(tmp_path)
    results = pd.read_parquet(outcome_path)
    pd.concat([results, results.assign(final_mark=90)]).to_parquet(outcome_path, index=False)
    actual = ObservedPlanStore(roster_path, outcome_path).get(STUDENT)
    assert actual["status"] == "PARTIAL"
    assert actual["courses"][0]["actual_mark"] is None
    assert actual["courses"][0]["result_status"] == "AMBIGUOUS_FINAL_RESULT"


def test_missing_sources_do_not_block_registration_display_or_fake_an_empty_plan(tmp_path):
    roster_path, outcome_path = sources(tmp_path)
    without_marks = ObservedPlanStore(roster_path, tmp_path / "missing.parquet").get(STUDENT)
    assert without_marks["status"] == "PARTIAL" and without_marks["course_count"] == 1
    assert without_marks["courses"][0]["actual_mark"] is None
    without_roster = ObservedPlanStore(tmp_path / "missing.parquet", outcome_path).get(STUDENT)
    assert without_roster["status"] == "UNAVAILABLE" and without_roster["course_count"] is None
    no_student = ObservedPlanStore(roster_path, outcome_path).get({**STUDENT, "student_id": "absent"})
    assert no_student["status"] == "UNAVAILABLE" and no_student["reason"] == "NO_REGISTRATION_RECORD"


@pytest.mark.parametrize("source_error", [False, True])
def test_saved_run_enrichment_does_not_rewrite_results_or_forward_actual_outcomes(tmp_path, source_error):
    from tools.recommendation_pilot_20251.app import create_app
    from tools.recommendation_pilot_20251.runner import RunStore

    (tmp_path / "students.csv").write_text(
        "sample_id,role,student_id,degree_id,part_id,previous_gpa,gpa_category\n"
        "sample-1,primary,s,d,20251,2,mid\n", encoding="utf-8")
    roster_path, outcome_path = sources(tmp_path)
    store = RunStore(tmp_path / "experiments")
    result = {"sample_id": "sample-1", "student_id": "s", "experiments": {}}
    store.save("run_observed", {"part_id": 20251}, [result], {})
    path = store.root / "run_observed" / "student_results.json"
    original = path.read_bytes()
    class BrokenObservedStore:
        def get(self, student):
            raise ValueError("private display-source error must not hide predictions or escape")

    class RecordingPredictor:
        def __init__(self):
            self.seen = []

        def predict(self, student, registrations):
            self.seen.append(registrations)
            return {"status": "PREDICTION_AVAILABLE", "context": "actual_registered_plan", "experiments": {}}

    predictor = RecordingPredictor()
    app = create_app(tmp_path, observed_store=BrokenObservedStore() if source_error else ObservedPlanStore(roster_path, outcome_path),
                     observed_predictor=predictor)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        saved = client.get("/api/runs/run_observed").json()
        actual = saved["student_results"][0]["observed_plan"]
        if source_error:
            assert actual["status"] == "UNAVAILABLE"
            assert "private display-source" not in json.dumps(saved)
        else:
            assert actual["courses"][0]["actual_mark"] == 0
            assert predictor.seen == [[{"course_id": "c1", "course_credits": 3.0}]]
            assert saved["student_results"][0]["observed_plan_prediction"]["context"] == "actual_registered_plan"
        assert saved["student_results"][0]["experiments"] == {}
        assert client.get("/api/students").json()["students"][0].get("observed_plan") is None
    assert path.read_bytes() == original
    assert json.loads(original)[0].get("observed_plan") is None
    assert json.loads(original)[0].get("observed_plan_prediction") is None
    if source_error:
        assert predictor.seen == []
