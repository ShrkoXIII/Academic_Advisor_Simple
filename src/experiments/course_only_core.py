"""Plan-independent inference and exact-credit search for isolated research."""
from bisect import insort
from decimal import Decimal
from time import perf_counter

import numpy as np
import pandas as pd

from src.features.feature_contract import (
    BASE_FEATURES, CATEGORICAL_FEATURES, CATEGORY_MISSING, CATEGORY_UNKNOWN,
)
from src.features.frozen_history import validate_history_pair, validate_history_selection
from src.features.temporal_features import COURSE_HISTORY_COLUMNS
from src.recommendation.inputs import CANDIDATE_COURSE_COLUMNS, STUDENT_SNAPSHOT_COLUMNS
from src.recommendation.plan_generation import enumerate_plan_indices
from src.recommendation.plan_scoring import project_cumulative_gpa


REMOVED_CONTEXT_FEATURES = frozenset([
    "plan_course_count", "plan_total_credits", "plan_credit_weighted_fail_rate",
    "plan_credit_weighted_avg_mark", "plan_credit_weighted_avg_attempt", "plan_difficulty_credit_load",
    "peer_course_count", "peer_total_credits", "peer_credit_weighted_fail_rate",
    "peer_credit_weighted_avg_mark", "peer_credit_weighted_avg_attempt", "peer_difficulty_credit_load",
    "peer_max_fail_rate", "peer_difficulty_missing",
])
COURSE_ONLY_FEATURES = [f for f in BASE_FEATURES if f not in REMOVED_CONTEXT_FEATURES]
if (len(BASE_FEATURES) != 47 or len(COURSE_ONLY_FEATURES) != 33
        or set(BASE_FEATURES) - set(COURSE_ONLY_FEATURES) != REMOVED_CONTEXT_FEATURES):
    raise ValueError("Course-only experiment requires precisely the documented 47-minus-14 contract.")


def prepare_course_matrix(frame, category_levels):
    """Match official numeric/category handling without needing plan columns."""
    missing = set(COURSE_ONLY_FEATURES) - set(frame)
    if missing:
        raise ValueError(f"Missing course-only features: {sorted(missing)}")
    matrix = pd.DataFrame(index=frame.index)
    for name in COURSE_ONLY_FEATURES:
        if name in CATEGORICAL_FEATURES:
            values = frame[name].astype("string").fillna(CATEGORY_MISSING)
            values = values.where(values.isin(category_levels[name]), CATEGORY_UNKNOWN)
            matrix[name] = pd.Categorical(values, categories=category_levels[name])
        else:
            matrix[name] = pd.to_numeric(frame[name], errors="coerce").astype("float32")
    return matrix


def prepare_course_rows(snapshot, candidates, part_id, history, *, training_as_of_part):
    """Use only the target-start snapshot, candidate properties, and frozen history."""
    validate_history_pair(history, None, history.as_of_part)
    validate_history_selection(part_id, history.as_of_part)
    if int(training_as_of_part) >= int(part_id):
        raise ValueError("Experimental model training must precede the target semester.")
    if int(snapshot["part_id"]) != int(part_id):
        raise ValueError("Snapshot must describe the target semester start.")
    missing = set(STUDENT_SNAPSHOT_COLUMNS) - set(snapshot)
    if missing:
        raise ValueError(f"Incomplete snapshot: {sorted(missing)}")
    names = [*CANDIDATE_COURSE_COLUMNS, *(["course_name"] if "course_name" in candidates else [])]
    rows = candidates[names].copy()
    rows["course_id"] = rows.course_id.astype("string").str.strip()
    if rows.course_id.isna().any() or rows.course_id.eq("").any() or rows.course_id.duplicated().any():
        raise ValueError("Candidate course IDs must be present and unique.")
    rows = rows.sort_values("course_id", kind="stable").reset_index(drop=True)
    for name in STUDENT_SNAPSHOT_COLUMNS:
        rows[name] = snapshot[name]
    rows["part_id"], rows["part_semester"] = int(part_id), int(part_id) % 10
    if "course_name" not in rows:
        rows["course_name"] = None
    applied = history.apply(rows)
    rows[COURSE_HISTORY_COLUMNS] = applied[COURSE_HISTORY_COLUMNS].to_numpy()
    return rows


def score_courses_once(rows, grade_model, fail_model, levels, grade_scale, *, num_threads=4):
    """One batched Grade call and one Fail call, exactly N candidate rows each."""
    started = perf_counter()
    matrix = prepare_course_matrix(rows, levels)
    marks = np.asarray(grade_model.predict(matrix, num_threads=num_threads), dtype=float)
    failures = np.asarray(fail_model.predict(matrix, num_threads=num_threads), dtype=float)
    if marks.shape != (len(rows),) or failures.shape != (len(rows),):
        raise ValueError("Model prediction shape does not match the candidate count.")
    if not np.isfinite(marks).all() or not np.isfinite(failures).all():
        raise ValueError("Experimental model returned non-finite predictions.")
    result = rows.copy()
    result["predicted_mark"] = np.clip(marks, 0, 100)
    result["expected_points"], result["expected_grade"] = grade_scale.convert(
        result.predicted_mark, result.grade_version_id,
    )
    result["fail_probability"] = np.clip(failures, 0, 1)
    return result, {"course_prediction_rows": len(matrix), "grade_prediction_rows": len(matrix),
                    "fail_prediction_rows": len(matrix), "model_prediction_calls": 2,
                    "prediction_seconds": perf_counter() - started}


