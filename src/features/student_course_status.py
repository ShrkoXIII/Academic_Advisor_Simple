"""Student-specific previous course attempt status at a target semester."""

import numpy as np
import pandas as pd


STATUS_LEVELS = [
    "NEVER_TAKEN",
    "FAILED",
    "WITHDRAWN",
    "CONDITIONAL_PASS",
    "NORMAL_PASS",
]
_KEYS = ["student_id", "course_id", "part_id"]


def _keys(frame, name):
    missing = set(_KEYS) - set(frame)
    if missing:
        raise ValueError(f"{name} missing keys: {sorted(missing)}")
    result = frame[_KEYS].copy()
    for column in ("student_id", "course_id"):
        result[column] = result[column].astype("string").str.strip()
        if result[column].isna().any() or result[column].eq("").any():
            raise ValueError(f"{name} has missing {column}")
    result["part_id"] = pd.to_numeric(result["part_id"], errors="raise")
    if result["part_id"].isna().any():
        raise ValueError(f"{name} has missing part_id")
    result["part_id"] = result["part_id"].astype("int64")
    return result


def previous_status_for_targets(
    target_rows, history_rows, *, withdrawal_column=None, unknown_column=None
):
    """Return each student's latest same-course status from a strictly earlier part.

    `history_rows` must contain graded attempts with `final_mark`. A caller may
    supply an explicit, trustworthy boolean withdrawal column. Unknown prior
    source codes may be marked by an explicit boolean unknown column; they do
    not become first attempts. A missing mark alone never means withdrawal.
    Multiple attempts in the same academic part
    are rejected because the available V2 data has no within-part sequence.
    """
    if target_rows.empty:
        return pd.Series([], index=target_rows.index, dtype="string", name="previous_course_status")
    left = _keys(target_rows, "target rows")
    left["_position"] = np.arange(len(left), dtype="int64")
    if history_rows.empty:
        return pd.Series(
            ["NEVER_TAKEN"] * len(left), index=target_rows.index,
            dtype="string", name="previous_course_status",
        )
    if "final_mark" not in history_rows:
        raise ValueError("history rows missing final_mark")
    if withdrawal_column is not None and withdrawal_column not in history_rows:
        raise ValueError(f"history rows missing withdrawal column {withdrawal_column}")
    if unknown_column is not None and unknown_column not in history_rows:
        raise ValueError(f"history rows missing unknown column {unknown_column}")
    right = _keys(history_rows, "history rows")
    right = right.loc[right["part_id"].lt(left["part_id"].max())].copy()
    if right.empty:
        return pd.Series(
            ["NEVER_TAKEN"] * len(left), index=target_rows.index,
            dtype="string", name="previous_course_status",
        )
    if right.duplicated(_KEYS).any():
        raise ValueError("Ambiguous same-part attempts for one student and course")
    mark = pd.to_numeric(history_rows.loc[right.index, "final_mark"], errors="coerce")
    if withdrawal_column is None:
        withdrawn = pd.Series(False, index=right.index)
    else:
        withdrawn = history_rows.loc[right.index, withdrawal_column].astype("boolean")
        if withdrawn.isna().any():
            raise ValueError("Explicit withdrawal indicator must be known")
    if unknown_column is None:
        unknown = pd.Series(False, index=right.index)
    else:
        unknown = history_rows.loc[right.index, unknown_column].astype("boolean")
        if unknown.isna().any():
            raise ValueError("Explicit unresolved indicator must be known")
    if (withdrawn & unknown).any():
        raise ValueError("An attempt cannot be both withdrawn and unresolved")
    if mark[~(withdrawn | unknown)].isna().any():
        raise ValueError("Non-withdrawn prior attempt has missing final_mark")
    right["previous_course_status"] = np.select(
        [
            withdrawn.to_numpy(dtype=bool), unknown.to_numpy(dtype=bool),
            mark.lt(50).fillna(False).to_numpy(dtype=bool),
            mark.lt(60).fillna(False).to_numpy(dtype=bool),
        ],
        ["WITHDRAWN", "__UNKNOWN__", "FAILED", "CONDITIONAL_PASS"],
        default="NORMAL_PASS",
    )
    merged = pd.merge_asof(
        left.sort_values(["part_id", "student_id", "course_id"], kind="stable"),
        right.sort_values(["part_id", "student_id", "course_id"], kind="stable"),
        on="part_id", by=["student_id", "course_id"],
        direction="backward", allow_exact_matches=False,
    )
    ordered = merged.sort_values("_position", kind="stable")
    return pd.Series(
        ordered["previous_course_status"].fillna("NEVER_TAKEN").to_numpy(),
        index=target_rows.index, dtype="string", name="previous_course_status",
    )
