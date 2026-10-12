# هندسة الميزات الزمنية المشتركة

```text
src/features/temporal_features.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يحفظ التعريف الواحد لتاريخ المواد والمعدل السابق وسياق الخطة، كي لا تحسب مرحلة التدريب والتوصية ميزات مختلفة بالاسم نفسه.

الدور في الخريطة:
ميزات مشتركة

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تحويل الطالب إلى لقطة بداية الفصل](../api/student_adapter.md)
- [حساب البحث على ميزات المادة فقط](../experiments/course_only_core.md)
- [تجميع ملفات ميزات التدريب](build_temporal_features.md)
- [بناء وتحميل الحزم التاريخية الثابتة](frozen_history.md)
- [المحرك المحلي ذو الزوج الواحد](../recommendation/engine.md)
- [مجاميع الدفعات ومدير اللقطة](../recommendation/history_update.md)
- [عقود النواة والمدخلات المحلية](../recommendation/inputs.md)
- [تحميل أصول المرحلتين والتحقق من مصدرها](../recommendation/two_stage_artifacts.md)
- [المحرك المعتمد ذو المرحلتين](../recommendation/two_stage_engine.md)

## ٣. المدخلات

جداول نتائج نهائية وجداول تسجيل كاملة وحالة طالب. يحتاج التاريخ مفاتيح الاختصاص والمادة والكلية والمتطلب والساعات والفصل والنتيجة والمحاولة.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

أسماء الحقول المعرّفة في الملف:

```text
COURSE_HISTORY_COLUMNS
course_history_avg_mark
course_history_fail_rate
course_history_avg_attempt
course_history_retake_rate
course_history_effective_support
course_history_fallback_level
course_history_missing
```

أسماء الحقول المعرّفة في الملف:

```text
PLAN_CONTEXT_COLUMNS
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
STUDENT_HISTORY_COLUMNS
gpa_prev_1
gpa_prev_2
gpa_trend_delta
gpa_trend_missing
prior_total_reg_courses
prior_total_reg_credits
prior_total_fail_courses
prior_total_fail_credits
prior_fail_credit_ratio
prior_registered_semesters
```

أسماء الحقول المعرّفة في الملف:

```text
HISTORY_SUM_COLUMNS
effective_support
raw_count
mark_sum
fail_sum
attempt_sum
retake_sum
```

الأنواع والبنى المستعملة في هذا الحد:

```text
train / test / roster / student_status: pandas.DataFrame
history: CourseHistoryState
```

## ٤. المخرجات

سبع ميزات تاريخ مادة، وعشر ميزات تاريخ طالب، وأربع عشرة ميزة خطة وأقران، وحالة مجاميع قابلة للحفظ.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

أنواع المخرجات الأساسية:

```text
apply / compute_* -> pandas.DataFrame
build_temporal_course_history -> 4 DataFrames + CourseHistoryState
add_student_history_features -> 2 DataFrames
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
<code>temporal_weight</code>
</td>
<td>
وزن النتيجة وفق السنة مع بقاء التعريف الحالي.
</td>
<td>
<pre>temporal_weight(part_id)</pre>
</td>
<td>
<pre>pd.Series(np.where(year &lt; 2022, 0.25, 1.0), index=part_id.index)</pre>
</td>
<td>
<a href="temporal_features.md">صفحة المستدعي</a>
<br>
<code>CourseHistoryState.update</code>
</td>
</tr>
<tr>
<td>
<code>_joined_key</code>
</td>
<td>
بناء مفتاح نصي مركب بمكونات واضحة.
</td>
<td>
<pre>_joined_key(frame, columns)</pre>
</td>
<td>
<pre>values</pre>
</td>
<td>
<a href="temporal_features.md">صفحة المستدعي</a>
<br>
<code>build_history_keys</code>
</td>
</tr>
<tr>
<td>
<code>build_history_keys</code>
</td>
<td>
تكوين خمسة مستويات تجميع للمواد والسياقات.
</td>
<td>
<pre>build_history_keys(frame)</pre>
</td>
<td>
<pre>{1: _joined_key(key_frame, ['degree_id', 'course_id']), 2: key_frame['course_id'].astype('string').fillna('__MISSING__'), 3: _joined_key(key_frame, ['degree_id', 'plan_requirement_type_id', '_rounded_credits']), 4: _joined_key(key_frame, ['faculty_id', 'plan_requirement_type_id', '_rounded_credits']), 5: _joined_key(key_frame, ['plan_requirement_type_id', '_rounded_credits'])}</pre>
</td>
<td>
<a href="temporal_features.md">صفحة المستدعي</a>
<br>
<code>CourseHistoryState.update</code>
<br>
<a href="temporal_features.md">صفحة المستدعي</a>
<br>
<code>CourseHistoryState.apply</code>
<br>
<a href="../recommendation/history_update.md">صفحة المستدعي</a>
<br>
<code>_apply_normalized_delta</code>
</td>
</tr>
<tr>
<td>
<code>CourseHistoryState</code>
</td>
<td>
مجاميع التاريخ المرجحة وتطبيق ميزاته السبع.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="frozen_history.md">صفحة المستدعي</a>
<br>
<code>build_frozen_history</code>
<br>
<a href="temporal_features.md">صفحة المستدعي</a>
<br>
<code>build_temporal_course_history</code>
<br>
<a href="temporal_features.md">صفحة المستدعي</a>
<br>
<code>load_course_history_state</code>
</td>
</tr>
<tr>
<td>
<code>build_temporal_course_history</code>
</td>
<td>
تاريخ تدريب متقدم زمنيًا واختبار متتابع بنسخة منفصلة.
</td>
<td>
<pre>build_temporal_course_history(temporal_train, temporal_train_roster, temporal_test, temporal_test_roster)</pre>
</td>
<td>
<pre>(train_features, train_roster_features, test_features, test_roster_features, state)</pre>
</td>
<td>
<a href="build_temporal_features.md">صفحة المستدعي</a>
<br>
<code>build_feature_tables</code>
</td>
</tr>
<tr>
<td>
<code>compute_student_gpa_history</code>
</td>
<td>
حساب معدلين سابقين واتجاههما من التسجيل الحقيقي.
</td>
<td>
<pre>compute_student_gpa_history(student_status)</pre>
</td>
<td>
<pre>semester[['student_status_id', 'gpa_prev_1', 'gpa_prev_2', 'gpa_trend_delta', 'gpa_trend_missing']]</pre>
</td>
<td>
<a href="../api/student_adapter.md">صفحة المستدعي</a>
<br>
<code>_history</code>
<br>
<a href="temporal_features.md">صفحة المستدعي</a>
<br>
<code>add_student_history_features</code>
</td>
</tr>
<tr>
<td>
<code>add_student_history_features</code>
</td>
<td>
إضافة العدادات السابقة والنسبة وتاريخ المعدل للأهداف.
</td>
<td>
<pre>add_student_history_features(temporal_train, temporal_test, student_status=None)</pre>
</td>
<td>
<pre>(train, test)</pre>
</td>
<td>
<a href="../api/student_adapter.md">صفحة المستدعي</a>
<br>
<code>_history</code>
<br>
<a href="build_temporal_features.md">صفحة المستدعي</a>
<br>
<code>build_feature_tables</code>
<br>
<a href="../recommendation/inputs.md">صفحة المستدعي</a>
<br>
<code>build_student_snapshot</code>
</td>
</tr>
<tr>
<td>
<code>compute_plan_context_features</code>
</td>
<td>
حساب أربع عشرة ميزة لخطة وأقران باستثناء المادة نفسها.
</td>
<td>
<pre>compute_plan_context_features(roster, group_columns=None)</pre>
</td>
<td>
<pre>result[PLAN_CONTEXT_COLUMNS]</pre>
</td>
<td>
<a href="build_temporal_features.md">صفحة المستدعي</a>
<br>
<code>attach_plan_context</code>
<br>
<a href="../recommendation/two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender._score_stage2</code>
<br>
<a href="../recommendation/engine.md">صفحة المستدعي</a>
<br>
<code>AcademicPlanRecommender.score_rows</code>
</td>
</tr>
<tr>
<td>
<code>save_course_history_state</code>
</td>
<td>
حفظ حالة تاريخ بإصدار وقطع معلومين.
</td>
<td>
<pre>save_course_history_state(state, path)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="build_temporal_features.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="frozen_history.md">صفحة المستدعي</a>
<br>
<code>save_frozen_history</code>
</td>
</tr>
<tr>
<td>
<code>load_course_history_state</code>
</td>
<td>
قراءة حالة محلية موثوقة بإصدار متحقق.
</td>
<td>
<pre>load_course_history_state(path)</pre>
</td>
<td>
<pre>CourseHistoryState(smoothing_k=payload['smoothing_k'], min_support=payload['min_support'], tables=payload['tables'], global_sums=payload['global_sums'], as_of_part=payload['as_of_part'])</pre>
</td>
<td>
<a href="frozen_history.md">صفحة المستدعي</a>
<br>
<code>verify_legacy_course_history</code>
<br>
<a href="frozen_history.md">صفحة المستدعي</a>
<br>
<code>load_frozen_history</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
temporal_weight / build_history_keys
```

يعطي النتائج قبل سنة ألفين واثنتين وعشرين ربع وزن، ويبني خمسة مستويات مفاتيح إضافة إلى المصدر العام.

خطوة 2:

```text
CourseHistoryState.apply / update
```

التطبيق يسبق تحديث نتائج الفصل. التطبيق يبدأ من العام ثم مستويات أعم فالأخص؛ الإحصاء الخاص الموجود يعلو على الأعم.

خطوة 3:

```text
build_temporal_course_history
```

يمشي فصول التدريب بالترتيب، ثم ينسخ الحالة للاختبار المتتابع؛ تحديث الاختبار لا يغير حالة نهاية التدريب المعادة.

خطوة 4:

```text
compute_student_gpa_history
```

يرتب حالة الطالب ويمرر آخر معدل مسجل ثم يزيحه إلى الماضي؛ يفصل عدم التسجيل عن معدل يساوي صفرًا.

خطوة 5:

```text
add_student_history_features
```

يدمج تاريخ الطالب بالأهداف؛ ينقل العدادات الأصلية ويحسب نسبة ساعات الرسوب ويحافظ على فقدان الاتجاه.

خطوة 6:

```text
compute_plan_context_features
```

يحسِب مجاميع الخطة ووسطها ثم يستثني المادة نفسها لميزات الأقران؛ في التوصية التجميع بمعرف الخطة.

### مستويات التاريخ والتنعيم

مستويات المفاتيح من الأخص إلى الأعم:

```text
1: degree_id + course_id
2: course_id
3: degree_id + plan_requirement_type_id + rounded(course_credits)
4: faculty_id + plan_requirement_type_id + rounded(course_credits)
5: plan_requirement_type_id + rounded(course_credits)
6: global
```

التطبيق يبدأ بالعام ثم ينتقل من المستوى الخامس نحو الأول؛ المفتاح الخاص الموجود يستبدل الإحصاء الأعم. قلة الدعم تُسجل في علم الفقدان ولا تحذف تلقائيًا الإحصاء الخاص.

```text
smoothed = (local_sum + 20 * global_prior) / (local_effective_support + 20)
```

حساب ميزات الأقران يستثني مساهمة المادة نفسها من عداد وساعات ومتوسطات الخطة. أعلى خطر بين الأقران يحتاج معالجة أعلى قيمتين عندما تكون المادة الوحيدة صاحبة الأعلى.

للخطة ذات مادة واحدة لا يوجد أقران، فتظل القيم المطلوبة مفقودة بدل صفر مثالي. سياق التدريب يجمع الطالب والاختصاص والفصل؛ سياق الاستدلال ذو المرحلتين يجمع معرف الخطة.

### طرق الأصناف الموجودة

هذه الطرق جزء من السلوك الأساسي؛ الترتيب أعلاه يبين ما يستدعى منها في المسار الفعلي.

<table>
<thead>
<tr>
<th>
الطريقة
</th>
<th>
التوقيع
</th>
<th>
وظيفتها
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>CourseHistoryState.update</code>
</td>
<td>
<pre>update(self, outcomes)</pre>
</td>
<td>
يضيف نتائج نهائية زمنيًا إلى المجاميع المرجحة.
</td>
</tr>
<tr>
<td>
<code>CourseHistoryState.apply</code>
</td>
<td>
<pre>apply(self, frame)</pre>
</td>
<td>
ينتج ميزات للصفوف من الحالة السابقة دون إدخال نتائجها إلى التاريخ.
</td>
</tr>
</tbody>
</table>

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
_joined_key

columns[1:]
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
build_temporal_course_history

sorted(temporal_train['part_id'].unique().tolist())
test_parts
(test_features, test_roster_features)
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
compute_student_gpa_history

not required.issubset(student_status.columns)
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
add_student_history_features

student_status is None
('gpa_prev_1', 'gpa_prev_2', 'gpa_trend_delta', 'gpa_trend_missing')
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
compute_plan_context_features

weighted_specs.items()
label == 'fail_rate'
```

