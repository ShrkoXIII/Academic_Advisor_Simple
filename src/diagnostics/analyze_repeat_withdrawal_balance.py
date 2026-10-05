"""Run an isolated, data-only repeat/withdrawal balance analysis into a NEW folder."""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.cleaning_utils import clean_column_names, clean_id_columns
from src.diagnostics.repeat_withdrawal_balance import (
    ATTEMPT_COLUMNS, STATUS_MAP, analyze_semesters, prepare_attempts, student_totals,
)
from src.diagnostics.repeat_withdrawal_report import (
    aggregate_outputs, outlier_outputs, policy_candidates, render_summary, write_json,
)
from src.paths import (
    PROJECT_ROOT, CLEAN_REGISTRATION_ROSTER_PATH_V2, STUDENT_COURSE_PATH, GRADE_SCALE_PATH,
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def protected_manifest():
    files = set(PROJECT_ROOT.glob("*.parquet"))
    for name in ["data", "models"]:
        files.update(p for p in (PROJECT_ROOT / name).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    files.update((PROJECT_ROOT / "src").rglob("*.py"))
    return {p.relative_to(PROJECT_ROOT).as_posix(): sha256(p) for p in sorted(files)}


def graph_navigation(path):
    """Read a user's existing graph; preserve a one-hop scoped traversal as evidence."""
    data = json.loads(path.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in data["nodes"]}
    links = data.get("links", data.get("edges", []))
    adjacency = {key: [] for key in nodes}
    for edge in links:
        a, b = edge["source"], edge["target"]
        if a in adjacency and b in adjacency:
            adjacency[a].append(b)
            adjacency[b].append(a)
    seeds = [key for key, node in nodes.items() if node.get("label") in [
        "build_registration_roster()", "build_registration_roster.py", "student_course_status.py",
        "clean_student_course.py", "paths.py", "previous_course_status_data.py",
    ]]
    visited = set(seeds)
    queue = deque((key, 0) for key in seeds)
    result = []
    while queue:
        key, depth = queue.popleft()
        node = nodes[key]
        result.append({name: node.get(name) for name in ["id", "label", "source_file", "source_location"]} | {"depth": depth})
        if depth == 0:
            for neighbor in adjacency[key]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, 1))
    return dict(graph_path=str(path), sha256=sha256(path), nodes=len(nodes), edges=len(links),
        expanded_tokens=["registration", "roster", "student", "course", "status", "previous", "grade", "temporal", "clean", "paths"],
        traversal="BFS depth 1 on actual graph seed labels; original graph read-only",
        scoped_nodes=result, scoped_edges=[edge for edge in links if edge["source"] in visited and edge["target"] in visited],
        interpretation="Graph sources omit src/ prefix; verify corresponding live files. Graph provides navigation, not current data statistics.")


def finish_status_inventory(frame):
    result = frame.assign(finish_status=frame.finish_status.fillna("__MISSING__")).groupby("finish_status").agg(
        count=("course_id", "size"), total_course_credits=("course_credits", "sum"), unique_students=("student_id", "nunique")).reset_index()
    result["percentage"] = 100 * result["count"] / len(frame)
    return result


def status_evidence(roster, raw, grades):
    result = finish_status_inventory(roster)
    meanings = {"F": "رسوب", "FE": "راسب امتحان نهائي", "FA": "محروم بالغياب؛ يصنفه الكود fail",
                "P": "نجاح حسب سلم الدرجة", "W": "منسحب", "D": "محروم؛ إذن إعادة الرسوب غير مثبت",
                "Z": "محروم من الامتحان؛ إذن إعادة الرسوب غير مثبت", "ST": "تدريب سريري علامته من الامتحان الوطني",
                "T": "معادل", "I": "غير مكتمل", "IP": "قيد الإنجاز"}
    all_codes = sorted(set(result.finish_status) | set(raw.finish_status.dropna()))
    result = result.set_index("finish_status").reindex(all_codes).reset_index()
    result[["count", "total_course_credits", "unique_students", "percentage"]] = result[["count", "total_course_credits", "unique_students", "percentage"]].fillna(0)
    result["semantic_category"] = result.finish_status.map(STATUS_MAP).fillna("UNRESOLVED")
    result.loc[result.finish_status.eq("__MISSING__"), "semantic_category"] = "UNKNOWN"
    result["verification"] = np.where(result.finish_status.isin(STATUS_MAP), "VERIFIED", "UNVERIFIED")
    result.loc[result.finish_status.eq("__MISSING__"), "verification"] = "MISSING"
    result["meaning"] = result.finish_status.map(meanings).fillna("معنى غير مثبت / قيمة مفقودة")
    for index, row in result.iterrows():
        grade_rows = grades[grades.finish_status.eq(row.finish_status)]
        result.loc[index, "grade_source_labels"] = " | ".join(sorted(grade_rows.grade_name_sl.dropna().unique()))
        result.loc[index, "grade_ids"] = " | ".join(sorted(grade_rows.grade_id.astype(str)))
        result.loc[index, "evidence_source"] = "data/raw/v_acs_grade.parquet; src/data/clean_student_course.py:16" if row.finish_status in ["F", "FE", "FA", "P"] else "data/raw/v_acs_grade.parquet"
    return result


