"""Independent synthetic oracles for the isolated XML search experiment."""
import importlib
import importlib.util
from decimal import Decimal
from itertools import combinations

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.features.feature_contract import BASE_FEATURES, CATEGORICAL_FEATURES
from src.features.temporal_features import PLAN_CONTEXT_COLUMNS
from src.grade_scale import GradeScale


FEATURES33 = [name for name in BASE_FEATURES if name not in PLAN_CONTEXT_COLUMNS]


def core():
    assert importlib.util.find_spec("src.recommendation_experiments.xml_two_stage_search") is not None, (
        "The isolated experiment needs its exhaustive search implementation"
    )
    return importlib.import_module("src.recommendation_experiments.xml_two_stage_search")


def candidates(credits, marks=None, ids=None):
    marks = marks if marks is not None else [75] * len(credits)
    rows = pd.DataFrame({name: [0.] * len(credits) for name in BASE_FEATURES})
    for name in CATEGORICAL_FEATURES:
        rows[name] = "1"
    rows["course_id"] = ids if ids is not None else [f"C{i:02}" for i in range(len(credits))]
    rows["course_name"] = rows["course_id"]
    rows["course_credits"] = credits
    rows["attempt_number"] = 1
    rows["course_history_avg_mark"] = marks
    rows["course_history_fail_rate"] = np.linspace(.1, .8, len(credits))
    rows["course_history_avg_attempt"] = 1.
    return rows


def scale():
    return GradeScale(pd.DataFrame({
        "grade_version_id": [1] * 5,
        "from_percent": [50, 60, 70, 80, 90],
        "points": [1., 2., 2.5, 3., 4.],
        "grade_show": ["D", "C", "C+", "B", "A"],
    }))


class MarksModel:
    """Replace only the artifact's predict boundary; feature processing stays real."""
    def __init__(self, context_effect=0., output=None):
        self.context_effect = context_effect
        self.output = output
        self.matrices = []

    def predict(self, matrix, num_threads=4):
        self.matrices.append(matrix.copy())
        if self.output is not None:
            return np.asarray(self.output)
        result = matrix["course_history_avg_mark"].to_numpy(dtype=float)
        if self.context_effect:
            result = result + self.context_effect * matrix["peer_max_fail_rate"].fillna(0).to_numpy(dtype=float)
        return result


def scorer(features=BASE_FEATURES, context_effect=0., model=None):
    return core().GradeOnlyScorer(
        MarksModel(context_effect) if model is None else model,
        {name: ["__MISSING__", "__UNKNOWN__", "1"] for name in CATEGORICAL_FEATURES},
        scale(), features,
    )


def oracle(rows, *, effect=0., gpa=2., denominator=90.):
    """Brute-force independently of project enumeration and aggregation helpers."""
    plans = []
    credits = [Decimal(str(value)) for value in rows.course_credits]
    course_ids = rows.course_id.map(str).tolist()
    marks = rows.course_history_avg_mark.to_numpy(dtype=np.float32)
    fail_rates = rows.course_history_fail_rate.to_numpy(dtype=np.float32)
    for size in range(1, len(rows) + 1):
        for selected in combinations(range(len(rows)), size):
            total = sum((credits[i] for i in selected), Decimal(0))
            if total != 18:
                continue
            quality = 0.
            for i in selected:
                peers = [float(fail_rates[j]) for j in selected if j != i]
                mark = float(marks[i]) + effect * max(peers, default=0.)
                points = 4. if mark >= 90 else 3. if mark >= 80 else 2.5 if mark >= 70 else 2. if mark >= 60 else 1. if mark >= 50 else 0.
                quality += float(credits[i]) * points
            plans.append({
                "course_ids": sorted(course_ids[i] for i in selected),
                "candidate_indices": list(selected), "quality": quality,
                "semester": quality / 18., "cumulative": (gpa * denominator + quality) / (denominator + 18.),
            })
    return sorted(plans, key=lambda p: (-p["cumulative"], -p["semester"], tuple(p["course_ids"])))


def test_exhaustive_matches_independent_brute_force_with_bounded_batches():
    rows = candidates([3] * 9, [95, 85, 75, 65, 55, 95, 85, 75, 65])
    expected = oracle(rows)
    result = core().search_exhaustive(rows, scorer(), 2., 90., batch_size=7)
    assert result["status"] == "ok"
    assert result["generated_plan_count"] == len(expected) == 84
    assert [p["course_ids"] for p in result["recommendations"]] == [p["course_ids"] for p in expected[:3]]
    assert [p["projected_cumulative_gpa"] for p in result["recommendations"]] == pytest.approx([p["cumulative"] for p in expected[:3]])
    assert result["counts"]["scored47"] == 84
    assert result["diagnostics"]["max_batch_rows"] <= 7 * 6
    assert result["diagnostics"]["max_retained_plans"] <= 3
    stats = result["diagnostics"]["gpa_statistics"]
    assert stats["count"] == 84
    assert stats["min"] == pytest.approx(min(p["cumulative"] for p in expected))
    assert stats["max"] == pytest.approx(max(p["cumulative"] for p in expected))
    assert stats["sum"] == pytest.approx(sum(p["cumulative"] for p in expected))


