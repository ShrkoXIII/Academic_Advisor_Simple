"""Allowlisted university examples and explicitly synthetic completion sources."""
import json
from pathlib import Path

import pandas as pd


def payloads(*, complete=False):
    folder = Path(__file__).parent / "fixtures"
    student = json.loads((folder / "api_student.json").read_text(encoding="utf8"))
    courses = json.loads((folder / "api_courses.json").read_text(encoding="utf8"))
    info = student["data"]["studentDegreeInfo"]
    identity = {"student_id": info["STUDENT_ID"], "degree_id": info["DEGREE_ID"], "part_id": 20251}
    request = {**identity, "student_api_response": student, "courses_api_response": courses,
               "source_contexts": {"student": dict(identity), "courses": dict(identity)},
               "history_as_of_part": 20243, "target_credits": 18}
    if complete:
        info.update(diploma_gpa="92", diploma_type_id="13.111", SEMESTER_REG_COURSES="6")
        def sourced(value):
            return {"value": value, "source": "synthetic_sis_ledger", "as_of_part": 20243}
        request["integration_context"] = {
            "student_values": {key: sourced(value) for key, value in {
                "current_gpa_credits": 108, "prior_total_reg_courses": 42,
                "prior_total_reg_credits": 111, "prior_total_fail_courses": 1,
                "prior_total_fail_credits": 3, "prior_registered_semesters": 8,
            }.items()},
            "previous_course_statuses": {row["COURSE_ID"]: sourced(
                "NEW" if int(row["ATTEMPTS_COUNT"]) == 0 else "FAILED"
            ) for row in courses["data"]["availableCourses"]},
            "registration_policy": {
                "source": "synthetic_registration_policy", "part_id": 20251,
                "requirement_group_modes": {row["REQUIREMENT_ID"]: "strict_remaining"
                                            for row in courses["data"]["availableCourses"]},
                "allow_register_all_optional_confirmed": True,
                "approved_exception_course_ids": [row["COURSE_ID"] for row in courses["data"]["availableCourses"]
                                                  if row["STATUS_REASON_CODE"] == "EXCEPTION"],
                "allowed_failed_repeat_credits": 18, "allowed_withdrawn_repeat_credits": 18,
                "attempts_scope_confirmed": True, "load_profile": "study",
            },
        }
    return request


def catalog(request):
    return pd.DataFrame([{
        "degree_id": request["degree_id"], "course_id": row["COURSE_ID"],
        "course_type_id": "3", "requirement_type_id": row["REQUIREMENT_TYPE_ID"],
        "course_credits": float(row["COURSE_CREDITS"]), "credits_count": float(row["CREDITS_COUNT"]),
        "year_order": int(row["YEAR_ORDER"]), "semester_order": int(row["SEMESTER_ORDER"]),
    } for row in request["courses_api_response"]["data"]["availableCourses"]]).drop_duplicates("course_id", keep="first")


def grade_scale():
    from src.grade_scale import GradeScale
    return GradeScale(pd.DataFrame({"grade_version_id": ["3.111"] * 4,
                                   "from_percent": [50., 60., 75., 90.],
                                   "points": [1., 2., 3., 4.], "grade_show": ["D", "C", "B", "A"]}))
