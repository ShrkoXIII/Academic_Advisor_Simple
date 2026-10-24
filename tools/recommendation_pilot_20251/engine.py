"""Isolated original-model diagnostics over identical exact-credit plan tuples.

The university policy evidence is insufficient to certify registration or GPA
improvement. Diagnostics deliberately keep those two decisions blocked. They
reuse the original 47-feature scorer, including its supported missing values.
"""
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
from time import perf_counter

import numpy as np
import pandas as pd
from lightgbm.basic import LightGBMError

from src import paths
from src.api.validators.courses import _check_source_duplicates
from src.api.validators.common import ApiError
from src.api.validators.student import DIRECT
from src.data.academic_calendar import count_regular_semesters_between, is_regular_semester
from src.features.feature_contract import BASE_FEATURES
from src.features.temporal_features import compute_student_gpa_history
from src.recommendation.engine import AcademicPlanRecommender
from src.recommendation.inputs import CANDIDATE_COURSE_COLUMNS, STUDENT_SNAPSHOT_COLUMNS
from src.recommendation.plan_generation import build_plan_rows, enumerate_plan_indices

from .adapter import (
    HISTORY_AS_OF_PART, PILOT_ROOT, TARGET_PART, TIMING_LIMITATION,
    PilotInputError, load_student_inputs, numeric, validate_identity,
)
from .selection import normalize_models


POLICY_ISSUES = [
    "GPA_DENOMINATOR_UNAVAILABLE", "REPEAT_POLICY_UNAVAILABLE",
    "REQUIREMENT_GROUP_POLICY_UNCONFIRMED", "PREREQUISITE_POLICY_UNCONFIRMED",
    "LOAD_PROFILE_UNCONFIRMED", "MAX_NEW_COURSES_POLICY_UNCONFIRMED",
    "ATTEMPT_SCOPE_UNCONFIRMED",
]
DEFAULT_MAX_SEARCH_STATES = 200_000


def classify_issue(code):
    """Separate inference requirements from projection and registration evidence."""
    if isinstance(code, dict):
        code = code.get("code", "UNKNOWN_INPUT_ISSUE")
    projection = code in {"GPA_DENOMINATOR_UNAVAILABLE", "REPEAT_POLICY_UNAVAILABLE"}
    optional_value = code in {"FACULTY_ID_UNAVAILABLE", "DEGREE_CREDITS_COUNT_UNAVAILABLE", "STUDENT_GAP_UNAVAILABLE"}
    policy = (code in POLICY_ISSUES and not projection or "POLICY" in code or "UNCONFIRMED" in code
              or code in {"REQUIREMENT_GROUP_CREDITS_UNAVAILABLE", "PREVIOUS_COURSE_STATUS_UNAVAILABLE",
                          "UNAUTHORIZED_ELIGIBILITY_REASON_EXCLUDED", "CREDIT_RULE_VALUE_UNCONFIRMED"})
    no_match = code in {"REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS", "NO_EXACT_CREDIT_SUBSET"}
    messages = {
        "GPA_DENOMINATOR_UNAVAILABLE": "ساعات احتساب المعدل التراكمي غير موثقة؛ توقع الفصل متاح.",
        "REPEAT_POLICY_UNAVAILABLE": "سياسة استبدال علامات الإعادة غير موثقة؛ لا نعتمد إسقاطاً تراكمياً.",
        "FACULTY_ID_UNAVAILABLE": "قيمة الكلية فارغة في الأرشيف؛ يحتفظ النموذج بالقيمة المجهولة.",
        "DEGREE_CREDITS_COUNT_UNAVAILABLE": "إجمالي ساعات البرنامج فارغ في الأرشيف؛ لا يُعاد اشتقاقه.",
        "STUDENT_GAP_UNAVAILABLE": "لا يتوفر دليل تاريخي كافٍ لحساب الفجوة؛ لا تُختلق قيمة صفرية.",
        "MAX_NEW_COURSES_POLICY_UNCONFIRMED": "حد المواد الجديدة موجود في استجابة التسجيل لكن تفسيره غير مثبت.",
        "MAX_NEW_COURSES_INVALID_OR_UNCONFIRMED": "قيمة حد المواد الجديدة غير قابلة للتفسير؛ صلاحية التسجيل مؤقتة.",
        "REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS": "الساعات المطلوبة خارج حدود التسجيل الصريحة لهذا الطالب.",
        "NO_EXACT_CREDIT_SUBSET": "لا توجد مجموعة مواد تطابق الساعات المطلوبة تماماً.",
        "FUTURE_COURSE_SOURCE": "بيانات محاولة مادة تتضمن الفصل المستهدف أو لاحقاً، ولا يمكن اعتمادها للتنبؤ.",
        "UNSUPPORTED_GRADE_VERSION": "إصدار سلم الدرجات غير مدعوم؛ لا يمكن تحويل التوقعات بصورة صحيحة.",
        "SEARCH_BUDGET_EXHAUSTED": "انتهت ميزانية البحث قبل العثور على خطة؛ لا يثبت ذلك غياب خطة مطابقة.",
    }
    return {"code": code, "blocks_prediction": not (projection or optional_value or policy or no_match),
            "blocks_cumulative_gpa": projection, "blocks_official_registration": bool(policy or no_match),
            "origin": "archive_null_or_absent_value" if optional_value else
                      "missing_projection_provenance" if projection else "unconfirmed_registration_policy" if policy else
                      "explicit_registration_limit" if no_match else "invalid_or_incompatible_prediction_input",
            "reason_ar": messages.get(code, "قيد تسجيل يحتاج إلى تحقق رسمي." if policy else "تعذر التنبؤ بسبب مدخل أو أصل غير متوافق.")}


