# أدوات تجربة رقم المحاولة

```text
src/experiments/attempt_number_core.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يدعم ثلاث صيغ بحثية لرقم المحاولة: كما هو، أو علم إعادة، أو حذفه. يحفظ هوية الصفوف وحماية الأصول.

الدور في الخريطة:
تجريبي

تصنيف الاستعمال:
تجريبي أو وصفي خارج الخدمة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تحليل أثر رقم المحاولة](attempt_number_analysis.md)
- [تقرير تجربة المحاولة](attempt_number_report.md)
- [ملاءمة صيغ تجربة المحاولة](attempt_number_training.md)
- [إعادة حساب مرجع تجربة المحاولة](attempt_number_validation.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [مرجع المسارات والإصدارات](../paths.md)

## ٣. المدخلات

مصفوفة أصلية ومعرف صيغة، أو فروق توقعات مترابطة بمعرف الطالب.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

مصفوفة بحثية وبصمات وفترة عدم يقين وسجل سلامة.

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
<a href="attempt_number_analysis.md">صفحة المستدعي</a>
<br>
<code>descriptive_analysis</code>
<br>
<a href="attempt_number_analysis.md">صفحة المستدعي</a>
<br>
<code>evaluate_predictions</code>
<br>
<a href="attempt_number_core.md">صفحة المستدعي</a>
<br>
<code>capture_protected</code>
<br>
<a href="attempt_number_core.md">صفحة المستدعي</a>
<br>
<code>verify_protected</code>
<br>
<a href="attempt_number_training.md">صفحة المستدعي</a>
<br>
<code>run_training</code>
</td>
</tr>
<tr>
<td>
<code>transform_matrix</code>
</td>
<td>
تحويل رقم المحاولة إلى الصيغة التجريبية المختارة.
</td>
<td>
<pre>transform_matrix(matrix, variant)</pre>
</td>
<td>
<pre>result.rename(columns={'attempt_number': 'is_repeat'})</pre>
<pre>result.drop(columns='attempt_number')</pre>
<pre>result</pre>
</td>
<td>
<a href="attempt_number_training.md">صفحة المستدعي</a>
<br>
<code>run_training</code>
<br>
<a href="attempt_number_validation.md">صفحة المستدعي</a>
<br>
<code>original_validation</code>
</td>
</tr>
<tr>
<td>
<code>row_fingerprint</code>
</td>
<td>
بصمة هوية وترتيب الصفوف المستخدمة في المقارنة.
</td>
<td>
<pre>row_fingerprint(frame)</pre>
</td>
<td>
<pre>hashlib.sha256(hashed.to_numpy().tobytes()).hexdigest()</pre>
</td>
<td>
<a href="attempt_number_training.md">صفحة المستدعي</a>
<br>
<code>run_training</code>
<br>
<a href="attempt_number_validation.md">صفحة المستدعي</a>
<br>
<code>original_validation</code>
</td>
</tr>
<tr>
<td>
<code>paired_cluster_interval</code>
</td>
<td>
فترة عدم يقين بفروق مزدوجة وإعادة أخذ عينات بالطالب.
</td>
<td>
<pre>paired_cluster_interval(students, differences, *, draws=1000)</pre>
</td>
<td>
<pre>{'rows': len(work), 'students': len(groups), 'delta': float(work.delta.mean()), 'low': float(np.quantile(results, 0.025)), 'high': float(np.quantile(results, 0.975)), 'draws': draws, 'seed': 42}</pre>
</td>
<td>
<a href="attempt_number_analysis.md">صفحة المستدعي</a>
<br>
<code>evaluate_predictions</code>
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
<pre>{p.relative_to(PROJECT_ROOT).as_posix(): file_sha256(p) for p in sorted(paths)}</pre>
</td>
<td>
<a href="attempt_number_core.md">صفحة المستدعي</a>
<br>
<code>capture_protected</code>
<br>
<a href="attempt_number_core.md">صفحة المستدعي</a>
<br>
<code>verify_protected</code>
</td>
</tr>
<tr>
<td>
<code>capture_protected</code>
</td>
<td>
تسجيل بصمات الحماية قبل تشغيل التجربة.
</td>
<td>
<pre>capture_protected()</pre>
</td>
<td>
<pre>verify_protected()</pre>
</td>
<td>
لا نداء رمز مباشر محسوم في الفهرس؛ قد يكون واجهة عامة أو نداء كائن أو موضع اختبار.
</td>
</tr>
<tr>
<td>
<code>verify_protected</code>
</td>
<td>
مقارنة بصمات المصدر والأصول قبل التجربة وبعدها.
</td>
<td>
<pre>verify_protected()</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="attempt_number_core.md">صفحة المستدعي</a>
<br>
<code>capture_protected</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
write_json
```

تحويل المصفوفة نسخة منفصلة؛ إعادة أخذ العينات تكون بالطالب لا بالصف لتبقى المحاولات المترابطة معًا. مقارنة البصمات تكشف أي تغيير محمي.

## ٦. كيف تتغير البيانات؟

التحول الرئيسي هو من المدخل الموصوف إلى المخرج الموصوف عبر الخطوات أعلاه. لم تتوفر عينة مستقلة موثقة تصلح لعرض قيم أكاديمية كاملة لهذا الملف؛ لذلك لا تُختلق بيانات جامعة أو درجات مودل.

## ٧. القواعد والافتراضات

هذا مسار تحليل أو تجربة صريح خارج طلب الخدمة. تفسير مخرجاته واعتمادها للتشغيل خطوتان منفصلتان.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

الفروق الصغيرة على المتوسط قد تخفي ضرر الإعادات؛ يجب قراءة الشرائح وعدم اليقين. المحاولة في السجل المرصود ليست بالضرورة كل التاريخ الجامعي.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [مرجع المسارات والإصدارات](../paths.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
```


مراجع خارج شجرة المصدر تستورد هذه الوحدة؛ ليست دليل تشغيل إنتاج:
[الأداة المرجعية](../../../scripts/experiments/attempt_number_experiment.py)

```text
scripts/experiments/attempt_number_experiment.py
```

[الأداة المرجعية](../../../scripts/experiments/attempt_number_recommendation.py)

```text
scripts/experiments/attempt_number_recommendation.py
```

[الأداة المرجعية](../../../scripts/experiments/student_progress_20261010/evidence/executed_workflow.py)

```text
scripts/experiments/student_progress_20261010/evidence/executed_workflow.py
```

[الأداة المرجعية](../../../scripts/experiments/student_progress_20261010/workflow.py)

```text
scripts/experiments/student_progress_20261010/workflow.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_attempt_number_experiment.py)

```text
tests/test_attempt_number_experiment.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_transform_keeps_other_columns_order_categories_and_input
test_unknown_or_invalid_attempt_cannot_become_first_attempt
test_row_fingerprint_detects_order_and_membership_changes
```

## ١١. القيود المعروفة

لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يدعم ثلاث صيغ بحثية لرقم المحاولة: كما هو، أو علم إعادة، أو حذفه. يحفظ هوية الصفوف وحماية الأصول.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
