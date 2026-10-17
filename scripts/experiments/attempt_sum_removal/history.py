"""Pure reduced history and context adapter. No persistence or production mutation.

Raw update accepts finalized outcome rows at strictly increasing cutoffs. Aggregate
delta uses the original degree/course/faculty/requirement/exact-credit grain and
count, fail_count, retake_count, mark_sum. Finalization is a caller attestation;
university meanings of these fields still require independent verification.
"""
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from src.features.temporal_features import temporal_weight, build_history_keys
from src.recommendation.history_update import _number, _part, _validate_exact_addition
from src.data.cleaning_utils import clean_id
from .contract import HISTORY_COLUMNS, PLAN_COLUMNS, SUM_COLUMNS


def _validate_parts(parts):
    for part in parts:
        _part(part)


def _merge(state, additions, keys):
    for level, key in keys.items():
        grouped = additions.assign(key=key).groupby('key', sort=False)[SUM_COLUMNS].sum()
        table = state.tables[level]
        state.tables[level] = (grouped if table.empty else
            pd.concat([table, grouped]).groupby(level=0, sort=False)[SUM_COLUMNS].sum())
    for column in SUM_COLUMNS:
        state.global_sums[column] += float(additions[column].sum())


@dataclass
class ReducedCourseHistoryState:
    """Official five-level smoothing using only five retained sufficient sums."""
    smoothing_k: float = 20.0
    min_support: float = 20.0
    tables: dict = field(default_factory=lambda: {
        level: pd.DataFrame(columns=SUM_COLUMNS).rename_axis('key')
        for level in range(1, 6)})
    global_sums: dict = field(default_factory=lambda: {name: 0. for name in SUM_COLUMNS})
    as_of_part: int | None = None

    def update(self, outcomes):
        """Add finalized raw outcomes; candidate attempts only identify retakes."""
        if outcomes.empty:
            return
        _validate_parts(outcomes.part_id)
        if self.as_of_part is not None and outcomes.part_id.le(self.as_of_part).any():
            raise ValueError('History updates must follow saved cutoff.')
        weight = temporal_weight(outcomes.part_id).astype('float64')
        mark = pd.to_numeric(outcomes.final_mark, errors='coerce')
        candidate_attempt = pd.to_numeric(outcomes.attempt_number, errors='coerce')
        additions = pd.DataFrame({
            'effective_support': weight, 'raw_count': 1., 'mark_sum': mark * weight,
            'fail_sum': mark.lt(50).astype('float64') * weight,
            'retake_sum': candidate_attempt.gt(1).astype('float64') * weight,
        }, index=outcomes.index)
        _merge(self, additions, build_history_keys(outcomes))
        self.as_of_part = int(outcomes.part_id.max())

    def apply(self, rows):
        """Return six retained outputs, in training order, before target semester."""
        _validate_parts(rows.part_id)
        if self.as_of_part is not None and rows.part_id.le(self.as_of_part).any():
            raise ValueError('History must end before target semester.')
        support_global = float(self.global_sums['effective_support'])
        sum_names = {'course_history_avg_mark': 'mark_sum',
                     'course_history_fail_rate': 'fail_sum',
                     'course_history_retake_rate': 'retake_sum'}
        priors = {name: self.global_sums[raw] / support_global if support_global else np.nan
                  for name, raw in sum_names.items()}
        values = {name: np.full(len(rows), prior, dtype='float64') for name, prior in priors.items()}
        supports = np.full(len(rows), support_global, dtype='float64')
        levels = np.full(len(rows), 6, dtype='int64')
        keys = build_history_keys(rows)
        for level in range(5, 0, -1):
            table = self.tables[level]
            support = keys[level].map(table.effective_support)
            available = support.notna().to_numpy()
            local_support = support.fillna(0).to_numpy(dtype='float64')
            supports[available], levels[available] = local_support[available], level
            for name, raw in sum_names.items():
                local_sum = keys[level].map(table[raw]).fillna(0).to_numpy(dtype='float64')
                smoothed = (local_sum + self.smoothing_k * priors[name]) / (local_support + self.smoothing_k)
                values[name][available] = smoothed[available]
        result = pd.DataFrame(values, index=rows.index)
        result['course_history_effective_support'] = supports
        result['course_history_fallback_level'] = levels
        result['course_history_missing'] = ((levels >= 3) | (supports < self.min_support)).astype('int64')
        return result[HISTORY_COLUMNS]


