from decimal import Decimal
from itertools import combinations
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from src.recommendation import (
    AcademicPlanRecommender, build_plan_rows,
    enumerate_plan_indices, resolve_credit_bounds, summarize_scored_plans,
)
from src.recommendation.inputs import (
    CandidateImportError, normalize_candidates, read_candidate_file,
    build_student_snapshot, validate_snapshot,
)
from src.recommendation.output import save_recommendations
from src.features.feature_contract import BASE_FEATURES, LEAKAGE_COLUMNS
from src.features.temporal_features import COURSE_HISTORY_COLUMNS, PLAN_CONTEXT_COLUMNS, compute_plan_context_features
from src.recommendation import local_cli
from tests.recommendation_fixtures import synthetic_engine, synthetic_snapshot, synthetic_candidates


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

    def test_range_uses_upper_exact_with_decimal_zero_and_variable_count(self):
        for credits in [[2, 3, 4.5, 1.5, 6, 0], [0.1, 0.2, 0.3], [0, 0], []]:
            for lower, upper in [(0, 3), (0.1, 0.3), (3, 6), (4.5, 7.5), (6, 6), (12, 18)]:
                expected = set()
                for size in range(1, len(credits) + 1):
                    for subset in combinations(range(len(credits)), size):
                        total = sum(Decimal(str(credits[i])) for i in subset)
                        if total == Decimal(str(upper)) and total > 0:
                            expected.add(subset)
                actual = list(enumerate_plan_indices(pd.DataFrame({"course_credits": credits}),
                                                    min_credits=lower, max_credits=upper))
                self.assertEqual(set(actual), expected)
                self.assertEqual(len(actual), len(expected))

    def test_range_rejects_interior_when_upper_is_unreachable(self):
        courses = pd.DataFrame({"course_credits": [2, 2]})
        self.assertEqual(list(enumerate_plan_indices(courses, min_credits=3, max_credits=5)), [])
        self.assertEqual(list(enumerate_plan_indices(courses, target_credits=5)), [])

    def test_mixed_credit_totals_rank_by_gpa_not_quality_point_sum(self):
        rows = pd.DataFrame({"plan_id": [0, 1], "course_id": ["A", "B"],
                             "course_credits": [12., 18.], "expected_points": [3.5, 3.0],
                             "fail_probability": [0.1, 0.1], "attempt_number": [1, 1]})
        self.assertEqual(summarize_scored_plans(rows, 2.5, 60).plan_id.tolist(), [0, 1])

    def test_gpa_improvement_flag_and_risk_only_tiebreak(self):
        rows = pd.DataFrame({"plan_id": [0, 1, 2, 3], "course_id": list("ABCD"),
                             "course_credits": [3.] * 4, "expected_points": [2.5, 2.50000001, 3, 3],
                             "fail_probability": [0, 1, 0.5, 0.1], "attempt_number": [1] * 4})
        result = summarize_scored_plans(rows, 2.5, 60)
        self.assertEqual(result.plan_id.tolist(), [3, 2, 1, 0])
        self.assertEqual(result.is_expected_cumulative_improvement.tolist(), [True, True, True, False])


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


class SyntheticIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = synthetic_engine()
        self.snapshot = synthetic_snapshot()
        self.candidates = synthetic_candidates()
        self.part = 20251

    def test_local_cli_without_snapshot_uses_synthetic_inputs_and_mock_models(self):
        candidates = self.candidates.iloc[:3]
        kwargs = dict(student_snapshot=self.snapshot, candidate_courses=candidates,
                      part_id=self.part, current_gpa=self.snapshot["start_agpa_points"], credits=9)
        expected, summary = self.engine.recommend(**kwargs)
        with tempfile.TemporaryDirectory() as directory:
            candidate_path = Path(directory) / "candidates.json"
            candidate_path.write_text(candidates[["course_id", "course_credits"]].to_json(orient="records"))
            output = Path(directory) / "result"
            argv = ["recommend_local", "--candidates", str(candidate_path), "--student-id", "S",
                    "--degree-id", "D", "--part-id", "20251", "--credits", "9",
                    "--history-as-of-part", "20243", "--threads", "2", "--output-dir", str(output)]
            with (
                    patch.object(sys, "argv", argv), patch.object(local_cli, "load_local_inputs",
                    return_value=(candidates, self.snapshot, {"errors": [], "warnings": []})) as inputs,
                    patch.object(AcademicPlanRecommender, "load", return_value=self.engine) as loader,
            ):
                local_cli.main()
            inputs.assert_called_once_with(candidate_path, "S", "D", 20251, None)
            loader.assert_called_once_with(history_as_of_part=20243, num_threads=2)
            result = json.loads((output / "result.json").read_text())
            snapshot = json.loads((output / "snapshot.json").read_text())
            assert_frame_equal(pd.DataFrame([snapshot]), pd.DataFrame([self.snapshot]), check_dtype=False)
            self.assertEqual(result["current_gpa"], self.snapshot["start_agpa_points"])
            self.assertEqual(result["current_gpa_credits"], 60)
            self.assertEqual(result["current_gpa_credits_source"], "snapshot.prior_total_reg_credits")
            self.assertEqual(result["matching_plan_count"], 1)
            self.assertEqual(result["recommendations"], summary["recommendations"])
            assert_frame_equal(pd.read_parquet(output / "plans.parquet"), expected)
            courses = pd.read_parquet(output / "courses.parquet")
            self.assertEqual(len(courses), 3)
            self.assertEqual(courses.expected_points.tolist(), [2.] * 3)
            self.assertEqual(courses.predicted_mark.tolist(), [60.] * 3)
            self.assertEqual(courses.expected_grade.tolist(), ["C"] * 3)

    def test_official_matrix_and_course_context_parity(self):
        prepared = self.engine.prepare_candidates(self.snapshot, self.candidates, self.part)
        plan_rows = build_plan_rows(prepared, [tuple(range(len(prepared)))])
        expected_context = compute_plan_context_features(plan_rows, group_columns=["plan_id"])
        scored = self.engine.score_rows(plan_rows)
        np.testing.assert_allclose(scored.expected_points, 2.)
        np.testing.assert_allclose(scored.predicted_mark, 60.)
        self.assertEqual(scored.expected_grade.tolist(), ["C"] * len(scored))
        np.testing.assert_allclose(scored[PLAN_CONTEXT_COLUMNS].astype(float),
                                   expected_context.astype(float), equal_nan=True)
        np.testing.assert_allclose(scored[COURSE_HISTORY_COLUMNS].astype(float),
                                   prepared[COURSE_HISTORY_COLUMNS].astype(float), equal_nan=True)
        grade_matrix = self.engine.grade_model.matrices[-1]
        assert_frame_equal(grade_matrix, self.engine.fail_model.matrices[-1])
        self.assertEqual(grade_matrix.columns.tolist(), BASE_FEATURES)
        self.assertFalse(set(LEAKAGE_COLUMNS) & set(grade_matrix.columns))

    def test_batch_order_empty_and_export(self):
        kwargs = dict(student_snapshot=self.snapshot, candidate_courses=self.candidates,
                      part_id=self.part, current_gpa=0, current_gpa_credits=60, credits=6)
        sink = []
        plans, result = self.engine.recommend(**kwargs, batch_size=1, course_sink=lambda x: sink.append(x.copy()))
        other, _ = self.engine.recommend(**{**kwargs, "candidate_courses": self.candidates.iloc[::-1]}, batch_size=2000)
        assert_frame_equal(plans, other)
        self.assertEqual(result["matching_plan_count"], 15)
        with tempfile.TemporaryDirectory() as directory:
            saved = save_recommendations(self.engine, directory, **kwargs)
            assert_frame_equal(pd.read_parquet(Path(directory) / "plans.parquet"), plans)
            self.assertEqual(len(pd.read_parquet(Path(directory) / "courses.parquet")), sum(len(x) for x in sink))
            self.assertEqual(saved["recommendations"], result["recommendations"])
        for change in [{"credits": 9999}, {"candidate_courses": self.candidates.iloc[:0]}]:
            with tempfile.TemporaryDirectory() as directory:
                empty = save_recommendations(self.engine, directory, **{**kwargs, **change})
                self.assertEqual(empty["status"], "no_matching_credit_plan")
                self.assertTrue(pd.read_parquet(Path(directory) / "courses.parquet").empty)
                self.assertTrue(pd.read_parquet(Path(directory) / "plans.parquet").empty)
        preserved, high_gpa = self.engine.recommend(**{**kwargs, "current_gpa": 4})
        self.assertEqual(high_gpa["status"], "ok")
        self.assertEqual(len(preserved), result["matching_plan_count"])
        self.assertFalse(high_gpa["has_expected_improvement"])

    def test_range_export_and_batch_order_use_upper_exact(self):
        candidates = self.candidates.iloc[:3].copy()
        candidates["course_credits"] = [2., 3., 4.5]
        kwargs = dict(student_snapshot=self.snapshot, candidate_courses=candidates,
                      part_id=self.part, current_gpa=0, current_gpa_credits=60,
                      min_credits=3, max_credits=6.5)
        plans, result = self.engine.recommend(**kwargs, batch_size=1)
        self.assertEqual(result["matching_plan_count"], 1)
        self.assertEqual((result["min_credits"], result["max_credits"]), (3, 6.5))
        self.assertEqual((result["requested_min_credits"], result["requested_max_credits"]), (3, 6.5))
        self.assertEqual(result["target_credits"], 6.5)
        self.assertEqual(result["credit_policy"], "upper_bound_exact")
        self.assertEqual(plans.total_credits.tolist(), [6.5])
        with tempfile.TemporaryDirectory() as directory:
            saved = save_recommendations(self.engine, directory,
                    **{**kwargs, "candidate_courses": candidates.iloc[::-1]}, batch_size=2000)
            assert_frame_equal(pd.read_parquet(Path(directory) / "plans.parquet"), plans)
            self.assertEqual(saved["recommendations"], result["recommendations"])
        _, no_upper = self.engine.recommend(**{**kwargs, "max_credits": 6})
        self.assertEqual(no_upper["matching_plan_count"], 0)

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
                validate_snapshot({**self.snapshot, **change}, "S", "D", self.part)

    def test_snapshot_ignores_current_future_outcomes(self):
        status = pd.DataFrame([
            {**self.snapshot, "student_status_id": str(part), "part_id": part, "gpa_points": gpa,
             "last_enrolled_gpa": np.nan, "semester_reg_courses": 3, "total_reg_courses": 20,
             "total_reg_credits": 60., "total_fail_courses": 1, "total_fail_credits": 3.,
             "reg_total_semesters": index + 1, "end_agpa_points": gpa,
             "end_total_in_courses": 99, "end_total_in_credits": 999, "semester_pass_courses": 2,
             "semester_fail_courses": 1}
            for index, (part, gpa) in enumerate([(20242, 2.), (20243, 3.), (20251, 4.), (20252, 1.)])
        ])
        history = pd.DataFrame({"student_id": ["S"], "degree_id": ["D"],
                                "part_id": [20243], "faculty_id": ["F"]})
        diplomas = pd.DataFrame({"student_id": ["S"], "diploma_gpa": [80.], "diploma_type_id": ["T"]})
        args = ["S", "D", self.part]
        original = build_student_snapshot(status, history, diplomas, *args)
        changed = status.copy()
        mask = changed.part_id.ge(self.part)
        for column in ["gpa_points", "end_agpa_points", "end_total_in_courses", "end_total_in_credits",
                       "semester_pass_courses", "semester_fail_courses", "reg_total_semesters"]:
            changed.loc[mask, column] = 0
        updated = build_student_snapshot(changed, history, diplomas, *args)
        assert_frame_equal(pd.DataFrame([original]), pd.DataFrame([updated]))
        self.assertEqual(original["gpa_prev_1"], 3.)
        self.assertEqual(original["gpa_prev_2"], 2.)
        self.assertEqual(original["prior_total_reg_credits"], 60.)
        validate_snapshot(original, *args)


if __name__ == "__main__":
    unittest.main()
