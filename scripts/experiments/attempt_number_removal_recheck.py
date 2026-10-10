"""Isolated fixed-configuration ablation of personal attempt in 47/33 models."""
import argparse
from datetime import datetime, timezone
import json
import platform
from time import perf_counter

import lightgbm as lgb
import numpy as np
import pandas as pd
import sklearn

from src.experiments import attempt_number_core as core
from src.experiments.attempt_number_training import load_frames
from src.features.feature_contract import (
    BASE_FEATURES, learn_category_levels, load_category_levels,
    prepare_model_matrix, save_category_levels,
)
from src.features.frozen_history import file_sha256
from src.grade_scale import GradeScale
from src.modeling import train_models as official
from src.modeling.training_config import training_weights
from src.paths import (
    CATEGORY_LEVELS_PATH_V2, COURSE_ONLY_MODEL_DIR, EVALUATION_DIR,
    FAIL_MODEL_PATH_V2, GRADE_MODEL_PATH_V2, GRADE_SCALE_PATH,
    MODEL_DIR, MODEL_METADATA_PATH_V2, PROJECT_ROOT,
)


def families():
    """Read each existing model's configuration; never tune on the holdout."""
    result = []
    for name, metadata_path, categories, grade_path, fail_path, task_keys in [
        ("47_plan_aware", MODEL_METADATA_PATH_V2, CATEGORY_LEVELS_PATH_V2,
         GRADE_MODEL_PATH_V2, FAIL_MODEL_PATH_V2,
         {"grade": "grade_regressor", "fail": "fail_risk_classifier"}),
        ("33_course_only", COURSE_ONLY_MODEL_DIR / "model_metadata.json",
         COURSE_ONLY_MODEL_DIR / "category_levels.json",
         COURSE_ONLY_MODEL_DIR / "grade_regressor.txt",
         COURSE_ONLY_MODEL_DIR / "fail_risk_classifier.txt",
         {"grade": "grade", "fail": "fail"}),
    ]:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        features = metadata["feature_contract"]["model_features"]
        expected_count = int(name.split("_")[0])
        if (len(features) != expected_count or "attempt_number" not in features
                or features != [f for f in BASE_FEATURES if f in features]):
            raise ValueError(f"Unexpected feature contract: {name}")
        result.append({"name": name, "features": features,
                       "categories": categories, "models": {"grade": grade_path, "fail": fail_path},
                       "config": {task: {"parameters": metadata[key]["parameters"],
                                          "rounds": metadata[key]["final_boost_rounds"]}
                                  for task, key in task_keys.items()},
                       "reference_sha256": {p.relative_to(PROJECT_ROOT).as_posix(): file_sha256(p)
                                            for p in [metadata_path, categories, grade_path, fail_path]}})
    return result


def evaluate(frame, family, cohort, scale, *, bootstrap):
    """Paired losses by attempt group; positive loss delta means removal hurts."""
    rows, intervals = [], []
    for variant in ["A", "C"]:
        frame[f"points_{variant}"], _ = scale.convert(frame[f"grade_{variant}"], frame.grade_version_id)
    for subset, mask in {
        "overall": np.ones(len(frame), dtype=bool), "first": frame.attempt_number.eq(1),
        "repeat": frame.attempt_number.gt(1), "second": frame.attempt_number.eq(2),
        "third_plus": frame.attempt_number.ge(3),
    }.items():
        part = frame.loc[mask]
        if part.empty:
            continue
        losses = {}
        for variant in ["A", "C"]:
            grade, fail, points = (part[f"{task}_{variant}"].to_numpy() for task in ["grade", "fail", "points"])
            actual_fail = part.is_fail.to_numpy(dtype=float)
            clipped = np.clip(fail, 1e-7, 1 - 1e-7)
            losses[variant] = {
                "mae": np.abs(grade - part.final_mark.to_numpy(dtype=float)),
                "points_mae": np.abs(points - part.points.to_numpy(dtype=float)),
                "log_loss": -(actual_fail * np.log(clipped) + (1 - actual_fail) * np.log1p(-clipped)),
            }
            rows.append({"family": family, "cohort": cohort, "subset": subset, "variant": variant,
                         "rows": len(part), "students": part.student_id.nunique(),
                         **official.regression_metrics(part.final_mark, grade),
                         **official.classification_metrics(part.is_fail, fail),
                         "points_mae": float(losses[variant]["points_mae"].mean()),
                         "points_rmse": float(np.sqrt(np.square(points - part.points.to_numpy(dtype=float)).mean()))})
        if bootstrap and subset in ["overall", "repeat", "third_plus"]:
            for metric in losses["A"]:
                intervals.append({"family": family, "cohort": cohort, "subset": subset,
                                  "metric": metric,
                                  **core.paired_cluster_interval(part.student_id, losses["C"][metric] - losses["A"][metric])})
    return rows, intervals


