"""Render explanations using only quoted production code and measured values."""
from html import escape
from pathlib import Path
import inspect
import json
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.recommendation import AcademicPlanRecommender, enumerate_plan_indices, summarize_scored_plans, rank_plans
from src.recommendation_inputs import normalize_candidates, build_student_snapshot, load_local_inputs
from src.features.temporal_features import (CourseHistoryState, temporal_weight, compute_plan_context_features,
                                  add_student_history_features, COURSE_HISTORY_COLUMNS, PLAN_CONTEXT_COLUMNS)
from src.experiments.specialty_history import _finish_specialty_history, SPECIALTY_HISTORY_FEATURES


def fmt(value):
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return '—'
    if isinstance(value, (float, np.floating)):
        return f'{value:.8f}'.rstrip('0').rstrip('.')
    return str(value)


def p(text):
    return '<p>' + text + '</p>'


def formula(text):
    return '<div class="formula" dir="ltr">' + escape(text) + '</div>'


def table(rows, columns=None):
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    if columns:
        frame = frame[list(columns)].rename(columns=columns)
    if frame.empty:
        return p('لا توجد صفوف.')
    return '<div class="table-wrap">' + frame.to_html(index=False, border=0, escape=True, na_rep='—',
        float_format=fmt) + '</div>'


def code(fn, first=None, last=None, before=None):
    lines, start = inspect.getsourcelines(fn)
    left = next(i for i, line in enumerate(lines) if first in line) if first else 0
    right = next(i for i in range(left, len(lines)) if last in lines[i]) + 1 if last else len(lines)
    if before:
        right = next(i for i in range(left, len(lines)) if before in lines[i])
    excerpt = ''.join(f'{start + i:>3}  {lines[i]}' for i in range(left, right))
    path = Path(inspect.getfile(fn)).resolve()
    CODE_SOURCES.add(str(path))
    return '<div class="source"><div class="source-label">' + escape(fn.__qualname__) + \
        f' · {escape(str(path.relative_to(ROOT)))} · السطور {start+left}–{start+right-1}</div>' + \
        '<pre dir="ltr"><code>' + escape(excerpt) + '</code></pre></div>'


SNAPSHOT = {
    'gpa_prev_1': 'معدل آخر فصل مسجل قبل الفصل المطلوب؛ نتيجة فعلية سابقة وليست توقعاً.',
    'gpa_prev_2': 'معدل الفصل المسجل الذي يسبق gpa_prev_1.',
    'gpa_trend_delta': 'الفرق gpa_prev_1 − gpa_prev_2؛ موجب يعني ارتفاع المعدل السابق.',
    'gpa_trend_missing': '1 إن تعذر حساب فرق المعدلين، وإلا 0.',
    'start_agpa_points': 'المعدل التراكمي عند بداية الفصل؛ وهو أيضاً عتبة قبول الخطط هنا.',
    'start_total_in_courses': 'رصيد المقررات المحتسبة عند بداية الفصل من حالة الطالب.',
    'start_total_in_credits': 'رصيد الساعات المحتسبة عند بداية الفصل من حالة الطالب.',
    'prior_total_reg_courses': 'total_reg_courses في صف حالة الفصل؛ يمثل مجموع التسجيلات قبل الفصل.',
    'prior_total_reg_credits': 'total_reg_credits في صف الحالة؛ مجموع ساعات التسجيل السابقة.',
    'prior_total_fail_courses': 'total_fail_courses قبل الفصل؛ لا نضيف رسوب الفصل الجاري.',
    'prior_total_fail_credits': 'total_fail_credits قبل الفصل.',
    'prior_fail_credit_ratio': 'prior_total_fail_credits ÷ prior_total_reg_credits.',
    'prior_registered_semesters': 'reg_total_semesters من صف الفصل السابق ضمن نفس الاختصاص.',
    'observed_gap_semesters': 'عدد فصول الانقطاع المتتالية المرصودة قبل العودة إلى التسجيل.',
    'diploma_gpa': 'معدل الشهادة السابقة للجامعة من student_diploma.parquet.',
    'diploma_type_id': 'نوع الشهادة السابقة؛ قيمة تصنيفية.',
    'grade_version_id': 'معرّف سلم العلامات المعتمد للطالب؛ قيمة تصنيفية.',
    'degree_credits_count': 'ساعات الاختصاص من حالة الطالب.'}
