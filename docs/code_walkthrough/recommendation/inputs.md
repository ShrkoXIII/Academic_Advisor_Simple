# عقود النواة والمدخلات المحلية

```text
src/recommendation/inputs.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يفصل قراءة الملفات المحلية وتطبيع أغلفة النواة عن نقل الواجهات، ويوحّد فحص اللقطة والمرشحين والسياسات.

الدور في الخريطة:
نواة التوصية

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تحويل الطالب إلى لقطة بداية الفصل](../api/student_adapter.md)
- [تقييم توصيات ملفات التصدير](../evaluation/evaluate_xml_recommendations.md)
- [حساب البحث على ميزات المادة فقط](../experiments/course_only_core.md)
- [مقارنة تجربة المادة بالمحرك المحلي](../experiments/course_only_evaluation.md)
- [تصدير واجهات نواة التوصية](__init__.md)
- [قياس المحرك المحلي](benchmark.md)
- [المحرك المحلي ذو الزوج الواحد](engine.md)
- [أداة التوصية المحلية](local_cli.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [رزنامة الفصول والفجوات](../data/academic_calendar.md)
- [أدوات تنظيف الأعمدة والمعرفات](../data/cleaning_utils.md)
- [هندسة الميزات الزمنية المشتركة](../features/temporal_features.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [القيود الأكاديمية على الخطط](constraints.md)
- [توحيد الحالة السابقة ومجموعة المادة](course_status.md)

## ٣. المدخلات

ملفات مرشحين أو جداول محلية، أو غلاف نواة بلقطة ومرشحين وغلاف طلب.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

أسماء الحقول المعرّفة في الملف:

```text
STUDENT_SNAPSHOT_COLUMNS
student_id
degree_id
faculty_id
grade_version_id
gpa_prev_1
gpa_prev_2
gpa_trend_delta
gpa_trend_missing
start_agpa_points
start_total_in_courses
start_total_in_credits
prior_total_reg_courses
prior_total_reg_credits
prior_total_fail_courses
prior_total_fail_credits
prior_fail_credit_ratio
prior_registered_semesters
observed_gap_semesters
diploma_gpa
diploma_type_id
degree_credits_count
```

أسماء الحقول المعرّفة في الملف:

```text
CANDIDATE_COURSE_COLUMNS
course_id
course_credits
attempt_number
plan_course_type_id
plan_requirement_type_id
plan_year_order
plan_semester_order
plan_credits_count
```

## ٤. المخرجات

مرشحون ولقطة وتقرير استيراد، أو بنية مدخلات مجهزة بقيود معيارية.

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
<code>CandidateImportError</code>
</td>
<td>
خطأ استيراد يحمل تقرير تفاصيل الاستيراد المحلي.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_candidates</code>
</td>
</tr>
<tr>
<td>
<code>read_candidate_file</code>
</td>
<td>
قراءة ملف مواد سجلي أو عمودي محلي.
</td>
<td>
<pre>read_candidate_file(path)</pre>
</td>
<td>
<pre>pd.read_parquet(path)</pre>
<pre>pd.DataFrame(data) if data else pd.DataFrame(columns=['course_id', 'course_credits'])</pre>
</td>
<td>
<a href="../experiments/course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>select_batch_cases</code>
<br>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>load_local_inputs</code>
</td>
</tr>
<tr>
<td>
<code>normalize_candidates</code>
</td>
<td>
تطبيع المرشحين المحليين وربطهم بالكتالوج والتاريخ السابق.
</td>
<td>
<pre>normalize_candidates(raw, catalog, course_history, student_id, degree_id, part_id)</pre>
</td>
<td>
<pre>(rows.sort_values('course_id', kind='stable').reset_index(drop=True), report)</pre>
</td>
<td>
<a href="../experiments/course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>select_batch_cases</code>
<br>
<a href="../evaluation/evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>observed_plan_estimate</code>
<br>
<a href="../evaluation/evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>run_case</code>
<br>
<a href="benchmark.md">صفحة المستدعي</a>
<br>
<code>benchmark</code>
<br>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>load_local_inputs</code>
</td>
</tr>
<tr>
<td>
<code>build_student_snapshot</code>
</td>
<td>
لقطة محلية من حالة الهدف والدبلوم والكلية التاريخية.
</td>
<td>
<pre>build_student_snapshot(status, course_history, diplomas, student_id, degree_id, part_id)</pre>
</td>
<td>
<pre>{c: snapshot[c] for c in [*STUDENT_SNAPSHOT_COLUMNS, 'part_id']}</pre>
</td>
<td>
<a href="../experiments/course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>select_batch_cases</code>
<br>
<a href="../evaluation/evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>run_case</code>
<br>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>load_local_inputs</code>
</td>
</tr>
<tr>
<td>
<code>validate_snapshot</code>
</td>
<td>
فحص أعمدة وهوية اللقطة المحلية.
</td>
<td>
<pre>validate_snapshot(snapshot, student_id, degree_id, part_id)</pre>
</td>
<td>
<pre>{c: snapshot[c] for c in [*required, *optional]}</pre>
</td>
<td>
<a href="../experiments/course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>select_batch_cases</code>
<br>
<a href="../evaluation/evaluate_xml_recommendations.md">صفحة المستدعي</a>
<br>
<code>run_case</code>
<br>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>load_local_inputs</code>
</td>
</tr>
<tr>
<td>
<code>load_local_inputs</code>
</td>
<td>
قراءة وتجهيز المرشحين واللقطة والتقرير المحلي.
</td>
<td>
<pre>load_local_inputs(candidate_path, student_id, degree_id, part_id, snapshot_path=None)</pre>
</td>
<td>
<pre>(candidates, validate_snapshot(snapshot, student_id, degree_id, part_id), report)</pre>
</td>
<td>
<a href="../experiments/course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>run_comparisons</code>
<br>
<a href="../recommendation_experiments/previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
<br>
<a href="local_cli.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>PreparedRecommendationInputs</code>
</td>
<td>
اللقطة والمرشحون والقيود وبيانات الطلب المعيارية.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>prepare_recommendation_payloads</code>
</td>
</tr>
<tr>
<td>
<code>_payload_id</code>
</td>
<td>
تطبيع معرف غلاف النواة.
</td>
<td>
<pre>_payload_id(value, name)</pre>
</td>
<td>
<pre>str(result)</pre>
</td>
<td>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>_validate_payload_identity</code>
<br>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_student_payload</code>
<br>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_candidate_payloads</code>
<br>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_request_payload</code>
</td>
</tr>
<tr>
<td>
<code>_payload_number</code>
</td>
<td>
تحقق أرقام غلاف النواة مع الفقدان المدعوم فقط.
</td>
<td>
<pre>_payload_number(value, name, *, nullable=False, nonnegative=False)</pre>
</td>
<td>
<pre>float('nan')</pre>
<pre>number</pre>
</td>
<td>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>_payload_part</code>
<br>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_student_payload</code>
<br>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_candidate_payloads</code>
<br>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_request_payload</code>
</td>
</tr>
<tr>
<td>
<code>_payload_part</code>
</td>
<td>
فحص الفصل الخماسي في غلاف النواة.
</td>
<td>
<pre>_payload_part(value)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>_validate_payload_identity</code>
<br>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_request_payload</code>
</td>
</tr>
<tr>
<td>
<code>_validate_payload_identity</code>
</td>
<td>
ربط هوية الغلاف بالطلب.
</td>
<td>
<pre>_validate_payload_identity(record, student_id, degree_id, part_id, *, required)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_student_payload</code>
<br>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_candidate_payloads</code>
</td>
</tr>
<tr>
<td>
<code>normalize_student_payload</code>
</td>
<td>
إنشاء لقطة نواة مع أنواع وقيم موثقة.
</td>
<td>
<pre>normalize_student_payload(snapshot, *, student_id, degree_id, part_id)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>prepare_recommendation_payloads</code>
</td>
</tr>
<tr>
<td>
<code>_explicitly_ineligible</code>
</td>
<td>
تمييز راية عدم الأهلية الصريحة والتحقق من رمزها.
</td>
<td>
<pre>_explicitly_ineligible(record)</pre>
</td>
<td>
<pre>rejected</pre>
</td>
<td>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>normalize_candidate_payloads</code>
</td>
</tr>
<tr>
<td>
<code>normalize_candidate_payloads</code>
</td>
<td>
فحص مرشحين جاهزين وهوية وميزات وحالة قبل التوقع.
</td>
<td>
<pre>normalize_candidate_payloads(records, snapshot)</pre>
</td>
<td>
<pre>rows.sort_values('course_id', kind='stable').reset_index(drop=True)</pre>
</td>
<td>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>prepare_recommendation_payloads</code>
</td>
</tr>
<tr>
<td>
<code>normalize_request_payload</code>
</td>
<td>
فحص الطلب وإنشاء قيوده وهدفه الأعلى الدقيق.
</td>
<td>
<pre>normalize_request_payload(request)</pre>
</td>
<td>
<pre>(identity, constraints, metadata)</pre>
</td>
<td>
<a href="inputs.md">صفحة المستدعي</a>
<br>
<code>prepare_recommendation_payloads</code>
</td>
</tr>
<tr>
<td>
<code>prepare_recommendation_payloads</code>
</td>
<td>
تجميع مدخل النواة والتحقق من اكتمال سياسات المرشحين.
</td>
<td>
<pre>prepare_recommendation_payloads(*, student_payload, request_payload)</pre>
</td>
<td>
<pre>PreparedRecommendationInputs(snapshot, candidates, constraints, metadata)</pre>
</td>
<td>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender.recommend_from_payloads</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
CandidateImportError.__init__
```

