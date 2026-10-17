"""Downstream grade-only exhaustive and global-top-50 XML search experiments.

This module consumes prepared candidate rows and already-loaded grade artifacts.
It neither loads production engines nor trains models or predicts failure risk.
The common objective is additive cumulative GPA, semester GPA, then canonical
course IDs; ranking never uses rounded GPA values.
"""
from hashlib import sha256
from itertools import islice
import json
from time import perf_counter

import numpy as np
import pandas as pd

from src.features.feature_contract import prepare_model_matrix
from src.features.temporal_features import PLAN_CONTEXT_COLUMNS, compute_plan_context_features
from src.recommendation.plan_generation import build_plan_rows, enumerate_plan_indices
from src.recommendation.plan_scoring import project_cumulative_gpa


class GradeOnlyScorer:
    """Apply one ordered grade-model contract and the loaded GradeScale bands."""

    def __init__(self, model, category_levels, grade_scale, features, num_threads=4):
        self.model = model
        self.category_levels = category_levels
        self.grade_scale = grade_scale
        self.features = list(features)
        self.num_threads = num_threads
        self.uses_plan_context = bool(set(self.features) & set(PLAN_CONTEXT_COLUMNS))

    def score(self, rows):
        """Rebuild context per complete plan only when the model uses it."""
        rows = rows.copy()
        self.grade_scale.validate_versions(rows["grade_version_id"])
        if self.uses_plan_context and len(rows):
            rows[PLAN_CONTEXT_COLUMNS] = compute_plan_context_features(
                rows, group_columns=["plan_id"],
            ).to_numpy()
        matrix = prepare_model_matrix(rows, self.category_levels, model_features=self.features)
        marks = np.asarray(self.model.predict(matrix, num_threads=self.num_threads), dtype=float)
        if marks.shape != (len(rows),):
            raise ValueError("Grade model returned predictions with the wrong shape.")
        if not np.isfinite(marks).all():
            raise ValueError("Grade model returned non-finite predictions.")
        rows["predicted_mark"] = np.clip(marks, 0, 100)
        rows["expected_points"], rows["expected_grade"] = self.grade_scale.convert(
            rows["predicted_mark"], rows["grade_version_id"],
        )
        if not np.isfinite(rows["expected_points"].to_numpy(dtype=float)).all():
            raise ValueError("GradeScale returned non-finite expected points.")
        return rows


def _validate_search(candidates, current_gpa, current_gpa_credits, batch_size, top_n):
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer.")
    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n <= 0:
        raise ValueError("top_n must be a positive integer.")
    # Validate even an empty search before returning a no-plan result.
    project_cumulative_gpa(current_gpa, current_gpa_credits, 0., 18.)
    if candidates["course_id"].isna().any():
        raise ValueError("course_id cannot be missing.")
    if candidates["course_id"].map(str).duplicated().any():
        raise ValueError("Duplicate course_id candidates are not allowed.")


def _sort_key(plan):
    return (-plan["projected_cumulative_gpa"], -plan["expected_plan_gpa"], tuple(plan["course_ids"]))


def _summaries(scored, current_gpa, current_gpa_credits, *, exact_credits=None):
    credits = pd.to_numeric(scored["course_credits"], errors="raise").astype(float)
    points = pd.to_numeric(scored["expected_points"], errors="raise").astype(float)
    work = scored.assign(_credits=credits, _quality=credits * points)
    summary = work.groupby("plan_id", sort=False).agg(
        course_count=("course_id", "size"), total_credits=("_credits", "sum"),
        expected_quality_points=("_quality", "sum"),
    )
    if exact_credits is not None:
        # Enumeration established this exact Decimal total; float summation must
        # not turn the same feasible total into different ranking denominators.
        summary["total_credits"] = float(exact_credits)
    summary["expected_plan_gpa"] = summary["expected_quality_points"] / summary["total_credits"]
    summary["projected_cumulative_gpa"] = project_cumulative_gpa(
        current_gpa, current_gpa_credits, summary["expected_quality_points"], summary["total_credits"],
    )
    summary["expected_cumulative_gpa_gain"] = summary["projected_cumulative_gpa"] - float(current_gpa)
    attempts = pd.to_numeric(scored["attempt_number"], errors="coerce") if "attempt_number" in scored else pd.Series(1, index=scored.index)
    summary["projected_gpa_requires_repeat_policy"] = attempts.gt(1).groupby(scored["plan_id"], sort=False).any()
    return summary


