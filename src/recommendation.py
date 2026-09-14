"""Exhaustive ## (generate then predict) , batched Expected Points ranking, independent of data sources."""
from decimal import Decimal ## credits
from hashlib import sha256 ## finger print 
from itertools import islice ## batch
import json
from time import perf_counter

import numpy as np
import pandas as pd

from .experiments.modeling import prepare_matrix
from .experiments.specialty_history import FrozenSpecialtyHistory
from .feature_contract import MODEL_FEATURES, load_category_levels, prepare_model_matrix, require_current_features
from .paths import (
    CATEGORY_LEVELS_PATH, COURSE_HISTORY_STATE_PATH, FAIL_MODEL_PATH, MODEL_METADATA_PATH,
    DEGREE_POINTS_SELECTED_MODEL_PATH, DEGREE_POINTS_CATEGORY_LEVELS_PATH,
    DEGREE_POINTS_EXPERIMENT_METADATA_PATH, TEMPORAL_TRAIN_FEATURES_PATH,
)
from .temporal_features import (
    COURSE_HISTORY_COLUMNS, PLAN_CONTEXT_COLUMNS, compute_plan_context_features,
    load_course_history_state,
)

STUDENT_SNAPSHOT_COLUMNS = [
    "student_id", "degree_id", "faculty_id", "grade_version_id",
    "gpa_prev_1", "gpa_prev_2", "gpa_trend_delta", "gpa_trend_missing",
    "start_agpa_points", "start_total_in_courses", "start_total_in_credits",
    "prior_total_reg_courses", "prior_total_reg_credits", "prior_total_fail_courses",
    "prior_total_fail_credits", "prior_fail_credit_ratio", "prior_registered_semesters",
    "observed_gap_semesters", "diploma_gpa", "diploma_type_id", "degree_credits_count",
]
CANDIDATE_COURSE_COLUMNS = [
    "course_id", "course_credits", "attempt_number", "plan_course_type_id",
    "plan_requirement_type_id", "plan_year_order", "plan_semester_order", "plan_credits_count",
]
SUMMARY_COLUMNS = [
    "plan_id", "course_count", "total_credits", "expected_quality_points",
    "expected_plan_gpa", "gpa_gain", "expected_failed_credits",
]
COURSE_OUTPUT_COLUMNS = [
    "plan_id", "course_id", "course_name", "course_credits", "expected_points", "fail_probability",
]


def resolve_credit_bounds(credits=None, min_credits=None, max_credits=None):
    """A single value becomes equal bounds; a range keeps both inclusive bounds."""
    if credits is not None:
        if min_credits is not None or max_credits is not None:
            raise ValueError("Use credits OR min_credits/max_credits, not both.")
        lower = upper = Decimal(str(credits))
    else:
        if min_credits is None or max_credits is None:
            raise ValueError("Supply credits or both min_credits and max_credits.")
        lower, upper = Decimal(str(min_credits)), Decimal(str(max_credits))
    if not lower.is_finite() or not upper.is_finite() or lower < 0 or upper <= 0 or lower > upper:
        raise ValueError("Invalid credit bounds: require 0 <= min <= max and max > 0.")
    return lower, upper


def enumerate_plan_indices(candidate_courses, target_credits=None, *, min_credits=None, max_credits=None):
    """Yield all positive-credit subsets within inclusive bounds, without rounding.

    Zero-credit courses remain optional members even after reaching the upper bound.
    """
    values = [Decimal(str(v)) for v in candidate_courses["course_credits"]]
    lower, upper = resolve_credit_bounds(target_credits, min_credits, max_credits)
    if any(not v.is_finite() or v < 0 for v in values):
        raise ValueError("Course credits must be finite and nonnegative.")
    scale = 10 ** max(0, *[-v.as_tuple().exponent for v in [*values, lower, upper]])
    units = [int(v * scale) for v in values]
    minimum, maximum = int(lower * scale), int(upper * scale)
    suffix = [0] * (len(units) + 1)
    for i in range(len(units) - 1, -1, -1):
        suffix[i] = suffix[i + 1] + units[i]

    def visit(i, total, selected):
        if total > maximum or total + suffix[i] < minimum:
            return
        if i == len(units):
            if minimum <= total <= maximum and total > 0:
                yield selected
            return
        yield from visit(i + 1, total + units[i], (*selected, i))
        yield from visit(i + 1, total, selected)

    yield from visit(0, 0, ())


def build_plan_rows(candidates, plans, first_plan_id=0):
    lengths = np.array([len(p) for p in plans], dtype="int64")
    indices = np.fromiter((i for plan in plans for i in plan), dtype="int64")
    rows = candidates.iloc[indices].reset_index(drop=True).copy()
    rows["plan_id"] = np.repeat(np.arange(first_plan_id, first_plan_id + len(plans)), lengths)
    return rows


