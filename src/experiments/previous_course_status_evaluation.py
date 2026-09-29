"""Compare baseline and augmented V2 models on the same holdout rows."""

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import average_precision_score, log_loss, mean_absolute_error

from src.experiments.course_only_core import COURSE_ONLY_FEATURES, prepare_course_matrix
from src.experiments.course_only_training import load_experiment, write_json
from src.experiments.previous_course_status_data import EVALUATION_OUTPUT_DIR
from src.experiments.previous_course_status_training import (
    VARIANTS, _load_tables, load_variant, prepare_augmented_matrix,
)
from src.features.feature_contract import (
    BASE_FEATURES, load_category_levels, prepare_model_matrix,
)
from src.features.student_course_status import STATUS_LEVELS
from src.modeling import train_models as official
from src.paths import (
    CATEGORY_LEVELS_PATH_V2, FAIL_MODEL_PATH_V2, GRADE_MODEL_PATH_V2,
    MODEL_METADATA_PATH_V2, PROJECT_ROOT,
)
import json


def status_slices(
    *, actual_grade, actual_fail, baseline_grade, augmented_grade,
    baseline_fail, augmented_fail, status,
):
    """Measure each latest-prior status; report PR-AUC for sufficient cases."""
    values = [np.asarray(value) for value in (
        actual_grade, actual_fail, baseline_grade, augmented_grade,
        baseline_fail, augmented_fail, status,
    )]
    if len({len(value) for value in values}) != 1:
        raise ValueError("Status comparison inputs must have identical rows")
    grade, fail, grade_base, grade_new, fail_base, fail_new, categories = values
    slices = {}
    for name in [*STATUS_LEVELS, "__UNKNOWN__"]:
        mask = categories == name
        rows = int(mask.sum())
        item = {"rows": rows, "fail_positives": int(fail[mask].sum()),
                "fail_negatives": rows - int(fail[mask].sum())}
        if rows:
            item["grade_mae_baseline"] = float(mean_absolute_error(grade[mask], grade_base[mask]))
            item["grade_mae_augmented"] = float(mean_absolute_error(grade[mask], grade_new[mask]))
            item["grade_mae_delta"] = item["grade_mae_augmented"] - item["grade_mae_baseline"]
            item["fail_log_loss_baseline"] = float(log_loss(
                fail[mask], np.clip(fail_base[mask], 1e-7, 1 - 1e-7), labels=[0, 1]
            ))
            item["fail_log_loss_augmented"] = float(log_loss(
                fail[mask], np.clip(fail_new[mask], 1e-7, 1 - 1e-7), labels=[0, 1]
            ))
            item["fail_log_loss_delta"] = item["fail_log_loss_augmented"] - item["fail_log_loss_baseline"]
        else:
            for field in ("grade_mae_baseline", "grade_mae_augmented", "grade_mae_delta",
                          "fail_log_loss_baseline", "fail_log_loss_augmented", "fail_log_loss_delta"):
                item[field] = None
        # A very small positive/negative count makes AP unstable and unhelpful.
        meaningful = rows >= 100 and min(item["fail_positives"], item["fail_negatives"]) >= 30
        item["pr_auc_criterion_met"] = meaningful
        item["pr_auc_baseline"] = float(average_precision_score(fail[mask], fail_base[mask])) if meaningful else None
        item["pr_auc_augmented"] = float(average_precision_score(fail[mask], fail_new[mask])) if meaningful else None
        item["pr_auc_delta"] = item["pr_auc_augmented"] - item["pr_auc_baseline"] if meaningful else None
        slices[name] = item
    return slices


def _predict(model, matrix, maximum):
    values = np.asarray(model.predict(matrix, num_threads=4), dtype="float64")
    if values.shape != (len(matrix),) or not np.isfinite(values).all():
        raise ValueError("Holdout model returned invalid predictions")
    return np.clip(values, 0, maximum)


