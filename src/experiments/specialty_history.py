import numpy as np
import pandas as pd

from ..feature_contract import training_weights


HISTORY_SMOOTHING_K = 20.0

SPECIALTY_HISTORY_FEATURES = [
    "degree_history_avg_mark",
    "degree_history_fail_rate",
    "degree_history_avg_points",
    "degree_history_effective_support",
    "degree_history_missing",
    "degree_requirement_history_avg_mark",
    "degree_requirement_history_fail_rate",
    "degree_requirement_history_avg_points",
    "degree_requirement_history_effective_support",
    "degree_requirement_history_missing",
]


def _weighted_history_source(frame):
    weight = training_weights(frame).astype("float64")
    return pd.DataFrame(
        {
            "part_id": pd.to_numeric(frame["part_id"]),
            "degree_id": frame["degree_id"],
            "plan_requirement_type_id": frame["plan_requirement_type_id"],
            "history_count": weight,
            "history_mark_sum": weight
            * pd.to_numeric(frame["final_mark"]).astype("float64"),
            "history_fail_sum": weight
            * pd.to_numeric(frame["is_fail"]).astype("float64"),
            "history_points_sum": weight
            * pd.to_numeric(frame["points"]).astype("float64"),
        },
        index=frame.index,
    )


def _prior_aggregates(source, keys, prefix):
    value_columns = [
        "history_count",
        "history_mark_sum",
        "history_fail_sum",
        "history_points_sum",
    ]
    group_columns = [*keys, "part_id"]
    grouped = (
        source.groupby(group_columns, dropna=False, observed=True, as_index=False)[
            value_columns
        ]
        .sum()
        .sort_values(group_columns, kind="stable")
    )
    if keys:
        cumulative = grouped.groupby(
            keys,
            dropna=False,
            observed=True,
        )[value_columns].cumsum()
    else:
        cumulative = grouped[value_columns].cumsum()
    prior = cumulative - grouped[value_columns]
    prior.columns = [f"{prefix}_{column}" for column in value_columns]
    return pd.concat(
        [grouped[group_columns].reset_index(drop=True), prior.reset_index(drop=True)],
        axis=1,
    )


def _total_aggregates(source, keys, prefix):
    value_columns = [
        "history_count",
        "history_mark_sum",
        "history_fail_sum",
        "history_points_sum",
    ]
    if keys:
        totals = source.groupby(
            keys,
            dropna=False,
            observed=True,
            as_index=False,
        )[value_columns].sum()
    else:
        totals = pd.DataFrame([source[value_columns].sum()])
    return totals.rename(
        columns={column: f"{prefix}_{column}" for column in value_columns}
    )


def _merge_training_history(frame, source):
    result = frame.copy()
    result["_experiment_row_order"] = np.arange(len(result))
    specifications = [
        ([], "global"),
        (["degree_id"], "degree"),
        (["degree_id", "plan_requirement_type_id"], "degree_requirement"),
    ]
    for keys, prefix in specifications:
        result = result.merge(
            _prior_aggregates(source, keys, prefix),
            on=[*keys, "part_id"],
            how="left",
            sort=False,
        )
    return (
        result.sort_values("_experiment_row_order", kind="stable")
        .drop(columns="_experiment_row_order")
        .reset_index(drop=True)
    )


def _merge_frozen_test_history(test, source):
    result = test.copy()
    global_totals = _total_aggregates(source, [], "global").iloc[0]
    for column, value in global_totals.items():
        result[column] = value
    result = result.merge(
        _total_aggregates(source, ["degree_id"], "degree"),
        on="degree_id",
        how="left",
        sort=False,
    )
    return result.merge(
        _total_aggregates(
            source,
            ["degree_id", "plan_requirement_type_id"],
            "degree_requirement",
        ),
        on=["degree_id", "plan_requirement_type_id"],
        how="left",
        sort=False,
    )


