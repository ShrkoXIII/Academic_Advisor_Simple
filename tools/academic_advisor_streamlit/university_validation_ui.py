"""Arabic university demonstration inside the existing console; browsing is read-only."""
import pandas as pd
import streamlit as st

from tools.academic_advisor_streamlit.validation_views import csv_bytes, numeric, plan_comparison


SECTIONS = ['📊 Overview', '🎓 Student Validation', '📚 Recommended Plans', '🔎 Search Algorithms',
            '📈 Cohort Evaluation', '🏛️ University Presentation']
LIMITATIONS = ('التنبؤات ليست نتائج فعلية مضمونة. لا نعرف أداء الطالب في الخطط البديلة غير المختارة. '
    'Exhaustive يثبت الأمثلية وفق المودل والقيود المنفذة فقط. صلاحية التسجيل الرسمية ما زالت غير مؤكدة بالكامل، '
    'وإسقاط المعدل التراكمي الرسمي غير مدعوم بموثوقية. ما زالت بعض دلالات توقيت المدخلات التاريخية وعقود البيانات قيد التحقق.')
ACTUAL_COLUMNS = {'course_id': 'رمز المادة', 'course_name': 'المادة', 'course_credits': 'الساعات',
    'course_outcome_status': 'النتيجة المرصودة',
    'actual_mark': 'العلامة الفعلية', 'B_predicted_mark': 'B توقع', 'C_predicted_mark': 'C توقع',
    'B_error': 'B خطأ ±', 'C_error': 'C خطأ ±', 'B_fail_probability': 'B خطر الرسوب',
    'C_fail_probability': 'C خطر الرسوب'}
DETAIL_COLUMNS = {'course_id': 'رمز المادة', 'course_name': 'المادة', 'course_credits': 'الساعات',
    'predicted_mark': 'العلامة المتوقعة', 'expected_grade': 'التقدير', 'expected_points': 'النقاط',
    'fail_probability': 'احتمال الرسوب', 'course_history_effective_support': 'دعم التاريخ',
    'similar_peer_support': 'دعم الأقران C'}


@st.cache_resource(show_spinner=False)
def get_validation_service():
    from tools.academic_advisor_streamlit.validation_service import ValidationService
    return ValidationService()


@st.cache_resource(show_spinner=False)
def get_cross_service():
    from tools.academic_advisor_streamlit.cross_model_service import CrossModelService
    validation = get_validation_service()
    return CrossModelService(validation=validation, root=validation.root)


def _fmt(value, signed=False):
    number = numeric(value)
    return (f'{number:+.3f}' if signed else f'{number:.3f}') if number is not None else 'غير متاح'


def _table(rows, columns=None, error_style=False):
    if not rows:
        st.caption('لا توجد بيانات محفوظة مطابقة لهذا العرض.')
        return
    if columns:
        frame = pd.DataFrame([{label: row.get(key) for key, label in columns.items()} for row in rows])
    else:
        # Callers supply explicit scalar DTOs, never raw API or manifest objects.
        frame = pd.DataFrame(rows)
    if error_style:
        errors = [c for c in frame if 'خطأ' in c]
        frame = frame.style.map(lambda v: 'color: #c84a31' if numeric(v) is not None and float(v) > 0
            else 'color: #1765a8' if numeric(v) is not None and float(v) < 0 else '', subset=errors)
    st.dataframe(frame, hide_index=True, width='stretch')


def _provenance(value):
    value = value or {}
    st.caption('المصدر المحفوظ: ' + str(value.get('run_id') or value.get('source_run') or 'غير متاح') +
               ' | Snapshot: ' + str(value.get('snapshot_id') or 'غير متاح'))
    versions = value.get('model_versions') or {m: a.get('model_version') for m, a in
        (value.get('model_assets') or {}).items() if isinstance(a, dict)}
    if versions:
        st.caption('نسخ المودلات: ' + ' | '.join(str(m) + ': ' + str(v or 'غير محفوظ') for m, v in versions.items()))


def _download(label, rows, filename, key):
    st.download_button(label, csv_bytes(rows), file_name=filename, mime='text/csv', key=key)


def _with_source(rows, provenance, **extra):
    versions = provenance.get('model_versions') or {m: a.get('model_version') for m, a in
        (provenance.get('model_assets') or {}).items() if isinstance(a, dict)}
    return [{**row, 'source_run': provenance.get('run_id'), 'snapshot_id': provenance.get('snapshot_id'),
             'part_id': provenance.get('part_id'), 'model_version': versions.get(row.get('model') or extra.get('model')),
             'B_model_version': versions.get('B'), 'C_model_version': versions.get('C'),
             **extra} for row in rows]