def grade_range_disagreements(joined, grades, output):
    """Audit explicit F rows against their actual grade-id range, not a global cutoff."""
    lookup = clean_id_columns(grades, ["grade_id"])
    lookup = lookup.reindex(columns=["grade_id", "grade_version_id", "from_percent", "to_percent"])
    matched = joined.merge(lookup, on="grade_id", how="left", validate="many_to_one")
    conflict = matched.finish_status.eq("F") & pd.to_numeric(matched.final_mark, errors="coerce").gt(pd.to_numeric(matched.to_percent, errors="coerce"))
    result = matched[conflict].groupby(["grade_id", "grade_version_id", "from_percent", "to_percent"], dropna=False).agg(
        count=("course_id", "size"), mark_min=("final_mark", "min"), mark_max=("final_mark", "max")).reset_index()
    result.to_csv(output / "grade_range_disagreements.csv", index=False)
    return result


def nonstandard_history_sensitivity(cases, target, candidates, output):
    """Keep the official calendar primary; quantify old numeric-part-4 uncertainty."""
    part = pd.to_numeric(candidates.part_id, errors="coerce")
    credit = pd.to_numeric(candidates.course_credits, errors="coerce")
    usable = part.notna() & part.eq(np.floor(part)) & part.between(10000, 99999)
    usable &= candidates[["student_course_id", "student_id", "degree_id", "course_id"]].notna().all(axis=1)
    usable &= np.isfinite(credit) & credit.ge(0)
    nonstandard = usable & ~part.mod(10).isin([1, 2, 3])
    affected = candidates.loc[nonstandard, "student_id"].unique()
    result = dict(interpretation="Sensitivity only: numeric ordering of otherwise nonstandard older parts. No calendar semantics inferred.",
        source_rows=int(nonstandard.sum()), affected_students=len(affected),
        excluded_part_counts={str(int(key)): int(value) for key, value in part[nonstandard].value_counts().items()})
    combined = cases.copy()
    columns = ["available_failed_credits", "available_withdrawn_credits", "registered_failed_retake_credits", "registered_withdrawn_retake_credits", "registered_new_credits"]
    if len(affected):
        subset = target[target.student_id.isin(affected)]
        expanded = candidates[usable & candidates.student_id.isin(affected)]
        sensitivity, _ = analyze_semesters(subset, expanded, allow_nonstandard_history=True)
        before = cases[cases.student_id.isin(affected)]
        keys = ["student_id", "target_part"]
        comparison = before[keys + columns].merge(sensitivity[keys + columns], on=keys,
            suffixes=("_primary", "_numeric_sensitivity"), validate="one_to_one")
        comparison.to_csv(output / "nonstandard_part_sensitivity_cases.csv", index=False)
        summaries = []
        for column in columns:
            a, b = comparison[f"{column}_primary"], comparison[f"{column}_numeric_sensitivity"]
            summaries.append(dict(metric=column, changed_cases=int((~np.isclose(a, b)).sum()),
                                  primary_total=float(a.sum()), numeric_sensitivity_total=float(b.sum())))
        pd.DataFrame(summaries).to_csv(output / "nonstandard_part_sensitivity_summary.csv", index=False)
        index = combined.set_index(keys)
        replacement = sensitivity.set_index(keys)
        index.loc[replacement.index, replacement.columns] = replacement
        combined = index.reset_index()
        result["changed_registered_cases"] = int((~np.isclose(comparison.registered_new_credits_primary, comparison.registered_new_credits_numeric_sensitivity)).sum())
        result["student_semesters_recomputed"] = len(sensitivity)
    else:
        pd.DataFrame(columns=["metric", "changed_cases", "primary_total", "numeric_sensitivity_total"]).to_csv(output / "nonstandard_part_sensitivity_summary.csv", index=False)
        result["changed_registered_cases"] = 0
        result["student_semesters_recomputed"] = 0
    result["primary_policy"] = policy_candidates(cases)
    result["numeric_part_sensitivity_policy"] = policy_candidates(combined)
    write_json(output / "nonstandard_part_policy_sensitivity.json", result)
    return result


