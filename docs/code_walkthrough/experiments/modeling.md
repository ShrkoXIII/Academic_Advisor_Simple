# خوارزميات ملاءمة التجارب وتقييمها

```text
src/experiments/modeling.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يوفر أدوات تجربة الاختصاص دون اعتمادها في تقديم التوصيات.

الدور في الخريطة:
تجريبي

تصنيف الاستعمال:
تجريبي أو وصفي خارج الخدمة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تنسيق تجربة أهداف النقاط والاختصاص](degree_points.md)
- [ملفات تجربة الاختصاص ومصدرها](experiment_io.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [تاريخ الاختصاص التجريبي](specialty_history.md)
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [تدريب الزوج الرسمي واختيار إعداداته](../modeling/train_models.md)
- [الأهداف وأوزان التدريب](../modeling/training_config.md)

## ٣. المدخلات

بيانات ملاءمة وتحقق وصيغة تحدد الميزات والهدف والأوزان.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

مودل ومستويات فئات ومقاييس مواد وخطط ومقارنة صيغ.

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
<code>feature_columns</code>
</td>
<td>
اختيار أعمدة العقد البحثي المحدد.
</td>
<td>
<pre>feature_columns(profile)</pre>
</td>
<td>
<pre>(numeric, categorical)</pre>
</td>
<td>
<a href="experiment_io.md">صفحة المستدعي</a>
<br>
<code>build_metadata</code>
<br>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>fit_experiment_model</code>
<br>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>evaluate_selected_holdout</code>
</td>
</tr>
<tr>
<td>
<code>learn_levels</code>
</td>
<td>
تعلم مستويات الفئات من مجموعة الملاءمة.
</td>
<td>
<pre>learn_levels(frame, categorical_features)</pre>
</td>
<td>
<pre>levels</pre>
</td>
<td>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>fit_experiment_model</code>
</td>
</tr>
<tr>
<td>
<code>prepare_matrix</code>
</td>
<td>
إنشاء مصفوفة البحث العددية والفئوية المرتبة.
</td>
<td>
<pre>prepare_matrix(frame, numeric_features, categorical_features, levels)</pre>
</td>
<td>
<pre>matrix[[*numeric_features, *categorical_features]]</pre>
</td>
<td>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>fit_experiment_model</code>
<br>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>evaluate_selected_holdout</code>
</td>
</tr>
<tr>
<td>
<code>fit_weights</code>
</td>
<td>
دمج وزن الزمن مع وزن الساعات الاختياري.
</td>
<td>
<pre>fit_weights(frame, credit_weighted)</pre>
</td>
<td>
<pre>weight.to_numpy(dtype='float32')</pre>
</td>
<td>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>fit_experiment_model</code>
</td>
</tr>
<tr>
<td>
<code>fit_experiment_model</code>
</td>
<td>
ملاءمة مودل لصيغة وهدف ووزن محددين.
</td>
<td>
<pre>fit_experiment_model(fit, valid, variant, candidate, num_boost_round=MAX_BOOST_ROUNDS)</pre>
</td>
<td>
<pre>(model, levels, valid_matrix)</pre>
</td>
<td>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>evaluate_variant</code>
<br>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>evaluate_selected_holdout</code>
</td>
</tr>
<tr>
<td>
<code>course_predictions</code>
</td>
<td>
تحويل خرج المودل البحثي إلى مقارنة علامات ونقاط.
</td>
<td>
<pre>course_predictions(frame, raw_prediction, target, grade_scale)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>evaluate_variant</code>
<br>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>evaluate_selected_holdout</code>
</td>
</tr>
<tr>
<td>
<code>aggregate_plans</code>
</td>
<td>
تجميع توقعات المواد إلى جودة ومعدل الخطة.
</td>
<td>
<pre>aggregate_plans(predictions)</pre>
</td>
<td>
<pre>plans</pre>
</td>
<td>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>evaluate_variant</code>
<br>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>evaluate_selected_holdout</code>
</td>
</tr>
<tr>
<td>
<code>prediction_metrics</code>
</td>
<td>
حساب مقاييس المادة والخطة في التجربة.
</td>
<td>
<pre>prediction_metrics(frame, predictions, plans, target)</pre>
</td>
<td>
<pre>metrics</pre>
</td>
<td>
<a href="degree_points.md">صفحة المستدعي</a>
<br>
<code>load_or_train_holdout</code>
<br>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>evaluate_variant</code>
<br>
<a href="modeling.md">صفحة المستدعي</a>
<br>
<code>evaluate_selected_holdout</code>
</td>
</tr>
<tr>
<td>
<code>evaluate_variant</code>
</td>
<td>
تقييم صيغة على فترة تحقق زمنية.
</td>
<td>
<pre>evaluate_variant(fit, valid, fold, variant, candidate, grade_scale)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="degree_points.md">صفحة المستدعي</a>
<br>
<code>run_validation</code>
</td>
</tr>
<tr>
<td>
<code>validation_summary</code>
</td>
<td>
مقارنة كل صيغة بالمرجع وتجميع سنوات التحقق.
</td>
<td>
<pre>validation_summary(results, baseline_name, fold_count)</pre>
</td>
<td>
<pre>(compared, summary.sort_values('mean_plan_gpa_mae', ascending=True, kind='stable').reset_index(drop=True))</pre>
</td>
<td>
<a href="degree_points.md">صفحة المستدعي</a>
<br>
<code>run_validation</code>
</td>
</tr>
<tr>
<td>
<code>select_variant</code>
</td>
<td>
اختيار متحسن في جميع سنوات التحقق أو المرجع.
</td>
<td>
<pre>select_variant(summary, variants, baseline_name)</pre>
</td>
<td>
<pre>next((variant for variant in variants if variant['name'] == selected_name))</pre>
</td>
<td>
<a href="degree_points.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>degree_metrics</code>
</td>
<td>
تجميع خطأ الخطة بحسب الاختصاص.
</td>
<td>
<pre>degree_metrics(plans, prefix)</pre>
</td>
<td>
<pre>grouped.rename(columns={column: f'{prefix}_{column}' for column in grouped.columns if column not in {'degree_id', 'degree_name'}})</pre>
</td>
<td>
<a href="degree_points.md">صفحة المستدعي</a>
<br>
<code>compare_holdout_by_degree</code>
</td>
</tr>
<tr>
<td>
<code>evaluate_selected_holdout</code>
</td>
<td>
ملاءمة المختار على كامل التدريب ثم تقييم الاختبار اللاحق.
</td>
<td>
<pre>evaluate_selected_holdout(train, test, variant, rounds, candidate, grade_scale, model_path, category_levels_path)</pre>
</td>
<td>
<pre>(model, predictions, plans, metrics)</pre>
</td>
<td>
<a href="degree_points.md">صفحة المستدعي</a>
<br>
<code>load_or_train_holdout</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
feature_columns
```

