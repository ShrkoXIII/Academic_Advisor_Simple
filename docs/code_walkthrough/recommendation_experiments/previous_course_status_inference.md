# مقارنة توقعات وخطط الحالة السابقة

```text
src/recommendation_experiments/previous_course_status_inference.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يقارن العقود الأساسية والموسعة مع عضويات متطابقة حتى لا يختلط أثر الميزة بأثر مجموعة المواد.

الدور في الخريطة:
تجريبي

تصنيف الاستعمال:
تجريبي أو وصفي خارج الخدمة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تنسيق تجربة توصيات الحالة السابقة](previous_course_status_experiment.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [حساب البحث على ميزات المادة فقط](../experiments/course_only_core.md)
- [تدريب تجربة المواد المستقلة](../experiments/course_only_training.md)
- [تدريب الحالة السابقة كميزة إضافية](../experiments/previous_course_status_training.md)
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [تصنيف أحدث محاولة سابقة](../features/student_course_status.md)
- [مرجع المسارات والإصدارات](../paths.md)

## ٣. المدخلات

مودلات وتجربة حالة وسجل سابق وطلب محلي.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

فروق توقعات مواد وخطط وتغيرات ترتيب ومخرجات تجربة.

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
<code>prepare_augmented_matrix</code>
</td>
<td>
إلحاق الحالة السابقة بالمصفوفة الأساسية المرتبة.
</td>
<td>
<pre>prepare_augmented_matrix(frame, levels, base_features)</pre>
</td>
<td>
<pre>prepare(frame, levels, base_features)</pre>
</td>
<td>
<a href="previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>score_augmented_rows</code>
</td>
</tr>
<tr>
<td>
<code>score_augmented_rows</code>
</td>
<td>
توقع صفوف بحثية بعقد موسع والتحقق من خرجها.
</td>
<td>
<pre>score_augmented_rows(rows, grade_model, fail_model, levels, grade_scale, base_features)</pre>
</td>
<td>
<pre>scored</pre>
</td>
<td>
<a href="previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
</td>
</tr>
<tr>
<td>
<code>_pair_scored_rows</code>
</td>
<td>
ربط توقعين واحدًا إلى واحد والتحقق من نفس العضويات.
</td>
<td>
<pre>_pair_scored_rows(baseline, augmented, key, baseline_number, augmented_number)</pre>
</td>
<td>
<pre>paired</pre>
</td>
<td>
<a href="previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>pair_course_scores</code>
<br>
<a href="previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>pair_plan_course_scores</code>
</td>
</tr>
<tr>
<td>
<code>pair_course_scores</code>
</td>
<td>
مقارنة ثلاثة وثلاثين وأربعة وثلاثين مدخلًا لكل مادة.
</td>
<td>
<pre>pair_course_scores(baseline, augmented)</pre>
</td>
<td>
<pre>_pair_scored_rows(baseline, augmented, ['course_id'], 33, 34)</pre>
</td>
<td>
<a href="previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
</td>
</tr>
<tr>
<td>
<code>pair_plan_course_scores</code>
</td>
<td>
مقارنة سبعة وأربعين وثمانية وأربعين مدخلًا للعضوية.
</td>
<td>
<pre>pair_plan_course_scores(baseline, augmented)</pre>
</td>
<td>
<pre>_pair_scored_rows(baseline, augmented, ['plan_id', 'course_id'], 47, 48)</pre>
</td>
<td>
<a href="previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
</td>
</tr>
<tr>
<td>
<code>pair_plan_summaries</code>
</td>
<td>
ربط ملخصات الخطط ومقارنة ترتيبها على نفس المواد.
</td>
<td>
<pre>pair_plan_summaries(baseline, augmented, membership)</pre>
</td>
<td>
<pre>(paired, summary)</pre>
</td>
<td>
<a href="previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
</td>
</tr>
<tr>
<td>
<code>_attach_status</code>
</td>
<td>
إضافة حالة سابقة موثقة إلى صفوف البحث.
</td>
<td>
<pre>_attach_status(rows, status_history)</pre>
</td>
<td>
<pre>with_status</pre>
</td>
<td>
<a href="previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
</td>
</tr>
<tr>
<td>
<code>_load_experimental_models</code>
</td>
<td>
تحميل مودلات الحالة السابقة الموسعة بعقدها الصحيح.
</td>
<td>
<pre>_load_experimental_models(model_dir, variant, base_features)</pre>
</td>
<td>
<pre>(grade, fail, levels, metadata)</pre>
</td>
<td>
<a href="previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
</td>
</tr>
<tr>
<td>
<code>run_student_comparison</code>
</td>
<td>
تنسيق مقارنة المادة والخطط داخل التجربة فقط.
</td>
<td>
<pre>run_student_comparison(*, status_history, model_dir, debug_dir)</pre>
</td>
<td>
<pre>summary</pre>
</td>
<td>
<a href="previous_course_status_experiment.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
prepare_augmented_matrix
```

يربط الصفوف بمادة أو بخطة ومادة ربطًا واحدًا إلى واحد، يتحقق من تطابق العضوية والساعات والحالة ثم يقارن أربعة وثلاثين بثلاثة وثلاثين وثمانية وأربعين بسبعة وأربعين.

## ٦. كيف تتغير البيانات؟

التحول الرئيسي هو من المدخل الموصوف إلى المخرج الموصوف عبر الخطوات أعلاه. لم تتوفر عينة مستقلة موثقة تصلح لعرض قيم أكاديمية كاملة لهذا الملف؛ لذلك لا تُختلق بيانات جامعة أو درجات مودل.

## ٧. القواعد والافتراضات

هذا مسار تحليل أو تجربة صريح خارج طلب الخدمة. تفسير مخرجاته واعتمادها للتشغيل خطوتان منفصلتان.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

الحالة السابقة يجب أن تخص فصلًا أصغر من الهدف؛ علامة مفقودة ليست انسحابًا. العقود الموسعة ليست العقود الرسمية.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [حساب البحث على ميزات المادة فقط](../experiments/course_only_core.md)
- [تدريب تجربة المواد المستقلة](../experiments/course_only_training.md)
- [تدريب الحالة السابقة كميزة إضافية](../experiments/previous_course_status_training.md)
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [تصنيف أحدث محاولة سابقة](../features/student_course_status.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [المحرك المحلي ذو الزوج الواحد](../recommendation/engine.md)
- [عقود النواة والمدخلات المحلية](../recommendation/inputs.md)
- [البحث عن مجموعات بالساعات الدقيقة](../recommendation/plan_generation.md)
- [توقع المواد وتلخيص جودة الخطط](../recommendation/plan_scoring.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[اختبار باستيراد ديناميكي](../../../tests/test_previous_course_status_inference.py)

```text
tests/test_previous_course_status_inference.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_course_comparison_joins_by_course_identity_and_keeps_status
test_course_comparison_rejects_mismatched_candidate_rows
test_unresolved_prior_attempt_is_unknown_in_serving_rows
```

## ١١. القيود المعروفة

لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يقارن العقود الأساسية والموسعة مع عضويات متطابقة حتى لا يختلط أثر الميزة بأثر مجموعة المواد.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.

