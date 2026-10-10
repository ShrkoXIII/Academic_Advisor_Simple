"""Read-only descriptive student progress audit; no models or 2025 feature labels."""
from pathlib import Path
import hashlib
import itertools
import json
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
EVIDENCE = OUT / "evidence"
FIELDS = ["start_total_in_credits", "start_total_in_courses", "total_reg_credits", "total_reg_courses"]
KEYS = ["student_id", "degree_id", "part_id"]
ALIASES = ["prior_total_reg_credits", "prior_total_reg_courses"]
PATHS = {
    "raw": "data/raw/v_add_student_degree_status.parquet",
    "clean_v1": "data/clean/student_status.parquet",
    "clean_v2": "data/clean/student_status_v2.parquet",
    "train_v2": "data/features/temporal_train_features_v2.parquet",
}


def save(name, records):
    df = records if isinstance(records, pd.DataFrame) else pd.DataFrame(records)
    df.to_csv(EVIDENCE / f"{name}.csv", index=False)
    return df


def numeric(s):
    return pd.to_numeric(s, errors="coerce").astype(float)


def window(df):
    return df[numeric(df.part_id).floordiv(10).between(2020, 2024)].copy()


def stats(s):
    s = numeric(s)
    return {"rows": len(s), "missing": int(s.isna().sum()),
            "missing_pct": 100 * s.isna().mean(), "unique": int(s.nunique()),
            "mean": s.mean(), "median": s.median(), "min": s.min(), "max": s.max(), "std": s.std()}


def corr(a, b, method):
    d = pd.concat([numeric(a), numeric(b)], axis=1).dropna()
    if len(d) < 2 or d.iloc[:, 0].nunique() < 2 or d.iloc[:, 1].nunique() < 2:
        return np.nan
    if method == "spearman":
        d = d.rank()
    return d.iloc[:, 0].corr(d.iloc[:, 1])


def pair_stats(df, a, b):
    av, bv = numeric(df[a]), numeric(df[b])
    valid = av.notna() & bv.notna()
    diff = av[valid] - bv[valid]
    return {"a": a, "b": b, "valid": int(valid.sum()), "pearson": corr(av, bv, "pearson"),
            "spearman": corr(av, bv, "spearman"), "exact_equal": int(diff.eq(0).sum()),
            "equal_tolerance_1e8": int(np.isclose(diff, 0, atol=1e-8, rtol=0).sum()),
            "equal_pct": 100 * diff.eq(0).mean(), "a_minus_b_mean": diff.mean(),
            "a_minus_b_median": diff.median(), "a_minus_b_min": diff.min(),
            "a_minus_b_max": diff.max(), "a_minus_b_std": diff.std(),
            "a_minus_b_unique": int(diff.nunique())}


def mapping(df, a, b):
    d = df[[a, b]].dropna()
    counts = d.groupby(a, dropna=False)[b].nunique()
    ambiguous = counts[counts.gt(1)].index
    return {"source": a, "destination": b, "valid": len(d), "source_values": len(counts),
            "ambiguous_source_values": len(ambiguous), "max_destination_values_per_source": counts.max(),
            "rows_in_ambiguous_source_values": int(d[a].isin(ambiguous).sum()),
            "deterministic_on_observed_data": bool(len(ambiguous) == 0)}


def identity(df, label, lhs, rhs, dataset):
    lhs, rhs = numeric(lhs), numeric(rhs)
    valid = lhs.notna() & rhs.notna()
    diff = lhs[valid] - rhs[valid]
    equal = np.isclose(diff, 0, atol=1e-8, rtol=0)
    return {"dataset": dataset, "identity": label, "valid": int(valid.sum()),
            "mismatch": int((~equal).sum()), "mismatch_pct": 100 * (~equal).mean(),
            "difference_mean": diff.mean(), "difference_min": diff.min(), "difference_max": diff.max()}


