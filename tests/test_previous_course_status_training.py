"""The experimental model matrix extends, rather than changes, V2 contracts."""

import pandas as pd

from src.experiments.course_only_core import COURSE_ONLY_FEATURES
from src.experiments.previous_course_status_training import (
    COURSE_ONLY_WITH_PREVIOUS_STATUS,
    PLAN_AWARE_WITH_PREVIOUS_STATUS,
    learn_augmented_levels,
    prepare_augmented_folds,
    prepare_augmented_matrix,
    train_augmented_one,
)
from src.features.feature_contract import (
    BASE_FEATURES, CATEGORICAL_FEATURES, CATEGORY_MISSING, CATEGORY_UNKNOWN,
)


def test_two_contracts_append_one_categorical_without_changing_base():
    assert PLAN_AWARE_WITH_PREVIOUS_STATUS == [*BASE_FEATURES, "previous_course_status"]
    assert COURSE_ONLY_WITH_PREVIOUS_STATUS == [*COURSE_ONLY_FEATURES, "previous_course_status"]
    assert len(PLAN_AWARE_WITH_PREVIOUS_STATUS) == 48
    assert len(COURSE_ONLY_WITH_PREVIOUS_STATUS) == 34
    assert len(CATEGORICAL_FEATURES) == 5


def test_augmented_matrix_keeps_order_and_maps_unseen_status():
    values = {name: ["known", "known", "known"] if name in CATEGORICAL_FEATURES
              else [1, 2, 3] for name in BASE_FEATURES}
    values["previous_course_status"] = ["FAILED", "UNSEEN_CODE", None]
    frame = pd.DataFrame(values)
    levels = learn_augmented_levels(frame.iloc[:1])

    matrix = prepare_augmented_matrix(frame, levels, COURSE_ONLY_FEATURES)

    assert matrix.columns.tolist() == [*COURSE_ONLY_FEATURES, "previous_course_status"]
    assert matrix.previous_course_status.tolist() == [
        "FAILED", CATEGORY_UNKNOWN, CATEGORY_MISSING,
    ]
    assert isinstance(matrix.previous_course_status.dtype, pd.CategoricalDtype)
    assert set(["NEVER_TAKEN", "FAILED", "WITHDRAWN", "CONDITIONAL_PASS", "NORMAL_PASS"]).issubset(
        levels["previous_course_status"]
    )


def test_augmented_folds_keep_official_cutoffs_and_fit_weights():
    values = {name: ["known"] * 3 if name in CATEGORICAL_FEATURES
              else [1, 2, 3] for name in BASE_FEATURES}
    values.update({
        "part_id": [20213, 20231, 20241],
        "final_mark": [45, 55, 65], "is_fail": [1, 0, 0],
        "previous_course_status": ["NEVER_TAKEN", "FAILED", "WITHDRAWN"],
    })

    folds = prepare_augmented_folds(pd.DataFrame(values), COURSE_ONLY_FEATURES)

    assert [(fold["fit_rows"], fold["valid_rows"]) for fold in folds] == [(1, 1), (2, 1)]
    assert folds[0]["fit_weight"].tolist() == [0.25]
    assert folds[1]["fit_weight"].tolist() == [0.25, 1.0]
    assert folds[0]["fit_X"].columns.tolist() == COURSE_ONLY_WITH_PREVIOUS_STATUS
    assert folds[0]["valid_X"].previous_course_status.tolist() == ["FAILED"]


def test_lightgbm_receives_six_categorical_features():
    values = {name: ["known"] * 8 if name in CATEGORICAL_FEATURES
              else list(range(8)) for name in BASE_FEATURES}
    values["previous_course_status"] = ["FAILED", "NEVER_TAKEN"] * 4
    frame = pd.DataFrame(values)
    matrix = prepare_augmented_matrix(frame, learn_augmented_levels(frame), BASE_FEATURES)

    model = train_augmented_one(
        matrix, [40, 80] * 4, [1.0] * 8,
        {"objective": "regression", "metric": "l1", "verbosity": -1,
         "min_data_in_leaf": 1, "num_leaves": 3, "num_threads": 1},
        num_boost_round=3,
    )

    assert model.feature_name() == PLAN_AWARE_WITH_PREVIOUS_STATUS
    assert len(model.pandas_categorical) == 6
