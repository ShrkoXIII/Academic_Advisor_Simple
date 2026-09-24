"""Collect real recommendation outputs for a production-code explanation of two terms.

No source/model mutation. Run from the project root with its .venv Python.
"""
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import paths
from src.data.clean_student_status import clean_student_status
from src.recommendation import AcademicPlanRecommender, build_plan_rows, rank_plans
from src.recommendation.inputs import load_local_inputs, normalize_candidates
from src.features.temporal_features import COURSE_HISTORY_COLUMNS, PLAN_CONTEXT_COLUMNS, build_history_keys, temporal_weight
from src.experiments.specialty_history import SPECIALTY_HISTORY_FEATURES
from src.experiments.modeling import prepare_matrix
from src.features.feature_contract import prepare_model_matrix

SID, DID = '29485.111', '42.111'
OUT = ROOT / 'data/evaluation/recommendation_trace_pilot' / (
    'explained_29485_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
CHECKS = []


def check(name, condition):
    CHECKS.append({'check': name, 'passed': bool(condition)})
    assert condition, name


def records(frame):
    return json.loads(frame.to_json(orient='records', force_ascii=False, double_precision=15))


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def read_export(path):
    text = path.read_text(encoding='utf-8-sig')
    text, escaped = re.subn(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', text)
    ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
    attr = '{urn:schemas-microsoft-com:office:spreadsheet}'
    rows = []
    for row in ET.fromstring(text).findall('.//ss:Table/ss:Row', ns):
        values = []
        for cell in row.findall('ss:Cell', ns):
            values.extend([None] * (int(cell.get(attr + 'Index', len(values) + 1)) - 1 - len(values)))
            data = cell.find('ss:Data', ns)
            values.append(None if data is None else data.text)
        rows.append(values)
    return pd.DataFrame(rows[1:], columns=rows[0]).drop(columns=[None, ''], errors='ignore'), escaped


def summarize_all(scored):
    frame = scored.assign(quality=scored.course_credits * scored.expected_points,
                          failed=scored.course_credits * scored.fail_probability)
    sums = frame.groupby('plan_id', sort=False).agg(course_count=('course_id', 'size'),
        total_credits=('course_credits', 'sum'), expected_quality_points=('quality', 'sum'),
        expected_failed_credits=('failed', 'sum'), membership_mask=('membership_bit', 'sum')).reset_index()
    sums['expected_plan_gpa'] = sums.expected_quality_points / sums.total_credits
    return sums


def course_math(prepared, engine, train, train_keys):
    rows = []
    keys = build_history_keys(prepared)
    for i, course in prepared.iterrows():
        level = int(course.course_history_fallback_level)
        key = 'global' if level == 6 else keys[level].iloc[i]
        raw = train if level == 6 else train.loc[train_keys[level].eq(key)]
        weight = temporal_weight(raw.part_id).astype(float)
        aggregates = {
            'effective_support': float(weight.sum()), 'raw_count': float(len(raw)),
            'mark_sum': float((raw.final_mark * weight).sum()),
            'fail_sum': float((raw.final_mark.lt(50) * weight).sum()),
            'attempt_sum': float((raw.attempt_number * weight).sum()),
            'retake_sum': float((raw.attempt_number.gt(1) * weight).sum())}
        saved = engine.course_history.global_sums if level == 6 else engine.course_history.tables[level].loc[key].to_dict()
        for column, value in aggregates.items():
            np.testing.assert_allclose(value, saved[column], rtol=0, atol=1e-8)
        details = []
        for feature, field in [('course_history_avg_mark', 'mark_sum'), ('course_history_fail_rate', 'fail_sum'),
                               ('course_history_avg_attempt', 'attempt_sum'), ('course_history_retake_rate', 'retake_sum')]:
            global_mean = engine.course_history.global_sums[field] / engine.course_history.global_sums['effective_support']
            value = global_mean if level == 6 else (saved[field] + engine.course_history.smoothing_k * global_mean) / (saved['effective_support'] + engine.course_history.smoothing_k)
            np.testing.assert_allclose(value, course[feature], rtol=0, atol=1e-12)
            details.append({'feature': feature, 'sum_field': field, 'weighted_sum': saved[field],
                            'global_mean': global_mean, 'value': value})
        periods = raw.assign(weight=weight, weighted_mark=raw.final_mark * weight,
                             weighted_fail=raw.final_mark.lt(50) * weight).groupby('part_id').agg(
            raw_count=('part_id', 'size'), weight_per_row=('weight', 'first'),
            effective_support=('weight', 'sum'), mark_sum=('weighted_mark', 'sum'), fail_sum=('weighted_fail', 'sum')).reset_index()
        rows.append({'course_id': course.course_id, 'level': level, 'key': key,
                     'sums': aggregates, 'smoothing_k': engine.course_history.smoothing_k,
                     'features': details, 'semester_contributions': records(periods)})
    check(f'{int(prepared.part_id.iloc[0])}: raw training sums reconstruct frozen course features', True)
    return rows


def collect_term(part, export_number, engine, history, status, train, train_keys):
    folder = OUT / str(part)
    folder.mkdir()
    source = Path.home() / 'Downloads' / f'exportdata ({export_number}).xml'
    raw, escaped = read_export(source)
    check(f'{part}: one student, unique Y courses', set(raw.STUDENT_ID) == {SID}
          and raw.IS_REQUESTABLE.eq('Y').all() and raw.COURSE_ID.nunique() == len(raw))
    (folder / 'original.xml').write_bytes(source.read_bytes())
    candidate_path = folder / 'candidates.json'
    save(candidate_path, records(raw))
    candidates, snapshot, import_report = load_local_inputs(candidate_path, SID, DID, part)
    prepared = engine.prepare_candidates(snapshot, candidates, part)
    prepared.to_parquet(folder / 'prepared_candidates.parquet', index=False)
    save(folder / 'snapshot.json', json.loads(pd.Series(snapshot).to_json(double_precision=15)))
    save(folder / 'import_report.json', import_report)
    check(f'{part}: complete supplied list retained', len(candidates) == len(raw))
    # DP is independent of the production subset enumerator, and handles Decimal credits.
    counts = Counter({Decimal(0): 1})
    for credit in candidates.course_credits:
        old = counts.copy()
        for total, count in old.items():
            counts[total + Decimal(str(credit))] += count
    expected_count = sum(count for total, count in counts.items() if 12 <= total <= 18)
    original_score = engine.score_rows
    all_summaries, top_summaries, top_rows = [], pd.DataFrame(), pd.DataFrame()
    bits = {course: 1 << i for i, course in enumerate(prepared.course_id)}

    def capture(rows):
        nonlocal top_summaries, top_rows
        scored = original_score(rows)
        scored['membership_bit'] = scored.course_id.map(bits)
        summary = summarize_all(scored)
        all_summaries.append(summary)
        top_summaries = rank_plans(pd.concat([top_summaries, summary], ignore_index=True)).head(5)
        selected = scored.loc[scored.plan_id.isin(top_summaries.plan_id)]
        top_rows = selected.copy() if top_rows.empty else pd.concat([top_rows, selected], ignore_index=True)
        top_rows = top_rows.loc[top_rows.plan_id.isin(top_summaries.plan_id)]
        return scored

    engine.score_rows = capture
    try:
        accepted, result = engine.recommend(snapshot, candidates, part, snapshot['start_agpa_points'],
            min_credits=12, max_credits=18, batch_size=2000,
            progress=lambda n: print(f'{part}: scored {n:,}/{expected_count:,} plans', flush=True) if n % 20000 == 0 else None)
    finally:
        engine.score_rows = original_score
    summaries = pd.concat(all_summaries, ignore_index=True)
    check(f'{part}: enumeration agrees with DP and has no duplicate subsets',
          result['matching_plan_count'] == expected_count == len(summaries)
          and not summaries.membership_mask.duplicated().any())
    check(f'{part}: acceptance uses original GPA threshold exactly',
          set(accepted.plan_id) == set(summaries.loc[summaries.expected_plan_gpa.gt(snapshot['start_agpa_points']), 'plan_id']))
    summaries.to_parquet(folder / 'all_plan_scores.parquet', index=False)
    accepted.to_parquet(folder / 'accepted_plan_scores.parquet', index=False)
    top_rows.to_parquet(folder / 'top_five_full_features.parquet', index=False)
    save(folder / 'result_before_evaluation.json', result)
    sealed = sha256((folder / 'result_before_evaluation.json').read_bytes()).hexdigest()
    best_id = int(top_summaries.iloc[0].plan_id)
    best = top_rows.loc[top_rows.plan_id.eq(best_id)].sort_values('course_id').reset_index(drop=True)
    check(f'{part}: selected plan rescoring agrees independently of batch',
          np.allclose(original_score(best).expected_points, best.expected_points, rtol=0, atol=1e-12))
    math = course_math(prepared, engine, train, train_keys)

    # Reveal observed outcomes only after the recommendations have been saved.
    actual = history.loc[history.student_id.eq(SID) & history.degree_id.eq(DID) & history.part_id.eq(part)].copy()
    roster = pd.read_parquet(paths.TEMPORAL_TEST_ROSTER_PATH)
    roster = roster.loc[roster.student_id.eq(SID) & roster.degree_id.eq(DID) & roster.part_id.eq(part)]
    check(f'{part}: observed outcomes cover full registration roster', set(actual.student_course_id) == set(roster.student_course_id))
    observed_candidates, _ = normalize_candidates(actual[['course_id', 'course_credits']],
        pd.read_parquet(paths.CLEAN_DEGREE_COURSE_PATH), history, SID, DID, part)
    observed_prepared = engine.prepare_candidates(snapshot, observed_candidates, part)
    observed_scored = engine.score_rows(build_plan_rows(observed_prepared, [tuple(range(len(observed_prepared)))], -1))
    actual_scored = actual.merge(observed_scored[['course_id', 'expected_points', 'fail_probability']], on='course_id', validate='one_to_one')
    contract = engine.metadata['feature_contract']
    reference = pd.read_parquet(paths.TEMPORAL_TEST_FEATURES_PATH)
    reference = reference.loc[reference.student_id.eq(SID) & reference.degree_id.eq(DID) & reference.part_id.eq(part)]
    reference = engine.specialty_history.apply(reference).sort_values('course_id').reset_index(drop=True)
    matrix = prepare_matrix(observed_scored, contract['numeric_features'], contract['categorical_features'], engine.points_levels)
    reference_matrix = prepare_matrix(reference, contract['numeric_features'], contract['categorical_features'], engine.points_levels)
    pd.testing.assert_frame_equal(matrix, reference_matrix, check_exact=False, rtol=1e-6, atol=1e-6)
    pd.testing.assert_frame_equal(prepare_model_matrix(observed_scored, engine.fail_levels),
                                prepare_model_matrix(reference, engine.fail_levels), check_exact=False, rtol=1e-6, atol=1e-6)
    check(f'{part}: observed plan 57/47 model inputs match saved features', True)
    saved_predictions = pd.read_parquet(paths.DEGREE_POINTS_HOLDOUT_COURSES_PATH)
    comparison = actual_scored.merge(saved_predictions[['student_course_id', 'predicted_points']], on='student_course_id', validate='one_to_one')
    check(f'{part}: observed plan predictions match saved holdout', len(comparison) == len(actual)
          and np.allclose(comparison.expected_points, comparison.predicted_points, rtol=0, atol=1e-10))
    check(f'{part}: no outcome feedback into saved recommendations', sealed == sha256((folder / 'result_before_evaluation.json').read_bytes()).hexdigest())
    common = sorted(set(actual.course_id) & set(best.course_id))
    model_only = sorted(set(best.course_id) - set(actual.course_id))
    actual_only = sorted(set(actual.course_id) - set(best.course_id))
    comparison = best[['course_id', 'course_name', 'course_credits', 'expected_points', 'fail_probability']].rename(
        columns={'expected_points': 'plan_expected_points', 'fail_probability': 'plan_fail_probability'})
    comparison = comparison.merge(actual_scored[['course_id', 'course_name_sl', 'course_credits', 'final_mark', 'points', 'expected_points']],
        on='course_id', how='outer', suffixes=('', '_actual'), validate='one_to_one')
    comparison['course_name'] = comparison.course_name.combine_first(comparison.course_name_sl)
    comparison['course_credits'] = comparison.course_credits.combine_first(comparison.course_credits_actual)
    comparison['membership'] = comparison.course_id.map(lambda cid: 'مشتركة' if cid in common else ('في الخطة المعروضة فقط' if cid in model_only else 'سجّلها الطالب فقط'))
    comparison = comparison.drop(columns=['course_name_sl', 'course_credits_actual']).sort_values(['membership', 'course_id'])
    best_matrix = prepare_matrix(best, contract['numeric_features'], contract['categorical_features'], engine.points_levels)
    check(f'{part}: real points feature order and bounded outputs', list(best_matrix) == engine.points_model.feature_name()
          and best.expected_points.between(0, 4).all() and best.fail_probability.between(0, 1).all())
    best_matrix.to_parquet(folder / 'best_plan_points_matrix.parquet', index=False)
    comparison.to_parquet(folder / 'comparison.parquet', index=False)
    actual_scored.to_parquet(folder / 'actual_registration_predictions.parquet', index=False)
    metrics = {'actual_gpa': float(np.average(actual.points, weights=actual.course_credits)),
               'predicted_gpa_for_actual_plan': float(np.average(actual_scored.expected_points, weights=actual_scored.course_credits)),
               'course_points_mae': float((actual_scored.expected_points - actual_scored.points).abs().mean()),
               'actual_credits': float(actual.course_credits.sum()), 'actual_count': len(actual)}
    term_status = status.loc[status.student_id.eq(SID) & status.degree_id.eq(DID) & status.part_id.le(part)].copy()
    term_status.loc[term_status.part_id.eq(part), ['gpa_points', 'end_agpa_points']] = np.nan
    payload = {'part_id': part, 'xml_name': source.name, 'xml_sha256': sha256(source.read_bytes()).hexdigest(),
        'xml_escaped_ampersands': escaped, 'xml_outcome_fields_excluded': records(raw[['GPA_POINTS', 'END_AGPA_POINTS']].drop_duplicates()),
        'snapshot': json.loads(pd.Series(snapshot).to_json(double_precision=15)), 'result': result,
        'best_is_recommendation': bool(result['recommendations']), 'best_summary': records(top_summaries.head(1))[0],
        'best_courses': records(best), 'candidates': records(prepared), 'course_math': math,
        'comparison': records(comparison), 'common': common, 'model_only': model_only, 'actual_only': actual_only,
        'actual_missing_from_candidates': sorted(set(actual.course_id) - set(candidates.course_id)),
        'actual': records(actual_scored), 'metrics': metrics,
        'status_history': records(term_status[['part_id', 'gpa_points', 'start_agpa_points', 'end_agpa_points', 'reg_total_semesters']]),
        'best_matrix': records(best_matrix), 'model_features': list(best_matrix),
        'top_five': records(top_summaries), 'credit_distribution': {str(t): c for t, c in sorted(counts.items()) if 12 <= t <= 18}}
    save(folder / 'explanation_data.json', payload)
    print(json.dumps({'part': part, 'candidates': len(candidates), 'plans': expected_count,
          'accepted': result['accepted_plan_count'], 'best_gpa': payload['best_summary']['expected_plan_gpa'],
          'actual_overlap': len(common)}, ensure_ascii=False), flush=True)
    return payload


def main():
    OUT.mkdir(parents=True)
    protected = [*ROOT.joinpath('src').rglob('*.py'), *ROOT.joinpath('models').rglob('*.txt'),
                 *ROOT.joinpath('models').rglob('*.json'), *ROOT.joinpath('data/artifacts').glob('*')]
    hashes = {str(p): sha256(p.read_bytes()).hexdigest() for p in protected if p.is_file()}
    engine = AcademicPlanRecommender.load(num_threads=4)
    history = pd.read_parquet(paths.CLEAN_STUDENT_COURSE_PATH)
    status = clean_student_status(pd.read_parquet(paths.STUDENT_STATUS_PATH))
    train = pd.read_parquet(paths.TEMPORAL_TRAIN_FEATURES_PATH)
    train_keys = build_history_keys(train)
    check('Frozen course and specialty histories match training cutoff 20243',
          int(train.part_id.max()) == engine.course_history.as_of_part == engine.specialty_history.as_of_part == 20243)
    cases = [collect_term(20251, 7, engine, history, status, train, train_keys),
             collect_term(20252, 12, engine, history, status, train, train_keys)]
    check('20252 previous semester GPA equals observed 20251 GPA',
          cases[1]['snapshot']['gpa_prev_1'] == float(status.loc[status.student_id.eq(SID) & status.part_id.eq(20251), 'gpa_points'].iloc[0]))
    check('Production sources, artifacts and models unchanged', all(sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()))
    save(OUT / 'checks.json', CHECKS)
    save(OUT / 'provenance.json', {'protected_sha256': hashes, 'training_sha256': sha256(paths.TEMPORAL_TRAIN_FEATURES_PATH.read_bytes()).hexdigest(),
        'created_at_utc': datetime.now(timezone.utc).isoformat(), 'model': engine.provenance})
    print('EXPLANATION_OUTPUT=' + str(OUT), flush=True)
    return OUT


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()
