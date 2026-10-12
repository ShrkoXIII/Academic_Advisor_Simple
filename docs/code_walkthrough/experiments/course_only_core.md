# حساب البحث على ميزات المادة فقط

```text
src/experiments/course_only_core.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يختبر فصل توقع المادة عن سياق الخطة باستخدام عقد ثلاثة وثلاثين مدخلًا.

الدور في الخريطة:
تجريبي

تصنيف الاستعمال:
تجريبي أو وصفي خارج الخدمة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [مقارنة تجربة المادة بالمحرك المحلي](course_only_evaluation.md)
- [عرض تجربة المواد المستقلة](course_only_report.md)
- [تدريب تجربة المواد المستقلة](course_only_training.md)
- [تقييم المودلات الموسعة بالحالة السابقة](previous_course_status_evaluation.md)
- [تدريب الحالة السابقة كميزة إضافية](previous_course_status_training.md)
- [مقارنة توقعات وخطط الحالة السابقة](../recommendation_experiments/previous_course_status_inference.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](../features/temporal_features.md)
- [عقود النواة والمدخلات المحلية](../recommendation/inputs.md)
- [البحث عن مجموعات بالساعات الدقيقة](../recommendation/plan_generation.md)
- [توقع المواد وتلخيص جودة الخطط](../recommendation/plan_scoring.md)

## ٣. المدخلات

لقطة ومواد وتاريخ، ثم مودلات بحثية ومستويات فئات وساعات مطلوبة.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

توقع مرة لكل مادة وخطط دقيقة ومقاييس اختلاف مجموعات وحساسية السياق.

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
<code>prepare_course_matrix</code>
</td>
<td>
إنشاء مصفوفة المادة دون ميزات سياق الخطة.
</td>
<td>
<pre>prepare_course_matrix(frame, category_levels)</pre>
</td>
<td>
<pre>prepare_model_matrix(frame, category_levels, model_features=COURSE_ONLY_FEATURES)</pre>
</td>
<td>
<a href="course_only_training.md">صفحة المستدعي</a>
<br>
<code>train_experiment</code>
<br>
<a href="previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>evaluate_holdout</code>
<br>
<a href="previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>prepare_augmented_matrix</code>
<br>
<a href="course_only_core.md">صفحة المستدعي</a>
<br>
<code>score_courses_once</code>
</td>
</tr>
<tr>
<td>
<code>prepare_course_rows</code>
</td>
<td>
إضافة لقطة الطالب والتاريخ إلى المواد البحثية.
</td>
<td>
<pre>prepare_course_rows(snapshot, candidates, part_id, history, *, training_as_of_part)</pre>
</td>
<td>
<pre>rows</pre>
</td>
<td>
<a href="course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>compare_case</code>
<br>
<a href="../recommendation_experiments/previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
</td>
</tr>
<tr>
<td>
<code>score_courses_once</code>
</td>
<td>
توقع كل مادة مرة مع عداد صفوف ووقت.
</td>
<td>
<pre>score_courses_once(rows, grade_model, fail_model, levels, grade_scale, *, num_threads=4)</pre>
</td>
<td>
<pre>(result, {'course_prediction_rows': len(matrix), 'grade_prediction_rows': len(matrix), 'fail_prediction_rows': len(matrix), 'model_prediction_calls': 2, 'prediction_seconds': perf_counter() - started})</pre>
</td>
<td>
<a href="course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>compare_case</code>
<br>
<a href="../recommendation_experiments/previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
</td>
</tr>
<tr>
<td>
<code>optimize_exact_credits</code>
</td>
<td>
بحث مجموعات دقيقة من توقعات ثابتة للمادة.
</td>
<td>
<pre>optimize_exact_credits(scored, target_credits, *, current_gpa, prior_credits, top_k=10)</pre>
</td>
<td>
<pre>(plans, {'candidate_courses': len(rows), 'matching_combinations': count, 'optimizer': 'exhaustive_exact_subset_search', 'retained_combinations': len(best), 'optimizer_seconds': perf_counter() - started})</pre>
</td>
<td>
<a href="course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>compare_case</code>
</td>
</tr>
<tr>
<td>
<code>distribution</code>
</td>
<td>
حساب متوسط وكمّيات توزيع القيم.
</td>
<td>
<pre>distribution(values)</pre>
</td>
<td>
<pre>{name: None for name in ['mean', 'median', 'p90', 'p95', 'max']}</pre>
<pre>{'mean': float(values.mean()), 'median': float(np.median(values)), 'p90': float(np.quantile(values, 0.9)), 'p95': float(np.quantile(values, 0.95)), 'max': float(values.max())}</pre>
</td>
<td>
<a href="course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>run_comparisons</code>
<br>
<a href="course_only_core.md">صفحة المستدعي</a>
<br>
<code>plan_context_sensitivity</code>
</td>
</tr>
<tr>
<td>
<code>plan_context_sensitivity</code>
</td>
<td>
قياس تغير توقع المادة عند اختلاف عضويتها في الخطط.
</td>
<td>
<pre>plan_context_sensitivity(scored)</pre>
</td>
<td>
<pre>(detail, summary)</pre>
</td>
<td>
<a href="course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>compare_case</code>
</td>
</tr>
<tr>
<td>
<code>compare_course_sets</code>
</td>
<td>
مقارنة هوية أفضل مجموعات المواد بين مسارين.
</td>
<td>
<pre>compare_course_sets(official, experimental)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>compare_case</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
prepare_course_matrix
```

يحذف سياق الخطة من المصفوفة، يتوقع كل مادة مرة ثم يبحث جميع العضويات ويجمع قيمها. يقارن حساسية المودل الرسمي لوجود المادة في خطط مختلفة.

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

- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](../features/temporal_features.md)
- [عقود النواة والمدخلات المحلية](../recommendation/inputs.md)
- [البحث عن مجموعات بالساعات الدقيقة](../recommendation/plan_generation.md)
- [توقع المواد وتلخيص جودة الخطط](../recommendation/plan_scoring.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
bisect
numpy
pandas
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_previous_course_status_training.py)

```text
tests/test_previous_course_status_training.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_two_contracts_append_one_categorical_without_changing_base
test_augmented_matrix_keeps_order_and_maps_unseen_status
test_augmented_folds_keep_official_cutoffs_and_fit_weights
```

[ملف اختبار مرتبط](../../../tests/test_two_stage_matrix.py)

```text
tests/test_two_stage_matrix.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_legacy_course_matrix_api_retains_33_feature_coercion_and_missing_validation
```

[اختبار باستيراد ديناميكي](../../../tests/test_course_only_recommendation.py)

```text
tests/test_course_only_recommendation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_course_matrix_does_not_need_plan_context_and_retains_unknown_categories
test_exact_search_uses_every_candidate_and_risk_then_course_order_for_ties
test_fractional_credit_search_and_zero_credit_optional_courses
```

## ١١. القيود المعروفة

لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يختبر فصل توقع المادة عن سياق الخطة باستخدام عقد ثلاثة وثلاثين مدخلًا.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
