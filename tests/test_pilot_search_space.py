"""Exact-credit search ordering and selector behavior on synthetic candidates."""
import importlib
import importlib.util
from decimal import Decimal, localcontext
from math import comb
import random

import pandas as pd
import pytest

from src.recommendation.plan_generation import enumerate_plan_indices


def _module():
    name = "tools.recommendation_pilot_20251.search_space"
    assert importlib.util.find_spec(name) is not None, "exact plan search space is missing"
    return importlib.import_module(name)


def _candidates(credits):
    return pd.DataFrame({"course_id": [f"C{i:03}" for i in range(len(credits))],
                         "course_credits": credits})


@pytest.mark.parametrize("credits,target", [
    ([0, 1, 0, 1], 1),
    (["0.1", "0.2", "0.3", "0"], "0.3"),
    (["1.25", "0.75", "2", "0.5"], "2"),
    (["0.1", "0.2"], "0.3000000000001"),
    ([], 3),
])
def test_rank_and_unrank_match_existing_include_first_decimal_dfs(credits, target):
    candidates = _candidates(credits)
    expected = list(enumerate_plan_indices(candidates, target))
    space = _module().ExactPlanSpace(candidates, target)
    assert space.count == len(expected)
    assert [space.unrank(i) for i in range(space.count)] == expected
    assert [space.rank(plan) for plan in expected] == list(range(len(expected)))


def test_zero_credit_courses_remain_optional_after_reaching_target():
    space = _module().ExactPlanSpace(_candidates([0, 1, 0, 1]), 1)
    assert [space.unrank(i) for i in range(space.count)] == [
        (0, 1, 2), (0, 1), (0, 2, 3), (0, 3), (1, 2), (1,), (2, 3), (3,)]


def test_credit_counting_is_independent_of_ambient_decimal_precision():
    with localcontext() as context:
        context.prec = 3
        space = _module().ExactPlanSpace(_candidates([
            "0.123456789123456789", "0.2", "0.323456789123456789"]),
            "0.323456789123456789")
        assert space.count == 2
        assert space.unrank(0) == (0, 1)
        assert space.unrank(1) == (2,)


def test_huge_feasible_count_does_not_materialize_universe():
    space = _module().ExactPlanSpace(_candidates([1] * 80), 40)
    assert space.count == comb(80, 40)
    assert space.states < 10_000
    assert space.unrank(0) == tuple(range(40))
    assert space.unrank(space.count - 1) == tuple(range(40, 80))
    selected = space.select("DIVERSE_N", 20, seed=42)
    assert len(set(selected.ranks)) == 20
    assert all(space.rank(plan) == rank for plan, rank in zip(selected.plans, selected.ranks))


@pytest.mark.parametrize("strategy", ["FIRST_N", "DIVERSE_N", "SMART_SEARCH"])
@pytest.mark.parametrize("budget", [200, 1000, 2000])
def test_selectors_return_unique_reproducible_exact_credit_plans(strategy, budget):
    space = _module().ExactPlanSpace(_candidates([1] * 16), 8)
    kwargs = {"utilities": list(range(16))} if strategy == "SMART_SEARCH" else {}
    first = space.select(strategy, budget, seed=42, **kwargs)
    repeated = space.select(strategy, budget, seed=42, **kwargs)
    assert first.ranks == repeated.ranks
    assert first.plans == repeated.plans
    assert len(first.plans) == budget
    assert len(set(first.ranks)) == budget
    assert all(len(plan) == 8 and len(set(plan)) == 8 for plan in first.plans)
    assert all(space.rank(plan) == rank for plan, rank in zip(first.plans, first.ranks))
    assert first.truncated and not first.discovery_complete
    assert first.reason == "BUDGET_REACHED"
    assert first.unique_discovered >= budget
    assert 0 < first.visited_states <= 2_000_000


def test_diverse_samples_feasible_global_ranks_beyond_dfs_prefix():
    space = _module().ExactPlanSpace(_candidates([1] * 16), 8)
    selected = space.select("DIVERSE_N", 200, seed=42)
    assert space.count == 12_870
    assert selected.ranks == random.Random(42).sample(range(12_870), 200)
    assert any(rank >= 2000 for rank in selected.ranks)
    assert space.select("FIRST_N", 200).ranks == list(range(200))


def test_smart_search_finds_quality_optimum_beyond_dfs_prefix():
    space = _module().ExactPlanSpace(_candidates([1] * 16), 8)
    selected = space.select("SMART_SEARCH", 200, utilities=list(range(16)))
    assert selected.plans[0] == tuple(range(8, 16))
    assert selected.ranks[0] == 12_869
    scores = [sum(plan) for plan in selected.plans]
    assert scores == sorted(scores, reverse=True)
    assert selected.visited_states < 100_000


def test_smart_quality_is_credit_weighted_and_breaks_ties_by_global_rank():
    space = _module().ExactPlanSpace(_candidates([2, 1, 1, 0]), 2)
    selected = space.select("SMART_SEARCH", 10, utilities=[2, 3, 2, 999])
    assert selected.plans == [(1, 2, 3), (1, 2), (0, 3), (0,)]
    assert selected.ranks == [2, 3, 0, 1]
    assert selected.discovery_complete and not selected.truncated


