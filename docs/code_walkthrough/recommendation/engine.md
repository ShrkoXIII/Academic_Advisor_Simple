# المحرك المحلي ذو الزوج الواحد

```text
src/recommendation/engine.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يحتفظ بمسار التوصية المحلي الرسمي السابق؛ ليس المحرك الذي تختاره واجهة المرحلتين الحالية.

الدور في الخريطة:
نواة التوصية

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [مقارنة تجربة المادة بالمحرك المحلي](../experiments/course_only_evaluation.md)
- [مدخل تنفيذ تجربة المواد](../experiments/course_only_recommendation.md)
- [تصدير واجهات نواة التوصية](__init__.md)
- [قياس المحرك المحلي](benchmark.md)
- [أداة التوصية المحلية](local_cli.md)
- [مقارنة توقعات وخطط الحالة السابقة](../recommendation_experiments/previous_course_status_inference.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](../features/temporal_features.md)
- [تحميل أصول المحرك المحلي الرسمي](artifacts.md)
- [عقود النواة والمدخلات المحلية](inputs.md)
- [البحث عن مجموعات بالساعات الدقيقة](plan_generation.md)

## ٣. المدخلات

لقطة طالب ومواد محلية مطبّعة وساعات وعدد نتائج وقطع تاريخ صريح.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

جميع ملخصات الخطط المرتبة وغلاف نتائج محلية.

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
<code>resolve_current_gpa_credits</code>
</td>
<td>
اختيار مقام معروف بتسجيل مصدره ورفض التخمين.
</td>
<td>
<pre>resolve_current_gpa_credits(snapshot, override=None)</pre>
</td>
<td>
<pre>(value, source)</pre>
</td>
<td>
<a href="../experiments/course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>compare_case</code>
<br>
<a href="../experiments/course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>select_batch_cases</code>
<br>
<a href="../recommendation_experiments/previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
<br>
<a href="engine.md">صفحة المستدعي</a>
<br>
<code>AcademicPlanRecommender.recommend</code>
</td>
</tr>
<tr>
<td>
<code>AcademicPlanRecommender</code>
</td>
<td>
المحرك المحلي السابق بالعقد الكامل والبحث على دفعات.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="../experiments/course_only_recommendation.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="../recommendation_experiments/previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
<br>
<a href="benchmark.md">صفحة المستدعي</a>
<br>
<code>benchmark</code>
<br>
<a href="local_cli.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
resolve_current_gpa_credits
```

يحضّر المواد مع التاريخ، يولّد جميع الخطط الدقيقة على دفعات ويحسب سياق كل خطة ثم توقعاتها، يحتفظ بأفضل النتائج أثناء المرور ويجمع جميع الملخصات في النهاية.

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
<code>AcademicPlanRecommender.__init__</code>
</td>
<td>
<pre>__init__(self, grade_model, fail_model, category_levels, grade_scale, course_history, metadata, provenance=None, num_threads=4)</pre>
</td>
<td>
يحفظ التبعيات أو الحقول ويطبق فحوص البناء الموجودة؛ لا تفترض تحميل أصول ما لم يذكر مسار التهيئة ذلك.
</td>
</tr>
<tr>
<td>
<code>AcademicPlanRecommender.load</code>
</td>
<td>
<pre>load(cls, *, history_as_of_part, num_threads=4, history_root=None)</pre>
</td>
<td>
يحمل النسخة أو الأصول المطلوبة ويتحقق منها؛ التفاصيل تختلف بحسب الصنف وتوضحها الصفحة.
</td>
</tr>
<tr>
<td>
<code>AcademicPlanRecommender.prepare_candidates</code>
</td>
<td>
<pre>prepare_candidates(self, student_snapshot, candidate_courses, part_id, *, allow_older_history=False)</pre>
</td>
<td>
يجهز ميزات الطالب وتاريخ المواد لمسار المحرك المحلي.
</td>
</tr>
<tr>
<td>
<code>AcademicPlanRecommender.score_rows</code>
</td>
<td>
<pre>score_rows(self, rows)</pre>
</td>
<td>
يحسب سياق الخطط المحلية ثم يتوقع بعقد سبع وأربعين ميزة.
</td>
</tr>
<tr>
<td>
<code>AcademicPlanRecommender.recommend</code>
</td>
<td>
<pre>recommend(self, student_snapshot, candidate_courses, part_id, current_gpa, credits=None, min_credits=None, max_credits=None, batch_size=2000, top_n=3, course_sink=None, progress=None, current_gpa_credits=None, allow_older_history=False)</pre>
</td>
<td>
ينفذ التسلسل الموضح في هذه الصفحة ويعيد النتيجة.
</td>
</tr>
</tbody>
</table>

## ٦. كيف تتغير البيانات؟

التحول الرئيسي هو من المدخل الموصوف إلى المخرج الموصوف عبر الخطوات أعلاه. لم تتوفر عينة مستقلة موثقة تصلح لعرض قيم أكاديمية كاملة لهذا الملف؛ لذلك لا تُختلق بيانات جامعة أو درجات مودل.

## ٧. القواعد والافتراضات

يحضّر المواد مع التاريخ، يولّد جميع الخطط الدقيقة على دفعات ويحسب سياق كل خطة ثم توقعاتها، يحتفظ بأفضل النتائج أثناء المرور ويجمع جميع الملخصات في النهاية.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

لا يجب وصف هذا المحرك أنه يختصر بخمسين أو يستعمل ثلاثًا وثلاثين ميزة؛ يستعمل العقد الكامل.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](../features/temporal_features.md)
- [تحميل أصول المحرك المحلي الرسمي](artifacts.md)
- [عقود النواة والمدخلات المحلية](inputs.md)
- [البحث عن مجموعات بالساعات الدقيقة](plan_generation.md)
- [توقع المواد وتلخيص جودة الخطط](plan_scoring.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
```


مراجع خارج شجرة المصدر تستورد هذه الوحدة؛ ليست دليل تشغيل إنتاج:
[الأداة المرجعية](../../../scripts/experiments/attempt_number_recommendation.py)

```text
scripts/experiments/attempt_number_recommendation.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_frozen_history.py)

```text
tests/test_frozen_history.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_same_models_load_two_versions_without_reading_any_training_table
test_selection_is_required_and_missing_version_is_not_rebuilt
```

[ملف اختبار مرتبط](../../../tests/test_local_recommendation.py)

```text
tests/test_local_recommendation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_exhaustive_oracle_fractional_zero_and_variable_count
test_single_value_is_exact_and_range_keeps_both_bounds
test_range_uses_upper_exact_with_decimal_zero_and_variable_count
```

[ملف اختبار مرتبط](../../../tests/test_projected_recommendation.py)

```text
tests/test_projected_recommendation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_invalid_or_unknown_denominators_are_rejected
```

[ملف اختبار مرتبط](../../../tests/test_two_stage_engine.py)

```text
tests/test_two_stage_engine.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_stage_two_context_matrix_predictions_and_summaries_match_legacy_path
test_pinned_official_stage_two_models_match_legacy_on_identical_synthetic_plans
```

## ١١. القيود المعروفة

ترتيبه الأكاديمي المرجعي مختلف عن ترتيب واجهة المرحلتين المعتمد، لكنه ما زال مستخدمًا في الأداة المحلية.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يحتفظ بمسار التوصية المحلي الرسمي السابق؛ ليس المحرك الذي تختاره واجهة المرحلتين الحالية.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: ترتيبه الأكاديمي المرجعي مختلف عن ترتيب واجهة المرحلتين المعتمد، لكنه ما زال مستخدمًا في الأداة المحلية.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.

