# البحث عن مجموعات بالساعات الدقيقة

```text
src/recommendation/plan_generation.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

ينشئ عضويات الخطط دون توقعات أو ترتيب، ويحافظ على الكسور وهوية المواد ذات الساعات الصفرية.

الدور في الخريطة:
نواة التوصية

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تطبيع المواد والأهلية والقيود](../api/courses_adapter.md)
- [تنسيق التحقق والتوصية والإدارة](../api/service.md)
- [تحويل الطالب إلى لقطة بداية الفصل](../api/student_adapter.md)
- [حساب البحث على ميزات المادة فقط](../experiments/course_only_core.md)
- [تصدير واجهات نواة التوصية](__init__.md)
- [القيود الأكاديمية على الخطط](constraints.md)
- [المحرك المحلي ذو الزوج الواحد](engine.md)
- [عقود النواة والمدخلات المحلية](inputs.md)
- [أداة التوصية المحلية](local_cli.md)
- [المحرك المعتمد ذو المرحلتين](two_stage_engine.md)
- [مقارنة توقعات وخطط الحالة السابقة](../recommendation_experiments/previous_course_status_inference.md)

## ٣. المدخلات

جدول مواد وساعات، وهدف أو مجال ساعات. يمكن تمرير إحصاءات للبحث.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

الأنواع والبنى المستعملة في هذا الحد:

```text
candidate_courses: pandas.DataFrame
credits: Decimal-compatible values
```

## ٤. المخرجات

مولّد مجموعات فهارس، أو جدول موسع بعضوية كل خطة. الحد الأعلى للمجال هو الهدف الدقيق الفعلي.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

أنواع المخرجات الأساسية:

```text
enumerate_plan_indices(...) -> iterator[tuple[int, ...]]
build_plan_rows(...) -> pandas.DataFrame
sum_credit_values(...) -> Decimal
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
<code>decimal_credit_units</code>
</td>
<td>
تمثيل الساعات العشرية بوحدات صحيحة موحدة.
</td>
<td>
<pre>decimal_credit_units(value, decimal_places)</pre>
</td>
<td>
<pre>(-coefficient if parts.sign else coefficient) * 10 ** (parts.exponent + decimal_places)</pre>
</td>
<td>
<a href="plan_generation.md">صفحة المستدعي</a>
<br>
<code>sum_credit_values</code>
<br>
<a href="plan_generation.md">صفحة المستدعي</a>
<br>
<code>enumerate_plan_indices</code>
</td>
</tr>
<tr>
<td>
<code>sum_credit_values</code>
</td>
<td>
جمع ساعات دون تقريب سياق الأعداد العشرية.
</td>
<td>
<pre>sum_credit_values(values)</pre>
</td>
<td>
<pre>Decimal((parts.sign, parts.digits, -places))</pre>
</td>
<td>
<a href="../api/courses_adapter.md">صفحة المستدعي</a>
<br>
<code>_course</code>
<br>
<a href="../api/service.md">صفحة المستدعي</a>
<br>
<code>ApiService.recommend</code>
<br>
<a href="../api/student_adapter.md">صفحة المستدعي</a>
<br>
<code>_official_gpa_credits</code>
<br>
<a href="constraints.md">صفحة المستدعي</a>
<br>
<code>normalize_requirement_policies</code>
<br>
<a href="constraints.md">صفحة المستدعي</a>
<br>
<code>enumerate_feasible_plan_indices</code>
</td>
</tr>
<tr>
<td>
<code>resolve_credit_bounds</code>
</td>
<td>
تحقق هدف الساعات أو حدود المجال.
</td>
<td>
<pre>resolve_credit_bounds(credits=None, min_credits=None, max_credits=None)</pre>
</td>
<td>
<pre>(lower, upper)</pre>
</td>
<td>
<a href="engine.md">صفحة المستدعي</a>
<br>
<code>AcademicPlanRecommender.recommend</code>
<br>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_request_payload</code>
<br>
<a href="local_cli.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="plan_generation.md">صفحة المستدعي</a>
<br>
<code>enumerate_plan_indices</code>
</td>
</tr>
<tr>
<td>
<code>enumerate_plan_indices</code>
</td>
<td>
بحث شامل بإضافة واستبعاد مع قص فروع آمن.
</td>
<td>
<pre>enumerate_plan_indices(candidate_courses, target_credits=None, *, min_credits=None, max_credits=None, search_stats=None)</pre>
</td>
<td>
<pre>(yield from visit(0, 0, ()))</pre>
</td>
<td>
<a href="../recommendation_experiments/previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
<br>
<a href="../experiments/course_only_core.md">صفحة المستدعي</a>
<br>
<code>optimize_exact_credits</code>
<br>
<a href="constraints.md">صفحة المستدعي</a>
<br>
<code>enumerate_feasible_plan_indices</code>
<br>
<a href="engine.md">صفحة المستدعي</a>
<br>
<code>AcademicPlanRecommender.recommend</code>
</td>
</tr>
<tr>
<td>
<code>build_plan_rows</code>
</td>
<td>
توسيع عضويات الخطط إلى صفوف مادة وخطة.
</td>
<td>
<pre>build_plan_rows(candidates, plans, first_plan_id=0)</pre>
</td>
<td>
<pre>rows</pre>
</td>
<td>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender.recommend_from_payloads</code>
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
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
decimal_credit_units / sum_credit_values
```

يحوّل الأعداد العشرية إلى وحدات صحيحة بمقياس موحد؛ لا يعتمد جمعًا قد يقربه سياق الحساب.

خطوة 2:

```text
resolve_credit_bounds
```

يثبت الحدود ويستخرج الهدف الأعلى، ولا يهبط لحد أصغر عند غياب حل.

خطوة 3:

```text
enumerate_plan_indices
```

يبحث بإضافة المادة ثم استبعادها، ويقص الفرع عند تجاوز الهدف أو عدم كفاية مجموع الساعات المتبقية.

خطوة 4:

```text
build_plan_rows
```

ينسخ صف المادة لكل عضوية ويضيف معرف الخطة؛ تصبح المادة نفسها صفوفًا متعددة في خطط مختلفة.

### سبب الوحدات الصحيحة والقص

العدد العشري للساعات قد يحتوي دقة أكبر من سياق جمعه. استخراج الإشارة والأرقام والأس ثم مقياس موحد يجعل اختبار المساواة بالهدف دقيقًا.

القص آمن لأن جميع ساعات المواد غير سالبة. فرع مجموعُه تجاوز الهدف لا يمكن أن يعود إليه بإضافة مواد، وفرع لا يكفيه مجموع بقية المواد لا يمكن أن يصل.

المادة الصفرية لا تغير الساعات لكنها تغير عضوية الخطة. لهذا يمكن متابعة فرعي إضافتها واستبعادها حتى بعد بلوغ الهدف.

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
decimal_credit_units

parts.digits
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
resolve_credit_bounds

credits is not None
not lower.is_finite() or not upper.is_finite() or lower < 0 or (upper <= 0) or (lower > upper)
min_credits is not None or max_credits is not None
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
enumerate_plan_indices

any((not v.is_finite() or v < 0 for v in values))
range(len(units) - 1, -1, -1)
search_stats is not None
```

