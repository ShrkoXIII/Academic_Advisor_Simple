"""Score the complete observed roster, with no target outcomes as inputs."""
import json

import pandas as pd
import pytest

from tests.test_pilot_20251_engine import bridge
from tools.recommendation_pilot_20251.observed_prediction import ObservedPlanPredictor


@pytest.fixture
def predictor(bridge, tmp_path):
    _, engine, student, _, _, _ = bridge
    engine._catalog["course_name_sl"] = [f"Course {c}" for c in "ABCD"]
    history_path = tmp_path / "prior_attempts.parquet"
    pd.DataFrame({"student_id": ["S"] * 3, "course_id": ["A"] * 3,
                  "part_id": [20243, 20251, 20252], "attempt_number": [2, 99, 200]}).to_parquet(history_path)

    class Experiments:
        fail_b = False

        def __init__(self):
            self.seen = []

        def inspect(self):
            return {name: {"status": "READY", "model_version": "synthetic-bc",
                           "manifest_sha256": "synthetic-manifest", "history_as_of_part": 20243,
                           "feature_count": 44 if name == "B" else 47} for name in "BC"}

        def predict_course_rows(self, frame, name):
            self.seen.append((name, frame.copy()))
            if self.fail_b and name == "B":
                raise ValueError("private model error")
            return frame.assign(predicted_mark=70 if name == "B" else 80, expected_points=3 if name == "B" else 4,
                                expected_grade="B", fail_probability=.2, course_history_fallback_level=6,
                                course_history_effective_support=0)

    engine._experimental = Experiments()
    instance = ObservedPlanPredictor(root=tmp_path, engine=engine, course_history_path=history_path)
    return instance, engine, student


def test_predicts_every_actual_course_in_its_full_plan_without_search_or_target_marks(predictor):
    instance, engine, student = predictor
    registrations = [{"course_id": "A", "course_credits": 3, "actual_mark": 99},
                     {"course_id": "B", "course_credits": 3, "actual_mark": 1}]
    result = instance.predict(student, registrations)
    assert result["status"] == "PREDICTION_AVAILABLE" and result["context"] == "actual_registered_plan"
    assert result["course_count"] == 2 and result["total_credits"] == 6
    assert len(result["shared_inputs_sha256"]) == 64
    for name, expected in [("A", 60), ("B", 70), ("C", 80)]:
        experiment = result["experiments"][name]
        assert experiment["prediction_status"] == "PREDICTION_AVAILABLE"
        assert [c["course_id"] for c in experiment["course_predictions"]] == ["A", "B"]
        assert all(c["predicted_mark"] == expected for c in experiment["course_predictions"])
        assert experiment["projected_cumulative_gpa"] is None
        assert experiment["official_registration_validated"] is False
        assert experiment["plan_set_sha256"] == result["plan_set_sha256"]
    matrix = engine._baseline.grade_model.matrices[-1]
    assert matrix.plan_course_count.tolist() == [2, 2]
    assert matrix.plan_total_credits.tolist() == [6, 6]
    assert matrix.attempt_number.tolist() == [3, 1]
    assert matrix.prior_total_reg_credits.tolist() == [97.5, 97.5]
    for name, frame in engine._experimental.seen:
        assert len(frame) == 2
        assert not {"actual_mark", "final_mark", "points", "grade_id", "finish_status"} & set(frame)
    assert result["provenance"]["target_outcomes_used"] is False
    json.dumps(result, allow_nan=False)


def test_changing_actual_outcomes_or_selected_candidate_plan_cannot_change_the_prediction(predictor):
    instance, engine, student = predictor
    a = instance.predict(student, [{"course_id": "A", "course_credits": 3, "actual_mark": 0}])
    b = instance.predict(student, [{"course_id": "A", "course_credits": 3, "actual_mark": 100}])
    assert a == b
    assert len(engine._baseline.grade_model.matrices) == 1


def test_batch_reuses_c_reference_work_and_preserves_each_plan_context(predictor):
    instance, engine, student = predictor
    results = instance.predict_many([
        (student, [{"course_id": "A", "course_credits": 3}, {"course_id": "B", "course_credits": 3}]),
        (student, [{"course_id": "C", "course_credits": 3}]),
    ])
    assert [result["course_count"] for result in results] == [2, 1]
    calls = [frame for name, frame in engine._experimental.seen if name == "C"]
    assert len(calls) == 1 and len(calls[0]) == 3
    assert calls[0].plan_id.nunique() == 2
    matrices = pd.concat(engine._baseline.grade_model.matrices)
    assert matrices.plan_course_count.tolist() == [2, 2, 1]
    for result in results:
        assert all(len(e["course_predictions"]) == result["course_count"] for e in result["experiments"].values())
        assert all({c["plan_id"] for c in e["course_predictions"]} == {0} for e in result["experiments"].values())


def test_one_incompatible_model_does_not_hide_other_actual_plan_predictions(predictor):
    instance, engine, student = predictor
    engine._experimental.fail_b = True
    result = instance.predict(student, [{"course_id": "A", "course_credits": 3}])
    assert result["experiments"]["A"]["prediction_status"] == "PREDICTION_AVAILABLE"
    assert result["experiments"]["B"]["prediction_status"] == "BLOCKED"
    assert result["experiments"]["C"]["prediction_status"] == "PREDICTION_AVAILABLE"
    assert result["experiments"]["B"]["course_predictions"] == []
    assert "private model error" not in json.dumps(result)


def test_original_model_failure_leaves_independent_b_c_forecasts_available(predictor, monkeypatch):
    instance, engine, student = predictor
    monkeypatch.setattr(engine, "inspect_assets", lambda: {"status": "BLOCKED", "reason": "BROKEN_ORIGINAL"})
    result = instance.predict(student, [{"course_id": "A", "course_credits": 3}])
    assert result["experiments"]["A"]["prediction_status"] == "BLOCKED"
    assert result["experiments"]["B"]["prediction_status"] == "PREDICTION_AVAILABLE"
    assert result["experiments"]["C"]["prediction_status"] == "PREDICTION_AVAILABLE"


@pytest.mark.parametrize("registrations", [[], [{"course_id": "A", "course_credits": 3}] * 2,
                                          [{"course_id": "A", "course_credits": 4}]])
def test_invalid_or_ambiguous_actual_plan_never_gets_fabricated_predictions(predictor, registrations):
    instance, engine, student = predictor
    result = instance.predict(student, registrations)
    assert result["status"] == "BLOCKED"
    assert all(e["course_predictions"] == [] for e in result["experiments"].values())
    assert not engine._baseline.grade_model.matrices
