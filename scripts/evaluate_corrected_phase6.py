"""Offline Phase 6 recall and trade-off evidence with pinned real 33/47 models.

Only synthetic students/courses/outcomes are used. Complete Stage 2 scoring is
bounded diagnostic work here; the production engine still scores at most 50.
Run after timed benchmarks to avoid CPU contention. Nothing is approved.
"""
import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import numpy as np
import pandas as pd

from scripts.benchmark_two_stage import (
    ROOT, STRATEGIES, METRICS, _final_metrics, supported_synthetic_grade_version,
    synthetic_case,
)
from src.data.cleaning_utils import clean_id
from src.features.temporal_features import CourseHistoryState
from src.recommendation.history_update import FrozenHistoryManager, HistorySnapshot
from src.recommendation.inputs import prepare_recommendation_payloads
from src.recommendation.plan_scoring import score_course_rows
from src.recommendation.ranking import RankingStrategy, rank_academic_reference, rank_evaluation_plans
from src.recommendation.shortlist import ShortlistResult, build_stage1_shortlist
from src.recommendation.two_stage_artifacts import load_two_stage_artifacts, stage_feature_contract
from src.recommendation.two_stage_engine import TwoStagePlanRecommender, _json_value


FIXTURES = ("retake_weak", "retake_strong", "alternating", "low_gpa", "high_gpa",
            "load_12", "fractional_zero", "mixed_scope", "summer", "easy", "no_solution")
PENALTIES = ("failed_balance_penalty", "withdrawn_balance_penalty", "total_previous_balance_penalty")
BALANCE_DISTRIBUTIONS = ("failed_ratio", "withdrawn_ratio", "total_previous_ratio",
    "failed_retake_credits", "withdrawn_retake_credits", "new_credits", "other_previous_credits")
TOP_K = (3, 10)


def _hash(value):
    return sha256(json.dumps(_json_value(value), sort_keys=True, ensure_ascii=False,
        allow_nan=False, separators=(",", ":")).encode("utf8")).hexdigest()


def corrected_fixture(name, *, root=None):
    """Predetermined profiles, never fitted to ranking outputs or real students.

    History is 30 fabricated outcomes per course at cutoff 20243, with marks
    around the documented anchors below. This deliberately tests varied proxy
    quality, retake mixtures, context and scope. No historical bundle is read.
    """
    if name not in FIXTURES:
        raise ValueError("Unknown documented corrected fixture.")
    scenario = "fractional_zero_constraints" if name == "fractional_zero" else (
        name if name in {"easy", "no_solution"} else "dense_ties")
    student, request = synthetic_case(15, scenario)
    if name not in {"fractional_zero", "easy", "no_solution"}:
        student["candidates"] = student["candidates"][:12 if name == "load_12" else 10]
        request["target_credits"] = 12 if name == "load_12" else 15
        for index, course in enumerate(student["candidates"]):
            group = "FAILED" if index < 3 else "WITHDRAWN" if index < 5 else "NEW"
            if name == "mixed_scope" and index == 9:
                group = "PASSED"
            course.update(previous_course_status=group, attempt_number=1 if group == "NEW" else 2,
                plan_course_type_id=str(1 + index % 3), plan_year_order=1 + index % 4,
                plan_semester_order=1 + index % 2)
    snapshot = student["snapshot"]
    snapshot["diploma_type_id"] = "13.111"
    snapshot["start_agpa_points"] = 1.5 if name == "low_gpa" else 3.5 if name == "high_gpa" else 2.5
    snapshot["gpa_prev_1"] = snapshot["start_agpa_points"]
    snapshot["gpa_prev_2"] = max(0., snapshot["start_agpa_points"] - .25)
    if name == "summer":
        snapshot["part_id"] = request["part_id"] = 20253
    marks = []
    for index, course in enumerate(student["candidates"]):
        if name == "retake_strong":
            mark = 88 - index * 2 if index < 5 else 46 + index * 2
        elif name == "alternating":
            mark = (45, 88, 62, 79, 52, 91, 58, 83, 68, 74)[index % 10]
        else:
            mark = 43 + index * 5 if index < 5 else 72 + (index % 5) * 4
        marks.append(mark)
    outcomes = []
    for course, mark in zip(student["candidates"], marks):
        for row_index in range(30):
            outcomes.append({"part_id": 20243, "degree_id": snapshot["degree_id"],
                "faculty_id": snapshot["faculty_id"], "course_id": course["course_id"],
                "course_credits": course["course_credits"],
                "plan_requirement_type_id": course["plan_requirement_type_id"],
                "attempt_number": 2 if row_index % 3 == 0 else 1,
                "final_mark": min(100, max(0, mark + row_index % 5 - 2))})
    state = CourseHistoryState()
    state.update(pd.DataFrame(outcomes))
    manager = FrozenHistoryManager(HistorySnapshot(state, {"as_of_part": 20243,
        "dataset_version": "V2", "history_source": "fabricated_in_memory_30_rows_per_course"}),
        root=root or ROOT / "unused_corrected_synthetic_history")
    specification = {"name": name, "construction_version": "predetermined_profiles_v1",
        "student_payload": student, "request_payload": request,
        "course_history_mark_anchors": marks, "synthetic_outcome_count": len(outcomes),
        "synthetic_outcomes_sha256": _hash(outcomes), "history_as_of_part": 20243,
        "history_source": "synthetic in-memory outcomes only; no bundle persistence or training"}
    return student, request, manager, specification


