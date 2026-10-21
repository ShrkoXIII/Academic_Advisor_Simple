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


class RunStore:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def directory(self, run_id):
        if not isinstance(run_id, str) or not re.fullmatch(r"run_[A-Za-z0-9_-]+", run_id):
            raise ValueError("Invalid run identifier.")
        path = self.root / run_id
        if path.is_symlink() or path.resolve().parent != self.root.resolve():
            raise ValueError("Run path escapes storage.")
        return path

    def load(self, run_id):
        directory = self.directory(run_id)
        saved = {name: json.loads((directory / f"{name}.json").read_text(encoding="utf-8"))
                 for name in ("run_manifest", "student_results", "diagnostics")}
        retired_path = self.root / "model_versions" / "retired_bundles.json"
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
        return saved

    def list_runs(self):
        results = []
        for file in sorted(self.root.glob("run_*/run_manifest.json"), reverse=True):
            try:
                if file.parent.is_symlink():
                    continue
                manifest = json.loads(file.read_text(encoding="utf-8"))
                results.append({key: manifest.get(key) for key in
                                ("run_id", "created_at", "student_count", "target_credits", "status")})
            except (OSError, ValueError):
                continue
        return results

    def save(self, run_id, manifest, results, diagnostics):
        directory = self.directory(run_id)
        directory.mkdir(exist_ok=False)
        write_json(directory / "run_manifest.json", manifest)
        write_json(directory / "student_results.json", results)
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
    def __init__(self, root=PILOT_ROOT, *, engine_factory=None):
        self.root = Path(root)
        self.store = RunStore(self.root / "experiments")
        if engine_factory is None:
            from .engine import PilotEngine
            engine_factory = PilotEngine
        self.engine_factory = engine_factory
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pilot-comparison")
        self.jobs, self.futures = {}, {}
        self.lock = Lock()

    def validate_request(self, sample_ids, target_credits, max_plans):
        if (not isinstance(sample_ids, list) or not sample_ids or len(sample_ids) > 30
                or any(not isinstance(s, str) for s in sample_ids) or len(set(sample_ids)) != len(sample_ids)):
            raise ValueError("Select distinct saved primary samples.")
        students = {s["sample_id"]: s for s in read_students(self.root)}
        if any(s not in students for s in sample_ids):
            raise ValueError("Unknown primary sample.")
        if (isinstance(target_credits, bool) or not isinstance(target_credits, (int, float))
                or not math.isfinite(target_credits) or not 0 < target_credits <= 36):
            raise ValueError("Target credits must be finite in (0,36].")
        if isinstance(max_plans, bool) or not isinstance(max_plans, int) or not 1 <= max_plans <= 2000:
            raise ValueError("Plan budget must be between 1 and 2000.")
        return [students[s] for s in sample_ids]

    def start(self, sample_ids, *, target_credits=18, max_plans=200):
        students = self.validate_request(sample_ids, target_credits, max_plans)
        run_id = "run_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:10]
        with self.lock:
            self.jobs[run_id] = {"run_id": run_id, "status": "running", "completed": 0, "total": len(students)}
        self.futures[run_id] = self.executor.submit(self._execute, run_id, students, target_credits, max_plans)
        return run_id

    def run_sync(self, sample_ids, *, target_credits=18, max_plans=200):
        run_id = self.start(sample_ids, target_credits=target_credits, max_plans=max_plans)
        self.wait_for_run(run_id)
        return self.progress(run_id)

    def wait_for_run(self, run_id, timeout=None):
        return self.futures[run_id].result(timeout=timeout)

    def progress(self, run_id):
        with self.lock:
            if run_id in self.jobs:
                return dict(self.jobs[run_id])
        saved = self.store.load(run_id)
        return {"run_id": run_id, "status": "completed", "completed": len(saved["student_results"]),
                "total": len(saved["student_results"])}

    def status(self):
        from .engine import build_snapshot
        engine = self.engine_factory(root=self.root)
        history = build_experimental_university_history(self.root)
        experimental = engine.inspect_experiments() if hasattr(engine, "inspect_experiments") else {}
        checked, issues = 0, []
        students = read_students(self.root)
        for student in students:
            try:
                build_snapshot(load_student_inputs(student, self.root))
                checked += 1
            except PilotInputError as error:
                issues.append({"sample_id": student["sample_id"], "code": error.code, "field": error.field})
        return {"phases": {"1": "PASS" if checked == len(students) else "PARTIAL", "2": history["status"],
                           "3": "PASS" if all(experimental.get(k, {}).get("status") == "READY" for k in "BC") else "PARTIAL",
                           "4": "PARTIAL", "5": "PARTIAL", "6": "PASS", "7": "PASS"},
                "input_validation": {"valid": checked, "total": len(students), "issues": issues},
                "history": history, "strict_legacy_history_audit": build_university_history(self.root),
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
        reports = sorted(self.store.root.glob("preparation_*/features/feature_validation_report.json"), reverse=True)
        if not reports:
            return {"status": "NOT_RUN"}
        return json.loads(reports[0].read_text(encoding="utf-8"))

    def _execute(self, run_id, students, target_credits, max_plans):
        import time
        started = time.perf_counter()
        try:
            engine = self.engine_factory(root=self.root)
            history = build_experimental_university_history(self.root)
            experimental = engine.inspect_experiments() if hasattr(engine, "inspect_experiments") else {}
            results = []
            for student in students:
                try:
                    result = engine.evaluate_student(student, target_credits=target_credits, max_plans=max_plans)
                    for name, experiment in result["experiments"].items():
                        experiment["plans"] = select_improving_plans(experiment.get("plans", []))
                        for plan in experiment.get("diagnostic_plans", []):
                            if plan.get("courses"):
                                plan["plan_difficulty_balance"] = plan_difficulty_balance(plan["courses"])
                                plan["balance_prediction_source"] = name
                except Exception as error:
                    code = error.code if isinstance(error, PilotInputError) else type(error).__name__
                    result = {"sample_id": student["sample_id"], "student_id": student["student_id"], "status": "BLOCKED",
                              "issues": [{"code": code}], "experiments": {name: {"status": "BLOCKED", "reason": code,
                                     "plans": [], "diagnostic_plans": [], "course_predictions": []} for name in "ABC"}}
                results.append(result)
                with self.lock:
                    self.jobs[run_id]["completed"] = len(results)
            created = datetime.now(timezone.utc).isoformat()
            manifest = {"run_id": run_id, "created_at": created, "status": "completed", "student_count": len(students),
                        "selected_students": [s["sample_id"] for s in students], "target_credits": target_credits,
                        "part_id": 20251, "history_as_of_part": 20243,
                        "training_cutoff": {"A": 20243, **{k: 20243 if experimental.get(k, {}).get("status") == "READY" else None for k in "BC"}},
                        "model_versions": {"A": "original_official_v2_47_features", **{k: experimental.get(k, {}).get("model_version") for k in "BC"}},
                        "data_collection_times": self._collection_times(students),
                        "models": {"A": engine.inspect_assets(), **experimental}, "contracts": self._contracts(history, experimental),
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
                        "incomplete_experiments": {r["sample_id"]: {k: v["status"] for k, v in r["experiments"].items()} for r in results},
                        "replay": {"sample_ids": [s["sample_id"] for s in students], "target_credits": target_credits, "max_plans": max_plans}}
            diagnostics = {"history": history, "features": self._features(experimental), "elapsed_seconds": manifest["elapsed_seconds"],
                           "student_status_counts": {state: sum(r["status"] == state for r in results) for state in {r["status"] for r in results}},
                           "failures": [{"sample_id": r["sample_id"], "issues": r.get("issues", [])} for r in results],
                           "accuracy_claim": "No accuracy improvement asserted; predictions are counterfactual diagnostics.",
                           "university_api_calls": 0, "history_commits": 0, "activations": 0}
            self.store.save(run_id, manifest, results, diagnostics)
            with self.lock:
                self.jobs[run_id]["status"] = "completed"
        except Exception as error:
            with self.lock:
                self.jobs[run_id].update(status="failed", error=type(error).__name__)

    def _collection_times(self, students):
        values = set()
        bases = [self.root / "api_data" / "students" / student["sample_id"] for student in students]
        bases.append(self.root / "api_data" / "frozen_history")
        for base in bases:
            for file in base.glob("*.meta.json"):
                try:
                    value = json.loads(file.read_text(encoding="utf-8-sig")).get("saved_at_utc")
                    if value:
                        values.add(value)
                except (OSError, ValueError):
                    continue
        return sorted(values)
