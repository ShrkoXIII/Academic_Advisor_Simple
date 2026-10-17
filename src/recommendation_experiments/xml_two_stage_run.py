"""Downstream reproducible orchestration; never trains or changes production inputs."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import platform
import re
import sys
from time import perf_counter

import numpy as np
import pandas as pd

from src import paths
from src.evaluation.evaluate_xml_recommendations import json_value, write_json
from src.features.frozen_history import file_sha256, load_frozen_history, validate_history_selection
from src.recommendation.engine import AcademicPlanRecommender
from src.recommendation.inputs import normalize_candidates
from src.recommendation.two_stage_artifacts import load_two_stage_artifacts
from .xml_two_stage_data import INPUT_PATHS, explicit_target, load_case, load_tables, sorted_xml_files
from .xml_two_stage_search import (
    GradeOnlyScorer, comparison_metrics, score_observed_plan, search_exhaustive, search_two_stage,
)


RUN_ROOT = paths.EVALUATION_DIR / "experiments" / "xml_two_stage"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def protected_inventory():
    """Hash all existing model/data/XML files except isolated experiment outputs."""
    inventory = {}
    for directory in (paths.MODEL_DIR, paths.DATA_DIR, paths.PROJECT_ROOT / "Xml"):
        for path in sorted(directory.rglob("*")):
            if path.is_file() and not path.is_relative_to(RUN_ROOT):
                inventory[path.relative_to(paths.PROJECT_ROOT).as_posix()] = file_sha256(path)
    return inventory


def execution_sources():
    names = ["src/paths.py", "src/grade_scale.py", "src/data/cleaning_utils.py",
             "src/data/clean_student_course.py", "src/data/academic_calendar.py", "src/data/xml_spreadsheet.py",
             "src/evaluation/evaluate_xml_recommendations.py", "src/features/feature_contract.py",
             "src/features/temporal_features.py", "src/features/frozen_history.py",
             "src/recommendation/engine.py", "src/recommendation/inputs.py", "src/recommendation/constraints.py",
             "src/recommendation/course_status.py", "src/recommendation/plan_generation.py",
             "src/recommendation/plan_scoring.py", "src/recommendation/two_stage_artifacts.py",
             "src/recommendation/ranking_policy.py"]
    names += [p.relative_to(paths.PROJECT_ROOT).as_posix() for p in (paths.PROJECT_ROOT / "src/experiments").glob("*xml_two_stage*.py")]
    names += [p.relative_to(paths.PROJECT_ROOT).as_posix() for p in (paths.PROJECT_ROOT / "src/recommendation_experiments").glob("*xml_two_stage*.py")]
    names += ["src/experiments/experiment_01_exhaustive_47.py", "src/experiments/experiment_02_two_stage.py"]
    return {name: file_sha256(paths.PROJECT_ROOT / name) for name in sorted(set(names))}


def stage_completed(cases, stage):
    return len(cases) == 10 and all(
        c.get(stage, {}).get("status") in {"ok", "no_feasible_18_credit_plan"}
        and c.get("observed", {}).get("status") == "ok"
        and (stage == "experiment_01" or c.get("verification", {}).get("observed_model47_identical") is True)
        for c in cases)


def prepare_case_frames(case, engine, tables, directory):
    """Complete validation before reserving a persisted student directory."""
    target = case.payload["target_part"]
    prepared = engine.prepare_candidates(case.snapshot, case.candidates, target)
    actual_input = case.actual_raw[["course_id", "course_credits", "course_name_sl"]].copy()
    actual_candidates, actual_import = normalize_candidates(actual_input, tables["catalog"], tables["history"],
        case.payload["student_id"], case.payload["degree_id"], target)
    observed_prepared = engine.prepare_candidates(case.snapshot, actual_candidates, target)
    directory.mkdir()
    prepared.to_parquet(directory / "prepared_candidates.parquet", index=False)
    observed_prepared.to_parquet(directory / "prepared_observed.parquet", index=False)
    case.payload["input_audit"]["observed_import"] = actual_import
    case.payload["prepared_files"] = {name: file_sha256(directory / name) for name in
                                      ("prepared_candidates.parquet", "prepared_observed.parquet")}
    return prepared, observed_prepared


def load_selected_cases(run_dir, manifest):
    return [json.loads((run_dir / "students" / entry["case_id"] / "case.json").read_text(encoding="utf-8"))
            for entry in manifest["selected_files"]]


def verify_protected(expected):
    actual = protected_inventory()
    changed = [name for name, digest in expected.items() if actual.get(name) != digest]
    added = sorted(actual.keys() - expected.keys())
    return {"status": "NOT CHANGED" if not changed and not added else "CHANGED",
            "checked_files": len(expected), "changed_or_removed": changed, "added": added}


def enrich_observed(actual, predicted):
    result = json_value(actual)
    result["status"] = "ok"
    result["predicted_actual_plan_gpa"] = predicted["expected_plan_gpa"]
    result["predicted_actual_cumulative_gpa"] = predicted["projected_cumulative_gpa"]
    result["predicted_plan"] = predicted
    result["projected_gpa_requires_repeat_policy"] = predicted["projected_gpa_requires_repeat_policy"]
    predictions = {c["course_id"]: c for c in predicted["courses"]}
    quality = 0.0
    for course in result["courses"]:
        prediction = predictions[course["course_id"]]
        course["predicted_points"] = prediction["expected_points"]
        course["predicted_mark"] = prediction["predicted_mark"]
        course["points_error"] = (prediction["expected_points"] - course["actual_points"]
                                  if course["actual_points"] is not None else None)
        if course["gpa_included"]:
            quality += course["course_credits"] * course["predicted_points"]
    observed_gpa = result.get("actual_plan_gpa")
    result["plan_gpa_error"] = predicted["expected_plan_gpa"] - observed_gpa if observed_gpa is not None else None
    result["absolute_plan_gpa_error"] = abs(result["plan_gpa_error"]) if observed_gpa is not None else None
    denominator = result["gpa_bearing_credits"]
    aligned = quality / denominator if denominator > 0 else None
    result["predicted_actual_gpa_bearing_plan_gpa"] = aligned
    result["policy_aligned_plan_gpa_error"] = aligned - observed_gpa if aligned is not None and observed_gpa is not None else None
    result["policy_aligned_absolute_plan_gpa_error"] = abs(result["policy_aligned_plan_gpa_error"]) if result["policy_aligned_plan_gpa_error"] is not None else None
    published = result.get("actual_published_end_cumulative_gpa")
    result["cumulative_gpa_error"] = predicted["projected_cumulative_gpa"] - published if published is not None else None
    if any(not c["gpa_included"] for c in result["courses"]):
        result["warnings"].append("Full-roster predicted GPA includes courses excluded by the current observed-GPA cleaner; policy-aligned error uses the same GPA-bearing denominator after prediction.")
    result["warnings"].append("Cumulative prediction is additive with prior registered credits; official repeat replacement and GPA denominator may differ.")
    return result


def verify_case_pair(case):
    first, second = case["experiment_01"], case["experiment_02"]
    if first.get("status") not in {"ok", "no_feasible_18_credit_plan"} or second.get("status") not in {"ok", "no_feasible_18_credit_plan"}:
        return {"status": "incomplete"}
    if first["counts"]["generated"] != second["counts"]["generated"]:
        raise ValueError("Exhaustive plan counts differ")
    if first["diagnostics"]["plan_identity_sha256"] != second["diagnostics"]["plan_identity_sha256"]:
        raise ValueError("Exhaustive plan identity digest differs")
    shortlist = {tuple(p["course_ids"]) for p in second.get("shortlist", [])}
    for result in (first, second):
        keys = []
        for plan in result["recommendations"]:
            ids = [c["course_id"] for c in plan["courses"]]
            if len(set(ids)) != len(ids):
                raise ValueError("Duplicate course in recommendation")
            if sum((Decimal(str(c["course_credits"])) for c in plan["courses"]), Decimal(0)) != 18:
                raise ValueError("Recommended plan does not have exactly18 credits")
            keys.append((-plan["projected_cumulative_gpa"], -plan["expected_plan_gpa"], tuple(plan["course_ids"])))
        if keys != sorted(keys):
            raise ValueError("Top recommendations are not ordered")
    if any(tuple(p["course_ids"]) not in shortlist for p in second["recommendations"]):
        raise ValueError("Stage2 recommended outside the Stage1 shortlist")
    metrics = comparison_metrics(first, second)
    if metrics["prediction_parity"]["all_match"] is False:
        raise ValueError("Model47 predictions differ for a shared plan")
    if metrics["gpa_regret"] is not None and metrics["gpa_regret"] < -1e-12:
        raise ValueError("Shortlisted plan beats exhaustive baseline: inconsistent scoring")
    case["comparison"] = metrics
    return {"status": "passed", "all_plans_same_count_and_digest": True,
            "stage2_membership_valid": True, "top3_exact18_and_sorted": True}


def summarize_run(cases):
    summary = {"requested_students": 10, "selected_students": len(cases)}
    for name in ("experiment_01", "experiment_02"):
        results = [c.get(name, {}) for c in cases]
        completed = [r for r in results if r.get("status") in {"ok", "no_feasible_18_credit_plan"}]
        summary[name + "_successful"] = sum(r.get("status") == "ok" for r in results)
        summary[name + "_completed"] = len(completed)
        summary[name + "_no_feasible"] = sum(r.get("status") == "no_feasible_18_credit_plan" for r in results)
        summary[name + "_failed"] = sum(r.get("status") not in {None, "ok", "no_feasible_18_credit_plan"} for r in results)
        summary[name + "_total_plans47"] = sum(r.get("counts", {}).get("scored47", 0) for r in results)
        summary[name + "_total_plans33"] = sum(r.get("counts", {}).get("scored33", 0) for r in results)
        summary[name + "_total_generated"] = sum(r.get("counts", {}).get("generated", 0) for r in results)
        summary[name + "_seconds"] = sum(r.get("timings", {}).get("total_seconds", 0) for r in results)
        summary[name + "_mean_seconds"] = summary[name + "_seconds"] / len(completed) if completed else None
    errors = [c["observed"]["absolute_plan_gpa_error"] for c in cases
              if c.get("observed", {}).get("status") == "ok" and c["observed"].get("absolute_plan_gpa_error") is not None]
    aligned = [c["observed"]["policy_aligned_absolute_plan_gpa_error"] for c in cases
               if c.get("observed", {}).get("status") == "ok" and c["observed"].get("policy_aligned_absolute_plan_gpa_error") is not None]
    summary.update(actual_valid_students=len(errors), actual_plan_mae=float(np.mean(errors)) if errors else None,
                   policy_aligned_actual_plan_mae=float(np.mean(aligned)) if aligned else None)
    paired = [c for c in cases if c.get("comparison", {}).get("top_1_match") is not None]
    summary.update(comparable_students=len(paired),
                   top_1_matches=sum(c["comparison"]["top_1_match"] for c in paired),
                   identical_top3_students=sum(
                       [p["course_ids"] for p in c["experiment_01"]["recommendations"]]
                       == [p["course_ids"] for p in c["experiment_02"]["recommendations"]] for c in paired),
                   aggregate_speedup=summary["experiment_01_seconds"] / summary["experiment_02_seconds"] if summary["experiment_02_seconds"] else None)
    return summary


def _persist(run_dir, cases, manifest):
    from src.experiments.xml_two_stage_reports import write_reports
    summary = summarize_run(cases)
    manifest["summary"] = summary
    manifest["updated_at_utc"] = utc_now()
    rows = []
    for case in cases:
        row = {k: case.get(k) for k in ("xml_file", "student_id", "degree_id", "target_part", "candidate_count")}
        for name in ("experiment_01", "experiment_02"):
            result = case.get(name, {})
            row[name + "_status"] = result.get("status")
            row[name + "_plans47"] = result.get("counts", {}).get("scored47")
            row[name + "_seconds"] = result.get("timings", {}).get("total_seconds")
            top = result.get("recommendations", [])
            row[name + "_best_cumulative_gpa"] = top[0]["projected_cumulative_gpa"] if top else None
        row.update({k: v for k, v in case.get("comparison", {}).items() if not isinstance(v, dict)})
        row.update({k: case.get("observed", {}).get(k) for k in (
            "actual_plan_gpa", "predicted_actual_plan_gpa", "predicted_actual_cumulative_gpa",
            "actual_published_end_cumulative_gpa", "plan_gpa_error", "absolute_plan_gpa_error",
            "policy_aligned_plan_gpa_error", "actual_total_credits", "gpa_bearing_credits")})
        rows.append(row)
        write_json(run_dir / "students" / case["case_id"] / "case.json", case)
    pd.DataFrame(rows).to_csv(run_dir / "summary.csv", index=False, encoding="utf-8-sig")
    write_json(run_dir / "summary.json", {"overview": summary, "students": rows})
    write_json(run_dir / "run_manifest.json", manifest)
    write_reports(run_dir, cases, manifest, summary)
    return summary


def _scorers(assets, threads):
    return tuple(GradeOnlyScorer(pair.grade_model, pair.category_levels, assets.grade_scale,
                                assets.manifest["stages"][stage]["feature_contract"]["model_features"], threads)
                 for pair, stage in ((assets.stage1, "stage1"), (assets.stage2, "stage2")))


def _engine(assets, history, provenance, target):
    validate_history_selection(target, history.as_of_part)
    return AcademicPlanRecommender(assets.stage2.grade_model, None, assets.stage2.category_levels,
        assets.grade_scale, history, assets.manifest["stages"]["stage2"]["provenance"]["metadata"],
        provenance={"training": {s: {"training_as_of_part": e["training_as_of_part"]}
                                  for s, e in assets.manifest["stages"].items()}, "history": provenance})


def _progress(stage, student):
    last = [perf_counter()]
    def update(event):
        if perf_counter() - last[0] > 20:
            print(f"{stage} {student}: {event.get('scored_plan_count')} plans / {event.get('elapsed_seconds'):.2f}s", flush=True)
            last[0] = perf_counter()
    return update


def run_experiment_01(args):
    run_dir = args.output_dir or RUN_ROOT / datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
    run_dir = run_dir.resolve()
    if not run_dir.is_relative_to(RUN_ROOT.resolve()):
        raise ValueError("Run output must stay inside isolated xml_two_stage output root")
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "students").mkdir()
    (run_dir / "logs").mkdir()
    started = perf_counter()
    xml_files = sorted_xml_files(args.xml_dir)
    targets = json.loads(args.target_map.read_text(encoding="utf-8-sig")) if args.target_map else {
        p.name: args.target_part for p in xml_files}
    inventory = protected_inventory()
    write_json(run_dir / "logs" / "protected_before.json", inventory)
    assets = load_two_stage_artifacts()
    tables = load_tables()
    manifest = {"manifest_version": 1, "created_at_utc": utc_now(), "timezone": "Asia/Damascus",
        "parameters": {"students_count": 10, "target_credits": 18, "experiment_1_top_n": 3,
                       "experiment_2_shortlist_size": 50, "experiment_2_top_n": 3,
                       "batch_size": args.batch_size, "num_threads": args.threads},
        "target_mapping": targets, "xml_sort_order": "natural numeric ascending filename",
        "selection_policy": "first10 input-valid distinct primary students; no replacement of no-plan/runtime failures",
        "selection_audit": [], "selected_files": [], "history": {},
        "artifact_manifest": assets.manifest, "feature_engineering_version": 2, "dataset_version": "V2",
        "input_files": {k: {"path": str(p.resolve()), "sha256": file_sha256(p)} for k, p in INPUT_PATHS.items()},
        "runtime": {"python": sys.version, "platform": platform.platform(), "executable": sys.executable},
        "ranking": ["projected_cumulative_gpa DESC", "expected_plan_gpa DESC", "canonical course_id tuple ASC"],
        "classifier_predict_calls": 0, "approximation": False,
        "production_changes": "none; only isolated new experiment modules and outputs",
        "execution_source_sha256": execution_sources(),
        "stages": {"experiment_01": "running", "experiment_02": "pending"}}
    for name in manifest["execution_source_sha256"]:
        destination = run_dir / "logs" / "execution_sources" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((paths.PROJECT_ROOT / name).read_bytes())
    write_json(run_dir / "run_manifest.json", manifest)
    selected, seen, history_cache = [], set(), {}
    for path in xml_files:
        if len(selected) == 10:
            break
        audit = {"file": path.name, "path": str(path.resolve()), "sha256": file_sha256(path)}
        try:
            target = explicit_target(path.name, targets)
            # Revalidates training before selecting a target-specific case.
            if any(e["training_as_of_part"] >= target for e in assets.manifest["stages"].values()):
                raise ValueError("Training cutoff must precede target")
            case = load_case(path, target, tables)
            if case.payload["student_id"] in seen:
                audit.update(status="excluded_duplicate_student", student_id=case.payload["student_id"])
                manifest["selection_audit"].append(audit)
                continue
            cutoff = case.payload["history_as_of_part"]
            if cutoff not in history_cache:
                history_cache[cutoff] = load_frozen_history(cutoff, dataset_version="V2")
            history, _, provenance = history_cache[cutoff]
            manifest["history"][str(cutoff)] = provenance
            engine = _engine(assets, history, provenance, target)
            directory = run_dir / "students" / case.payload["case_id"]
            prepared, observed_prepared = prepare_case_frames(case, engine, tables, directory)
            case.payload["xml_sha256"] = audit["sha256"]
            audit.update(status="selected", case_id=case.payload["case_id"], student_id=case.payload["student_id"], degree_id=case.payload["degree_id"],
                         target_part=target, history_as_of_part=cutoff)
            manifest["selected_files"].append(audit.copy())
            manifest["selection_audit"].append(audit)
            selected.append((case.payload, prepared, observed_prepared))
            seen.add(case.payload["student_id"])
        except Exception as error:
            audit.update(status="excluded_invalid_input", reason=f"{type(error).__name__}: {error}")
            manifest["selection_audit"].append(audit)
            print(f"EXCLUDED {path.name}: {audit['reason']}", flush=True)
    cases = [entry[0] for entry in selected]
    scorer33, scorer47 = _scorers(assets, args.threads)
    manifest["timings"] = {"setup_seconds": perf_counter() - started}
    for case, prepared, observed_prepared in selected:
        student = case["student_id"]
        try:
            case["experiment_01"] = search_exhaustive(prepared, scorer47, case["snapshot"]["start_agpa_points"],
                case["current_gpa_credits"], batch_size=args.batch_size, progress=_progress("01", student))
        except Exception as error:
            case["experiment_01"] = {"status": "incomplete", "reason": f"{type(error).__name__}: {error}"}
        try:
            tick = perf_counter()
            predicted = score_observed_plan(observed_prepared, scorer47, case["snapshot"]["start_agpa_points"], case["current_gpa_credits"])
            case["observed"] = enrich_observed(case["observed"], predicted)
            case["observed"]["experiment_01_prediction_seconds"] = perf_counter() - tick
        except Exception as error:
            case["observed"].update(status="prediction_unavailable", reason=f"{type(error).__name__}: {error}")
        write_json(run_dir / "students" / case["case_id"] / "case.json", case)
        r = case["experiment_01"]
        print(f"01 {student}: {r['status']} plans={r.get('counts', {}).get('scored47')} seconds={r.get('timings', {}).get('total_seconds')}", flush=True)
    manifest["stages"]["experiment_01"] = "completed" if stage_completed(cases, "experiment_01") else "incomplete"
    manifest["observed_model47_plan_counts"] = {"experiment_01": sum(c.get("observed", {}).get("status") == "ok" for c in cases)}
    manifest["incomplete_cases"] = [{"xml_file": c["xml_file"], "stage": "observed", "reason": c["observed"].get("reason")}
                                    for c in cases if c.get("observed", {}).get("status") != "ok"]
    manifest["timings"]["experiment_01_wall_seconds"] = perf_counter() - started
    manifest["protected_integrity"] = verify_protected(inventory)
    summary = _persist(run_dir, cases, manifest)
    print(f"RUN_DIR {run_dir}\nSUMMARY {json.dumps(summary, ensure_ascii=True)}", flush=True)
    return 0 if manifest["stages"]["experiment_01"] == "completed" and manifest["protected_integrity"]["status"] == "NOT CHANGED" else 2


def run_experiment_02(args):
    run_dir = args.run_dir.resolve()
    if not run_dir.is_relative_to(RUN_ROOT.resolve()):
        raise ValueError("Expected isolated experiment run directory")
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    if manifest["stages"]["experiment_02"] != "pending":
        raise ValueError("Experiment02 already attempted; use a fresh run for reproducible timing")
    if execution_sources() != manifest["execution_source_sha256"]:
        raise ValueError("Execution sources changed between experiments")
    before = json.loads((run_dir / "logs" / "protected_before.json").read_text(encoding="utf-8"))
    if verify_protected(before)["status"] != "NOT CHANGED":
        raise ValueError("Protected inputs changed between experiments")
    started = perf_counter()
    assets = load_two_stage_artifacts()
    if assets.manifest != manifest["artifact_manifest"]:
        raise ValueError("Model artifact contract changed between experiments")
    scorer33, scorer47 = _scorers(assets, manifest["parameters"]["num_threads"])
    cases = load_selected_cases(run_dir, manifest)
    manifest["stages"]["experiment_02"] = "running"
    write_json(run_dir / "run_manifest.json", manifest)
    for case in cases:
        directory = run_dir / "students" / case["case_id"]
        try:
            for name, digest in case["prepared_files"].items():
                if file_sha256(directory / name) != digest:
                    raise ValueError(f"Prepared input changed: {name}")
            prepared = pd.read_parquet(directory / "prepared_candidates.parquet")
            result = search_two_stage(prepared, scorer33, scorer47, case["snapshot"]["start_agpa_points"],
                case["current_gpa_credits"], batch_size=manifest["parameters"]["batch_size"],
                progress=_progress("02", case["student_id"]))
            case["experiment_02"] = result
            case["verification"] = verify_case_pair(case)
            observed_prepared = pd.read_parquet(directory / "prepared_observed.parquet")
            tick = perf_counter()
            prediction2 = score_observed_plan(observed_prepared, scorer47, case["snapshot"]["start_agpa_points"], case["current_gpa_credits"])
            case["observed"]["experiment_02_prediction_seconds"] = perf_counter() - tick
            prediction1 = case["observed"].get("predicted_plan")
            same = json_value(prediction2) == prediction1
            case["verification"]["observed_model47_identical"] = same
            case["observed"]["experiment_02_predicted_plan"] = prediction2
            if not same:
                raise ValueError("Observed-plan model47 predictions differ between experiments")
        except Exception as error:
            case["experiment_02"] = {"status": "incomplete", "reason": f"{type(error).__name__}: {error}"}
        r = case["experiment_02"]
        print(f"02 {case['student_id']}: {r['status']} plans33={r.get('counts', {}).get('scored33')} plans47={r.get('counts', {}).get('scored47')} seconds={r.get('timings', {}).get('total_seconds')}", flush=True)
        write_json(directory / "case.json", case)
    manifest["stages"]["experiment_02"] = "completed" if stage_completed(cases, "experiment_02") else "incomplete"
    manifest["timings"]["experiment_02_wall_seconds"] = perf_counter() - started
    manifest["protected_integrity"] = verify_protected(before)
    manifest["observed_model47_plan_counts"] = {"experiment_01": sum(c.get("observed", {}).get("status") == "ok" for c in cases),
                                              "experiment_02": sum(c.get("verification", {}).get("observed_model47_identical") is True for c in cases)}
    manifest["incomplete_cases"] = [{"xml_file": c["xml_file"], "stage": n, "reason": c[n].get("reason")}
        for c in cases for n in ("experiment_01", "experiment_02") if c.get(n, {}).get("status") == "incomplete"]
    summary = _persist(run_dir, cases, manifest)
    print(f"RUN_DIR {run_dir}\nSUMMARY {json.dumps(summary, ensure_ascii=True)}", flush=True)
    return 0 if manifest["stages"]["experiment_02"] == "completed" and manifest["protected_integrity"]["status"] == "NOT CHANGED" else 2


def experiment_01_main():
    parser = argparse.ArgumentParser(description="Historical exhaustive47 grade-only XML evaluation")
    parser.add_argument("--xml-dir", type=Path, default=paths.PROJECT_ROOT / "Xml")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--target-part", type=int)
    target.add_argument("--target-map", type=Path, help="JSON filename->target_part, explicit for every scanned file")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=1000)
    return run_experiment_01(parser.parse_args())


def experiment_02_main():
    parser = argparse.ArgumentParser(description="Reuse exhaustive47 run inputs for exhaustive33->top50->47")
    parser.add_argument("--run-dir", type=Path, required=True)
    return run_experiment_02(parser.parse_args())
