"""Point-in-time student/course status contracts for the isolated experiment."""

import pandas as pd
import pytest

from src.features.student_course_status import previous_status_for_targets


def row(student, course, part, mark, *, withdrawn=False):
    return {
        "student_id": student,
        "course_id": course,
        "part_id": part,
        "final_mark": mark,
        "withdrawn": withdrawn,
    }


@pytest.mark.parametrize(
    ("mark", "expected"),
    [
        (49.999, "FAILED"),
        (50, "CONDITIONAL_PASS"),
        (59.999, "CONDITIONAL_PASS"),
        (60, "NORMAL_PASS"),
    ],
)
def test_mark_boundaries_use_previous_attempt_only(mark, expected):
    target = pd.DataFrame([row("A", "X", 20252, 0)])
    history = pd.DataFrame([row("A", "X", 20251, mark)])

    result = previous_status_for_targets(target, history)

    assert result.tolist() == [expected]


def test_first_attempt_ignores_current_and_future_outcomes():
    target = pd.DataFrame([row("A", "X", 20251, 10)])
    history = pd.DataFrame([
        row("A", "X", 20251, 99),
        row("A", "X", 20252, 15),
    ])

    assert previous_status_for_targets(target, history).tolist() == ["NEVER_TAKEN"]
    target["final_mark"] = 100
    assert previous_status_for_targets(target, history).tolist() == ["NEVER_TAKEN"]


def test_latest_prior_attempt_wins_even_when_history_is_unsorted():
    target = pd.DataFrame([row("A", "X", 20252, 0)])
    history = pd.DataFrame([
        row("A", "X", 20243, 56),
        row("A", "X", 20231, 42),
        row("A", "X", 20232, None, withdrawn=True),
    ])

    assert previous_status_for_targets(
        target, history, withdrawal_column="withdrawn"
    ).tolist() == ["CONDITIONAL_PASS"]


@pytest.mark.parametrize(
    ("history", "expected"),
    [
        ([row("A", "X", 20231, 42), row("A", "X", 20243, 65)], "NORMAL_PASS"),
        ([row("A", "X", 20231, 42), row("A", "X", 20243, 56)], "CONDITIONAL_PASS"),
        ([row("A", "X", 20231, 42), row("A", "X", 20243, None, withdrawn=True)], "WITHDRAWN"),
        ([row("A", "X", 20231, 56), row("A", "X", 20243, None, withdrawn=True)], "WITHDRAWN"),
    ],
)
def test_retake_status_tracks_latest_attempt(history, expected):
    target = pd.DataFrame([row("A", "X", 20251, 0)])

    assert previous_status_for_targets(
        target, pd.DataFrame(history), withdrawal_column="withdrawn"
    ).tolist() == [expected]


def test_students_and_courses_are_isolated():
    target = pd.DataFrame([
        row("A", "X", 20251, 0),
        row("A", "Y", 20251, 0),
        row("B", "X", 20251, 0),
    ], index=[9, 4, 17])
    history = pd.DataFrame([
        row("A", "X", 20243, 42),
        row("A", "Y", 20243, 75),
        row("B", "X", 20243, 55),
    ])

    result = previous_status_for_targets(target, history)

    assert result.index.tolist() == [9, 4, 17]
    assert result.tolist() == ["FAILED", "NORMAL_PASS", "CONDITIONAL_PASS"]


def test_same_part_attempts_without_sequence_are_rejected():
    target = pd.DataFrame([row("A", "X", 20252, 0)])
    history = pd.DataFrame([
        row("A", "X", 20251, 42),
        row("A", "X", 20251, 75),
    ])

    with pytest.raises(ValueError, match="same-part attempts"):
        previous_status_for_targets(target, history)


def test_missing_prior_mark_without_explicit_withdrawal_is_rejected():
    target = pd.DataFrame([row("A", "X", 20252, 0)])
    history = pd.DataFrame([row("A", "X", 20251, None)])

    with pytest.raises(ValueError, match="final_mark"):
        previous_status_for_targets(target, history)


def test_latest_unresolved_attempt_is_unknown_not_first_or_older_fail():
    target = pd.DataFrame([row("A", "X", 20252, 0)])
    history = pd.DataFrame([
        {**row("A", "X", 20231, 42), "unresolved": False},
        {**row("A", "X", 20251, None), "unresolved": True},
    ])

    result = previous_status_for_targets(
        target, history, withdrawal_column="withdrawn", unknown_column="unresolved"
    )

    assert result.tolist() == ["__UNKNOWN__"]


def test_nullable_integer_mark_does_not_override_explicit_withdrawal():
    target = pd.DataFrame([row("A", "X", 20252, 0)])
    history = pd.DataFrame({
        "student_id": ["A"], "course_id": ["X"], "part_id": [20251],
        "final_mark": pd.Series([pd.NA], dtype="Int64"), "withdrawn": [True],
    })

    assert previous_status_for_targets(
        target, history, withdrawal_column="withdrawn"
    ).tolist() == ["WITHDRAWN"]