## ٦. كيف تتغير البيانات؟

ساعات المواد ثلاث وثلاث وصفر، والهدف ست: توجد عضويتان؛ الأولى تضم المادتين الموجبتين والثانية تضيف المادة الصفرية.

## ٧. القواعد والافتراضات

المجال من اثنتي عشرة إلى ثماني عشرة يعني هدف ثماني عشرة. المادة صفرية الساعات تحفظ هوية خطة مختلفة، لذلك لا ينتهي البحث بمجرد بلوغ الهدف.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

التقريب العشري قد يضيّع خطة صحيحة. حذف مادة صفرية أو دمج العضويات يغيّر هوية الخطط.

أي قيمة أو قطع غير مطابق يجب أن يرفض أو يسجل غير متاح حسب العقد، قبل تحويله إلى توقع. لا تعالج هذه الصفحة نقص المصدر بتغيير ميزة أو وضع قيمة افتراضية.

## ٩. التبعيات

لا توجد استيرادات داخلية من وحدات المشروع في هذا الملف.


تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
```


مراجع خارج شجرة المصدر تستورد هذه الوحدة؛ ليست دليل تشغيل إنتاج:
[الأداة المرجعية](../../../scripts/benchmark_two_stage.py)

```text
scripts/benchmark_two_stage.py
```

[الأداة المرجعية](../../../scripts/experiments/attempt_number_recommendation.py)

```text
scripts/experiments/attempt_number_recommendation.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

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

[ملف اختبار مرتبط](../../../tests/test_recommendation.py)

```text
tests/test_recommendation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_exact_credits_allow_different_course_counts
```

[ملف اختبار مرتبط](../../../tests/test_two_stage_benchmark.py)

```text
tests/test_two_stage_benchmark.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_search_counter_counts_actual_recursion_and_preserves_order
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert observed == list(enumerate_plan_indices(candidates, 3)) == [(0,), (1,)]
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

أسوأ تعقيد البحث أسي في عدد المرشحين. إحصاء البحث ليس حدًا لإيقافه ولا تحسينًا معتمدًا.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- الحساب العشري يحفظ هدف الساعات بدقة.
- الحد الأعلى الفعلي للمجال يصبح الهدف الدقيق.
- المادة الصفرية قد تغير هوية الخطة دون تغيير مجموع الساعات.

ثلاثة أسئلة للفهم:

1. كيف يتجنب البحث خطأ الكسور الثنائية؟
2. لماذا لا يرجع إلى حمل أقل حين يتعذر الهدف؟
3. ما الذي يختلف بين خطتين ساعاتُهما واحدة وفي إحداهما مادة صفرية؟

تمرين قراءة آمن:

اكتب مجموعات هدف ست ساعات من مواد بثلاث وثلاث وصفر؛ ميز الهوية عن مجموع الساعات.

التمرين قراءة وحساب على الورق؛ لا يغير المشروع ولا يشغّل بناءً أو توقعًا أو تحديث تاريخ.
