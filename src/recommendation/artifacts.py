"""Load and validate the saved models and frozen serving history."""
from hashlib import sha256
import json

from src.experiments.specialty_history import FrozenSpecialtyHistory
from src.features.feature_contract import (
    BASE_FEATURES, load_category_levels, require_current_features,
)
from src.features.frozen_history import load_frozen_history
from src.paths import (
    CATEGORY_LEVELS_PATH, FAIL_MODEL_PATH, MODEL_METADATA_PATH,
    DEGREE_POINTS_SELECTED_MODEL_PATH, DEGREE_POINTS_CATEGORY_LEVELS_PATH,
    DEGREE_POINTS_EXPERIMENT_METADATA_PATH,
)


def model_training_provenance(metadata):
    """Keep legacy cutoff evidence distinct from the selected serving history."""
    if "training_as_of_part" in metadata:
        return {"training_as_of_part": int(metadata["training_as_of_part"]), "basis": "explicit_model_metadata"}
    cutoff = metadata.get("course_history", {}).get("test_state_frozen_after_part")
    if cutoff is not None:
        return {"training_as_of_part": int(cutoff), "basis": "legacy_model_metadata.course_history.test_state_frozen_after_part"}
    if metadata.get("history_protocol", {}).get("holdout_2025") == "frozen after 2024":
        return {"training_as_of_part": 20243, "basis": "inferred_from_legacy_model_metadata.history_protocol.holdout_2025"}
    return {"training_as_of_part": None, "basis": "not_recorded_in_model_metadata"}


def load_recommendation_artifacts(*, history_as_of_part, history_root=None):
    """Return constructor components for the validated serving artifacts."""
    import lightgbm as lgb

    metadata = json.loads(DEGREE_POINTS_EXPERIMENT_METADATA_PATH.read_text(encoding="utf-8"))
    fail_metadata = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
    require_current_features(metadata)
    require_current_features(fail_metadata)
    if metadata["selected_variant"]["target"] != "points":
        raise ValueError("The selected artifact must predict points directly.")
    course_history, specialty_history, history_provenance = load_frozen_history(
        history_as_of_part, root=history_root,
        specialty_history_type=FrozenSpecialtyHistory,
    )
    points = lgb.Booster(model_file=str(DEGREE_POINTS_SELECTED_MODEL_PATH))
    fail = lgb.Booster(model_file=str(FAIL_MODEL_PATH))
    if points.feature_name() != metadata["feature_contract"]["model_features"]:
        raise ValueError("Expected Points model and metadata feature order disagree.")
    if fail.feature_name() != fail_metadata["feature_contract"]["model_features"]:
        raise ValueError("Fail model and metadata feature order disagree.")
    if fail.feature_name() != BASE_FEATURES:
        raise ValueError("Current failure feature contract differs from the saved model.")
    provenance = {
        "selected_variant": metadata["selected_variant"]["name"],
        "model_created_at_utc": metadata["created_at_utc"],
        "experiment_signature": metadata["experiment_signature"],
        "feature_engineering_version": metadata["feature_engineering_version"],
        "history_as_of_part": specialty_history.as_of_part,
        "history": history_provenance,
        "training": {
            "expected_points": model_training_provenance(metadata),
            "fail_risk": model_training_provenance(fail_metadata),
        },
        "artifact_sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in [
            DEGREE_POINTS_SELECTED_MODEL_PATH, DEGREE_POINTS_CATEGORY_LEVELS_PATH,
            FAIL_MODEL_PATH, CATEGORY_LEVELS_PATH,
            DEGREE_POINTS_EXPERIMENT_METADATA_PATH, MODEL_METADATA_PATH,
        ]},
    }
    return (points, fail, load_category_levels(DEGREE_POINTS_CATEGORY_LEVELS_PATH),
            load_category_levels(CATEGORY_LEVELS_PATH), course_history,
            specialty_history, metadata, provenance)