def _plan_record(plan_id, indices, ids, row):
    return {
        "plan_id": int(plan_id), "candidate_indices": list(indices),
        "course_ids": sorted(ids[i] for i in indices),
        "course_count": int(row.course_count), "total_credits": float(row.total_credits),
        "expected_quality_points": float(row.expected_quality_points),
        "expected_plan_gpa": float(row.expected_plan_gpa),
        "projected_cumulative_gpa": float(row.projected_cumulative_gpa),
        "expected_cumulative_gpa_gain": float(row.expected_cumulative_gpa_gain),
        "projected_gpa_requires_repeat_policy": bool(row.projected_gpa_requires_repeat_policy),
    }


def _courses(scored, plan_id):
    selected = scored.loc[scored["plan_id"].eq(plan_id)]
    columns = [name for name in (
        "course_id", "course_name", "course_credits", "attempt_number", "predicted_mark",
        "expected_points", "expected_grade",
    ) if name in selected]
    records = selected[columns].to_dict("records")
    for record in records:
        record["course_id"] = str(record["course_id"])
        record["course_credits"] = float(record["course_credits"])
    return sorted(records, key=lambda row: row["course_id"])


def _statistics():
    return {"count": 0, "min": None, "max": None, "sum": 0., "mean": None}


def _update_statistics(stats, values):
    values = np.asarray(values, dtype=float)
    if not len(values):
        return
    stats["count"] += len(values)
    stats["min"] = float(values.min()) if stats["min"] is None else min(stats["min"], float(values.min()))
    stats["max"] = float(values.max()) if stats["max"] is None else max(stats["max"], float(values.max()))
    stats["sum"] += float(values.sum())
    stats["mean"] = stats["sum"] / stats["count"]


