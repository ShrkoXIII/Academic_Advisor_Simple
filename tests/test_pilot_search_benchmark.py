"""Small offline proofs for chunk scoring, persistence, oracle and metrics."""
import json
from dataclasses import asdict

import pandas as pd
import pytest


def test_original_pilot_scoring_and_plan_context_are_preserved():
    from tools.recommendation_pilot_20251.search_benchmark import score_chunk
    from tools.recommendation_pilot_20251.engine import PilotEngine
    from src.recommendation.plan_generation import build_plan_rows

    class Scorer:
        def predict_course_rows(self, rows, name):
            assert not {'actual_mark', 'actual_points', 'final_mark'} & set(rows)
            rows = rows.copy()
            rows['predicted_mark'] = rows.groupby('plan_id').course_credits.transform('mean') * 20
            rows['expected_points'] = rows.predicted_mark / 25
            rows['expected_grade'] = 'X'
            rows['fail_probability'] = rows.groupby('plan_id').course_credits.transform('max') / 10
            rows['course_history_fallback_level'] = 6
            rows['course_history_effective_support'] = 0
            return rows

    base = pd.DataFrame({'course_id': list('ABC'), 'course_name': list('abc'), 'course_credits': [1., 2., 3.]})
    plans, ranks = [(0, 1), (2,)], [3, 8]
    expected = {}
    PilotEngine._attach_scores(expected, Scorer().predict_course_rows(build_plan_rows(base, plans), 'B'), 'B')
    actual, timing = score_chunk(base, plans, ranks, Scorer(), 'B')
    assert timing['feature_preparation_seconds'] >= 0
    for got, old in zip(actual, expected['diagnostic_plans']):
        assert got['expected_plan_gpa'] == old['expected_plan_gpa']
        assert got['expected_failed_credits'] == old['expected_failed_credits']
        assert got['total_credits'] == old['total_credits']
    assert actual[0]['expected_plan_gpa'] != actual[1]['expected_plan_gpa']
    assert [p['plan_id'] for p in actual] == ranks


def test_score_ledger_resume_integrity_and_completeness(tmp_path):
    from tools.recommendation_pilot_20251.search_benchmark import ScoreLedger, IntegrityError
    ledger = ScoreLedger(tmp_path / 'scores.sqlite', 'inputs-v1')
    plans = [dict(plan_id=i, canonical_id=str(i), total_credits=3, expected_plan_gpa=2+i/10,
                  expected_failed_credits=.1, plan_difficulty_balance={'max_fail_probability': .1}, courses=[])
             for i in range(5)]
    ledger.commit('oracle/B', plans[:2], {'full_plan_inference_seconds': .2})
    assert ledger.summary('oracle/B', expected_count=5, exhaustive=True)['status'] == 'EXHAUSTIVE_INCOMPLETE'
    ledger.close()
    with pytest.raises(IntegrityError, match='fingerprint'):
        ScoreLedger(tmp_path / 'scores.sqlite', 'different')
    ledger = ScoreLedger(tmp_path / 'scores.sqlite', 'inputs-v1')
    assert ledger.cursor('oracle/B') == 2
    ledger.commit('oracle/B', plans[2:], {'full_plan_inference_seconds': .3})
    result = ledger.summary('oracle/B', expected_count=5, exhaustive=True)
    assert result['status'] == 'EXHAUSTIVE_COMPLETE'
    assert result['completeness_proof']['unique_scored_count'] == 5
    assert result['best_gpa'] == 2.4
    assert [p['plan_id'] for p in result['top_plans']] == [4, 3, 2]
    ledger.connection.execute("UPDATE scores SET gpa=99 WHERE ordinal='0'")
    ledger.connection.commit()
    with pytest.raises(IntegrityError, match='checksum'):
        ledger.verify('oracle/B', exhaustive=True)
    ledger.close()


def test_top3_recall_handles_ties_without_changing_original_ranking():
    from tools.recommendation_pilot_20251.search_benchmark import compare_oracle, diversity
    top = [dict(canonical_id=str(i), expected_plan_gpa=g, courses=[{'course_id': c} for c in cs])
           for i,g,cs in [(0,3.,'AB'),(1,3.,'AC'),(2,2.5,'AD')]]
    search = [dict(canonical_id='other', expected_plan_gpa=3., courses=[{'course_id':'Z'}])]
    result = compare_oracle(search, top, oracle_complete=True, oracle_score_counts=[(3.,1)])
    assert result['gpa_gap'] == 0
    assert result['top3_recall'] == 0
    assert result['score_equivalent_top3_recall'] == pytest.approx(1/3)
    assert compare_oracle(search, top, oracle_complete=False)['oracle_gpa'] is None
    assert diversity(top)['mean_jaccard'] == pytest.approx(1/3)


