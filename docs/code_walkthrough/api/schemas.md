# عقود أجسام الطلبات

```text
src/api/schemas.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يفصل أشكال الطلبات العامة عن الحسابات. يمنع تمرير حقول غير معروفة ويسجل الهوية وسياقي الجلب ومصادر القيم والسياسات الإدارية صراحةً.

الدور في الخريطة:
واجهة وتشغيل

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [إنشاء تطبيق الواجهات والمصادقة](app.md)

## ٣. المدخلات

قواميس أجسام الطلبات. الهوية تستعمل معرفات نصية صارمة وفصلًا نصيًا أو صحيحًا. قيم الساعات أعداد عشرية، وعدد النتائج صحيح صارم.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

الحقول وأنواعها كما في تعريف المخططات:

```python
class Envelope(BaseModel):
class Identity(Envelope):
    student_id: StrictStr
    degree_id: StrictStr
    part_id: StrictInt | StrictStr
class SourceContexts(Envelope):
    student: Identity | None = None
    courses: Identity | None = None
class SourcedValue(Envelope):
    value: Any
    source: StrictStr
    as_of_part: StrictInt | StrictStr
class RegistrationPolicy(Envelope):
    source: StrictStr
    part_id: StrictInt | StrictStr
    requirement_group_modes: dict[StrictStr, Literal["strict_remaining", "unbounded", "approved_overflow"]]
    group_overflow_credits: dict[StrictStr, Decimal] = Field(default_factory=dict)
    allow_register_all_optional_confirmed: StrictBool = False
    approved_exception_course_ids: list[StrictStr] = Field(default_factory=list)
    allowed_failed_repeat_credits: Decimal
    allowed_withdrawn_repeat_credits: Decimal | None = None
    attempts_scope_confirmed: StrictBool = False
    load_profile: Literal["study", "graduation"]
class TotalRegCreditsSource(Envelope):
    source: StrictStr
    target_part: StrictInt | StrictStr
    as_of_part: StrictInt | StrictStr
    timing: Literal["beginning_of_semester", "end_of_semester"]
    rules_reference: StrictStr
    semester_complete: StrictBool = False
    additive_credit_accounting: StrictBool = False
    semester_gpa_counted_credits: Decimal | None = None
class IntegrationContext(Envelope):
    student_values: dict[StrictStr, SourcedValue] = Field(default_factory=dict)
    total_reg_credits_source: TotalRegCreditsSource | None = None
    previous_course_statuses: dict[StrictStr, SourcedValue] = Field(default_factory=dict)
    registration_policy: RegistrationPolicy | None = None
class StudentValidationRequest(Identity):
    student_api_response: dict
    source_contexts: SourceContexts
    integration_context: IntegrationContext = Field(default_factory=IntegrationContext)
class CoursesValidationRequest(Identity):
    courses_api_response: dict
    source_contexts: SourceContexts
    integration_context: IntegrationContext = Field(default_factory=IntegrationContext)
class RecommendationRequest(StudentValidationRequest):
    courses_api_response: dict
    history_as_of_part: StrictInt | StrictStr
    target_credits: Decimal | None = None
    min_credits: Decimal | None = None
    max_credits: Decimal | None = None
    top_k: StrictInt = Field(default=3, ge=1, le=50)
    mode: Literal["normal", "backtesting"] = "normal"
class Finalization(Envelope):
    finalized_part_id: StrictInt | StrictStr
    approval_reference: StrictStr
class HistoryDeltaRequest(Envelope):
    part_id: StrictInt | StrictStr
    rows: list[dict]
    finalization: Finalization | None = None
class HistoryModeRequest(Envelope):
    mode: Literal["disabled", "manual", "auto_on_finalization"]
class HistoryInitializeRequest(Envelope):
    expected_source_hash: StrictStr
    approval_reference: StrictStr
    confirmation: StrictBool
    cumulative_history_confirmed: StrictBool
class HistoryCommitRequest(HistoryDeltaRequest):
    preview_token: StrictStr
    confirmation: StrictBool
class HistoryActivationRequest(Envelope):
    history_as_of_part: StrictInt | StrictStr
    confirmation: StrictBool
    rollback: StrictBool = False
