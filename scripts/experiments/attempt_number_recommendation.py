"""Compare fixed ablations on exported requests using production plan mechanics."""
from itertools import islice

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.data.cleaning_utils import clean_column_names, clean_id
from src.features.feature_contract import load_category_levels, prepare_model_matrix
from src.features.temporal_features import PLAN_CONTEXT_COLUMNS, compute_plan_context_features
from src.paths import (
    CLEAN_DEGREE_COURSE_PATH_V2, CLEAN_STUDENT_COURSE_PATH_V2,
    CLEAN_STUDENT_DIPLOMA_PATH_V2, CLEAN_STUDENT_STATUS_PATH_V2, PROJECT_ROOT,
)
from src.recommendation.engine import AcademicPlanRecommender, resolve_current_gpa_credits
from src.recommendation.inputs import build_student_snapshot, normalize_candidates, read_candidate_file, validate_snapshot
from src.recommendation.plan_generation import build_plan_rows, enumerate_plan_indices
from src.recommendation.plan_scoring import rank_plans, summarize_scored_plans
from src.experiments.attempt_number_core import EXPERIMENT_MODEL_DIR, OUTPUT_DIR, VARIANTS, transform_matrix, write_json
from src.experiments.attempt_number_analysis import distribution


def select_cases(test, *, limit=30):
    status, history, diploma, catalog = (pd.read_parquet(p) for p in [
        CLEAN_STUDENT_STATUS_PATH_V2, CLEAN_STUDENT_COURSE_PATH_V2,
        CLEAN_STUDENT_DIPLOMA_PATH_V2, CLEAN_DEGREE_COURSE_PATH_V2])
    pairs = set(map(tuple, test[["student_id", "degree_id", "part_id"]].drop_duplicates().itertuples(index=False, name=None)))
    selected, excluded, seen = [], [], set()
    for path in sorted((PROJECT_ROOT / "json").glob("*.json")):
        raw = read_candidate_file(path)
        clean = clean_column_names(raw)
        if "student_id" not in clean:
            excluded.append({"source": path.name, "reason": "no student_id"})
            continue
        for student in clean_id(clean.student_id).dropna().drop_duplicates():
            # Existing exports were used for target 20251. Explicit export semesters
            # are still checked by the official normalizer, never re-labeled.
            part = 20251
            try:
                target = status[status.student_id.eq(student) & status.part_id.eq(part)]
                if len(target) != 1:
                    raise ValueError("no unique target status")
                degree = str(target.iloc[0].degree_id)
                key = (str(student), degree, part)
                if key in seen:
                    continue
                if key not in pairs:
                    raise ValueError("not in model holdout")
                candidates, imported = normalize_candidates(raw, catalog, history, student, degree, part)
                if not 2 <= len(candidates) <= 18:
                    raise ValueError("candidate count outside bounded [2,18] sample")
                if not candidates.attempt_number.gt(1).any():
                    raise ValueError("no repeat candidates")
                plans = list(islice(enumerate_plan_indices(candidates, target_credits=18), 50001))
                if not 2 <= len(plans) <= 50000:
                    raise ValueError("require 2-50000 feasible exact-18 alternatives")
                snapshot = validate_snapshot(build_student_snapshot(status, history, diploma, student, degree, part), student, degree, part)
                if pd.isna(snapshot["start_agpa_points"]):
                    raise ValueError("unknown start GPA")
                resolve_current_gpa_credits(snapshot)
                seen.add(key)
                selected.append((candidates, snapshot, {**imported, "source": path.name}))
            except (ValueError, KeyError) as exc:
                excluded.append({"source": path.name, "student_id": str(student), "reason": str(exc)})
    selected.sort(key=lambda case: (-int(case[0].attempt_number.max()), case[1]["student_id"]))
    write_json(OUTPUT_DIR / "recommendation_selection.json", {
        "method": "deterministic convenience sample from existing JSON exports; inputs only; repeat candidates; 20251; exact18; <=18 candidates; 2-50000 plans",
        "limit": limit, "eligible_cases": len(selected),
        "selected": [{"student_id": s["student_id"], "candidate_count": len(c),
                      "max_attempt": int(c.attempt_number.max()), **i} for c, s, i in selected[:limit]],
        "excluded": excluded})
    return selected[:limit]


