# تدريب الحالة السابقة كميزة إضافية

```text
src/experiments/previous_course_status_training.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يختبر زيادة عقد المادة إلى أربعة وثلاثين والخطة إلى ثمانية وأربعين دون ترقيتهما للتشغيل.

الدور في الخريطة:
تجريبي

تصنيف الاستعمال:
تجريبي أو وصفي خارج الخدمة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تقييم المودلات الموسعة بالحالة السابقة](previous_course_status_evaluation.md)
- [تنسيق تجربة توصيات الحالة السابقة](../recommendation_experiments/previous_course_status_experiment.md)
- [مقارنة توقعات وخطط الحالة السابقة](../recommendation_experiments/previous_course_status_inference.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [حساب البحث على ميزات المادة فقط](course_only_core.md)
- [تدريب تجربة المواد المستقلة](course_only_training.md)
- [بيانات تجربة الحالة السابقة](previous_course_status_data.md)
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [تصنيف أحدث محاولة سابقة](../features/student_course_status.md)

## ٣. المدخلات

ملفات الميزات الموسعة وبديل يحدد العقد الأساسي.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

مودلات بحثية ومستويات فئة الحالة وسجل مصدر.

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
<code>learn_augmented_levels</code>
</td>
<td>
إضافة قاموس ثابت لفئة الحالة إلى مستويات الأصل.
</td>
<td>
<pre>learn_augmented_levels(frame)</pre>
</td>
<td>
<pre>levels</pre>
</td>
<td>
<a href="previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>prepare_augmented_folds</code>
<br>
<a href="previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>train_all_variants</code>
</td>
</tr>
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
<pre>matrix[[*base_features, 'previous_course_status']]</pre>
</td>
<td>
<a href="previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>evaluate_holdout</code>
<br>
<a href="previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>prepare_augmented_folds</code>
<br>
<a href="previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>train_all_variants</code>
<br>
<a href="../recommendation_experiments/previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>prepare_augmented_matrix</code>
</td>
</tr>
<tr>
<td>
<code>prepare_augmented_folds</code>
</td>
<td>
بناء طيات زمنية بالمصفوفة الموسعة.
</td>
<td>
<pre>prepare_augmented_folds(train, base_features)</pre>
</td>
<td>
<pre>prepared</pre>
</td>
<td>
<a href="previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>train_all_variants</code>
</td>
</tr>
<tr>
<td>
<code>train_augmented_one</code>
</td>
<td>
ملاءمة مودل بميزات موسعة وفئة حالة ثابتة.
</td>
<td>
<pre>train_augmented_one(fit_X, fit_y, fit_weight, parameters, valid_X=None, valid_y=None, num_boost_round=official.MAX_BOOST_ROUNDS)</pre>
</td>
<td>
<pre>lgb.train(parameters, train_set, num_boost_round=num_boost_round, valid_sets=valid_sets, callbacks=callbacks)</pre>
</td>
<td>
<a href="previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>tune_augmented_model</code>
<br>
<a href="previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>train_all_variants</code>
</td>
</tr>
<tr>
<td>
<code>tune_augmented_model</code>
</td>
<td>
اختيار إعداد للعلامة أو الرسوب عبر الطيات.
</td>
<td>
<pre>tune_augmented_model(prepared_folds, task)</pre>
</td>
<td>
<pre>(min(reports, key=lambda report: report['mean_primary_metric']), reports)</pre>
</td>
<td>
<a href="previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>train_all_variants</code>
</td>
</tr>
<tr>
<td>
<code>_input_sha256</code>
</td>
<td>
بصمة ملفات مدخلات التجربة.
</td>
<td>
<pre>_input_sha256()</pre>
</td>
<td>
<pre>{path.relative_to(PROJECT_ROOT).as_posix(): file_sha256(path) for path in paths}</pre>
</td>
<td>
<a href="previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>load_variant</code>
<br>
<a href="previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>train_all_variants</code>
</td>
</tr>
<tr>
<td>
<code>_load_tables</code>
</td>
<td>
قراءة ميزات البحث والتحقق من الفترة والحقول.
</td>
<td>
<pre>_load_tables()</pre>
</td>
<td>
<pre>(train, test)</pre>
</td>
<td>
<a href="previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>evaluate_holdout</code>
<br>
<a href="previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>train_all_variants</code>
</td>
</tr>
<tr>
<td>
<code>load_variant</code>
</td>
<td>
تحميل صيغة موسعة بعد فحص المصدر والعقد.
</td>
<td>
<pre>load_variant(variant, *, signature=None)</pre>
</td>
<td>
<pre>(grade, fail, levels, metadata)</pre>
</td>
<td>
<a href="previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>evaluate_holdout</code>
<br>
<a href="previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>train_all_variants</code>
<br>
<a href="../recommendation_experiments/previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>_load_experimental_models</code>
</td>
</tr>
<tr>
<td>
<code>train_all_variants</code>
</td>
<td>
ملاءمة جميع الصيغ البحثية المعتمدة لهذه التجربة.
</td>
<td>
<pre>train_all_variants()</pre>
</td>
<td>
<pre>outputs</pre>
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
learn_augmented_levels
```

يثبت قائمة حالات الفئة، يجهز الطيات الزمنية ويتعلم مصفوفة موسعة ثم يختار ويدرب ويحفظ الأصول؛ التحميل يتحقق من البصمات والعدد.

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
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [تصنيف أحدث محاولة سابقة](../features/student_course_status.md)
- [تدريب الزوج الرسمي واختيار إعداداته](../modeling/train_models.md)
- [الأهداف وأوزان التدريب](../modeling/training_config.md)
- [مرجع المسارات والإصدارات](../paths.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
lightgbm
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_previous_course_status_training.py)

```text
tests/test_previous_course_status_training.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_augmented_matrix_keeps_order_and_maps_unseen_status
test_augmented_folds_keep_official_cutoffs_and_fit_weights
test_lightgbm_receives_six_categorical_features
```

## ١١. القيود المعروفة

لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يختبر زيادة عقد المادة إلى أربعة وثلاثين والخطة إلى ثمانية وأربعين دون ترقيتهما للتشغيل.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: لا يُستدعى هذا الملف لإنتاج طلب الشبكة الحالي. بعض نقاط التنفيذ تدرب أو تحفظ نتائج؛ لم تُشغّل في هذه المهمة.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.

