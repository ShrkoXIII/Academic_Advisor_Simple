"""Credit bounds are API contracts, independent of candidate supply and counts."""
import importlib
import importlib.util

import pytest

from tests.test_pilot_20251_engine import bridge


def resolve(inputs, manual_target=None, **kwargs):
    name = 'tools.recommendation_pilot_20251.credit_target'
    assert importlib.util.find_spec(name), 'API credit-target resolver is missing'
    return importlib.import_module(name).resolve_credit_target(inputs, manual_target, **kwargs)


def source(minimum='9', maximum='12', **rules):
    return {'identity': {'part_id': 20251}, 'courses_api_response': {'data': {
        'registserRule': {'LOAD_TYPE': 'CREDIT', 'MIN_CREDITS': minimum,
                        'MAX_CREDITS': maximum, **rules},
        'availableCourses': [{'COURSE_CREDITS': '24'}]}}}


@pytest.mark.parametrize('minimum,maximum,target', [('12', '18', 18), ('12', '16', 16),
                                                  ('9', '12', 12), ('15', '15', 15)])
def test_normal_target_is_api_maximum_not_course_count_or_candidate_sum(minimum, maximum, target):
    result = resolve(source(minimum, maximum, MAX_NEW_COURSES='2', MAX_STUDY_CREDITS='36'))
    assert result['status'] == 'RESOLVED'
    assert result['target_credits'] == target
    assert result['target_credits_source'] == 'API'
    assert result['minimum_credits'] == float(minimum)
    assert result['maximum_credits'] == target
    assert result['raw_rules']['MAX_NEW_COURSES'] == '2'


@pytest.mark.parametrize('rules,reason', [
    ({'MAX_CREDITS': None}, 'CREDIT_MAXIMUM_UNAVAILABLE'),
    ({'MIN_CREDITS': None}, 'CREDIT_MINIMUM_UNAVAILABLE'),
    ({'MIN_CREDITS': '18', 'MAX_CREDITS': '12'}, 'CONFLICTING_CREDIT_LIMITS'),
    ({'LOAD_TYPE': 'COURSE'}, 'UNRESOLVED_LOAD_TYPE'),
    ({'MAX_CREDITS': 'nan'}, 'CREDIT_MAXIMUM_UNAVAILABLE'),
])
def test_missing_conflicting_or_wrong_unit_bounds_block_automatic_target(rules, reason):
    inputs = source()
    inputs['courses_api_response']['data']['registserRule'].update(rules)
    result = resolve(inputs)
    assert result['status'] == 'UNRESOLVED'
    assert result['target_credits'] is None
    assert result['reason'] == reason


@pytest.mark.parametrize('profile,target,minimum', [('study', 16, 12), ('graduation', 15, 9)])
def test_explicit_scoped_policy_intersects_corresponding_profile(profile, target, minimum):
    inputs = source('9', '18', MIN_STUDY_CREDITS='12', MAX_STUDY_CREDITS='16',
                    GRAD_MIN_LIMIT='6', GRAD_MAX_LOAD='15')
    inputs['integration_context'] = {'registration_policy': {
        'source': 'approved_backend_policy', 'part_id': '20251', 'load_profile': profile}}
    result = resolve(inputs)
    assert result['status'] == 'RESOLVED'
    assert (result['target_credits'], result['minimum_credits']) == (target, minimum)
    assert result['policy_evidence']['load_profile'] == profile


def test_unknown_profile_is_not_inferred_and_scoped_policy_drift_blocks():
    inputs = source('9', '18', MAX_STUDY_CREDITS='12', GRAD_MAX_LOAD='24')
    assert resolve(inputs)['target_credits'] == 18
    inputs['integration_context'] = {'registration_policy': {
        'source': 'approved', 'part_id': 20252, 'load_profile': 'study'}}
    assert resolve(inputs)['status'] == 'UNRESOLVED'


def test_manual_override_is_separate_diagnostic_and_never_crosses_known_limit():
    assert resolve(source(), 12)['reason'] == 'DIAGNOSTIC_OVERRIDE_NOT_ENABLED'
    manual = resolve(source(), 12, diagnostic_override=True)
    assert manual['status'] == 'RESOLVED'
    assert manual['target_credits_source'] == 'MANUAL_DIAGNOSTIC'
    assert resolve(source(), 18, diagnostic_override=True)['status'] == 'UNRESOLVED'
    assert resolve(source(maximum=None), 12, diagnostic_override=True)['target_credits'] == 12
    assert resolve(source(minimum='18'), 12, diagnostic_override=True)['status'] == 'UNRESOLVED'


