"""Post-prediction diagnostics stay separate from recommendation coverage."""
from copy import deepcopy

import pytest

from tools.recommendation_pilot_20251.actual_metrics import (
    attach_prediction_metrics, attach_recommendation_metrics, summarize_results,
)


def observed():
    return {"status": "AVAILABLE", "total_credits": 6, "course_count": 2, "courses": [
        {"course_id": "1.0", "course_credits": 3, "actual_mark": 54,
         "course_outcome_status": "pass", "result_status": "AVAILABLE", "grade_version_id": "v"},
        {"course_id": "2", "course_credits": 3, "actual_mark": 40,
         "course_outcome_status": "fail", "result_status": "AVAILABLE", "grade_version_id": "v"},
    ]}


def plan(ids, credits=3, score=3, plan_id=0):
    return {"plan_id": plan_id, "total_credits": len(ids) * credits,
            "expected_plan_gpa": score, "expected_failed_credits": .2,
            "plan_difficulty_balance": {"max_fail_probability": .1},
            "courses": [{"course_id": str(key), "course_credits": credits} for key in ids]}


def result(sample="s", gpa=1.5):
    plans = [plan([1, 3], plan_id=0), plan([1, 2], score=2, plan_id=1)]
    forecast = {"prediction_status": "PREDICTION_AVAILABLE", "course_predictions": [
        {"course_id": "1", "course_credits": 3, "predicted_mark": 60, "fail_probability": .1},
        {"course_id": "2.00", "course_credits": 3, "predicted_mark": 50, "fail_probability": .8},
    ]}
    return {"sample_id": sample, "candidate_mode": "original", "credit_experiment": "fixed_18",
            "target_credits": 6, "student_summary": {"start_agpa_points": gpa},
            "observed_plan": observed(), "search": {"evaluated_plan_count": 2,
                "visited_search_states": 7, "truncated": True},
            "experiments": {name: {"prediction_status": "PREDICTION_AVAILABLE",
                "analytical_plans": deepcopy(plans), "diagnostic_plans": deepcopy(plans),
                "latency": {"feature_extraction_seconds": .01, "prediction_seconds": .02,
                    "ranking_seconds": .03, "total_seconds": .06}} for name in "ABC"},
            "observed_plan_prediction": {"experiments": {name: deepcopy(forecast) for name in "ABC"}},
            "latency": {"candidate_preparation_seconds": .01, "plan_generation_seconds": .02,
                        "total_request_seconds": .2}}


def test_overlap_is_normalized_and_examined_actual_plan_has_rank_and_frequency():
    row = result()
    attach_recommendation_metrics(row)
    metrics = row["experiments"]["A"]["recommendation_metrics"]
    assert metrics["top1_actual_overlap"] == 1
    assert metrics["top3_union_actual_overlap"] == 2
    assert metrics["actual_plan_examined"] is True
    assert metrics["actual_plan_rank"] == 2
    assert metrics["actual_plan_possible_by_load"] is True
    assert metrics["actual_course_exposure"]["1"]["examined_plan_count"] == 2
    assert metrics["actual_course_exposure"]["2"]["examined_plan_frequency"] == .5
    assert metrics["search_truncated"] is True


def test_same_ids_with_wrong_credit_load_never_becomes_exact_actual_match():
    row = result()
    row["target_credits"] = 18
    for model in row["experiments"].values():
        model["diagnostic_plans"] = [plan([1, 2], credits=9)]
        model["analytical_plans"] = model["diagnostic_plans"]
    attach_recommendation_metrics(row)
    metrics = row["experiments"]["A"]["recommendation_metrics"]
    assert metrics["top1_actual_overlap"] == 2
    assert metrics["actual_plan_examined"] is False
    assert metrics["actual_plan_possible_by_load"] is False
    assert metrics["actual_plan_rank"] is None


def test_unavailable_recommendations_are_na_and_never_zero_overlap():
    row = result()
    row["experiments"]["A"] = {"prediction_status": "NO_MATCHING_PLAN", "diagnostic_plans": []}
    attach_recommendation_metrics(row)
    metrics = row["experiments"]["A"]["recommendation_metrics"]
    assert metrics["top1_actual_overlap"] is None
    assert metrics["top3_union_actual_overlap"] is None
    assert metrics["actual_plan_examined"] is None


def test_prediction_error_uses_full_observed_forecast_and_trusted_failure_status():
    row = result()
    # A different recommended-course prediction cannot affect actual-plan errors.
    row["experiments"]["A"]["course_predictions"] = [{"course_id": "1", "predicted_mark": 99}]
    attach_prediction_metrics(row)
    metrics = row["prediction_metrics"]["A"]
    assert metrics["course_count"] == 2
    assert metrics["mae"] == 8
    assert metrics["rmse"] == pytest.approx((68) ** .5)
    assert metrics["bias"] == 8
    assert metrics["fail_brier"] == pytest.approx(.025)
    assert metrics["fail_roc_auc"] == 1
    # mark=54 is labelled pass by its trusted scale/status, not a guessed 60 cutoff.
    assert metrics["course_errors"][0]["fail_label"] == 0
    assert row["experiments"]["A"]["observed_prediction_metrics"] == metrics


