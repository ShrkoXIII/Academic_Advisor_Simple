"""Corrected Phase 6 evaluates recall independently of shortlist Balance."""
import importlib.util
from copy import deepcopy

import numpy as np
import pandas as pd
import pytest


def evaluation_module():
    assert importlib.util.find_spec("scripts.evaluate_corrected_phase6") is not None, (
        "Corrected Phase 6 recall evaluation is missing"
    )
    from scripts import evaluate_corrected_phase6
    return evaluate_corrected_phase6


def test_recall_has_independent_top_k_denominator_and_explicit_lost_ids():
    module = evaluation_module()
    evidence = module.recall_evidence(["P0", "P2", "P7"], [f"P{i}" for i in range(12)], k=3)
    assert evidence == {"k": 3, "denominator": 3, "retained_count": 2,
        "recall_at_50": 2 / 3, "oracle_plan_ids": ["P0", "P1", "P2"],
        "lost_plan_ids": ["P1"]}
    assert module.recall_evidence(["P0"], ["P0", "P1"], k=10)["recall_at_50"] == .5


def test_no_solution_recall_is_not_reported_as_perfect_retention():
    assert evaluation_module().recall_evidence([], [], k=3)["recall_at_50"] is None


def test_recall_at50_cannot_be_inflated_by_larger_shortlist():
    with pytest.raises(ValueError, match="at most 50"):
        evaluation_module().recall_evidence([str(index) for index in range(51)], ["0"], k=3)


@pytest.mark.parametrize("shortlist,oracle", [(["a", "a"], ["a"]), (["a"], ["a", "a"])])
def test_recall_rejects_duplicate_plan_ids(shortlist, oracle):
    with pytest.raises(ValueError, match="unique"):
        evaluation_module().recall_evidence(shortlist, oracle, k=3)


def test_fixed_final_pool_and_all_four_pairs_use_identical_scored_metrics(tmp_path):
    module = evaluation_module()
    from tests.two_stage_fixtures import synthetic_artifacts
    student, request, manager, specification = module.corrected_fixture("retake_weak", root=tmp_path)
    artifacts = synthetic_artifacts(grade1=75, grade2=80)
    # This test exercises real aggregation/ranking/context using inference doubles.
    result = module.evaluate_fixture(student, request, artifacts=artifacts, history_manager=manager,
        specification=specification, verify_determinism=True)
    assert result["feasible_plan_count"] > 50
    assert result["grade_scale_version_supported"]
    assert result["fixed_final_pool"]["size"] == 50
    assert set(result["fixed_final_pool"]["strategies"]) == {"balance_first", "pareto"}
    shared_ids = set(result["fixed_final_pool"]["plan_ids"])
    for row in result["fixed_final_pool"]["strategies"].values():
        assert set(row["all_ranked_plan_ids"]) == shared_ids
        assert row["deterministic_under_frame_permutation"]
    assert {(row["stage1_strategy"], row["final_strategy"]) for row in result["combinations"]} == {
        (first, final) for first in module.STRATEGIES for final in module.STRATEGIES}
    for choice in result["stage1"].values():
        assert set(choice["stage2_oracles"]) == {"academic_diagnostic", "balance_first", "pareto"}
        assert choice["determinism"]["shortlist_ids_equal"]
        assert set(choice["stage2_oracles"]["pareto"]) == {"top3", "top10"}
    assert result["production_ranking_strategy"] == "UNAPPROVED"
    assert not list(tmp_path.iterdir())


def test_fixed_pool_rejects_nonfinite_metrics():
    module = evaluation_module()
    from scripts.evaluate_two_stage_ranking import _mix_courses, _synthetic_eligible
    from src.recommendation.balance_policy import compute_balance_components
    from src.recommendation.ranking import canonical_plan_identity
    selected = _mix_courses(3, 0, 12)
    identity = canonical_plan_identity(selected.course_id)
    frame = pd.DataFrame([{"plan_id": identity.plan_id, "course_tuple": identity.course_tuple,
        "projected_cumulative_gpa": np.inf, "expected_quality_points": 30,
        "expected_plan_gpa": 2., "expected_failed_credits": .5,
        **compute_balance_components(selected, _synthetic_eligible(selected), part_semester=1)}])
    with pytest.raises(ValueError, match="finite"):
        module.compare_fixed_final(frame)


def test_evaluator_never_silently_accepts_unsupported_grade_version(tmp_path):
    module = evaluation_module()
    from tests.two_stage_fixtures import synthetic_artifacts
    student, request, manager, specification = module.corrected_fixture("retake_weak", root=tmp_path)
    artifacts = synthetic_artifacts()
    artifacts.grade_scale.pass_bands["grade_version_id"] = np.nan
    with pytest.raises(ValueError, match="supported GradeScale"):
        module.evaluate_fixture(student, request, artifacts=artifacts, history_manager=manager,
            specification=specification)


@pytest.mark.parametrize("grade_version", [99., np.inf, np.nan, True])
def test_explicit_grade_version_must_be_finite_supported_and_nonboolean(tmp_path, grade_version):
    module = evaluation_module()
    from tests.two_stage_fixtures import synthetic_artifacts
    student, request, manager, specification = module.corrected_fixture("no_solution", root=tmp_path)
    artifacts = synthetic_artifacts()
    with pytest.raises(ValueError, match="finite supported"):
        module.evaluate_fixture(student, request, artifacts=artifacts, history_manager=manager,
            specification=specification, grade_version=grade_version)
    assert not artifacts.stage1.grade_model.matrices