def recall_evidence(shortlist_ids, oracle_ids, *, k):
    """Strict identity recall: denominator min(k, number of feasible oracle plans)."""
    shortlist_ids, oracle_ids = list(shortlist_ids), list(oracle_ids)
    if len(set(shortlist_ids)) != len(shortlist_ids) or len(set(oracle_ids)) != len(oracle_ids):
        raise ValueError("Recall requires unique plan IDs.")
    if len(shortlist_ids) > 50:
        raise ValueError("recall@50 requires at most 50 shortlist IDs.")
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("k must be a positive integer.")
    top = oracle_ids[:k]
    retained = len(set(shortlist_ids) & set(top))
    return {"k": k, "denominator": len(top), "retained_count": retained,
        "recall_at_50": retained / len(top) if top else None, "oracle_plan_ids": top,
        "lost_plan_ids": [key for key in top if key not in set(shortlist_ids)]}


def _tie_signature(row, oracle):
    academic = (row["projected_cumulative_gpa"], row["expected_failed_credits"], row["expected_plan_gpa"])
    if oracle == "academic_diagnostic":
        return academic
    flags = row["component_active_flags"]
    return (row["scope_applicable"], tuple(flags.items()),
        *(row[key] if not pd.isna(row[key]) else None for key in PENALTIES),
        *academic, int(row["pareto_front"]) if oracle == "pareto" and not pd.isna(row["pareto_front"]) else None)


def _tie_recall(shortlist_ids, ranked, *, k, oracle):
    """Sensitivity allowing exact objective ties to exchange identity at boundary."""
    records = ranked.to_dict("records")
    targets = Counter(_tie_signature(row, oracle) for row in records[:k])
    available = Counter(_tie_signature(row, oracle) for row in records if row["plan_id"] in set(shortlist_ids))
    retained = sum(min(count, available[key]) for key, count in targets.items())
    boundary = _tie_signature(records[min(k, len(records)) - 1], oracle) if records else None
    return {"recall_at_50": retained / min(k, len(records)) if records else None,
        "retained_count": retained, "boundary_exact_objective_tie_count": sum(
            _tie_signature(row, oracle) == boundary for row in records) if records else 0,
        "definition": "Exact objective equality only; does not change strict PlanID recall or production order."}


def distributions(frame):
    output = {}
    for name in (*METRICS, *BALANCE_DISTRIBUTIONS):
        values = pd.to_numeric(frame[name], errors="raise").dropna() if name in frame else pd.Series(dtype=float)
        if not np.isfinite(values.to_numpy()).all():
            raise ValueError("Distribution metrics must be finite.")
        output[name] = {"count": len(values), "disabled_or_missing_count": len(frame) - len(values),
            **{label: float(value) if len(values) else None for label, value in (
                ("mean", values.mean()), ("min", values.min()), ("p25", values.quantile(.25)),
                ("median", values.median()), ("p75", values.quantile(.75)), ("max", values.max()))}}
    return output


