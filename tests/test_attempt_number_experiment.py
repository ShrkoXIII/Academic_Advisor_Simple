import numpy as np
import pandas as pd
import pytest

from src.experiments.attempt_number_core import (
    transform_matrix, row_fingerprint, paired_cluster_interval,
)


def test_transform_keeps_other_columns_order_categories_and_input():
    matrix = pd.DataFrame({"x": [8., 9., 10.], "attempt_number": [1., 2., 5.],
                           "cat": pd.Categorical(["a", "b", "a"])}, index=[9, 3, 7])
    before = matrix.copy(deep=True)
    binary = transform_matrix(matrix, "B")
    assert binary.columns.tolist() == ["x", "is_repeat", "cat"]
    assert binary.is_repeat.tolist() == [0., 1., 1.]
    pd.testing.assert_frame_equal(binary[["x", "cat"]], before[["x", "cat"]])
    assert transform_matrix(matrix, "C").columns.tolist() == ["x", "cat"]
    pd.testing.assert_frame_equal(transform_matrix(matrix, "A"), before)
    pd.testing.assert_frame_equal(matrix, before)


@pytest.mark.parametrize("value", [np.nan, 0, -1, 1.5, np.inf])
def test_unknown_or_invalid_attempt_cannot_become_first_attempt(value):
    with pytest.raises(ValueError, match="attempt"):
        transform_matrix(pd.DataFrame({"attempt_number": [value]}), "B")


def test_row_fingerprint_detects_order_and_membership_changes():
    rows = pd.DataFrame({"student_course_id": ["1", "2"], "student_id": ["s", "s"],
                         "degree_id": ["d", "d"], "course_id": ["a", "b"],
                         "part_id": [20251, 20251]})
    assert row_fingerprint(rows) != row_fingerprint(rows.iloc[::-1])
    assert row_fingerprint(rows) != row_fingerprint(rows.iloc[:1])


def test_cluster_bootstrap_resamples_students_and_retains_all_their_rows():
    result = paired_cluster_interval(["a", "a", "b"], [1., 1., 3.], draws=1000)
    assert result["students"] == 2
    assert result["rows"] == 3
    assert result["delta"] == pytest.approx(5 / 3)
    assert result["low"] == 1.
    assert result["high"] == 3.
