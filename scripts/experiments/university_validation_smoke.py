"""Read-only AppTest demonstration on three real saved samples, with inference forbidden."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from tools.academic_advisor_streamlit.validation_service import ValidationService
from tools.recommendation_pilot_20251.adapter import PILOT_ROOT


def main():
    ui_path = Path(__file__).resolve().parents[2] / 'tools/academic_advisor_streamlit'
    sys.path.insert(0, str(ui_path))
    import university_validation_ui as ui
    service = ValidationService()
    source = {'kind': 'benchmark', 'run_id': 'benchmark_20261024T120117_4a7c2fc8'}
    historical = {'run_id': 'run_20261024T095941_95ed021f89', 'family': 'comparison'}
    def forbidden(*args, **kwargs):
        raise AssertionError('Browsing must not perform inference, execution or HTTP requests.')
    records = []
    try:
        with ExitStack() as stack:
            stack.enter_context(patch.object(ui, 'get_validation_service', return_value=service))
            for target in ('requests.sessions.Session.request',
                'tools.recommendation_pilot_20251.engine.PilotEngine.evaluate_student',
                'tools.recommendation_pilot_20251.observed_prediction.ObservedPlanPredictor.predict',
                'tools.recommendation_pilot_20251.observed_prediction.ObservedPlanPredictor.predict_many',
                'tools.recommendation_pilot_20251.modeling.ExperimentalModels.predict_course_rows',
                'tools.recommendation_pilot_20251.search_benchmark.SearchBenchmarkService.start',
                'tools.academic_advisor_streamlit.cross_model_service.CrossModelService.start'):
                stack.enter_context(patch(target, side_effect=forbidden))
            app = AppTest.from_string('from university_validation_ui import render_validation\nrender_validation()', default_timeout=120).run()
            for sample in ('P20251-04-P04', 'P20251-01-P01', 'P20251-04-P01'):
                app.selectbox(key='university_student').set_value(sample).run()
                view = service.student(sample, historical_ref=historical)
                preview = service.preview(sample)
                target = preview['credit_target_resolution']['target_credits']
                recommendation = service.recommendations(sample, source_ref=source, target_credits=target)
                search = service.search_comparison(sample, run_id=source['run_id'], target_credits=target)
                sections = []
                for section in ('🎓 Student Validation', '📚 Recommended Plans', '🔎 Search Algorithms',
                                '📈 Cohort Evaluation', '🏛️ University Presentation'):
                    app.radio(key='university_section').set_value(section).run()
                    assert not app.exception, app.exception
                    assert not app.error, [e.value for e in app.error]
                    assert all('student_id' not in str(frame.value.columns) for frame in app.dataframe)
                    sections.append({'section': section, 'dataframes': len(app.dataframe),
                                     'metrics': len(app.metric), 'errors': 0})
                records.append({'sample_id': sample, 'historical_recommendation_status': view['recommendation_status'],
                    'actual_gpa': view['actual_summary']['descriptive_gpa'],
                    'actual_registered_credits': view['actual_summary']['total_credits'],
                    'B_predicted_actual_plan_gpa': view['actual_summary']['models']['B']['predicted_actual_plan_gpa'],
                    'C_predicted_actual_plan_gpa': view['actual_summary']['models']['C']['predicted_actual_plan_gpa'],
                    'api_target': target, 'new_recommendations_status': recommendation['status'],
                    'oracle_status': search['oracle_status'], 'sections': sections})
            cohort = service.cohort_evaluation(historical)
            assert cohort['total_students'] == 30
            assert service.search.engine is None
            assert not service.pilot._runners and not service.pilot._predictors
            evidence = {'status': 'PASS', 'inference_and_network_forbidden': True,
                'historical_run': historical['run_id'], 'benchmark_run': source['run_id'],
                'samples': records, 'historical_cohort_students': cohort['total_students'],
                'cohort_metrics': cohort['metrics'],
                'no_model_context_constructed': service.search.engine is None,
                'note': 'AppTest on real immutable snapshots; no separate website/server launched.'}
            audit = Path(PILOT_ROOT) / 'experiments/after_backend_fix/university_validation/audit_20261025'
            audit.mkdir(parents=True, exist_ok=True)
            (audit / 'saved_data_apptest.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf8')
            print(json.dumps({'status': 'PASS', 'samples': records, 'cohort_students': cohort['total_students']}, ensure_ascii=True))
    finally:
        service.search.executor.shutdown(wait=True)
        ui.get_cross_service.clear()


if __name__ == '__main__':
    main()
