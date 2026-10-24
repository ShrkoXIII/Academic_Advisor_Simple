"""Private immutable run storage and per-student failure isolation."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
import csv
import hashlib
import json
import math
from pathlib import Path
import re
from threading import Lock
import uuid

from .adapter import PILOT_ROOT, PilotInputError, TIMING_LIMITATION, read_students, load_student_inputs, sha256
from .enhanced import B_FEATURES, feature_readiness, plan_difficulty_balance, select_improving_plans
from .history import build_university_history, build_experimental_university_history
from .snapshots import (AFTER, BEFORE, api_data_root, manifest_context, model_versions_root,
                        preparation_reports, run_root, run_read_roots, validate_snapshot)
from .selection import normalize_models


def json_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "item"):
        return json_value(value.item())
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(json_value(value), stream, ensure_ascii=False, indent=2, allow_nan=False)


def compact_results(results):
    """Project saved top-three contexts only; never score or reorder a saved plan."""
    projected = []
    for row in results:
        item = {**row, 'experiments': {}}
        for name, experiment in row.get('experiments', {}).items():
            top = (experiment.get('analytical_plans') or [])[:3]
            fallback = (experiment.get('diagnostic_plans') or [])[:3]
            retained = top or fallback
            ids = {p.get('plan_id') for p in retained}
            item['experiments'][name] = {**experiment,
                'analytical_plans': top, 'diagnostic_plans': retained,
                'plans': (experiment.get('plans') or [])[:3],
                'course_predictions': [c for c in experiment.get('course_predictions', []) if c.get('plan_id') in ids],
                'assets': {k: v for k, v in experiment.get('assets', {}).items() if k in {
                    'status','model_version','feature_count','history_as_of_part','artifact_sha256',
                    'manifest_sha256','history_artifact_sha256','reference_sha256','grade_scale_sha256'}},
                'projection': 'saved_analytical_top3' if top else 'legacy_enumeration_prefix_not_ranked',
                'full_scored_plan_count': len(experiment.get('diagnostic_plans') or [])}
        projected.append(item)
    return projected


class RunStore:
    def __init__(self, root, *, read_roots=(), snapshot_id=None, model_root=None):
        self.root = Path(root)
        self.snapshot_id = snapshot_id
        self.read_roots = [(self.root, snapshot_id), *read_roots]
        self.model_root = Path(model_root) if model_root is not None else self.root / 'model_versions'
        if self.snapshot_id != BEFORE:
            self.root.mkdir(parents=True, exist_ok=True)

    def directory(self, run_id):
        if not isinstance(run_id, str) or not re.fullmatch(r"run_[A-Za-z0-9_-]+", run_id):
            raise ValueError("Invalid run identifier.")
        path = self.root / run_id
        if path.is_symlink() or path.resolve().parent != self.root.resolve():
            raise ValueError("Run path escapes storage.")
        return path

    def load(self, run_id, *, compact=False):
        directory, snapshot_id = self.read_directory(run_id)
        failure_file = directory / 'run_failure.json'
        if failure_file.is_file():
            failure = json.loads(failure_file.read_text(encoding='utf-8'))
            manifest = json.loads((directory / 'run_manifest.json').read_text(encoding='utf-8'))
            if manifest.get('snapshot_id', snapshot_id) != snapshot_id:
                raise ValueError('Saved run snapshot conflicts with its storage location.')
            return {'run_manifest': {**manifest, 'status': 'failed', 'error': failure.get('error')},
                    'student_results': [], 'diagnostics': failure, 'snapshot_id': snapshot_id,
                    'storage_path': str(directory.resolve())}
        result_file = directory / ('presentation_results.json' if compact and (directory / 'presentation_results.json').is_file()
                                   else 'student_results.json')
        saved = {name: json.loads((result_file if name == 'student_results' else directory / f'{name}.json').read_text(encoding='utf-8'))
                 for name in ('run_manifest','student_results','diagnostics')}
        if compact and result_file.name == 'student_results.json':
            saved['student_results'] = compact_results(saved['student_results'])
        completion = directory / 'run_completion.json'
        if completion.is_file():
            saved['completion'] = json.loads(completion.read_text(encoding='utf-8'))
        recorded = saved['run_manifest'].get('snapshot_id')
        if recorded is not None and snapshot_id is not None and recorded != snapshot_id:
            raise ValueError('Saved run snapshot conflicts with its storage location.')
        saved['snapshot_id'] = recorded or snapshot_id
        saved['storage_path'] = str(directory.resolve())
        retired_path = self.model_root / "retired_bundles.json"
        if retired_path.exists():
            retired = json.loads(retired_path.read_text(encoding="utf-8"))
            versions = saved["run_manifest"].get("model_versions", {})
            for student in saved["student_results"]:
                for name in "BC":
                    experiment = student.get("experiments", {}).get(name, {})
                    version = experiment.get("assets", {}).get("model_version") or versions.get(name)
                    if version in retired:
                        experiment.update(status="BLOCKED", prediction_status="BLOCKED", plan_status="UNAVAILABLE",
                            reason="RETIRED_EXPERIMENTAL_MODEL",
                            reason_ar="هذه النتيجة تستخدم نموذجاً تجريبياً سُحبت نسخته. شغّل المقارنة بالنسخة الحالية.",
                            retired_model_details=retired[version], plans=[], analytical_plans=[], diagnostic_plans=[], course_predictions=[])
                        forecast = student.get('observed_plan_prediction', {}).get('experiments', {}).get(name)
                        if forecast is not None:
                            forecast.update(prediction_status='BLOCKED', reason='RETIRED_EXPERIMENTAL_MODEL',
                                            expected_plan_gpa=None, course_predictions=[])
        return saved

    def load_compact(self, run_id):
        return RunStore.load(self, run_id, compact=True)

    def read_directory(self, run_id):
        self.directory(run_id)  # validate the identifier before trying compatibility roots
        for root, snapshot_id in self.read_roots:
            directory = root / run_id
            if directory.is_symlink() or directory.resolve().parent != root.resolve():
                raise ValueError('Run path escapes storage.')
            if directory.is_dir():
                return directory, snapshot_id
        raise FileNotFoundError('Run not found.')

    def list_runs(self):
        results = []
        seen = set()
        for root, snapshot_id in self.read_roots:
            for file in sorted(root.glob("run_*/run_manifest.json"), reverse=True):
                try:
                    if file.parent.is_symlink() or file.parent.name in seen:
                        continue
                    manifest = json.loads(file.read_text(encoding="utf-8"))
                    if (file.parent / 'run_failure.json').is_file():
                        manifest['status'] = 'failed'
                    if manifest.get('snapshot_id', snapshot_id) != snapshot_id:
                        continue
                    results.append({**{key: manifest.get(key) for key in
                                    ("run_id", "created_at", "student_count", "target_credits", "status")},
                                    'snapshot_id': manifest.get('snapshot_id') or snapshot_id})
                    seen.add(file.parent.name)
                except (OSError, ValueError):
                    continue
        return sorted(results, key=lambda row: row.get('created_at') or '', reverse=True)

    def save(self, run_id, manifest, results, diagnostics):
        if self.snapshot_id == BEFORE:
            raise ValueError('The before_backend_fix archive is read-only.')
        directory = self.directory(run_id)
        directory.mkdir(exist_ok=False)
        write_json(directory / "run_manifest.json", manifest)
        write_json(directory / "student_results.json", results)
        write_json(directory / 'presentation_results.json', compact_results(results))
        write_json(directory / "diagnostics.json", diagnostics)
        plans, courses = [], []
        for student in results:
            for label, experiment in student.get("experiments", {}).items():
                common = {"sample_id": student["sample_id"], "experiment": label, "status": experiment["status"],
                          "prediction_status": experiment.get("prediction_status", experiment["status"]),
                          "plan_status": experiment.get("plan_status", "UNAVAILABLE"),
                          "cumulative_gpa_status": experiment.get("cumulative_gpa_status", "UNAVAILABLE")}
                for kind in ("plans", "diagnostic_plans"):
                    for plan in experiment.get(kind, []):
                        plans.append({**common, "view": kind, **{k: v for k, v in plan.items() if k != "courses"}})
                for course in experiment.get("course_predictions", []):
                    courses.append({**common, **course})
        self._csv(directory / "plan_comparison.csv", plans,
                  ["sample_id", "experiment", "status", "view", "plan_id", "total_credits", "expected_plan_gpa",
                   "projected_cumulative_gpa", "expected_failed_credits"])
        self._csv(directory / "course_predictions.csv", courses,
                  ["sample_id", "experiment", "status", "plan_id", "course_id", "course_credits",
                   "expected_points", "fail_probability", "course_history_fallback_level", "course_history_effective_support"])

    @staticmethod
    def _csv(path, records, defaults):
        columns = list(dict.fromkeys([*defaults, *(key for record in records for key in record)]))
        with Path(path).open("x", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            for record in records:
                writer.writerow({key: json.dumps(json_value(value), ensure_ascii=False) if isinstance(value, (dict, list)) else value
                                 for key, value in record.items()})


class ComparisonRunner:
    def __init__(self, root=PILOT_ROOT, *, engine_factory=None, snapshot_id=AFTER,
                 result_enricher=None, reuse_engine=False, max_retained_jobs=64):
        self.root = Path(root)
        self.snapshot_id = validate_snapshot(snapshot_id)
        self.store = RunStore(run_root(self.root, snapshot_id), snapshot_id=snapshot_id,
            read_roots=run_read_roots(self.root), model_root=model_versions_root(self.root))
        if engine_factory is None:
            from .engine import PilotEngine
            from functools import partial
            engine_factory = partial(PilotEngine, snapshot_id=snapshot_id)
        self.engine_factory = engine_factory
        if isinstance(max_retained_jobs, bool) or not isinstance(max_retained_jobs, int) or max_retained_jobs < 1:
            raise ValueError('A positive retained job limit is required.')
        self.result_enricher = result_enricher
        self.reuse_engine, self.max_retained_jobs = reuse_engine, max_retained_jobs
        self._engine = None
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pilot-comparison")
        self.jobs, self.futures = {}, {}
        self.lock = Lock()

    def validate_request(self, sample_ids, target_credits, max_plans, *, include_reserve=False):
        if (not isinstance(sample_ids, list) or not sample_ids or len(sample_ids) > 30
                or any(not isinstance(s, str) for s in sample_ids) or len(set(sample_ids)) != len(sample_ids)):
            raise ValueError("Select distinct saved primary samples.")
        students = {s["sample_id"]: s for s in read_students(self.root, include_reserve=include_reserve)}
        if any(s not in students for s in sample_ids):
            raise ValueError("Unknown primary sample.")
        if (isinstance(target_credits, bool) or not isinstance(target_credits, (int, float))
                or not math.isfinite(target_credits) or not 0 < target_credits <= 36):
            raise ValueError("Target credits must be finite in (0,36].")
        if isinstance(max_plans, bool) or not isinstance(max_plans, int) or not 1 <= max_plans <= 2000:
            raise ValueError("Plan budget must be between 1 and 2000.")
        return [students[s] for s in sample_ids]

    def start(self, sample_ids, *, target_credits=18, max_plans=200, models=None, include_reserve=False):
        if self.snapshot_id != AFTER:
            raise ValueError('The before_backend_fix snapshot is read-only.')
        normalize_models(models)
        students = self.validate_request(sample_ids, target_credits, max_plans, include_reserve=include_reserve)
        run_id = "run_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:10]
        with self.lock:
            if sum(j['status'] == 'running' for j in self.jobs.values()) >= self.max_retained_jobs:
                raise ValueError('Pilot queue is full; wait for the current evaluation.')
            self.jobs[run_id] = {"run_id": run_id, "status": "running", "completed": 0, "total": len(students),
                                 'sample_statuses': [], 'selected_models': list(normalize_models(models))}
            self.futures[run_id] = self.executor.submit(self._execute, run_id, students, target_credits, max_plans, models)
            self._prune_jobs(run_id)
        return run_id

    def run_sync(self, sample_ids, *, target_credits=18, max_plans=200, models=None, include_reserve=False):
        run_id = self.start(sample_ids, target_credits=target_credits, max_plans=max_plans,
                            models=models, include_reserve=include_reserve)
        self.wait_for_run(run_id)
        return self.progress(run_id)

    def wait_for_run(self, run_id, timeout=None):
        return self.futures[run_id].result(timeout=timeout)

    def progress(self, run_id):
        with self.lock:
            if run_id in self.jobs:
                return {**self.jobs[run_id], 'sample_statuses': [dict(r) for r in self.jobs[run_id]['sample_statuses']]}
        saved = self.store.load_compact(run_id)
        return {"run_id": run_id, "status": saved['run_manifest'].get('status', 'completed'),
                'error': saved['run_manifest'].get('error'), "completed": len(saved["student_results"]),
                "total": len(saved["student_results"]), 'sample_statuses': saved['run_manifest'].get('sample_statuses', [])}

    def status(self):
        from .engine import build_snapshot
        engine = self.engine_factory(root=self.root)
        history = build_experimental_university_history(self.root, snapshot_id=self.snapshot_id)
        experimental = engine.inspect_experiments() if hasattr(engine, "inspect_experiments") else {}
        checked, issues = 0, []
        students = read_students(self.root)
        for student in students:
            try:
                build_snapshot(load_student_inputs(student, self.root, snapshot_id=self.snapshot_id))
                checked += 1
            except PilotInputError as error:
                issues.append({"sample_id": student["sample_id"], "code": error.code, "field": error.field})
        return {"phases": {"1": "PASS" if checked == len(students) else "PARTIAL", "2": history["status"],
                           "3": "PASS" if all(experimental.get(k, {}).get("status") == "READY" for k in "BC") else "PARTIAL",
                           "4": "PARTIAL", "5": "PARTIAL", "6": "PASS", "7": "PASS"},
                "input_validation": {"valid": checked, "total": len(students), "issues": issues},
                "snapshot_id": self.snapshot_id, "api_snapshot_path": str(api_data_root(self.root, self.snapshot_id)),
                "history": history, "strict_legacy_history_audit": build_university_history(self.root, snapshot_id=self.snapshot_id),
                "assets": {"A": engine.inspect_assets(), **experimental}, "features": self._features(experimental),
                "experimental_contracts": self._contracts(history, experimental), "feature_validation": self.feature_assessment(),
                "limitations": [TIMING_LIMITATION, "No validated GPA denominator or repeat-replacement policy.",
                                 "MAX_NEW_COURSES semantics unconfirmed; allowRegisterAllOptional=Y permits optional overflow by user clarification.",
                                 "A diagnostics use the original exhaustive47 scorer; the current serving API uses two-stage33-to47.",
                                 "B/C use compatible isolated models and an explicitly quarantined subset of university history.",
                                 "Analytical predictions do not certify registration or cumulative improvement. Historical validation is not 20251 accuracy."]}

    @staticmethod
    def _contracts(history, experimental=None):
        contracts = {}
        for name, features in [("B", B_FEATURES), ("C", [*B_FEATURES, "course_difficulty_gap", "peer_expected_points", "similar_peer_support"])]:
            ready = (experimental or {}).get(name, {})
            if ready.get("status") == "READY":
                contracts[name] = {**ready, "trained": True, "feature_count": len(ready["features"])}
                continue
            contracts[name] = {"version": "pilot-20251-" + name + "-draft-v1", "features": features,
                               "feature_count": len(features), "trained": False, "status": "BLOCKED",
                               "reason": "UNIVERSITY_HISTORY_NOT_VALIDATED" if history["status"] != "PASS" else "COMPATIBLE_MODEL_NOT_TRAINED",
                               "sha256": hashlib.sha256(json.dumps(features).encode()).hexdigest()}
        return contracts

    @staticmethod
    def _features(experimental):
        features = feature_readiness()
        if experimental.get("C", {}).get("status") == "READY":
            for name in ("course_difficulty_gap", "peer_expected_points", "similar_peer_support"):
                features[name] = {"status": "AVAILABLE_TRAINED_EXPERIMENTAL",
                                  "reason": "Measured separately on historical validation, then fitted through 20243; missing evidence stays NaN."}
        return features

    def feature_assessment(self):
        reports = preparation_reports(self.root)
        if not reports:
            return {"status": "NOT_RUN"}
        return json.loads(reports[0].read_text(encoding="utf-8"))

    def _execute(self, run_id, students, target_credits, max_plans, models=None):
        import time
        started = time.perf_counter()
        model_names = normalize_models(models)
        try:
            if self._engine is None or not self.reuse_engine:
                engine = self.engine_factory(root=self.root)
                if self.reuse_engine:
                    self._engine = engine
            else:
                engine = self._engine
            history = build_experimental_university_history(self.root, snapshot_id=self.snapshot_id)
            experimental = (engine.inspect_experiments() if any(n in model_names for n in 'BC')
                            and hasattr(engine, 'inspect_experiments') else {})
            results = []
            for student in students:
                student_started = time.perf_counter()
                with self.lock:
                    self.jobs[run_id]['current_sample_id'] = student['sample_id']
                try:
                    selection = {'models': list(model_names), 'measure_stages': True} if models is not None else {}
                    result = engine.evaluate_student(student, target_credits=target_credits, max_plans=max_plans, **selection)
                    for name, experiment in result["experiments"].items():
                        experiment["plans"] = select_improving_plans(experiment.get("plans", []))
                        for plan in experiment.get("diagnostic_plans", []):
                            if plan.get("courses"):
                                plan["plan_difficulty_balance"] = plan_difficulty_balance(plan["courses"])
                                plan["balance_prediction_source"] = name
                    if self.result_enricher is not None:
                        try:
                            result = self.result_enricher(result, student, engine, model_names)
                        except Exception as error:
                            result['observed_enrichment_status'] = 'UNAVAILABLE'
                            result['observed_enrichment_error'] = type(error).__name__
                            result.setdefault('issues', []).append('OBSERVED_DISPLAY_UNAVAILABLE')
                except Exception as error:
                    code = error.code if isinstance(error, PilotInputError) else type(error).__name__
                    result = {"sample_id": student["sample_id"], "student_id": student["student_id"], "status": "BLOCKED",
                              "issues": [{"code": code}], "experiments": {name: {"status": "BLOCKED", "reason": code,
                                     "plans": [], "diagnostic_plans": [], "course_predictions": []} for name in model_names}}
                result.setdefault('latency', {})['comparison_wall_seconds'] = time.perf_counter() - student_started
                results.append(result)
                with self.lock:
                    self.jobs[run_id]["completed"] = len(results)
                    self.jobs[run_id]['sample_statuses'].append({'sample_id': student['sample_id'], 'status': result.get('status'),
                        'models': {name: value.get('prediction_status', value.get('status')) for name, value in result['experiments'].items()},
                        'issues': result.get('issues', [])})
            created = datetime.now(timezone.utc).isoformat()
            manifest = {**manifest_context(self.root, self.snapshot_id, students),
                        "experiment_type": "comparison", "candidate_mode": "original", "actual_course_injection": False,
                        "run_id": run_id, "created_at": created, "status": "completed", "student_count": len(students),
                        'selected_models': list(model_names), 'sample_statuses': self.jobs[run_id]['sample_statuses'],
                        "selected_students": [s["sample_id"] for s in students], "target_credits": target_credits,
                        "part_id": 20251, "history_as_of_part": 20243,
                        "training_cutoff": {k: 20243 if k == 'A' or experimental.get(k, {}).get('status') == 'READY' else None for k in model_names},
                        "model_versions": {k: 'original_official_v2_47_features' if k == 'A' else experimental.get(k, {}).get('model_version') for k in model_names},
                        "data_collection_times": self._collection_times(students),
                        "models": {k: engine.inspect_assets() if k == 'A' else experimental.get(k, {}) for k in model_names}, "contracts": self._contracts(history, experimental),
                        "frozen_history": history, "student_inputs": {r["sample_id"]: r.get("input_fingerprints", {}) for r in results},
                        "students_csv_sha256": sha256(self.root / "students.csv"),
                        "generation_settings": {"target_credits": target_credits, "max_plans": max_plans, "seed": 42,
                                                "max_search_states": getattr(engine, "max_search_states", None),
                                                "search": "deterministic bounded exact-credit diagnostic enumeration; no global-optimum claim"},
                        "pilot_code_sha256": {p.relative_to(Path(__file__).parent).as_posix(): sha256(p)
                                               for p in Path(__file__).parent.rglob("*")
                                               if p.is_file() and p.suffix in {".py", ".js", ".html", ".css"}},
                        "features": self._features(experimental), "feature_validation": self.feature_assessment(), "timing_limitation": TIMING_LIMITATION,
                        "elapsed_seconds": time.perf_counter() - started,
                        'elapsed_seconds_scope': 'evaluation through manifest creation; excludes result persistence',
                        "incomplete_experiments": {r["sample_id"]: {k: v["status"] for k, v in r["experiments"].items()} for r in results},
                        "replay": {"sample_ids": [s["sample_id"] for s in students], "target_credits": target_credits, "max_plans": max_plans,
                                   'models': list(model_names), 'include_reserve': any(s.get('role') == 'reserve' for s in students)}}
            diagnostics = {"history": history, "features": self._features(experimental), "elapsed_seconds": manifest["elapsed_seconds"],
                           "student_status_counts": {state: sum(r["status"] == state for r in results) for state in {r["status"] for r in results}},
                           "failures": [{"sample_id": r["sample_id"], "issues": r.get("issues", [])} for r in results],
                           "accuracy_claim": "No accuracy improvement asserted; predictions are counterfactual diagnostics.",
                           "university_api_calls": 0, "history_commits": 0, "activations": 0}
            persistence_started = time.perf_counter()
            self.store.save(run_id, manifest, results, diagnostics)
            completion = {'total_wall_seconds': time.perf_counter() - started,
                          'persistence_seconds': time.perf_counter() - persistence_started,
                          'provenance': 'measured wall clock including engine preparation, evaluation, enrichment and result persistence',
                          'status': 'completed'}
            write_json(self.store.directory(run_id) / 'run_completion.json', completion)
            with self.lock:
                self.jobs[run_id]["status"] = "completed"
                self.jobs[run_id]['total_wall_seconds'] = completion['total_wall_seconds']
                self.jobs[run_id]['current_sample_id'] = None
                self._prune_jobs(run_id)
        except Exception as error:
            # Only this newly allocated run can receive a failure marker. Never
            # leave a partially persisted run advertised as a successful run.
            try:
                directory = self.store.directory(run_id)
                if directory.is_dir():
                    write_json(directory / 'run_failure.json', {'status': 'failed', 'error': type(error).__name__})
            except (OSError, ValueError):
                pass
            with self.lock:
                self.jobs[run_id].update(status="failed", error=type(error).__name__)
                self._prune_jobs(run_id)

    def _prune_jobs(self, current):
        """Keep bounded lifecycle metadata; persisted runs remain discoverable."""
        for old in list(self.jobs):
            if len(self.jobs) <= self.max_retained_jobs:
                break
            if old != current and self.jobs[old]['status'] != 'running':
                self.jobs.pop(old, None)
                self.futures.pop(old, None)

    def _collection_times(self, students):
        values = set()
        directory = api_data_root(self.root, self.snapshot_id)
        bases = [directory / "students" / student["sample_id"] for student in students]
        bases.append(directory / "frozen_history")
        for base in bases:
            for file in base.glob("*.meta.json"):
                try:
                    value = json.loads(file.read_text(encoding="utf-8-sig")).get("saved_at_utc")
                    if value:
                        values.add(value)
                except (OSError, ValueError):
                    continue
        return sorted(values)
