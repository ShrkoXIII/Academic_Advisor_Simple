# إنشاء تطبيق الواجهات والمصادقة

```text
src/api/app.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

هذا هو حد النقل الشبكي: ينشئ التطبيق ومساراته ويضبط المصادقة والأخطاء، ثم يسلّم العمل إلى الخدمة. لا يقرر السياسة الأكاديمية ولا يجري توقعًا بنفسه.

الدور في الخريطة:
واجهة وتشغيل

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

لم يظهر مستورد داخلي مباشر ضمن جرد الوحدات؛ لا يكفي ذلك للحكم أنه غير مستعمل.

الوحدات التي يعتمد عليها بعد ذلك:

- [عقود أجسام الطلبات](schemas.md)
- [تنسيق التحقق والتوصية والإدارة](service.md)
- [الإعدادات ومصادرها البيئية](settings.md)
- [أدوات الهوية والأرقام والتشخيص الآمن](validation.md)

## ٣. المدخلات

طلبات تحتوي أغلفة الطالب والمواد أو إدارة التاريخ. يجري تحليل الأعداد العشرية بدقة قبل التحقق من مخطط الطلب. مفتاح المصادقة يأتي في ترويسة الطلب، لا في جسمه.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

الأنواع والبنى المستعملة في هذا الحد:

```text
settings: ApiSettings | None
service: ApiService | None
```

## ٤. المخرجات

تطبيق قابل للتشغيل عبر مصنع، واستجابات تحقق أو توصية أو إدارة. الأخطاء العامة تُحوّل إلى غلاف آمن؛ أخطاء مخطط الطلب لا تعيد القيم الأصلية أو السياق الخاص.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

أنواع المخرجات الأساسية:

```text
create_app(...) -> FastAPI
HTTP responses -> JSONResponse
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
<code>DecimalRequest</code>
</td>
<td>
تحليل جسم الطلب مع حفظ دقة الساعات.
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
</td>
</tr>
<tr>
<td>
<code>DecimalRoute</code>
</td>
<td>
تغليف مسار النقل وتحويل الاستثناء العام إلى خطأ آمن.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
لا نداء رمز مباشر محسوم في الفهرس؛ قد يكون واجهة عامة أو نداء كائن أو موضع اختبار.
</td>
</tr>
<tr>
<td>
<code>create_app</code>
</td>
<td>
إنشاء التطبيق والمسارات ودورة الحياة والمصادقة.
</td>
<td>
<pre>create_app(*, settings=None, service=None)</pre>
</td>
<td>
<pre>app</pre>
</td>
<td>
لا نداء رمز مباشر محسوم في الفهرس؛ قد يكون واجهة عامة أو نداء كائن أو موضع اختبار.
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
create_app
```

يختار الإعداد والخدمة المحقونة إن وجدت، وينشئ التطبيق. استيراد وحدة النقل نفسها يحتاج تبعيات الويب؛ استيراد الحزمة أو الخدمة لا يحتاجها.

خطوة 2:

```text
lifespan
```

عند بدء الخدمة يهيئ التبعيات في عامل منفصل؛ فشل تحميل المودلات لا يلغي صحة النقل.

خطوة 3:

```text
DecimalRequest.json
```

يحلل الجسم مرة واحدة ويحفظ الأعداد العشرية؛ يمنع القيم العددية غير المحدودة.

خطوة 4:

```text
DecimalRoute.get_route_handler
```

يلف التنفيذ ليحافظ على أسلوب الاستجابة الآمن عند الاستثناءات.

خطوة 5:

```text
authenticate
```

يقارن مفتاح الدور المطلوب مقارنة ثابتة الزمن؛ غياب المفتاح أو استعمال دور آخر يُرفض.

خطوة 6:

```text
ApiService
```

كل مسار يمرر بيانات المخطط المحولة إلى الخدمة؛ إدارة التثبيت لها مفتاح مستقل.

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
<code>DecimalRequest.json</code>
</td>
<td>
<pre>json(self)</pre>
</td>
<td>
يحلل الجسم مع دقة عشرية ويحفظ نتيجة التحليل.
</td>
</tr>
<tr>
<td>
<code>DecimalRoute.get_route_handler</code>
</td>
<td>
<pre>get_route_handler(self)</pre>
</td>
<td>
يعيد غلافًا لمعالج المسار يمنع تسرب الاستثناء العام.
</td>
</tr>
</tbody>
</table>

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
create_app

service is None
not expected
value is None
```


