"""Fixed official V2 parameters, folds and tree budgets for A/B/C."""
import json
from time import perf_counter

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.features.feature_contract import (
    BASE_FEATURES, learn_category_levels, load_category_levels,
    prepare_model_matrix, require_current_features, save_category_levels,
)
from src.features.frozen_history import file_sha256
from src.modeling import train_models as official
from src.modeling.training_config import training_weights
from src.paths import (
    CATEGORY_LEVELS_PATH_V2, FAIL_MODEL_PATH_V2, GRADE_MODEL_PATH_V2,
    MODEL_METADATA_PATH_V2, TEMPORAL_TRAIN_FEATURES_PATH_V2,
    TEMPORAL_TEST_FEATURES_PATH_V2,
)
from .attempt_number_core import (
    EXPERIMENT_MODEL_DIR, OUTPUT_DIR, ROW_KEYS, VARIANTS, row_fingerprint,
    transform_matrix, write_json,
)


def load_frames():
    columns = list(dict.fromkeys([*ROW_KEYS, "faculty_id", "grade_version_id", "points",
                                 "final_mark", "is_fail", "course_outcome_status", *BASE_FEATURES]))
    train = pd.read_parquet(TEMPORAL_TRAIN_FEATURES_PATH_V2, columns=columns)
    test = pd.read_parquet(TEMPORAL_TEST_FEATURES_PATH_V2, columns=columns)
    for frame in [train, test]:
        require_current_features(frame.attrs)
        if frame.student_course_id.isna().any() or frame.student_course_id.duplicated().any():
            raise ValueError("Modeling rows need unique nonmissing student_course_id.")
        if not frame.is_fail.eq(frame.final_mark.lt(50).astype(int)).all():
            raise ValueError("Failure target differs from the official mark<50 definition.")
    if train.part_id.max() != 20243 or sorted(test.part_id.unique()) != [20251, 20252]:
        raise ValueError("Unexpected temporal cutoffs.")
    if set(train.student_course_id) & set(test.student_course_id):
        raise ValueError("Train and holdout record IDs overlap.")
    return train, test


def model_metrics(frame, marks, probability):
    return {**official.regression_metrics(frame.final_mark, marks),
            **official.classification_metrics(frame.is_fail, probability)}


