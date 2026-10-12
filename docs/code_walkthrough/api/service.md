# تنسيق التحقق والتوصية والإدارة

```text
src/api/service.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يجمع النقل والمحولات والأصول والمحرك من دون نقل التدريب إلى الواجهة. هو المكان الذي يقرر هل الطلب صالح ومكتمل وجاهز قبل أول توقع.

الدور في الخريطة:
واجهة وتشغيل

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [إنشاء تطبيق الواجهات والمصادقة](app.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [تطبيع المواد والأهلية والقيود](courses_adapter.md)
- [المعاينة التشخيصية لدفعة التاريخ](history_adapter.md)
- [الإعدادات ومصادرها البيئية](settings.md)
- [تحويل الطالب إلى لقطة بداية الفصل](student_adapter.md)
- [أدوات الهوية والأرقام والتشخيص الآمن](validation.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [تحويل العلامة إلى نقاط وفق النسخة](../grade_scale.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [الإدارة الدائمة للتاريخ التراكمي](../recommendation/cumulative_history.md)
- [مجاميع الدفعات ومدير اللقطة](../recommendation/history_update.md)
- [البحث عن مجموعات بالساعات الدقيقة](../recommendation/plan_generation.md)
- [التحقق من اعتماد سياسة الترتيب](../recommendation/ranking_policy.md)

## ٣. المدخلات

إعداد الخدمة، وتبعيات محقونة أو محمّلة: الكتالوج وسلم العلامات ومدير التاريخ والمحرك. الطلبات العامة قواميس ناتجة عن المخططات.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

الأنواع والبنى المستعملة في هذا الحد:

```text
request: dict
catalog: pandas.DataFrame | None
engine: TwoStagePlanRecommender | None
history_manager: FrozenHistoryManager | None
```

## ٤. المخرجات

نتائج تشخيص مستقلة، وحالة جاهزية مفصّلة، أو استجابة توصية منقّحة. عمليات الإدارة تعيد حالة المخزن وبصمات النسخ دون الصفوف الخاصة.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

أنواع المخرجات الأساسية:

```text
validate_* -> ValidationResult
recommend -> dict
health -> dict
history operations -> dict
```

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
<code>ApiService</code>
</td>
<td>
تنسيق التبعيات والتحقق والتوصية والإدارة المنقحة.
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
<code>create_app</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
ApiService.__init__ / initialize
```

يبني مخزن الإدارة ويهيئ الكتالوج والسلم والتاريخ والأصول بصورة مستقلة؛ الفشل يبقى معلومة جاهزية.

خطوة 2:

```text
health
```

يفصل صحة النقل عن جاهزية المودلات والتاريخ والكتالوج؛ تحديث المؤشر الدائم قد يغيّر جاهزية التاريخ.

خطوة 3:

```text
validate_student / validate_courses / validate_delta
```

يشغّل محولات القراءة والتشخيص دون اشتراط تحميل المودلات.

خطوة 4:

```text
recommend
```

يبدأ بالهوية والتحويل، يراجع وضع الزمن وحد الاختبار والأصول وقطع التدريب والنواقص، ثم يصنع مدخل النواة.

خطوة 5:

```text
TwoStagePlanRecommender.recommend_from_payloads
```

يمرر قطعًا تاريخيًا صريحًا والعدد المطلوب تحت قفل التوقع؛ المجال يُختزل إلى الحد الأعلى الفعلي هدفًا دقيقًا.

خطوة 6:

```text
_history_operation / _refresh_history_manager
```

يسلسل الإدارة مع التوقع المحلي، ثم يعيد ربط المدير بمؤشر المخزن الدائم. الرد العام يستعمل قائمة بيانات مسموح بها.

### الحدود قبل أول توقع

تسلسل القرار داخل التوصية مهم: التحويل والهوية أولًا، ثم تحديث المرجع التاريخي وفحص وضع القطع وحد اختبار الأداء، ثم الجاهزية والنواقص وقطع التدريب ووجود النسخة الدقيقة، ثم ساعات الطلب والسياسات وقفل التوقع.

