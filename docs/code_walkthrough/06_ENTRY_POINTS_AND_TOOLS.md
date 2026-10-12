# مداخل التنفيذ والأدوات

هذا الفهرس يميز تشغيل الخدمة عن البناء والتوصية المحلية والتجارب. ذكر الأمر أو الحارس توثيق، ولم تُنفذ أدواته في المهمة.

## مدخل خدمة الشبكة

مصنع التطبيق هو مدخل خدمة الويب؛ لا يوجد كائن تطبيق عالمي يحمل المودلات بمجرد استيراد الحزمة.


```text
src.api.app:create_app
```

[شرح المصنع](api/app.md)

صيغة تشغيل المصنع المعروفة، للقراءة فقط هنا:

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.app:create_app --factory
```

هذا الأمر يحتاج تبعيات الويب وإعداد أسرار الخدمة، ولا يمثل اختبار اتصال أو توصية في هذا الدليل.

## مداخل المصدر المباشرة

الوحدات التالية تحتوي حارس تشغيل مباشر. أسماء الوحدات المسجلة نصيًا في المنظم تظهر أيضًا في صفحة المنظم. بعض الأسماء القديمة تفوض إلى وحدة حالية.

[واجهة اسم قديم لقياس المحرك](benchmark_recommendation.md)

```text
src/benchmark_recommendation.py
```

[إنشاء سجل التسجيل الكامل](data/build_registration_roster.md)

```text
src/data/build_registration_roster.py
```

[ربط النتائج بحالة الطالب والخطة](data/build_student_course_enriched.md)

```text
src/data/build_student_course_enriched.py
```

[تقسيم التدريب والاختبار زمنيًا](data/build_temporal_split.md)

```text
src/data/build_temporal_split.py
```

[تنظيف كتالوج الاختصاص](data/clean_degree_course.md)

```text
src/data/clean_degree_course.py
```

[تدقيق القيم المتطرفة واستبعاد الطلاب](data/clean_outliers.md)

```text
src/data/clean_outliers.py
```

[تنظيف نتائج المواد وتكوين المحاولات](data/clean_student_course.md)

```text
src/data/clean_student_course.py
```

[تنظيف الدبلوم وربطه بالطالب](data/clean_student_diploma.md)

```text
src/data/clean_student_diploma.py
```

[تنظيف الحالة وتاريخ التسجيل](data/clean_student_status.md)

```text
src/data/clean_student_status.py
```

[مزامنة مجموعة الطلاب](data/filter_common_students.md)

```text
src/data/filter_common_students.py
```

[تحويل التصدير المحلي إلى سجلات](data/xml_to_json.md)

```text
src/data/xml_to_json.py
```

[تحليل تغير كتالوج الخطة القديم](diagnostics/analyze_course_plan_changes.md)

```text
src/diagnostics/analyze_course_plan_changes.py
```

[تشغيل تدقيق سياسة التوازن الوصفية](diagnostics/analyze_repeat_withdrawal_balance.md)

```text
src/diagnostics/analyze_repeat_withdrawal_balance.py
```

[مقارنة تغطية الحالة والنتائج](diagnostics/compare_student_status_course.md)

```text
src/diagnostics/compare_student_status_course.py
```

[واجهة اسم قديم لتقييم التصدير](evaluate_xml_recommendations.md)

```text
src/evaluate_xml_recommendations.py
```

[تحليل أخطاء النموذج زمنيًا وبحسب المجموعات](evaluation/analyze_model_errors.md)

```text
src/evaluation/analyze_model_errors.py
```

[تقييم معدل الخطط المرصودة](evaluation/evaluate_plan_gpa.md)

```text
src/evaluation/evaluate_plan_gpa.py
```

[تقييم توصيات ملفات التصدير](evaluation/evaluate_xml_recommendations.md)

```text
src/evaluation/evaluate_xml_recommendations.py
```

[واجهة اسم قديم لتجربة النقاط](experiment_degree_points.md)

```text
src/experiment_degree_points.py
```

[مدخل تنفيذ تجربة المواد](experiments/course_only_recommendation.md)

```text
src/experiments/course_only_recommendation.py
```

[تنسيق تجربة أهداف النقاط والاختصاص](experiments/degree_points.md)

```text
src/experiments/degree_points.py
```

[أداة إنشاء لقطة نهائية محددة](features/build_frozen_history.md)

```text
src/features/build_frozen_history.py
```

[تجميع ملفات ميزات التدريب](features/build_temporal_features.md)

```text
src/features/build_temporal_features.py
```

[منظم نقاط التنفيذ وتسلسل البناء](main.md)

```text
src/main.py
```

[تدريب الزوج الرسمي واختيار إعداداته](modeling/train_models.md)

```text
src/modeling/train_models.py
```

[عرض الحالة المحلية للمشروع](project_status.md)

```text
src/project_status.py
```

[واجهة تشغيل التوصية المحلية](recommend_local.md)

```text
src/recommend_local.py
```

[قياس المحرك المحلي](recommendation/benchmark.md)

```text
src/recommendation/benchmark.py
```

[أداة التوصية المحلية](recommendation/local_cli.md)

```text
src/recommendation/local_cli.py
```

[تنسيق تجربة توصيات الحالة السابقة](recommendation_experiments/previous_course_status_experiment.md)

```text
src/recommendation_experiments/previous_course_status_experiment.py
```

[واجهة اسم قديم لتحويل التصدير](xml_2_json.md)

```text
src/xml_2_json.py
```

## خط البناء ومنظم الأقسام

اختيار الخطوة أو القسم يعمل عبر عمليات فرعية. العرض والمعاينة موجودان، لكن تشغيل جميع الخطوات يعيد البناء والملاءمة والتقييم ويشمل تجربة مكلفة. لا تستخدمه كتمرين قراءة.


```text
src.main
--list
--dry-run
--all
--section
--step
--from / --to
```

[شرح المنظم](main.md)

## الأداة المحلية ومسارها المختلف

أمر التوصية المحلي يصل إلى محرك الزوج الرسمي السابق، لا إلى خدمة المرحلتين. مدخلات الملفات واللقطة والقطع صريحة، ومخرجاته محلية.


```text
src.recommend_local -> src.recommendation.local_cli -> AcademicPlanRecommender
```

[شرح المحرك المحلي](recommendation/engine.md)

## جرد الأدوات خارج المصدر

الجرد التالي يحصر إحدى وثلاثين أداة وملف مساعدة واختبارًا بحثيًا. الوظائف العليا الفعلية معروضة لتسهيل فتح موضع الشرح. الاستيراد الداخلي علاقة ثابتة، وليس دليل تشغيل الأداة في خدمة الجامعة.

<a id="tool-1"></a>

### الأداة 1

```text
scripts/benchmark_two_stage.py
```

[الشفرة الموجودة](../../scripts/benchmark_two_stage.py)

يقيس البحث والترتيب والتوقع الدافئ في حالات اصطناعية بعامل جديد لكل قياس. يقرأ أصول المودلات والفئات والسلم فقط؛ لا يجلب طالبًا حقيقيًا. القياس ليس اعتماد أداء خدمة.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
Path(__file__).resolve
Path
SystemExit
main
```

