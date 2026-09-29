"""Run the isolated previous-course-status experiment without promotion."""

import json

import pandas as pd

from src.experiments.previous_course_status_data import (
    EVALUATION_OUTPUT_DIR, build_experimental_datasets, build_status_history,
)
from src.experiments.previous_course_status_evaluation import evaluate_holdout
from src.recommendation_experiments.previous_course_status_inference import run_student_comparison
from src.experiments.previous_course_status_training import (
    EXPERIMENT_MODEL_DIR, train_all_variants,
)
from src.features.frozen_history import file_sha256
from src.paths import (
    CATEGORY_LEVELS_PATH_V2, CLEAN_REGISTRATION_ROSTER_PATH_V2,
    CLEAN_STUDENT_COURSE_PATH_V2, FAIL_MODEL_PATH_V2,
    FROZEN_HISTORY_DIR_V2, GRADE_MODEL_PATH_V2, MODEL_METADATA_PATH_V2,
    PROJECT_ROOT, TEMPORAL_TEST_FEATURES_PATH_V2,
    TEMPORAL_TRAIN_FEATURES_PATH_V2,
)


def _protected_paths():
    paths = [
        GRADE_MODEL_PATH_V2, FAIL_MODEL_PATH_V2, MODEL_METADATA_PATH_V2,
        CATEGORY_LEVELS_PATH_V2, TEMPORAL_TRAIN_FEATURES_PATH_V2,
        TEMPORAL_TEST_FEATURES_PATH_V2,
        PROJECT_ROOT / "src/features/feature_contract.py",
        PROJECT_ROOT / "src/features/frozen_history.py",
        PROJECT_ROOT / "src/features/build_frozen_history.py",
        PROJECT_ROOT / "src/paths.py",
    ]
    paths.extend(path for path in FROZEN_HISTORY_DIR_V2.rglob("*") if path.is_file())
    paths.extend((PROJECT_ROOT / "src/recommendation").glob("*.py"))
    return sorted(set(paths))


def verify_protected_files():
    """Compare official hashes captured before this experiment's first run."""
    before_path = EVALUATION_OUTPUT_DIR / "protected_before.json"
    if not before_path.exists():
        EVALUATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        before = {
            path.relative_to(PROJECT_ROOT).as_posix(): file_sha256(path)
            for path in _protected_paths()
        }
        before_path.write_text(json.dumps(before, indent=2), encoding="utf-8")
    before = json.loads(before_path.read_text(encoding="utf-8"))
    after = {name: file_sha256(PROJECT_ROOT / name) for name in before}
    changed = [name for name in before if after[name] != before[name]]
    (EVALUATION_OUTPUT_DIR / "protected_after.json").write_text(
        json.dumps(after, indent=2), encoding="utf-8"
    )
    result = {
        "protected_files": len(before), "changed": changed,
        "official_artifacts_modified": bool(changed),
        "official_recommendation_modified": any(
            name.startswith("src/recommendation/") for name in changed
        ),
    }
    (EVALUATION_OUTPUT_DIR / "isolation_verification.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    if changed:
        raise ValueError(f"Protected official files changed: {changed}")
    return result


def main():
    verify_protected_files()
    build_experimental_datasets()
    train_all_variants()
    evaluate_holdout()
    roster = pd.read_parquet(CLEAN_REGISTRATION_ROSTER_PATH_V2, columns=[
        "student_course_id", "student_id", "course_id", "part_id", "finish_status",
    ])
    graded = pd.read_parquet(CLEAN_STUDENT_COURSE_PATH_V2, columns=[
        "student_course_id", "student_id", "course_id", "part_id", "final_mark",
    ])
    history = build_status_history(roster, graded)
    comparison = run_student_comparison(
        status_history=history, model_dir=EXPERIMENT_MODEL_DIR,
        debug_dir=PROJECT_ROOT / "data/debug/previous_course_status",
    )
    isolation = verify_protected_files()
    print({
        "candidate_count": comparison["candidate_count"],
        "matching_plan_count": comparison["plan_aware"]["plan_count"],
        "protected_changed": isolation["changed"],
    })


if __name__ == "__main__":
    main()
