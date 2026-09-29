"""Protect feature independence, exact search, and comparison semantics."""
import importlib
from itertools import combinations

import numpy as np
import pandas as pd
import pytest

from src.features.feature_contract import BASE_FEATURES, CATEGORICAL_FEATURES, learn_category_levels


def experiment():
    return importlib.import_module("src.experiments.course_only_core")


def scores(ids, credits, points, failures):
    return pd.DataFrame({"course_id": ids, "course_credits": credits,
                         "expected_points": points, "fail_probability": failures})


def test_course_matrix_does_not_need_plan_context_and_retains_unknown_categories():
    ex = experiment()
    frame = pd.DataFrame({name: [1.0, np.nan] for name in ex.COURSE_ONLY_FEATURES})
    for name in CATEGORICAL_FEATURES:
        frame[name] = ["known", "unseen"]
    levels = learn_category_levels(frame.iloc[:1])
    matrix = ex.prepare_course_matrix(frame, levels)
    assert matrix.shape == (2, 33)
    assert matrix.columns.tolist() == [f for f in BASE_FEATURES if f not in ex.REMOVED_CONTEXT_FEATURES]
    assert len(set(BASE_FEATURES) - set(matrix.columns)) == 14
    assert matrix.iloc[1].plan_course_type_id == "__UNKNOWN__"
    assert np.isnan(matrix.iloc[1].gpa_prev_1)


def test_exact_search_uses_every_candidate_and_risk_then_course_order_for_ties():
    ex = experiment()
    rows = scores(["c", "a", "b", "d"], [2, 2, 2, 4], [3, 3, 3, 2.75], [.1, .1, .2, 0])
    plans, stats = ex.optimize_exact_credits(rows, 4, current_gpa=3, prior_credits=6, top_k=10)
    assert [p["course_ids"] for p in plans] == [["a", "c"], ["a", "b"], ["b", "c"], ["d"]]
    assert plans[0]["expected_quality_points"] == 12
    assert plans[0]["expected_plan_gpa"] == 3
    assert plans[0]["projected_cumulative_gpa"] == 3
    assert plans[0]["expected_failed_credits"] == pytest.approx(.4)
    assert stats["matching_combinations"] == 4


def test_fractional_credit_search_and_zero_credit_optional_courses():
    ex = experiment()
    rows = scores(["a", "b", "z"], [.1, .2, 0], [4, 3, 4], [.1, .2, 0])
    plans, stats = ex.optimize_exact_credits(rows, .3, current_gpa=2, prior_credits=1, top_k=10)
    assert [p["course_ids"] for p in plans] == [["a", "b"], ["a", "b", "z"]]
    assert plans[0]["expected_quality_points"] == pytest.approx(1)
    assert plans[0]["total_credits"] == .3
    assert stats["matching_combinations"] == 2
    assert ex.optimize_exact_credits(rows, .4, current_gpa=2, prior_credits=1)[0] == []


def test_top_k_matches_independent_bruteforce_and_is_input_order_invariant():
    ex = experiment()
    rows = scores([f"c{i:02}" for i in range(12)], [1, 2, 3] * 4,
                  [1, 3, 4, 2] * 3, [.2, .1, .3] * 4)
    expected = []
    for n in range(1, 13):
        for indices in combinations(range(12), n):
            group = rows.iloc[list(indices)]
            if group.course_credits.sum() == 8:
                expected.append((-(group.course_credits * group.expected_points).sum(),
                                 (group.course_credits * group.fail_probability).sum(),
                                 tuple(group.course_id)))
    # Compare risk to tolerance; tuples fix the order for equal mathematical sums.
    expected.sort(key=lambda item: (item[0], round(item[1], 12), item[2]))
    actual, _ = ex.optimize_exact_credits(rows.sample(frac=1, random_state=4), 8, current_gpa=2, prior_credits=10)
    assert [p["course_ids"] for p in actual] == [list(x[2]) for x in expected[:10]]


@pytest.mark.parametrize("column,value", [("course_credits", -1), ("expected_points", np.nan),
                                         ("expected_points", 5), ("fail_probability", 1.1)])
def test_optimizer_rejects_invalid_scores(column, value):
    ex = experiment()
    rows = scores(["a"], [3], [3], [.1])
    rows.loc[0, column] = value
    with pytest.raises(ValueError):
        ex.optimize_exact_credits(rows, 3, current_gpa=2, prior_credits=10)


def test_sensitivity_uses_population_std_and_course_sets_ignore_plan_ids():
    ex = experiment()
    rows = pd.DataFrame({"student_id": ["s"] * 4, "course_id": ["a", "a", "b", "b"],
                         "predicted_mark": [60, 80, 70, 70], "fail_probability": [.1, .3, .2, .2]})
    detail, summary = ex.plan_context_sensitivity(rows)
    assert detail.loc[detail.course_id.eq("a"), "predicted_mark_std"].iloc[0] == 10
    assert summary["predicted_mark_range"]["median"] == 10
    official = [{"course_ids": ["b", "a"]}, {"course_ids": ["a", "c"]}, {"course_ids": ["b", "c"]}]
    experimental = [{"course_ids": ["c", "a"]}, {"course_ids": ["a", "b"]}, {"course_ids": ["x"]}]
    result = ex.compare_course_sets(official, experimental)
    assert result["top1_recall_at_1"] == 0
    assert result["top1_recall_at_3"] == 1
    assert result["top3_recall_at_3"] == pytest.approx(2 / 3)


