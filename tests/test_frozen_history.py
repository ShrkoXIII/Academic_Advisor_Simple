import copy
import json
from pathlib import Path
import pickle
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal

from src.features.feature_contract import FEATURE_ENGINEERING_VERSION
from src.experiments.specialty_history import FrozenSpecialtyHistory
from src.features.frozen_history import (
    build_frozen_history, file_sha256, load_frozen_history, save_frozen_history,
    validate_history_selection, verify_legacy_course_history,
)
from src.paths import (
    DEGREE_POINTS_SELECTED_MODEL_PATH, course_history_state_path, frozen_history_dir,
    history_metadata_path, specialty_history_state_path,
)
from src.recommendation import AcademicPlanRecommender
from src.features.temporal_features import save_course_history_state


def history_source():
    frame = pd.DataFrame({
        "student_course_id": ["old", "new", "future"],
        "part_id": [20243, 20251, 20252], "degree_id": ["D"] * 3,
        "course_id": ["A"] * 3, "faculty_id": ["F"] * 3,
        "plan_requirement_type_id": ["R"] * 3, "course_credits": [3.] * 3,
        "attempt_number": [1, 1, 1], "final_mark": [40., 80., 90.],
        "is_fail": [1, 0, 0], "points": [0., 3., 4.],
    })
    frame.attrs["feature_engineering_version"] = FEATURE_ENGINEERING_VERSION
    return frame


class FrozenHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = history_source()

    def save(self, part, *, specialty=False):
        bundle = build_frozen_history(
            self.source, part, finalized_through_part=part,
            specialty_history_type=FrozenSpecialtyHistory if specialty else None,
        )
        save_frozen_history(*bundle, root=self.root)
        return bundle

    def test_new_version_preserves_original_hashes_and_values(self):
        self.save(20243)
        before = {p.name: file_sha256(p) for p in frozen_history_dir(20243, self.root).iterdir()}
        old_course, old_specialty, _ = load_frozen_history(20243, root=self.root)
        self.save(20251)
        after = {p.name: file_sha256(p) for p in frozen_history_dir(20243, self.root).iterdir()}
        self.assertEqual(before, after)
        reloaded, specialty, _ = load_frozen_history(20243, root=self.root)
        newer, updated_specialty, _ = load_frozen_history(20251, root=self.root)
        self.assertEqual(reloaded.global_sums, old_course.global_sums)
        self.assertIsNone(old_specialty)
        self.assertIsNone(specialty)
        self.assertIsNone(updated_specialty)
        for level in old_course.tables:
            assert_frame_equal(reloaded.tables[level], old_course.tables[level])
        self.assertEqual(reloaded.global_sums["raw_count"], 1)
        self.assertEqual(newer.global_sums["raw_count"], 2)
        with self.assertRaises(FileExistsError):
            self.save(20243)
        self.assertEqual(before, {p.name: file_sha256(p) for p in frozen_history_dir(20243, self.root).iterdir()})

    def test_target_and_future_outcomes_cannot_enter_prefix(self):
        original = build_frozen_history(self.source, 20243, finalized_through_part=20243)
        poisoned = self.source.copy()
        poisoned.loc[poisoned.part_id.ge(20251), ["final_mark", "points", "is_fail"]] = float("nan")
        changed = build_frozen_history(poisoned, 20243, finalized_through_part=20243)
        self.assertEqual(original[0].global_sums, changed[0].global_sums)
        self.assertIsNone(original[1])
        self.assertIsNone(changed[1])
        self.assertEqual(original[2], changed[2])

    def test_prefix_fingerprint_survives_row_order_and_future_dtype_change(self):
        original = build_frozen_history(self.source, 20251, finalized_through_part=20251)
        reordered = self.source.iloc[[2, 1, 0]].reset_index(drop=True)
        reordered.loc[0, "part_id"] = 20252.0
        reordered.loc[0, "final_mark"] = 0.0
        changed = build_frozen_history(reordered, 20251, finalized_through_part=20251)
        self.assertEqual(original[2]["selected_source_sha256"], changed[2]["selected_source_sha256"])
        self.assertEqual(original[0].global_sums, changed[0].global_sums)

    def test_rejects_unfinalized_missing_cutoff_duplicate_and_invalid_source(self):
        with self.assertRaisesRegex(ValueError, "finalized"):
            build_frozen_history(self.source, 20251, finalized_through_part=20243)
        with self.assertRaisesRegex(ValueError, "exact requested"):
            build_frozen_history(self.source, 20253, finalized_through_part=20253)
        for changed in [pd.concat([self.source, self.source]), self.source.assign(final_mark=float("nan"))]:
            changed.attrs = self.source.attrs.copy()
            with self.assertRaises(ValueError):
                build_frozen_history(changed, 20243, finalized_through_part=20243)
        old_version = self.source.copy()
        old_version.attrs["feature_engineering_version"] = 1
        with self.assertRaises(ValueError):
            build_frozen_history(old_version, 20243, finalized_through_part=20243)

    def test_base_history_ignores_experimental_labels_but_specialty_requires_them(self):
        source = self.source.drop(columns=["is_fail", "points"])
        course, specialty, _ = build_frozen_history(source, 20243, finalized_through_part=20243)
        self.assertIsNone(specialty)
        self.assertEqual(course.global_sums["raw_count"], 1)
        with self.assertRaisesRegex(ValueError, "missing columns"):
            build_frozen_history(
                source, 20243, finalized_through_part=20243,
                specialty_history_type=FrozenSpecialtyHistory,
            )

    def test_invalid_prefix_values_are_rejected(self):
        changes = {
            "missing_id": ("student_course_id", None),
            "negative_credits": ("course_credits", -1),
            "zero_attempt": ("attempt_number", 0),
            "mark_over_100": ("final_mark", 101),
            "infinite_mark": ("final_mark", float("inf")),
            "invalid_part": ("part_id", 20244),
        }
        for name, (column, value) in changes.items():
            with self.subTest(name=name):
                changed = self.source.copy()
                changed.loc[0, column] = value
                with self.assertRaises(ValueError):
                    build_frozen_history(changed, 20243, finalized_through_part=20243)

    def test_history_selection_requires_explicit_stale_opt_in(self):
        for target, cutoff in [(20251, 20243), (20252, 20251), (20253, 20252)]:
            self.assertTrue(validate_history_selection(target, cutoff)["history_is_previous_part"])
        with self.assertRaisesRegex(ValueError, "older"):
            validate_history_selection(20252, 20243)
        self.assertFalse(validate_history_selection(20252, 20243, allow_older_history=True)["history_is_previous_part"])
        for cutoff in [20251, 20252]:
            with self.assertRaisesRegex(ValueError, "forbidden"):
                validate_history_selection(20251, cutoff, allow_older_history=True)
        for part in ["../20243", 20244, 20243.5]:
            with self.assertRaises(ValueError):
                course_history_state_path(part, self.root)

    def test_course_specialty_mismatch_refused_by_save_load_and_recommender(self):
        course, specialty, meta = self.save(20243, specialty=True)
        wrong = copy.deepcopy(specialty)
        wrong.as_of_part = 20251
        with self.assertRaisesRegex(ValueError, "cutoffs"):
            save_frozen_history(course, wrong, meta, root=self.root)
        with self.assertRaisesRegex(ValueError, "cutoffs"):
            AcademicPlanRecommender(None, None, {}, {}, course, wrong, {})
        path = specialty_history_state_path(20243, self.root)
        payload = pickle.loads(path.read_bytes())
        payload["as_of_part"] = 20251
        path.write_bytes(pickle.dumps(payload))
        metadata_path = history_metadata_path(20243, self.root)
        saved_meta = json.loads(metadata_path.read_text())
        saved_meta["artifact_sha256"][path.name] = file_sha256(path)
        metadata_path.write_text(json.dumps(saved_meta))
        with self.assertRaisesRegex(ValueError, "cutoffs"):
            load_frozen_history(20243, root=self.root, specialty_history_type=FrozenSpecialtyHistory)

    def test_optional_specialty_load_requires_matching_bundle(self):
        self.save(20243)
        with self.assertRaisesRegex(ValueError, "no specialty history"):
            load_frozen_history(20243, root=self.root, specialty_history_type=FrozenSpecialtyHistory)
        self.save(20251, specialty=True)
        course, specialty, _ = load_frozen_history(
            20251, root=self.root, specialty_history_type=FrozenSpecialtyHistory,
        )
        self.assertEqual(course.as_of_part, 20251)
        self.assertEqual(specialty.as_of_part, 20251)
        self.assertEqual(specialty.global_totals["global_history_points_sum"], 3)

    def test_hash_tampering_and_incomplete_bundle_are_rejected(self):
        self.save(20243)
        with course_history_state_path(20243, self.root).open("ab") as stream:
            stream.write(b"tampered")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            load_frozen_history(20243, root=self.root)
        frozen_history_dir(20251, self.root).mkdir()
        with self.assertRaises(FileNotFoundError):
            load_frozen_history(20251, root=self.root)
        with self.assertRaises(FileExistsError):
            self.save(20251)

    def test_legacy_migration_verifies_values_without_changing_original(self):
        course, specialty, metadata = build_frozen_history(self.source, 20243, finalized_through_part=20243)
        legacy = self.root / "legacy.pkl"
        save_course_history_state(course, legacy)
        before = file_sha256(legacy)
        old = verify_legacy_course_history(legacy, course)
        save_frozen_history(old, specialty, metadata, root=self.root)
        self.assertEqual(before, file_sha256(legacy))
        self.assertEqual(before, file_sha256(course_history_state_path(20243, self.root)))
        changed = copy.deepcopy(course)
        changed.global_sums["raw_count"] += 1
        with self.assertRaises(ValueError):
            verify_legacy_course_history(legacy, changed)


