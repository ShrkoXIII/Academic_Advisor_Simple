"""Phase 6 measures real core code on synthetic inputs, without promotion."""
import importlib.util
import itertools
import json

import pandas as pd
import pytest

from src.recommendation.constraints import PlanConstraints, enumerate_feasible_plan_indices
from src.recommendation.plan_generation import enumerate_plan_indices


def benchmark_module():
    assert importlib.util.find_spec("scripts.benchmark_two_stage") is not None, (
        "Phase 6 synthetic benchmark is missing"
    )
    from scripts import benchmark_two_stage
    return benchmark_two_stage


def test_search_counter_counts_actual_recursion_and_preserves_order():
    candidates = pd.DataFrame({"course_credits": [3, 3]})
    stats = {}
    observed = list(enumerate_plan_indices(candidates, 3, search_stats=stats))
    assert observed == list(enumerate_plan_indices(candidates, 3)) == [(0,), (1,)]
    assert stats == {"visited_search_states": 7, "exact_credit_plan_count": 2}


def test_feasible_counter_keeps_zero_options_and_filters_complete_plans():
    candidates = pd.DataFrame({"course_credits": [3, 3, 0],
        "candidate_group": ["FAILED_RETAKE", "NEW", "NEW"],
        "plan_requirement_type_id": ["R"] * 3})
    stats = {}
    constraints = PlanConstraints(3, {"R": 3}, 0)
    observed = list(enumerate_feasible_plan_indices(candidates, constraints, search_stats=stats))
    assert observed == list(enumerate_feasible_plan_indices(candidates, constraints))
    assert observed == [(1, 2), (1,)]
    assert stats["exact_credit_plan_count"] == 4
    assert stats["feasible_plan_count"] == 2


@pytest.mark.parametrize("size", [15, 20, 25, 30, 35])
def test_scenarios_cover_sizes_fractions_zero_ties_constraints_and_no_solution(size):
    module = benchmark_module()
    cases = [module.synthetic_case(size, name) for name in module.SCENARIOS]
    assert len(cases) >= 4
    for student, request in cases:
        assert len(student["candidates"]) == size
        assert student["snapshot"]["student_id"].startswith("SYNTHETIC")
        assert request["allowed_failed_repeat_credits"] >= 0
    fractional = module.synthetic_case(size, "fractional_zero_constraints")[0]["candidates"]
    assert any(row["course_credits"] == 0 for row in fractional)
    assert any(float(row["course_credits"]) % 1 for row in fractional)
    assert len({row["plan_requirement_type_id"] for row in fractional}) == 2
    assert module.synthetic_case(size, "dense_ties") == module.synthetic_case(size, "dense_ties")


@pytest.mark.parametrize("mode", ["search", "stage1_ranking", "final_ranking", "full"])
def test_measurements_use_real_core_and_explicit_strategies_without_bundle_io(mode, tmp_path):
    from tests.two_stage_fixtures import synthetic_artifacts
    module = benchmark_module()
    artifacts = synthetic_artifacts()
    result = module.measure_case(15, "easy", mode, stage1="balance_first", final="pareto",
                                 artifacts=artifacts, history_root=tmp_path)
    assert not list(tmp_path.iterdir())
    assert result["status"] == "completed"
    assert result["candidate_count"] == 15
    assert result["elapsed_time"] >= 0
    assert result["peak_memory"] > 0
    assert result["feasible_plan_count"] == 1
    assert result["shortlist_count"] == 1
    if mode in {"search", "full"}:
        assert result["visited_search_states"] > 0
    if mode == "full":
        assert result["stage1_row_count"] == 15
        assert result["stage2_row_count"] == 6
        assert len(artifacts.stage1.grade_model.matrices) == 1
        assert len(artifacts.stage2.grade_model.matrices) == 1
        assert result["production_ranking_strategy"] == "UNAPPROVED"
        assert result["stage1_strategy"] != result["final_strategy"]


