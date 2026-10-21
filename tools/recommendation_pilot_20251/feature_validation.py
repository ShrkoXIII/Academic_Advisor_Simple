"""Observed pre-20251 peer-feature diagnostics, independent of C retraining.

Only genuine historical points are averaged. The target's observed points
are held aside for error measurement and never passed into peer prediction.
Output contains aggregate metrics, without student/course identities.
"""
from collections import Counter
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from src import paths
from src.features.frozen_history import file_sha256
from src.paths import academic_part
from .adapter import PILOT_ROOT
from .enhanced import PEER_FIELDS, PointInTimePeers


SOURCE_COLUMNS = [
    "student_course_id", "student_id", "degree_id", "course_id", "part_id",
    "grade_version_id", "points", "start_agpa_points", "start_total_in_credits",
    "degree_credits_count", "gpa_trend_delta", "prior_total_fail_courses",
]
QUERY_COLUMNS = ["student_id", "degree_id", "grade_version_id", "degree_credits_count",
                 *[column for column in PEER_FIELDS if column != "academic_progress"]]


def _metrics(actual, predicted):
    valid = [(truth, value) for truth, value in zip(actual, predicted) if value is not None]
    count = len(valid)
    return {"covered_rows": count, "coverage": count / len(actual) if actual else 0.0,
            "mae": float(np.mean([abs(truth - value) for truth, value in valid])) if count else None}