الدوال والأصناف العليا:

```text
synthetic_case
synthetic_history_manager
supported_synthetic_grade_version
_means
_comparison
_final_metrics
measure_case
timing_class
benchmark_jobs
censored_result
run_worker
_write_worker_json
build_report
save_report
main
```

صفحات المصدر المرجعية:

- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [قياس المحرك المحلي](recommendation/benchmark.md)
- [القيود الأكاديمية على الخطط](recommendation/constraints.md)
- [مجاميع الدفعات ومدير اللقطة](recommendation/history_update.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)
- [البحث عن مجموعات بالساعات الدقيقة](recommendation/plan_generation.md)
- [توقع المواد وتلخيص جودة الخطط](recommendation/plan_scoring.md)
- [الهوية والترتيب وجبهات المفاضلة](recommendation/ranking.md)
- [قائمة الخطط المختصرة للمرحلة الأولى](recommendation/shortlist.md)
- [تحميل أصول المرحلتين والتحقق من مصدرها](recommendation/two_stage_artifacts.md)
- [المحرك المعتمد ذو المرحلتين](recommendation/two_stage_engine.md)

<a id="tool-2"></a>

### الأداة 2

```text
scripts/evaluate_corrected_phase6.py
```

[الشفرة الموجودة](../../scripts/evaluate_corrected_phase6.py)