## ٦. كيف تتغير البيانات؟

معدل فصل مسجل ثلاثة، يليه فصل غير مسجل، ثم الهدف: المعدل السابق يظل آخر معدل مسجل، ولا يصنع الملف نتيجة صفرية للفصل الفارغ. خطة بمادة واحدة تعطي فئة أقران مفقودة.

## ٧. القواعد والافتراضات

التنعيم بمعامل عشرين والدعم الأقل من عشرين يرفع إشارة الفقدان. اختيار مستوى خاص موجود لا ينتقل تلقائيًا لمستوى أعم بسبب دعم قليل. لا استعمال لنتيجة الفصل قبل توقعه.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

تحديث التاريخ قبل تطبيقه يسرب نتائج الفصل. استعمال نتائج منظفة فقط للسياق بدل كامل التسجيلات يغيّر حمل الخطة. حذف صفوف عدم التسجيل يغيّر المعدلات والفجوات.

أي قيمة أو قطع غير مطابق يجب أن يرفض أو يسجل غير متاح حسب العقد، قبل تحويله إلى توقع. لا تعالج هذه الصفحة نقص المصدر بتغيير ميزة أو وضع قيمة افتراضية.

## ٩. التبعيات

لا توجد استيرادات داخلية من وحدات المشروع في هذا الملف.


تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
```


مراجع خارج شجرة المصدر تستورد هذه الوحدة؛ ليست دليل تشغيل إنتاج:
[الأداة المرجعية](../../../scripts/benchmark_two_stage.py)

```text
scripts/benchmark_two_stage.py
```

[الأداة المرجعية](../../../scripts/evaluate_corrected_phase6.py)

```text
scripts/evaluate_corrected_phase6.py
```

[الأداة المرجعية](../../../scripts/experiments/attempt_number_recommendation.py)

```text
scripts/experiments/attempt_number_recommendation.py
```

[الأداة المرجعية](../../../scripts/experiments/student_progress_20261010/downstream.py)

```text
scripts/experiments/student_progress_20261010/downstream.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_api_academic_semantics.py)

```text
tests/test_api_academic_semantics.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_official_beginning_total_preserves_training_feature_definition
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert result.normalized['prior_total_reg_credits'] == training.iloc[0]['prior_total_reg_credits']
```

[ملف اختبار مرتبط](../../../tests/test_api_core_extensions.py)

```text
tests/test_api_core_extensions.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_requirement_groups_do_not_merge_by_model_category
test_max_new_courses_is_an_optional_plan_constraint
test_exact_history_selection_and_explicit_backtesting
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert list(enumerate_feasible_plan_indices(candidates, constraints)) == [(0, 1, 3), (0, 2, 3), (1, 2, 3)]
```

