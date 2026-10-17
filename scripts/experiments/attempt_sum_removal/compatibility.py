"""Replay retained V2 features with reduced history, without modifying inputs."""
from copy import deepcopy
import json
from pathlib import Path
import pickle

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from src import paths
from src.features.feature_contract import load_category_levels, prepare_model_matrix
from .contract import FULL_FEATURES, SHORTLIST_FEATURES, HISTORY_COLUMNS, PLAN_COLUMNS, REMOVED_FEATURES, SUM_COLUMNS
from .history import ReducedCourseHistoryState, compute_plan_context, apply_delta


def _compare(actual, expected, columns):
    result = {}
    for name in columns:
        a = pd.to_numeric(actual[name], errors='raise').to_numpy(dtype=float)
        b = pd.to_numeric(expected[name], errors='raise').to_numpy(dtype=float)
        if not np.array_equal(np.isnan(a), np.isnan(b)):
            raise ValueError(f'Replay missingness mismatch: {name}')
        finite = ~np.isnan(a)
        difference = float(np.max(np.abs(a[finite] - b[finite]))) if finite.any() else 0.
        if not np.allclose(a, b, rtol=1e-12, atol=1e-10, equal_nan=True):
            raise ValueError(f'Replay value mismatch {name}: maxdiff={difference}')
        result[name] = {'max_abs_diff': difference, 'missing_count': int(np.isnan(a).sum())}
    return result


def _aggregate_delta(outcomes, part):
    grain = ['degree_id', 'course_id', 'faculty_id', 'plan_requirement_type_id', 'course_credits']
    work = outcomes[grain].copy()
    work['count'] = 1
    work['fail_count'] = pd.to_numeric(outcomes.final_mark).lt(50).astype(int)
    work['retake_count'] = pd.to_numeric(outcomes.attempt_number).gt(1).astype(int)
    work['mark_sum'] = pd.to_numeric(outcomes.final_mark)
    records = work.groupby(grain, sort=False, dropna=False, observed=True)[
        ['count', 'fail_count', 'retake_count', 'mark_sum']].sum().reset_index().to_dict('records')
    return {'delta_part': int(part), 'finalized': True, 'aggregates': records}


def _compare_states(actual, expected):
    for level in range(1, 6):
        assert_frame_equal(actual.tables[level].sort_index(), expected.tables[level].sort_index(),
                           check_exact=False, rtol=1e-12, atol=1e-8)
    for name in SUM_COLUMNS:
        if not np.isclose(actual.global_sums[name], expected.global_sums[name], rtol=1e-12, atol=1e-8):
            raise ValueError(f'Delta aggregate mismatch: {name}')
    if actual.as_of_part != expected.as_of_part:
        raise ValueError('Delta cutoff mismatch')


