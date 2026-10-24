import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest


def test_snapshot_paths_keep_models_independent_and_reject_unknown_snapshot(tmp_path):
    from tools.recommendation_pilot_20251.snapshots import api_data_root, model_versions_root
    model = tmp_path / 'before_backend_fix/experiments/model_versions'
    model.mkdir(parents=True)
    assert model_versions_root(tmp_path) == model
    assert api_data_root(tmp_path) == tmp_path / 'snapshots/after_backend_fix/api_data'
    assert api_data_root(tmp_path, 'before_backend_fix') == tmp_path / 'snapshots/before_backend_fix/api_data'
    with pytest.raises(ValueError):
        api_data_root(tmp_path, '../before_backend_fix')


def test_missing_after_courses_never_reads_legacy_or_before_inputs(tmp_path):
    from tools.recommendation_pilot_20251.adapter import load_student_inputs, PilotInputError
    for folder in ('api_data/students/s', 'snapshots/before_backend_fix/api_data/students/s'):
        base = tmp_path / folder
        base.mkdir(parents=True)
        for kind in ('student', 'courses'):
            (base / f'{kind}_response.json').write_text('{"success":true,"data":{}}')
    student = {'sample_id': 's', 'student_id': 'S', 'degree_id': 'D', 'part_id': 20251}
    with pytest.raises(PilotInputError, match='MISSING_SNAPSHOT_RESPONSE'):
        load_student_inputs(student, tmp_path)


def test_collector_defaults_to_after_and_before_is_read_only(tmp_path):
    from tools.academic_advisor_streamlit.pilot_collection_store import PilotCollectionStore, CollectionError
    current = PilotCollectionStore(tmp_path)
    p = current.student_file('s', 'courses')
    assert 'snapshots/after_backend_fix/api_data' in p.as_posix()
    body = b'{"success":true,"data":{"availableCourses":[]}}'
    assert current.save(p, body, kind='courses', identity={}, source='fixture')
    assert not current.save(p, b'{"different":true}', kind='courses', identity={}, source='fixture')
    assert p.read_bytes() == body
    old = PilotCollectionStore(tmp_path, snapshot_id='before_backend_fix')
    with pytest.raises(CollectionError, match='read.only'):
        old.save(old.student_file('s', 'courses'), body, kind='courses', identity={}, source='fixture')
    with pytest.raises(CollectionError):
        current.save(old.student_file('s', 'courses'), body, kind='courses', identity={}, source='fixture')


def test_new_runs_use_after_and_old_ids_are_discovered_without_rescoring(tmp_path):
    from tests.test_pilot_20251_app import cohort, SyntheticEngine
    from tools.recommendation_pilot_20251.app import create_app
    from tools.recommendation_pilot_20251.runner import RunStore
    cohort(tmp_path)
    old = RunStore(tmp_path / 'experiments/before_backend_fix/comparison')
    row = {'sample_id': 'sample-1', 'student_id': 's-1', 'experiments': {}}
    old.save('run_historical', {'run_id': 'run_historical', 'status': 'completed', 'part_id': 20251}, [row], {})
    before = (old.root / 'run_historical/student_results.json').read_bytes()

    class Forbidden:
        def predict_many(self, *args):
            raise AssertionError('Historical browsing must never rescore')
        def predict(self, *args):
            raise AssertionError('Historical browsing must never rescore')

    app = create_app(tmp_path, engine_factory=SyntheticEngine, observed_predictor=Forbidden())
    with TestClient(app, base_url='http://127.0.0.1') as client:
        listing = client.get('/api/runs').json()['runs']
        assert listing[0]['snapshot_id'] == 'before_backend_fix'
        saved = client.get('/api/runs/run_historical').json()
        assert saved['student_results'][0]['observed_plan_prediction']['reason'] == 'HISTORICAL_RECOMPUTATION_DISABLED'
        assert saved['student_results'][0]['experiments'] == {}
        job = app.state.runner.run_sync(['sample-1'])
        directory = tmp_path / 'experiments/after_backend_fix/comparison' / job['run_id']
        manifest = json.loads((directory / 'run_manifest.json').read_text())
        assert manifest['snapshot_id'] == 'after_backend_fix'
        assert Path(manifest['api_snapshot_path']) == tmp_path / 'snapshots/after_backend_fix/api_data'
        assert manifest['candidate_mode'] == 'original'
        assert not manifest['actual_course_injection']
        assert (old.root / 'run_historical/student_results.json').read_bytes() == before


def test_before_snapshot_cannot_start_new_runs(tmp_path):
    from tests.test_pilot_20251_app import cohort, SyntheticEngine
    from tools.recommendation_pilot_20251.runner import ComparisonRunner
    cohort(tmp_path)
    runner = ComparisonRunner(tmp_path, snapshot_id='before_backend_fix', engine_factory=SyntheticEngine)
    try:
        with pytest.raises(ValueError, match='read.only'):
            runner.start(['sample-1'])
    finally:
        runner.executor.shutdown()


def test_before_view_cannot_rescore_an_after_run_with_before_inputs(tmp_path):
    from tools.recommendation_pilot_20251.runner import RunStore
    from tools.recommendation_pilot_20251.app import create_app
    store = RunStore(tmp_path / 'experiments/after_backend_fix/comparison', snapshot_id='after_backend_fix')
    store.save('run_new', {'snapshot_id': 'after_backend_fix'}, [{'experiments': {}, 'sample_id': 's'}], {})
    class Forbidden:
        def predict_many(self, *args):
            raise AssertionError('No cross-snapshot inference')
    app = create_app(tmp_path, snapshot_id='before_backend_fix', observed_predictor=Forbidden())
    with TestClient(app, base_url='http://127.0.0.1') as client:
        result = client.get('/api/runs/run_new').json()['student_results'][0]
    assert result['observed_plan_prediction']['reason'] == 'SAVED_RUN_SNAPSHOT_MISMATCH'