### المعالجات الداخلية ومساراتها

المعالجات التالية معرفة داخل مصنع التطبيق، لذلك ليست تعريفات مستقلة في المستوى الأعلى. تحويل جسم المخطط إلى قاموس يسبق استدعاء الخدمة في عامل تنفيذ؛ لا يجري حد النقل الحساب الأكاديمي.

```text
body.model_dump()
run_in_threadpool
```

<table>
<thead><tr>
<th>المسار</th>
<th>المعالج الداخلي</th>
<th>مخطط الجسم</th>
<th>تابع الخدمة</th>
<th>المفتاح المطلوب</th>
</tr></thead>
<tbody>
<tr>
<td>
<code>GET /health</code>
</td>
<td>
<code>health</code>
</td>
<td>
<code>—</code>
</td>
<td>
<code>ApiService.health</code>
</td>
<td>
عام
</td>
</tr>
<tr>
<td>
<code>POST /api/v1/inputs/student/validate</code>
</td>
<td>
<code>validate_student</code>
</td>
<td>
<code>StudentValidationRequest</code>
</td>
<td>
<code>ApiService.validate_student</code>
</td>
<td>
خدمة
</td>
</tr>
<tr>
<td>
<code>POST /api/v1/inputs/courses/validate</code>
</td>
<td>
<code>validate_courses</code>
</td>
<td>
<code>CoursesValidationRequest</code>
</td>
<td>
<code>ApiService.validate_courses</code>
</td>
<td>
خدمة
</td>
</tr>
<tr>
<td>
<code>POST /api/v1/recommendations</code>
</td>
<td>
<code>recommend</code>
</td>
<td>
<code>RecommendationRequest</code>
</td>
<td>
<code>ApiService.recommend</code>
</td>
<td>
خدمة
</td>
</tr>
<tr>
<td>
<code>POST /api/v1/history/deltas/validate</code>
</td>
<td>
<code>validate_delta</code>
</td>
<td>
<code>HistoryDeltaRequest</code>
</td>
<td>
<code>ApiService.validate_delta</code>
</td>
<td>
إدارة
</td>
</tr>
<tr>
<td>
<code>GET /api/v1/admin/history/status</code>
</td>
<td>
<code>history_status</code>
</td>
<td>
<code>—</code>
</td>
<td>
<code>ApiService.history_status</code>
</td>
<td>
إدارة
</td>
</tr>
<tr>
<td>
<code>PUT /api/v1/admin/history/mode</code>
</td>
<td>
<code>history_mode</code>
</td>
<td>
<code>HistoryModeRequest</code>
</td>
<td>
<code>ApiService.set_history_mode</code>
</td>
<td>
إدارة
</td>
</tr>
<tr>
<td>
<code>POST /api/v1/admin/history/initialize</code>
</td>
<td>
<code>initialize_history</code>
</td>
<td>
<code>HistoryInitializeRequest</code>
</td>
<td>
<code>ApiService.initialize_history</code>
</td>
<td>
إدارة
</td>
</tr>
<tr>
<td>
<code>POST /api/v1/admin/history/preview</code>
</td>
<td>
<code>preview_history</code>
</td>
<td>
<code>HistoryDeltaRequest</code>
</td>
<td>
<code>ApiService.preview_history</code>
</td>
<td>
إدارة
</td>
</tr>
<tr>
<td>
<code>POST /api/v1/admin/history/commit</code>
</td>
<td>
<code>commit_history</code>
</td>
<td>
<code>HistoryCommitRequest</code>
</td>
<td>
<code>ApiService.commit_history</code>
</td>
<td>
إدارة
</td>
</tr>
<tr>
<td>
<code>POST /api/v1/admin/history/activate</code>
</td>
<td>
<code>activate_history</code>
</td>
<td>
<code>HistoryActivationRequest</code>
</td>
<td>
<code>ApiService.activate_history</code>
</td>
<td>
إدارة
</td>
</tr>
<tr>
<td>
<code>POST /api/v1/admin/history/finalization-events</code>
</td>
<td>
<code>finalization_event</code>
</td>
<td>
<code>HistoryDeltaRequest</code>
</td>
<td>
<code>ApiService.finalize_history</code>
</td>
<td>
تثبيت نهائي
</td>
</tr>
</tbody>
</table>