def test_global_top_fifty_oracle_then_stage_two_only_sees_those_plans():
    rows = candidates([3] * 12, [91, 89, 86, 81, 78, 74, 71, 68, 64, 61, 57, 51])
    expected33 = oracle(rows)
    expected47 = oracle(rows, effect=18.)
    shortlist_ids = {tuple(p["course_ids"]) for p in expected33[:50]}
    expected_final = [p for p in expected47 if tuple(p["course_ids"]) in shortlist_ids][:3]
    stage2 = scorer(context_effect=18.)
    result = core().search_two_stage(rows, scorer(FEATURES33), stage2, 2., 90., batch_size=17)
    assert result["counts"]["generated"] == result["counts"]["scored33"] == 924
    assert result["counts"]["scored47"] == 50
    assert sum(len(m) for m in stage2.model.matrices) == 300
    assert [p["course_ids"] for p in result["shortlist"]] == [p["course_ids"] for p in expected33[:50]]
    assert [p["course_ids"] for p in result["recommendations"]] == [p["course_ids"] for p in expected_final]
    assert {p["stage2_rank"] for p in result["shortlist"]} == set(range(1, 51))
    for plan in result["shortlist"]:
        assert plan["stage1_rank"] in range(1, 51)
        assert plan["delta"] == pytest.approx(plan["stage2_GPA"] - plan["stage1_GPA"])


def test_ties_use_canonical_sorted_course_ids_independent_of_input_order():
    rows = candidates([6] * 5, ids=["Z", "A", "M", "C", "B"])
    result = core().search_exhaustive(rows, scorer(), 2., 90., batch_size=2)
    assert [p["course_ids"] for p in result["recommendations"]] == [["A", "B", "C"], ["A", "B", "M"], ["A", "B", "Z"]]
    reordered = rows.iloc[::-1].reset_index(drop=True)
    second = core().search_exhaustive(reordered, scorer(), 2., 90., batch_size=4)
    assert [p["course_ids"] for p in second["recommendations"]] == [p["course_ids"] for p in result["recommendations"]]


def test_decimal_credits_do_not_round_near_matches_and_keep_optional_zero_course():
    rows = candidates(["17.999999999999999999", "18", "0"], ids=["near", "exact", "zero"])
    result = core().search_exhaustive(rows, scorer(), 2., 90., top_n=10, batch_size=1)
    assert result["generated_plan_count"] == 2
    assert [p["course_ids"] for p in result["recommendations"]] == [["exact"], ["exact", "zero"]]
    assert len({tuple(p["course_ids"]) for p in result["recommendations"]}) == 2
    assert all(p["total_credits"] == 18 for p in result["recommendations"])


def test_fractional_exact_sum_is_feasible_without_integer_credit_rounding():
    rows = candidates(["5.5", "6.25", "6.25", "6.24"])
    result = core().search_exhaustive(rows, scorer(), 2., 90.)
    assert result["generated_plan_count"] == 1
    assert result["recommendations"][0]["candidate_indices"] == [0, 1, 2]


@pytest.mark.parametrize("credits,expected_count", [([9, 9, 6], 1), ([6, 6], 0), ([], 0)])
def test_two_stage_handles_fewer_than_fifty_and_no_exact_plan(credits, expected_count):
    rows = candidates(credits)
    model = MarksModel()
    result = core().search_two_stage(rows, scorer(FEATURES33), scorer(model=model), 2., 90.)
    assert result["counts"]["generated"] == expected_count
    assert result["counts"]["scored47"] == expected_count
    assert len(result["shortlist"]) == expected_count
    assert result["status"] == ("ok" if expected_count else "no_feasible_18_credit_plan")
    if not expected_count:
        assert result["recommendations"] == []
        assert model.matrices == []


def test_grade_only_scorer_recomputes_full_context_per_plan_and_preserves_inputs():
    rows = candidates([6, 12, 18], [70, 80, 90])
    rows["plan_id"] = [10, 10, 20]
    rows[PLAN_CONTEXT_COLUMNS] = 999.
    before = rows.copy(deep=True)
    model = MarksModel()
    scored = scorer(model=model).score(rows)
    assert model.matrices[0].columns.tolist() == BASE_FEATURES
    assert scored["plan_total_credits"].tolist() == [18., 18., 18.]
    assert scored["plan_course_count"].tolist() == [2, 2, 1]
    assert scored["peer_total_credits"].tolist() == [12., 6., 0.]
    assert scored["peer_credit_weighted_avg_mark"].iloc[:2].tolist() == [80., 70.]
    assert scored["peer_difficulty_missing"].tolist() == [0, 0, 1]
    assert "fail_probability" not in scored
    assert_frame_equal(rows, before)