def test_small_search_matches_independent_subsets():
    module = benchmark_module()
    from src.recommendation.inputs import prepare_recommendation_payloads
    student, request = module.synthetic_case(15, "fractional_zero_constraints")
    # Keep the diverse prefix for a small independent exhaustive oracle.
    student["candidates"] = student["candidates"][:7]
    prepared = prepare_recommendation_payloads(student_payload=student, request_payload=request)
    expected = []
    from fractions import Fraction
    rows = prepared.candidates.to_dict("records")
    for mask in itertools.product((False, True), repeat=len(rows)):
        chosen = [i for i, enabled in enumerate(mask) if enabled]
        if sum(Fraction(str(rows[i]["course_credits"])) for i in chosen) != Fraction(prepared.constraints.target_credits):
            continue
        consumed = {key: sum(Fraction(str(rows[i]["course_credits"])) for i in chosen
                            if rows[i]["plan_requirement_type_id"] == key)
                    for key in prepared.constraints.requirement_policies}
        failed = sum(Fraction(str(rows[i]["course_credits"])) for i in chosen if rows[i]["candidate_group"] == "FAILED_RETAKE")
        withdrawn = sum(Fraction(str(rows[i]["course_credits"])) for i in chosen if rows[i]["candidate_group"] == "WITHDRAWN_RETAKE")
        if (any(value > Fraction(prepared.constraints.requirement_policies[key]) for key, value in consumed.items())
                or failed > Fraction(prepared.constraints.allowed_failed_repeat_credits)
                or withdrawn > Fraction(prepared.constraints.allowed_withdrawn_repeat_credits)):
            continue
        expected.append(tuple(chosen))
    stats = {}
    actual = list(enumerate_feasible_plan_indices(prepared.candidates, prepared.constraints, search_stats=stats))
    assert set(actual) == set(expected)
    assert stats["feasible_plan_count"] == len(expected)


def test_jobs_compare_stages_independently_and_every_combination():
    module = benchmark_module()
    jobs = module.benchmark_jobs([15], ["easy"])
    assert len(jobs) == 9
    pairs = {(job["stage1"], job["final"]) for job in jobs if job["mode"] == "full"}
    assert pairs == set(itertools.product(module.STRATEGIES, repeat=2))
    assert {job["mode"] for job in jobs} == {"search", "stage1_ranking", "final_ranking", "full"}


def test_timeout_is_censored_evidence_never_a_fabricated_measurement():
    module = benchmark_module()
    result = module.censored_result({"size": 35, "scenario": "dense_ties", "mode": "full",
                                    "stage1": "pareto", "final": "balance_first"}, 15, {})
    assert result["status"] == "timeout"
    assert result["elapsed_time"] is None
    assert result["peak_memory"] is None
    assert result["worker_wall_time_lower_bound"] == 15
    assert result["candidate_count"] == 35
    assert result["stress_only"] is True


def test_report_keeps_approvals_open_and_records_censored_jobs(tmp_path):
    module = benchmark_module()
    row = module.censored_result({"size": 30, "scenario": "dense_ties", "mode": "full",
                                 "stage1": "pareto", "final": "pareto"}, 15, {})
    report = module.build_report([row], timeout_seconds=15, threads=1)
    module.save_report(report, tmp_path)
    assert json.loads((tmp_path / "benchmark.json").read_text(encoding="utf8")) == report
    assert report["ranking_approval"] == {"stage1_shortlist_strategy": "UNAPPROVED",
        "final_ranking_strategy": "UNAPPROVED", "combination": "UNAPPROVED"}
    assert report["open_production_contract"]["backend_max_candidate_count"] == "UNRESOLVED"
    text = (tmp_path / "benchmark.md").read_text(encoding="utf8")
    assert "timeout" in text and "UNAPPROVED" in text
    assert "peak" in text.lower()


def test_no_solution_is_measured_without_inventing_ranker_work(tmp_path):
    from tests.two_stage_fixtures import synthetic_artifacts
    module = benchmark_module()
    result = module.measure_case(15, "no_solution", "full", artifacts=synthetic_artifacts(), history_root=tmp_path)
    assert result["feasible_plan_count"] == result["shortlist_count"] == result["stage2_row_count"] == 0
    assert result["result_status"] == "no_feasible_plan"
    assert result["elapsed_time"] > 0


def test_final_comparison_uses_identical_fixed_shortlist_for_both_strategies(tmp_path):
    from tests.two_stage_fixtures import synthetic_artifacts
    module = benchmark_module()
    rows = [module.measure_case(15, "fractional_zero_constraints", "final_ranking", final=choice,
        artifacts=synthetic_artifacts(), history_root=tmp_path) for choice in module.STRATEGIES]
    assert rows[0]["fixed_shortlist_plan_ids"] == rows[1]["fixed_shortlist_plan_ids"]
    assert len(rows[0]["fixed_shortlist_plan_ids"]) <= 50
    assert rows[0]["feasible_plan_count"] > 0


