"""Hand-calculated checks for the isolated registration-history analysis."""
import importlib
import importlib.util

import pandas as pd
import pytest


@pytest.fixture
def analysis():
    name = "src.diagnostics.repeat_withdrawal_balance"
    assert importlib.util.find_spec(name) is not None, "Analysis implementation is missing"
    return importlib.import_module(name)


def rows(*values):
    return pd.DataFrame([
        dict(student_course_id=str(i), student_id="S", degree_id="D",
             course_id=course, part_id=part, course_credits=credits,
             register_status="R", finish_status=status)
        for i, (course, part, credits, status) in enumerate(values)
    ])


@pytest.mark.parametrize("status", ["F", "FE", "FA"])
def test_failed_repeated_and_not_repeated(analysis, status):
    history = rows(("A", 20241, 3, status), ("B", 20241, 2, status))
    target = rows(("A", 20242, 3, "P"), ("C", 20242, 4, "P"))
    result, classified = analysis.analyze_semesters(target, history)
    r = result.iloc[0]
    assert r.available_failed_courses == 2
    assert r.available_failed_credits == 5
    assert r.registered_failed_retake_credits == 3
    assert r.registered_new_credits == 4
    assert r.failed_retake_ratio == pytest.approx(3 / 7)
    assert r.failed_backlog_consumption_ratio == pytest.approx(3 / 5)
    assert classified.previous_status.tolist() == ["FAILED", "NEVER_TAKEN"]


def test_withdrawn_repeated_and_not_repeated(analysis):
    history = rows(("A", 20241, 3, "W"), ("B", 20241, 1, "W"))
    target = rows(("A", 20242, 3, "F"))
    result, _ = analysis.analyze_semesters(target, history)
    r = result.iloc[0]
    assert r.available_withdrawn_credits == 4
    assert r.registered_withdrawn_retake_credits == 3
    assert r.registered_failed_retake_credits == 0
    assert r.mix_type == "WITHDRAWN_RETAKE_ONLY"


def test_latest_previous_attempt_wins(analysis):
    history = rows(("A", 20231, 3, "F"), ("A", 20232, 3, "W"),
                   ("B", 20231, 2, "F"), ("B", 20232, 2, "P"))
    target = rows(("A", 20241, 3, "P"), ("B", 20241, 2, "P"))
    result, classified = analysis.analyze_semesters(target, history)
    assert classified.previous_status.tolist() == ["WITHDRAWN", "PASSED"]
    assert result.iloc[0].available_failed_credits == 0
    assert result.iloc[0].registered_other_previous_credits == 2


def test_current_and_future_outcomes_cannot_change_previous_status(analysis):
    past = rows(("A", 20241, 3, "F"))
    target = rows(("A", 20242, 3, "W"), ("B", 20242, 2, "P"))
    future = rows(("A", 20243, 3, "P"), ("B", 20243, 2, "F"))
    baseline, _ = analysis.analyze_semesters(target, past)
    augmented, audit = analysis.analyze_semesters(target, pd.concat([past, target, future], ignore_index=True).assign(student_course_id=lambda x: x.index.astype(str)))
    pd.testing.assert_frame_equal(baseline, augmented)
    assert audit.previous_part_id.dropna().lt(20242).all()


def test_decimal_and_zero_credit_courses_are_not_rounded(analysis):
    history = rows(("A", 20241, 4.5, "F"), ("Z", 20241, 0, "W"))
    target = rows(("A", 20242, 4.5, "P"), ("Z", 20242, 0, "P"), ("N", 20242, 1, "P"))
    result, _ = analysis.analyze_semesters(target, history)
    r = result.iloc[0]
    assert r.registered_failed_retake_credits == 4.5
    assert r.registered_withdrawn_retake_courses == 1
    assert r.semester_total_registered_credits == 5.5
    assert r.mix_type == "FAILED_WITHDRAWN_AND_NEW"