STATIC = {
    'course_credits': 'ساعات المادة من ملف الطلب، بعد مطابقتها مع منهاج الاختصاص.',
    'attempt_number': 'أكبر attempt_number سابق لهذه المادة عند الطالب + 1؛ دون نتائج الفصل المطلوب.',
    'plan_course_type_id': 'معرّف نوع المادة من صف degree_id + course_id في المنهاج.',
    'plan_requirement_type_id': 'معرّف نوع المتطلب من المنهاج، وليس نتيجة الطالب بالمادة.',
    'plan_year_order': 'ترتيب السنة في المنهاج؛ لا يُحسب من سنة الطالب الحالية.',
    'plan_semester_order': 'ترتيب الفصل في المنهاج.',
    'plan_credits_count': 'قيمة credits_count المنقولة من صف المنهاج؛ حقل مستقل عن course_credits.'}
HISTORY = {
    'course_history_avg_mark': 'متوسط العلامة التاريخي من 100، موزون زمنياً ثم ممزوج بالمتوسط العام؛ ليس علامة متوقعة لهذا الطالب.',
    'course_history_fail_rate': 'نسبة الرسوب التاريخية بعد التنعيم؛ الرسوب هنا final_mark < 50. القيمة بين 0 و1.',
    'course_history_avg_attempt': 'متوسط رقم المحاولة في السجلات التاريخية، موزون ومُنعّم؛ مختلف عن attempt_number لهذا الطالب.',
    'course_history_retake_rate': 'نسبة السجلات ذات attempt_number > 1، موزونة ومُنعّمة.',
    'course_history_effective_support': 'مجموع الأوزان الزمنية للسجلات المستخدمة، وليس دائماً عددها الحقيقي.',
    'course_history_fallback_level': 'مصدر التجميع: 1 المادة ضمن الاختصاص؛ 2 المادة عبر الاختصاصات؛ 3 الاختصاص والمتطلب والساعات؛ 4 الكلية والمتطلب والساعات؛ 5 المتطلب والساعات؛ 6 العام.',
    'course_history_missing': '1 عندما يكون المستوى 3 فأكثر أو الدعم أقل من 20. قد تكون المتوسطات متاحة مع هذا التنبيه.'}
SPECIALTY = {
    'avg_mark': 'متوسط العلامة من 100 بعد الوزن الزمني والتنعيم.',
    'fail_rate': 'نسبة الرسوب التاريخية بعد التنعيم، بين 0 و1.',
    'avg_points': 'متوسط النقاط التاريخية من 4 بعد التنعيم.',
    'effective_support': 'مجموع أوزان السجلات الفعلية؛ لا يشمل معامل التنعيم 20.',
    'missing': '1 عندما لا توجد سجلات للمجموعة الأصلية، حتى إن أمكن إعطاء متوسط بديل.'}


def group_name(column):
    if column in SNAPSHOT: return 'حالة الطالب'
    if column in STATIC: return 'خصائص المادة والمنهاج'
    if column in HISTORY: return 'تاريخ المادة المجمد'
    if column in SPECIALTY_HISTORY_FEATURES: return 'تاريخ الاختصاص المجمد'
    if column in PLAN_CONTEXT_COLUMNS: return 'سياق الخطة؛ يعاد حسابه'
    return 'رقم الفصل داخل السنة'


