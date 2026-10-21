"""Read-only target-semester registrations/outcomes for post-prediction display.

This module is imported only by the local presentation API. The prediction,
ranking, training and run-storage paths do not receive observed outcomes.
"""
import math
from pathlib import Path
from threading import Lock

import pandas as pd

from src import paths
from .adapter import sha256


IDENTITY = ["student_id", "degree_id", "part_id"]
REGISTRATION_COLUMNS = ["student_course_id", *IDENTITY, "course_id", "course_credits", "register_status", "finish_status"]
OUTCOME_COLUMNS = ["student_course_id", *IDENTITY, "course_id", "course_credits", "course_name_sl",
                   "final_mark", "points", "grade_id", "grade_version_id", "course_outcome_status"]


def _identifier(value):
    return None if pd.isna(value) else str(value).strip()


def _number(value):
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def unavailable(reason, message):
    return {"status": "UNAVAILABLE", "reason": reason, "reason_ar": message,
            "course_count": None, "total_credits": None, "graded_course_count": None, "courses": []}


class ObservedPlanStore:
    """Cache local display data, refreshing when source file signatures change."""

    def __init__(self, roster_path=None, outcome_path=None):
        self.roster_path = Path(roster_path or paths.TEMPORAL_TEST_ROSTER_PATH_V2)
        self.outcome_path = Path(outcome_path or paths.TEMPORAL_TEST_PATH_V2)
        self._signature = None
        self._lock = Lock()
        self._frames = {}
        self._source = {}

    def _load(self):
        with self._lock:
            signature = []
            for path in (self.roster_path, self.outcome_path):
                try:
                    stat = path.stat()
                    signature.append((stat.st_size, stat.st_mtime_ns))
                except OSError:
                    signature.append(None)
            if signature == self._signature:
                return
            frames, source = {}, {}
            for name, path, columns in (("roster", self.roster_path, REGISTRATION_COLUMNS),
                                        ("outcomes", self.outcome_path, OUTCOME_COLUMNS)):
                try:
                    fingerprint = sha256(path)
                    frame = pd.read_parquet(path, columns=columns)
                    if sha256(path) != fingerprint:
                        raise ValueError("Display source changed while being read.")
                    for column in ["student_course_id", "student_id", "degree_id", "course_id"]:
                        frame[column] = frame[column].map(_identifier)
                    frame["part_id"] = pd.to_numeric(frame.part_id, errors="coerce")
                    frames[name] = frame
                    source[f"{name}_sha256"] = fingerprint
                    source[f"{name}_path"] = str(path.resolve())
                except (OSError, ValueError, KeyError):
                    source[f"{name}_status"] = "SOURCE_UNAVAILABLE_OR_INVALID"
            self._frames, self._source, self._signature = frames, source, signature

    def get(self, student):
        self._load()
        roster = self._frames.get("roster")
        if roster is None:
            return unavailable("REGISTRATION_SOURCE_UNAVAILABLE", "ملف التسجيل الفعلي غير متوفر أو غير صالح؛ لا يمكن حساب التطابق.")
        identity = {key: student[key] for key in IDENTITY}
        identity["part_id"] = int(identity["part_id"])

        def selected(frame):
            return frame.loc[frame.student_id.eq(str(identity["student_id"])) &
                             frame.degree_id.eq(str(identity["degree_id"])) & frame.part_id.eq(identity["part_id"])]

        registrations = selected(roster)
        if registrations.empty:
            return unavailable("NO_REGISTRATION_RECORD", "لا يوجد سجل تسجيل فعلي مطابق لهذا الطالب والدرجة والفصل.")
        if registrations.course_id.duplicated().any() or registrations.student_course_id.duplicated().any():
            return unavailable("AMBIGUOUS_REGISTRATION", "توجد تسجيلات مكررة للمادة أو المحاولة؛ لا يمكن اختيار سجل فعلي تلقائياً.")
        if (registrations[["course_id", "student_course_id"]].isna().any().any() or
                not registrations.register_status.isin(["R", "E"]).all() or
                any((_number(value) is None or _number(value) <= 0) for value in registrations.course_credits)):
            return unavailable("INVALID_REGISTRATION", "هوية مادة أو ساعاتها أو حالة تسجيلها غير صالحة للمقارنة.")
        outcomes = self._frames.get("outcomes")
        outcomes = selected(outcomes) if outcomes is not None else None
        by_attempt = {} if outcomes is None else {key: group for key, group in outcomes.groupby("student_course_id")}
        courses = []
        for registration in registrations.sort_values("course_id", kind="stable").to_dict("records"):
            course = {"course_id": registration["course_id"], "course_name": None,
                      "student_course_id": registration["student_course_id"],
                      "course_credits": _number(registration["course_credits"]),
                      "register_status": _identifier(registration["register_status"]),
                      "finish_status": _identifier(registration["finish_status"]),
                      "actual_mark": None, "actual_points": None, "grade_id": None, "grade_version_id": None,
                      "course_outcome_status": None, "result_status": "NO_FINAL_RESULT"}
            matches = by_attempt.get(registration["student_course_id"])
            if matches is not None:
                if len(matches) != 1:
                    course["result_status"] = "AMBIGUOUS_FINAL_RESULT"
                else:
                    outcome = matches.iloc[0]
                    if (outcome.course_id != registration["course_id"] or
                            _number(outcome.course_credits) != course["course_credits"]):
                        course["result_status"] = "OUTCOME_IDENTITY_MISMATCH"
                    else:
                        mark = _number(outcome.final_mark)
                        course["course_name"] = _identifier(outcome.course_name_sl)
                        if mark is None or not 0 <= mark <= 100:
                            course["result_status"] = "INVALID_FINAL_MARK"
                        else:
                            course.update(actual_mark=mark, actual_points=_number(outcome.points),
                                          grade_id=_identifier(outcome.grade_id), grade_version_id=_identifier(outcome.grade_version_id),
                                          course_outcome_status=_identifier(outcome.course_outcome_status), result_status="AVAILABLE")
            courses.append(course)
        graded = sum(course["actual_mark"] is not None for course in courses)
        return {"status": "AVAILABLE" if graded == len(courses) else "PARTIAL", **identity,
                "course_count": len(courses), "total_credits": sum(course["course_credits"] for course in courses),
                "graded_course_count": graded, "courses": courses,
                "source": {**self._source, "registration_definition": "saved R/E registration roster, including registrations without final outcomes",
                           "join_key": "student_course_id + student_id + degree_id + part_id + course_id + course_credits",
                           "used_for_prediction": False, "purpose": "post_prediction_display_only"}}
