"""Independent A/B/C inference on the complete actual registration plan.

Only course IDs/credits cross the display boundary. Target marks, grades,
points, finish statuses and the candidate-plan search never enter this path.
"""
from copy import deepcopy
from pathlib import Path
from threading import Lock
from time import perf_counter

from lightgbm.basic import LightGBMError
import pandas as pd

from src import paths
from src.recommendation.inputs import normalize_candidates
from src.recommendation.plan_generation import build_plan_rows
from .adapter import HISTORY_AS_OF_PART, PILOT_ROOT, TARGET_PART, PilotInputError, load_student_inputs, sha256
from .engine import PilotEngine, _digest, build_snapshot


def blocked_forecast(reason="ACTUAL_PLAN_INPUT_UNAVAILABLE", reason_ar="مدخلات خطة الطالب الفعلية غير كافية للتنبؤ الصحيح."):
    return {"status": "BLOCKED", "context": "actual_registered_plan", "reason": reason,
            "experiments": {name: {"prediction_status": "BLOCKED", "reason": reason, "reason_ar": reason_ar,
                                    "course_predictions": []} for name in "ABC"}}


class ObservedPlanPredictor:
    """Lazy read-only models and memoized predictions, separate from saved runs."""

    def __init__(self, root=PILOT_ROOT, *, engine=None, course_history_path=None):
        self.root = Path(root)
        self.engine = engine if engine is not None else PilotEngine(root)
        self.course_history_path = Path(course_history_path or paths.CLEAN_STUDENT_COURSE_PATH_V2)
        self._history = None
        self._source = {}
        self._cache = {}
        self._c_forecasts = {}
        self._lock = Lock()

    def _load_sources(self):
        if self._history is None:
            fingerprint = sha256(self.course_history_path)
            frame = pd.read_parquet(self.course_history_path, columns=["student_id", "course_id", "part_id", "attempt_number"])
            if sha256(self.course_history_path) != fingerprint:
                raise ValueError("Attempt history changed during reading.")
            self._history = frame.loc[pd.to_numeric(frame.part_id).lt(TARGET_PART)].copy()
            self._source["attempt_history_sha256"] = fingerprint
        if self.engine._catalog is None:
            fingerprint = sha256(paths.CLEAN_DEGREE_COURSE_PATH_V2)
            self.engine._catalog = pd.read_parquet(paths.CLEAN_DEGREE_COURSE_PATH_V2)
            if sha256(paths.CLEAN_DEGREE_COURSE_PATH_V2) != fingerprint:
                raise ValueError("Course catalog changed during reading.")
            self._source["catalog_sha256"] = fingerprint
        return self.engine._catalog, self._history

    def _prepare_inputs(self, student, registrations):
        if student.get("part_id") != TARGET_PART or not registrations:
            raise ValueError("Missing actual registration plan.")
        courses = pd.DataFrame([{key: course[key] for key in ("course_id", "course_credits")}
                                for course in registrations])
        if courses.course_id.astype(str).str.strip().duplicated().any():
            raise ValueError("Ambiguous actual registration plan.")
        inputs = load_student_inputs(student, self.root)
        snapshot, issues = build_snapshot(inputs)
        catalog, history = self._load_sources()
        candidates, report = normalize_candidates(courses, catalog, history,
            student["student_id"], student["degree_id"], TARGET_PART)
        if len(candidates) != len(courses) or not pd.to_numeric(candidates.course_credits).gt(0).all():
            raise ValueError("Invalid actual registration plan.")
        shared_hash = _digest({"snapshot": snapshot, "courses": candidates.to_dict("records"),
                               "input_fingerprints": inputs["fingerprints"]})
        return inputs, snapshot, issues, candidates, report, shared_hash

    @staticmethod
    def _raw_plan(candidates, snapshot):
        base = candidates.copy()
        for key, value in snapshot.items():
            base[key] = value
        base["part_semester"] = TARGET_PART % 10
        return build_plan_rows(base, [tuple(range(len(base)))])

    def predict_many(self, cases):
        """Compute C's expensive earlier-peer reference once for all actual plans.

        Every plan has a distinct plan_id while history/context is rebuilt.
        Per-student scoring, model failures and memoization stay independent.
        """
        with self._lock:
            prepared = []
            try:
                assets = self.engine.inspect_experiments()
                if assets.get("C", {}).get("status") == "READY":
                    for student, registrations in cases:
                        try:
                            _, snapshot, _, candidates, _, key = self._prepare_inputs(student, registrations)
                            if key not in self._c_forecasts:
                                rows = self._raw_plan(candidates, snapshot)
                                rows["plan_id"] = len(prepared)
                                prepared.append((key, rows))
                        except (ValueError, OSError, KeyError, TypeError):
                            continue
                    if prepared:
                        scored = self.engine._experimental.predict_course_rows(pd.concat([rows for _, rows in prepared], ignore_index=True), "C")
                        for plan_id, (key, rows) in enumerate(prepared):
                            selected = scored.loc[scored.plan_id.eq(plan_id)].copy()
                            if len(selected) == len(rows) and set(selected.course_id) == set(rows.course_id):
                                selected["plan_id"] = 0
                                self._c_forecasts[key] = selected
            except (LightGBMError, ValueError, OSError, KeyError, TypeError):
                # Fall back to the isolated per-student path rather than hide A/B.
                pass
        return [self.predict(student, registrations) for student, registrations in cases]

    def predict(self, student, registrations):
        """Recompute one full-plan context, independently of eligibility/search."""
        with self._lock:
            try:
                inputs, snapshot, issues, candidates, import_report, shared_hash = self._prepare_inputs(student, registrations)
                assets = {"A": self.engine.inspect_assets(), **self.engine.inspect_experiments()}
                model_keys = {name: {key: assets[name].get(key) for key in
                                    ("status", "reason", "artifact_sha256", "history_artifact_sha256", "manifest_sha256")}
                              for name in "ABC"}
                cache_key = _digest({"inputs": shared_hash, "models": model_keys, "local_sources": self._source})
                if cache_key in self._cache:
                    return deepcopy(self._cache[cache_key])
                plan_hash = _digest([candidates.course_id.tolist()])
                result = blocked_forecast()
                result.update(course_count=len(candidates), total_credits=float(candidates.course_credits.sum()),
                              shared_inputs_sha256=shared_hash, plan_set_sha256=plan_hash,
                              provenance={"target_outcomes_used": False, "history_as_of_part": HISTORY_AS_OF_PART,
                                  "student_source": "unchanged_archived_Student_API_snapshot_and_five_direct_counters",
                                  "course_source": "actual_roster_ids_credits_plus_local_catalog_and_strictly_prior_attempts",
                                  "input_fingerprints": inputs["fingerprints"], **self._source,
                                  "snapshot_issues": issues, "candidate_import": import_report,
                                  "eligibility_or_credit_limit_override": False,
                                  "purpose": "observed_plan_prediction_only_not_registration_recommendation"})
                base = candidates
                selected = [tuple(range(len(base)))]
                raw = self._raw_plan(candidates, snapshot)
                for name in "ABC":
                    started = perf_counter()
                    try:
                        if assets[name]["status"] != "READY":
                            raise PilotInputError(assets[name].get("reason", "MODEL_UNAVAILABLE"))
                        if name == "A":
                            prepared = self.engine._baseline.prepare_candidates(snapshot, candidates, TARGET_PART)
                            scored = self.engine._baseline.score_rows(build_plan_rows(prepared, selected))
                        else:
                            scored = (self._c_forecasts[shared_hash].copy() if name == "C" and shared_hash in self._c_forecasts
                                      else self.engine._experimental.predict_course_rows(raw.copy(), name))
                        if (len(scored) != len(base) or scored.course_id.astype(str).duplicated().any() or
                                set(scored.course_id.astype(str)) != set(base.course_id.astype(str))):
                            raise PilotInputError("ACTUAL_PLAN_SCORE_ALIGNMENT_ERROR")
                        indexed = scored.set_index("course_id").reindex(base.course_id)
                        if not pd.to_numeric(indexed.course_credits).eq(base.course_credits.to_numpy()).all():
                            raise PilotInputError("ACTUAL_PLAN_SCORE_ALIGNMENT_ERROR")
                        experiment = {}
                        PilotEngine._attach_scores(experiment, scored, name)
                        plan = experiment["diagnostic_plans"][0]
                        result["experiments"][name] = {
                            "prediction_status": "PREDICTION_AVAILABLE", "context": "actual_registered_plan",
                            "course_predictions": experiment["course_predictions"],
                            "expected_plan_gpa": plan["expected_plan_gpa"], "expected_failed_credits": plan["expected_failed_credits"],
                            "projected_cumulative_gpa": None, "official_registration_validated": False,
                            "plan_set_sha256": plan_hash, "shared_inputs_sha256": shared_hash,
                            "elapsed_seconds": perf_counter() - started,
                            "assets": {key: assets[name][key] for key in ("feature_count", "model_version", "history_as_of_part",
                                "artifact_sha256", "history_artifact_sha256", "manifest_sha256", "grade_scale_sha256") if key in assets[name]}}
                    except (PilotInputError, LightGBMError, ValueError, OSError, KeyError, TypeError):
                        result["experiments"][name].update(reason="ACTUAL_PLAN_MODEL_INPUT_OR_ARTIFACT_INCOMPATIBLE",
                            reason_ar="تعذر توقع الخطة الفعلية بهذا النموذج بسبب عدم توافق المدخلات أو النموذج.")
                if any(e["prediction_status"] == "PREDICTION_AVAILABLE" for e in result["experiments"].values()):
                    result["status"] = "PREDICTION_AVAILABLE"
                    result.pop("reason", None)
                if all(e["prediction_status"] == "PREDICTION_AVAILABLE" for e in result["experiments"].values()):
                    self._cache[cache_key] = deepcopy(result)
                return result
            except (PilotInputError, LightGBMError, ValueError, OSError, KeyError, TypeError):
                return blocked_forecast()