def _credits(preview):
    resolution = preview.get('credit_target_resolution') or {}
    columns = st.columns(3)
    for column, key, title in zip(columns, ('minimum_credits', 'maximum_credits', 'target_credits'),
            ('الحد الأدنى API', 'الحد الأعلى API', 'هدف الساعات الدقيق · API')):
        column.metric(title, _fmt(resolution.get(key)))
    st.caption('مصدر الهدف: ' + str(resolution.get('target_credits_source') or 'UNRESOLVED') +
        ' | الهدف الحالي من اللقطة؛ أهداف التشغيلات التاريخية تُعرض بقيمها الأصلية. لا تخفيض تلقائي للساعات.')
    if resolution.get('status') != 'RESOLVED':
        st.warning('API_TARGET_UNRESOLVED — ' + str(resolution.get('reason') or preview.get('reason') or 'SAVED_LIMITS_UNAVAILABLE'))


def _actual(view, models, *, presentation=False):
    summary = view.get('actual_summary') or {}
    st.subheader('النتيجة الفعلية مقابل توقع الخطة الفعلية')
    _provenance(view.get('provenance'))
    metrics = st.columns(1 + len(models))
    metrics[0].metric('Actual Semester GPA · معدل فصلي محسوب', _fmt(summary.get('descriptive_gpa')))
    for column, model in zip(metrics[1:], models):
        values = (summary.get('models') or {}).get(model) or {}
        column.metric(f'{model} · Predicted Actual-Plan GPA', _fmt(values.get('predicted_actual_plan_gpa')))
        column.caption('الخطأ الموقّع: ' + _fmt(values.get('actual_plan_gpa_error'), True) +
                       ' | الخطأ المطلق: ' + _fmt(values.get('actual_plan_gpa_absolute_error')))
    st.caption('GPA الفعلي محسوب بوزن الساعات من نقاط النتائج المرصودة المعتمدة في المصدر؛ ليس معدلًا رسميًا مؤكدًا. '
               'الخطأ = التوقع − الفعلي. هذه التنبؤات مستقلة عن خوارزمية البحث، ولا يُحسب معدل تراكمي رسمي.')
    if summary.get('descriptive_gpa') is None:
        st.warning('ACTUAL_GPA_UNAVAILABLE — ' + str(summary.get('descriptive_gpa_reason') or 'COMPLETE_RESULTS_UNAVAILABLE'))
        if summary.get('partial_graded_gpa') is not None:
            st.caption('معدل جزئي للمواد ذات النتائج فقط: ' + _fmt(summary['partial_graded_gpa']))
    courses = view.get('actual_course_rows') or []
    model = models[0] if models else 'B'
    filtered = courses
    if not presentation:
        left, right = st.columns(2)
        mode = left.selectbox('تصفية مقارنة المواد', ['جميع المواد', 'أكبر أخطاء التنبؤ', 'توقع أعلى من الفعلي',
            'توقع أدنى من الفعلي', 'مواد رسب فيها الطالب'], key='university_actual_filter')
        model = right.selectbox('مودل تصفية الخطأ', models or ['B', 'C'], key='university_error_model')
        if mode == 'أكبر أخطاء التنبؤ':
            filtered = sorted((r for r in courses if numeric(r.get(model + '_error')) is not None),
                              key=lambda r: -abs(float(r[model + '_error'])))[:5]
        elif mode in ('توقع أعلى من الفعلي', 'توقع أدنى من الفعلي'):
            sign = 1 if mode == 'توقع أعلى من الفعلي' else -1
            filtered = [r for r in courses if numeric(r.get(model + '_error')) is not None and sign * float(r[model + '_error']) > 0]
        elif mode == 'مواد رسب فيها الطالب':
            filtered = [r for r in courses if r.get('course_outcome_status') == 'fail']
    columns = {k: v for k, v in ACTUAL_COLUMNS.items()
               if not k.startswith(('B_', 'C_')) or k[0] in models}
    _table(filtered, columns, error_style=True)
    if courses:
        chart = pd.DataFrame([{**{'المادة': str(c.get('course_name') or c.get('course_id')),
                                  'الفعلي': numeric(c.get('actual_mark'))},
                    **{m: numeric(c.get(m + '_predicted_mark')) for m in models}} for c in filtered])
        if not chart.empty:
            st.bar_chart(chart.set_index('المادة'), stack=False)
    _download('تنزيل أخطاء مواد الطالب', _with_source(courses, view.get('provenance') or {}, sample_id=view.get('sample_id')),
              'student_course_errors.csv', 'university_student_errors_download')


