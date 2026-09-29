"""Controlled plan comparisons; official inference is invoked without source edits."""
import json
from time import perf_counter

import numpy as np
import pandas as pd

from src.data.cleaning_utils import clean_column_names, clean_id
from src.features.frozen_history import file_sha256
from src.paths import (
    CLEAN_DEGREE_COURSE_PATH_V2, CLEAN_STUDENT_COURSE_PATH_V2, CLEAN_STUDENT_DIPLOMA_PATH_V2,
    CLEAN_STUDENT_STATUS_PATH_V2, COURSE_ONLY_DEBUG_DIR, COURSE_ONLY_EVALUATION_DIR,
    PROJECT_ROOT, TEMPORAL_TEST_FEATURES_PATH_V2,
)
from src.recommendation.engine import resolve_current_gpa_credits
from src.recommendation.inputs import (
    build_student_snapshot, normalize_candidates, read_candidate_file, validate_snapshot,
)
from .course_only_core import (
    compare_course_sets, distribution, optimize_exact_credits, plan_context_sensitivity,
    prepare_course_rows, score_courses_once,
)
from .course_only_training import write_json


class PredictionCounter:
    """Observe real model input counts without changing the official implementation."""
    def __init__(self, model):
        self.model, self.calls, self.rows = model, 0, 0

    def predict(self, matrix, **kwargs):
        self.calls += 1
        self.rows += len(matrix)
        return self.model.predict(matrix, **kwargs)


def official_plan_lookup(scored):
    """Construct immutable keys outside pandas' string aggregation coercions."""
    return {tuple(sorted(str(value) for value in group.course_id)): int(plan_id)
            for plan_id, group in scored.groupby("plan_id", sort=False)}