def test_safeguards_and_budget_validation():
    from tools.recommendation_pilot_20251.search_benchmark import ResourceLimits, validate_configuration
    assert ResourceLimits(**asdict(ResourceLimits())).chunk_size <= 512
    with pytest.raises(ValueError):
        ResourceLimits(chunk_size=0)
    with pytest.raises(ValueError):
        validate_configuration(['B'], ['FIRST_N'], [201], ['FULL_SPACE'])


def test_canonical_identity_does_not_depend_on_input_order():
    from tools.recommendation_pilot_20251.search_benchmark import canonical_plan_id
    assert canonical_plan_id(['C','A']) == canonical_plan_id(['A','C'])
    assert canonical_plan_id(['AB','C']) != canonical_plan_id(['A','BC'])


def synthetic_service(tmp_path):
    from tools.recommendation_pilot_20251.search_benchmark import SearchBenchmarkService, BenchmarkContext
    from tools.recommendation_pilot_20251.search_space import ExactPlanSpace
    class Scorer:
        def __init__(self):
            self.calls = []
        def predict_course_rows(self, rows, name):
            self.calls.append((name, rows.plan_id.nunique()))
            rows = rows.copy()
            rows['predicted_mark'] = rows.course_id.map({'A': 30., 'B': 50., 'C': 80., 'D': 95.})
            rows['expected_points'] = rows.predicted_mark / 25
            rows['expected_grade'] = 'X'
            rows['fail_probability'] = .1
            rows['course_history_fallback_level'] = 6
            rows['course_history_effective_support'] = 0
            return rows
    scorer = Scorer()
    student = {'sample_id':'sample', 'part_id':20251}
    def factory(student, limits, manual, diagnostic):
        base = pd.DataFrame({'course_id':list('ABCD'), 'course_name':list('abcd'), 'course_credits':[3.] * 4})
        return BenchmarkContext(student, {'status':'RESOLVED','target_credits':6.,'target_credits_source':'API'},
            base, ExactPlanSpace(base, 6.), scorer, {'B':{'status':'READY'},'C':{'status':'READY'}},
            {'source':'unchanged'}, ['REPEAT_POLICY_UNAVAILABLE'], [30,50,80,95], 0.,0.,{})
    service = SearchBenchmarkService(tmp_path, context_factory=factory)
    service.cohort = lambda: [student]
    return service, scorer


def test_complete_matrix_matches_exhaustive_and_reading_never_scores(tmp_path):
    from tools.recommendation_pilot_20251.search_benchmark import ResourceLimits
    service, scorer = synthetic_service(tmp_path)
    try:
        saved = service.run_sync(['sample'], scopes=['FIXED_POOL','FULL_SPACE','EXHAUSTIVE'],
                                 limits=ResourceLimits(chunk_size=2))
        assert saved['run_manifest']['status'] == 'completed', saved['run_manifest']
        row = saved['student_results'][0]
        assert len(row['experiments']) == 38
        for result in row['experiments']:
            assert result['evaluated_plans'] == 6
            assert result['gpa_gap'] == 0
            assert result['top3_recall'] == 1
            assert [p['plan_id'] for p in result['top_plans']] == [5,4,3]
            assert result['oracle_complete'] is True
        calls = list(scorer.calls)
        service.load_run(saved['run_manifest']['run_id'])
        service.list_runs()
        assert scorer.calls == calls
        assert (tmp_path/'experiments/after_backend_fix/search_benchmark'/saved['run_manifest']['run_id']/'integrity.json').exists()
    finally:
        service.executor.shutdown(wait=True)


