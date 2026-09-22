# %% 1. ملفات الطلب والطالب المختار
# هذا التتبّع يستدعي كود المشروع الفعلي؛ لا يدرّب المودل ولا يغيّر قواعد التوصية.
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from itertools import combinations
import inspect
import json
import re
import sys
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents]
            if (p / 'src/recommendation.py').exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src import paths
from src.data.clean_student_status import clean_student_status
from src.recommendation import (AcademicPlanRecommender, enumerate_plan_indices,
    build_plan_rows, rank_plans, summarize_scored_plans, STUDENT_SNAPSHOT_COLUMNS, CANDIDATE_COURSE_COLUMNS)
from src.recommendation_inputs import (load_local_inputs, normalize_candidates,
    build_student_snapshot, validate_snapshot)
from src.features.temporal_features import (COURSE_HISTORY_COLUMNS, PLAN_CONTEXT_COLUMNS,
    build_history_keys, compute_plan_context_features, add_student_history_features)
from src.experiments.specialty_history import SPECIALTY_HISTORY_FEATURES
from src.experiments.modeling import prepare_matrix
from src.features.feature_contract import prepare_model_matrix, LEAKAGE_COLUMNS

SID, DID, PART = '29485.111', '42.111', 20251
MIN_CREDITS, MAX_CREDITS = 12, 18
OUT = Path(globals().get('TRACE_OUTPUT', ROOT / 'data/evaluation/recommendation_trace_pilot' /
    ('trace_29485_20251_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))))
OUT.mkdir(parents=True, exist_ok=True)
checks = []
def check(name, condition):
    checks.append({'check': name, 'passed': bool(condition)})
    assert condition, name

def show(frame):
    frame = frame if isinstance(frame, pd.DataFrame) else pd.DataFrame(frame)
    markup = frame.to_html(index=False, escape=True, border=0, na_rep='—',
                           float_format=lambda x: f'{x:.8g}')
    if globals().get('_capture_trace', False):
        _trace_displays.append(markup)
    else:
        try:
            from IPython.display import display, HTML
            display(HTML(markup))
        except ImportError:
            print(frame.to_string(index=False))

def save_json(name, value):
    def default(v):
        if isinstance(v, Path): return str(v)
        if isinstance(v, np.generic): return v.item()
        raise TypeError(type(v).__name__)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                      default=default, allow_nan=False), encoding='utf-8')

def records(frame):
    return json.loads(frame.to_json(orient='records', force_ascii=False, double_precision=15))

def source(fn):
    lines, start = inspect.getsourcelines(fn)
    return {'function': fn.__qualname__, 'file': str(Path(inspect.getfile(fn)).resolve()),
            'line': start, 'code': ''.join(lines)}

def read_export(path):
    # Preserve the source bytes. Bare & in exported names is escaped only for XML parsing.
    text = path.read_text(encoding='utf-8-sig')
    text, escaped = re.subn(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', text)
    ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
    attr = '{urn:schemas-microsoft-com:office:spreadsheet}'
    root = ET.fromstring(text)
    rows = []
    for row in root.findall('.//ss:Table/ss:Row', ns):
        values = []
        for cell in row.findall('ss:Cell', ns):
            position = int(cell.get(attr + 'Index', len(values) + 1))
            values.extend([None] * (position - 1 - len(values)))
            data = cell.find('ss:Data', ns)
            values.append(data.text if data is not None else None)
        rows.append(values)
    # The unnamed first column is only the Excel row number.
    frame = pd.DataFrame(rows[1:], columns=rows[0]).drop(columns=[None, ''], errors='ignore')
    return frame, escaped

exports, audit = {}, []
for number in range(2, 12):
    p = Path.home() / 'Downloads' / f'exportdata ({number}).xml'
    frame, escaped = read_export(p)
    exports[number] = frame
    per_student = frame.loc[frame.IS_REQUESTABLE.eq('Y')].groupby('STUDENT_ID').COURSE_ID.nunique().to_dict()
    audit.append({'file': p.name, 'sha256': sha256(p.read_bytes()).hexdigest(),
        'rows': len(frame), 'requestable_by_student': per_student,
        'non_null_part_values': sorted(frame.PART_ID.dropna().unique().tolist()),
        'null_part_rows': int(frame.PART_ID.isna().sum()), 'bare_ampersands_escaped_in_memory': escaped})
save_json('01_export_audit.json', audit)
show(pd.DataFrame(audit).drop(columns='sha256'))
raw = exports[7]
check('Selected export: exactly one student and 15 unique requestable courses',
      set(raw.STUDENT_ID) == {SID} and raw.IS_REQUESTABLE.eq('Y').all() and raw.COURSE_ID.nunique() == len(raw) == 15)
check('Selected export needs no XML repair', audit[5]['bare_ampersands_escaped_in_memory'] == 0)
# Record the semester supplied by the user separately; do not rewrite the source PART_ID.
source_path = Path.home() / 'Downloads' / 'exportdata (7).xml'
(OUT / 'original_export_7.xml').write_bytes(source_path.read_bytes())
candidate_path = OUT / '01_candidates_from_xml.json'
save_json(candidate_path.name, records(raw))
save_json('01_request.json', {'student_id': SID, 'degree_id': DID, 'part_id': PART,
    'min_credits': MIN_CREDITS, 'max_credits': MAX_CREDITS,
    'semester_source': 'User explicitly confirmed the procedure was executed with 20251; source PART_ID is null.',
    'procedure_execution_semester_user_confirmed': True,
    'historical_eligibility_proven': False, 'xml_source': str(source_path),
    'source_sha256': sha256(source_path.read_bytes()).hexdigest()})
print('15 مادة / الفصل المطلوب 20251 / المجال شامل: 12 إلى 18 ساعة.')
print('STUDENT_DEGREE_ID = 30782.111 هو سجل ارتباط الطالب؛ degree_id للخطة = 42.111.')
print('المستخدم أكد تنفيذ procedure على 20251؛ هذا يوثق الباراميتر ولا يثبت أنها تستخدم حالة بداية ذلك الفصل.')
show(raw[['COURSE_ID', 'COURSE_NAME_SL', 'COURSE_CREDITS', 'IS_REQUESTABLE', 'PART_ID']])

# %% 2. حالة الطالب عند بداية الفصل ومصدر كل قيمة
# القيم النهائية في XML ليست مصدر snapshot. نستخدم دوال CLI نفسها دون --snapshot.
candidates, snapshot, import_report = load_local_inputs(candidate_path, SID, DID, PART)
save_json('02_snapshot.json', json.loads(pd.Series(snapshot).to_json(double_precision=15)))
save_json('02_import_report.json', import_report)
candidates.to_parquet(OUT / '02_normalized_candidates.parquet', index=False)
status = clean_student_status(pd.read_parquet(paths.STUDENT_STATUS_PATH))
history = pd.read_parquet(paths.CLEAN_STUDENT_COURSE_PATH)
diplomas = pd.read_parquet(paths.CLEAN_STUDENT_DIPLOMA_PATH)
student_status = status.loc[status.student_id.eq(SID) & status.part_id.le(PART)].copy()
prior = student_status.loc[student_status.part_id.lt(PART)]
show(prior[['part_id', 'degree_id', 'semester_reg_courses', 'gpa_points', 'start_agpa_points',
            'end_agpa_points', 'reg_total_semesters']])
origins = {c: 'صف حالة الطالب 20251: قيمة معروفة عند بداية الفصل' for c in STUDENT_SNAPSHOT_COLUMNS}
origins.update({
    'gpa_prev_1': 'آخر GPA لفصل مسجل قبل 20251؛ إزاحة سجل الفصول',
    'gpa_prev_2': 'GPA المسجل الذي يسبق gpa_prev_1',
    'gpa_trend_delta': 'gpa_prev_1 - gpa_prev_2',
    'gpa_trend_missing': 'هل فرق المعدلين مفقود؟',
    'prior_total_reg_courses': 'total_reg_courses في حالة 20251؛ يمثل بداية الفصل',
    'prior_total_reg_credits': 'total_reg_credits في حالة 20251؛ يمثل بداية الفصل',
    'prior_total_fail_courses': 'total_fail_courses في حالة 20251؛ يمثل بداية الفصل',
    'prior_total_fail_credits': 'total_fail_credits في حالة 20251؛ يمثل بداية الفصل',
    'prior_fail_credit_ratio': 'prior_total_fail_credits / prior_total_reg_credits',
    'prior_registered_semesters': 'reg_total_semesters من حالة الفصل السابق ضمن نفس الاختصاص',
    'observed_gap_semesters': 'عدد فصول الانقطاع المتتالية السابقة من سجل التسجيل',
    'faculty_id': 'السجل الدراسي للطالب ضمن نفس الاختصاص قبل 20251',
    'diploma_gpa': 'data/clean/student_diploma.parquet',
    'diploma_type_id': 'data/clean/student_diploma.parquet', 'part_id': 'الفصل المحدد في طلب المستخدم'})
snapshot_table = pd.DataFrame([{'feature': k, 'value': v, 'source': origins[k]} for k, v in snapshot.items()])
show(snapshot_table)
print('GPA_POINTS في XML:', raw.GPA_POINTS.unique().tolist(),
      '/ END_AGPA_POINTS في XML:', raw.END_AGPA_POINTS.unique().tolist())
print('current_gpa المستخدم فعلياً = start_agpa_points =', snapshot['start_agpa_points'])
print('ملاحظات الاستيراد:', import_report['warnings'])
# Adversarial check: target/future outcomes must not change this start snapshot.
poisoned = status.copy()
mask = poisoned.student_id.eq(SID) & poisoned.part_id.ge(PART)
for column in ['gpa_points', 'end_agpa_points', 'semester_fail_courses', 'semester_fail_credits',
               'semester_pass_courses', 'semester_pass_credits', 'reg_total_semesters']:
    poisoned[column] = poisoned[column].astype('float64')
    poisoned.loc[mask, column] = 999.0
changed = validate_snapshot(build_student_snapshot(poisoned, history.loc[history.part_id.lt(PART)],
                            diplomas, SID, DID, PART), SID, DID, PART)
pd.testing.assert_series_equal(pd.Series(snapshot), pd.Series(changed))
check('Snapshot invariant to target/future outcome poisoning and removal of future course rows', True)

# %% 3. المواد بعد التطبيع وإضافة التاريخ المجمد
# أسماء المقررات وساعاتها من الطلب؛ سمات الخطة من catalog والـattempt من الماضي فقط.
engine = AcademicPlanRecommender.load(num_threads=4)
prepared = engine.prepare_candidates(snapshot, candidates, PART)
prepared.to_parquet(OUT / '03_prepared_candidates.parquet', index=False)
check('Both frozen histories stop at 20243',
      engine.course_history.as_of_part == engine.specialty_history.as_of_part == 20243)
check('No supplied outcome columns reach prepared candidates', not set(LEAKAGE_COLUMNS).intersection(prepared.columns))
show(prepared[['course_id', 'course_name', *[c for c in CANDIDATE_COURSE_COLUMNS if c != 'course_id']]])
show(prepared[['course_id', *COURSE_HISTORY_COLUMNS]])
show(prepared[['course_id', *SPECIALTY_HISTORY_FEATURES]])
print('Course + specialty cutoff:', engine.course_history.as_of_part,
      '/ أقصى فصل لمحاولات الطالب:', import_report['history_latest_part'])
# Check all seven course-history values against the actual selected aggregate and formula.
keys = build_history_keys(prepared)
history_math = []
for i, row in prepared.iterrows():
    level = int(row.course_history_fallback_level)
    sums = engine.course_history.global_sums if level == 6 else engine.course_history.tables[level].loc[keys[level].iloc[i]].to_dict()
    support = sums['effective_support']
    for feature, field in [('course_history_avg_mark', 'mark_sum'), ('course_history_fail_rate', 'fail_sum'),
                           ('course_history_avg_attempt', 'attempt_sum'), ('course_history_retake_rate', 'retake_sum')]:
        global_mean = engine.course_history.global_sums[field] / engine.course_history.global_sums['effective_support']
        expected = global_mean if level == 6 else (sums[field] + engine.course_history.smoothing_k * global_mean) / (support + engine.course_history.smoothing_k)
        np.testing.assert_allclose(row[feature], expected, rtol=0, atol=1e-12)
        history_math.append({'course_id': row.course_id, 'feature': feature, 'level': level,
            'key': 'global' if level == 6 else keys[level].iloc[i], 'weighted_sum': sums[field],
            'support': support, 'global_mean': global_mean, 'smoothing_k': engine.course_history.smoothing_k,
            'calculated_value': expected, 'production_value': row[feature]})
    assert row.course_history_effective_support == support
    assert row.course_history_missing == int(level >= 3 or support < engine.course_history.min_support)
check('Course history independently reconstructed for all 15 courses', True)
save_json('03_course_history_math.json', history_math)
print('الحساب عند وجود تاريخ محلي: (weighted_sum + 20 × global_mean) / (support + 20).')
print('اختيار المستوى يعتمد وجود التاريخ؛ support أقل من 20 يرفع missing ولا يمنع استخدامه.')
show(pd.DataFrame(history_math).head(4))

# %% 4. توليد كل الخطط ضمن 12–18 ساعة وفحص العدد مستقلاً
# لا نأخذ أول N خطة: نعد جميع subsets ونطابقها مع combinations مستقلة.
plans = list(enumerate_plan_indices(prepared, min_credits=MIN_CREDITS, max_credits=MAX_CREDITS))
credit_values = [Decimal(str(v)) for v in prepared.course_credits]
oracle = {p for size in range(1, len(prepared) + 1)
          for p in combinations(range(len(prepared)), size)
          if Decimal(MIN_CREDITS) <= sum((credit_values[i] for i in p), Decimal(0)) <= Decimal(MAX_CREDITS)}
check('Enumeration matches independent combinations exactly, with no duplicates', set(plans) == oracle and len(plans) == len(oracle))
plan_menu = pd.DataFrame([{'plan_id': n, 'course_count': len(p),
    'total_credits': float(sum(credit_values[i] for i in p)),
    'course_ids': prepared.iloc[list(p)].course_id.tolist()} for n, p in enumerate(plans)])
plan_menu.to_parquet(OUT / '04_all_plan_membership.parquet', index=False)
print('عدد جميع المجموعات غير الفارغة =', 2 ** len(prepared) - 1)
print('عدد الخطط المطابقة للمجال =', len(plans))
show(plan_menu.groupby('total_credits', as_index=False).agg(plan_count=('plan_id', 'size')))
print('الخطة رقم 0 هي أول خطة في ترتيب التوليد، وليست الأفضل:')
show(build_plan_rows(prepared, plans[:1])[['plan_id', 'course_id', 'course_name', 'course_credits']])

# %% 5. تنفيذ recommend الفعلي والتقاط صفوف البيانات عند score_rows
# اعتراض محلي للاستدعاء بغرض التسجيل فقط؛ كل القيم ناتجة عن الدالة الأصلية نفسها.
original_score_rows = engine.score_rows
captured = []
def capture_score_rows(rows):
    scored = original_score_rows(rows)
    captured.append(scored)
    return scored
engine.score_rows = capture_score_rows
try:
    accepted, result = engine.recommend(snapshot, candidates, PART, snapshot['start_agpa_points'],
        min_credits=MIN_CREDITS, max_credits=MAX_CREDITS, batch_size=2000)
finally:
    engine.score_rows = original_score_rows
all_scored = pd.concat(captured, ignore_index=True)
all_scored.to_parquet(OUT / '05_all_scored_rows_and_features.parquet', index=False)
accepted.to_parquet(OUT / '05_accepted_plans.parquet', index=False)
save_json('05_result_before_observed_outcomes.json', result)
sealed_hash = sha256((OUT / '05_result_before_observed_outcomes.json').read_bytes()).hexdigest()
check('Real recommend enumerated exactly the independently verified plan count', result['matching_plan_count'] == len(plans))
check('All model outputs finite and within their contracts',
      np.isfinite(all_scored[['expected_points', 'fail_probability']].to_numpy()).all()
      and all_scored.expected_points.between(0, 4).all() and all_scored.fail_probability.between(0, 1).all())
unfiltered = all_scored.assign(quality=all_scored.course_credits * all_scored.expected_points,
    failed=all_scored.course_credits * all_scored.fail_probability).groupby('plan_id', sort=False).agg(
    total_credits=('course_credits', 'sum'), expected_quality_points=('quality', 'sum'),
    expected_failed_credits=('failed', 'sum')).reset_index()
unfiltered['expected_plan_gpa'] = unfiltered.expected_quality_points / unfiltered.total_credits
unfiltered['accepted'] = unfiltered.expected_plan_gpa.gt(snapshot['start_agpa_points'])
check('Acceptance is exactly expected semester GPA > current GPA',
      set(unfiltered.loc[unfiltered.accepted, 'plan_id']) == set(accepted.plan_id))
unfiltered.to_parquet(OUT / '05_all_plan_scores_including_rejected.parquet', index=False)
print('صفوف التنبؤ =', len(all_scored), '/ دفعات =', len(captured))
print('خطط مقبولة =', result['accepted_plan_count'], '/ مستبعدة بعد التنبؤ =', len(plans) - result['accepted_plan_count'])
print('الشرط الفعلي:', 'expected_plan_gpa >', snapshot['start_agpa_points'])
print('أوزان المودلين وإحصاءات التاريخ لم تتحدث أثناء هذه العملية.')

# %% 6. حساب سياق خطة واحدة ثم رؤية الـ57 feature عند مدخل المودل
# نبقي هوية المادة ثابتة ونغيّر رفاقها في الخطة لرؤية ما الذي يتغير فعلاً.
example = all_scored.loc[all_scored.plan_id.eq(0)].copy().reset_index(drop=True)
focal = example.iloc[0]
weights = example.course_credits.to_numpy(float)
manual = {'plan_course_count': len(example), 'plan_total_credits': weights.sum(),
          'peer_course_count': len(example) - 1, 'peer_total_credits': weights[1:].sum()}
for label, column in [('fail_rate', 'course_history_fail_rate'), ('avg_mark', 'course_history_avg_mark'), ('avg_attempt', 'course_history_avg_attempt')]:
    values = example[column].to_numpy(float)
    manual['plan_credit_weighted_' + label] = np.average(values, weights=weights)
    manual['peer_credit_weighted_' + label] = np.average(values[1:], weights=weights[1:])
manual.update(plan_difficulty_credit_load=float(np.dot(weights, example.course_history_fail_rate)),
    peer_difficulty_credit_load=float(np.dot(weights[1:], example.course_history_fail_rate.iloc[1:])),
    peer_max_fail_rate=float(example.course_history_fail_rate.iloc[1:].max()), peer_difficulty_missing=0)
for name in PLAN_CONTEXT_COLUMNS:
    np.testing.assert_allclose(focal[name], manual[name], rtol=0, atol=1e-10)
check('All 14 context features independently verified for focal course in plan 0', True)
show(pd.DataFrame([{'feature': n, 'manual_value': manual[n], 'code_value': focal[n]} for n in PLAN_CONTEXT_COLUMNS]))
print('plan_total_credits = مجموع ساعات الخطة؛ peer_total_credits = المجموع ناقص ساعات المادة الحالية.')
print('المتوسطات موزونة بالساعات؛ difficulty_credit_load يستخدم فشل التاريخ المجمد، لا تنبؤ fail_model.')
contract = engine.metadata['feature_contract']
matrix = prepare_matrix(example, contract['numeric_features'], contract['categorical_features'], engine.points_levels)
fail_matrix = prepare_model_matrix(example, engine.fail_levels)
check('Model column order matches real artifacts: 57 points / 47 failure',
      list(matrix) == engine.points_model.feature_name() and len(matrix.columns) == 57
      and list(fail_matrix) == engine.fail_model.feature_name() and len(fail_matrix.columns) == 47)
def family(column):
    if column in PLAN_CONTEXT_COLUMNS: return '14: يعاد حسابها لكل خطة'
    if column in SPECIALTY_HISTORY_FEATURES: return '10: تاريخ الاختصاص المجمد'
    if column in COURSE_HISTORY_COLUMNS: return '7: تاريخ المادة المجمد'
    if column in CANDIDATE_COURSE_COLUMNS: return '7: المادة وموضعها في المنهاج ومحاولتها'
    if column == 'part_semester': return '1: رقم الفصل داخل السنة'
    return '18: حالة الطالب قبل الفصل'
feature_trace = pd.DataFrame([{'position': i + 1, 'feature': c, 'family': family(c),
    'before_matrix': example[c].iloc[0], 'model_value': matrix[c].iloc[0], 'dtype': str(matrix[c].dtype),
    'category_code': int(matrix[c].cat.codes.iloc[0]) if isinstance(matrix[c].dtype, pd.CategoricalDtype) else None,
    'used_by_fail_model': c in fail_matrix} for i, c in enumerate(matrix)])
show(feature_trace)
save_json('06_feature_trace_plan_0.json', records(feature_trace))
matrix.to_parquet(OUT / '06_points_matrix_plan_0.parquet', index=False)
fail_matrix.to_parquet(OUT / '06_fail_matrix_plan_0.parquet', index=False)
show(example[['course_id', 'course_name', 'course_credits', 'expected_points', 'fail_probability']].assign(
    quality_points=example.course_credits * example.expected_points))
show(unfiltered.loc[unfiltered.plan_id.eq(0)])
same_course = all_scored.loc[all_scored.course_id.eq(focal.course_id)]
low, high = same_course.expected_points.idxmin(), same_course.expected_points.idxmax()
context_change = all_scored.loc[[low, high], ['plan_id', 'course_id', 'plan_course_count', 'plan_total_credits',
    'peer_total_credits', 'peer_credit_weighted_fail_rate', 'expected_points', 'fail_probability']]
print('نفس المادة ضمن خطتين مختلفتين؛ اختلاف التنبؤ ناتج عن سياق الخطة:')
show(context_change)
save_json('06_same_course_different_plans.json', records(context_change))

# %% 7. مطابقة التتبع مع CLI الحقيقي دون --snapshot
import subprocess
cli_dir = OUT / 'cli'
command = [sys.executable, '-B', '-m', 'src.recommend_local', '--candidates', str(candidate_path),
    '--student-id', SID, '--degree-id', DID, '--part-id', str(PART),
    '--min-credits', str(MIN_CREDITS), '--max-credits', str(MAX_CREDITS), '--output-dir', str(cli_dir)]
process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
(OUT / '07_cli.log').write_text(process.stdout + process.stderr, encoding='utf-8')
check('Actual local CLI without --snapshot exits successfully', process.returncode == 0)
cli_result = json.loads((cli_dir / 'result.json').read_text(encoding='utf-8'))
pd.testing.assert_frame_equal(accepted, pd.read_parquet(cli_dir / 'plans.parquet'))
check('Every accepted plan and score match CLI exactly', True)
check('CLI top five details match the trace exactly', result['recommendations'] == cli_result['recommendations'])
print(process.stdout)
print('التوصيات محفوظة ومثبتة قبل فتح النتائج الفعلية. SHA256:', sealed_hash)

# %% 8. الآن: ماذا سجل الطالب فعلياً وما نتائج خطته؟
# أول قراءة لصفوف نتائج 20251 بهدف التقييم؛ لا نعيد اختيار المودل أو تعديل التوصيات.
actual = history.loc[history.student_id.eq(SID) & history.degree_id.eq(DID) & history.part_id.eq(PART)].copy()
roster = pd.read_parquet(paths.TEMPORAL_TEST_ROSTER_PATH)
roster = roster.loc[roster.student_id.eq(SID) & roster.degree_id.eq(DID) & roster.part_id.eq(PART)]
check('All actual registered courses have observed outcomes', set(roster.student_course_id) == set(actual.student_course_id))
actual['in_supplied_candidates'] = actual.course_id.isin(candidates.course_id)
show(actual[['course_id', 'course_name_sl', 'course_credits', 'final_mark', 'points', 'attempt_number', 'in_supplied_candidates']])
print('المسجل فعلياً:', len(actual), 'مواد /', actual.course_credits.sum(), 'ساعة.')
missing_actual = actual.loc[~actual.in_supplied_candidates, 'course_id'].tolist()
print('مواد مسجلة فعلياً غير موجودة ضمن قائمة الطلب:', missing_actual)
eligibility_comparison = []
for term in [20251, 20252]:
    term_actual = history.loc[history.student_id.eq(SID) & history.degree_id.eq(DID) & history.part_id.eq(term)]
    eligibility_comparison.append({'part_id': term, 'observed_course_count': len(term_actual),
        'in_supplied_candidates': int(term_actual.course_id.isin(candidates.course_id).sum()),
        'missing_from_supplied_candidates': int((~term_actual.course_id.isin(candidates.course_id)).sum())})
show(pd.DataFrame(eligibility_comparison))
save_json('08_eligibility_semester_comparison.json', eligibility_comparison)
print('مطابقة مواد فصل آخر قرينة تستدعي مراجعة تشغيل procedure؛ لا تثبت وحدها تاريخ أهلية القائمة.')
target_status = student_status.loc[student_status.degree_id.eq(DID) & student_status.part_id.eq(PART)].iloc[0]
export_end_gpa = float(raw.END_AGPA_POINTS.dropna().iloc[0])
eligibility_diagnosis = {
    'procedure_called_with_20251_user_confirmed': True,
    'actual_20251_courses': len(actual), 'actual_20251_missing_from_export': len(missing_actual),
    'xml_end_agpa_points': export_end_gpa,
    'start_20251_agpa_points': float(target_status.start_agpa_points),
    'end_20251_agpa_points': float(target_status.end_agpa_points),
    'observation': 'All 8 actual 20251 courses absent, all 7 actual 20252 courses present; XML end AGPA equals end-20251 AGPA.',
    'hypothesis_not_proven': 'Procedure may use current or end-of-target-term progress instead of start-of-target-term progress, or its term parameter has a different contract.',
    'needed_to_confirm': 'Procedure definition and its status, passed-course and prerequisite queries; no procedure definition was found in this project.',
    'evaluation_limit': 'This run validates code execution; it is not a validated historical eligibility backtest for 20251.'}
save_json('08_eligibility_diagnosis.json', eligibility_diagnosis)
show(pd.DataFrame([{'source': 'بداية 20251 من حالة الطالب', 'AGPA': float(target_status.start_agpa_points)},
                  {'source': 'نهاية 20251 من حالة الطالب', 'AGPA': float(target_status.end_agpa_points)},
                  {'source': 'END_AGPA_POINTS في XML', 'AGPA': export_end_gpa}]))
print('مؤكد: اختلاف قائمة الأهلية عن المواد المسجلة. غير محسوم: الاستعلام الداخلي المسؤول؛ تعريف procedure غير موجود في المشروع.')
# Evaluate the observed plan even if its courses are outside the supplied eligible pool.
# This is a separate evaluation path, and never augments the recommendation candidates.
observed_candidates, observed_import = normalize_candidates(actual[['course_id', 'course_credits']],
    pd.read_parquet(paths.CLEAN_DEGREE_COURSE_PATH), history, SID, DID, PART)
observed_prepared = engine.prepare_candidates(snapshot, observed_candidates, PART)
observed_scored = engine.score_rows(build_plan_rows(observed_prepared, [tuple(range(len(observed_prepared)))], -1))
comparison = observed_scored[['course_id', 'expected_points', 'fail_probability']].merge(actual,
    on='course_id', validate='one_to_one')
comparison['point_error'] = comparison.expected_points - comparison.points
actual_gpa = float(np.average(comparison.points, weights=comparison.course_credits))
predicted_gpa = float(np.average(comparison.expected_points, weights=comparison.course_credits))
actual_metrics = {'actual_course_count': len(actual), 'actual_credits': float(actual.course_credits.sum()),
    'actual_credit_weighted_plan_gpa': actual_gpa, 'predicted_plan_gpa_for_actual_registration': predicted_gpa,
    'absolute_gpa_error': abs(actual_gpa - predicted_gpa), 'course_points_mae': float(comparison.point_error.abs().mean()),
    'actual_failed_credits': float(actual.loc[actual.final_mark.lt(50), 'course_credits'].sum()),
    'expected_failed_credits': float(np.dot(comparison.course_credits, comparison.fail_probability)),
    'actual_courses_missing_from_candidate_list': missing_actual}
show(comparison[['course_id', 'course_name_sl', 'course_credits', 'points', 'expected_points', 'point_error', 'fail_probability']])
show(pd.DataFrame([actual_metrics]).drop(columns='actual_courses_missing_from_candidate_list'))
comparison.to_parquet(OUT / '08_actual_registration_evaluation.parquet', index=False)
save_json('08_actual_metrics.json', actual_metrics)
# Reconstruct saved holdout features for the SAME observed course set.
reference = pd.read_parquet(paths.TEMPORAL_TEST_FEATURES_PATH)
reference = reference.loc[reference.student_id.eq(SID) & reference.degree_id.eq(DID) & reference.part_id.eq(PART)]
reference = engine.specialty_history.apply(reference).sort_values('course_id').reset_index(drop=True)
observed_matrix = prepare_matrix(observed_scored, contract['numeric_features'], contract['categorical_features'], engine.points_levels)
reference_matrix = prepare_matrix(reference, contract['numeric_features'], contract['categorical_features'], engine.points_levels)
pd.testing.assert_frame_equal(observed_matrix, reference_matrix, check_exact=False, rtol=1e-6, atol=1e-6)
pd.testing.assert_frame_equal(prepare_model_matrix(observed_scored, engine.fail_levels),
    prepare_model_matrix(reference, engine.fail_levels), check_exact=False, rtol=1e-6, atol=1e-6)
check('All observed-plan features match existing holdout: 57 points and 47 fail inputs', True)
saved = pd.read_parquet(paths.DEGREE_POINTS_HOLDOUT_COURSES_PATH)
saved = saved.loc[saved.student_id.eq(SID) & saved.degree_id.eq(DID) & saved.part_id.eq(PART)]
parity = comparison.merge(saved[['student_course_id', 'predicted_points']], on='student_course_id', validate='one_to_one')
check('Observed plan predictions match saved holdout predictions',
      len(parity) == len(actual) and np.allclose(parity.expected_points, parity.predicted_points, rtol=0, atol=1e-10))
check('Observed outcomes did not modify the sealed recommendations',
      sha256((OUT / '05_result_before_observed_outcomes.json').read_bytes()).hexdigest() == sealed_hash)

# %% 9. أفضل توصيات المودل والمقارنة مع التسجيل الفعلي
# هذه تقديرات لخطط بديلة؛ نتيجة المادة ضمن خطة فعلية ليست حقيقة تجريبية للخطة البديلة.
show(accepted.head(5))
if result['recommendations']:
    best = result['recommendations'][0]
    best_courses = pd.DataFrame(best['courses'])
    best_courses['also_in_actual_registration'] = best_courses.course_id.isin(actual.course_id)
    print('مواد التوصية الأولى:')
    show(best_courses)
    print('فرق معدل الخطة المتوقع عن المعدل التراكمي الحالي =', best['gpa_gain'])
    print('هذا الفرق ليس مقدار التحسن الفعلي في المعدل التراكمي بعد الفصل.')
    actual_members = set(actual.course_id)
    match = plan_menu.loc[plan_menu.course_ids.map(lambda ids: set(ids) == actual_members)]
    actual_plan_ids = match.plan_id.tolist()
    print('رقم الخطة الفعلية ضمن التوليد (إن كانت كلها في الطلب):', actual_plan_ids)
    if actual_plan_ids:
        show(unfiltered.loc[unfiltered.plan_id.isin(actual_plan_ids)])
        ranks = accepted.reset_index().rename(columns={'index': 'zero_based_rank'})
        print('ترتيب الخطة الفعلية بين المقبول:', (ranks.loc[ranks.plan_id.isin(actual_plan_ids), 'zero_based_rank'] + 1).tolist())
    print('الفرز: expected_plan_gpa تنازلياً، ثم expected_failed_credits تصاعدياً، ثم plan_id.')
else:
    print('لم توجد خطة تتجاوز عتبة المعدل الحالي؛ لا نختلق توصية.')
    best_rejected = unfiltered.sort_values(['expected_plan_gpa', 'expected_failed_credits', 'plan_id'],
                                           ascending=[False, True, True]).head(5).copy()
    best_rejected['gap_to_current_gpa'] = best_rejected.expected_plan_gpa - snapshot['start_agpa_points']
    print('للتشخيص فقط: أعلى خمس خطط قبل الفلترة؛ كلها مستبعدة وليست توصيات صادرة من النظام.')
    show(best_rejected)
    best_rejected_id = int(best_rejected.iloc[0].plan_id)
    best_rejected_courses = all_scored.loc[all_scored.plan_id.eq(best_rejected_id),
        ['plan_id', 'course_id', 'course_name', 'course_credits', 'expected_points', 'fail_probability']]
    print('مواد أعلى خطة مستبعدة، رقم', best_rejected_id, ':')
    show(best_rejected_courses)
    save_json('09_best_rejected_plans.json', records(best_rejected))
    save_json('09_best_rejected_courses.json', records(best_rejected_courses))
print('تقييم الدقة هنا يخص الخطة الفعلية لطالب واحد فقط. جودة ترتيب الخطط البديلة لا تُحسم بهذه المقارنة.')
print('تنفيذ الطلب الحالي تشخيص لمسار الكود؛ لا يُعتمد كاختبار أهلية تاريخي صحيح لـ20251 قبل حل اختلاف القائمة.')

# %% 10. أدلة التنفيذ وحدود الاستنتاج ونقاط التوقف للمراجعة
source_functions = [load_local_inputs, normalize_candidates, build_student_snapshot,
    add_student_history_features, AcademicPlanRecommender.load, AcademicPlanRecommender.prepare_candidates,
    enumerate_plan_indices, build_plan_rows, compute_plan_context_features,
    AcademicPlanRecommender.score_rows, AcademicPlanRecommender.recommend]
save_json('10_source_functions.json', [source(fn) for fn in source_functions])
source_paths = sorted({Path(inspect.getfile(fn)).resolve() for fn in source_functions})
source_paths += [paths.STUDENT_STATUS_PATH, paths.CLEAN_STUDENT_COURSE_PATH,
    paths.CLEAN_DEGREE_COURSE_PATH, paths.CLEAN_STUDENT_DIPLOMA_PATH,
    paths.COURSE_HISTORY_STATE_PATH, paths.TEMPORAL_TRAIN_FEATURES_PATH,
    paths.DEGREE_POINTS_EXPERIMENT_METADATA_PATH, paths.MODEL_METADATA_PATH]
provenance = {'created_at_utc': datetime.now(timezone.utc).isoformat(),
    'model': engine.provenance, 'sources': {str(p): sha256(p.read_bytes()).hexdigest() for p in source_paths},
    'recommendation_result_sha256_before_evaluation': sealed_hash,
    'xml_sources_unchanged': all(sha256((Path.home() / 'Downloads' / a['file']).read_bytes()).hexdigest() == a['sha256'] for a in audit)}
check('All original XML source files unchanged', provenance['xml_sources_unchanged'])
save_json('10_provenance.json', provenance)
save_json('10_checks.json', checks)
show(pd.DataFrame(checks))
show(pd.DataFrame([{k: v for k, v in source(fn).items() if k != 'code'} for fn in source_functions]))
print('فحوص التتبع الناجحة:', len(checks))
print('الملفات الأصلية ومنطق المودل محفوظة. تاريخ أهلية المقررات يعتمد توثيق تشغيل procedure؛ PART_ID فارغ في الملف المختار.')
print('الخطط تحقق قائمة المواد ومجال الساعات؛ الكود لا يفحص تعارض المواعيد أو شروط اختيار مجموعات المواد.')
print('تفاصيل كل صف وكل خطة محفوظة في:', OUT)