def _matrix(plans, labels, key, *, shared_predictions=False):
    result = plan_comparison(plans, labels)
    if not plans:
        st.caption('PLANS_UNAVAILABLE — لا تتوفر خطط كافية للمقارنة.')
        return
    if result['near_identical']:
        st.info('البدائل متشابهة جدًا: Jaccard بين كل زوج ≥ 0.8. هذا وصف للتشابه، ولا يغير ترتيب GPA.')
    only = st.checkbox('عرض الاختلافات فقط', key=key + '_differences')
    matrix = [r for r in result['matrix'] if not only or not r['shared_by_all']]
    st.caption('مشتركة بين جميع الخطط: ' + (', '.join(result['common_ids']) or 'لا توجد'))
    columns = {'course_id': 'رمز المادة', 'course_name': 'المادة', 'shared_by_all': 'مشتركة بالكامل',
               **{label: label for label in labels}}
    _table(matrix, columns)
    _table(result['pairs'], {'first': 'الخطة الأولى', 'second': 'الخطة الثانية', 'jaccard': 'Jaccard',
        'shared_course_count': 'مواد مشتركة', 'gpa_difference_second_minus_first': 'فرق GPA (الثانية−الأولى)',
        'failed_credits_difference_second_minus_first': 'فرق ساعات الرسوب المتوقعة', 'max_risk_difference_second_minus_first': 'فرق أعلى خطر',
        'first_credits': 'ساعات الأولى', 'second_credits': 'ساعات الثانية', 'identical_gpa': 'نفس GPA',
        'identical_course_set': 'نفس المواد', 'removed_from_first': 'تخرج من الأولى', 'added_in_second': 'تضاف في الثانية'})
    _table([{'الخطة': label, 'مواد حصرية': ', '.join(ids) or 'لا توجد'} for label, ids in result['unique_ids'].items()])
    if shared_predictions:
        with st.expander('فروق التنبؤ والمخاطر للمواد المشتركة'):
            _table(result['shared_predictions'], {'first': 'الأولى', 'second': 'الثانية', 'course_id': 'المادة',
                'first_predicted_mark': 'توقع الأولى', 'second_predicted_mark': 'توقع الثانية',
                'predicted_mark_difference_second_minus_first': 'فرق التوقع',
                'first_fail_probability': 'خطر الأولى', 'second_fail_probability': 'خطر الثانية'})


def _plan_cards(experiments, models, actual_ids):
    columns = st.columns(max(1, len(models)))
    for column, model in zip(columns, models):
        with column:
            st.subheader('Model ' + model)
            experiment = experiments.get(model) or {}
            st.caption('Strategy: ' + str(experiment.get('strategy', 'UNVERIFIED')) +
                ' | Budget: ' + str(experiment.get('budget', 'UNAVAILABLE')) + ' | Scope: ' + str(experiment.get('scope', 'UNAVAILABLE')))
            plans = experiment.get('top_plans') or []
            if not plans:
                st.info(str(experiment.get('status') or 'NO_SAVED_PLANS') + ' — ' + str(experiment.get('reason') or 'NO_MATCHING_PLAN'))
            for position, plan in enumerate(plans[:3], 1):
                st.markdown(f'**Top {position} · GPA {_fmt(plan.get("expected_plan_gpa"))}**')
                ids = {str(c['course_id']) for c in plan.get('courses', [])}
                overlap = sorted(ids & actual_ids) if actual_ids is not None else None
                a, b = st.columns(2)
                a.metric('إجمالي الساعات / الهدف', f'{_fmt(plan.get("total_credits"))} / {_fmt(experiment.get("target_credits"))}')
                b.metric('عدد المواد', len(ids))
                a.caption('ساعات الرسوب المتوقعة: ' + _fmt(plan.get('expected_failed_credits')))
                b.caption('أعلى احتمال رسوب: ' + _fmt((plan.get('plan_difficulty_balance') or {}).get('max_fail_probability')))
                st.caption('التقاطع مع الفعلي: ' + (str(len(overlap)) + ' [' + ', '.join(overlap) + ']' if overlap is not None else 'غير متاح') +
                           ' — تقاطع تاريخي، وليس دليل جودة توصية.')
                st.caption('PROVISIONAL — صلاحية التسجيل الرسمية غير مؤكدة. الهوية: ' + str(plan.get('canonical_id') or 'محسوبة من مجموعة المواد'))
                with st.expander(f'{model} · Top {position} · تفاصيل المواد'):
                    _table(plan.get('courses') or [], {k: v for k, v in DETAIL_COLUMNS.items()
                        if k != 'similar_peer_support' or model == 'C'})