def run(output_name):
    if not output_name.startswith("attempt_number_removal_") or not all(c.isalnum() or c == "_" for c in output_name):
        raise ValueError("Use a simple attempt_number_removal_... output name.")
    output = EVALUATION_DIR / "experiments" / output_name
    models = MODEL_DIR / "experiments" / output_name
    if output.exists() or models.exists():
        raise FileExistsError("Use a new output name; existing evidence is preserved.")
    core.OUTPUT_DIR, core.EXPERIMENT_MODEL_DIR = output, models
    core.capture_protected()
    specs = families()
    provenance = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "lightgbm": lgb.__version__,
        "numpy": np.__version__, "pandas": pd.__version__, "sklearn": sklearn.__version__,
        "experiment_script_sha256": file_sha256(__file__), "seed": official.SEED,
        "variants": {"A": "attempt_number retained", "C": "only attempt_number dropped"},
        "configuration": "Existing pre-2025 choices and tree counts fixed for both variants; no tuning",
        "history": "Read existing V2 temporal features without rebuilding or changing Frozen History",
        "holdout_limitation": "2025 holdout was previously inspected; this is a fixed-config recheck, not a new blind holdout",
        "recommendation_quality_evaluated": False, "promotion": False,
        "families": [{**s, "categories": str(s["categories"]),
                      "models": {k: str(v) for k, v in s["models"].items()}} for s in specs],
    }
    core.write_json(output / "provenance.json", provenance)
    started = perf_counter()
    try:
        train, test = load_frames()
        core.write_json(output / "rows.json", {
            "train_rows": len(train), "test_rows": len(test),
            "train_through": int(train.part_id.max()), "holdout_parts": sorted(test.part_id.unique()),
            "train_fingerprint": core.row_fingerprint(train), "test_fingerprint": core.row_fingerprint(test),
        })
        jobs = [(f["name"], train.loc[train.part_id.le(f["train_through"])],
                 train.loc[train.part_id.between(f["valid_from"], f["valid_through"])]) for f in official.TEMPORAL_FOLDS]
        jobs.append(("holdout", train, test))
        metrics, intervals, reproduction, importance = [], [], [], []
        scale = GradeScale.from_parquet(GRADE_SCALE_PATH)
        for family in specs:
            for cohort, fit, valid in jobs:
                levels = learn_category_levels(fit)
                fit_x = prepare_model_matrix(fit, levels, model_features=family["features"])
                valid_x = prepare_model_matrix(valid, levels, model_features=family["features"])
                weight = training_weights(fit).to_numpy(dtype="float32")
                directory = models / family["name"] / cohort
                save_category_levels(levels, directory / "category_levels.json")
                predictions = valid[[*core.ROW_KEYS, "attempt_number", "final_mark", "is_fail", "points", "grade_version_id"]].copy()
                for variant in ["A", "C"]:
                    tx, vx = core.transform_matrix(fit_x, variant), core.transform_matrix(valid_x, variant)
                    for task, target in [("grade", "final_mark"), ("fail", "is_fail")]:
                        config = family["config"][task]
                        print(f"FIT {family['name']} {cohort} {variant} {task}: {len(tx)} rows / {len(tx.columns)} features / {config['rounds']} rounds", flush=True)
                        model = official.train_one(tx, fit[target].to_numpy(dtype="float64" if task == "grade" else "int64"),
                                                   weight, config["parameters"], num_boost_round=config["rounds"])
                        if model.feature_name() != list(tx.columns):
                            raise ValueError("Trained feature order differs from matrix.")
                        model_path = directory / f"{variant}_{task}.txt"
                        model.save_model(str(model_path))
                        core.write_json(model_path.with_suffix(".json"), {
                            "sha256": file_sha256(model_path), "features": list(tx.columns), "config": config,
                            "fit_fingerprint": core.row_fingerprint(fit), "valid_fingerprint": core.row_fingerprint(valid),
                        })
                        predictions[f"{task}_{variant}"] = np.clip(model.predict(vx, num_threads=4), 0, 100 if task == "grade" else 1)
                        if variant == "A" and cohort == "holdout":
                            reference_x = prepare_model_matrix(valid, load_category_levels(family["categories"]), model_features=family["features"])
                            reference = lgb.Booster(model_file=str(family["models"][task]))
                            ref_prediction = np.clip(reference.predict(reference_x, num_threads=4), 0, 100 if task == "grade" else 1)
                            delta = float(np.abs(ref_prediction - predictions[f"{task}_A"]).max())
                            reproduction.append({"family": family["name"], "task": task, "max_absolute_difference": delta})
                            if delta > 1e-9:
                                raise ValueError(f"Baseline failed reproduction: {family['name']} {task}: {delta}")
                            gains = model.feature_importance(importance_type="gain")
                            index = model.feature_name().index("attempt_number")
                            importance.append({"family": family["name"], "task": task,
                                               "attempt_gain_share_percent": float(100 * gains[index] / gains.sum()),
                                               "attempt_gain_rank": int((gains > gains[index]).sum() + 1)})
                        del model
                new_metrics, new_intervals = evaluate(predictions, family["name"], cohort, scale, bootstrap=cohort == "holdout")
                metrics.extend(new_metrics)
                intervals.extend(new_intervals)
                evidence = output / family["name"] / cohort
                evidence.mkdir(parents=True, exist_ok=True)
                predictions.to_parquet(evidence / "predictions.parquet", index=False)
                if cohort == "holdout":
                    for part_id, part in predictions.groupby("part_id"):
                        part_metrics, _ = evaluate(part.copy(), family["name"], str(part_id), scale, bootstrap=False)
                        metrics.extend(part_metrics)
                print(f"DONE {family['name']} {cohort}", flush=True)
        pd.DataFrame(metrics).to_csv(output / "model_metrics.csv", index=False)
        pd.DataFrame(intervals).to_csv(output / "paired_student_bootstrap.csv", index=False)
        core.write_json(output / "baseline_reproduction.json", reproduction)
        core.write_json(output / "feature_importance.json", importance)
        core.write_json(output / "execution.json", {"status": "COMPLETE", "seconds": perf_counter() - started})
    finally:
        print("Isolation:", core.verify_protected(), flush=True)
    print(pd.DataFrame(metrics).query("cohort == 'holdout' and subset == 'overall'")[["family", "variant", "mae", "points_mae", "log_loss", "pr_auc"]].to_string(index=False))
    print(f"Evidence: {output}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-name", default="attempt_number_removal_20261008")
    run(parser.parse_args().output_name)
