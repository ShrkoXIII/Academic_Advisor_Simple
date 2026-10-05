"""Pure, retrospective registration analysis. No model or serving imports."""
import numpy as np
import pandas as pd

from src.data.cleaning_utils import clean_column_names, clean_id_columns


STATUS_MAP = {
    "F": "FAILED", "FE": "FAILED", "FA": "FAILED", "P": "PASSED",
    "W": "WITHDRAWN", "D": "OTHER", "Z": "OTHER", "ST": "OTHER",
    "T": "OTHER", "I": "UNRESOLVED", "IP": "UNRESOLVED",
}
ATTEMPT_COLUMNS = ["student_course_id", "student_id", "degree_id", "course_id",
                   "part_id", "course_credits", "register_status", "finish_status"]
CATEGORIES = ["FAILED", "WITHDRAWN", "PASSED", "OTHER", "UNRESOLVED", "UNKNOWN"]


def semantic_status(values):
    """Use verified source codes; never infer failure/withdrawal from a zero mark."""
    values = values.astype("string").str.strip().str.upper().replace("", pd.NA)
    return values.map(STATUS_MAP).fillna("UNRESOLVED").mask(values.isna(), "UNKNOWN")


def prepare_attempts(frame, *, allow_nonstandard_parts=False):
    """Normalize a copy, report exact duplicates, reject ambiguous temporal keys."""
    result = clean_column_names(frame)[ATTEMPT_COLUMNS].copy()
    result = clean_id_columns(result, ["student_course_id", "student_id", "degree_id", "course_id"])
    for column in ["register_status", "finish_status"]:
        result[column] = result[column].astype("string").str.strip().str.upper().replace("", pd.NA)
    if result[["student_id", "course_id", "student_course_id", "degree_id"]].isna().any().any():
        raise ValueError("Missing attempt identifiers")
    part = pd.to_numeric(result.part_id, errors="raise")
    valid = part.eq(np.floor(part)) & part.between(10000, 99999)
    if not allow_nonstandard_parts:
        valid &= part.mod(10).isin([1, 2, 3])
    if part.isna().any() or not valid.all():
        raise ValueError("Invalid academic part")
    result["part_id"] = part.astype("int64")
    credits = pd.to_numeric(result.course_credits, errors="raise").astype(float)
    if not (np.isfinite(credits) & credits.ge(0)).all():
        raise ValueError("Invalid course credits")
    result["course_credits"] = credits
    duplicate_count = int(result.duplicated().sum())
    result = result.drop_duplicates().reset_index(drop=True)
    if result.student_course_id.duplicated().any() or result.duplicated(["student_id", "course_id", "part_id"]).any():
        raise ValueError("Ambiguous same-part attempts; no reliable within-part sequence")
    result["semantic_status"] = semantic_status(result.finish_status)
    return result, duplicate_count


def student_totals(attempts):
    """Count historical registration attempts within the roster observation window."""
    frame, _ = prepare_attempts(attempts)
    group = frame.groupby("student_id", sort=True)
    result = group.course_credits.sum().rename("total_attempted_credits").to_frame()
    for category in CATEGORIES:
        subset = frame[frame.semantic_status.eq(category)].groupby("student_id")
        label = category.lower()
        result[f"{label}_course_count"] = subset.size().reindex(result.index, fill_value=0)
        result[f"{label}_credits"] = subset.course_credits.sum().reindex(result.index, fill_value=0)
    for label in ["failed", "withdrawn"]:
        result[f"{label}_credit_ratio"] = result[f"{label}_credits"] / result.total_attempted_credits.replace(0, np.nan)
    return result.reset_index()


