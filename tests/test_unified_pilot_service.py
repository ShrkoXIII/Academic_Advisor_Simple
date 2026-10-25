"""Offline service/presentation contracts, using saved synthetic results only."""
from copy import deepcopy

import pytest


def saved_result():
    from tests.test_pilot_20251_actual_metrics import result
    row = result()
    row['candidate_count'] = 4
    row['observed_plan']['graded_course_count'] = 2
    row['observed_plan']['courses'][0]['actual_points'] = 3
    row['observed_plan']['courses'][1]['actual_points'] = 1
    for forecast in row['observed_plan_prediction']['experiments'].values():
        forecast['expected_plan_gpa'] = 2.5
    row['experiments']['B']['analytical_plans'][0]['courses'][0].update(
        predicted_mark=80, expected_points=3.5, fail_probability=.05)
    return {'run_manifest': {'snapshot_id': 'after_backend_fix', 'selected_models': ['B']},
            'student_results': [row]}


def test_presentation_preserves_ranking_and_separates_alternative_from_actual_context():
    from tools.academic_advisor_streamlit.pilot_service import PilotService
    saved = saved_result()
    original = deepcopy(saved)
    view = PilotService().presentation(saved, 's')
    assert list(view['plans_by_model']) == ['B']
    assert [p['plan_id'] for p in view['plans_by_model']['B']] == [0, 1]
    assert view['plans_by_model']['B'][0]['rank'] == 1
    assert view['plans_by_model']['B'][0]['course_rows'][0]['actual_mark'] == 54
    assert view['plans_by_model']['B'][0]['course_rows'][1]['actual_mark'] is None
    assert view['actual_course_rows'][0]['B_predicted_mark'] == 60
    assert view['plans_by_model']['B'][0]['course_rows'][0]['predicted_mark'] == 80
    assert view['actual_summary']['descriptive_gpa'] == 2
    assert view['actual_summary']['official_gpa'] is None
    assert view['summary_rows'][0]['predicted_actual_plan_gpa'] == 2.5
    assert view['summary_rows'][0]['actual_plan_gpa_error'] == .5
    assert saved == original


def test_partial_outcomes_do_not_become_complete_gpa_or_fabricated_zero():
    from tools.academic_advisor_streamlit.pilot_service import PilotService
    saved = saved_result()
    row = saved['student_results'][0]
    row['observed_plan']['courses'][1].update(actual_points=None, actual_mark=None, result_status='NO_FINAL_RESULT')
    row['observed_plan']['status'] = 'PARTIAL'
    row['observed_plan']['graded_course_count'] = 1
    view = PilotService().presentation(saved, 's')
    assert view['actual_summary']['descriptive_gpa'] is None
    assert view['actual_summary']['partial_graded_gpa'] == 3
    assert view['actual_summary']['descriptive_gpa_reason']
    assert view['summary_rows'][0]['actual_plan_gpa_error'] is None


def test_legacy_browsing_never_loads_engine_observations_or_scores(tmp_path):
    from tools.academic_advisor_streamlit.pilot_service import PilotService
    from tools.recommendation_pilot_20251.runner import RunStore
    root = tmp_path / 'pilot'
    store = RunStore(root / 'experiments/before_backend_fix/comparison')
    store.save('run_old', {'selected_models': ['C']}, [{'sample_id': 's', 'experiments': {'C': {'status': 'BLOCKED'}}}], {})
    prior = (store.root / 'run_old/student_results.json').read_bytes()
    def forbidden(*args, **kwargs):
        raise AssertionError('Read must not construct scoring dependencies')
    service = PilotService(root, engine_factory=forbidden, predictor_factory=forbidden)
    saved = service.load_run('run_old')
    view = service.presentation(saved, 's')
    assert saved['snapshot_id'] == 'before_backend_fix'
    assert view['summary_rows'][0]['top1_actual_overlap'] is None
    assert view['actual_summary']['descriptive_gpa'] is None
    assert service.list_runs()[0]['family'] == 'comparison'
    assert (store.root / 'run_old/student_results.json').read_bytes() == prior