def run_training(train, test, *, resume=False):
    saved = json.loads(MODEL_METADATA_PATH_V2.read_text(encoding="utf-8"))
    signature = {str(p): file_sha256(p) for p in [TEMPORAL_TRAIN_FEATURES_PATH_V2,
                 TEMPORAL_TEST_FEATURES_PATH_V2, MODEL_METADATA_PATH_V2, CATEGORY_LEVELS_PATH_V2]}
    signature["source"] = file_sha256(__file__)
    setup = {"variants": VARIANTS, "input_signature": signature,
             "train_rows": len(train), "test_rows": len(test),
             "train_row_fingerprint": row_fingerprint(train),
             "test_row_fingerprint": row_fingerprint(test),
             "folds": official.TEMPORAL_FOLDS, "seed": official.SEED,
             "frozen_configuration": {t: {"parameters": saved[s]["parameters"],
                                       "rounds": saved[s]["final_boost_rounds"]}
                                      for t, s in [("grade", "grade_regressor"), ("fail", "fail_risk_classifier")]},
             "selection": "preexisting official pre-2025 selection; no retuning or early stopping in A/B/C",
             "descriptive_margins": {"mark_mae": .10, "points_mae": .02, "log_loss": .005},
             "margins_are_product_tolerances": False}
    setup_path = OUTPUT_DIR / "setup.json"
    if setup_path.exists():
        if not resume or json.loads(setup_path.read_text()) != setup:
            raise ValueError("Existing experiment: explicit --resume with matching signature required.")
    else:
        write_json(setup_path, setup)
    jobs = []
    for fold in official.TEMPORAL_FOLDS:
        fit = train.loc[train.part_id.le(fold["train_through"])]
        valid = train.loc[train.part_id.between(fold["valid_from"], fold["valid_through"])]
        jobs.append((fold["name"], fit, valid))
    jobs.append(("holdout", train, test))
    manifest = []
    for name, fit, valid in jobs:
        levels = learn_category_levels(fit)
        fit_x, valid_x = prepare_model_matrix(fit, levels), prepare_model_matrix(valid, levels)
        weight = training_weights(fit).to_numpy(dtype="float32")
        out = OUTPUT_DIR / name
        out.mkdir(parents=True, exist_ok=True)
        save_category_levels(levels, EXPERIMENT_MODEL_DIR / name / "category_levels.json")
        predictions = valid[[*ROW_KEYS, "attempt_number", "points", "final_mark", "is_fail", "grade_version_id", "course_credits"]].copy()
        details = {"fit_rows": len(fit), "valid_rows": len(valid),
                   "fit_fingerprint": row_fingerprint(fit), "valid_fingerprint": row_fingerprint(valid)}
        for variant in VARIANTS:
            tx, vx = transform_matrix(fit_x, variant), transform_matrix(valid_x, variant)
            for task, target in [("grade", "final_mark"), ("fail", "is_fail")]:
                config = setup["frozen_configuration"][task]
                model_path = EXPERIMENT_MODEL_DIR / name / f"{variant}_{task}.txt"
                started = perf_counter()
                if model_path.exists():
                    if not resume:
                        raise FileExistsError(model_path)
                    record = json.loads(model_path.with_suffix(".json").read_text())
                    if file_sha256(model_path) != record["sha256"]:
                        raise ValueError(f"Changed experiment model: {model_path}")
                    model = lgb.Booster(model_file=str(model_path))
                else:
                    print(f"FIT {name} {variant} {task}: {len(tx)} rows, {len(tx.columns)} features, {config['rounds']} rounds", flush=True)
                    model = official.train_one(tx, pd.to_numeric(fit[target]).to_numpy(
                        dtype="float64" if task == "grade" else "int64"), weight,
                        config["parameters"], num_boost_round=config["rounds"])
                    model_path.parent.mkdir(parents=True, exist_ok=True)
                    model.save_model(str(model_path))
                    record = {"sha256": file_sha256(model_path), "seconds": perf_counter() - started,
                              "parameters": config, "features": list(tx.columns), **details}
                    write_json(model_path.with_suffix(".json"), record)
                if model.feature_name() != list(tx.columns):
                    raise ValueError("Model feature order mismatch.")
                prediction = np.clip(model.predict(vx, num_threads=4), 0, 100 if task == "grade" else 1)
                predictions[f"{task}_{variant}"] = prediction
                importance = pd.DataFrame({"feature": model.feature_name(),
                    "gain": model.feature_importance(importance_type="gain"),
                    "splits": model.feature_importance(importance_type="split")}).sort_values("gain", ascending=False)
                importance["gain_share"] = importance.gain / importance.gain.sum()
                importance.to_csv(out / f"importance_{variant}_{task}.csv", index=False)
                print(f"DONE {name} {variant} {task}: {record['seconds']:.1f}s", flush=True)
                del model
        predictions.to_parquet(out / "predictions.parquet", index=False)
        details["metrics"] = {v: model_metrics(valid, predictions[f"grade_{v}"], predictions[f"fail_{v}"]) for v in VARIANTS}
        write_json(out / "metrics.json", details)
        manifest.append({"name": name, **details})
        if name == "holdout":
            official_x = prepare_model_matrix(test, load_category_levels(CATEGORY_LEVELS_PATH_V2))
            reproduction = {}
            for task, path in [("grade", GRADE_MODEL_PATH_V2), ("fail", FAIL_MODEL_PATH_V2)]:
                model = lgb.Booster(model_file=str(path))
                prediction = np.clip(model.predict(official_x, num_threads=4), 0, 100 if task == "grade" else 1)
                difference = np.abs(prediction - predictions[f"{task}_A"])
                reproduction[task] = {"max_absolute_difference": float(difference.max()),
                                      "mean_absolute_difference": float(difference.mean())}
                if difference.max() > 1e-9:
                    raise ValueError(f"Fresh baseline does not reproduce official {task}: {reproduction[task]}")
            write_json(OUTPUT_DIR / "baseline_reproduction.json", reproduction)
    write_json(OUTPUT_DIR / "training_manifest.json", manifest)
    return setup
