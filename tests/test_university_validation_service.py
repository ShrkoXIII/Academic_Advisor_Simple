"""Read-only university facade: exact saved selection, privacy and denominators."""
from copy import deepcopy
import json
import sqlite3

import pytest

from tools.academic_advisor_streamlit.validation_service import ValidationService


AFTER = 'after_backend_fix'
FP = {'student_response': 'a' * 64, 'courses_response': 'b' * 64}


def historical():
    results = []
    for sample, mark, predicted, point, gpa in [('S1', 50, 60, 1., 0.), ('S2', 80, 60, 3., 2.5)]:
        course = {'course_id': '10', 'course_name': 'Course', 'course_credits': 3,
                  'actual_mark': mark, 'actual_points': point, 'result_status': 'AVAILABLE',
                  'course_outcome_status': 'fail' if mark < 60 else 'pass'}
        prediction = {'course_id': '10', 'course_credits': 3, 'predicted_mark': predicted,
                      'expected_points': 2., 'fail_probability': .3}
        experiment = {'status': 'PREDICTION_AVAILABLE', 'analytical_plans': [plan()],
                      'student_id': 'SECRET', 'reason': None}
        results.append({'sample_id': sample, 'part_id': 20251, 'snapshot_id': AFTER,
                        'status': 'NO_MATCHING_PLAN', 'target_credits': 18,
                        'student_summary': {'start_agpa_points': gpa, 'gpa_category': 'low' if gpa < 2 else 'high',
                                            'student_id': 'SECRET', 'degree_id': 'SECRET'},
                        'input_fingerprints': FP, 'observed_plan': {'status': 'AVAILABLE', 'courses': [course]},
                        'observed_plan_prediction': {'experiments': {m: {'status': 'PREDICTION_AVAILABLE',
                            'expected_plan_gpa': 2., 'course_predictions': [prediction]} for m in ('B', 'C')}},
                        'prediction_metrics': {m: {'course_errors': [{'course_id': '10', 'error': predicted - mark,
                            'fail_label': int(mark < 60), 'fail_probability': .3}], 'course_count': 1,
                            'mae': abs(predicted - mark)} for m in ('B', 'C')},
                        'experiments': {m: deepcopy(experiment) for m in ('B', 'C')}})
    return {'snapshot_id': AFTER, 'run_manifest': {'run_id': 'run_saved', 'snapshot_id': AFTER,
        'part_id': 20251, 'selected_models': ['B', 'C'], 'selected_students': ['S1', 'S2'],
        'generation_settings': {'max_plans': 200}, 'student_inputs': {'S1': FP, 'S2': FP},
        'model_versions': {'B': 'vB', 'C': 'vC'}, 'models': {}}, 'student_results': results}


def plan():
    return {'plan_id': 2, 'canonical_id': '10', 'total_credits': 18, 'expected_plan_gpa': 3.,
            'courses': [{'course_id': '10', 'course_name': 'Course', 'course_credits': 18,
                         'predicted_mark': 75, 'student_id': 'SECRET'}]}


def benchmark():
    experiments = []
    for model in ('B', 'C'):
        for strategy in ('FIRST_N', 'DIVERSE_N', 'SMART_SEARCH', 'EXHAUSTIVE'):
            oracle = strategy == 'EXHAUSTIVE'
            experiments.append({'model': model, 'strategy': strategy,
                'scope': 'EXHAUSTIVE' if oracle else 'FULL_SPACE', 'budget': None if oracle else 1000,
                'target_credits': 18, 'status': 'EXHAUSTIVE_COMPLETE' if oracle else 'COMPLETE',
                'evaluated_plans': 3, 'feasible_plan_count': 3, 'top_plans': [plan()],
                'completeness_proof': {'all_feasible_plans_scored': True, 'unique_scored_count': 3,
                    'expected_feasible_count': 3, 'sequential_dfs_ordinals': True,
                    'transactional_checkpoint': True, 'score_chain_sha256': 'c' * 64}})
    return {'run_manifest': {'run_id': 'benchmark_saved', 'snapshot_id': AFTER, 'part_id': 20251,
        'configuration': {'models': ['B', 'C'], 'sample_ids': ['S1'], 'strategies': ['FIRST_N', 'DIVERSE_N', 'SMART_SEARCH'],
                          'budgets': [1000], 'scopes': ['FULL_SPACE', 'EXHAUSTIVE']}},
        'student_results': [{'sample_id': 'S1', 'part_id': 20251, 'input_fingerprints': FP,
            'model_assets': {'B': {'model_version': 'vB'}, 'C': {'model_version': 'vC'}},
            'target_resolution': {'target_credits': 18}, 'fingerprint': 'c' * 64,
            'experiments': experiments}]}


