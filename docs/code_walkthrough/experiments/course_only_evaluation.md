# مقارنة تجربة المادة بالمحرك المحلي

```text
src/experiments/course_only_evaluation.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يقارن مجموعات الخطط والوقت وعدد صفوف التوقع في مسارين منفصلين.

الدور في الخريطة:
تجريبي

تصنيف الاستعمال:
تجريبي أو وصفي خارج الخدمة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [مدخل تنفيذ تجربة المواد](course_only_recommendation.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [أدوات تنظيف الأعمدة والمعرفات](../data/cleaning_utils.md)
- [حساب البحث على ميزات المادة فقط](course_only_core.md)
- [تدريب تجربة المواد المستقلة](course_only_training.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [المحرك المحلي ذو الزوج الواحد](../recommendation/engine.md)

## ٣. المدخلات

محرك محلي رسمي ومودلات التجربة وحالات محلية.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

تفاصيل المقارنة وتوقعات محفوظة وسجل حماية الأصول.

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
<code>PredictionCounter</code>
</td>
<td>
غلاف مودل يسجل عدد استدعاءات وصفوف التوقع.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>run_comparisons</code>
</td>
</tr>
<tr>
<td>
<code>official_plan_lookup</code>
</td>
<td>
ربط مجموعة المواد المعيارية بمعرف خطتها الرسمية.
</td>
<td>
<pre>official_plan_lookup(scored)</pre>
</td>
<td>
<pre>{tuple(sorted((str(value) for value in group.course_id))): int(plan_id) for plan_id, group in scored.groupby('plan_id', sort=False)}</pre>
</td>
<td>
<a href="course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>compare_case</code>
</td>
</tr>
<tr>
<td>
<code>compare_case</code>
</td>
<td>
مقارنة حالة واحدة بين الرسمي وتجربة المادة.
</td>
<td>
<pre>compare_case(engine, experiment_models, candidates, snapshot, *, repeats=3)</pre>
</td>
<td>
<pre>(comparison, scores, official, plans, all_plans, official_scores, sensitivity, sensitivity_summary)</pre>
</td>
<td>
<a href="course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>run_comparisons</code>
</td>
</tr>
<tr>
<td>
<code>save_case</code>
</td>
<td>
حفظ تفاصيل وخطط وتوقعات حالة مقارنة.
</td>
<td>
<pre>save_case(output, candidates, snapshot, imported, measured)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>run_comparisons</code>
</td>
</tr>
<tr>
<td>
<code>select_batch_cases</code>
</td>
<td>
اختيار حالات محلية موثقة لقياس متكرر.
</td>
<td>
<pre>select_batch_cases(*, limit=12)</pre>
</td>
<td>
<pre>cases[:limit]</pre>
</td>
<td>
<a href="course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>run_comparisons</code>
</td>
</tr>
<tr>
<td>
<code>run_comparisons</code>
</td>
<td>
تنسيق المقارنة والقياس والحفظ لحالات التجربة.
</td>
<td>
<pre>run_comparisons(engine, experiment_models, *, repeats=3)</pre>
</td>
<td>
<pre>(measured[0], aggregate)</pre>
</td>
<td>
<a href="course_only_recommendation.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>capture_protected_files</code>
</td>
<td>
التقاط بصمات أصول الحماية قبل التجربة.
</td>
<td>
<pre>capture_protected_files(*, protected_paths=None)</pre>
</td>
<td>
<pre>verify_protected_files()</pre>
</td>
<td>
<a href="course_only_recommendation.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>verify_protected_files</code>
</td>
<td>
رفض أي تغير محمي وإصدار نتيجة تدقيق.
</td>
<td>
<pre>verify_protected_files()</pre>
</td>
<td>
<pre>verification</pre>
</td>
<td>
<a href="course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>capture_protected_files</code>
<br>
<a href="course_only_recommendation.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
PredictionCounter.__init__
```

يلف المودلات بعدّاد استدعاء وصفوف، يقيس الحالتين على المرشحين أنفسهم ثم يحفظ العضويات والتداخل وحساسية السياق؛ يفحص بصمات الأصول.

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
<code>PredictionCounter.__init__</code>
</td>
<td>
<pre>__init__(self, model)</pre>
</td>
<td>
يحفظ التبعيات أو الحقول ويطبق فحوص البناء الموجودة؛ لا تفترض تحميل أصول ما لم يذكر مسار التهيئة ذلك.
</td>
</tr>
<tr>
<td>
<code>PredictionCounter.predict</code>
</td>
<td>
<pre>predict(self, matrix, **kwargs)</pre>
</td>
<td>
يزيد عداد الاستدعاءات والصفوف ثم يفوض التوقع إلى المودل الأصلي.
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

التقرير الوصفي أو التقييم المحلي لا يثبت جودة توصية منشورة. ميزات التاريخ يجب أن تستعمل الماضي فقط.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [أدوات تنظيف الأعمدة والمعرفات](../data/cleaning_utils.md)
- [حساب البحث على ميزات المادة فقط](course_only_core.md)
- [تدريب تجربة المواد المستقلة](course_only_training.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [المحرك المحلي ذو الزوج الواحد](../recommendation/engine.md)
- [عقود النواة والمدخلات المحلية](../recommendation/inputs.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

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

- مسؤولية الملف: يقارن مجموعات الخطط والوقت وعدد صفوف التوقع في مسارين منفصلين.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