def run_recommendations(test):
    cases = select_cases(test)
    engine = AcademicPlanRecommender.load(history_as_of_part=20243, num_threads=4)
    levels = load_category_levels(EXPERIMENT_MODEL_DIR / "holdout/category_levels.json")
    models = {v: {t: lgb.Booster(model_file=str(EXPERIMENT_MODEL_DIR / "holdout" / f"{v}_{t}.txt"))
                  for t in ["grade", "fail"]} for v in VARIANTS}
    results = []
    for index, (candidates, snapshot, imported) in enumerate(cases, 1):
        case_name = f"case_{index:02d}"
        folder = OUTPUT_DIR / "recommendations" / case_name
        folder.mkdir(parents=True, exist_ok=True)
        candidates.to_parquet(folder / "candidates.parquet", index=False)
        write_json(folder / "snapshot.json", {k: (None if pd.isna(v) else v) for k, v in snapshot.items()})
        prepared = engine.prepare_candidates(snapshot, candidates, int(snapshot["part_id"]))
        iterator = enumerate_plan_indices(prepared, target_credits=18)
        summaries, evaluated, max_reproduction = {v: [] for v in VARIANTS}, 0, 0.
        prior_credits, _ = resolve_current_gpa_credits(snapshot)
        while batch := list(islice(iterator, 2000)):
            rows = build_plan_rows(prepared, batch, evaluated)
            rows[PLAN_CONTEXT_COLUMNS] = compute_plan_context_features(rows, group_columns=["plan_id"]).to_numpy()
            base = prepare_model_matrix(rows, levels)
            for variant in VARIANTS:
                matrix = transform_matrix(base, variant)
                scored = rows.copy()
                scored["predicted_mark"] = np.clip(models[variant]["grade"].predict(matrix, num_threads=4), 0, 100)
                scored["expected_points"], scored["expected_grade"] = engine.grade_scale.convert(scored.predicted_mark, scored.grade_version_id)
                scored["fail_probability"] = np.clip(models[variant]["fail"].predict(matrix, num_threads=4), 0, 1)
                if variant == "A":
                    production = engine.score_rows(rows)
                    max_reproduction = max(max_reproduction, float(np.abs(production.predicted_mark-scored.predicted_mark).max()),
                                           float(np.abs(production.fail_probability-scored.fail_probability).max()))
                    if max_reproduction > 1e-9:
                        raise ValueError("Recommendation baseline does not reproduce production scoring.")
                summaries[variant].append(summarize_scored_plans(scored, float(snapshot["start_agpa_points"]), prior_credits))
            evaluated += len(batch)
        ranked = {}
        for variant in VARIANTS:
            table = rank_plans(pd.concat(summaries[variant], ignore_index=True))
            table["rank"] = np.arange(1, len(table)+1)
            table.to_parquet(folder / f"plans_{variant}.parquet", index=False)
            ranked[variant] = table
        a = ranked["A"]
        for variant in ["B", "C"]:
            b = ranked[variant]
            paired = a.merge(b, on="plan_id", suffixes=("_A", "_other"), validate="one_to_one")
            differences = np.abs(paired["rank_A"]-paired["rank_other"])
            row = {"case": case_name, "variant": variant, "part_id": int(snapshot["part_id"]),
                   "candidates": len(candidates), "repeat_candidates": int(candidates.attempt_number.gt(1).sum()),
                   "third_plus_candidates": int(candidates.attempt_number.ge(3).sum()),
                   "plans": len(a), "baseline_max_scoring_difference": max_reproduction,
                   "top1_changed": bool(a.iloc[0].plan_id != b.iloc[0].plan_id),
                   "top3_order_changed": a.head(3).plan_id.tolist() != b.head(3).plan_id.tolist(),
                   "top3_set_changed": set(a.head(3).plan_id) != set(b.head(3).plan_id),
                   "top3_overlap": len(set(a.head(3).plan_id) & set(b.head(3).plan_id))/min(3,len(a)),
                   "rank_spearman": float(paired.rank_A.corr(paired.rank_other, method="spearman")),
                   "mean_absolute_rank_movement": float(differences.mean()),
                   "max_absolute_rank_movement": int(differences.max()),
                   "baseline_top1_rank_other": int(b.loc[b.plan_id.eq(a.iloc[0].plan_id), "rank"].iloc[0]),
                   "other_top1_rank_baseline": int(a.loc[a.plan_id.eq(b.iloc[0].plan_id), "rank"].iloc[0]),
                   "best_expected_plan_gpa_A": float(a.iloc[0].expected_plan_gpa),
                   "best_expected_plan_gpa_other": float(b.iloc[0].expected_plan_gpa),
                   "best_projected_gpa_A": float(a.iloc[0].projected_cumulative_gpa),
                   "best_projected_gpa_other": float(b.iloc[0].projected_cumulative_gpa)}
            for name in ["expected_plan_gpa", "projected_cumulative_gpa"]:
                for stat, value in distribution(np.abs(paired[f"{name}_A"]-paired[f"{name}_other"])).items():
                    row[f"same_plan_abs_{name}_{stat}"] = value
            results.append(row)
        print(f"RECOMMENDATION {case_name}: {len(candidates)} candidates, {evaluated} exact18 plans", flush=True)
    pd.DataFrame(results).to_csv(OUTPUT_DIR / "recommendation_comparison.csv", index=False)
    write_json(OUTPUT_DIR / "recommendation_summary.json", {
        "cases": len(cases), "third_plus_cases": sum(c.attempt_number.ge(3).any() for c, _, _ in cases),
        "limitations": "Convenience input sample; no counterfactual outcomes; ranking disagreement is sensitivity, not a quality metric. 20252 recommendation exports were not synthesized."})
    return results
