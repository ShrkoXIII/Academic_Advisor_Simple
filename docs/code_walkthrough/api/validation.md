# أدوات الهوية والأرقام والتشخيص الآمن

```text
src/api/validation.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يوحّد التحقق الصغير المشترك حتى لا تختلف حدود الطالب والمواد والتاريخ في تفسير الهوية أو الأعداد أو مصادر القيم.

الدور في الخريطة:
واجهة وتشغيل

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [إنشاء تطبيق الواجهات والمصادقة](app.md)
- [الجلب المباشر الاختياري للاختبار](backend_client.md)
- [تطبيع المواد والأهلية والقيود](courses_adapter.md)
- [المعاينة التشخيصية لدفعة التاريخ](history_adapter.md)
- [تنسيق التحقق والتوصية والإدارة](service.md)
- [تحويل الطالب إلى لقطة بداية الفصل](student_adapter.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [مرجع المسارات والإصدارات](../paths.md)

## ٣. المدخلات

قيم منفردة ومعرفات وفصول وأغلفة ردود وسياقات جلب. المدخل غير الموثوق قد يحمل قيمًا فارغة أو نوعًا غير مقبول.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

قيم مطبّعة أو استثناء آمن برمز ثابت، وكائن نتيجة تحقق يتحول إلى بنية صالحة للإرسال.

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
<code>ApiError</code>
</td>
<td>
استثناء عام برمز ومعلومات آمنة وحالة نقل.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="app.md">صفحة المستدعي</a>
<br>
<code>DecimalRoute.get_route_handler</code>
<br>
<a href="app.md">صفحة المستدعي</a>
<br>
<code>create_app</code>
<br>
<a href="backend_client.md">صفحة المستدعي</a>
<br>
<code>BackendClient._address</code>
<br>
<a href="backend_client.md">صفحة المستدعي</a>
<br>
<code>BackendClient._exchange</code>
<br>
<a href="backend_client.md">صفحة المستدعي</a>
<br>
<code>BackendClient._get</code>
</td>
</tr>
<tr>
<td>
<code>identifier</code>
</td>
<td>
تطبيع معرف نصي مع رفض القيم غير المقبولة.
</td>
<td>
<pre>identifier(value, field)</pre>
</td>
<td>
<pre>value.strip()</pre>
</td>
<td>
<a href="backend_client.md">صفحة المستدعي</a>
<br>
<code>BackendClient.fetch_inputs</code>
<br>
<a href="courses_adapter.md">صفحة المستدعي</a>
<br>
<code>_check_source_duplicates</code>
<br>
<a href="courses_adapter.md">صفحة المستدعي</a>
<br>
<code>_course</code>
<br>
<a href="history_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_history_delta</code>
<br>
<a href="service.md">صفحة المستدعي</a>
<br>
<code>ApiService._finalized_payload</code>
</td>
</tr>
<tr>
<td>
<code>number</code>
</td>
<td>
تحويل عدد عشري محدود وفحص الحدود والفقدان المسموح.
</td>
<td>
<pre>number(value, field, *, integer=False, nullable=False)</pre>
</td>
<td>
<pre>None</pre>
<pre>int(result) if integer else result</pre>
</td>
<td>
<a href="courses_adapter.md">صفحة المستدعي</a>
<br>
<code>_check_source_duplicates</code>
<br>
<a href="courses_adapter.md">صفحة المستدعي</a>
<br>
<code>_course</code>
<br>
<a href="courses_adapter.md">صفحة المستدعي</a>
<br>
<code>_rules</code>
<br>
<a href="service.md">صفحة المستدعي</a>
<br>
<code>ApiService.recommend</code>
<br>
<a href="student_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_student</code>
</td>
</tr>
<tr>
<td>
<code>part</code>
</td>
<td>
تحقق رقم فصل أكاديمي عبر الرزنامة.
</td>
<td>
<pre>part(value, field='part_id')</pre>
</td>
<td>
<pre>academic_part(result)</pre>
</td>
<td>
<a href="backend_client.md">صفحة المستدعي</a>
<br>
<code>BackendClient.fetch_inputs</code>
<br>
<a href="courses_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_courses</code>
<br>
<a href="courses_adapter.md">صفحة المستدعي</a>
<br>
<code>_course</code>
<br>
<a href="history_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_history_delta</code>
<br>
<a href="service.md">صفحة المستدعي</a>
<br>
<code>ApiService._finalized_payload</code>
</td>
</tr>
<tr>
<td>
<code>response_data</code>
</td>
<td>
فك غلاف الرد الجامعي المتحقق.
</td>
<td>
<pre>response_data(payload, component)</pre>
</td>
<td>
<pre>payload['data']</pre>
</td>
<td>
<a href="courses_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_courses</code>
<br>
<a href="student_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_student</code>
</td>
</tr>
<tr>
<td>
<code>identity</code>
</td>
<td>
جمع هوية الطلب المعيارية.
</td>
<td>
<pre>identity(request)</pre>
</td>
<td>
<pre>{'student_id': identifier(request.get('student_id'), 'student_id'), 'degree_id': identifier(request.get('degree_id'), 'degree_id'), 'part_id': part(request.get('part_id'))}</pre>
</td>
<td>
<a href="validation.md">صفحة المستدعي</a>
<br>
<code>binding</code>
</td>
</tr>
<tr>
<td>
<code>check_record_identity</code>
</td>
<td>
مقارنة الهوية الموجودة في السجل بالطلب.
</td>
<td>
<pre>check_record_identity(record, expected, *, historical=False, required=False)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="courses_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_courses</code>
<br>
<a href="student_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_student</code>
<br>
<a href="student_adapter.md">صفحة المستدعي</a>
<br>
<code>_history</code>
<br>
<a href="validation.md">صفحة المستدعي</a>
<br>
<code>binding</code>
</td>
</tr>
<tr>
<td>
<code>binding</code>
</td>
<td>
إلزام سياق الجلب ومطابقته وتحديد مستوى إثبات الهوية.
</td>
<td>
<pre>binding(request, component)</pre>
</td>
<td>
<pre>expected</pre>
</td>
<td>
<a href="courses_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_courses</code>
<br>
<a href="student_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_student</code>
</td>
</tr>
<tr>
<td>
<code>sourced</code>
</td>
<td>
تحقق شهادة مصدر القيمة وحدها الزمني.
</td>
<td>
<pre>sourced(record, target_part, field)</pre>
</td>
<td>
<pre>record['value']</pre>
</td>
<td>
<a href="courses_adapter.md">صفحة المستدعي</a>
<br>
<code>_course</code>
<br>
<a href="student_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_student</code>
</td>
</tr>
<tr>
<td>
<code>ValidationResult</code>
</td>
<td>
تجميع الأخطاء والفحوص والنواقص والمخرجات العامة.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="courses_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_courses</code>
<br>
<a href="history_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_history_delta</code>
<br>
<a href="student_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_student</code>
</td>
</tr>
<tr>
<td>
<code>json_safe</code>
</td>
<td>
تحويل القيم للرد دون قيم عددية غير محدودة.
</td>
<td>
<pre>json_safe(value)</pre>
</td>
<td>
<pre>format(value, 'f')</pre>
<pre>{key: json_safe(item) for key, item in value.items()}</pre>
<pre>[json_safe(item) for item in value]</pre>
<pre>value</pre>
</td>
<td>
<a href="app.md">صفحة المستدعي</a>
<br>
<code>create_app</code>
<br>
<a href="validation.md">صفحة المستدعي</a>
<br>
<code>json_safe</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
identifier / number / part
```

