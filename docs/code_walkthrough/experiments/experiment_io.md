# ملفات تجربة الاختصاص ومصدرها

```text
src/experiments/experiment_io.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يحفظ نتائج التجربة ويفصل إعادة الاستخدام عن فقدان المصدر.

الدور في الخريطة:
تجريبي

تصنيف الاستعمال:
تجريبي أو وصفي خارج الخدمة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تنسيق تجربة أهداف النقاط والاختصاص](degree_points.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [إعداد تجربة الاختصاص والنقاط](degree_points_config.md)
- [خوارزميات ملاءمة التجارب وتقييمها](modeling.md)
- [تاريخ الاختصاص التجريبي](specialty_history.md)
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [مرجع المسارات والإصدارات](../paths.md)

## ٣. المدخلات

إعداد تجربة وتواقيع مصادر وجداول مقارنة.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

بصمة تجربة وذاكرة تحقق وبيانات وصفية وملفات نتائج.

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
<code>experiment_signature</code>
</td>
<td>
بصمة المصادر والإعداد لتقييد إعادة الاستخدام.
</td>
<td>
<pre>experiment_signature()</pre>
</td>
<td>
<pre>digest.hexdigest()</pre>
</td>
<td>
<a href="degree_points.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>load_cached_validation</code>
</td>
<td>
قراءة نتائج تحقق فقط عند تطابق البصمة.
</td>
<td>
<pre>load_cached_validation(signature)</pre>
</td>
<td>
<pre>([], set())</pre>
<pre>(previous.to_dict(orient='records'), completed)</pre>
</td>
<td>
<a href="degree_points.md">صفحة المستدعي</a>
<br>
<code>run_validation</code>
</td>
</tr>
<tr>
<td>
<code>build_metadata</code>
</td>
<td>
تسجيل الهدف والميزات والزمن والأصول في مصدر التجربة.
</td>
<td>
<pre>build_metadata(selected, rounds, summary, holdout_metrics, baseline_holdout, signature, *, train_parts=(), test_parts=())</pre>
</td>
<td>
<pre>{'dataset_version': 'V2', 'feature_engineering_version': FEATURE_ENGINEERING_VERSION, 'sources': {'baseline_model_metadata': MODEL_METADATA_PATH_V2.relative_to(PROJECT_ROOT).as_posix(), 'train_features': TEMPORAL_TRAIN_FEATURES_PATH_V2.relative_to(PROJECT_ROOT).as_posix(), 'test_features': TEMPORAL_TEST_FEATURES_PATH_V2.relative_to(PROJECT_ROOT).as_posix(), 'baseline_plan_gpa_metrics': PLAN_GPA_METRICS_PATH_V2.relative_to(PROJECT_ROOT).as_posix(), 'baseline_plan_gpa_evaluation': PLAN_GPA_EVALUATION_PATH_V2.relative_to(PROJECT_ROOT).as_posix(), 'grade_scale': GRADE_SCALE_PATH.relative_to(PROJECT_ROOT).as_posix()}, 'experiment_signature': signature, 'created_at_utc': datetime.now(timezone.utc).isoformat(), 'selection_protocol': 'Select only variants improving Plan GPA MAE in both 2023 and 2024; evaluate the selected variant once on the untouched 2025 holdout.', 'history_protocol': history_protocol, 'selected_variant': selected, 'selected_boost_rounds': rounds, 'variant_catalog': VARIANTS, 'feature_contract': {'profile': selected['feature_profile'], 'numeric_features': numeric_features, 'categorical_features': categorical_features, 'model_features': [*numeric_features, *categorical_features]}, 'validation_summary': summary.to_dict(orient='records'), 'holdout_2025': {'selected': holdout_metrics, 'baseline': baseline_holdout, 'mae_delta': holdout_metrics['plan_gpa_mae'] - baseline_holdout['mae'], 'mae_relative_change': holdout_metrics['plan_gpa_mae'] / baseline_holdout['mae'] - 1}, 'artifacts': {'model': DEGREE_POINTS_SELECTED_MODEL_PATH_V2.relative_to(PROJECT_ROOT).as_posix(), 'category_levels': DEGREE_POINTS_CATEGORY_LEVELS_PATH_V2.relative_to(PROJECT_ROOT).as_posix()}}</pre>
</td>
<td>
<a href="degree_points.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>_json_default</code>
</td>
<td>
تحويل النوع العددي الخاص للتسلسل أو رفض غير المدعوم.
</td>
<td>
<pre>_json_default(value)</pre>
</td>
<td>
<pre>value.item()</pre>
</td>
<td>
لا نداء رمز مباشر محسوم في الفهرس؛ قد يكون واجهة عامة أو نداء كائن أو موضع اختبار.
</td>
</tr>
<tr>
<td>
<code>save_results</code>
</td>
<td>
حفظ جداول ومقاييس ومصدر التجربة.
</td>
<td>
<pre>save_results(validation_results, summary, holdout_predictions, holdout_plans, by_degree, metadata)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="degree_points.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>print_summary</code>
</td>
<td>
عرض نتائج الاختيار والمقارنة.
</td>
<td>
<pre>print_summary(summary, selected, holdout_metrics, baseline_holdout, metadata)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="degree_points.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
experiment_signature
```

يربط إعادة الاستخدام بالبصمة، يجمع الهدف والميزات وبروتوكول التاريخ في المصدر ثم يكتب التقارير والجداول.

## ٦. كيف تتغير البيانات؟

التحول الرئيسي هو من المدخل الموصوف إلى المخرج الموصوف عبر الخطوات أعلاه. لم تتوفر عينة مستقلة موثقة تصلح لعرض قيم أكاديمية كاملة لهذا الملف؛ لذلك لا تُختلق بيانات جامعة أو درجات مودل.

## ٧. القواعد والافتراضات

هذا مسار تحليل أو تجربة صريح خارج طلب الخدمة. تفسير مخرجاته واعتمادها للتشغيل خطوتان منفصلتان.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

التقرير الوصفي أو التقييم المحلي لا يثبت جودة توصية منشورة. ميزات التاريخ يجب أن تستعمل الماضي فقط.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [إعداد تجربة الاختصاص والنقاط](degree_points_config.md)
- [خوارزميات ملاءمة التجارب وتقييمها](modeling.md)
- [تاريخ الاختصاص التجريبي](specialty_history.md)
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [مرجع المسارات والإصدارات](../paths.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_degree_points_config.py)

```text
tests/test_degree_points_config.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_experiment_configuration_preserves_folds_and_variants
test_experiment_modules_import_without_running_experiment
```

[ملف اختبار مرتبط](../../../tests/test_experiment_io.py)

```text
tests/test_experiment_io.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_metadata_retains_protocol_and_artifact_contract
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

[ملف اختبار مرتبط](../../../tests/test_feature_pipeline.py)

```text
tests/test_feature_pipeline.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_validation_cache_rejects_old_or_different_feature_data
```

## ١١. القيود المعروفة

لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يحفظ نتائج التجربة ويفصل إعادة الاستخدام عن فقدان المصدر.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