def test_engine_automatically_uses_twelve_credit_maximum_and_preserves_exactness(bridge):
    _, engine, student, _, cp, save = bridge
    cp['data']['registserRule']['MAX_CREDITS'] = '12'
    save(courses_payload=cp)
    result = engine.evaluate_student(student, models=['A'])
    assert result['target_credits'] == 12
    assert result['target_credits_source'] == 'API'
    assert result['status'] == 'PREDICTION_AVAILABLE'
    assert result['experiments']['A']['analytical_plans'][0]['total_credits'] == 12
    cp['data']['registserRule']['MAX_CREDITS'] = '11'
    save(courses_payload=cp)
    result = engine.evaluate_student(student, models=['A'])
    assert result['target_credits'] == 11
    assert result['status'] == 'NO_MATCHING_PLAN'
    assert result['search']['evaluated_plan_count'] == 0


def test_engine_missing_api_maximum_blocks_before_scoring(bridge):
    _, engine, student, _, cp, save = bridge
    cp['data']['registserRule'].pop('MAX_CREDITS')
    save(courses_payload=cp)
    result = engine.evaluate_student(student, models=['A'])
    assert result['status'] == 'BLOCKED'
    assert result['target_credits'] is None
    assert 'CREDIT_MAXIMUM_UNAVAILABLE' in result['issues']


def test_explicit_legacy_engine_target_remains_diagnostic(bridge):
    _, engine, student, _, _, _ = bridge
    result = engine.evaluate_student(student, target_credits=6, models=['A'])
    assert result['status'] == 'PREDICTION_AVAILABLE'
    assert result['target_credits_source'] == 'MANUAL_DIAGNOSTIC'


def test_batch_resolves_each_student_and_persists_their_own_bounds(bridge):
    import csv
    import json
    import shutil
    from tools.recommendation_pilot_20251.adapter import sha256
    from tools.recommendation_pilot_20251.runner import ComparisonRunner
    _, engine, student, _, cp, save = bridge
    cp['data']['registserRule']['MAX_CREDITS'] = '12'
    save(courses_payload=cp)
    second = {**student, 'sample_id': 'second'}
    first_dir = engine.root / 'snapshots/after_backend_fix/api_data/students/sample'
    second_dir = first_dir.parent / 'second'
    shutil.copytree(first_dir, second_dir)
    cp['data']['registserRule']['MAX_CREDITS'] = '6'
    path = second_dir / 'courses_response.json'
    path.write_text(json.dumps(cp), encoding='utf-8')
    meta_path = path.with_suffix('.meta.json')
    meta = json.loads(meta_path.read_text())
    meta.update(sha256=sha256(path), bytes=path.stat().st_size)
    meta_path.write_text(json.dumps(meta))
    with (engine.root / 'students.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=[*student, 'role', 'previous_gpa'])
        writer.writeheader()
        for row in (student, second):
            writer.writerow({**row, 'role': 'primary', 'previous_gpa': 2.5})
    runner = ComparisonRunner(engine.root, engine_factory=lambda **kwargs: engine)
    job = runner.run_sync(['sample', 'second'], models=['A'])
    assert job['status'] == 'completed'
    saved = runner.store.load(job['run_id'])
    rows = saved['student_results']
    assert [r['target_credits'] for r in rows] == [12, 6]
    assert all(r['target_credits_source'] == 'API' for r in rows)
    recorded = saved['run_manifest']['credit_targets_by_student']
    assert recorded['sample']['maximum_credits'] == 12
    assert recorded['second']['target_credits'] == 6
    assert saved['run_manifest']['target_credits_source'] == 'API'


def test_service_preview_exposes_api_target_and_blocks_unenabled_manual_override(bridge, monkeypatch):
    from tools.academic_advisor_streamlit.pilot_service import PilotService
    _, engine, student, _, cp, save = bridge
    cp['data']['registserRule']['MAX_CREDITS'] = '12'
    save(courses_payload=cp)
    service = PilotService(engine.root)
    monkeypatch.setattr(service, 'cohort', lambda **kwargs: [student])
    preview = service.preview('sample')
    assert preview['credit_target_resolution']['target_credits'] == 12
    assert preview['credit_target_resolution']['target_credits_source'] == 'API'
    with pytest.raises(ValueError, match='diagnostic'):
        service.start(['sample'], target_credits=6)