def _safe_average(numerator, denominator):
    numerator = pd.to_numeric(numerator).to_numpy(dtype="float64")
    denominator = pd.to_numeric(denominator).to_numpy(dtype="float64")
    return np.divide(
        numerator,
        denominator,
        out=np.full(len(denominator), np.nan, dtype="float64"),
        where=denominator > 0,
    )


def _finish_specialty_history(frame):
    result = frame.copy()
    prefixes = ["global", "degree", "degree_requirement"]
    suffixes = [
        "history_count",
        "history_mark_sum",
        "history_fail_sum",
        "history_points_sum",
    ]
    for prefix in prefixes:
        for suffix in suffixes:
            column = f"{prefix}_{suffix}"
            result[column] = pd.to_numeric(result[column]).fillna(0.0)

    global_count = result["global_history_count"].to_numpy(dtype="float64")
    global_mark = _safe_average(
        result["global_history_mark_sum"], result["global_history_count"]
    )
    global_fail = _safe_average(
        result["global_history_fail_sum"], result["global_history_count"]
    )
    global_points = _safe_average(
        result["global_history_points_sum"], result["global_history_count"]
    )

    degree_count = result["degree_history_count"].to_numpy(dtype="float64")
    degree_denominator = degree_count + HISTORY_SMOOTHING_K
    degree_mark = np.where(
        global_count > 0,
        (
            result["degree_history_mark_sum"].to_numpy(dtype="float64")
            + HISTORY_SMOOTHING_K * global_mark
        )
        / degree_denominator,
        np.nan,
    )
    degree_fail = np.where(
        global_count > 0,
        (
            result["degree_history_fail_sum"].to_numpy(dtype="float64")
            + HISTORY_SMOOTHING_K * global_fail
        )
        / degree_denominator,
        np.nan,
    )
    degree_points = np.where(
        global_count > 0,
        (
            result["degree_history_points_sum"].to_numpy(dtype="float64")
            + HISTORY_SMOOTHING_K * global_points
        )
        / degree_denominator,
        np.nan,
    )

    requirement_count = result[
        "degree_requirement_history_count"
    ].to_numpy(dtype="float64")
    requirement_denominator = requirement_count + HISTORY_SMOOTHING_K
    requirement_mark = (
        result["degree_requirement_history_mark_sum"].to_numpy(dtype="float64")
        + HISTORY_SMOOTHING_K * degree_mark
    ) / requirement_denominator
    requirement_fail = (
        result["degree_requirement_history_fail_sum"].to_numpy(dtype="float64")
        + HISTORY_SMOOTHING_K * degree_fail
    ) / requirement_denominator
    requirement_points = (
        result["degree_requirement_history_points_sum"].to_numpy(dtype="float64")
        + HISTORY_SMOOTHING_K * degree_points
    ) / requirement_denominator

    result["degree_history_avg_mark"] = degree_mark
    result["degree_history_fail_rate"] = degree_fail
    result["degree_history_avg_points"] = degree_points
    result["degree_history_effective_support"] = degree_count
    result["degree_history_missing"] = degree_count == 0
    result["degree_requirement_history_avg_mark"] = requirement_mark
    result["degree_requirement_history_fail_rate"] = requirement_fail
    result["degree_requirement_history_avg_points"] = requirement_points
    result["degree_requirement_history_effective_support"] = requirement_count
    result["degree_requirement_history_missing"] = requirement_count == 0

    history_columns = [
        f"{prefix}_{suffix}" for prefix in prefixes for suffix in suffixes
    ]
    return result.drop(columns=history_columns)


def add_specialty_history_features(train, test):
    if not train.empty and not test.empty and test["part_id"].min() <= train["part_id"].max():
        raise ValueError("Frozen specialty history must precede every test semester.")
    source = _weighted_history_source(train)
    enriched_train = _finish_specialty_history(
        _merge_training_history(train, source)
    )
    enriched_test = _finish_specialty_history(
        _merge_frozen_test_history(test, source)
    )
    return enriched_train, enriched_test