```

الأنواع والبنى المستعملة في هذا الحد:

```text
HTTP request body: dict
IDs: StrictStr
credits: Decimal
flags: StrictBool
```

## ٤. المخرجات

كائنات مخطط متحققة تُحوّل لاحقًا إلى قواميس. المخطط يكشف عدم توافق شكل الطلب؛ فحص المصادر والجامعة والتاريخ داخل المحولات والخدمة.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

أنواع المخرجات الأساسية:

```text
Envelope subclasses -> Pydantic BaseModel
model_dump() -> dict
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
<code>Envelope</code>
</td>
<td>
الأصل الصارم للمخططات ورفض الحقول الزائدة.
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
<code>Identity</code>
</td>
<td>
هوية الطالب والاختصاص والفصل.
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
<code>SourceContexts</code>
</td>
<td>
سياق مستقل لجلب كل رد.
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
<code>SourcedValue</code>
</td>
<td>
قيمة مكملة بمصدر ووقت محددين.
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
<code>RegistrationPolicy</code>
</td>
<td>
السياسات والحدود والتفويضات الموثقة.
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
<code>TotalRegCreditsSource</code>
</td>
<td>
شهادة توقيت مقام المعدل وقواعد جمع التسجيل.
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
<code>IntegrationContext</code>
</td>
<td>
حاوية مصادر وقيم وسياسات مكملة.
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
<code>StudentValidationRequest</code>
</td>
<td>
جسم التحقق من الطالب.
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
<code>CoursesValidationRequest</code>
</td>
<td>
جسم التحقق من المواد.
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
<code>RecommendationRequest</code>
</td>
<td>
جسم التوصية والقطع والوضع والساعات والعدد.
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
<code>Finalization</code>
</td>
<td>
مرجع تثبيت الفصل النهائي.
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
<code>HistoryDeltaRequest</code>
</td>
<td>
جسم دفعة المجاميع للقراءة أو الإدارة.
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
<code>HistoryModeRequest</code>
</td>
<td>
اختيار وضع تحديث التاريخ الدائم.
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
<code>HistoryInitializeRequest</code>
</td>
<td>
تأكيد ترحيل أساس تراكمي ببصمته وموافقته.
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
<code>HistoryCommitRequest</code>
</td>
<td>
تأكيد نشر دفعة مطابقة لمعاينتها.
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
<code>HistoryActivationRequest</code>
</td>
<td>
تأكيد تفعيل نسخة محددة أو الرجوع إليها.
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
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
Envelope
```

يمنع الحقول الزائدة في جميع العقود المشتقة.

خطوة 2:

```text
Identity / SourceContexts
```

يفصل هوية الطلب عن سياق كل رد جامعي؛ الحقول الاختيارية هنا لا تلغي إلزام المحول بالسياق المناسب.

خطوة 3:

```text
SourcedValue / TotalRegCreditsSource
```

يحمل القيمة ومصدرها ووقتها، أو شهادة توقيت مقام المعدل وقواعد احتسابه.

خطوة 4:

```text
IntegrationContext / RegistrationPolicy
```

يجمع المصادر المكملة وسياسة الساعات والإعادات والتفويضات؛ لا يجعلها قيمًا جامعية افتراضية.

خطوة 5:

```text
RecommendationRequest.credit_mode
```

يرفض خلط عدد ساعات دقيق مع مجال، ويرفض المجال غير المكتمل. العدد الافتراضي للنتائج ثلاثة والمسموح من واحد إلى خمسين.

خطوة 6:

```text
HistoryCommitRequest / HistoryActivationRequest
```

يفصل تأكيد إنشاء النسخة عن تأكيد تفعيلها؛ الرجوع للخلف حقل صريح.

### نوع التحقق وحدوده

المعرفات النصية الصارمة تمنع قبول معرف منطقي أو تحوله ضمنيًا. الساعات عشرية، وعدد النتائج عدد صحيح صارم من واحد إلى خمسين.

```text
StrictStr
StrictInt
StrictBool
Decimal
Literal
```

الغلاف الأصلي للجامعة يبقى قاموسًا لأن حقوله الخارجية تمر إلى المحولات باسمها الفعلي. رفض الحقول الزائدة يخص الغلاف العام وعناصر سياقه المعرّفة، ولا يستبدل التحقق من محتوى الجامعة.

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
<code>RecommendationRequest.credit_mode</code>
</td>
<td>
<pre>credit_mode(self)</pre>
</td>
<td>
يرفض خلط هدف دقيق مع مجال أو غياب حدود المجال.
</td>
</tr>
</tbody>
</table>

## ٦. كيف تتغير البيانات؟

طلب ساعات دقيق مع حدود ساعات في الوقت نفسه يُرفض قبل المحرك؛ طلب بساعات دقيقة وعدد نتائج ثلاثة ينتقل إلى التحقق الأكاديمي.

## ٧. القواعد والافتراضات

شكل الطلب صارم، لكن تأكيد صحة القواعد الجامعية ليس وظيفة المخطط. حالة التشغيل المعتادة افتراضية، والاختبار التاريخي اختيار صريح.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

القيمة المصدّرة من مخطط صحيح قد تكون زمنيًا خاطئة أو متعارضة؛ لذلك لا يجوز تجاوز المحولات. عدادات المحاولات ومقام المعدل لا تُستنتج من صحة النوع وحدها.

أي قيمة أو قطع غير مطابق يجب أن يرفض أو يسجل غير متاح حسب العقد، قبل تحويله إلى توقع. لا تعالج هذه الصفحة نقص المصدر بتغيير ميزة أو وضع قيمة افتراضية.

## ٩. التبعيات

لا توجد استيرادات داخلية من وحدات المشروع في هذا الملف.


تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
pydantic
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_api_academic_semantics.py)

```text
tests/test_api_academic_semantics.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_typed_http_contract_accepts_official_total_evidence_and_rejects_string_bool
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert StudentValidationRequest.model_validate(request).integration_context.total_reg_credits_source.timing == 'end_of_semester'
```

## ١١. القيود المعروفة

المخططات لا تثبت اكتمال فصل أو إذن تسجيل مادة، ولا تحميل المودلات أو وجود لقطة تاريخ.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- المخططات ترفض الحقول غير المعلنة.
- الساعات الدقيقة تختلف عن المعرفات النصية والعدادات الصحيحة.
- صحة البنية لا تثبت الهوية أو التوقيت أو نهائية الفصل.

ثلاثة أسئلة للفهم:

1. ما الفرق بين تعريف سياق اختياري واشتراطه أثناء التحقق؟
2. لماذا يمنع الجمع بين الساعات الدقيقة ومجال الساعات؟
3. أي مخطط يحتاج مرجع نهائية وأي مخطط يحتاج تأكيد تفعيل؟

تمرين قراءة آمن:

قارن على الورق جسمًا بساعات دقيقة وآخر بحدين؛ حدد شرط الرفض إذا جمع الجسم الطريقتين.

التمرين قراءة وحساب على الورق؛ لا يغير المشروع ولا يشغّل بناءً أو توقعًا أو تحديث تاريخ.
