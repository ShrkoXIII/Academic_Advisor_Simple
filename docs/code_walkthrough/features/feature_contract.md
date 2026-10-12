# العقد المرتب لميزات المودل

```text
src/features/feature_contract.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يثبت قائمة الميزات وترتيبها وأنواعها ومستويات الفئات؛ أسماء الأعمدة وحدها لا تكفي لتوافق مصفوفة مع مودل محفوظ.

الدور في الخريطة:
ميزات مشتركة

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تحليل أخطاء النموذج زمنيًا وبحسب المجموعات](../evaluation/analyze_model_errors.md)
- [تقييم معدل الخطط المرصودة](../evaluation/evaluate_plan_gpa.md)
- [ملاءمة صيغ تجربة المحاولة](../experiments/attempt_number_training.md)
- [إعادة حساب مرجع تجربة المحاولة](../experiments/attempt_number_validation.md)
- [حساب البحث على ميزات المادة فقط](../experiments/course_only_core.md)
- [تدريب تجربة المواد المستقلة](../experiments/course_only_training.md)
- [تنسيق تجربة أهداف النقاط والاختصاص](../experiments/degree_points.md)
- [إعداد تجربة الاختصاص والنقاط](../experiments/degree_points_config.md)
- [ملفات تجربة الاختصاص ومصدرها](../experiments/experiment_io.md)
- [خوارزميات ملاءمة التجارب وتقييمها](../experiments/modeling.md)
- [تقييم المودلات الموسعة بالحالة السابقة](../experiments/previous_course_status_evaluation.md)
- [تدريب الحالة السابقة كميزة إضافية](../experiments/previous_course_status_training.md)
- [أداة إنشاء لقطة نهائية محددة](build_frozen_history.md)
- [تجميع ملفات ميزات التدريب](build_temporal_features.md)
- [بناء وتحميل الحزم التاريخية الثابتة](frozen_history.md)
- [تدريب الزوج الرسمي واختيار إعداداته](../modeling/train_models.md)

## ٣. المدخلات

جدول ميزات وبيانات إصدار ومستويات فئوية متعلمة من التدريب، مع قائمة ميزات كاملة أو مجموعة مدعومة للمرحلة الأولى.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

أسماء الحقول المعرّفة في الملف:

```text
CATEGORICAL_FEATURES
plan_course_type_id
plan_requirement_type_id
diploma_type_id
grade_version_id
part_semester
```

أسماء الحقول المعرّفة في الملف:

```text
NUMERIC_FEATURES
gpa_prev_1
gpa_prev_2
gpa_trend_delta
gpa_trend_missing
start_agpa_points
start_total_in_courses
start_total_in_credits
prior_total_reg_courses
prior_total_reg_credits
prior_total_fail_courses
prior_total_fail_credits
prior_fail_credit_ratio
prior_registered_semesters
observed_gap_semesters
diploma_gpa
course_credits
attempt_number
plan_year_order
plan_semester_order
plan_credits_count
degree_credits_count
course_history_avg_mark
course_history_fail_rate
course_history_avg_attempt
course_history_retake_rate
course_history_effective_support
course_history_fallback_level
course_history_missing
plan_course_count
plan_total_credits
plan_credit_weighted_fail_rate
plan_credit_weighted_avg_mark
plan_credit_weighted_avg_attempt
plan_difficulty_credit_load
peer_course_count
peer_total_credits
peer_credit_weighted_fail_rate
peer_credit_weighted_avg_mark
peer_credit_weighted_avg_attempt
peer_difficulty_credit_load
peer_max_fail_rate
peer_difficulty_missing
```

أسماء الحقول المعرّفة في الملف:

```text
LEAKAGE_COLUMNS
final_mark
is_fail
points
grade_id
course_outcome_status
gpa_points
end_agpa_points
end_total_in_courses
end_total_in_credits
semester_pass_courses
semester_pass_credits
semester_fail_courses
semester_fail_credits
reg_total_semesters
total_pass_courses
total_pass_credits
finish_part_id
finish_status
```

أسماء الحقول المعرّفة في الملف:

```text
RAW_ID_COLUMNS
student_course_id
student_status_id
student_id
course_id
degree_id
faculty_id
plan_degree_course_id
```

الأنواع والبنى المستعملة في هذا الحد:

```text
frame: pandas.DataFrame
category_levels: dict[str, list[str]]
model_features: optional ordered list
```

## ٤. المخرجات

مصفوفة عددية وفئوية مرتبة، أو ملفات مستويات الفئات، أو رفض إصدار غير مطابق.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

أنواع المخرجات الأساسية:

```text
prepare_model_matrix(...) -> pandas.DataFrame
numeric dtype: float32
categorical dtype: category
```

## ٥. الدوال والأصناف

الجدول يحصر جميع الدوال والأصناف المعرفة في المستوى الأعلى. عمود المستدعي يعتمد نداء رمز يمكن حله من الشفرة؛ الاستخدام عبر كائن محقون أو استيراد ديناميكي يُشرح في التسلسل، ولا يُنفى عند غياب رابط مباشر.

<table>
<thead>
<tr>
<th>
الدالة أو الصنف
</th>
<th>
الغرض
</th>
<th>
المدخل
</th>
<th>
المخرج أو تعبيره الفعلي
</th>
<th>
من يستدعيه
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>require_current_features</code>
</td>
<td>
رفض إصدار هندسة غير مطابق.
</td>
<td>
<pre>require_current_features(metadata)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="../experiments/course_only_training.md">صفحة المستدعي</a>
<br>
<code>train_experiment</code>
<br>
<a href="../experiments/course_only_training.md">صفحة المستدعي</a>
<br>
<code>load_experiment</code>
<br>
<a href="../experiments/degree_points.md">صفحة المستدعي</a>
<br>
<code>load_feature_frames</code>
<br>
<a href="../experiments/degree_points.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="../experiments/previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>_load_tables</code>
</td>
</tr>
<tr>
<td>
<code>learn_category_levels</code>
</td>
<td>
تعلم قاموس الفئات من التدريب فقط.
</td>
<td>
<pre>learn_category_levels(frame)</pre>
</td>
<td>
<pre>levels</pre>
</td>
<td>
<a href="../experiments/course_only_training.md">صفحة المستدعي</a>
<br>
<code>train_experiment</code>
<br>
<a href="../experiments/previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>learn_augmented_levels</code>
<br>
<a href="../modeling/train_models.md">صفحة المستدعي</a>
<br>
<code>prepare_folds</code>
<br>
<a href="../modeling/train_models.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="../evaluation/analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>fit_historical_grade_model</code>
</td>
</tr>
<tr>
<td>
<code>prepare_model_matrix</code>
</td>
<td>
تكوين المصفوفة المرتبة بالعقد ومستويات ثابتة.
</td>
<td>
<pre>prepare_model_matrix(frame, category_levels, *, model_features=None)</pre>
</td>
<td>
<pre>matrix[features]</pre>
</td>
<td>
<a href="../experiments/course_only_training.md">صفحة المستدعي</a>
<br>
<code>train_experiment</code>
<br>
<a href="../experiments/previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>evaluate_holdout</code>
<br>
<a href="../experiments/previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>prepare_augmented_matrix</code>
<br>
<a href="../modeling/train_models.md">صفحة المستدعي</a>
<br>
<code>prepare_folds</code>
<br>
<a href="../modeling/train_models.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>save_category_levels</code>
</td>
<td>
حفظ مستويات الفئات المتوافقة مع الأصول.
</td>
<td>
<pre>save_category_levels(category_levels, path)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="../experiments/course_only_training.md">صفحة المستدعي</a>
<br>
<code>train_experiment</code>
<br>
<a href="../experiments/previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>train_all_variants</code>
<br>
<a href="../modeling/train_models.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="../experiments/attempt_number_training.md">صفحة المستدعي</a>
<br>
<code>run_training</code>
</td>
</tr>
<tr>
<td>
<code>load_category_levels</code>
</td>
<td>
قراءة مستويات الفئات المحفوظة.
</td>
<td>
<pre>load_category_levels(path)</pre>
</td>
<td>
<pre>json.loads(path.read_text(encoding='utf-8'))</pre>
</td>
<td>
<a href="../experiments/course_only_training.md">صفحة المستدعي</a>
<br>
<code>train_experiment</code>
<br>
<a href="../experiments/course_only_training.md">صفحة المستدعي</a>
<br>
<code>load_experiment</code>
<br>
<a href="../experiments/previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>evaluate_holdout</code>
<br>
<a href="../recommendation/artifacts.md">صفحة المستدعي</a>
<br>
<code>load_recommendation_artifacts</code>
<br>
<a href="../evaluation/analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>make_out_of_time_predictions</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
require_current_features
```

يثبت إصدار هندسة الميزات، فلا يمر جدول قديم باسم حديث.

خطوة 2:

```text
learn_category_levels
```

يتعلم الفئات من جدول الملاءمة فقط ويرتبها مع رمزي المفقود وغير المعروف.

خطوة 3:

```text
prepare_model_matrix
```

يتحقق من القائمة ثم يحول الأعداد إلى دقة اثنتين وثلاثين ويستخدم مستويات ثابتة؛ القيمة غير المعروفة لا تعيد تعلم الفئات.

خطوة 4:

```text
save_category_levels / load_category_levels
```

يحفظ ويقرأ تفسير الفئات المشترك مع المودلات.

### العقود والأعمدة المحظورة

النسخة الحالية لهندسة الميزات هي الثانية. جميع ميزات المودل مرتبة وعددها سبعة وأربعون. الأولى تحذف سياق الخطة والأقران فقط؛ لا تحذف تاريخ الطالب أو محاولة المادة.

القيم العددية المفقودة تبقى مفقودة إذا سمح العقد بها، والفئات المفقودة وغير المرصودة تتجه إلى رمزين ثابتين.

```text
__MISSING__
__UNKNOWN__
```

معرف الطالب والاختصاص والمادة ونتيجة الهدف ودرجته ونقاطه لا تدخل مصفوفة المودل بوصفها أهدافًا مقنعة. بعض المعرفات الفئوية المحددة في العقد تدخل لأنها أنواع مصنفة، لا هوية الفرد.

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
require_current_features