def _paired_metrics(test, predictions, baseline_number, augmented_number, baseline_meta, augmented_meta):
    actual_grade = test["final_mark"]
    actual_fail = test["is_fail"]
    grade_base = predictions[f"predicted_mark_{baseline_number}"]
    grade_new = predictions[f"predicted_mark_{augmented_number}"]
    fail_base = predictions[f"fail_probability_{baseline_number}"]
    fail_new = predictions[f"fail_probability_{augmented_number}"]
    gb = official.regression_metrics(actual_grade, grade_base)
    gn = official.regression_metrics(actual_grade, grade_new)
    fb = official.classification_metrics(actual_fail, fail_base)
    fn = official.classification_metrics(actual_fail, fail_new)
    return {
        "baseline_features": baseline_number,
        "experimental_features": augmented_number,
        "grade": {key: {"baseline": gb[key], "augmented": gn[key], "delta": gn[key] - gb[key]}
                  for key in gb},
        "fail": {key: {"baseline": fb[key], "augmented": fn[key], "delta": fn[key] - fb[key]}
                 for key in fb},
        "cv_mean_mae": {
            "baseline": baseline_meta["grade"], "augmented": augmented_meta["grade"],
            "delta": augmented_meta["grade"] - baseline_meta["grade"],
        },
        "cv_mean_log_loss": {
            "baseline": baseline_meta["fail"], "augmented": augmented_meta["fail"],
            "delta": augmented_meta["fail"] - baseline_meta["fail"],
        },
        "by_previous_status": status_slices(
            actual_grade=actual_grade, actual_fail=actual_fail,
            baseline_grade=grade_base, augmented_grade=grade_new,
            baseline_fail=fail_base, augmented_fail=fail_new,
            status=test["previous_course_status"],
        ),
    }


def _check_saved_baseline(fresh, saved, label):
    differences = {key: abs(fresh[key] - saved[key]) for key in fresh}
    if max(differences.values()) > 1e-5:
        raise ValueError(f"Fresh {label} holdout metrics differ from saved baseline: {differences}")
    return differences


def _retake_sample(predictions):
    rows = []
    for status in ("FAILED", "WITHDRAWN", "CONDITIONAL_PASS"):
        sample = predictions.loc[predictions.previous_course_status.eq(status)].sort_values(
            ["student_id", "course_id", "part_id", "student_course_id"], kind="stable"
        ).head(20)
        for baseline_number, augmented_number in ((47, 48), (33, 34)):
            for row in sample.itertuples(index=False):
                base = getattr(row, f"predicted_mark_{baseline_number}")
                new = getattr(row, f"predicted_mark_{augmented_number}")
                rows.append({
                    "comparison": f"{baseline_number}_vs_{augmented_number}",
                    "student_id": row.student_id, "course_id": row.course_id,
                    "part_id": row.part_id, "previous_status": status,
                    "attempt_number": row.attempt_number,
                    "actual_final_mark": row.final_mark,
                    "baseline_prediction": base, "new_prediction": new,
                    "absolute_error_baseline": abs(row.final_mark - base),
                    "absolute_error_new": abs(row.final_mark - new),
                })
    return pd.DataFrame(rows)


