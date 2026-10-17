"""Read-only official references; experimental history performs no file I/O."""
from copy import deepcopy

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.features.feature_contract import BASE_FEATURES, prepare_model_matrix
from src.features.temporal_features import CourseHistoryState, compute_plan_context_features
from scripts.experiments.attempt_sum_removal.contract import (
    FULL_FEATURES, SHORTLIST_FEATURES, REMOVED_FEATURES, HISTORY_COLUMNS,
    PLAN_COLUMNS, SUM_COLUMNS,
)
from scripts.experiments.attempt_sum_removal.history import (
    ReducedCourseHistoryState, apply_delta, build_history_prefix, compute_plan_context,
)


def outcomes():
    return pd.DataFrame([
        dict(student_id='s', degree_id='d', course_id='a', faculty_id='f',
             plan_requirement_type_id='r', course_credits=3., part_id=20211,
             final_mark=40., attempt_number=2.),
        dict(student_id='s', degree_id='d', course_id='b', faculty_id='f',
             plan_requirement_type_id='r', course_credits=3., part_id=20221,
             final_mark=80., attempt_number=1.),
    ])


def delta(**changes):
    value = dict(finalized=True, delta_part=20231, aggregates=[dict(
        degree_id='d', course_id='b', faculty_id='f', plan_requirement_type_id='r',
        course_credits=3, count=2, fail_count=1, retake_count=1, mark_sum=110)])
    value.update(changes)
    return value


def test_contract_and_candidate_feature_order():
    assert len(FULL_FEATURES) == 44 and len(SHORTLIST_FEATURES) == 32
    assert len(HISTORY_COLUMNS) == 6 and len(PLAN_COLUMNS) == 12
    assert set(BASE_FEATURES) - set(FULL_FEATURES) == set(REMOVED_FEATURES)
    assert FULL_FEATURES == [c for c in BASE_FEATURES if c not in REMOVED_FEATURES]
    assert 'attempt_number' in FULL_FEATURES and 'attempt_number' in SHORTLIST_FEATURES
    assert 'course_history_retake_rate' in FULL_FEATURES
    rows = pd.DataFrame({c: [2] for c in FULL_FEATURES})
    categories = {c: ['__MISSING__', '__UNKNOWN__', '2'] for c in
                  ['plan_course_type_id', 'plan_requirement_type_id', 'diploma_type_id',
                   'grade_version_id', 'part_semester']}
    for names in (FULL_FEATURES, SHORTLIST_FEATURES):
        matrix = prepare_model_matrix(rows, categories, model_features=names)
        assert matrix.columns.tolist() == names
        assert matrix.at[0, 'attempt_number'] == 2


@pytest.mark.parametrize('empty', [True, False])
def test_history_parity_all_fallbacks_and_empty(empty):
    source = outcomes()
    official, reduced = CourseHistoryState(), ReducedCourseHistoryState()
    if not empty:
        official.update(source)
        reduced.update(source)
    rows = pd.concat([source.iloc[[0]]] * 6, ignore_index=True)
    rows['part_id'] = 20231
    rows.loc[1:, 'course_id'] = 'unknown'
    rows.loc[1, 'course_id'] = 'a'
    rows.loc[1, 'degree_id'] = 'other'
    rows.loc[3:, 'degree_id'] = 'other'
    rows.loc[4:, 'faculty_id'] = 'other'
    rows.loc[5, 'plan_requirement_type_id'] = 'other'
    actual = reduced.apply(rows)
    assert_frame_equal(actual, official.apply(rows)[HISTORY_COLUMNS])
    if not empty:
        assert actual.course_history_fallback_level.tolist() == [1, 2, 3, 4, 5, 6]
        assert reduced.global_sums['effective_support'] == 1.25
        assert reduced.global_sums['retake_sum'] == .25
    assert set(reduced.global_sums) == set(SUM_COLUMNS)
    for table in reduced.tables.values():
        assert table.columns.tolist() == SUM_COLUMNS


def test_temporal_prefix_excludes_target_future_and_update_order():
    rows = outcomes()
    state = build_history_prefix(rows, target_part=20221)
    assert state.as_of_part == 20211
    assert state.global_sums['raw_count'] == 1
    with pytest.raises(ValueError):
        state.apply(rows.iloc[[0]])
    with pytest.raises(ValueError):
        state.update(rows.iloc[[0]])
    state.apply(rows.iloc[[1]])
    assert build_history_prefix(rows, target_part=20201).as_of_part is None


def test_delta_without_removed_aggregate_matches_raw_and_is_pure():
    state = ReducedCourseHistoryState()
    state.update(outcomes())
    before = deepcopy(state)
    updated = apply_delta(state, delta())
    reference = deepcopy(state)
    raw = pd.concat([outcomes().iloc[[1]]] * 2, ignore_index=True)
    raw['part_id'] = 20231
    raw['final_mark'] = [40., 70.]
    raw['attempt_number'] = [2., 1.]
    reference.update(raw)
    assert state.global_sums == before.global_sums
    assert updated.global_sums == reference.global_sums
    for level in range(1, 6):
        assert_frame_equal(updated.tables[level].sort_index(), reference.tables[level].sort_index())


@pytest.mark.parametrize('mutation', [
    lambda p: p.update(finalized=False),
    lambda p: p.update(delta_part=20221),
    lambda p: p.update(delta_part=99991),
    lambda p: p['aggregates'].append(dict(p['aggregates'][0])),
    lambda p: p['aggregates'][0].update(count=True),
    lambda p: p['aggregates'][0].update(fail_count=3),
    lambda p: p['aggregates'][0].update(mark_sum=10),
    lambda p: p['aggregates'][0].update(retake_count=3),
    lambda p: p['aggregates'][0].update(part_id=20232),
    lambda p: p['aggregates'][0].update(course_id='x||y'),
])
def test_delta_rejects_invalid(mutation):
    state = ReducedCourseHistoryState()
    state.update(outcomes())
    payload = delta()
    mutation(payload)
    with pytest.raises(ValueError):
        apply_delta(state, payload)