def evaluate_peer_features(frame, *, target_part=20243, sample_size=60, seed=42,
                           k=20, min_support=5):
    """Measure one held-out historical semester against earlier distinct peers.

    The diagnostic baseline is an unweighted mean of true points from all
    earlier same-course/degree/grade-version distinct other students, retaining
    their latest earlier record. Both methods require the same support floor.
    This is a feature assessment, not an experiment C model evaluation.
    """
    target_part = academic_part(target_part)
    if target_part >= 20251:
        raise ValueError("Feature validation must use historical target parts before 20251.")
    if isinstance(sample_size, bool) or not isinstance(sample_size, int) or sample_size < 1:
        raise ValueError("A positive integer sample_size is required.")
    missing = set(SOURCE_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError("Historical peer source missing fields: " + ", ".join(sorted(missing)))
    parts = pd.to_numeric(frame.part_id, errors="coerce")
    if not np.isfinite(parts).all() or not parts.eq(parts.astype("int64")).all():
        raise ValueError("Historical peer source needs finite integer part_id values.")
    for part in parts.unique():
        academic_part(int(part))
    # Physically remove target/future records before constructing the helper.
    prefix = frame.loc[parts.lt(target_part), SOURCE_COLUMNS].copy()
    prefix["part_id"] = pd.to_numeric(prefix.part_id).astype("int64")
    prefix = prefix.sort_values(["part_id", "student_course_id"], kind="stable").reset_index(drop=True)
    targets = frame.loc[parts.eq(target_part), SOURCE_COLUMNS].copy()
    target_points = pd.to_numeric(targets.points, errors="coerce")
    targets = targets.loc[target_points.between(0, 4)].copy()
    targets = targets.sort_values("student_course_id", kind="stable").reset_index(drop=True)
    available_targets = len(targets)
    if len(targets) > sample_size:
        targets = targets.sample(n=sample_size, random_state=seed).sort_values(
            "student_course_id", kind="stable").reset_index(drop=True)
    predictor = PointInTimePeers(prefix, k=k, min_support=min_support)
    actual, predictions, baseline_predictions, supports = [], [], [], []
    maximum_selected_part, maximum_baseline_part = None, None
    for _, row in targets.iterrows():
        # Parquet nullable scalars use pd.NA; the peer helper accepts None for
        # omitted query dimensions. Preserve missingness instead of imputing.
        query = {column: None if pd.isna(row[column]) else row[column] for column in QUERY_COLUMNS}
        result = predictor.predict(query, row.course_id, target_part=target_part)
        selected_part = result["max_source_part"]
        if selected_part is not None:
            if selected_part >= target_part:
                raise ValueError("Peer temporal boundary was violated.")
            maximum_selected_part = max(maximum_selected_part or selected_part, selected_part)
        actual.append(float(row.points))
        predictions.append(result["peer_expected_points"])
        supports.append(int(result["similar_peer_support"]))
        matching = prefix.loc[
            prefix.degree_id.astype(str).eq(str(row.degree_id))
            & prefix.course_id.astype(str).eq(str(row.course_id))
            & prefix.grade_version_id.astype(str).eq(str(row.grade_version_id))
            & prefix.student_id.astype(str).ne(str(row.student_id))
        ].drop_duplicates("student_id", keep="last")
        points = pd.to_numeric(matching.points, errors="coerce")
        matching = matching.loc[points.between(0, 4)]
        if len(matching) >= min_support:
            baseline_predictions.append(float(pd.to_numeric(matching.points).mean()))
            baseline_part = int(matching.part_id.max())
            maximum_baseline_part = max(maximum_baseline_part or baseline_part, baseline_part)
        else:
            baseline_predictions.append(None)
    paired = [(truth, peer, baseline) for truth, peer, baseline in zip(
        actual, predictions, baseline_predictions) if peer is not None and baseline is not None]
    peer_paired_mae = float(np.mean([abs(a - p) for a, p, _ in paired])) if paired else None
    baseline_paired_mae = float(np.mean([abs(a - b) for a, _, b in paired])) if paired else None
    return {
        "phase": 3, "status": "PASS" if actual else "BLOCKED",
        "assessment": "standalone_observed_peer_feature_diagnostic",
        "target_part": target_part, "source_rule": "part_id < target_part; other students only",
        "seed": seed, "requested_sample_rows": sample_size, "available_target_rows": available_targets,
        "sample_rows": len(actual), "peer_pool_rows": len(prefix),
        "peer_pool_min_part": int(prefix.part_id.min()) if len(prefix) else None,
        "peer_pool_max_part": int(prefix.part_id.max()) if len(prefix) else None,
        "method": {"name": "uniform_knn", "k": k, "minimum_support": min_support,
                   "dimensions": PEER_FIELDS, "minimum_shared_dimensions": 3,
                   "grouping": ["degree_id", "course_id", "grade_version_id"],
                   "standardization": "earlier matching distinct-peer population; missing dimensions omitted",
                   "deduplication": "one latest earlier course record per other student"},
        "peer_expected_points": {"status": "MEASURED_DIAGNOSTIC", **_metrics(actual, predictions)},
        "similar_peer_support": {"minimum": min(supports) if supports else None,
                                 "maximum": max(supports) if supports else None,
                                 "mean": float(np.mean(supports)) if supports else None,
                                 "weak_support_rows": sum(s < min_support for s in supports),
                                 "histogram": {str(key): value for key, value in sorted(Counter(supports).items())}},
        "same_course_mean_points_baseline": {
            "method": "earlier_same_course_degree_grade_distinct_other_student_mean_true_points",
            "minimum_support": min_support, **_metrics(actual, baseline_predictions)},
        "paired_comparison": {"rows": len(paired), "peer_mae": peer_paired_mae,
                              "baseline_mae": baseline_paired_mae,
                              "peer_minus_baseline_mae": (peer_paired_mae - baseline_paired_mae) if paired else None},
        "point_in_time_checks": {"maximum_selected_peer_part": maximum_selected_part,
                                 "maximum_baseline_source_part": maximum_baseline_part,
                                 "target_outcomes_used_for_features": False,
                                 "target_points_used_only_for_error_measurement": True,
                                 "same_student_excluded": True},
        "student_relative_course_strength": {
            "status": "NOT_AVAILABLE", "reason": "No trusted academic-domain taxonomy; curriculum requirement types do not establish academic domains."},
        "course_difficulty_gap": {"status": "NOT_EVALUATED", "reason": "University aggregate integrity and compatible mark references remain unresolved."},
        "plan_difficulty_balance": {"status": "NOT_EVALUATED", "reason": "This course-feature assessment performs no plan generation or C-model predictions."},
        "selected_20251_outcomes_used": False, "model_training_performed": False,
        "experiment_c_accuracy_established": False,
        "limitations": [
            "A small deterministic 20243 observed-course sample is a diagnostic, not a population estimate.",
            "Feature prediction error does not establish usefulness after retraining, recommendation quality, or C-model accuracy.",
            "No probability of improvement, confidence interval, or calibrated uncertainty is estimated.",
            "The approved five-field Student API timing exception remains unproven for the separate pilot comparison.",
        ],
    }


def run_feature_validation(output_dir, *, source_path=None, sample_size=60):
    """Read one individual source and exclusively create a safe aggregate report."""
    if output_dir is None or not str(output_dir).strip():
        raise ValueError("An explicit fresh output directory is required.")
    output_dir = Path(output_dir).resolve()
    protected = [paths.RAW_DIR, paths.CLEAN_DIR, paths.MERGED_DIR, paths.TEMPORAL_DIR,
                 paths.FEATURE_DIR, paths.ARTIFACT_DIR, paths.MODEL_DIR, PILOT_ROOT / "api_data"]
    if any(output_dir == p.resolve() or output_dir.is_relative_to(p.resolve()) for p in protected):
        raise ValueError("Feature diagnostic output cannot be written under protected original data/model directories.")
    if output_dir.exists():
        raise FileExistsError("Feature diagnostic output already exists; choose a fresh directory.")
    source_path = Path(source_path or paths.TEMPORAL_TRAIN_FEATURES_PATH_V2)
    source_hash = file_sha256(source_path)
    schema = pq.ParquetFile(source_path)
    columns = schema.schema_arrow.names
    missing = set(SOURCE_COLUMNS) - set(columns)
    if missing:
        raise ValueError("Historical peer source missing fields: " + ", ".join(sorted(missing)))
    frame = pd.read_parquet(source_path, columns=SOURCE_COLUMNS)
    report = evaluate_peer_features(frame, sample_size=sample_size)
    report.update({"source_path": str(source_path.resolve()), "source_sha256": source_hash,
                   "source_row_count": int(schema.metadata.num_rows), "source_column_count": len(columns),
                   "source_schema_columns": columns, "read_columns": SOURCE_COLUMNS,
                   "source_feature_engineering_version": frame.attrs.get("feature_engineering_version"),
                   "source_min_part": int(pd.to_numeric(frame.part_id).min()) if len(frame) else None,
                   "source_max_part": int(pd.to_numeric(frame.part_id).max()) if len(frame) else None,
                   "individual_source_student_count": int(frame.student_id.nunique()),
                   "individual_source_degree_count": int(frame.degree_id.nunique())})
    if file_sha256(source_path) != source_hash:
        raise ValueError("Historical peer source changed during validation; no result was written.")
    output_dir.mkdir(parents=True, exist_ok=False)
    with (output_dir / "feature_validation_report.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    return report