def _cross_evaluation(selection, recommendation):
    with st.expander('تقييم الخطة نفسها بالمودلين — تجربة مستقلة صريحة'):
        st.caption('تقييم Top 1 المختارة من B وC بكلا المودلين. لا تعد قراءة النتائج تشغيلًا، ولا يعني أعلى GPA أن المودل أفضل فعليًا.')
        if selection['source_ref'].get('kind') != 'benchmark':
            st.info('CROSS_MODEL_UNAVAILABLE — يتطلب مصدر Search Benchmark متوافقًا بمواد API الأصلية.')
            return
        # Construction and saved reads never load model contexts.
        service = get_cross_service()
        valid = recommendation.get('status') == 'AVAILABLE'
        if not valid:
            st.info('CROSS_MODEL_UNAVAILABLE — لا توجد نتيجة مصدر مطابقة لهذا السياق؛ لا تُعرض نتائج تجربة أخرى.')
            return
        if st.button('تشغيل تقييم مشترك للمودلين وحفظه', key='university_cross_run', disabled=not valid):
            run_id = service.start(selection['sample_id'], snapshot_id=selection['snapshot_id'],
                source_ref=selection['source_ref'], strategy=selection['strategy'], budget=selection['budget'],
                scope=selection['scope'], target_credits=selection['target_credits'])
            st.session_state['university_cross_active'] = run_id
        active = st.session_state.get('university_cross_active')
        if active:
            progress = service.progress(active)
            st.caption(str(active) + ' | ' + str(progress.get('status')))
            if progress.get('reason'):
                st.warning(str(progress['reason']))
            st.button('تحديث التقييم المشترك', key='university_cross_refresh')
        runs = service.list_runs()
        # Only relevant sample/source selections are offered, never another student's job.
        compatible_runs = []
        for row in runs:
            if row.get('sample_id') != selection['sample_id'] or any(row.get(key) != selection[key]
                    for key in ('strategy', 'budget', 'scope', 'target_credits')):
                continue
            manifest = service.load_run(row['run_id'])['run_manifest']
            if manifest.get('source_ref', {}).get('run_id') == selection['source_ref']['run_id']:
                compatible_runs.append(row)
        runs = compatible_runs
        if runs:
            chosen = st.selectbox('تقييم مشترك محفوظ', [r['run_id'] for r in runs], key='university_cross_saved')
            saved = service.load_run(chosen)
            st.caption('تجربة مشتركة محفوظة مستقلة: ' + chosen + ' | ' + str(saved.get('status')))
            if saved.get('reason'):
                st.warning(str(saved['reason']))
            _table(saved.get('rows') or [], {'source_model': 'خطة مختارة بواسطة', 'scoring_model': 'مودل التقييم',
                'canonical_id': 'هوية مجموعة المواد', 'expected_plan_gpa': 'GPA المتوقع',
                'expected_failed_credits': 'ساعات الرسوب المتوقعة', 'max_fail_probability': 'أعلى خطر'})


def _recommended(service, selection, actual, models, *, presentation=False):
    recommendation = service.recommendations(selection['sample_id'], snapshot_id=selection['snapshot_id'],
        source_ref=selection['source_ref'], strategy=selection['strategy'], budget=selection['budget'],
        scope=selection['scope'], target_credits=selection['target_credits'], allow_historical=selection['legacy'])
    st.subheader('خطط بديلة افتراضية · B / C')
    _provenance(recommendation.get('provenance'))
    if hasattr(service, 'source_compatibility'):
        compatibility = service.source_compatibility(selection['sample_id'], snapshot_id=selection['snapshot_id'],
            historical_ref=selection['historical_ref'], source_ref=selection['source_ref'])
        if compatibility.get('status') != 'COMPATIBLE':
            st.warning('سياقات مستقلة: ' + ' | '.join(compatibility.get('issues') or []) +
                ' | هدف التشغيل التاريخي: ' + _fmt(compatibility.get('historical_target_credits')) +
                ' | هدف المصدر البديل: ' + _fmt(compatibility.get('source_target_credits')) +
                '. لا تُحسب فجوة Oracle عبر هدفين مختلفين؛ تبقى التنبؤات الفعلية في مصدرها الأصلي.')
    if not recommendation.get('models'):
        st.info('No saved results for this configuration')
        st.caption(str(recommendation.get('reason') or 'EXACT_SAVED_CONFIGURATION_UNAVAILABLE'))
    if recommendation.get('status') == 'AVAILABLE_LEGACY':
        st.warning('تشغيل تاريخي بإعداداته الأصلية — لم يُعد تصنيفه Smart Search. الهدف والميزانية أدناه من التشغيل المحفوظ.')
    actual_rows = actual.get('actual_course_rows') or []
    actual_ids = {str(c['course_id']) for c in actual_rows} if actual_rows else None
    experiments = recommendation.get('models') or {}
    _plan_cards(experiments, models, actual_ids)
    for model in models:
        plans = (experiments.get(model) or {}).get('top_plans') or []
        if plans:
            with st.expander(f'{model} · مقارنة Top 1 / Top 2 / Top 3', expanded=False):
                _matrix(plans[:3], [f'{model} Top {i + 1}' for i in range(min(3, len(plans)))], 'university_' + model)
    if {'B', 'C'}.issubset(models) and all((experiments.get(m) or {}).get('top_plans') for m in ('B', 'C')):
        st.markdown('**B مقابل C — اختلاف المواد والتوقعات**')
        left, right = st.columns(2)
        b = left.selectbox('خطة B للمقارنة', list(range(len(experiments['B']['top_plans']))),
            format_func=lambda i: f'B Top {i + 1}', key='university_b_plan')
        c = right.selectbox('خطة C للمقارنة', list(range(len(experiments['C']['top_plans']))),
            format_func=lambda i: f'C Top {i + 1}', key='university_c_plan')
        _matrix([experiments['B']['top_plans'][b], experiments['C']['top_plans'][c]],
            [f'B Top {b + 1}', f'C Top {c + 1}'], 'university_bc', shared_predictions=True)
        st.info('ارتفاع GPA المتوقع من C لا يثبت أن خطته أفضل فعليًا؛ للمقارنة المضبوطة تُقيّم مجموعة المواد نفسها بالمودلين.')
        if not presentation:
            _cross_evaluation(selection, recommendation)
    return recommendation


