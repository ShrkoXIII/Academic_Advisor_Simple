"""Reproducible local throughput test; catalog courses are NOT an eligibility claim."""
import argparse
from datetime import datetime, timezone
import json
import platform
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import pandas as pd

from .paths import (
    RECOMMENDATION_BENCHMARK_DIR, TEMPORAL_TEST_FEATURES_PATH,
    CLEAN_DEGREE_COURSE_PATH, CLEAN_STUDENT_COURSE_PATH,
)
from .recommendation import AcademicPlanRecommender, STUDENT_SNAPSHOT_COLUMNS
from .recommendation_inputs import normalize_candidates
from .recommendation_output import save_recommendations, write_json


def peak_memory_mib():
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in [
                    "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
                    "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage",
                ]
            ]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return counters.PeakWorkingSetSize / 1024**2
    import resource
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / (1024**2 if sys.platform == "darwin" else 1024)


def benchmark(size, output, threads):
    start = perf_counter()
    catalog = pd.read_parquet(CLEAN_DEGREE_COURSE_PATH)
    eligible_sizes = catalog[catalog.course_credits.isin([2, 3])].groupby("degree_id").course_id.nunique()
    degrees = eligible_sizes[eligible_sizes.ge(25)].index
    test = pd.read_parquet(TEMPORAL_TEST_FEATURES_PATH)
    row = test[test.degree_id.isin(degrees) & test.start_agpa_points.ge(3)].sort_values(
        ["degree_id", "student_id", "part_id"], kind="stable",
    ).iloc[0]
    snapshot = row[[*STUDENT_SNAPSHOT_COLUMNS, "part_id"]].to_dict()
    # Deterministic alternating 2/3-hour lists, then remaining catalog courses.
    pool = catalog[catalog.degree_id.eq(row.degree_id) & catalog.course_credits.isin([2, 3])].sort_values("course_id").copy()
    pool["position"] = pool.groupby("course_credits").cumcount()
    raw = pool.sort_values(["position", "course_credits"])[["course_id", "course_credits"]].head(size)
    candidates, report = normalize_candidates(raw, catalog, pd.read_parquet(CLEAN_STUDENT_COURSE_PATH),
                                              row.student_id, row.degree_id, int(row.part_id))
    output.mkdir(parents=True, exist_ok=False)
    raw.to_parquet(output / "input_courses.parquet", index=False)
    # pandas serializes explicit missing histories to JSON null.
    write_json(output / "snapshot.json", json.loads(pd.Series(snapshot).to_json()))
    write_json(output / "import_report.json", report)
    engine = AcademicPlanRecommender.load(num_threads=threads)
    prepared_seconds = perf_counter() - start
    last = perf_counter()

    def progress(count):
        nonlocal last
        if perf_counter() - last >= 15:
            print(f"n={size}: {count:,} plans evaluated", flush=True)
            last = perf_counter()

    result = save_recommendations(
        engine, output, student_snapshot=snapshot, candidate_courses=candidates,
        part_id=int(row.part_id), current_gpa=2.5, credits=18, progress=progress,
    )
    metrics = {
        "candidate_count": size, "credit_distribution": {str(k): int(v) for k, v in raw.course_credits.value_counts().items()},
        "target_credits": 18, "current_gpa": 2.5, "matching_plan_count": result["matching_plan_count"],
        "accepted_plan_count": result["accepted_plan_count"], "scoring_seconds": result["elapsed_seconds"],
        "prepare_seconds": prepared_seconds, "total_seconds": perf_counter() - start,
        "peak_process_memory_mib": peak_memory_mib(), "threads": threads, "batch_size": 2000,
        "platform": platform.platform(), "python": platform.python_version(), "model": result["model"],
        "fixture": "Catalog-based throughput fixture; course eligibility is not established.",
    }
    write_json(output / "benchmark.json", metrics)
    print(json.dumps({k: v for k, v in metrics.items() if k not in ["model", "platform"]}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, choices=[15, 20, 25])
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    output = args.output_dir or RECOMMENDATION_BENCHMARK_DIR / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    if args.size:
        benchmark(args.size, output, args.threads)
    else:
        # Each case has a separate process so peak memory is independent.
        results = []
        for size in [15, 20, 25]:
            child = output / str(size)
            subprocess.run([sys.executable, "-m", "src.benchmark_recommendation", "--size", str(size),
                            "--threads", str(args.threads), "--output-dir", str(child)], check=True)
            results.append(json.loads((child / "benchmark.json").read_text()))
        write_json(output / "benchmark_summary.json", results)
        print(f"Benchmark summary: {output.resolve()}")


if __name__ == "__main__":
    main()
