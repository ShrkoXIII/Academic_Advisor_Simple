"""Scan raw registrations from 20251 and export the requested low-load cohorts.

Run from the project root: python -m scripts.scan_student_over_polict
The exports contain one row per registered course, joined to its exact status.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.data.cleaning_utils import clean_id_columns


ROOT = Path(__file__).resolve().parents[1]
KEYS = ["student_id", "degree_id", "part_id"]
MIN_PART = 20251
LIMIT = 12
SOURCES = {
    "status": ROOT / "data/raw/v_add_student_degree_status.parquet",
    "courses": ROOT / "data/raw/v_crg_student_course_raw.parquet",
    "plan": ROOT / "data/raw/v_acd_degree_course.parquet",
}
RULES = {
    "semester_filter": "part_id >= 20251 (inclusive, including 20253)",
    "load_filter": "0 < semester_reg_credits < 12; zero means no registration",
    "registered_courses": "register_status in [R, E]; no outcome or GPA filters",
    "join_key": KEYS,
    "final_year_order": "max(year_order) per degree_id in the active raw curriculum",
    "final_year": "start_level_name_short >= final_year_order",
    "remaining_credits_start": "degree_credits_count - start_total_in_credits",
    "all_remaining": "remaining_credits_start > 0 and semester_reg_credits equals remaining_credits_start",
    "excluded": "final_year OR all_remaining; evaluated separately for each semester",
    "unresolved": "missing status, inconsistent registration totals, or insufficient exception data",
    "output_grain": "one raw registered course joined to its student-degree-semester status",
    "suffixes": "shared non-key raw columns use _course and _status",
    "policy_scope": "requested numerical screen; does not establish a summer policy violation",
}


def cohort_counts(frame):
    return {
        "student_semesters": len(frame),
        "unique_students": int(frame["student_id"].nunique()),
    }


def main():
    raw = {name: pd.read_parquet(path) for name, path in SOURCES.items()}
    status = clean_id_columns(raw["status"], ["student_status_id", "student_id", "degree_id", "grade_version_id"])
    courses = clean_id_columns(raw["courses"], ["student_course_id", "student_id", "degree_id", "course_id", "grade_id", "faculty_id"])
    plan = clean_id_columns(raw["plan"], ["degree_id"])
    status["part_id"] = status["part_id"].astype("Int64")
    courses["part_id"] = courses["part_id"].astype("Int64")
    status = status.loc[status["part_id"].ge(MIN_PART)].copy()
    courses = courses.loc[courses["part_id"].ge(MIN_PART)].copy()
    registered = courses.loc[courses["register_status"].str.strip().isin(["R", "E"])].copy()
    assert not status.duplicated(KEYS).any(), "Ambiguous status join"
    assert not registered["student_course_id"].duplicated().any(), "Duplicate course records"
    assert not status[KEYS].isna().any().any()
    assert not registered[KEYS + ["course_credits"]].isna().any().any()

    totals = registered.groupby(KEYS, dropna=False).agg(
        course_registered_credits=("course_credits", "sum"),
        course_registered_count=("student_course_id", "size"),
    ).reset_index()
    scan = status.merge(totals, on=KEYS, how="outer", validate="one_to_one", indicator="source_match")
    status_low = scan["semester_reg_credits"].gt(0) & scan["semester_reg_credits"].lt(LIMIT)
    course_low = scan["course_registered_credits"].gt(0) & scan["course_registered_credits"].lt(LIMIT)
    low = scan.loc[status_low | course_low].copy()
    low["status_row_found"] = low["source_match"].ne("right_only")
    low["registration_credit_match"] = np.isclose(low["semester_reg_credits"], low["course_registered_credits"], rtol=0, atol=1e-8)
    low["registration_count_match"] = low["semester_reg_courses"].eq(low["course_registered_count"])

    years = plan.loc[plan["active"].eq("A")].groupby("degree_id")["year_order"].max()
    low["final_year_order"] = low["degree_id"].map(years).astype("Int64")
    year_known = low["start_level_name_short"].gt(0) & low["final_year_order"].gt(0)
    low["is_final_year_start"] = low["start_level_name_short"].ge(low["final_year_order"]).astype("boolean").where(year_known)
    low["remaining_credits_start"] = low["degree_credits_count"] - low["start_total_in_credits"]
    remaining_known = low["degree_credits_count"].gt(0) & low["start_total_in_credits"].ge(0) & low["remaining_credits_start"].ge(0)
    all_remaining = np.isclose(low["semester_reg_credits"], low["remaining_credits_start"], rtol=0, atol=1e-8) & low["remaining_credits_start"].gt(0)
    low["registered_all_remaining_credits"] = pd.Series(all_remaining, index=low.index, dtype="boolean").where(remaining_known)
    # End-of-semester level is retained as evidence, but never drives exclusion.
    low["reaches_final_year_at_end"] = low["end_level_name_short"].ge(low["final_year_order"]).astype("boolean").where(low["end_level_name_short"].gt(0) & low["final_year_order"].gt(0))
    reliable = low["status_row_found"] & low["registration_credit_match"] & low["registration_count_match"]
    exception = low["is_final_year_start"] | low["registered_all_remaining_credits"]
    low["classification"] = "unresolved"
    low.loc[reliable & exception.eq(False).fillna(False), "classification"] = "retained"
    low.loc[reliable & exception.eq(True).fillna(False), "classification"] = "excluded"
    low["exclusion_reason"] = ""
    last = low["is_final_year_start"].fillna(False)
    remaining = low["registered_all_remaining_credits"].fillna(False)
    low.loc[last, "exclusion_reason"] = "final_year_at_semester_start"
    low.loc[remaining, "exclusion_reason"] = "registered_all_remaining_credits"
    low.loc[last & remaining, "exclusion_reason"] = "final_year_at_semester_start;registered_all_remaining_credits"
    low["review_reason"] = ""
    low.loc[low["classification"].eq("unresolved"), "review_reason"] = "insufficient_exception_data_or_inconsistent_registration_totals"
    low.loc[~low["status_row_found"], "review_reason"] = "missing_exact_student_degree_semester_status"
    low = low.sort_values(["part_id", "student_id", "degree_id"]).reset_index(drop=True)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "rules": RULES,
        "sources": {},
        "scan": {
            "status_rows_in_window": len(status),
            "course_rows_in_window_all_statuses": len(courses),
            "registered_course_rows_in_window": len(registered),
            "zero_credit_status_rows_not_enrolled": int(status["semester_reg_credits"].eq(0).sum()),
            "course_student_semesters_missing_status": int(scan["source_match"].eq("right_only").sum()),
            "matched_registration_totals_disagree": int((scan["source_match"].eq("both") & ~np.isclose(scan["semester_reg_credits"], scan["course_registered_credits"], rtol=0, atol=1e-8)).sum()),
        },
        "all_low_load": cohort_counts(low),
        "status_confirmed_low_load": cohort_counts(low.loc[low["status_row_found"]]),
        "exception_counts_status_confirmed": {
            "final_year_at_start": int(last.sum()),
            "all_remaining_credits": int(remaining.sum()),
            "both": int((last & remaining).sum()),
        },
        "cohorts": {},
        "by_semester": [],
    }
    for name, path in SOURCES.items():
        summary["sources"][name] = {
            "path": str(path.relative_to(ROOT)),
            "rows": len(raw[name]),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    for part in sorted(scan["part_id"].dropna().unique()):
        term = low.loc[low["part_id"].eq(part)]
        summary["by_semester"].append({
            "part_id": int(part),
            "status_confirmed_low_load": cohort_counts(term.loc[term["status_row_found"]]),
            **{label: cohort_counts(term.loc[term["classification"].eq(label)]) for label in ["retained", "excluded", "unresolved"]},
        })

    outputs = {"retained": "student_over_polict.parquet", "excluded": "student_over_polict_excluded.parquet", "unresolved": "student_over_polict_unresolved.parquet"}
    for label, filename in outputs.items():
        cohort = low.loc[low["classification"].eq(label)].copy()
        detail = registered.merge(cohort, on=KEYS, how="right", suffixes=("_course", "_status"), validate="many_to_one")
        detail = detail.sort_values(["part_id", "student_id", "degree_id", "student_course_id"]).reset_index(drop=True)
        table = pa.Table.from_pandas(detail, preserve_index=False)
        metadata = dict(table.schema.metadata or {})
        metadata[b"student_over_polict_rules"] = json.dumps(RULES, ensure_ascii=False).encode("utf-8")
        metadata[b"student_over_polict_generated_at"] = summary["generated_at_utc"].encode("utf-8")
        pq.write_table(table.replace_schema_metadata(metadata), ROOT / filename, compression="snappy")
        restored = pd.read_parquet(ROOT / filename)
        pd.testing.assert_frame_equal(detail, restored)
        assert len(restored[KEYS].drop_duplicates()) == len(cohort)
        summary["cohorts"][label] = {**cohort_counts(cohort), "course_rows": len(detail), "file": filename}
    assert sum(item["student_semesters"] for item in summary["cohorts"].values()) == len(low)
    summary["retained_students_reaching_final_year_at_end"] = int(low.loc[low["classification"].eq("retained"), "reaches_final_year_at_end"].sum())
    summary["validation"] = "Exact composite joins, no duplicate source records, registration total reconciliation, complete cohort partition, and all three Parquet read-back comparisons passed."
    report = ROOT / "reports/student_over_polict_scan.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ["all_low_load", "status_confirmed_low_load", "exception_counts_status_confirmed", "cohorts", "by_semester", "validation"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
