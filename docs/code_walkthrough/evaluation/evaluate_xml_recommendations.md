# تقييم توصيات ملفات التصدير

```text
src/evaluation/evaluate_xml_recommendations.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يقارن توصيات محلية بمواد مسجلة في أمثلة تصدير ويكتب تقارير أثر.

الدور في الخريطة:
تقييم

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [واجهة اسم قديم لتقييم التصدير](../evaluate_xml_recommendations.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [أدوات تنظيف الأعمدة والمعرفات](../data/cleaning_utils.md)
- [قراءة تصدير الجداول وإصلاح النص مؤقتًا](../data/xml_spreadsheet.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [تصدير واجهات نواة التوصية](../recommendation/__init__.md)
- [عقود النواة والمدخلات المحلية](../recommendation/inputs.md)

## ٣. المدخلات

ملفات تصدير محلية وهدف وقطع صريح وأصول رسمية.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

تقارير حالات وتداخل مجموعات مواد ومقارنة معدل وتوقع خطة مرصودة.

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
<code>parse_args</code>
</td>
<td>
قراءة خيارات أداة التنفيذ والتحقق من شكلها.
</td>
<td>
<pre>parse_args()</pre>
</td>
<td>
<pre>parser.parse_args()</pre>
</td>
<td>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>json_value</code>
</td>
<td>
تهيئة قيم التقرير للتسلسل الآمن.
</td>
<td>
<pre>json_value(value)</pre>
</td>
<td>
<pre>{str(k): json_value(v) for k, v in value.items()}</pre>
<pre>[json_value(v) for v in value]</pre>
<pre>float(value) if np.isfinite(value) else None</pre>
<pre>None</pre>
<pre>str(value)</pre>
<pre>value</pre>
</td>
<td>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>json_value</code>
<br>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>write_json</code>
</td>
</tr>
<tr>
<td>
<code>write_json</code>
</td>
<td>
حفظ قاموس قابل للتسلسل في ملف نتائج.
</td>
<td>
<pre>write_json(path, payload)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>run_case</code>
<br>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>xml_rows</code>
</td>
<td>
قراءة صفوف التصدير وتحديد الحاجة لإصلاح الصيغة.
</td>
<td>
<pre>xml_rows(path)</pre>
</td>
<td>
<pre>(pd.DataFrame(records), repaired)</pre>
</td>
<td>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>run_case</code>
</td>
</tr>
<tr>
<td>
<code>source_candidates</code>
</td>
<td>
استخراج أعمدة المرشحين من المصدر المحلي.
</td>
<td>
<pre>source_candidates(raw)</pre>
</td>
<td>
<pre>(rows[columns].copy(), rows)</pre>
</td>
<td>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>run_case</code>
</td>
</tr>
<tr>
<td>
<code>one_id</code>
</td>
<td>
اشتراط معرف وحيد في بيانات الحالة.
</td>
<td>
<pre>one_id(rows, name)</pre>
</td>
<td>
<pre>values[0]</pre>
</td>
<td>
لا نداء رمز مباشر محسوم في الفهرس؛ قد يكون واجهة عامة أو نداء كائن أو موضع اختبار.
</td>
</tr>
<tr>
<td>
<code>actual_metrics</code>
</td>
<td>
حساب معدلات المصدر ومقارنة صيغها بالنتائج المرصودة.
</td>
<td>
<pre>actual_metrics(status_row, actual)</pre>
</td>
<td>
<pre>{'actual_source_semester_gpa': semester_gpa, 'actual_source_semester_courses': int(status_row.semester_reg_courses), 'actual_source_semester_credits': semester_reg, 'actual_source_prior_credits': total_reg, 'actual_source_start_cumulative_gpa': start_gpa, 'actual_cumulative_gpa_formula': calculated, 'actual_published_end_cumulative_gpa': float(status_row.end_agpa_points), 'actual_formula_minus_published': calculated - float(status_row.end_agpa_points) if calculated is not None else None, 'actual_cleaned_course_count': int(len(actual)), 'actual_cleaned_credits': float(credits[valid].sum()), 'actual_cleaned_plan_gpa': cleaned_gpa, 'actual_cleaned_failed_credits': float(credits[valid &amp; points.lt(2)].sum())}</pre>
</td>
<td>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>run_case</code>
</td>
</tr>
<tr>
<td>
<code>observed_plan_estimate</code>
</td>
<td>
توقع الخطة المسجلة فعليًا للمقارنة المحلية.
</td>
<td>
<pre>observed_plan_estimate(engine, snapshot, actual, catalog, history, student_id, degree_id, target_part, *, allow_older_history=False)</pre>
</td>
<td>
<pre>{'status': 'no_cleaned_actual_courses'}</pre>
<pre>{'status': 'ok', **summary, 'courses': courses}</pre>
<pre>{'status': 'unavailable', 'reason': str(error)}</pre>
</td>
<td>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>run_case</code>
</td>
</tr>
<tr>
<td>
<code>course_overlap</code>
</td>
<td>
قياس تقاطع مواد التوصية مع مواد مسجلة.
</td>
<td>
<pre>course_overlap(recommendation, actual_ids)</pre>
</td>
<td>
<pre>{'recommended_course_count': len(recommended_ids), 'shared_actual_course_ids': shared, 'shared_actual_course_count': len(shared), 'jaccard_with_actual': len(shared) / len(union) if union else None}</pre>
</td>
<td>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>report_markdown</code>
<br>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>run_case</code>
</td>
</tr>
<tr>
<td>
<code>markdown_number</code>
</td>
<td>
عرض رقم أو علامة فقدان في التقرير.
</td>
<td>
<pre>markdown_number(value, digits=3)</pre>
</td>
<td>
<pre>'—' if value is None or (isinstance(value, float) and (not np.isfinite(value))) else f'{float(value):.{digits}f}'</pre>
</td>
<td>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>course_text</code>
<br>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>report_markdown</code>
</td>
</tr>
<tr>
<td>
<code>course_text</code>
</td>
<td>
عرض قائمة مواد الخطة في النص.
</td>
<td>
<pre>course_text(courses)</pre>
</td>
<td>
نص يجمع معرفات المواد وساعاتها، مع فاصلة عربية ورمز ساعات عربي.
</td>
<td>
لا نداء رمز مباشر محسوم في الفهرس؛ قد يكون واجهة عامة أو نداء كائن أو موضع اختبار.
</td>
</tr>
<tr>
<td>
<code>report_markdown</code>
</td>
<td>
صياغة تقرير مقارنة التوصيات والحالات.
</td>
<td>
<pre>report_markdown(cases, args, run_dir)</pre>
</td>
<td>
<pre>'\n'.join(lines)</pre>
</td>
<td>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>run_case</code>
</td>
<td>
تنفيذ حالة تصدير محلية ونتائجها المقارنة.
</td>
<td>
<pre>run_case(path, engine, status, history, diplomas, catalog, args, run_dir)</pre>
</td>
<td>
<pre>payload</pre>
</td>
<td>
<a href="evaluate_xml_recommendations.md">صفحة المستدعي</a>
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
parse_args
```

