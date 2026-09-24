"""Credit-bound validation and exhaustive plan-row generation."""
from decimal import Decimal

import numpy as np


def resolve_credit_bounds(credits=None, min_credits=None, max_credits=None):
    """A single value becomes equal bounds; a range keeps both inclusive bounds."""
    if credits is not None:
        if min_credits is not None or max_credits is not None:
            raise ValueError("Use credits OR min_credits/max_credits, not both.")
        lower = upper = Decimal(str(credits))
    else:
        if min_credits is None or max_credits is None:
            raise ValueError("Supply credits or both min_credits and max_credits.")
        lower, upper = Decimal(str(min_credits)), Decimal(str(max_credits))
    if not lower.is_finite() or not upper.is_finite() or lower < 0 or upper <= 0 or lower > upper:
        raise ValueError("Invalid credit bounds: require 0 <= min <= max and max > 0.")
    return lower, upper


def enumerate_plan_indices(candidate_courses, target_credits=None, *, min_credits=None, max_credits=None):
    """Yield all positive-credit subsets within inclusive bounds, without rounding.

    Zero-credit courses remain optional members even after reaching the upper bound.
    """
    values = [Decimal(str(v)) for v in candidate_courses["course_credits"]]
    lower, upper = resolve_credit_bounds(target_credits, min_credits, max_credits)
    if any(not v.is_finite() or v < 0 for v in values):
        raise ValueError("Course credits must be finite and nonnegative.")
    scale = 10 ** max(0, *[-v.as_tuple().exponent for v in [*values, lower, upper]])
    units = [int(v * scale) for v in values]
    minimum, maximum = int(lower * scale), int(upper * scale)
    suffix = [0] * (len(units) + 1)
    for i in range(len(units) - 1, -1, -1):
        suffix[i] = suffix[i + 1] + units[i]

    def visit(i, total, selected):
        if total > maximum or total + suffix[i] < minimum:
            return
        if i == len(units):
            if minimum <= total <= maximum and total > 0:
                yield selected
            return
        yield from visit(i + 1, total + units[i], (*selected, i))
        yield from visit(i + 1, total, selected)

    yield from visit(0, 0, ())


def build_plan_rows(candidates, plans, first_plan_id=0):
    lengths = np.array([len(p) for p in plans], dtype="int64")
    indices = np.fromiter((i for plan in plans for i in plan), dtype="int64")
    rows = candidates.iloc[indices].reset_index(drop=True).copy()
    rows["plan_id"] = np.repeat(np.arange(first_plan_id, first_plan_id + len(plans)), lengths)
    return rows