def test_interrupted_oracle_resumes_only_uncommitted_plans(tmp_path):
    from tools.recommendation_pilot_20251.search_benchmark import ResourceLimits
    service, scorer = synthetic_service(tmp_path)
    try:
        saved = service.run_sync(['sample'], models=['B'], scopes=['EXHAUSTIVE'],
                                 limits=ResourceLimits(chunk_size=2, max_oracle_plans=2))
        first = saved['student_results'][0]['experiments'][0]
        assert first['status'] == 'EXHAUSTIVE_INCOMPLETE'
        assert first['oracle_gpa'] is None
        assert first['completeness_proof']['all_feasible_plans_scored'] is False
        run_id = saved['run_manifest']['run_id']
        resumed = service.run_sync([], resume_run_id=run_id, limits=ResourceLimits(chunk_size=2, max_oracle_plans=10))
        assert resumed['student_results'][0]['experiments'][0]['status'] == 'EXHAUSTIVE_COMPLETE'
        assert sum(count for _, count in scorer.calls) == 6
    finally:
        service.executor.shutdown(wait=True)


def test_resuming_invalidates_old_seal_and_interrupted_results_remain_readable(tmp_path, monkeypatch):
    from concurrent.futures import Future
    from pathlib import Path
    from tools.recommendation_pilot_20251.search_benchmark import ResourceLimits
    service, scorer = synthetic_service(tmp_path)
    try:
        saved = service.run_sync(['sample'], models=['B'], scopes=['EXHAUSTIVE'],
                                 limits=ResourceLimits(chunk_size=2, max_oracle_plans=2))
        directory = Path(saved['storage_path'])
        run_id = saved['run_manifest']['run_id']
        assert (directory / 'integrity.json').exists()
        calls = list(scorer.calls)
        monkeypatch.setattr(service.executor, 'submit', lambda *args: Future())
        service.start([], resume_run_id=run_id)
        assert not (directory / 'integrity.json').exists()
        # A worker updates this file before its next chunk; the prior seal must
        # no longer certify an actively changing result directory.
        context_path = directory / 'sample/context.json'
        context = json.loads(context_path.read_text(encoding='utf8'))
        context['preparation_attempts'].append({'preparation_seconds': .25})
        context_path.write_text(json.dumps(context), encoding='utf8')
        assert service.load_run(run_id)['run_manifest']['status'] == 'running'
        service.jobs[run_id]['status'] = 'interrupted'
        recovered = service.load_run(run_id)
        assert recovered['run_manifest']['status'] == 'EXHAUSTIVE_INCOMPLETE'
        assert recovered['student_results'][0]['experiments'][0]['evaluated_plans'] == 2
        assert scorer.calls == calls
    finally:
        service.executor.shutdown(wait=True)


def test_checkpoint_top3_must_be_the_actual_global_order(tmp_path):
    from tools.recommendation_pilot_20251.search_benchmark import ScoreLedger, IntegrityError
    ledger = ScoreLedger(tmp_path/'scores.sqlite', 'same')
    plans = [dict(plan_id=i,canonical_id=str(i),total_credits=3.,expected_plan_gpa=3.-i,
        expected_failed_credits=.1,plan_difficulty_balance={'max_fail_probability':.1},courses=[]) for i in range(2)]
    try:
        ledger.commit('oracle/B', plans, {})
        ledger.connection.execute('UPDATE checkpoints SET top_json=? WHERE job=?', (json.dumps([plans[1]]),'oracle/B'))
        ledger.connection.commit()
        with pytest.raises(IntegrityError, match='top-three'):
            ledger.summary('oracle/B', expected_count=2, exhaustive=True)
    finally:
        ledger.close()


def test_selection_is_pinned_on_resume_even_with_changed_state_allowance(tmp_path):
    from tools.recommendation_pilot_20251.search_benchmark import ResourceLimits
    service, scorer = synthetic_service(tmp_path)
    try:
        saved = service.run_sync(['sample'], models=['B'],strategies=['SMART_SEARCH'],budgets=[200],scopes=['FIXED_POOL'],
            limits=ResourceLimits(chunk_size=2,max_space_states=5))
        run_id = saved['run_manifest']['run_id']
        selected_path = tmp_path/'experiments/after_backend_fix/search_benchmark'/run_id/'sample/FIXED_POOL_SMART_SEARCH_200.json'
        selected = selected_path.read_bytes()
        resumed = service.run_sync([], resume_run_id=run_id, limits=ResourceLimits(chunk_size=2,max_space_states=100))
        assert resumed['run_manifest']['status'] != 'failed'
        assert selected_path.read_bytes() == selected
        assert sum(count for _,count in scorer.calls) == resumed['student_results'][0]['experiments'][0]['evaluated_plans']
    finally:
        service.executor.shutdown(wait=True)


