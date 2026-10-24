"""Selected models must score the exact same plan contexts without extra inference."""
from copy import deepcopy

import pytest

from tests.test_pilot_20251_engine import bridge
from tests.test_pilot_20251_observed_prediction import predictor


class Experiments:
    def __init__(self):
        self.calls = []

    def inspect(self):
        return {name: {'status': 'READY', 'model_version': 'fixture', 'feature_count': 44 if name == 'B' else 47}
                for name in 'BC'}

    def predict_course_rows(self, frame, name):
        self.calls.append((name, frame.copy()))
        return frame.assign(predicted_mark=70 if name == 'B' else 80,
                            expected_points=3 if name == 'B' else 4, expected_grade='B',
                            fail_probability=.2, course_history_fallback_level=6,
                            course_history_effective_support=0)


@pytest.mark.parametrize('models', [('A',), ('B',), ('C',), ('A','B'), ('A','C'), ('B','C'), ('A','B','C')])
def test_selected_scoring_matches_original_plan_space_and_top_three(bridge, models):
    _, engine, student, *_ = bridge
    engine._experimental = Experiments()
    original = engine.evaluate_student(student, target_credits=6)
    engine._experimental.calls.clear()
    engine._baseline.grade_model.matrices.clear()
    selected = engine.evaluate_student(student, target_credits=6, models=models, measure_stages=True)
    assert set(selected['experiments']) == set(models)
    assert selected['selected_models'] == list(models)
    assert {name for name, _ in engine._experimental.calls} == set(models) & {'B', 'C'}
    assert bool(engine._baseline.grade_model.matrices) == ('A' in models)
    assert selected['search']['plan_set_sha256'] == original['search']['plan_set_sha256']
    assert selected['search']['shared_inputs_sha256'] == original['search']['shared_inputs_sha256']
    for name in models:
        for field in ('course_predictions', 'analytical_plans', 'diagnostic_plans', 'plan_set_sha256', 'shared_inputs_sha256'):
            assert selected['experiments'][name][field] == original['experiments'][name][field]
        assert selected['experiments'][name]['elapsed_seconds'] >= 0
        assert selected['experiments'][name]['latency']['ranking_seconds'] >= 0


def test_bc_selection_does_not_initialize_or_inspect_baseline(bridge, monkeypatch):
    _, engine, student, *_ = bridge
    engine._experimental = Experiments()
    def forbidden():
        raise AssertionError('A is not selected')
    monkeypatch.setattr(engine, 'inspect_assets', forbidden)
    result = engine.evaluate_student(student, target_credits=6, models=['B', 'C'])
    assert all(e['prediction_status'] == 'PREDICTION_AVAILABLE' for e in result['experiments'].values())


@pytest.mark.parametrize('models', [[], ['A','A'], ['X'], 'BC', [True]])
def test_invalid_selection_is_rejected_before_scoring(bridge, models):
    _, engine, student, *_ = bridge
    with pytest.raises(ValueError):
        engine.evaluate_student(student, models=models)
    assert not engine._baseline.grade_model.matrices


def test_actual_plan_selected_models_preserve_context_and_never_run_unselected(predictor, monkeypatch):
    instance, engine, student = predictor
    registrations = [{'course_id':'A', 'course_credits':3}, {'course_id':'B','course_credits':3}]
    expected = deepcopy(instance.predict(student, registrations))
    engine._experimental.seen.clear()
    engine._baseline.grade_model.matrices.clear()
    def forbidden():
        raise AssertionError('No historical A inspection')
    monkeypatch.setattr(engine, 'inspect_assets', forbidden)
    actual = instance.predict(student, registrations, models=['B','C'])
    assert set(actual['experiments']) == {'B','C'}
    assert not engine._baseline.grade_model.matrices
    assert {name for name, _ in engine._experimental.seen} == {'B','C'}
    for name in 'BC':
        assert actual['experiments'][name]['course_predictions'] == expected['experiments'][name]['course_predictions']
        assert actual['experiments'][name]['expected_plan_gpa'] == expected['experiments'][name]['expected_plan_gpa']
    assert instance.last_cache_status == 'FRESH'
    cached = instance.predict(student, registrations, models=['B','C'])
    assert cached == actual
    assert instance.last_cache_status == 'CACHED'