التحقق الجزئي لا يعني دائمًا منع التوصية؛ قيمة عددية يقبل العقد فقدانها تبقى مفقودة مع بيانها في الرد. لكن مقام المعدل أو مخطط تاريخ الطالب اللازم أو الفجوات غير القابلة للاشتقاق يمنع الطلب.

في مجال ساعات صحيح ومتقاطع مع قواعد الجامعة، الحد الأعلى الفعلي يصبح هدفًا دقيقًا. لا تجربة تلقائية لهدف أقل عند غياب خطة.

```text
requested range -> intersect confirmed range -> effective upper bound -> exact target
```

حالة النقل السليمة لا تساوي جاهزية توصية. الإدارة والتوقع متسلسلان في عامل الخدمة، بينما المخزن يضيف قفل نظام ملفات للتحديثات بين العمليات.

### طرق الأصناف الموجودة

هذه الطرق جزء من السلوك الأساسي؛ الترتيب أعلاه يبين ما يستدعى منها في المسار الفعلي.

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
<code>ApiService.__init__</code>
</td>
<td>
<pre>__init__(self, *, settings=None, catalog=None, grade_scale=None, history_manager=None, engine=None, history_store=None)</pre>
</td>
<td>
يحفظ التبعيات أو الحقول ويطبق فحوص البناء الموجودة؛ لا تفترض تحميل أصول ما لم يذكر مسار التهيئة ذلك.
</td>
</tr>
<tr>
<td>
<code>ApiService._history_compatibility</code>
</td>
<td>
<pre>_history_compatibility(self, state, metadata)</pre>
</td>
<td>
يتحقق من سياسة وأصول الخدمة ومخطط التاريخ الأساسي.
</td>
</tr>
<tr>
<td>
<code>ApiService._load_history</code>
</td>
<td>
<pre>_load_history(self)</pre>
</td>
<td>
يختار المؤشر التراكمي المهيأ، وإلا مدير الحزم السابقة.
</td>
</tr>
<tr>
<td>
<code>ApiService._bind_history_manager</code>
</td>
<td>
<pre>_bind_history_manager(self, manager)</pre>
</td>
<td>
يحدّث مرجع التاريخ في الخدمة والمحرك أو ينشئ المحرك من الأصول المحملة.
</td>
</tr>
<tr>
<td>
<code>ApiService._refresh_history_manager</code>
</td>
<td>
<pre>_refresh_history_manager(self)</pre>
</td>
<td>
يتبنى مؤشر الإدارة الدائم للعمال ويعطل الجاهزية عند فساده.
</td>
</tr>
<tr>
<td>
<code>ApiService.initialize</code>
</td>
<td>
<pre>initialize(self, *, catalog_loader=None, grade_scale_loader=None, history_loader=None, model_loader=None)</pre>
</td>
<td>
يهيئ التبعيات بصورة مستقلة، أو يرحل أساس المخزن في صنف الإدارة حسب التوقيع.
</td>
</tr>
<tr>
<td>
<code>ApiService.health</code>
</td>
<td>
<pre>health(self)</pre>
</td>
<td>
يفصل صحة النقل عن جاهزية كل تبعية.
</td>
</tr>
<tr>
<td>
<code>ApiService.validate_student</code>
</td>
<td>
<pre>validate_student(self, request)</pre>
</td>
<td>
يفوض إلى محول الطالب دون انتظار المودلات.
</td>
</tr>
<tr>
<td>
<code>ApiService.validate_courses</code>
</td>
<td>
<pre>validate_courses(self, request)</pre>
</td>
<td>
يفوض إلى محول المواد بكتالوج اختياري.
</td>
</tr>
<tr>
<td>
<code>ApiService.validate_delta</code>
</td>
<td>
<pre>validate_delta(self, request)</pre>
</td>
<td>
يفوض إلى معاينة القراءة فقط مع مدير تاريخ إن توفر.
</td>
</tr>
<tr>
<td>
<code>ApiService.history_status</code>
</td>
<td>
<pre>history_status(self)</pre>
</td>
<td>
يعرض وضع ومؤشر ونسخ المخزن دون صفوف خاصة.
</td>
</tr>
<tr>
<td>
<code>ApiService._finalized_payload</code>
</td>
<td>
<pre>_finalized_payload(request, *, require_finalized=False)</pre>
</td>
<td>
يربط مرجع التثبيت بالفصل وينشئ غلاف الدفعة الداخلي.
</td>
</tr>
<tr>
<td>
<code>ApiService._history_operation</code>
</td>
<td>
<pre>_history_operation(self, operation, **kwargs)</pre>
</td>
<td>
يسلسل عملية الإدارة مع التوقع المحلي ويحوّل الأخطاء إلى رموز عامة.
</td>
</tr>
<tr>
<td>
<code>ApiService.set_history_mode</code>
</td>
<td>
<pre>set_history_mode(self, request)</pre>
</td>
<td>
يغير الإعداد الدائم عبر المخزن الإداري.
</td>
</tr>
<tr>
<td>
<code>ApiService.initialize_history</code>
</td>
<td>
<pre>initialize_history(self, request)</pre>
</td>
<td>
يرحل الأساس المحدد بإعداد الخدمة وتأكيد المشرف.
</td>
</tr>
<tr>
<td>
<code>ApiService.preview_history</code>
</td>
<td>
<pre>preview_history(self, request)</pre>
</td>
<td>
يحفظ معاينة إدارة وبصمة مرتبطة بالأساس.
</td>
</tr>
<tr>
<td>
<code>ApiService.commit_history</code>
</td>
<td>
<pre>commit_history(self, request)</pre>
</td>
<td>
ينشر دفعة مؤكدة دون تفعيلها.
</td>
</tr>
<tr>
<td>
<code>ApiService.activate_history</code>
</td>
<td>
<pre>activate_history(self, request)</pre>
</td>
<td>
يفعل النسخة المؤكدة ويعيد ربط مدير الخدمة.
</td>
</tr>
<tr>
<td>
<code>ApiService.finalize_history</code>
</td>
<td>
<pre>finalize_history(self, request)</pre>
</td>
<td>
يتعامل مع حدث موثوق في وضع التثبيت الآلي.
</td>
</tr>
<tr>
<td>
<code>ApiService.recommend</code>
</td>
<td>
<pre>recommend(self, request)</pre>
</td>
<td>
ينفذ التسلسل الموضح في هذه الصفحة ويعيد النتيجة.
</td>
</tr>
</tbody>
</table>