[ملف اختبار مرتبط](../../../tests/test_api_integration.py)

```text
tests/test_api_integration.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_original_gpa_calculation_and_helper_are_identical_on_full_schema
```

[ملف اختبار مرتبط](../../../tests/test_cumulative_history.py)

```text
tests/test_cumulative_history.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_lazy_defaults_and_persistent_modes
test_approved_initialization_preserves_full_weighted_history_and_source
test_initialization_requires_exact_approved_cumulative_prefix
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert not root.exists()
```

[ملف اختبار مرتبط](../../../tests/test_feature_pipeline.py)

```text
tests/test_feature_pipeline.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_poisoning_current_and_future_outcomes_leaves_all_features_unchanged
test_feature_version_survives_parquet_projection_and_rejects_old_models
test_validation_cache_rejects_old_or_different_feature_data
```

[ملف اختبار مرتبط](../../../tests/test_frozen_history.py)

```text
tests/test_frozen_history.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_legacy_migration_verifies_values_without_changing_original
```

[ملف اختبار مرتبط](../../../tests/test_history_update.py)

```text
tests/test_history_update.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_aggregate_addition_preserves_weighted_prefix_and_matches_raw_oracle
test_delta_identity_is_canonical_and_state_bytes_are_deterministic
test_invalid_aggregate_is_rejected_without_mutating_prefix
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert updated.global_sums == {'effective_support': 4.25, 'raw_count': 5.0, 'mark_sum': 270.0, 'fail_sum': 1.25, 'attempt_sum': 5.5, 'retake_sum': 1.25}
```

[ملف اختبار مرتبط](../../../tests/test_local_recommendation.py)

```text
tests/test_local_recommendation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_official_matrix_and_course_context_parity
```

## ١١. القيود المعروفة

نسخ إجمالي التسجيل الأصلي إلى ميزة التسجيل السابق يعتمد على توقيت مصدر التدريب؛ هذا يحتاج تأكيدًا جامعيًا. ملفات الحالة التسلسلية تُحمّل من مصدر محلي موثوق فقط.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- تاريخ المادة يستخدم نتائج أسبق وأوزانًا زمنية محددة.
- ميزات الطالب السابقة تستبعد نتائج الهدف.
- سياق الخطة يحسب حملها وأقران كل عضوية.

ثلاثة أسئلة للفهم:

1. متى يستعمل تاريخ أوسع بدل المفتاح الأكثر خصوصية؟
2. لماذا يجب الحفاظ على صفوف الفصول غير المسجلة؟
3. كيف يختلف إجمالي الخطة عن إجمالي أقران مادة داخلها؟

تمرين قراءة آمن:

اكتب على الورق صفين لمادتين في خطة، ثم اطرح مساهمة كل مادة من إجماليها لتحديد ميزات الأقران.

التمرين قراءة وحساب على الورق؛ لا يغير المشروع ولا يشغّل بناءً أو توقعًا أو تحديث تاريخ.
