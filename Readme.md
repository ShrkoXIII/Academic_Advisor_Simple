# Academic Advisor — ترشيح الخطة الفصلية عبر توقع العلامة ومخاطر الرسوب

> تحديث النقل إلى V2: مراحل `src.data` و`src.features` تكتب ملفات `_v2` وتقرأ الوسائط من الإصدار نفسه. المسارات غير الملحقة والأرقام القديمة أدناه تصف مخرجات V1 المحفوظة. التدريب والتقييم والتوصية ما زالت تستخدم مخرجاتها الحالية ولم تُحوّل إلى V2. التشغيل الفعلي الكامل لـV2 متوقف حاليًا على مفاتيح ناقصة في raw courses وفصول خام غير صالحة وفق الحراس الحالية؛ راجع [تقرير النقل](reports/data_features_v2_20260921/report.md).

> نقطة الدخول الموصى بها لقراءة المشروع والتنقل بين التدريب والتجارب والنتائج:
> [`START_HERE.md`](START_HERE.md).
> وخريطة الملفات والتنفيذ الكاملة موجودة في
> [`PIPELINE_README.md`](PIPELINE_README.md).

الهدف النهائي للمشروع هو **ترتيب خطط فصلية كاملة** من قائمة مقررات قانونية
وجاهزة للطالب، وليس مجرد توقع علامة مادة منفردة. توقع العلامة ومخاطر الرسوب
طبقة وسيطة يستخدمها نظام الترشيح لتقدير جودة كل خطة وحملها ومخاطرها.

يعتمد النظام مودلين LightGBM يشتركان في عقد الخصائص نفسه:

- `GradeRegressor`: يتوقع `final_mark` بين 0 و100.
- `FailRiskClassifier`: يتوقع احتمال `is_fail = final_mark < 50`.

بعد توقع كل مادة ضمن سياق الخطة، يحسب النظام نقاط الجودة والساعات المتوقع
نجاحها أو رسوبها، ثم يعيد أفضل الخطط حسب حدود الساعات والمخاطرة التي يمررها
النظام المستدعي.

> لمتابعة ما أُنجز والخطوة التالية افتح [`PROJECT_TRACKER.md`](PROJECT_TRACKER.md)
> أو شغّل `python src\project_status.py` من جذر المشروع.

## 1. مصادر البيانات

الجداول الخام موجودة تحت `data/raw/`:

- `v_crg_student_course_raw.parquet`: تسجيلات المقررات ونتائجها.
- `v_add_student_degree_status.parquet`: حالة الطالب وملخص كل فصل.
- `v_acd_degree_course.parquet`: مقررات الخطط وخصائص المتطلبات.
- `v_add_academic_info.parquet`: معدل ونوع الشهادة قبل الجامعة.
- `v_acs_grade.parquet`: جدول الدرجات والنقاط الرسمي حسب `grade_version_id`.

جميع المسارات المركزية معرفة في `src/paths.py`.

## 2. التنظيف والدمج

### مقررات الطلاب وحالاتهم

المسارات والأرقام الأساسية في الفقرات التالية تصف ملفات V1 التاريخية. سلسلة V2
تنظف المصدرين باستقلال إلى `student_course_pre_common_v2.parquet` و
`student_status_pre_common_v2.parquet`، ثم تشغّل `src/data/filter_common_students.py`
للاحتفاظ بالطلاب المشتركين على مستوى `student_id` فقط. الملفات النهائية هي
`student_course_v2.parquet` (456,595 صفًا) و`student_status_v2.parquet`
(107,939 صفًا)، ولكل منهما 12,792 طالبًا.

ينفذ `src/data/clean_student_course.py` توحيد الأعمدة والمعرّفات، ويحتفظ بتسجيلات
`R/E` والنتائج النهائية `P/F/FE/FA` بعد 2019، ويحسب `attempt_number` زمنيًا.
الناتج هو `data/clean/student_course.parquet` وفيه 456,453 صفًا.

ينظف `src/data/clean_student_status.py` حالات الطالب، ويحسب `last_enrolled_gpa`
والفجوات المرصودة بين الفصول. الناتج هو
`data/clean/student_status.parquet` وفيه 95,622 حالة فصلية.

ينظف `src/data/clean_degree_course.py` الخطة الدراسية، ثم يدمج
`src/data/build_student_course_enriched.py` المقرر مع حالة الطالب وخصائص الخطة.
الناتج هو `data/clean/student_course_enriched.parquet` وفيه 456,453 صفًا.

### الشهادة قبل الجامعة

ينفذ `src/data/clean_student_diploma.py` ما يلي:

- يحتفظ بـ `student_id`, `diploma_gpa`, `diploma_type_id`.
- يحذف الصفوف ذات `diploma_type_id` المفقود.
- يبقي أكثر أربعة أنواع تكرارًا ويدمج الباقي في `55.111`.
- يملأ `diploma_gpa` المفقود بطريقة `ffill`.
- يدمج الشهادة بـ`left join` كي لا تضيع تسجيلات مقررات.

الناتجان هما:

- `data/clean/student_diploma.parquet`: عددها 32,524 طالبًا.
- `data/merged/student_course_enriched_with_diploma.parquet`: عددها 456,453
  صفًا.

### القيم الشاذة

يطبق `src/data/clean_outliers.py` حدودًا ثابتة على خصائص الفصل والمقررات، ويحذف
الطالب كاملًا إذا ظهر له سجل شاذ مثل حمل ساعات غير منطقي أو تراكمات رسوب شديدة
الخروج عن المجتمع النظامي. حُذف 533 طالبًا و22,285 صفًا، وبقي 12,259 طالبًا
و434,168 صفًا.

- البيانات النظيفة: `data/merged/student_course_enriched_without_outliers.parquet`.
- تقرير أسباب الحذف: `data/merged/outlier_students.parquet`.

## 3. Roster الحمل الفصلي

يبني `src/data/build_registration_roster.py` جدولًا منفصلًا من **كل تسجيلات `R/E` قبل
فلترة النتيجة**. لذلك يشمل المواد المنسحبة وغير المكتملة لأنها كانت جزءًا من
الحمل الحقيقي للفصل.

مفتاح الخطة هو `[student_id, degree_id, part_id]`. تبقى صفوف `pass/fail` وحدها
أهدافًا للتدريب، بينما يستخدم الـroster الكامل لحساب حمل مجموعة المواد. أثبت
المسح أن هذا الجدول يطابق `semester_reg_courses/credits` تقريبًا بالكامل، في
حين تغطي صفوف أهداف المودل نحو 80% من الحمل فقط.

المخرجات:

- `data/clean/registration_roster.parquet`: عددها 463,721 تسجيلًا.
- `data/temporal/temporal_train_roster.parquet`: عددها 390,134 تسجيلًا.
- `data/temporal/temporal_test_roster.parquet`: عددها 73,581 تسجيلًا.

## 4. التقسيم الزمني

ينفذ `src/data/build_temporal_split.py` فلاتر زمنية مباشرة بدون shuffle وبدون إنشاء
ملف validation ثابت:

- `temporal_train`: من `20201` حتى `20243`، أي 2020–2024.
- `temporal_test`: الفصلان `20251` و`20252`.
- `20253`: مستبعد حاليًا لأنه غير مكتمل ويحتوي خمسة صفوف فقط.

المخرجات:

- `data/temporal/temporal_train.parquet`: عددها 365,585 صفًا و10,490 طالبًا.
- `data/temporal/temporal_test.parquet`: عددها 68,578 صفًا و7,177 طالبًا.

ظهور الطالب نفسه في التدريب ثم الاختبار مقصود، لأنه يحاكي توقع فصل مستقبلي
لطالب معروف. لا يحتوي سكربت التقسيم فحوص مخطط أو فصول مكررة؛ مخطط البيانات
والفصول الحالية حقائق ثابتة، ويترك pandas يفشل طبيعيًا عند وجود خطأ فعلي.

## 5. هندسة الخصائص الزمنية

ينفذ `src/features/build_temporal_features.py` البناء الكامل ويحفظ حالة الصعوبة المتعلمة.

### صعوبة المقرر التاريخية

تُحسب خصائص كل فصل تدريبي من الفصول السابقة فقط، ثم تضاف نتائج الفصل إلى
التاريخ بعد إنهاء خصائصه:

- `course_history_avg_mark`
- `course_history_fail_rate`
- `course_history_avg_attempt`
- `course_history_retake_rate`
- `course_history_effective_support`
- `course_history_fallback_level`
- `course_history_missing`

تدخل نتائج ما قبل 2022 بوزن `0.25`، ونتائج 2022–2024 بوزن `1.0`. يستخدم
smoothing بقيمة `k=20` وتسلسل fallback التالي:

1. التخصص + المقرر.
2. المقرر عبر التخصصات.
3. التخصص + نوع المتطلب + الساعات.
4. الكلية + نوع المتطلب + الساعات.
5. نوع المتطلب + الساعات.
6. المتوسط العام السابق.

حالة الصعوبة المطبقة على اختبار 2025 مجمدة بعد `20243`؛ لا تدخل نتيجة من 2025
في إحصائيات صعوبة مقررات الاختبار.

### اتجاه GPA

تُحسب القيم مرة واحدة لكل طالب وفصل ثم تكرر على مقرراته:

- `gpa_prev_1`: GPA آخر فصل مكتمل.
- `gpa_prev_2`: GPA الفصل السابق له.
- `gpa_trend_delta = gpa_prev_1 - gpa_prev_2`.
- `gpa_trend_missing`: يساوي 1 عند غياب فصلين سابقين.

تبقى القيمة غير المتاحة `NaN` لأن الصفر يعني اتجاهًا ثابتًا حقيقيًا. عند توقع
`20252` يسمح باستخدام GPA الحقيقي من `20251`، لكنه لا يستخدم أي فصل حالي أو
مستقبلي.

### حمل الخطة والـleave-one-out

تحسب خصائص الحمل من الـroster الكامل وبوزن `course_credits`. خصائص `plan_*`
تصف الخطة كلها، أما خصائص `peer_*` فتستبعد المقرر المستهدف كي لا يصف نفسه:

- العدد والساعات: `plan/peer_course_count`, `plan/peer_total_credits`.
- متوسط الرسوب والعلامة والمحاولات الموزون بالساعات.
- `plan/peer_difficulty_credit_load = Σ credits × fail_rate`.
- `peer_max_fail_rate` و`peer_difficulty_missing`.

بذلك تؤثر مادة من 6 ساعات في حمل الخطة أكثر من مادة من ساعتين. وفي مرحلة
الترشيح يعاد حساب هذه الخصائص لكل خطة محتملة قبل التوقع.

المخرجات المؤقتة، التي تبقى مسماة `temporal_*` لأغراض التدقيق الزمني:

- `data/features/temporal_train_features.parquet`: 365,585 صفًا و95 عمودًا.
- `data/features/temporal_test_features.parquet`: 68,578 صفًا و95 عمودًا.
- `data/artifacts/course_history_state.pkl`: حالة صعوبة مجمدة حتى نهاية 2024.

## 6. عقد الخصائص الآمنة

يعرف `src/features/feature_contract.py` allowlist ثابتة من 47 خاصية يستخدمها المودلان.
يشمل العقد تاريخ الطالب السابق، GPA والـAGPA المتاحين قبل الفصل، التراكمات
السابقة، الشهادة، خصائص المقرر والخطة، صعوبة المقرر، واتجاه وحمل الخطة.

تعامل الخصائص التالية كـcategorical ولا تفسر كمسافات عددية:

- `plan_course_type_id`
- `plan_requirement_type_id`
- `diploma_type_id`
- `grade_version_id`
- `part_semester`

لا تدخل raw IDs مثل `student_id`, `course_id`, `degree_id`, `faculty_id` إلى
المودل. كما تستبعد أعمدة التسرب، ومنها `final_mark` من `X`، و`points`,
`grade_id`, `course_outcome_status`, GPA الحالي، أعمدة نجاح/رسوب الفصل،
تراكمات نهاية الفصل و`finish_status`.

تتعلم مستويات التصنيفات من التدريب فقط، وتحول الفئات الجديدة في inference إلى
`__UNKNOWN__`. يحفظ القاموس في `data/artifacts/category_levels.json`.

## 7. التدريب والتقييم

ينفذ `src/modeling/train_models.py` ضبطًا زمنيًا متوسعًا داخل 2020–2024:

1. تدريب حتى نهاية 2022 وتقييم 2023.
2. تدريب حتى نهاية 2023 وتقييم 2024.
3. اختيار إعداد كل مودل وفق متوسط MAE للـregressor وlog-loss للمصنف.
4. إعادة التدريب على 2020–2024 كاملًا.
5. فتح اختبار 2025 وتقييمه مرة واحدة.

يطبق وزن الصفوف وقت `fit` فقط:

```python
sample_weight = 0.25  # قبل 2022
sample_weight = 1.00  # من 2022 حتى 2024
```

لا يستخدم المصنف `class_weight` أو `scale_pos_weight` في baseline حتى تبقى
احتمالات الرسوب قابلة للتفسير والمعايرة. الهدف المعتمد بقرار المشروع هو
`final_mark < 50` حتى لو اختلفت بعض تسميات المصدر التاريخية.

أفضل إعداد حالي للمودلين هو `capacity_63`. نتائج الاختبار المغلق 2025:

| المودل | المقاييس |
|---|---|
| GradeRegressor | MAE `9.150`، RMSE `12.120`، ضمن ±5: `36.09%`، ضمن ±10: `64.28%` |
| FailRiskClassifier | PR-AUC `0.524`، ROC-AUC `0.903`، Brier `0.0688`، log-loss `0.2202`، ECE `0.0202` |

المخرجات:

- `models/grade_regressor.txt`
- `models/fail_risk_classifier.txt`
- `models/model_metadata.json`: العقد والإعدادات ونتائج كل fold والاختبار
  وأهم الخصائص.

## 8. ترشيح الخطط الفصلية

يوفر `src/recommendation/engine.py` الصنف `AcademicPlanRecommender`، والمتاح أيضًا عبر `src.recommendation`. المدخلات هي:

- snapshot آمن يمثل حالة الطالب قبل الفصل المستهدف.
- قائمة مقررات قانونية وجاهزة؛ توليد الأهلية والمتطلبات السابقة خارج نطاق هذه
  الطبقة.
- `credits` لقيمة محددة بالضبط، أو `min_credits` و`max_credits` لقبول جميع الخطط ضمن المجال شاملاً طرفيه.
- `current_gpa` وساعات معدله التراكمي من snapshot أو `current_gpa_credits`: لحساب التوقع التراكمي.

يعدّد النظام كل المجموعات المطابقة للساعات بعدد مواد متغير، ثم يعيد حساب
خصائص الحمل ويتوقع كل مقرر داخل سياق كل خطة على دفعات. مثال الاستدعاء:

```python
from src.recommendation import AcademicPlanRecommender

advisor = AcademicPlanRecommender.load(history_as_of_part=20243)
plans, result = advisor.recommend(
    student_snapshot=snapshot,
    candidate_courses=legal_candidates,
    part_id=20251,
    min_credits=12,
    max_credits=18,
    current_gpa=2.5,
    batch_size=2000,
    top_n=5,
)
```

يتوقع المودل المختار من `degree_points` النقاط مباشرة. تُرتّب كل الخطط المطابقة دون استبعاد غير المحسّنة:

1. أعلى `projected_cumulative_gpa`.
2. عند التعادل: أقل `expected_failed_credits = Σ credits × p_fail`.
3. ثم أعلى `expected_plan_gpa = Σ credits × expected_points / Σ credits`.
4. ثم أصغر `plan_id` لكسر التعادل.

يُعرض التحسن المتوقع كمؤشر في النتائج، وليس شرطًا للاحتفاظ بالخطة.

يعيد كل اقتراح النقاط المتوقعة واحتمال الرسوب لكل مادة وعدد المواد والساعات.
لحفظ تفاصيل جميع الخطط استخدم `python -m src.recommend_local`؛ دليل الملفات
وsnapshot والتشغيل والاختبارات في [LOCAL_RECOMMENDATION.md](LOCAL_RECOMMENDATION.md).

## 9. تقييم خطأ GPA للخطة الفعلية

ينفذ `src/evaluation/evaluate_plan_gpa.py` أول خطوة من backtesting على جميع الخطط المسجلة
فعليًا في اختبار 2025. يحول علامة كل مادة المتوقعة إلى نقاط عبر جدول الدرجات
الرسمي ثم يحسب:

```text
actual_plan_gpa    = Σ(course_credits × actual_points) / Σ(course_credits)
predicted_plan_gpa = Σ(course_credits × predicted_points) / Σ(course_credits)
plan_gpa_error     = predicted_plan_gpa - actual_plan_gpa
```

على 68,578 مادة ضمن 12,976 خطة فصلية، كان MAE للخطة `0.3764` وRMSE
`0.5284`، وكانت 75.60% من الخطط ضمن ±0.50 نقطة GPA. بلغ الانحياز `+0.1597`،
أي أن التوقع يميل إلى رفع GPA قليلًا.

المخرجات:

- `data/evaluation/plan_gpa_course_predictions_2025.parquet`: توقع ونقاط كل مادة.
- `data/evaluation/plan_gpa_evaluation_2025.parquet`: صف واحد لكل طالب وفصل.
- `data/evaluation/plan_gpa_metrics_2025.json`: المقاييس الإجمالية وحسب الفصل.

يوجد تحليل أوسع خارج الزمن حسب 2023–2025، وحسب الاختصاص، مع SHAP وشرح أسباب
الخطأ وخطة التحسين في
[`reports/model_error_analysis.md`](reports/model_error_analysis.md).

## 10. تجربة الاختصاص وتوقع النقاط

يقارن `src/experiment_degree_points.py` بين إدخال `degree_id` كفئة، وإحصائيات
الاختصاص التاريخية، وتوقع العلامة أو النقاط، ووزن التدريب بساعات المقرر. اختيرت
النسخة الفائزة على 2023–2024 فقط، ثم قيّمت على 2025. المرجع الحالي للنسخة
والأرقام هو `data/evaluation/experiments/degree_points/experiment_metadata.json`.

التحسن الأساسي جاء من توقع النقاط مباشرة؛ تاريخ الاختصاص أضاف تحسنًا أصغر،
بينما أثر وزن الساعات المعزول كان ضعيفًا. يستخدم مسار التوصية المحلي الآن
مودل النقاط المختار، وتبقى جودة اختيار الخطط البديلة بحاجة لتقييم مستقل.

التقرير الكامل:
[`reports/degree_points_experiment.md`](reports/degree_points_experiment.md).
وجدول تتبع كل إضافة ونتيجتها:
[`reports/model_improvement_table.md`](reports/model_improvement_table.md).

## 11. الاختبارات

اختبارات `tests/` منفصلة عن سكربتات التشغيل، وتثبت:

- أن نتيجة الفصل الحالي لا تغير خصائص المقرر التاريخية ولا `X` للصف نفسه.
- صحة وزن `0.25` لما قبل 2022.
- تجميد حالة صعوبة اختبار 2025 من التدريب.
- صحة وزن الساعات والـleave-one-out على مثال يدوي.
- أن `4 → 3` يعطي trend `-1` و`2 → 3` يعطي `+1`.
- أن `20252` يستخدم `20251` ولا يستخدم المستقبل.
- استبعاد raw IDs وأعمدة التسرب من عقد المودل.
- تطبيق جدول الدرجات الرسمي وحدود الخطط وترتيبها.

لتشغيلها:

```powershell
python -m unittest discover -s tests -v
```

الحالة الحالية: **15 اختبارًا ناجحًا**.

## 12. ترتيب إعادة البناء

من جذر المشروع، وبعد معالجة عوائق المصدر بقرار منفصل، ترتيب بناء قسمَي البيانات والخصائص V2 هو:

```powershell
python -m src.data.clean_student_course
python -m src.data.clean_student_status
python -m src.data.filter_common_students
python -m src.data.clean_degree_course
python -m src.data.build_student_course_enriched
python -m src.data.clean_student_diploma
python -m src.data.clean_outliers
python -m src.data.build_temporal_split
python -m src.data.build_registration_roster
python -m src.features.build_temporal_features
```

تنتهي سلسلة V2 هنا. الأوامر التالية مستقلة وتقرأ ملفات V1 الحالية؛ لا تدرّب على مخرجات V2 الجديدة:

```powershell
python src\modeling\train_models.py
python src\evaluation\evaluate_plan_gpa.py
python src\evaluation\analyze_model_errors.py
python src\experiment_degree_points.py
python -m unittest discover -s tests -v
```

هذا الملف هو المرجع الرسمي للمحادثات القادمة: **المودلان ليسا هدف المشروع
النهائي، بل طبقة تقدير داخل نظام يرشح خطة فصلية كاملة**.