def test_orphan_running_job_is_resumable_and_not_advertised_as_complete(tmp_path):
    service, _ = synthetic_service(tmp_path)
    try:
        saved = service.run_sync(['sample'],models=['B'],scopes=['EXHAUSTIVE'])
        run_id = saved['run_manifest']['run_id']
        path = tmp_path/'experiments/after_backend_fix/search_benchmark'/run_id/'run_manifest.json'
        manifest = json.loads(path.read_text())
        manifest['status'] = 'running'
        path.write_text(json.dumps(manifest))
        service.jobs.clear()
        assert service.list_runs()[0]['status'] == 'EXHAUSTIVE_INCOMPLETE'
    finally:
        service.executor.shutdown(wait=True)


def test_atomic_json_retries_transient_windows_sharing_failure(tmp_path, monkeypatch):
    from pathlib import Path
    from tools.recommendation_pilot_20251.search_benchmark import atomic_json
    original = Path.replace
    calls = []
    def transient(self, target):
        calls.append(target)
        if len(calls) < 3:
            raise PermissionError('transient sharing lock')
        return original(self, target)
    monkeypatch.setattr(Path, 'replace', transient)
    atomic_json(tmp_path/'value.json', {'complete':False})
    assert json.loads((tmp_path/'value.json').read_text()) == {'complete':False}
    assert len(calls) == 3


def test_huge_oracle_count_is_capped_without_materializing_the_universe(tmp_path):
    from tools.recommendation_pilot_20251.search_benchmark import ResourceLimits, BenchmarkContext, SearchBenchmarkService
    from tools.recommendation_pilot_20251.search_space import ExactPlanSpace
    class Scorer:
        def predict_course_rows(self, rows, name):
            return rows.assign(predicted_mark=75.,expected_points=3.,expected_grade='B',fail_probability=.1,
                course_history_fallback_level=6,course_history_effective_support=0)
    base = pd.DataFrame({'course_id':[str(i) for i in range(80)],'course_name':['x']*80,'course_credits':[1.]*80})
    space = ExactPlanSpace(base,40.)
    student = {'sample_id':'huge','part_id':20251}
    service = SearchBenchmarkService(tmp_path,context_factory=lambda *args: BenchmarkContext(student,
        {'target_credits':40.,'target_credits_source':'API'},base,space,Scorer(),{'B':{'status':'READY'}},{},[],[0.]*80,0.,0.,{}))
    service.cohort = lambda: [student]
    try:
        saved = service.run_sync(['huge'],models=['B'],scopes=['EXHAUSTIVE'],limits=ResourceLimits(max_oracle_plans=2,chunk_size=2))
        result = saved['student_results'][0]['experiments'][0]
        assert result['status'] == 'EXHAUSTIVE_INCOMPLETE'
        assert result['evaluated_plans'] == result['unique_plans_discovered'] == 2
        assert result['feasible_plan_count'] > 2**63
        assert result['reason'] == 'ORACLE_PLAN_RESOURCE_LIMIT'
    finally:
        service.executor.shutdown(wait=True)


def test_unstarted_selection_can_be_bound_after_a_deferred_attempt(tmp_path):
    from tools.recommendation_pilot_20251.search_benchmark import ScoreLedger
    ledger = ScoreLedger(tmp_path/'scores.sqlite','inputs')
    try:
        ledger.bind_selection('deferred/B', [])
        ledger.bind_selection('deferred/B', [4,2,3])
    finally:
        ledger.close()


def test_resumed_runtime_includes_all_context_preparation_attempts(tmp_path):
    from tools.recommendation_pilot_20251.search_benchmark import ResourceLimits
    service, _ = synthetic_service(tmp_path)
    original = service.context_factory
    def factory(*args):
        context = original(*args)
        context.preparation_seconds = .25
        return context
    service.context_factory = factory
    try:
        saved = service.run_sync(['sample'],models=['B'],scopes=['EXHAUSTIVE'],limits=ResourceLimits(max_oracle_plans=2))
        resumed = service.run_sync([],resume_run_id=saved['run_manifest']['run_id'],limits=ResourceLimits(max_oracle_plans=10))
        row = resumed['student_results'][0]
        assert row['cumulative_preparation_seconds'] == .5
        result = row['experiments'][0]
        assert result['standalone_runtime_seconds'] == pytest.approx(result['runtime_seconds']+.5)
    finally:
        service.executor.shutdown(wait=True)