المسار المحلي يربط الكتالوج والتاريخ السابق والدبلوم وحالة الهدف. مسار النواة يقبل بيانات مطبّعة جاهزة، يفحص الهوية والأرقام والحالة والسقوف ثم يعيد بنية مجهزة.

### طرق الأصناف الموجودة

قائمة الطرق الموجودة، دون افتراض أن ترتيب تعريفها هو ترتيب التنفيذ.

<table>
<thead>
<tr>
<th>
الطريقة
</th>
<th>
التوقيع
</th>
<th>
وظيفتها
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>CandidateImportError.__init__</code>
</td>
<td>
<pre>__init__(self, report)</pre>
</td>
<td>
يحفظ التبعيات أو الحقول ويطبق فحوص البناء الموجودة؛ لا تفترض تحميل أصول ما لم يذكر مسار التهيئة ذلك.
</td>
</tr>
</tbody>
</table>

## ٦. كيف تتغير البيانات؟

التحول الرئيسي هو من المدخل الموصوف إلى المخرج الموصوف عبر الخطوات أعلاه. لم تتوفر عينة مستقلة موثقة تصلح لعرض قيم أكاديمية كاملة لهذا الملف؛ لذلك لا تُختلق بيانات جامعة أو درجات مودل.

## ٧. القواعد والافتراضات

