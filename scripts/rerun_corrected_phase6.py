"""Replace every stale Phase 6 inference observation; never approve a strategy.

Existing reports remain byte-identical. Old search-only results are retained
with their old provenance; every other observation, including censored and
supplemental attempts, gets a fresh isolated worker with its original deadline.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path

from scripts import benchmark_two_stage as benchmark


ROOT = benchmark.ROOT


def classify_old_evidence(report):
    """Only the search branch demonstrably avoids model/GradeScale inputs."""
    search, stale = [], []
    for index, row in enumerate(report["results"]):
        if row["mode"] not in benchmark.MODES:
            raise ValueError("Unknown old measurement mode cannot be retained.")
        (search if row["mode"] == "search" else stale).append(index)
    return {"retained_search_indices": search, "invalidated_indices": stale,
            "invalidated_by_mode": dict(Counter(report["results"][i]["mode"] for i in stale)),
            "search_proof": "measure_case search branch only normalizes inputs and enumerates credit/official constraints; it loads neither models nor GradeScale",
            "old_inference_status": "OLD / INVALIDATED RESULT"}


def corrected_jobs(report):
    """Keep duplicates from separate batches and each independent choice."""
    jobs = []
    for index in classify_old_evidence(report)["invalidated_indices"]:
        row = report["results"][index]
        deadline = row.get("worker_timeout_seconds", report["worker_timeout_seconds"])
        if not math.isfinite(deadline) or deadline <= 0:
            raise ValueError("Old worker deadline must be finite and positive.")
        jobs.append({"old_result_index": index, "size": row["size"],
            "scenario": row["scenario"], "mode": row["mode"],
            "stage1": row.get("stage1_strategy") or row.get("stage1") or "balance_first",
            "final": row.get("final_strategy") or row.get("final") or "balance_first",
            "timeout_seconds": deadline})
    return jobs


def validate_replacement(job, row):
    """Never accept a different workload or unsupported completed inference."""
    if any(row.get(key) != job[key] for key in ("size", "scenario", "mode")):
        raise ValueError("Corrected result does not match its old workload.")
    for key, alias, modes in (("stage1_strategy", "stage1", {"stage1_ranking", "full"}),
                             ("final_strategy", "final", {"final_ranking", "full"})):
        if job["mode"] in modes and (row.get(key) or row.get(alias)) != job[alias]:
            raise ValueError("Corrected strategy does not match its old observation.")
    if row.get("worker_timeout_seconds") != job["timeout_seconds"]:
        raise ValueError("Corrected diagnostic deadline does not match the old observation.")
    if row.get("status") == "completed":
        version = row.get("grade_version_id")
        if (isinstance(version, bool) or not isinstance(version, (int, float))
                or not math.isfinite(version) or version <= 0
                or row.get("grade_scale_version_supported") is not True):
            raise ValueError("Completed inference lacks supported GradeVersion evidence.")
    elif row.get("status") not in {"timeout", "error"}:
        raise ValueError("Unknown corrected observation status.")


def assemble_corrected_results(old, replacements):
    """Corrected aggregate contains no old nonsearch metric values."""
    jobs = corrected_jobs(old)
    indices = [row["old_result_index"] for row in replacements]
    if len(indices) != len(set(indices)) or set(indices) != {row["old_result_index"] for row in jobs}:
        raise ValueError("Every invalidated observation needs exactly one replacement.")
    by_index = {row["old_result_index"]: row for row in replacements}
    output = []
    for index, row in enumerate(old["results"]):
        if row["mode"] == "search":
            value = deepcopy(row)
            value.update(evidence_status="RETAINED / UNAFFECTED SEARCH", old_result_index=index)
        else:
            value = deepcopy(by_index[index])
            validate_replacement(next(job for job in jobs if job["old_result_index"] == index), value)
            value["evidence_status"] = "CORRECTED RESULT"
        output.append(value)
    return {"results": output, "evidence_validity": classify_old_evidence(old)}


def archive_old_evidence(old_dir, output_dir):
    """Archive exact bytes separately, with explicit invalidation labeling."""
    archive = Path(output_dir) / "old_invalidated"
    archive.mkdir(parents=True, exist_ok=True)
    sources = {}
    for source in sorted(Path(old_dir).iterdir()):
        if not source.is_file() or source.suffix not in {".json", ".md"}:
            continue
        content = source.read_bytes()
        target = archive / source.name
        if target.exists() and target.read_bytes() != content:
            raise ValueError("An existing old-evidence archive disagrees with its source.")
        target.write_bytes(content)
        sources[source.name] = {"sha256": sha256(content).hexdigest(), "bytes": len(content)}
    (archive / "README.md").write_text(
        "# OLD / INVALIDATED RESULT\n\nExact copies of the earlier Phase 6 reports. "
        "Every non-search observation is stale, including timings, memory and censored attempts. "
        "Only pure search is retained, separately labeled with its original provenance. "
        "These files are never aggregated into corrected quality conclusions.\n", encoding="utf8")
    return sources


def _hash_file(path):
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def protected_inventory(root=ROOT):
    """Read bytes only: data/models plus all Production source modules."""
    root = Path(root)
    artifacts = {path.relative_to(root).as_posix(): _hash_file(path)
        for folder in ("models", "data") for path in sorted((root / folder).rglob("*")) if path.is_file()}
    source = {path.relative_to(root).as_posix(): _hash_file(path)
              for path in sorted((root / "src").rglob("*.py"))}
    return {"artifacts": artifacts, "production_source": source}


def run_corrected_benchmarks(old_dir, output_dir, *, threads=1):
    """Sequential fresh workers, incremental checkpoints and protected hashes."""
    old_dir, output_dir = Path(old_dir), Path(output_dir)
    if old_dir.resolve() == output_dir.resolve():
        raise ValueError("Corrected outputs must be separate from old evidence.")
    old = json.loads((old_dir / "benchmark.json").read_text(encoding="utf8"))
    jobs = corrected_jobs(old)
    before = protected_inventory()
    output_dir.mkdir(parents=True, exist_ok=True)
    sources = archive_old_evidence(old_dir, output_dir)
    source_files = [Path(__file__), ROOT / "scripts/benchmark_two_stage.py"]
    worker_source_hashes = {path.relative_to(ROOT).as_posix(): _hash_file(path) for path in source_files}
    measurement_context = {"protected_inventory": before, "threads": threads}
    baseline_path = output_dir / "protected_before.json"
    progress_path = output_dir / "rerun_progress.json"
    progress = {"started_at": datetime.now(timezone.utc).isoformat(), "sources": sources,
                "worker_source_hashes": worker_source_hashes,
                "measurement_context": measurement_context, "replacements": []}
    if progress_path.exists():
        saved = json.loads(progress_path.read_text(encoding="utf8"))
        if saved.get("measurement_context") != measurement_context:
            raise ValueError("Cannot resume measurements after protected context/threads changed or without a pinned context.")
        if saved["sources"] != sources or saved["worker_source_hashes"] != worker_source_hashes:
            raise ValueError("Cannot resume measurements after source/evidence bytes changed.")
        if not baseline_path.exists() or json.loads(baseline_path.read_text(encoding="utf8")) != before:
            raise ValueError("Cannot resume measurements with a missing or changed baseline context.")
        progress = saved
    else:
        if baseline_path.exists() and json.loads(baseline_path.read_text(encoding="utf8")) != before:
            raise ValueError("Cannot overwrite an existing protected baseline context.")
        if not baseline_path.exists():
            benchmark._write_worker_json(baseline_path, before)
        benchmark._write_worker_json(progress_path, progress)
    done = {row["old_result_index"] for row in progress["replacements"]}
    for number, job in enumerate(jobs, 1):
        if job["old_result_index"] in done:
            continue
        print(f"[{number}/{len(jobs)}] {job}", flush=True)
        worker_job = {key: job[key] for key in ("size", "scenario", "mode", "stage1", "final")}
        result = benchmark.run_worker(worker_job, timeout_seconds=job["timeout_seconds"], threads=threads)
        validate_replacement(job, result)
        result.update(old_result_index=job["old_result_index"],
                      measured_at=datetime.now(timezone.utc).isoformat(), evidence_status="CORRECTED RESULT")
        progress["replacements"].append(result)
        benchmark._write_worker_json(progress_path, progress)
        print(f"  {result['status']} elapsed={result['elapsed_time']} peak={result['peak_memory']}", flush=True)
    assembled = assemble_corrected_results(old, progress["replacements"])
    report = benchmark.build_report(assembled["results"], timeout_seconds=old["worker_timeout_seconds"], threads=threads)
    report.update(evidence_validity={**assembled["evidence_validity"], "original_sources": sources,
        "old_measurement_batches": old.get("measurement_batches", []),
        "old_inference_records_location": "old_invalidated/benchmark.json",
        "corrected_records_location": "benchmark.json",
        "invalidated_count": len(jobs), "rerun_count": len(progress["replacements"]),
        "retained_search_count": len(assembled["evidence_validity"]["retained_search_indices"])},
        runner_source_hashes=worker_source_hashes,
        grade_version_selection="smallest finite version in loaded official GradeScale pass bands",
        completion_status="CORRECTED BENCHMARK COMPLETE; censored workloads remain unmeasured")
    after = protected_inventory()
    if after != before:
        raise ValueError("Protected models/data or Production source changed during measurements.")
    if {path.relative_to(ROOT).as_posix(): _hash_file(path) for path in source_files} != worker_source_hashes:
        raise ValueError("Benchmark worker source changed during measurements.")
    report["protected_files"] = {"artifact_count": len(before["artifacts"]),
        "production_source_count": len(before["production_source"]),
        "changed": 0, "added": 0, "removed": 0,
        "manifest_sha256": before["artifacts"]["models/shortlist_v2/manifest.json"]}
    for name, record in sources.items():
        if _hash_file(old_dir / name) != record["sha256"]:
            raise ValueError("An original report changed during the corrected rerun.")
    benchmark.save_report(report, output_dir)
    print(json.dumps(report["job_status_counts"]), flush=True)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-dir", type=Path, default=ROOT / "reports/two_stage_phase6")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports/two_stage_phase6/corrected")
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args(argv)
    if args.threads < 1:
        parser.error("threads must be positive")
    report = run_corrected_benchmarks(args.old_dir, args.output_dir, threads=args.threads)
    return 1 if report["job_status_counts"].get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