الفحص التشخيصي يعيد الحالة المختارة في نتيجة التحقق، والتوصية تعيد القاموس بعد تحويله إلى قيم صالحة للنقل. مسارات الإدارة تمر بالتحويل الآمن نفسه.

```text
diagnostic -> result.http_status / result.public()
json_safe
```

المصادقة تستخدم ترويسة المفتاح. عدم إعداد مفتاح الدور ينتج عدم جاهزية، وغيابه عن الطلب يحتاج توثيقًا، والقيمة المخالفة تمنع الوصول. فشل مخطط الطلب له رسالة ثابتة لا تضم الجسم الخام.

```text
X-API-Key
AUTH_UNCONFIGURED: 503
AUTH_REQUIRED: 401
AUTH_FORBIDDEN: 403
INVALID_REQUEST_SCHEMA: 422
INTERNAL_ERROR: 500
```

## ٦. كيف تتغير البيانات؟

واجهة الصحة تستطيع إعادة حالة النقل السليمة مع عدم جاهزية المودلات. هذه حالة صحيحة ومختلفة عن السماح بالتوصية.

مثال اصطناعي لحالة تغيب فيها جميع الأصول؛ لا يجرى فيه توقع ولا يمر جسم طالب.

```text
GET /health
```

```json
{
  "api_health": "healthy",
  "model_readiness": {"ready": false},
  "history_readiness": {"ready": false},
  "catalog_readiness": {"ready": false},
  "grade_scale_readiness": {"ready": false},
  "recommendation_readiness": {"ready": false},
  "production_operational_limits": "UNRESOLVED"
}
```

## ٧. القواعد والافتراضات

المفاتيح ثلاثة أدوار مستقلة: خدمة، إدارة، وتثبيت نهائي. واجهة التحقق من دفعة التاريخ للقراءة فقط. لا يوجد تطبيق عام يُحمّل المودلات أثناء استيراد الملف.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

المصادقة هنا تثبت هوية الخدمة الوسيطة، بينما صلاحية المستخدم الجامعي على الطالب مسؤولية الخلفية الجامعية. يجب أن تبقى بيانات الرد الخام وأسرار الترويسات خارج الأخطاء.

أي قيمة أو قطع غير مطابق يجب أن يرفض أو يسجل غير متاح حسب العقد، قبل تحويله إلى توقع. لا تعالج هذه الصفحة نقص المصدر بتغيير ميزة أو وضع قيمة افتراضية.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [عقود أجسام الطلبات](schemas.md)
- [تنسيق التحقق والتوصية والإدارة](service.md)
- [الإعدادات ومصادرها البيئية](settings.md)
- [أدوات الهوية والأرقام والتشخيص الآمن](validation.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
fastapi
starlette
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
test_http_migration_manual_auto_rollback_and_existing_pareto_contract
test_missing_artifacts_block_migration_but_http_validation_remains_available
test_specialty_feature_requirement_rejects_update_before_publication
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert status['active_as_of_part'] == 20251
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

وجود مصنع التطبيق لا يثبت نشره فعليًا أو نجاح الاتصال الجامعي. إنشاء التطبيق يحتاج تبعيات الويب الاختيارية.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- النقل ينشئ المسارات ويفوض الحساب للخدمة.
- مفتاح الخدمة لا يملك صلاحيات إدارة التاريخ.
- صحة النقل مستقلة عن جاهزية أصول التوصية.

ثلاثة أسئلة للفهم:

1. لماذا تعمل الصحة والتحقق عند غياب المودل؟
2. كيف يصل جسم الطلب من المخطط إلى تابع الخدمة؟
3. أين يمنع تسرب قيمة خاصة عند فشل المخطط؟

تمرين قراءة آمن:

اختر مسار التوصية ومسار التفعيل من الجدول، وارسم شروط التوثيق والتحويل لكل منهما على الورق.

التمرين قراءة وحساب على الورق؛ لا يغير المشروع ولا يشغّل بناءً أو توقعًا أو تحديث تاريخ.