def compare_case(engine, experiment_models, candidates, snapshot, *, repeats=3):
    """Same request and history; time warm in-memory paths, alternating order."""
    grade, fail, levels, metadata = experiment_models
    gpa = float(snapshot["start_agpa_points"])
    prior_credits, _ = resolve_current_gpa_credits(snapshot)
    part = int(snapshot["part_id"])
    official_times, experimental_times = [], []
    official_counts = None
    for iteration in range(repeats):
        def official_run():
            nonlocal official_counts
            chunks = []
            before = (engine.grade_model.calls, engine.fail_model.calls, engine.grade_model.rows, engine.fail_model.rows)
            start = perf_counter()
            all_plans, result = engine.recommend(
                snapshot, candidates, part, gpa, min_credits=12, max_credits=18,
                top_n=10, batch_size=2000, course_sink=chunks.append,
            )
            official_times.append(perf_counter() - start)
            official_counts = {
                "model_prediction_calls": engine.grade_model.calls + engine.fail_model.calls - before[0] - before[1],
                "grade_prediction_rows": engine.grade_model.rows - before[2],
                "fail_prediction_rows": engine.fail_model.rows - before[3],
            }
            scored = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
            return all_plans, result, scored

        def experimental_run():
            start = perf_counter()
            course_rows = prepare_course_rows(snapshot, candidates, part, engine.course_history,
                                               training_as_of_part=metadata["training_as_of_part"])
            scores, prediction_stats = score_courses_once(course_rows, grade, fail, levels, engine.grade_scale)
            plans, optimizer_stats = optimize_exact_credits(scores, 18, current_gpa=gpa, prior_credits=prior_credits)
            experimental_times.append(perf_counter() - start)
            return scores, plans, {**prediction_stats, **optimizer_stats}

        if iteration % 2:
            scores, plans, exp_stats = experimental_run()
            all_plans, result, official_scores = official_run()
        else:
            all_plans, result, official_scores = official_run()
            scores, plans, exp_stats = experimental_run()
    if not plans or not result["recommendations"]:
        raise ValueError("No feasible exact-18-credit plan.")
    if exp_stats["matching_combinations"] != result["matching_plan_count"]:
        raise ValueError("Official and experimental feasible combination counts differ.")
    official = result["recommendations"]
    for plan in official:
        plan["course_ids"] = sorted(str(c["course_id"]) for c in plan["courses"])
    lookup = official_plan_lookup(official_scores)
    indexed = all_plans.set_index("plan_id")
    for plan in plans:
        plan_id = lookup[tuple(plan["course_ids"])]
        plan["official_rescore"] = {"plan_id_for_trace_only": int(plan_id), **indexed.loc[plan_id].to_dict()}
    off_best, exp_best = official[0], plans[0]
    comparison = {
        **compare_course_sets(official, plans),
        "student_id": str(snapshot["student_id"]), "degree_id": str(snapshot["degree_id"]),
        "part_id": part, "candidate_courses": len(candidates),
        "official_matching_plans": result["matching_plan_count"],
        "official_course_in_plan_prediction_rows": official_counts["grade_prediction_rows"],
        "experimental_course_prediction_rows": exp_stats["course_prediction_rows"],
        "official_model_prediction_calls": official_counts["model_prediction_calls"],
        "experimental_model_prediction_calls": exp_stats["model_prediction_calls"],
        "optimizer_combinations": exp_stats["matching_combinations"],
        "official_best_projected_gpa": off_best["projected_cumulative_gpa"],
        "experimental_best_projected_gpa": exp_best["projected_cumulative_gpa"],
        "projected_gpa_regret_cross_model": off_best["projected_cumulative_gpa"] - exp_best["projected_cumulative_gpa"],
        "expected_plan_gpa_regret_cross_model": off_best["expected_plan_gpa"] - exp_best["expected_plan_gpa"],
        "expected_failed_credits_difference_exp_minus_official": exp_best["expected_failed_credits"] - off_best["expected_failed_credits"],
        "official_rescored_projected_gpa_regret": off_best["projected_cumulative_gpa"] - exp_best["official_rescore"]["projected_cumulative_gpa"],
        "official_rescored_plan_gpa_regret": off_best["expected_plan_gpa"] - exp_best["official_rescore"]["expected_plan_gpa"],
        "official_runtime_seconds": float(np.median(official_times)),
        "experimental_runtime_seconds": float(np.median(experimental_times)),
        "official_runtime_repeats": official_times, "experimental_runtime_repeats": experimental_times,
        "runtime_speedup": float(np.median(official_times) / np.median(experimental_times)),
        "prediction_row_reduction_factor": official_counts["grade_prediction_rows"] / len(candidates),
        "prediction_row_reduction_percent": 100 * (1 - len(candidates) / official_counts["grade_prediction_rows"]),
        "runtime_scope": "warm in-memory recommendation; input/model/history loading and disk persistence excluded; same 4 threads",
        "timing_repeats": repeats,
    }
    official_scores["student_id"] = str(snapshot["student_id"])
    sensitivity, sensitivity_summary = plan_context_sensitivity(official_scores)
    return comparison, scores, official, plans, all_plans, official_scores, sensitivity, sensitivity_summary


def save_case(output, candidates, snapshot, imported, measured):
    output.mkdir(parents=True, exist_ok=True)
    comparison, scores, official, experimental, all_plans, official_scores, sensitivity, sens_summary = measured
    write_json(output / "snapshot.json", json.loads(pd.Series(snapshot).to_json(double_precision=15)))
    write_json(output / "import_report.json", imported)
    candidates.to_parquet(output / "candidates.parquet", index=False)
    scores.to_parquet(output / "course_scores_33.parquet", index=False)
    display = scores[["course_id", "course_name", "course_credits", "predicted_mark", "expected_grade", "expected_points", "fail_probability"]]
    display = display.rename(columns={"course_credits": "credits", "predicted_mark": "predicted_mark_33",
                                      "expected_grade": "expected_grade_33", "expected_points": "expected_points_33",
                                      "fail_probability": "fail_probability_33"})
    display.to_csv(output / "course_scores_33.csv", index=False, encoding="utf-8-sig")
    all_plans.to_parquet(output / "official_all_plans.parquet", index=False)
    official_scores.to_parquet(output / "official_course_in_plan_scores.parquet", index=False)
    sensitivity.to_parquet(output / "official_plan_context_sensitivity.parquet", index=False)
    write_json(output / "sensitivity_summary.json", sens_summary)
    # Serialize only serving outputs in plan files; unknown model inputs stay in parquet.
    plan_outputs = []
    for plan in experimental:
        item = {k: v for k, v in plan.items() if k != "courses"}
        item["courses"] = json.loads(display[display.course_id.isin(plan["course_ids"])].to_json(orient="records", double_precision=15))
        plan_outputs.append(item)
    write_json(output / "experimental_top10.json", plan_outputs)
    write_json(output / "experimental_top3.json", plan_outputs[:3])
    write_json(output / "official_top10.json", official)
    write_json(output / "comparison.json", comparison)