@unittest.skipUnless(DEGREE_POINTS_SELECTED_MODEL_PATH.exists(), "Local models unavailable")
class FrozenHistoryModelIntegrationTests(unittest.TestCase):
    def test_same_models_load_two_versions_without_reading_any_training_table(self):
        with tempfile.TemporaryDirectory() as root:
            for cutoff in [20243, 20251]:
                save_frozen_history(*build_frozen_history(
                    history_source(), cutoff, finalized_through_part=cutoff,
                    specialty_history_type=FrozenSpecialtyHistory,
                ), root=root)
            with patch("pandas.read_parquet", side_effect=AssertionError("Serving read a training table")):
                old = AcademicPlanRecommender.load(history_as_of_part=20243, history_root=root)
                new = AcademicPlanRecommender.load(history_as_of_part=20251, history_root=root)
            self.assertEqual(old.provenance["artifact_sha256"], new.provenance["artifact_sha256"])
            self.assertEqual(old.provenance["training"], new.provenance["training"])
            self.assertEqual(old.provenance["training"]["expected_points"]["training_as_of_part"], 20243)
            self.assertEqual((old.course_history.as_of_part, new.course_history.as_of_part), (20243, 20251))
            self.assertEqual(validate_history_selection(20251, old.course_history.as_of_part)["target_part"], 20251)
            self.assertEqual(validate_history_selection(20252, new.course_history.as_of_part)["target_part"], 20252)

    def test_selection_is_required_and_missing_version_is_not_rebuilt(self):
        with self.assertRaises(TypeError):
            AcademicPlanRecommender.load()
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(FileNotFoundError):
                AcademicPlanRecommender.load(history_as_of_part=20243, history_root=root)
            self.assertFalse(list(Path(root).iterdir()))


if __name__ == "__main__":
    unittest.main()
