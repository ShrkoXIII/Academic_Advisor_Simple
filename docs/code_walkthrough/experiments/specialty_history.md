# تاريخ الاختصاص التجريبي

```text
src/experiments/specialty_history.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

ينشئ ميزات مجاميع الاختصاص ومتطلبه لأبحاث اختيار الهدف والميزات.

الدور في الخريطة:
تجريبي

تصنيف الاستعمال:
تجريبي أو وصفي خارج الخدمة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تنسيق تجربة أهداف النقاط والاختصاص](degree_points.md)
- [ملفات تجربة الاختصاص ومصدرها](experiment_io.md)
- [خوارزميات ملاءمة التجارب وتقييمها](modeling.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [الأهداف وأوزان التدريب](../modeling/training_config.md)

## ٣. المدخلات

نتائج بعلامات ورسوب ونقاط واختصاص ومتطلب وفصل.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

عشر ميزات تاريخ اختصاص أو حالة مجمدة تجريبية.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

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
<code>_weighted_history_source</code>
</td>
<td>
تحويل النتائج إلى مجاميع مرجحة قابلة للتاريخ البحثي.
</td>
<td>
<pre>_weighted_history_source(frame)</pre>
</td>
<td>
<pre>pd.DataFrame({'part_id': pd.to_numeric(frame['part_id']), 'degree_id': frame['degree_id'], 'plan_requirement_type_id': frame['plan_requirement_type_id'], 'history_count': weight, 'history_mark_sum': weight * pd.to_numeric(frame['final_mark']).astype('float64'), 'history_fail_sum': weight * pd.to_numeric(frame['is_fail']).astype('float64'), 'history_points_sum': weight * pd.to_numeric(frame['points']).astype('float64')}, index=frame.index)</pre>
</td>
<td>
<a href="specialty_history.md">صفحة المستدعي</a>
<br>
<code>add_specialty_history_features</code>
<br>
<a href="specialty_history.md">صفحة المستدعي</a>
<br>
<code>_merge_sequential_test_history</code>
<br>
<a href="specialty_history.md">صفحة المستدعي</a>
<br>
<code>FrozenSpecialtyHistory.from_training</code>
</td>
</tr>
<tr>
<td>
<code>_prior_aggregates</code>
</td>
<td>
حساب مجاميع تسبق كل فصل داخل مجموعة التاريخ.
</td>
<td>
<pre>_prior_aggregates(source, keys, prefix)</pre>
</td>
<td>
<pre>pd.concat([grouped[group_columns].reset_index(drop=True), prior.reset_index(drop=True)], axis=1)</pre>
</td>
<td>
<a href="specialty_history.md">صفحة المستدعي</a>
<br>
<code>_merge_training_history</code>
</td>
</tr>
<tr>
<td>
<code>_total_aggregates</code>
</td>
<td>
تكوين المجاميع الإجمالية عند مستوى معين.
</td>
<td>
<pre>_total_aggregates(source, keys, prefix)</pre>
</td>
<td>
<pre>totals.rename(columns={column: f'{prefix}_{column}' for column in value_columns})</pre>
</td>
<td>
<a href="specialty_history.md">صفحة المستدعي</a>
<br>
<code>_merge_frozen_test_history</code>
<br>
<a href="specialty_history.md">صفحة المستدعي</a>
<br>
<code>FrozenSpecialtyHistory.from_training</code>
</td>
</tr>
<tr>
<td>
<code>_merge_training_history</code>
</td>
<td>
ربط الماضي الصارم بالصفوف مع حفظ ترتيبها.
</td>
<td>
<pre>_merge_training_history(frame, source)</pre>
</td>
<td>
<pre>result.sort_values('_experiment_row_order', kind='stable').drop(columns='_experiment_row_order').reset_index(drop=True)</pre>
</td>
<td>
<a href="specialty_history.md">صفحة المستدعي</a>
<br>
<code>add_specialty_history_features</code>
</td>
</tr>
<tr>
<td>
<code>_merge_frozen_test_history</code>
</td>
<td>
إلحاق مجاميع ثابتة باختبار دون تحديث أثناء التطبيق.
</td>
<td>
<pre>_merge_frozen_test_history(test, source)</pre>
</td>
<td>
<pre>result.merge(_total_aggregates(source, ['degree_id', 'plan_requirement_type_id'], 'degree_requirement'), on=['degree_id', 'plan_requirement_type_id'], how='left', sort=False)</pre>
</td>
<td>
<a href="specialty_history.md">صفحة المستدعي</a>
<br>
<code>_merge_sequential_test_history</code>
</td>
</tr>
<tr>
<td>
<code>_safe_average</code>
</td>
<td>
قسمة آمنة تعيد فقدانًا عند انعدام المقام.
</td>
<td>
<pre>_safe_average(numerator, denominator)</pre>
</td>
<td>
<pre>np.divide(numerator, denominator, out=np.full(len(denominator), np.nan, dtype='float64'), where=denominator &gt; 0)</pre>
</td>
<td>
<a href="specialty_history.md">صفحة المستدعي</a>
<br>
<code>_finish_specialty_history</code>
</td>
</tr>
<tr>
<td>
<code>_finish_specialty_history</code>
</td>
<td>
تنعيم ميزات الاختصاص والمتطلب بالمصدر العام.
</td>
<td>
<pre>_finish_specialty_history(frame)</pre>
</td>
<td>
<pre>result.drop(columns=history_columns)</pre>
</td>
<td>
<a href="specialty_history.md">صفحة المستدعي</a>
<br>
<code>add_specialty_history_features</code>
<br>
<a href="specialty_history.md">صفحة المستدعي</a>
<br>
<code>FrozenSpecialtyHistory.apply</code>
</td>
</tr>
<tr>
<td>
<code>add_specialty_history_features</code>
</td>
<td>
إضافة تاريخ الاختصاص للنسخ البحثية من التدريب والاختبار.
</td>
<td>
<pre>add_specialty_history_features(train, test)</pre>
</td>
<td>
<pre>(enriched_train, enriched_test)</pre>
</td>
<td>
<a href="degree_points.md">صفحة المستدعي</a>
<br>
<code>load_feature_frames</code>
</td>
</tr>
<tr>
<td>
<code>_merge_sequential_test_history</code>
</td>
<td>
تطبيق فصل اختبار ثم إضافة نتائجه قبل الفصل اللاحق.
</td>
<td>
<pre>_merge_sequential_test_history(test, source)</pre>
</td>
<td>
<pre>_merge_frozen_test_history(test, source)</pre>
<pre>pd.concat(enriched_parts, ignore_index=True).sort_values('_experiment_row_order', kind='stable').drop(columns='_experiment_row_order').reset_index(drop=True)</pre>
</td>
<td>
<a href="specialty_history.md">صفحة المستدعي</a>
<br>
<code>add_specialty_history_features</code>
</td>
</tr>
<tr>
<td>
<code>FrozenSpecialtyHistory</code>
</td>
<td>
حالة تاريخ اختصاص اختيارية للتجارب والواجهات القديمة الصريحة.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
لا نداء رمز مباشر محسوم في الفهرس؛ قد يكون واجهة عامة أو نداء كائن أو موضع اختبار.
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
_weighted_history_source
```

