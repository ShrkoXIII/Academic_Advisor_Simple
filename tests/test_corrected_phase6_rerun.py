"""Stale inference evidence is replaced without mixing it with corrected results."""
from copy import deepcopy
import importlib
import json

import pytest


def module():
    return importlib.import_module("scripts.rerun_corrected_phase6")


def old_report():
    rows = [
        {"size": 15, "scenario": "easy", "mode": "search", "status": "completed", "elapsed_time": .1},
        {"size": 15, "scenario": "easy", "mode": "stage1_ranking", "stage1_strategy": "balance_first", "status": "completed"},
        {"size": 15, "scenario": "easy", "mode": "final_ranking", "final_strategy": "pareto", "status": "completed"},
        {"size": 15, "scenario": "dense_ties", "mode": "full", "stage1": "pareto", "final": "balance_first", "status": "timeout"},
        {"size": 15, "scenario": "dense_ties", "mode": "full", "stage1_strategy": "pareto", "final_strategy": "balance_first", "status": "completed", "worker_timeout_seconds": 90},
    ]
    return {"results": rows, "worker_timeout_seconds": 15}


def corrected(job):
    return {**job, "status": "completed", "grade_version_id": 1.111,
            "grade_scale_version_supported": True, "elapsed_time": .2,
            "worker_timeout_seconds": job["timeout_seconds"]}


def test_every_nonsearch_row_is_invalidated_including_timeout_and_duplicate_batch():
    inventory = module().classify_old_evidence(old_report())
    assert inventory["retained_search_indices"] == [0]
    assert inventory["invalidated_indices"] == [1, 2, 3, 4]
    assert inventory["invalidated_by_mode"] == {"stage1_ranking": 1, "final_ranking": 1, "full": 2}


def test_jobs_preserve_old_independent_choices_and_each_observations_deadline():
    jobs = module().corrected_jobs(old_report())
    assert [row["old_result_index"] for row in jobs] == [1, 2, 3, 4]
    assert jobs[0]["stage1"] == "balance_first"
    assert jobs[1]["final"] == "pareto"
    assert jobs[2]["stage1"] == "pareto" and jobs[2]["final"] == "balance_first"
    assert [row["timeout_seconds"] for row in jobs] == [15, 15, 15, 90]


@pytest.mark.parametrize("changes", [
    {"grade_version_id": None}, {"grade_scale_version_supported": False},
    {"grade_version_id": float("nan")}, {"size": 20}, {"scenario": "no_solution"},
])
def test_completed_replacements_must_match_job_and_prove_supported_grade_version(changes):
    job = module().corrected_jobs(old_report())[0]
    row = {**corrected(job), **changes}
    with pytest.raises(ValueError):
        module().validate_replacement(job, row)


def test_old_metric_values_are_never_in_the_corrected_aggregate():
    old = old_report()
    old["results"][1]["comparison"] = {"metric_means": {"expected_plan_gpa": 0}}
    original = deepcopy(old)
    replacements = [corrected(job) for job in module().corrected_jobs(old)]
    report = module().assemble_corrected_results(old, replacements)
    assert len(report["results"]) == 5
    assert report["results"][0]["evidence_status"] == "RETAINED / UNAFFECTED SEARCH"
    assert all(row["evidence_status"] == "CORRECTED RESULT" for row in report["results"][1:])
    assert "comparison" not in report["results"][1]
    assert old == original


def test_incomplete_or_duplicate_replacement_set_is_rejected():
    old = old_report()
    replacements = [corrected(job) for job in module().corrected_jobs(old)]
    with pytest.raises(ValueError):
        module().assemble_corrected_results(old, replacements[:-1])
    with pytest.raises(ValueError):
        module().assemble_corrected_results(old, replacements + replacements[:1])


