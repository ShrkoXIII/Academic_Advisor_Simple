"""Read-only, diagnostic union of API candidates and missing actual courses.

Actual choices are post-decision information. This module proves neither
historical requestability nor historical catalog validity. Registrations cross
the boundary through an explicit ID/credits allowlist; target outcomes never do.
"""
from collections.abc import Mapping
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from math import isfinite
from pathlib import Path

import pandas as pd

from src import paths
from .adapter import HISTORY_AS_OF_PART, TARGET_PART, sha256


DIAGNOSTIC_MODE = "DIAGNOSTIC_ACTUAL_COURSE_INJECTION"
HISTORY_COLUMNS = ["student_id", "course_id", "part_id", "attempt_number"]
CATALOG_FIELDS = {
    "plan_course_type_id": "course_type_id", "plan_requirement_type_id": "requirement_type_id",
    "plan_year_order": "year_order", "plan_semester_order": "semester_order",
    "plan_credits_count": "credits_count",
}


def normalize_course_id(value):
    """Compare finite numeric IDs with Decimal, preserving opaque identifiers."""
    if value is None or isinstance(value, bool) or pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = Decimal(text)
    except InvalidOperation:
        return text
    if not number.is_finite():
        return None
    return format(number.normalize(), "f") if number else "0"


def _number(value, *, positive=False, integer=False):
    if value is None or isinstance(value, bool) or pd.isna(value):
        raise ValueError("Missing numeric value.")
    try:
        number = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError("Invalid numeric value.") from error
    if not number.is_finite() or not isfinite(float(number)) or number < 0 or (positive and number == 0):
        raise ValueError("Invalid numeric range.")
    if integer and number != number.to_integral_value():
        raise ValueError("Expected integer.")
    return number


def _history_for_student(prior_history, student_id):
    if not isinstance(prior_history, pd.DataFrame) or not set(HISTORY_COLUMNS).issubset(prior_history):
        return None
    normalized = prior_history.attrs.get("actual_candidate_identifiers_normalized", False)
    student_ids = prior_history.student_id if normalized else prior_history.student_id.map(normalize_course_id)
    result = prior_history.loc[student_ids.eq(student_id), HISTORY_COLUMNS].copy()
    if not normalized:
        result["course_id"] = result.course_id.map(normalize_course_id)
    if result.course_id.isna().any():
        return None
    result["part_id"] = pd.to_numeric(result.part_id, errors="coerce")
    return result


def _attempt(prior, course_id):
    if prior is None:
        raise ValueError("ATTEMPT_HISTORY_INVALID")
    matching = prior.loc[prior.course_id.eq(course_id)]
    # Missing chronology cannot prove that a row precedes the target.
    if matching.part_id.isna().any():
        raise ValueError("ATTEMPT_HISTORY_INVALID")
    matching = matching.loc[matching.part_id.lt(TARGET_PART)]
    try:
        values = [_number(value, positive=True, integer=True) for value in matching.attempt_number]
    except ValueError:
        raise ValueError("ATTEMPT_HISTORY_INVALID") from None
    return int(max(values, default=Decimal(0))) + 1