def test_dashboard_normal_execution_never_selects_injection_implicitly():
    from tests.test_pilot_20251_dashboard import run_dashboard_scenario, read_dashboard
    assert 'checked' not in read_dashboard().elements['compare-candidates'][1]
    run_dashboard_scenario('''
state.selectedSample = "s";
$("experiment-mode").value = "original";
$("target-credits").value = "18";
$("max-plans").value = "200";
$("compare-candidates").checked = false;
let calls = [];
api = async (path, options) => { calls.push([path, JSON.parse(options.body)]); return {run_id:"run_fixture"}; };
pollRun = async () => {};
executeRun(["s"]).then(() => {
 assert.equal(calls[0][0], "/api/runs");
 assert.deepEqual(calls[0][1], {sample_ids:["s"],target_credits:18,max_plans:200});
 $("experiment-mode").value = "augmented"; // Viewing an archived diagnostic is not permission to inject.
 return executeRun(["s"]);
}).then(() => {
 assert.equal(calls[1][0], "/api/runs");
});
''')


def test_capture_to_snapshot_to_recommendation_smoke(tmp_path):
    from tools.academic_advisor_streamlit.pilot_collection_store import PilotCollectionStore
    from tools.recommendation_pilot_20251.adapter import load_student_inputs, PilotInputError, sha256
    from tools.recommendation_pilot_20251.engine import PilotEngine
    from tests.test_pilot_20251_engine import payloads
    from tests.recommendation_fixtures import synthetic_engine
    import pandas as pd

    store = PilotCollectionStore(tmp_path)
    student = {'sample_id': 'sample', 'student_id': 'S', 'degree_id': 'D', 'part_id': 20251}
    sp, cp = payloads()
    identity = {**student}
    # Seed the verified Student snapshot and an obsolete Courses response only in Before.
    student_path = store.student_file('sample', 'student')
    store.save(student_path, json.dumps(sp).encode(), kind='student', identity=identity, source='fixture')
    old = store.pilot / 'snapshots/before_backend_fix/api_data/students/sample/courses_response.json'
    old.parent.mkdir(parents=True)
    old.write_bytes(b'{"success":true,"data":{"obsolete":true}}')
    before = sha256(old)
    with pytest.raises(PilotInputError, match='MISSING_SNAPSHOT_RESPONSE.*courses_response'):
        load_student_inputs(student, store.pilot)

    class FixtureClient:
        calls = []
        def capture_student(self, *args):
            raise AssertionError('Verified Student bytes must be reused')
        def capture_courses(self, *args):
            self.calls.append(args)
            return cp, json.dumps(cp).encode()

    client = FixtureClient()
    assert store.collect_student(student, client, courses_only=True)
    assert store.collect_student(student, client, courses_only=True)
    assert client.calls == [('S', 'D', 20251)]
    assert sha256(old) == before
    inputs = load_student_inputs(student, store.pilot)
    assert inputs['snapshot_id'] == 'after_backend_fix'
    assert inputs['fingerprints']['courses_response.json'] == sha256(store.student_file('sample', 'courses'))
    engine = PilotEngine(store.pilot)
    engine._baseline = synthetic_engine()
    engine._catalog = pd.DataFrame({'degree_id': ['D'] * 4, 'course_id': list('ABCD'),
        'course_type_id': ['T'] * 4, 'requirement_type_id': ['R'] * 4,
        'course_credits': [3.] * 4, 'credits_count': [120.] * 4,
        'year_order': [1] * 4, 'semester_order': [1] * 4})
    result = engine.evaluate_student(student, target_credits=6, max_plans=10)
    assert result['experiments']['A']['prediction_status'] == 'PREDICTION_AVAILABLE'
    assert result['input_fingerprints'] == inputs['fingerprints']
    assert not list((store.pilot / 'experiments/before_backend_fix').glob('*'))
    (store.pilot / 'students.csv').write_text(
        'sample_id,role,student_id,degree_id,part_id,previous_gpa\nsample,primary,S,D,20251,2.5\n')
    from tests.test_pilot_20251_history import write_source, row
    history_file = write_source(store.pilot, 20243, [row(20243)])
    from tools.recommendation_pilot_20251.runner import ComparisonRunner
    runner = ComparisonRunner(store.pilot, engine_factory=lambda **kwargs: engine)
    try:
        job = runner.run_sync(['sample'], target_credits=6, max_plans=10)
        assert job['status'] == 'completed'
        saved = runner.store.load(job['run_id'])
        assert saved['run_manifest']['api_response_sha256']['sample'] == inputs['fingerprints']
        provenance = saved['run_manifest']['frozen_history_provenance']
        assert provenance['source_sha256']['20243.json'] == sha256(history_file)
        assert Path(provenance['path']) == store.root / 'frozen_history'
    finally:
        runner.executor.shutdown()


def test_real_shared_models_still_load_without_moving_artifacts():
    from tools.recommendation_pilot_20251 import modeling
    from tools.recommendation_pilot_20251.adapter import PILOT_ROOT
    from tools.recommendation_pilot_20251.snapshots import model_versions_root
    if not (model_versions_root(PILOT_ROOT) / 'latest.json').is_file():
        pytest.skip('Local model artifacts unavailable')
    bundle = modeling.load_model_bundle()
    assert set(bundle['models']) == {'B', 'C'}
    assert bundle['manifest']['experiments']['B']['features'] == modeling.B_FEATURES
    assert bundle['manifest']['experiments']['C']['features'] == modeling.C_FEATURES
    assert bundle['path'].startswith(str(model_versions_root(PILOT_ROOT)))
