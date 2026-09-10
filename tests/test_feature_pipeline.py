from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from build_temporal_features import build_feature_tables
from feature_contract import (
    CATEGORICAL_FEATURES, FEATURE_ENGINEERING_VERSION, MODEL_FEATURES,
    NUMERIC_FEATURES, require_current_features,
)
from src.experiments.degree_points import load_cached_validation, load_or_train_holdout
from src.experiments.specialty_history import SPECIALTY_HISTORY_FEATURES, add_specialty_history_features
from tests.test_temporal_features import semester_rows


class FeaturePipelineTests(unittest.TestCase):
    def test_poisoning_current_and_future_outcomes_leaves_all_features_unchanged(self):
        parts = [20231, 20232, 20241, 20242, 20251, 20252]
        status = semester_rows("S1", parts, [1.0, 2.0, 3.0, 4.0, 2.5, 3.5])
        rows = []
        for index, semester in status.iterrows():
            for course in ["C1", "C2"]:
                row = {column: 1.0 for column in NUMERIC_FEATURES}
                row.update({column: "A" for column in CATEGORICAL_FEATURES})
                row.update(semester.to_dict())
                row.update(
                    student_course_id=f"{index}-{course}", course_id=course,
                    faculty_id="F1", course_credits=3.0, attempt_number=1,
                    final_mark=40.0 + index * 10, points=index * 0.5,
                )
                rows.append(row)
        frame = pd.DataFrame(rows)
        # These columns must actually be engineered, not copied from a fixture.
        from temporal_features import COURSE_HISTORY_COLUMNS, PLAN_CONTEXT_COLUMNS, STUDENT_HISTORY_COLUMNS
        frame = frame.drop(columns=[*COURSE_HISTORY_COLUMNS, *PLAN_CONTEXT_COLUMNS, *STUDENT_HISTORY_COLUMNS])

        def build(source, history):
            train = source[source.part_id.lt(20251)].copy()
            test = source[source.part_id.ge(20251)].copy()
            train, test, _ = build_feature_tables(train, test, train.copy(), test.copy(), history)
            return add_specialty_history_features(train, test)

        original = build(frame, status)
        for cutoff in [20232, 20251, 20252]:
            changed = frame.copy()
            changed_status = status.copy()
            changed.loc[changed.part_id.ge(cutoff), ["final_mark", "points"]] = [0, 0]
            changed_status.loc[
                changed_status.part_id.ge(cutoff),
                ["gpa_points", "semester_fail_courses", "semester_fail_credits", "reg_total_semesters"],
            ] = [0, 5, 15, 0]
            updated = build(changed, changed_status)
            for before, after in zip(original, updated):
                columns = [*MODEL_FEATURES, *SPECIALTY_HISTORY_FEATURES]
                assert_frame_equal(
                    before.loc[before.part_id.le(cutoff), columns],
                    after.loc[after.part_id.le(cutoff), columns],
                )

    def test_feature_version_survives_parquet_projection_and_rejects_old_models(self):
        with self.assertRaisesRegex(ValueError, "Stale feature engineering"):
            require_current_features({})
        frame = pd.DataFrame({"value": [1]})
        frame.attrs["feature_engineering_version"] = FEATURE_ENGINEERING_VERSION
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "features.parquet"
            frame.to_parquet(path)
            restored = pd.read_parquet(path, columns=["value"])
        require_current_features(restored.attrs)


class ExperimentCacheTests(unittest.TestCase):
    def test_validation_cache_rejects_old_or_different_feature_data(self):
        cached = pd.DataFrame({"variant": ["baseline"], "validation_year": [2023]})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "validation.parquet"
            with patch("src.experiments.degree_points.DEGREE_POINTS_VALIDATION_PATH", path):
                cached.to_parquet(path)
                self.assertEqual(load_cached_validation("new"), ([], set()))
                cached.assign(experiment_signature="old").to_parquet(path)
                self.assertEqual(load_cached_validation("new"), ([], set()))
                cached.assign(experiment_signature="new").to_parquet(path)
                self.assertEqual(load_cached_validation("new")[1], {("baseline", 2023)})

    def test_changed_features_force_holdout_retraining(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.json"
            path.write_text(json.dumps({
                "feature_engineering_version": FEATURE_ENGINEERING_VERSION,
                "experiment_signature": "old", "selected_variant": {"name": "winner"},
            }))
            with (
                patch("src.experiments.degree_points.DEGREE_POINTS_EXPERIMENT_METADATA_PATH", path),
                patch("src.experiments.degree_points.evaluate_selected_holdout", return_value=(None, "courses", "plans", "metrics")) as fit,
            ):
                result = load_or_train_holdout(None, None, {"name": "winner"}, 10, {}, None, "new")
                self.assertEqual(result, ("courses", "plans", "metrics"))
                fit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