def _search(service, selection, models, *, presentation=False):
    st.subheader('مقارنة خوارزميات البحث ومجموعات المواد')
    source = selection['source_ref']
    if source.get('kind') != 'benchmark':
        st.warning('ORACLE_UNAVAILABLE — اختر مصدر Search Benchmark؛ نتائج Pilot التاريخية مستقلة عن oracle.')
        return []
    model = models[0] if presentation else st.selectbox('مودل مقارنة البحث', models or ['B', 'C'], key='university_search_model')
    comparison = service.search_comparison(selection['sample_id'], snapshot_id=selection['snapshot_id'],
        run_id=source['run_id'], model=model, budget=selection['budget'], scope=selection['scope'],
        target_credits=selection['target_credits'])
    _provenance(comparison.get('provenance'))
    if comparison.get('oracle_status') != 'EXHAUSTIVE_COMPLETE':
        st.warning('ORACLE_UNAVAILABLE — لم يكتمل تحقق exhaustive المتوافق لهذا الطالب والمودل؛ لا توجد دعوى أفضلية عالمية.')
    _table(comparison.get('rows') or [], {'strategy': 'Strategy', 'budget': 'Budget', 'best_gpa': 'Best GPA',
        'oracle_gpa': 'Oracle GPA', 'gpa_gap': 'GPA Gap', 'top3_recall': 'Exact Top-3 Recall',
        'score_equivalent_top3_recall': 'Score-equivalent Recall',
        'standalone_runtime_seconds': 'Runtime s', 'evaluated_plans': 'Evaluated Plans',
        'candidate_exploration_coverage': 'Coverage', 'status': 'Status'})
    rows = comparison.get('rows') or []
    if rows:
        data = pd.DataFrame([{'Strategy': r.get('strategy'), 'Best GPA': r.get('best_gpa')} for r in rows])
        st.bar_chart(data.set_index('Strategy'))
    strategies = comparison.get('plans_by_strategy') or {}
    labels, first_plans = [], []
    for strategy, plans in strategies.items():
        if strategy == 'EXHAUSTIVE':
            continue  # The dedicated oracle section retains its unbudgeted scope.
        if plans and strategy != 'EXHAUSTIVE':
            first_plans.append(plans[0])
            labels.append(strategy)
        with st.expander(model + ' · ' + strategy + ' · أفضل ثلاث خطط'):
            _plan_cards({model: {'top_plans': plans, 'strategy': strategy, 'scope': selection['scope'],
                'budget': selection['budget'], 'target_credits': selection['target_credits']}}, [model], None)
    if first_plans:
        st.markdown('**Top 1 بين الاستراتيجيات — المواد المشتركة والاستبدالات**')
        _matrix(first_plans, labels, 'university_strategies', shared_predictions=True)
    oracle = {**(comparison.get('oracle_summary') or {}),
              'top_plans': strategies.get('EXHAUSTIVE') or (comparison.get('oracle_summary') or {}).get('top_plans') or []}
    if comparison.get('oracle_status') == 'EXHAUSTIVE_COMPLETE' and oracle.get('top_plans'):
        st.caption('EXHAUSTIVE_COMPLETE | حجم الفضاء: ' + str(oracle.get('feasible_plan_count', oracle.get('evaluated_plans'))) +
            ' | عدد الخطط ذات أفضل GPA متعادل: ' + str(oracle.get('tied_optimal_count', 'غير محفوظ')))
        with st.expander('أفضل ثلاث خطط Oracle المكتملة — ' + model):
            _plan_cards({model: {**oracle, 'strategy': 'EXHAUSTIVE', 'scope': 'EXHAUSTIVE',
                'budget': None, 'target_credits': selection['target_credits']}}, [model], None)
        if first_plans:
            _matrix([*first_plans, oracle['top_plans'][0]], [*labels, 'EXHAUSTIVE'], 'university_oracle')
        _table(oracle.get('ordinal_ranks') or [], {'strategy': 'الطريقة', 'rank': 'Top',
            'oracle_rank': 'الرتبة ضمن Oracle', 'canonical_id': 'هوية الخطة'})
    _download('تنزيل مقارنة البحث', _with_source(rows, comparison.get('provenance') or {},
        sample_id=selection['sample_id'], model=model), 'search_comparison.csv', 'university_search_download')
    return rows


