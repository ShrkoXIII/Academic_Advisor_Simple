"""Downstream, read-only XML inputs and outcomes for paired historical experiments.

Outcomes are returned separately and never passed to the model feature adapter.
Only existing V2 inputs and immutable histories are consumed.
"""
from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np
import pandas as pd

from src import paths
from src.data.cleaning_utils import clean_column_names, clean_id, clean_id_columns
from src.data.clean_student_course import REGISTER_STATUSES, FINISH_STATUS_MAP
from src.evaluation.evaluate_xml_recommendations import xml_rows
from src.features.frozen_history import previous_academic_part
from src.recommendation.engine import resolve_current_gpa_credits
from src.recommendation.inputs import (
    CandidateImportError, build_student_snapshot, normalize_candidates, validate_snapshot,
    _explicitly_ineligible,
)


def sorted_xml_files(directory):
    return sorted(Path(directory).glob("*.xml"), key=lambda p: [
        int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", p.name)
    ])


def explicit_target(filename, targets):
    if filename not in targets:
        raise ValueError(f"Missing explicit target for {filename}")
    return paths.academic_part(targets[filename])


def normalize_raw_rows(frame):
    frame = clean_column_names(frame).copy()
    ids = [c for c in ("student_course_id", "student_status_id", "student_id", "degree_id", "course_id") if c in frame]
    frame = clean_id_columns(frame, ids)
    for col in ("part_id", "course_credits", "points"):
        if col in frame:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    for col in ("register_status", "finish_status", "in_gpa", "in_agpa", "in_credits"):
        if col in frame:
            frame[col] = frame[col].astype("string").str.strip().str.upper()
    return frame


def _finite(value):
    return value is not None and not pd.isna(value) and np.isfinite(float(value))


def calculate_observed_metrics(raw, cleaned, status):
    """Use existing GPA-bearing cleaning policy; retain exclusions and conflicts.

    An incomplete outcome denominator does not yield a partial-GPA accuracy claim.
    Published status GPAs remain independent of the course-row calculation.
    """
    raw = raw[raw.register_status.isin(REGISTER_STATUSES)].copy()
    if raw.student_course_id.duplicated().any() or raw.course_id.duplicated().any():
        raise ValueError("Duplicate actual student-course registration")
    if len(raw) and raw[["student_id", "degree_id", "part_id"]].drop_duplicates().shape[0] != 1:
        raise ValueError("Observed rows mix student, degree or target semester")
    if cleaned.student_course_id.duplicated().any():
        raise ValueError("Duplicate cleaned student-course registration")
    clean_lookup = cleaned.set_index("student_course_id")
    courses, conflicts, missing_points, unknown_policy = [], [], [], []
    raw_ids = set(raw.student_course_id)
    for _, row in cleaned.loc[~cleaned.student_course_id.isin(raw_ids)].iterrows():
        conflicts.append({"course_id": row.course_id, "field": "unexplained_cleaned_membership",
                          "student_course_id": row.student_course_id})
    total_quality = total_gpa_credits = 0.0
    for _, row in raw.sort_values("course_id", kind="stable").iterrows():
        flags = {c: row.get(c) for c in ("in_gpa", "in_agpa", "in_credits")}
        excluded_flag = any(v == "N" for v in flags.values() if pd.notna(v))
        allowed_outcome = row.finish_status in FINISH_STATUS_MAP
        unknown = not allowed_outcome and row.finish_status not in {"W", "D", "Z"}
        unknown |= any(pd.isna(v) or v not in {"Y", "N"} for v in flags.values())
        if unknown:
            unknown_policy.append(str(row.course_id))
        included = bool(allowed_outcome and not excluded_flag)
        points = float(row.points) if _finite(row.points) else None
        credit = float(row.course_credits) if _finite(row.course_credits) else None
        if credit is None or credit < 0:
            raise ValueError("Actual credits must be finite and nonnegative")
        clean_row = clean_lookup.loc[row.student_course_id] if row.student_course_id in clean_lookup.index else None
        if included and clean_row is None:
            conflicts.append({"course_id": row.course_id, "field": "missing_cleaned_membership",
                              "student_course_id": row.student_course_id})
        if not included and clean_row is not None:
            conflicts.append({"course_id": row.course_id, "field": "excluded_raw_membership_in_cleaned",
                              "student_course_id": row.student_course_id})
        if clean_row is not None:
            for field in ("points", "course_credits", "course_id", "degree_id", "part_id"):
                lhs, rhs = row.get(field), clean_row.get(field)
                if pd.isna(lhs) and pd.isna(rhs):
                    continue
                if pd.isna(lhs) or pd.isna(rhs) or lhs != rhs:
                    conflicts.append({"course_id": row.course_id, "field": field, "raw": lhs, "cleaned": rhs})
            if included and _finite(clean_row.points):
                points = float(clean_row.points)
        if included and credit > 0:
            if points is None or not 0 <= points <= 4:
                missing_points.append(str(row.course_id))
            else:
                total_quality += points * credit
            total_gpa_credits += credit
        courses.append({
            "course_id": str(row.course_id), "student_course_id": str(row.student_course_id),
            "course_name": row.get("course_name_sl"), "course_credits": credit,
            "actual_points": points, "actual_mark": row.get("final_mark"),
            "finish_status": row.finish_status, "register_status": row.register_status,
            **flags, "gpa_included": included, "present_in_cleaned": clean_row is not None,
            "predicted_points": None, "points_error": None,
        })
    state = ("raw_clean_conflict" if conflicts else "missing_gpa_bearing_points" if missing_points
             else "unverified_gpa_policy" if unknown_policy else "no_gpa_bearing_credits" if total_gpa_credits <= 0
             else "ok")
    actual_gpa = total_quality / total_gpa_credits if state == "ok" else None
    published = status.get("gpa_points")
    warnings = []
    raw_credits = float(raw.course_credits.sum())
    clean_credits = float(cleaned.course_credits.sum())
    if len(raw) != len(cleaned) or raw_credits != clean_credits:
        warnings.append("Raw and cleaned registration counts/credits differ; per-course exclusions are retained.")
    if raw_credits != float(status["semester_reg_credits"]):
        warnings.append("Raw course credits differ from published semester_reg_credits.")
    if actual_gpa is not None and _finite(published) and abs(actual_gpa - float(published)) > 1e-10:
        warnings.append("Calculated course GPA differs from published gpa_points; university rounding/repeat rules are not assumed.")
    return {
        "actual_gpa_status": state, "actual_plan_gpa": actual_gpa,
        "actual_source_semester_gpa": published,
        "calculated_minus_published_semester_gpa": actual_gpa - float(published) if actual_gpa is not None and _finite(published) else None,
        "actual_published_end_cumulative_gpa": status.get("end_agpa_points"),
        "actual_total_credits": raw_credits, "gpa_bearing_credits": total_gpa_credits,
        "actual_raw_course_count": len(raw), "actual_cleaned_course_count": len(cleaned),
        "actual_cleaned_credits": clean_credits, "actual_source_semester_credits": status.get("semester_reg_credits"),
        "actual_source_semester_courses": status.get("semester_reg_courses"),
        "raw_clean_conflicts": conflicts, "missing_points_course_ids": missing_points,
        "unverified_policy_course_ids": unknown_policy, "courses": courses, "warnings": warnings,
        "gpa_policy": "register R/E; outcomes F/FE/FA/P; exclude any in_gpa/in_agpa/in_credits=N; no invented points",
    }


