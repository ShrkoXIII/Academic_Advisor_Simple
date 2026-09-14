"""Run with: python -m src.recommend_local --help"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

import pandas as pd

from .paths import RECOMMENDATION_RUN_DIR
from .recommendation import AcademicPlanRecommender, resolve_credit_bounds
from .recommendation_inputs import CandidateImportError, load_local_inputs
from .recommendation_output import save_recommendations, write_json


def main():
    parser = argparse.ArgumentParser(description="Rank all plans matching exact credits or an inclusive credit range.")
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--student-id", required=True)
    parser.add_argument("--degree-id", required=True)
    parser.add_argument("--part-id", type=int, required=True)
    parser.add_argument("--credits", type=float)
    parser.add_argument("--min-credits", type=float)
    parser.add_argument("--max-credits", type=float)
    parser.add_argument("--current-gpa", type=float, help="Defaults to snapshot start_agpa_points.")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--batch-size", type=int, default=2000)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    started = perf_counter()
    output = args.output_dir or RECOMMENDATION_RUN_DIR / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output.mkdir(parents=True, exist_ok=False)
    try:
        resolve_credit_bounds(args.credits, args.min_credits, args.max_credits)
        candidates, snapshot, report = load_local_inputs(
            args.candidates, args.student_id, args.degree_id, args.part_id, args.snapshot,
        )
        report["source_file"] = str(args.candidates.resolve())
        report["source_sha256"] = sha256(args.candidates.read_bytes()).hexdigest()
        report["snapshot_source"] = str(args.snapshot.resolve()) if args.snapshot else "local target-semester status and prior history"
        write_json(output / "import_report.json", report)
        write_json(output / "snapshot.json", json.loads(pd.Series(snapshot).to_json(double_precision=15)))
        candidates.to_parquet(output / "candidates.parquet", index=False)
        engine = AcademicPlanRecommender.load(num_threads=args.threads)
        last_message = perf_counter()

        def progress(count):
            nonlocal last_message
            if perf_counter() - last_message >= 10:
                print(f"Evaluated {count:,} plans matching credit bounds...", flush=True)
                last_message = perf_counter()

        result = save_recommendations(
            engine, output, student_snapshot=snapshot, candidate_courses=candidates,
            part_id=args.part_id, current_gpa=args.current_gpa if args.current_gpa is not None else snapshot["start_agpa_points"],
            credits=args.credits, min_credits=args.min_credits, max_credits=args.max_credits,
            batch_size=args.batch_size, progress=progress,
        )
        result["total_elapsed_seconds"] = perf_counter() - started
        result["input"] = report
        write_json(output / "result.json", result)
        print(f"{result['status']}: {result['accepted_plan_count']:,}/{result['matching_plan_count']:,} plans accepted")
        print(f"Results: {output.resolve()}")
    except CandidateImportError as exc:
        write_json(output / "import_report.json", exc.report)
        parser.exit(2, f"{exc}\n")
    except (ValueError, KeyError, FileNotFoundError) as exc:
        write_json(output / "error.json", {"error": str(exc)})
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
