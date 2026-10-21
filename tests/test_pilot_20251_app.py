import csv
import json

from fastapi.testclient import TestClient
import pytest

from tools.recommendation_pilot_20251.app import create_app
from tools.recommendation_pilot_20251.runner import RunStore, ComparisonRunner


def cohort(root):
    with (root / 'students.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_id','role','student_id','degree_id','part_id','previous_gpa','gpa_category'])
        writer.writeheader()
        for i in range(2):
            writer.writerow(dict(sample_id=f'sample-{i}',role='primary',student_id=f's-{i}',degree_id='d',part_id=20251,previous_gpa=2,gpa_category='mid'))


class SyntheticEngine:
    def __init__(self, **kwargs):
        pass

    def inspect_assets(self):
        return {'status': 'PASS', 'test_fixture': True}

    def evaluate_student(self, student, **kwargs):
        if student['sample_id'] == 'sample-0':
            raise ValueError('sensitive record must not escape')
        return {'sample_id': student['sample_id'], 'student_id': student['student_id'], 'status': 'BLOCKED',
                'experiments': {name: {'status': 'BLOCKED', 'reason': 'synthetic policy gate', 'plans': [],
                                       'diagnostic_plans': [], 'course_predictions': []} for name in 'ABC'}}


def test_batch_continues_and_saved_result_is_immutable(tmp_path):
    cohort(tmp_path)
    runner = ComparisonRunner(tmp_path, engine_factory=SyntheticEngine)
    job = runner.run_sync(['sample-0', 'sample-1'], target_credits=18)
    assert job['status'] == 'completed'
    run = runner.store.load(job['run_id'])
    assert len(run['student_results']) == 2
    assert run['student_results'][0]['status'] == 'BLOCKED'
    assert run['student_results'][1]['sample_id'] == 'sample-1'
    assert 'sensitive record' not in json.dumps(run)
    for name in ['run_manifest.json','student_results.json','plan_comparison.csv','course_predictions.csv','diagnostics.json']:
        assert (runner.store.root / job['run_id'] / name).exists()
    before = (runner.store.root / job['run_id'] / 'run_manifest.json').read_bytes()
    other = runner.run_sync(['sample-1'], target_credits=18)
    assert other['run_id'] != job['run_id']
    assert (runner.store.root / job['run_id'] / 'run_manifest.json').read_bytes() == before


def test_store_rejects_path_traversal(tmp_path):
    store = RunStore(tmp_path)
    with pytest.raises(ValueError):
        store.load('../outside')


def test_retired_experimental_model_cannot_reappear_as_available_saved_predictions(tmp_path):
    store = RunStore(tmp_path)
    result = {'sample_id': 'sample', 'experiments': {
        name: {'status': 'PREDICTION_AVAILABLE', 'prediction_status': 'PREDICTION_AVAILABLE',
               'assets': {'model_version': 'retired-v1'}, 'analytical_plans': [{'plan_id': 1}],
               'diagnostic_plans': [{'plan_id': 1}], 'course_predictions': [{'course_id':'c'}], 'plans': []}
        for name in 'ABC'}}
    store.save('run_saved', {'model_versions': {'B':'retired-v1','C':'retired-v1'}}, [result], {})
    original = (tmp_path/'run_saved/student_results.json').read_bytes()
    (tmp_path/'model_versions').mkdir()
    (tmp_path/'model_versions/retired_bundles.json').write_text(json.dumps({
        'retired-v1': {'reason': 'TRAINING_CONTEXT_DID_NOT_USE_FULL_ROSTER', 'replacement':'correct-v2'}}))
    loaded = store.load('run_saved')['student_results'][0]
    assert loaded['experiments']['A']['prediction_status'] == 'PREDICTION_AVAILABLE'
    for name in 'BC':
        assert loaded['experiments'][name]['prediction_status'] == 'BLOCKED'
        assert loaded['experiments'][name]['analytical_plans'] == []
        assert loaded['experiments'][name]['course_predictions'] == []
        assert loaded['experiments'][name]['reason'] == 'RETIRED_EXPERIMENTAL_MODEL'
    assert (tmp_path/'run_saved/student_results.json').read_bytes() == original


def test_api_csv_selection_validation_storage_and_loopback(tmp_path):
    cohort(tmp_path)
    app = create_app(tmp_path, engine_factory=SyntheticEngine)
    with TestClient(app, base_url='http://127.0.0.1') as client:
        students = client.get('/api/students').json()
        assert students['count'] == 2
        assert client.post('/api/runs', json={'sample_ids': [], 'target_credits':18}).status_code == 422
        assert client.post('/api/runs', json={'sample_ids': ['unknown'], 'target_credits':18}).status_code == 422
        assert client.post('/api/runs', json={'sample_ids': ['sample-1'], 'target_credits':0}).status_code == 422
        assert client.post('/api/runs', json={'sample_ids': ['sample-1'], 'target_credits':18}, headers={'Origin':'https://foreign.example'}).status_code == 403
        assert client.get('/api/students', headers={'host':'foreign.example'}).status_code == 403
        response = client.post('/api/runs', json={'sample_ids':['sample-0','sample-1'],'target_credits':18})
        assert response.status_code == 202
        run_id = response.json()['run_id']
        app.state.runner.wait_for_run(run_id, timeout=10)
        assert client.get(f'/api/runs/{run_id}/progress').json()['status'] == 'completed'
        saved = client.get(f'/api/runs/{run_id}').json()
        assert len(saved['student_results']) == 2
        assert client.get('/api/runs').json()['runs'][0]['run_id'] == run_id
        assert client.get('/api/runs/not-existing').status_code == 404