ينشئ دليل استبقاء ومفاضلات بمودلات المرحلتين المثبتة ومدخلات اصطناعية. توقع كامل الثانية هنا مرجع تشخيصي محدود، بينما المحرك يخدم مختصر الخمسين.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
main
```

الدوال والأصناف العليا:

```text
_hash
corrected_fixture
recall_evidence
_tie_signature
_tie_recall
distributions
_top_comparison
compare_fixed_final
tradeoff_examples
_collect
evaluate_fixture
summarize_evidence
build_report
main
```

صفحات المصدر المرجعية:

- [أدوات تنظيف الأعمدة والمعرفات](data/cleaning_utils.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [مجاميع الدفعات ومدير اللقطة](recommendation/history_update.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)
- [توقع المواد وتلخيص جودة الخطط](recommendation/plan_scoring.md)
- [الهوية والترتيب وجبهات المفاضلة](recommendation/ranking.md)
- [قائمة الخطط المختصرة للمرحلة الأولى](recommendation/shortlist.md)
- [تحميل أصول المرحلتين والتحقق من مصدرها](recommendation/two_stage_artifacts.md)
- [المحرك المعتمد ذو المرحلتين](recommendation/two_stage_engine.md)

<a id="tool-3"></a>

### الأداة 3

```text
scripts/evaluate_two_stage_ranking.py
```

[الشفرة الموجودة](../../scripts/evaluate_two_stage_ranking.py)

يبني أدلة مرحلة التقييم السابقة من توقعات اصطناعية ومجاميع حفظت سابقًا؛ لا يحمل مودلات أو تاريخ خدمة ولا يقرر اعتمادًا.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
Path(__file__).resolve
Path
main
```

الدوال والأصناف العليا:

```text
synthetic_fixture
_metrics
_change
_diagnostic_stage2
_top_comparison
evaluate_synthetic
_mix_courses
_synthetic_eligible
evaluate_historical_policy
evaluate_sensitivities
evaluate_mixed_scope
build_evaluation_report
save_report
main
```

صفحات المصدر المرجعية:

- [مكونات التوازن الناعم](recommendation/balance_policy.md)
- [القيود الأكاديمية على الخطط](recommendation/constraints.md)
- [الهوية والترتيب وجبهات المفاضلة](recommendation/ranking.md)
- [قائمة الخطط المختصرة للمرحلة الأولى](recommendation/shortlist.md)

<a id="tool-4"></a>

### الأداة 4

```text
scripts/experiments/attempt_number_experiment.py
```

[الشفرة الموجودة](../../scripts/experiments/attempt_number_experiment.py)

نقطة تنفيذ صريحة لتجربة رقم المحاولة، تنسق التدريب والتحليل والتقرير وتحقق الحماية. بعض الخطوات مكلفة وتكتب أصول تجربة.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
main
```

الدوال والأصناف العليا:

```text
source_signature
save_provenance
main
```

صفحات المصدر المرجعية:

- [تحليل أثر رقم المحاولة](experiments/attempt_number_analysis.md)
- [أدوات تجربة رقم المحاولة](experiments/attempt_number_core.md)
- [تقرير تجربة المحاولة](experiments/attempt_number_report.md)
- [ملاءمة صيغ تجربة المحاولة](experiments/attempt_number_training.md)
- [إعادة حساب مرجع تجربة المحاولة](experiments/attempt_number_validation.md)
- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)
- [مرجع المسارات والإصدارات](paths.md)

<a id="tool-5"></a>

### الأداة 5

```text
scripts/experiments/attempt_number_recommendation.py
```

[الشفرة الموجودة](../../scripts/experiments/attempt_number_recommendation.py)

مساعدة بحثية تقارن حذف أو تغيير المحاولة على طلبات مصدرة مع آليات الخطة نفسها. ليست نقطة تقديم معتمدة للجامعة.

لا يظهر حارس التشغيل القياسي في الجرد؛ بعض ملفات التشخيص تنفذ عملًا في المستوى الأعلى. اقرأ آثارها قبل الاستيراد.

الدوال والأصناف العليا:

```text
select_cases
run_recommendations
```

صفحات المصدر المرجعية:

- [أدوات تنظيف الأعمدة والمعرفات](data/cleaning_utils.md)
- [تحليل أثر رقم المحاولة](experiments/attempt_number_analysis.md)
- [أدوات تجربة رقم المحاولة](experiments/attempt_number_core.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [مرجع المسارات والإصدارات](paths.md)
- [المحرك المحلي ذو الزوج الواحد](recommendation/engine.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)
- [البحث عن مجموعات بالساعات الدقيقة](recommendation/plan_generation.md)
- [توقع المواد وتلخيص جودة الخطط](recommendation/plan_scoring.md)

<a id="tool-6"></a>

### الأداة 6

```text
scripts/experiments/attempt_number_removal_recheck.py
```

[الشفرة الموجودة](../../scripts/experiments/attempt_number_removal_recheck.py)

إعادة فحص حذف المحاولة بإعداد ثابت على عقدي المادة والخطة، في مخرجات بحثية معزولة. قد تدرب وتقيم؛ لا تُشغّل ضمن القراءة.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
argparse.ArgumentParser
parser.add_argument
run
parser.parse_args
```

