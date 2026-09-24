"""Batched recommendation inference over frozen historical state."""
from itertools import islice
import json
from time import perf_counter

import numpy as np
import pandas as pd

from src.experiments.modeling import prepare_matrix
from src.features.feature_contract import prepare_model_matrix
from src.features.frozen_history import validate_history_pair, validate_history_selection
from src.features.temporal_features import (
    COURSE_HISTORY_COLUMNS, PLAN_CONTEXT_COLUMNS, compute_plan_context_features,
)

from .artifacts import load_recommendation_artifacts
from .inputs import STUDENT_SNAPSHOT_COLUMNS, CANDIDATE_COURSE_COLUMNS
from .plan_generation import resolve_credit_bounds, enumerate_plan_indices, build_plan_rows
from .plan_scoring import COURSE_OUTPUT_COLUMNS, rank_plans, summarize_scored_plans, empty_summaries


def resolve_current_gpa_credits(snapshot, override=None):
    """Use prior registered credits: snapshot prior_total_reg_credits = source total_reg_credits."""
    if override is not None:
        value, source = override, "explicit_override"
    elif "current_gpa_credits" in snapshot:
        value, source = snapshot["current_gpa_credits"], "snapshot.current_gpa_credits"
    else:
        value, source = snapshot.get("prior_total_reg_credits"), "snapshot.prior_total_reg_credits"
    if value is None or pd.isna(value):
        raise ValueError("Supply known current_gpa_credits; snapshot prior_total_reg_credits (source total_reg_credits) is missing.")
    value = float(value)
    if not np.isfinite(value) or value < 0:
        raise ValueError("current_gpa_credits must be finite and nonnegative.")
    return value, source


class AcademicPlanRecommender:
    def __init__(self, points_model, fail_model, points_levels, fail_levels,
                 course_history, specialty_history, metadata, provenance=None, num_threads=4):
        self.points_model, self.fail_model = points_model, fail_model
        self.points_levels, self.fail_levels = points_levels, fail_levels
        self.course_history, self.specialty_history = course_history, specialty_history
        self.metadata, self.provenance = metadata, provenance or {}
        validate_history_pair(course_history, specialty_history, course_history.as_of_part)
        self.num_threads = num_threads

    @classmethod
    def load(cls, *, history_as_of_part, num_threads=4, history_root=None):
        return cls(*load_recommendation_artifacts(
            history_as_of_part=history_as_of_part, history_root=history_root,
        ), num_threads=num_threads)

    def prepare_candidates(self, student_snapshot, candidate_courses, part_id, *, allow_older_history=False):
        validate_history_pair(self.course_history, self.specialty_history, self.course_history.as_of_part)
        validate_history_selection(part_id, self.course_history.as_of_part, allow_older_history=allow_older_history)
        for training in self.provenance.get("training", {}).values():
            cutoff = training["training_as_of_part"]
            if cutoff is not None and cutoff >= int(part_id):
                raise ValueError("Model training cutoff must precede the target semester.")
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
                  top_n=3, course_sink=None, progress=None, current_gpa_credits=None,
                  allow_older_history=False):
        """Rank every matching plan; return all summaries and top-N course details."""
        started = perf_counter()
        if current_gpa is None or pd.isna(current_gpa):
            raise ValueError("Supply a known current_gpa; snapshot start_agpa_points is missing.")
        current_gpa = float(current_gpa)
        if not np.isfinite(current_gpa) or not 0 <= current_gpa <= 4:
            raise ValueError("current_gpa must be between 0 and 4.")
        if batch_size < 1 or top_n < 1:
            raise ValueError("batch_size and top_n must be positive.")
        current_gpa_credits, credits_source = resolve_current_gpa_credits(student_snapshot, current_gpa_credits)
        lower, upper = resolve_credit_bounds(credits, min_credits, max_credits)
        candidates = self.prepare_candidates(student_snapshot, candidate_courses, part_id,
                                              allow_older_history=allow_older_history)
        iterator = enumerate_plan_indices(candidates, min_credits=lower, max_credits=upper)
        summaries, top = [], empty_summaries()
        top_courses = pd.DataFrame(columns=COURSE_OUTPUT_COLUMNS)
        evaluated = 0
        while batch := list(islice(iterator, batch_size)):
            scored = self.score_rows(build_plan_rows(candidates, batch, evaluated))
            scored_plans = summarize_scored_plans(scored, current_gpa, current_gpa_credits)
            evaluated += len(batch)
            summaries.append(scored_plans)
            course_rows = scored[COURSE_OUTPUT_COLUMNS]
            if course_sink is not None:
                course_sink(course_rows)
            top = rank_plans(pd.concat([top, scored_plans], ignore_index=True)).head(top_n)
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
        status = "ok" if len(all_plans) else "no_matching_credit_plan"
        improvement_count = int(all_plans.is_expected_cumulative_improvement.sum())
        return all_plans, {
            "status": status, "student_id": str(student_snapshot["student_id"]),
            "degree_id": str(student_snapshot["degree_id"]), "part_id": int(part_id),
            "target_credits": float(lower) if lower == upper else None,
            "min_credits": float(lower), "max_credits": float(upper), "current_gpa": current_gpa,
            "current_gpa_credits": current_gpa_credits, "current_gpa_credits_source": credits_source,
            "projected_gpa_method": "standard_additive_without_repeat_replacement",
            "repeat_detection": "observed_prior_cleaned_attempts_only; earlier/excluded attempts may be missing",
            **validate_history_selection(part_id, self.course_history.as_of_part, allow_older_history=allow_older_history),
            "candidate_count": len(candidates), "matching_plan_count": evaluated,
            "scored_plan_count": len(all_plans), "returned_plan_count": len(recommendations),
            "plans_with_expected_improvement": improvement_count,
            "has_expected_improvement": improvement_count > 0,
            "best_projected_cumulative_gpa": recommendations[0]["projected_cumulative_gpa"] if recommendations else None,
            "best_expected_cumulative_gpa_gain": recommendations[0]["expected_cumulative_gpa_gain"] if recommendations else None,
            "history": self.provenance.get("history"),
            "model_training": self.provenance.get("training"),
            "top_n": top_n,
            # Compatibility alias: all scored feasible plans, irrespective of GPA.
            "accepted_plan_count": len(all_plans), "batch_size": batch_size,
            "elapsed_seconds": perf_counter() - started, "model": self.provenance,
            "recommendations": recommendations,
        }