def test_scoring_predicts_each_candidate_once_and_clips_before_grade_conversion():
    ex = experiment()
    rows = pd.DataFrame({name: [1, 2, 3] for name in ex.COURSE_ONLY_FEATURES})
    rows["course_id"] = ["a", "b", "c"]
    for name in CATEGORICAL_FEATURES:
        rows[name] = "v"
    class Model:
        def __init__(self, values):
            self.values, self.calls, self.rows = values, 0, 0
        def predict(self, matrix, **kwargs):
            self.calls += 1
            self.rows += len(matrix)
            return self.values
    class Scale:
        def convert(self, marks, versions):
            assert marks.tolist() == [0, 50, 100]
            return np.array([0, 2, 4]), np.array(["F", "C", "A"])
    grade, fail = Model([-10, 50, 110]), Model([-.1, .2, 1.1])
    output, stats = ex.score_courses_once(rows, grade, fail, learn_category_levels(rows), Scale())
    assert output.expected_points.tolist() == [0, 2, 4]
    assert output.fail_probability.tolist() == [0, .2, 1]
    assert stats["grade_prediction_rows"] == stats["fail_prediction_rows"] == 3
    assert stats["model_prediction_calls"] == 2
    assert grade.calls == fail.calls == 1
    assert grade.rows == fail.rows == 3


def test_training_folds_keep_official_temporal_cutoffs_weights_and_33_columns():
    training = importlib.import_module("src.experiments.course_only_training")
    frame = pd.DataFrame({f: [1] * 6 for f in BASE_FEATURES})
    frame["part_id"] = [20211, 20221, 20231, 20233, 20241, 20243]
    frame["final_mark"], frame["is_fail"] = [40, 70, 80, 90, 50, 60], [1, 0, 0, 0, 0, 0]
    frame["grade_version_id"] = ["old", "old", "new", "new", "future", "future"]
    folds = training.prepare_course_folds(frame)
    assert [(f["fit_rows"], f["valid_rows"]) for f in folds] == [(2, 2), (4, 2)]
    assert folds[0]["fit_weight"].tolist() == [.25, 1]
    assert folds[0]["valid_X"].grade_version_id.astype("string").tolist() == ["__UNKNOWN__"] * 2
    assert all(f["fit_X"].shape[1] == f["valid_X"].shape[1] == 33 for f in folds)


def test_official_rescore_lookup_uses_hashable_course_sets_for_arrow_strings():
    evaluation = importlib.import_module("src.experiments.course_only_evaluation")
    rows = pd.DataFrame({"plan_id": [1, 1, 4, 4], "course_id": pd.Series(["b", "a", "a", "c"], dtype="string")})
    assert evaluation.official_plan_lookup(rows) == {("a", "b"): 1, ("a", "c"): 4}


@pytest.mark.parametrize("history_cutoff,training_cutoff", [(20251, 20243), (20243, 20251), (20233, 20243)])
def test_course_rows_reject_target_or_future_training_history_and_stale_history(history_cutoff, training_cutoff):
    from tests.recommendation_fixtures import synthetic_snapshot, synthetic_candidates, synthetic_course_history
    with pytest.raises(ValueError):
        experiment().prepare_course_rows(synthetic_snapshot(), synthetic_candidates(), 20251,
                                         synthetic_course_history(history_cutoff), training_as_of_part=training_cutoff)


def test_complete_comparison_preserves_same_request_scores_and_official_rescoring():
    from tests.recommendation_fixtures import synthetic_snapshot, synthetic_candidates, synthetic_engine, RecordingModel
    evaluation = importlib.import_module("src.experiments.course_only_evaluation")
    engine = synthetic_engine(grade=60, fail=.1)
    engine.grade_model = evaluation.PredictionCounter(engine.grade_model)
    engine.fail_model = evaluation.PredictionCounter(engine.fail_model)
    experimental = (RecordingModel(60), RecordingModel(.1), engine.category_levels, {"training_as_of_part": 20243})
    measured = evaluation.compare_case(engine, experimental, synthetic_candidates(), synthetic_snapshot(), repeats=1)
    comparison, scored, official, plans, *_ = measured
    assert comparison["top1_recall_at_1"] == 1
    assert comparison["official_matching_plans"] == 1
    assert comparison["official_course_in_plan_prediction_rows"] == comparison["experimental_course_prediction_rows"] == 6
    assert comparison["official_rescored_projected_gpa_regret"] == pytest.approx(0)
    assert plans[0]["expected_quality_points"] == 36
    assert plans[0]["projected_cumulative_gpa"] == pytest.approx(186 / 78)
    assert plans[0]["expected_failed_credits"] == pytest.approx(1.8)
    assert len(scored) == 6


def test_protection_preflight_preserves_original_hashes_and_detects_later_changes(tmp_path, monkeypatch):
    evaluation = importlib.import_module("src.experiments.course_only_evaluation")
    monkeypatch.setattr(evaluation, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(evaluation, "COURSE_ONLY_EVALUATION_DIR", tmp_path / "results")
    source = tmp_path / "official.txt"
    source.write_text("original", encoding="utf-8")
    evaluation.capture_protected_files(protected_paths=[source])
    assert evaluation.verify_protected_files()["changed"] == []
    source.write_text("modified", encoding="utf-8")
    with pytest.raises(ValueError, match="Protected files changed"):
        evaluation.capture_protected_files(protected_paths=[source])
