# تقرير التحليل الوصفي للإعادات

```text
src/diagnostics/repeat_withdrawal_report.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يعرض المجموعات والقيم المتطرفة والبدائل المقترحة دون منحها صلاحية تسجيل.

الدور في الخريطة:
تشخيص

تصنيف الاستعمال:
تجريبي أو وصفي خارج الخدمة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تشغيل تدقيق سياسة التوازن الوصفية](analyze_repeat_withdrawal_balance.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [تحليل تاريخ الإعادة والانسحاب](repeat_withdrawal_balance.md)

## ٣. المدخلات

نتائج تحليل تسجيل ودلالات حالات.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

ملفات تقرير وجداول مجمعة ونص ملخص.

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
<code>write_json</code>
</td>
<td>
حفظ قاموس قابل للتسلسل في ملف نتائج.
</td>
<td>
<pre>write_json(path, value)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>nonstandard_history_sensitivity</code>
<br>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>run</code>
<br>
<a href="repeat_withdrawal_report.md">صفحة المستدعي</a>
<br>
<code>aggregate_outputs</code>
</td>
</tr>
<tr>
<td>
<code>markdown_table</code>
</td>
<td>
عرض جدول التقرير نصيًا مع حماية الفواصل.
</td>
<td>
<pre>markdown_table(frame)</pre>
</td>
<td>
<pre>'\n'.join(lines)</pre>
</td>
<td>
<a href="repeat_withdrawal_report.md">صفحة المستدعي</a>
<br>
<code>render_summary</code>
</td>
</tr>
<tr>
<td>
<code>cohorts</code>
</td>
<td>
تكوين مجموعات التحليل بحسب الحمل والفصل.
</td>
<td>
<pre>cohorts(cases)</pre>
</td>
<td>
<pre>{'all': cases, 'failed_available': cases[failed], 'withdrawn_available': cases[withdrawn], 'both_available': cases[failed &amp; withdrawn], 'any_available': cases[failed | withdrawn], 'failed_available_and_repeated': cases[failed &amp; cases.registered_failed_retake_courses.gt(0)], 'withdrawn_available_and_repeated': cases[withdrawn &amp; cases.registered_withdrawn_retake_courses.gt(0)], 'policy_reference_any': cases[reference &amp; (failed | withdrawn)], 'policy_reference_failed': cases[reference &amp; failed], 'policy_reference_withdrawn': cases[reference &amp; withdrawn], 'policy_reference_both': cases[reference &amp; failed &amp; withdrawn]}</pre>
</td>
<td>
<a href="repeat_withdrawal_report.md">صفحة المستدعي</a>
<br>
<code>policy_candidates</code>
<br>
<a href="repeat_withdrawal_report.md">صفحة المستدعي</a>
<br>
<code>aggregate_outputs</code>
</td>
</tr>
<tr>
<td>
<code>policy_candidates</code>
</td>
<td>
تجميع بدائل السياسة الوصفية للمقارنة.
</td>
<td>
<pre>policy_candidates(cases)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>nonstandard_history_sensitivity</code>
<br>
<a href="repeat_withdrawal_report.md">صفحة المستدعي</a>
<br>
<code>aggregate_outputs</code>
</td>
</tr>
<tr>
<td>
<code>aggregate_outputs</code>
</td>
<td>
حفظ ملخصات التحليل وجداوله المجمعة.
</td>
<td>
<pre>aggregate_outputs(cases, students, output)</pre>
</td>
<td>
<pre>(distributions, mixes, common, probability_frame, policies)</pre>
</td>
<td>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>run</code>
</td>
</tr>
<tr>
<td>
<code>outlier_outputs</code>
</td>
<td>
حفظ وصف الحالات المتطرفة في التحليل.
</td>
<td>
<pre>outlier_outputs(cases, audit, output)</pre>
</td>
<td>
<pre>pd.DataFrame(summaries)</pre>
</td>
<td>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>run</code>
</td>
</tr>
<tr>
<td>
<code>render_summary</code>
</td>
<td>
تكوين النص الملخص لدليل النتائج وحدوده.
</td>
<td>
<pre>render_summary(output, cases, status_mapping, distributions, mixes, common, probabilities, policies, metadata, issues)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>run</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
write_json
```

يفصل مجموعات الحمل والفصل، يقارن النسب ويعرض بدائل سياسة على أنها نتائج وصفية؛ لا يحمّل مودلًا أو يغير التوصية.

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

- [تحليل تاريخ الإعادة والانسحاب](repeat_withdrawal_balance.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_repeat_withdrawal_balance.py)

```text
tests/test_repeat_withdrawal_balance.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_policy_components_use_separate_backlog_denominators
test_small_policy_reference_reports_insufficient_evidence
```

## ١١. القيود المعروفة

لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يعرض المجموعات والقيم المتطرفة والبدائل المقترحة دون منحها صلاحية تسجيل.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