يجمع التاريخ المرجح قبل الفصل للتدريب، ويحدّث الاختبار متتابعًا بعد كل فصل؛ ينعّم كل من الاختصاص والمتطلب بالعام بمعامل عشرين.

### طرق الأصناف الموجودة

قائمة الطرق الموجودة، دون افتراض أن ترتيب تعريفها هو ترتيب التنفيذ.

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
<code>FrozenSpecialtyHistory.from_training</code>
</td>
<td>
<pre>from_training(cls, train)</pre>
</td>
<td>
يبني الحالة البحثية من النتائج المتاحة عبر قطع التدريب.
</td>
</tr>
<tr>
<td>
<code>FrozenSpecialtyHistory.apply</code>
</td>
<td>
<pre>apply(self, candidates)</pre>
</td>
<td>
ينتج ميزات للصفوف من الحالة السابقة دون إدخال نتائجها إلى التاريخ.
</td>
</tr>
</tbody>
</table>

## ٦. كيف تتغير البيانات؟

التحول الرئيسي هو من المدخل الموصوف إلى المخرج الموصوف عبر الخطوات أعلاه. لم تتوفر عينة مستقلة موثقة تصلح لعرض قيم أكاديمية كاملة لهذا الملف؛ لذلك لا تُختلق بيانات جامعة أو درجات مودل.

## ٧. القواعد والافتراضات

هذا مسار تحليل أو تجربة صريح خارج طلب الخدمة. تفسير مخرجاته واعتمادها للتشغيل خطوتان منفصلتان.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

تاريخ الاختصاص يحتاج مجموع نقاط حقيقيًا؛ لا تستطيع دفعة التاريخ الأساسي اختراعه. جمع نتائج الهدف قبل التطبيق تسرب.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [الأهداف وأوزان التدريب](../modeling/training_config.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
```


مراجع خارج شجرة المصدر تستورد هذه الوحدة؛ ليست دليل تشغيل إنتاج:
[الأداة المرجعية](../../../scripts/experiments/student_progress_20261010/evidence/executed_workflow.py)

```text
scripts/experiments/student_progress_20261010/evidence/executed_workflow.py
```

[الأداة المرجعية](../../../scripts/experiments/student_progress_20261010/workflow.py)

```text
scripts/experiments/student_progress_20261010/workflow.py
```

[الأداة المرجعية](../../../debugging/explain_recommendation.py)

```text
debugging/explain_recommendation.py
```

[الأداة المرجعية](../../../debugging/render_recommendation_explanation.py)

```text
debugging/render_recommendation_explanation.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_degree_points_experiment.py)

```text
tests/test_degree_points_experiment.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_changing_current_or_future_labels_changes_no_earlier_features
test_frozen_history_rejects_overlap_with_test_semester
test_current_part_does_not_enter_its_own_specialty_history
```

[ملف اختبار مرتبط](../../../tests/test_feature_pipeline.py)

```text
tests/test_feature_pipeline.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_poisoning_current_and_future_outcomes_leaves_all_features_unchanged
```

[ملف اختبار مرتبط](../../../tests/test_frozen_history.py)

```text
tests/test_frozen_history.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_new_version_preserves_original_hashes_and_values
test_target_and_future_outcomes_cannot_enter_prefix
test_prefix_fingerprint_survives_row_order_and_future_dtype_change
```

[ملف اختبار مرتبط](../../../tests/test_specialty_history_sequential.py)

```text
tests/test_specialty_history_sequential.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_20251_excludes_current_and_future_and_20252_includes_finalized_20251
test_generalized_parts_restore_unsorted_rows_with_duplicate_indices
test_new_degree_enters_both_hierarchy_levels_only_in_later_parts
```

## ١١. القيود المعروفة

لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: ينشئ ميزات مجاميع الاختصاص ومتطلبه لأبحاث اختيار الهدف والميزات.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
