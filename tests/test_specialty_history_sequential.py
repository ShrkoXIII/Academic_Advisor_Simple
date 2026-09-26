"""The test semester is applied before its finalized outcomes update history."""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.experiments.specialty_history import (
    SPECIALTY_HISTORY_FEATURES, add_specialty_history_features,
)


def rows(parts, marks, fails, points):
    return pd.DataFrame({
        "row_id": range(len(parts)), "part_id": parts,
        "degree_id": ["A"] * len(parts),
        "plan_requirement_type_id": ["R"] * len(parts),
        "final_mark": marks, "is_fail": fails, "points": points,
    })


def test_20251_excludes_current_and_future_and_20252_includes_finalized_20251():
    train = rows([20243], [20], [1], [0])
    test = rows([20251, 20251, 20252], [80, 100, 10], [0, 0, 1], [4, 4, 0])
    before_train, before_test = train.copy(deep=True), test.copy(deep=True)
    _, enriched = add_specialty_history_features(train, test)
    for prefix in ["degree", "degree_requirement"]:
        assert enriched.loc[0, prefix + "_history_avg_mark"] == 20
        assert enriched.loc[1, prefix + "_history_avg_mark"] == 20
        assert enriched.loc[0, prefix + "_history_fail_rate"] == 1
        assert enriched.loc[0, prefix + "_history_avg_points"] == 0
        assert enriched.loc[0, prefix + "_history_effective_support"] == 1
        assert enriched.loc[2, prefix + "_history_avg_mark"] == pytest.approx(200 / 3)
        assert enriched.loc[2, prefix + "_history_fail_rate"] == pytest.approx(1 / 3)
        assert enriched.loc[2, prefix + "_history_avg_points"] == pytest.approx(8 / 3)
        assert enriched.loc[2, prefix + "_history_effective_support"] == 3
    changed = test.copy()
    changed.loc[changed.part_id.eq(20252), ["final_mark", "is_fail", "points"]] = [100, 0, 4]
    _, changed_features = add_specialty_history_features(train, changed)
    assert_frame_equal(enriched[SPECIALTY_HISTORY_FEATURES], changed_features[SPECIALTY_HISTORY_FEATURES])
    changed.loc[changed.part_id.eq(20251), ["final_mark", "is_fail", "points"]] = [0, 1, 0]
    _, changed_features = add_specialty_history_features(train, changed)
    assert_frame_equal(enriched.iloc[:2][SPECIALTY_HISTORY_FEATURES],
                       changed_features.iloc[:2][SPECIALTY_HISTORY_FEATURES])
    assert changed_features.loc[2, "degree_history_avg_mark"] == pytest.approx(20 / 3)
    assert_frame_equal(train, before_train)
    assert_frame_equal(test, before_test)


def test_generalized_parts_restore_unsorted_rows_with_duplicate_indices():
    train = rows([20243], [20], [1], [0])
    test = rows([20261, 20251, 20252, 20251], [0, 80, 10, 100], [1, 0, 1, 0], [0, 4, 0, 4])
    test.index = [7, 7, 2, 9]
    _, enriched = add_specialty_history_features(train, test)
    assert len(enriched) == len(test)
    assert enriched.row_id.tolist() == [0, 1, 2, 3]
    assert enriched.part_id.tolist() == test.part_id.tolist()
    assert enriched.degree_history_avg_mark.tolist() == pytest.approx([52.5, 20, 200 / 3, 20])
    assert_frame_equal(enriched[test.columns], test.reset_index(drop=True))


def test_new_degree_enters_both_hierarchy_levels_only_in_later_parts():
    train = rows([20243], [20], [1], [0])
    test = rows([20251, 20252], [80, 0], [0, 1], [4, 0]).assign(degree_id="B")
    _, enriched = add_specialty_history_features(train, test)
    assert enriched.loc[0, "degree_history_missing"]
    assert enriched.loc[0, "degree_requirement_history_missing"]
    assert enriched.loc[0, "degree_history_avg_mark"] == 20
    assert enriched.loc[1, "degree_history_effective_support"] == 1
    assert enriched.loc[1, "degree_requirement_history_effective_support"] == 1
    degree_mean = (80 + 20 * 50) / 21
    assert enriched.loc[1, "degree_history_avg_mark"] == pytest.approx(degree_mean)
    assert enriched.loc[1, "degree_requirement_history_avg_mark"] == pytest.approx((80 + 20 * degree_mean) / 21)


def test_training_rows_never_see_own_or_future_part_outcomes():
    train = rows([20221, 20231, 20231, 20243], [20, 80, 100, 0], [1, 0, 0, 1], [0, 4, 4, 0])
    test = rows([20251], [100], [0], [4])
    enriched, _ = add_specialty_history_features(train, test)
    assert enriched.loc[0, "degree_history_missing"]
    assert enriched.loc[1, "degree_history_avg_mark"] == 20
    assert enriched.loc[2, "degree_history_avg_mark"] == 20
    assert enriched.loc[3, "degree_history_avg_mark"] == pytest.approx(200 / 3)
    changed = train.copy()
    changed.loc[changed.part_id.ge(20231), ["final_mark", "points", "is_fail"]] = [0, 0, 1]
    altered, _ = add_specialty_history_features(changed, test)
    assert_frame_equal(enriched.iloc[:3][SPECIALTY_HISTORY_FEATURES],
                       altered.iloc[:3][SPECIALTY_HISTORY_FEATURES])


def test_empty_test_keeps_output_schema():
    train = rows([20243], [20], [1], [0])
    empty_test = rows([], [], [], [])
    _, enriched = add_specialty_history_features(train, empty_test)
    assert enriched.empty
    assert set(SPECIALTY_HISTORY_FEATURES) <= set(enriched)


@pytest.mark.parametrize("part", [20243, 20242])
def test_test_parts_must_all_follow_training(part):
    with pytest.raises(ValueError, match="precede every test"):
        add_specialty_history_features(rows([20243], [20], [1], [0]),
                                       rows([20251, part], [80, 0], [0, 1], [4, 0]))