## ٦. كيف تتغير البيانات؟

عند غياب المودلات تستمر واجهتا التحقق وحالة النقل. محاولة توصية مكتملة في هذه الحالة تعيد عدم توفر الخدمة، قبل أي توقع.

## ٧. القواعد والافتراضات

لا اقتطاع صامت للمرشحين عند حد الأداء؛ الرفض كامل وفي وضع الاختبار فقط. التشغيل المعتاد يحتاج لقطة الفصل السابق بالضبط. الاختبار التاريخي يحتاج تفعيل الإعداد والوضع الصريح. التوصية لا تبدأ عند نقص المدخل اللازم.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

الجاهزية وحدها ليست فحص هوية. تبدل التاريخ أثناء الطلب يجب ألا يخلط الميزات. تسريب مصدر المودلات ومساراته أو معرف الطالب في البيانات العامة ممنوع بالقائمة المنقّحة.

أي قيمة أو قطع غير مطابق يجب أن يرفض أو يسجل غير متاح حسب العقد، قبل تحويله إلى توقع. لا تعالج هذه الصفحة نقص المصدر بتغيير ميزة أو وضع قيمة افتراضية.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [تطبيع المواد والأهلية والقيود](courses_adapter.md)
- [المعاينة التشخيصية لدفعة التاريخ](history_adapter.md)
- [الإعدادات ومصادرها البيئية](settings.md)
- [تحويل الطالب إلى لقطة بداية الفصل](student_adapter.md)
- [أدوات الهوية والأرقام والتشخيص الآمن](validation.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [تحويل العلامة إلى نقاط وفق النسخة](../grade_scale.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [الإدارة الدائمة للتاريخ التراكمي](../recommendation/cumulative_history.md)
- [مجاميع الدفعات ومدير اللقطة](../recommendation/history_update.md)
- [البحث عن مجموعات بالساعات الدقيقة](../recommendation/plan_generation.md)
- [التحقق من اعتماد سياسة الترتيب](../recommendation/ranking_policy.md)
- [تحميل أصول المرحلتين والتحقق من مصدرها](../recommendation/two_stage_artifacts.md)
- [المحرك المعتمد ذو المرحلتين](../recommendation/two_stage_engine.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
pandas
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_api_cumulative_integration.py)

```text
tests/test_api_cumulative_integration.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_worker_started_before_migration_adopts_shared_active_pointer
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert response.status_code == 200
```

[ملف اختبار مرتبط](../../../tests/test_api_history_admin.py)

```text
tests/test_api_history_admin.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_admin_status_and_durable_mode_workflow
test_service_credentials_cannot_access_administration
test_manual_preview_commit_and_activation_are_separate
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert response.status_code == 200
```

[ملف اختبار مرتبط](../../../tests/test_api_integration.py)

```text
tests/test_api_integration.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_all_history_identity_rows_checked_even_when_first_schema_incomplete
test_supplement_conflict_with_original_beginning_fail_total_is_rejected
test_nonregistered_semesters_preserve_gpa_and_current_gap
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert any((error['code'] == 'IDENTITY_MISMATCH' for error in ApiService().validate_student(request).errors))
```

[اختبار باستيراد ديناميكي](../../../tests/test_api_adapters.py)

```text
tests/test_api_adapters.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_complete_student_uses_previous_gpa_and_explicit_denominator
test_actual_sanitized_student_reports_missing_diploma_and_denominator
test_independent_source_bindings_reject_wrong_identity
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert result.errors == []
```

[اختبار باستيراد ديناميكي](../../../tests/test_api_http.py)

```text
tests/test_api_http.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_http_health_and_validators_survive_unready_models_and_history
test_http_context_conflicts_make_zero_engine_calls
test_missing_courses_context_and_payload_identity_conflict_stop_inference
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert health['api_health'] == 'healthy'
```

## ١١. القيود المعروفة

حد المرشحين والأداء والذاكرة للإنتاج لم يعتمد. اكتمال الطلب الحقيقي يعتمد على شهادات الجامعة وبيانات الدبلوم والتسجيل والسياسات.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- الخدمة تجمع التحقق وتثبيت التاريخ وتفويض المحرك.
- نقص تبعية تشغيل يمنع التوصية دون إيقاف تشخيص المدخل.
- الرد العام ينتقي البيانات الوصفية المسموح نشرها.

ثلاثة أسئلة للفهم:

1. أي فحص يجب أن يتوقف قبل أي استدعاء توقع؟
2. متى يطبق حد المواد الخاص باختبار الأداء؟
3. كيف تتغير جهة التاريخ بعد وجود نسخة تراكمية نشطة؟

تمرين قراءة آمن:

ارسم مسار طلب به تعارض هوية، ثم مسار طلب صحيح بلا مودل؛ حدد المرحلة الأخيرة الممكن بلوغها في كل منهما.

التمرين قراءة وحساب على الورق؛ لا يغير المشروع ولا يشغّل بناءً أو توقعًا أو تحديث تاريخ.
