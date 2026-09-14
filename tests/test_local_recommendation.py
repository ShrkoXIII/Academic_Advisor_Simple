from decimal import Decimal
from itertools import combinations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from src.recommendation import (
    AcademicPlanRecommender, STUDENT_SNAPSHOT_COLUMNS, build_plan_rows,
    enumerate_plan_indices, resolve_credit_bounds, summarize_scored_plans,
)
from src.recommendation_inputs import (
    CandidateImportError, normalize_candidates, read_candidate_file,
    build_student_snapshot, validate_snapshot,
)
from src.recommendation_output import save_recommendations
from src.experiments.specialty_history import FrozenSpecialtyHistory, add_specialty_history_features, SPECIALTY_HISTORY_FEATURES
from src.paths import (
    DEGREE_POINTS_SELECTED_MODEL_PATH, TEMPORAL_TEST_FEATURES_PATH,
    TEMPORAL_TRAIN_FEATURES_PATH, DEGREE_POINTS_HOLDOUT_COURSES_PATH,
    TEMPORAL_TEST_ROSTER_PATH, CLEAN_STUDENT_COURSE_PATH, CLEAN_STUDENT_DIPLOMA_PATH,
    STUDENT_STATUS_PATH,
)
from src.clean_student_status import clean_student_status


class EnumerationTests(unittest.TestCase):
    def test_exhaustive_oracle_fractional_zero_and_variable_count(self):
        for credits in [[2, 3, 4.5, 1.5, 6, 0], [0.1, 0.2, 0.3], [2, 2, 3, 3, 3], []]:
            for target in [0.3, 4.5, 6, 18]:
                expected = set()
                for size in range(1, len(credits) + 1):
                    for subset in combinations(range(len(credits)), size):
                        if sum(Decimal(str(credits[i])) for i in subset) == Decimal(str(target)):
                            expected.add(subset)
                actual = list(enumerate_plan_indices(pd.DataFrame({"course_credits": credits}), target))
                self.assertEqual(set(actual), expected)
                self.assertEqual(len(actual), len(set(actual)))

    def test_single_value_is_exact_and_range_keeps_both_bounds(self):
        self.assertEqual(resolve_credit_bounds(min_credits=12, max_credits=18), (12, 18))
        self.assertEqual(resolve_credit_bounds(credits=18), (18, 18))
        for kw in [{"credits": 18, "max_credits": 18}, {"min_credits": 19, "max_credits": 18}, {"credits": 0}]:
            with self.assertRaises(ValueError):
                resolve_credit_bounds(**kw)

    def test_inclusive_range_matches_exhaustive_oracle(self):
        for credits in [[2, 3, 4.5, 1.5, 6, 0], [0.1, 0.2, 0.3], [0, 0], []]:
            for lower, upper in [(0, 3), (0.1, 0.3), (3, 6), (4.5, 7.5), (6, 6), (12, 18)]:
                expected = set()
                for size in range(1, len(credits) + 1):
                    for subset in combinations(range(len(credits)), size):
                        total = sum(Decimal(str(credits[i])) for i in subset)
                        if Decimal(str(lower)) <= total <= Decimal(str(upper)) and total > 0:
                            expected.add(subset)
                actual = list(enumerate_plan_indices(pd.DataFrame({"course_credits": credits}),
                                                    min_credits=lower, max_credits=upper))
                self.assertEqual(set(actual), expected)
                self.assertEqual(len(actual), len(expected))

    def test_range_accepts_interior_when_upper_is_unreachable(self):
        courses = pd.DataFrame({"course_credits": [2, 2]})
        self.assertEqual(list(enumerate_plan_indices(courses, min_credits=3, max_credits=5)), [(0, 1)])
        self.assertEqual(list(enumerate_plan_indices(courses, target_credits=5)), [])

    def test_mixed_credit_totals_rank_by_gpa_not_quality_point_sum(self):
        rows = pd.DataFrame({"plan_id": [0, 1], "course_id": ["A", "B"],
                             "course_credits": [12., 18.], "expected_points": [3.5, 3.0],
                             "fail_probability": [0.1, 0.1]})
        self.assertEqual(summarize_scored_plans(rows, 2.5).plan_id.tolist(), [0, 1])

    def test_gpa_strict_threshold_and_risk_only_tiebreak(self):
        rows = pd.DataFrame({"plan_id": [0, 1, 2, 3], "course_id": list("ABCD"),
                             "course_credits": [3.] * 4, "expected_points": [2.5, 2.50000001, 3, 3],
                             "fail_probability": [0, 1, 0.5, 0.1]})
        result = summarize_scored_plans(rows, 2.5)
        self.assertEqual(result.plan_id.tolist(), [3, 2, 1])


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.catalog = pd.DataFrame({"degree_id": ["D"] * 3, "course_id": list("ABC"),
            "course_credits": [2., 3., 4.5], "course_name_sl": list("abc"),
            "course_type_id": ["T"] * 3, "requirement_type_id": ["R"] * 3,
            "year_order": [1] * 3, "semester_order": [1] * 3, "credits_count": [120] * 3})
        self.history = pd.DataFrame({"student_id": ["S"] * 3, "course_id": ["A"] * 3,
            "part_id": [20241, 20251, 20261], "attempt_number": [1, 2, 3]})

    def normalize(self, raw):
        return normalize_candidates(raw, self.catalog, self.history, "S ", "D", 20251)

    def test_company_filter_ids_duplicates_and_prior_attempt(self):
        raw = pd.DataFrame({"STUDENT_ID": ["S ", "S", "S", "X"], "COURSE_ID": ["A ", "A", "B", "C"],
            "COURSE_CREDITS": [2, 2, 3, 4.5], "IS_REQUESTABLE": ["Y", "Y", "N", "Y"]})
        rows, report = self.normalize(raw)
        self.assertEqual(rows.course_id.tolist(), ["A"])
        self.assertEqual(rows.attempt_number.tolist(), [2])
        self.assertEqual(report["duplicate_rows_removed"], 1)
        self.assertEqual(report["filtered_rows"], 2)

    def test_conflicts_missing_catalog_wrong_part_fail_explicitly(self):
        for raw in [
            pd.DataFrame({"course_id": ["A", "A"], "course_credits": [2, 3]}),
            pd.DataFrame({"course_id": ["A"], "course_credits": [3]}),
            pd.DataFrame({"course_id": ["Z"], "course_credits": [2]}),
            pd.DataFrame({"course_id": ["A"], "course_credits": [2], "part_id": [20241]}),
        ]:
            with self.assertRaises(CandidateImportError) as ctx:
                self.normalize(raw)
            self.assertTrue(ctx.exception.report["errors"])

    def test_json_and_parquet_same_and_empty_list(self):
        with tempfile.TemporaryDirectory() as d:
            raw = pd.DataFrame({"course_id": ["A", "C"], "course_credits": [2., 4.5]})
            jp, pp = Path(d) / "courses.json", Path(d) / "courses.parquet"
            jp.write_text(raw.to_json(orient="records"))
            raw.to_parquet(pp)
            a, _ = self.normalize(read_candidate_file(jp))
            b, _ = self.normalize(read_candidate_file(pp))
            assert_frame_equal(a, b)
            jp.write_text("[]")
            empty, _ = self.normalize(read_candidate_file(jp))
            self.assertTrue(empty.empty)


