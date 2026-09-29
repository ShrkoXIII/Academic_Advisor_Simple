"""Isolated 33/34 and 47/48 inference comparison for one V2 request."""

from itertools import islice
from pathlib import Path

import numpy as np
import pandas as pd

from src.experiments.course_only_core import (
    COURSE_ONLY_FEATURES, prepare_course_rows, score_courses_once,
)
from src.experiments.course_only_training import load_experiment, write_json
from src.experiments.previous_course_status_training import load_variant
from src.features.feature_contract import BASE_FEATURES, CATEGORY_UNKNOWN
from src.features.student_course_status import STATUS_LEVELS, previous_status_for_targets
from src.paths import PROJECT_ROOT
from src.recommendation.engine import AcademicPlanRecommender, resolve_current_gpa_credits
from src.recommendation.inputs import load_local_inputs
from src.recommendation.plan_generation import build_plan_rows, enumerate_plan_indices
from src.recommendation.plan_scoring import rank_plans, summarize_scored_plans


STATUS_VALUES = tuple(STATUS_LEVELS)


def prepare_augmented_matrix(frame, levels, base_features):
    """Use the experiment's single training/inference matrix contract."""
    from src.experiments.previous_course_status_training import prepare_augmented_matrix as prepare

    return prepare(frame, levels, base_features)


def score_augmented_rows(rows, grade_model, fail_model, levels, grade_scale, base_features):
    """Score rows using the experimental contract and official GradeScale."""
    matrix = prepare_augmented_matrix(rows, levels, base_features)
    marks = np.asarray(grade_model.predict(matrix, num_threads=4), dtype="float64")
    failures = np.asarray(fail_model.predict(matrix, num_threads=4), dtype="float64")
    if marks.shape != (len(rows),) or failures.shape != (len(rows),):
        raise ValueError("Experimental prediction shape does not match model rows.")
    if not np.isfinite(marks).all() or not np.isfinite(failures).all():
        raise ValueError("Experimental model returned non-finite predictions.")
    scored = rows.copy()
    scored["predicted_mark"] = np.clip(marks, 0, 100)
    scored["expected_points"], scored["expected_grade"] = grade_scale.convert(
        scored["predicted_mark"], scored["grade_version_id"],
    )
    scored["fail_probability"] = np.clip(failures, 0, 1)
    if not np.isfinite(pd.to_numeric(scored.expected_points).to_numpy(dtype=float)).all():
        raise ValueError("GradeScale returned non-finite expected points.")
    return scored


def _pair_scored_rows(baseline, augmented, key, baseline_number, augmented_number):
    fields = [*key, "course_credits", "attempt_number", "previous_course_status",
              "predicted_mark", "fail_probability"]
    missing = (set(fields) - set(baseline)) | (set(fields) - set(augmented))
    if missing:
        raise ValueError(f"Missing score columns: {sorted(missing)}")
    if baseline.duplicated(key).any() or augmented.duplicated(key).any():
        raise ValueError("Scored row identities must be unique.")
    left_rows = baseline[fields].copy()
    left_rows["_baseline_order"] = np.arange(len(left_rows))
    paired = left_rows.merge(
        augmented[fields], on=key, how="outer", validate="one_to_one",
        suffixes=(f"_{baseline_number}", f"_{augmented_number}"),
        indicator=True, sort=False,
    )
    if len(paired) != len(baseline) or len(paired) != len(augmented) or not paired._merge.eq("both").all():
        raise ValueError("Comparisons require identical candidate rows.")
    for field in ("course_credits", "attempt_number", "previous_course_status"):
        left, right = paired[f"{field}_{baseline_number}"], paired[f"{field}_{augmented_number}"]
        if not left.equals(right):
            raise ValueError("Comparisons require identical candidate rows.")
    paired = paired.sort_values("_baseline_order", kind="stable").drop(columns=["_merge", "_baseline_order", *(f"{field}_{augmented_number}"
                                              for field in ("course_credits", "attempt_number", "previous_course_status"))])
    paired = paired.rename(columns={
        f"course_credits_{baseline_number}": "credits",
        f"attempt_number_{baseline_number}": "attempt_number",
        f"previous_course_status_{baseline_number}": "previous_course_status",
    })
    paired[f"predicted_mark_delta_{augmented_number}_minus_{baseline_number}"] = (
        paired[f"predicted_mark_{augmented_number}"] - paired[f"predicted_mark_{baseline_number}"]
    )
    paired[f"fail_probability_delta_{augmented_number}_minus_{baseline_number}"] = (
        paired[f"fail_probability_{augmented_number}"] - paired[f"fail_probability_{baseline_number}"]
    )
    return paired