def select_batch_cases(*, limit=12):
    """Select unique 20251 test students with validated exported candidates; log exclusions."""
    status = pd.read_parquet(CLEAN_STUDENT_STATUS_PATH_V2)
    history = pd.read_parquet(CLEAN_STUDENT_COURSE_PATH_V2)
    diplomas = pd.read_parquet(CLEAN_STUDENT_DIPLOMA_PATH_V2)
    catalog = pd.read_parquet(CLEAN_DEGREE_COURSE_PATH_V2)
    test = pd.read_parquet(TEMPORAL_TEST_FEATURES_PATH_V2, columns=["student_id", "degree_id", "part_id"])
    test_pairs = set(map(tuple, test.loc[test.part_id.eq(20251), ["student_id", "degree_id"]].astype("string").drop_duplicates().to_numpy()))
    cases, excluded, seen = [], [], {"29485.111"}
    for path in sorted((PROJECT_ROOT / "json").glob("*.json")):
        raw = read_candidate_file(path)
        clean = clean_column_names(raw)
        if "student_id" not in clean:
            excluded.append({"source": path.name, "reason": "no student_id"})
            continue
        for student in clean_id(clean.student_id).dropna().drop_duplicates():
            record = {"source": path.name, "student_id": str(student)}
            try:
                if student in seen:
                    raise ValueError("duplicate student scenario / primary case excluded from batch")
                targets = status[status.student_id.eq(student) & status.part_id.eq(20251)]
                if len(targets) != 1:
                    raise ValueError("no unique target-20251 degree status")
                degree = str(targets.iloc[0].degree_id)
                if (str(student), degree) not in test_pairs:
                    raise ValueError("student-degree absent from 20251 V2 model holdout")
                candidates, imported = normalize_candidates(raw, catalog, history, student, degree, 20251)
                if not 2 <= len(candidates) <= 18:
                    raise ValueError(f"candidate count {len(candidates)} outside bounded sample [2,18]")
                snapshot = validate_snapshot(build_student_snapshot(status, history, diplomas, student, degree, 20251), student, degree, 20251)
                if pd.isna(snapshot["start_agpa_points"]):
                    raise ValueError("unknown starting GPA")
                resolve_current_gpa_credits(snapshot)
                seen.add(str(student))
                imported.update({"source_file": str(path), "source_sha256": file_sha256(path)})
                cases.append((candidates, snapshot, imported))
            except (ValueError, KeyError) as exc:
                excluded.append({**record, "reason": str(exc)})
    if len(cases) > limit:
        excluded.extend({"student_id": str(s["student_id"]), "reason": "deterministic sample limit"} for _, s, _ in cases[limit:])
    write_json(COURSE_ONLY_EVALUATION_DIR / "batch_selection.json", {
        "selection": "unique exported students in target-20251 V2 holdout; deterministic convenience sample; exact18; <=18 candidates",
        "max_cases": limit, "selected": [{"student_id": s["student_id"], "degree_id": s["degree_id"], "candidate_count": len(c)} for c, s, _ in cases[:limit]],
        "excluded": excluded,
    })
    return cases[:limit]