def _top_comparison(ranked, reference):
    comparisons = {}
    for k in TOP_K:
        top, baseline = ranked.head(k), reference.head(k)
        means, original = distributions(top), distributions(baseline)
        comparisons[f"top{k}"] = {"plan_ids": top.plan_id.tolist(), "plan_count": len(top),
            "academic_overlap": len(set(top.plan_id) & set(baseline.plan_id)),
            "distribution": means,
            "mean_change_vs_academic": {name: means[name]["mean"] - original[name]["mean"]
                if means[name]["mean"] is not None and original[name]["mean"] is not None else None for name in METRICS}}
    return comparisons


def compare_fixed_final(pool):
    """Both candidates receive exactly one shared Stage2-scored metrics frame."""
    reference = rank_academic_reference(pool, stage="final")
    choices = {}
    for name in STRATEGIES:
        strategy = RankingStrategy(stage="final", name=name)
        start = perf_counter()
        ranked = rank_evaluation_plans(pool, strategy=strategy)
        elapsed = perf_counter() - start
        repeated = rank_evaluation_plans(pool.iloc[::-1].reset_index(drop=True), strategy=strategy)
        choices[name] = {"strategy": strategy.metadata(), "elapsed_time": elapsed,
            "all_ranked_plan_ids": ranked.plan_id.tolist(), **_top_comparison(ranked, reference),
            "deterministic_under_frame_permutation": ranked.plan_id.tolist() == repeated.plan_id.tolist()}
    return {"size": len(pool), "plan_ids": pool.plan_id.tolist(),
        "scored_metrics_sha256": _hash(pool.sort_values("plan_id").to_dict("records")),
        "academic_reference_plan_ids": reference.plan_id.tolist(), "strategies": choices}


def tradeoff_examples(frame, *, limit=2):
    """Concrete higher-GPA/worse-Balance pairs; never sum penalty dimensions."""
    orders = {name: rank_evaluation_plans(frame, strategy=RankingStrategy(stage="final", name=name))
              for name in STRATEGIES}
    positions = {name: {key: index + 1 for index, key in enumerate(order.plan_id)} for name, order in orders.items()}
    fronts = orders["pareto"].set_index("plan_id").pareto_front.to_dict()
    records = frame.sort_values("plan_id").to_dict("records")
    examples = []
    for high in records:
        if not high["scope_applicable"]:
            continue
        for balanced in records:
            if not balanced["scope_applicable"] or high["projected_cumulative_gpa"] <= balanced["projected_cumulative_gpa"]:
                continue
            active = [key for key in PENALTIES if not pd.isna(high[key]) and not pd.isna(balanced[key])]
            if not active or not all(high[key] >= balanced[key] for key in active) or not any(high[key] > balanced[key] for key in active):
                continue
            def details(row):
                return {"plan_id": row["plan_id"], "course_tuple": row["course_tuple"],
                    **{name: row[name] for name in METRICS},
                    "rank_positions": {name: mapping[row["plan_id"]] for name, mapping in positions.items()},
                    "pareto_front": fronts[row["plan_id"]]}
            examples.append({"higher_gpa_worse_balance": details(high), "lower_gpa_better_balance": details(balanced),
                "strategy_preferences_differ": (positions["balance_first"][high["plan_id"]] < positions["balance_first"][balanced["plan_id"]])
                    != (positions["pareto"][high["plan_id"]] < positions["pareto"][balanced["plan_id"]]),
                "gpa_gap": high["projected_cumulative_gpa"] - balanced["projected_cumulative_gpa"]})
    examples.sort(key=lambda row: (not row["strategy_preferences_differ"], -row["gpa_gap"], row["higher_gpa_worse_balance"]["plan_id"], row["lower_gpa_better_balance"]["plan_id"]))
    return examples[:limit]