يقرأ ملفات التصدير ويختار هوية الطلب، يطبّع المرشحين ويشغّل المحرك المحلي ويقارن مع نتائج مسجلة؛ يحفظ حالات الفشل بصورة منفصلة.

## ٦. كيف تتغير البيانات؟

التحول الرئيسي هو من المدخل الموصوف إلى المخرج الموصوف عبر الخطوات أعلاه. لم تتوفر عينة مستقلة موثقة تصلح لعرض قيم أكاديمية كاملة لهذا الملف؛ لذلك لا تُختلق بيانات جامعة أو درجات مودل.

## ٧. القواعد والافتراضات

يقرأ ملفات التصدير ويختار هوية الطلب، يطبّع المرشحين ويشغّل المحرك المحلي ويقارن مع نتائج مسجلة؛ يحفظ حالات الفشل بصورة منفصلة.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

بعض حسابات المقارنة تفترض توقيت إجمالي التسجيل الأصلي؛ لا تستعمل كدليل مقام جامعي عام أو كعينة بيانات شخصية.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [أدوات تنظيف الأعمدة والمعرفات](../data/cleaning_utils.md)
- [قراءة تصدير الجداول وإصلاح النص مؤقتًا](../data/xml_spreadsheet.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [تصدير واجهات نواة التوصية](../recommendation/__init__.md)
- [عقود النواة والمدخلات المحلية](../recommendation/inputs.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
__future__
argparse
numpy
pandas
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_recommendation_inputs_v2.py)

```text
tests/test_recommendation_inputs_v2.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_local_loader_reads_only_cleaned_v2_and_preserves_history
test_local_missing_v2_fails_without_legacy_fallback
test_local_supplied_snapshot_reads_only_v2_catalog_and_attempts
```

[ملف اختبار مرتبط](../../../tests/test_xml_package.py)

```text
tests/test_xml_package.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_xml_converter_and_evaluator_keep_parsing_behavior
```

## ١١. القيود المعروفة

هذا تقييم بأداة محلية سابقة؛ ليس غلاف خدمة الشبكة ولا إثبات جودة سياسة مرحلتين.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يقارن توصيات محلية بمواد مسجلة في أمثلة تصدير ويكتب تقارير أثر.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: هذا تقييم بأداة محلية سابقة؛ ليس غلاف خدمة الشبكة ولا إثبات جودة سياسة مرحلتين.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