def test_before_start_is_read_only_and_after_preflight_identifies_affected_sample(tmp_path):
    from tools.academic_advisor_streamlit.pilot_service import PilotService, PilotPreflightError
    from tests.test_pilot_20251_app import cohort
    cohort(tmp_path)
    service = PilotService(tmp_path)
    with pytest.raises(ValueError, match='read.only'):
        service.start(['sample-1'], snapshot_id='before_backend_fix')
    summary = service.completeness()
    assert summary['ready_sample_ids'] == []
    assert 'sample-1' in {row['sample_id'] for row in summary['blocked']}
    with pytest.raises(PilotPreflightError) as error:
        service.start(['sample-1'])
    assert error.value.blocked[0]['sample_id'] == 'sample-1'


def test_post_score_enrichment_uses_only_registration_identity_for_predictor():
    from tools.academic_advisor_streamlit.pilot_service import PilotService
    from tests.test_pilot_20251_actual_metrics import observed
    calls = []
    class Store:
        def get(self, student):
            calls.append('labels')
            return observed()
    class Predictor:
        def __init__(self, **kwargs):
            self.engine = kwargs['engine']
        def predict(self, student, registrations, *, models):
            calls.append((registrations, models))
            assert all(set(course) == {'course_id', 'course_credits'} for course in registrations)
            return {'experiments': {name: {} for name in models}}
    service = PilotService(observed_store=Store(), predictor_factory=Predictor)
    row = {'sample_id': 's', 'experiments': {'B': {}, 'C': {}}}
    enriched = service._enrich(row, {'sample_id': 's'}, object(), ('B', 'C'))
    assert set(enriched['experiments']) == {'B', 'C'}
    assert calls[1][1] == ('B', 'C')


def test_metrics_selection_does_not_invent_unselected_experiments():
    from tools.recommendation_pilot_20251.actual_metrics import attach_prediction_metrics, attach_recommendation_metrics
    row = saved_result()['student_results'][0]
    row['experiments'] = {'B': row['experiments']['B']}
    attach_recommendation_metrics(row, models=('B',))
    attach_prediction_metrics(row, models=('B',))
    assert set(row['experiments']) == {'B'}
    assert set(row['prediction_metrics']) == {'B'}


def test_missing_timing_is_na_and_existing_timers_are_not_summed():
    from tools.academic_advisor_streamlit.pilot_service import PilotService
    saved = saved_result()
    saved['student_results'][0]['experiments']['B']['latency'].pop('feature_extraction_seconds')
    view = PilotService().presentation(saved, 's')
    stage = next(row for row in view['timing_rows'] if row['model'] == 'B' and row['stage'] == 'feature_extraction_seconds')
    assert stage['seconds'] is None and stage['reason']
    assert view['summary_rows'][0]['elapsed_seconds'] is None


