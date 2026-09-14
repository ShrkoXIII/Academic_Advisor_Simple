"""Export recorded 12-18 credit loads with fewer than 12 pass/fail credits.

Run: python -m scripts.scan_under_12_after_status_change
This is a comparison within the raw export, not a dated registration history.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.cleaning_utils import clean_id_columns


ROOT = Path(__file__).resolve().parents[1]
KEYS = ["student_id", "degree_id", "part_id"]
PASS_FAIL = ["P", "F", "FA", "FE"]  # src/clean_student_course.py FINISH_STATUS_MAP
SOURCES = {
    "status": "data/raw/v_add_student_degree_status.parquet",
    "courses": "data/raw/v_crg_student_course_raw.parquet",
    "plan": "data/raw/v_acd_degree_course.parquet",
    "grade": "data/raw/v_acs_grade.parquet",
}
RULES = {
    "scope": "part_id >= 20251; inclusive recorded load 12 through 18 credits",
    "registered_courses": "register_status in [R, E]; raw outcomes retained",
    "pass_fail_codes": PASS_FAIL,
    "pass_fail_definition_source": "src/clean_student_course.py:FINISH_STATUS_MAP",
    "candidate": "registered_credits_before_filter between 12 and 18; pass_fail_credits < 12, including zero",
    "before": "recorded semester_reg_credits, reconciled to the raw registered course sum",
    "after": "sum(course_credits) for finish_status in [P, F, FA, FE]",
    "known_status_reduction": "registered_credits_before_filter - known_non_pass_fail_credits < 12",
    "unknown_outcomes": "missing finish_status alone cannot establish a withdrawal or other status change",
    "graduation_exceptions": "start_level_name_short >= max active plan year_order OR recorded credits equal positive degree_credits_count - start_total_in_credits",
    "retained": "known status codes suffice to cross below 12, exact status matches, and neither graduation exception applies",
    "excluded": "known status codes suffice to cross below 12 and a graduation exception applies",
    "unresolved": "missing or inconsistent exact status, insufficient exception data, or missing outcomes needed to cross below 12",
    "temporal_limit": "Sources have no change timestamps; these are before/after outcome-filter credit totals, not proof of a dated registration reduction.",
    "output_grain": "one row per registered course with exact student-degree-semester status; all pass/fail and other courses preserved",
}


def count(frame):
    return {"student_semesters": len(frame), "unique_students": int(frame.student_id.nunique())}


def main():
    previous_paths = list(ROOT.glob("student_over_polict*.parquet"))
    previous_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in previous_paths}
    raw = {name: pd.read_parquet(ROOT / path) for name, path in SOURCES.items()}
    s = clean_id_columns(raw["status"], ["student_id", "student_status_id", "degree_id", "grade_version_id"])
    c = clean_id_columns(raw["courses"], ["student_id", "degree_id", "course_id", "student_course_id", "grade_id", "faculty_id"])
    d = clean_id_columns(raw["plan"], ["degree_id"])
    s["part_id"] = s.part_id.astype("Int64")
    c["part_id"] = c.part_id.astype("Int64")
    s = s.loc[s.part_id.ge(20251)].copy()
    c = c.loc[c.part_id.ge(20251) & c.register_status.str.strip().isin(["R", "E"])].copy()
    assert not s.duplicated(KEYS).any()
    assert not c.student_course_id.duplicated().any()
    assert not s[KEYS].isna().any().any()
    assert not c[KEYS + ["course_credits"]].isna().any().any()

    code = c.finish_status.astype("string").str.strip().str.upper().replace("", pd.NA)
    c["is_pass_fail"] = code.isin(PASS_FAIL)
    c["is_known_non_pass_fail"] = code.notna() & ~c.is_pass_fail
    c["is_missing_finish_status"] = code.isna()
    c["finish_status_code_for_audit"] = code.fillna("MISSING")
    grade_names = raw["grade"].dropna(subset=["finish_status", "grade_name_sl"]).groupby("finish_status").grade_name_sl.agg(lambda a: " | ".join(sorted(set(a))))
    c["finish_status_name_for_audit"] = code.map(grade_names)
    for flag, column in [("is_pass_fail", "pass_fail_course_credits"), ("is_known_non_pass_fail", "known_non_pass_fail_course_credits"), ("is_missing_finish_status", "missing_finish_status_course_credits")]:
        c[column] = c.course_credits.where(c[flag], 0)
    totals = c.groupby(KEYS).agg(
        course_registered_credits=("course_credits", "sum"),
        course_registered_count=("student_course_id", "size"),
        pass_fail_credits=("pass_fail_course_credits", "sum"),
        known_non_pass_fail_credits=("known_non_pass_fail_course_credits", "sum"),
        missing_finish_status_credits=("missing_finish_status_course_credits", "sum"),
        missing_finish_status_courses=("is_missing_finish_status", "sum"),
    ).reset_index()
    x = s.merge(totals, on=KEYS, how="outer", validate="one_to_one", indicator="source_match")
    x["registered_credits_before_filter"] = x.semester_reg_credits.combine_first(x.course_registered_credits)
    x = x.loc[x.registered_credits_before_filter.between(12, 18) & x.pass_fail_credits.lt(12)].copy()
    x["non_pass_fail_credits"] = x.known_non_pass_fail_credits + x.missing_finish_status_credits
    assert np.isclose(x.course_registered_credits, x.pass_fail_credits + x.non_pass_fail_credits, rtol=0, atol=1e-8).all()
    x["status_row_found"] = x.source_match.ne("right_only")
    x["registration_credit_match"] = np.isclose(x.semester_reg_credits, x.course_registered_credits, rtol=0, atol=1e-8)
    x["registration_count_match"] = x.semester_reg_courses.eq(x.course_registered_count)
    x["credits_after_known_status_exclusions"] = x.registered_credits_before_filter - x.known_non_pass_fail_credits
    x["known_statuses_suffice_for_below_12"] = x.credits_after_known_status_exclusions.lt(12)
    x["status_pass_fail_credits"] = x.semester_pass_credits + x.semester_fail_credits
    x["status_pass_fail_matches_course_codes"] = np.isclose(x.status_pass_fail_credits, x.pass_fail_credits, rtol=0, atol=1e-8)
    x["final_year_order"] = x.degree_id.map(d.loc[d.active.eq("A")].groupby("degree_id").year_order.max()).astype("Int64")
    year_known = x.start_level_name_short.gt(0) & x.final_year_order.gt(0)
    x["is_final_year_start"] = x.start_level_name_short.ge(x.final_year_order).astype("boolean").where(year_known)
    x["remaining_credits_start"] = x.degree_credits_count - x.start_total_in_credits
    remaining_known = x.degree_credits_count.gt(0) & x.start_total_in_credits.ge(0) & x.remaining_credits_start.ge(0)
    equal_remaining = x.remaining_credits_start.gt(0) & np.isclose(x.remaining_credits_start, x.registered_credits_before_filter, rtol=0, atol=1e-8)
    x["registered_all_remaining_credits"] = pd.Series(equal_remaining, index=x.index, dtype="boolean").where(remaining_known)
    exception = x.is_final_year_start | x.registered_all_remaining_credits
    reliable = x.status_row_found & x.registration_credit_match & x.registration_count_match & x.known_statuses_suffice_for_below_12
    x["classification"] = "unresolved"
    x.loc[reliable & exception.eq(False).fillna(False), "classification"] = "retained"
    x.loc[reliable & exception.eq(True).fillna(False), "classification"] = "excluded"
    x["reason"] = "known_non_pass_fail_statuses_reduce_filtered_credits_below_12"
    x.loc[x.classification.eq("excluded"), "reason"] = "requested_final_year_or_all_remaining_credits_exception"
    x.loc[x.classification.eq("unresolved"), "reason"] = "missing_outcomes_needed_or_insufficient_status_data"
    x.loc[~x.status_row_found, "reason"] = "missing_exact_student_degree_semester_status"
    x = x.sort_values(["part_id", "student_id", "degree_id"]).reset_index(drop=True)

    summary = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "rules": RULES, "sources": {}, "all_candidates": count(x), "cohorts": {}, "by_semester": []}
    for name, path in SOURCES.items():
        summary["sources"][name] = {"path": path, "rows": len(raw[name]), "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
    for part, term in x.groupby("part_id"):
        identified = term.loc[term.status_row_found & term.known_statuses_suffice_for_below_12]
        summary["by_semester"].append({
            "part_id": int(part), "all_candidates": count(term), "known_status_reduction_with_exact_status": count(identified),
            **{label: count(term.loc[term.classification.eq(label)]) for label in ["retained", "excluded", "unresolved"]},
            "retained_with_zero_pass_fail_credits": int((term.classification.eq("retained") & term.pass_fail_credits.eq(0)).sum()),
            "retained_with_positive_pass_fail_credits": int((term.classification.eq("retained") & term.pass_fail_credits.gt(0)).sum()),
        })
    outputs = {"retained": "student_under_12_after_status_change.parquet", "excluded": "student_under_12_after_status_change_excluded.parquet", "unresolved": "student_under_12_after_status_change_unresolved.parquet"}
    for label, filename in outputs.items():
        cohort = x.loc[x.classification.eq(label)].copy()
        detail = c.merge(cohort, on=KEYS, how="right", suffixes=("_course", "_status"), validate="many_to_one")
        detail = detail.sort_values(["part_id", "student_id", "degree_id", "student_course_id"]).reset_index(drop=True)
        table = pa.Table.from_pandas(detail, preserve_index=False)
        metadata = dict(table.schema.metadata or {})
        metadata[b"under_12_after_status_change_rules"] = json.dumps(RULES, ensure_ascii=False).encode("utf-8")
        metadata[b"generated_at_utc"] = summary["generated_at_utc"].encode("utf-8")
        pq.write_table(table.replace_schema_metadata(metadata), ROOT / filename, compression="snappy")
        restored = pd.read_parquet(ROOT / filename)
        pd.testing.assert_frame_equal(detail, restored)
        assert len(restored[KEYS].drop_duplicates()) == len(cohort)
        summary["cohorts"][label] = {**count(cohort), "course_rows": len(detail), "file": filename}
    assert sum(a["student_semesters"] for a in summary["cohorts"].values()) == len(x)
    retained = x.loc[x.classification.eq("retained")]
    assert retained.registered_credits_before_filter.between(12, 18).all()
    assert retained.pass_fail_credits.lt(12).all()
    assert retained.known_statuses_suffice_for_below_12.all()
    assert not retained.is_final_year_start.any()
    assert not retained.registered_all_remaining_credits.any()
    summary["retained_status_pass_fail_sum_disagrees_with_course_codes"] = int((~retained.status_pass_fail_matches_course_codes).sum())
    summary["known_non_pass_fail_codes_in_retained"] = c.merge(retained[KEYS], on=KEYS).loc[lambda a: a.is_known_non_pass_fail].groupby("finish_status_code_for_audit").agg(course_rows=("student_course_id", "size"), credits=("course_credits", "sum"), unique_students=("student_id", "nunique")).reset_index().to_dict("records")
    summary["unresolved_cases"] = x.loc[x.classification.eq("unresolved"), KEYS + ["registered_credits_before_filter", "pass_fail_credits", "known_non_pass_fail_credits", "missing_finish_status_credits", "reason"]].to_dict("records")
    assert previous_hashes == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in previous_paths}
    summary["previous_outputs_unchanged"] = previous_hashes
    summary["validation"] = "Unique composite status joins, reconciled registered credits/counts, conserved course credits, cohort partition, exception checks, and three Parquet read-back checks passed."
    (ROOT / "reports/under_12_after_status_change_scan.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ["all_candidates", "cohorts", "by_semester", "retained_status_pass_fail_sum_disagrees_with_course_codes", "known_non_pass_fail_codes_in_retained", "validation"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