def test_worker_subprocess_serializes_completed_search():
    module = benchmark_module()
    job = {"size": 15, "scenario": "easy", "mode": "search", "stage1": "balance_first", "final": "pareto"}
    row = module.run_worker(job, timeout_seconds=30, threads=1)
    assert row["status"] == "completed"
    assert row["feasible_plan_count"] == 1
    assert row["peak_memory"] > 0


def test_worker_timeout_returns_censored_record(monkeypatch):
    import subprocess
    module = benchmark_module()
    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])
    monkeypatch.setattr(module.subprocess, "run", timeout)
    row = module.run_worker({"size": 35, "scenario": "dense_ties", "mode": "full",
                            "stage1": "pareto", "final": "pareto"}, timeout_seconds=.01, threads=1)
    assert row["status"] == "timeout"
    assert row["elapsed_time"] is None


def test_atomic_checkpoint_has_complete_json_and_no_leftover(tmp_path):
    module = benchmark_module()
    target = tmp_path/"checkpoint.json"
    module._write_worker_json(target, {"worker_phase": "setup"})
    module._write_worker_json(target, {"worker_phase": "measurement", "feasible_plan_count": 7})
    assert json.loads(target.read_text()) == {"worker_phase": "measurement", "feasible_plan_count": 7}
    assert {p.name for p in tmp_path.iterdir()} == {"checkpoint.json"}


def test_fast_search_is_not_blamed_for_full_or_ranking_timeouts():
    module = benchmark_module()
    search = {"size": 30, "scenario": "dense_ties", "mode": "search", "status": "completed", "elapsed_time": .2}
    timed = module.censored_result({"size": 30, "scenario": "dense_ties", "mode": "full",
        "stage1": "pareto", "final": "pareto"}, 15, {})
    report = module.build_report([search, timed], timeout_seconds=15, threads=1)
    assert report["search_decision"].startswith("KEEP")


def test_slow_non_dense_search_is_included_in_the_search_decision():
    module = benchmark_module()
    row = {"size": 20, "scenario": "fractional_zero_constraints", "mode": "search",
           "status": "completed", "elapsed_time": 6.0}
    report = module.build_report([row], timeout_seconds=15, threads=1)
    assert report["search_decision"].startswith("PROPOSE SEPARATE")


def test_missing_search_measurement_cannot_produce_a_keep_verdict():
    module = benchmark_module()
    row = module.censored_result({"size": 30, "scenario": "easy", "mode": "search",
                                 "stage1": "balance_first", "final": "pareto"}, 15, {})
    assert module.build_report([row], timeout_seconds=15, threads=1)["search_decision"].startswith("INCOMPLETE")


def test_dense_upper_target_search_has_the_complete_choose_six_count(tmp_path):
    import math
    module = benchmark_module()
    student, request = module.synthetic_case(15, "dense_upper_18")
    assert request["target_credits"] == 18
    assert all(row["course_credits"] == 3 for row in student["candidates"])
    row = module.measure_case(15, "dense_upper_18", "search", history_root=tmp_path)
    assert row["feasible_plan_count"] == math.comb(15, 6)
    assert row["visited_search_states"] > row["feasible_plan_count"]


def test_inference_fixture_uses_a_grade_version_present_in_loaded_bands(tmp_path):
    from tests.two_stage_fixtures import synthetic_artifacts
    module = benchmark_module()
    artifacts = synthetic_artifacts()
    artifacts.grade_scale.pass_bands["grade_version_id"] = 1.111
    row = module.measure_case(15, "easy", "full", artifacts=artifacts, history_root=tmp_path)
    assert row["top_metric_means"]["expected_plan_gpa"] == 2.0
    assert row["grade_version_id"] == 1.111
    assert row["grade_scale_version_supported"] is True


def test_inference_fixture_rejects_a_scale_without_supported_versions(tmp_path):
    from tests.two_stage_fixtures import synthetic_artifacts
    module = benchmark_module()
    artifacts = synthetic_artifacts()
    artifacts.grade_scale.pass_bands["grade_version_id"] = float("nan")
    with pytest.raises(ValueError, match="supported GradeScale version"):
        module.measure_case(15, "easy", "full", artifacts=artifacts, history_root=tmp_path)
