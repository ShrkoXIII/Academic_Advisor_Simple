# تقييم معدل الخطط المرصودة

```text
src/evaluation/evaluate_plan_gpa.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يقيس دقة مودل العلامة على خطط الطلاب المرصودة، لا جودة اختيار خطة لم تُسجل.

الدور في الخريطة:
تقييم

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تحليل أخطاء النموذج زمنيًا وبحسب المجموعات](analyze_model_errors.md)
- [تحليل أثر رقم المحاولة](../experiments/attempt_number_analysis.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [تحويل العلامة إلى نقاط وفق النسخة](../grade_scale.md)
- [مرجع المسارات والإصدارات](../paths.md)

## ٣. المدخلات

ميزات الاختبار ومودل العلامة الرسمي وسلم العلامات ومستويات الفئات.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

أسماء الحقول المعرّفة في الملف:

```text
AUDIT_COLUMNS
student_course_id
student_id
degree_id
part_id
course_id
course_name_sl
course_credits
grade_version_id
final_mark
points
gpa_points
```

## ٤. المخرجات

توقعات مواد وملخصات خطط ومقاييس معدل محفوظة.

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
<code>predict_course_points</code>
</td>
<td>
توقع العلامة وتحويلها لنقاط سلم الطالب.
</td>
<td>
<pre>predict_course_points(frame, grade_model, category_levels, grade_scale)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>make_out_of_time_predictions</code>
<br>
<a href="evaluate_plan_gpa.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>aggregate_plan_gpa</code>
</td>
<td>
جمع جودة المواد الحقيقية والمتوقعة إلى معدل خطة.
</td>
<td>
<pre>aggregate_plan_gpa(course_predictions)</pre>
</td>
<td>
<pre>plans.sort_values('plan_gpa_absolute_error', ascending=False, kind='stable').reset_index(drop=True)</pre>
</td>
<td>
<a href="analyze_model_errors.md">صفحة المستدعي</a>
<br>
<code>build_plan_frame</code>
<br>
<a href="evaluate_plan_gpa.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>summarize_plan_errors</code>
</td>
<td>
تلخيص الخطأ المطلق والتربيعي والانحياز والدقة القريبة.
</td>
<td>
<pre>summarize_plan_errors(plans)</pre>
</td>
<td>
<pre>{'plans': int(len(plans)), 'mae': float(absolute_error.mean()), 'credits_weighted_mae': float(np.average(absolute_error, weights=weights)), 'rmse': float(np.sqrt(np.mean(np.square(error)))), 'bias': float(error.mean()), 'median_absolute_error': float(np.median(absolute_error)), 'within_0_25': float(np.mean(absolute_error &lt;= 0.25)), 'within_0_50': float(np.mean(absolute_error &lt;= 0.5)), 'within_1_00': float(np.mean(absolute_error &lt;= 1.0))}</pre>
</td>
<td>
<a href="evaluate_plan_gpa.md">صفحة المستدعي</a>
<br>
<code>build_metrics_report</code>
<br>
<a href="../experiments/attempt_number_analysis.md">صفحة المستدعي</a>
<br>
<code>evaluate_predictions</code>
</td>
</tr>
<tr>
<td>
<code>build_metrics_report</code>
</td>
<td>
تكوين مقاييس عامة وبحسب الفصل مع صيغة الحساب.
</td>
<td>
<pre>build_metrics_report(course_predictions, plans)</pre>
</td>
<td>
<pre>{'evaluation_unit': 'student_id + degree_id + part_id', 'feature_engineering_version': FEATURE_ENGINEERING_VERSION, 'actual_plan_gpa_formula': 'sum(course_credits * actual_points) / sum(course_credits)', 'predicted_plan_gpa_formula': 'sum(course_credits * predicted_points) / sum(course_credits)', 'predicted_points_source': 'GradeRegressor predicted_mark mapped through v_acs_grade', 'course_rows': int(len(course_predictions)), 'overall': summarize_plan_errors(plans), 'by_part': by_part}</pre>
</td>
<td>
<a href="evaluate_plan_gpa.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>print_report</code>
</td>
<td>
عرض ملخص المقاييس المسجلة.
</td>
<td>
<pre>print_report(report, plans)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="evaluate_plan_gpa.md">صفحة المستدعي</a>
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
predict_course_points
```

يتوقع العلامة ثم يحول النقاط، يجمع جودة النتائج الحقيقية والمتوقعة بساعات المواد، يقارن المعدلَيْن ويحسب الخطأ العام والمرجح وبحسب الفصل.

## ٦. كيف تتغير البيانات؟

التحول الرئيسي هو من المدخل الموصوف إلى المخرج الموصوف عبر الخطوات أعلاه. لم تتوفر عينة مستقلة موثقة تصلح لعرض قيم أكاديمية كاملة لهذا الملف؛ لذلك لا تُختلق بيانات جامعة أو درجات مودل.

## ٧. القواعد والافتراضات

يتوقع العلامة ثم يحول النقاط، يجمع جودة النتائج الحقيقية والمتوقعة بساعات المواد، يقارن المعدلَيْن ويحسب الخطأ العام والمرجح وبحسب الفصل.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

دقة معدل الخطة المرصودة لا تثبت ترتيب أفضل توصية ولا أثرًا على الطالب.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [تحويل العلامة إلى نقاط وفق النسخة](../grade_scale.md)
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

[ملف اختبار مرتبط](../../../tests/test_evaluate_plan_gpa.py)

```text
tests/test_evaluate_plan_gpa.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_predict_course_points_preserves_audit_and_quality_points
test_aggregate_plan_gpa_uses_student_degree_part_and_credit_weighting
test_summarize_plan_errors_includes_threshold_boundaries
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

[ملف اختبار مرتبط](../../../tests/test_plan_gpa_evaluation.py)

```text
tests/test_plan_gpa_evaluation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_plan_gpa_uses_credit_weighted_points
```

## ١١. القيود المعروفة

التقييم الرسمي هنا للزوج السابق على الاختبار، وليس تقييم سياسة المرحلتين.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يقيس دقة مودل العلامة على خطط الطلاب المرصودة، لا جودة اختيار خطة لم تُسجل.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: التقييم الرسمي هنا للزوج السابق على الاختبار، وليس تقييم سياسة المرحلتين.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
