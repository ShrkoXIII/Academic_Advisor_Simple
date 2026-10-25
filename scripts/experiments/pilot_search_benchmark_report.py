"""Verify and summarize a saved offline search run without selecting candidates.

Run only after search completion. Oracle rankings are consumed exclusively for
evaluation here; this module is never imported by the selectors or Pilot.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean, median
import xml.etree.ElementTree as ET

from tools.recommendation_pilot_20251.adapter import sha256
from tools.recommendation_pilot_20251.search_benchmark import (
    ResourceLimits, ScoreLedger, SearchBenchmarkService, atomic_json, canonical_plan_id,
    prepare_context, ranking_key, score_chunk,
)


def verify_and_summarize(service, run_id, audit_directory):
    saved = service.load_run(run_id)  # Checks every sealed JSON/CSV/SQLite hash.
    directory = Path(saved['storage_path'])
    students = saved['student_results']
    manifest = saved['run_manifest']
    proofs, pool_checks, comparisons, cross_model = [], [], [], []
    for student in students:
        sample = student['sample_id']
        if not student.get('experiments'):
            continue
        ledger = ScoreLedger(directory / sample / 'scores.sqlite', student['fingerprint'])
        try:
            for experiment in student['experiments']:
                scope, strategy, budget, model = (experiment[k] for k in ('scope', 'strategy', 'budget', 'model'))
                job = f'{scope}/{strategy}/{budget}/{model}'
                proof = ledger.verify(job, exhaustive=scope == 'EXHAUSTIVE')
                assert proof['unique_scored_count'] == experiment['evaluated_plans']
                for plan in experiment['top_plans']:
                    assert plan['canonical_id'] == canonical_plan_id(c['course_id'] for c in plan['courses'])
                    assert plan['total_credits'] == experiment['target_credits']
                    assert plan['enforceable_constraints_validated']
                if scope == 'EXHAUSTIVE':
                    complete = (experiment['status'] == 'EXHAUSTIVE_COMPLETE')
                    assert complete == (proof['unique_scored_count'] == student['feasible_plan_count'])
                    proofs.append(dict(sample_id=sample, model=model, complete=complete,
                        feasible_count=student['feasible_plan_count'], **proof))
                else:
                    selection = json.loads((directory / sample / f'{scope}_{strategy}_{budget}.json').read_text(encoding='utf8'))
                    assert len(selection['canonical_ids']) == len(set(selection['canonical_ids']))
                    assert experiment['evaluated_plans'] <= budget
                    if scope == 'FIXED_POOL':
                        pool = json.loads((directory / sample / 'reference_pool.json').read_text(encoding='utf8'))
                        assert set(selection['canonical_ids']) <= {p['canonical_id'] for p in pool['plans']}
                comparisons.append(dict(sample_id=sample, **{k: experiment[k] for k in (
                    'scope', 'strategy', 'budget', 'model', 'target_credits', 'evaluated_plans', 'best_gpa',
                    'oracle_gpa', 'gpa_gap', 'top3_recall', 'score_equivalent_top3_recall',
                    'oracle_equivalent_top1', 'standalone_runtime_seconds', 'status')}))
            for model in manifest['configuration']['models']:
                full_pool = [e for e in student['experiments'] if e['scope'] == 'FIXED_POOL' and e['budget'] == 2000 and e['model'] == model]
                identities = [[p['canonical_id'] for p in e['top_plans']] for e in full_pool]
                assert all(value == identities[0] for value in identities)
                pool_checks.append(dict(sample_id=sample, model=model, identical_top3_at_2000=True))
            oracles = {e['model']: e for e in student['experiments'] if e['scope'] == 'EXHAUSTIVE'}
            if {'B', 'C'} <= set(oracles):
                first, second = oracles['B']['top_plans'], oracles['C']['top_plans']
                b = {c['course_id'] for c in first[0]['courses']}
                c = {c['course_id'] for c in second[0]['courses']}
                cross_model.append(dict(sample_id=sample, same_top1=first[0]['canonical_id'] == second[0]['canonical_id'],
                    top1_jaccard=len(b & c) / len(b | c), top1_shared_courses=len(b & c),
                    top3_exact_intersection=len({p['canonical_id'] for p in first} & {p['canonical_id'] for p in second})))
        finally:
            ledger.close()
    aggregates = []
    for scope in ('FIXED_POOL', 'FULL_SPACE'):
        for model in ('B', 'C'):
            for budget in (200, 1000, 2000):
                for strategy in ('FIRST_N', 'DIVERSE_N', 'SMART_SEARCH'):
                    for population in ('all_five', 'space_over_2000'):
                        rows = [e for s in students for e in s.get('experiments', [])
                            if e['scope'] == scope and e['model'] == model and e['budget'] == budget
                            and e['strategy'] == strategy and e['oracle_complete']
                            and (population == 'all_five' or s['feasible_plan_count'] > 2000)]
                        if not rows:
                            continue
                        aggregates.append(dict(scope=scope, model=model, budget=budget, strategy=strategy,
                            population=population, student_count=len(rows), mean_gap=mean(e['gpa_gap'] for e in rows),
                            max_gap=max(e['gpa_gap'] for e in rows), equivalent_best_count=sum(e['oracle_equivalent_top1'] for e in rows),
                            mean_exact_recall=mean(e['top3_recall'] for e in rows),
                            mean_score_recall=mean(e['score_equivalent_top3_recall'] for e in rows),
                            mean_jaccard=mean(e['diversity']['mean_jaccard'] for e in rows if e['diversity']['mean_jaccard'] is not None),
                            median_standalone_seconds=median(e['standalone_runtime_seconds'] for e in rows),
                            median_job_seconds=median(e['runtime_seconds'] for e in rows)))
    result = dict(run_id=run_id, status=manifest['status'], oracle_proofs=proofs,
        full_pool_checks=pool_checks, aggregated_metrics=aggregates, bc_oracle_comparison=cross_model,
        total_plan_model_evaluations=sum(e['evaluated_plans'] for s in students for e in s.get('experiments', [])),
        experiment_rows=len(comparisons), cumulative_wall_seconds=manifest['cumulative_attempt_wall_seconds'],
        peak_process_memory_mb=manifest['peak_process_memory_mb'])
    atomic_json(audit_directory / 'verified_results.json', result)
    with (audit_directory / 'aggregate_comparison.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(aggregates[0]))
        writer.writeheader()
        writer.writerows(aggregates)
    return result


def verify_protected(audit_directory):
    before = json.loads((audit_directory / 'protected_before.json').read_text(encoding='utf8'))
    changed = []
    for filename, evidence in before.items():
        path = Path(filename)
        if not path.is_file() or sha256(path) != evidence['sha256'] or path.stat().st_size != evidence['bytes']:
            changed.append(filename)
    result = dict(status='PASS' if not changed else 'FAIL', files_checked=len(before), changed=changed,
        baseline_sha256=sha256(audit_directory / 'protected_before.json'))
    atomic_json(audit_directory / 'protected_after.json', result)
    assert not changed, changed
    return result


def verify_prediction_parity(service, run_id, audit_directory, sample):
    """Compare real B/C pathways with different batch sizes on identical plans."""
    from tools.recommendation_pilot_20251.engine import PilotEngine
    from tools.recommendation_pilot_20251.snapshots import AFTER
    student = next(s for s in service.cohort() if s['sample_id'] == sample)
    engine = PilotEngine(root=service.root, snapshot_id=AFTER)
    original = engine.evaluate_student(student, max_plans=200, models=['B', 'C'])
    assert original['status'] == 'PREDICTION_AVAILABLE', original['issues']
    context = prepare_context(student, service.root, engine, ResourceLimits())
    selection = context.space.select('FIRST_N', 200)
    saved = service.load_run(run_id)
    saved_student = next(s for s in saved['student_results'] if s['sample_id'] == sample)
    evidence = []
    for model in ('B', 'C'):
        plans = []
        for start in range(0, len(selection.plans), 64):
            chunk, _ = score_chunk(context.base, selection.plans[start:start + 64],
                selection.ranks[start:start + 64], context.scorer, model)
            plans.extend(chunk)
        expected = original['experiments'][model]['diagnostic_plans']
        assert len(plans) == len(expected) == len(selection.plans)
        for new, old in zip(plans, expected):
            assert {k: v for k, v in new.items() if k not in ('canonical_id', 'enforceable_constraints_validated')} == old
        top_ids = [p['canonical_id'] for p in sorted(plans, key=ranking_key)[:3]]
        historical = next(e for e in saved_student['experiments']
            if e['model'] == model and e['scope'] == 'FULL_SPACE' and e['strategy'] == 'FIRST_N' and e['budget'] == 200)
        assert top_ids == [p['canonical_id'] for p in historical['top_plans']]
        by_course = {}
        for plan in plans:
            for course in plan['courses']:
                by_course.setdefault(course['course_id'], set()).add((course['predicted_mark'], course['fail_probability']))
        evidence.append(dict(model=model, plans_compared=len(plans),
            course_predictions_compared=sum(len(p['courses']) for p in plans),
            all_prediction_and_score_fields_exactly_equal=True, saved_run_top3_exactly_equal=True,
            chunk_size=64, original_batch_size=len(plans),
            courses_with_composition_dependent_predictions=sum(len(v) > 1 for v in by_course.values())))
    result = dict(status='PASS', sample_id=sample, models=evidence,
        separate_verification_plan_model_evaluations=4 * len(selection.plans),
        note='Independent parity audit; additional verification cost is outside benchmark rows.')
    atomic_json(audit_directory / 'prediction_parity.json', result)
    return result


def write_results_report(service, run_id, audit_directory):
    """Append measured evidence to the reviewed design, preserving its contract."""
    # Narrative includes this fixed cohort's observed cases and attempt costs.
    # Other runs can be verified/summarized but must not inherit those claims.
    if run_id != 'benchmark_20261024T120117_4a7c2fc8':
        raise ValueError('The measured narrative is specific to the audited 2026-10-24 run.')
    saved = service.load_run(run_id)
    verified = json.loads((audit_directory / 'verified_results.json').read_text(encoding='utf8'))
    manifest = saved['run_manifest']
    students = saved['student_results']
    assert manifest['status'] == 'completed' and len(manifest['attempts']) == 2
    assert len(students) == 5 and verified['experiment_rows'] == 190
    assert len(verified['oracle_proofs']) == 10 and all(p['complete'] for p in verified['oracle_proofs'])
    lines = ['## 10. النتائج المقاسة والقرار', '',
        f"التشغيل المعتمد: `{run_id}`، حالته `{manifest['status']}`. يحتوي **190 صف مقارنة و10 Oracles مكتملة** "
        f"على خمسة طلاب. إجمالي التقييمات الكاملة للخطة/المودل **{verified['total_plan_model_evaluations']:,}**؛ "
        'يشمل ذلك إعادة تقييم العينات استقلاليًا لكل ميزانية ونطاق، ولا يمثل ميزانية تجربة واحدة.', '',
        'القرار العام لتعميم أفضل استراتيجية على الثلاثين: **INCONCLUSIVE**؛ العينة صغيرة والبذرة الوحيدة 42. '
        'في العينة الحالية، `SMART_SEARCH/1000` اختيار تجريبي واعد: وجد GPA مكافئًا للأفضل لدى الطلاب الخمسة بالنموذجين، '
        'ومقابل 2000 يقلل التقييمات إلى النصف في الفضاءات الأكبر من 2000. '
        'لا تكفي ميزانية 200 دائمًا، ولا يكفي رفع `FIRST_N` إلى 2000 لإزالة انحياز البادئة.', '',
        '### العينة وإثبات Oracle', '',
        '| Student | GPA البداية من المصدر | المرشحون | الهدف API | الفضاء الكامل | Oracle B | Oracle C |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for student in students:
        oracle = {e['model']: e for e in student['experiments'] if e['scope'] == 'EXHAUSTIVE'}
        lines.append(f"| {student['sample_id']} | {student['student_summary']['previous_gpa']:g} | "
            f"{len(student['candidate_order'])} | {student['target_resolution']['target_credits']:g} | "
            f"{student['feasible_plan_count']:,} | {oracle['B']['best_gpa']:.8f} | {oracle['C']['best_gpa']:.8f} |")
    lines += ['', 'في كل Oracle تطابق `unique_scored_count` مع العدد المحسوب مسبقًا، وكانت رتب DFS متصلة من صفر حتى العدد ناقص واحد. '
        'أعيد فحص سلسلة SHA-256 لكل سجل درجات، وعدم تكرار الرتب/الهويات، وتطابق أفضل ثلاث خطط مع ترتيب السجل الكامل. '
        'الأدلة التفصيلية: `audit_20261024/verified_results.json` و`oracle_summaries.json` و`integrity.json` وملفات `scores.sqlite`.', '',
        '### البحث العالمي: الفضاءات الثلاثة الأكبر من 2000', '',
        'المتوسطات التالية على `P20251-03-P01` و`P20251-04-P04` و`P20251-01-P02`. '
        'استُبعدت حالتا 1 و792 خطة من هذه المتوسطات لتجنب إخفاء أثر حجم الفضاء. '
        'Recall Exact يعني العثور على هوية oracle الحتمية، وScore يعني GPA مكافئًا مع احتساب تعدد التعادلات.', '',
        '| Model | Strategy | Budget | Mean Gap | Max Gap | أفضل مكافئ /3 | Recall Exact | Recall Score | Median seconds |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for row in verified['aggregated_metrics']:
        if row['scope'] == 'FULL_SPACE' and row['population'] == 'space_over_2000':
            lines.append(f"| {row['model']} | {row['strategy']} | {row['budget']} | {row['mean_gap']:.8f} | "
                f"{row['max_gap']:.8f} | {row['equivalent_best_count']} | {row['mean_exact_recall']:.3f} | "
                f"{row['mean_score_recall']:.3f} | {row['median_standalone_seconds']:.3f} |")
    lines += ['', '`SMART_SEARCH/200` أخفق في الوصول لأفضل GPA لدى `P20251-03-P01` بالنموذجين (Gap=0.04166667)، '
        'بينما حقق `DIVERSE_N/200` أفضل GPA لـC عند الطالب نفسه. عند B/200 كان Smart صاحب أقل متوسط regret؛ '
        'عند C/200 كان Diverse أفضل. عند B/1000 تعادل First وSmart في أفضل GPA؛ وعند C/1000 تعادل Diverse وSmart. '
        'عند 2000 تعادلت الطرق الثلاث في GPA لـB، وتعادل Diverse وSmart لـC. '
        'في Top-3 Exact ظل Smart/2000 أفضل في هذه العينة. لا تعني هذه النتائج تفوقًا عامًا مضمونًا.', '',
        'حالة حاسمة خارج البادئة: الطالب `P20251-04-P04`، مودل C، هدف 16 ساعة: '
        'أفضل GPA كامل هو 2.4375، وأفضل خططه رتبها 3256 و3382 و3214؛ جميعها خارج أول 2000. '
        '`FIRST_N/2000` بقي عند 2.40625 (Gap=0.03125)، بينما Smart وDiverse بميزانية 1000 وصلا إلى 2.4375. '
        'كما يثبت المثال الاصطناعي ذو 12,870 خطة أن Smart يصل للخطة ذات الرتبة 12,869 دون حصره في pool الأول.', '',
        '### تجربة FIXED_POOL — منفصلة عن الاستنتاج العالمي', '',
        '| Model | Strategy | Budget | Mean gap to global oracle | Recall Exact | Recall Score |',
        '|---|---|---:|---:|---:|---:|']
    for row in verified['aggregated_metrics']:
        if row['scope'] == 'FIXED_POOL' and row['population'] == 'space_over_2000':
            lines.append(f"| {row['model']} | {row['strategy']} | {row['budget']} | {row['mean_gap']:.8f} | "
                f"{row['mean_exact_recall']:.3f} | {row['mean_score_recall']:.3f} |")
    lines += ['', 'المقارنة هنا أيضًا مع oracle العالمي بعد انتهاء الاختيار، وليست oracle مفترضة للمجموعة. '
        'تطابقت هويات Top-3 للطرق الثلاث عند 2000 في الحالات الخمس ولكلا النموذجين (10 فحوص اتساق). '
        'بقاء regret لـC في المجموعة يؤكد أن ملء 2000 لا يثبت تغطية الفضاء العالمي.', '',
        '### اختلاف B/C وتنوع أفضل ثلاث خطط', '',
        '| Student | نفس Top 1؟ | Top-1 Jaccard B/C | مواد مشتركة | تقاطع هويات Top 3 |',
        '|---|---|---:|---:|---:|']
    for row in verified['bc_oracle_comparison']:
        lines.append(f"| {row['sample_id']} | {row['same_top1']} | {row['top1_jaccard']:.3f} | "
            f"{row['top1_shared_courses']} | {row['top3_exact_intersection']} |")
    lines += ['', 'باستثناء حالة الخطة الوحيدة، يفضل B وC مجموعات مختلفة؛ لا توجد هويات Top-3 مشتركة بينهما في الحالات الأربع الأخرى. '
        'داخل كل مودل تتراوح متوسطات Jaccard لأفضل ثلاث خطط oracle من 0.333 إلى 0.778؛ '
        'عدد من الخيارات متقارب جدًا، ولا يجوز عرضه بوصفه ثلاثة بدائل مستقلة تمامًا. '
        'تُحفظ أعداد المواد المشتركة لكل زوج في `diversity.pairs`، ولا تُستخدم لتغيير هدف GPA أو ترتيب Pilot.', '',
        '### أفضل ثلاث خطط في Oracle', '',
        'الهويات أدناه بادئات عرض؛ الهوية الكاملة والدرجات والنقاط والمخاطر لكل مادة محفوظة في JSON وتظهر في واجهة Streamlit. '
        'معدلات الخطط التالية فصلية متوقعة، وصلاحية التسجيل الرسمية غير متحققة.', '',
        '| Student | Model | Top | Canonical prefix | Credits | GPA | Expected failed credits | Max fail probability | Course IDs / Names |',
        '|---|---|---:|---|---:|---:|---:|---:|---|']
    for student in students:
        for oracle in (e for e in student['experiments'] if e['scope'] == 'EXHAUSTIVE'):
            for rank, plan in enumerate(oracle['top_plans'], 1):
                names = '; '.join(str(c['course_id']) + ': ' + str(c['course_name']).replace('|', '/').replace('\n', ' ')
                                  for c in plan['courses'])
                lines.append(f"| {student['sample_id']} | {oracle['model']} | {rank} | `{plan['canonical_id'][:16]}` | "
                    f"{plan['total_credits']:g} | {plan['expected_plan_gpa']:.8f} | {plan['expected_failed_credits']:.6f} | "
                    f"{plan['plan_difficulty_balance']['max_fail_probability']:.6f} | {names} |")
    lines += ['', '### الزمن والذاكرة والحالات غير المكتملة', '',
        f"استغرقت المحاولة الأولى {manifest['attempts'][0]['wall_seconds']:.3f} ثانية حتى حد 600 ثانية، "
        f"ثم الاستئناف {manifest['attempts'][1]['wall_seconds']:.3f} ثانية ضمن حد 180 ثانية؛ "
        f"الإجمالي {manifest['cumulative_attempt_wall_seconds']:.3f} ثانية. "
        'الحماية تعاونية بين الدفعات، ولذلك تجاوزت المحاولة الأولى الحد بنحو 2.76 ثانية. '
        'توقفت C عند 30,208/31,714 بوضع EXHAUSTIVE_INCOMPLETE، ثم قيّم الاستئناف 1,506 فقط. '
        'فحص السجل أكد عدم تكرار تقييم الخطط الملتزم بها. ظل الحد الأعلى 50,000 خطة لكل مودل؛ لم ينطلق exhaustive لجميع الطلاب.', '',
        f"أعلى ذاكرة عملية مسجلة في manifest الأخير: {manifest['peak_process_memory_mb']:.2f} MiB لعملية الاستئناف؛ "
        'هذا قياس العملية الحالية، وليس عدادًا تراكميًا عبر عمليتي التشغيل. '
        'سُجلت المحاولة الأصلية أثناء الفحص عند 557.26 MiB قبل الاستئناف. الحد المسموح 2048 MiB، وحد القرص 512 MiB، والدفعة 512 خطة. '
        'زمن Oracle الأكبر B≈43.30s وC≈102.68s (يتضمن كلفة الوظيفة عبر المحاولات). '
        'الأزمنة تفصل التحضير/التوجيه/الميزات/inference/الترتيب/الحفظ؛ `scoring_wall_seconds` إجمالي متداخل تشخيصي لا يضاف إلى مكوناته. '
        'وسيط B عند 1000 نحو 1.56–1.77s، وC نحو 4.13–4.20s. تقارب الأزمنة يمنع إعلان فائز سرعة ثابت من تجربة واحدة. '
        'المودل C أغلى حسابيًا في هذه العينة؛ كلفة Smart الإضافية محدودة لأنه لا يجري inference للتوجيه.', '',
        'المحاولة الأقدم `benchmark_20261024T114958_fbedab54` محفوظة بحالة partial: '
        'فشل استئناف أحد الطلاب بسبب اختلاف fingerprint الاختيار. لم تُعدّل درجاتها أو تُستخدم لإعلان oracle عالمي لذلك الطالب. '
        'التشغيل المعتمد الجديد ثبت الاختيارات المحفوظة. أصلح اختبار لاحق أيضًا بقاء seal قديم أثناء الاستئناف: '
        'تُتحقق بصمته أولًا، ثم يُبطل ويُكتب running قبل أي تعديل؛ يعاد seal عند نهاية التشغيل. '
        'هذا الإصلاح في دورة الحفظ فقط، بعد اكتمال التشغيل المقاس؛ بصمة كود التشغيل الأصلية موجودة في manifest، ولا تتغير معادلات الدرجات.', '',
        '## 11. التحقق والحماية', '',
        '`prediction_parity.json`: مقارنة 200 خطة لكل مودل، و964 صف مادة لكل مودل، بين Pilot الأصلي ودفعات benchmark حجمها 64 '
        'مقابل دفعة Pilot حجمها 200. تطابقت جميع حقول الدرجات/GPA/المخاطر والـTop-3 المحفوظة تمامًا. '
        'لدى كل مودل اختلفت تنبؤات 18 مادة مع تغير تركيب الخطة. كلفة هذا الفحص مستقلة: 800 تقييم خطة/مودل إضافي، '
        'ولا تُنسب إلى ميزانية صف benchmark.', '',
        '`protected_after.json`: **PASS، 1421 ملفًا، صفر تغيير** مقابل SHA-256 قبل العمل؛ '
        'يشمل اللقطات السابقة، ومدخلات After، والتجارب القديمة، والنماذج وFrozen History وملفات Production المحمية. '
        'لم يحدث تدريب أو إضافة/تعديل KNN أو تغيير GradeScale أو حقن مواد أو اتصال حي بالجامعة أو commit/push/merge. '
        'يظل احتساب peer features القائم داخل C كما هو؛ لم ينشأ أي مودل KNN جديد.', '',
        'تغطي اختبارات AppTest واجهتي Production/Pilot والـSearch Benchmark ضمن التطبيق نفسه، والتشغيل الصريح، '
        'وبقاء عرض النتائج وإعادة العرض بلا inference، وعزل Before/After والهدف اليدوي لكل طالب. '
        'أثبتت اختبارات الموارد انقطاع oracle واستئنافه، والميزانيات وعدم التكرار، وتلف السجل أو Top-3، '
        'وتجاوز العد `2^63` دون تحميل الفضاء في الذاكرة. نتائج الاختبارات النهائية محفوظة في ملفات JUnit داخل مجلد audit.', '',
        '## 12. الملفات والمخرجات', '',
        'ملفات التنفيذ/الواجهة المعدلة:', '',
        '- `tools/recommendation_pilot_20251/credit_target.py` (جديد).',
        '- `tools/recommendation_pilot_20251/search_space.py` (جديد).',
        '- `tools/recommendation_pilot_20251/search_benchmark.py` (جديد).',
        '- `tools/recommendation_pilot_20251/engine.py` و`runner.py` و`README.md`.',
        '- `tools/academic_advisor_streamlit/pilot_service.py` و`pilot_ui.py` و`streamlit_app.py`.',
        '- `tools/academic_advisor_streamlit/search_benchmark_ui.py` (جديد).',
        '- `scripts/experiments/pilot_search_benchmark_report.py` (جديد؛ تدقيق وتلخيص بعد انتهاء الاختيار فقط).', '',
        'الاختبارات: `tests/test_pilot_credit_target.py` و`test_pilot_search_space.py` و`test_pilot_search_benchmark.py` '
        'و`test_unified_pilot_service.py` و`test_unified_pilot_integration.py`، '
        'و`tools/academic_advisor_streamlit/tests/test_search_benchmark_ui.py` و`test_unified_pilot_ui.py`. '
        'التخطيط: `docs/superpowers/plans/2026-10-24-search-benchmark.md`. تحديثات `graphify-out/` مولدة.', '',
        f"مجلد النتائج: `data/evaluation/recommendation_pilot_20251/experiments/after_backend_fix/search_benchmark/{run_id}/`.", '',
        '- `student_results.json`: جميع التفاصيل لكل طالب/نطاق/طريقة/ميزانية/مودل.',
        '- `search_comparison.csv`: جدول المقارنة 190 صفًا؛ canonical IDs وGPA والمخاطر والتوقيت والتغطية.',
        '- `oracle_summaries.json`: أفضل ثلاث خطط والأدلة العشرة.',
        '- `run_manifest.json` و`integrity.json`: الإعدادات والمصادر والنماذج والكود والبصمات وحالة الاكتمال.',
        '- مجلد لكل طالب: `scores.sqlite`، `context.json`، `reference_pool.json`، ملفات الاختيار و`results.json` وcheckpoint.',
        '- `audit_20261024/`: جرد الثلاثين، فحص اكتمال التجارب السابقة، hashes الحماية، `verified_results.json`، '
        '`aggregate_comparison.csv`، `prediction_parity.json`، ونتائج الاختبارات.', '',
        'إعادة تدقيق التشغيل والتلخيص دون إعادة البحث:', '',
        '```powershell',
        f'.\\.venv\\Scripts\\python.exe -B -m scripts.experiments.pilot_search_benchmark_report --run {run_id}',
        '# فحص التنبؤات الاختياري يجري inference محليًا إضافيًا مستقلاً:',
        f'.\\.venv\\Scripts\\python.exe -B -m scripts.experiments.pilot_search_benchmark_report --run {run_id} --verify-predictions P20251-03-P01',
        '```', '',
        'النتائج المقاسة تثبت البحث الأمثل حسابيًا وفق المودل والقيود الحالية للحالات المكتملة فقط. '
        'صلاحية السياسات غير المؤكدة، والأداء على بقية الطلاب والفضاءات الأكبر، وأثر التوصية الفعلي على GPA تبقى غير محسومة.', '']
    report = Path(__file__).resolve().parents[2] / 'reports/pilot_20251_search_benchmark_design_and_results.md'
    prefix = report.read_text(encoding='utf8').split('## 10.')[0]
    report.write_text(prefix + '\n'.join(lines), encoding='utf8')


def write_delivery_manifest(service, run_id, audit_directory):
    """Seal final evidence, keeping execution and delivery code versions distinct."""
    from tools.recommendation_pilot_20251.search_benchmark import code_fingerprints
    saved = service.load_run(run_id)
    verified = json.loads((audit_directory / 'verified_results.json').read_text(encoding='utf8'))
    tests = {}
    for filename in ('targeted_tests.xml', 'full_regression.xml'):
        suite = next(ET.parse(audit_directory / filename).getroot().iter('testsuite'))
        tests[filename] = dict(suite.attrib)
        assert int(suite.attrib['errors']) == int(suite.attrib['failures']) == 0
    assert verified['status'] == 'completed' and all(p['complete'] for p in verified['oracle_proofs'])
    protection = verify_protected(audit_directory)
    repo = Path(__file__).resolve().parents[2]
    report = repo / 'reports/pilot_20251_search_benchmark_design_and_results.md'
    current = code_fingerprints()
    execution = saved['run_manifest']['code_sha256']
    changed = [key for key in current if execution.get(key) != current[key]]
    evidence = {p.name: sha256(p) for p in audit_directory.glob('*')
                if p.is_file() and p.name != 'delivery_integrity.json'}
    result = dict(acceptance_status='PASS', scope='implementation_and_bounded_five_student_benchmark',
        algorithm_generalization_decision='INCONCLUSIVE', created_at=datetime.now(timezone.utc).isoformat(),
        run_id=run_id, snapshot_id=saved['run_manifest']['snapshot_id'],
        experiment_rows=verified['experiment_rows'], completed_oracles=sum(p['complete'] for p in verified['oracle_proofs']),
        source_protection=protection, tests=tests, execution_code_sha256=execution, delivery_code_sha256=current,
        post_execution_code_changes=changed,
        post_execution_change_reason='search_benchmark.py: resume integrity seal lifecycle only; scoring equations unchanged',
        additional_audit_script_sha256=sha256(Path(__file__)),
        report=dict(path=str(report), sha256=sha256(report)), audit_file_sha256=evidence,
        saved_run_integrity_sha256=sha256(Path(saved['storage_path']) / 'integrity.json'),
        prediction_parity=json.loads((audit_directory / 'prediction_parity.json').read_text(encoding='utf8')),
        limitations=['unconfirmed academic policy stays flagged', 'single seed and five selected students',
            'counterfactual plan predictions are not observed academic outcomes'])
    atomic_json(audit_directory / 'delivery_integrity.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--verify-predictions', metavar='SAMPLE_ID')
    parser.add_argument('--write-report', action='store_true')
    parser.add_argument('--finalize', action='store_true')
    args = parser.parse_args()
    service = SearchBenchmarkService()
    audit = service.output / 'audit_20261024'
    try:
        result = verify_and_summarize(service, args.run, audit)
        if args.verify_predictions:
            verify_prediction_parity(service, args.run, audit, args.verify_predictions)
        protection = verify_protected(audit)
        if args.write_report:
            write_results_report(service, args.run, audit)
        if args.finalize:
            write_delivery_manifest(service, args.run, audit)
        print(json.dumps(dict(status=result['status'], rows=result['experiment_rows'],
            completed_oracles=sum(p['complete'] for p in result['oracle_proofs']), protection=protection,
            total_plan_model_evaluations=result['total_plan_model_evaluations']), indent=2))
    finally:
        service.executor.shutdown(wait=True)


if __name__ == '__main__':
    main()