metadata.get('feature_engineering_version') != FEATURE_ENGINEERING_VERSION
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
learn_category_levels

CATEGORICAL_FEATURES
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
prepare_model_matrix

len(selected) != len(features)
unknown
NUMERIC_FEATURES
```

## ٦. كيف تتغير البيانات؟

فئة موجودة في الطلب لكنها لم تظهر في التدريب تُحوّل إلى رمز غير معروف؛ لا تضاف إلى قائمة فئات المودل.

## ٧. القواعد والافتراضات

اثنتان وأربعون ميزة عددية وخمس فئوية تعطي سبعًا وأربعين؛ إزالة أربع عشرة ميزة سياق خطة تعطي ثلاثة وثلاثين. المعرفات والنتائج المباشرة ليست ميزات.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

اختلاف ترتيب الأعمدة أو مستويات الفئات قد يغير التوقع دون خطأ شكلي. تعلم الفئات من الاختبار تسرب. قيمة مفقودة ليست فئة جديدة.

أي قيمة أو قطع غير مطابق يجب أن يرفض أو يسجل غير متاح حسب العقد، قبل تحويله إلى توقع. لا تعالج هذه الصفحة نقص المصدر بتغيير ميزة أو وضع قيمة افتراضية.

## ٩. التبعيات

لا توجد استيرادات داخلية من وحدات المشروع في هذا الملف.


تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
pandas
```


مراجع خارج شجرة المصدر تستورد هذه الوحدة؛ ليست دليل تشغيل إنتاج:
[الأداة المرجعية](../../../scripts/experiments/attempt_number_recommendation.py)

```text
scripts/experiments/attempt_number_recommendation.py
```

[الأداة المرجعية](../../../scripts/experiments/attempt_number_removal_recheck.py)

```text
scripts/experiments/attempt_number_removal_recheck.py
```