def _collect(engine, student, request):
    prepared = prepare_recommendation_payloads(student_payload=student, request_payload=request)
    base = engine._prepare_candidates(prepared, engine.history_manager.capture(target_part=prepared.snapshot["part_id"]))
    pair = engine.artifacts.stage1
    scored = score_course_rows(base, pair.grade_model, pair.fail_model, pair.category_levels,
        engine.artifacts.grade_scale, features=stage_feature_contract("stage1")["model_features"], num_threads=engine.num_threads)
    with patch("src.recommendation.shortlist.rank_evaluation_plans", lambda frame, **kwargs: frame):
        selection = build_stage1_shortlist(scored, prepared.constraints,
            stage1_shortlist_strategy=engine.stage1_shortlist_strategy,
            current_gpa=prepared.snapshot["start_agpa_points"], current_gpa_credits=prepared.snapshot["current_gpa_credits"],
            part_semester=prepared.snapshot["part_semester"])
    if selection.all_plans.empty:
        # The core skips ranking for no solution. Diagnostics carry zero-row
        # columns so empty comparisons are typed without invented plan values.
        frame = selection.all_plans.reindex(columns=[*selection.all_plans.columns,
            "scope_applicable", "component_active_flags", *PENALTIES,
            "failed_retake_credits", "withdrawn_retake_credits", "new_credits", "other_previous_credits"])
        selection = ShortlistResult(frame, frame.copy(), selection.plan_indices)
    return prepared, base, scored, selection


