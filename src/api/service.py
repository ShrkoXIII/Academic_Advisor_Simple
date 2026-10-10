"""Independent validation dependencies and lazy, manifest-gated inference."""
from collections import defaultdict
from decimal import Decimal
from threading import Lock

from src import paths
from src.features.frozen_history import validate_history_selection
from src.grade_scale import GradeScale
from src.recommendation.history_update import FrozenHistoryManager
from src.recommendation.plan_generation import sum_credit_values
from src.recommendation.ranking_policy import validate_ranking_policy
from src.recommendation.two_stage_artifacts import load_two_stage_artifacts
from src.recommendation.two_stage_engine import TwoStagePlanRecommender

from .courses_adapter import adapt_courses
from .history_adapter import adapt_history_delta
from .settings import ApiSettings
from .student_adapter import adapt_student
from .validation import ApiError, number, part


PUBLIC_METADATA = {"dataset_version", "feature_engineering_version", "input_fingerprint_version", "input_sha256",
                   "manifest_version", "grade_scale_sha256", "grade_scale_version", "grade_model_target",
                   "expected_points_method", "balance_policy_version", "received_candidate_count", "candidate_count",
                   "stage1_row_count", "feasible_plan_count", "shortlist_count", "shortlist_limit", "shortlist_plan_ids",
                   "scored_plan_count", "stage2_row_count", "returned_plan_count", "top_k", "global_top_k_guaranteed",
                   "credit_policy", "target_credits", "allowed_failed_repeat_credits", "allowed_withdrawn_repeat_credits",
                   "projected_gpa_method", "production_ranking_strategy", "usage", "max_new_courses"}