def test_explicit_supported_grade_version_is_recorded_with_category_coverage(tmp_path):
    module = evaluation_module()
    from tests.two_stage_fixtures import synthetic_artifacts
    student, request, manager, specification = module.corrected_fixture("no_solution", root=tmp_path)
    artifacts = synthetic_artifacts()
    version = float(artifacts.grade_scale.pass_bands.grade_version_id.dropna().iloc[0])
    result = module.evaluate_fixture(student, request, artifacts=artifacts, history_manager=manager,
        specification=specification, grade_version=version)
    assert result["grade_version_id"] == version
    assert result["grade_version_selection"] == "explicit_validated_pass_band_version"
    assert set(result["grade_version_known_category"]) == {"stage1", "stage2"}


def test_offline_oracle_bound_refuses_large_fixture_without_stage2_inference(tmp_path):
    module = evaluation_module()
    from tests.two_stage_fixtures import synthetic_artifacts
    student, request, manager, specification = module.corrected_fixture("retake_weak", root=tmp_path)
    artifacts = synthetic_artifacts()
    with pytest.raises(ValueError, match="offline oracle bound"):
        module.evaluate_fixture(student, request, artifacts=artifacts, history_manager=manager,
            specification=specification, max_feasible_plans=5)
    assert not artifacts.stage2.grade_model.matrices


def test_no_solution_fixture_skips_stage2_and_does_not_invent_comparisons(tmp_path):
    module = evaluation_module()
    from tests.two_stage_fixtures import synthetic_artifacts
    student, request, manager, specification = module.corrected_fixture("no_solution", root=tmp_path)
    artifacts = synthetic_artifacts()
    result = module.evaluate_fixture(student, request, artifacts=artifacts,
        history_manager=manager, specification=specification)
    assert result["feasible_plan_count"] == result["stage2_row_count"] == 0
    assert result["stage1"]["balance_first"]["stage2_oracles"]["pareto"]["top3"]["recall_at_50"] is None
    assert not artifacts.stage2.grade_model.matrices


def test_summary_keeps_recommendation_separate_from_approval(tmp_path):
    module = evaluation_module()
    from tests.two_stage_fixtures import synthetic_artifacts
    student, request, manager, specification = module.corrected_fixture("no_solution", root=tmp_path)
    result = module.evaluate_fixture(student, request, artifacts=synthetic_artifacts(),
        history_manager=manager, specification=specification)
    summary = module.summarize_evidence([result])
    assert summary["stage1"]["balance_first"]["oracles"]["pareto"]["top3"]["pooled_recall_at_50"] is None
    assert summary["production_ranking_strategy"] == "UNAPPROVED"
    assert summary["approval_status"] == "UNAPPROVED"


def test_exact_objective_ties_are_additional_sensitivity_not_identity_recall():
    module = evaluation_module()
    frame = pd.DataFrame([{"plan_id": key, "projected_cumulative_gpa": 2.5,
        "expected_failed_credits": .2, "expected_plan_gpa": 3.} for key in ("A", "B")])
    strict = module.recall_evidence(["B"], frame.plan_id, k=1)
    sensitivity = module._tie_recall(["B"], frame, k=1, oracle="academic_diagnostic")
    assert strict["recall_at_50"] == 0
    assert sensitivity["recall_at_50"] == 1
    assert sensitivity["boundary_exact_objective_tie_count"] == 2


def test_disabled_balance_distances_remain_missing_in_distributions():
    module = evaluation_module()
    frame = pd.DataFrame({key: [None, .1] if key.endswith("penalty") else [1., 2.] for key in module.METRICS})
    penalty = module.distributions(frame)["failed_balance_penalty"]
    assert penalty["disabled_or_missing_count"] == 1
    assert penalty["mean"] == penalty["min"] == .1


@pytest.mark.parametrize("failure", ["final_permutation", "stage1_shortlist", "stage1_order", "stage2_metrics", "skipped"])
def test_summary_determinism_requires_every_actual_check(failure):
    module = evaluation_module()
    case = {"name": "no_solution", "feasible_plan_count": 0,
        "stage2_candidate_permutation_checked": True,
        "stage2_metrics_deterministic_under_candidate_permutation": True,
        "stage1": {name: {"determinism": {"candidate_permutation_checked": True,
            "complete_order_equal": True, "shortlist_ids_equal": True}} for name in module.STRATEGIES},
        "fixed_final_pool": {"strategies": {name: {"deterministic_under_frame_permutation": True} for name in module.STRATEGIES}}}
    assert module.summarize_evidence([case])["determinism_all_passed"]
    invalid = deepcopy(case)
    if failure == "final_permutation":
        invalid["fixed_final_pool"]["strategies"]["pareto"]["deterministic_under_frame_permutation"] = False
    elif failure == "stage1_shortlist":
        invalid["stage1"]["balance_first"]["determinism"]["shortlist_ids_equal"] = False
    elif failure == "stage1_order":
        invalid["stage1"]["balance_first"]["determinism"]["complete_order_equal"] = False
    elif failure == "stage2_metrics":
        invalid["stage2_metrics_deterministic_under_candidate_permutation"] = False
    else:
        invalid["stage2_candidate_permutation_checked"] = False
        invalid["stage2_metrics_deterministic_under_candidate_permutation"] = None
    assert not module.summarize_evidence([invalid])["determinism_all_passed"]


def test_skipped_candidate_permutation_is_explicitly_unverified(tmp_path):
    module = evaluation_module()
    from tests.two_stage_fixtures import synthetic_artifacts
    student, request, manager, specification = module.corrected_fixture("no_solution", root=tmp_path)
    result = module.evaluate_fixture(student, request, artifacts=synthetic_artifacts(),
        history_manager=manager, specification=specification, verify_determinism=False)
    assert not result["stage2_candidate_permutation_checked"]
    assert result["stage2_metrics_deterministic_under_candidate_permutation"] is None
    assert not module.summarize_evidence([result])["determinism_all_passed"]