def test_actual_plan_b_only_batch_does_not_precompute_c(predictor):
    instance, engine, student = predictor
    results = instance.predict_many([(student, [{'course_id':'A','course_credits':3}])], models=['B'])
    assert set(results[0]['experiments']) == {'B'}
    assert {name for name, _ in engine._experimental.seen} == {'B'}
    assert not engine._baseline.grade_model.matrices


def test_runner_selection_reuses_engine_enriches_after_scoring_and_saves_compact(tmp_path):
    from tests.test_pilot_20251_app import cohort
    from tools.recommendation_pilot_20251.runner import ComparisonRunner
    cohort(tmp_path)
    calls, engines, enriched = [], [], []
    class Engine:
        def __init__(self, **kwargs):
            engines.append(self)
        def inspect_experiments(self):
            return {name: {**asset, 'features': ['fixture']} for name, asset in Experiments().inspect().items()}
        def inspect_assets(self):
            raise AssertionError('Unselected A must not be inspected by the runner')
        def evaluate_student(self, student, *, models, **kwargs):
            calls.append(tuple(models))
            plans = [{'plan_id': i, 'courses': [{'course_id':str(i),
                      'course_credits': 3, 'fail_probability': .1}]} for i in range(7)]
            return {'sample_id':student['sample_id'], 'status':'PREDICTION_AVAILABLE', 'experiments':{
                name: {'status':'PREDICTION_AVAILABLE','prediction_status':'PREDICTION_AVAILABLE',
                       'plans':[], 'diagnostic_plans':plans,'analytical_plans':plans[:3],
                       'course_predictions':[{'plan_id':i,'course_id':str(i)} for i in range(7)]} for name in models}}
    def enrich(result, student, engine, models):
        assert calls
        enriched.append((student['sample_id'], engine, tuple(models)))
        result['observed_plan'] = {'status':'AVAILABLE','courses':[]}
        return result
    runner = ComparisonRunner(tmp_path, engine_factory=Engine, result_enricher=enrich,
                              reuse_engine=True, max_retained_jobs=1)
    try:
        first = runner.run_sync(['sample-1'], models=['B'])
        second = runner.run_sync(['sample-1'], models=['B'])
        assert first['run_id'] != second['run_id'] and len(engines) == 1
        assert calls == [('B',),('B',)] and len(enriched) == 2
        saved = runner.store.load_compact(first['run_id'])
        assert saved['run_manifest']['selected_models'] == ['B']
        experiment = saved['student_results'][0]['experiments']['B']
        assert len(experiment['diagnostic_plans']) == len(experiment['course_predictions']) == 3
        assert len(runner.store.load(first['run_id'])['student_results'][0]['experiments']['B']['diagnostic_plans']) == 7
        assert (runner.store.root / first['run_id'] / 'presentation_results.json').is_file()
        assert len(runner.jobs) <= 1 and len(runner.futures) <= 1
        assert runner.progress(second['run_id'])['sample_statuses'][0]['sample_id'] == 'sample-1'
    finally:
        runner.executor.shutdown()


def test_runner_persistence_failure_cannot_be_listed_as_success(tmp_path, monkeypatch):
    from tests.test_pilot_20251_app import cohort, SyntheticEngine
    from tools.recommendation_pilot_20251.runner import ComparisonRunner, write_json
    cohort(tmp_path)
    runner = ComparisonRunner(tmp_path, engine_factory=SyntheticEngine)
    def fail_after_manifest(run_id, manifest, *args):
        directory = runner.store.directory(run_id)
        directory.mkdir()
        write_json(directory / 'run_manifest.json', manifest)
        raise OSError('sensitive storage details')
    monkeypatch.setattr(runner.store, 'save', fail_after_manifest)
    try:
        job = runner.run_sync(['sample-1'], models=['B'])
        assert job['status'] == 'failed' and job['error'] == 'OSError'
        assert runner.store.list_runs()[0]['status'] == 'failed'
        assert 'sensitive' not in (runner.store.directory(job['run_id']) / 'run_failure.json').read_text()
    finally:
        runner.executor.shutdown(wait=True)