def build_history_prefix(outcomes, *, target_part, smoothing_k=20., min_support=20.):
    """Build strictly earlier finalized history; target and future rows excluded."""
    target = _part(target_part)
    _validate_parts(outcomes.part_id)
    state = ReducedCourseHistoryState(smoothing_k=smoothing_k, min_support=min_support)
    state.update(outcomes.loc[outcomes.part_id.lt(target)])
    return state


def _validate_state(state):
    if not isinstance(state, ReducedCourseHistoryState) or set(state.global_sums) != set(SUM_COLUMNS):
        raise ValueError('Invalid reduced history contract.')
    if set(state.tables) != set(range(1, 6)) or not np.isfinite([state.smoothing_k, state.min_support]).all() or state.smoothing_k <= 0 or state.min_support < 0:
        raise ValueError('Invalid reduced history configuration.')
    global_values = np.array([state.global_sums[c] for c in SUM_COLUMNS], dtype=float)
    def check(values):
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError('Invalid history sums.')
        support, count, mark, fail, retake = values.T
        if (np.any(support > count + 1e-8) or np.any(count != np.floor(count))
                or np.any(fail > support + 1e-8) or np.any(retake > support + 1e-8)
                or np.any(mark > support * 100 + 1e-8)
                or np.any((support == 0) & (np.sum(values, axis=1) != 0))):
            raise ValueError('Inconsistent history sums.')
    check(global_values.reshape(1, -1))
    if state.as_of_part is not None:
        _part(state.as_of_part)
    elif np.any(global_values):
        raise ValueError('Nonempty history requires cutoff.')
    for table in state.tables.values():
        if list(table.columns) != SUM_COLUMNS or table.index.has_duplicates or table.index.isna().any() or not all(isinstance(k, str) for k in table.index):
            raise ValueError('Invalid reduced table keys/schema.')
        check(table.to_numpy(dtype=float))
        if not np.allclose(table.sum().to_numpy(dtype=float), global_values, rtol=1e-10, atol=1e-7):
            raise ValueError('History totals disagree.')


def apply_delta(state, payload):
    """Return a clone updated by one attested finalized post-2021 semester.

    Reject future academic years (the precise current-semester finalization is
    attested by the caller), duplicate normalized grain, and inexact count sums.
    Exact credit grain is retained until official rounded history-key grouping.
    """
    _validate_state(state)
    if not isinstance(payload, Mapping) or payload.get('finalized') is not True:
        raise ValueError('Delta requires finalized=True.')
    part = _part(payload.get('delta_part'))
    if part < 20221 or part // 10 > datetime.now(timezone.utc).year:
        raise ValueError('Delta must use post-2021 weighting and cannot be future year.')
    if state.as_of_part is not None and part <= state.as_of_part:
        raise ValueError('Delta is out-of-order.')
    records = payload.get('aggregates')
    if not isinstance(records, (list, tuple)):
        raise ValueError('aggregates must be a list of records.')
    id_names = ['degree_id', 'course_id', 'faculty_id', 'plan_requirement_type_id']
    number_names = ['course_credits', 'count', 'fail_count', 'retake_count', 'mark_sum']
    normalized, seen = [], set()
    for record in records:
        if not isinstance(record, Mapping) or not set(id_names + number_names).issubset(record):
            raise ValueError('Missing aggregate fields.')
        if 'part_id' in record and _part(record['part_id']) != part:
            raise ValueError('Aggregate semester mismatch.')
        ids = {}
        for name in id_names:
            value = record[name]
            if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                raise ValueError('Invalid history ID.')
            value = clean_id(pd.Series([value])).iloc[0]
            if pd.isna(value) or '||' in value or value == '__MISSING__':
                raise ValueError('Invalid history ID.')
            ids[name] = str(value)
        numbers = {name: _number(record[name], name, integer=name not in ('course_credits', 'mark_sum'))
                   for name in number_names}
        count, failed, retakes, marks = [numbers[n] for n in ('count', 'fail_count', 'retake_count', 'mark_sum')]
        if (count <= 0 or failed > count or retakes > count or marks > 100 * count
                or marks < 50 * (count - failed)
                or (failed > 0 and marks >= 50 * failed + 100 * (count - failed))
                or numbers['course_credits'] >= 2**63 - 1):
            raise ValueError('Inconsistent finalized aggregate sums.')
        grain = (*ids.values(), numbers['course_credits'])
        if grain in seen:
            raise ValueError('Duplicate normalized aggregate grain.')
        seen.add(grain)
        normalized.append({**ids, **numbers})
    exact_sources = {'effective_support': 'count', 'raw_count': 'count',
                     'fail_sum': 'fail_count', 'retake_sum': 'retake_count'}
    for name, source in exact_sources.items():
        _validate_exact_addition(state.global_sums[name], sum(int(r[source]) for r in normalized), name)
    cloned = deepcopy(state)
    if normalized:
        frame = pd.DataFrame(normalized)
        additions = pd.DataFrame({name: frame[source].map(float) for name, source in
            {**exact_sources, 'mark_sum': 'mark_sum'}.items()})[SUM_COLUMNS]
        keys = build_history_keys(frame)
        # Aggregate exact integer counts before conversion, including key merges.
        for level, key in keys.items():
            for group in key.drop_duplicates():
                positions = np.flatnonzero(key.eq(group).to_numpy())
                for name, source in exact_sources.items():
                    addition = sum(int(normalized[i][source]) for i in positions)
                    previous = state.tables[level].at[group, name] if group in state.tables[level].index else 0.
                    _validate_exact_addition(previous, addition, name)
        _merge(cloned, additions, keys)
    cloned.as_of_part = part
    _validate_state(cloned)
    return cloned