الدوال والأصناف العليا:

```text
families
evaluate
run
```

صفحات المصدر المرجعية:

- [ملاءمة صيغ تجربة المحاولة](experiments/attempt_number_training.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)
- [تحويل العلامة إلى نقاط وفق النسخة](grade_scale.md)
- [الأهداف وأوزان التدريب](modeling/training_config.md)
- [مرجع المسارات والإصدارات](paths.md)

<a id="tool-7"></a>

### الأداة 7

```text
scripts/experiments/student_progress_20261010/complete_registration.py
```

[الشفرة الموجودة](../../scripts/experiments/student_progress_20261010/complete_registration.py)

مقاييس إضافية للخطط المرصودة التي تطابق كامل سجل التسجيل.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
run
```

الدوال والأصناف العليا:

```text
run
```

صفحات المصدر المرجعية:

- [تحويل العلامة إلى نقاط وفق النسخة](grade_scale.md)

<a id="tool-8"></a>

### الأداة 8

```text
scripts/experiments/student_progress_20261010/coverage.py
```

[الشفرة الموجودة](../../scripts/experiments/student_progress_20261010/coverage.py)

قياس تغطية خطط التقييم لسياق التسجيل الكامل القائم.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
run
```

الدوال والأصناف العليا:

```text
run
```

<a id="tool-9"></a>

### الأداة 9

```text
scripts/experiments/student_progress_20261010/data_analysis.py
```

[الشفرة الموجودة](../../scripts/experiments/student_progress_20261010/data_analysis.py)

تدقيق وصفي لتقدم الطالب من المصادر؛ لا يحمل مودلات أو أهداف سنة الاختبار اللاحقة، لكنه يحفظ تقريرًا.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
Path(__file__).resolve
Path
main
```

الدوال والأصناف العليا:

```text
save
numeric
window
stats
corr
pair_stats
mapping
identity
table
main
```

<a id="tool-10"></a>

### الأداة 10

```text
scripts/experiments/student_progress_20261010/downstream.py
```

[الشفرة الموجودة](../../scripts/experiments/student_progress_20261010/downstream.py)

حساسية ترتيب مرشحين وتجربة تبديل خطط داخل التحقق فقط، مع إعادة بناء السياق.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
run
```

الدوال والأصناف العليا:

```text
validated_model
candidate_rows
run
```

صفحات المصدر المرجعية:

- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [تحويل العلامة إلى نقاط وفق النسخة](grade_scale.md)

<a id="tool-11"></a>

### الأداة 11

```text
scripts/experiments/student_progress_20261010/evidence/executed_workflow.py
```

[الشفرة الموجودة](../../scripts/experiments/student_progress_20261010/evidence/executed_workflow.py)

