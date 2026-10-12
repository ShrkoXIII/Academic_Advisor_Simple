# تدريب الزوج الرسمي واختيار إعداداته

```text
src/modeling/train_models.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يدرّب مودل علامة ومودل احتمال رسوب، ويختار الإعداد بطيّات زمنية قبل تقييم الاختبار اللاحق.

الدور في الخريطة:
تدريب

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تحليل أخطاء النموذج زمنيًا وبحسب المجموعات](../evaluation/analyze_model_errors.md)
- [تحليل أثر رقم المحاولة](../experiments/attempt_number_analysis.md)
- [ملاءمة صيغ تجربة المحاولة](../experiments/attempt_number_training.md)
- [إعادة حساب مرجع تجربة المحاولة](../experiments/attempt_number_validation.md)
- [تدريب تجربة المواد المستقلة](../experiments/course_only_training.md)
- [خوارزميات ملاءمة التجارب وتقييمها](../experiments/modeling.md)
- [تقييم المودلات الموسعة بالحالة السابقة](../experiments/previous_course_status_evaluation.md)
- [تدريب الحالة السابقة كميزة إضافية](../experiments/previous_course_status_training.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [الأهداف وأوزان التدريب](training_config.md)
- [مرجع المسارات والإصدارات](../paths.md)

## ٣. المدخلات

جدولا ميزات النسخة الثانية بعقد سبع وأربعين ميزة وهدفَي العلامة والرسوب.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

مودلان رسميان ومفاتيح فئات وبيانات وصفية للمقاييس والمصدر.

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
<code>_lightgbm</code>
</td>
<td>
تحميل مكتبة المودلات عند الحاجة للملاءمة.
</td>
<td>
<pre>_lightgbm()</pre>
</td>
<td>
<pre>lgb</pre>
</td>
<td>
<a href="train_models.md">صفحة المستدعي</a>
<br>
<code>train_one</code>
</td>
</tr>
<tr>
<td>
<code>regression_metrics</code>
</td>
<td>
حساب خطأ العلامة المطلق والتربيعي والتغطية القريبة.
</td>
<td>
<pre>regression_metrics(actual, predicted)</pre>
</td>
<td>
<pre>{'mae': float(mean_absolute_error(actual, predicted)), 'rmse': float(np.sqrt(mean_squared_error(actual, predicted))), 'within_5': float(np.mean(error &lt;= 5)), 'within_10': float(np.mean(error &lt;= 10))}</pre>
</td>
<td>
<a href="../experiments/previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>_paired_metrics</code>
<br>
<a href="../experiments/previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>evaluate_holdout</code>
<br>
<a href="train_models.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="../experiments/attempt_number_analysis.md">صفحة المستدعي</a>
<br>
<code>evaluate_predictions</code>
<br>
<a href="../experiments/attempt_number_training.md">صفحة المستدعي</a>
<br>
<code>model_metrics</code>
</td>
</tr>
<tr>
<td>
<code>classification_metrics</code>
</td>
<td>
حساب فقد ومقاييس احتمال الرسوب ومعايرته.
</td>
<td>
<pre>classification_metrics(actual, probability)</pre>
</td>
<td>
<pre>{'pr_auc': float(average_precision_score(actual, probability)), 'roc_auc': float(roc_auc_score(actual, probability)), 'brier': float(brier_score_loss(actual, probability)), 'log_loss': float(log_loss(actual, probability, labels=[0, 1])), 'calibration_error_10_bins': calibration_error}</pre>
</td>
<td>
<a href="../experiments/previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>_paired_metrics</code>
<br>
<a href="../experiments/previous_course_status_evaluation.md">صفحة المستدعي</a>
<br>
<code>evaluate_holdout</code>
<br>
<a href="train_models.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="../experiments/attempt_number_analysis.md">صفحة المستدعي</a>
<br>
<code>evaluate_predictions</code>
<br>
<a href="../experiments/attempt_number_training.md">صفحة المستدعي</a>
<br>
<code>model_metrics</code>
</td>
</tr>
<tr>
<td>
<code>calibration_table</code>
</td>
<td>
تجميع الاحتمالات في عشر شرائح ومقارنتها بالرسوب الفعلي.
</td>
<td>
<pre>calibration_table(actual, probability)</pre>
</td>
<td>
<pre>rows</pre>
</td>
<td>
<a href="train_models.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="../experiments/attempt_number_analysis.md">صفحة المستدعي</a>
<br>
<code>evaluate_predictions</code>
</td>
</tr>
<tr>
<td>
<code>shared_parameters</code>
</td>
<td>
إنشاء إعدادات ملاءمة ثابتة مشتركة للمهمتين.
</td>
<td>
<pre>shared_parameters(candidate)</pre>
</td>
<td>
<pre>{'learning_rate': 0.04, 'num_leaves': candidate['num_leaves'], 'min_data_in_leaf': candidate['min_data_in_leaf'], 'feature_fraction': candidate['feature_fraction'], 'bagging_fraction': candidate['bagging_fraction'], 'bagging_freq': 1, 'lambda_l1': candidate['lambda_l1'], 'lambda_l2': candidate['lambda_l2'], 'max_bin': 255, 'verbosity': -1, 'seed': SEED, 'feature_fraction_seed': SEED, 'bagging_seed': SEED, 'data_random_seed': SEED, 'deterministic': True, 'force_col_wise': True, 'num_threads': 0}</pre>
</td>
<td>
<a href="../experiments/course_only_training.md">صفحة المستدعي</a>
<br>
<code>train_experiment</code>
<br>
<a href="../experiments/modeling.md">صفحة المستدعي</a>
<br>
<code>fit_experiment_model</code>
<br>
<a href="../experiments/previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>tune_augmented_model</code>
<br>
<a href="../experiments/previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>train_all_variants</code>
<br>
<a href="train_models.md">صفحة المستدعي</a>
<br>
<code>tune_model</code>
</td>
</tr>
<tr>
<td>
<code>prepare_folds</code>
</td>
<td>
تكوين مصفوفات طيات زمنية بفئات تعلمت داخل الملاءمة.
</td>
<td>
<pre>prepare_folds(train)</pre>
</td>
<td>
<pre>prepared</pre>
</td>
<td>
<a href="../experiments/course_only_training.md">صفحة المستدعي</a>
<br>
<code>prepare_course_folds</code>
<br>
<a href="train_models.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>train_one</code>
</td>
<td>
ملاءمة مهمة واحدة مع أوزان وتوقف مبكر اختياري.
</td>
<td>
<pre>train_one(fit_X, fit_y, fit_weight, parameters, valid_X=None, valid_y=None, num_boost_round=MAX_BOOST_ROUNDS)</pre>
</td>
<td>
<pre>lgb.train(parameters, train_set, num_boost_round=num_boost_round, valid_sets=valid_sets, callbacks=callbacks)</pre>
</td>
<td>
<a href="../experiments/course_only_training.md">صفحة المستدعي</a>
<br>
<code>train_experiment</code>
<br>
<a href="train_models.md">صفحة المستدعي</a>
<br>
<code>tune_model</code>
<br>
<a href="train_models.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="../evaluation/analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>fit_historical_grade_model</code>
<br>
<a href="../experiments/attempt_number_training.md">صفحة المستدعي</a>
<br>
<code>run_training</code>
</td>
</tr>
<tr>
<td>
<code>tune_model</code>
</td>
<td>
اختيار المرشح الأقل بمتوسط متريّة المهمة عبر الطيات.
</td>
<td>
<pre>tune_model(prepared_folds, task)</pre>
</td>
<td>
<pre>(min(reports, key=lambda report: report['mean_primary_metric']), reports)</pre>
</td>
<td>
<a href="../experiments/course_only_training.md">صفحة المستدعي</a>
<br>
<code>train_experiment</code>
<br>
<a href="train_models.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>feature_importance</code>
</td>
<td>
ترتيب الميزات بحسب مكسب المودل.
</td>
<td>
<pre>feature_importance(model)</pre>
</td>
<td>
<pre>importance.head(25).to_dict(orient='records')</pre>
</td>
<td>
<a href="../experiments/course_only_training.md">صفحة المستدعي</a>
<br>
<code>train_experiment</code>
<br>
<a href="../experiments/previous_course_status_training.md">صفحة المستدعي</a>
<br>
<code>train_all_variants</code>
<br>
<a href="train_models.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>_json_default</code>
</td>
<td>
تحويل النوع العددي الخاص للتسلسل أو رفض غير المدعوم.
</td>
<td>
<pre>_json_default(value)</pre>
</td>
<td>
<pre>value.item()</pre>
</td>
<td>
لا نداء رمز مباشر محسوم في الفهرس؛ قد يكون واجهة عامة أو نداء كائن أو موضع اختبار.
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
_lightgbm
```

