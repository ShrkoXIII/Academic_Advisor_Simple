"""Observed distributions and paired prediction evidence for the fixed experiment."""
import numpy as np
import pandas as pd

from src.evaluation.evaluate_plan_gpa import summarize_plan_errors
from src.grade_scale import GradeScale
from src.modeling import train_models as official
from src.paths import CLEAN_STUDENT_COURSE_PATH_V2, GRADE_SCALE_PATH
from .attempt_number_core import OUTPUT_DIR, VARIANTS, paired_cluster_interval, write_json


def subsets(frame):
    attempt = frame.attempt_number
    return {"overall": np.ones(len(frame), dtype=bool), "first": attempt.eq(1),
            "repeat": attempt.gt(1), "second": attempt.eq(2), "third_plus": attempt.ge(3),
            "third": attempt.eq(3), "fourth_plus": attempt.ge(4)}


def distribution(values):
    values = np.asarray(values, dtype=float)
    return {"mean": float(values.mean()), "median": float(np.median(values)),
            "p95": float(np.quantile(values, .95)), "p99": float(np.quantile(values, .99)),
            "max": float(values.max())}


def save_table(name, records):
    frame = pd.DataFrame(records)
    frame.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
    return frame


def descriptive_analysis(train, test):
    cohorts = {"train": train, "20251": test[test.part_id.eq(20251)],
               "20252": test[test.part_id.eq(20252)], "holdout": test,
               "all_modeling": pd.concat([train, test], ignore_index=True)}
    dist, shift, outcome, summaries = [], [], [], {}
    for name, frame in cohorts.items():
        for label, mask in [(str(a), frame.attempt_number.eq(a)) for a in [1, 2, 3, 4]] + [("5+", frame.attempt_number.ge(5))]:
            part = frame.loc[mask]
            dist.append({"cohort": name, "attempt": label, "rows": len(part),
                         "percent": 100 * len(part) / len(frame), "students": part.student_id.nunique(),
                         "courses": part.course_id.nunique()})
        summaries[name] = {"rows": len(frame), "students": frame.student_id.nunique(),
                           "courses": frame.course_id.nunique(), **distribution(frame.attempt_number),
                           "first_percent": 100 * frame.attempt_number.eq(1).mean(),
                           "repeat_percent": 100 * frame.attempt_number.gt(1).mean(),
                           "third_plus_rows": int(frame.attempt_number.ge(3).sum()),
                           "repeat_students": frame.loc[frame.attempt_number.gt(1)].student_id.nunique(),
                           "repeat_courses": frame.loc[frame.attempt_number.gt(1)].course_id.nunique()}
        for label, mask in subsets(frame).items():
            part = frame.loc[mask]
            outcome.append({"cohort": name, "subset": label, "rows": len(part),
                            "students": part.student_id.nunique(), "mean_final_mark": float(part.final_mark.mean()),
                            "mean_points": float(part.points.mean()), "fail_rate": float(part.is_fail.mean())})
    for part_id, part in pd.concat([train, test]).groupby("part_id"):
        shift.append({"part_id": part_id, "rows": len(part),
                      "first_percent": 100 * part.attempt_number.eq(1).mean(),
                      "repeat_percent": 100 * part.attempt_number.gt(1).mean(),
                      "third_plus_percent": 100 * part.attempt_number.ge(3).mean()})
    save_table("distribution", dist)
    save_table("outcomes", outcome)
    save_table("distribution_shift", shift)
    write_json(OUTPUT_DIR / "distribution_summary.json", summaries)

    features = ["course_history_avg_attempt", "course_history_retake_rate",
                "prior_total_fail_courses", "prior_total_fail_credits", "prior_fail_credit_ratio"]
    overlap = []
    for feature in features:
        pair = train[["attempt_number", feature]].dropna().astype(float)
        overlap.append({"feature": feature, "paired_rows": len(pair),
                        "pearson": pair.corr().iloc[0, 1], "spearman": pair.corr(method="spearman").iloc[0, 1],
                        "first_mean": float(train.loc[train.attempt_number.eq(1), feature].mean()),
                        "repeat_mean": float(train.loc[train.attempt_number.gt(1), feature].mean())})
    save_table("feature_overlap", overlap)
    grouped = train.groupby(["degree_id", "course_id", "part_id"], sort=False)
    variation = grouped[["attempt_number", *features[:2]]].nunique(dropna=False)
    mixed = variation.attempt_number.gt(1)
    report = {"course_degree_part_groups": len(variation), "mixed_personal_attempt_groups": int(mixed.sum()),
              "mixed_groups_with_identical_course_retry_aggregates": int((mixed & variation[features[0]].eq(1) & variation[features[1]].eq(1)).sum()),
              "rows_in_mixed_groups": int(grouped.size().loc[mixed].sum())}
    work = train.assign(fail_history_bin=pd.cut(train.prior_total_fail_courses,
                         [-1, 0, 4, 9, np.inf], labels=["0", "1-4", "5-9", "10+"]).astype("string").fillna("unknown"),
                        personal_group=np.where(train.attempt_number.eq(1), "first", "repeat"))
    stratified = work.groupby(["fail_history_bin", "personal_group"], observed=True).agg(
        rows=("is_fail", "size"), mean_mark=("final_mark", "mean"), fail_rate=("is_fail", "mean")).reset_index()
    stratified.to_csv(OUTPUT_DIR / "overlap_fail_history_strata.csv", index=False)
    cells = work.groupby(["degree_id", "course_id", "part_id", "fail_history_bin", "personal_group"], observed=True).agg(
        rows=("is_fail", "size"), mean_mark=("final_mark", "mean"), fail_rate=("is_fail", "mean")).reset_index()
    cell_keys = ["degree_id", "course_id", "part_id", "fail_history_bin"]
    paired = cells[cells.personal_group.eq("first")].merge(cells[cells.personal_group.eq("repeat")], on=cell_keys, suffixes=("_first", "_repeat"))
    paired = paired[paired.rows_first.ge(10) & paired.rows_repeat.ge(10)]
    if len(paired):
        weights = np.minimum(paired.rows_first, paired.rows_repeat)
        report.update({"matched_cells_min10_each": len(paired),
                       "matched_first_rows": int(paired.rows_first.sum()), "matched_repeat_rows": int(paired.rows_repeat.sum()),
                       "weighted_repeat_minus_first_mark": float(np.average(paired.mean_mark_repeat - paired.mean_mark_first, weights=weights)),
                       "weighted_repeat_minus_first_fail_rate": float(np.average(paired.fail_rate_repeat - paired.fail_rate_first, weights=weights))})
    write_json(OUTPUT_DIR / "overlap_structure.json", report)

    history = pd.read_parquet(CLEAN_STUDENT_COURSE_PATH_V2)
    history = history.sort_values(["student_id", "course_id", "part_id"], kind="stable")
    # Vectorized prior cumulative maximum avoids Python work for every course key.
    cumulative = history.groupby(["student_id", "course_id"], sort=False).attempt_number.cummax()
    prior_max = cumulative.groupby([history.student_id, history.course_id], sort=False).shift()
    history["serving_attempt"] = prior_max.fillna(0).astype(int) + 1
    joined = pd.concat([train, test]).merge(history[["student_course_id", "serving_attempt"]], on="student_course_id", validate="one_to_one")
    joined["mismatch"] = joined.attempt_number.ne(joined.serving_attempt)
    degree_counts = history.groupby(["student_id", "course_id"]).degree_id.nunique()
    mismatches = joined[joined.mismatch]
    mismatches[["student_course_id", "part_id", "attempt_number", "serving_attempt"]].to_parquet(OUTPUT_DIR / "serving_semantics_mismatches.parquet", index=False)
    write_json(OUTPUT_DIR / "semantics_audit.json", {
        "model_rows_joined": len(joined), "serving_attempt_mismatch_rows": len(mismatches),
        "mismatch_by_part": {str(k): int(v) for k, v in joined.groupby("part_id").mismatch.sum().items()},
        "cross_degree_student_course_keys_in_clean_history": int(degree_counts.gt(1).sum()),
        "clean_history_max_attempt": int(history.attempt_number.max()),
        "model_outcome_code_vs_mark_disagreement": int(pd.concat([train, test]).course_outcome_status.eq("fail").ne(pd.concat([train, test]).is_fail.astype(bool)).sum())})