def student_summary(snapshot, student=None):
    """Compact API-sourced summary; the cohort CSV GPA is never substituted."""
    keys = ("start_agpa_points", "start_total_in_credits", "degree_credits_count", "faculty_id",
            "grade_version_id", "prior_registered_semesters")
    result = {key: snapshot.get(key) for key in keys}
    result.update(previous_gpa=snapshot.get("start_agpa_points"), completed_credits=snapshot.get("start_total_in_credits"),
                  gpa_category=(student or {}).get("gpa_category"), source="Student API beginning snapshot")
    return result


class _SearchBudgetExceeded(RuntimeError):
    """The isolated diagnostic traversal used its declared work allowance."""


class _BudgetedSearchStats(dict):
    """Stop through the original generator's existing diagnostic counter hook.

    The generator increments ``visited_search_states`` at each recursive visit.
    Raising before a counter above the budget is stored preserves an exact
    deterministic traversal prefix without modifying the production generator.
    """

    def __init__(self, state_budget):
        super().__init__()
        self.state_budget = state_budget

    def __setitem__(self, key, value):
        if key == "visited_search_states" and value > self.state_budget:
            raise _SearchBudgetExceeded
        super().__setitem__(key, value)


def _number(value, field, *, integer=False):
    value = numeric(value, field, integer=integer)
    if not math.isfinite(float(value)):
        raise PilotInputError("INVALID_NUMBER", field)
    return int(value) if integer else float(value)


def _identifier(value, field):
    if isinstance(value, bool) or value is None or not isinstance(value, (str, int)):
        raise PilotInputError("INVALID_IDENTITY", field)
    value = str(value).strip()
    if not value:
        raise PilotInputError("INVALID_IDENTITY", field)
    return value


