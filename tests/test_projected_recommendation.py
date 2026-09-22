import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from src.experiments.specialty_history import FrozenSpecialtyHistory
from src.recommendation import (
    AcademicPlanRecommender, CANDIDATE_COURSE_COLUMNS, STUDENT_SNAPSHOT_COLUMNS,
    model_training_provenance, project_cumulative_gpa, rank_plans,
    resolve_current_gpa_credits, summarize_scored_plans,
)
from src.recommendation_inputs import validate_snapshot
from src.recommendation_output import save_recommendations
from src.features.temporal_features import CourseHistoryState


class ProjectionTests(unittest.TestCase):
    def test_additive_example_and_zero_prior_credits(self):
        self.assertAlmostEqual(project_cumulative_gpa(2, 60, 42, 12), 2.25)
        self.assertAlmostEqual(project_cumulative_gpa(0, 0, 42, 12), 3.5)

    def test_invalid_or_unknown_denominators_are_rejected(self):
        for value in [-1, np.nan, np.inf]:
            with self.assertRaises(ValueError):
                project_cumulative_gpa(2, value, 42, 12)
        for quality, credits in [(42, 0), (np.nan, 12), (49, 12)]:
            with self.assertRaises(ValueError):
                project_cumulative_gpa(2, 60, quality, credits)
        for snapshot in [{}, {"prior_total_reg_credits": None}, {"prior_total_reg_credits": np.nan},
                         {"start_total_in_credits": 60}]:
            with self.assertRaisesRegex(ValueError, "known current_gpa_credits"):
                resolve_current_gpa_credits(snapshot)
        self.assertEqual(resolve_current_gpa_credits({"prior_total_reg_credits": 60, "start_total_in_credits": 30}),
                         (60, "snapshot.prior_total_reg_credits"))
        self.assertEqual(resolve_current_gpa_credits({"current_gpa_credits": 55})[0], 55)
        self.assertEqual(resolve_current_gpa_credits({"current_gpa_credits": 55}, 60)[0], 60)

    def test_larger_load_can_win_despite_lower_semester_gpa(self):
        rows = pd.DataFrame({"plan_id": [0, 1], "course_id": ["A", "B"],
                             "course_credits": [12., 18.], "expected_points": [3.5, 3.25],
                             "fail_probability": [.1, .2], "attempt_number": [1, 2]})
        result = summarize_scored_plans(rows, 2, 60)
        self.assertEqual(result.plan_id.tolist(), [1, 0])
        self.assertAlmostEqual(result.projected_cumulative_gpa.iloc[0], 178.5 / 78)
        self.assertAlmostEqual(result.projected_cumulative_gpa.iloc[1], 2.25)
        self.assertEqual(result.projected_gpa_requires_repeat_policy.tolist(), [True, False])

    def test_all_four_ranking_keys(self):
        plans = pd.DataFrame({"plan_id": [9, 8, 7, 6, 5],
                              "projected_cumulative_gpa": [2.5, 2.4, 2.4, 2.4, 2.4],
                              "expected_failed_credits": [3, 2, 1, 1, 1],
                              "expected_plan_gpa": [3, 4, 3, 3.5, 3.5]})
        self.assertEqual(rank_plans(plans).plan_id.tolist(), [9, 5, 6, 7, 8])

    def test_explicit_model_cutoff_takes_priority_over_legacy_history_metadata(self):
        meta = {"training_as_of_part": 20251, "history_protocol": {"holdout_2025": "frozen after 2024"}}
        self.assertEqual(model_training_provenance(meta)["training_as_of_part"], 20251)
        self.assertIsNone(model_training_provenance({})["training_as_of_part"])


class FixedScoreRecommender(AcademicPlanRecommender):
    def score_rows(self, rows):
        return rows.assign(expected_points=2., fail_probability=.9)


