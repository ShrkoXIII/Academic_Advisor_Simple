"""Read-only A/B/C diagnostic union experiment; never a historical backtest.

Only this runner writes, exclusively to a new run directory below
experiments/actual_candidate_injection. Existing Pilot and production scorers
retain their prediction, policy and ordering behavior.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import copy, deepcopy
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import re
import subprocess
from threading import Lock
from time import perf_counter
from uuid import uuid4

import pandas as pd

from src import paths
from src.recommendation.inputs import CANDIDATE_COURSE_COLUMNS
from .adapter import PILOT_ROOT, TARGET_PART, HISTORY_AS_OF_PART, TIMING_LIMITATION, PilotInputError, read_students, sha256
from .actual_candidates import ActualCandidateSources, normalize_course_id
from .engine import PilotEngine, _candidates
from .observed import ObservedPlanStore
from .observed_prediction import ObservedPlanPredictor, blocked_forecast
from .runner import RunStore, write_json
from .snapshots import (AFTER, BEFORE, manifest_context, model_versions_root,
                        run_root, run_read_roots, validate_snapshot)


DIAGNOSTIC = "DIAGNOSTIC_ACTUAL_COURSE_INJECTION"
WARNING = "DIAGNOSTIC ONLY \u2014 ACTUAL COURSES WERE INJECTED"
REPO = Path(__file__).resolve().parents[2]


class _TimedCall:
    """Delegate unchanged inference/GradeScale calls on a request-local clone."""
    def __init__(self, target, timings, method):
        self.target, self.timings, self.method = target, timings, method

    def __getattr__(self, name):
        value = getattr(self.target, name)
        if name != self.method:
            return value

        def measured(*args, **kwargs):
            started = perf_counter()
            try:
                return value(*args, **kwargs)
            finally:
                self.timings["prediction_seconds"] += perf_counter() - started
        return measured


def _timings():
    return {"feature_extraction_seconds": 0., "prediction_seconds": 0., "ranking_seconds": 0.}


class _TimedBaseline:
    def __init__(self, baseline, timings):
        self.baseline, self.timings = baseline, timings

    def __getattr__(self, name):
        return getattr(self.baseline, name)

    def prepare_candidates(self, *args, **kwargs):
        started = perf_counter()
        try:
            return self.baseline.prepare_candidates(*args, **kwargs)
        finally:
            self.timings["feature_extraction_seconds"] += perf_counter() - started

    def score_rows(self, rows):
        scorer = copy(self.baseline)
        for field in ("grade_model", "fail_model"):
            setattr(scorer, field, _TimedCall(getattr(scorer, field), self.timings, "predict"))
        scorer.grade_scale = _TimedCall(scorer.grade_scale, self.timings, "convert")
        started, prior = perf_counter(), self.timings["prediction_seconds"]
        try:
            return scorer.score_rows(rows)
        finally:
            self.timings["feature_extraction_seconds"] += max(0., perf_counter() - started -
                (self.timings["prediction_seconds"] - prior))


class _TimedExperiments:
    def __init__(self, experiments, timings):
        self.experiments, self.timings = experiments, timings

    def inspect(self):
        return self.experiments.inspect()

    def predict_course_rows(self, rows, name):
        timing = self.timings[name]
        started, prior = perf_counter(), timing["prediction_seconds"]
        try:
            if not hasattr(self.experiments, "_load"):
                return self.experiments.predict_course_rows(rows, name)
            from .modeling import predict_course_rows
            original = self.experiments._load()
            bundle = {**original, "models": {**original["models"]}}
            models = bundle["models"][name] = {**original["models"][name]}
            for task in ("grade", "fail"):
                models[task] = _TimedCall(models[task], timing, "predict")
            bundle["grade_scale"] = _TimedCall(original["grade_scale"], timing, "convert")
            return predict_course_rows(rows, name, bundle=bundle, num_threads=4)
        finally:
            timing["feature_extraction_seconds"] += max(0., perf_counter() - started -
                (timing["prediction_seconds"] - prior))


class ActualCandidateEngine(PilotEngine):
    """Request-local candidate hook; shared original generator/scorers/ranking."""
    def __init__(self, root=PILOT_ROOT, *, sources=None, **kwargs):
        super().__init__(root, **kwargs)
        self.sources = sources if sources is not None else ActualCandidateSources()

    def _candidate_pool(self, student, inputs, catalog):
        started = perf_counter()
        error = None
        try:
            original, rules, issues, rejected = _candidates(inputs, catalog)
        except PilotInputError as caught:
            error = caught
            original = pd.DataFrame(columns=[*CANDIDATE_COURSE_COLUMNS, "course_name"])
        raw_ids = [row.get("COURSE_ID") for row in inputs["courses_api_response"]["data"]["availableCourses"]]
        if self.candidate_mode == "augmented":
            union, report = self.sources.augment(original, student, self.registrations,
                                                 original_api_course_ids=raw_ids)
        else:
            raw_set = {normalize_course_id(c) for c in raw_ids}
            model_set = {normalize_course_id(c) for c in original.course_id}
            actual_set = {normalize_course_id(c["course_id"]) for c in self.registrations}
            before = len(actual_set & raw_set)
            model_before = len(actual_set & model_set)
            union = original
            report = {"actual_course_count": len(actual_set), "original_candidate_count": len(raw_set),
                "augmented_candidate_count": len(raw_set), "original_model_candidate_count": len(original),
                "augmented_model_candidate_count": len(original), "number_of_injected_courses": 0,
                "injected_courses": [], "injected_course_ids": [], "rejected_courses": [],
                "actual_courses_in_original_candidates": before, "actual_courses_in_augmented_candidates": before,
                "actual_courses_in_augmented_model_candidates": model_before,
                "candidate_coverage_before": before / len(actual_set) if actual_set else None,
                "candidate_coverage_after": before / len(actual_set) if actual_set else None,
                "model_candidate_coverage_before": model_before / len(actual_set) if actual_set else None,
                "model_candidate_coverage_after": model_before / len(actual_set) if actual_set else None,
                "candidate_provenance": {c: {"candidate_source": "API"} for c in model_set},
                "actual_courses_excluded_by_original_policy": sorted(actual_set & (raw_set - model_set))}
        report = deepcopy(report)
        count = report["number_of_injected_courses"]
        report.update(injected_course_count=count,
            actual_in_candidates_before=report["actual_courses_in_original_candidates"],
            actual_in_candidates_after=report["actual_courses_in_augmented_candidates"],
            coverage_before=report["candidate_coverage_before"], coverage_after=report["candidate_coverage_after"],
            rejected_injections=report["rejected_courses"],
            model_actual_in_candidates_before=round(report["model_candidate_coverage_before"] * report["actual_course_count"])
                if report["model_candidate_coverage_before"] is not None else None,
            model_actual_in_candidates_after=report["actual_courses_in_augmented_model_candidates"])
        self.coverage = report
        self.candidate_seconds = perf_counter() - started
        if error is not None:
            report.update(model_pool_status="BLOCKED_ORIGINAL_API_INPUT", original_model_candidate_count=None,
                          augmented_model_candidate_count=None, model_candidate_coverage_before=None,
                          model_candidate_coverage_after=None, actual_courses_in_augmented_model_candidates=None,
                          model_actual_in_candidates_before=None, model_actual_in_candidates_after=None,
                          actual_courses_excluded_by_original_policy=[])
            raise error
        selected = union if self.candidate_mode == "augmented" else original
        # A.prepare_candidates uses the same stable lexical order. This is the
        # common order BEFORE generating the single A/B/C plan space.
        return selected.sort_values("course_id", kind="stable").reset_index(drop=True), rules, issues, rejected

    def _attach_scores(self, experiment, scored, name):
        started = perf_counter()
        try:
            return PilotEngine._attach_scores(experiment, scored, name)
        finally:
            self.model_timings[name]["ranking_seconds"] += perf_counter() - started

    def evaluate_case(self, student, *, registrations, candidate_mode="original", target_credits=18, max_plans=200):
        if candidate_mode not in {"original", "augmented"}:
            raise ValueError("Unknown candidate mode.")
        started = perf_counter()
        self.inspect_assets()
        self.inspect_experiments()
        local = copy(self)
        local.candidate_mode = candidate_mode
        local.registrations = [{k: record[k] for k in ("course_id", "course_credits")} for record in registrations]
        local.coverage, local.candidate_seconds = {}, 0.
        local.model_timings = {name: _timings() for name in "ABC"}
        if self._baseline is not None:
            local._baseline = _TimedBaseline(self._baseline, local.model_timings["A"])
        if self._experimental is not None:
            local._experimental = _TimedExperiments(self._experimental, local.model_timings)
        result = PilotEngine.evaluate_student(local, student, target_credits, max_plans)
        result.update(candidate_mode=candidate_mode, candidate_coverage=local.coverage,
            degree_id=student["degree_id"], part_id=student["part_id"], cohort_previous_gpa=student.get("previous_gpa"),
            warnings=[TIMING_LIMITATION, "STUDENT_SNAPSHOT_TEMPORAL_EQUIVALENCE_UNVERIFIED",
                      "HISTORICAL_CANDIDATE_ELIGIBILITY_NOT_VERIFIABLE"] +
                     ([DIAGNOSTIC, WARNING] if candidate_mode == "augmented" else []))
        result["latency"].update(candidate_preparation_seconds=local.candidate_seconds,
                                  total_request_seconds=perf_counter() - started)
        result["search"]["search_truncated"] = result["search"]["truncated"]
        for name, experiment in result["experiments"].items():
            experiment["latency"] = {**local.model_timings[name], "total_seconds": experiment.get("elapsed_seconds", 0.)}
            if candidate_mode == "augmented":
                provenance = local.coverage.get("candidate_provenance", {})
                for course in experiment.get("course_predictions", []):
                    source = provenance.get(normalize_course_id(course["course_id"]), {})
                    course["candidate_source"] = source.get("candidate_source", "API")
                    if course["candidate_source"] == "ACTUAL_INJECTED":
                        course["historical_eligibility_unverified"] = True
        result["snapshot_contract"] = "University declares TOTAL_* beginning-of-semester; values unchanged. Local V2 equivalence remains unverified."
        return result


def git_provenance():
    def git(*args):
        return subprocess.check_output(["git", "-c", f"safe.directory={REPO.as_posix()}", *args], cwd=REPO, text=True).strip()
    branch = git("branch", "--show-current")
    if branch not in {"new_branch", "experiment/pilot-20251-actual-candidates"}:
        raise ValueError("An explicitly approved experiment branch is required.")
    prior_branch = None
    checkout_evidence = None
    for entry in git("reflog", "-100", "--format=%gs").splitlines():
        match = re.fullmatch(r"checkout: moving from (.+) to " + re.escape(branch), entry)
        if match:
            prior_branch, checkout_evidence = match.group(1), entry
            break
    return {"branch": branch, "base_commit": git("rev-parse", "HEAD"),
            "initial_branch": "new_branch", "experiment_branch_authorized_by_user": "new_branch",
            "branch_of_origin": prior_branch or "UNVERIFIED",
            "branch_of_origin_evidence": checkout_evidence,
            "branch_of_origin_head": git("rev-parse", prior_branch) if prior_branch else None,
            "initial_worktree_status": "clean_verified_before_implementation",
            "git_status_at_start": git("status", "--short"), "commits_created": 0, "pushes": 0}


class ScenarioRunStore(RunStore):
    """Every CSV key includes candidate mode and credit experiment."""
    def __init__(self, root, **kwargs):
        kwargs.setdefault('model_root', Path(root).parent / 'model_versions')
        super().__init__(root, **kwargs)

    def load(self, run_id):
        return self._retire(super().load(run_id))

    def load_dashboard(self, run_id):
        """Read a small saved projection; never transmit every examined plan."""
        directory, snapshot_id = self.read_directory(run_id)
        if not (directory / "dashboard_results.json").exists():
            return self.load(run_id)
        saved = {name: json.loads((directory / (filename + ".json")).read_text(encoding="utf-8"))
            for name, filename in (("run_manifest", "run_manifest"), ("student_results", "dashboard_results"),
                                   ("diagnostics", "diagnostics"))}
        if saved['run_manifest'].get('snapshot_id', snapshot_id) != snapshot_id:
            raise ValueError('Saved run snapshot conflicts with its storage location.')
        saved['snapshot_id'] = saved['run_manifest'].get('snapshot_id') or snapshot_id
        saved['storage_path'] = str(directory.resolve())
        return self._retire(saved)

    def _retire(self, saved):
        registry = self.model_root / "retired_bundles.json"
        retired = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else {}
        versions = saved["run_manifest"].get("model_versions", {})
        for result in saved["student_results"]:
            for name in "BC":
                experiment = result.get("experiments", {}).get(name, {})
                version = experiment.get("assets", {}).get("model_version") or versions.get(name)
                if version not in retired:
                    continue
                for target in (experiment, result.get("observed_plan_prediction", {}).get("experiments", {}).get(name, {})):
                    target.update(status="BLOCKED", prediction_status="BLOCKED", reason="RETIRED_EXPERIMENTAL_MODEL",
                        reason_ar="Experimental model version retired; saved scores unavailable.", plans=[],
                        analytical_plans=[], diagnostic_plans=[], course_predictions=[])
        return saved

    def save(self, run_id, manifest, results, diagnostics):
        if self.snapshot_id == BEFORE:
            raise ValueError('The before_backend_fix archive is read-only.')
        directory = self.directory(run_id)
        directory.mkdir(exist_ok=False)
        for name, value in (("run_manifest", manifest), ("student_results", results), ("diagnostics", diagnostics)):
            write_json(directory / (name + ".json"), value)
        dashboard = []
        for row in results:
            projected = {**row, "experiments": {}}
            for model, experiment in row["experiments"].items():
                top = experiment.get("analytical_plans", [])
                selected_ids = {p["plan_id"] for p in top}
                projected["experiments"][model] = {**experiment, "diagnostic_plans": top,
                    "course_predictions": [course for course in experiment.get("course_predictions", [])
                                           if course.get("plan_id") in selected_ids],
                    "assets": {key: value for key, value in experiment.get("assets", {}).items() if key in {
                        "status", "feature_count", "model_features", "model_version", "history_as_of_part",
                        "artifact_sha256", "manifest_sha256", "history_artifact_sha256"}},
                    "dashboard_projection": "top3_only_full_search_metrics_preserved"}
            dashboard.append(projected)
        write_json(directory / "dashboard_results.json", dashboard)
        plans, courses, metrics = [], [], []
        for row in results:
            for model, experiment in row["experiments"].items():
                common = {"sample_id": row["sample_id"], "candidate_mode": row["candidate_mode"],
                          "credit_experiment": row["credit_experiment"], "target_credits": row["target_credits"],
                          "experiment": model, "status": experiment["status"]}
                for plan in experiment.get("diagnostic_plans", []):
                    plans.append({**common, **{k: v for k, v in plan.items() if k != "courses"}})
                courses.extend({**common, **course} for course in experiment.get("course_predictions", []))
                metrics.append({**common, **row.get("candidate_coverage", {}),
                    **experiment.get("recommendation_metrics", {}),
                    "observed_prediction_metrics": experiment.get("observed_prediction_metrics", {}),
                    "latency": {**row.get("latency", {}), **experiment.get("latency", {})}})
        keys = ["sample_id", "candidate_mode", "credit_experiment", "target_credits", "experiment", "status"]
        self._csv(directory / "plan_comparison.csv", plans, keys)
        self._csv(directory / "course_predictions.csv", courses, keys)
        self._csv(directory / "student_metrics.csv", metrics, keys)


def protected_fingerprints(root=PILOT_ROOT):
    """Hash production, immutable inputs/models, old Pilot runs and all Parquets."""
    selected = set()
    for directory in (REPO / "src", REPO / "models", Path(root) / "api_data", Path(root) / "snapshots",
                      Path(root) / "experiments", Path(root) / "before_backend_fix"):
        if directory.exists():
            selected.update(p for p in directory.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                            and "actual_candidate_injection" not in p.parts)
    selected.update((REPO / "data").rglob("*.parquet"))
    for directory in (paths.ARTIFACT_DIR,):
        selected.update(p for p in directory.rglob("*") if p.is_file())
    if (Path(root) / "students.csv").exists():
        selected.add(Path(root) / "students.csv")
    return {p.relative_to(REPO).as_posix() if p.is_relative_to(REPO) else str(p): sha256(p) for p in sorted(selected)}


class ActualCandidateRunner:
    """One queued private batch; immutable saved results and no GET inference."""
    def __init__(self, root=PILOT_ROOT, *, engine_factory=None, observed_store=None, snapshot_id=AFTER):
        self.root = Path(root)
        self.snapshot_id = validate_snapshot(snapshot_id)
        self.store = ScenarioRunStore(run_root(self.root, snapshot_id, 'actual_candidate_injection'),
            snapshot_id=snapshot_id, read_roots=run_read_roots(self.root, 'actual_candidate_injection'),
            model_root=model_versions_root(self.root))
        from functools import partial
        self.engine_factory = engine_factory or partial(ActualCandidateEngine, snapshot_id=snapshot_id)
        self.observed = observed_store if observed_store is not None else ObservedPlanStore()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="actual-candidate-diagnostic")
        self.lock, self.jobs, self.futures = Lock(), {}, {}

    def start(self, sample_ids, *, candidate_modes=None, credit_experiments=None, max_plans=200):
        if self.snapshot_id != AFTER:
            raise ValueError('The before_backend_fix snapshot is read-only.')
        modes = ["original", "augmented"] if candidate_modes is None else candidate_modes
        credits = ["fixed_18", "actual_load"] if credit_experiments is None else credit_experiments
        for values, allowed in ((modes, {"original", "augmented"}), (credits, {"fixed_18", "actual_load"})):
            if not isinstance(values, list) or not values or len(set(values)) != len(values) or not set(values) <= allowed:
                raise ValueError("Select distinct supported experiment modes.")
        if not isinstance(sample_ids, list) or not sample_ids or len(sample_ids) > 30 or len(set(sample_ids)) != len(sample_ids):
            raise ValueError("Select distinct saved primary samples.")
        if isinstance(max_plans, bool) or not isinstance(max_plans, int) or not 1 <= max_plans <= 2000:
            raise ValueError("Plan budget must be between 1 and 2000.")
        available = {s["sample_id"]: s for s in read_students(self.root)}
        if any(s not in available for s in sample_ids):
            raise ValueError("Unknown primary sample.")
        provenance = git_provenance()
        run_id = "run_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_") + uuid4().hex[:10]
        with self.lock:
            self.jobs[run_id] = {"run_id": run_id, "status": "running", "completed": 0,
                                 "total": len(sample_ids) * len(modes) * len(credits)}
        self.futures[run_id] = self.executor.submit(self._execute, run_id, [available[s] for s in sample_ids],
                                                   modes, credits, max_plans, provenance)
        return run_id

    def progress(self, run_id):
        with self.lock:
            if run_id in self.jobs:
                return dict(self.jobs[run_id])
        saved = self.store.load(run_id)
        return {"run_id": run_id, "status": "completed", "completed": len(saved["student_results"]),
                "total": len(saved["student_results"])}

    def run_sync(self, sample_ids, **kwargs):
        run_id = self.start(sample_ids, **kwargs)
        self.futures[run_id].result()
        return self.progress(run_id)

    def _execute(self, run_id, students, modes, credit_experiments, max_plans, provenance):
        from .actual_metrics import attach_recommendation_metrics, attach_prediction_metrics, summarize_results
        started = perf_counter()
        try:
            code_before = {p.relative_to(Path(__file__).parent).as_posix(): sha256(p)
                for p in Path(__file__).parent.rglob("*") if p.is_file() and p.suffix in {".py", ".js", ".html", ".css"}}
            before = protected_fingerprints(self.root)
            engine = self.engine_factory(root=self.root)
            assets = {"A": engine.inspect_assets(), **engine.inspect_experiments()}
            # Warm shared immutable source/model caches equally for both modes.
            if hasattr(engine.sources, "load"):
                engine.sources.load()
            if engine._catalog is None and hasattr(engine.sources, "catalog"):
                engine._catalog = engine.sources.catalog
            observed = {s["sample_id"]: self.observed.get(s) for s in students}
            predictor = ObservedPlanPredictor(self.root, engine=engine, snapshot_id=self.snapshot_id)
            cases, eligible = [], []
            for student in students:
                actual = observed[student["sample_id"]]
                if actual["status"] in {"AVAILABLE", "PARTIAL"}:
                    cases.append((student, [{k: c[k] for k in ("course_id", "course_credits")} for c in actual["courses"]]))
                    eligible.append(student["sample_id"])
            forecast_started = perf_counter()
            forecasts = dict(zip(eligible, predictor.predict_many(cases)))
            forecast_seconds = perf_counter() - forecast_started
            results = []
            for index, student in enumerate(students):
                actual = observed[student["sample_id"]]
                registrations = [{k: c[k] for k in ("course_id", "course_credits")} for c in actual.get("courses", [])]
                for credit_experiment in credit_experiments:
                    target = 18 if credit_experiment == "fixed_18" else actual.get("total_credits")
                    # Counterbalance warm/order effects across students.
                    ordered_modes = modes if index % 2 == 0 else list(reversed(modes))
                    for mode in ordered_modes:
                        if target is None or not registrations:
                            result = engine._empty(student, target or 18, max_plans)
                            result.update(candidate_mode=mode, issues=["ACTUAL_REGISTRATION_UNAVAILABLE"], warnings=[])
                        else:
                            result = engine.evaluate_case(student, registrations=registrations, candidate_mode=mode,
                                                          target_credits=target, max_plans=max_plans)
                        result.update(credit_experiment=credit_experiment, observed_plan=actual,
                            observed_plan_prediction=forecasts.get(student["sample_id"], blocked_forecast()),
                            target_credit_source="fixed_experiment_18" if credit_experiment == "fixed_18" else "actual_registration_DIAGNOSTIC_ONLY",
                            cohort_previous_gpa=student.get("previous_gpa"))
                        attach_recommendation_metrics(result, actual)
                        attach_prediction_metrics(result, actual, result["observed_plan_prediction"])
                        results.append(result)
                        with self.lock:
                            self.jobs[run_id]["completed"] = len(results)
            summary = summarize_results(results)
            after = protected_fingerprints(self.root)
            changed = [key for key in before if before[key] != after.get(key)]
            protection = {"status": "PASS" if not changed else "FAIL", "file_count": len(before),
                          "changed_files": changed, "before": before, "after": after,
                          "new_protected_files": sorted(set(after) - set(before))}
            if protection["new_protected_files"]:
                protection["status"] = "FAIL"
            code_after = {p.relative_to(Path(__file__).parent).as_posix(): sha256(p)
                for p in Path(__file__).parent.rglob("*") if p.is_file() and p.suffix in {".py", ".js", ".html", ".css"}}
            manifest = {**manifest_context(self.root, self.snapshot_id, students),
                "experiment_type": "actual_candidate_injection", "actual_course_injection": "augmented" in modes,
                "run_id": run_id, "created_at": datetime.now(timezone.utc).isoformat(), "status": "completed",
                "experiment": DIAGNOSTIC, "diagnostic_only": True, "student_count": len(students), "result_case_count": len(results),
                "part_id": TARGET_PART, "history_as_of_part": HISTORY_AS_OF_PART, "git": provenance,
                "models": assets, "model_versions": {k: v.get("model_version", "original_official_v2_47_features") for k, v in assets.items()},
                "generation_settings": {"max_plans": max_plans, "max_search_states": engine.max_search_states,
                    "seed": 42, "num_threads": 4, "candidate_modes": modes, "credit_experiments": credit_experiments,
                    "ordering": "original_stable_lexical_course_id_exact_first_N", "top_n": 3,
                    "mode_order": "counterbalanced_by_student_index", "cache_protocol": "shared models and sources warmed before cases"},
                "candidate_sources": engine.sources.metadata, "students_csv_sha256": sha256(self.root / "students.csv"),
                "student_input_fingerprints": {r["sample_id"]: r.get("input_fingerprints", {}) for r in results},
                "observed_sources": {s: a.get("source", {}) for s, a in observed.items()},
                "pilot_code_sha256": code_before, "pilot_code_sha256_after": code_after,
                "code_stable_during_run": code_before == code_after,
                "observed_prediction_seconds": forecast_seconds, "elapsed_seconds": perf_counter() - started,
                "latency_definition": "features include history/context/matrix/copies/validation; prediction is Booster.predict plus GradeScale.convert; ranking includes aggregation/serialization; total excludes independent observed forecasts and immutable protection hashing",
                "warnings": [WARNING, DIAGNOSTIC, TIMING_LIMITATION, "NO_HISTORICAL_ELIGIBILITY_OR_COUNTERFACTUAL_QUALITY_CLAIM",
                    "LOW_GPA_PREDICTION_IS_SNAPSHOT_CONDITIONAL", "SEARCH_PREFIX_BIAS_RETAINED"],
                "production_changes": False, "training_performed": False, "university_api_calls": 0,
                "protection_status": protection["status"], "replay": {"sample_ids": [s["sample_id"] for s in students],
                    "candidate_modes": modes, "credit_experiments": credit_experiments, "max_plans": max_plans}}
            self.store.save(run_id, manifest, results, summary)
            directory = self.store.directory(run_id)
            write_json(directory / "protected_files.json", protection)
            write_json(directory / "metrics_summary.json", summary)
            write_json(directory / "latency_summary.json", summary["latency_summary"])
            write_json(directory / "original_results.json", [r for r in results if r["candidate_mode"] == "original"])
            write_json(directory / "augmented_results.json", [r for r in results if r["candidate_mode"] == "augmented"])
            write_json(directory / "injected_courses.json", [{"sample_id": r["sample_id"], "credit_experiment": r["credit_experiment"],
                **r.get("candidate_coverage", {})} for r in results if r["candidate_mode"] == "augmented"])
            portable_exports(directory, manifest, results, summary)
            with self.lock:
                self.jobs[run_id].update(status="completed", protection_status=protection["status"])
        except Exception as error:
            with self.lock:
                self.jobs[run_id].update(status="failed", error=type(error).__name__, reason=str(error))
            raise


def portable_exports(directory, manifest, results, summary):
    """Portable results omit model inputs, injected rows, names and student IDs."""
    output = Path(directory) / "portable_results"
    output.mkdir(exist_ok=False)
    write_json(output / "metrics_summary.json", summary)
    write_json(output / "latency_summary.json", summary["latency_summary"])
    write_json(output / "provenance.json", {key: manifest[key] for key in (
        "run_id", "created_at", "experiment", "diagnostic_only", "student_count", "result_case_count", "part_id",
        "history_as_of_part", "git", "generation_settings", "candidate_sources", "students_csv_sha256", "models",
        "pilot_code_sha256", "latency_definition", "warnings", "protection_status")})
    rows = []
    for result in results:
        coverage = result.get("candidate_coverage", {})
        for name, experiment in result["experiments"].items():
            prediction = result.get("prediction_metrics", {}).get(name, {})
            recommendation = experiment.get("recommendation_metrics", {})
            rows.append({"sample_id": result["sample_id"], "candidate_mode": result["candidate_mode"],
                "credit_experiment": result["credit_experiment"], "model": name, "status": experiment["status"],
                "target_credits": result["target_credits"], "target_credit_source": result.get("target_credit_source"),
                **{k: v for k, v in coverage.items() if isinstance(v, (int, float)) or v is None},
                **{k: v for k, v in recommendation.items() if isinstance(v, (int, float, str)) or v is None},
                **{"observed_" + k: v for k, v in prediction.items() if isinstance(v, (int, float, str)) or v is None},
                **result.get("latency", {}), **experiment.get("latency", {})})
    RunStore._csv(output / "student_summary.csv", rows, ["sample_id", "candidate_mode", "credit_experiment", "model"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-id", action="append")
    parser.add_argument("--max-plans", type=int, choices=(200, 2000), default=200)
    parser.add_argument("--candidate-mode", choices=("original", "augmented"), action="append")
    parser.add_argument("--credit-experiment", choices=("fixed_18", "actual_load"), action="append")
    args = parser.parse_args(argv)
    runner = ActualCandidateRunner()
    try:
        print(json.dumps(runner.run_sync(args.sample_id or [s["sample_id"] for s in read_students()],
            max_plans=args.max_plans, candidate_modes=args.candidate_mode, credit_experiments=args.credit_experiment)))
    finally:
        runner.executor.shutdown(wait=True)


if __name__ == "__main__":
    main()