def pair_course_scores(baseline, augmented):
    """Pair 33 and 34 scores by course ID, independent of input row order."""
    return _pair_scored_rows(baseline, augmented, ["course_id"], 33, 34)


def pair_plan_course_scores(baseline, augmented):
    """Pair plan-aware model scores for each exact plan-course membership."""
    return _pair_scored_rows(baseline, augmented, ["plan_id", "course_id"], 47, 48)


def pair_plan_summaries(baseline, augmented, membership):
    """Compare the same plan IDs and explain rankings through course sets."""
    required = {"plan_id", "projected_cumulative_gpa", "expected_plan_gpa", "expected_failed_credits"}
    if not required.issubset(baseline) or not required.issubset(augmented):
        raise ValueError("Missing plan summary columns.")
    if baseline.plan_id.duplicated().any() or augmented.plan_id.duplicated().any():
        raise ValueError("Plan summaries must have unique plan IDs.")
    if set(baseline.plan_id) != set(augmented.plan_id):
        raise ValueError("Plan summaries must have identical plan IDs.")
    if membership.duplicated(["plan_id", "course_id"]).any():
        raise ValueError("Duplicate course in plan membership.")
    course_sets = membership.groupby("plan_id", sort=False).course_id.agg(
        lambda values: tuple(sorted(str(value) for value in values))
    ).to_dict()
    if set(course_sets) != set(baseline.plan_id):
        raise ValueError("Plan membership must cover exactly the compared plans.")
    metrics = ["projected_cumulative_gpa", "expected_plan_gpa", "expected_failed_credits"]
    left = baseline[["plan_id", *metrics]].copy()
    right = augmented[["plan_id", *metrics]].copy()
    left["rank_47"] = np.arange(1, len(left) + 1)
    right["rank_48"] = np.arange(1, len(right) + 1)
    paired = left.merge(right, on="plan_id", how="inner", validate="one_to_one", suffixes=("_47", "_48"))
    paired["course_ids"] = paired.plan_id.map(lambda plan_id: "|".join(course_sets[plan_id]))
    for metric in metrics:
        name = "projected_gpa" if metric == "projected_cumulative_gpa" else metric
        paired[f"{name}_delta_48_minus_47"] = paired[f"{metric}_48"] - paired[f"{metric}_47"]
    top3_47 = [list(course_sets[plan_id]) for plan_id in baseline.plan_id.head(3)]
    top3_48 = [list(course_sets[plan_id]) for plan_id in augmented.plan_id.head(3)]
    summary = {
        "plan_count": len(paired),
        "top3_47": top3_47,
        "top3_48": top3_48,
        "top3_order_changed": top3_47 != top3_48,
        "top3_membership_changed": {tuple(ids) for ids in top3_47} != {tuple(ids) for ids in top3_48},
        "plans_with_rank_change": int(paired.rank_47.ne(paired.rank_48).sum()),
        "best_projected_gpa_47": float(baseline.projected_cumulative_gpa.iloc[0]),
        "best_projected_gpa_48": float(augmented.projected_cumulative_gpa.iloc[0]),
        "best_projected_gpa_delta_48_minus_47": float(
            augmented.projected_cumulative_gpa.iloc[0] - baseline.projected_cumulative_gpa.iloc[0]
        ),
    }
    return paired, summary


def _attach_status(rows, status_history):
    with_status = rows.copy()
    status = previous_status_for_targets(
        with_status[["student_id", "course_id", "part_id"]],
        status_history, withdrawal_column="withdrawn", unknown_column="unresolved",
    )
    if len(status) != len(with_status) or status.isna().any() or not status.isin((*STATUS_VALUES, CATEGORY_UNKNOWN)).all():
        raise ValueError("Student-course status helper returned invalid candidate statuses.")
    with_status["previous_course_status"] = status.to_numpy()
    return with_status


def _load_experimental_models(model_dir, variant, base_features):
    from src.experiments.previous_course_status_training import EXPERIMENT_MODEL_DIR

    if Path(model_dir).resolve() != EXPERIMENT_MODEL_DIR.resolve():
        raise ValueError("Experimental inference requires the verified model namespace")
    grade, fail, levels, metadata = load_variant(variant)
    if "previous_course_status" not in levels or not set(STATUS_VALUES).issubset(levels["previous_course_status"]):
        raise ValueError(f"{variant} category levels omit previous status values.")
    features = [*base_features, "previous_course_status"]
    if grade.feature_name() != features or fail.feature_name() != features:
        raise ValueError(f"{variant} model headers do not match the ordered feature contract.")
    return grade, fail, levels, metadata


