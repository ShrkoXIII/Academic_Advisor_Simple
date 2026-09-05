import unittest

import pandas as pd

from src.experiment_degree_points import (
    SPECIALTY_HISTORY_FEATURES,
    add_specialty_history_features,
    fit_weights,
)


class SpecialtyHistoryTests(unittest.TestCase):
    def setUp(self):
        self.train = pd.DataFrame(
            {
                "part_id": [20211, 20211, 20221, 20221],
                "degree_id": ["A", "A", "A", "B"],
                "plan_requirement_type_id": ["R", "R", "R", "R"],
                "final_mark": [40.0, 80.0, 100.0, 50.0],
                "is_fail": [1, 0, 0, 0],
                "points": [0.0, 3.0, 4.0, 1.0],
                "course_credits": [2.0, 4.0, 3.0, 3.0],
            }
        )
        self.test = pd.DataFrame(
            {
                "part_id": [20231, 20232],
                "degree_id": ["A", "A"],
                "plan_requirement_type_id": ["R", "R"],
                "final_mark": [0.0, 100.0],
                "is_fail": [1, 0],
                "points": [0.0, 4.0],
                "course_credits": [3.0, 3.0],
            }
        )

    def test_current_part_does_not_enter_its_own_specialty_history(self):
        enriched_train, _ = add_specialty_history_features(self.train, self.test)
        first_part = enriched_train[enriched_train["part_id"].eq(20211)]
        self.assertTrue(first_part["degree_history_missing"].all())
        later_a = enriched_train[
            enriched_train["part_id"].eq(20221)
            & enriched_train["degree_id"].eq("A")
        ].iloc[0]
        self.assertAlmostEqual(later_a["degree_history_effective_support"], 0.5)

    def test_test_history_is_frozen_and_ignores_test_outcomes(self):
        _, enriched_test = add_specialty_history_features(self.train, self.test)
        for feature in SPECIALTY_HISTORY_FEATURES:
            self.assertEqual(enriched_test.iloc[0][feature], enriched_test.iloc[1][feature])

    def test_credit_weight_multiplies_temporal_weight(self):
        weights = fit_weights(self.train, credit_weighted=True)
        self.assertEqual(weights.tolist(), [0.5, 1.0, 3.0, 3.0])


if __name__ == "__main__":
    unittest.main()
