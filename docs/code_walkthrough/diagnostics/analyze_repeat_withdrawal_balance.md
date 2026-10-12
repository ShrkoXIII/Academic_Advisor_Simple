# تشغيل تدقيق سياسة التوازن الوصفية

```text
src/diagnostics/analyze_repeat_withdrawal_balance.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يجمع مصادر السجل والتحليل وتقرير نطاق التوازن مع حماية الملفات.

الدور في الخريطة:
تشخيص

تصنيف الاستعمال:
تجريبي أو وصفي خارج الخدمة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

له نقطة تشغيل مباشرة؛ عدم وجود مستورد لا يعني عدم استعماله.

الوحدات التي يعتمد عليها بعد ذلك:

- [أدوات تنظيف الأعمدة والمعرفات](../data/cleaning_utils.md)
- [تحليل تاريخ الإعادة والانسحاب](repeat_withdrawal_balance.md)
- [تقرير التحليل الوصفي للإعادات](repeat_withdrawal_report.md)
- [مرجع المسارات والإصدارات](../paths.md)

## ٣. المدخلات

جداول تسجيل ونتائج ومصادر خام محلية.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

جداول وصفية وتدقيق حساس وتقارير ومقارنة بصمات.

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
<code>sha256</code>
</td>
<td>
حساب بصمة ملف محلي دون تغييره.
</td>
<td>
<pre>sha256(path)</pre>
</td>
<td>
<pre>digest.hexdigest()</pre>
</td>
<td>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>protected_manifest</code>
<br>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>graph_navigation</code>
</td>
</tr>
<tr>
<td>
<code>protected_manifest</code>
</td>
<td>
جرد بصمات الأصول التي يجب حمايتها.
</td>
<td>
<pre>protected_manifest()</pre>
</td>
<td>
<pre>{p.relative_to(PROJECT_ROOT).as_posix(): sha256(p) for p in sorted(files)}</pre>
</td>
<td>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>run</code>
</td>
</tr>
<tr>
<td>
<code>graph_navigation</code>
</td>
<td>
عرض مراجع الخريطة لأجل التنقل البحثي.
</td>
<td>
<pre>graph_navigation(path)</pre>
</td>
<td>
<pre>dict(graph_path=str(path), sha256=sha256(path), nodes=len(nodes), edges=len(links), expanded_tokens=['registration', 'roster', 'student', 'course', 'status', 'previous', 'grade', 'temporal', 'clean', 'paths'], traversal='BFS depth 1 on actual graph seed labels; original graph read-only', scoped_nodes=result, scoped_edges=[edge for edge in links if edge['source'] in visited and edge['target'] in visited], interpretation='Graph sources omit src/ prefix; verify corresponding live files. Graph provides navigation, not current data statistics.')</pre>
</td>
<td>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>run</code>
</td>
</tr>
<tr>
<td>
<code>finish_status_inventory</code>
</td>
<td>
جرد رموز الحالة وتواترها في المصدر.
</td>
<td>
<pre>finish_status_inventory(frame)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>status_evidence</code>
<br>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>run</code>
</td>
</tr>
<tr>
<td>
<code>status_evidence</code>
</td>
<td>
جمع أدلة معنى رموز الحالة وربطها بالنتائج.
</td>
<td>
<pre>status_evidence(roster, raw, grades)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>run</code>
</td>
</tr>
<tr>
<td>
<code>grade_range_disagreements</code>
</td>
<td>
كشف اختلاف معنى الحالة عن نطاق العلامة.
</td>
<td>
<pre>grade_range_disagreements(joined, grades, output)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>run</code>
</td>
</tr>
<tr>
<td>
<code>nonstandard_history_sensitivity</code>
</td>
<td>
قياس أثر إدخال فصول غير اعتيادية على التحليل.
</td>
<td>
<pre>nonstandard_history_sensitivity(cases, target, candidates, output)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>run</code>
</td>
</tr>
<tr>
<td>
<code>run</code>
</td>
<td>
تنسيق خطوات تشغيل التحليل الخاص بهذه الوحدة.
</td>
<td>
<pre>run(output, graph_path)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="analyze_repeat_withdrawal_balance.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>main</code>
</td>
<td>
نقطة التنفيذ المباشر للوحدة؛ ترتيبها وآثارها موضحان أعلاه.
</td>
<td>
<pre>main()</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
مدخل التشغيل المباشر للوحدة.
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
sha256
```

يجرد رموز الحالات، يقارن أدلة الحالة والعلامة ويشغّل تحليل التاريخ الاعتيادي وغير الاعتيادي ثم يكتب تقريرًا؛ لا يستنتج إذن جامعة من النسب.

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
- [تحليل تاريخ الإعادة والانسحاب](repeat_withdrawal_balance.md)
- [تقرير التحليل الوصفي للإعادات](repeat_withdrawal_report.md)
- [مرجع المسارات والإصدارات](../paths.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
argparse
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
test_failed_repeated_and_not_repeated
test_withdrawn_repeated_and_not_repeated
test_latest_previous_attempt_wins
```

## ١١. القيود المعروفة

لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يجمع مصادر السجل والتحليل وتقرير نطاق التوازن مع حماية الملفات.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