def test_exact_duplicates_are_reported_and_do_not_double_credits(analysis):
    target = rows(("N", 20241, 3, "P"))
    doubled = pd.concat([target, target], ignore_index=True)
    clean, removed = analysis.prepare_attempts(doubled)
    assert removed == 1
    result, _ = analysis.analyze_semesters(clean, clean.iloc[:0])
    assert result.iloc[0].semester_total_registered_credits == 3


def test_conflicting_same_semester_attempts_are_rejected(analysis):
    conflicting = rows(("A", 20241, 3, "F"), ("A", 20241, 3, "W"))
    with pytest.raises(ValueError, match="Ambiguous"):
        analysis.prepare_attempts(conflicting)


def test_unverified_and_missing_statuses_do_not_become_failed_or_new(analysis):
    history = rows(("A", 20241, 3, "X"), ("B", 20241, 2, None), ("C", 20241, 4, "I"))
    target = rows(("A", 20242, 3, "P"), ("B", 20242, 2, "P"), ("C", 20242, 4, "P"))
    result, audit = analysis.analyze_semesters(target, history)
    assert audit.previous_status.tolist() == ["UNRESOLVED", "UNKNOWN", "UNRESOLVED"]
    assert result.iloc[0].registered_new_credits == 0
    assert result.iloc[0].registered_other_previous_credits == 9


def test_status_precedes_mark_and_other_codes_are_separate(analysis):
    frame = rows(("A", 20241, 3, "FE"), ("B", 20241, 3, "W"), ("C", 20241, 3, "D"))
    frame["final_mark"] = [62, 0, 0]
    assert analysis.semantic_status(frame.finish_status).tolist() == ["FAILED", "WITHDRAWN", "OTHER"]


def test_no_history_in_observed_window_is_corrected_by_raw_prior(analysis):
    old = rows(("A", 20193, 2, "F"))
    target = rows(("A", 20201, 2, "P"))
    result, _ = analysis.analyze_semesters(target, old)
    assert result.iloc[0].registered_failed_retake_credits == 2
    assert result.iloc[0].registered_new_credits == 0


def test_available_credits_use_last_prior_not_current_credit_value(analysis):
    history = rows(("A", 20241, 2, "F"))
    target = rows(("A", 20242, 3, "P"))
    result, audit = analysis.analyze_semesters(target, history)
    assert result.iloc[0].available_failed_credits == 2
    assert result.iloc[0].failed_backlog_consumption_ratio == 1.5
    assert audit.iloc[0].previous_course_credits == 2


def test_student_totals_count_attempts_not_unique_courses(analysis):
    frame = rows(("A", 20241, 3, "F"), ("A", 20242, 3, "P"), ("B", 20242, 2, "W"))
    result = analysis.student_totals(frame).iloc[0]
    assert result.failed_course_count == 1
    assert result.passed_course_count == 1
    assert result.withdrawn_course_count == 1
    assert result.total_attempted_credits == 8
    assert result.failed_credit_ratio == pytest.approx(3 / 8)


def test_credit_bins_keep_decimal_other_values_visible(analysis):
    counts = analysis.credit_bins(pd.Series([0, 3, 4.5, 6, 9, 12, 13]))
    assert counts.set_index("bucket").loc["OTHER (<12)", "count"] == 1
    assert counts["count"].sum() == 7


def test_zero_load_ratios_remain_undefined(analysis):
    target = rows(("N", 20241, 0, "P"))
    result, _ = analysis.analyze_semesters(target, target.iloc[:0])
    assert pd.isna(result.iloc[0].new_credit_ratio)
    assert result.iloc[0].registered_new_courses == 1


def test_nonstandard_old_parts_are_explicit_sensitivity_only(analysis):
    old = rows(("A", 20164, 3, "F"))
    target = rows(("A", 20201, 3, "P"))
    with pytest.raises(ValueError, match="Invalid academic part"):
        analysis.analyze_semesters(target, old)
    result, _ = analysis.analyze_semesters(target, old, allow_nonstandard_history=True)
    assert result.iloc[0].registered_failed_retake_credits == 3
    with pytest.raises(ValueError, match="Invalid academic part"):
        analysis.analyze_semesters(old, old, allow_nonstandard_history=True)


