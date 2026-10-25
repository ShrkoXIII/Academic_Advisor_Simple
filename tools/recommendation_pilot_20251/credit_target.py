"""Resolve exact experiment credits from the saved Courses API load contract.

The normal range is MIN_CREDITS..MAX_CREDITS with LOAD_TYPE=CREDIT. Only an
explicit, sourced, semester-scoped integration registration policy activates
the study/graduation intersection used by src.api.validators.courses._rules.
Course counts, requirement groups and candidate supply never define the load.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation


def _credit(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value))
        return parsed if parsed.is_finite() and parsed >= 0 else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def resolve_credit_target(inputs, manual_target=None, *, diagnostic_override=False):
    """Return resolved bounds/provenance or a blocking reason without inference."""
    data = (inputs.get('courses_api_response') or {}).get('data') or {}
    rules = data.get('registserRule')
    rules = rules if isinstance(rules, dict) else {}
    minimum, maximum = _credit(rules.get('MIN_CREDITS')), _credit(rules.get('MAX_CREDITS'))
    evidence = {'normal_bounds_source': 'Courses API.data.registserRule',
                'load_profile': None, 'load_profile_status': 'UNCONFIRMED',
                'precedence': 'normal credit bounds intersect explicit scoped policy profile',
                'ignored_as_credit_limits': ['MAX_NEW_COURSES', 'requirement groups', 'candidate credit sum']}
    result = {'status': 'UNRESOLVED', 'reason': None, 'target_credits': None,
              'target_credits_source': 'MANUAL_DIAGNOSTIC' if manual_target is not None else 'API',
              'minimum_credits': float(minimum) if minimum is not None else None,
              'maximum_credits': float(maximum) if maximum is not None else None,
              'raw_rules': deepcopy(rules), 'policy_evidence': evidence}

    def blocked(reason):
        result['reason'] = reason
        return result

    if manual_target is not None and not diagnostic_override:
        return blocked('DIAGNOSTIC_OVERRIDE_NOT_ENABLED')
    if rules.get('LOAD_TYPE') != 'CREDIT':
        return blocked('UNRESOLVED_LOAD_TYPE')
    policy = (inputs.get('integration_context') or {}).get('registration_policy')
    if policy is not None:
        if not isinstance(policy, dict):
            return blocked('UNRESOLVED_LOAD_PROFILE')
        evidence['registration_policy'] = deepcopy(policy)
        source = policy.get('source')
        expected_part = (inputs.get('identity') or {}).get('part_id')
        part = _credit(policy.get('part_id'))
        if not isinstance(source, str) or not source.strip() or part is None or part != _credit(expected_part):
            return blocked('UNCONFIRMED_REGISTRATION_POLICY')
        profile = policy.get('load_profile')
        if profile not in {'study', 'graduation'}:
            return blocked('UNRESOLVED_LOAD_PROFILE')
        lo, hi = (('MIN_STUDY_CREDITS', 'MAX_STUDY_CREDITS') if profile == 'study'
                  else ('GRAD_MIN_LIMIT', 'GRAD_MAX_LOAD'))
        lower, upper = _credit(rules.get(lo)), _credit(rules.get(hi))
        evidence.update(load_profile=profile, load_profile_status='EXPLICIT_SCOPED_POLICY',
                        applied_profile_fields=[lo, hi])
        # Retain every known applicable bound even if its partner is missing.
        minimum = max(v for v in (minimum, lower) if v is not None) if minimum is not None or lower is not None else None
        maximum = min(v for v in (maximum, upper) if v is not None) if maximum is not None or upper is not None else None
        result.update(minimum_credits=float(minimum) if minimum is not None else None,
                      maximum_credits=float(maximum) if maximum is not None else None)
        if lower is None or upper is None:
            return blocked('PROFILE_CREDIT_LIMITS_UNAVAILABLE')
        if lower > upper:
            return blocked('CONFLICTING_CREDIT_LIMITS')
    if minimum is not None and maximum is not None and minimum > maximum:
        return blocked('CONFLICTING_CREDIT_LIMITS')
    if manual_target is not None:
        target = _credit(manual_target)
        if target is None or target <= 0:
            return blocked('INVALID_TARGET_CREDITS')
        if minimum is not None and target < minimum or maximum is not None and target > maximum:
            return blocked('REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS')
    else:
        # A profile intersection cannot repair a missing normal contract bound.
        if _credit(rules.get('MAX_CREDITS')) is None:
            return blocked('CREDIT_MAXIMUM_UNAVAILABLE')
        if _credit(rules.get('MIN_CREDITS')) is None:
            return blocked('CREDIT_MINIMUM_UNAVAILABLE')
        target = maximum
        if target is None or target <= 0:
            return blocked('INVALID_TARGET_CREDITS')
    result.update(status='RESOLVED', target_credits=float(target))
    return result