def test_old_files_remain_byte_identical_and_archive_is_separate(tmp_path):
    old_dir, new_dir = tmp_path / "old", tmp_path / "corrected"
    old_dir.mkdir()
    content = {"benchmark.json": json.dumps(old_report()).encode(),
               "benchmark.md": b"OLD GPA=0\r\n", "supplemental.json": b"{\"results\":[]}\n"}
    for name, value in content.items():
        (old_dir / name).write_bytes(value)
    sources = module().archive_old_evidence(old_dir, new_dir)
    for name, value in content.items():
        assert (old_dir / name).read_bytes() == value
        assert (new_dir / "old_invalidated" / name).read_bytes() == value
        assert sources[name]["sha256"]
    assert "INVALIDATED" in (new_dir / "old_invalidated" / "README.md").read_text()


@pytest.mark.parametrize("change", ["artifact", "production_source", "threads"])
def test_resume_rejects_changed_context_and_preserves_original_baseline(tmp_path, monkeypatch, change):
    target = module()
    old_dir, new_dir = tmp_path / "old", tmp_path / "corrected"
    old_dir.mkdir()
    (old_dir / "benchmark.json").write_text(json.dumps(old_report()), encoding="utf8")
    protected = {"artifacts": {"models/shortlist_v2/manifest.json": "a" * 64},
                 "production_source": {"src/recommendation/ranking.py": "b" * 64}}
    monkeypatch.setattr(target, "protected_inventory", lambda: deepcopy(protected))
    calls = []
    def interrupted(job, *, timeout_seconds, threads):
        calls.append(job)
        if len(calls) == 2:
            raise RuntimeError("intentional interruption")
        return {**job, "status": "completed", "elapsed_time": .1, "peak_memory": 1.,
                "grade_version_id": 1.111, "grade_scale_version_supported": True,
                "worker_timeout_seconds": timeout_seconds}
    monkeypatch.setattr(target.benchmark, "run_worker", interrupted)
    with pytest.raises(RuntimeError, match="intentional interruption"):
        target.run_corrected_benchmarks(old_dir, new_dir)
    original_baseline = (new_dir / "protected_before.json").read_bytes()
    if change == "artifact":
        protected["artifacts"]["models/shortlist_v2/manifest.json"] = "c" * 64
    elif change == "production_source":
        protected["production_source"]["src/recommendation/ranking.py"] = "c" * 64
    def unexpected(*args, **kwargs):
        pytest.fail("resume must reject a changed measurement context before starting workers")
    monkeypatch.setattr(target.benchmark, "run_worker", unexpected)
    with pytest.raises(ValueError, match="context"):
        target.run_corrected_benchmarks(old_dir, new_dir, threads=2 if change == "threads" else 1)
    assert (new_dir / "protected_before.json").read_bytes() == original_baseline


def test_completion_rejects_changed_worker_source(tmp_path, monkeypatch):
    target = module()
    old_dir, new_dir = tmp_path / "old", tmp_path / "corrected"
    old_dir.mkdir()
    (old_dir / "benchmark.json").write_text(json.dumps(old_report()), encoding="utf8")
    protected = {"artifacts": {"models/shortlist_v2/manifest.json": "a" * 64}, "production_source": {}}
    monkeypatch.setattr(target, "protected_inventory", lambda: deepcopy(protected))
    original_hash = target._hash_file
    changed = []
    def file_hash(path):
        if changed and path == target.ROOT / "scripts/benchmark_two_stage.py":
            return "f" * 64
        return original_hash(path)
    def worker(job, *, timeout_seconds, threads):
        changed.append(True)
        return {**job, "status": "completed", "elapsed_time": .1, "peak_memory": 1.,
                "grade_version_id": 1.111, "grade_scale_version_supported": True,
                "worker_timeout_seconds": timeout_seconds}
    monkeypatch.setattr(target, "_hash_file", file_hash)
    monkeypatch.setattr(target.benchmark, "run_worker", worker)
    monkeypatch.setattr(target.benchmark, "save_report", lambda *args: None)
    with pytest.raises(ValueError, match="worker source"):
        target.run_corrected_benchmarks(old_dir, new_dir)