def analyze_semesters(roster, history, *, allow_nonstandard_history=False):
    """Snapshot latest (student, course) attempts at part<T, then read T registrations.

    Availability means historical unresolved backlog, not current offer/permission.
    Prior credits describe the latest prior attempt; registered credits describe T.
    Histories span degrees per the student+course contract. Current degrees are
    retained separately for audit. Zero-credit registrations still count as courses.
    """
    target, _ = prepare_attempts(roster)
    prior, _ = prepare_attempts(history, allow_nonstandard_parts=allow_nonstandard_history)
    histories = {student: list(group.sort_values(["part_id", "course_id"]).itertuples(index=False))
                 for student, group in prior.groupby("student_id", sort=False)}
    cases, audit = [], []
    for student, semesters in target.groupby("student_id", sort=True):
        attempts = histories.get(student, [])
        pointer, latest = 0, {}
        for part, registrations in semesters.groupby("part_id", sort=True):
            while pointer < len(attempts) and attempts[pointer].part_id < part:
                attempt = attempts[pointer]
                latest[attempt.course_id] = attempt
                pointer += 1
            case = dict(student_id=student, target_part=int(part),
                        degree_id="|".join(sorted(registrations.degree_id.unique())),
                        degree_count=int(registrations.degree_id.nunique()),
                        semester_total_registered_courses=len(registrations),
                        semester_total_registered_credits=float(registrations.course_credits.sum()),
                        zero_credit_courses=int(registrations.course_credits.eq(0).sum()),
                        max_course_credits=float(registrations.course_credits.max()))
            for label, category in [("failed", "FAILED"), ("withdrawn", "WITHDRAWN")]:
                backlog = [a for a in latest.values() if a.semantic_status == category]
                case[f"available_{label}_courses"] = len(backlog)
                case[f"available_{label}_credits"] = sum(a.course_credits for a in backlog)
            case["available_other_previous_courses"] = sum(a.semantic_status not in ["FAILED", "WITHDRAWN", "PASSED"] for a in latest.values())
            for label in ["failed_retake", "withdrawn_retake", "new", "other_previous"]:
                case[f"registered_{label}_courses"] = 0
                case[f"registered_{label}_credits"] = 0.0
            for row in registrations.itertuples(index=False):
                old = latest.get(row.course_id)
                status = old.semantic_status if old else "NEVER_TAKEN"
                label = {"FAILED": "failed_retake", "WITHDRAWN": "withdrawn_retake", "NEVER_TAKEN": "new"}.get(status, "other_previous")
                case[f"registered_{label}_courses"] += 1
                case[f"registered_{label}_credits"] += row.course_credits
                audit.append(dict(student_id=student, degree_id=row.degree_id,
                                  course_id=row.course_id, student_course_id=row.student_course_id,
                                  target_part=int(part), course_credits=row.course_credits,
                                  previous_status=status, previous_part_id=old.part_id if old else None,
                                  previous_course_credits=old.course_credits if old else None,
                                  previous_degree_id=old.degree_id if old else None))
            total = case["semester_total_registered_credits"]
            for label in ["failed_retake", "withdrawn_retake", "new", "other_previous"]:
                case[f"{label}_ratio" if label != "new" else "new_credit_ratio"] = case[f"registered_{label}_credits"] / total if total else np.nan
            case["previously_attempted_ratio"] = (case["registered_failed_retake_credits"] + case["registered_withdrawn_retake_credits"]) / total if total else np.nan
            for label in ["failed", "withdrawn"]:
                available = case[f"available_{label}_credits"]
                case[f"{label}_backlog_consumption_ratio"] = case[f"registered_{label}_retake_credits"] / available if available else np.nan
            f, w, n, o = [case[f"registered_{label}_courses"] > 0 for label in ["failed_retake", "withdrawn_retake", "new", "other_previous"]]
            case["mix_type"] = {
                (False, False, True): "NEW_ONLY", (True, False, False): "FAILED_RETAKE_ONLY",
                (False, True, False): "WITHDRAWN_RETAKE_ONLY", (True, False, True): "FAILED_AND_NEW",
                (False, True, True): "WITHDRAWN_AND_NEW", (True, True, True): "FAILED_WITHDRAWN_AND_NEW",
            }.get((f, w, n), "OTHER") if not o else "OTHER"
            case["load_bucket"] = "<=12" if total <= 12 else "(12,15]" if total <= 15 else "(15,18]" if total <= 18 else ">18"
            case["part_type"] = "part_3" if int(part) % 10 == 3 else "parts_1_2"
            cases.append(case)
    result, classified = pd.DataFrame(cases), pd.DataFrame(audit)
    if not result.empty:
        pieces = result[[f"registered_{label}_credits" for label in ["failed_retake", "withdrawn_retake", "new", "other_previous"]]].sum(axis=1)
        if not np.allclose(pieces, result.semester_total_registered_credits):
            raise AssertionError("Credit partition does not reconcile")
        count = result[[f"registered_{label}_courses" for label in ["failed_retake", "withdrawn_retake", "new", "other_previous"]]].sum(axis=1)
        if not count.eq(result.semester_total_registered_courses).all():
            raise AssertionError("Course partition does not reconcile")
        if not classified.loc[classified.previous_part_id.notna(), "previous_part_id"].lt(classified.loc[classified.previous_part_id.notna(), "target_part"]).all():
            raise AssertionError("Temporal leakage")
    return result, classified


def describe_metrics(frame, columns, cohort="all"):
    output = []
    for column in columns:
        values = frame[column].dropna().astype(float)
        row = dict(cohort=cohort, metric=column, sample_count=len(values),
                   missing_count=int(frame[column].isna().sum()),
                   mean=values.mean(), std=values.std(), min=values.min(), max=values.max(),
                   zero_percentage=100 * values.eq(0).mean())
        row.update({name: values.quantile(q) for name, q in [
            ("p10", .1), ("p25", .25), ("median", .5), ("p75", .75), ("p90", .9), ("p95", .95)]})
        output.append(row)
    return pd.DataFrame(output)


def credit_bins(values):
    """Exact requested credit amounts plus explicit remainder; decimals preserved."""
    series = values.dropna().astype(float)
    groups = {"0": series.eq(0), "3": series.eq(3), "6": series.eq(6),
              "9": series.eq(9), "12+": series.ge(12),
              "OTHER (<12)": series.lt(12) & ~series.isin([0, 3, 6, 9])}
    return pd.DataFrame([dict(bucket=key, count=int(mask.sum()), percentage=100 * mask.mean())
                         for key, mask in groups.items()])
