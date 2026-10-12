# القيود الأكاديمية على الخطط

```text
src/recommendation/constraints.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يفصل صلاحية الخطة عن جودة توقعها وترتيبها. لا يحق لدرجة مرتفعة تجاوز سقف متطلب أو ساعات إعادة.

الدور في الخريطة:
نواة التوصية

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تصدير واجهات نواة التوصية](__init__.md)
- [مكونات التوازن الناعم](balance_policy.md)
- [عقود النواة والمدخلات المحلية](inputs.md)
- [قائمة الخطط المختصرة للمرحلة الأولى](shortlist.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [أدوات تنظيف الأعمدة والمعرفات](../data/cleaning_utils.md)
- [البحث عن مجموعات بالساعات الدقيقة](plan_generation.md)

## ٣. المدخلات

مواد مطبّعة بساعات دقيقة وتصنيف سابق، وقيد هدف ساعات وسقوف أنواع المتطلبات وساعات الإعادة. سقوف المجموعات وحد المواد الجديدة اختياريان.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

الأنواع والبنى المستعملة في هذا الحد:

```text
courses: pandas.DataFrame
constraints: PlanConstraints
credits: Decimal
```

## ٤. المخرجات

فهارس مجموعات مواد تحقق الهدف وجميع القيود. القاموس المعياري للسياسات يصف الساعات المتبقية بعد المكتمل والمحجوز والسماح المعتمد.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

أنواع المخرجات الأساسية:

```text
normalize_requirement_policies(...) -> dict
enumerate_feasible_plan_indices(...) -> iterator[tuple[int, ...]]
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
<code>_credit_value</code>
</td>
<td>
تحقق عدد ساعات دقيق مع الحدود المطلوبة.
</td>
<td>
<pre>_credit_value(value, field, *, positive=False)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="balance_policy.md">صفحة المستدعي</a>
<br>
<code>_course_records</code>
<br>
<a href="balance_policy.md">صفحة المستدعي</a>
<br>
<code>compute_balance_components</code>
<br>
<a href="constraints.md">صفحة المستدعي</a>
<br>
<code>normalize_requirement_policies</code>
<br>
<a href="constraints.md">صفحة المستدعي</a>
<br>
<code>PlanConstraints.__post_init__</code>
<br>
<a href="constraints.md">صفحة المستدعي</a>
<br>
<code>enumerate_feasible_plan_indices</code>
</td>
</tr>
<tr>
<td>
<code>_requirement_id</code>
</td>
<td>
تطبيع هوية متطلب ورفض الفقدان.
</td>
<td>
<pre>_requirement_id(value)</pre>
</td>
<td>
<pre>str(normalized)</pre>
</td>
<td>
<a href="constraints.md">صفحة المستدعي</a>
<br>
<code>normalize_requirement_policies</code>
<br>
<a href="constraints.md">صفحة المستدعي</a>
<br>
<code>PlanConstraints.__post_init__</code>
<br>
<a href="constraints.md">صفحة المستدعي</a>
<br>
<code>enumerate_feasible_plan_indices</code>
</td>
</tr>
<tr>
<td>
<code>normalize_requirement_policies</code>
</td>
<td>
استخراج المتبقي لكل نوع من السقف والمكتمل والمحجوز.
</td>
<td>
<pre>normalize_requirement_policies(records)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_request_payload</code>
</td>
</tr>
<tr>
<td>
<code>PlanConstraints</code>
</td>
<td>
عقد ثابت للساعات والسقوف والإعادات والمواد الجديدة.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_request_payload</code>
</td>
</tr>
<tr>
<td>
<code>enumerate_feasible_plan_indices</code>
</td>
<td>
تصفية العضويات الدقيقة بجميع القيود الأكاديمية.
</td>
<td>
<pre>enumerate_feasible_plan_indices(candidates, constraints, *, search_stats=None)</pre>
</td>
<td>
<pre>(yield plan)</pre>
</td>
<td>
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
_credit_value / _requirement_id
```

يثبت النوع والمدى والهوية حتى لا تدخل أعداد منطقية أو قيم غير محدودة.

خطوة 2:

```text
normalize_requirement_policies
```

يحسِب المتبقي غير السالب من السقف والسماح ناقص المكتمل والمحجوز؛ يعيد بناء سياسة معيارية.

خطوة 3:

```text
PlanConstraints
```

يحفظ الهدف والسياسات، ويتحقق من حد المواد الجديدة وأنواع مجموعات المرشحين.

خطوة 4:

```text
enumerate_feasible_plan_indices
```

يستدعي بحث الساعات الدقيق، ثم يرفض أي خطة تتجاوز النوع أو المجموعة أو سقف الإعادة أو عدد المواد الجديدة.

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
<code>PlanConstraints.__post_init__</code>
</td>
<td>
<pre>__post_init__(self)</pre>
</td>
<td>
يراجع اتساق إعداد الكائن بعد بناء حقوله.
</td>
</tr>
</tbody>
</table>

## ٦. كيف تتغير البيانات؟

عند بقاء أربع ساعات في مجموعة، خطة ثلاث مواد من ساعتين تُرفض مهما كانت علامات المواد المتوقعة.

## ٧. القواعد والافتراضات

الساعات تُجمع بدقة عشرية. قيود المجموعة مستقلة عن تصنيف المودل. الإعادة الراسبة والمنسحبة لهما سقوف منفصلة. التوازن لا يضيف قيد صلاحية.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

تصفية مواد منفردة بسقف المجموعة لا تكشف تجاوز مجموعها. خلط المواد الجديدة بالإعادات يغيّر السقوف.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [أدوات تنظيف الأعمدة والمعرفات](../data/cleaning_utils.md)
- [البحث عن مجموعات بالساعات الدقيقة](plan_generation.md)

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

[الأداة المرجعية](../../../scripts/evaluate_two_stage_ranking.py)

```text
scripts/evaluate_two_stage_ranking.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_api_core_extensions.py)

