"""Synthetic complete-plan proofs for the explicit optional cross-model action."""
from copy import deepcopy
from importlib.util import find_spec
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from tools.recommendation_pilot_20251.engine import _digest
from tools.recommendation_pilot_20251.search_benchmark import canonical_plan_id
from tools.recommendation_pilot_20251.search_space import ExactPlanSpace


class CompletePlanScorer:
    def __init__(self):
        self.calls = []

    def predict_course_rows(self, rows, model):
        assert not {'actual_mark', 'actual_points', 'final_mark', 'course_outcome_status'} & set(rows)
        self.calls.append((model, [tuple(group.course_id) for _, group in rows.groupby('plan_id')]))
        rows = rows.copy()
        rows['predicted_mark'] = 60. if model == 'B' else 80.
        rows['expected_points'] = 2. if model == 'B' else 3.
        rows['expected_grade'] = 'X'
        rows['fail_probability'] = .2 if model == 'B' else .1
        rows['course_history_fallback_level'] = 6
        rows['course_history_effective_support'] = 0
        return rows


def configured_service(tmp_path, *, identical=False):
    assert find_spec('tools.academic_advisor_streamlit.cross_model_service') is not None, 'CrossModelService is missing'
    from tools.academic_advisor_streamlit.cross_model_service import CrossModelService
    base = pd.DataFrame({'course_id': list('ABC'), 'course_name': list('abc'), 'course_credits': [3.] * 3})
    assets = {model: {'status': 'READY', 'model_version': 'test-v1', 'feature_count': 44 if model == 'B' else 47,
                     'artifact_sha256': model * 64, 'manifest_sha256': 'a' * 64,
                     'reference_sha256': 'b' * 64, 'grade_scale_sha256': 'c' * 64,
                     'training_as_of_part': 20243, 'history_as_of_part': 20243}
              for model in 'BC'}
    inputs = {'student_response.json': 'd' * 64, 'courses_response.json': 'e' * 64}
    scorer = CompletePlanScorer()
    context = SimpleNamespace(base=base, space=ExactPlanSpace(base, 6), scorer=scorer,
        assets=assets, inputs=inputs, target_resolution={'status': 'RESOLVED', 'target_credits': 6.,
        'target_credits_source': 'API'}, fingerprint='context-fingerprint')
    plans = {model: {'canonical_id': canonical_plan_id(ids), 'total_credits': 6.,
                     'courses': [{'course_id': cid, 'course_credits': 3.} for cid in ids]}
             for model, ids in [('B', 'AB'), ('C', 'AB' if identical else 'BC')]}
    source = {'status': 'AVAILABLE', 'models': {model: {'top_plans': [plans[model]]} for model in 'BC'},
        'provenance': {'snapshot_id': 'after_backend_fix', 'part_id': 20251, 'sample_id': 'safe-sample',
            'input_fingerprints': deepcopy(inputs), 'model_assets': deepcopy(assets),
            'candidate_sha256': _digest(base.to_dict('records')), 'fingerprint': 'context-fingerprint',
            'target_credits': 6., 'target_resolution': deepcopy(context.target_resolution),
            'actual_course_injection': False, 'strategy': 'SMART_SEARCH', 'budget': 1000, 'scope': 'FULL_SPACE'}}

    class Validation:
        def recommendations(self, sample_id, **kwargs):
            assert sample_id == 'safe-sample'
            assert kwargs['allow_historical'] is False
            return deepcopy(source)

    class Search:
        context_calls = 0

        def cohort(self):
            return [{'sample_id': 'safe-sample', 'part_id': 20251, 'student_id': 'PRIVATE_STUDENT'}]

        def _context(self, student, limits):
            self.context_calls += 1
            assert limits.chunk_size <= 2 and limits.max_seconds <= 300
            return context

    search = Search()
    service = CrossModelService(validation=Validation(), search=search, root=tmp_path)
    return service, scorer, search, source, context


def execute(service):
    run_id = service.start('safe-sample', snapshot_id='after_backend_fix',
        source_ref={'kind': 'benchmark', 'run_id': 'benchmark_synthetic'}, target_credits=6)
    service.futures[run_id].result(timeout=15)
    return run_id, service.load_run(run_id)


def test_construct_and_read_never_prepare_or_score_or_create_storage(tmp_path):
    service, scorer, search, _, _ = configured_service(tmp_path)
    try:
        assert service.list_runs() == []
        assert not (tmp_path / 'experiments').exists()
        with pytest.raises(FileNotFoundError):
            service.load_run('cross_missing')
        assert search.context_calls == 0
        assert scorer.calls == []
    finally:
        service.executor.shutdown(wait=True)


def test_two_source_top1_plans_are_scored_as_complete_shared_contexts(tmp_path):
    service, scorer, search, source, _ = configured_service(tmp_path)
    try:
        original = deepcopy(source)
        run_id, saved = execute(service)
        assert saved['status'] == 'completed', saved
        assert source == original
        assert scorer.calls == [('B', [('A', 'B'), ('B', 'C')]), ('C', [('A', 'B'), ('B', 'C')])]
        assert search.context_calls == 1
        assert {(r['source_model'], r['scoring_model']) for r in saved['rows']} == {('B', 'B'), ('B', 'C'), ('C', 'B'), ('C', 'C')}
        assert [r['expected_plan_gpa'] for r in saved['rows'] if r['scoring_model'] == 'B'] == [2., 2.]
        assert [r['expected_failed_credits'] for r in saved['rows'] if r['scoring_model'] == 'C'] == pytest.approx([.6, .6])
        assert saved['run_manifest']['complete_plan_model_evaluations'] == 4
        assert service.progress(run_id)['status'] == 'completed'
        assert service.list_runs()[0]['run_id'] == run_id
        service.load_run(run_id)
        assert len(scorer.calls) == 2
        assert 'PRIVATE_STUDENT' not in json.dumps(saved)
        assert 'student_id' not in json.dumps(saved)
    finally:
        service.executor.shutdown(wait=True)