def search_exhaustive(candidates, scorer, current_gpa, current_gpa_credits, *, top_n=3,
                      batch_size=1000, progress=None):
    """Score every exact-18 subset, retaining only a bounded global top N."""
    started = perf_counter()
    _validate_search(candidates, current_gpa, current_gpa_credits, batch_size, top_n)
    ids = candidates["course_id"].map(str).tolist()
    search_stats, digest, stats = {}, sha256(), _statistics()
    iterator = enumerate_plan_indices(candidates, target_credits=18, search_stats=search_stats)
    retained = []
    generated = scored_rows = max_batch_rows = max_batch_plans = max_retained = 0
    enumeration_seconds = scoring_seconds = aggregation_seconds = 0.
    while True:
        tick = perf_counter()
        plans = list(islice(iterator, batch_size))
        for indices in plans:
            identity = sorted(ids[i] for i in indices)
            digest.update(json.dumps(identity, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n")
        enumeration_seconds += perf_counter() - tick
        if not plans:
            break
        tick = perf_counter()
        rows = build_plan_rows(candidates, plans, first_plan_id=generated)
        scored = scorer.score(rows)
        scoring_seconds += perf_counter() - tick
        tick = perf_counter()
        summary = _summaries(scored, current_gpa, current_gpa_credits, exact_credits=18)
        _update_statistics(stats, summary["projected_cumulative_gpa"])
        batch_records = [
            _plan_record(plan_id, plans[plan_id - generated], ids, row)
            for plan_id, row in summary.iterrows()
        ]
        retained = sorted([*retained, *batch_records], key=_sort_key)[:top_n]
        for plan in retained:
            if "courses" not in plan:
                plan["courses"] = _courses(scored, plan["plan_id"])
        generated += len(plans)
        scored_rows += len(rows)
        max_batch_rows = max(max_batch_rows, len(rows))
        max_batch_plans = max(max_batch_plans, len(plans))
        max_retained = max(max_retained, len(retained))
        aggregation_seconds += perf_counter() - tick
        if progress is not None:
            progress({"phase": "exhaustive", "generated_plan_count": generated,
                      "scored_plan_count": generated, "scored_row_count": scored_rows,
                      "elapsed_seconds": perf_counter() - started})
    for rank, plan in enumerate(retained, 1):
        plan["rank"] = rank
    stage = "47" if scorer.uses_plan_context else "33"
    return {
        "status": "ok" if generated else "no_feasible_18_credit_plan",
        "recommendations": retained, "generated_plan_count": generated,
        "scored_plan_count": generated, "scored_row_count": scored_rows,
        "counts": {"generated": generated, "scored33": generated if stage == "33" else 0,
                   "scored47": generated if stage == "47" else 0,
                   "scored_rows33": scored_rows if stage == "33" else 0,
                   "scored_rows47": scored_rows if stage == "47" else 0},
        "timings": {"enumeration_seconds": enumeration_seconds, "scoring_seconds": scoring_seconds,
                    "aggregation_seconds": aggregation_seconds, "total_seconds": perf_counter() - started},
        "diagnostics": {"search_stats": search_stats, "plan_identity_sha256": digest.hexdigest(),
                        "max_batch_rows": max_batch_rows, "max_batch_plans": max_batch_plans,
                        "max_retained_plans": max_retained, "gpa_statistics": stats},
    }


def search_two_stage(candidates, scorer33, scorer47, current_gpa, current_gpa_credits, *,
                     top_n=3, batch_size=1000, progress=None):
    """Select global top 50 after scoring all plans with 33, then score only those with 47."""
    started = perf_counter()
    _validate_search(candidates, current_gpa, current_gpa_credits, batch_size, top_n)
    stage1 = search_exhaustive(candidates, scorer33, current_gpa, current_gpa_credits,
                               top_n=50, batch_size=batch_size, progress=progress)
    stage1_seconds = perf_counter() - started
    shortlist = stage1["recommendations"]
    ids = candidates["course_id"].map(str).tolist()
    records, stage2_rows, stage2_max_batch_rows, stage2_stats = [], 0, 0, _statistics()
    tick = perf_counter()
    for offset in range(0, len(shortlist), batch_size):
        batch = shortlist[offset:offset + batch_size]
        plans = [plan["candidate_indices"] for plan in batch]
        rows = build_plan_rows(candidates, plans)
        rows["plan_id"] = rows["plan_id"].map({i: plan["plan_id"] for i, plan in enumerate(batch)})
        scored = scorer47.score(rows)
        summary = _summaries(scored, current_gpa, current_gpa_credits, exact_credits=18)
        _update_statistics(stage2_stats, summary["projected_cumulative_gpa"])
        for original in batch:
            plan_id = original["plan_id"]
            plan = _plan_record(plan_id, original["candidate_indices"], ids, summary.loc[plan_id])
            plan.update(courses=_courses(scored, plan_id), stage1_rank=original["rank"],
                        stage1_GPA=original["projected_cumulative_gpa"],
                        stage1_expected_plan_gpa=original["expected_plan_gpa"],
                        stage2_GPA=plan["projected_cumulative_gpa"],
                        stage2_expected_plan_gpa=plan["expected_plan_gpa"])
            plan["delta"] = plan["stage2_GPA"] - plan["stage1_GPA"]
            records.append(plan)
        stage2_rows += len(rows)
        stage2_max_batch_rows = max(stage2_max_batch_rows, len(rows))
        if progress is not None:
            progress({"phase": "stage2", "scored_plan_count": len(records),
                      "scored_row_count": stage2_rows, "elapsed_seconds": perf_counter() - started})
    ranked = sorted(records, key=_sort_key)
    for rank, plan in enumerate(ranked, 1):
        plan["stage2_rank"] = rank
        plan["rank"] = rank
    stage2_seconds = perf_counter() - tick
    diagnostics = dict(stage1["diagnostics"])
    diagnostics.update(stage1_gpa_statistics=stage1["diagnostics"]["gpa_statistics"],
                       stage2_gpa_statistics=stage2_stats, stage2_max_batch_rows=stage2_max_batch_rows)
    return {
        "status": stage1["status"], "recommendations": ranked[:top_n],
        "shortlist": sorted(records, key=lambda plan: plan["stage1_rank"]),
        "generated_plan_count": stage1["generated_plan_count"], "shortlist_count": len(records),
        "counts": {"generated": stage1["generated_plan_count"], "scored33": stage1["scored_plan_count"],
                   "scored47": len(records), "scored_rows33": stage1["scored_row_count"],
                   "scored_rows47": stage2_rows},
        "timings": {"stage1_seconds": stage1_seconds, "stage2_seconds": stage2_seconds,
                    "stage1_enumeration_seconds": stage1["timings"]["enumeration_seconds"],
                    "stage1_scoring_seconds": stage1["timings"]["scoring_seconds"],
                    "stage1_aggregation_seconds": stage1["timings"]["aggregation_seconds"],
                    "total_seconds": perf_counter() - started},
        "diagnostics": diagnostics,
    }


def score_observed_plan(prepared, scorer47, current_gpa, current_gpa_credits):
    """Score the supplied observed roster as one plan, without a credit target."""
    _validate_search(prepared, current_gpa, current_gpa_credits, 1, 1)
    if prepared.empty:
        raise ValueError("The observed plan must contain at least one course.")
    rows = build_plan_rows(prepared, [tuple(range(len(prepared)))])
    scored = scorer47.score(rows)
    summary = _summaries(scored, current_gpa, current_gpa_credits)
    plan = _plan_record(0, range(len(prepared)), prepared["course_id"].map(str).tolist(), summary.loc[0])
    plan.update(courses=_courses(scored, 0), rank=1)
    return plan


def comparison_metrics(baseline, two_stage):
    """Compare recommendation identities, shortlist recall, regret and prediction parity."""
    baseline_top = baseline.get("recommendations", [])[:3]
    two_stage_top = two_stage.get("recommendations", [])[:3]
    identity = lambda plan: tuple(sorted(map(str, plan["course_ids"])))
    baseline_ids = {identity(plan) for plan in baseline_top}
    shortlist = {identity(plan): plan for plan in two_stage.get("shortlist", two_stage_top)}
    retained = baseline_ids & shortlist.keys()
    overlap = baseline_ids & {identity(plan) for plan in two_stage_top}
    parity = {"compared_plan_count": 0, "compared_course_count": 0, "all_match": None,
              "max_abs_mark_difference": 0., "max_abs_points_difference": 0., "mismatches": []}
    for plan in baseline_top:
        key = identity(plan)
        if key not in shortlist:
            continue
        parity["compared_plan_count"] += 1
        first = {str(row["course_id"]): row for row in plan["courses"]}
        second = {str(row["course_id"]): row for row in shortlist[key]["courses"]}
        if first.keys() != second.keys():
            parity["mismatches"].append({"course_ids": list(key), "reason": "course prediction membership differs"})
        for course_id in first.keys() & second.keys():
            parity["compared_course_count"] += 1
            mark_diff = abs(float(first[course_id]["predicted_mark"]) - float(second[course_id]["predicted_mark"]))
            points_diff = abs(float(first[course_id]["expected_points"]) - float(second[course_id]["expected_points"]))
            parity["max_abs_mark_difference"] = max(parity["max_abs_mark_difference"], mark_diff)
            parity["max_abs_points_difference"] = max(parity["max_abs_points_difference"], points_diff)
            if mark_diff != 0 or points_diff != 0:
                parity["mismatches"].append({"course_ids": list(key), "course_id": course_id,
                                              "mark_difference": mark_diff, "points_difference": points_diff})
    if parity["compared_plan_count"]:
        parity["all_match"] = not parity["mismatches"]
    baseline_time = baseline.get("timings", {}).get("total_seconds")
    two_stage_time = two_stage.get("timings", {}).get("total_seconds")
    return {
        "top_1_match": identity(baseline_top[0]) == identity(two_stage_top[0]) if baseline_top and two_stage_top else None,
        "top_3_overlap": len(overlap), "top_3_overlap_fraction": len(overlap) / len(baseline_ids) if baseline_ids else None,
        "baseline_top_3_recall_at_50_count": len(retained),
        "baseline_top_3_recall_at_50": len(retained) / len(baseline_ids) if baseline_ids else None,
        "gpa_regret": baseline_top[0]["projected_cumulative_gpa"] - two_stage_top[0]["projected_cumulative_gpa"] if baseline_top and two_stage_top else None,
        "speedup": baseline_time / two_stage_time if baseline_time is not None and two_stage_time else None,
        "prediction_parity": parity,
    }