class Pilot:
    def __init__(self): self.saved = historical()
    def cohort(self, **kwargs):
        return [{'sample_id': s, 'part_id': 20251, 'student_id': 'SECRET'} for s in ('S1', 'S2')]
    def list_runs(self):
        return [{'run_id': 'run_saved', 'family': 'comparison', 'snapshot_id': AFTER, 'student_count': 2}]
    def load_run(self, run_id, family='comparison'):
        assert run_id == 'run_saved'
        return deepcopy(self.saved)
    def preview(self, sample_id, snapshot_id=AFTER):
        return {'sample_id': sample_id, 'snapshot_id': snapshot_id, 'student_summary': {'start_agpa_points': 0., 'student_id': 'SECRET'},
                'status': 'READY', 'input_fingerprints': FP, 'credit_target_resolution': {'status': 'RESOLVED',
                    'target_credits': 18, 'maximum_credits': 18, 'raw_rules': {'student_id': 'SECRET'}}}


class Search:
    def __init__(self): self.saved = benchmark()
    def list_runs(self): return [{'run_id': 'benchmark_saved', 'status': 'completed'}]
    def load_run(self, run_id):
        assert run_id == 'benchmark_saved'
        return deepcopy(self.saved)


@pytest.fixture
def service(tmp_path): return ValidationService(tmp_path, pilot=Pilot(), search=Search())


def test_read_only_browsing_whitelists_identities_and_independent_actuals(service):
    view = service.student('S1', snapshot_id=AFTER, historical_ref={'run_id': 'run_saved', 'family': 'comparison'})
    assert view['actual_summary']['models']['B']['predicted_actual_plan_gpa'] == 2
    assert view['actual_summary']['descriptive_gpa'] == 1
    assert view['student_summary']['start_agpa_points'] == 0
    for value in [service.cohort(), service.preview('S1'), service.catalog(), view]:
        assert 'SECRET' not in json.dumps(value)
        assert 'student_id' not in json.dumps(value)


def test_exact_benchmark_selection_and_missing_configuration_does_not_fallback(service):
    selected = service.recommendations('S1', snapshot_id=AFTER, source_ref={'kind': 'benchmark', 'run_id': 'benchmark_saved'})
    assert selected['status'] == 'AVAILABLE'
    assert selected['models']['B']['strategy'] == 'SMART_SEARCH'
    assert len(selected['models']['C']['top_plans']) == 1
    missing = service.recommendations('S1', snapshot_id=AFTER, source_ref={'kind': 'benchmark', 'run_id': 'benchmark_saved'}, budget=200)
    assert missing['status'] == 'UNAVAILABLE'
    assert not missing['models']


def test_historical_legacy_requires_explicit_opt_in_and_keeps_original_target(service):
    ref = {'kind': 'historical', 'run_id': 'run_saved', 'family': 'comparison'}
    assert service.recommendations('S1', snapshot_id=AFTER, source_ref=ref)['status'] == 'UNAVAILABLE'
    old = service.recommendations('S1', snapshot_id=AFTER, source_ref=ref, allow_historical=True, target_credits=16)
    assert old['status'] == 'AVAILABLE_LEGACY'
    assert old['provenance']['recorded_configuration']['strategy'] == 'FIRST_N'
    assert old['provenance']['recorded_configuration']['target_credits'] == 18


@pytest.mark.parametrize('change,expected', [('snapshot','SNAPSHOT_MISMATCH'), ('part','SEMESTER_MISMATCH'),
                                            ('input','INPUT_FINGERPRINT_MISMATCH'), ('target','TARGET_CREDITS_MISMATCH')])
def test_recommendations_reject_incompatible_context(service, change, expected):
    if change == 'snapshot': service.search.saved['run_manifest']['snapshot_id'] = 'before_backend_fix'
    if change == 'part': service.search.saved['student_results'][0]['part_id'] = 20243
    if change == 'input': service.search.saved['student_results'][0]['input_fingerprints'] = {'student_response': 'wrong'}
    kwargs = {'target_credits': 16} if change == 'target' else {}
    result = service.recommendations('S1', snapshot_id=AFTER, source_ref={'kind': 'benchmark', 'run_id': 'benchmark_saved'}, **kwargs)
    assert result['status'] == 'UNAVAILABLE'
    assert result['reason'] == expected