يفحص النوع والحدود قبل تحويل المعرف أو العدد أو الفصل.

خطوة 2:

```text
response_data / identity / check_record_identity
```

يفك الغلاف ويجمع الهوية ويفحص أي هوية موجودة في المحتوى.

خطوة 3:

```text
binding
```

يشترط سياق الجلب المستقل ويربطه بالطلب؛ يحدد مستوى إثبات الهوية.

خطوة 4:

```text
sourced
```

يراجع شهادة القيمة وحدها الزمني.

خطوة 5:

```text
ValidationResult / json_safe
```

يجمع الفحوص والنواقص ثم يحول القيم العددية والمفقودة إلى شكل قابل للإرسال.

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
<code>ApiError.__init__</code>
</td>
<td>
<pre>__init__(self, code, message, *, field=None, component='input', status_code=422, details=None)</pre>
</td>
<td>
يحفظ التبعيات أو الحقول ويطبق فحوص البناء الموجودة؛ لا تفترض تحميل أصول ما لم يذكر مسار التهيئة ذلك.
</td>
</tr>
<tr>
<td>
<code>ValidationResult.status</code>
</td>
<td>
<pre>status(self)</pre>
</td>
<td>
يحدد غير صالح عند الأخطاء، وجزئي عند نقص الفحوص، وصالح عند اكتمالها.
</td>
</tr>
<tr>
<td>
<code>ValidationResult.add</code>
</td>
<td>
<pre>add(self, error)</pre>
</td>
<td>
يسجل خطأ تحقق داخل النتيجة.
</td>
</tr>
<tr>
<td>
<code>ValidationResult.public</code>
</td>
<td>
<pre>public(self)</pre>
</td>
<td>
يعيد التشخيص المنقح دون الحمولة المطبعة الخاصة.
</td>
</tr>
</tbody>
</table>

## ٦. كيف تتغير البيانات؟

المعرف العددي النصي يظل نصًا بعد إزالة فراغاته، والعدد غير المحدود يرفض.

## ٧. القواعد والافتراضات

القيمة المنطقية ليست رقمًا أكاديميًا. المعرف يبقى نصًا. غياب السياق لا يصبح موافقة ضمنية.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

تمرير قيمة غير محدودة إلى الأصول أو الرد قد يخفي خطأ حسابيًا. تحويل المعرف إلى عدد قد يغير تمثيله.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [مرجع المسارات والإصدارات](../paths.md)
## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_api_backend_client.py)

```text
tests/test_api_backend_client.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_php_push_remains_default_and_pull_requires_explicit_configuration
test_environment_urls_timeout_and_courses_parameters
test_unsafe_endpoint_configuration_is_rejected
```

[ملف اختبار مرتبط](../../../tests/test_api_cumulative_integration.py)

```text
tests/test_api_cumulative_integration.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_http_migration_manual_auto_rollback_and_existing_pareto_contract
test_missing_artifacts_block_migration_but_http_validation_remains_available
test_corrupt_active_pointer_preserves_independent_diagnostics
```

[ملف اختبار مرتبط](../../../tests/test_api_integration.py)

```text
tests/test_api_integration.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_api_calls_actual_core_with_33_and_47_features_and_group_caps
test_original_gpa_calculation_and_helper_are_identical_on_full_schema
test_all_history_identity_rows_checked_even_when_first_schema_incomplete
```

## ١١. القيود المعروفة

هذه الفحوص تثبت اتساقًا وبنية؛ لا تثبت صلاحية المستخدم لدى الجامعة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يوحّد التحقق الصغير المشترك حتى لا تختلف حدود الطالب والمواد والتاريخ في تفسير الهوية أو الأعداد أو مصادر القيم.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: هذه الفحوص تثبت اتساقًا وبنية؛ لا تثبت صلاحية المستخدم لدى الجامعة.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