def context_math(courses, own):
    weights = np.array([r['course_credits'] for r in courses], dtype=float)
    mask = np.array([r['course_id'] != own['course_id'] for r in courses])
    total, peer_total = weights.sum(), weights[mask].sum()
    desc = {
        'plan_course_count': (len(courses), f'n = {len(courses)}', 'عدد مواد الخطة كاملة.'),
        'plan_total_credits': (total, ' + '.join(fmt(x) for x in weights), 'مجموع ساعات الخطة.'),
        'peer_course_count': (len(courses)-1, f'{len(courses)} - 1', 'عدد المواد الأخرى بعد استبعاد هذه المادة.'),
        'peer_total_credits': (peer_total, f'{fmt(total)} - {fmt(own["course_credits"])}', 'ساعات المواد الأخرى فقط.')}
    for label, col in [('fail_rate', 'course_history_fail_rate'), ('avg_mark', 'course_history_avg_mark'), ('avg_attempt', 'course_history_avg_attempt')]:
        values = np.array([r[col] for r in courses], dtype=float)
        full_sum = float(np.dot(values, weights))
        peer_sum = float(np.dot(values[mask], weights[mask]))
        desc['plan_credit_weighted_' + label] = (full_sum / total, f'{fmt(full_sum)} / {fmt(total)}',
            'متوسط تاريخ المواد موزوناً بساعاتها؛ نفس القيمة لجميع مواد هذه الخطة.')
        desc['peer_credit_weighted_' + label] = (peer_sum / peer_total, f'({fmt(full_sum)} - {fmt(own["course_credits"])} × {fmt(own[col])}) / {fmt(peer_total)}',
            'المتوسط الموزون للمواد الأخرى؛ يتغير بحسب المادة المستبعدة.')
        if label == 'fail_rate':
            desc['plan_difficulty_credit_load'] = (full_sum, ' + '.join(f'{fmt(w)}×{fmt(v)}' for w,v in zip(weights,values)),
                'مجموع ساعات × نسبة الرسوب التاريخية؛ مؤشر حمل الصعوبة المستخدم في المدخلات.')
            desc['peer_difficulty_credit_load'] = (peer_sum, f'{fmt(full_sum)} - {fmt(own["course_credits"])} × {fmt(own[col])}',
                'نفس حمل الصعوبة بعد طرح مساهمة المادة الحالية.')
            desc['peer_max_fail_rate'] = (float(values[mask].max()), 'max(' + ', '.join(fmt(v) for v in values[mask]) + ')',
                'أعلى نسبة رسوب تاريخية بين المواد الأخرى.')
    desc['peer_difficulty_missing'] = (0, 'isna(peer_credit_weighted_fail_rate) → 0', 'يوجد تاريخ صالح للمواد الأخرى في هذه الخطة.')
    for col, (value, _, _) in desc.items():
        np.testing.assert_allclose(value, own[col], rtol=0, atol=1e-10)
    return [{'feature': col, 'الحساب لهذه المادة': expr, 'القيمة الفعلية': own[col], 'التفسير': meaning}
            for col, (value, expr, meaning) in desc.items()]


