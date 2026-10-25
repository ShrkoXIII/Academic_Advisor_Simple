"""Counted exact-credit subsets and isolated benchmark selectors.

Candidates must already have passed the Pilot's candidate normalization. This
space enforces only nonnegative exact credits and one occurrence of each course;
it does not assert unverified requirement, retake, or registration policies.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import heapq
import json
import operator
import random
import sys
from time import perf_counter

from src.recommendation.plan_generation import decimal_credit_units


class SearchSpaceLimit(RuntimeError):
    """The exact state guard was reached; no completeness claim is available."""

    def __init__(self, states, limit, phase):
        self.states = states
        self.limit = limit
        self.phase = phase
        super().__init__(f"SEARCH_STATE_LIMIT: {phase} visited {states} states (limit {limit})")


@dataclass
class Selection:
    """Selected global DFS ordinals and explicit scope/resource accounting.

    ``unique_discovered`` counts unique plans returned for subsequent full-model
    scoring. Cheap per-course bounds and fixed-pool heuristic inspections are
    state work, not additional full-model evaluations. ``discovery_complete``
    means the returned plans cover this selection's full or fixed-pool scope.
    """

    plans: list[tuple[int, ...]]
    ranks: list[int]
    visited_states: int
    truncated: bool
    discovery_complete: bool
    unique_discovered: int
    reason: str
    state_limit_reached: bool
    scope_size: int
    preparation_seconds: float
    selection_seconds: float
    heuristic_preparation_seconds: float = 0.0
    heuristic_states: int = 0


def _integer(value, name, *, minimum=0):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    try:
        result = operator.index(value)
    except TypeError:
        raise ValueError(f"{name} must be an integer >= {minimum}") from None
    if result < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return result


def _decimal(value, name):
    try:
        result = Decimal(str(value))
    except (ValueError, InvalidOperation):
        raise ValueError(f"{name} must be finite") from None
    if not result.is_finite():
        raise ValueError(f"{name} must be finite")
    return result


class ExactPlanSpace:
    """Lazy DFS rank/unrank over every subset meeting one exact credit target.

    Counting is dynamic programming over ``(candidate index, remaining units)``.
    Integer Decimal units preserve the existing include-first DFS order, including
    optional zero-credit courses, without materializing the feasible universe.
    """

    def __init__(self, candidates, target_credits, *, max_states=2_000_000):
        started = perf_counter()
        self.max_states = _integer(max_states, "max_states", minimum=1)
        if not {"course_id", "course_credits"}.issubset(candidates.columns):
            raise ValueError("Candidates require course_id and course_credits")
        self.candidate_ids = [str(value) for value in candidates["course_id"]]
        if any(not value.strip() for value in self.candidate_ids) or len(set(self.candidate_ids)) != len(self.candidate_ids):
            raise ValueError("Candidate course IDs must be nonempty and unique")
        self.target_credits = _decimal(target_credits, "target_credits")
        if self.target_credits <= 0:
            raise ValueError("target_credits must be positive")
        credits = [_decimal(value, "course_credits") for value in candidates["course_credits"]]
        if any(value < 0 for value in credits):
            raise ValueError("course_credits must be nonnegative")
        self.decimal_places = max(0, *[-value.as_tuple().exponent for value in [*credits, self.target_credits]])
        self._units = tuple(decimal_credit_units(value, self.decimal_places) for value in credits)
        self._target = decimal_credit_units(self.target_credits, self.decimal_places)
        self._n = len(self._units)
        self._suffix = [0] * (self._n + 1)
        for i in range(self._n - 1, -1, -1):
            self._suffix[i] = self._suffix[i + 1] + self._units[i]
        self._counts = {}
        self.states = 0
        self.count = self._count(0, self._target)
        self.preparation_seconds = perf_counter() - started

    def _count(self, i, remaining):
        key = (i, remaining)
        if key in self._counts:
            return self._counts[key]
        if self.states >= self.max_states:
            raise SearchSpaceLimit(self.states, self.max_states, "count")
        self.states += 1
        if remaining < 0 or remaining > self._suffix[i]:
            result = 0
        elif i == self._n:
            result = int(remaining == 0)
        else:
            result = self._count(i + 1, remaining - self._units[i]) + self._count(i + 1, remaining)
        self._counts[key] = result
        return result

    def _ordinal(self, rank):
        rank = _integer(rank, "rank")
        if rank >= self.count:
            raise ValueError("rank is outside the feasible space")
        return rank

    def _unrank(self, rank, tick=None):
        remaining, selected = self._target, []
        for i, credits in enumerate(self._units):
            if tick is not None:
                tick()
            include_count = self._counts.get((i + 1, remaining - credits), 0)
            if rank < include_count:
                selected.append(i)
                remaining -= credits
            else:
                rank -= include_count
        if tick is not None:
            tick()
        return tuple(selected)

    def unrank(self, rank):
        """Return the indexed feasible plan; rank zero is the first DFS plan."""
        return self._unrank(self._ordinal(rank))

    def rank(self, plan):
        """Return a feasible plan's global ordinal in the original DFS order."""
        indices = tuple(_integer(index, "plan index") for index in plan)
        if any(index >= self._n for index in indices) or tuple(sorted(set(indices))) != indices:
            raise ValueError("Plan indices must be increasing, unique, and in range")
        if sum(self._units[index] for index in indices) != self._target:
            raise ValueError("Plan does not meet the exact credit target")
        selected = set(indices)
        remaining, rank = self._target, 0
        for i, credits in enumerate(self._units):
            if i in selected:
                remaining -= credits
            else:
                rank += self._counts.get((i + 1, remaining - credits), 0)
        return rank

    def canonical_id(self, plan):
        """Hash sorted course IDs, independently of candidate row ordering."""
        plan = tuple(plan)
        self.rank(plan)
        payload = json.dumps(sorted(self.candidate_ids[i] for i in plan),
                             ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _weights(self, utilities):
        if utilities is None:
            raise ValueError("SMART_SEARCH requires precomputed per-course utilities")
        utilities = list(utilities)
        if len(utilities) != self._n:
            raise ValueError("Utilities must contain one value per candidate")
        values = [_decimal(value, "utility") for value in utilities]
        places = max([0, *[-value.as_tuple().exponent for value in values]])
        return [credits * decimal_credit_units(value, places)
                for credits, value in zip(self._units, values)]

    def select(self, strategy, budget, seed=42, pool=None, utilities=None, max_states=2_000_000):
        """Select unique feasible plans under a bounded amount of selector work.

        DIVERSE_N is uniform sampling without replacement from feasible global
        ranks (or supplied pool), not a diversity claim about course composition.
        SMART_SEARCH uses exact credit-weighted additive utility bounds and a
        best-first branch queue. Utilities must be computed from allowed prior
        information by the caller; no model or oracle is accessed here.
        """
        started = perf_counter()
        budget = _integer(budget, "budget")
        limit = _integer(max_states, "max_states", minimum=1)
        if strategy not in {"FIRST_N", "DIVERSE_N", "SMART_SEARCH"}:
            raise ValueError("Unknown search strategy")
        if pool is not None:
            pool = [self._ordinal(rank) for rank in pool]
            if len(set(pool)) != len(pool):
                raise ValueError("Pool ranks must be unique")
        scope_size = self.count if pool is None else len(pool)
        requested = min(budget, scope_size)
        weights = self._weights(utilities) if strategy == "SMART_SEARCH" and requested else None
        plans, ranks = [], []
        visited, heuristic_states = 0, 0
        heuristic_seconds = 0.0
        limited = False

        def tick():
            nonlocal visited
            if visited >= limit:
                raise SearchSpaceLimit(visited, limit, "selection")
            visited += 1

        try:
            if requested and strategy in {"FIRST_N", "DIVERSE_N"}:
                if strategy == "FIRST_N":
                    chosen = range(requested) if pool is None else sorted(pool)[:requested]
                else:
                    rng = random.Random(seed)
                    if pool is not None:
                        chosen = rng.sample(pool, requested)
                    elif self.count <= sys.maxsize:
                        chosen = rng.sample(range(self.count), requested)
                    else:
                        # random.sample's large-population set algorithm, with
                        # arbitrary-size Python integers rather than len(range).
                        chosen, seen = [], set()
                        while len(chosen) < requested:
                            ordinal = rng.randrange(self.count)
                            if ordinal not in seen:
                                seen.add(ordinal)
                                chosen.append(ordinal)
                for ordinal in chosen:
                    plan = self._unrank(ordinal, tick)
                    plans.append(plan)
                    ranks.append(ordinal)
            elif requested and pool is not None:
                scored = []
                try:
                    for ordinal in pool:
                        plan = self._unrank(ordinal, tick)
                        scored.append((-sum(weights[index] for index in plan), ordinal, plan))
                finally:
                    scored.sort()
                    for _, ordinal, plan in scored[:requested]:
                        plans.append(plan)
                        ranks.append(ordinal)
            elif requested:
                best = {}
                heuristic_started = perf_counter()

                def bound(i, remaining):
                    nonlocal heuristic_states
                    key = (i, remaining)
                    if key in best:
                        return best[key]
                    tick()
                    heuristic_states += 1
                    if i == self._n:
                        result = 0
                    else:
                        options = []
                        if self._counts.get((i + 1, remaining - self._units[i]), 0):
                            options.append(weights[i] + bound(i + 1, remaining - self._units[i]))
                        if self._counts.get((i + 1, remaining), 0):
                            options.append(bound(i + 1, remaining))
                        result = max(options)
                    best[key] = result
                    return result

                try:
                    root_bound = bound(0, self._target)
                finally:
                    heuristic_seconds = perf_counter() - heuristic_started
                # Subtree ordinals are contiguous. Their first ordinal is a
                # deterministic tie breaker for equal optimistic quality.
                queue = [(-root_bound, 0, 0, self._target, (), 0)]
                while queue and len(plans) < requested:
                    tick()
                    _, ordinal, i, remaining, plan, score = heapq.heappop(queue)
                    if i == self._n:
                        plans.append(plan)
                        ranks.append(ordinal)
                        continue
                    next_remaining = remaining - self._units[i]
                    included = self._counts.get((i + 1, next_remaining), 0)
                    if included:
                        next_score = score + weights[i]
                        heapq.heappush(queue, (-(next_score + best[(i + 1, next_remaining)]),
                                               ordinal, i + 1, next_remaining, (*plan, i), next_score))
                    if self._counts.get((i + 1, remaining), 0):
                        heapq.heappush(queue, (-(score + best[(i + 1, remaining)]),
                                               ordinal + included, i + 1, remaining, plan, score))
        except SearchSpaceLimit:
            limited = True
        complete = len(plans) == scope_size
        reason = ("SEARCH_STATE_LIMIT" if limited else "NO_MATCHING_PLAN" if scope_size == 0
                  else "COMPLETE" if complete else "BUDGET_REACHED")
        return Selection(plans=plans, ranks=ranks, visited_states=visited,
                         truncated=not complete, discovery_complete=complete,
                         unique_discovered=len(plans), reason=reason,
                         state_limit_reached=limited, scope_size=scope_size,
                         preparation_seconds=self.preparation_seconds + heuristic_seconds,
                         selection_seconds=max(0.0, perf_counter() - started - heuristic_seconds),
                         heuristic_preparation_seconds=heuristic_seconds,
                         heuristic_states=heuristic_states)