def test_policy_components_use_separate_backlog_denominators(analysis):
    from src.diagnostics.repeat_withdrawal_report import policy_candidates
    history = rows(("F", 20241, 3, "F"), ("W", 20241, 3, "W"))
    target = rows(("F", 20242, 3, "P"), ("W", 20242, 3, "P"), ("N", 20242, 9, "P"))
    cases, _ = analysis.analyze_semesters(target, history)
    # 120 distinct students, each with the hand-calculated 3+3+9 / 15 mix.
    cases = pd.concat([cases.assign(student_id=f"S{i}") for i in range(120)], ignore_index=True)
    policy = policy_candidates(cases)
    assert policy["reference_students"] == 120
    assert policy["policies"][1]["failed_component"]["preferred_ratio"] == pytest.approx([.2, .2])
    assert policy["policies"][1]["withdrawn_component"]["preferred_ratio"] == pytest.approx([.2, .2])
    assert policy["policies"][1]["total_previous_component"]["preferred_ratio"] == pytest.approx([.4, .4])
    assert policy["policies"][1]["new_component"]["preferred_ratio_from_total_residual"] == pytest.approx([.6, .6])


def test_small_policy_reference_reports_insufficient_evidence(analysis):
    from src.diagnostics.repeat_withdrawal_report import policy_candidates
    target = rows(("A", 20242, 15, "P"))
    history = rows(("A", 20241, 15, "F"))
    cases, _ = analysis.analyze_semesters(target, history)
    policy = policy_candidates(cases)
    assert policy["evidence"] == "INSUFFICIENT EVIDENCE"
    assert policy["policies"] == []


def test_analysis_runner_preserves_inputs_and_rejects_existing_output(analysis, tmp_path, monkeypatch):
    import json
    import src.diagnostics.analyze_repeat_withdrawal_balance as runner
    target = rows(("A", 20242, 3, "P"), ("B", 20242, 12, "P"))
    raw = pd.concat([rows(("A", 20241, 3, "F"), ("B", 20164, 12, "W")), target], ignore_index=True)
    raw["student_course_id"] = raw.index.astype(str)
    target["student_course_id"] = ["2", "3"]
    raw["grade_id"] = "G"
    raw["final_mark"] = [40, 0, 70, 80]
    raw["points"] = [0, 0, 2.5, 3]
    data = tmp_path / "data"
    data.mkdir()
    roster_path, raw_path, grade_path = [data / name for name in ["roster.parquet", "raw.parquet", "grades.parquet"]]
    target.to_parquet(roster_path)
    raw.to_parquet(raw_path)
    pd.DataFrame([dict(grade_id="W", finish_status="W", grade_name_sl="منسحب")]).to_parquet(grade_path)
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps(dict(nodes=[], edges=[])), encoding="utf-8")
    for name, value in [("PROJECT_ROOT", tmp_path), ("CLEAN_REGISTRATION_ROSTER_PATH_V2", roster_path),
                        ("STUDENT_COURSE_PATH", raw_path), ("GRADE_SCALE_PATH", grade_path)]:
        monkeypatch.setattr(runner, name, value)
    original = {p: runner.sha256(p) for p in [roster_path, raw_path, grade_path]}
    output = tmp_path / "reports" / "analysis"
    runner.run(output, graph)
    assert {p: runner.sha256(p) for p in original} == original
    assert json.loads((output / "artifact_integrity.json").read_text())["unchanged"] is True
    cases = pd.read_csv(output / "student_semester_mix.csv")
    assert cases.iloc[0].registered_failed_retake_credits == 3
    assert cases.iloc[0].registered_new_credits == 12
    sensitivity = json.loads((output / "nonstandard_part_policy_sensitivity.json").read_text())
    assert sensitivity["source_rows"] == 1
    assert sensitivity["changed_registered_cases"] == 1
    with pytest.raises(FileExistsError):
        runner.run(output, graph)
