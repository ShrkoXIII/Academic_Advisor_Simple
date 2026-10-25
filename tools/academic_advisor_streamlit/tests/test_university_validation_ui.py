"""The university demonstration reads saved views; only buttons can run inference."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def sample_plan(ids, gpa=2.5):
    return {'canonical_id': '-'.join(ids), 'total_credits': 16, 'expected_plan_gpa': gpa,
        'expected_failed_credits': .5, 'plan_difficulty_balance': {'max_fail_probability': .2},
        'courses': [{'course_id': c, 'course_name': 'مادة ' + c, 'course_credits': 4,
            'predicted_mark': 70., 'expected_grade': 'C', 'expected_points': 2.,
            'fail_probability': .2, 'course_history_effective_support': 30} for c in ids]}


class FakeSearch:
    def __init__(self):
        self.starts = []
    def start(self, samples, **kwargs):
        self.starts.append((samples, kwargs))
        return 'benchmark_new'
    def progress(self, run_id):
        return {'status': 'running', 'completed': 0, 'total': 1}


class FakeValidation:
    def __init__(self):
        self.search = FakeSearch()
        self.requests = []
    def cohort(self):
        return [{'sample_id': k, 'part_id': 20251} for k in ('S01', 'S02', 'S03')]
    def catalog(self, snapshot_id):
        return {'historical': [{'key': 'comparison:historical', 'run_id': 'historical',
            'family': 'comparison', 'snapshot_id': snapshot_id, 'student_count': 30}],
            'benchmark': [{'key': 'benchmark:saved', 'run_id': 'saved', 'snapshot_id': snapshot_id,
                'student_count': 5}] if snapshot_id == 'after_backend_fix' else []}
    def preview(self, sample_id, snapshot_id):
        return {'sample_id': sample_id, 'part_id': 20251, 'snapshot_id': snapshot_id,
            'student_summary': {'previous_gpa': None if sample_id == 'S02' else 0.,
                'source': 'Student API beginning snapshot'},
            'credit_target_resolution': {'status': 'RESOLVED', 'minimum_credits': 12,
                'maximum_credits': 16, 'target_credits': 16, 'target_credits_source': 'API'}, 'issues': []}
    def student(self, sample_id, **kwargs):
        return {'sample_id': sample_id, 'part_id': 20251, 'status': 'AVAILABLE',
            'recommendation_status': 'BLOCKED' if sample_id == 'S03' else 'PREDICTION_AVAILABLE',
            'student_summary': self.preview(sample_id, kwargs['snapshot_id'])['student_summary'],
            'provenance': {'run_id': 'historical', 'snapshot_id': kwargs['snapshot_id']},
            'actual_summary': {'descriptive_gpa': 2.25, 'actual_course_count': 2, 'total_credits': 6,
                'models': {m: {'predicted_actual_plan_gpa': 2.5, 'actual_plan_gpa_error': .25,
                    'actual_plan_gpa_absolute_error': .25, 'status': 'PREDICTION_AVAILABLE'} for m in ('B', 'C')}},
            'actual_course_rows': [{'course_id': 'A', 'course_name': 'مادة A', 'course_credits': 3,
                'actual_mark': 60, 'B_predicted_mark': 65, 'C_predicted_mark': 55,
                'B_error': 5, 'C_error': -5, 'B_fail_probability': .2, 'C_fail_probability': .3,
                'course_outcome_status': 'fail', 'student_id': 'PRIVATE_IDENTIFIER'},
                {'course_id': 'B', 'course_name': 'مادة B', 'course_credits': 3,
                 'actual_mark': None, 'B_predicted_mark': None, 'C_predicted_mark': None}], 'issues': []}
    def recommendations(self, sample_id, **kwargs):
        self.requests.append((sample_id, deepcopy(kwargs)))
        legacy = kwargs['source_ref']['kind'] == 'historical'
        if (sample_id != 'S01' or legacy) and not kwargs.get('allow_historical'):
            return {'status': 'UNAVAILABLE', 'reason': 'EXACT_SAVED_CONFIGURATION_UNAVAILABLE', 'models': {}, 'provenance': {}}
        return {'status': 'AVAILABLE_LEGACY' if legacy else 'AVAILABLE', 'provenance': {'run_id': 'historical' if legacy else 'saved'},
            'models': {m: {'strategy': 'FIRST_N' if legacy else kwargs['strategy'],
                'scope': 'LEGACY_DFS_PREFIX' if legacy else kwargs['scope'],
                'budget': 2000 if legacy else kwargs['budget'], 'target_credits': 18 if legacy else 16,
                'status': 'COMPLETE', 'top_plans': [sample_plan(ids, 2.5 + i / 10)
                    for i, ids in enumerate(('ABC', 'ABD', 'ABE'))]} for m in ('B', 'C')}}
    def search_comparison(self, sample_id, **kwargs):
        available = sample_id == 'S01'
        plans = {s: [sample_plan('AB' + str(i))] for i, s in enumerate(('FIRST_N', 'DIVERSE_N', 'SMART_SEARCH'))} if available else {}
        return {'status': 'AVAILABLE' if available else 'UNAVAILABLE', 'reason': None,
            'provenance': {'run_id': 'saved'}, 'oracle_status': 'EXHAUSTIVE_COMPLETE' if available else 'ORACLE_UNAVAILABLE',
            'oracle_summary': {'best_gpa': 2.5, 'evaluated_plans': 3000, 'tied_optimal_count': 2,
                'top_plans': [sample_plan('ABX')]} if available else {},
            'plans_by_strategy': plans,
            'rows': [{'strategy': s, 'budget': kwargs['budget'], 'best_gpa': 2.5,
                'oracle_gpa': 2.5, 'gpa_gap': 0, 'top3_recall': 1, 'evaluated_plans': kwargs['budget'],
                'runtime_seconds': 1.} for s in plans]}
    def cohort_evaluation(self, historical_ref, **kwargs):
        return {'status': 'AVAILABLE', 'total_students': 30, 'provenance': {'run_id': 'historical'},
            'metrics': [{'model': m, 'metric': 'mae', 'value': 5., 'student_count': 30,
                'course_observations': 166} for m in ('B', 'C')],
            'students': [{'sample_id': 'S01', 'model': 'B', 'actual_plan_gpa_error': .25,
                'status': 'AVAILABLE', 'source_run': 'historical'}],
            'courses': [{'sample_id': 'S01', 'model': 'B', 'course_id': 'A', 'error': 5,
                'actual_mark': 60, 'predicted_mark': 65, 'source_run': 'historical'}], 'plans': []}


@pytest.fixture
def university_ui(monkeypatch):
    import requests
    import university_validation_ui as ui
    monkeypatch.setattr(requests.Session, 'request', lambda *a, **k: (_ for _ in ()).throw(AssertionError('LIVE NETWORK')))
    fake = FakeValidation()
    monkeypatch.setattr(ui, 'get_validation_service', lambda: fake)
    class Cross:
        def list_runs(self):
            return []
    monkeypatch.setattr(ui, 'get_cross_service', lambda: Cross())
    app = AppTest.from_string('from university_validation_ui import render_validation\nrender_validation()', default_timeout=30)
    return app, fake


def navigate(app, label):
    app.radio(key='university_section').set_value(label).run()
    assert not app.exception


def test_default_configuration_and_all_six_sections_are_offline(university_ui):
    app, fake = university_ui
    app.run()
    assert not app.exception
    assert app.selectbox(key='university_strategy').value == 'SMART_SEARCH'
    assert app.selectbox(key='university_budget').value == 1000
    assert app.selectbox(key='university_scope').value == 'FULL_SPACE'
    for section in ('🎓 Student Validation', '📚 Recommended Plans', '🔎 Search Algorithms', '📈 Cohort Evaluation', '🏛️ University Presentation'):
        navigate(app, section)
    app.multiselect(key='university_models').set_value(['C']).run()
    navigate(app, '🎓 Student Validation')
    assert not any(metric.label.startswith('B ·') for metric in app.metric)
    app.selectbox(key='university_scope').set_value('FIXED_POOL').run()
    navigate(app, '📚 Recommended Plans')
    assert fake.requests[-1][1]['scope'] == 'FIXED_POOL'
    assert not fake.search.starts


def test_student_state_persists_and_missing_results_are_not_relabelled(university_ui):
    app, fake = university_ui
    app.run().selectbox(key='university_student').set_value('S02').run()
    navigate(app, '📚 Recommended Plans')
    assert any('No saved results for this configuration' in i.value for i in app.info)
    navigate(app, '🔎 Search Algorithms')
    assert app.selectbox(key='university_student').value == 'S02'
    assert any('ORACLE_UNAVAILABLE' in i.value for i in app.warning)
    assert not fake.search.starts


def test_explicit_run_matches_selected_configuration(university_ui):
    app, fake = university_ui
    app.run()
    navigate(app, '📚 Recommended Plans')
    app.selectbox(key='university_budget').set_value(200).run()
    app.selectbox(key='university_strategy').set_value('DIVERSE_N').run()
    app.button(key='university_run').click().run()
    samples, config = fake.search.starts[0]
    assert samples == ['S01'] and config['models'] == ['B', 'C']
    assert config['strategies'] == ['DIVERSE_N'] and config['budgets'] == [200]
    assert config['scopes'] == ['FULL_SPACE']
    app.run()
    assert len(fake.search.starts) == 1


def test_blocked_recommendation_keeps_independent_actual_predictions(university_ui):
    app, fake = university_ui
    app.run().selectbox(key='university_student').set_value('S03').run()
    navigate(app, '🎓 Student Validation')
    assert any('2.500' == item.value for item in app.metric)
    app.selectbox(key='university_strategy').set_value('FIRST_N').run()
    assert any('2.500' == item.value for item in app.metric)
    assert not fake.search.starts


def test_presentation_and_downloads_exclude_personal_fields(university_ui):
    app, fake = university_ui
    app.run()
    navigate(app, '🏛️ University Presentation')
    assert any('غير المختارة' in i.value for i in app.info)
    assert all('PRIVATE_IDENTIFIER' not in str(d.value) for d in app.dataframe)
    navigate(app, '📈 Cohort Evaluation')
    assert len(app.get('download_button')) >= 5
    assert all('student_id' not in str(d.value.columns) for d in app.dataframe)
    assert not fake.search.starts


def test_oracle_course_set_is_visible_and_legacy_target_is_not_relabelled(university_ui):
    app, fake = university_ui
    app.run()
    navigate(app, '🔎 Search Algorithms')
    assert any('أفضل ثلاث خطط Oracle' in e.label for e in app.expander)
    assert any('EXHAUSTIVE' in str(d.value) for d in app.dataframe)
    assert not any('Strategy: EXHAUSTIVE' in c.value and 'Budget: 1000' in c.value for c in app.caption)
    app.selectbox(key='university_source_run').set_value('comparison:historical').run()
    app.checkbox(key='university_legacy').check().run()
    navigate(app, '📚 Recommended Plans')
    assert any('FIRST_N' in c.value and '2000' in c.value for c in app.caption)
    assert any('18.000' in m.value for m in app.metric)
    assert not fake.search.starts


def test_entry_point_preserves_production_and_exposes_university_mode(monkeypatch, university_ui):
    import ui_client
    def unavailable():
        raise ui_client.ClientError('TEST_CONFIG_UNAVAILABLE')
    monkeypatch.setattr(ui_client.Config, 'from_env', unavailable)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'streamlit_app.py'), default_timeout=30).run()
    assert '🏛️ University Validation' in app.radio(key='advisor_operating_mode').options
    app.radio(key='advisor_operating_mode').set_value('🏛️ University Validation').run()
    assert not app.exception
    assert app.selectbox(key='university_strategy').value == 'SMART_SEARCH'