@pytest.mark.parametrize("strategy", ["FIRST_N", "DIVERSE_N", "SMART_SEARCH"])
@pytest.mark.parametrize("budget", [200, 1000, 2000])
def test_fixed_pool_is_strict_and_full_pool_budget_selects_every_plan(strategy, budget):
    space = _module().ExactPlanSpace(_candidates([1] * 16), 8)
    pool = list(range(2000))
    selected = space.select(strategy, budget, seed=42, pool=pool, utilities=list(range(16)))
    assert len(selected.ranks) == budget
    assert set(selected.ranks).issubset(pool)
    if budget == 2000:
        assert set(selected.ranks) == set(pool)
        assert selected.discovery_complete and not selected.truncated


def test_canonical_id_is_stable_across_candidate_order():
    module = _module()
    first = module.ExactPlanSpace(pd.DataFrame({"course_id": ["z", "a"], "course_credits": [1, 1]}), 2)
    other = module.ExactPlanSpace(pd.DataFrame({"course_id": ["a", "z"], "course_credits": [1, 1]}), 2)
    assert first.candidate_ids == ["z", "a"]
    assert len(first.canonical_id((0, 1))) == 64
    assert first.canonical_id((0, 1)) == other.canonical_id((0, 1))


def test_count_state_guard_raises_explicit_limit():
    module = _module()
    with pytest.raises(module.SearchSpaceLimit) as caught:
        module.ExactPlanSpace(_candidates([1] * 16), 8, max_states=3)
    assert caught.value.states == 3
    assert caught.value.limit == 3
    assert caught.value.phase == "count"


@pytest.mark.parametrize("strategy", ["FIRST_N", "DIVERSE_N", "SMART_SEARCH"])
def test_selection_state_guard_returns_explicit_incomplete_result(strategy):
    space = _module().ExactPlanSpace(_candidates([1] * 16), 8)
    selected = space.select(strategy, 200, utilities=list(range(16)), max_states=1)
    assert selected.plans == []
    assert selected.reason == "SEARCH_STATE_LIMIT"
    assert selected.state_limit_reached
    assert selected.truncated and not selected.discovery_complete
    assert selected.visited_states == 1


@pytest.mark.parametrize("credits,target", [([-1], 1), (["NaN"], 1), (["Infinity"], 1), ([1], 0)])
def test_invalid_credit_values_cannot_enter_feasible_space(credits, target):
    with pytest.raises(ValueError):
        _module().ExactPlanSpace(_candidates(credits), target)


def test_no_matching_plan_is_complete_without_lowering_target():
    space = _module().ExactPlanSpace(_candidates([2, 2]), 3)
    selected = space.select("DIVERSE_N", 200)
    assert space.count == 0
    assert selected.plans == []
    assert selected.discovery_complete and not selected.truncated
    assert selected.reason == "NO_MATCHING_PLAN"


def test_empty_smart_scope_needs_no_utility_evidence():
    space = _module().ExactPlanSpace(_candidates([2, 2]), 3)
    selected = space.select("SMART_SEARCH", 200)
    assert selected.plans == []
    assert selected.discovery_complete
    assert selected.reason == "NO_MATCHING_PLAN"


def test_smart_search_matches_exhaustive_quality_order_with_negative_utilities():
    candidates = _candidates([1, 2, 0, 3, 1, 2, 1, 0])
    utilities = [Decimal("-0.25"), Decimal("0.1"), Decimal("9"),
                 Decimal("0.2"), Decimal("-0.1"), Decimal("0.05"),
                 Decimal("0.2"), Decimal("-1")]
    expected = list(enumerate_plan_indices(candidates, 4))
    weights = [Decimal(str(credits)) * utility
               for credits, utility in zip(candidates.course_credits, utilities)]
    ordered = sorted(range(len(expected)),
                     key=lambda rank: (-sum(weights[index] for index in expected[rank]), rank))
    space = _module().ExactPlanSpace(candidates, 4)
    selected = space.select("SMART_SEARCH", 200, utilities=utilities)
    assert selected.ranks == ordered
    assert selected.plans == [expected[rank] for rank in ordered]
    assert selected.discovery_complete


def test_duplicate_candidate_ids_cannot_form_distinct_course_combinations():
    candidates = pd.DataFrame({"course_id": ["a", "a"], "course_credits": [1, 1]})
    with pytest.raises(ValueError):
        _module().ExactPlanSpace(candidates, 2)


def test_rank_and_pool_reject_invalid_plans_and_ordinals():
    space = _module().ExactPlanSpace(_candidates([1] * 4), 2)
    for plan in [(0,), (0, 0), (1, 0), (0, 4)]:
        with pytest.raises(ValueError):
            space.rank(plan)
    for rank in [-1, 6, True, 1.2]:
        with pytest.raises(ValueError):
            space.unrank(rank)
    for pool in [[-1], [6], [1, 1]]:
        with pytest.raises(ValueError):
            space.select("FIRST_N", 2, pool=pool)
    with pytest.raises(ValueError):
        space.select("SMART_SEARCH", 2, utilities=[1])
    with pytest.raises(ValueError):
        space.select("SMART_SEARCH", 2, utilities=[1, 2, 3, float("nan")])