def evaluate_fixture(student, request, *, artifacts, history_manager, specification,
                     max_feasible_plans=1000, verify_determinism=True, threads=1, grade_version=None):
    student = deepcopy(student)
    version = supported_synthetic_grade_version(artifacts)
    if grade_version is not None:
        available = pd.to_numeric(artifacts.grade_scale.pass_bands["grade_version_id"], errors="raise")
        if isinstance(grade_version, (bool, np.bool_)):
            raise ValueError("Explicit grade_version must be a finite supported GradeScale version.")
        try:
            requested = float(grade_version)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("Explicit grade_version must be a finite supported GradeScale version.") from None
        if not np.isfinite(requested) or not available.eq(requested).any():
            raise ValueError("Explicit grade_version must be a finite supported GradeScale version.")
        version = requested
    grade_category = clean_id(pd.Series([version])).iloc[0]
    grade_category_known = {stage: grade_category in pair.category_levels["grade_version_id"]
        for stage, pair in (("stage1", artifacts.stage1), ("stage2", artifacts.stage2))}
    student["snapshot"]["grade_version_id"] = version
    engine = TwoStagePlanRecommender(artifacts, history_manager,
        stage1_shortlist_strategy=RankingStrategy(stage="stage1", name="balance_first"),
        final_ranking_strategy=RankingStrategy(stage="final", name="balance_first"), num_threads=threads)
    start = perf_counter()
    prepared, base, scored, selection = _collect(engine, student, request)
    setup_seconds = perf_counter() - start
    if len(selection.all_plans) > max_feasible_plans:
        raise ValueError("Fixture exceeds the complete Stage2 offline oracle bound; reduce synthetic fixture size.")
    frame = selection.all_plans
    stage1_reference = rank_academic_reference(frame, stage="stage1")
    start = perf_counter()
    stage2_predictions = pd.DataFrame()
    score_stage2 = engine._score_stage2
    def capture_stage2(rows):
        nonlocal stage2_predictions
        stage2_predictions = score_stage2(rows)
        return stage2_predictions
    with patch.object(engine, "_score_stage2", capture_stage2):
        final_frame = _final_metrics(engine, base, ShortlistResult(frame, frame, selection.plan_indices), prepared.snapshot) if not frame.empty else frame.copy()
    stage2_seconds = perf_counter() - start
    oracles = {"academic_diagnostic": rank_academic_reference(final_frame, stage="final"),
        **{name: rank_evaluation_plans(final_frame, strategy=RankingStrategy(stage="final", name=name)) for name in STRATEGIES}}
    permutation_frame, permutation_final = None, None
    if verify_determinism:
        reversed_student = deepcopy(student)
        reversed_student["candidates"] = reversed_student["candidates"][::-1]
        repeat_prepared, repeat_base, _, repeat_selection = _collect(engine, reversed_student, request)
        permutation_frame = repeat_selection.all_plans
        permutation_final = _final_metrics(engine, repeat_base,
            ShortlistResult(permutation_frame, permutation_frame, repeat_selection.plan_indices), repeat_prepared.snapshot) if not permutation_frame.empty else permutation_frame.copy()
    first, combinations = {}, []
    for name in STRATEGIES:
        strategy = RankingStrategy(stage="stage1", name=name)
        start = perf_counter()
        ranked = rank_evaluation_plans(frame, strategy=strategy)
        elapsed = perf_counter() - start
        shortlist = ranked.head(50)
        ids = shortlist.plan_id.tolist()
        selected = final_frame.loc[final_frame.plan_id.isin(ids)].copy()
        repeated = rank_evaluation_plans(permutation_frame if permutation_frame is not None else frame.iloc[::-1], strategy=strategy)
        first[name] = {"strategy": strategy.metadata(), "plan_ids": ids, "shortlist_size": len(ids),
            "ranking_elapsed_time": elapsed, "academic_shortlist_overlap": len(set(ids) & set(stage1_reference.head(50).plan_id)),
            "stage1_distribution": distributions(shortlist), "stage2_distribution": distributions(selected),
            "scope_distribution": {"in_scope": int(shortlist.scope_applicable.sum()),
                "out_of_scope": int((~shortlist.scope_applicable.astype(bool)).sum()),
                "component_active_plan_counts": {component: sum(bool(flags[component]) for flags in shortlist.component_active_flags)
                    for component in ("failed", "withdrawn", "total_previous")}},
            "stage2_oracles": {oracle: {f"top{k}": {**recall_evidence(ids, order.plan_id, k=k),
                "lost_plan_details": order.head(k).loc[~order.head(k).plan_id.isin(ids),
                    ["plan_id", "course_tuple", *METRICS]].to_dict("records"),
                "exact_objective_tie_sensitivity": _tie_recall(ids, order, k=k, oracle=oracle)} for k in TOP_K}
                for oracle, order in oracles.items()},
            "diversity": {"distinct_courses": len({course for values in shortlist.course_tuple for course in values}),
                "distinct_credit_mixes": len(shortlist[["failed_retake_credits", "withdrawn_retake_credits", "new_credits", "other_previous_credits"]].drop_duplicates()) if not shortlist.empty else 0},
            "determinism": {"candidate_permutation_checked": verify_determinism,
                "shortlist_ids_equal": ids == repeated.head(50).plan_id.tolist(),
                "complete_order_equal": ranked.plan_id.tolist() == repeated.plan_id.tolist()}}
        for final in STRATEGIES:
            chosen = rank_evaluation_plans(selected, strategy=RankingStrategy(stage="final", name=final))
            combinations.append({"stage1_strategy": name, "final_strategy": final,
                "shortlist_ids": ids, "shortlist_stage2_metrics_sha256": _hash(selected.sort_values("plan_id").to_dict("records")),
                **_top_comparison(chosen, rank_academic_reference(selected, stage="final")),
                "global_final_oracle_retention": {f"top{k}": recall_evidence(ids, oracles[final].plan_id, k=k) for k in TOP_K}})
    fixed_ids = stage1_reference.head(50).plan_id.tolist()
    fixed = final_frame.loc[final_frame.plan_id.isin(fixed_ids)].copy()
    stage2_records = final_frame.sort_values("plan_id").to_dict("records")
    repeat_records = permutation_final.sort_values("plan_id").to_dict("records") if permutation_final is not None else stage2_records
    fixed_comparison = compare_fixed_final(fixed)
    prediction_columns = ["plan_id", "course_id", "predicted_mark", "expected_points", "expected_grade", "fail_probability"]
    prediction_records = stage2_predictions.sort_values(["plan_id", "course_id"])[prediction_columns].to_dict("records") if not stage2_predictions.empty else []
    fixed_prediction_records = [row for row in prediction_records if row["plan_id"] in set(fixed_ids)]
    fixed_comparison["stage2_course_predictions_sha256"] = _hash(fixed_prediction_records)
    return _json_value({"name": specification["name"], "construction": specification,
        "student_payload_used": student, "input_sha256": _hash({"student": student, "request": request}),
        "grade_version_id": version, "grade_scale_version_supported": True,
        "grade_version_selection": "explicit_validated_pass_band_version" if grade_version is not None else "smallest_finite_available_pass_band_version",
        "grade_version_known_category": grade_category_known,
        "candidate_count": len(base), "feasible_plan_count": len(frame),
        "stage1_row_count": len(scored), "stage2_row_count": sum(frame.course_count) if not frame.empty else 0,
        "stage1_course_predictions_sha256": _hash(scored.sort_values("course_id").to_dict("records")),
        "stage1_predictions": scored[["course_id", "predicted_mark", "expected_points", "fail_probability"]].to_dict("records"),
        "stage1": first, "stage1_shortlist_overlap": len(set(first["balance_first"]["plan_ids"]) & set(first["pareto"]["plan_ids"])),
        "fixed_final_pool": fixed_comparison, "combinations": combinations,
        "stage2_course_predictions_sha256": _hash(prediction_records),
        "stage2_course_predictions": prediction_records,
        "complete_stage2_metrics": stage2_records, "complete_stage2_metrics_sha256": _hash(stage2_records),
        "stage2_candidate_permutation_checked": verify_determinism,
        "stage2_metrics_deterministic_under_candidate_permutation": _hash(stage2_records) == _hash(repeat_records) if verify_determinism else None,
        "tradeoff_examples": tradeoff_examples(final_frame),
        "runtime": {"stage1_prediction_and_metric_collection_seconds": setup_seconds,
            "offline_complete_stage2_scoring_seconds": stage2_seconds, "threads": threads,
            "note": "Diagnostic measurements, not isolated production benchmark timings; repeated determinism work excluded."},
        "production_ranking_strategy": "UNAPPROVED"})