def evaluate_holdout():
    """Freshly score 47/48 and 33/34 on the same unmodified V2 test rows."""
    _, test = _load_tables()
    official_meta = json.loads(MODEL_METADATA_PATH_V2.read_text(encoding="utf-8"))
    grade33, fail33, levels33, course_meta = load_experiment()
    grade47 = lgb.Booster(model_file=str(GRADE_MODEL_PATH_V2))
    fail47 = lgb.Booster(model_file=str(FAIL_MODEL_PATH_V2))
    if grade47.feature_name() != BASE_FEATURES or fail47.feature_name() != BASE_FEATURES:
        raise ValueError("Official model feature headers changed")
    official_levels = load_category_levels(CATEGORY_LEVELS_PATH_V2)
    matrices = {
        47: prepare_model_matrix(test, official_levels),
        33: prepare_course_matrix(test, levels33),
    }
    columns = ["student_course_id", "student_id", "course_id", "part_id",
               "attempt_number", "final_mark", "is_fail", "previous_course_status"]
    predictions = test[columns].copy()
    models = {47: (grade47, fail47), 33: (grade33, fail33)}
    variant_metadata = {}
    for variant, base_features in VARIANTS.items():
        grade, fail, levels, metadata = load_variant(variant)
        number = len(base_features) + 1
        models[number] = (grade, fail)
        matrices[number] = prepare_augmented_matrix(test, levels, base_features)
        variant_metadata[number] = metadata
    for number in (47, 48, 33, 34):
        grade, fail = models[number]
        predictions[f"predicted_mark_{number}"] = _predict(grade, matrices[number], 100)
        predictions[f"fail_probability_{number}"] = _predict(fail, matrices[number], 1)
        print(f"Scored holdout with {number} features", flush=True)
    del matrices
    official_saved = {
        "grade": official_meta["grade_regressor"]["selected_candidate"]["mean_primary_metric"],
        "fail": official_meta["fail_risk_classifier"]["selected_candidate"]["mean_primary_metric"],
    }
    course_saved = {
        "grade": course_meta["grade"]["selected_candidate"]["mean_primary_metric"],
        "fail": course_meta["fail"]["selected_candidate"]["mean_primary_metric"],
    }
    augmented48 = {
        "grade": variant_metadata[48]["grade"]["selected_candidate"]["mean_primary_metric"],
        "fail": variant_metadata[48]["fail"]["selected_candidate"]["mean_primary_metric"],
    }
    augmented34 = {
        "grade": variant_metadata[34]["grade"]["selected_candidate"]["mean_primary_metric"],
        "fail": variant_metadata[34]["fail"]["selected_candidate"]["mean_primary_metric"],
    }
    pairs = {
        "47_vs_48": _paired_metrics(test, predictions, 47, 48, official_saved, augmented48),
        "33_vs_34": _paired_metrics(test, predictions, 33, 34, course_saved, augmented34),
    }
    baseline_parity = {
        "official_grade": _check_saved_baseline(
            official.regression_metrics(test.final_mark, predictions.predicted_mark_47),
            official_meta["grade_regressor"]["test_2025_metrics"], "official grade",
        ),
        "official_fail": _check_saved_baseline(
            official.classification_metrics(test.is_fail, predictions.fail_probability_47),
            official_meta["fail_risk_classifier"]["test_2025_metrics"], "official fail",
        ),
        "course_grade": _check_saved_baseline(
            official.regression_metrics(test.final_mark, predictions.predicted_mark_33),
            course_meta["grade"]["experimental_test_metrics"], "course-only grade",
        ),
        "course_fail": _check_saved_baseline(
            official.classification_metrics(test.is_fail, predictions.fail_probability_33),
            course_meta["fail"]["experimental_test_metrics"], "course-only fail",
        ),
    }
    EVALUATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    predictions.to_parquet(EVALUATION_OUTPUT_DIR / "holdout_predictions.parquet", index=False)
    (PROJECT_ROOT / "data/debug/previous_course_status").mkdir(parents=True, exist_ok=True)
    _retake_sample(predictions).to_csv(
        PROJECT_ROOT / "data/debug/previous_course_status/retake_sample.csv",
        index=False, encoding="utf-8-sig",
    )
    summary = {
        "holdout_rows": len(test), "baseline_parity_max_abs_difference": {
            key: max(item.values()) for key, item in baseline_parity.items()
        },
        "pr_auc_slice_criterion": "at least 100 rows, 30 fail positives and 30 fail negatives",
        "comparisons": pairs,
    }
    write_json(EVALUATION_OUTPUT_DIR / "holdout_comparison.json", summary)
    return summary