def table(df):
    # Avoid dependency on tabulate.
    def fmt(x):
        if isinstance(x, (float, np.floating)):
            return "NA" if pd.isna(x) else f"{x:.6g}"
        return str(x).replace("|", "/")
    return "| " + " | ".join(df.columns) + " |\n| " + " | ".join(["---"] * len(df.columns)) + " |\n" + "\n".join("| " + " | ".join(map(fmt, r)) + " |" for r in df.itertuples(index=False, name=None))


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    inputs = {}
    frames = {}
    schemas = {}
    for label, rel in PATHS.items():
        p = ROOT / rel
        schemas[label] = [{"name": f.name, "type": str(f.type)} for f in pq.read_schema(p)]
        inputs[label] = {"path": rel, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                         "physical_rows": pq.ParquetFile(p).metadata.num_rows}
        # No temporal_test_features file is opened.
        df = pd.read_parquet(p)
        for col in ["student_id", "student_status_id", "degree_id"]:
            df[col] = df[col].astype("string").str.replace(r"^(\d+)\.0+$", r"\1", regex=True)
        inputs[label]["window_rows"] = len(window(df))
        inputs[label]["duplicate_status_keys_window"] = int(window(df).duplicated(KEYS).sum())
        frames[label] = df
    (EVIDENCE / "schemas.json").write_text(json.dumps(schemas, indent=2), encoding="utf-8")
    (EVIDENCE / "input_manifest.json").write_text(json.dumps(inputs, indent=2), encoding="utf-8")
    windows = {k: window(v) for k, v in frames.items()}
    train = windows.pop("train_v2")
    assert train.part_id.floordiv(10).between(2020, 2024).all()
    windows["train_v2_course"] = train
    targets = ["points", "final_mark", "is_fail"]
    # Semester-level labels are means over finalized course rows, not GPA targets.
    agg = {c: "first" for c in FIELDS + ALIASES}
    agg.update({c: "mean" for c in targets})
    train_status = train.groupby(KEYS, as_index=False, dropna=False).agg(agg)
    windows["train_v2_status"] = train_status
    within = train.groupby(KEYS, dropna=False)[FIELDS + ALIASES].nunique(dropna=False)
    save("train_status_constancy", [{"field": c, "status_groups": len(within), "groups_with_multiple_values": int(within[c].gt(1).sum())} for c in within])
    aliases = [identity(train, "prior_total_reg_credits = total_reg_credits", train.prior_total_reg_credits, train.total_reg_credits, "train_v2_course"),
               identity(train, "prior_total_reg_courses = total_reg_courses", train.prior_total_reg_courses, train.total_reg_courses, "train_v2_course")]
    save("alias_equality", aliases)
    summaries, pairs, mappings, target_corrs, difference_values = [], [], [], [], []
    stratified_summaries, stratified_pairs, stratified_targets, stratified_mappings = [], [], [], []
    group_inventory = []
    for dataset, df in windows.items():
        df = df.copy()
        df["year"] = numeric(df.part_id).floordiv(10).astype(int)
        df["progress_quartile"] = pd.qcut(numeric(df.start_total_in_credits), 4, duplicates="drop").astype(str)
        for c in FIELDS:
            summaries.append({"dataset": dataset, "field": c, **stats(df[c])})
        for a, b in itertools.combinations(FIELDS, 2):
            pairs.append({"dataset": dataset, **pair_stats(df, a, b)})
            diffs = (numeric(df[a]) - numeric(df[b])).dropna().value_counts().sort_index()
            difference_values.extend({"dataset": dataset, "a": a, "b": b, "a_minus_b": value, "rows": int(count)} for value, count in diffs.items())
            for source, destination in [(a, b), (b, a)]:
                mappings.append({"dataset": dataset, **mapping(df, source, destination)})
        if dataset.startswith("train"):
            for c, t in itertools.product(FIELDS, targets):
                target_corrs.append({"dataset": dataset, "feature": c, "target": t,
                                     "valid": int((df[c].notna() & df[t].notna()).sum()),
                                     "pearson": corr(df[c], df[t], "pearson"), "spearman": corr(df[c], df[t], "spearman")})
        for group_col in ["year", "degree_id", "progress_quartile"]:
            for group_value, group in df.groupby(group_col, observed=True, dropna=False):
                prefix = {"dataset": dataset, "group_by": group_col, "group_value": str(group_value), "group_rows": len(group)}
                group_inventory.append({**prefix, "included": len(group) >= 100})
                if len(group) < 100:
                    continue
                for c in FIELDS:
                    stratified_summaries.append({**prefix, "field": c, **stats(group[c])})
                for a, b in itertools.combinations(FIELDS, 2):
                    stratified_pairs.append({**prefix, **pair_stats(group, a, b)})
                    for source, destination in [(a, b), (b, a)]:
                        stratified_mappings.append({**prefix, **mapping(group, source, destination)})
                if dataset.startswith("train"):
                    for c, t in itertools.product(FIELDS, targets):
                        stratified_targets.append({**prefix, "feature": c, "target": t,
                                                   "pearson": corr(group[c], group[t], "pearson"),
                                                   "spearman": corr(group[c], group[t], "spearman")})
    summary = save("summary", summaries)
    pair = save("pairwise", pairs)
    save("pair_difference_frequencies", difference_values)
    map_df = save("deterministic_mappings", mappings)
    target_df = save("target_correlations", target_corrs)
    save("stratified_summary", stratified_summaries)
    stratified_pair_df = save("stratified_pairwise", stratified_pairs)
    save("stratified_target_correlations", stratified_targets)
    save("stratified_deterministic_mappings", stratified_mappings)
    inventory_df = save("group_inventory", group_inventory)
    group_overview = []
    for (dataset, group_by), groups in inventory_df.groupby(["dataset", "group_by"]):
        included = groups[groups.included]
        group_overview.append({"dataset": dataset, "group_by": group_by,
                               "observed_groups": len(groups), "included_groups": len(included),
                               "excluded_below_100": len(groups) - len(included),
                               "smallest_observed_group": groups.group_rows.min(),
                               "smallest_included_group": included.group_rows.min(),
                               "largest_included_group": included.group_rows.max()})
    overview_df = save("group_overview", group_overview)
    training_credit_pairs = stratified_pair_df[
        stratified_pair_df.dataset.eq("train_v2_status")
        & stratified_pair_df.a.eq("start_total_in_credits")
        & stratified_pair_df.b.eq("total_reg_credits")]
    year_credit_pairs = training_credit_pairs[training_credit_pairs.group_by.eq("year")]
    save("train_status_year_credit_pairwise", year_credit_pairs)
    range_rows = []
    for group_by, groups in training_credit_pairs.groupby("group_by"):
        range_rows.append({"group_by": group_by, "groups": len(groups),
                           "pearson_min": groups.pearson.min(), "pearson_median": groups.pearson.median(),
                           "pearson_max": groups.pearson.max(), "equality_pct_min": groups.equal_pct.min(),
                           "equality_pct_median": groups.equal_pct.median(), "equality_pct_max": groups.equal_pct.max()})
    range_df = save("train_status_credit_pairwise_ranges", range_rows)
    identities, transitions = [], []
    examples = []
    for dataset in ["raw", "clean_v1", "clean_v2"]:
        d = windows[dataset]
        for unit in ["credits", "courses"]:
            def col(name):
                return d[f"{name}_{unit}"]
            for label, lhs, rhs in [
                (f"total_reg_{unit} = total_pass + total_fail", col("total_reg"), col("total_pass") + col("total_fail")),
                (f"start_total_in_{unit} = total_pass", col("start_total_in"), col("total_pass")),
                (f"start_total_in_{unit} = total_reg - total_fail", col("start_total_in"), col("total_reg") - col("total_fail")),
                (f"end_total_in_{unit} = start_total_in + semester_pass", col("end_total_in"), col("start_total_in") + col("semester_pass")),
                (f"semester_reg_{unit} = semester_pass + semester_fail", col("semester_reg"), col("semester_pass") + col("semester_fail")),
            ]:
                identities.append(identity(d, label, lhs, rhs, dataset))
            if f"semester_in_{unit}" in d:
                identities.append(identity(d, f"end_total_in_{unit} = start_total_in + semester_in", col("end_total_in"), col("start_total_in") + col("semester_in"), dataset))
        # Current target within 2020-2024, prior source row can precede 2020.
        hist = frames[dataset].dropna(subset=KEYS).sort_values(KEYS + ["student_status_id"], kind="stable")
        duplicate = hist.duplicated(KEYS, keep=False)
        if duplicate.any():
            # Ambiguous raw status keys are excluded from transition claims.
            hist = hist[~duplicate].copy()
        previous = hist.groupby(KEYS[:2], dropna=False).shift()
        current = numeric(hist.part_id).floordiv(10).between(2020, 2024)
        valid_previous = previous.part_id.notna() & current
        consecutive = (valid_previous
                       & numeric(hist.part_id).mod(10).isin([1, 2, 3])
                       & numeric(previous.part_id).mod(10).isin([1, 2, 3])
                       & ((numeric(hist.part_id) - numeric(previous.part_id)).isin([1, 8])))
        for cohort, mask in [("all_observed", valid_previous), ("calendar_adjacent_1_2_3", consecutive)]:
            dh = hist.loc[mask]
            ph = previous.loc[mask]
            for unit in ["credits", "courses"]:
                for label, lhs, rhs in [
                    (f"current_start_total_in_{unit} = previous_end_total_in", dh[f"start_total_in_{unit}"], ph[f"end_total_in_{unit}"]),
                    (f"current_total_reg_{unit} = previous_total_reg + previous_semester_reg", dh[f"total_reg_{unit}"], ph[f"total_reg_{unit}"] + ph[f"semester_reg_{unit}"]),
                    (f"current_total_pass_{unit} = previous_total_pass + previous_semester_pass", dh[f"total_pass_{unit}"], ph[f"total_pass_{unit}"] + ph[f"semester_pass_{unit}"]),
                    (f"current_total_fail_{unit} = previous_total_fail + previous_semester_fail", dh[f"total_fail_{unit}"], ph[f"total_fail_{unit}"] + ph[f"semester_fail_{unit}"]),
                    (f"current_total_reg_{unit} = previous_total_reg + CURRENT_semester_reg_control", dh[f"total_reg_{unit}"], ph[f"total_reg_{unit}"] + dh[f"semester_reg_{unit}"]),
                ]:
                    transitions.append({"cohort": cohort, **identity(dh, label, lhs, rhs, dataset)})
        if dataset == "clean_v2":
            dh = hist.loc[valid_previous]
            ph = previous.loc[valid_previous]
            checks = {
                "lag_start_end_mismatch": ~np.isclose(numeric(dh.start_total_in_credits), numeric(ph.end_total_in_credits), atol=1e-8, rtol=0),
                "lag_reg_increment_mismatch": ~np.isclose(numeric(dh.total_reg_credits), numeric(ph.total_reg_credits + ph.semester_reg_credits), atol=1e-8, rtol=0),
                "start_vs_reg_difference": ~np.isclose(numeric(dh.start_total_in_credits), numeric(dh.total_reg_credits), atol=1e-8, rtol=0),
            }
            for reason, m in checks.items():
                for idx in dh.index[m][:5]:
                    row = dh.loc[idx]
                    prev = ph.loc[idx]
                    record = {"reason": reason, "student_sha256": hashlib.sha256(str(row.student_id).encode()).hexdigest(),
                              "degree_id": row.degree_id, "part_id": row.part_id, "previous_part_id": prev.part_id}
                    record.update({c: row[c] for c in FIELDS + ["end_total_in_credits", "total_pass_credits", "total_fail_credits", "semester_reg_credits"]})
                    record.update({f"previous_{c}": prev[c] for c in ["end_total_in_credits", "total_reg_credits", "semester_reg_credits"]})
                    examples.append(record)
    identity_df = save("concept_identities", identities)
    transition_df = save("status_transitions", transitions)
    example_df = save("anonymized_examples", examples)
    parity_records = []
    a, b = windows["clean_v1"], windows["clean_v2"]
    relevant = [c for c in a.columns if c in b.columns and (c in FIELDS or any(term in c for term in ["total_", "semester_"]))]
    join = a[KEYS + relevant].merge(b[KEYS + relevant], on=KEYS, how="outer", suffixes=("_v1", "_v2"), indicator=True, validate="one_to_one")
    parity_counts = {str(k): int(v) for k, v in join._merge.value_counts().items()}
    common = join[join._merge.eq("both")]
    for c in relevant:
        v1, v2 = numeric(common[c + "_v1"]), numeric(common[c + "_v2"])
        equal = v1.eq(v2) | (v1.isna() & v2.isna())
        parity_records.append({"field": c, "common_rows": len(common), "mismatch": int((~equal).sum()),
                               "both_missing": int((v1.isna() & v2.isna()).sum()),
                               "v1_missing_only": int((v1.isna() & v2.notna()).sum()), "v2_missing_only": int((v1.notna() & v2.isna()).sum())})
    parity_df = save("v1_v2_parity", parity_records)
    (EVIDENCE / "v1_v2_join_counts.json").write_text(json.dumps(parity_counts, indent=2), encoding="utf-8")
    # 2025 status-only summaries, clearly outside training comparisons.
    diag = []
    for dataset in ["raw", "clean_v1", "clean_v2"]:
        d = frames[dataset]
        d = d[numeric(d.part_id).floordiv(10).eq(2025)]
        for c in FIELDS:
            diag.append({"dataset": dataset, "source_temporal_diagnostic_year": 2025, "field": c, **stats(d[c])})
    save("status_2025_source_diagnostics_only", diag)
    raw_clean = []
    raw = windows["raw"]
    for dataset in ["clean_v1", "clean_v2"]:
        clean = windows[dataset]
        matched = clean[["student_status_id"] + FIELDS].merge(raw[["student_status_id"] + FIELDS], on="student_status_id", suffixes=("_clean", "_raw"), validate="one_to_one")
        for c in FIELDS:
            raw_clean.append(identity(matched, f"{c} clean = raw", matched[c + "_clean"], matched[c + "_raw"], dataset))
    save("raw_clean_value_preservation", raw_clean)
    train_clean = train[["student_status_id"] + FIELDS].merge(windows["clean_v2"][["student_status_id"] + FIELDS], on="student_status_id", suffixes=("_train", "_clean"), validate="many_to_one", how="left", indicator=True)
    assert train_clean._merge.eq("both").all()
    save("train_clean_value_preservation", [identity(train_clean, f"{c} train = clean V2", train_clean[c + "_train"], train_clean[c + "_clean"], "train_v2_course") for c in FIELDS])
    source_unchanged = {}
    for label, rel in PATHS.items():
        source_unchanged[label] = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == inputs[label]["sha256"]
    assert all(source_unchanged.values())
    (EVIDENCE / "read_only_verification.json").write_text(json.dumps({"all_sources_unchanged": all(source_unchanged.values()), "sources": source_unchanged, "opened_2025_feature_tables": False, "trained_or_evaluated_models": False}, indent=2), encoding="utf-8")
    train_pairs = pair[pair.dataset.eq("train_v2_course")]
    def relation(a, b):
        return train_pairs[train_pairs.a.eq(a) & train_pairs.b.eq(b)].iloc[0]
    credit_relation = relation("start_total_in_credits", "total_reg_credits")
    course_relation = relation("start_total_in_courses", "total_reg_courses")
    clean_adjacent = transition_df[transition_df.dataset.eq("clean_v2") & transition_df.cohort.eq("calendar_adjacent_1_2_3")]
    reg_credit_transition = clean_adjacent[clean_adjacent.identity.eq("current_total_reg_credits = previous_total_reg + previous_semester_reg")].iloc[0]
    start_credit_transition = clean_adjacent[clean_adjacent.identity.eq("current_start_total_in_credits = previous_end_total_in")].iloc[0]
    report = ["# Student progress: empirical data audit", "",
              "Analysis window: target parts 20201–20243 (2020–2024). No 2025 feature table was opened. Separate 2025 raw/clean status summaries are source diagnostics only. No model was trained or evaluated.", "",
              "These are empirical relations in the provided extract. The SQL/view definition and database business semantics were not supplied, so field names and source comments do not independently verify semantics.", "",
              "## Main findings", "",
              f"- The four fields have no missing values in clean V1/V2 or training V2. Raw 2020–2024 has 11 missing values per field. Training has {len(train):,} course rows and {len(train_status):,} status groups; all four fields and both aliases are constant inside each status group.",
              f"- Start and registration totals are correlated but differ: credits Pearson {credit_relation.pearson:.6f}, equal {credit_relation.equal_pct:.4f}%; courses Pearson {course_relation.pearson:.6f}, equal {course_relation.equal_pct:.4f}%. No directed pair is globally deterministic in any of the five grains/datasets. This does not establish whether a field helps a trained model.",
              f"- On {int(reg_credit_transition.valid):,} adjacent clean V2 status transitions, registration credits follow previous cumulative total plus previous semester registration with {int(reg_credit_transition.mismatch):,} mismatch ({reg_credit_transition.mismatch_pct:.6f}%). Start credits equal previous end credits with {int(start_credit_transition.mismatch):,} mismatches ({start_credit_transition.mismatch_pct:.4f}%). The timing evidence supports a prior-semester interpretation of total registration credits; it is not a verified SQL/view contract.",
              f"- V1/V2 share {len(common):,} status keys with zero mismatches across {len(relevant)} progress/semester columns; V2 adds {parity_counts.get('right_only', 0):,} rows. Matched raw/clean and clean/training checks preserve the four fields exactly. Both prior aliases equal original total registration fields on all training rows.",
              "- Simple passed/failed decompositions are not exact identities: roughly half the clean status rows fail total registration = total passed + total failed, and roughly half fail start in = total passed. Do not substitute these fields using those formulas.", "",
              "## Grain and reproducibility", "",
              "`train_v2_course` weights a semester by its finalized course rows. `train_v2_status` uses one student/degree/part and means of its course labels (`points`, `final_mark`, `is_fail`); these are not GPA labels. Clean/raw windows use status rows. All six unordered field pairs and twelve directed mappings are tested. Statistics use sample standard deviation; equality is exact, identities additionally use absolute tolerance 1e-8. Missing pairs are excluded. Progress quartiles use `start_total_in_credits` separately per dataset; tied cut points can reduce bins. Stratified groups need at least 100 rows; excluded counts are in `group_inventory.csv`.", "",
              table(pd.DataFrame([{"dataset": k, **v} for k, v in inputs.items()]).drop(columns=["sha256"])), "",
              "## Distributions", "", table(summary), "", "## All pair relationships", "",
              table(pair[["dataset", "a", "b", "pearson", "spearman", "equal_pct", "a_minus_b_mean", "a_minus_b_min", "a_minus_b_max"]]), "",
              "Pairwise difference distributions (every observed value and its row frequency) are in `pair_difference_frequencies.csv`.", "",
              "## Status group counts and stratified credit relationships", "",
              "Training status groups use one student/degree/part. Every included stratum has at least 100 such groups; the same threshold is applied separately at course grain. Observed counts and exclusions:", "",
              table(overview_df[overview_df.dataset.eq("train_v2_status")]), "",
              "Start-credit versus total-registration-credit correlations by training target year:", "",
              table(year_credit_pairs[["group_value", "group_rows", "pearson", "spearman", "equal_pct", "a_minus_b_mean"]]), "",
              "Ranges over qualifying training-status degree and progress strata:", "", table(range_df), "",
              "## Training target correlations", "", table(target_df), "",
              "## Directed deterministic mapping checks", "", table(map_df), "",
              "## Concept identity checks", "", table(identity_df), "", "## Lagged source transitions", "",
              "Transitions group by student/degree; rows with ambiguous duplicate raw keys are excluded. `all_observed` may contain gaps. `calendar_adjacent_1_2_3` includes differences 1 or 8 between normal semester codes; semester-4 raw rows may disrupt adjacency. Current rows are limited to 2020–2024. Prior rows may predate 2020. Missing prior status history and filtering can explain failures and are not automatically leakage.", "",
              table(transition_df), "", "## V1 / V2 parity", "", f"Outer join counts in the 2020–2024 window: `{json.dumps(parity_counts)}`.", "", table(parity_df), "",
              "## Representative real-source examples", "",
              "These examples retain degree, part and measured progress numbers. Student keys are reproducible SHA256 pseudonyms. Previous/current differences demonstrate observed variation; they do not establish database business semantics.", "",
              table(example_df.groupby("reason", sort=False).head(1)[["reason", "student_sha256", "degree_id", "part_id", "previous_part_id", "start_total_in_credits", "total_reg_credits", "previous_end_total_in_credits", "previous_total_reg_credits", "previous_semester_reg_credits"]]), "",
              "## Evidence files", "", "All tables are saved as CSV under `evidence/`. `schemas.json` records actual Parquet types; `input_manifest.json` records source SHA256 and row counts. `alias_equality.csv` verifies the training aliases. Stratified distribution, correlation, equality/difference and deterministic mapping tables are saved separately for year, degree and progress quartile. `anonymized_examples.csv` uses SHA256 of the source student ID; no original student or status IDs are emitted. This stable pseudonym is not proof of irreversible anonymization. `raw_clean_value_preservation.csv` checks whether cleaning changes the four fields for matched status IDs.", ""]
    (OUT / "data_findings.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"input_counts": inputs, "train_status_rows": len(train_status), "parity_counts": parity_counts,
                      "aliases": aliases, "report": str(OUT / "data_findings.md")}, indent=2))


if __name__ == "__main__":
    main()