```text
tests/test_api_core_extensions.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_requirement_groups_do_not_merge_by_model_category
test_max_new_courses_is_an_optional_plan_constraint
```

[ملف اختبار مرتبط](../../../tests/test_two_stage_benchmark.py)

```text
tests/test_two_stage_benchmark.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_feasible_counter_keeps_zero_options_and_filters_complete_plans
test_small_search_matches_independent_subsets
```

[ملف اختبار مرتبط](../../../tests/test_two_stage_constraints.py)

```text
tests/test_two_stage_constraints.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_requirement_alias_and_adjustments_preserve_fractional_remaining
test_requirement_without_adjustments_defaults_to_zero_adjustments
test_overcompleted_requirement_has_zero_remaining
```

[ملف اختبار مرتبط](../../../tests/test_two_stage_shortlist.py)

```text
tests/test_two_stage_shortlist.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_complete_feasibility_before_shortlist_fractional_and_optional_zero
test_no_lower_credit_fallback_and_no_prefiltering_of_failed_availability
test_remaining_policy_arithmetic_preserves_every_supplied_decimal_digit
```

## ١١. القيود المعروفة

الطبقة تطبق سياسة مدخلة؛ لا تجلب الصلاحيات ولا تمنح استثناء جامعيًا بنفسها.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- البحث يطبق الساعات الدقيقة والقيود أثناء اختيار المجموعة.
- كل مادة تستهلك من مجموعتها المستقلة.
- حد المواد الجديدة وقيود الإعادة لا يبدلان تصنيف المودل.

ثلاثة أسئلة للفهم:

1. لماذا ترفض ثلاث مواد من ساعتين مع بقاء أربع ساعات للمجموعة؟
2. كيف يمنع خلط متطلبين لهما المعرف نفسه في اختصاصين؟
3. ما الفرق بين السماح الإداري باستثناء وبين استنتاجه من قيمة الخام؟

تمرين قراءة آمن:

عدد على الورق مجموعات من مواد بساعتين وساعتين وثلاث ساعات مع هدف أربع، ثم طبق قيد المجموعة وحد المواد الجديدة.

التمرين قراءة وحساب على الورق؛ لا يغير المشروع ولا يشغّل بناءً أو توقعًا أو تحديث تاريخ.