def replay(train, test, evidence_dir):
    """Walk original finalized outcomes and rosters; save new reduced snapshots.

    ``train`` and ``test`` are original V2 feature DataFrames. Numeric feature
    parity uses rtol=1e-12, atol=1e-10 and exact missingness; final float32 and
    categorical model matrices must match exactly including order and dtypes.
    Saves only into a newly created ``evidence_dir/reduced_history`` directory.
    """
    destination = Path(evidence_dir) / 'reduced_history'
    if destination.exists():
        raise FileExistsError(f'Replay evidence already exists: {destination}')
    state = ReducedCourseHistoryState()
    levels = load_category_levels(paths.CATEGORY_LEVELS_PATH_V2)
    report = {'splits': {}, 'snapshots': {}, 'delta_check': None,
              'feature_counts': {'full': len(FULL_FEATURES), 'shortlist': len(SHORTLIST_FEATURES)},
              'finalization': 'Local saved finalized outcomes attest finalized=True; API semantics unverified',
              'numeric_tolerance': {'rtol': 1e-12, 'atol': 1e-10},
              'matrix_comparison': 'exact values, missingness, column order, dtypes and categories'}
    snapshots = {}
    for split, original, roster_path in (
        ('train', train, paths.TEMPORAL_TRAIN_ROSTER_PATH_V2),
        ('test', test, paths.TEMPORAL_TEST_ROSTER_PATH_V2),
    ):
        clean = original.drop(columns=list(REMOVED_FEATURES), errors='ignore').reset_index(drop=True)
        roster = pd.read_parquet(roster_path).drop(columns=list(REMOVED_FEATURES), errors='ignore')
        if roster.student_course_id.duplicated().any() or clean.student_course_id.duplicated().any():
            raise ValueError('Replay requires unique student_course_id keys')
        reconstructed = clean.copy()
        parts = sorted(set(clean.part_id) | set(roster.part_id))
        history_results, context_results = [], []
        for part in parts:
            mask = clean.part_id.eq(part)
            target = clean.loc[mask]
            part_roster = roster.loc[roster.part_id.eq(part)].copy()
            history = state.apply(target)
            reconstructed.loc[mask, HISTORY_COLUMNS] = history.to_numpy()
            roster_history = state.apply(part_roster)
            part_roster[HISTORY_COLUMNS] = roster_history.to_numpy()
            context = compute_plan_context(part_roster)
            context.index = part_roster.student_course_id
            aligned = context.reindex(target.student_course_id)
            if not target.student_course_id.isin(context.index).all():
                raise ValueError('Finalized outcome absent from original roster')
            reconstructed.loc[mask, PLAN_COLUMNS] = aligned.to_numpy()
            history_results.append(_compare(history.reset_index(drop=True), target.reset_index(drop=True), HISTORY_COLUMNS))
            context_results.append(_compare(aligned.reset_index(drop=True), target.reset_index(drop=True), PLAN_COLUMNS))
            if int(part) == 20251:
                delta_state = apply_delta(state, _aggregate_delta(target, part))
                raw_state = deepcopy(state)
                raw_state.update(target)
                _compare_states(delta_state, raw_state)
                report['delta_check'] = {'part': 20251, 'rows': len(target), 'passed': True,
                                         'aggregate_rows': len(_aggregate_delta(target, part)['aggregates']),
                                         'sums': SUM_COLUMNS}
            state.update(target)
            if int(part) in (20243, 20251):
                snapshots[int(part)] = deepcopy(state)
        columns = HISTORY_COLUMNS + PLAN_COLUMNS
        parity = _compare(reconstructed, clean, columns)
        matrices = {}
        for family, features in [('full', FULL_FEATURES), ('shortlist', SHORTLIST_FEATURES)]:
            rebuilt_matrix = prepare_model_matrix(reconstructed, levels, model_features=features)
            saved_matrix = prepare_model_matrix(clean, levels, model_features=features)
            assert_frame_equal(rebuilt_matrix, saved_matrix, check_exact=True)
            matrices[family] = {'columns': list(rebuilt_matrix.columns),
                                'dtypes': [str(dtype) for dtype in rebuilt_matrix.dtypes],
                                'exact_match': True}
        report['splits'][split] = {'rows': len(clean), 'roster_rows': len(roster),
                                  'parts': [int(part) for part in parts], 'parity': parity,
                                  'matrices': matrices, 'final_cutoff': state.as_of_part}
    if set(snapshots) != {20243, 20251} or report['delta_check'] is None:
        raise ValueError('Required 20243/20251 snapshots and finalized delta replay missing')
    destination.mkdir(parents=True, exist_ok=False)
    for cutoff, snapshot in snapshots.items():
        path = destination / f'state_as_of_{cutoff}.pkl'
        with path.open('xb') as stream:
            pickle.dump(snapshot, stream)
        report['snapshots'][str(cutoff)] = {'path': str(path.resolve()),
            'as_of_part': snapshot.as_of_part, 'global_sums': snapshot.global_sums,
            'table_rows': {str(level): len(table) for level, table in snapshot.tables.items()},
            'sum_columns': SUM_COLUMNS}
    with (destination / 'compatibility.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
    return report