INPUT_PATHS = {
    "status": paths.CLEAN_STUDENT_STATUS_PATH_V2,
    "history": paths.CLEAN_STUDENT_COURSE_PATH_V2,
    "diplomas": paths.CLEAN_STUDENT_DIPLOMA_PATH_V2,
    "catalog": paths.CLEAN_DEGREE_COURSE_PATH_V2,
    "raw_courses": paths.STUDENT_COURSE_PATH,
    "raw_status": paths.STUDENT_STATUS_PATH,
}


def load_tables():
    return {name: normalize_raw_rows(pd.read_parquet(path)) if name.startswith("raw_")
            else pd.read_parquet(path) for name, path in INPUT_PATHS.items()}


@dataclass
class StudentCase:
    payload: dict
    candidates: pd.DataFrame
    snapshot: dict
    actual_raw: pd.DataFrame


def load_case(path, target_part, tables):
    raw, repaired = xml_rows(path)
    diagnostic = clean_column_names(raw)
    ids = clean_id(diagnostic.student_id)
    if ids.dropna().empty:
        raise ValueError("No student identity in XML")
    student_id = ids.dropna().iloc[0]
    foreign_rows = int((~ids.eq(student_id).fillna(False)).sum())
    primary = diagnostic.loc[ids.eq(student_id)].copy()
    status = tables["status"]
    target_status = status[status.student_id.eq(student_id) & status.part_id.eq(target_part)]
    if len(target_status) != 1:
        raise ValueError(f"No unique status for student {student_id} target {target_part}")
    status_row = target_status.iloc[0]
    degree_id = str(status_row.degree_id)
    source_columns = [c for c in ("student_id", "degree_id", "course_id", "course_credits", "course_name_sl",
                                  "is_requestable", "allow_register", "course_type_id", "requirement_type_id",
                                  "year_order", "semester_order") if c in primary]
    source = primary[source_columns].copy()  # XML part is diagnostic only.
    eligibility_excluded = source.apply(lambda r: _explicitly_ineligible(r.to_dict()), axis=1)
    source = source.loc[~eligibility_excluded].copy()
    candidates, report = normalize_candidates(source, tables["catalog"], tables["history"],
                                               student_id, degree_id, target_part)
    snapshot = validate_snapshot(build_student_snapshot(
        status, tables["history"], tables["diplomas"], student_id, degree_id, target_part,
    ), student_id, degree_id, target_part)
    credits, credits_source = resolve_current_gpa_credits(snapshot)
    raw_status = tables["raw_status"]
    raw_status = raw_status[raw_status.student_id.eq(student_id) & raw_status.degree_id.eq(degree_id)
                            & raw_status.part_id.eq(target_part)]
    if len(raw_status) != 1:
        raise ValueError("No unique raw status under student+degree+target key")
    denominator = pd.to_numeric(raw_status.iloc[0]["total_reg_credits"], errors="coerce")
    if not _finite(denominator) or float(denominator) != credits:
        raise ValueError("GPA denominator raw total_reg_credits differs from resolved prior_total_reg_credits")
    raw_start = pd.to_numeric(raw_status.iloc[0]["start_agpa_points"], errors="coerce")
    if not _finite(raw_start) or float(raw_start) != float(snapshot["start_agpa_points"]):
        raise ValueError("Raw and cleaned start_agpa_points differ")
    raw_actual = tables["raw_courses"]
    raw_actual = raw_actual[raw_actual.student_id.eq(student_id) & raw_actual.degree_id.eq(degree_id)
                             & raw_actual.part_id.eq(target_part) & raw_actual.register_status.isin(REGISTER_STATUSES)].copy()
    clean_actual = tables["history"]
    clean_actual = clean_actual[clean_actual.student_id.eq(student_id) & clean_actual.degree_id.eq(degree_id)
                                 & clean_actual.part_id.eq(target_part)].copy()
    observed = calculate_observed_metrics(raw_actual, clean_actual, raw_status.iloc[0].to_dict())
    if raw_actual.empty:
        raise ValueError("No actual target-semester registrations")
    warning = [
        "GPA projection follows resolve_current_gpa_credits using prior registered total_reg_credits; an authoritative university GPA-denominator definition is not supplied.",
        "Prerequisites, offering timetable, requirement caps, official failed/withdrawn-repeat caps and historical XML eligibility are unverified where absent from this export.",
        "Additive cumulative projection does not implement official repeat-grade replacement.",
    ]
    if foreign_rows:
        warning.append(f"XML contains {foreign_rows} foreign-student rows; existing first-row identity policy excludes them explicitly.")
    raw_prior = tables["raw_courses"]
    raw_prior = raw_prior[raw_prior.student_id.eq(student_id) & raw_prior.part_id.lt(target_part)
                          & raw_prior.register_status.isin(REGISTER_STATUSES)]
    eligibility = primary[[c for c in ("course_id", "is_requestable", "allow_register") if c in primary]].copy()
    eligibility["course_id"] = clean_id(eligibility.course_id)
    flags = eligibility.drop_duplicates("course_id").set_index("course_id").to_dict("index")
    candidate_records = [{**record, **flags.get(record["course_id"], {}),
                          "raw_prior_attempt": record["course_id"] in set(raw_prior.course_id)}
                         for record in candidates.to_dict("records")]
    payload = {
        "case_id": f"{path.stem.replace(' ', '_')}_{student_id.replace('.', '_')}_{target_part}",
        "xml_file": path.name, "student_id": student_id, "degree_id": degree_id,
        "degree_name": status_row.get("degree_name_sl"), "target_part": target_part,
        "history_as_of_part": previous_academic_part(target_part), "candidate_count": len(candidates),
        "snapshot": snapshot, "candidates": candidate_records, "observed": observed, "warnings": warning,
        "current_gpa_credits": credits, "current_gpa_credits_source": credits_source,
        "input_audit": {"xml_repaired_in_memory": repaired, "xml_raw_rows": len(raw),
                        "mixed_student_xml_rows_excluded": foreign_rows,
                        "xml_part_values": sorted(str(x) for x in diagnostic.get("part_id", pd.Series(dtype="object")).dropna().unique()),
                        "eligibility_excluded_rows": int(eligibility_excluded.sum()), "candidate_import": report,
                        "gpa_denominator_raw_field": "V_ADD_STUDENT_DEGREE_STATUS.total_reg_credits",
                        "gpa_denominator_raw_clean_equal": True,
                        "actual_raw_vs_clean_course_count_difference": len(raw_actual) - len(clean_actual),
                        "actual_raw_vs_clean_credit_difference": float(raw_actual.course_credits.sum() - clean_actual.course_credits.sum())},
    }
    return StudentCase(payload, candidates, snapshot, raw_actual)
