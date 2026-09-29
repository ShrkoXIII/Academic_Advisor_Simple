"""Isolated V2 training for previous student-course status."""

from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb

from src.experiments.course_only_core import COURSE_ONLY_FEATURES, prepare_course_matrix
from src.features.feature_contract import (
    BASE_FEATURES, CATEGORICAL_FEATURES, CATEGORY_MISSING, CATEGORY_UNKNOWN,
    learn_category_levels, prepare_model_matrix,
)
from src.features.student_course_status import STATUS_LEVELS
from src.features.frozen_history import file_sha256
from src.modeling import train_models as official
from src.modeling.training_config import TARGET_FAIL, TARGET_GRADE, training_weights
from src.paths import (
    CATEGORY_LEVELS_PATH_V2, CLEAN_REGISTRATION_ROSTER_PATH_V2,
    CLEAN_STUDENT_COURSE_PATH_V2, FAIL_MODEL_PATH_V2, GRADE_MODEL_PATH_V2,
    MODEL_METADATA_PATH_V2, PROJECT_ROOT, TEMPORAL_TEST_FEATURES_PATH_V2,
    TEMPORAL_TRAIN_FEATURES_PATH_V2,
)
from src.features.feature_contract import (
    FEATURE_ENGINEERING_VERSION, require_current_features, save_category_levels,
)
from src.experiments.course_only_training import write_json
from src.experiments.previous_course_status_data import FEATURE_OUTPUT_DIR, EVALUATION_OUTPUT_DIR


PLAN_AWARE_WITH_PREVIOUS_STATUS = [*BASE_FEATURES, "previous_course_status"]
COURSE_ONLY_WITH_PREVIOUS_STATUS = [*COURSE_ONLY_FEATURES, "previous_course_status"]
EXPERIMENT_MODEL_DIR = PROJECT_ROOT / "models/experiments/previous_course_status"
VARIANTS = {
    "plan_aware_48": BASE_FEATURES,
    "course_only_34": COURSE_ONLY_FEATURES,
}


def learn_augmented_levels(frame):
    """Learn old categories from fit rows; fix status levels for every fold."""
    levels = learn_category_levels(frame)
    levels["previous_course_status"] = [*STATUS_LEVELS, CATEGORY_MISSING, CATEGORY_UNKNOWN]
    return levels


def prepare_augmented_matrix(frame, levels, base_features):
    """Apply the exact ordered 47/33 base matrix plus one categorical column."""
    if base_features == BASE_FEATURES:
        matrix = prepare_model_matrix(frame, levels)
    elif base_features == COURSE_ONLY_FEATURES:
        matrix = prepare_course_matrix(frame, levels)
    else:
        raise ValueError("Unknown experimental base feature contract")
    if "previous_course_status" not in frame:
        raise ValueError("Missing previous_course_status")
    allowed = levels["previous_course_status"]
    values = frame["previous_course_status"].astype("string").fillna(CATEGORY_MISSING)
    values = values.where(values.isin(allowed), CATEGORY_UNKNOWN)
    matrix["previous_course_status"] = pd.Categorical(values, categories=allowed)
    return matrix[[*base_features, "previous_course_status"]]


def prepare_augmented_folds(train, base_features):
    """Use the official temporal masks, targets, fit-only weights and levels."""
    prepared = []
    for fold in official.TEMPORAL_FOLDS:
        fit_rows = train["part_id"].le(fold["train_through"])
        valid_rows = train["part_id"].between(fold["valid_from"], fold["valid_through"])
        fit, valid = train.loc[fit_rows], train.loc[valid_rows]
        levels = learn_augmented_levels(fit)
        prepared.append({
            **fold,
            "fit_X": prepare_augmented_matrix(fit, levels, base_features),
            "valid_X": prepare_augmented_matrix(valid, levels, base_features),
            "fit_grade": pd.to_numeric(fit[TARGET_GRADE]).to_numpy(dtype="float64"),
            "valid_grade": pd.to_numeric(valid[TARGET_GRADE]).to_numpy(dtype="float64"),
            "fit_fail": pd.to_numeric(fit[TARGET_FAIL]).to_numpy(dtype="int64"),
            "valid_fail": pd.to_numeric(valid[TARGET_FAIL]).to_numpy(dtype="int64"),
            "fit_weight": training_weights(fit).to_numpy(dtype="float32"),
            "fit_rows": int(fit_rows.sum()), "valid_rows": int(valid_rows.sum()),
        })
    return prepared


