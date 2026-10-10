"""Beginning-of-semester snapshots from verified SIS fields and partial history."""
from collections.abc import Mapping
import math

import pandas as pd

from src.data.academic_calendar import count_regular_semesters_between, is_regular_semester
from src.features.temporal_features import compute_student_gpa_history, add_student_history_features
from src.recommendation.inputs import BACKEND_SNAPSHOT_COLUMNS

from .validation import ApiError, ValidationResult, binding, check_record_identity, identifier, number, part, response_data, sourced


DIRECT = {"faculty_id": "FACULTY_ID", "grade_version_id": "GRADE_VERSION_ID",
          "start_agpa_points": "START_AGPA_POINTS", "start_total_in_courses": "START_TOTAL_IN_COURSES",
          "start_total_in_credits": "START_TOTAL_IN_CREDITS", "degree_credits_count": "DEGREE_CREDITS_COUNT"}
SOURCED_FIELDS = {"current_gpa_credits", "prior_total_reg_courses", "prior_total_reg_credits",
                 "prior_total_fail_courses", "prior_total_fail_credits", "prior_registered_semesters"}
COUNTS = {"start_total_in_courses", "prior_total_reg_courses", "prior_total_fail_courses", "prior_registered_semesters"}


def adapt_student(request, *, settings, grade_scale=None):
    result = ValidationResult(checks={"identity": "unavailable", "grade_scale": "unavailable"})
    try:
        expected = binding(request, "student")
        data = response_data(request.get("student_api_response"), "student")
        check_record_identity(request["student_api_response"], expected)
        check_record_identity(data, expected)
        info, histories = data.get("studentDegreeInfo"), data.get("studentSummaryInfo")
        if not isinstance(info, Mapping) or not isinstance(histories, list):
            raise ApiError("INVALID_STUDENT_SHAPE", "Student degree information and summary rows are required.")
        check_record_identity(info, expected, required=True)
        result.checks["identity"] = "payload_verified"
        snapshot = {key: None for key in BACKEND_SNAPSHOT_COLUMNS}
        snapshot.update(expected)
        for key, source in DIRECT.items():
            try:
                if source not in info or info[source] is None:
                    raise ApiError("MISSING_FIELD", "Required student source field is missing.", field=key)
                if key in {"faculty_id", "grade_version_id"}:
                    snapshot[key] = identifier(info[source], source)
                else:
                    value = number(info[source], key, integer=key in COUNTS)
                    snapshot[key] = float(value)
                    if not math.isfinite(snapshot[key]):
                        raise ApiError("INVALID_NUMBER", "Numeric value exceeds supported range.", field=key)
                if key == "start_agpa_points" and snapshot[key] > 4:
                    raise ApiError("INVALID_GPA", "Starting GPA must be between zero and four.", field=key)
            except ApiError as error:
                result.add(error)
        for key, aliases in (("diploma_gpa", settings.diploma_gpa_aliases),
                             ("diploma_type_id", settings.diploma_type_aliases)):
            try:
                present = [info[name] for name in aliases if name in info and info[name] is not None]
                if not present:
                    raise ApiError("MISSING_FIELD", "Required diploma information is missing.", field=key)
                values = [identifier(v, key) if key.endswith("id") else number(v, key) for v in present]
                if any(value != values[0] for value in values[1:]):
                    raise ApiError("CONFLICTING_ALIASES", "Configured source aliases conflict.", field=key)
                snapshot[key] = values[0] if key.endswith("id") else float(values[0])
                if key == "diploma_gpa" and not math.isfinite(snapshot[key]):
                    raise ApiError("INVALID_NUMBER", "Diploma value exceeds supported range.", field=key)
            except ApiError as error:
                result.add(error)
        values = (request.get("integration_context") or {}).get("student_values", {})
        if set(values) - SOURCED_FIELDS:
            raise ApiError("UNSUPPORTED_SUPPLEMENT", "Only documented student supplement fields are accepted.")
        for key in SOURCED_FIELDS:
            try:
                if key not in values:
                    if key == "current_gpa_credits":
                        raise ApiError("MISSING_FIELD", "Official GPA-bearing credits with provenance are required.", field=key)
                    result.unavailable_fields.append(key)
                    continue
                value = sourced(values[key], expected["part_id"], key)
                numeric_value = number(value, key, integer=key in COUNTS)
                snapshot[key] = float(numeric_value)
                if not math.isfinite(snapshot[key]):
                    raise ApiError("INVALID_NUMBER", "Supplement value exceeds supported range.", field=key)
                original_key = {"prior_total_fail_courses": "TOTAL_FAIL_COURSES", "prior_total_fail_credits": "TOTAL_FAIL_CREDITS",
                                "current_gpa_credits": "CURRENT_GPA_CREDITS"}.get(key, key.upper())
                if original_key in info and numeric_value != number(info[original_key], original_key, integer=key in COUNTS):
                    raise ApiError("CONFLICTING_STUDENT_SOURCE", "Beginning-of-semester student sources conflict.", field=key)
                raw_total = {"prior_total_reg_courses": "TOTAL_REG_COURSES", "prior_total_reg_credits": "TOTAL_REG_CREDITS"}.get(key)
                if raw_total in info:
                    # Preserve the distinction: a different registration total is diagnostic,
                    # never substituted for the official beginning-of-semester supplement.
                    result.summary["registration_totals_require_timing_contract"] = True
            except ApiError as error:
                result.add(error)
        _history(histories, info, expected, snapshot, result)
        denominator = snapshot["prior_total_reg_credits"]
        failed = snapshot["prior_total_fail_credits"]
        snapshot["prior_fail_credit_ratio"] = None if denominator in (None, 0) or failed is None else failed / denominator
        if grade_scale is not None and snapshot["grade_version_id"] is not None:
            try:
                grade_scale.validate_versions([snapshot["grade_version_id"]])
                result.checks["grade_scale"] = "verified"
            except ValueError:
                result.add(ApiError("UNSUPPORTED_GRADE_VERSION", "Grade version is unsupported.", field="grade_version_id"))
        snapshot["part_semester"] = expected["part_id"] % 10
        snapshot["gpa_trend_delta"] = (None if snapshot["gpa_prev_1"] is None or snapshot["gpa_prev_2"] is None
                                       else snapshot["gpa_prev_1"] - snapshot["gpa_prev_2"])
        snapshot["gpa_trend_missing"] = int(snapshot["gpa_trend_delta"] is None)
        result.normalized = snapshot
        result.summary["field_readiness"] = {key: "unavailable" if value is None else "ready"
                                              for key, value in snapshot.items() if key not in expected}
    except ApiError as error:
        result.add(error)
    return result


