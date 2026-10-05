"""Explicit entry point for the isolated, reproducible attempt-number experiment."""
import argparse
import json
import platform

import lightgbm
import numpy
import pandas
import sklearn

from src.experiments.attempt_number_core import OUTPUT_DIR, capture_protected, verify_protected, write_json
from src.experiments.attempt_number_training import load_frames, run_training
from src.features.frozen_history import file_sha256
from src.paths import PROJECT_ROOT


def source_signature():
    sources = [*sorted((PROJECT_ROOT / "src/experiments").glob("attempt_number_*.py")),
               *sorted((PROJECT_ROOT / "scripts/experiments").glob("attempt_number_*.py")),
               PROJECT_ROOT / "tests/test_attempt_number_experiment.py"]
    return {p.relative_to(PROJECT_ROOT).as_posix(): file_sha256(p) for p in sources}


def save_provenance():
    write_json(OUTPUT_DIR / "execution_provenance.json", {
        "sources": source_signature(),
        "python": platform.python_version(), "platform": platform.platform(),
        "lightgbm": lightgbm.__version__, "numpy": numpy.__version__,
        "pandas": pandas.__version__, "sklearn": sklearn.__version__,
        "code_entrypoint": "python -m scripts.experiments.attempt_number_experiment",
        "promotion": False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true", help="Reuse matching signed experimental models only.")
    parser.add_argument("--report-only", action="store_true", help="Rebuild report from existing evidence.")
    args = parser.parse_args()
    if args.resume:
        prior = json.loads((OUTPUT_DIR / "execution_provenance.json").read_text(encoding="utf-8"))
        if prior["sources"] != source_signature():
            raise ValueError("Experiment sources changed; refuse to reuse signed models.")
    if not args.report_only:
        capture_protected()
        train, test = load_frames()
        run_training(train, test, resume=args.resume)
        from src.experiments.attempt_number_analysis import descriptive_analysis, evaluate_predictions
        from src.experiments.attempt_number_validation import original_validation
        from scripts.experiments.attempt_number_recommendation import run_recommendations
        descriptive_analysis(train, test)
        original_validation(train)
        evaluate_predictions()
        run_recommendations(test)
    verify_protected()
    save_provenance()
    if not (OUTPUT_DIR / "validation_results.json").exists():
        write_json(OUTPUT_DIR / "validation_results.json", {
            "focused": "not recorded; run pytest tests/test_attempt_number_experiment.py tests/test_recommendation_dependency_direction.py -q",
            "full": "not recorded; run pytest -q"})
    from src.experiments.attempt_number_report import build_report
    print(build_report())


if __name__ == "__main__":
    main()
