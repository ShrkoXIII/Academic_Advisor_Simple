"""Load only the official V2 baseline and its isolated base serving history."""
import json

from src.features.feature_contract import (
    BASE_FEATURES, CATEGORICAL_FEATURES, CATEGORY_MISSING, CATEGORY_UNKNOWN,
    NUMERIC_FEATURES, load_category_levels, require_current_features,
)
from src.features.frozen_history import file_sha256, load_frozen_history
from src.grade_scale import GradeScale
from src.paths import (
    CATEGORY_LEVELS_PATH_V2, FAIL_MODEL_PATH_V2, FROZEN_HISTORY_DIR_V2,
    GRADE_MODEL_PATH_V2, GRADE_SCALE_PATH, MODEL_METADATA_PATH_V2,
)


def model_training_provenance(metadata):
    """Keep evidence of the training cutoff distinct from serving history."""
    if "training_as_of_part" in metadata:
        return {"training_as_of_part": int(metadata["training_as_of_part"]), "basis": "explicit_model_metadata"}
    cutoff = metadata.get("course_history", {}).get("initial_history_cutoff")
    if cutoff is not None:
        return {"training_as_of_part": int(cutoff), "basis": "model_metadata.course_history.initial_history_cutoff"}
    # Preserve the public helper's interpretation of historical metadata.
    cutoff = metadata.get("course_history", {}).get("test_state_frozen_after_part")
    if cutoff is not None:
        return {"training_as_of_part": int(cutoff), "basis": "legacy_model_metadata.course_history.test_state_frozen_after_part"}
    if metadata.get("history_protocol", {}).get("holdout_2025") == "frozen after 2024":
        return {"training_as_of_part": 20243, "basis": "inferred_from_legacy_model_metadata.history_protocol.holdout_2025"}
    return {"training_as_of_part": None, "basis": "not_recorded_in_model_metadata"}


def load_recommendation_artifacts(*, history_as_of_part, history_root=None):
    """Return grade/fail models, categories, GradeScale, base history and provenance."""
    import lightgbm as lgb

    artifact_paths = {
        "grade_model": GRADE_MODEL_PATH_V2, "fail_model": FAIL_MODEL_PATH_V2,
        "category_levels": CATEGORY_LEVELS_PATH_V2, "model_metadata": MODEL_METADATA_PATH_V2,
        "grade_scale": GRADE_SCALE_PATH,
    }
    for path in artifact_paths.values():
        if not path.is_file():
            raise FileNotFoundError(f"Required Recommendation V2 artifact missing: {path}")
    metadata = json.loads(MODEL_METADATA_PATH_V2.read_text(encoding="utf-8"))
    require_current_features(metadata)
    contract = metadata.get("feature_contract", {})
    if (contract.get("model_features") != BASE_FEATURES
            or contract.get("numeric_features") != NUMERIC_FEATURES
            or contract.get("categorical_features") != CATEGORICAL_FEATURES
            or contract.get("feature_count") != len(BASE_FEATURES)):
        raise ValueError("Official V2 metadata must declare the ordered 47 BASE_FEATURES contract.")
    if metadata.get("dataset_version", "V2") != "V2":
        raise ValueError("Official model metadata is not V2.")
    if metadata.get("targets", {}).get("grade_regressor") != "final_mark":
        raise ValueError("Official V2 grade model target must be final_mark.")
    for task, candidate in [("grade_regressor", "capacity_63"), ("fail_risk_classifier", "balanced_31")]:
        name = metadata.get(task, {}).get("selected_candidate", {}).get("candidate", {}).get("name")
        if name != candidate:
            raise ValueError(f"Official V2 {task} candidate must be {candidate}.")
    expected_paths = {
        "grade_model": "models/grade_regressor_v2.txt", "fail_model": "models/fail_risk_classifier_v2.txt",
        "category_levels": "data/artifacts/category_levels_v2.json", "model_metadata": "models/model_metadata_v2.json",
    }
    if any(metadata.get("artifacts", {}).get(key) != value for key, value in expected_paths.items()):
        raise ValueError("Official metadata artifact paths must identify the V2 baseline.")
    levels = load_category_levels(CATEGORY_LEVELS_PATH_V2)
    if set(levels) != set(CATEGORICAL_FEATURES) or any(
        not isinstance(values, list) or not all(isinstance(value, str) for value in values)
        or len(values) != len(set(values))
        or CATEGORY_MISSING not in values or CATEGORY_UNKNOWN not in values
        for values in levels.values()
    ):
        raise ValueError("Official V2 category levels do not match the categorical contract.")
    grade = lgb.Booster(model_file=str(GRADE_MODEL_PATH_V2))
    fail = lgb.Booster(model_file=str(FAIL_MODEL_PATH_V2))
    if grade.feature_name() != BASE_FEATURES or fail.feature_name() != BASE_FEATURES:
        raise ValueError("Official V2 models must have the ordered BASE_FEATURES contract.")
    grade_scale = GradeScale.from_parquet(GRADE_SCALE_PATH)
    course, _, history_provenance = load_frozen_history(
        history_as_of_part,
        root=FROZEN_HISTORY_DIR_V2 if history_root is None else history_root,
        dataset_version="V2",
    )
    provenance = {
        "dataset_version": "V2", "feature_engineering_version": metadata["feature_engineering_version"],
        "grade_model_target": "final_mark", "expected_points_method": "predicted_mark_to_grade_scale",
        "grade_candidate": "capacity_63", "fail_candidate": "balanced_31",
        "model_created_at_utc": metadata.get("created_at_utc"),
        "history_as_of_part": course.as_of_part, "history": history_provenance,
        "training": {"grade": model_training_provenance(metadata), "fail_risk": model_training_provenance(metadata)},
        **{key: {"path": str(path.resolve()), "sha256": file_sha256(path)}
           for key, path in artifact_paths.items()},
    }
    provenance["artifact_sha256"] = {path.name: provenance[key]["sha256"] for key, path in artifact_paths.items()}
    return grade, fail, levels, grade_scale, course, metadata, provenance