class PlanPreservationTests(unittest.TestCase):
    def setUp(self):
        history = pd.DataFrame({"part_id": [20243], "degree_id": ["D"],
                                "plan_requirement_type_id": ["R"], "final_mark": [60.],
                                "is_fail": [0], "points": [2.]})
        self.engine = FixedScoreRecommender(None, None, {}, {}, CourseHistoryState(as_of_part=20243),
                                            FrozenSpecialtyHistory.from_training(history), {})
        self.snapshot = {c: 1 for c in STUDENT_SNAPSHOT_COLUMNS}
        self.snapshot.update(student_id="S", degree_id="D", part_id=20251,
                             start_agpa_points=3.5, start_total_in_credits=999, current_gpa_credits=60)
        self.candidates = pd.DataFrame({c: [1] * 6 for c in CANDIDATE_COURSE_COLUMNS})
        self.candidates["course_id"] = list("ABCDEF")
        self.candidates["course_credits"] = 3.
        self.candidates["plan_requirement_type_id"] = "R"
        self.kwargs = dict(student_snapshot=self.snapshot, candidate_courses=self.candidates,
                           part_id=20251, current_gpa=3.5, credits=9)

    def test_twenty_below_current_gpa_plans_are_scored_saved_and_top_three_returned(self):
        with tempfile.TemporaryDirectory() as directory:
            result = save_recommendations(self.engine, directory, **self.kwargs, batch_size=2)
            plans = pd.read_parquet(Path(directory) / "plans.parquet")
            courses = pd.read_parquet(Path(directory) / "courses.parquet")
            saved = json.loads((Path(directory) / "result.json").read_text())
        self.assertEqual(result["status"], "ok")
        for field in ["matching_plan_count", "scored_plan_count", "accepted_plan_count"]:
            self.assertEqual(result[field], 20)
        self.assertEqual(len(plans), 20)
        self.assertEqual(len(courses), 60)
        self.assertEqual(result["returned_plan_count"], 3)
        self.assertEqual(len(result["recommendations"]), 3)
        self.assertFalse(result["has_expected_improvement"])
        self.assertEqual(result["plans_with_expected_improvement"], 0)
        self.assertEqual((result["target_part"], result["history_as_of_part"]), (20251, 20243))
        self.assertEqual(result["current_gpa_credits"], 60)
        self.assertEqual(saved["recommendations"], result["recommendations"])
        self.assertAlmostEqual(result["best_projected_cumulative_gpa"], (60 * 3.5 + 18) / 69)
        self.assertLess(result["best_expected_cumulative_gpa_gain"], 0)
        self.assertEqual([r["rank"] for r in result["recommendations"]], [1, 2, 3])
        for recommendation in result["recommendations"]:
            self.assertIs(recommendation["is_expected_cumulative_improvement"], False)
            self.assertEqual(len(recommendation["courses"]), 3)
            self.assertTrue(all(c["fail_probability"] == .9 for c in recommendation["courses"]))

    def test_batch_and_candidate_order_are_stable_and_top_n_override_is_deliberate(self):
        plans, result = self.engine.recommend(**self.kwargs, batch_size=1)
        other, changed = self.engine.recommend(**{**self.kwargs, "candidate_courses": self.candidates.iloc[::-1]}, batch_size=20)
        assert_frame_equal(plans, other)
        self.assertEqual(result["recommendations"], changed["recommendations"])
        _, override = self.engine.recommend(**self.kwargs, top_n=5)
        self.assertEqual(override["returned_plan_count"], 5)

    def test_projection_uses_prior_registered_credits_and_proposed_semester(self):
        snapshot = {k: v for k, v in self.snapshot.items() if k != "current_gpa_credits"}
        snapshot.update(prior_total_reg_credits=60, start_total_in_credits=30,
                        semester_reg_credits=18, gpa_points=0, end_agpa_points=0)
        _, result = self.engine.recommend(**{**self.kwargs, "student_snapshot": snapshot})
        self.assertEqual(result["current_gpa_credits"], 60)
        self.assertEqual(result["current_gpa_credits_source"], "snapshot.prior_total_reg_credits")
        for plan in result["recommendations"]:
            expected = (9 * 2.0 + 60 * 3.5) / (9 + 60)
            self.assertAlmostEqual(plan["projected_cumulative_gpa"], expected)
            self.assertNotAlmostEqual(plan["projected_cumulative_gpa"], (9 * 2.0 + 30 * 3.5) / (9 + 30))

    def test_one_two_and_no_matching_plans(self):
        for size in [1, 2]:
            _, result = self.engine.recommend(**{**self.kwargs, "candidate_courses": self.candidates.iloc[:size], "credits": 3})
            self.assertEqual(result["returned_plan_count"], size)
        with tempfile.TemporaryDirectory() as directory:
            result = save_recommendations(self.engine, directory, **{**self.kwargs, "credits": 100})
            self.assertTrue(pd.read_parquet(Path(directory) / "plans.parquet").empty)
            self.assertTrue(pd.read_parquet(Path(directory) / "courses.parquet").empty)
        self.assertEqual(result["status"], "no_matching_credit_plan")
        self.assertEqual(result["returned_plan_count"], 0)
        self.assertIsNone(result["best_projected_cumulative_gpa"])

    def test_snapshot_preserves_serving_only_denominator_and_history_validation(self):
        checked = validate_snapshot(self.snapshot, "S", "D", 20251)
        self.assertEqual(checked["current_gpa_credits"], 60)
        self.assertNotIn("current_gpa_credits", STUDENT_SNAPSHOT_COLUMNS)
        with self.assertRaisesRegex(ValueError, "cutoffs"):
            self.engine.specialty_history.as_of_part = 20251
            self.engine.recommend(**self.kwargs)


if __name__ == "__main__":
    unittest.main()
