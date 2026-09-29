"""Experimental datasets add only point-in-time status to official V2 rows."""

import pandas as pd

from src.experiments.previous_course_status_data import (
    augment_feature_frame,
    build_status_history,
)


def test_roster_is_chronology_and_w_is_not_a_zero_mark_fail():
    roster = pd.DataFrame([
        {"student_course_id": "1", "student_id": "A", "course_id": "X", "part_id": 20231, "finish_status": "F"},
        {"student_course_id": "2", "student_id": "A", "course_id": "X", "part_id": 20243, "finish_status": "W"},
        {"student_course_id": "3", "student_id": "B", "course_id": "Y", "part_id": 20243, "finish_status": "Z"},
        {"student_course_id": "4", "student_id": "C", "course_id": "Z", "part_id": 20243, "finish_status": "P"},
    ])
    graded = pd.DataFrame([
        {"student_course_id": "1", "final_mark": 42},
        {"student_course_id": "4", "final_mark": 56},
    ])

    history = build_status_history(roster, graded)
    official = pd.DataFrame([
        {"student_course_id": "5", "student_id": "A", "course_id": "X", "part_id": 20251, "attempt_number": 3, "final_mark": 75, "is_fail": 0},
        {"student_course_id": "6", "student_id": "B", "course_id": "Y", "part_id": 20251, "attempt_number": 2, "final_mark": 30, "is_fail": 1},
        {"student_course_id": "7", "student_id": "C", "course_id": "Z", "part_id": 20251, "attempt_number": 2, "final_mark": 80, "is_fail": 0},
        {"student_course_id": "8", "student_id": "D", "course_id": "Q", "part_id": 20251, "attempt_number": 1, "final_mark": 90, "is_fail": 0},
    ])

    augmented = augment_feature_frame(official, history)

    assert augmented.previous_course_status.tolist() == [
        "WITHDRAWN", "__UNKNOWN__", "CONDITIONAL_PASS", "NEVER_TAKEN"
    ]
    pd.testing.assert_frame_equal(
        augmented.drop(columns="previous_course_status"), official
    )
