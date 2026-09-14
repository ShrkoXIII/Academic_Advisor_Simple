from pathlib import Path
import sys
import unittest

import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from grade_scale import GradeScale  # noqa: E402
from src.recommendation import (  # noqa: E402
    enumerate_plan_indices,
    summarize_scored_plans,
)


class GradeScaleTests(unittest.TestCase):
    def test_predicted_mark_uses_official_pass_band_thresholds(self):
        scale = GradeScale(
            pd.DataFrame(
                {
                    "grade_version_id": [3.111, 3.111],
                    "from_percent": [50, 60],
                    "points": [1.5, 2.0],
                    "grade_show": ["D", "C-"],
                }
            )
        )
        points, labels = scale.convert(
            [49.9, 50.0, 59.9, 60.0],
            [3.111, 3.111, 3.111, 3.111],
        )

        self.assertEqual(points.tolist(), [0.0, 1.5, 1.5, 2.0])
        self.assertEqual(labels.tolist(), ["F", "D", "D", "C-"])


class PlanEnumerationTests(unittest.TestCase):
    def test_exact_credits_allow_different_course_counts(self):
        candidates = pd.DataFrame(
            {
                "course_id": ["A", "B", "C"],
                "course_credits": [3.0, 3.0, 6.0],
            }
        )
        plans = enumerate_plan_indices(
            candidates,
            target_credits=6,
        )

        self.assertEqual(set(plans), {(2,), (0, 1)})

    def test_ranking_uses_gpa_then_failure_without_risk_exclusion(self):
        scored = pd.DataFrame(
            {
                "plan_id": [0, 0, 1],
                "course_id": ["A", "B", "C"],
                "course_credits": [3.0, 3.0, 6.0],
                "expected_points": [4.0, 3.0, 3.5],
                "predicted_mark": [95.0, 85.0, 90.0],
                "fail_probability": [0.2, 0.2, 0.1],
                "plan_credit_weighted_fail_rate": [0.3, 0.3, 0.2],
                "plan_credit_weighted_avg_mark": [70.0, 70.0, 80.0],
                "plan_difficulty_credit_load": [1.8, 1.8, 1.2],
            }
        )
        summaries = summarize_scored_plans(
            scored,
            current_gpa=2.5,
        )

        self.assertEqual(summaries["plan_id"].tolist(), [1, 0])
        self.assertAlmostEqual(summaries.loc[0, "expected_quality_points"], 21.0)
        self.assertAlmostEqual(summaries.loc[0, "expected_failed_credits"], 0.6)
        self.assertAlmostEqual(summaries.loc[0, "expected_plan_gpa"], 3.5)

        risk_filtered = summarize_scored_plans(
            scored,
            current_gpa=3.5,
        )
        self.assertTrue(risk_filtered.empty)


if __name__ == "__main__":
    unittest.main()