def test_stage_one_needs_no_plan_context_sources_and_rejects_invalid_grade_before_predict():
    rows = candidates([18]).drop(columns=[*PLAN_CONTEXT_COLUMNS, "course_history_avg_attempt"])
    features = [name for name in FEATURES33 if name != "course_history_avg_attempt"]
    model = MarksModel()
    stage1 = scorer(features=features, model=model)
    assert stage1.score(rows)["expected_points"].tolist() == [2.5]
    rows["grade_version_id"] = "999"
    before = len(model.matrices)
    with pytest.raises(ValueError, match="grade_version_id"):
        stage1.score(rows)
    assert len(model.matrices) == before


@pytest.mark.parametrize("output,match", [([np.nan], "non-finite"), ([70, 80], "shape")])
def test_grade_only_scorer_rejects_invalid_prediction_arrays(output, match):
    with pytest.raises(ValueError, match=match):
        scorer(model=MarksModel(output=output)).score(candidates([18]).assign(plan_id=0))


def test_grade_only_scorer_clips_marks_before_points_conversion():
    result = scorer(model=MarksModel(output=[-10, 150])).score(candidates([9, 9]).assign(plan_id=0))
    assert result["predicted_mark"].tolist() == [0., 100.]
    assert result["expected_points"].tolist() == [0., 4.]


def test_observed_plan_allows_other_credit_totals_and_uses_backend_gpa_denominator():
    rows = candidates([3, 3], [95, 55])
    rows.loc[1, "attempt_number"] = 2
    plan = core().score_observed_plan(rows, scorer(), 2.5, 60.)
    assert plan["total_credits"] == 6.
    assert plan["expected_quality_points"] == 15.
    assert plan["expected_plan_gpa"] == 2.5
    assert plan["projected_cumulative_gpa"] == 2.5
    assert plan["expected_cumulative_gpa_gain"] == 0.
    assert plan["projected_gpa_requires_repeat_policy"] is True
    changed = core().score_observed_plan(candidates([18], [95]), scorer(), 2.5, 60.)
    assert changed["projected_cumulative_gpa"] == pytest.approx(222 / 78)


def test_digest_is_batch_independent_and_shared_plan_predictions_are_exactly_equal():
    rows = candidates([3] * 9, [91, 85, 78, 76, 73, 65, 62, 55, 51])
    baseline = core().search_exhaustive(rows, scorer(), 2., 90., batch_size=7)
    rerun = core().search_exhaustive(rows, scorer(), 2., 90., batch_size=11)
    two_stage = core().search_two_stage(rows, scorer(FEATURES33), scorer(), 2., 90., batch_size=13)
    assert baseline["diagnostics"]["plan_identity_sha256"] == rerun["diagnostics"]["plan_identity_sha256"]
    assert baseline["diagnostics"]["plan_identity_sha256"] == two_stage["diagnostics"]["plan_identity_sha256"]
    metrics = core().comparison_metrics(baseline, two_stage)
    assert metrics["top_1_match"] is True
    assert metrics["top_3_overlap"] == 3
    assert metrics["baseline_top_3_recall_at_50_count"] == 3
    assert metrics["baseline_top_3_recall_at_50"] == 1.
    assert metrics["gpa_regret"] == 0.
    assert metrics["prediction_parity"]["all_match"] is True
    assert metrics["prediction_parity"]["compared_plan_count"] == 3
    assert metrics["prediction_parity"]["compared_course_count"] == 18


def test_comparison_exposes_shortlist_loss_and_prediction_disagreement():
    baseline = {"recommendations": [
        {"course_ids": ["A"], "projected_cumulative_gpa": 3.2, "courses": [{"course_id": "A", "predicted_mark": 80., "expected_points": 3.}]},
        {"course_ids": ["B"], "projected_cumulative_gpa": 3.1, "courses": [{"course_id": "B", "predicted_mark": 75., "expected_points": 2.5}]},
        {"course_ids": ["C"], "projected_cumulative_gpa": 3.0, "courses": []},
    ], "timings": {"total_seconds": 10.}}
    two_stage = {"recommendations": [baseline["recommendations"][1]], "shortlist": [
        {**baseline["recommendations"][1], "courses": [{"course_id": "B", "predicted_mark": 76., "expected_points": 2.5}]}
    ], "timings": {"total_seconds": 2.}}
    metrics = core().comparison_metrics(baseline, two_stage)
    assert metrics["top_1_match"] is False
    assert metrics["top_3_overlap"] == 1
    assert metrics["baseline_top_3_recall_at_50_count"] == 1
    assert metrics["baseline_top_3_recall_at_50"] == pytest.approx(1 / 3)
    assert metrics["gpa_regret"] == pytest.approx(.1)
    assert metrics["speedup"] == 5.
    assert metrics["prediction_parity"]["all_match"] is False


def test_duplicate_course_ids_are_rejected_before_search_and_invalid_bounds_are_explicit():
    with pytest.raises(ValueError, match="Duplicate course_id"):
        core().search_exhaustive(candidates([9, 9], ids=["A", "A"]), scorer(), 2., 90.)
    with pytest.raises(ValueError, match="batch_size"):
        core().search_exhaustive(candidates([18]), scorer(), 2., 90., batch_size=0)
    with pytest.raises(ValueError, match="GPA"):
        core().search_exhaustive(candidates([6]), scorer(), 2., -1.)
