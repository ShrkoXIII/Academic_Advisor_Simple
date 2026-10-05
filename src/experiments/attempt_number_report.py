"""Render the auditable report from saved experiment evidence."""
import json
import re

import numpy as np
import pandas as pd

from .attempt_number_core import OUTPUT_DIR, REPORT_PATH


def table(frame, columns=None, *, digits=6):
    frame = frame[columns] if columns else frame
    def display(value):
        if isinstance(value, (float, np.floating)):
            return f"{value:.{digits}f}" if np.isfinite(value) else "NA"
        return str(value).replace("|", "/")
    lines = ["| " + " | ".join(frame.columns) + " |", "| " + " | ".join(["---"] * len(frame.columns)) + " |"]
    lines.extend("| " + " | ".join(display(v) for v in row) + " |" for row in frame.itertuples(index=False, name=None))
    return "\n".join(lines)


def build_report():
    def csv(name):
        return pd.read_csv(OUTPUT_DIR / f"{name}.csv", dtype={"cohort": str})
    def js(name):
        return json.loads((OUTPUT_DIR / f"{name}.json").read_text(encoding="utf-8"))
    metrics, dist, outcomes, uncertainty = (csv(n) for n in ["model_metrics", "distribution", "outcomes", "paired_student_bootstrap"])
    summary, semantics, overlap = (js(n) for n in ["distribution_summary", "semantics_audit", "overlap_structure"])
    holdout = metrics[metrics.cohort.eq("holdout")]
    comparisons, calibration, differences = (csv(n) for n in ["recommendation_comparison", "calibration_means", "prediction_differences"])
    original_cv = csv("original_validation_metrics")
    calibration = calibration[calibration.cohort.eq("holdout") & calibration.subset.isin(["first", "second", "third_plus"])]
    examples = pd.read_parquet(OUTPUT_DIR / "largest_prediction_changes.parquet")
    examples = examples.groupby(["attempt_group", "chosen_by"], sort=False).head(1)
    isolation = js("isolation_verification")
    validation = js("validation_results")
    sections = []
    sections.append("""# تحليل وتجربة `attempt_number` المعزولة

تاريخ التقرير: 2026-10-01. **القرار: Evidence is insufficient لإقرار استبدال الإنتاج.**
**Does the model need the exact attempt number? INCONCLUSIVE.**

جودة التنبؤ متقاربة جدًا في المتوسط بين A وB، لكن اختلاف النتيجة الزمنية لدى 3+، وتغيّر ترتيب التوصيات، وصغر عينة التوصيات تمنع إثبات أن الاستبدال لا يسبب خسارة مهمة للمنتج. الإجراء الحالي: **Keep attempt_number** إلى أن تتوافر أدلة أقوى؛ هذا إجراء احترازي مبني على نقص الدليل، وليس إثباتًا أن الرقم الكامل ضروري لكل تنبؤ. لا ترقية لأي تجربة.

كل الأرقام من ملفات V2 الحالية الفعلية. لا فرضية مسبقة بأن Boolean أفضل؛ لا Experiment D، ولا إعادة ضبط أو إعادة تدريب بعد رؤية نتائج Test لاختيار تمثيل جديد.

## A. Current semantics

المسار الفعلي في `src/data/clean_student_course.py`:

```text
Raw student-course records
→ normalize register_status
→ keep register_status in {R,E}
→ normalize finish_status, IDs, part_id
→ drop missing course_id/part_id; validate other required keys and duplicates
→ keep part_id > 20193
→ normalize values/flags
→ stable sort [student_id, course_id, part_id]
→ groupby [student_id, course_id], cumcount()+1
→ keep finish_status in {P,F,FE,FA}
→ drop any row with N in in_agpa/in_gpa/in_credits
→ later common-student joins, enrichment, diploma, outliers, temporal split, features
```

- المفتاح `(student_id, course_id)` يعبر تغيير `degree_id`. حد البيانات 20201 يعني أن محاولات ما قبل 2020 لا تدخل الرقم، فلا يمثل بالضرورة عدد المحاولات مدى الحياة.
- R وE يدخلان العدّ؛ أي تسجيل آخر مستبعد قبل العدّ. ترتيب الصفوف زمني تصاعدي، مع منع تكرار الطالب/المادة/الفصل حتى لو تغير degree، ومنع تكرار `student_course_id`.
- P نجاح، وF/FE/FA رسوب في تنظيف النتائج. Withdrawal وأي finish_status آخر أو مفقود يدخل العدّ إذا اجتاز فلاتر ما قبل العدّ، ثم يُحذف من النتائج. اختبار `test_withdrawn_counts_as_attempt_before_removal` يثبت ذلك.
- أعلام `in_agpa/in_gpa/in_credits` لا تغير العدّ. الصف ذو N يدخل العدّ ثم يُحذف؛ الغياب/قيمة أخرى لا تُعامل N تلقائيًا. الأسماء لا تكفي لاستنتاج معنى تاريخي إضافي.
- التسجيل الحالي دون نتيجة يدخل العدّ في الذاكرة، لكنه لا يظهر في Dataset Modeling بعد فلتر finish_status. إذا أصبح صفًا سابقًا لمحاولة لاحقة، قد يرفع رقمها؛ لا يحدث إعادة ترقيم بعد فلاتر Modeling.
- `feature_contract.py` يمرر `attempt_number` كـfloat32 رقمي ضمن 47 Feature، دون bucketing أو categorical encoding. `temporal_features.py` لا يعيد حساب الرقم الشخصي، ويستخدمه لبناء متوسطات CourseHistory بشكل مستقل؛ هذه المتوسطات لم تتغير.
- `train_models.py` يستخدم `final_mark` للـGrade و`is_fail` للفشل. `src/experiments/modeling.py` محرك تجارب degree/points اختياري، وليس Production target جديدًا لهذه التجربة؛ لا نغيره.

### الفرق الحالي مع Serving

`recommendation/inputs.py::normalize_candidates` ينظر فقط إلى السجل المنظف المشترك V2 للطالب/المادة قبل target part، دون degree، ثم يحسب `max(previous saved attempt_number)+1`؛ وإذا لا توجد نتائج سابقة محفوظة يعطي 1. لا يستخدم محاولات الفصل المستهدف أو المستقبل ولا رقمًا واردًا من طلب العميل.

يمكن للرقم المحفوظ أن يحتفظ بآثار Withdrawal/N أقدم منه، لكن Serving لا يرى محاولة مستبعدة أحدث من آخر نتيجة محفوظة، ولا يرى تاريخ مادة جميع صفوفه السابقة مستبعدة. لذا ليس مطابقًا تمامًا لعدّ جميع التسجيلات المؤهلة قبل فلاتر النتائج. لم يُصلَح هذا الفرق هنا.
""")
    sections.append(f"""فحص تاريخي عند صفوف Modeling: إعادة تطبيق صيغة Serving من النتائج السابقة المنظفة أعطت **{semantics['serving_attempt_mismatch_rows']:,}/{semantics['model_rows_joined']:,}** اختلافًا ({100*semantics['serving_attempt_mismatch_rows']/semantics['model_rows_joined']:.3f}%)؛ منها 1,157 في 20251 و1,617 في 20252. الفحص قائم على prior cumulative maximum shifted، فلا يستخدم مستقبل الصف. يوجد {semantics['cross_degree_student_course_keys_in_clean_history']} مفتاح طالب/مادة ظهر في أكثر من degree في السجل المنظف. تفاصيل الصفوف محلية في `serving_semantics_mismatches.parquet`.

الـModel target للفشل هو `final_mark < 50`، وليس outcome code. يوجد {semantics['model_outcome_code_vs_mark_disagreement']} صفًا يختلف فيه تعريف الرسوب بالعلامة عن `course_outcome_status`؛ المقارنة تبقي target الحالي كما هو.

## B. Distribution

جدول كل الصفوف المستخدمة في Modeling، Train + Holdout، بعد كل فلاتر الإنتاج:

{table(dist[dist.cohort.eq('all_modeling')], ['attempt','rows','percent','students','courses'], digits=3)}

First attempt = **{summary['all_modeling']['first_percent']:.3f}%**؛ repeat = **{summary['all_modeling']['repeat_percent']:.3f}%**.
الحد الأعلى 5؛ Mean = {summary['all_modeling']['mean']:.6f}؛ Median = 1؛ P95 = 2؛ P99 = 3.
المحاولة الثالثة فأكثر: **{summary['all_modeling']['third_plus_rows']:,} صفًا**؛ الطلاب ذوو أي repeat: **{summary['all_modeling']['repeat_students']:,}**؛ المواد التي تظهر فيها repeats: **{summary['all_modeling']['repeat_courses']}**.

3+ ليست مجرد عشرات صفوف؛ لكن عدد الصفوف لا يساوي عدد وحدات مستقلة. حجم Holdout 3+ = 1,648 صفًا لدى 954 طالبًا، و4+ = 474 صفًا لدى 330 طالبًا. ما فوق 5 غير قابل للحكم بهذه البيانات.

**قيد اختيار العينة:** `src/data/clean_outliers.py` يعتبر attempt خارج [1,5] outlier ويزيل الطالب كاملًا. السجل المنظف قبل Modeling يصل إلى {semantics['clean_history_max_attempt']} محاولة؛ لذلك لا ننسب ندرة 3+ إلى الواقع كاملًا، ولا نستنتج شيئًا عن 6+ أو الطلاب المستبعدين. فلتر outliers الحالي يستخدم بيانات السجل ومقاييس نتائج؛ توجد مشكلة اختيار محتملة تعتمد على معلومات لاحقة، لكنها سابقة لهذه التجربة وثابتة في A/B/C، ولم تُعدَّل.

### Distribution shift

{table(pd.DataFrame([{'cohort': k, 'rows': summary[k]['rows'], 'repeat_percent': summary[k]['repeat_percent'], 'third_plus_rows': summary[k]['third_plus_rows']} for k in ['train','20251','20252','holdout']]), digits=3)}

تضاعفت تقريبًا نسبة repeats بين فصلي Holdout. توجد التفاصيل لجميع الفصول في `distribution_shift.csv` وتفاصيل توزيع كل cohort في `distribution.csv`.

## C. Outcome relationship

Train (وصفي، لا سببية):

{table(outcomes[outcomes.cohort.eq('train') & outcomes.subset.isin(['first','second','third','fourth_plus','repeat'])], ['subset','rows','mean_final_mark','mean_points','fail_rate'])}

Holdout:

{table(outcomes[outcomes.cohort.eq('holdout') & outcomes.subset.isin(['first','second','third','fourth_plus','repeat'])], ['subset','rows','mean_final_mark','mean_points','fail_rate'])}

الفرق الكبير المرصود يحدث بين 1 و>1، لكن بقي فرق بين الثانية و3+: الرسوب 22.61% مقابل 35.13%. وفي 4+ يظهر تغير زمني قوي: fail rate 29.44% في 20251 مقابل 46.15% في 20252. الخلفية الأكاديمية والمواد والفصول تختلف؛ هذه الأرقام لا تعني أن التكرار يسبب رسوبًا.

### التداخل مع Features الأخرى

حُسب هذا التحليل على Train فقط:

{table(csv('feature_overlap'), digits=4)}

الرقم الشخصي يخص هذا الطالب وهذه المادة. `course_history_avg_attempt/retake_rate` يصفان نتائج الطلاب السابقة لهذه المادة/degree، مع fallback وsmoothing ووزن زمني؛ أما `prior_total_fail_*` فيصف تاريخ الطالب عبر جميع المواد، ولا يحدد المادة المعادة. كذلك قد يكون repeat بعد انسحاب أو تحسين درجة، لا بعد رسوب فقط.

دليل بنيوي يتجاوز correlation: من {overlap['course_degree_part_groups']:,} مجموعة course/degree/part في Train، يوجد {overlap['mixed_personal_attempt_groups']:,} مجموعة تختلف فيها المحاولة الشخصية؛ **كلها** تحمل قيمة مطابقة للـcourse retry aggregates بين طلابها، وتضم {overlap['rows_in_mixed_groups']:,} صفًا. إذًا aggregates ليست نسخة من الرقم الشخصي.

عند مطابقة course/degree/part وشريحة prior fail courses (0،1–4،5–9،10+) مع >=10 صفوف لكل first/repeat في الخلية: {overlap['matched_cells_min10_each']} خلية، {overlap['matched_first_rows']:,} first و{overlap['matched_repeat_rows']:,} repeat. المتوسط الموزون للفرق repeat−first: mark {overlap['weighted_repeat_minus_first_mark']:+.4f}، fail rate {overlap['weighted_repeat_minus_first_fail_rate']:+.4f}. انقلاب الفرق عن الجدول الخام يبين قوة الاختلاط؛ هذا تشخيص وصفي لا ضبط سببي ولا إثبات redundancy. الاختبار العملي للفائدة هو C.

## D. Experiment setup

| Variant | Personal attempt feature | Feature count |
| --- | --- | --- |
| A | attempt_number، كما هو | 47 |
| B | is_repeat = (attempt_number > 1)، مكان العمود نفسه | 47 |
| C | حذف attempt_number فقط، دون بديل | 46 |

المصدر `temporal_train_features_v2.parquet` / `temporal_test_features_v2.parquet`؛ **356,816 / 67,536 صفًا**. المفاتيح وترتيبها مشتركة حرفيًا؛ SHA-256 للصفوف ولكل fold محفوظة في `setup.json` و`training_manifest.json`، مع التأكد من عدم تقاطع IDs وتطابق failure target. لا صفوف محذوفة أو مضافة لأي variant.

- Train: 20201–20243 حسب الفصول الـ15 الحالية؛ Test: 20251 و20252. لا تحديث للمودل بنتائج 20251؛ فقط features التاريخية المحفوظة الحالية تستخدم finalized 20251 قبل 20252، وفق apply-before-update.
- التحقق الزمني: through 20223 → 20231–20233 (205,369 fit /77,014 valid)؛ through 20233 → 20241–20243 (282,383 /74,433).
- نفس LightGBM، targets، categories fit-only، missing/unknown handling، weights (0.25 قبل 2022،1 من 2022)، seed 42 وكل seeds الفرعية، deterministic،feature/bagging fractions وregularization. Fail بلا class weights.
- إعدادات Grade الرسمية num_leaves=63/min_leaf=100،learning_rate=.04،feature_fraction=.85،bagging=.90،L1=.20،L2=2.00؛ Fail 31/80،.04،.90،.90،.10،1.00. باقي parameters كاملة في `setup.json`.
- **المقارنة النهائية تثبت 114 شجرة Grade و112 Fail لجميع A/B/C**، وهي أعداد الإنتاج المختارة مسبقًا على pre-2025. لم نجعل B أوC يغيران الميزانية أو يعيدان اختيار hyperparameters. قدمنا CV بميزانية ثابتة كتشخيص مضبوط.
- وللحفاظ على استراتيجية Validation الأصلية أيضًا، نفذنا 12 fit إضافية بإعدادات candidate الرسمي المثبت، max=900 وpatience=75، وفصول المشروع نفسها؛ الأعداد المثلى متاحة في `original_validation_protocol.json`. هذه تشخيصية؛ لم تغيّر أعداد fit النهائي أو تؤدي إلى تجربة جديدة.
- أعاد A المدرب محليًا توقعات الـartifacts الرسمية بالضبط: maximum absolute difference **0.0** للـGrade والـFail. عدم تطابق اسم `capaciy_63` في المصدر مع `capacity_63` في metadata لم يؤثر على القيم؛ نقرأ الإعدادات الفعلية من metadata، ولا نصلح الاسم هنا.

لا تستخدم B عدد المحاولات النهائي للمادة؛ تستخدم **فقط الرقم الموجود عند الصف** وتحوله مباشرة، فلا تضيف اعتمادًا على نتائج مستقبلية. بقي Frozen History وCourseHistoryState وكل course/plan/peer history columns ثابتة. لا نزعم أن Dataset خالٍ من جميع مشكلات اختيار العينة السابقة، أو أن Holdout لم يُعرض في تجارب المشروع الماضية؛ هذه تجربة ثابتة دون tuning على Holdout وليست blind prospective test جديدًا.

### Validation باستراتيجية الإنتاج الأصلية

{table(original_cv[original_cv.subset.isin(['overall','repeat','third_plus'])], ['cohort','subset','variant','rows','mae','points_mae','log_loss','pr_auc'])}

تفاصيل fixed-budget CV والمقاييس الأخرى في `model_metrics.csv`. لا توجد مكاسب ثابتة لـB في كل المقاييس/الفصول؛ التحليل لم يُضف trial لتصحيح فصل بعينه.

## E. Overall model results

Points هو تحويل توقع `final_mark` بواسطة GradeScale الرسمي؛ **لا يوجد مودل Production منفصل مدرب على points** في هذا المسار. لا نغير target إلى points لمجرد اسم Expected Points. GradeScale يستخدم أعلى `from_percent <= predicted_mark` لكل grade version، مع درجات النجاح، دون rounding.

{table(holdout[holdout.subset.eq('overall')], ['variant','rows','mae','rmse','within_5','within_10','points_mae','points_rmse'])}

كل مقاييس Fail الحالية:

{table(holdout[holdout.subset.eq('overall')], ['variant','log_loss','pr_auc','roc_auc','brier','calibration_error_10_bins'])}

Lower أفضل لـMAE/RMSE/log_loss/Brier/ECE؛ Higher أفضل لـwithin/PR-AUC/ROC-AUC. دقة prediction similarity وحدها لا تعني صحة اختيار الخطط.

## F. Repeat-only results

**8,184 صفًا،3,348 طالبًا**؛ أهم مقارنة:

{table(holdout[holdout.subset.eq('repeat')], ['variant','rows','mae','rmse','points_mae','log_loss','pr_auc','roc_auc','brier','calibration_error_10_bins'])}

وللمحاولة الأولى والثانية:

{table(holdout[holdout.subset.isin(['first','second'])], ['subset','variant','rows','mae','points_mae','log_loss','pr_auc'])}

C أضعف من A على repeats في Grade MAE وPoints MAE وFail LogLoss، لكن حجم الزيادة صغير: +0.030945 mark،+0.004674 points،+0.001270 log loss. لا يكفي هذا وحده لإثبات ضرورة المعلومات الشخصية، ولا يعطي إذنًا بحذفها. جميع مقاييس C محفوظة مع فواصل الثقة.

### Paired uncertainty

فروق B−A؛ قيم موجبة تعني خسارة أعلى. 1,000 bootstrap draws على **الطلاب** مع كل صفوف الطالب في draw، seed=42،95% percentile interval؛ مقارنة paired على الصف نفسه. هذه فواصل شرطية على المودلين المدربين؛ لا تغطي اختلاف training samples/seeds أو تغيّر الفصول مستقبلًا، ولا تُصحح تعدد المقارنات.

{table(uncertainty[uncertainty.cohort.eq('holdout') & uncertainty.variant.eq('B') & uncertainty.subset.isin(['overall','repeat','third_plus'])], ['subset','metric','rows','students','delta','low','high'])}

Margins الوصفية المثبتة قبل fit: .10 mark MAE،.02 points MAE،.005 log loss. ليست حدود قبول منتج اعتمدها المستخدم، وليست شهادة equivalence لجميع metrics. الزيادات على Repeat/3+ المجمّعة أصغر منها، لكن ذلك لا يغطي PR-AUC أو ترتيب الخطط.

## G. Third+ attempt results

**1,648 صفًا،954 طالبًا**؛ 761/537 في 20251 و887/637 في 20252:

{table(holdout[holdout.subset.eq('third_plus')], ['variant','rows','students','mae','rmse','points_mae','log_loss','pr_auc','roc_auc','brier','calibration_error_10_bins'])}

3 و4+ منفصلتان:

{table(holdout[holdout.subset.isin(['third','fourth_plus'])], ['subset','variant','rows','students','mae','points_mae','log_loss','pr_auc'])}

مقارنة الفصول لدى Repeat و3+:

{table(metrics[metrics.cohort.isin(['20251','20252']) & metrics.subset.isin(['repeat','third_plus'])], ['cohort','subset','variant','rows','mae','points_mae','log_loss','pr_auc'])}

{table(uncertainty[uncertainty.cohort.isin(['20251','20252']) & uncertainty.variant.eq('B') & uncertainty.subset.eq('third_plus')], ['cohort','metric','rows','students','delta','low','high'])}

في 20251 ارتفع 3+ Fail LogLoss مع B بمقدار +.004451،CI [.000247,.008534]؛ لا نستطيع استبعاد خسارة أعلى من margin .005. في 20252 تحسن بمقدار −.007602،CI [−.013410,−.002366]. التجميع يخفي هذا الاتجاه المعاكس. PR-AUC المجمّع لـ3+ انخفض .516184→.507086،ولـ4+ .556018→.528077؛ حجم العينة/التذبذب يمنع الحكم القطعي على منفعة الرقم لكل tail أوفصل. Error هذه الشرائح أكبر من first؛ ندرتها لا تجعلها غير مهمة.

### Fail calibration

{table(calibration, ['subset','variant','rows','mean_predicted_fail','actual_fail_rate','prediction_minus_actual'])}

B لا يعطي فعليًا نفس احتمال الرسوب لجميع الثانية والثالثة: المتوسط .185350 للثانية و.265809 لـ3+، لأن Features التاريخ الأكاديمي/المادة الأخرى ما زالت مختلفة. لكنه يفقد التمييز الشخصي المباشر 2 مقابل3+. كلا A وB يقللان الخطر عن المرصود؛ B حسّن mean calibration المجمّع لدى3+،مع ضعف PR-AUC. جدول bin-by-bin الحالي،10 bins،لكل subgroup وsemester وvariant متاح في `calibration_bins.csv`؛ لم نطبق recalibration.

## H. Prediction differences

Absolute B−A على الصفوف نفسها؛ delta fail probability بوحدة احتمال [0,1]،mark بوحدة [0,100]،points بوحدة [0,4]:

{table(differences[differences.cohort.eq('holdout') & differences.variant.eq('B') & differences.subset.isin(['overall','repeat','second','third','fourth_plus'])], ['subset','task','rows','mean','median','p95','max'])}

الحالات التالية اختيرت لتوضيح تغيرات كبيرة **وليست عينة تمثيلية**؛ لا ننشر IDs شخصية في التقرير،والتفاصيل محلية في Parquet:

{table(examples, ['attempt_group','chosen_by','course_id','part_id','attempt_number','final_mark','grade_A','grade_B','points_A','points_B','fail_A','fail_B'], digits=4)}

حتى first attempts يمكن أن تتغير توقعاتها بعد إعادة تدريب الشجر كله؛ مساواة تمثيلها الشخصي لا تعني مساواة كل splits/leaf values،خاصة مع feature_fraction. وفي C يقل عدد الأعمدة، فيتغير أيضًا فضاء اختيار feature_fraction؛ هذه خاصية ablation مع نفس إعدادات التدريب،وليست تعديلاً يدويًا لها. GradeScale المتقطع يضخم عبور حد 50 إلى فرق points يصل1.5،رغم أن تغير mark صغير نسبيًا.

### Feature importance كدليل مساعد
""")
    importance = []
    for task in ["grade", "fail"]:
        for variant in ["A", "B"]:
            frame = pd.read_csv(OUTPUT_DIR / "holdout" / f"importance_{variant}_{task}.csv")
            frame["rank"] = np.arange(1, len(frame)+1)
            feature = "attempt_number" if variant == "A" else "is_repeat"
            item = frame[frame.feature.eq(feature)].iloc[0].to_dict()
            importance.append({"model": task, "variant": variant, **item})
    sections.append(table(pd.DataFrame(importance), ['model','variant','feature','rank','gain_share','splits']))
    sections.append(f"""هذه أهمية gain مشروطة بالشجر وبتداخل Features؛ لا تثبت السببية ولا تحل محل A/B/C،ولا نقارن القيم الخام للـgain بين مودلين مختلفي targets كدليل على المنفعة.

## I. Recommendation impact

أربعة طلبات فعلية صالحة من JSON exports الحالية، كلها تضم repeat candidates؛ واحدة فقط تضم 3+. اختيار inputs فقط، بترتيب حتمي، دون اختيار الحالات حسب تغير التوقعات. لم نصطنع requests أو توفر مواد في 20252. جُمعت {int(comparisons[comparisons.variant.eq('B')].plans.sum()):,} خطة exact18 ممكنة، بنفس المرشحين وترتيبهم وFrozen base history as_of_20243 وsnapshot بداية 20251. القائمة والتفسيرات والاستبعادات في `recommendation_selection.json`.

أُعيد استخدام `prepare_candidates`،`enumerate_plan_indices`،`build_plan_rows`،`compute_plan_context_features`،GradeScale،`summarize_scored_plans`،`rank_plans` الإنتاجية دون أي تعديل. كل variant يتنبأ بكل course-in-plan لأن سياق الخطة مهم؛ لم نستخدم طريقة course-only. تحققنا أن A يطابق Production scoring لكل خطة: فرق0.0. GPA projection هو additive الحالي،ويحمل تحذير repeat policy؛ لا نحسب استبدال درجات سابقة من عندنا.

{table(comparisons, ['case','variant','candidates','repeat_candidates','third_plus_candidates','plans','top1_changed','top3_set_changed','top3_order_changed','rank_spearman','mean_absolute_rank_movement'], digits=4)}

B: **Top‑1 تغير في2/4**؛ Top‑3 set في2/4؛ Top‑3 order في3/4. C: Top‑1 في2/4؛ Top‑3 set في3/4. 2/4 ليس تقديرًا سكانيًا مستقرًا: Wilson95% تقريبًا15%–85%،والعينة convenience أصلًا. الحالة الوحيدة3+ تغير فيها Top‑1 وTop‑3؛ **INSUFFICIENT EVIDENCE** للحكم على معدل التغير أوquality لدى3+ فيProduction.

GPA أفضل خطة لكل مودل:

{table(comparisons, ['case','variant','best_expected_plan_gpa_A','best_expected_plan_gpa_other','best_projected_gpa_A','best_projected_gpa_other','baseline_top1_rank_other','other_top1_rank_baseline'])}

قد تتغير Top‑1 مع نفس GPA بسبب فصل النقاط المتقطع وFail tie breaker؛ هذا حدث فيcase_01 وcase_03 معB. لا تعني مساواة GPA أن المواد المختارة متطابقة.

تغير توقعات **الخطة نفسها** (absolute deltas،نمنع خلط أثر اختيار خطة مختلفة بأثر النموذج):

{table(comparisons[comparisons.variant.eq('B')], ['case','same_plan_abs_expected_plan_gpa_mean','same_plan_abs_expected_plan_gpa_median','same_plan_abs_expected_plan_gpa_p95','same_plan_abs_expected_plan_gpa_max','same_plan_abs_projected_cumulative_gpa_mean','same_plan_abs_projected_cumulative_gpa_max'])}

لكل حالة all-plans A/B/C محفوظة مع rank وexpected_failed_credits وكل GPA في `recommendations/case_*/plans_*.parquet`. اختلاف الترتيب **حساسية سلوك**،وليس إثبات جودة أعلى أوأقل: لا تتوافر نتائج counterfactual للخطط البديلة. كذلك مصدر exports ووقت `is_requestable` لا يثبتان توفرها تاريخيًا في20251؛ هذه مقارنة serving inputs موثوقة،وليست historical availability backtest أوpolicy evaluation كاملة.

### GPA للخطط المسجلة الفعلية

التقييم الحالي على observed plans،مختلف عن ترتيب البدائل: 12,713 خطة طالب/degree/فصل. كل مقاييس `summarize_plan_errors` الحالية محفوظة لجميع الفصول والvariants،وللخطط ذات أيrepeat.
""")
    observed = []
    for variant in ["A","B","C"]:
        for label in ["all_observed_plans","observed_plans_with_repeat"]:
            item = js(f"observed_plan_metrics_holdout_{variant}_{label}")
            observed.append({"variant": variant, "subset": label, **item})
    sections.append(table(pd.DataFrame(observed), ['variant','subset','plans','mae','credits_weighted_mae','rmse','bias','within_0_25','within_0_50','within_1_00']))
    sections.append(fr"""## J. Production implication

| خيار | ماذا يحتاج Backend | حدود الدلالة |
| --- | --- | --- |
| A | رقم مطابق لقواعد العد الحالية للطالب/المادة،عبر degrees،مع cutoff | يعتمد على تاريخ عدّ كامل وفق الفلاتر المحددة |
| B | Boolean يدل على وجود محاولة سابقة **حسب قواعد العد نفسها** | لا يكفي تعريفه had_previous_fail أووجود صف ناجح/راسب محفوظ فقط |
| C | لا feature محاولة شخصية في المودل | تبقى احتياجات repeat policy والتاريخ وتجميع course retries مستقلة |

Boolean قد يقلل متطلبات نقل عدد المحاولات،لكن **لا يحل تلقائيًا اختلاف Cleaning/Serving** أوحد ماقبل2020. تعريف has_previous_attempt يجب أن يتفق مع أنواع التسجيل counted؛ وإلا تختبر الخدمة feature مختلفة عن `(attempt_number>1)` هنا. وفيB/C ما زال التحذير `projected_gpa_requires_repeat_policy` يحتاج كشف repeat لأغراضRecommendation. لا يترتب على حذف feature شخصية حذف Frozen History أوقدرة النظام على معرفة retries تجميعيًا.

## K. Conclusion

**Evidence is insufficient** لإقرار أنBoolean مكافئ فيPrediction quality **و**Recommendation behavior. على metrics المجمعة B قريب منA،لكن LogLoss لـ3+ يتغير اتجاهه بين20251/20252،وCI20251 لا يستبعد خسارة>.005،وPR‑AUC أقل،والترتيب تغير في2/4 حالات. حجم العينة يكفي لرصد فروق التنبؤ الصغيرة المشروطة في3+،لكنه لا يكفي لاستنتاج ثبات توصياتهم أوتعميمها على6+.

**Keep attempt_number فيProduction حاليًا.** لا نزعم YES للضرورة الإحصائية،ولاNO لإمكان الاستبدال بلا خسارة؛ الإجابة **INCONCLUSIVE**. كذلك لا ندعم حذف attempt information لمجرد أنC قريب إجمالًا؛ هو أضعف علىRepeat وبعض مقاييسValidation.

قبل قرار لاحق: عينة توصيات أكبر من فصول ذات requests موثقة الوقت،وبالأخص3+؛ tolerances منتج متفق عليها لمقاييس Repeat/3+ وTop‑K؛ تحقق مستقبلي ثابت قبل أيengineering جديد. هذه خطوات تالية،لم تُستخدم لتعديل trial الحالي.

### العزل والتحقق وإعادة التنفيذ

- protected files: **{isolation['protected_files']}**؛changed={isolation['changed']}؛added={isolation['added']}؛ production artifacts modified={isolation['official_artifacts_modified']}.
- الاختبارات المركزة: {validation['focused']}. الاختبارات الكاملة: {validation['full']}.
- الفشل المتبقي السابق: `tests/test_train_models.py` يتوقع `capacity_63` بينما المصدر الحالي يعطي `capaciy_63`. لم يُصلح ضمن هذه المهمة. اختبار اتجاه الاعتماد نجح بعد وضع أداة Recommendation في scripts، دون تخفيف الاختبار.
- output/model SHA‑256 وordered row fingerprints ومعلومات environment في manifests. ملفات predictions والcases محلية وتتضمن سجلات؛ لم تُرسل ولم تُعمل commits لها.
- إضافة كود فقط: `src/experiments/attempt_number_*.py`؛أداة orchestration/recommendation في `scripts/experiments/attempt_number_*.py`؛اختبارات وتجربةplan وتقرير. لا تعديل source إنتاجي أوfeature contract أوrecommendation contract.

```powershell
.\.venv\Scripts\python.exe -m scripts.experiments.attempt_number_experiment
# Existing signed run: explicit reuse without silently refitting
.\.venv\Scripts\python.exe -m scripts.experiments.attempt_number_experiment --resume
# Rebuild report only from saved evidence
.\.venv\Scripts\python.exe -m scripts.experiments.attempt_number_experiment --report-only
```

أي محاولة initial جديدة في namespace موجودة تُرفض؛--resume يتطلب نفسinput/source signature ويتحقق من model hashes. الحذف الممكن لاحقًا محصور بـnamespace التجربة وموديولاتها الجديدة؛لا يحتاج مراجعة أوتغيير artifacts الإنتاج.

### Summary

Points MAE وFail LogLoss؛قيمة أقل أفضل. عموداRepeat/3+ يعرضان `points / logloss`:

| Experiment | Points model | Fail model | Repeat subset | Third+ subset | Recommendation impact | Complexity |
| --- | --- | --- | --- | --- | --- | --- |
| attempt_number | 0.576022 | 0.274023 | 0.754979 / 0.518130 | 0.842536 / 0.626647 | reference | عدد صحيح |
| is_repeat | 0.576215 | 0.274334 | 0.755346 / 0.518008 | 0.838896 / 0.624611 | Top‑1:2/4،Top‑3 set:2/4 | Boolean |
| no attempt | 0.577096 | 0.274425 | 0.759653 / 0.519400 | 0.843750 / 0.625877 | Top‑1:2/4،Top‑3 set:3/4 | featureأقل |

**Does the model need the exact attempt number? INCONCLUSIVE.**
الفروق الإجمالية صغيرة جدًا، وBoolean مرشح معقول للتبسيط، لكن 3+ يظهر تباينًا زمنيًا تخفيه المقارنة المجمعة.
التوصيات تغيرت في عينة صغيرة من cases حقيقية؛ لا دليل على تكافؤ quality للخطط المتغيرة.
الحفاظ على attempt_number حاليًا، مع بقاء B/C تجريبيين، هو القرار المدعوم بما لدينا.
""")
    rendered = "\n\n".join(sections)
    rendered = re.sub(r"([،؛])(?=\S)", r"\1 ", rendered)
    rendered = re.sub(r"([\u0621-\u064a])([A-Za-z0-9])", r"\1 \2", rendered)
    rendered = re.sub(r"([A-Za-z0-9])([\u0621-\u064a])", r"\1 \2", rendered)
    REPORT_PATH.write_text(rendered, encoding="utf-8")
    return REPORT_PATH