def rank_plans(summaries):
    return summaries.sort_values(
        ["expected_plan_gpa", "expected_failed_credits", "plan_id"],
        ascending=[False, True, True], kind="stable",
    ).reset_index(drop=True)


def summarize_scored_plans(scored_courses, current_gpa):
    work = scored_courses.assign(
        quality=scored_courses["course_credits"] * scored_courses["expected_points"],
        failed=scored_courses["course_credits"] * scored_courses["fail_probability"],
    )
    summary = work.groupby("plan_id", sort=False).agg(
        course_count=("course_id", "size"), total_credits=("course_credits", "sum"),
        expected_quality_points=("quality", "sum"), expected_failed_credits=("failed", "sum"),
    ).reset_index()
    summary["expected_plan_gpa"] = summary["expected_quality_points"] / summary["total_credits"]
    summary["gpa_gain"] = summary["expected_plan_gpa"] - current_gpa
    return rank_plans(summary.loc[summary["expected_plan_gpa"].gt(current_gpa), SUMMARY_COLUMNS])


def empty_summaries():
    return pd.DataFrame({c: pd.Series(dtype="int64" if c in ["plan_id", "course_count"] else "float64")
                         for c in SUMMARY_COLUMNS})


class AcademicPlanRecommender:
    def __init__(self, points_model, fail_model, points_levels, fail_levels,
                 course_history, specialty_history, metadata, provenance=None, num_threads=4):
        self.points_model, self.fail_model = points_model, fail_model
        self.points_levels, self.fail_levels = points_levels, fail_levels
        self.course_history, self.specialty_history = course_history, specialty_history
        self.metadata, self.provenance = metadata, provenance or {}
        self.num_threads = num_threads

    @classmethod
    def load(cls, num_threads=4):
        import lightgbm as lgb

        metadata = json.loads(DEGREE_POINTS_EXPERIMENT_METADATA_PATH.read_text(encoding="utf-8"))
        fail_metadata = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
        require_current_features(metadata)
        require_current_features(fail_metadata)
        if metadata["selected_variant"]["target"] != "points":
            raise ValueError("The selected artifact must predict points directly.")
        train = pd.read_parquet(TEMPORAL_TRAIN_FEATURES_PATH, columns=[
            "part_id", "degree_id", "plan_requirement_type_id", "final_mark", "is_fail", "points",
        ])
        require_current_features(train.attrs)
        course_history = load_course_history_state(COURSE_HISTORY_STATE_PATH)
        specialty_history = FrozenSpecialtyHistory.from_training(train)
        if course_history.as_of_part != specialty_history.as_of_part:
            raise ValueError("Course and specialty history cutoffs do not match; rebuild artifacts.")
        points = lgb.Booster(model_file=str(DEGREE_POINTS_SELECTED_MODEL_PATH))
        fail = lgb.Booster(model_file=str(FAIL_MODEL_PATH))
        if points.feature_name() != metadata["feature_contract"]["model_features"]:
            raise ValueError("Expected Points model and metadata feature order disagree.")
        if fail.feature_name() != fail_metadata["feature_contract"]["model_features"]:
            raise ValueError("Fail model and metadata feature order disagree.")
        if fail.feature_name() != MODEL_FEATURES:
            raise ValueError("Current failure feature contract differs from the saved model.")
        provenance = {
            "selected_variant": metadata["selected_variant"]["name"],
            "model_created_at_utc": metadata["created_at_utc"],
            "experiment_signature": metadata["experiment_signature"],
            "feature_engineering_version": metadata["feature_engineering_version"],
            "history_as_of_part": specialty_history.as_of_part,
            "artifact_sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in [
                DEGREE_POINTS_SELECTED_MODEL_PATH, DEGREE_POINTS_CATEGORY_LEVELS_PATH,
                FAIL_MODEL_PATH, CATEGORY_LEVELS_PATH,
            ]},
        }
        return cls(points, fail, load_category_levels(DEGREE_POINTS_CATEGORY_LEVELS_PATH),
                   load_category_levels(CATEGORY_LEVELS_PATH), course_history,
                   specialty_history, metadata, provenance, num_threads)

    def prepare_candidates(self, student_snapshot, candidate_courses, part_id):
        if int(part_id) <= self.specialty_history.as_of_part:
            raise ValueError("Target semester must follow frozen training history.")
        if int(student_snapshot["part_id"]) != int(part_id):
            raise ValueError("Snapshot must describe the target semester's start.")
        missing = set(STUDENT_SNAPSHOT_COLUMNS) - student_snapshot.keys()
        if missing:
            raise ValueError(f"Incomplete snapshot: {sorted(missing)}")
        rows = candidate_courses.copy()
        rows["course_id"] = rows["course_id"].astype("string").str.strip()
        if rows["course_id"].isna().any() or rows["course_id"].eq("").any() or rows["course_id"].duplicated().any():
            raise ValueError("Candidate course IDs must be present and unique.")
        rows = rows.sort_values("course_id", kind="stable").reset_index(drop=True)
        # Do not allow supplied outcome/history columns to override model features.
        rows = rows[[*CANDIDATE_COURSE_COLUMNS, *(["course_name"] if "course_name" in rows else [])]].copy()
        if "course_name" not in rows:
            rows["course_name"] = pd.Series(None, index=rows.index, dtype="string")
        for column in STUDENT_SNAPSHOT_COLUMNS:
            rows[column] = student_snapshot[column]
        rows["part_id"] = int(part_id)
        rows["part_semester"] = int(part_id) % 10
        history = self.course_history.apply(rows)
        rows[COURSE_HISTORY_COLUMNS] = history[COURSE_HISTORY_COLUMNS].to_numpy()
        return self.specialty_history.apply(rows)

    def score_rows(self, rows):
        rows = rows.copy()
        context = compute_plan_context_features(rows, group_columns=["plan_id"])
        rows[PLAN_CONTEXT_COLUMNS] = context.to_numpy()
        contract = self.metadata["feature_contract"]
        matrix = prepare_matrix(rows, contract["numeric_features"], contract["categorical_features"], self.points_levels)
        rows["expected_points"] = np.clip(self.points_model.predict(matrix, num_threads=self.num_threads), 0, 4)
        fail_matrix = prepare_model_matrix(rows, self.fail_levels)
        rows["fail_probability"] = np.clip(self.fail_model.predict(fail_matrix, num_threads=self.num_threads), 0, 1)
        if not np.isfinite(rows[["expected_points", "fail_probability"]].to_numpy()).all():
            raise ValueError("Model returned non-finite predictions.")
        return rows

    def recommend(self, student_snapshot, candidate_courses, part_id, current_gpa,
                  credits=None, min_credits=None, max_credits=None, batch_size=2000,
                  top_n=5, course_sink=None, progress=None):
        """Return all accepted summaries and top-N details; stream course rows to sink."""
        started = perf_counter()
        if current_gpa is None or pd.isna(current_gpa):
            raise ValueError("Supply a known current_gpa; snapshot start_agpa_points is missing.")
        current_gpa = float(current_gpa)
        if not np.isfinite(current_gpa) or not 0 <= current_gpa <= 4:
            raise ValueError("current_gpa must be between 0 and 4.")
        if batch_size < 1 or top_n < 1:
            raise ValueError("batch_size and top_n must be positive.")
        lower, upper = resolve_credit_bounds(credits, min_credits, max_credits)
        candidates = self.prepare_candidates(student_snapshot, candidate_courses, part_id)
        iterator = enumerate_plan_indices(candidates, min_credits=lower, max_credits=upper)
        summaries, top = [], empty_summaries()
        top_courses = pd.DataFrame(columns=COURSE_OUTPUT_COLUMNS)
        evaluated = 0
        while batch := list(islice(iterator, batch_size)):
            scored = self.score_rows(build_plan_rows(candidates, batch, evaluated))
            accepted = summarize_scored_plans(scored, current_gpa)
            evaluated += len(batch)
            if not accepted.empty:
                summaries.append(accepted)
                course_rows = scored.loc[scored.plan_id.isin(accepted.plan_id), COURSE_OUTPUT_COLUMNS]
                if course_sink is not None:
                    course_sink(course_rows)
                top = rank_plans(pd.concat([top, accepted], ignore_index=True)).head(top_n)
                selected_rows = course_rows[course_rows.plan_id.isin(top.plan_id)]
                top_courses = selected_rows.copy() if top_courses.empty else pd.concat([top_courses, selected_rows], ignore_index=True)
                top_courses = top_courses[top_courses.plan_id.isin(top.plan_id)]
            if progress is not None:
                progress(evaluated)
        all_plans = rank_plans(pd.concat(summaries, ignore_index=True)) if summaries else empty_summaries()
        recommendations = []
        for rank, (_, row) in enumerate(top.iterrows(), 1):
            item = json.loads(row.to_json(double_precision=15))
            item["plan_id"], item["course_count"], item["rank"] = int(row.plan_id), int(row.course_count), rank
            item["courses"] = json.loads(top_courses[top_courses.plan_id.eq(row.plan_id)].to_json(orient="records", double_precision=15))
            recommendations.append(item)
        status = "ok" if len(all_plans) else ("no_matching_credit_plan" if evaluated == 0 else "no_plan_above_current_gpa")
        return all_plans, {
            "status": status, "student_id": str(student_snapshot["student_id"]),
            "degree_id": str(student_snapshot["degree_id"]), "part_id": int(part_id),
            "target_credits": float(lower) if lower == upper else None,
            "min_credits": float(lower), "max_credits": float(upper), "current_gpa": current_gpa,
            "candidate_count": len(candidates), "matching_plan_count": evaluated,
            "accepted_plan_count": len(all_plans), "batch_size": batch_size,
            "elapsed_seconds": perf_counter() - started, "model": self.provenance,
            "recommendations": recommendations,
        }