يجهز طيتين زمانيتين ويتعلم فئات الملاءمة لكل طية؛ يقارن ثلاثة إعدادات مع توقف مبكر، يختار أدنى متوسط خطأ للعلامة أو فقد احتمالي للرسوب، ثم يدرّب على كامل التدريب بعدد دورات متوسط ويقيّم الاختبار.

### الاختيار الحقيقي قبل الاختبار

الطية الأولى تلائم حتى نهاية سنة ألفين واثنتين وعشرين وتتحقق في التالية؛ الثانية تلائم حتى نهاية التالية وتتحقق في سنة ألفين وأربع وعشرين.

```text
grade: minimum mean MAE
fail: minimum mean log_loss
final rounds: rounded mean best_iteration
```

ثلاثة مرشحين للمعاملات؛ الاسم الحالي المصحح لمرشح السعة ذو ثلاث وستين ورقة موجود في الكود وفي الأصول. المودل الحالي للعلامة اختاره، بينما الرسوب اختار المرشح المتوازن.

```text
capacity_63
balanced_31
regularized_47
```

هذه هوية الأصول المفحوصة، ولا تضمن أن أي إعادة تدريب مستقبلية ستختار الأسماء نفسها. التحميل الرسمي يشترط هوية الأصول المعتمدة حاليًا.

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
classification_metrics

