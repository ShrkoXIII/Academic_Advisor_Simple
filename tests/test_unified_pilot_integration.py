"""Synthetic offline orchestration and real serving-pipeline timing parity."""
import csv
import json
from pathlib import Path

import pandas as pd
import pytest

from tests.test_pilot_20251_engine import bridge
from tests.test_pilot_20251_observed_prediction import predictor
from tests.test_pilot_20251_history import PARTS, row, write_source
from tools.recommendation_pilot_20251.adapter import sha256


def _hashes(root):
    return {p.relative_to(root).as_posix(): sha256(p) for p in root.rglob('*') if p.is_file()}


def test_saved_synthetic_student_runs_directly_and_cold_browsing_never_scores(predictor, tmp_path, monkeypatch):
    from tools.academic_advisor_streamlit.pilot_service import PilotService
    from tools.recommendation_pilot_20251 import modeling

    observed_predictor, engine, student = predictor
    with (tmp_path / 'students.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=[*student, 'role', 'previous_gpa'])
        writer.writeheader()
        writer.writerow({**student, 'role': 'primary', 'previous_gpa': 2.5})
    for part in PARTS:
        write_source(tmp_path, part, [row(part)])
    inspect = engine._experimental.inspect
    monkeypatch.setattr(engine._experimental, 'inspect', lambda: {
        name: {**asset, 'features': modeling.B_FEATURES if name == 'B' else modeling.C_FEATURES}
        for name, asset in inspect().items()})

    def forbidden(*args, **kwargs):
        raise AssertionError('Offline Pilot must not use HTTP or construct scoring dependencies on load')

    import requests
    monkeypatch.setattr(requests.sessions.Session, 'request', forbidden)
    # Binding a listening socket would reveal an accidental Pilot-server startup.
    import socket
    monkeypatch.setattr(socket.socket, 'bind', forbidden)
    observations = []

    class SavedObservations:
        def get(self, selected_student):
            # Outcomes become accessible only after both selected candidate scorers ran.
            assert selected_student['sample_id'] == 'sample'
            assert [name for name, _ in engine._experimental.seen] == ['B', 'C']
            assert not engine._baseline.grade_model.matrices
            observations.append('post-score')
            return {'status': 'AVAILABLE', 'course_count': 2, 'graded_course_count': 2,
                    'total_credits': 6, 'courses': [
                        {'course_id': 'A', 'course_credits': 3, 'grade_version_id': '1',
                         'actual_mark': 60, 'actual_points': 2, 'result_status': 'AVAILABLE',
                         'course_outcome_status': 'pass'},
                        {'course_id': 'B', 'course_credits': 3, 'grade_version_id': '1',
                         'actual_mark': 80, 'actual_points': 4, 'result_status': 'AVAILABLE',
                         'course_outcome_status': 'pass'}]}

    snapshots = tmp_path / 'snapshots'
    before = _hashes(snapshots)
    service = PilotService(tmp_path, engine_factory=lambda **kwargs: engine,
                           predictor_factory=lambda **kwargs: observed_predictor,
                           observed_store=SavedObservations())
    run_id = service.start(['sample'], models=('B', 'C'), target_credits=6, max_plans=6)
    runner = service._runners['after_backend_fix']
    try:
        runner.wait_for_run(run_id, timeout=20)
        progress = service.progress(run_id)
        assert progress['status'] == 'completed', progress
        assert progress['completed'] == progress['total'] == 1
        assert progress['sample_statuses'][0]['models'] == {
            'B': 'PREDICTION_AVAILABLE', 'C': 'PREDICTION_AVAILABLE'}
        saved = service.load_run(run_id)
        manifest = saved['run_manifest']
        assert manifest['selected_models'] == ['B', 'C']
        assert manifest['actual_course_injection'] is False
        assert saved['diagnostics']['university_api_calls'] == 0
        result = saved['student_results'][0]
        assert set(result['experiments']) == set(result['observed_plan_prediction']['experiments']) == {'B', 'C'}
        assert set(result['prediction_metrics']) == {'B', 'C'}
        assert observations == ['post-score']
        assert not engine._baseline.grade_model.matrices
        assert [name for name, _ in engine._experimental.seen] == ['B', 'C', 'B', 'C']
        for _, frame in engine._experimental.seen:
            assert not {'actual_mark', 'actual_points', 'final_mark', 'points', 'finish_status'} & set(frame)
        view = service.presentation(saved, 'sample')
        assert view['actual_summary']['descriptive_gpa'] == 3
        assert view['actual_summary']['official_gpa'] is None
        for name, predicted_gpa, mae in [('B', 3, 10), ('C', 4, 10)]:
            summary = next(r for r in view['summary_rows'] if r['model'] == name)
            assert summary['predicted_actual_plan_gpa'] == predicted_gpa
            assert summary['actual_plan_gpa_error'] == predicted_gpa - 3
            assert summary['evaluated_plans'] == 6
            assert summary['top1_actual_overlap'] == 2
            assert summary['top3_union_actual_overlap'] == 2
            assert view['actual_summary']['models'][name]['mae'] == mae
            assert len(view['plans_by_model'][name]) == 3
            assert len(result['experiments'][name]['diagnostic_plans']) == 3
            assert result['experiments'][name]['full_scored_plan_count'] == 6
        directory = Path(saved['storage_path'])
        complete = json.loads((directory / 'student_results.json').read_text(encoding='utf-8'))[0]
        assert len(complete['experiments']['B']['diagnostic_plans']) == 6
        assert (directory / 'presentation_results.json').stat().st_size < (directory / 'student_results.json').stat().st_size
        run_hashes = _hashes(directory)
        # A rerender and a fresh process resource use saved projections only.
        monkeypatch.setattr(engine, 'evaluate_student', forbidden)
        monkeypatch.setattr(observed_predictor, 'predict', forbidden)
        monkeypatch.setattr(service.observed_store, 'get', forbidden)
        cached_view = service.presentation(service.load_run(run_id), 'sample')
        assert cached_view['execution']['presentation_load_cache_status'] == 'CACHED'
        cached_view['execution']['presentation_load_cache_status'] = 'FRESH'
        assert cached_view == view
        cold = PilotService(tmp_path, engine_factory=forbidden, predictor_factory=forbidden)
        cold_saved = cold.load_run(run_id)
        assert cold.presentation(cold_saved, 'sample') == view
        assert cold.progress(run_id)['completed'] == 1
        assert cold.list_runs()[0]['run_id'] == run_id
        assert cold._runners == cold._predictors == {}
        assert _hashes(directory) == run_hashes
        assert _hashes(snapshots) == before
    finally:
        runner.executor.shutdown(wait=True)


@pytest.mark.parametrize('name', ['B', 'C'])
def test_real_experimental_feature_pipeline_is_identical_with_stage_timers(name):
    from tests.recommendation_fixtures import RecordingModel, synthetic_grade_scale
    from tests.test_pilot_20251_modeling import peer_row
    from tools.recommendation_pilot_20251 import modeling
    from tools.recommendation_pilot_20251.actual_experiment import _TimedExperiments, _timings

    frame = pd.DataFrame({feature: [None, None, None] for feature in modeling.C_FEATURES})
    frame = frame.assign(student_id='target', degree_id='D', course_id=['A', 'B', 'A'],
                         part_id=20251, plan_id=[0, 0, 1], course_credits=[3., 2., 3.],
                         grade_version_id='1', start_agpa_points=2., start_total_in_credits=30.,
                         degree_credits_count=120., prior_total_fail_courses=1.)
    frame['course_history_avg_mark'] = 999.
    contract = modeling.B_FEATURES if name == 'B' else modeling.C_FEATURES
    grade, fail = RecordingModel(80), RecordingModel(.2)
    levels = {feature: ['__MISSING__', '__UNKNOWN__', '1', 'D', 'A', 'B']
              for feature in modeling.CATEGORICAL_FEATURES}
    bundle = {
        'history': modeling.UniversityHistory([
            row(20241, DEGREE_ID='D', COURSE_ID='A'),
            row(20241, DEGREE_ID='D', COURSE_ID='B', COURSE_CREDITS='2')]),
        'models': {name: {'grade': grade, 'fail': fail, 'levels': levels}},
        'manifest': {'experiments': {name: {'features': contract}}},
        'grade_scale': synthetic_grade_scale(),
        'reference': pd.DataFrame([
            {**peer_row(f'peer_{course}_{i}', 20241, 3.), 'course_id': course}
            for course in ('A', 'B') for i in range(20)] + [
                {**peer_row('target', 20241, 2., mark=70.), 'course_id': 'A'}]),
    }
    experimental = modeling.ExperimentalModels()
    experimental._bundle = bundle
    original = frame.copy(deep=True)
    expected = modeling.predict_course_rows(frame, name, bundle=bundle, num_threads=4)
    timings = {name: _timings()}
    actual = _TimedExperiments(experimental, timings).predict_course_rows(frame, name)
    pd.testing.assert_frame_equal(actual, expected)
    pd.testing.assert_frame_equal(frame, original)
    assert actual.course_history_avg_mark.tolist() == [60., 60., 60.]
    assert actual.plan_course_count.tolist() == [2, 2, 1]
    assert actual.plan_total_credits.tolist() == [5., 5., 3.]
    assert actual.expected_points.tolist() == [3., 3., 3.]
    if name == 'C':
        assert actual.peer_expected_points.tolist() == [3., 3., 3.]
        assert actual.similar_peer_support.tolist() == [20, 20, 20]
        assert actual.course_difficulty_gap.tolist() == [10., 10., 10.]
    pd.testing.assert_frame_equal(grade.matrices[0], grade.matrices[1])
    pd.testing.assert_frame_equal(fail.matrices[0], fail.matrices[1])
    assert list(grade.matrices[0]) == contract
    assert bundle['models'][name]['grade'] is grade
    assert bundle['models'][name]['fail'] is fail
    assert timings[name]['prediction_seconds'] > 0
    assert timings[name]['feature_extraction_seconds'] > 0
