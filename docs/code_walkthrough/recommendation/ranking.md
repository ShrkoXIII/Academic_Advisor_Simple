# الهوية والترتيب وجبهات المفاضلة

```text
src/recommendation/ranking.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يفصل معايير اختيار الأولى عن ترتيب النهائي ويحفظ هوية خطة مستقلة عن ترتيب صفوف المواد.

الدور في الخريطة:
نواة التوصية

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [التحقق من اعتماد سياسة الترتيب](ranking_policy.md)
- [قائمة الخطط المختصرة للمرحلة الأولى](shortlist.md)
- [المحرك المعتمد ذو المرحلتين](two_stage_engine.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [أدوات تنظيف الأعمدة والمعرفات](../data/cleaning_utils.md)
- [مكونات التوازن الناعم](balance_policy.md)

## ٣. المدخلات

جدول خطط بمتريّات جودة ورسوب وهوية، ومكونات توازن وأعلام تفعيل، واستراتيجية صريحة مع المرحلة والنسخة.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

أسماء الحقول المعرّفة في الملف:

```text
_ACADEMIC_COLUMNS
expected_quality_points
expected_failed_credits
expected_plan_gpa
projected_cumulative_gpa
```

## ٤. المخرجات

جدول مرتب مع معلومات الاستراتيجية والجبهة عندما تكون مفعلة، وهوية معيارية قائمة على معرفات المواد.

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
<code>PlanIdentity</code>
</td>
<td>
هوية خطة من معرفات موادها المرتبة وبصمتها.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="ranking.md">صفحة المستدعي</a>
<br>
<code>canonical_plan_identity</code>
</td>
</tr>
<tr>
<td>
<code>canonical_plan_identity</code>
</td>
<td>
هوية مستقلة عن ترتيب صفوف مجموعة المواد.
</td>
<td>
<pre>canonical_plan_identity(course_ids)</pre>
</td>
<td>
<pre>PlanIdentity(course_tuple, canonical_json, sha256(canonical_json.encode('utf-8')).hexdigest())</pre>
</td>
<td>
<a href="ranking.md">صفحة المستدعي</a>
<br>
<code>_validated_rows</code>
<br>
<a href="shortlist.md">صفحة المستدعي</a>
<br>
<code>build_stage1_shortlist</code>
</td>
</tr>
<tr>
<td>
<code>RankingStrategy</code>
</td>
<td>
هوية مرحلة واستراتيجية ونسخة منفصلة.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender.from_loaded_artifacts</code>
<br>
<a href="ranking_policy.md">صفحة المستدعي</a>
<br>
<code>validate_ranking_policy</code>
</td>
</tr>
<tr>
<td>
<code>_validated_rows</code>
</td>
<td>
فحص قيم الترتيب وهوية الخطط وأعلام التوازن.
</td>
<td>
<pre>_validated_rows(plans, *, with_balance)</pre>
</td>
<td>
<pre>rows</pre>
</td>
<td>
<a href="ranking.md">صفحة المستدعي</a>
<br>
<code>rank_academic_reference</code>
<br>
<a href="ranking.md">صفحة المستدعي</a>
<br>
<code>rank_evaluation_plans</code>
</td>
</tr>
<tr>
<td>
<code>_academic_key</code>
</td>
<td>
مفتاح ترتيب مرجعي يختلف بحسب المرحلة.
</td>
<td>
<pre>_academic_key(row, stage)</pre>
</td>
<td>
<pre>(-row['expected_quality_points'], row['expected_failed_credits'], row['course_tuple'])</pre>
<pre>(-row['projected_cumulative_gpa'], row['expected_failed_credits'], -row['expected_plan_gpa'], row['plan_id'])</pre>
</td>
<td>
<a href="ranking.md">صفحة المستدعي</a>
<br>
<code>rank_academic_reference</code>
<br>
<a href="ranking.md">صفحة المستدعي</a>
<br>
<code>rank_evaluation_plans</code>
</td>
</tr>
<tr>
<td>
<code>rank_academic_reference</code>
</td>
<td>
ترتيب مرجعي ثابت بلا اختيار سياسة بحثية.
</td>
<td>
<pre>rank_academic_reference(plans, *, stage)</pre>
</td>
<td>
<pre>plans.iloc[order].reset_index(drop=True).copy()</pre>
</td>
<td>
لا نداء رمز مباشر محسوم في الفهرس؛ قد يكون واجهة عامة أو نداء كائن أو موضع اختبار.
</td>
</tr>
<tr>
<td>
<code>_pareto_levels</code>
</td>
<td>
استخراج جبهات الهيمنة عبر مقارنات زوجية.
</td>
<td>
<pre>_pareto_levels(rows, active_components)</pre>
</td>
<td>
<pre>levels</pre>
</td>
<td>
<a href="ranking.md">صفحة المستدعي</a>
<br>
<code>rank_evaluation_plans</code>
</td>
</tr>
<tr>
<td>
<code>rank_evaluation_plans</code>
</td>
<td>
تطبيق الاستراتيجية الصريحة مع نطاق التوازن وكسر التعادل.
</td>
<td>
<pre>rank_evaluation_plans(plans, *, strategy)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender.recommend_from_payloads</code>
<br>
<a href="shortlist.md">صفحة المستدعي</a>
<br>
<code>build_stage1_shortlist</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
canonical_plan_identity
```