def _history(histories, info, expected, snapshot, result):
    records, seen = [], set()
    required = {"STUDENT_STATUS_ID", "STUDENT_ID", "DEGREE_ID", "PART_ID", "GPA_POINTS", "SEMESTER_REG_COURSES"}
    for raw in histories:
        if not isinstance(raw, Mapping):
            raise ApiError("INVALID_HISTORY_ROW", "Semester summaries must be records.")
        check_record_identity(raw, expected, historical=True, required=True)
    for raw in histories:
        if not required.issubset(raw):
            result.unavailable_fields.extend(["gpa_prev_1", "gpa_prev_2", "observed_gap_semesters"])
            result.checks["student_history_schema"] = "unavailable"
            return
        semester = part(raw["PART_ID"])
        status = identifier(raw["STUDENT_STATUS_ID"], "STUDENT_STATUS_ID")
        if semester in seen or any(row["student_status_id"] == status for row in records):
            raise ApiError("DUPLICATE_HISTORY", "Semester summary keys must be unique.")
        seen.add(semester)
        record = {"student_status_id": status, "student_id": expected["student_id"], "degree_id": expected["degree_id"],
                  "part_id": semester, "semester_reg_courses": number(raw["SEMESTER_REG_COURSES"], "SEMESTER_REG_COURSES", integer=True),
                  "gpa_points": float(number(raw["GPA_POINTS"], "GPA_POINTS", nullable=True)) if raw["GPA_POINTS"] is not None else None}
        if record["gpa_points"] is not None and record["gpa_points"] > 4:
            raise ApiError("INVALID_GPA", "Historical GPA must be between zero and four.", field="GPA_POINTS")
        for key in ("last_enrolled_gpa", "total_reg_courses", "total_reg_credits", "total_fail_courses", "total_fail_credits", "reg_total_semesters"):
            if key.upper() in raw:
                val = number(raw[key.upper()], key, nullable=True,
                             integer=key in {"total_reg_courses", "total_fail_courses", "reg_total_semesters"})
                if key == "last_enrolled_gpa" and val is not None and val > 4:
                    raise ApiError("INVALID_GPA", "Previous enrolled GPA must be between zero and four.", field=key)
                record[key] = None if val is None else float(val)
                if record[key] is not None and not math.isfinite(record[key]):
                    raise ApiError("INVALID_NUMBER", "History value exceeds supported range.", field=key)
        records.append(record)
    target_count = number(info.get("SEMESTER_REG_COURSES"), "SEMESTER_REG_COURSES", integer=True, nullable=True)
    target_status = identifier(info.get("STUDENT_STATUS_ID", "api-target-status"), "STUDENT_STATUS_ID")
    if any(row["student_status_id"] == target_status for row in records):
        raise ApiError("DUPLICATE_HISTORY", "Target and historical status keys conflict.")
    target = {"student_status_id": target_status, **expected, "semester_reg_courses": target_count, "gpa_points": None}
    for key, source in (("total_reg_courses", "prior_total_reg_courses"), ("total_reg_credits", "prior_total_reg_credits"),
                        ("total_fail_courses", "prior_total_fail_courses"), ("total_fail_credits", "prior_total_fail_credits")):
        target[key] = snapshot[source]
    full_columns = {"last_enrolled_gpa", "total_reg_courses", "total_reg_credits", "total_fail_courses", "total_fail_credits", "reg_total_semesters"}
    frame = pd.DataFrame([*records, target])
    if records and all(full_columns.issubset(row) for row in records):
        target["last_enrolled_gpa"], target["reg_total_semesters"] = None, None
        frame = pd.DataFrame([*records, target])
        lookup, _ = add_student_history_features(frame[["student_status_id"]], frame[["student_status_id"]].iloc[:0], frame)
        computed = lookup[lookup.student_status_id.eq(target_status)].iloc[0]
        key = "prior_registered_semesters"
        value = None if pd.isna(computed[key]) else float(computed[key])
        if value is not None and snapshot[key] is not None and snapshot[key] != value:
            raise ApiError("CONFLICTING_STUDENT_SOURCE", "Student counter sources conflict.", field=key)
        if snapshot[key] is None and value is not None:
            snapshot[key] = value
            result.unavailable_fields = [field for field in result.unavailable_fields if field != key]
    else:
        lookup = compute_student_gpa_history(frame)
    last = lookup[lookup.student_status_id.eq(target_status)].iloc[0]
    for key in ("gpa_prev_1", "gpa_prev_2"):
        snapshot[key] = None if pd.isna(last[key]) else float(last[key])
        if snapshot[key] is None:
            result.unavailable_fields.append(key)
    registered = [row for row in records if row["semester_reg_courses"] > 0]
    current_registered = None if target_count is None else target_count > 0
    if current_registered is None and info.get("SEMESTER_REG_CREDITS") is not None:
        if number(info["SEMESTER_REG_CREDITS"], "SEMESTER_REG_CREDITS") > 0:
            current_registered = True  # Positive credits prove positive course enrollment.
    if registered and current_registered is not None:
        previous = max(row["part_id"] for row in registered)
        snapshot["observed_gap_semesters"] = count_regular_semesters_between(previous, expected["part_id"]) + (
            is_regular_semester(expected["part_id"]) and not current_registered)
    else:
        result.unavailable_fields.append("observed_gap_semesters")
    result.checks["student_history_schema"] = "verified"
    result.summary["historical_semester_count"] = len(records)