def train_augmented_one(
    fit_X, fit_y, fit_weight, parameters, valid_X=None, valid_y=None,
    num_boost_round=official.MAX_BOOST_ROUNDS,
):
    """Match official LightGBM training, explicitly naming the sixth category."""
    categorical = [*CATEGORICAL_FEATURES, "previous_course_status"]
    train_set = lgb.Dataset(
        fit_X, label=fit_y, weight=fit_weight,
        categorical_feature=categorical, free_raw_data=False,
    )
    valid_sets = None
    callbacks = [lgb.log_evaluation(period=0)]
    if valid_X is not None:
        valid_set = lgb.Dataset(
            valid_X, label=valid_y, reference=train_set,
            categorical_feature=categorical, free_raw_data=False,
        )
        valid_sets = [valid_set]
        callbacks.append(lgb.early_stopping(
            official.EARLY_STOPPING_ROUNDS,
            first_metric_only=True, verbose=False,
        ))
    return lgb.train(
        parameters, train_set, num_boost_round=num_boost_round,
        valid_sets=valid_sets, callbacks=callbacks,
    )


def tune_augmented_model(prepared_folds, task):
    """Use official candidates, early stopping, metrics and selection logic."""
    reports = []
    for candidate in official.PARAMETER_CANDIDATES:
        fold_reports = []
        for fold in prepared_folds:
            if task == "grade":
                fit_y, valid_y = fold["fit_grade"], fold["valid_grade"]
                task_params = {"objective": "regression", "metric": "l1"}
                metric_function, primary_name = official.regression_metrics, "mae"
            else:
                fit_y, valid_y = fold["fit_fail"], fold["valid_fail"]
                task_params = {"objective": "binary", "metric": "binary_logloss"}
                metric_function, primary_name = official.classification_metrics, "log_loss"
            params = {**official.shared_parameters(candidate), **task_params}
            model = train_augmented_one(
                fold["fit_X"], fit_y, fold["fit_weight"], params,
                fold["valid_X"], valid_y,
            )
            prediction = model.predict(fold["valid_X"], num_iteration=model.best_iteration)
            metrics = metric_function(valid_y, prediction)
            fold_reports.append({
                "fold": fold["name"], "fit_rows": fold["fit_rows"],
                "valid_rows": fold["valid_rows"],
                "best_iteration": int(model.best_iteration), "metrics": metrics,
            })
            print(
                f"{task} | {candidate['name']} | {fold['name']} | "
                f"best_iteration={model.best_iteration} | score={metrics[primary_name]:.6f}",
                flush=True,
            )
        reports.append({
            "candidate": candidate, "folds": fold_reports,
            "mean_primary_metric": float(np.mean([
                report["metrics"][primary_name] for report in fold_reports
            ])),
            "mean_best_iteration": int(round(np.mean([
                report["best_iteration"] for report in fold_reports
            ]))),
        })
    return min(reports, key=lambda report: report["mean_primary_metric"]), reports


def _input_sha256():
    paths = [
        TEMPORAL_TRAIN_FEATURES_PATH_V2, TEMPORAL_TEST_FEATURES_PATH_V2,
        FEATURE_OUTPUT_DIR / "temporal_train_features.parquet",
        FEATURE_OUTPUT_DIR / "temporal_test_features.parquet",
        CLEAN_REGISTRATION_ROSTER_PATH_V2, CLEAN_STUDENT_COURSE_PATH_V2,
        PROJECT_ROOT / "src/features/student_course_status.py",
        PROJECT_ROOT / "src/experiments/previous_course_status_data.py",
        PROJECT_ROOT / "src/experiments/previous_course_status_training.py",
        PROJECT_ROOT / "src/modeling/train_models.py",
        PROJECT_ROOT / "src/modeling/training_config.py",
        PROJECT_ROOT / "src/features/feature_contract.py",
    ]
    return {path.relative_to(PROJECT_ROOT).as_posix(): file_sha256(path) for path in paths}


def _load_tables():
    columns = list(dict.fromkeys([
        "student_course_id", "student_id", "degree_id", "course_id", "part_id",
        "attempt_number", TARGET_GRADE, TARGET_FAIL, *BASE_FEATURES,
        "previous_course_status",
    ]))
    train = pd.read_parquet(FEATURE_OUTPUT_DIR / "temporal_train_features.parquet", columns=columns)
    test = pd.read_parquet(FEATURE_OUTPUT_DIR / "temporal_test_features.parquet", columns=columns)
    require_current_features(train.attrs)
    require_current_features(test.attrs)
    if train["part_id"].max() >= test["part_id"].min():
        raise ValueError("Training and holdout temporal cutoffs overlap")
    if train["previous_course_status"].isna().any() or test["previous_course_status"].isna().any():
        raise ValueError("Experimental status must be explicit on every model row")
    return train, test