نسخة مصدر محفوظة ضمن دليل تجربة تقدم الطالب المنفذة؛ ليست مستوردًا في خدمة التوصية. وجود حارس تشغيل لا يجعلها أداة ينبغي إعادة تشغيلها.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
enumerate
argparse.ArgumentParser
parser.add_argument
parser.parse_args
print
run
verify_protected
```

الدوال والأصناف العليا:

```text
write_json
feature_subset
temporal_partition
configuration_signature
validate_signature
protected_manifest
verify_protected
load_train
specs
matrix
aggregate_points
predict
evaluate
fit_model
inner_selection
gain_rows
permutation
group_metrics
run
```

صفحات المصدر المرجعية:

- [أدوات تجربة رقم المحاولة](experiments/attempt_number_core.md)
- [تاريخ الاختصاص التجريبي](experiments/specialty_history.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [تحويل العلامة إلى نقاط وفق النسخة](grade_scale.md)
- [الأهداف وأوزان التدريب](modeling/training_config.md)

<a id="tool-12"></a>

### الأداة 12

```text
scripts/experiments/student_progress_20261010/report.py
```

[الشفرة الموجودة](../../scripts/experiments/student_progress_20261010/report.py)

يجمع تقرير التجربة من أدلة محلية منفذة ومتحقق من مصدرها.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
build
```

الدوال والأصناف العليا:

```text
table
deltas
build
```

صفحات المصدر المرجعية:

- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)

<a id="tool-13"></a>

### الأداة 13

```text
scripts/experiments/student_progress_20261010/safeguards.py
```

[الشفرة الموجودة](../../scripts/experiments/student_progress_20261010/safeguards.py)

يتحقق من أصالة أدلة التجربة ويسجل الاكتمال بعد فحص حماية الأصول.

لا يظهر حارس التشغيل القياسي في الجرد؛ بعض ملفات التشخيص تنفذ عملًا في المستوى الأعلى. اقرأ آثارها قبل الاستيراد.

الدوال والأصناف العليا:

```text
sign_record
authenticate_record
authenticate_selection
publish_completion
```

<a id="tool-14"></a>

### الأداة 14

```text
scripts/experiments/student_progress_20261010/test_downstream.py
```

[الشفرة الموجودة](../../scripts/experiments/student_progress_20261010/test_downstream.py)

اختبارات حساسية المرشحين تشترط إعادة بناء سياق الخطة بلا قراءة نتيجة الهدف.

لا يظهر حارس التشغيل القياسي في الجرد؛ بعض ملفات التشخيص تنفذ عملًا في المستوى الأعلى. اقرأ آثارها قبل الاستيراد.

الدوال والأصناف العليا:

```text
pool
test_exact_candidates_recompute_plan_and_peer_context
test_candidate_choice_and_context_are_outcome_independent
```

صفحات المصدر المرجعية:

- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)

<a id="tool-15"></a>

### الأداة 15

```text
scripts/experiments/student_progress_20261010/test_safeguards.py
```

[الشفرة الموجودة](../../scripts/experiments/student_progress_20261010/test_safeguards.py)

اختبارات أصالة الأدلة وعدم إعلان اكتمال غير مثبت.

لا يظهر حارس التشغيل القياسي في الجرد؛ بعض ملفات التشخيص تنفذ عملًا في المستوى الأعلى. اقرأ آثارها قبل الاستيراد.

الدوال والأصناف العليا:

```text
test_tuning_record_rejects_changed_rounds_and_unsigned_cache
test_failure_to_verify_cannot_leave_complete
test_complete_is_published_only_after_verification
test_tuning_selection_accepts_only_matching_context
test_signed_tuning_selection_cannot_be_transplanted
```

<a id="tool-16"></a>

### الأداة 16

```text
scripts/experiments/student_progress_20261010/test_workflow.py
```

[الشفرة الموجودة](../../scripts/experiments/student_progress_20261010/test_workflow.py)

اختبارات حواجز تجربة تقدم الطالب المعزولة.

لا يظهر حارس التشغيل القياسي في الجرد؛ بعض ملفات التشخيص تنفذ عملًا في المستوى الأعلى. اقرأ آثارها قبل الاستيراد.

الدوال والأصناف العليا:

```text
test_subsets_preserve_other_features_and_order
test_inner_partition_never_sees_outer_or_holdout
test_plan_gpa_weights_credits_and_excludes_zero_denominator
test_signature_rejects_different_features_and_parameters
test_experiment_names_cannot_escape_isolated_roots
test_named_experiment_uses_both_isolated_roots
```

<a id="tool-17"></a>

### الأداة 17

```text
scripts/experiments/student_progress_20261010/verify_artifacts.py
```

[الشفرة الموجودة](../../scripts/experiments/student_progress_20261010/verify_artifacts.py)