المسار المحلي يربط الكتالوج والتاريخ السابق والدبلوم وحالة الهدف. مسار النواة يقبل بيانات مطبّعة جاهزة، يفحص الهوية والأرقام والحالة والسقوف ثم يعيد بنية مجهزة.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

المسار المحلي لا يعوّض شهادات الجامعة الحالية؛ عداد المحاولات فيه مشتق من السجل السابق المرصود.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [رزنامة الفصول والفجوات](../data/academic_calendar.md)
- [أدوات تنظيف الأعمدة والمعرفات](../data/cleaning_utils.md)
- [هندسة الميزات الزمنية المشتركة](../features/temporal_features.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [القيود الأكاديمية على الخطط](constraints.md)
- [توحيد الحالة السابقة ومجموعة المادة](course_status.md)
- [البحث عن مجموعات بالساعات الدقيقة](plan_generation.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
```


مراجع خارج شجرة المصدر تستورد هذه الوحدة؛ ليست دليل تشغيل إنتاج:
[الأداة المرجعية](../../../scripts/benchmark_two_stage.py)

```text
scripts/benchmark_two_stage.py
```

[الأداة المرجعية](../../../scripts/evaluate_corrected_phase6.py)

```text
scripts/evaluate_corrected_phase6.py
```

[الأداة المرجعية](../../../scripts/experiments/attempt_number_recommendation.py)

```text
scripts/experiments/attempt_number_recommendation.py
```

[الأداة المرجعية](../../../debugging/explain_recommendation.py)

```text
debugging/explain_recommendation.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_local_recommendation.py)

```text
tests/test_local_recommendation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_json_and_parquet_same_and_empty_list
test_missing_gpa_and_mismatched_snapshot_are_rejected
test_snapshot_ignores_current_future_outcomes
```

[ملف اختبار مرتبط](../../../tests/test_projected_recommendation.py)

```text
tests/test_projected_recommendation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_snapshot_preserves_serving_only_denominator_and_history_validation
```

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

[ملف اختبار مرتبط](../../../tests/test_two_stage_benchmark.py)

```text
tests/test_two_stage_benchmark.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_small_search_matches_independent_subsets
```

## ١١. القيود المعروفة

ليس محولًا للرد الجامعي الخام؛ المحولان العامان يسبقان أغلفة النواة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يفصل قراءة الملفات المحلية وتطبيع أغلفة النواة عن نقل الواجهات، ويوحّد فحص اللقطة والمرشحين والسياسات.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: ليس محولًا للرد الجامعي الخام؛ المحولان العامان يسبقان أغلفة النواة.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