def summarize_evidence(cases):
    """Separate >50 recall from trivial retention and undefined no-solution cases."""
    large = [case for case in cases if case["feasible_plan_count"] > 50]
    stage1 = {}
    for name in STRATEGIES:
        oracles = {}
        for oracle in ("academic_diagnostic", *STRATEGIES):
            evidence = {}
            for k in TOP_K:
                rows = [case["stage1"][name]["stage2_oracles"][oracle][f"top{k}"] for case in large]
                denominator = sum(row["denominator"] for row in rows)
                retained = sum(row["retained_count"] for row in rows)
                evidence[f"top{k}"] = {"case_count": len(rows), "retained_count": retained,
                    "denominator": denominator, "pooled_recall_at_50": retained / denominator if denominator else None,
                    "macro_recall_at_50": float(np.mean([row["recall_at_50"] for row in rows])) if rows else None,
                    "tie_equivalent_macro_recall_at_50": float(np.mean([row["exact_objective_tie_sensitivity"]["recall_at_50"] for row in rows])) if rows else None}
            oracles[oracle] = evidence
        stage1[name] = {"oracles": oracles,
            "mean_ranking_seconds_over_gt50_fixtures": float(np.mean([case["stage1"][name]["ranking_elapsed_time"] for case in large])) if large else None}
    final = {}
    nonempty = [case for case in cases if case["feasible_plan_count"]]
    for name in STRATEGIES:
        final[name] = {f"top{k}": {metric: float(np.mean(values)) if values else None
            for metric in METRICS for values in [[case["fixed_final_pool"]["strategies"][name][f"top{k}"]["mean_change_vs_academic"][metric]
                for case in nonempty if case["fixed_final_pool"]["strategies"][name][f"top{k}"]["mean_change_vs_academic"][metric] is not None]]}
            for k in TOP_K}
    return {"stage1": stage1, "final_fixed_pool_mean_changes_vs_academic": final,
        "recall_aggregation": "Only >50-plan fixtures; equal-case macro and pooled hits reported for each oracle separately.",
        "gt50_case_names": [case["name"] for case in large],
        "le50_case_names": [case["name"] for case in cases if 0 < case["feasible_plan_count"] <= 50],
        "undefined_no_solution_case_names": [case["name"] for case in cases if not case["feasible_plan_count"]],
        "determinism_all_passed": bool(cases) and all(case["stage2_candidate_permutation_checked"]
            and case["stage2_metrics_deterministic_under_candidate_permutation"]
            and all(row["determinism"]["candidate_permutation_checked"]
                and row["determinism"]["complete_order_equal"]
                and row["determinism"]["shortlist_ids_equal"] for row in case["stage1"].values())
            and all(row["deterministic_under_frame_permutation"]
                for row in case["fixed_final_pool"]["strategies"].values()) for case in cases),
        "production_ranking_strategy": "UNAPPROVED", "approval_status": "UNAPPROVED"}


