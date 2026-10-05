"""Original temporal early-stopping validation with the frozen official candidate."""
import json

import numpy as np
import pandas as pd

from src.features.feature_contract import learn_category_levels, prepare_model_matrix
from src.grade_scale import GradeScale
from src.modeling import train_models as official
from src.modeling.training_config import training_weights
from src.paths import GRADE_SCALE_PATH, MODEL_METADATA_PATH_V2
from .attempt_number_core import OUTPUT_DIR, VARIANTS, transform_matrix, write_json, row_fingerprint
from .attempt_number_analysis import subsets


def original_validation(train):
    """No candidate search; same 900-round maximum and 75-round stopping patience."""
    metadata = json.loads(MODEL_METADATA_PATH_V2.read_text())
    scale = GradeScale.from_parquet(GRADE_SCALE_PATH)
    results, iterations = [], []
    for fold in official.TEMPORAL_FOLDS:
        fit = train[train.part_id.le(fold["train_through"])]
        valid = train[train.part_id.between(fold["valid_from"], fold["valid_through"])]
        levels = learn_category_levels(fit)
        fit_x, valid_x = prepare_model_matrix(fit, levels), prepare_model_matrix(valid, levels)
        weights = training_weights(fit).to_numpy(dtype="float32")
        for variant in VARIANTS:
            tx, vx = transform_matrix(fit_x, variant), transform_matrix(valid_x, variant)
            predicted = {}
            for task, target, section in [("grade", "final_mark", "grade_regressor"), ("fail", "is_fail", "fail_risk_classifier")]:
                print(f"ORIGINAL CV {fold['name']} {variant} {task}", flush=True)
                model = official.train_one(tx, pd.to_numeric(fit[target]).to_numpy(
                    dtype="float64" if task == "grade" else "int64"), weights,
                    metadata[section]["parameters"], vx, pd.to_numeric(valid[target]).to_numpy(
                    dtype="float64" if task == "grade" else "int64"))
                predicted[task] = np.clip(model.predict(vx, num_iteration=model.best_iteration, num_threads=4), 0, 100 if task == "grade" else 1)
                iterations.append({"fold": fold["name"], "variant": variant, "task": task,
                                   "best_iteration": int(model.best_iteration),
                                   "fit_rows": len(fit), "valid_rows": len(valid),
                                   "fit_fingerprint": row_fingerprint(fit), "valid_fingerprint": row_fingerprint(valid)})
                del model
            points, _ = scale.convert(predicted["grade"], valid.grade_version_id)
            for subset, mask in subsets(valid).items():
                results.append({"cohort": fold["name"], "variant": variant, "subset": subset,
                                "rows": int(mask.sum()),
                                **official.regression_metrics(valid.loc[mask,"final_mark"], predicted["grade"][mask]),
                                **official.classification_metrics(valid.loc[mask,"is_fail"], predicted["fail"][mask]),
                                "points_mae": float(np.abs(points[mask]-valid.loc[mask,"points"].to_numpy(dtype=float)).mean())})
    pd.DataFrame(results).to_csv(OUTPUT_DIR / "original_validation_metrics.csv", index=False)
    write_json(OUTPUT_DIR / "original_validation_protocol.json", {
        "max_boost_rounds": official.MAX_BOOST_ROUNDS, "early_stopping_rounds": official.EARLY_STOPPING_ROUNDS,
        "purpose": "Same production validation protocol; diagnostic only; no change to frozen final 114/112 rounds or feature experiments.",
        "iterations": iterations})