def _digest(value):
    raw = json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if value is None or value is pd.NA:
        return None
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def build_snapshot(inputs):
    """Use direct pilot totals, start values and genuinely observed prior lags."""
    identity = inputs["identity"]
    data = inputs["student_api_response"]["data"]
    info = data["studentDegreeInfo"]
    academic = data.get("studentAcademicInfo")
    if not isinstance(academic, dict):
        raise PilotInputError("INVALID_DIPLOMA_SOURCE")
    validate_identity(academic, identity)
    snapshot = {key: None for key in STUDENT_SNAPSHOT_COLUMNS}
    snapshot.update(identity)
    snapshot.update({key: float(value) for key, value in inputs["mapped_features"].items()})
    issues = []
    for key, source in DIRECT.items():
        value = info.get(source)
        if key in {"faculty_id", "degree_credits_count"} and value is None:
            value = academic.get(source)
        if key in {"faculty_id", "degree_credits_count"} and value is None:
            issues.append(source + "_UNAVAILABLE")
            continue
        if key in {"faculty_id", "grade_version_id"}:
            snapshot[key] = _identifier(value, source)
        else:
            snapshot[key] = _number(value, source, integer=key == "start_total_in_courses")
    if snapshot["start_agpa_points"] > 4:
        raise PilotInputError("INVALID_GPA", "START_AGPA_POINTS")
    snapshot["diploma_gpa"] = _number(academic.get("DIPLOMA_GPA"), "DIPLOMA_GPA")
    snapshot["diploma_type_id"] = _identifier(academic.get("DIPLOMA_TYPE_ID"), "DIPLOMA_TYPE_ID")
    total = snapshot["prior_total_reg_credits"]
    snapshot["prior_fail_credit_ratio"] = snapshot["prior_total_fail_credits"] / total if total else None
    summaries = data.get("studentSummaryInfo")
    if summaries is not None and not isinstance(summaries, list):
        raise PilotInputError("INVALID_STUDENT_HISTORY")
    records, seen_parts, seen_statuses = [], set(), set()
    for raw in summaries or []:
        if not isinstance(raw, dict):
            raise PilotInputError("INVALID_STUDENT_HISTORY")
        semester = _number(raw.get("PART_ID"), "PART_ID", integer=True)
        is_regular_semester(semester)
        if semester >= identity["part_id"]:
            raise PilotInputError("FUTURE_STUDENT_HISTORY")
        validate_identity(raw, {**identity, "part_id": semester}, required=True)
        status = _identifier(raw.get("STUDENT_STATUS_ID"), "STUDENT_STATUS_ID")
        if semester in seen_parts or status in seen_statuses:
            raise PilotInputError("DUPLICATE_STUDENT_HISTORY")
        seen_parts.add(semester)
        seen_statuses.add(status)
        gpa = None if raw.get("GPA_POINTS") is None else _number(raw["GPA_POINTS"], "GPA_POINTS")
        if gpa is not None and gpa > 4:
            raise PilotInputError("INVALID_GPA", "GPA_POINTS")
        records.append({"student_status_id": status, **identity, "part_id": semester,
                        "semester_reg_courses": _number(raw.get("SEMESTER_REG_COURSES"),
                                                         "SEMESTER_REG_COURSES", integer=True),
                        "gpa_points": gpa})
    target_status = _identifier(info.get("STUDENT_STATUS_ID"), "STUDENT_STATUS_ID")
    if target_status in seen_statuses:
        raise PilotInputError("DUPLICATE_STUDENT_HISTORY")
    # This is the real target row, with its outcome deliberately excluded.
    target = {"student_status_id": target_status, **identity,
              "semester_reg_courses": 0, "gpa_points": None}
    histories = compute_student_gpa_history(pd.DataFrame([*records, target]))
    current = histories.loc[histories.student_status_id.eq(target_status)].iloc[0]
    for key in ("gpa_prev_1", "gpa_prev_2", "gpa_trend_delta"):
        snapshot[key] = None if pd.isna(current[key]) else float(current[key])
    snapshot["gpa_trend_missing"] = int(current["gpa_trend_missing"])
    registered = [row for row in records if row["semester_reg_courses"] > 0]
    current_enrolled = None
    if info.get("SEMESTER_REG_COURSES") is not None:
        current_enrolled = _number(info["SEMESTER_REG_COURSES"], "SEMESTER_REG_COURSES", integer=True) > 0
    elif info.get("SEMESTER_REG_CREDITS") is not None:
        if _number(info["SEMESTER_REG_CREDITS"], "SEMESTER_REG_CREDITS") > 0:
            current_enrolled = True
    if registered and current_enrolled is not None:
        previous = max(row["part_id"] for row in registered)
        snapshot["observed_gap_semesters"] = count_regular_semesters_between(previous, identity["part_id"]) + int(
            is_regular_semester(identity["part_id"]) and not current_enrolled)
    else:
        issues.append("STUDENT_GAP_UNAVAILABLE")
    return snapshot, issues