def test_delta_preserves_exact_weighted_counts():
    state = ReducedCourseHistoryState()
    state.update(outcomes().iloc[[0]])
    payload = delta()
    payload['aggregates'][0].update(count=2**52, fail_count=0, retake_count=0,
                                   mark_sum=60 * 2**52)
    with pytest.raises(ValueError, match='exact'):
        apply_delta(state, payload)


def test_context_parity_missing_singletons_and_nondefault_groups():
    rows = pd.concat([outcomes(), outcomes()], ignore_index=True)
    rows['part_id'] = [20231, 20231, 20232, 20233]
    rows['course_credits'] = [3., np.nan, 0., 2.]
    rows['course_history_fail_rate'] = [.8, np.nan, .8, .2]
    rows['course_history_avg_mark'] = [30., 75., np.nan, 80.]
    rows['course_history_avg_attempt'] = [2., 1., 2., 1.]
    for groups in (None, ['degree_id']):
        reference = compute_plan_context_features(rows, groups)[PLAN_COLUMNS]
        reduced = rows.drop(columns=['course_history_avg_attempt'])
        assert_frame_equal(compute_plan_context(reduced, groups), reference)


def test_history_path_performs_no_filesystem_writes(monkeypatch):
    import builtins
    def forbidden(*args, **kwargs):
        raise AssertionError('History path must perform no filesystem I/O')
    monkeypatch.setattr(builtins, 'open', forbidden)
    state = build_history_prefix(outcomes(), target_part=20231)
    state = apply_delta(state, delta())
    rows = outcomes().assign(part_id=20241)
    computed = state.apply(rows)
    compute_plan_context(pd.concat([rows, computed], axis=1))


def test_full_training_inference_parity_and_dense_support():
    source = pd.concat([outcomes()] * 30, ignore_index=True)
    official, reduced = CourseHistoryState(), ReducedCourseHistoryState()
    official.update(source)
    reduced.update(source)
    rows = outcomes().assign(part_id=20231)
    for column in BASE_FEATURES:
        if column not in rows:
            rows[column] = 1
    expected = rows.copy()
    expected[official.apply(rows).columns] = official.apply(rows)
    expected[compute_plan_context_features(expected).columns] = compute_plan_context_features(expected)
    actual = rows.drop(columns=list(REMOVED_FEATURES))
    actual[HISTORY_COLUMNS] = reduced.apply(actual)
    actual[PLAN_COLUMNS] = compute_plan_context(actual)
    assert actual.course_history_missing.tolist() == [1, 0]
    for names in (FULL_FEATURES, SHORTLIST_FEATURES):
        assert_frame_equal(actual[names], expected[names])


def test_sparse_key_existence_overrides_denser_fallback():
    source = pd.concat([outcomes().iloc[[1]]] * 25 + [outcomes().iloc[[0]]], ignore_index=True)
    official, reduced = CourseHistoryState(), ReducedCourseHistoryState()
    official.update(source)
    reduced.update(source)
    rows = outcomes().iloc[[0]].assign(part_id=20231)
    result = reduced.apply(rows)
    assert_frame_equal(result, official.apply(rows)[HISTORY_COLUMNS])
    assert result.iloc[0].course_history_fallback_level == 1
    assert result.iloc[0].course_history_effective_support == .25
    assert result.iloc[0].course_history_missing == 1


def test_no_support_global_and_present_zero_support_key_match_reference():
    official, reduced = CourseHistoryState(), ReducedCourseHistoryState()
    rows = outcomes().iloc[[0]].assign(part_id=20231)
    for state in (official, reduced):
        state.tables[1].loc['d||a'] = 0.
    assert_frame_equal(reduced.apply(rows), official.apply(rows)[HISTORY_COLUMNS])


def test_normalized_duplicate_credit_grain_and_malformed_state_rejected():
    state = ReducedCourseHistoryState()
    payload = delta()
    payload['aggregates'].append(dict(payload['aggregates'][0], course_credits='3.0'))
    with pytest.raises(ValueError, match='Duplicate'):
        apply_delta(state, payload)
    state.global_sums['raw_count'] = 1
    with pytest.raises(ValueError):
        apply_delta(state, delta())


def test_delta_can_advance_empty_history_but_reject_replay():
    empty = ReducedCourseHistoryState()
    result = apply_delta(empty, delta(aggregates=[]))
    assert result.as_of_part == 20231 and empty.as_of_part is None
    assert result.global_sums == empty.global_sums
    with pytest.raises(ValueError, match='out-of-order'):
        apply_delta(result, delta())


def test_context_ties_missing_groups_and_missing_values_parity():
    rows = pd.concat([outcomes()] * 3, ignore_index=True)
    rows['part_id'] = 20231
    rows['student_id'] = ['a', 'a', 'a', 'b', None, None]
    rows['course_history_fail_rate'] = [.8, .8, .1, np.nan, np.nan, .2]
    rows['course_history_avg_mark'] = [20., 30., 80., np.nan, 50., np.nan]
    rows['course_history_avg_attempt'] = 1.
    reference = compute_plan_context_features(rows)[PLAN_COLUMNS]
    assert_frame_equal(compute_plan_context(rows.drop(columns='course_history_avg_attempt')), reference)