def run(output, graph_path):
    output = output.resolve()
    if output.exists():
        raise FileExistsError("Use a NEW output directory; existing reports are never overwritten")
    if not output.is_relative_to(PROJECT_ROOT / "reports"):
        raise ValueError("Analysis outputs must stay in a new reports/ directory")
    navigation = graph_navigation(graph_path.resolve())
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("student_history.csv\nstudent_semester_mix.csv\nregistration_classification.parquet\noutlier_cases.csv\ncredit_change_cases.csv\nwindow_sensitivity_cases.csv\nnonstandard_part_sensitivity_cases.csv\n", encoding="utf-8")
    write_json(output / "graph_navigation.json", navigation)
    print("Hashing protected inputs/models/source...", flush=True)
    before = protected_manifest()
    write_json(output / "protected_before_sha256.json", before)
    roster = pd.read_parquet(CLEAN_REGISTRATION_ROSTER_PATH_V2)
    inventory = finish_status_inventory(roster)
    inventory.to_csv(output / "finish_status_inventory.csv", index=False)
    print("Finish status inventory BEFORE semantic mapping:\n" + inventory.to_string(index=False), flush=True)
    raw = clean_column_names(pd.read_parquet(STUDENT_COURSE_PATH))
    raw = clean_id_columns(raw, ["student_course_id", "student_id", "course_id", "degree_id", "grade_id"])
    for column in ["register_status", "finish_status"]:
        raw[column] = raw[column].astype("string").str.strip().str.upper().replace("", pd.NA)
    grades = clean_column_names(pd.read_parquet(GRADE_SCALE_PATH))
    # Verify the withdrawal definition from the actual grade lookup, not mark zero.
    if not grades.loc[grades.finish_status.eq("W"), "grade_name_sl"].eq("منسحب").any():
        raise ValueError("Withdrawal code W no longer verified by the grade source")
    mapping = status_evidence(roster, raw, grades)
    mapping.to_csv(output / "finish_status_mapping.csv", index=False)
    grades.to_csv(output / "grade_status_evidence.csv", index=False)
    target, exact_duplicates = prepare_attempts(roster)
    candidates = raw[raw.register_status.isin(["R", "E"]) & raw.student_id.isin(target.student_id)].copy()
    numeric_part = pd.to_numeric(candidates.part_id, errors="coerce")
    valid_part = numeric_part.notna() & numeric_part.eq(np.floor(numeric_part)) & numeric_part.between(10000, 99999) & numeric_part.mod(10).isin([1, 2, 3])
    valid_keys = candidates[["student_course_id", "student_id", "degree_id", "course_id"]].notna().all(axis=1)
    valid_credits = pd.to_numeric(candidates.course_credits, errors="coerce")
    usable = valid_part & valid_keys & np.isfinite(valid_credits) & valid_credits.ge(0)
    issues = [dict(issue="raw_history_unusable_temporal_or_course_key_or_credits", affected_rows=int((~usable).sum()),
        affected_students=int(candidates.loc[~usable, "student_id"].nunique()), assessment="Reported exclusion in analysis copy only; source retained. Unknown history may remain.")]
    history, raw_duplicates = prepare_attempts(candidates[usable])
    source_keys = raw[["student_course_id", "student_id", "degree_id", "course_id", "part_id", "course_credits", "register_status", "finish_status", "final_mark", "points", "grade_id"]]
    if source_keys.student_course_id.duplicated().any():
        raise ValueError("Raw source student_course_id is not unique")
    joined = target.merge(source_keys, on="student_course_id", how="left", validate="one_to_one", suffixes=("", "_raw"), indicator=True)
    if not joined._merge.eq("both").all():
        raise ValueError("Roster registrations do not all match the raw source")
    for column in ["student_id", "degree_id", "course_id", "register_status"]:
        if not joined[column].eq(joined[f"{column}_raw"]).all():
            raise ValueError(f"Roster/raw mismatch: {column}")
    if not joined.part_id.eq(pd.to_numeric(joined.part_id_raw)).all() or not np.allclose(joined.course_credits, pd.to_numeric(joined.course_credits_raw)):
        raise ValueError("Roster/raw semester or credit mismatch")
    if not joined.finish_status.fillna("__MISSING__").eq(joined.finish_status_raw.fillna("__MISSING__")).all():
        raise ValueError("Roster/raw outcome mismatch")
    crosscheck = joined.assign(finish_status=joined.finish_status.fillna("__MISSING__")).groupby("finish_status").agg(
        rows=("course_id", "size"), mark_min=("final_mark", "min"), mark_max=("final_mark", "max"),
        missing_marks=("final_mark", lambda v: v.isna().sum()),
        marks_ge50=("final_mark", lambda v: pd.to_numeric(v).ge(50).sum()),
        positive_points=("points", lambda v: pd.to_numeric(v).gt(0).sum())).reset_index()
    crosscheck.to_csv(output / "status_mark_crosscheck.csv", index=False)
    grade_conflicts = grade_range_disagreements(joined, grades, output)
    print("Computing strictly prior snapshots from raw R/E histories...", flush=True)
    cases, audit = analyze_semesters(target, history)
    audit.to_parquet(output / "registration_classification.parquet", index=False)
    students = student_totals(target)
    distributions, mixes, common, probabilities, policies = aggregate_outputs(cases, students, output)
    outliers = outlier_outputs(cases, audit, output)
    print("Computing roster-window sensitivity...", flush=True)
    window_cases, window_audit = analyze_semesters(target, target)
    columns = ["student_id", "target_part", "available_failed_credits", "available_withdrawn_credits", "registered_failed_retake_credits", "registered_withdrawn_retake_credits", "registered_new_credits"]
    compare = cases[columns].merge(window_cases[columns], on=["student_id", "target_part"], suffixes=("_raw_history", "_roster_history"), validate="one_to_one")
    compare.to_csv(output / "window_sensitivity_cases.csv", index=False)
    sensitivity = []
    for column in columns[2:]:
        a, b = compare[f"{column}_raw_history"], compare[f"{column}_roster_history"]
        sensitivity.append(dict(metric=column, changed_cases=int((~np.isclose(a, b)).sum()), raw_history_median=float(a.median()), roster_history_median=float(b.median()), raw_history_total=float(a.sum()), roster_history_total=float(b.sum())))
    pd.DataFrame(sensitivity).to_csv(output / "window_sensitivity_summary.csv", index=False)
    print("Computing nonstandard older-part sensitivity...", flush=True)
    calendar_sensitivity = nonstandard_history_sensitivity(cases, target, candidates, output)
    correction = window_audit.previous_status.eq("NEVER_TAKEN") & audit.previous_status.ne("NEVER_TAKEN")
    credit_changes = audit.previous_course_credits.notna() & ~np.isclose(audit.course_credits, audit.previous_course_credits.fillna(audit.course_credits))
    cross_degree = audit.previous_degree_id.notna() & audit.previous_degree_id.ne(audit.degree_id)
    issues += [
        dict(issue="exact_duplicate_roster_rows", affected_rows=exact_duplicates, assessment="Deduplicated in analysis copy only"),
        dict(issue="exact_duplicate_raw_R_E_rows", affected_rows=raw_duplicates, assessment="Deduplicated in analysis copy only"),
        dict(issue="ambiguous_same_part_course_attempts", affected_rows=0, assessment="Validation passed; conflicts would stop analysis"),
        dict(issue="roster_window_new_corrected_by_raw_history", affected_rows=int(correction.sum()), assessment="Primary analysis uses raw earlier registrations; roster-window sensitivity saved"),
        dict(issue="repeat_credit_amount_changed", affected_rows=int(credit_changes.sum()), assessment="Prior credits for available; current credits for registered; no capping"),
        dict(issue="previous_attempt_in_different_degree", affected_rows=int(cross_degree.sum()), assessment="Latest student+course contract spans degrees; eligibility/credit transfer unverified"),
        dict(issue="zero_credit_registrations", affected_rows=int(target.course_credits.eq(0).sum()), assessment="Retained; undefined zero-load ratios remain NA"),
        dict(issue="24_credit_course_registrations", affected_rows=int(target.course_credits.ge(24).sum()), assessment="Retained; unusual institutional credit convention unverified"),
        dict(issue="unverified_status_in_raw_R_E_history", affected_rows=int((history.semantic_status.eq("UNRESOLVED") & ~history.finish_status.isin(["I", "IP"])).sum()), assessment="Never assigned Failed/Withdrawn/New from a mark"),
        dict(issue="missing_finish_status_in_20253", affected_rows=int(target.loc[target.part_id.eq(20253), "finish_status"].isna().sum()), assessment="Current target outcome never used for its own classification"),
        dict(issue="F_mark_above_its_grade_id_failure_range", affected_rows=int(grade_conflicts['count'].sum()), assessment="Source inconsistency; explicit F preserved, marks never override status"),
    ]
    issue_frame = pd.concat([pd.DataFrame(issues), outliers], ignore_index=True)
    issue_frame.to_csv(output / "data_quality_issues.csv", index=False)
    metadata = dict(roster_path=str(CLEAN_REGISTRATION_ROSTER_PATH_V2), raw_path=str(STUDENT_COURSE_PATH),
        grade_path=str(GRADE_SCALE_PATH), graph_path=str(graph_path.resolve()),
        roster_rows=len(target), roster_students=target.student_id.nunique(), student_semesters=len(cases),
        target_parts=sorted(target.part_id.unique().tolist()), raw_R_E_history_rows=len(history),
        raw_pre_window_rows=int(history.part_id.lt(target.part_id.min()).sum()),
        first_raw_part=int(history.part_id.min()), raw_latest_part=int(history.part_id.max()),
        roster_raw_join_matched_rows=len(joined), all_roster_source_fields_reconcile=True,
        history_semantics="Latest student+course, strictly part<T, raw R/E from same roster cohort; no within-semester outcomes or attempt_number",
        classifications_partition_courses_and_credits=True, zero_total_credit_semesters=int(cases.semester_total_registered_credits.eq(0).sum()),
        duplicate_conflicts=0, roster_new_corrected_by_raw=int(correction.sum()),
        raw_unusable_by_reason={"invalid_part": int((~valid_part).sum()), "invalid_keys": int((~valid_keys).sum()), "invalid_credits": int((~(np.isfinite(valid_credits) & valid_credits.ge(0))).sum())},
        nonstandard_part_sensitivity={key: calendar_sensitivity[key] for key in ["source_rows", "affected_students", "excluded_part_counts", "changed_registered_cases"]},
        policy_requires_backlog=True, policy_outcome="Descriptive candidate only; formal eligibility and causal benefit INSUFFICIENT EVIDENCE",
        publication_time_evidence="Unavailable: prior finalized state at beginning of T not recoverable from final snapshot")
    write_json(output / "analysis_metadata.json", metadata)
    render_summary(output, cases, mapping, distributions, mixes, common, probabilities, policies, metadata, issue_frame)
    print("Verifying protected files after analysis...", flush=True)
    after = protected_manifest()
    write_json(output / "protected_after_sha256.json", after)
    changed = sorted(key for key in before if before[key] != after.get(key))
    added = sorted(set(after) - set(before))
    integrity = dict(protected_files=len(before), changed=changed, added=added, unchanged=not changed and not added)
    write_json(output / "artifact_integrity.json", integrity)
    if changed or added:
        raise AssertionError("Protected artifact/source files changed during analysis")
    print(json.dumps(dict(students=int(target.student_id.nunique()), student_semesters=len(cases),
        conditional_probabilities=probabilities.to_dict("records"), policy_candidates=policies,
        integrity=integrity, output=str(output)), ensure_ascii=True, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "reports/repeat_withdrawal_analysis")
    parser.add_argument("--graph", type=Path, required=True, help="Existing graph.json; read-only navigation")
    args = parser.parse_args()
    run(args.output_dir, args.graph)


if __name__ == "__main__":
    main()