[الأداة المرجعية](../../../scripts/experiments/student_progress_20261010/evidence/executed_workflow.py)

```text
scripts/experiments/student_progress_20261010/evidence/executed_workflow.py
```

[الأداة المرجعية](../../../scripts/experiments/student_progress_20261010/workflow.py)

```text
scripts/experiments/student_progress_20261010/workflow.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_course_only_recommendation.py)

```text
tests/test_course_only_recommendation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_course_matrix_does_not_need_plan_context_and_retains_unknown_categories
test_scoring_predicts_each_candidate_once_and_clips_before_grade_conversion
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert matrix.shape == (2, 33)
```

[ملف اختبار مرتبط](../../../tests/test_degree_points_config.py)

```text
tests/test_degree_points_config.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_experiment_configuration_preserves_folds_and_variants
test_experiment_modules_import_without_running_experiment
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert BASELINE_VARIANT == 'baseline_mark_temporal'
```

[ملف اختبار مرتبط](../../../tests/test_evaluate_plan_gpa.py)

```text
tests/test_evaluate_plan_gpa.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_predict_course_points_preserves_audit_and_quality_points
test_aggregate_plan_gpa_uses_student_degree_part_and_credit_weighting
test_summarize_plan_errors_includes_threshold_boundaries
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert not {'final_mark', 'points', 'gpa_points'} & set(result)
```

[ملف اختبار مرتبط](../../../tests/test_evaluation_v2_io.py)

```text
tests/test_evaluation_v2_io.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_plan_evaluation_reads_and_writes_v2_with_shared_grade_scale
test_error_analysis_uses_v2_in_historical_holdout_and_shap_paths
test_missing_v2_input_fails_without_v1_fallback_or_output
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert all((versioned[name].is_file() for name in PLAN_OUTPUTS))
```

[ملف اختبار مرتبط](../../../tests/test_experiment_io.py)

```text
tests/test_experiment_io.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_signature_hashes_current_dependencies_deterministically
test_validation_cache_reuses_only_matching_signature
test_metadata_retains_protocol_and_artifact_contract
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert experiment_io.experiment_signature() == expected
```

[ملف اختبار مرتبط](../../../tests/test_experiments_v2_io.py)

```text
tests/test_experiments_v2_io.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_coordinator_uses_v2_baseline_cache_outputs_and_metadata_candidate
test_missing_v2_input_fails_without_using_v1
test_path_constants_are_v2_and_grade_scale_is_shared
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert all((versioned[name].is_file() for name in OUTPUTS))
```

[ملف اختبار مرتبط](../../../tests/test_feature_contract_responsibilities.py)

```text
tests/test_feature_contract_responsibilities.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_saved_training_levels_keep_unseen_serving_values_unknown
test_base_matrix_preserves_schema_and_category_handling
```

[ملف اختبار مرتبط](../../../tests/test_feature_pipeline.py)

```text
tests/test_feature_pipeline.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_feature_version_survives_parquet_projection_and_rejects_old_models
```

## ١١. القيود المعروفة

هذا عقد ميزة وليس توثيقًا لصحة مصدر كل قيمة؛ المسؤولية الزمنية عند المحولات والبناء.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- الترتيب والأنواع جزء من العقد، وليس عدد الأعمدة وحده.
- الفئات تتعلم من الملاءمة ويعاد استخدامها أثناء الخدمة.
- نتائج الهدف والمعرفات الخام لا تصبح ميزات مباشرة.

ثلاثة أسئلة للفهم:

1. كيف ينتج حذف سياق الخطة عقد المرحلة الأولى؟
2. لماذا لا تتعلم مستويات الفئات من الاختبار اللاحق؟
3. ما أثر فئة غير موجودة في مستويات المودل المحفوظ؟

تمرين قراءة آمن:

احسب عدد الميزات الكاملة ثم احذف ميزات سياق الخطة على الورق، وطابق ترتيب الناتج مع عقد الأولى.

التمرين قراءة وحساب على الورق؛ لا يغير المشروع ولا يشغّل بناءً أو توقعًا أو تحديث تاريخ.