def optimize_exact_credits(scored, target_credits, *, current_gpa, prior_credits, top_k=10):
    """Search all subsets; retain K by quality DESC, failure ASC, course-ID tuple.

    Decimal arithmetic preserves fractional credits and mathematical quality/risk
    ties. Zero-credit courses remain optional. This bounded research search does
    not prune candidates by their individual score.
    """
    started = perf_counter()
    if top_k < 1:
        raise ValueError("top_k must be positive.")
    required = ["course_credits", "expected_points", "fail_probability"]
    numeric = scored[required].apply(pd.to_numeric, errors="raise").to_numpy(dtype=float)
    if (not np.isfinite(numeric).all() or (numeric[:, 0] < 0).any()
            or (numeric[:, 1] < 0).any() or (numeric[:, 1] > 4).any()
            or (numeric[:, 2] < 0).any() or (numeric[:, 2] > 1).any()):
        raise ValueError("Invalid finite credit/points/probability scores.")
    rows = scored.copy()
    rows["course_id"] = rows.course_id.astype("string").str.strip()
    if rows.course_id.isna().any() or rows.course_id.eq("").any() or rows.course_id.duplicated().any():
        raise ValueError("Course IDs must be nonempty and unique.")
    rows = rows.sort_values("course_id", kind="stable").reset_index(drop=True)
    # Validate GPA even if there is no feasible combination.
    target = Decimal(str(target_credits))
    project_cumulative_gpa(current_gpa, prior_credits, 0, float(target))
    credits = [Decimal(str(x)) for x in rows.course_credits]
    quality = [c * Decimal(str(x)) for c, x in zip(credits, rows.expected_points)]
    risk = [c * Decimal(str(x)) for c, x in zip(credits, rows.fail_probability)]
    ids = rows.course_id.tolist()
    best, count = [], 0
    for indices in enumerate_plan_indices(rows, target_credits=target):
        count += 1
        q = sum((quality[i] for i in indices), Decimal(0))
        f = sum((risk[i] for i in indices), Decimal(0))
        insort(best, (-q, f, tuple(ids[i] for i in indices), indices))
        if len(best) > top_k:
            best.pop()
    plans = []
    for rank, (neg_q, failed, course_ids, indices) in enumerate(best, 1):
        q, total = float(-neg_q), float(target)
        plans.append({"rank": rank, "course_ids": list(course_ids),
                      "courses": rows.iloc[list(indices)].to_dict(orient="records"),
                      "total_credits": total, "expected_quality_points": q,
                      "expected_plan_gpa": q / total,
                      "projected_cumulative_gpa": float(project_cumulative_gpa(current_gpa, prior_credits, q, total)),
                      "expected_failed_credits": float(failed)})
    return plans, {"candidate_courses": len(rows), "matching_combinations": count,
                   "optimizer": "exhaustive_exact_subset_search", "retained_combinations": len(best),
                   "optimizer_seconds": perf_counter() - started}


def distribution(values):
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return {name: None for name in ["mean", "median", "p90", "p95", "max"]}
    return {"mean": float(values.mean()), "median": float(np.median(values)),
            "p90": float(np.quantile(values, .9)), "p95": float(np.quantile(values, .95)),
            "max": float(values.max())}


def plan_context_sensitivity(scored):
    """Ranges across alternative plans, grouped by student and course (std ddof=0)."""
    grouped = scored.groupby(["student_id", "course_id"], sort=True)
    detail = grouped.size().rename("prediction_rows").to_frame()
    for name in ["predicted_mark", "fail_probability"]:
        detail[f"{name}_std"] = grouped[name].std(ddof=0)
        detail[f"{name}_min"] = grouped[name].min()
        detail[f"{name}_max"] = grouped[name].max()
        detail[f"{name}_range"] = detail[f"{name}_max"] - detail[f"{name}_min"]
    detail = detail.reset_index()
    summary = {f"{name}_range": distribution(detail[f"{name}_range"])
               for name in ["predicted_mark", "fail_probability"]}
    summary["student_course_pairs"] = len(detail)
    summary["pairs_with_multiple_plans"] = int(detail.prediction_rows.gt(1).sum())
    return detail, summary


def compare_course_sets(official, experimental):
    """Compare plans by course identity; never compare enumeration IDs."""
    off = [frozenset(p["course_ids"]) for p in official[:3]]
    exp = [frozenset(p["course_ids"]) for p in experimental[:10]]
    if not off or not exp:
        raise ValueError("Both comparisons require at least one feasible plan.")
    result = {f"top1_recall_at_{k}": int(off[0] in exp[:k]) for k in [1, 3, 10]}
    result.update({f"top3_recall_at_{k}": len(set(off) & set(exp[:k])) / len(off) for k in [3, 10]})
    return result
