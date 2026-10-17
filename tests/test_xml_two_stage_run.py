import pytest

from src.recommendation_experiments.xml_two_stage_run import (
    enrich_observed, summarize_run, verify_case_pair, stage_completed, prepare_case_frames,
    load_selected_cases,
)


def test_observed_errors_keep_full_roster_and_policy_aligned_gpa_separate():
    actual = dict(actual_plan_gpa=2, actual_published_end_cumulative_gpa=2.5,
                  gpa_bearing_credits=3, courses=[
                      dict(course_id="a", course_credits=3, actual_points=2, gpa_included=True),
                      dict(course_id="b", course_credits=3, actual_points=None, gpa_included=False),
                  ], warnings=[])
    predicted = dict(expected_plan_gpa=3, projected_cumulative_gpa=2.6,
                     projected_gpa_requires_repeat_policy=False, courses=[
                         dict(course_id="a", expected_points=2.5, predicted_mark=70),
                         dict(course_id="b", expected_points=3.5, predicted_mark=90),
                     ])
    result = enrich_observed(actual, predicted)
    assert result["plan_gpa_error"] == 1
    assert result["absolute_plan_gpa_error"] == 1
    assert result["predicted_actual_gpa_bearing_plan_gpa"] == 2.5
    assert result["policy_aligned_plan_gpa_error"] == 0.5
    assert result["courses"][0]["points_error"] == 0.5
    assert result["courses"][1]["points_error"] is None
    assert result["cumulative_gpa_error"] == pytest.approx(0.1)


def test_summary_averages_actual_plan_error_even_when_no_recommended_plan():
    empty = dict(status="no_feasible_18_credit_plan", recommendations=[],
                 counts=dict(generated=0, scored47=0), timings=dict(total_seconds=0.01))
    cases = [dict(experiment_01=empty, experiment_02=empty,
                  observed=dict(status="ok", absolute_plan_gpa_error=0.25,
                                policy_aligned_absolute_plan_gpa_error=0.2))]
    summary = summarize_run(cases)
    assert summary["requested_students"] == 10
    assert summary["selected_students"] == 1
    assert summary["experiment_01_successful"] == 0
    assert summary["actual_plan_mae"] == 0.25
    assert summary["policy_aligned_actual_plan_mae"] == 0.2


def test_identical_available_top_lists_with_fewer_than_three_plans():
    result = dict(status="ok", recommendations=[dict(course_ids=["a"], projected_cumulative_gpa=3)],
                  counts=dict(generated=1, scored47=1), timings=dict(total_seconds=1))
    case = dict(experiment_01=result, experiment_02=result, comparison=dict(top_1_match=True, top_3_overlap=1))
    assert summarize_run([case])["identical_top3_students"] == 1


def test_pair_verification_rejects_different_exhaustive_search_identity():
    a = dict(status="ok", counts=dict(generated=1), diagnostics=dict(plan_identity_sha256="a"), recommendations=[])
    b = dict(status="ok", counts=dict(generated=1), diagnostics=dict(plan_identity_sha256="b"), recommendations=[], shortlist=[])
    with pytest.raises(ValueError, match="identity"):
        verify_case_pair(dict(experiment_01=a, experiment_02=b))


def test_missing_mandatory_observed_prediction_keeps_stage_incomplete():
    case = dict(experiment_01=dict(status="ok"), observed=dict(status="prediction_unavailable"))
    assert stage_completed([case] * 10, "experiment_01") is False


def test_selected_case_manifest_ignores_orphan_directories(tmp_path):
    import json
    selected = tmp_path / "students" / "selected"
    selected.mkdir(parents=True)
    (selected / "case.json").write_text(json.dumps(dict(case_id="selected")))
    (tmp_path / "students" / "orphan").mkdir()
    assert load_selected_cases(tmp_path, {"selected_files": [{"case_id": "selected"}]}) == [dict(case_id="selected")]


def test_observed_normalization_failure_writes_no_orphan_directory(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import pandas as pd
    from src.recommendation_experiments import xml_two_stage_run as runner
    case = SimpleNamespace(snapshot={}, candidates=pd.DataFrame(), actual_raw=pd.DataFrame([
        dict(course_id="x", course_credits=3, course_name_sl="X")]),
        payload=dict(student_id="s", degree_id="d", target_part=20251, input_audit={}))
    engine = SimpleNamespace(prepare_candidates=lambda *a: pd.DataFrame())
    def reject(*a):
        raise ValueError("observed catalog conflict")
    monkeypatch.setattr(runner, "normalize_candidates", reject)
    target = tmp_path / "student"
    with pytest.raises(ValueError, match="catalog"):
        prepare_case_frames(case, engine, {"catalog": None, "history": None}, target)
    assert not target.exists()
