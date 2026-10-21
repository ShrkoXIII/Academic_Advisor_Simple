"""Prediction readiness is independent of academic approval and GPA projection."""
from tests.test_pilot_20251_engine import bridge
from tools.recommendation_pilot_20251 import adapter
from tools.recommendation_pilot_20251 import engine as pilot


def test_successful_scores_have_independent_provisional_and_projection_states(bridge):
    _, engine, student, _, _, _ = bridge
    result = engine.evaluate_student(student, target_credits=6)
    experiment = result['experiments']['A']
    assert experiment['prediction_status'] == 'PREDICTION_AVAILABLE'
    assert experiment['plan_status'] == 'PROVISIONAL_PLAN'
    assert experiment['cumulative_gpa_status'] == 'UNAVAILABLE'
    assert 0 < len(experiment['analytical_plans']) <= 3
    assert experiment['plans'] == []
    assert all(p['official_registration_validated'] is False for p in experiment['analytical_plans'])
    assert all(p['projected_cumulative_gpa'] is None for p in experiment['analytical_plans'])
    assert experiment['reason_ar']


def test_supplied_degree_and_faculty_values_are_mapped_without_unavailable_warning(bridge):
    _, engine, student, _, _, _ = bridge
    result = engine.evaluate_student(student, target_credits=6)
    assert result['student_summary']['degree_credits_count'] == 120
    assert result['student_summary']['faculty_id'] == 'F'
    assert 'DEGREE_CREDITS_COUNT_UNAVAILABLE' not in result['issues']
    assert 'FACULTY_ID_UNAVAILABLE' not in result['issues']


def test_null_degree_and_faculty_are_real_source_missingness_not_inference_blockers(bridge):
    _, engine, student, sp, cp, save = bridge
    sp['data']['studentDegreeInfo']['DEGREE_CREDITS_COUNT'] = None
    sp['data']['studentDegreeInfo']['FACULTY_ID'] = None
    save(sp, cp)
    result = engine.evaluate_student(student, target_credits=6)
    assert result['experiments']['A']['prediction_status'] == 'PREDICTION_AVAILABLE'
    assert result['student_summary']['degree_credits_count'] is None
    assert result['student_summary']['faculty_id'] is None
    for code in ('DEGREE_CREDITS_COUNT_UNAVAILABLE', 'FACULTY_ID_UNAVAILABLE'):
        issue = next(i for i in result['technical_details']['issues'] if i['code'] == code)
        assert issue['blocks_prediction'] is False
        assert issue['origin'] == 'archive_null_or_absent_value'


def test_existing_academic_source_alias_is_used_without_rederiving_degree_credits(bridge):
    module, engine, student, sp, cp, save = bridge
    sp['data']['studentDegreeInfo']['DEGREE_CREDITS_COUNT'] = None
    sp['data']['studentAcademicInfo']['DEGREE_CREDITS_COUNT'] = '128'
    save(sp, cp)
    snapshot, issues = module.build_snapshot(adapter.load_student_inputs(student, root=engine.root))
    assert snapshot['degree_credits_count'] == 128
    assert 'DEGREE_CREDITS_COUNT_UNAVAILABLE' not in issues


def test_bad_registration_only_value_cannot_block_model_scoring(bridge):
    _, engine, student, sp, cp, save = bridge
    cp['data']['registserRule']['MAX_NEW_COURSES'] = 'undocumented'
    save(sp, cp)
    result = engine.evaluate_student(student, target_credits=6)
    assert result['experiments']['A']['prediction_status'] == 'PREDICTION_AVAILABLE'
    assert result['policy_evidence']['max_new_courses_source'] == 'Courses API.data.registserRule.MAX_NEW_COURSES'
    assert 'MAX_NEW_COURSES_INVALID_OR_UNCONFIRMED' in result['issues']


def test_core_source_conflict_remains_a_prediction_blocker(bridge):
    _, engine, student, sp, cp, save = bridge
    sp['data']['studentDegreeInfo']['GRADE_VERSION_ID'] = 'unknown-version'
    save(sp, cp)
    result = engine.evaluate_student(student, target_credits=6)
    assert result['experiments']['A']['prediction_status'] == 'BLOCKED'
    assert result['experiments']['A']['analytical_plans'] == []


def test_issue_classification_separates_projection_from_registration():
    denominator = pilot.classify_issue('GPA_DENOMINATOR_UNAVAILABLE')
    assert denominator['blocks_prediction'] is False
    assert denominator['blocks_cumulative_gpa'] is True
    policy = pilot.classify_issue('MAX_NEW_COURSES_POLICY_UNCONFIRMED')
    assert policy['blocks_prediction'] is False
    assert policy['blocks_cumulative_gpa'] is False
    assert policy['blocks_official_registration'] is True


def test_bad_experimental_model_inspection_does_not_hide_valid_original_prediction(bridge):
    from lightgbm.basic import LightGBMError
    _, engine, student, _, _, _ = bridge
    class BrokenExperiments:
        def inspect(self):
            raise LightGBMError('invalid model bytes')
    engine._experimental = BrokenExperiments()
    result = engine.evaluate_student(student, target_credits=6)
    assert result['experiments']['A']['prediction_status'] == 'PREDICTION_AVAILABLE'
    assert result['experiments']['B']['prediction_status'] == 'BLOCKED'


def test_bad_original_model_does_not_hide_independent_experimental_prediction(bridge, monkeypatch):
    from lightgbm.basic import LightGBMError
    _, engine, student, _, _, _ = bridge
    def broken_original():
        raise LightGBMError('invalid original model bytes')
    class IndependentExperiments:
        def inspect(self):
            return {name: {'status': 'READY'} for name in 'BC'}
        def predict_course_rows(self, rows, name):
            return rows.assign(predicted_mark=60., expected_points=2., expected_grade='C',
                               fail_probability=.2, course_history_fallback_level=1,
                               course_history_effective_support=30.)
    monkeypatch.setattr(engine, '_load', broken_original)
    engine._experimental = IndependentExperiments()
    result = engine.evaluate_student(student, target_credits=6)
    assert result['experiments']['A']['prediction_status'] == 'BLOCKED'
    assert result['experiments']['B']['prediction_status'] == 'PREDICTION_AVAILABLE'
    assert result['experiments']['C']['prediction_status'] == 'PREDICTION_AVAILABLE'


def test_C_course_feature_evidence_and_weak_support_survive_result_serialization(bridge):
    import pandas as pd
    _, engine, student, _, _, _ = bridge
    result = engine.evaluate_student(student, target_credits=6)
    rows = pd.DataFrame(result['experiments']['A']['course_predictions']).assign(
        peer_expected_points=float('nan'), similar_peer_support=3, course_difficulty_gap=5.)
    experiment = {}
    engine._attach_scores(experiment, rows, 'C')
    course = experiment['course_predictions'][0]
    assert course['peer_expected_points'] is None
    assert course['similar_peer_support'] == 3
    assert course['peer_support_status'] == 'LOW_SUPPORT'
    assert course['peer_minimum_support'] == 5
    assert course['course_difficulty_gap'] == 5.
    assert experiment['analytical_plans'][0]['courses'][0]['peer_support_status'] == 'LOW_SUPPORT'
