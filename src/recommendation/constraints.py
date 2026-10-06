"""Pure requirement and official-repeat credit limits for the payload core."""
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import numpy as np
import pandas as pd

from src.data.cleaning_utils import clean_id
from .plan_generation import enumerate_plan_indices


_CANDIDATE_GROUPS = {"NEW", "FAILED_RETAKE", "WITHDRAWN_RETAKE", "OTHER_PREVIOUS"}


def _credit_value(value, field, *, positive=False):
    """Preserve decimal credit precision; reject missing and non-finite values."""
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{field} must be numeric credits, not a boolean.")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{field} must contain finite nonnegative credits.") from None
    if not result.is_finite() or result < 0 or (positive and result == 0):
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{field} must contain finite {qualifier} credits.")
    return result


def _requirement_id(value):
    normalized = clean_id(pd.Series([value])).iloc[0]
    if pd.isna(normalized):
        raise ValueError("Requirement policy ID must be present.")
    return str(normalized)


def normalize_requirement_policies(records):
    """Return remaining credits keyed by normalized requirement ID.

    Records require ``plan_requirement_type_id`` and ``requirement_max_credits``
    (or the compatible ``max_credits`` alias). Missing overflow, completed, and
    reserved adjustments mean zero; explicit missing values are invalid.
    """
    if not isinstance(records, list):
        raise ValueError("Requirement policies must be a list of records.")
    result = {}
    for record in records:
        if not isinstance(record, Mapping):
            raise ValueError("Each requirement policy must be a record.")
        if "plan_requirement_type_id" not in record:
            raise ValueError("Requirement policy is missing plan_requirement_type_id.")
        requirement_id = _requirement_id(record["plan_requirement_type_id"])
        if requirement_id in result:
            raise ValueError(f"Duplicate requirement policy: {requirement_id}.")
        aliases = [name for name in ("requirement_max_credits", "max_credits") if name in record]
        if not aliases:
            raise ValueError(f"Requirement policy {requirement_id} is missing requirement_max_credits.")
        maximum = _credit_value(record[aliases[0]], aliases[0])
        if len(aliases) == 2 and maximum != _credit_value(record[aliases[1]], aliases[1]):
            raise ValueError(f"Conflicting requirement max credit aliases: {requirement_id}.")
        overflow = _credit_value(record.get("allowed_overflow_credits", 0), "allowed_overflow_credits")
        completed = _credit_value(record.get("completed_credits", 0), "completed_credits")
        reserved = _credit_value(record.get("reserved_credits", 0), "reserved_credits")
        result[requirement_id] = max(Decimal("0"), maximum + overflow - completed - reserved)
    return result


@dataclass(frozen=True)
class PlanConstraints:
    """Exact target and independent caps; requirement policies contain remaining credits."""

    target_credits: Decimal
    requirement_policies: dict[str, Decimal]
    allowed_failed_repeat_credits: Decimal
    allowed_withdrawn_repeat_credits: Decimal | None = None

    def __post_init__(self):
        object.__setattr__(self, "target_credits", _credit_value(self.target_credits, "target_credits", positive=True))
        if not isinstance(self.requirement_policies, Mapping):
            raise ValueError("requirement_policies must map IDs to remaining credits.")
        policies = {}
        for key, value in self.requirement_policies.items():
            requirement_id = _requirement_id(key)
            if requirement_id in policies:
                raise ValueError(f"Duplicate requirement policy: {requirement_id}.")
            policies[requirement_id] = _credit_value(value, "remaining requirement credits")
        object.__setattr__(self, "requirement_policies", policies)
        object.__setattr__(self, "allowed_failed_repeat_credits", _credit_value(
            self.allowed_failed_repeat_credits, "allowed_failed_repeat_credits",
        ))
        if self.allowed_withdrawn_repeat_credits is not None:
            object.__setattr__(self, "allowed_withdrawn_repeat_credits", _credit_value(
                self.allowed_withdrawn_repeat_credits, "allowed_withdrawn_repeat_credits",
            ))


def enumerate_feasible_plan_indices(candidates, constraints):
    """Yield every exact-credit subset satisfying requirement and official-repeat caps.

    The existing exhaustive Decimal search defines subset order and optional
    zero-credit selections. This wrapper filters complete subsets without
    removing candidates, scoring plans, or changing the search algorithm.
    """
    if not isinstance(constraints, PlanConstraints):
        raise ValueError("Supply normalized PlanConstraints.")
    required = {"course_credits", "plan_requirement_type_id", "candidate_group"}
    missing = required - set(candidates.columns)
    if missing:
        raise ValueError(f"Missing candidate constraint columns: {sorted(missing)}.")
    credits = [_credit_value(value, "course_credits") for value in candidates["course_credits"]]
    requirements = [_requirement_id(value) for value in candidates["plan_requirement_type_id"]]
    groups = []
    for value in candidates["candidate_group"]:
        group = str(value).strip().upper()
        if group not in _CANDIDATE_GROUPS:
            raise ValueError(f"Invalid official candidate_group: {value}.")
        groups.append(group)
    uncovered = set(requirements) - set(constraints.requirement_policies)
    if uncovered:
        raise ValueError(f"Missing requirement policy for candidates: {sorted(uncovered)}.")

    for plan in enumerate_plan_indices(candidates, target_credits=constraints.target_credits):
        consumed = {}
        failed = withdrawn = Decimal("0")
        feasible = True
        for index in plan:
            requirement_id, cost = requirements[index], credits[index]
            consumed[requirement_id] = consumed.get(requirement_id, Decimal("0")) + cost
            if consumed[requirement_id] > constraints.requirement_policies[requirement_id]:
                feasible = False
                break
            if groups[index] == "FAILED_RETAKE":
                failed += cost
            elif groups[index] == "WITHDRAWN_RETAKE":
                withdrawn += cost
            if (failed > constraints.allowed_failed_repeat_credits
                    or (constraints.allowed_withdrawn_repeat_credits is not None
                        and withdrawn > constraints.allowed_withdrawn_repeat_credits)):
                feasible = False
                break
        if feasible:
            yield plan