def test_oracle_requires_full_proof_and_same_model_target(service):
    comparison = service.search_comparison('S1', snapshot_id=AFTER, run_id='benchmark_saved')
    assert len(comparison['rows']) == 4
    assert comparison['oracle_status'] == 'EXHAUSTIVE_COMPLETE'
    oracle = service.search.saved['student_results'][0]['experiments'][3]
    oracle['completeness_proof']['all_feasible_plans_scored'] = False
    incomplete = service.search_comparison('S1', snapshot_id=AFTER, run_id='benchmark_saved')
    assert len(incomplete['rows']) == 3
    assert incomplete['oracle_status'] != 'EXHAUSTIVE_COMPLETE'
    assert 'EXHAUSTIVE' not in incomplete['plans_by_strategy']


def test_cohort_filters_before_aggregation_and_valid_pair_denominators(service):
    ref = {'run_id': 'run_saved', 'family': 'comparison'}
    all_rows = service.cohort_evaluation(ref, snapshot_id=AFTER)
    metric = next(r for r in all_rows['metrics'] if r['model'] == 'B' and r['metric'] == 'mae')
    assert metric['value'] == 15
    assert metric['student_count'] == 2 and metric['course_observations'] == 2
    selected = service.cohort_evaluation(ref, snapshot_id=AFTER, starting_category='low')
    metric = next(r for r in selected['metrics'] if r['model'] == 'B' and r['metric'] == 'mae')
    assert metric['value'] == 10
    assert metric['student_count'] == selected['total_students'] == 1
    assert 'SECRET' not in json.dumps(selected)
    empty = service.cohort_evaluation(ref, snapshot_id=AFTER, actual_gpa_range=(3.5,4))
    assert empty['total_students'] == 0
    counts = {'total_students', 'actual_prediction_available', 'recommendation_available', 'BLOCKED', 'NO_MATCHING_PLAN'}
    assert all(r['value'] == 0 if r['metric'] in counts else r['value'] is None for r in empty['metrics'])


def test_cross_source_keeps_observed_forecast_compatibility_separate_from_target(service):
    service.search.saved['student_results'][0]['target_resolution']['target_credits'] = 16
    view = service.source_compatibility('S1', snapshot_id=AFTER,
        historical_ref={'run_id': 'run_saved'}, source_ref={'kind': 'benchmark', 'run_id': 'benchmark_saved'})
    assert view['observed_forecast_compatible'] is True
    assert view['recommendation_target_compatible'] is False
    assert 'TARGET_CREDITS_MISMATCH' in view['issues']
    service.search.saved['student_results'][0]['model_assets']['B']['model_version'] = 'other'
    view = service.source_compatibility('S1', snapshot_id=AFTER,
        historical_ref={'run_id': 'run_saved'}, source_ref={'kind': 'benchmark', 'run_id': 'benchmark_saved'})
    assert view['observed_forecast_compatible'] is False
    assert 'MODEL_FINGERPRINT_MISMATCH:B' in view['issues']


def test_model_hashes_preserved_without_paths_in_provenance(service):
    row = service.search.saved['student_results'][0]
    row['model_assets']['B'].update(artifact_sha256={'model.txt': 'd' * 64}, bundle_path='C:/private/SECRET')
    value = service.recommendations('S1', source_ref={'kind': 'benchmark', 'run_id': 'benchmark_saved'})
    assert value['provenance']['model_assets']['B']['artifact_sha256'] == {'model.txt': 'd' * 64}
    assert value['provenance']['part_id'] == 20251
    assert value['provenance']['target_credits'] == 18
    assert value['provenance']['strategy'] == 'SMART_SEARCH'
    assert 'SECRET' not in json.dumps(value)


def test_oracle_wrong_fingerprint_does_not_reuse_saved_recall(service):
    selected = service.search.saved['student_results'][0]['experiments'][0]
    selected.update(oracle_fingerprint='wrong', top3_recall=1.)
    result = service.search_comparison('S1', run_id='benchmark_saved')
    assert result['rows'][0]['top3_recall'] is None


def test_missing_algorithm_configuration_is_explicit(service):
    experiments = service.search.saved['student_results'][0]['experiments']
    experiments[:] = [e for e in experiments if not (e['strategy'] == 'DIVERSE_N' and e['model'] == 'B')]
    value = service.search_comparison('S1', run_id='benchmark_saved')
    missing = next(r for r in value['rows'] if r['strategy'] == 'DIVERSE_N')
    assert missing['status'] == 'UNAVAILABLE'
    assert missing['reason'] == 'EXACT_SAVED_CONFIGURATION_UNAVAILABLE'
    assert value['plans_by_strategy']['DIVERSE_N'] == []