يرتب معرفات المواد ويبصمها؛ المادة صفرية الساعات جزء من الهوية.

خطوة 2:

```text
_validated_rows / _academic_key
```

يفحص القيم والهوية ومكونات التوازن ثم يحسب ترتيبًا أكاديميًا مرجعيًا ثابتًا.

خطوة 3:

```text
_pareto_levels
```

يقارن كل خطة بغيرها لاستخراج غير المهيمَن عليها، ثم يعيد العملية لبقية الجبهات.

خطوة 4:

```text
rank_evaluation_plans
```

يطبق استراتيجية المرحلة المطلوبة داخل نطاق التوازن ويحافظ على مواضع المرجع خارجه؛ كسر التعادل ثابت.

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
<code>RankingStrategy.__post_init__</code>
</td>
<td>
<pre>__post_init__(self)</pre>
</td>
<td>
يراجع اتساق إعداد الكائن بعد بناء حقوله.
</td>
</tr>
<tr>
<td>
<code>RankingStrategy.metadata</code>
</td>
<td>
<pre>metadata(self)</pre>
</td>
<td>
يعيد نسخة منفصلة من بيانات المصدر.
</td>
</tr>
</tbody>
</table>

## ٦. كيف تتغير البيانات؟

خطة أفضل معدلًا لكنها أعلى رسوبًا قد تشارك خطة أخرى الجبهة الأولى؛ المفاضلة ليست جمعًا تلقائيًا لكل الأبعاد في درجة واحدة.

## ٧. القواعد والافتراضات

قلة الرسوب وعلو التراكمي وانخفاض عقوبات التوازن أبعاد مستقلة عند تفعيلها. العقوبة المعطلة مفقودة وليست صفرًا مثاليًا. الاسم التاريخي لوظيفة التقييم لا يمنع استعمالها داخل المحرك المعتمد.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

إدخال عقوبة معطلة كصفر يمنح أفضلية زائفة. تغيير معرف خطة عند ترتيب المواد يهدم المطابقة بين المرحلتين.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [أدوات تنظيف الأعمدة والمعرفات](../data/cleaning_utils.md)
- [مكونات التوازن الناعم](balance_policy.md)

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

[الأداة المرجعية](../../../scripts/evaluate_two_stage_ranking.py)

```text
scripts/evaluate_two_stage_ranking.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_corrected_phase6_evaluation.py)

```text
tests/test_corrected_phase6_evaluation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_fixed_pool_rejects_nonfinite_metrics
```

[ملف اختبار مرتبط](../../../tests/test_ranking_strategies.py)

```text
tests/test_ranking_strategies.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_identity_is_canonical_sha256_and_includes_optional_zero_course
test_invalid_plan_identity_is_rejected
test_balance_changes_rank_despite_different_gpa_and_failures
```

[ملف اختبار مرتبط](../../../tests/test_two_stage_activation.py)

```text
tests/test_two_stage_activation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_production_does_not_allow_replacing_an_approved_strategy
test_wrong_stage_or_missing_strategy_fails_before_any_inference
test_one_request_pins_both_approved_choices_despite_mid_request_replacement
```

[ملف اختبار مرتبط](../../../tests/test_two_stage_engine.py)

```text
tests/test_two_stage_engine.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_evaluation_factory_loads_assets_and_history_once_for_reused_requests
test_evaluation_needs_two_explicit_stage_choices
```

## ١١. القيود المعروفة

المقارنة زوجية وقد تكون مكلفة. الترتيب لا يغيّر صلاحية الخطة ولا يضمن تحسنًا واقعيًا للطالب.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يفصل معايير اختيار الأولى عن ترتيب النهائي ويحفظ هوية خطة مستقلة عن ترتيب صفوف المواد.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: المقارنة زوجية وقد تكون مكلفة. الترتيب لا يغيّر صلاحية الخطة ولا يضمن تحسنًا واقعيًا للطالب.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