يراجع أصول ملاءمة التجربة مقابل المصدر والصفوف والإعداد وترتيب الميزات.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
run
```

الدوال والأصناف العليا:

```text
run
```

صفحات المصدر المرجعية:

- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)

<a id="tool-18"></a>

### الأداة 18

```text
scripts/experiments/student_progress_20261010/workflow.py
```

[الشفرة الموجودة](../../scripts/experiments/student_progress_20261010/workflow.py)

تجربة حذف وإضافة ميزات تقدم الطالب بتحقق زمني داخلي؛ لا تحمل صفوف هدف الاختبار اللاحق. لها آثار تدريب وكتابة معزولة.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
enumerate
argparse.ArgumentParser
parser.add_argument
parser.parse_args
experiment_directories
print
run
verify_protected
```

الدوال والأصناف العليا:

```text
write_json
feature_subset
temporal_partition
configuration_signature
validate_signature
experiment_directories
implementation_signature
protected_manifest
verify_protected
load_train
specs
matrix
aggregate_points
predict
evaluate
fit_model
selection_context
inner_selection
gain_rows
permutation
group_metrics
run
```

صفحات المصدر المرجعية:

- [أدوات تجربة رقم المحاولة](experiments/attempt_number_core.md)
- [تاريخ الاختصاص التجريبي](experiments/specialty_history.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [تحويل العلامة إلى نقاط وفق النسخة](grade_scale.md)
- [الأهداف وأوزان التدريب](modeling/training_config.md)

<a id="tool-19"></a>

### الأداة 19

```text
scripts/promote_shortlist_artifacts.py
```

[الشفرة الموجودة](../../scripts/promote_shortlist_artifacts.py)

يرقي أصول الثلاثة والثلاثين الموجودة بنسخ مطابق البايتات بعد فحص المصدر والعقد والهدف. لا يدرب ولا يجدد تجربة، ووجهة الأصول المعتمدة منفصلة.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
promote_shortlist_artifacts
print
```

الدوال والأصناف العليا:

```text
verify_training_sources
build_promotion_manifest
promote_shortlist_artifacts
```

صفحات المصدر المرجعية:

- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)
- [تحميل أصول المرحلتين والتحقق من مصدرها](recommendation/two_stage_artifacts.md)

<a id="tool-20"></a>

### الأداة 20

```text
scripts/rebuild_common_students_v2.py
```

[الشفرة الموجودة](../../scripts/rebuild_common_students_v2.py)

يعيد بناء خطوات بيانات وميزات النسخة الثانية المصرح بها ويكتب دليل حماية للمدخلات؛ له آثار إعادة بناء ولا يدخل مسار طلب الخدمة.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
main
```

الدوال والأصناف العليا:

```text
digest
compare
main
```

<a id="tool-21"></a>

### الأداة 21

```text
scripts/rerun_corrected_phase6.py
```

[الشفرة الموجودة](../../scripts/rerun_corrected_phase6.py)

يعيد قياسات الاستدلال القديمة بعامل وحدود وقت مماثلة مع حفظ التقارير السابقة؛ لا يمنح اعتماد استراتيجية.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
SystemExit
main
```

الدوال والأصناف العليا:

```text
classify_old_evidence
corrected_jobs
validate_replacement
assemble_corrected_results
archive_old_evidence
_hash_file
protected_inventory
run_corrected_benchmarks
main
```

<a id="tool-22"></a>

### الأداة 22

```text
scripts/scan_student_over_polict.py
```

[الشفرة الموجودة](../../scripts/scan_student_over_polict.py)

يفحص تسجيلات مصدر جامعي خام ويصدر مجموعات حمل منخفض مع صف لكل مادة وحالة دقيقة. المخرجات قد تحتوي بيانات شخصية؛ لا تستخدمها عينات عامة.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
Path(__file__).resolve
Path
main
```

الدوال والأصناف العليا:

```text
cohort_counts
main
```

صفحات المصدر المرجعية:

- [أدوات تنظيف الأعمدة والمعرفات](data/cleaning_utils.md)

<a id="tool-23"></a>

### الأداة 23

```text
scripts/scan_under_12_after_status_change.py
```

[الشفرة الموجودة](../../scripts/scan_under_12_after_status_change.py)

يقارن حملًا مسجلًا بمواد نجاح ورسوب داخل التصدير نفسه؛ ليس تاريخ تعديل تسجيل مؤرخًا، ولا قاعدة أهلية.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
Path(__file__).resolve
Path
main
```

الدوال والأصناف العليا:

```text
count
main
```

صفحات المصدر المرجعية:

- [أدوات تنظيف الأعمدة والمعرفات](data/cleaning_utils.md)

<a id="tool-24"></a>

### الأداة 24

```text
scripts/verify_cleaning_policy_v2.py
```

[الشفرة الموجودة](../../scripts/verify_cleaning_policy_v2.py)

يتحقق من سياسة تنظيف النسخة الثانية عبر إعادة بناء مصرح بها، ويدقق النسخة الأولى بلا تعديل. الاسم لا يعني فحص قراءة خالصًا.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
main
```

الدوال والأصناف العليا:

```text
audit_policy
compare_tables
verify_policy_only
main
```

صفحات المصدر المرجعية:

- [أدوات تنظيف الأعمدة والمعرفات](data/cleaning_utils.md)

<a id="tool-25"></a>

### الأداة 25

```text
scripts/verify_data_features_v2.py
```

[الشفرة الموجودة](../../scripts/verify_data_features_v2.py)

أداة تحقق ترحيل أحادية ترفض استبدال مخرجات قائمة وتحتاج سجل مصدر سابقًا؛ يمكن أن تنشئ بيانات، فلا تُشغّل أثناء التوثيق.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
main
```

الدوال والأصناف العليا:

```text
signature
describe
compare
original_cleaner
main
```

صفحات المصدر المرجعية:

- [تنظيف الدبلوم وربطه بالطالب](data/clean_student_diploma.md)

<a id="tool-26"></a>

### الأداة 26

```text
debugging/explain_recommendation.py
```

[الشفرة الموجودة](../../debugging/explain_recommendation.py)

يجمع مخرجات توصية فعلية لأجل شرح شفرة الإنتاج على حالتين. مع أنه لا يغير المصدر أو المودل فإنه يشغّل توصيات، لذلك لم يستخدم في هذه المهمة.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
Path(__file__).resolve
Path
sys.path.insert
str
datetime.now(timezone.utc).strftime
datetime.now
hasattr
main
sys.stdout.reconfigure
```

الدوال والأصناف العليا:

```text
check
records
save
read_export
summarize_all
course_math
collect_term
main
```

صفحات المصدر المرجعية:

- [تنظيف الحالة وتاريخ التسجيل](data/clean_student_status.md)
- [خوارزميات ملاءمة التجارب وتقييمها](experiments/modeling.md)
- [تاريخ الاختصاص التجريبي](experiments/specialty_history.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)

<a id="tool-27"></a>

### الأداة 27

```text
debugging/pipeline_audit.py
```

[الشفرة الموجودة](../../debugging/pipeline_audit.py)

تدقيق تشخيصي يقرأ ملفات ويكتب مجلد تقرير مؤرخًا. فيه عمل على المستوى الأعلى، واستيراده ليس مضمونًا بلا آثار كتابة.

لا يظهر حارس التشغيل القياسي في الجرد؛ بعض ملفات التشخيص تنفذ عملًا في المستوى الأعلى. اقرأ آثارها قبل الاستيراد.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
Path(__file__).resolve
Path
sys.path.insert
str
datetime.now(timezone.utc).strftime
datetime.now
OUT.mkdir
progress
sorted
(ROOT / 'src').rglob
(ROOT / 'models').rglob
p.is_file
```

الدوال والأصناف العليا:

```text
records
save
progress
metrics
```

صفحات المصدر المرجعية:

- [تدقيق القيم المتطرفة واستبعاد الطلاب](data/clean_outliers.md)
- [تنظيف الحالة وتاريخ التسجيل](data/clean_student_status.md)
- [أدوات تنظيف الأعمدة والمعرفات](data/cleaning_utils.md)
- [خوارزميات ملاءمة التجارب وتقييمها](experiments/modeling.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [تدريب الزوج الرسمي واختيار إعداداته](modeling/train_models.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)

<a id="tool-28"></a>

### الأداة 28

```text
debugging/pipeline_audit_details.py
```

[الشفرة الموجودة](../../debugging/pipeline_audit_details.py)

فحوص إضافية تقرأ البيانات وتكتب في مجلد تدقيق موجود يمرره المشغل. عمله على المستوى الأعلى؛ ليس مكتبة نقية للطلب.

لا يظهر حارس التشغيل القياسي في الجرد؛ بعض ملفات التشخيص تنفذ عملًا في المستوى الأعلى. اقرأ آثارها قبل الاستيراد.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
Path(__file__).resolve
Path
sys.path.insert
str
Path(sys.argv[1]).resolve
OUT.is_relative_to
(paths.EVALUATION_DIR / 'pipeline_audits').resolve
pd.read_parquet
clean_id_columns
raw[c].astype('string').str.strip().str.upper
raw[c].astype('string').str.strip
raw[c].astype
```

الدوال والأصناف العليا:

```text
records
save
```

صفحات المصدر المرجعية:

- [تدقيق القيم المتطرفة واستبعاد الطلاب](data/clean_outliers.md)
- [أدوات تنظيف الأعمدة والمعرفات](data/cleaning_utils.md)
- [خوارزميات ملاءمة التجارب وتقييمها](experiments/modeling.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)

<a id="tool-29"></a>

### الأداة 29

```text
debugging/render_recommendation_explanation.py
```

[الشفرة الموجودة](../../debugging/render_recommendation_explanation.py)

يصوغ شرحًا من مقتطفات إنتاج وقياسات محفوظة، ويفصل العرض عن حساب القيم. يكتب مستندات شرح عند تشغيله.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
Path(__file__).resolve
Path
sys.path.insert
str
set
main
```

الدوال والأصناف العليا:

```text
fmt
p
formula
table
code
group_name
context_math
sections
main
```

صفحات المصدر المرجعية:

- [تاريخ الاختصاص التجريبي](experiments/specialty_history.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)

<a id="tool-30"></a>

### الأداة 30

```text
debugging/run_trace.py
```

[الشفرة الموجودة](../../debugging/run_trace.py)

ينفذ خلايا ملف تتبع ويحفظ مخططًا ودفترًا وتقرير عرض محليًا. التنفيذ قد يشغّل توصية؛ لا يساوي قراءة الملف.

يوجد حارس تشغيل مباشر؛ تنفيذه قد يكتب أو يتوقع أو يدرب حسب غرض الأداة.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
Path(__file__).resolve
Path
Path(__file__).with_name
datetime.now(timezone.utc).strftime
datetime.now
hasattr
SystemExit
sys.stdout.reconfigure
main
```

الدوال والأصناف العليا:

```text
main
```

<a id="tool-31"></a>

### الأداة 31

```text
debugging/trace_student_29485_20251.py
```

[الشفرة الموجودة](../../debugging/trace_student_29485_20251.py)

ملف خلايا تشخيص حالة طالب محلي سابق، يتضمن إعدادًا وقراءة بيانات وتوقعات وحفظ أثر على المستوى الأعلى. يرد هنا مساره لأجل الجرد فقط؛ لا تنقل بياناته إلى أمثلة عامة ولا تستورده للتجربة.

لا يظهر حارس التشغيل القياسي في الجرد؛ بعض ملفات التشخيص تنفذ عملًا في المستوى الأعلى. اقرأ آثارها قبل الاستيراد.

نداءات فعلية على المستوى الأعلى أو داخل حارس التشغيل:

```text
next
(p / 'src/recommendation/engine.py').exists
Path.cwd
str
sys.path.insert
Path
globals().get
globals
datetime.now(timezone.utc).strftime
datetime.now
OUT.mkdir
range
```

الدوال والأصناف العليا:

```text
check
show
save_json
records
source
read_export
capture_score_rows
family
```

صفحات المصدر المرجعية:

- [تنظيف الحالة وتاريخ التسجيل](data/clean_student_status.md)
- [خوارزميات ملاءمة التجارب وتقييمها](experiments/modeling.md)
- [تاريخ الاختصاص التجريبي](experiments/specialty_history.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)

## ما لم يُنفذ

لا تدريب أو إعادة بناء أو قياس أداء أو توصية فعلية أو ترقية أصول أو تفعيل تاريخ. جرى تحليل الشفرة والبيانات الوصفية وسجل اختبار سابق فقط.