def _candidates(inputs, catalog):
    identity = inputs["identity"]
    data = inputs["courses_api_response"]["data"]
    rows, rules = data.get("availableCourses"), data.get("registserRule")
    if not isinstance(rows, list) or not isinstance(rules, dict):
        raise PilotInputError("INVALID_COURSES_SHAPE")
    for raw in rows:
        validate_identity(raw, identity)
    try:
        _check_source_duplicates(rows)
    except ApiError as error:
        raise PilotInputError(error.issue["code"]) from None
    required = {"degree_id", "course_id", "course_type_id", "requirement_type_id",
                "course_credits", "credits_count", "year_order", "semester_order"}
    if not required.issubset(catalog.columns):
        raise PilotInputError("CATALOG_INCOMPATIBLE")
    selected = catalog.loc[catalog.degree_id.astype(str).eq(identity["degree_id"])].copy()
    selected["course_id"] = selected.course_id.astype(str)
    if selected.course_id.duplicated().any():
        raise PilotInputError("CATALOG_INCOMPATIBLE")
    selected = selected.set_index("course_id")
    candidates, seen, issues = [], set(), []
    rejected = {"denied": 0, "unauthorized_reason": 0, "duplicate": 0}
    group_sources = {}
    for raw in rows:
        for flag in ("IS_REQUESTABLE", "ALLOW_REGISTER"):
            if raw.get(flag) not in {"Y", "N"}:
                raise PilotInputError("INVALID_ELIGIBILITY", flag)
        if "N" in (raw["IS_REQUESTABLE"], raw["ALLOW_REGISTER"]):
            rejected["denied"] += 1
            continue
        if raw.get("STATUS_REASON_CODE") != "REQUESTABLE":
            rejected["unauthorized_reason"] += 1
            issues.append("UNAUTHORIZED_ELIGIBILITY_REASON_EXCLUDED")
            continue
        course = _identifier(raw.get("COURSE_ID"), "COURSE_ID")
        if course in seen:
            rejected["duplicate"] += 1
            continue
        seen.add(course)
        if course not in selected.index:
            raise PilotInputError("CATALOG_COURSE_MISSING")
        prior = raw.get("LAST_REGISTER_SEMESTER_ID")
        if prior is not None:
            previous = _number(prior, "LAST_REGISTER_SEMESTER_ID", integer=True)
            is_regular_semester(previous)
            if previous >= identity["part_id"]:
                raise PilotInputError("FUTURE_COURSE_SOURCE")
        attempts = _number(raw.get("ATTEMPTS_COUNT"), "ATTEMPTS_COUNT", integer=True)
        if attempts == 0 and (prior is not None or raw.get("FINISH_STATUS") is not None):
            raise PilotInputError("CONFLICTING_COURSE_STATUS")
        if attempts > 0 and raw.get("FINISH_STATUS") is None:
            issues.append("PREVIOUS_COURSE_STATUS_UNAVAILABLE")
        record = {"course_id": course, "attempt_number": attempts + 1,
                  "course_name": raw.get("COURSE_NAME_SL"),
                  "plan_course_type_id": _identifier(selected.loc[course, "course_type_id"], "course_type_id"),
                  "plan_requirement_type_id": _identifier(raw.get("REQUIREMENT_TYPE_ID"), "REQUIREMENT_TYPE_ID")}
        if not isinstance(record["course_name"], str) or not record["course_name"].strip():
            raise PilotInputError("MISSING_COURSE_NAME")
        for external, internal, catalog_key in [
                ("COURSE_CREDITS", "course_credits", "course_credits"),
                ("CREDITS_COUNT", "plan_credits_count", "credits_count"),
                ("YEAR_ORDER", "plan_year_order", "year_order"),
                ("SEMESTER_ORDER", "plan_semester_order", "semester_order")]:
            value = numeric(raw.get(external), external, integer=external in {"YEAR_ORDER", "SEMESTER_ORDER"})
            if value != numeric(selected.loc[course, catalog_key], catalog_key):
                raise PilotInputError("CATALOG_CONFLICT", external)
            record[internal] = _number(value, external)
        if record["plan_requirement_type_id"] != str(selected.loc[course, "requirement_type_id"]):
            raise PilotInputError("CATALOG_CONFLICT", "REQUIREMENT_TYPE_ID")
        group = _identifier(raw.get("REQUIREMENT_ID"), "REQUIREMENT_ID")
        passed = raw.get("REQUIREMENT_PASSED_CREDITS")
        if passed is None:
            issues.append("REQUIREMENT_GROUP_CREDITS_UNAVAILABLE")
        group_source = (record["plan_requirement_type_id"], numeric(raw.get("CREDITS_COUNT"), "CREDITS_COUNT"),
                        None if passed is None else numeric(passed, "REQUIREMENT_PASSED_CREDITS"))
        if group in group_sources and group_sources[group] != group_source:
            raise PilotInputError("CONFLICTING_REQUIREMENT_GROUP")
        group_sources[group] = group_source
        candidates.append(record)
    columns = [*CANDIDATE_COURSE_COLUMNS, "course_name"]
    return pd.DataFrame(candidates, columns=columns).sort_values("course_id", kind="stable").reset_index(drop=True), rules, issues, rejected