def build_report(*, names=FIXTURES, threads=1, max_feasible_plans=1000, grade_version=None):
    artifacts = load_two_stage_artifacts()
    cases = []
    for name in names:
        print(f"Corrected ranking evaluation: {name}", flush=True)
        student, request, manager, specification = corrected_fixture(name)
        cases.append(evaluate_fixture(student, request, artifacts=artifacts, history_manager=manager,
            specification=specification, max_feasible_plans=max_feasible_plans, threads=threads, grade_version=grade_version))
    sources = [Path(__file__), ROOT / "scripts/benchmark_two_stage.py", ROOT / "src/recommendation/ranking.py",
        ROOT / "src/recommendation/balance_policy.py", ROOT / "src/recommendation/shortlist.py",
        ROOT / "src/recommendation/plan_scoring.py", ROOT / "src/recommendation/two_stage_engine.py",
        ROOT / "src/features/temporal_features.py"]
    return {"phase": 6, "evidence_version": "corrected_grade_version_real_models_v1",
        "evidence_scope": "Synthetic payloads and fabricated historical outcomes with real pinned 33/47 artifacts; no real students.",
        "diagnostic_stage2_scope": "All feasible plans of bounded small synthetic fixtures outside serving only.",
        "model_and_grade_scale_provenance": artifacts.manifest,
        "manifest_sha256": sha256((ROOT / "models/shortlist_v2/manifest.json").read_bytes()).hexdigest(),
        "source_sha256": {path.relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest() for path in sources},
        "metric_definitions": {"strict_recall": "PlanID intersection with deterministic complete Stage2 oracle Top K / min(K, feasible count), K=3 or10; shortlist limit50.",
            "oracle_ties": "Production rankers retain their exact deterministic tie order; exact-objective tie sensitivity is additional diagnostic evidence.",
            "final_pool": "Academic Stage1 Top50 IDs shared by both Final candidates, scored once with Stage2.",
            "gpa": "Additive projected cumulative GPA using current_gpa_credits; no grade replacement.",
            "balance": "Each enabled distance distribution separately; missing disabled components never become zero."},
        "cases": cases, "summary": summarize_evidence(cases),
        "explicit_grade_version_requested": grade_version,
        "production_ranking_strategy": "UNAPPROVED", "ranking_approval": artifacts.manifest["ranking_approval"],
        "limitations": ["Synthetic profile results do not establish actual student improvement or statistical generalization.",
            "Complete Stage2 oracle is bounded offline diagnostic work, not a changed serving path or global serving guarantee.",
            "First supported GradeScale pass-band version can be an unknown training category; recorded version remains valid for conversion.",
            "Runtime here is diagnostic; isolated benchmark is reported separately.",
            "Historical Phase5 fabricated predictions are excluded from these real-model quality aggregates.",
            "Recommendations require separate human approval; no manifest policy is changed."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/two_stage_phase6/corrected_ranking_evaluation.json")
    parser.add_argument("--fixtures", nargs="+", choices=FIXTURES, default=list(FIXTURES))
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--max-feasible-plans", type=int, default=1000)
    parser.add_argument("--grade-version", type=float, default=None,
        help="Explicit synthetic conversion version validated against loaded pass bands; no Production default change.")
    args = parser.parse_args(argv)
    report = build_report(names=args.fixtures, threads=args.threads, max_feasible_plans=args.max_feasible_plans,
        grade_version=args.grade_version)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf8")
    print(f"Corrected evidence saved to {args.output}; approvals remain UNAPPROVED.")


if __name__ == "__main__":
    main()