def _cohort(service, selection, models):
    st.subheader('تقييم المجموعة التاريخية · مستقل عن benchmark الخمسة')
    left, middle, right = st.columns(3)
    samples = left.multiselect('تصفية الطلاب', [r['sample_id'] for r in service.cohort()], key='university_cohort_students')
    statuses = middle.multiselect('حالة التوصية التاريخية', ['PREDICTION_AVAILABLE', 'BLOCKED', 'NO_MATCHING_PLAN'], key='university_cohort_status')
    category = right.selectbox('فئة GPA البداية الموثقة', [None, 'below_2', 'at_least_2', 'unavailable'],
        format_func=lambda x: {None: 'الجميع', 'below_2': 'أقل من 2', 'at_least_2': '2 فأعلى', 'unavailable': 'غير متاح'}[x], key='university_cohort_starting')
    range_enabled = st.checkbox('تصفية بحسب GPA الفصل الفعلي اللاحق', key='university_cohort_gpa_filter')
    actual_range = st.slider('مجال GPA الفعلي للفصل', min_value=0., max_value=4., value=(0., 4.), step=.1,
        key='university_cohort_actual_range') if range_enabled else None
    report = service.cohort_evaluation(selection['historical_ref'], snapshot_id=selection['snapshot_id'],
        sample_ids=samples or None, models=models, statuses=statuses or None,
        starting_category=category, actual_gpa_range=actual_range)
    _provenance(report.get('provenance'))
    st.caption('عدد الطلاب في هذا المصدر التاريخي: ' + str(report.get('total_students', 0)) +
        '. لا تدمج هذه الأعداد مع Oracles الخمسة. كل مؤشر يعرض مقامه من الطلاب والملاحظات الصالحة.')
    _table(report.get('metrics') or [], {'model': 'المودل', 'metric': 'المؤشر', 'value': 'القيمة',
        'student_count': 'عدد الطلاب', 'course_observations': 'ملاحظات المواد'})
    students, courses, plans = (report.get(key) or [] for key in ('students', 'courses', 'plans'))
    if students:
        _table(students, {'sample_id': 'الطالب', 'model': 'المودل', 'status': 'حالة التوصية',
            'actual_plan_gpa': 'GPA فعلي', 'predicted_actual_plan_gpa': 'GPA الخطة الفعلية المتوقع',
            'actual_plan_gpa_error': 'خطأ GPA', 'candidate_count': 'المرشحون', 'runtime_seconds': 'زمن محفوظ s'})
    if courses:
        errors = pd.DataFrame([{'المودل': r.get('model'), 'خطأ العلامة': r.get('error')} for r in courses]).dropna()
        if not errors.empty:
            st.bar_chart(errors.groupby('المودل').mean())
    if students:
        distribution = pd.DataFrame([{'الطالب / المودل': str(s.get('sample_id')) + ' / ' + str(s.get('model')),
            'GPA الخطة الفعلية المتوقع': s.get('predicted_actual_plan_gpa'),
            'GPA الفعلي': s.get('actual_plan_gpa')} for s in students])
        st.caption('توزيع GPA الفعلي والمتوقع للخطة الفعلية حسب الطالب؛ لا يمثل توقع خطط بديلة.')
        st.bar_chart(distribution.set_index('الطالب / المودل'), stack=False)
    if plans:
        risk = pd.DataFrame([{'الخطة': str(p.get('sample_id')) + ' / ' + str(p.get('model')) + ' / ' + str(p.get('rank')),
            'GPA بديل متوقع': p.get('expected_plan_gpa'), 'ساعات رسوب متوقعة': p.get('expected_failed_credits')}
            for p in plans])
        st.caption('توزيع توقعات الخطط البديلة والمخاطر؛ مقاييس وصفية منفصلة عن الخطط الفعلية.')
        st.bar_chart(risk.set_index('الخطة'), stack=False)
        report['plans'] = [{**p, 'course_ids': ', '.join(str(c['course_id']) for c in p.get('courses', [])),
            'max_fail_probability': (p.get('plan_difficulty_balance') or {}).get('max_fail_probability')}
            for p in plans]
    for source_key, label, filename in [('metrics', 'تنزيل مؤشرات المجموعة', 'cohort_metrics.csv'),
            ('students', 'تنزيل أخطاء الطلاب', 'student_errors.csv'), ('courses', 'تنزيل أخطاء المواد', 'course_errors.csv'),
            ('plans', 'تنزيل مقارنة أفضل ثلاث خطط', 'top3_comparison.csv')]:
        _download(label, _with_source(report.get(source_key) or [], report.get('provenance') or {}), filename, 'university_download_' + source_key)
    source = selection['source_ref']
    rows = []
    if source.get('kind') == 'benchmark':
        for model in models:
            comparison = service.search_comparison(selection['sample_id'], snapshot_id=selection['snapshot_id'],
                run_id=source['run_id'], model=model, budget=selection['budget'], scope=selection['scope'],
                target_credits=selection['target_credits'])
            rows += _with_source(comparison.get('rows') or [], comparison.get('provenance') or {},
                                 sample_id=selection['sample_id'], model=model)
    _download('تنزيل مقارنة benchmark المختارة — منفصلة عن المجموعة', rows,
              'selected_search_comparison.csv', 'university_download_search')


