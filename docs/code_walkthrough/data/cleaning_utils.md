# أدوات تنظيف الأعمدة والمعرفات

```text
src/data/cleaning_utils.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يوحد تفسير المعرفات والقيم الخالية وأسماء الأعمدة لجميع خطوات البيانات.

الدور في الخريطة:
إعداد بيانات

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [إنشاء سجل التسجيل الكامل](build_registration_roster.md)
- [تنظيف كتالوج الاختصاص](clean_degree_course.md)
- [تنظيف نتائج المواد وتكوين المحاولات](clean_student_course.md)
- [تنظيف الدبلوم وربطه بالطالب](clean_student_diploma.md)
- [تنظيف الحالة وتاريخ التسجيل](clean_student_status.md)
- [تشغيل تدقيق سياسة التوازن الوصفية](../diagnostics/analyze_repeat_withdrawal_balance.md)
- [تحليل تاريخ الإعادة والانسحاب](../diagnostics/repeat_withdrawal_balance.md)
- [تقييم توصيات ملفات التصدير](../evaluation/evaluate_xml_recommendations.md)

## ٣. المدخلات

جدول أو سلسلة أو قائمة أسماء أعمدة.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

نسخ منظفة أو سلاسل نصية وعددية قابلة لتمثيل الفقدان.

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
<code>clean_column_names</code>
</td>
<td>
توحيد أسماء الأعمدة والفراغات وحالة الحروف.
</td>
<td>
<pre>clean_column_names(df)</pre>
</td>
<td>
<pre>df</pre>
</td>
<td>
<a href="build_registration_roster.md">صفحة المستدعي</a>
<br>
<code>build_registration_roster</code>
<br>
<a href="clean_degree_course.md">صفحة المستدعي</a>
<br>
<code>clean_degree_course</code>
<br>
<a href="clean_student_course.md">صفحة المستدعي</a>
<br>
<code>clean_student_course</code>
<br>
<a href="clean_student_diploma.md">صفحة المستدعي</a>
<br>
<code>clean_student_diploma</code>
<br>
<a href="clean_student_status.md">صفحة المستدعي</a>
<br>
<code>clean_student_status</code>
</td>
</tr>
<tr>
<td>
<code>clean_id</code>
</td>
<td>
توحيد المعرف النصي ومعاني القيم الخالية.
</td>
<td>
<pre>clean_id(series)</pre>
</td>
<td>
<pre>values</pre>
</td>
<td>
<a href="cleaning_utils.md">صفحة المستدعي</a>
<br>
<code>clean_id_columns</code>
<br>
<a href="cleaning_utils.md">صفحة المستدعي</a>
<br>
<code>extract_university_id</code>
<br>
<a href="../experiments/course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>select_batch_cases</code>
<br>
<a href="../recommendation/balance_policy.md">صفحة المستدعي</a>
<br>
<code>_course_records</code>
<br>
<a href="../evaluation/evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>one_id</code>
</td>
</tr>
<tr>
<td>
<code>clean_id_columns</code>
</td>
<td>
تطبيق تنظيف المعرفات على أعمدة محددة.
</td>
<td>
<pre>clean_id_columns(df, columns)</pre>
</td>
<td>
<pre>df</pre>
</td>
<td>
<a href="build_registration_roster.md">صفحة المستدعي</a>
<br>
<code>build_registration_roster</code>
<br>
<a href="clean_degree_course.md">صفحة المستدعي</a>
<br>
<code>clean_degree_course</code>
<br>
<a href="clean_student_course.md">صفحة المستدعي</a>
<br>
<code>clean_student_course</code>
<br>
<a href="clean_student_diploma.md">صفحة المستدعي</a>
<br>
<code>clean_student_diploma</code>
<br>
<a href="clean_student_status.md">صفحة المستدعي</a>
<br>
<code>clean_student_status</code>
</td>
</tr>
<tr>
<td>
<code>extract_university_id</code>
</td>
<td>
استخراج الجزء الجامعي من المعرف المركب.
</td>
<td>
<pre>extract_university_id(series)</pre>
</td>
<td>
<pre>values.str.extract('\\.([^.]+)$', expand=False).astype('string')</pre>
</td>
<td>
لا نداء رمز مباشر محسوم في الفهرس؛ قد يكون واجهة عامة أو نداء كائن أو موضع اختبار.
</td>
</tr>
<tr>
<td>
<code>to_integer</code>
</td>
<td>
تحويل إلى عدد صحيح قابل للفقدان.
</td>
<td>
<pre>to_integer(series)</pre>
</td>
<td>
<pre>pd.to_numeric(series).astype('Int64')</pre>
</td>
<td>
<a href="build_registration_roster.md">صفحة المستدعي</a>
<br>
<code>build_registration_roster</code>
<br>
<a href="clean_degree_course.md">صفحة المستدعي</a>
<br>
<code>clean_degree_course</code>
<br>
<a href="clean_student_course.md">صفحة المستدعي</a>
<br>
<code>clean_student_course</code>
<br>
<a href="clean_student_status.md">صفحة المستدعي</a>
<br>
<code>clean_student_status</code>
</td>
</tr>
<tr>
<td>
<code>to_float</code>
</td>
<td>
تحويل إلى عدد عشري قابل للفقدان.
</td>
<td>
<pre>to_float(series)</pre>
</td>
<td>
<pre>pd.to_numeric(series).astype('Float64')</pre>
</td>
<td>
<a href="build_registration_roster.md">صفحة المستدعي</a>
<br>
<code>build_registration_roster</code>
<br>
<a href="clean_degree_course.md">صفحة المستدعي</a>
<br>
<code>clean_degree_course</code>
<br>
<a href="clean_student_course.md">صفحة المستدعي</a>
<br>
<code>clean_student_course</code>
<br>
<a href="clean_student_diploma.md">صفحة المستدعي</a>
<br>
<code>clean_student_diploma</code>
<br>
<a href="clean_student_status.md">صفحة المستدعي</a>
<br>
<code>clean_student_status</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
clean_column_names
```