@pytest.mark.parametrize("mutation,reason", [
    ({"course_credits": 9}, "CREDIT_MISMATCH"),
    ({"grade_version_id": "other"}, "GRADE_VERSION_MISMATCH"),
])
def test_observed_prediction_misalignment_is_rejected(mutation, reason):
    row = result()
    row["observed_plan_prediction"]["experiments"]["A"]["course_predictions"][0].update(mutation)
    attach_prediction_metrics(row)
    metrics = row["prediction_metrics"]["A"]
    assert metrics["course_count"] == 1
    assert metrics["rejected_courses"] == [{"course_id": "1", "reason": reason}]


def test_repeated_scenarios_do_not_quadruple_weight_observed_predictions():
    rows = []
    for mode in ["original", "augmented"]:
        for credit in ["fixed_18", "actual_load"]:
            row = result()
            row.update(candidate_mode=mode, credit_experiment=credit)
            rows.append(row)
    summary = summarize_results(rows)
    overall = next(row for row in summary["prediction_summary"] if row["model"] == "A" and row["group"] == "all")
    low = next(row for row in summary["prediction_summary"] if row["model"] == "A" and row["group"] == "low_archived_gpa")
    assert overall["student_count"] == 1
    assert overall["course_count"] == 2
    assert overall["micro_mae"] == 8
    assert overall["macro_mae"] == 8
    assert low["course_count"] == 2
    assert len(summary["recommendation_summary"]) == 12
    assert len(summary["latency_summary"]) == 12


def test_macro_and_micro_prediction_metrics_use_correct_denominators():
    first, second = result(), result("s2", gpa=3)
    second["observed_plan_prediction"]["experiments"]["A"]["course_predictions"] = [
        {"course_id": "1", "course_credits": 3, "predicted_mark": 54, "fail_probability": .2}]
    summary = summarize_results([first, second])
    overall = next(row for row in summary["prediction_summary"] if row["model"] == "A" and row["group"] == "all")
    assert overall["student_count"] == 2
    assert overall["course_count"] == 3
    assert overall["micro_mae"] == pytest.approx(16 / 3)
    assert overall["macro_mae"] == 4
    assert overall["missing_prediction_count"] == 1


def test_summary_does_not_treat_unavailable_as_negative_or_conflicting_forecasts_as_replicates():
    first, second = result(), result()
    second["candidate_mode"] = "augmented"
    second["observed_plan_prediction"]["experiments"]["A"]["course_predictions"][0]["predicted_mark"] = 100
    summary = summarize_results([first, second])
    aggregate = next(row for row in summary["prediction_summary"] if row["model"] == "A" and row["group"] == "all")
    assert aggregate["student_count"] == 0
    assert any("OBSERVED_FORECAST_DIFFERS_ACROSS_SCENARIOS:s:A" == value for value in summary["warnings"])


def test_latency_summary_reports_component_mean_p95_and_measurement_count():
    summary = summarize_results([result()])
    row = next(row for row in summary["latency_summary"] if row["model"] == "A")
    assert row["measurement_count"] == 1
    assert row["prediction_seconds_mean"] == .02
    assert row["total_request_seconds_p95"] == .2


def test_paired_summary_uses_only_same_student_available_in_both_modes():
    baseline, augmented, unavailable = result(), result(), result("s2")
    augmented["candidate_mode"] = "augmented"
    augmented["experiments"]["A"]["analytical_plans"] = [plan([1, 2])]
    unavailable["experiments"]["A"] = {"prediction_status": "BLOCKED"}
    summary = summarize_results([baseline, augmented, unavailable])
    paired = next(row for row in summary["paired_recommendation_summary"] if row["model"] == "A")
    assert paired["paired_student_count"] == 1
    assert paired["original_mean_top1_actual_overlap"] == 1
    assert paired["augmented_mean_top1_actual_overlap"] == 2
    assert paired["mean_top1_actual_overlap_delta"] == 1
    assert paired["augmentation_is_post_choice_diagnostic"] is True


def test_fractional_credit_load_uses_decimal_sum_and_independent_status_labels():
    row = result()
    row["target_credits"] = 3.3
    row["observed_plan"]["courses"][0]["course_credits"] = 1.1
    row["observed_plan"]["courses"][1]["course_credits"] = 2.2
    exact = plan([1, 2])
    exact.update(total_credits=3.3)
    exact["courses"][0]["course_credits"] = 1.1
    exact["courses"][1]["course_credits"] = 2.2
    row["experiments"]["A"]["diagnostic_plans"] = [exact]
    attach_recommendation_metrics(row)
    assert row["experiments"]["A"]["recommendation_metrics"]["actual_plan_possible_by_load"] is True
    assert row["experiments"]["A"]["recommendation_metrics"]["actual_plan_examined"] is True
