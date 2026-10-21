import pandas as pd
import pytest

from tools.recommendation_pilot_20251.enhanced import (
    PointInTimePeers, difficulty_gap, plan_difficulty_balance, select_improving_plans,
)


def historical():
    return pd.DataFrame([
        {"student_id": str(i), "degree_id": "d", "course_id": "c", "part_id": 20231,
         "grade_version_id": "v", "start_agpa_points": 2.5, "start_total_in_credits": 60,
         "degree_credits_count": 120, "gpa_trend_delta": .1, "prior_total_fail_courses": 2,
         "points": 3.0, "final_mark": 80.0} for i in range(6)])


def target():
    return {"student_id": "target", "degree_id": "d", "grade_version_id": "v",
            "start_agpa_points": 2.5, "start_total_in_credits": 60,
            "degree_credits_count": 120, "gpa_trend_delta": .1, "prior_total_fail_courses": 2}


def test_peers_never_see_target_or_future_outcomes():
    frame = historical()
    frame.loc[len(frame)] = {**frame.iloc[0].to_dict(), "student_id": "future", "part_id": 20251, "points": 0}
    frame.loc[len(frame)] = {**frame.iloc[0].to_dict(), "student_id": "target", "points": 0}
    result = PointInTimePeers(frame).predict(target(), "c", target_part=20251)
    assert result["peer_expected_points"] == 3.0
    assert result["similar_peer_support"] == 6
    assert result["max_source_part"] == 20231


def test_peer_prefix_changes_with_historical_target():
    model = PointInTimePeers(historical())
    assert model.predict(target(), "c", target_part=20231)["status"] == "NOT_AVAILABLE"


def test_peer_support_is_distinct_students_and_weak_support_is_visible():
    data = pd.concat([historical().iloc[:2]] * 4, ignore_index=True)
    result = PointInTimePeers(data).predict(target(), "c", target_part=20251)
    assert result["similar_peer_support"] == 2
    assert result["peer_expected_points"] is None
    assert result["status"] == "NOT_AVAILABLE"


def test_peer_degree_course_and_grade_version_are_not_mixed():
    data = historical()
    data["grade_version_id"] = "other"
    assert PointInTimePeers(data).predict(target(), "c", target_part=20251)["similar_peer_support"] == 0


def test_nullable_query_and_missing_trend_preserve_available_distances():
    import warnings
    data = historical()
    data["gpa_trend_delta"] = float('nan')
    query = {**target(), "gpa_trend_delta": pd.NA}
    with warnings.catch_warnings():
        warnings.simplefilter('error', RuntimeWarning)
        result = PointInTimePeers(data).predict(query, 'c', target_part=20251)
    assert result['peer_expected_points'] == 3.0
    assert result['similar_peer_support'] == 6


def test_difficulty_uses_marks_without_fabricating_grade_points():
    assert difficulty_gap(75, 60) == 15
    with pytest.raises(ValueError):
        difficulty_gap(105, 60)
    assert difficulty_gap(None, 60) is None


def test_plan_balance_has_weighted_risk_and_documented_threshold():
    result = plan_difficulty_balance([{"course_credits": 4, "fail_probability": .8},
                                      {"course_credits": 2, "fail_probability": .2}])
    assert result["max_fail_probability"] == .8
    assert result["credit_weighted_fail_probability"] == pytest.approx(.6)
    assert result["high_risk_course_count"] == 1
    assert result["high_risk_threshold"] == .5
    assert result["risk_dispersion"] > 0


def test_no_unproven_improvements_are_selected_or_list_padded():
    plans = [{"plan_id": "valid", "is_expected_cumulative_improvement": True, "projected_cumulative_gpa": 3.1},
             {"plan_id": "unknown", "is_expected_cumulative_improvement": None, "expected_plan_gpa": 4},
             {"plan_id": "worse", "is_expected_cumulative_improvement": False, "projected_cumulative_gpa": 2}]
    assert [p["plan_id"] for p in select_improving_plans(plans)] == ["valid"]
    assert select_improving_plans(plans[1:]) == []
