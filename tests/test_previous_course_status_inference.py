"""Focused checks for isolated status experiment inference comparisons."""

import importlib

import numpy as np
import pandas as pd
import pytest


def inference():
    return importlib.import_module("src.recommendation_experiments.previous_course_status_inference")


def test_course_comparison_joins_by_course_identity_and_keeps_status():
    baseline = pd.DataFrame({
        "course_id": ["B", "A"], "course_credits": [2, 3],
        "attempt_number": [2, 1],
        "previous_course_status": ["FAILED", "NEVER_TAKEN"],
        "predicted_mark": [48.0, 72.0],
        "fail_probability": [0.6, 0.1],
    })
    augmented = pd.DataFrame({
        "course_id": ["A", "B"], "course_credits": [3, 2],
        "attempt_number": [1, 2],
        "previous_course_status": ["NEVER_TAKEN", "FAILED"],
        "predicted_mark": [74.0, 54.0],
        "fail_probability": [0.08, 0.4],
    })

    paired = inference().pair_course_scores(baseline, augmented)

    assert paired.course_id.tolist() == ["B", "A"]
    assert paired.previous_course_status.tolist() == ["FAILED", "NEVER_TAKEN"]
    assert paired.attempt_number.tolist() == [2, 1]
    assert paired.credits.tolist() == [2, 3]
    assert paired.predicted_mark_delta_34_minus_33.tolist() == [6.0, 2.0]
    assert paired.fail_probability_delta_34_minus_33.tolist() == pytest.approx([-0.2, -0.02])


def test_course_comparison_rejects_mismatched_candidate_rows():
    baseline = pd.DataFrame({
        "course_id": ["A"], "course_credits": [3], "attempt_number": [1],
        "previous_course_status": ["NEVER_TAKEN"], "predicted_mark": [70.0],
        "fail_probability": [0.1],
    })
    augmented = baseline.assign(course_credits=4)

    with pytest.raises(ValueError, match="identical candidate rows"):
        inference().pair_course_scores(baseline, augmented)


def test_unresolved_prior_attempt_is_unknown_in_serving_rows():
    targets = pd.DataFrame({
        "student_id": ["S"], "course_id": ["A"], "part_id": [20251],
    })
    history = pd.DataFrame({
        "student_id": ["S"], "course_id": ["A"], "part_id": [20243],
        "final_mark": [np.nan], "withdrawn": [False], "unresolved": [True],
    })

    result = inference()._attach_status(targets, history)

    assert result.previous_course_status.tolist() == ["__UNKNOWN__"]


def test_plan_comparison_uses_same_memberships_and_reports_rank_changes():
    membership = pd.DataFrame({
        "plan_id": [10, 10, 20, 20, 30, 40],
        "course_id": ["A", "B", "A", "C", "D", "E"],
    })
    baseline = pd.DataFrame({
        "plan_id": [10, 20, 30, 40],
        "projected_cumulative_gpa": [3.40, 3.30, 3.20, 3.10],
        "expected_plan_gpa": [3.8, 3.6, 3.4, 3.2],
        "expected_failed_credits": [0.1, 0.2, 0.3, 0.4],
    })
    augmented = pd.DataFrame({
        "plan_id": [40, 20, 10, 30],
        "projected_cumulative_gpa": [3.45, 3.35, 3.25, 3.15],
        "expected_plan_gpa": [3.9, 3.7, 3.5, 3.3],
        "expected_failed_credits": [0.1, 0.2, 0.3, 0.4],
    })

    paired, summary = inference().pair_plan_summaries(baseline, augmented, membership)

    assert paired.plan_id.tolist() == [10, 20, 30, 40]
    assert paired.loc[paired.plan_id.eq(10), "course_ids"].iloc[0] == "A|B"
    assert paired.rank_47.tolist() == [1, 2, 3, 4]
    assert paired.rank_48.tolist() == [3, 2, 4, 1]
    assert paired.projected_gpa_delta_48_minus_47.tolist() == pytest.approx([-0.15, 0.05, -0.05, 0.35])
    assert summary["top3_order_changed"] is True
    assert summary["top3_membership_changed"] is True
    assert summary["plans_with_rank_change"] == 3
    assert summary["top3_47"] == [["A", "B"], ["A", "C"], ["D"]]
    assert summary["top3_48"] == [["E"], ["A", "C"], ["A", "B"]]


def test_augmented_scoring_clips_predictions_before_grade_conversion(monkeypatch):
    module = inference()
    rows = pd.DataFrame({"course_id": ["A", "B"], "grade_version_id": ["v", "v"],
                         "previous_course_status": ["FAILED", "NEVER_TAKEN"]})

    class Model:
        def __init__(self, values):
            self.values = values

        def predict(self, matrix, **kwargs):
            assert matrix.columns.tolist() == ["base", "previous_course_status"]
            return self.values

    class Scale:
        def convert(self, marks, versions):
            assert marks.tolist() == [0, 100]
            return np.array([0.0, 4.0]), np.array(["F", "A"])

    monkeypatch.setattr(module, "prepare_augmented_matrix", lambda frame, levels, base_features:
                        pd.DataFrame({"base": [1, 2], "previous_course_status": frame.previous_course_status}))

    scored = module.score_augmented_rows(rows, Model([-1, 101]), Model([-0.1, 1.1]), {}, Scale(), ["base"])

    assert scored.predicted_mark.tolist() == [0, 100]
    assert scored.expected_points.tolist() == [0, 4]
    assert scored.fail_probability.tolist() == [0, 1]


def test_augmented_scoring_rejects_nonfinite_predictions(monkeypatch):
    module = inference()
    rows = pd.DataFrame({"grade_version_id": ["v"], "previous_course_status": ["FAILED"]})
    monkeypatch.setattr(module, "prepare_augmented_matrix", lambda *args: pd.DataFrame({"base": [1]}))

    class Model:
        def __init__(self, value):
            self.value = value

        def predict(self, matrix, **kwargs):
            return [self.value]

    with pytest.raises(ValueError, match="non-finite"):
        module.score_augmented_rows(rows, Model(float("nan")), Model(0.2), {}, None, ["base"])