class ApiService:
    def __init__(self, *, settings=None, catalog=None, grade_scale=None, history_manager=None, engine=None):
        self.settings = settings or ApiSettings()
        self.catalog, self.grade_scale = catalog, grade_scale
        self.history_manager = history_manager or (engine.history_manager if engine is not None else None)
        self.engine = engine
        self.artifacts = engine.artifacts if engine is not None else None
        self._inference_lock = Lock()

    def initialize(self, *, catalog_loader=None, grade_scale_loader=None, history_loader=None, model_loader=None):
        """Load each dependency independently; ordinary load errors leave HTTP usable."""
        import pandas as pd
        loaders = {"catalog": catalog_loader or (lambda: pd.read_parquet(paths.CLEAN_DEGREE_COURSE_PATH_V2)),
                   "grade_scale": grade_scale_loader or (lambda: GradeScale.from_parquet(paths.GRADE_SCALE_PATH)),
                   "history_manager": history_loader or FrozenHistoryManager.load,
                   "artifacts": model_loader or load_two_stage_artifacts}
        for name, loader in loaders.items():
            if getattr(self, name) is None:
                try:
                    value = loader()
                    if name == "artifacts":
                        policy = validate_ranking_policy(value.manifest, require_approved=True)
                        if any(policy[key] != {"name": "pareto", "version": "v1"} for key in
                               ("stage1_shortlist_strategy", "final_ranking_strategy")):
                            raise ValueError("API requires the approved pareto v1 policy at both stages.")
                    setattr(self, name, value)
                except Exception:
                    # Never expose loader errors, private artifact paths or input data.
                    setattr(self, name, None)
        if self.engine is None and self.artifacts is not None and self.history_manager is not None:
            try:
                self.engine = TwoStagePlanRecommender.from_loaded_artifacts(self.artifacts, self.history_manager)
            except Exception:
                self.engine = None

    def health(self):
        return {"api_health": "healthy", "model_readiness": {"ready": self.artifacts is not None},
                "history_readiness": {"ready": self.history_manager is not None},
                "catalog_readiness": {"ready": self.catalog is not None},
                "grade_scale_readiness": {"ready": self.grade_scale is not None},
                "recommendation_readiness": {"ready": all(value is not None for value in
                    (self.engine, self.history_manager, self.catalog, self.grade_scale))},
                "production_operational_limits": "UNRESOLVED"}

    def validate_student(self, request):
        return adapt_student(request, settings=self.settings, grade_scale=self.grade_scale)

    def validate_courses(self, request):
        return adapt_courses(request, catalog=self.catalog)

    def validate_delta(self, request):
        return adapt_history_delta(request, manager=self.history_manager)

    def recommend(self, request):
        student, courses = self.validate_student(request), self.validate_courses(request)
        errors = [*student.errors, *courses.errors]
        if errors:
            status = max(student.http_status, courses.http_status)
            raise ApiError("INVALID_INPUTS", "Recommendation inputs need correction.", status_code=status,
                           details={"student": student.public(), "courses": courses.public()})
        cutoff, target = part(request.get("history_as_of_part"), "history_as_of_part"), part(request.get("part_id"))
        mode = request.get("mode", "normal")
        if mode not in {"normal", "backtesting"} or (mode == "backtesting" and not self.settings.enable_backtesting):
            raise ApiError("BACKTESTING_DISABLED", "Backtesting requires explicit mode and service authorization.")
        try:
            validate_history_selection(target, cutoff, allow_older_history=mode == "backtesting")
        except ValueError:
            raise ApiError("INVALID_HISTORY_CUTOFF", "History cutoff does not satisfy the requested temporal policy.") from None
        candidates = courses.normalized["candidates"]
        if (self.settings.performance_test_mode and
                len(candidates) > self.settings.performance_test_max_candidates):
            raise ApiError("PERFORMANCE_TEST_LIMIT", "Entire request exceeds the configured performance test limit.")
        if not self.health()["recommendation_readiness"]["ready"]:
            raise ApiError("DEPENDENCY_UNAVAILABLE", "Recommendation dependencies are unavailable.", status_code=503)
        # Unknown histories are retained only where the existing snapshot contract
        # permits null; no totals or GPA lags are invented here.
        if "observed_gap_semesters" in student.unavailable_fields or student.checks.get("student_history_schema") != "verified":
            raise ApiError("INSUFFICIENT_STUDENT_HISTORY", "Student history cannot support required temporal features.")
        for stage in self.artifacts.manifest["stages"].values():
            if target <= part(stage["training_as_of_part"]):
                raise ApiError("TRAINING_CUTOFF_OVERLAP", "Target must follow every model training cutoff.")
        try:
            self.history_manager.capture(target_part=target, history_as_of_part=cutoff, allow_older_history=mode == "backtesting")
        except (ValueError, OSError):
            raise ApiError("HISTORY_UNAVAILABLE", "The exact requested history snapshot is unavailable or incompatible.", status_code=503) from None
        rules = courses.normalized["registration_rules"]
        exact = request.get("target_credits")
        if exact is not None:
            lower = upper = number(exact, "target_credits")
        else:
            lower, upper = number(request.get("min_credits"), "min_credits"), number(request.get("max_credits"), "max_credits")
        if lower > upper:
            raise ApiError("INVALID_CREDIT_BOUNDS", "Requested credit minimum exceeds maximum.")
        lower, upper = max(lower, rules["effective_min"]), min(upper, rules["effective_max"])
        if lower > upper:
            raise ApiError("CREDIT_RANGE_CONFLICT", "Requested and confirmed credit ranges do not intersect.")
        categories, groups = defaultdict(list), defaultdict(list)
        for row in candidates:
            categories[row["plan_requirement_type_id"]].append(row["course_credits"])
            groups[row["requirement_group_id"]].append(row["course_credits"])
        policies = courses.normalized["requirement_group_policies"]
        policy = courses.normalized["registration_policy"]
        engine_request = {"student_id": request["student_id"], "degree_id": request["degree_id"], "part_id": target,
                          "target_credits": upper,
                          "allowed_failed_repeat_credits": number(policy.get("allowed_failed_repeat_credits"), "allowed_failed_repeat_credits"),
                          "allowed_withdrawn_repeat_credits": number(policy.get("allowed_withdrawn_repeat_credits"),
                              "allowed_withdrawn_repeat_credits", nullable=True),
                          "requirement_policies": [{"plan_requirement_type_id": key, "max_credits": sum_credit_values(values)}
                                                   for key, values in categories.items()],
                          "requirement_group_policies": {key: sum_credit_values(groups[key]) if value is None else value
                                                         for key, value in policies.items()},
                          "max_new_courses": rules["MAX_NEW_COURSES"]}
        if engine_request["allowed_withdrawn_repeat_credits"] is None:
            engine_request.pop("allowed_withdrawn_repeat_credits")
        if not self._inference_lock.acquire(blocking=False):
            raise ApiError("INFERENCE_BUSY", "Recommendation worker is busy.", status_code=503)
        try:
            output = self.engine.recommend_from_payloads(student_payload={"snapshot": student.normalized, "candidates": candidates},
                        request_payload=engine_request, top_k=request.get("top_k", 3), history_as_of_part=cutoff,
                        allow_older_history=mode == "backtesting")
        except ValueError:
            raise ApiError("INCOMPATIBLE_INPUTS", "Prepared inputs do not satisfy the inference contract.") from None
        finally:
            self._inference_lock.release()
        metadata = {key: value for key, value in output["metadata"].items() if key in PUBLIC_METADATA}
        metadata.update(mode=mode, history_as_of_part=cutoff, part_id=target,
                        input_validation={"student": student.status, "courses": courses.status},
                        unavailable_student_fields=sorted(set(student.unavailable_fields)),
                        identity_verification={"student": student.checks["identity"], "courses": courses.checks["identity"]},
                        performance_test_mode=self.settings.performance_test_mode)
        return {"status": output["status"], "metadata": metadata, "recommendations": output["recommendations"]}