def sections(data, cases):
    part, snap = data['part_id'], data['snapshot']
    best = data['best_courses']
    focal = next((r for r in best if r['course_id'] == '347.111'), best[0])
    parts = []
    first = p(f'الطالب <b>29485.111</b>، الاختصاص <b>42.111</b>، الفصل <b>{part}</b>، '
        f'الملف <b>{escape(data["xml_name"])}</b> وفيه <b>{len(data["candidates"])}</b> مادة. المجال 12–18 ساعة شامل الطرفين.')
    first += code(load_local_inputs, 'if snapshot_path:', 'return candidates,')
    first += p('استُخدم المسار دون <code>--snapshot</code>: ينظف سجل الحالات ثم يستدعي <code>build_student_snapshot</code>. '
        'هذه الدالة تختار صف بداية الفصل وتضيف تاريخ الطالب السابق. قيم GPA الموجودة في XML لا تدخل في هذا الحساب.')
    first += code(build_student_snapshot, 'status = status[', 'snapshot.update(lookup')
    first += code(add_student_history_features, 'semester["gpa_prev_1"]', before='semester["gpa_trend_missing"] =')
    first += formula(f'gpa_trend_delta = {fmt(snap["gpa_prev_1"])} - {fmt(snap["gpa_prev_2"])} = {fmt(snap["gpa_trend_delta"])}')
    first += p('عند 20252 أصبحت نتيجة 20251 المعروفة جزءاً من حالة الطالب: آخر GPA = 3.06، والساعات السابقة = 86، '
        'وعدد الفصول السابقة = 5. المودل وتاريخ المواد ما زالا مجمدين حتى 20243. '
        '3.06 هي قيمة سجل الحالة المقربة؛ إعادة حساب المعدل من نقاط المواد تعطي 3.05556 تقريباً.')
    first += table([{'feature': k, 'القيمة': snap[k], 'المعنى والمصدر': desc} for k, desc in SNAPSHOT.items()])
    first += p('حقول نهاية الفصل في التصدير مستبعدة من snapshot:') + table(data['xml_outcome_fields_excluded'])
    parts.append(('1. حالة الطالب', first))

    second = code(normalize_candidates, 'catalog = catalog.rename(', '})')
    second += p('نقلنا بيانات المنهاج تحت أسماء <code>plan_*</code>. الربط يكون بعد تقييد المنهاج بالاختصاص، '
        'ثم على <code>course_id</code>. ساعات الطلب تُطابق ساعات المنهاج قبل القبول.')
    second += code(normalize_candidates, '# Match training', 'rows["course_name"]')
    second += p(f'هنا <code>prior</code> يستخدم <code>part_id &lt; {part}</code>. ثم يجمع سجل المحاولات لكل مادة ويضيف 1؛ '
        'لا يُسمح لمحاولة من الفصل المطلوب أن ترفع رقم المحاولة مسبقاً.')
    second += table([{'feature': k, 'المعنى': v} for k, v in STATIC.items()])
    second += table(pd.DataFrame(data['candidates'])[['course_id', 'course_name', *STATIC]])
    parts.append(('2. خصائص المادة', second))

    third = p('هناك وزن زمني لكل تسجيل تاريخي: <b>0.25</b> قبل سنة 2022، و<b>1</b> من 2022 فصاعداً. '
        '<code>weighted_sum</code> يعني أن نضرب كل قيمة بوزنها أولاً، ثم نجمع. هذه الأوزان لا تستخدم ساعات المادة.')
    third += code(temporal_weight)
    third += p('<b>بناء المجاميع المحفوظة:</b> المقطع التالي هو كود بناء التاريخ أثناء تجهيز البيانات؛ لا ننفذ '
        '<code>update</code> عند التوصية. وقت التوصية نقرأ هذه المجاميع من <code>course_history_state.pkl</code>.')
    third += code(CourseHistoryState.update, 'base["effective_support"]', 'base["retake_sum"]')
    third += formula('mark_sum = Σ(weight × final_mark)\nfail_sum = Σ(weight × 1[final_mark < 50])\nattempt_sum = Σ(weight × attempt_number)\nretake_sum = Σ(weight × 1[attempt_number > 1])\neffective_support = Σ(weight)\nraw_count = عدد التسجيلات دون أوزان')
    third += p('اختار <code>apply</code> أقرب مستوى له بيانات. المستوى 1 يعني المادة في اختصاص الطالب؛ المستوى 2 يعني '
        'المادة عبر جميع الاختصاصات. وجود دعم أقل من 20 لا يمنع استخدام المستوى الأقرب؛ يرفع فقط <code>course_history_missing</code>.')
    third += code(CourseHistoryState.apply, 'for level in range', 'prior = global_values')
    third += p('<b>هذا المقطع نُفذ عند التنبؤ:</b> يمزج المتوسط المحلي بالمتوسط العام. الثابت 20 يُعادل وزن 20 تسجيلًا '
        'بمتوسط المجموعة العامة؛ تأثيره أكبر عند قلة السجلات المحلية.')
    third += code(CourseHistoryState.apply, 'smoothed = (', 'values[output_column][available]')
    third += formula('smoothed_value = (local_weighted_sum + 20 × global_mean) / (local_support + 20)')
    third += table([{'feature': k, 'المعنى': desc} for k, desc in HISTORY.items()])
    candidates_by_id = {r['course_id']: r for r in data['candidates']}
    for item in sorted(data['course_math'], key=lambda r: (r['course_id'] != focal['course_id'], r['course_id'])):
        course = candidates_by_id[item['course_id']]
        s = item['sums']
        terms = item['semester_contributions']
        early = sum(r['raw_count'] for r in terms if r['part_id'] < 20220)
        recent = s['raw_count'] - early
        body = p(f'المستوى المستخدم <b>{item["level"]}</b>؛ مفتاح التجميع <code>{escape(item["key"])}</code>. '
            f'عدد التسجيلات الحقيقي <b>{fmt(s["raw_count"])}</b>، ومجموع الأوزان <b>{fmt(s["effective_support"])}</b>.')
        body += formula(f'effective_support = {fmt(early)} × 0.25 + {fmt(recent)} × 1 = {fmt(s["effective_support"])}')
        body += table(terms, {'part_id': 'الفصل التاريخي', 'raw_count': 'عدد السجلات', 'weight_per_row': 'وزن السجل',
            'effective_support': 'مجموع الأوزان', 'mark_sum': 'مجموع العلامات الموزون', 'fail_sum': 'مجموع الرسوب الموزون'})
        body += p('جمعنا أعمدة الجدول السابق عبر الفصول؛ ثم طبقنا التنعيم على كل خاصية:')
        for feature in item['features']:
            body += formula(f'{feature["feature"]} = ({fmt(feature["weighted_sum"])} + 20 × {fmt(feature["global_mean"])}) / '
                f'({fmt(s["effective_support"])} + 20) = {fmt(feature["value"])}')
        body += table([{'feature': col, 'القيمة التي دخلت التنبؤ': course[col]} for col in COURSE_HISTORY_COLUMNS])
        if early == 0:
            body += p('كل سجلات هذا المستوى من 2022 فما بعد؛ لذلك مجموع الأوزان هنا يساوي عدد السجلات. هذا ناتج من البيانات.')
        third += f'<details {"open" if item["course_id"] == focal["course_id"] else ""}><summary>{escape(course["course_name"])} · {course["course_id"]}</summary>{body}</details>'
    parts.append(('3. التاريخ وweighted sum', third))

    fourth = p('تاريخ الاختصاص يضيف 10 خصائص: خمس على مستوى الاختصاص كله، وخمس على مستوى الاختصاص + نوع المتطلب. '
        'هذه المجاميع موزونة زمنياً ومجمدة عند 20243 أيضاً. المودل الحالي يعيد تجميعها من ملف التدريب أثناء <code>load()</code>.')
    fourth += code(AcademicPlanRecommender.load, 'train = pd.read_parquet', 'specialty_history =')
    fourth += code(_finish_specialty_history, 'degree_points = np.where', before='requirement_count = result[')
    fourth += p('متوسط الاختصاص يُنعّم نحو العام؛ متوسط نوع المتطلب يُنعّم نحو متوسط الاختصاص الناتج. '
        'هذه سلسلة مختلفة عن تاريخ المادة، الذي يستخدم المتوسط العام مباشرة في التنعيم.')
    fourth += formula('degree_avg = (degree_weighted_sum + 20 × global_avg) / (degree_support + 20)\nrequirement_avg = (requirement_weighted_sum + 20 × degree_avg) / (requirement_support + 20)')
    for prefix, name in [('degree_history_', 'كل الاختصاص'), ('degree_requirement_history_', 'الاختصاص + نوع المتطلب')]:
        fourth += table([{'feature': prefix + suffix, 'المجموعة': name, 'المعنى': desc, 'قيمة المادة المعروضة': focal[prefix+suffix]}
                         for suffix, desc in SPECIALTY.items()])
    parts.append(('4. تاريخ الاختصاص', fourth))

    fifth = p(f'من المواد الـ{len(data["candidates"])} ولّد الكود <b>{data["result"]["matching_plan_count"]:,}</b> خطة ضمن 12–18 ساعة. '
        f'سنشرح أعلى خطة قبل الفلترة، رقم <b>{data["best_summary"]["plan_id"]}</b>، وفيها '
        f'<b>{len(best)}</b> مواد و<b>{fmt(data["best_summary"]["total_credits"])}</b> ساعة.')
    fifth += code(enumerate_plan_indices, 'def visit(', 'yield from visit(0')
    fifth += p('بعد تركيب صفوف كل خطة يُستدعى هذا السطر، فيفصل الحساب حسب <code>plan_id</code>؛ '
        'الـ14 خاصية التالية تُحسب للخطة المعروضة، وليست لمجموع المواد المتاحة كلها:')
    fifth += code(AcademicPlanRecommender.score_rows, 'context =', 'rows[PLAN_CONTEXT_COLUMNS]')
    fifth += code(compute_plan_context_features, 'weighted_specs = {', 'weighted = (')
    fifth += p('الوزن هنا هو <b>ساعات المادة</b>. لكل صف يحسب <code>weighted = source × credits</code>، '
        'ثم يجمعه داخل الخطة. عند <code>source = course_history_fail_rate</code> نحصل على مساهمة المادة في حمل الصعوبة.')
    fifth += table([{'المادة': r['course_name'], 'الساعات': r['course_credits'], 'نسبة الرسوب التاريخية': r['course_history_fail_rate'],
        'حاصل الضرب: ساعات × رسوب': r['course_credits'] * r['course_history_fail_rate']} for r in best])
    fifth += code(compute_plan_context_features, 'if label == "fail_rate":', before='fail_rate = pd.to_numeric(')
    difficulty = sum(r['course_credits'] * r['course_history_fail_rate'] for r in best)
    fifth += formula(f'plan_difficulty_credit_load = Σ(credits × history_fail_rate) = {fmt(difficulty)}\n'
        f'plan_credit_weighted_fail_rate = {fmt(difficulty)} / {fmt(data["best_summary"]["total_credits"])} = {fmt(focal["plan_credit_weighted_fail_rate"])}')
    fifth += p('الأول <b>مجموع موزون</b> بوحدة الساعات، والثاني <b>متوسط موزون</b> بين 0 و1. '
        'هذه صعوبة مبنية على التاريخ، وليست مجموع احتمالات الرسوب التي توقعها مودل الرسوب لهذا الطالب.')
    for course in sorted(best, key=lambda r: r['course_id'] != focal['course_id']):
        detail = p('في خصائص <code>peer_*</code> تُستبعد المادة المعروضة وحدها، وتبقى بقية مواد الخطة. '
            'خصائص <code>plan_*</code> مشتركة بين جميع صفوف الخطة.')
        detail += table(context_math(best, course))
        fifth += f'<details {"open" if course["course_id"] == focal["course_id"] else ""}><summary>الحساب الكامل للمادة: {escape(course["course_name"])} · {course["course_id"]}</summary>{detail}</details>'
    parts.append(('5. صعوبة الخطة', fifth))

    sixth = code(AcademicPlanRecommender.score_rows, 'contract =', 'rows["fail_probability"]')
    sixth += p('مررنا <b>57 feature</b> إلى مودل النقاط، و<b>47 feature</b> إلى مودل الرسوب. '
        'قيم <code>expected_points</code> هي النقاط المتوقعة من <b>4</b>؛ لا يعطي هذا المسار علامة متوقعة من 100. '
        'القيم العشرية مثل 3.08 هي متوسطات متوقعة، وتبقى كما أخرجها المودل دون تقريب إلى سلم التقديرات.')
    sixth += p('<b>حالة الخطة المعروضة: ' + ('توصية مقبولة.' if data['best_is_recommendation'] else 'مستبعدة؛ أعلى خطة قبل شرط القبول وليست توصية صادرة من النظام.') + '</b>')
    sixth += table([{'course_id': r['course_id'], 'المادة': r['course_name'], 'الساعات': r['course_credits'],
        'النقاط المتوقعة /4': r['expected_points'], 'احتمال الرسوب': r['fail_probability'],
        'النقاط الموزونة بالساعات': r['course_credits'] * r['expected_points']} for r in best])
    sixth += code(summarize_scored_plans)
    sixth += formula(f'expected_quality_points = Σ(credits × expected_points) = {fmt(data["best_summary"]["expected_quality_points"])}\n'
        f'expected_plan_gpa = {fmt(data["best_summary"]["expected_quality_points"])} / {fmt(data["best_summary"]["total_credits"])} = {fmt(data["best_summary"]["expected_plan_gpa"])}\n'
        f'شرط القبول: {fmt(data["best_summary"]["expected_plan_gpa"])} > {fmt(snap["start_agpa_points"])} → {str(data["best_is_recommendation"])}')
    sixth += p('السطر الذي يستخدم <code>.gt(current_gpa)</code> هو سبب استبعاد الخطة. '
        f'عدد الخطط المقبولة الفعلي <b>{data["result"]["accepted_plan_count"]:,}</b>. '
        '<code>gpa_gain</code> هو فرق معدل الخطة المتوقع عن التراكمي الحالي، وليس مقدار تغير التراكمي بعد الفصل.')
    for index, course in enumerate(best):
        feature_rows = [{'feature': name, 'المجموعة': group_name(name), 'القيمة قبل المصفوفة': course[name],
                         'القيمة المرسلة للمودل': data['best_matrix'][index][name]} for name in data['model_features']]
        sixth += f'<details><summary>الـ57 feature التي أعطت توقع {escape(course["course_name"])} = {fmt(course["expected_points"])}</summary>' + table(feature_rows) + '</details>'
    parts.append(('6. توقع كل مادة', sixth))

    seventh = p('المقارنة التالية بين <b>' + ('التوصية الأولى' if data['best_is_recommendation'] else 'أعلى خطة مستبعدة') +
        '</b> وبين التسجيل الفعلي. لا ننسب إلى النظام اختياراً نهائياً عندما تكون قائمة التوصيات فارغة.')
    seventh += p(f'<b>{len(data["common"])}</b> مواد مشتركة، <b>{len(data["model_only"])}</b> في الخطة المعروضة فقط، '
        f'<b>{len(data["actual_only"])}</b> سجّلها الطالب فقط.')
    seventh += table(data['comparison'], {'course_id': 'course_id', 'course_name': 'المادة', 'membership': 'المقارنة',
        'course_credits': 'الساعات', 'plan_expected_points': 'توقعها في الخطة المعروضة /4',
        'expected_points': 'توقعها في التسجيل الفعلي /4', 'points': 'نقاطها الفعلية /4', 'final_mark': 'علامتها الفعلية /100'})
    seventh += p('اختلاف التوقع للمادة المشتركة بين العمودين سببه اختلاف رفاقها وحمل الخطة؛ '
        'كل توقع أُعيد حسابه ضمن سياقه. العلامة الفعلية تخص الخطة التي درسها الطالب فقط؛ '
        'لا نستخدمها بوصفها نتيجة مؤكدة للخطة البديلة. الشرطة — تعني عدم وجود تسجيل فعلي أو عدم وجود المادة في تلك الخطة.')
    metrics = data['metrics']
    seventh += table([{'القياس للخطة الفعلية فقط': name, 'القيمة': value} for name, value in [
        ('عدد مواد التسجيل الفعلي', metrics['actual_count']), ('الساعات الفعلية', metrics['actual_credits']),
        ('المعدل الفعلي المحسوب من نقاط المواد', metrics['actual_gpa']),
        ('المعدل المتوقع لنفس المواد المسجلة', metrics['predicted_gpa_for_actual_plan']),
        ('الخطأ المطلق في معدل الخطة الفعلية', abs(metrics['actual_gpa'] - metrics['predicted_gpa_for_actual_plan'])),
        ('متوسط الخطأ المطلق لنقاط المواد', metrics['course_points_mae'])]])
    if data['actual_missing_from_candidates']:
        seventh += p('<b>ملاحظة مصدر البيانات:</b> المواد المسجلة التالية غائبة عن ملف الأهلية: ' + ', '.join(data['actual_missing_from_candidates']) +
            '. تشغيل procedure على 20251 مؤكد من المستخدم؛ سبب عدم التطابق داخلها غير مثبت.')
    else:
        seventh += p('كل مواد التسجيل الفعلي موجودة في ملف الأهلية لهذا الفصل. هذا يحقق فحص الاحتواء، '
            'لكنه لا يثبت وحده أن حالة المتطلبات والمقررات المستعملة في procedure تعود لبداية الفصل.')
    parts.append(('7. المقارنة مع الطالب', seventh))
    return parts


