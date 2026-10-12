# تحليل أخطاء النموذج زمنيًا وبحسب المجموعات

```text
src/evaluation/analyze_model_errors.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يفسر مواضع الخطأ ويقارنها عبر سنوات واختصاصات وشرائح.

الدور في الخريطة:
تقييم

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

له نقطة تشغيل مباشرة؛ عدم وجود مستورد لا يعني عدم استعماله.

الوحدات التي يعتمد عليها بعد ذلك:

- [تقييم معدل الخطط المرصودة](evaluate_plan_gpa.md)
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [تحويل العلامة إلى نقاط وفق النسخة](../grade_scale.md)
- [تدريب الزوج الرسمي واختيار إعداداته](../modeling/train_models.md)
- [الأهداف وأوزان التدريب](../modeling/training_config.md)
- [مرجع المسارات والإصدارات](../paths.md)

## ٣. المدخلات

ميزات تدريب واختبار ومودل نهائي وبيانات إعداداته.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

أسماء الحقول المعرّفة في الملف:

```text
EXTRA_ANALYSIS_COLUMNS
degree_name_sl_status
course_history_missing
gpa_trend_missing
gpa_prev_1
```

## ٤. المخرجات

تقارير أخطاء وتحليلات مجموعات وأهمية تفسيرية للميزات.

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
<code>one_way_effect_size</code>
</td>
<td>
قياس نسبة تباين المتريّة المفسرة بالمجموعة.
</td>
<td>
<pre>one_way_effect_size(frame, group_column, value_column)</pre>
</td>
<td>
<pre>{'groups': int(group_count), 'rows': int(len(clean)), 'eta_squared': eta_squared, 'omega_squared': omega_squared}</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>course_metrics</code>
</td>
<td>
حساب أخطاء توقع المادة في شريحة.
</td>
<td>
<pre>course_metrics(frame)</pre>
</td>
<td>
<pre>pd.Series({'course_rows': len(frame), 'mark_mae': absolute_error.mean(), 'mark_rmse': np.sqrt(np.mean(np.square(error))), 'mark_bias': error.mean(), 'mark_within_5': absolute_error.le(5).mean(), 'mark_within_10': absolute_error.le(10).mean()})</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>build_course_segments</code>
</td>
</tr>
<tr>
<td>
<code>plan_metrics</code>
</td>
<td>
حساب أخطاء معدل وجودة الخطط في شريحة.
</td>
<td>
<pre>plan_metrics(frame)</pre>
</td>
<td>
<pre>pd.Series({'plans': len(frame), 'plan_gpa_mae': absolute_error.mean(), 'plan_gpa_rmse': np.sqrt(np.mean(np.square(frame['plan_gpa_error']))), 'plan_gpa_bias': frame['plan_gpa_error'].mean(), 'plan_within_0_25': absolute_error.le(0.25).mean(), 'plan_within_0_50': absolute_error.le(0.5).mean(), 'plan_within_1_00': absolute_error.le(1.0).mean(), 'previous_gpa_coverage': previous_available.mean(), 'model_mae_on_previous_gpa_rows': model_same_rows.mean(), 'previous_gpa_baseline_mae': previous_error.mean(), 'improvement_over_previous_gpa': 1 - model_same_rows.mean() / previous_error.mean()})</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>segment_metrics</code>
<br>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>build_plan_segments</code>
</td>
</tr>
<tr>
<td>
<code>selected_fold_iterations</code>
</td>
<td>
استخراج عدد دورات المرجع للطية الزمنية.
</td>
<td>
<pre>selected_fold_iterations(metadata)</pre>
</td>
<td>
<pre>iterations</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>make_out_of_time_predictions</code>
</td>
</tr>
<tr>
<td>
<code>fit_historical_grade_model</code>
</td>
<td>
ملاءمة مودل علامة بماضٍ محدود للتحليل.
</td>
<td>
<pre>fit_historical_grade_model(train, cutoff_part, rounds, candidate)</pre>
</td>
<td>
<pre>(model, category_levels)</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>make_out_of_time_predictions</code>
</td>
</tr>
<tr>
<td>
<code>attach_analysis_columns</code>
</td>
<td>
إضافة السنة وحقول تقسيم التحليل إلى التوقعات.
</td>
<td>
<pre>attach_analysis_columns(course_predictions, source)</pre>
</td>
<td>
<pre>course_predictions</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>make_out_of_time_predictions</code>
</td>
</tr>
<tr>
<td>
<code>make_out_of_time_predictions</code>
</td>
<td>
توقع فصول بعد نهاية ملاءمة كل مودل تاريخي.
</td>
<td>
<pre>make_out_of_time_predictions(train, test, metadata, grade_scale, final_model)</pre>
</td>
<td>
<pre>pd.concat(predictions, ignore_index=True)</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>build_plan_frame</code>
</td>
<td>
جمع المواد في خطط مرصودة وإضافة سياق المقارنة.
</td>
<td>
<pre>build_plan_frame(course_predictions)</pre>
</td>
<td>
<pre>plans</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>build_year_analysis</code>
</td>
<td>
تجميع مقاييس المواد والخطط بحسب السنة.
</td>
<td>
<pre>build_year_analysis(course_predictions, plans)</pre>
</td>
<td>
<pre>course.merge(plan, on='academic_year')</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>build_degree_analysis</code>
</td>
<td>
تجميع المقاييس بحسب الاختصاص مع علم دعم العينة.
</td>
<td>
<pre>build_degree_analysis(course_predictions, plans)</pre>
</td>
<td>
<pre>result.sort_values(['enough_support', 'plans'], ascending=[False, False], kind='stable').reset_index(drop=True)</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>build_year_degree_analysis</code>
</td>
<td>
تجميع السنة والاختصاص معًا.
</td>
<td>
<pre>build_year_degree_analysis(course_predictions, plans)</pre>
</td>
<td>
<pre>result.sort_values(['academic_year', 'plans'], ascending=[True, False], kind='stable').reset_index(drop=True)</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>segment_metrics</code>
</td>
<td>
إرفاق اسم الشريحة بمقاييس خططها.
</td>
<td>
<pre>segment_metrics(frame, segment, level)</pre>
</td>
<td>
<pre>metrics</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>build_plan_segments</code>
</td>
</tr>
<tr>
<td>
<code>build_plan_segments</code>
</td>
<td>
قياس الخطط عبر شرائح الحمل والسياق.
</td>
<td>
<pre>build_plan_segments(plans)</pre>
</td>
<td>
<pre>pd.DataFrame(frames)[['segment', 'level', *plan_metrics(plans).index.tolist()]]</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>build_course_segments</code>
</td>
<td>
قياس المواد عبر شرائح العلامة والفقدان.
</td>
<td>
<pre>build_course_segments(course_predictions)</pre>
</td>
<td>
<pre>pd.DataFrame(frames)[['segment', 'level', *course_metrics(course_predictions).index.tolist()]]</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>feature_family</code>
</td>
<td>
تجميع اسم الميزة في عائلتها التفسيرية.
</td>
<td>
<pre>feature_family(feature)</pre>
</td>
<td>
<pre>'course_history'</pre>
<pre>'plan_load'</pre>
<pre>'pre_university'</pre>
<pre>'calendar_and_policy'</pre>
<pre>'course_and_degree_plan'</pre>
<pre>'student_history'</pre>
</td>
<td>
لا نداء رمز مباشر محسوم في الفهرس؛ قد يكون واجهة عامة أو نداء كائن أو موضع اختبار.
</td>
</tr>
<tr>
<td>
<code>build_shap_importance</code>
</td>
<td>
حساب مساهمة الميزات المطلقة وأهميتها حسب العائلة.
</td>
<td>
<pre>build_shap_importance(model, test)</pre>
</td>
<td>
<pre>(importance, families)</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
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
one_way_effect_size
```