def load_variant(variant, *, signature=None):
    """Load only a matching experimental feature/model contract and hashes."""
    base_features = VARIANTS[variant]
    root = EXPERIMENT_MODEL_DIR / variant
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    expected = [*base_features, "previous_course_status"]
    if metadata.get("feature_contract", {}).get("model_features") != expected:
        raise ValueError(f"{variant} feature contract changed")
    if metadata.get("input_sha256") != (signature if signature is not None else _input_sha256()):
        raise ValueError(f"{variant} source/input signature changed")
    for filename, digest in metadata["artifact_sha256"].items():
        if file_sha256(root / filename) != digest:
            raise ValueError(f"{variant} artifact changed: {filename}")
    grade = lgb.Booster(model_file=str(root / "grade_model.txt"))
    fail = lgb.Booster(model_file=str(root / "fail_model.txt"))
    if grade.feature_name() != expected or fail.feature_name() != expected:
        raise ValueError(f"{variant} LightGBM feature header changed")
    levels = json.loads((root / "category_levels.json").read_text(encoding="utf-8"))
    if levels["previous_course_status"] != [*STATUS_LEVELS, CATEGORY_MISSING, CATEGORY_UNKNOWN]:
        raise ValueError(f"{variant} status category levels changed")
    return grade, fail, levels, metadata


def train_all_variants():
    """Fit both isolated models on the same V2 rows, folds, weights and grid."""
    signature = _input_sha256()
    train, test = _load_tables()
    outputs = {}
    for variant, base_features in VARIANTS.items():
        root = EXPERIMENT_MODEL_DIR / variant
        if (root / "metadata.json").exists():
            outputs[variant] = load_variant(variant, signature=signature)[3]
            print(f"Verified existing {variant} artifact; skipped training", flush=True)
            continue
        print(f"Starting {variant}: {len(base_features)} + 1 features", flush=True)
        prepared = prepare_augmented_folds(train, base_features)
        selections = {}
        for task in ("grade", "fail"):
            best, all_candidates = tune_augmented_model(prepared, task)
            selections[task] = best
            write_json(EVALUATION_OUTPUT_DIR / f"{variant}_{task}_validation.json", {
                "best": best, "all_candidates": all_candidates,
            })
        del prepared
        levels = learn_augmented_levels(train)
        final_x = prepare_augmented_matrix(train, levels, base_features)
        weights = training_weights(train).to_numpy(dtype="float32")
        root.mkdir(parents=True, exist_ok=True)
        metadata = {
            "experiment": "previous_course_status", "variant": variant,
            "dataset_version": "V2",
            "feature_engineering_version": FEATURE_ENGINEERING_VERSION,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "feature_contract": {
                "model_features": [*base_features, "previous_course_status"],
                "numeric_features": [name for name in base_features if name not in CATEGORICAL_FEATURES],
                "categorical_features": [*CATEGORICAL_FEATURES, "previous_course_status"],
                "feature_count": len(base_features) + 1,
            },
            "targets": {"grade": TARGET_GRADE, "fail": TARGET_FAIL},
            "training_as_of_part": int(train["part_id"].max()),
            "train_rows": len(train), "test_rows": len(test),
            "temporal_folds": official.TEMPORAL_FOLDS,
            "training_weight": {"before_2022": .25, "from_2022": 1., "fit_only": True},
            "candidate_grid": official.PARAMETER_CANDIDATES,
            "seed": official.SEED, "max_boost_rounds": official.MAX_BOOST_ROUNDS,
            "early_stopping_rounds": official.EARLY_STOPPING_ROUNDS,
            "holdout_history_protocol": "existing_V2_features_sequential_roll_forward",
            "status_source": "V2 registration roster + V2 cleaned graded marks",
            "input_sha256": signature,
        }
        for task, filename, target in [
            ("grade", "grade_model.txt", TARGET_GRADE),
            ("fail", "fail_model.txt", TARGET_FAIL),
        ]:
            selected = selections[task]
            task_params = ({"objective": "regression", "metric": "l1"} if task == "grade"
                           else {"objective": "binary", "metric": "binary_logloss"})
            params = {**official.shared_parameters(selected["candidate"]), **task_params}
            y = pd.to_numeric(train[target]).to_numpy(dtype="float64" if task == "grade" else "int64")
            rounds = max(1, selected["mean_best_iteration"])
            model = train_augmented_one(final_x, y, weights, params, num_boost_round=rounds)
            if model.feature_name() != [*base_features, "previous_course_status"]:
                raise ValueError(f"{variant} {task} fitted feature order changed")
            model.save_model(str(root / filename))
            metadata[task] = {
                "selected_candidate": selected, "parameters": params,
                "final_boost_rounds": rounds,
                "feature_importance": official.feature_importance(model),
            }
            print(f"Saved {variant} {task} ({rounds} rounds)", flush=True)
        save_category_levels(levels, root / "category_levels.json")
        metadata["artifact_sha256"] = {
            filename: file_sha256(root / filename)
            for filename in ("grade_model.txt", "fail_model.txt", "category_levels.json")
        }
        write_json(root / "metadata.json", metadata)
        outputs[variant] = metadata
    return outputs