CODE_SOURCES = set()


def main(folder):
    folder = Path(folder)
    cases = {term: json.loads((folder / str(term) / 'explanation_data.json').read_text(encoding='utf-8')) for term in [20251, 20252]}
    all_sections = {term: sections(data, cases) for term, data in cases.items()}
    checks = json.loads((folder / 'checks.json').read_text(encoding='utf-8'))
    html = '''<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>شرح الكود والبيانات — الطالب 29485.111</title><style>
*{box-sizing:border-box}body{margin:0;background:#f6f8fb;color:#182c41;font:16px/1.85 system-ui,Segoe UI,sans-serif}
header,main,nav,footer{max-width:1350px;margin:auto;padding:18px 30px}header{padding-bottom:6px}h1{font-size:27px;line-height:1.5;margin:8px 0}h2{font-size:23px}p{max-width:100ch;margin:16px 0}
nav{display:flex;gap:8px;flex-wrap:wrap;padding-top:8px;padding-bottom:8px}button{font:inherit;cursor:pointer;padding:8px 14px;background:#fff;border:1px solid #bdcddd;color:#20466b;border-radius:6px}button[aria-pressed=true]{color:#fff;background:#20466b}
button:focus-visible,summary:focus-visible{outline:3px solid #ca861a;outline-offset:3px}.source{margin:18px 0;border:1px solid #d6e0eb;border-radius:7px;background:white;overflow:hidden}.source-label{background:#e9f0f7;padding:10px 16px;font-size:14px;unicode-bidi:plaintext}
pre{margin:0;padding:18px;white-space:pre-wrap;overflow-wrap:anywhere;text-align:left;font:14px/1.7 Consolas,monospace}code{direction:ltr;unicode-bidi:isolate;font:14px Consolas,monospace}p code{padding:2px 5px;background:#e8eef4}
.formula{background:#eaf4f2;border-right:4px solid #318779;padding:14px 18px;white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.9 Consolas,monospace;text-align:left;margin:16px 0}.table-wrap{overflow-x:auto;border:1px solid #d6e0eb;border-radius:7px;background:white;margin:18px 0}
table{border-collapse:collapse;width:100%;font-size:14px}th{background:#e9f0f7;font-weight:600}td,th{padding:10px 12px;text-align:right;border-bottom:1px solid #e0e7ef;vertical-align:top;unicode-bidi:plaintext}tr:last-child td{border:0}
details{margin:16px 0;border-top:1px solid #ccd9e6;padding-top:8px}summary{cursor:pointer;color:#145a84;font-weight:600;padding:8px 0;overflow-wrap:anywhere}small,footer{color:#51677d}strong,b{font-weight:650}.note{border-right:4px solid #c38a24;padding:12px 18px;background:#fff7e7}
@media(max-width:760px){header,main,nav,footer{padding:14px}h1{font-size:23px}pre{font-size:12px;padding:12px}td,th{min-width:100px;font-size:13px}.source-label{overflow-wrap:anywhere}}
@media print{nav{display:none}section[hidden]{display:block}details>div,details>p{display:block}.table-wrap{overflow:visible}pre{font-size:10px}td,th{font-size:10px}}
</style><header><small>شرح التنفيذ الفعلي · كود المشروع مقابل الأرقام</small><h1>الطالب 29485.111 — من خصائص المادة إلى مقارنة الخطط</h1>
<p>الفصلان 20251 و20252 · الحد الأدنى 12 والحد الأعلى 18 ساعة · تاريخ المواد والاختصاص حتى 20243</p>
<p class="note">في الفصلين لم تتجاوز أي خطة عتبة المعدل الحالي. يعرض الشرح أعلى خطة قبل الفلترة وسبب استبعادها؛ التوصيات النهائية فارغة.</p></header>
<nav aria-label="الفصل"><button data-term="20251" aria-pressed="false">20251 · 15 مادة</button><button data-term="20252" aria-pressed="true">20252 · 20 مادة</button></nav><nav aria-label="خطوات التنفيذ">'''
    html += ''.join(f'<button data-step="{i}" aria-pressed="{str(i==1).lower()}">{escape(title)}</button>'
                    for i, (title, _) in enumerate(all_sections[20252], 1))
    html += '</nav><main aria-live="polite">'
    for term, blocks in all_sections.items():
        for i, (title, content) in enumerate(blocks, 1):
            html += f'<section data-panel-term="{term}" data-panel-step="{i}" {"" if term==20252 and i==1 else "hidden"}><h2>{escape(title)} · {term}</h2>{content}</section>'
    snapshot_diff = [{'feature': k, '20251': cases[20251]['snapshot'][k], '20252': cases[20252]['snapshot'][k]} for k in SNAPSHOT]
    html += '<details><summary>كيف تغيرت حالة الطالب بين الفصلين؟</summary>' + table(snapshot_diff) + '</details>'
    html += '<details><summary>فحوص الأرقام ومصدرها</summary>' + table(checks) + p('طُوبقت مجاميع تاريخ المواد مع سجلات التدريب الأصلية، '
        'وحُسبت خصائص الخطة الأربع عشرة مستقلاً لكل مادة معروضة، وطابقت مصفوفتا 57 و47 feature للخطة الفعلية ملفات التقييم المحفوظة. '
        'لم يتغير كود المشروع أو المودلان أو التاريخ المجمد.') + '</details></main>'
    html += '''<footer>الأرقام مبنية على تشغيل فعلي. كل مقطع كود ظاهر من ملفات src الأصلية، وأرقام السطور تخص النسخة التي نُفّذ عليها الحساب.</footer>
<script>
let term='20252',step='1';
function update(){document.querySelectorAll('section[data-panel-term]').forEach(p=>p.hidden=p.dataset.panelTerm!==term||p.dataset.panelStep!==step);
document.querySelectorAll('button[data-term]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.term===term)));
document.querySelectorAll('button[data-step]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.step===step)));}
document.querySelectorAll('button[data-term]').forEach(b=>b.addEventListener('click',()=>{term=b.dataset.term;update();}));
document.querySelectorAll('button[data-step]').forEach(b=>b.addEventListener('click',()=>{step=b.dataset.step;update();}));
</script></html>'''
    (folder / 'explanation.html').write_text(html, encoding='utf-8')
    (folder / 'render_validation.json').write_text(json.dumps({'context_formulas_verified_for_courses': sum(len(d['best_courses']) for d in cases.values()),
        'production_code_sources': sorted(CODE_SOURCES), 'helper_code_displayed': False}, indent=2), encoding='utf-8')
    print(folder / 'explanation.html')


if __name__ == '__main__':
    main(sys.argv[1])