def augment_candidates(original, student, registrations, catalog, prior_history, *,
                       catalog_source=None, history_source=None, original_api_course_ids=None):
    """Return a separate model frame and outcome-free provenance sidecar.

    Existing model candidates retain their exact values and order. When raw API
    IDs are provided, actual courses present there but rejected by existing
    eligibility rules remain rejected. Only genuinely absent IDs are injected.
    """
    if not isinstance(original, pd.DataFrame) or "course_id" not in original:
        raise ValueError("Original candidates require course_id.")
    if _number(student.get("part_id"), integer=True) != TARGET_PART:
        raise ValueError("Diagnostic injection requires the explicit 20251 target.")
    student_id, degree_id = [normalize_course_id(student.get(key)) for key in ("student_id", "degree_id")]
    if student_id is None or degree_id is None:
        raise ValueError("Student and degree identity are required.")
    if not isinstance(registrations, list) or any(not isinstance(row, Mapping) for row in registrations):
        raise ValueError("Actual registrations must be a list of mappings.")
    original_ids = set(original.course_id.map(normalize_course_id).dropna())
    raw_ids = (original_ids if original_api_course_ids is None else
               {course for value in original_api_course_ids if (course := normalize_course_id(value)) is not None})
    actual, rejected, invalid = {}, [], set()
    # Deliberately ignore names, marks, statuses and target attempt counters.
    for registration in registrations:
        course = normalize_course_id(registration.get("course_id"))
        if course is None:
            rejected.append({"course_id": None, "reason": "ACTUAL_REGISTRATION_ID_INVALID"})
            continue
        try:
            credits = _number(registration.get("course_credits"), positive=True)
        except ValueError:
            invalid.add(course)
            actual.setdefault(course, None)
            continue
        if course in actual and actual[course] != credits:
            invalid.add(course)
        actual[course] = credits
    missing = sorted(set(actual) - raw_ids)
    prior = _history_for_student(prior_history, student_id)
    catalog_required = {"degree_id", "course_id", "course_credits", *CATALOG_FIELDS.values()}
    selected = None
    if isinstance(catalog, pd.DataFrame) and catalog_required.issubset(catalog):
        selected = catalog.loc[catalog.degree_id.map(normalize_course_id).eq(degree_id)].copy()
        selected["course_id"] = selected.course_id.map(normalize_course_id)
    provenance = {course: {"candidate_source": "API", "historical_eligibility_unverified": True,
        "official_requestability": "UNCHANGED_ORIGINAL_API_RULES"} for course in sorted(original_ids)}
    injected = []
    for course in missing:
        reason, row = None, None
        if course in invalid:
            reason = "ACTUAL_REGISTRATION_CREDIT_CONFLICT"
        elif selected is None:
            reason = "CATALOG_STRUCTURE_INVALID"
        else:
            matches = selected.loc[selected.course_id.eq(course)]
            if len(matches) != 1:
                reason = "CATALOG_COURSE_MISSING" if matches.empty else "CATALOG_COURSE_AMBIGUOUS"
            else:
                entry = matches.iloc[0]
                try:
                    catalog_credits = _number(entry.course_credits, positive=True)
                    if catalog_credits != actual[course]:
                        reason = "CATALOG_CREDIT_CONFLICT"
                    row = {"course_id": course, "course_credits": float(catalog_credits)}
                    for target, source in CATALOG_FIELDS.items():
                        if target in {"plan_course_type_id", "plan_requirement_type_id"}:
                            value = normalize_course_id(entry[source])
                            if value is None:
                                raise ValueError("Missing categorical catalog structure.")
                        else:
                            value = float(_number(entry[source], integer=target in {"plan_year_order", "plan_semester_order"}))
                        row[target] = value
                except ValueError:
                    reason = reason or "CATALOG_STRUCTURE_INVALID"
                if reason is None:
                    try:
                        row["attempt_number"] = _attempt(prior, course)
                    except ValueError as error:
                        reason = str(error)
                if reason is None:
                    name = entry.get("course_name_sl")
                    row["course_name"] = None if pd.isna(name) else str(name)
        if reason:
            rejected.append({"course_id": course, "reason": reason})
            continue
        field_sources = {"course_id": {"source": "actual_registration.course_id", "normalized": "Decimal_numeric_or_opaque_id"},
            "course_credits": {"source": "degree_course_catalog.course_credits", "matched_actual_registration_credits": True,
                               "catalog_source": deepcopy(catalog_source)},
            "attempt_number": {"source": "max_strictly_prior_cleaned_attempt_plus_one_across_degrees",
                "student_id": student_id, "course_id": course, "strict_before_part": TARGET_PART,
                "no_prior_record_semantics": "first_cleaned_GPA_bearing_attempt",
                "history_source": deepcopy(history_source)},
            "course_name": {"source": "degree_course_catalog.course_name_sl", "catalog_source": deepcopy(catalog_source)}}
        field_sources.update({target: {"source": "degree_course_catalog." + source,
            "catalog_source": deepcopy(catalog_source)} for target, source in CATALOG_FIELDS.items()})
        provenance[course] = {"candidate_source": "ACTUAL_INJECTED", "historical_eligibility_unverified": True,
            "official_requestability": "UNVERIFIED", "catalog_temporal_validity": "UNVERIFIED",
            "catalog_join_key": {"degree_id": degree_id, "course_id": course}, "field_sources": field_sources}
        injected.append(row)
    result = (pd.concat([original.copy(deep=True), pd.DataFrame(injected)], ignore_index=True)
              if injected else original.copy(deep=True))
    injected_ids = [row["course_id"] for row in injected]
    after_raw, after_model = raw_ids | set(injected_ids), original_ids | set(injected_ids)
    count = len(actual)
    coverage = lambda ids: len(set(actual) & ids) / count if count else None
    prior_parts = None if prior is None else prior.loc[prior.part_id.lt(TARGET_PART), "part_id"]
    report = {"mode": DIAGNOSTIC_MODE, "warning": "DIAGNOSTIC ONLY — ACTUAL COURSES WERE INJECTED",
        "target_outcomes_used": False, "historical_backtest_valid": False,
        "actual_course_count": count, "actual_course_ids": sorted(actual),
        "original_candidate_count": len(raw_ids), "augmented_candidate_count": len(after_raw),
        "original_model_candidate_count": len(original), "augmented_model_candidate_count": len(result),
        "number_of_injected_courses": len(injected), "injected_course_ids": injected_ids,
        "injected_courses": deepcopy(injected), "rejected_courses": rejected,
        "candidate_coverage_before": coverage(raw_ids), "candidate_coverage_after": coverage(after_raw),
        "model_candidate_coverage_before": coverage(original_ids), "model_candidate_coverage_after": coverage(after_model),
        "actual_courses_in_original_candidates": len(set(actual) & raw_ids),
        "actual_courses_in_augmented_candidates": len(set(actual) & after_raw),
        "actual_courses_in_augmented_model_candidates": len(set(actual) & after_model),
        "actual_courses_excluded_by_original_policy": sorted(set(actual) & (raw_ids - original_ids)),
        "history_latest_part": int(prior_parts.max()) if prior_parts is not None and len(prior_parts) else None,
        "candidate_provenance": provenance, "catalog_temporal_validity": "UNVERIFIED",
        "registration_identity_contract": "caller selects student_id + degree_id + part_id; only course_id/course_credits enter augmentation",
        "catalog_source": deepcopy(catalog_source), "history_source": deepcopy(history_source)}
    return result, report


