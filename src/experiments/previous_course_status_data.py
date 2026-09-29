"""Build isolated V2 feature tables with a previous student-course status."""

import json

import pandas as pd

from src.features.student_course_status import STATUS_LEVELS, previous_status_for_targets
from src.paths import (
    CLEAN_REGISTRATION_ROSTER_PATH_V2,
    CLEAN_STUDENT_COURSE_PATH_V2,
    PROJECT_ROOT,
    TEMPORAL_TEST_FEATURES_PATH_V2,
    TEMPORAL_TRAIN_FEATURES_PATH_V2,
)


FEATURE_OUTPUT_DIR = PROJECT_ROOT / "data/features/experiments/previous_course_status"
EVALUATION_OUTPUT_DIR = PROJECT_ROOT / "data/evaluation/experiments/previous_course_status"
GRADED_FINISH_CODES = frozenset({"F", "FE", "FA", "P"})


def build_status_history(roster, graded):
    """Join course-level registrations to marks, retaining W and unresolved events.

    The V2 registration roster is the withdrawal source. Clean graded rows
    absent from that roster are also retained as dated attempts when they have
    keys. Finish codes other than W/P/F/FE/FA remain explicitly unresolved.
    """
    required_roster = {
        "student_course_id", "student_id", "course_id", "part_id", "finish_status"
    }
    required_graded = {"student_course_id", "final_mark"}
    if required_roster - set(roster) or required_graded - set(graded):
        raise ValueError("Status history source is missing required columns")
    roster = roster[list(required_roster)].copy()
    graded = graded.copy()
    for frame, name in [(roster, "roster"), (graded, "graded")]:
        frame["student_course_id"] = frame["student_course_id"].astype("string")
        if frame["student_course_id"].isna().any() or frame["student_course_id"].duplicated().any():
            raise ValueError(f"{name} has missing or duplicate student_course_id")
    graded_columns = ["student_course_id", "final_mark"]
    joined = roster.merge(graded[graded_columns], on="student_course_id", how="left", validate="one_to_one")
    for column in ("student_id", "course_id", "part_id"):
        if column in graded:
            audit = roster[["student_course_id", column]].merge(
                graded[["student_course_id", column]], on="student_course_id",
                how="inner", suffixes=("_roster", "_graded"), validate="one_to_one",
            )
            if not audit[f"{column}_roster"].astype("string").equals(
                audit[f"{column}_graded"].astype("string")
            ):
                raise ValueError(f"Roster and graded sources disagree on {column}")
    joined["finish_status"] = joined["finish_status"].astype("string").str.strip().str.upper()
    joined["withdrawn"] = joined["finish_status"].eq("W").fillna(False).astype(bool)
    joined["unresolved"] = (
        ~joined["withdrawn"]
        & (~joined["finish_status"].isin(GRADED_FINISH_CODES).fillna(False)
           | joined["final_mark"].isna())
    ).astype(bool)
    extra = graded.loc[~graded["student_course_id"].isin(roster["student_course_id"])].copy()
    if len(extra):
        if not {"student_id", "course_id", "part_id"}.issubset(extra):
            raise ValueError("Clean-only grade rows need student/course/part keys")
        extra = extra[["student_course_id", "student_id", "course_id", "part_id", "final_mark"]]
        extra["finish_status"] = "CLEAN_GRADED"
        extra["withdrawn"] = False
        extra["unresolved"] = extra["final_mark"].isna()
        joined = pd.concat([joined, extra], ignore_index=True)
    if joined.duplicated(["student_id", "course_id", "part_id"]).any():
        raise ValueError("Status history has ambiguous same-part attempts")
    return joined.reset_index(drop=True)


def augment_feature_frame(official_features, history):
    """Preserve every official row/column/value and append one status column."""
    if "previous_course_status" in official_features:
        raise ValueError("Feature already exists on the official frame")
    augmented = official_features.copy()
    augmented["previous_course_status"] = previous_status_for_targets(
        official_features, history,
        withdrawal_column="withdrawn", unknown_column="unresolved",
    )
    return augmented


def _distribution(frame):
    counts = frame["previous_course_status"].value_counts(dropna=False)
    return {
        status: {"rows": int(counts.get(status, 0)),
                 "percent": 100 * int(counts.get(status, 0)) / len(frame)}
        for status in [*STATUS_LEVELS, "__UNKNOWN__"]
    }


def build_experimental_datasets():
    """Write two new Parquet files and prove row/target reconciliation."""
    outputs = {
        "train": FEATURE_OUTPUT_DIR / "temporal_train_features.parquet",
        "test": FEATURE_OUTPUT_DIR / "temporal_test_features.parquet",
    }
    roster = pd.read_parquet(CLEAN_REGISTRATION_ROSTER_PATH_V2, columns=[
        "student_course_id", "student_id", "course_id", "part_id", "finish_status",
    ])
    graded = pd.read_parquet(CLEAN_STUDENT_COURSE_PATH_V2, columns=[
        "student_course_id", "student_id", "course_id", "part_id", "final_mark",
    ])
    history = build_status_history(roster, graded)
    summary = {
        "status_source": "V2 registration roster chronology + V2 clean student-course marks",
        "withdrawal_source": "registration_roster_v2.finish_status == W",
        "history_rows": len(history),
        "roster_rows": len(roster),
        "withdrawal_rows": int(history["withdrawn"].sum()),
        "unresolved_history_rows": int(history["unresolved"].sum()),
    }
    FEATURE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, official_path in [
        ("train", TEMPORAL_TRAIN_FEATURES_PATH_V2),
        ("test", TEMPORAL_TEST_FEATURES_PATH_V2),
    ]:
        official = pd.read_parquet(official_path)
        if not official["student_course_id"].isin(roster["student_course_id"]).all():
            raise ValueError(f"{name} target row is absent from V2 roster")
        augmented = augment_feature_frame(official, history)
        if outputs[name].exists():
            saved = pd.read_parquet(outputs[name])
        else:
            augmented.to_parquet(outputs[name], index=False)
            saved = pd.read_parquet(outputs[name])
        pd.testing.assert_frame_equal(
            saved.drop(columns="previous_course_status"), official,
        )
        if not saved["previous_course_status"].equals(augmented["previous_course_status"]):
            raise ValueError(f"{name} saved status differs from current V2 sources")
        if saved["previous_course_status"].isna().any():
            raise ValueError(f"{name} has missing previous_course_status")
        summary[name] = {
            "official_rows": len(official), "experimental_rows": len(saved),
            "row_difference": len(saved) - len(official),
            "official_students": int(official["student_id"].nunique()),
            "experimental_students": int(saved["student_id"].nunique()),
            "part_distribution": {str(k): int(v) for k, v in official["part_id"].value_counts().sort_index().items()},
            "targets_identical": bool(saved[["final_mark", "is_fail"]].equals(official[["final_mark", "is_fail"]])),
            "status_distribution": _distribution(saved),
        }
        if not summary[name]["targets_identical"]:
            raise ValueError(f"{name} targets changed")
        print(f"{name}: {len(saved)} rows, status={saved.previous_course_status.value_counts().to_dict()}", flush=True)
    EVALUATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (EVALUATION_OUTPUT_DIR / "data_reconciliation.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary
