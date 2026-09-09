إي، الدقة الحالية كافية لننتقل إلى تجربة Shadow على طلاب حقيقيين، لكنها ليست كافية بعد لإطلاق توصيات نهائية للطلاب.

السبب:

- خطأ العلامة `MAE = 9.15` مقبول كنموذج أولي.
- خطأ معدل الخطة تحسن من `0.376` إلى `0.345`، أي تحسن `8.34%`.
- مصنّف الرسوب عنده `ROC-AUC = 0.903`، وهي نتيجة قوية، لكن `PR-AUC = 0.524` ما زالت متوسطة.
- الأهم: قسنا دقة معدل الخطة الفعلية، لكن لم نقس بعد هل المودل يرتب الخطط البديلة بالترتيب الصحيح.

الخلاصة:

> كافية لنبدأ تجربة الترشيح ونفهم سلوك النظام، وليست كافية لنقول إن أعلى خطة متوقعة هي فعلًا الأفضل للطالب.

## الأولوية الحالية

لا تضيف features أو تجارب جديدة الآن. أعطِ نفسك 2–3 أيام لفهم هذه السلسلة فقط:

```text
feature contract
      ↓
temporal features
      ↓
training
      ↓
Expected Points experiment
      ↓
plan scoring
      ↓
recommendation
```

## اليوم الأول: كيف تُبنى الخصائص — حوالي 4.5 ساعات

| الملف | الوقت | ماذا يجب أن تفهم؟ |
|---|---:|---|
| [START_HERE.md](<D:/AI/Real projects/Academic_Advisor_Simple/START_HERE.md>) | 20 دقيقة | أين نحن وما المسار الرسمي |
| [PIPELINE_README.md](<D:/AI/Real projects/Academic_Advisor_Simple/PIPELINE_README.md>) | 40 دقيقة | اقرأ الخريطة، ولا تحفظ التفاصيل |
| [paths.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/paths.py>) | 10 دقائق | أماكن المدخلات والمخرجات |
| [feature_contract.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/feature_contract.py>) | 40 دقيقة | ما يدخل المودل، categorical، target، الأوزان وأعمدة التسرب |
| [temporal_features.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/temporal_features.py>) | ساعتان | أهم ملف: تاريخ المقرر، تاريخ الطالب، GPA trend وخصائص حمل الخطة |
| [build_temporal_features.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/build_temporal_features.py>) | 30 دقيقة | كيف تُجمع الخصائص السابقة في ملف واحد |
| [test_temporal_features.py](<D:/AI/Real projects/Academic_Advisor_Simple/tests/test_temporal_features.py>) | 40 دقيقة | افهم منه كيف نمنع التسرب الزمني |

داخل `temporal_features.py` ركّز فقط على:

- `CourseHistoryState`
- `build_temporal_course_history`
- `add_student_history_features`
- `compute_plan_context_features`

## اليوم الثاني: التدريب والتقييم — حوالي 4 ساعات

| الملف | الوقت | ماذا يجب أن تفهم؟ |
|---|---:|---|
| [train_models.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/train_models.py>) | ساعتان | التقسيم الزمني، tuning، وزن السجلات، تدريب المودلين |
| [model_metadata.json](<D:/AI/Real projects/Academic_Advisor_Simple/models/model_metadata.json>) | 20 دقيقة | الإعدادات والخصائص والنتائج الفعلية |
| [grade_scale.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/grade_scale.py>) | 15 دقيقة | تحويل العلامة إلى points |
| [evaluate_plan_gpa.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/evaluate_plan_gpa.py>) | 45 دقيقة | تجميع توقعات المواد إلى معدل خطة |
| [test_plan_gpa_evaluation.py](<D:/AI/Real projects/Academic_Advisor_Simple/tests/test_plan_gpa_evaluation.py>) | 15 دقيقة | التأكد من معادلة المعدل |
| [model_improvement_table.md](<D:/AI/Real projects/Academic_Advisor_Simple/reports/model_improvement_table.md>) | 20 دقيقة | مقارنة كل تحسين بالـbaseline |
| [model_error_analysis.md](<D:/AI/Real projects/Academic_Advisor_Simple/reports/model_error_analysis.md>) | 20 دقيقة | أين يخطئ المودل أكثر |

لا تقرأ الآن `analyze_model_errors.py` كاملًا؛ هو 572 سطرًا وتفاصيله ليست ضرورية لفهم التدريب.

## اليوم الثالث: آخر تعديلين والترشيح — حوالي 4.5 ساعات

| الملف | الوقت | ماذا يجب أن تفهم؟ |
|---|---:|---|
| [experiment_degree_points.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/experiment_degree_points.py>) | 5 دقائق | مجرد نقطة تشغيل |
| [degree_points.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/experiments/degree_points.py>) | 60 دقيقة | التجارب، المقارنة واختيار النسخة الفائزة |
| [specialty_history.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/experiments/specialty_history.py>) | 50 دقيقة | خصائص تاريخ الاختصاص دون تسرب |
| [modeling.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/experiments/modeling.py>) | 70 دقيقة | تدريب points، وزن الساعات، وتجميع الخطة |
| [test_degree_points_experiment.py](<D:/AI/Real projects/Academic_Advisor_Simple/tests/test_degree_points_experiment.py>) | 20 دقيقة | إثبات صحة وزن الساعات والخصائص |
| [recommendation.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/recommendation.py>) | 90 دقيقة | توليد الخطط، إعادة حساب الحمل، التصفية والترتيب |
| [test_recommendation.py](<D:/AI/Real projects/Academic_Advisor_Simple/tests/test_recommendation.py>) | 25 دقيقة | أمثلة صغيرة توضح اختيار الخطط |

داخل `modeling.py` ركّز على:

- `fit_weights`: لماذا الوزن `course_credits × temporal_weight`.
- `fit_experiment_model`: كيف يتدرب مودل points.
- `aggregate_plans`: كيف تتحول المواد إلى معدل خطة.
- `prediction_metrics`: كيف نقارن الخطط.

وداخل `recommendation.py` ركّز على:

- `enumerate_plan_indices`
- `build_plan_rows`
- `summarize_scored_plans`
- `AcademicPlanRecommender`

## ملفات لا تعطيها وقتًا كبيرًا الآن

سكربتات `clean_*` والدمج والتقسيم راجع لكل واحد منها 10–20 دقيقة فقط: المدخل، الفلترة، والمخرج. أنت لا تحتاج فهم كل سطر فيها قبل تجربة الترشيح.

كذلك أجّل القراءة التفصيلية لـ:

- `analyze_model_errors.py`
- `compare_student_status_course.py`
- `analyze_course_plan_changes.py`

الخطة العملية بعد الأيام الثلاثة:

1. نتأكد أنك قادر تشرح مسار صف واحد من parquet حتى توقع الخطة.
2. ندمج مودل Expected Points الفائز داخل محرك الترشيح.
3. نجرب على 10–20 طالبًا فقط.
4. نعطيه المواد المتاحة والحمل المسموح.
5. نحفظ أفضل خمس خطط قبل النظر لاختيارات ونتائج الطلاب.
6. بعدها نقرر إذا نحتاج تحسين الدقة أو أن مشكلة الترتيب موجودة بمكان آخر.

لا تجعل هدفك فهم كل سطر. إذا استطعت تفسير: «من أين جاءت الخاصية؟ هل هي متاحة وقت التسجيل؟ كيف أثرت في points؟ وكيف جُمعت على مستوى الخطة؟» فأنت فهمت الجزء المهم من المشروع.