def run_comparisons(engine, experiment_models, *, repeats=3):
    from src.recommendation.inputs import load_local_inputs
    original_grade, original_fail = engine.grade_model, engine.fail_model
    engine.grade_model, engine.fail_model = PredictionCounter(original_grade), PredictionCounter(original_fail)
    try:
        source = PROJECT_ROOT / "json" / "exportdata (7).json"
        candidates, snapshot, imported = load_local_inputs(source, "29485.111", "42.111", 20251)
        imported.update({"source_file": str(source), "source_sha256": file_sha256(source)})
        measured = compare_case(engine, experiment_models, candidates, snapshot, repeats=repeats)
        save_case(COURSE_ONLY_DEBUG_DIR, candidates, snapshot, imported, measured)
        print("Primary student:", measured[0], flush=True)
        comparisons, sensitivities, failures = [], [], []
        for candidates, snapshot, imported in select_batch_cases():
            student = str(snapshot["student_id"])
            try:
                measured_case = compare_case(engine, experiment_models, candidates, snapshot, repeats=repeats)
                save_case(COURSE_ONLY_EVALUATION_DIR / "batch" / student.replace(".", "_"), candidates, snapshot, imported, measured_case)
                comparisons.append(measured_case[0])
                sensitivities.append(measured_case[6])
                print(f"Batch {student}: {len(candidates)} candidates; {measured_case[0]['official_matching_plans']} plans; speedup={measured_case[0]['runtime_speedup']:.2f}", flush=True)
            except ValueError as exc:
                failures.append({"student_id": student, "reason": str(exc)})
                print(f"Batch {student} excluded: {exc}", flush=True)
        frame = pd.DataFrame(comparisons)
        frame.drop(columns=["official_runtime_repeats", "experimental_runtime_repeats"], errors="ignore").to_parquet(
            COURSE_ONLY_EVALUATION_DIR / "batch_comparisons.parquet", index=False,
        )
        columns = ["top1_recall_at_1", "top1_recall_at_3", "top1_recall_at_10", "top3_recall_at_3", "top3_recall_at_10",
                   "projected_gpa_regret_cross_model", "expected_plan_gpa_regret_cross_model",
                   "official_rescored_projected_gpa_regret", "official_rescored_plan_gpa_regret",
                   "expected_failed_credits_difference_exp_minus_official", "runtime_speedup",
                   "prediction_row_reduction_factor", "prediction_row_reduction_percent"]
        aggregate = {"cases": len(frame), "failures": failures,
                     "distributions": {c: distribution(frame[c]) for c in columns} if len(frame) else {}}
        if sensitivities:
            detail = pd.concat(sensitivities, ignore_index=True)
            detail.to_parquet(COURSE_ONLY_EVALUATION_DIR / "batch_plan_context_sensitivity.parquet", index=False)
            aggregate["sensitivity"] = {c: distribution(detail[c]) for c in ["predicted_mark_range", "fail_probability_range"]}
            aggregate["sensitivity"]["student_course_pairs"] = len(detail)
        write_json(COURSE_ONLY_EVALUATION_DIR / "batch_summary.json", aggregate)
        return measured[0], aggregate
    finally:
        engine.grade_model, engine.fail_model = original_grade, original_fail


def capture_protected_files(*, protected_paths=None):
    """Reserve the original baseline before execution, never replace its hashes."""
    before_path = COURSE_ONLY_EVALUATION_DIR / "protected_before_sha256.json"
    if before_path.exists():
        return verify_protected_files()
    if protected_paths is None:
        roots = [PROJECT_ROOT / relative for relative in [
            "models", "data/artifacts", "data/features", "data/raw", "data/clean",
            "data/temporal", "data/merged", "data/debug/recommendation_trace_29485_111",
        ]]
        protected_paths = {p for root in roots for p in root.rglob("*")
                           if p.is_file() and "__pycache__" not in p.parts and "course_only_recommendation" not in p.parts}
        for package in ["recommendation", "modeling"]:
            protected_paths.update((PROJECT_ROOT / "src" / package).glob("*.py"))
        protected_paths.add(PROJECT_ROOT / "src/features/feature_contract.py")
    before = {p.relative_to(PROJECT_ROOT).as_posix(): file_sha256(p) for p in sorted(protected_paths)}
    before_path.parent.mkdir(parents=True, exist_ok=True)
    with before_path.open("x", encoding="utf-8") as stream:
        json.dump(before, stream, indent=2)
    return verify_protected_files()


def verify_protected_files():
    """Compare the pre-work manifest, preserving pre-existing official edits."""
    before = json.loads((COURSE_ONLY_EVALUATION_DIR / "protected_before_sha256.json").read_text(encoding="utf-8"))
    after = {name: file_sha256(PROJECT_ROOT / name) for name in before}
    changed = [name for name in before if before[name] != after[name]]
    write_json(COURSE_ONLY_EVALUATION_DIR / "protected_after_sha256.json", after)
    verification = {"protected_files": len(before), "changed": changed,
                    "official_artifacts_modified": bool(changed), "official_recommendation_modified": any(name.startswith("src/recommendation/") for name in changed)}
    write_json(COURSE_ONLY_EVALUATION_DIR / "isolation_verification.json", verification)
    if changed:
        raise ValueError(f"Protected files changed: {changed}")
    return verification