يطبع الأسماء ويزيل الفراغات، يحوّل تمثيل المعرف الصحيح ذي لاحقة كسرية صفرية إلى نصه المعياري؛ التحويل العددي يحتفظ بنوع قابل للفقدان.

## ٦. كيف تتغير البيانات؟

التحول الرئيسي هو من المدخل الموصوف إلى المخرج الموصوف عبر الخطوات أعلاه. لم تتوفر عينة مستقلة موثقة تصلح لعرض قيم أكاديمية كاملة لهذا الملف؛ لذلك لا تُختلق بيانات جامعة أو درجات مودل.

مثال نصي اصطناعي وفق التعبير النظامي الموجود:

```text
" 123.0 " -> "123"
"null" -> pd.NA
```

## ٧. القواعد والافتراضات

يطبع الأسماء ويزيل الفراغات، يحوّل تمثيل المعرف الصحيح ذي لاحقة كسرية صفرية إلى نصه المعياري؛ التحويل العددي يحتفظ بنوع قابل للفقدان.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

المعرف النصي ليس كمية؛ التحويل العددي العشوائي قد يفقد جزءًا مهمًا منه.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

لا توجد استيرادات داخلية من وحدات المشروع في هذا الملف.


تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
pandas
```


مراجع خارج شجرة المصدر تستورد هذه الوحدة؛ ليست دليل تشغيل إنتاج:
[الأداة المرجعية](../../../scripts/evaluate_corrected_phase6.py)

```text
scripts/evaluate_corrected_phase6.py
```

[الأداة المرجعية](../../../scripts/experiments/attempt_number_recommendation.py)

```text
scripts/experiments/attempt_number_recommendation.py
```

[الأداة المرجعية](../../../scripts/scan_student_over_polict.py)

```text
scripts/scan_student_over_polict.py
```

[الأداة المرجعية](../../../scripts/scan_under_12_after_status_change.py)

```text
scripts/scan_under_12_after_status_change.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_clean_utils.py)

```text
tests/test_clean_utils.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_clean_column_names_normalizes_whitespace_without_mutating_input
test_clean_id_preserves_meaningful_dots_and_normalizes_nulls
test_clean_id_columns_cleans_multiple_selected_columns_and_copies_input
```

## ١١. القيود المعروفة

هذه أدوات تنسيق لا تفحص هوية الطلب أو حقوق التسجيل.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يوحد تفسير المعرفات والقيم الخالية وأسماء الأعمدة لجميع خطوات البيانات.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: هذه أدوات تنسيق لا تفحص هوية الطلب أو حقوق التسجيل.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.