def _execution(service, selection, preview, models):
    resolution = preview.get('credit_target_resolution') or {}
    disabled = selection['snapshot_id'] != 'after_backend_fix' or resolution.get('status') != 'RESOLVED' or not models
    st.caption('تشغيل جديد على اللقطة المحفوظة، باستراتيجية واحدة ولكلا المودلين؛ لا يُشغّل Exhaustive تلقائيًا.')
    with st.expander('حدود التشغيل الجديد'):
        seconds = st.number_input('الحد الزمني بالثواني', min_value=1, value=300, key='university_seconds')
        states = st.number_input('حد حالات البحث', min_value=1, value=2000000, key='university_states')
        seed = st.number_input('البذرة', min_value=0, value=42, key='university_seed')
    active = st.session_state.get('university_active_run')
    if active:
        progress = service.search.progress(active)
        st.caption('التشغيل النشط: ' + active + ' | ' + str(progress.get('status')))
        st.progress(min(1., (progress.get('completed') or 0) / max(1, progress.get('total') or 1)))
        disabled = disabled or progress.get('status') == 'running'
        st.button('تحديث تقدم التجربة', key='university_refresh')
    if st.button('تشغيل تجربة جديدة وحفظها', key='university_run', disabled=disabled):
        run_id = service.search.start([selection['sample_id']], models=['B', 'C'],
            strategies=[selection['strategy']], budgets=[selection['budget']], scopes=[selection['scope']],
            seed=int(seed), limits={'max_seconds': float(seconds), 'max_space_states': int(states)})
        st.session_state['university_active_run'] = run_id
        st.success('بدأت التجربة: ' + run_id + '. اختر تشغيلها المحفوظ بعد الاكتمال؛ لا تُنسب نتائج المصدر القديم إليها.')


def _goto_search():
    st.session_state['university_section'] = '🔎 Search Algorithms'