ينشئ توقعات خارج زمن الملاءمة بمودلات تاريخية، يلخص المواد والخطط والشرائح ثم يحسب مساهمات تفسيرية على عينة ثابتة.

## ٦. كيف تتغير البيانات؟

التحول الرئيسي هو من المدخل الموصوف إلى المخرج الموصوف عبر الخطوات أعلاه. لم تتوفر عينة مستقلة موثقة تصلح لعرض قيم أكاديمية كاملة لهذا الملف؛ لذلك لا تُختلق بيانات جامعة أو درجات مودل.

## ٧. القواعد والافتراضات

ينشئ توقعات خارج زمن الملاءمة بمودلات تاريخية، يلخص المواد والخطط والشرائح ثم يحسب مساهمات تفسيرية على عينة ثابتة.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

قراءة الاسم توحي بتحليل فقط لكن بعض وظائفه تدرّب مودلات تاريخية؛ لا تُشغّل بلا إذن.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [تقييم معدل الخطط المرصودة](evaluate_plan_gpa.md)
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [تحويل العلامة إلى نقاط وفق النسخة](../grade_scale.md)
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

[ملف اختبار مرتبط](../../../tests/test_analyze_model_errors.py)

```text
tests/test_analyze_model_errors.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_modeling_does_not_import_evaluation
test_course_metrics
test_plan_metrics_previous_gpa_coverage_and_boundaries
```

[ملف اختبار مرتبط](../../../tests/test_evaluation_v2_io.py)

```text
tests/test_evaluation_v2_io.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_plan_evaluation_reads_and_writes_v2_with_shared_grade_scale
test_error_analysis_uses_v2_in_historical_holdout_and_shap_paths
test_missing_v2_input_fails_without_v1_fallback_or_output
```

## ١١. القيود المعروفة

الدعم الصغير في الاختصاص يوضع له علم موثوقية؛ الشرح الإحصائي ليس سببًا أكاديميًا حتميًا.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يفسر مواضع الخطأ ويقارنها عبر سنوات واختصاصات وشرائح.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: الدعم الصغير في الاختصاص يوضع له علم موثوقية؛ الشرح الإحصائي ليس سببًا أكاديميًا حتميًا.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