class ActualCandidateSources:
    """Read/hash existing catalog and strictly earlier attempt history, once."""

    def __init__(self, catalog_path=None, history_path=None):
        self.catalog_path = Path(catalog_path or paths.CLEAN_DEGREE_COURSE_PATH_V2)
        self.history_path = Path(history_path or paths.CLEAN_STUDENT_COURSE_PATH_V2)
        self._catalog = self._history = None
        self.metadata = {}

    def load(self):
        if self._catalog is None or self._history is None:
            frames, metadata = {}, {}
            for name, path, columns in (("catalog", self.catalog_path, None),
                                        ("history", self.history_path, HISTORY_COLUMNS)):
                fingerprint = sha256(path)
                frame = pd.read_parquet(path, columns=columns)
                if sha256(path) != fingerprint:
                    raise ValueError(name + " changed while being read.")
                frames[name] = frame
                metadata[name + "_source"] = {"path": str(path.resolve()), "sha256": fingerprint}
            history = frames["history"]
            parts = pd.to_numeric(history.part_id, errors="coerce")
            if parts.isna().any():
                raise ValueError("Attempt history contains missing chronology.")
            history = history.loc[parts.lt(TARGET_PART)].copy()
            history["part_id"] = parts.loc[history.index]
            for column in ("student_id", "course_id"):
                history[column] = history[column].map(normalize_course_id)
            history.attrs["actual_candidate_identifiers_normalized"] = True
            self._catalog, self._history = frames["catalog"], history
            self.metadata = {**metadata, "history_as_of_part": HISTORY_AS_OF_PART,
                "history_strict_before_part": TARGET_PART, "history_rows": len(history),
                "history_latest_part": int(history.part_id.max()) if len(history) else None,
                "catalog_temporal_validity": "UNVERIFIED", "source_files_modified": False}
        return self._catalog, self._history

    def augment(self, original, student, registrations, *, original_api_course_ids=None):
        catalog, history = self.load()
        return augment_candidates(original, student, registrations, catalog, history,
            catalog_source=self.metadata["catalog_source"], history_source=self.metadata["history_source"],
            original_api_course_ids=original_api_course_ids)