def test_missing_grade_pairs_and_missing_gpa_are_not_invented_zeros(service):
    row = service.pilot.saved['student_results'][1]
    row['observed_plan']['courses'][0].update(actual_mark=None, actual_points=None, result_status='UNAVAILABLE')
    value = service.cohort_evaluation({'run_id': 'run_saved'})
    mark = next(r for r in value['metrics'] if r['model'] == 'B' and r['metric'] == 'mae')
    gpa = next(r for r in value['metrics'] if r['model'] == 'B' and r['metric'] == 'plan_gpa_mae')
    assert mark['student_count'] == mark['course_observations'] == 1
    assert gpa['student_count'] == 1
    assert value['total_students'] == 2


def test_repeated_scenarios_do_not_duplicate_labels_and_conflicts_are_excluded(service):
    first = service.pilot.saved['student_results'][0]
    first.update(candidate_mode='original', credit_experiment='fixed_18')
    duplicate = deepcopy(first)
    duplicate.update(candidate_mode='actual_augmented')
    service.pilot.saved['student_results'].append(duplicate)
    value = service.cohort_evaluation({'run_id': 'run_saved'})
    metric = next(r for r in value['metrics'] if r['model'] == 'B' and r['metric'] == 'mae')
    assert metric['student_count'] == 2 and metric['course_observations'] == 2
    duplicate['observed_plan_prediction']['experiments']['B']['course_predictions'][0]['predicted_mark'] = 99
    value = service.cohort_evaluation({'run_id': 'run_saved'})
    metric = next(r for r in value['metrics'] if r['model'] == 'B' and r['metric'] == 'mae')
    assert metric['student_count'] == metric['course_observations'] == 1
    assert 'CONFLICTING_SAVED_ACTUAL_FORECAST:S1:B' in value['issues']


def test_oracle_tied_optimal_count_and_ordinal_ranks_are_read_only(service):
    directory = service.root / 'experiments' / AFTER / 'search_benchmark' / 'benchmark_saved'
    sample_dir = directory / 'S1'
    sample_dir.mkdir(parents=True)
    path = sample_dir / 'scores.sqlite'
    connection = sqlite3.connect(path)
    connection.execute('CREATE TABLE scores(job TEXT,ordinal TEXT,canonical TEXT,gpa REAL,failed REAL,risk REAL)')
    connection.executemany('INSERT INTO scores VALUES (?,?,?,?,?,?)',
        [('EXHAUSTIVE/EXHAUSTIVE/None/B', str(i), canonical, 3., 0., .1)
         for i, canonical in enumerate(('best', 'tie', '10'))])
    connection.commit()
    connection.close()
    service.search.saved['storage_path'] = str(directory)
    before = path.read_bytes()
    result = service.search_comparison('S1', run_id='benchmark_saved')
    summary = result['oracle_summary']
    assert summary['tied_optimal_count'] == 3
    assert summary['ordinal_ranks'][0]['oracle_rank'] == 3
    assert path.read_bytes() == before


def test_starting_filter_uses_verified_numeric_snapshot_and_not_cohort_labels(service):
    ref = {'run_id': 'run_saved'}
    service.pilot.saved['student_results'][0]['student_summary']['gpa_category'] = 'high'
    low = service.cohort_evaluation(ref, starting_category='below_2')
    assert {s['sample_id'] for s in low['students']} == {'S1'}
    service.pilot.saved['student_results'][0]['student_summary']['start_agpa_points'] = None
    missing = service.cohort_evaluation(ref, starting_category='unavailable')
    assert {s['sample_id'] for s in missing['students']} == {'S1'}
    assert service.cohort_evaluation(ref, starting_category='at_least_2')['total_students'] == 1


def test_cohort_covers_availability_runtime_candidate_and_similarity_denominators(service):
    first = service.pilot.saved['student_results'][0]
    first['candidate_count'] = 7
    first['experiments']['B']['elapsed_seconds'] = .2
    first['experiments']['B']['status'] = 'BLOCKED'
    report = service.cohort_evaluation({'run_id': 'run_saved'})
    metrics = {r['metric']: r for r in report['metrics'] if r['model'] == 'B'}
    assert metrics['actual_prediction_available']['value'] == 2
    assert metrics['mean_candidate_count']['value'] == 7
    assert metrics['mean_candidate_count']['student_count'] == 1
    assert metrics['mean_runtime_seconds']['value'] == .2
    assert metrics['mean_top3_jaccard']['value'] is None
