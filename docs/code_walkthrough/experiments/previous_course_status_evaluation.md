# تقييم المودلات الموسعة بالحالة السابقة

```text
src/experiments/previous_course_status_evaluation.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يقارن النموذج الأساسي والموسع على الصفوف نفسها وشرائح الحالات.

الدور في الخريطة:
تجريبي

تصنيف الاستعمال:
تجريبي أو وصفي خارج الخدمة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تنسيق تجربة توصيات الحالة السابقة](../recommendation_experiments/previous_course_status_experiment.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [حساب البحث على ميزات المادة فقط](course_only_core.md)
- [تدريب تجربة المواد المستقلة](course_only_training.md)
- [بيانات تجربة الحالة السابقة](previous_course_status_data.md)
- [تدريب الحالة السابقة كميزة إضافية](previous_course_status_training.md)
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [تصنيف أحدث محاولة سابقة](../features/student_course_status.md)

## ٣. المدخلات

اختبار موسع ومودلات رسمية وبحثية.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

مقاييس مقارنة وتوقعات وعينات إعادة منقحة في الاستخدام الخارجي.

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
<code>status_slices</code>
</td>
<td>
تقسيم المقاييس بحسب الحالة السابقة وحساب فروقها.
</td>
<td>
<pre>status_slices(*, actual_grade, actual_fail, baseline_grade, augmented_grade, baseline_fail, augmented_fail, status)</pre>
</td>
<td>
<pre>slices</pre>
</td>
<td>
<a href="previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>_paired_metrics</code>
</td>
</tr>
<tr>
<td>
<code>_predict</code>
</td>
<td>
توقع المودل مع فحص الشكل والمدى.
</td>
<td>
<pre>_predict(model, matrix, maximum)</pre>
</td>
<td>
<pre>np.clip(values, 0, maximum)</pre>
</td>
<td>
<a href="previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>evaluate_holdout</code>
</td>
</tr>
<tr>
<td>
<code>_paired_metrics</code>
</td>
<td>
مقارنة مقاييس العقود على الصفوف نفسها.
</td>
<td>
<pre>_paired_metrics(test, predictions, baseline_number, augmented_number, baseline_meta, augmented_meta)</pre>
</td>
<td>
<pre>{'baseline_features': baseline_number, 'experimental_features': augmented_number, 'grade': {key: {'baseline': gb[key], 'augmented': gn[key], 'delta': gn[key] - gb[key]} for key in gb}, 'fail': {key: {'baseline': fb[key], 'augmented': fn[key], 'delta': fn[key] - fb[key]} for key in fb}, 'cv_mean_mae': {'baseline': baseline_meta['grade'], 'augmented': augmented_meta['grade'], 'delta': augmented_meta['grade'] - baseline_meta['grade']}, 'cv_mean_log_loss': {'baseline': baseline_meta['fail'], 'augmented': augmented_meta['fail'], 'delta': augmented_meta['fail'] - baseline_meta['fail']}, 'by_previous_status': status_slices(actual_grade=actual_grade, actual_fail=actual_fail, baseline_grade=grade_base, augmented_grade=grade_new, baseline_fail=fail_base, augmented_fail=fail_new, status=test['previous_course_status'])}</pre>
</td>
<td>
<a href="previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>evaluate_holdout</code>
</td>
</tr>
<tr>
<td>
<code>_check_saved_baseline</code>
</td>
<td>
اشتراط إعادة إنتاج مقاييس المرجع المحفوظ.
</td>
<td>
<pre>_check_saved_baseline(fresh, saved, label)</pre>
</td>
<td>
<pre>differences</pre>
</td>
<td>
<a href="previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>evaluate_holdout</code>
</td>
</tr>
<tr>
<td>
<code>_retake_sample</code>
</td>
<td>
اختيار عينات إعادة مستقرة لإيضاح فروق التوقع.
</td>
<td>
<pre>_retake_sample(predictions)</pre>
</td>
<td>
<pre>pd.DataFrame(rows)</pre>
</td>
<td>
<a href="previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>evaluate_holdout</code>
</td>
</tr>
<tr>
<td>
<code>evaluate_holdout</code>
</td>
<td>
قياس العقود الأساسية والموسعة في الاختبار اللاحق.
</td>
<td>
<pre>evaluate_holdout()</pre>
</td>
<td>
<pre>summary</pre>
</td>
<td>
<a href="../recommendation_experiments/previous_course_status_experiment.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
status_slices
```

يتوقع العقود الأساسية والموسعة، يراجع تطابق المرجع المحفوظ ويحسب فروق العلامة والرسوب لكل حالة؛ لا يفعّل المودلات.

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

- [حساب البحث على ميزات المادة فقط](course_only_core.md)
- [تدريب تجربة المواد المستقلة](course_only_training.md)
- [بيانات تجربة الحالة السابقة](previous_course_status_data.md)
- [تدريب الحالة السابقة كميزة إضافية](previous_course_status_training.md)
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [تصنيف أحدث محاولة سابقة](../features/student_course_status.md)
- [تدريب الزوج الرسمي واختيار إعداداته](../modeling/train_models.md)
- [مرجع المسارات والإصدارات](../paths.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
lightgbm
sklearn
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_previous_course_status_evaluation.py)

```text
tests/test_previous_course_status_evaluation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_status_slices_measure_retake_errors_without_small_group_pr_auc
```

## ١١. القيود المعروفة

لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يقارن النموذج الأساسي والموسع على الصفوف نفسها وشرائح الحالات.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