def render_validation():
    """One student selection, six read-only views and explicit experiment actions."""
    st.markdown('<style>[data-testid="stAppViewContainer"] .stMarkdown p, [data-testid="stAppViewContainer"] h2, '
        '[data-testid="stAppViewContainer"] h3 {direction:rtl;text-align:right;} '
        '[data-testid="stDataFrame"] {font-size:0.9rem;}</style>', unsafe_allow_html=True)
    st.title('🎓 منصة التحقق الأكاديمي والعرض الجامعي')
    st.caption('بيانات محفوظة محليًا · هويات عينة مستعارة · لا اتصال حي أو توقع تلقائي عند التصفح')
    try:
        service = get_validation_service()
        left, right = st.columns(2)
        snapshot = left.selectbox('اللقطة المشتركة', ['after_backend_fix', 'before_backend_fix'], key='university_snapshot')
        samples = [r['sample_id'] for r in service.cohort()]
        if not samples:
            st.warning('SAVED_COHORT_UNAVAILABLE')
            return
        sample = right.selectbox('الطالب المشترك · Sample ID', samples, key='university_student')
        catalog = service.catalog(snapshot)
        history = {r['key']: r for r in catalog.get('historical') or []}
        sources = {r['key']: {**r, 'kind': 'benchmark'} for r in catalog.get('benchmark') or []}
        sources.update({key: {**row, 'kind': 'historical'} for key, row in history.items()})
        if not history or not sources:
            st.info('No saved results for this configuration')
            return
        with st.expander('المصادر والإعدادات المشتركة', expanded=False):
            historical_key = st.selectbox('مصدر التنبؤات التاريخية المستقلة', list(history),
                format_func=lambda key: history[key]['run_id'] + f" | {history[key].get('student_count', '?')} طالب", key='university_history_run')
            source_key = st.selectbox('مصدر التوصيات / benchmark', list(sources),
                format_func=lambda key: sources[key]['run_id'] + ' | ' + sources[key]['kind'], key='university_source_run')
            a, b, c = st.columns(3)
            strategy = a.selectbox('الخوارزمية التجريبية', ['SMART_SEARCH', 'FIRST_N', 'DIVERSE_N'], key='university_strategy')
            budget = b.selectbox('ميزانية الخطط الكاملة', [200, 1000, 2000], index=1, key='university_budget')
            scope = c.selectbox('نطاق التجربة', ['FULL_SPACE', 'FIXED_POOL'], key='university_scope')
            models = st.multiselect('المودلات المعروضة', ['B', 'C'], default=['B', 'C'], key='university_models')
            legacy = st.checkbox('عرض التشغيل التاريخي بإعداداته الأصلية صراحةً', key='university_legacy',
                                 disabled=sources[source_key]['kind'] != 'historical')
        historical_ref = {'run_id': history[historical_key]['run_id'], 'family': history[historical_key].get('family', 'comparison')}
        source_ref = {k: sources[source_key][k] for k in ('kind', 'run_id', 'family') if k in sources[source_key]}
        preview = service.preview(sample, snapshot)
        target = (preview.get('credit_target_resolution') or {}).get('target_credits')
        selection = dict(sample_id=sample, snapshot_id=snapshot, historical_ref=historical_ref, source_ref=source_ref,
                         strategy=strategy, budget=budget, scope=scope, target_credits=target,
                         legacy=bool(legacy and source_ref['kind'] == 'historical'))
        section = st.radio('أقسام المنصة', SECTIONS, horizontal=True, key='university_section')
        if not models:
            st.info('اختر مودلًا واحدًا على الأقل لعرض النتائج.')
            return
        st.caption(f'{sample} | Semester: {preview.get("part_id", "UNAVAILABLE")} | Requested: {strategy} / {budget} / {scope} '
                   '| Experimental default; لا اعتماد Production')
        actual = service.student(sample, snapshot_id=snapshot, historical_ref=historical_ref)
        if section == '📊 Overview':
            _credits(preview)
            _provenance(actual.get('provenance'))
            st.markdown('اختر الطالب مرة واحدة، ثم راجع النتائج الفعلية والتنبؤات والخطط البديلة وخوارزميات البحث. '
                        'المجموعة التاريخية تضم ثلاثين طالبًا؛ إثباتات البحث الشامل تخص الطلاب الذين اكتمل لهم Oracle فقط.')
            st.metric('حالة التوصية في المصدر التاريخي', str(actual.get('recommendation_status', 'UNAVAILABLE')))
            st.info('توقع الخطة الفعلية مستقل عن البحث. الخطط البديلة افتراضية ولا توجد نتائج مرصودة لها.')
            st.button('🔍 Compare Search Algorithms', on_click=_goto_search, key='university_compare_search')
        elif section == '🎓 Student Validation':
            summary = actual.get('student_summary') or preview.get('student_summary') or {}
            _credits(preview)
            a, b, c = st.columns(3)
            a.metric('GPA البداية · المصدر المحفوظ', _fmt(summary.get('previous_gpa')))
            b.metric('المواد المسجلة فعليًا', (actual.get('actual_summary') or {}).get('actual_course_count') or 'غير متاح')
            c.metric('الساعات المسجلة فعليًا', _fmt((actual.get('actual_summary') or {}).get('total_credits')))
            st.caption('مصدر GPA البداية: ' + str(summary.get('source') or 'UNVERIFIED') +
                ' | الصفر قيمة مصدرية ولا يدل وحده على أن الطالب مستجد. حالة التوصية: ' + str(actual.get('recommendation_status')))
            _actual(actual, models)
            with st.expander('جودة البيانات والقيود'):
                _table([{'القيد': str(issue)} for issue in [*(actual.get('issues') or []), *(preview.get('issues') or [])]])
        elif section == '📚 Recommended Plans':
            _credits(preview)
            _recommended(service, selection, actual, models)
            st.button('🔍 Compare Search Algorithms', on_click=_goto_search, key='university_compare_search')
            _execution(service, selection, preview, models)
        elif section == '🔎 Search Algorithms':
            _search(service, selection, models)
            _execution(service, selection, preview, models)
            st.caption('للإعدادات المتقدمة أو تشغيل Oracle محدود الموارد صراحةً، استخدم وضع 🔎 Search Benchmark الحالي من أعلى التطبيق.')
        elif section == '📈 Cohort Evaluation':
            _cohort(service, selection, models)
        else:
            st.subheader('1 · الطالب قبل التسجيل')
            st.caption(sample + ' | Semester: ' + str(preview.get('part_id', 'غير متاح')))
            summary = actual.get('student_summary') or {}
            st.metric('GPA البداية من المصدر', _fmt(summary.get('previous_gpa')))
            _credits(preview)
            st.caption('حالة التوصية التاريخية: ' + str(actual.get('recommendation_status', 'UNAVAILABLE')))
            if actual.get('recommendation_status') in ('BLOCKED', 'NO_MATCHING_PLAN'):
                st.warning('قيود الطالب المحفوظة: ' + ' | '.join(str(i) for i in actual.get('issues') or ['SAVED_RECOMMENDATION_UNAVAILABLE']))
            st.subheader('2 · المواد التي اختارها الطالب فعلًا ونتائجها')
            _table(actual.get('actual_course_rows') or [], {'course_name': 'المادة', 'course_credits': 'الساعات', 'actual_mark': 'العلامة الفعلية'})
            st.subheader('3 · ما توقعه المودلان للخطة نفسها')
            _actual(actual, models, presentation=True)
            st.caption('قد تختلف التوقعات لأن B وC يستخدمان عقود ميزات مختلفة؛ C يتضمن إشارات أقران على مستوى المادة. هذا لا يثبت تفوقه.')
            st.subheader('4 · ما يوصي به النظام ضمن الإعداد المختار فعليًا')
            _recommended(service, selection, actual, models, presentation=True)
            _execution(service, selection, preview, models)
            st.subheader('5 · تحقق خوارزمية البحث مقابل Oracle')
            _search(service, selection, models, presentation=True)
            st.subheader('6 · ما أثبتناه وما لم نثبته')
            st.info(LIMITATIONS)
    except (OSError, ValueError, KeyError, RuntimeError, ImportError):
        st.error('SAVED_VALIDATION_DATA_UNAVAILABLE — تعذر عرض مصدر محفوظ متوافق؛ راجع اختيار اللقطة والتشغيل. لا تُعرض تفاصيل أو هويات شخصية.')
