"""Offline evidence uses complete synthetic sets and aggregate credit mixes only."""
import importlib.util
import itertools
from fractions import Fraction
from pathlib import Path

import pytest


def evaluator():
    assert importlib.util.find_spec("scripts.evaluate_two_stage_ranking") is not None, (
        "Phase 5 offline evaluator has not been implemented"
    )
    from scripts import evaluate_two_stage_ranking
    return evaluate_two_stage_ranking


@pytest.fixture(scope="module")
def synthetic_result():
    return evaluator().evaluate_synthetic()


def independent_plans(candidates, constraints):
    """Enumerate subsets directly, without the production search or constraints."""
    result = []
    for size in range(1, len(candidates) + 1):
        for indices in itertools.combinations(range(len(candidates)), size):
            rows = candidates.iloc[list(indices)].to_dict("records")
            total = sum(Fraction(str(row["course_credits"])) for row in rows)
            if total != Fraction(constraints.target_credits):
                continue
            failed = sum(Fraction(str(row["course_credits"])) for row in rows
                         if row["candidate_group"] == "FAILED_RETAKE")
            withdrawn = sum(Fraction(str(row["course_credits"])) for row in rows
                            if row["candidate_group"] == "WITHDRAWN_RETAKE")
            consumed = {key: sum(Fraction(str(row["course_credits"])) for row in rows
                                 if row["plan_requirement_type_id"] == key)
                        for key in constraints.requirement_policies}
            if (failed > Fraction(constraints.allowed_failed_repeat_credits)
                    or withdrawn > Fraction(constraints.allowed_withdrawn_repeat_credits)
                    or any(value > Fraction(constraints.requirement_policies[key])
                           for key, value in consumed.items())):
                continue
            quality = sum(Fraction(str(row["course_credits"])) * Fraction(str(row["expected_points"]))
                          for row in rows)
            risk = sum(Fraction(str(row["course_credits"])) * Fraction(str(row["fail_probability"]))
                       for row in rows)
            result.append({"course_tuple": tuple(sorted(row["course_id"] for row in rows)),
                           "expected_quality_points": float(quality), "expected_failed_credits": float(risk),
                           "expected_plan_gpa": float(quality / total),
                           "projected_cumulative_gpa": float((Fraction(120) + quality) / 75),
                           "failed_balance_penalty": float(max(Fraction(1, 6) - failed / total, 0, failed / total - Fraction(4, 17))),
                           "withdrawn_balance_penalty": float(max(0, withdrawn / total - Fraction(3, 17))),
                           "total_previous_balance_penalty": float(max(Fraction(1, 6) - (failed + withdrawn) / total,
                               0, (failed + withdrawn) / total - Fraction(2, 7)))})
    return result


def independent_order(rows, stage, name):
    """Repeated complete nondominance peeling and literal lexicographic keys."""
    levels, remaining, level = {}, list(range(len(rows))), 0
    vectors = [(-row["projected_cumulative_gpa"], row["expected_failed_credits"],
                row["failed_balance_penalty"], row["total_previous_balance_penalty"],
                row["withdrawn_balance_penalty"]) for row in rows]
    if name == "pareto":
        while remaining:
            front = [i for i in remaining if not any(
                all(a <= b for a, b in zip(vectors[j], vectors[i]))
                and any(a < b for a, b in zip(vectors[j], vectors[i]))
                for j in remaining if j != i)]
            for i in front:
                levels[i] = level
            remaining = [i for i in remaining if i not in front]
            level += 1

    def key(i):
        row = rows[i]
        academic = (-row["expected_quality_points"], row["expected_failed_credits"], row["course_tuple"]) if stage == "stage1" else (
            -row["projected_cumulative_gpa"], row["expected_failed_credits"], -row["expected_plan_gpa"], row["plan_id"])
        return (*((levels[i],) if name == "pareto" else ()), row["failed_balance_penalty"],
                row["total_previous_balance_penalty"], row["withdrawn_balance_penalty"], *academic)

    return sorted(range(len(rows)), key=key)


def test_complete_synthetic_evaluation_has_all_feasible_plans(synthetic_result):
    assert synthetic_result["feasible_plan_count"] == 176


@pytest.mark.parametrize("name", ["balance_first", "pareto"])
def test_real_shortlist_matches_independent_complete_subset_and_ranking_oracle(name):
    from src.recommendation.ranking import RankingStrategy
    from src.recommendation.shortlist import build_stage1_shortlist
    candidates, constraints = evaluator().synthetic_fixture()
    expected = independent_plans(candidates, constraints)
    actual = build_stage1_shortlist(candidates, constraints,
        stage1_shortlist_strategy=RankingStrategy(stage="stage1", name=name),
        current_gpa=2, current_gpa_credits=60, part_semester=1)
    assert len(expected) == len(actual.all_plans) == 176
    assert set(actual.all_plans.course_tuple) == {row["course_tuple"] for row in expected}
    order = independent_order(expected, "stage1", name)
    assert actual.shortlist.course_tuple.tolist() == [expected[i]["course_tuple"] for i in order[:50]]
    for row in actual.all_plans.itertuples():
        matched = next(item for item in expected if item["course_tuple"] == row.course_tuple)
        for column in ("expected_quality_points", "expected_failed_credits", "projected_cumulative_gpa",
                       "failed_balance_penalty", "withdrawn_balance_penalty", "total_previous_balance_penalty"):
            assert getattr(row, column) == pytest.approx(matched[column])