def run_student_comparison(*, status_history, model_dir, debug_dir):
    """Score the authorized 20251 request without changing official serving."""
    if not {"student_id", "course_id", "part_id", "withdrawn", "unresolved"}.issubset(status_history):
        raise ValueError("Status history must have normalized keys, withdrawn, and unresolved flags.")
    grade48, fail48, levels48, _ = _load_experimental_models(model_dir, "plan_aware_48", BASE_FEATURES)
    grade34, fail34, levels34, metadata34 = _load_experimental_models(model_dir, "course_only_34", COURSE_ONLY_FEATURES)
    grade33, fail33, levels33, _ = load_experiment()
    engine = AcademicPlanRecommender.load(history_as_of_part=20243, num_threads=4)
    candidates, snapshot, imported = load_local_inputs(
        PROJECT_ROOT / "json" / "exportdata (7).json", "29485.111", "42.111", 20251,
    )
    if len(candidates) != 15:
        raise ValueError(f"Expected 15 exported candidates, found {len(candidates)}.")
    part = 20251
    current_gpa = float(snapshot["start_agpa_points"])
    prior_credits, _ = resolve_current_gpa_credits(snapshot)

    course_rows = prepare_course_rows(
        snapshot, candidates, part, engine.course_history,
        training_as_of_part=metadata34["training_as_of_part"],
    )
    course_rows = _attach_status(course_rows, status_history)
    scored33, _ = score_courses_once(course_rows, grade33, fail33, levels33, engine.grade_scale)
    scored34 = score_augmented_rows(course_rows, grade34, fail34, levels34, engine.grade_scale, COURSE_ONLY_FEATURES)
    course_comparison = pair_course_scores(scored33, scored34)

    plan_candidates = _attach_status(engine.prepare_candidates(snapshot, candidates, part), status_history)
    same_status = course_rows.set_index("course_id").previous_course_status.sort_index().equals(
        plan_candidates.set_index("course_id").previous_course_status.sort_index()
    )
    if not same_status:
        raise ValueError("Course-only and plan-aware candidates have different previous statuses.")
    official_summaries, augmented_summaries, paired_course_chunks = [], [], []
    evaluated = 0
    iterator = enumerate_plan_indices(plan_candidates, target_credits=18)
    while batch := list(islice(iterator, 2000)):
        rows = build_plan_rows(plan_candidates, batch, evaluated)
        scored47 = engine.score_rows(rows)
        scored48 = score_augmented_rows(scored47, grade48, fail48, levels48, engine.grade_scale, BASE_FEATURES)
        paired_course_chunks.append(pair_plan_course_scores(scored47, scored48))
        official_summaries.append(summarize_scored_plans(scored47, current_gpa, prior_credits))
        augmented_summaries.append(summarize_scored_plans(scored48, current_gpa, prior_credits))
        evaluated += len(batch)
    if evaluated != 2503:
        raise ValueError(f"Expected 2,503 exact-18 plans, found {evaluated}.")
    ranked47 = rank_plans(pd.concat(official_summaries, ignore_index=True))
    ranked48 = rank_plans(pd.concat(augmented_summaries, ignore_index=True))
    plan_courses = pd.concat(paired_course_chunks, ignore_index=True)
    plans, plan_summary = pair_plan_summaries(ranked47, ranked48, plan_courses[["plan_id", "course_id"]])

    debug_dir = Path(debug_dir)
    debug_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "course_comparison": debug_dir / "course_scores_33_vs_34.csv",
        "plan_course_comparison": debug_dir / "plan_course_scores_47_vs_48.csv",
        "plan_comparison": debug_dir / "plans_47_vs_48.csv",
        "summary": debug_dir / "student_comparison.json",
    }
    course_comparison.to_csv(output_paths["course_comparison"], index=False, encoding="utf-8-sig")
    plan_courses.to_csv(output_paths["plan_course_comparison"], index=False, encoding="utf-8-sig")
    plans.to_csv(output_paths["plan_comparison"], index=False, encoding="utf-8-sig")
    summary = {
        "student_id": "29485.111", "degree_id": "42.111", "target_part": part,
        "candidate_source": "json/exportdata (7).json", "candidate_import": imported,
        "candidate_count": len(candidates), "exact_target_credits": 18,
        "history_as_of_part": 20243,
        "status_counts": {name: int(course_rows.previous_course_status.eq(name).sum())
                          for name in (*STATUS_VALUES, CATEGORY_UNKNOWN)},
        "course_only_max_abs_mark_delta": float(course_comparison.predicted_mark_delta_34_minus_33.abs().max()),
        "course_only_max_abs_fail_delta": float(course_comparison.fail_probability_delta_34_minus_33.abs().max()),
        "plan_aware": plan_summary,
        "outputs": {name: str(path) for name, path in output_paths.items()},
    }
    write_json(output_paths["summary"], summary)
    return summary