range(10)
in_bin.any()
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
calibration_table

range(10)
in_bin.any()
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
prepare_folds

TEMPORAL_FOLDS
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
train_one

valid_X is not None
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
tune_model

PARAMETER_CANDIDATES
prepared_folds
task == 'grade'
```

## ٦. كيف تتغير البيانات؟

التحول الرئيسي هو من المدخل الموصوف إلى المخرج الموصوف عبر الخطوات أعلاه. لم تتوفر عينة مستقلة موثقة تصلح لعرض قيم أكاديمية كاملة لهذا الملف؛ لذلك لا تُختلق بيانات جامعة أو درجات مودل.

## ٧. القواعد والافتراضات

يجهز طيتين زمانيتين ويتعلم فئات الملاءمة لكل طية؛ يقارن ثلاثة إعدادات مع توقف مبكر، يختار أدنى متوسط خطأ للعلامة أو فقد احتمالي للرسوب، ثم يدرّب على كامل التدريب بعدد دورات متوسط ويقيّم الاختبار.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

تعلم الفئات أو اختيار الإعداد من اختبار سنة ألفين وخمس وعشرين يلوث التقييم؛ لا يستعمل الاختبار للاختيار هنا.

أي قيمة أو قطع غير مطابق يجب أن يرفض أو يسجل غير متاح حسب العقد، قبل تحويله إلى توقع. لا تعالج هذه الصفحة نقص المصدر بتغيير ميزة أو وضع قيمة افتراضية.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [الأهداف وأوزان التدريب](training_config.md)
- [مرجع المسارات والإصدارات](../paths.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
sklearn
lightgbm
```


مراجع خارج شجرة المصدر تستورد هذه الوحدة؛ ليست دليل تشغيل إنتاج:
[الأداة المرجعية](../../../debugging/pipeline_audit.py)

```text
debugging/pipeline_audit.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_modeling_v2_io.py)

```text
tests/test_modeling_v2_io.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_modeling_io_constants_resolve_to_isolated_v2_files
test_main_reads_v2_and_writes_only_v2_with_correct_metadata
test_missing_v2_input_fails_without_reading_v1_or_writing_models
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert hasattr(paths, versioned_name)
```

[ملف اختبار مرتبط](../../../tests/test_train_models.py)

```text
tests/test_train_models.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_regression_metrics_known_errors_and_inclusive_boundaries
test_classification_metrics_known_ranking_and_probabilities
test_classification_metrics_clips_endpoint_probabilities
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert result == pytest.approx({'mae': 7.5, 'rmse': math.sqrt(87.5), 'within_5': 0.5, 'within_10': 0.75})
```

## ١١. القيود المعروفة

هذه نقطة تدريب تكتب الأصول عند تشغيلها. التوثيق لم يشغلها. لا تنشئ مودلات المرحلة الأولى أو ترقيتها تلقائيًا.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- اختيار مرشح العلامة والرسوب مستقل ومن طيات زمنية.
- الاختبار اللاحق لا يختار المرشح.
- الأصول المحفوظة تشمل العقود والفئات ومصدر التدريب.

ثلاثة أسئلة للفهم:

1. ما الفرق بين مقياس اختيار العلامة ومقياس اختيار الرسوب؟
2. كيف يحدد عدد دورات الملاءمة النهائية؟
3. لماذا لا يكفي حفظ ملف مودل دون بيانات المصدر والفئات؟

تمرين قراءة آمن:

اكتب جدول طيتي التحقق وحدود الملاءمة، وحدد في أي جزء يسمح بتعلم الفئات وفي أي جزء يمنع ذلك.

التمرين قراءة وحساب على الورق؛ لا يغير المشروع ولا يشغّل بناءً أو توقعًا أو تحديث تاريخ.