def evaluate_predictions():
    scale = GradeScale.from_parquet(GRADE_SCALE_PATH)
    metrics, calibration, gaps, intervals, plans = [], [], [], [], []
    sources = [(path.parent.name, path) for path in sorted(OUTPUT_DIR.glob("*/predictions.parquet"))]
    for split, path in sources:
        frame = pd.read_parquet(path)
        for variant in VARIANTS:
            frame[f"points_{variant}"], _ = scale.convert(frame[f"grade_{variant}"], frame.grade_version_id)
        frame.to_parquet(path, index=False)
        cohorts = {split: frame}
        if split == "holdout":
            cohorts.update({str(part): frame[frame.part_id.eq(part)] for part in [20251, 20252]})
        for cohort, rows in cohorts.items():
            for subset, mask in subsets(rows).items():
                part = rows.loc[mask]
                if part.empty:
                    continue
                for variant in VARIANTS:
                    grade, fail, points = (part[f"{task}_{variant}"].to_numpy() for task in ["grade", "fail", "points"])
                    classification = official.classification_metrics(part.is_fail, fail) if part.is_fail.nunique() == 2 else {"roc_auc": None}
                    point_error = points - part.points.to_numpy(dtype=float)
                    metrics.append({"cohort": cohort, "subset": subset, "variant": variant,
                                    "rows": len(part), "students": part.student_id.nunique(),
                                    **official.regression_metrics(part.final_mark, grade), **classification,
                                    "points_mae": float(np.abs(point_error).mean()),
                                    "points_rmse": float(np.sqrt(np.square(point_error).mean()))})
                    calibration.append({"cohort": cohort, "subset": subset, "variant": variant,
                                        "rows": len(part), "mean_predicted_fail": float(fail.mean()),
                                        "actual_fail_rate": float(part.is_fail.mean()),
                                        "prediction_minus_actual": float(fail.mean() - part.is_fail.mean())})
                    for bin_row in official.calibration_table(part.is_fail, fail):
                        bin_row.update(cohort=cohort, subset=subset, variant=variant)
                        # Separate bin table retains the exact official calibration algorithm.
                        plans.append(bin_row)
                if split == "holdout":
                    for variant in ["B", "C"]:
                        for task in ["grade", "points", "fail"]:
                            diff = np.abs(part[f"{task}_{variant}"] - part[f"{task}_A"])
                            gaps.append({"cohort": cohort, "subset": subset, "variant": variant,
                                         "task": task, "rows": len(part), **distribution(diff)})
                            if subset in ["overall", "repeat", "second", "third_plus"]:
                                if task == "fail":
                                    actual = part.is_fail.to_numpy(dtype=float)
                                    a, b = (np.clip(part[f"fail_{v}"].to_numpy(), 1e-7, 1-1e-7) for v in ["A", variant])
                                    differences = -(actual*np.log(b)+(1-actual)*np.log1p(-b)) + (actual*np.log(a)+(1-actual)*np.log1p(-a))
                                else:
                                    actual = part["final_mark" if task == "grade" else "points"].to_numpy(dtype=float)
                                    differences = np.abs(part[f"{task}_{variant}"]-actual) - np.abs(part[f"{task}_A"]-actual)
                                intervals.append({"cohort": cohort, "subset": subset, "variant": variant,
                                                  "metric": "log_loss" if task == "fail" else f"{task}_mae",
                                                  **paired_cluster_interval(part.student_id, differences)})
            for variant in VARIANTS:
                work = rows.assign(actual_q=rows.course_credits*rows.points,
                                   predicted_q=rows.course_credits*rows[f"points_{variant}"])
                agg = work.groupby(["student_id", "degree_id", "part_id"], as_index=False).agg(
                    total_credits=("course_credits", "sum"), actual_q=("actual_q", "sum"),
                    predicted_q=("predicted_q", "sum"), has_repeat=("attempt_number", lambda a: a.gt(1).any()))
                agg = agg[agg.total_credits.gt(0)].copy()
                agg["plan_gpa_error"] = (agg.predicted_q-agg.actual_q)/agg.total_credits
                for label, mask in [("all_observed_plans", np.ones(len(agg),dtype=bool)), ("observed_plans_with_repeat", agg.has_repeat)]:
                    results = summarize_plan_errors(agg.loc[mask])
                    write_json(OUTPUT_DIR / f"observed_plan_metrics_{cohort}_{variant}_{label}.json", results)
        if split == "holdout":
            examples = []
            for label, mask in [("2", frame.attempt_number.eq(2)), ("3", frame.attempt_number.eq(3)), ("4+", frame.attempt_number.ge(4))]:
                for task in ["grade", "fail"]:
                    part = frame.loc[mask].copy()
                    part["absolute_difference"] = (part[f"{task}_B"]-part[f"{task}_A"]).abs()
                    part = part.nlargest(3, "absolute_difference")
                    part["chosen_by"], part["attempt_group"] = task, label
                    examples.append(part)
            pd.concat(examples).to_parquet(OUTPUT_DIR / "largest_prediction_changes.parquet", index=False)
    save_table("model_metrics", metrics)
    save_table("calibration_means", calibration)
    save_table("calibration_bins", plans)
    save_table("prediction_differences", gaps)
    save_table("paired_student_bootstrap", intervals)