def compute_plan_context(rows, group_columns=None):
    """Calculate only the twelve retained plan/leave-one-out peer outputs."""
    groups = group_columns or ['student_id', 'degree_id', 'part_id']
    groupers = [rows[c] for c in groups]
    def total(series):
        return series.groupby(groupers, sort=False, dropna=False).transform('sum')
    credits = pd.to_numeric(rows.course_credits, errors='coerce').fillna(0.)
    count = rows.groupby(groups, sort=False, dropna=False).course_id.transform('size')
    result = pd.DataFrame(index=rows.index)
    result['plan_course_count'] = count.astype('int64')
    result['plan_total_credits'] = total(credits)
    result['peer_course_count'] = (count - 1).astype('int64')
    result['peer_total_credits'] = result.plan_total_credits - credits
    for label, column in [('fail_rate', 'course_history_fail_rate'), ('avg_mark', 'course_history_avg_mark')]:
        source = pd.to_numeric(rows[column], errors='coerce')
        valid = credits.where(source.notna(), 0.)
        weighted = (source * credits).fillna(0.)
        summed, denominator = total(weighted), total(valid)
        peer_sum, peer_denominator = summed - weighted, denominator - valid
        result[f'plan_credit_weighted_{label}'] = summed.div(denominator.replace(0, np.nan))
        result[f'peer_credit_weighted_{label}'] = peer_sum.div(peer_denominator.replace(0, np.nan))
        if label == 'fail_rate':
            result['plan_difficulty_credit_load'] = summed.where(denominator.gt(0))
            result['peer_difficulty_credit_load'] = peer_sum.where(peer_denominator.gt(0))
    fail = pd.to_numeric(rows.course_history_fail_rate, errors='coerce')
    maximum = fail.groupby(groupers, sort=False, dropna=False).transform('max')
    at_max = fail.eq(maximum) & fail.notna()
    max_count = total(at_max.astype('int64'))
    second = fail.where(fail.lt(maximum)).groupby(groupers, sort=False, dropna=False).transform('max')
    result['peer_max_fail_rate'] = maximum.mask(at_max & max_count.eq(1), second)
    result.loc[result.peer_course_count.eq(0), 'peer_max_fail_rate'] = np.nan
    result['peer_difficulty_missing'] = result.peer_credit_weighted_fail_rate.isna().astype('int64')
    return result[PLAN_COLUMNS]