def test_valid_subset_uses_one_reused_direct_runner_and_explicit_models(tmp_path):
    import csv
    import json
    from tests.test_pilot_20251_engine import payloads
    from tests.test_pilot_20251_history import PARTS, write_source, row
    from tools.academic_advisor_streamlit.pilot_collection_store import PilotCollectionStore
    from tools.academic_advisor_streamlit.pilot_service import PilotService, PilotPreflightError
    store = PilotCollectionStore(tmp_path)
    store.pilot.mkdir(parents=True)
    with (store.pilot / 'students.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['sample_id', 'role', 'student_id', 'degree_id', 'part_id', 'previous_gpa'])
        writer.writeheader()
        for sample in ('valid', 'missing'):
            writer.writerow(dict(sample_id=sample, role='primary', student_id='S', degree_id='D', part_id=20251, previous_gpa=2))
    for kind, payload in zip(('student', 'courses'), payloads()):
        store.save(store.student_file('valid', kind), json.dumps(payload).encode(), kind=kind,
                   identity={'student_id': 'S', 'degree_id': 'D', 'part_id': 20251}, source='fixture')
    for part in PARTS:
        write_source(store.pilot, part, [row(part)])
    runners, calls = [], []
    class Runner:
        def __init__(self, root, **kwargs):
            runners.append(self)
            self.kwargs = kwargs
        def start(self, sample_ids, **kwargs):
            calls.append((sample_ids, kwargs))
            return 'run_fixture'
    service = PilotService(store.pilot, runner_factory=Runner)
    complete = service.completeness()
    assert complete['ready_sample_ids'] == ['valid']
    assert service.preview('valid')['student_summary']['start_agpa_points'] == 2.5
    assert service.preview('valid')['credit_target_resolution']['target_credits'] == 18
    with pytest.raises(PilotPreflightError):
        service.start(['valid', 'missing'])
    assert runners == []
    assert service.start(['valid'], models=('C',)) == 'run_fixture'
    service.start(['valid'], models=('B', 'C'))
    assert len(runners) == 1
    assert runners[0].kwargs['reuse_engine'] is True
    assert calls[0][1]['models'] == ('C',)
    assert calls[0][1]['target_credits'] is None  # runner resolves separately per student
    # Existing experimental policy quarantines invalid rows rather than
    # incorrectly rejecting intact files with a retained valid population.
    write_source(store.pilot, PARTS[0], [row(PARTS[0]), row(PARTS[0], COURSE_ID='bad', SUM_MARKS=None)])
    assert service.completeness()['ready_sample_ids'] == ['valid']


def test_actual_matching_rejects_ambiguous_ids_and_mismatched_credits():
    from tools.academic_advisor_streamlit.pilot_service import PilotService
    saved = saved_result()
    row = saved['student_results'][0]
    row['experiments']['B']['analytical_plans'][0]['courses'][0]['course_credits'] = 4
    view = PilotService().presentation(saved, 's')
    course = view['plans_by_model']['B'][0]['course_rows'][0]
    assert course['actual_mark'] is None
    assert course['actual_mark_reason'] == 'ACTUAL_COURSE_CREDIT_MISMATCH'
    row['observed_plan']['courses'].append(deepcopy(row['observed_plan']['courses'][0]))
    view = PilotService().presentation(saved, 's')
    assert view['actual_summary']['descriptive_gpa'] is None
    assert view['plans_by_model']['B'][0]['overlap_count'] is None


def test_saved_scenarios_require_explicit_selection_and_remain_labelled():
    from tools.academic_advisor_streamlit.pilot_service import PilotService
    saved = saved_result()
    other = deepcopy(saved['student_results'][0])
    other.update(candidate_mode='augmented', credit_experiment='actual_load')
    other['experiments']['B']['analytical_plans'][0]['expected_plan_gpa'] = 3.9
    saved['student_results'].append(other)
    service = PilotService()
    with pytest.raises(ValueError, match='scenario'):
        service.presentation(saved, 's')
    view = service.presentation(saved, 's', scenario=('augmented', 'actual_load'))
    assert view['candidate_mode'] == 'augmented' and view['credit_experiment'] == 'actual_load'
    assert view['summary_rows'][0]['best_predicted_plan_gpa'] == 3.9


def test_blocked_forecasts_do_not_display_saved_error_derivatives():
    from tools.academic_advisor_streamlit.pilot_service import PilotService
    from tools.recommendation_pilot_20251.actual_metrics import attach_prediction_metrics
    saved = saved_result()
    row = saved['student_results'][0]
    attach_prediction_metrics(row, models=('B',))
    forecast = row['observed_plan_prediction']['experiments']['B']
    forecast.update(prediction_status='BLOCKED', reason='RETIRED_EXPERIMENTAL_MODEL', course_predictions=[])
    view = PilotService().presentation(saved, 's')
    assert view['actual_summary']['models']['B']['mae'] is None
    assert view['actual_course_rows'][0]['B_error'] is None


def test_measured_run_and_student_totals_have_separate_scope_and_cache_labels():
    from tools.academic_advisor_streamlit.pilot_service import PilotService
    saved = saved_result()
    saved['completion'] = dict(total_wall_seconds=9, persistence_seconds=1, provenance='measured test run')
    saved['student_results'][0]['latency']['comparison_wall_seconds'] = 7
    saved['student_results'][0]['observed_prediction_cache_status'] = 'CACHED'
    view = PilotService().presentation(saved, 's')
    assert view['execution']['total_wall_seconds'] == 9
    assert view['execution']['observed_prediction_cache_status'] == 'CACHED'
    assert view['summary_rows'][0]['total_elapsed_seconds'] == 7
    assert view['search']['visited_search_states'] == 7


def test_summary_uses_model_scored_count_and_marks_unavailable_fields():
    from tools.academic_advisor_streamlit.pilot_service import PilotService
    saved = saved_result()
    row = saved['student_results'][0]
    row['experiments']['B'].update(prediction_status='BLOCKED', reason='MODEL_UNAVAILABLE', analytical_plans=[], diagnostic_plans=[])
    view = PilotService().presentation(saved, 's')
    summary = view['summary_rows'][0]
    assert summary['evaluated_plans'] is None and summary['evaluated_plans_reason']
    assert summary['actual_plan_gpa_absolute_error'] == .5