يبني المصفوفة الخاصة بالصيغة ويتعلم فئات الملاءمة؛ الوزن الإضافي بالساعات اختياري. يقارن متوسط خطأ معدل الخطة والتحسن في جميع سنوات التحقق ثم يقيّم المختار.

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

- [تاريخ الاختصاص التجريبي](specialty_history.md)
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [تدريب الزوج الرسمي واختيار إعداداته](../modeling/train_models.md)
- [الأهداف وأوزان التدريب](../modeling/training_config.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
gc
numpy
pandas
sklearn
lightgbm
```


مراجع خارج شجرة المصدر تستورد هذه الوحدة؛ ليست دليل تشغيل إنتاج:
[الأداة المرجعية](../../../debugging/explain_recommendation.py)

```text
debugging/explain_recommendation.py
```

[الأداة المرجعية](../../../debugging/pipeline_audit.py)

```text
debugging/pipeline_audit.py
```

[الأداة المرجعية](../../../debugging/pipeline_audit_details.py)

```text
debugging/pipeline_audit_details.py
```

[الأداة المرجعية](../../../debugging/trace_student_29485_20251.py)

```text
debugging/trace_student_29485_20251.py
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
test_credit_weight_multiplies_temporal_weight
```

[ملف اختبار مرتبط](../../../tests/test_model_artifact_isolation.py)

```text
tests/test_model_artifact_isolation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_artifact_namespaces
test_dependency_checker_detects_forbidden_imports_and_paths
test_dependency_checker_allows_official_and_local_imports
```

## ١١. القيود المعروفة

لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يوفر أدوات تجربة الاختصاص دون اعتمادها في تقديم التوصيات.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.

