"""Render the Arabic experiment report from completed, saved evidence only."""
import json
import re
from pathlib import Path

import pandas as pd


def _json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _value(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "UNAVAILABLE"
    if isinstance(value, float):
        return f"{value:.8g}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(columns, rows):
    return "\n".join([
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
        *("| " + " | ".join(_value(v) for v in row) + " |" for row in rows),
    ])


def render(evidence_dir, model_dir, root):
    """Return A–J Markdown; refuse missing/incomplete results instead of guessing."""
    evidence_dir, model_dir, root = map(Path, (evidence_dir, model_dir, root))
    metadata = _json(evidence_dir / "metadata.json")
    if metadata.get("status") != "COMPLETE":
        raise ValueError("Report requires COMPLETE experiment metadata")
    comparison = pd.read_csv(evidence_dir / "comparison.csv")
    families = metadata["families"]
    if set(families) != {"stage1", "stage2"}:
        raise ValueError("Both model families must finish before reporting")
    cohorts = {(stage, arm): pd.read_csv(evidence_dir / f"{stage}_{arm}_cohorts.csv")
               for stage in families for arm in ("baseline", "reduced")}
    intervals = {stage: pd.read_csv(evidence_dir / f"{stage}_intervals.csv") for stage in families}
    protection = _json(evidence_dir / "protection.json")
    validation = _json(evidence_dir / "validation.json")

    def source(relative, marker):
        path = root / relative
        lines = path.read_text(encoding="utf-8").splitlines()
        hits = [i for i, line in enumerate(lines, 1) if marker in line]
        if not hits:
            return f"`{relative}`: UNVERIFIED (لم يوجد موضع المصدر)"
        return f"[{relative}]({path.as_posix()}:{hits[0]})"

    out = ["# تجربة إزالة اعتماد `attempt_sum`", "",
        "## A. الهدف", "",
        "قياس أثر إزالة الاعتماد التاريخي على `attempt_sum` لأن واجهة الجامعة لا توفره، دون تخمينه أو إضافة ميزات بديلة. "
        "النتائج التالية محسوبة من ملفات التنفيذ المحفوظة، وليست اقتراحًا لاعتماد النماذج في الإنتاج.", "",
        "## B. تدقيق الاعتماد", "",
        "المسار الرسمي: outcomes النهائية → `attempt_number × temporal_weight` → `attempt_sum` في الحالة التاريخية → "
        "`course_history_avg_attempt` → المتوسطان الموزونان لسياق الخطة والمواد الأخرى. "
        "يتطلب مسار تحديث Frozen History الرسمي الحقل نفسه؛ حذف أعمدة التدريب وحده لا يزيل هذا الاعتماد.", "",
        _table(["المصدر الفعلي", "الاعتماد"], [
            [source("src/features/temporal_features.py", 'base["attempt_sum"]'), "تجميع attempt_sum؛ يبقى retake_sum مستقلاً"],
            [source("src/features/temporal_features.py", '"course_history_avg_attempt": "attempt_sum"'), "المتوسط التاريخي من attempt_sum"],
            [source("src/features/temporal_features.py", '"avg_attempt": "course_history_avg_attempt"'), "اشتقاق plan/peer average attempt"],
            [source("src/features/feature_contract.py", '"course_history_avg_attempt"'), "عقد الميزات الرسمي"],
            [source("src/experiments/course_only_core.py", '"plan_credit_weighted_avg_mark"'), "استبعاد سياق الخطة من shortlist مع إبقاء historical average attempt"],
            [source("src/recommendation/history_update.py", "DELTA_NUMERIC_COLUMNS"), "عقد delta الرسمي ما زال يتطلب attempt_sum"],
            [source("src/features/frozen_history.py", "def validate_history_selection"), "إدارة الحزم والحدود الزمنية الرسمية لم تتغير"],
            [source("src/features/build_temporal_features.py", "def build_feature_tables"), "بناء الجداول الزمنية الرسمية؛ لم يُعَد بناؤها"],
            [source("src/modeling/train_models.py", "def train_one"), "إعادة استخدام تدريب LightGBM الرسمي"],
            [source("src/experiments/course_only_training.py", "def "), "مسار تدريب shortlist الرسمي؛ تُقرأ إعداداته المؤرشفة"],
            [source("src/evaluation/evaluate_plan_gpa.py", "def aggregate_plan_gpa"), "تجميع GPA للخطة المرصودة بوحدة الساعات نفسها"],
            [source("src/recommendation/two_stage_engine.py", "def _score_stage2"), "الاستدلال الرسمي للمرحلة الثانية لم يتغير"],
            [source("scripts/experiments/attempt_sum_removal/history.py", "class ReducedCourseHistoryState"), "حالة منفصلة بخمسة مجاميع"],
        ]), "",
        "المحذوف فقط: `course_history_avg_attempt`، `plan_credit_weighted_avg_attempt`، `peer_credit_weighted_avg_attempt`. "
        "يبقى `attempt_number` الخاص بالمرشح، و`course_history_retake_rate`، و`retake_sum`. "
        "`retake_count` يحسب محاولات الإعادة كأحداث `attempt_number > 1` في البيانات المحلية؛ ليس بديلًا لمجموع المحاولات.", "",
        "## C. العزل", "",
        f"تم التحقق من {protection['protected_file_count']} ملفًا محميًا؛ `unchanged={protection['unchanged']}`. "
        "يشمل ذلك العقود الرسمية والبيانات والنماذج وManifest وFrozen History وGraphify. "
        "الاستثناءات هي مساحات التجربة المحددة وملفات التشغيل المؤقتة فقط.", "",
        f"الأدلة: [{evidence_dir.name}]({evidence_dir.as_posix()})؛ النماذج: [{model_dir.name}]({model_dir.as_posix()}). "
        "تعيد `protected_before.json` و`protection.json` توثيق مقارنة SHA-256.", "",
        "## D. إعداد التدريب وإعادة الإنتاج", "",
        f"Dataset: `{metadata['dataset_version']}`. ينتهي التدريب في `20243`، والتقييم على `20251` و`20252`. "
        "هذه بيانات 2025 سبق فحصها؛ الاختبار retrospective وليس اختبارًا أعمى جديدًا. "
        "فواصل التحقق: التدريب حتى 2022 ثم 2023، والتدريب حتى 2023 ثم 2024. "
        "الهدف `final_mark` و`is_fail = final_mark < 50`؛ وزن الصف قبل 2022 هو `0.25` وبعد ذلك `1.0`.", "",
        f"تعريف الوزن: {source('src/modeling/training_config.py', 'def training_weights')}. "
        "نفس الصفوف وترتيبها، وتحويل الفئات، وGradeScale، والأهداف والأوزان بين الطرفين. "
        "لا retuning ولا early stopping: عدد جولات كل fold مأخوذ من baseline المختار نفسه، والجولات النهائية ثابتة من metadata.", "",
        "```json", json.dumps({k:metadata[k] for k in ('created_utc','rows','input_sha256','python','lightgbm','pandas','numpy','threads','retuned')}, ensure_ascii=False, indent=2), "```", "",
        _table(["العائلة", "grade rounds", "fail rounds", "ميزات baseline", "ميزات reduced"], [
            [stage, m['rounds']['grade'], m['rounds']['fail'], len(m['original_features']), len(m['reduced_features'])]
            for stage,m in families.items()]), "",
        "القيم أعلاه مستخرجة من التنفيذ. معاملات LightGBM الفعلية وإثبات إعادة baseline:", ""]
    for stage, entry in families.items():
        out += [f"### {stage}", "", "```json", json.dumps({k:entry[k] for k in (
            'effective_parameters','saved_baseline_verification','baseline_replica_max_prediction_difference')}, ensure_ascii=False,indent=2), "```", ""]
    out += ["تحقق زمني محفوظ؛ لا تُستخدم نتائجه لاختيار إعداد جديد:", "",
        _table(["العائلة", "fold", "الطرف", "train rows", "valid rows", "rounds", "Grade MAE", "Fail log loss"], [
            [r['family'],r['fold'],r['arm'],r['fit_rows'],r['valid_rows'],json.dumps(r['rounds']),r['grade']['mae'],r['fail']['log_loss']]
            for r in validation]), "", "## E. توافق Frozen History", ""]
    compatibility = metadata['history_compatibility']
    parity_rows=[]
    for split, details in compatibility['splits'].items():
        parity = details['parity']
        parity_rows.append([split,details['rows'],details['roster_rows'],len(parity),
            max(v['max_abs_diff'] for v in parity.values()),details['matrices']['full']['exact_match'],
            len(details['matrices']['full']['columns']),details['matrices']['shortlist']['exact_match'],
            len(details['matrices']['shortlist']['columns']),details['final_cutoff']])
    out += ["الحالة التجريبية تحفظ `effective_support, raw_count, mark_sum, fail_sum, retake_sum` فقط. "
        "أُعيد تشغيل جميع فصول train/test باستخدام roster الأصلي. تقارن 6 ميزات تاريخية و12 ميزة سياق متبقية، "
        "مع تطابق missingness؛ التسامح العددي `rtol=1e-12, atol=1e-10`. "
        "مصفوفات float32 والفئات وأسماء الأعمدة وترتيبها وأنواعها تطابق النسخة المحفوظة تطابقًا تامًا.", "",
        _table(["split","rows","roster rows","features replayed","max diff","full exact","full cols","shortlist exact","shortlist cols","cutoff"], parity_rows), "",
        "```json",json.dumps({'snapshots':compatibility['snapshots'],'delta_check':compatibility['delta_check']},ensure_ascii=False,indent=2),"```", "",
        "يُحسب سياق الفصل قبل تحديث الحالة بنتائجه؛ الدلتا النهائية لـ20251 تقارن بمسار تحديث outcomes المحلية "
        "ثم تسمح بسياق 20252. التاريخ الرسمي ما زال يتطلب `attempt_sum` ولم يُستبدل بهذه الحالة. "
        "توافق local replay لا يثبت تعريفات API: دلالة `count` مقابل `students_count`، و`retake_count`، "
        "وfinalized/cutoff في واجهة الجامعة تبقى `UNVERIFIED` حتى مطابقتها مع الجهة الموردة.", "",
        "## F. المقارنة العددية", "",
        "الفرق دائمًا `reduced − baseline`. انخفاض مقاييس الخطأ/الخسارة أفضل؛ ارتفاع AUC ونسب within أفضل. "
        "`bias` موقّع ويُقرأ قربه من الصفر، وليس اتجاهه وحده. النسب within أعداد بين 0 و1. "
        "Course points تنتج من تحويل العلامة المتوقعة عبر GradeScale نفسه؛ ليست توقعًا احتماليًا مباشرًا لتوزيع النقاط.", ""]
    for stage, label in [('stage2','Full 47 → 44'),('stage1','Shortlist 33 → 32')]:
        selected=comparison[comparison.family.eq(stage)]
        rows=[]
        for row in selected.itertuples():
            if 'bias' in row.metric:
                direction='أقرب للصفر' if abs(row.reduced)<abs(row.baseline) else 'أبعد عن الصفر' if abs(row.reduced)>abs(row.baseline) else 'تعادل'
            else:
                higher='auc' in row.metric or 'within' in row.metric
                direction='تحسن وصفي' if (row.delta>0 if higher else row.delta<0) else 'تراجع وصفي' if row.delta else 'تعادل'
            rows.append([row.metric,row.baseline,row.reduced,row.delta,direction])
        out += [f"### {label}","",_table(['Metric','Official baseline','Reduced','Delta','الاتجاه'],rows),""]
    timing=[]
    for stage, entry in families.items():
        for role in ('grade','fail'):
            timing.append([stage,role,entry['training_seconds']['baseline'][role],entry['training_seconds']['reduced'][role],
                entry['prediction_seconds_median_3']['baseline'][role],entry['prediction_seconds_median_3']['reduced'][role],
                entry['model_size_bytes']['baseline'][role],entry['model_size_bytes']['reduced'][role]])
    out += [_table(['العائلة','model','baseline train s','reduced train s','baseline predict s','reduced predict s','baseline bytes','reduced bytes'],timing),"",
        "وقت التدريب للـbaseline هو إعادة تدريب replica بالإعداد نفسه. زمن التنبؤ median لثلاث مرات بعد warm-up، "
        "على الصفوف والجهاز وعدد threads نفسه؛ جرت اختبارات المستودع بالتوازي مع بعض التدريب، لذلك الأزمنة وصفية وتتأثر بحمل الجهاز، "
        "ولا تثبت تفوقًا في الأداء أو زمن خدمة API أو ترتيب خطط مرشحة.","",
        "## G. الطلبة ذوو المعدل السابق المنخفض", "",
        "الفئات الموجبة هي `(0,1]`، `(1,2]`، `(2,3]`، `(3,4]` و`(0,2]`. "
        "نفصل الصفر مع outcomes سابقة مرصودة عن الصفر دون outcomes سابقة مرصودة وعن التاريخ المجهول. "
        "التاريخ المتاح left-censored: عدم رصد فصل سابق لا يثبت أن الطالب جديد، والصفر وحده لا يثبت تعثرًا أكاديميًا. "
        "تحتسب مجموعات المعدل باستخدام `start_agpa_points`، أما عدّ الفصول السابقة فوصفي للتقييم فقط.", ""]
    cohort_names=['positive_prior_gpa_0_1','positive_prior_gpa_1_2','positive_prior_gpa_2_3','positive_prior_gpa_3_4',
        'positive_prior_gpa_le_2','zero_with_observed_prior_outcomes','zero_no_observed_prior_outcomes','zero_history_unknown','missing_prior_gpa','prior_gpa_out_of_range']
    for stage in ('stage2','stage1'):
        baseline=cohorts[stage,'baseline'].set_index('cohort')
        reduced=cohorts[stage,'reduced'].set_index('cohort')
        rows=[]
        for name in cohort_names:
            a,b=baseline.loc[name],reduced.loc[name]
            rows.append([name,a.n_students,a.n_plans,a.n_course_rows,a.get('plan_gpa_mae'),b.get('plan_gpa_mae'),
                b.get('plan_gpa_mae',float('nan'))-a.get('plan_gpa_mae',float('nan')),a.get('student_macro_plan_mae'),b.get('student_macro_plan_mae')])
        out += [f"### {stage}","",_table(['cohort','students','plans','course rows','base Plan MAE','reduced Plan MAE','delta','base student macro','reduced student macro'],rows),""]
    out += ["`n_students` عدد هويات student_id الفريدة داخل الفئة، وقد يظهر الطالب في أكثر من فصل أو فئة؛ "
        "خطأ الطالب macro يعطي كل طالب وزنًا متساويًا، بينما Plan MAE يعطي كل خطة مرصودة وزنًا متساويًا.", "",
        "## H. توافق المرحلتين", "",
        "عقد full يحذف الميزات الثلاث ليصبح 44؛ shortlist يستبعد أصلًا ميزات سياق الخطة ويحذف historical average attempt فقط ليصبح 32. "
        "تظل هوية ميزات التدريب والاستدلال وترتيبها موثقة في `feature_contract.json` و`compatibility.json`. "
        "التوافق المثبت يخص المصفوفات والتوقعات للخطط المرصودة ومسار التاريخ التجريبي؛ "
        "لم يُقَس shortlist recall أو جودة البحث عن خطط بديلة أو جودة التوصيات counterfactual، ولم يتغير Manifest.", "",
        "## I. الحكم وعدم اليقين", "",
        f"paired student-cluster bootstrap: `{metadata['bootstrap_draws']}` draws، seed `{metadata['bootstrap_seed']}`، "
        "فواصل percentile 95%؛ تُسحب هوية الطالب كاملة مع الحفاظ على مقام كل مقياس. "
        "المقارنة مشتركة الصفوف/الخطط باستخدام المفاتيح الفعلية. الفئات الثانوية وصفية، دون تصحيح تعدد المقارنات.", "",
        "الهوامش حُددت مسبقًا في PLAN.md قبل النتائج: overall Plan MAE `+0.01`، positive prior GPA ≤2 Plan MAE `+0.02`، "
        "overall Log Loss `+0.002` وBrier `+0.001`. هي افتراضات بحثية وليست موافقة أكاديمية. "
        "`COMPARABLE` يتطلب الحد الأعلى لكل CI ضمن هامشه؛ `WORSE` إذا تجاوز الحد الأدنى أي هامش؛ "
        "`BETTER` يتطلب أيضًا الحد الأعلى لتحسن overall Plan MAE أقل من `−0.01`. خلاف ذلك `INCONCLUSIVE`. "
        "عدم الدلالة وحده لا يثبت التكافؤ، ولا نعيد ضبط الهوامش بعد مشاهدة النتائج.", ""]
    for stage in ('stage2','stage1'):
        entry=families[stage]
        primary=entry['decision_checks']
        out += [f"### {stage}: `{entry['verdict']}`","",
            _table(['cohort','metric','margin','delta','95% low','95% high'],[
                [c['cohort'],c['metric'],c['margin'],c['delta'],c['ci_low'],c['ci_high']] for c in primary]),"",
            "فواصل المؤشرات الأساسية والثانوية:","",
            _table(['cohort','metric','delta','95% low','95% high','students'],[
                [r.cohort,r.metric,r.delta,r.ci_low,r.ci_high,r.n_students]
                for r in intervals[stage].itertuples()
                if r.cohort in ('overall','positive_prior_gpa_le_2','positive_prior_gpa_0_1','positive_prior_gpa_1_2')]),""]
        for metric in ('grade_mae','plan_gpa_mae'):
            selected=intervals[stage][intervals[stage].cohort.eq('overall') & intervals[stage].metric.eq(metric)]
            if len(selected)==1:
                row=selected.iloc[0]
                interpretation=('تراجع إحصائي قابل للرصد لأن CI موجب بالكامل' if row.ci_low>0 else
                    'تحسن إحصائي قابل للرصد لأن CI سالب بالكامل' if row.ci_high<0 else
                    'الفاصل يشمل الصفر؛ اتجاه الفرق غير محسوم إحصائيًا')
                out += [f"`{stage}/{metric}`: delta `{_value(row.delta)}`، CI `[{_value(row.ci_low)}, {_value(row.ci_high)}]`: "
                        f"{interpretation}. الحكم العملي أعلاه يُقارن بالهوامش المحددة مسبقًا؛ "
                        "قد يجتمع COMPARABLE عمليًا مع تراجع صغير ذي دلالة إحصائية.",""]
    verdicts=', '.join(f"{s}={families[s]['verdict']}" for s in ('stage2','stage1'))
    out += ["## J. التوصية والأسئلة الستة", "",
        "1. **هل يمكن حذف `attempt_sum` بأمان من العقد المستقبلي؟** المسار التجريبي يدعم تمثيل التاريخ وتحديثه دون هذا الحقل "
        f"مع parity موثق؛ الحكم التنبؤي المستقل: `{verdicts}`. الأمان الكامل لعقد API غير مثبت قبل التحقق من تعريفات بقية المجاميع وcutoff، "
        "ولا يمكن تحميل الحالة المختزلة مكان الحالة الرسمية مباشرة.", "",
        "2. **ما الميزات التي تختفي من عقد الإنتاج؟** إذا تقرر الانتقال لاحقًا: `course_history_avg_attempt` و"
        "`plan_credit_weighted_avg_attempt` و`peer_credit_weighted_avg_attempt` للـfull؛ الأولى فقط للـshortlist. "
        "يبقى `attempt_number` و`course_history_retake_rate` و`retake_sum`.", "",
        f"3. **هل تغيرت الدقة بصورة مهمة؟** الحكم المحدد سلفًا هو `{verdicts}`؛ "
        "جداول F وI تعرض الفروق وفواصلها. لا نساوي فرقًا صغيرًا في MAE بتحسن موثوق ولا نخلط بين الدلالة الإحصائية والهامش العملي.", "",
        "4. **هل الأثر مختلف لدى أصحاب GPA المنخفض؟** تعرض G الفئات الموجبة منفصلة والصفر منفصلًا، "
        "وتعرض I فواصل `(0,2]` والفئتين الأدنى. يُقرأ اختلاف الأثر من هذه التقديرات وحدودها؛ "
        "الفئات قليلة الطلاب وفواصلها الواسعة لا تدعم تعميمًا مستقلًا.", "",
        "5. **هل البديل متوافق مع المرحلتين؟** نعم ضمن replay المحلي للميزات المتبقية ومصفوفتي 44 و32، "
        "مع تدريب وتقييم مستقلين لكل عائلة. دمج engine/Manifest وتشغيل توصيات بديلة في الإنتاج لم يُنفذ ولم يُثبت بهذه التجربة.", "",
        "6. **اعتماد مباشر أم بحث ميزات بديلة أولًا؟** لا اعتماد إنتاجي مباشر. "
        "إذا كانت العائلتان COMPARABLE/BETTER فالأدلة تدعم الانتقال إلى تحقق عقد الجامعة وتقييم الدمج المنفصل، "
        "دون اشتراط اختراع ميزات بديلة. إذا كانت أي عائلة WORSE/INCONCLUSIVE يلزم تحقيق إضافي محدد، "
        "وقد تُبحث البدائل في تجربة لاحقة مستقلة. لم تُضف هذه التجربة أي بديل ولم تُرقَّ أي قطعة أثرية.", "",
        "### إعادة التشغيل والملفات", "",
        "الأمر القابل لإعادة الإنتاج من جذر المستودع:", "", "```powershell",
        f".\\.venv\\Scripts\\python.exe -B -m scripts.experiments.attempt_sum_removal.runner --threads {metadata['threads']} --draws {metadata['bootstrap_draws']}",
        "```", "",
        "المشغل يرفض التشغيل إذا وُجد أي مجلد نتائج/نماذج للتجربة أو التقرير النهائي؛ لا overwrite ولا resume. "
        "لتكرار مستقل يجب حفظ هذه الأدلة أولًا واختيار مساحة جديدة مصرح بها أو إعادة تشغيله في checkout نظيف. "
        "`metadata.json` يحفظ الإعدادات والأزمنة وإعادة baseline، و`comparison.csv/json` المقارنات، "
        "`validation.json` الفواصل الزمنية، و`stage*_intervals.csv` عدم اليقين، و`stage*_*_cohorts.csv` أحجام الفئات ومقاييسها. "
        "البيانات الفردية تظل محلية داخل مساحة التجربة.", ""]
    return re.sub(r'\]\(([^\n)]+)\)', lambda m: '](<'+m.group(1)+'>)' if ' ' in m.group(1) else m.group(0), '\n'.join(out))