def test_identical_source_sets_are_evaluated_once_per_model(tmp_path):
    service, scorer, _, _, _ = configured_service(tmp_path, identical=True)
    try:
        _, saved = execute(service)
        assert saved['status'] == 'completed', saved
        assert scorer.calls == [('B', [('A', 'B')]), ('C', [('A', 'B')])]
        assert len(saved['rows']) == 4
        assert saved['run_manifest']['complete_plan_model_evaluations'] == 2
        assert saved['run_manifest']['unique_source_plan_count'] == 1
    finally:
        service.executor.shutdown(wait=True)


@pytest.mark.parametrize('mismatch', ['inputs', 'model', 'candidate', 'target', 'canonical', 'unknown_course'])
def test_incompatible_source_never_reaches_complete_plan_scoring(tmp_path, mismatch):
    service, scorer, _, source, _ = configured_service(tmp_path)
    if mismatch == 'inputs':
        source['provenance']['input_fingerprints']['student_response.json'] = 'different'
    elif mismatch == 'model':
        source['provenance']['model_assets']['C']['artifact_sha256'] = 'different'
    elif mismatch == 'candidate':
        source['provenance']['candidate_sha256'] = 'different'
    elif mismatch == 'target':
        source['provenance']['target_credits'] = 9.
    elif mismatch == 'canonical':
        source['models']['B']['top_plans'][0]['canonical_id'] = 'different'
    else:
        source['models']['B']['top_plans'][0]['courses'][0]['course_id'] = 'UNKNOWN'
    try:
        _, saved = execute(service)
        assert saved['status'] == 'BLOCKED', saved
        assert saved['reason']
        assert saved['rows'] == []
        assert scorer.calls == []
    finally:
        service.executor.shutdown(wait=True)


def test_missing_saved_selection_blocks_without_preparing_current_context(tmp_path):
    service, scorer, search, source, _ = configured_service(tmp_path)
    source.update(status='UNAVAILABLE', reason='NO_COMPATIBLE_SAVED_RECOMMENDATIONS')
    try:
        _, saved = execute(service)
        assert saved['status'] == 'BLOCKED'
        assert saved['reason'] == 'NO_COMPATIBLE_SAVED_RECOMMENDATIONS'
        assert search.context_calls == 0 and scorer.calls == []
    finally:
        service.executor.shutdown(wait=True)


def test_legacy_or_injected_source_is_rejected_without_scoring(tmp_path):
    service, scorer, search, source, _ = configured_service(tmp_path)
    try:
        with pytest.raises(ValueError):
            service.start('safe-sample', snapshot_id='before_backend_fix', source_ref={'kind': 'benchmark', 'run_id': 'benchmark_old'})
        with pytest.raises(ValueError):
            service.start('safe-sample', snapshot_id='after_backend_fix', source_ref={'kind': 'historical', 'run_id': 'run_old'})
        source['provenance']['actual_course_injection'] = True
        _, saved = execute(service)
        assert saved['status'] == 'BLOCKED'
        assert scorer.calls == [] and search.context_calls == 0
    finally:
        service.executor.shutdown(wait=True)


def test_tampered_saved_cross_model_rows_are_rejected_on_read(tmp_path):
    service, _, _, _, _ = configured_service(tmp_path)
    try:
        run_id, saved = execute(service)
        directory = tmp_path / 'experiments/after_backend_fix/university_validation/cross_model' / run_id
        path = directory / 'rows.json'
        rows = json.loads(path.read_text(encoding='utf-8'))
        rows[0]['expected_plan_gpa'] = 999
        path.write_text(json.dumps(rows), encoding='utf-8')
        with pytest.raises(ValueError, match='integrity|hash|checksum'):
            service.load_run(run_id)
    finally:
        service.executor.shutdown(wait=True)


def test_guard_blocks_expired_context_before_any_scoring(tmp_path, monkeypatch):
    service, scorer, search, _, _ = configured_service(tmp_path)
    original = search._context

    def context_after_deadline(student, limits):
        context = original(student, limits)
        monkeypatch.setattr('tools.academic_advisor_streamlit.cross_model_service.perf_counter', lambda: float('inf'))
        return context

    search._context = context_after_deadline
    try:
        _, saved = execute(service)
        assert saved['status'] == 'BLOCKED'
        assert saved['reason'] == 'CROSS_MODEL_RUNTIME_LIMIT'
        assert scorer.calls == []
    finally:
        service.executor.shutdown(wait=True)


def test_persistence_error_is_reported_without_a_permanently_running_job(tmp_path, monkeypatch):
    service, _, _, _, _ = configured_service(tmp_path)

    def cannot_write(*args):
        raise PermissionError('private system detail')

    monkeypatch.setattr('tools.academic_advisor_streamlit.cross_model_service.atomic_json', cannot_write)
    try:
        run_id = service.start('safe-sample', snapshot_id='after_backend_fix',
            source_ref={'kind': 'benchmark', 'run_id': 'benchmark_synthetic'}, target_credits=6)
        with pytest.raises(PermissionError):
            service.futures[run_id].result(timeout=15)
        progress = service.progress(run_id)
        assert progress['status'] == 'failed'
        assert progress['reason'] == 'CROSS_MODEL_PERSISTENCE_UNAVAILABLE'
        assert 'private system detail' not in json.dumps(progress)
    finally:
        service.executor.shutdown(wait=True)