def test_all_four_cross_stage_results_match_independent_final_oracle(synthetic_result):
    result = synthetic_result
    final = {row["plan_id"]: row for row in result["complete_synthetic_stage2"]}
    assert len(result["combinations"]) == 4
    assert {(row["stage1_strategy"], row["final_strategy"]) for row in result["combinations"]} == {
        (first, last) for first in ("balance_first", "pareto") for last in ("balance_first", "pareto")}
    for combination in result["combinations"]:
        shortlist = result["stage1_candidates"][combination["stage1_strategy"]]["plan_ids"]
        rows = [final[plan_id] for plan_id in shortlist]
        order = independent_order(rows, "final", combination["final_strategy"])
        assert combination["top_plan_ids"] == [rows[i]["plan_id"] for i in order[:3]]
        assert set(combination["top_plan_ids"]).issubset(shortlist)
        assert combination["stage1_approval"] == combination["final_approval"] == "UNAPPROVED"


def test_fixed_shortlist_is_identical_for_both_final_comparisons(synthetic_result):
    result = synthetic_result
    fixed = result["fixed_shortlist_final_comparison"]
    assert len(fixed["plan_ids"]) == 50
    assert len(fixed["strategies"]) == 2
    for row in fixed["strategies"]:
        assert set(row["top_plan_ids"]).issubset(fixed["plan_ids"])
        assert "metric_change_vs_academic" in row
        assert set(row["metric_change_vs_academic"]) >= {
            "projected_cumulative_gpa", "expected_failed_credits", "failed_balance_penalty",
            "withdrawn_balance_penalty", "total_previous_balance_penalty"}


def test_over_50_diagnostic_reports_lost_global_quality_and_component_retention(synthetic_result):
    result = synthetic_result
    assert result["feasible_plan_count"] > 50
    assert any(row["lost_global_academic_top_k"] for row in result["stage1_candidates"].values())
    for row in result["stage1_candidates"].values():
        assert len(row["plan_ids"]) == 50
        assert set(row["best_component_top_k_retention"]) == {"failed", "withdrawn", "total_previous"}
        assert 0 <= row["academic_shortlist_overlap"] <= 50
        assert row["diversity"]["distinct_courses"] <= 10


def test_aggregate_report_preserves_denominators_and_does_not_claim_historical_eligibility():
    root = Path(__file__).resolve().parents[1]
    result = evaluator().evaluate_historical_policy(root / "reports/repeat_withdrawal_analysis")
    assert result["unique_mix_rows"] == 3507
    assert result["all_group_sums_match_denominator"] is True
    assert result["synthetic_scope_mix_rows"] == 686
    assert result["synthetic_scope_descriptive_cases"] == 49907
    assert result["saved_reference_cases"] == 23535
    assert result["eligibility_source"] == "explicit_synthetic_positive_failed_and_withdrawn"
    assert result["semester_source"] == "synthetic_part_semester_1"
    for distribution in result["penalty_distributions"].values():
        assert distribution["zero_penalty_cases"] + distribution["positive_penalty_cases"] == 49907
    assert result["source_hashes"] and all(len(value) == 64 for value in result["source_hashes"].values())


def test_report_sensitivity_keeps_soft_distance_and_correct_scope_and_availability():
    cases = {row["name"]: row for row in evaluator().evaluate_sensitivities()}
    assert cases["failed_lower_boundary"]["failed_balance_penalty"] == 0
    assert cases["failed_upper_boundary"]["failed_balance_penalty"] == 0
    assert cases["failed_above_upper"]["failed_balance_penalty"] > 0
    assert cases["summer"]["scope_applicable"] is False
    assert cases["outside_load"]["scope_applicable"] is False
    assert cases["zero_other"]["scope_applicable"] is False
    assert cases["zero_new"]["scope_applicable"] is True
    assert cases["no_repeat_eligibility"]["component_active_flags"] == {
        "failed": False, "withdrawn": False, "total_previous": False}


def test_mixed_scope_report_preserves_outside_academic_slots_for_all_candidates():
    rows = evaluator().evaluate_mixed_scope()
    assert len(rows) == 4
    for row in rows:
        assert row["academic_course_names"] == ["academic", "outside", "balanced"]
        assert row["ranked_course_names"] == ["balanced", "outside", "academic"]
        assert row["outside_positions_preserved"] is True


def test_reports_are_deterministic_and_cli_only_writes_requested_output(tmp_path):
    root = Path(__file__).resolve().parents[1]
    module = evaluator()
    report = module.build_evaluation_report(root / "reports/repeat_withdrawal_analysis")
    assert report == module.build_evaluation_report(root / "reports/repeat_withdrawal_analysis")
    module.save_report(report, tmp_path)
    assert {path.name for path in tmp_path.iterdir()} == {"comparison.json", "comparison.md"}
    import json
    assert json.loads((tmp_path / "comparison.json").read_text(encoding="utf-8")) == report
    assert report["production_ranking_strategy"] == "UNAPPROVED"
    assert report["benchmark_performed"] is False
