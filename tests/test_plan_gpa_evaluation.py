from pathlib import Path
import sys
import unittest

import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evaluate_plan_gpa import aggregate_plan_gpa, summarize_plan_errors  # noqa: E402


class PlanGpaEvaluationTests(unittest.TestCase):
    def test_plan_gpa_uses_credit_weighted_points(self):
        courses = pd.DataFrame(
            {
                "student_id": ["S1", "S1"],
                "degree_id": ["D1", "D1"],
                "part_id": [20251, 20251],
                "course_id": ["C1", "C2"],
                "course_credits": [3.0, 2.0],
                "actual_quality_points": [12.0, 3.0],
                "predicted_quality_points": [10.5, 4.0],
                "source_semester_gpa": [3.0, 3.0],
            }
        )
        plans = aggregate_plan_gpa(courses)
        metrics = summarize_plan_errors(plans)

        self.assertAlmostEqual(plans.loc[0, "actual_plan_gpa"], 3.0)
        self.assertAlmostEqual(plans.loc[0, "predicted_plan_gpa"], 2.9)
        self.assertAlmostEqual(plans.loc[0, "plan_gpa_error"], -0.1)
        self.assertAlmostEqual(metrics["mae"], 0.1)
        self.assertAlmostEqual(metrics["bias"], -0.1)


if __name__ == "__main__":
    unittest.main()