class PilotEngine:
    """Lazy read-only baseline and catalog; writes belong to the pilot runner."""

    def __init__(self, root=PILOT_ROOT, *, max_search_states=DEFAULT_MAX_SEARCH_STATES, snapshot_id="after_backend_fix"):
        if isinstance(max_search_states, bool) or not isinstance(max_search_states, int) or max_search_states < 1:
            raise PilotInputError("INVALID_SEARCH_STATE_BUDGET")
        from .snapshots import validate_snapshot
        self.root = Path(root)
        self.snapshot_id = validate_snapshot(snapshot_id)
        self.max_search_states = max_search_states
        self._baseline = None
        self._catalog = None
        self._experimental = None

    def inspect_experiments(self):
        from .modeling import ExperimentalModels
        if self._experimental is None:
            self._experimental = ExperimentalModels(self.root)
        try:
            return self._experimental.inspect()
        except (LightGBMError, ValueError, OSError, KeyError, TypeError):
            return {name: {"status": "BLOCKED", "reason": "COMPATIBLE_EXPERIMENTAL_MODEL_UNAVAILABLE"} for name in "BC"}

    def _load(self):
        if self._baseline is None:
            self._baseline = AcademicPlanRecommender.load(history_as_of_part=HISTORY_AS_OF_PART)
        if self._catalog is None:
            self._catalog = pd.read_parquet(paths.CLEAN_DEGREE_COURSE_PATH_V2)
        return self._baseline, self._catalog

    def inspect_assets(self):
        """Expose validated contract/cutoffs and hashes, without private paths."""
        try:
            baseline, catalog = self._load()
            if any(model.feature_name() != BASE_FEATURES for model in (baseline.grade_model, baseline.fail_model)):
                raise PilotInputError("ORIGINAL_FEATURE_CONTRACT_MISMATCH")
            training = baseline.provenance.get("training", {})
            if not training or any(row.get("training_as_of_part") != HISTORY_AS_OF_PART for row in training.values()):
                raise PilotInputError("ORIGINAL_TRAINING_CUTOFF_UNVERIFIED")
            if baseline.course_history.as_of_part != HISTORY_AS_OF_PART:
                raise PilotInputError("ORIGINAL_HISTORY_CUTOFF_MISMATCH")
            return {"status": "READY", "model_features": BASE_FEATURES.copy(), "feature_count": len(BASE_FEATURES),
                    "history_as_of_part": HISTORY_AS_OF_PART, "training": training,
                    "artifact_sha256": baseline.provenance.get("artifact_sha256", {}),
                    "history_artifact_sha256": baseline.provenance.get("history", {}).get("artifact_sha256", {}),
                    "catalog_row_count": len(catalog), "usage": "original_47_feature_diagnostics_only"}
        except (LightGBMError, ValueError, OSError, KeyError, TypeError):
            return {"status": "BLOCKED", "reason": "ORIGINAL_ASSETS_UNAVAILABLE_OR_INCOMPATIBLE"}

    @staticmethod
    def _empty(student, target, maximum):
        return {"sample_id": student.get("sample_id"), "student_id": student.get("student_id"),
                "status": "BLOCKED", "target_credits": float(target), "candidate_count": 0,
                "experiments": {name: {"status": "BLOCKED", "prediction_status": "BLOCKED",
                    "plan_status": "UNAVAILABLE", "cumulative_gpa_status": "UNAVAILABLE",
                    "reason": "PREDICTION_NOT_COMPLETED", "reason_ar": "لم تكتمل مدخلات التنبؤ بعد.",
                    "plans": [], "analytical_plans": [], "diagnostic_plans": [], "course_predictions": []} for name in "ABC"},
                "search": {"plan_count": 0, "evaluated_plan_count": 0, "scanned_exact_plan_count": 0,
                    "truncated": False, "max_plans": maximum, "plan_set_sha256": None,
                    "global_optimum_guaranteed": False,
                    "policy": "original_Decimal_exact_first_N_sorted_course_ids"},
                "issues": [], "input_fingerprints": {}, "timing_limitation": TIMING_LIMITATION}

    def evaluate_student(self, student, target_credits=18, max_plans=200, *, models=None, measure_stages=False):
        """Return genuine bounded baseline diagnostics and explicit strict blockers."""
        model_names = normalize_models(models)
        target = numeric(target_credits, "target_credits")
        if target <= 0 or not math.isfinite(float(target)):
            raise PilotInputError("INVALID_TARGET_CREDITS")
        if isinstance(max_plans, bool) or not isinstance(max_plans, int) or not 1 <= max_plans <= 5000:
            raise PilotInputError("INVALID_MAX_PLANS")
        result = self._empty(student, target, max_plans)
        result['experiments'] = {name: result['experiments'][name] for name in model_names}
        result['selected_models'] = list(model_names)
        result['executed_models'] = []
        result["search"].update(state_budget=self.max_search_states, search_budget_exhausted=False,
                                 visited_search_states=0, complete_plan_space_examined=False,
                                 total_plan_count=None)
        started = perf_counter()
        result["latency"] = {"candidate_preparation_seconds": 0., "plan_generation_seconds": 0.}
        try:
            if not re.fullmatch(r"[A-Za-z0-9_-]+", str(student.get("sample_id", ""))):
                raise PilotInputError("INVALID_SAMPLE_ID")
            if student.get("part_id") != TARGET_PART:
                raise PilotInputError("PILOT_SEMESTER_MISMATCH")
            inputs = load_student_inputs(student, root=self.root, snapshot_id=self.snapshot_id)
            result["input_fingerprints"] = inputs["fingerprints"]
            snapshot, snapshot_issues = build_snapshot(inputs)
            result["student_summary"] = student_summary(snapshot, student)
            result["issues"] = [*POLICY_ISSUES, *snapshot_issues]
            if self._catalog is None:
                self._catalog = pd.read_parquet(paths.CLEAN_DEGREE_COURSE_PATH_V2)
            catalog = self._catalog
            assets = self.inspect_assets() if 'A' in model_names else {'status': 'NOT_SELECTED'}
            baseline = self._baseline if assets["status"] == "READY" else None
            candidate_started = perf_counter()
            candidates, rules, course_issues, rejected = self._candidate_pool(student, inputs, catalog)
            result["latency"]["candidate_preparation_seconds"] = perf_counter() - candidate_started
            result.update(candidate_count=len(candidates), candidate_rejections=rejected,
                          feature_readiness={key: "unavailable" if value is None else "ready"
                                             for key, value in snapshot.items() if key not in inputs["identity"]})
            result["issues"] = list(dict.fromkeys([*POLICY_ISSUES, *snapshot_issues, *course_issues]))
            data = inputs["courses_api_response"]["data"]
            optional = data.get("allowRegisterAllOptional")
            if optional not in {"Y", "N"}:
                result["issues"].append("OPTIONAL_POLICY_UNCONFIRMED")
            result["policy_evidence"] = {"optional_overflow_allowed": optional == "Y" if optional in {"Y", "N"} else None,
                "optional_overflow_source": "user_clarification_2026_10_19",
                "max_new_courses_semantics": "UNCONFIRMED",
                "max_new_courses_source": "Courses API.data.registserRule.MAX_NEW_COURSES",
                "max_new_courses_raw_value": rules.get("MAX_NEW_COURSES"),
                "requirement_type_optional_mapping": "UNCONFIRMED"}
            if rules.get("LOAD_TYPE") != "CREDIT":
                result["issues"].append("LOAD_PROFILE_UNCONFIRMED")
            minimum = maximum = None
            try:
                minimum, maximum = numeric(rules.get("MIN_CREDITS"), "MIN_CREDITS"), numeric(rules.get("MAX_CREDITS"), "MAX_CREDITS")
                if minimum > maximum:
                    minimum = maximum = None
                    result["issues"].append("CREDIT_LIMITS_UNCONFIRMED")
            except PilotInputError:
                result["issues"].append("CREDIT_LIMITS_UNCONFIRMED")
            # Study/graduation profile is unknown; these fields remain evidence.
            for key in ("MIN_STUDY_CREDITS", "MAX_STUDY_CREDITS", "GRAD_MIN_LIMIT", "GRAD_MAX_LOAD", "MAX_NEW_COURSES"):
                if rules.get(key) is not None:
                    try:
                        numeric(rules[key], key, integer=key == "MAX_NEW_COURSES")
                    except PilotInputError:
                        result["issues"].append("MAX_NEW_COURSES_INVALID_OR_UNCONFIRMED" if key == "MAX_NEW_COURSES" else "CREDIT_RULE_VALUE_UNCONFIRMED")
            result["registration_rules"] = {key: value for key, value in rules.items()
                                             if isinstance(value, (str, int, float, bool)) or value is None}
            result["search"]["shared_inputs_sha256"] = _digest({
                "snapshot": snapshot, "candidates": candidates.to_dict("records"), "target_credits": target,
                "rules": rules, "input_fingerprints": inputs["fingerprints"]})
            if minimum is not None and maximum is not None and not minimum <= target <= maximum:
                self._no_match(result, "REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS")
                return result
            base = candidates.copy()
            for key, value in snapshot.items():
                base[key] = value
            base["part_semester"] = TARGET_PART % 10
            generation_started = perf_counter()
            stats = _BudgetedSearchStats(self.max_search_states)
            found, budget_exhausted = [], False
            try:
                for plan in enumerate_plan_indices(base, target_credits=target, search_stats=stats):
                    found.append(plan)
                    if len(found) > max_plans:
                        break
            except _SearchBudgetExceeded:
                budget_exhausted = True
                result["issues"].append("SEARCH_BUDGET_EXHAUSTED")
            truncated = budget_exhausted or len(found) > max_plans
            selected = found[:max_plans]
            course_tuples = [[str(base.iloc[index].course_id) for index in plan] for plan in selected]
            result["latency"]["plan_generation_seconds"] = perf_counter() - generation_started
            result["search"].update(plan_count=len(selected), evaluated_plan_count=0,
                scanned_exact_plan_count=len(found), visited_search_states=stats.get("visited_search_states", 0),
                state_budget=self.max_search_states, search_budget_exhausted=budget_exhausted,
                truncated=truncated, plan_set_sha256=_digest(course_tuples),
                total_plan_count=None if truncated else len(selected), complete_plan_space_examined=not truncated)
            if not selected:
                if budget_exhausted:
                    for experiment in result["experiments"].values():
                        experiment.update(status="BLOCKED", reason="SEARCH_BUDGET_EXHAUSTED")
                    return result
                self._no_match(result, "NO_EXACT_CREDIT_SUBSET")
                return result
            context_started = perf_counter()
            raw_rows = build_plan_rows(base, selected)
            result['latency']['shared_plan_context_seconds'] = perf_counter() - context_started
            experimental_assets = self.inspect_experiments() if any(n in model_names for n in 'BC') else {}
            scoring_baseline, scoring_experiments = baseline, self._experimental
            timings = {}
            if measure_stages:
                # Reuse the diagnostic's transparent timing delegates, never its candidate union.
                from .actual_experiment import _TimedBaseline, _TimedExperiments, _timings
                timings = {name: _timings() for name in model_names}
                if baseline is not None:
                    scoring_baseline = _TimedBaseline(baseline, timings['A'])
                if scoring_experiments is not None:
                    scoring_experiments = _TimedExperiments(scoring_experiments, timings)
            for name in model_names:
                experiment_started = perf_counter()
                experiment = result["experiments"][name]
                try:
                    if name == "A":
                        if baseline is None:
                            raise PilotInputError(assets["reason"])
                        try:
                            baseline.grade_scale.validate_versions([snapshot["grade_version_id"]])
                        except ValueError:
                            raise PilotInputError("UNSUPPORTED_GRADE_VERSION") from None
                        prepared = scoring_baseline.prepare_candidates(snapshot, candidates, TARGET_PART)
                        if prepared.course_id.tolist() != base.course_id.tolist():
                            raise PilotInputError("CANDIDATE_ORDER_CONFLICT")
                        result['executed_models'].append(name)
                        scored = scoring_baseline.score_rows(build_plan_rows(prepared, selected))
                        experiment["assets"] = assets
                    else:
                        if experimental_assets[name]["status"] != "READY":
                            raise PilotInputError(experimental_assets[name].get("reason", "COMPATIBLE_EXPERIMENTAL_MODEL_UNAVAILABLE"))
                        result['executed_models'].append(name)
                        scored = scoring_experiments.predict_course_rows(raw_rows.copy(), name)
                        experiment["assets"] = experimental_assets[name]
                    ranking_started = perf_counter()
                    self._attach_scores(experiment, scored, name)
                    experiment['evaluated_plan_count'] = len(selected)
                    if measure_stages:
                        timings[name]['ranking_seconds'] += perf_counter() - ranking_started
                        instrumented = name == 'A' or hasattr(self._experimental, '_load')
                        experiment['latency'] = {**timings[name],
                            'provenance': 'transparent original scorer delegates; ranking includes aggregation and serialization',
                            'additive_with_total': False}
                        if not instrumented:
                            experiment['latency'].update(feature_extraction_seconds=None, prediction_seconds=None,
                                reason='SCORER_STAGE_TIMING_UNAVAILABLE')
                    experiment["elapsed_seconds"] = perf_counter() - experiment_started
                    experiment["plan_set_sha256"] = result["search"]["plan_set_sha256"]
                    experiment["shared_inputs_sha256"] = result["search"]["shared_inputs_sha256"]
                except (PilotInputError, LightGBMError, ValueError, OSError, KeyError, TypeError) as error:
                    code = error.code if isinstance(error, PilotInputError) else "MODEL_INPUT_OR_ARTIFACT_INCOMPATIBLE"
                    experiment.update(reason=code, reason_ar=classify_issue(code)["reason_ar"])
                    result["issues"].append(code)
                finally:
                    experiment['elapsed_seconds'] = perf_counter() - experiment_started
            if any(e["prediction_status"] == "PREDICTION_AVAILABLE" for e in result["experiments"].values()):
                result["status"] = result["prediction_status"] = "PREDICTION_AVAILABLE"
                result["plan_status"] = "PROVISIONAL_PLAN"
                result["search"]["evaluated_plan_count"] = len(selected)
        except PilotInputError as error:
            result["issues"].append(error.code)
            for experiment in result["experiments"].values():
                experiment["reason"] = error.code
        except (ValueError, OSError, KeyError, TypeError, OverflowError):
            result["issues"].append("BASELINE_INPUT_OR_ARTIFACT_INCOMPATIBLE")
            for experiment in result['experiments'].values():
                experiment['reason'] = 'BASELINE_INPUT_OR_ARTIFACT_INCOMPATIBLE'
        finally:
            result["elapsed_seconds"] = perf_counter() - started
            result["latency"]["total_request_seconds"] = result["elapsed_seconds"]
            result["issues"] = list(dict.fromkeys(result["issues"]))
            result["technical_details"] = {"issues": [classify_issue(code) for code in result["issues"]],
                                           "policy_evidence": result.get("policy_evidence", {}),
                                           "feature_readiness": result.get("feature_readiness", {})}
            for experiment in result["experiments"].values():
                if experiment["prediction_status"] == "BLOCKED":
                    experiment["reason_ar"] = classify_issue(experiment["reason"])["reason_ar"]
        return result

    def _candidate_pool(self, student, inputs, catalog):
        """Default archived API pool; isolated experiments may supply a union."""
        return _candidates(inputs, catalog)

    @staticmethod
    def _attach_scores(experiment, scored, name):
        columns = ["plan_id", "course_id", "course_name", "course_credits", "predicted_mark", "expected_points",
                   "expected_grade", "fail_probability", "course_history_fallback_level", "course_history_effective_support"]
        columns.extend(key for key in ("peer_expected_points", "similar_peer_support", "course_difficulty_gap") if key in scored)
        predictions = _json_safe(scored[columns].to_dict("records"))
        for course in predictions:
            if "similar_peer_support" in course:
                support = course["similar_peer_support"]
                course["peer_minimum_support"] = 5
                course["peer_support_status"] = "SUFFICIENT" if support is not None and support >= 5 else "LOW_SUPPORT"
        diagnostics = []
        for plan_id, courses in scored.groupby("plan_id", sort=False):
            credits = courses.course_credits.to_numpy(dtype=float)
            points = courses.expected_points.to_numpy(dtype=float)
            risk = courses.fail_probability.to_numpy(dtype=float)
            total = float(credits.sum())
            weighted_risk = float(np.average(risk, weights=credits))
            diagnostics.append({"plan_id": int(plan_id), "course_count": len(courses), "total_credits": total,
                "expected_plan_gpa": float(np.dot(credits, points) / total), "expected_failed_credits": float(np.dot(credits, risk)),
                "projected_cumulative_gpa": None, "expected_cumulative_gpa_gain": None,
                "is_expected_cumulative_improvement": None, "validity": "UNVERIFIED", "status": "PROVISIONAL_PLAN",
                "official_registration_validated": False,
                "courses": [row for row in predictions if row["plan_id"] == int(plan_id)],
                "plan_difficulty_balance": {"source_experiment": name, "max_fail_probability": float(risk.max()),
                    "credit_weighted_fail_probability": weighted_risk,
                    "credit_weighted_risk_variance": float(np.average((risk - weighted_risk) ** 2, weights=credits)),
                    "high_risk_course_count": int((risk >= .5).sum()), "high_risk_threshold": .5,
                    "usage": "descriptive_only_unvalidated_threshold"}})
        ordered = sorted(diagnostics, key=lambda p: (-p["expected_plan_gpa"], p["expected_failed_credits"],
                                                    p["plan_difficulty_balance"]["max_fail_probability"], p["plan_id"]))
        experiment.update(status="PREDICTION_AVAILABLE", prediction_status="PREDICTION_AVAILABLE", plan_status="PROVISIONAL_PLAN",
            cumulative_gpa_status="UNAVAILABLE", reason="ANALYTICAL_PREDICTIONS_OFFICIAL_VALIDITY_UNCONFIRMED",
            reason_ar="التوقعات متاحة للتحليل؛ صلاحية التسجيل وإسقاط المعدل التراكمي غير معتمدين.",
            analytical_plans=ordered[:3], diagnostic_plans=diagnostics, course_predictions=predictions,
            analytical_ranking="semester_gpa_desc_failed_credits_asc_max_risk_asc_plan_id",
            diagnostic_ranking="original_enumeration_order_no_academic_recommendation")

    @staticmethod
    def _no_match(result, reason):
        result["status"] = "NO_MATCHING_PLAN"
        result["issues"].append(reason)
        for experiment in result["experiments"].values():
            experiment.update(status="NO_MATCHING_PLAN", prediction_status="NO_MATCHING_PLAN", reason=reason,
                              reason_ar=classify_issue(reason)["reason_ar"])
