"""Entry point for the explicitly authorized, isolated 33-feature experiment."""
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse

from src.experiments.course_only_evaluation import capture_protected_files, run_comparisons, verify_protected_files
from src.experiments.course_only_training import load_experiment, train_experiment
from src.recommendation.engine import AcademicPlanRecommender


def main():
    parser = argparse.ArgumentParser(description="Research only: fit 33-feature models and compare exact-credit recommendations; no promotion.")
    parser.add_argument("--skip-training", action="store_true", help="Load only experimental models with matching source/input hashes.")
    parser.add_argument("--repeats", type=int, default=3, help="Alternating warm runtime repetitions per case.")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    capture_protected_files()
    if not args.skip_training:
        train_experiment()
    experimental = load_experiment()
    engine = AcademicPlanRecommender.load(history_as_of_part=20243, num_threads=4)
    primary, batch = run_comparisons(engine, experimental, repeats=args.repeats)
    verified = verify_protected_files()
    from src.experiments.course_only_report import build_report
    build_report(experimental[3], primary, batch, verified)


if __name__ == "__main__":
    main()
