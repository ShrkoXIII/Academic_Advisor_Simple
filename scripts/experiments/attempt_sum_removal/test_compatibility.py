import pandas as pd
import pytest

from scripts.experiments.attempt_sum_removal.compatibility import _compare, _aggregate_delta
from scripts.experiments.attempt_sum_removal.test_history import outcomes


def test_parity_checks_missingness_and_values():
    rows = pd.DataFrame({'a': [1., float('nan')]})
    assert _compare(rows, rows.copy(), ['a'])['a']['max_abs_diff'] == 0
    with pytest.raises(ValueError):
        _compare(rows, rows.fillna(0), ['a'])
    with pytest.raises(ValueError):
        _compare(rows, rows.assign(a=[2., float('nan')]), ['a'])


def test_aggregate_delta_uses_retained_raw_definitions():
    rows = outcomes().assign(part_id=20251)
    payload = _aggregate_delta(rows, 20251)
    assert payload['finalized'] is True
    assert sum(r['count'] for r in payload['aggregates']) == 2
    assert sum(r['retake_count'] for r in payload['aggregates']) == 1
    assert sum(r['mark_sum'] for r in payload['aggregates']) == 120
    assert all(set(r) == {'degree_id', 'course_id', 'faculty_id',
                         'plan_requirement_type_id', 'course_credits', 'count',
                         'retake_count', 'fail_count', 'mark_sum'}
               for r in payload['aggregates'])