@unittest.skipUnless(DEGREE_POINTS_SELECTED_MODEL_PATH.exists(), "Local model artifacts unavailable")
class ArtifactLoadTests(unittest.TestCase):
    def test_load_succeeds_from_real_artifacts(self):
        engine = AcademicPlanRecommender.load(num_threads=2)
        train_parts = pd.read_parquet(TEMPORAL_TRAIN_FEATURES_PATH, columns=["part_id"])
        expected_cutoff = int(train_parts.part_id.max())
        self.assertEqual(engine.course_history.as_of_part, expected_cutoff)
        self.assertEqual(engine.specialty_history.as_of_part, expected_cutoff)
        self.assertGreater(engine.points_model.num_trees(), 0)
        self.assertGreater(engine.fail_model.num_trees(), 0)


@unittest.skipUnless(DEGREE_POINTS_SELECTED_MODEL_PATH.exists() and TEMPORAL_TEST_FEATURES_PATH.exists(), "Local model/data artifacts unavailable")
class ArtifactIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = AcademicPlanRecommender.load(num_threads=2)
        cls.test = pd.read_parquet(TEMPORAL_TEST_FEATURES_PATH)
        cls.roster = pd.read_parquet(TEMPORAL_TEST_ROSTER_PATH)
        keys = ["student_id", "degree_id", "part_id"]
        # A complete observed roster ensures parity; actual labels exist for every course.
        sizes = cls.test.groupby(keys).size().rename("targets").to_frame().join(cls.roster.groupby(keys).size().rename("roster"))
        key = sizes[(sizes.targets == sizes.roster) & sizes.targets.ge(5)].index[0]
        mask = np.logical_and.reduce([cls.test[c].eq(v).to_numpy() for c, v in zip(keys, key)])
        cls.actual = cls.test[mask].copy().sort_values("course_id").reset_index(drop=True)
        cls.snapshot = cls.actual.iloc[0][[*STUDENT_SNAPSHOT_COLUMNS, "part_id"]].to_dict()
        cls.candidates = cls.actual.copy()
        cls.candidates["course_name"] = cls.candidates["course_name_sl"]
        cls.part = int(cls.snapshot["part_id"])

    def test_local_cli_without_snapshot(self):
        candidates = self.candidates.loc[self.candidates.course_credits.gt(0)].iloc[:3]
        credits = float(candidates.course_credits.sum())
        with tempfile.TemporaryDirectory() as directory:
            candidate_path = Path(directory) / "candidates.parquet"
            output = Path(directory) / "result"
            candidates[["course_id", "course_credits"]].to_parquet(candidate_path, index=False)
            completed = subprocess.run(
                [sys.executable, "-m", "src.recommend_local",
                 "--candidates", str(candidate_path),
                 "--student-id", str(self.snapshot["student_id"]),
                 "--degree-id", str(self.snapshot["degree_id"]),
                 "--part-id", str(self.part), "--credits", str(credits),
                 "--threads", "2", "--output-dir", str(output)],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True, text=True, encoding="utf-8", timeout=60,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            result = json.loads((output / "result.json").read_text(encoding="utf-8"))
            snapshot = json.loads((output / "snapshot.json").read_text(encoding="utf-8"))
            expected_snapshot = validate_snapshot(
                self.snapshot, self.snapshot["student_id"], self.snapshot["degree_id"], self.part,
            )
            columns = [*STUDENT_SNAPSHOT_COLUMNS, "part_id"]
            assert_frame_equal(pd.DataFrame([snapshot])[columns],
                               pd.DataFrame([expected_snapshot])[columns], check_dtype=False)
            self.assertEqual(result["current_gpa"], self.snapshot["start_agpa_points"])
            self.assertEqual(result["matching_plan_count"], 1)
            expected, summary = self.engine.recommend(
                expected_snapshot, candidates, self.part, self.snapshot["start_agpa_points"],
                credits=credits,
            )
            self.assertEqual(result["status"], summary["status"])
            assert_frame_equal(pd.read_parquet(output / "plans.parquet"), expected)
            courses = pd.read_parquet(output / "courses.parquet")
            self.assertEqual(len(courses), len(expected) * len(candidates))

    def test_saved_prediction_and_feature_parity(self):
        prepared = self.engine.prepare_candidates(self.snapshot, self.candidates, self.part)
        scored = self.engine.score_rows(build_plan_rows(prepared, [tuple(range(len(prepared)))]))
        saved = pd.read_parquet(DEGREE_POINTS_HOLDOUT_COURSES_PATH)
        expected = self.actual[["student_course_id", "course_id"]].merge(saved[["student_course_id", "predicted_points"]], on="student_course_id").sort_values("course_id")
        np.testing.assert_allclose(scored.expected_points, expected.predicted_points, atol=1e-10, rtol=0)
        from src.temporal_features import COURSE_HISTORY_COLUMNS, PLAN_CONTEXT_COLUMNS
        for c in [*COURSE_HISTORY_COLUMNS, *PLAN_CONTEXT_COLUMNS]:
            np.testing.assert_allclose(scored[c].astype(float), self.actual[c].astype(float), atol=1e-10, equal_nan=True)

    def test_batch_order_empty_and_export(self):
        kwargs = dict(student_snapshot=self.snapshot, candidate_courses=self.candidates,
                      part_id=self.part, current_gpa=0, credits=float(self.candidates.course_credits.iloc[:2].sum()))
        sink = []
        plans, result = self.engine.recommend(**kwargs, batch_size=1, course_sink=lambda x: sink.append(x.copy()))
        other, _ = self.engine.recommend(**{**kwargs, "candidate_courses": self.candidates.iloc[::-1]}, batch_size=2000)
        assert_frame_equal(plans, other)
        self.assertGreater(result["matching_plan_count"], 0)
        with tempfile.TemporaryDirectory() as d:
            saved = save_recommendations(self.engine, d, **kwargs)
            assert_frame_equal(pd.read_parquet(Path(d) / "plans.parquet"), plans)
            self.assertEqual(len(pd.read_parquet(Path(d) / "courses.parquet")), sum(len(x) for x in sink))
            self.assertEqual(saved["recommendations"], result["recommendations"])
        for change, expected_status in [({"credits": 9999}, "no_matching_credit_plan"),
                                       ({"candidate_courses": self.candidates.iloc[:0]}, "no_matching_credit_plan"),
                                       ({"current_gpa": 4}, "no_plan_above_current_gpa")]:
            with tempfile.TemporaryDirectory() as d:
                empty = save_recommendations(self.engine, d, **{**kwargs, **change})
                self.assertEqual(empty["status"], expected_status)
                self.assertTrue(pd.read_parquet(Path(d) / "courses.parquet").empty)

    def test_range_export_and_batch_order_preserve_all_feasible_subsets(self):
        candidates = self.candidates.iloc[:3].copy()
        candidates["course_credits"] = [2., 3., 4.5]
        kwargs = dict(student_snapshot=self.snapshot, candidate_courses=candidates,
                      part_id=self.part, current_gpa=0, min_credits=3, max_credits=6.5)
        expected_count = len(list(enumerate_plan_indices(candidates, min_credits=3, max_credits=6.5)))
        plans, result = self.engine.recommend(**kwargs, batch_size=1)
        self.assertEqual(result["matching_plan_count"], expected_count)
        self.assertEqual((result["min_credits"], result["max_credits"]), (3, 6.5))
        self.assertIsNone(result["target_credits"])
        self.assertTrue(plans.total_credits.between(3, 6.5).all())
        self.assertGreater(plans.total_credits.nunique(), 1)
        with tempfile.TemporaryDirectory() as d:
            saved = save_recommendations(self.engine, d, **{**kwargs, "candidate_courses": candidates.iloc[::-1]}, batch_size=2000)
            assert_frame_equal(pd.read_parquet(Path(d) / "plans.parquet"), plans)
            self.assertEqual(saved["recommendations"], result["recommendations"])

    def test_supplied_outcomes_cannot_override_context(self):
        baseline = self.engine.prepare_candidates(self.snapshot, self.candidates, self.part)
        changed = self.candidates.assign(final_mark=0, points=0, course_history_avg_mark=0, plan_total_credits=999)
        modified = self.engine.prepare_candidates(self.snapshot, changed, self.part)
        assert_frame_equal(baseline, modified)
        with self.assertRaisesRegex(ValueError, "follow frozen"):
            self.engine.prepare_candidates(self.snapshot, self.candidates, 20241)

    def test_missing_gpa_and_mismatched_snapshot_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "known current_gpa"):
            self.engine.recommend(self.snapshot, self.candidates, self.part, None, credits=18)
        for change in [{"student_id": None}, {"degree_id": "wrong"}, {"part_id": self.part + 1}]:
            with self.assertRaises(ValueError):
                validate_snapshot({**self.snapshot, **change}, self.snapshot["student_id"],
                                  self.snapshot["degree_id"], self.part)

    def test_frozen_specialty_matches_experiment_and_ignores_future(self):
        train = pd.read_parquet(TEMPORAL_TRAIN_FEATURES_PATH)
        _, expected = add_specialty_history_features(train, self.actual)
        predicted = self.engine.specialty_history.apply(self.actual)
        for c in SPECIALTY_HISTORY_FEATURES:
            np.testing.assert_allclose(predicted[c].astype(float), expected[c].astype(float), equal_nan=True)
        changed = self.engine.specialty_history.apply(self.actual.assign(points=4, final_mark=100, is_fail=0))
        assert_frame_equal(predicted[SPECIALTY_HISTORY_FEATURES], changed[SPECIALTY_HISTORY_FEATURES])

    def test_snapshot_ignores_current_future_outcomes(self):
        status = clean_student_status(pd.read_parquet(STUDENT_STATUS_PATH))
        history = pd.read_parquet(CLEAN_STUDENT_COURSE_PATH)
        diplomas = pd.read_parquet(CLEAN_STUDENT_DIPLOMA_PATH)
        args = [self.snapshot["student_id"], self.snapshot["degree_id"], self.part]
        original = build_student_snapshot(status, history, diplomas, *args)
        columns = [*STUDENT_SNAPSHOT_COLUMNS, "part_id"]
        assert_frame_equal(pd.DataFrame([original])[columns],
                           pd.DataFrame([self.snapshot])[columns], check_dtype=False)
        changed = status.copy()
        mask = changed.part_id.ge(self.part)
        for c in ["gpa_points", "end_agpa_points", "end_total_in_courses", "end_total_in_credits", "semester_pass_courses", "semester_fail_courses", "reg_total_semesters"]:
            changed.loc[mask, c] = 0
        updated = build_student_snapshot(changed, history, diplomas, *args)
        assert_frame_equal(pd.DataFrame([original]), pd.DataFrame([updated]))
        validate_snapshot(original, *args)


if __name__ == "__main__":
    unittest.main()
